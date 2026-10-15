#!/usr/bin/env python3
"""Generate docs/BUILTINS.md from compiler/amiga_builtins.py.

Usage:
    python3 tools/gen_builtins_doc.py          # write docs/BUILTINS.md
    python3 tools/gen_builtins_doc.py --check  # exit 1 if the file is out of date
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import compiler.amiga_builtins as builtins_module  # noqa: E402
from compiler.amiga_builtins import BuiltinFunc  # noqa: E402
from compiler.codegen import unimplemented_builtins  # noqa: E402

OUTPUT = PROJECT_ROOT / "docs" / "BUILTINS.md"

GROUPS = [
    ("GRAPHICS_BASIC", "Gráficos básicos"),
    ("GRAPHICS_ADVANCED", "Gráficos avanzados"),
    ("INPUT_FUNCTIONS", "Entrada (teclado, ratón, joystick)"),
    ("GADTOOLS_FUNCTIONS", "GadTools"),
    ("MENU_FUNCTIONS", "Menús"),
    ("ASL_FUNCTIONS", "Requesters ASL"),
    ("REACTION_FUNCTIONS", "ReAction"),
    ("SYSTEM_FUNCTIONS", "Sistema y memoria"),
    ("DOS_FUNCTIONS", "Ficheros (DOS)"),
    ("BUFFER_FUNCTIONS", "Buffers"),
    ("AUDIO_FUNCTIONS", "Audio"),
    ("INTUITION_EXPANDED", "Intuition"),
    ("RTG_FUNCTIONS", "RTG (CyberGraphX / Picasso96)"),
    ("MUI_FUNCTIONS", "MUI"),
]


def render() -> str:
    missing = unimplemented_builtins()
    lines = [
        "# Funciones built-in",
        "",
        "> Generado por `tools/gen_builtins_doc.py` desde `compiler/amiga_builtins.py`. No editar a mano.",
        "",
        "Las marcadas **sin implementar** están declaradas pero no tienen código C:",
        "usarlas da el error `Builtin 'x' is declared but not implemented yet`.",
        "",
    ]
    total = implemented = 0
    sections = []
    for attr, title in GROUPS:
        group = getattr(builtins_module, attr)
        rows = []
        for name, b in group.items():
            assert isinstance(b, BuiltinFunc)
            total += 1
            status = "**sin implementar**" if name in missing else ""
            implemented += name not in missing
            params = ", ".join(b.params)
            desc = b.description.replace("|", "\\|")
            rows.append(f"| `{name}({params})` | `{b.return_type}` | {desc} | {status} |")
        sections += [f"## {title}", "", "| Función | Devuelve | Descripción | Estado |",
                     "|---|---|---|---|", *rows, ""]
    lines.append(f"Total: {total} funciones, {implemented} implementadas, {total - implemented} sin implementar.")
    lines.append("")
    return "\n".join(lines + sections)


def main():
    text = render()
    if "--check" in sys.argv:
        current = OUTPUT.read_text() if OUTPUT.exists() else ""
        if current != text:
            print("docs/BUILTINS.md is out of date: run python3 tools/gen_builtins_doc.py")
            sys.exit(1)
        return
    OUTPUT.write_text(text)
    print(f"Wrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
