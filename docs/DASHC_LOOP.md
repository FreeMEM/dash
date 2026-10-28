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
- Cobertura completa (antes de Float): compila 72 de 309; en el A1200, 54 de 61 iguales. Arreglados los 7 que
  fallaban: el temporizador (`_dash_finish` cerraba el de bench mirando `TimerBase`, que también pone el runtime de
  tiempo: un puntero nulo colgaba el Amiga y a los siguientes; `time_ms` cuenta desde el arranque con un puntero débil
  a `_dash_time_init`), textos adoptados que no eran temporales (constructor y `c.t = t` copian si no es un temporal
  nuevo), el elemento de `for x in lista` retenido durante la vuelta (el cuerpo puede vaciar la lista), las globales
  del programa no se ven desde sus módulos (dashweb D14) y `+` de listas (`DashArray_concat`).
- D6 (1.ª parte): `Window` (propiedades y valores por defecto de ./dash; un DashWinDesc en el código y una variable
  en los datos), `.open`/`.close`, `EventLoop` con `On Close`, `On Key` ("a", 69 o un nombre de KEY_NAMES), `On
  Click`, `On Timer` y `Stop`; la espera, apuntar la tecla o el clic y ReplyMsg en C (`dl_event_next`, api.c) y el
  reparto por clase en 68000. Las ventanas abiertas se cierran al salir (puntero débil). Builtins `gfx_*` y los de
  `needs_gfx` (sin pantallas, bitmaps ni fuentes). Test `ventana` (se para sola con On Timer). Cobertura: 64 de 64
  en el A1200 antes de esto. Falta: On Gadget, On Menu, GadTools, MUI, ReAction, pantallas, `.dashui`.
- Cobertura con ventanas: compila 111 de 309 (35 %); en el A1200, 67 de 67 iguales. Lo que más falla: `@header`
  y `@c` (47, C), `mui_app_begin` (15), `screen_open` (8), tipos aún no admitidos (7), `.dashui` (6),
  `image_from_rgb` (5).
- D6 (2.ª parte): GadTools. Builtins de gadgets (`button_create`...), `gt_*`, `menu_*`, pantallas, bitmaps,
  imágenes, fuentes, sprites, bobs y copper en el runtime. `On Gadget` (la espera con GT_GetIMsg y el gadget del
  mensaje apuntado, `dl_event_gt_on`; las teclas de los gadgets "_Vale") y `On Menu` (una vez por opción elegida,
  `dl_menu_next`); los IDCMP de gadgets y menús al abrir la ventana. `x.abs()` de Int. De libnix y amiga.lib,
  en `runtime/rt_libs.s`: `LayersBase`, `UtilityBase` (cada base con su apertura, por puntero débil) y
  `DoMethod`; gadtools.library se abre igual (`dl_gt_open`). Test `gadgets` (input_click y Amiga + Q).
- D2, tamaño (con lo de arriba, que lo hacía crecer):
  - Fallo arreglado: las limpiezas de los runtimes (`_dash_lt_cleanup` del temporizador, fuentes, imágenes, red,
    gadgets...) no entraban nunca: solo las apuntaba un puntero débil. Ahora hunk.c mete la de un puntero débil
    si toca datos que el programa usa y que no son del arranque (ni `_dash_win`/`_dash_rp`), hasta que no entre
    ninguna más.
  - Los textos constantes del runtime (2,5 KB en un `.text` sin trocear) se parten en un hunk por texto
    (`split_strings`): cada programa lleva solo los suyos.
  - Las llamadas débiles de `_dash_exit_cleanup`, en una tabla con un bucle (de 576 bytes a unos 250).
  - aritmetica: 7.076 → 4.808 bytes (gcc 7.464); ventana 10.756 → 8.912; listas 16.516 → 15.040.
- D6 (3.ª parte) y D3: ventanas por número (`window_create`, `close_window`, `event_window`: el EventLoop
  escucha también esas ventanas, por puntero débil; `dl_window_open` recibe la variable de la ventana para
  dejarla a nil al cerrarla de otra forma), ASL (`file_open_dialog`...), audio (`sound_*`, `music_*`, con
  `BeginIO` de amiga.lib), relleno de áreas (`gfx_circle_fill`...: `dl_init_area` al abrir) y RTG.
  `malloc`/`free` (zlib) en un pool que se borra al salir. Núcleo: parámetros sin tipo deducidos de la primera
  llamada (`infer_params`), `for c in texto`, constantes de texto y Float, `var x: Tipo` sin valor (0 o nil),
  escapes de C en los textos (`\33`, `\x1b`, `\e`...). Compilan 159 de 309 (antes 111).
- Cobertura: compila 158 de 309 (51 %); en el A1200, 91 de 91 iguales (los `# rtg` se saltan: piden tarjeta
  gráfica, con gcc fallan igual en este A1200). Arreglado en `split_strings`: con varias referencias al mismo
  texto, el hunk se quedaba con tamaño 0 (deflate de zlib no veía su versión y daba -1); además, un hunk con
  bytes de control raros (tablas binarias) ya no se trocea.
