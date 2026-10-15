# D.A.S.H.

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
- Expresiones aritméticas, lógicas y de comparación
- Control de flujo: `if`/`else`, `while`, `for`/`in`, `for`/`range` (también descendente y con `step`),
  `break` y `continue`
- Funciones con parámetros, retorno y recursión
- Arrays con literales, acceso por índice, slicing y `.length`
- Strings con interpolación, concatenación y operaciones
- Structs con métodos
- Constantes y enumeraciones
- Imports de módulos
- Scope léxico
- Memoria automática: strings, listas y structs se liberan solos (temporales por vuelta y contador
  de referencias), sin recolector ni pausas

### Amiga API
- **Intuition** — Ventanas, screens, event loops, GadTools, ReAction
- **Graphics** — Primitivas de dibujo, colores, bitmaps
- **Sprites** — Hardware sprites y soft sprites
- **Copper** — Listas de cobre programables
- **Blitter** — BOBs y operaciones de blitting
- **Audio** — Reproducción de tonos y samples
- **IFF** — Carga de imágenes ILBM
- **DOS** — Operaciones de ficheros
- **RTG** — Soporte para tarjetas gráficas
- **Double Buffering** — Animación sin flicker
- **FFI** — Llamadas directas a funciones C/AmigaOS

Los programas necesitan Kickstart 3.0 o superior (usan los pools de memoria de exec V39) y funcionan en
un 68000.

## Instalación rápida

### Ubuntu / Debian

```bash
# 1. Dependencias del sistema
sudo apt update
sudo apt install -y python3 python3-pip make wget git gcc g++ \
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
sudo pacman -S --needed python python-pip make wget git gcc \
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

# Más pequeño (gcc -Os): ~7 % menos de tamaño, 10-50 % más lento en bucles
./dash --small archivo.dash -o bin/archivo

# Pila mínima del programa (por defecto 16 KB; 0 = la que dé el shell, 720 bytes menos)
./dash --stack 32768 archivo.dash -o bin/archivo

# Para Amigas con FPU 68881/68882 (Float con instrucciones de FPU; 68020+)
./dash --fpu archivo.dash -o bin/archivo

# Comprobación de memoria: avisa de dobles liberaciones y usos tras liberar, y de lo que queda vivo al salir
./dash --memcheck archivo.dash -o bin/archivo

# Ejecutar en FS-UAE sin ventana y ver la salida (Kickstart en $DASH_KICKSTART o AROS)
tools/emu_run.py archivo.dash
tools/emu_run.py --autoclose 3 ventana.dash   # termina sola a los 3 s

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
los programas (`emu_run.py --workbench`): la `window.class` de 3.2 lo espera.

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
lib/amiga/            Módulos estándar de Amiga
runtime/softfloat/    Coma flotante por software (suma y multiplicación en ensamblador 68000)
tools/                Emulador (emu_run.py), benchmarks (bench.py, bench_report.py), gen_builtins_doc.py
examples/             Programas de ejemplo
tests/                Suite de tests (tests/errors: deben fallar; tests/runtime: runtime en el PC;
                      tests/bench: benchmarks)
docs/                 Documentación
```

## Documentación

- [Documentación del lenguaje](docs/DOCUMENTACION_LENGUAJE.md) — Guía completa
- [Manual de referencia](docs/MANUAL_REFERENCIA.md) — Referencia del programador
- [Quick Reference](docs/QUICK_REFERENCE.md) — Cheat sheet
- [Funciones built-in](docs/BUILTINS.md) — Lista real, generada desde el código
- [API Amiga](docs/AMIGA_API.md) — Catálogo de diseño de la API
- [Instalación](docs/INSTALACION.md) — Setup del entorno
- [Roadmap](docs/ROADMAP.md) — Plan de desarrollo

## Licencia

Este proyecto es software libre. Ver fichero LICENSE para detalles.
