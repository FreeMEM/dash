# Dash para DashOS: AArch64 big-endian (plan y bitácora)

DashOS (`~/Projects/dashos`, su `PLAN.md`, "Dash en los dos sistemas") necesita que el mismo programa Dash compile
para AmigaOS 3.x (hunks de 68k) y para DashOS (ELF de AArch64 big-endian). Rama `aarch64`, worktree
`.worktrees/aarch64`.

## Decisiones (usuario, 2026-11-03)

- **Capa común y un generador por procesador.** `dashc/src/gen68k.c` se parte en el recorrido del programa, que
  decide qué hacer, y el generador de 68k, que escribe las instrucciones. El de AArch64 es otro generador detrás de
  la misma interfaz. Cada cambio del lenguaje se hace una vez.
- **Punteros de 32 bits solo en las estructuras de Amiga.** Los programas nativos usan punteros de 64 bits. Las
  estructuras que comparte la caja Amiga se marcan y guardan sus punteros en 32 bits; el código los convierte al
  leerlos y escribirlos. En 68k la marca no cambia nada.
- **64 bits de verdad** (usuario, 2026-11-03, tras saber el coste). El runtime y los dos caminos guardan hoy punteros
  en `LONG` (elementos de listas, valores de diccionarios, casillas). Se hacen limpios de tamaño de puntero:
  - Int sigue siendo de 32 bits.
  - Cada lista usa el tamaño de elemento de lo que guarda: Int 4 bytes; texto, objeto o lista 4 en 68k y 8 en
    ARM; Double 8.
  - Los structs se colocan con los tamaños del procesador.
  - Se descartó tener toda la memoria por debajo de 2 GB: dejaba un límite para siempre en las bibliotecas.
- **El C de `./dash --gcc` puede cambiar de texto, pero no de código de 68k.** La red de seguridad del camino por C
  compara los objetos que da m68k-amigaos-gcc, no el C.
- **Runtime sin sistema debajo.** El runtime pide la memoria y escribe la salida a través de unas pocas funciones
  de plataforma, que pone quien lo aloja (DashOS, o el arnés de pruebas).
- **El camino de 68k no se toca.** Cada paso del reparto deja los ejecutables de 68k idénticos byte a byte
  (`dashc/tests/identicos.py`) y el C de `./dash --gcc` idéntico.

## Diseño del reparto (A3)

- `gen68k.c` es el recorrido común. Incluye en tiempo de compilación el generador del procesador: `t68k_base.c`
  (código, etiquetas, saltos y su relajación) y `t68k_ops.c` (operandos y operaciones con valores de Dash). El de
  AArch64 serán `ta64_*.c` con las mismas funciones, compilado como otro binario (`dashc` y `dashc-a64`): sin
  punteros a funciones ni coste en tiempo de ejecución.
- Cada paso saca del recorrido una secuencia de instrucciones de 68k a una función con nombre del generador (lo que
  hace, no cómo), sin cambiar un byte: `dashc/tests/identicos.py` tras cada paso.
- El modelo del recorrido se queda: el valor en un acumulador (d0, en ARM x0), los operandos en la pila, las
  variables en huecos (registro, marco, global, constante). En ARM los argumentos de una llamada se sacan de la
  pila a x0..x7 justo antes del `bl`.

## Diseño del generador de AArch64 (A4)

- **Registros:** d0 = x0 (el valor; también lo que devuelve una llamada), d1 = x1, a0 = x9, a1 = x10, a2 (el
  objeto que se llena) = x28. Las variables en registros: x19-x27 (`FIRST_REG` 2..10 = x19..x27, `MAX_REGS` 9).
  x29 marco, x30 vuelta.
- **Valores de 64 bits canónicos:** un Int vive en un registro de 64 bits con su signo extendido. Las operaciones de
  Int se hacen en 32 bits (w) y el resultado se extiende (`sxtw`): así el desbordamiento es el de 32 bits y las
  comparaciones y `tst` pueden ser siempre de 64 bits (sirven para Int y para punteros).
- **Pila:** `SLOT` = 16 (cada cosa que se mete ocupa 16 bytes: sp siempre alineado). Variables del marco de 8
  bytes, bajo x29. Siempre con marco (`CAN_FRAMELESS` 0).
- **Llamadas:** todas con el convenio de C (AAPCS64), también entre funciones de Dash: los argumentos que el
  recorrido metió en la pila se cargan en x0..x7 justo antes del `bl` (`call_sym(sym, n)`, `call_label`...); al
  entrar, cada parámetro se guarda en su hueco del marco. Más de 8 argumentos: aún no.
- **El runtime visto desde el código:** las funciones `dl_*` de ARM devuelven `_DashP` (un Int de C en w0 deja la
  parte alta sin definir).
