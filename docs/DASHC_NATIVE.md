# Los @native de los programas del usuario

Encargo D7 de `docs/DASHC_LOOP.md`. Decisión del usuario (2026-10-28): dashc (Dash 2.0) no admite `@native` (C
embebido) en los programas del usuario; el de `lib/amiga` se compila al construir dashc. Este documento clasifica
los `@native` que hay hoy en los programas del usuario y dice con qué se sustituiría cada grupo.

Alcance: los `.dash` de `~/Projects/tachyon`, `~/Projects/trasfondo` y `~/Projects/lorraine`, sin `.worktrees` ni
`node_modules` (recuento del 2026-10-28).

| Proyecto | `@native` | Ficheros |
|---|---|---|
| tachyon | 137 | 27 |
| trasfondo | 33 | 5 (todos en `tests/`) |
| lorraine | 1 | 1 (`tools/medir_cpu.dash`) |
| **Total** | **171** | 33 |

Otras directivas que dashc no puede compilar sin un compilador de C:

- `@c`: 13 bloques de C suelto, 3.311 líneas (tachyon: `jsdom` 963, `lienzo` 488, `fuente_web` 471, `js` 478,
  `html5` 275, `imagen_dec` 256, `http` 4, `documento` 3; trasfondo: `prueba_fondo` 214, `prueba_cpu` 159).
- `@header`: 54 líneas, casi todas `#include`; las 13 de `lib/red.dash` llevan también C (tabla `_rt[48]`,
  `SignalSemaphore`, `_rt_liberar`).
- `@link`: 6 (`libimg.a`, `libvideo.a`, `libqjs.a`).
- `@stack`: 3. No es C: dashc debe admitirlo.

## Resumen

| # | Categoría | Bloques | ¿Lo cubre ya Dash? | Qué haría falta |
|---|---|---|---|---|
| 1 | QuickJS: motor JS, DOM y canvas 2D | 34 | No | QuickJS en la librería de dashc (`js_*`) con llamadas de JS a Dash, o módulos nativos precompilados |
| 2 | Vídeo MintVID (`libvideo.a`, `dwv_*`) | 20 | No (solo `gfx_rgb_draw*` pinta los fotogramas) | Builtins `video_*` o enlazar `libvideo.a` con firmas declaradas |
| 3 | HTML5 con Hubbub | 12 | No | `html5_parse(texto, utf8)` con accesores, o un analizador en Dash |
| 4 | Decodificar imágenes (TJpgDec, libwebp, nanosvg, stb_image) | 10 | En parte (`image_load`, `image_from_rgb`) | `image_decode(fichero, maxw, maxh)` que pueda correr en una tarea |
| 5 | Fuentes web (stb_truetype, WOFF 1/2, Brotli) | 4 | No (`font_open` solo FONTS:) | `font_from_ttf(fichero, tam, ancho%)` para `font_use` |
| 6 | gzip/zlib en HTTP | 3 | Casi (`inflate`, `crc32`) | La cabecera en Dash; opcional `inflate_auto` |
| 7 | Red en una tarea aparte (semáforo, AmiSSL) | 14 | En parte (`net_*_start/poll`, `tls_*`) | Conexiones de fondo `net_bg_*`, o `task_start` con funciones Dash y cerrojos |
| 8 | Funciones para `task_start` | 1 (+4 en 4, 7 y 20) | No: `task_start` solo acepta `@native` | `task_start` con funciones Dash (búferes y enteros, sin textos ni listas compartidos) |
| 9 | Esperas (`Delay`) | 12 | Sí (`time_delay`, `time_delay_ms`) | Sustituir |
| 10 | Fecha y hora (`DateStamp`) | 3 | Casi (`clock_*`) | Opcional `clock_seconds()` o `time_unix()` |
| 11 | Memoria libre | 3 | Casi (`mem_total`) | `mem_largest()` |
| 12 | Lanzar programas, abrir iconos y cajones | 6 | En parte (`run_program` asíncrono) | `run_command(orden)` síncrono, `wb_open(ruta)` |
| 13 | Información del sistema y del programa | 6 | En parte (`@version`, `program_version`) | `cpu_model`, `fpu_model`, `library_version`, `program_path`, `locale_language`, `build_date`/`build_time` |
| 14 | Ficheros y bytes | 3 | Sí (`file_load`, `inflate`, `crc32`...) | Reescribirlos en Dash |
| 15 | Ventanas MUI y petición ASL | 3 | En parte | `mui_set_active`, `mui_window_move`, `dialog_file` con cajón y nombre iniciales |
| 16 | Bajo nivel del programa principal | 3 | No | `input_qualifiers()`, `console_flush()`, precisión de la FPU puesta por el runtime |
| 17 | Medida de CPU y prioridad | 3 | `time_ms` sí; la prioridad no | `task_priority(n)`; `cpu_loop(n)` o calibrar con el bucle de dashc |
| 18 | Pruebas: simular entrada, ventanas ajenas | 14 | En parte (`input_*`) | `window_find`, `input_event`, `input_move_screen`, `input_menu`, `screen_pixel`, `gadget_find`, `cx_send` |
| 19 | Depuración interna de exec | 4 | Solo `peek_*` sin `Forbid` | Dejarlas en Dash 1.x, o unos pocos builtins `task_*` |
| 20 | Prototipos que ya son builtins (`cpu_*`, `desktop_canvas_*`) | 13 | Sí | Retirar o reescribir con los builtins |

Las categorías 1 a 7 son 97 bloques (57 %) y casi todo el `@c`: pegamento con librerías de C. Las 9 a 20 (73
bloques) salen con builtins existentes, con Dash o con builtins nuevos y pequeños.

