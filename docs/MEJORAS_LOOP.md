# Mejoras tras el repaso (para `/loop`)

Arranque:

```
/loop Sigue las instrucciones de docs/MEJORAS_LOOP.md: haz UNA tarea y actualiza la bitácora. No hagas pausas entre vuelta y vuelta
```

## Objetivo

Aplicar las cinco decisiones del usuario del 2026-10-14 sobre las propuestas del repaso
(`docs/REPASO_LOOP.md`, "Resumen final"):

1. Memoria durante la ejecución: método ligero, recomendado abajo.
2. Implementar los 72 builtins declarados sin código.
3. `-O2` por defecto, después de probarlo en emulador.
4. Salida común de error en `main`.
5. Mejoras del lenguaje: hexadecimal, floats, `break`/`continue`, rangos descendentes,
   `On Key`, asignación anidada `a.b.c = x`, enums negativos, propiedades de ventana booleanas.

## Reglas de cada iteración

1. **Rama.** Trabaja en la rama local `mejoras` (sale de `repaso`). Nunca hagas push ni toques `main` ni `repaso`.
2. **Base.** `python3 tests/run_tests.py` y `./compile_all.sh`. Anota si cambia respecto a la última entrada.
3. **Tarea.** Coge la primera tarea `[ ]`. Márcala `[~]` mientras trabajas. Una por iteración.
   Si es demasiado grande, divídela en la lista y haz solo la primera parte.
4. **Hacer.** Cada cambio lleva su test en `tests/` (normal, de error o `# expect-c:`).
   Prueba en el emulador lo que se pueda ejecutar: `# expect-out:` en el test y
   `python3 tests/run_tests.py --emu` (unos 30 s). Usa el Kickstart 3.1 real del usuario:
   `export DASH_KICKSTART="/home/freemem/Descargas/Telegram Desktop/ks31a1200.rom"`
   (sin la variable se usa el AROS de FS-UAE).
5. **Verificar.** Repite el paso 2. Nada que antes funcionaba puede romperse.
   Si algo se rompe y no lo arreglas en esta iteración, revierte.
6. **Documentar.** Actualiza `docs/QUICK_REFERENCE.md`, `docs/MANUAL_REFERENCIA.md` y, si cambian
   builtins, `python3 tools/gen_builtins_doc.py`.
7. **Cerrar.** Marca `[x]`, añade una entrada a la bitácora y commit local con mensaje
   `mejoras: <tarea> - <resumen>`.
8. **Fin.** Si no quedan tareas `[ ]`, escribe el resumen final y termina el loop.

## Límites

- No instales paquetes del sistema. Un `venv` en el scratchpad sí vale.
- No toques `sesion.txt`, `*.zip` ni `amiga1200_rtg.fs-uae`. No borres tests ni ejemplos.
- Si una tarea exige una decisión del usuario, déjala `[?]` con la pregunta y pasa a la siguiente.
- 68000 sin FPU: nada de instrucciones de 68020+ salvo que el builtin sea de RTG/AGA.

## Memoria: método recomendado

Un Amiga tiene poca RAM y una CPU lenta. Un recolector de basura (GC) que recorre la memoria
necesita margen libre y provoca pausas. El conteo de referencias suma trabajo en cada asignación
y no libera ciclos. Para Dash se recomienda algo más simple, centrado en los strings,
que son los que crecen en un bucle (concatenar, interpolar, `Print("x" + n)`):

- **Cada variable String es dueña de su texto.** Al asignar se copia (o se adopta si el valor es
  un temporal recién creado) y se libera el texto anterior. Al salir del bloque o de la función se
  liberan sus strings locales. Cuesta una copia corta, nunca una pausa.
- **Temporales por iteración.** Los strings intermedios (`a + b + c`, `"#{x}"`, `from_int`) van a una
  lista de temporales. Al final de cada vuelta de un bucle, de cada `EventLoop` y de cada función se
  libera lo que quedó en la lista desde el principio de esa vuelta.
- **Escape.** Si un string sale hacia algo que el compilador no controla (un array, una llamada al
  sistema que guarda el puntero como el título de una ventana, un `@native`), se marca como
  permanente y ya solo se libera al salir del programa con el pool.
