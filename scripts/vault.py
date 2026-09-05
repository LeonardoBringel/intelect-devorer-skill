#!/usr/bin/env python3
"""Utilitário para o vault "second brain" do Obsidian.

Cuida das partes deterministas e chatas do fluxo, para que o Claude não
reinvente essa lógica (e não erre) a cada anotação:

  - resolver as pastas do vault de forma tolerante a variações
  - derivar o slug canônico de um título (kebab-case, sem acento)
  - achar se já existe uma nota para um conceito (evitar duplicar)
  - renderizar um template do vault (a fonte de verdade dos templates)
  - criar nota nova já no lugar certo, com nome e links corretos
  - garantir/abrir a nota do dia (Daily), sempre a partir do template do vault
  - registrar uma entrada na Daily sem duplicar linhas
  - versionar o vault num commit único ao fim da sessão
  - apontar o que está fora do padrão (`lint`)

Os templates NÃO são definidos aqui. Este script sempre lê os arquivos em
`<vault>/templates/` — assim a estrutura das notas fica sob controle do
usuário, no próprio Obsidian, e nunca conflita com o que o script gera.

Sem dependências externas — só a biblioteca padrão do Python 3.

Uso:
  python vault.py slug     "<título>"
  python vault.py find     <vault> "<termo>"
  python vault.py new      <vault> <project|task|lesson|knowledge|dump> "<Título>" [--project <slug>] [--progress "<síntese>"]
  python vault.py fmt      <arquivo|pasta|vault> [--check]   # normaliza a forma das notas
  python vault.py lint     <vault>               # nomenclatura, frontmatter e links fora do padrão
  python vault.py tags     <vault> ["<termo>"]   # vocabulário de tags já em uso
  python vault.py template <vault> <daily|dump|project|task|lesson|knowledge> [--title "<Título>"] [--date YYYY-MM-DD]
  python vault.py daily    <vault> [--date YYYY-MM-DD]
  python vault.py log      <vault> "<Título ou slug>" "<descrição curta>" [--section Projetos|Aprendizados|"Outras notas"] [--date YYYY-MM-DD]
  python vault.py commit   <vault>               # versiona tudo num commit só (fim da sessão)
  python vault.py folder   <vault> <papel>       # imprime o caminho da pasta pelo papel
  python vault.py tree     <vault>               # visão rápida da estrutura
  python vault.py version                        # versão da skill (vai pro frontmatter)
"""

import argparse
import datetime as dt
import difflib
import os
import re
import subprocess
import sys
import unicodedata

# Versão da skill, gravada em `skill_version` nas notas criadas. Serve para
# responder depois "sob quais regras esta nota foi escrita?" — então precisa ser
# um valor discreto e comparável, não algo derivado da árvore de trabalho.
#
# Declarada aqui de propósito, e NÃO lida do git: a cópia em execução da skill
# pode não ser um checkout (`git describe` falharia), e numa árvore suja o git
# devolveria o mesmo valor antes e depois de uma mudança de comportamento.
#
# Bump manual no release, junto com a tag git — mesma disciplina do
# `template_version` dos templates do vault.
SKILL_VERSION = "0.4.0"

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

# Nomes numerados da estrutura anterior (`03 - Knowledge`), mantidos só para
# uma cópia antiga do vault continuar resolvendo. `lessons` casa com o antigo
# `03 - Knowledge` porque foi essa pasta que virou Lessons na migração.
LEGACY_PREFIX = {
    "dump": "00",
    "daily": "01",
    "projects": "02",
    "lessons": "03",
    "resources": "04",
    "archives": "05",
}

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

# Onde cada tipo de nota nasce. `task` fica de fora: mora dentro do projeto.
KIND_FOLDER = {
    "dump": "dump",
    "project": "projects",
    "lesson": "lessons",
    "knowledge": "knowledge",
}

