#!/usr/bin/env python3
"""Data and page of the Dash benchmark dashboard (task 28 of docs/MEJORAS_LOOP.md).

    tools/bench_report.py            # writes build/bench_report/

Reads tests/bench/results.json (written by tools/bench.py --save) and writes:
  runs.csv    run, short, label, commit, date, total_bytes, programs
  ns.csv      run, short, machine, benchmark, ns, def
  mem.csv     run, short, machine, name, bytes
  sizes.csv   run, short, program, bytes
  index.html  the page (a copy of tools/bench_report.html)

The page is a Claude "Dashboard" artifact: it reads those CSV files as its
datasets. To update it after a new `bench.py --save`, run this script and ask
Claude to upload the four CSV files to the dashboard again (its URL is in
docs/MEJORAS_LOOP.md, task 28).

`def` counts the definitions of a benchmark: when a benchmark program changed
what it measures, its later runs get the next number and the page does not
compare across them. `commit` is the HEAD when the run was measured, so the
change named by the label is not in it yet (bench.py runs before the commit).
"""

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "tests" / "bench" / "results.json"
PAGE = ROOT / "tools" / "bench_report.html"
OUT = ROOT / "build" / "bench_report"

# benchmark -> label prefix of the first run of each later definition
REDEFINED = {
    # 26e2: GCC folded loops without effects; they now store into bench_sink
    "int_loop": ["26e2:"],
    "while_loop": ["26e2:"],
    "func_call": ["26e2:"],
    "string_compare": ["26e2:"],      # also compares pal[i % 2], not a constant
    # 27d: the loop now uses the character (it was folded differently by -O2 and -Os)
    "string_chars_26": ["27d:"],
}
# (label prefix, benchmark): values that are wrong and are left out
INVALID = {
    # fastfp was not linked yet: Float went through mathieeesingbas.library
    ("26d: suma y multiplicación Float propias", "float_mul"),
    ("26d: suma y multiplicación Float propias", "float_mul_add"),
}


def short(label: str) -> str:
    """'26e2: sin marcas...' -> '26e2'; 'base (antes de optimizar)' -> 'base'."""
    head = label.split(":", 1)[0] if ":" in label else label.split(" (", 1)[0]
    return head.strip() or "?"


def main():
    runs = json.loads(RESULTS.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    shorts, seen = [], {}
    for r in runs:                       # 26d2 twice -> 26d2, 26d2b
        s = short(r["label"])
        seen[s] = seen.get(s, 0) + 1
        shorts.append(s if seen[s] == 1 else s + "abcdefgh"[seen[s] - 1])

    def write(name, header, rows):
        with open(OUT / name, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write("runs.csv", ["run", "short", "label", "commit", "date", "total_bytes", "programs"],
          [[i, shorts[i], r["label"], r["commit"], r["date"], sum(r["sizes"].values()), len(r["sizes"])]
           for i, r in enumerate(runs)])

    ns_rows = []
    for i, r in enumerate(runs):
        for machine, values in r["ns"].items():
            for bench, ns in sorted(values.items()):
                if any(r["label"].startswith(p) and bench == b for p, b in INVALID):
                    continue
                d = 1 + sum(1 for k, rr in enumerate(runs[:i + 1])
                            for p in REDEFINED.get(bench, []) if rr["label"].startswith(p))
                ns_rows.append([i, shorts[i], machine, bench, ns, d])
    write("ns.csv", ["run", "short", "machine", "benchmark", "ns", "def"], ns_rows)

    write("mem.csv", ["run", "short", "machine", "name", "bytes"],
          [[i, shorts[i], m, n, b] for i, r in enumerate(runs)
           for m, vals in r.get("mem", {}).items() for n, b in sorted(vals.items())])

    write("sizes.csv", ["run", "short", "program", "bytes"],
          [[i, shorts[i], p, b] for i, r in enumerate(runs) for p, b in sorted(r["sizes"].items())])

    shutil.copy(PAGE, OUT / "index.html")
    print(f"{len(runs)} ejecuciones, {len(ns_rows)} medidas -> {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
