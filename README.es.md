# D.A.S.H.

*[English](README.md) | Castellano*

**Development Amiga Synthesis Hub**

Lenguaje de programación de alto nivel que transpila a C para **Commodore Amiga**.

Escribe código limpio, sintetiza ejecutables nativos.

```
Source (.dash) → Parser (Lark) → AST → Analyzer → CodeGen → C → GCC → Amiga Executable
```

## Por qué Dash

Programar para Amiga en C implica gestión manual de memoria, punteros, includes interminables y conocer la API de AmigaOS a fondo. Dash elimina esa fricción: sintaxis clara inspirada en Ruby/Python, tipos inferidos y acceso directo a Intuition, Graphics, Audio, Sprites, Copper y más.

El resultado es un binario nativo m68k. Sin intérpretes, sin VM, sin compromiso.

## Ejemplo

```ruby
Window MiVentana
  title "Hola Dash"
  width 400
  height 150
end

Main
  MiVentana.open

  EventLoop
    On Close
      Print "Adiós!"
      Stop
    end
  end
end
```

```bash
./dash examples/hola.dash -o bin/hola
```

## Características

### Lenguaje
- Variables con inferencia de tipos (sin declaraciones)
- Enteros (también `0xDFF000`, `$DFF000`, `0b1010`), `Float` (coma flotante propia) y `Fixed` (coma fija
  16.16: decimales a velocidad de entero en un 68000)
- `nil` para structs, listas y textos (listas enlazadas, árboles, "sin objetivo")
- Expresiones aritméticas, lógicas, de comparación y de bits (`& | ^ ~ << >>`, también en `const`)
- Control de flujo: `if`/`elif`/`else`, `while`, `for`/`in`, `for`/`range` (también descendente y con `step`),
  `break` y `continue`
- Funciones con parámetros, retorno y recursión; funciones como valor y lambdas
- Listas con literales, índice, slicing, `.length` y tipo de elemento (`[String]`, `[Nodo]`...) que crecen
  (`push`, `pop`, `insert`, `remove`); diccionarios `{String: T}`, también de listas y de diccionarios, con
  `d.get(clave, defecto)` (una sola búsqueda); las
  funciones y métodos que devuelven listas o diccionarios conservan el tipo de sus elementos
- Textos con interpolación de cualquier expresión (`"#{a + 1}"`, `"#{f(x)}"`), concatenación eficiente y
  funciones (`str_find`, `str_replace`, `str_split`, `str_upper`...); un `Bool` se escribe `true`/`false`
- Structs con métodos, campos `weak` para referencias hacia atrás
- Constantes y enumeraciones
- Imports de módulos, y de ventanas MUI hechas con el editor visual (`.dashui`); lo que empieza por `_` en
  un módulo (funciones, constantes, globales, structs, enums) es privado y no choca con otro módulo
- Scope léxico
- Memoria automática: strings, listas y structs se liberan solos (temporales por vuelta y contador
  de referencias), sin recolector ni pausas

### Sin Gurus por un descuido

AmigaOS 3 no protege la memoria: en C, un puntero nulo o una división por cero se llevan el sistema entero
por delante. Un programa de Dash, en cambio, para con un mensaje y deja el Amiga como estaba:

- **Campos de `nil`**: leer o escribir un campo de un struct que es `nil`, o llamar a uno de sus métodos, da
  `Error: campo de nil (en juego.dash:42)`. Sin esa comprobación, la lectura daría basura y la escritura iría
  a la dirección 0, donde están los vectores del procesador.
- **Excepciones del procesador**: dirección impar, instrucción ilegal, división por cero, CHK, TRAPV... (lo que
  en C es un Guru, normalmente desde código `@native` o desde una librería que recibe un puntero malo). Cada
  programa pone su propio manejador en su tarea (`tc_TrapCode`) y, en vez del Guru, dice qué excepción fue y
  en qué punto del ejecutable.

