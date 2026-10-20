# Changelog

## Unreleased (found making the video tutorial, docs/IDE_VIDEO_LOOP.md)

- Debugger: step into (F11) goes only into the program's functions, not into the runtime's C; a session without
  the emulator's window is no longer cut after 60 s; the stop on attaching is not shown (it said "Paused on attach"
  at the first breakpoint); no Ada/C++ exception filters, gdb start-up messages or registers.
- Tasks: `./dash -q` and no echo of the command; no duplicate errors in Problems with the language server on.
- The visual editor in the colours of VS Code's theme; a quote typed over a selection no longer surrounds it.
- New project: a name with accents keeps its letters without them ("Mi Juego Ñandú": `Mi_Juego_Nandu`).
- `./dash`: `-o` into a folder that is not there makes it.
- Odd text: `.dash` files with a BOM or in Latin-1 (written on the Amiga) compile, and VS Code guesses their
  encoding; formatting keeps Windows line ends; a module without `Main` is not a problem; a line that ends in an
  operator says so in the syntax error.
- A `.dash` opened without a folder compiles and runs (in a terminal of its own, which keeps the output); an
  untitled one asks for its name first; its errors are underlined. Needs VS Code 1.86.
- Something missing (the Amiga compiler, the emulator, bgdbserver, gdb, the MUI SDK, a system with MUI, a ROM) is
  said in words, with how to get it; a wrong `dash.path` says so (and `~/` works in it).
- `./dash`: two programs of the same name compiled at once take turns (they shared `build/<name>.c`).
- Visual editor: a `.dashui` given to VS Code when it starts opens in it (it opened as JSON text); names that are
  words of the language and event numbers that are not are refused, as the compiler does; at half the screen
  the properties go under the rest.
- Debugger: big values are fast (texts and lists read in blocks, children counted without reading them, a
  dictionary's first 100 entries, `d["k"]` straight to its slot); breakpoints and steps in an `@native`'s lines;
  what the program writes just before it ends reaches the debug console.

## 0.2.0 (2026-10-20)

An IDE for Dash (docs/IDE_LOOP.md of the Dash repository).

- **Editing**: highlighting generated from the compiler; the `end` of a block added on Enter and `else`/`end` put back at
  their level; snippets.
- **Language server** (`compiler/lsp.py`): errors while typing, completion with the parameters of every builtin,
  signature help, hover, go to definition, references, outline, symbols of the workspace, rename, formatting and
  quick fixes.
- **Compile and run**: tasks with problem matchers (the errors at their line, also those of `--memcheck`), the profile
  of `--profile` in a table, CodeLens over `Main` and functions, a status bar with the emulator's machine (A1200 3.1, A500,
  A1200 3.2, 68040 with a graphics card) and Amiberry as the other emulator.
- **Debugger** (F5): breakpoints, steps, the stack and the variables in Dash lines and values, on the emulated Amiga
  (`m68k-amigaos-gdb` and `bgdbserver`) or a real one; Dash expressions in the console, watch, hover, conditions and
  logpoints; the program's output in the debug console; its errors stop it like exceptions; global variables read right.
- **Visual editor of MUI windows** (`.dashui`): keyboard in the tree, copy and paste, drag before, after or into a group,
  undo and redo, accessibility; its problems in the Problems panel; from an event to its code in the `.dash` (or that
  code created); **Ver en Amiga** with an emulated Amiga that stays on (about 2 s a preview).
- **Getting started**: **Dash: Nuevo proyecto**, **Dash: Elegir la carpeta del compilador** and the walkthrough
  "Primeros pasos con Dash".
- Restricted Mode: highlighting and the visual editor work; compiling and the emulator need a trusted folder.

## 0.1.0 (2026-10-16)

- Highlighting of `.dash`, compile and run in FS-UAE, and the visual editor of MUI windows (`.dashui`) with
  **Ver en Amiga**.
