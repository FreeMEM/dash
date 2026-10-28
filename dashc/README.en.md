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
| `src/gen68k.c` | 68000 code: the value in d0, a5 frame, C-like calls |
| `src/hunk.c` | Reads the runtime's Hunk object, joins the hunks and writes the executable |
| `runtime/rt.c`, `runtime/rt_math.s` | Startup, `Print`, 32-bit multiply and divide on a 68000 |

## What was checked

- The four tests give the same output as the Python Dash on A1200 and A500 with the 3.1 ROM.
- `build/dashc.amiga` compiles the four inside an emulated A500; the executables are byte-identical
  to the PC ones and run.
- The executables take 1 to 2 KB (6 to 7.5 KB with gcc).

Not measured: the speed of the code compared with gcc `-O2`.
