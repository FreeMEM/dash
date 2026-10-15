#!/usr/bin/env python3
"""Random programs for the reference counting (task 30d of docs/MEJORAS_LOOP.md).

    tools/fuzz_refcount.py                    # 40 programs, A1200 (Kickstart in $DASH_KICKSTART)
    tools/fuzz_refcount.py -n 200 --seed 7    # more, from another seed
    tools/fuzz_refcount.py --a500             # on the A500 ($DASH_KICKSTART_A500)
    tools/fuzz_refcount.py --keep DIR         # keep the .dash of the programs that fail
    tools/fuzz_refcount.py --normal           # normal builds (no --memcheck): only the output is compared

Each program moves structs (Punto, Caja), a list of structs, a list of Strings, a
String and a global through random statements: assignments, fields, list
elements and slices, functions that replace the field or global they got an
object from, a method, "for x in" that replaces elements, if/while/break. A
Python model runs the same statements, so the expected output is known. The
programs are built with --memcheck and run in FS-UAE, many per boot; a program
fails if its output differs from the model, if memcheck warns, or if anything
is alive at exit.
"""

import argparse
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

PREAMBLE = """\
struct Punto
    x: Int
    y: Int
end

struct Caja
    p: Punto
    q: Punto
    nombre: String
    datos: Array

    func mover(dx)
        self.p = Punto(self.p.x + dx, self.p.y)
        return self.p.x
    end
end

var G: Caja

func cambia(c: Caja, p: Punto) -> Int
    c.p = Punto(p.x + 1, p.y)
    return p.x
end

func cambia_global(p: Punto) -> Int
    G.p = Punto(p.y, p.x)
    return p.x + p.y
end

func nuevo(n) -> Punto
    t = Punto(n, n + 2)
    return t
end

func elige(a: Punto, b: Punto) -> Punto
    if a.x > b.x
        return a
    end
    return b
end

func caja_de(p: Punto) -> Caja
    return Caja(p, Punto(p.y, p.x), "c", [p.x, p.y])
end
"""


# ---- model ----------------------------------------------------------------

class Punto:
    def __init__(self, x, y):
        self.x, self.y = x, y


class Caja:
    def __init__(self, p, q, nombre, datos):
        self.p, self.q, self.nombre, self.datos = p, q, nombre, datos


def wrap(n):
    return (n + 2**31) % 2**32 - 2**31


