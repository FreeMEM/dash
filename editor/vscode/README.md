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
- Editing: snippets (`Main`, `func`, `struct`, `if`, `for`, `Window`, `mui`, `muiui`...), the `end` of a block
  added by itself when Enter opens one (setting `dash.editor.autoEnd`), `else`/`elif`/`end` back to their level,
  indentation, folding (also `# region` / `# endregion`), `#` comments, and an icon for `.dash` files.
- In a folder not trusted (Restricted Mode) only colours and the visual editor work; compiling, the emulator
  and the language server need a trusted folder.
- **Dash: Compilar**: compiles the open program with `./dash` (to `bin/` next to it).
- **Dash: Ejecutar en emulador**: runs it in FS-UAE with `tools/emu_run.py` (output in the terminal).

- **Visual editor for MUI windows** (`.dashui` files, format in `docs/MUI_EDITOR.md` of the Dash repository):
  palette, tree (drag to add and move, Delete to remove), properties, menus and an approximate preview.
  **Ver en Amiga** compiles a tiny program with the window, runs it in FS-UAE with MUI and shows a picture of
  the real thing (about 30 s). A Dash program uses the file with `import "ventana.dashui"`.
- **Dash: Nuevo fichero de ventanas MUI**: a new `.dashui` with one empty window.

## Settings

- `dash.path`: folder of the Dash compiler (the one with `./dash`). Empty: looked for up from the file.
- `dash.emulator.kickstart`, `dash.emulator.system`: Kickstart ROM and Workbench files for FS-UAE
  (the same as `DASH_KICKSTART` and `DASH_EMU_SYS`).
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
npm run test:vscode   # tests inside the installed VS Code (a window opens a few seconds; own profile)
npm run package    # dash-mui-editor-<version>.vsix
```
