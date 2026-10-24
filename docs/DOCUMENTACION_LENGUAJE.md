# Documentación de D.A.S.H.

> **D.A.S.H.** — *Development Amiga Synthesis Hub*

Esta es la guía del lenguaje: qué es, cómo se trabaja con él y un recorrido por todo lo que tiene, con
ejemplos. La referencia completa de cada función está en el [manual de referencia](MANUAL_REFERENCIA.md),
la lista de builtins en [BUILTINS.md](BUILTINS.md) y la chuleta en [QUICK_REFERENCE.md](QUICK_REFERENCE.md).

## 1. Qué es Dash

Dash es un lenguaje de alto nivel para el **Commodore Amiga** que se traduce a C y se compila con GCC a un
ejecutable nativo m68k. No hay intérprete ni máquina virtual: el programa es tan rápido como uno escrito en C,
pero sin punteros, sin `includes` y sin liberar memoria a mano.

- **Sintaxis clara**, al estilo de Ruby y Python: bloques que acaban en `end`, tipos que se deducen.
- **La API del Amiga a mano:** ventanas, gráficos, sprites, copper, blitter, sonido, ficheros, red, y tres
  formas de hacer interfaces (GadTools, ReAction y MUI). Son 609 funciones ya hechas (builtins), en
  [BUILTINS.md](BUILTINS.md).
- **Memoria automática y ligera:** sin recolector de basura ni pausas (sección 4.10).
- **Para un Amiga de verdad:** funciona en un A500 con 68000 y Kickstart 3.0; lo que necesita más
  (MUI 5, TLS) lo dice.

