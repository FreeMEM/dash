# D.A.S.H. Documentation

*English | [Castellano](DOCUMENTACION_LENGUAJE.md)*

> **D.A.S.H.** — *Development Amiga Synthesis Hub*

This is the language guide: what it is, how you work with it, and a tour of everything it offers, with
examples. The full reference for each function is in the [reference manual](MANUAL_REFERENCIA.en.md),
the list of builtins in [BUILTINS.md](BUILTINS.en.md) and the cheat sheet in [QUICK_REFERENCE.md](QUICK_REFERENCE.en.md).

## 1. What Dash is

Dash is a high-level language for the **Commodore Amiga** that is translated to C and compiled with GCC into a
native m68k executable. There is no interpreter and no virtual machine: the program is as fast as one written in C,
but without pointers, without `includes` and without freeing memory by hand.

- **Clean syntax**, in the style of Ruby and Python: blocks that end in `end`, types that are inferred.
- **The Amiga API at your fingertips:** windows, graphics, sprites, copper, blitter, sound, files, networking, and three
  ways to build user interfaces (GadTools, ReAction and MUI). There are 617 ready-made functions (builtins), listed in
  [BUILTINS.md](BUILTINS.en.md).
- **Automatic, lightweight memory management:** no garbage collector and no pauses (section 4.10).
- **For a real Amiga:** it runs on an A500 with a 68000 and Kickstart 3.0; anything that needs more
  (MUI 5, TLS) says so.

