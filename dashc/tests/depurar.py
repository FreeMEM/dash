#!/usr/bin/env python3
"""Los tests del depurador (docs/DEPURADOR_LOOP.md): cada tests/depurar/*.dash menos depurado.dash es un depurador
que se compila con dashc y se ejecuta en el A1200 emulado con, en DH0:, cada depurado*.dash compilado con --debug
y sin_debug (depurado.dash sin --debug). Su salida tiene que ser la de sus líneas "# expect-out:".

    python3 tests/depurar.py [--a500] [filtro]      (--a500: un A500 con 68000 en vez del A1200)"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import emu_run  # noqa: E402


def main():
    args = sys.argv[1:]
    a500 = "--a500" in args
    args = [a for a in args if a != "--a500"]
    filtro = args[0] if args else ""
    d = HERE / "depurar"
    tests = sorted(t for t in d.glob("*.dash") if not t.name.startswith("depurado") and filtro in t.stem)
    debugged = sorted(t.stem for t in d.glob("depurado*.dash"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        dash = str(REPO / "dash")
        for name in debugged:
            subprocess.run([dash, "--debug", name + ".dash", "-o", str(tmp / name)], cwd=d, check=True)
        subprocess.run([dash, "depurado.dash", "-o", str(tmp / "sin_debug")], cwd=d, check=True)
        exes = []
        for t in tests:
            exe = tmp / t.stem
            subprocess.run([dash, t.name, "-o", str(exe)], cwd=d, check=True)
            exes.append(str(exe))

        def on_disk(hd):
            for name in debugged + ["sin_debug"]:
                shutil.copy(tmp / name, Path(hd) / name)

        res = emu_run.run_programs(exes, timeout=600,
                                   kickstart=os.environ["DASH_KICKSTART_A500" if a500 else "DASH_KICKSTART"],
                                   system=os.environ.get("DASH_EMU_SYS"), on_disk=on_disk,
                                   extra_config="amiga_model = A500\n" if a500 else "")
    bad = 0
    for t, r in zip(tests, res):
        want = [l.split(":", 1)[1].strip() for l in t.read_text().splitlines() if l.startswith("# expect-out:")]
        got = [l.strip() for l in (r.output or "").splitlines()]
        if got != want or r.rc != 0:
            bad += 1
            print(f"FALLO {t.stem} (rc {r.rc})")
            for i in range(max(len(want), len(got))):
                a = want[i] if i < len(want) else "-"
                b = got[i] if i < len(got) else "-"
                print(f"  {'  ' if a == b else '!='} {a}  |  {b}")
        else:
            print(f"OK {t.stem}")
    print("todo bien" if not bad else f"{bad} mal")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