# Seções da Daily onde `log` pode inserir entradas. Devem bater com os
# cabeçalhos `## ...` do `daily-template.md` do vault. `Pendentes` fica de fora
# de propósito: lá vão checkboxes de tarefa, não registro de nota tocada.
DAILY_SECTIONS = ["Projetos", "Aprendizados", "Outras notas"]

# Nomes antigos de seção que ainda existem em daily já escritas. Sem isso, uma
# daily criada quando a seção se chamava "Outros" ganharia uma segunda seção em
# vez de receber a entrada na que já está lá.
SECTION_ALIASES = {"Outras notas": ("outras notas", "outros")}

# Linhas de exemplo dos templates que devem sair quando entra conteúdo real.
PLACEHOLDER_LINES = {
    "- wikilink - síntese da adição/modificação",
    "- outras informações sobre o dia",
    "- wikilinks",
    "- wikilinks para as notas de lessons/ e knowledge/ que este projeto rendeu.",
    "- yyyy-mm-dd: síntese do progresso. → [[slug-da-task|título da task]]",
    "- yyyy-mm-dd: **decisão** — motivo.",
    "-",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

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
    names = sorted(os.listdir(vault))
    for name in names:
        if os.path.isdir(os.path.join(vault, name)) and name.strip().lower() == role:
            return os.path.join(vault, name)
    prefix = LEGACY_PREFIX.get(role)
    if prefix:
        for name in names:
            full = os.path.join(vault, name)
            if os.path.isdir(full) and name.strip().startswith(prefix):
                return full
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


def stamp(text: str, key: str, value: str) -> str:
    """Preenche uma chave do frontmatter, se ela existir no template.

    Nunca cria a chave: o template do vault decide quais campos existem em
    cada tipo de nota — o Dump, por exemplo, não tem `skill_version`.
    """
    return re.sub(rf"(?m)^{re.escape(key)}:.*$", lambda _m: f"{key}: {value}", text, count=1)


def render_template(text: str, date: str, title: str = "") -> str:
    """Preenche os campos que o script sabe responder sozinho.

    Estampar aqui é deliberado: são os campos que não dependem de o modelo
    lembrar de preenchê-los. `llm_model_used` fica de fora — só o modelo sabe.
    """
    text = stamp(text, "created", date)
    text = stamp(text, "skill_version", f'"{SKILL_VERSION}"')
    if title:
        text = stamp(text, "title", title)
    return text


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


def cmd_slug(args):
    print(slugify(args.text))


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


def cmd_template(args):
    """Imprime o template do vault já renderizado (útil para criar notas)."""
    print(render_template(load_template(args.vault, args.kind), args.date, args.title), end="")


# --- Criação de notas --------------------------------------------------------


def project_main(vault: str, project_slug: str) -> str:
    """Caminho da nota principal de um projeto: `projects/<slug>/<slug>.md`."""
    path = os.path.join(resolve_folder(vault, "projects"), project_slug, f"{project_slug}.md")
    if not os.path.isfile(path):
        sys.exit(f"[erro] projeto '{project_slug}' não encontrado (esperado: {path}).")
    return path


def _write_new(path: str, body: str):
    if os.path.exists(path):
        sys.exit(f"[erro] já existe: {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(path)


def _append_to_section(path: str, section: str, entry: str):
    """Insere uma linha no fim da seção, tirando os placeholders do template."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    start, end = _section_bounds(lines, section)
    if start is None:
        sys.exit(f"[erro] seção '{section}' não encontrada em {path}.")
    body = [
        ln for ln in lines[start:end]
        if ln.strip() and ln.strip().lower() not in PLACEHOLDER_LINES
    ]
    body.append(entry)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines[:start] + body + [""] + lines[end:]).rstrip("\n") + "\n")


def cmd_new(args):
    """Cria a nota no lugar certo, com slug canônico e links já montados."""
    title = args.title.strip()
    note_slug = slugify(title)
    if not note_slug:
        sys.exit(f"[erro] título não gera um slug válido: '{title}'")

    if args.project and args.kind != "task":
        sys.exit(f"[erro] --project só vale para `new task` (recebido em `new {args.kind}`).")

    if args.kind == "task":
        if not args.project:
            sys.exit("[erro] `new task` exige --project <slug do projeto>.")
        main = project_main(args.vault, args.project)
        proj_title = note_title(main, args.project)
        task_slug = f"{args.date}-{note_slug}"
        body = render_template(load_template(args.vault, "task"), args.date, title)
        body = stamp(body, "project", f'"{wikilink(args.project, proj_title)}"')
        _write_new(os.path.join(os.path.dirname(main), "tasks", f"{task_slug}.md"), body)
        if not args.no_progress:
            synthesis = args.progress or title
            _append_to_section(
                main, "Progresso",
                f"- {args.date}: {synthesis} → {wikilink(task_slug, title)}",
            )
            print(f"[ok] progresso registrado em {os.path.relpath(main, args.vault)}")
        return

    body = render_template(load_template(args.vault, args.kind), args.date, title)
    folder = resolve_folder(args.vault, KIND_FOLDER[args.kind])
    if args.kind == "project":
        path = os.path.join(folder, note_slug, f"{note_slug}.md")
        os.makedirs(os.path.join(folder, note_slug, "tasks"), exist_ok=True)
    else:
        path = os.path.join(folder, f"{note_slug}.md")
    _write_new(path, body)


# --- Daily -------------------------------------------------------------------


def daily_path(vault: str, date: str) -> str:
    return os.path.join(resolve_folder(vault, "daily"), f"{date}.md")


def ensure_daily(vault: str, date: str) -> str:
    """Garante que a nota do dia exista, criada a partir do `daily-template.md` do vault."""
    path = daily_path(vault, date)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = render_template(load_template(vault, "daily"), date)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
    return path


def cmd_daily(args):
    print(ensure_daily(args.vault, args.date))


def _section_bounds(lines, section: str):
    """Retorna (inicio, fim) das linhas de conteúdo sob o cabeçalho `## <section>`.

    `inicio` já pula a linha separadora `---` logo abaixo do cabeçalho, se houver.
    Retorna (None, None) se a seção não existe no arquivo.
    """
    names = SECTION_ALIASES.get(section, (section.lower(),))
    targets = {f"## {n}" for n in names}
    hdr = next((i for i, ln in enumerate(lines) if ln.strip().lower() in targets), None)
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


def resolve_note(vault: str, term: str):
    """Resolve um termo (slug, título ou alias) em (slug, título) da nota."""
    term_l = term.lower().strip()
    term_slug = slugify(term)
    for path, note_slug in iter_notes(vault):
        title = note_title(path, note_slug)
        names = [note_slug.lower(), title.lower()] + [a.lower() for a in read_aliases(path)]
        if term_l in names or term_slug == note_slug.lower():
            return note_slug, title
    return term_slug, term


def cmd_log(args):
    """Registra `- [[slug|Título]] — descrição` na seção pedida da Daily, sem duplicar."""
    path = ensure_daily(args.vault, args.date)
    note_slug, title = resolve_note(args.vault, args.title)
    entry = f"- {wikilink(note_slug, title)}"
    if args.description:
        entry += f" — {args.description}"

    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    # dedupe: se já existe uma linha para essa mesma nota em qualquer seção, não repete
    if re.search(rf"(?m)^- \[\[{re.escape(note_slug)}[\]|]", content):
        print(f"[ok] entrada para [[{note_slug}]] já existe na Daily de {args.date} — nada a fazer.")
        return

    lines = content.splitlines()
    start, end = _section_bounds(lines, args.section)

    if start is None:
        # o template do vault não tem essa seção — anexa uma no fim
        block = ["", f"## {args.section}", "---", entry]
        new = "\n".join(lines + block).rstrip("\n") + "\n"
    else:
        body = [
            ln for ln in lines[start:end]
            if ln.strip() and ln.strip().lower() not in PLACEHOLDER_LINES
        ]
        body.append(entry)
        new = "\n".join(lines[:start] + body + [""] + lines[end:]).rstrip("\n") + "\n"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"[ok] registrado na Daily de {args.date} (seção {args.section}): {entry}")


def cmd_version(args):
    print(SKILL_VERSION)


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


def strip_code(text: str) -> str:
    """Remove blocos e trechos de código antes de procurar links.

    `[[slug|Título]]` escrito entre crases é exemplo de sintaxe, e o Obsidian
    também não o trata como link — o lint não pode reclamar de link quebrado ali.
    """
    text = re.sub(r"(?ms)^\s{0,3}(?:```|~~~).*?^\s{0,3}(?:```|~~~)\s*$", "", text)
    return re.sub(r"`[^`\n]*`", "", text)


def cmd_lint(args):
    """Aponta o que está fora do padrão: nomenclatura, frontmatter e links."""
    vault = args.vault
    issues, pending = [], []
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

        kind = read_frontmatter_value(path, "type")
        if kind in ("project", "task", "lesson", "knowledge") and not read_frontmatter_value(path, "title"):
            issues.append((rel, "frontmatter sem `title`"))
        if kind in ("project", "lesson", "knowledge") and not read_frontmatter_list(path, "tags"):
            issues.append((rel, "frontmatter sem `tags`"))
        if kind == "task" and not read_frontmatter_value(path, "project"):
            issues.append((rel, "task sem `project`"))

        with open(path, encoding="utf-8") as fh:
            body = strip_code(fh.read())
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
# aqui é densidade textual: cortar redundância é julgamento, e mora no SKILL.md.

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


def split_frontmatter(text: str):
    """Separa o frontmatter YAML do corpo. O frontmatter nunca é reformatado."""
    m = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(0), text[m.end():]


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


# --- Versionamento -----------------------------------------------------------


def _git(vault: str, *argv: str):
    """Roda um comando git dentro do vault e devolve o resultado."""
    return subprocess.run(["git", "-C", vault, *argv], capture_output=True, text=True)


def cmd_commit(args):
    """Versiona de uma vez tudo que a sessão mexeu no vault.

    É um commit por sessão, no fim de todas as edições — nunca um por nota:
    uma anotação costuma tocar várias notas (a nota em si, o projeto, a Daily),
    e commitar cada uma separada quebraria em pedaços algo que só faz sentido
    junto. A mensagem é só o timestamp `yyyy-mm-dd-hh-mm-ss`, porque o histórico
    do vault é uma linha do tempo — o "o quê" de cada dia já está na Daily.
    """
    vault = args.vault
    if not os.path.isdir(vault):
        sys.exit(f"[erro] vault não encontrado: {vault}")

    if _git(vault, "rev-parse", "--is-inside-work-tree").returncode != 0:
        sys.exit(
            f"[erro] o vault não é um repositório git: {vault}\n"
            f'       rode `git -C "{vault}" init` antes de versionar.'
        )

    add = _git(vault, "add", "-A")
    if add.returncode != 0:
        sys.exit(f"[erro] git add falhou: {add.stderr.strip()}")

    if _git(vault, "diff", "--cached", "--quiet").returncode == 0:
        print("[ok] nada a commitar — o vault já está versionado.")
        return

    files = [f for f in _git(vault, "diff", "--cached", "--name-only").stdout.splitlines() if f]
    message = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    commit = _git(vault, "commit", "-m", message)
    if commit.returncode != 0:
        sys.exit(f"[erro] git commit falhou: {(commit.stderr or commit.stdout).strip()}")

    short = _git(vault, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"[ok] commit {short} ({message}) — {len(files)} arquivo(s):")
    for f in files:
        print(f"  {f}")


def cmd_folder(args):
    print(resolve_folder(args.vault, args.role))


def cmd_tree(args):
    for role in FOLDER_ROLE:
        try:
            full = resolve_folder(args.vault, role)
        except SystemExit:
            print(f"{role:12} (pasta ausente)")
            continue
        n = sum(1 for _ in iter_notes(full))
        extra = ""
        if role == "projects":
            projects = [d for d in sorted(os.listdir(full)) if os.path.isdir(os.path.join(full, d))]
            tasks = sum(
                len([f for f in os.listdir(os.path.join(full, d, "tasks")) if f.endswith(".md")])
                for d in projects
                if os.path.isdir(os.path.join(full, d, "tasks"))
            )
            extra = f" — {len(projects)} projeto(s), {tasks} task(s)"
        print(f"{os.path.basename(full):12} — {n} nota(s){extra}")


def today() -> str:
    return dt.date.today().isoformat()


def main():
    p = argparse.ArgumentParser(description="Utilitário do vault second brain.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("slug", help="imprime o slug canônico de um título")
    sp.add_argument("text")
    sp.set_defaults(func=cmd_slug)

    sp = sub.add_parser("find", help="procura nota existente por slug/título/alias")
    sp.add_argument("vault")
    sp.add_argument("term")
    sp.set_defaults(func=cmd_find)

    sp = sub.add_parser("new", help="cria uma nota nova no lugar certo")
    sp.add_argument("vault")
    sp.add_argument("kind", choices=["project", "task", "lesson", "knowledge", "dump"])
    sp.add_argument("title")
    sp.add_argument("--project", default="", help="slug do projeto (obrigatório em task)")
    sp.add_argument("--progress", default="", help="síntese do bullet de Progresso (task)")
    sp.add_argument("--no-progress", action="store_true", help="não registra o bullet no projeto")
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_new)

    sp = sub.add_parser("template", help="imprime um template do vault já renderizado")
    sp.add_argument("vault")
    sp.add_argument("kind", choices=sorted(TEMPLATE_FILE))
    sp.add_argument("--title", default="")
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_template)

    sp = sub.add_parser("daily", help="garante/abre a nota do dia (a partir do template do vault)")
    sp.add_argument("vault")
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_daily)

    sp = sub.add_parser("log", help="registra uma entrada na Daily")
    sp.add_argument("vault")
    sp.add_argument("title")
    sp.add_argument("description", nargs="?", default="")
    sp.add_argument("--section", choices=DAILY_SECTIONS, default=DAILY_SECTIONS[-1])
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_log)

    sp = sub.add_parser("version", help="imprime a versão da skill")
    sp.set_defaults(func=cmd_version)

    sp = sub.add_parser("tags", help="lista o vocabulário de tags em uso")
    sp.add_argument("vault")
    sp.add_argument("term", nargs="?", default="")
    sp.set_defaults(func=cmd_tags)

    sp = sub.add_parser("fmt", help="normaliza a formatação das notas (unwrap + divider)")
    sp.add_argument("target", help="arquivo .md, pasta do vault ou o vault inteiro")
    sp.add_argument("--check", action="store_true", help="só relata o que está fora do padrão")
    sp.set_defaults(func=cmd_fmt)

    sp = sub.add_parser("lint", help="aponta nomenclatura, frontmatter e links fora do padrão")
    sp.add_argument("vault")
    sp.set_defaults(func=cmd_lint)

    sp = sub.add_parser("commit", help="versiona o vault num commit único (fim da sessão)")
    sp.add_argument("vault")
    sp.set_defaults(func=cmd_commit)

    sp = sub.add_parser("folder", help="resolve a pasta pelo papel (dump, projects, lessons…)")
    sp.add_argument("vault")
    sp.add_argument("role", choices=FOLDER_ROLE)
    sp.set_defaults(func=cmd_folder)

    sp = sub.add_parser("tree", help="visão rápida da estrutura")
    sp.add_argument("vault")
    sp.set_defaults(func=cmd_tree)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
