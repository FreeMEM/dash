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

## Debugging

`dashc --debug prog.dash -o prog` (or `./dash --debug`) puts a `NOP` at the start of every line and adds a
`HUNK_DEBUG` to the executable with the files, lines, functions, variables, globals and struct fields
(`dashc --debug-info prog` prints it). No function is copied inline and every variable stays in the frame, where the
debugger finds it; the program does the same as without `--debug`.

The `dbg_*` builtins debug such a program from another one (Forja, the IDE), built with either Dash (`./dash` or
`./dash --c`):

```ruby
dbg_start("Work:prog", "")              # loaded and paused before its first line
dbg_break("prog.dash", 12)              # a breakpoint (by the end of the file name)
dbg_continue()
if dbg_wait(0) == 3                     # 3: stopped at a line; 4: ended
    Print "#{dbg_function()} #{dbg_line()}: p = " + dbg_value(0, "p")
end
dbg_next()                              # dbg_step goes into functions; dbg_out leaves this one
dbg_end(5000)                           # ends it (its usual cleanup); dbg_rc() gives its code
```

| Builtin | What it does |
|---------|--------------|
| `dbg_start(prog, args)`, `dbg_error()` | Load paused; why it failed |
| `dbg_state()`, `dbg_wait(ms)`, `dbg_signal()` | State (0 none, 1 paused at the start, 2 running, 3 stopped, 4 ended); wait; the signal that comes when it stops or ends (for `mui_wait_event_signals`) |
| `dbg_break(file, line)`, `dbg_unbreak(...)` | Breakpoints |
| `dbg_continue()`, `dbg_step()`, `dbg_next()`, `dbg_out()`, `dbg_pause()` | Go on, step in, step over, step out, stop at the next line |
| `dbg_end(ms)`, `dbg_rc()`, `dbg_output()` | End it, its code, what it wrote |
| `dbg_file()`, `dbg_line()`, `dbg_function()` | Where it stopped |
| `dbg_frames()`, `dbg_frame_function/line/file(i)` | The call stack (0, where it is) |
| `dbg_vars(i)`, `dbg_var_name/type(i, k)`, `dbg_globals()`, `dbg_global_name(g)` | The variables of each call and the globals |
| `dbg_value(i, expr)`, `dbg_value_type(i, expr)` | The value as text (`"p.hijos[0].x"`) and its type |
| `dbg_reg(n)`, `dbg_peek(addr, size)` | Registers (0-7 d0-d7, 8-15 a0-a7, 16 the PC) and memory |

How it works (`DEBUGGER_RUNTIME` in `compiler/codegen.py`, plan in `docs/DEPURADOR_LOOP.md`): the program runs in a child process with its
own exception handler; a breakpoint turns the line's `NOP` into `TRAP #15`, and going on needs nothing put back.
Stepping makes every line stop and looks at the frame (`a5`). It does not use the CPU's trace bit, so it works the
same on a 68000, in FS-UAE and in Emu68.

Limits: a `task_start` task that runs a line with a `TRAP` crashes (it has no handler); a program waiting without
running any line (in `mui_wait_event`) does not end with `dbg_end` until it is back in its code; read the output
before `dbg_end`. Tests: `python3 tests/depurar.py [--a500] [--c]`.

`tools/amiga/dbgserver.dash` puts these builtins on the network: it debugs a program and serves one-line orders
over TCP (its protocol is at the top of the file). It is the debugger of the VS Code extension
(`editor/vscode/dashDebug.js`); `tools/emu_run.py --dbgserver PORT prog` starts it in the emulator. Tests:
`python3 tests/depurar_vscode.py [--a500]` (the server and, with node, the VS Code adapter).

## How it is built

| File | What it does |
|------|--------------|
| `src/lexer.c`, `src/parser.c` | Text to tree, with the grammar of `compiler/grammar.py` |
| `src/gen68k.c` | 68000 code: the value in d0, C-like calls; each function is generated twice to keep the most used variables in d2-d7 |
| `src/hunk.c` | Reads the runtime's Hunk object, joins the hunks that are reached and writes the executable (with `DASHC_MAPA=1`, it lists what goes in from the runtime, its size and what brought it) |
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
