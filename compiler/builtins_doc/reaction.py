"""ReAction (REACTION_FUNCTIONS)."""

GROUPS = {
    "REACTION_FUNCTIONS": {
        "es": """\
Ventanas con las clases ReAction de AmigaOS 3.2 (`window.class`, `layout.gadget` y los gadgets): se colocan solas,
como las de MUI, y vienen con el sistema. En AmigaOS 3.1 no están: para un programa que vaya en todos, MUI o los
gadgets por número.

**El flujo:**

1. `ra_window_create(título, ancho, alto)`: una ventana, hasta 4; pasa a ser la actual (`ra_window_use` elige otra).
2. Los gadgets, en orden, dentro de grupos (`ra_layout_hgroup_begin`, `ra_layout_vgroup_begin` y
   `ra_layout_group_end`). Cada `ra_add_*` recibe primero un número de gadget que elige el programa (0 a 63).
3. Los menús, si hacen falta (`ra_menu_*`), antes de abrir.
4. `ra_window_open()` y el bucle: `ra_wait_event()` devuelve el número del gadget usado, `RA_EVENT_CLOSE()` (-1)
   si se cerró la ventana o `RA_EVENT_MENU()` si se eligió un menú (`ra_menu_id` dice cuál).
5. `ra_window_close()`.

Los valores se leen y cambian por el número del gadget: `ra_get_value`, `ra_set_value`, `ra_get_string`...
""",
        "en": """\
Windows with AmigaOS 3.2's ReAction classes (`window.class`, `layout.gadget` and the gadgets): they lay themselves
out, like MUI's, and come with the system. AmigaOS 3.1 lacks them: for a program that runs everywhere, MUI or the
numbered gadgets.

**The flow:**

1. `ra_window_create(title, width, height)`: a window, up to 4; it becomes the current one (`ra_window_use` picks
   another).
2. The gadgets, in order, inside groups (`ra_layout_hgroup_begin`, `ra_layout_vgroup_begin` and
   `ra_layout_group_end`). Each `ra_add_*` takes first a gadget number chosen by the program (0 to 63).
3. The menus, if needed (`ra_menu_*`), before opening.
4. `ra_window_open()` and the loop: `ra_wait_event()` returns the number of the gadget used, `RA_EVENT_CLOSE()` (-1)
   if the window was closed or `RA_EVENT_MENU()` if a menu was chosen (`ra_menu_id` says which).
5. `ra_window_close()`.

Values are read and changed by the gadget's number: `ra_get_value`, `ra_set_value`, `ra_get_string`...
""",
        "example": "tests/test_doc_reaction.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_ID_ES = "- `id`: el número del gadget, que elige el programa (de 0 a 63).\n"
_ID_EN = "- `id`: the gadget's number, chosen by the program (0 to 63).\n"
_ADD_ES = "\nLo añade al grupo abierto de la ventana actual. Devuelve 1, o 0 si no pudo.\n"
_ADD_EN = "\nAdds it to the current window's open group. Returns 1, or 0 if it could not.\n"
_CV_ES = "Dentro de la función de dibujo del lienzo, devuelve "
_CV_EN = "Inside the canvas drawing function, returns "
_DR_ES = "Tras `ra_get_drawing_bounds`, devuelve "
_DR_EN = "After `ra_get_drawing_bounds`, returns "

FUNCS = {
    # ------------------------------------------------------------ ventanas y eventos
    "ra_window_create": _f("""\
- `title`: el título.
- `width`, `height`: el tamaño inicial.

Crea una ventana ReAction con su layout (vertical) y la hace la actual. Devuelve su número (1 a 4), o 0 si no pudo
(falta `window.class`: no es AmigaOS 3.2).
""", """\
- `title`: the title.
- `width`, `height`: the initial size.

Creates a ReAction window with its (vertical) layout and makes it the current one. Returns its number (1 to 4), or 0
if it could not (`window.class` is missing: not AmigaOS 3.2).
""", ["ra_window_open", "ra_window_use"]),
    "ra_window_use": _f("- `window`: el número de `ra_window_create`.\n\nLas siguientes llamadas `ra_*` trabajan con esa ventana.\n",
                        "- `window`: the number from `ra_window_create`.\n\nThe following `ra_*` calls work on that window.\n",
                        ["ra_event_window"]),
    "ra_event_window": _f("Devuelve de qué ventana vino el último evento: su número de `ra_window_create`.\n",
                          "Returns which window the last event came from: its `ra_window_create` number.\n", ["ra_window_use"]),
    "ra_window_open": _f("Abre la ventana actual, con los gadgets y menús añadidos. Devuelve 0 si no pudo.\n",
                         "Opens the current window, with the gadgets and menus added. Returns 0 if it could not.\n", ["ra_wait_event"]),
    "ra_window_close": _f("Cierra la ventana actual y libera sus gadgets; si queda otra abierta, pasa a ser la actual.\n",
                          "Closes the current window and frees its gadgets; if another one is open, it becomes current.\n", ["ra_window_open"]),
    "ra_window_sigmask": _f("Devuelve la señal de la ventana, para esperar a la vez otras cosas con código propio.\n",
                            "Returns the window's signal, to wait for other things at the same time with code of your own.\n", ["ra_handle_events"]),
    "ra_handle_events": _f("Atiende los eventos pendientes sin esperar. Devuelve el número del gadget usado, `RA_EVENT_CLOSE()` si se cerró o `RA_EVENT_NONE()` si no hay nada.\n",
                           "Handles pending events without waiting. Returns the number of the gadget used, `RA_EVENT_CLOSE()` if it was closed or `RA_EVENT_NONE()` if there is nothing.\n",
                           ["ra_wait_event"]),
    "ra_wait_event": _f("Espera, sin gastar CPU, y devuelve el número del gadget usado, `RA_EVENT_CLOSE()` si se cerró la ventana o `RA_EVENT_MENU()` si se eligió un menú.\n",
                        "Waits, using no CPU, and returns the number of the gadget used, `RA_EVENT_CLOSE()` if the window was closed or `RA_EVENT_MENU()` if a menu was chosen.\n",
                        ["ra_handle_events", "ra_menu_id"]),
    "RA_EVENT_CLOSE": _f("Devuelve el código del evento de cerrar la ventana: -1.\n", "Returns the close-window event code: -1.\n", ["ra_wait_event"]),
    "RA_EVENT_NONE": _f("Devuelve el código de ningún evento: -3 (un gadget puede tener el número 0).\n",
                        "Returns the no-event code: -3 (a gadget may have number 0).\n", ["ra_handle_events"]),
    "RA_EVENT_MENU": _f("Devuelve el código del evento de menú; `ra_menu_id` dice qué opción.\n", "Returns the menu event code; `ra_menu_id` says which item.\n", ["ra_menu_id"]),
    "ra_window_width": _f("Devuelve el ancho de la ventana actual.\n", "Returns the current window's width.\n", ["ra_window_height"]),
    "ra_window_height": _f("Devuelve el alto de la ventana actual.\n", "Returns the current window's height.\n", ["ra_window_width"]),
    "ra_window_is_open": _f("Devuelve 1 si la ventana actual está abierta.\n", "Returns 1 if the current window is open.\n", ["ra_window_open"]),
    "ra_refresh_layout": _f("Rehace la colocación de la ventana después de añadir o cambiar gadgets con ella abierta.\n",
                            "Lays the window out again after adding or changing gadgets while it is open.\n", []),
    # ------------------------------------------------------------ gadgets
    "ra_add_button": _f(_ID_ES + "- `label`: el texto.\n\nUn botón." + _ADD_ES, _ID_EN + "- `label`: the text.\n\nA button." + _ADD_EN, ["ra_wait_event", "ra_set_text"]),
    "ra_add_string": _f(_ID_ES + "- `initial`: el texto con el que empieza.\n- `maxchars`: cuántas letras caben.\n\nUn campo de texto." + _ADD_ES,
                        _ID_EN + "- `initial`: the starting text.\n- `maxchars`: how many letters fit.\n\nA text field." + _ADD_EN, ["ra_get_string", "ra_set_string"]),
    "ra_add_checkbox": _f(_ID_ES + "- `label`: el texto.\n- `checked`: si empieza marcada.\n\nUna casilla; `ra_get_value` da 1 o 0." + _ADD_ES,
                          _ID_EN + "- `label`: the text.\n- `checked`: whether it starts ticked.\n\nA checkbox; `ra_get_value` gives 1 or 0." + _ADD_EN, ["ra_get_value"]),
    "ra_add_slider": _f(_ID_ES + "- `min`, `max`: los extremos.\n- `initial`: el valor con el que empieza.\n\nUn deslizador horizontal." + _ADD_ES,
                        _ID_EN + "- `min`, `max`: the ends.\n- `initial`: the starting value.\n\nA horizontal slider." + _ADD_EN, ["ra_get_value"]),
    "ra_add_integer": _f(_ID_ES + "- `initial`: el número con el que empieza.\n- `min`, `max`: los límites.\n\nUn campo de números con flechas." + _ADD_ES,
                         _ID_EN + "- `initial`: the starting number.\n- `min`, `max`: the limits.\n\nA number field with arrows." + _ADD_EN, ["ra_get_value"]),
    "ra_add_label": _f("- `text`: el texto.\n\nUna etiqueta fija: no tiene número y no se puede cambiar. Devuelve 1, o 0 si no pudo.\n",
                       "- `text`: the text.\n\nA fixed label: it has no number and cannot be changed. Returns 1, or 0 if it could not.\n", []),
    "ra_add_palette": _f(_ID_ES + "- `depth`: cuántos colores: 2 elevado a `depth`.\n- `initial_color`: el elegido al empezar.\n\nUn gadget de paleta." + _ADD_ES,
                         _ID_EN + "- `depth`: how many colours: 2 to the power of `depth`.\n- `initial_color`: the one chosen at the start.\n\nA palette gadget." + _ADD_EN,
                         ["ra_get_palette_color"]),
    "ra_add_chooser": _f(_ID_ES + "\nUna lista desplegable vacía; las opciones, con `ra_chooser_add_item`." + _ADD_ES,
                         _ID_EN + "\nAn empty drop-down list; the options, with `ra_chooser_add_item`." + _ADD_EN, ["ra_chooser_add_item"]),
    "ra_chooser_add_item": _f(_ID_ES + "- `label`: la opción.\n\nLa añade al final de la lista desplegable.\n",
                              _ID_EN + "- `label`: the option.\n\nAdds it to the end of the drop-down list.\n", ["ra_get_chooser_selected"]),
    "ra_get_chooser_selected": _f(_ID_ES + "\nDevuelve la opción elegida, desde 0.\n", _ID_EN + "\nReturns the chosen option, from 0.\n", ["ra_set_chooser_selected"]),
    "ra_set_chooser_selected": _f(_ID_ES + "- `index`: la opción, desde 0.\n", _ID_EN + "- `index`: the option, from 0.\n", ["ra_get_chooser_selected"]),
    "ra_add_scroller": _f(_ID_ES + "- `min`, `max`: el documento.\n- `visible`: cuánto se ve.\n- `initial`: la posición.\n\nUna barra de desplazamiento horizontal." + _ADD_ES,
                          _ID_EN + "- `min`, `max`: the document.\n- `visible`: how much shows.\n- `initial`: the position.\n\nA horizontal scroll bar." + _ADD_EN,
                          ["ra_get_scroller", "ra_add_scroller_vert"]),
    "ra_add_scroller_vert": _f(_ID_ES + "- `min`, `max`, `visible`, `initial`: como en `ra_add_scroller`.\n\nUna barra de desplazamiento vertical." + _ADD_ES,
                               _ID_EN + "- `min`, `max`, `visible`, `initial`: as in `ra_add_scroller`.\n\nA vertical scroll bar." + _ADD_EN, ["ra_add_scroller"]),
    "ra_get_scroller": _f(_ID_ES + "\nDevuelve su posición.\n", _ID_EN + "\nReturns its position.\n", ["ra_set_scroller"]),
    "ra_set_scroller": _f(_ID_ES + "- `pos`: la posición nueva.\n", _ID_EN + "- `pos`: the new position.\n", ["ra_get_scroller"]),
    "ra_add_listbrowser": _f(_ID_ES + "\nUna lista de líneas; su valor es la línea elegida, -1 ninguna." + _ADD_ES,
                             _ID_EN + "\nA list of lines; its value is the chosen line, -1 none." + _ADD_EN, ["ra_listbrowser_add"]),
    "ra_listbrowser_add": _f(_ID_ES + "- `text`: la línea.\n\nLa añade al final.\n", _ID_EN + "- `text`: the line.\n\nAdds it at the end.\n", ["ra_listbrowser_clear"]),
    "ra_listbrowser_clear": _f(_ID_ES + "\nQuita todas las líneas.\n", _ID_EN + "\nRemoves every line.\n", ["ra_listbrowser_add"]),
    "ra_listbrowser_count": _f(_ID_ES + "\nDevuelve cuántas líneas tiene.\n", _ID_EN + "\nReturns how many lines it has.\n", ["ra_listbrowser_add"]),
    "ra_add_radio": _f(_ID_ES + "- `options`: separadas por `|`.\n\nBotones de radio; su valor es la opción, desde 0." + _ADD_ES,
                       _ID_EN + "- `options`: separated by `|`.\n\nRadio buttons; its value is the option, from 0." + _ADD_EN, ["ra_get_value"]),
    "ra_add_clicktab": _f(_ID_ES + "- `titles`: separados por `|`.\n\nPestañas; su valor es la pestaña, desde 0." + _ADD_ES,
                          _ID_EN + "- `titles`: separated by `|`.\n\nTabs; its value is the tab, from 0." + _ADD_EN, ["ra_get_value"]),
    "ra_add_fuelgauge": _f(_ID_ES + "- `max`: el valor de la barra llena.\n\nUna barra de progreso; `ra_set_value` la llena." + _ADD_ES,
                           _ID_EN + "- `max`: the value of the full bar.\n\nA progress bar; `ra_set_value` fills it." + _ADD_EN, ["ra_set_value"]),
    "ra_add_getfile": _f(_ID_ES + "- `title`: el título de la petición.\n\nUn botón que abre la petición de ficheros; `ra_get_string(id)` da el elegido." + _ADD_ES,
                         _ID_EN + "- `title`: the requester's title.\n\nA button that opens the file requester; `ra_get_string(id)` gives the chosen one." + _ADD_EN,
                         ["ra_get_string"]),
    "ra_get_value": _f(_ID_ES + "\nDevuelve su valor: casilla 1 o 0, deslizador, número, paleta, selector, barra, lista, radio, pestaña o progreso.\n",
                       _ID_EN + "\nReturns its value: checkbox 1 or 0, slider, number, palette, chooser, bar, list, radio, tab or progress.\n", ["ra_set_value"]),
    "ra_set_value": _f(_ID_ES + "- `value`: el valor nuevo, como en `ra_get_value`.\n", _ID_EN + "- `value`: the new value, as in `ra_get_value`.\n", ["ra_get_value"]),
    "ra_get_string": _f(_ID_ES + "\nDevuelve el texto de un campo de texto, o el fichero de un `ra_add_getfile`.\n",
                        _ID_EN + "\nReturns a text field's text, or a `ra_add_getfile` file.\n", ["ra_set_string"]),
    "ra_set_string": _f(_ID_ES + "- `text`: el texto nuevo del campo.\n", _ID_EN + "- `text`: the field's new text.\n", ["ra_get_string"]),
    "ra_set_text": _f(_ID_ES + "- `text`: el texto nuevo de un botón.\n", _ID_EN + "- `text`: the new text of a button.\n", ["ra_add_button"]),
    "ra_get_palette_color": _f(_ID_ES + "\nDevuelve el color elegido.\n", _ID_EN + "\nReturns the chosen colour.\n", ["ra_set_palette_color"]),
    "ra_set_palette_color": _f(_ID_ES + "- `color`: el color.\n", _ID_EN + "- `color`: the colour.\n", ["ra_get_palette_color"]),
    "ra_enable_gadget": _f(_ID_ES + "\nVuelve a dejar usarlo.\n", _ID_EN + "\nLets it be used again.\n", ["ra_disable_gadget"]),
    "ra_disable_gadget": _f(_ID_ES + "\nLo desactiva: en gris, sin responder.\n", _ID_EN + "\nDisables it: grey, not responding.\n", ["ra_enable_gadget"]),
    "ra_gadget_exists": _f(_ID_ES + "\nDevuelve 1 si hay un gadget con ese número en la ventana actual.\n", _ID_EN + "\nReturns 1 if there is a gadget with that number in the current window.\n", []),
    # ------------------------------------------------------------ grupos
    "ra_layout_hgroup_begin": _f("Empieza un grupo que pone sus gadgets uno al lado de otro, dentro del grupo abierto. Se acaba con `ra_layout_group_end`.\n",
                                 "Starts a group placing its gadgets side by side, inside the open group. It ends with `ra_layout_group_end`.\n",
                                 ["ra_layout_vgroup_begin", "ra_layout_group_end"]),
    "ra_layout_vgroup_begin": _f("Empieza un grupo que pone sus gadgets uno debajo de otro. Se acaba con `ra_layout_group_end`.\n",
                                 "Starts a group placing its gadgets one under the other. It ends with `ra_layout_group_end`.\n", ["ra_layout_group_end"]),
    "ra_layout_group_end": _f("Acaba el último grupo abierto.\n", "Ends the last open group.\n", ["ra_layout_hgroup_begin"]),
    "ra_layout_hgroup_weighted": _f("- `weight`: cuánto espacio se lleva frente a sus vecinos.\n\nComo `ra_layout_hgroup_begin`, con peso; se acaba con `ra_layout_group_end_weighted`.\n",
                                    "- `weight`: how much space it takes compared with its neighbours.\n\nLike `ra_layout_hgroup_begin`, weighted; it ends with `ra_layout_group_end_weighted`.\n",
                                    ["ra_layout_group_end_weighted"]),
    "ra_layout_vgroup_weighted": _f("- `weight`: su peso.\n\nComo `ra_layout_vgroup_begin`, con peso.\n", "- `weight`: its weight.\n\nLike `ra_layout_vgroup_begin`, weighted.\n",
                                    ["ra_layout_group_end_weighted"]),
    "ra_layout_group_end_weighted": _f("Acaba un grupo con peso.\n", "Ends a weighted group.\n", ["ra_layout_hgroup_weighted"]),
    "ra_add_space": _f("Un espacio que se estira entre gadgets de un grupo horizontal.\n", "A space that stretches between gadgets of a horizontal group.\n", ["ra_add_vspace"]),
    "ra_add_vspace": _f("Un espacio que se estira entre gadgets de un grupo vertical.\n", "A space that stretches between gadgets of a vertical group.\n", ["ra_add_space"]),
    # ------------------------------------------------------------ dibujo
    "ra_get_rastport": _f("Devuelve el RastPort de la ventana actual y lo hace el destino de los `gfx_*`.\n",
                          "Returns the current window's RastPort and makes it the `gfx_*` target.\n", ["ra_get_inner_left"]),
    "ra_get_inner_left": _f("Devuelve dónde empieza por la izquierda el interior de la ventana.\n", "Returns where the window's inside starts on the left.\n", ["ra_get_inner_top"]),
    "ra_get_inner_top": _f("Devuelve dónde empieza por arriba el interior de la ventana.\n", "Returns where the window's inside starts at the top.\n", ["ra_get_inner_left"]),
    "ra_get_inner_width": _f("Devuelve el ancho del interior de la ventana.\n", "Returns the width of the window's inside.\n", ["ra_get_inner_height"]),
    "ra_get_inner_height": _f("Devuelve el alto del interior de la ventana.\n", "Returns the height of the window's inside.\n", ["ra_get_inner_width"]),
    "ra_add_drawing_area": _f(_ID_ES + "- `min_width`, `min_height`: el tamaño mínimo.\n\nUna zona (gadget Space) para dibujar a mano; crece con la ventana." + _ADD_ES,
                              _ID_EN + "- `min_width`, `min_height`: the minimum size.\n\nAn area (Space gadget) to draw by hand; it grows with the window." + _ADD_EN,
                              ["ra_init_canvas_render", "ra_get_drawing_bounds"]),
    "ra_get_drawing_bounds": _f(_ID_ES + "\nMira dónde quedó la zona de dibujo, después de abrir la ventana; `ra_drawing_*` lo dan.\n",
                                _ID_EN + "\nLooks up where the drawing area ended up, after opening the window; `ra_drawing_*` give it.\n", ["ra_drawing_left"]),
    "ra_drawing_left": _f(_DR_ES + "la izquierda de la zona de dibujo.\n", _DR_EN + "the drawing area's left.\n", ["ra_drawing_top"]),
    "ra_drawing_top": _f(_DR_ES + "su parte de arriba.\n", _DR_EN + "its top.\n", ["ra_drawing_left"]),
    "ra_drawing_width": _f(_DR_ES + "su ancho.\n", _DR_EN + "its width.\n", ["ra_drawing_height"]),
    "ra_drawing_height": _f(_DR_ES + "su alto.\n", _DR_EN + "its height.\n", ["ra_drawing_width"]),
    "ra_calc_drawing_area": _f("""\
- `toolbar_h`, `timeline_h`: lo que ocupan arriba y abajo.
- `left_w`, `right_w`: lo que ocupan a los lados.

Calcula la zona de dibujo restando eso al interior de la ventana, cuando no se puede preguntar al gadget.
""", """\
- `toolbar_h`, `timeline_h`: what is taken at the top and the bottom.
- `left_w`, `right_w`: what is taken at the sides.

Works out the drawing area by taking that away from the window's inside, when the gadget cannot be asked.
""", ["ra_get_drawing_bounds"]),
    "ra_init_canvas_render": _f("""\
Hace que la zona de dibujo se pinte con una función del programa llamada `render_canvas()`, que dibuja con los
`gfx_*`: ReAction la llama cuando hace falta. Dentro, `ra_canvas_*` dicen dónde está el lienzo.
""", """\
Makes the drawing area paint itself with a program function named `render_canvas()`, which draws with the `gfx_*`
functions: ReAction calls it when needed. Inside, `ra_canvas_*` say where the canvas is.
""", ["ra_canvas_enable", "ra_refresh_canvas"]),
    "ra_canvas_enable": _f("Activa el dibujo del lienzo, cuando todo lo que usa `render_canvas()` está preparado.\n",
                           "Turns canvas drawing on, once everything `render_canvas()` uses is ready.\n", ["ra_init_canvas_render"]),
    "ra_refresh_canvas": _f(_ID_ES + "\nPide que el lienzo se dibuje otra vez (llama a `render_canvas()`).\n",
                            _ID_EN + "\nAsks for the canvas to be drawn again (it calls `render_canvas()`).\n", ["ra_init_canvas_render"]),
    "ra_canvas_left": _f(_CV_ES + "la izquierda del lienzo.\n", _CV_EN + "the canvas's left.\n", ["ra_canvas_top"]),
    "ra_canvas_top": _f(_CV_ES + "su parte de arriba.\n", _CV_EN + "its top.\n", ["ra_canvas_left"]),
    "ra_canvas_width": _f(_CV_ES + "su ancho.\n", _CV_EN + "its width.\n", ["ra_canvas_height"]),
    "ra_canvas_height": _f(_CV_ES + "su alto.\n", _CV_EN + "its height.\n", ["ra_canvas_width"]),
    # ------------------------------------------------------------ menús
    "ra_menu_title": _f("- `label`: el título.\n\nEmpieza un menú de la ventana actual, antes de `ra_window_open`.\n",
                        "- `label`: the title.\n\nStarts a menu of the current window, before `ra_window_open`.\n", ["ra_menu_item"]),
    "ra_menu_item": _f("- `label`: el texto.\n- `key`: la letra con Amiga; `\"\"` ninguna.\n- `id`: su número.\n\nAñade una opción al último menú.\n",
                       "- `label`: the text.\n- `key`: the letter with Amiga; `\"\"` none.\n- `id`: its number.\n\nAdds an item to the last menu.\n",
                       ["ra_menu_id", "RA_EVENT_MENU"]),
    "ra_menu_separator": _f("Añade una raya entre opciones.\n", "Adds a line between items.\n", ["ra_menu_item"]),
    "ra_menu_id": _f("Tras un `RA_EVENT_MENU()`, devuelve el número de la opción elegida.\n", "After a `RA_EVENT_MENU()`, returns the chosen item's number.\n", ["RA_EVENT_MENU"]),
}
