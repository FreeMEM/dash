# Documentación ampliada de los builtins

Encargo del usuario (2026-11-08, por la sesión "telegram"): "Hay que desarrollar un poco más la documentación. Por
ejemplo la de built-in es demasiado escueta".

## Cómo está hecho

- `compiler/builtins_doc.py`: `GROUPS` (introducción de cada grupo, en castellano y en inglés, y su ejemplo) y
  `FUNCS` (cada builtin: parámetros y rango, qué devuelve, qué pasa si falla, y `see`, las relacionadas).
- `tools/gen_builtins_doc.py` lo junta con las tablas de siempre en `docs/BUILTINS.md` y `docs/BUILTINS.en.md`.
  La tabla queda como índice, con enlace a las funciones explicadas. Comprueba que los nombres existen y que hay
  los dos idiomas.
- Cada ejemplo es un test, `tests/test_doc_*.dash`: el runner lo compila por los dos caminos y comprueba su salida
  en el emulador (`# expect-out:`). Esas líneas no salen en la documentación.
- Lo que se afirma de una función se mira en su código C (`c_template` y el runtime de `compiler/codegen.py`) o
  se prueba en el emulador. Si al probar sale un fallo, se arregla aparte, con su test.

## Tareas

Primero los grupos que más usa la gente del grupo de Telegram.

- [x] T1. Infraestructura: `compiler/builtins_doc/`, el generador, la tabla con tipos de Dash.
- [x] T2. Gráficos básicos (`GRAPHICS_BASIC`, 30), con `tests/test_doc_graficos.dash`.
- [x] T3. Ventanas, gadgets y peticiones (`INTUITION_EXPANDED`, 59), con `tests/test_doc_ventanas.dash`.
- [x] T4. Entrada y pantallas (`INPUT_FUNCTIONS`, 37: las `screen_*` están en este grupo), con
  `tests/test_doc_entrada.dash`.
- [x] T5. Ficheros (`DOS_FUNCTIONS`, 29, y `ASL_FUNCTIONS`, 5), con `tests/test_doc_ficheros.dash`.
- [x] T6a. MUI: aplicación, ventanas, grupos, objetos, valores, listas, eventos y menús, con
  `tests/test_doc_mui.dash`.
- [x] T6b. MUI: la zona de dibujo (`mui_canvas*`), imágenes, combo, barra de desplazamiento, con
  `tests/test_doc_mui_lienzo.dash` (un grupo puede llevar varios ejemplos).
- [x] T7a. Gráficos avanzados: introducción, sprites de hardware y de software, BOBs, con
  `tests/test_doc_sprites.dash`.
- [x] T7b. Mapas de tiles (`tilemap_*`), con `tests/test_doc_tiles.dash`.
- [x] T7c. Copper y bitmaps, con `tests/test_doc_bitmaps.dash`.
- [x] T8a. Texto, búferes y buscar en un búfer, con `tests/test_doc_texto.dash`.
- [x] T8b. Sistema y memoria (`SYSTEM_FUNCTIONS`), con `tests/test_doc_sistema.dash`.
- [x] T8c. Audio (`AUDIO_FUNCTIONS`), con `tests/test_doc_audio.dash`.
- [x] T9a. GadTools y menús (`GADTOOLS_FUNCTIONS`, `MENU_FUNCTIONS`), con `tests/test_doc_gadtools.dash`.
- [x] T9b. Fuentes, transparencia, RGB, imágenes, TrueType e imágenes decodificadas, con
  `tests/test_doc_fuentes.dash`.
- [x] T9c. Red, TLS y red en una tarea aparte, con `tests/test_doc_red.dash` (servidor de eco del runner).
- [ ] T9d. Tareas, reloj, traducciones y escritorio (`TASK_FUNCTIONS`, 89), en dos tandas.
- [x] T9e. Argumentos, zlib, UTF-8, Double, matemáticas, expresiones regulares, portapapeles, ordenar, JSON, con
  `tests/test_doc_varios.dash`.
- [x] T9f. Sistema y programa (`SYSPROG_FUNCTIONS`), con `tests/test_doc_sysprog.dash`.
- [ ] T9g. Simular teclado y ratón, ventanas de otros programas, gestor de ventanas.
- [ ] T9h. Depurador (`DEBUGGER_FUNCTIONS`).
- [ ] T9i. ReAction (`REACTION_FUNCTIONS`, 79), en dos tandas.
- [ ] T9j. RTG.
- [ ] T9k. DashOS.
- [ ] T10. Otras guías escuetas: repasar `QUICK_REFERENCE`, `MANUAL_REFERENCIA` (secciones de una tabla sin
  explicar) y `SINTAXIS`, y enlazar a `BUILTINS.md` en vez de repetir.

## Bitácora

- 2026-11-08: T1-T3. Los textos van en `compiler/builtins_doc/`, un módulo por grupo. Los dos ejemplos pasan en
  el emulador por los dos caminos (`tools/emu_run.py --dash2` para `./dash`).
  - Arreglo: `gfx_flood` no rellenaba nada sin búfer de relleno (TmpRas), por ejemplo en una ventana de
    `window_create`. Ahora presta el suyo como los otros rellenos (`_dash_flood`); `tests/test_gfx_flood.dash`.
  - Visto: el `EventLoop` exige una ventana declarada (`Window X`) abierta; con solo `window_create` no compila.
    Documentado. Podría admitirlas: pendiente de decidir.
  - La fuente del sistema del emulador no es topaz 8 (`gfx_text_len("Hola")` da 40): los ejemplos no dependen
    del ancho del texto.
