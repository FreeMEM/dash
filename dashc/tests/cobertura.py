#!/usr/bin/env python3
"""Cuánto Dash entiende dashc: compila con dashc los tests/test_*.dash y los examples/*.dash de Dash y,
de los que compila y declaran "# expect-out:", mira en el A1200 emulado si dan esa salida (y su
"# expect-rc:"). Saca el recuento y los errores de dashc más repetidos (lo siguiente que falta).

    python3 tests/cobertura.py            # compilar y ejecutar
    python3 tests/cobertura.py --sin-emu  # solo compilar

Usa las ROMs de $DASH_KICKSTART y $DASH_EMU_SYS (ver AGENTS.md)."""
import argparse
import collections
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC = HERE.parent / "dashc"
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import emu_run  # noqa: E402


def lines_with(text, mark):
    return [l.split(mark, 1)[1].strip() for l in text.splitlines() if l.strip().startswith(mark)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-emu", action="store_true")
    ap.add_argument("--errores", type=int, default=25, help="cuántos errores distintos enseñar")
    args = ap.parse_args()

    files = sorted((REPO / "tests").glob("test_*.dash")) + sorted((REPO / "examples").glob("*.dash"))
    tmp = Path(tempfile.mkdtemp(prefix="dashc-cobertura-"))
    ok, errors, runnable = [], collections.Counter(), []
    for f in files:
        exe = tmp / f"{f.parent.name}_{f.stem}"
        r = subprocess.run([str(DASHC), f.name, "-o", str(exe)], capture_output=True, text=True,
                           cwd=f.parent, errors="replace")
        if r.returncode == 0:
            ok.append(f)
            text = f.read_text(encoding="utf-8", errors="replace")
            if lines_with(text, "# expect-out:") and not lines_with(text, "# emu-needs:"):
                runnable.append((f, exe, text))
        else:
            msg = (r.stderr.strip().splitlines() or ["?"])[-1]
            msg = re.sub(r"^.*?:\d+:\d+: ", "", msg)          # sin fichero:línea:columna
            msg = re.sub(r"\b(la variable|la función|el tipo|el struct) \S+", r"\1 X", msg)
            errors[msg] += 1
    print(f"compila dashc: {len(ok)} de {len(files)} ({100 * len(ok) // max(len(files), 1)} %)")
    print(f"\nlos errores más repetidos ({len(errors)} distintos):")
    for msg, n in errors.most_common(args.errores):
        print(f"  {n:4}  {msg}")

    if args.sin_emu or not runnable:
        return 0
    rom = os.environ.get("DASH_KICKSTART")
    if not rom:
        print("falta $DASH_KICKSTART: no se ejecuta")
        return 1
    res = emu_run.run_programs([str(e) for _, e, _ in runnable], timeout=900, kickstart=rom,
                               system=os.environ.get("DASH_EMU_SYS"))
    good = 0
    bad = []
    for (f, _, text), r in zip(runnable, res):
        want = lines_with(text, "# expect-out:")
        ignore = lines_with(text, "# ignore-out:")
        rc = int((lines_with(text, "# expect-rc:") or ["0"])[0])
        got = [l.strip() for l in (r.output or "").splitlines()]
        got = [l for l in got if not any(l.startswith(p) for p in ignore)]
        want = [l for l in want if not any(l.startswith(p) for p in ignore)]
        if got == want and r.rc == rc:
            good += 1
        else:
            bad.append(f"{f.parent.name}/{f.name}")
    print(f"\nen el A1200, con la salida esperada: {good} de {len(runnable)}")
    for b in bad:
        print(f"  distinto: {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
