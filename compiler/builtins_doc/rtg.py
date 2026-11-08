"""RTG (RTG_FUNCTIONS)."""

GROUPS = {
    "RTG_FUNCTIONS": {
        "es": """\
Tarjetas gráficas (RTG) con CyberGraphX o Picasso96: pantallas de 16, 24 o 32 bits donde cada píxel lleva su
color RGB, sin paleta.

`rtg_available` dice si hay librería RTG y `rtg_is_active` si la pantalla de dibujo es de color verdadero. Los
colores van como `0xRRGGBB` (`rtg_rgb` los compone). En una pantalla de paleta, `rtg_write_pixel` y
`rtg_fill_rect` usan el color más parecido de la paleta; `rtg_write_array` y `rtg_read_array` solo funcionan en
RTG. Para dibujar con RGB en cualquier pantalla, también `color_pen` y `gfx_rgb_draw`.
""",
        "en": """\
Graphics cards (RTG) with CyberGraphX or Picasso96: 16, 24 or 32-bit screens where each pixel carries its RGB
colour, without a palette.

`rtg_available` says whether there is an RTG library and `rtg_is_active` whether the drawing screen is true colour.
Colours go as `0xRRGGBB` (`rtg_rgb` builds them). On a palette screen, `rtg_write_pixel` and `rtg_fill_rect` use the
palette's closest colour; `rtg_write_array` and `rtg_read_array` only work on RTG. To draw with RGB on any screen,
there are also `color_pen` and `gfx_rgb_draw`.
""",
        "example": "tests/test_doc_rtg.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_C_ES = "- `color`: un color `0xRRGGBB`.\n"
_C_EN = "- `color`: a `0xRRGGBB` colour.\n"

FUNCS = {
    "rtg_available": _f("Devuelve `true` si está instalada CyberGraphX o Picasso96 (su `cybergraphics.library`).\n",
                        "Returns `true` if CyberGraphX or Picasso96 is installed (its `cybergraphics.library`).\n", ["rtg_is_active"]),
    "rtg_is_active": _f("Devuelve `true` si la pantalla donde se dibuja es de una tarjeta gráfica y de color verdadero.\n",
                        "Returns `true` if the screen being drawn on belongs to a graphics card and is true colour.\n", ["rtg_available"]),
    "rtg_get_depth": _f("Devuelve la profundidad en bits de la pantalla del programa o, si no hay, del Workbench: 8 de paleta, 16, 24 o 32 de color verdadero.\n",
                        "Returns the depth in bits of the program's screen or, without one, the Workbench's: 8 palette, 16, 24 or 32 true colour.\n",
                        ["rtg_get_width"]),
    "rtg_get_width": _f("Devuelve el ancho de la pantalla del programa o, si no hay, del Workbench.\n",
                        "Returns the width of the program's screen or, without one, the Workbench's.\n", ["rtg_get_height"]),
    "rtg_get_height": _f("Devuelve el alto de la pantalla del programa o, si no hay, del Workbench.\n",
                         "Returns the height of the program's screen or, without one, the Workbench's.\n", ["rtg_get_width"]),
    "rtg_alloc_bitmap": _f("""\
- `width`, `height`: el tamaño.
- `depth`: la profundidad en bits.

Pide un bitmap fuera de pantalla del formato de la tarjeta, para `rtg_blit`. Devuelve su dirección, o 0. Se libera
con `rtg_free_bitmap`.
""", """\
- `width`, `height`: the size.
- `depth`: the depth in bits.

Asks for an off-screen bitmap in the card's format, for `rtg_blit`. Returns its address, or 0. Free it with
`rtg_free_bitmap`.
""", ["rtg_free_bitmap", "rtg_blit"]),
    "rtg_free_bitmap": _f("- `bitmap`: el de `rtg_alloc_bitmap`.\n\nLo libera.\n", "- `bitmap`: the one from `rtg_alloc_bitmap`.\n\nFrees it.\n",
                          ["rtg_alloc_bitmap"]),
    "rtg_write_pixel": _f("- `x`, `y`: el punto.\n- `rgb`: el color `0xRRGGBB`.\n\nPinta el píxel; en una pantalla de paleta, con el color más parecido.\n",
                          "- `x`, `y`: the point.\n- `rgb`: the `0xRRGGBB` colour.\n\nPaints the pixel; on a palette screen, with the closest colour.\n",
                          ["rtg_read_pixel", "rtg_fill_rect"]),
    "rtg_read_pixel": _f("- `x`, `y`: el punto.\n\nDevuelve su color `0xRRGGBB`.\n", "- `x`, `y`: the point.\n\nReturns its `0xRRGGBB` colour.\n",
                         ["rtg_write_pixel", "gfx_pixel_rgb"]),
    "rtg_fill_rect": _f("- `x`, `y`: la esquina.\n- `w`, `h`: el tamaño.\n- `rgb`: el color `0xRRGGBB`.\n\nRellena el rectángulo; en una pantalla de paleta, con el color más parecido.\n",
                        "- `x`, `y`: the corner.\n- `w`, `h`: the size.\n- `rgb`: the `0xRRGGBB` colour.\n\nFills the rectangle; on a palette screen, with the closest colour.\n",
                        ["rtg_write_pixel"]),
    "rtg_write_array": _f("""\
- `buffer`: los píxeles, 4 bytes cada uno (alfa, rojo, verde, azul).
- `bpr`: los bytes de cada fila del búfer (normalmente `w * 4`).
- `x`, `y`, `w`, `h`: dónde y cuánto.

Copia el bloque a la pantalla de una vez. Solo en RTG: en una pantalla de paleta no hace nada (para eso,
`gfx_rgb_draw`).
""", """\
- `buffer`: the pixels, 4 bytes each (alpha, red, green, blue).
- `bpr`: the bytes per buffer row (usually `w * 4`).
- `x`, `y`, `w`, `h`: where and how much.

Copies the block to the screen in one go. RTG only: on a palette screen it does nothing (for that, `gfx_rgb_draw`).
""", ["rtg_read_array", "gfx_rgb_draw"]),
    "rtg_read_array": _f("- `buffer`, `bpr`, `x`, `y`, `w`, `h`: como en `rtg_write_array`.\n\nLee el bloque de la pantalla al búfer. Solo en RTG.\n",
                         "- `buffer`, `bpr`, `x`, `y`, `w`, `h`: as in `rtg_write_array`.\n\nReads the block from the screen into the buffer. RTG only.\n",
                         ["rtg_write_array"]),
    "rtg_rgb": _f("- `r`, `g`, `b`: de 0 a 255.\n\nDevuelve el color `0xRRGGBB`.\n", "- `r`, `g`, `b`: 0 to 255.\n\nReturns the `0xRRGGBB` colour.\n",
                  ["rtg_rgb_r", "rtg_argb"]),
    "rtg_argb": _f("- `a`, `r`, `g`, `b`: de 0 a 255; `a` es la opacidad.\n\nDevuelve el color `0xAARRGGBB`, para los búferes de `rtg_write_array`.\n",
                   "- `a`, `r`, `g`, `b`: 0 to 255; `a` is the opacity.\n\nReturns the `0xAARRGGBB` colour, for `rtg_write_array` buffers.\n",
                   ["rtg_rgb"]),
    "rtg_rgb_r": _f(_C_ES + "\nDevuelve su rojo, de 0 a 255.\n", _C_EN + "\nReturns its red, 0 to 255.\n", ["rtg_rgb_g", "rtg_rgb_b"]),
    "rtg_rgb_g": _f(_C_ES + "\nDevuelve su verde, de 0 a 255.\n", _C_EN + "\nReturns its green, 0 to 255.\n", ["rtg_rgb_r"]),
    "rtg_rgb_b": _f(_C_ES + "\nDevuelve su azul, de 0 a 255.\n", _C_EN + "\nReturns its blue, 0 to 255.\n", ["rtg_rgb_r"]),
    "rtg_best_mode": _f("- `width`, `height`, `depth`: lo que se quiere.\n\nDevuelve el modo de pantalla RTG que mejor le cuadra, o -1 si no hay (o no hay RTG).\n",
                        "- `width`, `height`, `depth`: what you want.\n\nReturns the RTG screen mode that fits best, or -1 if none (or no RTG).\n",
                        ["rtg_open_screen", "screen_open_mode"]),
    "rtg_open_screen": _f("""\
- `width`, `height`: el tamaño.
- `depth`: 16, 24 o 32 bits.
- `title`: el título.

Abre una pantalla propia en la tarjeta gráfica; si no hay un modo de ese tamaño, prueba con 640 x 480. Cierra antes
la pantalla propia que hubiera. Devuelve `false` sin RTG o sin modo.
""", """\
- `width`, `height`: the size.
- `depth`: 16, 24 or 32 bits.
- `title`: the title.

Opens a screen of your own on the graphics card; if there is no mode of that size, it tries 640 x 480. It closes any
screen of your own first. Returns `false` without RTG or without a mode.
""", ["rtg_best_mode", "screen_close"]),
    "rtg_blit": _f("""\
- `src`: un bitmap de `rtg_alloc_bitmap`.
- `sx`, `sy`: la esquina de origen.
- `dx`, `dy`: dónde va.
- `w`, `h`: el tamaño.

Copia esa parte del bitmap al destino de los `gfx_*`.
""", """\
- `src`: a bitmap from `rtg_alloc_bitmap`.
- `sx`, `sy`: the source corner.
- `dx`, `dy`: where it goes.
- `w`, `h`: the size.

Copies that part of the bitmap to the `gfx_*` target.
""", ["rtg_scale_blit"]),
    "rtg_scale_blit": _f("""\
- `src`: un bitmap de `rtg_alloc_bitmap`.
- `sx`, `sy`, `sw`, `sh`: la parte de origen.
- `dx`, `dy`, `dw`, `dh`: dónde va y a qué tamaño.

Como `rtg_blit`, agrandando o reduciendo.
""", """\
- `src`: a bitmap from `rtg_alloc_bitmap`.
- `sx`, `sy`, `sw`, `sh`: the source part.
- `dx`, `dy`, `dw`, `dh`: where it goes and at what size.

Like `rtg_blit`, enlarging or reducing.
""", ["rtg_blit"]),
}
