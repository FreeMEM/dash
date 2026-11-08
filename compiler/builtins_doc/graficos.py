"""Gráficos básicos (GRAPHICS_BASIC)."""

GROUPS = {
    "GRAPHICS_BASIC": {
        "es": """\
Dibujo con la `graphics.library` del sistema: puntos, líneas, rectángulos, círculos, polígonos y texto, con los
colores de la paleta (lápices).

**Dónde dibujan.** Todos los `gfx_*` dibujan en el destino actual:

- la última ventana abierta, con `Window X ... end` y `X.open` o con `window_create`; `window_use` elige otra;
- la pantalla abierta con `screen_open` o `screen_open_custom`, si no hay ventana;
- un bitmap fuera de pantalla, entre `bitmap_draw_to` y `bitmap_draw_screen`;
- la zona de dibujo de MUI, dentro de la función de `mui_canvas_on_draw`.

Antes de dibujar hay que abrir una de esas cosas. Las coordenadas son píxeles desde la esquina de arriba a la
izquierda del destino. En las ventanas de Dash es la esquina de dentro de los bordes: (0, 0) no pisa la barra de
título. Lo que se sale del destino no se dibuja.

**Colores.** Se dibuja con un número de color de la paleta, el lápiz: `gfx_pen(2)`. Una pantalla de profundidad
3 tiene 8 colores (0 a 7); una de 5, 32. `gfx_rgb` y `gfx_rgb8` cambian cómo se ve un color de la paleta. En el
Workbench los colores son de todos los programas: para cambiarlos sin molestar, abre una pantalla propia. Para
dibujar con un color RGB cualquiera, sin pensar en la paleta, están `color_pen` (Fuentes y colores) y
`gfx_pixel_rgb` (Transparencia y degradados).

**El flujo de siempre:** abrir la pantalla o la ventana, poner los colores, elegir el lápiz, dibujar, esperar
(`key_wait`, un `EventLoop`) y cerrar.
""",
        "en": """\
Drawing with the system's `graphics.library`: points, lines, rectangles, circles, polygons and text, with the
palette colours (pens).

**Where they draw.** Every `gfx_*` draws on the current target:

- the window opened last, with `Window X ... end` and `X.open` or with `window_create`; `window_use` picks another;
- the screen opened with `screen_open` or `screen_open_custom`, if there is no window;
- an off-screen bitmap, between `bitmap_draw_to` and `bitmap_draw_screen`;
- the MUI drawing area, inside the function given to `mui_canvas_on_draw`.

Open one of those before drawing. Coordinates are pixels from the top left corner of the target. In Dash's
windows that is the corner inside the borders: (0, 0) does not touch the title bar. What falls outside the target
is not drawn.

**Colours.** You draw with a palette colour number, the pen: `gfx_pen(2)`. A screen of depth 3 has 8 colours (0
to 7); one of depth 5, 32. `gfx_rgb` and `gfx_rgb8` change how a palette colour looks. On the Workbench the
colours belong to every program: to change them without getting in the way, open a screen of your own. To draw
with any RGB colour without thinking about the palette there are `color_pen` (Fonts and colors) and
`gfx_pixel_rgb` (Transparency and gradients).

**The usual flow:** open the screen or the window, set the colours, pick the pen, draw, wait (`key_wait`, an
`EventLoop`) and close.
""",
        "example": "tests/test_doc_graficos.dash",
    },
}

