*[English](MINIGL.en.md) | Castellano*

# 3D con MiniGL

Las funciones `gl_*` dibujan en 3D con MiniGL, la parte de OpenGL 1.x del Amiga. Van por los dos caminos (`./dash` y
`./dash --gcc`), con y sin `--fpu`. Lo pidió el usuario (paso 5.3 de `FORJA_LOOP` de Forja). Lista completa:
[BUILTINS.md](BUILTINS.md#3d-con-minigl).

<!-- indice -->
<a id="indice"></a>

**Índice**

- [Qué hace falta](#qué-hace-falta)
- [Cómo se usa](#cómo-se-usa)
- [Coma flotante](#coma-flotante)
- [Probado en el emulador](#probado-en-el-emulador)
- [Dibujar en bloque](#dibujar-en-bloque)
- [El motor 3D con MiniGL](#el-motor-3d-con-minigl)
<!-- /indice -->

<a id="qué-hace-falta"></a>

## Qué hace falta

- `minigl.library` 29 o más. Hay varias, todas con la misma interfaz:
  - **MiniGL Classic** (Steffen Häuser, Aminet `util/libs/MiniGL_Library_Classic.lha`), encima de un Warp3D:
    tarjetas 3D clásicas (CyberVision 64/3D, Voodoo 3 PCI), QuarkTex en WinUAE o Wazp3D, que es Warp3D por software.
  - **PiStorm3D** (Aminet `util/libs/PiStorm3D.lha`): con la GPU de la Raspberry Pi en un PiStorm32 con Pi 4 o CM4.
  - **RadeonGL** (Aminet `driver/video/RadeonGL.lha`): Radeon R200 con Picasso96.
- Una FPU. Las bibliotecas están compiladas para ella: sin FPU, `gl_open` da `false` en vez de colgarse.
- Pantalla RTG para la ventana (`gl_open`); `gl_open_screen` abre una pantalla propia de 16 bits.

Dash no necesita el SDK de MiniGL: llama a la biblioteca por su tabla de funciones (ABI 5 de
`libraries/minigl_dispatch.h`), con los números de OpenGL.

[Volver al índice](#indice)

<a id="cómo-se-usa"></a>

## Cómo se usa

```ruby
import "lib/amiga/gl.dash"      # GL_TRIANGLES, GL_DEPTH_TEST, GL_BLEND...

Main
    if not gl_open(320, 240)
        Print "Hace falta minigl.library y una FPU"
        program_exit(5)
    end
    gl_enable(GL_DEPTH_TEST)
    angulo = 0.0
    while not gl_closed()
        gl_clear()
        gl_load_identity()
        gl_translate(0, 0, -4)
        gl_rotate(angulo, 0, 1, 0)
        gl_begin(GL_TRIANGLES)
        gl_color(1, 0, 0)
        gl_vertex(0, 1, 0)
        gl_color(0, 1, 0)
        gl_vertex(-1, -1, 0)
        gl_color(0, 0, 1)
        gl_vertex(1, -1, 0)
        gl_end()
        gl_swap()
        angulo = angulo + 2.0
    end
end
```

- **Contexto:** `gl_open(ancho, alto)` (ventana en el Workbench) o `gl_open_screen(ancho, alto)`, `gl_close`,
  `gl_swap`, `gl_vsync(on)`, `gl_closed()`, `gl_key()`. `gl_open` deja una perspectiva de 60 grados y la matriz
  modelview activa. `gl_swap` espera al refresco de la pantalla; `gl_vsync(false)` quita la espera.
- **Estado:** `gl_enable`/`gl_disable` con las constantes de `lib/amiga/gl.dash`, `gl_clear_color`, `gl_clear`,
  `gl_viewport`, `gl_shade_model`, `gl_cull_face`, `gl_blend_func`.
- **Matrices:** `gl_matrix_mode`, `gl_load_identity`, `gl_push_matrix`, `gl_pop_matrix`, `gl_translate`,
  `gl_rotate`, `gl_scale`, `gl_perspective`, `gl_ortho`, `gl_look_at`.
- **Figuras:** `gl_begin(modo)` ... `gl_end()`, con `gl_vertex`, `gl_color`, `gl_color_alpha`, `gl_normal` y
  `gl_tex_coord`.
- **Texturas:** `gl_texture(d)` de una imagen de `image_decode` (PNG, JPEG, GIF, BMP, WebP), llevada a potencias de
  dos hasta 256 x 256; `gl_texture_bind(t)` (0: sin textura), `gl_texture_free(t)`.
- **Luces:** `gl_light(n, x, y, z)` enciende la luz n desde esa dirección, con `gl_color` como material;
  `gl_light_color`, `gl_ambient`. Cada cara necesita su `gl_normal`.
- **Niebla:** `gl_fog(inicio, fin, r, g, b)`; `gl_disable(GL_FOG)` la quita.
- **Otros:** `gl_read_pixel(x, y)` (el color de un píxel antes de `gl_swap`, para pruebas) y `gl_error()`.

Los números van a MiniGL como `float`: valen un `Float`, un `Int` o un `Double`. Los colores, de 0.0 a 1.0.

[Volver al índice](#indice)

<a id="coma-flotante"></a>

## Coma flotante

Los programas `gl_*` no piden `--fpu`: van igual sin ella, porque el runtime pasa los números a la biblioteca como
`float` de C. Pero la biblioteca sí necesita FPU, así que la máquina la tiene. Con `--fpu` las cuentas del programa
(ángulos, `sin`, `cos`, matrices propias) van con la FPU en vez de por software: es lo recomendable.

[Volver al índice](#indice)

<a id="probado-en-el-emulador"></a>

## Probado en el emulador

En la máquina `coffin` (FS-UAE, 68040 con JIT, RTG), con MiniGL Classic 30.0 encima del Wazp3D 57V que trae el
disco de CoffinOS. El disco no trae `minigl.library`: las pruebas la ponen en `LIBS:` de la copia del disco.

```bash
DASH_EMU_MINIGL=~/.cache/dash-emu/minigl/minigl.library python3 tests/run_tests.py test_gl --emu-coffin
tools/emu_run.py --machine coffin --lib ~/.cache/dash-emu/minigl/minigl.library examples/gl_cubo.dash
```

`examples/gl_cubo.dash` (cubo con luz, 320 x 240) va a 56 fotogramas por segundo esperando al refresco, y a unos
300 sin esperar (`RAPIDO=1`), igual por los dos caminos y con o sin `--fpu`. Es un 68040 emulado a toda velocidad:
en un Amiga de verdad con Wazp3D será mucho más lento.

Lo que Wazp3D, con su configuración de serie, no hace (también en un programa de C, así que no es cosa de Dash):

- El Z-buffer no tiene efecto: gana lo último que se dibuja. Un objeto convexo se ve bien con `GL_CULL_FACE`.
- Un color por esquina sale plano (el de la primera esquina).
- La mezcla (`GL_BLEND`) mezcla con negro, no con lo que hay debajo.
- No hay niebla (está apagada en sus preferencias, `SYS:Prefs/Wazp3D`).
- Con textura, el color de `gl_color` no la tiñe.

`gl_open` arregla dos cosas de MiniGL Classic con Wazp3D: la primera figura de un contexto nuevo no se dibujaba, y
`GL_CULL_FACE` quitaba las caras de delante (las que se ven en sentido contrario a las agujas del reloj). Lo
comprueba al abrir, dibujando y leyendo el píxel del centro, así que con otra biblioteca que lo haga bien no cambia
nada.

[Volver al índice](#indice)


<a id="dibujar-en-bloque"></a>

## Dibujar en bloque

`gl_draw_arrays` y `gl_draw_elements` mandan de una vez un bloque de esquinas preparado en búferes (3 `float` por
esquina, con `buffer_set_float` o de un fichero; 4 bytes de color por esquina), y `gl_mult_matrix` pone de una vez el
giro y el desplazamiento de una pieza (los huesos de un modelo). Lo pidió el juego Titan Force (`~/Projects/titanforce`).

Medido en `coffin` con MiniGL Classic sobre Wazp3D, un robot de 1200 triángulos en 17 piezas y un barrio de casas: con
`gl_vertex` uno a uno, quitando antes las caras de espaldas, el dibujo llevaba unos 116 ms por fotograma; con
`gl_draw_arrays` (sin quitarlas, porque MiniGL calcula cada esquina antes de ver si la cara se ve) unos 133 ms, y con
`gl_draw_elements` unos 258 ms. Con Wazp3D lo que cuesta es el trabajo de MiniGL en cada esquina, no las llamadas: en
bloque no se gana. Las tres están pensadas para una tarjeta 3D (PiStorm3D, Warp3D), sin probar. Para ese juego, un
motor por software en Dash (las cuentas, el orden y el relleno con `buffer_fill` en un búfer de lápices, volcado con
`gfx_pens_draw`) fue tres veces más rápido que MiniGL sobre Wazp3D.

Sin probar: PiStorm3D, RadeonGL y MiniGL Classic con una tarjeta 3D o con QuarkTex.

[Volver al índice](#indice)

<a id="el-motor-3d-con-minigl"></a>

## El motor 3D con MiniGL

`lib/motor3d.dash` puede rellenar con MiniGL: `m3d_abrir_gl(ancho, alto, propia)` en vez de `m3d_abrir` y
`m3d_con_gl(m)` después de `m3d_nuevo` (antes de `m3d_cargar`, que sube las texturas). El motor sigue haciendo las
cuentas, quita las caras de espaldas, pone la luz y ordena de lejos a cerca; MiniGL solo rellena los triángulos, en 2D
y en ese orden, sin Z-buffer: el mismo dibujo que por software, con la textura filtrada y la trama hecha mezcla de
colores. La niebla del suelo va en el color de cada franja de 4 filas, sin transparencias: con Wazp3D, la mezcla con
`GL_BLEND` salía hacia negro. Para acabar el fotograma, `m3d_mostrar(m)`; `m3d_texto` escribe encima en los dos
caminos y `m3d_cerrar(m)` cierra. Lo pidió Titan Force (`RENDER=MINIGL`). En `coffin` con Wazp3D va a 1-2 fotogramas
por segundo (MiniGL por software); sin probar con una tarjeta 3D. `m3d_abrir_gl(..., true)` abre una pantalla propia
de 16 bits: en `coffin`, ahí Wazp3D pinta con los colores cambiados; en una ventana del Workbench salen bien.

[Volver al índice](#indice)
