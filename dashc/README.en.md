# dashc: a self-sufficient Dash proof of concept

[Español](README.md)

`dashc` compiles a `.dash` file into an Amiga executable without a C compiler: it generates 68000 code,
links it with the runtime (precompiled and embedded in `dashc`) and writes the Hunk file. It is written
in C and the same code builds for the PC and for the Amiga.

```bash
make                     # dashc for this computer
./dashc prog.dash -o prog
make amiga               # build/dashc.amiga: dashc running on the Amiga (68000, OS 2.0+)
make test                # tests/*.dash with dashc and with ./dash: same output on A1200 and A500 (FS-UAE)
python3 bench/bench_run.py   # speed against ./dash (gcc -O2) on A500 and A1200 at real speed
make runtime             # rebuilds runtime/dashrt.o with bebbo's gcc (it is in git: not needed otherwise)
```

## What it understands

Integers (decimal, `0x`, `$`, `0b`), `Bool`, `const`, globals with `var x: Int = constant`, local
variables, functions with parameters and `return`, `if`/`elif`/`else`, `while`, `for` over a range
(`step`, backwards), `break`, `continue`, short-circuit `and`/`or`/`not`, every integer operator and
`Print` of an integer, a Bool or a string literal (in Latin-1).

Everything else is missing: strings in variables, arrays, structs, Float, builtins, windows, `@native`...

## How it is built

| File | What it does |
|------|--------------|
| `src/lexer.c`, `src/parser.c` | Text to tree, with the grammar of `compiler/grammar.py` |
| `src/gen68k.c` | 68000 code: the value in d0, C-like calls; each function is generated twice to keep the most used variables in d2-d7 |
| `src/hunk.c` | Reads the runtime's Hunk object, joins the hunks and writes the executable |
| `runtime/rt.c`, `runtime/rt_math.s` | Startup, `Print`, 32-bit multiply and divide on a 68000 |

## What was checked

- The seven tests give the same output as the Python Dash on A1200 and A500 with the 3.1 ROM.
- `build/dashc.amiga` compiles the seven inside an emulated A500 and A1200; the executables are
  byte-identical to the PC ones and run.
- The executables take 1.7 to 4.7 KB (6 to 9.5 KB with gcc).
- Speed (`bench/bench_enteros.dash`, times the time of gcc `-O2`; below 1 is faster): on average
  0.93 on A500 and 1.00 on A1200. The slowest, 1.14 (counting bits on A1200); the fastest,
  recursion (fib, 0.55 and 0.75).
- Optimizations, like gcc's: variables in d2-d7; a small function or one called from a single place
  is copied where it is called (not if it is recursive), and a one-line one as an expression; a `for`
  or a `while` that only adds 1 counts with `dbra`; `i * k` in a loop is kept as a running sum; a
  variable assigned once with a fixed value is a constant; a `for` index has a known range, and with
  it 16-bit division and product need no checks; multiply and divide try the 16-bit case inline; on
  a 68020 or better the runtime uses `divs.l` and `muls.l`.
