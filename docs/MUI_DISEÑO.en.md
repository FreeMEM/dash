# MUI in Dash: design (task 2 of `docs/MUI_LOOP.md`)

*English | [Castellano](MUI_DISEÑO.md)*

Works with MUI 3.8 (muimaster.library V19) or MUI 5. The full list of `mui_` builtins is in
`docs/BUILTINS.md`.

## Decisions

1. **`mui_` builtins**, no new syntax for now. MUI objects are values the program
   stores in variables (numbers, like Dash buffers and files: the codegen converts them to pointers when calling
   the runtime; task 3): several windows and many objects are needed (the browser, now Tachyon). The ReAction API (`ra_`)
   is not up to that: at most 4 windows, and gadgets by number.
2. **The tree is built with a stack**, like `ra_layout_*`: `mui_vgroup_begin()` ... `mui_group_end()`.
   Every object created goes into the open group. Internally, each group is created empty and the children are added
   with `OM_ADDMEMBER`; `mui_window_end()` creates the window with its root group and adds it to the application.
3. **Events by number**, like `ra_wait_event`: `mui_on_press(boton, ID_ATRAS)` sets up a `MUIM_Notify` that
   returns `ID_ATRAS` via `MUIV_Application_ReturnID`. `mui_wait_event()` waits and returns it. -1 = quit.
4. **Custom drawing area** with a MUI class built into the runtime and a Dash function (`Func`) that draws with
   the `gfx_` builtins. This is the core piece of the browser.
5. **Declarative format: `.dashui`** (decided in task 19). A JSON file produced by the visual editor that
   the program uses with `import "ventana.dashui"`; `compiler/dashui.py` turns it into Dash code using these
   builtins. Format and rules in `docs/MUI_EDITOR.md`.

## API

Types: MUI object = number (handle, like a buffer); `Int`; `String`. Strings that MUI does not copy (application and window titles,
menus, cycles, tabs) are copied by the runtime into its pool, and live until `mui_app_end()`.

### Application and windows

| Builtin | What it does |
|---|---|
| `mui_app_begin(titulo, base)` | Opens muimaster (version 19+), checks for a 68020 and creates the application (`base`: ARexx name, in uppercase). |
| `mui_window_begin(titulo, id)` | Starts a window. `id` (1-255, 0 = none) makes MUI remember its size and position. Opens its vertical root group. |
| `mui_window_end()` | Closes the root group, creates the window and adds it to the application. |
| `mui_window_open(win) -> Bool` | Opens the window (false if it could not: screen too small, out of memory). |
| `mui_window_close(win)` | Closes it (it still exists). |
| `mui_window_size(win, ancho, alto)` | Size when opened, as a percentage of the visible screen, centered (before opening it). |
| `mui_window_fullscreen(win)` | Fills the whole screen, with no borders, title bar or gadgets (before opening it). |
| `mui_window_own_screen(win) -> Bool` | Full screen on a screen of its own, like the public one (before opening it; false: on the public screen). |
| `mui_window_active(win) -> Int` | 1 if it is the active window (several windows from one `.dashui` share event numbers). |
| `mui_app_end()` | `MUI_DisposeObject` on the application (and its whole tree), closes muimaster, frees the strings. Called automatically on exit if the program does not call it. |

### Groups and layout

| Builtin | What it does |
|---|---|
| `mui_vgroup_begin()`, `mui_hgroup_begin()` | Vertical or horizontal group. |
| `mui_frame_begin(titulo, horizontal)` | Group with a frame and title (`""` = no title). |
| `mui_columns_begin(n)` | Grid group with `n` columns (forms with label + field). |
| `mui_group_end()` | Closes the open group. |
| `mui_scroll_begin()` | Area with scrollbars (content larger than the window). |
| `mui_space()` | Stretchable space. |
| `mui_balance()` | Divider the user can drag (`Balance`). |
| `mui_weight(obj, peso)` | Weight when sharing out space (100 by default). |
| `mui_register_begin(titulos)` | Tabs (`Register`); `titulos` = strings separated by `|`. Each child is a page. |

