# D.A.S.H. Language - Programmer's Reference Manual

*English | [Castellano](MANUAL_REFERENCIA.md)*

**D.A.S.H.** (*Development Amiga Synthesis Hub*) — A high-level language for the Amiga that compiles to C

*Updated: October 2026*

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Program Structure](#2-program-structure)
3. [Variables and Data Types](#3-variables-and-data-types)
4. [Constants](#4-constants)
5. [Operators](#5-operators)
6. [Control Structures](#6-control-structures)
7. [Functions](#7-functions)
8. [Structures (Structs)](#8-structures-structs)
9. [Enumerations](#9-enumerations)
10. [Arrays](#10-arrays)
11. [Screens](#11-screens)
12. [Windows and Events](#12-windows-and-events)
13. [Graphics](#13-graphics)
14. [Input (Keyboard, Mouse, Joystick)](#14-input-keyboard-mouse-joystick)
15. [Audio and Music](#15-audio-and-music)
16. [File System](#16-file-system)
17. [Memory Management](#17-memory-management)
18. [System Functions](#18-system-functions)
19. [User Interface - GadTools](#19-user-interface---gadtools)
20. [User Interface - ReAction](#20-user-interface---reaction)
20b. [User Interface - MUI](#20b-user-interface---mui)
21. [Modules and Imports](#21-modules-and-imports)
22. [Complete Examples](#22-complete-examples)
23. [Quick Reference](#23-quick-reference)

---

## 1. Introduction

Dash is a high-level programming language designed for writing applications and games for the Amiga. The compiler translates Dash code into a single C file, and bebbo's gcc (`m68k-amigaos-gcc`) compiles that into an AmigaOS executable.

### Main Features

- Clear, modern syntax inspired by Ruby and Python
- Native integration with AmigaOS (Intuition, Graphics, DOS, Exec, Commodities, Locale...)
- Simplified window and graphics system
- 659 built-in functions (listed in [BUILTINS.en.md](BUILTINS.en.md)) for graphics, audio, files, networking (TCP, UDP,
  TLS), GUI (GadTools, ReAction, MUI), commodities, catalogs, date and time, disks and WiFi, and more
- Structs with methods (lightweight object-oriented programming)
- Automatic memory management with Reference Counting
- Arena Allocators for maximum performance

### Requirements

- AmigaOS 3.0 (Kickstart 39) or later. A 68000 will do, except for MUI 5 and TLS (AmiSSL), which need a 68020.
- TLS: AmiSSL 5.1 or later installed. Networking: a TCP/IP stack (Roadshow, AmiTCP, MiamiDx...).
- ReAction: AmigaOS 3.2 (that is where it is tested).

### What is not there

- HTTP: there is no `Http.get` and no HTTP builtin. Each program does it on top of `net_*` (TCP) and `tls_*`.
- Raw sockets (`SOCK_RAW`) or raw SANA-II frames: from the drivers only counters and the WiFi signal are read.
- Classes (OOP with inheritance) and macros: open questions, not yet decided.
- `export` in modules: deliberately ruled out (anything starting with `_` is private; everything else is public).

Real programs written in Dash: Tachyon (web browser, MUI), Trasfondo (a monitor in the Workbench background)
and Ratonera (an acceleration curve for each mouse, in development).

### Hello World

```
Main
    Print "Hola Amiga!"
end
```

### Compiling

```bash
./dash programa.dash -o programa              # gcc -O2, for 68000
./dash -O0 programa.dash -o programa          # unoptimized (for debugging)
./dash --small programa.dash -o programa      # gcc -Os: ~7 % smaller, slower loops
./dash --stack 32768 programa.dash -o prog    # minimum stack (16 KB by default; 0 = the shell's)
./dash --fpu programa.dash -o programa        # 68020 with 68881/68882 FPU only
./dash --cpu 68040 programa.dash -o programa  # 68020 code tuned for the 68040 (68020/030/040/060)
./dash --memcheck programa.dash -o programa   # memory checking (for testing)
./dash -q programa.dash -o programa           # only warnings, errors and the result
./dash -v programa.dash -o programa           # shows each step of the transpiler
./dash --multifile programa.dash -o programa  # one .c per module (in build/<name>_multi/)
./dash --no-hunk programa.dash -o programa    # leaves gcc's output as is, without converting it to Hunk
```

The C code and the intermediate files go to `build/`, in the directory `./dash` is called from.
Bebbo's gcc already produces Hunk, so `--no-hunk` only makes a difference with a gcc that outputs ELF.

Without `--cpu`, the program is 68000 code and starts on any Amiga. With `--cpu 68020`, `68030`, `68040` or `68060`
it is 68020 code tuned for that CPU: it will not start on a lower one, but on an accelerated Amiga it multiplies and
divides in one instruction (on an emulated 68040, `Fixed` divides about 30 times faster and multiplies 4 times;
strings, 13 %). With `--cpu 68060` the runtime avoids the 64-bit instructions the 68060 lacks (68060.library emulates
them, very slowly). It can be combined with `--fpu`.

Environment variables:

| Variable | Purpose |
|---|---|
| `DASH_TOOLCHAIN` | Folder of bebbo's gcc, if it is not in `/opt/amiga` |
| `DASH_CFLAGS` | Extra options for gcc (for example `DASH_CFLAGS="-fbbb=-"`) |
| `DASH_MUI_SDK` | The `SDK/MUI` folder of the MUI SDK (by default, the one from `tools/get_mui_sdk.sh`) |
| `DASH_AMISSL_SDK` | The `AmiSSL/Developer` folder of the AmiSSL SDK (by default, the one from `tools/get_amissl.sh`) |
| `DASH_PRINT_FLUSH=1` | Each `Print` comes out immediately (see below) |

`./dash --debug` compiles for the debugger: `-O0 -g` (DWARF in the executable) and, in the C code, `#line` pointing to the
lines of the `.dash` file: `m68k-amigaos-gdb` stops, steps and shows the stack and the variables in Dash lines
(with `bgdbserver` on the Amiga: see the VS Code extension). Without `--debug` the C code does not change. With `--debug`, also:
each `Print` comes out immediately; if the DOS variable `DASH_OUT` holds a file name, the output goes there;
a program error (index out of range, memory error) calls `_dash_debug_stop`, where the debugger
stops; and zero-initialized globals (`.bss`) go in the same block as the others, so that gdb can find them
(`tools/gdb_relay.py`). The executable grows by the space they take.

With `--memcheck`, each memory error also says where it happened: `memcheck: ERROR campo de nil (en
prog.dash:15)` (each statement records its file and line; only in those builds).

With `DASH_PRINT_FLUSH=1` at compile time, each `Print` comes out immediately (dos.library `Flush`) even if the
output goes to a file: that way `tools/emu_run.py --follow` and the VS Code extension see it live. Without it
the C code does not change.

Compiler errors say where they are: `fichero.dash:línea:columna: Error: mensaje` (also those in an
imported module, with its file), like gcc: editors link them to the code. Syntax errors are
reported in one sentence (`sintaxis: no se esperaba ... aquí; se esperaba ...`).

Programs need Kickstart 3.0 or higher. On startup they ask for a stack of at least 16 KB:
the 3.1 shell gives 4 KB and a moderately deep recursion would overflow it (it costs 720 bytes per program;
`--stack 0` removes it). With MUI they ask for 32 KB and with TLS 64 KB. A program or module that needs
more says so with `@stack 262144` (in bytes, at function level): the program takes the largest of
them all; `--stack` still overrides.

Started from the Workbench (its icon), a program has no console: the first thing it writes opens a
libnix `CON:` window. `@workbench_output "NIL:"` (at function level) removes it: whatever is written is
lost. Any file or window will do, for example `@workbench_output "CON:0/0/640/200/Mi programa/AUTO/CLOSE"`.
From the Shell nothing changes. If both the program and a module set it, the program's wins.

`@version "Mi programa 1.2"` (at function level) puts `$VER: Mi programa 1.2 (24.10.2026)` in the executable,
with the date of the day it is compiled, for `C:Version` and the Workbench (Information). `program_version()` returns
`"Mi programa 1.2"` inside the program (`""` without the directive), for example for the title of `cx_broker`.

`--profile` compiles a version that, on exit, writes a table with the calls to each function and
the time spent in it (self) and in what it calls (total), from slowest to fastest
(`perfil: ...`). Time is measured by checking where the program is 50 times per second (VBlank
interrupt): it takes a few seconds of running for it to be reliable.

`--memcheck` compiles a test version that watches the memory of lists, structs and strings. It warns
as soon as something is freed twice or used after being freed (`memcheck: ERROR ...`) and, on
exit, says how much is still alive:

```
memcheck: vivos 0 objetos y 0 strings (escapados 0 y 0), errores 0
```

"Escaped" ones (`escapados`) are those that were stored inside a list or handed to C code: they are freed on
program exit. For the count to be useful, `Main` releases its variables when it finishes (only in
this mode). Freed blocks are filled with `0xDB` and the last 64 are not reused, so they can be
recognized. It is slower and uses a little more memory; without the option it costs nothing.

---

## 2. Program Structure

### Basic Structure

```
# Imports (optional)
import "lib/utils.dash"

# Constants (optional)
const MAX_ENEMIES = 10
const TITLE = "Mi Juego"

# Enumerations (optional)
enum GameState
    MENU
    PLAYING
    PAUSED
end

# Global variables (optional): with var and their type
var puntos: Int = 0

# Structures (optional)
struct Player
    x: Int
    y: Int
end

# Window definition (optional)
Window MainWindow
    title "Mi Aplicacion"
    width 320
    height 200
end

# Functions (optional)
func calculate(a, b)
    return a + b
end

# Main block (required)
Main
    # Program code
    Print "Iniciando..."
end
```

The parts can go in any order, except that a constant can only use those defined before it.

### Comments

```
# This is a single-line comment
x = 10  # Comment at the end of a line
```

---

## 3. Variables and Data Types

### Declaring Variables

Variables are declared implicitly on their first assignment:

```
# Integers
edad = 25
puntuacion = -100
hex_value = 0xFF       # hexadecimal (also $FF, Amiga style)
bits = 0b1010          # binary

# Strings
nombre = "Amiga"
mensaje = "Hola Mundo"

# Booleans
activo = true
pausado = false

# Arrays
numeros = [1, 2, 3, 4, 5]
vacio = []
```

### Data Types

| Type | Description | Example |
|------|-------------|---------|
| Int | Signed 32-bit integer | `42`, `-100`, `0xFF`, `$DFF000`, `0b1010` |
| Float | 32-bit decimal (about 7 digits) | `1.5`, `-0.25`, `2.0e3` |
| Double | 64-bit decimal (15 to 17 digits) | `Double(0.1)`, `var d: Double = 2.5` |
| Fixed | 16.16 fixed point: fast decimals on a 68000 | `Fixed(1.5)`, `Fixed(n)` |
| String | Text string | `"Hola"` |
| Bool | Boolean value (`Print` and strings write it as `true` / `false`) | `true`, `false` |
| Array | Collection of elements (untyped: read as integers) | `[1, 2, 3]` |
| `[T]` | List of `T` (`[Int]`, `[String]`, `[Enemigo]`, `[[Int]]`, `[Fixed]`) | `var l: [String] = []` |
| `{String: T}` | Dictionary with string keys | `{"Ana": 30}` |
| `{Int: T}` | Dictionary with integer keys | `{1: "one"}` |
| Struct | User-defined compound type | `Player(10, 20)` |
| Func | A function or a lambda, to pass around as a value | `fn(x) -> x * 2` |
| Pointer | Memory address (for C and the system) | `buffer_alloc(64)` |

### Fixed (fixed point)

`Fixed` stores a number with decimals in a 32-bit integer: 16 bits of integer part and 16 of
fraction. Range from -32768 to 32767.9999, in steps of 1/65536 (about 4 decimal digits). On a
68000 without an FPU it is much faster than `Float`:

| Operation (A500, cycles) | Fixed | Float |
|--------------------------|-------|-------|
| Addition, subtraction, comparison | like an integer | ~750 |
| Multiplication | ~390 | ~940 |
| Multiplied or divided by an integer | like an integer | ~940 |
| Division | ~2,200 | |

```
v = Fixed(1.5)              # a literal is computed at compile time
g = Fixed(0.35)
y = Fixed(0)
y = y + v                   # integer addition
v = v * Fixed(0.85)         # Fixed * Fixed
v = v * 2                   # by an integer: integer multiplication
x = Int(y)                  # truncates towards zero
Print "y = #{y}"            # up to 4 decimals: y = 1.5
r = fx_sqrt(Fixed(2))       # 1.4142
s = fx_sin(Fixed(30))       # 0.5 (degrees); also fx_cos
```

- An integer given to a `Fixed` (variable, field, parameter, `return`) is converted automatically:
  `var v: Fixed = 3`, `b.x = 2`, `mitad(5)` with `func mitad(v: Fixed)`.
- Mixing `Fixed` and `Float` is an error: convert with `Fixed(f)` or `Float(x)`.
- Going out of range wraps around, like an integer. Dividing by 0 gives the maximum value with
  the sign of the dividend (it does not hang the Amiga).
- Fields, parameters and return values can be `Fixed`. Complete example: `examples/fixed_gravedad.dash`.
- Lists of `Fixed`: a literal with at least one `Fixed` (`[Fixed(1.5), 2, Fixed(-0.25)]`: the numbers are
  converted), or declared `[Fixed]` (variables, parameters, return values, fields). `l[i]`, `push`, `insert`,
  `pop`, `for v in l`, slices and `+` return and take `Fixed`; `l.push(2)` stores 2.0. They are stored as a
  list of integers (a `Fixed` is a `LONG`). Lists of `Float` and of `Double` are in the `Double` section.

### Double (64 bits)

`Double` is a C `double` (64-bit IEEE 754): 15 to 17 digits, for money and spreadsheet cells. With
`--fpu` the FPU does it; without one, GCC's software floating point (slower than `Float`).

```
d = Double(0.1)             # a literal where a Double goes keeps all its digits
var t: Double = 0.2         # also in declared variables, fields, parameters and return
s = d + t                   # 0.30000000000000004, as in any language with doubles
n = Int(d)                  # truncates toward zero; Float(d) loses digits
x = Double("2.5e-3")        # from text: exact up to 17 significant digits; 0.0 if there is no number
Print "s = #{s}"            # the shortest decimal that reads back the same (Ryu): s = 0.30000000000000004
p = str_from_double(2.675, 2)   # "2.68": fixed decimals, the shortest decimal rounded (as a spreadsheet)
```

- A literal (`0.1`) where a `Double` goes (in an operation with a `Double`, given to a `Double` variable,
  field or parameter, in a `return` of a `Double` function) is a C `double`. Elsewhere it is a `Float`:
  `d = 0.1` undeclared is a `Float`.
- A `Float` or an `Int` become `Double` by themselves; a `Double` into a `Float` or an `Int` is an error
  (`Float(d)`, `Int(d)`). Mixing `Fixed` and `Double` is an error.
- It is written in fixed notation while the point falls within 17 digits (`150.0`, `0.00001`) and with an
  exponent beyond that (`1.0e17`, `1.0e-6`); `inf`, `-inf` and `nan` when they come.
- Lists of `Double` and of `Float`: a literal with some `Double` is a `[Double]`, and one with some
  `Float` (`[1.5, 2]`) is a `[Float]`. Also declared: `var l: [Double] = [1, 2]` (there the numbers of the
  literal are `Double`), parameters, returns, fields, `[[Double]]` and `{String: [Double]}`. `l[i]`,
  `push`, `insert`, `pop`, `remove`, `clear`, `for v in l`, slices and `+` work as in a list of integers.
  A `[Double]` takes 8 bytes per element; a `[Float]`, 4. A `[Float]` does not fit where a `[Double]`
  goes (they are stored differently): it is an error.

Math functions (with fdlibm; an `Int` or a `Float` goes in as a `Double` and a `Double` comes out):
`sqrt`, `pow`, `exp`, `log`, `log10`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2(y, x)`, `floor`,
`ceil`, `round` (halves away from zero: `round(2.5)` is `3.0`), `trunc`, `fmod`, `abs`, `is_nan` and
`is_inf`. Angles are in radians. They give the same digits with and without `--fpu` (now and then, not the
last one). Without an FPU they are slow: on an A1200, `sin` takes about 7 ms and `pow` about 20; with a
68882, 0.1 and 0.25 ms.

```
h = sqrt(3.0 * 3.0 + 4.0 * 4.0)     # 5.0
n = Int(round(2.5))                 # 3: Int() to keep it in an Int
x = fmod(-7.5, 2.0)                 # -1.5: the sign of the first one
if is_nan(sqrt(Double(-1)))         # nan is not even equal to itself: is_nan
```

### Type Inference

The type is inferred automatically:

```
x = 10          # Int
name = "Dash"   # String
flag = true     # Bool
nums = [1,2,3]  # Array of Int
v = 1.5         # Float
```

### Float

```
v = 2.5
area = 3.14159 * r * r      # Int and Float mix: the result is Float
n = Int(v)                  # 2 (truncates towards zero)
f = Float(7) / 2            # 3.5 (7 / 2 between integers gives 3)
Print "v = " + v            # v = 2.5
Print "#{v} metros"

struct Cuerpo
    masa: Float
end

func doble(x: Float) -> Float
    return x * 2.0
end
```

- A decimal literal needs digits on both sides of the point: `1.0`, not `1.` (so `1..10` is still a range).
- A variable that started out as Int cannot receive a Float (`n = 0` and then `n = 2.5` is an error):
  declare it with `n = 0.0` or convert with `Int()`.
- `%` only with integers. Lists hold integers, `Bool`, strings, `Fixed`, structs, lists and
  dictionaries, but not `Float` (`[1.5, 2.0]` is an error): use a struct with `Float` or `Fixed` fields.
- `./dash --fpu` compiles for 68020 + 68881/68882 FPU: Floats use FPU instructions
  (much faster, and the executable is smaller). On a machine without an FPU, libnix shows a
  system message and the program exits. Like LightWave: one version for each machine.
- Without `--fpu` (a 68000 has no FPU) operations are done in software (GCC routines in
  `runtime/softfloat`, about 4 KB, only if the program uses Float). They do not depend on
  `mathieeesingbas.library`, which hangs in FS-UAE with Kickstart 3.1 and no FPU.

### Global variables

A global variable is declared outside `Main` and the functions, with `var`, its name and its type.
The type is mandatory (`var x = 5` is a syntax error). The value is optional: without it, it starts
at 0 (or `nil` for strings, lists, dictionaries and structs).

```
var puntos: Int = 0
var nombres: [String] = []
var titulo: String = "Dash"
var total: Int                  # 0

func sumar(n)
    puntos = puntos + n         # the program's functions can see and change it
end

Main
    sumar(10)
    Print puntos                # 10
end
```

Functions in an imported module do not see the program's globals (see
[Modules and Imports](#21-modules-and-imports)). Inside `Main` or a function, `var nombre: Tipo = valor`
declares a local variable with its type.

### Variable scope

A variable created inside a block (`if`, `elif`, `else`, `while`, `for`) only exists in that
block. From inside, the variables of the enclosing block can be seen and changed:

```
a = 1
if a == 1
    b = 2                       # b only exists inside the if
    a = 3                       # changes the outer a
end
Print a                         # 3
Print b                         # error: Variable 'b' is not defined
```

To use a value computed inside afterwards, create the variable before the block (`b = 0`).

---

## 4. Constants

Constants are defined with `const` and cannot be modified:

```
const MAX_VIDAS = 3
const SCREEN_WIDTH = 320
const SCREEN_HEIGHT = 200
const GAME_TITLE = "Space Invaders"
const DEBUG_MODE = true
const AREA = SCREEN_WIDTH * SCREEN_HEIGHT   # integer expression: computed at compile time
const BIT_FUEGO = 1 << 7
```

The value is a literal (number, string, `true`/`false`, `Float`) or an integer expression of numbers and
constants declared earlier (`+ - * / %` and the bitwise operators); it is computed at compile time, in 32 bits.

### Using Constants

```
Main
    Print GAME_TITLE

    for i in (1..MAX_VIDAS)
        Print "Vida: "
        Print i
    end

    if DEBUG_MODE
        Print "Modo debug activo"
    end
end
```

---

## 5. Operators

### Arithmetic Operators

| Operator | Operation | Example |
|----------|-----------|---------|
| `+` | Addition | `a + b` |
| `-` | Subtraction | `a - b` |
| `*` | Multiplication | `a * b` |
| `/` | Division | `a / b` |
| `%` | Modulo | `a % b` |
| `-` | Negation (unary) | `-x` |

```
resultado = (10 + 5) * 2    # 30
resto = 17 % 5              # 2
negativo = -valor
```

### Bitwise Operators

On integers (a `Float` or a `Fixed` is converted first with `Int()`):

| Operator | Operation | Example |
|----------|-----------|---------|
| `&` | Bitwise AND | `color & 0xFF` |
| `\|` | Bitwise OR | `flags \| 4` |
| `^` | Exclusive OR | `a ^ b` |
| `~` | Complement (unary) | `~mascara` |
| `<<` | Shift left | `1 << 4` |
| `>>` | Shift right (arithmetic: keeps the sign) | `rgb >> 16` |

Precedence as in Python: shifts bind tighter than `&`, which binds tighter than `^`, which
binds tighter than `|`; all of them below `+ -` and above comparisons. So `1 + 2 << 1`
is 6 and `a & 4 == 4` is `(a & 4) == 4` (in C it would be the other way round). `~` works like unary `-`.

```
const MASCARA = 1 << 4             # a const can be an integer expression of numbers and
const TODOS = (1 << 8) - 1         # earlier constants: computed at compile time (255)
rojo = (rgb >> 16) & 0xFF
if flags & MASCARA != 0
    Print "activo"
end
```

### Comparison Operators

| Operator | Meaning |
|----------|-------------|
| `==` | Equal to |
| `!=` | Not equal to |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

With strings, `==` and `!=` compare the contents, and `<`, `>`, `<=`, `>=` the order: byte by byte, like
`strcmp` (`"abc" < "abd"`, `"" < "a"`, uppercase before lowercase).

### Logical Operators

| Operator | Meaning |
|----------|-------------|
| `and` | Logical AND |
| `or` | Logical OR |
| `not` | Negation |

```
if x > 0 and x < 100
    Print "En rango"
end

if not activo or pausado
    Print "Detenido"
end
```

### String Concatenation

```
saludo = "Hola " + nombre + "!"
Print saludo
```

### Interpolation

Any expression can go inside `#{...}`: a variable, a call, a calculation, a field, an element...

```
Print "Hola #{nombre}, tienes #{puntos * 10} puntos"
Print "#{p.x},#{p.y} de #{lista.length} (#{doble(n)})"
Print "#{a}#{b}"            # always a string: with a = 1 and b = 2 gives "12"
Print "#{str_upper(\"ok\")}"   # quotes inside are escaped: \"
```

The result is always a string, even if there is only a number (`"#{n}"`). A `#{` without its `}` is left as is.

### String functions

They return new strings (the original does not change) or numbers. Positions start at 0.

| Function | What it does |
|---|---|
| `s.length`, `s[i]` | Length and character at position `i` (`""`/0 outside the string) |
| `str_code(s, i)`, `Int(s[i])` | Character code (0-255, Latin-1) |
| `str_char(codigo)` | One-character string with that code |
| `str_find(s, sub)`, `str_find_from(s, sub, desde)` | Position of `sub`, or -1 |
| `str_starts(s, prefijo)`, `str_ends(s, sufijo)` | Starts / ends with |
| `str_lower(s)`, `str_upper(s)` | Lowercase / uppercase (also `Ñ`, `É`...) |
| `str_trim(s)` | Without spaces, tabs or line breaks at either end |
| `Int(s)`, `str_to_int(s, base)` | Number written in the string (`Int("42")`, `str_to_int("ff", 16)`) |
| `str_from_int(n, base)` | Number written in another base (`str_from_int(255, 16)` = `"ff"`) |
| `str_replace(s, de, a)` | Replaces every occurrence of `de` with `a` |
| `str_contains(s, sub)` | Whether `sub` is in `s` (`""` is in all of them) |
| `str_split(s, sep)` | The pieces between each `sep`, in a new `[String]` list; with `sep` `""` or if it is not there, `[s]`; two `sep` in a row give `""` |
| `file_read_text(nombre)` | The whole file as a string (`nil` if it cannot be read) |
| `file_write_text(nombre, texto)` | Writes the string as the whole file (`true` if it went well) |
| `str_from_buffer(buffer, desde, n)` | String with `n` bytes from a buffer |
| `str_to_buffer(s, buffer, desde)` | Copies the bytes of the string to the buffer; returns how many |

A string ends at the first 0 byte, so when reading files or buffers 0 bytes are
turned into spaces. For binary data, use buffers (`buffer_get_byte`...).

Walking through a long string by position is fast: the length of long strings is
remembered, so `while i < s.length` with `s[i]` does not measure it on every iteration.

```
linea = str_trim(linea)
if str_starts(linea, "#")
    continue
end
p = str_find(linea, "=")
clave = str_lower(linea[:p])
valor = Int(linea[p + 1:])
```

### Operator Precedence

From strongest to weakest:

1. `-` and `~` (unary)
2. `*`, `/`, `%`
3. `+`, `-`
4. `<<`, `>>`
5. `&`
6. `^`
7. `|`
8. `==`, `!=`, `<`, `>`, `<=`, `>=`
9. `not` (as in Python: `not a == b` is `not (a == b)`)
10. `and`
11. `or`

---

## 6. Control Structures

### If / Else

```
if condicion
    # code if true
end

if edad >= 18
    Print "Adulto"
else
    Print "Menor"
end
```

### If / Elif / Else

With `elif` conditions are chained without nesting; each one is tested in order and only the
first one that holds is executed (or the `else`, if none does):

```
if puntos >= 1000
    Print "Experto"
elif puntos >= 500
    Print "Intermedio"
else
    Print "Principiante"
end
```

It is the same as nesting an `if` inside the `else` (and it generates the same C).

### While

```
contador = 10
while contador > 0
    Print contador
    contador = contador - 1
end
Print "Despegue!"
```

### For with a Range

Iterates from `inicio` (start) to `fin` (end), both included:

```
# Prints 1, 2, 3, 4, 5
for i in (1..5)
    Print i
end

# Backwards: 5, 4, 3, 2, 1 (both limits are constants and start > end)
for i in (5..1)
    Print i
end

# With a step: 0, 5, 10 / 10, 7, 4, 1
for i in (0..10 step 5)
    Print i
end
for i in (10..1 step -3)
    Print i
end

# Countdown using a variable: with variable limits the range
# always goes up ((1..0) does not loop), so step -1 is needed
for i in (n..1 step -1)
    Print i
end
```

`step` cannot be 0. If it is a variable, its sign decides at run time whether the loop goes up or down.

### For Each (Iterating over Arrays)

```
enemigos = [enemy1, enemy2, enemy3]

for enemigo in enemigos
    enemigo.mover(1, 0)
end
```

### break and continue

```
for i in (1..10)
    if i % 2 == 0
        continue        # skips the even ones
    end
    if i > 7
        break           # ends the loop
    end
    Print i
end
```

They are only valid inside a `while` or `for`. Inside any `On ...` handler of the `EventLoop`
(`On Close`, `On Key`, `On Gadget`, `On Menu`, `On Click`, `On Timer`), even if the `EventLoop` is
inside a loop, they are an error: to leave the `EventLoop` use `Stop`.

### Control Commands

| Command | Effect |
|---------|--------|
| `Stop` | Leaves the EventLoop and ends the program |
| `Wait n` | Waits `n` seconds (`Wait 2`; `n` can be an expression) |
| `break` | Leaves the innermost `while`/`for` |
| `continue` | Jumps to the next iteration of the innermost `while`/`for` |
| `return valor` | Returns from a function with a value |
| `return` | Returns from a function without a value |

---

## 7. Functions

### Basic Definition

```
func saludar()
    Print "Hola!"
end

func duplicar(n)
    return n * 2
end
```

### With Type Annotations

```
func sumar(a: Int, b: Int) -> Int
    return a + b
end

func crear_mensaje(nombre: String) -> String
    return "Bienvenido " + nombre
end

func siguientes(a: Array) -> Array     # list of integers
    return [a[0] + 1, a[1] + 1]
end
```

Types that can be written: `Int`, `Float`, `Fixed`, `String`, `Bool`, `Array`, `Pointer`, `Func`, `Void`,
lists `[T]`, dictionaries `{String: T}` or `{Int: T}` and the name of a struct or an enum. Any other name is an error (it used to be taken as `Int` silently).
An `Array` field of a struct is freed with the struct, just like a field of struct type.

The `return` is checked against the declared type: it is an error to return a string where a number or a
`Bool` is expected (and vice versa), a struct of another type, `nil` in an `Int`, `Float`, `Fixed` or `Bool` function, or a
value in a `Void` function. An integer is valid for `Bool` and for `Fixed` (it is converted).

### Calling Functions

```
saludar()
resultado = duplicar(21)
suma = sumar(10, 20)
```

### Recursive Functions

```
func factorial(n)
    if n <= 1
        return 1
    end
    return n * factorial(n - 1)
end
```

### Functions as values and lambdas

A function can be passed to another one by its name. The parameter that receives it is declared `Func` and is
called like a function. A lambda is a function without a name: `fn(x) -> expression`, or with several
lines, `fn(x) ... end` with its `return`.

```
func doble(x: Int) -> Int
    return x * 2
end

func aplicar(f: Func, v: Int) -> Int
    return f(v)
end

Main
    Print aplicar(doble, 5)              # 10
    Print aplicar(fn(x) -> x + 1, 9)     # 10
    triple = fn(x) -> x * 3
    Print triple(2)                      # 6
    g = doble                            # a named function, in a variable
    Print g(4)                           # 8
    cuadrado = fn(x)
        y = x * x
        return y
    end
    Print cuadrado(3)                    # 9
end
```

A lambda does not capture variables: it only sees its parameters, the globals, the constants and the functions.
Using a local variable from outside is an error (`lambdas cannot use local variables from outside`); it has
to be passed as a parameter. A named function is stored in a variable without parentheses: `g = doble`,
`var g: Func = doble` or a global `var g: Func = doble`; then `g(4)` calls it.

---

## 8. Structures (Structs)

### Definition

```
struct Enemigo
    x: Int
    y: Int
    vida: Int = 100     # Default value
    nombre: String
end
```

### Creating Instances

```
# Constructor: the fields in order
e1 = Enemigo(100, 50, 100, "Alien")

# Field access
Print e1.x
Print e1.nombre
e1.vida = e1.vida - 10
```

The last fields can be left out if they have a default value: they take that value. The others are
mandatory (`Struct 'X' expects 1-2 arguments`):

```
struct Bala
    x: Int
    y: Int = 0
    velocidad: Int = 4
end

b1 = Bala(10)            # y = 0, velocidad = 4
b2 = Bala(10, 20)        # velocidad = 4
b3 = Bala(10, 20, 8)
```

### Structs inside structs

A field can be of another struct type. It is read and assigned by chaining dots:

```
struct Punto
    x: Int
    y: Int
end

struct Sprite
    pos: Punto
end

s = Sprite(Punto(10, 20))
s.pos.x = 15            # also self.pos.x inside a method
Print s.pos.x

var lista: [Punto] = [Punto(1, 2), Punto(3, 4)]
lista[0].x = 5          # the field of a list element (also caja.items[i].nombre)
lista[0].mover(1)       # and its methods; d["k"].push(x) in a {String: [T]}
```

To assign `a.b.c` the compiler has to know that `a.b` is a struct: the variable
must come from a constructor (`Sprite(...)`), from a function with a struct return type,
or be a typed parameter (`func f(s: Sprite)`). Otherwise it is an error.
Assigning a field the struct does not have is also an error.

### Methods

```
struct Jugador
    x: Int = 0
    y: Int = 0
    velocidad: Int = 5

    func mover(dx, dy)
        self.x = self.x + dx * self.velocidad
        self.y = self.y + dy * self.velocidad
    end

    func dibujar()
        gfx_rect(self.x, self.y, self.x + 16, self.y + 16)
    end

    func reset()
        self.x = 160
        self.y = 100
    end
end

Main
    player = Jugador(160, 100, 5)
    player.mover(1, 0)      # Moves right
    player.dibujar()
end
```

---

## 9. Enumerations

### Definition

```
enum Estado
    MENU
    JUGANDO
    PAUSADO
    GAME_OVER
end

enum Direccion
    ARRIBA = 0
    ABAJO = 1
    IZQUIERDA = 2
    DERECHA = 3
end

enum Resultado
    ERROR = -1      # negative and hexadecimal (0xFF) values allowed
    OK              # keeps counting: 0
end
```

Without `=`, each value is the previous one + 1 (the first one, 0).

Also on one line, separated by commas: `enum Estado IDLE, RUN, STOP end`.

### Usage

```
estado_actual = Estado.MENU

if estado_actual == Estado.JUGANDO
    actualizar_juego()
end

direccion = Direccion.ARRIBA
```

---

## 10. Arrays

### Creation

```
numeros = [1, 2, 3, 4, 5]
nombres = ["Ana", "Bob", "Carlos"]
vacio = []
```

### Access and Modification

```
primero = numeros[0]      # Access (index 0)
numeros[2] = 100          # Modification
```

### Properties

```
longitud = numeros.length
```

### Slicing

```
arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

sub1 = arr[2:5]     # [2, 3, 4]
sub2 = arr[:3]      # [0, 1, 2]
sub3 = arr[7:]      # [7, 8, 9]
```

### Iteration

```
for num in numeros
    Print num
end
```

### Joining lists

`a + b` creates a new list with the elements of both (the originals do not change). It works for
lists of integers, strings, structs and lists; the new one has the type of the first one that
has one (`[] + enemigos` is a list of `Enemigo`).

```
numeros = numeros + [6, 7]
todos = enemigos + [Enemigo(90, 3)]
```

Adding lists of different types (`[1] + ["a"]`) or a list and something else (`lista + 3`) is an error.
Each addition copies the whole list: to add items one at a time, use `push`.

### Growing lists

| Method | What it does |
|---|---|
| `l.push(x)` | Appends `x` at the end |
| `l.insert(i, x)` | Inserts `x` at position `i` (0 to `l.length`); the ones after it move along |
| `l.pop()` | Removes and returns the last one |
| `l.remove(i)` | Removes the one at position `i` |
| `l.clear()` | Leaves the list empty |
| `l.sort(f)` | Sorts it with the function `f(a, b)`, keeping the order of equal ones |

They also work through fields (`nodo.hijos.push(h)`, `self.lista.clear()`). When it fills up,
the list moves to a block twice the size: adding 20,000 elements one at a time takes less than
half a second on an A1200. The list owns its strings and structs: `remove` and `clear`
release them, and `pop` hands them over to whoever receives it. Putting in something of another type (`l.push(5)` in a
`[String]`) is an error.

`l.sort(f)` sorts the list (merge sort, stable: equal ones stay as they were). `f` gets two elements and
returns `Bool` (`true` if `a` goes before `b`) or `Int` (negative if `a` goes before, 0 if they are equal,
positive if after). It can be a function of the program, a lambda or a `Func` variable (that one returning
`Int`). Sorting 1,000 integers takes about 0.36 s on an A1200; 1,000 `Double`s, about 1.3 s without an FPU.

```
func por_nota(a: Fila, b: Fila) -> Int
    return a.nota - b.nota
end
filas.sort(por_nota)
numeros.sort(fn(a, b) -> a < b)
```

```
var pila: [String] = []
pila.push("a")
pila.push("b")
Print pila.pop()             # b
```

### Lists of structs and of lists

A list whose literal holds only structs of the same type, only strings or only lists knows
what it holds: its elements are read with their type and the list owns them.

```
enemigos = [Enemigo(0, 10), Enemigo(50, 10)]
enemigos[1] = Enemigo(80, 5)     # the previous Enemigo is freed
e = enemigos[0]                  # e is an Enemigo
Print enemigos[1].vida
for x in enemigos
    Print x.x
end
filas = [[1, 2], [3, 4]]
Print filas[1][0]
```

### Dictionaries

A dictionary stores values by string key. Its type is `{String: T}`:

```
edades = {"Ana": 30, "Bob": 25}
edades["Eva"] = 41             # adds or changes
Print edades["Ana"]            # 30; a key that is not there gives 0 (nil for strings and structs)
Print edades.get("Zoe", -1)    # -1: the value, or the default if it is not there (a single lookup)
if edades.has("Bob")
    edades.remove("Bob")
end
Print edades.length            # 2
for nombre in edades.keys()    # list of the keys (in any order)
    Print nombre
end

var cabeceras: {String: String} = {}
cabeceras["Host"] = "ejemplo.org"
```

With integer keys, `{Int: T}`: the same, and `keys()` gives a list of `Int`. A key of another type is a
compile error.

```
styles = {0: "normal", 7: "title"}
var cells: {Int: Cell} = {}
cells[row * 1024 + column] = Cell(...)
```

Values can be `Int`, `Bool`, `String`, structs, lists or other dictionaries
(`{String: {String: T}}`), and the dictionary owns them just like a list; there are also
lists of dictionaries (`[{String: T}]`). A variable that takes one of them (`x = d[k]`, `y = l[0]`)
is a dictionary of its type, without declaring it with `var`. `for k in d.keys()` does not create the list of keys if the
body does not change that dictionary. `d.clear()` empties it. It can also be written through fields
(`hoja.reglas["color"] = "red"`). Looking up, adding and removing cost the same with 10 keys
as with 10,000 (hash table).

`d.get(clave, defecto)` looks up once: `if d.has(k)` followed by `d[k]` looks up twice. The default has the type
of the values (`""` in a `{String: String}`); in a dictionary of structs, lists or dictionaries it can only
be `nil`. The result is used like that of `d[k]`.

### nil

`nil` means "no struct, list, dictionary or string". A variable that starts out empty needs its type:

```
struct Nodo
    valor: Int
    siguiente: Nodo
end

var lista: Nodo = nil            # empty linked list
for i in (1..10)
    lista = Nodo(i, lista)
end
n = lista
while n != nil
    Print n.valor
    n = n.siguiente
end
nave = Nave("x", nil)            # "no target" field
if buscar(lista, 3) == nil
    Print "no esta"
end
```

- `x = nil` releases what `x` held; `x == nil` and `x != nil` compare the pointer (also for strings).
- Only for structs, lists, dictionaries and `String`: `n = nil` with an integer is an error, and so is `x = nil` without
  `var x: Tipo`.
- Reading or writing a field of `nil`, or calling a method of `nil`, stops the program with
  `Error: campo de nil (en prog.dash:12)` and return code 20 (see "Runtime errors"). Without the check,
  reading would return garbage from low memory and writing would go to address 0 and hang the Amiga. With
  `--memcheck` it warns (`memcheck: ERROR campo de nil`) and carries on.

### List types: `[T]`

`[T]` is a list of `T`: `[Int]`, `[String]`, `[Enemigo]`, `[[Int]]`. With that type, the list
keeps the type of its elements when it goes through a global variable, a parameter, the return value of a
function or a struct field:

```
var NOMBRES: [String] = ["Ana", "Bob"]

struct Nodo
    nombre: String
    hijos: [Nodo]
end

func nombres_de(n: Nodo) -> [String]
    r = [n.nombre]
    for h in n.hijos             # for walks any list: variable, field, call or literal
        r = r + [h.nombre]
    end
    return r
end
```

`Array` is still an untyped list (its elements are read as integers).

---

## 11. Screens

Screens on the Amiga are independent drawing surfaces that can have their own resolution, color depth and palette. Dash provides functions to create screens that clone the Workbench or custom screens.

### Cloning the Workbench

The `screen_open()` function clones the Workbench display mode, including resolution, video mode and system pens:

```
# Open a screen cloning the Workbench with 16 colors (4 bitplanes)
screen_open(4, "Mi Aplicacion")

# With 32 colors (5 bitplanes)
screen_open(5, "Juego 32 colores")
```

This function:
- Locks the Workbench to read its properties
- Gets the ModeID of the ViewPort
- Copies the DrawInfo pens for visual consistency
- Creates a screen with the same display mode

### Custom Screen

For screens with specific dimensions, use `screen_open_custom()`:

```
# 320x256 screen with 32 colors
screen_open_custom(320, 256, 5, "Juego Retro")

# 640x480 screen with 256 colors (for RTG)
screen_open_custom(640, 480, 8, "Aplicacion HiRes")

# 1280x720 screen for modern monitors
screen_open_custom(1280, 720, 8, "App Moderna")
```

This function uses `BestModeID()` to find the best display mode that supports the requested dimensions. If it does not find a specific one, it falls back to the Workbench mode.

### Closing the Screen

```
screen_close()
```

Closes the open screen and frees its resources.

### Complete Example

```
Window MiVentana
    title "Demo Screen"
    width 300
    height 200
    left 10
    top 20
end

Main
    # Open a screen cloning the Workbench
    screen_open(4, "Demo Dash")

    # Open the window on the screen
    MiVentana.open

    # Set up a custom palette
    gfx_rgb(0, 0, 0, 8)      # Dark blue background
    gfx_rgb(1, 15, 15, 15)   # White
    gfx_rgb(2, 15, 0, 0)     # Red
    gfx_rgb(3, 0, 15, 0)     # Green

    # Draw
    gfx_pen(1)
    gfx_text_at(50, 100, "Hola desde Dash!")

    # Wait for a key
    key_wait()

    # Close everything
    close_window()
    screen_close()
end
```

### Screen Functions

| Function | Description |
|---------|-------------|
| `screen_open(depth, title)` | Clones the Workbench with the given depth |
| `screen_open_custom(w, h, depth, title)` | Screen with custom dimensions |
| `screen_close()` | Closes the current screen |

### Important Notes

- Windows opened after `screen_open()` automatically open on that screen
- The depth determines the number of colors: 4=16, 5=32, 6=64, 8=256
- On RTG systems, `screen_open_custom()` can use non-native resolutions
- Always close the screen when you are done to free resources

---

## 12. Windows and Events

### Window Definition

```
Window MiVentana
    title "Mi Aplicacion"
    width 400
    height 300
    left 50
    top 50
    closegadget true
    dragbar true
    depthgadget true
    sizegadget false
end
```

### Window Properties

| Property | Description | Type |
|-----------|-------------|------|
| `title` | Window title | String |
| `width` | Width in pixels | Int |
| `height` | Height in pixels | Int |
| `left` | Initial X position | Int |
| `top` | Initial Y position | Int |
| `closegadget` | Close button | Bool |
| `dragbar` | Drag bar | Bool |
| `depthgadget` | Depth gadget | Bool |
| `sizegadget` | Allows resizing (default `false`) | Bool |
| `borderless` | No borders (default `false`) | Bool |
| `activate` | Activates the window when it opens (default `true`) | Bool |

`closegadget`, `dragbar` and `depthgadget` are `true` by default. An unknown
property or one with a value of the wrong type (`closegadget 1`) is an error.

`MiVentana.width`, `.height`, `.left`, `.top` and `.title` can be read: with the window
open they give the current value (after resizing or moving it); otherwise, the one in the definition.
`.inner_left`, `.inner_top`, `.inner_width` and `.inner_height` give the area inside the
borders (where drawing happens): only with the window open (when closed they are 0). Dash windows
already draw inside the borders (GimmeZeroZero), so `inner_left` and `inner_top` are 0.

### Opening and Closing

```
MiVentana.open      # Opens the window
MiVentana.close     # Closes the window (inside its EventLoop, it also ends it)
```

### Windows by number

To open windows from code, without declaring them with `Window`:

```
a = window_create("Herramientas", 10, 20, 200, 100, 0)   # returns 1..16 (0 if it fails)
window_move(a, 100, 30)         # absolute position
window_resize(a, 300, 150)
window_title(a, "Nuevo titulo")
window_to_front(a)              # also window_to_back, window_activate
window_close(a)
```

- `flags`: 1 = resizable, 2 = borderless, 4 = no close button, 8 = width and height are the
  interior, without the borders (they are added together).
- To make it fit with any font: `screen_font_height()` and `screen_font_text_width(texto)` measure with the
  screen font (the program's or the Workbench's), which is the one used by title bars and
  GadTools gadgets. With the window open, `window_border_top()`, `window_border_bottom()`,
  `window_border_left()` and `window_border_right()` give its borders. Gadgets count from the interior (the
  corner inside the borders), so with flag 8 it is enough to measure them:

```
alto = screen_font_height() + 6                  # a button with the screen font
v = window_create("Prefs", 40, 30, 300, 4 * alto + 20, 8)    # exactly the interior
y = 4                                            # the first row of gadgets, already inside
```
- The created window becomes the current one: the `gfx_*` functions draw in it. Number 0 is the current window.
- A number that is not an open window does nothing. Those still open are closed on exit.
- Minimum size 40x20 (Intuition 3.1 hangs with a 0x0 window).
- An `EventLoop` also handles these windows: their gadgets arrive at `On Gadget` and their close button at
  `On Close`. `event_window()` tells which one the event came from (its number; 0 = the `EventLoop` window):

```
EventLoop
    On Close
        if event_window() == a
            window_close(a)     # only that window
        else
            Stop
        end
    end
end
```

The `gt_*` functions are single-window; for programs with many windows, use gadgets by number, ReAction
(up to 4 windows, see `ra_window_use`) or MUI.

### Event Loop

```
Main
    MiVentana.open

    EventLoop
        On Close
            Print "Cerrando..."
            Stop
        end
    end
end
```

### Complete Example

```
Window GameWindow
    title "Space Game"
    width 320
    height 256
end

Main
    Print "Iniciando juego..."
    GameWindow.open

    # Draw initial content
    gfx_pen(1)
    gfx_text_at(100, 128, "Pulsa para jugar")

    EventLoop
        On Close
            Stop
        end
    end

    Print "Juego terminado"
end
```

---

## 13. Graphics

### Color Setup

```
gfx_pen(color)                  # Drawing color (0-31)
gfx_pen_bg(color)               # Background color
gfx_pen_outline(color)          # Outline color

# Define RGB colors (0-15 per component)
gfx_rgb(0, 0, 0, 0)             # Color 0 = Black
gfx_rgb(1, 15, 15, 15)          # Color 1 = White
gfx_rgb(2, 15, 0, 0)            # Color 2 = Red
gfx_rgb(3, 0, 15, 0)            # Color 3 = Green
gfx_rgb(4, 0, 0, 15)            # Color 4 = Blue
```

### Basic Primitives

```
# Pixel
gfx_pixel(x, y)
color = gfx_pixel_read(x, y)

# Lines
gfx_move(x, y)                  # Move cursor
gfx_draw(x, y)                  # Line to point
gfx_line(x1, y1, x2, y2)        # Direct line

# Rectangles
gfx_rect(x1, y1, x2, y2)        # Filled rectangle
gfx_box(x1, y1, x2, y2)         # Rectangle outline

# Circles and Ellipses
gfx_circle(cx, cy, radio)              # Circle outline
gfx_circle_fill(cx, cy, radio)         # Filled circle
gfx_ellipse(cx, cy, rx, ry)            # Ellipse outline
gfx_ellipse_fill(cx, cy, rx, ry)       # Filled ellipse
```

### Polygons

```
gfx_pen(3)
gfx_poly_begin(100, 50)         # First vertex
gfx_poly_add(150, 100)          # Second vertex
gfx_poly_add(50, 100)           # Third vertex
gfx_poly_end()                  # Closes and fills
```

Fills (circle, ellipse and polygon, up to 100 vertices) work on any RastPort: in an
MUI drawing area or a window without its buffers, Dash lends its own for the duration of the fill.

### Text

```
gfx_text_at(x, y, "Texto")      # Text at position
gfx_text("Mas texto")           # Text at cursor
ancho = gfx_text_len("Hola")    # Width in pixels
```

### Fonts and RGB colors

```
f = font_open("helvetica.font", 13)    # 0 if it does not exist (the ROM topaz 8 is always there)
                                       # (a size below 2 requests 2: 1 and 0 make the 3.2 diskfont trash memory)
font_use(f)                            # text drawn afterwards uses this font
font_style(2)                          # 0 normal, +1 underlined, +2 bold, +4 italic
ancho = font_text_width("Hola")        # with the current font and style
alto = font_height()                   # and font_baseline(): from the top to the baseline
rojo = color_pen(255, 0, 0)            # the closest pen on the screen being drawn on
gfx_pen(rojo)
```

`font_size(f)` tells the size the system gave (the closest one it has). `font_close(f)` closes a
font before exiting (if it is the one in use, first set another one with `font_use`). With no window open (or with
MUI, outside the drawing area) `font_use`, `font_style` and the measurements work on a RastPort of
Dash's own: text can be laid out before painting it. Disk
fonts need `diskfont.library` and the font in `FONTS:`. Open fonts and pens
are given back on exit.

### Transparency and gradients

```
gfx_blend_rect(0, 80, 199, 99, 0x000000, 128)        # half black over what is already there (alpha 0-255)
gfx_gradient_rect(0, 40, 199, 99, 0x000000, 0, 0x000000, 230, true)   # darkens downwards
gfx_gradient_rect(0, 0, 99, 9, 0xFF0000, 255, 0xFFFF00, 255, false)   # from red to yellow, horizontally
c = gfx_pixel_rgb(10, 10)                             # color of a pixel as 0xRRGGBB
```

On a true-color screen (15, 16, 24 or 32-bit RTG) each pixel is really blended with
what was there: it is read and written in blocks of rows (`Picasso96API.library`, or `cybergraphics.library`
if that is not present), about 20 ms for 400x300 on a 68040; with alpha 255 nothing is read. On a
palette screen (AGA, ECS, 8-bit RTG) there is no blending: the color is drawn with the closest pen and
a 4x4 ordered dither (alpha 128 paints half the pixels, 0 none, 255 all of them), with the
blitter. Whatever falls outside the window is not painted. In a gradient each row (or column) has its own
color and alpha; with few colors in the palette, the intermediate ones come from the closest pen.

### RGB images from a buffer (video)

```
buf = buffer_alloc(640 * 360 * 3)                   # RGB24: 3 bytes per pixel, rows one after another
gfx_rgb_draw(buf, 640, 360, 0, 0)                   # as is at 0, 0
gfx_rgb_draw_scaled(buf, 640, 360, 0, 0, 1024, 576) # scaled (nearest pixel)
```

On RTG it uses `WritePixelArray` from `cybergraphics.library` or `p96WritePixelArray` from Picasso96: without
scaling, a single call; scaled, each source row is scaled once and written for all
the destination rows it covers. On an emulated 68040 with uaegfx at 16 bits: 640x360 in about 10 ms and at
1024x576 in about 43 ms. On a palette screen each color takes the closest pen (3 bits per
channel) with `WriteChunkyPixels`, without aiming for speed. Whatever falls outside the window is not painted.

### Images (datatypes)

```
img = image_load("logo.png")           # 0 if it cannot be read
ancho = image_width(img)               # and image_height(img)
image_draw(img, 10, 20)                # whole at 10, 20
image_draw_part(img, 0, 8, 10, 20, 32, 16)   # the 32x16 piece starting at 0, 8
peq = image_scale(img, 64, 48)         # a copy at another size (another image)
image_free(peq)                        # any left are freed on exit
```

It reads any format with a datatype on the system: ILBM always; PNG, GIF, JPEG and BMP from
3.2 or with their datatypes installed. Colors are adapted to the screen of the current window
(open the window before loading; without a window, the default public screen). Transparent
pixels are not painted when the datatype provides the mask (transparent GIF on 3.2) or an
alpha channel that is not all 0; the 3.2 `png.datatype` does not provide it, so a PNG with alpha comes out
with a background.

A program that decodes its own images (like dashweb, with its own JPEG and
PNG decoders) passes them to the screen with `image_from_rgb(buffer, ancho, alto, alfa)`: rows of RGB pixels
(3 bytes) or, with `alfa`, RGBA (4 bytes). It uses the V43 `picture.datatype`
(AmigaOS 3.5 and later) to adapt the colors to the screen, as with a file; on a stock 3.1
it returns 0. On a graphics card screen (15 to 32-bit RTG, with Picasso96 or CyberGraphX)
it does not use the datatype: it writes the pixels into a bitmap like the screen's, about 20 times
faster (5 ms for 400x300 on a 68040). The image is used like those from `image_load`.

The alpha of `image_from_rgb`: on a palette screen (AGA, ECS, 8-bit RTG) pixels with alpha of 128 or
more are painted and the rest are not. On 15 to 32-bit RTG it is blended with what is underneath (alpha 64: one quarter
of the image and three of what is underneath), also in `image_draw_part` and in the copies from `image_scale`.
It is slower than painting without blending: it reads and writes what is underneath. If the alphas are only 0 and 255, it
is painted with the mask, without reading anything.

### Screen

```
gfx_clear()                     # Clear with color 0
gfx_clear_color(color)          # Clear with a color
gfx_scroll(dx, dy, x1, y1, x2, y2)  # Scroll a region
gfx_copy(sx, sy, ancho, alto, dx, dy)   # Copies a piece of the window to another place in it
```

### More drawing functions

| Function | What it does |
|---|---|
| `gfx_rgb8(color, r, g, b)` | Like `gfx_rgb`, with components from 0 to 255 (AGA and RTG); needs an open window |
| `gfx_mode(modo)` | Drawing mode: 0 pen only (JAM1), 1 pen and background (JAM2), 2 inverts what is there (COMPLEMENT), 4 inverse text (INVERSVID) |
| `gfx_pattern(patron)` | 16-bit pattern for lines: `0xFFFF` solid, `0xF0F0` dashed |
| `gfx_flood(x, y, modo)` | Fills from `x, y` with the pen: mode 0 up to the color of `gfx_pen_outline`, mode 1 the area of the same color as that point |

### Off-screen bitmaps

Up to 32 bitmaps (numbers 0..31) in Chip memory, to prepare images and copy them:

```
bitmap_create(0, 64, 32, 4)          # id, width, height, planes (colors = 2^planes)
bitmap_draw_to(0)                    # gfx_* draws into the bitmap...
gfx_pen(3)
gfx_circle_fill(16, 16, 10)
bitmap_draw_screen()                 # ...and goes back to the window
bitmap_blit(0, 0, 0, 64, 32, 10, 10) # id, source x/y, width, height, destination x/y

bitmap_create(1, 64, 32, 1)          # mask: 1 plane, same width
bitmap_blit_mask(0, 1, 0, 0, 64, 32, 80, 10)   # only where the mask has 1

if bitmap_load(2, "Work:fondo.iff")  # IFF ILBM (ByteRun1 or uncompressed)
    bitmap_blit(2, 0, 0, 320, 200, 0, 0)
end
bitmap_save(0, "RAM:dibujo.iff")
bitmap_free(0)
```

`bitmap_load` on a screen of your own (`screen_open`) also sets the colors of the image;
on the Workbench it is drawn with the Workbench colors. Bitmaps are freed on exit.

### Bobs

A bob is a bitmap that moves over the screen, saving what it covers. As its image it uses
the bitmap with the same number (0..31): it is painted with `bitmap_draw_to` or loaded from an IFF.
Color 0 is transparent.

```
bob_create(0, 16, 16, 4)            # or bob_load(0, "Work:nave.iff")
bitmap_draw_to(0)
gfx_pen(5)
gfx_circle_fill(8, 8, 6)
bitmap_draw_screen()

bob_pos(0, x, y)
bob_draw(0)                         # saves the background and draws (if it was already there, erases it first)
bob_erase(0)                        # restores the background
if bob_collision(0, 1)              # pixel by pixel
    Print "choque"
end
bob_frame(0, 2)                     # a strip of squares (48x16 = 3 frames of 16x16)
bob_free(0)                         # removes it from the screen and frees it
```

With several bobs that overlap: erase them in the reverse order to the one they were drawn in.

### Copper

A user copper list (the system-friendly way): it changes registers of the graphics
chip on a given line of the screen, for example colors for a gradient.

```
copper_create(32)              # maximum number of instructions
copper_wait(40, 0)             # wait for line 40 (from the top of the screen)
copper_color(0, 0xF00)         # color 0 = red (12-bit 0xRGB format)
copper_wait(80, 0)
copper_move(0x180, 0x0F0)      # any register: 0x180 is COLOR00
copper_end()
copper_install()               # on the current screen (your own or the Workbench's)
copper_free()                  # remove it (it is removed automatically on exit)
```

### Hardware sprites

The graphics chip's sprites (up to 8, numbers 0..7): 16 pixels wide and 3 colors plus
transparent. They need a chipset screen of your own (`screen_open`) (not RTG: there it warns and they are not visible).

| Function | What it does |
|---|---|
| `sprite_create(id, ancho, alto)` | Allocates a free sprite from the system (`false` if none is left). The width is always 16 |
| `sprite_set_row(id, fila, plano0, plano1)` | Sets a row: two 16-bit words; each pixel takes the color `bit0 + 2*bit1` (0 = transparent) |
| `sprite_color(id, indice, r, g, b)` | Color 0..2 of the sprite (colors 1..3), with components from 0 to 15 |
| `sprite_pos(id, x, y)`, `sprite_show(id)`, `sprite_hide(id)` | Moves, shows or hides it |
| `sprite_collision(id1, id2)` | Whether their rectangles touch |
| `sprite_free(id)` | Gives it back to the system |
| `sprite_load(id, fichero)` | Sprite from a picture (ILBM...): frames 16 pixels wide side by side, as tall as the picture; colors 0-3 of the picture are those of the sprite (0 transparent). Shows the first frame. `false` if it cannot |
| `sprite_frame(id, marco)` | Shows that frame (0 the first) of a sprite from `sprite_load` |

### Software sprites

Up to 16 (numbers 0..15). They are drawn with the blitter in the current window, saving what they cover,
so they also work on RTG. Color 0 is transparent.

| Function | What it does |
|---|---|
| `soft_sprite_create(id, ancho, alto, planos)` | Creates an empty one (`false` if it could not); an open window is needed |
| `soft_sprite_pixel(id, x, y, color)`, `soft_sprite_clear(id, color)` | Paints one pixel or the whole sprite |
| `soft_sprite_row(id, fila, plano0, plano1)` | A row in the hardware sprite format (16 pixels, 4 colors) |
| `soft_sprite_show(id)`, `soft_sprite_hide(id)` | Draws or removes it (restores the background) |
| `soft_sprite_pos(id, x, y)`, `soft_sprite_x(id)`, `soft_sprite_y(id)` | Moves it (if visible, it is redrawn) and gives its position |
| `soft_sprite_free(id)` | Frees it |

### RTG (graphics cards)

Functions from `cybergraphics.library` (CyberGraphX, or Picasso96 with its compatibility layer).
They draw in the current window or screen with `0xRRGGBB` colors. On a screen of 8 bits or less
`rtg_write_pixel` and `rtg_fill_rect` use an approximate pen, and the array ones do nothing.

| Function | What it does |
|---|---|
| `rtg_available()` | Whether `cybergraphics.library` (V41 or later) is present |
| `rtg_is_active()` | Whether the current screen is true color (more than 8 bits) |
| `rtg_get_depth()`, `rtg_get_width()`, `rtg_get_height()` | Bits per pixel and size of the current screen |
| `rtg_best_mode(ancho, alto, bits)` | The best RTG screen mode for that size |
| `rtg_open_screen(ancho, alto, bits, titulo)` | Opens an RTG screen of your own (with the best mode; `false` if there is none) |
| `rtg_write_pixel(x, y, rgb)`, `rtg_read_pixel(x, y)` | Writes or reads a pixel |
| `rtg_fill_rect(x, y, ancho, alto, rgb)` | Filled rectangle |
| `rtg_write_array(buffer, bpr, x, y, ancho, alto)` | Copies ARGB pixels (4 bytes) from a buffer; `bpr` = bytes per row |
| `rtg_read_array(buffer, bpr, x, y, ancho, alto)` | The opposite: from the screen to the buffer |
| `rtg_rgb(r, g, b)`, `rtg_argb(a, r, g, b)` | Combines components from 0 to 255 into a color |
| `rtg_rgb_r(c)`, `rtg_rgb_g(c)`, `rtg_rgb_b(c)` | Extracts each component |
| `rtg_alloc_bitmap(ancho, alto, bits)`, `rtg_free_bitmap(bm)` | Off-screen bitmap, in the window's format |
| `rtg_blit(bm, sx, sy, dx, dy, ancho, alto)` | Copies a piece of the bitmap to the window |
| `rtg_scale_blit(bm, sx, sy, sw, sh, dx, dy, dw, dh)` | The same, scaled (treats the bitmap as 8 bits per pixel; without RTG, copies without scaling) |

To paint a whole RGB image, `gfx_rgb_draw` (see above) is simpler and works on any screen.

### Graphics Example

```
Window GfxDemo
    title "Demo Graficos"
    width 320
    height 200
end

Main
    GfxDemo.open

    # Define the palette
    gfx_rgb(1, 15, 15, 15)      # White
    gfx_rgb(2, 15, 0, 0)        # Red
    gfx_rgb(3, 0, 15, 0)        # Green

    # Draw shapes
    gfx_pen(1)
    gfx_box(10, 10, 310, 190)   # Frame

    gfx_pen(2)
    gfx_circle_fill(160, 100, 40)

    gfx_pen(3)
    gfx_line(0, 100, 320, 100)

    gfx_pen(1)
    gfx_text_at(120, 180, "Demo!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

---

## 14. Input (Keyboard, Mouse, Joystick)

### Keyboard

```
# Check whether a key is available (key_pressed only looks; key_get takes it out)
while key_pressed()
    tecla = key_get()
    Print tecla
end

# Game loop: close and keys at the same time (neither eats the other's messages)
while not window_check_close()
    if key_pressed()
        tecla = key_get()
    end
    wait_vblank()
end

# Wait for a key (blocking)
tecla = key_wait()

# Raw code of the last key (EventLoop, key_get, key_wait...)
raw = key_raw()

# Text produced by a raw code with the active keymap ("a", "1"...)
texto = key_text(raw)
```

`key_get()` gives the raw code of the oldest waiting key (0 if there is none), and also
key releases: the code plus 128 (releasing Esc, 69, gives 197). To keep only the presses,
`if tecla < 128`. `key_wait()` already skips the releases.

Other input and screen functions:

| Function | What it does |
|---|---|
| `wait_key()` | Waits for a key in the window and gives its raw code (without a window, waits one second and gives 0) |
| `wait_click()` | Waits for a mouse button to be pressed and released (polls the hardware non-stop: uses CPU) |
| `check_lmb()`, `check_rmb()`, `check_mouse()` | Whether the left, the right or any button is pressed (reads the hardware) |
| `check_esc()` | Whether Esc is pressed (reads the keyboard in the hardware) |
| `screen_width()`, `screen_height()` | Size of your own screen or of the window's screen |
| `screen_to_front()`, `screen_to_back()` | Brings your own screen (`screen_open`) to the front or sends it behind the others |

### Keys in the EventLoop

```
EventLoop
    On Key "a"          # a character (according to the keymap: "a" is not "A")
        Print "a"
    end
    On Key "ESC"        # a name: SPACE BACKSPACE TAB ENTER RETURN ESC DEL HELP
        Stop            #         UP DOWN LEFT RIGHT F1..F10
    end
    On Key 0x4C         # a raw code
        Print "arriba"
    end
    On Key              # any key
        Print key_raw()
    end
    On Close
        Stop
    end
end
```

If several `On Key` match the key, all of them run, in order. Key
releases do not count. If the program uses keys, the window requests them from Intuition when it opens.

### Clicks and timer in the EventLoop

```
paso = 100
EventLoop
    On Click            # left button pressed in the window
        Print "" + click_x() + "," + click_y()   # inside the borders (where drawing happens)
    end
    On Timer paso       # every 100 ms (a number or a variable, which is read each time)
        Print "tic"
    end
    On Close
        Stop
    end
end
```

`On Timer` uses `timer.device` while the loop waits: it uses no CPU between ticks. Only one `On Timer`
per loop. It also works if the program opens windows with `window_create`.

### Mouse

```
x = mouse_x()
y = mouse_y()

# Buttons: 0 = left, 1 = right
if mouse_button(0)
    Print "Click izquierdo"
end
```

### Joystick

```
# Ports: 0 or 1
dx = joy_x(0)       # -1, 0, or 1
dy = joy_y(0)       # -1, 0, or 1

if joy_button(0)
    Print "Disparo!"
end

# Direction functions (return Bool)
if joy_up(0)
    y = y - 1
end
if joy_down(0)
    y = y + 1
end
if joy_left(0)
    x = x - 1
end
if joy_right(0)
    x = x + 1
end
if joy_fire(0)
    disparar()
end
```

---

## 15. Audio and Music

### Loading and Playing Sounds

```
# Load an IFF 8SVX sound
sound_load(0, "disparo.8svx")
sound_load(1, "explosion.8svx")

# Play on a channel (0-3)
sound_play(0, 0)        # Sound 0 on channel 0

# Play in a loop
sound_loop(1, 1)        # Sound 1 on channel 1, looping

# Stop a channel
sound_stop(0)

# Volume (0-64) and period (pitch: lower = higher) of a channel
sound_volume(0, 48)
sound_period(0, 300)

if sound_playing(0)          # still playing?
    Print "sonando"
end

# Synthesized sound: samples from -128 to 127
sound_create(2, 2000, 8000)  # id, samples, samples per second
for i in (0..1999)
    sound_sample(2, i, (i % 20) * 12 - 120)
end
sound_play(2, 0)
sound_free(2)
```

It uses `audio.device`: the four channels are allocated on the first sound and given back on
exit. Everything is asynchronous: `sound_play` and `tone_play` return immediately. Uncompressed 8SVX.

### MOD Music

```
# Load a module
music_load("intro.mod")

# Playback control
music_play()
music_pause()
music_resume()
music_stop()

# Volume (0-64)
music_volume(64)

# Position
music_position(0)       # Go to the start
Print music_pos()       # position in the pattern list
Print music_row()       # pattern row (0-63)

# Free
music_free()
```

ProTracker modules with 4 channels and 31 instruments (M.K., M!K!, FLT4, 4CHN). It plays from
a VBlank interrupt (the BPM of `Fxx` are approximated with an accumulator); effects 0, 1,
2, 3, 4, 5, 6, 9, A, B, C, D, F and E1, E2, EA, EB, EC. While the music is playing, the channels
belong to it: `music_play` stops the `sound_*` ones.

### Synthesized Tones

```
# tone_play(channel, frequency_hz, volume, duration_ms)
tone_play(0, 440, 64, 500)  # A 440 Hz, half a second (sine wave)
tone_play(1, 523, 48, 250)  # C
```

---

## 16. File System

### Opening and Closing Files

```
# Modes: 1005 = read (the file must exist), 1006 = new file (deletes any existing one),
#        1004 = read and write (creates it if it does not exist)
handle = file_open("datos.txt", 1005)

if handle != 0              # 0 if it could not be opened
    # Use the file...
    file_close(handle)
end
```

The modes are those of dos.library's `Open`. `import "lib/amiga/dos.dash"` gives them names:
`MODE_READ` (1005), `MODE_WRITE` (1006) and `MODE_READWRITE` (1004). The C names
(`MODE_OLDFILE`, `MODE_NEWFILE`...) do not exist in Dash.

### Reading

```
handle = file_open("config.txt", 1005)

while not file_eof(handle)
    byte = file_read_byte(handle)    # 0-255; -1 at the end
end

file_close(handle)
```

`file_eof` peeks at the next byte without consuming it, so the loop reads every byte. To read a whole
text file, `file_read_text(nombre)` is simpler (see [String functions](#string-functions)).

### Writing

```
handle = file_open("salida.txt", 1006)

file_write_line(handle, "Primera linea")
file_print(handle, "Texto sin salto")
file_write_byte(handle, 65)     # 'A'

file_close(handle)
```

### File Position

```
file_seek(handle, 0, -1)        # to the beginning
file_seek(handle, -10, 1)       # 10 bytes before the end
file_seek(handle, 5, 0)         # 5 bytes after the current position
pos = file_pos(handle)          # current position
```

The third parameter says where to count from, as in dos.library's `Seek`: -1 from the
beginning, 0 from the current position and 1 from the end. It returns the previous position (-1 on failure).
`lib/amiga/dos.dash` provides the constants `SEEK_START`, `SEEK_CURRENT` and `SEEK_END` (-1, 0 and 1) and the functions
`seek_start(h, pos)`, `seek_forward(h, n)`, `seek_end(h, n)` and `seek_rewind(h)`.

### Binary data and buffers

A buffer is a block of memory (a number, like a file handle), for binary data:

```
buf = buffer_alloc(1024)                    # zero-filled; 0 if out of memory
n = file_load("datos.bin", buf, 1024)      # bytes read; -1 if it does not exist or does not fit
if n > 0
    Print buffer_get_byte(buf, 0)
    buffer_set_word(buf, 2, 0x1234)        # 16 bits, big-endian (like the 68000)
    file_save("RAM:copia.bin", buf, n)
end
buffer_free(buf)
```

| Function | What it does |
|---|---|
| `buffer_alloc(n)`, `buffer_free(b)` | Allocates `n` zero-filled bytes and frees them. They are not freed automatically on exit: use `buffer_free` |
| `buffer_get_byte(b, i)`, `buffer_set_byte(b, i, v)` | One byte (0-255) at position `i` |
| `buffer_get_word(b, i)`, `buffer_set_word(b, i, v)` | 16 bits at `i` (big-endian) |
| `buffer_get_long(b, i)`, `buffer_set_long(b, i, v)` | 32 bits at `i` (big-endian) |
| `buffer_copy(dest, i_dest, origen, i_origen, n)` | Copies `n` bytes (destination first) |
| `buffer_fill(b, i, n, v)` | Sets `n` bytes to `v` starting at `i` |
| `file_read_line(h, b, max)` | Reads a line (including its newline) into the buffer, up to `max - 1` bytes; returns the text, or `nil` at the end |
| `file_read(h, b, n)`, `file_write(h, b, n)` | Reads or writes up to `n` bytes between an open file and the buffer; returns how many (-1 on failure) |
| `file_load(nombre, b, max)` | Reads the whole file into the buffer; returns the bytes, or -1 if it does not exist or is larger than `max` |
| `file_save(nombre, b, n)` | Writes `n` bytes of the buffer as a new file; returns how many |
| `console_read(b, max)` | Reads up to `max` bytes from the program's input (the console); returns how many |
| `console_write(texto)` | Writes the text to the output, without a newline |
| `str_from_buffer(b, i, n)`, `str_to_buffer(s, b, i)` | Text from or to a buffer (see [String functions](#string-functions)) |

No access checks the buffer's bounds: a position outside it writes to other memory.

### File System

```
if file_exists("config.dat")
    Print "Archivo encontrado"
end

tamano = file_size("datos.bin")

file_delete("temp.tmp")
file_rename("viejo.txt", "nuevo.txt")
file_copy("original.dat", "backup.dat")
```

### Directories

```
dir_create("saves")
dir_change("work:")         # true if it exists; on exit it goes back to the initial directory
Print dir_current()         # full name: "Work:", "Ram Disk:"...
```

---

### Network (TCP and UDP)

TCP and UDP connections with `bsdsocket.library` (requires a TCP/IP stack: Roadshow, AmiTCP, Miami...).
A socket is a number (-1 = none). The library is opened when first used and closed on exit,
along with any sockets still open.

| Function | What it does |
|---|---|
| `net_connect(host, puerto, ms)` | Connects (name or address); the socket, or -1 if it fails or `ms` elapse |
| `net_send(s, texto)`, `net_send_buffer(s, buf, n)` | Sends everything; the bytes or -1 |
| `net_recv(s, max, ms)` | Up to `max` bytes as text: `""` if nothing arrived within `ms` (-1: wait), `nil` when closed |
| `net_recv_buffer(s, buf, max, ms)` | The same into a buffer: the bytes, 0 if nothing arrived, -1 when closed |
| `net_wait(s, ms)` | Waits until there is something to read: 1 yes, 0 timed out, -1 error |
| `net_close(s)` | Closes |
| `net_resolve(host)` | IPv4 address (`"a.b.c.d"`), `nil` if not found |
| `net_error()` | What went wrong in the last call |
| `net_stack_running()` | `true` if a TCP/IP stack is running (its `bsdsocket.library` in memory); loads nothing. Roadshow's stays in memory after `NetShutdown`: that one is opened and closed to find out |
| `net_release()` | Releases the network right away: closes the library and with it any remaining sockets, TLS connections and lookups; the next `net_` call opens it again |

```
s = net_connect("ejemplo.org", 80, 10000)
if s < 0
    Print "Error: " + net_error()
else
    net_send(s, "GET / HTTP/1.0\r\nHost: ejemplo.org\r\n\r\n")
    trozo = net_recv(s, 4096, 10000)
    while trozo != nil
        Print trozo
        trozo = net_recv(s, 4096, 10000)
    end
    net_close(s)
end
```

**If the network goes down.** Roadshow's `NetShutdown` (also WHDLoad's when launching a game) notifies every
program that has the library open and waits for it to close it. By default the notification is Ctrl-C, which would end the
program; Dash installs its own. When it arrives, the program releases the network as with `net_release` and carries on: in
`cx_wait` and `mui_wait_event` straight away, and otherwise at the next `net_` call that opens something, which fails. A
network wait (`net_recv`, `net_wait`) ends straight away. After that, `net_` calls fail (`net_error()`
says why) until the network comes back. Ctrl-C still stops the program as always.

**Without waiting.** `net_connect` waits for the name to be resolved and for the connection to be made.
A program with windows can avoid waiting: `net_connect_start` looks up the name in another process
(the TCP/IP stack has no non-blocking DNS query) and connects without blocking;
`net_connect_poll` makes progress each time it is called (on every tick of a timer). Resolved names
are remembered (the last eight). On exit, the program waits for any lookups still
in progress.

| Function | What it does |
|---|---|
| `net_connect_start(host, puerto, ms)` | Starts and returns straight away: the socket, or -1. `ms` for the name lookup and again for connecting |
| `net_connect_poll(s)` | 1 connected, 0 not yet, -1 failed (the socket is closed; `net_error()`) |
| `net_connect_stage(s)` | 0 looking up the name, 1 connecting, 2 done |

```
s = net_connect_start("ejemplo.org", 80, 10000)
r = net_connect_poll(s)
while r == 0
    ... la interfaz sigue; r = net_connect_poll(s) en el siguiente tic
end
```

`net_close` on a socket that is still being opened leaves it unfinished. Time during which the
program calls neither `net_connect_poll` nor `tls_connect_poll` (busy with something else) does not count
towards the limit, and the TLS handshake limit starts again each time the handshake makes progress.

**Waking up on network activity.** Instead of checking every so often, the program can sleep until something happens:
`net_signal()` gives a signal that the sockets send on every event (connected, data arrives, closed,
error) and that the name lookup sends when it finishes. Call it before every wait, because each call empties the
TCP/IP stack's event queue:

```
ev = mui_wait_event_signals(net_signal())
if ev == 0
    ... mirar las conexiones: net_connect_poll, net_recv_buffer(s, buf, max, 0), tls_...
end
```

**TCP server.** `net_listen` opens a port and `net_accept` returns each incoming connection as just another
socket (`net_send`, `net_recv`, `net_close`).

| Function | What it does |
|---|---|
| `net_listen(puerto)` | Listens on that port (0: any free one): the server socket, or -1 (`net_error()`: "ese puerto está ocupado"...) |
| `net_accept(s, ms)` | The next connection, waiting at most `ms` (-1: wait, 0: just check): its socket, or -1 if none arrived |
| `net_peer(s)` | The address of the other end (`"a.b.c.d"`), `nil` if not connected |
| `net_port(s)` | A socket's own port (the one assigned by `net_listen(0)` or `net_udp_open(0)`) |

```
srv = net_listen(8080)
while not break_check()
    c = net_accept(srv, 1000)
    if c >= 0
        Print "conexión de " + net_peer(c)
        peticion = net_recv(c, 4096, 5000)
        net_send(c, "HTTP/1.0 200 OK\r\n\r\nHola desde el Amiga\n")
        net_close(c)
    end
end
net_close(srv)
```

**UDP.** Individual messages (datagrams), connectionless: each one carries its destination and arrives whole or not at all.

| Function | What it does |
|---|---|
| `net_udp_open(puerto)` | A UDP socket on that port (0: any free one); -1 on failure. Closed with `net_close` |
| `net_udp_send(s, host, puerto, texto)`, `net_udp_send_buffer(s, host, puerto, buf, n)` | Sends a datagram; the bytes or -1. `"255.255.255.255"`: to the whole local network |
| `net_udp_recv(s, max, ms)` | The next datagram as text (up to `max` bytes; the rest is lost): `""` if none arrived within `ms`, `nil` on error |
| `net_udp_recv_buffer(s, buf, max, ms)` | The same into a buffer: the bytes, 0 if none arrived, -1 on error |
| `net_udp_from()`, `net_udp_from_port()` | Who sent the last datagram received: to reply to it |

```
u = net_udp_open(5000)
m = net_udp_recv(u, 1500, 10000)
if m != nil and m != ""
    net_udp_send(u, net_udp_from(), net_udp_from_port(), "recibido: " + m)
end
net_close(u)
```

There are no raw sockets (`SOCK_RAW`): for that, use `@native` with `bsdsocket.library`. Nor is there HTTP as a builtin
(no `Http.get`): the request is written by hand over TCP or TLS, as in the examples. The network can also be used
from another process: see [The network from a task](#c-in-another-process-task_start).

If the stack does not support it (FS-UAE's `bsdsocket.library` has no `SO_EVENTMASK`), `net_signal()` returns 0 and
you have to keep polling with a timer. The time limits of `net_connect_start` are only
checked when `net_connect_poll` is called: a slow timer (one second) is advisable even when there is a signal.
Tested with Amiberry 8.2's `bsdsocket`; Roadshow and AmiTCP 4 have the same thing (`SBTC_SIGEVENTMASK`).

### TLS (HTTPS) with AmiSSL

On a socket from `net_connect`, `tls_connect` negotiates TLS with AmiSSL 5 and checks that the
server's certificate is valid and is for that name (against `AmiSSL:Certs`; an IPv4 address
such as `127.0.0.1` is checked as an address). It requires AmiSSL 5.1 or later installed (any
AmiSSL 5 will do, even though Dash is compiled with the 5.27 SDK) and a 68020 or better; the program requests 64 KB of
stack (OpenSSL needs it).
Compiling requires the SDK headers: `tools/get_amissl.sh` downloads them.

| Function | What it does |
|---|---|
| `tls_connect(socket, host)` | The TLS connection, or -1 (`net_error()` says why: certificate, name...) |
| `tls_send(t, texto)`, `tls_send_buffer(t, buf, n)` | Like `net_send` |
| `tls_recv(t, max, ms)`, `tls_recv_buffer(t, buf, max, ms)` | Like `net_recv` |
| `tls_close(t)` | Ends TLS (the socket is closed afterwards with `net_close`) |
| `tls_connect_start(socket, host, ms)` | Like `tls_connect` without waiting for the handshake: the connection or -1 |
| `tls_connect_poll(t)` | 1 negotiated (certificate checked), 0 not yet, -1 failed (`t` is freed; the socket stays open) |
| `tls_resumed(t)` | `true` if the connection resumed a previous session with the same server |

Dash stores each server's session (name and port; up to 8) once a connection has read something
or is closed (TLS 1.3 sends it after the handshake), and the next connection to that server
resumes it: the certificate is not checked again. With TLS 1.3 the key exchange is repeated
anyway (on an emulated A1200, 9 s new and 7.9 s resumed); with TLS 1.2 that is skipped too.
Connections opened at the same time before the first one reads anything have no session to resume.

```
s = net_connect("ejemplo.org", 443, 10000)
t = tls_connect(s, "ejemplo.org")
if t >= 0
    tls_send(t, "GET / HTTP/1.0\r\nHost: ejemplo.org\r\n\r\n")
    Print tls_recv(t, 4096, 10000)
    tls_close(t)
end
net_close(s)
```

## 17. Memory Management

### Strings (automatic)

Strings are freed automatically while the program runs, with no garbage collector
and no pauses:

- Each String variable (local, global or struct field) owns its text.
  Reassigning it frees the previous text; so does leaving its block or function.
- Intermediate strings (`a + b`, `"#{x}"`, what a function returns) are freed
  at the end of each iteration of a loop or of the `EventLoop`, and on leaving a function.
- A list of strings (`nombres = ["a", "b"]`) owns its strings: replacing one
  frees the previous one. A string handed to a system function that keeps it
  (a gadget label, a screen title, `@native`) is copied and stays fixed until
  the program ends.
- Cost: 12 bytes per string and a short copy when assigning a string that is not temporary.

A loop that concatenates 100,000 times uses the same memory at the end as at the start.

To build up a string, `s = s + algo` (or `s = s + a + b`) on a variable appends to the
end of the text it already holds, without copying it all: it leaves plenty of spare room and, when it does not fit,
moves it to a block twice the size. Building a 20,000-character string one character at a time
takes less than a second on an A1200 (previously, minutes). This does not happen if another part of the sum reads
the same variable (`s = s + s` makes a new copy), nor with struct fields.

Copies of long strings. Assigning a string to a variable copies it (`s = t.texto` duplicates the
whole text). Passing a String field to a function (`f(t.texto)`) also copies it, because the
function could change that field and free the text, unless no code in the program assigns
that field of that struct (only the constructor sets it) and `t` is a local variable or a
parameter: then it is passed as is. To walk through a long string stored in a struct, pass it
as a parameter (`func trocear(t: Lector, s: String)` called with `trocear(t, t.texto)`) instead
of copying it to a variable on each call. The length of strings of 64 characters or more is
remembered (a cache of 8), so `s.length`, `s[i]` and `s[a:b]` do not walk the whole string.

### Arrays and structs (automatic, reference counting)

Several variables can share the same array or struct, so each one carries a
count of who is using it (a 16-byte header). It goes up when assigned to a variable,
to a field or when returned, and goes down when that variable is reassigned or its block
ends. When it reaches 0 it is freed, along with its Strings and its structs.

```
struct Objeto
    valor: Int
end

Main
    obj = Objeto(42)        # refcount(obj) = 1
    otro = obj              # 2: they share the same struct
    otro.valor = 7          # obj.valor is now 7 too
    otro = Objeto(1)        # obj goes back to 1
end
```

- A new array or struct that nobody stores (`suma([1, 2])`) is freed at the end of the
  loop iteration, like temporary strings.
- A list of structs or of lists (see "Lists of structs and of lists") counts as one
  reference to each element: replacing one, or freeing the list, releases them.
  A struct stored in a list of integers or a mixed list, or handed to C code
  (`@native`, `@extern`), stays fixed until the program ends.
- A struct that reaches a function from a field, a global or a list element
  is retained until the end of the iteration: the function can replace that field without
  the struct it is using being freed.
- Freeing a long linked list (thousands of structs each pointing to the next) uses no stack.
- Cycles: if a struct points to another that points back to the first, they are not freed until exit.
  `--memcheck` shows them as live on exit.
- `refcount(x)`, `retain(x)` and `release(x)` still exist for advanced cases; one
  `release` too many frees something a variable is still using.

### `weak` fields (no cycles)

Reference counting does not free cycles: a node that points to its parent, and the parent to its
children, would stay alive until exit. A field marked `weak` points without retaining:

```
struct Nodo
    nombre: String
    hijos: [Nodo]          # the parent retains its children
    weak padre: Nodo       # the child only points to its parent
end
```

When nobody retains the root, the whole tree is freed. The object in a `weak` field must
outlive whoever points to it (a parent outlives its children). Otherwise, the field points to something
freed: with `--memcheck`, reading it gives the error `campo weak de un objeto ya liberado` (and `nil`).
It only works for fields of structs, lists or dictionaries.

### When each thing is freed

| What | Freed |
|-----|-----------|
| String variable, array or struct of a block or function | When reassigned or on leaving the block (also with `break`, `continue`, `return`) |
| String, struct or `Array` field of a struct | When the field is reassigned or the struct is freed |
| Element of a list of strings, structs or lists | When replaced or when the list is freed |
| Intermediate value (`a + b`, `Punto(1, 2)` passed to a function, `[1, 2]` with no variable) | At the end of the loop or `EventLoop` iteration, or on leaving the function |
| What a function returns | Becomes an intermediate value of the caller (or of the variable that receives it) |
| Global variable | When reassigned; otherwise, when the program ends |
| Struct in a list of integers or a mixed list, or handed to `@native`/`@extern`; string handed to the system | When the program ends |
| Struct cycles | When the program ends |

The cheapest option is to assign the new value directly to a variable or field
(`p = Punto(x, y)`, `b = [1, 2, 3]`): it is created already holding its reference. An intermediate value
goes through the list of temporaries.

### Finding memory bugs (`--memcheck`)

With `./dash --memcheck` the program reports as soon as something is freed twice, used after
being freed or released without anyone holding it (`memcheck: ERROR ...`), and on exit it prints:

```
memcheck: vivos 0 objetos y 0 strings (escapados 0 y 0), errores 0
```

- "Vivos" (live) that are not "escapados" (escaped) on exit are leaks or cycles: something nothing will free.
- "Escapados" are the ones that stay until the end on purpose (see the table).
- In this version freed blocks are filled with `0xDB`: a number such as
  `-606348325` in the output is a value read from memory already freed.

For the compiler: `python3 tests/run_tests.py --emu --memcheck` runs all the tests this way, and
`tools/fuzz_refcount.py` generates random programs with structs, lists and strings, compares them
against a model and checks the memory.

### Arena Allocator (Manual)

For high-performance temporary allocations:

```
# Create a 64KB arena
arena = arena_new(65536)

# Allocate quickly (no overhead)
ptr1 = arena_alloc(arena, 100)
ptr2 = arena_alloc(arena, 200)
ptr3 = arena_alloc(arena, 50)

# Check usage
Print arena_used(arena)         # Bytes used
Print arena_available(arena)    # Bytes available

# Reset everything at once (instant)
arena_reset(arena)

# Free the whole arena
arena_free(arena)
```

### When to Use Each

| Scenario | Method |
|-----------|--------|
| Long-lived objects | Reference Counting (automatic) |
| Temporary per-frame objects | Arena Allocator |
| Enemy/bullet pools | Arena Allocator |
| Persistent game data | Reference Counting |

---

## 18. System Functions

### Clock

`time_ms()` gives the milliseconds since the program started (the EClock of `timer.device`). The system clock's date and
time: `clock_read` and `date_text` (see [Date and time](#date-and-time-clock_-and-date_text)).

```
t = time_ms()
procesa()
Print "tardo " + (time_ms() - t) + " ms"
```

### Debugging in the emulator

`debug_break()` stops the emulated machine in the UAE debugger (FS-UAE, WinUAE). On a real Amiga
it does nothing. With `tools/emu_run.py --debug ORDEN` (repeatable) each command goes to the debugger while
it waits, and then `g` so the program carries on. At the end, the debugger's replies are printed:

```
x = 41
debug_break()
x = x + 1
```

```bash
tools/emu_run.py --debug r --debug t --debug "d" prog.dash
```

Useful commands: `r` registers, `t` one instruction, `d dir n` disassemble, `m dir n` memory,
`H n` the last instructions, `f dir` breakpoint, `g` continue. `h` gives the full list.
Without `--debug` (the tests) the program carries on by itself.

### Runtime errors

A bug in the program doesn't hang the Amiga: the program says what happened and where, does the same cleanup
as when it ends normally (it closes its windows, screens and libraries and frees its memory) and exits with
return code 20. The system keeps working.

| Failure | Message |
|---|---|
| A field or a method of `nil` | `Error: campo de nil (en prog.dash:12)` |
| A processor exception | `Error: division por cero (excepcion 5)` and, below it, `en el programa: hunk 0 + $4AC` |

Processor exceptions are the ones that give a Guru in C: bus error (2), odd address (3, a jump or a word at an
odd address on a 68000), illegal instruction (4), division by zero (5), CHK (6), TRAPV (7), privileged
instruction (8) and lines A and F (10 and 11). They come mostly from `@native` code or from a library that is
passed a bad pointer; if the fault is inside a library, the second line says `fuera del programa (una
libreria)`. The hunk and the offset let you find the instruction in the executable
(`m68k-amigaos-objdump -d`); with `--memcheck` you also get the Dash line.

How it works: the program installs its own handler in its task's `tc_TrapCode` when it starts (and restores
the previous one on exit: from the Shell, the program runs in the Shell's process). Exec jumps there with the
exception; the handler drops the exception frame and continues in user mode, on a stack of its own, in a
function that writes the message and calls the cleanup. With `./dash --debug`, the debugger stops first.

What can't be prevented: AmigaOS 3 has no memory protection. A write through a wild pointer (in `@native`)
can break another part of the system without anyone noticing, and a fault inside another task (a
`task_start` process, an input handler) or with the system in `Forbid()`/`Disable()` can leave it damaged.
With no console (a program started from the Workbench), the message comes up in a requester.

### Program arguments

From the Shell, whatever follows the program name (`visor pagina.html "otra cosa"`):

```
for i in (0..arg_count() - 1)
    Print arg(i)
end
```

`arg(i)` gives `""` if there is no such argument. From the Workbench they are the project icons the
program was started with: a double click on a document whose default tool it is, or shift + click on
several and a double click on the last one. `arg(i)` then gives the full path of each
(`Work:Textos/carta.odt`; of a drawer or a disk, its own path).

### System Memory

```
chip = mem_chip_free()      # free Chip RAM, in bytes
fast = mem_fast_free()      # free Fast RAM
libre = mem_total()         # free memory of both (not the size of the RAM)
tam = mem_chip_total()      # size of Chip RAM (free and in use); mem_fast_total(), that of Fast RAM
```

### Reading and writing memory: peek and poke

```
v = peek_byte(0xBFE001)          # also peek_word and peek_long
poke_word(0xDFF180, 0x0F00)      # also poke_byte and poke_long
```

They read or write 8, 16 or 32 bits at an address (a number or a buffer). They check nothing: a
bad address hangs the Amiga, and on a 68000 `peek_word`, `peek_long` and their `poke` counterparts need an
even address. For the chip registers, the graphics and sound functions are a better choice.

### Time and Waiting

```
time_delay(50)              # Wait 50 ticks (1 second)
time_delay_ms(500)          # Wait 500 milliseconds
wait_vblank()               # Wait for vertical blank
wait_blit()                 # Wait for the blitter to finish
```

### Random Numbers

```
n = random()                        # Random number
dado = random_range(1, 6)           # Between 1 and 6
random_seed(12345)                  # Set the seed
```

---

## 19. User Interface - GadTools

GadTools is the native gadget system of AmigaOS 2.0+. It is ideal for applications that need to combine gadgets with custom drawing (such as graphics editors).

### Initialization

```
gt_init()       # Initialize GadTools (after opening the window)
gt_attach()     # Attach the gadgets to the window
gt_cleanup()    # Clean up on close
```

### Buttons

```
# gt_button(x, y, width, height, label) -> gadget_id
btn_ok = gt_button(10, 10, 80, 20, "OK")
btn_cancel = gt_button(100, 10, 80, 20, "Cancel")
```

### Color Palette

```
# gt_palette(x, y, width, height, label, depth, color_inicial) -> gadget_id
pal = gt_palette(10, 40, 100, 80, "Color", 4, 1)    # 16 colors (4 bitplanes), color 1 selected

# Get the selected color
color = gt_get_value(pal)
```

### Slider

```
# gt_slider(x, y, width, height, label, min, max, initial) -> gadget_id
slider = gt_slider(10, 130, 150, 20, "Volumen", 0, 100, 50)

# Get/set the value
valor = gt_get_value(slider)
gt_set_value(slider, 75)
```

### Checkbox

```
# gt_checkbox(x, y, width, height, label, checked) -> gadget_id
check = gt_checkbox(10, 160, 150, 20, "Activar", false)

# Get the state
activo = gt_get_value(check)
```

### Gadget Events

```
# In the main loop:
event = gt_event()

if event == -2          # Window closed
    running = false
end

if event == btn_ok
    Print "OK pulsado"
end

if event == slider
    valor = gt_get_value(slider)
end
```

### Menus

```
# Build the menu structure
menu_title("Archivo")
menu_item("Nuevo", "N", MENU_NEW)
menu_item("Abrir...", "O", MENU_OPEN)
menu_item("Guardar...", "S", MENU_SAVE)
menu_separator()
menu_item("Salir", "Q", MENU_QUIT)

menu_title("Ayuda")
menu_item("Acerca de...", "?", MENU_ABOUT)

# Attach the menus to the window
menu_attach()

# In the loop:
menu_ev = menu_event()
if menu_ev == MENU_QUIT
    running = false
end
```

The `gt_*` gadgets and the menus belong to the window in which `gt_init()` was called (even if another
one later becomes the current window). Calling `gt_init()` again starts from scratch, and calling `menu_attach()` again
changes the menus. `gt_event()` and `menu_event()` read the same window port: whatever one reads that is meant for the other is
kept, so both can be called on every iteration. `gt_event()` returns -1 if there is nothing and
-2 on close; `gt_wait_event()` waits. The coordinates of `gt_*` count from inside the window
borders.

With an `EventLoop`, the menu is handled with `On Menu` and `menu_id()`:

```
EventLoop
    On Menu
        if menu_id() == MENU_QUIT
            Stop
        end
    end
end
```

If several items are chosen at once (dragging with the right button and clicking the left one),
`On Menu` runs once for each of them.

### ASL Requesters

```
# File requester for opening
if file_open_dialog("Abrir Sprite", "#?.iff")
    ruta = file_fullpath()          # "Work:sprites/nave.iff"
    nombre = file_get_name()        # "nave.iff"
    carpeta = file_get_path()       # "Work:sprites"
end

# File requester for saving
if file_save_dialog("Guardar Como", "#?.iff")
    destino = file_fullpath()
end

# These return the choice directly ("" if cancelled)
ruta = dialog_file("Abrir", "#?.iff", false)      # true: save requester
fuente = dialog_font("Tipo de letra")            # "topaz.font/8"
color = dialog_color("Color de pluma", 1)        # screen color number
```

`file_fullpath()`, `file_get_name()` and `file_get_path()` give what was chosen in the last
`file_open_dialog` or `file_save_dialog` that was accepted (drawer and name together, just the name or
just the drawer). Store it in a variable, because the next requester changes it.

`asl.library` is on the Workbench disk (`LIBS:`), not in ROM: without it the ASL requesters
return `""` (or false). `dialog_color` does not use ASL (3.1 has no color requester):
it opens a window with the screen's palette; you choose with the mouse or with the arrow keys and
Return, and Esc or the close button return the initial color.

### Gadgets by number (without gt_init / gt_attach)

They can be created at any time and appear immediately. They return a number (1..64, 0 on failure).
The first parameter is the window: 0 = the current one (or the number from `window_create`).
The coordinates are inside the window, like those of `gfx_*`.

```
b = button_create(0, 10, 10, 80, 14, "OK")
c = checkbox_create(0, 10, 30, "Activo")
s = slider_create(0, 10, 50, 100, 10, 0, 10, 3)       # min, max, value
t = textfield_create(0, 10, 66, 120, 14, 20)          # up to 20 characters
l = listview_create(0, 150, 10, 120, 60)
listview_add(l, "uno")

EventLoop
    On Gadget
        g = gadget_id()
        if g == b
            Print textfield_get(t)
        end
        if g == l
            Print listview_selected(l)                # row, or -1
        end
    end
    On Close
        Stop
    end
end
```

Also: `button_enable/disable`, `checkbox_get/set`, `slider_get/set`, `textfield_set`,
`listview_clear`, and these other gadgets (their value is also updated with `On Gadget`):

| Function | Gadget |
|---|---|
| `cycle_create(win, x, y, w, h, "Uno|Dos")`, `cycle_get/set` | Cycle gadget; value = option (from 0) |
| `radio_create(win, x, y, "A|B|C")`, `radio_get/set` | Radio buttons, one below the other |
| `integer_create(win, x, y, w, h, valor)`, `integer_get/set` | Number field |
| `palette_create(win, x, y, w, h, prof)`, `palette_get/set` | Palette of 2^prof colors; value = color |
| `number_create(win, x, y, w, h, valor)`, `number_set` | Number in a box (read-only) |

**Size based on the font:** with a width or height of 0, the gadget is measured with the screen font (the
one GadTools uses, which may not be the window's): a button fits its label, a cycle gadget its
longest option and a field ten letters; the height is the font's plus 6. `gadget_width(g)` and
`gadget_height(g)` give the size so you can place the next one:

```
b = button_create(0, 10, 10, 0, 0, "_Guardar")
c = cycle_create(0, 10, 10 + gadget_height(b) + 4, 0, 0, "Uno|Dos|Cuatro")
```

**Keyboard shortcuts:** a `_` in the label of a button or a checkbox underlines the next letter
(`button_create(0, 10, 10, 80, 14, "_Guardar")`), and that key, with or without Shift, presses it in the
`EventLoop` like a click: it reaches `On Gadget` with its `gadget_id()` and a checkbox toggles. It does not reach
`On Key`; other keys do. With Amiga, Ctrl or Alt it does not count (those belong to the menus).

Gadgets are freed on exit; they are not used after their window is closed.
GadTools does not support GimmeZeroZero windows (all of Dash's are): the row chosen in a
listview is worked out by Dash from the mouse position.

### Complete GadTools Example

```
Window EditorWin
    title "Editor"
    width 320
    height 220
end

const BTN_CLEAR = 1
const BTN_SAVE = 2

Main
    screen_open(4, "Mi Editor")
    EditorWin.open

    gt_init()

    # Create gadgets
    pal = gt_palette(10, 40, 70, 80, "Color", 4, 1)
    btn_clear = gt_button(10, 130, 70, 20, "Limpiar")
    btn_save = gt_button(10, 155, 70, 20, "Guardar")

    gt_attach()

    # Draw the work area
    gfx_pen(1)
    gfx_box(90, 40, 300, 200)

    running = true
    while running
        event = gt_event()

        if event == -2
            running = false
        end

        if event == btn_clear
            gfx_pen(0)
            gfx_rect(91, 41, 299, 199)
        end

        if event == pal
            color = gt_get_value(pal)
            gfx_pen(color)
        end

        wait_vblank()
    end

    gt_cleanup()
    close_window()
    screen_close()
end
```

### GadTools Functions

| Function | Description |
|---------|-------------|
| `gt_init()` | Initialize GadTools |
| `gt_attach()` | Attach gadgets to the window |
| `gt_cleanup()` | Clean up resources |
| `gt_button(x,y,w,h,label)` | Create a button |
| `gt_palette(x,y,w,h,label,depth,color)` | Create a palette selector (2^depth colors; `color` = the one selected at the start) |
| `gt_slider(x,y,w,h,label,min,max,init)` | Create a slider |
| `gt_checkbox(x,y,w,h,label,checked)` | Create a checkbox |
| `gt_string(x,y,w,h,label,inicial,max)` | Text field of up to `max` characters |
| `gt_integer(x,y,w,h,label,inicial)` | Number field (`gt_get_value` gives the number) |
| `gt_text(x,y,w,h,label,texto)` | Fixed text with a frame (changed with `gt_set_text`) |
| `gt_get_string(gadget)` | Text of a `gt_string` |
| `gt_event()` | Get a gadget event (-1 nothing, -2 close) |
| `gt_wait_event()` | Like `gt_event()`, but waits until there is one |
| `gt_get_value(gadget)` | Value: checkbox 1/0, slider, palette color, number of an integer field |
| `gt_set_value(gadget,value)` | Change that value |
| `menu_title(name)` | Create a menu title |
| `menu_item(name,shortcut,id)` | Create a menu item (`shortcut` `""` = no shortcut) |
| `menu_sub(name,shortcut,id)` | Create a sub-item of the last `menu_item` |
| `menu_separator()` | Create a separator |
| `menu_attach()` | Attach the menus |
| `menu_event()` | Get a menu event |
| `menu_id()` | In `On Menu`: the chosen item |
| `menu_check_item(name,shortcut,id)` | Item with a checkmark that toggles on and off when chosen |
| `menu_checked(id)` | 1 if that item's checkmark is set |
| `menu_enable(id, si)` | Enables or disables (ghosts) an item, after `menu_attach` |
| `gt_cycle(x,y,w,h,label,"A|B")` | Cycle gadget (`gt_get_value`: option) |
| `gt_enable(id)`, `gt_disable(id)` | Enable or disable a gadget |
| `gt_set_text(id, texto)` | Change the text of a `gt_text` or `gt_string` |

---

## 20. User Interface - ReAction

ReAction is the BOOPSI-based GUI system of AmigaOS 3.2 (Dash is tested there). It uses an automatic layout system that handles gadget positioning.

**Note:** ReAction is ideal for dialogs and forms. For applications with extensive custom drawing (such as pixel editors), use GadTools.

### Creating a ReAction Window

```
# ra_window_create(titulo, ancho, alto)
ra_window_create("Mi Aplicacion", 300, 200)

# Open the window
ra_window_open()

# Close when finished
ra_window_close()
```

### Several windows

Up to 4. `ra_window_create` returns the window number (1-4) and makes it the current one: the `ra_add_*`,
`ra_window_open` and `ra_window_close` calls that follow apply to it. `ra_window_use(n)` selects another.
`ra_wait_event` listens to all of them and `ra_event_window()` says which one the event came from. Gadget ids
are program-wide (do not repeat them across windows); `ra_get_value`/`ra_set_value` and the others
work even when their window is not the current one.

```
v1 = ra_window_create("Una", 220, 120)
ra_add_button(10, "Uno")
ra_window_open()
v2 = ra_window_create("Dos", 220, 120)
ra_add_button(20, "Dos")
ra_window_open()
abiertas = 2
while abiertas > 0
    ev = ra_wait_event()
    if ev == RA_EVENT_CLOSE()
        ra_window_use(ra_event_window())
        ra_window_close()           # the other one becomes current
        abiertas = abiertas - 1
    elif ev >= 0
        Print "boton #{ev} de la ventana #{ra_event_window()}"
    end
end
```

### Available Gadgets

```
# Text label
ra_add_label("Titulo:")

# Button
# ra_add_button(id, label)
ra_add_button(1, "Aceptar")
ra_add_button(2, "Cancelar")

# Text field
# ra_add_string(id, texto_inicial, max_chars)
ra_add_string(3, "Nombre", 64)

# Checkbox
# ra_add_checkbox(id, label, checked)
ra_add_checkbox(4, "Activar opcion", false)

# Slider
# ra_add_slider(id, min, max, initial)
ra_add_slider(5, 0, 100, 50)

# Integer
# ra_add_integer(id, initial, min, max)
ra_add_integer(6, 0, 0, 999)

# Color palette (color selector)
# ra_add_palette(id, depth, initial_color)
ra_add_palette(7, 4, 1)   # 4 bits = 16 colors, initial color 1

# Chooser (dropdown menu)
# ra_add_chooser(id) - creates the empty chooser
ra_add_chooser(8)
ra_chooser_add_item(8, "Opcion 1")
ra_chooser_add_item(8, "Opcion 2")
ra_chooser_add_item(8, "Opcion 3")

# Scroller (horizontal)
# ra_add_scroller(id, min, max, visible, initial)
ra_add_scroller(9, 0, 100, 10, 0)

# Vertical scroller
# ra_add_scroller_vert(id, min, max, visible, initial)
ra_add_scroller_vert(10, 0, 100, 10, 0)
```

### Layout with Groups

ReAction lets you arrange gadgets in horizontal and vertical groups:

```
# Create a horizontal group
ra_layout_hgroup_begin()
    ra_add_button(1, "Izq")
    ra_add_button(2, "Centro")
    ra_add_button(3, "Der")
ra_layout_group_end()

# Create a vertical group
ra_layout_vgroup_begin()
    ra_add_label("Seccion 1")
    ra_add_string(4, "", 32)
    ra_add_label("Seccion 2")
    ra_add_string(5, "", 32)
ra_layout_group_end()

# Spacers
ra_add_space()   # Horizontal space
ra_add_vspace()  # Vertical space
```

### Getting and Setting Values

```
# Get a numeric value (slider, checkbox, integer, scroller)
valor = ra_get_value(gadget_id)

# Get text (string gadget)
texto = ra_get_string(gadget_id)

# Set a numeric value
ra_set_value(gadget_id, nuevo_valor)

# Set the text of a string gadget
ra_set_string(gadget_id, "nuevo texto")

# Set the text of a label
ra_set_text(gadget_id, "Nuevo titulo")

# For Palette
color = ra_get_palette_color(palette_id)

# For Chooser (dropdown)
indice = ra_get_chooser_selected(chooser_id)
ra_set_chooser_selected(chooser_id, nuevo_indice)
```

### Gadget Control

```
# Enable/disable gadgets
ra_disable_gadget(gadget_id)  # Disable (ghosted)
ra_enable_gadget(gadget_id)   # Enable again

# Check whether a gadget exists
if ra_gadget_exists(gadget_id)
    valor = ra_get_value(gadget_id)
end
```

### Window Utilities

```
# Get the window dimensions
ancho = ra_window_width()
alto = ra_window_height()

# Check whether the window is open
if ra_window_is_open()
    # The window exists
end
```

### Event Handling

```
# Wait for and get an event
event = ra_wait_event()

# Event constants
# RA_EVENT_CLOSE() - Window closed
# RA_EVENT_NONE()  - No event

if event == RA_EVENT_CLOSE()
    running = false
end

if event == 1  # ID of the Accept button
    Print "Aceptar pulsado"
end
```

`RA_EVENT_NONE()` is -3, so a gadget can have id 0. `ra_wait_event()` first returns any
messages left pending and then waits; it can return `RA_EVENT_NONE()` if what arrived was not
from a gadget (the mouse, for example). Ids go from 0 to 63; one outside that range is not stored.
`ra_get_value` and `ra_set_value` also work before the window is opened.

For `func render_canvas()` to draw the `ra_add_drawing_area` area, you have to call
`ra_init_canvas_render()` before creating the area and `ra_canvas_enable()` when the program is ready.

### Custom Drawing in ReAction

To draw in a ReAction window:

```
# Get the RastPort after opening the window
ra_get_rastport()

# Now you can use the gfx_* functions
gfx_pen(1)
gfx_rect(10, 100, 200, 150)
```

**Warning:** ReAction's automatic layout may overwrite custom drawing when resizing. For drawing-heavy applications, use GadTools.

### Example: Settings Dialog

```
const BTN_OK = 1
const BTN_CANCEL = 2
const CHK_SOUND = 3
const SLD_VOLUME = 4
const STR_NAME = 5

Main
    ra_window_create("Configuracion", 250, 180)

    ra_add_label("Nombre del jugador:")
    ra_add_string(STR_NAME, "Player1", 32)

    ra_add_checkbox(CHK_SOUND, "Activar sonido", true)

    ra_add_label("Volumen:")
    ra_add_slider(SLD_VOLUME, 0, 100, 75)

    ra_add_label("---")
    ra_add_button(BTN_OK, "Aceptar")
    ra_add_button(BTN_CANCEL, "Cancelar")

    ra_window_open()

    running = true
    while running
        event = ra_wait_event()

        if event == RA_EVENT_CLOSE()
            running = false
        end

        if event == BTN_OK
            nombre = ra_get_string(STR_NAME)
            sonido = ra_get_value(CHK_SOUND)
            volumen = ra_get_value(SLD_VOLUME)
            # Save settings...
            running = false
        end

        if event == BTN_CANCEL
            running = false
        end
    end

    ra_window_close()
end
```

### ReAction with a Custom Screen

```
Main
    # Open the screen first
    screen_open(4, "Mi App")

    # The ReAction window will open on that screen
    ra_window_create("Opciones", 200, 150)
    ra_add_button(1, "OK")
    ra_window_open()

    # ...

    ra_window_close()
    screen_close()
end
```

### ReAction Functions

#### Window
| Function | Description |
|---------|-------------|
| `ra_window_create(title,w,h)` | Create a ReAction window (returns its number, 1-4; it becomes current) |
| `ra_window_use(n)` | Select the current window |
| `ra_event_window()` | Window of the last event |
| `ra_window_open()` | Open the window |
| `ra_window_close()` | Close the window (the current one) |
| `ra_window_width()` | Get the window width |
| `ra_window_height()` | Get the window height |
| `ra_window_is_open()` | Check whether the window is open |
| `ra_get_rastport()` | Get the RastPort for drawing |

#### Basic Gadgets
| Function | Description |
|---------|-------------|
| `ra_add_label(text)` | Add a label |
| `ra_add_button(id,label)` | Add a button |
| `ra_add_string(id,text,max)` | Add a text field |
| `ra_add_checkbox(id,label,checked)` | Add a checkbox |
| `ra_add_slider(id,min,max,init)` | Add a slider |
| `ra_add_integer(id,init,min,max)` | Add a numeric field |

#### Advanced Gadgets
| Function | Description |
|---------|-------------|
| `ra_add_palette(id,depth,init)` | Color selector (depth=bits) |
| `ra_add_listbrowser(id)` | List of lines (value: selected line, -1 none) |
| `ra_listbrowser_add(id,texto)`, `ra_listbrowser_clear(id)`, `ra_listbrowser_count(id)` | Add, clear, count lines |
| `ra_add_radio(id,"A|B|C")` | Radio buttons (value: option) |
| `ra_add_clicktab(id,"A|B")` | Tabs (value: tab, from 0) |
| `ra_add_fuelgauge(id,max)` | Progress bar (value: level) |
| `ra_add_getfile(id,titulo)` | Button that opens the file requester; `ra_get_string(id)` gives the chosen file |
| `ra_menu_title(texto)`, `ra_menu_item(texto,tecla,id)`, `ra_menu_separator()` | Window menus (before `ra_window_open`) |
| `ra_menu_id()` | The chosen item, when `ra_wait_event()` returns `RA_EVENT_MENU()` (-4) |
| `ra_add_chooser(id)` | Create an empty dropdown |
| `ra_chooser_add_item(id,label)` | Add an item to a dropdown |
| `ra_add_scroller(id,min,max,vis,init)` | Horizontal scroller |
| `ra_add_scroller_vert(id,min,max,vis,init)` | Vertical scroller |

#### Layout
| Function | Description |
|---------|-------------|
| `ra_layout_hgroup_begin()` | Start a horizontal group |
| `ra_layout_vgroup_begin()` | Start a vertical group |
| `ra_layout_group_end()` | Close a group |
| `ra_add_space()` | Horizontal space |
| `ra_add_vspace()` | Vertical space |

#### Get/Set Values
| Function | Description |
|---------|-------------|
| `ra_get_value(id)` | Get a numeric value |
| `ra_set_value(id,value)` | Set a numeric value |
| `ra_get_string(id)` | Get text |
| `ra_set_string(id,text)` | Set the text of a string gadget |
| `ra_set_text(id,text)` | Set the text of a label |
| `ra_get_palette_color(id)` | Get the palette color |
| `ra_get_chooser_selected(id)` | Get the dropdown index |
| `ra_set_chooser_selected(id,idx)` | Set the dropdown selection |

#### Gadget Control
| Function | Description |
|---------|-------------|
| `ra_enable_gadget(id)` | Enable a gadget |
| `ra_disable_gadget(id)` | Disable a gadget |
| `ra_gadget_exists(id)` | Check whether a gadget exists |

#### Events
| Function | Description |
|---------|-------------|
| `ra_wait_event()` | Wait for an event |
| `RA_EVENT_CLOSE()` | Constant: window closed |
| `RA_EVENT_NONE()` | Constant: no event |
| `ra_handle_events()` | Like `ra_wait_event()` without waiting: the event, or `RA_EVENT_NONE()` if there is none |
| `ra_window_sigmask()` | Signals of the open windows, to wait for them together with others |

#### More gadgets and layout
| Function | Description |
|---------|-------------|
| `ra_get_scroller(id)`, `ra_set_scroller(id,pos)` | Position of a scroller |
| `ra_set_palette_color(id,color)` | Select the color of a palette |
| `ra_layout_hgroup_weighted(peso)`, `ra_layout_vgroup_weighted(peso)` | Horizontal or vertical group with a weight: the share of free space it gets relative to its neighbours |
| `ra_layout_group_end_weighted()` | Closes one of those groups (with `ra_layout_group_end` the weight does not count) |
| `ra_refresh_layout()` | Recalculate the window after adding gadgets while it is open |
| `ra_get_inner_left()`, `ra_get_inner_top()`, `ra_get_inner_width()`, `ra_get_inner_height()` | Area inside the window borders |

#### Drawing area
| Function | Description |
|---------|-------------|
| `ra_add_drawing_area(id,ancho_min,alto_min)` | Area for drawing with `gfx_*`; grows with the window |
| `ra_init_canvas_render()` | Before creating the area: the program's `render_canvas()` function paints it |
| `ra_canvas_enable()` | When the program is ready: from here on `render_canvas()` is called |
| `ra_canvas_left()`, `ra_canvas_top()`, `ra_canvas_width()`, `ra_canvas_height()` | Inside `render_canvas()`: where the area is in the window |
| `ra_refresh_canvas(id)` | Repaint the area (calls `render_canvas()`) |
| `ra_get_drawing_bounds(id)` | With the window open, measures the area (1 if it could) for `ra_drawing_*` |
| `ra_drawing_left()`, `ra_drawing_top()`, `ra_drawing_width()`, `ra_drawing_height()` | What was measured by `ra_get_drawing_bounds` or `ra_calc_drawing_area` |
| `ra_calc_drawing_area(barra_h,linea_h,izq_w,der_w)` | Calculates the area by subtracting those margins from the window (if there is no area to measure) |

### GadTools vs ReAction

| Feature | GadTools | ReAction |
|----------------|----------|----------|
| Positioning | Manual (absolute) | Automatic (layout) |
| Compatibility | AmigaOS 3.0+ (what Dash requires) | AmigaOS 3.2 (where it is tested) |
| Custom drawing | Excellent | Limited |
| Resizing | No problems | Layout recalculates |
| Ideal for | Editors, games | Dialogs, forms |
| Visual style | Classic | Modern |

---

## 20b. User Interface - MUI

MUI (MagicUserInterface) is the interface used by most large Amiga programs. Dash
uses MUI 5 (3.8 works too). It requires:

- **On the Amiga:** MUI installed and a **68020** or better (MUI 5 for AmigaOS 3 is 68020 code).
  On a 68000 `mui_app_begin` prints "MUI: needs a 68020 or better" and returns 0.
- **To compile:** the MUI SDK, which does not come with the toolchain: `tools/get_mui_sdk.sh` downloads it
  into `~/.cache/dash-mui` (or `DASH_MUI_SDK` points to its `SDK/MUI` folder).

Programs with MUI request 32 KB of stack (with less, MUI stops with a warning). Full design (lists,
menus, drawing area...): `docs/MUI_DISEÑO.md`.

### Building the window

The window is described from top to bottom. Each object created goes into the open group;
`mui_window_begin` opens a vertical group and `mui_hgroup_begin`/`mui_vgroup_begin` open others inside it.
Objects are numbers (like buffers or file handles): they are stored in variables and passed to other functions.

```ruby
const ID_SALUDA = 1

Main
    if mui_app_begin("Hola MUI", "HOLAMUI") == 0
        Print "No se puede usar MUI"
    else
        win = mui_window_begin("Hola MUI", 1)   # 1: MUI remembers size and position (0: it does not)
            mui_text("\33cPulsa el botón")      # \33c = centered
            mui_hgroup_begin()
                saluda = mui_button("_Saluda")  # _S: keyboard shortcut
            mui_group_end()
        mui_window_end()
        mui_on_press(saluda, ID_SALUDA)
        mui_window_open(win)
        while true
            ev = mui_wait_event()
            if ev == -1                         # window closed or Ctrl-C
                break
            end
            if ev == ID_SALUDA
                Print "Hola"
            end
        end
        mui_app_end()
    end
end
```

### Events

Events are numbers chosen by the program (greater than 0). `mui_on_press(boton, id)` makes
`mui_wait_event()` return `id` when the button is pressed. Closing the first window returns -1;
`mui_on_close(ventana, id)` changes that to another number. `mui_poll_event()` does not wait (0 if there is nothing)
and `mui_press(boton)` fires the button's event as if it were pressed (on a menu item, as if it were chosen).

Several windows can be created (each with its own `mui_window_begin` ... `mui_window_end`). Closing a
window that is not the first one just closes it, unless it has its own `mui_on_close`.

### Functions

| Function | What it does |
|---|---|
| `mui_app_begin(titulo, base)` | Opens MUI and creates the application (`base`: ARexx name). 0 if it cannot. |
| `mui_window_begin(titulo, id)` / `mui_window_end()` | Starts and ends a window. |
| `mui_vgroup_begin()`, `mui_hgroup_begin()` / `mui_group_end()` | Vertical or horizontal group. |
| `mui_frame_begin(titulo, horizontal)` | Group with a frame and title (`""` = no title). |
| `mui_columns_begin(n)` | Grid of `n` columns, filled row by row (label, field, label, field...). |
| `mui_register_begin("Uno|Dos")` | Tabs: each child is a page. Its value is the visible page (from 0). |
| `mui_scroll_begin()` | Area with scroll bars for content larger than the window. |
| `mui_space()`, `mui_balance()` | Space that takes up whatever is left over; bar the user drags to share out space. |
| `mui_weight(obj, peso)` | Share of the free space it gets (100 by default). |
| `mui_set_visible(obj, si)` | Shows or hides (the window re-lays itself out). |
| `mui_menu_begin(titulo)` ... `mui_menu_end()` | Menu of the window being built. |
| `mui_menu_item(texto, tecla, id)` | Menu item: `tecla` = letter for Amiga+key (`""` = none); returns the object (for `mui_set_enabled`). |
| `mui_menu_separator()` | Separator line. |
| `mui_menu_check(text, key, id, checked)` | Item with a check mark: choosing it toggles the mark and gives its `id`. `mui_get_value(item)` says whether it is checked (1/0) and `mui_set_value(item, 1)` checks it from the program. |
| `mui_submenu_begin(title)` ... `mui_submenu_end()` | Submenu inside the menu (one level, as in Intuition). |
| `mui_set_enabled(item, false)`, `mui_set_text(item, text)` | Disables an item or a whole menu (the object of `mui_menu_begin`); changes an item's text ("Open recent"). |
| `mui_canvas(ancho_min, alto_min)` | Custom drawing area; grows with the window. |
| `mui_canvas_on_draw(zona, funcion)` | Function `f(x, y, ancho, alto)` that paints it with the `gfx_` functions. MUI calls it when needed (on opening, on resizing...). You can only paint inside it. Fills work too (`gfx_circle_fill`, `gfx_poly_*`...). |
| `mui_canvas_redraw(zona)` | Repaints it now. |
| `mui_canvas_buffered(zona, true)` | The drawing function paints into a separate bitmap (with the same coordinates) and the area is copied to the window in one go at the end: a slow drawing is never seen half-done. Uses the window's memory up to the corner of the area (on RTG, graphics card memory). `mui_canvas_update` still paints directly into the window. |
| `mui_canvas_update(zona)` | Calls its drawing function now without clearing it first: paints only what changed (a video, a cursor). |
| `mui_canvas_update_area(zona, x, y, ancho, alto)` | Like `mui_canvas_update`, only that part (x, y from the corner of the area): what the drawing function paints is clipped there. With `mui_canvas_buffered` it paints into the buffer and only that part goes to the window, without flicker; the function must paint the whole part, because the rest of it in the buffer is what was there last time. |
| `mui_canvas_updating()` | Inside the drawing function: `true` if it comes from `mui_canvas_update` (everything else is still painted). On opening, resizing or being uncovered, MUI clears it and it is `false`: everything must be painted. |
| `mui_canvas_on_input(zona, id)` | Event on a click, the wheel or a key over the area (before opening the window). |
| `mui_canvas_mouse_x(z)`, `mui_canvas_mouse_y(z)`, `mui_canvas_button(z)`, `mui_canvas_wheel(z)`, `mui_canvas_key(z)` | The last input: position inside the area, 1 if it was a click, +1/-1 the wheel, key code (-1 if it was not a key). |
| `mui_canvas_char(z)` | The character for that key, with Shift and the keymap (`"A"`, `"ñ"`; `""` if it gives none; Backspace gives code 8). |
| `mui_canvas_on_move(zona, id)` | Event when the mouse moves over the area, without a click, and when it leaves it (before opening the window). Movements that arrive before the program picks one up count as one; it does not delay clicks. |
| `mui_canvas_pointer_x(z)`, `mui_canvas_pointer_y(z)`, `mui_canvas_pointer_inside(z)` | Where the mouse is now, from the corner of the area, and whether it is inside it; whether or not there was a click. |
| `mui_scrollbar(vertical)` | Scroll bar; its value is the first visible line. |
| `mui_image(fichero)` | Image from a file via datatypes: ILBM always; PNG, JPEG, GIF and BMP if their datatypes are installed (AmigaOS 3.2 includes them). `mui_set_text` changes the file. |
| `mui_image_button(fichero)` | Button with an image (a toolbar icon): the frame and background of MUI's image buttons; it is pressed like a button (`mui_on_press`) and `mui_set_text` changes the image. |
| `mui_help(obj, texto)` | The help that MUI shows in a bubble when the pointer rests over it. |
| `mui_window_size(ventana, ancho, alto)` | Size the window opens with, as a percentage of the visible screen, centered (before `mui_window_open`). |
| `mui_window_fullscreen(ventana)` | The window takes up the whole screen: no borders, no title bar or buttons, at 0,0, active on opening (before `mui_window_open`). For video or games. |
| `mui_window_own_screen(ventana)` | The same on a new screen, with the mode, size and colors of the public screen; it is closed when the application ends. `false` if it could not open it (the window stays fullscreen on the public screen). |
| `mui_width(obj)`, `mui_height(obj)` | On-screen size in pixels (0 before the window is opened). |
| `mui_set_range(barra, total, visible)` | Size of the document and of what fits. |
| `mui_text(texto)` | Text. |
| `mui_label(texto)` | Form label (right-aligned). |
| `mui_button(texto)` | Button. |
| `mui_string(inicial, max)` | Text field of up to `max` characters. |
| `mui_checkbox(marcada)` | Checkbox. |
| `mui_cycle("Uno|Dos|Tres")` | Cycle gadget with options. |
| `mui_slider(min, max, valor)` | Slider. |
| `mui_gauge(max)` | Progress bar from 0 to `max`. |
| `mui_get_value(obj)`, `mui_set_value(obj, v)` | Value: checkbox 1/0, cycle option (from 0), slider level, progress. Changing it fires its `mui_on_change`. |
| `mui_get_text(obj)`, `mui_set_text(obj, texto)` | Text of a field, text, button or window title. |
| `mui_set_enabled(obj, si)` | Enables or disables (ghosts). |
| `mui_list()` | List of strings with a scroll bar. Its value is the selected line (-1 = none). |
| `mui_list_add(l, texto)`, `mui_list_insert(l, pos, texto)` | Adds at the end or at `pos` (0 = first). |
| `mui_list_remove(l, pos)`, `mui_list_clear(l)` | Deletes one line or all of them. |
| `mui_list_count(l)`, `mui_list_get(l, pos)` | Number of lines and the text of one (`""` outside the list). |
| `mui_list_quiet(l, si)` | While it is "quiet" it is not redrawn: for adding many lines. |
| `mui_on_double(l, id)` | Event on double-clicking a line. |
| `mui_on_change(obj, id)` | Event when the value or the text changes. |
| `mui_on_ack(campo, id)` | Event when Return is pressed in a text field. |
| `mui_window_open(ventana)` | Opens the window; false if it could not. |
| `mui_window_close(ventana)` | Closes it (it still exists). |
| `mui_window_active(ventana)` | 1 if it is the active window: with several windows from the same `.dashui` (same event numbers), tells which one an event comes from. |
| `mui_on_press(boton, id)`, `mui_on_close(ventana, id)` | Events. |
| `mui_wait_event()`, `mui_poll_event()`, `mui_press(boton)` | Wait for, check or fire events. |
| `mui_timer(ms, id)` | In `ms` milliseconds, `mui_wait_event` returns `id` (once; to repeat, call it again; 0 = cancel). |
| `mui_wait_event_signals(mascara)` | Like `mui_wait_event`, but also returns 0 when one of those signals arrives (network...). |
| `mui_signals()` | Which signals of the mask woke up the last wait. |
| `mui_app_end()` | Frees the application, its windows and objects (also done on exit). |

Objects are no longer valid after `mui_app_end()`.

Example of a drawing area with its scroll bar:

```ruby
func pinta(x: Int, y: Int, ancho: Int, alto: Int)
    gfx_pen(2)
    gfx_rect(x, y, x + ancho - 1, y + alto - 1)
    gfx_pen(1)
    gfx_text_at(x + 4, y + 12, "Página")
end
...
    mui_hgroup_begin()
        pagina = mui_canvas(320, 200)
        barra = mui_scrollbar(true)
    mui_group_end()
...
mui_canvas_on_draw(pagina, pinta)
mui_set_range(barra, 1000, 200)
```

On an A1200 (68020 at 14 MHz) repainting 320 x 200 takes about 20 ms for the background and about 5 ms for each line of
50 characters: a page full of text, about 115 ms. Better to repaint only what changes.

### Windows made with the visual editor (`.dashui`)

A `.dashui` file (JSON, format in `docs/MUI_EDITOR.md`) describes MUI windows. It is imported like a module and
each window provides a struct with its named objects and a `<Ventana>_create()` function that builds it:

```ruby
import "ventana.dashui"

Main
    mui_app_begin("Navegador", "NAVEGADOR")
    v = Principal_create()     # v.window, v.url, v.ir...
    mui_window_open(v.window)
    ...
end
```

Events (`"event"`, `"change"`, `"ack"`, `"double"` with their number) can be set in the `.dashui`.
Example: `examples/mui_navegador_editor.dash` with `examples/mui_navegador.dashui` (the same window as
`mui_navegador.dash`, but described in the `.dashui`). The visual editor is in `editor/vscode/` (a VS Code extension).

Complete example: `examples/mui_navegador.dash`, the skeleton of the dashweb browser window
(address bar, history, painted page with its scroll bar, status, progress with `mui_timer`, menu
and a second window). This is how it looks on an emulated A1200 with AmigaOS 3.1 and MUI 5:

![Browser window in MUI](img/mui_navegador.png)

---

## 21. Modules and Imports

### Importing a Module

```
import "lib/matematicas.dash"
import "utils/helpers.dash"
```

The path is searched, in this order: next to the file doing the `import`; in the project root (the
first folder further up that has the `dash` script or the `compiler` folder); and in the directory
the compilation is run from. An absolute path is used as is. A module imported twice is read once.

Dash ships ready-made modules in `lib/amiga/`: `audio`, `blitter`, `copper`, `dos`, `doublebuf`, `graphics`,
`iff`, `intuition`, `memory`, `rtg` and `sprites` (`import "lib/amiga/dos.dash"`). They are Dash functions
on top of the builtins; each file explains them in its comments (in English).

### Creating a Module

File `lib/matematicas.dash`:
```
func cuadrado(n)
    return n * n
end

func cubo(n)
    return n * n * n
end

func maximo(a, b)
    if a > b
        return a
    end
    return b
end
```

Functions whose name starts with `_` are private to the module: only the
module itself calls them. Each module has its own: two modules (or the program and a module) can
each have a `_ayuda` without clashing.
The same goes for constants, global variables, structs and enums with `_`: two modules
can each have their own `_TOPE` or `_Caja`. Those that match ones in another module or in
the program are renamed in the C (`_TOPE_m1_a`); the others keep their name.

A module's functions do not see the global variables (`var`) of the program that imports it: if the
module does `actual = 0` and the program has `var actual`, the module's one is a local variable of its own and the
global does not change. The program does see the globals of its modules. A variable can also have the same name as
a function (for example an `inicio = 0` in a module when the program has `func inicio()`): inside
that block the name refers to the variable.

### Using the Module

```
import "lib/matematicas.dash"

Main
    x = cuadrado(5)         # 25
    y = cubo(3)             # 27
    z = maximo(10, 20)      # 20
    Print z
end
```

### C Code: @native and @extern

`@native` writes a function in C inside the program. Its parameters and its result are Dash
types (`Int` is `LONG`, `String` is `STRPTR`, `Pointer` is `APTR`):

```
@native func peek(addr: Pointer) -> Int
"""
    return (LONG)*(volatile UBYTE *)addr;
"""
end
```

`@extern("milib.library")` declares a function from a library that is not in the NDK headers:

```
@extern("milib.library")
func MiFuncion(x: Int, y: Int) -> Int
```

**Warning (68000):** in the C of an `@native`, do not pass a system function an argument that contains a 32-bit
`*`, `/` or `%` (`SetAPen(rp, a * b)`). On a 68000 GCC computes it with a call to libgcc
that can clobber the registers the library macro had already loaded. Compute the value beforehand in
a variable and pass the variable. Dash's builtins already do it this way.

A String that an `@native` stores or hands back to the system is outside Dash's control: it is copied and
freed when the program exits (see [Memory Management](#17-memory-management)). The same goes for a struct
or a list it receives: it is retained until exit. If the C only uses its arguments during the call,
`@native(borrow) func f(s: String) ...` lends them to it as to a Dash function and they are freed as usual
(if the C wants to keep an object, it retains it itself with `_dash_retain` and releases it with
`_dash_release`).

**Long C strings.** Dash remembers the length of the long strings (64 characters or more) that it creates
itself, which is why walking through them with `s[i]`, `str_code(s, i)` or `s.length` in a loop is fast. A string that
comes from C (a pointer returned by an `@native`, or passed to a Dash function by the C of an `@c`) is not
remembered, because the C may free it and another string may take its address: each `s.length` or `str_code` measures it
in full, and walking through it is quadratic (a 26 KB string: seconds). If an `@native` returns a long string
that is going to be walked through, have it return a Dash copy: `return _dash_str_dup(texto_de_c, TRUE);` (a Dash
temporary, freed like the others; the C can release its own afterwards). Assigning it to a variable
(`t = f()`) also copies it.

### External C: @link, @header and @c

`@link` links a C source file, an object file or a library (`.c`, `.o`, `.a`) into the program, with the path
relative to the `.dash` file that names it. Its directory is also passed to gcc with `-I`, for its header.
`@header` puts a line of C at the beginning (`#include`, declarations). `@c` puts free-form C after
the prototypes of the Dash functions: functions with a C signature (callbacks) that call Dash functions
by name. `@native` functions can call whatever an `@c` defines.

```
@link "lib/externo.c"                  # or "libqjs.a"; if it does not exist, compile error
@header "#include <externo.h>"         # or "#include \"externo.h\""

func doble(x: Int) -> Int
    return x * 2
end

@c
"""
static long cb_doble(long x) { return doble(x); }   /* a callback that calls Dash */
"""
end

@native func aplicar(x: Int) -> Int
"""
    return ext_aplicar(cb_doble, x);   /* function from externo.c */
"""
end
```

From C, the public functions are called (a module's private `_x` functions are renamed). A String
returned by a Dash function is temporary: copy it if the C keeps it. The C of an `@native` or of an `@c`
can use the Dash runtime functions (`_dash_str_dup(s, TRUE)` gives a temporary Dash string) and the
program includes them. External C can use libnix's stdio (`printf`). `./dash` and the runner read the
`@link` directives from the generated C (`/* dash-link: ruta */`).

---

### C in another process: task_start

An `@native` function that takes a while (decoding an image, for example) can run in another AmigaOS
process while the program carries on with its own work (its MUI loop):

```ruby
@native func decodificar(datos: Int) -> Int
"""
    /* C: may use malloc/free (libnix's ones take a semaphore) */
    return 0;
"""
end

t = task_start(decodificar, buffer)        # the process, or 0 if it could not be created
if task_done(t)                            # true when the function has returned (does not wait)
    r = task_result(t)                     # what it returned (waits if it has not returned yet)
    task_free(t)                           # forget it (waits if it is still running)
end
t2 = task_start_with(decodificar, buffer, 65536, -1)   # stack in bytes (0: 128 KB) and priority
ev = mui_wait_event_signals(task_signal())  # wakes up when one finishes (0 if no signals are left)
```

Only C runs in the other process: no Dash strings, lists or `Print`, which are not
ready for two tasks at once. The function receives an `Int` (a number or an address) and
returns another. `task_start` uses 128 KB of stack and the program's priority; with priority `-1`
it only makes progress when the program is waiting (for example in `mui_wait_event`), and the window responds
sooner. On exit, the program waits for any tasks still running.

To notify the program without finishing (for example, that it has left some data), the task's C calls
`_dash_task_wake()`: the program receives the `task_signal()` signal. Whatever they exchange goes behind an
exec `SignalSemaphore` (`InitSemaphore`, `ObtainSemaphore`, `ReleaseSemaphore`).

**The network from a task.** On AmigaOS each process opens its own `bsdsocket.library`, so the network
belongs to one process at a time: the one that uses it first (the program or a task), until its task ends (or the
program exits). From any other, the network functions return -1 and `net_error()` says "la red es de otra
tarea". The owning task has its own name lookups, its own cache of names and TLS sessions and its own
AmiSSL, and when it ends it closes them in its own process; after that, another can take over the network.

In the task's C you can use the network functions that do not use Dash strings: `_dash_net_connect`,
`_dash_net_connect_start`, `_dash_net_connect_poll`, `_dash_net_connect_stage`,
`_dash_net_send_buffer`, `_dash_net_recv_buffer`, `_dash_net_select` (`net_wait`), `_dash_net_close`,
`_dash_net_error`, `_dash_net_signal`, `_dash_net_listen`, `_dash_net_accept`, `_dash_net_port`,
`_dash_net_udp_open`, `_dash_net_udp_send_buffer`, `_dash_net_udp_recv_buffer`, `_dash_tls_connect`,
`_dash_tls_connect_start`, `_dash_tls_connect_poll`, `_dash_tls_send_buffer`, `_dash_tls_recv_buffer`,
`_dash_tls_close` and `_dash_tls_resumed` (those of the builtins with the same name). Not: `net_recv`,
`net_send`, `net_resolve`, `net_peer`, `net_udp_recv`, `net_udp_from`, `tls_recv` or `tls_send`, which
create or read Dash strings. `_dash_net_signal()` in the task gives a signal belonging to the task, to sleep with
`Wait` until a connection has something.

### A windowless program that can be stopped: break_check and single_instance

```ruby
Main
    if not single_instance("Trasfondo")
        Print "Ya estaba en marcha: se para"    # the other copy receives Ctrl-C
    else
        while not break_check()                 # Ctrl-C ("Break" in the Shell, or launching it again)
            time_delay(50)
        end
    end
end
```

`break_check()` says whether Ctrl-C arrived and clears it. `single_instance(nombre)` keeps only one copy of the program
running: using a public port with that name. If it already exists, it sends Ctrl-C to the copy that owns it and returns `false`
(this one should exit); if not, it creates it and returns `true`. The port is removed when the program ends. That way, launching a
windowless program again from the Workbench closes it.

### A commodity: tooltype and cx_*

A windowless program can be a commodity: it appears in Exchange, which sends it commands (Show, Hide,
Disable, Enable, Kill), and it can have a hotkey.

```ruby
const CX_OCULTAR = 1
const CX_MOSTRAR = 2
const CX_DESACTIVAR = 3
const CX_ACTIVAR = 4
const CX_ELIMINAR = 5
const CX_TECLA = 6

Main
    if single_instance("Trasfondo")
        prioridad = Int(tooltype("CX_PRIORITY", "0"))
        cx_broker("Trasfondo", "Trasfondo 0.2", "La CPU en el fondo del Workbench", prioridad)
        tecla = tooltype("CX_POPKEY", "")
        if tecla != "" and not cx_hotkey(tecla)
            Print "CX_POPKEY no vale: " + tecla
        end
        while true
            orden = cx_wait(1000)           # a command, Ctrl-C (-1) or the second elapses (0)
            if orden == -1 or orden == CX_ELIMINAR
                break
            end
            # CX_OCULTAR, CX_MOSTRAR, CX_TECLA... and every second, paint
        end
    end
end
```

- `tooltype(nombre, defecto)`: from the Shell, the argument `NOMBRE=valor` (`CX_POPKEY="ctrl alt t"`; the name in
  upper or lower case); if it is not there, or from the Workbench, the tooltype of the program's icon; failing that, the
  default.
- `cx_broker(nombre, título, descripción, prioridad)`: the commodity in Exchange, with Show and Hide, enabled
  (name up to 23 letters; title and description up to 39). `false` without `commodities.library` or if there is already one with that
  name. A second call puts another in its place.
- `cx_hotkey(descripción)`: the hotkey (`"ctrl alt t"`); `false` if the description is not valid. `""` removes it.
- `cx_command()`: the next command: 0 none, 1 hide, 2 show, 3 disable, 4 enable, 5 kill,
  6 the hotkey. Disable and enable switch the commodity off and on (Exchange shows it, and the hotkey does
  nothing while it is disabled).
- `cx_wait(ms)`: waits without using CPU for a command to arrive (returns it, like `cx_command`), Ctrl-C (-1, and clears it,
  like `break_check`), a file watched with `file_notify` to change (7) or `ms` milliseconds to elapse (0).

When the program ends, the commodity and its hotkey are removed automatically. Launching the program again still stops it through
`single_instance`, which comes first.

### Disks, network and WiFi for a monitor

Each reading is done afresh, so a volume that goes away, a network that drops or a stack that stops are noticed on
the next one. Only the driver queried by `wifi_read_device` and `net_driver_read` stays open between one
reading and the next (see below). None waits longer than its timeout.

```ruby
n = disks_read(500)                  # each mounted volume, waiting 500 ms at most
for i in (0..n - 1)
    if disk_kb(i) >= 0
        Print disk_name(i) + ": #{disk_free_kb(i)} KB libres de #{disk_kb(i)}"
    else
        Print disk_name(i) + ": sin respuesta"
    end
end

m = net_ifs_read()                   # -1: no Roadshow
for i in (0..m - 1)
    Print net_if_name(i) + " #{net_if_up(i)} #{net_if_bytes_in(i)} #{net_if_bytes_out(i)}"
end

if wifi_read("wlan0", 500) == 0      # the interface name in Roadshow
    Print "señal: #{wifi_signal()} dBm, ruido: #{wifi_noise()} dBm"
end

# with any stack (Roadshow, MiamiDx, AmiTCP...): by asking the driver
d = net_drivers_read()               # the DEVS:Networks/ drivers in use
for i in (0..d - 1)
    driver = net_driver_name(i)      # "wifipi.device"
    if wifi_read_device(driver, 0, 500) == 0
        Print driver + ": #{wifi_signal()} dBm"
    end
    if net_driver_read(driver, 0, 500) == 0
        Print "paquetes: #{net_driver_packets_in()} #{net_driver_packets_out()}"
    end
end
```

- `disks_read(ms)`: reads the mounted volumes (with a disk inserted) and returns how many there are. It queries all of them at once
  (`ACTION_DISK_INFO`) and waits `ms` milliseconds at most. It never asks for a disk to be inserted.
- `disk_name(i)`, `disk_kb(i)`, `disk_free_kb(i)`: the name (without the colon), the size and the free space in KB, as
  `Info` gives them. -1 if that volume did not reply in time. A volume that does not reply is not queried again until
  it replies; meanwhile it returns -1 straight away.
- `net_ifs_read()`: reads Roadshow's network interfaces (including `lo0`) and returns how many there are. -1 without a TCP/IP stack or
  with one that does not report them (AmiTCP, Miami, the emulator's); that -1 is remembered for a minute (`bsdsocket.library`
  is not opened every second for nothing). It only uses a `bsdsocket.library` that is already in memory: it does not
  load it from `LIBS:` (that would start a stack, or get in the way of one that is starting: CaffeineOS flushes it from memory to
  put in Miami's).
- `net_if_name(i)`, `net_if_up(i)`: the name and whether it is connected.
- `net_if_bytes_in(i)`, `net_if_bytes_out(i)`: the bytes received and sent. Subtracting two readings gives the
  bytes in between, even if it goes past 2 GB. For the speed: the difference divided by the time elapsed.
- `wifi_read(interfaz, ms)`: asks the interface's SANA-II driver for the signal (`S2_GETSIGNALQUALITY`, the wireless
  extension of `prism2.device` and others) and waits `ms` at most. Returns 0 if it read it, 1 if it did not reply in time (the request
  is aborted), 2 if the driver does not provide it, 3 if there is no such interface, 4 if the driver returns an error (disconnected), 5 if the stack
  has the driver to itself and -1 without Roadshow. If a driver holds on to the request after it is aborted,
  it is not queried again until it returns it.
- `net_drivers_read()`, `net_driver_name(i)`: the network drivers (SANA-II) in use, with any stack: those in
  `DEVS:Networks/` that someone has open. `bsdsocket.library` is not needed. The drawer is read once a
  minute; the list of open devices, on every reading.
- `wifi_read_device(driver, unidad, ms)`: like `wifi_read`, but asking that driver directly (the unit
  is almost always 0). It only queries a driver that is already in use: it does not load any, because that would start up
  its card. With a driver nobody is using it returns 3. Between queries the driver stays open (up to four
  drivers and units), so it is not opened and closed every second; when only the program has it open (its stack
  let it go), it is closed and returns 3.
- `net_driver_read(driver, unidad, ms)`, `net_driver_packets_in()`, `net_driver_packets_out()`: the packets
  received and sent by the driver, with the same codes. If the driver counts bytes per packet type
  (`S2_TRACKTYPE` and `S2_GETTYPESTATS` for IPv4, IPv6 and ARP), `net_driver_has_bytes()` is `true` and
  `net_driver_bytes_in()` and `net_driver_bytes_out()` return them (the low 32 bits, like `net_if_bytes_in`). Not all
  drivers count them: `wifipi.device` does not. On exit, the types that started being tracked stop being tracked.
- `wifi_signal()`, `wifi_noise()`: the signal and noise of the last good reading, in dBm (-30 very good, -90 very
  poor).
- `pistorm_temperature()`: the temperature of a PiStorm's (Emu68) Raspberry Pi, in tenths of a degree (523 =
  52.3 °C). It is provided by the Pi's firmware, through Emu68's `mailbox.resource`, like EmuControl. -1 without Emu68. An
  Amiga without a PiStorm has no temperature sensor.

From SANA-II drivers only these counters and the signal are read: there are no functions to send or receive raw
frames.

### A curve for each mouse: mouse_curve and usb_hid_*

Each mouse with its own acceleration: the Amiga one and each USB mouse or trackpad (Poseidon). A movement from a USB
mouse reaches `input.device` from that mouse's `hid.class` task (`hid.class<emisor>`); the number of that
task is its **emitter**. Emitter 0 is the Amiga mouse (and any movement that does not come from a USB mouse).

```ruby
mouse_prefs_set(1, false)            # the system: speed 1, no acceleration (restored automatically on exit)
mouse_curve(0, [100, 100, 150, 200]) # the Amiga mouse: unchanged up to 2, faster after that
n = usb_hid_read()                   # -1: no Poseidon
for i in (0..n - 1)
    if usb_hid_kind(i) != 2          # not keyboards
        Print usb_hid_name(i) + " de " + usb_hid_maker(i)
        mouse_curve(usb_hid_emitter(i), [50, 80, 120, 200])
    end
end
```

- `usb_hid_read()`: reads the USB devices handled by `hid.class` (`poseidon.library` 4): how many there are, or -1 without
  Poseidon. A mouse and a keyboard in the same device show up as two, each with its own emitter.
- `usb_hid_name(i)`, `usb_hid_maker(i)`, `usb_hid_vendor(i)`, `usb_hid_product(i)`: product, manufacturer and IDs.
- `usb_hid_kind(i)`: 1 mouse, 2 keyboard, 0 other (many trackpads give 0).
- `usb_hid_emitter(i)`: its emitter, for `mouse_curve`.
- `mouse_curve(emisor, factores)`: the curve for that emitter, in hundredths (100 = as it arrives). Entry i applies to
  a movement of i units (the longer axis) and the last one from there on; up to 32. `[]` removes it. The fractional
  part is kept for the next movement: with factors below 100, slow movement is not
  lost. It can be changed at any time. `false` if `input.device` does not open or there are already 16 emitters.
- `mouse_curve_events(emisor)`: how many movements have gone through its curve.
- `mouse_curves_off()`: removes the curves from `input.device` (also when the program ends); another `mouse_curve`
  puts them back.
- `mouse_prefs_ticks()`, `mouse_prefs_accel()`, `mouse_prefs_set(ticks, accel)`: the speed (1 the fastest,
  2, 4) and the acceleration from the Input preferences. The previous ones are restored automatically when the program ends.

How it works: USB mice, with a patch on `input.device`'s `BeginIO` that scales a copy of the event
(`hid.class`'s memory is not touched); the Amiga mouse, with an input handler above Intuition. Wheel,
buttons and absolute positions are not touched. When it is removed, if another program has patched `BeginIO` on top, an
8-byte stub is left that passes everything through untouched and is never freed (`mouse_patch_left()` says how many).

### Watching a file: file_notify

Instead of reading a file every so often in case it has changed (the settings in `ENV:` written by a
preferences program), the system notifies you when it changes:

```ruby
ajustes = file_notify("ENV:MiPrograma.prefs")      # also if it does not exist yet; 0 if it cannot
while true
    orden = cx_wait(1000)                           # 7: a watched file changed
    if orden == 7 and file_changed(ajustes)
        leer_ajustes()
    end
end
```

- `file_notify(ruta)`: watches that file (up to 8): returns its number, or 0. `file_changed(n)`: whether it changed since the
  last time it was asked. `file_notify_end(n)`: stops watching it (when the program ends, all of them).
- `cx_wait` wakes up with 7 when one changes; for `mui_wait_event_signals`, `file_notify_signal()`.

### Launching programs: run_program and program_relaunch

- `run_program(orden)`: launches a command line (`"SYS:Prefs/Font"`, with quotes if the path contains spaces) in
  another process, without waiting for it, with input and output to `NIL:`. `false` if it could not start.
- `program_relaunch()`: when the program ends, launches it again, after everything else at the end (including the
  `single_instance` port, so the new copy does not find the old one) and the way it was started: from the Workbench
  with `OpenWorkbenchObject` (3.5 or later: it reads the tooltypes of its icon) or from a Shell with the same
  arguments. Useful for updating itself: replace the executable, call `program_relaunch()` and exit.

### Date and time: clock_* and date_text

```ruby
clock_read()                                   # takes the date and time from the system clock
Print "#{clock_day()}/#{clock_month()}/#{clock_year()} #{clock_hour()}:#{clock_minute()}"
Print date_text("%A %d-%b-%Y %H:%M")           # "Saturday 24-Oct-2026 18:05", in the system language
```

- `clock_read()`: takes the date and time; `clock_year()`, `clock_month()` (1 to 12), `clock_day()`,
  `clock_weekday()` (0 Sunday, 1 Monday ... 6 Saturday), `clock_hour()`, `clock_minute()` and `clock_second()` give
  its parts (those of the last `clock_read`, all from the same moment). No libraries needed.
- `date_text(formato)`: the current date and time using `locale.library`'s `FormatDate`, in the system's language and
  country. Codes: `%A`/`%a` day of the week (long or short), `%B`/`%b` month, `%d` day, `%m` month as a number,
  `%Y`/`%y` year, `%H` hour, `%I` 12-hour clock hour, `%p` AM/PM, `%M` minute, `%S` second, `%w` day of the week as a
  number, `%%`; `locale.library` has more (`%x`, `%X`, `%c`: the date and time as that country writes them). Without
  `locale.library` (a 3.0 without it), those in the list, in English.
- `locale_decimal_point()`, `locale_group_separator()` and `locale_date_order()`: how the user's country writes
  numbers and dates. The decimal and the thousands separators (in English `"."` and `","`, also without
  `locale.library`) and the order of day, month and year in the short date: `"DMY"`, `"MDY"` or `"YMD"`. Note: the
  `españa.country` of Workbench 3.1 and 3.2 has `"'"` for the decimals and `","` for the thousands.

### Translations: tr and @catalog

The strings the user sees can come from a `locale.library` catalog, in their language. The program carries
its strings in its own language, each with a number:

```ruby
@catalog "Tachyon.catalog" 1 "español"   # the catalog, its version (0: any) and the language of the strings

const MSG_SALIR = 3

Main
    Print tr(1, "Hola")                   # "Hello" with the English catalog; "Hola" without a catalog
    Print tr(MSG_SALIR, "Salir")
end
```

- `@catalog "X.catalog" versión "idioma"` (at function level; the language is optional, by default
  `english`): the catalog is opened by the first `tr` (including one in a global) from `PROGDIR:Catalogs/<idioma>/` or
  `LOCALE:Catalogs/<idioma>/`, in the languages the user chose in Preferences. No catalog is looked up for the language of the
  program's own strings. It is closed automatically on exit. With a version other than 0, only a catalog of that
  version is accepted.
- `tr(número, "texto")`: the string for that number in the catalog; the program's one if there is no catalog, it does not have that
  number or there is no `locale.library`. Without `@catalog`, always the program's one.
- `catalog_open("X.catalog", versión)`: opens another catalog in place of the previous one (`false` if there is none: `tr` gives the
  program's strings). `catalog_language()`: the language of the catalog in use, `""` if there is none.
- The catalog is read from its file each time it is opened, not with `OpenCatalog`. `locale.library` keeps the catalogs
  it loads and returns the same one while anyone has it open: a program that updated itself with a new catalog
  kept the old strings until a reboot. This way, a `catalog_open` after writing the new file, or the new program
  on startup, already have the new strings.
- In a `.dashui`, `"tr": N` on an object, window or menu (see `docs/MUI_EDITOR.md`).

Catalogs are built with `tools/catalogo.py`, without FlexCat:

```bash
python3 tools/catalogo.py cd tachyon.dash -o Tachyon.cd       # the strings (and those of its .dashui files and imports)
python3 tools/catalogo.py ct Tachyon.cd --language english --name Tachyon.catalog --version 1.0 \
        [--update english.ct] -o english.ct                    # for translating (--update keeps what is already translated)
python3 tools/catalogo.py catalog english.ct                   # -> Catalogs/english/Tachyon.catalog
```

In the `.ct`, under each `MSG_<número>` goes the translation (empty: the program's string is kept) and, as a
comment, the original. The same escapes work as in a Dash string: `\n`, `\t`, `\"`, `\e`. The catalog comes out in
Latin-1, like the program's strings. The version in the `.ct` (`1.0`) must match that of `@catalog` (`1`).

### No DOS requesters: dos_requesters

```ruby
dos_requesters(false)            # no "Insert volume" requesters or disk errors
h = file_open("NOEXISTE:x", 1005)    # returns 0 straight away, without waiting for a click
dos_requesters(true)             # back as they were
```

With them off, a call that would bring up a requester (a volume that is not there, a disk with errors) simply fails. When
the program ends they come back automatically. Useful for a program that opens paths the user does not choose, such as a browser.

### Base64 to a file: base64_to_file

`base64_to_file(texto, fichero)` writes the bytes of the base64 text to the file (for example, that of a
`data:...;base64,` URL). It skips spaces and line breaks, and the `=` padding may or may not be present. It returns the bytes
written, or -1 if the text is not base64 (in which case it writes nothing) or the file cannot be written.

### CPU per task: cpu_sample

```ruby
if cpu_start()                         # false without EClock or before OS 2.04
    while true
        time_delay(50)                 # one second
        n = cpu_sample()               # the tasks, from the one that took the most CPU to the least
        Print "en uso #{cpu_total() / 10} %"
        for i in (0..n - 1)
            Print "#{cpu_task_load(i)} por mil  #{cpu_task_name(i)}"
        end
    end
end
```

It counts the exact CPU of each task using exec's task-switch hooks and the EClock, like
Michael Sinz's PM. Each sample gives each task's usage since the previous one, in parts per thousand; whatever is not
counted is idle time. For a Shell process, the name is that of its command. Each sample hooks
new tasks and forgets those that ended. A task that already has those hooks from another program is not
touched or counted. A task's count includes the interrupts that arrive while it has the CPU.
`cpu_stop()` removes the hooks; when the program ends they are removed automatically (also if the C calls `exit`).

### Drawing on the Workbench background: desktop_canvas

```ruby
func panel(x, y, w, h)
    gfx_pen(1)
    gfx_text_at(x + 4, y + 12, "CPU #{cpu_total() / 10} %")
end

Main
    c = desktop_canvas(-1, 4, 300, 90)    # top right (-1: flush with the edge)
    if c != 0
        desktop_canvas_on_draw(c, panel)
        desktop_canvas_update(c)           # everything
        while true
            time_delay(50)
            desktop_canvas_update_area(c, 0, 0, 120, 20)   # only where the figure goes
        end
    end
end
```

An area of the Workbench desktop (below the screen's title bar), behind the icons and not receiving
clicks. It works with the Workbench in backdrop mode (icons on the desktop) or without it (the screen
background, where there are no windows), and if the mode is changed while the program is running (Workbench menu >
Backdrop); also with another program as the desktop (Directory Opus 5, Scalos: its backdrop window, the one that
covers the whole screen and is frontmost); on planar and RTG screens (8-bit with a palette, 16, 24 and 32). The coordinates are those of the
desktop; negative ones count from the right or bottom edge. It returns 0 if it cannot (no Workbench screen, out of
memory, or on 16-bit or higher RTG without Picasso96 or CyberGraphX).

The drawing function paints with `gfx_` into a separate bitmap that already has the backdrop underneath:
whatever is not painted lets the backdrop show through. `desktop_canvas_update` calls it and copies to the screen only the rows
that changed. `desktop_canvas_update_area(c, x, y, w, h)` does the same only in that part: the drawing is
clipped to it and only it is compared; whatever changes outside does not appear until another update covers it.
If a window covers the area and goes away, the area repaints itself with whatever was last drawn. Each time the desktop
repaints the area, the canvas picks up again the background that has just been painted: if the Workbench applies its pattern afterwards
(started from WBStartup), the next update already has it underneath. The same applies to
`desktop_canvas_update_area`: that time it also draws where the desktop repainted, even if it falls outside its part.

**Veils that do not cost every time.** A semi-transparent panel over the backdrop used to blend its veil
(`gfx_blend_rect` over the whole canvas) on every draw: on RTG that was half of Trasfondo's time.
`desktop_canvas_veil(c, rgb, alpha)` blends the background underneath with that color once, and again only where the
desktop repaints it; the drawing then starts on top of the already-veiled background. `desktop_canvas_veil_rect(c, x, y, w, h,
rgb, alpha)` adds another veil only in a rectangle that is always there (up to 16; `desktop_canvas_veil` removes them,
so it goes first). With alpha 255 the background is covered by that color: an opaque background that is not painted every
time either. They show up from the next `desktop_canvas_update` on.

**Drawing only what is visible.** Inside the drawing function, `desktop_canvas_drawing(x, y, w, h)` says whether that
rectangle falls in the part being drawn (the whole canvas, or the `desktop_canvas_update_area` area plus what the
desktop repainted): everything else can be skipped, because it would not appear.

In backdrop mode the icons are not touched (they do not flicker): a pixel belongs to an icon if it is neither the screen
background nor what the canvas left, or if it already was one the previous time. The next update fixes the
boxes the Workbench clears when redrawing its icons. Limitation: an icon pixel that has the color of the
backdrop at that point, or that the Workbench paints with the color the canvas has there, is taken as
background and the canvas paints over it.

On freeing (`desktop_canvas_free`, or when the program ends) the area goes back to the Workbench: it is
repainted once, and the icons underneath flicker at that point.

Cost measured in FS-UAE with a 300x90 canvas in 4 colors with icons underneath:

| Machine | Almost everything changes | One figure changes | 120x20 `update_area` |
|---------|------------------|------------------|--------------------------|
| A1200 (planar) | 37 ms | 22 ms | 13 ms |
| 68040 with JIT, 16-bit RTG | 6 ms | 5 ms | 0.6 ms |

On the A1200 the most expensive part is comparing the drawing with the previous one (Chip memory); `update_area` avoids
that. On RTG, with Picasso96, the drawing is read and compared in the screen's format, without converting it, row
by row. Trasfondo measuring every second, on a 68030 without JIT with uaegfx at 16 bits: from 99 % CPU down to 22 % with the
veil and the areas (and from 21.5 % to 15.5 % on the A1200).

## 22. Complete Examples

### Example 1: Hello World with a Window

```
Window HelloWin
    title "Hola Mundo"
    width 300
    height 100
end

Main
    HelloWin.open

    gfx_pen(1)
    gfx_text_at(100, 50, "Hola Amiga!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Example 2: Interactive Counter

```
Window CounterWin
    title "Contador"
    width 200
    height 100
end

const MAX_COUNT = 100

Main
    CounterWin.open

    count = 0

    while count < MAX_COUNT
        gfx_clear()
        gfx_pen(1)
        gfx_text_at(20, 50, "Contador: #{count}")

        count = count + 1
        time_delay(25)      # Half a second
    end

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Example 3: Joystick Movement

```
Window GameWin
    title "Joystick Demo"
    width 320
    height 200
end

struct Player
    x: Int = 160
    y: Int = 100
    size: Int = 10

    func update()
        dx = joy_x(0)
        dy = joy_y(0)
        self.x = self.x + dx * 2
        self.y = self.y + dy * 2

        # Screen limits
        if self.x < 0
            self.x = 0
        end
        if self.x > 310
            self.x = 310
        end
        if self.y < 0
            self.y = 0
        end
        if self.y > 190
            self.y = 190
        end
    end

    func draw()
        gfx_pen(2)
        gfx_rect(self.x, self.y, self.x + self.size, self.y + self.size)
    end
end

Main
    GameWin.open

    gfx_rgb(2, 0, 15, 0)    # Green for the player

    player = Player(160, 100, 10)

    while not window_check_close()      # until the close button is clicked
        gfx_clear()

        player.update()
        player.draw()

        wait_vblank()
    end
end
```

### Example 4: Drawing Graphics

```
Window ArtWin
    title "Arte Amiga"
    width 320
    height 256
end

Main
    ArtWin.open

    # Set up the palette
    gfx_rgb(0, 0, 0, 4)         # Dark blue background
    gfx_rgb(1, 15, 15, 15)      # White
    gfx_rgb(2, 15, 8, 0)        # Orange
    gfx_rgb(3, 15, 0, 0)        # Red
    gfx_rgb(4, 0, 15, 0)        # Green

    gfx_clear()

    # Frame
    gfx_pen(1)
    gfx_box(5, 5, 315, 251)

    # Sun
    gfx_pen(2)
    gfx_circle_fill(260, 50, 30)

    # Mountains
    gfx_pen(4)
    gfx_poly_begin(0, 200)
    gfx_poly_add(80, 120)
    gfx_poly_add(160, 200)
    gfx_poly_end()

    gfx_poly_begin(100, 200)
    gfx_poly_add(200, 100)
    gfx_poly_add(300, 200)
    gfx_poly_end()

    # Text
    gfx_pen(1)
    gfx_text_at(110, 240, "Amiga Forever!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Example 5: File System

```
Main
    # Write a file
    handle = file_open("RAM:test.txt", 1006)     # new file
    if handle != 0
        file_write_line(handle, "Linea 1")
        file_write_line(handle, "Linea 2")
        file_write_line(handle, "Linea 3")
        file_close(handle)
        Print "Archivo escrito"
    end

    # Read a file
    handle = file_open("RAM:test.txt", 1005)     # read
    if handle != 0
        Print "Contenido:"
        bytes = 0
        while not file_eof(handle)
            byte = file_read_byte(handle)
            bytes = bytes + 1
        end
        Print "#{bytes} bytes"
        file_close(handle)
    end

    # Check that it exists
    if file_exists("RAM:test.txt")
        tamano = file_size("RAM:test.txt")
        Print "Tamano del archivo:"
        Print tamano
    end
end
```

### Example 6: Sound and Music

```
Window SoundWin
    title "Demo Audio"
    width 200
    height 100
end

Main
    SoundWin.open

    # Load sounds
    sound_load(0, "sounds/beep.8svx")
    sound_load(1, "sounds/boom.8svx")

    # Load music
    music_load("mods/intro.mod")
    music_volume(48)
    music_play()

    gfx_pen(1)
    gfx_text_at(50, 50, "Musica sonando...")

    EventLoop
        On Close
            music_stop()
            music_free()
            Stop
        end
    end
end
```

---

## 23. Quick Reference

### Basic Syntax

| Construct | Syntax |
|--------------|----------|
| Variable | `nombre = valor` |
| Global variable | `var nombre: Tipo = valor` (outside `Main` and functions) |
| Constant | `const NOMBRE = valor` |
| Function | `func nombre(params) ... end` |
| Struct | `struct Nombre ... end` |
| Enum | `enum Nombre ... end` or `enum Nombre A, B, C end` |
| Lambda | `fn(x) -> x * 2` or `fn(x) ... end` |
| If | `if cond ... end` |
| If/Else | `if cond ... else ... end` |
| While | `while cond ... end` |
| For Range | `for i in (a..b) ... end` |
| For Each | `for x in array ... end` (also the characters of a String) |
| For with step | `for i in (a..b step s) ... end`; `(10..1)` counts down |
| Exit / skip | `break`, `continue` (inside `while`/`for`) |
| Wait | `Wait 2` (seconds) |
| Window | `Window Nombre ... end` |
| Main | `Main ... end` |
| EventLoop | `EventLoop ... end` |
| On Close | `On Close ... end` |
| On Key | `On Key "ESC" ... end` (also `"a"`, `0x4C` or no key = any) |
| Comment | `# comentario` |

### Functions by Category

Full list with parameters: [docs/BUILTINS.en.md](BUILTINS.en.md). All of them are implemented.

| Category | Count | Examples |
|-----------|----------|----------|
| Basic graphics | 29 | `gfx_pen`, `gfx_line`, `gfx_rect`, `gfx_circle`, `gfx_flood` |
| Advanced graphics | 43 | `sprite_*`, `soft_sprite_*`, `bitmap_*`, `bob_*`, `copper_*` |
| Input and screens | 30 | `key_*`, `mouse_*`, `joy_*`, `screen_open`, `check_lmb`, `event_window` |
| GadTools | 19 | `gt_button`, `gt_slider`, `gt_string`, `gt_event` |
| Menus | 10 | `menu_title`, `menu_item`, `menu_sub`, `menu_id` |
| ASL requesters | 5 | `file_open_dialog`, `file_save_dialog`, `file_fullpath` |
| ReAction | 79 | `ra_window_*`, `ra_add_*`, `ra_get_*`, `ra_canvas_*` |
| System and memory | 28 | `mem_*`, `time_*`, `random_*`, `arena_*`, `peek_*`, `poke_*` |
| Files (DOS) | 26 | `file_*`, `dir_*`, `console_read`, `console_write`, `base64_to_file`, `dos_requesters` |
| Buffers | 10 | `buffer_alloc`, `buffer_get_byte`, `buffer_copy` |
| Text | 18 | `str_find`, `str_split`, `str_replace`, `file_read_text` |
| Network (TCP and UDP) | 26 | `net_connect`, `net_send`, `net_recv`, `net_listen`, `net_accept`, `net_udp_open`, `net_udp_send`, `net_udp_recv` |
| TLS (AmiSSL) | 9 | `tls_connect`, `tls_send`, `tls_recv` |
| Fonts and colors | 9 | `font_open`, `font_use`, `font_text_width`, `color_pen` |
| Transparency and gradients | 3 | `gfx_blend_rect`, `gfx_gradient_rect`, `gfx_pixel_rgb` |
| RGB images from a buffer | 2 | `gfx_rgb_draw`, `gfx_rgb_draw_scaled` |
| Tasks, CPU and desktop | 22 | `task_start`, `cpu_sample`, `desktop_canvas`, `break_check`, `single_instance` |
| Commodity (Exchange) | 5 | `tooltype`, `cx_broker`, `cx_hotkey`, `cx_command`, `cx_wait` |
| Watched files and programs | 6 | `file_notify`, `file_changed`, `run_program`, `program_relaunch` |
| Date, time and version | 13 | `clock_read`, `clock_year`, `clock_hour`, `date_text`, `locale_decimal_point`, `program_version` |
| Translations (catalogs) | 3 | `tr`, `catalog_open`, `catalog_language` |
| A curve for each mouse | 14 | `mouse_curve`, `mouse_curves_off`, `mouse_prefs_set`, `usb_hid_read`, `usb_hid_emitter` |
| Disks, network, WiFi and temperature | 22 | `disks_read`, `disk_kb`, `net_ifs_read`, `net_if_bytes_in`, `net_drivers_read`, `net_driver_read`, `wifi_read`, `wifi_read_device`, `wifi_signal`, `pistorm_temperature` |
| Images (datatypes) | 8 | `image_load`, `image_draw`, `image_scale`, `image_from_rgb` |
| Arguments, clicks and clock | 5 | `arg_count`, `arg`, `click_x`, `click_y`, `time_ms` |
| Compression (zlib) | 3 | `inflate`, `deflate`, `crc32` |
| UTF-8 | 8 | `utf8_next`, `utf8_prev`, `utf8_code`, `utf8_char`, `utf8_length`, `utf8_to_latin1`, `latin1_to_utf8`, `utf8_check` |
| Comparing and searching in a buffer | 3 | `buffer_equals`, `buffer_find_byte`, `buffer_find_any` |
| Double and text | 2 | `str_from_double`, `str_to_double` |
| Double math | 20 | `sqrt`, `pow`, `exp`, `log`, `sin`, `atan2`, `floor`, `round`, `fmod`, `abs`, `is_nan` |
| Audio | 21 | `sound_*`, `music_*`, `tone_play` |
| Intuition | 52 | `window_*` (also `window_border_*`), `screen_font_height`, `button_*`, `listview_*`, `dialog_file` |
| RTG | 21 | `rtg_*` |
| MUI | 85 | `mui_app_begin`, `mui_window_begin`, `mui_button`, `mui_list`, `mui_canvas`, `mui_timer`, `mui_wait_event` |
| **Total** | **659** | |

### Standard Amiga Colors

| Index | Typical Color |
|--------|--------------|
| 0 | Background (black/gray) |
| 1 | Text (white) |
| 2 | Highlight |
| 3 | Shadow |

### Common Key Codes

| Key | Code |
|-------|--------|
| ESC | 69 |
| RETURN | 68 |
| SPACE | 64 |
| UP | 76 |
| DOWN | 77 |
| LEFT | 79 |
| RIGHT | 78 |

---

## Appendix: Common Errors

### Error: Undefined variable
```
# Wrong
Print x     # x does not exist

# Right
x = 10
Print x
```

### Error: Missing 'end'
```
# Wrong
if x > 0
    Print "positivo"
# Missing end

# Right
if x > 0
    Print "positivo"
end
```

### Error: Wrong type
```
# Wrong
s = "hola"
s = 5               # Cannot assign a int to 's', which holds a string

# Right
s = "hola"
s = "5"             # or "#{n}" to put a number in the string
n = 5               # or a new variable for the number
```

A variable keeps the type of its first assignment. Adding a number to a string does work:
`"hola" + 5` gives `"hola5"`.

---

**Dash Language** - Created to revive the magic of programming on the Amiga.
