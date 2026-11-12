"""Entrada (teclado, ratón, joystick) y pantallas (INPUT_FUNCTIONS)."""

GROUPS = {
    "INPUT_FUNCTIONS": {
        "es": """\
El teclado, el ratón y el joystick, y las pantallas propias del programa.

**Dos formas de leer la entrada.**

- **Por eventos**, en un programa con ventanas: el `EventLoop` recibe `On Key`, `On Click`, `On Gadget`... y el
  programa no gasta CPU mientras espera (manual, secciones 12 y 14). `key_wait` y `wait_key` esperan una tecla de la
  misma forma, sin bucle.
- **Preguntando**, en un juego: en cada vuelta del bucle principal se mira cómo están ahora las teclas
  (`key_down`), el joystick (`joy_*`) y los botones del ratón (`mouse_button`). Estas leen el hardware o el
  teclado del sistema: no necesitan ventana, pero tampoco miran cuál está activa.

**Códigos de tecla.** Las funciones de teclado usan el código en bruto de la tecla, el mismo en todos los mapas
de teclado: 0x45 Esc, 0x40 espacio, 0x44 Return, 0x41 retroceso, 0x4C arriba, 0x4D abajo, 0x4E derecha, 0x4F
izquierda, 0x50 a 0x59 F1 a F10. `key_text` dice qué letra da una tecla con el mapa que haya puesto.

**El joystick** va en el puerto 1, el de siempre. El puerto 0 es el del ratón: solo sirve si se enchufa ahí un
segundo joystick.

**Pantallas.** Una pantalla propia tiene su paleta, su resolución y su profundidad, sin molestar al Workbench. Se
abre una (`screen_open`, `screen_open_custom`, `screen_open_mode`), se abren en ella las ventanas o se dibuja
directamente, y al acabar se cierran las ventanas y luego la pantalla. Hay una sola a la vez. Para animar sin
parpadeo, `screen_double_buffer` y `screen_flip`.
""",
        "en": """\
The keyboard, the mouse and the joystick, and the program's own screens.

**Two ways to read input.**

- **By events**, in a program with windows: the `EventLoop` gets `On Key`, `On Click`, `On Gadget`... and the
  program uses no CPU while it waits (manual, sections 12 and 14). `key_wait` and `wait_key` wait for a key the
  same way, without a loop.
- **By asking**, in a game: every turn of the main loop looks at how the keys (`key_down`), the joystick (`joy_*`)
  and the mouse buttons (`mouse_button`) are right now. These read the hardware or the system's keyboard: they need
  no window, but they do not look at which one is active either.

**Key codes.** The keyboard functions use the key's raw code, the same on every keymap: 0x45 Esc, 0x40 space,
0x44 Return, 0x41 backspace, 0x4C up, 0x4D down, 0x4E right, 0x4F left, 0x50 to 0x59 F1 to F10. `key_text` says
which letter a key gives with the keymap in use.

**The joystick** goes in port 1, the usual one. Port 0 is the mouse's: it is only useful with a second joystick
plugged in there.

**Screens.** A screen of your own has its palette, resolution and depth, without bothering the Workbench. Open one
(`screen_open`, `screen_open_custom`, `screen_open_mode`), open the windows on it or draw on it directly, and when
done close the windows and then the screen. There is one at a time. To animate without flicker,
`screen_double_buffer` and `screen_flip`.
""",
        "example": "tests/test_doc_entrada.dash",
    },
}