- **Salida:** un objeto ELF64 big-endian (.text, .data, .rela.*, .symtab), enlazado con ld.lld con el runtime de
  dashc para ARM. Reubicaciones: CALL26 (llamadas), ADR_PREL_PG_HI21 + ADD_ABS_LO12_NC o LDST64/32_ABS_LO12_NC
  (direcciones y variables), ABS64 (punteros en tablas y descriptores). `Reloc` lleva tipo y sumando.
- **Sin FP ni SIMD**, como el resto de lo de DashOS.

## Herramientas

- `clang --target=aarch64_be-none-elf` y `ld.lld` (clang 23 del sistema): compilan el runtime en C para ARM.
- `qemu-aarch64_be` (modo usuario): ejecuta en el PC los programas de prueba. Para eso hay una plataforma de
  pruebas que habla con Linux (write, exit, mmap). DashOS pondrá la suya.
- `dashc/tests/identicos.py`: 2310 compilaciones de 68k (tests, ejemplos, 6 juegos de opciones) contra un dashc de
  referencia, en un segundo. `--guardar` fija la referencia.
- `tests/identicos_c.py`: el camino por C. Transpila 385 programas y compara los objetos de m68k-amigaos-gcc -c
  (normal, `-DDASH_MEMCHECK` y `--fpu`; 1149 objetos y 4 errores) con `build/c_ref.json`, en 30 s.

## Fases

| Fase | Qué | Cómo se prueba |
|---|---|---|
| A0 | Red de seguridad: `identicos.py` | 2310/2310 idénticos con la referencia de `origin/main` |
| A1 | Capa de plataforma en el runtime (memoria, salida, salida del programa, errores) | C de Amiga idéntico; el runtime compila para ARM sin sistema |
| A2 | `./dash --gcc --dashos`: por C con clang, a ELF de AArch64 big-endian | Tests con `# expect-out` en `qemu-aarch64_be`, misma salida que en el A1200 |
| A3 | Reparto de `gen68k.c`: recorrido común + interfaz de objetivo + generador de 68k | `identicos.py` tras cada paso; `make -C dashc test` al final |
| A4 | Codificador de AArch64 y escritor de ELF (enlaza el runtime, un `.o` ELF) | Enteros, funciones, control y `Print`, contra A2 |
| A5 | Cobertura en ARM: textos, listas, structs, diccionarios, Float y Double (FPU de ARM) | Los tests de A2 por el camino directo, misma salida |
| A6 | Structs de Amiga con punteros de 32 bits, en los dos caminos | Tests en ARM; en 68k, ejecutables idénticos |
| A7 | Builtins de DashOS | Cuando DashOS tenga su API (S11). Fuera de este bucle |

Con A2 hecho, el camino por C es el oráculo del directo, como hoy `./dash --gcc` lo es del directo de 68k.

## El cargador de DashOS (freemem-f9, 2026-11-03)

`kernel/src/elf.rs` de `~/Projects/dashos` (C19); referencia que ya funciona: `usuario/enlace.ld` y
`usuario/src/lib.rs`.

- ELF64 big-endian (EI_DATA = 2), ET_EXEC, EM_AARCH64 (183), estático en 0x400000. Sin PIE, sin relocaciones ni
  enlazado dinámico. Solo PT_LOAD.
- Permisos por p_flags: X = código de solo lectura, W = datos sin ejecución, el resto solo lectura. memsz > filesz
  queda a cero (.bss).
- Cada segmento alineado a 4 KB y sin compartir página con otro. Toda VA por debajo de 1 << 39.
- Entrada en e_entry. La pila acaba en 0x80000000 (SP inicial) y crece hacia abajo; se reserva entera al cargar.
  Tamaño: el p_memsz de PT_GNU_STACK (con lld, `-z stack-size=N`), de 4 KB a 8 MB; si vale 0, 64 KB
  (DashOS 4d653fe). Ningún segmento pasa de 0x80000000 - 8 MB; las proyecciones, por debajo de la pila.
- **Sin FP ni SIMD en los programas** (DashOS, 2026-11-03): el kernel no guarda esos registros al cambiar de hilo.
  Todo se compila con `-march=armv8-a+nofp+nosimd -mabi=aapcs-soft`; Float y Double van por el fp-bit de
  `runtime/softfloat` más `runtime/dashos/softfloat_extra.c`. Usar la FPU de verdad es decisión del usuario (trabajo
  de kernel en DashOS).
- Llamadas provisionales: `svc #0`, número en x8, argumentos en x0..x5, resultado en x0 (negativo = error).
  escribir(ptr, len) = 1; salir(código) = 2; memoria_crear(tamaño) = 7 da una llave;
  memoria_proyectar(llave, va, permisos 1 leer | 2 escribir) = 8, con la VA alineada a 4 KB que elige el programa.
  Cambiarán con la API de S11: solo las funciones de plataforma conocen estos números.

