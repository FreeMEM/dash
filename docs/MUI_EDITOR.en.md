# MUI visual editor for VS Code (task 19 of `docs/MUI_LOOP.md`)

*English | [Castellano](MUI_EDITOR.md)*

A "Glade for MUI": you build the window with the mouse (groups, buttons, fields, lists...) inside VS Code and the
Dash program uses it. It fits the AmiCachy development profile (`dev_station`: VS Code + Amiberry, `DEV:`
drawer; see AmiCachy's `ARCHITECTURE.md`, section 5).

## Decisions

1. **Its own format, `.dashui` (JSON), like Glade's `.ui`.** The user does not remember the format that was discussed; this
   one is the simplest to edit with a tool and to read back without losing anything (task 22): the file is the
   single source of truth, there is no generated code that can get out of sync.
2. **The compiler understands it directly:** `import "ventana.dashui"` in a Dash program. When `compiler/main.py`
   resolves an import ending in `.dashui`, it generates the Dash code (`compiler/dashui.py`) and compiles it as just another
   module. That code uses the `mui_` builtins (docs/MUI_DISEÑO.en.md); nothing new in the runtime.
3. **What it generates:** for each window, a `struct` with one field per named object (plus `window`) and a function
   `<Ventana>_create()` that builds it (the bare struct name would be its constructor):

   ```ruby
   # ventana.dashui with a window "Principal" and objects "url", "ir", "pagina"
   import "ventana.dashui"

   Main
       mui_app_begin("Navegador", "NAVEGADOR")
       v = Principal_create()       # creates the window and its objects; v.url, v.ir, v.pagina...
       mui_on_press(v.ir, 1)
       mui_window_open(v.window)
       ...
   end
   ```

   Events can be set in the `.dashui` (an event number per object) or in the program, as today.
4. **Where it lives:** the `editor/vscode/` folder of this repo (extension `dash-mui-editor`). It goes with the language: if
   the `mui_` functions change, the editor changes in the same commit. It is published in this repo, as a release (`vscode-0.2.1`).
5. **Two-level preview:**
   - **Instant**, in the webview: an approximate rendering with HTML/CSS (boxes that share space like MUI groups).
   - **Real**: the editor's "Ver en Amiga" (View on Amiga) button. It compiles a minimal program that imports the `.dashui`, runs it on
     an emulated Amiga that stays powered on (`tools/emu_preview.py`) and shows the screenshot in the webview (about 2 s;
     originally it was `tools/emu_run.py --screenshot`, about 30 s). Details at the end.
     With the "al cambiar" (on change) checkbox (`dash.emulator.previewOnChange`), it requests a new one only 1.2 s after the last
     change (one at a time; any that arrive in the meantime are merged into one); if the emulator fails, it switches itself off.

## The `.dashui` format

```json
{
  "dashui": 1,
  "windows": [
    {
      "name": "Principal",
      "title": "Navegador",
      "id": 1,
      "root": {
        "type": "vgroup",
        "children": [
          { "type": "hgroup", "children": [
              { "type": "button", "name": "atras", "label": "<", "event": 10 },
              { "type": "string", "name": "url", "text": "http://", "max": 1024, "ack": 11 }
          ]},
          { "type": "canvas", "name": "pagina", "min_width": 320, "min_height": 200, "weight": 300 },
          { "type": "text", "name": "estado", "text": "Listo" }
        ]
      },
      "menus": [
        { "title": "Proyecto", "items": [
            { "label": "Salir", "key": "Q", "event": 99 }
        ]}
      ]
    }
  ]
}
```

| `type` | Builtin | Properties |
|---|---|---|
| `vgroup`, `hgroup` | `mui_vgroup_begin`/`mui_hgroup_begin` | `children` |
| `frame` | `mui_frame_begin` | `title`, `horizontal`, `children` |
| `columns` | `mui_columns_begin` | `columns`, `children` |
| `tabs` | `mui_register_begin` | `titles` ("A|B"), `children` (one page each), `change` |
| `scroll` | `mui_scroll_begin` | `children` |
| `text`, `label` | `mui_text`, `mui_label` | `text` |
| `button` | `mui_button` | `label`, `event` |
| `string` | `mui_string` | `text`, `max`, `ack`, `change` |
| `checkbox` | `mui_checkbox` | `checked`, `change` |
| `cycle` | `mui_cycle` | `options` ("A|B"), `change` |
| `slider` | `mui_slider` | `min`, `max`, `value`, `change` |
| `gauge` | `mui_gauge` | `max` |
| `list` | `mui_list` | `change`, `double` |
| `canvas` | `mui_canvas` | `min_width`, `min_height` |
| `scrollbar` | `mui_scrollbar` | `vertical`, `change` |
| `image` | `mui_image` | `file` |
| `image_button` | `mui_image_button` | `file`, `event` |
| `space`, `balance` | `mui_space`, `mui_balance` | — |

Common: `name` (struct field; without a name the object is not stored), `weight` (`mui_weight`), `disabled`
(`mui_set_enabled`), `hidden` (`mui_set_visible`), `help` (`mui_help`: help in a bubble). On the window, `"size": [ancho,
alto]` is its size when opened, as a percentage of the screen (`mui_window_size`). `event`/`change`/`ack`/`double` = event number
(`mui_on_press`, `mui_on_change`, `mui_on_ack`, `mui_on_double`). `"dashui": 1` is the format version.

Rules checked by the compiler (`compiler/dashui.py`; the editor flags the same ones):

- **Names** of windows and objects: unaccented letters, digits and `_`, not starting with a digit. Language keywords
  (`end`, `if`, `func`...) are not allowed, nor is `window` (it is the window's field). No duplicates within the same window. An
  object is only a field of its window's struct (`v.descargas`): it can have the same name as a global variable of the
  program or of a module without affecting it (dashweb D72).
- **Integers**: `event`, `change`, `ack`, `double`, `weight`, the window's `id` and `close`, and a menu's `event`.
  `"event": "uno"` or `true` is an error.
- **Strings**: they cannot contain `#{` (in Dash that would be an interpolation).
- **Events on any object**: `event`, `change`, `ack` and `double` are valid on every type, groups included;
  the compiler does not restrict them by type.
- **Window**: `"close": N` makes the close button return `N` (`mui_on_close`). Without it, closing the first
  window gives -1 (quit).
- **Menus**: each item is `label`, `key` (letter for Amiga+key) and `event`, or `{ "separator": true }` (a line).
  With `"check": true` it has a check mark (`mui_menu_check`): choosing it toggles the mark and gives its event;
  `"checked": true` sets it at the start, and `mui_get_value`/`mui_set_value` read and set it. `"submenu": [ ...items... ]`
  with its `label` is a submenu (`mui_submenu_begin`), one level only and with no `key` or `event`. A menu, item or
  submenu with `name` is a field of the window, like the objects (`v.ver_formulas`: check it, change its text with
  `mui_set_text` or disable it with `mui_set_enabled`); `"disabled": true` leaves it disabled. The visual editor shows
  submenus, but their items, the marks and the names are changed by editing the file as text (Lorraine D47).
- **Translations** (dashweb D71): `"tr": N` on an object, a window, a menu or a menu item gives the main
  text (`text`, `label`, `title`, `titles`, `options`) catalog number `N`: the code requests it with
  `tr(N, "texto")`. For several strings of the same object, `"tr": { "label": 12, "help": 13 }`. They are extracted by
  `tools/catalogo.py cd` together with the program's own (see "Translations" in `docs/MANUAL_REFERENCIA.md`). The visual
  editor preserves them, but does not show or change them yet: you set them by editing the file as text.

## The extension

- **Custom editor** (`CustomTextEditorProvider`) for `*.dashui`: the JSON stays in the VS Code document (normal undo,
  save and source control); the webview is the view.
- **Webview:** object palette on the left, window tree in the middle, properties of the selected object on
  the right, approximate preview below. Tabs per window and a list of menus. Drag from the palette, the
  tree or the preview: before, after or inside a group, depending on where you drop it. Keyboard in the tree: arrows,
  Alt+arrows to move, Del, F2 (name), Enter (properties), Ctrl+D (duplicate); copy, cut and paste
  (duplicate names get a number); undo and redo are the document's (plus ↶ ↷ buttons).
- **Problems and code:** problems in the `.dashui` (JSON, types, names, event numbers) show up in Problems on their
  line. An event's → button takes you to its code in the `.dash` that imports the file: a constant with that number
  (`const ID_ACEPTAR = 3`) and `if ev == ID_ACEPTAR`; if there is none, it creates it (the constant and an `if` in the
  `mui_wait_event` loop).
- **Commands** (`editor/vscode/package.json`): "Dash: Compilar", "Ejecutar en emulador", "Ejecutar con comprobación
  de memoria", "Ejecutar con perfil", "Depurar en el Amiga", "Preparar para un Amiga real", "Elegir la máquina del
  emulador", "Nuevo proyecto", "Nuevo fichero de ventanas MUI (.dashui)", "Elegir la carpeta del compilador" and
  "Reiniciar el servidor de lenguaje". "Ir al código del evento" (the → button) and "Nueva línea (con end)" (the
  Enter key) do not appear in the command palette. "Ver en Amiga" is not a command: it is a button in the visual editor. The Dash path and the emulator variables go in the settings (`dash.path`, `dash.emulator.*`).
- **Syntax highlighting** for `.dash` (TextMate grammar, `syntaxes/dash.tmLanguage.json`, generated with
  `tools/gen_tmgrammar.py`).
- **Editor behavior:**
  - It activates when you open a folder that contains a `.dashui` (`workspaceContains:**/*.dashui`), as well as when you open
    a `.dash` or a `.dashui`.
  - A `.dashui` passed to VS Code at startup (`code carpeta ventana.dashui`) opens in the visual editor, not
    as JSON text.
  - In a narrow panel (the editor beside the `.dash`, half the screen) the properties move below everything else.
  - It uses the VS Code theme colors.
- One runtime dependency, `vscode-languageclient` (the language server client, bundled
  into the package with esbuild). To package, `@vscode/vsce` in a local `node_modules` (not global).

## Plan (tasks 20-24)

- 20: extension skeleton (highlighting, Compile and Run commands) and `compiler/dashui.py` with `import
  ".dashui"` (with generation tests without VS Code).
- 21: editor in the webview (palette, tree, properties, approximate preview), save and open.
- 22: round trip: open a `.dashui` written by hand or modified elsewhere, and preserve what the editor does not understand
  (unknown properties are saved as they are).
- 23: "Ver en Amiga" with the screenshot.
- 24: the browser window (`examples/mui_navegador.dash`) redone with a `.dashui`; documentation.

## Status

Done (tasks 20-24): `compiler/dashui.py` and `import ".dashui"`; extension in `editor/vscode/` with Dash highlighting,
commands, visual editor (palette, tree, properties, menus, approximate preview) and "Ver en Amiga". Example:
`examples/mui_navegador.dashui` + `examples/mui_navegador_editor.dash`. Later, the IDE (`docs/IDE_LOOP.md`):
language server, debugger, copy and paste in the tree.

Published in this repo: release [vscode-0.2.1](https://github.com/FreeMEM/dash/releases/tag/vscode-0.2.1) (PR #11),
with `dash-mui-editor-0.2.1.vsix`. Install it with "Extensions: Install from VSIX..." (VS Code 1.86 or later); see
`docs/INSTALACION.md`, step 9. What was done afterwards (the "al cambiar" checkbox, highlighting for the new builtins) is
in `main` and in the "Unreleased" section of `editor/vscode/CHANGELOG.md`, not yet released.

Pending: there is no multiple selection; the approximate preview does not share out space exactly like MUI.

## Ver en Amiga (IDE, task 20)

An emulated Amiga that stays powered on between previews (it shuts down after 10 minutes unused):
`tools/emu_preview.py --machine a1200|a1200-32|rtg`. With the A500 machine the preview goes to the A1200 (MUI 5 needs a 68020). Inside, a
watcher waits for `DH0:pide` and runs `DH0:vista`, which opens the window, takes its own screenshot with `C:dash_shot` as soon as
it is open, and exits. On planar screens the screenshot is the raw bitplanes (`.dsh`, about 40 KB in 4 colors) and the
PC produces the PNG (`emu_run.planar_to_png`). The extension keeps one per machine and does not recompile a window that has not
changed. Measured: startup 2.5 s (A1200 3.1), 5 s (3.2) and 1.7 s (68040 RTG); each preview, 2.4 s, 2.5 s and 1.8 s (previously,
about 30 s each).

