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
   (sin la variable se usa el AROS de FS-UAE). Benchmarks: `tools/bench.py` (A500 con
   `export DASH_KICKSTART_A500=~/.cache/dash-emu/kick/kick31_a500.rom`, CRC FC24AE0D; A1200 con `DASH_KICKSTART`);
   `--save "etiqueta"` guarda la ejecución en `tests/bench/results.json`. `run_tests.py --emu-a500` ejecuta los tests de
   salida también en un A500 (68000): úsalo cuando cambie el runtime o el codegen. Para lo que necesita Workbench (asl.library...):
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
- [x] 25. Optimización (1/3) — medir: `tests/bench/` con programas que cronometran en FS-UAE (ReadEClock o
      contador de VBlank) bucles de enteros, Float, strings, arrays, structs, llamadas y gráficos, más el tamaño de
      cada ejecutable. Guardar la tabla base en la bitácora. CPU de la prueba: 68000 (A500) y 68020 (A1200).
      Pedido por el usuario el 2026-10-14: "un lenguaje que aproveche muy bien la máquina".
- [x] 26. Optimización (2/3) — ciclos, función por función. Partes: 26a marcas de temporales (bucles y
      funciones), 26b arrays (`DashArray_get/set`, `%`, for-each), 26c strings (concat, interpolación, from_int, set),
      26d Float por software (rutinas propias), 26d2 suma y multiplicación Float en ensamblador 68000, 26d3 suma y multiplicación Float con menos ciclos
      (exponente sin desplazar, mantisa `<< 8` para que el producto alto ya sea la mantisa, menos registros; meta: la
      suma de la ROM, `IEEESPAdd`, que en A500 da 88.865 ns frente a 125.864 de la mía), 26e llamadas y return, 26e2 no marcar/soltar temporales en bucles y funciones que no los crean (repaso del C
      final, hecho), 26f gráficos y texto (plantillas con `${str}`
      doble). Detalle original:: cada función del runtime (`DashString_*`,
      `DashArray_*`, `_dash_str_*`, `_dash_tmp_*`, objetos, Float, gráficos...) con su microbenchmark en
      `tests/bench/` (ciclos por llamada en 68000 y 68020) y su ensamblador (`-S`); mejorarlas una a una y
      guardar antes/después en `tests/bench/results.json` (versión = commit). Revisar también el C generado.
      Ideas a medir una a una: plantillas que evalúan un argumento dos veces (`gfx_text`), `DashArray_get/set`
      como macros o `static inline` con la comprobación de límites barata, no marcar/soltar temporales en funciones
      y bucles que no crean strings ni objetos, `WORD` donde baste en 68000 (multiplicación 16x16), `-fomit-frame-pointer`,
      `-m68000` vs `-m68020` por defecto, `-fno-...` que estorben, divisiones y módulos por potencias de 2, `Print`
      sin `Printf` cuando el formato es fijo. Cada cambio con antes/después de la tabla de la tarea 25.
- [~] 27. Optimización (3/3) — memoria y tamaño. Partes: 27a funciones `static` y `--small` (hecha), 27b pila
      (`__stack` + `swapstack` de libnix; el shell de 3.1 da 4 KB; hecha), 27c pool y cabeceras, 27d bucle de caracteres
      (`string_chars_26` va el doble de rápido con `-Os` que con `-O2`: mirar el C). Detalle original: cabeceras de strings/objetos, tamaño de puddle del pool,
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

### 2026-10-14 — Tarea 25 (optimización 1/3: medir)
- Hecho: `tests/bench/bench_lib.dash` (EClock de timer.device, ~709 kHz), `bench_core.dash` (14 pruebas: bucles, llamadas,
  Float, arrays, structs, strings) y `bench_gfx.dash` (6: píxel, rectángulo, línea, texto, blit, bob). `tools/bench.py`
  las compila, las ejecuta en FS-UAE a velocidad real (A500 68000 con Kickstart 3.1 A500 extraído de los zips del
  usuario —el `ob` era un volcado malo, se usa el `!`—, y A1200 68020), calcula ns por vuelta, mide el tamaño de 32
  ejecutables (pruebas + ejemplos) y guarda en `tests/bench/results.json`. Base guardada: "base (antes de optimizar)".
