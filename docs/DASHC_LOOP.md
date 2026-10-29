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
- D10 (descartada por el usuario el 2026-10-29: QuickJS, Hubbub y MintVID van enlazados en Tachyon con `@link`; se
  retoma si otro programa los quiere) QuickJS y Hubbub como librerías compartidas (en `LIBS:`, con nombre propio), pedido por el
  usuario (2026-10-28): con `@link`, cada programa lleva su copia (QuickJS, unos 800 KB); una `.library` se carga
  una vez y la usan todos los programas, y se actualiza sin recompilarlos. Hace falta: la librería con su tabla de
  funciones (libinit de bebbo), dentro lo de libc que necesitan (`realloc`, `snprintf`...), que la abran varios
  programas a la vez (estado por apertura) y que dashc llame a funciones de librería (registros y base) con
  `@extern("tachyonjs.library")`. Antes, Tachyon compilando con `@link` (D7).
  Nombres propios, no `quickjs`/`hubbub`: que otro port (NetSurf...) no pise la versión de Tachyon ni Tachyon la
  suya; el programa pide una versión mínima al abrirla.
  Decidido por el usuario (2026-10-28): van con Tachyon, que las necesita, y su instalador las pone en `LIBS:`
  (solo si la suya es más nueva). Hacerlas es trabajo de Tachyon; lo de Dash es que dashc llame a funciones de
  una `.library` (`@extern("x.library")`: por registros, con su base). Nombres decididos por el usuario
  (2026-10-28): `tachyonjs.library` y `tachyonhtml5.library` (no `dash...`).
- D9 Cierre: `./dash` llama a dashc (o dashc pasa a ser `dash`), documentación en dos idiomas, versión 2.0.
  Decidido por el usuario (2026-10-29):
  - D9a `dash` es dashc; un programa con C (`@native`, `@c`, `@header`) da un error claro que remite a `dash1`, el
    Dash de Python (1.x), que sigue tal cual para lo viejo.
  - D9b las descripciones de los 738 builtins en los dos idiomas, como el README (README.md en inglés,
    README.es.md en castellano): docs/BUILTINS.en.md en inglés y docs/BUILTINS.md en castellano.
  - D9c la documentación de la 2.0 (README, SINTAXIS, MANUAL, VERSIONES, AGENTS) en los dos idiomas.
  - D9d un PR de la rama dashc a main, sin fusionar ni publicar: el usuario decide cuándo.
- D11 Tachyon sin C (pedido por el usuario el 2026-10-29: "mueve sus C a builtins"), en la rama `dash2` de Tachyon
  (worktree `~/Projects/tachyon/.worktrees/dash2`, sale de `dev`; sin subir). Se prueba con su runner y dashc:
  `DASH=~/Projects/FreeMEMLang/.worktrees/dashc python3 tests/run.py <filtro>`. Por partes:
  - D11a red (`net_bg_*`), D11b gzip (`inflate_auto`), horas (`time_unix`), esperas de los tests (`time_delay`),
    D11c imágenes (`image_decode*`; nuevos `image_decode_start/ready/finish` y tamaños negativos como tope),
    D11d fuentes web (`font_from_ttf`; nuevo `font_ttf_icon`), D11e vídeo y YouTube (`@link` + `@extern` a `dwv_*`),
    D11f actualizar y descargas, D11g `src/dashweb.dash` (la precisión de la FPU la pone el runtime de `--fpu`).
  - D11h informe del sistema: `library_revision`, `resident_version` (MorphOS).
  - D11i herramientas (`tools/amiga/clicar.dash`, `latido.dash`) y el tutorial (`paso5_tarea`).
  - D11j QuickJS, DOM, lienzo y HTML5 (`js`, `jsdom`, `lienzo`, `html5`, `documento`: ~2.200 líneas de `@c` que
    llaman a funciones de Dash y leen sus structs `_Dash_Nodo` y listas): su C a ficheros .c de Tachyon dentro de
    sus librerías (`libqjs.a`, `libimg.a`) con `@extern`; para lo que el C lee de Dash, o retrollamadas a Dash, o una
    cabecera con la forma de los structs de dashc (`dashc --cabecera`). Diseño (2026-10-29): (1) hunk.c resuelve
    los símbolos que pide un objeto de `@link` y nadie define con las funciones de Dash del mismo nombre
    (`_jsdom_por_id`: ya siguen el convenio de C); (2) `dashc --cabecera prog.dash` escribe un .h con los structs de
    Dash tal como los coloca dashc (cabecera de objeto y campos) para el C del módulo; (3) `dash.h`, una API del
    runtime con nombres que se pueden enlazar (`dl_str_dup`, `dl_array_length`, `dl_array_get`, `dl_retain`,
    `dl_release`...: las de ./dash son `static`). El C de Tachyon pasa de `@c` a ficheros .c en sus librerías
    (tools/build_qjs.sh) casi sin cambios: los nombres de esa API.
