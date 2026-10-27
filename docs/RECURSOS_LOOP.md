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

