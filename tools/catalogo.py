#!/usr/bin/env python3
"""Catalogs of translations for Dash programs (dashweb D71), without FlexCat.

    tools/catalogo.py cd programa.dash ventana.dashui ... -o Programa.cd
    tools/catalogo.py ct Programa.cd --language english --name Programa.catalog [--version 1.0] \\
                         [--update english.ct] -o english.ct
    tools/catalogo.py catalog english.ct [-o Catalogs/english/Programa.catalog]

cd: the texts of the program, from its tr(id, "text") calls (id a number or a const) and the "tr" ids of its
.dashui files, in FlexCat's descriptor format (one MSG_x (id//) line and its text each). ct: a translation
file for a language, the texts to translate empty with the original below as a comment (--update keeps the
translations of an older one). catalog: an IFF CTLG file for locale.library, in Latin-1 (as the program's
own texts): $VER, language, code set and the strings by number. Texts keep the escapes of a Dash string
(\\n, \\t, \\", \\\\, \\e or \\033 ESC, \\xNN).
"""
import argparse
import datetime
import json
import re
import struct
import sys
from pathlib import Path

_CONST = re.compile(r"^\s*const\s+([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*$", re.M)
_TR = re.compile(r'\btr\(\s*(0x[0-9A-Fa-f]+|\d+|[A-Za-z_]\w*)\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compiler.dashui import _MAIN_TEXT   # noqa: E402  (the text a .dashui "tr" number goes with)


class CatalogError(Exception):
    pass


def _number(text):
    return int(text, 16) if text.lower().startswith("0x") else int(text)


def dash_texts(source: str, where: str, consts: dict):
    """(id, text as written, name or None) of each tr(id, "text") of a Dash source"""
    for m in _TR.finditer(source):
        key = m.group(1)
        if key[0].isdigit():
            yield _number(key), m.group(2), None
        elif key in consts:
            yield consts[key], m.group(2), key
        else:
            raise CatalogError(f"{where}: tr({key}, ...): {key} is not a const with a number")


def _escape(text: str) -> str:
    """A text of a .dashui as a Dash string has it (what the .cd keeps)"""
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 32 or ord(ch) == 127:
            out.append("\\%03o" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def dashui_texts(doc: dict, where: str):
    """(id, text, None) of each "tr" of a .dashui"""
    def ids(node, kind):
        tr = node.get("tr")
        if tr is None:
            return {}
        if isinstance(tr, bool) or not isinstance(tr, (int, dict)):
            raise CatalogError(f"{where}: \"tr\" must be a number or {{\"field\": number}}: {tr!r}")
        if isinstance(tr, int):
            field = _MAIN_TEXT.get(kind)
            if not field:
                raise CatalogError(f"{where}: a {kind!r} has no text for \"tr\": {tr}")
            return {field: tr}
        return tr

    def emit(node, kind):
        for field, number in ids(node, kind).items():
            if isinstance(number, bool) or not isinstance(number, int):
                raise CatalogError(f"{where}: \"tr\" of {field!r} must be a number: {number!r}")
            default = node.get("name", "") if field == "title" and kind == "window" else ""
            yield number, _escape(str(node.get(field, default))), None

    def walk(node):
        if not isinstance(node, dict):
            return
        yield from emit(node, node.get("type", ""))
        for child in node.get("children", []):
            yield from walk(child)

    for win in doc.get("windows", []):
        yield from emit(win, "window")
        for menu in win.get("menus", []):
            yield from emit(menu, "menu")
            for item in menu.get("items", []):
                if not item.get("separator"):
                    yield from emit(item, "item")
                    for sub in item.get("submenu", []):   # (Lorraine D47)
                        if not sub.get("separator"):
                            yield from emit(sub, "item")
        if win.get("root"):
            yield from walk(win["root"])


def collect(files):
    """{id: (text, name)} of the program: its files and the .dashui files they import"""
    texts, consts, seen = {}, {}, set()
    sources = []
    queue = [Path(f) for f in files]
    while queue:
        f = queue.pop(0).resolve()
        if f in seen:
            continue
        seen.add(f)
        if f.suffix == ".dashui":
            sources.append((f, None))
            continue
        src = f.read_text(encoding="utf-8")
        sources.append((f, src))
        consts.update((m.group(1), _number(m.group(2))) for m in _CONST.finditer(src))
        for m in re.finditer(r'^\s*import\s+"([^"]+)"', src, re.M):
            queue.append(f.parent / m.group(1))
    for f, src in sources:
        found = (dashui_texts(json.loads(f.read_text(encoding="utf-8")), str(f)) if src is None
                 else dash_texts(src, str(f), consts))
        for number, text, name in found:
            if number in texts and texts[number][0] != text:
                raise CatalogError(f"{f}: number {number} is already \"{texts[number][0]}\", not \"{text}\"")
            if number not in texts or (name and not texts[number][1]):
                texts[number] = (text, name)
    return texts


def write_cd(texts: dict, sources) -> str:
    """Each text as MSG_<number> (the const that names it, if any, in a comment above)"""
    lines = [f"; Texts of {', '.join(str(s) for s in sources)} (tools/catalogo.py)", ";"]
    for number in sorted(texts):
        text, name = texts[number]
        if name:
            lines.append(f"; {name}")
        lines += [f"MSG_{number} ({number}//)", text]
    return "\n".join(lines) + "\n"


def read_cd(text: str):
    """[(name, id, text)] of a .cd"""
    out, lines = [], [l for l in text.splitlines() if l.strip() and not l.startswith(";") and not l.startswith("#")]
    for i in range(0, len(lines) - 1, 2):
        m = re.match(r"^(\w+)\s*\((\d+)/\d*/\d*\)\s*$", lines[i])
        if not m:
            raise CatalogError(f"not a .cd line: {lines[i]!r}")
        out.append((m.group(1), int(m.group(2)), lines[i + 1]))
    return out


def read_ct(text: str):
    """(header {version, language, codeset}, {name: translation}) of a .ct"""
    head, trans, name = {}, {}, None
    for line in text.splitlines():
        if line.startswith("##"):
            key, _, value = line[2:].strip().partition(" ")
            head[key.lower()] = value.strip()
        elif line.startswith(";"):
            continue
        elif name is None:
            if line.strip():
                name = line.strip()
        elif re.match(r"^MSG_\d+\s*$", line):   # (its translation line was taken away: not translated)
            trans[name] = ""
            name = line.strip()
        else:
            trans[name] = line
            name = None
    return head, trans


def write_ct(cd, language, catalog_name, version, old=None) -> str:
    today = datetime.date.today().strftime("%d.%m.%Y")
    lines = [f"## version $VER: {catalog_name} {version} ({today})", f"## language {language}", "## codeset 0", ";"]
    for name, number, text in cd:
        lines += [name, (old or {}).get(name, ""), f"; {text}"]
    return "\n".join(lines) + "\n"


def unescape(text: str) -> str:
    out, i = [], 0
    simple = {"n": "\n", "t": "\t", "r": "\r", "e": "\x1b", "a": "\a", "b": "\b", "f": "\f", "v": "\v",
              "\\": "\\", '"': '"', "'": "'"}
    while i < len(text):
        ch = text[i]
        if ch != "\\" or i + 1 == len(text):
            out.append(ch)
            i += 1
            continue
        nxt = text[i + 1]
        if nxt in simple:
            out.append(simple[nxt])
            i += 2
        elif nxt == "x" and re.match(r"[0-9A-Fa-f]{2}", text[i + 2:i + 4]):
            out.append(chr(int(text[i + 2:i + 4], 16)))
            i += 4
        elif nxt in "01234567":
            m = re.match(r"[0-7]{1,3}", text[i + 1:])
            out.append(chr(int(m.group(0), 8)))
            i += 1 + len(m.group(0))
        else:
            out.append(nxt)
            i += 2
    return "".join(out)


def _chunk(cid: bytes, data: bytes) -> bytes:
    return cid + struct.pack(">I", len(data)) + data + (b"\0" if len(data) & 1 else b"")


def build_catalog(ct_text: str) -> tuple:
    """(catalog name, language, bytes) of a .ct: IFF FORM CTLG with FVER, LANG, CSET and STRS (each string:
    its number, its length with the ending 0, the bytes and 0s up to a multiple of 4)"""
    head, trans = read_ct(ct_text)
    ver = head.get("version", "")
    m = re.match(r"\$VER:\s+(\S+)\s+(\d+)\.(\d+)", ver)
    if not m:
        raise CatalogError(f"## version must be \"$VER: Name.catalog 1.0 (date)\", not {ver!r}")
    language = head.get("language")
    if not language:
        raise CatalogError("## language is missing")
    strings = []
    for name, value in trans.items():
        if not value:
            continue                       # not translated: the program's own text
        if not re.match(r"^MSG_\d+$", name):
            raise CatalogError(f"{name}: messages are MSG_<number>")
        number = int(name[4:])
        strings.append((number, unescape(value).encode("latin-1", errors="replace")))
    strs = b""
    for number, data in sorted(strings):
        data += b"\0"
        strs += struct.pack(">II", number, len(data)) + data + b"\0" * (-len(data) % 4)
    body = (b"CTLG" + _chunk(b"FVER", ver.encode("latin-1", errors="replace") + b"\0")
            + _chunk(b"LANG", language.encode("latin-1", errors="replace") + b"\0")
            + _chunk(b"CSET", b"\0" * 32) + _chunk(b"STRS", strs))
    return m.group(1), language, b"FORM" + struct.pack(">I", len(body)) + body


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("cd", help="the texts of the program, as a .cd")
    a.add_argument("files", nargs="+")
    a.add_argument("-o", "--output", required=True)
    a = sub.add_parser("ct", help="a .ct to translate, for a language")
    a.add_argument("cd")
    a.add_argument("--language", required=True)
    a.add_argument("--name", required=True, help="the catalog's name (Programa.catalog)")
    a.add_argument("--version", default="1.0")
    a.add_argument("--update", help="an older .ct whose translations are kept")
    a.add_argument("-o", "--output", required=True)
    a = sub.add_parser("catalog", help="a .ct compiled for locale.library")
    a.add_argument("ct")
    a.add_argument("-o", "--output", help="default: Catalogs/<language>/<name>")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "cd":
            texts = collect(args.files)
            Path(args.output).write_text(write_cd(texts, args.files), encoding="utf-8")
            print(f"{args.output}: {len(texts)} texts")
        elif args.cmd == "ct":
            cd = read_cd(Path(args.cd).read_text(encoding="utf-8"))
            old = read_ct(Path(args.update).read_text(encoding="utf-8"))[1] if args.update else None
            Path(args.output).write_text(write_ct(cd, args.language, args.name, args.version, old), encoding="utf-8")
            print(f"{args.output}: {len(cd)} texts to translate")
        else:
            name, language, data = build_catalog(Path(args.ct).read_text(encoding="utf-8"))
            out = Path(args.output) if args.output else Path("Catalogs") / language / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"{out}: {len(data)} bytes")
    except (CatalogError, OSError, json.JSONDecodeError) as e:
        print(f"catalogo.py: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