- D12 Depurador con dashc (pendiente, sin diseñar; anotado el 2026-10-29). Hoy dashc no tiene `--debug`: solo da el
  fichero y la línea de un fallo en tiempo de ejecución, y el depurador de la extensión de VS Code usa `dash1`.
  Aviso de David Martínez por Telegram (2026-10-29): en Emu68 la depuración línea a línea de SAS/C y otras
  herramientas no funciona, porque a la emulación le falta algo por implementar; el compilador de E (AmigaE) lo
  hace de otra forma y en Emu68 sí depura línea a línea. El motivo: Emu68 no implementa el modo traza de la CPU
  (el bit T del SR), y esos depuradores paso a paso dependen de él.
  - Cómo lo hace EDBG, según Darren Coles, que mantiene el compilador de E (E-VO): compilado en modo depuración,
    E pone un `NOP` antes de cada línea de código fuente. Al arrancar, EDBG busca esos `NOP` con los hunks de
    depuración (línea → dirección) y los cambia todos por `TRAP`. Cada `TRAP` entra en el manejador de EDBG, que
    mira los puntos de parada, el paso a paso, etc. No usa la traza de la CPU.
  - Idea para D12: el mismo enfoque. `dashc --debug` pondría un `NOP` (o un `TRAP` fijo) al principio de cada
    línea de Dash y un `HUNK_DEBUG` con la tabla línea → dirección (dashc ya lleva fichero y línea en `cur_file` y
    `cur_line`). El depurador sería un programa del Amiga, o el manejador de `TRAP` del runtime, que ya tiene
    `tc_TrapCode` propio. Así funcionaría igual en un 68000 real, en FS-UAE y en Emu68.

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
- D7 (4.ª parte): QuickJS enlaza y corre con dashc. `runtime/rt_compat.c` (en la librería, una sección por
  función: solo entra lo que se llama) pone lo de libc y libm que pide el C de `@link`: `vsnprintf`/`snprintf`
  (enteros de 32 y 64 bits, anchura y precisión con `*`, `%s %c %p %x`; la coma flotante sale como `?`),
  `realloc`, `calloc`, `abort`, `strchr`, `strrchr`, stdio a `Output()` con su búfer (`fprintf`, `printf`,
  `fwrite`, `fputc`, `fputs`, `puts`, `__sF`), `gettimeofday`, `gmtime`, `localtime` (sin zona), `mktime`, y
  `trunc round lrint fmax fmin log2 asinh acosh atanh` sobre el fdlibm del runtime. De libgcc, los desplazamientos,
  comparaciones y conversiones de 64 bits y `ctz`, `popcount`, `bswap`, `ffs`. Los programas de siempre no cambian
  de tamaño.
  - Prueba (fuera del repo): QuickJS de Tachyon compilado para 68000 sin FPU (la `libqjs.a` de Tachyon es de
    68020+68881), un `motor.c` de 50 líneas y un programa Dash con `@link`/`@extern`: en el A1200, `1 + 2 * 3`,
    `sort`/`join`, `0.1 + 0.2`, `Math.sqrt/log2/round/trunc`, `JSON.stringify`, `Date.toISOString`, recursión,
    expresiones regulares y una excepción, todo bien. 876 KB (por eso D10).
  - También los nombres de libm (`sin`, `log`, `pow`, `sqrt`...: la `math.h` de libnix cambia `log2` por `log`), como
    envoltorios del fdlibm del runtime. dashc/tests/externo.dash compara `snprintf`, `realloc`, `gmtime`, `round`,
    `trunc`, `lrint` y `log2` con los de libnix: iguales en A1200 y A500 (el `log2(64)` de libnix da 5,999...: el
    test redondea). Batería y cobertura bien (208 de 312; 135 de 135); los tamaños de siempre, iguales.
  - A Tachyon, para su `js.dash`, le falta lo de su `@c` (`_js_aserto`, las clases `__dashweb_*`...), que llama a
    funciones Dash y a la API interna del runtime: eso, a su módulo de C (y las retrollamadas a Dash, por ver).
- D7 (5.ª parte): retrollamadas de C a Dash. Una función de Dash pasada como `Func` a un `@extern` sigue el convenio
  de C (argumentos en la pila, `link a5`, guarda los d2-d7 que usa), pero crear un struct dejaba a2 cambiado: ahora
  lo guarda y lo restaura (2 instrucciones por struct creado). dashc/tests/externo.dash: `ext_aplicar(doble, 21)` y
  `ext_sumar_con(guardar)`, que llama 6 veces a una función de Dash que crea structs con textos mientras gcc tiene
  un puntero en a2 (antes daba basura). Iguales que gcc en A1200 y A500. Un texto que devuelve la función de Dash
  es un temporal: el C lo copia si lo guarda.
  - Batería bien (42 de 42) y cobertura igual (208 de 312; 135 de 135).
- D7 (6.ª parte): `task_start(f, n)` y `task_start_with` con una función de Dash (en ./dash, solo `@native`). Las
  funciones de Dash ya siguen el convenio de C, así que el runtime de tareas de ./dash las llama tal cual; lo que
  falta es seguridad: corre a la vez que el programa y la memoria del runtime (textos, listas, structs, Double y sus
  temporales) es de uno solo. dashc lo comprueba al compilar (`task_impure`, también en las funciones a las que
  llama): solo Int, Bool, Float, globales de esos, builtins que no dan textos, listas ni Double, `@extern` y textos
  literales para `Print` o como argumento; si no, "task_start: f corre a la vez que el programa y no puede crear
  structs" con su línea. dashc/tests/tareas.dash: primos en una tarea mientras el programa hace textos y listas,
  con un global Int compartido: igual que gcc en A1200 y A500.
  - Para Tachyon (decodificar imágenes, red de fondo) harán falta búferes compartidos: los `buffer_*` son
    builtins de enteros y valen ya dentro de una tarea.
  - Batería bien (44 de 44) y cobertura igual (208 de 312; 135 de 135).
