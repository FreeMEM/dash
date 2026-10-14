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
   (sin la variable se usa el AROS de FS-UAE). Para lo que necesita Workbench (asl.library...):
   `export DASH_EMU_SYS=~/.cache/dash-emu/sys31` (sacado de `~/Amiberry/HardDrives/system3.1.hdf` con
   `tools/emu_sys_from_hdf.sh`; no va a git). Tests con `# emu-needs: x.library`.
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
- Cabecera de 12 bytes por string (enlace, tamaño y número de serie).
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
- [x] 11. Floats: tipo `Float` (C `float`, soft-float en 68000), literales `1.5`, operaciones,
      conversión a texto y `Int()`/`Float()`.
- [x] 12. Memoria (1/4): runtime de strings con cabecera, lista de temporales, `_dash_str_set`,
      liberación por marca. Tests en el PC (`tests/runtime/host_harness.c`).
- [x] 13. Memoria (2/4): codegen: asignaciones a String, liberación al salir de bloques, funciones,
      `return`, `break`/`continue`; marcas por vuelta de bucle y de `EventLoop`.
- [x] 14. Memoria (3/4): escapes (arrays, campos, llamadas al sistema, `@native`), prueba de un bucle
      que concatena 100.000 veces sin crecer.
- [x] 15. Memoria (4/4): listas y structs con contador de referencias; listas temporales por vuelta.
- [x] 16. Builtins: `window_*` (9) y `dir_change`/`dir_current`. También `MiVentana.close`
      (documentado en MANUAL_REFERENCIA, pero la gramática solo tiene `.open`).
- [x] 17. Builtins: diálogos ASL `dialog_file`, `dialog_font`, `dialog_color`.
- [x] 18. Builtins: gadgets GadTools `button_*`, `checkbox_*`, `slider_*`, `textfield_*`, `listview_*`.
- [x] 19. Builtins: `bitmap_*` (crear, liberar, copiar, con máscara, cargar/guardar IFF).
- [x] 20. Builtins: `bob_*`.
- [x] 21. Builtins: `copper_*` (lista de copper de usuario, `UCopList`).
- [x] 22. Builtins: `sound_*` y `tone_play` (audio.device).
- [x] 23. Builtins: `music_*` (reproductor de módulos ProTracker).
- [x] 24. `./dash --fpu`: compilar para 68881/68882 (`-m68881`, instrucciones de FPU directas, sin
      `runtime/softfloat`), como las versiones FPU de LightWave. Probar en FS-UAE con `fpu=68882` y comparar
      velocidad con la versión sin FPU. Pedido por el usuario el 2026-10-14.
- [ ] 25. Optimización (1/3) — medir: `tests/bench/` con programas que cronometran en FS-UAE (ReadEClock o
      contador de VBlank) bucles de enteros, Float, strings, arrays, structs, llamadas y gráficos, más el tamaño de
      cada ejecutable. Guardar la tabla base en la bitácora. CPU de la prueba: 68000 (A500) y 68020 (A1200).
      Pedido por el usuario el 2026-10-14: "un lenguaje que aproveche muy bien la máquina".
- [ ] 26. Optimización (2/3) — ciclos, función por función: cada función del runtime (`DashString_*`,
      `DashArray_*`, `_dash_str_*`, `_dash_tmp_*`, objetos, Float, gráficos...) con su microbenchmark en
      `tests/bench/` (ciclos por llamada en 68000 y 68020) y su ensamblador (`-S`); mejorarlas una a una y
      guardar antes/después en `tests/bench/results.json` (versión = commit). Revisar también el C generado.
      Ideas a medir una a una: plantillas que evalúan un argumento dos veces (`gfx_text`), `DashArray_get/set`
      como macros o `static inline` con la comprobación de límites barata, no marcar/soltar temporales en funciones
      y bucles que no crean strings ni objetos, `WORD` donde baste en 68000 (multiplicación 16x16), `-fomit-frame-pointer`,
      `-m68000` vs `-m68020` por defecto, `-fno-...` que estorben, divisiones y módulos por potencias de 2, `Print`
      sin `Printf` cuando el formato es fijo. Cada cambio con antes/después de la tabla de la tarea 25.
- [ ] 27. Optimización (3/3) — memoria y tamaño: cabeceras de strings/objetos, tamaño de puddle del pool,
      runtime que no se usa (secciones, `-ffunction-sections -Wl,--gc-sections` si el linker de Amiga lo admite),
      `-Os` frente a `-O2` por programa, código de arranque de libnix, strings duplicados. Antes/después en bytes.