## Detalle

1. **QuickJS** (`tachyon/lib/js.dash` 14, `jsdom.dash` 12, `lienzo.dash` 7, `documento.dash` 1; `libqjs.a`;
   ~2.200 líneas de `@c`: clase `Node`, ~40 funciones `__dashweb_*`, rasterizador de canvas `_lz_*`, perfilador
   por VBlank). El C llama a ~43 funciones Dash (`jsdom_por_id`, `jsdom_selector`, `css_media_vale`...) y usa la API
   interna del runtime (`_dash_retain`, `_dash_str_dup`, `_Dash_Nodo`).
2. **Vídeo**: `tachyon/lib/video.dash` (18) y `youtube.dash` (2): envoltorios de una línea de `dwv_*`.
3. **HTML5**: `tachyon/lib/html5.dash`, 17 callbacks de Hubbub que guardan el árbol en una tabla numerada (la API
   de un builtin puede ser esa tabla).
4. **Imágenes**: `tachyon/lib/imagen_dec.dash`, JPEG reducido al decodificar, WebP, SVG y stb_image, en una tarea.
5. **Fuentes web**: `tachyon/lib/fuente_web.dash`, TTF/WOFF/WOFF2 a una `TextFont` de 1 bit, con caché.
6. **gzip**: `tachyon/lib/http.dash`, `_http_inflar` con cabecera gzip/zlib/crudo.
7. **Red de fondo**: `tachyon/lib/red.dash`, `_rt_bucle` en `task_start` avanza 48 conexiones (connect, TLS,
   envío, recepción no bloqueante con `SSL_read`/`IoctlSocket`), búferes bajo semáforo, `Signal` para despertar.
8. **`task_start`**: `tachyon/docs/tutorial/paso5_tarea.dash` (`contar_palabras`), más `_rt_bucle`,
   `_imgdec_tarea`, `tf_lleno` y `tf_medio`. Requisito de las categorías 4, 7 y 20.
9. **Esperas**: `esperar(ticks)` en 6 tests de tachyon, `esperar_ms` en 3 herramientas, y en trasfondo `medir_cpu`,
   `prueba_commodity`, `prueba_prefs`.
10. **Fecha**: `actualizar_hoy`, `cookies_ahora`, `historial_ahora` (tachyon).
11. **Memoria**: `libre()` (trasfondo 2) y `libre(mayor)` (tachyon `latido.dash`, `MEMF_LARGEST`).
12. **Lanzar**: `actualizar_lanzar` (cubierto por `run_program`), `lanzar(orden)` síncrono (trasfondo, 3),
    `_abrir_cajon` y `lanzar_icono` (`OpenWorkbenchObjectA`, que el runtime ya usa en `program_relaunch`).
13. **Sistema**: `_informe_sistema` (CPU, FPU, versiones de librerías, MorphOS, memorias), `actualizar_programa`
    (`GetProgramDir`/`NameFromLock`), `actualizar_idioma_preferido` (`loc_PrefLanguages`, ya en el runtime de
    `tr`), `compilado_fecha`/`compilado_hora`, `texto_version`.
14. **Ficheros**: `actualizar_catalogo_lang`, `actualizar_ascii`, `_actualizar_instalar` (tachyon `actualizar.dash`).
15. **MUI y ASL**: `activar`, `mover_ventana` (tachyon `dashweb.dash`), `descargas_pedir_ruta`.
16. **Bajo nivel**: `modificadoras` (`PeekQualifier`), `vaciar_salida` (`Flush(Output())`),
    `fpu_precision_extendida` (`fmove.l fpcr`).
17. **CPU**: `bucle_cpu` (lorraine, asm), `contar` y `al_fondo` (trasfondo, `SetTaskPri`).
18. **Pruebas**: `tachyon/tools/amiga/clicar.dash` (6), `trasfondo/tests/prueba_prefs.dash` (5) y
    `prueba_commodity.dash` (3): buscar ventanas ajenas, eventos crudos de input.device, menús con el ratón,
    gadgets por texto, `ReadPixel`, `BrokerCommand`.
19. **Exec**: `tarea_de`, `tarea_linea`, `trozos` (tachyon `latido.dash`), `ganchos` (trasfondo).
20. **Prototipos**: `trasfondo/tests/prueba_cpu.dash` (7) y `prueba_fondo.dash` (6), hoy builtins `cpu_*` y
    `desktop_canvas_*`.

## Conclusiones

1. Lo que bloquea es Tachyon (categorías 1 a 7: QuickJS, MintVID, Hubbub, stb, TJpgDec, libwebp, nanosvg, Brotli
   y la red de fondo). Vía intermedia que encaja con la decisión: **módulos nativos precompilados**. Su C se compila
   una vez con gcc a un objeto Hunk, y el programa Dash solo declara las firmas (`@extern`) que dashc enlaza. Habría
   que resolver además que ese C llame a funciones Dash y use la API interna del runtime.
2. `task_start` con funciones Dash: requisito de las categorías 4, 7, 8 y 20.
3. Builtins nuevos y pequeños para las categorías 10 a 18: `clock_seconds`, `mem_largest`, `run_command`, `wb_open`,
   `program_path`, `locale_language`, `cpu_model`, `fpu_model`, `library_version`, `build_date`, `build_time`,
   `task_priority`, `input_qualifiers`, `console_flush`, `mui_set_active`, `mui_window_move`, `dialog_file_at`,
   `window_find`, `input_event`, `input_move_screen`, `input_menu`, `screen_pixel`, `gadget_find`, `cx_send`.
4. Sin trabajo nuevo: categorías 9, 14 y 20 (28 bloques).
