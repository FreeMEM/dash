# Changelog

## 0.3.0 (2026-10-27)

- New versions of Dash: once a day the extension looks at Dash's releases on GitHub (tags `v1.0.0`...) and, if
  there is one newer than the compiler in use, says so, with a button to its notes and another to pass over that
  version. Setting `dash.updates.check`; without network it tries again the next time.
- Highlighting: the builtins added to Dash since 0.2.4 (`clip_*`, `mui_canvas_set_pointer`,
  `mui_canvas_take_tab`, `mui_context_menu_begin`, `mui_set_context_menu`, `input_button`, `str_compare_locale`).
- Visual editor: context menus (`context_menus` of the window, `context_menu` of an object, "+ menú contextual")
  and `take_tab` on a drawing area (Tab and Shift+Tab go to it while the pointer is over it).

## 0.2.4 (2026-10-27)

- Highlighting: the keyword `interface` and the type `Double`, and the builtins added to Dash since 0.2.3
  (`sqrt`, `pow`, `sin` and the other Double maths, `str_from_double`/`str_to_double`, `utf8_*`, `inflate`,
  `deflate`, `crc32`, `buffer_*`, `regex_*`, `wildcard_match`, `locale_*`, `input_*`, `mui_menu_check`,
  `mui_submenu_*`, `mui_canvas_qualifiers`, `mui_canvas_on_drag`, `mui_image_toggle`, `mui_combo`...).
- Visual editor: two new objects for toolbars, `image_toggle` (a picture button that stays pressed; with a
  `group`, the buttons of the group exclude each other) and `combo` (a text field with a list that drops down),
  in the palette and the preview.
- Visual editor: menus may have items with a check mark (`check`, `checked`), submenus of one level (`submenu`)
  and names (`name`, a field of the window). The editor shows submenus; their items, the marks and the names are
  changed by editing the file as text. It reports a submenu inside another, `checked` without `check` and a name
  used by a menu item and an object.
- Visual editor: `interface` is refused as a name, as the compiler does.

## 0.2.3 (2026-10-25)

- Visual editor: problems that the compiler refuses are now shown before compiling: two windows with the same
  name, and `#{` in a text or a title (it would be read as interpolation). An object named `constructor` or
  `toString` is no longer reported as repeated.
- Visual editor: emptying a number field says it must be a whole number instead of leaving 0; a drawing area
  with a weight keeps its minimum size in the preview; a drag cancelled with Esc or let go elsewhere leaves
  nothing marked, and a file dragged in afterwards is not taken for the old object.
- Visual editor and Problems panel: what the compiler refuses in a hand-edited or pasted `.dashui` is shown
  before compiling: children inside an object that is not a group, a wrong `tr`, `size` that is not
  [width, height], a list where a text goes, an object without a type, and a window `id`, `close` or menu event
  that is not a whole number.
- Problems panel: a new menu option (event 0) is no longer an error, and an object or window called
  `constructor` is no longer reported as repeated.
- Ver en Amiga: after updating Dash, the window is compiled again (the saved program also depends on the
  compiler), instead of showing the one built with the old Dash.

## 0.2.2 (2026-10-25)

- Visual editor: "al cambiar", next to "Ver en Amiga", shows the window on the Amiga again by itself a moment
  after each change (the setting `dash.emulator.previewOnChange`). One at a time; if the emulator fails, it goes
  off by itself instead of showing an error at every change. Ticking it is remembered for every `.dashui`.
- Highlighting: the directives `@catalog` and `@version`, and the builtins added to Dash since 0.2.1
  (`dos_requesters`, `base64_to_file`, `tooltype`, `cx_*`, `disks_read`/`disk_*`, `net_ifs_read`/`net_if_*`,
  `wifi_*`, `net_drivers_read`/`net_driver_*`, `net_listen`/`net_accept`/`net_peer`/`net_port`, `net_udp_*`,
  `mouse_curve*`, `mouse_patch_left`, `usb_hid_*`, `mouse_prefs_*`, `tr`, `catalog_*`, `screen_font_*`,
  `window_border_*`, `clock_*`, `date_text`, `program_version`, `file_notify*`, `file_changed`, `run_program`,
  `program_relaunch`). Completion and hover get them from the compiler, without a new version.
- README: the video tutorial is on YouTube.

## 0.2.1 (2026-10-21)

Found making the video tutorial and hunting odd cases (docs/IDE_VIDEO_LOOP.md of the Dash repository).

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
- Rename refuses a name that would join two things (two functions, two variables, two fields) and works from a
  field's declaration; completion inside `#{...}` offers only what goes in an expression.

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
