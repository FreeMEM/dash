"""emu_tools.py JOBFILE OUTDIR [timeout]: runs an AmigaDOS script in FS-UAE with the compilers copied from
Coffin on a second drive (TOOLS:). Env: MACHINE=fast (68040, default) | a1200 | a500 (real speed, for
measuring), SHOT=seconds (screenshot to shot.png), FILES=dir copied to DH0:files."""
import os, sys, shutil
sys.path.insert(0, os.path.expanduser("~/Projects/FreeMEMLang/tools"))
from emu_run import run_programs
job, out = sys.argv[1], sys.argv[2]
timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 300
here = os.path.dirname(os.path.abspath(__file__))


def add(hd):
    shutil.copy(job, os.path.join(hd, "job"))
    if os.environ.get("FILES"):
        shutil.copytree(os.environ["FILES"], os.path.join(hd, "files"), dirs_exist_ok=True)


machine = os.environ.get("MACHINE", "fast")
tools = "hard_drive_1 = " + os.path.join(here, "coffin", "t") + "\nhard_drive_1_label = TOOLS\nhard_drive_0_priority = 127\nhard_drive_1_priority = -128\n"
kick31 = os.path.expanduser("~/Descargas/Telegram Desktop/ks31a1200.rom")
kick32 = os.path.expanduser("~/Descargas/Telegram Desktop/Kickstart v3.2.3 A1200.47.115_Pack_noSCSI.rom")
if machine == "fast":
    cfg, rom, model = "cpu = 68040\nfpu = 68040\nuae_cpu_speed = max\nzorro_iii_memory = 131072\n", kick32, "A1200"
elif machine == "a1200":
    cfg, rom, model = "uae_cpu_speed = real\n", kick31, "A1200"
else:
    cfg, rom, model = "amiga_model = A500\nuae_cpu_speed = real\n", os.path.expanduser(
        "~/.cache/dash-emu/kick/kick31_a500.rom"), "A500"
system = os.path.expanduser("~/.cache/dash-emu/sys32" if machine == "fast" else "~/.cache/dash-emu/sys31")
shot = (float(os.environ["SHOT"]), os.path.join(here, "shot.png")) if os.environ.get("SHOT") else None
rs = run_programs([os.path.join(here, "shell.dash")], timeout=timeout, kickstart=rom, system=system,
                  extra_config=cfg + tools, keep=out, on_disk=add, screenshot=shot, model=model)
print(rs[0].output, "timeout" if rs[0].timed_out else "")
