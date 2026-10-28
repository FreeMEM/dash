#!/usr/bin/env python3
"""Saca el runtime de datos (memoria, textos, listas, objetos con contador, errores) del C que genera el
Dash de Python para cocina.dash, un programa que usa todo eso. Así dashc lleva el mismo runtime que
./dash y sigue al día con compiler/codegen.py.

    python3 runtime/gen_lib.py build/dashlib_rt.c

Se quita lo del programa (sus structs, funciones y main) y lo que depende de libnix (exit, la lista de
salida de stabs.h, la pila): api.c, que se incluye al final, pone el arranque y la salida de dashc y
exporta con nombre dl_* lo que llama el código de dashc."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def cut(text, start, end, what):
    """quita de start (incluido) a end (sin incluir)"""
    a = text.find(start)
    b = text.find(end, a)
    assert a >= 0 and b > a, f"gen_lib: no encuentro {what} en el C de ./dash"
    return text[:a] + text[b:]


def main():
    out = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "cocina.c"
        subprocess.run([sys.executable, "-m", "compiler.main", str(HERE / "cocina.dash"), "-o", str(c)],
                       cwd=REPO, check=True, capture_output=True)
        text = c.read_text(encoding="latin-1")

    # libnix: ADD2EXIT (la lista de salida la recorre _dash_quit) y la pila de swapstack
    text = text.replace("#include <stabs.h>\n", "")
    text = text.replace("ADD2EXIT(_dash_atexit_run, 0);\n", "")
    text = re.sub(r"#if DASH_STACK > 0\nextern void __stkinit\(void\);\n.*?#endif\n", "", text, flags=re.S)
    assert "__stkinit" not in text, "gen_lib: la petición de pila ha cambiado"
    # lo del programa: structs, listas literales, prototipos, constructores y funciones
    text = cut(text, "/* Struct Definitions */", "static void _dash_exit_cleanup(void)", "los structs del programa")
    # exit() de libnix: dashc vuelve al arranque con _dash_quit
    assert "    exit(code);\n" in text
    text = text.replace("    exit(code);\n", "    _dash_quit(code);\n")
    text = text.replace("static void _dash_exit(int code);\n",
                        "static void _dash_exit(int code);\nvoid _dash_quit(int code) __attribute__((noreturn));\n", 1)
    # el nombre del fuente lo pone dashc al arrancar
    text, n = re.subn(r"static const char \*const _dash_srcfiles\[\] = \{[^\n]*\};",
                      "const char *_dash_srcfiles[64];", text)
    assert n == 1, "gen_lib: no encuentro _dash_srcfiles"
    # --memcheck: dashc pone el sitio de cada instrucción en _dash_mc_where (tiene que verse fuera)
    old = "static const char *_dash_mc_where = NULL;"
    assert old in text, "gen_lib: no encuentro _dash_mc_where"
    text = text.replace(old, "const char *_dash_mc_where = NULL;")
    # sin main
    a = text.find("int main() {")
    assert a >= 0
    text = text[:a]
    out.write_text("/* Generado por runtime/gen_lib.py a partir del C de ./dash: no editar */\n" + text +
                   '\n#include "api.c"\n' + natives(), encoding="latin-1")


# usan el runtime de ventanas (_dash_win), que aún no va en la librería (D6 de docs/DASHC_LOOP.md)
PENDING = {"intuition.dash"}
C_TYPES = {"Int": "LONG", "Pointer": "APTR", "String": "STRPTR", "Bool": "BOOL", "Array": "DashArrayLong *"}
NATIVE = re.compile(r'^@native func (\w+)\((.*?)\)\s*(?:->\s*(\w+))?\s*\n"""\n(.*?)\n"""\s*\nend', re.S | re.M)


def natives():
    """Los @native de lib/amiga (los de los programas no se admiten en dashc): cada uno como en ./dash,
    static, y un envoltorio dn_nombre con todo en LONG, que es lo que llama dashc."""
    out = ["\n/* ---- @native de lib/amiga ---- */\n#include \"natives.h\"\n"]
    seen = set()
    for mod in sorted((REPO / "lib" / "amiga").glob("*.dash")):
        if mod.name in PENDING:
            continue
        for name, params, ret, body in NATIVE.findall(mod.read_text(encoding="utf-8")):
            if name in seen:
                continue
            seen.add(name)
            ps = []
            for p in [p.strip() for p in params.split(",") if p.strip()]:
                pn, _, pt = p.partition(":")
                ps.append((pn.strip(), C_TYPES[pt.strip()] if pt.strip() else "LONG"))
            rt = C_TYPES[ret] if ret else "void"
            decl = ", ".join(f"{t} {n}" for n, t in ps) or "void"
            out.append(f"/* {mod.name} */\nstatic {rt} __dn_{name}({decl}) {{\n{body}\n}}\n")
            args = ", ".join(f"LONG {n}" for n, _ in ps) or "void"
            call = f"__dn_{name}(" + ", ".join(f"({t}){n}" for n, t in ps) + ")"
            out.append(f"LONG dn_{name}({args}) {{ " + (f"return (LONG){call}; }}\n" if ret else f"{call}; return 0; }}\n"))
    return "\n".join(out)


if __name__ == "__main__":
    main()
