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
- [ ] T5. Ficheros (`DOS_FUNCTIONS`, 29, y `ASL_FUNCTIONS`, 5).
- [ ] T6. MUI (`MUI_FUNCTIONS`, 108), en dos o tres tandas.
- [ ] T7. Gráficos avanzados (`GRAPHICS_ADVANCED`, 85): sprites, bobs, bitmaps, copper.
- [ ] T8. Texto, buffers, sistema y memoria, audio.
- [ ] T9. El resto de grupos.
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