- [ ] 28. Artefacto de comparativas: página publicada (Artifact) con las tablas y gráficas de
      `tests/bench/results.json`: ciclos por función y por programa, tamaño de ejecutables y memoria, antes y
      después, por versión (commit), para ver cómo evoluciona. Script que la regenere (`tools/bench_report.py`).
- [ ] 29. Documentación final: README, ROADMAP, QUICK_REFERENCE, MANUAL_REFERENCIA, CLAUDE.md local.

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

### 2026-10-14 — Tarea 11 (Float)
- Base: 100/100 con `--emu`, ejemplos 30/30. Después: 105/105 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_float` con salida en FS-UAE; `errors/float_in_int_var`, `errors/float_modulo`,
  `errors/float_array`):
  - `FloatLiteral` (`FLOAT.2`: dígitos a los dos lados del punto, para que `1..10` siga siendo rango),
    tipo `Float` → C `float` en variables, parámetros, retornos, campos, globales y `const`.
  - `Int(x)` (trunca) y `Float(x)`. Mezcla Int/Float como en C. `_is_float_expr()` en el codegen,
    `DashType.FLOAT` en el analyzer (que ahora también infiere `+ - * /` entre enteros como INT).
  - `DashString_from_float`: unos 7 dígitos significativos, quita ceros (`1.5`, `2.0`, `0.333333`,
    `1.0e-5`, `1.0e9`); probado en el PC con 19 valores y en FS-UAE.
  - Errores: Float en una variable Int, `%` con Float, Float en arrays.
- Problema encontrado en el emulador: con libnix `-lm` las operaciones llaman a `mathieeesingbas.library`
  de la ROM, y con el Kickstart 3.1 original (CRC32 1483A091) sin FPU `IEEESPMul` no vuelve nunca
  (probado con CPU exacta, 68020 y 68030). Con 3.2.3, con AROS o con FPU funciona. Solución: el
  `fp-bit.c` de libgcc (GPL + excepción de runtime) en `runtime/softfloat/`, compilado una vez en
  `build/` (`compiler/softfloat.py`) y enlazado solo si el programa usa Float. ~3,7 KB.
- No verificado: si el cuelgue de `mathieeesingbas` 3.1 pasa también en un A1200 real o es del emulador.

### 2026-10-14 — Tarea 12 (memoria 1/4: runtime de strings)
- Base: 105/105 con `--emu`, ejemplos 30/30. Después: igual (el codegen aún no llama a las funciones nuevas).
- Hecho (en `MEMORY_RUNTIME`; test: `runtime/host`, con contador de bloques vivos en los stubs del harness):
  - Cabecera `_DashStrHdr` de 12 bytes delante de cada string creado en ejecución: enlace, tamaño
    (para `FreePooled`, con un bit `KEEP` de "escapado") y número de serie.
  - Lista de temporales (lo nuevo primero). Las marcas son números de serie, no punteros: sacar un
    temporal del medio de la lista (al asignarlo) no rompe ninguna marca. `_dash_tmp_mark/_release`.
  - `_dash_str_set(&var, v)`: adopta un temporal o copia cualquier otro valor (literales incluidos) y libera
    el texto anterior. `_dash_str_keep` / `_keep_owned` (escape), `_dash_str_ret` y `_dash_tmp_release_keep`
    (valor de retorno que sobrevive a la limpieza de la función). `DashString_concat` crea temporales.
  - Probado en el PC: un bucle de 1000 concatenaciones deja un solo bloque vivo; adopción, copia, escape,
    retorno y marcas con huecos. Sin errores con AddressSanitizer.
- Cabecera de 12 bytes y no 8 como decía el plan: el número de serie hace falta para que las marcas sean seguras.

### 2026-10-14 — Tareas 13 y 14 (memoria 2/4 y 3/4: codegen de strings y escapes)
- Base: 105/105 con `--emu`, ejemplos 30/30. Después: 107/107 con `--emu`, ejemplos 30/30.
- Las dos tareas van juntas: soltar temporales sin tratar los escapes habría dejado punteros colgando
  (títulos de ventana, arrays) entre una y otra.
- Hecho (test: `test_string_memory`, en FS-UAE con Kickstart 3.1):
  - Variables String locales, globales (`var g: String`, se inicializan al empezar `main`) y campos String de
    structs (también en el constructor): `_dash_str_set`. Las variables de bucle solo toman prestado.
  - `CodeGenContext` lleva por cada scope sus Strings propios y su tipo (`main`, `block`, `loop`, `func`,
    `handler`). Se liberan al final del bloque, antes de `break`/`continue` (hasta el bucle) y de `return`
    (hasta la función). `return` calcula el valor primero (`__typeof__`) y un String devuelto sobrevive como
    temporal del que llama (`_dash_str_ret` + `_dash_tmp_release_keep`).
  - Marca de temporales por bucle (`while`, `for`, `for each`, `for` de caracteres): se liberan al empezar cada
    vuelta y al salir; también por mensaje del `EventLoop` y al salir de funciones, métodos y lambdas.
    Sin strings en el programa, `_dash_tmp_mark/_release` son macros vacías.
  - Parámetros String que la función reasigna: se copian al entrar (el original es del que llama).
  - Escapes (`_dash_str_escape`: el temporal pasa a permanente o se copia; los literales no): elementos de arrays,
    argumentos de `@native`/`@extern`, builtins que pueden guardar el puntero (todos salvo `_STRING_READERS`:
    texto, ficheros...), campos no String y lo que devuelve una lambda.
  - Contra alias: un global o un campo String pasado a una función Dash va como copia temporal.
  - `On Close` va entre llaves (antes una declaración justo después del `case` no compilaba).
- Probado en FS-UAE: 100.000 concatenaciones + 10.000 vueltas con funciones, campos, globales, `break` y
  `continue`: la memoria libre no baja (< 8 KB). Con el compilador anterior el mismo programa gastaba 8,6 MB.
  Los 29 ejemplos que no esperan un clic terminan con RC=0 y la misma salida que antes.
- Pendiente: los builtins cuya plantilla usa `${str}` dos veces (`gfx_text`: `Text(rp, s, strlen(s))`) evalúan
  la expresión dos veces (dos concatenaciones); no pierde memoria, solo tiempo.

### 2026-10-14 — Tarea 15 (memoria 4/4: arrays y structs)
- Base: 107/107 con `--emu`, ejemplos 30/30. Después: 109/109 con `--emu`, ejemplos 30/30.
- Hecho (tests: `test_object_memory` en FS-UAE, `runtime/host` con objetos):
  - Cabecera de objeto de 20 bytes (enlace y serie de temporal, contador, tamaño, `destroy`), en `MEMORY_RUNTIME`
    (comparte los números de serie con los strings; `_dash_tmp_release` suelta los dos).
  - Objeto nuevo = temporal con contador 0; `_dash_obj_set` en variables, globales `var x: Struct` y campos struct
    (también en el constructor) lo adopta (+1) y suelta el anterior. Al llegar a 0, `destroy` libera los datos del
    array o los campos String y struct del struct. Variables de arrays/structs se sueltan al acabar su bloque, en
    `break`/`continue`/`return`, igual que los strings.
  - `return` de un objeto: se retiene, se limpian locales y temporales y `_dash_obj_float` lo deja como temporal del que llama.
  - Escapes: objetos guardados en arrays, dados a `@native`/builtins o devueltos por lambdas: una referencia que nunca
    se suelta. `refcount`/`retain`/`release` no cuentan como escape.
  - Analyzer: una función sin tipo de retorno que hace `return Struct(...)` ya se reconoce como de ese struct
    (para `a.b.c = x`).
- Probado en FS-UAE: 20.000 vueltas creando structs anidados, arrays y trozos `a[1:3]`, con funciones que los
  devuelven: la memoria no baja (< 8 KB); con el compilador anterior perdía 2,6 MB. Los 29 ejemplos terminan con
  RC=0; solo cambian los contadores que imprime `test_memory`, que ahora suben solos (ejemplo actualizado y sin el
  `release` manual que habría liberado una variable en uso).
- Pendiente: strings dentro de arrays siguen siendo permanentes; alias de un global o campo struct pasado a una
  función que reasigna ese global (el string sí está protegido, el objeto no).

### 2026-10-14 — Tarea 16 (ventanas por número, `Win.close`, directorios)
- Base: 109/109 con `--emu`, ejemplos 30/30. Después: 111/111 con `--emu`, ejemplos 30/30. Builtins sin código: 72 → 60.
- Hecho (test: `test_window_handles` en FS-UAE):
  - `WINMGR_RUNTIME`: tabla de 16 ventanas; `window_create` (flags 1 redimensionable, 2 sin bordes, 4 sin cerrar),
    `window_move`/`resize` (absolutos con `ChangeWindowBox`; `MoveWindow`/`SizeWindow` son relativos), `title`,
    `to_front`/`to_back`, `activate`, `close`. Número 0 = ventana actual; números no válidos no hacen nada.
    `_dash_windows_cleanup` las cierra al salir. `close_window()` y `window_close` olvidan el número y el `win_<Nombre>`.
  - `MiVentana.close` (estaba documentado y no existía): nodo `WindowClose`. Dentro de su `EventLoop` también
    termina el bucle, y el bucle interno de mensajes comprueba que la ventana sigue abierta.
  - `DIR_RUNTIME`: `dir_change(path)` y `dir_current()` (ahora devuelve un String temporal en vez de pedir un buffer).
    El directorio inicial (del shell) se restaura al salir y solo se liberan los locks propios.
- Encontrado en el emulador: abrir una ventana de 0x0 cuelga Intuition 3.1 → tamaño mínimo 40x20.
- Aviso: `dir_change("VOLUMEN:")` de un volumen que no existe abre el requester del sistema "inserte el volumen"
  y espera a que alguien lo cierre (comportamiento normal de AmigaOS).

### 2026-10-14 — Tarea 17 (diálogos ASL)
- Base: 111/111 con `--emu`, ejemplos 30/30. Después: 115/115 con `--emu` (con `DASH_EMU_SYS`), ejemplos 30/30.
  Builtins sin código: 60 → 57.
- Hecho (tests: `test_dialogs`, `test_dialogs_asl` con `# emu-needs: asl.library`):
  - `dialog_file(title, pattern, save)` → ruta completa o `""`; `dialog_font(title)` → `"nombre.font/tamaño"` o `""`;
    `dialog_color(title, inicial)`: asl.library 3.1 no tiene selector de color, así que es una ventana propia con la
    paleta de la pantalla (ratón, flechas + Return; Esc/cerrar devuelve el inicial).
  - asl.library se abre en el primer uso (antes solo la abría la plantilla de GadTools: `file_open_dialog` fallaba
    siempre en los demás programas) y se cierra en `_dash_exit_cleanup`.
