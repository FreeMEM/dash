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

### 2.6.1 (2026-11-07)

Two fixes. What compiled before still does the same.

- **Fix (`desktop_canvas`):** two programs with a desktop canvas at once (Trasfondo and another) hung the display.
  Now both can run, and each one leaves the backdrop as it was when it ends. Both programs must be built with this
  version or a later one.
- **Fix (sprites):** on a plain PAL or NTSC screen, `sprite_load` warned that it was a graphics card (RTG) screen.
  Found with the example game of the VS Code extension.
- Tested on emulated A1200 (3.1 and 3.2), A500 and CoffinOS.

### 2.6.0 (2026-11-07)

Dropping icons on MUI windows and DashOS's own builtins. What compiled before still does the same.

- **Icons dropped on a MUI window:** `mui_on_drop(object, id)` makes `mui_wait_event()` return `id` when a
  Workbench icon is dropped on that object (on a window, anywhere on it). The paths, with `app_drop()`. Every MUI
  window now takes icons. Tachyon uses it to open a saved page (idea by Ferrán García). Tested with MUI 3.8 and
  MUI 5.
- **DashOS:** 32 builtins of its own (channels, keys, timers, shared memory, processes and groups). They only
  compile for DashOS; on the Amiga they give an error that says so.
- **`return` in `Main`:** without a value it ends the program, now also with `./dash --gcc` (before, only with
  `./dash`).
- Tested on emulated A1200 (3.1 and 3.2) and A500, both ways.

### 2.5.0 (2026-11-07)

Compiler fixes found by Forja, Trasfondo's memory leak and a builtin for the pictures of its dock. What compiled
before still does the same.

- **Pictures at another size:** `image_from_decoded_size(d, width, height)` makes an image from a decoded picture
  (a PNG with transparency, say) at another size, with smooth edges.
- **Fix (memory leak):** builtins that only read their strings got a copy that was never freed when the string was
  computed. Now they get the string as it is: `tooltype`, `date_text`, `file_copy`, `notify`,
  `screen_font_text_width`, `wifi_read`, `net_driver_read`, `rexx_reply`, `dir_change`, `input_text` and the ones
  that load or save files. It was the memory Trasfondo's backdrop lost over the hours (reported by Oskisrp).
- **Fix (`./dash`):** in a very long program, a branch that had to grow could overwrite the next instruction.
- **Fix (`./dash --debug`):** a function nobody calls no longer leaves debug data pointing at another function.
  Forja's debugger could break the program when stepping.
- Tested on emulated A1200 (3.1 and 3.2) and A500, both ways.

### 2.4.0 (2026-11-06)

What Trasfondo 2.2's dock and notifications need. All new features; what already compiled stays the same.

- **Icons at another size:** `icon_draw_size(icon, x, y, width, height)` draws an `icon_load` icon smaller or
  bigger, with soft edges (on true colour screens; on palette ones, at its size and centred).
- **An ARexx port of its own:** `rexx_port(name)` opens it; commands arrive with `rexx_get()` and are answered with
  `rexx_reply(rc, result)`. Before, Dash could only send commands (`rexx_send`). Manual, section 18.
- **Notifications:** `notify(title, text)` leaves a notification on the desktop, with the program's name: to
  Trasfondo's bar by ARexx (port `TRASFONDO`) or, if it isn't running, in its list, which it shows when it starts.
- **Fix:** `run_program` and `run_command` in a program started from the Workbench gave the command only `C:` in
  its path, and so did a Shell opened through `C:WBRun` (Trasfondo's dock). Now they give it a copy of the
  Workbench's path, the same one a double click gives.
- **`wm_bar_gadgets()`:** how far from the right edge the gadgets of the Workbench screen's title bar start (the
  depth gadget), asked to the screen.