FUNCS = {
    # ---------------------------------------------------------------- Gráficos básicos
    "gfx_pen": {
        "es": """\
- `color`: el número de color de la paleta, de 0 al último de la pantalla (7 con profundidad 3, 31 con 5).

El color de las líneas, los puntos, los rellenos y el texto que vienen después. Sigue puesto hasta el siguiente
`gfx_pen`. Llamarlo con el color que ya tiene no cuesta nada, así que se puede poner en cada vuelta de un bucle.
""",
        "en": """\
- `color`: the palette colour number, from 0 to the screen's last one (7 at depth 3, 31 at depth 5).

The colour of the lines, points, fills and text that come next. It stays set until the next `gfx_pen`. Calling it
with the colour it already has costs nothing, so it can go in every turn of a loop.
""",
        "see": ["gfx_pen_bg", "gfx_rgb", "color_pen"],
    },
    "gfx_pen_bg": {
        "es": """\
- `color`: un número de color de la paleta.

El color de fondo. Se usa en el texto con el modo JAM2 (`gfx_mode(1)`, el fondo de cada letra) y en los huecos de
las líneas con patrón (`gfx_pattern`) en ese modo.
""",
        "en": """\
- `color`: a palette colour number.

The background colour. It is used by text in JAM2 mode (`gfx_mode(1)`, the background of each letter) and by the
gaps of patterned lines (`gfx_pattern`) in that mode.
""",
        "see": ["gfx_pen", "gfx_mode"],
    },
    "gfx_pen_outline": {
        "es": """\
- `color`: un número de color de la paleta.

El color del borde. Lo usa `gfx_flood` con el modo 0: rellena hasta encontrar ese color.
""",
        "en": """\
- `color`: a palette colour number.

The outline colour. `gfx_flood` uses it in mode 0: it fills until it meets that colour.
""",
        "see": ["gfx_flood"],
    },
    "gfx_mode": {
        "es": """\
- `mode`: 0 = JAM1, 1 = JAM2, 2 = COMPLEMENT, 4 = INVERSVID. Dash no tiene esas constantes: se pone el número.

Cómo se pinta. Con JAM1, lo normal, solo se pinta el lápiz: el texto no tapa lo que hay detrás. Con JAM2 el
texto lleva su fondo, del color de `gfx_pen_bg`. Con COMPLEMENT se invierten los bits de lo que ya hay: dibujar
dos veces lo mismo lo deja como estaba, útil para un cursor o un marco de selección. INVERSVID cambia de sitio
lápiz y fondo en el texto; se suma a los otros (`1 + 4`).
""",
        "en": """\
- `mode`: 0 = JAM1, 1 = JAM2, 2 = COMPLEMENT, 4 = INVERSVID. Dash has no such constants: use the number.

How things are painted. With JAM1, the normal one, only the pen is painted: text does not cover what is behind it.
With JAM2 text carries its background, in the colour of `gfx_pen_bg`. With COMPLEMENT the bits already there are
inverted: drawing the same thing twice leaves it as it was, handy for a cursor or a selection frame. INVERSVID
swaps pen and background in text; it adds to the others (`1 + 4`).
""",
        "see": ["gfx_pen", "gfx_pen_bg", "gfx_pattern"],
    },
    "gfx_pattern": {
        "es": """\
- `pattern`: 16 bits; cada bit a 1 es un píxel pintado. `0xFFFF` es la línea entera, `0xF0F0` discontinua y
  `0xAAAA` de puntos.

El patrón de las líneas que vienen después (`gfx_line`, `gfx_draw`, `gfx_box`). Se repite a lo largo de la línea.
Para volver a la línea entera: `gfx_pattern(0xFFFF)`.
""",
        "en": """\
- `pattern`: 16 bits; each bit set is a painted pixel. `0xFFFF` is a solid line, `0xF0F0` dashed and `0xAAAA`
  dotted.

The pattern of the lines that come next (`gfx_line`, `gfx_draw`, `gfx_box`). It repeats along the line. Back to
a solid line: `gfx_pattern(0xFFFF)`.
""",
        "see": ["gfx_line", "gfx_mode"],
    },
    "gfx_rgb": {
        "es": """\
- `index`: el color de la paleta que se cambia.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 15.

Lo que ya está dibujado con ese color cambia al momento: no se vuelve a dibujar nada. Cambia la paleta de la
pantalla propia, o la de la pantalla de la ventana si no hay. En el Workbench eso cambia los colores de todos los
programas. Sin pantalla ni ventana no hace nada.
""",
        "en": """\
- `index`: the palette colour to change.
- `r`, `g`, `b`: red, green and blue, from 0 to 15.

What is already drawn in that colour changes at once: nothing is drawn again. It changes the palette of the
program's own screen, or of the window's screen if there is none. On the Workbench that changes the colours of
every program. With no screen or window it does nothing.
""",
        "see": ["gfx_rgb8", "gfx_pen", "screen_open_custom"],
    },
    "gfx_rgb8": {
        "es": """\
- `index`: el color de la paleta que se cambia.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 255.

Como `gfx_rgb`, con 8 bits por componente. Exacto en AGA y en tarjetas gráficas. En OCS y ECS solo cuentan los
4 bits de arriba: 192 y 200 se ven igual.
""",
        "en": """\
- `index`: the palette colour to change.
- `r`, `g`, `b`: red, green and blue, from 0 to 255.

Like `gfx_rgb`, with 8 bits per component. Exact on AGA and graphics cards. On OCS and ECS only the top 4 bits
count: 192 and 200 look the same.
""",
        "see": ["gfx_rgb"],
    },
    "gfx_move": {
        "es": """\
- `x`, `y`: el punto, en píxeles.

Lleva el cursor de dibujo a ese punto sin pintar. Desde ahí empiezan `gfx_draw` y `gfx_text`.
""",
        "en": """\
- `x`, `y`: the point, in pixels.

Moves the drawing cursor to that point without painting. `gfx_draw` and `gfx_text` start from there.
""",
        "see": ["gfx_draw", "gfx_text"],
    },
    "gfx_draw": {
        "es": """\
- `x`, `y`: el final de la línea.

Una línea desde el cursor hasta ese punto, con el lápiz y el patrón. El cursor se queda en el final, así que
varios `gfx_draw` seguidos hacen una línea quebrada.
""",
        "en": """\
- `x`, `y`: the end of the line.

A line from the cursor to that point, with the pen and the pattern. The cursor stays at the end, so several
`gfx_draw` in a row make a polyline.
""",
        "see": ["gfx_move", "gfx_line"],
    },
    "gfx_line": {
        "es": """\
- `x1`, `y1`: el principio.
- `x2`, `y2`: el final.

Una línea entre dos puntos, con el lápiz y el patrón. Los dos puntos se pintan. Deja el cursor en el final.
""",
        "en": """\
- `x1`, `y1`: the start.
- `x2`, `y2`: the end.

A line between two points, with the pen and the pattern. Both points are painted. It leaves the cursor at the end.
""",
        "see": ["gfx_draw", "gfx_pattern", "gfx_box"],
    },
    "gfx_pixel": {
        "es": """\
- `x`, `y`: el punto.

Pinta un píxel con el lápiz. Para muchos píxeles es más rápido preparar la imagen en un búfer y dibujarla de una
vez con `gfx_pens_draw`.
""",
        "en": """\
- `x`, `y`: the point.

Paints one pixel with the pen. For many pixels it is faster to build the picture in a buffer and draw it at once
with `gfx_pens_draw`.
""",
        "see": ["gfx_pixel_read", "gfx_pens_draw"],
    },
    "gfx_pixel_read": {
        "es": """\
- `x`, `y`: el punto.

Devuelve el número de color de ese píxel, o -1 si está fuera del destino.
""",
        "en": """\
- `x`, `y`: the point.

Returns the colour number of that pixel, or -1 if it is outside the target.
""",
        "see": ["gfx_pixel"],
    },
    "gfx_rect": {
        "es": """\
- `x1`, `y1`: la esquina de arriba a la izquierda.
- `x2`, `y2`: la de abajo a la derecha, incluida.

Un rectángulo relleno con el lápiz. `x2` tiene que ser mayor o igual que `x1`, y `y2` que `y1`: al revés, el
sistema no garantiza lo que pinta. `gfx_rect(0, 0, 9, 9)` pinta 10 x 10 píxeles.
""",
        "en": """\
- `x1`, `y1`: the top left corner.
- `x2`, `y2`: the bottom right one, included.

A rectangle filled with the pen. `x2` must be greater than or equal to `x1`, and `y2` to `y1`: the other way round
the system does not promise what it paints. `gfx_rect(0, 0, 9, 9)` paints 10 x 10 pixels.
""",
        "see": ["gfx_box", "gfx_clear_color"],
    },
    "gfx_box": {
        "es": """\
- `x1`, `y1`, `x2`, `y2`: dos esquinas opuestas, incluidas.

El borde de un rectángulo, de un píxel de grueso, con el lápiz y el patrón. Deja el cursor en `x1`, `y1`.
""",
        "en": """\
- `x1`, `y1`, `x2`, `y2`: two opposite corners, included.

The outline of a rectangle, one pixel thick, with the pen and the pattern. It leaves the cursor at `x1`, `y1`.
""",
        "see": ["gfx_rect", "gfx_line"],
    },
    "gfx_ellipse": {
        "es": """\
- `cx`, `cy`: el centro.
- `rx`, `ry`: el radio horizontal y el vertical, en píxeles.

El borde de una elipse con el lápiz. En los modos de pantalla de píxeles alargados (640 x 256 en PAL) un círculo
se ve estirado: con `ry` la mitad de `rx` se ve redondo.
""",
        "en": """\
- `cx`, `cy`: the centre.
- `rx`, `ry`: the horizontal and vertical radius, in pixels.

The outline of an ellipse with the pen. On screen modes with tall pixels (640 x 256 PAL) a circle looks stretched:
with `ry` half of `rx` it looks round.
""",
        "see": ["gfx_ellipse_fill", "gfx_circle"],
    },
    "gfx_circle": {
        "es": """\
- `cx`, `cy`: el centro.
- `r`: el radio, en píxeles.

El borde de un círculo con el lápiz. Es `gfx_ellipse(cx, cy, r, r)`.
""",
        "en": """\
- `cx`, `cy`: the centre.
- `r`: the radius, in pixels.

The outline of a circle with the pen. It is `gfx_ellipse(cx, cy, r, r)`.
""",
        "see": ["gfx_circle_fill", "gfx_ellipse"],
    },
    "gfx_ellipse_fill": {
        "es": """\
- `cx`, `cy`: el centro.
- `rx`, `ry`: los radios.

Una elipse rellena con el lápiz. Va en cualquier destino: si no tiene los búferes de relleno del sistema (una zona
de MUI), Dash le presta los suyos mientras dura.
""",
        "en": """\
- `cx`, `cy`: the centre.
- `rx`, `ry`: the radii.

An ellipse filled with the pen. It works on any target: if it lacks the system's fill buffers (a MUI area), Dash
lends it its own while it lasts.
""",
        "see": ["gfx_ellipse", "gfx_circle_fill", "gfx_poly_begin"],
    },
    "gfx_circle_fill": {
        "es": """\
- `cx`, `cy`: el centro.
- `r`: el radio.

Un círculo relleno con el lápiz. Es `gfx_ellipse_fill(cx, cy, r, r)`.
""",
        "en": """\
- `cx`, `cy`: the centre.
- `r`: the radius.

A circle filled with the pen. It is `gfx_ellipse_fill(cx, cy, r, r)`.
""",
        "see": ["gfx_circle", "gfx_ellipse_fill"],
    },
    "gfx_flood": {
        "es": """\
- `x`, `y`: el punto donde empieza el relleno.
- `mode`: 1 = rellena los píxeles vecinos que tienen el mismo color que el de `x`, `y`; 0 = rellena hasta
  encontrar el color del borde (`gfx_pen_outline`).

Rellena con el lápiz, como el bote de pintura de un programa de dibujo. Si la figura tiene un hueco en el borde,
el relleno se sale por él.
""",
        "en": """\
- `x`, `y`: the point where the fill starts.
- `mode`: 1 = fills the neighbouring pixels that have the same colour as the one at `x`, `y`; 0 = fills until it
  meets the outline colour (`gfx_pen_outline`).

Fills with the pen, like the paint bucket of a paint program. If the shape has a gap in its border, the fill leaks
out through it.
""",
        "see": ["gfx_pen_outline", "gfx_poly_begin"],
    },
    "gfx_text": {
        "es": """\
- `str`: el texto.

Escribe el texto en el cursor con la fuente actual y el lápiz. El cursor marca la línea de base de las letras, no
su parte de arriba: con la fuente topaz de 8 puntos, el texto ocupa desde `y - 6` hasta `y + 1`. Después, el cursor
queda al final del texto. No parte líneas: un texto largo se corta en el borde.
""",
        "en": """\
- `str`: the text.

Writes the text at the cursor with the current font and the pen. The cursor marks the baseline of the letters, not
their top: with the 8 point topaz font the text takes from `y - 6` to `y + 1`. Afterwards the cursor sits at the
end of the text. It does not wrap: a long text is cut at the edge.
""",
        "see": ["gfx_text_at", "gfx_text_len", "font_use", "font_baseline"],
    },
    "gfx_text_at": {
        "es": """\
- `x`, `y`: dónde empieza el texto; `y` es la línea de base.
- `str`: el texto.

Es `gfx_move(x, y)` y `gfx_text(str)`. Para escribir con la esquina de arriba en `y`, suma la línea de base de la
fuente: `gfx_text_at(x, y + font_baseline(), "Hola")`.
""",
        "en": """\
- `x`, `y`: where the text starts; `y` is the baseline.
- `str`: the text.

It is `gfx_move(x, y)` and `gfx_text(str)`. To write with the top at `y`, add the font's baseline:
`gfx_text_at(x, y + font_baseline(), "Hello")`.
""",
        "see": ["gfx_text", "gfx_text_len", "font_baseline"],
    },
    "gfx_text_len": {
        "es": """\
- `str`: el texto.

Devuelve cuántos píxeles de ancho ocupa el texto con la fuente actual, sin dibujarlo. Sirve para centrar:
`gfx_text_at((ancho - gfx_text_len(t)) / 2, y, t)`.
""",
        "en": """\
- `str`: the text.

Returns how many pixels wide the text is with the current font, without drawing it. Useful to centre:
`gfx_text_at((width - gfx_text_len(t)) / 2, y, t)`.
""",
        "see": ["gfx_text", "font_height"],
    },
    "gfx_clear": {
        "es": """\
Pinta todo el destino con el color 0. En una ventana es su interior.
""",
        "en": """\
Paints the whole target with colour 0. In a window, its inside.
""",
        "see": ["gfx_clear_color"],
    },
    "gfx_clear_color": {
        "es": """\
- `color`: un número de color de la paleta.

Pinta todo el destino con ese color.
""",
        "en": """\
- `color`: a palette colour number.

Paints the whole target with that colour.
""",
        "see": ["gfx_clear", "gfx_rect"],
    },
    "gfx_scroll": {
        "es": """\
- `dx`, `dy`: cuántos píxeles se desplaza. Positivo mueve el contenido hacia la izquierda (`dx`) o hacia
  arriba (`dy`); negativo, al revés.
- `x1`, `y1`, `x2`, `y2`: el rectángulo que se desplaza, esquinas incluidas.

Mueve lo que hay dentro del rectángulo y pinta con el color de fondo (`gfx_pen_bg`) la franja que queda libre.
Para un texto que sube o un fondo que avanza.
""",
        "en": """\
- `dx`, `dy`: how many pixels it moves. Positive moves the contents left (`dx`) or up (`dy`); negative, the other
  way.
- `x1`, `y1`, `x2`, `y2`: the rectangle that scrolls, corners included.

Moves what is inside the rectangle and paints the strip left free with the background colour (`gfx_pen_bg`). For
text that scrolls up or a background that moves along.
""",
        "see": ["gfx_copy", "gfx_pen_bg"],
    },
    "gfx_poly_begin": {
        "es": """\
- `x`, `y`: el primer vértice.

Empieza un polígono relleno. Después van los vértices con `gfx_poly_add` y se cierra con `gfx_poly_end`, que es
cuando se pinta. Hasta 100 vértices.
""",
        "en": """\
- `x`, `y`: the first vertex.

Starts a filled polygon. Then come the vertices with `gfx_poly_add`, and `gfx_poly_end` closes it, which is when
it is painted. Up to 100 vertices.
""",
        "see": ["gfx_poly_add", "gfx_poly_end"],
    },
    "gfx_poly_add": {
        "es": """\
- `x`, `y`: el siguiente vértice.

Añade un vértice al polígono que empezó `gfx_poly_begin`. Sin un `gfx_poly_begin` antes no hace nada.
""",
        "en": """\
- `x`, `y`: the next vertex.

Adds a vertex to the polygon started by `gfx_poly_begin`. Without a `gfx_poly_begin` before, it does nothing.
""",
        "see": ["gfx_poly_begin", "gfx_poly_end"],
    },
    "gfx_poly_end": {
        "es": """\
Cierra el polígono uniendo el último vértice con el primero y lo rellena con el lápiz.
""",
        "en": """\
Closes the polygon joining the last vertex to the first and fills it with the pen.
""",
        "see": ["gfx_poly_begin", "gfx_poly_add"],
    },
    "gfx_pens_draw": {
        "es": """\
- `buffer`: un búfer (`buffer_alloc`) con un byte por píxel, el número de color, fila tras fila.
- `width`, `height`: el tamaño de la imagen en píxeles. El búfer tiene que tener al menos `width * height` bytes.
- `x`, `y`: dónde va la esquina de arriba a la izquierda.
- `zoom`: cuántas veces se agranda cada píxel; 1 = tamaño real, 2 = cada píxel ocupa 2 x 2.

Dibuja la imagen entera en una llamada, mucho más rápido que un `gfx_pixel` por píxel. Va bien para imágenes que
el programa calcula (un fractal, un mapa) o que lee de un fichero.
""",
        "en": """\
- `buffer`: a buffer (`buffer_alloc`) with one byte per pixel, the colour number, row after row.
- `width`, `height`: the picture's size in pixels. The buffer must hold at least `width * height` bytes.
- `x`, `y`: where the top left corner goes.
- `zoom`: how many times each pixel is enlarged; 1 = real size, 2 = each pixel takes 2 x 2.

Draws the whole picture in one call, much faster than one `gfx_pixel` per pixel. Good for pictures the program
computes (a fractal, a map) or reads from a file.
""",
        "see": ["gfx_pixel", "buffer_alloc", "gfx_rgb_draw"],
    },
    "gfx_copy": {
        "es": """\
- `sx`, `sy`: la esquina de arriba a la izquierda de la zona que se copia.
- `w`, `h`: su ancho y alto.
- `dx`, `dy`: dónde va la copia.

Copia un rectángulo del destino a otro sitio del mismo destino. La zona de origen no se borra. Para copiar desde
un bitmap fuera de pantalla están los `bitmap_*`.
""",
        "en": """\
- `sx`, `sy`: the top left corner of the area to copy.
- `w`, `h`: its width and height.
- `dx`, `dy`: where the copy goes.

Copies a rectangle of the target to another place in the same target. The source area is not cleared. To copy from
an off-screen bitmap there are the `bitmap_*` functions.
""",
        "see": ["gfx_scroll", "bitmap_draw_to"],
    },
}
