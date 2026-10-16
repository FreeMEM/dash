# Dash for VS Code

Support for [Dash](https://github.com/FreeMEM/dash), a language that compiles to C for the Amiga:

- Syntax highlighting of `.dash` files (with the C of `@native` blocks).
- **Dash: Compilar**: compiles the open program with `./dash` (to `bin/` next to it).
- **Dash: Ejecutar en emulador**: runs it in FS-UAE with `tools/emu_run.py` (output in the terminal).

Coming next: a visual editor for MUI windows (`.dashui` files, see `docs/MUI_EDITOR.md` in the Dash repository).

## Settings

- `dash.path`: folder of the Dash compiler (the one with `./dash`). Empty: looked for up from the file.
- `dash.emulator.kickstart`, `dash.emulator.system`: Kickstart ROM and Workbench files for FS-UAE
  (the same as `DASH_KICKSTART` and `DASH_EMU_SYS`).
- `dash.emulator.autoclose`: seconds after which a windowed program closes itself in the emulator.

## Development

```
npm install        # only dev tools, in node_modules/
npm test           # grammar and commands, without VS Code
npm run package    # dash-mui-editor-<version>.vsix
```
