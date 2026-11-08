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

- [x] T1. Infraestructura: `builtins_doc.py`, el generador, la tabla con tipos de Dash.
- [x] T2. Gráficos básicos (`GRAPHICS_BASIC`, 30), con `tests/test_doc_graficos.dash`.
- [x] T3. Ventanas, gadgets y peticiones (`INTUITION_EXPANDED`, 59), con `tests/test_doc_ventanas.dash`.
- [ ] T3b. Pantallas (`screen_open*`, `screen_close`, `close_window`... de `GRAPHICS_ADVANCED`).
- [ ] T4. Entrada (`INPUT_FUNCTIONS`, 37).
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
