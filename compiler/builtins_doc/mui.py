"""MUI (MUI_FUNCTIONS): aplicación, ventanas, grupos, objetos, valores, listas, eventos y menús. La zona de dibujo y
lo demás, en mui_lienzo.py."""

GROUPS = {
    "MUI_FUNCTIONS": {
        "es": """\
Interfaces con MUI: ventanas que se colocan solas, se adaptan a la fuente y al tamaño, y que el usuario configura
desde las preferencias de MUI. Funciona con MUI 3.8 o MUI 5, en un 68020 o mejor.

**Cómo se construye.** Los objetos de MUI son números que se guardan en variables. La ventana se describe de
arriba abajo, como un árbol, con una pila de grupos:

1. `mui_app_begin(título, base)`: la aplicación. Devuelve 0 si no hay MUI: el programa tiene que decirlo y acabar.
2. `win = mui_window_begin(título, id)` ... `mui_window_end()`: una ventana. Dentro, grupos
   (`mui_vgroup_begin`, `mui_hgroup_begin`, `mui_columns_begin`, `mui_frame_begin`... hasta su `mui_group_end`) y
   objetos (`mui_button`, `mui_string`, `mui_list`...). Cada objeto entra en el grupo abierto.
3. Los eventos: `mui_on_press(boton, 1)`, `mui_on_change(casilla, 2)`... dan un número a cada cosa que interesa.
   Los números son del programa, mayores que 0.
4. `mui_window_open(win)` y el bucle: `ev = mui_wait_event()` espera y devuelve el número del evento, o -1 para
   salir (el botón de cerrar de la primera ventana, por defecto).
5. `mui_app_end()` al acabar (si no, se hace solo).

**Valores.** `mui_get_value` y `mui_set_value` leen y cambian el valor de un objeto (la casilla, el deslizador, la
opción, la línea elegida...); `mui_get_text` y `mui_set_text`, su texto.

**El editor visual.** Las ventanas se pueden dibujar con el editor de Forja o de la extensión de VS Code, que
guarda un `.dashui`; el programa lo usa con `import "ventana.dashui"` (ver `docs/MUI_EDITOR.md`). El diseño de la
API está en `docs/MUI_DISEÑO.md`.
""",
        "en": """\
Interfaces with MUI: windows that lay themselves out, adapt to the font and the size, and that the user sets up
from the MUI preferences. It works with MUI 3.8 or MUI 5, on a 68020 or better.

**How it is built.** MUI objects are numbers kept in variables. The window is described top down, as a tree, with
a stack of groups:

1. `mui_app_begin(title, base)`: the application. Returns 0 if there is no MUI: the program has to say so and end.
2. `win = mui_window_begin(title, id)` ... `mui_window_end()`: a window. Inside, groups (`mui_vgroup_begin`,
   `mui_hgroup_begin`, `mui_columns_begin`, `mui_frame_begin`... up to their `mui_group_end`) and objects
   (`mui_button`, `mui_string`, `mui_list`...). Each object goes into the open group.
3. Events: `mui_on_press(button, 1)`, `mui_on_change(checkbox, 2)`... give a number to each thing of interest. The
   numbers are the program's, greater than 0.
4. `mui_window_open(win)` and the loop: `ev = mui_wait_event()` waits and returns the event's number, or -1 to quit
   (the close button of the first window, by default).
5. `mui_app_end()` at the end (otherwise it happens on its own).

**Values.** `mui_get_value` and `mui_set_value` read and change an object's value (the checkbox, the slider, the
option, the chosen line...); `mui_get_text` and `mui_set_text`, its text.

**The visual editor.** Windows can be drawn with the editor in Forja or in the VS Code extension, which saves a
`.dashui`; the program uses it with `import "window.dashui"` (see `docs/MUI_EDITOR.md`). The API's design is in
`docs/MUI_DISEÑO.md`.
""",
        "example": "tests/test_doc_mui.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


FUNCS = {
    # ------------------------------------------------------------ aplicación
    "mui_app_begin": _f("""\
- `title`: el nombre de la aplicación, el que enseña MUI en sus preferencias y en Exchange.
- `base`: el nombre de su puerto ARexx, en mayúsculas (`"MIPROG"`); el puerto es `base` más `.1`.

Abre la `muimaster.library` y crea la aplicación. Va antes de todo lo demás de MUI. Devuelve 0 si no hay MUI o la
CPU es un 68000: el programa tiene que avisar y acabar.
""", """\
- `title`: the application's name, the one MUI shows in its preferences and in Exchange.
- `base`: the name of its ARexx port, in capitals (`"MYPROG"`); the port is `base` plus `.1`.

Opens `muimaster.library` and creates the application. It goes before anything else of MUI. Returns 0 if there is
no MUI or the CPU is a 68000: the program has to warn and end.
""", ["mui_app_end", "mui_window_begin"]),
    "mui_app_end": _f("""\
Deshace la aplicación con todas sus ventanas y objetos y cierra MUI. Si el programa no la llama, se hace sola al
acabar. Después ningún objeto de MUI sirve.
""", """\
Disposes of the application with all its windows and objects and closes MUI. If the program does not call it, it
happens on its own at the end. Afterwards no MUI object is valid.
""", ["mui_app_begin"]),
    "mui_app_rexx": _f("""\
- `app`: la aplicación (lo que devolvió `mui_app_begin`).
- `func`: una función `f(orden: String) -> String`.

Cada orden ARexx que llegue al puerto de la aplicación y que MUI no conteste solo (QUIT, SHOW, HIDE, INFO...)
llama a `func` con la línea entera. Lo que devuelve es el RESULT. Corre mientras `mui_wait_event` espera.
""", """\
- `app`: the application (what `mui_app_begin` returned).
- `func`: a function `f(command: String) -> String`.

Every ARexx command reaching the application's port that MUI does not answer itself (QUIT, SHOW, HIDE, INFO...)
calls `func` with the whole line. What it returns is the RESULT. It runs while `mui_wait_event` waits.
""", ["mui_rexx_fail"]),
    "mui_rexx_fail": _f("""\
- `rc`: el código: 5 aviso, 10 error, 20 fallo.

Dentro de la función de `mui_app_rexx`, hace que la orden acabe con ese RC. Con un RC no hay RESULT.
""", """\
- `rc`: the code: 5 warning, 10 error, 20 failure.

Inside the `mui_app_rexx` function, makes the command end with that RC. With an RC there is no RESULT.
""", ["mui_app_rexx"]),
    "mui_app_field_colors": _f("""\
- `r`, `g`, `b`: el fondo de los campos sin el cursor (0 a 255).
- `active_r`, `active_g`, `active_b`: el fondo del campo con el cursor.
- `cursor_r`, `cursor_g`, `cursor_b`: el color del cursor.

Los colores de todos los campos de texto de la aplicación (`mui_string`, `mui_text_editor`, `mui_combo`) en las
ventanas que se abran después. El texto sigue negro: elige fondos claros, o grises en los que se lea.
""", """\
- `r`, `g`, `b`: the background of fields without the cursor (0 to 255).
- `active_r`, `active_g`, `active_b`: the background of the field with the cursor.
- `cursor_r`, `cursor_g`, `cursor_b`: the cursor's colour.

The colours of every text field in the application (`mui_string`, `mui_text_editor`, `mui_combo`) in windows opened
afterwards. The text stays black: pick light backgrounds, or greys it can be read on.
""", ["mui_set_background"]),
    # ------------------------------------------------------------ ventanas
    "mui_window_begin": _f("""\
- `title`: el título.
- `id`: de 1 a 255 para que MUI recuerde su tamaño y su sitio de una vez a otra (cada ventana el suyo); 0 =
  ninguno.

Empieza a describir una ventana con un grupo vertical dentro: lo que se cree hasta `mui_window_end` va en ella.
Devuelve la ventana, para `mui_window_open` y las demás.
""", """\
- `title`: the title.
- `id`: 1 to 255 so MUI remembers its size and place from one run to the next (each window its own); 0 = none.

Starts describing a window with a vertical group inside: what is created up to `mui_window_end` goes in it.
Returns the window, for `mui_window_open` and the rest.
""", ["mui_window_end", "mui_window_open"]),
    "mui_window_end": _f("""\
Acaba la ventana empezada con `mui_window_begin` y la añade a la aplicación. Los grupos abiertos dentro tienen que
estar cerrados con su `mui_group_end`. La ventana no se ve hasta `mui_window_open`.
""", """\
Ends the window started with `mui_window_begin` and adds it to the application. The groups opened inside must be
closed with their `mui_group_end`. The window does not show until `mui_window_open`.
""", ["mui_window_begin"]),
    "mui_window_open": _f("""\
- `win`: la ventana.

La abre y la hace la activa. Devuelve 0 si no pudo: no cabe en la pantalla o falta memoria.
""", """\
- `win`: the window.

Opens it and makes it the active one. Returns 0 if it could not: it does not fit on the screen or memory is short.
""", ["mui_window_close", "mui_window_open_back"]),
    "mui_window_open_back": _f("""\
- `win`: la ventana.

La abre sin hacerla la activa: el teclado se queda donde estaba. Devuelve 0 si no pudo.
""", """\
- `win`: the window.

Opens it without making it the active one: the keyboard stays where it was. Returns 0 if it could not.
""", ["mui_window_open"]),
    "mui_window_close": _f("""\
- `win`: la ventana.

La cierra. Sigue existiendo con todos sus objetos y valores: `mui_window_open` la vuelve a abrir igual.
""", """\
- `win`: the window.

Closes it. It still exists with all its objects and values: `mui_window_open` opens it again as it was.
""", ["mui_window_open", "mui_window_dispose"]),
    "mui_window_dispose": _f("""\
- `win`: la ventana.

La cierra, la quita de la aplicación y la libera con todos sus objetos, que ya no se pueden usar. Para ventanas que
se hacen una y otra vez, como una vista previa. Con 0 o una ventana que ya no está, no hace nada.
""", """\
- `win`: the window.

Closes it, removes it from the application and frees it with all its objects, which can no longer be used. For
windows made over and over, like a preview. With 0 or a window that is gone, it does nothing.
""", ["mui_window_close"]),
    "mui_window_activate": _f("""\
- `win`: la ventana.

La pone delante y la hace la activa. Si está cerrada, la abre.
""", """\
- `win`: the window.

Brings it to the front and makes it the active one. If it is closed, it opens it.
""", ["mui_window_active"]),
    "mui_window_active": _f("""\
- `win`: la ventana.

Devuelve 1 si es la ventana activa, si no 0. Sirve cuando varias ventanas de un `.dashui` dan el mismo número de
evento.
""", """\
- `win`: the window.

Returns 1 if it is the active window, otherwise 0. Useful when several windows from a `.dashui` give the same event
number.
""", ["mui_window_activate"]),
    "mui_window_move": _f("""\
- `win`: una ventana abierta.
- `dx`, `dy`: cuántos píxeles se mueve.

Desplaza la ventana. Las de un `.dashui` se abren todas en el mismo sitio: así no quedan una encima de otra.
""", """\
- `win`: an open window.
- `dx`, `dy`: how many pixels it moves.

Shifts the window. Those of a `.dashui` all open in the same place: this keeps them from piling up.
""", ["mui_window_size"]),
    "mui_window_size": _f("""\
- `win`: la ventana, antes de abrirla.
- `width_pct`, `height_pct`: su tamaño en tanto por ciento de la pantalla visible.

La ventana se abre de ese tamaño y centrada. Si tiene un `id`, lo que MUI recuerde manda las veces siguientes.
""", """\
- `win`: the window, before opening it.
- `width_pct`, `height_pct`: its size as a percentage of the visible screen.

The window opens at that size and centred. If it has an `id`, what MUI remembers rules on later runs.
""", ["mui_window_fullscreen", "mui_window_begin"]),
    "mui_window_fullscreen": _f("""\
- `win`: la ventana, antes de abrirla.

Ocupa toda la pantalla, sin bordes, barra de título ni gadgets, y se abre activa.
""", """\
- `win`: the window, before opening it.

It takes the whole screen, without borders, title bar or gadgets, and opens active.
""", ["mui_window_own_screen"]),
    "mui_window_screen": _f("""\
- `win`: la ventana, antes de abrirla.
- `name`: el nombre de una pantalla pública: la de `screen_clone_wb` u otra.

La ventana se abre, normal, en esa pantalla. Devuelve `false` si esa pantalla no existe.
""", """\
- `win`: the window, before opening it.
- `name`: the name of a public screen: the `screen_clone_wb` one or another.

The window opens, normally, on that screen. Returns `false` if that screen does not exist.
""", ["screen_clone_wb", "mui_window_own_screen"]),
    "mui_window_own_screen": _f("""\
- `win`: la ventana, antes de abrirla.

La ventana ocupa toda una pantalla propia, igual que la pública. Devuelve `false` si no pudo; entonces se abre en
la pública.
""", """\
- `win`: the window, before opening it.

The window fills a screen of its own, like the public one. Returns `false` if it could not; then it opens on the
public screen.
""", ["mui_window_fullscreen"]),
    "mui_request": _f("""\
- `window`: la ventana sobre la que sale; 0 = sobre la aplicación.
- `title`: el título.
- `text`: la pregunta; admite los códigos de texto de MUI.
- `buttons`: los botones separados por `|`, con `_` para su tecla: `"_Guardar|_Descartar|_Cancelar"`.

Pregunta y espera; mientras, las ventanas de la aplicación no responden. Devuelve el botón elegido: 1, 2...
desde la izquierda, y 0 el último (también con Esc).
""", """\
- `window`: the window it shows over; 0 = over the application.
- `title`: the title.
- `text`: the question; it takes MUI's text codes.
- `buttons`: the buttons separated by `|`, with `_` for their key: `"_Save|_Discard|_Cancel"`.

Asks and waits; meanwhile the application's windows do not respond. Returns the chosen button: 1, 2... from the
left, and 0 the last one (also with Esc).
""", ["mui_window_begin"]),
    # ------------------------------------------------------------ grupos
    "mui_vgroup_begin": _f("""\
Empieza un grupo que pone sus objetos uno debajo de otro, dentro del grupo abierto. Se acaba con `mui_group_end`.
Devuelve el grupo, para `mui_set_visible`, `mui_weight` o `mui_set_background`.
""", """\
Starts a group that places its objects one under the other, inside the open group. It ends with `mui_group_end`.
Returns the group, for `mui_set_visible`, `mui_weight` or `mui_set_background`.
""", ["mui_hgroup_begin", "mui_group_end"]),
    "mui_hgroup_begin": _f("""\
Empieza un grupo que pone sus objetos uno al lado de otro. Se acaba con `mui_group_end`. Devuelve el grupo.
""", """\
Starts a group that places its objects side by side. It ends with `mui_group_end`. Returns the group.
""", ["mui_vgroup_begin", "mui_group_end"]),
    "mui_group_end": _f("""\
Acaba el último grupo abierto (de cualquier clase: `mui_vgroup_begin`, `mui_frame_begin`, `mui_register_begin`...).
Los siguientes objetos van otra vez en el grupo de fuera.
""", """\
Ends the last open group (of any kind: `mui_vgroup_begin`, `mui_frame_begin`, `mui_register_begin`...). The next
objects go into the outer group again.
""", ["mui_vgroup_begin"]),
    "mui_frame_begin": _f("""\
- `title`: el título del marco; `""` = sin título.
- `horizontal`: `true` pone los objetos uno al lado de otro; `false`, uno debajo de otro.

Empieza un grupo con un marco alrededor. Se acaba con `mui_group_end`.
""", """\
- `title`: the frame's title; `""` = no title.
- `horizontal`: `true` places the objects side by side; `false`, one under the other.

Starts a group with a frame around it. It ends with `mui_group_end`.
""", ["mui_group_end"]),
    "mui_columns_begin": _f("""\
- `columns`: cuántas columnas.

Empieza un grupo en rejilla: los objetos llenan las filas de izquierda a derecha. Con 2 columnas, una etiqueta y
su campo por fila, sale un formulario con todo alineado. Se acaba con `mui_group_end`.
""", """\
- `columns`: how many columns.

Starts a grid group: the objects fill the rows left to right. With 2 columns, a label and its field per row, you
get a form with everything aligned. It ends with `mui_group_end`.
""", ["mui_label", "mui_group_end"]),
    "mui_register_begin": _f("""\
- `titles`: los títulos de las pestañas separados por `|`: `"General|Avanzado"`.

Empieza un grupo de pestañas: cada hijo directo (normalmente un grupo) es una página. `mui_get_value` dice la
página que se ve, desde 0, y `mui_set_value` cambia de página. Se acaba con `mui_group_end`.
""", """\
- `titles`: the tab titles separated by `|`: `"General|Advanced"`.

Starts a tab group: each direct child (usually a group) is a page. `mui_get_value` says which page shows, from 0,
and `mui_set_value` changes page. It ends with `mui_group_end`.
""", ["mui_group_end", "mui_on_change"]),
    "mui_scroll_begin": _f("""\
Empieza una zona con barras de desplazamiento, para un contenido más grande que la ventana. Se acaba con
`mui_group_end`.
""", """\
Starts an area with scroll bars, for contents bigger than the window. It ends with `mui_group_end`.
""", ["mui_group_end"]),
    "mui_space": _f("""\
Un espacio vacío que se estira y ocupa lo que sobra. Entre dos botones de un grupo horizontal, los separa a los
extremos.
""", """\
An empty space that stretches and takes up what is left. Between two buttons of a horizontal group, it pushes them
to the ends.
""", ["mui_weight"]),
    "mui_balance": _f("""\
Una barra entre dos objetos que el usuario arrastra para repartir el sitio entre ellos (una lista y un texto, por
ejemplo).
""", """\
A bar between two objects that the user drags to share the space between them (a list and a text, for instance).
""", ["mui_weight"]),
    "mui_weight": _f("""\
- `obj`: el objeto.
- `weight`: su peso; 100 por defecto.

Qué parte del espacio libre se lleva el objeto frente a sus vecinos: con 200 crece el doble que uno de 100.
""", """\
- `obj`: the object.
- `weight`: its weight; 100 by default.

How much of the free space the object takes compared with its neighbours: at 200 it grows twice as much as one at
100.
""", ["mui_space", "mui_balance"]),
    # ------------------------------------------------------------ objetos
    "mui_text": _f("""\
- `text`: el texto. Admite los códigos de MUI: `"\\33c"` centrado, `"\\33r"` a la derecha, `"\\33b"` negrita.

Un texto que no se edita. `mui_set_text` lo cambia.
""", """\
- `text`: the text. It takes MUI's codes: `"\\33c"` centred, `"\\33r"` right aligned, `"\\33b"` bold.

A text that is not edited. `mui_set_text` changes it.
""", ["mui_label", "mui_set_text"]),
    "mui_label": _f("""\
- `text`: el texto.

La etiqueta de una fila de un formulario: alineada a la derecha, para ir delante de su campo en un
`mui_columns_begin(2)`.
""", """\
- `text`: the text.

The label of a form row: right aligned, to go in front of its field in a `mui_columns_begin(2)`.
""", ["mui_columns_begin", "mui_text"]),
    "mui_button": _f("""\
- `label`: el texto; una `_` delante de una letra la hace su tecla.

Un botón. Al pulsarlo, el evento de `mui_on_press`.
""", """\
- `label`: the text; a `_` before a letter makes it its key.

A button. Pressing it fires the `mui_on_press` event.
""", ["mui_on_press", "mui_image_button"]),
    "mui_string": _f("""\
- `initial`: el texto con el que empieza.
- `maxlen`: cuántas letras caben como mucho.

Un campo de texto de una línea. `mui_get_text` lo lee; `mui_on_ack` avisa al pulsar Return y `mui_on_change` con
cada cambio.
""", """\
- `initial`: the starting text.
- `maxlen`: the most letters it holds.

A one-line text field. `mui_get_text` reads it; `mui_on_ack` fires on Return and `mui_on_change` on every change.
""", ["mui_get_text", "mui_on_ack", "mui_text_editor"]),
    "mui_text_editor": _f("""\
- `lines`: cuántas líneas de alto.

Un campo de texto de varias líneas, con su barra. Return empieza otra línea. `mui_get_text` y `mui_set_text` lo
leen y lo cambian entero; `mui_on_ack` avisa con Amiga+Return.
""", """\
- `lines`: how many lines high.

A multi-line text field, with its scroll bar. Return starts a new line. `mui_get_text` and `mui_set_text` read and
change all of it; `mui_on_ack` fires on Amiga+Return.
""", ["mui_string"]),
    "mui_checkbox": _f("""\
- `checked`: si empieza marcada.

Una casilla. `mui_get_value` da 1 marcada y 0 sin marcar; `mui_on_change` avisa al cambiar.
""", """\
- `checked`: whether it starts ticked.

A checkbox. `mui_get_value` gives 1 ticked and 0 unticked; `mui_on_change` fires when it changes.
""", ["mui_get_value", "mui_on_change"]),
    "mui_cycle": _f("""\
- `options`: las opciones separadas por `|`: `"Baja|Media|Alta"`.

Un gadget que pasa a la siguiente opción con cada clic. `mui_get_value` da la elegida, desde 0.
""", """\
- `options`: the options separated by `|`: `"Low|Medium|High"`.

A gadget that moves to the next option with each click. `mui_get_value` gives the chosen one, from 0.
""", ["mui_get_value", "mui_register_begin"]),
    "mui_slider": _f("""\
- `min`, `max`: los extremos.
- `value`: el valor con el que empieza.

Un deslizador horizontal. `mui_get_value` da su valor; `mui_on_change` avisa mientras se mueve.
""", """\
- `min`, `max`: the ends.
- `value`: the starting value.

A horizontal slider. `mui_get_value` gives its value; `mui_on_change` fires while it moves.
""", ["mui_gauge", "mui_get_value"]),
    "mui_gauge": _f("""\
- `max`: el valor de la barra llena.

Una barra de progreso, vacía al principio. `mui_set_value(barra, n)` la llena hasta `n`.
""", """\
- `max`: the value of the full bar.

A progress bar, empty at the start. `mui_set_value(bar, n)` fills it up to `n`.
""", ["mui_set_value"]),
    "mui_get_value": _f("""\
- `obj`: el objeto.

Devuelve su valor: casilla 1 o 0; la opción de un ciclo o la pestaña, desde 0; el nivel de un deslizador o de una
barra; la línea elegida de una lista (-1 ninguna); la marca de una opción de menú; la posición de una barra de
desplazamiento. 0 en un objeto sin valor.
""", """\
- `obj`: the object.

Returns its value: checkbox 1 or 0; a cycle's option or the tab, from 0; a slider's or a gauge's level; a list's
chosen line (-1 none); a menu item's check mark; a scroll bar's position. 0 on an object without a value.
""", ["mui_set_value", "mui_get_text"]),
    "mui_set_value": _f("""\
- `obj`: el objeto.
- `value`: el valor nuevo, como en `mui_get_value`.

Cambia el valor. Lanza el evento de `mui_on_change` como si lo hubiera hecho el usuario.
""", """\
- `obj`: the object.
- `value`: the new value, as in `mui_get_value`.

Changes the value. It fires the `mui_on_change` event as if the user had done it.
""", ["mui_get_value", "mui_on_change"]),
    "mui_get_text": _f("""\
- `obj`: un campo de texto, un texto, un botón o una ventana.

Devuelve su texto (en una ventana, el título).
""", """\
- `obj`: a text field, a text, a button or a window.

Returns its text (for a window, the title).
""", ["mui_set_text", "mui_get_value"]),
    "mui_set_text": _f("""\
- `obj`: un campo de texto, un texto, un botón, una opción de menú, una imagen o una ventana.
- `text`: el texto nuevo (en una imagen, el fichero).

Cambia su texto; en una ventana, el título.
""", """\
- `obj`: a text field, a text, a button, a menu item, a picture or a window.
- `text`: the new text (for a picture, the file).

Changes its text; for a window, the title.
""", ["mui_get_text"]),
    "mui_set_enabled": _f("""\
- `obj`: un objeto, una opción de menú o un menú entero.
- `enabled`: `false` lo desactiva (en gris, no responde); `true` lo vuelve a activar.
""", """\
- `obj`: an object, a menu item or a whole menu.
- `enabled`: `false` disables it (greyed out, no response); `true` enables it again.
""", ["mui_set_visible"]),
    "mui_set_visible": _f("""\
- `obj`: el objeto o el grupo.
- `visible`: `false` lo oculta, `true` lo enseña.

La ventana se recoloca para dar o quitar su sitio.
""", """\
- `obj`: the object or the group.
- `visible`: `false` hides it, `true` shows it.

The window lays itself out again to give or take its space.
""", ["mui_set_enabled"]),
    "mui_set_background": _f("""\
- `obj`: un grupo, un texto, una etiqueta, un botón, una lista o una ventana.
- `r`, `g`, `b`: el color, de 0 a 255.

Un fondo de ese color. Los objetos de dentro lo toman si no tienen el suyo.
""", """\
- `obj`: a group, a text, a label, a button, a list or a window.
- `r`, `g`, `b`: the colour, from 0 to 255.

A background in that colour. The objects inside take it if they have none of their own.
""", ["mui_set_text_pen"]),
    "mui_set_text_pen": _f("""\
- `obj`: un texto, una etiqueta o un botón.
- `r`, `g`, `b`: el color, de 0 a 255.

El color de su texto; se mantiene tras un `mui_set_text`.
""", """\
- `obj`: a text, a label or a button.
- `r`, `g`, `b`: the colour, from 0 to 255.

The colour of its text; it stays after a `mui_set_text`.
""", ["mui_set_background"]),
    "mui_help": _f("""\
- `obj`: el objeto.
- `text`: la ayuda.

Una burbuja con el texto, que sale cuando el puntero se para un momento sobre el objeto.
""", """\
- `obj`: the object.
- `text`: the help.

A bubble with the text, shown when the pointer rests a moment over the object.
""", []),
    "mui_set_active": _f("""\
- `win`: la ventana.
- `obj`: un objeto de ella, normalmente un campo de texto.

Lo hace el objeto activo: el cursor va a ese campo y se puede escribir sin hacer clic.
""", """\
- `win`: the window.
- `obj`: one of its objects, usually a text field.

Makes it the active object: the cursor goes to that field and you can type without clicking.
""", ["mui_string"]),
    "mui_width": _f("""\
- `obj`: el objeto.

Devuelve su ancho en la pantalla en píxeles; 0 antes de abrirse su ventana.
""", """\
- `obj`: the object.

Returns its on-screen width in pixels; 0 before its window opens.
""", ["mui_height"]),
    "mui_height": _f("""\
- `obj`: el objeto.

Devuelve su alto en la pantalla en píxeles; 0 antes de abrirse su ventana.
""", """\
- `obj`: the object.

Returns its on-screen height in pixels; 0 before its window opens.
""", ["mui_width"]),
    # ------------------------------------------------------------ listas
    "mui_list": _f("""\
Una lista de textos con su barra de desplazamiento. Su valor (`mui_get_value`) es la línea elegida, desde 0, o -1
si no hay ninguna; `mui_on_change` avisa al elegir y `mui_on_double` con un doble clic.
""", """\
A list of texts with its scroll bar. Its value (`mui_get_value`) is the chosen line, from 0, or -1 if there is none;
`mui_on_change` fires on a choice and `mui_on_double` on a double click.
""", ["mui_list_add", "mui_on_double"]),
    "mui_list_add": _f("""\
- `list`: la lista (o un `mui_combo`).
- `text`: la línea; la lista guarda su copia.

Añade la línea al final.
""", """\
- `list`: the list (or a `mui_combo`).
- `text`: the line; the list keeps its own copy.

Adds the line at the end.
""", ["mui_list_insert", "mui_list_quiet"]),
    "mui_list_insert": _f("""\
- `list`: la lista.
- `pos`: dónde, desde 0; las de después bajan.
- `text`: la línea.
""", """\
- `list`: the list.
- `pos`: where, from 0; the following ones move down.
- `text`: the line.
""", ["mui_list_add"]),
    "mui_list_remove": _f("""\
- `list`: la lista.
- `pos`: la línea que se quita, desde 0.
""", """\
- `list`: the list.
- `pos`: the line to remove, from 0.
""", ["mui_list_clear"]),
    "mui_list_clear": _f("- `list`: la lista.\n\nQuita todas las líneas.\n",
                         "- `list`: the list.\n\nRemoves every line.\n", ["mui_list_remove"]),
    "mui_list_count": _f("- `list`: la lista.\n\nDevuelve cuántas líneas tiene.\n",
                         "- `list`: the list.\n\nReturns how many lines it has.\n", ["mui_list_get"]),
    "mui_list_get": _f("""\
- `list`: la lista.
- `pos`: la línea, desde 0.

Devuelve su texto; `""` si no existe esa línea.
""", """\
- `list`: the list.
- `pos`: the line, from 0.

Returns its text; `""` if there is no such line.
""", ["mui_list_count", "mui_get_value"]),
    "mui_list_quiet": _f("""\
- `list`: la lista.
- `quiet`: `true` deja de redibujarla; `false` la redibuja con todo lo nuevo.

Para añadir muchas líneas de golpe sin que se vea cada una.
""", """\
- `list`: the list.
- `quiet`: `true` stops redrawing it; `false` redraws it with everything new.

To add many lines at once without each one being drawn.
""", ["mui_list_add"]),
    # ------------------------------------------------------------ eventos
    "mui_on_press": _f("""\
- `obj`: un botón (o un botón con imagen).
- `id`: el número de evento, mayor que 0.

Desde ahora, al pulsar el botón `mui_wait_event` devuelve `id`.
""", """\
- `obj`: a button (or a picture button).
- `id`: the event number, greater than 0.

From now on, pressing the button makes `mui_wait_event` return `id`.
""", ["mui_wait_event", "mui_press"]),
    "mui_on_change": _f("""\
- `obj`: el objeto.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` cuando cambia su valor o su texto: una casilla, un ciclo, un deslizador, la línea de
una lista, la pestaña, un campo de texto.
""", """\
- `obj`: the object.
- `id`: the event number.

`mui_wait_event` returns `id` when its value or text changes: a checkbox, a cycle, a slider, a list's line, the
tab, a text field.
""", ["mui_get_value", "mui_on_ack"]),
    "mui_on_ack": _f("""\
- `obj`: un campo de texto, un `mui_text_editor` o un `mui_combo`.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` al pulsar Return en el campo (Amiga+Return en el de varias líneas; en un combo,
también al elegir una línea).
""", """\
- `obj`: a text field, a `mui_text_editor` or a `mui_combo`.
- `id`: the event number.

`mui_wait_event` returns `id` when Return is pressed in the field (Amiga+Return in the multi-line one; in a combo,
also on choosing a line).
""", ["mui_on_change", "mui_string"]),
    "mui_on_double": _f("""\
- `list`: la lista.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` con un doble clic en una línea; `mui_get_value` dice cuál.
""", """\
- `list`: the list.
- `id`: the event number.

`mui_wait_event` returns `id` on a double click on a line; `mui_get_value` says which.
""", ["mui_list"]),
    "mui_on_close": _f("""\
- `win`: la ventana.
- `id`: el número de evento.

`mui_wait_event` devuelve `id` al pulsar el botón de cerrar de esa ventana; la ventana no se cierra sola. Sin
llamarla, cerrar la primera ventana devuelve -1 (salir) y las demás se cierran sin dar evento.
""", """\
- `win`: the window.
- `id`: the event number.

`mui_wait_event` returns `id` when that window's close button is pressed; the window does not close by itself.
Without calling it, closing the first window returns -1 (quit) and the others just close, with no event.
""", ["mui_window_close", "mui_wait_event"]),
    "mui_on_drop": _f("""\
- `obj`: el objeto, o una ventana (en cualquier sitio de ella).
- `id`: el número de evento.

`mui_wait_event` devuelve `id` cuando se sueltan iconos del Workbench sobre el objeto. `app_drop` da sus rutas.
""", """\
- `obj`: the object, or a window (anywhere on it).
- `id`: the event number.

`mui_wait_event` returns `id` when Workbench icons are dropped on the object. `app_drop` gives their paths.
""", ["app_drop"]),
    "mui_press": _f("""\
- `obj`: un botón.

Lanza su evento de `mui_on_press` como si se hubiera pulsado. Para atajos propios y para las pruebas.
""", """\
- `obj`: a button.

Fires its `mui_on_press` event as if it had been pressed. For shortcuts of your own and for tests.
""", ["mui_on_press"]),
    "mui_wait_event": _f("""\
Espera, sin gastar CPU, hasta el siguiente evento y devuelve su número; -1 para salir (el botón de cerrar de la
primera ventana sin `mui_on_close`, la orden ARexx QUIT, Exchange). Va en el bucle principal:
`while ev != -1`.
""", """\
Waits, using no CPU, for the next event and returns its number; -1 to quit (the first window's close button without
`mui_on_close`, the ARexx QUIT command, Exchange). It goes in the main loop: `while ev != -1`.
""", ["mui_poll_event", "mui_wait_event_signals", "mui_timer"]),
    "mui_poll_event": _f("""\
Como `mui_wait_event` sin esperar: devuelve 0 si no hay evento. Para un bucle que hace otras cosas a la vez; si
solo espera, `mui_wait_event` o `mui_timer` gastan menos.
""", """\
Like `mui_wait_event` without waiting: returns 0 if there is no event. For a loop that does other things at the same
time; if it only waits, `mui_wait_event` or `mui_timer` use less.
""", ["mui_wait_event"]),
    "mui_wait_event_signals": _f("""\
- `mask`: las señales que también despiertan: `net_signal()` (red), `task_signal()` (tareas),
  `file_notify_signal()` (ficheros vigilados), sumadas con `|`.

Como `mui_wait_event`, pero devuelve 0 cuando llega una de esas señales; `mui_signals()` dice cuáles.
""", """\
- `mask`: the signals that also wake it: `net_signal()` (network), `task_signal()` (tasks), `file_notify_signal()`
  (watched files), joined with `|`.

Like `mui_wait_event`, but returns 0 when one of those signals arrives; `mui_signals()` says which.
""", ["mui_signals", "mui_wait_event"]),
    "mui_signals": _f("""\
Devuelve las señales de la máscara que despertaron al último `mui_wait_event_signals`: se mira con `&`.
""", """\
Returns the mask signals that woke the last `mui_wait_event_signals`: check them with `&`.
""", ["mui_wait_event_signals"]),
    "mui_timer": _f("""\
- `ms`: dentro de cuántos milisegundos; 0 anula el que hubiera.
- `id`: el número de evento.

`mui_wait_event` devolverá `id` una vez pasado ese tiempo. Para que se repita, se vuelve a llamar al recibirlo.
""", """\
- `ms`: in how many milliseconds; 0 cancels any pending one.
- `id`: the event number.

`mui_wait_event` will return `id` once that time has passed. To repeat it, call it again when it arrives.
""", ["mui_wait_event"]),
    # ------------------------------------------------------------ menús
    "mui_menu_begin": _f("""\
- `title`: el título del menú en la barra.

Empieza un menú de la ventana que se está describiendo (entre `mui_window_begin` y `mui_window_end`). Sus opciones
van hasta `mui_menu_end`.
""", """\
- `title`: the menu's title on the bar.

Starts a menu of the window being described (between `mui_window_begin` and `mui_window_end`). Its items go up to
`mui_menu_end`.
""", ["mui_menu_item", "mui_menu_end"]),
    "mui_menu_item": _f("""\
- `title`: el texto de la opción.
- `key`: la letra del atajo con Amiga (`"S"` = Amiga+S); `""` ninguna.
- `id`: el número de evento que da al elegirla.

Una opción del menú abierto. Devuelve la opción, para `mui_set_enabled` o `mui_set_text`.
""", """\
- `title`: the item's text.
- `key`: the shortcut letter with Amiga (`"S"` = Amiga+S); `""` none.
- `id`: the event number it gives when chosen.

An item of the open menu. Returns the item, for `mui_set_enabled` or `mui_set_text`.
""", ["mui_menu_check", "mui_menu_separator"]),
    "mui_menu_check": _f("""\
- `title`, `key`, `id`: como en `mui_menu_item`.
- `checked`: si empieza marcada.

Una opción con marca: elegirla cambia la marca y da `id`. `mui_get_value` y `mui_set_value` leen y ponen la marca.
""", """\
- `title`, `key`, `id`: as in `mui_menu_item`.
- `checked`: whether it starts checked.

An item with a check mark: choosing it toggles the mark and gives `id`. `mui_get_value` and `mui_set_value` read
and set the mark.
""", ["mui_menu_item"]),
    "mui_menu_separator": _f("Una raya entre opciones del menú.\n", "A line between menu items.\n",
                             ["mui_menu_item"]),
    "mui_submenu_begin": _f("""\
- `title`: el texto de la opción que abre el submenú.

Empieza un submenú dentro del menú abierto; sus opciones van hasta `mui_submenu_end`. Un solo nivel.
""", """\
- `title`: the text of the item that opens the submenu.

Starts a submenu inside the open menu; its items go up to `mui_submenu_end`. One level only.
""", ["mui_submenu_end"]),
    "mui_submenu_end": _f("Acaba el submenú.\n", "Ends the submenu.\n", ["mui_submenu_begin"]),
    "mui_menu_end": _f("Acaba el menú abierto, o el menú contextual.\n", "Ends the open menu, or the context menu.\n",
                       ["mui_menu_begin", "mui_context_menu_begin"]),
    "mui_context_menu_begin": _f("""\
- `title`: el título del menú.

Empieza un menú contextual, en cualquier sitio del programa; sus opciones como en un menú, hasta `mui_menu_end`.
Devuelve el menú, para `mui_set_context_menu`.
""", """\
- `title`: the menu's title.

Starts a context menu, anywhere in the program; its items as in a menu, up to `mui_menu_end`. Returns the menu, for
`mui_set_context_menu`.
""", ["mui_set_context_menu", "mui_menu_item"]),
    "mui_set_context_menu": _f("""\
- `object`: el objeto.
- `menu`: el menú de `mui_context_menu_begin`; 0 = ninguno.

El botón derecho sobre el objeto abre ese menú, y sus opciones dan sus eventos. En una zona de dibujo,
`mui_canvas_mouse_x` y `_y` dicen dónde se pulsó.
""", """\
- `object`: the object.
- `menu`: the menu from `mui_context_menu_begin`; 0 = none.

The right button over the object opens that menu, and its items give their events. On a drawing area,
`mui_canvas_mouse_x` and `_y` say where it was pressed.
""", ["mui_context_menu_begin"]),
}
