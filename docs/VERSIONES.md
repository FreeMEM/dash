# Versiones de Dash

*[English](VERSIONES.en.md) | Castellano*

Lo que lleva número es el compilador: el lenguaje, sus builtins, el runtime que va dentro de cada programa y las
herramientas (`tools/`). Un programa ya compilado no depende de la versión: es un ejecutable del Amiga y sigue
funcionando igual. La versión sirve para saber qué Dash hace falta para compilar un programa y qué ha cambiado.

`./dash --version` dice la que tienes. Cada versión es una etiqueta `vX.Y.Z` del repositorio con su página en
[Releases](https://github.com/FreeMEM/dash/releases) (las etiquetas `vscode-X.Y.Z` son de la extensión de VS Code,
que va aparte).

## Qué significa cada número

`X.Y.Z`, como en [Semantic Versioning](https://semver.org/lang/es/):

- **Z (arreglos):** fallos corregidos, programas más rápidos o más pequeños, documentación. Nada que haga falta
  cambiar en un programa.
- **Y (novedades):** builtins, sintaxis u opciones nuevas. Todo programa que compilaba sigue compilando y hace lo
  mismo; uno que use lo nuevo necesita esta versión o una posterior.
- **X (cambios que rompen):** algo deja de compilar o cambia lo que hace (un builtin que cambia de nombre o de
  argumentos, una palabra reservada nueva). Las notas de la versión dicen qué cambiar en cada caso.

No cuentan como cambio que rompe: arreglar un fallo aunque algún programa dependiera de él, mensajes de error
distintos, el C generado (puede cambiar en cualquier versión), lo marcado como experimental en la documentación ni
el código `@native` que use funciones internas del runtime (`_dash_*`).

## Cómo actualizar

Con el repositorio clonado: `git pull` (o `git checkout v1.2.0` para una versión concreta). Si no, el zip de la
versión en Releases. La extensión de VS Code avisa una vez al día si hay una versión más nueva que la del
compilador que usa (ajuste `dash.updates.check`; la consulta va a `api.github.com`).

## Notas de cada versión

### 2.6.4 (2026-11-08)

La documentación de los builtins, ampliada, y los arreglos que salieron al escribirla. Lo que ya compilaba sigue
igual.

- **Documentación:** las 961 funciones de [BUILTINS.md](BUILTINS.md) tienen ya su explicación: qué recibe, qué
  devuelve y con qué otras funciones va. Cada grupo empieza con una introducción y un ejemplo completo. Cada ejemplo
  es también un test que se prueba en el emulador. La tabla da los tipos de Dash (`Int`, `String`...).
- **Arreglo:** `joy_x` y `joy_y` no daban arriba ni abajo, y `joy_button` miraba el segundo botón en vez del
  disparo.
- **Arreglo:** `wait_key` volvía con 0 si llegaba otro mensaje antes de la tecla, y `wait_click` gastaba toda la
  CPU mientras esperaba.
- **Arreglo:** `gfx_flood` no rellenaba en una ventana de `window_create`.
- **Arreglo:** `tilemap_draw` dejaba vacías las celdas que seguían a la primera celda en espejo.
- **Arreglo:** en una pantalla propia, `color_pen` daba el color 1 para cualquier color; `rtg_write_pixel` y
  `rtg_fill_rect` en una pantalla de paleta pintaban casi todo en el último color. Ahora usan el más parecido de la
  paleta.
- **Arreglo:** `random_range` con `max` menor que `min` podía dividir por cero; ahora devuelve `min`.
- **Arreglo (`./dash --gcc`):** unas comillas dentro de una interpolación (`"#{f("x")}"`) daban error de sintaxis.
  Con `./dash` ya iba bien.
- **Arreglo:** un carácter (`t[i]`) donde va un texto, como en `str_find` o `str_replace`, iba como un número sin
  sentido. Ahora va como un texto de una letra, por los dos caminos.
- Probado en A1200 (3.1), A500 y A1200 con OS 3.2 emulados.

### 2.6.3 (2026-11-08)

Un arreglo de `./dash --gcc` y Forja 0.5.1 en el paquete. Lo que ya compilaba sigue igual.

- **Arreglo (`./dash --gcc`):** un programa que solo usaba `run_start` y `run_finish` no enlazaba (faltaban
  funciones de textos del runtime). Con `./dash` ya iba bien.
- El paquete del Amiga trae Forja 0.5.1: al depurar, el código ya no salta ni se repinta entero en cada paso (lo
  contó David Martínez).
- Probado en A1200 (3.1) emulado.

### 2.6.2 (2026-11-08)

Un arreglo del compilador y dos cosas de las herramientas. Lo que ya compilaba sigue igual.

- **Arreglo (`./dash`):** una interpolación con más de 16 números (`"#{a} #{b} ..."`) daba algunos mal: los
  últimos pisaban a los primeros. Salió en el editor de mapas de Forja. Con `./dash --gcc` ya iba bien.
- **Herramientas:** `tools/emu_run.py --cd CARPETA` monta esa carpeta como `Proyecto:` y ejecuta los programas en
  ella, así que encuentran sus ficheros con una ruta relativa.
- **Extensión de VS Code:** ajuste `dash.outputFolder` para elegir dónde van los ejecutables (idea de Ferrán
  García), y "Ejecutar en emulador" arranca el programa en la carpeta de su `.dash`. Llega con la próxima versión
  de la extensión.
- El paquete del Amiga trae Forja 0.5: "Ejecutables en:" en Preferencias (idea de Ferrán García).
- Probado en A1200 (3.1) y A500 emulados, por los dos caminos.

### 2.6.1 (2026-11-07)

Dos arreglos. Lo que ya compilaba sigue igual.

- **Arreglo (`desktop_canvas`):** dos programas con lienzo en el escritorio a la vez (Trasfondo y otro) colgaban la
  pantalla. Ahora pueden estar los dos, y cada uno deja el fondo como estaba al acabar. Los dos programas tienen que
  estar compilados con esta versión o una posterior.
- **Arreglo (sprites):** en una pantalla PAL o NTSC normal, `sprite_load` avisaba de que era una pantalla de
  tarjeta gráfica (RTG). Salió con el juego de ejemplo de la extensión de VS Code.
- Probado en A1200 (3.1 y 3.2), A500 y un CoffinOS emulados.

### 2.6.0 (2026-11-07)

Soltar iconos sobre las ventanas MUI y los builtins propios de DashOS. Lo que ya compilaba sigue igual.

- **Iconos soltados sobre una ventana MUI:** `mui_on_drop(objeto, id)` hace que `mui_wait_event()` devuelva `id`
  cuando se suelta un icono del Workbench sobre ese objeto (sobre una ventana, en cualquier sitio de ella). Las
  rutas, con `app_drop()`. Todas las ventanas MUI admiten ya iconos. Lo usa Tachyon para abrir una página guardada
  (idea de Ferrán García). Probado con MUI 3.8 y MUI 5.
- **DashOS:** 32 builtins propios (canales, llaves, temporizadores, memoria compartida, procesos y grupos). Solo
  compilan para DashOS; en el Amiga dan un error que lo dice.
- **`return` en `Main`:** sin valor, acaba el programa, ahora también con `./dash --gcc` (antes solo con `./dash`).
- Probado en A1200 (3.1 y 3.2) y A500 emulados, por los dos caminos.

### 2.5.0 (2026-11-07)

Arreglos del compilador que encontró Forja, la fuga de memoria de Trasfondo y un builtin para las imágenes de su
dock. Lo que ya compilaba sigue igual.

- **Imágenes a otro tamaño:** `image_from_decoded_size(d, ancho, alto)` hace una imagen de una decodificada (un PNG
  con transparencia, por ejemplo) a otro tamaño, con los bordes suaves.
- **Arreglo (fuga de memoria):** las funciones que solo leen sus textos recibían una copia que no se liberaba nunca
  cuando el texto era calculado. Ahora reciben el texto tal cual: `tooltype`, `date_text`, `file_copy`, `notify`,
  `screen_font_text_width`, `wifi_read`, `net_driver_read`, `rexx_reply`, `dir_change`, `input_text` y las que
  cargan o guardan ficheros. Era la memoria que perdía el fondo de Trasfondo con las horas (lo contó Oskisrp).
- **Arreglo (`./dash`):** en un programa muy largo, un salto que había que alargar podía pisar la instrucción
  siguiente.
- **Arreglo (`./dash --debug`):** una función que nadie llama ya no deja datos de depuración que apuntan a otra
  función. El depurador de Forja podía romper el programa al ir paso a paso.
- Probado en A1200 (3.1 y 3.2) y A500 emulados, por los dos caminos.

### 2.4.0 (2026-11-06)

Lo que piden el dock y los avisos de Trasfondo 2.2. Todo son novedades; lo que ya compilaba sigue igual.

- **Iconos a otro tamaño:** `icon_draw_size(icon, x, y, ancho, alto)` dibuja un icono de `icon_load` más pequeño o
  más grande, con los bordes suaves (en pantallas de color real; en las de paleta, a su tamaño y centrado).
- **Un puerto ARexx propio:** `rexx_port(nombre)` lo abre; las órdenes llegan con `rexx_get()` y se contestan con
  `rexx_reply(rc, resultado)`. Antes Dash solo podía mandar órdenes (`rexx_send`). Manual, sección 18.
- **Avisos:** `notify(titulo, texto)` deja un aviso en el escritorio, con el nombre del programa: a la barra de
  Trasfondo por ARexx (puerto `TRASFONDO`) o, si no está en marcha, en su lista, que enseña al arrancar.
- **Arreglo:** `run_program` y `run_command` en un programa arrancado desde el Workbench daban a la orden solo `C:`
  en el path, y así también a un Shell abierto con `C:WBRun` (el del dock de Trasfondo). Ahora le dan una copia
  del path del Workbench, el mismo que da un doble clic.
- **`wm_bar_gadgets()`:** a qué distancia del borde derecho empiezan los botones de la barra de título de la
  pantalla del Workbench (el de profundidad), preguntado a la pantalla.
- **Pegar en los campos de texto:** en los de GadTools y ReAction (`gt_string`, `gt_integer`, `textfield_create`,
  `integer_create`, `ra_add_string`), Amiga derecha, Amiga izquierda o Ctrl con V pegan el portapapeles donde está
  el cursor (su primera línea; en uno de números, solo las cifras), con C copian todo el texto y con X lo cortan.
  Antes, Amiga + V escribía una "v". Los de MUI ya pegan solos, con Amiga derecha o Ctrl + V.
- **Arreglo:** `window_move` justo después de `window_resize` (o al revés) devolvía a la ventana el tamaño (o el
  sitio) de antes, porque el sistema cambia la ventana más tarde. Ahora la segunda parte de lo pedido por la
  primera. Se notaba en la barra de Trasfondo en la de título: al encoger dejaba un hueco.
- Probado en A1200 (3.1 y 3.2) y A500 emulados, por los dos caminos.
- **Arreglo:** en MUI, el color de un texto (`mui_set_text_pen`, el `"color"` de un `.dashui`) usa un color de la
  paleta de la pantalla en todas las pantallas. En una de 32 bits con MUI 5 el texto se quedaba oscuro (Forja).

### 2.3.1 (2026-11-04)

Arreglos y el paquete del Amiga con dashgit. Nada que cambiar en los programas.

- **Red con `./dash`:** el compilador directo no cerraba `bsdsocket.library` al salir. Cada programa con red la
  dejaba abierta, y en un mismo Shell FS-UAE la negaba desde el noveno.
- **Paquete del Amiga:** trae dashgit, un git escrito en Dash (`DASH:dashgit`, GPLv2 como git, con
  `DASH:dashgit.LICENSE`; fuentes en https://github.com/FreeMEM/dashgit). **Está en alfa:** queda mucho por
  probar. Trae Forja 0.3, con su menú Git, y los `.dashui` de los ejemplos (sin `mui_navegador.dashui`,
  `mui_navegador_editor.dash` no compilaba en el Amiga).

### 2.3.0 (2026-11-04)

Dash para DashOS (AArch64), lo que piden el dock y los colores de Trasfondo 2.0 y lo que necesita dashgit, un git
escrito en Dash. Todo son novedades; lo que ya compilaba sigue igual.

- **DashOS:** `./dash --dashos` compila para DashOS, un ELF de AArch64 (little-endian; `--be` big-endian, `--pie`
  en cualquier dirección), por los dos caminos (`--dashos --gcc`, con clang). Float y Double con la FPU, textos en
  UTF-8. `@amiga struct` y `Ptr X`: vistas sobre memoria con la disposición del 68000, para las estructuras de
  AmigaOS, con `amiga_alloc` y `amiga_free`. En 68k, los ejecutables salen igual que antes. Manual, sección 25.
- **Ventanas de otros programas y del Workbench:** `wm_path` (la ruta del programa de una ventana),
  `file_real_path`, `screen_pixel_rgb` (el color de la pantalla, sea de quien sea), `screen_pen_rgb` (los colores
  del Workbench), `app_window` y `app_drop` (iconos soltados encima desde el Workbench), `icon_load` e
  `icon_draw` (iconos .info como los pinta el Workbench, sin datatypes) y `window_use` (volver a dibujar en la
  ventana declarada).
- **Para git:** `sha1` y `sha1_text`, y por partes `sha1_new`, `sha1_add`, `sha1_hex`, `sha1_bytes`...;
  `adler32`, `inflate_used` (dónde acaba un objeto comprimido), `program_exit(rc)` y `locale_gmt_offset`.
- **`./dash --gcc` con C de `@link`:** lo que se le pasa ya no se queda sin liberar (con `--memcheck`, Tachyon dejaba
  textos y objetos vivos) y sus librerías se enlazan en cualquier orden y solo con lo que se usa.
- **`dash` en el Amiga:** `version dash` dice su versión (antes, "%s (%d.%d.%d)"), y los programas con catálogo ya
  no llevan una marca de versión vacía delante de la suya.
- **Instalador:** si ya hay `DASH:`, ofrece poner al día esa instalación en su sitio; un fichero que estorba se
  aparta como `.antes`; en `S:User-Startup`, `DASH:` y el Path (también `DASH:Forja` y `DASH:Inferencia`: `forja` e
  `inferencia` desde cualquier Shell) solo si su cajón está, así que mover el cajón ya no para el arranque; la ruta
  de dash de Forja es `DASH:dash`. Trae Forja 0.2 e Inferencia 0.1, con su número de versión.
- **MorphOS:** los ejecutables de 68k de Dash funcionan en MorphOS (los probó Tolkien).
- Probado en A1200 (3.1 y 3.2) y A500 emulados, y el instalador en Coffin.

### 2.2.0 (2026-11-03)

Lo que piden el editor de sprites y de mapas de Forja y Fragua, la biblioteca de juegos. Todo son builtins nuevos;
lo que ya compilaba sigue igual, salvo las ventanas sin pantalla propia (abajo).

- **Mapas de tiles:** `tilemap_create`, `tilemap_load` y `tilemap_save` (IFF `FORM FMAP`, el del editor de mapas
  de Forja), celdas con espejo (`tilemap_get`, `tilemap_set`), capas (nombre, tipo, visibles; añadir, quitar,
  mover), `tilemap_resize` y objetos (`tilemap_object_add`, `_find`, `_x`, `_y`, `_kind`...). `tilemap_draw` y
  `tilemap_draw_masked` pintan un trozo del mapa con los fotogramas de un BOB, de una vez en la ventana.
- **Sprites y BOB:** `sprite_load_attached` (sprites acoplados de 15 colores), `sprite_rgb8`, `sprite_load_colors`,
  `bob_load_colors`, `bob_frame_width` (y `bob_load` lee el ancho de fotograma que guarda Forja), `bob_paste`
  (un fotograma con máscara sin guardar el fondo) y `bob_width`, `bob_height`, `bob_frames`.
- **Pantallas:** `screen_double_buffer` y `screen_flip` (doble búfer), `screen_clone_wb` (un clon público del
  Workbench), `screen_make_default`, `screen_visitors`, `mui_window_screen`, `dialog_screen_mode` y
  `screen_open_mode`. Una pantalla propia sin ventana ya se puede dibujar (`gfx_rgb8` colgaba).
- **Ventanas sin pantalla propia:** se abren en la pantalla pública por defecto en vez de en el Workbench siempre.
  Mientras nadie cambie la pública por defecto, es el Workbench, como antes.
- **Dibujo:** `gfx_pens_draw` (una imagen de lápices de una vez, con zoom; en planos, una sola copia del blitter),
  `color_pen_free`, y `key_down` (si una tecla está pulsada ahora, para juegos).
- **Para el Amiga:** el paquete trae Forja con sus editores de sprites y de mapas.

### 2.1.0 (2026-11-03)

El mismo C de `@link` vale por los dos caminos, el directo y por C con gcc. Es el paso para llevar programas como
Tachyon a PowerPC.

- **`@link` por C con gcc:** `./dash --gcc` da al C enlazado las mismas funciones del runtime que el directo
  (`dl_str_dup`, `dl_arr_get`, `dl_retain`...) y los builtins como `db_nombre` (`db_time_ms`...). Solo entran las
  que ese C llama.
- **`./dash --gcc --cabecera tipos.h programa.dash`:** escribe los structs del programa tal como los coloca el
  camino por C, sus constantes y los prototipos de las `@export`, con los mismos nombres que la del directo. Un
  `Bool` ocupa ahí 2 bytes, así que el C se compila aparte para cada camino, cada uno con su cabecera.
- **`./dash --gcc` desde cualquier carpeta:** antes había que estar en la del repositorio o poner `PYTHONPATH`.
- **Constructores:** solo se pueden omitir los últimos campos, y solo si tienen valor por defecto. Antes, con un
  campo con valor por defecto en medio del struct, los dos compiladores aceptaban una llamada a la que le faltaba
  un campo obligatorio de detrás. Ahora es un error, como dice el manual. Un programa que compilaba así tenía
  los campos desplazados.

### 2.0.2 (2026-11-03)

El compilador directo genera código más rápido. Ya va igual o más rápido que el camino por C (`--gcc`) en casi
todo. Nada que cambiar en los programas.

- **Textos:** unir textos (`s = a + b`, `s = "x" + n`, `"...#{x}..."`) va la mitad de tiempo que en la 2.0.1. Ya es
  un 9 % más rápido que por C en un A1200 y un 7 % en un A500.
- **Coma flotante:** la mitad de tiempo que en la 2.0.1; igual que por C. Los cálculos que no cambian dentro de un
  bucle se hacen una sola vez, antes.
- **Listas:** leer y escribir `a[i]` va en línea, sin llamar al runtime: un 31 % menos de tiempo. Aún es un 12-15 %
  más lento que por C.
- **Enteros:** `r = a + b` se calcula en el registro de `r`, y dividir por una constante sin comprobaciones cuando
  se sabe el rango. Las llamadas a funciones, un 8 % más rápidas.

Medido con `tools/comparativa/medir_dash.py` en un A1200 y un A500 emulados.

### 2.0.1 (2026-11-02)

La 2.0 pasa a `main`. Una sola orden, `./dash`, con dos caminos: directo a hunk (por defecto) y por C con gcc
(`--gcc`). Cómo instalar cada uno y cuándo usarlo: [README, Instalación](../README.es.md#instalación).

- **Un solo `dash`:** lo que en la 2.0.0 era la orden `./dash1` es ahora `./dash --gcc`. Un programa con C dentro
  (`@native`, `@c`, `@header`) o una opción de gcc (`-O`, `-O0`, `--small`, `--multifile`, `--no-hunk`) ya no da
  un error: `./dash` lo pasa por C él solo y lo dice en una línea. `./dash --version` dice "Dash 2.0.1". En el
  Amiga la orden también se llama `dash` (antes `dashc`), y sus runtimes, `dash_*.drt`.
- **Amiberry con JIT ya no se cierra:** en Amiberry 8.2.2 con JIT, en un PC, el emulador entero se cerraba con
  algunos programas (lo vio Tachyon, al descomprimir con zlib). Es un fallo de Amiberry
  ([aviso](https://github.com/BlitterStudio/amiberry/issues/2591)); gcc ya no genera las instrucciones que lo
  provocan (`-fno-branch-count-reg`), tampoco en el runtime del compilador directo. En un A500, algunos bucles
  muy cerrados compilados por C van hasta un 10 % más lentos; en un A1200, sin cambio claro.
- **`cpu_start` y `cpu_sample` con varios programas a la vez:** antes, dos programas que medían la CPU (la barra y
  el panel de Trasfondo) se repartían las tareas y cada uno veía solo las suyas. Ahora el primero publica su tabla
  y los demás la leen: todos ven todas las tareas.
- **Extensión de VS Code:** sus tareas, la vista previa y el depurador usan `./dash` y `./dash --gcc`; con una
  2.0.0 siguen como antes.

### 2.0.0 (2026-10-31, versión previa)

Un compilador nuevo. `./dash` es ahora **dashc**: escrito en C, genera él mismo el código 68000 y enlaza el
ejecutable con su runtime, sin gcc ni el Python con Lark de antes. El compilador de la 1.x sigue, sin cambios,
como `./dash1`. Sube el número mayor porque `./dash` deja de compilar los programas con C dentro y algunas opciones;
`./dash1` los compila como siempre. Detalle en el [manual, sección 24](MANUAL_REFERENCIA.md#24-dash-20-el-compilador-directo).

- **dashc:** el mismo lenguaje, los mismos builtins y el mismo runtime que la 1.x, así que los programas hacen lo
  mismo. En la batería de tests de Dash compilan todos los programas que no llevan C, y los que se comprueban en
  el emulador dan la misma salida que con la 1.x (salvo uno, por la FPU del emulador). Para construirlo basta un compilador de C del PC y Python 3
  (`make -C dashc`). `./dash --version` dice "Dash 2.0.0 (dashc)".
- **En el Amiga:** dashc también se compila para el Amiga (`make -C dashc amiga`, corre en un 68000) y, con el
  mismo fichero de entrada, escribe el mismo ejecutable byte a byte que el del PC. Para instalarlo allí,
  `dash-2.0.0-amiga.lha` (de `tools/paquete_amiga.py`), con su instalador: el cajón Dash y el `Assign DASH:`.
- **Qué cambiar:** un programa con `@native`, `@c` o `@header`, a `./dash1`, o su C a un objeto con `@link` y
  `@extern`. Las opciones `-O`, `-O0`, `--small`, `--multifile` y `--no-hunk`, a `./dash1`. En los dos casos
  `./dash` da un error con la orden de `./dash1` que lo hace. `--stack 0` ya no deja la pila del shell.
- **C ya compilado:** `@link "x.o"` o `"libx.a"` enlaza un objeto o una biblioteca del gcc de Amiga; `@extern`
  declara sus funciones (con `Int`, `Bool`, `String`, structs y `Func`); `@export` (nuevo, también en la 1.x)
  hace que una función de Dash se pueda llamar desde ese C por su nombre. El runtime pone lo de libc y libm que
  ese C necesita, y `dashc --cabecera` escribe los structs del programa como cabecera de C.
- **Opciones de dashc:** `--fpu`, `--cpu`, `--memcheck` (también junto con `--fpu`), `--stack`, `--profile` y
  `--debug`, que prepara el programa para el depurador nuevo.
- **Depurador nuevo:** los builtins `dbg_*` depuran desde otro programa uno compilado con `./dash --debug`
  (puntos de parada, paso a paso, pila, variables, registros y memoria). No usa el modo traza de la CPU, el que
  Emu68 no tiene.
- **`task_start`** acepta una función de Dash; dashc comprueba al compilar que no crea textos, listas ni structs
  (corre a la vez que el programa).
- **Builtins nuevos (también en la 1.x), 836 en total:** imágenes PNG, JPEG, GIF, BMP, WebP y SVG decodificadas
  por el programa, sin datatypes (`image_decode`); fuentes TrueType, WOFF y WOFF2 (`font_from_ttf`); red en una
  tarea aparte (`net_bg_*`); gzip y zlib (`inflate_auto`); sistema y programa (`time_unix`, `run_command`,
  `program_path`, `cpu_model`...); tareas, puertos y asignaciones del sistema (`tasks_read`, `ports_read`,
  `assigns_read`); ARexx (`rexx_send`); variables de entorno (`env_get`, `env_set`); memoria (`mem_puddle`,
  `mem_trim`); ventanas de otros programas, para pruebas (`window_find`, `input_menu`...); un gestor de ventanas
  (`wm_*`); el depurador (`dbg_*`) y más MUI.
- **Ventanas (también en la 1.x):** `On RightClick` (con `rmbtrap`), `On Inactive` y ventanas sin barra de título
  (`title ""`).
- **Memoria del C enlazado:** el `malloc` de dashc para ese C usa un pool de exec, y el `FreePooled` de exec 40
  (Kickstart 3.1) podía devolver al sistema un trozo del pool con bloques aún en uso, según lo que hubiera antes
  en esa memoria. dashc lo evita.
- **VS Code:** las tareas (compilar, ejecutar en el emulador, con comprobación de memoria o con perfil) y la vista
  previa de MUI ("Ver en Amiga") compilan con `./dash`, y con `./dash1` si el programa lleva C (`DASH_FALLBACK_DASH1=1`
  en `./dash`). El depurador (F5) también: compila con `./dash --debug` y depura en el Amiga emulado con el depurador
  nuevo, a través de `tools/amiga/dbgserver.dash`, que lo maneja con los `dbg_*` y habla con VS Code por la red. Un
  programa con C sigue con `./dash1 --debug` y gdb, como antes.
- **Medidas:** los ejecutables de los programas de prueba suelen salir algo más pequeños que con gcc, aunque hay
  casos más grandes. En Tachyon, de momento, más lento que la 1.x en casi todas las fases (hasta un 18 %, en un
  A1200 emulado).
- Probado en A1200 y A500 emulados (FS-UAE).

### 1.0.1 (2026-10-28)

Programas más rápidos y con menos memoria. No cambia nada del lenguaje: lo que compilaba con la 1.0.0 compila igual.
Detalle y medidas en [RECURSOS_LOOP.md](RECURSOS_LOOP.md) ("Tercera ronda").

- **Textos:** cada texto guarda su longitud y `s = a + b` se escribe en el sitio de `s` si cabe. Unir texto y número
  va un 17 % más rápido; la interpolación, un 8 %.
- **Diccionarios:** las claves literales llevan su hash calculado al compilar. Buscar con una clave literal va un
  34-41 % más rápido.
- **Comparar con un literal:** `s == "hola"` mira el primer carácter antes de llamar a `strcmp`. Una cadena de
  comparaciones va un 54 % más rápida.
- **Float:** en un 68020, 030 o 040 la multiplicación usa la instrucción de 32 bits del procesador: un 20 % más
  rápida. En el 68000, un 2 % más lenta (lo que cuesta mirar el procesador).
- **Memoria:** cada programa usa 8 KB menos (la pila para las excepciones del procesador ya no es aparte).
- **RTG:** el lienzo del escritorio sin fondo no lee de la tarjeta gráfica al actualizarse.
- **Coste:** los ejecutables son un 1,8 % más grandes; retornar un texto y crear un struct con texto, un 2-3 % más
  lentos.
- Sin probar en un 68060 ni en una máquina real.

### 1.0.0 (2026-10-27)

La primera versión con número. Recoge todo lo hecho hasta ahora (registro completo en [ROADMAP.md](ROADMAP.md)):

- **Lenguaje:** tipos inferidos, `Int`, `Float` (por software) y `Fixed` (16.16), textos con interpolación,
  listas y diccionarios con tipo, structs con métodos e interfaces, funciones como valores y lambdas, módulos con
  parte privada, memoria automática sin recolector (temporales por vuelta y contadores de referencias).
- **Sin gurús por un descuido:** un campo de `nil` o una excepción del procesador acaban el programa con un mensaje
  y la limpieza normal; `--memcheck` comprueba la memoria y `--debug` lleva al depurador.
- **686 builtins** (94 de MUI): Intuition, GadTools, ReAction, MUI 3.8 y 5, gráficos (también RTG), sprites,
  Copper, Blitter, audio y módulos ProTracker, IFF y datatypes, red (TCP, UDP y TLS con AmiSSL), procesos,
  commodities, catálogos de idioma, el portapapeles, el fondo del Workbench y monitores del sistema. Lista en
  [BUILTINS.md](BUILTINS.md).
- **Herramientas:** catálogos sin FlexCat (`tools/catalogo.py`), el emulador sin ventana (`tools/emu_run.py`),
  benchmarks y el editor visual de ventanas MUI (`.dashui`).
- **VS Code:** colores, errores al escribir, autocompletado, compilar y ejecutar en el Amiga emulado, depurar
  (también en un Amiga real por red) y el editor visual de MUI. Desde esta versión avisa de versiones nuevas de Dash.
- **Requisitos de los programas:** Kickstart 3.0 y un 68000; MUI y TLS piden un 68020. `--cpu 68020` a `68060`
  afina el código para cada procesador.
- **Para compilar:** Python 3 con Lark y el gcc de Amiga de bebbo (6.5); ver [INSTALACION.md](INSTALACION.md).
