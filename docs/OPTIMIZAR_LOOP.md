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

- [ ] O1 lista: `a[i]` y `a[i] = x` en línea en gen68k (comprobación de nil y de límites, y la carga), con el mismo
  comportamiento que el runtime ante un índice fuera de rango.
- [ ] O2 `%` y `/` con divisor constante: `divu` directo cuando se sabe que el dividendo cabe (rango del `for`,
  valores pequeños), y la rutina solo si no.
- [ ] O3 flotante: ver qué rutinas llama el directo y usar las rápidas (fastfp) del camino por C.
- [ ] O4 texto: perfil de `s = "x" + i` y quitar copias o llamadas que el camino por C no hace.
- [ ] O5 llamada: menos trabajo por llamada (registros que se guardan, argumentos en registros para funciones
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
