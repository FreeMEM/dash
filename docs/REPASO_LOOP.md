# Repaso continuo del compilador (para `/loop`)

Arranque:

```
/loop Sigue las instrucciones de docs/REPASO_LOOP.md: haz UNA iteración del repaso y actualiza la bitácora.
```

## Objetivo

Repasar todo el compilador Dash por zonas. En cada zona: encontrar errores,
arreglarlos con un test que lo demuestre, y aplicar optimizaciones seguras.
Corrección antes que velocidad. Nada de refactors grandes.

## Reglas de cada iteración

1. **Rama.** Trabaja en la rama local `repaso`. Si no existe, créala desde `main`.
   Nunca hagas push ni toques `main`.
2. **Base.** Ejecuta `python3 tests/run_tests.py` y transpila todos los ejemplos:
   `for f in examples/*.dash; do python3 -m compiler.main "$f" -o build/ex.c >/dev/null 2>&1 || echo "FALLA $f"; done`.
   Anota el resultado si cambia respecto a la última entrada de la bitácora.
3. **Zona.** Coge la primera zona `[ ]` de la lista de abajo. Márcala `[~]` mientras trabajas.
   Una sola zona por iteración. Si es demasiado grande, divídela en la lista y haz solo la primera parte.
4. **Buscar errores.** Lee el código de la zona. Para cada sospecha, escribe un
   `.dash` mínimo que la reproduzca. Si no puedes reproducirla, no es un error confirmado:
   anótala como sospecha, no la arregles.
   Mira sobre todo: C generado inválido o con comportamiento distinto al esperado,
   fugas de memoria en el runtime, scope mal resuelto, tipos inferidos mal,
   errores que el analyzer debería dar y no da, mensajes de error confusos,
   desbordamientos (68000: `LONG` de 32 bits, alineación de `WORD` a dirección par).
5. **Arreglar.** Cada error confirmado lleva su test de regresión en `tests/test_<feature>.dash`.
   El test debe fallar antes del arreglo y pasar después.
6. **Optimizar.** Solo cambios que no alteren el comportamiento: C generado más pequeño
   o rápido en 68000, código muerto del compilador, duplicados. Si una optimización
   cambia semántica o toca más de una zona, anótala como propuesta y no la hagas.
7. **Verificar.** Repite el paso 2. Ningún test ni ejemplo que antes funcionaba puede romperse.
   Si algo se rompe y no lo arreglas en esta iteración, revierte tus cambios.
8. **Cerrar.** Marca la zona `[x]`, añade una entrada a la bitácora y haz un commit
   local en `repaso` con mensaje `repaso: <zona> - <resumen>`.
9. **Fin.** Si no quedan zonas `[ ]`, escribe en la bitácora un resumen final
   (errores arreglados, sospechas abiertas, propuestas) y termina el loop.

## Límites

- No instales el toolchain de Amiga ni paquetes del sistema. Si falta
  `/opt/amiga/bin/m68k-amigaos-gcc`, el runner solo comprueba la transpilación:
  revisa el C generado a ojo y dilo en la bitácora.
- No cambies la sintaxis del lenguaje ni decisiones de diseño. Si crees que hace falta, propónlo.
- No borres tests ni ejemplos. No toques `sesion.txt`, `*.zip` ni `amiga1200_rtg.fs-uae`.
- Si una zona exige una decisión del usuario, déjala `[?]` con la pregunta y pasa a la siguiente.

## Zonas

- [x] 1. `tests/run_tests.py`: da por bueno un test si falta GCC. Hacer que lo diga claro
      (estado "SKIP compile" o similar) en vez de contarlo como PASS completo.
- [x] 2. `compiler/grammar.py`: ambigüedades, precedencia de operadores, formas documentadas
      que no parsean (p. ej. `enum State IDLE, RUN end` de QUICK_REFERENCE).
