# dashc: textos, listas y structs (plan y bitácora)

Objetivo: que dashc compile textos, listas y structs con el mismo comportamiento que el Dash de Python,
incluida la memoria (temporales, contadores de referencias, préstamos).

## Decisión

No se reescribe el runtime: se compila una vez con gcc el mismo C de `compiler/codegen.py` (CTemplates:
memoria, textos, listas, contador de referencias, errores) y dashc lo lleva dentro, como `dashrt.o`.
dashc genera las mismas llamadas que el C del Dash de Python en los mismos sitios. Lo que en C son macros o
funciones `static inline` se exporta con envoltorios (`dl_*`) y, si hace falta velocidad, se escribe en línea
en 68000 después.

- `runtime/gen_lib.py`: saca el runtime del C que genera el Dash de Python para un programa que usa todo
  (sin structs propios), le quita `main` y añade los envoltorios. Así sigue al día con codegen.py.
- Los structs los genera dashc: descriptor `_DashType` en datos, constructor y destructor en 68000.
- Las divisiones de 32 bits del C del runtime (`__divsi3`...) van a las rutinas de `rt_math.s`.

## Fases

1. Runtime como librería: gen_lib.py, Makefile, enlazado, arranque y salida (`_dash_exit_cleanup`).
2. Textos: literales, variables (dueñas de su texto), `+`, interpolación, `Print`, `length`, `[i]`,
   `[a:b]`, comparaciones, parámetros y valores devueltos, marcas de temporales por vuelta y por función.
3. Listas de Int: literales, `[i]`, `[i] = v`, `push`, `length`, `for x in lista`, trozos.
4. Structs: declaración con valores por defecto, constructor, campos, `nil`, métodos, `self`.
5. Listas de textos y de structs, structs dentro de structs, préstamos (`_dash_obj_lend`).

Cada fase: tests en `tests/` comparados con el Dash de Python en A1200 y A500 (`tests/run.py`), y el dashc
de Amiga dando ejecutables idénticos.

## Bitácora

- 2026-10-28: plan.
