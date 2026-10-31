# Bucle del depurador de dashc (pieza 6 de Forja; D12 de DASHC_LOOP)

Encargo (2026-10-29, rama dashc, pedido por el usuario): información de
depuración en dashc y una librería de depurador para Forja, el IDE de Dash: lanzar un programa como proceso hijo,
puntos de parada, paso a paso, leer su memoria, sus registros y sus variables. Solo dashc: nada para dash1 (el
usuario, 2026-10-29: "no quiero generar nada para dash1"). Rama `ide-piezas` (worktree `.worktrees/ide-piezas`).

## Diseño

Como EDBG de AmigaE (DASHC_LOOP, D12): sin el bit de traza de la CPU, que Emu68 no tiene.

- `dashc --debug`: un `NOP` (0x4E71) al principio de cada línea de Dash. Un punto de parada cambia ese `NOP` por
  `TRAP #n` (0x4E4n, el mismo tamaño): al seguir no hay que reponer ni volver a ejecutar nada, se sigue en la
  instrucción de después. Sin copiar funciones en línea, sin funciones de una línea como expresión y sin pasar a
  constante una variable asignada una vez (que todas las variables y líneas estén donde se las busca). Todas las
  funciones con marco (`link a5`).
- La información va en un `HUNK_DEBUG` tras el hunk de código (LoadSeg no lo carga): texto, una cosa por línea,
  que lee el C del depurador. Ficheros; por cada `NOP`, su desplazamiento, fichero y línea; por cada función, dónde
  empieza y acaba y sus variables y parámetros (nombre, tipo, registro dN o desplazamiento sobre a5); las globales
  (desplazamiento en datos o BSS); los campos de cada struct.
- El depurador, builtins `dbg_*` solo de dashc: su C en `dashc/runtime/depurar.c` (incluido en la librería como
  `api.c`) y sus filas en la tabla de builtins de dashc, aparte de `compiler/amiga_builtins.py`.
  - Lanzar: `LoadSeg` del programa y su `HUNK_DEBUG` leído del fichero; un proceso hijo (`NP_Cli`, salida a un
    fichero) cuya entrada es código del depurador: pone su `tc_TrapCode` y ejecuta el programa con `RunCommand`
    (el runtime de Dash, al empezar, pone el suyo y le pasa los `TRAP` que no son errores al de antes).
  - Parar: el manejador (supervisor) apunta el PC del marco y vuelve a modo usuario en una rutina del depurador, en
    el proceso hijo: guarda los registros, avisa al depurador (Signal) y espera; al seguir, los repone y salta al
    PC apuntado.
  - Paso a paso: todos los `NOP` a `TRAP` y, al parar, se mira la pila: "entrar" para en la siguiente línea; "pasar"
    en la siguiente con a7 igual o más arriba; "salir" con a7 más arriba que el marco de la función.
  - Leer: registros guardados, memoria (`peek`), variables por nombre con su valor como texto (Int, Bool, String,
    Float, structs y listas por encima), la pila de llamadas (cadena de a5) con fichero y línea de cada marco.
  - Caché: `CacheClearU()` tras cambiar código (68020 y más).
- Forja los usa con un módulo Dash encima (`lib/depurar.dash`) si hace falta.

## Tareas (cada una con sus tests y commit)

- G1 `dashc --debug`: el `NOP` de cada línea, las optimizaciones de arriba quitadas, y el `HUNK_DEBUG` con ficheros,
  líneas y funciones. `dashc --debug-info prog` lo enseña (para los tests en el PC).
- G2 Variables: locales, parámetros, globales y campos de structs en el `HUNK_DEBUG`.
- G3 `depurar.c`: lanzar, puntos de parada, seguir, esperar, dónde está, registros, memoria, acabar. Test en el
  emulador: un programa que depura a otro (compilado con `--debug`, en el mismo disco).
- G4 Paso a paso (entrar, pasar, salir) y la pila de llamadas.
- G5 Variables con su valor; la salida del programa depurado.
- G6 Documentación (README de dashc, BUILTINS de dashc) y aviso a freememlang-f3 (Forja).

## Bitácora

- 2026-10-29: plan. freememlang-51 fusiona `ide-piezas` en `dashc` (piezas 1-5 y 7-10); este trabajo toca
  `gen68k.c`, que también cambia el bucle de dashc: tras su fusión, traer `dashc` aquí antes de G1.