Programas hechos con Dash: [Tachyon](https://github.com/FreeMEM/tachyon) (un navegador con MUI),
[Trasfondo](https://github.com/FreeMEM/trasfondo) (un monitor del sistema en el fondo del Workbench) y Ratonera
(curvas de aceleración del ratón, en desarrollo).

Se programa en un PC (Linux o macOS) y se prueba en un emulador o en el Amiga.

## 2. Cómo funciona

```
programa.dash → parser (Lark) → AST → análisis → generador de C → GCC m68k → ejecutable Amiga
```

- El compilador (`compiler/`) está escrito en Python. Lee el programa, comprueba tipos y nombres, y escribe
  **un solo fichero C** con el programa y la parte del runtime que usa (memoria, textos, gráficos...).
- GCC (`m68k-amigaos-gcc`, de bebbo) lo compila con `-O2` y genera el ejecutable en formato Hunk.
- El ejecutable abre las librerías que necesita, pide su pila y, al salir (también por error), cierra todo lo
  que abrió.

## 3. Primeros pasos

```bash
./dash examples/hola.dash -o bin/hola        # compilar
python3 tools/emu_run.py bin/hola             # ejecutarlo en FS-UAE sin ventana y ver su salida
```

Opciones de `./dash`: `-O0` (sin optimizar), `--small` (`-Os`), `--fpu` (68020 + 68881), `--stack N` (pila
mínima), `--memcheck` (comprobación de memoria), `--profile` (llamadas y tiempo de cada función al salir),
`--debug` (para gdb o VS Code: `-O0 -g` y las líneas del `.dash`), `--multifile` (un C por módulo), `-q` (solo
avisos, errores y el resultado) y `--no-hunk` (sin el paso de ELF a Hunk; el GCC de bebbo ya escribe Hunk).
`DASH_TOOLCHAIN` indica dónde está el GCC si no es `/opt/amiga`, y `DASH_CFLAGS` añade opciones a GCC. La
instalación del entorno (GCC para Amiga, emulador, SDK de MUI) está en [INSTALACION.md](INSTALACION.md).

Un programa mínimo:

```ruby
Main
    Print "Hola, Amiga"
end
```

## 4. El lenguaje

### 4.1 Estructura de un programa

```ruby
import "lib/utilidades.dash"   # módulos

const MAX = 100                # constantes
var total: Int = 0             # variable global (con tipo): las funciones la leen y la cambian
enum Estado
    PARADO
    ANDANDO
end
struct Punto
    x: Int
    y: Int
end
Window Ventana                 # ventanas declaradas
    title "Mi programa"
    width 320
    height 200
end

func doble(n: Int) -> Int      # funciones
    return n * 2
end

Main                           # punto de entrada
    Print doble(MAX)
end
```

Los comentarios empiezan con `#`. No hay `;`: una instrucción por línea. Un enum también cabe en una línea:
`enum Color ROJO, VERDE, AZUL end` (las comas son opcionales; `= N` da el valor).

### 4.2 Variables y tipos

La primera asignación declara la variable; su tipo se deduce del valor.

| Tipo | Ejemplo | Notas |
|---|---|---|
| `Int` | `n = 42`, `m = 0xFF`, `b = 0b1010`, `d = $DFF000` | 32 bits con signo |
| `Float` | `v = 1.5` | coma flotante propia (rápida en 68000); `--fpu` usa la FPU |
| `Fixed` | `f = Fixed(1.5)` | coma fija 16.16: decimales a velocidad de entero en un 68000 |
| `String` | `s = "Dash"` | textos (Latin-1 en el Amiga) |
| `Bool` | `ok = true` | `true`, `false` (así se escriben con `Print` y en los textos) |
| listas | `l = [1, 2, 3]`, `var t: [String] = []` | ver 4.7 |
| diccionarios | `d = {"a": 1}` | `{String: T}`, ver 4.7 |
| structs | `p = Punto(10, 20)` | ver 4.8 |
| `nil` | `var siguiente: Nodo = nil` | "nada" para structs, listas y textos |

`var nombre: Tipo = valor` declara con tipo explícito (hace falta para empezar con `nil` o una lista vacía).
Conversiones: `Int(x)`, `Float(n)`, `Fixed(n)`, `Int("42")`.

### 4.3 Operadores

```ruby
a + b   a - b   a * b   a / b   a % b      # aritmética (/ y % enteros con Int)
a == b  a != b  a < b   a > b   a <= b  a >= b
x and y   x or y   not x
a & b   a | b   a ^ b   ~a   a << n   a >> n  # bits de enteros (precedencia de Python)
"Hola " + nombre                            # concatenar textos
"abc" < "abd"                               # los textos se comparan por su contenido
```

### 4.4 Control de flujo

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

for i in (1..10)             # 1 a 10
end
for i in (10..1)             # hacia abajo
end
for i in (0..100 step 5)     # de 5 en 5
end
for i in (100..0 step -5)    # hacia abajo con step: negativo
end
for nombre in nombres        # cada elemento de una lista
end
```

`break` sale del bucle y `continue` pasa a la siguiente vuelta. Las variables creadas dentro de un bloque solo
existen dentro de él; las de fuera se pueden leer y cambiar.

### 4.5 Funciones

```ruby
func suma(a, b)              # sin tipos: se deducen al usarla
    return a + b
end

func area(ancho: Int, alto: Int) -> Int
    return ancho * alto
end

doble = fn(x) -> x * 2       # función anónima (lambda)
triple = fn(x)               # también con varias líneas
    return x * 3
end
func aplica(f: Func, v: Int) -> Int
    return f(v)
end
```

Tipos de parámetro y retorno: `Int`, `Float`, `Fixed`, `String`, `Bool`, `Array`, `[T]`, `{String: T}`,
`Pointer`, `Func`, `Void`, un struct o un enum; el `return` se comprueba contra el tipo declarado (un texto
no vale por un `Bool`, ni un struct por otro). Las funciones son recursivas y se pueden pasar como valor
(`aplica(doble, 4)`); una función guardada en una variable (`g = doble`) se llama con `g(x)`. Una lambda no
puede usar las variables locales de fuera (las globales sí): no hay closures. En un módulo, las que empiezan
por `_` son privadas.

### 4.6 Textos

```ruby
s = "Hola, " + nombre
m = "Tienes #{puntos * 2} puntos"   # interpolación: cualquier expresión (comillas de dentro: \")
n = s.length
c = s[0]                            # un carácter
trozo = s[2:5]                      # también s[:5] y s[2:]
p = str_find(s, "la")               # posición o -1
t = str_upper(str_trim(s))
s = s + "más"                       # añadir al final es lineal: construir textos en un bucle es barato
```

Más: `str_replace`, `str_starts`, `str_ends`, `str_lower`, `str_code`, `str_char`, `str_to_int`,
`str_from_int`, `file_read_text`, `file_write_text` (manual, sección de textos).

### 4.7 Listas y diccionarios

```ruby
numeros = [3, 1, 4]
numeros[0] = 9
total = numeros.length
parte = numeros[1:3]
todos = numeros + [1, 5]            # lista nueva

var pendientes: [String] = []       # lista con tipo de elemento
pendientes.push("leer")
pendientes.insert(0, "abrir")
ultimo = pendientes.pop()
pendientes.remove(0)

edades = {"Ana": 30, "Luis": 41}    # diccionario de texto a valor
edades["Eva"] = 25
if edades.has("Ana")
    Print edades["Ana"]
end
for clave in edades.keys()
    Print clave
end
n = edades.get("Pepe", 0)           # el valor, o el de por defecto si no está
edades.remove("Luis")
```

Una clave que no está da `0` (o `nil` en textos y objetos); `d.get(k, defecto)` lo busca una sola vez (con
objetos, el defecto solo puede ser `nil`). `l.clear()` y `d.clear()` vacían, y `d.length` cuenta las claves.
Las listas comprueban los índices: fuera de la lista, leer da `0` (o `nil`) y escribir no hace nada (con
`--debug`, el depurador para ahí). Una lista de structs, textos o listas es dueña de sus elementos.

### 4.8 Structs y enums

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
lista[0].vida = 80                  # el campo de un elemento
lista[0].mueve(1)                   # y sus métodos

struct Nodo
    valor: Int
    siguiente: Nodo = nil
    weak padre: Nodo                # apunta sin retener: padres sin ciclos de memoria
end

enum Estado
    PARADO = 0
    ANDANDO = 1
end
st = Estado.ANDANDO
```

### 4.9 Módulos

```ruby
import "lib/geometria.dash"         # funciones, structs, constantes y enums públicos del módulo
import "ventanas.dashui"            # ventanas MUI hechas con el editor visual (sección 6)
```

Las rutas son relativas al fichero que importa (o a la raíz del proyecto). `lib/amiga/` trae módulos listos:
audio, blitter, copper, dos, gráficos, IFF, intuition, memoria, RTG, sprites, doble buffer.

### 4.10 Memoria

Dash no tiene recolector de basura. Libera la memoria así:

- **Textos:** cada variable es dueña de su texto. Los textos intermedios (`"a" + b`) se liberan al acabar la vuelta
  del bucle, el evento o la función.
- **Listas y structs:** con un contador de referencias; se liberan cuando nadie los usa. Los ciclos (un hijo que
  apunta a su padre) se evitan con campos `weak`; si no, se liberan al salir.
- **Todo** sale de un pool de exec que se borra al terminar el programa, pase lo que pase.

`./dash --memcheck` compila una versión que avisa de usos después de liberar, liberaciones dobles y de lo que
queda vivo al salir. Para casos especiales: `retain`, `release`, `refcount` y arenas (`arena_*`).

## 5. El Amiga

### 5.1 Ventanas y eventos

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

`On Key` (una tecla, o sin nada cualquiera), `On Close`, `On Gadget` (gadgets por número), `On Menu` (menús),
`On Click` (botón izquierdo en la ventana: `click_x()`, `click_y()`) y `On Timer 100` (cada 100 ms; vale un
número o una variable). También ventanas desde el código
(`window_create`, con número; el `EventLoop` las atiende y `event_window()` dice cuál), pantallas propias
(`screen_open`) y RTG.

Los gadgets GadTools cuentan desde el interior de la ventana, sin los bordes. Para que quepan:
`window_create` con el flag 8 toma el ancho y el alto del interior; `window_border_top/bottom/left/right` dan
los bordes, y `screen_font_height` y `screen_font_text_width` miden con la fuente de la pantalla.

### 5.2 Gráficos, sprites y animación

`gfx_*` (puntos, líneas, rectángulos, círculos, polígonos, texto), colores (`gfx_rgb`, `color_pen`), fuentes de
disco (`font_open`), imágenes por datatypes (`image_load`, `image_draw`), bitmaps, BOBs con el blitter, sprites
de hardware y por software, listas de copper y doble buffer.

### 5.3 Entrada, sonido y ficheros

Teclado (`key_*`), ratón (`mouse_*`), joystick (`joy_*`). Sonidos IFF 8SVX en los cuatro canales (`sound_*`),
tonos (`tone_play`) y música ProTracker (`music_*`). Ficheros y directorios (`file_*`, `dir_*`), diálogos ASL,
argumentos del Shell (`arg_count`, `arg`).

### 5.4 Red

Por `bsdsocket.library` (Roadshow, MiamiDx, AmiTCP...):

- TCP cliente (`net_connect`, `net_send`, `net_recv`, `net_close`) y servidor (`net_listen`, `net_accept`,
  `net_peer`, `net_port`).
- UDP (`net_udp_open`, `net_udp_send`, `net_udp_recv`, `net_udp_from`), también a toda la red local
  (`"255.255.255.255"`).
- TLS con AmiSSL 5.1 o posterior (`tls_connect`, 68020+); reanuda la sesión con el mismo servidor.
- Conexión sin esperar (`net_connect_start`, `tls_connect_start`) y `net_signal()`, que despierta al programa
  cuando llega algo.
- La red también desde una tarea de `task_start`: solo una tarea la usa a la vez.
- Medir la red: interfaces de Roadshow (`net_ifs_read`), drivers SANA-II con cualquier pila (`net_drivers_read`,
  `net_driver_read`) y la señal WiFi (`wifi_read`, `wifi_read_device`).

No hay HTTP como builtin: cada programa lo escribe sobre TCP o TLS. Tampoco sockets raw ni tramas SANA-II en
crudo.

```ruby
s = net_connect("aminet.net", 80, 10000)
if s >= 0
    net_send(s, "HEAD / HTTP/1.0\r\nHost: aminet.net\r\n\r\n")
    respuesta = net_recv(s, 4096, 10000)
    Print respuesta
    net_close(s)
end
```

### 5.5 Sistema y tareas

- `break_check()` dice si llegó Ctrl-C (el "Break" del Shell); `single_instance("Nombre")` deja una sola copia
  del programa en marcha.
- `task_start(f, arg)` ejecuta una función `@native` en otro proceso (solo C); `task_done`, `task_result` y
  `task_free` la siguen.
- `cpu_start()` y `cpu_sample()` miden la CPU que usa cada tarea del sistema (`cpu_task_name`, `cpu_task_load`).
- `desktop_canvas(x, y, w, h)` dibuja en un trozo del escritorio del Workbench, detrás de los iconos, con una
  función Dash como la zona de dibujo de MUI. También con Directory Opus 5 o Scalos de escritorio.
- Commodity: `cx_broker` pone el programa en Exchange, `cx_hotkey` le da una tecla rápida y `cx_wait` espera
  órdenes sin gastar CPU (`cx_command`). `tooltype("NOMBRE", defecto)` lee un tooltype del icono o un
  argumento del Shell.
- `file_notify(ruta)` avisa cuando cambia un fichero (`file_changed`; `cx_wait` despierta con 7).
  `run_program(orden)` lanza otro programa sin esperar y `program_relaunch()` vuelve a arrancar este al acabar.
- Volúmenes montados y su espacio libre: `disks_read`, `disk_name`, `disk_kb`, `disk_free_kb`.
- Ratón: `mouse_curve` pone una curva de aceleración a cada ratón (también a los USB de Poseidon, `usb_hid_*`);
  `mouse_prefs_*` cambia la velocidad del sistema.

### 5.6 Fecha, versión e idiomas

- `clock_read()` lee la hora; `clock_year()`, `clock_month()`... dan cada parte, y `date_text("%d-%m-%Y")` la
  escribe en el idioma del sistema (`FormatDate` de `locale.library`).
- `@version "Mi programa 1.2"` pone la cadena `$VER:` que lee `C:Version`; `program_version()` la devuelve.
- Traducciones con catálogos de `locale.library`: `@catalog "Prog.catalog" 1` y `tr(1, "Hola")` (el texto
  del catálogo en el idioma del usuario o, si no hay, el del programa). `tools/catalogo.py` saca los textos
  y hace el `.catalog` sin FlexCat; en un `.dashui` los textos llevan `"tr"`.

## 6. Interfaces gráficas

| | GadTools | ReAction | MUI |
|---|---|---|---|
| Sistema | AmigaOS 3.0+ | AmigaOS 3.2 (3.5+) | MUI 3.8 o 5 instalado |
| CPU | 68000 | 68000 | 68020+ (MUI 5) |
| Disposición | posiciones a mano | automática | automática |
| En Dash | gadgets por número (`button_create`...) + `On Gadget`; o `gt_*` | `ra_*` | `mui_*` |
| Para | utilidades, juegos con panel | diálogos y formularios | aplicaciones grandes |

**MUI** es la más completa: ventanas que se adaptan solas, pestañas, listas, menús, imágenes y una zona de dibujo
propia que pinta una función Dash (`mui_canvas`; sabe dónde está el puntero con `mui_canvas_on_move` y repinta
solo un trozo con `mui_canvas_update_area`):

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

**Editor visual:** las ventanas MUI también se pueden dibujar con el ratón en VS Code (extensión de
`editor/vscode/`). Se guardan en un fichero `.dashui` que el programa importa; cada ventana da una función que
la construye y devuelve sus objetos:

```ruby
import "navegador.dashui"

Main
    mui_app_begin("Navegador", "NAVEGADOR")
    v = Navegador_create()          # v.window, v.url, v.pagina...
    mui_window_open(v.window)
    ...
end
```

Diseño de la API: [MUI_DISEÑO.md](MUI_DISEÑO.md); formato y editor: [MUI_EDITOR.md](MUI_EDITOR.md).

## 7. C desde Dash

Para lo que no tiene builtin:

```ruby
@extern("milib.library")            # una función de una librería del sistema
func MiFuncion(x: Int) -> Int

@native func peek(addr: Pointer) -> Int
"""
    return (LONG)*(volatile UBYTE *)addr;
"""
end
```

`@header "#include <x.h>"` añade cabeceras, `@link "lib/x.c"` enlaza un fichero C, objeto o librería, `@c """ ... """
end` pone C libre (por ejemplo funciones que llaman a Dash), `@stack N` pide una pila mínima y
`@workbench_output "NIL:"` evita la ventana de consola al arrancar desde el Workbench (lo escrito se pierde),
`@version "Prog 1.2"` pone la versión y `@catalog "Prog.catalog" 1` el catálogo de idioma (sección 5.6).
`@native(borrow) func` indica que el C solo usa sus argumentos durante la llamada (se ahorra copiarlos).

## 8. Herramientas

- **Emulador:** `tools/emu_run.py` ejecuta programas en FS-UAE sin ventana y devuelve su salida; con
  `--screenshot` saca una captura de la pantalla del Amiga. Con `--debug` habla con el depurador del
  emulador cuando el programa llama a `debug_break()` (registros, memoria, paso a paso).
- **Tests:** `python3 tests/run_tests.py` (con `--emu`, `--emu-a500` y `--emu-32` los ejecuta en un A1200,
  un A500 y un A1200 con AmigaOS 3.2; `--memcheck` con la comprobación de memoria).
- **Medidas:** `tools/bench.py` (velocidad, memoria y tamaño en A500 y A1200 emulados).
- **VS Code** (`editor/vscode/`, versión 0.2.1, ver [INSTALACION.md](INSTALACION.md)): errores al escribir,
  completar, ir a la definición, compilar y ejecutar en el emulador, depurar con F5 (también en un Amiga real
  por la red) y el editor visual de MUI. Vídeo tutorial: https://youtu.be/_UTJ_0s3xLc
- **Catálogos:** `tools/catalogo.py` (sección 5.6).

## 9. El C que genera

Un programa Dash es un solo fichero C (`build/programa.c`, o uno por módulo con `--multifile`): primero el runtime
que usa, después sus structs y funciones (`static`) y al final `main`. Se puede leer: los nombres del programa se
conservan. Ver la tabla de equivalencias en el [manual](MANUAL_REFERENCIA.md).

## 10. Requisitos de los programas

- Kickstart 3.0 o superior (pools de memoria de exec) y un 68000; cada programa pide 16 KB de pila (32 KB si usa MUI).
- MUI 5 y TLS (AmiSSL 5.1 o posterior) necesitan un 68020 o superior; ReAction, AmigaOS 3.2 (o 3.5+).
- Los textos del programa se escriben en UTF-8 y llegan al Amiga en Latin-1.

## 11. Lo que no tiene

- Clases con herencia (hay structs con métodos) ni macros: son preguntas abiertas.
- Closures: una lambda no ve las variables locales de fuera.
- `export`: no hace falta, todo es público salvo lo que empieza por `_` (decisión tomada).
- HTTP como builtin, sockets raw y tramas SANA-II en crudo.