- D8 (1.ª parte): el dashc del Amiga, más rápido y más pequeño.
  - Medido dentro del emulador con `dashc --tiempos` (lo que lleva cada fase): compilar un "hola" costaba 5,8 s
    en el A1200 y 19,5 s en el A500, casi todo en preparar el runtime en cada compilación (leer sus 2.200 hunks,
    2,4 s; trocear sus textos, 2,2 s; una búsqueda de `_dash_win` por todos los símbolos en cada limpieza, 0,5 s).
  - Ahora el runtime va preparado (`dashc --preparar`, al construir dashc; formato "DRT1" en hunk.c): leído, con
    los textos troceados y los nombres atados. Al compilar se carga sin copiar nada, las reubicaciones de un hunk
    se leen solo si se mira, los datos se copian solo los de los hunks que van, y lo de `_dash_win`/`_dash_rp` se
    busca una vez. Un "hola": 0,66 s en el A1200 y 2,2 s en el A500 (aritmetica: 0,87 s y 3,0 s).
  - Comprimir los dos runtimes con zlib dejaba el dashc del Amiga en 668 KB pero añadía 4,5 s (A1200) y 12,7 s
    (A500) por descomprimir: solo va comprimido el de `--memcheck` (se descomprime solo entonces). El dashc del
    Amiga: 1,0 MB (era 1,4 MB con rt_compat).
  - Los ejecutables, idénticos a los de antes (todos los de dashc/tests, `--memcheck`, `externo` y QuickJS,
    comparados con el runtime sin preparar, `--runtime runtime/dashrt.o`); el dashc del Amiga hace los mismos que
    el del PC (dobles, structs, aritmetica, gadgets).
  - Batería bien (44 de 44) y cobertura igual (208 de 312; 135 de 135).
- D7 (7.ª parte): `inflate_auto(src, n, dest, max)` (705 builtins): gzip (su cabecera, también con FEXTRA, FNAME,
  FCOMMENT y FHCRC; el final no se mira), zlib (con su adler32) o deflate crudo, por sus primeros bytes: lo que
  hacía el `_http_inflar` de Tachyon con stb_image. En `runtime/zlib/dash_inflate.c`. tests/test_inflate_auto.dash
  (las cabeceras hechas a mano en Dash), igual con gcc y con dashc.
  - Encontrado al escribirlo, un fallo de ./dash: `CONSTANTE.length` de una constante de texto daba el largo de
    una lista (basura: leía los bytes del texto). Ahora `strlen`. dashc ya lo hacía bien.
    tests/test_const_string_length.dash.
  - Tests de ./dash: 460 bien; batería de dashc bien; cobertura: compilan 210 de 314 y en el A1200 137 de 137.
- D7 (8.ª parte): `image_decode(fichero, maxw, maxh)` y sus partes (`image_decoded_width/height/alpha/pixels/free`,
  `image_from_decoded`; 712 builtins): JPEG con TJpgDec (reducido al decodificar: 1/2, 1/4, 1/8) y PNG, GIF, BMP y
  JPEG progresivo con stb_image (reducidos después), sin datatypes. En `runtime/imgdec` (biblioteca aparte de
  compiler/clibs.py, como zlib; LEEME con el origen y las licencias). Toda la memoria es de exec: vale dentro de
  `task_start` (lo que hacía Tachyon para no parar la ventana).
  - El GIF se colgaba: `stbi__gif_load` pone en la pila unos 35 KB (su tabla LZW) y un programa de Dash tiene 16
    KB. Cambio en stb_image (el único): ese estado, de la memoria. `STBI_NO_THREAD_LOCALS`: su mensaje de error sin
    emutls de libgcc (dashc no la tiene).
  - tests/test_image_decode.dash: imágenes de 16 x 8 y 64 x 32 hechas con PIL en el PC, como listas de bytes, a
    RAM: y decodificadas; tamaños, alfa y los colores de tres esquinas. Igual con gcc y con dashc.
  - Pendientes de Tachyon: WebP (libwebp) y SVG (nanosvg: necesita `sqrtf`, `powf`... de float sin FPU).
  - Tests de ./dash: 461 bien (test_image_decode también en el A500); batería de dashc bien; cobertura: 211 de 315 y 138 de 138.
