"""Gráficos avanzados (GRAPHICS_ADVANCED): la introducción del grupo, los sprites y los BOBs. Los mapas de tiles, el
copper y los bitmaps, en tiles.py y bitmaps.py."""

GROUPS = {
    "GRAPHICS_ADVANCED": {
        "es": """\
Lo que usan los juegos: sprites, BOBs, mapas de tiles, el copper y bitmaps fuera de pantalla. Todo se maneja por
número (`id`), que elige el programa.

**Sprites de hardware** (`sprite_*`): los dibuja el chip de vídeo encima de todo, sin tocar la pantalla, así que
moverlos no cuesta nada. Necesitan una pantalla propia (`screen_open_custom`), y no van en tarjetas gráficas. Hay 8
números, del 0 al 7, pero el chip tiene 8 sprites y el puntero del ratón usa uno: caben 7 a la vez, o menos si van
acoplados. Cada uno mide 16 píxeles de ancho y tiene 3 colores más el transparente. Dos sprites seguidos (0 y 1,
2 y 3...) comparten sus colores: los del 0 y el 1 son los colores 17 a 19 de la pantalla. `sprite_load_attached` une
dos para tener 15 colores.

**Sprites por software** (`soft_sprite_*`): imágenes que Dash dibuja en la ventana o la pantalla y quita
restaurando lo que había detrás. Van en cualquier pantalla, también en tarjetas gráficas. Hasta 16.

**BOBs** (`bob_*`): imágenes de cualquier tamaño y colores, con el color 0 transparente, que se pegan en el
destino de los `gfx_*` con el blitter. Un BOB puede tener varios fotogramas, uno al lado de otro en la imagen.
`bob_draw` guarda lo que tapa y `bob_erase` lo devuelve; `bob_paste` solo pinta, para juegos que repintan todo en
cada fotograma con `screen_double_buffer`. Los BOBs y los bitmaps comparten números, del 0 al 31: un BOB es un
bitmap con su máscara, y se puede dibujar en él con `bitmap_draw_to`.

**Mapas de tiles** (`tilemap_*`): un nivel hecho de celdas, con capas y objetos, como el que guarda el editor de
mapas de Forja o de la extensión. Se pinta con los fotogramas de un BOB.

**El copper** (`copper_*`): una lista de instrucciones que cambian registros del chip de vídeo en una línea concreta
de la pantalla, para degradados de fondo y otros efectos.

**Bitmaps** (`bitmap_*`): imágenes fuera de pantalla, para cargar una imagen IFF, preparar algo sin que se vea y
copiarlo de golpe.

Las imágenes salen de ficheros IFF ILBM, los que guardan Deluxe Paint, PPaint y el editor de sprites de Forja.
""",
        "en": """\
What games use: sprites, BOBs, tile maps, the copper and off-screen bitmaps. Everything is handled by number (`id`),
chosen by the program.

**Hardware sprites** (`sprite_*`): the video chip draws them on top of everything, without touching the screen, so
moving them costs nothing. They need a screen of your own (`screen_open_custom`), and they do not work on graphics
cards. There are 8 numbers, 0 to 7, but the chip has 8 sprites and the mouse pointer uses one: 7 fit at once, or
fewer if attached. Each is 16 pixels wide and has 3 colours plus transparent. Two consecutive sprites (0 and 1, 2
and 3...) share their colours: those of 0 and 1 are colours 17 to 19 of the screen. `sprite_load_attached` joins
two to get 15 colours.

**Software sprites** (`soft_sprite_*`): pictures that Dash draws on the window or the screen and removes by
restoring what was behind. They work on any screen, graphics cards too. Up to 16.

**BOBs** (`bob_*`): pictures of any size and colours, with colour 0 transparent, pasted on the `gfx_*` target with
the blitter. A BOB can have several frames, side by side in the picture. `bob_draw` saves what it covers and
`bob_erase` puts it back; `bob_paste` only paints, for games that repaint everything every frame with
`screen_double_buffer`. BOBs and bitmaps share numbers, 0 to 31: a BOB is a bitmap with its mask, and you can draw
on it with `bitmap_draw_to`.

**Tile maps** (`tilemap_*`): a level made of cells, with layers and objects, like the one saved by the map editor
in Forja or the extension. It is painted with the frames of a BOB.

**The copper** (`copper_*`): a list of instructions that change video chip registers at a given line of the
screen, for background gradients and other effects.

**Bitmaps** (`bitmap_*`): off-screen pictures, to load an IFF picture, prepare something unseen and copy it in one
go.

Pictures come from IFF ILBM files, the ones Deluxe Paint, PPaint and Forja's sprite editor save.
""",
        "example": ["tests/test_doc_sprites.dash", "tests/test_doc_tiles.dash"],
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_ID_ES = "- `id`: el número del sprite, de 0 a 7.\n"
_ID_EN = "- `id`: the sprite's number, 0 to 7.\n"
_SS_ES = "- `id`: el número del sprite por software, de 0 a 15.\n"
_SS_EN = "- `id`: the software sprite's number, 0 to 15.\n"
_BOB_ES = "- `id`: el número del BOB, de 0 a 31.\n"
_BOB_EN = "- `id`: the BOB's number, 0 to 31.\n"

FUNCS = {
    # ------------------------------------------------------------ sprites de hardware
    "sprite_load": _f(_ID_ES + """\
- `filename`: una imagen IFF ILBM con los fotogramas de 16 píxeles de ancho uno al lado del otro; el alto de la
  imagen es el del sprite.

Crea el sprite con la imagen y enseña el primer fotograma (`sprite_frame` cambia de fotograma). Sus colores son los
1 a 3 de la imagen; el 0 es transparente. No pone los colores: `sprite_load_colors` los toma de la imagen. Devuelve
`false` si no se puede leer el fichero, no hay pantalla propia o no queda un sprite libre.
""", _ID_EN + """\
- `filename`: an IFF ILBM picture with the 16-pixel-wide frames side by side; the picture's height is the
  sprite's.

Creates the sprite from the picture and shows the first frame (`sprite_frame` changes frame). Its colours are 1 to 3
of the picture; 0 is transparent. It does not set the colours: `sprite_load_colors` takes them from the picture.
Returns `false` if the file cannot be read, there is no screen of your own or no sprite is free.
""", ["sprite_load_colors", "sprite_frame", "sprite_pos", "sprite_load_attached"]),
    "sprite_load_attached": _f(_ID_ES + """\
- `filename`: una imagen IFF ILBM de hasta 16 colores, con los fotogramas de 16 píxeles de ancho.

Como `sprite_load`, pero une dos sprites de hardware para tener 15 colores más el transparente: los colores 1 a 15
de la imagen se ven con los colores 17 a 31 de la pantalla. Gasta dos sprites. Devuelve `false` si no queda una
pareja libre.
""", _ID_EN + """\
- `filename`: an IFF ILBM picture of up to 16 colours, with 16-pixel-wide frames.

Like `sprite_load`, but joins two hardware sprites to get 15 colours plus transparent: colours 1 to 15 of the
picture show with colours 17 to 31 of the screen. It takes two sprites. Returns `false` if no pair is free.
""", ["sprite_load", "sprite_load_colors"]),
    "sprite_create": _f(_ID_ES + """\
- `width`: no cuenta: los sprites de hardware miden siempre 16 píxeles de ancho.
- `height`: el alto en píxeles.

Crea un sprite vacío, transparente. Su dibujo se pone fila a fila con `sprite_set_row`. Devuelve `false` sin
pantalla propia o si no queda un sprite libre.
""", _ID_EN + """\
- `width`: it does not count: hardware sprites are always 16 pixels wide.
- `height`: the height in pixels.

Creates an empty, transparent sprite. Its picture is set row by row with `sprite_set_row`. Returns `false` without
a screen of your own or if no sprite is free.
""", ["sprite_set_row", "sprite_load"]),
    "sprite_pos": _f(_ID_ES + """\
- `x`, `y`: la posición de su esquina de arriba a la izquierda en la pantalla.

Mueve el sprite. No hay que borrar ni repintar nada.
""", _ID_EN + """\
- `x`, `y`: the position of its top left corner on the screen.

Moves the sprite. Nothing needs clearing or repainting.
""", ["sprite_show", "sprite_collision"]),
    "sprite_show": _f(_ID_ES + "\nLo enseña en su posición, después de un `sprite_hide`.\n",
                      _ID_EN + "\nShows it at its position, after a `sprite_hide`.\n", ["sprite_hide"]),
    "sprite_hide": _f(_ID_ES + "\nLo oculta: lo lleva fuera de la pantalla. Sigue siendo suyo.\n",
                      _ID_EN + "\nHides it: it moves it off the screen. It is still yours.\n",
                      ["sprite_show", "sprite_free"]),
    "sprite_color": _f(_ID_ES + """\
- `index`: el color del sprite, de 0 a 2 (sus colores 1 a 3); de 0 a 14 en una pareja acoplada.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 15.

Cambia un color del sprite. Lo comparte con el sprite de su pareja (el 0 con el 1, el 2 con el 3...).
""", _ID_EN + """\
- `index`: the sprite's colour, 0 to 2 (its colours 1 to 3); 0 to 14 in an attached pair.
- `r`, `g`, `b`: red, green and blue, 0 to 15.

Changes a colour of the sprite. It is shared with the sprite of its pair (0 with 1, 2 with 3...).
""", ["sprite_rgb8", "sprite_load_colors"]),
    "sprite_rgb8": _f(_ID_ES + """\
- `index`: como en `sprite_color`.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 255; en OCS y ECS solo cuentan los 4 bits de arriba.

Como `sprite_color`, con 8 bits por componente.
""", _ID_EN + """\
- `index`: as in `sprite_color`.
- `r`, `g`, `b`: red, green and blue, 0 to 255; on OCS and ECS only the top 4 bits count.

Like `sprite_color`, with 8 bits per component.
""", ["sprite_color"]),
    "sprite_load_colors": _f(_ID_ES + """\
- `filename`: una imagen IFF con paleta: la del sprite, normalmente.

Pone como colores del sprite los colores 1 a 3 de la paleta de la imagen (1 a 15 en una pareja acoplada).
Devuelve `false` si el fichero no tiene paleta o el sprite no existe.
""", _ID_EN + """\
- `filename`: an IFF picture with a palette: usually the sprite's own.

Sets colours 1 to 3 of the picture's palette as the sprite's colours (1 to 15 in an attached pair). Returns `false`
if the file has no palette or the sprite does not exist.
""", ["sprite_load", "bob_load_colors"]),
    "bob_load_colors": _f("""\
- `filename`: una imagen IFF con paleta.
- `first`: desde qué color de la pantalla se ponen.

Copia la paleta de la imagen en la de la pantalla (la propia o la de la ventana), desde el color `first`. Devuelve
cuántos colores puso, 0 si el fichero no tiene paleta.
""", """\
- `filename`: an IFF picture with a palette.
- `first`: the screen colour to start from.

Copies the picture's palette into the screen's (your own or the window's), from colour `first` on. Returns how many
colours it set, 0 if the file has no palette.
""", ["bob_load", "gfx_rgb8"]),
    "sprite_frame": _f(_ID_ES + """\
- `frame`: el fotograma, desde 0.

Enseña ese fotograma de un sprite de `sprite_load` o `sprite_load_attached`. Para animarlo, se cambia cada pocos
fotogramas de pantalla. Un fotograma que no existe no hace nada.
""", _ID_EN + """\
- `frame`: the frame, from 0.

Shows that frame of a sprite from `sprite_load` or `sprite_load_attached`. To animate it, change it every few
screen frames. A frame that does not exist does nothing.
""", ["sprite_load"]),
    "sprite_free": _f(_ID_ES + "\nLo quita y deja libre su sprite de hardware. Al acabar el programa se liberan solos.\n",
                      _ID_EN + "\nRemoves it and frees its hardware sprite. They are freed on their own when the program ends.\n",
                      ["sprite_hide"]),
    "sprite_collision": _f("""\
- `id1`, `id2`: dos sprites.

Devuelve `true` si sus rectángulos (16 píxeles por su alto) se tocan. No mira los píxeles transparentes: para eso,
los BOBs y `bob_collision`.
""", """\
- `id1`, `id2`: two sprites.

Returns `true` if their rectangles (16 pixels by their height) overlap. It does not look at transparent pixels: for
that, BOBs and `bob_collision`.
""", ["bob_collision"]),
    "sprite_set_row": _f(_ID_ES + """\
- `row`: la fila, desde 0.
- `plane0`, `plane1`: 16 bits cada uno; el bit de más a la izquierda es el píxel 0. El color de cada píxel es su bit
  de `plane0` más el doble del de `plane1`: 0 transparente, 1 a 3 los colores del sprite.

Cambia una fila del dibujo del sprite: `sprite_set_row(0, 0, 0xFFFF, 0)` pinta la primera fila con el color 1.
""", _ID_EN + """\
- `row`: the row, from 0.
- `plane0`, `plane1`: 16 bits each; the leftmost bit is pixel 0. Each pixel's colour is its `plane0` bit plus twice
  its `plane1` bit: 0 transparent, 1 to 3 the sprite's colours.

Changes one row of the sprite's picture: `sprite_set_row(0, 0, 0xFFFF, 0)` paints the first row in colour 1.
""", ["sprite_create"]),
    # ------------------------------------------------------------ sprites por software
    "soft_sprite_create": _f(_SS_ES + """\
- `width`, `height`: el tamaño en píxeles.
- `depth`: la profundidad de su imagen (los colores, como en una pantalla).

Crea un sprite por software vacío, transparente, para el destino actual de los `gfx_*`. Se dibuja con
`soft_sprite_pixel` o `soft_sprite_row`. Devuelve `false` sin destino o sin memoria.
""", _SS_EN + """\
- `width`, `height`: the size in pixels.
- `depth`: the depth of its picture (the colours, as on a screen).

Creates an empty, transparent software sprite, for the current `gfx_*` target. You draw it with
`soft_sprite_pixel` or `soft_sprite_row`. Returns `false` without a target or without memory.
""", ["soft_sprite_pixel", "soft_sprite_show", "soft_sprite_pos"]),
    "soft_sprite_free": _f(_SS_ES + "\nLo quita (devolviendo lo que tapaba) y libera su memoria.\n",
                           _SS_EN + "\nRemoves it (putting back what it covered) and frees its memory.\n",
                           ["soft_sprite_hide"]),
    "soft_sprite_pixel": _f(_SS_ES + """\
- `x`, `y`: el píxel dentro del sprite.
- `color`: el color; 0 = transparente.
""", _SS_EN + """\
- `x`, `y`: the pixel inside the sprite.
- `color`: the colour; 0 = transparent.
""", ["soft_sprite_clear"]),
    "soft_sprite_clear": _f(_SS_ES + "- `color`: el color; 0 lo deja todo transparente.\n\nPinta todo el sprite de un color.\n",
                            _SS_EN + "- `color`: the colour; 0 makes it all transparent.\n\nPaints the whole sprite one colour.\n",
                            ["soft_sprite_pixel"]),
    "soft_sprite_row": _f(_SS_ES + """\
- `row`: la fila.
- `plane0`, `plane1`: como en `sprite_set_row`.

Pone los 16 primeros píxeles de una fila con el formato de los sprites de hardware, para usar el mismo dibujo.
""", _SS_EN + """\
- `row`: the row.
- `plane0`, `plane1`: as in `sprite_set_row`.

Sets the first 16 pixels of a row in the hardware sprite format, to reuse the same picture.
""", ["sprite_set_row"]),
    "soft_sprite_show": _f(_SS_ES + "\nLo dibuja en su posición, guardando lo que tapa.\n",
                           _SS_EN + "\nDraws it at its position, saving what it covers.\n", ["soft_sprite_hide"]),
    "soft_sprite_hide": _f(_SS_ES + "\nLo quita devolviendo lo que tapaba.\n",
                           _SS_EN + "\nRemoves it, putting back what it covered.\n", ["soft_sprite_show"]),
    "soft_sprite_pos": _f(_SS_ES + """\
- `x`, `y`: la posición nueva.

Lo mueve: si se ve, devuelve el fondo de donde estaba y lo dibuja en el sitio nuevo. Si se dibuja algo debajo
mientras se ve, quítalo antes con `soft_sprite_hide`: si no, al moverlo vuelve el fondo viejo.
""", _SS_EN + """\
- `x`, `y`: the new position.

Moves it: if it shows, it restores the background where it was and draws it at the new place. If something is drawn
under it while it shows, take it off first with `soft_sprite_hide`: otherwise moving it brings the old background
back.
""", ["soft_sprite_x", "soft_sprite_show"]),
    "soft_sprite_x": _f(_SS_ES + "\nDevuelve su posición X.\n", _SS_EN + "\nReturns its X position.\n",
                        ["soft_sprite_y"]),
    "soft_sprite_y": _f(_SS_ES + "\nDevuelve su posición Y.\n", _SS_EN + "\nReturns its Y position.\n",
                        ["soft_sprite_x"]),
    # ------------------------------------------------------------ BOBs
    "bob_load": _f(_BOB_ES + """\
- `filename`: una imagen IFF ILBM. Si es más ancha que alta y su ancho es múltiplo del alto, son fotogramas
  cuadrados uno al lado de otro; los del editor de sprites de Forja dicen su ancho de fotograma.

Carga el BOB. Su color 0 es transparente. No pone la paleta: `bob_load_colors`. Devuelve `false` si no se puede
leer.
""", _BOB_EN + """\
- `filename`: an IFF ILBM picture. If it is wider than tall and its width is a multiple of its height, it holds
  square frames side by side; those from Forja's sprite editor state their frame width.

Loads the BOB. Its colour 0 is transparent. It does not set the palette: `bob_load_colors`. Returns `false` if it
cannot be read.
""", ["bob_load_colors", "bob_draw", "bob_frame_width"]),
    "bob_create": _f(_BOB_ES + """\
- `width`, `height`: el tamaño de la imagen; si el ancho es múltiplo del alto, salen fotogramas cuadrados.
- `depth`: la profundidad, de 1 a 8; la de la pantalla, normalmente.

Crea un BOB vacío (todo color 0, transparente). Se dibuja en él con `bitmap_draw_to(id)` y los `gfx_*`, y
`bitmap_draw_screen()` vuelve a la pantalla.
""", _BOB_EN + """\
- `width`, `height`: the picture's size; if the width is a multiple of the height, you get square frames.
- `depth`: the depth, 1 to 8; usually the screen's.

Creates an empty BOB (all colour 0, transparent). Draw on it with `bitmap_draw_to(id)` and the `gfx_*` functions,
and `bitmap_draw_screen()` goes back to the screen.
""", ["bitmap_draw_to", "bob_draw"]),
    "bob_pos": _f(_BOB_ES + """\
- `x`, `y`: la posición de su esquina en el destino.

Cambia dónde irá; se ve en el siguiente `bob_draw`.
""", _BOB_EN + """\
- `x`, `y`: the position of its corner on the target.

Changes where it will go; it shows on the next `bob_draw`.
""", ["bob_draw"]),
    "bob_draw": _f(_BOB_ES + """\
Lo pinta en su posición y fotograma, guardando antes lo que tapa. Si ya estaba pintado, primero lo quita del sitio
de antes: para moverlo basta `bob_pos` y `bob_draw`. Con varios BOBs que se tocan, se quitan en orden inverso al
que se pintaron.
""", _BOB_EN + """\
Paints it at its position and frame, saving first what it covers. If it was already painted, it removes it from
the old place first: to move it, `bob_pos` and `bob_draw` are enough. With several overlapping BOBs, remove them in
the reverse order they were painted.
""", ["bob_erase", "bob_paste", "bob_pos"]),
    "bob_erase": _f(_BOB_ES + "\nLo quita devolviendo lo que tapaba.\n",
                    _BOB_EN + "\nRemoves it, putting back what it covered.\n", ["bob_draw"]),
    "bob_frame": _f(_BOB_ES + """\
- `frame`: el fotograma, desde 0; da la vuelta (con 4 fotogramas, el 5 es el 1).

Elige el fotograma del siguiente `bob_draw`.
""", _BOB_EN + """\
- `frame`: the frame, from 0; it wraps around (with 4 frames, 5 is 1).

Chooses the frame for the next `bob_draw`.
""", ["bob_frames", "bob_frame_width"]),
    "bob_frame_width": _f(_BOB_ES + """\
- `width`: el ancho de cada fotograma en píxeles.

Dice que la imagen es una tira de fotogramas de ese ancho, cuando no son cuadrados.
""", _BOB_EN + """\
- `width`: each frame's width in pixels.

Says the picture is a strip of frames that wide, when they are not square.
""", ["bob_frame", "bob_frames"]),
    "bob_width": _f(_BOB_ES + "\nDevuelve el ancho de un fotograma; 0 si no hay ese BOB.\n",
                    _BOB_EN + "\nReturns a frame's width; 0 if there is no such BOB.\n", ["bob_height"]),
    "bob_height": _f(_BOB_ES + "\nDevuelve el alto; 0 si no hay ese BOB.\n",
                     _BOB_EN + "\nReturns the height; 0 if there is no such BOB.\n", ["bob_width"]),
    "bob_frames": _f(_BOB_ES + "\nDevuelve cuántos fotogramas tiene; 0 si no hay ese BOB.\n",
                     _BOB_EN + "\nReturns how many frames it has; 0 if there is no such BOB.\n", ["bob_frame"]),
    "bob_paste": _f(_BOB_ES + """\
- `frame`: el fotograma.
- `x`, `y`: dónde.

Pinta ese fotograma en `x`, `y` con su color 0 transparente, sin guardar lo que tapa ni moverlo de donde esté.
Para juegos que repintan la pantalla entera en cada fotograma, y para dibujar el mismo BOB en muchos sitios.
""", _BOB_EN + """\
- `frame`: the frame.
- `x`, `y`: where.

Paints that frame at `x`, `y` with its colour 0 transparent, without saving what it covers or moving it from where
it is. For games that repaint the whole screen every frame, and to draw the same BOB in many places.
""", ["bob_draw", "screen_double_buffer"]),
    "bob_free": _f(_BOB_ES + "\nLo quita de la pantalla si estaba pintado y libera su memoria.\n",
                   _BOB_EN + "\nRemoves it from the screen if it was painted and frees its memory.\n", ["bob_erase"]),
    "bob_collision": _f("""\
- `id1`, `id2`: dos BOBs distintos.

Devuelve `true` si se tocan sus píxeles no transparentes, con sus posiciones y fotogramas de ahora. Mira primero
los rectángulos y luego los píxeles de la parte común.
""", """\
- `id1`, `id2`: two different BOBs.

Returns `true` if their non-transparent pixels touch, with their current positions and frames. It checks the
rectangles first and then the pixels where they overlap.
""", ["sprite_collision"]),
}
