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
- [x] 4. Literales hexadecimales `0xDFF000` / `$DFF000` y binarios `0b1010`.
- [x] 5. `break` y `continue` (con error si están fuera de un bucle).
- [x] 6. Rangos descendentes: `for i in (10..1)` con límites constantes, y `step` para el resto.
- [x] 7. Enums con valores negativos.
- [x] 8. Asignación anidada `a.b.c = x` (structs dentro de structs).
- [x] 9. Propiedades de ventana booleanas (`closegadget true`, `sizegadget false`...).
- [x] 10. `On Key` en el `EventLoop` (añadir `IDCMP_RAWKEY`/`VANILLAKEY` al abrir la ventana) y `key_raw`/`key_text`.
- [ ] 11. Floats: tipo `Float` (C `float`, soft-float en 68000), literales `1.5`, operaciones,
      conversión a texto y `Int()`/`Float()`.
- [ ] 12. Memoria (1/4): runtime de strings con cabecera, lista de temporales, `_dash_str_set`,
      liberación por marca. Tests en el PC (`tests/runtime/host_harness.c`).
- [ ] 13. Memoria (2/4): codegen: asignaciones a String, liberación al salir de bloques, funciones,
      `return`, `break`/`continue`; marcas por vuelta de bucle y de `EventLoop`.
- [ ] 14. Memoria (3/4): escapes (arrays, campos, llamadas al sistema, `@native`), prueba de un bucle
      que concatena 100.000 veces sin crecer.
- [ ] 15. Memoria (4/4): listas y structs con contador de referencias; listas temporales por vuelta.
- [ ] 16. Builtins: `window_*` (9) y `dir_change`/`dir_current`. También `MiVentana.close`
      (documentado en MANUAL_REFERENCIA, pero la gramática solo tiene `.open`).
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

### 2026-10-14 — Tarea 4 (hexadecimal y binario)
- Base: 76/76 con `--emu`, ejemplos 30/30. Después: 63/63 sin emulador (+16 `emu/`), ejemplos 30/30.
- Hecho (tests: `test_hex_literals` con `expect-out` en FS-UAE, `errors/hex_too_big`):
  - `0xDFF000`, `$DFF000` (estilo Amiga) y `0b1010`, en expresiones, `const`, propiedades de ventana y enums.
  - `parse_int()` en el transformer; más de 32 bits es error ("does not fit in 32 bits").
  - `c_int_literal()` en el codegen: de 0x80000000 a 0xFFFFFFFF sale `((LONG)0x...UL)` (conserva los bits,
    `0xFFFF0000` vale -65536) y los negativos entre paréntesis.
- Descartado: `%1010` para binario, choca con el operador módulo (`a %10`).
- Docs: MANUAL_REFERENCIA (ya decía `0xFF` sin funcionar) y QUICK_REFERENCE.

### 2026-10-14 — Tarea 5 (`break` y `continue`)
- Base: 63/63 (+16 `emu/`), ejemplos 30/30. Después: 83/83 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_break_continue` con salida comprobada en FS-UAE, `errors/break_outside_loop`,
  `errors/continue_in_handler`):
  - Nodos `BreakStmt`/`ContinueStmt`, terminales `BREAK`/`CONTINUE` (el error lleva línea y columna).
  - Analyzer: `loop_depth`. Funciones, métodos, lambdas y manejadores de `EventLoop` empiezan en 0:
    en C un manejador es un `case` de un `switch`, y `break` saldría del `switch`, no del bucle Dash.
  - Variables llamadas `breaking`/`continued` siguen funcionando; `break` y `continue` pasan a ser palabras reservadas.
- Docs: MANUAL_REFERENCIA y QUICK_REFERENCE.

### 2026-10-14 — Tarea 6 (rangos descendentes y `step`)
- Base: 83/83 con `--emu`, ejemplos 30/30. Después: 86/86 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_range_step` con `expect-c` y salida en FS-UAE, `errors/step_zero`):
  - `(a..b)` baja cuando los dos límites son constantes (literal, negativo o `const`) y `a > b`.
    Con límites variables sigue subiendo: `(1..n)` con `n = 0` no da vueltas, como antes (no rompe código existente).
  - `(a..b step s)`: con `s` constante el C usa `<=`/`>=` y `++`/`--`/`+= s`; con `s` variable se evalúa
    una vez y su signo decide la dirección. `step 0` es error.
  - `constant_int()` en `ast_nodes.py` (literal, negación o `const`), compartida por analyzer y codegen.
  - Un fin constante (`const`) ya no crea la variable `_end_`.
