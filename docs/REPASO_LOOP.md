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

- No instales paquetes del sistema. El toolchain está en `/opt/amiga` (GCC 6.5.0b, instalado
  el 2026-10-14). Comprueba también los ejemplos con `./compile_all.sh`.
- GCC 6 solo avisa de conversiones entero/puntero que un GCC moderno trata como error:
  revisa los avisos de `-Wint-conversion` en el C generado.
- No cambies la sintaxis del lenguaje ni decisiones de diseño. Si crees que hace falta, propónlo.
- No borres tests ni ejemplos. No toques `sesion.txt`, `*.zip` ni `amiga1200_rtg.fs-uae`.
- Si una zona exige una decisión del usuario, déjala `[?]` con la pregunta y pasa a la siguiente.

## Zonas

- [x] 1. `tests/run_tests.py`: da por bueno un test si falta GCC. Hacer que lo diga claro
      (estado "SKIP compile" o similar) en vez de contarlo como PASS completo.
- [x] 2. `compiler/grammar.py`: ambigüedades, precedencia de operadores, formas documentadas
      que no parsean (p. ej. `enum State IDLE, RUN end` de QUICK_REFERENCE).
- [x] 3. `compiler/transformer.py` + `compiler/ast_nodes.py`
- [x] 4. `compiler/analyzer.py`: scope, tipos, símbolos no definidos, errores que faltan.
- [x] 5. `compiler/codegen.py` — expresiones, variables y scope.
- [x] 6. `compiler/codegen.py` — control de flujo (if, while, for-range, for-each).
- [x] 7. `compiler/codegen.py` — funciones, return, recursión, lambdas.
- [x] 8. `compiler/codegen.py` — arrays, slicing y strings (concat, interpolación, memoria).
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

### 2026-10-14 — Zona 3 (`transformer.py` + `ast_nodes.py`)
- Base: tests 30/30, ejemplos 29/30. Tras la zona: tests 31/31, ejemplos 29/30.
  El C de todos los tests y ejemplos previos sale idéntico byte a byte.
- Errores arreglados (test: `tests/test_transformer_edge.dash`, fallaba antes):
  - `Wait n` o `Wait n + 1` rompía el compilador (`int()` sobre un nodo). Ahora acepta
    cualquier expresión: `Delay((n) * 50)`.
  - `@native` con el cuerpo en una línea (`"""return 1;"""`) se tomaba como tipo de retorno
    y la función salía vacía sin avisar. Ahora el cuerpo se marca con `_NativeCode`.
  - Lambda de bloque (`fn(x) ... end`): solo quedaba la última sentencia, tratada como expresión
    (`return /* unknown expr */`). Además el codegen llamaba a `_generate_statement` con 3 argumentos
    y declaraba `void` aunque hubiera `return`. Ahora genera el cuerpo con su scope y tipo `LONG` si devuelve valor.
- Para zona 4: dos bloques `Main` se aceptan y el primero se descarta sin avisar.
- Para zona 7: `f = fn(x) -> ...` genera `LONG f = (APTR)_dash_lambda_1;` (puntero en un `LONG`).
- `ast_nodes.py`: dataclasses simples, sin errores encontrados.

### 2026-10-14 — Zona 4 (`compiler/analyzer.py`)
- Base: tests 31/31, ejemplos 29/30. Tras la zona: tests 38/38 (32 normales + 6 de error), ejemplos 29/30.
- Novedad en el runner: `tests/errors/*.dash` son tests que deben FALLAR con el texto de su línea `# expect: ...`.
- Errores arreglados (tests en `tests/errors/`, todos fallaban antes; caso válido en `tests/test_analyzer_checks.dash`):
  - El cuerpo de las funciones y métodos nunca se analizaba: variables o funciones inexistentes
    pasaban y daban C inválido. Ahora se analizan; los métodos ven `self` y sus parámetros.
  - Reasignar un parámetro (`n = n + 1`) daba "not a variable" (latente hasta analizar funciones).
  - `Print` no analizaba su expresión: `Print y` con `y` local a un `if` pasaba y el C no compilaba.
    `Wait` tampoco analizaba la suya.
  - Una función de usuario con nombre de builtin (`func random()`) se ignoraba: la llamada iba al builtin.
    Ahora es error.
  - Dos bloques `Main`: el segundo sustituía al primero sin aviso. Ahora es error (`Program.extra_mains`).
