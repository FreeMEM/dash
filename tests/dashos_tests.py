#!/usr/bin/env python3
"""Los tests de Dash en DashOS (docs/AARCH64_LOOP.md): cada tests/test_*.dash con "# expect-out:" se compila por
el camino de C para AArch64 little-endian (tools/dashos_run.py) y se ejecuta en qemu-aarch64. Su salida debe ser
la esperada, como en el A1200.

    python3 tests/dashos_tests.py              # recuento, y los errores de compilación más repetidos
    python3 tests/dashos_tests.py -k lista -v  # solo esos, con el detalle de cada fallo
    python3 tests/dashos_tests.py --lista      # qué da cada test (ok, build, salida, timeout, rc)
    python3 tests/dashos_tests.py --directo    # por el compilador directo (dashc-a64), sin C
    python3 tests/dashos_tests.py --pie        # enlazados como PIE
    python3 tests/dashos_tests.py --be         # en big-endian (la caja Amiga), en qemu-aarch64_be

Un test con "# expect-rc: N" debe acabar con ese código. En DashOS los textos son UTF-8 (en el Amiga, Latin-1): una
línea "# dashos-line N: texto" cambia la línea N de la salida esperada, y "# dashos-skip: motivo" deja fuera el test.
Los de tests/dashos/ son solo de DashOS."""
import argparse
import collections
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import dashos_run  # noqa: E402


def marks(text, mark):
    return [l.split(mark, 1)[1].strip() for l in text.splitlines() if l.strip().startswith(mark)]


DIRECT = False
PIE = False
BE = False


def one(f, tmp):
    text = f.read_text(encoding="utf-8", errors="replace")
    exe = Path(tmp) / f.stem
    memcheck = any(l.strip() == "# memcheck" for l in text.splitlines())
    ok, msg = (dashos_run.build_direct if DIRECT else dashos_run.build)(f.relative_to(REPO), exe, memcheck=memcheck,
                                                                        pie=PIE, be=BE)   # (relativo: como en los errores del A1200)
    if not ok:
        return "build", msg
    try:
        rc, out, err = dashos_run.run(exe, timeout=30)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    want = marks(text, "# expect-out:")
    for m in marks(text, "# dashos-line"):
        n, line = m.split(":", 1)
        want[int(n) - 1] = line.strip()
    ignore = marks(text, "# ignore-out:")
    got = [l.rstrip() for l in out.splitlines() if not any(l.startswith(i) for i in ignore)]
    want = [l for l in want if not any(l.startswith(i) for i in ignore)]
    want_rc = int((marks(text, "# expect-rc:") or ["0"])[0])
    if rc != want_rc:
        return "rc", f"código {rc}, se esperaba {want_rc}\n{out[-400:]}{err[-400:]}"
    if got != want:
        return "salida", "esperada:\n  " + "\n  ".join(want[:12]) + "\nobtenida:\n  " + "\n  ".join(got[:12]) + err[-300:]
    return "ok", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="")
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--directo", action="store_true")
    ap.add_argument("--pie", action="store_true", help="enlazados como PIE (qemu los carga en otra dirección)")
    ap.add_argument("--be", action="store_true", help="big-endian (la caja Amiga)")
    a = ap.parse_args()
    global DIRECT, PIE, BE
    DIRECT = a.directo
    PIE = a.pie
    BE = a.be
    fs = [f for f in sorted(REPO.glob("tests/test_*.dash")) + sorted(REPO.glob("tests/dashos/test_*.dash"))
          if a.k in f.name and "# expect-out:" in (t := f.read_text(encoding="utf-8", errors="replace"))
          and "# dashos-skip:" not in t]
    with tempfile.TemporaryDirectory() as tmp, cf.ThreadPoolExecutor(os.cpu_count()) as ex:
        res = dict(zip(fs, ex.map(lambda f: one(f, tmp), fs)))
    errs = collections.Counter()
    for f, (k, m) in res.items():
        if a.lista:
            print(k, f.relative_to(REPO))
        if a.v and k != "ok":
            print(f"--- {f.name}: {k}\n{m[:1500]}")
        if k == "build":
            for l in m.splitlines():
                mm = re.search(r"error: (.*?)(\[-W|$)", l) or re.search(r"(aún no está .*)", l)
                if mm:
                    errs[re.sub(r"'[^']*'", "'X'", mm.group(1))[:100]] += 1
    if not a.v:
        for e, n in errs.most_common(15):
            print(f"{n:5} {e}")
    c = collections.Counter(k for k, m in res.values())
    print(" ".join(f"{k}={n}" for k, n in c.most_common()), f"de {len(fs)}")
    sys.exit(0 if c["ok"] == len(fs) else 1)


if __name__ == "__main__":
    main()