- Banco de pruebas: el usuario tiene discos duros con Workbench en `~/Amiberry/HardDrives/`. `tools/emu_sys_from_hdf.sh`
  saca `Libs/` y `C/Assign`, `C/MakeDir` (con amitools) a `~/.cache/dash-emu/sys31`; `emu_run.py` los copia al disco
  emulado (`$DASH_EMU_SYS`), crea `Fonts`, `Locale`, `Devs/Keymaps` y las asignaciones `ENV:`, `T:`, `LOCALE:`...
  (sin ellas ASL abre un "inserte el volumen" y se queda esperando). `--keep DIR` guarda el disco emulado.
- Los tests pulsan teclas y hacen clic de verdad desde un proceso auxiliar (`input.device`): el botón OK/Cancelar de
  ASL se busca por su `GadgetID` (1 y 2). Esc no cierra el requester de ficheros de ASL 3.1 y Return no cierra el de fuentes.

### 2026-10-14 — Tarea 18 (gadgets por número, `On Gadget`)
- Base: 115/115 con `--emu`, ejemplos 30/30. Después: 117/117 con `--emu`, ejemplos 30/30. Builtins sin código: 57 → 41.
- Hecho (test: `test_gadgets`, clics reales con `input.device` en FS-UAE):
  - `GADGET_RUNTIME`: tabla de 64 gadgets; cada uno en su propia lista GadTools (contexto + gadget) añadida en el
    momento (`AddGList`), así se crean en cualquier momento sin `gt_init`/`gt_attach`. Ventana: 0 = actual o número
    de `window_create`. `button_*`, `checkbox_*`, `slider_*`, `textfield_*` (get devuelve String temporal),
    `listview_*` (los textos de la lista escapan, son permanentes), `gadget_id()` (builtin nuevo).
  - `On Gadget` en el `EventLoop` (nodo `OnGadgetHandler`). Con gadgets, el `EventLoop` usa `GT_GetIMsg`/`GT_ReplyIMsg`,
    atiende `IDCMP_REFRESHWINDOW` y actualiza el estado del gadget antes de responder el mensaje.