- D4 (2.ª parte): Double. En dashc es una caja: un texto de 16 cifras hexadecimales con sus 8 bytes, para que su
  variable, campo, global o elemento sea dueño de él con lo que ya hay para los textos (copias, temporales,
  marcas, liberación, `--memcheck`). Las cuentas, en api.c (`dl_d_op`, `dl_d_cmp` con nan, `dl_d_neg`,
  conversiones, `dl_d_str` con Ryu), con el float doble de gcc por software (fp-bit en doble, como ./dash; de
  libgcc `__extendsfdf2` y `__clzdi2`). Un literal o un número fijo es una caja constante hecha al compilar
  con todas sus cifras (el lexer guarda el double del literal). Builtins de math (fdlibm) y `str_from_double`
  con cajas (`dparams` en la tabla de builtins). Listas: un elemento se convierte al tipo de la lista (también
  Int a `[Float]`, pendiente de D4) y una lista literal toma el tipo de su destino (`[Double]` de un campo, de
  un `var`, de un diccionario o de una lista de listas). test_double, test_double_lists, test_double_texto y
  test_math, iguales que con gcc (y sin nada vivo con `--memcheck`). Test `dobles`. Es más lento que en
  registros: las cajas son para tener el lenguaje completo; si Lorraine lo pide, D8 puede pasar a d0/d1.
- Cobertura con Double: compila 167 de 309 (54 %); en el A1200, 100 de 100 iguales. Batería de dashc bien.
- D6 (4.ª parte) y D3: MUI y funciones como valor.
  - MUI 5: los builtins `mui_*` en el runtime (con el SDK de MUI al construirlo, tools/get_mui_sdk.sh; sus
    cabeceras no van en git) y `DoSuperMethod(A)` de amiga.lib en rt_libs.s.
  - La pila de verdad (antes en D8): el código de entrada pasa la que quiere (16 KB, 32 KB con MUI, 64 KB con
    AmiSSL, más con `@stack`, como ./dash) y `_dash_start` cambia a una nueva con `StackSwap` si la del shell
    es menor; `_dash_quit` vuelve a la de antes desde donde sea. Sin esto MUI avisaba de 4 KB y se paraba.
  - Funciones como valor: el nombre de una función sin llamarla es su dirección (`E_FUNCREF`, al resolver el
    programa), el tipo `Func`, la llamada a través de una variable (`g(4)`: `jsr (a0)`, como una de C), lambdas
    `fn(a, b) -> expresión` (funciones `__fn_N`), `lista.sort(f)` (`DashArray_sort`, con f de Bool o de Int,
    como ./dash) y `mui_canvas_on_draw(lienzo, pinta)`. Una función de una línea que llama a un parámetro no
    se sustituye (el nombre de la llamada no es un nodo). test_func_values, test_functions_adv y test_list_sort,
    iguales.
  - La cobertura arranca aparte los que piden MUI (`$DASH_EMU_SYS_MUI`).
- Cobertura con MUI: compila 182 de 309 (58 %); en el A1200 (y los de MUI en su arranque), 112 de 112 iguales.
- D6 (5.ª parte): `import "x.dashui"`. `dashc/src/dashui.c` (un lector de JSON y el generador de
  compiler/dashui.py pasado a C) da el código Dash de las ventanas, que se compila como un módulo más. Con los 13
  `.dashui` del repositorio, el mismo código que el de Python (`dashc --dashui fichero` lo saca). El dashc de
  Amiga enlaza con `-lm` (strtod y los double de los literales: faltaba desde Float).
- dashc dentro del Amiga (A1200 emulado), otra vez: se colgaba compilando Double (los double de libnix van a
  mathieeedoubbas de la ROM, que en FS-UAE se cuelga como la de simple): ahora enlaza el float por software del
  runtime (fp-bit en doble y simple, fastfp), como ./dash. Y el strtod de libnix fallaba en la última cifra de
  `1.0e300`: los literales pasan por el s2d de Ryu (exacto, en los dos dashc). Con dobles, flotantes, dicc,
  aritmetica, ventana y gadgets, ejecutables idénticos a los del PC.
- D6 (6.ª parte): ReAction. Los builtins `ra_*` en el runtime y `NewList` de amiga.lib en rt_libs.s.
  test_reaction_values y test_ra_more (con `--memcheck`), iguales en el A1200 con 3.2 (`--machine a1200-32
  --workbench`; la cobertura no lo arranca, los demás de ReAction llevan C).
- D4 (3.ª parte): Fixed, coma fija 16.16 en un LONG como ./dash: un literal, al compilar (`Fixed(1.5)` = 98304);
  un Int, `swap`/`clr.w` (<< 16); un Float, × 65536. `+ - %` y comparaciones con los dos lados Fixed (el Int se
  convierte), `*` y `/` por un Int como enteros, Fixed × Fixed y Fixed / Fixed por el runtime (`_dash_fx_mul`,
  `_dash_fx_div`), `fx_sqrt`, `fx_sin`, `fx_cos`, `Int()`, `Float()`, texto, campos, parámetros, return y listas.
  Arreglos de paso: la sustitución de una función de una línea no convierte (no se hace si un parámetro o lo que
  devuelve es Float, Double o Fixed y el argumento no), y `fold` no junta cuentas de Fixed que no son de
  enteros. test_fixed y test_fixed_lists, iguales.
  - Fallo visto al meter ReAction: `_ra_close_all()` de `_dash_exit_cleanup` se llamaba directo (el filtro de
    limpiezas débiles solo cogía `_dash_` y `dl_`), así que cada programa saltaba a ReAction sin abrirla
    (excepción en una librería de base 0 en el A500 y la cobertura tumbada). Ahora cualquier llamada suelta de la
    limpieza va por puntero débil.
- Cobertura: compila 192 de 309 (62 %); en el A1200 (y MUI), 115 de 115 iguales. Batería bien.