class Gen:
    """Builds statements as (dash_text, python_action) pairs."""

    P = ["p1", "p2", "p3"]
    C = ["c1", "c2"]

    def __init__(self, rnd):
        self.r = rnd

    def i(self):
        return self.r.randrange(3)

    # an Int expression: a constant, k, or one field plus a constant (grows slowly)
    def expr(self, in_for=False):
        r = self.r
        c = r.randrange(10)
        opts = [
            (str(c), lambda e: c),
            ("k", lambda e: e["k"]),
        ]
        p = r.choice(self.P)
        opts.append((f"{p}.x + {c}", lambda e: e[p].x + c))
        cb = r.choice(self.C)
        f = r.choice(["p", "q"])
        opts.append((f"{cb}.{f}.y", lambda e: getattr(e[cb], f).y))
        i = self.i()
        opts.append((f"L[{i}].x", lambda e: e["L"][i].x))
        opts.append((f"G.q.x - {c}", lambda e: e["G"].q.x - c))
        j = self.i()
        opts.append((f"N[{j}].length", lambda e: len(e["N"][j])))
        opts.append(("s.length", lambda e: len(e["s"])))
        if in_for:
            opts.append(("x.x", lambda e: e["x"].x))
        return r.choice(opts)

    def stmt(self, depth=0, in_for=False):
        r = self.r
        pa, pb, pc = r.choice(self.P), r.choice(self.P), r.choice(self.P)
        ca, cb = r.choice(self.C), r.choice(self.C)
        i, j = self.i(), self.i()
        e1t, e1 = self.expr(in_for)
        e2t, e2 = self.expr(in_for)
        f = r.choice(["p", "q"])

        def setv(name, fn):
            def act(e):
                e[name] = fn(e)
            return act

        def setf(objname, field, fn):
            def act(e):
                v = fn(e)
                setattr(e[objname], field, v)
            return act

        def setl(lst, idx, fn):
            def act(e):
                v = fn(e)
                e[lst][idx] = v
            return act

        def add(fn):
            def act(e):
                e["acc"] = wrap(e["acc"] + fn(e))
            return act

        def cambia(cn, pfn):
            def call(e):
                p = pfn(e)
                c = e[cn]
                c.p = Punto(p.x + 1, p.y)
                return p.x
            return call

        def cambia_global(pfn):
            def call(e):
                p = pfn(e)
                e["G"].p = Punto(p.y, p.x)
                return p.x + p.y
            return call

        def mover(cn, dfn):
            def call(e):
                c = e[cn]
                c.p = Punto(c.p.x + dfn(e), c.p.y)
                return c.p.x
            return call

        def elige(afn, bfn):
            def call(e):
                a, b = afn(e), bfn(e)
                return a if a.x > b.x else b
            return call

        choices = [
            (f"{pa} = Punto({e1t}, {e2t})", setv(pa, lambda e: Punto(e1(e), e2(e)))),
            (f"{pa} = {pb}", setv(pa, lambda e: e[pb])),
            (f"{pa} = {cb}.{f}", setv(pa, lambda e: getattr(e[cb], f))),
            (f"{pa} = L[{i}]", setv(pa, lambda e: e["L"][i])),
            (f"{pa} = nuevo({e1t})", setv(pa, lambda e: Punto(e1(e), e1(e) + 2))),
            (f"{pa} = elige({pb}, {pc})", setv(pa, elige(lambda e: e[pb], lambda e: e[pc]))),
            (f"{pa} = elige({cb}.p, L[{i}])", setv(pa, elige(lambda e: e[cb].p, lambda e: e["L"][i]))),
            (f"{ca}.{f} = {pb}", setf(ca, f, lambda e: e[pb])),
            (f"{ca}.q = Punto({e1t}, {e2t})", setf(ca, "q", lambda e: Punto(e1(e), e2(e)))),
            (f"{ca}.p = L[{i}]", setf(ca, "p", lambda e: e["L"][i])),
            (f"{ca}.q = {cb}.p", setf(ca, "q", lambda e: e[cb].p)),
            (f"{ca} = {cb}", setv(ca, lambda e: e[cb])),
            (f"{ca} = caja_de({pb})",
             setv(ca, lambda e: Caja(e[pb], Punto(e[pb].y, e[pb].x), "c", [e[pb].x, e[pb].y]))),
            (f'{ca} = Caja({pb}, {pc}, "t" + ({e1t}), [{e2t}, 1])',
             setv(ca, lambda e: Caja(e[pb], e[pc], "t" + str(e1(e)), [e2(e), 1]))),
            (f"G = {ca}", setv("G", lambda e: e[ca])),
            (f"G.p = {pb}", setf("G", "p", lambda e: e[pb])),
            (f"G.q = L[{i}]", setf("G", "q", lambda e: e["L"][i])),
            (f"{pa} = G.{f}", setv(pa, lambda e: getattr(e["G"], f))),
            (f"L[{i}] = {pa}", setl("L", i, lambda e: e[pa])),
            (f"L[{i}] = Punto({e1t}, {e2t})", setl("L", i, lambda e: Punto(e1(e), e2(e)))),
            (f"L[{i}] = {ca}.{f}", setl("L", i, lambda e: getattr(e[ca], f))),
            (f"L[{i}] = L[{j}]", setl("L", i, lambda e: e["L"][j])),
            (f'N[{i}] = "n" + ({e1t})', setl("N", i, lambda e: "n" + str(e1(e)))),
            (f"s = N[{i}]", setv("s", lambda e: e["N"][i])),
            (f'N[{i}] = s + "x"', setl("N", i, lambda e: e["s"] + "x")),
            (f"{ca}.nombre = N[{j}]", setf(ca, "nombre", lambda e: e["N"][j])),
            (f"acc = acc + {ca}.nombre.length", add(lambda e: len(e[ca].nombre))),
            (f"acc = acc + cambia({ca}, {ca}.p)", add(cambia(ca, lambda e: e[ca].p))),
            (f"acc = acc + cambia({ca}, {cb}.q)", add(cambia(ca, lambda e: e[cb].q))),
            (f"acc = acc + cambia({ca}, L[{i}])", add(cambia(ca, lambda e: e["L"][i]))),
            ("acc = acc + cambia(G, G.p)", add(cambia("G", lambda e: e["G"].p))),
            ("acc = acc + cambia_global(G.p)", add(cambia_global(lambda e: e["G"].p))),
            (f"acc = acc + cambia_global({pa})", add(cambia_global(lambda e: e[pa]))),
            (f"acc = acc + cambia_global(L[{i}])", add(cambia_global(lambda e: e["L"][i]))),
            (f"acc = acc + {ca}.mover({e1t})", add(mover(ca, e1))),
            (f"acc = acc + {e1t}", add(e1)),
            (f"acc = acc + {ca}.datos[0]", add(lambda e: e[ca].datos[0])),
            (f"{ca}.datos = [{e1t}, {e2t}]", setf(ca, "datos", lambda e: [e1(e), e2(e)])),
            ("L2 = L", setv("L2", lambda e: e["L"])),
            (f"L2[{i}] = Punto({e1t}, 0)", setl("L2", i, lambda e: Punto(e1(e), 0))),
            ("L = [Punto(1, 1), L[2], L[0]]", setv("L", lambda e: [Punto(1, 1), e["L"][2], e["L"][0]])),
            (f"T = L[{min(i, j)}:{max(i, j) + 1}]",
             setv("T", lambda e: e["L"][min(i, j):max(i, j) + 1])),
            ("acc = acc + T[0].x + T.length", add(lambda e: e["T"][0].x + len(e["T"]))),
        ]
        if depth < 1:
            n = r.randrange(1, 3)
            body = [self.stmt(depth + 1, True) for _ in range(n)]
            k = r.randrange(3)

            def for_act(e, body=body):
                for x in e["L"]:      # the live list, like Dash (it holds the array, reads elements)
                    e["x"] = x
                    e["acc"] = wrap(e["acc"] + x.x)
                    for _, act in body:
                        act(e)
            choices.append(("for x in L\n    acc = acc + x.x\n"
                            + "".join("    " + t.replace("\n", "\n    ") + "\n" for t, _ in body) + "end",
                            for_act))
            body2 = [self.stmt(depth + 1, in_for) for _ in range(n)]

            def if_act(e, body=body2, k=k):
                if e["k"] % 3 == k:
                    for _, act in body:
                        act(e)
            choices.append((f"if k % 3 == {k}\n"
                            + "".join("    " + t.replace("\n", "\n    ") + "\n" for t, _ in body2) + "end",
                            if_act))
            body3 = [self.stmt(depth + 1, in_for) for _ in range(n)]

            def while_act(e, body=body3):
                e["w"] = 0
                while e["w"] < 3:
                    e["w"] += 1
                    if e["w"] == 2:
                        break
                    for _, act in body:
                        act(e)
            choices.append(("w = 0\nwhile w < 3\n    w = w + 1\n    if w == 2\n        break\n    end\n"
                            + "".join("    " + t.replace("\n", "\n    ") + "\n" for t, _ in body3) + "end",
                            while_act))
        if in_for:   # no "L2 = L"/"L = [...]"/slices inside a for: same as outside, kept simple
            choices = [c for c in choices if not c[0].startswith(("L2", "L =", "T", "acc = acc + T"))]
        return r.choice(choices)