- Errores encontrados en el emulador:
  - Al salir se colgaba: `AddGList` encadena las listas y `FreeGadgets` de la primera seguía hasta la segunda
    (doble liberación). Se guarda el último gadget de cada lista y se corta la cadena antes de liberar.
  - En ventanas GimmeZeroZero (todas las de Dash) los gadgets ya van en el área interior: sumar el borde los
    desplazaba (el clic en la casilla caía en el botón).
  - GadTools no admite GZZ: el listview calcula la fila con la posición exterior del ratón (una o dos filas de más).
    `_dash_listview_row` la calcula bien (`GTLV_Top` + altura de la fuente) y corrige el resaltado.
  - La limpieza de GadTools usaba `_dash_win` aunque la ventana ya estuviera cerrada; la limpieza final ahora pone
    `_dash_win` a NULL al cerrar las ventanas declaradas.
- Pendiente: los `gt_*` antiguos tienen el mismo problema de GZZ en su listview (no se tocan en esta tarea).

### 2026-10-14 — Tarea 19 (bitmaps)
- Base: 117/117 con `--emu`, ejemplos 30/30. Después: 119/119 con `--emu`, ejemplos 30/30. Builtins sin código: 41 → 33.
- Hecho (test: `test_bitmaps` en FS-UAE): `BITMAP_RUNTIME` con 32 bitmaps (`AllocBitMap` + `RastPort` propio).
  `bitmap_create/free`, `bitmap_draw_to/draw_screen` (desvían `_dash_rp`), `bitmap_blit` (`BltBitMapRastPort`),
  `bitmap_blit_mask` (`BltMaskBitMapRastPort` con el primer plano de otro bitmap del mismo ancho),
  `bitmap_load` (IFF ILBM: BMHD, CMAP, BODY plano o ByteRun1, con comprobación de límites; en pantalla propia
  aplica la paleta) y `bitmap_save` (ILBM sin comprimir con la paleta de la pantalla).
