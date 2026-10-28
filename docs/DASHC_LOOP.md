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
- D10 QuickJS y Hubbub como librerías compartidas (en `LIBS:`, con nombre propio), pedido por el
  usuario (2026-10-28): con `@link`, cada programa lleva su copia (QuickJS, unos 800 KB); una `.library` se carga
  una vez y la usan todos los programas, y se actualiza sin recompilarlos. Hace falta: la librería con su tabla de
  funciones (libinit de bebbo), dentro lo de libc que necesitan (`realloc`, `snprintf`...), que la abran varios
  programas a la vez (estado por apertura) y que dashc llame a funciones de librería (registros y base) con
  `@extern("dashjs.library")`. Antes, Tachyon compilando con `@link` (D7).
  Nombres propios (`dashjs.library`, `dashhtml5.library`), no `quickjs`/`hubbub`: que otro port (NetSurf...) no
  pise la versión de Dash ni Dash la suya; el programa pide una versión mínima al abrirla.
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
- D3 (4.ª parte): interfaces, `weak`, `-> Void`, `Win.width` y compañía, lambdas de bloque, `#{` sin cerrar.
  - Interfaces como ./dash: cada método de interfaz tiene un slot del programa; el `_DashType` de un struct que las
    cumple (`struct Cuadro: Figura, Orden`) lleva detrás su tabla de métodos, y `o.metodo()` salta por ella
    (cabecera del objeto a -4, tabla a 8 del tipo); los métodos de la tabla se generan siempre. test_interfaces y
    test_interfaces_module, iguales (con `--memcheck`).
  - `weak padre: Nodo`: se guarda sin referencia y el destroy del struct no lo suelta; con `--memcheck`, leer uno
    de un objeto ya liberado es un error (`_dash_weak_check`). test_weak y test_weak_dangling, iguales.
  - `Win.width`, `height`, `left`, `top`, `title` e `inner_*`: de la ventana abierta o de su definición
    (`dl_win_member`). `-> Void`. `fn(x)` con el cuerpo debajo y `end`. Un `#{` sin cerrar es texto.
  - Regresión arreglada: un local de un módulo con el nombre de una función del programa (`inicio`) se tomaba
    por la función como valor; ahora una variable o un parámetro de ese cuerpo tapa a la función.
  - Cobertura: compilan 200 de 309 (64 %); en el A1200 (y MUI), 123 de 123 iguales. Batería bien.
- D3 (5.ª parte): lo que faltaba del lenguaje sin C.
  - Nombres privados por módulo: al leer un módulo, lo que declara con `_` delante (func, const, var, struct,
    enum, interface) se lee como `_x__mN` (N, su número de fichero), también en los `#{}`; tras un `.` no (campos).
    test_private_per_module y test_private_names_per_module, iguales. Los errores lo enseñan sin el sufijo.
  - `@catalog "X.catalog" versión ["idioma"]`: el programa pone el nombre, la versión y el idioma en variables del
    runtime al arrancar (`set_rt_var`), antes de los globales (que pueden llamar a `tr`). test_catalog, igual.
  - Desde el Workbench, dashc no abría consola (la salida iba a un Output() nulo). Ahora abre la de libnix
    (`CON://///AUTO/CLOSE/WAIT`) o la de `@workbench_output` (gana la del programa a la de un módulo), y la
    cierra al final. Probado con un lanzador como el del Workbench (de ./dash): a un fichero y a `NIL:`, igual
    que gcc. La consola por defecto no se prueba (espera a que la cierren). Cuesta 304 bytes a cada programa.
  - `wifi_*` y `usb_*` ya van en la librería (no hacía falta quitarlos). test_meter_net, igual.
  - La cobertura ya ejecuta los tests con `# emu-needs:` que el sistema tiene, los de `# emu-catalog:` (con su
    catálogo en el disco) y los de `# emu-net:` (arranque aparte con la bsdsocket de FS-UAE y el eco del runner).
  - Lo que queda sin compilar es todo C (`@header`, `@c`, `@native`, `@link`): `task_start` con funciones
    `@native` y `@native(borrow)` también lo son.
  - Cobertura: compilan 205 de 309 (66 %); en el A1200 (MUI y red), 132 de 132 iguales. Batería bien.
  - Un error que salía al generar código (no al leer) en un módulo llevaba el nombre del fichero principal con la
    línea del módulo: `fatal_node` pone el fichero del nodo.