### Objects

| Builtin | MUI class |
|---|---|
| `mui_text(texto)` | `Text` (accepts MUI formatting codes, `\33c` centered...) |
| `mui_label(texto)` | `Label` (aligned for forms) |
| `mui_button(texto)` | `SimpleButton` (`_` before a letter = keyboard shortcut) |
| `mui_string(inicial, max)` | `String` |
| `mui_checkbox(marcado)` | `CheckMark` |
| `mui_cycle(opciones)` | `Cycle` (`"Uno|Dos|Tres"`) |
| `mui_slider(min, max, valor)` | `Slider` |
| `mui_gauge(max)` | Horizontal `Gauge` (progress bar) |
| `mui_list()` | `Listview` + `List` of strings (the object returned is the `Listview`; the runtime uses its `List`) |
| `mui_scrollbar(vertical)` | `Scrollbar` (`Prop`) |
| `mui_canvas(ancho_min, alto_min)` | Custom drawing class (below) |
| `mui_image(fichero)` | `Dtpic` (ILBM; PNG, JPEG, GIF if their datatypes are installed). `mui_set_text` changes the file |
| `mui_image_button(fichero)` | Button with an image (toolbar icon): `mui_on_press` as with a button |
| `mui_image_toggle(fichero, grupo, pulsado)` | Image button that stays pressed; `grupo` > 0: exclusive (Lorraine D14) |
| `mui_combo(texto, opciones)` | Text field with a drop-down list; `mui_on_ack` on Return or a pick (Lorraine D14) |

### Values

| Builtin | What it does |
|---|---|
| `mui_get_text(obj) -> String` | Text of a `String`, `Text`, button or window title (a new copy for Dash). |
| `mui_set_text(obj, texto)` | Changes the text (`String`, `Text`, button; window: title is copied). |
| `mui_get_value(obj) -> Int` | Depending on the class: checked state, slider level, cycle choice, gauge value, active list line (-1 = none), tab, scrollbar position. |
| `mui_set_value(obj, v)` | The same, for writing. Fires notifications as if the user had done it. |
| `mui_set_enabled(obj, si)` | `MUIA_Disabled`. |
| `mui_set_visible(obj, si)` | `MUIA_ShowMe` (the window relayouts). |
| `mui_set_range(barra, total, visible)` | Scrollbar: size of the document and of the visible part. |
| `mui_width(obj) -> Int`, `mui_height(obj) -> Int` | On-screen size in pixels (0 before the window is opened). |
| `mui_help(obj, texto)` | Bubble help when the pointer rests over it. |

### Lists

`mui_list_add(lista, texto)`, `mui_list_insert(lista, pos, texto)`, `mui_list_remove(lista, pos)`,
`mui_list_clear(lista)`, `mui_list_count(lista) -> Int`, `mui_list_get(lista, pos) -> String`.
The strings are copied by MUI (`MUIV_List_ConstructHook_String`). For many lines: `mui_list_quiet(lista, si)`.

### Events

| Builtin | Notification |
|---|---|
| `mui_on_press(obj, id)` | button pressed (`MUIA_Pressed` → FALSE) |
| `mui_on_change(obj, id)` | the value changes (checked state, level, cycle, active line, tab, text) |
| `mui_on_ack(string, id)` | Return in a string gadget (`MUIA_String_Acknowledge`) |
| `mui_on_double(lista, id)` | double-click on a list |
| `mui_on_close(win, id)` | the window's close gadget. Without calling it, closing the first window = -1 (quit). |
| `mui_menu_begin(titulo)`, `mui_menu_item(texto, tecla, id)`, `mui_menu_separator()`, `mui_menu_end()` | menu of the open window (`Menustrip`) |
| `mui_menu_check(texto, tecla, id, marcada)`, `mui_submenu_begin(titulo)` / `mui_submenu_end()` | item with a check mark (`mui_get_value`/`mui_set_value`) and one-level submenu |
| `mui_context_menu_begin(titulo)` ... `mui_menu_end()`, `mui_set_context_menu(obj, menu)` | context menu (right button over `obj`): its items give their events; MUI does not free it with the object, Dash does at the end |
| `mui_wait_event() -> Int` | Waits and returns the number of an event, or -1 to quit. |
| `mui_poll_event() -> Int` | The same without waiting: 0 if there is nothing. |
| `mui_wait_event_signals(mascara) -> Int` | Also waits for other signals: `net_signal()` (network), `task_signal()` (tasks), `file_notify_signal()` (watched files). Returns 0 when one of them arrives; `mui_signals()` tells which. |
| `mui_timer(ms, id)` | In `ms` milliseconds `mui_wait_event` returns `id`, once (for another one, call it again; 0 cancels it). |
| `mui_press(obj)` | Fires that object's `mui_on_press` event as if it had been pressed (shortcuts, tests). |