- Probado: píxeles dentro del bitmap, tras el blit y tras el blit con máscara; guardar + cargar; un ILBM ByteRun1
  generado byte a byte; fichero inexistente → 0. El IFF guardado se validó en el PC con otro lector (cabeceras,
  tamaños y píxeles).

### 2026-10-14 — Tarea 20 (bobs)
- Base: 119/119 con `--emu`, ejemplos 30/30. Después: 121/121 con `--emu`, ejemplos 30/30. Builtins sin código: 33 → 25.
- Hecho (test: `test_bobs` en FS-UAE): los bobs reutilizan los bitmaps (misma id = su imagen). Máscara automática
  (OR de los planos: color 0 transparente) rehecha cuando la imagen cambia (`_dash_bitmap_version`), fondo guardado
  con `ClipBlit` (respeta las capas de la ventana) y dibujo con `BltMaskBitMapRastPort`. Tira de frames cuadrados
  para `bob_frame`; `bob_collision` por cajas y luego máscara a máscara. `bob_draw` borra antes el dibujo anterior;
  `bob_free` lo quita de la pantalla.
- Error previo encontrado: una función sin tipo que devuelve una concatenación (`return "" + x`) se imprimía como
  número (el puntero): `_call_returns_string` solo miraba literales. Ahora usa el tipo deducido de la función.

### 2026-10-14 — Tarea 21 (copper)
- Base: 121/121 con `--emu`, ejemplos 30/30. Después: 122/122 con `--emu`, ejemplos 30/30. Builtins sin código: 25 → 18.
- Hecho (test: `test_copper` en FS-UAE): `COPPER_RUNTIME` con una `UCopList` (`UCopperListInit`, `CMove`/`CWait` +
  `CBump`) instalada en el ViewPort de la pantalla actual (`vp->UCopIns` + `RethinkDisplay`). `copper_free` la quita
  (UCopIns a NULL, `RethinkDisplay`, `FreeCopList`) y la limpieza final lo hace antes de cerrar la pantalla propia.
- Probado: las instrucciones aparecen en la lista de copper real del sistema (`GfxBase->LOFlist`) tras instalar y
  desaparecen tras `copper_free`. Con pantalla propia, dos ejecuciones seguidas saliendo con la lista instalada.
- No verificado: el efecto visual (no hay captura de pantalla).

