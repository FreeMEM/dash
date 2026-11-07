#!/usr/bin/env python3
"""La tabla de builtins que lleva dashc (build/builtins_tab.c), sacada de compiler/amiga_builtins.py:
de cada uno, cuántos parámetros tiene, qué devuelve (5: Double), si guarda sus argumentos, qué parámetros son
Double (entonces un texto o un
objeto que se le pasa se "escapa", como en ./dash). Su código está en la librería (db_nombre)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from compiler import amiga_builtins as ab  # noqa: E402
from compiler.codegen import CodeGenerator  # noqa: E402

RET = {"void": 0, "LONG": 1, "ULONG": 1, "APTR": 1, "BOOL": 2, "STRPTR": 3, "double": 5}
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_lib import double_params  # noqa: E402


def main():
    rows = []
    for v in vars(ab).values():
        if not isinstance(v, dict):
            continue
        for n, b in v.items():
            if not isinstance(b, ab.BuiltinFunc):
                continue
            ret = 4 if b.list_of == "String" else RET.get(b.return_type)
            if ret is None:
                continue
            keeps = n not in CodeGenerator._STRING_READERS and not b.reads_only
            dmask = sum(1 << i for i in double_params(n, b))
            rows.append(f'    {{"{n}", {len(b.params)}, {ret}, {int(keeps)}, {dmask}, {int(b.needs_dashos)}}},\n')
    from compiler.ast_nodes import KEY_NAMES
    keys = "".join(f'    {{"{k}", {v}}},\n' for k, v in sorted(KEY_NAMES.items()))
    out = Path(sys.argv[1])
    out.write_text("/* Generado por runtime/gen_builtins_tab.py: no editar */\n#include \"../src/dashc.h\"\n"
                   "const BuiltinInfo builtin_info[] = {\n" + "".join(sorted(rows)) + "};\n"
                   f"const int builtin_count = {len(rows)};\n"
                   "/* On Key \"NOMBRE\": su código de tecla (compiler/ast_nodes.py KEY_NAMES) */\n"
                   "const KeyName key_names[] = {\n" + keys + "    {0, 0}\n};\n")


if __name__ == "__main__":
    main()
