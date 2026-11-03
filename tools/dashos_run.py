#!/usr/bin/env python3
"""Compila un programa Dash para DashOS por el camino de C (docs/AARCH64_LOOP.md, fase A2) y lo ejecuta en el PC
con qemu-aarch64_be. Para probar: la plataforma es la de Linux (runtime/dashos/plat.c con DASH_PLAT_LINUX).

    python3 tools/dashos_run.py prog.dash            # compila, ejecuta y enseña la salida
    python3 tools/dashos_run.py prog.dash -o prog    # además deja el ELF
    python3 tools/dashos_run.py prog.dash --dashos -o prog   # el ELF para DashOS de verdad (no se ejecuta)

Sale con el código del programa. Necesita clang (objetivo aarch64_be-none-elf), ld.lld y qemu-aarch64_be."""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RT = REPO / "runtime" / "dashos"
CFLAGS = ["--target=aarch64_be-none-elf", "-ffreestanding", "-fno-builtin", "-O2", "-fno-pic", "-fno-pie",
          "-march=armv8-a",
          "-fno-delete-null-pointer-checks", "-Wno-unknown-attributes", "-Wno-pointer-sign",
          "-Werror=implicit-function-declaration", "-Werror=int-conversion",
          "-Werror=pointer-to-int-cast", "-Werror=int-to-pointer-cast", "-Werror=incompatible-pointer-types",
          "-I" + str(RT / "include"), "-I" + str(RT)]


def build(src, exe, linux=True, memcheck=False):
    """Transpila y enlaza; devuelve (ok, mensajes)"""
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "prog.c"
        env = dict(os.environ, DASH_TARGET="dashos", **({"DASH_MEMCHECK_C": "1"} if memcheck else {}))
        r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)], cwd=REPO, env=env,
                           capture_output=True, text=True)
        if r.returncode:
            return False, r.stdout + r.stderr
        text = c.read_text(encoding="latin-1")
        m = re.search(r"^#define DASH_STACK (\d+)", text, re.M)
        stack = max(int(m.group(1)) if m else 16384, 16384)
        objs = []
        for f, defs in ((c, ["-DDASH_MEMCHECK"] if memcheck else []), (RT / "plat.c", ["-DDASH_PLAT_LINUX"] if linux else [])):
            o = Path(tmp) / (f.stem + ".o")
            r = subprocess.run(["clang", *CFLAGS, *defs, "-c", str(f), "-o", str(o)], capture_output=True, text=True)
            if r.returncode:
                return False, r.stderr.replace(str(c), "prog.c")
            objs.append(str(o))
        r = subprocess.run(["ld.lld", "-static", "-e", "_start", "--image-base=0x400000",
                            "-z", "separate-loadable-segments", "-z", f"stack-size={stack}",
                            *objs, "-o", str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
    return True, ""


def run(exe, timeout=30):
    r = subprocess.run(["qemu-aarch64_be", str(exe)], capture_output=True, timeout=timeout)
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o")
    ap.add_argument("--dashos", action="store_true", help="plataforma de DashOS (no se ejecuta)")
    ap.add_argument("--memcheck", action="store_true", help="como ./dash --memcheck")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(a.o) if a.o else Path(tmp) / "prog"
        ok, msg = build(Path(a.src).resolve(), exe.resolve(), linux=not a.dashos, memcheck=a.memcheck)
        if not ok:
            sys.exit(msg)
        if a.dashos:
            return
        rc, out, err = run(exe)
        sys.stdout.write(out)
        sys.stderr.write(err)
        sys.exit(rc)


if __name__ == "__main__":
    main()
