#!/usr/bin/env python3
"""Construye runtime/dashrt.o y runtime/dashrt_mc.o (--memcheck): el runtime que dashc lleva dentro.

    python3 runtime/build_lib.py        (make runtime)

1. gen_lib.py saca el runtime de ./dash (con los @native de lib/amiga y los builtins) a build/dashlib_rt.c.
2. Se compila con gcc de bebbo, normal y con DASH_MEMCHECK, una sección por función (hunk.c se queda solo
   con lo que usa cada programa).
3. Se añaden las librerías de C que ./dash compila aparte (compiler/clibs.py: zlib...), la libc mínima de
   rt_libc.c, las rutinas de rt_math.s y las de libgcc que hacen falta (64 bits).
4. Los objetos van uno tras otro (sin ld -r, que juntaría las secciones): hunk.c lee las unidades.

Necesita el gcc de bebbo, el Dash de Python y el SDK de AmiSSL (tools/get_amissl.sh)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC = HERE.parent
REPO = DASHC.parent
GCC = "/opt/amiga/bin/m68k-amigaos-gcc"
AR = "/opt/amiga/bin/m68k-amigaos-ar"
AMISSL = os.environ.get("DASH_AMISSL_SDK") or os.path.expanduser("~/.cache/dash-amissl/x/AmiSSL/Developer")
FLAGS = ["-O2", "-m68000", "-noixemul", "-fomit-frame-pointer", "-fno-common", "-ffunction-sections",
         "-fdata-sections"]
LIBGCC = ["_udivdi3.o", "_umoddi3.o", "_divdi3.o", "_moddi3.o", "_muldi3.o", "_udivmoddi4.o", "_clz.o"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"falla: {' '.join(cmd)}\n{r.stdout}{r.stderr}")


def main():
    build = DASHC / "build"
    build.mkdir(exist_ok=True)
    src = build / "dashlib_rt.c"
    run([sys.executable, str(HERE / "gen_lib.py"), str(src)])
    inc = [f"-I{HERE}", f"-I{AMISSL}/include"]
    run([GCC, *FLAGS, *inc, "-c", str(src), "-o", str(build / "dashlib.o")])
    run([GCC, *FLAGS, *inc, "-DDASH_MEMCHECK", "-c", str(src), "-o", str(build / "dashlib_mc.o")])
    common = []
    run([GCC, *FLAGS, "-fno-builtin", "-fno-tree-loop-distribute-patterns", "-c", str(HERE / "rt_libc.c"),
         "-o", str(build / "rt_libc.o")])
    common.append(build / "rt_libc.o")
    run([GCC, "-m68000", "-c", str(HERE / "rt_math.s"), "-o", str(build / "rt_math.o")])
    common.append(build / "rt_math.o")
    # las librerías de C de ./dash, con sus opciones
    sys.path.insert(0, str(REPO))
    from compiler.clibs import LIBRARIES
    for name, spec in LIBRARIES.items():
        if name != "zlib":
            continue   # (ryu y fdlibm, con Double: D4)
        for s in spec["sources"]:
            obj = build / f"{name}_{Path(s).stem}.o"
            run([GCC, *FLAGS, *spec["defines"], f"-I{REPO / 'runtime' / name}", "-c",
                 str(REPO / "runtime" / name / s), "-o", str(obj)])
            common.append(obj)
    # de libgcc, la aritmética de 64 bits
    libgcc = subprocess.run([GCC, "-m68000", "-print-libgcc-file-name"], capture_output=True,
                            text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([AR, "x", libgcc, *LIBGCC], cwd=tmp, check=True)
        for o in LIBGCC:
            dst = build / f"libgcc{o}"
            dst.write_bytes((Path(tmp) / o).read_bytes())
            common.append(dst)
    for out, lib in (("dashrt.o", "dashlib.o"), ("dashrt_mc.o", "dashlib_mc.o")):
        with open(HERE / out, "wb") as f:
            for p in [build / lib] + common:
                f.write(p.read_bytes())


if __name__ == "__main__":
    main()