Event numbers belong to the program (`const ID_ATRAS = 1`) and are greater than 0.

### Drawing area

```ruby
func pinta(x: Int, y: Int, ancho: Int, alto: Int)
    gfx_pen(2)
    gfx_rect(x, y, x + ancho - 1, y + alto - 1)
end

pagina = mui_canvas(320, 200)
mui_canvas_on_draw(pagina, pinta)      # MUIM_Draw: _dash_rp = the object's RastPort, clipped to it
mui_canvas_on_input(pagina, ID_RATON)  # clicks, wheel and keys inside the area
...
mui_canvas_redraw(pagina)              # requests a redraw (from the main task, never from another one)
mui_canvas_update(pagina)              # MUI_Redraw with MADF_DRAWUPDATE: no clearing; mui_canvas_updating() = true
mui_canvas_update_area(pagina, x, y, an, al)  # the same, only in that area (with buffered, only that area goes to the window)
mui_canvas_buffered(pagina, true)      # D48: draws into a friend BitMap with its own layer; one BltBitMapRastPort at the end
mui_canvas_on_move(pagina, ID_MUEVE)   # the pointer moves over the area or leaves it, without a click
```

After a `mui_canvas_on_input` event, what happened (position relative to the corner of the area):

| Builtin | What it returns |
|---|---|
| `mui_canvas_mouse_x(c)`, `mui_canvas_mouse_y(c)` | Position of the last click or wheel movement. |
| `mui_canvas_button(c)` | 1 if it was a left click, otherwise 0. |
| `mui_canvas_wheel(c)` | +1 / -1 if it was the wheel (up / down), otherwise 0. |
| `mui_canvas_key(c)` | Key code (raw), -1 if it was not a key. |
| `mui_canvas_char(c) -> String` | The character for that key, with Shift and the keymap applied (`""` if there is none). |
| `mui_canvas_qualifiers(c)` | Keys held at the last input (key, click, wheel): 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga, added up. |
| `mui_canvas_on_drag(c, id)`, `mui_canvas_drag(c)` | Dragging: event when moving with the button down (1) and when let go (2). |
| `mui_canvas_pointer_x(c)`, `mui_canvas_pointer_y(c)` | Current pointer position (with or without a click). |
| `mui_canvas_pointer_inside(c) -> Bool` | Whether the pointer is currently over the area. |
| `mui_canvas_set_pointer(c, shape)` | The pointer's shape over the area: 0 normal, 1 text (I), 2 resize left-right, 3 up-down, 4 busy. It changes at once if the pointer is over it (or dragging the area) and goes back to normal outside it. 1-3 are sprites of their own: Intuition 3.1 and 3.2 lack them. |

The custom class (`MUI_CreateCustomClass` on top of `Area`) implements `MUIM_AskMinMax`, `MUIM_Draw`, `MUIM_Setup`/
`MUIM_Cleanup` (event handler with `MUIM_Window_AddEventHandler`) and `MUIM_HandleEvent`. Scrolling is
handled by the program with a `mui_scrollbar` alongside: the browser draws from the line the scrollbar indicates. It is faster
and simpler than putting the area inside a `Virtgroup`.

## Example: the browser window

