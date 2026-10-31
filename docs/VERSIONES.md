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

### 2.0.0 (sin publicar)

Un compilador nuevo. `./dash` es ahora **dashc**: escrito en C, genera él mismo el código 68000 y enlaza el
ejecutable con su runtime, sin gcc ni el Python con Lark de antes. El compilador de la 1.x sigue, sin cambios,
como `./dash1`. Sube el número mayor porque `./dash` deja de compilar los programas con C dentro y algunas opciones;
`./dash1` los compila como siempre. Detalle en el [manual, sección 24](MANUAL_REFERENCIA.md#24-dash-20-el-compilador-dashc).

- **dashc:** el mismo lenguaje, los mismos builtins y el mismo runtime que la 1.x, así que los programas hacen lo
  mismo. En la batería de tests de Dash compilan todos los programas que no llevan C, y los que se comprueban en
  el emulador dan la misma salida que con la 1.x (salvo uno, por la FPU del emulador). Para construirlo basta un compilador de C del PC y Python 3
  (`make -C dashc`). `./dash --version` dice "Dash 2.0.0 (dashc)".
- **En el Amiga:** dashc también se compila para el Amiga (`make -C dashc amiga`, corre en un 68000) y, con el
  mismo fichero de entrada, escribe el mismo ejecutable byte a byte que el del PC.
- **Qué cambiar:** un programa con `@native`, `@c` o `@header`, a `./dash1`, o su C a un objeto con `@link` y
  `@extern`. Las opciones `-O`, `-O0`, `--small`, `--multifile` y `--no-hunk`, a `./dash1`. En los dos casos
  `./dash` da un error con la orden de `./dash1` que lo hace. El depurador de VS Code (gdb) sigue con
  `./dash1 --debug`. `--stack 0` ya no deja la pila del shell.
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
- **VS Code:** "ejecutar en el emulador" compila con `./dash` (y con `./dash1` si el programa lleva C); las
  tareas, el depurador y la vista previa de MUI siguen con `./dash1`.
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
