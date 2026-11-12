"""Fuentes y colores (FONT_FUNCTIONS), transparencia (BLEND_FUNCTIONS), RGB (RGB_FUNCTIONS), imágenes con datatypes
(IMAGE_FUNCTIONS), TrueType (TTF_FUNCTIONS) e imágenes decodificadas por el programa (IMGDEC_FUNCTIONS)."""

GROUPS = {
    "FONT_FUNCTIONS": {
        "es": """\
Escribir con otras fuentes y elegir colores por su valor RGB.

**Fuentes.** `font_open` abre una fuente del sistema (de `FONTS:`) de un tamaño; `font_use` hace que `gfx_text` y
`gfx_text_at` escriban con ella en el destino actual. `font_height`, `font_baseline` y `font_text_width` miden con
la fuente puesta. Para fuentes TrueType, `font_from_ttf`.

**Colores RGB.** En una pantalla de paleta solo hay unos pocos colores. `color_pen(r, g, b)` busca el más parecido
de la pantalla (o reserva uno libre) y devuelve su número, para `gfx_pen`. Cuando ya no hace falta,
`color_pen_free`.
""",
        "en": """\
Writing with other fonts and choosing colours by their RGB value.

**Fonts.** `font_open` opens a system font (from `FONTS:`) at a size; `font_use` makes `gfx_text` and `gfx_text_at`
write with it on the current target. `font_height`, `font_baseline` and `font_text_width` measure with the font in
use. For TrueType fonts, `font_from_ttf`.

**RGB colours.** A palette screen has only a few colours. `color_pen(r, g, b)` finds the closest one on the screen
(or takes a free one) and returns its number, for `gfx_pen`. When it is no longer needed, `color_pen_free`.
""",
        "example": "tests/test_doc_fuentes.dash",
    },
    "BLEND_FUNCTIONS": {
        "es": """\
Color semitransparente sobre lo ya dibujado. En pantallas de color verdadero (RTG de 15 bits o más) se mezcla de
verdad; en las de paleta se imita con un tramado de puntos del color más cercano.
""",
        "en": """\
Semi-transparent colour over what is already drawn. On true-colour screens (RTG of 15 bits or more) it really
blends; on palette screens it is imitated with a dot pattern of the closest colour.
""",
    },
    "RGB_FUNCTIONS": {
        "es": """\
Dibujar una imagen que el programa tiene en un búfer, con 3 bytes por píxel (rojo, verde, azul), como un fotograma
de vídeo. En RTG va directa; en una pantalla de paleta cada píxel toma el color más cercano.
""",
        "en": """\
Drawing a picture the program holds in a buffer, 3 bytes per pixel (red, green, blue), like a video frame. On RTG
it goes straight; on a palette screen each pixel takes the closest colour.
""",
    },
    "IMAGE_FUNCTIONS": {
        "es": """\
Imágenes de fichero con los datatypes del sistema: ILBM siempre; PNG, GIF o JPEG si están instalados sus
datatypes. La imagen se adapta a los colores de la pantalla donde se dibuja. Cada imagen es un número que se
dibuja las veces que haga falta y se libera con `image_free` (al acabar, las que queden). Para decodificar sin
datatypes, `image_decode`.
""",
        "en": """\
Pictures from files with the system's datatypes: always ILBM; PNG, GIF or JPEG if their datatypes are installed.
The picture adapts to the colours of the screen it is drawn on. Each picture is a number drawn as many times as
needed and freed with `image_free` (at the end, those left). To decode without datatypes, `image_decode`.
""",
    },
    "TTF_FUNCTIONS": {
        "es": """\
Fuentes TrueType (TTF, OTF con contornos TrueType, WOFF y WOFF2) convertidas a una fuente del Amiga de un tamaño,
con sus caracteres Latin-1. Se escribe con ellas con `font_use` como con cualquier otra. Las usa Tachyon para las
fuentes de las páginas web.
""",
        "en": """\
TrueType fonts (TTF, OTF with TrueType outlines, WOFF and WOFF2) turned into an Amiga font of one size, with their
Latin-1 characters. You write with them via `font_use` like any other. Tachyon uses them for web page fonts.
""",
    },
    "IMGDEC_FUNCTIONS": {
        "es": """\
Decodificar JPEG, WebP, PNG, GIF, BMP y SVG con código del propio programa, sin datatypes: va en cualquier Amiga.
El resultado son píxeles RGB o RGBA en memoria (`image_decoded_*`); `image_from_decoded` los convierte en una
imagen para `image_draw`. Decodificar una imagen grande tarda: `image_decode_start` lo hace en otro proceso para
que la ventana siga respondiendo.
""",
        "en": """\
Decoding JPEG, WebP, PNG, GIF, BMP and SVG with the program's own code, without datatypes: it works on any Amiga.
The result is RGB or RGBA pixels in memory (`image_decoded_*`); `image_from_decoded` turns them into a picture for
`image_draw`. Decoding a big picture takes time: `image_decode_start` does it in another process so the window keeps
responding.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_IMG_ES = "- `image`: la imagen.\n"
_IMG_EN = "- `image`: the picture.\n"
_D_ES = "- `d`: la imagen decodificada.\n"
_D_EN = "- `d`: the decoded picture.\n"

FUNCS = {
    # ------------------------------------------------------------ fuentes y colores
    "font_open": _f("""\
- `name`: el nombre de la fuente con `.font`: `"helvetica.font"`, `"topaz.font"`.
- `size`: el alto en píxeles, 2 como poco.

Abre la fuente; si no tiene ese tamaño, el sistema da el más cercano (`font_size` dice cuál). Devuelve la fuente, o
0 si no existe.
""", """\
- `name`: the font's name with `.font`: `"helvetica.font"`, `"topaz.font"`.
- `size`: the height in pixels, at least 2.

Opens the font; if it lacks that size, the system gives the closest (`font_size` says which). Returns the font, or 0
if it does not exist.
""", ["font_use", "font_close", "font_from_ttf"]),
    "font_use": _f("""\
- `font`: una fuente de `font_open` o `font_from_ttf`.

Desde ahora `gfx_text` escribe con ella en el destino actual.
""", """\
- `font`: a font from `font_open` or `font_from_ttf`.

From now on `gfx_text` writes with it on the current target.
""", ["font_open", "font_style", "gfx_text"]),
    "font_close": _f("- `font`: la fuente.\n\nLa cierra. Las abiertas se cierran solas al acabar.\n",
                     "- `font`: the font.\n\nCloses it. Open fonts close on their own at the end.\n", ["font_open"]),
    "font_style": _f("""\
- `style`: sumados: 0 normal, 1 subrayado, 2 negrita, 4 cursiva (`2 + 4` negrita y cursiva).

El estilo del texto que viene. Si la fuente no tiene ese estilo dibujado, el sistema lo imita.
""", """\
- `style`: added up: 0 normal, 1 underlined, 2 bold, 4 italic (`2 + 4` bold italic).

The style of the text that follows. If the font has no drawn version of that style, the system imitates it.
""", ["font_use"]),
    "font_height": _f("Devuelve el alto en píxeles de la fuente puesta: lo que hay entre una línea de texto y la siguiente.\n",
                      "Returns the height in pixels of the font in use: the distance from one line of text to the next.\n",
                      ["font_baseline", "font_text_width"]),
    "font_baseline": _f("""\
Devuelve cuántos píxeles hay desde arriba de las letras hasta su línea de base. `gfx_text_at` escribe con la línea
de base en `y`: para que la parte de arriba quede en `y`, se le suma esto.
""", """\
Returns how many pixels there are from the top of the letters to their baseline. `gfx_text_at` writes with the
baseline at `y`: to put the top at `y`, add this.
""", ["gfx_text_at", "font_height"]),
    "font_text_width": _f("- `text`: el texto.\n\nDevuelve su ancho en píxeles con la fuente y el estilo puestos.\n",
                          "- `text`: the text.\n\nReturns its width in pixels with the font and style in use.\n",
                          ["gfx_text_len"]),
    "font_size": _f("- `font`: la fuente.\n\nDevuelve el tamaño que dio el sistema, que puede no ser el pedido.\n",
                    "- `font`: the font.\n\nReturns the size the system gave, which may differ from the one asked for.\n",
                    ["font_open"]),
    "color_pen": _f("""\
- `r`, `g`, `b`: el color, de 0 a 255.

Devuelve el número del color de la pantalla de dibujo más parecido, para `gfx_pen`. En el Workbench o en otra
pantalla compartida, reserva el color para el programa (uno exacto, si hay sitio) y cada `color_pen` necesita su
`color_pen_free`. En una pantalla propia, toda su paleta es del programa: da el más parecido de los que tiene.
""", """\
- `r`, `g`, `b`: the colour, 0 to 255.

Returns the number of the closest colour on the drawing screen, for `gfx_pen`. On the Workbench or another shared
screen it reserves the colour for the program (an exact one, if there is room) and each `color_pen` needs its
`color_pen_free`. On a screen of your own the whole palette is the program's: it gives the closest one it has.
""", ["color_pen_free", "gfx_pen"]),
    "color_pen_free": _f("""\
- `pen`: lo que dio `color_pen`.

Avisa de que ese color ya no hace falta. Cuando no queda ningún uso, el sistema puede dárselo a otro programa.
""", """\
- `pen`: what `color_pen` gave.

Says that colour is no longer needed. When no use is left, the system may give it to another program.
""", ["color_pen"]),
    # ------------------------------------------------------------ transparencia
    "gfx_blend_rect": _f("""\
- `x1`, `y1`, `x2`, `y2`: el rectángulo, esquinas incluidas.
- `rgb`: el color, `0xRRGGBB`.
- `alpha`: cuánto tapa, de 0 (nada) a 255 (del todo).

Mezcla el color con lo que ya hay dentro del rectángulo: para oscurecer un fondo detrás de un texto o un panel
translúcido.
""", """\
- `x1`, `y1`, `x2`, `y2`: the rectangle, corners included.
- `rgb`: the colour, `0xRRGGBB`.
- `alpha`: how much it covers, 0 (nothing) to 255 (fully).

Blends the colour with what is already inside the rectangle: to darken a background behind a text or a translucent
panel.
""", ["gfx_gradient_rect"]),
    "gfx_gradient_rect": _f("""\
- `x1`, `y1`, `x2`, `y2`: el rectángulo.
- `rgb1`, `alpha1`: el color y la transparencia del principio.
- `rgb2`, `alpha2`: los del final.
- `vertical`: `true` de arriba abajo, `false` de izquierda a derecha.

Un degradado entre los dos, mezclado con lo dibujado.
""", """\
- `x1`, `y1`, `x2`, `y2`: the rectangle.
- `rgb1`, `alpha1`: the colour and transparency at the start.
- `rgb2`, `alpha2`: those at the end.
- `vertical`: `true` top to bottom, `false` left to right.

A gradient between the two, blended with what is drawn.
""", ["gfx_blend_rect"]),
    "gfx_pixel_rgb": _f("""\
- `x`, `y`: el punto.

Devuelve el color de ese píxel como `0xRRGGBB`; en una pantalla de paleta, el de su número de color.
""", """\
- `x`, `y`: the point.

Returns that pixel's colour as `0xRRGGBB`; on a palette screen, the one of its colour number.
""", ["gfx_pixel_read"]),
    # ------------------------------------------------------------ RGB
    "gfx_rgb_draw": _f("""\
- `buffer`: los píxeles, 3 bytes cada uno (rojo, verde, azul), fila tras fila.
- `width`, `height`: el tamaño de la imagen.
- `x`, `y`: dónde va.

La dibuja de una vez. En una pantalla de paleta, cada píxel toma el color más cercano.
""", """\
- `buffer`: the pixels, 3 bytes each (red, green, blue), row after row.
- `width`, `height`: the picture's size.
- `x`, `y`: where it goes.

Draws it in one go. On a palette screen, each pixel takes the closest colour.
""", ["gfx_rgb_draw_scaled", "gfx_pens_draw"]),
    "gfx_rgb_draw_scaled": _f("""\
- `buffer`, `width`, `height`: como en `gfx_rgb_draw`.
- `x`, `y`: dónde va.
- `dest_width`, `dest_height`: el tamaño con el que se dibuja.

La dibuja agrandada o reducida, tomando para cada punto el píxel más cercano.
""", """\
- `buffer`, `width`, `height`: as in `gfx_rgb_draw`.
- `x`, `y`: where it goes.
- `dest_width`, `dest_height`: the size it is drawn at.

Draws it enlarged or reduced, taking the nearest pixel for each point.
""", ["gfx_rgb_draw"]),
    # ------------------------------------------------------------ datatypes
    "image_load": _f("""\
- `file`: la imagen: ILBM; PNG, GIF o JPEG si están sus datatypes.

La carga ya adaptada a los colores de la pantalla donde se dibuja ahora. Devuelve la imagen, o 0 si no se puede.
""", """\
- `file`: the picture: ILBM; PNG, GIF or JPEG if their datatypes are installed.

Loads it already adapted to the colours of the screen being drawn on. Returns the picture, or 0 if it cannot.
""", ["image_draw", "image_free", "image_decode"]),
    "image_width": _f(_IMG_ES + "\nDevuelve su ancho en píxeles.\n", _IMG_EN + "\nReturns its width in pixels.\n", ["image_height"]),
    "image_height": _f(_IMG_ES + "\nDevuelve su alto en píxeles.\n", _IMG_EN + "\nReturns its height in pixels.\n", ["image_width"]),
    "image_draw": _f(_IMG_ES + "- `x`, `y`: dónde va su esquina.\n\nLa dibuja en el destino actual; los píxeles transparentes dejan ver lo de debajo.\n",
                     _IMG_EN + "- `x`, `y`: where its corner goes.\n\nDraws it on the current target; transparent pixels let what is underneath show.\n",
                     ["image_draw_part", "image_scale"]),
    "image_draw_part": _f(_IMG_ES + """\
- `sx`, `sy`: la esquina de la parte, dentro de la imagen.
- `x`, `y`: dónde va.
- `w`, `h`: el tamaño de la parte.

Dibuja solo esa parte: para una imagen con varias piezas (iconos, letras).
""", _IMG_EN + """\
- `sx`, `sy`: the part's corner, inside the picture.
- `x`, `y`: where it goes.
- `w`, `h`: the part's size.

Draws only that part: for a picture holding several pieces (icons, letters).
""", ["image_draw"]),
    "image_scale": _f(_IMG_ES + "- `w`, `h`: el tamaño nuevo.\n\nDevuelve una copia de ese tamaño, otra imagen que también hay que liberar, o 0.\n",
                      _IMG_EN + "- `w`, `h`: the new size.\n\nReturns a copy at that size, another picture to free too, or 0.\n",
                      ["image_draw"]),
    "image_free": _f(_IMG_ES + "\nLa libera. Las que queden se liberan al acabar.\n", _IMG_EN + "\nFrees it. Those left are freed at the end.\n",
                     ["image_load"]),
    "image_from_rgb": _f("""\
- `buffer`: los píxeles, fila tras fila: 3 bytes (RGB) o 4 (RGBA).
- `width`, `height`: el tamaño.
- `alpha`: `true` si hay 4 bytes por píxel. La transparencia se mezcla en RTG; en una pantalla de paleta, un píxel
  se dibuja si su alfa es 128 o más.

Devuelve una imagen con esos píxeles, para `image_draw`, o 0. En pantallas de paleta necesita AmigaOS 3.5 o más.
""", """\
- `buffer`: the pixels, row after row: 3 bytes (RGB) or 4 (RGBA).
- `width`, `height`: the size.
- `alpha`: `true` if there are 4 bytes per pixel. Transparency blends on RTG; on a palette screen a pixel is drawn
  if its alpha is 128 or more.

Returns a picture with those pixels, for `image_draw`, or 0. On palette screens it needs AmigaOS 3.5 or later.
""", ["image_draw", "image_from_decoded"]),
    # ------------------------------------------------------------ TrueType
    "font_from_ttf": _f("""\
- `file`: el fichero de la fuente.
- `size`: el tamaño en píxeles.
- `width`: el ancho en tanto por ciento del normal; 0 = 100.

Devuelve una fuente con sus caracteres Latin-1 a ese tamaño, para `font_use`, o 0 si no se puede. Se libera con
`font_ttf_free`.
""", """\
- `file`: the font file.
- `size`: the size in pixels.
- `width`: the width as a percentage of the normal one; 0 = 100.

Returns a font with its Latin-1 characters at that size, for `font_use`, or 0 if it cannot. Free it with
`font_ttf_free`.
""", ["font_use", "font_ttf_free"]),
    "font_ttf_icon": _f("""\
- `file`: una fuente de iconos (de las que usan las webs).
- `size`: el tamaño.
- `code`: el código Unicode del icono.

Devuelve una fuente cuya letra "A" es ese icono: se dibuja escribiendo "A" con ella. 0 si no se puede.
""", """\
- `file`: an icon font (the kind web pages use).
- `size`: the size.
- `code`: the icon's Unicode code.

Returns a font whose letter "A" is that icon: you draw it by writing "A" with it. 0 if it cannot.
""", ["font_from_ttf"]),
    "font_ttf_free": _f("- `font`: una fuente de `font_from_ttf`.\n\nLa libera. No mientras una ventana siga escribiendo con ella.\n",
                        "- `font`: a `font_from_ttf` font.\n\nFrees it. Not while a window is still writing with it.\n",
                        ["font_from_ttf"]),
    "font_ttf_forget": _f("""\
- `file`: el fichero.

`font_from_ttf` guarda en memoria los 8 últimos ficheros para sacar otros tamaños sin leerlos otra vez; este lo
olvida. Para cuando el fichero ha cambiado.
""", """\
- `file`: the file.

`font_from_ttf` keeps the last 8 files in memory to make other sizes without reading them again; this forgets that
one. For when the file has changed.
""", ["font_from_ttf"]),
    # ------------------------------------------------------------ imágenes decodificadas
    "image_decode": _f("""\
- `file`: la imagen: JPEG, WebP, PNG, GIF, BMP o SVG.
- `maxw`, `maxh`: el tamaño máximo; se reduce hasta que no pase mucho de él. 0, 0 = su tamaño.

Devuelve la imagen decodificada, o 0 si no se puede. Se lee con `image_decoded_*` y se libera con
`image_decoded_free`.
""", """\
- `file`: the picture: JPEG, WebP, PNG, GIF, BMP or SVG.
- `maxw`, `maxh`: the maximum size; it is reduced until it is not much bigger. 0, 0 = its own size.

Returns the decoded picture, or 0 if it cannot. Read it with `image_decoded_*` and free it with
`image_decoded_free`.
""", ["image_decode_start", "image_from_decoded", "image_decoded_free"]),
    "image_decode_start": _f("""\
- `file`, `maxw`, `maxh`: como en `image_decode`.

Empieza a decodificar en otro proceso y vuelve enseguida. Devuelve un número para `image_decode_ready` e
`image_decode_finish`, o 0 si no pudo empezar.

Si el programa acaba con una sin terminar, esa decodificación se para y el programa no la espera. Una imagen que
acabó y no se recogió con `image_decode_finish` se libera al salir.
""", """\
- `file`, `maxw`, `maxh`: as in `image_decode`.

Starts decoding in another process and returns at once. Returns a number for `image_decode_ready` and
`image_decode_finish`, or 0 if it could not start.

If the program ends with one unfinished, that decode stops and the program does not wait for it. A picture that
was decoded but never taken with `image_decode_finish` is freed at the exit.
""", ["image_decode_ready", "image_decode_finish"]),
    "image_decode_ready": _f("- `t`: el número de `image_decode_start`.\n\nDevuelve `true` cuando ha acabado, sin esperar.\n",
                             "- `t`: the number from `image_decode_start`.\n\nReturns `true` once it has finished, without waiting.\n",
                             ["image_decode_finish"]),
    "image_decode_finish": _f("""\
- `t`: el número de `image_decode_start`.

Devuelve la imagen decodificada, como `image_decode`, o 0. Si aún no acabó, espera. Hay que llamarla siempre: libera
el proceso.
""", """\
- `t`: the number from `image_decode_start`.

Returns the decoded picture, like `image_decode`, or 0. If it has not finished, it waits. Always call it: it frees
the process.
""", ["image_decode_start"]),
    "image_decoded_width": _f(_D_ES + "\nDevuelve su ancho en píxeles.\n", _D_EN + "\nReturns its width in pixels.\n", ["image_decoded_height"]),
    "image_decoded_height": _f(_D_ES + "\nDevuelve su alto en píxeles.\n", _D_EN + "\nReturns its height in pixels.\n", ["image_decoded_width"]),
    "image_decoded_alpha": _f(_D_ES + "\nDevuelve `true` si tiene transparencia: 4 bytes por píxel (RGBA); si no, 3 (RGB).\n",
                              _D_EN + "\nReturns `true` if it has transparency: 4 bytes per pixel (RGBA); otherwise 3 (RGB).\n",
                              ["image_decoded_pixels"]),
    "image_decoded_pixels": _f(_D_ES + "\nDevuelve la dirección de sus píxeles, fila tras fila, para `buffer_get_byte` o `image_from_rgb`. Vive hasta `image_decoded_free`.\n",
                               _D_EN + "\nReturns the address of its pixels, row after row, for `buffer_get_byte` or `image_from_rgb`. It lives until `image_decoded_free`.\n",
                               ["image_decoded_alpha"]),
    "image_decoded_free": _f(_D_ES + "\nLa libera.\n", _D_EN + "\nFrees it.\n", ["image_decode"]),
    "image_from_decoded": _f(_D_ES + "\nDevuelve una imagen para `image_draw` con sus píxeles, o 0. Las dos se liberan por separado.\n",
                             _D_EN + "\nReturns a picture for `image_draw` with its pixels, or 0. Both are freed separately.\n",
                             ["image_from_decoded_size", "image_from_rgb"]),
    "image_from_decoded_size": _f(_D_ES + """\
- `w`, `h`: el tamaño de la imagen nueva.

Como `image_from_decoded`, a ese tamaño y con los bordes suaves: cada punto es la media de los que cubre.
""", _D_EN + """\
- `w`, `h`: the new picture's size.

Like `image_from_decoded`, at that size and with smooth edges: each point is the average of those it covers.
""", ["image_from_decoded"]),
}