```ruby
const ID_ATRAS = 1
const ID_ADELANTE = 2
const ID_RECARGAR = 3
const ID_IR = 4
const ID_SCROLL = 5
const ID_SALIR = 6

func pinta(x: Int, y: Int, ancho: Int, alto: Int)
    gfx_pen(0)
    gfx_rect(x, y, x + ancho - 1, y + alto - 1)
    gfx_pen(1)
    gfx_text_at(x + 4, y + 12, "Página de prueba")
end

Main
    mui_app_begin("dashweb", "DASHWEB")
    win = mui_window_begin("dashweb", 1)
        mui_menu_begin("Proyecto")
            mui_menu_item("Salir", "Q", ID_SALIR)
        mui_menu_end()
        mui_hgroup_begin()
            atras = mui_button("<")
            adelante = mui_button(">")
            recargar = mui_button("_Recargar")
            url = mui_string("http://aminet.net/", 1024)
        mui_group_end()
        mui_hgroup_begin()
            pagina = mui_canvas(320, 160)
            barra = mui_scrollbar(true)
        mui_group_end()
        mui_hgroup_begin()
            estado = mui_text("Listo")
            progreso = mui_gauge(100)
            mui_weight(progreso, 30)
        mui_group_end()
    mui_window_end()

    mui_on_press(atras, ID_ATRAS)
    mui_on_press(adelante, ID_ADELANTE)
    mui_on_press(recargar, ID_RECARGAR)
    mui_on_ack(url, ID_IR)
    mui_on_change(barra, ID_SCROLL)
    mui_canvas_on_draw(pagina, pinta)
    mui_set_enabled(adelante, false)

    mui_window_open(win)
    while true
        ev = mui_wait_event()
        if ev == -1 or ev == ID_SALIR
            break
        end
        if ev == ID_IR
            mui_set_text(estado, "Cargando " + mui_get_text(url))
            mui_set_value(progreso, 50)
        end
        if ev == ID_SCROLL
            mui_canvas_redraw(pagina)
        end
    end
    mui_app_end()
end
```

## Under the hood

- **Headers:** the runtime defines `NO_INLINE_STDARG` before `proto/muimaster.h` and uses its own array-based
  macros (`MUI_NewObject`, `DoMethod`), because the SDK's inline function loses the tags with `-O2`
  (log, task 1). `IPTR` = `ULONG` if the NDK does not provide it.
- **Building:** the MUI runtime is only emitted if the program uses some `mui_` builtin. Then `./dash` and the runner add
  `-I $DASH_MUI_SDK/C/include` (by default `~/.cache/dash-mui/x/SDK/MUI`), in `compiler/cflags.py`. Without the SDK:
  a clear error ("MUI SDK not found: run tools/get_mui_sdk.sh or set DASH_MUI_SDK").
- **Stack:** 32 KB by default in programs that use MUI (done in task 1).
- **CPU:** MUI 5 for OS3 requires a 68020. `mui_app_begin` checks for it (`SysBase->AttnFlags`) and exits with a message
  on a 68000 instead of hanging. The check also applies with MUI 3.8.
- **Version:** `mui_app_begin` opens muimaster.library V19 or later (MUI 3.8 or 5).
- **Memory:** MUI owns the objects; handles carry no reference count and become invalid after
  `mui_app_end()`. Strings passed to `mui_text`, `mui_string`, `mui_list_add`... are copied by MUI, so
  Dash temporaries can be freed at the end of the loop iteration. `--memcheck` must finish with nothing left alive.
- **Tests in the emulator:** almost all without a mouse: `mui_set_value` (fires `on_change`), `mui_press`, `mui_get_*` and
  `mui_window_open`. Three move the pointer, click or press keys for real through `input.device`
  (`test_mui_canvas_move`, `test_mui_canvas_char`, `test_mui_menu_keys`). Programs end on their own with
  `--autoclose`: when the time is up `mui_wait_event` returns -1, as when closing, and the program exits along its normal path (whatever comes after the loop runs); if it still has not finished 5 s later, it is killed outright.
- **Error chain:** no muimaster, a window that will not open or a 68000 → message on standard output and
  `mui_app_begin` returns 0; the program decides what to do.
