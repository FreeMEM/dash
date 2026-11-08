*[English](BUILTINS.en.md) | Castellano*

# Funciones built-in

> Generado por `tools/gen_builtins_doc.py` desde `compiler/amiga_builtins.py`. No editar a mano.

Las marcadas **sin implementar** están declaradas pero no tienen código C:
usarlas da el error `Builtin 'x' is declared but not implemented yet`.

Total: 961 funciones, 961 implementadas, 0 sin implementar.

## Gráficos básicos

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

**Ejemplo** (`tests/test_doc_graficos.dash`: se compila y se prueba en el emulador con los tests):

```dash
# Gráficos básicos: una pantalla propia con su paleta, una ventana y unas figuras.

Main
    screen_open_custom(320, 200, 3, "Dibujo")      # profundidad 3: 8 colores, del 0 al 7
    v = window_create("Figuras", 0, 12, 300, 150, 8)
    if v == 0
        Print "no se pudo abrir la ventana"
        screen_close()
        return
    end
    gfx_rgb(2, 15, 0, 0)           # el color 2, rojo
    gfx_rgb(3, 0, 0, 15)           # el 3, azul
    gfx_clear()

    gfx_pen(2)
    gfx_rect(10, 10, 60, 40)       # un rectángulo relleno
    gfx_pen(1)
    gfx_box(10, 10, 60, 40)        # y su borde

    gfx_circle(120, 40, 25)
    gfx_pen(3)
    gfx_flood(120, 40, 1)          # rellena el interior del círculo
    Print "dentro del circulo: #{gfx_pixel_read(120, 40)}"

    gfx_pen(2)
    gfx_poly_begin(200, 15)        # un triángulo
    gfx_poly_add(240, 65)
    gfx_poly_add(160, 65)
    gfx_poly_end()
    Print "triangulo: #{gfx_pixel_read(200, 50)}"

    gfx_pen(1)
    t = "Hola"
    gfx_text_at((300 - gfx_text_len(t)) / 2, 100, t)    # centrado

    time_delay(100)                # dos segundos para verlo; en un programa, key_wait() o un EventLoop
    window_close(v)
    screen_close()
end
```

