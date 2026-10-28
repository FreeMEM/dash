# Bucle de dashc: hacia Dash 2.0

Encargo (2026-10-28): con dashc (rama `dashc`, worktree `.worktrees/dashc`) llevar Dash a 2.0: un compilador
autosuficiente, sin Python ni compilador de C, que corre en Linux y en el Amiga. En este bucle: ejecutables
pequeños, más optimización donde se pueda y el lenguaje completo, con el mismo comportamiento que `./dash`.

Tope: al 90 % del uso semanal (`~/.claude/state/uso-7d.txt`) se para todo (al empezar, 32 %).
Plan anterior y decisiones de fondo: `dashc/PLAN_DATOS.md`, `dashc/README.md`.

## Cómo se mide el avance

- `dashc/tests/run.py`: los tests propios de dashc, misma salida y código de salida que `./dash` en A1200 y A500.
- `dashc/tests/cobertura.py` (por hacer, D1): los 275 `tests/test_*.dash` y los 34 `examples/` de Dash: cuántos
  compila dashc y, de los que tienen `# expect-out`, cuántos dan lo mismo en el emulador. Es la medida de "lenguaje
  completo": cada vuelta, el número sube.
- `dashc/bench/bench_run.py` (25 s): la velocidad frente a gcc no puede empeorar.
- El dashc de Amiga (`make amiga`) sigue dando ejecutables idénticos a los del PC.

## Tareas (en orden; cada una con sus tests, commit en la rama `dashc`)

- D1 `tests/cobertura.py` y la primera medida.
- D2 Tamaño: enlazar solo lo usado del runtime. El runtime se compila con `-ffunction-sections` (o en varios
  objetos) y `hunk.c` se queda con los hunks a los que se llega desde el programa. Medir: tamaño de cada test antes
  y después; un "hola" debería volver a unos 2 KB.
- D3 Núcleo que falta: enums, `const` de texto, `import` (varios ficheros, privadas con `_`), diccionarios,
  `sort`, métodos y builtins de texto (`find`, `upper`, `split`...), lambdas y `Func`, interfaces, `weak`,
  préstamos (`_dash_obj_lend`), globales de cualquier tipo.
- D4 Números: Float (softfloat), Fixed, Double, como `./dash`.
- D5 Builtins de Amiga (609 en `compiler/amiga_builtins.py`): sus runtimes en C van a la librería de dashc, como
  el resto (`gen_lib.py`), y dashc los llama.
- D6 Ventanas y eventos: `Window`, `EventLoop`, GadTools, MUI, ReAction, `.dashui`.
- D7 `@native`: es C. `lib/amiga` lo usa 93 veces; los tests, 92. Decidido por el usuario (2026-10-28): el
  `@native` de `lib/amiga` se compila al construir dashc (ahí sí hay gcc) y va en su librería; el de un programa
  del usuario NO se admite en Dash 2.0. Lo que hacen los `@native` de tachyon (137), trasfondo (33) y Lorraine (1)
  se cubre con builtins o con el lenguaje: clasificación en `docs/DASHC_NATIVE.md`.
- D8 Optimizaciones nuevas que salgan al medir programas reales (no solo enteros).
- D9 Cierre: `./dash` llama a dashc (o dashc pasa a ser `dash`), documentación en dos idiomas, versión 2.0.

## Bitácora

- 2026-10-28: plan.
- D1 hecha: `dashc/tests/cobertura.py`. Primera medida: compila 24 de 309 (7 %); en el A1200, 4 de 23 con la
  salida esperada. Errores más repetidos: `@` (95: `@native`, `@header`...), sintaxis aún no admitida (94),
  funciones que no existen (42: builtins), Float (17), `{` (13: diccionarios). Algún programa se cuelga (la
  vuelta en el emulador duró 15 min): sospecha, un `for` con paso negativo sabido solo al ejecutar (dashc solo
  mira el signo si el paso es fijo; ./dash lo mira al ejecutar).
- D2 hecha: el runtime con `-ffunction-sections -fdata-sections`, los objetos sin `ld -r` (uno tras otro) y
  `hunk.c` se queda con los hunks a los que se llega y los junta en código, datos y BSS (`DASHC_MAPA=1` enseña qué
  entra). Tamaños: textos 12.208 → 3.416 bytes (gcc 6.436), funciones 4.188 (gcc 7.236), cadenas 10.536 (gcc
  12.952), listas 14.112 (gcc 17.512), árbol 12.520 (gcc 13.220): todos por debajo de gcc. Los 12 tests bien.
  Idea para D8: llamar al runtime con `jsr d16(pc)` en vez de `jsr abs.l` (ahora que va en el mismo hunk): 2 bytes
  menos y una reubicación menos (4 bytes) por llamada.
- D3 (1.ª parte): arreglado el `for` con paso sabido al ejecutar (el sentido, por su signo, como ./dash: era lo
  que colgaba la cobertura). `dashc --memcheck` (el runtime con DASH_MEMCHECK, segundo blob dentro de dashc; el
  sitio de cada instrucción en `_dash_mc_where`; al acabar Main se suelta todo). Préstamos de argumentos (textos de
  campos, globales y elementos, como copia; objetos con `_dash_obj_lend`; un campo que nada cambia, tal cual). La
  cobertura compila como el runner (ruta relativa, `--memcheck` con `# memcheck`): 23 de 23 iguales en el A1200
  (antes 4). Siguen compilando 24 de 309.
- D3 (2.ª parte): `import` (relativo al fichero que importa, a sus carpetas de más arriba y a la carpeta actual; cada
  fichero una vez; los errores, al compilar y al ejecutar, con su fichero: `_dash_srcfiles` de 64, la tabla la pone
  dashc). `enum` (cada miembro, el anterior + 1; un tipo enum es Int) y `Wait`. Una función de una línea con un
  campo ya no se pone como expresión (el nil diría la línea de quien llama). Test `importa`. Cobertura sin emulador:
  25 de 309; al entrar los módulos, el `@` sube a 113.