- G1 y G2 hechas: `dashc --debug` (también `./dash --debug`, que ya no remite a dash1) pone un `NOP` con su etiqueta
  (se recoloca al acortar saltos) en cada línea, sin copiar en línea, sin variables en registros ni como constantes,
  todas las funciones con marco; el `HUNK_DEBUG` de texto tras el hunk de código: `F` ficheros, `G` globales
  (desplazamiento en datos), `S` campos, `P` funciones (inicio y fin en el código), `V` variables y parámetros
  (sobre a5, con su línea), `L` el `NOP` de cada línea. `dashc --debug-info prog` lo enseña. Los 31 tests de dashc
  compilados con y sin `--debug` dan lo mismo en el A1200. Test `tests/unit/test_dashc_debug.py`. Antes, `dashc`
  traído a la rama (fusión con el runtime rehecho).
- G3 hecha: `dashc/runtime/depurar.c` (en la librería tras `api.c`) con los builtins `dbg_*`, solo de dashc: sus filas
  en `dashc/runtime/builtins_dashc.py`, que lee `gen_builtins_tab.py`. `dbg_start` (LoadSeg, el `HUNK_DEBUG` leído del
  fichero, un proceso hijo con su `tc_TrapCode` que espera y ejecuta el programa con `RunCommand`, salida a T:),
  `dbg_break`/`dbg_unbreak` (por el final del nombre del fichero), `dbg_continue`, `dbg_wait`, `dbg_state`,
  `dbg_signal`, `dbg_file`/`dbg_line`/`dbg_function`, `dbg_reg`, `dbg_peek`, `dbg_output`, `dbg_end` (todas las
  líneas a `TRAP` y en la siguiente a `_dash_quit(20)` del programa: `hunk.c` apunta su sitio con una línea `Q`),
  `dbg_rc`; también `dbg_step`/`dbg_next`/`dbg_out`/`dbg_pause` (sin probar aún: G4). Los textos del C, con
  escapes Latin-1. Tests: `dashc/tests/depurar.py` (en el A1200, con el depurado en DH0:), `basico` bien.
- D13 (freememlang-51, 2026-10-29): Dash 2.0 mantiene los dos caminos (dashc y `./dash --c`, dash1); los `dbg_*` son
  solo de dashc y lo dicen en su documentación.
- G4 hecha: `dbg_step` (entra en las funciones), `dbg_next` y `dbg_out` miran el marco (a5, no a7: dentro de un
  bucle dashc deja cosas en la pila), `dbg_pause` (todas las líneas a `TRAP`), la pila de llamadas por la cadena de
  a5 (`dbg_frames`, `dbg_frame_function/line/file`: la línea de una llamada es la del último `NOP` antes de su
  vuelta). `dbg_end` deja el estado (4) y el código (20 si lo acabó el depurador). Tests `basico` y `pasos` bien en
  A1200 y A500 (`depurar.py --a500`).
- G5 hecha: `dbg_vars(i)` y `dbg_var_name/type(i, k)` (los parámetros y las variables declaradas antes de la línea
  del marco i; de dos con el mismo nombre, la última), `dbg_globals`/`dbg_global_name`, `dbg_value(i, expr)` y
  `dbg_value_type`: una variable del marco o una global con `.campo` y `[n]` detrás, como texto (Int, Bool, Fixed,
  Float y Double con el runtime, textos entre comillas, structs con sus campos a dos niveles, listas hasta 20,
  diccionarios con su número de claves, nil) o "? " y el porqué. La salida del programa ya estaba (`dbg_output`,
  G3). Los depurados de los tests son `depurado*.dash`. Tests `basico`, `pasos` y `variables` bien en A1200 y A500.
- G6: el depurador en `dashc/README.md` y `README.en.md` (sección "Depurar"/"Debugging": cómo se usa, los `dbg_*`,
  cómo va y sus límites).
- 2026-10-30: el usuario retira el "nada para dash1"; vale la D13. Los `dbg_*` pasan a los dos Dash: su C es la
  plantilla `DEBUGGER_RUNTIME` de `compiler/codegen.py` (con listas, diccionarios, Float y Double; un Double del
  programa depurado es la caja de dashc, que se lee aquí) y sus entradas, `DEBUGGER_FUNCTIONS` de
  `amiga_builtins.py`; fuera `dashc/runtime/depurar.c` y `builtins_dashc.py`. El depurado sigue siendo de
  `dashc --debug`. `tests/depurar.py --c` compila los depuradores con dash1: los tres bien en A1200 y A500, como
  con dashc.