Programs made with Dash: [Tachyon](https://github.com/FreeMEM/tachyon) (a web browser with MUI),
[Trasfondo](https://github.com/FreeMEM/trasfondo) (a system monitor on the Workbench backdrop) and Ratonera
(mouse acceleration curves, in development).

You write code on a PC (Linux or macOS) and test it in an emulator or on the Amiga.

## 2. How it works

```
programa.dash → parser (Lark) → AST → analysis → C generator → GCC m68k → Amiga executable
```

- The compiler (`compiler/`) is written in Python. It reads the program, checks types and names, and writes
  **a single C file** with the program and the parts of the runtime it uses (memory, strings, graphics...).
- GCC (`m68k-amigaos-gcc`, by bebbo) compiles it with `-O2` and produces the executable in Hunk format.
- The executable opens the libraries it needs, requests its stack and, on exit (including on error), closes everything
  it opened.

## 3. Getting started

```bash
./dash examples/hola.dash -o bin/hola        # compile
python3 tools/emu_run.py bin/hola             # run it in FS-UAE without a window and see its output
```

`./dash` options: `-O0` (no optimization), `--small` (`-Os`), `--fpu` (68020 + 68881), `--cpu 68040` (code for that CPU or better), `--stack N` (minimum
stack), `--memcheck` (memory checking), `--profile` (calls and time per function on exit),
`--debug` (for gdb or VS Code: `-O0 -g` and the `.dash` line numbers), `--multifile` (one C file per module), `-q` (only
warnings, errors and the result) and `--no-hunk` (skips the ELF-to-Hunk step; bebbo's GCC already writes Hunk).
`DASH_TOOLCHAIN` says where GCC is if it is not in `/opt/amiga`, and `DASH_CFLAGS` adds options to GCC. Setting
up the environment (GCC for Amiga, emulator, MUI SDK) is covered in [INSTALACION.md](INSTALACION.en.md).

A minimal program:

```ruby
Main
    Print "Hola, Amiga"
end
```

## 4. The language

### 4.1 Structure of a program

```ruby
import "lib/utilidades.dash"   # modules

const MAX = 100                # constants
var total: Int = 0             # global variable (typed): functions can read and change it
enum Estado
    PARADO
    ANDANDO
end
struct Punto
    x: Int
    y: Int
end
Window Ventana                 # declared windows
    title "Mi programa"
    width 320
    height 200
end

func doble(n: Int) -> Int      # functions
    return n * 2
end

Main                           # entry point
    Print doble(MAX)
end
```

Comments start with `#`. There is no `;`: one statement per line. An enum also fits on one line:
`enum Color ROJO, VERDE, AZUL end` (the commas are optional; `= N` sets the value).

### 4.2 Variables and types

The first assignment declares the variable; its type is inferred from the value.

| Type | Example | Notes |
|---|---|---|
| `Int` | `n = 42`, `m = 0xFF`, `b = 0b1010`, `d = $DFF000` | 32-bit signed |
| `Float` | `v = 1.5` | its own floating point (fast on a 68000); `--fpu` uses the FPU |
| `Fixed` | `f = Fixed(1.5)` | 16.16 fixed point: decimals at integer speed on a 68000 |
| `String` | `s = "Dash"` | strings (Latin-1 on the Amiga) |
| `Bool` | `ok = true` | `true`, `false` (that is how `Print` and strings show them) |
| lists | `l = [1, 2, 3]`, `var t: [String] = []` | see 4.7 |
| dictionaries | `d = {"a": 1}` | `{String: T}`, see 4.7 |
| structs | `p = Punto(10, 20)` | see 4.8 |
| `nil` | `var siguiente: Nodo = nil` | "nothing" for structs, lists and strings |

`var nombre: Tipo = valor` declares with an explicit type (needed to start with `nil` or an empty list).
Conversions: `Int(x)`, `Float(n)`, `Fixed(n)`, `Int("42")`.

### 4.3 Operators

```ruby
a + b   a - b   a * b   a / b   a % b      # arithmetic (integer / and % with Int)
a == b  a != b  a < b   a > b   a <= b  a >= b
x and y   x or y   not x
a & b   a | b   a ^ b   ~a   a << n   a >> n  # integer bitwise ops (Python precedence)
"Hola " + nombre                            # string concatenation
"abc" < "abd"                               # strings are compared by content
```

### 4.4 Control flow

```ruby
if n > 10
    Print "grande"
elif n > 5
    Print "mediano"
else
    Print "pequeño"
end

while vidas > 0
    vidas = vidas - 1
end

for i in (1..10)             # 1 to 10
end
for i in (10..1)             # counting down
end
for i in (0..100 step 5)     # in steps of 5
end
for i in (100..0 step -5)    # counting down with step: negative
end
for nombre in nombres        # each element of a list
end
```

`break` leaves the loop and `continue` moves on to the next iteration. Variables created inside a block only
exist inside it; those from outside can be read and changed.

### 4.5 Functions

```ruby
func suma(a, b)              # no types: inferred from how it is used
    return a + b
end

func area(ancho: Int, alto: Int) -> Int
    return ancho * alto
end

doble = fn(x) -> x * 2       # anonymous function (lambda)
triple = fn(x)               # also with several lines
    return x * 3
end
func aplica(f: Func, v: Int) -> Int
    return f(v)
end
```

Parameter and return types: `Int`, `Float`, `Fixed`, `String`, `Bool`, `Array`, `[T]`, `{String: T}`,
`Pointer`, `Func`, `Void`, a struct or an enum; `return` is checked against the declared type (a string
will not do for a `Bool`, nor one struct for another). Functions can be recursive and can be passed as values
(`aplica(doble, 4)`); a function stored in a variable (`g = doble`) is called with `g(x)`. A lambda cannot
use local variables from outside (globals are fine): there are no closures. In a module, those starting
with `_` are private.

### 4.6 Strings

```ruby
s = "Hola, " + nombre
m = "Tienes #{puntos * 2} puntos"   # interpolation: any expression (quotes inside: \")
n = s.length
c = s[0]                            # one character
trozo = s[2:5]                      # also s[:5] and s[2:]
p = str_find(s, "la")               # position or -1
t = str_upper(str_trim(s))
s = s + "más"                       # appending is linear: building strings in a loop is cheap
```

More: `str_replace`, `str_starts`, `str_ends`, `str_lower`, `str_code`, `str_char`, `str_to_int`,
`str_from_int`, `file_read_text`, `file_write_text` (manual, strings section).

### 4.7 Lists and dictionaries

```ruby
numeros = [3, 1, 4]
numeros[0] = 9
total = numeros.length
parte = numeros[1:3]
todos = numeros + [1, 5]            # new list

var pendientes: [String] = []       # list with an element type
pendientes.push("leer")
pendientes.insert(0, "abrir")
ultimo = pendientes.pop()
pendientes.remove(0)

edades = {"Ana": 30, "Luis": 41}    # dictionary from string to value
edades["Eva"] = 25
if edades.has("Ana")
    Print edades["Ana"]
end
for clave in edades.keys()
    Print clave
end
n = edades.get("Pepe", 0)           # the value, or the default if it is missing
edades.remove("Luis")
```

A missing key gives `0` (or `nil` for strings and objects); `d.get(k, defecto)` looks it up only once (with
objects, the default can only be `nil`). `l.clear()` and `d.clear()` empty them, and `d.length` counts the keys.
Lists check their indices: outside the list, reading gives `0` (or `nil`) and writing does nothing (with
`--debug`, the debugger stops there). A list of structs, strings or lists owns its elements.

### 4.8 Structs and enums

```ruby
struct Enemigo
    x: Int = 0
    vida: Int = 100

    func mueve(dx: Int)
        self.x = self.x + dx
    end
end

e = Enemigo(10, 50)
e.mueve(5)
var lista: [Enemigo] = []
lista.push(e)
lista[0].vida = 80                  # a field of an element
lista[0].mueve(1)                   # and its methods

struct Nodo
    valor: Int
    siguiente: Nodo = nil
    weak padre: Nodo                # points without retaining: parents without memory cycles
end

enum Estado
    PARADO = 0
    ANDANDO = 1
end
st = Estado.ANDANDO
```

### 4.9 Modules

```ruby
import "lib/geometria.dash"         # the module's public functions, structs, constants and enums
import "ventanas.dashui"            # MUI windows made with the visual editor (section 6)
```

Paths are relative to the importing file (or to the project root). `lib/amiga/` comes with ready-made modules:
audio, blitter, copper, dos, graphics, IFF, intuition, memory, RTG, sprites, double buffering.

### 4.10 Memory

Dash has no garbage collector. It frees memory like this:

- **Strings:** each variable owns its string. Temporary strings (`"a" + b`) are freed at the end of the loop
  iteration, the event or the function.
- **Lists and structs:** with a reference count; they are freed when nothing uses them any more. Cycles (a child
  pointing to its parent) are avoided with `weak` fields; otherwise they are freed on exit.
- **Everything** comes from an exec pool that is wiped when the program ends, no matter what.

`./dash --memcheck` builds a version that reports use after free, double frees and whatever is
still alive on exit. For special cases: `retain`, `release`, `refcount` and arenas (`arena_*`).

## 5. The Amiga

### 5.1 Windows and events

```ruby
Window Principal
    title "Dash"
    width 320
    height 200
end

Main
    Principal.open
    gfx_pen(1)
    gfx_text_at(20, 30, "Pulsa ESC")
    EventLoop
        On Key "ESC"
            Stop
        end
        On Close
            Stop
        end
    end
end
```

`On Key` (one key, or any key if nothing is given), `On Close`, `On Gadget` (gadgets by number), `On Menu` (menus),
`On Click` (left button in the window: `click_x()`, `click_y()`) and `On Timer 100` (every 100 ms; takes a
number or a variable). There are also windows created from code
(`window_create`, by number; the `EventLoop` handles them and `event_window()` tells which one), custom screens
(`screen_open`) and RTG.

GadTools gadgets are positioned from the inside of the window, excluding the borders. To make them fit:
`window_create` with flag 8 takes the inner width and height; `window_border_top/bottom/left/right` give
the borders, and `screen_font_height` and `screen_font_text_width` measure with the screen font.

### 5.2 Graphics, sprites and animation

`gfx_*` (points, lines, rectangles, circles, polygons, text), colors (`gfx_rgb`, `color_pen`), disk
fonts (`font_open`), images via datatypes (`image_load`, `image_draw`), bitmaps, BOBs with the blitter, hardware
and software sprites, copper lists and double buffering.

### 5.3 Input, sound and files

Keyboard (`key_*`), mouse (`mouse_*`), joystick (`joy_*`). IFF 8SVX sounds on all four channels (`sound_*`),
tones (`tone_play`) and ProTracker music (`music_*`). Files and directories (`file_*`, `dir_*`), ASL requesters,
Shell arguments (`arg_count`, `arg`).

### 5.4 Networking

Through `bsdsocket.library` (Roadshow, MiamiDx, AmiTCP...):

- TCP client (`net_connect`, `net_send`, `net_recv`, `net_close`) and server (`net_listen`, `net_accept`,
  `net_peer`, `net_port`).
- UDP (`net_udp_open`, `net_udp_send`, `net_udp_recv`, `net_udp_from`), including broadcast to the whole local network
  (`"255.255.255.255"`).
- TLS with AmiSSL 5.1 or later (`tls_connect`, 68020+); resumes the session with the same server.
- Non-blocking connect (`net_connect_start`, `tls_connect_start`) and `net_signal()`, which wakes the program up
  when something arrives.
- Networking also from a `task_start` task: only one task uses it at a time.
- Network monitoring: Roadshow interfaces (`net_ifs_read`), SANA-II drivers with any stack (`net_drivers_read`,
  `net_driver_read`) and WiFi signal strength (`wifi_read`, `wifi_read_device`).

There is no HTTP builtin: each program writes its own on top of TCP or TLS. Nor are there raw sockets or raw SANA-II
frames.

```ruby
s = net_connect("aminet.net", 80, 10000)
if s >= 0
    net_send(s, "HEAD / HTTP/1.0\r\nHost: aminet.net\r\n\r\n")
    respuesta = net_recv(s, 4096, 10000)
    Print respuesta
    net_close(s)
end
```

### 5.5 System and tasks

- `break_check()` tells whether Ctrl-C (the Shell's "Break") has arrived; `single_instance("Nombre")` allows only one copy
  of the program to run.
- `task_start(f, arg)` runs a `@native` function in another process (C only); `task_done`, `task_result` and
  `task_free` keep track of it.
- `cpu_start()` and `cpu_sample()` measure the CPU used by each task in the system (`cpu_task_name`, `cpu_task_load`).
- `desktop_canvas(x, y, w, h)` draws on a region of the Workbench desktop, behind the icons, with a
  Dash function, like the MUI drawing area. It also works with Directory Opus 5 or Scalos as the desktop.
- Commodity: `cx_broker` registers the program in Exchange, `cx_hotkey` gives it a hotkey and `cx_wait` waits for
  commands without using CPU (`cx_command`). `tooltype("NOMBRE", defecto)` reads a tooltype from the icon or a
  Shell argument.
- `file_notify(ruta)` reports when a file changes (`file_changed`; `cx_wait` wakes up with 7).
  `run_program(orden)` launches another program without waiting and `program_relaunch()` restarts this one when it ends.
- Mounted volumes and their free space: `disks_read`, `disk_name`, `disk_kb`, `disk_free_kb`.
- Mouse: `mouse_curve` sets an acceleration curve for each mouse (including Poseidon USB mice, `usb_hid_*`);
  `mouse_prefs_*` changes the system speed.

### 5.6 Date, version and languages

- `clock_read()` reads the time; `clock_year()`, `clock_month()`... give each part, and `date_text("%d-%m-%Y")` writes it
  in the system language (`FormatDate` from `locale.library`).
- `@version "Mi programa 1.2"` sets the `$VER:` string read by `C:Version`; `program_version()` returns it.
- Translations with `locale.library` catalogs: `@catalog "Prog.catalog" 1` and `tr(1, "Hola")` (the catalog
  text in the user's language or, if there is none, the program's own). `tools/catalogo.py` extracts the strings
  and builds the `.catalog` without FlexCat; in a `.dashui` the strings carry `"tr"`.

## 6. Graphical user interfaces

| | GadTools | ReAction | MUI |
|---|---|---|---|
| System | AmigaOS 3.0+ | AmigaOS 3.2 (3.5+) | MUI 3.8 or 5 installed |
| CPU | 68000 | 68000 | 68020+ (MUI 5) |
| Layout | positions by hand | automatic | automatic |
| In Dash | gadgets by number (`button_create`...) + `On Gadget`; or `gt_*` | `ra_*` | `mui_*` |
| For | utilities, games with a panel | dialogs and forms | large applications |

**MUI** is the most complete: windows that adapt on their own, tabs, lists, menus, images and its own drawing area
painted by a Dash function (`mui_canvas`; it knows where the pointer is with `mui_canvas_on_move` and repaints
just one region with `mui_canvas_update_area`):

```ruby
const ID_HOLA = 1

Main
    if mui_app_begin("Hola", "HOLA") == 0
        Print "Hace falta MUI"
    else
        win = mui_window_begin("Hola MUI", 1)
            mui_text("Bienvenido")
            boton = mui_button("_Saluda")
        mui_window_end()
        mui_on_press(boton, ID_HOLA)
        mui_window_open(win)
        while true
            ev = mui_wait_event()
            if ev == -1
                break
            end
            if ev == ID_HOLA
                Print "Hola"
            end
        end
        mui_app_end()
    end
end
```

**Visual editor:** MUI windows can also be drawn with the mouse in VS Code (extension in
`editor/vscode/`). They are saved in a `.dashui` file that the program imports; each window provides a function that
builds it and returns its objects:

```ruby
import "navegador.dashui"

Main
    mui_app_begin("Navegador", "NAVEGADOR")
    v = Navegador_create()          # v.window, v.url, v.pagina...
    mui_window_open(v.window)
    ...
end
```

API design: [MUI_DISEÑO.md](MUI_DISEÑO.en.md); format and editor: [MUI_EDITOR.md](MUI_EDITOR.en.md).

## 7. C from Dash

For anything without a builtin:

```ruby
@extern("milib.library")            # a function from a system library
func MiFuncion(x: Int) -> Int

@native func peek(addr: Pointer) -> Int
"""
    return (LONG)*(volatile UBYTE *)addr;
"""
end
```

`@header "#include <x.h>"` adds headers, `@link "lib/x.c"` links a C file, object file or library, `@c """ ... """
end` inserts free-form C (for example functions that call into Dash), `@stack N` requests a minimum stack and
`@workbench_output "NIL:"` avoids the console window when started from the Workbench (anything written is lost),
`@version "Prog 1.2"` sets the version and `@catalog "Prog.catalog" 1` the language catalog (section 5.6).
`@native(borrow) func` indicates that the C code only uses its arguments during the call (saves copying them).

## 8. Tools

- **Emulator:** `tools/emu_run.py` runs programs in FS-UAE without a window and returns their output; with
  `--screenshot` it takes a screenshot of the Amiga screen. With `--debug` it talks to the emulator's
  debugger when the program calls `debug_break()` (registers, memory, single-stepping).
- **Tests:** `python3 tests/run_tests.py` (with `--emu`, `--emu-a500` and `--emu-32` it runs them on an A1200,
  an A500 and an A1200 with AmigaOS 3.2; `--memcheck` with memory checking).
- **Benchmarks:** `tools/bench.py` (speed, memory and size on emulated A500 and A1200).
- **VS Code** (`editor/vscode/`, version 0.2.3, see [INSTALACION.md](INSTALACION.en.md)): errors as you type,
  completion, go to definition, compile and run in the emulator, debug with F5 (also on a real Amiga
  over the network) and the MUI visual editor. Video tutorial: https://youtu.be/_UTJ_0s3xLc
- **Catalogs:** `tools/catalogo.py` (section 5.6).

## 9. The generated C

A Dash program is a single C file (`build/programa.c`, or one per module with `--multifile`): first the runtime
it uses, then its structs and functions (`static`) and finally `main`. It is readable: the program's names are
preserved. See the equivalence table in the [manual](MANUAL_REFERENCIA.en.md).

## 10. Program requirements

- Kickstart 3.0 or later (exec memory pools) and a 68000; each program requests 16 KB of stack (32 KB if it uses MUI).
- MUI 5 and TLS (AmiSSL 5.1 or later) need a 68020 or better; ReAction needs AmigaOS 3.2 (or 3.5+).
- The program's strings are written in UTF-8 and reach the Amiga as Latin-1.

## 11. What it does not have

- Classes with inheritance (there are structs with methods) or macros: these are open questions.
- Closures: a lambda cannot see local variables from outside.
- `export`: not needed, everything is public except what starts with `_` (decision made).
- An HTTP builtin, raw sockets and raw SANA-II frames.
