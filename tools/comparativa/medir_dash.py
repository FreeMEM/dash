#!/usr/bin/env python3
"""Mide los programas de la comparativa (tools/comparativa/src/dash) por los dos caminos de Dash: directo a hunk
(./dash, "dashd_*") y por C con gcc (./dash --gcc, "dash_*"), con timeit.c en FS-UAE a velocidad real: A1200
(68020 a 14 MHz, 8 MB de fast) y A500 (68000 a 7 MHz), Kickstart 3.1. Escribe "nombre ms pico 0" como
res_a1200.txt (el formato de gen.py) y una tabla directo frente a C.

    python3 tools/comparativa/medir_dash.py [--machines a1200,a500] [--out DIR] [--solo directo]

Necesita $DASH_KICKSTART, $DASH_KICKSTART_A500 y $DASH_EMU_SYS (como tools/emu_run.py) y el gcc de bebbo (para
timeit y el camino por C). Va con el cerrojo del emulador (/run/user/1000/dash-emu-red.lock) si existe flock."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

C = Path(__file__).resolve().parent
REPO = C.parent.parent
GCC = "/opt/amiga/bin/m68k-amigaos-gcc"
CERROJO = "/run/user/1000/dash-emu-red.lock"


def compilar(dest, solo):
    progs = sorted((C / "src" / "dash").glob("*.dash"))
    for f in progs:
        n = f.stem
        caminos = [("dashd", [])] + ([] if solo == "directo" else [("dash", ["--gcc", "-q"])])
        for pref, ops in caminos:
            r = subprocess.run([sys.executable, str(REPO / "dash"), *ops, str(f), "-o", str(dest / f"{pref}_{n}")],
                               cwd=REPO, capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"{f.name} ({pref}): no compila\n{r.stdout}{r.stderr}")
    subprocess.run([GCC, "-O2", "-noixemul", "-o", str(dest / "timeit"), str(C / "timeit.c")], check=True)
    with open(dest / "lista", "w") as l:
        for f in progs:
            for pref in ("dash", "dashd"):
                if (dest / f"{pref}_{f.stem}").exists():
                    l.write(f"{pref}_{f.stem} DH0:Cmp/{pref}_{f.stem}\n")
    return [f.stem for f in progs]


def medir(tmp, maquina):
    sysdir = tmp / "sys"
    medir_dash = tmp / "medir.dash"
    medir_dash.write_text('Main\n    run_command("DH0:Cmp/timeit DH0:Cmp/lista")\n    Print "medido"\nend\n')
    exe = tmp / "medir"
    subprocess.run([sys.executable, str(REPO / "dash"), str(medir_dash), "-o", str(exe)], cwd=REPO, check=True)
    cmd = [sys.executable, str(REPO / "tools/emu_run.py"), "--machine", maquina, "--system", str(sysdir),
           "--timeout", "1200", "--set", "uae_cpu_speed=real"]
    if maquina == "a1200":
        cmd += ["--set", "fast_memory=8192"]
    cmd.append(str(exe))
    if shutil.which("flock") and os.path.exists(os.path.dirname(CERROJO)):
        cmd = ["flock", CERROJO] + cmd
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    lineas = [l for l in r.stdout.splitlines() if l.startswith(("dash_", "dashd_"))]
    if not lineas:
        sys.exit(f"{maquina}: sin medidas\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    return {l.split()[0]: (int(l.split()[1]), int(l.split()[2])) for l in lineas}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--machines", default="a1200,a500")
    ap.add_argument("--out", default=str(REPO / "build" / "comparativa"))
    ap.add_argument("--solo", choices=["directo"], help="solo el directo (más rápido; la columna de C, de antes)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sistema = os.environ.get("DASH_EMU_SYS")
    if not sistema:
        sys.exit("falta $DASH_EMU_SYS")
    with tempfile.TemporaryDirectory(prefix="medir-dash-") as t:
        tmp = Path(t)
        (tmp / "sys").mkdir()
        for d in Path(sistema).iterdir():
            (tmp / "sys" / d.name).symlink_to(d)
        (tmp / "sys" / "Cmp").mkdir()
        nombres = compilar(tmp / "sys" / "Cmp", a.solo)
        for m in a.machines.split(","):
            res = medir(tmp, m)
            with open(out / f"res_{m}.txt", "w") as f:
                for k in sorted(res):
                    f.write(f"{k} {res[k][0]} {res[k][1]} 0\n")
            print(f"== {m} (ms; directo frente a por C)")
            for n in nombres:
                d, g = res.get(f"dashd_{n}"), res.get(f"dash_{n}")
                if d and g:
                    print(f"  {n:10} {d[0]:7} {g[0]:7}  {100 * (d[0] - g[0]) / g[0]:+6.1f} %")
                elif d:
                    print(f"  {n:10} {d[0]:7}")
    print(f"resultados en {out}")


if __name__ == "__main__":
    main()