- Base (ns por vuelta, A500 / A1200): `int_loop` 41.423 / 9.334, `func_call` 82.036 / 18.348, `array_get_set`
  197.203 / 36.216, `string_concat_int` 1.141.401 / 246.752, `float_mul_add` 123.427 / 31.285, `gfx_pixel` 497.871 / 122.221.
  Tamaño total: 250.460 bytes.
- Primeras sospechas para la tarea 26: una vuelta vacía de bucle cuesta ~290 ciclos en el 68000 (la llamada
  `_dash_tmp_release` en cada vuelta aunque el cuerpo no cree temporales), `func_call` ~580 ciclos (marca y
  liberación de temporales en cada función, `__typeof__` en el return), `array_get_set` (llamadas a `DashArray_get/set`
  y `%` en 68000 sin división de 32 bits).

### 2026-10-14 — Tarea 26a (temporales y un fallo grave de GCC en 68000)
- Base: 127/127 con `--emu`. Después: 161/161 con `--emu --emu-a500` (los 34 tests de salida también en un A500).
- Hecho:
  - `_dash_tmp_release(m)` es una macro con vía rápida: si no se creó nada desde la marca (serie igual) no hay llamada.
    A500: `int_loop` 41.423 → 6.663 ns (x6,2), `func_call` 82.036 → 6.617 (x12), `for_each_10` 696.067 → 251.354 (x2,8),
    `string_chars_26` x4,1, `array_get_set` -19 %, `float_mul_add` -28 %, `string_compare` -33 %. A1200 parecido.
- Fallo grave encontrado al medir (el benchmark gráfico colgaba el A500): las macros inline del NDK pasan los argumentos
  en registros fijos (`register asm`). En 68000, `i % 200` o `a * b` de 32 bits es una llamada a libgcc (`__modsi3`,
  `__mulsi3`) que GCC trata como pura y coloca después de cargar esos registros: la llamada los machaca y la función
  del sistema recibe basura (aquí `BltBitMapRastPort`). En 68020 esas operaciones son instrucciones, por eso no se veía.
  Una barrera `asm("" ::: "memory")` no basta (GCC mueve igual una llamada pura).
  - Arreglo: en cada builtin, los argumentos que no son valores simples se calculan antes en temporales `volatile`
    (también evita evaluar dos veces `${str}` en `gfx_text`: `gfx_text_concat` -18 %). `Wait expr` igual.
  - Runtime revisado: dos multiplicaciones de 32 bits dentro de llamadas al sistema (`bitmap_save`, `bob_draw`) pasan a
    temporales `volatile`.
  - Las cifras base de `bitmap_blit_32` eran de código mal compilado (blit con basura, por eso rápido). La medida real
    en A1200 es 645.026 ns.
  - `run_tests.py --emu-a500`: la batería de salida en 68000.
- Pendiente: `@native` del usuario y los módulos de `lib/amiga` pueden tener el mismo problema; documentarlo.
  Tamaño total 250.460 → 260.192 bytes (+3,9 %: la comprobación inline en cada bucle); se mira en la tarea 27.

### 2026-10-14 — Tarea 26b (aritmética entera y arrays)
- Base: 161/161 (`--emu --emu-a500`). Después: 164/164.
- Hecho (test: `test_int_ops`, en A1200 y A500: negativos, cocientes de más de 16 bits, divisores > 65535, productos grandes):
  - `*`, `/`, `%` entre enteros → `_DASH_MUL/_DIV/_MOD`. En 68000: si caben en 16 bits, una instrucción `muls.w`/`divu.w`
    (inline asm); si no, libgcc. En 68020+ (`--fpu`) son los operadores normales. No se usan con constantes potencia de 2
    (desplazamientos) ni en `*` por constante (GCC ya hace sumas y desplazamientos).
  - `for each` sobre arrays: longitud leída una vez, acceso directo a `data[i]` (los arrays no cambian de tamaño), el array
    retenido durante el bucle (un `return` dentro lo suelta).
  - GCC ya hacía inline de `DashArray_get/set`.