- **Pasting in text fields:** in GadTools and ReAction ones (`gt_string`, `gt_integer`, `textfield_create`,
  `integer_create`, `ra_add_string`), right Amiga, left Amiga or Ctrl with V paste the clipboard at the cursor
  (its first line; in a number field, only the digits), with C copy the whole text and with X cut it. Before,
  Amiga + V typed a "v". MUI's already paste by themselves, with right Amiga or Ctrl + V.
- **Fix:** `window_move` just after `window_resize` (or the other way round) gave the window back its old size
  (or place), because the system changes the window later. Now the second one starts from what the first asked
  for. It showed in Trasfondo's bar in the title bar: when it got narrower it left a gap.
- Tested on emulated A1200 (3.1 and 3.2) and A500, through both paths.
- **Fix:** in MUI, a text's colour (`mui_set_text_pen`, a `.dashui`'s `"color"`) uses a pen of the screen on every
  screen. On a 32-bit one with MUI 5 the text stayed dark (Forja).

### 2.3.1 (2026-11-04)

Fixes and the Amiga package with dashgit. Nothing to change in programs.

- **Network with `./dash`:** the direct compiler did not close `bsdsocket.library` at exit. Every program with
  network left it open, and in one Shell FS-UAE refused it from the ninth on.
- **Amiga package:** it brings dashgit, a git written in Dash (`DASH:dashgit`, GPLv2 like git, with
  `DASH:dashgit.LICENSE`; sources at https://github.com/FreeMEM/dashgit). **It is in alpha:** much is still to be
  tested. It brings Forja 0.3, with its Git menu, and the examples' `.dashui` files (without
  `mui_navegador.dashui`, `mui_navegador_editor.dash` did not compile on the Amiga).

### 2.3.0 (2026-11-04)

Dash for DashOS (AArch64), what Trasfondo 2.0's dock and colours ask for and what dashgit, a git written in Dash,
needs. All of it is new; what compiled before stays the same.

- **DashOS:** `./dash --dashos` compiles for DashOS, an AArch64 ELF (little-endian; `--be` big-endian, `--pie` at
  any address), by both paths (`--dashos --gcc`, with clang). Float and Double on the FPU, texts in UTF-8.
  `@amiga struct` and `Ptr X`: views on memory with the 68000's layout, for AmigaOS's structures, with
  `amiga_alloc` and `amiga_free`. On 68k, executables come out as before. Manual, section 25.
