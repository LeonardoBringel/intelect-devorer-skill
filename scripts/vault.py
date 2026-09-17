#!/usr/bin/env python3
"""Utilitário para o vault "second brain" do Obsidian.

O script não cria notas — quem escreve é o agente. Aqui ficam só as partes
deterministas que dão errado quando feitas de cabeça, e a auditoria que confere
o resultado depois:

  - achar se já existe uma nota para um conceito (evitar duplicar)  -> `find`
  - listar o vocabulário de tags em uso (evitar sinônimos)          -> `tags`
  - normalizar a forma da nota (unwrap + divider sob cabeçalho)     -> `fmt`
  - auditar o vault contra os templates e as convenções            -> `lint`

`lint` é o portão: sai com código ≠ 0 quando encontra erro, e usa os arquivos
em `<vault>/templates/` como fonte de verdade. Editar um template no Obsidian
ajusta o lint sem tocar neste código — placeholder, chave de frontmatter e
seção obrigatória saem todos de lá, não de uma lista fixa aqui dentro.

Os templates NÃO são definidos aqui, e este script nunca os escreve.

A versão da skill vive em `metadata.version` na frontmatter do `SKILL.md`.

Sem dependências externas — só a biblioteca padrão do Python 3.

Uso:
  python vault.py find   <vault> "<termo>"
  python vault.py tags   <vault> ["<termo>"]   # vocabulário de tags já em uso
  python vault.py fmt    <arquivo|pasta|vault> [--check]
  python vault.py lint   <vault>               # portão: exit ≠ 0 se houver erro
"""

import argparse
import difflib
import os
import re
import sys
import unicodedata

# Papel lógico -> nome canônico da pasta. Os nomes são kebab minúsculo, sem
# numeração: a ordem do fluxo vive no SKILL.md, não no nome da pasta.
FOLDER_ROLE = [
    "dump",
    "daily",
    "projects",
    "lessons",
    "knowledge",
    "resources",
    "archives",
]

# Tipos de nota -> nome do arquivo de template dentro de `<vault>/templates/`.
# A correspondência é case-insensitive na hora de procurar.
TEMPLATE_FILE = {
    "daily": "daily-template.md",
    "dump": "dump-template.md",
    "project": "project-template.md",
    "task": "task-template.md",
    "lesson": "lesson-template.md",
    "knowledge": "knowledge-template.md",
}

# Chaves de frontmatter que, quando o template daquele tipo as declara, precisam
# chegar preenchidas na nota. A lista é um teto, não um piso: o template é quem
# decide quais existem (`dump` não tem `tags`, `daily` não tem `title`).
REQUIRED_WHEN_IN_TEMPLATE = [
    "title",
    "created",
    "tags",
    "project",
]

