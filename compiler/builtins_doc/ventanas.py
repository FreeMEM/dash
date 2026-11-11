"""Ventanas, gadgets y peticiones (INTUITION_EXPANDED)."""

GROUPS = {
    "INTUITION_EXPANDED": {
        "es": """\
Ventanas abiertas desde el código, sus gadgets y las peticiones del sistema (fichero, color, fuente, modo de
pantalla).

**Dos formas de tener ventanas.** Con `Window X ... end` se declara una ventana y se abre con `X.open` (ver el
manual, sección 12). Con `window_create` se abre desde el código, sin declararla, y se le pueden abrir varias. Las
dos se pueden mezclar. El `EventLoop` necesita una ventana declarada y abierta; atiende también las de
`window_create`, y `event_window()` dice de cuál vino cada evento.

**Los números de ventana.** `window_create` devuelve un número del 1 al 16, o 0 si no pudo abrirla. Las demás
funciones `window_*` reciben ese número; el 0 es la ventana actual, la última abierta o la elegida con
`window_use`. Un número que no es una ventana abierta no hace nada. Las ventanas que sigan abiertas se cierran
solas al acabar el programa.

**Los gadgets.** Botones, campos de texto, casillas, deslizadores, listas... son gadgets de GadTools. Cada
`*_create` recibe primero la ventana (el número de `window_create`, o 0 para la actual) y devuelve el número del
gadget, del 1 al 64, o 0 si no se pudo crear. Lo demás:

- `x`, `y` cuentan desde la esquina de dentro de los bordes, como los `gfx_*`.
- Con ancho o alto 0, Dash los mide con la fuente de la pantalla: el texto del botón, la opción más larga, diez
  letras en un campo.
- Una `_` en el texto subraya la letra siguiente, que hace de tecla: `"_Aceptar"` se pulsa también con la A.
- Al usarlos, el `EventLoop` recibe `On Gadget` y `gadget_id()` dice cuál fue.

**Medir para cualquier fuente.** La fuente de la pantalla puede ser de 8 puntos o de 13. `screen_font_height` y
`screen_font_text_width` miden con ella; con el flag 8 de `window_create` el tamaño es el del interior, así que no
hace falta contar los bordes.

**Programas más grandes.** Para muchas ventanas o ventanas que cambian de tamaño solas, MUI es más cómodo (ver el
grupo MUI). Los `gt_*` (GadTools) son de una sola ventana.
""",
        "en": """\
Windows opened from code, their gadgets, and the system requesters (file, colour, font, screen mode).

**Two ways to have windows.** `Window X ... end` declares a window and `X.open` opens it (see the manual, section
12). `window_create` opens one from code, without declaring it, and you can open several. The two can be mixed. The `EventLoop` needs a declared, open window; it also serves the `window_create` ones, and
`event_window()` says which one each event came from.

**Window numbers.** `window_create` returns a number from 1 to 16, or 0 if it could not open the window. The other
`window_*` functions take that number; 0 is the current window, the one opened last or chosen with `window_use`. A
number that is not an open window does nothing. Windows still open close on their own when the program ends.

**Gadgets.** Buttons, text fields, checkboxes, sliders, lists... are GadTools gadgets. Each `*_create` takes the
window first (the number from `window_create`, or 0 for the current one) and returns the gadget's number, from 1 to
64, or 0 if it could not be created. Also:

- `x`, `y` count from the corner inside the borders, like the `gfx_*` functions.
- With width or height 0, Dash measures them with the screen's font: the button's text, the longest option, ten
  letters for a field.
- A `_` in the text underlines the next letter, which works as a key: `"_Accept"` is also pressed with A.
- When they are used, the `EventLoop` gets `On Gadget` and `gadget_id()` says which one.

**Measuring for any font.** The screen's font can be 8 points or 13. `screen_font_height` and
`screen_font_text_width` measure with it; with flag 8 of `window_create` the size is the inside one, so there is no
need to count the borders.

**Bigger programs.** For many windows, or windows that resize on their own, MUI is easier (see the MUI group). The
`gt_*` functions (GadTools) are for a single window.
""",
        "example": "tests/test_doc_ventanas.dash",
    },
}

