#!/usr/bin/env python3
"""Cuánto Dash entiende dashc: compila con dashc los tests/test_*.dash y los examples/*.dash de Dash y,
de los que compila y declaran "# expect-out:", mira en el A1200 emulado si dan esa salida (y su
"# expect-rc:"). Saca el recuento y los errores de dashc más repetidos (lo siguiente que falta).

    python3 tests/cobertura.py            # compilar y ejecutar
    python3 tests/cobertura.py --sin-emu  # solo compilar

Usa las ROMs de $DASH_KICKSTART y $DASH_EMU_SYS (ver AGENTS.md); con $DASH_EMU_SYS_MUI, también los que piden
MUI ("# emu-needs: muimaster.library"), en otro arranque."""
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


SKIP_MARKS = ("# rtg", "# autoclose:", "# emu-shot", "# emu-rtg", "# emu-fpu")


def lines_with(text, mark):
    return [l.split(mark, 1)[1].strip() for l in text.splitlines() if l.strip().startswith(mark)]


def has_lib(name):
    """'# emu-needs: x.library': MUI con su sistema aparte; lo demás, si lo tiene $DASH_EMU_SYS"""
    if name == "muimaster.library":
        return bool(os.environ.get("DASH_EMU_SYS_MUI"))
    if name == "amisslmaster.library":
        return bool(os.environ.get("DASH_EMU_SYS_SSL"))
    sys_dir = os.environ.get("DASH_EMU_SYS")
    return bool(sys_dir) and (Path(sys_dir) / "Libs" / name).exists()


def catalogs(hd, group):
    """'# emu-catalog: lib/x.ct': compilado con tools/catalogo.py en DH0:Catalogs/<idioma>/, como el runner"""
    sys.path.insert(0, str(REPO / "tools"))
    from catalogo import build_catalog
    for f, _, text in group:
        for ct in lines_with(text, "# emu-catalog:"):
            name, language, data = build_catalog((f.parent / ct).read_text(encoding="utf-8"))
            out = Path(hd) / "Catalogs" / language / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-emu", action="store_true")
    ap.add_argument("--errores", type=int, default=25, help="cuántos errores distintos enseñar")
    ap.add_argument("filtro", nargs="?", default="", help="solo los ficheros con esto en el nombre")
    args = ap.parse_args()

    files = sorted((REPO / "tests").glob("test_*.dash")) + sorted((REPO / "examples").glob("*.dash"))
    files = [f for f in files if any(x in f.name for x in args.filtro.split(","))]
    tmp = Path(tempfile.mkdtemp(prefix="dashc-cobertura-"))
    ok, errors, runnable = [], collections.Counter(), []
    for f in files:
        exe = tmp / f"{f.parent.name}_{f.stem}"
        # como tests/run_tests.py: desde la raíz, con la ruta relativa (sale en los errores)
        mc = ["--memcheck"] if "\n# memcheck" in "\n" + f.read_text(encoding="utf-8", errors="replace") else []
        r = subprocess.run([str(DASHC), str(f.relative_to(REPO)), "-o", str(exe)] + mc, capture_output=True,
                           text=True, cwd=REPO, errors="replace")
        if r.returncode == 0:
            ok.append(f)
            text = f.read_text(encoding="utf-8", errors="replace")
            # (los que piden algo del runner que dashc aún no tiene: cerrarse solos, pantallas, red...)
            needs = lines_with(text, "# emu-needs:")
            # (lo que tiene el sistema emulado; MUI va aparte, con $DASH_EMU_SYS_MUI)
            if not all(has_lib(n) for n in needs):
                continue
            if lines_with(text, "# expect-out:") and not any(lines_with(text, m) for m in SKIP_MARKS):
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
    # dos arranques: los de MUI con su sistema
    # cuatro arranques: los de MUI con su sistema, los de red ('# emu-net: PUERTO') con la bsdsocket.library de
    # FS-UAE y el servidor de eco del runner, y los de TLS ('# emu-net-tls:') con el sistema con AmiSSL
    # ($DASH_EMU_SYS_SSL) y el eco hablando TLS
    def mui(x):
        return "muimaster.library" in lines_with(x[2], "# emu-needs:")

    def net(x):
        return bool(lines_with(x[2], "# emu-net:") or lines_with(x[2], "# emu-net-tls:"))

    def tls(x):
        return bool(lines_with(x[2], "# emu-net-tls:"))

    groups = [([x for x in runnable if not mui(x) and not net(x)], os.environ.get("DASH_EMU_SYS"), ""),
              ([x for x in runnable if mui(x)], os.environ.get("DASH_EMU_SYS_MUI"), ""),
              ([x for x in runnable if net(x) and not mui(x) and not tls(x)], os.environ.get("DASH_EMU_SYS"),
               "bsdsocket_library = 1\n"),
              ([x for x in runnable if tls(x)], os.environ.get("DASH_EMU_SYS_SSL"), "bsdsocket_library = 1\n")]
    runnable, res = [], []
    for g, system, config in groups:
        if not g:
            continue
        runnable += g
        server = None
        if config:
            sys.path.insert(0, str(REPO / "tests"))
            from run_tests import _EchoServer
            ports = {int((lines_with(t, "# emu-net:") or lines_with(t, "# emu-net-tls:"))[0]) for _, _, t in g}
            server = _EchoServer(sorted(ports), {p for p in ports if system == os.environ.get("DASH_EMU_SYS_SSL")})
        try:
            res += emu_run.run_programs([str(e) for _, e, _ in g], timeout=900, kickstart=rom, system=system,
                                        args=[(lines_with(t, "# emu-args:") or [""])[0] for _, _, t in g],
                                        on_disk=lambda hd, g=g: catalogs(hd, g), extra_config=config)
        finally:
            if server:
                server.close()
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
            diff = f"rc {r.rc} (espera {rc})"
            for i in range(max(len(got), len(want))):
                g = got[i] if i < len(got) else "<nada>"
                w = want[i] if i < len(want) else "<nada>"
                if g != w:
                    diff = f"línea {i + 1}: {g!r}, espera {w!r}"
                    break
            bad.append(f"{f.parent.name}/{f.name}: {diff}")
    print(f"\nen el A1200, con la salida esperada: {good} de {len(runnable)}")
    for b in bad:
        print(f"  distinto: {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
