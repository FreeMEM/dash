# Dash versions

*English | [Castellano](VERSIONES.md)*

What carries a number is the compiler: the language, its builtins, the runtime that goes inside every program and
the tools (`tools/`). A program already compiled does not depend on the version: it is an Amiga executable and
keeps working the same. The version tells which Dash a program needs to compile and what has changed.

`./dash --version` says which one you have. Each version is a `vX.Y.Z` tag of the repository with its page in
[Releases](https://github.com/FreeMEM/dash/releases) (the `vscode-X.Y.Z` tags belong to the VS Code extension,
which goes apart).

## What each number means

`X.Y.Z`, as in [Semantic Versioning](https://semver.org/):

- **Z (fixes):** bugs fixed, faster or smaller programs, documentation. Nothing to change in a program.
- **Y (new things):** new builtins, syntax or options. Every program that compiled still compiles and does the
  same; one that uses the new things needs this version or a later one.
- **X (breaking changes):** something no longer compiles or does something else (a builtin that changes its name or
  its arguments, a new reserved word). The release notes say what to change in each case.

Not counted as breaking: fixing a bug even if some program relied on it, different error messages, the generated
C (it may change in any version), whatever the documentation marks as experimental, and `@native` code that uses
internal functions of the runtime (`_dash_*`).

## How to update

With the repository cloned: `git pull` (or `git checkout v1.2.0` for a given version). Otherwise, the zip of the
version in Releases. The VS Code extension tells you once a day if there is a version newer than the one of the
compiler it uses (setting `dash.updates.check`; the request goes to `api.github.com`).

## Notes of each version

### 2.0.1 (2026-11-02)

2.0 goes into `main`. One command, `./dash`, with two paths: straight to hunk (the default) and through C with
gcc (`--gcc`). How to install each one and when to use it: [README, Installation](../README.md#installation).

- **One `dash`:** what was the `./dash1` command in 2.0.0 is now `./dash --gcc`. A program with C inside
  (`@native`, `@c`, `@header`) or a gcc option (`-O`, `-O0`, `--small`, `--multifile`, `--no-hunk`) no longer
  gives an error: `./dash` takes it through C by itself and says so in a line. `./dash --version` says
  "Dash 2.0.1". On the Amiga the command is also called `dash` (it was `dashc`), and its runtimes `dash_*.drt`.
- **Amiberry with JIT no longer closes:** on Amiberry 8.2.2 with JIT, on a PC, the whole emulator closed with
  some programs (Tachyon hit it, inflating with zlib). It is an Amiberry bug
  ([report](https://github.com/BlitterStudio/amiberry/issues/2591)); gcc no longer generates the instructions
  that trigger it (`-fno-branch-count-reg`), also in the straight compiler's runtime. On an A500, some very tight
  loops compiled through C run up to 10 % slower; on an A1200, no clear change.
- **`cpu_start` and `cpu_sample` with several programs at once:** before, two programs measuring the CPU
  (Trasfondo's bar and panel) shared out the tasks and each saw only its own. Now the first one publishes its table
  and the others read it: all of them see every task.
- **VS Code extension:** its tasks, the preview and the debugger use `./dash` and `./dash --gcc`; with a 2.0.0
  they work as before.

### 2.0.0 (2026-10-31, pre-release)

A new compiler. `./dash` is now **dashc**: written in C, it generates the 68000 code itself and links the
executable with its runtime, without gcc or the Python with Lark of before. The 1.x compiler stays, unchanged, as
`./dash1`. The major version goes up because `./dash` no longer compiles programs with C inside them and some options;
`./dash1` compiles them as always. Details in the [manual, section 24](MANUAL_REFERENCIA.en.md#24-dash-20-the-straight-compiler).

- **dashc:** the same language, the same builtins and the same runtime as 1.x, so programs do the same. In Dash's
  test suite every program without C compiles, and those checked in the emulator give the same output as with
  1.x (all but one, because of the emulator's FPU). Building it needs only a C compiler for the PC and Python 3
  (`make -C dashc`). `./dash --version` says "Dash 2.0.0 (dashc)".
- **On the Amiga:** dashc is also compiled for the Amiga (`make -C dashc amiga`, it runs on a 68000) and, from the
  same input file, writes the same executable byte for byte as the PC one. To install it there,
  `dash-2.0.0-amiga.lha` (from `tools/paquete_amiga.py`), with its installer: the Dash drawer and the `DASH:` assign.
- **What to change:** a program with `@native`, `@c` or `@header`, to `./dash1`, or its C into an object with
  `@link` and `@extern`. The options `-O`, `-O0`, `--small`, `--multifile` and `--no-hunk`, to `./dash1`. In both
  cases `./dash` gives an error with the `./dash1` command that does it. `--stack 0` no longer keeps the shell's
  stack.
- **Already compiled C:** `@link "x.o"` or `"libx.a"` links an object or library from the Amiga gcc; `@extern`
  declares its functions (with `Int`, `Bool`, `String`, structs and `Func`); `@export` (new, also in 1.x) lets that
  C call a Dash function by its name. The runtime provides the libc and libm parts that C needs, and
  `dashc --cabecera` writes the program's structs as a C header.
- **dashc options:** `--fpu`, `--cpu`, `--memcheck` (also together with `--fpu`), `--stack`, `--profile` and
  `--debug`, which prepares the program for the new debugger.
- **New debugger:** the `dbg_*` builtins debug, from another program, one compiled with `./dash --debug`
  (breakpoints, stepping, stack, variables, registers and memory). It does not use the CPU's trace mode, which
  Emu68 does not have.
- **`task_start`** accepts a Dash function; dashc checks at compile time that it does not create strings, lists
  or structs (it runs at the same time as the program).
- **New builtins (also in 1.x), 836 in all:** PNG, JPEG, GIF, BMP, WebP and SVG images decoded by the program,
  without datatypes (`image_decode`); TrueType, WOFF and WOFF2 fonts (`font_from_ttf`); network in a separate
  task (`net_bg_*`); gzip and zlib (`inflate_auto`); system and program (`time_unix`, `run_command`,
  `program_path`, `cpu_model`...); the system's tasks, ports and assigns (`tasks_read`, `ports_read`,
  `assigns_read`); ARexx (`rexx_send`); environment variables (`env_get`, `env_set`); memory (`mem_puddle`,
  `mem_trim`); other programs' windows, for tests (`window_find`, `input_menu`...); a window manager (`wm_*`);
  the debugger (`dbg_*`) and more MUI.
- **Windows (also in 1.x):** `On RightClick` (with `rmbtrap`), `On Inactive` and windows without a title bar
  (`title ""`).
- **Memory of linked C:** dashc's `malloc` for that C uses an exec pool, and the `FreePooled` of exec 40
  (Kickstart 3.1) could give back to the system a piece of the pool with blocks still in use, depending on what
  was in that memory before. dashc prevents it.
- **VS Code:** the tasks (compile, run in the emulator, with memory checking or with profiling) and the MUI preview
  ("Ver en Amiga") compile with `./dash`, and with `./dash1` if the program has C (`DASH_FALLBACK_DASH1=1` in
  `./dash`). So does the debugger (F5): it compiles with `./dash --debug` and debugs on the emulated Amiga with the
  new debugger, through `tools/amiga/dbgserver.dash`, which drives it with the `dbg_*` and talks to VS Code over
  the network. A program with C stays with `./dash1 --debug` and gdb, as before.
- **Measurements:** the executables of the test programs usually come out somewhat smaller than with gcc, though
  some are larger. In Tachyon, for now, slower than 1.x in almost every phase (up to 18 %, on an emulated A1200).
- Tested on emulated A1200 and A500 (FS-UAE).

### 1.0.1 (2026-10-28)

Faster programs that use less memory. Nothing in the language changes: what compiled with 1.0.0 compiles the same.
Details and measurements in [RECURSOS_LOOP.md](RECURSOS_LOOP.md) ("Tercera ronda", in Spanish).

- **Strings:** each string keeps its length and `s = a + b` is written in place in `s` when it fits. Joining a
  string and a number is 17 % faster; interpolation, 8 %.
- **Dictionaries:** literal keys carry their hash computed at compile time. Looking up with a literal key is
  34-41 % faster.
- **Comparing with a literal:** `s == "hello"` checks the first character before calling `strcmp`. A chain of
  comparisons is 54 % faster.
- **Float:** on a 68020, 030 or 040, multiplication uses the processor's 32-bit instruction: 20 % faster. On the
  68000, 2 % slower (the cost of checking the processor).
- **Memory:** each program uses 8 KB less (the stack for processor exceptions is no longer separate).
- **RTG:** the desktop canvas without a backdrop no longer reads from the graphics card when it updates.
- **Cost:** executables are 1.8 % larger; returning a string and creating a struct with a string, 2-3 % slower.
- Not tested on a 68060 or on real hardware.

### 1.0.0 (2026-10-27)

The first version with a number. It gathers everything done so far (full log in [ROADMAP.md](ROADMAP.md)):

- **Language:** inferred types, `Int`, `Float` (in software) and `Fixed` (16.16), strings with interpolation,
  typed lists and dictionaries, structs with methods and interfaces, functions as values and lambdas, modules with
  a private part, automatic memory without a garbage collector (per-iteration temporaries and reference counts).
- **No Gurus from a slip:** a field of `nil` or a processor exception ends the program with a message and the
  normal clean-up; `--memcheck` checks memory and `--debug` stops in the debugger.
- **686 builtins** (94 of them MUI): Intuition, GadTools, ReAction, MUI 3.8 and 5, graphics (also RTG), sprites,
  Copper, Blitter, audio and ProTracker modules, IFF and datatypes, network (TCP, UDP and TLS with AmiSSL),
  processes, commodities, language catalogs, the clipboard, the Workbench backdrop and system monitors. List in
  [BUILTINS.en.md](BUILTINS.en.md).
- **Tools:** catalogs without FlexCat (`tools/catalogo.py`), the emulator without a window (`tools/emu_run.py`),
  benchmarks and the visual editor of MUI windows (`.dashui`).
- **VS Code:** colours, errors as you type, completion, compiling and running on the emulated Amiga, debugging
  (also on a real Amiga over the network) and the MUI visual editor. From this version it tells you about new
  versions of Dash.
- **What programs need:** Kickstart 3.0 and a 68000; MUI and TLS need a 68020. `--cpu 68020` to `68060` tunes
  the code for each processor.
- **To compile:** Python 3 with Lark and bebbo's Amiga gcc (6.5); see [INSTALACION.en.md](INSTALACION.en.md).