FUNCS = {
    "window_create": {
        "es": """\
- `title`: el título. Con `""`, sin flag 1 y con los flags 2 y 4, la ventana no tiene barra de título.
- `x`, `y`: la posición en la pantalla.
- `w`, `h`: el tamaño, 40 x 20 como poco.
- `flags`: se suman. 1 = se puede cambiar de tamaño; 2 = sin bordes; 4 = sin botón de cerrar; 8 = `w` y `h` son
  el interior, sin los bordes; 16 = el botón derecho va al programa (`On RightClick`) en vez de a los menús.

Abre la ventana en la pantalla del programa, si se abrió una, o en el Workbench. Devuelve su número (1 a 16) y la
hace la ventana actual: los `gfx_*` dibujan en ella. Devuelve 0 si no se pudo abrir o si ya hay 16.
""",
        "en": """\
- `title`: the title. With `""`, no flag 1 and flags 2 and 4, the window has no title bar.
- `x`, `y`: the position on the screen.
- `w`, `h`: the size, at least 40 x 20.
- `flags`: they add up. 1 = resizable; 2 = borderless; 4 = no close button; 8 = `w` and `h` are the inside, without
  the borders; 16 = the right button goes to the program (`On RightClick`) instead of the menus.

Opens the window on the program's screen, if one was opened, or on the Workbench. Returns its number (1 to 16) and
makes it the current window: the `gfx_*` functions draw in it. Returns 0 if it could not be opened or if there are
already 16.
""",
        "see": ["window_close", "window_use", "screen_font_height", "event_window"],
    },
    "window_border_top": {
        "es": """\
Devuelve el grosor del borde de arriba de la ventana actual, con la barra de título, en píxeles; 0 sin ventana.
Depende de la fuente de la pantalla. Hace falta para calcular el tamaño de fuera de una ventana; con el flag 8 de
`window_create` no.
""",
        "en": """\
Returns the thickness of the current window's top border, title bar included, in pixels; 0 without a window. It
depends on the screen's font. You need it to work out a window's outer size; with flag 8 of `window_create` you
do not.
""",
        "see": ["window_border_bottom", "window_border_left", "window_border_right", "window_create"],
    },
    "window_border_bottom": {
        "es": "Devuelve el grosor del borde de abajo de la ventana actual, en píxeles; 0 sin ventana.\n",
        "en": "Returns the thickness of the current window's bottom border, in pixels; 0 without a window.\n",
        "see": ["window_border_top"],
    },
    "window_border_left": {
        "es": "Devuelve el grosor del borde izquierdo de la ventana actual, en píxeles; 0 sin ventana.\n",
        "en": "Returns the thickness of the current window's left border, in pixels; 0 without a window.\n",
        "see": ["window_border_top"],
    },
    "window_border_right": {
        "es": "Devuelve el grosor del borde derecho de la ventana actual, en píxeles; 0 sin ventana.\n",
        "en": "Returns the thickness of the current window's right border, in pixels; 0 without a window.\n",
        "see": ["window_border_top"],
    },
    "screen_font_height": {
        "es": """\
Devuelve el alto en píxeles de la fuente de la pantalla: la del programa, la de la ventana actual o, sin ninguna,
la del Workbench. Es la fuente de las barras de título y de los gadgets. Una fila de gadgets cómoda mide
`screen_font_height() + 6`.
""",
        "en": """\
Returns the height in pixels of the screen's font: the program's screen, the current window's or, with neither,
the Workbench's. It is the font of title bars and gadgets. A comfortable row of gadgets is
`screen_font_height() + 6` high.
""",
        "see": ["screen_font_text_width", "window_create"],
    },
    "screen_font_text_width": {
        "es": """\
- `text`: el texto.

Devuelve cuántos píxeles de ancho ocupa el texto con la fuente de la pantalla. Sirve para dar a una ventana o a
una columna de etiquetas el ancho justo.
""",
        "en": """\
- `text`: the text.

Returns how many pixels wide the text is in the screen's font. Useful to give a window or a column of labels just
the right width.
""",
        "see": ["screen_font_height", "gfx_text_len"],
    },
    "window_close": {
        "es": """\
- `handle`: el número de la ventana; 0, la actual.

Cierra la ventana. Si era la actual, no queda ventana actual: antes de dibujar otra vez, `window_use`. Sus gadgets
dejan de dibujarse. Cerrar una que ya está cerrada no hace nada.
""",
        "en": """\
- `handle`: the window's number; 0, the current one.

Closes the window. If it was the current one, there is no current window left: call `window_use` before drawing
again. Its gadgets stop being drawn. Closing one that is already closed does nothing.
""",
        "see": ["window_create", "window_use", "close_window"],
    },
    "window_title": {
        "es": """\
- `handle`: el número de la ventana; 0, la actual.
- `title`: el título nuevo.

Cambia el texto de la barra de título. Para enseñar un estado: el nombre del fichero, un `*` si hay cambios.
""",
        "en": """\
- `handle`: the window's number; 0, the current one.
- `title`: the new title.

Changes the text of the title bar. Handy to show a state: the file's name, a `*` when there are changes.
""",
        "see": ["window_create"],
    },
    "window_move": {
        "es": """\
- `handle`: el número de la ventana; 0, la actual.
- `x`, `y`: la posición nueva en la pantalla (no un desplazamiento).

Lleva la ventana a ese sitio. Intuition lo hace un momento después, no al volver de la llamada. Un
`window_resize` justo después cuenta ya con la posición nueva.
""",
        "en": """\
- `handle`: the window's number; 0, the current one.
- `x`, `y`: the new position on the screen (not an offset).

Moves the window there. Intuition does it a moment later, not when the call returns. A `window_resize` right after
already counts with the new position.
""",
        "see": ["window_resize", "window_create"],
    },
    "window_resize": {
        "es": """\
- `handle`: el número de la ventana; 0, la actual.
- `w`, `h`: el tamaño nuevo, de fuera (con los bordes).

Cambia el tamaño de la ventana. Como `window_move`, Intuition lo hace un momento después.
""",
        "en": """\
- `handle`: the window's number; 0, the current one.
- `w`, `h`: the new outer size (with the borders).

Changes the window's size. Like `window_move`, Intuition does it a moment later.
""",
        "see": ["window_move", "window_border_top"],
    },
    "window_to_front": {
        "es": "- `handle`: el número de la ventana; 0, la actual.\n\nPone la ventana delante de las demás de su pantalla.\n",
        "en": "- `handle`: the window's number; 0, the current one.\n\nPuts the window in front of the others on its screen.\n",
        "see": ["window_to_back", "window_activate"],
    },
    "window_to_back": {
        "es": "- `handle`: el número de la ventana; 0, la actual.\n\nPone la ventana detrás de las demás de su pantalla (delante de las de fondo y de la barra de título). Si ya está detrás, no hace nada: se puede llamar en cada vuelta para que una ventana se quede siempre atrás.\n",
        "en": "- `handle`: the window's number; 0, the current one.\n\nPuts the window behind the others on its screen (in front of the backdrop ones and of the title bar). If it already is, it does nothing: it can be called every tick to keep a window at the back.\n",
        "see": ["window_to_front"],
    },
    "window_activate": {
        "es": """\
- `handle`: el número de la ventana; 0, la actual.

La hace la ventana activa, la que recibe el teclado. No la pone delante: para eso, `window_to_front`.
""",
        "en": """\
- `handle`: the window's number; 0, the current one.

Makes it the active window, the one that gets the keyboard. It does not bring it to the front: for that,
`window_to_front`.
""",
        "see": ["window_to_front"],
    },
    "window_use": {
        "es": """\
- `handle`: el número de una ventana de `window_create`, o 0 para la ventana declarada (`Window X ... end`) abierta
  la última.

La hace la ventana actual: los `gfx_*` dibujan en ella y el número 0 de las demás funciones es ella. Devuelve
`false` si esa ventana no está abierta, y entonces no cambia nada.
""",
        "en": """\
- `handle`: the number of a `window_create` window, or 0 for the declared window (`Window X ... end`) opened last.

Makes it the current window: the `gfx_*` functions draw in it and number 0 of the other functions is this one.
Returns `false` if that window is not open, and then nothing changes.
""",
        "see": ["window_create", "gfx_pen"],
    },
    "screen_to_front": {
        "es": "Pone delante la pantalla del programa (la de `screen_open`). Sin pantalla propia no hace nada.\n",
        "en": "Brings the program's screen (the `screen_open` one) to the front. Without a screen of its own it does nothing.\n",
        "see": ["screen_to_back", "screen_open"],
    },
    "screen_to_back": {
        "es": "Pone detrás la pantalla del programa, y se ve la de debajo (el Workbench). Sin pantalla propia no hace nada.\n",
        "en": "Sends the program's screen to the back, showing the one below (the Workbench). Without a screen of its own it does nothing.\n",
        "see": ["screen_to_front"],
    },
    "gadget_id": {
        "es": """\
Devuelve el número del último gadget usado. Se mira en el `On Gadget` del `EventLoop` y se compara con lo que
devolvió su `*_create`.
""",
        "en": """\
Returns the number of the last gadget used. Check it in the `EventLoop`'s `On Gadget` and compare it with what its
`*_create` returned.
""",
        "see": ["button_create", "event_window"],
    },
    "gadget_width": {
        "es": """\
- `gadget`: el número del gadget.

Devuelve su ancho en píxeles, también cuando se creó con ancho 0 y lo midió Dash. 0 si no es un gadget.
""",
        "en": """\
- `gadget`: the gadget's number.

Returns its width in pixels, also when it was created with width 0 and Dash measured it. 0 if it is not a gadget.
""",
        "see": ["gadget_height"],
    },
    "gadget_height": {
        "es": """\
- `gadget`: el número del gadget.

Devuelve su alto en píxeles, también cuando se creó con alto 0. 0 si no es un gadget.
""",
        "en": """\
- `gadget`: the gadget's number.

Returns its height in pixels, also when it was created with height 0. 0 if it is not a gadget.
""",
        "see": ["gadget_width"],
    },
    "button_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`: la esquina de arriba a la izquierda.
- `w`, `h`: el tamaño; 0 lo mide Dash con el texto.
- `label`: el texto; una `_` subraya la letra que lo pulsa con el teclado.

Crea un botón. Al pulsarlo llega `On Gadget` con `gadget_id()` igual al número que devuelve. Devuelve 0 si no se
pudo crear.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`: the top left corner.
- `w`, `h`: the size; 0 lets Dash measure it from the text.
- `label`: the text; a `_` underlines the letter that presses it from the keyboard.

Creates a button. Pressing it sends `On Gadget` with `gadget_id()` equal to the number it returns. Returns 0 if it
could not be created.
""",
        "see": ["button_disable", "gadget_id"],
    },
    "button_enable": {
        "es": "- `gad`: el número del gadget.\n\nVuelve a dejar usar un gadget desactivado. Vale para cualquier gadget, no solo botones.\n",
        "en": "- `gad`: the gadget's number.\n\nLets a disabled gadget be used again. It works for any gadget, not only buttons.\n",
        "see": ["button_disable"],
    },
    "button_disable": {
        "es": """\
- `gad`: el número del gadget.

Desactiva el gadget: se ve en gris y no responde al ratón ni a su tecla. Vale para cualquier gadget.
""",
        "en": """\
- `gad`: the gadget's number.

Disables the gadget: it shows in grey and does not respond to the mouse or its key. It works for any gadget.
""",
        "see": ["button_enable"],
    },
    "textfield_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño; 0 lo mide Dash (diez letras de ancho).
- `maxlen`: cuántas letras caben como mucho; 0 = 64.

Crea un campo de texto. Lleva las teclas de edición del sistema y las de copiar y pegar. `On Gadget` llega al
pulsar Return o Tab.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size; 0 lets Dash measure it (ten letters wide).
- `maxlen`: the most letters it holds; 0 = 64.

Creates a text field. It has the system's editing keys and copy and paste. `On Gadget` arrives when Return or Tab
is pressed.
""",
        "see": ["textfield_get", "textfield_set", "integer_create"],
    },
    "textfield_get": {
        "es": "- `gad`: el número del campo.\n\nDevuelve lo que hay escrito, también si aún no se pulsó Return. `\"\"` si no es un campo.\n",
        "en": "- `gad`: the field's number.\n\nReturns what is typed, even if Return was not pressed yet. `\"\"` if it is not a field.\n",
        "see": ["textfield_set"],
    },
    "textfield_set": {
        "es": "- `gad`: el número del campo.\n- `text`: el texto nuevo.\n\nCambia lo que enseña el campo.\n",
        "en": "- `gad`: the field's number.\n- `text`: the new text.\n\nChanges what the field shows.\n",
        "see": ["textfield_get"],
    },
    "checkbox_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`: dónde va la casilla; el texto va a su derecha.