- Docs: MANUAL_REFERENCIA y QUICK_REFERENCE.

### 2026-10-14 — Tarea 7 (enums negativos)
- Base: 86/86 con `--emu`, ejemplos 30/30. Después: 88/88 con `--emu`, ejemplos 30/30.
- Hecho (test: `test_enum_negative`, salida comprobada en FS-UAE): `A = -1` (regla `enum_value_neg`),
  también en la forma de una línea con comas; después de un negativo se sigue contando (`-1`, `0`).
  Los valores salen por `c_int_literal()`: negativos entre paréntesis y hexadecimales grandes con sus 32 bits.
- Docs: MANUAL_REFERENCIA.

### 2026-10-14 — Tarea 8 (asignación anidada `a.b.c = x`)
- Base: 88/88 con `--emu`, ejemplos 30/30. Después: 92/92 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_nested_assign` con salida en FS-UAE; `errors/nested_assign_not_struct`,
  `errors/member_assign_no_field`):
  - Gramática: `ID ("." ID)+ = expr` y `self ("." ID)+ = expr`. `MemberAssign.target` guarda el dueño
    del último campo, construido igual que una lectura (`MemberAccess`/`PropertyAccess`), así el C sale
    de `_generate_expression`: `e->caja->peso = 9;`.
  - Analyzer: `Symbol.struct_name` (de constructores, funciones con retorno struct, parámetros y globales
    con tipo, `self` en métodos) y `_struct_name_of()`. Error si un paso intermedio no es un struct conocido
    (antes habría salido C inválido) o si el struct no tiene ese campo (también con un solo nivel).
  - Esta información de tipos servirá para la gestión de memoria (tareas 12-15).
- Docs: MANUAL_REFERENCIA ("Structs dentro de structs") y QUICK_REFERENCE.

### 2026-10-14 — Tarea 9 (propiedades de ventana booleanas)
- Base: 92/92 con `--emu`, ejemplos 30/30. Después: 97/97 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_window_bool_props` con `expect-c` y salida en FS-UAE; `errors/window_prop_type`,
  `errors/window_prop_unknown`, `errors/window_member_unknown`):
  - `true`/`false` como valor de propiedad. Nuevas: `sizegadget` (con límites de tamaño para que se pueda
    redimensionar de verdad), `borderless`, `activate`. `WindowDef.PROPERTY_KINDS` lista nombres y tipos.
  - Analyzer: propiedad desconocida (antes una errata como `widht` se ignoraba en silencio) o de tipo equivocado → error.
  - Error previo encontrado al probar: `Print Panel.width` generaba C inválido (`Panel->width`).
    Ahora `Win.width/height/left/top/title` leen la ventana abierta o, si está cerrada, la definición.
- No verificado: que `sizegadget` se vea y funcione (no hay captura de pantalla); el C y la ejecución sí.
- Pendiente (tarea 16): `MiVentana.close` está documentado pero no existe en la gramática.

### 2026-10-14 — Tarea 10 (`On Key`, `key_raw`, `key_text`)
- Base: 97/97 con `--emu`, ejemplos 30/30. Después: 100/100 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_on_key`, `errors/on_key_unknown`):
  - `On Key` (cualquier tecla), `On Key "a"` (carácter según el keymap), `On Key "ESC"` (nombres en
    `KEY_NAMES`) y `On Key 0x4C` (código raw). Todos los `On Key` de un `EventLoop` en un único
    `case IDCMP_RAWKEY` (antes dos handlers repetían la etiqueta del `case`); las teclas al soltarse se ignoran.
  - `KEY_RUNTIME`: `_dash_key_record()` guarda el código y traduce con `MapRawKey` (keymap.library, abierta
    al primer uso y cerrada en `_dash_exit_cleanup`) antes de `ReplyMsg`. `key_raw()` y `key_text(code)`
    implementados (quedan 70 builtins sin código).
  - Prescan: si el programa usa teclas, la ventana se abre ya con `IDCMP_RAWKEY`. Antes `key_get`/`key_wait`
    nunca recibían teclas porque nadie pedía ese evento.
  - Error previo arreglado: `_dash_key_pressed` leía `msg->Class` después de `ReplyMsg`.
- Probado en FS-UAE de punta a punta: el test escribe en su propia ventana con `input.device`
  (`IND_WRITEEVENT`) y los handlers reciben "a", 0x21 ("s") y ESC. Ejemplos con gráficos siguen terminando con RC=0.
