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
    tools/emu_run.py --autoclose 20 --screenshot 15 shot.png ventana.dash   # picture of the screen

Libraries that are not in the Kickstart ROM (asl.library, diskfont.library...)
come from $DASH_EMU_SYS (or --system): a directory with Libs/, C/ (Assign, MakeDir)
and Classes/ (ReAction) taken from a Workbench disk (see tools/emu_sys_from_hdf.sh).
Any other drawer in it is copied too, and the lines of its S/Startup-Extra run after
the assigns (MUI: see tools/emu_sys_mui.sh).

    tools/emu_run.py --kickstart kick323.rom --system ~/.cache/dash-emu/sys32 --workbench prog.dash

--workbench runs C:LoadWB from those files before the programs, as on a real Amiga:
in AmigaOS 3.2 window.class (ReAction) waits for the Workbench when it is opened.

--debug CMD (repeatable) talks to FS-UAE's debugger: a program that calls debug_break()
stops the emulated machine there, each CMD is sent in turn while the debugger waits
("r" registers, "m addr n" memory, "d addr n" disassembly, "t" one instruction, "H n"
history...), then "g" so the program goes on. What the debugger said is printed at the end.

    tools/emu_run.py --debug r --debug "m 4 2" prog.dash

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
import threading
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
volume = 0
uae_sound_output = interrupts
automatic_input_grab = 0
uae_cpu_speed = max
{kickstart}"""


class EmuResults(list):
    """The EmuResult of each program; debugger: what FS-UAE's debugger printed (--debug)."""
    debugger = ""


def _debugger_session(proc, commands, transcript):
    """Read FS-UAE's console; each time its debugger waits (a '>' prompt after it was
    activated), send the next command, or "g" once they are used up."""
    pending = list(commands)
    active = False
    since = b""
    while True:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
        except OSError:
            break
        if not chunk:
            break
        transcript.append(chunk)
        since += chunk
        active = active or b"activate_console" in since or b"Next PC:" in since
        if active and since.endswith(b">"):
            command = pending.pop(0) if pending else "g"
            try:
                proc.stdin.write((command + "\n").encode())
                proc.stdin.flush()
            except OSError:
                break
            transcript.append(command.encode() + b"\n")
            since = b""


class EmuResult:
    def __init__(self, name, output, rc):
        self.name = name
        self.output = output   # text the program printed (None if it never ran)
        self.rc = rc           # return code, or None on timeout

    @property
    def timed_out(self):
        return self.rc is None


def compile_dash(src: Path, exe: Path, optimize: bool, autoclose: int = 0, fpu: bool = False) -> None:
    cmd = [sys.executable, str(ROOT / "dash"), str(src), "-o", str(exe)]
    if optimize:
        cmd.append("-O")
    if fpu:
        cmd.append("--fpu")
    env = dict(os.environ)
    if autoclose:
        env["DASH_TEST_AUTOCLOSE"] = str(autoclose)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0 or not exe.exists():
        raise RuntimeError(f"{src}: compile failed\n{result.stdout}{result.stderr}")


SHOT_SOURCE = Path(__file__).resolve().parent / "amiga" / "shot.c"


def shot_tool() -> Path:
    """tools/amiga/shot.c built with the Amiga toolchain (cached next to the emulator files)."""
    exe = Path(os.path.expanduser("~/.cache/dash-emu/shot"))
    if not exe.exists() or exe.stat().st_mtime < SHOT_SOURCE.stat().st_mtime:
        exe.parent.mkdir(parents=True, exist_ok=True)
        gcc = "/opt/amiga/bin/m68k-amigaos-gcc"
        build = subprocess.run([gcc, "-O2", "-noixemul", "-o", str(exe), str(SHOT_SOURCE)],
                               capture_output=True, text=True)
        if build.returncode != 0:
            raise RuntimeError(f"cannot build {SHOT_SOURCE}: {build.stderr[-300:]}")
    return exe