- `label`: el texto; una `_` subraya su tecla.

Crea una casilla sin marcar. Cada clic, o su tecla, la marca o la desmarca y manda `On Gadget`.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`: where the box goes; the text goes to its right.
- `label`: the text; a `_` underlines its key.

Creates an unticked checkbox. Each click, or its key, ticks or unticks it and sends `On Gadget`.
""",
        "see": ["checkbox_get", "checkbox_set"],
    },
    "checkbox_get": {
        "es": "- `gad`: el número de la casilla.\n\nDevuelve `true` si está marcada.\n",
        "en": "- `gad`: the checkbox's number.\n\nReturns `true` if it is ticked.\n",
        "see": ["checkbox_set"],
    },
    "checkbox_set": {
        "es": "- `gad`: el número de la casilla.\n- `state`: `true` la marca, `false` la desmarca.\n\nNo manda `On Gadget`.\n",
        "en": "- `gad`: the checkbox's number.\n- `state`: `true` ticks it, `false` unticks it.\n\nIt does not send `On Gadget`.\n",
        "see": ["checkbox_get"],
    },
    "slider_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño. Más ancho que alto es horizontal.
- `min`, `max`: el valor del principio y el del final.
- `value`: el valor con el que empieza; si se sale, se queda en `min` o `max`.

Crea un deslizador. Manda `On Gadget` mientras se arrastra, no solo al soltarlo.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size. Wider than tall is horizontal.
- `min`, `max`: the value at the start and at the end.
- `value`: the starting value; out of range, it stays at `min` or `max`.

Creates a slider. It sends `On Gadget` while it is dragged, not only when it is let go.
""",
        "see": ["slider_get", "slider_set"],
    },
    "slider_get": {
        "es": "- `gad`: el número del deslizador.\n\nDevuelve su valor, entre `min` y `max`.\n",
        "en": "- `gad`: the slider's number.\n\nReturns its value, between `min` and `max`.\n",
        "see": ["slider_set"],
    },
    "slider_set": {
        "es": "- `gad`: el número del deslizador.\n- `value`: el valor nuevo.\n\nMueve el deslizador. No manda `On Gadget`.\n",
        "en": "- `gad`: the slider's number.\n- `value`: the new value.\n\nMoves the slider. It does not send `On Gadget`.\n",
        "see": ["slider_get"],
    },
    "listview_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.

Crea una lista vacía con su barra para desplazarla. Las líneas se añaden con `listview_add`. Al elegir una llega
`On Gadget`.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size.

Creates an empty list with its scroll bar. Lines are added with `listview_add`. Choosing one sends `On Gadget`.
""",
        "see": ["listview_add", "listview_selected", "listview_clear"],
    },
    "listview_add": {
        "es": "- `gad`: el número de la lista.\n- `text`: la línea.\n\nAñade una línea al final. La lista guarda su propia copia del texto.\n",
        "en": "- `gad`: the list's number.\n- `text`: the line.\n\nAdds a line at the end. The list keeps its own copy of the text.\n",
        "see": ["listview_clear"],
    },
    "listview_clear": {
        "es": "- `gad`: el número de la lista.\n\nQuita todas las líneas y deja la lista sin ninguna elegida.\n",
        "en": "- `gad`: the list's number.\n\nRemoves every line and leaves no line chosen.\n",
        "see": ["listview_add"],
    },
    "listview_selected": {
        "es": "- `gad`: el número de la lista.\n\nDevuelve la línea elegida, contando desde 0, o -1 si no hay ninguna.\n",
        "en": "- `gad`: the list's number.\n\nReturns the chosen line, counting from 0, or -1 if there is none.\n",
        "see": ["listview_create"],
    },
    "cycle_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño; 0 lo mide Dash con la opción más larga.
- `options`: las opciones separadas por `|`: `"Baja|Media|Alta"`.

Crea un gadget que enseña una opción y pasa a la siguiente con cada clic. Empieza en la primera, la 0. Manda
`On Gadget` al cambiar.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size; 0 lets Dash measure it from the longest option.
- `options`: the options separated by `|`: `"Low|Medium|High"`.

Creates a gadget that shows one option and moves to the next with each click. It starts at the first, 0. It sends
`On Gadget` when it changes.
""",
        "see": ["cycle_get", "cycle_set", "radio_create"],
    },
    "cycle_get": {
        "es": "- `gad`: el número del gadget.\n\nDevuelve la opción elegida, desde 0. -1 si no es un gadget de opciones.\n",
        "en": "- `gad`: the gadget's number.\n\nReturns the chosen option, from 0. -1 if it is not a cycle gadget.\n",
        "see": ["cycle_set"],
    },
    "cycle_set": {
        "es": "- `gad`: el número del gadget.\n- `index`: la opción, desde 0.\n\nElige esa opción. No manda `On Gadget`.\n",
        "en": "- `gad`: the gadget's number.\n- `index`: the option, from 0.\n\nChooses that option. It does not send `On Gadget`.\n",
        "see": ["cycle_get"],
    },
    "radio_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`: dónde va el primer botón; los demás van debajo, con su texto a la derecha.