- D7 (9.ª parte): WebP en `image_decode`, con el decodificador de libwebp 1.4.0 (`runtime/imgdec/libwebp`: `src/dec`,
  `src/dsp`, `src/utils`, sin cambios; BSD) ya reducido al decodificar. Su malloc, calloc y free, con
  `-Dmalloc=dash_imgdec_malloc...` a los de exec de `dash_imgdec.c` (vale en una tarea); `-DNDEBUG` (sus `assert`
  pedían `__assert_func` de libnix). tests/test_image_decode.dash con un WebP con pérdida (a su tamaño y a 16x8) y
  uno sin pérdida con alfa: igual con gcc y con dashc.
  - Los programas no cambian de tamaño, pero el dashc del Amiga vuelve a 1,4 MB (las bibliotecas de imágenes van
    en el runtime). Siguiente para D8: comprimir cada hunk del runtime preparado por separado y descomprimir solo
    los que van (la carga ya es perezosa).
  - Tests de ./dash: 461 bien (test_image_decode también en el A500); batería bien; cobertura 211 de 315 y 138 de 138.
- D8 (2.ª parte): el runtime normal dentro de dashc va en "DRT2" (runtime/rt_blob.py): los datos de cada hunk
  comprimidos aparte (deflate crudo, si así ocupan menos) y hunk.c los descomprime solo para los hunks que van
  (`own_data`). Los nombres de sección ya no van si un símbolo nombra el hunk, y los nombres repetidos, una vez.
  Runtime preparado: de 792 KB a 600 KB; el dashc del Amiga, de 1,4 MB (con las bibliotecas de imágenes) a 1,2 MB.
  Descomprimir cuesta unos 80 ms en el A1200 y 300 ms en el A500: un "hola", 0,89 s y 2,8 s (la carga ha crecido
  también por los 3.200 hunks que traen ahora las imágenes; antes, 2.200). Los ejecutables, idénticos (todos los
  de dashc/tests, `--memcheck`, QuickJS y test_image_decode, con el runtime sin preparar).
  - Lo que queda grande son las tablas (3.200 hunks a 28 bytes, 10.500 reubicaciones a 8): se podrían guardar en
    menos bytes. Y comprimir juntos los datos de varios hunks daría más (todo junto, 250 KB en vez de 360 KB).
  - Batería bien; cobertura 211 de 315 y 138 de 138.
- D7 (10.ª parte): SVG en `image_decode` con nanosvg (la copia de Tachyon, con su cambio de `pathLength`; zlib),
  dibujado en RGBA a la escala que cubre maxw x maxh (o a su tamaño). Sus cuentas van a `dash_imgdec_mathf.c`
  (sobre el fdlibm de Dash: las de libnix van a la ROM, que sin FPU da una excepción de línea F) y su memoria a exec
  (`-Drealloc` también). ./dash enlaza con `image_decode` el fdlibm (`compiler/clibs.py`: un marcador puede ser
  varios) y el float por software (`compiler/softfloat.py`); el runtime de dashc lleva `strtol`, `strtoll`,
  `strtoul`, `qsort` (Shell) y un `sscanf` con lo que usa nanosvg (`%d %u %x` con anchura y texto literal).
  tests/test_image_decode.dash con un SVG (`#ff0000`, `#00f`, `rgb(0, 255, 0)`) a su tamaño y a 32x16: igual con
  gcc y con dashc.
  - Tests de ./dash: 461 bien (test_image_decode también en el A500); batería bien; cobertura 211 de 315 y 138 de 138.
- D7 (11.ª parte): `font_from_ttf(fichero, tam, ancho)`, `font_ttf_free` y `font_ttf_forget` (715 builtins): una
  fuente TrueType (TTF, OTF con contornos TrueType, WOFF o WOFF2 de ellas) hecha TextFont de 1 bit para `font_use`,
  sin diskfont ni bullet. En `runtime/fontweb` (biblioteca aparte): stb_truetype 1.26, el descompresor de Brotli
  1.1.0 y `dash_fontweb.c`, el C de Tachyon (WOFF 1 con el zlib de Dash, WOFF 2 con Brotli y glyf/loca/hmtx
  rehechas) con memoria de exec y cuentas en el fdlibm de Dash. ./dash enlaza con ella zlib, fdlibm y el float por
  software (un marcador de clibs puede ser varios; las bibliotecas van en orden de enlace: fontweb antes de zlib).
  - Parecía colgarse con la segunda fuente: era lentitud. Cada fuente dibujaba los 224 caracteres de Latin-1 con
    coma flotante por software (23 s en el A1200 emulado, con gcc y con dashc), y en la fuente de prueba 220 eran
    el mismo .notdef. Ahora un glifo que ya está no se dibuja otra vez (comparten su trozo del plano): 0,66 s.
    Una fuente de verdad (~190 glifos distintos) seguirá siendo lenta sin FPU.
  - tests/test_font_ttf.dash: una fuente diminuta hecha con fontTools en el PC (venv en el scratchpad), en TTF,
    WOFF y WOFF2 (glyf transformada): las tres dan las mismas medidas, también al 50 % de ancho; igual con gcc y
    con dashc.
  - Tests de ./dash: 462 bien (test_font_ttf también en el A500); batería bien; cobertura 212 de 316 y 139 de 139.
- D8 (3.ª parte): con las bibliotecas de imágenes y fuentes, el dashc del Amiga subió a 1,5 MB, la mitad por la
  copia del runtime de `--memcheck`. En el Amiga va aparte: `build/dashc_mc.drt` (770 KB, en DRT2), que se copia
  junto a dashc y se lee de `PROGDIR:` solo con `--memcheck` (sin él, un error que lo dice). El dashc del Amiga:
  1,0 MB. El del PC lo sigue llevando dentro. Probado en el A1200: `--memcheck` con structs.dash da el mismo
  ejecutable que el PC.