## Reglas del bucle

- Cada vuelta mira `~/.claude/state/uso-7d.txt`: con 90 % o más, se cierra en un punto seguro, se anota y se para.
- Se hace el siguiente paso pendiente, con sus pruebas. Antes de cada commit que toque `compiler/` o `dashc/src/`,
  pasan `tests/identicos_c.py` y `dashc/tests/identicos.py`.
- Commit y push de la rama `aarch64`; una línea en la bitácora. Sin pausas entre vueltas.
- Al acabar una fase, aviso a freemem-f9 (DashOS).
- El emulador se usa bajo `flock /run/user/1000/dash-emu-red.lock`.

## Preguntas abiertas

- Nombre de la opción: `--dashos` (propuesta).
- Marca de las estructuras de Amiga: `@amiga struct X` (propuesta). Va en la gramática de los dos caminos.

## Bitácora

- 2026-11-03: plan. A0 hecha: `dashc/tests/identicos.py`, 2310/2310 idénticos. dashc compila 277 de 385 programas
  del corpus (tests, ejemplos y los suyos); el resto da error en los dos y también se compara.
- 2026-11-03: el usuario elige 64 bits de verdad. `tests/identicos_c.py`: 385/385 idénticos (fecha y hora de gcc
  fijas). Cargador y pila de DashOS apuntados.
- 2026-11-03: A1 empezada. `runtime/dashos/` (`dash_dashos.h`: tipos del Amiga con punteros de 64 bits;
  `plat.c`: arranque, memoria con los nombres de exec desde 4 GB, Printf, libc mínima; plataformas DashOS y Linux)
  y `DASH_TARGET=dashos` en codegen (`_dashos_port`). `tools/dashos_run.py` compila con clang y ld.lld y ejecuta en
  qemu-aarch64_be: el primer programa (Print, funciones, textos) da su salida. `_DashP`, entero del tamaño de un
  puntero, para los primeros cortes. `identicos_c.py` compara secciones y relocaciones (`objdump -s -r`) sin los
  números de los static locales; `--desde COMMIT` saca la referencia de otro commit. 385/385.
- 2026-11-03: listas, diccionarios, parámetros sin tipo y casts de valores a `_DashP` (casillas del tamaño de un
  puntero; Int, Float y punteros en una casilla, Double en 1 << `_DASH_DBL_SH`). Cabecera de textos con `_DashUP`.
  `tests/dashos_tests.py`: 73 de 284 tests con salida esperada pasan en qemu (los demás piden builtins de AmigaOS,
  Float/Double o más cortes). Lecciones de la red de seguridad:
  - `--desde` no funcionaba: `python -m` toma antes la carpeta actual que PYTHONPATH. Se ejecuta desde la copia
    vieja; la referencia es el commit de partida de la rama (7a989d7), no `origin/main`, que avanza.
  - En el Amiga, `_DashP` y `_DashUP` son macros de `LONG` y `ULONG`, no typedefs: con typedef, gcc cambiaba el
    código de algunas funciones. Y donde había `(ULONG)` va `_DashUP`, no `_DashP`.
  - Con eso, 385/385 objetos de 68k idénticos al compilador de partida. Tests: 525/525.
- Decisión técnica: por ahora toda casilla de lista es un `_DashP` (8 bytes en ARM, también las de Int). Guardar
  las listas de Int en 4 bytes queda para después, cuando funcione todo (es una optimización de memoria).
- 2026-11-03: Ryu, fdlibm y zlib compiladas para ARM (`build/dashos/*.a`, con cabeceras mínimas en
  `runtime/dashos/include/`); Double en ARM. Funciones como valores: los Func se llaman como
  `_DashP f(_DashP, ...)` y las lambdas devuelven `_DashP`; en DashOS, las funciones con nombre usadas como valor van
  por un envoltorio (`_dash_fv_*`): una lambda veía un Int negativo como positivo (`tests/test_func_valores.dash`,
  también en el A1200). `./dash --dashos prog.dash -o prog`: ELF para DashOS (estático en 0x400000, segmentos en
  páginas aparte, PT_GNU_STACK con la pila del programa). 91 de 284 tests en qemu; los demás piden AmigaOS (A7).
  Ojo: un volcado de qemu (`*.core`) lleva el entorno y GitHub lo paró por un token: no se suben (`.gitignore`) y
  `dashos_run.py` ejecuta qemu sin volcados.