- A500 (ns): `array_get_set` 159.859 → 73.957 (x2,2), `for_each_10` 251.354 → 212.802 (-15 %), `gfx_pixel` 476.837 → 394.530
  (-17 %, usa `%`), `gfx_line` -5 %. A1200: `array_get_set` -45 %, `for_each_10` -14 %.
- Tamaño: 260.192 → 261.924 bytes.

### 2026-10-14 — Tarea 26c (strings)
- Base: 164/164 (`--emu --emu-a500`). Después: 167/167 (test nuevo: `test_string_join`, 12 números en una interpolación).
- Hecho:
  - `DashString_join(n, partes)`: una cadena de `+` (y la interpolación) reserva una vez y copia en una pasada, en grupos de
    6 partes (las conversiones de números usan buffers rotativos, ahora 16 por tipo).
  - Caché de bloques pequeños: los strings de hasta 64 bytes (con cabecera) van a listas libres por clase de 16 bytes en
    vez de volver al pool; un bucle que crea un string corto por vuelta reutiliza el mismo bloque.
  - `DashString_from_int`: cada dígito con `divu.w #10` mientras el número quepa (< 655.360), sin libgcc.
  - Harness: los bloques en caché cuentan como libres (`LIVE`); sin errores con AddressSanitizer.
- A500 (ns): `string_concat_int` 1.146.631 → 619.796 (x1,85), `string_interp` 2.244.846 → 786.585 (x2,85),
  `string_return` 1.261.345 → 735.371 (x1,7), `nested_struct_new` -23 %, `gfx_text_concat` -10 %. A1200 parecido.
- Tamaño: 261.924 → 263.864 bytes.
- Pendiente (26e): una concatenación aún cuesta ~4.400 ciclos en 68000; mirar el ensamblador (strlen/memcpy de libnix,
  `_dash_str_set`, la marca del bucle).

### 2026-10-14 — Tarea 26d (Float por software)
- Base: 167/167 (`--emu --emu-a500`). Después: igual.
- Hecho: `runtime/softfloat/fastfp.c`: `__mulsf3`, `__addsf3`, `__subsf3` para el caso normal (24x24 con cuatro `mulu.w`,
  redondeo al par), con los casos especiales a las de fp-bit renombradas por `objcopy` (`__dash_fb_*`).
  `tools/fastfp_check.py` las compara bit a bit con la FPU del PC: 0 diferencias en 9 millones de operaciones.
- Error encontrado: el soft float de Dash solo se enlazaba si el programa imprimía o concatenaba un Float (la marca del
  runtime). Un programa que solo calculaba enlazaba la libm de libnix → `mathieeesingbas.library` de la ROM, la que
  cuelga multiplicando en Kickstart 3.1 sin FPU. Ahora cualquier Float (literal, variable, campo, parámetro, retorno,
  `Float()`) activa el runtime.
- Benchmark nuevo `float_mul` (en `float_mul_add` GCC saca la multiplicación del bucle). A500: `float_mul` 175.275 ns,
  `float_mul_add` 161.701 (antes 88.865, pero eso era la suma de la ROM, en ensamblador, que en 3.1 sí funciona).
  Mis rutinas en C cuestan ~1.150-1.250 ciclos por operación en 68000: hay que bajarlas (26d2).
- Tamaño: 263.864 → 268.464 bytes (programas con Float llevan ahora sus rutinas).

