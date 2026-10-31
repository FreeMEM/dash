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
    },
}


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
            rows.append(f"| `{name}({params})` | `{b.return_type}` | {desc} | {status} |")
        title = title_es if lang == "es" else title_en
        sections += [f"## {title}", "", t["header"], "|---|---|---|---|", *rows, ""]
    # every builtin must be in a group: a new group missing from GROUPS would be left out silently
    listed = {name for attr, _, _ in GROUPS for name in getattr(builtins_module, attr)}
    left_out = sorted(set(builtins_module.ALL_BUILTINS) - listed)
    if left_out:
        raise SystemExit(f"tools/gen_builtins_doc.py: builtins in no group of GROUPS: {', '.join(left_out)}")
    lines.append(t["total"].format(total=total, implemented=implemented, missing=total - implemented))
    lines.append("")
    return "\n".join(lines + sections)


def main():
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
