# Bucle de optimización: el compilador directo, al nivel del camino por C

Encargo (2026-11-02, el usuario, al ver la comparativa de dash.freemem.space): "en general el código compilado con
el directo es más lento que el compilado con GCC. Habría que mejorar estos números". Rama `optimizar`, worktree
`.worktrees/optimizar`, sale de `main` (Dash 2.0.1). Se fusiona en `main` por PR cuando haya mejoras medidas.

## Punto de partida (2026-11-02, Dash 2.0.1, `tools/comparativa/medir_dash.py`)

Milisegundos por programa (menos es mejor). Directo = `./dash`; por C = `./dash --gcc` (gcc -O2).

| Prueba | A1200 directo | A1200 por C | A500 directo | A500 por C |
|---|---|---|---|---|
| vacio (arranque) | 42 | 46 | 147 | 165 |
| bucle (300.000 vueltas) | 623 | 632 | 2831 | 3237 |
| llamada (100.000 llamadas) | 272 | 225 | 1213 | 1069 |
| texto (20.000 texto + número) | 2758 | 1516 | 11817 | 6411 |
| lista (100.000 accesos) | 2601 | 1553 | 12596 | 7524 |
| flotante (20.000 operaciones) | 999 | 491 | 4880 | 2378 |
| lineas (2.000 líneas) | 4934 | 4989 | 6685 | 6733 |

Objetivo: que el directo no sea más lento que el de C en ninguna prueba, en las dos máquinas, sin romper nada
(las baterías de los dos caminos) y sin agrandar mucho los ejecutables.

## Lo visto antes de empezar

- **lista:** gcc mete el acceso en línea con todo en registros. El directo llama en cada vuelta a `dl_arr_get` y
  `dl_arr_set` del runtime con los argumentos en la pila (unas 20 instrucciones de más por acceso, y dos `jsr`).
- **`%` y `/`:** con un divisor constante que cabe en 16 bits, el directo compara el dividendo con 655359 y salta
  a una rutina si no cabe; gcc sabe del rango (el índice del bucle) y usa `divu` sin más. Ver si el rango del
  `for` se puede usar igual.
- **llamada:** cada función del directo guarda y pasa más que la de gcc (marco, registros, argumentos por pila).
- **texto y flotante:** sin mirar aún por dentro; medir con `--perfil` (perfil por rutina del runtime, PC cada
  VBlank: `dashc/tests/perfil_pc.py`). Sospechas: Float por las rutinas genéricas en vez de las de ensamblador
  (`runtime/softfloat/fastfp.c`) que usa el camino por C; textos: temporales y copias.

## Tareas

- [x] O1 lista: `a[i]` y `a[i] = x` en línea en gen68k (comprobación de nil y de límites, y la carga), con el mismo
  comportamiento que el runtime ante un índice fuera de rango.
- [x] O2 `%` y `/` con divisor constante: `divu` directo cuando se sabe que el dividendo cabe (rango del `for`,
  valores pequeños), y la rutina solo si no.
- [x] O3 flotante: ver qué rutinas llama el directo y usar las rápidas (fastfp) del camino por C.
- [~] O4 texto: perfil de `s = "x" + i` y quitar copias o llamadas que el camino por C no hace.
- [~] O5 llamada: menos trabajo por llamada (registros que se guardan, argumentos en registros para funciones
  `static` del programa, si el resto del compilador lo permite).
- [ ] O6 Medir de nuevo con `medir_dash.py`, actualizar la comparativa de la web (dash.freemem.space, columnas
  "Dash (directo)" y "Dash (por C)") y `docs/COMPARATIVA*.md`.

## Cómo se trabaja

- Cada cambio: `make -C dashc` (y `make -C dashc runtime` si se toca `compiler/codegen.py`), las pruebas del
  directo (`make -C dashc test`), `python3 tests/run_tests.py` y `./compile_all.sh`. Antes de fusionar, también
  `python3 tests/run_tests.py --emu --emu-a500`.
- Medir con `python3 tools/comparativa/medir_dash.py` (unos minutos; `--solo directo` para ir rápido) y anotar
  las cifras aquí, frente a la tabla de partida.
- Emulador y servidores, bajo `flock /run/user/1000/dash-emu-red.lock` (el script ya lo usa).
- Sin pausas entre vueltas; mientras corre una tanda, seguir con otra tarea. Al 90 % del uso semanal
  (`~/.claude/state/uso-7d.txt`), parar en un punto seguro y anotarlo.
- De cara al usuario no se dice "dashc" ni "dash1": "el directo" y "por C".

## Bitácora

