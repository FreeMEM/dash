# Bucle de consumo de recursos (velocidad y memoria)

Encargo (2026-10-25): optimizar velocidad y memoria del código que genera Dash, medir cada cambio con
`tools/bench.py --save` y anotarlo en el panel de benchmarks (https://claude.ai/artifact/9XyJ1JNSGuDo5q6NCRzM2N,
`tools/bench_report.py` y subir los CSV). Pensar también en máquinas reales con 68040/68060 y tarjetas
gráficas Zorro II/III, no solo en A500/A1200.

Tope: al 90 % del uso semanal (`~/.claude/state/uso-7d.txt`) se para (al empezar estaba en 85 %).

## Tareas

- R1 `./dash --cpu 68020|68030|68040|68060`: código de 68020 afinado para cada CPU (`-m68020 -mtune=...`; la
  toolchain solo trae libnix de 68000 y 68020). En 68060 el runtime no usa `muls.l`/`divs.l` de 64 bits (el 060
  no los tiene: 68060.library los emula con una excepción por cada uno). Máquina `a4000` en `tools/bench.py`
  (68040 con fast RAM): mismo benchmark con código de 68000 y con `--cpu 68040`.
- R2 Textos: `+` e interpolación sin `strlen` de libnix cuando el texto es de Dash (su tamaño está en la cabecera).
- R3 Cabecera de objetos de 20 a 16 bytes (un struct de dos Int pasa de bloques de 32 a 24 bytes). El usuario lo
  aparcó en 27c "salvo que un programa real lo pida"; con este encargo de memoria, se mide antes de decidir.
- R4 RTG en Zorro II/III: leer de la memoria de la tarjeta es lo más caro (Zorro II, unos 3 MB/s). Buscar en los
  runtimes de gráficos lecturas de la pantalla que se puedan evitar. FS-UAE no emula la lentitud del bus: se
  mide contando bytes leídos de la tarjeta, no tiempo.

## Bitácora

### 2026-10-25 — R1 (`--cpu`)
- `./dash --cpu 68020|68030|68040|68060` (`compiler/cflags.py` `cpu_flags`): `-m68020` más `-mtune`. `_DASH_68020` en el
  runtime (con `-mtune=68060` GCC define `__mc68060__` y no `__mc68020__`). Fixed en 68060 por el camino de 68000:
  0 `muls.l`/`divs.l` de 64 bits en el ensamblador (test en `tests/unit/test_dash_cli.py`). Fixed con dos constantes
  no pasa por el asm (con él, `fixed_mul_add` iba de 261 a 1.880 ns en el 68040).
- Probado: `test_fixed`, `test_fixed_lists`, `test_fixed_runtime_amiga`, `test_return_types` con `--cpu 68040` en
  un 68040 emulado (OS 3.1) y con `--cpu 68060` en un 68060 (OS 3.2 con 68060.library: con 3.1 el 060 no arranca
  en FS-UAE, ni con código de 68000). 381/381 sin emulador.
- Medida (`R1`, ns, 68040 con código de 68000 → `--cpu 68040`): `fixed_div` 27.727 → 823, `fixed_mul` 6.179 →
  1.598, `fixed_mul_add` 261 → 12, `array_get_set` 6.881 → 4.684, textos −13 % (`string_concat_int` 42.543 →
  36.951, `string_interp` 64.332 → 55.448, `string_return` 47.902 → 40.276), `nested_struct_new` −10 %. Peor:
  `string_compare` +8 %, `struct_new_field` +5 %. Gráficos y Float casi igual (los manda la ROM y softfloat).
  A500 y A1200 sin cambios (es el mismo código).
- No medido: un 68060 (FS-UAE no da tiempos reales de 040/060) ni la libnix de 68020 en un 060 (puede traer
  instrucciones de 64 bits que emula 68060.library).
- R2 descartada: el tamaño de la cabecera de un texto no es su longitud (los textos crecen en su sitio).

