"""Gráficos avanzados (GRAPHICS_ADVANCED): el copper y los bitmaps fuera de pantalla."""

GROUPS = {}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_B_ES = "- `id`: el número del bitmap, de 0 a 31 (los mismos que los BOBs).\n"
_B_EN = "- `id`: the bitmap's number, 0 to 31 (the same as the BOBs).\n"

FUNCS = {
    # ------------------------------------------------------------ copper
    "copper_create": _f("""\
- `size`: cuántas instrucciones caben; 0 = 64. Cada `copper_wait`, `copper_move` o `copper_color` es una.

Empieza una lista del copper vacía. Después van las instrucciones, `copper_end` y `copper_install`. Hay una sola
lista: si había una instalada, se sigue viendo hasta que `copper_install` pone la nueva en su sitio (sin una imagen
sin lista entre las dos). Devuelve `false` sin memoria.
""", """\
- `size`: how many instructions fit; 0 = 64. Each `copper_wait`, `copper_move` or `copper_color` is one.

Starts an empty copper list. Then come the instructions, `copper_end` and `copper_install`. There is a single
list: if one was installed, it stays on screen until `copper_install` puts the new one in its place (with no frame
without a list between them). Returns `false` without memory.
""", ["copper_wait", "copper_color", "copper_install"]),
    "copper_wait": _f("""\
- `y`: la línea de la pantalla, contando desde arriba de la pantalla del programa.
- `x`: la posición en la línea; 0 = el principio.

El copper espera a que el haz llegue ahí antes de seguir con la lista. Las líneas van en orden: una espera a una
línea ya pasada no se cumple hasta el siguiente fotograma.
""", """\
- `y`: the screen line, counting from the top of the program's screen.
- `x`: the position along the line; 0 = the start.

The copper waits for the beam to get there before going on with the list. Lines go in order: a wait for a line
already passed is not met until the next frame.
""", ["copper_color", "copper_move"]),
    "copper_move": _f("""\
- `reg`: el registro del chip de vídeo, como desplazamiento desde 0xDFF000: 0x180 es COLOR00.
- `value`: el valor de 16 bits.

Escribe ese valor en el registro cuando el copper llega a esta instrucción. Para efectos que no son de color; un
registro equivocado puede estropear la imagen hasta que se quite la lista.
""", """\
- `reg`: the video chip register, as an offset from 0xDFF000: 0x180 is COLOR00.
- `value`: the 16-bit value.

Writes that value to the register when the copper reaches this instruction. For effects other than colour; a wrong
register can spoil the picture until the list is removed.
""", ["copper_color"]),
    "copper_color": _f("""\
- `index`: el color, de 0 a 31.
- `rgb`: el color en 12 bits, `0xRGB`: `0xF00` rojo, `0x00F` azul.

Cambia ese color desde la línea de la espera anterior. Varias esperas con un color cada una hacen un degradado de
fondo.
""", """\
- `index`: the colour, 0 to 31.
- `rgb`: the colour in 12 bits, `0xRGB`: `0xF00` red, `0x00F` blue.

Changes that colour from the line of the previous wait on. Several waits with a colour each make a background
gradient.
""", ["copper_wait", "copper_move"]),
    "copper_end": _f("Cierra la lista. Va después de la última instrucción y antes de `copper_install`.\n",
                     "Closes the list. It goes after the last instruction and before `copper_install`.\n",
                     ["copper_install"]),
    "copper_install": _f("""\
Pone la lista en marcha en la pantalla del programa (o en la de la ventana, que puede ser el Workbench: mejor una
pantalla propia). Funciona por el sistema, sin quitarle el control. Una instrucción de la lista instalada se cambia
con `copper_set`; para otra lista, `copper_create` y las instrucciones nuevas: la de antes se ve hasta este
`copper_install`.
""", """\
Starts the list on the program's screen (or on the window's, which may be the Workbench: better a screen of your
own). It goes through the system, without taking it over. An instruction of the installed list changes with
`copper_set`; for another list, `copper_create` and the new instructions: the old one shows until this
`copper_install`.
""", ["copper_free", "copper_create", "copper_set"]),
    "copper_free": _f("Quita la lista de la pantalla y libera su memoria. Al acabar el programa se quita sola.\n",
                      "Removes the list from the screen and frees its memory. It is removed on its own when the program ends.\n",
                      ["copper_install"]),
    "copper_set": _f("""\
- `i`: la instrucción, desde 0, en el orden en que se añadieron (`copper_wait`, `copper_move`, `copper_color` y
  `copper_end` cuentan una cada una). `copper_count()` antes de añadir una da su número.
- `value`: en un `copper_move` o un `copper_color`, el valor nuevo (`0xRGB` en un color); en un `copper_wait`, la
  línea nueva.

Cambia esa instrucción. Si la lista está instalada se ve enseguida: la pantalla se rehace por el sistema
(`MakeScreen` y `RethinkDisplay`, unos milisegundos), así que es para cambios de vez en cuando (un editor que manda
colores a una demo en marcha), no para cada imagen. Un número que no es de la lista no hace nada.
""", """\
- `i`: the instruction, from 0, in the order they were added (`copper_wait`, `copper_move`, `copper_color` and
  `copper_end` count one each). `copper_count()` before adding one gives its number.
- `value`: in a `copper_move` or a `copper_color`, the new value (`0xRGB` in a colour); in a `copper_wait`, the new
  line.

Changes that instruction. If the list is installed it shows at once: the screen is made again through the system
(`MakeScreen` and `RethinkDisplay`, a few milliseconds), so it is for changes now and then (an editor sending
colours to a running demo), not for every frame. A number outside the list does nothing.
""", ["copper_count", "copper_install"]),
    "copper_count": _f("Devuelve cuántas instrucciones tiene la lista: el número que tendrá la siguiente, para `copper_set`.\n",
                       "Returns how many instructions the list has: the number the next one will have, for `copper_set`.\n",
                       ["copper_set"]),
    # ------------------------------------------------------------ el haz
    "beam_line": _f("""\
Devuelve la línea que dibuja ahora el haz de vídeo: 0 arriba de la imagen, hasta 312 en PAL (262 en NTSC). Lee
`VPOSR` y `VHPOSR` hasta que salen de la misma línea: nunca medio número de una y medio de la siguiente. Para medir
cuánto de la imagen gasta una parte de una demo: la línea antes y después.
""", """\
Returns the line the video beam is drawing now: 0 at the top of the frame, up to 312 on PAL (262 on NTSC). It reads
`VPOSR` and `VHPOSR` until they come from the same line: never half the number of one and half of the next. To
measure how much of the frame a part of a demo takes: the line before and after.
""", ["beam_lines", "vblank_count"]),
    "beam_lines": _f("""\
Devuelve las líneas de una imagen de la pantalla: 313 en PAL, 263 en NTSC (las del monitor que usa graphics; si no,
las de la máquina). Con `beam_line`, la parte de la imagen que se ha gastado.
""", """\
Returns the lines of a frame of the display: 313 on PAL, 263 on NTSC (those of the monitor graphics uses; otherwise,
the machine's). With `beam_line`, the part of the frame used up.
""", ["beam_line", "video_pal"]),
    "video_pal": _f("Devuelve `true` en un Amiga PAL (50 imágenes por segundo) y `false` en uno NTSC (60).\n",
                    "Returns `true` on a PAL Amiga (50 frames a second) and `false` on an NTSC one (60).\n",
                    ["beam_lines"]),
    "vblank_count": _f("""\
Devuelve las imágenes mostradas (las interrupciones de VBlank) desde la primera llamada, que da 0: un servidor de
interrupción las cuenta, y se quita al acabar el programa. Si un bucle de una imagen tarda más, la cuenta sube 2: así
se saben las imágenes perdidas, lo que no dice un tiempo.
""", """\
Returns the frames shown (the VBlank interrupts) since the first call, which returns 0: an interrupt server counts
them, and goes away when the program ends. If a one-frame loop takes longer, the count goes up by 2: that is how
lost frames are known, which a time does not tell.
""", ["beam_line", "wait_vblank"]),
    # ------------------------------------------------------------ bitmaps
    "bitmap_create": _f(_B_ES + """\
- `width`, `height`: el tamaño en píxeles.
- `depth`: la profundidad, de 1 a 8. Con 0, la de la pantalla donde se dibuja y en su formato, también el de una
  tarjeta gráfica: para preparar algo sin que se vea (imágenes, iconos y colores RGB incluidos) y copiarlo a la
  ventana de una vez, sin parpadeo.

Crea un bitmap vacío (todo color 0) fuera de pantalla; el que hubiera en ese número se libera. Devuelve `false` con
medidas fuera de rango o sin memoria.
""", _B_EN + """\
- `width`, `height`: the size in pixels.
- `depth`: the depth, 1 to 8. With 0, that of the screen being drawn on and in its format, a graphics card's too:
  to prepare something out of sight (pictures, icons and RGB colours included) and copy it to the window at once,
  without flicker.

Creates an empty bitmap (all colour 0) off screen; any bitmap at that number is freed. Returns `false` with sizes
out of range or without memory.
""", ["bitmap_draw_to", "bitmap_blit"]),
    "bitmap_load": _f(_B_ES + """\
- `filename`: una imagen IFF ILBM, comprimida o no.

La carga en el bitmap. En una pantalla propia, la paleta pasa a ser la de la imagen; el Workbench se queda con la
suya. Devuelve `false` si no se puede leer o no es un ILBM.
""", _B_EN + """\
- `filename`: an IFF ILBM picture, compressed or not.

Loads it into the bitmap. On a screen of your own, the palette becomes the picture's; the Workbench keeps its own.
Returns `false` if it cannot be read or is not an ILBM.
""", ["bitmap_blit", "bob_load_colors", "image_load"]),
    "bitmap_save": _f(_B_ES + """\
- `filename`: el fichero.

Lo guarda como IFF ILBM sin comprimir, con la paleta de la pantalla del programa o de la ventana. Devuelve `false`
si no se puede escribir, o si el bitmap es de más de 8 planos (uno de `bitmap_create` con profundidad 0 en una
tarjeta gráfica).
""", _B_EN + """\
- `filename`: the file.

Saves it as an uncompressed IFF ILBM, with the palette of the program's screen or the window's. Returns `false` if
it cannot be written, or if the bitmap has more than 8 planes (one from `bitmap_create` with depth 0 on a graphics
card).
""", ["bitmap_load"]),
    "bitmap_free": _f(_B_ES + "\nLibera el bitmap. Si se estaba dibujando en él, se vuelve a dibujar en la pantalla.\n",
                      _B_EN + "\nFrees the bitmap. If drawing was going to it, drawing goes back to the screen.\n",
                      ["bitmap_create"]),
    "bitmap_blit": _f("""\
- `src_id`: el bitmap de origen.
- `sx`, `sy`: la esquina de la parte que se copia, dentro del bitmap.
- `w`, `h`: su tamaño.
- `dx`, `dy`: dónde va en el destino de los `gfx_*`.

Copia esa parte del bitmap tal cual, color 0 incluido. Es la forma rápida de poner un fondo o una pantalla
preparada.
""", """\
- `src_id`: the source bitmap.
- `sx`, `sy`: the corner of the part to copy, inside the bitmap.
- `w`, `h`: its size.
- `dx`, `dy`: where it goes on the `gfx_*` target.

Copies that part of the bitmap as it is, colour 0 included. It is the fast way to put up a background or a prepared
screen.
""", ["bitmap_blit_mask", "bob_paste"]),
    "bitmap_blit_mask": _f("""\
- `src_id`: el bitmap de origen.
- `mask_id`: un bitmap del mismo ancho que dice dónde se copia: los píxeles con el primer plano a 1 (color impar).
- `sx`, `sy`, `w`, `h`, `dx`, `dy`: como en `bitmap_blit`.

Copia solo donde la máscara lo dice; lo demás deja ver lo que había. Si los anchos no coinciden, no hace nada. Un
BOB hace su máscara solo: para imágenes con color 0 transparente es más cómodo `bob_paste`.
""", """\
- `src_id`: the source bitmap.
- `mask_id`: a bitmap of the same width that says where to copy: pixels with the first plane set (odd colour).
- `sx`, `sy`, `w`, `h`, `dx`, `dy`: as in `bitmap_blit`.

Copies only where the mask says; elsewhere what was there shows. If the widths do not match, it does nothing. A BOB
makes its own mask: for pictures with colour 0 transparent, `bob_paste` is easier.
""", ["bitmap_blit", "bob_paste"]),
    "bitmap_draw_to": _f(_B_ES + """\
Desde ahora los `gfx_*` dibujan en ese bitmap (o BOB) en vez de en la pantalla, hasta `bitmap_draw_screen`. Las
coordenadas cuentan desde su esquina.
""", _B_EN + """\
From now on the `gfx_*` functions draw on that bitmap (or BOB) instead of the screen, until `bitmap_draw_screen`.
Coordinates count from its corner.
""", ["bitmap_draw_screen", "bob_create"]),
    "bitmap_draw_screen": _f("""\
Los `gfx_*` vuelven a dibujar donde dibujaban antes del `bitmap_draw_to`: la ventana o la pantalla.
""", """\
The `gfx_*` functions go back to drawing where they drew before `bitmap_draw_to`: the window or the screen.
""", ["bitmap_draw_to"]),
}