- 2026-11-02: plan, rama y `tools/comparativa/medir_dash.py` (mide los dos caminos en A1200 y A500 de una vez).
- 2026-11-02, O1: `a[i]` en línea en gen68k (movea, comparación sin signo con la longitud, que cubre también el
  índice negativo, y la carga; nil o fuera de rango dan 0, como `DashArray_get`) y `a[i] = x` en línea para listas
  de valores (las de textos y objetos siguen por el runtime, por la cuenta de referencias). Mismo resultado que por C
  en un programa de bordes (índices -1, 3, 100000, nil, escritura fuera de rango, Float, textos). `make -C dashc test`
  entero bien. lista: A1200 2601 → 2051 ms (−21 %), A500 12596 → 9815 ms (−22 %); por C, 1553 y 7524: aún falta.
  Lo que queda en el bucle: la lista se apila y se recoge (sin registro libre fijo) y el `%` con su comprobación.
- 2026-11-02, O4 (parte): `s = a + b + ...` y `s = "...#{x}..."` (hasta 6 partes) a una variable de texto llaman a
  `dl_str_set_join_r` (nuevo en `runtime/api.c`, sobre `_dash_str_set_join`, como el camino por C): escribe en el
  texto de `s` si cabe, sin el temporal de la unión ni su copia. Mismo resultado que por C y `--memcheck` limpio en un
  programa con uniones de literales, números, interpolación, la propia variable, una global y una función.
  texto: A1200 2758 → 2181 ms (−21 %), A500 11817 → 9373 (−21 %); por C, 1516 y 6411. Queda: cada parte numérica
  pasa por `dl_str_from_int` (una llamada de más) y lo demás de la vuelta; mirar con `--perfil`.
- 2026-11-02, O3: el `for` saca del bucle las operaciones de Float (+, -, *, /) cuyos operandos no cambian en el
  cuerpo (literales, constantes y locales que el cuerpo no asigna; las globales no, por las llamadas): se calculan
  una vez en un hueco (`Repl` lleva ahora su tipo). Es lo que hace gcc en `flotante` (`g * 0.5`). Mismo resultado que
  por C con una variable que sí cambia, una llamada y una división por cero en una rama que no se ejecuta.
  flotante: A1200 999 → 495 ms (por C 491), A500 4880 → 2431 (por C 2378): ya igual. `make -C dashc test` entero bien.
- 2026-11-02, O5 (parte): `r = a + b` y `r = a - b` de enteros con `r` en un registro (también la primera
  asignación) se calculan en el registro de `r` sin pasar por d0, y al final de una asignación `move.l dX,d0;
  move.l d0,dN` queda en `move.l dX,dN` (`store_d0_stmt`, con `take_move_to_d0`): lo que devuelve una función en
  línea ya no da la vuelta por d0. El bucle de llamada, de 11 instrucciones a 8 (gcc, 7). Mismo resultado que por C en
  un programa de bordes (desbordamiento, negativos, Char, funciones en línea). `make -C dashc test` entero bien.
  Medida completa (A1200 / A500, ms, directo frente a por C): bucle 623/625 y 2845/3240; flotante 494/488 y
  2423/2401; lineas 4934/4989 y 6679/6829; lista 2048/1549 y 9817/7561; llamada 245/219 y 1089/1059; texto
  2181/1520 y 9371/6426; vacio 43/51 y 147/155.
- 2026-11-02, O1b y O2: con la lista en una variable local, `a[i]` calcula el índice y carga la lista directamente
  en a0, y `a[i] = x` lleva el índice a d1 sin pasar por la pila (simple) o con un solo apilado; `var_range` conoce el
  rango de `x + k`, `x - k` y `k + x` (si no se sale de 32 bits): `(i + 1) % 10` en un for usa `divu` sin comprobar,
  y con un cociente que no cabe (hasta 700.005) sigue comprobando. Quitado un bloque repetido de O1 que nunca se
  ejecutaba. Mismo resultado que por C. `make -C dashc test` entero bien. lista: A1200 2048 → 1787 ms (por C 1549,
  +15 %), A500 9817 → 8467 (por C 7561, +12 %).
- Estado (2026-11-02, uso semanal al 99 %): hechas O1, O2, O3; O4 y O5 a medias. Queda: texto (+44 %: el perfil
  `--perfil` da 106 muestras, casi todas en el runtime, 0x1200-0x14D0; mirar qué rutina con el mapa del hunk y
  `dashc/tests/perfil_pc.py`), llamada (+12 % en A1200), el resto de lista (+15 %), luego O6 (medida completa, web y
  `docs/COMPARATIVA*.md`) y la PR. Antes de la PR: `python3 tests/run_tests.py` y `--emu --emu-a500`.

