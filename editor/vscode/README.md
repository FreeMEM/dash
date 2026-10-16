# Dash for VS Code

Support for [Dash](https://github.com/FreeMEM/dash), a language that compiles to C for the Amiga:

- Syntax highlighting of `.dash` files (with the C of `@native` blocks).
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
DASH_PREVIEW_EMU=1 npm test   # also "Ver en Amiga" in FS-UAE (DASH_KICKSTART, DASH_EMU_SYS_MUI)
npm run package    # dash-mui-editor-<version>.vsix
```