- 2026-11-08: T4. Entrada y pantallas.
  - Arreglo: el joystick. `joy_x`/`joy_y` leían un byte de JOYxDAT (la mitad de arriba): arriba y abajo no salían
    nunca, la izquierda llegaba con arriba y la derecha no. `joy_button`/`joy_fire` miraban POTGOR (el segundo
    botón) en vez del disparo (CIA-A PRA, bits 6 y 7). Lo usa la plantilla de juego de la extensión.
    `tests/test_joystick.dash` prueba la descodificación con valores del registro; con un joystick de verdad no
    se ha probado (FS-UAE sin entrada).
  - Arreglo: `wait_key` volvía con 0 si llegaba antes otro mensaje que una tecla; `wait_click` gastaba toda la CPU
    esperando (ahora mira 50 veces por segundo). `tests/test_wait_key.dash` (no reproduce el caso de antes: las
    dos cosas llegan juntas). Visto de paso: un `input_click` en el botón de cerrar y un `input_key` desde otra
    tarea (`task_start`) cuelgan el programa; sin investigar.
  - `screen_open` y `screen_open_custom` no miran si ya hay una pantalla abierta (abrirían otra y perderían la
    primera); `screen_open_mode` sí. Documentado: una a la vez.
- 2026-11-08: T5. Ficheros. Sin fallos en lo probado (líneas con `file_read_line`, `file_seek`, `dir_read`,
  borrar un cajón vacío).
  - Visto: una llamada con un texto entre comillas dentro de una interpolación (`"#{file_size("RAM:x")}"`) compila
    con `./dash` y no con `./dash --gcc` (error de sintaxis). Los dos caminos deberían hacer lo mismo; sin tocar.
- 2026-11-08: T6a. MUI, primera tanda (75 funciones). Sin fallos en lo probado.
- 2026-11-08: T6b. MUI, segunda tanda (29). MUI entero documentado. Sin fallos en lo probado.
- 2026-11-08: T7a. Sprites y BOBs. Sin fallos en lo probado (fotogramas de un BOB creado, choque por píxeles,
  fondo devuelto, sprite hecho fila a fila). Visto: `sprite_create` no usa el ancho (siempre 16); documentado.
- 2026-11-08: T7b. Mapas de tiles.
  - Arreglo: `tilemap_draw` (sin máscara) dejaba vacías las celdas de después de la primera celda en espejo, la
    primera vez que se pintaba el mapa tras crear o cambiar el BOB: al preparar los espejos se liberaba la copia
    entrelazada del BOB que se estaba usando, y el blitter leía de una dirección nula. Afectaba al primer pintado
    de un nivel con tiles en espejo (en un juego y en el editor de mapas de Forja). `tests/test_tilemap_espejo.dash`.
- 2026-11-08: T7c. Copper y bitmaps. `bitmap_load` y `bob_load` ponen la paleta de la imagen en una pantalla
  propia (la descripción corta no lo decía); documentado. El degradado del copper no se ha podido ver: la captura
  (`tools/amiga/shot.c`) lee la imagen y su paleta, no lo que sale por pantalla.
- 2026-11-08: T8a. Texto y búferes. `buffer_alloc` no se libera al acabar el programa (AllocVec sin apuntar):
  documentado como aviso.
  - Arreglo: un texto entre comillas dentro de una interpolación (`"#{f("x")}"`) ya compila con `./dash --gcc`,
    como con `./dash` (el literal de Lark acababa en la comilla de dentro). `tests/test_interp_comillas.dash`;
    `./compile_all.sh` 34/34. Sigue distinto un caso raro: un `#{` sin cerrar seguido de otra interpolación en el
    mismo texto (`./dash --gcc` lo deja todo como texto, `./dash` interpola la segunda).
- 2026-11-08: T8b. Sistema y memoria.
  - Arreglo: `random_range(min, max)` con `max` = `min` - 1 dividía por cero (un fallo de la CPU) y con `max` menor
    daba números fuera; ahora `max <= min` devuelve `min`. En `tests/test_doc_sistema.dash`.
  - Visto: `random` da solo 15 bits (0 a 32767), las arenas no se liberan solas y `arena_alloc` no pone a cero
    tras un `arena_reset`; documentado.
- 2026-11-08: T8c. Audio. `music_play` empieza siempre desde el principio (`music_position` solo vale mientras
  suena) y los `sound_*` durante la música se pisan con ella; documentado.
- 2026-11-08: T9a. GadTools y menús. Comprobado en el emulador que los `gt_*` cuentan `x`, `y` desde dentro de los
  bordes (el comentario de `_dash_window_border` en el runtime dice lo contrario; sin tocar).
- 2026-11-08: T9b. Fuentes, imágenes y colores.
  - Arreglo: `color_pen` en una pantalla propia daba el lápiz 1 (negro) para cualquier color: ObtainBestPen solo
    mira los lápices compartidos del sistema, y en una pantalla sin SA_SharePens todos los demás son del programa.
    Ahora busca el más parecido de su paleta (FindColor). `tests/test_color_pen_pantalla.dash`. En el Workbench
    sigue igual.
  - `image_decode` y `font_from_ttf` no tienen ejemplo propio (necesitan ficheros); los cubren sus tests de siempre.
- 2026-11-08: T9c. Red. El ejemplo usa el servidor de eco del runner (`# emu-net:`); por `./dash`, con un servidor de
  eco lanzado a mano. TLS y la red en una tarea, sin ejemplo propio (los cubren sus tests).
- 2026-11-08: T9e. Utilidades (66 funciones). Sin fallos en lo probado.
- 2026-11-08: T9f. Sistema y programa (42). Sin fallos en lo probado. El sistema del emulador no trae `Delete`.
