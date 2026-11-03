#!/usr/bin/env python3
"""Qué builtins de Dash se pueden usar en DashOS hoy: para cada uno, un programa que lo llama, transpilado para
DashOS (DASH_TARGET=dashos) y compilado con clang como lo hace tools/dashos_run.py. Los que compilan van en
build/dashos/portables.txt (runtime/dashos/build.py los mete en el runtime del camino directo).

    python3 dashc/runtime/dashos/portables.py
"""
import concurrent.futures as cf
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "dashc" / "runtime"))
sys.path.insert(0, str(REPO / "tools"))
import gen_lib  # noqa: E402
import dashos_run  # noqa: E402


def try_one(name, b, tmp):
    d = Path(tempfile.mkdtemp(dir=tmp))
    src = d / "p.dash"
    src.write_text("Main\n    " + f"{name}({', '.join('0' for _ in b.params)})\n" + "end\n", encoding="utf-8")
    c = d / "p.c"
    r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)], cwd=REPO,
                       env=dict(os.environ, DASH_TARGET="dashos"), capture_output=True, text=True)
    if r.returncode:
        return False
    r = subprocess.run(["clang", *dashos_run.CFLAGS, "-c", str(c), "-o", str(d / "p.o")], capture_output=True)
    return r.returncode == 0


def main():
    bs = gen_lib.builtins()
    with tempfile.TemporaryDirectory() as tmp, cf.ThreadPoolExecutor(os.cpu_count()) as ex:
        res = dict(zip(bs, ex.map(lambda n: try_one(n, bs[n], tmp), bs)))
    ok = sorted(n for n, v in res.items() if v)
    out = REPO / "build" / "dashos" / "portables.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ok) + "\n")
    print(f"{len(ok)} de {len(bs)} builtins compilan para DashOS: {out}")


if __name__ == "__main__":
    main()