- Fallos destapados por el análisis de funciones, arreglados:
  - `lib/amiga/graphics.dash`: `clear_with_color(c)` llamaba a `gfx_clear(c)`, que ignora el argumento
    y borraba siempre con color 0. Ahora usa `gfx_clear_color(c)`.
  - `examples/test_native.dash`: sus `@native peek_byte/poke_byte` chocaban con builtins del mismo nombre.
    Renombradas a `native_peek/native_poke`.
- Para zona 13 (`main.py`, imports):
  - Las funciones privadas (`_x`) de un módulo se descartan al fusionar: si una pública las llama, el C queda sin ellas.
  - Los `@header` de módulos importados se pierden (solo se conservan los del programa principal).
- Para zona 7: el codegen da prioridad a los builtins sobre funciones de usuario; hoy queda cubierto por el error nuevo.

### 2026-10-14 — Zona 5 (codegen: expresiones, variables, scope)
- Base: tests 38/38, ejemplos 29/30. Tras la zona: tests 40/40, ejemplos 29/30.
- Novedad en el runner: líneas `# expect-c: <texto>` en un test exigen ese texto en el C generado.
  Sin GCC es la única forma de detectar regresiones de contenido.
- Errores arreglados (test: `tests/test_string_types.dash` con `expect-c`, y `tests/errors/string_to_number_var.dash`; fallaban antes):
  - Parámetros `String` se trataban como número: `nombre + "!"` era aritmética de punteros.
  - `a == "x"` comparaba punteros. Ahora `strcmp(a, "x") == 0` (igual con `!=`).
  - `"Total: " + n` pasaba un `LONG` como `STRPTR`. Ahora `DashString_from_int(n)` (nuevo en el runtime,
    8 buffers rotatorios; probado en host con 0, negativos, `LONG_MIN` y concatenación anidada).
    También `n + " items"` y la interpolación `"#{n}"` con números.
  - `not a == b` se leía `(not a) == b`. Ahora `not` va por debajo de las comparaciones, como en Python.
  - El tipo de las variables (`var_types`) se compartía entre funciones: un parámetro `s` salía con `%s`
    porque otra función tenía un `s` string. Ahora cada función, método y lambda tiene su copia.
  - Funciones que devuelven string (`-> String`, `return "..."` o builtins `STRPTR`) se trataban como `LONG`.
    El tipo de retorno ahora se busca también en bloques anidados y tras generar el cuerpo.
  - `Print "100%"` usaba el texto como formato de `Printf`. Ahora se escapa `%`.
  - Reasignar una variable con otro tipo (`x = 1` luego `x = "hola"`) generaba C inválido. Ahora es error.
- Optimización: `Print` genera una sola llamada (`Printf("texto\n")`) en vez de dos. C de 68000 más corto.
- Efecto en ejemplos: `test_gadtools` declara `path`/`name` como `STRPTR` (antes `LONG`). Resto: solo `Printf`.
- Pendiente (zona 8): `DashString_concat` reserva memoria que nunca se libera.
- Pendiente (zona 11): `runtime/*.h` no se usa; el codegen lleva su propia copia del runtime.
- Pendiente: concatenar un carácter (`s + s[0]`) pasa un `char` como `STRPTR`.

### 2026-10-14 — Zona 6 (codegen: if, while, for-range, for-each)
- Base: tests 40/40, ejemplos 29/30. Tras la zona: tests 41/41, ejemplos 29/30.
- Errores arreglados (test: `tests/test_loops.dash` con `expect-c`, fallaba antes):
  - `for c in texto` usaba `DashArray_length` sobre un `STRPTR`. Ahora recorre los caracteres (`char c`).
  - La variable del bucle heredaba el tipo de otra con el mismo nombre (`for s in nums` imprimía con `%s`).
  - El final del rango se evaluaba en cada vuelta (`for i in (1..f())` llamaba a `f` cada vez).
    Ahora se evalúa una vez, como un rango de Python (`_end_i`). Si es un literal se deja tal cual.
  - `c == "n"` con `c` carácter (o `s[0] == "A"`) llamaba a `strcmp` con un `char`. Ahora compara `'n'`.
- Comprobación nueva: cabeceras Amiga falsas en el scratchpad para pasar `gcc -fsyntax-only` en el host.
  `test_loops` y `test_string_types` compilan limpios. Faltan stubs de ventanas (zona 10).
  Confirmado con ella: `f = fn(x) -> ...` mete un puntero en un `LONG` (error en GCC moderno) → zona 7.
