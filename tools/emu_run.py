#!/usr/bin/env python3
"""Run Dash programs inside FS-UAE and collect their output.

Uses the Kickstart ROM in $DASH_KICKSTART (or --kickstart), or the AROS
replacement built into FS-UAE when none is given, and SDL's offscreen
video driver, so no window appears. All the
programs run in one boot: a host directory is mounted as DH0: and its
S:Startup-Sequence runs each program with its output redirected to a file.

    tools/emu_run.py prog.dash [otro.dash ...]   # compile and run
    tools/emu_run.py --opt prog.dash             # compile with -O
    tools/emu_run.py bin/programa                # already compiled

    tools/emu_run.py --autoclose 3 ventana.dash  # ends by itself after 3 s

A program that never ends (an EventLoop waiting for the close gadget
without --autoclose, a crash) stops the boot: it and the ones after it are reported as TIMEOUT.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FSUAE_CONFIG = """\
[fs-uae]
amiga_model = A1200
fast_memory = 8192
hard_drive_0 = {hd}
hard_drive_0_label = DH0
fullscreen = 0
floppy_drive_volume = 0
automatic_input_grab = 0
uae_cpu_speed = max
{kickstart}"""


class EmuResult:
    def __init__(self, name, output, rc):
        self.name = name
        self.output = output   # text the program printed (None if it never ran)
        self.rc = rc           # return code, or None on timeout

    @property
    def timed_out(self):
        return self.rc is None


def compile_dash(src: Path, exe: Path, optimize: bool, autoclose: int = 0) -> None:
    cmd = [sys.executable, str(ROOT / "dash"), str(src), "-o", str(exe)]
    if optimize:
        cmd.append("-O")
    env = dict(os.environ)
    if autoclose:
        env["DASH_TEST_AUTOCLOSE"] = str(autoclose)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0 or not exe.exists():
        raise RuntimeError(f"{src}: compile failed\n{result.stdout}{result.stderr}")


def run_programs(programs, timeout: float = 60.0, optimize: bool = False,
                 kickstart: str = None, autoclose: int = 0):
    """programs: list of .dash sources or Amiga executables.
    Returns one EmuResult per program, in order."""
    if not shutil.which("fs-uae"):
        raise RuntimeError("fs-uae not found")
    with tempfile.TemporaryDirectory(prefix="dash_emu_") as tmp:
        tmp = Path(tmp)
        hd = tmp / "hd"
        (hd / "S").mkdir(parents=True)
        lines = []
        names = []
        for i, prog in enumerate(programs):
            prog = Path(prog)
            exe = hd / f"p{i}"
            if prog.suffix == ".dash":
                compile_dash(prog, exe, optimize, autoclose)
            else:
                shutil.copy(prog, exe)
            names.append(prog.name)
            lines.append(f"DH0:p{i} >DH0:out{i}.txt")
            lines.append(f'Echo "$RC" >DH0:rc{i}.txt')
        lines.append('Echo "fin" >DH0:done.txt')
        (hd / "S" / "Startup-Sequence").write_text("\n".join(lines) + "\n")
        config = tmp / "run.fs-uae"
        kickstart = kickstart or os.environ.get("DASH_KICKSTART")
        if kickstart and not Path(kickstart).is_file():
            raise RuntimeError(f"Kickstart ROM not found: {kickstart}")
        ks_line = f"kickstart_file = {kickstart}\n" if kickstart else ""
        config.write_text(FSUAE_CONFIG.format(hd=hd, kickstart=ks_line))

        env = dict(os.environ, SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy")
        proc = subprocess.Popen(["fs-uae", str(config)], cwd=tmp, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            deadline = time.time() + timeout
            while time.time() < deadline and not (hd / "done.txt").exists():
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
            time.sleep(0.3)  # let the last file be flushed to the host
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()

        results = []
        for i, name in enumerate(names):
            out_file, rc_file = hd / f"out{i}.txt", hd / f"rc{i}.txt"
            output = out_file.read_text(errors="replace") if out_file.exists() else None
            rc = None
            if rc_file.exists():
                try:
                    rc = int(rc_file.read_text().strip() or "0")
                except ValueError:
                    rc = None
            results.append(EmuResult(name, output, rc))
        return results


def main():
    parser = argparse.ArgumentParser(description="Run Dash programs in FS-UAE (AROS ROM)")
    parser.add_argument("programs", nargs="+")
    parser.add_argument("--opt", "-O", action="store_true", help="compile with -O")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--autoclose", type=int, default=0, metavar="SECONDS",
                        help="compile .dash in test mode: the program ends by itself after SECONDS "
                             "(for programs that wait for the close gadget)")
    parser.add_argument("--kickstart", help="Kickstart ROM (default: $DASH_KICKSTART, else AROS)")
    args = parser.parse_args()
    try:
        results = run_programs(args.programs, args.timeout, args.opt, args.kickstart,
                               args.autoclose)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2
    failed = 0
    for r in results:
        status = "TIMEOUT" if r.timed_out else f"RC={r.rc}"
        print(f"=== {r.name}: {status}")
        if r.output:
            print(r.output, end="" if r.output.endswith("\n") else "\n")
        if r.timed_out or r.rc != 0:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
