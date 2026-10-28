#!/usr/bin/env python3
"""Pruebas de dashc: cada tests/*.dash se compila con dashc y con el Dash de Python
(./dash, gcc por debajo) y los dos ejecutables corren en FS-UAE. Su salida y su código
de retorno tienen que ser iguales.

    python3 tests/run.py                 # A1200 y A500 (el A500 es el 68000 de verdad)
    python3 tests/run.py --machine a500  # solo una máquina
    python3 tests/run.py control         # solo los tests cuyo nombre lleva "control"

Usa las ROMs de $DASH_KICKSTART y $DASH_KICKSTART_A500 (ver AGENTS.md)."""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC = HERE.parent / "dashc"
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import emu_run  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filtro", nargs="?", default="")
    ap.add_argument("--machine", action="append", choices=["a1200", "a500"])
    args = ap.parse_args()
    machines = args.machine or ["a1200", "a500"]

    tests = sorted(p for p in HERE.glob("*.dash") if args.filtro in p.stem)
    tmp = Path(tempfile.mkdtemp(prefix="dashc-tests-"))
    progs = []
    for t in tests:
        a, b = tmp / f"{t.stem}.dashc", tmp / f"{t.stem}.gcc"
        r = subprocess.run([str(DASHC), str(t), "-o", str(a)], capture_output=True, text=True)
        if r.returncode:
            print(f"FALLO {t.name}: dashc no lo compila\n{r.stderr}")
            return 1
        r = subprocess.run([str(REPO / "dash"), str(t), "-o", str(b)], capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            print(f"FALLO {t.name}: ./dash no lo compila\n{r.stdout}{r.stderr}")
            return 1
        progs += [a, b]
        print(f"{t.stem}: dashc {a.stat().st_size} bytes, gcc {b.stat().st_size} bytes")

    fallos = 0
    for m in machines:
        mach = emu_run.MACHINES[m]
        rom = os.environ.get(mach["rom"])
        if not rom:
            print(f"falta ${mach['rom']}: no se prueba en {m}")
            fallos += 1
            continue
        res = emu_run.run_programs([str(p) for p in progs], timeout=300, kickstart=rom,
                                   system=os.environ.get(mach["system"]),
                                   extra_config=mach.get("config", ""), model=mach["model"])
        for i, t in enumerate(tests):
            a, b = res[2 * i], res[2 * i + 1]
            if b.output is None or b.rc is None:
                print(f"FALLO {m} {t.name}: el ejecutable de gcc no terminó")
                fallos += 1
            elif (a.output, a.rc) != (b.output, b.rc):
                fallos += 1
                print(f"FALLO {m} {t.name}: rc {a.rc} (dashc) y {b.rc} (gcc)")
                al, bl = (a.output or "").splitlines(), (b.output or "").splitlines()
                for n in range(max(len(al), len(bl))):
                    x = al[n] if n < len(al) else "<nada>"
                    y = bl[n] if n < len(bl) else "<nada>"
                    if x != y:
                        print(f"  línea {n + 1}: dashc {x!r}, gcc {y!r}")
            else:
                print(f"OK {m} {t.name} ({len(a.output.splitlines())} líneas)")
    print("todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