- D7 (12.ª parte): decidido por el usuario (2026-10-29): el vídeo de Tachyon (MintVID, 7,2 MB de fuente con un
  decodificador H.264) no va como builtins: Tachyon lo llama con `@link` y `@extern` a su API `dwv_*` (su
  `video.dash` ya son envoltorios de una línea). Para que su `libvideo.a` enlace con dashc, `rt_compat.c` lleva
  ahora ficheros de stdio de verdad (`fopen`, `fread`, `fseek`, `ftell`, `fclose`, `setvbuf`; un FILE propio con el
  de libnix delante, y `fwrite`, `fputc`, `fputs`, `fprintf` escriben al fichero que sea), `getenv`, `strcspn`,
  `clock` y `__assert_func`. Le quedan 4 nombres que no son de libc (`gFdct32HalfSparse16Precondition*`, comunes
  que hunk.c ya resuelve, y `mr_yuv_dither_q6_*`, de otra parte de Tachyon). externo y QuickJS, como antes.
- D7 (13.ª parte): la red de fondo de Tachyon como builtins `net_bg_*` (727 builtins): `net_bg_open`/`_tls` piden
  una conexión que una tarea propia (la de `task_start`, 64 KB de pila) busca, conecta, negocia, envía y recibe
  mientras el programa está ocupado (hasta 48); `net_bg_state`, `_stage`, `_error`, `_send`, `_send_buffer`,
  `_recv` (sin esperar), `_pending`, `_close`, `_idle` y `_stop`. El C de Tachyon (`lib/red.dash`) en
  `NETBG_RUNTIME`; la TLS en `NETBG_TLS_RUNTIME`, por punteros que llena `net_bg_open_tls`: un programa sin TLS no
  lleva AmiSSL. Las dependencias entre runtimes van donde las demás (`uses_tls` → `uses_net`...): al principio las
  puse al montar el programa, tarde, y faltaba el runtime de texto. Al acabar el programa, la tarea acaba antes de
  que se espere a las tareas.
  - tests/test_net_bg.dash (dos conexiones al eco a la vez mientras el programa sigue, y un puerto cerrado) y
    test_net_bg_tls.dash (TLS con el certificado de prueba, y un nombre que no existe): iguales con gcc y con
    dashc. La cobertura ya ejecuta también los de `# emu-net-tls:` (con `$DASH_EMU_SYS_SSL`).
  - Ojo al escribir tests: `time_delay_ms` de menos de 20 ms (un tic) no espera nada; el bucle de espera del test
    acababa antes de que la tarea hiciera nada.
  - Tests de ./dash: 464 bien; batería bien; cobertura (ya con TLS): 214 de 318 y 144 de 144.
- D7 (14.ª parte), pedido por el usuario: el `malloc` y el `free` del runtime de dashc (los del C de `@link`) con
  un semáforo, como los de libnix: el sonido de MintVID pide memoria desde una tarea suya. Probado: una función
  `@extern` de C en `task_start` haciendo 3.000 malloc/free mientras el programa hace los mismos: las dos sumas
  iguales (externo.dash, también con gcc). Para eso, una función `@extern` puede ir como valor (`task_start(f, n)`
  o un puntero para otro C): la dirección de su símbolo.
  - Para Hubbub (el HTML5 de Tachyon, que va con `@link`): `bsearch`, `strncasecmp`, `strcasecmp` y la tabla
    `_ctype_` de libnix (sus macros `isalpha`... la leen). Y las de float de libm (`sqrtf`, `floorf`, `sinf`,
    `powf`...). A la `libimg.a` de Tachyon solo le quedan `cexpf` y `emutls` de sus copias de nanosvg y stb, que con
    dashc cambiará por `image_decode` y `font_from_ttf`.
  - Encontrado al probar: dashc dejaba guardar un número en una variable que guarda un texto (lo convertía); ./dash
    da error. Ahora dashc también: "no se puede guardar un Int en t, que guarda un String".
  - Los programas llevan 8 bytes más: dos entradas en la tabla de limpiezas (fuentes y red de fondo).
  - Batería bien; cobertura 214 de 318 y 144 de 144.
