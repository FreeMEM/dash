"""MUI (MUI_FUNCTIONS), segunda parte: la zona de dibujo, las imágenes, el combo y la barra de desplazamiento."""

GROUPS = {}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_C_ES = "- `canvas`: la zona de dibujo.\n\n"
_C_EN = "- `canvas`: the drawing area.\n\n"

FUNCS = {
    "mui_canvas": _f("""\
- `min_width`, `min_height`: el tamaño mínimo en píxeles; crece con la ventana.

Una zona donde el programa dibuja con los `gfx_*`. No se dibuja en ella cuando se quiere: MUI llama a la función de
`mui_canvas_on_draw` cada vez que hace falta (al abrir, al cambiar de tamaño, al destaparse) y cuando el programa
lo pide con `mui_canvas_redraw`. Para que responda al ratón y al teclado, `mui_canvas_on_input`.
""", """\
- `min_width`, `min_height`: the minimum size in pixels; it grows with the window.

An area where the program draws with the `gfx_*` functions. You do not draw on it whenever you like: MUI calls the
`mui_canvas_on_draw` function each time it is needed (on opening, on resizing, when uncovered) and when the program
asks with `mui_canvas_redraw`. To respond to the mouse and the keyboard, `mui_canvas_on_input`.
""", ["mui_canvas_on_draw", "mui_canvas_redraw", "mui_canvas_on_input"]),
    "mui_canvas_on_draw": _f("""\
- `canvas`: la zona de dibujo.
- `func`: una función `f(x: Int, y: Int, ancho: Int, alto: Int)`.

La función que dibuja la zona. `x`, `y` es la esquina de la zona dentro de la ventana y `ancho`, `alto` su tamaño
ahora: se dibuja de `x` a `x + ancho - 1`. Lo que se salga queda recortado. Dentro, los `gfx_*` dibujan en la zona.
""", """\
- `canvas`: the drawing area.
- `func`: a function `f(x: Int, y: Int, width: Int, height: Int)`.

The function that draws the area. `x`, `y` is the area's corner inside the window and `width`, `height` its current
size: you draw from `x` to `x + width - 1`. What goes outside is clipped. Inside it, the `gfx_*` functions draw on
the area.
""", ["mui_canvas", "mui_canvas_redraw", "mui_canvas_updating"]),
    "mui_canvas_redraw": _f(_C_ES + """\
Pide a MUI que la borre y la vuelva a dibujar ya, llamando a su función. Se llama desde el programa principal,
nunca desde otra tarea.
""", _C_EN + """\
Asks MUI to clear it and draw it again now, calling its function. Call it from the main program, never from another
task.
""", ["mui_canvas_update", "mui_canvas_on_draw"]),
    "mui_canvas_update": _f(_C_ES + """\
Llama a la función de dibujo sin borrar la zona antes: dentro, `mui_canvas_updating()` es `true` y basta pintar lo
que cambió. Más rápido que `mui_canvas_redraw` para un cursor o un contador.
""", _C_EN + """\
Calls the drawing function without clearing the area first: inside, `mui_canvas_updating()` is `true` and painting
what changed is enough. Faster than `mui_canvas_redraw` for a cursor or a counter.
""", ["mui_canvas_updating", "mui_canvas_update_area"]),
    "mui_canvas_update_area": _f("""\
- `canvas`: la zona de dibujo.
- `x`, `y`, `w`, `h`: la parte que se repinta, contando desde la esquina de la zona.

Como `mui_canvas_update`, pero el dibujo se recorta a esa parte. Con `mui_canvas_buffered`, solo esa parte pasa a
la ventana.
""", """\
- `canvas`: the drawing area.
- `x`, `y`, `w`, `h`: the part to repaint, counting from the area's corner.

Like `mui_canvas_update`, but drawing is clipped to that part. With `mui_canvas_buffered`, only that part goes to
the window.
""", ["mui_canvas_update"]),
    "mui_canvas_updating": _f("""\
Dentro de la función de dibujo, devuelve `true` si la llamó `mui_canvas_update` (lo de antes sigue en la zona) y
`false` si hay que dibujarla entera.
""", """\
Inside the drawing function, returns `true` if `mui_canvas_update` called it (the old picture is still on the area)
and `false` if it has to be drawn whole.
""", ["mui_canvas_update"]),
    "mui_canvas_buffered": _f("""\
- `canvas`: la zona de dibujo.
- `on`: `true` lo enciende.

La zona se dibuja en una imagen aparte y se enseña de golpe al acabar la función: no se ve a medio dibujar. Las
coordenadas son las mismas. Gasta la memoria de una imagen del tamaño de la zona.
""", """\
- `canvas`: the drawing area.
- `on`: `true` turns it on.

The area is drawn on a separate picture and shown at once when the function ends: it is never seen half drawn. The
coordinates are the same. It uses the memory of a picture the size of the area.
""", ["mui_canvas_update_area"]),
    "mui_canvas_on_input": _f("""\
- `canvas`: la zona de dibujo.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` con un clic, la rueda del ratón o una tecla sobre la zona. Después,
`mui_canvas_button`, `mui_canvas_wheel` o `mui_canvas_key` dicen qué fue, y `mui_canvas_mouse_x`, `_y` dónde. Se
llama antes de abrir la ventana.
""", """\
- `canvas`: the drawing area.
- `id`: the event number.

`mui_wait_event` returns `id` on a click, the mouse wheel or a key over the area. Then `mui_canvas_button`,
`mui_canvas_wheel` or `mui_canvas_key` say what it was, and `mui_canvas_mouse_x`, `_y` where. Call it before
opening the window.
""", ["mui_canvas_button", "mui_canvas_key", "mui_canvas_mouse_x"]),
    "mui_canvas_on_move": _f("""\
- `canvas`: la zona de dibujo.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` cuando el puntero se mueve sobre la zona, o sale de ella, sin pulsar. Si llegan
varios movimientos mientras el programa está ocupado, cuentan como uno. Se llama antes de abrir la ventana.
""", """\
- `canvas`: the drawing area.
- `id`: the event number.

`mui_wait_event` returns `id` when the pointer moves over the area, or leaves it, without a click. Several moves
arriving while the program is busy count as one. Call it before opening the window.
""", ["mui_canvas_pointer_x", "mui_canvas_pointer_inside"]),
    "mui_canvas_on_drag": _f("""\
- `canvas`: la zona de dibujo.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` mientras se arrastra (se pulsa en la zona y se mueve con el botón pulsado) y al
soltar. `mui_canvas_drag` dice cuál de los dos y `mui_canvas_mouse_x`, `_y` dónde, aunque sea fuera de la zona. Se
llama antes de abrir la ventana.
""", """\
- `canvas`: the drawing area.
- `id`: the event number.

`mui_wait_event` returns `id` while dragging (pressing on the area and moving with the button held) and on release.
`mui_canvas_drag` says which and `mui_canvas_mouse_x`, `_y` where, even outside the area. Call it before opening the
window.
""", ["mui_canvas_drag"]),
    "mui_canvas_drag": _f(_C_ES + """\
Devuelve el último evento de arrastre: 1 moviéndose con el botón pulsado, 2 al soltarlo, 0 antes de ninguno.
""", _C_EN + """\
Returns the last drag event: 1 moving with the button held, 2 on release, 0 before any.
""", ["mui_canvas_on_drag"]),
    "mui_canvas_mouse_x": _f(_C_ES + """\
Devuelve la X del último clic, rueda o arrastre, contando desde el borde izquierdo de la zona.
""", _C_EN + """\
Returns the X of the last click, wheel or drag, counting from the area's left edge.
""", ["mui_canvas_mouse_y", "mui_canvas_pointer_x"]),
    "mui_canvas_mouse_y": _f(_C_ES + """\
Devuelve la Y del último clic, rueda o arrastre, contando desde el borde de arriba de la zona.
""", _C_EN + """\
Returns the Y of the last click, wheel or drag, counting from the area's top edge.
""", ["mui_canvas_mouse_x"]),
    "mui_canvas_button": _f(_C_ES + """\
Devuelve 1 si lo último fue un clic izquierdo, 2 si fue el derecho con un menú contextual y 0 si no fue un clic.
""", _C_EN + """\
Returns 1 if the last thing was a left click, 2 if it was the right one with a context menu, and 0 if it was not a
click.
""", ["mui_canvas_on_input"]),
    "mui_canvas_wheel": _f(_C_ES + """\
Devuelve 1 si lo último fue la rueda del ratón hacia arriba, -1 hacia abajo y 0 si no fue la rueda.
""", _C_EN + """\
Returns 1 if the last thing was the mouse wheel upwards, -1 downwards, and 0 if it was not the wheel.
""", ["mui_canvas_on_input"]),
    "mui_canvas_key": _f(_C_ES + """\
Devuelve el código en bruto de la última tecla pulsada sobre la zona, o -1 si lo último no fue una tecla.
`mui_canvas_char` da la letra.
""", _C_EN + """\
Returns the raw code of the last key pressed over the area, or -1 if the last thing was not a key.
`mui_canvas_char` gives the letter.
""", ["mui_canvas_char", "mui_canvas_qualifiers"]),
    "mui_canvas_char": _f(_C_ES + """\
Devuelve el carácter de la última tecla, con Mayúsculas y el mapa de teclado puestos (`"A"`, `"ñ"`); `""` si la
tecla no da ninguno.
""", _C_EN + """\
Returns the character of the last key, with Shift and the keymap applied (`"A"`, `"ñ"`); `""` if the key gives
none.
""", ["mui_canvas_key"]),
    "mui_canvas_qualifiers": _f(_C_ES + """\
Devuelve las teclas que estaban pulsadas en la última tecla, clic o rueda, sumadas: 1 Mayúsculas, 2 Ctrl, 4 Alt,
8 Amiga. `q & 2` dice si había Ctrl.
""", _C_EN + """\
Returns the keys that were held during the last key, click or wheel, added up: 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga.
`q & 2` tells whether Ctrl was held.
""", ["mui_canvas_key"]),
    "mui_canvas_pointer_x": _f(_C_ES + """\
Devuelve la X del puntero ahora mismo, desde el borde izquierdo de la zona, haya clic o no.
""", _C_EN + """\
Returns the pointer's X right now, from the area's left edge, with or without a click.
""", ["mui_canvas_pointer_y", "mui_canvas_on_move"]),
    "mui_canvas_pointer_y": _f(_C_ES + "Devuelve la Y del puntero ahora mismo, desde el borde de arriba de la zona.\n",
                               _C_EN + "Returns the pointer's Y right now, from the area's top edge.\n",
                               ["mui_canvas_pointer_x"]),
    "mui_canvas_pointer_inside": _f(_C_ES + "Devuelve `true` si el puntero está ahora sobre la zona.\n",
                                    _C_EN + "Returns `true` if the pointer is over the area now.\n",
                                    ["mui_canvas_on_move"]),
    "mui_canvas_set_pointer": _f("""\
- `canvas`: la zona de dibujo.
- `shape`: 0 normal, 1 texto (una I), 2 cambiar de tamaño a los lados, 3 arriba y abajo, 4 ocupado.

La forma del puntero cuando está sobre la zona. Cambia al momento si ya está encima y vuelve a la normal al salir.
""", """\
- `canvas`: the drawing area.
- `shape`: 0 normal, 1 text (an I beam), 2 resize sideways, 3 up and down, 4 busy.

The pointer's shape while it is over the area. It changes at once if it is already there and goes back to normal
on leaving.
""", ["mui_canvas_pointer_inside"]),
    "mui_canvas_take_tab": _f("""\
- `canvas`: la zona de dibujo.
- `on`: `true` lo enciende.

Con el puntero sobre la zona, Tab y Mayúsculas+Tab llegan a la zona como teclas (código 66) en vez de pasar al
siguiente objeto de la ventana. Necesita `mui_canvas_on_input`.
""", """\
- `canvas`: the drawing area.
- `on`: `true` turns it on.

With the pointer over the area, Tab and Shift+Tab reach the area as keys (code 66) instead of moving to the window's
next object. It needs `mui_canvas_on_input`.
""", ["mui_canvas_key"]),
    "mui_scrollbar": _f("""\
- `vertical`: `true` vertical, `false` horizontal.

Una barra de desplazamiento suelta, para ir junto a una zona de dibujo. `mui_set_range` dice cuánto mide el
documento; su valor (`mui_get_value`) es la primera línea que se ve, y `mui_on_change` avisa al moverla.
""", """\
- `vertical`: `true` vertical, `false` horizontal.

A standalone scroll bar, to go next to a drawing area. `mui_set_range` says how big the document is; its value
(`mui_get_value`) is the first line shown, and `mui_on_change` fires when it moves.
""", ["mui_set_range", "mui_canvas"]),
    "mui_set_range": _f("""\
- `scrollbar`: la barra.
- `total`: el tamaño del documento (líneas, píxeles...).
- `visible`: cuánto de él cabe a la vista.

El tamaño del tirador sale de los dos.
""", """\
- `scrollbar`: the bar.
- `total`: the document's size (lines, pixels...).
- `visible`: how much of it fits in view.

The knob's size comes from the two.
""", ["mui_scrollbar"]),
    "mui_image": _f("""\
- `file`: el fichero de la imagen: ILBM siempre; PNG, JPEG o GIF si están sus datatypes.

Una imagen. `mui_set_text` cambia el fichero.
""", """\
- `file`: the picture file: always ILBM; PNG, JPEG or GIF if their datatypes are installed.

A picture. `mui_set_text` changes the file.
""", ["mui_image_button", "image_load"]),
    "mui_image_button": _f("""\
- `file`: el fichero de la imagen.

Un botón con una imagen, como los de una barra de herramientas. Responde a `mui_on_press` como un botón;
`mui_set_text` cambia la imagen.
""", """\
- `file`: the picture file.

A button with a picture, like those of a toolbar. It responds to `mui_on_press` like a button; `mui_set_text`
changes the picture.
""", ["mui_image_toggle", "mui_on_press"]),
    "mui_image_toggle": _f("""\
- `file`: el fichero de la imagen.
- `group`: 0 = suelto; mayor que 0 = pulsar uno suelta los demás del mismo grupo (como la alineación).
- `selected`: si empieza pulsado.

Un botón con imagen que se queda pulsado, como negrita o cursiva. `mui_get_value` da 1 o 0 y `mui_on_change`
avisa al cambiar; en un grupo, solo salta en el que se pulsa.
""", """\
- `file`: the picture file.
- `group`: 0 = on its own; greater than 0 = pressing one releases the others of the same group (like alignment).
- `selected`: whether it starts pressed.

A picture button that stays pressed, like bold or italic. `mui_get_value` gives 1 or 0 and `mui_on_change` fires on
a change; in a group, only the one pressed fires.
""", ["mui_image_button", "mui_on_change"]),
    "mui_combo": _f("""\
- `text`: el texto con el que empieza.
- `options`: las líneas de la lista, separadas por `|`.

Un campo de texto con una lista que se despliega: se escribe o se elige una línea. `mui_get_text` lo lee,
`mui_list_add` y las demás `mui_list_*` cambian la lista, y `mui_on_ack` avisa con Return o al elegir.
""", """\
- `text`: the starting text.
- `options`: the list's lines, separated by `|`.

A text field with a drop-down list: you type or pick a line. `mui_get_text` reads it, `mui_list_add` and the other
`mui_list_*` functions change the list, and `mui_on_ack` fires on Return or on a pick.
""", ["mui_string", "mui_on_ack", "mui_list_add"]),
}
