#!/usr/bin/env python3
"""Red de seguridad del reparto de dashc en capa común + generador por procesador (docs/AARCH64_LOOP.md):
compila los tests y ejemplos de Dash con un dashc de referencia y con el de ahora, con varias opciones, y exige
que los ejecutables de 68k salgan idénticos byte a byte (y los errores, con el mismo texto). No usa el emulador.

    python3 tests/identicos.py --guardar   # el dashc de ahora pasa a ser la referencia (build/dashc.ref)
    python3 tests/identicos.py             # comparar con la referencia
    python3 tests/identicos.py -k lista    # solo los ficheros con "lista" en el nombre

Los programas con build_date()/build_time() o @version cambian con la hora: se comparan sin esos bytes si la
única diferencia es esa (se compilan los dos en el mismo segundo, y se reintenta una vez)."""
import argparse
import concurrent.futures as cf
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC_DIR = HERE.parent
REPO = DASHC_DIR.parent
DASHC = DASHC_DIR / "dashc"
REF = DASHC_DIR / "build" / "dashc.ref"

VARIANTES = [[], ["--cpu", "68020"], ["--fpu"], ["--memcheck"], ["--debug"], ["--perfil"]]


def corpus():
    fs = sorted(REPO.glob("tests/test_*.dash")) + sorted(DASHC_DIR.glob("tests/*.dash")) + \
        sorted(REPO.glob("examples/*.dash")) + sorted(REPO.glob("tests/multifile/*.dash"))
    return fs


def compilar(dashc, src, opts, out):
    r = subprocess.run([str(dashc), str(src), "-o", str(out)] + opts, cwd=src.parent,
                       capture_output=True, timeout=120)
    datos = out.read_bytes() if r.returncode == 0 and out.exists() else b""
    return r.returncode, (r.stdout + r.stderr).replace(str(out).encode(), b"OUT"), datos


def comparar(src, opts, tmp):
    tag = src.stem + "_" + "_".join(o.strip("-") for o in opts)
    for intento in range(2):
        a = compilar(REF, src, opts, Path(tmp) / (tag + ".ref"))
        b = compilar(DASHC, src, opts, Path(tmp) / (tag + ".new"))
        if a == b:
            return None
    if a[0] != b[0] or a[1] != b[1]:
        return f"{src.relative_to(REPO)} {' '.join(opts)}: código {a[0]} / {b[0]}\n  ref: {a[1][:300]!r}\n  new: {b[1][:300]!r}"
    n = sum(1 for x, y in zip(a[2], b[2]) if x != y) + abs(len(a[2]) - len(b[2]))
    return f"{src.relative_to(REPO)} {' '.join(opts)}: {len(a[2])} / {len(b[2])} bytes, {n} distintos"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("-k", default="")
    ap.add_argument("-j", type=int, default=os.cpu_count())
    a = ap.parse_args()
    if a.guardar:
        REF.parent.mkdir(exist_ok=True)
        shutil.copy2(DASHC, REF)
        print(f"referencia: {REF}")
        return
    if not REF.exists():
        sys.exit("falta la referencia: python3 tests/identicos.py --guardar (con el dashc de antes del cambio)")
    trabajos = [(f, o) for f in corpus() if a.k in f.name for o in VARIANTES]
    fallos = []
    with tempfile.TemporaryDirectory() as tmp, cf.ThreadPoolExecutor(a.j) as ex:
        for r in ex.map(lambda t: comparar(t[0], t[1], tmp), trabajos):
            if r:
                fallos.append(r)
    for f in fallos:
        print("DISTINTO", f)
    print(f"{len(trabajos) - len(fallos)}/{len(trabajos)} idénticos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