### 2026-10-14 — Tarea 26d2 (en curso: multiplicación Float en ensamblador)
- Hecho: `__mulsf3` escrito a mano en 68000 dentro de `fastfp.c` (cuatro `mulu.w`, `addx` para el acarreo, solo d2-d5
  guardados, sin marco); casos especiales y desbordes a `__dash_fb_mulsf3`. Test nuevo `test_fastfp_amiga` (emu):
  compara multiplicación y suma con fp-bit bit a bit en el propio Amiga, 20.000 pares: 0 diferencias en A1200 y A500.
- Medido (`26d2: __mulsf3 en asm`): `float_mul` A500 175.275 → 152.388 ns, A1200 38.701 → 33.772. Solo un 13 %:
  el desensamblado del bucle es limpio; la rutina cuesta ~960 ciclos en 68000 (cuatro `mulu.w` ~220, sacar
  exponentes con `lsr` ~70, recomponer mantisa y exponente ~340, `movem` ~84). Ideas para 26d3.
- Hecho después: `__addsf3`/`__subsf3` en 68000 (misma lógica que la versión en C). `|x| >= |y|` comparando los
  valores `<< 1`, así solo hacen falta dos comprobaciones de exponente. Sin bit pegajoso cuando la diferencia de
  exponentes es <= 6 (los seis bits de guarda son ceros). Exponente final como `(e - 1) << 23 + mant`, que ya
  lleva el bit implícito. La resta entra por `___subsf3` cambiando el signo; el caso raro salta (`jmp (a1)`) a la
  de fp-bit que toca, suma o resta, con los argumentos intactos en la pila.
- `test_fastfp_amiga` ampliado: resta contra `__dash_fb_subsf3`, y una cuarta parte de los pares con exponentes
  cercanos (-16..15), para pasar por alineación, bit pegajoso, cancelación y acarreo. 0 diferencias en A1200 y A500.
  Prueba de que el test sirve: con el redondeo estropeado a propósito (`cmp.w #0x1F`) da 1.736 diferencias.
- Tests: 170/170 (`--emu --emu-a500`).
- Medido (`26d2: __addsf3/__subsf3 en asm`): `float_mul_add` (en el bucle solo queda la suma) A500 163.428 →
  125.864 ns, A1200 34.715 → 26.389. Aviso: la suma de la ROM (`IEEESPAdd` de `mathieeesingbas.library`, que en 3.1
  sí funciona) medía 88.865 ns en A500; la mía aún cuesta unos 260 ciclos más. Cuento ~710 ciclos por suma: `movem`
  84, sacar exponentes 84, preparar las dos mantisas 104, bit pegajoso ~100, recomponer ~146. Queda para 26d3.
- Tamaño: 268.464 → 268.248 bytes.

### 2026-10-14 — Tarea 26d3 (suma y multiplicación Float con menos ciclos)
- Multiplicación: `ma << 8`, así los 32 bits altos del producto de 56 ya son la mantisa (o les falta un bit) y los
  32 bajos son el resto para redondear (`add.l d5,d5`: C = medio, Z = nada debajo). Exponentes como `e << 7` en la
  palabra alta, sin desplazar; `d2` lleva el signo en el bit 31 y `(e - 1) << 7` abajo, con una sola comparación
  sin signo para el rango. `mid` puede pasar de 32 bits (ah ahora es de 16): su bit 32 entra con `addx.w`.
- Suma: mantisas con el bit implícito en el 31 y ocho bits de guarda; el acarreo vuelve con `roxr`. Solo d2-d3
  guardados (`x` en a0, `y` en a1). Los casos raros llaman a la suma de fp-bit con `x` e `y` (la resta entra como
  `a + (-b)`). El resultado se monta con `move.b e` + `ror.l #8` + `roxr.l #1` con X = signo.