- Sin cambios: `if`/`while` correctos. La variable de un `for` es local al bucle (coherente con el scope de bloque).
- Propuestas: `break`/`continue` no existen; rangos descendentes (`10..1`) no iteran.
  Cosmético: las plantillas de `if`/`while` sangran 4 espacios de más.

### 2026-10-14 — Zona 7 (codegen: funciones, return, recursión, lambdas)
- Base: tests 41/41, ejemplos 29/30. Tras la zona: tests 45/45, ejemplos 29/30.
- Errores arreglados (test: `tests/test_functions_adv.dash` con `expect-c`, compila limpio con stubs en host;
  y `tests/errors/{lambda_capture,void_func_as_value,call_untyped_param}.dash`; todos fallaban antes):
  - Las lambdas no se podían llamar (`doble(4)` daba "not a function") y se guardaban en un `LONG`.
    Ahora se guardan en `APTR` y se llaman con cast: `((LONG (*)(LONG))doble)(4)`. Igual con parámetros `f: Func`.
  - `_dash_type_to_c` estaba definido dos veces; la segunda anulaba la primera y perdía `Func`.
    Había además 6 mapas de tipos copiados a mano. Ahora hay uno (`_BASE_C_TYPES`) que también
    convierte nombres de struct en `_Dash_X *`.
  - Parámetros de tipo struct (`q: Punto`) salían `LONG`: `q->x` no compilaba.
  - El resultado de funciones que devuelven array o struct se guardaba en `LONG`. Ahora el llamante usa
    el tipo de retorno (con protección contra recursión al inferirlo).
  - Usar como valor una función sin `return` con valor (`v = nada()`) daba C inválido. Ahora es error
    (`FunctionCall.is_statement` distingue la llamada como sentencia).
  - Una lambda que usa variables locales de fuera generaba C inválido (es una función C de nivel superior).
    Ahora es error con explicación. El analyzer ya revisa el cuerpo de las lambdas.
- Cosmético: las llamadas como sentencia usaban siempre 4 espacios de sangría; ahora la del bloque.
- Propuestas: funciones que devuelven tipos mezclados (`"pos"` y `0`) no dan error; llamar a un
  constructor de struct como sentencia (`P(1)` suelto) genera C inválido; no hay expresiones como
  sentencia (`f(1) + 2` no parsea).

### 2026-10-14 — Zona 8 (codegen: arrays, slicing, strings, memoria)
- Toolchain instalado durante la zona: `m68k-amigaos-gcc` 6.5.0b en `/opt/amiga`.
  Tests 46/46 compilan de verdad para Amiga. Ejemplos: 26/30 compilan (`./compile_all.sh`).
  Fallan, y ya fallaban en `main`: `test_dos_module` (`read_line`), `flowpaint3` y `test_reaction`
  (`render_canvas` sin definir al enlazar), `test_rtg` (falta `cybergraphx/cybergraphics.h` en el NDK).
- Errores arreglados (test: `tests/test_arrays_adv.dash` con `expect-c`, fallaba antes):
  - Un array literal fuera de una asignación directa perdía sus valores: `return [1, 2, 3]` o `f([4, 5])`
    generaban `DashArray_create(3) /* init: ... */`, un array de ceros. Ahora `DashArray_from(3, (LONG[]){1, 2, 3})`.
  - Fugas permanentes: arrays y strings se pedían con `AllocMem` y nunca se liberaban; en AmigaOS esa
    memoria se pierde hasta reiniciar. Ahora salen de un pool de exec (`_dash_alloc`) que se borra al
    final del programa (`_dash_mem_cleanup()` antes de cerrar librerías). Requiere exec V39 (OS 3.0).
  - Arrays de strings: se guardaban sin cast y se imprimían como número. Ahora se guardan como `(LONG)`
    y se leen como `(STRPTR)`, también en for-each.
  - `"x" + s[0]` pasaba un `char` como `STRPTR`. Ahora `DashString_from_char`.
  - Arrays pasados a parámetros sin tipo (y leídos dentro) mezclaban `LONG` y puntero: ahora hay cast en
    la llamada (`(LONG)arr`) y dentro (`(DashArrayLong *)arr`). El resultado de un slice se declara como array.
- Optimización: un array literal asignado es una sola llamada en vez de `create` + un `set` por elemento.
- Pendiente: los strings y arrays siguen sin liberarse durante la ejecución (solo al salir); un bucle
  que concatena crece sin límite. Decisión de diseño abierta (GC o manual).
- Para zona 12: `render_canvas` se usa pero no se define.
