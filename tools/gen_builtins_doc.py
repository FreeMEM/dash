#!/usr/bin/env python3
"""Generate docs/BUILTINS.md (Spanish) and docs/BUILTINS.en.md (English) from compiler/amiga_builtins.py.

Usage:
    python3 tools/gen_builtins_doc.py          # write both files
    python3 tools/gen_builtins_doc.py --check  # exit 1 if either file is out of date
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import compiler.amiga_builtins as builtins_module  # noqa: E402
from compiler.amiga_builtins import BuiltinFunc  # noqa: E402
from compiler.codegen import unimplemented_builtins  # noqa: E402
from compiler.builtins_es import DESC_ES  # noqa: E402
from compiler import builtins_doc  # noqa: E402

OUTPUTS = {"es": PROJECT_ROOT / "docs" / "BUILTINS.md", "en": PROJECT_ROOT / "docs" / "BUILTINS.en.md"}

# (attribute, Spanish title, English title)
GROUPS = [
    ("GRAPHICS_BASIC", "Gráficos básicos", "Basic graphics"),
    ("GRAPHICS_ADVANCED", "Gráficos avanzados", "Advanced graphics"),
    ("INPUT_FUNCTIONS", "Entrada (teclado, ratón, joystick)", "Input (keyboard, mouse, joystick)"),
    ("GADTOOLS_FUNCTIONS", "GadTools", "GadTools"),
    ("MENU_FUNCTIONS", "Menús", "Menus"),
    ("ASL_FUNCTIONS", "Requesters ASL", "ASL requesters"),
    ("REACTION_FUNCTIONS", "ReAction", "ReAction"),
    ("SYSTEM_FUNCTIONS", "Sistema y memoria", "System and memory"),
    ("DOS_FUNCTIONS", "Ficheros (DOS)", "Files (DOS)"),
    ("BUFFER_FUNCTIONS", "Buffers", "Buffers"),
    ("TEXT_FUNCTIONS", "Texto", "Text"),          # dashweb D2
    ("NET_FUNCTIONS", "Red (TCP)", "Network (TCP)"),       # dashweb D8
    ("TLS_FUNCTIONS", "TLS (AmiSSL)", "TLS (AmiSSL)"),    # dashweb D11
    ("FONT_FUNCTIONS", "Fuentes y colores", "Fonts and colors"),  # dashweb D9
    ("BLEND_FUNCTIONS", "Transparencia y degradados", "Transparency and gradients"),
    ("RGB_FUNCTIONS", "Imágenes RGB desde un buffer (vídeo)", "RGB images from a buffer (video)"),
    ("TASK_FUNCTIONS", "Tareas, reloj, traducciones y escritorio", "Tasks, clock, translations and desktop"),
    ("IMAGE_FUNCTIONS", "Imágenes (datatypes)", "Images (datatypes)"),  # dashweb D12
    ("ARGS_FUNCTIONS", "Argumentos", "Arguments"),     # dashweb D19
    ("ZLIB_FUNCTIONS", "Compresión (zlib)", "Compression (zlib)"),  # Lorraine D6
    ("UTF8_FUNCTIONS", "UTF-8", "UTF-8"),              # Lorraine D5
    ("BUFSEARCH_FUNCTIONS", "Comparar y buscar en un búfer", "Comparing and searching in a buffer"),  # Lorraine D38, D39
    ("DOUBLE_FUNCTIONS", "Double y texto", "Double and text"),   # Lorraine D3
    ("MATH_FUNCTIONS", "Matemáticas de Double", "Double math"),   # Lorraine D4
    ("REGEX_FUNCTIONS", "Expresiones regulares y comodines", "Regular expressions and wildcards"),   # Lorraine D45
    ("SIMINPUT_FUNCTIONS", "Simular teclado y ratón", "Simulated keyboard and mouse"),   # Lorraine D46
    ("CLIP_FUNCTIONS", "Portapapeles", "Clipboard"),   # Lorraine D18
    ("COLLATE_FUNCTIONS", "Ordenar textos según el idioma", "Sorting texts by language"),   # Lorraine D7
    ("SYSPROG_FUNCTIONS", "Sistema y programa", "System and program"),   # Dash 2.0
    ("JSON_FUNCTIONS", "JSON leído en C (para lib/json.dash)", "JSON read in C (for lib/json.dash)"),   # Dash 2.0
    ("DEBUGGER_FUNCTIONS", "Depurador (el programa depurado, con dash --debug)",
     "Debugger (the debugged program, built with dash --debug)"),   # Dash 2.0: Forja
    ("IMGDEC_FUNCTIONS", "Imágenes decodificadas por el programa (sin datatypes)",
     "Pictures decoded by the program (no datatypes)"),
    ("TTF_FUNCTIONS", "Fuentes TrueType, WOFF y WOFF2", "TrueType, WOFF and WOFF2 fonts"),
    ("NETBG_FUNCTIONS", "Red en una tarea aparte", "Network in a task of its own"),
    ("OTHERWIN_FUNCTIONS", "Ventanas de otros programas (pruebas)", "Other programs' windows (tests)"),
    ("WM_FUNCTIONS", "Gestor de ventanas (las de todos los programas)", "Window manager (every program's windows)"),
    ("AUDIO_FUNCTIONS", "Audio", "Audio"),
    ("INTUITION_EXPANDED", "Intuition", "Intuition"),
    ("RTG_FUNCTIONS", "RTG (CyberGraphX / Picasso96)", "RTG (CyberGraphX / Picasso96)"),
    ("MUI_FUNCTIONS", "MUI", "MUI"),
    ("DASHOS_FUNCTIONS", "DashOS (solo con ./dash --dashos)", "DashOS (only with ./dash --dashos)"),   # A7
]

# The generator's own texts. The descriptions of the builtins: in English in the code (BUILTINS.en.md), in Spanish in
# compiler/builtins_es.py (BUILTINS.md)
TEXTS = {
    "es": {
        "switch": "*[English](BUILTINS.en.md) | Castellano*",
        "title": "# Funciones built-in",
        "generated": "> Generado por `tools/gen_builtins_doc.py` desde `compiler/amiga_builtins.py`. No editar a mano.",
        "missing": ["Las marcadas **sin implementar** están declaradas pero no tienen código C:",
                    "usarlas da el error `Builtin 'x' is declared but not implemented yet`."],
        "header": "| Función | Devuelve | Descripción | Estado |",
        "unimplemented": "**sin implementar**",
        "total": "Total: {total} funciones, {implemented} implementadas, {missing} sin implementar.",
        "example": "**Ejemplo** (`{path}`: se compila y se prueba en el emulador con los tests):",
        "index": "**Índice.** Las que tienen enlace están explicadas más abajo.",
        "returns": "Devuelve",
        "see": "Ver también",
        "types": {"LONG": "Int", "ULONG": "Int", "BOOL": "Bool", "STRPTR": "String", "double": "Double",
                  "APTR": "Int (dirección)", "DashArrayLong *": "[Int]"},
    },
    "en": {
        "switch": "*English | [Castellano](BUILTINS.md)*",
        "title": "# Built-in functions",
        "generated": "> Generated by `tools/gen_builtins_doc.py` from `compiler/amiga_builtins.py`. Do not edit by hand.",
        "missing": ["The ones marked **not implemented** are declared but have no C code:",
                    "using them gives the error `Builtin 'x' is declared but not implemented yet`."],
        "header": "| Function | Returns | Description | Status |",
        "unimplemented": "**not implemented**",
        "total": "Total: {total} functions, {implemented} implemented, {missing} not implemented.",
        "example": "**Example** (`{path}`: the tests compile it and run it on the emulator):",
        "index": "**Index.** The ones with a link are explained further down.",
        "returns": "Returns",
        "see": "See also",
        "types": {"LONG": "Int", "ULONG": "Int", "BOOL": "Bool", "STRPTR": "String", "double": "Double",
                  "APTR": "Int (address)", "DashArrayLong *": "[Int]"},
    },
}


# lines of a test that are for the runner, not for the reader
RUNNER_LINES = ("# expect", "# emu-", "# ignore-", "# memcheck")


def example(path: str) -> str:
    """The code of a group's example, without the runner's lines"""
    lines = (PROJECT_ROOT / path).read_text().splitlines()
    return "\n".join(line for line in lines if not line.startswith(RUNNER_LINES)).strip("\n")


def details(lang: str, group: dict, t: dict) -> list:
    """The explained functions of a group: a heading with an anchor each, the text and the related ones"""
    out = []
    for name, b in group.items():
        doc = builtins_doc.FUNCS.get(name)
        if not doc:
            continue
        ret = t["types"].get(b.return_type)
        head = f"### `{name}({', '.join(b.params)})`"
        out += [f'<a id="{name}"></a>', "", head + (f" → `{ret}`" if ret else ""), "", doc[lang].strip(), ""]
        if doc.get("see"):
            out += [t["see"] + ": " + ", ".join(f"[`{s}`](#{s})" if s in builtins_doc.FUNCS else f"`{s}`"
                                                for s in doc["see"]) + ".", ""]
    return out


def check_doc():
    """Every name in compiler/builtins_doc.py is a builtin and a group, with both languages"""
    groups = {attr for attr, _, _ in GROUPS}
    for attr, doc in builtins_doc.GROUPS.items():
        if attr not in groups:
            raise SystemExit(f"compiler/builtins_doc.py: {attr} is not a group of GROUPS")
        if not (doc.get("es") and doc.get("en")):
            raise SystemExit(f"compiler/builtins_doc.py: the group {attr} needs es and en")
        if doc.get("example") and not (PROJECT_ROOT / doc["example"]).exists():
            raise SystemExit(f"compiler/builtins_doc.py: {doc['example']} does not exist")
    for name, doc in builtins_doc.FUNCS.items():
        if name not in builtins_module.ALL_BUILTINS:
            raise SystemExit(f"compiler/builtins_doc.py: {name} is not a builtin")
        if not (doc.get("es") and doc.get("en")):
            raise SystemExit(f"compiler/builtins_doc.py: {name} needs es and en")
        for s in doc.get("see", []):
            if s not in builtins_module.ALL_BUILTINS:
                raise SystemExit(f"compiler/builtins_doc.py: {name} sees {s}, which is not a builtin")


def render(lang: str) -> str:
    t = TEXTS[lang]
    missing = unimplemented_builtins()
    lines = [t["switch"], "", t["title"], "", t["generated"], "", *t["missing"], ""]
    total = implemented = 0
    sections = []
    for attr, title_es, title_en in GROUPS:
        group = getattr(builtins_module, attr)
        rows = []
        for name, b in group.items():
            assert isinstance(b, BuiltinFunc)
            total += 1
            status = t["unimplemented"] if name in missing else ""
            implemented += name not in missing
            params = ", ".join(b.params)
            if lang == "es":
                if name not in DESC_ES:
                    raise SystemExit(f"tools/gen_builtins_doc.py: {name} has no Spanish description in "
                                     "compiler/builtins_es.py")
                desc = DESC_ES[name].replace("|", "\\|")
            else:
                desc = b.description.replace("|", "\\|")
            call = f"`{name}({params})`"
            if name in builtins_doc.FUNCS:
                call = f"[{call}](#{name})"
            ret = t["types"].get(b.return_type, b.return_type) if b.return_type != "void" else "—"
            rows.append(f"| {call} | {ret} | {desc} | {status} |")
        title = title_es if lang == "es" else title_en
        sections += [f"## {title}", ""]
        gdoc = builtins_doc.GROUPS.get(attr)
        if gdoc:
            sections += [gdoc[lang].strip(), ""]
            if gdoc.get("example"):
                sections += [t["example"].format(path=gdoc["example"]), "", "```dash", example(gdoc["example"]),
                             "```", "", t["index"], ""]
        sections += [t["header"], "|---|---|---|---|", *rows, ""]
        sections += details(lang, group, t)
    # every builtin must be in a group: a new group missing from GROUPS would be left out silently
    listed = {name for attr, _, _ in GROUPS for name in getattr(builtins_module, attr)}
    left_out = sorted(set(builtins_module.ALL_BUILTINS) - listed)
    if left_out:
        raise SystemExit(f"tools/gen_builtins_doc.py: builtins in no group of GROUPS: {', '.join(left_out)}")
    lines.append(t["total"].format(total=total, implemented=implemented, missing=total - implemented))
    lines.append("")
    return "\n".join(lines + sections)


def main():
    check_doc()
    stale = []
    for lang, output in OUTPUTS.items():
        text = render(lang)
        if "--check" in sys.argv:
            if (output.read_text() if output.exists() else "") != text:
                stale.append(str(output.relative_to(PROJECT_ROOT)))
            continue
        output.write_text(text)
        print(f"Wrote {output.relative_to(PROJECT_ROOT)}")
    if stale:
        print(f"{' and '.join(stale)} out of date: run python3 tools/gen_builtins_doc.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