### 2026-10-14 — Tarea 22 (sonido)
- Base: 123/123 con `--emu`, ejemplos 30/30. Después: 125/125 con `--emu`, ejemplos 30/30. Builtins sin código: 18 → 8 (solo `music_*`).
- Hecho (test: `test_sound` en FS-UAE): `SOUND_RUNTIME` con audio.device: los 4 canales se reservan al primer uso
  (mapa 15), una petición `CMD_WRITE` asíncrona por canal (`BeginIO`, `CheckIO`/`WaitIO`, `AbortIO`) y otra de control
  para `ADCMD_PERVOL`. 32 sonidos en memoria chip: `sound_create` + `sound_sample` (builtin nuevo, para llenarlos),
  `sound_load` (IFF 8SVX sin comprimir), `sound_play/loop/stop/playing/volume/period/free`. `tone_play`: seno de 32
  muestras, duración en milisegundos (el manual decía "ticks"; corregido). Reloj PAL/NTSC según `GfxBase->DisplayFlags`.
  Al salir: parar canales, cerrar el device (devuelve los canales) y liberar.
- Probado en FS-UAE (la emulación de Paula corre aunque no haya salida de audio en el PC): un sonido de 0,25 s
  termina, uno en bucle sigue hasta `sound_stop`, `tone_play` dura lo pedido, el 8SVX generado carga y suena.
- No verificado: que se oiga bien (el emulador corre sin audio).

### 2026-10-14 — Tarea 23 (música MOD)
- Base: 125/125 con `--emu`, ejemplos 30/30. Después: 127/127 con `--emu`, ejemplos 30/30. Builtins sin código: 8 → 0.
- Hecho (test: `test_music`, un módulo de dos patrones generado byte a byte, en FS-UAE): `MUSIC_RUNTIME`, reproductor
  ProTracker propio: el módulo entero en memoria chip, servidor de interrupción VBlank (`AddIntServer(INTB_VERTB)`)
  con acumulador para los BPM, canales reservados por audio.device y escritos directamente en Paula (DMA off,
  4 líneas de espera, punteros, DMA on; el bucle del instrumento al tick siguiente). Efectos 0-6, 9, A-D, F, E1/E2/EA/EB/EC.
  `music_pos()` y `music_row()` nuevos (para saber por dónde va).
- Error real encontrado: un array literal grande (3164 elementos) colgaba el Amiga: el compound literal va a la pila
  y el shell de Kickstart 3.1 da 4 KB. Los arrays literales con todos los valores constantes son ahora tablas
  `static const` globales (sin pila y sin copia). El test de error `unimplemented_builtin` pasa a comprobar el
  número de argumentos (ya no queda ningún builtin sin implementar).
- No verificado: cómo suena (sin audio en el emulador); sí que avanza, salta (`B01`), pausa y reanuda.
- Pendiente (optimización): pila de 4 KB del shell. Recursión profunda o locales grandes la desbordan; mirar
  `__stack`/`StackSwap` en el arranque de libnix.

### 2026-10-14 — Tarea 24 (`--fpu`)
- Base: 127/127 con `--emu`. Después: igual (sin tests nuevos en el runner; el runner no varía la CPU emulada).
- Hecho: `./dash --fpu` añade `-m68020 -m68881` y no enlaza `runtime/softfloat` (GCC usa instrucciones de FPU; el
  enlazador toma libnix `libm020`/FPU). `tools/emu_run.py --fpu` para compilar así (con `--set fpu=68882`).
- Probado en FS-UAE: `test_float` compilado con `--fpu` en un A1200 con 68882 da la misma salida que la versión sin FPU.
  Bucle de 20.000 vueltas con 2 multiplicaciones y 1 suma: software 433 ticks (8,7 s) a velocidad real; con FPU 2
  ticks, pero FS-UAE no cuenta los ciclos reales de la FPU, así que esa cifra no vale como medida. Tamaño: 9.396 →
  4.992 bytes.
- Sin FPU: libnix (`__fpucheck`, antes de `main`) muestra un Alert de sistema (0x68881) y sale con 20. Probé un
  constructor propio para avisar con texto, pero GCC guarda registros de la FPU al entrar en `main` y libnix ya lo
  comprueba antes: se quitó.
- Para la tarea 26: `fp-bit.c` es lento (unos 145 µs por operación en un 68020 a 14 MHz). Merece unas rutinas
  propias de suma/multiplicación en enteros de 32 bits.