- D7 (15.ª parte): los builtins de pruebas de la conclusión 3 (738 builtins), lo que hacían con `@native` el
  `clicar` de Tachyon y las pruebas de Trasfondo: `window_find` (una ventana por el principio de su título, en
  cualquier pantalla), `window_found_activate`, `window_found_box`, `gadget_index` (por su texto), `gadget_x`,
  `gadget_y`, `gadget_selected` (por su sitio: los botones de GadTools no guardan su texto en el gadget, se
  encuentran contando desde uno con texto, como hacía Trasfondo), `input_menu` (un menú elegido con el ratón),
  `input_move_screen` (paso a paso, con botones: los menús de MUI), `screen_pixel` y `cx_send` (BrokerCommand, el
  privado de commodities, como Exchange). En SIMINPUT_RUNTIME. tests/test_window_find.dash: el programa se busca a
  sí mismo como si fuera otro, clica sus gadgets, lee un píxel, manda una orden a una commodity que no está y elige
  "Salir" con el ratón; igual con gcc y con dashc.
  - De la conclusión 3 ya no queda ninguno: los `@native` de Tachyon, Trasfondo y Lorraine que no son C de
    terceros tienen su builtin.
  - Arreglado: SIMINPUT_RUNTIME sin `proto/graphics.h` (el `ReadPixel` de `screen_pixel`) rompía los programas que
    usan ese runtime sin gráficos (test_sysinfo, test_mui_toolbar).
  - docs/BUILTINS.md: los builtins nuevos de Dash 2.0 tenían secciones que no eran suyas (`time_unix` en "Tareas (C
    en otro proceso)", `image_decode` en "Imágenes (datatypes)"...). Ahora en grupos propios de amiga_builtins.py
    (`_move`): "Sistema y programa", "Imágenes decodificadas por el programa", "Fuentes TrueType, WOFF y WOFF2",
    "Red en una tarea aparte" y "Ventanas de otros programas (pruebas)"; y "Tareas, reloj, traducciones y
    escritorio" en vez de "Tareas (C en otro proceso)". Pendiente para D9: las descripciones en castellano (hoy van
    en inglés en los dos ficheros, como todas) y ejemplos.
  - Tests de ./dash: 465 bien; batería bien; cobertura 215 de 319 y 145 de 145.
- D9a: `./dash` es dashc. El script de Python pasa a `./dash1` (Dash 1.x, sin cambios); el nuevo `./dash` llama a
  `dashc/dashc` (`make -C dashc`) y, con C en el programa (`@native`, `@c`, `@header`) o con una opción que dashc
  no tiene (`--fpu`, `--cpu`, `--debug`, `--small`, `--multifile`...), da un error que dice la orden de `dash1`.
  dashc tiene ya `--stack N` (como `@stack`) y `--version` ("Dash 2.0.0 (dashc)"). Las herramientas de pruebas de la
  1.x (`emu_run`, `bench`, `fuzz_refcount`, `emu_preview`, `compile_all.sh`, los tests unitarios y la batería de
  dashc, que compara con gcc) llaman a `dash1`. La extensión de VS Code usa `dash1` donde lo hay para sus tareas, el
  depurador y la vista previa de MUI (necesitan `--fpu`, `--debug`, `DASH_TEST_AUTOCLOSE`, `DASH_PRINT_FLUSH`);
  CHANGELOG, "Unreleased". tests/unit/test_dash2_cli.py.
  - Pendientes que salen de aquí: dashc no genera código de FPU (Tachyon se compila con `--fpu`: con dashc, sus
    Double y Float por software) ni tiene `DASH_TEST_AUTOCLOSE`/`DASH_PRINT_FLUSH` (para que la extensión use
    dashc). Los tests de la extensión (`npm test`) no arrancan en este equipo: falta `vscode-textmate` (npm install).
- D9b: las descripciones de los 738 builtins en castellano, en `compiler/builtins_es.py` (`DESC_ES`), que
  tools/gen_builtins_doc.py pone en docs/BUILTINS.md (BUILTINS.en.md sigue con las de amiga_builtins.py, en inglés).
  Si un builtin no tiene la suya, el generador falla y con él la comprobación de la documentación (docs/builtins):
  quien añada un builtin (también la sesión de Tachyon en su rama) tiene que añadir su línea ahí. Corregida de paso la
  de `task_start`, que decía "solo C".
- D9e: `--fpu` en dashc, para compilar Tachyon como antes (`./dash --fpu`, tools/paquete.sh). Un tercer runtime,
  `runtime/dashrt_fpu.o` (runtime/build_lib.py): el C para 68020 + 68881, como `./dash --fpu`, sin el float por
  software y con `runtime/rt_fpu.s`, las siete funciones de Float que llama el código de dashc (`__addsf3`,
  `__subsf3`, `__mulsf3`, `__divsf3`, `__floatsisf`, `__fixsfsi`, `__cmpsf2`) con la FPU, devolviendo en d0
  como las de fp-bit (`__fixsfsi` cambia el redondeo del FPCR en vez de usar `fintrz`, que el 68040 no tiene).
  El código de dashc sigue siendo de 68000: el runtime pasa los Double en cajas y los Float como LONG, y `@extern`
  solo admite Int, Bool y String, así que lo que el C con FPU devuelve en fp0 no llega a dashc. El dashc del PC lo
  lleva dentro (DRT2, como el normal); el del Amiga, aparte en `dashc_fpu.drt` junto a él (como `dashc_mc.drt`).
  Con `--memcheck`, el runtime de `--memcheck` (Float por software). `--cpu X` se acepta y no cambia nada (el
  código vale para todas). `./dash` ya no remite a dash1 por `--fpu` ni `--cpu`.
  - Arreglado: el runtime se compilaba sin las opciones de `./dash` (compiler/cflags.py), con todas las pasadas de
    `-fbbb`, también las que dan código erróneo: con FPU salía `2.0000000039833282e300` por `2.0e300`. Ahora
    `opt_flags()`, también en el runtime normal y el de `--memcheck`.
  - FS-UAE pasa inf a 2.0 (y nan a 1.0) al guardar un registro de la FPU en 80 bits (`fmove.x`), lo que hace el C
    al guardar un valor antes de llamar a otra función: `str_from_double(1/0, 2)` da "2.0" (en test_double_texto_fpu,
    la línea "raros"). Comprobado con un `@native` de dash1: es el emulador. Su modo exacto (`uae_fpu_softfloat`)
    arregla eso pero rompe más (raíces, conversiones y denormales salen mal, también con `./dash1 --fpu`), así que
    cobertura.py usa el normal, un 68040 como el runner, y esa línea queda como diferencia conocida del emulador.
  - tests/cobertura.py compila los `# fpu` con `--fpu` y los ejecuta en un 68040: 4 de 5 iguales, el quinto por lo
    de inf (test_fpu_68040 lleva `@native`). El dashc del Amiga con `--fpu` da el mismo ejecutable, byte a byte,
    que el del PC. Batería de dashc (run.py) bien con el runtime rehecho; cobertura: 142 de 145 con el modo exacto
    de FS-UAE (los tres fallos, del emulador, comprobados con dash1).
  - Lo que queda para Tachyon: su código aún tiene unos 150 bloques de C (`@native`, `@c`, `@header` en lib/red,
    js, html5, video, imagen_dec, fuente_web...). Hay que pasarlos a los builtins de D7 y a `@link`/`@extern`: es
    trabajo de Tachyon, en su repositorio. Hasta entonces, Tachyon se compila con `./dash1 --fpu`.