# Chaves que só um agente tem como preencher. Nota escrita à mão pelo usuário no
# Obsidian não tem modelo a declarar nem versão de skill: vazio aqui quer dizer
# "não houve agente", não "o agente esqueceu" — e preencher depois seria inventar
# dado. O lint reporta como metadado, sem contar erro nem mexer no exit code.
AGENT_ONLY_WHEN_IN_TEMPLATE = [
    "skill_version",
    "llm_model_used",
]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# `[[alvo#âncora|texto]]` — âncora e texto opcionais. Link só de âncora
# (`[[#Seção]]`) não casa, e é isso que queremos: ele é interno à nota.
WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(#[^\[\]|]+)?(?:\|([^\[\]]+))?\]\]")


def slugify(text: str) -> str:
    """Nome canônico de arquivo: kebab minúsculo, sem acento nem caractere especial."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    return text.strip("-")


def resolve_folder(vault: str, role: str) -> str:
    """Acha a pasta do papel pedido (`projects`, `lessons`…)."""
    if not os.path.isdir(vault):
        sys.exit(f"[erro] vault não encontrado: {vault}")
    for name in sorted(os.listdir(vault)):
        if os.path.isdir(os.path.join(vault, name)) and name.strip().lower() == role:
            return os.path.join(vault, name)
    sys.exit(
        f"[erro] não encontrei a pasta '{role}' em {vault}. "
        f"O vault segue a estrutura {', '.join(FOLDER_ROLE)}?"
    )


def resolve_templates_dir(vault: str) -> str:
    """Acha a pasta de templates do vault (tolerante a caixa/variação)."""
    if not os.path.isdir(vault):
        sys.exit(f"[erro] vault não encontrado: {vault}")
    tdir = _templates_dir_or_none(vault)
    if tdir is None:
        sys.exit(f"[erro] não encontrei a pasta 'templates/' em {vault}.")
    return tdir


def load_template(vault: str, kind: str) -> str:
    """Lê o texto cru do template do vault para o tipo de nota pedido."""
    if kind not in TEMPLATE_FILE:
        sys.exit(
            f"[erro] tipo de template inválido: '{kind}'. "
            f"Use um de: {', '.join(sorted(TEMPLATE_FILE))}"
        )
    tdir = resolve_templates_dir(vault)
    want = TEMPLATE_FILE[kind].lower()
    for name in sorted(os.listdir(tdir)):
        if name.lower() == want:
            with open(os.path.join(tdir, name), encoding="utf-8") as fh:
                return fh.read()
    sys.exit(
        f"[erro] template de '{kind}' não encontrado em {tdir} "
        f"(esperado: '{TEMPLATE_FILE[kind]}')."
    )


def _templates_dir_or_none(vault: str):
    for name in os.listdir(vault):
        full = os.path.join(vault, name)
        if os.path.isdir(full) and name.strip().lower() == "templates":
            return os.path.normpath(full)
    return None


def iter_notes(vault: str):
    """Gera (caminho, slug) de toda nota .md do vault, exceto os templates.

    Pastas ocultas ficam de fora: `.obsidian/` guarda plugins, e vários deles
    trazem um `README.md` que não é nota do usuário — o `fmt` não pode reescrever
    esses arquivos, nem o `find` deve devolvê-los.
    """
    tdir = _templates_dir_or_none(vault)
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if tdir is not None and os.path.normpath(root) == tdir:
            continue
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f), f[:-3]


def read_frontmatter(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return ""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""


def read_frontmatter_value(path: str, key: str) -> str:
    """Lê um campo escalar do frontmatter (`title`, `type`, `project`…)."""
    m = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*)$", read_frontmatter(path))
    return m.group(1).strip().strip("\"'") if m else ""


def read_frontmatter_list(path: str, key: str):
    """Lê um campo de lista do frontmatter (`aliases`, `tags`…), se houver.

    Aceita as duas formas que o Obsidian escreve:  `key: [a, b]`  e
    `key:` seguido de itens `  - a`. Os itens só contam até a próxima chave
    do frontmatter, para que `tags:` e `aliases:` não se misturem.
    """
    front = read_frontmatter(path)
    if not front:
        return []

    values = []
    lines = front.splitlines()
    for i, line in enumerate(lines):
        inline = re.match(rf"^{re.escape(key)}:\s*\[(.*?)\]\s*$", line)
        if inline:
            values += [v.strip().strip("\"'") for v in inline.group(1).split(",")]
            continue
        if not re.match(rf"^{re.escape(key)}:\s*$", line):
            continue
        # forma de bloco: consome os itens de lista até a próxima chave
        for item in lines[i + 1:]:
            if re.match(r"^\s*-\s+", item):
                values.append(item.split("-", 1)[1].strip().strip("\"'"))
            elif item.strip():
                break
    return [v for v in values if v]


def read_aliases(path: str):
    return read_frontmatter_list(path, "aliases")


def note_title(path: str, note_slug: str) -> str:
    """Título humano da nota: `title:` do frontmatter, ou o próprio slug."""
    return read_frontmatter_value(path, "title") or note_slug


def wikilink(note_slug: str, title: str) -> str:
    """Forma canônica do link: `[[slug|Título]]`, sem pipe redundante."""
    return f"[[{note_slug}]]" if title == note_slug else f"[[{note_slug}|{title}]]"


def split_frontmatter(text: str):
    """Separa o frontmatter YAML do corpo. O frontmatter nunca é reformatado."""
    m = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(0), text[m.end():]


def _section_bounds(lines, section: str):
    """Retorna (inicio, fim) das linhas de conteúdo sob o cabeçalho `## <section>`.

    `inicio` já pula a linha separadora `---` logo abaixo do cabeçalho, se houver.
    Retorna (None, None) se a seção não existe no arquivo.
    """
    target = f"## {section.strip().lower()}"
    hdr = next((i for i, ln in enumerate(lines) if ln.strip().lower() == target), None)
    if hdr is None:
        return None, None
    start = hdr + 1
    if start < len(lines) and lines[start].strip() == "---":
        start += 1
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return start, end


def cmd_find(args):
    """Procura notas cujo slug, título ou alias case com o termo."""
    term = args.term.lower().strip()
    term_slug = slugify(term)
    exact, partial = [], []
    for path, note_slug in iter_notes(args.vault):
        title = note_title(path, note_slug)
        names = [note_slug.lower(), title.lower()] + [a.lower() for a in read_aliases(path)]
        rel = os.path.relpath(path, args.vault)
        if term in names or term_slug == note_slug.lower():
            exact.append((note_slug, title, rel))
        elif any(term in n for n in names):
            partial.append((note_slug, title, rel))
    for label, group in (("EXATO:", exact), ("PARCIAL:", partial)):
        if group:
            print(label)
            for note_slug, title, rel in group:
                print(f"  {wikilink(note_slug, title)}  ->  {rel}")
    if not exact and not partial:
        print("NENHUMA nota encontrada — provavelmente é uma nota nova a criar.")


def cmd_tags(args):
    """Lista o vocabulário de tags já em uso, da mais frequente pra menos.

    Serve pro mesmo papel que o `find` cumpre pras notas: reusar o que já
    existe em vez de inventar uma variante (`docker` vs `containers`).
    """
    counts = {}
    for path, _slug in iter_notes(args.vault):
        for tag in read_frontmatter_list(path, "tags"):
            counts[tag] = counts.get(tag, 0) + 1

    if not counts:
        print("NENHUMA tag em uso ainda — o vocabulário começa agora.")
        return

    if args.term:
        term = args.term.lower()
        counts = {t: n for t, n in counts.items() if term in t.lower()}
        if not counts:
            print(f"NENHUMA tag existente casa com '{args.term}'.")
            return

    for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:3}  {tag}")


# --- Lint --------------------------------------------------------------------
#
# O lint é o backstop do fluxo: o agente escreve a nota à mão e o lint confere o
# resultado contra o template do vault. Tudo que ele sabe sobre "como a nota
# deveria ser" vem de `<vault>/templates/` — nada de lista fixa aqui, que
# dessincroniza na primeira vez que o usuário mexe num template no Obsidian.


def strip_code(text: str) -> str:
    """Remove blocos e trechos de código antes de procurar links.

    `[[slug|Título]]` escrito entre crases é exemplo de sintaxe, e o Obsidian
    também não o trata como link — o lint não pode reclamar de link quebrado ali.
    """
    text = re.sub(r"(?ms)^\s{0,3}(?:```|~~~).*?^\s{0,3}(?:```|~~~)\s*$", "", text)
    return re.sub(r"`[^`\n]*`", "", text)


_TEMPLATE_CACHE: dict = {}


def template_text(vault: str, kind: str):
    """Texto do template daquele tipo, ou None se o vault não tiver esse arquivo.

    O lint nunca aborta por template ausente: ele só perde as checagens que
    dependem daquele tipo e segue auditando o resto do vault.
    """
    if kind not in _TEMPLATE_CACHE:
        try:
            _TEMPLATE_CACHE[kind] = load_template(vault, kind)
        except SystemExit:
            _TEMPLATE_CACHE[kind] = None
    return _TEMPLATE_CACHE[kind]


def _body_lines(text: str):
    """Linhas de conteúdo do corpo, sem cabeçalho, divider nem linha em branco.

    Devolve (numero_da_linha_no_arquivo, texto_normalizado, texto_literal). A
    normalização é trim + minúsculas: é ela que faz a comparação nota ↔ template
    sobreviver a um espaço a mais ou a uma maiúscula trocada. O literal vai junto
    porque é ele que a mensagem de erro imprime — o usuário precisa achar a linha
    no Obsidian buscando o texto exato, não a versão minusculada.
    """
    front, body = split_frontmatter(text)
    offset = front.count("\n")
    out = []
    for i, raw in enumerate(body.split("\n")):
        s = raw.strip()
        if not s or s.startswith("#") or set(s) == {"-"}:
            continue
        out.append((offset + i + 1, s.lower(), s))
    return out


def _template_sections(text: str):
    """Cabeçalhos `## ...` que o template exige (na ordem em que aparecem)."""
    _front, body = split_frontmatter(text)
    return [ln.strip()[3:].strip() for ln in body.split("\n") if ln.strip().startswith("## ")]


def _template_keys(text: str):
    """Chaves de topo declaradas no frontmatter do template."""
    front, _body = split_frontmatter(text)
    return set(re.findall(r"(?m)^([A-Za-z_][\w-]*):", front))


def _check_against_template(path: str, rel: str, kind: str, text: str, tpl: str, issues, metadata):
    """Checagens que comparam a nota com o template do seu `type:`."""
    # 1. placeholder residual — linha de corpo idêntica a uma linha do template
    tpl_lines = {s for _n, s, _raw in _body_lines(tpl)}
    for lineno, s, raw in _body_lines(text):
        if s in tpl_lines:
            issues.append((rel, f"linha {lineno}: placeholder do template não substituído: {raw}"))

    # 2. frontmatter preenchido, não só presente — só as chaves que o template tem
    keys = _template_keys(tpl)
    for key in REQUIRED_WHEN_IN_TEMPLATE + AGENT_ONLY_WHEN_IN_TEMPLATE:
        if key not in keys:
            continue
        filled = read_frontmatter_list(path, key) if key == "tags" else read_frontmatter_value(path, key)
        if filled:
            continue
        msg = f"frontmatter com `{key}` vazio (o template de {kind} declara a chave)"
        bucket = metadata if key in AGENT_ONLY_WHEN_IN_TEMPLATE else issues
        bucket.append((rel, msg))

    # 3. seções faltando — cabeçalho extra na nota é permitido, faltar não é
    lines = text.split("\n")
    for section in _template_sections(tpl):
        if _section_bounds(lines, section)[0] is None:
            issues.append((rel, f"falta a seção `## {section}` do template de {kind}"))


def _check_path(rel: str, path: str, kind: str, note_slug: str, projects_dir: str, issues):
    """4. Caminho: onde cada tipo de nota tem de morar, e como o arquivo se chama."""
    if kind == "task":
        tasks_dir = os.path.dirname(path)
        project_dir = os.path.dirname(tasks_dir)
        if os.path.basename(tasks_dir) != "tasks" or os.path.dirname(project_dir) != projects_dir:
            issues.append((rel, "task fora de projects/<slug>/tasks/"))
        if not DATE_PREFIX_RE.match(note_slug):
            issues.append((rel, "task sem prefixo de data no nome (esperado: yyyy-mm-dd-<slug>.md)"))
    elif kind == "project":
        folder = os.path.dirname(path)
        if os.path.dirname(folder) != projects_dir or os.path.basename(folder) != note_slug:
            issues.append((rel, f"projeto fora de projects/{note_slug}/{note_slug}.md"))
    elif kind == "daily" and not DATE_RE.match(note_slug):
        issues.append((rel, "daily com nome fora do padrão yyyy-mm-dd.md"))


def cmd_lint(args):
    """Portão do fluxo: audita o vault e sai com código ≠ 0 se houver erro."""
    vault = args.vault
    issues, pending, metadata = [], [], []
    notes = sorted(iter_notes(vault))
    slugs = {note_slug for _p, note_slug in notes}

    projects_dir = resolve_folder(vault, "projects")
    for name in sorted(os.listdir(projects_dir)):
        full = os.path.join(projects_dir, name)
        if os.path.isfile(full) and name.endswith(".md"):
            issues.append((name, "nota solta em projects/ — todo projeto é uma pasta"))
        elif os.path.isdir(full) and not name.startswith("."):
            if not os.path.isfile(os.path.join(full, f"{name}.md")):
                issues.append((name, f"falta a nota principal {name}/{name}.md"))
            if not os.path.isdir(os.path.join(full, "tasks")):
                issues.append((name, "falta a subpasta tasks/"))

    for path, note_slug in notes:
        rel = os.path.relpath(path, vault)
        if not SLUG_RE.match(note_slug):
            issues.append((rel, f"nome fora do kebab-case (sugerido: {slugify(note_slug)}.md)"))

        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            issues.append((rel, f"não consegui ler o arquivo: {exc}"))
            continue

        kind = read_frontmatter_value(path, "type")
        tpl = template_text(vault, kind) if kind in TEMPLATE_FILE else None
        if tpl is not None:
            _check_against_template(path, rel, kind, text, tpl, issues, metadata)
        elif kind in TEMPLATE_FILE:
            # sem o template não há contra o que comparar: `title`, `tags`,
            # `project`, placeholder e seções deixam de ser auditados nesta nota.
            # Avisa em vez de calar — mas é aviso, não erro: template ausente é
            # defeito do vault, não da nota.
            metadata.append(
                (rel, f"template de {kind} ausente, checagens de frontmatter e seções puladas")
            )
        else:
            # `type:` é a chave de junção da auditoria: placeholder residual,
            # frontmatter, seções e caminho todos dependem dele para saber contra
            # qual template comparar. Sem um `type:` reconhecido a nota atravessa
            # o lint inteira sem uma única linha de saída — por isso é erro, não
            # metadado: não é dívida histórica nem informação, é nota que escapa
            # de toda a auditoria.
            got = f"`type: {kind}` desconhecido" if kind else "frontmatter sem `type:`"
            issues.append(
                (
                    rel,
                    f"{got} — a nota escapa de toda a auditoria; "
                    f"use um de: {', '.join(sorted(TEMPLATE_FILE))}",
                )
            )
        _check_path(rel, path, kind, note_slug, projects_dir, issues)

        body = strip_code(text)
        for target, _anchor, _label in WIKILINK_RE.findall(body):
            target = target.strip()
            if target.endswith((".pdf", ".png", ".jpg", ".jpeg", ".ppt", ".pptx")):
                continue
            if target not in slugs:
                # link para nota que ainda não existe é uso legítimo do Obsidian:
                # marca uma nota a escrever, não um defeito. Reporta sem reprovar.
                pending.append((rel, f"link pendente (nota ainda não existe): [[{target}]]"))
            elif target != slugify(target):
                issues.append((rel, f"link fora do kebab-case: [[{target}]]"))

    for rel, msg in pending:
        print(f"[pendente] {rel}: {msg}")
    for rel, msg in metadata:
        print(f"[metadado] {rel}: {msg}")
    if not issues:
        print("[ok] vault dentro do padrão.")
        return
    for rel, msg in issues:
        print(f"[lint] {rel}: {msg}")
    print(f"\n{len(issues)} item(ns) fora do padrão.")
    sys.exit(1)


# --- Formatação de notas -----------------------------------------------------
#
# O `fmt` cuida das regras de forma que são deterministas — desfazer hard wrap e
# garantir o divider `---` sob cada cabeçalho. São regras que o modelo esquece ao
# longo de uma sessão longa, e que uma função aplica sempre igual. O que NÃO está
# aqui é densidade textual: cortar redundância é julgamento, e mora nas rules.

FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
HEADER_RE = re.compile(r"^#{1,6}\s+\S")
THEMATIC_BREAK = ("---", "***", "___")

# Uma linha que abre seu próprio bloco nunca é continuação da anterior: item de
# lista, citação, tabela, cabeçalho, régua horizontal.
BLOCK_START_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>|\||#{1,6}\s|---\s*$|\*\*\*\s*$|___\s*$)"
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")


def _is_indented_code(line: str) -> bool:
    """Linha indentada que NÃO pertence a um item de lista = bloco de código."""
    return (line.startswith("    ") or line.startswith("\t")) and not LIST_ITEM_RE.match(line)


def _is_continuation(line: str, prev: str) -> bool:
    """A linha é continuação visual da anterior (fruto de hard wrap)?"""
    if not line.strip() or BLOCK_START_RE.match(line):
        return False
    if line.startswith("    ") or line.startswith("\t"):
        # indentação profunda só é continuação dentro de lista; fora dela é
        # bloco de código indentado, que passa intacto.
        return bool(LIST_ITEM_RE.match(prev))
    return True


def _accepts_continuation(prev: str) -> bool:
    """A linha anterior pode absorver uma continuação?"""
    if not prev or not prev.strip():
        return False
    if prev.endswith("  ") or prev.endswith("\\"):
        return False  # quebra de linha explícita do Markdown — é intencional
    if _is_indented_code(prev):
        return False
    s = prev.strip()
    if HEADER_RE.match(s) or s in THEMATIC_BREAK:
        return False
    return not (s.startswith("|") or s.startswith(">"))


def format_markdown(text: str) -> str:
    """Normaliza o corpo da nota.

    Três regras: (1) parágrafo/item é uma linha física só — linhas quebradas por
    largura são rejuntadas; (2) todo cabeçalho leva `---` logo abaixo e o
    conteúdo começa na linha seguinte, sem branco no meio; (3) uma linha em
    branco antes de cada cabeçalho e no máximo uma entre blocos.

    Frontmatter e blocos de código cercados passam intactos.
    """
    front, body = split_frontmatter(text)
    lines = body.split("\n")
    out: list[str] = []
    in_fence = False
    i = 0

    while i < len(lines):
        raw = lines[i].rstrip("\n")
        line = raw.rstrip()
        if line and raw[len(line):].startswith("  "):
            line += "  "  # break duro do Markdown: intencional, sobrevive

        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue

        if in_fence:
            out.append(lines[i].rstrip("\n"))
            i += 1
            continue

        if not line.strip():
            if out and out[-1].strip():
                out.append("")
            i += 1
            continue

        if HEADER_RE.match(line):
            while out and not out[-1].strip():
                out.pop()
            if out:
                out.append("")
            out.append(line.rstrip())
            # o divider é obrigatório: reaproveita o que já existe (mesmo
            # separado por linhas em branco) ou insere um.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            out.append("---")
            i = j + 1 if j < len(lines) and lines[j].strip() in THEMATIC_BREAK else i + 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue

        if out and _is_continuation(line, out[-1]) and _accepts_continuation(out[-1]):
            tail = "  " if line.endswith("  ") else ""
            out[-1] = f"{out[-1]} {line.strip()}{tail}"
        else:
            out.append(line)
        i += 1

    return front + ("\n".join(out).strip("\n") + "\n" if out else "")


def _fmt_targets(target: str):
    """Resolve o alvo do `fmt` em uma lista de notas (nunca inclui templates)."""
    if os.path.isfile(target):
        return [target]
    if os.path.isdir(target):
        return sorted(path for path, _slug in iter_notes(target))
    sys.exit(f"[erro] alvo não encontrado: {target}")


def cmd_fmt(args):
    """Normaliza a formatação das notas; com --check, só relata e sai com 1."""
    pending = 0
    for path in _fmt_targets(args.target):
        with open(path, encoding="utf-8") as fh:
            old = fh.read()
        new = format_markdown(old)
        if new == old:
            continue
        pending += 1
        rel = os.path.relpath(path, args.target if os.path.isdir(args.target) else os.path.dirname(path) or ".")
        if args.check:
            diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0))
            print(f"[check] {rel}")
            for ln in diff[2:8]:
                print(f"        {ln}")
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"[fmt] {rel}")

    if not pending:
        print("[ok] formatação já está normalizada.")
        return
    if args.check:
        print(f"\n{pending} nota(s) fora do padrão — rode sem --check para corrigir.")
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Utilitário do vault second brain.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("find", help="procura nota existente por slug/título/alias")
    sp.add_argument("vault")
    sp.add_argument("term")
    sp.set_defaults(func=cmd_find)

    sp = sub.add_parser("tags", help="lista o vocabulário de tags em uso")
    sp.add_argument("vault")
    sp.add_argument("term", nargs="?", default="")
    sp.set_defaults(func=cmd_tags)

    sp = sub.add_parser("fmt", help="normaliza a formatação das notas (unwrap + divider)")
    sp.add_argument("target", help="arquivo .md, pasta do vault ou o vault inteiro")
    sp.add_argument("--check", action="store_true", help="só relata o que está fora do padrão")
    sp.set_defaults(func=cmd_fmt)

    sp = sub.add_parser("lint", help="audita o vault contra os templates (exit ≠ 0 se houver erro)")
    sp.add_argument("vault")
    sp.set_defaults(func=cmd_lint)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