- `test_fastfp_amiga` por tipos de pares (`i & 7`): aleatorios, mismo exponente, exponentes cercanos, mantisas
  cortas (empates exactos, bit suelto) y sumas que acarrean con bit pegajoso. Antes no había ningún empate exacto
  en la multiplicación. Mutaciones (redondeo de la mult., redondeo de la suma, umbral del bit pegajoso, bit
  perdido en el acarreo, bit pegajoso de la alineación, bit 32 de `mid`): las seis dan diferencias (1 a 1.699).
  Además, una pasada de 1.000.000 de pares (3 millones de operaciones) en el emulador: 0 diferencias.
- Medido (`26d3: ...`): `float_mul` A500 152.386 → 122.073 ns, A1200 34.322 → 29.677; `float_mul_add` (suma)
  A500 125.864 → 107.830, A1200 26.389 → 23.451. Desde la versión en C (26d): mult. -30 %, suma -33 %.
- Pendiente: la suma de la ROM sigue más rápida en A500 (88.865 ns, ~135 ciclos menos); en A1200 la mía gana
  (23.451 frente a 33.990). Elegir la de la ROM según la CPU es posible (`AttnFlags`), pero la `mathieeesingbas` de
  3.1 ya falló con la multiplicación en FS-UAE: no me fío sin probarla en hardware real. Lo dejo así.
- Tests: 170/170 (`--emu --emu-a500`).
- Tamaño: 268.248 → 268.144 bytes.

### 2026-10-14 — Tarea 26e (llamadas, return, concatenación, objetos)
- Base: 170/170 (`--emu --emu-a500`). Después: 173/173 (tests nuevos: `test_int_to_string_amiga`).
- Medido primero por piezas (programa propio en el scratchpad, A500): `AllocPooled` + `FreePooled` de 28 bytes 2.026
  ciclos; `DashString_from_int` de 4 cifras 1.409; reservar y soltar un string corto ~640; `"x" + "1234"` con su
  liberación 2.448 (el `memcpy` de libnix es una llamada genérica); bucle vacío 53.
- Hecho:
  - Caché de bloques pequeños común (`_dash_block_get`, `_dash_block_get_clear`, `_dash_block_put`): hasta 64 bytes,
    listas libres por clase de 16 bytes. La usaban solo los strings; ahora también structs, cabeceras de array y sus
    datos (que antes iban siempre al pool). Los bloques de objetos se reciclan borrados, como `MEMF_CLEAR`.
  - `_dash_copy`: copia de menos de 32 bytes en línea (`move.b`/`dbra`) en `DashString_concat` y `_dash_str_dup`.
  - `DashString_from_int`: dos cifras por `divu.w #100` y tabla `"00".."99"` (200 bytes).
  - `-fomit-frame-pointer` con `-O2` (sin `link`/`unlk`, a5 libre). Casi no se nota en las medidas.
  - Harness del PC: `CONST_STRPTR`, lista de bloques en caché genérica. Con AddressSanitizer: 0 errores (las fugas que
    señala son bloques que en el Amiga borra `DeletePool` al salir).
- Probado y descartado: comprobar en la macro `_dash_tmp_release` la cabeza de las dos listas en vez del número de serie
  (evita llamar a `_dash_tmp_release_f` cuando todo se adoptó). La macro crece en cada bucle y función, GCC deja de
  expandir en línea funciones pequeñas (`suma1`) y los bucles sin strings ya no sacan la comprobación: `func_call` x6,
  `int_loop` +40 %. Medido, anotado y deshecho. Lo de fondo es que codegen marca y suelta temporales en todos los bucles
  y funciones: queda como 26e2.
- Medido (A500 ns): `array_literal_new` 894.879 → 452.037 (x2), `struct_new_field` 539.900 → 312.675 (-42 %),
  `nested_struct_new` 1.614.554 → 1.039.195 (-36 %), `string_concat_int` 619.737 → 459.234 (-26 %), `string_interp`
  -17 %, `string_return` -23 %. El resto igual (±1 %). A1200 parecido.
- Tamaño: 268.144 → 269.360 bytes (tabla de cifras y rutinas en línea).

