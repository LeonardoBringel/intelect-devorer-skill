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
  python vault.py template <vault> <daily|dump|knowledge|project> [--date YYYY-MM-DD]
  python vault.py daily    <vault> [--date YYYY-MM-DD]
  python vault.py log      <vault> "<Título da nota>" "<descrição curta>" [--section Projetos|Aprendizados|Outros] [--date YYYY-MM-DD]
  python vault.py folder   <vault> <NN>          # imprime o caminho da pasta pelo prefixo (00..05)
  python vault.py tree     <vault>               # visão rápida da estrutura
"""

import argparse
import datetime as dt
import os
import re
import sys

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
# cabeçalhos `## ...` do `Daily Template.md` do vault.
DAILY_SECTIONS = ["Projetos", "Aprendizados", "Outros"]

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
    """Ajusta o `created:` do frontmatter para a data alvo. O resto fica como está."""
    return re.sub(r"(?m)^created:.*$", f"created: {date}", text, count=1)


def _templates_dir_or_none(vault: str):
    for name in os.listdir(vault):
        full = os.path.join(vault, name)
        if os.path.isdir(full) and name.strip().lower() == "templates":
            return os.path.normpath(full)
    return None


def iter_notes(vault: str):
    """Gera (caminho, título) de toda nota .md do vault, exceto os templates."""
    tdir = _templates_dir_or_none(vault)
    for root, _dirs, files in os.walk(vault):
        if tdir is not None and os.path.normpath(root) == tdir:
            continue
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f), f[:-3]


def read_aliases(path: str):
    """Lê o campo `aliases` do frontmatter, se houver."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    aliases = []
    # aliases: [a, b]  |  aliases:\n  - a\n  - b
    inline = re.search(r"^aliases:\s*\[(.*?)\]", block, re.MULTILINE)
    if inline:
        aliases += [a.strip().strip("\"'") for a in inline.group(1).split(",") if a.strip()]
    listform = re.findall(r"^\s*-\s*(.+)$", block, re.MULTILINE)
    # só considera itens de lista que estejam sob "aliases:"
    if re.search(r"^aliases:\s*$", block, re.MULTILINE):
        aliases += [a.strip().strip("\"'") for a in listform]
    return [a for a in aliases if a]


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
    target = f"## {section}".lower()
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
    sp.add_argument("--section", choices=DAILY_SECTIONS, default="Outros")
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_log)

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
