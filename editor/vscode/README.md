# Dash for VS Code

Support for [Dash](https://github.com/FreeMEM/dash), a language that compiles to C for the Amiga:

- Syntax highlighting of `.dash` files (with the C of `@native` blocks): every keyword, directive and builtin,
  `Window` blocks, `#{...}` with expressions. Generated from the compiler (`tools/gen_tmgrammar.py` in the Dash
  repository; do not edit `syntaxes/dash.tmLanguage.json` by hand).
- **Errors while typing**: Dash's language server (`python3 -m compiler.lsp` in the compiler's folder, the
  same parser and analyzer as `./dash`) marks errors and warnings a moment after you stop typing, also those of
  imported modules in their files. Only in a trusted folder; `dash.languageServer.enabled`, `dash.python`, and
  **Dash: Reiniciar el servidor de lenguaje** (after changing `dash.path`).
- **Completion** (same server): every builtin with its parameters to fill in, keywords, the program's
  functions, structs, enums, constants and the variables seen at the cursor; after `x.` the fields and
  methods of its struct (or the values of an enum, the methods of a list...); types after `:` and `->`;
  files after `import "`. **Signature help** while writing the arguments of a call.
- **Navigation** (same server): hover (signature, type, description), go to definition (also into imported
  modules, into the window of a `.dashui`, and from an `import "..."` to its file), find references and the
  highlight of a name's uses (a local only inside its function).
- **Outline and symbols**: the outline and breadcrumbs of a file (structs with their fields and methods,
  enums with their values, functions, Main, windows, constants), symbols of the whole workspace (Ctrl+T), and
  **rename** (F2) of functions, structs, variables, fields... in every file of the program (not builtins, nor
  names that come from a `.dashui`: those are renamed in the visual editor; C inside `@native` is not changed).
- **Format document** (Shift+Alt+F): the indentation of every line by its blocks (also the trees of
  `mui_*_begin` ... `_end()` when they were indented), no spaces at the end; the C of `@native` untouched.
  **Quick fixes** (Ctrl+.) on "not defined": create the function (with as many parameters as the call),
  import it from the file of the workspace that has it, or "Cambiar a ..." a name that looks like it.
- Editing: snippets (`Main`, `func`, `struct`, `if`, `for`, `Window`, `mui`, `muiui`...), the `end` of a block
  added by itself when Enter opens one (setting `dash.editor.autoEnd`), `else`/`elif`/`end` back to their level,
  indentation, folding (also `# region` / `# endregion`), `#` comments, and an icon for `.dash` files.
- In a folder not trusted (Restricted Mode) only colours and the visual editor work; compiling, the emulator
  and the language server need a trusted folder.
- **Debugging (F5)**: breakpoints in the `.dash`, continue, step over/into/out, pause, the call stack and the
  variables, in Dash lines, on the emulated Amiga. F5 (or **Dash: Depurar en el Amiga**, or "Depurar" over
  `Main`) builds the program with `./dash --debug`, starts the emulator with it under `bgdbserver`
  (`tools/get_bgdbserver.sh` of the Dash repository, once) and attaches `m68k-amigaos-gdb -i=dap` to it (gdb is the
  debug adapter; `dash.debug.gdb`). The emulator stops with the session. `launch.json`: `program`, `stopOnEntry`,
  `machine`, `emulator`, `window`; `attach` with `target` (host:port of a bgdbserver) for a real Amiga.
- **Memory and profile**: a `--memcheck` run puts each memory error on the line where it happened (problem
  matcher `$dash-memcheck`); a `--profile` run opens its table (own and total time, calls) in a panel, each
  function a link to its code.
- **Emulator machine**: `dash.emulator.machine` (A1200 3.1, A500, A1200 3.2, 68040 with RTG) and
  `dash.emulator.program` (FS-UAE or Amiberry), also from the status bar (**Dash: Elegir la máquina del
  emulador**); per project in `.vscode/settings.json`. The program runs in the emulator's window
  (`dash.emulator.window`) and its output shows in the task's panel while it runs; stopping the task stops the
  emulator. MUI programs on the A1200 3.1 get `dash.emulator.muiSystem`.
- **Build and run** as VS Code tasks (type `dash`: `compile`, `run`, `memcheck`, `profile`; Terminal > Run Task,
  Ctrl+Shift+B, or in `tasks.json` with `"file": "${file}"`): **Dash: Compilar** (to `bin/` next to the file),
  **Dash: Ejecutar en emulador** (FS-UAE, `tools/emu_run.py`), **con comprobación de memoria** (`--memcheck`) and
  **con perfil** (`--profile`). Errors go through the `$dash` problem matcher (`file:line:column: Error: ...`) and
  `$gcc`, to Problems and onto the code. A CodeLens over `Main` (▶ Ejecutar · Compilar · Memoria · Perfil) and a
  ▶ Dash button in the status bar.

- **Visual editor for MUI windows** (`.dashui` files, format in `docs/MUI_EDITOR.md` of the Dash repository):
  palette, tree (drag to add and move, Delete to remove), properties, menus and an approximate preview.
  **Ver en Amiga** compiles a tiny program with the window, runs it in FS-UAE with MUI and shows a picture of
  the real thing (about 30 s). A Dash program uses the file with `import "ventana.dashui"`.
- **Dash: Nuevo fichero de ventanas MUI**: a new `.dashui` with one empty window.

## Settings

- `dash.path`: folder of the Dash compiler (the one with `./dash`). Empty: looked for up from the file.
- `dash.emulator.kickstart`, `dash.emulator.system`: Kickstart ROM and Workbench files for FS-UAE
  (the same as `DASH_KICKSTART` and `DASH_EMU_SYS`); `kickstartA500`, `kickstart32`, `system32`, `systemRtg`
  for the other machines (`DASH_KICKSTART_A500`, `DASH_KICKSTART_32`, `DASH_EMU_SYS_32`, `DASH_EMU_SYS_32_RTG`).
- `dash.emulator.autoclose`: seconds after which a windowed program closes itself in the emulator.
- `dash.emulator.muiSystem`: Workbench files with MUI for "Ver en Amiga" (`DASH_EMU_SYS_MUI`, made with
  `tools/emu_sys_mui.sh`).

## Development

```
npm install        # only dev tools, in node_modules/
npm test           # grammar, model, preview and commands, without VS Code
python3 ../../tools/gen_tmgrammar.py   # after a change to the language or its builtins
DASH_PREVIEW_EMU=1 npm test   # also "Ver en Amiga" in FS-UAE (DASH_KICKSTART, DASH_EMU_SYS_MUI)
npm run build      # dist/extension.js (esbuild: the extension and vscode-languageclient in one file)
npm run test:vscode   # tests inside the installed VS Code (a window opens a few seconds; own profile and folder;
                      # the tests that type are skipped if that window does not get the desktop's focus)
npm run package    # dash-mui-editor-<version>.vsix
```