- 2026-11-03: DashOS cargó `hola_dashos.elf` y se paró en la primera instrucción SIMD (memset vectorizado): sus
  programas no pueden usar FP/SIMD. Ahora sin ellos (ver arriba); fp-bit necesita
  `-D__FLOAT_WORD_ORDER__=__ORDER_BIG_ENDIAN__` con clang (si no, da la vuelta a las mitades de un double: 5 * 2 daba
  -12). 92 de 294 tests en qemu, sin un solo registro de FP en los ejecutables. Fusionado `main` (fdc06b0): 395/395.
- 2026-11-03: el ELF de 10448c2 corre en DashOS (QEMU raspi4b, cargador de C19, FP bloqueado en EL0): escribe
  "hola 12" y "a5" y sale con 0. Es el primer programa Dash en DashOS.
- 2026-11-03: A3 empezada. Maquinaria de 68k fuera de `gen68k.c`, sin cambiar nada: `t68k_base.c` (284 líneas) y
  `t68k_ops.c` (212). 2370/2370 idénticos. Quedan unas 600 instrucciones escritas a mano en el recorrido, repartidas
  en unas 100 funciones (las que más: `gen_arr_store`, `gen_ranged`, `mul_const`, `gen_function_pass`, `gen_new`).
- 2026-11-03: A3 sigue. Fuera del recorrido, con nombre: textos en línea (`str_ours`, largo, código), pila
  (`push_var`, `push_word`, `reserve_args`/`store_d0_arg`...), campos y constructores (`field_off`, `struct_bytes`,
  `obj_begin`...), nil (`fail_if_nil`), listas (`arr_get`, `arr_put`), llamadas por puntero y métodos
  (`call_d0`, `call_method`), y `t68k_arith.c` (aritmética) y `t68k_opt.c` (optimizaciones del 68000 que el
  recorrido pide por nombre, como `gen_ranged`; en ARM devolverán 0). `SLOT` = lo que ocupa cada cosa de la pila.
  Siempre 2370/2370. Quedan unas 280 instrucciones a mano: `gen_function_pass`, `gen_program`, `gen_compare`,
  `gen_expr`, `str_set_join`, diccionarios, `gen_keys_loop`, `gen_stmt`, `gen_struct_types`, bucles y EventLoop.
- 2026-11-03: A3 hecha en lo esencial. El recorrido común (`gen68k.c`, 6293 líneas) ya no escribe ninguna
  instrucción ni sabe tamaños: todo pasa por unas 170 funciones del generador (`t68k_base.c`, `t68k_ops.c`,
  `t68k_arith.c`, `t68k_opt.c`): pila (`SLOT`), listas y diccionarios por dentro (`ELEM`, `ARR_LEN`, `DICT_CAP`),
  campos (`field_off`, `struct_bytes`), globales (`global_off`), marco (`frame_off`, `param_off`), registros
  (`FIRST_REG`, `MAX_REGS`), prólogo y epílogo, descriptores, arranque. 2370/2370 en cada paso. Queda en el
  recorrido el modelo (acumulador d0, d1, a0, a1, a2 para el objeto que se llena) y los códigos de condición CC_*,
  que el generador de ARM traduce.
- Siguiente: A4. `dashc-a64` (el mismo `gen68k.c` con `-DDASH_A64` y `ta64_*.c`), que escribe un objeto ELF y se
  enlaza (al principio con ld.lld) con el runtime de dashc compilado para ARM (gen_lib con `DASH_TARGET=dashos`,
  `api.c` sin AmigaOS).
- 2026-11-03: A4 empezada, y el primer programa por el camino directo corre en ARM ("hola" y 6 * 7 = 42, en
  qemu). `dashc-a64` (`make -C dashc dashc-a64`): `gen68k.c` con `-DDASH_A64` incluye `ta64_base.c` (codificación,
  etiquetas, saltos, reubicaciones), `ta64_ops.c` (las ~110 operaciones), `ta64_arith.c` y `ta64_opt.c`; `elf.c`
  escribe el objeto (ET_REL, .text/.data/.rela/.symtab; entrada `_dashc_start`). El recorrido dice ahora cuántos
  argumentos lleva cada llamada (`call_sym`, `call_label`...), alinea los descriptores (`code_align`) y no hace
  funciones sin marco si el generador no puede (`CAN_FRAMELESS`). El runtime de dashc para ARM
  (`dashc/runtime/dashos/build.py` → `build/dashos/dashc_rt.a`): la cocina sin ventanas transpilada para DashOS,
  las envolturas `dl_*` de `api.c` que no tocan AmigaOS (devolviendo `_DashP`) y `start.c` (arranque, Print).
  `api.c`, limpio de tamaño de puntero con las macros: el runtime de 68k sale igual (solo cambia la hora de
  compilación que lleva dentro). `tools/dashos_run.py --directo` compila, enlaza (ld.lld) y ejecuta.
  2370/2370 y 395/395.

