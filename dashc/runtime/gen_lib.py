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
        # cocina.dash más una llamada a cada builtin: así ./dash pone todo su runtime
        src = Path(tmp) / "cocina.dash"
        calls = "".join(f"    {n}({', '.join('0' for _ in b.params)})\n" for n, b in sorted(builtins().items()))
        src.write_text((HERE / "cocina.dash").read_text(encoding="utf-8") +
                       "\nfunc _cocina_builtins()\n" + calls + "end\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"gen_lib: ./dash no transpila la cocina:\n{r.stdout}{r.stderr}")
        text = c.read_text(encoding="latin-1")

    # libnix: ADD2EXIT (la lista de salida la recorre _dash_quit) y la pila de swapstack
    text = text.replace("#include <stabs.h>\n", "")
    text = text.replace("ADD2EXIT(_dash_atexit_run, 0);\n", "")
    text = re.sub(r"#if DASH_STACK > 0\nextern void __stkinit\(void\);\n.*?#endif\n", "", text, flags=re.S)
    assert "__stkinit" not in text, "gen_lib: la petición de pila ha cambiado"
    # lo del programa: structs, listas literales, prototipos, constructores y funciones
    text = cut(text, "/* Struct Definitions */", "static void _dash_exit_cleanup(void)", "los structs del programa")
    # (y lo de después que no es del runtime: el main y sus marcas)
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
    # las ventanas del programa (win_CocinaWin): las cierra _dash_finish de api.c
    text = "\n".join(ln for ln in text.split("\n") if "win_CocinaWin" not in ln)
    # La limpieza de cada runtime (red, catálogos, tareas...) por un puntero débil: hunk.c no lo cuenta como
    # uso, y si el programa no usa ese runtime, el puntero queda a 0 y no se llama
    m = re.search(r"static void _dash_exit_cleanup\(void\) \{\n(.*?)\n\}\n", text, re.S)
    assert m, "gen_lib: no encuentro _dash_exit_cleanup"
    body, weak = m.group(1), []
    # GadTools y la pantalla: también por puntero débil (dl_gt_fin de api.c cierra además la librería)
    for a, b in (("    if (GadToolsBase) _dash_gt_cleanup();\n", "    dl_gt_fin();\n"),
                 ("    if (GfxBase) _dash_close_screen();\n", "    _dash_close_screen();\n"),
                 ("    if (GadToolsBase) { CloseLibrary(GadToolsBase); GadToolsBase = NULL; }\n", "")):
        assert a in body + "\n", a
        body = (body + "\n").replace(a, b)[:-1]
    # ASL (si el runtime de diálogos va dentro), igual
    body = body.replace("    if (AslBase) { _dash_asl_cleanup(); CloseLibrary(AslBase); AslBase = NULL; }",
                        "    dl_asl_fin();")
    # Las llamadas seguidas, en una tabla de punteros débiles que recorre un bucle (cada "if (p) p();" son
    # 12 bytes en cada programa; un puntero, 4)
    lines_, decls, group = [], [], []
    def flush():
        if not group:
            return
        t = f"_dash_weak_cleanups{len(decls)}"
        decls.append("".join(f"static void {n}(void);\n" for n in group) +
                     f"void (*{t}[{len(group)}])(void) = {{{', '.join(group)}}};\n")
        lines_.append(f"    {{ int i; for (i = 0; i < {len(group)}; i++) if ({t}[i]) {t}[i](); }}")
        group.clear()
    for ln in body.split("\n"):
        mm = re.match(r"^\s*((?:_dash|dl)_\w+)\(\);$", ln)
        if mm and mm.group(1) != "_dash_mem_cleanup":
            group.append(mm.group(1))
        else:
            flush()
            lines_.append(ln)
    flush()
    body, decls = "\n".join(lines_), "".join(decls)
    text = text[:m.start()] + decls + "static void _dash_exit_cleanup(void) {\n" + body + "\n}\n" + text[m.end():]
    # El ensamblador suelto de cada runtime (excepciones, medida de CPU...) a su propia sección, como las
    # funciones: si no, todo junto va en el mismo hunk y entra entero en cada programa
    lines, n, inside = text.split("\n"), 0, False
    for i, ln in enumerate(lines):
        if ln.startswith("__asm__("):
            n, inside = n + 1, True
        if inside:
            lines[i] = re.sub(r'"(\s*)\.text\\n"',
                              lambda t: '"' + t.group(1) + '.section .text._dash_asm%d,\\"ax\\"\\n"' % n, ln)
            if ln.rstrip().endswith(");"):
                inside = False
    text = "\n".join(lines)
    # sin main
    m = re.search(r"^int main\(.*?\) \{", text, re.M)
    assert m, "gen_lib: no encuentro main"
    a = m.start()
    text = text[:a]
    # las teclas de los gadgets ("_Vale"): dl_event_gt_on(1) las mira
    out.write_text("/* Generado por runtime/gen_lib.py a partir del C de ./dash: no editar */\n"
                   "#define _DASH_GADGET_KEYS\n" + text +
                   '\n#include "api.c"\n' + natives() + builtin_wrappers(), encoding="latin-1")


# usan el runtime de ventanas (_dash_win), que aún no va en la librería (D6 de docs/DASHC_LOOP.md)
PENDING = {"intuition.dash"}
C_TYPES = {"Int": "LONG", "Pointer": "APTR", "String": "STRPTR", "Bool": "BOOL", "Array": "DashArrayLong *"}
NATIVE = re.compile(r'^@native func (\w+)\((.*?)\)\s*(?:->\s*(\w+))?\s*\n"""\n(.*?)\n"""\s*\nend', re.S | re.M)


# Los builtins que van en la librería: aún sin ventanas ni gráficos (D6) ni Double (D4)
GUI = ("mui_", "ra_", "usb_", "wifi_")
LIB_FLAGS = ("needs_reaction",)


def builtins():
    sys.path.insert(0, str(REPO))
    from compiler import amiga_builtins as ab
    out = {}
    for v in vars(ab).values():
        if isinstance(v, dict):
            for n, b in v.items():
                if (isinstance(b, ab.BuiltinFunc) and not any(getattr(b, f) for f in LIB_FLAGS) and
                        not n.startswith(GUI) and
                        b.return_type != "double" and "double" not in b.c_template):
                    out[n] = b
    return out


def builtin_wrappers():
    """Cada builtin como db_nombre(LONG...): su plantilla de C con los parámetros en LONG"""
    from string import Template
    out = ["\n/* ---- builtins (compiler/amiga_builtins.py) ---- */\n"
           "#pragma GCC diagnostic ignored \"-Wint-conversion\"\n"]
    for n, b in sorted(builtins().items()):
        if n in SKIP:
            continue
        # (los parámetros como _a0, _a1...: alguno se llama como una palabra de C, default)
        params = ", ".join(f"LONG _a{i}" for i in range(len(b.params))) or "void"
        code = Template(b.c_template).substitute({p: f"_a{i}" for i, p in enumerate(b.params)})
        if b.return_type == "void":
            out.append(f"LONG db_{n}({params}) {{ {code}; return 0; }}\n")
        else:
            out.append(f"LONG db_{n}({params}) {{ return (LONG)({code}); }}\n")
    return "".join(out)


# no compilan como envoltorio (se miran uno a uno)
# (de Double: D4)
SKIP = {"is_inf", "is_nan"}


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