- D7 (1.ª parte): builtins nuevos para lo que los programas del usuario hacían con `@native` (conclusión 3 de
  `docs/DASHC_NATIVE.md`), en ./dash (runtime `SYSINFO_RUNTIME`) y por tanto en la librería de dashc: `time_unix`,
  `clock_days`, `mem_largest`, `run_command` (espera; vacía antes el búfer de `Print`), `wb_open`, `program_path`,
  `locale_language`, `cpu_model`, `fpu_model`, `library_version`, `task_priority` y `console_flush`. 698 builtins
  (recuentos de la documentación en los dos idiomas al día). tests/test_sysinfo.dash: igual con gcc y con dashc
  (10.984 bytes frente a 11.960).
  - Tests de ./dash: 456 bien (con la gramática de VS Code regenerada); batería de dashc bien; cobertura: compilan
    206 de 310 (66 %) y en el A1200 (MUI, red y catálogos) 133 de 133 iguales.
  - Pendientes de la conclusión 3: `input_qualifiers`, `mui_set_active`, `mui_window_move`, `dialog_file_at`,
    `build_date`/`build_time` (son del momento de compilar: dashc los pondría como texto), y los de pruebas
    (`window_find`, `input_event`, `input_move_screen`, `input_menu`, `screen_pixel`, `gadget_find`, `cx_send`).
- D7 (2.ª parte): `input_qualifiers`, `mui_window_move`, `mui_set_active`, `dialog_file_at`, `build_date` y
  `build_time` (704 builtins, 96 de MUI). En dashc, `build_date()`/`build_time()` son un texto hecho al compilar
  (parser.c); en ./dash, `__DATE__` en ISO y `__TIME__`. Tests: test_mui_move_active, test_dialog_file_at (sin C:
  se relanza con `run_program(program_path())` y la copia pulsa Return con `input_key` medio segundo después de
  ver el diálogo: antes, el campo aún no está activo) y test_sysinfo ampliado; iguales con gcc y con dashc.
  - Quedan de la conclusión 3 los de pruebas: `window_find`, `input_event`, `input_move_screen`, `input_menu`,
    `screen_pixel`, `gadget_find`, `cx_send`.
  - Tests de ./dash: 458 bien; batería de dashc bien; cobertura: compilan 208 de 312 (66 %) y en el A1200 135 de
    135 iguales.
- D7 (3.ª parte): `@link "x.o"` o `"libx.a"` (relativo al fichero) y `@extern("...") func f(a: Int, s: String) ->
  Int|Bool|String`. hunk.c lee los objetos Hunk de gcc y las bibliotecas ar (salta las tablas `/`, `//` y
  `__.SYMDEF`), con los símbolos comunes (variables sin `-fno-common`: un BSS para cada uno) y enlaza solo lo que se
  alcanza (un objeto sin `-ffunction-sections` entra entero). La llamada es la de C (pila de derecha a izquierda,
  d0); un `String` devuelto se copia a un temporal (`dl_str_tmpcopy`) y un `Bool` se normaliza a 0/1. Lo que no
  define nadie sale junto en un error. dashc/tests/externo.dash con `tests/c/externo.o` (su .c al lado; el .o va
  en git): igual que gcc en A1200 y A500, y 8.404 bytes frente a 9.488.
  - Enlazar la `libqjs.a` de Tachyon dice lo que falta: `_js_aserto` (del `@c` de Tachyon) y de libc/libm/libgcc
    `trunc acosh asinh atanh log2 abort __floatdidf __fixdfdi vsnprintf strrchr lrint realloc fprintf round fwrite
    fputc snprintf fmax fmin strchr gmtime mktime localtime gettimeofday __lshrdi3 __ashldi3`. Siguiente paso para
    QuickJS: una libc de compatibilidad para lo de `@link` (enlazada solo si hace falta) o que el módulo las lleve.
    Que el C llame a funciones Dash (las retrollamadas) está por ver: dashc guarda solo los registros que usa.
  - Batería de dashc bien (con externo.dash); cobertura: compilan 208 de 312 y en el A1200 135 de 135 iguales.