- Cabecera de 8 bytes por string (tamaño + enlace).
- **Listas y structs** (decisión del usuario: abarcar más que los textos): varias variables pueden
  compartir la misma lista o struct, así que no sirve "un dueño". Contador de referencias: 4 bytes por
  objeto y una suma/resta solo al asignar listas o structs. Las listas temporales (literales, trozos
  `a[1:3]`) usan la misma lista de temporales por vuelta. Los ciclos (un struct que apunta a otro que
  apunta al primero) no se liberan hasta salir del programa.

## Tareas

- [x] 1. Salida común de error en `main`: si falla `OpenWindowTags` (u otra apertura), liberar
      todo lo abierto (librerías, pantalla, ventanas, pool) antes de salir. También dentro de funciones.
- [x] 2. Banco de pruebas en emulador: `fs-uae` con el Kickstart 3.1 del usuario o el AROS integrado (antes creía que no había ROM
      de Commodore en el equipo), un directorio como disco duro y `S:Startup-Sequence` que ejecuta el
      programa y guarda la salida en un fichero. Script `tools/emu_run.sh` y, si va estable, tests de
      ejecución en el runner. Si no se puede sin ventana visible, anotarlo y seguir.
- [x] 3. `-O2`: compilar los ejemplos con y sin `-O2`, ejecutarlos en el emulador y comparar.
      Si van igual, `-O2` por defecto y `-O0` para desactivarlo.
- [ ] 4. Literales hexadecimales `0xDFF000` y binarios `%1010` / `0b1010`.
- [ ] 5. `break` y `continue` (con error si están fuera de un bucle).
- [ ] 6. Rangos descendentes: `for i in (10..1)` con límites constantes, y `step` para el resto.
- [ ] 7. Enums con valores negativos.
- [ ] 8. Asignación anidada `a.b.c = x` (structs dentro de structs).
- [ ] 9. Propiedades de ventana booleanas (`closegadget true`, `sizegadget false`...).
- [ ] 10. `On Key` en el `EventLoop` (añadir `IDCMP_RAWKEY`/`VANILLAKEY` al abrir la ventana) y `key_raw`/`key_text`.
- [ ] 11. Floats: tipo `Float` (C `float`, soft-float en 68000), literales `1.5`, operaciones,
      conversión a texto y `Int()`/`Float()`.
- [ ] 12. Memoria (1/4): runtime de strings con cabecera, lista de temporales, `_dash_str_set`,
      liberación por marca. Tests en el PC (`tests/runtime/host_harness.c`).
- [ ] 13. Memoria (2/4): codegen: asignaciones a String, liberación al salir de bloques, funciones,
      `return`, `break`/`continue`; marcas por vuelta de bucle y de `EventLoop`.
- [ ] 14. Memoria (3/4): escapes (arrays, campos, llamadas al sistema, `@native`), prueba de un bucle
      que concatena 100.000 veces sin crecer.
- [ ] 15. Memoria (4/4): listas y structs con contador de referencias; listas temporales por vuelta.
- [ ] 16. Builtins: `window_*` (9) y `dir_change`/`dir_current`.
- [ ] 17. Builtins: diálogos ASL `dialog_file`, `dialog_font`, `dialog_color`.
- [ ] 18. Builtins: gadgets GadTools `button_*`, `checkbox_*`, `slider_*`, `textfield_*`, `listview_*`.
- [ ] 19. Builtins: `bitmap_*` (crear, liberar, copiar, con máscara, cargar/guardar IFF).
- [ ] 20. Builtins: `bob_*`.
- [ ] 21. Builtins: `copper_*` (lista de copper de usuario, `UCopList`).
- [ ] 22. Builtins: `sound_*` y `tone_play` (audio.device).
- [ ] 23. Builtins: `music_*` (reproductor de módulos ProTracker).
- [ ] 24. Documentación final: README, ROADMAP, QUICK_REFERENCE, MANUAL_REFERENCIA, CLAUDE.md local.

## Bitácora

<!-- Una entrada por iteración:
### YYYY-MM-DD — Tarea N
- Base: tests X, ejemplos Y/30
- Hecho: ... (test: tests/...)
- Probado en emulador: sí/no
- Pendiente: ...
-->

