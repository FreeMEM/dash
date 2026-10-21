#!/usr/bin/env python3
"""An emulated Amiga that stays on, to show windows one after another: the "Ver en Amiga" of the VS Code
extension's visual editor (docs/IDE_LOOP.md, task 20). Booting takes most of the time; here it is paid
once, and each window after costs its compilation and a second or two.

Inside, a small program (the watcher) waits for DH0:pide, runs DH0:vista (a program that opens the
window, takes its own picture of the screen with C:dash_shot as soon as it is open, and ends) and
leaves DH0:hecho. The picture is DH0:shot.dsh (the planes, from a planar screen: tools/amiga/shot.c)
or DH0:shot.ppm. Out here, the commands come on stdin, one per line, and the answers go to stdout:

    ready                          (when the Amiga is up)
    show <program> <picture.png> [<folder>]   ->  ok <picture.png>   |   error <why>
                                   (the folder's files go to DH0: first: the images the window names)
    quit                           (or the end of stdin)

    tools/emu_preview.py --machine a1200        # MUI 3.8 or 5 on Kickstart 3.1 ($DASH_EMU_SYS_MUI)
    tools/emu_preview.py --machine a1200-32     # AmigaOS 3.2 ($DASH_EMU_SYS_32_MUI)
    tools/emu_preview.py --machine rtg          # 68040 with a graphics card ($DASH_EMU_SYS_32_RTG)

The programs it shows must take their picture themselves: see editor/vscode/amigaPreview.js.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# the Workbench files with MUI of each machine (MUI needs a 68020: no A500)
MUI_SYSTEMS = {"a1200": "DASH_EMU_SYS_MUI", "a1200-32": "DASH_EMU_SYS_32_MUI", "rtg": "DASH_EMU_SYS_32_RTG"}

WATCHER = '''# The watcher of tools/emu_preview.py: runs DH0:vista each time DH0:pide appears, until DH0:fin
@header "#include <dos/dostags.h>"

@native func vigilar() -> Int
"""
    BPTR l, f;
    if ((f = Open((CONST_STRPTR)"DH0:vigia", MODE_NEWFILE))) Close(f);
    for (;;) {
        if ((l = Lock((CONST_STRPTR)"DH0:fin", ACCESS_READ))) { UnLock(l); return 0; }
        if ((l = Lock((CONST_STRPTR)"DH0:pide", ACCESS_READ))) {
            UnLock(l);
            DeleteFile((CONST_STRPTR)"DH0:pide");
            SystemTags((CONST_STRPTR)"DH0:vista >DH0:vista.txt", TAG_DONE);
            if ((f = Open((CONST_STRPTR)"DH0:hecho", MODE_NEWFILE))) Close(f);
        }
        Delay(5);
    }
"""
end

Main
    vigilar()
end
'''


def watcher_program() -> Path:
    """The watcher, compiled once (cached by its text)."""
    key = hashlib.sha1(WATCHER.encode()).hexdigest()[:12]
    exe = Path(os.path.expanduser(f"~/.cache/dash-emu/preview_watcher_{key}"))
    if not exe.exists():
        exe.parent.mkdir(parents=True, exist_ok=True)
        src = exe.with_suffix(".dash")
        src.write_text(WATCHER)
        run = subprocess.run([str(ROOT / "dash"), str(src), "-o", str(exe)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode != 0 or not exe.exists():
            raise RuntimeError("the watcher does not compile: " + (run.stdout + run.stderr)[-500:])
    return exe


def say(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def serve(machine, system=None, kickstart=None, window=False):
    m = emu_run.MACHINES[machine]
    kickstart = kickstart or os.environ.get(m["rom"])
    system = system or os.environ.get(MUI_SYSTEMS[machine])
    if not kickstart:
        raise RuntimeError(f"--machine {machine} needs ${m['rom']} (or --kickstart)")
    if not system:
        raise RuntimeError(f"--machine {machine} needs ${MUI_SYSTEMS[machine]} (Workbench files with MUI) or --system")
    watcher = watcher_program()
    disk = {}
    ended = threading.Event()
    failure = []

    def on_disk(hd):
        (hd / "C").mkdir(exist_ok=True)
        shutil.copy(emu_run.shot_tool(), hd / "C" / "dash_shot")
        disk["hd"] = hd

    def emulator():
        try:
            emu_run.run_programs([str(watcher)], timeout=0, kickstart=kickstart, system=system,
                                 workbench=m["workbench"], extra_config=m["config"], window=window,
                                 model=m["model"], on_disk=on_disk)
        except Exception as e:     # noqa: BLE001 (said to the other side)
            failure.append(str(e))
        ended.set()

    threading.Thread(target=emulator, daemon=True).start()
    deadline = time.time() + 240
    while time.time() < deadline and not ended.is_set() and not (disk.get("hd") and (disk["hd"] / "vigia").exists()):
        time.sleep(0.1)
    if not (disk.get("hd") and (disk["hd"] / "vigia").exists()):
        raise RuntimeError(failure[0] if failure else "the Amiga did not start (ROM, Workbench files?)")
    hd = disk["hd"]
    say("ready")
    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "quit":
            break
        if parts[0] != "show" or len(parts) not in (3, 4):
            say("error unknown command: " + line.strip())
            continue
        if ended.is_set():
            say("error the emulator ended")
            break
        program, png = parts[1], parts[2]
        if len(parts) == 4 and Path(parts[3]).is_dir():
            shutil.copytree(parts[3], hd, dirs_exist_ok=True)
        for name in ("hecho", "shot.ppm", "shot.dsh", "vista.txt"):
            (hd / name).unlink(missing_ok=True)
        shutil.copy(program, hd / "vista")
        (hd / "pide").write_text("")
        deadline = time.time() + 120
        while time.time() < deadline and not (hd / "hecho").exists() and not ended.is_set():
            time.sleep(0.05)
        # the picture: the planes (.dsh) of a planar screen, or a PPM; written with one Write, but it may
        # be seen half-way for a moment
        ppm, dsh = hd / "shot.ppm", hd / "shot.dsh"
        # (on an RTG screen shot.c writes a PPM, also when asked for .dsh)
        complete = lambda: any(emu_run.planar_complete(f) or emu_run._ppm_complete(f) for f in (dsh, ppm))   # noqa: E731
        for _ in range(100):
            if complete():
                break
            time.sleep(0.05)
        if (hd / "hecho").exists() and complete():
            if emu_run.planar_complete(dsh):
                emu_run.planar_to_png(dsh, Path(png))
            else:
                emu_run.ppm_to_png(dsh if emu_run._ppm_complete(dsh) else ppm, Path(png))
            say("ok " + png)
        else:
            out = (hd / "vista.txt").read_text(encoding="latin-1").strip() if (hd / "vista.txt").exists() else ""
            say("error " + (" ".join(out.split()) or ("the emulator ended" if ended.is_set() else "no picture")))
    (hd / "fin").write_text("")
    ended.wait(10)


def main():
    parser = argparse.ArgumentParser(description="An emulated Amiga that stays on, showing windows (see the top)")
    parser.add_argument("--machine", choices=sorted(MUI_SYSTEMS), default="a1200")
    parser.add_argument("--system", help="Workbench files with MUI (default: the machine's variable)")
    parser.add_argument("--kickstart", help="Kickstart ROM (default: the machine's variable)")
    parser.add_argument("--window", action="store_true", help="show the emulator's window")
    args = parser.parse_args()
    try:
        serve(args.machine, args.system, args.kickstart, args.window)
    except RuntimeError as e:
        say("error " + str(e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
