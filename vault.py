#!/usr/bin/env python3
"""Utilitário para o vault "second brain" do Obsidian.

Cuida das partes deterministas e chatas do fluxo, para que o Claude não
reinvente essa lógica (e não erre) a cada anotação:

  - resolver as pastas numeradas do vault de forma tolerante a variações
  - achar se já existe uma nota para um conceito (evitar duplicar)
  - garantir/abrir a nota do dia (Daily)
  - registrar uma entrada na Daily sem duplicar linhas

Sem dependências externas — só a biblioteca padrão do Python 3.

Uso:
  python vault.py find   <vault> "<termo>"
  python vault.py daily  <vault> [--date YYYY-MM-DD]
  python vault.py log    <vault> "<Título da nota>" "<descrição curta>" [--date YYYY-MM-DD]
  python vault.py folder <vault> <NN>          # imprime o caminho da pasta pelo prefixo (00..05)
  python vault.py tree   <vault>               # visão rápida da estrutura
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


def iter_notes(vault: str):
    """Gera (caminho, título) de toda nota .md do vault."""
    for root, _dirs, files in os.walk(vault):
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


def daily_path(vault: str, date: str) -> str:
    return os.path.join(resolve_folder(vault, "01"), f"{date}.md")


def ensure_daily(vault: str, date: str) -> str:
    """Garante que a nota do dia exista; cria a partir de um template mínimo."""
    path = daily_path(vault, date)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        template = (
            f"---\n"
            f"type: daily\n"
            f"created: {date}\n"
            f"---\n\n"
            f"# {date}\n\n"
            f"## Adicionado / Atualizado\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(template)
    return path


def cmd_daily(args):
    print(ensure_daily(args.vault, args.date))


def cmd_log(args):
    """Registra `- [[Título]] — descrição` na Daily, sem duplicar a linha."""
    path = ensure_daily(args.vault, args.date)
    entry = f"- [[{args.title}]]"
    if args.description:
        entry += f" — {args.description}"

    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    # dedupe: se já existe uma linha para esse mesmo título, não repete
    if re.search(rf"^- \[\[{re.escape(args.title)}\]\]", content, re.MULTILINE):
        print(f"[ok] entrada para [[{args.title}]] já existe na Daily de {args.date} — nada a fazer.")
        return

    heading = "## Adicionado / Atualizado"
    if heading in content:
        content = content.rstrip("\n") + "\n" + entry + "\n"
    else:
        content = content.rstrip("\n") + f"\n\n{heading}\n{entry}\n"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"[ok] registrado na Daily de {args.date}: {entry}")


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

    sp = sub.add_parser("daily", help="garante/abre a nota do dia")
    sp.add_argument("vault")
    sp.add_argument("--date", default=today())
    sp.set_defaults(func=cmd_daily)

    sp = sub.add_parser("log", help="registra uma entrada na Daily")
    sp.add_argument("vault")
    sp.add_argument("title")
    sp.add_argument("description", nargs="?", default="")
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