### 2026-10-14 — Tarea 1 (salida común de error)
- Base: tests 58/58, ejemplos 30/30. Después: tests 59/59, ejemplos 30/30.
- Hecho (test: `tests/test_exit_cleanup.dash`, ventana abierta dentro de una función):
  - Cada programa tiene `_dash_exit_cleanup()`: cierra ventanas abiertas, ReAction, pantalla,
    GadTools/ASL, pool y librerías. Comprueba cada cosa antes de cerrarla, así que llamarla con
    algo a medio abrir es seguro. `main` la llama al final.
  - `_dash_exit(código)` = limpieza + `exit()`. La usan el fallo al abrir librerías (10) y el fallo
    de `OpenWindowTags` (20), que antes salía con `return 20` sin liberar casi nada (y en una función ni compilaba bien).
  - `_ra_close_libs` deja los punteros a NULL: ya no cierra dos veces si se llama otra vez.
- Probado en emulador: no (tarea 2).

### 2026-10-14 — Tarea 2 (emulador)
- Base: tests 59/59, ejemplos 30/30. Después: 59/59 normales + 14 `emu/` = 73/73, ejemplos 30/30.
- Hecho:
  - `tools/emu_run.py`: compila (o copia) programas, los ejecuta todos en un solo arranque de FS-UAE
    sin ventana (`SDL_VIDEODRIVER=offscreen`) y devuelve la salida y el código de retorno de cada uno.
    ROM: `$DASH_KICKSTART` o `--kickstart`; sin ella, el AROS que trae FS-UAE. Unos 7 s por arranque.
  - Funciona con el Kickstart 3.1 (40.68) de A1200 del usuario y con AROS.
  - Runner: `# expect-out: <línea>` declara la salida exacta; `--emu` ejecuta esos tests en FS-UAE.
    14 tests anotados (salidas revisadas a mano contra el código). `test_builtins_runtime` no, usa `random`.
- Error encontrado al ejecutar por primera vez (no se veía compilando): `Print c` de un carácter
  imprimía una línea vacía. El `Printf` de dos.library lee `%c` como WORD de 16 bits y C pasa un int
  de 32. Ahora `Printf("%lc\n", (LONG)(UBYTE)(c))` (test: `emu/test_loops`).
- Los programas con `EventLoop` esperan al botón de cerrar y se quedan colgados en el emulador
  (salen como TIMEOUT). Para la tarea 3 hace falta una forma de cerrarlos solos.

### 2026-10-14 — Tarea 3 (`-O2` por defecto)
- Base: 73/73 (con `--emu`), ejemplos 30/30. Después: 76/76 con `--emu`, ejemplos 30/30.
- Modo prueba para el emulador: compilar con `DASH_TEST_AUTOCLOSE=<s>` (o `tools/emu_run.py --autoclose <s>`)
  hace que el programa acabe solo con `_dash_exit(0)` pasados esos segundos. `WaitPort`/`Wait` pasan a
  esperar comprobando la hora, y cada vuelta de `while` también la comprueba. Sin la variable no cambia nada.
- Prueba (Kickstart 3.1, A1200): los 30 ejemplos compilados con `-O0` y con `-O2`.
  29 terminan con RC=0 y la salida es idéntica byte a byte entre `-O0` y `-O2`.
  `test_intuition` se queda esperando en un requester (`alert`/`confirm`) en los dos casos: necesita un clic.
  Los 14 tests `emu/` también dan la misma salida con `-O2`. Sin avisos nuevos de GCC con `-O2 -Wall`.
- Hecho: `./dash` compila con `-O2` por defecto; `-O0` (`--no-optimize`) lo quita; `-O` se acepta y no cambia nada.
  El runner compila también con `-O2`.
- Error encontrado al ejecutar los ejemplos: `file_write_line` no escribía el salto de línea (todo el fichero
  quedaba en una línea). Ahora `FPuts` + `FPutC('\\n')`, devuelve 0 o -1 (test: `emu/test_fileio_lines`).
- No verificado: lo que se dibuja en pantalla (no hay captura de imagen), solo que no se cuelga y la salida de texto.
- Docs: README (`-O0`, `tools/emu_run.py`, `--emu`), `docs/BUILTINS.md` regenerado.