- **Windows of other programs and of the Workbench:** `wm_path` (the path of a window's program),
  `file_real_path`, `screen_pixel_rgb` (the screen's colour, whoever drew it), `screen_pen_rgb` (the Workbench's
  colours), `app_window` and `app_drop` (icons dropped on it from the Workbench), `icon_load` and `icon_draw`
  (.info icons as the Workbench draws them, without datatypes) and `window_use` (drawing in the declared window
  again).
- **For git:** `sha1` and `sha1_text`, and bit by bit `sha1_new`, `sha1_add`, `sha1_hex`, `sha1_bytes`...;
  `adler32`, `inflate_used` (where a compressed object ends), `program_exit(rc)` and `locale_gmt_offset`.
- **`./dash --gcc` with C of `@link`:** what is passed to it is no longer kept forever (with `--memcheck`, Tachyon
  left texts and objects alive) and its libraries link in any order and only with what is used.
- **`dash` on the Amiga:** `version dash` gives its version (before, "%s (%d.%d.%d)"), and programs with a catalog
  no longer carry an empty version mark before their own.
- **Installer:** if there is a `DASH:` already, it offers to update that installation where it is; a file in the
  way is moved aside as `.antes`; in `S:User-Startup`, `DASH:` and the Path (also `DASH:Forja` and
  `DASH:Inferencia`: `forja` and `inferencia` from any Shell) only if their drawer is there, so moving the drawer
  no longer stops the boot; Forja's dash path is `DASH:dash`. It brings Forja 0.2 and Inferencia 0.1, with their
  version numbers.
- **MorphOS:** Dash's 68k executables run on MorphOS (Tolkien tried them).
- Tested on emulated A1200 (3.1 and 3.2) and A500, and the installer on Coffin.

### 2.2.0 (2026-11-03)

What Forja's sprite and map editors and Fragua, the games library, need. All of it is new builtins; what compiled
before stays the same, except windows with no screen of their own (below).

- **Tile maps:** `tilemap_create`, `tilemap_load` and `tilemap_save` (IFF `FORM FMAP`, the one of Forja's map
  editor), cells with mirroring (`tilemap_get`, `tilemap_set`), layers (name, type, visible; add, remove, move),
  `tilemap_resize` and objects (`tilemap_object_add`, `_find`, `_x`, `_y`, `_kind`...). `tilemap_draw` and
  `tilemap_draw_masked` draw a piece of the map with a BOB's frames, in one go on the window.
- **Sprites and BOBs:** `sprite_load_attached` (attached 15-colour sprites), `sprite_rgb8`, `sprite_load_colors`,
  `bob_load_colors`, `bob_frame_width` (and `bob_load` reads the frame width Forja saves), `bob_paste` (a frame
  with its mask without saving the background) and `bob_width`, `bob_height`, `bob_frames`.
- **Screens:** `screen_double_buffer` and `screen_flip` (double buffering), `screen_clone_wb` (a public clone of
  the Workbench), `screen_make_default`, `screen_visitors`, `mui_window_screen`, `dialog_screen_mode` and
  `screen_open_mode`. An own screen with no window can now be drawn on (`gfx_rgb8` hung).
- **Windows with no screen of their own:** they open on the default public screen instead of always on the
  Workbench. As long as nobody changes the default public screen, it is the Workbench, as before.
- **Drawing:** `gfx_pens_draw` (a picture of pens in one go, with zoom; on planes, a single blitter copy),
  `color_pen_free`, and `key_down` (whether a key is held down now, for games).
- **For the Amiga:** the package brings Forja with its sprite and map editors.

### 2.1.0 (2026-11-03)

The same `@link` C works on both paths, straight and through C with gcc. It is the step to take programs like
Tachyon to PowerPC.

- **`@link` through C with gcc:** `./dash --gcc` gives the linked C the same runtime functions as the straight
  path (`dl_str_dup`, `dl_arr_get`, `dl_retain`...) and the builtins as `db_name` (`db_time_ms`...). Only the ones
  that C calls go in.
- **`./dash --gcc --cabecera tipos.h programa.dash`:** writes the program's structs as the C path lays them out,
  its constants and the `@export` prototypes, with the same names as the straight path's header. A `Bool` takes
  2 bytes there, so the C is compiled separately for each path, each with its header.
- **`./dash --gcc` from any folder:** before, you had to be in the repository's folder or set `PYTHONPATH`.
- **Constructors:** only the last fields can be left out, and only if they have a default. Before, with a field
  with a default in the middle of the struct, both compilers accepted a call missing a required field after it.
  Now it is an error, as the manual says. A program that compiled like that had its fields shifted.

### 2.0.2 (2026-11-03)

The straight compiler generates faster code. It is now as fast as or faster than the C path (`--gcc`) in almost
everything. Nothing to change in programs.

- **Text:** joining strings (`s = a + b`, `s = "x" + n`, `"...#{x}..."`) takes half the time it did in 2.0.1. It is
  now 9 % faster than through C on an A1200 and 7 % on an A500.
- **Floating point:** half the time of 2.0.1; the same as through C. Calculations that do not change inside a loop
  are done once, before it.
- **Lists:** reading and writing `a[i]` is inline, without calling the runtime: 31 % less time. Still 12-15 %
  slower than through C.
- **Integers:** `r = a + b` is computed in `r`'s register, and division by a constant skips its checks when the
  range is known. Function calls, 8 % faster.

Measured with `tools/comparativa/medir_dash.py` on an emulated A1200 and A500.

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