- `options`: las opciones separadas por `|`.

Crea un grupo de botones de radio, de los que solo uno está elegido. Empieza en el primero, el 0. Manda
`On Gadget` al cambiar.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`: where the first button goes; the others go below, with their text to the right.
- `options`: the options separated by `|`.

Creates a group of radio buttons, only one of them chosen. It starts at the first, 0. It sends `On Gadget` when it
changes.
""",
        "see": ["radio_get", "radio_set", "cycle_create"],
    },
    "radio_get": {
        "es": "- `gad`: el número del grupo.\n\nDevuelve el botón elegido, desde 0. -1 si no es un grupo de radio.\n",
        "en": "- `gad`: the group's number.\n\nReturns the chosen button, from 0. -1 if it is not a radio group.\n",
        "see": ["radio_set"],
    },
    "radio_set": {
        "es": "- `gad`: el número del grupo.\n- `index`: el botón, desde 0.\n\nElige ese botón. No manda `On Gadget`.\n",
        "en": "- `gad`: the group's number.\n- `index`: the button, from 0.\n\nChooses that button. It does not send `On Gadget`.\n",
        "see": ["radio_get"],
    },
    "integer_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `value`: el número con el que empieza.

Crea un campo que solo admite números enteros, de hasta 10 cifras. `On Gadget` llega al pulsar Return o Tab.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size.
- `value`: the starting number.

Creates a field that only takes whole numbers, up to 10 digits. `On Gadget` arrives when Return or Tab is pressed.
""",
        "see": ["integer_get", "integer_set", "textfield_create"],
    },
    "integer_get": {
        "es": "- `gad`: el número del campo.\n\nDevuelve el número escrito, también si aún no se pulsó Return. -1 si no es un campo de números.\n",
        "en": "- `gad`: the field's number.\n\nReturns the number typed, even if Return was not pressed yet. -1 if it is not a number field.\n",
        "see": ["integer_set"],
    },
    "integer_set": {
        "es": "- `gad`: el número del campo.\n- `value`: el número nuevo.\n\nCambia el número que enseña.\n",
        "en": "- `gad`: the field's number.\n- `value`: the new number.\n\nChanges the number it shows.\n",
        "see": ["integer_get"],
    },
    "palette_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `depth`: cuántos colores enseña: 2 elevado a `depth` (3 = 8 colores); 0 = 4 colores.

Crea un gadget con los colores de la pantalla para elegir uno. Empieza en el color 1. Manda `On Gadget` al elegir.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size.
- `depth`: how many colours it shows: 2 to the power of `depth` (3 = 8 colours); 0 = 4 colours.

Creates a gadget with the screen's colours to pick one. It starts at colour 1. It sends `On Gadget` on a pick.
""",
        "see": ["palette_get", "palette_set", "dialog_color"],
    },
    "palette_get": {
        "es": "- `gad`: el número del gadget.\n\nDevuelve el color elegido. -1 si no es un gadget de paleta.\n",
        "en": "- `gad`: the gadget's number.\n\nReturns the chosen colour. -1 if it is not a palette gadget.\n",
        "see": ["palette_set"],
    },
    "palette_set": {
        "es": "- `gad`: el número del gadget.\n- `color`: el color.\n\nElige ese color. No manda `On Gadget`.\n",
        "en": "- `gad`: the gadget's number.\n- `color`: the colour.\n\nChooses that colour. It does not send `On Gadget`.\n",
        "see": ["palette_get"],
    },
    "number_create": {
        "es": """\
- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `value`: el número que enseña.

Crea una caja con borde que enseña un número y no se puede editar. Para un contador o un resultado.
""",
        "en": """\
- `win`: the window; 0, the current one.
- `x`, `y`, `w`, `h`: position and size.
- `value`: the number it shows.

Creates a bordered box that shows a number and cannot be edited. For a counter or a result.
""",
        "see": ["number_set"],
    },
    "number_set": {
        "es": "- `gad`: el número del gadget.\n- `value`: el número nuevo.\n\nCambia el número que enseña.\n",
        "en": "- `gad`: the gadget's number.\n- `value`: the new number.\n\nChanges the number it shows.\n",
        "see": ["number_create"],
    },
    "dialog_file": {
        "es": """\
- `title`: el título de la petición.
- `pattern`: qué ficheros se ven, con los comodines de AmigaDOS: `"#?.dash"`; `""` = todos.
- `save_mode`: `true` para guardar (se puede escribir un nombre nuevo), `false` para abrir.

Abre la petición de ficheros del sistema (ASL) y espera. Devuelve la ruta entera del fichero elegido, o `""` si se
canceló. La siguiente vez se abre en el cajón de la última.
""",
        "en": """\
- `title`: the requester's title.
- `pattern`: which files show, with AmigaDOS wildcards: `"#?.dash"`; `""` = all of them.
- `save_mode`: `true` to save (a new name can be typed), `false` to open.

Opens the system's file requester (ASL) and waits. Returns the full path of the chosen file, or `""` if it was
cancelled. Next time it opens in the last drawer.
""",
        "see": ["dialog_file_at", "file_open_dialog"],
    },
    "dialog_file_at": {
        "es": """\
- `title`, `pattern`, `save_mode`: como en `dialog_file`.
- `drawer`: el cajón donde se abre; `""` = el de la última vez.
- `file`: el nombre que sale escrito; `""` = ninguno.

Como `dialog_file`, empezando en ese cajón y con ese nombre. Para "Guardar como..." con el nombre del fichero
abierto.
""",
        "en": """\
- `title`, `pattern`, `save_mode`: as in `dialog_file`.
- `drawer`: the drawer it opens in; `""` = the last one.
- `file`: the name already typed; `""` = none.

Like `dialog_file`, starting in that drawer with that name. For "Save as..." with the open file's name.
""",
        "see": ["dialog_file"],
    },
    "dialog_color": {
        "es": """\
- `title`: el título de la ventana.
- `initial`: el color que sale elegido.

Abre una ventana con los colores de la pantalla y espera. Se elige con un clic, o con las flechas y Return.
Devuelve el color elegido; con Esc o el botón de cerrar, `initial`.
""",
        "en": """\
- `title`: the window's title.
- `initial`: the colour chosen at the start.

Opens a window with the screen's colours and waits. You pick with a click, or with the arrows and Return. Returns
the chosen colour; with Esc or the close button, `initial`.
""",
        "see": ["palette_create"],
    },
    "dialog_screen_mode": {
        "es": """\
- `title`: el título de la petición.

Abre la petición de modo de pantalla del sistema, empezando en el del Workbench, y espera. Devuelve `true` si se
eligió uno: entonces `screen_mode_id`, `screen_mode_width`, `screen_mode_height` y `screen_mode_depth` lo dan, para
`screen_open_mode`. `false` si se canceló.
""",
        "en": """\
- `title`: the requester's title.

Opens the system's screen mode requester, starting at the Workbench's mode, and waits. Returns `true` if one was
chosen: then `screen_mode_id`, `screen_mode_width`, `screen_mode_height` and `screen_mode_depth` give it, for
`screen_open_mode`. `false` if it was cancelled.
""",
        "see": ["screen_mode_id", "screen_open_mode"],
    },
    "screen_mode_id": {
        "es": "Devuelve el modo elegido en el último `dialog_screen_mode`, el número que pide `screen_open_mode`.\n",
        "en": "Returns the mode chosen in the last `dialog_screen_mode`, the number `screen_open_mode` takes.\n",
        "see": ["dialog_screen_mode", "screen_open_mode"],
    },
    "screen_mode_width": {
        "es": "Devuelve el ancho elegido en el último `dialog_screen_mode`.\n",
        "en": "Returns the width chosen in the last `dialog_screen_mode`.\n",
        "see": ["dialog_screen_mode"],
    },
    "screen_mode_height": {
        "es": "Devuelve el alto elegido en el último `dialog_screen_mode`.\n",
        "en": "Returns the height chosen in the last `dialog_screen_mode`.\n",
        "see": ["dialog_screen_mode"],
    },
    "screen_mode_depth": {
        "es": "Devuelve la profundidad elegida en el último `dialog_screen_mode`: 3 son 8 colores, 8 son 256.\n",
        "en": "Returns the depth chosen in the last `dialog_screen_mode`: 3 is 8 colours, 8 is 256.\n",
        "see": ["dialog_screen_mode"],
    },
    "dialog_font": {
        "es": """\
- `title`: el título de la petición.

Abre la petición de fuentes del sistema y espera. Devuelve la fuente elegida como `"nombre.font/tamaño"`
(`"topaz.font/8"`), o `""` si se canceló. Para abrirla, el nombre y el tamaño van por separado en `font_open`.
""",
        "en": """\
- `title`: the requester's title.

Opens the system's font requester and waits. Returns the chosen font as `"name.font/size"` (`"topaz.font/8"`),
or `""` if it was cancelled. To open it, the name and the size go separately to `font_open`.
""",
        "see": ["font_open"],
    },
}