### 2026-10-14 — Tarea 26e2 (sin marcas de temporales donde no hacen falta)
- Base: 173/173 (`--emu --emu-a500`). Después: 174/174 (test nuevo: `test_tmp_marks`).
- Hecho: `compiler/tmp_marks.py`, un repaso del C final (al acabar `generate()`). Calcula qué funciones pueden dejar
  temporales en las listas del que llama: las que meten en ellas (`_dash_otmp_push`, `_dash_tmp_release_keep`,
  `_dash_str_alloc`/`_dash_str_dup` con `temp` distinto de `FALSE`) y las que llaman a esas, hasta no cambiar. Una
  función con su propia marca solo cuenta por lo que devuelve (`_dash_str_ret`, `_dash_obj_float`, `release_keep`).
  Las llamadas a funciones que no están en el fichero (sistema, libc) y por puntero no dejan nada. Un bucle o una
  función sin llamadas de esas pierde la marca y sus liberaciones. Lee también funciones de una línea y firmas en
  varias líneas: comprobado que reconoce todas las definiciones de los 103 tests y ejemplos.
- Runner: `# expect-no-c: <texto>` (el C no debe contenerlo; `\n` = salto de línea).
- Aviso, benchmarks: sin las marcas, GCC calculaba en tiempo de compilación los bucles sin efectos (`int_loop`,
  `while_loop`, `func_call` daban 7 ns) y sacaba del bucle la comparación de `string_compare`. Ahora `bench_lib` tiene
  `bench_sink(x)` (un `move.l` a una variable `volatile`) y esos bucles lo llaman en cada vuelta; `string_compare`
  compara `pal[i % 2]`. Esos cuatro no se comparan con las ejecuciones anteriores.
- Medido el antes justo (mismos benchmarks nuevos, C sin el repaso, A500 ns): `int_loop` 12.649 → 6.940 (-45 %),
  `while_loop` 10.917 → 5.758, `func_call` 10.862 → 5.771, `string_compare` 66.169 → 60.406. Y en la tabla:
  `for_each_10` 209.640 → 86.753 (x2,4), `string_chars_26` 300.862 → 156.235 (x1,9), `array_get_set` -8 %,
  Float -4 %, gráficos -1 %. A1200 parecido.
- Tamaño: 269.360 → 251.620 bytes (-6,6 %): menos código por bucle y función, y más funciones pequeñas en línea.

### 2026-10-14 — Tarea 26f (gráficos y texto)
- Base: 174/174. Después: 179/179 (`--emu --emu-a500`; test nuevo: `test_gfx_pen_cache`, lee los píxeles).
- Medido: casi todo el tiempo de los gráficos está dentro de graphics.library (`WritePixel` ~1.800 ciclos, `Text` de
  11 letras ~27.000, un bob = tres blits ~37.000). Las rutinas de Dash ya hacen lo mínimo. La plantilla con `${str}`
  doble ya iba por un temporal (`volatile`, 26a).
- Probado y descartado: ventana sin `WA_GimmeZeroZero`, y sin GZZ con región de recorte (`InstallClipRegion`). A500:
  igual en todo (±1 %) y la región empeora las líneas (892.465 → 1.629.411 ns). Se queda GZZ.
- Hecho: `gfx_pen`, `gfx_pen_bg` y `gfx_mode` llaman a `SetAPen`/`SetBPen`/`SetDrMd` solo si el valor cambia (lo
  miran en el RastPort actual: `FgPen`, `BgPen`, `DrawMode`). Cada llamada cuesta ~600 ciclos aunque no cambie nada.
  El argumento se evalúa una vez (temporal `volatile`, comprobado con `random()`).
- Benchmark nuevo `gfx_pixel_same_pen` (el bucle típico: color y punto). A500: 2.511 → 1.886 ciclos por punto
  (medido aparte); en la tabla 267.380 ns frente a los ~390.000 de `gfx_pixel`. Cuando el color cambia en cada vuelta
  la comprobación cuesta un 1,5 % (`gfx_pixel` 388.844 → 394.621).