FUNCS = {
    "key_pressed": {
        "es": """\
Devuelve `true` si hay una tecla esperando en la ventana actual, sin sacarla: la recogen después `key_get` o
`key_wait`. Cuentan también las teclas soltadas. Sin ventana, `false`. Dentro de un `EventLoop` las teclas van a
`On Key`.
""",
        "en": """\
Returns `true` if a key is waiting in the current window, without taking it: `key_get` or `key_wait` pick it up
afterwards. Released keys count too. Without a window, `false`. Inside an `EventLoop` keys go to `On Key`.
""",
        "see": ["key_get", "key_wait", "key_down"],
    },
    "key_get": {
        "es": """\
Saca la siguiente tecla de la cola de la ventana actual y devuelve su código en bruto, o 0 si no hay ninguna. Al
soltar una tecla llega otra vez con 128 sumado (0x80): `if k < 128` se queda solo con las pulsaciones. La cola
guarda 16; si se llena, se pierden las más viejas.
""",
        "en": """\
Takes the next key from the current window's queue and returns its raw code, or 0 if there is none. Releasing a
key sends it again with 128 added (0x80): `if k < 128` keeps only the presses. The queue holds 16; when it is full
the oldest ones are lost.
""",
        "see": ["key_pressed", "key_wait", "key_text"],
    },
    "key_wait": {
        "es": """\
Espera a que se pulse una tecla en la ventana actual y devuelve su código en bruto. No gasta CPU mientras espera.
Las teclas soltadas no cuentan. Sin ventana devuelve 0 enseguida.
""",
        "en": """\
Waits for a key press in the current window and returns its raw code. It uses no CPU while it waits. Released keys
do not count. Without a window it returns 0 at once.
""",
        "see": ["key_get", "wait_key", "key_text"],
    },
    "key_raw": {
        "es": """\
Devuelve el código en bruto de la última tecla leída, con `key_get`, `key_wait` o un `On Key`. No mira el
teclado: para saber si una tecla está pulsada ahora, `key_down`.
""",
        "en": """\
Returns the raw code of the last key read, with `key_get`, `key_wait` or an `On Key`. It does not look at the
keyboard: to know whether a key is held now, `key_down`.
""",
        "see": ["key_get", "key_down"],
    },
    "key_down": {
        "es": """\
- `code`: el código en bruto de la tecla, de 0 a 127.

Devuelve `true` si esa tecla está pulsada ahora mismo. Lee el estado del teclado del sistema: no necesita ventana
y no consume nada de la cola. Es lo que va en el bucle de un juego, una vez por fotograma. Ojo: ve las teclas
aunque el programa no sea el activo.
""",
        "en": """\
- `code`: the key's raw code, from 0 to 127.

Returns `true` if that key is held right now. It reads the system's keyboard state: it needs no window and takes
nothing from the queue. It is what goes in a game loop, once per frame. Note: it sees keys even when the program
is not the active one.
""",
        "see": ["joy_x", "key_get", "check_esc"],
    },
    "key_text": {
        "es": """\
- `keycode`: un código en bruto de tecla.

Devuelve el texto que da esa tecla con el mapa de teclado puesto, sin Mayúsculas: `key_text(0x20)` es `"a"`.
`""` para las teclas sin letra, como las flechas o las de función.
""",
        "en": """\
- `keycode`: a raw key code.

Returns the text that key gives with the keymap in use, without Shift: `key_text(0x20)` is `"a"`. `""` for keys
without a letter, like the arrows or the function keys.
""",
        "see": ["key_get", "key_raw"],
    },
    "mouse_x": {
        "es": """\
Devuelve la X del puntero contando desde la esquina de dentro de los bordes de la ventana actual, como los
`gfx_*`. Puede ser negativa o pasar del ancho si el puntero está fuera. Sin ventana, 0.
""",
        "en": """\
Returns the pointer's X counting from the corner inside the current window's borders, like the `gfx_*` functions.
It can be negative or beyond the width when the pointer is outside. Without a window, 0.
""",
        "see": ["mouse_y", "mouse_button", "click_x"],
    },
    "mouse_y": {
        "es": "Devuelve la Y del puntero dentro de la ventana actual, como `mouse_x`. Sin ventana, 0.\n",
        "en": "Returns the pointer's Y inside the current window, like `mouse_x`. Without a window, 0.\n",
        "see": ["mouse_x"],
    },
    "mouse_button": {
        "es": """\
- `btn`: 0 el izquierdo, 1 el derecho.

Devuelve `true` si ese botón está pulsado ahora. Lee el hardware del puerto del ratón: no necesita ventana y ve
los clics en cualquier sitio de la pantalla. En un programa con ventana, `On Click` es mejor.
""",
        "en": """\
- `btn`: 0 the left one, 1 the right one.

Returns `true` if that button is held now. It reads the mouse port's hardware: it needs no window and sees clicks
anywhere on the screen. In a program with a window, `On Click` is better.
""",
        "see": ["mouse_x", "check_lmb", "wait_click"],
    },
    "event_window": {
        "es": """\
Dentro de un `EventLoop`, devuelve de qué ventana vino el evento: el número de `window_create`, o 0 si fue de la
ventana del propio bucle. Sirve para cerrar solo esa ventana en su `On Close`.
""",
        "en": """\
Inside an `EventLoop`, returns which window the event came from: the `window_create` number, or 0 if it was the
loop's own window. Useful to close only that window in its `On Close`.
""",
        "see": ["window_create", "gadget_id"],
    },
    "window_check_close": {
        "es": """\
Devuelve `true` si se pulsó el botón de cerrar de la ventana actual desde la última vez que se miró, sin esperar.
Para un bucle propio, sin `EventLoop`: `while not window_check_close()`.
""",
        "en": """\
Returns `true` if the current window's close button was pressed since the last look, without waiting. For a loop
of your own, without an `EventLoop`: `while not window_check_close()`.
""",
        "see": ["close_window", "key_get"],
    },
    "close_window": {
        "es": """\
Cierra la ventana actual, sea declarada o de `window_create`. Después no queda ventana actual.
""",
        "en": """\
Closes the current window, declared or from `window_create`. Afterwards there is no current window.
""",
        "see": ["window_close", "window_check_close"],
    },
    "screen_open": {
        "es": """\
- `depth`: la profundidad: 1 = 2 colores, 2 = 4, 3 = 8, 4 = 16, 5 = 32, 8 = 256 (AGA o tarjeta gráfica).
- `title`: el título de la barra de la pantalla.

Abre una pantalla con el modo y el tamaño del Workbench y la profundidad que se diga. Las ventanas que se abran
después van en ella y, sin ventana, los `gfx_*` dibujan en la pantalla. Devuelve `false` si no se pudo abrir. Solo
una pantalla a la vez: cierra la anterior antes de abrir otra.
""",
        "en": """\
- `depth`: the depth: 1 = 2 colours, 2 = 4, 3 = 8, 4 = 16, 5 = 32, 8 = 256 (AGA or a graphics card).
- `title`: the title on the screen's bar.

Opens a screen with the Workbench's mode and size and the given depth. Windows opened afterwards go on it and,
without a window, the `gfx_*` functions draw on the screen. Returns `false` if it could not be opened. One screen at
a time: close the old one before opening another.
""",
        "see": ["screen_open_custom", "screen_open_mode", "screen_close"],
    },
    "screen_open_custom": {
        "es": """\
- `width`, `height`: el tamaño en píxeles: 320 x 256 es PAL de baja resolución, 640 x 256 la de alta.
- `depth`: la profundidad, como en `screen_open`.
- `title`: el título.

Abre una pantalla de ese tamaño; el sistema elige el modo que mejor le cuadra (sin HAM ni medio brillo). Devuelve
`false` si no se pudo abrir.
""",
        "en": """\
- `width`, `height`: the size in pixels: 320 x 256 is PAL low resolution, 640 x 256 high.
- `depth`: the depth, as in `screen_open`.
- `title`: the title.

Opens a screen of that size; the system picks the mode that fits best (no HAM or half-brite). Returns `false` if it
could not be opened.
""",
        "see": ["screen_open", "screen_close", "gfx_rgb"],
    },
    "screen_open_mode": {
        "es": """\
- `mode`: el modo exacto: el de `dialog_screen_mode` (`screen_mode_id`), o uno conocido: 0x21000 PAL baja
  resolución, 0x29000 PAL alta.
- `width`, `height`, `depth`: tamaño y profundidad.
- `title`: el título.

Abre la pantalla en ese modo. Devuelve `false` si el modo no existe en esta máquina, no admite esa profundidad o ya
hay una pantalla abierta.
""",
        "en": """\
- `mode`: the exact mode: the one from `dialog_screen_mode` (`screen_mode_id`), or a known one: 0x21000 PAL low
  resolution, 0x29000 PAL high.
- `width`, `height`, `depth`: size and depth.
- `title`: the title.

Opens the screen in that mode. Returns `false` if the mode does not exist on this machine, does not allow that depth
or a screen is already open.
""",
        "see": ["dialog_screen_mode", "screen_open_custom"],
    },
    "screen_clone_wb": {
        "es": """\
- `name`: el nombre público de la pantalla.

Abre una pantalla pública igual que la del Workbench (modo, tamaño, profundidad, lápices y fuente) con ese nombre.
Otros programas pueden abrir ventanas en ella si se lo dicen. Devuelve `false` si el nombre ya existe o ya hay una
pantalla abierta. `screen_close` espera a que los demás cierren sus ventanas, un minuto como mucho; si siguen
abiertas, la deja.
""",
        "en": """\
- `name`: the screen's public name.

Opens a public screen like the Workbench's (mode, size, depth, pens and font) with that name. Other programs can
open windows on it when told to. Returns `false` if the name already exists or a screen is already open.
`screen_close` waits for the others to close their windows, a minute at most; if they are still open, it leaves it.
""",
        "see": ["screen_visitors", "screen_make_default", "screen_close"],
    },
    "screen_visitors": {
        "es": """\
Devuelve cuántas ventanas y bloqueos de otros programas hay en la pantalla pública del programa
(`screen_clone_wb`); una ventana de MUI puede contar dos. 0 si no hay ninguno o no hay pantalla pública.
""",
        "en": """\
Returns how many windows and locks of other programs there are on the program's public screen
(`screen_clone_wb`); a MUI window can count as two. 0 if there are none or there is no public screen.
""",
        "see": ["screen_clone_wb"],
    },
    "screen_make_default": {
        "es": """\
Hace de la pantalla pública del programa (`screen_clone_wb`) la pública por defecto: ahí se abren las ventanas que
no dicen pantalla, como las de los programas que lance o una consola. `screen_close` deja la de antes. Devuelve
`false` si no hay pantalla pública.
""",
        "en": """\
Makes the program's public screen (`screen_clone_wb`) the default public one: windows that do not name a screen,
like those of programs it launches or a console, open there. `screen_close` puts the old one back. Returns `false`
if there is no public screen.
""",
        "see": ["screen_clone_wb"],
    },
    "screen_double_buffer": {
        "es": """\
Prepara dos imágenes para la pantalla propia: desde ahora los `gfx_*` dibujan en la escondida y `screen_flip` la
enseña. Así se ve cada fotograma entero, sin parpadeo. Se dibuja sobre la pantalla, no en ventanas: es para juegos
y demos a pantalla completa. Devuelve `false` sin pantalla propia, con una pública (`screen_clone_wb`) o antes de
AmigaOS 3.0. Llamarlo otra vez no hace nada.
""",
        "en": """\
Sets up two pictures for the program's own screen: from now on the `gfx_*` functions draw on the hidden one and
`screen_flip` shows it. Each frame is seen whole, without flicker. Drawing goes on the screen, not in windows: it is
for full-screen games and demos. Returns `false` without a screen of its own, with a public one (`screen_clone_wb`)
or before AmigaOS 3.0. Calling it again does nothing.
""",
        "see": ["screen_flip", "screen_open_custom"],
    },
    "screen_flip": {
        "es": """\
Enseña lo dibujado en la imagen escondida y pasa a dibujar en la otra. Espera a la pantalla, un fotograma como
mucho, así que marca el ritmo del bucle: 50 vueltas por segundo en PAL. La imagen nueva tiene lo de hace dos
fotogramas: hay que borrar o repintar lo que se mueve. Devuelve `false` si ahora no pudo cambiarla.
""",
        "en": """\
Shows what was drawn on the hidden picture and moves on to drawing on the other one. It waits for the display, one
frame at most, so it sets the pace of the loop: 50 turns a second on PAL. The new picture holds what was there two
frames ago: what moves has to be cleared or repainted. Returns `false` if it could not swap now.
""",
        "see": ["screen_double_buffer"],
    },
    "screen_close": {
        "es": """\
Cierra la pantalla propia. Antes hay que cerrar las ventanas que haya en ella. Sin pantalla propia no hace nada.
""",
        "en": """\
Closes the program's own screen. Close the windows on it first. Without a screen of its own it does nothing.
""",
        "see": ["screen_open", "window_close"],
    },
    "screen_width": {
        "es": "Devuelve el ancho en píxeles de la pantalla propia o, si no hay, de la pantalla de la ventana actual. Sin ninguna, el de la pantalla pública donde se abriría una ventana (el Workbench, por lo general): sirve para medir una ventana antes de abrirla.\n",
        "en": "Returns the width in pixels of the program's screen or, without one, of the current window's screen. With neither, that of the public screen where a window would open (the Workbench, as a rule): it helps to size a window before opening it.\n",
        "see": ["screen_height"],
    },
    "screen_height": {
        "es": "Devuelve el alto en píxeles de la pantalla propia o de la de la ventana actual. Sin ninguna, el de la pantalla pública donde se abriría una ventana.\n",
        "en": "Returns the height in pixels of the program's screen or of the current window's. With neither, that of the public screen where a window would open.\n",
        "see": ["screen_width"],
    },
    "check_lmb": {
        "es": "Devuelve `true` si el botón izquierdo del ratón está pulsado ahora. Es `mouse_button(0)`.\n",
        "en": "Returns `true` if the left mouse button is held now. It is `mouse_button(0)`.\n",
        "see": ["mouse_button", "check_rmb"],
    },
    "check_rmb": {
        "es": "Devuelve `true` si el botón derecho del ratón está pulsado ahora. Es `mouse_button(1)`.\n",
        "en": "Returns `true` if the right mouse button is held now. It is `mouse_button(1)`.\n",
        "see": ["mouse_button", "check_lmb"],
    },
    "check_mouse": {
        "es": "Devuelve `true` si está pulsado alguno de los dos botones del ratón.\n",
        "en": "Returns `true` if either mouse button is held.\n",
        "see": ["mouse_button"],
    },
    "check_esc": {
        "es": """\
Devuelve `true` si lo último que mandó el teclado fue Esc pulsada. Si a la vez se pulsa otra tecla, deja de verla:
`key_down(0x45)` es más fiable.
""",
        "en": """\
Returns `true` if the last thing the keyboard sent was Esc pressed. If another key is pressed meanwhile it stops
seeing it: `key_down(0x45)` is more reliable.
""",
        "see": ["key_down"],
    },
    "wait_click": {
        "es": """\
Espera a que se pulse y se suelte un botón del ratón, en cualquier sitio de la pantalla. Mira el ratón 50 veces
por segundo. Devuelve 1. En un programa con ventana, `On Click` dice además dónde fue.
""",
        "en": """\
Waits for a mouse button to be pressed and released, anywhere on the screen. It looks at the mouse 50 times a
second. Returns 1. In a program with a window, `On Click` also says where it was.
""",
        "see": ["mouse_button", "wait_key"],
    },
    "wait_key": {
        "es": """\
Espera a que se pulse una tecla en la ventana actual y devuelve su código en bruto. Los demás mensajes de la
ventana (el botón de cerrar, por ejemplo) se pierden mientras espera. Sin ventana, espera un segundo y devuelve 0.
""",
        "en": """\
Waits for a key press in the current window and returns its raw code. The window's other messages (the close
button, for instance) are lost while it waits. Without a window, it waits one second and returns 0.
""",
        "see": ["key_wait", "wait_click"],
    },
    "joy_x": {
        "es": """\
- `port`: 1 el puerto del joystick; 0 el del ratón.

Devuelve -1 si el joystick está a la izquierda, 1 a la derecha y 0 en el centro. Se mira en cada fotograma.
""",
        "en": """\
- `port`: 1 the joystick port; 0 the mouse's.

Returns -1 if the joystick is pushed left, 1 right and 0 in the middle. Check it every frame.
""",
        "see": ["joy_y", "joy_fire", "key_down"],
    },
    "joy_y": {
        "es": "- `port`: 1 el puerto del joystick; 0 el del ratón.\n\nDevuelve -1 arriba, 1 abajo y 0 en el centro.\n",
        "en": "- `port`: 1 the joystick port; 0 the mouse's.\n\nReturns -1 up, 1 down and 0 in the middle.\n",
        "see": ["joy_x"],
    },
    "joy_button": {
        "es": """\
- `port`: 1 el puerto del joystick; 0 el del ratón.

Devuelve `true` si el botón de disparo está pulsado. En el puerto 0 es también el botón izquierdo del ratón.
""",
        "en": """\
- `port`: 1 the joystick port; 0 the mouse's.

Returns `true` if the fire button is held. On port 0 it is also the left mouse button.
""",
        "see": ["joy_fire"],
    },
    "joy_up": {
        "es": "- `port`: el puerto, 1 normalmente.\n\nDevuelve `true` si el joystick está hacia arriba (también en diagonal).\n",
        "en": "- `port`: the port, normally 1.\n\nReturns `true` if the joystick is pushed up (diagonals too).\n",
        "see": ["joy_y"],
    },
    "joy_down": {
        "es": "- `port`: el puerto, 1 normalmente.\n\nDevuelve `true` si el joystick está hacia abajo (también en diagonal).\n",
        "en": "- `port`: the port, normally 1.\n\nReturns `true` if the joystick is pushed down (diagonals too).\n",
        "see": ["joy_y"],
    },
    "joy_left": {
        "es": "- `port`: el puerto, 1 normalmente.\n\nDevuelve `true` si el joystick está a la izquierda (también en diagonal).\n",
        "en": "- `port`: the port, normally 1.\n\nReturns `true` if the joystick is pushed left (diagonals too).\n",
        "see": ["joy_x"],
    },
    "joy_right": {
        "es": "- `port`: el puerto, 1 normalmente.\n\nDevuelve `true` si el joystick está a la derecha (también en diagonal).\n",
        "en": "- `port`: the port, normally 1.\n\nReturns `true` if the joystick is pushed right (diagonals too).\n",
        "see": ["joy_x"],
    },
    "joy_fire": {
        "es": "- `port`: el puerto, 1 normalmente.\n\nDevuelve `true` si el botón de disparo está pulsado. Es `joy_button`.\n",
        "en": "- `port`: the port, normally 1.\n\nReturns `true` if the fire button is held. It is `joy_button`.\n",
        "see": ["joy_button"],
    },
}
