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

- The six tests give the same output as the Python Dash on A1200 and A500 with the 3.1 ROM.
- `build/dashc.amiga` compiles the six inside an emulated A500; the executables are byte-identical
  to the PC ones and run.
- The executables take 1.5 to 3 KB (6 to 9 KB with gcc).
- Speed (`bench/bench_enteros.dash`, times the time of gcc `-O2`): 1.1 to 1.7 on A500 and 1.1 to 2.4
  on A1200; recursion (fib) is faster than with gcc (0.6 and 0.8).
- Like gcc with `static` functions, a small function or one called from a single place is copied where
  it is called (not if it is recursive); functions never really called are left out of the executable.