En los dos casos el programa hace la limpieza de siempre (cierra sus ventanas, pantallas y librerías y libera
su memoria) y termina con el código de retorno 20; desde el Workbench, el mensaje sale en un requester.
Funciona en cualquier Amiga, también en un 68000 sin MMU, y cuesta poco: Tachyon (30.000 líneas) crece un 0,1 %.
Lo que no puede evitar es una escritura por un puntero salvaje en código C propio, que puede romper otra parte
del sistema sin que nadie se entere. Detalles en el [manual](docs/MANUAL_REFERENCIA.md) ("Errores en tiempo
de ejecución").

### Amiga API

633 funciones built-in, todas hechas (lista generada desde el código en [docs/BUILTINS.md](docs/BUILTINS.md)).

- **Intuition** — Ventanas, screens, event loops (también de varias ventanas), menús, `On Click`, `On Timer`;
  `window_create` con el tamaño interior (flag 8) y los bordes de la ventana (`window_border_top`...) y la
  fuente de la pantalla (`screen_font_height`, `screen_font_text_width`) para colocar gadgets
- **Interfaces** — GadTools (con atajos de teclado y gadgets medidos con la fuente), ReAction (hasta 4
  ventanas) y **MUI 3.8 o 5**: zona de dibujo propia (con doble búfer, rellenos, repintado de solo una zona con
  `mui_canvas_update_area` y el ratón sin clic con `mui_canvas_on_move` y `mui_canvas_pointer_x`/`_y`),
  temporizador, señales y ventanas a pantalla completa (con MUI 3.8 queda un marco de 4 y 3 píxeles alrededor);
  editor visual de ventanas MUI para VS Code
- **Graphics** — Primitivas de dibujo, colores, bitmaps, transparencias y degradados (rápidos también en
  RTG), búferes RGB24 en la ventana (también escalados: vídeo)
- **Sprites** — Hardware sprites y soft sprites
- **Copper** — Listas de cobre programables
- **Blitter** — BOBs y operaciones de blitting
- **Audio** — Tonos, samples 8SVX y sonidos hechos muestra a muestra (`audio.device`), y módulos ProTracker
  (`music_*`, reproductor propio)
- **IFF y datatypes** — Imágenes ILBM, PNG, JPEG, GIF, o desde píxeles RGB/RGBA en memoria (con
  transparencia, también en RTG y sin `picture.datatype`; en RTG, alfa de verdad: se mezclan con lo de debajo),
  sin tope de imágenes a la vez (antes, 64); fuentes de disco, también vectoriales (tamaño
  mínimo 2: con 1 o 0, diskfont y bullet de AmigaOS 3.2 escriben fuera de su memoria), y colores RGB
- **Red** — Con `bsdsocket.library` (cualquier pila: Roadshow, AmiTCP, MiamiDx): TCP como cliente y como
  servidor (`net_listen`, `net_accept`), UDP con difusión (`net_udp_*`) y TLS con AmiSSL (5.1 o posterior, o
  las anteriores) que comprueba el certificado; conexiones por pasos, sin esperar; la sesión TLS de cada
  servidor se reanuda en la siguiente conexión; `net_signal` despierta al programa cuando la red tiene algo; la
  red también desde una tarea de `task_start`. HTTP no es un builtin: cada programa lo hace sobre TCP y TLS
- **Procesos** — `task_start`: una función `@native` en otro proceso de AmigaOS; `task_signal` avisa al acabar
- **Escritorio y sistema** — `desktop_canvas*`: dibujar en el fondo del Workbench, detrás de los iconos (planar
  y RTG, con y sin backdrop; también con Directory Opus 5 o Scalos de escritorio); `cpu_*`: la CPU de cada
  tarea; `break_check`: parar con Ctrl-C un programa sin ventana; `single_instance`: una sola copia a la vez;
  `@workbench_output "NIL:"`: sin ventana de consola al arrancar desde el icono; `tooltype`; commodities
  (`cx_broker`, `cx_hotkey`, `cx_command`, `cx_wait`: el programa en Exchange y con tecla rápida);
  `run_program` y `program_relaunch`; `@version` (para `C:Version`) y `program_version()`
- **Medidores** — Discos montados con su tamaño y espacio libre (`disks_read`); interfaces de red de Roadshow con
  su estado y bytes (`net_ifs_read`); drivers SANA-II en uso, con cualquier pila, con sus paquetes y bytes
  (`net_drivers_read`, `net_driver_read`); señal WiFi (`wifi_read`, `wifi_read_device`); dispositivos USB de
  Poseidon (`usb_hid_*`); curva de aceleración de cada ratón (`mouse_curve`) y las preferencias del ratón
- **Idiomas, fecha y hora** — Catálogos de `locale.library`: `@catalog "X.catalog"`, `tr(id, texto)` (también
  en los `.dashui`), `catalog_open`; `tools/catalogo.py` hace los `.cd`, `.ct` y `.catalog` sin FlexCat.
  `clock_read` y `clock_year`... `clock_second`; `date_text(formato)` con `FormatDate` en el idioma del usuario
- **DOS** — Ficheros y directorios, requesters de ASL (ficheros, color, fuente), argumentos y tooltypes,
  vigilar ficheros (`file_notify`, `file_changed`)
- **RTG** — Tarjetas gráficas con CyberGraphX o Picasso96 (`rtg_*`: pantallas, píxeles, bloques, escalado)
- **Double Buffering** — Animación sin flicker
- **FFI** — Llamadas directas a funciones C/AmigaOS; C propio en línea (`@native`, `@c`) o enlazado (`@link`),
  con sus cabeceras (`@header`) y funciones de C declaradas (`@extern`)

Los programas necesitan Kickstart 3.0 o superior (usan los pools de memoria de exec V39) y funcionan en
un 68000. MUI (3.8 o 5) y TLS (AmiSSL 5.1 o posterior) piden un 68020 o superior. Algunas funciones piden
más: la red, una pila TCP/IP; `net_ifs_read` y `wifi_read`, Roadshow; `usb_hid_*`, Poseidon; ReAction, las
clases de AmigaOS 3.2.

### Lo que no hay

- HTTP como builtin: cada programa lo hace sobre TCP y TLS.
- Sockets raw (ICMP, para un ping) ni tramas en crudo de un driver SANA-II: hoy, con `@native`.
- Clases (OOP) y macros: son preguntas abiertas, sin decidir.
- Exports: descartado a propósito.

## Programas hechos con Dash

- [Tachyon](https://github.com/FreeMEM/tachyon) (antes dashweb): un navegador web para Amiga con MUI: XHTML,
  CSS, JavaScript (QuickJS) y HTTPS. Es el proyecto más grande escrito en Dash, y lo que le falta se añade a
  Dash. Tiene versiones alfa de prueba en sus [releases](https://github.com/FreeMEM/tachyon/releases).
- [Trasfondo](https://github.com/FreeMEM/trasfondo): un monitor de recursos (fecha y hora, CPU, memoria,
  tareas, discos, red y WiFi) pintado en el fondo del Workbench, detrás de los iconos; es una commodity.
  Versiones en sus [releases](https://github.com/FreeMEM/trasfondo/releases).
- Ratonera: aceleración del ratón por dispositivo (`mouse_curve`, `usb_hid_*`), en desarrollo.

## Desarrollar en VS Code

La extensión de `editor/vscode` hace de VS Code un entorno para Dash: colores, errores mientras se escribe,
completar, ir a la definición y renombrar; compilar y ejecutar en el Amiga emulado (A1200, A500, AmigaOS 3.2 o
con tarjeta gráfica); depurar con puntos de parada, variables y paso a paso, también en un Amiga de verdad por la
red; y un editor visual de ventanas MUI que las enseña en el emulador. Usa el compilador de este repositorio.
La versión publicada es la 0.2.4.

[![Tutorial en vídeo de Dash en VS Code](docs/media/vscode-tutorial.jpg)](https://youtu.be/_UTJ_0s3xLc)

Un tutorial de 6 minutos, con subtítulos: el primer proyecto, escribir código, la ventana, compilar y ejecutar,
depurar y depurar en un Amiga de verdad.

### Instalar la extensión

1. Dash y el compilador de Amiga, como en [Instalación rápida](#instalación-rápida) (para el emulador, FS-UAE y una
   ROM de Kickstart; para ventanas MUI, `tools/get_mui_sdk.sh` y `tools/emu_sys_mui.sh`).
2. La extensión: el fichero `dash-mui-editor-0.2.4.vsix` de la [release](https://github.com/FreeMEM/dash/releases/tag/vscode-0.2.4), y en VS Code (1.86 o posterior)
   **Extensions: Install from VSIX...**, o `code --install-extension dash-mui-editor-0.2.4.vsix`. También se
   puede construir: `cd editor/vscode && npm install && npm run package`.
3. Un proyecto: **Dash: Nuevo proyecto**. Si su carpeta no está dentro de este repositorio, **Dash: Elegir la
   carpeta del compilador** (el ajuste `dash.path`). La guía **Primeros pasos con Dash** lleva paso a paso, y si
   falta algo la extensión dice qué y cómo conseguirlo.

### Cómo encaja con Dash

La extensión es una capa fina: lo que hace lo hacen las herramientas de este repositorio, en la carpeta de
`dash.path`.

| En VS Code | Lo hace |
|---|---|
| Colores | `editor/vscode/syntaxes/dash.tmLanguage.json`, sacado de la gramática (`tools/gen_tmgrammar.py`) |
| Errores al escribir, completar, ir a la definición, renombrar, formatear | `compiler/lsp.py` (el mismo compilador) |
| Compilar | `./dash` |
| Ejecutar, memoria y perfil | `./dash` y `tools/emu_run.py` (FS-UAE o Amiberry) |
| Editor visual y Ver en Amiga | `.dashui` (`compiler/dashui.py`) y `tools/emu_preview.py` |
| Depurar (F5) | `./dash --debug`, `tools/emu_run.py --gdbserver`, `m68k-amigaos-gdb` con `tools/gdb/dash.py` y `bgdbserver` |

Por eso, al actualizar Dash (`git pull`), lo que la extensión sabe del lenguaje se actualiza también, sin
reinstalarla. La extensión y el compilador van en el mismo repositorio para que no se separen.

## Instalación rápida

### Ubuntu / Debian

```bash
# 1. Dependencias del sistema
sudo apt update
sudo apt install -y python3 python3-pip python3-dev make wget curl openssl git gcc g++ \
    lhasa libgmp-dev libmpfr-dev libmpc-dev flex bison \
    gettext texinfo ncurses-dev autoconf rsync libreadline-dev

# 2. Parser de Dash
pip install lark --break-system-packages

# 3. Cross-compiler para Amiga (m68k-amigaos-gcc)
git clone https://github.com/BlitterStudio/m68k-amigaos-gcc.git ~/m68k-amigaos-gcc
cd ~/m68k-amigaos-gcc
make update
sudo mkdir -p /opt/amiga && sudo chown $USER /opt/amiga
make all -j$(nproc)
make sdk=cgx            # cabeceras CyberGraphX (funciones rtg_*)

# 4. Añadir al PATH
echo 'export PATH="/opt/amiga/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 5. Clonar Dash y probar
git clone https://github.com/FreeMEM/dash.git
cd dash
./dash examples/hola.dash -o bin/hola
```

### CachyOS / Arch Linux

```bash
# 1. Dependencias del sistema
sudo pacman -S --needed python python-pip make wget curl openssl git gcc \
    lhasa gmp mpfr libmpc flex bison gettext texinfo \
    ncurses autoconf rsync readline

# 2. Parser de Dash
pip install lark --break-system-packages

# 3. Cross-compiler para Amiga (m68k-amigaos-gcc)
git clone https://github.com/BlitterStudio/m68k-amigaos-gcc.git ~/m68k-amigaos-gcc
cd ~/m68k-amigaos-gcc
make update
sudo mkdir -p /opt/amiga && sudo chown $USER /opt/amiga
make all -j$(nproc)
make sdk=cgx            # cabeceras CyberGraphX (funciones rtg_*)

# 4. Añadir al PATH
echo 'export PATH="/opt/amiga/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 5. Clonar Dash y probar
git clone https://github.com/FreeMEM/dash.git
cd dash
./dash examples/hola.dash -o bin/hola
```

> La compilación del cross-compiler tarda entre 30 minutos y 2 horas según tu hardware. Ver [docs/INSTALACION.md](docs/INSTALACION.md) para la guía completa, resolución de problemas y opciones avanzadas (macOS, versiones de GCC, elf2hunk).

## Uso

```bash
# Compilar a ejecutable Amiga (optimizado con gcc -O2)
./dash archivo.dash -o bin/archivo

# Sin optimizar (más fácil de depurar)
./dash -O0 archivo.dash -o bin/archivo

# Para el depurador (gdb, VS Code): -O0 -g y las líneas del C apuntan al .dash
./dash --debug archivo.dash -o bin/archivo

# Sin ruido: solo avisos, errores y el resultado (no cada orden y paso)
./dash -q archivo.dash -o bin/archivo

# Más pequeño (gcc -Os): ~7 % menos de tamaño, 10-50 % más lento en bucles
./dash --small archivo.dash -o bin/archivo

# Pila mínima del programa (por defecto 16 KB; 0 = la que dé el shell, 720 bytes menos)
./dash --stack 32768 archivo.dash -o bin/archivo

# Para Amigas con FPU 68881/68882 (Float con instrucciones de FPU; 68020+)
./dash --fpu archivo.dash -o bin/archivo

# Para Amigas aceleradas: código para esa CPU o mejor (68020, 68030, 68040, 68060); no arranca en una inferior
./dash --cpu 68040 archivo.dash -o bin/archivo

# Comprobación de memoria: avisa de dobles liberaciones y usos tras liberar, y de lo que queda vivo al salir
./dash --memcheck archivo.dash -o bin/archivo

# Perfil: llamadas y tiempo (propio y total) de cada función al salir
./dash --profile archivo.dash -o bin/archivo

# Ejecutar en FS-UAE sin ventana y ver la salida (Kickstart en $DASH_KICKSTART o AROS)
tools/emu_run.py archivo.dash
tools/emu_run.py --autoclose 3 ventana.dash   # termina sola a los 3 s
tools/emu_run.py --autoclose 30 --screenshot 20 shot.png ventana.dash   # captura de pantalla a los 20 s
tools/emu_run.py --debug r archivo.dash       # en cada debug_break(), los registros (depurador de FS-UAE)

# Compilar todos los ejemplos
./compile_all.sh

# Solo transpilar a C (sin compilar)
python3 -m compiler.main archivo.dash -o build/archivo.c

# Ejecutar tests (--emu: también los que comprueban la salida en FS-UAE; --emu-a500: además en un A500;
# --emu-32: además en un A1200 con AmigaOS 3.2, el único que prueba ReAction)
python3 tests/run_tests.py
python3 tests/run_tests.py --emu --emu-a500 --emu-32

# Medir velocidad, memoria y tamaño en un A500 y un A1200 emulados, y guardar la medida
tools/bench.py --save "descripción del cambio"
tools/bench_report.py        # datos y página del panel de comparativas (build/bench_report/)

# Programas aleatorios contra el conteo de referencias: salida comparada con un modelo y --memcheck
tools/fuzz_refcount.py -n 100
```

Variables del banco de pruebas: `DASH_KICKSTART` (ROM del A1200), `DASH_KICKSTART_A500` (ROM del A500),
`DASH_EMU_SYS` (directorio con `Libs`, `C` y `Classes` de un Workbench, para los tests que lo necesitan; se
puede sacar de un disco duro con `tools/emu_sys_from_hdf.sh`), y para `--emu-32` `DASH_KICKSTART_32` (ROM 3.2)
y `DASH_EMU_SYS_32` (los mismos ficheros de un Workbench 3.2). En esa máquina se carga el Workbench antes de
los programas (`emu_run.py --workbench`): la `window.class` de 3.2 lo espera. Para MUI y HTTPS, los sistemas con
MUI (`DASH_EMU_SYS_MUI`, `DASH_EMU_SYS_32_MUI`) y con AmiSSL (`DASH_EMU_SYS_SSL`, `DASH_EMU_SYS_32_SSL`). Los
tests `# rtg` usan una máquina 68040 con tarjeta gráfica y `DASH_EMU_SYS_32_RTG` (un Workbench 3.2 con
Picasso96). Todo en [docs/INSTALACION.md](docs/INSTALACION.md).

## Estructura del proyecto

```
dash                  CLI principal
compiler/             Transpilador (Python/Lark)
  grammar.py          Gramática del lenguaje
  transformer.py      Parse tree → AST
  ast_nodes.py        Nodos del AST
  analyzer.py         Análisis semántico
  codegen.py          Generación de código C
  amiga_builtins.py   Bindings de la API Amiga
  dashui.py           Ventanas del editor visual (.dashui) como código Dash
  lsp.py              Servidor de lenguaje para VS Code (con lsp_index.py y lsp_format.py)
  debuglines.py       ./dash --debug: líneas del C hacia el .dash
lib/amiga/            Módulos estándar de Amiga
runtime/softfloat/    Coma flotante por software (suma y multiplicación en ensamblador 68000)
tools/                Emulador (emu_run.py, emu_preview.py, capturas con tools/amiga/shot.c), sistemas emulados
                      (emu_sys_*.sh), SDK de MUI, AmiSSL y bgdbserver (get_*.sh), depurador (gdb_relay.py,
                      gdb/dash.py), benchmarks (bench.py, bench_report.py), catálogos (catalogo.py),
                      fuzz_refcount.py, gen_builtins_doc.py, gen_tmgrammar.py
editor/vscode/        Extensión de VS Code: colores, errores al escribir, compilar, emulador, depurador, editor
                      visual de MUI
examples/             Programas de ejemplo (34)
tests/                Suite de tests (tests/errors: deben fallar; tests/runtime: runtime en el PC;
                      tests/lsp y tests/unit: tests en Python; tests/bench: benchmarks)
docs/                 Documentación
```

## Documentación

- [Documentación del lenguaje](docs/DOCUMENTACION_LENGUAJE.md) — Guía completa
- [Manual de referencia](docs/MANUAL_REFERENCIA.md) — Referencia del programador
- [Comparativa con Blitz, AMOS y C](docs/COMPARATIVA.md) — Velocidad, memoria y estabilidad medidas en A500 y A1200
- [Quick Reference](docs/QUICK_REFERENCE.md) — Cheat sheet
- [Funciones built-in](docs/BUILTINS.md) — Lista real, generada desde el código
- [MUI en Dash](docs/MUI_DISEÑO.md) — Diseño de la API de MUI
- [Editor visual de MUI](docs/MUI_EDITOR.md) — Formato `.dashui` y extensión de VS Code
- [API Amiga](docs/AMIGA_API.md) — Catálogo de diseño de la API (el original; la lista real es BUILTINS.md)
- [Instalación](docs/INSTALACION.md) — Setup del entorno
- [Requisitos funcionales](docs/REQUERIMIENTOS_FUNCIONALES.md) y [del sistema](docs/REQUERIMIENTOS_SISTEMA.md) —
  Los requisitos originales, con lo hecho, lo descartado y lo que falta
- [Roadmap](docs/ROADMAP.md) — Plan de desarrollo y registro de lo hecho

## Licencia

MIT (ver [LICENSE](LICENSE)). Los programas compilados con Dash pueden llevar la licencia que quieras.
El float por software (`runtime/softfloat/fp-bit.*`) viene de GCC: GPL con la excepción de runtime,
que permite distribuir los programas con cualquier licencia.
