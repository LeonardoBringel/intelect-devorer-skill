#!/usr/bin/env python3
"""Utilitário para o vault "second brain" do Obsidian.

Cuida das partes deterministas e chatas do fluxo, para que o Claude não
reinvente essa lógica (e não erre) a cada anotação:

  - resolver as pastas numeradas do vault de forma tolerante a variações
  - achar se já existe uma nota para um conceito (evitar duplicar)
  - renderizar um template do vault (a fonte de verdade dos templates)
  - garantir/abrir a nota do dia (Daily), sempre a partir do template do vault
  - registrar uma entrada na Daily sem duplicar linhas

Os templates NÃO são definidos aqui. Este script sempre lê os arquivos em
`<vault>/templates/` — assim a estrutura das notas fica sob controle do
usuário, no próprio Obsidian, e nunca conflita com o que o script gera.

Sem dependências externas — só a biblioteca padrão do Python 3.

Uso:
  python vault.py find     <vault> "<termo>"
  python vault.py fmt      <arquivo|pasta|vault> [--check]   # normaliza a forma das notas
  python vault.py tags     <vault> ["<termo>"]   # vocabulário de tags já em uso
  python vault.py template <vault> <daily|dump|knowledge|project> [--date YYYY-MM-DD]
  python vault.py daily    <vault> [--date YYYY-MM-DD]
  python vault.py log      <vault> "<Título da nota>" "<descrição curta>" [--section Projetos|Aprendizados|"Outras notas"] [--date YYYY-MM-DD]
  python vault.py folder   <vault> <NN>          # imprime o caminho da pasta pelo prefixo (00..05)
  python vault.py tree     <vault>               # visão rápida da estrutura
  python vault.py version                        # versão da skill (vai pro frontmatter)
"""

import argparse
import datetime as dt
import difflib
import os
import re
import sys

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
SKILL_VERSION = "0.3.0"

# Prefixo numérico -> apelido lógico. O nome exato ("00 - Dump") pode variar
# um pouco entre vaults, então resolvemos pela numeração, que é estável.
FOLDER_ROLE = {
    "00": "dump",
    "01": "daily",
    "02": "projects",
    "03": "knowledge",
    "04": "resources",
    "05": "archives",
}

# Tipos de nota -> nome do arquivo de template dentro de `<vault>/templates/`.
# A correspondência é case-insensitive na hora de procurar.
TEMPLATE_FILE = {
    "daily": "Daily Template.md",
    "dump": "Dump Template.md",
    "knowledge": "Knowledge Template.md",
    "project": "Project Template.md",
}

# Seções da Daily onde `log` pode inserir entradas. Devem bater com os
# cabeçalhos `## ...` do `Daily Template.md` do vault. `Pendentes` fica de fora
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
}


