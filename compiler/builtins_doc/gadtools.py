"""GadTools (GADTOOLS_FUNCTIONS) y menús (MENU_FUNCTIONS)."""

GROUPS = {
    "GADTOOLS_FUNCTIONS": {
        "es": """\
Gadgets de GadTools para una sola ventana, con su propio bucle de eventos. Es la forma más antigua de Dash; para
programas nuevos, los gadgets por número del grupo Intuition (`button_create`...), que admiten varias ventanas y el
`EventLoop`, o MUI.

**El flujo:**

1. Abrir la ventana (`Window X ... end` y `X.open`, o `window_create`).
2. `gt_init()`: prepara GadTools para la ventana actual. Los `gt_*` y los menús son de esa ventana.
3. Crear los gadgets: `gt_button`, `gt_string`, `gt_slider`... Cada uno devuelve su número, desde 0 y por orden, o
   -1 si no se pudo. Hasta 64. `x`, `y` cuentan desde la esquina de dentro de los bordes.
4. `gt_attach()`: los pone en la ventana. Los creados después no salen.
5. El bucle: `gt_wait_event()` espera y devuelve el número del gadget usado, o -2 si se pulsó el botón de cerrar.

`gt_init` otra vez empieza de cero: libera los gadgets y menús de antes. Al acabar el programa se libera todo.
""",
        "en": """\
GadTools gadgets for a single window, with their own event loop. It is Dash's oldest way; for new programs, the
numbered gadgets of the Intuition group (`button_create`...), which allow several windows and the `EventLoop`, or
MUI.

**The flow:**

1. Open the window (`Window X ... end` and `X.open`, or `window_create`).
2. `gt_init()`: sets GadTools up for the current window. The `gt_*` functions and the menus belong to that window.
3. Create the gadgets: `gt_button`, `gt_string`, `gt_slider`... Each returns its number, from 0 and in order, or -1
   if it could not. Up to 64. `x`, `y` count from the corner inside the borders.
4. `gt_attach()`: puts them on the window. Those created afterwards do not show.
5. The loop: `gt_wait_event()` waits and returns the number of the gadget used, or -2 if the close button was
   pressed.

`gt_init` again starts from scratch: it frees the previous gadgets and menus. Everything is freed when the program
ends.
""",
        "example": "tests/test_doc_gadtools.dash",
    },
    "MENU_FUNCTIONS": {
        "es": """\
Los menús de la barra de la pantalla para la ventana de `gt_init`. Se describen en orden (`menu_title`, sus
`menu_item`, el siguiente `menu_title`...) y `menu_attach()` los pone. Cada opción tiene un número del programa.
Se leen con `menu_event()` en un bucle propio, o en el `On Menu` de un `EventLoop` con `menu_id()`. Los menús de
MUI van aparte (`mui_menu_*`).
""",
        "en": """\
The screen bar's menus for the `gt_init` window. They are described in order (`menu_title`, its `menu_item`s, the
next `menu_title`...) and `menu_attach()` puts them up. Each item has a number of the program's. Read them with
`menu_event()` in a loop of your own, or in an `EventLoop`'s `On Menu` with `menu_id()`. MUI's menus are separate
(`mui_menu_*`).
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_G_ES = "- `x`, `y`: la esquina, dentro de los bordes.\n- `w`, `h`: el tamaño.\n- `label`: el texto; con una `_` delante, la letra sale subrayada.\n"
_G_EN = "- `x`, `y`: the corner, inside the borders.\n- `w`, `h`: the size.\n- `label`: the text; with a `_` before a letter, it shows underlined.\n"
_ID_ES = "- `gad_id`: el número que dio su `gt_*`.\n"
_ID_EN = "- `gad_id`: the number its `gt_*` gave.\n"
_M_ES = "- `label`: el texto.\n- `shortcut`: la letra del atajo con Amiga (`\"N\"` = Amiga+N); `\"\"` ninguno.\n- `id`: el número que da al elegirla.\n"
_M_EN = "- `label`: the text.\n- `shortcut`: the shortcut letter with Amiga (`\"N\"` = Amiga+N); `\"\"` none.\n- `id`: the number it gives when chosen.\n"

FUNCS = {
    "gt_init": _f("""\
Prepara GadTools para la ventana actual, que tiene que estar abierta. Libera los gadgets y menús de un `gt_init`
anterior. Devuelve `false` sin ventana o sin memoria.
""", """\
Sets GadTools up for the current window, which must be open. Frees the gadgets and menus of an earlier `gt_init`.
Returns `false` without a window or without memory.
""", ["gt_attach", "gt_cleanup"]),
    "gt_cleanup": _f("Quita los gadgets y los menús de la ventana y los libera. Al acabar el programa se hace solo.\n",
                     "Removes the gadgets and menus from the window and frees them. It happens on its own when the program ends.\n",
                     ["gt_init"]),
    "gt_attach": _f("""\
Pone en la ventana los gadgets creados desde `gt_init` y los dibuja. Va después del último `gt_*`.
""", """\
Puts the gadgets created since `gt_init` on the window and draws them. It goes after the last `gt_*`.
""", ["gt_init", "gt_wait_event"]),
    "gt_button": _f(_G_ES + "\nCrea un botón. Devuelve su número, o -1. `gt_wait_event` lo devuelve al pulsarlo.\n",
                    _G_EN + "\nCreates a button. Returns its number, or -1. `gt_wait_event` returns it when pressed.\n",
                    ["gt_wait_event"]),
    "gt_checkbox": _f(_G_ES + "- `checked`: si empieza marcada.\n\nCrea una casilla, con el texto a la izquierda. `gt_get_value` da 1 o 0.\n",
                      _G_EN + "- `checked`: whether it starts ticked.\n\nCreates a checkbox, with the text on its left. `gt_get_value` gives 1 or 0.\n",
                      ["gt_get_value"]),
    "gt_string": _f(_G_ES + """\
- `initial`: el texto con el que empieza.
- `maxchars`: cuántas letras caben.

Crea un campo de texto, con la etiqueta a la izquierda. Llega su evento al pulsar Return o Tab; `gt_get_string`
lo lee.
""", _G_EN + """\
- `initial`: the starting text.
- `maxchars`: how many letters fit.

Creates a text field, with the label on its left. Its event arrives on Return or Tab; `gt_get_string` reads it.
""", ["gt_get_string", "gt_set_text"]),
    "gt_integer": _f(_G_ES + "- `initial`: el número con el que empieza.\n\nCrea un campo de números enteros. `gt_get_value` lo lee.\n",
                     _G_EN + "- `initial`: the starting number.\n\nCreates a whole-number field. `gt_get_value` reads it.\n",
                     ["gt_get_value"]),
    "gt_slider": _f(_G_ES + """\
- `min`, `max`: los extremos.
- `level`: el valor con el que empieza.

Crea un deslizador horizontal. Manda su evento mientras se mueve; `gt_get_value` da el valor.
""", _G_EN + """\
- `min`, `max`: the ends.
- `level`: the starting value.

Creates a horizontal slider. It sends its event while it moves; `gt_get_value` gives the value.
""", ["gt_get_value", "gt_set_value"]),
    "gt_palette": _f(_G_ES + """\
- `depth`: cuántos colores enseña: 2 elevado a `depth`.
- `color`: el elegido al empezar.

Crea un selector con los colores de la pantalla. `gt_get_value` da el elegido.
""", _G_EN + """\
- `depth`: how many colours it shows: 2 to the power of `depth`.
- `color`: the one chosen at the start.

Creates a picker with the screen's colours. `gt_get_value` gives the chosen one.
""", ["gt_get_value"]),
    "gt_text": _f(_G_ES + "- `text`: lo que enseña.\n\nCrea un texto con borde que no se edita; `gt_set_text` lo cambia.\n",
                  _G_EN + "- `text`: what it shows.\n\nCreates a bordered text that is not edited; `gt_set_text` changes it.\n",
                  ["gt_set_text"]),
    "gt_cycle": _f(_G_ES + "- `options`: las opciones separadas por `|`.\n\nCrea un gadget que pasa a la siguiente opción con cada clic. `gt_get_value` da la elegida, desde 0.\n",
                   _G_EN + "- `options`: the options separated by `|`.\n\nCreates a gadget that moves to the next option with each click. `gt_get_value` gives the chosen one, from 0.\n",
                   ["gt_get_value"]),
    "gt_get_value": _f(_ID_ES + """\
Devuelve su valor: 1 o 0 en una casilla; el nivel de un deslizador; el color de una paleta; el número de un campo
de números; la opción de un ciclo. 0 en los demás.
""", _ID_EN + """\
Returns its value: 1 or 0 for a checkbox; a slider's level; a palette's colour; a number field's number; a cycle's
option. 0 for the others.
""", ["gt_set_value", "gt_get_string"]),
    "gt_set_value": _f(_ID_ES + "- `value`: el valor nuevo, como en `gt_get_value`.\n\nNo manda evento.\n",
                       _ID_EN + "- `value`: the new value, as in `gt_get_value`.\n\nIt sends no event.\n", ["gt_get_value"]),
    "gt_get_string": _f(_ID_ES + "\nDevuelve el texto de un `gt_string`.\n", _ID_EN + "\nReturns the text of a `gt_string`.\n",
                        ["gt_set_text"]),
    "gt_set_text": _f(_ID_ES + "- `text`: el texto nuevo.\n\nCambia lo que enseña un `gt_text` o un `gt_string`.\n",
                      _ID_EN + "- `text`: the new text.\n\nChanges what a `gt_text` or a `gt_string` shows.\n",
                      ["gt_get_string"]),
    "gt_enable": _f(_ID_ES + "\nVuelve a dejar usar un gadget desactivado.\n", _ID_EN + "\nLets a disabled gadget be used again.\n",
                    ["gt_disable"]),
    "gt_disable": _f(_ID_ES + "\nLo desactiva: se ve en gris y no responde.\n", _ID_EN + "\nDisables it: it shows grey and does not respond.\n",
                     ["gt_enable"]),
    "gt_event": _f("""\
Mira, sin esperar, si se usó un gadget. Devuelve su número, -1 si no hay nada o -2 si se pulsó el botón de
cerrar. Los eventos de menú los deja para `menu_event`.
""", """\
Looks, without waiting, whether a gadget was used. Returns its number, -1 if there is nothing or -2 if the close
button was pressed. It leaves menu events for `menu_event`.
""", ["gt_wait_event", "menu_event"]),
    "gt_wait_event": _f("""\
Espera, sin gastar CPU, a que se use un gadget y devuelve su número, o -2 si se pulsó el botón de cerrar.
""", """\
Waits, using no CPU, for a gadget to be used and returns its number, or -2 if the close button was pressed.
""", ["gt_event"]),
    # ------------------------------------------------------------ menús
    "menu_title": _f("- `label`: el título en la barra.\n\nEmpieza un menú nuevo; las opciones que siguen van en él.\n",
                     "- `label`: the title on the bar.\n\nStarts a new menu; the items that follow go in it.\n",
                     ["menu_item", "menu_attach"]),
    "menu_item": _f(_M_ES + "\nAñade una opción al último menú.\n", _M_EN + "\nAdds an item to the last menu.\n",
                    ["menu_sub", "menu_check_item", "menu_separator"]),
    "menu_sub": _f(_M_ES + "\nAñade una opción a un submenú de la última opción: esa opción pasa a abrir el submenú.\n",
                   _M_EN + "\nAdds an item to a submenu of the last item: that item now opens the submenu.\n",
                   ["menu_item"]),
    "menu_separator": _f("Añade una raya entre opciones.\n", "Adds a line between items.\n", ["menu_item"]),
    "menu_check_item": _f(_M_ES + "\nAñade una opción con marca: cada vez que se elige, la marca se pone o se quita. `menu_checked` la lee.\n",
                          _M_EN + "\nAdds an item with a check mark: each time it is chosen the mark toggles. `menu_checked` reads it.\n",
                          ["menu_checked"]),
    "menu_attach": _f("""\
Pone en la ventana los menús descritos. Va después de `gt_init` y del último `menu_*`. Otro `menu_attach`
reemplaza los menús. Devuelve `false` si no se pudo.
""", """\
Puts the described menus on the window. It goes after `gt_init` and the last `menu_*`. Another `menu_attach`
replaces the menus. Returns `false` if it could not.
""", ["menu_title", "menu_event"]),
    "menu_event": _f("""\
Mira, sin esperar, si se eligió una opción. Devuelve su número, -1 si no hay nada o -2 si se pulsó el botón de
cerrar. Si se eligieron varias de una vez, salen una a una.
""", """\
Looks, without waiting, whether an item was chosen. Returns its number, -1 if there is nothing or -2 if the close
button was pressed. If several were chosen at once, they come one by one.
""", ["menu_id", "gt_event"]),
    "menu_id": _f("Dentro del `On Menu` de un `EventLoop`, devuelve el número de la opción elegida.\n",
                  "Inside an `EventLoop`'s `On Menu`, returns the number of the chosen item.\n", ["menu_event"]),
    "menu_checked": _f("- `id`: el número de la opción.\n\nDevuelve 1 si tiene la marca puesta, si no 0.\n",
                       "- `id`: the item's number.\n\nReturns 1 if its mark is set, otherwise 0.\n", ["menu_check_item"]),
    "menu_enable": _f("""\
- `id`: el número de la opción.
- `enabled`: `false` la desactiva (en gris), `true` la activa.

Va después de `menu_attach`.
""", """\
- `id`: the item's number.
- `enabled`: `false` disables it (grey), `true` enables it.

It goes after `menu_attach`.
""", ["menu_attach"]),
}
