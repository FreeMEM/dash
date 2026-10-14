#!/usr/bin/env python3
"""Benchmarks of Dash in FS-UAE: speed per feature and executable sizes.

    tools/bench.py                 # run, print the table, compare with the last saved run
    tools/bench.py --save LABEL    # also store the run in tests/bench/results.json
    tools/bench.py --machines a1200

Each tests/bench/bench_*.dash prints "BENCH name iterations eclock_ticks freq"
(see bench_lib.dash); this script turns them into nanoseconds per iteration.
Machines (cycle-exact speed, not "max"):
  a500   68000 7 MHz, Kickstart 3.1 A500 ROM ($DASH_KICKSTART_A500)
  a1200  68020 14 MHz, Kickstart 3.1 A1200 ROM ($DASH_KICKSTART)
Sizes: every bench program and every example, compiled with the default flags.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from emu_run import run_programs  # noqa: E402

RESULTS = ROOT / "tests" / "bench" / "results.json"
MACHINES = {
    "a500": {"rom_env": "DASH_KICKSTART_A500", "config": "amiga_model = A500\nuae_cpu_speed = real\n"},
    "a1200": {"rom_env": "DASH_KICKSTART", "config": "uae_cpu_speed = real\n"},
}


def compile_all(paths, out_dir):
    exes = {}
    for src in paths:
        exe = Path(out_dir) / src.stem
        r = subprocess.run([sys.executable, str(ROOT / "dash"), str(src), "-o", str(exe)],
                           capture_output=True, text=True)
        if r.returncode == 0 and exe.exists():
            exes[src] = exe
        else:
            print(f"! {src}: does not compile", file=sys.stderr)
    return exes


def parse(output):
    out = {}
    for line in (output or "").splitlines():
        parts = line.split()
        if len(parts) == 5 and parts[0] == "BENCH":
            _, name, iters, ticks, freq = parts
            out[name] = round(int(ticks) * 1e9 / int(freq) / int(iters))   # ns per iteration
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--save", metavar="LABEL", help="store this run in tests/bench/results.json")
    ap.add_argument("--machines", default="a500,a1200")
    args = ap.parse_args()

    benches = sorted((ROOT / "tests" / "bench").glob("bench_*.dash"))
    benches = [b for b in benches if b.stem != "bench_lib"]
    examples = sorted((ROOT / "examples").glob("*.dash"))
    run = {"commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                    text=True, cwd=ROOT).stdout.strip(),
           "date": time.strftime("%Y-%m-%d %H:%M"), "label": args.save or "", "ns": {}, "sizes": {}}
    with tempfile.TemporaryDirectory() as tmp:
        exes = compile_all(benches + examples, tmp)
        for src, exe in exes.items():
            run["sizes"][src.stem] = exe.stat().st_size
        for machine in args.machines.split(","):
            m = MACHINES[machine]
            rom = os.environ.get(m["rom_env"])
            if not rom:
                print(f"! {machine}: set ${m['rom_env']} to its Kickstart ROM", file=sys.stderr)
                continue
            results = run_programs([exes[b] for b in benches if b in exes], timeout=900, kickstart=rom,
                                   extra_config=m["config"])
            run["ns"][machine] = {}
            for r in results:
                if r.timed_out:
                    print(f"! {machine}/{r.name}: timeout", file=sys.stderr)
                run["ns"][machine].update(parse(r.output))

    history = json.loads(RESULTS.read_text()) if RESULTS.exists() else []
    prev = history[-1] if history else None
    names = sorted({n for m in run["ns"].values() for n in m})
    print(f"{'benchmark':22}" + "".join(f"{m + ' ns':>14}{'antes':>10}" for m in run["ns"]))
    for n in names:
        row = f"{n:22}"
        for m, vals in run["ns"].items():
            old = prev["ns"].get(m, {}).get(n) if prev else None
            row += f"{vals.get(n, '-'):>14}" + (f"{old:>10}" if old else f"{'':>10}")
        print(row)
    total = sum(v for k, v in run["sizes"].items())
    old_total = sum(prev["sizes"].values()) if prev else None
    print(f"tamaño total {len(run['sizes'])} ejecutables: {total} bytes" + (f" (antes {old_total})" if prev else ""))
    if args.save:
        history.append(run)
        RESULTS.write_text(json.dumps(history, indent=1) + "\n")
        print(f"guardado en {RESULTS.relative_to(ROOT)} como '{args.save}'")


if __name__ == "__main__":
    main()
