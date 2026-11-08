"""Simular teclado y ratón (SIMINPUT_FUNCTIONS), ventanas de otros programas (OTHERWIN_FUNCTIONS) y el gestor de
ventanas (WM_FUNCTIONS)."""

GROUPS = {
    "SIMINPUT_FUNCTIONS": {
        "es": """\
Teclas y clics de mentira, como si los hiciera el usuario, por el `input.device` del sistema: van a la ventana
activa, sea del programa o de otro. Sirven para probar un programa solo (los tests de Forja y de Dash los usan) y
para automatizar otros. Las coordenadas cuentan desde la esquina de fuera de la ventana activa, con los bordes.
""",
        "en": """\
Fake keys and clicks, as if the user made them, through the system's `input.device`: they go to the active window,
the program's or another's. They are for testing a program unattended (Forja's and Dash's tests use them) and for
automating others. Coordinates count from the active window's outer corner, borders included.
""",
        "example": "tests/test_doc_otros.dash",
    },
    "OTHERWIN_FUNCTIONS": {
        "es": """\
Encontrar la ventana de otro programa por su título, ponerla delante, saber dónde están sus gadgets y leer los
colores de la pantalla. Con los `input_*`, para manejar otro programa como lo haría el usuario.
""",
        "en": """\
Finding another program's window by its title, bringing it to the front, finding out where its gadgets are and
reading the screen's colours. With the `input_*` functions, to drive another program as the user would.
""",
    },
    "WM_FUNCTIONS": {
        "es": """\
Lo que necesita un gestor de ventanas o una barra de tareas (Trasfondo, por ejemplo): la lista de ventanas de la
pantalla del Workbench con su programa y su tamaño, moverlas, traerlas delante, y los iconos del Workbench, para
dibujarlos o recibir los que se sueltan sobre una ventana.

`wm_read` lee una foto de las ventanas, de delante atrás; las demás `wm_*` dan cada una por número, desde 0. Para
cambiarlas se usa su id (`wm_id`), que sigue valiendo aunque cambie el orden.
""",
        "en": """\
What a window manager or a task bar (Trasfondo, for instance) needs: the list of windows on the Workbench screen
with their program and size, moving them, bringing them to the front, and Workbench icons, to draw them or to get
those dropped on a window.

`wm_read` takes a snapshot of the windows, front to back; the other `wm_*` functions give each one by number, from
0. To change them you use their id (`wm_id`), which stays valid even if the order changes.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_W_ES = "- `win`: la ventana de `window_find`.\n"
_W_EN = "- `win`: the window from `window_find`.\n"
_I_ES = "- `i`: la ventana, desde 0, del último `wm_read`.\n"
_I_EN = "- `i`: the window, from 0, of the last `wm_read`.\n"
_ID_ES = "- `id`: el id de la ventana (`wm_id`).\n"
_ID_EN = "- `id`: the window's id (`wm_id`).\n"
_Q_ES = "1 Mayúsculas, 2 Ctrl, 4 Alt, 8 Amiga, sumadas"
_Q_EN = "1 Shift, 2 Ctrl, 4 Alt, 8 Amiga, added up"
_IC_ES = "- `icon`: el icono de `icon_load`.\n"
_IC_EN = "- `icon`: the icon from `icon_load`.\n"

FUNCS = {
    # ------------------------------------------------------------ simular
    "input_key": _f(f"""\
- `code`: el código en bruto de la tecla (0x44 Return, 0x45 Esc, 0x4C arriba...).
- `qualifiers`: las teclas que van pulsadas alrededor: {_Q_ES}; 0 ninguna.

Pulsa y suelta la tecla en la ventana activa.
""", f"""\
- `code`: the key's raw code (0x44 Return, 0x45 Esc, 0x4C up...).
- `qualifiers`: the keys held around it: {_Q_EN}; 0 none.

Presses and releases the key in the active window.
""", ["input_text", "key_text"]),
    "input_text": _f("- `text`: el texto.\n\nLo escribe en la ventana activa con el mapa de teclado; lo que el mapa no puede escribir se queda fuera.\n",
                     "- `text`: the text.\n\nTypes it into the active window with the keymap; what the keymap cannot type is left out.\n",
                     ["input_key"]),
    "input_move": _f("- `x`, `y`: el punto, desde la esquina de la ventana activa.\n\nLleva allí el puntero.\n",
                     "- `x`, `y`: the point, from the active window's corner.\n\nMoves the pointer there.\n", ["input_click"]),
    "input_click": _f(f"""\
- `x`, `y`: el punto, desde la esquina de fuera de la ventana activa (con los bordes).
- `qualifiers`: las teclas pulsadas durante el clic: 1 Mayúsculas, 2 Ctrl, 4 Alt.

Hace un clic con el botón izquierdo. Para dar en un gadget de otro programa, `gadget_x` y `gadget_y` dicen dónde.
""", f"""\
- `x`, `y`: the point, from the active window's outer corner (borders included).
- `qualifiers`: the keys held during the click: 1 Shift, 2 Ctrl, 4 Alt.

Makes a left-button click. To hit another program's gadget, `gadget_x` and `gadget_y` say where.
""", ["input_drag", "gadget_x"]),
    "input_button": _f("""\
- `button`: 1 izquierdo, 2 derecho (los menús), 3 central.
- `down`: `true` lo pulsa, `false` lo suelta.

Donde esté el puntero. Para mantener abierto un menú mientras se mueve el puntero.
""", """\
- `button`: 1 left, 2 right (menus), 3 middle.
- `down`: `true` presses it, `false` releases it.

Wherever the pointer is. To hold a menu open while the pointer moves.
""", ["input_menu"]),
    "input_drag": _f("- `x1`, `y1`: donde se pulsa.\n- `x2`, `y2`: donde se suelta.\n\nArrastra con el botón izquierdo, desde la esquina de la ventana activa.\n",
                     "- `x1`, `y1`: where it presses.\n- `x2`, `y2`: where it releases.\n\nDrags with the left button, from the active window's corner.\n",
                     ["input_click"]),
    "input_qualifiers": _f("Devuelve las teclas pulsadas ahora, sumadas: 1 y 2 Mayúsculas, 8 Ctrl, 16 y 32 Alt, 64 y 128 Amiga (izquierda y derecha); 0 si no se puede.\n",
                           "Returns the keys held now, added up: 1 and 2 Shift, 8 Ctrl, 16 and 32 Alt, 64 and 128 Amiga (left and right); 0 if it cannot.\n",
                           ["input_key"]),
    "input_menu": _f("""\
- `menu`: el menú, desde 0.
- `item`: la opción, desde 0, contando los separadores.
- `hold`: cuántos tics (1/50 s) se queda pulsado antes de soltar.

Elige esa opción del menú de la ventana activa con el ratón, como un usuario. Devuelve `false` si no hay esa opción.
""", """\
- `menu`: the menu, from 0.
- `item`: the item, from 0, counting separators.
- `hold`: how many ticks (1/50 s) it stays pressed before releasing.

Chooses that item from the active window's menu with the mouse, like a user. Returns `false` if there is no such
item.
""", ["input_button"]),
    "input_move_screen": _f("""\
- `x`, `y`: el punto en la pantalla.
- `buttons`: los botones pulsados durante el camino: 1 izquierdo, 2 derecho, 0 ninguno.

Lleva el puntero píxel a píxel, para que lo sigan los menús de MUI.
""", """\
- `x`, `y`: the point on the screen.
- `buttons`: the buttons held along the way: 1 left, 2 right, 0 none.

Moves the pointer pixel by pixel, so MUI's menus follow it.
""", ["input_move"]),
    "input_active_title": _f("Devuelve el título de la ventana activa, o `\"\"`. Para esperar a que se abra la del programa que se prueba.\n",
                             "Returns the active window's title, or `\"\"`. To wait for the window of the program under test to open.\n",
                             ["window_find"]),
    # ------------------------------------------------------------ otras ventanas
    "window_find": _f("""\
- `title`: el principio del título.

Busca, en todas las pantallas, la ventana cuyo título empieza así (del propio programa u otro). Devuelve un número
para `window_found_*` y `gadget_*`, o 0. Deja de valer si esa ventana se cierra.
""", """\
- `title`: the start of the title.

Looks, on every screen, for the window whose title starts like that (the program's or another's). Returns a number
for `window_found_*` and `gadget_*`, or 0. It stops being valid if that window closes.
""", ["window_found_activate", "gadget_index"]),
    "window_found_activate": _f(_W_ES + "\nLa pone delante, con su pantalla, y la hace activa: los `input_*` van a ella.\n",
                                _W_EN + "\nBrings it to the front, with its screen, and makes it active: the `input_*` functions go to it.\n",
                                ["window_find"]),
    "window_found_box": _f(_W_ES + "- `what`: 0 izquierda, 1 arriba (en su pantalla), 2 ancho, 3 alto, 4 borde izquierdo, 5 borde de arriba.\n",
                           _W_EN + "- `what`: 0 left, 1 top (on its screen), 2 width, 3 height, 4 left border, 5 top border.\n",
                           ["window_find"]),
    "gadget_index": _f(_W_ES + """\
- `text`: el texto del gadget.

Devuelve su sitio en la ventana, desde 0, o -1. Los botones de GadTools no guardan su texto: se busca uno de al lado
que sí lo tenga y se cuenta desde él.
""", _W_EN + """\
- `text`: the gadget's text.

Returns its place in the window, from 0, or -1. GadTools buttons do not keep their text: find a neighbour that does
and count from it.
""", ["gadget_x", "gadget_selected"]),
    "gadget_x": _f(_W_ES + "- `n`: el sitio del gadget.\n\nDevuelve la x de su centro, desde la esquina de la ventana, como la quiere `input_click`; -1 si no hay.\n",
                   _W_EN + "- `n`: the gadget's place.\n\nReturns the x of its centre, from the window's corner, as `input_click` wants it; -1 if none.\n",
                   ["gadget_y", "input_click"]),
    "gadget_y": _f(_W_ES + "- `n`: el sitio del gadget.\n\nDevuelve la y de su centro, como `gadget_x`.\n",
                   _W_EN + "- `n`: the gadget's place.\n\nReturns the y of its centre, like `gadget_x`.\n", ["gadget_x"]),
    "gadget_selected": _f(_W_ES + "- `n`: el sitio del gadget.\n\nDevuelve `true` si está marcado (una casilla).\n",
                          _W_EN + "- `n`: the gadget's place.\n\nReturns `true` if it is ticked (a checkbox).\n", ["gadget_index"]),
    "screen_pixel": _f("- `x`, `y`: el punto.\n\nDevuelve el número de color de ese píxel de la pantalla de delante; -1 fuera de ella.\n",
                       "- `x`, `y`: the point.\n\nReturns the colour number of that pixel of the front screen; -1 outside it.\n",
                       ["screen_pixel_rgb"]),
    "screen_pixel_rgb": _f("- `x`, `y`: el punto.\n\nDevuelve el color de ese píxel de la pantalla de delante como `0xRRGGBB`, lo pinte quien lo pinte; -1 fuera de ella.\n",
                           "- `x`, `y`: the point.\n\nReturns that pixel's colour on the front screen as `0xRRGGBB`, whoever painted it; -1 outside it.\n",
                           ["screen_pixel"]),
    "screen_pen_rgb": _f("""\
- `n`: el lápiz del Workbench: 0 detalle, 1 bloque, 2 texto, 3 brillo, 4 sombra, 5 relleno (la barra de título
  activa), 6 texto del relleno, 7 fondo, 8 texto resaltado, 9 a 11 los de la barra.

Devuelve su color como `0xRRGGBB`, o -1 si no hay ese lápiz. Para que un programa se vea como el Workbench.
""", """\
- `n`: the Workbench pen: 0 detail, 1 block, 2 text, 3 shine, 4 shadow, 5 fill (the active title bar), 6 fill text,
  7 background, 8 highlighted text, 9 to 11 the bar's.

Returns its colour as `0xRRGGBB`, or -1 if there is no such pen. So a program can look like the Workbench.
""", ["color_pen"]),
    "cx_send": _f("""\
- `name`: el nombre de la commodity.
- `command`: como Exchange: 15 desactivar, 17 activar, 19 enseñar, 21 ocultar, 23 quitar.

Devuelve 0 si se hizo, -1 si no hay esa commodity, -2 si no tiene puerto, -99 sin `commodities.library`.
""", """\
- `name`: the commodity's name.
- `command`: as Exchange does: 15 disable, 17 enable, 19 show, 21 hide, 23 quit.

Returns 0 if done, -1 if there is no such commodity, -2 if it has no port, -99 without `commodities.library`.
""", []),
    # ------------------------------------------------------------ gestor de ventanas
    "wm_read": _f("Lee las ventanas de la pantalla del Workbench, de delante atrás, hasta 64, y devuelve cuántas.\n",
                  "Reads the Workbench screen's windows, front to back, up to 64, and returns how many.\n", ["wm_id", "wm_title"]),
    "wm_id": _f(_I_ES + "\nDevuelve su id, para `wm_set_box`, `wm_front` y las demás; 0 fuera de la lista.\n",
                _I_EN + "\nReturns its id, for `wm_set_box`, `wm_front` and the rest; 0 outside the list.\n", ["wm_read"]),
    "wm_title": _f(_I_ES + "\nDevuelve su título, o `\"\"`.\n", _I_EN + "\nReturns its title, or `\"\"`.\n", ["wm_task"]),
    "wm_task": _f(_I_ES + "\nDevuelve su programa: la orden de un proceso de Shell, sin la ruta, o el nombre de su tarea (`\"Workbench\"`).\n",
                  _I_EN + "\nReturns its program: a Shell process's command, without the path, or its task's name (`\"Workbench\"`).\n", ["wm_path"]),
    "wm_path": _f(_I_ES + "\nDevuelve la ruta del programa de esa ventana; `\"\"` si no es de un proceso o ya se cerró.\n",
                  _I_EN + "\nReturns the path of that window's program; `\"\"` if it is not a process's or it has closed.\n", ["file_real_path"]),
    "wm_box": _f(_I_ES + "- `what`: 0 izquierda, 1 arriba, 2 ancho, 3 alto, 4 y 5 el mínimo, 6 y 7 el máximo (0 o 65535: sin límite).\n\nDevuelve ese dato, o -1 fuera de la lista.\n",
                 _I_EN + "- `what`: 0 left, 1 top, 2 width, 3 height, 4 and 5 the minimum, 6 and 7 the maximum (0 or 65535: no limit).\n\nReturns that value, or -1 outside the list.\n",
                 ["wm_set_box"]),
    "wm_flags": _f(_I_ES + "\nDevuelve, sumados: 1 se puede redimensionar, 2 de fondo, 4 sin bordes, 8 activa, 16 con barra de arrastre, 32 del propio programa, 64 un cajón del Workbench, 128 con un requester.\n",
                   _I_EN + "\nReturns, added up: 1 resizable, 2 backdrop, 4 borderless, 8 active, 16 with a drag bar, 32 the program's own, 64 a Workbench drawer, 128 with a requester.\n",
                   ["wm_box"]),
    "wm_set_box": _f(_ID_ES + "- `x`, `y`, `width`, `height`: la caja nueva.\n\nMueve y redimensiona la ventana, dentro de sus límites y de su pantalla. Devuelve `false` si ya no está.\n",
                     _ID_EN + "- `x`, `y`, `width`, `height`: the new box.\n\nMoves and resizes the window, within its limits and its screen. Returns `false` if it is gone.\n",
                     ["wm_box"]),
    "wm_front": _f(_ID_ES + "\nLa pone delante. Devuelve `false` si ya no está.\n", _ID_EN + "\nBrings it to the front. Returns `false` if it is gone.\n", ["wm_back"]),
    "wm_back": _f(_ID_ES + "\nLa pone detrás. Devuelve `false` si ya no está.\n", _ID_EN + "\nSends it to the back. Returns `false` if it is gone.\n", ["wm_front"]),
    "wm_activate": _f(_ID_ES + "\nLa hace activa: las teclas van a ella. Devuelve `false` si ya no está.\n", _ID_EN + "\nMakes it active: keys go to it. Returns `false` if it is gone.\n", ["wm_active"]),
    "wm_zip": _f(_ID_ES + "\nLa pasa a su otro tamaño, como su botón de zoom. Devuelve `false` si ya no está.\n", _ID_EN + "\nSwitches it to its other size, like its zoom button. Returns `false` if it is gone.\n", ["wm_set_box"]),
    "wm_active": _f("Devuelve el id de la ventana activa si está en la pantalla del Workbench; 0 si no.\n", "Returns the active window's id if it is on the Workbench screen; 0 otherwise.\n", ["wm_activate"]),
    "wm_at": _f("- `x`, `y`: un punto de la pantalla del Workbench.\n\nDevuelve el id de la ventana de delante en ese punto; 0 si ninguna.\n",
                "- `x`, `y`: a point on the Workbench screen.\n\nReturns the id of the front window at that point; 0 if none.\n", ["wm_pointer_x"]),
    "wm_pointer_x": _f("Devuelve la x del puntero en la pantalla del Workbench.\n", "Returns the pointer's x on the Workbench screen.\n", ["wm_pointer_y"]),
    "wm_pointer_y": _f("Devuelve la y del puntero en la pantalla del Workbench.\n", "Returns the pointer's y on the Workbench screen.\n", ["wm_pointer_x"]),
    "wm_bar_height": _f("Devuelve el alto de la barra de título de la pantalla del Workbench, donde suelen empezar las ventanas.\n",
                        "Returns the height of the Workbench screen's title bar, where windows usually start.\n", []),
    "wm_bar_gadgets": _f("Devuelve a qué distancia del borde derecho de la barra de la pantalla empiezan sus botones del sistema; 0 si no lo sabe.\n",
                         "Returns how far from the right edge of the screen's bar its system buttons start; 0 if unknown.\n", []),
    "file_real_path": _f("- `path`: un fichero o cajón.\n\nDevuelve su ruta real, con el nombre del volumen (`\"SYS:Utilities/Clock\"` da `\"System:Utilities/Clock\"`), para compararla con `wm_path`; `\"\"` si no existe.\n",
                         "- `path`: a file or drawer.\n\nReturns its real path, with the volume's name (`\"SYS:Utilities/Clock\"` gives `\"System:Utilities/Clock\"`), to compare with `wm_path`; `\"\"` if it does not exist.\n",
                         ["wm_path"]),
    "app_window": _f("- `handle`: la ventana: 0 la actual, o un número de `window_create`.\n\nHace que acepte iconos soltados desde el Workbench. Devuelve `true` si los acepta. Las rutas, con `app_drop`.\n",
                     "- `handle`: the window: 0 the current one, or a `window_create` number.\n\nMakes it accept icons dropped from the Workbench. Returns `true` if it does. The paths come with `app_drop`.\n",
                     ["app_drop", "mui_on_drop"]),
    "app_drop": _f("Devuelve la ruta del siguiente icono soltado en una `app_window`, o `\"\"` si no hay; se mira desde un `On Timer`. Varios iconos salen uno a uno.\n",
                   "Returns the path of the next icon dropped on an `app_window`, or `\"\"` if none; check it from an `On Timer`. Several icons come one by one.\n",
                   ["app_drop_x", "app_window"]),
    "app_drop_x": _f("Devuelve la x de donde cayó el último icono, desde la esquina de la ventana.\n", "Returns the x where the last icon landed, from the window's corner.\n", ["app_drop_y"]),
    "app_drop_y": _f("Devuelve la y de donde cayó el último icono.\n", "Returns the y where the last icon landed.\n", ["app_drop_x"]),
    "icon_load": _f("""\
- `path`: el programa, cajón o fichero, sin `.info`.

Carga su icono con los colores de la pantalla de la ventana (con AmigaOS 3.5 o más, también iconos de color y PNG,
y el de su tipo si no tiene). Devuelve un número para `icon_draw`, o 0.
""", """\
- `path`: the program, drawer or file, without `.info`.

Loads its icon with the colours of the window's screen (with AmigaOS 3.5 or later, colour and PNG icons too, and its
type's icon if it has none). Returns a number for `icon_draw`, or 0.
""", ["icon_draw", "icon_free"]),
    "icon_draw": _f(_IC_ES + "- `x`, `y`: su esquina.\n\nLo dibuja como el Workbench, sin nombre ni marco.\n",
                    _IC_EN + "- `x`, `y`: its corner.\n\nDraws it like the Workbench, without a name or frame.\n", ["icon_draw_size"]),
    "icon_draw_size": _f(_IC_ES + "- `x`, `y`, `width`, `height`: el recuadro.\n\nLo dibuja a ese tamaño con los bordes suaves en una pantalla de color real; en otra, a su tamaño y centrado.\n",
                         _IC_EN + "- `x`, `y`, `width`, `height`: the box.\n\nDraws it at that size with smooth edges on a true-colour screen; on others, at its own size and centred.\n",
                         ["icon_draw"]),
    "icon_width": _f(_IC_ES + "\nDevuelve su ancho tal como lo dibuja `icon_draw`; 0 si no está.\n", _IC_EN + "\nReturns its width as `icon_draw` draws it; 0 if missing.\n", ["icon_height"]),
    "icon_height": _f(_IC_ES + "\nDevuelve su alto tal como lo dibuja `icon_draw`; 0 si no está.\n", _IC_EN + "\nReturns its height as `icon_draw` draws it; 0 if missing.\n", ["icon_width"]),
    "icon_free": _f(_IC_ES + "\nLo libera. Los que queden, al acabar.\n", _IC_EN + "\nFrees it. Those left, at the end.\n", ["icon_load"]),
}
