# dashc: a self-sufficient Dash proof of concept

[Español](README.md)

`dashc` compiles a `.dash` file into an Amiga executable without a C compiler: it generates 68000 code,
links it with the runtime (precompiled and embedded in `dashc`) and writes the Hunk file. It is written
in C and the same code builds for the PC and for the Amiga. The runtime is `./dash`'s (memory, strings,
lists, reference-counted objects, errors): it is taken from `compiler/codegen.py`, so programs behave
the same, memory included.

```bash
make                     # dashc for this computer
./dashc prog.dash -o prog
make amiga               # build/dashc.amiga: dashc running on the Amiga (68000, OS 2.0+)
make test                # tests/*.dash with dashc and with ./dash: same output on A1200 and A500 (FS-UAE)
python3 bench/bench_run.py   # speed against ./dash (gcc -O2) on A500 and A1200 at real speed
make runtime             # rebuilds runtime/dashrt.o with bebbo's gcc and ./dash (it is in git: not needed otherwise)
```

## What it understands

Integers (decimal, `0x`, `$`, `0b`), `Bool`, `const`, globals with `var`, local variables, functions
with parameters and `return`, `if`/`elif`/`else`, `while`, `for` over a range (`step`, backwards),
`break`, `continue`, short-circuit `and`/`or`/`not`, every integer operator and `Print`.

- Strings (Latin-1): variables, `+` (also with numbers), `#{...}` interpolation, `s[i]`, `s[a:b]`,
  `.length`, comparisons, parameters and return values.
- Lists `[...]` and `[T]` types: `a[i]`, `a[i] = v`, `push`, `pop`, `insert`, `remove`, `clear`,
  `.length`, slices, `for x in list`; of numbers, strings, structs or lists.
- Structs with default values, fields, methods with `self`, `nil` (a field of nil stops the program with
  the same error as `./dash`), recursive structs and structs in lists.

Missing: dictionaries, string methods (`find`, `upper`...), `sort`, lambdas, enums, Float and Fixed,
builtins, windows, `@native`, `import`.

## How it is built

| File | What it does |
|------|--------------|
| `src/lexer.c`, `src/parser.c` | Text to tree, with the grammar of `compiler/grammar.py` |
| `src/gen68k.c` | 68000 code: the value in d0, C-like calls; each function is generated twice to keep the most used variables in d2-d7 |
| `src/hunk.c` | Reads the runtime's Hunk object, joins the hunks and writes the executable |
| `runtime/gen_lib.py` | Takes `./dash`'s runtime from the C it generates for `runtime/cocina.dash`, without libnix |
| `runtime/api.c` | Startup and exit, `Print`, and named `dl_*` what dashc's code calls |
| `runtime/rt_math.s`, `runtime/rt_libc.c` | `_dash_start`, 32-bit multiply and divide, the little libc needed |

## What was checked

- The twelve tests give the same output and exit code as the Python Dash on A1200 and A500 with the
  3.1 ROM, including those that make tens of thousands of strings, lists and structs on an A500.
- `build/dashc.amiga` compiles the twelve inside an emulated A500; the executables are byte-identical to
  the PC ones (with the same source name, which goes inside for errors) and run.
- The executables take 12 to 16 KB, because they carry the whole runtime (6 to 17 KB with gcc): linking
  only what is used is still to do.
- Speed (`bench/bench_enteros.dash`, times the time of gcc `-O2`; below 1 is faster): on average
  0.92 on A500 and 0.97 on A1200 (the emulator varies 3 % between runs). The slowest, 1.05
  (nested loops: gcc deduces that if i < j, i == j is false); the fastest, recursion (fib, 0.55
  and 0.70).
- Optimizations, like gcc's: variables in d2-d7; a small function or one called from a single place
  is copied where it is called (not if it is recursive), and a one-line one as an expression; a `for`
  or a `while` that only adds 1 counts with `dbra`; `i * k` in a loop is kept as a running sum; a
  variable assigned once with a fixed value is a constant; a `for` index has a known range, and with
  it 16-bit division and product need no checks; multiply and divide try the 16-bit case inline; on
  a 68020 or better the runtime uses `divs.l` and `muls.l`; branches that reach with 8 bits use
  their short form.