### 2026-10-25 — R3 (cabecera de objetos de 16 bytes)
- `_Dash_RefHeader`: `_size` y `destroy` pasan a un descriptor `const _DashType` por tipo (structs, listas,
  diccionarios, el soporte de préstamos). `_dash_rc_alloc` (C, tamaño cualquiera) guarda el tamaño en un LONG
  delante de la cabecera. El tamaño, constante, sigue yendo como argumento al reservar: solo con el descriptor
  GCC no sabía la clase de bloque y crear un struct iba un 28 % más lento en A500 (medida tirada).
- Medida (`R3` frente a `R1`): `mem_1000_structs` 33.088 → 24.816 bytes (−25 %, igual en las cuatro máquinas).
  Velocidad: `struct_new_field` +3,6 % en A500 (116.903 → 121.044), +12 % en A1200 (24.256 → 27.074), +3 % en
  68040; `array_literal_new` +1,7 % en A500; lo demás igual. Tamaño total +1.360 bytes (los descriptores).
- Probado: 383/383 sin emulador; `--emu --emu-a500 --emu-32` 928/931 y `--emu --memcheck` 541/542 (los fallos,
  `test_on_click_timer`: falla a ratos con la máquina cargada, solo pasa con y sin el cambio); 100 programas de
  `tools/fuzz_refcount.py` sin fallos. MUI con `--memcheck` se probó con la primera versión (la segunda pasada iba
  sin `DASH_EMU_SYS_MUI`); el arreglo solo cambia los argumentos al reservar.
- Gana un bloque en structs de 2, 4, 6... campos (y diccionarios); listas y structs de 1, 3, 5... campos, igual.

### 2026-10-25 — R4 (RTG en Zorro), solo análisis
- Lo que lee la tarjeta por el bus: `desktop_canvas_*` en cada actualización lee el área del bitmap de atrás
  (`_dash_desk_dirty`, para ver qué dibujó el programa) y, en los rectángulos que cambian, la pantalla
  (`_dash_desk_present_chunky`, para no pisar iconos). Las mezclas con alfa (`_dash_blend_block`, velos) leen lo que
  hay debajo; las opacas no leen. Las copias entre bitmaps de la tarjeta las hace su blitter (no pasan por el bus).
- Coste estimado en Zorro II (unos 3 MB/s): un panel de 200 x 300 a 16 bits son unos 120 KB por actualización,
  unos 40 ms; cada 2 s, un 2 % de CPU. En Zorro III, bastante menos. No es lo más caro y FS-UAE no deja medirlo.
- Para quitar la primera lectura, el programa tendría que dibujar en fast RAM (bitmap sin amigo): con Picasso96 sale
  negro (sin paleta), ya probado. Pendiente, si un usuario con Zorro II lo nota: guardar qué rectángulos dibuja el
  programa en vez de comparar el área entera.