- [ ] 3. `compiler/transformer.py` + `compiler/ast_nodes.py`
- [ ] 4. `compiler/analyzer.py`: scope, tipos, símbolos no definidos, errores que faltan.
- [ ] 5. `compiler/codegen.py` — expresiones, variables y scope.
- [ ] 6. `compiler/codegen.py` — control de flujo (if, while, for-range, for-each).
- [ ] 7. `compiler/codegen.py` — funciones, return, recursión, lambdas.
- [ ] 8. `compiler/codegen.py` — arrays, slicing y strings (concat, interpolación, memoria).
- [ ] 9. `compiler/codegen.py` — structs, métodos, enums, const.
- [ ] 10. `compiler/codegen.py` — ventanas, EventLoop, FFI (`@extern`, `@native`).
- [ ] 11. `runtime/dash_array.h` + `runtime/dash_string.h`: fugas, bounds, NULL.
- [ ] 12. `compiler/amiga_builtins.py`: firmas, tipos, liberación de recursos al salir.
- [ ] 13. `compiler/main.py` + `dash` (CLI): imports, rutas, imports circulares, códigos de salida.
- [ ] 14. `lib/amiga/*.dash` + `examples/`: `examples/test_dos_module.dash` no transpila
      (`read_line` no definida). Que todos los ejemplos transpilen.
- [ ] 15. Documentación: que `docs/QUICK_REFERENCE.md`, `docs/MANUAL_REFERENCIA.md`,
      `README.md` y `CLAUDE.md` digan lo mismo que el código.

## Bitácora

<!-- Una entrada por iteración:
### YYYY-MM-DD — Zona N
- Base: tests X/29, ejemplos Y/30 transpilan
- Errores arreglados: ... (test: tests/test_...)
- Optimizaciones: ...
- Sospechas sin confirmar: ...
- Propuestas (no aplicadas): ...
- Commit: <hash>
-->

### 2026-10-14 — Estado inicial
- Base: tests 29/29 (solo transpilación: no hay toolchain Amiga en esta máquina), ejemplos 29/30 transpilan.
- Conocido: `test_dos_module.dash` falla (`read_line`), enum en una línea no parsea.

### 2026-10-14 — Zona 1 (`tests/run_tests.py`)
- Base: tests 29/29 (solo transpilación), ejemplos 29/30 transpilan. Sin cambios.
- Error arreglado: sin GCC, el runner marcaba `compile_ok=True` y contaba el test como PASS completo.
  Ahora `compile_skipped=True`, cada test sale como "OK (transpile only)" y al final avisa
  cuántos no se compilaron. Sin test de regresión: es el propio runner; verificado a mano.
- Propuesta (no aplicada): los tests solo comprueban que compila, nunca la salida.
  Se podría comparar el C generado con ficheros esperados (`tests/expected/*.c`) o ejecutar en emulador.
- Nota: el usuario pidió instalar `m68k-amigaos-gcc` (README, BlitterStudio). En curso.

### 2026-10-14 — Zona 2 (`compiler/grammar.py`)
- Base: tests 29/29 (solo transpilación), ejemplos 29/30. Tras la zona: tests 30/30, ejemplos 29/30.
- Errores arreglados (test: `tests/test_grammar_edge.dash`, fallaba antes):
  - Comentarios dentro de `struct`, `enum` y `Window` daban error de parseo (también al final de línea).
  - `const N = -1` no parseaba. Añadido `const_neg_int`; el `#define` sale entre paréntesis `(-1)`
    para que `a-N` no genere `a--1` (también en las cabeceras de módulos).
  - `enum State IDLE, RUN end` (documentado en QUICK_REFERENCE) no parseaba: comas opcionales.
- Propuestas (no aplicadas, cambian el lenguaje):
  - Literales hexadecimales (`0xDFF000`): muy útiles en Amiga; hoy dan error de parseo.
  - Asignación encadenada `q.p.x = 5` (structs anidados): no parsea.
  - `On Key(...)` y `On Gadget(...)` existen en la gramática vieja pero no en la que se usa.
  - Propiedades de ventana booleanas (`closegadget true`): solo se aceptan strings y enteros.
  - Floats (`1.5`): no soportados (decisión de diseño, todo es `LONG`).
- Para zona 13: la gramática `dash_grammar` (flag `--extended`) ni siquiera construye
  (conflicto reduce/reduce en LALR). Es código muerto: candidata a borrar.
- Comparaciones encadenadas (`1 < 2 < 3`) dan error de parseo: correcto, no es un fallo.
