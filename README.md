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
- Expresiones aritméticas, lógicas y de comparación
- Control de flujo: `if`/`else`, `while`, `for`/`in`, `for`/`range`
- Funciones con parámetros, retorno y recursión
- Arrays con literales, acceso por índice, slicing y `.length`
- Strings con interpolación, concatenación y operaciones
- Structs con métodos
- Constantes y enumeraciones
- Imports de módulos
- Scope léxico

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

## Requisitos

- **Python 3.10+** con librería [Lark](https://github.com/lark-parser/lark)
- **m68k-amigaos-gcc** — Cross-compiler ([BlitterStudio](https://github.com/BlitterStudio/m68k-amigaos-gcc))
- **Linux**, macOS o Windows (WSL2)

Ver [docs/INSTALACION.md](docs/INSTALACION.md) para la guía completa de instalación.

## Uso

```bash
# Compilar a ejecutable Amiga
./dash archivo.dash -o bin/archivo

# Solo transpilar a C (sin compilar)
python3 -m compiler.main archivo.dash -o build/archivo.c

# Ejecutar tests
python3 tests/run_tests.py
```

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
runtime/              Headers del runtime (arrays, strings)
lib/amiga/            Módulos estándar de Amiga
examples/             Programas de ejemplo
tests/                Suite de tests
docs/                 Documentación
```

## Documentación

- [Documentación del lenguaje](docs/DOCUMENTACION_LENGUAJE.md) — Guía completa
- [Manual de referencia](docs/MANUAL_REFERENCIA.md) — Referencia del programador
- [Quick Reference](docs/QUICK_REFERENCE.md) — Cheat sheet
- [API Amiga](docs/AMIGA_API.md) — Referencia de la API
- [Instalación](docs/INSTALACION.md) — Setup del entorno
- [Roadmap](docs/ROADMAP.md) — Plan de desarrollo

## Licencia

Este proyecto es software libre. Ver fichero LICENSE para detalles.