Parado al 86 % del uso semanal: R1 (PR #52) y R3 (PR #53, sobre #52) a la espera de fusionar.

## Segunda ronda (2026-10-27)

Encargo: "ráscate una ronda de optimización de recursos de dash", tras los encargos de Lorraine (PR #62). Base
medida: `Base tras Lorraine (PR #62)`; frente a R3, `array_literal_new` iba un 28 % más lento en A500 y los 36
ejecutables pesaban 110 KB más (+33 %, unos 3 KB cada uno).

### R5 — listas sin multiplicaciones
- Las listas de Double (Lorraine D2) hacían el tamaño de cada elemento (1 o 2 LONG) con una multiplicación, que
  en un 68000 es una llamada a libgcc: al liberar cada lista, al añadir (`open`, `reserve`), en trozos, `+` y
  `sort`. Ahora son desplazamientos (`_DASH_ARR_SH`) y liberar una lista de enteros tiene camino propio.
- Medida: `array_literal_new` 316.844 → 253.764 ns en A500 (R3: 248.010), 68.415 → 57.789 en A1200.

### R6 — funciones de salida sin `atexit` de libnix
- `atexit` de libnix toma sus nodos de `malloc`, y el primer `malloc` pide un bloque de 16 KB (`__MEMORY_STEP`)
  que el programa guarda hasta el final; además enlaza `malloc.o`. Dash lo usaba para quitar su manejador de
  excepciones (todo programa, desde la sesión 17) y en varios runtimes. `_dash_atexit`: una tabla de 16
  funciones que corre la lista de salida de libnix (`ADD2EXIT` de `<stabs.h>`).
- Medida: 16 KB menos de memoria por programa en marcha; `hola` 7.888 → 6.780 bytes; los 36 ejecutables
  440.852 → 401.108 bytes (−9 %). El resto de los ~3 KB por programa es el manejador de excepciones (unos
  1.200 bytes de código, más 8 KB de pila suya en BSS, que no ocupan disco pero sí memoria).
- `test_meter_wifi` fallaba con el cambio: sus variables del driver falso, sin `volatile`, las cambia el driver
  dentro de las llamadas a exec y GCC las leía de un registro (con otra disposición del código, otra decisión).
  Arreglado en el test.

### Lo que no se tocó
- Textos y structs: reservar y liberar un texto ya es una docena de instrucciones (31 µs en el A1200 sin fast
  RAM: concatenar con su liberación, 88 µs; pasar un número a texto, 29 µs). Mejorar de verdad pide cambiar el
  diseño (cabecera de texto de 12 bytes, temporales): no sin preguntar.
- La pila de 8 KB para recuperarse de una excepción: la limpieza puede cerrar MUI, que necesita pila.
- `fixed_mul_add` (2.630 → 4.350 ns) y `string_chars_26` (+5 %) en A500: mismo C que antes; varían con dónde cae
  el programa en la memoria del A500 emulado.


## Tercera ronda (2026-10-27)

Encargo: seguir con el bucle, "lo de los Zorro II y III, mejorar el diseño de lo de los textos y de lo que sea
necesario", sin pausas entre vueltas. Rama `recursos3` (worktree `.worktrees/recursos3`); a `main` solo cuando lo
diga el usuario. Base medida: `Base ronda 3`.

### Plan
- R8 Textos con su longitud en la cabecera. Hoy la cabecera (12 bytes: `next`, `size`, `serial`) no tiene la
  longitud: `+`, la interpolación y `dup` llaman a `strlen` de libnix, `s.length` va por una caché de 8 textos
  largos, y saber si un texto es temporal (`_dash_tmp_take`, `_dash_str_ret`) recorre la lista de temporales.
  Diseño nuevo, mismos 12 bytes: `size` (con marca y bits), `len` y `self` (la dirección de la cabecera con una
  clave). Un texto es de Dash si `self` cuadra: un texto de C (un literal, una librería) solo pasaría por uno con
  probabilidad 2^-32, así que su `len` se cree sin medir. Los temporales salen de la cabecera a una pila aparte
  (puntero y número de serie, el mismo contador que los objetos), y un bit de `size` dice si lo es.
  - R8a la cabecera nueva y la pila de temporales; `_dash_str_len` y `strlen` de los runtimes por `len`.
  - R8b `+`, interpolación y copias sin `strlen` cuando el texto es de Dash; quitar la caché de longitudes.
  - R8c literales con su cabecera (`static const`), si compensa: así tampoco se miden los literales.
- R7 Zorro II/III en serio (R4 era solo análisis). Contar los bytes que se leen de la tarjeta por actualización
  (FS-UAE no da el tiempo del bus) en un caso como el de Trasfondo, y quitar lecturas:
  - R7a las mezclas con alfa sobre el fondo recién puesto leen la copia del fondo en fast RAM, no la tarjeta.
  - R7b comparar solo donde el programa dibujó en esta pasada y en la anterior, no el área entera.
- R9 Lo demás que salga de las medidas: `nested_struct_new`, `string_compare`, tamaño de los ejecutables.

### R8 — textos con su longitud, y `s = a + b` escrito en su sitio
- Cabecera de texto, los mismos 12 bytes: `size` (con marca y los bits `TEMP` y `KEEP`), `len` y `self` (la
  dirección de la cabecera más una clave). Un texto es de Dash si `self` cuadra (`_DASH_STR_OURS`): su longitud se
  lee, no se mide; uno de C (un literal, una librería) se mide con `strlen` como antes. `_dash_str_len` está en el
  runtime de memoria y la caché de longitudes de los textos largos (D22, D36, D41, D61) desaparece.
- Los temporales pasan de una lista en la cabecera a una pila aparte (puntero y número de serie; las marcas siguen
  siendo números). Sacar uno mira primero la cima (comparar punteros, sin leer antes del texto).
- `var = a + b` y la interpolación (hasta 6 partes) van por `_dash_str_set_join`: se escriben en el texto que ya
  tiene la variable si caben y ninguna parte está en él; si no, en uno nuevo suyo. Ni temporal ni liberación. Los
  textos pequeños ocupan su bloque entero de 8, 16... bytes (más sitio para volver a escribirse).
- Medida (`R8`, frente a `Base ronda 3`, A500 / A1200): `string_concat_int` −15 % / −16 %, `string_interp` −7 % /
  −7 %; en un programa aparte, `t = s + "a"` con `s` de Dash −40 %. Peor: `string_return` +12 % / +14 %,
  `nested_struct_new` +6 % / +8 % (un texto hecho en una función: la reserva y el apilado cuestan algo más que
  antes y no hay `strlen` que ahorrar). `string_chars_26` −9 % en A500. Memoria igual; ejecutables +9 KB en total
  (+2 %).
- Probado y tirado: la longitud como llamada (no en línea): `+` e interpolación perdían lo ganado. Literales con su
  cabecera hecha por el compilador (`static const`): el retorno, un 5 % peor y nada mejor. Los búferes de
  `DashString_from_int` con cabecera: contar las cifras costaba más que medirlas.
- Lo que costó encontrar: gcc lee byte a byte un `ULONG` delante de un literal (lo cree de alineación 1): un `asm`
  vacío esconde la dirección. Y meter en línea los caminos raros (crecer la pila, sacar del medio) hacía guardar 7
  u 8 registros en cada llamada: van aparte con `noinline`.
- Probado: 455/455 sin emulador; 34/34 ejemplos; `--emu --emu-a500 --emu-32` con los mismos 16 fallos que `main`
  (los 4 del escritorio en cada máquina, más `test_desktop_canvas` en 3.2, y `test_on_click_timer`).
- Aparte (ya en `main`, no de esta ronda): los tests del escritorio fallan en la batería entera porque antes corre
  `test_args_wb` (Lorraine D31) en el mismo arranque; solos o en grupo pasan. Sin causa encontrada aún.

### R7 — RTG sin backdrop: ninguna lectura de la tarjeta al actualizar
- Lo que se lee de la tarjeta en cada actualización (R4 lo midió a ojo): el bitmap de atrás en el área, para
  comparar (`_dash_desk_dirty`), y con backdrop además la pantalla en lo que cambió (para no pisar iconos). El velo
  de Trasfondo no: `desktop_canvas_veil` ya lo guarda mezclado en un bitmap de la tarjeta (`under`), copiado por
  su blitter.
- Sin backdrop (el escritorio es el fondo de la pantalla), comparar solo servía para elegir qué copiar, y la copia
  la hace el blitter de la tarjeta, sin pasar por el bus. Ahora el área (o todo) y lo que repintó el escritorio
  van tal cual, sin leer nada; las copias en fast RAM no se ponen al día (un cambio de modo vuelve a empezar el
  lienzo con `_dash_desk_reset`, que las toma de nuevo). Planar y backdrop, igual que antes: el planar lee Chip
  RAM, y con backdrop las lecturas hacen falta para los iconos.
- Medida: `_dash_desk_read_bytes` cuenta lo que se lee de la tarjeta. `update_area` de 80 x 40 en 16 bits sin
  backdrop: 6.400 bytes antes, 0 ahora (lo comprueba `test_desktop_canvas_modes_rtg`). Un panel de 200 x 300 como
  el de Trasfondo eran unos 120 KB por actualización completa (unos 40 ms en Zorro II).
- Probado: los 40 tests del lienzo en A1200, A500 y 3.2 y los 6 RTG (68040 con uaegfx); 455/455 sin emulador.

### R9 — Float: una sola multiplicación en 68020, 030 y 040
- `__mulsf3` (`runtime/softfloat/fastfp.c`) hacía el producto de mantisas con cuatro `mulu.w`, lo único que tiene
  un 68000. Los programas son código de 68000 por defecto aunque corran en un A1200: la primera llamada mira
  `AttnFlags` de ExecBase y, con un 68020, 030 o 040, usa un `mulu.l` de 64 bits (escrito como `.word`: el fichero
  es de 68000). En 68060 no (68060.library lo emula con una excepción): sigue el camino de 68000. La comprobación
  va primero por el 68000: un `move.b` y un salto corto.
- Medida (`float_mul`): A1200 28.242 → 22.752 ns (−19 %); A500 119.479 → 121.531 (+1,7 %, la comprobación).
  `float_mul_add` no cambia: GCC saca `g * 0.5` del bucle y solo mide sumas.
- Probado: `test_fastfp_amiga` (bit a bit contra fp-bit) en A1200, A500, 3.2 y un 68040; los 81 tests de
  float/fixed en las tres máquinas; 455/455. Sin probar en un 68060.
- Aparte: la batería `--emu --memcheck` da 66 fallos también en `main`: `test_on_click_timer` se cuelga y los
  siguientes del mismo arranque agotan el tiempo. Solos pasan.

### R10 — reservar un texto: temporal y propio, por separado
- `_dash_str_alloc(len, temp)` es ahora una macro sobre `_dash_str_alloc_tmp(len)` y `_dash_str_alloc_own(len)`
  (el cuerpo, en línea en las dos): el `temp` de los llamadores es una constante, así que no se pasa ni se mira.
- Medida frente a R8: `string_return` −2,3 % / −2,6 % (A500 / A1200), `nested_struct_new` −1,5 % / −1,8 %; frente
  a la base de la ronda quedan en +9 % / +11 % y +5 % / +6 %. En un programa con solo el retorno ya va igual que
  `main`. Ejecutables +2 KB en total.

### R11 — sin los 8 KB de pila propia para recuperarse de una excepción
- `_dash_trap_recover` corría en una pila suya de 8 KB en BSS (todo programa la cargaba, aunque nunca fallara;
  R6 la dejó porque la limpieza puede cerrar MUI, que pide pila). Ahora sigue en la pila del propio programa,
  desde donde empezó `main` (`_dash_trap_on`, no en línea, apunta la dirección): lo de debajo se abandona; lo de
  encima son los marcos del arranque y del Shell, que se conservan para volver. No la cima de la pila: sin
  `StackSwap` (el Shell ya daba bastante) la cima es del Shell.
- Medida: un programa vacío ocupa al cargarse 3.668 bytes (código, datos y BSS) en vez de 11.836: −8 KB en todo
  programa. En la comparativa, la memoria media al ejecutar era de 16,6 KB.
- Probado: los tests de excepciones y de nil en A1200, A500 y 3.2 (también con `--memcheck`), y uno nuevo,
  `test_trap_mui`: división por cero a 200 llamadas de profundidad con una ventana MUI abierta (A1200 y 3.2).

### Los fallos del escritorio y de `test_on_click_timer` en la batería entera (de `main`, no de la ronda)
- Causa: `test_args_wb` (Lorraine D31) lanza su copia como el Workbench, pero con la entrada y salida por defecto
  de `CreateNewProc` (NIL:, que DOS abre y cierra): al salir, con la consola de libnix, "fichero cerrado dos
  veces" (alerta 8700000E), un requester "Software Failure" que se quedaba sobre la pantalla. Los tests del
  escritorio leen esa zona y `test_on_click_timer` clicaba en él (con `--memcheck` se colgaba y los siguientes
  del arranque agotaban el tiempo: 66 fallos). Con `--memcheck`, además, el resumen de memoria de la copia abría
  una consola de libnix a pantalla completa que espera a que la cierren.
- Arreglo, en el test: `NP_Input`/`NP_Output` a 0 sin cerrarlos, como el Workbench, y `@workbench_output "NIL:"`.
  Seguidos con `--memcheck`, `test_args_wb`, `test_on_click_timer` y `test_desktop_canvas_fondo` pasan.
- Batería entera tras el arreglo: `--emu --emu-a500 --emu-32` 1.100/1.103 (solo `test_on_click_timer`);
  `--emu --memcheck` 671/674. De esos, dos eran de esta ronda y están arreglados: `test_zlib` con `--memcheck`
  iba cuadrático (la comprobación de la longitud medía con `strlen` el texto entero en cada `s.length`, y el
  test hace crecer uno hasta 100 KB): ahora mide entero solo si es corto, y en los largos mira el byte final.
  `test_trap_mui` dejaba vivo con `--memcheck` el texto de una interpolación de antes del fallo (lo que la
  excepción abandona no se libera): el test ya no lo hace.

### R12 — diccionarios: hash de las claves literales hecho al compilar, longitudes antes que bytes
- `d["color"]`, `d.get("color", x)`, `d.has("color")`, `d.remove("color")` y `d["color"] = v`: la clave literal
  (ASCII sin escapes) va como `_DASH_KEY("color", 0x...)`, un texto de Dash hecho por el compilador con su hash
  (el mismo djb2 del runtime) en el LONG de delante de la cabecera y el bit `_DASH_STR_HASHED`. En Tachyon hay
  265 accesos con clave literal y 268 `has`.
- `_dash_dict_slot`: hash y longitud de la clave con una sola mirada a la cabecera; cada hueco compara primero la
  longitud (las claves son textos del diccionario: la tienen en la cabecera) y luego los bytes, en línea (con
  `memcmp` de libnix, una llamada, iba más lento que antes).
- Medida (programa aparte, 12 claves de CSS de 5 a 19 letras, A500 / A1200): leer con clave variable −6 % / −3 %,
  escribir −4 % / −2 %, leer con clave literal −41 % / −34 %.
- Probado: `test_dict_key_hash` (clave literal y calculada en los dos sentidos, `has`, `remove`, una con acento que
  no lleva hash, dos de la misma longitud) en A1200 y A500; los tests de diccionarios con `--memcheck`; 456/456.
- Pendiente (también en `main`): `test_on_click_timer` falla en la batería entera ("sin clic") y pasa solo, tras
  115 programas vacíos, o con una de las dos mitades de los tests anteriores; falla con cualquiera de los dos
  cuartos de la primera mitad más la segunda. La misma copia, justo detrás del fallo, pasa: es algo pasajero que
  depende de cuántos tests reales corrieron antes, no de uno. Sin causa encontrada.

### R13 — `s == "literal"` sin strcmp
- `==` y `!=` con un literal van por `_dash_str_eq_lit(s, "lit", sizeof("lit") - 1)`, en línea: el primer byte
  primero (descarta casi todo sin leer la cabecera: `tag == "div"`, `"span"`... uno tras otro), luego la longitud
  si es un texto de Dash, y los bytes que quedan. nil sigue sin ser igual a ningún texto (D70). En Tachyon hay
  1.888 comparaciones así.
- Medida (`string_compare`, textos de la misma longitud y mismo primer byte: el peor caso): −7 % en A500 y A1200.
  La primera versión (longitud primero y un bucle con contador) iba un 3-6 % peor que `strcmp`.
- Probado: los tests de textos en las tres máquinas y con `--memcheck`; 456/456.

### Cierre de la tercera ronda
- Medida final (`Ronda 3 final (R7-R13)` frente a `Base ronda 3`, A500 / A1200): `string_concat_int` −16 % / −17 %,
  `string_interp` −7 % / −7 %, `string_compare` −6 % / −10 %, `string_chars_26` −6 % / −3 %, `float_mul` +3 % / −20 %;
  peor `string_return` +9 % / +11 % y `nested_struct_new` +5 % / +6 %. Diccionarios con clave literal −41 % / −34 %
  (programa aparte). Memoria: −8 KB por programa (R11). Zorro: sin backdrop, ninguna lectura de la tarjeta al
  actualizar el lienzo (R7). Ejecutables +11 KB en total (+2,8 %).
- Batería final: 456/456 sin emulador; 34/34 ejemplos; `--emu --emu-a500 --emu-32` (con RTG) 1.104/1.107 y
  `--emu --memcheck` 675/676: solo `test_on_click_timer` (pendiente, también en `main`).
- Queda: con backdrop (RTG) las lecturas de la tarjeta siguen (las pide la detección de iconos); el bucle por píxel
  de `_dash_desk_present_chunky` se podría acelerar por filas, sin forma de medirlo en FS-UAE.

## Después de la tercera ronda (2026-10-28): `test_on_click_timer` y lo que la ronda empeoró

### `test_on_click_timer` en la batería entera: arreglado (era `test_mouse_curve`)
- Con un programa que lista pantallas y ventanas en el sitio del test: la pantalla del Workbench estaba en y=25
  (y en 107 tras el clic) y la ventana del test nunca se activaba. Un programa que dice la posición de la pantalla
  tras cada test la señala: `test_mouse_curve` (Ratonera). Su falso hid.class manda una pulsación del botón
  izquierdo sin soltarla; con el botón abajo, la posición absoluta que manda después arrastraba la pantalla por su
  barra. Se quedaba baja para el resto del arranque, y el clic de `test_on_click_timer` caía en la barra.
  Dependía de dónde estaba el puntero al pulsar: por eso fallaba solo con muchos tests delante.
- Arreglo, en el test: la suelta justo después de la pulsación (el manejador sigue contando 3 de 3).

### R14 — `+` e interpolación con la longitud de cada parte dicha por el compilador
- Cada parte de `+` (`DashString_concat_h`, `DashString_join_h`, `_dash_str_set_join`) lleva una pista
  (`_DASH_HLEN`): un literal, su longitud (`sizeof("x") - 1`: la cuenta el compilador de C, tras pasar los
  acentos a Latin-1); un número o carácter hecho texto (`DashString_from_int`, `from_char`, un Bool), -2: texto de
  C que nunca es nil, medido con `strlen` sin mirar la cabecera; lo demás, -1 (`_dash_str_len`). Así un texto de
  C ya no paga la comprobación de la cabecera para acabar en `strlen`, que era lo que hacía antes de R8. Sin pista
  los literales con `\0` o `\x` dentro (`sizeof` contaría más allá de un byte 0).
- Medida frente al cierre de la ronda (A500 / A1200): `string_return` −2,6 % / −3,8 %, `nested_struct_new`
  −0,9 % / −1,6 %, `string_concat_int` −1,7 % / −0,2 %, `gfx_text_concat` −1,8 % / −1,4 %; ejecutables −512 bytes.
  Frente a la base de la ronda: `string_return` +6,4 % / +6,9 % (antes +9 / +11), `nested_struct_new` +3,6 % / +4,5 %.
- Probado: 456/456; los tests de textos en las tres máquinas y con `--memcheck`.
