"""3D con MiniGL (GL_FUNCTIONS)."""

GROUPS = {
    "GL_FUNCTIONS": {
        "es": """\
3D con MiniGL, la parte de OpenGL 1.x del Amiga, a través de `minigl.library` 29 o más: MiniGL Classic encima de
Warp3D (tarjetas 3D clásicas, QuarkTex en WinUAE o Wazp3D, por software), PiStorm3D en un PiStorm32 con una Pi 4, o
RadeonGL. La biblioteca necesita una FPU; los programas también van sin `--fpu`, pero con `--fpu` sus cuentas son
mucho más rápidas.

`gl_open(ancho, alto)` abre una ventana con doble búfer y Z-buffer, y da `false` si falta la biblioteca o la FPU.
Cada fotograma: `gl_clear`, las matrices (`gl_load_identity`, `gl_translate`, `gl_rotate`...), las figuras entre
`gl_begin` y `gl_end` con `gl_color` y `gl_vertex`, y `gl_swap` para enseñarlo. Los números de los estados y las
figuras (`GL_TRIANGLES`, `GL_DEPTH_TEST`...) están en `lib/amiga/gl.dash`. Detalles, rendimiento y lo que falta en
[MINIGL.md](MINIGL.md).
""",
        "en": """\
3D with MiniGL, the Amiga's part of OpenGL 1.x, through `minigl.library` 29 or newer: MiniGL Classic over Warp3D
(classic 3D cards, QuarkTex in WinUAE or Wazp3D, in software), PiStorm3D on a PiStorm32 with a Pi 4, or RadeonGL. The
library needs a FPU; programs also work without `--fpu`, but with `--fpu` their maths are much faster.

`gl_open(width, height)` opens a double-buffered window with a Z buffer, and gives `false` if the library or the FPU
are missing. Each frame: `gl_clear`, the matrices (`gl_load_identity`, `gl_translate`, `gl_rotate`...), the shapes
between `gl_begin` and `gl_end` with `gl_color` and `gl_vertex`, and `gl_swap` to show it. The numbers of the states
and shapes (`GL_TRIANGLES`, `GL_DEPTH_TEST`...) are in `lib/amiga/gl.dash`. Details, speed and what is missing in
[MINIGL.en.md](MINIGL.en.md).
""",
        "example": "tests/test_doc_gl.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


FUNCS = {
    "gl_open": _f("""\
- `width`, `height`: el tamaño del dibujo en píxeles.

Abre una ventana de MiniGL en el Workbench, con doble búfer y un Z-buffer de 16 bits. Deja puesta una perspectiva de
60 grados (lo que está entre 0.5 y 100 unidades delante de la cámara, que mira hacia -z) y la matriz modelview
activa, así que `gl_translate(0, 0, -5)` ya deja ver lo que se dibuja en el origen. Si ya había una abierta, la
cierra antes.

Devuelve `false` si no está `minigl.library` 29 o más, si la máquina no tiene FPU (la biblioteca la usa) o si no se
pudo abrir. Las demás `gl_*` no hacen nada sin una ventana abierta.
""", """\
- `width`, `height`: the size of the picture in pixels.

Opens a MiniGL window on the Workbench, double buffered and with a 16-bit Z buffer. It leaves a 60 degree perspective
(what is between 0.5 and 100 units in front of the camera, which looks towards -z) and the modelview matrix current,
so `gl_translate(0, 0, -5)` already shows what is drawn at the origin. If one was open, it is closed first.

Returns `false` if `minigl.library` 29 or newer is not there, if the machine has no FPU (the library uses it) or if it
could not open. The other `gl_*` do nothing without an open window.
""", ["gl_open_screen", "gl_close", "gl_swap", "gl_closed"]),
    "gl_swap": _f("""\
Enseña lo dibujado desde el último `gl_swap` y deja el otro búfer para el fotograma siguiente. Espera al refresco de
la pantalla (`gl_vsync`), así que un bucle de dibujo va como mucho a 50 o 60 fotogramas por segundo.
""", """\
Shows what was drawn since the last `gl_swap` and leaves the other buffer for the next frame. It waits for the
screen's refresh (`gl_vsync`), so a drawing loop runs at 50 or 60 frames a second at most.
""", ["gl_vsync", "gl_clear"]),
    "gl_closed": _f("""\
Devuelve `true` desde que se pulsó el botón de cerrar de la ventana. Para el bucle de dibujo:
`while not gl_closed()`. En `gl_open_screen` no hay botón: la salida va con `gl_key` o `key_down`.
""", """\
Returns `true` once the close gadget of the window was clicked. For the drawing loop: `while not gl_closed()`. On
`gl_open_screen` there is no gadget: leave with `gl_key` or `key_down`.
""", ["gl_key", "key_down"]),
    "gl_draw_arrays": _f("""\
- `mode`: la figura, como en `gl_begin` (`GL_TRIANGLES`...).
- `vertices`: un búfer con 3 `float` por esquina (x, y, z), puestos con `buffer_set_float` o leídos de un fichero.
- `colors`: un búfer con 4 bytes por esquina (rojo, verde, azul, alfa, de 0 a 255), o 0 para usar el color de
  `gl_color`.
- `first`: la primera esquina que se dibuja, desde 0.
- `count`: cuántas esquinas.

Dibuja todas esas esquinas de una vez (`glDrawArrays`), con la matriz y el estado de ese momento: un modelo de 1200
triángulos son 3600 llamadas menos en cada fotograma. Los búferes se preparan una vez y se mueven con
`gl_mult_matrix` o `gl_translate` y `gl_rotate`. Está pensado para una tarjeta 3D (sin probar): con MiniGL Classic
sobre Wazp3D, que lo hace todo por software, no fue más rápido que `gl_vertex` (docs/MINIGL.md).
""", """\
- `mode`: the shape, as in `gl_begin` (`GL_TRIANGLES`...).
- `vertices`: a buffer with 3 `float`s per corner (x, y, z), set with `buffer_set_float` or read from a file.
- `colors`: a buffer with 4 bytes per corner (red, green, blue, alpha, 0 to 255), or 0 to use the `gl_color` one.
- `first`: the first corner drawn, from 0.
- `count`: how many corners.

Draws all those corners at once (`glDrawArrays`), with the matrix and the state of that moment: a model of 1200
triangles is 3600 calls fewer each frame. The buffers are made once and moved with `gl_mult_matrix` or `gl_translate`
and `gl_rotate`. It is meant for a 3D card (untested): with MiniGL Classic over Wazp3D, all in software, it was not
faster than `gl_vertex` (docs/MINIGL.en.md).
""", ["gl_begin", "buffer_set_float", "gl_mult_matrix"]),
    "gl_draw_elements": _f("""\
- `mode`: la figura, como en `gl_begin` (`GL_TRIANGLES`...).
- `vertices`, `colors`: como en `gl_draw_arrays` (`colors` puede ser 0).
- `nverts`: cuántas esquinas hay en `vertices`.
- `indices`: un búfer con los números de las esquinas de cada figura, 2 bytes cada uno (0 es la primera de
  `vertices`), puestos con `buffer_set_word` o leídos de un fichero.
- `count`: cuántos números se usan.

Como `gl_draw_arrays`, pero cada esquina va una sola vez en `vertices` aunque la compartan varias caras: MiniGL la
debería calcular una vez (bloquea las `nverts` esquinas con `glLockArrays` y dibuja con `glDrawElements`). Está
pensado para una tarjeta 3D (sin probar): con MiniGL Classic sobre Wazp3D fue más lento que `gl_draw_arrays`
(docs/MINIGL.md).
""", """\
- `mode`: the shape, as in `gl_begin` (`GL_TRIANGLES`...).
- `vertices`, `colors`: as in `gl_draw_arrays` (`colors` may be 0).
- `nverts`: how many corners there are in `vertices`.
- `indices`: a buffer with the numbers of the corners of each shape, 2 bytes each (0 is the first of `vertices`),
  set with `buffer_set_word` or read from a file.
- `count`: how many numbers are used.

As `gl_draw_arrays`, but each corner is only once in `vertices` however many faces share it: MiniGL should work it out
once (it locks the `nverts` corners with `glLockArrays` and draws with `glDrawElements`). It is meant for a 3D card
(untested): with MiniGL Classic over Wazp3D it was slower than `gl_draw_arrays` (docs/MINIGL.en.md).
""", ["gl_draw_arrays", "gl_mult_matrix"]),
    "gl_mult_matrix": _f("""\
- `a`, `b`, `c`, `tx`: la primera fila de la matriz.
- `d`, `e`, `f`, `ty`: la segunda.
- `g`, `h`, `i`, `tz`: la tercera (la cuarta es 0, 0, 0, 1).

Multiplica la matriz activa por esa: un giro (las 3 primeras columnas) y un desplazamiento (`tx`, `ty`, `tz`) en una
sola llamada (`glMultMatrixf`). Es lo que hace falta para los huesos de un modelo: el programa calcula la matriz de
cada hueso y la pone antes de dibujar su pieza.
""", """\
- `a`, `b`, `c`, `tx`: the first row of the matrix.
- `d`, `e`, `f`, `ty`: the second.
- `g`, `h`, `i`, `tz`: the third (the fourth is 0, 0, 0, 1).

Multiplies the current matrix by that one: a rotation (the first 3 columns) and a translation (`tx`, `ty`, `tz`) in
a single call (`glMultMatrixf`). It is what the bones of a model need: the program works out the matrix of each bone
and sets it before drawing its piece.
""", ["gl_push_matrix", "gl_draw_arrays", "gl_translate"]),
    "gl_begin": _f("""\
- `mode`: la figura, con los números de OpenGL (`lib/amiga/gl.dash`): `GL_POINTS` 0, `GL_LINES` 1, `GL_LINE_LOOP` 2,
  `GL_LINE_STRIP` 3, `GL_TRIANGLES` 4, `GL_TRIANGLE_STRIP` 5, `GL_TRIANGLE_FAN` 6, `GL_QUADS` 7, `GL_QUAD_STRIP` 8,
  `GL_POLYGON` 9.

Las esquinas van con `gl_vertex` hasta `gl_end`. Las caras de delante son las que se ven en sentido contrario a las
agujas del reloj, como en OpenGL.
""", """\
- `mode`: the shape, with OpenGL's numbers (`lib/amiga/gl.dash`): `GL_POINTS` 0, `GL_LINES` 1, `GL_LINE_LOOP` 2,
  `GL_LINE_STRIP` 3, `GL_TRIANGLES` 4, `GL_TRIANGLE_STRIP` 5, `GL_TRIANGLE_FAN` 6, `GL_QUADS` 7, `GL_QUAD_STRIP` 8,
  `GL_POLYGON` 9.

The corners go with `gl_vertex` until `gl_end`. The front faces are the ones seen counterclockwise, as in OpenGL.
""", ["gl_vertex", "gl_end", "gl_color"]),
    "gl_texture": _f("""\
- `d`: una imagen decodificada con `image_decode` (PNG, JPEG, GIF, BMP, WebP).

Devuelve el número de una textura nueva, o 0. MiniGL quiere lados de potencias de dos: la imagen se lleva a la
potencia de dos que no pasa de su tamaño, hasta 256 x 256 (el punto más cercano). Después se puede liberar la imagen
con `image_decoded_free`. Se dibuja con `gl_texture_bind` y `gl_tex_coord`; con `gl_close` las texturas se pierden.
""", """\
- `d`: an image decoded with `image_decode` (PNG, JPEG, GIF, BMP, WebP).

Returns the number of a new texture, or 0. MiniGL wants sides that are powers of two: the image is taken to the power
of two not above its size, up to 256 x 256 (the nearest point). The image can be freed afterwards with
`image_decoded_free`. It is drawn with `gl_texture_bind` and `gl_tex_coord`; with `gl_close` the textures are lost.
""", ["gl_texture_bind", "gl_tex_coord", "gl_texture_free", "image_decode"]),
    "gl_light": _f("""\
- `n`: la luz, de 0 a 7.
- `x`, `y`, `z`: de dónde llega la luz (una dirección, como el sol).

Enciende esa luz y la iluminación (`GL_LIGHTING`), con el color de `gl_color` como material de las figuras. Cada cara
necesita su `gl_normal`. `gl_disable(GL_LIGHTING)` apaga todas.
""", """\
- `n`: the light, 0 to 7.
- `x`, `y`, `z`: where the light comes from (a direction, like the sun).

Turns on that light and the lighting (`GL_LIGHTING`), with the colour of `gl_color` as the material of the shapes.
Each face needs its `gl_normal`. `gl_disable(GL_LIGHTING)` turns them all off.
""", ["gl_light_color", "gl_ambient", "gl_normal"]),
    "gl_fog": _f("""\
- `start`, `end`: dónde empieza y dónde lo tapa todo, en distancia desde el ojo.
- `r`, `g`, `b`: su color, de 0.0 a 1.0.

Niebla lineal. Con Wazp3D (Warp3D por software) solo se ve si se activa la niebla en sus preferencias.
""", """\
- `start`, `end`: where it starts and where it covers everything, as distance from the eye.
- `r`, `g`, `b`: its colour, 0.0 to 1.0.

Linear fog. With Wazp3D (Warp3D in software) it only shows if fog is turned on in its preferences.
""", ["gl_disable"]),
    "gl_read_pixel": _f("""\
- `x`, `y`: el píxel, desde la esquina de arriba a la izquierda.

Devuelve el color de ese píxel del dibujo en curso, antes de `gl_swap`, como `0xRRGGBB`; -1 sin ventana. Es lento:
para pruebas o para saber qué hay bajo el ratón, no para cada píxel.
""", """\
- `x`, `y`: the pixel, from the top left corner.

Returns the colour of that pixel of the picture being drawn, before `gl_swap`, as `0xRRGGBB`; -1 without a window. It
is slow: for tests or to know what is under the mouse, not for every pixel.
""", ["gl_swap"]),
}