CHECK = ("p1.x + p2.y + p3.x + c1.p.x + c1.q.y + c2.p.y + c2.q.x + G.p.x + G.q.y"
         " + L[0].x + L[1].y + L[2].x + N[0].length + N[2].length + s.length"
         " + c1.nombre.length + c2.datos[1] + L2[1].x")


def check(e):
    return wrap(e["p1"].x + e["p2"].y + e["p3"].x + e["c1"].p.x + e["c1"].q.y + e["c2"].p.y
                + e["c2"].q.x + e["G"].p.x + e["G"].q.y + e["L"][0].x + e["L"][1].y + e["L"][2].x
                + len(e["N"][0]) + len(e["N"][2]) + len(e["s"]) + len(e["c1"].nombre)
                + e["c2"].datos[1] + e["L2"][1].x)


def program(seed, n_stmts=30, rounds=12):
    """Dash source and expected output of one random program."""
    gen = Gen(random.Random(seed))
    stmts = [gen.stmt() for _ in range(n_stmts)]
    body = "".join("    " + t.replace("\n", "\n    ") + "\n" for t, _ in stmts)
    src = (f"# fuzz_refcount seed {seed}\n" + PREAMBLE + "\nfunc ronda(k) -> Int\n"
           "    acc = 0\n    p1 = Punto(1, 2)\n    p2 = Punto(3, 4)\n    p3 = nuevo(k)\n"
           '    c1 = Caja(p1, p2, "a", [1, 2])\n    c2 = caja_de(p3)\n'
           "    L = [Punto(5, 6), Punto(7, 8), Punto(9, 10)]\n    L2 = L\n    T = L[0:2]\n"
           '    N = ["x", "y", "z"]\n    s = "s"\n    x = 0\n    w = 0\n'
           + body + f"    return acc + {CHECK}\nend\n\nMain\n"
           '    G = Caja(Punto(0, 0), Punto(0, 0), "g", [0])\n'
           f"    for k in (1..{rounds})\n        Print ronda(k)\n    end\nend\n")
    g = Caja(Punto(0, 0), Punto(0, 0), "g", [0])
    out = []
    for k in range(1, rounds + 1):
        e = {"k": k, "acc": 0, "G": g}
        e["p1"], e["p2"] = Punto(1, 2), Punto(3, 4)
        e["p3"] = Punto(k, k + 2)
        e["c1"] = Caja(e["p1"], e["p2"], "a", [1, 2])
        e["c2"] = Caja(e["p3"], Punto(e["p3"].y, e["p3"].x), "c", [e["p3"].x, e["p3"].y])
        e["L"] = [Punto(5, 6), Punto(7, 8), Punto(9, 10)]
        e["L2"] = e["L"]
        e["T"] = e["L"][0:2]
        e["N"], e["s"] = ["x", "y", "z"], "s"
        for _, act in stmts:
            act(e)
        g = e["G"]
        out.append(str(wrap(e["acc"] + check(e))))
    return src, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-n", type=int, default=40, help="programs (default 40)")
    ap.add_argument("--seed", type=int, default=1, help="first seed")
    ap.add_argument("--batch", type=int, default=20, help="programs per emulator boot")
    ap.add_argument("--a500", action="store_true", help="run on the A500 ($DASH_KICKSTART_A500)")
    ap.add_argument("--keep", metavar="DIR", help="copy the .dash of failing programs here")
    ap.add_argument("--normal", action="store_true", help="build without --memcheck (the code users run)")
    args = ap.parse_args()
    from emu_run import run_programs
    import os
    kick = os.environ.get("DASH_KICKSTART_A500" if args.a500 else "DASH_KICKSTART")
    config = "amiga_model = A500\n" if args.a500 else ""
    want_summary = "memcheck: vivos 0 objetos y 0 strings (escapados 0 y 0), errores 0"
    failed = 0
    with tempfile.TemporaryDirectory(prefix="dash_fuzz_") as tmp:
        tmp = Path(tmp)
        seeds = list(range(args.seed, args.seed + args.n))
        for b in range(0, len(seeds), args.batch):
            batch = seeds[b:b + args.batch]
            exes, expected = [], {}
            for seed in batch:
                src, out = program(seed)
                dash = tmp / f"fz{seed}.dash"
                dash.write_text(src)
                exe = tmp / f"fz{seed}"
                flags = [] if args.normal else ["--memcheck"]
                r = subprocess.run([sys.executable, str(ROOT / "dash"), *flags, str(dash), "-o", str(exe)],
                                   capture_output=True, text=True)
                if r.returncode != 0 or not exe.exists():
                    print(f"seed {seed}: does not compile\n{(r.stdout + r.stderr)[-600:]}")
                    failed += 1
                    if args.keep:
                        Path(args.keep).mkdir(parents=True, exist_ok=True)
                        shutil.copy(dash, args.keep)
                    continue
                exes.append(exe)
                expected[exe.name] = out if args.normal else out + [want_summary]
            results = run_programs(exes, timeout=60 + 30 * len(exes) * (4 if args.a500 else 1),
                                   kickstart=kick, extra_config=config)
            for exe, res in zip(exes, results):
                got = [l.rstrip() for l in (res.output or "").splitlines()]
                want = expected[exe.name]
                if res.timed_out or got != want:
                    failed += 1
                    diff = next((i for i, (a, w) in enumerate(zip(got, want)) if a != w), min(len(got), len(want)))
                    print(f"seed {exe.name[2:]}: {'TIMEOUT ' if res.timed_out else ''}line {diff + 1}: "
                          f"got {got[diff] if diff < len(got) else '<end>'!r}, "
                          f"expected {want[diff] if diff < len(want) else '<end>'!r}")
                    if args.keep:
                        Path(args.keep).mkdir(parents=True, exist_ok=True)
                        shutil.copy(tmp / f"{exe.name}.dash", args.keep)
            print(f"{b + len(batch)}/{len(seeds)} programs, {failed} failed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