- D7: clasificados los `@native` del usuario (171 bloques): `docs/DASHC_NATIVE.md`. Lo que bloquea es Tachyon
  (QuickJS, vídeo, HTML5, imágenes, fuentes, red de fondo: 97 bloques); propuesta, módulos nativos precompilados con
  firmas `@extern`. Para el resto, ~25 builtins pequeños y `task_start` con funciones Dash.
- D7 (1.ª parte): los `@native` de `lib/amiga` van en la librería (gen_lib.py los saca con un envoltorio `dn_nombre`
  todo en LONG; `natives.h` con sus cabeceras; `GfxBase` se abre al arrancar, como libnix). dashc lee `@native`,
  `"""...""""` y `@stack` (que aún no cambia la pila); cualquier otra `@` da "Dash 2.0 no admite C en los
  programas", y un `@native` que no está en la librería, lo mismo. Pendiente: `intuition.dash` (usa la ventana del
  runtime de ventanas: D6). `Pointer` es un número de 32 bits. Test `nativos`. Fallo visto en ./dash: no compila
  `memory.dash` si el programa no usa listas.
- D5 (1.ª parte): builtins. `runtime/build_lib.py` (make runtime) monta la librería: gen_lib.py añade a la cocina
  una llamada a cada builtin que no es de ventanas, gráficos, sonido ni Double (215 de 686) para que ./dash ponga
  su runtime, y un envoltorio `db_nombre(LONG...)` con su plantilla; zlib (opciones de compiler/clibs.py), libc
  mínima (sprintf, strcpy, strstr...), `__bcopz` y la aritmética de 64 bits de libgcc. `runtime/builtins_tab.c`
  (de amiga_builtins.py, en git): parámetros, tipo devuelto y si guarda lo que recibe (escapa textos y objetos
  como ./dash). Tamaño: la limpieza de cada runtime va por un puntero débil (`_dash_weak_*`: hunk.c no lo cuenta
  como uso y lo deja a 0 si no entra) y cada bloque de ensamblador suelto en su sección; los programas vuelven a
  quedar por debajo de gcc (textos 5.804, gcc 6.436). Quedan 2,2 KB de textos constantes del runtime en una sección
  que gcc no trocea. La librería pesa 211 KB (dos: normal y memcheck): para el dashc de Amiga habrá que adelgazarla
  (quitar símbolos) o cargarla de un fichero. Arranque desde el Workbench: pendiente (`_WBenchMsg` a 0).
- Decidido por el usuario (2026-10-28), para el C de los programas (docs/DASHC_NATIVE.md): camino mixto.
  Builtins de Dash para lo general (gzip, decodificar imágenes, fuentes TTF/WOFF, red en segundo plano, vídeo y
  los ~25 pequeños de sistema); módulo precompilado solo para QuickJS y HTML5 (exclusivos de Tachyon). El módulo:
  su C en ficheros .c del proyecto, un Makefile con el gcc de bebbo (`-ffunction-sections`) que deja un objeto
  Hunk (p. ej. `build/js.o`, se rehace solo si cambia el C); en Dash, `@extern func ...` con las firmas y
  `@link "build/js.o"`; dashc lo lee y enlaza como su runtime (hunk.c ya lee objetos Hunk), también en el Amiga
  sin compilador. Falta: que dashc exporte con nombre de C las funciones Dash que llama ese C (jsdom_*) y una
  cabecera `dash.h` con la API del runtime para ese C (en vez de `_dash_str_dup` y compañía).
- D3 (3.ª parte): diccionarios `{String: T}` y `{Int: T}` (tipo `TY_DICT` + n en `dict_types`; literal con
  `DashDict_from`/`fromi`, `d[k]`, `d[k] = v`, `has`, `remove`, `get(k, defecto)`, `keys()`, `clear()`,
  `.length`; `{}` aprende qué guarda con lo primero que se mete). Los 6 tests de diccionarios de Dash, iguales en
  el A1200. `@version` (el `$VER:` como ./dash); `@catalog`, `@workbench_output` y `@extern` dicen "aún no está".
  `\"` dentro de `#{...}`. Globales de cualquier tipo con cualquier valor inicial (al empezar Main). Test `dicc`.
  La cobertura completa anterior se torció: tras `test_args` (argumentos de la línea de órdenes, que el arranque
  de dashc aún no lee) los demás programas no sacaron nada; se repite.
- Arranque como libnix: la línea de órdenes (a0/d0 de AmigaDOS) partida en argc/argv con sus comillas (`arg`,
  `arg_count`); desde el Workbench, su mensaje (`_WBenchMsg`), la carpeta del programa como actual y el mensaje
  devuelto en Forbid al acabar. El código de entrada ya no pisa a0/d0 (main y los ficheros van en la pila).
  Test `argumentos`; la cobertura pasa `# emu-args:`.
- D4 (1.ª parte): Float, como ./dash: el float de gcc por software (fp-bit.c en simple con sus nombres cambiados
  y fastfp.c, de compiler/softfloat.py, una sección por función; de libgcc `__fixunssfsi` y `__clzsi2`).
  Literales (`1.5`, sus bits al compilar), `+ - * /` (`__addsf3`...), comparaciones (`__cmpsf2`), signo
  (eori del bit 31), `Int()`/`Float()` (también `Int("12")`), mezcla con Int (convertido al compilar si es fijo),
  `Print` e interpolación (`DashString_from_float`), parámetros y valores devueltos Float. Test `flotantes`.
  Falta: listas y campos Float con valores Int, Double, Fixed.