- Tamaño: 251.620 → 252.728 bytes.
- Con esto la tarea 26 queda cerrada. Resumen A500 desde la base (ns): `array_literal_new` 885.694 → 452.097,
  `string_interp` 2.238.460 → 651.378, `string_concat_int` 1.141.401 → 459.880, `for_each_10` 696.067 → 86.753,
  `struct_new_field` 531.440 → 311.913, Float (`float_mul_add`) 123.427 → 104.612. Tamaño 250.460 → 252.728 bytes
  (con 2 benchmarks más y Float propio).

### 2026-10-15 — Tarea 27a (funciones static, `--small`)
- Base: 179/179 (`--emu --emu-a500`). Después: igual; 30/30 ejemplos.
- `dash`: `DASH_CFLAGS` añade opciones a GCC (para pruebas). Medido el total de los 32 programas (benchmarks y
  ejemplos), 252.728 bytes de partida:
  | opciones | bytes |
  |---|---|
  | `-O2` (antes) | 252.728 |
  | `-ffunction-sections -fdata-sections -Wl,--gc-sections` | 234.964 (unos crecen, otros bajan hasta 3 KB) |
  | `-Os` | 231.700 |
  | funciones `static` (hecho) | 230.048 |
  | `static` + gc-sections | 231.060 (ya no aporta) |
  | `static` + `-Os` | 213.852 |
- Hecho: las funciones de usuario y las `@native` se generan `static` (prototipo con `__attribute__((unused))`). Todo
  el programa va en un solo C (también con `--multifile`, que solo compila `main.c`), así que GCC quita las que nadie
  llama, sobre todo de los módulos de `lib/amiga`, y expande en línea las que se llaman una vez. -9 %, ningún
  programa crece (`test_fileio` 10.644 → 7.512, `test_rtg` 11.580 → 8.496).
- `-Os` cuesta velocidad (A500): `for_each_10` +52 %, `gfx_pixel` +17 %, strings +20 %, `array_literal_new` +11 %; solo
  `string_chars_26` mejora (173.412 → 95.682). Por defecto sigue `-O2`; nueva opción `./dash --small` (`-Os`).
  Probados con `--small` en A500 `test_int_to_string_amiga`, `test_tmp_marks` y `test_fastfp_amiga`: misma salida.
- Velocidad con `static` (tabla `27a`): igual (±1 %), `string_return` -3 %; `string_chars_26` +8 % (160.521 →
  173.412): queda para 27d.

### 2026-10-15 — Tarea 27b (pila)
- Base: 179/179. Después: 182/182 (`--emu --emu-a500`; test nuevo: `test_stack_amiga`); 30/30 ejemplos.
- Problema: el shell de Kickstart 3.1 (y un icono sin `Stack`) arranca los programas con 4 KB de pila. Una recursión
  algo honda o un array local grande en un `@native` la desborda y el Amiga se cuelga sin avisar. Comprobado: el test
  nuevo (40 niveles de 256 bytes, ~11 KB) se queda colgado en el emulador sin el cambio.
- Hecho: el C de cada programa pide `__stack = DASH_STACK` y referencia `__stkinit`, lo que enlaza el módulo
  `swapstack` de libnix: antes de `main()` pasa a una pila de ese tamaño si la actual es menor, y vuelve al salir.
  Por defecto 16 KB; `./dash --stack N` la cambia y `--stack 0` lo quita. El test comprueba `tc_SPUpper - tc_SPLower`
  y que la recursión acaba bien, en A1200 y A500; `--stack 32768` probado aparte.
- Coste: 720 bytes por programa (`swapstack` 324 + `__request` 120 + estructura del ejecutable): `hola` 4.276 → 4.996.
  Lo dejo por defecto: un desbordamiento de pila cuelga la máquina; quien quiera los bytes tiene `--stack 0`.
  En memoria, 16 KB más mientras corre el programa (solo si arrancó con menos).