def ppm_to_png(ppm: Path, png: Path):
    """Binary PPM (P6) from shot.c to PNG, without extra Python packages."""
    import struct
    import zlib
    data = ppm.read_bytes()
    parts = data.split(b"\n", 3)
    width, height = map(int, parts[1].split())
    pixels = parts[3]
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def run_programs(programs, timeout: float = 60.0, optimize: bool = False,
                 kickstart: str = None, autoclose: int = 0, extra_config: str = "",
                 keep: str = None, fpu: bool = False, system: str = None, workbench: bool = False,
                 screenshot: tuple = None, args: list = None, background: list = None,
                 debug: list = None):
    """programs: list of .dash sources or Amiga executables. system: Workbench
    files directory (default $DASH_EMU_SYS). screenshot: (seconds, file.png) saves the
    front screen that many seconds after boot. background: (program, arguments) pairs
    started with Run before the programs, e.g. one that clicks in their windows; their
    output goes to DH0:bg<i>.txt (keep= to read it). debug: commands for FS-UAE's debugger
    when a program calls debug_break() (see --debug). Returns one EmuResult per program, in
    order, in an EmuResults list (.debugger: the debugger's text)."""
    if not shutil.which("fs-uae"):
        raise RuntimeError("fs-uae not found")
    with tempfile.TemporaryDirectory(prefix="dash_emu_") as tmp:
        tmp = Path(tmp)
        hd = tmp / "hd"
        (hd / "S").mkdir(parents=True)
        # Optional mini system from a Workbench disk ($DASH_EMU_SYS): Libs/ (asl,
        # diskfont... are not in the ROM) and C/ (Assign, MakeDir). The boot
        # volume's drawers are LIBS:, C:, FONTS:...; with C:Assign the volumes the
        # Workbench Startup-Sequence assigns are created too, or the first Lock on
        # ENV: or LOCALE: opens a "please insert volume" requester and waits.
        for drawer in ("Fonts", "Locale", "Devs/Keymaps"):
            (hd / drawer).mkdir(parents=True)
        lines = []
        names = []
        system = system or os.environ.get("DASH_EMU_SYS")
        if system:
            if not Path(system).is_dir():
                raise RuntimeError(f"Workbench files directory not found: {system}")
            for sub in sorted(Path(system).iterdir()):   # Libs, C, Classes, MUI...
                if sub.is_dir() and sub.name != "S":
                    shutil.copytree(sub, hd / sub.name, dirs_exist_ok=True)
            if (hd / "C" / "Assign").exists() and (hd / "C" / "MakeDir").exists():
                lines += ["C:MakeDir RAM:T RAM:ENV RAM:ENV/Sys RAM:Clipboards",
                          "C:Assign ENV: RAM:ENV", "C:Assign T: RAM:T", "C:Assign CLIPS: RAM:Clipboards",
                          "C:Assign LOCALE: SYS:Locale", "C:Assign KEYMAPS: DEVS:Keymaps"]
                if (hd / "Classes").is_dir():   # window.class, gadgets/layout.gadget...
                    lines.append("C:Assign LIBS: SYS:Classes ADD")
                if (hd / "C" / "AddDataTypes").exists() and (hd / "Devs" / "DataTypes").is_dir():
                    lines.append("C:AddDataTypes REFRESH QUIET")   # picture formats (MUI Dtpic)
            # Extra boot commands of that system (MUI: its assigns, see tools/emu_sys_mui.sh)
            extra = Path(system) / "S" / "Startup-Extra"
            if extra.is_file():
                lines += [l for l in extra.read_text().splitlines() if l.strip()]
        if workbench:
            if not (hd / "C" / "LoadWB").exists():
                raise RuntimeError("--workbench needs C/LoadWB in the Workbench files (tools/emu_sys_from_hdf.sh)")
            lines.append("C:LoadWB")
        if screenshot:
            (hd / "C").mkdir(exist_ok=True)
            shutil.copy(shot_tool(), hd / "C" / "dash_shot")
            lines.append(f"Run >NIL: C:dash_shot {int(float(screenshot[0]) * 50)} DH0:shot.ppm")
        for i, (prog, bg_args) in enumerate(background or []):
            prog = Path(prog)
            exe = hd / f"b{i}"
            if prog.suffix == ".dash":
                compile_dash(prog, exe, optimize, 0, fpu)
            else:
                shutil.copy(prog, exe)
            # the redirection after the command is the program's (before it, only Run's message)
            lines.append(f"Run >NIL: DH0:b{i} >DH0:bg{i}.txt{' ' + bg_args if bg_args else ''}")
        for i, prog in enumerate(programs):
            prog = Path(prog)
            exe = hd / f"p{i}"
            if prog.suffix == ".dash":
                compile_dash(prog, exe, optimize, autoclose, fpu)
            else:
                shutil.copy(prog, exe)
            names.append(prog.name)
            extra = f" {args[i]}" if args and i < len(args) and args[i] else ""   # Shell arguments
            lines.append(f"DH0:p{i}{extra} >DH0:out{i}.txt")
            lines.append(f'Echo "$RC" >DH0:rc{i}.txt')
        lines.append('Echo "fin" >DH0:done.txt')
        (hd / "S" / "Startup-Sequence").write_text("\n".join(lines) + "\n")
        config = tmp / "run.fs-uae"
        kickstart = kickstart or os.environ.get("DASH_KICKSTART")
        if kickstart and not Path(kickstart).is_file():
            raise RuntimeError(f"Kickstart ROM not found: {kickstart}")
        ks_line = f"kickstart_file = {kickstart}\n" if kickstart else ""
        config.write_text(FSUAE_CONFIG.format(hd=hd, kickstart=ks_line) + extra_config)

        env = dict(os.environ, SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy", ALSOFT_DRIVERS="null")
        transcript = []
        if debug is not None:   # the debugger talks on FS-UAE's stdin/stdout
            proc = subprocess.Popen(["fs-uae", str(config)], cwd=tmp, env=env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            reader = threading.Thread(target=_debugger_session, args=(proc, debug, transcript), daemon=True)
            reader.start()
        else:
            # no stdin: a debug_break() without --debug must not wait for commands from the terminal
            proc = subprocess.Popen(["fs-uae", str(config)], cwd=tmp, env=env, stdin=subprocess.DEVNULL,
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

        if keep:
            shutil.copytree(hd, keep, dirs_exist_ok=True)
        if screenshot:
            if (hd / "shot.ppm").exists():
                ppm_to_png(hd / "shot.ppm", Path(screenshot[1]))
            else:
                print(f"no screenshot (did a program still run after {screenshot[0]} s?)", file=sys.stderr)
        results = EmuResults()
        text = b"".join(transcript).decode("latin-1")
        start = text.find("activate_console")
        if start >= 0:   # from the first stop on, without the stub's note
            text = text[text.find("\n", start) + 1:]
            results.debugger = "\n".join(l for l in text.splitlines()
                                         if not l.startswith(("UAE: ", " -- stub --")))
        for i, name in enumerate(names):
            out_file, rc_file = hd / f"out{i}.txt", hd / f"rc{i}.txt"
            output = out_file.read_text(encoding="latin-1") if out_file.exists() else None  # AmigaOS texts
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
    parser.add_argument("--fpu", action="store_true", help="compile .dash with --fpu (use --set fpu=68882)")
    parser.add_argument("--system", metavar="DIR", help="Workbench files (Libs/, C/, Classes/; default: $DASH_EMU_SYS)")
    parser.add_argument("--workbench", action="store_true", help="run C:LoadWB first (AmigaOS 3.2 ReAction needs it)")
    parser.add_argument("--keep", metavar="DIR", help="copy the emulated disk (outputs, files the programs wrote) to DIR")
    parser.add_argument("--screenshot", nargs=2, metavar=("SECONDS", "FILE.png"),
                        help="save the front screen SECONDS after boot (tools/amiga/shot.c); "
                             "use --autoclose so the program is still open then")
    parser.add_argument("--debug", action="append", metavar="CMD",
                        help="FS-UAE debugger command when a program calls debug_break() "
                             "(repeatable; then \"g\": see the help at the top of this file)")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="extra FS-UAE option, e.g. --set amiga_model=A500 (repeatable)")
    args = parser.parse_args()
    try:
        results = run_programs(args.programs, args.timeout, args.opt, args.kickstart,
                               args.autoclose,
                               "".join(f"{kv.split('=', 1)[0].strip()} = {kv.split('=', 1)[1].strip()}\n"
                                       for kv in args.set),
                               args.keep, args.fpu, args.system, args.workbench, args.screenshot,
                               debug=args.debug)
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
    if args.debug is not None:
        print("=== debugger")
        print(results.debugger or "(no program called debug_break)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