def resolve_folder(vault: str, prefix: str) -> str:
    """Acha a pasta cujo nome começa com o prefixo numérico dado (ex: '01')."""
    if not os.path.isdir(vault):
        sys.exit(f"[erro] vault não encontrado: {vault}")
    for name in sorted(os.listdir(vault)):
        full = os.path.join(vault, name)
        if os.path.isdir(full) and name.strip().startswith(prefix):
            return full
    sys.exit(
        f"[erro] não encontrei a pasta com prefixo '{prefix}' em {vault}. "
        f"O vault segue a estrutura 00..05?"
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
            f"Use um de: {', '.join(TEMPLATE_FILE)}"
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


def render_template(text: str, date: str) -> str:
    """Preenche `created:` e `skill_version:` no frontmatter. O resto fica como está.

    Estampar aqui é deliberado: são os campos que o script sabe responder
    sozinho, então não dependem de o modelo lembrar de preenchê-los. Cada
    `sub` só age se a chave existir no template (o Dump, por exemplo, não tem
    `skill_version`) — nunca inventamos campo que o template do vault não pede.
    """
    text = re.sub(r"(?m)^created:.*$", f"created: {date}", text, count=1)
    text = re.sub(
        r"(?m)^skill_version:.*$", f'skill_version: "{SKILL_VERSION}"', text, count=1
    )
    return text


def _templates_dir_or_none(vault: str):
    for name in os.listdir(vault):
        full = os.path.join(vault, name)
        if os.path.isdir(full) and name.strip().lower() == "templates":
            return os.path.normpath(full)
    return None


def iter_notes(vault: str):
    """Gera (caminho, título) de toda nota .md do vault, exceto os templates.

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


def read_frontmatter_list(path: str, key: str):
    """Lê um campo de lista do frontmatter (`aliases`, `tags`…), se houver.

    Aceita as duas formas que o Obsidian escreve:  `key: [a, b]`  e
    `key:` seguido de itens `  - a`. Os itens só contam até a próxima chave
    do frontmatter, para que `tags:` e `aliases:` não se misturem.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return []

    values = []
    lines = m.group(1).splitlines()
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


def cmd_find(args):
    """Procura notas cujo título ou alias case com o termo (case-insensitive)."""
    term = args.term.lower().strip()
    exact, partial = [], []
    for path, title in iter_notes(args.vault):
        names = [title.lower()] + [a.lower() for a in read_aliases(path)]
        rel = os.path.relpath(path, args.vault)
        if term in names:
            exact.append((title, rel))
        elif any(term in n for n in names):
            partial.append((title, rel))
    if exact:
        print("EXATO:")
        for title, rel in exact:
            print(f"  [[{title}]]  ->  {rel}")
    if partial:
        print("PARCIAL:")
        for title, rel in partial:
            print(f"  [[{title}]]  ->  {rel}")
    if not exact and not partial:
        print("NENHUMA nota encontrada — provavelmente é uma nota nova a criar.")


def cmd_template(args):
    """Imprime o template do vault já renderizado (útil para criar notas)."""
    print(render_template(load_template(args.vault, args.kind), args.date), end="")


def daily_path(vault: str, date: str) -> str:
    return os.path.join(resolve_folder(vault, "01"), f"{date}.md")


def ensure_daily(vault: str, date: str) -> str:
    """Garante que a nota do dia exista, criada a partir do `Daily Template.md` do vault."""
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


def cmd_log(args):
    """Registra `- [[Título]] — descrição` na seção pedida da Daily, sem duplicar."""
    path = ensure_daily(args.vault, args.date)
    entry = f"- [[{args.title}]]"
    if args.description:
        entry += f" — {args.description}"

    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    # dedupe: se já existe uma linha para esse mesmo título em qualquer seção, não repete
    if re.search(rf"(?m)^- \[\[{re.escape(args.title)}\]\]", content):
        print(f"[ok] entrada para [[{args.title}]] já existe na Daily de {args.date} — nada a fazer.")
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
    for path, _title in iter_notes(args.vault):
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
        return sorted(path for path, _title in iter_notes(target))
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


def cmd_folder(args):
    print(resolve_folder(args.vault, args.prefix))


def cmd_tree(args):
    for prefix, role in FOLDER_ROLE.items():
        try:
            full = resolve_folder(args.vault, prefix)
            n = sum(1 for _ in iter_notes(full))
            print(f"{os.path.basename(full):24} ({role:10}) — {n} nota(s)")
        except SystemExit:
            print(f"[{prefix} - {role}]  (pasta ausente)")


def today() -> str:
    return dt.date.today().isoformat()


def main():
    p = argparse.ArgumentParser(description="Utilitário do vault second brain.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("find", help="procura nota existente por título/alias")
    sp.add_argument("vault")
    sp.add_argument("term")
    sp.set_defaults(func=cmd_find)

    sp = sub.add_parser("template", help="imprime um template do vault já renderizado")
    sp.add_argument("vault")
    sp.add_argument("kind", choices=sorted(TEMPLATE_FILE))
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

    sp = sub.add_parser("folder", help="resolve pasta pelo prefixo (00..05)")
    sp.add_argument("vault")
    sp.add_argument("prefix")
    sp.set_defaults(func=cmd_folder)

    sp = sub.add_parser("tree", help="visão rápida da estrutura")
    sp.add_argument("vault")
    sp.set_defaults(func=cmd_tree)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
