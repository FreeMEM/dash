#!/usr/bin/env python3
"""Compara la velocidad del código de dashc con la del Dash de Python (gcc -O2).

    python3 bench/bench_run.py                # A500 y A1200 a velocidad real (como tools/bench.py)
    python3 bench/bench_run.py --machine a500

Cada bench_*.dash se compila con dashc y con ./dash (añadiéndole el import de
tests/bench/bench_lib.dash, que da bench_start/bench_end/bench_sink) y los dos
corren en la misma máquina. Las líneas que no son BENCH tienen que coincidir."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import bench  # noqa: E402
from emu_run import run_programs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine", action="append", choices=["a500", "a1200"])
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="dashc-bench-"))
    shutil.copy(REPO / "tests/bench/bench_lib.dash", tmp)
    progs, names = [], []
    for src in sorted(HERE.glob("bench_*.dash")):
        a, b = tmp / f"{src.stem}.dashc", tmp / f"{src.stem}.gcc"
        subprocess.run([str(HERE.parent / "dashc"), str(src), "-o", str(a)], check=True)
        conlib = tmp / src.name
        conlib.write_text('import "bench_lib.dash"\n' + src.read_text())
        r = subprocess.run([str(REPO / "dash"), str(conlib), "-o", str(b)], capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            sys.exit(f"./dash no compila {src.name}:\n{r.stdout}{r.stderr}")
        progs += [a, b]
        names.append(src.name)
        print(f"{src.stem}: dashc {a.stat().st_size} bytes, gcc {b.stat().st_size} bytes")

    for m in args.machine or ["a500", "a1200"]:
        conf = bench.MACHINES[m]
        rom = os.environ.get(conf["rom_env"])
        if not rom:
            sys.exit(f"falta ${conf['rom_env']}")
        res = run_programs([str(p) for p in progs], timeout=900, kickstart=rom, extra_config=conf["config"])
        print(f"\n{m} (ns por vuelta; más de 1 = dashc más lento)")
        print(f"{'':12} {'dashc':>9} {'gcc':>9}  dashc/gcc")
        for i, name in enumerate(names):
            a, b = res[2 * i], res[2 * i + 1]
            resto = [[ln for ln in (r.output or "").splitlines() if not ln.startswith("BENCH")] for r in (a, b)]
            if resto[0] != resto[1] or a.rc != 0 or b.rc != 0:
                print(f"! {name}: salidas distintas o fallo: rc {a.rc}/{b.rc}\n  dashc {resto[0]}\n  gcc   {resto[1]}")
            na, nb = bench.parse(a.output)[0], bench.parse(b.output)[0]
            for k in nb:
                if k in na:
                    print(f"{k:12} {na[k]:9} {nb[k]:9}  {na[k] / nb[k]:.2f}")


if __name__ == "__main__":
    main()