**Índice.** Las que tienen enlace están explicadas más abajo.

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| [`gfx_pen(color)`](#gfx_pen) | — | Pone el color (lápiz) de dibujo |  |
| [`gfx_pen_bg(color)`](#gfx_pen_bg) | — | Pone el color de fondo |  |
| [`gfx_pen_outline(color)`](#gfx_pen_outline) | — | Pone el color del borde de los rellenos |  |
| [`gfx_mode(mode)`](#gfx_mode) | — | Pone el modo de dibujo (JAM1, JAM2, COMPLEMENT, INVERSVID) |  |
| [`gfx_pattern(pattern)`](#gfx_pattern) | — | Pone el patrón de las líneas (16 bits) |  |
| [`gfx_rgb(index, r, g, b)`](#gfx_rgb) | — | Cambia un color de la paleta (componentes de 4 bits, 0-15) |  |
| [`gfx_rgb8(index, r, g, b)`](#gfx_rgb8) | — | Cambia un color de la paleta (componentes de 8 bits, AGA) |  |
| [`gfx_move(x, y)`](#gfx_move) | — | Mueve el cursor de dibujo |  |
| [`gfx_draw(x, y)`](#gfx_draw) | — | Dibuja una línea del cursor al punto |  |
| [`gfx_line(x1, y1, x2, y2)`](#gfx_line) | — | Dibuja una línea entre dos puntos |  |
| [`gfx_pixel(x, y)`](#gfx_pixel) | — | Dibuja un píxel |  |
| [`gfx_pixel_read(x, y)`](#gfx_pixel_read) | Int | Lee el color de un píxel |  |
| [`gfx_rect(x1, y1, x2, y2)`](#gfx_rect) | — | Dibuja un rectángulo relleno |  |
| [`gfx_box(x1, y1, x2, y2)`](#gfx_box) | — | Dibuja el contorno de un rectángulo |  |
| [`gfx_ellipse(cx, cy, rx, ry)`](#gfx_ellipse) | — | Dibuja el contorno de una elipse |  |
| [`gfx_circle(cx, cy, r)`](#gfx_circle) | — | Dibuja el contorno de un círculo |  |
| [`gfx_ellipse_fill(cx, cy, rx, ry)`](#gfx_ellipse_fill) | — | Dibuja una elipse rellena |  |
| [`gfx_circle_fill(cx, cy, r)`](#gfx_circle_fill) | — | Dibuja un círculo relleno |  |
| [`gfx_flood(x, y, mode)`](#gfx_flood) | — | Rellena un área (como un cubo de pintura) |  |
| [`gfx_text(str)`](#gfx_text) | — | Escribe un texto en el cursor |  |
| [`gfx_text_at(x, y, str)`](#gfx_text_at) | — | Escribe un texto en una posición |  |
| [`gfx_text_len(str)`](#gfx_text_len) | Int | El ancho de un texto en píxeles |  |
| [`gfx_clear()`](#gfx_clear) | — | Borra con el color 0 |  |
| [`gfx_clear_color(color)`](#gfx_clear_color) | — | Borra con un color |  |
| [`gfx_scroll(dx, dy, x1, y1, x2, y2)`](#gfx_scroll) | — | Desplaza una zona |  |
| [`gfx_poly_begin(x, y)`](#gfx_poly_begin) | — | Empieza un polígono en un punto |  |
| [`gfx_poly_add(x, y)`](#gfx_poly_add) | — | Añade un vértice al polígono |  |
| [`gfx_poly_end()`](#gfx_poly_end) | — | Cierra y rellena el polígono |  |
| [`gfx_pens_draw(buffer, width, height, x, y, zoom)`](#gfx_pens_draw) | — | Dibuja una imagen de lápices (un byte por píxel, fila tras fila) en x, y, cada píxel de zoom x zoom: una imagen entera en una llamada (3.1: WriteChunkyPixels) |  |
| [`gfx_copy(sx, sy, w, h, dx, dy)`](#gfx_copy) | — | Copia una zona dentro de la ventana |  |

<a id="gfx_pen"></a>

### `gfx_pen(color)`

- `color`: el número de color de la paleta, de 0 al último de la pantalla (7 con profundidad 3, 31 con 5).

El color de las líneas, los puntos, los rellenos y el texto que vienen después. Sigue puesto hasta el siguiente
`gfx_pen`. Llamarlo con el color que ya tiene no cuesta nada, así que se puede poner en cada vuelta de un bucle.

Ver también: [`gfx_pen_bg`](#gfx_pen_bg), [`gfx_rgb`](#gfx_rgb), `color_pen`.

<a id="gfx_pen_bg"></a>

### `gfx_pen_bg(color)`

- `color`: un número de color de la paleta.

El color de fondo. Se usa en el texto con el modo JAM2 (`gfx_mode(1)`, el fondo de cada letra) y en los huecos de
las líneas con patrón (`gfx_pattern`) en ese modo.

Ver también: [`gfx_pen`](#gfx_pen), [`gfx_mode`](#gfx_mode).

<a id="gfx_pen_outline"></a>

### `gfx_pen_outline(color)`

- `color`: un número de color de la paleta.

El color del borde. Lo usa `gfx_flood` con el modo 0: rellena hasta encontrar ese color.

Ver también: [`gfx_flood`](#gfx_flood).

<a id="gfx_mode"></a>

### `gfx_mode(mode)`

- `mode`: 0 = JAM1, 1 = JAM2, 2 = COMPLEMENT, 4 = INVERSVID. Dash no tiene esas constantes: se pone el número.

Cómo se pinta. Con JAM1, lo normal, solo se pinta el lápiz: el texto no tapa lo que hay detrás. Con JAM2 el
texto lleva su fondo, del color de `gfx_pen_bg`. Con COMPLEMENT se invierten los bits de lo que ya hay: dibujar
dos veces lo mismo lo deja como estaba, útil para un cursor o un marco de selección. INVERSVID cambia de sitio
lápiz y fondo en el texto; se suma a los otros (`1 + 4`).

Ver también: [`gfx_pen`](#gfx_pen), [`gfx_pen_bg`](#gfx_pen_bg), [`gfx_pattern`](#gfx_pattern).

<a id="gfx_pattern"></a>

### `gfx_pattern(pattern)`

- `pattern`: 16 bits; cada bit a 1 es un píxel pintado. `0xFFFF` es la línea entera, `0xF0F0` discontinua y
  `0xAAAA` de puntos.

El patrón de las líneas que vienen después (`gfx_line`, `gfx_draw`, `gfx_box`). Se repite a lo largo de la línea.
Para volver a la línea entera: `gfx_pattern(0xFFFF)`.

Ver también: [`gfx_line`](#gfx_line), [`gfx_mode`](#gfx_mode).

<a id="gfx_rgb"></a>

### `gfx_rgb(index, r, g, b)`

- `index`: el color de la paleta que se cambia.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 15.

Lo que ya está dibujado con ese color cambia al momento: no se vuelve a dibujar nada. Cambia la paleta de la
pantalla propia, o la de la pantalla de la ventana si no hay. En el Workbench eso cambia los colores de todos los
programas. Sin pantalla ni ventana no hace nada.

Ver también: [`gfx_rgb8`](#gfx_rgb8), [`gfx_pen`](#gfx_pen), [`screen_open_custom`](#screen_open_custom).

<a id="gfx_rgb8"></a>

### `gfx_rgb8(index, r, g, b)`

- `index`: el color de la paleta que se cambia.
- `r`, `g`, `b`: rojo, verde y azul, de 0 a 255.

Como `gfx_rgb`, con 8 bits por componente. Exacto en AGA y en tarjetas gráficas. En OCS y ECS solo cuentan los
4 bits de arriba: 192 y 200 se ven igual.

Ver también: [`gfx_rgb`](#gfx_rgb).

<a id="gfx_move"></a>

### `gfx_move(x, y)`

- `x`, `y`: el punto, en píxeles.

Lleva el cursor de dibujo a ese punto sin pintar. Desde ahí empiezan `gfx_draw` y `gfx_text`.

Ver también: [`gfx_draw`](#gfx_draw), [`gfx_text`](#gfx_text).

<a id="gfx_draw"></a>

### `gfx_draw(x, y)`

- `x`, `y`: el final de la línea.

Una línea desde el cursor hasta ese punto, con el lápiz y el patrón. El cursor se queda en el final, así que
varios `gfx_draw` seguidos hacen una línea quebrada.

Ver también: [`gfx_move`](#gfx_move), [`gfx_line`](#gfx_line).

<a id="gfx_line"></a>

### `gfx_line(x1, y1, x2, y2)`

- `x1`, `y1`: el principio.
- `x2`, `y2`: el final.

Una línea entre dos puntos, con el lápiz y el patrón. Los dos puntos se pintan. Deja el cursor en el final.

Ver también: [`gfx_draw`](#gfx_draw), [`gfx_pattern`](#gfx_pattern), [`gfx_box`](#gfx_box).

<a id="gfx_pixel"></a>

### `gfx_pixel(x, y)`

- `x`, `y`: el punto.

Pinta un píxel con el lápiz. Para muchos píxeles es más rápido preparar la imagen en un búfer y dibujarla de una
vez con `gfx_pens_draw`.

Ver también: [`gfx_pixel_read`](#gfx_pixel_read), [`gfx_pens_draw`](#gfx_pens_draw).

<a id="gfx_pixel_read"></a>

### `gfx_pixel_read(x, y)` → `Int`

- `x`, `y`: el punto.

Devuelve el número de color de ese píxel, o -1 si está fuera del destino.

Ver también: [`gfx_pixel`](#gfx_pixel).

<a id="gfx_rect"></a>

### `gfx_rect(x1, y1, x2, y2)`

- `x1`, `y1`: la esquina de arriba a la izquierda.
- `x2`, `y2`: la de abajo a la derecha, incluida.

Un rectángulo relleno con el lápiz. `x2` tiene que ser mayor o igual que `x1`, y `y2` que `y1`: al revés, el
sistema no garantiza lo que pinta. `gfx_rect(0, 0, 9, 9)` pinta 10 x 10 píxeles.

Ver también: [`gfx_box`](#gfx_box), [`gfx_clear_color`](#gfx_clear_color).

<a id="gfx_box"></a>

### `gfx_box(x1, y1, x2, y2)`

- `x1`, `y1`, `x2`, `y2`: dos esquinas opuestas, incluidas.

El borde de un rectángulo, de un píxel de grueso, con el lápiz y el patrón. Deja el cursor en `x1`, `y1`.

Ver también: [`gfx_rect`](#gfx_rect), [`gfx_line`](#gfx_line).

<a id="gfx_ellipse"></a>

### `gfx_ellipse(cx, cy, rx, ry)`

- `cx`, `cy`: el centro.
- `rx`, `ry`: el radio horizontal y el vertical, en píxeles.

El borde de una elipse con el lápiz. En los modos de pantalla de píxeles alargados (640 x 256 en PAL) un círculo
se ve estirado: con `ry` la mitad de `rx` se ve redondo.

Ver también: [`gfx_ellipse_fill`](#gfx_ellipse_fill), [`gfx_circle`](#gfx_circle).

<a id="gfx_circle"></a>

### `gfx_circle(cx, cy, r)`

- `cx`, `cy`: el centro.
- `r`: el radio, en píxeles.

El borde de un círculo con el lápiz. Es `gfx_ellipse(cx, cy, r, r)`.

Ver también: [`gfx_circle_fill`](#gfx_circle_fill), [`gfx_ellipse`](#gfx_ellipse).

<a id="gfx_ellipse_fill"></a>

### `gfx_ellipse_fill(cx, cy, rx, ry)`

- `cx`, `cy`: el centro.
- `rx`, `ry`: los radios.

Una elipse rellena con el lápiz. Va en cualquier destino: si no tiene los búferes de relleno del sistema (una zona
de MUI), Dash le presta los suyos mientras dura.

Ver también: [`gfx_ellipse`](#gfx_ellipse), [`gfx_circle_fill`](#gfx_circle_fill), [`gfx_poly_begin`](#gfx_poly_begin).

<a id="gfx_circle_fill"></a>

### `gfx_circle_fill(cx, cy, r)`

- `cx`, `cy`: el centro.
- `r`: el radio.

Un círculo relleno con el lápiz. Es `gfx_ellipse_fill(cx, cy, r, r)`.

Ver también: [`gfx_circle`](#gfx_circle), [`gfx_ellipse_fill`](#gfx_ellipse_fill).

<a id="gfx_flood"></a>

### `gfx_flood(x, y, mode)`

- `x`, `y`: el punto donde empieza el relleno.
- `mode`: 1 = rellena los píxeles vecinos que tienen el mismo color que el de `x`, `y`; 0 = rellena hasta
  encontrar el color del borde (`gfx_pen_outline`).

Rellena con el lápiz, como el bote de pintura de un programa de dibujo. Si la figura tiene un hueco en el borde,
el relleno se sale por él.

Ver también: [`gfx_pen_outline`](#gfx_pen_outline), [`gfx_poly_begin`](#gfx_poly_begin).

<a id="gfx_text"></a>

### `gfx_text(str)`

- `str`: el texto.

Escribe el texto en el cursor con la fuente actual y el lápiz. El cursor marca la línea de base de las letras, no
su parte de arriba: con la fuente topaz de 8 puntos, el texto ocupa desde `y - 6` hasta `y + 1`. Después, el cursor
queda al final del texto. No parte líneas: un texto largo se corta en el borde.

Ver también: [`gfx_text_at`](#gfx_text_at), [`gfx_text_len`](#gfx_text_len), `font_use`, `font_baseline`.

<a id="gfx_text_at"></a>

### `gfx_text_at(x, y, str)`

- `x`, `y`: dónde empieza el texto; `y` es la línea de base.
- `str`: el texto.

Es `gfx_move(x, y)` y `gfx_text(str)`. Para escribir con la esquina de arriba en `y`, suma la línea de base de la
fuente: `gfx_text_at(x, y + font_baseline(), "Hola")`.

Ver también: [`gfx_text`](#gfx_text), [`gfx_text_len`](#gfx_text_len), `font_baseline`.

<a id="gfx_text_len"></a>

### `gfx_text_len(str)` → `Int`

- `str`: el texto.

Devuelve cuántos píxeles de ancho ocupa el texto con la fuente actual, sin dibujarlo. Sirve para centrar:
`gfx_text_at((ancho - gfx_text_len(t)) / 2, y, t)`.

Ver también: [`gfx_text`](#gfx_text), `font_height`.

<a id="gfx_clear"></a>

### `gfx_clear()`

Pinta todo el destino con el color 0. En una ventana es su interior.

Ver también: [`gfx_clear_color`](#gfx_clear_color).

<a id="gfx_clear_color"></a>

### `gfx_clear_color(color)`

- `color`: un número de color de la paleta.

Pinta todo el destino con ese color.

Ver también: [`gfx_clear`](#gfx_clear), [`gfx_rect`](#gfx_rect).

<a id="gfx_scroll"></a>

### `gfx_scroll(dx, dy, x1, y1, x2, y2)`

- `dx`, `dy`: cuántos píxeles se desplaza. Positivo mueve el contenido hacia la izquierda (`dx`) o hacia
  arriba (`dy`); negativo, al revés.
- `x1`, `y1`, `x2`, `y2`: el rectángulo que se desplaza, esquinas incluidas.

Mueve lo que hay dentro del rectángulo y pinta con el color de fondo (`gfx_pen_bg`) la franja que queda libre.
Para un texto que sube o un fondo que avanza.

Ver también: [`gfx_copy`](#gfx_copy), [`gfx_pen_bg`](#gfx_pen_bg).

<a id="gfx_poly_begin"></a>

### `gfx_poly_begin(x, y)`

- `x`, `y`: el primer vértice.

Empieza un polígono relleno. Después van los vértices con `gfx_poly_add` y se cierra con `gfx_poly_end`, que es
cuando se pinta. Hasta 100 vértices.

Ver también: [`gfx_poly_add`](#gfx_poly_add), [`gfx_poly_end`](#gfx_poly_end).

<a id="gfx_poly_add"></a>

### `gfx_poly_add(x, y)`

- `x`, `y`: el siguiente vértice.

Añade un vértice al polígono que empezó `gfx_poly_begin`. Sin un `gfx_poly_begin` antes no hace nada.

Ver también: [`gfx_poly_begin`](#gfx_poly_begin), [`gfx_poly_end`](#gfx_poly_end).

<a id="gfx_poly_end"></a>

### `gfx_poly_end()`

Cierra el polígono uniendo el último vértice con el primero y lo rellena con el lápiz.

Ver también: [`gfx_poly_begin`](#gfx_poly_begin), [`gfx_poly_add`](#gfx_poly_add).

<a id="gfx_pens_draw"></a>

### `gfx_pens_draw(buffer, width, height, x, y, zoom)`

- `buffer`: un búfer (`buffer_alloc`) con un byte por píxel, el número de color, fila tras fila.
- `width`, `height`: el tamaño de la imagen en píxeles. El búfer tiene que tener al menos `width * height` bytes.
- `x`, `y`: dónde va la esquina de arriba a la izquierda.
- `zoom`: cuántas veces se agranda cada píxel; 1 = tamaño real, 2 = cada píxel ocupa 2 x 2.

Dibuja la imagen entera en una llamada, mucho más rápido que un `gfx_pixel` por píxel. Va bien para imágenes que
el programa calcula (un fractal, un mapa) o que lee de un fichero.

Ver también: [`gfx_pixel`](#gfx_pixel), `buffer_alloc`, `gfx_rgb_draw`.

<a id="gfx_copy"></a>

### `gfx_copy(sx, sy, w, h, dx, dy)`

- `sx`, `sy`: la esquina de arriba a la izquierda de la zona que se copia.
- `w`, `h`: su ancho y alto.
- `dx`, `dy`: dónde va la copia.

Copia un rectángulo del destino a otro sitio del mismo destino. La zona de origen no se borra. Para copiar desde
un bitmap fuera de pantalla están los `bitmap_*`.

Ver también: [`gfx_scroll`](#gfx_scroll), `bitmap_draw_to`.

## Gráficos avanzados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sprite_load(id, filename)` | Bool | Un sprite de una imagen (ILBM...): fotogramas de 16 píxeles uno al lado del otro, los colores 0-3 los suyos (el 0, transparente); FALSE si no se puede |  |
| `sprite_load_attached(id, filename)` | Bool | Un sprite de 15 colores de una imagen: una pareja de sprites acoplados; los colores 1-15 de la imagen (0 transparente) son los 17-31 de la pantalla. Falso si no puede |  |
| `sprite_create(id, width, height)` | Bool | Crea un sprite vacío |  |
| `sprite_pos(id, x, y)` | — | Pone la posición de un sprite |  |
| `sprite_show(id)` | — | Hace visible un sprite |  |
| `sprite_hide(id)` | — | Oculta un sprite |  |
| `sprite_color(id, index, r, g, b)` | — | Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada; componentes de 0 a 15) |  |
| `sprite_load_colors(id, filename)` | Bool | Los colores 1-3 (1-15 en una pareja acoplada) de la paleta (CMAP) de una imagen como los colores del sprite, con 8 bits; falso si el fichero no la tiene |  |
| `bob_load_colors(filename, first)` | Int | Los colores de la paleta (CMAP) de una imagen en la paleta de la pantalla desde el color first: cuántos puso |  |
| `sprite_rgb8(id, index, r, g, b)` | — | Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada), con componentes de 8 bits (0-255; exacto en AGA, 4 bits en ECS) |  |
| `sprite_frame(id, frame)` | — | Enseña el fotograma frame (0 el primero) de un sprite de sprite_load o sprite_load_attached |  |
| `sprite_free(id)` | — | Libera la memoria de un sprite |  |
| `sprite_collision(id1, id2)` | Bool | Mira si chocan dos sprites |  |
| `sprite_set_row(id, row, plane0, plane1)` | — | Pone una fila de los datos de un sprite (2 planos de bits) |  |
| `soft_sprite_create(id, width, height, depth)` | Bool | Crea un sprite por software (vale en RTG) |  |
| `soft_sprite_free(id)` | — | Libera un sprite por software |  |
| `soft_sprite_pixel(id, x, y, color)` | — | Pone un píxel de un sprite por software |  |
| `soft_sprite_clear(id, color)` | — | Borra un sprite por software con un color |  |
| `soft_sprite_row(id, row, plane0, plane1)` | — | Pone una fila del sprite (en el formato de los sprites de hardware) |  |
| `soft_sprite_show(id)` | — | Enseña un sprite por software |  |
| `soft_sprite_hide(id)` | — | Oculta un sprite por software |  |
| `soft_sprite_pos(id, x, y)` | — | Pone la posición de un sprite por software |  |
| `soft_sprite_x(id)` | Int | La posición X de un sprite por software |  |
| `soft_sprite_y(id)` | Int | La posición Y de un sprite por software |  |
| `bob_load(id, filename)` | Bool | Carga un BOB de un fichero |  |
| `bob_create(id, width, height, depth)` | Bool | Crea un BOB vacío |  |
| `bob_pos(id, x, y)` | — | Pone la posición de un BOB |  |
| `bob_draw(id)` | — | Dibuja un BOB |  |
| `bob_erase(id)` | — | Borra un BOB (deja el fondo como estaba) |  |
| `bob_frame(id, frame)` | — | Pone el fotograma de la animación de un BOB |  |
| `bob_frame_width(id, width)` | — | La imagen del BOB es una tira de fotogramas de ese ancho en píxeles (bob_load lo toma del trozo FRJA de Forja; si no, supone fotogramas cuadrados) |  |
| `bob_width(id)` | Int | El ancho de un fotograma de un BOB (0 si no hay ese BOB) |  |
| `bob_height(id)` | Int | El alto de un BOB |  |
| `bob_frames(id)` | Int | Cuántos fotogramas tiene un BOB |  |
| `bob_paste(id, frame, x, y)` | — | Pinta un fotograma de un BOB en x, y con su máscara (el color 0, transparente), sin guardar lo que hay debajo: para juegos que pintan el fotograma entero cada vez (doble búfer) |  |
| `bob_free(id)` | — | Libera la memoria de un BOB |  |
| `tilemap_create(id, width, height, tile, layers)` | Bool | Un mapa de tiles nuevo en id (el que hubiera se va): ancho x alto celdas (de 1 a 1024 cada lado), tiles cuadrados de 8, 16 o 32 píxeles y de 1 a 8 capas de celdas vacías |  |
| `tilemap_load(id, filename)` | Bool | Carga en id un mapa de tiles (IFF FORM FMAP, el que guarda el editor de mapas de Forja); falso si no lo es |  |
| `tilemap_save(id, filename)` | Bool | Guarda un mapa de tiles en IFF FORM FMAP; falso si no se puede |  |
| `tilemap_free(id)` | — | Libera un mapa de tiles |  |
| `tilemap_width(id)` | Int | El ancho de un mapa de tiles en celdas (0 si no hay) |  |
| `tilemap_height(id)` | Int | El alto de un mapa de tiles en celdas |  |
| `tilemap_tile_size(id)` | Int | El lado de los tiles de un mapa en píxeles (8, 16 o 32) |  |
| `tilemap_layers(id)` | Int | Cuántas capas tiene un mapa de tiles |  |
| `tilemap_get(id, layer, x, y)` | Int | Una celda de una capa (0 la primera): el tile (1 el primer fotograma del tileset, 0 vacía) más 16384 si va en espejo de izquierda a derecha y 32768 si de arriba abajo; 0 fuera del mapa |  |
| `tilemap_set(id, layer, x, y, value)` | — | Pone una celda de una capa (como la da tilemap_get); nada fuera del mapa |  |
| `tilemap_tileset(id)` | String | El nombre del fichero del tileset del mapa, como va guardado en él ("" si no tiene) |  |
| `tilemap_set_tileset(id, filename)` | — | El nombre del fichero del tileset del mapa (un IFF del editor de sprites de Forja: un BOB con un fotograma por tile) |  |
| `tilemap_layer_name(id, layer)` | String | El nombre de una capa |  |
| `tilemap_layer_type(id, layer)` | Int | El tipo de una capa (0 tiles; el editor usa otros para choques y objetos) |  |
| `tilemap_layer_visible(id, layer)` | Bool | Si una capa se ve (para el editor) |  |
| `tilemap_layer_set(id, layer, name, type, visible)` | — | Nombre (hasta 31 caracteres), tipo y si se ve de una capa |  |
| `tilemap_layer_add(id)` | Int | Una capa vacía nueva al final: su número, o -1 (como mucho hay 8) |  |
| `tilemap_layer_remove(id, layer)` | Bool | Quita una capa (las de detrás bajan un puesto); falso si es la única |  |
| `tilemap_layer_move(id, from, to)` | Bool | Mueve una capa a otro puesto (las de en medio se corren uno) |  |
| `tilemap_resize(id, width, height)` | Bool | Tamaño nuevo en celdas: lo que cabe se queda, desde la esquina de arriba a la izquierda, y las celdas nuevas van vacías |  |
| `tilemap_draw(id, layer, bob, tx, ty, tw, th, x, y)` | — | Pinta tw x th celdas de una capa, desde la celda tx, ty, en x, y, con los fotogramas de un BOB (el tile n es el fotograma n - 1, en espejo si la celda lo dice; cada celda, del tamaño de un fotograma); las celdas vacías dejan ver lo de debajo. De una vez en la ventana |  |
| `tilemap_draw_masked(id, layer, bob, tx, ty, tw, th, x, y)` | — | Como tilemap_draw, pero el color 0 y las celdas vacías dejan ver lo de debajo (para las capas de delante) |  |
| `tilemap_objects(id)` | Int | Cuántos objetos tiene el mapa |  |
| `tilemap_object_add(id, x, y, kind)` | Int | Un objeto nuevo de esa clase (un texto: "jugador", "moneda"...) en x, y en píxeles del mapa: su número (0 el primero), o -1 (como mucho 256) |  |
| `tilemap_object_remove(id, object)` | Bool | Quita un objeto (los de detrás bajan un puesto) |  |
| `tilemap_object_x(id, object)` | Int | Dónde está un objeto: x en píxeles del mapa |  |
| `tilemap_object_y(id, object)` | Int | Dónde está un objeto: y en píxeles del mapa |  |
| `tilemap_object_move(id, object, x, y)` | — | Lleva un objeto a x, y |  |
| `tilemap_object_kind(id, object)` | String | La clase de un objeto |  |
| `tilemap_object_name(id, object)` | String | El nombre de un objeto |  |
| `tilemap_object_sprite(id, object)` | String | El fichero del sprite de un objeto ("" si no tiene) |  |
| `tilemap_object_set(id, object, kind, name, sprite)` | — | Clase, nombre (hasta 31 caracteres cada uno) y fichero del sprite de un objeto |  |
| `tilemap_object_find(id, kind, from)` | Int | El primer objeto de esa clase desde el número from; -1 si no hay (para encontrar al jugador, o recorrer los enemigos) |  |
| `bob_collision(id1, id2)` | Bool | Mira si chocan dos BOB |  |
| `copper_create(size)` | Bool | Crea una lista del copper |  |
| `copper_wait(y, x)` | — | Añade una instrucción WAIT del copper |  |
| `copper_move(reg, value)` | — | Añade una instrucción MOVE del copper |  |
| `copper_color(index, rgb)` | — | Añade un cambio de color del copper |  |
| `copper_end()` | — | Termina la lista del copper |  |
| `copper_install()` | — | Pone en marcha la lista del copper |  |
| `copper_free()` | — | Libera la lista del copper |  |
| `bitmap_create(id, width, height, depth)` | Bool | Crea un bitmap |  |
| `bitmap_load(id, filename)` | Bool | Carga un bitmap IFF |  |
| `bitmap_save(id, filename)` | Bool | Guarda un bitmap IFF |  |
| `bitmap_free(id)` | — | Libera un bitmap |  |
| `bitmap_blit(src_id, sx, sy, w, h, dx, dy)` | — | Copia de un bitmap a la pantalla |  |
| `bitmap_blit_mask(src_id, mask_id, sx, sy, w, h, dx, dy)` | — | Copia de un bitmap con máscara |  |
| `bitmap_draw_to(id)` | — | Dibuja en un bitmap desde ahora |  |
| `bitmap_draw_screen()` | — | Dibuja en la pantalla desde ahora |  |

## Entrada (teclado, ratón, joystick)

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

**Ejemplo** (`tests/test_doc_entrada.dash`: se compila y se prueba en el emulador con los tests):

```dash
# Entrada: el bucle de un juego que mueve un cuadrado con el joystick o las flechas, en una pantalla propia.

const ESC = 0x45
const ARRIBA = 0x4C
const ABAJO = 0x4D
const DERECHA = 0x4E
const IZQUIERDA = 0x4F

# v, sin salirse de a..b
func entre(v: Int, a: Int, b: Int) -> Int
    if v < a
        return a
    elif v > b
        return b
    end
    return v
end

Main
    if not screen_open_custom(320, 200, 3, "Entrada")
        Print "no se pudo abrir la pantalla"
        return
    end
    Print "la A escribe #{key_text(0x20)}"
    x = 150
    y = 90
    fin = time_ms() + 2000                 # para la prueba: acaba sola a los dos segundos
    while time_ms() < fin and not key_down(ESC) and not joy_fire(1)
        dx = joy_x(1)                      # -1, 0 o 1
        dy = joy_y(1)
        if key_down(IZQUIERDA)
            dx = -1
        elif key_down(DERECHA)
            dx = 1
        end
        if key_down(ARRIBA)
            dy = -1
        elif key_down(ABAJO)
            dy = 1
        end
        gfx_pen(0)
        gfx_rect(x, y, x + 19, y + 19)     # borra el cuadrado donde estaba
        x = entre(x + 2 * dx, 0, 300)
        y = entre(y + 2 * dy, 12, 180)
        gfx_pen(1)
        gfx_rect(x, y, x + 19, y + 19)
        time_delay(1)                      # una vuelta por fotograma, más o menos
    end
    Print "x = #{x}, y = #{y}"
    screen_close()
    Print "fin"
end
```

**Índice.** Las que tienen enlace están explicadas más abajo.

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| [`key_pressed()`](#key_pressed) | Bool | Mira si hay una tecla pulsada esperando |  |
| [`key_get()`](#key_get) | Int | El código de la tecla |  |
| [`key_wait()`](#key_wait) | Int | Espera una tecla y da su código |  |
| [`key_raw()`](#key_raw) | Int | El código de tecla en bruto (sin traducir) |  |
| [`key_down(code)`](#key_down) | Bool | Si una tecla está pulsada ahora, por su código (0x45 Esc, 0x40 espacio, 0x4C arriba, 0x4D abajo, 0x4E derecha, 0x4F izquierda): para juegos, se pregunta en cada fotograma; no necesita ventana |  |
| [`key_text(keycode)`](#key_text) | String | Pasa un código de tecla a texto |  |
| [`mouse_x()`](#mouse_x) | Int | La X del ratón dentro del interior de la ventana (0 sin ventana) |  |
| [`mouse_y()`](#mouse_y) | Int | La Y del ratón dentro del interior de la ventana (0 sin ventana) |  |
| [`mouse_button(btn)`](#mouse_button) | Bool | Mira un botón del ratón (0 izquierdo, 1 derecho) |  |
| [`event_window()`](#event_window) | Int | En un EventLoop: la ventana de la que vino el evento (window_create), 0 para la del propio bucle |  |
| [`window_check_close()`](#window_check_close) | Bool | Mira si se pulsó el botón de cerrar (sin esperar) |  |
| [`close_window()`](#close_window) | — | Cierra la ventana actual |  |
| [`screen_open_mode(mode, width, height, depth, title)`](#screen_open_mode) | Bool | Abre una pantalla con un modo exacto (el de dialog_screen_mode, o uno conocido: 0x21000 es PAL de baja resolución y 0x29000 la de alta), tamaño y profundidad; falso si el modo no existe o no admite esa profundidad |  |
| [`screen_clone_wb(name)`](#screen_clone_wb) | Bool | Abre una pantalla pública igual que la del Workbench (modo, tamaño, profundidad, lápices y fuente) con ese nombre, donde otros programas pueden abrir ventanas; falso si no se puede (o el nombre ya está). screen_close espera a que se cierren sus ventanas |  |
| [`screen_visitors()`](#screen_visitors) | Int | Cuántos usos de la pantalla pública del programa hay: ventanas y bloqueos (LockPubScreen; una ventana de MUI puede contar dos); 0 si ninguno |  |
| [`screen_make_default()`](#screen_make_default) | Bool | La pantalla pública del programa (screen_clone_wb) pasa a ser la pública por defecto: ahí se abren las ventanas que no dicen pantalla (los programas que lanza, las consolas); screen_close deja la de antes. Falso si no tiene pantalla pública |  |
| [`screen_open(depth, title)`](#screen_open) | Bool | Abre una pantalla con el modo del Workbench y la profundidad que se diga |  |
| [`screen_double_buffer()`](#screen_double_buffer) | Bool | Dos búferes para la pantalla propia del programa: se dibuja en el escondido y screen_flip lo enseña; falso sin pantalla propia (o si es pública) o antes de AmigaOS 3.0 |  |
| [`screen_flip()`](#screen_flip) | Bool | Enseña lo dibujado en el búfer escondido (screen_double_buffer) y pasa a dibujar en el otro; espera a la pantalla, un fotograma como mucho. Falso si ahora no pudo cambiarlo |  |
| [`screen_open_custom(width, height, depth, title)`](#screen_open_custom) | Bool | Abre una pantalla propia del tamaño y la profundidad que se digan |  |
| [`screen_close()`](#screen_close) | — | Cierra la pantalla |  |
| [`screen_width()`](#screen_width) | Int | El ancho de la pantalla en píxeles |  |
| [`screen_height()`](#screen_height) | Int | El alto de la pantalla en píxeles |  |
| [`check_lmb()`](#check_lmb) | Bool | Mira si está pulsado el botón izquierdo del ratón (hardware) |  |
| [`check_rmb()`](#check_rmb) | Bool | Mira si está pulsado el botón derecho del ratón (hardware) |  |
| [`check_mouse()`](#check_mouse) | Bool | Mira si está pulsado algún botón del ratón (hardware) |  |
| [`check_esc()`](#check_esc) | Bool | Mira si está pulsada la tecla Esc (hardware) |  |
| [`wait_click()`](#wait_click) | Int | Espera un clic del ratón (pulsar y soltar) |  |
| [`wait_key()`](#wait_key) | Int | Espera una tecla y da su código |  |
| [`joy_x(port)`](#joy_x) | Int | La dirección X del joystick (-1, 0, 1) |  |
| [`joy_y(port)`](#joy_y) | Int | La dirección Y del joystick (-1, 0, 1) |  |
| [`joy_button(port)`](#joy_button) | Bool | El estado del botón del joystick |  |
| [`joy_up(port)`](#joy_up) | Bool | Joystick hacia arriba |  |
| [`joy_down(port)`](#joy_down) | Bool | Joystick hacia abajo |  |
| [`joy_left(port)`](#joy_left) | Bool | Joystick a la izquierda |  |
| [`joy_right(port)`](#joy_right) | Bool | Joystick a la derecha |  |
| [`joy_fire(port)`](#joy_fire) | Bool | El botón de disparo del joystick |  |

<a id="key_pressed"></a>

### `key_pressed()` → `Bool`

Devuelve `true` si hay una tecla esperando en la ventana actual, sin sacarla: la recogen después `key_get` o
`key_wait`. Cuentan también las teclas soltadas. Sin ventana, `false`. Dentro de un `EventLoop` las teclas van a
`On Key`.

Ver también: [`key_get`](#key_get), [`key_wait`](#key_wait), [`key_down`](#key_down).

<a id="key_get"></a>

### `key_get()` → `Int`

Saca la siguiente tecla de la cola de la ventana actual y devuelve su código en bruto, o 0 si no hay ninguna. Al
soltar una tecla llega otra vez con 128 sumado (0x80): `if k < 128` se queda solo con las pulsaciones. La cola
guarda 16; si se llena, se pierden las más viejas.

Ver también: [`key_pressed`](#key_pressed), [`key_wait`](#key_wait), [`key_text`](#key_text).

<a id="key_wait"></a>

### `key_wait()` → `Int`

Espera a que se pulse una tecla en la ventana actual y devuelve su código en bruto. No gasta CPU mientras espera.
Las teclas soltadas no cuentan. Sin ventana devuelve 0 enseguida.

Ver también: [`key_get`](#key_get), [`wait_key`](#wait_key), [`key_text`](#key_text).

<a id="key_raw"></a>

### `key_raw()` → `Int`

Devuelve el código en bruto de la última tecla leída, con `key_get`, `key_wait` o un `On Key`. No mira el
teclado: para saber si una tecla está pulsada ahora, `key_down`.

Ver también: [`key_get`](#key_get), [`key_down`](#key_down).

<a id="key_down"></a>

### `key_down(code)` → `Bool`

- `code`: el código en bruto de la tecla, de 0 a 127.

Devuelve `true` si esa tecla está pulsada ahora mismo. Lee el estado del teclado del sistema: no necesita ventana
y no consume nada de la cola. Es lo que va en el bucle de un juego, una vez por fotograma. Ojo: ve las teclas
aunque el programa no sea el activo.

Ver también: [`joy_x`](#joy_x), [`key_get`](#key_get), [`check_esc`](#check_esc).

<a id="key_text"></a>

### `key_text(keycode)` → `String`

- `keycode`: un código en bruto de tecla.

Devuelve el texto que da esa tecla con el mapa de teclado puesto, sin Mayúsculas: `key_text(0x20)` es `"a"`.
`""` para las teclas sin letra, como las flechas o las de función.

Ver también: [`key_get`](#key_get), [`key_raw`](#key_raw).

<a id="mouse_x"></a>

### `mouse_x()` → `Int`

Devuelve la X del puntero contando desde la esquina de dentro de los bordes de la ventana actual, como los
`gfx_*`. Puede ser negativa o pasar del ancho si el puntero está fuera. Sin ventana, 0.

Ver también: [`mouse_y`](#mouse_y), [`mouse_button`](#mouse_button), `click_x`.

<a id="mouse_y"></a>

### `mouse_y()` → `Int`

Devuelve la Y del puntero dentro de la ventana actual, como `mouse_x`. Sin ventana, 0.

Ver también: [`mouse_x`](#mouse_x).

<a id="mouse_button"></a>

### `mouse_button(btn)` → `Bool`

- `btn`: 0 el izquierdo, 1 el derecho.

Devuelve `true` si ese botón está pulsado ahora. Lee el hardware del puerto del ratón: no necesita ventana y ve
los clics en cualquier sitio de la pantalla. En un programa con ventana, `On Click` es mejor.

Ver también: [`mouse_x`](#mouse_x), [`check_lmb`](#check_lmb), [`wait_click`](#wait_click).

<a id="event_window"></a>

### `event_window()` → `Int`

Dentro de un `EventLoop`, devuelve de qué ventana vino el evento: el número de `window_create`, o 0 si fue de la
ventana del propio bucle. Sirve para cerrar solo esa ventana en su `On Close`.

Ver también: [`window_create`](#window_create), [`gadget_id`](#gadget_id).

<a id="window_check_close"></a>

### `window_check_close()` → `Bool`

Devuelve `true` si se pulsó el botón de cerrar de la ventana actual desde la última vez que se miró, sin esperar.
Para un bucle propio, sin `EventLoop`: `while not window_check_close()`.

Ver también: [`close_window`](#close_window), [`key_get`](#key_get).

<a id="close_window"></a>

### `close_window()`

Cierra la ventana actual, sea declarada o de `window_create`. Después no queda ventana actual.

Ver también: [`window_close`](#window_close), [`window_check_close`](#window_check_close).

<a id="screen_open_mode"></a>

### `screen_open_mode(mode, width, height, depth, title)` → `Bool`

- `mode`: el modo exacto: el de `dialog_screen_mode` (`screen_mode_id`), o uno conocido: 0x21000 PAL baja
  resolución, 0x29000 PAL alta.
- `width`, `height`, `depth`: tamaño y profundidad.
- `title`: el título.

Abre la pantalla en ese modo. Devuelve `false` si el modo no existe en esta máquina, no admite esa profundidad o ya
hay una pantalla abierta.

Ver también: [`dialog_screen_mode`](#dialog_screen_mode), [`screen_open_custom`](#screen_open_custom).

<a id="screen_clone_wb"></a>

### `screen_clone_wb(name)` → `Bool`

- `name`: el nombre público de la pantalla.

Abre una pantalla pública igual que la del Workbench (modo, tamaño, profundidad, lápices y fuente) con ese nombre.
Otros programas pueden abrir ventanas en ella si se lo dicen. Devuelve `false` si el nombre ya existe o ya hay una
pantalla abierta. `screen_close` espera a que los demás cierren sus ventanas, un minuto como mucho; si siguen
abiertas, la deja.

Ver también: [`screen_visitors`](#screen_visitors), [`screen_make_default`](#screen_make_default), [`screen_close`](#screen_close).

<a id="screen_visitors"></a>

### `screen_visitors()` → `Int`

Devuelve cuántas ventanas y bloqueos de otros programas hay en la pantalla pública del programa
(`screen_clone_wb`); una ventana de MUI puede contar dos. 0 si no hay ninguno o no hay pantalla pública.

Ver también: [`screen_clone_wb`](#screen_clone_wb).

<a id="screen_make_default"></a>

### `screen_make_default()` → `Bool`

Hace de la pantalla pública del programa (`screen_clone_wb`) la pública por defecto: ahí se abren las ventanas que
no dicen pantalla, como las de los programas que lance o una consola. `screen_close` deja la de antes. Devuelve
`false` si no hay pantalla pública.

Ver también: [`screen_clone_wb`](#screen_clone_wb).

<a id="screen_open"></a>

### `screen_open(depth, title)` → `Bool`

- `depth`: la profundidad: 1 = 2 colores, 2 = 4, 3 = 8, 4 = 16, 5 = 32, 8 = 256 (AGA o tarjeta gráfica).
- `title`: el título de la barra de la pantalla.

Abre una pantalla con el modo y el tamaño del Workbench y la profundidad que se diga. Las ventanas que se abran
después van en ella y, sin ventana, los `gfx_*` dibujan en la pantalla. Devuelve `false` si no se pudo abrir. Solo
una pantalla a la vez: cierra la anterior antes de abrir otra.

Ver también: [`screen_open_custom`](#screen_open_custom), [`screen_open_mode`](#screen_open_mode), [`screen_close`](#screen_close).

<a id="screen_double_buffer"></a>

### `screen_double_buffer()` → `Bool`

Prepara dos imágenes para la pantalla propia: desde ahora los `gfx_*` dibujan en la escondida y `screen_flip` la
enseña. Así se ve cada fotograma entero, sin parpadeo. Se dibuja sobre la pantalla, no en ventanas: es para juegos
y demos a pantalla completa. Devuelve `false` sin pantalla propia, con una pública (`screen_clone_wb`) o antes de
AmigaOS 3.0. Llamarlo otra vez no hace nada.

Ver también: [`screen_flip`](#screen_flip), [`screen_open_custom`](#screen_open_custom).

<a id="screen_flip"></a>

### `screen_flip()` → `Bool`

Enseña lo dibujado en la imagen escondida y pasa a dibujar en la otra. Espera a la pantalla, un fotograma como
mucho, así que marca el ritmo del bucle: 50 vueltas por segundo en PAL. La imagen nueva tiene lo de hace dos
fotogramas: hay que borrar o repintar lo que se mueve. Devuelve `false` si ahora no pudo cambiarla.

Ver también: [`screen_double_buffer`](#screen_double_buffer).

<a id="screen_open_custom"></a>

### `screen_open_custom(width, height, depth, title)` → `Bool`

- `width`, `height`: el tamaño en píxeles: 320 x 256 es PAL de baja resolución, 640 x 256 la de alta.
- `depth`: la profundidad, como en `screen_open`.
- `title`: el título.

Abre una pantalla de ese tamaño; el sistema elige el modo que mejor le cuadra (sin HAM ni medio brillo). Devuelve
`false` si no se pudo abrir.

Ver también: [`screen_open`](#screen_open), [`screen_close`](#screen_close), [`gfx_rgb`](#gfx_rgb).

<a id="screen_close"></a>

### `screen_close()`

Cierra la pantalla propia. Antes hay que cerrar las ventanas que haya en ella. Sin pantalla propia no hace nada.

Ver también: [`screen_open`](#screen_open), [`window_close`](#window_close).

<a id="screen_width"></a>

### `screen_width()` → `Int`

Devuelve el ancho en píxeles de la pantalla propia o, si no hay, de la pantalla de la ventana actual. Sin ninguna, 640.

Ver también: [`screen_height`](#screen_height).

<a id="screen_height"></a>

### `screen_height()` → `Int`

Devuelve el alto en píxeles de la pantalla propia o de la de la ventana actual. Sin ninguna, 256.

Ver también: [`screen_width`](#screen_width).

<a id="check_lmb"></a>

### `check_lmb()` → `Bool`

Devuelve `true` si el botón izquierdo del ratón está pulsado ahora. Es `mouse_button(0)`.

Ver también: [`mouse_button`](#mouse_button), [`check_rmb`](#check_rmb).

<a id="check_rmb"></a>

### `check_rmb()` → `Bool`

Devuelve `true` si el botón derecho del ratón está pulsado ahora. Es `mouse_button(1)`.

Ver también: [`mouse_button`](#mouse_button), [`check_lmb`](#check_lmb).

<a id="check_mouse"></a>

### `check_mouse()` → `Bool`

Devuelve `true` si está pulsado alguno de los dos botones del ratón.

Ver también: [`mouse_button`](#mouse_button).

<a id="check_esc"></a>

### `check_esc()` → `Bool`

Devuelve `true` si lo último que mandó el teclado fue Esc pulsada. Si a la vez se pulsa otra tecla, deja de verla:
`key_down(0x45)` es más fiable.

Ver también: [`key_down`](#key_down).

<a id="wait_click"></a>

### `wait_click()` → `Int`

Espera a que se pulse y se suelte un botón del ratón, en cualquier sitio de la pantalla. Mira el ratón 50 veces
por segundo. Devuelve 1. En un programa con ventana, `On Click` dice además dónde fue.

Ver también: [`mouse_button`](#mouse_button), [`wait_key`](#wait_key).

<a id="wait_key"></a>

### `wait_key()` → `Int`

Espera a que se pulse una tecla en la ventana actual y devuelve su código en bruto. Los demás mensajes de la
ventana (el botón de cerrar, por ejemplo) se pierden mientras espera. Sin ventana, espera un segundo y devuelve 0.

Ver también: [`key_wait`](#key_wait), [`wait_click`](#wait_click).

<a id="joy_x"></a>

### `joy_x(port)` → `Int`

- `port`: 1 el puerto del joystick; 0 el del ratón.

Devuelve -1 si el joystick está a la izquierda, 1 a la derecha y 0 en el centro. Se mira en cada fotograma.

Ver también: [`joy_y`](#joy_y), [`joy_fire`](#joy_fire), [`key_down`](#key_down).

<a id="joy_y"></a>

### `joy_y(port)` → `Int`

- `port`: 1 el puerto del joystick; 0 el del ratón.

Devuelve -1 arriba, 1 abajo y 0 en el centro.

Ver también: [`joy_x`](#joy_x).

<a id="joy_button"></a>

### `joy_button(port)` → `Bool`

- `port`: 1 el puerto del joystick; 0 el del ratón.

Devuelve `true` si el botón de disparo está pulsado. En el puerto 0 es también el botón izquierdo del ratón.

Ver también: [`joy_fire`](#joy_fire).

<a id="joy_up"></a>

### `joy_up(port)` → `Bool`

- `port`: el puerto, 1 normalmente.

Devuelve `true` si el joystick está hacia arriba (también en diagonal).

Ver también: [`joy_y`](#joy_y).

<a id="joy_down"></a>

### `joy_down(port)` → `Bool`

- `port`: el puerto, 1 normalmente.

Devuelve `true` si el joystick está hacia abajo (también en diagonal).

Ver también: [`joy_y`](#joy_y).

<a id="joy_left"></a>

### `joy_left(port)` → `Bool`

- `port`: el puerto, 1 normalmente.

Devuelve `true` si el joystick está a la izquierda (también en diagonal).

Ver también: [`joy_x`](#joy_x).

<a id="joy_right"></a>

### `joy_right(port)` → `Bool`

- `port`: el puerto, 1 normalmente.

Devuelve `true` si el joystick está a la derecha (también en diagonal).

Ver también: [`joy_x`](#joy_x).

<a id="joy_fire"></a>

### `joy_fire(port)` → `Bool`

- `port`: el puerto, 1 normalmente.

Devuelve `true` si el botón de disparo está pulsado. Es `joy_button`.

Ver también: [`joy_button`](#joy_button).

## GadTools

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gt_init()` | Bool | Prepara GadTools (después de abrir la ventana) |  |
| `gt_cleanup()` | — | Libera lo de GadTools |  |
| `gt_attach()` | — | Pone los gadgets en la ventana (después de crearlos todos) |  |
| `gt_button(x, y, w, h, label)` | Int | Crea un botón; da su número |  |
| `gt_checkbox(x, y, w, h, label, checked)` | Int | Crea una casilla |  |
| `gt_string(x, y, w, h, label, initial, maxchars)` | Int | Crea un campo de texto |  |
| `gt_integer(x, y, w, h, label, initial)` | Int | Crea un campo de números |  |
| `gt_slider(x, y, w, h, label, min, max, level)` | Int | Crea un deslizador |  |
| `gt_palette(x, y, w, h, label, depth, color)` | Int | Crea un selector de color de la paleta |  |
| `gt_text(x, y, w, h, label, text)` | Int | Crea un texto fijo |  |
| `gt_get_value(gad_id)` | Int | El valor de un gadget (deslizador, paleta...) |  |
| `gt_set_value(gad_id, value)` | — | Cambia el valor de un gadget |  |
| `gt_get_string(gad_id)` | String | El texto de un campo de texto |  |
| `gt_event()` | Int | Mira si hay un evento de gadget: su número, -1 (ninguno) o -2 (cerrar) |  |
| `gt_wait_event()` | Int | Espera un evento de gadget: su número o -2 (cerrar) |  |
| `gt_cycle(x, y, w, h, label, options)` | Int | Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por \| (gt_get_value: la elegida) |  |
| `gt_enable(gad_id)` | — | Activa un gadget |  |
| `gt_disable(gad_id)` | — | Desactiva (en gris) un gadget |  |
| `gt_set_text(gad_id, text)` | — | Cambia el texto de un gt_text o un gt_string |  |

## Menús

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `menu_title(label)` | — | Añade el título de un menú |  |
| `menu_item(label, shortcut, id)` | — | Añade una opción de menú con su tecla y su número |  |
| `menu_sub(label, shortcut, id)` | — | Añade una opción de un submenú |  |
| `menu_separator()` | — | Añade una raya de separación al menú |  |
| `menu_attach()` | Bool | Pone los menús en la ventana (después de definirlos todos) |  |
| `menu_event()` | Int | Mira si hay un evento de menú: el número de la opción, o -1/-2 |  |
| `menu_id()` | Int | En el On Menu de un EventLoop: el número de la opción elegida |  |
| `menu_check_item(label, shortcut, id)` | — | Añade una opción de menú con una marca que cambia cada vez que se elige |  |
| `menu_checked(id)` | Int | 1 si está puesta la marca de esa opción |  |
| `menu_enable(id, enabled)` | — | Activa o desactiva (en gris) una opción de menú, después de menu_attach |  |

## Requesters ASL

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open_dialog(title, pattern)` | Bool | Enseña el diálogo de abrir fichero; true si se eligió uno |  |
| `file_save_dialog(title, pattern)` | Bool | Enseña el diálogo de guardar fichero; true si se eligió uno |  |
| `file_get_path()` | String | El cajón elegido en el último diálogo |  |
| `file_get_name()` | String | El nombre de fichero elegido en el último diálogo |  |
| `file_fullpath()` | String | La ruta entera (cajón + fichero) del último diálogo |  |

## ReAction

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `ra_window_create(title, width, height)` | Int | Crea una ventana ReAction con un layout; pasa a ser la actual. Su número (1-4), 0 si no se pudo |  |
| `ra_window_use(window)` | — | La ventana con la que trabajan las siguientes llamadas ra_* (el número que dio ra_window_create; hasta 4 ventanas) |  |
| `ra_event_window()` | Int | La ventana del último evento (su número de ra_window_create) |  |
| `ra_window_open()` | Int | Abre la ventana ReAction |  |
| `ra_window_close()` | — | Cierra la ventana ReAction actual y libera sus gadgets (otra abierta pasa a ser la actual) |  |
| `ra_window_sigmask()` | Int | La máscara de señal de la ventana, para Wait() |  |
| `ra_handle_events()` | Int | Atiende los eventos de la ventana (sin esperar): el número del gadget, o -1 si se cerró |  |
| `ra_wait_event()` | Int | Espera y atiende los eventos de la ventana: el número del gadget, o -1 si se cerró |  |
| `ra_add_button(id, label)` | Int | Añade un botón al layout |  |
| `ra_add_string(id, initial, maxchars)` | Int | Añade un campo de texto |  |
| `ra_add_checkbox(id, label, checked)` | Int | Añade una casilla |  |
| `ra_add_slider(id, min, max, initial)` | Int | Añade un deslizador horizontal |  |
| `ra_add_integer(id, initial, min, max)` | Int | Añade un campo de números |  |
| `ra_add_label(text)` | Int | Añade una etiqueta de texto |  |
| `ra_get_value(id)` | Int | El valor de un gadget (casilla 1/0, deslizador, número, paleta, selector, barra de desplazamiento) |  |
| `ra_get_string(id)` | String | El texto de un campo de texto |  |
| `ra_set_value(id, value)` | — | Cambia el valor de un gadget (los mismos que ra_get_value) |  |
| `ra_refresh_layout()` | — | Rehace el layout de la ventana después de añadir gadgets |  |
| `RA_EVENT_CLOSE()` | Int | El código del evento de cerrar la ventana (-1) |  |
| `RA_EVENT_NONE()` | Int | El código de ningún evento (-3) |  |
| `ra_get_rastport()` | Int (dirección) | El RastPort para dibujar a mano (también pone _dash_rp) |  |
| `ra_get_inner_left()` | Int | El borde izquierdo interior de la ventana |  |
| `ra_get_inner_top()` | Int | El borde de arriba interior de la ventana |  |
| `ra_get_inner_width()` | Int | El ancho interior de la ventana |  |
| `ra_get_inner_height()` | Int | El alto interior de la ventana |  |
| `ra_add_palette(id, depth, initial_color)` | Int | Añade un gadget de paleta de colores |  |
| `ra_get_palette_color(id)` | Int | El color elegido en la paleta |  |
| `ra_set_palette_color(id, color)` | — | Elige un color de la paleta |  |
| `ra_add_chooser(id)` | Int | Añade una lista desplegable (chooser) |  |
| `ra_chooser_add_item(id, label)` | Int | Añade una opción a la lista desplegable |  |
| `ra_get_chooser_selected(id)` | Int | La opción elegida de la lista desplegable |  |
| `ra_set_chooser_selected(id, index)` | — | Elige una opción de la lista desplegable |  |
| `ra_add_scroller(id, min, max, visible, initial)` | Int | Añade una barra de desplazamiento horizontal |  |
| `ra_add_scroller_vert(id, min, max, visible, initial)` | Int | Añade una barra de desplazamiento vertical |  |
| `ra_get_scroller(id)` | Int | La posición de una barra de desplazamiento |  |
| `ra_set_scroller(id, pos)` | — | Cambia la posición de una barra de desplazamiento |  |
| `ra_enable_gadget(id)` | — | Activa un gadget |  |
| `ra_disable_gadget(id)` | — | Desactiva un gadget |  |
| `ra_set_string(id, text)` | — | Cambia el texto de un campo de texto |  |
| `ra_set_text(id, text)` | — | Cambia el texto de un botón o una etiqueta |  |
| `ra_layout_hgroup_begin()` | Int | Empieza un grupo horizontal del layout |  |
| `ra_layout_vgroup_begin()` | Int | Empieza un grupo vertical del layout |  |
| `ra_layout_group_end()` | Int | Acaba un grupo del layout |  |
| `ra_add_space()` | — | Añade un separador horizontal |  |
| `ra_add_vspace()` | — | Añade un separador vertical |  |
| `ra_layout_hgroup_weighted(weight)` | Int | Empieza un grupo horizontal con un peso (lo que ocupa respecto a los demás) |  |
| `ra_layout_vgroup_weighted(weight)` | Int | Empieza un grupo vertical con un peso |  |
| `ra_layout_group_end_weighted()` | Int | Acaba un grupo con peso |  |
| `ra_add_drawing_area(id, min_width, min_height)` | Int | Añade un gadget Space para dibujar a mano |  |
| `ra_get_drawing_bounds(id)` | Int | Mira dónde está el gadget Space (después de abrir la ventana) |  |
| `ra_drawing_left()` | Int | La izquierda de la zona de dibujo |  |
| `ra_drawing_top()` | Int | La parte de arriba de la zona de dibujo |  |
| `ra_drawing_width()` | Int | El ancho de la zona de dibujo |  |
| `ra_drawing_height()` | Int | El alto de la zona de dibujo |  |
| `ra_calc_drawing_area(toolbar_h, timeline_h, left_w, right_w)` | Int | Calcula la zona de dibujo con las medidas de la ventana (si no hay otra forma) |  |
| `ra_refresh_canvas(id)` | — | Pide que se redibuje el lienzo del gadget Space (llama a su función de dibujo) |  |
| `ra_canvas_left()` | Int | La izquierda del lienzo, desde su función de dibujo |  |
| `ra_canvas_top()` | Int | La parte de arriba del lienzo, desde su función de dibujo |  |
| `ra_canvas_width()` | Int | El ancho del lienzo, desde su función de dibujo |  |
| `ra_canvas_height()` | Int | El alto del lienzo, desde su función de dibujo |  |
| `ra_init_canvas_render()` | — | Pone render_canvas() como la función de dibujo del lienzo |  |
| `ra_canvas_enable()` | — | Activa el dibujo del lienzo (cuando todo esté preparado) |  |
| `ra_gadget_exists(id)` | Int | Mira si existe un gadget |  |
| `ra_window_width()` | Int | El ancho de la ventana |  |
| `ra_window_height()` | Int | El alto de la ventana |  |
| `ra_window_is_open()` | Int | Mira si la ventana está abierta |  |
| `ra_add_listbrowser(id)` | Int | Añade una lista de líneas de texto (valor: la línea elegida, -1 ninguna) |  |
| `ra_listbrowser_add(id, text)` | Int | Añade una línea al final de una lista |  |
| `ra_listbrowser_clear(id)` | — | Quita todas las líneas de una lista |  |
| `ra_listbrowser_count(id)` | Int | Cuántas líneas tiene una lista |  |
| `ra_add_radio(id, options)` | Int | Añade botones de radio, opciones separadas por \| (valor: la opción) |  |
| `ra_add_clicktab(id, titles)` | Int | Añade pestañas, títulos separados por \| (valor: la pestaña, desde 0) |  |
| `ra_add_fuelgauge(id, max)` | Int | Añade una barra de progreso de 0 a max (valor: el nivel) |  |
| `ra_menu_title(label)` | — | Añade un menú a la ventana ReAction (antes de ra_window_open) |  |
| `ra_menu_item(label, key, id)` | — | Añade una opción de menú: key = la letra de Amiga+tecla ("" ninguna); eventos: RA_EVENT_MENU() y ra_menu_id() |  |
| `ra_menu_separator()` | — | Añade una raya de separación al menú |  |
| `ra_menu_id()` | Int | El número de la opción de menú del último RA_EVENT_MENU() |  |
| `RA_EVENT_MENU()` | Int | Evento: se eligió una opción de menú (ra_menu_id) |  |
| `ra_add_getfile(id, title)` | Int | Añade un botón que abre un diálogo de ficheros; ra_get_string(id) da el fichero elegido |  |

## Sistema y memoria

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `debug_break()` | — | Para en el depurador del emulador UAE (en un Amiga de verdad no hace nada; tools/emu_run.py --debug) |  |
| `mem_chip_free()` | Int | La memoria chip libre |  |
| `mem_fast_free()` | Int | La memoria fast libre |  |
| `mem_total()` | Int | La memoria libre, chip y fast (la que queda, no el tamaño de la RAM) |  |
| `mem_chip_total()` | Int | El tamaño de la memoria chip en bytes (libre y en uso: AvailMem con MEMF_TOTAL) |  |
| `mem_fast_total()` | Int | El tamaño de la memoria fast en bytes (libre y en uso: AvailMem con MEMF_TOTAL) |  |
| `peek_byte(addr)` | Int | Lee un byte de una dirección de memoria |  |
| `peek_word(addr)` | Int | Lee un word (16 bits) de una dirección de memoria |  |
| `peek_long(addr)` | Int | Lee un long (32 bits) de una dirección de memoria |  |
| `poke_byte(addr, value)` | — | Escribe un byte en una dirección de memoria |  |
| `poke_word(addr, value)` | — | Escribe un word (16 bits) en una dirección de memoria |  |
| `amiga_alloc(size)` | Int | size bytes para estructuras de AmigaOS (@amiga struct), a cero: AllocMem(MEMF_PUBLIC \| MEMF_CLEAR) en el Amiga, memoria de la caja Amiga (por debajo de 4 GB) en DashOS; 0 si no hay memoria |  |
| `amiga_free(addr, size)` | — | Devuelve lo que dio amiga_alloc (con el mismo tamaño) |  |
| `poke_long(addr, value)` | — | Escribe un long (32 bits) en una dirección de memoria |  |
| `time_delay(ticks)` | — | Espera tics (50 por segundo) |  |
| `time_delay_ms(ms)` | — | Espera milisegundos (de 20 en 20: lo que dura un tic) |  |
| `random()` | Int | Un número al azar |  |
| `random_range(min, max)` | Int | Un número al azar entre min y max (los dos incluidos) |  |
| `random_seed(seed)` | — | Pone la semilla de los números al azar |  |
| `wait_vblank()` | — | Espera al retrazado vertical |  |
| `wait_blit()` | — | Espera a que acabe el blitter |  |
| `arena_new(size)` | Int | Crea una arena (memoria que se reparte por orden) de ese tamaño en bytes |  |
| `arena_alloc(arena, size)` | Int | Pide memoria de una arena (muy rápido) |  |
| `arena_reset(arena)` | — | Vacía una arena (reusa la memoria sin liberarla) |  |
| `arena_free(arena)` | — | Libera una arena y toda su memoria |  |
| `arena_used(arena)` | Int | Los bytes usados de una arena |  |
| `arena_available(arena)` | Int | Los bytes libres de una arena |  |
| `refcount(obj)` | Int | El contador de referencias de un objeto |  |
| `retain(obj)` | — | Suma una referencia a mano |  |
| `release(obj)` | — | Quita una referencia a mano (libera el objeto si llega a 0) |  |
| `mem_trim()` | Int | Devuelve al sistema los charcos de bloques pequeños (hasta 128 bytes) que están del todo libres; los bytes devueltos |  |
| `mem_puddle(bytes)` | Bool | El tamaño de los charcos del pool de memoria (de 1 KB a 1 MB; 4 KB si no); solo antes de pedir memoria |  |

## Ficheros (DOS)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open(filename, mode)` | Int | Abre un fichero (modo: 1005 leer, 1006 nuevo, 1004 leer y escribir; 0 si no se puede) |  |
| `file_close(handle)` | — | Cierra un fichero |  |
| `file_read_byte(handle)` | Int | Lee un byte |  |
| `file_read_line(handle, buffer, maxlen)` | String | Lee una línea en un búfer |  |
| `file_read(handle, buffer, length)` | Int | Lee bytes en un búfer |  |
| `file_eof(handle)` | Bool | True al final del fichero (mira el byte siguiente sin gastarlo) |  |
| `file_write_byte(handle, byte)` | Int | Escribe un byte |  |
| `file_write_line(handle, str)` | Int | Escribe un texto y un salto de línea (0 bien, -1 error) |  |
| `file_write(handle, buffer, length)` | Int | Escribe bytes de un búfer |  |
| `file_print(handle, str)` | — | Escribe un texto en un fichero |  |
| `file_seek(handle, position, mode)` | Int | Va a un sitio del fichero (modo: OFFSET_BEGINNING, OFFSET_CURRENT, OFFSET_END) |  |
| `file_pos(handle)` | Int | El sitio actual en el fichero |  |
| `file_size(filename)` | Int | El tamaño de un fichero |  |
| `file_exists(filename)` | Bool | Mira si existe un fichero |  |
| `file_delete(filename)` | Bool | Borra un fichero |  |
| `file_rename(oldname, newname)` | Bool | Cambia el nombre de un fichero |  |
| `file_copy(src, dest)` | Bool | Copia un fichero |  |
| `dir_create(path)` | Bool | Crea un cajón |  |
| `dir_change(path)` | Bool | Cambia el cajón actual |  |
| `dir_current()` | String | El nombre entero del cajón actual ("Ram Disk:"...) |  |
| `dir_read(path)` | Int | Lee lo que hay en un cajón, por orden de nombre (sin mirar mayúsculas): cuántas entradas, -1 si no es un cajón que se pueda leer. dir_entry_name y las demás las leen, hasta el siguiente dir_read |  |
| `dir_entry_name(i)` | String | El nombre de la entrada i (desde 0) del último dir_read; "" si no la hay |  |
| `dir_entry_size(i)` | Int | El tamaño en bytes de la entrada i del último dir_read (0 si es un cajón) |  |
| `dir_entry_is_dir(i)` | Bool | Verdadero si la entrada i del último dir_read es un cajón |  |
| `dir_entry_date(i)` | Int | La fecha de la entrada i del último dir_read, como time_unix: segundos desde el 1 de enero de 1970 |  |
| `console_read(buffer, maxlen)` | Int | Lee de la consola |  |
| `console_write(str)` | — | Escribe en la consola (sin búfer) |  |
| `file_load(filename, buffer, maxsize)` | Int | Carga un fichero entero en un búfer: los bytes leídos, o -1 |  |
| `file_save(filename, buffer, size)` | Int | Guarda un búfer en un fichero: los bytes escritos |  |

## Buffers

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `buffer_alloc(size)` | Int (dirección) | Pide un búfer de memoria |  |
| `buffer_free(buffer)` | — | Libera un búfer |  |
| `buffer_get_byte(buffer, offset)` | Int | El byte en una posición |  |
| `buffer_set_byte(buffer, offset, value)` | — | Pone el byte de una posición |  |
| `buffer_get_word(buffer, offset)` | Int | El word de 16 bits en una posición (big-endian) |  |
| `buffer_set_word(buffer, offset, value)` | — | Pone el word de 16 bits de una posición (big-endian) |  |
| `buffer_get_long(buffer, offset)` | Int | El long de 32 bits en una posición (big-endian) |  |
| `buffer_set_long(buffer, offset, value)` | — | Pone el long de 32 bits de una posición (big-endian) |  |
| `buffer_copy(dest, dest_offset, src, src_offset, length)` | — | Copia bytes de un búfer a otro |  |
| `buffer_fill(buffer, offset, length, value)` | — | Llena una zona de un búfer con un byte |  |

## Texto

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_code(s, i)` | Int | El código (0-255) del carácter en la posición i; 0 fuera del texto |  |
| `str_char(code)` | String | Un texto de un carácter con ese código |  |
| `str_find(s, sub)` | Int | La posición del primer sub en s; -1 si no está |  |
| `str_find_from(s, sub, start)` | Int | La posición del primer sub en s desde start; -1 si no está |  |
| `str_starts(s, prefix)` | Bool | ¿Empieza s por prefix? |  |
| `str_ends(s, suffix)` | Bool | ¿Acaba s en suffix? |  |
| `str_lower(s)` | String | Una copia en minúsculas (Latin-1: también las letras con acento) |  |
| `str_upper(s)` | String | Una copia en mayúsculas (Latin-1: también las letras con acento) |  |
| `str_trim(s)` | String | Una copia sin espacios, tabuladores ni saltos de línea a los lados |  |
| `str_to_int(s, base)` | Int | El número escrito en s en esa base (2-36); Int(s) es en base 10 |  |
| `str_from_int(n, base)` | String | n escrito en esa base (2-36, letras en minúscula) |  |
| `str_replace(s, from, to)` | String | Una copia con cada from cambiado por to |  |
| `str_contains(s, sub)` | Bool | Si sub está en s ("" está en todos) |  |
| `str_split(s, sep)` | [Int] | Los trozos de s entre cada sep, en una [String] nueva; con sep "" o si no está, [s] |  |
| `file_read_text(filename)` | String | El fichero entero como texto (los bytes 0 pasan a espacios); nil si no se puede leer |  |
| `file_write_text(filename, text)` | Bool | Escribe el texto como el fichero entero; true si se escribió todo |  |
| `str_from_buffer(buffer, offset, length)` | String | Un texto con length bytes de un búfer desde offset (los bytes 0 pasan a espacios) |  |
| `str_to_buffer(s, buffer, offset)` | Int | Copia los bytes de s a buffer + offset; da cuántos |  |

## Red (TCP)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `net_connect(host, port, timeout_ms)` | Int | Una conexión TCP a host:port (nombre o dirección): el socket, o -1 (ver net_error) |  |
| `net_connect_start(host, port, timeout_ms)` | Int | Empieza una conexión TCP sin esperar (el nombre se busca en otro proceso): el socket, o -1 (ver net_error) |  |
| `net_connect_poll(sock)` | Int | Sigue con net_connect_start sin esperar: 1 conectada, 0 aún no, -1 falló (el socket se cierra; ver net_error) |  |
| `net_connect_stage(sock)` | Int | Qué está haciendo net_connect_start: 0 buscando el nombre, 1 conectando, 2 hecho |  |
| `net_send(sock, text)` | Int | Envía el texto entero; los bytes enviados o -1 |  |
| `net_send_buffer(sock, buffer, length)` | Int | Envía length bytes de un búfer; los bytes enviados o -1 |  |
| `net_recv(sock, max, timeout_ms)` | String | Hasta max bytes como texto: "" si no llegó nada en timeout_ms (-1: esperar), nil al cerrarse |  |
| `net_recv_buffer(sock, buffer, max, timeout_ms)` | Int | Hasta max bytes en un búfer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse |  |
| `net_wait(sock, timeout_ms)` | Int | Espera a que haya algo que leer: 1 sí, 0 se acabó el tiempo, -1 error |  |
| `net_close(sock)` | — | Cierra la conexión |  |
| `net_resolve(host)` | String | La dirección IPv4 de un nombre ("a.b.c.d"); nil si no se conoce |  |
| `net_error()` | String | Qué falló en la última llamada net_ |  |
| `net_listen(port)` | Int | Un servidor TCP en un puerto (0: uno libre cualquiera, net_port dice cuál): el socket que escucha, o -1 (ver net_error) |  |
| `net_accept(sock, timeout_ms)` | Int | La siguiente conexión a un servidor de net_listen, esperando como mucho timeout_ms (-1: esperar, 0: solo mirar): su socket (net_send, net_recv...), o -1 si no llegó ninguna |  |
| `net_peer(sock)` | String | La dirección ("a.b.c.d") del otro lado de una conexión TCP; nil si no hay |  |
| `net_port(sock)` | Int | El puerto local de un socket (el que tocó con net_listen(0) o net_udp_open(0)); -1 si no hay |  |
| `net_udp_open(port)` | Int | Un socket UDP en un puerto (0: uno libre cualquiera), con difusión: el socket, o -1 (se cierra con net_close) |  |
| `net_udp_send(sock, host, port, text)` | Int | Envía el texto como un datagrama a host:port ("255.255.255.255": toda la red local); los bytes enviados o -1 |  |
| `net_udp_send_buffer(sock, host, port, buffer, length)` | Int | Envía length bytes de un búfer como un datagrama a host:port; los bytes enviados o -1 |  |
| `net_udp_recv(sock, max, timeout_ms)` | String | El siguiente datagrama como texto (hasta max bytes): "" si no llegó ninguno en timeout_ms, nil si hubo un error; quién lo envió: net_udp_from, net_udp_from_port |  |
| `net_udp_recv_buffer(sock, buffer, max, timeout_ms)` | Int | El siguiente datagrama en un búfer: su largo, 0 si no llegó a tiempo, -1 si hubo un error |  |
| `net_udp_from()` | String | La dirección ("a.b.c.d") de quien envió el último datagrama recibido |  |
| `net_udp_from_port()` | Int | El puerto de quien envió el último datagrama recibido (para contestarle) |  |
| `net_stack_running()` | Bool | True si hay una pila TCP/IP en marcha (su bsdsocket.library está en memoria), sin cargar nada para saberlo. La de Roadshow sigue en memoria tras NetShutdown: esa se abre y se cierra |  |
| `net_release()` | — | Suelta la red ya: se cierra bsdsocket.library, con los sockets, las conexiones TLS y las búsquedas de nombres abiertos; la siguiente llamada net_ la abre otra vez (al acabar el programa también) |  |
| `net_signal()` | Int | La máscara de señal que dan los sockets con cada evento (conectado, datos, cerrado...), 0 si la pila TCP/IP no puede: llamarla antes de cada espera, mui_wait_event_signals(net_signal()) |  |

## TLS (AmiSSL)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `tls_connect(sock, host)` | Int | TLS sobre un socket conectado, comprobando el certificado de host; -1 si no (net_error) |  |
| `tls_connect_start(sock, host, timeout_ms)` | Int | TLS sobre un socket conectado sin esperar al saludo: la conexión, o -1 (ver net_error) |  |
| `tls_connect_poll(tls)` | Int | Sigue con tls_connect_start: 1 hecho (certificado comprobado), 0 aún no, -1 falló (la conexión TLS se libera; ver net_error) |  |
| `tls_send(tls, text)` | Int | Envía el texto entero; los bytes enviados o -1 |  |
| `tls_send_buffer(tls, buffer, length)` | Int | Envía length bytes de un búfer; los bytes enviados o -1 |  |
| `tls_recv(tls, max, timeout_ms)` | String | Como net_recv: "" si no llegó nada a tiempo, nil al cerrarse |  |
| `tls_recv_buffer(tls, buffer, max, timeout_ms)` | Int | Como net_recv_buffer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse |  |
| `tls_close(tls)` | — | Acaba la TLS de la conexión (después, net_close del socket) |  |
| `tls_resumed(tls)` | Bool | True si la conexión retomó una sesión anterior con el mismo servidor (sin intercambiar claves) |  |

## Fuentes y colores

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `font_open(name, size)` | Int | Abre una fuente ("helvetica.font", tamaño en píxeles, 2 como poco): la fuente, o 0 si no hay |  |
| `font_use(font)` | — | Escribe con esta fuente |  |
| `font_close(font)` | — | Cierra una fuente (las abiertas se cierran al acabar) |  |
| `font_style(style)` | — | El estilo del texto: 0 normal, +1 subrayado, +2 negrita, +4 cursiva |  |
| `font_height()` | Int | El alto de la fuente actual |  |
| `font_baseline()` | Int | Los píxeles de arriba del texto a su línea base |  |
| `font_text_width(text)` | Int | El ancho de un texto en píxeles con la fuente y el estilo actuales |  |
| `font_size(font)` | Int | El tamaño que dio el sistema para esta fuente (el más cercano que tiene) |  |
| `color_pen(r, g, b)` | Int | El color de la pantalla en la que se dibuja más parecido a r, g, b (0-255); para gfx_pen |  |
| `color_pen_free(pen)` | — | Un color_pen de ese lápiz ya no hace falta; cuando no queda ninguno, vuelve a la pantalla (ReleasePen) |  |

## Transparencia y degradados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_blend_rect(x1, y1, x2, y2, rgb, alpha)` | — | Mezcla el color 0xRRGGBB con lo dibujado, alfa 0-255 (pantallas de paleta: un tramado 4x4 del color más cercano) |  |
| `gfx_gradient_rect(x1, y1, x2, y2, rgb1, alpha1, rgb2, alpha2, vertical)` | — | Un degradado de (rgb1, alpha1) a (rgb2, alpha2), de arriba abajo si vertical, si no de izquierda a derecha, mezclado con lo dibujado |  |
| `gfx_pixel_rgb(x, y)` | Int | El color de un píxel como 0xRRGGBB (en una pantalla de paleta, el de su color) |  |

## Imágenes RGB desde un buffer (vídeo)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_rgb_draw(buffer, width, height, x, y)` | — | Dibuja un búfer RGB24 (3 bytes por píxel, filas una tras otra) en x, y (RTG: con un WritePixelArray; pantallas de paleta: los colores más cercanos) |  |
| `gfx_rgb_draw_scaled(buffer, width, height, x, y, dest_width, dest_height)` | — | Dibuja un búfer RGB24 en x, y a dest_width x dest_height (el píxel más cercano, fila a fila) |  |

## Tareas, reloj, traducciones y escritorio

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `task_start(func, arg)` | Int | Ejecuta una función f(arg: Int) -> Int en otro proceso: una de Dash que solo use Int, Bool, Float y builtins que no den textos ni listas (el compilador lo comprueba), o una de C (@extern, @native: malloc/free sí, textos y listas de Dash no); 128 KB de pila, la prioridad del programa: la tarea, o 0 |  |
| `task_start_with(func, arg, stack, priority)` | Int | task_start con su pila en bytes (0: 128 KB) y su prioridad respecto a la del programa (-1: solo corre cuando el programa espera) |  |
| `task_done(task)` | Bool | True cuando la función ha acabado (no espera) |  |
| `desktop_canvas(x, y, width, height)` | Int (dirección) | Una zona del escritorio del Workbench (debajo de la barra de título de la pantalla), detrás de los iconos y sin clics, en modo fondo o no, planar o RTG; x o y negativas: desde el borde derecho o el de abajo (-1 lo toca). 0 si no se puede |  |
| `desktop_canvas_on_draw(canvas, func)` | — | La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (desde 0, 0), sobre el fondo de escritorio que hay debajo |  |
| `desktop_canvas_update(canvas)` | — | Dibuja otra vez la zona ya y enseña lo que cambió, sin tocar los iconos |  |
| `desktop_canvas_update_area(canvas, x, y, width, height)` | — | desktop_canvas_update solo en esa parte de la zona: el dibujo se recorta a ella y solo se compara ella (lo demás se queda como estaba; donde el escritorio se repintó entretanto, también se dibuja) |  |
| `desktop_canvas_veil(canvas, rgb, alpha)` | — | El fondo de debajo del dibujo mezclado con rgb (0xRRGGBB) con alpha (0-255; 0: ninguno), una vez y otra solo donde el escritorio lo repinta: como un gfx_blend_rect sobre toda la zona en cada dibujo, sin su coste. Quita los velos de desktop_canvas_veil_rect. Se ve desde el siguiente desktop_canvas_update |  |
| `desktop_canvas_veil_rect(canvas, x, y, width, height, rgb, alpha)` | Bool | Un velo más, solo en ese rectángulo, mezclado una vez sobre el de desktop_canvas_veil (que los quita: llamarlo antes): una caja que siempre está. Hasta 16; false si no caben más |  |
| `desktop_canvas_drawing(x, y, width, height)` | Bool | Dentro de la función de dibujo: true si ese rectángulo llega a la parte que se dibuja (toda la zona, o la de desktop_canvas_update_area con lo que repintó el escritorio), para saltarse lo que no se vería. Fuera de ella, siempre true |  |
| `desktop_canvas_free(canvas)` | — | Vuelve a poner el fondo de escritorio en la zona (al acabar el programa también) |  |
| `break_check()` | Bool | True si llegó un Ctrl-C ("Break" en el Shell, u otra copia: single_instance); se borra |  |
| `single_instance(name)` | Bool | Una sola copia a la vez: false si corre otra copia del programa (un puerto público con ese nombre), que recibe un Ctrl-C; si no, true (el puerto es del programa hasta que acaba) |  |
| `tooltype(name, default)` | String | Un tooltype del programa: desde el Shell, el argumento NOMBRE=valor (también NOMBRE="a b"); si no (o desde el Workbench), el tooltype de su icono; default si no está en ninguno |  |
| `cx_broker(name, title, description, priority)` | Bool | El programa en Exchange como commodity, con Mostrar y Ocultar, activado (nombre de hasta 23 letras, título y descripción de hasta 39); false sin commodities.library o si ya hay uno con ese nombre. Se quita al acabar el programa |  |
| `cx_hotkey(description)` | Bool | La tecla rápida de la commodity, según su descripción ("ctrl alt t"): cx_command da 6 al pulsarla; false si la descripción no vale (o no hay cx_broker); "" la quita |  |
| `cx_key_add(description, n)` | Bool | Una tecla rápida más para la commodity (hasta 32, n de 1 a 32; también un botón del ratón: "rawmouse lalt mouse_leftpress"): cx_command da 100 + n al pulsarla, y el evento no sigue; "" quita la tecla n; false si la descripción no vale (o no hay cx_broker) |  |
| `cx_command()` | Int | La siguiente orden de Exchange o de la tecla rápida: 0 ninguna, 1 ocultar, 2 mostrar, 3 desactivar, 4 activar, 5 quitar, 6 tecla rápida. Desactivar y activar apagan y encienden la commodity (y su tecla) |  |
| `cx_wait(ms)` | Int | Espera, sin gastar nada, hasta que llegue una orden (la da como cx_command), un Ctrl-C (-1, se borra) o pasen ms milisegundos (0) |  |
| `disks_read(ms)` | Int | Lee los volúmenes montados (con disco dentro), su tamaño y su espacio libre, preguntando a todos a la vez y esperando como mucho ms milisegundos: cuántos hay. No pide ningún disco |  |
| `disk_name(i)` | String | El nombre del volumen i (de 0 a disks_read() - 1) del último disks_read, sin los dos puntos |  |
| `disk_kb(i)` | Int | El tamaño del volumen i en KB (como lo enseña Info); -1 si no contestó a tiempo |  |
| `disk_free_kb(i)` | Int | El espacio libre del volumen i en KB; -1 si no contestó a tiempo |  |
| `net_ifs_read()` | Int | Lee las interfaces de red de Roadshow (también lo0), su estado y sus bytes: cuántas hay; -1 sin pila TCP/IP o con una que no lo dice (AmiTCP, Miami) |  |
| `net_if_name(i)` | String | El nombre de la interfaz i (de 0 a net_ifs_read() - 1) del último net_ifs_read |  |
| `net_if_up(i)` | Bool | True si la interfaz i está levantada (conectada) |  |
| `net_if_bytes_in(i)` | Int | Los bytes recibidos por la interfaz i (los 32 bits bajos: la diferencia entre dos lecturas son los bytes de entretanto, aunque pase de 2 GB) |  |
| `net_if_bytes_out(i)` | Int | Los bytes enviados por la interfaz i (los 32 bits bajos, como net_if_bytes_in) |  |
| `pistorm_temperature()` | Int | La temperatura de la Raspberry Pi de una PiStorm (Emu68), en décimas de grado Celsius (523: 52,3), de su firmware por el mailbox.resource de Emu68; -1 sin Emu68 |  |
| `wifi_read(interface, ms)` | Int | Pide al driver SANA-II de una interfaz de Roadshow su señal WiFi, esperando como mucho ms milisegundos: 0 leída (wifi_signal, wifi_noise), 1 no contestó a tiempo, 2 el driver no lo dice, 3 no hay esa interfaz, 4 el driver da un error (desconectado), 5 la pila tiene el driver solo para ella, -1 sin Roadshow |  |
| `wifi_read_device(driver, unit, ms)` | Int | Como wifi_read, preguntando directamente a un driver SANA-II en uso ("wifipi.device", unidad 0), con cualquier pila TCP/IP: 0 leída, 1 no contestó a tiempo, 2 el driver no lo dice, 3 no hay ese driver en uso, 4 desconectado, 5 la pila lo tiene solo para ella |  |
| `net_drivers_read()` | Int | Lee los drivers de red SANA-II en uso, con cualquier pila TCP/IP (los de DEVS:Networks que algo tiene abiertos): cuántos |  |
| `net_driver_name(i)` | String | El nombre del driver i (de 0 a net_drivers_read() - 1) del último net_drivers_read ("wifipi.device") |  |
| `net_driver_read(driver, unit, ms)` | Int | Pide a un driver SANA-II en uso sus paquetes de entrada y salida, esperando como mucho ms: los códigos de wifi_read_device (0 leído: net_driver_packets_in, net_driver_packets_out) |  |
| `net_driver_has_bytes()` | Bool | True si el driver del último net_driver_read cuenta bytes (sus paquetes IPv4, IPv6 y ARP): net_driver_bytes_in y net_driver_bytes_out |  |
| `net_driver_bytes_in()` | Int | Los bytes recibidos por el driver del último net_driver_read (los 32 bits bajos), si net_driver_has_bytes |  |
| `net_driver_bytes_out()` | Int | Los bytes enviados por el driver del último net_driver_read, si net_driver_has_bytes |  |
| `net_driver_packets_in()` | Int | Los paquetes recibidos por el driver del último net_driver_read que dio 0 |  |
| `net_driver_packets_out()` | Int | Los paquetes enviados por el driver del último net_driver_read que dio 0 |  |
| `wifi_signal()` | Int | El nivel de señal del último wifi_read que dio 0, en dBm (-30 muy bueno, -90 muy malo) |  |
| `wifi_noise()` | Int | El nivel de ruido del último wifi_read que dio 0, en dBm |  |
| `usb_hid_read()` | Int | Lee los dispositivos USB (cada interfaz) que lleva la hid.class de Poseidon: cuántos; -1 sin poseidon.library 4 |  |
| `usb_hid_name(i)` | String | El nombre del producto del dispositivo USB i (de 0 a usb_hid_read() - 1) del último usb_hid_read |  |
| `usb_hid_maker(i)` | String | El fabricante del dispositivo USB i |  |
| `usb_hid_vendor(i)` | Int | El VendorID del dispositivo USB i |  |
| `usb_hid_product(i)` | Int | El ProductID del dispositivo USB i |  |
| `usb_hid_kind(i)` | Int | Qué es el dispositivo USB i: 1 ratón, 2 teclado, 0 otra cosa (muchos trackpads) |  |
| `usb_hid_emitter(i)` | Int | El emisor del dispositivo USB i: el número de la tarea de hid.class que envía sus movimientos, para mouse_curve |  |
| `mouse_curve(emitter, factors)` | Bool | La curva de aceleración de un ratón: el emisor 0 es el ratón del Amiga (y todo movimiento que no venga de un ratón USB); si no, uno de usb_hid_emitter. factors: una lista de centésimas (100 = tal cual), la entrada i para un movimiento de i unidades, la última desde ahí (hasta 32); [] la quita. Las fracciones que sobran se guardan. False si input.device no se abre o ya hay 16 emisores |  |
| `mouse_curve_events(emitter)` | Int | Cuántos movimientos ha escalado la curva de un emisor |  |
| `mouse_curves_off()` | — | Quita ya las curvas de input.device (al acabar el programa también); un mouse_curve las vuelve a poner. Bajo el parche de otro programa queda un puente que lo deja pasar todo |  |
| `mouse_patch_left()` | Int | Cuántos puentes quedaron bajo el parche de otro programa en input.device (lo dejan pasar todo, para siempre) |  |
| `mouse_prefs_ticks()` | Int | La velocidad del ratón del sistema (preferencias de Input): 1 la más rápida, 2, 4 la más lenta |  |
| `mouse_prefs_accel()` | Bool | True si está puesta la aceleración del ratón del sistema (preferencias de Input) |  |
| `mouse_prefs_set(ticks, accel)` | — | Pone la velocidad y la aceleración del ratón del sistema; vuelven a ser como eran al acabar el programa |  |
| `tr(id, text)` | String | El texto número id del catálogo del programa (@catalog) en el idioma del usuario; text (el del propio programa) sin catálogo, sin ese número o sin locale.library |  |
| `catalog_open(name, version)` | Bool | Abre otro catálogo ("X.catalog", versión 0: cualquiera) en los idiomas del usuario en vez del que se usa; false si no hay (tr da los textos del propio programa) |  |
| `catalog_language()` | String | El idioma del catálogo que se usa ("english"); "" si no hay |  |
| `clock_read()` | — | Toma la fecha y la hora del reloj del sistema: clock_year, clock_month... dan sus partes |  |
| `clock_year()` | Int | El año del último clock_read (1978...) |  |
| `clock_month()` | Int | El mes del último clock_read (1 a 12) |  |
| `clock_day()` | Int | El día del mes del último clock_read (1 a 31) |  |
| `clock_weekday()` | Int | El día de la semana del último clock_read: 0 domingo, 1 lunes ... 6 sábado |  |
| `clock_hour()` | Int | La hora del último clock_read (0 a 23) |  |
| `clock_minute()` | Int | El minuto del último clock_read |  |
| `clock_second()` | Int | El segundo del último clock_read |  |
| `date_text(format)` | String | La fecha y la hora de ahora como dice format, con el FormatDate de locale.library en el idioma y el país del usuario: %A día, %d-%m-%Y, %b mes, %H:%M:%S... (en inglés sin locale.library) |  |
| `locale_gmt_offset()` | Int | Cuántos minutos va el reloj del Amiga por delante de GMT (60 en España en invierno), de Locale; 0 sin locale.library. Así guarda git sus horas ("+0100") |  |
| `locale_decimal_point()` | String | Lo que va antes de los decimales en el país del usuario: "," en España, "." en inglés (también sin locale.library) |  |
| `locale_group_separator()` | String | Lo que separa los miles en el país del usuario: "." en España (1.234,5), "," en inglés (1,234.5); puede ser "" |  |
| `locale_date_order()` | String | El orden de día, mes y año en la fecha corta del usuario: "DMY", "MDY" o "YMD" |  |
| `program_version()` | String | El nombre y la versión del programa de @version ("Trasfondo 0.7"); "" sin ella |  |
| `file_notify(path)` | Int | Vigila un fichero (puede no existir aún): su número (1 a 8), 0 si no se puede vigilar. cx_wait da 7 cuando cambia; file_changed(n) dice si cambió |  |
| `file_changed(n)` | Bool | True si el fichero vigilado con ese número cambió desde el último file_changed |  |
| `file_notify_end(n)` | — | Deja de vigilar ese fichero (al acabar el programa se dejan todos) |  |
| `file_notify_signal()` | Int | La señal de los ficheros vigilados, para mui_wait_event_signals (0 antes de un file_notify) |  |
| `run_program(command)` | Bool | Empieza una orden ("SYS:Prefs/Font", "\"Work:Mi Prog\" arg") en otro proceso sin esperar, con su entrada y su salida en NIL:; false si no pudo empezar |  |
| `program_relaunch()` | — | Al acabar el programa, lo vuelve a empezar (después de todo lo de su final, también el puerto de single_instance) como empezó: desde el Workbench (3.5+: con su icono) o desde un Shell con sus argumentos. Para actualizarse |  |
| `dos_requesters(on)` | — | false: sin requesters de "Inserta el volumen" ni de errores de disco para este programa (la llamada falla en su lugar); true: como antes. Al acabar el programa vuelven |  |
| `base64_to_file(text, file)` | Int | Escribe en un fichero los bytes de un texto en base64 (sin mirar espacios ni saltos de línea, con relleno = o sin él): los bytes escritos, o -1 si el texto no es base64 (y entonces no hay fichero) o no se puede escribir |  |
| `cpu_start()` | Bool | Empieza a contar la CPU de cada tarea (los ganchos de cambio de tarea de exec; una tarea con ganchos de otro programa no se cuenta): false sin EClock o antes del OS 2.04 |  |
| `cpu_sample()` | Int | Toma una muestra: el número de tareas, con la CPU que gastó cada una desde la muestra anterior (o cpu_start), de más a menos; también engancha las tareas empezadas desde entonces |  |
| `cpu_task_name(i)` | String | El nombre de la tarea i de la última muestra, desde 0 (de un proceso de Shell, su orden) |  |
| `cpu_task_load(i)` | Int | La CPU de la tarea i de la última muestra, en tanto por mil |  |
| `cpu_total()` | Int | La CPU de todas las tareas contadas en la última muestra, en tanto por mil (lo demás es reposo) |  |
| `cpu_stop()` | — | Quita los ganchos de las tareas (al acabar el programa también) |  |
| `task_signal()` | Int | La máscara de señal que cada tarea envía al programa cuando acaba su función (para mui_wait_event_signals); 0 si no queda ninguna libre |  |
| `task_result(task)` | Int | Lo que devolvió la función (la espera si no ha acabado) |  |
| `task_free(task)` | — | Olvida la tarea (la espera si sigue en marcha); al acabar, el programa espera a las que queden |  |

## Imágenes (datatypes)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `image_load(file)` | Int | Una imagen de un fichero con los datatypes (ILBM; PNG, GIF, JPEG si el sistema los tiene), con los colores de la pantalla en la que se dibuja: la imagen, o 0 |  |
| `image_width(image)` | Int | El ancho de una imagen |  |
| `image_height(image)` | Int | El alto de una imagen |  |
| `image_draw(image, x, y)` | — | Dibuja una imagen en x, y (sus píxeles transparentes no se dibujan) |  |
| `image_draw_part(image, sx, sy, x, y, w, h)` | — | Dibuja la parte w x h de una imagen que empieza en sx, sy, en x, y |  |
| `image_scale(image, w, h)` | Int | Una copia de una imagen a w x h píxeles: una imagen nueva, o 0 |  |
| `image_free(image)` | — | Libera una imagen (las que queden se liberan al acabar) |  |
| `image_from_rgb(buffer, width, height, alpha)` | Int | Una imagen con los píxeles de un búfer (RGB, o RGBA con alfa: mezclado con lo de debajo en RTG, dibujado desde 128 en una pantalla de paleta), con los colores de la pantalla: la imagen, o 0 (necesita picture.datatype V43, AmigaOS 3.5+, salvo en pantallas RTG) |  |

## Argumentos

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `arg_count()` | Int | Cuántos argumentos recibió el programa del Shell, o iconos de proyecto del Workbench (un doble clic en un documento, mayúsculas + clic en varios) |  |
| `arg(i)` | String | El argumento i, desde 0 ("" si no hay); desde el Workbench, la ruta entera del icono |  |
| `click_x()` | Int | La X del último On Click, en la ventana (dentro de sus bordes) |  |
| `click_y()` | Int | La Y del último On Click, en la ventana (dentro de sus bordes) |  |
| `time_ms()` | Int | Los milisegundos desde que empezó el programa (EClock de timer.device) |  |

## Compresión (zlib)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `inflate(src, n, dest, max)` | Int | Descomprime n bytes de deflate sin cabecera (como en un ZIP) del búfer src a dest: los bytes escritos, o -1 si no es deflate o está cortado, -2 si no cabe en max, -3 si no hay memoria (zlib) |  |
| `inflate_auto(src, n, dest, max)` | Int | inflate para gzip, zlib o deflate sin cabecera, según sus primeros bytes (un cuerpo HTTP con Content-Encoding gzip o deflate): los bytes escritos, o lo mismo que inflate |  |
| `deflate(src, n, dest, max, level)` | Int | Comprime n bytes del búfer src a dest como deflate sin cabecera, nivel 0 (sin comprimir) a 9 (lo más pequeño; -1: 6): los bytes escritos, -2 si no caben en max, -3 si no hay memoria (zlib; unos 260 KB mientras trabaja, con cualquier nivel) |  |
| `crc32(buffer, n, crc)` | Int | El CRC-32 (como en ZIP y PNG) de n bytes de un búfer, siguiendo desde crc (0 para empezar) |  |
| `adler32(buffer, n, a)` | Int | El Adler-32 (la suma del final de un zlib) de n bytes de un búfer, siguiendo desde a (1 para empezar) |  |
| `inflate_used()` | Int | Los bytes de entrada que usó el último inflate o inflate_auto (con cabecera zlib, también su adler32): dónde empieza el siguiente objeto en un pack de git |  |
| `sha1(buffer, n)` | String | El SHA-1 de n bytes de un búfer, en 40 cifras hexadecimales (así nombra git sus objetos) |  |
| `sha1_text(s)` | String | El SHA-1 de un texto, en 40 cifras hexadecimales |  |
| `sha1_new()` | Int | Un SHA-1 hecho por partes con sha1_add, sha1_add_text y sha1_add_byte: su número (1-8), 0 si están todos en uso. Lo acaban sha1_hex o sha1_bytes |  |
| `sha1_add(sha, buffer, n)` | — | Añade n bytes de un búfer a un SHA-1 de sha1_new |  |
| `sha1_add_text(sha, s)` | — | Añade un texto a un SHA-1 de sha1_new |  |
| `sha1_add_byte(sha, b)` | — | Añade un byte (0-255) a un SHA-1 de sha1_new (el 0 tras el "blob 6" de git) |  |
| `sha1_hex(sha)` | String | Acaba un SHA-1 de sha1_new: sus 40 cifras hexadecimales ("" si ese número no está en uso) |  |
| `sha1_bytes(sha, out)` | Bool | Acaba un SHA-1 de sha1_new: sus 20 bytes a un búfer (como los guarda git en los árboles y el índice); false si ese número no está en uso |  |

## UTF-8

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `utf8_next(s, i)` | Int | La posición del carácter UTF-8 que sigue al del byte i (el largo, al final) |  |
| `utf8_prev(s, i)` | Int | La posición del carácter UTF-8 anterior al byte i (0 al principio) |  |
| `utf8_code(s, i)` | Int | El punto de código del carácter UTF-8 en el byte i (65533 para un byte no válido, 0 fuera del texto) |  |
| `utf8_char(code)` | String | Un texto con el carácter de ese punto de código en UTF-8 ("" para 0; U+FFFD si no es uno) |  |
| `utf8_length(s)` | Int | Cuántos caracteres UTF-8 tiene s (cada byte no válido cuenta como uno) |  |
| `utf8_to_latin1(s)` | String | Un texto UTF-8 en Latin-1: lo que Latin-1 no tiene pasa a algo parecido (“ a ", € a EUR, … a ...) o a ?, igual que los bytes no válidos |  |
| `latin1_to_utf8(s)` | String | Un texto Latin-1 en UTF-8 (los bytes desde 128 ocupan dos) |  |
| `utf8_check(buffer, from, to)` | Int | La posición del primer byte, de from a to - 1 de un búfer, que no es UTF-8 válido (o empieza una secuencia cortada por to); -1 si todos lo son |  |

## Comparar y buscar en un búfer

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `buffer_equals(buffer, offset, n, s)` | Bool | Si los n bytes de un búfer en offset son el texto s (y s tiene n bytes) |  |
| `buffer_find_byte(buffer, from, to, byte)` | Int | La posición del primer byte igual a byte, de from a to - 1; o -1 |  |
| `buffer_find_any(buffer, from, to, bytes)` | Int | La posición del primer byte, de from a to - 1, que es uno de los bytes del texto bytes; o -1 |  |

## Double y texto

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_from_double(d, decimals)` | String | Un Double con tantos decimales (0: ninguno), su decimal más corto redondeado alejándose del cero (2.675 con 2 da 2.68); decimales < 0: el más corto que se lee igual |  |
| `str_to_double(s)` | Double | El Double del principio del texto, como Double(s): exacto hasta 17 cifras significativas; 0.0 si no hay número |  |

## Matemáticas de Double

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sqrt(x)` | Double | La raíz cuadrada (nan para un negativo) |  |
| `pow(x, y)` | Double | x elevado a y |  |
| `exp(x)` | Double | e elevado a x |  |
| `log(x)` | Double | El logaritmo neperiano (-inf para 0, nan para un negativo) |  |
| `log10(x)` | Double | El logaritmo en base 10 |  |
| `sin(x)` | Double | El seno de x radianes |  |
| `cos(x)` | Double | El coseno de x radianes |  |
| `tan(x)` | Double | La tangente de x radianes |  |
| `asin(x)` | Double | El arcoseno en radianes, de -pi/2 a pi/2 (nan fuera de -1..1) |  |
| `acos(x)` | Double | El arcocoseno en radianes, de 0 a pi (nan fuera de -1..1) |  |
| `atan(x)` | Double | El arcotangente en radianes, de -pi/2 a pi/2 |  |
| `atan2(y, x)` | Double | El ángulo del punto (x, y) en radianes, de -pi a pi |  |
| `floor(x)` | Double | El mayor número entero que no pasa de x (un Double) |  |
| `ceil(x)` | Double | El menor número entero que no es menor que x (un Double) |  |
| `round(x)` | Double | El número entero más cercano, las mitades alejándose del cero (2.5 da 3.0, -2.5 da -3.0) |  |
| `trunc(x)` | Double | La parte entera, hacia el cero (-2.7 da -2.0) |  |
| `fmod(x, y)` | Double | El resto de x / y con el signo de x (nan si y es 0) |  |
| `abs(x)` | Double | El valor absoluto, un Double |  |
| `is_nan(x)` | Bool | True si x es nan (no es un número: sqrt(-1.0), 0.0 / 0.0) |  |
| `is_inf(x)` | Bool | True si x es inf o -inf |  |

## Expresiones regulares y comodines

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `regex_match(pattern, text, ignore_case)` | Bool | True si el texto entero encaja con la expresión regular (la sintaxis común de ICU: . * + ? {m,n} [] [^] ^ $ \d \w \s \b \| grupos); false también si el patrón está mal (regex_error dice por qué) |  |
| `regex_find(pattern, text, from, ignore_case)` | Int | La posición en bytes donde empieza lo primero que encaja desde el byte from; -1 si no hay (o el patrón está mal); regex_length da su largo |  |
| `regex_length()` | Int | El largo en bytes de lo último que encajó con regex_find o regex_match (0 si nada) |  |
| `regex_error()` | String | Por qué está mal el último patrón; "" si está bien |  |
| `wildcard_match(pattern, text, ignore_case)` | Bool | True si el texto entero encaja con los comodines de Excel: * cualquier cosa, ? un carácter, ~ delante de un carácter lo toma tal cual (~* ~? ~~) |  |

## Simular teclado y ratón

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `input_key(code, qualifiers)` | — | Pulsa y suelta una tecla en bruto en la ventana activa (0x44 Return, 0x45 Esc, 0x4C arriba, 0x4D abajo, 0x4E derecha, 0x4F izquierda, 0x41 Retroceso), con las teclas 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 Amiga (sumadas) pulsadas alrededor |  |
| `input_text(text)` | — | Escribe un texto en la ventana activa con el mapa de teclado ("=SUM(A1:A3)"); lo que el mapa no puede escribir se queda fuera |  |
| `input_move(x, y)` | — | Lleva el puntero a (x, y) desde la esquina de la ventana activa |  |
| `input_click(x, y, qualifiers)` | — | Clic con el botón izquierdo en (x, y) desde la esquina de la ventana activa, con las teclas 1 Mayúsculas, 2 Ctrl, 4 Alt (Amiga + clic es del sistema) |  |
| `input_button(button, down)` | — | Pulsa (down true) o suelta un botón del ratón donde está el puntero: 1 izquierdo, 2 derecho (menús, un menú contextual), 3 central |  |
| `input_drag(x1, y1, x2, y2)` | — | Pulsa el botón izquierdo en (x1, y1), lo lleva pulsado a (x2, y2) y lo suelta (desde la esquina de la ventana activa) |  |
| `input_qualifiers()` | Int | Las teclas pulsadas ahora (PeekQualifier de input.device): 1, 2 Mayúsculas; 8 Ctrl; 16, 32 Alt; 64, 128 Amiga; 0 si no se puede abrir input.device |  |
| `input_menu(menu, item, hold)` | Bool | Elige con el ratón, como un usuario, la opción item (desde 0, separadores incluidos) del menú menu (desde 0) de la ventana activa: el botón derecho en su título, hasta la opción, hold tics (1/50 s) pulsado, y suelta; false si no hay esa opción |  |
| `input_move_screen(x, y, buttons)` | — | Lleva el puntero a (x, y) de la pantalla de píxel en píxel con botones pulsados (1 izquierdo, 2 derecho, 0 ninguno): los menús de MUI lo siguen |  |
| `input_active_title()` | String | El título de la ventana activa ("" si no hay): para esperar a la del programa que se prueba |  |

## Portapapeles

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `clip_write_text(s)` | Bool | Copia un texto UTF-8 al portapapeles (unidad 0, IFF FTXT en Latin-1, como lo leen los demás programas): lo que Latin-1 no tiene pasa a algo parecido, como utf8_to_latin1 (€ a EUR); false si no se puede escribir |  |
| `clip_read_text()` | String | El texto del portapapeles (unidad 0) en UTF-8; "" si está vacío o no tiene texto |  |
| `clip_write_block(unit, type, buffer, n)` | Bool | Copia n bytes de un búfer a la unidad 1-255 del portapapeles como un FORM de un tipo propio (4 caracteres, "LCLC"), después de clip_write_text: queda unido a ese texto, y si se copia otra cosa a la unidad 0, el bloque se da por perdido |  |
| `clip_block_size(unit, type)` | Int | Los bytes del bloque de ese tipo en una unidad del portapapeles; -1 si no hay o se copió otra cosa después |  |
| `clip_read_block(unit, type, dest, max)` | Int | Copia el bloque de ese tipo de una unidad del portapapeles al búfer dest: sus bytes, -1 si no hay o se copió otra cosa después, -2 si no cabe en max |  |

## Ordenar textos según el idioma

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_compare_locale(a, b, ignore_case)` | Int | Compara dos textos UTF-8 en el orden del idioma del usuario (locale.library): -1 si a va antes, 0 si son iguales, 1 si va antes b; los acentos y las mayúsculas cuentan solo después de las letras ("árbol" antes que "barco", "apple" antes que "Banana"), y nada con ignore_case. Sin locale.library, por sus bytes Latin-1 |  |

## Sistema y programa

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `time_unix()` | Int | El reloj del sistema en segundos desde el 1 de enero de 1970 (para fechas de HTTP y cookies) |  |
| `clock_days()` | Int | Los días desde el 1 de enero de 1978 según el reloj del sistema (el ds_Days de DateStamp) |  |
| `mem_largest()` | Int | El bloque de memoria libre más grande, chip o fast, en bytes |  |
| `program_exit(rc)` | — | Acaba el programa ya con ese código de retorno (5 aviso, 10 error, 20 fallo), tras la limpieza de siempre: ventanas, ficheros y memoria |  |
| `run_command(command)` | Int | Ejecuta una orden y espera a que acabe, con su salida en la del programa: su código de retorno, -1 si no pudo empezar |  |
| `wb_open(path)` | Bool | Abre un cajón, un programa o un proyecto como un doble clic en su icono (workbench.library 44, OS 3.5+); false si no pudo |  |
| `program_path()` | String | La ruta entera del programa ("Work:Tachyon/Tachyon"), desde un Shell o desde el Workbench |  |
| `locale_language()` | String | El primer idioma preferido del usuario en las preferencias de Locale ("español"); "" si no hay |  |
| `cpu_model()` | Int | El procesador: 68000, 68010, 68020, 68030, 68040 o 68060 |  |
| `fpu_model()` | Int | La FPU: 68881, 68882, 68040 o 68060 (la del procesador); 0 si no hay |  |
| `library_version(name)` | Int | La versión de una librería ("muimaster.library"), cargándola si no está en memoria; -1 si no está |  |
| `library_revision(name)` | Int | La revisión de una librería (el 3 de 47.3), como library_version; -1 si no está |  |
| `resident_version(name)` | Int | La versión de un módulo residente del sistema (FindResident: "MorphOS" dice que el programa corre en MorphOS); -1 si no hay |  |
| `task_priority(n)` | Int | Pone la prioridad del programa (-128 a 127; el Shell da 0): la que tenía |  |
| `build_date()` | String | La fecha en que se compiló el programa, "2026-10-28" |  |
| `build_time()` | String | La hora en que se compiló el programa, "20:45:10" |  |
| `console_flush()` | — | Saca ya lo que Print dejó en el búfer de la salida (una línea de progreso sin su final) |  |
| `run_capture(command, timeout_ms)` | String | Ejecuta una orden y espera a que acabe: lo que escribió, con su código de retorno en run_rc(). Con timeout_ms mayor que 0, al pasar ese tiempo la orden recibe Ctrl-C (y otra vez cada segundo hasta que acaba). Solo su salida: AmigaOS no da canal de errores a una orden lanzada así (el stderr de un programa en C va a la consola; dashc escribe sus errores por su salida en el Amiga) |  |
| `run_start(command, timeout_ms)` | Int | run_capture sin esperar: un número para run_ready, run_break y run_finish, 0 si no pudo empezar. El programa espera al acabar a las que no terminó |  |
| `run_ready(run)` | Bool | Verdadero cuando un run_start ha acabado (no espera; también aplica el tope de tiempo) |  |
| `run_break(run)` | — | Manda Ctrl-C a un run_start que sigue en marcha (y otra vez cada segundo hasta que acaba) |  |
| `run_finish(run)` | String | Lo que escribió un run_start, como run_capture (espera si sigue en marcha), y lo olvida |  |
| `run_rc()` | Int | El código de retorno del último run_capture o run_finish: el de la orden, -1 si no pudo empezar, -2 si se le acabó el tiempo |  |
| `env_get(name)` | String | Una variable de entorno (de la Shell del programa y si no, de ENV:), hasta su primer fin de línea; "" si no existe |  |
| `env_set(name, value, save)` | Bool | Pone una variable en ENV: (con save verdadero, también en ENVARC:, para que siga tras reiniciar); falso si no pudo |  |
| `rexx_send(port, command)` | String | Manda una orden ARexx al puerto público de otro programa ("MULTIVIEW.1"; "REXX": ejecutar un script) y espera la respuesta: su RESULT ("" si no hay), el RC en rexx_rc(). No al puerto del propio programa: se esperaría a sí mismo |  |
| `rexx_rc()` | Int | El RC del último rexx_send: 0 bien, 5, 10, 20... los del programa; -1 si no existe el puerto, -2 sin rexxsyslib.library |  |
| `rexx_port(name)` | Bool | Abre el puerto ARexx propio del programa con ese nombre ("ADDRESS NOMBRE" desde ARexx): false si ya hay uno, o sin rexxsyslib.library. Sus órdenes, con rexx_get |  |
| `rexx_get()` | String | La siguiente orden que llegó al puerto de rexx_port ("" si ninguna): espera su rexx_reply (el siguiente rexx_get la contesta con RC 0) |  |
| `rexx_reply(rc, result)` | — | Contesta la orden de rexx_get: rc (0 bien, 5, 10, 20) y, con 0, result como RESULT ("": ninguno) |  |
| `notify(title, text)` | Bool | Un aviso para el escritorio, con el nombre del programa: a la barra de Trasfondo por ARexx (puerto TRASFONDO) o, sin ella, a su lista (ENV:Trasfondo.avisos), que enseña al arrancar. False si no llegó a ninguno de los dos |  |
| `ports_read()` | Int | Lee los nombres de los puertos públicos abiertos (los de ARexx entre ellos): cuántos, para port_name, hasta el siguiente ports_read |  |
| `port_name(i)` | String | El nombre del puerto i (desde 0) del último ports_read |  |
| `tasks_read()` | Int | Lee las tareas y procesos del sistema (el programa, el primero): cuántos, para las task_entry_, hasta el siguiente tasks_read |  |
| `task_entry_name(i)` | String | El nombre de la tarea i del último tasks_read ("Shell Process", "input.device"...) |  |
| `task_entry_command(i)` | String | La orden que ejecuta un proceso de Shell del último tasks_read ("" si ninguna) |  |
| `task_entry_state(i)` | String | El estado de la tarea i: "running" (el programa), "ready" o "waiting" |  |
| `task_entry_priority(i)` | Int | La prioridad de la tarea i del último tasks_read |  |
| `task_entry_cli(i)` | Int | El número de Shell de la tarea i (el que da Status, para Break), 0 si no es un proceso de Shell |  |
| `assigns_read()` | Int | Lee las asignaciones (C:, LIBS:, las de Assign): cuántas, para assign_name y assign_path, hasta el siguiente assigns_read |  |
| `assign_name(i)` | String | El nombre de la asignación i del último assigns_read, sin los dos puntos |  |
| `assign_path(i)` | String | Adónde apunta la asignación i: un cajón ("Workbench:C"), varios separados por ";", o el nombre que buscará una diferida o no ligada |  |

## JSON leído en C (para lib/json.dash)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `json_scan(text)` | Int | Lee un texto JSON a una tabla de nodos en orden, cada uno seguido de lo que contiene (lib/json.dash hace su árbol con ella): cuántos, -1 si no es JSON (json_scan_error dice por qué y dónde) |  |
| `json_scan_error()` | String | Por qué el último json_scan dio -1, y en qué byte ("unexpected end at byte 1") |  |
| `json_scan_kind(i)` | Int | El tipo del nodo i: 0 null, 1 true o false, 2 número, 3 texto, 4 lista, 5 objeto |  |
| `json_scan_count(i)` | Int | Cuántos elementos tiene un nodo de lista u objeto (van detrás); 1 si es true, 0 si es false |  |
| `json_scan_text(i)` | String | El texto de un nodo de texto (sin sus escapes, \uXXXX en UTF-8) o de número (como está escrito) |  |
| `json_scan_name(i)` | String | El nombre del nodo i dentro de su objeto ("" en una lista o arriba del todo) |  |

## Depurador (el programa depurado, con dash --debug)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `dbg_start(program, args)` | Bool | Carga un programa compilado con dash --debug y lo lanza en un proceso propio, en pausa antes de su primera línea (se ponen los puntos de parada y luego dbg_continue): falso si no pudo (dbg_error dice por qué) |  |
| `dbg_error()` | String | Por qué falló el último dbg_start |  |
| `dbg_state()` | Int | El programa depurado: 0 ninguno, 1 en pausa antes de empezar, 2 corriendo, 3 parado en una línea, 4 acabado |  |
| `dbg_signal()` | Int | La señal que recibe el depurador cuando el programa para o acaba (para mui_wait_event_signals) |  |
| `dbg_wait(ms)` | Int | Espera a que el programa pare o acabe, como mucho ms (0: sin tope): su estado |  |
| `dbg_break(file, line)` | Bool | Un punto de parada en esa línea de ese fichero ("prog.dash": el final de su ruta): falso si la línea no tiene código |  |
| `dbg_unbreak(file, line)` | Bool | Quita el punto de parada de esa línea |  |
| `dbg_continue()` | Bool | Sigue (desde el principio o una parada) hasta un punto de parada o el final |  |
| `dbg_step()` | Bool | Sigue hasta la línea siguiente, entrando en las funciones a las que llama |  |
| `dbg_next()` | Bool | Sigue hasta la línea siguiente de esta función (o de la que la llamó) |  |
| `dbg_out()` | Bool | Sigue hasta que la función vuelve: la línea siguiente de la que la llamó |  |
| `dbg_pause()` | Bool | Para el programa que corre en la siguiente línea que ejecute |  |
| `dbg_end(ms)` | Bool | Acaba el programa (Ctrl-C y, en su siguiente línea, su final de siempre): verdadero si acabó en ms |  |
| `dbg_rc()` | Int | El código de retorno del programa acabado |  |
| `dbg_file()` | String | El fichero de la línea donde paró el programa (su ruta entera) |  |
| `dbg_line()` | Int | La línea donde paró el programa (0 si no está parado) |  |
| `dbg_function()` | String | La función donde paró el programa ("Main", "Punto.mover"...) |  |
| `dbg_frames()` | Int | Cuántas llamadas hay abiertas donde paró: 1 en Main, 2 en una función que llamó Main... (0 si no está parado) |  |
| `dbg_frame_function(i)` | String | La función de la llamada i: 0 donde paró, 1 la que la llamó... |  |
| `dbg_frame_line(i)` | Int | La línea donde está la llamada i: 0 donde paró, 1 la de la llamada en la que la llamó... |  |
| `dbg_frame_file(i)` | String | El fichero de la llamada i (su ruta entera) |  |
| `dbg_vars(i)` | Int | Cuántas variables ve la llamada i: sus parámetros y las variables declaradas antes de su línea |  |
| `dbg_var_name(i, k)` | String | El nombre de la variable k (desde 0) de la llamada i |  |
| `dbg_var_type(i, k)` | String | El tipo de la variable k de la llamada i, como en Dash ("Int", "[String]", "Punto") |  |
| `dbg_globals()` | Int | Cuántas variables globales tiene el programa |  |
| `dbg_global_name(g)` | String | El nombre de la global g (desde 0) |  |
| `dbg_value(i, expr)` | String | El valor de expr en la llamada i, como texto: una variable de esa llamada o una global, con .campo y [n] detrás ("p.hijos[0].x"): 3, "hola", Punto(x: 3, y: 4), [1, 2], nil; "? " y el porqué si no se puede |  |
| `dbg_value_type(i, expr)` | String | El tipo de expr en la llamada i ("" si no se puede) |  |
| `dbg_reg(n)` | Int | Un registro del programa parado: 0-7 d0-d7, 8-15 a0-a7, 16 el PC |  |
| `dbg_peek(addr, size)` | Int | 1, 2 o 4 bytes de memoria en addr, sin signo |  |
| `dbg_output()` | String | Lo que ha escrito el programa hasta ahora (salida y salida de errores) |  |

## Imágenes decodificadas por el programa (sin datatypes)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `image_decode(file, maxw, maxh)` | Int | Decodifica un JPEG (TJpgDec), WebP (libwebp; los dos ya reducidos al decodificar), PNG, GIF, BMP (stb_image) o SVG (nanosvg: dibujado para cubrir maxw x maxh, RGBA) a píxeles RGB o RGBA, reducidos hasta que no pasen mucho de maxw x maxh (0, 0: su tamaño; negativos, un tope: un SVG va entonces a su tamaño, más pequeño si no cabe): la imagen decodificada, o 0. Sin datatypes, y vale dentro de un task_start |  |
| `image_decode_start(file, maxw, maxh)` | Int | image_decode en un proceso aparte, uno por debajo de la prioridad del programa, para que la ventana siga respondiendo: un número para image_decode_ready e image_decode_finish, o 0 si no pudo empezar |  |
| `image_decode_ready(t)` | Bool | Cierto cuando un image_decode_start ha terminado (no espera) |  |
| `image_decode_finish(t)` | Int | Lo que decodificó un image_decode_start, como image_decode (0 si no pudo); espera si aún no ha acabado y libera su proceso |  |
| `image_decoded_width(d)` | Int | El ancho de una imagen decodificada |  |
| `image_decoded_height(d)` | Int | El alto de una imagen decodificada |  |
| `image_decoded_alpha(d)` | Bool | True si una imagen decodificada tiene alfa (4 bytes por píxel, RGBA; si no, 3, RGB) |  |
| `image_decoded_pixels(d)` | Int (dirección) | Los píxeles de una imagen decodificada, fila tras fila: un búfer para buffer_get_byte o image_from_rgb |  |
| `image_decoded_free(d)` | — | Libera una imagen decodificada |  |
| `image_from_decoded(d)` | Int | Una imagen (como image_from_rgb) de una imagen decodificada, que hay que liberar después |  |
| `image_from_decoded_size(d, w, h)` | Int | Como image_from_decoded, pero a ancho x alto, con los bordes suaves (cada punto, la media de los que cubre, también la transparencia); la imagen decodificada hay que liberarla después |  |

## Fuentes TrueType, WOFF y WOFF2

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `font_from_ttf(file, size, width)` | Int | Una fuente TrueType (TTF, un OTF con contornos TrueType, o un WOFF o WOFF2 de ellos) a size píxeles de em y al width % de su ancho (0: 100), sus caracteres Latin-1 en un plano de 1 bit (stb_truetype): una fuente para font_use, o 0. Se libera con font_ttf_free, no con font_close |  |
| `font_ttf_icon(file, size, code)` | Int | Una fuente del fichero cuya "A" es el carácter code (un icono de una fuente web, en la zona privada de Unicode) a size píxeles, con las demás letras vacías: se dibuja "A" con ella; 0 si no se puede |  |
| `font_ttf_free(font)` | — | Libera una fuente de font_from_ttf (no mientras una ventana siga escribiendo con ella); las que queden se liberan al acabar |  |
| `font_ttf_forget(file)` | — | font_from_ttf guarda los 8 últimos ficheros leídos para otros tamaños: este se lee otra vez la próxima |  |

## Red en una tarea aparte

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `net_bg_open(host, port, timeout_ms)` | Int | Pide una conexión TCP que una tarea propia abre, por la que envía y recibe mientras el programa está ocupado (hasta 48): su número, o -1. net_bg_state dice cómo va |  |
| `net_bg_open_tls(host, port, timeout_ms)` | Int | net_bg_open con TLS (AmiSSL, comprobando su certificado) |  |
| `net_bg_state(c)` | Int | 1 pedida, 2 conectando, 3 negociando la TLS, 4 abierta, 5 cerrada, 6 error (net_bg_error dice por qué) |  |
| `net_bg_stage(c)` | Int | Mientras conecta, en qué fase está, como net_connect_stage |  |
| `net_bg_error(c)` | String | Por qué falló o se cerró una conexión; "" si no |  |
| `net_bg_send(c, text)` | Bool | Deja un texto para enviar (la tarea lo envía en cuanto la conexión esté abierta); false si no hay memoria |  |
| `net_bg_send_buffer(c, buffer, n)` | Bool | net_bg_send de n bytes de un búfer |  |
| `net_bg_recv(c, buffer, max)` | Int | Hasta max bytes de lo que ha llegado, a un búfer, sin esperar: cuántos (0: nada aún), -1 si está cerrada y no queda nada. task_signal despierta al programa cuando llega algo |  |
| `net_bg_pending(c)` | Int | Cuántos bytes han llegado y no se han leído |  |
| `net_bg_close(c)` | — | Cierra una conexión y deja libre su número |  |
| `net_bg_idle(ms)` | — | La tarea acaba sola tras tantos ms sin tráfico (2000; una conexión que el programa sigue leyendo, esperando la respuesta, cuenta como tráfico); cuando hace falta empieza otra |  |
| `net_bg_stop()` | — | Acaba la tarea ya (cierra lo que esté abierto) y la espera; también al acabar el programa |  |

## Ventanas de otros programas (pruebas)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `window_find(title)` | Int | La ventana de otro programa (o la del propio) cuyo título empieza por title, en cualquier pantalla: un número para window_found_* y gadget_*, 0 si no hay (no vale cuando se cierra) |  |
| `window_found_activate(win)` | — | Una ventana de window_find delante, con su pantalla, y activa (los input_* van a la ventana activa) |  |
| `window_found_box(win, what)` | Int | De una ventana de window_find: 0 izquierda, 1 arriba (en su pantalla), 2 ancho, 3 alto, 4 borde izquierdo, 5 borde de arriba |  |
| `gadget_index(win, text)` | Int | El sitio (desde 0, también los gadgets de la propia ventana) del gadget cuyo texto es text en una ventana de window_find; -1 si no hay. Los botones de GadTools no guardan su texto: se cuentan desde uno de al lado |  |
| `gadget_x(win, n)` | Int | La x del centro del gadget del sitio n de una ventana de window_find, desde su esquina (como cuenta input_click); -1 si no hay |  |
| `gadget_y(win, n)` | Int | La y del centro de ese gadget, como gadget_x |  |
| `gadget_selected(win, n)` | Bool | True si el gadget del sitio n (una casilla) está marcado |  |
| `screen_pixel(x, y)` | Int | El color del píxel (x, y) de la pantalla de delante; -1 fuera de ella |  |
| `screen_pixel_rgb(x, y)` | Int | El color del píxel (x, y) de la pantalla de delante como 0xRRGGBB, la pinte quien la pinte; -1 fuera de ella. Lo que hay detrás de una ventana antes de abrirla |  |
| `screen_pen_rgb(n)` | Int | El color del lápiz n de la pantalla del Workbench como 0xRRGGBB: 0 detalle, 1 bloque, 2 texto, 3 brillo, 4 sombra, 5 relleno (la barra de título activa), 6 texto del relleno, 7 fondo, 8 texto resaltado, 9 detalle de la barra, 10 bloque de la barra, 11 borde de la barra; -1 si no lo tiene |  |
| `cx_send(name, command)` | Int | Una orden a una commodity por su nombre, como hace Exchange (15 desactivar, 17 activar, 19 enseñar, 21 ocultar, 23 quitar...): 0 hecho, -1 no hay esa commodity, -2 no tiene puerto, -99 no hay commodities.library |  |

## Gestor de ventanas (las de todos los programas)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `wm_read()` | Int | Lee las ventanas de la pantalla del Workbench, de delante atrás (hasta 64): cuántas, para wm_id, wm_title, wm_task, wm_box y wm_flags, hasta el siguiente wm_read |  |
| `wm_id(i)` | Int | El id de la ventana i del último wm_read, para wm_set_box, wm_front... (0 fuera de la lista) |  |
| `wm_title(i)` | String | El título de la ventana i del último wm_read ("" si no tiene) |  |
| `wm_task(i)` | String | El programa de la ventana i: la orden de un proceso de Shell (sin su ruta), o el nombre de su tarea ("Workbench") |  |
| `wm_path(i)` | String | La ruta del programa de la ventana i (el directorio del que se cargó su proceso y su nombre): "" si no es de un proceso, o si la ventana se cerró desde el wm_read |  |
| `wm_box(i, what)` | Int | De la ventana i: 0 izquierda, 1 arriba, 2 ancho, 3 alto, 4 ancho mínimo, 5 alto mínimo, 6 ancho máximo, 7 alto máximo (0 o 65535: sin límite); -1 fuera de la lista |  |
| `wm_flags(i)` | Int | De la ventana i, sumados: 1 se puede redimensionar, 2 de fondo (backdrop), 4 sin bordes, 8 activa, 16 con barra de arrastre, 32 del propio programa, 64 un cajón del Workbench, 128 con un requester |  |
| `wm_set_box(id, x, y, width, height)` | Bool | Mueve y redimensiona una ventana por su id, dentro de sus límites y de su pantalla (la que no tiene botón de tamaño se queda con el suyo); false si ya no está abierta. Intuition lo hace justo después |  |
| `wm_front(id)` | Bool | Una ventana delante de las demás; false si ya no está abierta |  |
| `wm_back(id)` | Bool | Una ventana detrás de las demás; false si ya no está abierta |  |
| `wm_activate(id)` | Bool | Hace activa una ventana (las teclas van a ella); false si ya no está abierta |  |
| `wm_zip(id)` | Bool | Una ventana a su otro tamaño, como su botón de zoom; false si ya no está abierta |  |
| `wm_active()` | Int | El id de la ventana activa, si está en la pantalla del Workbench; 0 si no |  |
| `wm_at(x, y)` | Int | El id de la ventana que hay en (x, y) de la pantalla del Workbench, la de delante; 0 si ninguna |  |
| `wm_pointer_x()` | Int | Dónde está el puntero en la pantalla del Workbench: la x |  |
| `wm_pointer_y()` | Int | Dónde está el puntero en la pantalla del Workbench: la y |  |
| `wm_bar_height()` | Int | El alto de la barra de título de la pantalla del Workbench (donde suelen empezar las ventanas) |  |
| `wm_bar_gadgets()` | Int | A qué distancia del borde derecho de la barra de título de la pantalla del Workbench empiezan sus botones del sistema (el de profundidad), preguntado a la pantalla; 0 si no lo sabe |  |
| `file_real_path(path)` | String | La ruta real de un fichero o cajón, como la nombra su sistema de ficheros ("SYS:Utilities/Clock" da "System:Utilities/Clock"), para compararla con wm_path: "" si no está |  |
| `app_window(handle)` | Bool | La ventana (0 la actual, o un número de window_create) acepta iconos soltados encima desde el Workbench (AppWindow): true si los acepta. Los da app_drop |  |
| `app_drop()` | String | La ruta del siguiente icono soltado en una app_window, "" si no hay (se mira desde On Timer); app_drop_x y app_drop_y, dónde cayó |  |
| `app_drop_x()` | Int | Dónde cayó el último icono de app_drop: x desde la esquina de la ventana |  |
| `app_drop_y()` | Int | Dónde cayó el último icono de app_drop: y desde la esquina de la ventana |  |
| `icon_load(path)` | Int | El icono (.info) de un programa, cajón o fichero (la ruta sin ".info"), con icon.library y los colores de la pantalla de la ventana (3.5+: iconos en color y PNG, y el de su tipo si no tiene): un número para icon_draw, o 0 |  |
| `icon_draw(icon, x, y)` | — | Dibuja un icono de icon_load con su esquina de arriba a la izquierda en (x, y), como el Workbench, sin su nombre ni marco |  |
| `icon_draw_size(icon, x, y, width, height)` | — | Dibuja un icono de icon_load en (x, y) a width x height, más pequeño o más grande, con los bordes suaves (en una pantalla de color real; en otra, a su tamaño, centrado en ese recuadro) |  |
| `icon_width(icon)` | Int | El ancho de un icono de icon_load tal como lo dibuja icon_draw (0 si no está) |  |
| `icon_height(icon)` | Int | El alto de un icono de icon_load tal como lo dibuja icon_draw (0 si no está) |  |
| `icon_free(icon)` | — | Libera un icono de icon_load (los que queden, al salir) |  |

## Audio

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sound_load(id, filename)` | Bool | Carga un sonido IFF 8SVX (sin comprimir) |  |
| `sound_sample(id, index, value)` | — | Pone una muestra (-128..127) de un sonido de sound_create |  |
| `sound_create(id, length, rate)` | Bool | Crea un sonido en silencio en memoria chip: largo en muestras, frecuencia en muestras por segundo |  |
| `sound_free(id)` | — | Libera la memoria de un sonido |  |
| `sound_play(id, channel)` | — | Toca un sonido una vez en un canal (0-3) |  |
| `sound_stop(channel)` | — | Para un canal |  |
| `sound_loop(id, channel)` | — | Toca un sonido en bucle en un canal (hasta sound_stop) |  |
| `sound_playing(channel)` | Bool | Mira si un canal está sonando |  |
| `sound_volume(channel, vol)` | — | Pone el volumen de un canal (0-64) |  |
| `sound_period(channel, period)` | — | Pone el periodo de un canal (el tono: cuanto más bajo, más agudo) |  |
| `music_load(filename)` | Bool | Carga un fichero MOD |  |
| `music_play()` | — | Empieza a tocar la música |  |
| `music_stop()` | — | Para la música |  |
| `music_pause()` | — | Pausa la música |  |
| `music_resume()` | — | Sigue con la música |  |
| `music_volume(vol)` | — | Pone el volumen de la música (0-64) |  |
| `music_position(pos)` | — | Pone la posición de la música |  |
| `music_pos()` | Int | La posición de la canción que suena (en la lista de orden) |  |
| `music_row()` | Int | La fila del patrón que suena (0-63) |  |
| `music_free()` | — | Libera los datos de la música |  |
| `tone_play(channel, freq, vol, duration)` | — | Toca un tono senoidal: frecuencia en Hz, volumen 0-64, duración en milisegundos (vuelve en seguida) |  |

## Intuition

Ventanas abiertas desde el código, sus gadgets y las peticiones del sistema (fichero, color, fuente, modo de
pantalla).

**Dos formas de tener ventanas.** Con `Window X ... end` se declara una ventana y se abre con `X.open` (ver el
manual, sección 12). Con `window_create` se abre desde el código, sin declararla, y se le pueden abrir varias. Las
dos se pueden mezclar. El `EventLoop` necesita una ventana declarada y abierta; atiende también las de
`window_create`, y `event_window()` dice de cuál vino cada evento.

**Los números de ventana.** `window_create` devuelve un número del 1 al 16, o 0 si no pudo abrirla. Las demás
funciones `window_*` reciben ese número; el 0 es la ventana actual, la última abierta o la elegida con
`window_use`. Un número que no es una ventana abierta no hace nada. Las ventanas que sigan abiertas se cierran
solas al acabar el programa.

**Los gadgets.** Botones, campos de texto, casillas, deslizadores, listas... son gadgets de GadTools. Cada
`*_create` recibe primero la ventana (el número de `window_create`, o 0 para la actual) y devuelve el número del
gadget, del 1 al 64, o 0 si no se pudo crear. Lo demás:

- `x`, `y` cuentan desde la esquina de dentro de los bordes, como los `gfx_*`.
- Con ancho o alto 0, Dash los mide con la fuente de la pantalla: el texto del botón, la opción más larga, diez
  letras en un campo.
- Una `_` en el texto subraya la letra siguiente, que hace de tecla: `"_Aceptar"` se pulsa también con la A.
- Al usarlos, el `EventLoop` recibe `On Gadget` y `gadget_id()` dice cuál fue.

**Medir para cualquier fuente.** La fuente de la pantalla puede ser de 8 puntos o de 13. `screen_font_height` y
`screen_font_text_width` miden con ella; con el flag 8 de `window_create` el tamaño es el del interior, así que no
hace falta contar los bordes.

**Programas más grandes.** Para muchas ventanas o ventanas que cambian de tamaño solas, MUI es más cómodo (ver el
grupo MUI). Los `gt_*` (GadTools) son de una sola ventana.

**Ejemplo** (`tests/test_doc_ventanas.dash`: se compila y se prueba en el emulador con los tests):

```dash
# Ventanas: una ventana declarada, sus gadgets y su bucle de eventos.

Window Prefs
    title "Preferencias"
    width 270
    height 130
end

Main
    Prefs.open
    alto = screen_font_height() + 6                # una fila de gadgets, con la fuente de la pantalla
    gfx_pen(1)
    gfx_text_at(8, 4 + alto - 5, "Nombre")         # la etiqueta del campo, en su fila
    nombre = textfield_create(0, 70, 4, 180, alto, 40)     # 0: la ventana actual
    sonido = checkbox_create(0, 70, alto + 8, "_Sonido")
    modo = cycle_create(0, 70, 2 * alto + 12, 0, alto, "NTSC|PAL")
    aceptar = button_create(0, 70, 3 * alto + 16, 0, alto, "_Aceptar")

    textfield_set(nombre, "Amiga")
    checkbox_set(sonido, true)
    cycle_set(modo, 1)
    modos = ["NTSC", "PAL"]

    EventLoop
        On Gadget
            if gadget_id() == aceptar
                Stop
            end
        end
        On Timer 1500                              # para la prueba: sin nadie que pulse, acaba sola
            Stop
        end
        On Close
            Stop
        end
    end
    Print "nombre: #{textfield_get(nombre)}, sonido: #{checkbox_get(sonido)}, modo: #{modos[cycle_get(modo)]}"
    Prefs.close
    Print "fin"
end
```

**Índice.** Las que tienen enlace están explicadas más abajo.

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| [`window_create(title, x, y, w, h, flags)`](#window_create) | Int | Abre una ventana; da su número 1..16 (0: no se pudo); flags: 1 se puede cambiar de tamaño, 2 sin bordes, 4 sin botón de cerrar, 8 w y h son el interior (sin los bordes). Pasa a ser la ventana actual |  |
| [`window_border_top()`](#window_border_top) | Int | El borde de arriba de la ventana actual (con la barra de título); los gadgets cuentan desde dentro, sin él |  |
| [`window_border_bottom()`](#window_border_bottom) | Int | El borde de abajo de la ventana actual |  |
| [`window_border_left()`](#window_border_left) | Int | El borde izquierdo de la ventana actual |  |
| [`window_border_right()`](#window_border_right) | Int | El borde derecho de la ventana actual |  |
| [`screen_font_height()`](#screen_font_height) | Int | El alto de la fuente de la pantalla (la del programa, o la del Workbench): la de las barras de título y la de los gadgets de GadTools |  |
| [`screen_font_text_width(text)`](#screen_font_text_width) | Int | El ancho de un texto con la fuente de la pantalla |  |
| [`window_close(handle)`](#window_close) | — | Cierra una ventana (número 0: la actual) |  |
| [`window_title(handle, title)`](#window_title) | — | Cambia el título de una ventana (número 0: la actual) |  |
| [`window_move(handle, x, y)`](#window_move) | — | Lleva una ventana a x, y (absolutas; número 0: la actual) |  |
| [`window_resize(handle, w, h)`](#window_resize) | — | Cambia el tamaño de una ventana a w x h (número 0: la actual) |  |
| [`window_to_front(handle)`](#window_to_front) | — | Pone una ventana delante (número 0: la actual) |  |
| [`window_to_back(handle)`](#window_to_back) | — | Pone una ventana detrás (número 0: la actual) |  |
| [`window_activate(handle)`](#window_activate) | — | Activa una ventana (número 0: la actual) |  |
| [`window_use(handle)`](#window_use) | Bool | Hace actual una ventana, en la que dibujan los gfx_: un número de window_create, o 0 la ventana declarada (Window X ... end) abierta la última; false si no está abierta |  |
| [`screen_to_front()`](#screen_to_front) | — | Pone delante la pantalla propia |  |
| [`screen_to_back()`](#screen_to_back) | — | Pone detrás la pantalla propia |  |
| [`gadget_id()`](#gadget_id) | Int | El número del último gadget usado (para el On Gadget del EventLoop) |  |
| [`gadget_width(gadget)`](#gadget_width) | Int | El ancho de un gadget en píxeles (también si se creó con ancho 0) |  |
| [`gadget_height(gadget)`](#gadget_height) | Int | El alto de un gadget en píxeles (también si se creó con alto 0) |  |
| [`button_create(win, x, y, w, h, label)`](#button_create) | Int | Crea un botón |  |
| [`button_enable(gad)`](#button_enable) | — | Activa un botón |  |
| [`button_disable(gad)`](#button_disable) | — | Desactiva un botón |  |
| [`textfield_create(win, x, y, w, h, maxlen)`](#textfield_create) | Int | Crea un campo de texto |  |
| [`textfield_get(gad)`](#textfield_get) | String | El texto de un campo de texto |  |
| [`textfield_set(gad, text)`](#textfield_set) | — | Cambia el texto de un campo de texto |  |
| [`checkbox_create(win, x, y, label)`](#checkbox_create) | Int | Crea una casilla |  |
| [`checkbox_get(gad)`](#checkbox_get) | Bool | Si la casilla está marcada |  |
| [`checkbox_set(gad, state)`](#checkbox_set) | — | Marca o desmarca una casilla |  |
| [`slider_create(win, x, y, w, h, min, max, value)`](#slider_create) | Int | Crea un deslizador |  |
| [`slider_get(gad)`](#slider_get) | Int | El valor de un deslizador |  |
| [`slider_set(gad, value)`](#slider_set) | — | Cambia el valor de un deslizador |  |
| [`listview_create(win, x, y, w, h)`](#listview_create) | Int | Crea una lista |  |
| [`listview_add(gad, text)`](#listview_add) | — | Añade una línea a una lista |  |
| [`listview_clear(gad)`](#listview_clear) | — | Vacía una lista |  |
| [`listview_selected(gad)`](#listview_selected) | Int | La línea elegida (-1 si ninguna) |  |
| [`cycle_create(win, x, y, w, h, options)`](#cycle_create) | Int | Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por \| (el valor es la opción, desde 0) |  |
| [`cycle_get(gad)`](#cycle_get) | Int | La opción elegida de un gadget de opciones |  |
| [`cycle_set(gad, index)`](#cycle_set) | — | Elige una opción de un gadget de opciones |  |
| [`radio_create(win, x, y, options)`](#radio_create) | Int | Crea botones de radio (uno por opción, separadas por \|) |  |
| [`radio_get(gad)`](#radio_get) | Int | El botón de radio elegido |  |
| [`radio_set(gad, index)`](#radio_set) | — | Elige un botón de radio |  |
| [`integer_create(win, x, y, w, h, value)`](#integer_create) | Int | Crea un campo de números enteros |  |
| [`integer_get(gad)`](#integer_get) | Int | El valor de un campo de números |  |
| [`integer_set(gad, value)`](#integer_set) | — | Cambia el valor de un campo de números |  |
| [`palette_create(win, x, y, w, h, depth)`](#palette_create) | Int | Crea un gadget de paleta de colores (2^depth colores) |  |
| [`palette_get(gad)`](#palette_get) | Int | El color elegido |  |
| [`palette_set(gad, color)`](#palette_set) | — | Elige un color |  |
| [`number_create(win, x, y, w, h, value)`](#number_create) | Int | Crea una caja que enseña un número |  |
| [`number_set(gad, value)`](#number_set) | — | Cambia el número que se enseña |  |
| [`dialog_file(title, pattern, save_mode)`](#dialog_file) | String | Diálogo de ficheros: la ruta entera del fichero elegido, "" si se canceló (save_mode true: diálogo de guardar) |  |
| [`dialog_file_at(title, pattern, save_mode, drawer, file)`](#dialog_file_at) | String | dialog_file abriéndose en ese cajón con ese nombre de fichero ("": como dialog_file) |  |
| [`dialog_color(title, initial)`](#dialog_color) | Int | Ventana con la paleta: da el color elegido (con un clic, o con las flechas + Return); Esc deja el inicial |  |
| [`dialog_screen_mode(title)`](#dialog_screen_mode) | Bool | Petición de modo de pantalla (modo, ancho, alto y profundidad), empezando en el del Workbench: cierto si se eligió uno; screen_mode_id, _width, _height y _depth lo dan |  |
| [`screen_mode_id()`](#screen_mode_id) | Int | El modo del último dialog_screen_mode (para screen_open_mode) |  |
| [`screen_mode_width()`](#screen_mode_width) | Int | El ancho elegido en el último dialog_screen_mode |  |
| [`screen_mode_height()`](#screen_mode_height) | Int | El alto elegido en el último dialog_screen_mode |  |
| [`screen_mode_depth()`](#screen_mode_depth) | Int | La profundidad (planos) elegida en el último dialog_screen_mode |  |
| [`dialog_font(title)`](#dialog_font) | String | Diálogo de fuentes: "nombre.font/tamaño", "" si se canceló |  |

<a id="window_create"></a>

### `window_create(title, x, y, w, h, flags)` → `Int`

- `title`: el título. Con `""`, sin flag 1 y con los flags 2 y 4, la ventana no tiene barra de título.
- `x`, `y`: la posición en la pantalla.
- `w`, `h`: el tamaño, 40 x 20 como poco.
- `flags`: se suman. 1 = se puede cambiar de tamaño; 2 = sin bordes; 4 = sin botón de cerrar; 8 = `w` y `h` son
  el interior, sin los bordes; 16 = el botón derecho va al programa (`On RightClick`) en vez de a los menús.

Abre la ventana en la pantalla del programa, si se abrió una, o en el Workbench. Devuelve su número (1 a 16) y la
hace la ventana actual: los `gfx_*` dibujan en ella. Devuelve 0 si no se pudo abrir o si ya hay 16.

Ver también: [`window_close`](#window_close), [`window_use`](#window_use), [`screen_font_height`](#screen_font_height), [`event_window`](#event_window).

<a id="window_border_top"></a>

### `window_border_top()` → `Int`

Devuelve el grosor del borde de arriba de la ventana actual, con la barra de título, en píxeles; 0 sin ventana.
Depende de la fuente de la pantalla. Hace falta para calcular el tamaño de fuera de una ventana; con el flag 8 de
`window_create` no.

Ver también: [`window_border_bottom`](#window_border_bottom), [`window_border_left`](#window_border_left), [`window_border_right`](#window_border_right), [`window_create`](#window_create).

<a id="window_border_bottom"></a>

### `window_border_bottom()` → `Int`

Devuelve el grosor del borde de abajo de la ventana actual, en píxeles; 0 sin ventana.

Ver también: [`window_border_top`](#window_border_top).

<a id="window_border_left"></a>

### `window_border_left()` → `Int`

Devuelve el grosor del borde izquierdo de la ventana actual, en píxeles; 0 sin ventana.

Ver también: [`window_border_top`](#window_border_top).

<a id="window_border_right"></a>

### `window_border_right()` → `Int`

Devuelve el grosor del borde derecho de la ventana actual, en píxeles; 0 sin ventana.

Ver también: [`window_border_top`](#window_border_top).

<a id="screen_font_height"></a>

### `screen_font_height()` → `Int`

Devuelve el alto en píxeles de la fuente de la pantalla: la del programa, la de la ventana actual o, sin ninguna,
la del Workbench. Es la fuente de las barras de título y de los gadgets. Una fila de gadgets cómoda mide
`screen_font_height() + 6`.

Ver también: [`screen_font_text_width`](#screen_font_text_width), [`window_create`](#window_create).

<a id="screen_font_text_width"></a>

### `screen_font_text_width(text)` → `Int`

- `text`: el texto.

Devuelve cuántos píxeles de ancho ocupa el texto con la fuente de la pantalla. Sirve para dar a una ventana o a
una columna de etiquetas el ancho justo.

Ver también: [`screen_font_height`](#screen_font_height), [`gfx_text_len`](#gfx_text_len).

<a id="window_close"></a>

### `window_close(handle)`

- `handle`: el número de la ventana; 0, la actual.

Cierra la ventana. Si era la actual, no queda ventana actual: antes de dibujar otra vez, `window_use`. Sus gadgets
dejan de dibujarse. Cerrar una que ya está cerrada no hace nada.

Ver también: [`window_create`](#window_create), [`window_use`](#window_use), [`close_window`](#close_window).

<a id="window_title"></a>

### `window_title(handle, title)`

- `handle`: el número de la ventana; 0, la actual.
- `title`: el título nuevo.

Cambia el texto de la barra de título. Para enseñar un estado: el nombre del fichero, un `*` si hay cambios.

Ver también: [`window_create`](#window_create).

<a id="window_move"></a>

### `window_move(handle, x, y)`

- `handle`: el número de la ventana; 0, la actual.
- `x`, `y`: la posición nueva en la pantalla (no un desplazamiento).

Lleva la ventana a ese sitio. Intuition lo hace un momento después, no al volver de la llamada. Un
`window_resize` justo después cuenta ya con la posición nueva.

Ver también: [`window_resize`](#window_resize), [`window_create`](#window_create).

<a id="window_resize"></a>

### `window_resize(handle, w, h)`

- `handle`: el número de la ventana; 0, la actual.
- `w`, `h`: el tamaño nuevo, de fuera (con los bordes).

Cambia el tamaño de la ventana. Como `window_move`, Intuition lo hace un momento después.

Ver también: [`window_move`](#window_move), [`window_border_top`](#window_border_top).

<a id="window_to_front"></a>

### `window_to_front(handle)`

- `handle`: el número de la ventana; 0, la actual.

Pone la ventana delante de las demás de su pantalla.

Ver también: [`window_to_back`](#window_to_back), [`window_activate`](#window_activate).

<a id="window_to_back"></a>

### `window_to_back(handle)`

- `handle`: el número de la ventana; 0, la actual.

Pone la ventana detrás de las demás de su pantalla.

Ver también: [`window_to_front`](#window_to_front).

<a id="window_activate"></a>

### `window_activate(handle)`

- `handle`: el número de la ventana; 0, la actual.

La hace la ventana activa, la que recibe el teclado. No la pone delante: para eso, `window_to_front`.

Ver también: [`window_to_front`](#window_to_front).

<a id="window_use"></a>

### `window_use(handle)` → `Bool`

- `handle`: el número de una ventana de `window_create`, o 0 para la ventana declarada (`Window X ... end`) abierta
  la última.

La hace la ventana actual: los `gfx_*` dibujan en ella y el número 0 de las demás funciones es ella. Devuelve
`false` si esa ventana no está abierta, y entonces no cambia nada.

Ver también: [`window_create`](#window_create), [`gfx_pen`](#gfx_pen).

<a id="screen_to_front"></a>

### `screen_to_front()`

Pone delante la pantalla del programa (la de `screen_open`). Sin pantalla propia no hace nada.

Ver también: [`screen_to_back`](#screen_to_back), [`screen_open`](#screen_open).

<a id="screen_to_back"></a>

### `screen_to_back()`

Pone detrás la pantalla del programa, y se ve la de debajo (el Workbench). Sin pantalla propia no hace nada.

Ver también: [`screen_to_front`](#screen_to_front).

<a id="gadget_id"></a>

### `gadget_id()` → `Int`

Devuelve el número del último gadget usado. Se mira en el `On Gadget` del `EventLoop` y se compara con lo que
devolvió su `*_create`.

Ver también: [`button_create`](#button_create), [`event_window`](#event_window).

<a id="gadget_width"></a>

### `gadget_width(gadget)` → `Int`

- `gadget`: el número del gadget.

Devuelve su ancho en píxeles, también cuando se creó con ancho 0 y lo midió Dash. 0 si no es un gadget.

Ver también: [`gadget_height`](#gadget_height).

<a id="gadget_height"></a>

### `gadget_height(gadget)` → `Int`

- `gadget`: el número del gadget.

Devuelve su alto en píxeles, también cuando se creó con alto 0. 0 si no es un gadget.

Ver también: [`gadget_width`](#gadget_width).

<a id="button_create"></a>

### `button_create(win, x, y, w, h, label)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`: la esquina de arriba a la izquierda.
- `w`, `h`: el tamaño; 0 lo mide Dash con el texto.
- `label`: el texto; una `_` subraya la letra que lo pulsa con el teclado.

Crea un botón. Al pulsarlo llega `On Gadget` con `gadget_id()` igual al número que devuelve. Devuelve 0 si no se
pudo crear.

Ver también: [`button_disable`](#button_disable), [`gadget_id`](#gadget_id).

<a id="button_enable"></a>

### `button_enable(gad)`

- `gad`: el número del gadget.

Vuelve a dejar usar un gadget desactivado. Vale para cualquier gadget, no solo botones.

Ver también: [`button_disable`](#button_disable).

<a id="button_disable"></a>

### `button_disable(gad)`

- `gad`: el número del gadget.

Desactiva el gadget: se ve en gris y no responde al ratón ni a su tecla. Vale para cualquier gadget.

Ver también: [`button_enable`](#button_enable).

<a id="textfield_create"></a>

### `textfield_create(win, x, y, w, h, maxlen)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño; 0 lo mide Dash (diez letras de ancho).
- `maxlen`: cuántas letras caben como mucho; 0 = 64.

Crea un campo de texto. Lleva las teclas de edición del sistema y las de copiar y pegar. `On Gadget` llega al
pulsar Return o Tab.

Ver también: [`textfield_get`](#textfield_get), [`textfield_set`](#textfield_set), [`integer_create`](#integer_create).

<a id="textfield_get"></a>

### `textfield_get(gad)` → `String`

- `gad`: el número del campo.

Devuelve lo que hay escrito, también si aún no se pulsó Return. `""` si no es un campo.

Ver también: [`textfield_set`](#textfield_set).

<a id="textfield_set"></a>

### `textfield_set(gad, text)`

- `gad`: el número del campo.
- `text`: el texto nuevo.

Cambia lo que enseña el campo.

Ver también: [`textfield_get`](#textfield_get).

<a id="checkbox_create"></a>

### `checkbox_create(win, x, y, label)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`: dónde va la casilla; el texto va a su derecha.
- `label`: el texto; una `_` subraya su tecla.

Crea una casilla sin marcar. Cada clic, o su tecla, la marca o la desmarca y manda `On Gadget`.

Ver también: [`checkbox_get`](#checkbox_get), [`checkbox_set`](#checkbox_set).

<a id="checkbox_get"></a>

### `checkbox_get(gad)` → `Bool`

- `gad`: el número de la casilla.

Devuelve `true` si está marcada.

Ver también: [`checkbox_set`](#checkbox_set).

<a id="checkbox_set"></a>

### `checkbox_set(gad, state)`

- `gad`: el número de la casilla.
- `state`: `true` la marca, `false` la desmarca.

No manda `On Gadget`.

Ver también: [`checkbox_get`](#checkbox_get).

<a id="slider_create"></a>

### `slider_create(win, x, y, w, h, min, max, value)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño. Más ancho que alto es horizontal.
- `min`, `max`: el valor del principio y el del final.
- `value`: el valor con el que empieza; si se sale, se queda en `min` o `max`.

Crea un deslizador. Manda `On Gadget` mientras se arrastra, no solo al soltarlo.

Ver también: [`slider_get`](#slider_get), [`slider_set`](#slider_set).

<a id="slider_get"></a>

### `slider_get(gad)` → `Int`

- `gad`: el número del deslizador.

Devuelve su valor, entre `min` y `max`.

Ver también: [`slider_set`](#slider_set).

<a id="slider_set"></a>

### `slider_set(gad, value)`

- `gad`: el número del deslizador.
- `value`: el valor nuevo.

Mueve el deslizador. No manda `On Gadget`.

Ver también: [`slider_get`](#slider_get).

<a id="listview_create"></a>

### `listview_create(win, x, y, w, h)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.

Crea una lista vacía con su barra para desplazarla. Las líneas se añaden con `listview_add`. Al elegir una llega
`On Gadget`.

Ver también: [`listview_add`](#listview_add), [`listview_selected`](#listview_selected), [`listview_clear`](#listview_clear).

<a id="listview_add"></a>

### `listview_add(gad, text)`

- `gad`: el número de la lista.
- `text`: la línea.

Añade una línea al final. La lista guarda su propia copia del texto.

Ver también: [`listview_clear`](#listview_clear).

<a id="listview_clear"></a>

### `listview_clear(gad)`

- `gad`: el número de la lista.

Quita todas las líneas y deja la lista sin ninguna elegida.

Ver también: [`listview_add`](#listview_add).

<a id="listview_selected"></a>

### `listview_selected(gad)` → `Int`

- `gad`: el número de la lista.

Devuelve la línea elegida, contando desde 0, o -1 si no hay ninguna.

Ver también: [`listview_create`](#listview_create).

<a id="cycle_create"></a>

### `cycle_create(win, x, y, w, h, options)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño; 0 lo mide Dash con la opción más larga.
- `options`: las opciones separadas por `|`: `"Baja|Media|Alta"`.

Crea un gadget que enseña una opción y pasa a la siguiente con cada clic. Empieza en la primera, la 0. Manda
`On Gadget` al cambiar.

Ver también: [`cycle_get`](#cycle_get), [`cycle_set`](#cycle_set), [`radio_create`](#radio_create).

<a id="cycle_get"></a>

### `cycle_get(gad)` → `Int`

- `gad`: el número del gadget.

Devuelve la opción elegida, desde 0. -1 si no es un gadget de opciones.

Ver también: [`cycle_set`](#cycle_set).

<a id="cycle_set"></a>

### `cycle_set(gad, index)`

- `gad`: el número del gadget.
- `index`: la opción, desde 0.

Elige esa opción. No manda `On Gadget`.

Ver también: [`cycle_get`](#cycle_get).

<a id="radio_create"></a>

### `radio_create(win, x, y, options)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`: dónde va el primer botón; los demás van debajo, con su texto a la derecha.
- `options`: las opciones separadas por `|`.

Crea un grupo de botones de radio, de los que solo uno está elegido. Empieza en el primero, el 0. Manda
`On Gadget` al cambiar.

Ver también: [`radio_get`](#radio_get), [`radio_set`](#radio_set), [`cycle_create`](#cycle_create).

<a id="radio_get"></a>

### `radio_get(gad)` → `Int`

- `gad`: el número del grupo.

Devuelve el botón elegido, desde 0. -1 si no es un grupo de radio.

Ver también: [`radio_set`](#radio_set).

<a id="radio_set"></a>

### `radio_set(gad, index)`

- `gad`: el número del grupo.
- `index`: el botón, desde 0.

Elige ese botón. No manda `On Gadget`.

Ver también: [`radio_get`](#radio_get).

<a id="integer_create"></a>

### `integer_create(win, x, y, w, h, value)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `value`: el número con el que empieza.

Crea un campo que solo admite números enteros, de hasta 10 cifras. `On Gadget` llega al pulsar Return o Tab.

Ver también: [`integer_get`](#integer_get), [`integer_set`](#integer_set), [`textfield_create`](#textfield_create).

<a id="integer_get"></a>

### `integer_get(gad)` → `Int`

- `gad`: el número del campo.

Devuelve el número escrito, también si aún no se pulsó Return. -1 si no es un campo de números.

Ver también: [`integer_set`](#integer_set).

<a id="integer_set"></a>

### `integer_set(gad, value)`

- `gad`: el número del campo.
- `value`: el número nuevo.

Cambia el número que enseña.

Ver también: [`integer_get`](#integer_get).

<a id="palette_create"></a>

### `palette_create(win, x, y, w, h, depth)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `depth`: cuántos colores enseña: 2 elevado a `depth` (3 = 8 colores); 0 = 4 colores.

Crea un gadget con los colores de la pantalla para elegir uno. Empieza en el color 1. Manda `On Gadget` al elegir.

Ver también: [`palette_get`](#palette_get), [`palette_set`](#palette_set), [`dialog_color`](#dialog_color).

<a id="palette_get"></a>

### `palette_get(gad)` → `Int`

- `gad`: el número del gadget.

Devuelve el color elegido. -1 si no es un gadget de paleta.

Ver también: [`palette_set`](#palette_set).

<a id="palette_set"></a>

### `palette_set(gad, color)`

- `gad`: el número del gadget.
- `color`: el color.

Elige ese color. No manda `On Gadget`.

Ver también: [`palette_get`](#palette_get).

<a id="number_create"></a>

### `number_create(win, x, y, w, h, value)` → `Int`

- `win`: la ventana; 0, la actual.
- `x`, `y`, `w`, `h`: posición y tamaño.
- `value`: el número que enseña.

Crea una caja con borde que enseña un número y no se puede editar. Para un contador o un resultado.

Ver también: [`number_set`](#number_set).

<a id="number_set"></a>

### `number_set(gad, value)`

- `gad`: el número del gadget.
- `value`: el número nuevo.

Cambia el número que enseña.

Ver también: [`number_create`](#number_create).

<a id="dialog_file"></a>

### `dialog_file(title, pattern, save_mode)` → `String`

- `title`: el título de la petición.
- `pattern`: qué ficheros se ven, con los comodines de AmigaDOS: `"#?.dash"`; `""` = todos.
- `save_mode`: `true` para guardar (se puede escribir un nombre nuevo), `false` para abrir.

Abre la petición de ficheros del sistema (ASL) y espera. Devuelve la ruta entera del fichero elegido, o `""` si se
canceló. La siguiente vez se abre en el cajón de la última.

Ver también: [`dialog_file_at`](#dialog_file_at), `file_open_dialog`.

<a id="dialog_file_at"></a>

### `dialog_file_at(title, pattern, save_mode, drawer, file)` → `String`

- `title`, `pattern`, `save_mode`: como en `dialog_file`.
- `drawer`: el cajón donde se abre; `""` = el de la última vez.
- `file`: el nombre que sale escrito; `""` = ninguno.

Como `dialog_file`, empezando en ese cajón y con ese nombre. Para "Guardar como..." con el nombre del fichero
abierto.

Ver también: [`dialog_file`](#dialog_file).

<a id="dialog_color"></a>

### `dialog_color(title, initial)` → `Int`

- `title`: el título de la ventana.
- `initial`: el color que sale elegido.

Abre una ventana con los colores de la pantalla y espera. Se elige con un clic, o con las flechas y Return.
Devuelve el color elegido; con Esc o el botón de cerrar, `initial`.

Ver también: [`palette_create`](#palette_create).

<a id="dialog_screen_mode"></a>

### `dialog_screen_mode(title)` → `Bool`

- `title`: el título de la petición.

Abre la petición de modo de pantalla del sistema, empezando en el del Workbench, y espera. Devuelve `true` si se
eligió uno: entonces `screen_mode_id`, `screen_mode_width`, `screen_mode_height` y `screen_mode_depth` lo dan, para
`screen_open_mode`. `false` si se canceló.

Ver también: [`screen_mode_id`](#screen_mode_id), [`screen_open_mode`](#screen_open_mode).

<a id="screen_mode_id"></a>

### `screen_mode_id()` → `Int`

Devuelve el modo elegido en el último `dialog_screen_mode`, el número que pide `screen_open_mode`.

Ver también: [`dialog_screen_mode`](#dialog_screen_mode), [`screen_open_mode`](#screen_open_mode).

<a id="screen_mode_width"></a>

### `screen_mode_width()` → `Int`

Devuelve el ancho elegido en el último `dialog_screen_mode`.

Ver también: [`dialog_screen_mode`](#dialog_screen_mode).

<a id="screen_mode_height"></a>

### `screen_mode_height()` → `Int`

Devuelve el alto elegido en el último `dialog_screen_mode`.

Ver también: [`dialog_screen_mode`](#dialog_screen_mode).

<a id="screen_mode_depth"></a>

### `screen_mode_depth()` → `Int`

Devuelve la profundidad elegida en el último `dialog_screen_mode`: 3 son 8 colores, 8 son 256.

Ver también: [`dialog_screen_mode`](#dialog_screen_mode).

<a id="dialog_font"></a>

### `dialog_font(title)` → `String`

- `title`: el título de la petición.

Abre la petición de fuentes del sistema y espera. Devuelve la fuente elegida como `"nombre.font/tamaño"`
(`"topaz.font/8"`), o `""` si se canceló. Para abrirla, el nombre y el tamaño van por separado en `font_open`.

Ver también: `font_open`.

## RTG (CyberGraphX / Picasso96)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `rtg_available()` | Bool | Mira si hay CyberGraphX o Picasso96 |  |
| `rtg_is_active()` | Bool | Mira si la pantalla actual es RTG |  |
| `rtg_get_depth()` | Int | La profundidad en bits de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_get_width()` | Int | El ancho de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_get_height()` | Int | El alto de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_alloc_bitmap(width, height, depth)` | Int (dirección) | Pide un bitmap que vale para RTG |  |
| `rtg_free_bitmap(bitmap)` | — | Libera un bitmap RTG |  |
| `rtg_write_pixel(x, y, rgb)` | — | Escribe un píxel con un color RGB de 24 bits |  |
| `rtg_read_pixel(x, y)` | Int | Lee un píxel: su color RGB de 24 bits |  |
| `rtg_fill_rect(x, y, w, h, rgb)` | — | Rellena un rectángulo con un color RGB de 24 bits |  |
| `rtg_write_array(buffer, bpr, x, y, w, h)` | — | Escribe un bloque de píxeles (el búfer es ARGB de 32 bits; bpr, los bytes por fila) |  |
| `rtg_read_array(buffer, bpr, x, y, w, h)` | — | Lee un bloque de píxeles de la pantalla a un búfer |  |
| `rtg_rgb(r, g, b)` | Int | Un color RGB de 24 bits a partir de sus componentes |  |
| `rtg_argb(a, r, g, b)` | Int | Un color ARGB de 32 bits a partir de sus componentes |  |
| `rtg_rgb_r(color)` | Int | El componente rojo de un color RGB |  |
| `rtg_rgb_g(color)` | Int | El componente verde de un color RGB |  |
| `rtg_rgb_b(color)` | Int | El componente azul de un color RGB |  |
| `rtg_best_mode(width, height, depth)` | Int | El mejor modo de pantalla RTG para ese tamaño |  |
| `rtg_open_screen(width, height, depth, title)` | Bool | Abre una pantalla RTG del tamaño que se diga |  |
| `rtg_blit(src, sx, sy, dx, dy, w, h)` | — | Copia de un bitmap a la pantalla |  |
| `rtg_scale_blit(src, sx, sy, sw, sh, dx, dy, dw, dh)` | — | Copia de un bitmap a la pantalla cambiando el tamaño |  |

## MUI

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `mui_app_begin(title, base)` | Int (dirección) | Abre muimaster.library y crea la aplicación MUI (base: el nombre ARexx); 0 si no hay MUI o la CPU es un 68000 |  |
| `mui_text_editor(lines)` | Int (dirección) | Un campo de texto de varias líneas (el Textinput de MUI), de ese número de líneas de alto, con su barra: Return empieza otra línea; mui_get_text y mui_set_text lo leen y lo cambian, mui_on_ack da el evento de mandarlo (Amiga+Return en su ventana) |  |
| `mui_window_open_back(win)` | Int | Abre una ventana sin hacerla la activa: el teclado se queda donde estaba; falso si no pudo abrirse |  |
| `mui_window_activate(win)` | — | Hace activa una ventana, delante de las demás (si está cerrada, la abre) |  |
| `mui_window_dispose(window)` | — | Cierra una ventana, la quita de la aplicación y la libera con todos sus objetos (y los menús contextuales hechos tras ella): para ventanas que se hacen una y otra vez (una vista previa). Nada con 0 o con una ventana que ya no está; sus objetos no se pueden usar después |  |
| `mui_request(window, title, text, buttons)` | Int | Pregunta con la petición de MUI sobre una ventana (0: sobre la aplicación), con sus botones separados por "\|" ("_Guardar\|_Descartar\|_Cancelar"); las ventanas de la aplicación esperan. El botón elegido: 1, 2... desde la izquierda, 0 el último (también Esc) |  |
| `mui_set_background(obj, r, g, b)` | — | Un fondo RGB (0-255 cada uno) para un objeto: un grupo, un texto, una etiqueta, un botón, una lista (y la lista de dentro) o una ventana (su grupo raíz); los objetos de dentro lo toman si no tienen el suyo |  |
| `mui_set_text_pen(obj, r, g, b)` | — | El color (RGB, 0-255 cada uno) del texto de un texto, una etiqueta o un botón; mui_set_text lo mantiene |  |
| `mui_app_field_colors(r, g, b, active_r, active_g, active_b, cursor_r, cursor_g, cursor_b)` | — | El fondo (RGB, 0-255 cada uno) de todos los campos de texto de la aplicación (string, text_editor, combo), sin el cursor y con él, y el color del cursor; lo toman las ventanas que se abran después. El texto sigue negro: un gris en el que aún se lea, como 96, 96, 104 y 120, 120, 128 |  |
| `mui_app_rexx(app, func)` | — | Cada orden ARexx al puerto de la aplicación (su base y ".1": "BASE.1") que MUI no contesta por sí mismo (QUIT, SHOW, HIDE, INFO...) llama a f(orden: String) -> String con la línea entera: lo que devuelve es el RESULT, y mui_rexx_fail durante la llamada pone el RC. Se ejecuta mientras mui_wait_event espera |  |
| `mui_rexx_fail(rc)` | — | Desde la función de mui_app_rexx: el RC de la orden (5 aviso, 10 error, 20 fallo; entonces sin RESULT) |  |
| `mui_app_end()` | — | Deshace la aplicación con sus ventanas y objetos, y cierra MUI (también al acabar) |  |
| `mui_window_begin(title, id)` | Int (dirección) | Empieza una ventana (id 1-255: MUI recuerda su tamaño y su sitio; 0 ninguno) con un grupo raíz vertical |  |
| `mui_window_end()` | — | Acaba la ventana empezada con mui_window_begin |  |
| `mui_window_open(win)` | Int | Abre una ventana; false si no se pudo |  |
| `mui_window_close(win)` | — | Cierra una ventana (sigue existiendo) |  |
| `mui_window_active(win)` | Int | 1 si la ventana es la activa (varias ventanas de un .dashui comparten números de evento; dashweb D32) |  |
| `mui_vgroup_begin()` | Int (dirección) | Empieza un grupo vertical dentro del grupo abierto |  |
| `mui_hgroup_begin()` | Int (dirección) | Empieza un grupo horizontal dentro del grupo abierto |  |
| `mui_group_end()` | — | Acaba el grupo abierto |  |
| `mui_text(text)` | Int (dirección) | Un texto (con los códigos de texto de MUI) |  |
| `mui_button(label)` | Int (dirección) | Un botón (un guion bajo delante de una letra la hace su atajo de teclado) |  |
| `mui_on_press(obj, id)` | — | mui_wait_event da id cuando se pulsa el botón |  |
| `mui_on_close(win, id)` | — | mui_wait_event da id cuando se pulsa el botón de cerrar de la ventana (en la primera ventana, por defecto: -1) |  |
| `mui_on_drop(obj, id)` | — | mui_wait_event devuelve id cuando se sueltan iconos del Workbench sobre ese objeto (una ventana: en cualquier sitio de ella); app_drop da sus rutas y app_drop_x/y dónde cayeron |  |
| `mui_press(obj)` | — | Envía el evento mui_on_press de un botón como si se hubiera pulsado |  |
| `mui_label(text)` | Int (dirección) | La etiqueta de una fila de un formulario (alineada a la derecha) |  |
| `mui_string(initial, maxlen)` | Int (dirección) | Un campo de texto de hasta maxlen caracteres |  |
| `mui_checkbox(checked)` | Int (dirección) | Una casilla |  |
| `mui_cycle(options)` | Int (dirección) | Un gadget de opciones que cambian al pulsarlo; opciones separadas por \| ("Uno\|Dos\|Tres") |  |
| `mui_slider(min, max, value)` | Int (dirección) | Un deslizador horizontal |  |
| `mui_gauge(max)` | Int (dirección) | Una barra de progreso de 0 a max |  |
| `mui_get_value(obj)` | Int | El valor: casilla 1/0, opción elegida, nivel del deslizador, progreso, marca de menú 1/0 |  |
| `mui_set_value(obj, value)` | — | Cambia el valor (dispara mui_on_change como lo haría el usuario) |  |
| `mui_get_text(obj)` | String | El texto de un campo de texto, un texto, un botón o el título de una ventana |  |
| `mui_set_text(obj, text)` | — | Cambia el texto de un campo de texto, un texto, un botón, una opción de menú o el título de una ventana |  |
| `mui_set_enabled(obj, enabled)` | — | Activa o desactiva (en gris) un objeto, una opción de menú o un menú entero |  |
| `mui_on_change(obj, id)` | — | mui_wait_event da id cuando cambia el valor o el texto |  |
| `mui_on_ack(obj, id)` | — | mui_wait_event da id cuando se pulsa Return en un campo de texto (en un mui_combo, también al elegir una línea) |  |
| `mui_list()` | Int (dirección) | Una lista de textos con barra de desplazamiento; su valor es la línea elegida (-1 ninguna) |  |
| `mui_list_add(list, text)` | — | Añade una línea al final |  |
| `mui_list_insert(list, pos, text)` | — | Mete una línea en pos (0 = la primera) |  |
| `mui_list_remove(list, pos)` | — | Quita la línea de pos |  |
| `mui_list_clear(list)` | — | Quita todas las líneas |  |
| `mui_list_count(list)` | Int | Cuántas líneas hay |  |
| `mui_list_get(list, pos)` | String | El texto de la línea de pos ("" fuera de la lista) |  |
| `mui_list_quiet(list, quiet)` | — | Mientras está callada, la lista no se redibuja (para añadir muchas líneas) |  |
| `mui_on_double(list, id)` | — | mui_wait_event da id con un doble clic en la lista |  |
| `mui_frame_begin(title, horizontal)` | Int (dirección) | Empieza un grupo con marco y un título ("" = ninguno) |  |
| `mui_columns_begin(columns)` | Int (dirección) | Empieza un grupo en rejilla con tantas columnas (formularios: etiqueta, campo...) |  |
| `mui_register_begin(titles)` | Int (dirección) | Empieza unas pestañas ("Una\|Dos"); cada hijo es una página; valor = la página que se ve |  |
| `mui_scroll_begin()` | Int (dirección) | Empieza una zona con barras de desplazamiento (contenido más grande que la ventana) |  |
| `mui_space()` | Int (dirección) | Un espacio vacío que ocupa lo que sobra |  |
| `mui_balance()` | Int (dirección) | Una barra que el usuario arrastra para repartir el sitio entre sus vecinos |  |
| `mui_weight(obj, weight)` | — | La parte del espacio libre que se lleva un objeto (100 por defecto) |  |
| `mui_set_visible(obj, visible)` | — | Enseña u oculta un objeto (la ventana se recoloca) |  |
| `mui_menu_begin(title)` | Int (dirección) | Empieza un menú de la ventana que se está haciendo |  |
| `mui_menu_item(title, key, id)` | Int (dirección) | Una opción de menú: key = la letra de Amiga+tecla ("" ninguna); mui_wait_event da id |  |
| `mui_menu_check(title, key, id, checked)` | Int (dirección) | Una opción de menú con marca: elegirla cambia la marca y mui_wait_event da id; mui_get_value / mui_set_value leen y ponen la marca |  |
| `mui_submenu_begin(title)` | Int (dirección) | Empieza un submenú en el menú que se está haciendo (un nivel): sus opciones van dentro hasta mui_submenu_end |  |
| `mui_submenu_end()` | — | Acaba el submenú |  |
| `mui_menu_separator()` | — | Una raya de separación en el menú |  |
| `mui_context_menu_begin(title)` | Int (dirección) | Empieza un menú contextual (en cualquier sitio, no solo en una ventana): sus opciones como en un menú (mui_menu_item, mui_menu_check, mui_submenu_begin...) hasta mui_menu_end; se da a un objeto con mui_set_context_menu (Lorraine D15) |  |
| `mui_set_context_menu(object, menu)` | — | El botón derecho sobre el objeto abre ese menú contextual (0: ninguno); sus opciones dan sus eventos; en un lienzo, mui_canvas_mouse_x/_y dicen dónde se pulsó y mui_canvas_button es 2 |  |
| `mui_menu_end()` | — | Acaba el menú |  |
| `mui_canvas(min_width, min_height)` | Int (dirección) | Una zona de dibujo (crece con la ventana); se dibuja desde mui_canvas_on_draw |  |
| `mui_canvas_on_draw(canvas, func)` | — | La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (MUI la llama cuando hace falta) |  |
| `mui_canvas_on_input(canvas, id)` | — | mui_wait_event da id con un clic, la rueda o una tecla sobre la zona (llamarla antes de abrir la ventana) |  |
| `mui_canvas_redraw(canvas)` | — | Dibuja otra vez la zona ya |  |
| `mui_canvas_buffered(canvas, on)` | — | Dibuja la zona en un bitmap propio y la enseña de golpe al acabar (sin zona a medio dibujar; las mismas coordenadas; mui_canvas_update sigue dibujando en la ventana) |  |
| `mui_canvas_update(canvas)` | — | Llama ya a la función de dibujo sin borrar la zona (pinta solo lo que cambió) |  |
| `mui_canvas_update_area(canvas, x, y, w, h)` | — | Como mui_canvas_update, solo en la parte w x h en x, y de la zona (desde su esquina): el dibujo se recorta a ella y, con mui_canvas_buffered, solo ella pasa del búfer a la ventana |  |
| `mui_canvas_updating()` | Bool | En la función de dibujo: true si corre por un mui_canvas_update (lo demás sigue ahí) |  |
| `mui_canvas_on_move(canvas, id)` | — | mui_wait_event da id cuando el puntero se mueve sobre la zona o sale de ella, sin clic (los movimientos que lleguen entretanto hacen uno; llamarla antes de abrir la ventana) |  |
| `mui_canvas_pointer_x(canvas)` | Int | La X del puntero ahora, desde el borde izquierdo de la zona (con clic o sin él) |  |
| `mui_canvas_pointer_y(canvas)` | Int | La Y del puntero ahora, desde el borde de arriba de la zona (con clic o sin él) |  |
| `mui_canvas_pointer_inside(canvas)` | Bool | True si el puntero está ahora sobre la zona |  |
| `mui_canvas_set_pointer(canvas, shape)` | — | La forma del puntero sobre la zona: 0 normal, 1 texto (I), 2 cambiar de tamaño a los lados, 3 arriba y abajo, 4 ocupado; cambia ya si el puntero está sobre la zona (o arrastrándola) y vuelve a la normal fuera de ella (Lorraine D16) |  |
| `mui_canvas_take_tab(canvas, on)` | — | Con el puntero sobre la zona, Tab y Mayúsculas+Tab son teclas para ella (mui_canvas_key 66, Mayúsculas en mui_canvas_qualifiers; necesita mui_canvas_on_input) y no el gadget siguiente y anterior de la ventana; fuera de ella pasan de gadget en gadget como siempre (Lorraine D48) |  |
| `mui_canvas_mouse_x(canvas)` | Int | La X del último clic o de la rueda, desde el borde izquierdo de la zona |  |
| `mui_canvas_mouse_y(canvas)` | Int | La Y del último clic o de la rueda, desde el borde de arriba de la zona |  |
| `mui_canvas_button(canvas)` | Int | 1 si lo último fue un clic izquierdo; si no, 0 |  |
| `mui_canvas_wheel(canvas)` | Int | +1 / -1 si lo último fue la rueda del ratón (arriba/abajo); si no, 0 |  |
| `mui_canvas_key(canvas)` | Int | El código en bruto de la última tecla; -1 si lo último no fue una tecla |  |
| `mui_canvas_on_drag(canvas, id)` | — | El id del evento cuando se arrastra la zona (moverse con el botón izquierdo pulsado tras pulsarlo en ella) y cuando se suelta; mui_canvas_drag dice cuál, mui_canvas_mouse_x/y dónde (puede ser fuera de la zona). Llamarla antes de abrir la ventana |  |
| `mui_canvas_drag(canvas)` | Int | El último evento de arrastre: 1 moviéndose con el botón pulsado, 2 soltado (0 antes de ninguno) |  |
| `mui_canvas_qualifiers(canvas)` | Int | Las teclas pulsadas en la última tecla, clic o rueda: 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 Amiga, sumadas (Mayúsculas + Ctrl = 3); q & 1 dice si había Mayúsculas |  |
| `mui_canvas_char(canvas)` | String | El carácter de la última tecla en la zona, con las mayúsculas y el mapa de teclado ("" si no hay; dashweb D31) |  |
| `mui_scrollbar(vertical)` | Int (dirección) | Una barra de desplazamiento; su valor es la primera línea que se ve |  |
| `mui_set_range(scrollbar, total, visible)` | — | El tamaño del documento y de la parte que cabe |  |
| `mui_wait_event_signals(mask)` | Int | Como mui_wait_event, pero también da 0 cuando llega una de las señales de mask (sockets...); mui_signals dice cuál |  |
| `mui_signals()` | Int | Las señales de la máscara que despertaron al último mui_wait_event_signals |  |
| `mui_timer(ms, id)` | — | Dentro de ms milisegundos mui_wait_event da id, una vez (otra: llamarla otra vez; 0 la cancela) |  |
| `mui_image(file)` | Int (dirección) | Una imagen de un fichero con los datatypes (ILBM; PNG, JPEG, GIF si están sus datatypes); mui_set_text cambia el fichero |  |
| `mui_image_button(file)` | Int (dirección) | Un botón con una imagen (un icono de barra de herramientas; ILBM, o lo que lean los datatypes): mui_on_press como un botón, mui_set_text cambia la imagen |  |
| `mui_image_toggle(file, group, selected)` | Int (dirección) | Un botón con imagen que se queda pulsado (negrita, cursiva): valor 1/0 con mui_get_value / mui_set_value, mui_on_change cuando cambia; group > 0: pulsar uno suelta los demás de ese grupo (alineación), y mui_on_change solo salta en el pulsado |  |
| `mui_combo(text, options)` | Int (dirección) | Un campo de texto con una lista que se despliega (fuente, tamaño; opciones "A\|B"): se escribe o se elige una línea (doble clic); mui_get_text / mui_set_text, mui_list_* cambian las líneas, mui_on_ack con Return o al elegir una línea |  |
| `mui_help(obj, text)` | — | Una ayuda en burbuja que sale cuando el puntero se para sobre el objeto |  |
| `mui_window_move(win, dx, dy)` | — | Mueve una ventana abierta dx, dy píxeles (las ventanas de un .dashui se abren en el mismo sitio) |  |
| `mui_set_active(win, obj)` | — | Hace de obj el objeto activo de la ventana: el cursor va a ese campo de texto (Amiga-L) |  |
| `mui_window_size(win, width_pct, height_pct)` | — | El tamaño de la ventana al abrirse, en tanto por ciento de la pantalla visible, centrada (antes de mui_window_open) |  |
| `mui_window_fullscreen(win)` | — | La ventana ocupa toda la pantalla: sin bordes, barra de título ni gadgets, y activa (antes de mui_window_open) |  |
| `mui_window_screen(win, name)` | Bool | La ventana se abre como una ventana normal en la pantalla pública con ese nombre (la de screen_clone_wb, o la de otro programa); antes de mui_window_open; falso si no existe esa pantalla |  |
| `mui_window_own_screen(win)` | Bool | Pantalla completa en una pantalla propia, como la pública (antes de mui_window_open; false: en la pública) |  |
| `mui_width(obj)` | Int | El ancho de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana) |  |
| `mui_height(obj)` | Int | El alto de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana) |  |
| `mui_wait_event()` | Int | Espera el siguiente evento y da su número; -1 para salir |  |
| `mui_poll_event()` | Int | Como mui_wait_event sin esperar: 0 si no hay evento |  |

## DashOS (solo con ./dash --dashos)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `channel_create()` | Int | Un canal nuevo: uno de sus dos lados (el otro, channel_other); o un error negativo |  |
| `channel_other()` | Int | El otro lado del último channel_create (lo que se escribe en un lado se lee en el otro) |  |
| `channel_pass(handle)` | Int | Mete una llave (con derecho a pasarla) en el siguiente channel_send: sale de este programa; hasta 8 por mensaje; 0, o -1 si ya hay 8 |  |
| `channel_send(handle, text)` | Int | Manda un texto (hasta 256 bytes) al otro lado del canal, sin esperar: 0 o un error negativo |  |
| `channel_send_buffer(handle, buffer, length)` | Int | Manda length bytes (hasta 256) de un búfer: 0 o un error negativo |  |
| `channel_receive(handle)` | String | Espera el siguiente mensaje del canal y lo da como texto; nil si hay un error (channel_error); sus llaves: channel_handles, channel_handle; quién lo mandó: channel_mark |  |
| `channel_receive_buffer(handle, buffer, max)` | Int | Espera el siguiente mensaje y lo copia en un búfer (max bytes; con 256 basta): su largo o un error negativo |  |
| `channel_handles()` | Int | Cuántas llaves llegaron con el último mensaje recibido |  |
| `channel_handle(i)` | Int | La llave i (desde 0) del último mensaje recibido; 0 si no hay |  |
| `channel_mark()` | Int | La marca de la llave que escribió el último mensaje recibido (handle_copy): quién lo mandó; 0 sin marca o el kernel (temporizadores) |  |
| `channel_error()` | Int | El error del último channel_receive (0: ninguno; -4: el otro lado se cerró) |  |
| `handle_copy(handle, rights, mark)` | Int | Una copia de una llave con esos derechos o menos (1 leer, 2 escribir, 4 pasar; sumados) y una marca si no tenía (0: la suya): la llave nueva o un error negativo |  |
| `handle_close(handle)` | Int | Cierra una llave (la última de un lado de canal cierra ese lado): 0 o un error negativo |  |
| `handle_revocable(handle)` | Int | Una copia de una llave que se puede retirar (su revocador: handle_revoker): la copia o un error negativo |  |
| `handle_revoker()` | Int | El revocador del último handle_revocable |  |
| `handle_revoke(revoker)` | Int | Retira la llave de un revocador y las copias hechas de ella: desde entonces no valen: 0 o un error negativo |  |
| `timer_create(handle, first_ms, period_ms)` | Int | Un temporizador que manda un mensaje al otro lado del canal a los first_ms, y luego cada period_ms (0: una vez); pasos de 10 ms; se para al cerrar su llave: la llave o un error negativo |  |
| `memory_create(size)` | Int | Un objeto de memoria de size bytes (hasta 4 MB), a cero; se puede pasar a otro programa (memoria compartida): su llave o un error negativo |  |
| `memory_map(handle, writable)` | Int (dirección) | Proyecta un objeto de memoria en este programa, para buffer_* (writable: true para escribir): el búfer, o 0 |  |
| `memory_unmap(buffer)` | Int | Quita lo que dio memory_map (el objeto sigue mientras tenga llaves): 0 o un error negativo |  |
| `process_give(handle)` | Int | Una llave para el siguiente process_start: el programa nuevo las recibe como llaves 1, 2... en este orden; hasta 16; 0, o -1 si ya hay 16 |  |
| `process_group(group)` | — | El grupo de los siguientes procesos (0: el de este programa) |  |
| `process_start(memory, size)` | Int | Lanza un programa desde el ELF de un objeto de memoria (sus primeros size bytes), con las llaves de process_give: el proceso o un error negativo |  |
| `process_start_buffer(buffer, length)` | Int | process_start con un ELF en un búfer (se copia a un objeto de memoria nuevo, hasta 4 MB) |  |
| `process_kill(process)` | Int | Acaba un proceso: 0 o un error negativo |  |
| `process_wait(process)` | Int | Espera a que acabe un proceso: su código de salida (cómo acabó: process_end), o un error negativo |  |
| `process_end()` | Int | Cómo acabó el proceso del último process_wait: 0 salió, 1 lo mataron, 2 falló |  |
| `group_create(bytes)` | Int | Un grupo con un presupuesto de memoria sacado del de este programa: lo que crean sus procesos se cobra ahí: el grupo o un error negativo |  |
| `group_kill(group)` | Int | Acaba todos los procesos de un grupo y suelta todo lo que tenía: 0 o un error negativo |  |
| `group_used(group)` | Int | Los bytes que lleva gastados un grupo (0: el de este programa), o un error negativo |  |
| `group_limit(group)` | Int | El presupuesto de un grupo en bytes (0: el de este programa), o un error negativo |  |
| `dashos_error_text(code)` | String | Qué quiere decir un error negativo de DashOS, como texto |  |