- D11 (1.ª parte, 2026-10-29): Tachyon sin C, rama `dash2` de Tachyon (7 commits, sin subir). Pasados a builtins o
  a Dash: la red de fondo (`net_bg_*`), el gzip de HTTP (`inflate_auto`, el destino crece mientras no quepa), las
  horas de cookies e historial (`time_unix`), las esperas de los tests (`time_delay`), las imágenes (`image_decode*`),
  las fuentes web (`font_from_ttf`), el vídeo y YouTube (`@link` + `@extern` a `dwv_*` de `libvideo.a`), actualizar
  (catálogo IFF, idioma, instalar el .gz con su CRC, relanzar), descargas (`wb_open`, `dialog_file_at`), el informe
  del sistema, `src/dashweb.dash` (teclas, salida, MUI, versión con `@version`, fecha de compilación), `clicar` y el
  paso 5 del tutorial (una función de Dash en `task_start`, también en TUTORIAL.md y .en.md). `latido` lee exec por
  dentro: sigue con dash1. Con dashc pasan test_red, los 5 de HTTP, marcadores, imagen_dec, fuente_web, video,
  video_bajando, youtube y actualizar.
  - Builtins nuevos (y en ./dash): `image_decode_start/ready/finish` (decodificar en un proceso aparte: una tarea de
    Dash no puede recibir el nombre como texto), tamaños negativos en `image_decode` como tope (un SVG a su tamaño;
    Tachyon pasa así 1280x1024 o más, "no se sabe a qué tamaño se ve"), `font_ttf_icon` (la "A" de la fuente es un
    icono de la zona privada de Unicode), `library_revision` y `resident_version` (MorphOS). 745 builtins.
  - `--fpu` pone la FPU en precisión extendida al arrancar (api.c): un sistema del usuario la dejaba en simple
    (Tachyon lo hacía con C, tarea 49).
  - Arreglado en dashc: una función de otro fichero copiada en línea dentro de una condición dejaba como fichero
    actual el suyo, y lo que seguía en la instrucción ya no veía las globales del programa ("la variable lienzo no
    existe" en Trasfondo). gen_inline guarda y repone el fichero, la línea y el nombre. dashc/tests/importa.dash lo
    prueba. Con esto Trasfondo (panel y preferencias) compila entero con dashc y se ve en el Workbench emulado.
  - dashc/bench/bench_run.py compara con `dash1` (desde D9a, `./dash` es dashc).
  - Queda D11j (QuickJS, DOM, lienzo, HTML5) con el diseño de arriba, y `editor/tmgrammar` se regenera al añadir
    builtins (tools/gen_tmgrammar.py; el runner lo exige).
  - Tests de ./dash: 470, bien salvo la gramática (regenerada); batería de dashc bien; cobertura 144 de 145 (el de
    inf con FPU, del emulador).
- D11j (2.ª parte, 2026-10-29): el C de QuickJS, DOM, lienzo y HTML5 de Tachyon como módulo de C.
  - En Dash: `@export func f(...)` (también en ./dash: la función no es `static`): dashc la genera aunque nadie la
    llame desde Dash y hunk.c le da su símbolo de C (`_f`, sin el sufijo `__mN` de una privada), para el C de
    `@link`. `@extern` admite structs (su puntero, prestado; uno devuelto se sostiene al guardarlo, como el de una
    función). `dashc --cabecera x.h prog.dash` (también de un módulo sin Main): los structs como los coloca dashc
    (el puntero, al primer campo; 4 bytes por campo), las constantes enteras, la API del runtime (`dl_str_dup`,
    `dl_str_temp`, `dl_str_forget`, `dl_retain`, `dl_release`, `dl_arr_length`, `dl_arr_get`, `dl_dict_*`, los
    `db_*` de los builtins), los nombres del C de ./dash como macros (`_dash_str_dup`, `DashArray_get`...) y los
    prototipos de las `@export`. Tests: externo.dash (C que llama a Dash por su nombre, structs de ida y vuelta) y
    tests/unit/test_dashc_cabecera.py.
  - rt_compat.c: `exit`, `strdup`, `strtod` (con el s2d de Ryu: exacto; el de libnix falla en la última cifra) y
    `cexp`/`cexpf`.
  - Saltos de más de 32 KB (Main de un test de Tachyon): `grow_branches` alarga los que no llegan (.s a .w; .w a
    `jmp` absoluto reubicado, Bcc con la condición contraria por encima, dbra por encima de un bra.s). Test lejos.dash
    (de paso: ahí el ejecutable de dashc ocupa 3 veces el de gcc, por el % de una constante grande en línea: D8).
  - Un cuarto runtime, `--fpu --memcheck` (dashrt_fpu_mc.o): el de `--memcheck` lleva el float por software y,
    mezclado con el C de Tachyon compilado para FPU, rompía los números. 99 tests de Tachyon usan `# memcheck`.
  - Arreglado: un `return` dentro de un `for` de una función copiada en una condición ("if not _tiene_clase(n, c)",
    dentro de otro for) saltaba fuera sin quitar de la pila las marcas del bucle: lo que seguía leía mal sus
    variables (nil). Encontrado por bisección con `DASHC_NO_COPIAR=f,g` (y `DASHC_SIN_COPIAR`), nuevos para eso.
    Test bucle_copiado.dash.
  - En Tachyon (rama dash2): tools/a_modulo.py sacó el `@c`, `@header` y `@native` de js, lienzo, jsdom, html5 y
    documento a src_c/tachyon.c (2.800 líneas, un solo fichero como en ./dash: jsdom usa lo static de js), con
    `@extern` en los .dash y `@export` en las 43 funciones de Dash que llama ese C; tools/build_pegamento.sh lo
    compila (con build/dash_tipos.h de `dashc --cabecera`) a libpegamento.a, que tests/run.py rehace si hace falta.
    Ya no queda C en lib/ ni src/ de Tachyon (solo tools/amiga/latido.dash, con dash1). Tachyon entero compila con
    dashc --fpu en 1 s en el PC (4,3 MB).
- D11j (3.ª parte, 2026-10-29): la tanda de Tachyon con dashc.
  - Arreglado en dashc:
    - `_ctype_` de rt_compat.c era un array, y libnix lo declara `const char *_ctype_`: las macros
      `isupper`/`tolower` del C de `@link` leían basura (Hubbub no reconocía "UTF-8"). Ahora es un puntero, y hay
      también `__locale_ctype_ptr` para las cabeceras de newlib.
    - Un texto devuelto por `@extern` reusaba el largo guardado de una dirección reciclada: se copia con
      `dl_str_tmpcopy_c`, que primero olvida ese largo.
    - El `return` de una copia en una condición, dentro de su bucle, quitaba las marcas dos veces cuando no saltaba:
      Tachyon se colgaba al calcular estilos (`_cumple_atributo`).
    - `fmax`, `fmin` y la prueba de NaN miran los bits: la FPU de FS-UAE da `inf != inf`, y
      `Math.max(1, Infinity)` daba 1 (test_js_infinito).
    - Un `while` contado (`i < total`, `i + 1` al final) se genera en la primera pasada con un contador, y `total` ya
      no se lee dentro: su registro se lo llevaba otra variable. Si en la segunda pasada al contador no le toca
      registro, el bucle va con su condición, que lee `total` en cada vuelta: leía esa otra variable y no acababa
      (test_animacion, en `animaciones_de`, por la copia de `_animacion_atajo`). Ahora, en la primera pasada, el
      final sigue vivo en todo el bucle. Test bucle_fin.dash.
    - Para buscar un fallo de copia: la bisección "sin copiar la mitad" engaña cuando hay más de una culpable. Va
      mejor al revés, copiando solo una mitad (las demás en `DASHC_NO_COPIAR`), y desensamblando con
      `m68k-amigaos-objdump -d`.
  - En Tachyon (rama dash2): `lienzo.dash` y `html5.dash` enlazan también libpegamento (sin js.dash no se
    enlazaba su C).
  - Primera tanda completa de Tachyon con dashc: 30 de 114. Casi todos los fallos eran esperas agotadas en grupo,
    porque test_animacion se colgaba y todos los tests del mismo arranque del emulador esperaban.
  - Con esos arreglos, la tanda completa de Tachyon con dashc: 114 de 114 (43 min).
  - El navegador (src/dashweb.dash, 4,5 MB) compilado con dashc --fpu, en el emulador con RTG y MUI 3.8
    (`tools/medir_visor.py --maquina rtg --sistema ~/.cache/dash-emu/sys32rtg38`): pinta prueba.html (499 ms) y
    lienzo.html, con su JavaScript y el canvas (921 ms), bien en las capturas. No medido aún contra el de dash1.
- Pendiente: D12, depurador (ver arriba); D9c, D9d; `DASH_TEST_AUTOCLOSE`/`DASH_PRINT_FLUSH` en dashc; D8 (tamaño).
