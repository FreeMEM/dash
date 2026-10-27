# D.A.S.H. Language - Hoja de Ruta de Desarrollo
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

**Última actualización:** 2026-10-24
**Fecha de inicio:** 2025-01-01
**Objetivo:** Crear un lenguaje de programación completo para Amiga

---

## Visión General

Dash es un lenguaje de alto nivel que transpila a C para Commodore Amiga. El objetivo es permitir desarrollo Amiga moderno sin lidiar con la complejidad de C y la gestión manual de memoria.

### Principios de Diseño

1. **Sintaxis limpia** - Inspirada en Ruby/Python
2. **Seguridad** - Sin punteros expuestos, gestión automática de recursos
3. **Amiga-first** - Acceso nativo a Intuition, Graphics, Audio, etc.
4. **Pragmático** - Escape hatch a bajo nivel cuando sea necesario

---

## Estado Actual (2026-10-24)

### Implementado ✅

- [x] Definición de ventanas (`Window ... end`)
- [x] Bloque principal (`Main ... end`)
- [x] Comandos básicos (`Print`, `Wait`, `Stop`)
- [x] Event Loop con `On Close`
- [x] Variables (asignación declara, estilo Python)
- [x] Expresiones aritméticas (`+`, `-`, `*`, `/`, `%`)
- [x] Expresiones lógicas (`and`, `or`, `not`)
- [x] Comparaciones (`==`, `!=`, `<`, `>`, `<=`, `>=`) y operadores de bits (`& | ^ ~ << >>`)
- [x] Control de flujo (`if`/`elif`/`else`/`end`, `while`/`end`, `for`, `break`, `continue`)
- [x] Comentarios (`# ...`)
- [x] Tipos inferidos (LONG, STRPTR, BOOL) y `Float`
- [x] Memoria automática (temporales por vuelta, contador de referencias)
- [x] Funciones, structs con métodos, enums, listas, diccionarios, `Float` y `Fixed`, lambdas e imports
- [x] Los 660 builtins Amiga implementados, 86 de ellos de MUI (ver `docs/BUILTINS.md`)
- [x] Interfaces con GadTools, ReAction y MUI (3.8 o 5); red con TCP (cliente y servidor), UDP y TLS (AmiSSL 5.1+).
      No hay HTTP como builtin: cada programa lo hace sobre TCP o TLS
- [x] Directivas `@native`, `@extern`, `@header`, `@link`, `@c`, `@stack`, `@workbench_output`, `@catalog` y `@version`
- [x] Commodities, catálogos de idioma (`tr`), fecha y hora, avisos de ficheros cambiados, CPU de cada tarea,
      dibujo en el fondo del Workbench
- [x] Extensión de VS Code (`editor/vscode/`, versión 0.2.3): errores al escribir, completar, compilar,
      emulador, depurador y editor visual de MUI

### Arquitectura del Compilador ✅

```
Source (.dash) → Parser (Lark) → AST → Analyzer → CodeGen → C → GCC → Amiga Executable
```

En `compiler/`:

- `grammar.py` - Gramática Lark
- `transformer.py` - Parse tree → AST
- `ast_nodes.py` - Definición de nodos AST
- `analyzer.py` - Análisis semántico, tabla de símbolos
- `codegen.py` - Generación de código C y runtime C embebido (`CTemplates`)
- `amiga_builtins.py` - Los builtins de Amiga (lista en `docs/BUILTINS.md`)
- `main.py` - Orquestador del pipeline e imports
- `dashui.py` - Ventanas MUI del editor visual (`.dashui`) como código Dash
- `cflags.py` - Opciones de gcc, comunes a `./dash` y al runner de tests
- `tmp_marks.py` - Repaso del C final: quita marcas de temporales que no hacen falta
- `latin1.py` - Los textos de los literales pasan a Latin-1
- `softfloat.py` - Float por software (con `runtime/softfloat/`)
- `debuglines.py` - `./dash --debug`: líneas `#line` hacia el `.dash` para gdb
- `lsp.py`, `lsp_index.py`, `lsp_format.py` - Servidor de lenguaje de la extensión de VS Code

En `tools/`: el emulador (`emu_run.py`, `emu_preview.py`, `emu_sys_*.sh`), el depurador (`gdb_relay.py`,
`gdb/dash.py`, `get_bgdbserver.sh`), SDK y librerías (`get_mui_sdk.sh`, `get_amissl.sh`), benchmarks
(`bench.py`, `bench_report.py`), `fuzz_refcount.py`, `fastfp_check.py` y generadores (`gen_builtins_doc.py`,
`gen_tmgrammar.py`).

---

## Fase 1: Fundamentos del Lenguaje

**Objetivo:** Hacer Dash un lenguaje de programación general completo.

### 1.1 Scope Léxico
**Estado:** ✅ Completado
**Prioridad:** Alta
**Complejidad:** Media

**Descripción:**
Implementar scope léxico estilo Python/Ruby donde las variables definidas en bloques internos no escapan al scope exterior.

**Comportamiento esperado:**
```ruby
x = 10
if true
    x = 20        # modifica x del scope exterior
    y = 30        # y es LOCAL al bloque if
end
Print x           # 20 (modificado)
Print y           # ERROR: y no está definido
```

**Reglas:**
- Una variable existe en el scope donde se asigna por primera vez
- Bloques hijos pueden LEER variables del padre
- Bloques hijos pueden MODIFICAR variables del padre (si ya existe)
- Variables creadas en bloque hijo NO son visibles en padre
- Funciones crean nuevo scope (las variables internas son locales)

**Cambios realizados:**
- [x] `analyzer.py`: Ya manejaba scopes correctamente (lookup en parent scopes)
- [x] `codegen.py`: Añadido `scope_stack` para tracking de variables por scope
- [x] Tests: `tests/scope_test.dash` creado y funcionando

**Notas de implementación:**
```c
// Dash:                    // C generado:
x = 10                      LONG x = 10;
if true                     if (TRUE) {
    x = 20                      x = 20;        // no redeclara
    y = 30                      LONG y = 30;   // local al bloque
end                         }
```

---

### 1.2 Funciones
**Estado:** ✅ Completado
**Prioridad:** Alta
**Complejidad:** Media

**Descripción:**
Funciones definidas por el usuario con parámetros y retorno.

**Sintaxis:**
```ruby
# Función simple
func saludar(nombre)
    Print "Hola " + nombre
end

# Función con retorno
func suma(a, b)
    return a + b
end

# Función sin parámetros
func obtener_version()
    return 1
end

# Llamadas
saludar("Amiga")
resultado = suma(5, 3)
ver = obtener_version()
```

**Reglas:**
- `func nombre(params) ... end`
- `return` opcional (si no hay return, retorna 0/null)
- Parámetros son locales a la función
- Sin sobrecarga (un nombre = una función)
- Una función se puede llamar antes de su definición: el compilador escribe los prototipos

**Cambios realizados:**
- [x] `grammar.py`: Añadido `function_def`, `function_call`, `return_stmt`
- [x] `transformer.py`: Procesar FunctionDef y ReturnStmt
- [x] `analyzer.py`:
  - Registrar funciones en tabla de símbolos global
  - Crear scope nuevo para cuerpo de función
  - Verificar llamadas a funciones (existe, número de args)
- [x] `codegen.py`:
  - Generar prototipos de función antes de main
  - Generar cuerpos de función con tipo de retorno inferido
  - Generar llamadas y return statements
- [x] Tests: `test_func_simple.dash`, `test_func_params.dash`, `test_func_recursive.dash`

**C generado:**
```c
// Prototipo
LONG suma(LONG a, LONG b);

// Implementación
LONG suma(LONG a, LONG b) {
    return (a + b);
}

// En main
LONG resultado = suma(5, 3);
```

**Consideraciones:**
- ¿Recursión? Sí, debería funcionar automáticamente
- ¿Funciones como valores? Sí: tipo `Func` y lambdas (`doble = fn(x) -> x * 2`)
- ¿Closures? No: una lambda solo ve sus parámetros y los nombres globales, no las variables locales de fuera

---

### 1.3 Arrays
**Estado:** ✅ Completado
**Prioridad:** Alta
**Complejidad:** Media

**Descripción:**
Arrays dinámicos con sintaxis simple.

**Sintaxis:**
```ruby
# Crear array
numeros = [1, 2, 3, 4, 5]
nombres = ["Ana", "Bob", "Carlos"]
vacio = []

# Acceso por índice (base 0)
primero = numeros[0]
numeros[2] = 100

# Propiedades
len = numeros.length

# Iterar
for num in numeros
    Print num
end

# Operaciones (también insert, remove y clear)
numeros.push(6)
ultimo = numeros.pop()
```

**Reglas:**
- Arrays son homogéneos (todos elementos mismo tipo)
- Índices base 0
- Bounds checking en runtime: fuera de rango, leer da 0 y escribir no hace nada (con `--debug`, para el depurador)
- `.length` retorna tamaño

**Implementación en C:**
```c
// Estructura interna para arrays
typedef struct {
    LONG *data;
    LONG length;
    LONG capacity;
} DashArrayLong;

// Dash: numeros = [1, 2, 3]
DashArrayLong *numeros = DashArray_create(3);
DashArray_set(numeros, 0, 1);
DashArray_set(numeros, 1, 2);
DashArray_set(numeros, 2, 3);

// Dash: x = numeros[1]
LONG x = DashArray_get(numeros, 1);
```

**Cambios realizados:**
- [x] `grammar.py`: Añadido `array_literal`, `array_access`, `array_assign`, `array_length`
- [x] `ast_nodes.py`: ArrayLiteral, ArrayAccess, ArrayAssign, PropertyAccess
- [x] `transformer.py`: Procesar nuevos nodos de arrays
- [x] `analyzer.py`: Tipos ARRAY_INT, ARRAY_STRING, visitors para arrays
- [x] `codegen.py`: Generar código con runtime de arrays inline
- [x] Runtime de arrays (embebido en `compiler/codegen.py`, `CTemplates.ARRAY_RUNTIME`)
- [x] Tests: `test_array_basic.dash`, `test_array_ops.dash`

**Consideraciones:**
- Arrays de arrays (matrices): hechos (`m[i][j]`, `tests/test_matrix.dash`)
- Slicing (`arr[1:3]`, `[:b]`, `[a:]`): hecho, también en strings
- Con tipo de elemento: `var x: [String]`; `var x: Array` sigue siendo una lista de enteros (ver "Pendiente")

---

### 1.4 Strings Mejorados
**Estado:** ✅ Completado
**Prioridad:** Media
**Complejidad:** Baja-Media

**Descripción:**
Operaciones de string más allá de literales.

**Sintaxis:**
```ruby
nombre = "Amiga"
saludo = "Hola, " + nombre + "!"    # concatenación
inicial = nombre[0]                   # "A"
longitud = nombre.length              # 5

# Interpolación (también expresiones: "#{a + 1}", "#{f(x)}")
msg = "Usuario: #{nombre}"
```

**Implementación en C:**
```c
// Concatenación - necesita buffer
STRPTR saludo = DashString_concat("Hola, ", nombre);
saludo = DashString_concat(saludo, "!");  // memory management!

// Acceso a carácter
char inicial = DashString_char_at(nombre, 0);

// Longitud
LONG longitud = DashString_length(nombre);
```

**Cambios realizados:**
- [x] `grammar.py`: Operador `+` ya soportado, `str[i]` usa array_access
- [x] `analyzer.py`: Detecta operaciones string vs numéricas con _is_string_expr
- [x] `codegen.py`: Genera llamadas a runtime de strings, tracking de tipos
- [x] Runtime de strings (embebido en `CTemplates.STRING_RUNTIME`): DashString_concat, DashString_length, DashString_char_at
- [x] Tests: `test_string_ops.dash`

**Consideraciones:**
- Memoria automática: cada variable es dueña de su texto y los temporales se liberan solos (por vuelta de
  bucle, `EventLoop` y función)
- Strings inmutables (más seguro)

---

### 1.5 For Loop
**Estado:** ✅ Completado
**Prioridad:** Media
**Complejidad:** Baja

**Sintaxis:**
```ruby
# Iterar sobre rango
for i in (1..10)
    Print i
end

# Iterar sobre array
for item in items
    Print item
end
```

**Cambios realizados:**
- [x] `grammar.py`: `for_range_stmt` y `for_each_stmt` con RANGE_OP token
- [x] `ast_nodes.py`: ForRangeStmt y ForEachStmt
- [x] `transformer.py`: Procesar ambos tipos de for
- [x] `analyzer.py`: Visitors para for loops con scope de variable
- [x] `codegen.py`: Templates y generación de for loops C
- [x] Tests: `test_for_range.dash`, `test_for_each.dash`

**C generado:**
```c
// for i in (1..5)
for (LONG i = 1; i <= 5; i++) { ... }

// for item in array
for (LONG _idx_item = 0; _idx_item < DashArray_length(arr); _idx_item++) {
    LONG item = DashArray_get(arr, _idx_item);
    ...
}
```

---

## Fase 2: Sistema de Módulos

**Objetivo:** Permitir organización de código en múltiples archivos.

### 2.1 Imports (Estilo Python)
**Estado:** ✅ Completado
**Prioridad:** Media
**Complejidad:** Media

**Sintaxis:**
```ruby
# Importar archivo completo
import "utils.dash"

# Importar desde subdirectorio
import "lib/math_utils.dash"
```

**Comportamiento:**
- `import "file.dash"` - carga el archivo y hace disponible lo público
- Lo que empieza por `_` es privado del módulo: funciones, constantes, globales, structs y enums (D45).
  Usarlo desde otro módulo da el error `'_x' is private to module 'm.dash'`. Dos módulos pueden tener cada uno
  su `_x`: si chocan, el compilador los renombra
- Solo existe la forma `import "ruta"` (no hay `import X from "y"`)
- Imports recursivos soportados
- Protección contra imports circulares

**Cambios realizados:**
- [x] `grammar.py`: Sintaxis `import "path"`
- [x] `ast_nodes.py`: Nodo `ImportStmt`
- [x] `transformer.py`: Procesar import statements
- [x] `main.py`: Sistema de carga de módulos con `_merge_modules()`
- [x] Resolución de paths relativos al archivo fuente
- [x] Filtrado de funciones privadas (`_nombre`)
- [x] Caché de módulos para evitar duplicados
- [x] Tests: `test_import_basic.dash`, `lib/math_utils.dash`

**Ejemplo:**
```ruby
# lib/utils.dash
func helper(x)
    return x * 2
end

func _internal()  # Privada - no accesible desde fuera
    return 42
end

# main.dash
import "lib/utils.dash"

Main
    result = helper(5)  # OK - función pública
    # _internal()       # Error: '_internal' is private to module 'utils.dash'
end
```

### 2.2 Exports
**Estado:** ⬜ No implementado (decisión: no necesario)

**Nota:** Se decidió usar el enfoque estilo Python donde todo es público por defecto, excepto lo que empieza por `_`, que es privado. Esto simplifica el lenguaje sin necesidad de keyword `export`.

---

## Fase 3: Soporte Amiga

**Objetivo:** Acceso completo a las APIs de AmigaOS.

### Estrategia: Híbrida (A + B)

Combinar:
- **Módulos Built-in** (Estrategia A): API de alto nivel, el compilador conoce y optimiza
- **FFI** (Estrategia B): Escape hatch para acceso directo cuando sea necesario

### 3.1 Módulos Built-in
**Estado:** ✅ Completado (660 funciones, 86 de MUI; lista en `docs/BUILTINS.md`)
**Prioridad:** Alta
**Complejidad:** Alta

**Nota:** Los builtins están implementados como templates de codegen en `amiga_builtins.py`, cubriendo:
- **Graphics:** drawing, colors, bitmaps
- **Sprites:** hardware + soft sprites
- **Copper:** copper list manipulation
- **Blitter/BOBs:** blitting operations
- **Audio:** canales Paula, samples
- **Input:** keyboard, mouse, joystick
- **DOS:** files, directories
- **Intuition:** windows, gadgets, screens, requesters
- **RTG:** retargetable graphics
- **Double Buffering:** pantalla doble buffer
- **System:** memoria, signals, tasks
- **Interfaces:** GadTools, ReAction y MUI (`mui_*`)
- **Red:** TCP cliente y servidor, UDP (`bsdsocket.library`) y TLS con AmiSSL; contadores de los drivers
  SANA-II y señal WiFi
- **Sistema:** commodities (`cx_*`), tooltypes, avisos de ficheros (`file_notify`), lanzar programas, fecha y hora,
  catálogos de idioma (`tr`), CPU de cada tarea, fondo del Workbench, curvas del ratón
- **Imágenes y fuentes:** datatypes, píxeles RGB/RGBA, transparencias, fuentes de disco

**Ejemplo - gráficos:**
```ruby
Window MyWindow
    title "Gráficos"
    width 320
    height 200
end

Main
    MyWindow.open

    gfx_pen(1)                      # SetAPen
    gfx_line(10, 10, 100, 50)       # Move + Draw
    gfx_rect(20, 20, 80, 60)        # RectFill
    gfx_text_at(10, 120, "Hola")    # Move + Text

    # ...
end
```

**Implementación:**
Cada builtin es una plantilla de C. El compilador traduce `gfx_line(x1, y1, x2, y2)` a:
```c
Move(_dash_rp, x1, y1); Draw(_dash_rp, x2, y2);
```

Además, `lib/amiga/` tiene módulos escritos en Dash (audio, blitter, copper, dos, graphics, iff, intuition,
memory, rtg, sprites...) que se importan con `import "lib/amiga/graphics.dash"`.

---

### 3.2 FFI (Foreign Function Interface)
**Estado:** ✅ Completado
**Prioridad:** Media
**Complejidad:** Alta

**Sintaxis:**
```ruby
# Declarar función externa
@extern("mylib.library")
func CustomFunc(x: Int, y: Int) -> Int

# Usar
result = CustomFunc(10, 20)
```

**Nota:** Para funciones ya disponibles en headers de Amiga SDK, usar los builtins.
FFI es para librerías custom que no están en los headers estándar.

**Cambios realizados:**
- [x] `grammar.py`: Decorador `@extern`
- [x] `ast_nodes.py`: ExternFunc, FunctionParam
- [x] `analyzer.py`: Validar declaraciones extern
- [x] `codegen.py`: Generar prototipos extern

---

### 3.3 Especificación de Módulos Amiga

> **Nota:** esta especificación es el diseño original y no se hizo así. No existe `import X from "y"` ni
> objetos como `Graphics.line`. La API real son los builtins (`docs/BUILTINS.md`) y los módulos de `lib/amiga/`.
> Gadgets y menús existen, con GadTools, ReAction y MUI.

#### amiga/intuition
```ruby
import Intuition from "amiga/intuition"

# Ventanas (ya parcialmente implementado)
Window MyWin
    title "Test"
    width 320
    height 200
    flags [CLOSEGADGET, DRAGBAR, DEPTHGADGET]
end

# Gadgets (futuro)
Button myButton
    label "Click me"
    x 10
    y 10
end

# Menús (futuro)
Menu fileMenu
    item "Open", shortcut: "O", action: onOpen
    item "Save", shortcut: "S", action: onSave
    separator
    item "Quit", shortcut: "Q", action: onQuit
end

# Requesters
Intuition.alert("Error!", "OK")
result = Intuition.confirm("¿Continuar?", "Sí", "No")
filename = Intuition.fileRequest("Abrir archivo")
```

#### amiga/graphics
```ruby
import Graphics from "amiga/graphics"

# Colores
Graphics.pen(window, colorIndex)
Graphics.color(r, g, b)  # Modifica paleta

# Primitivas
Graphics.pixel(window, x, y)
Graphics.line(window, x1, y1, x2, y2)
Graphics.rect(window, x, y, w, h)
Graphics.rectFill(window, x, y, w, h)
Graphics.circle(window, cx, cy, radius)
Graphics.ellipse(window, cx, cy, rx, ry)

# Texto
Graphics.text(window, "Hello")
Graphics.textAt(window, x, y, "Hello")

# BitMaps y Blitting
bm = Graphics.loadIFF("image.iff")
Graphics.blit(source, dest, x, y)

# Modo
Graphics.drawMode(JAM1)  # JAM1, JAM2, COMPLEMENT, etc.
```

#### amiga/dos
```ruby
import DOS from "amiga/dos"

# Archivos
file = DOS.open("data.txt", MODE_READ)
content = DOS.read(file, size)
DOS.write(file, data)
DOS.close(file)

# Alto nivel
text = DOS.readFile("config.txt")
DOS.writeFile("output.txt", text)

# Directorios
files = DOS.listDir("DF0:")
DOS.makeDir("RAM:temp")
exists = DOS.exists("file.txt")

# CLI
DOS.print("Mensaje")
input = DOS.input("Nombre: ")
DOS.execute("dir")
```

---

## Fase 4: Tipos y Estructuras

### 4.1 Tipos Opcionales
**Estado:** ✅ Completado

```ruby
# Con tipos explícitos
func suma(a: Int, b: Int) -> Int
    return a + b
end

# Sin tipos (inferido) - sigue funcionando
func suma(a, b)
    return a + b
end
```

**Tipos soportados:** `Int`, `Float`, `Fixed`, `String`, `Bool`, `Array`, `Pointer`, `Func`, `Void`, el nombre de un
struct o de un enum, listas con tipo (`[String]`, `[Nodo]`) y diccionarios (`{String: T}`). Otro nombre es un error.

### 4.2 Structs
**Estado:** ✅ Completado

```ruby
struct Player
    name: String
    x: Int
    y: Int
    score: Int = 0
end

player = Player("Hero", 100, 50)
player.score = player.score + 10
Print player.name
```

**Implementación:**
- Tipos con prefijo `_Dash_` para evitar colisiones con SDK Amiga
- Constructores que piden memoria del pool, con contador de referencias (`_dash_rc_new_obj`)
- Acceso a miembros con notación `->` en C

### 4.3 Enums
**Estado:** ✅ Completado

```ruby
enum Direction
    UP
    DOWN
    LEFT
    RIGHT
end

enum State
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    STOPPED = 10
end

dir = Direction.UP
state = State.RUNNING
```

**Implementación:**
- Genera `typedef enum` en C
- Valores explícitos o auto-incrementales
- Acceso: `EnumName.VALUE` → `EnumName_VALUE`

---

## Runtime Library

El runtime en C va embebido en `compiler/codegen.py` (`CTemplates`) y solo se incluye
en el C generado la parte que el programa usa:

- `MEMORY_RUNTIME`: pool de exec (`_dash_alloc`), borrado al salir (`_dash_mem_cleanup`); caché de bloques de
  hasta 128 bytes en clases de 8 (`_dash_block_get/put`); strings con cabecera y lista de temporales por marca;
  objetos (arrays y structs) con contador de referencias y lista de temporales
- `ARRAY_RUNTIME`: `DashArrayLong`, create/from/get/set/length/slice
- `STRING_RUNTIME`: concat, join, length, char_at, from_int (dos cifras por `divu`), from_char
- `FLOAT_RUNTIME` y `runtime/softfloat/`: Float por software (fp-bit de GCC + suma y multiplicación en
  ensamblador 68000); `--fpu` usa la FPU
- `STACK_REQUEST`: pila mínima de 16 KB con el `swapstack` de libnix (`--stack N`)

**Consideraciones Amiga:**
- Pool de exec (V39, Kickstart 3.0+); memoria CHIP solo donde la pide el hardware (sonido, bitmaps, sprites)
- Velocidad, memoria y tamaño medidos en un A500 y un A1200 emulados: `tools/bench.py`, `tests/bench/`

---

## Testing

### Estructura de Tests
```
tests/
├── test_*.dash          # Deben compilar y enlazar (y dar su salida en el emulador)
├── errors/              # Deben fallar con el texto de su línea "# expect: ..."
├── lib/                 # Módulos para los tests de import
├── runtime/             # El runtime C ejecutado en el PC (host_harness.c)
├── lsp/, unit/          # Tests en Python: servidor de lenguaje, CLI, depurador, emulador
├── bench/               # Benchmarks (results.json)
└── run_tests.py
```

### Criterios de Completitud

**Fase 1 completa cuando:**
- [x] Todos los tests de scope pasan
- [x] Todos los tests de funciones pasan
- [x] Todos los tests de arrays pasan
- [x] Todos los tests de strings pasan
- [x] Ejemplos originales siguen funcionando
- [x] Documentación actualizada

---

## Registro de Progreso

### Sesión 1 (Fecha: 2025-01-01)
- [x] Refactorización del compilador (AST, Analyzer, CodeGen)
- [x] Variables con asignación (estilo Python)
- [x] Expresiones aritméticas y lógicas
- [x] if/else/end, while/end
- [x] Creación de este documento de roadmap
- [x] **1.1 Scope Léxico** - Implementado y testeado
  - `codegen.py`: scope_stack para tracking de variables
  - `tests/scope_test.dash`: test de scoping

### Sesión 2 (Fecha: 2025-12-31)
- [x] Corregido soporte de comentarios en EventLoop y al final de archivo
- [x] **1.2 Funciones** - Implementado completamente:
  - Funciones sin parámetros y con parámetros
  - Return statement con inferencia de tipo
  - Funciones recursivas
  - Funciones llamando otras funciones
  - Prototipos generados automáticamente
  - Tests: `test_func_simple.dash`, `test_func_params.dash`, `test_func_recursive.dash`
- [x] **1.3 Arrays** - Implementado completamente:
  - Literales de array: `[1, 2, 3]`
  - Acceso por índice: `arr[i]`
  - Asignación de elementos: `arr[i] = valor`
  - Propiedad length: `arr.length`
  - Runtime DashArrayLong inline
  - Bounds checking en runtime
  - Tests: `test_array_basic.dash`, `test_array_ops.dash`
- [x] Test suite: 29 tests pasando

### Sesión 3 (Fecha: 2026-01-01)
- [x] **1.5 For Loops** - Implementado completamente:
  - For-range: `for i in (1..10)`
  - For-each: `for item in array`
  - Token RANGE_OP para evitar conflicto con números flotantes
  - Tests: `test_for_range.dash`, `test_for_each.dash`
- [x] **1.4 Strings Mejorados** - Implementado completamente:
  - Concatenación: `str1 + str2`
  - Acceso a caracteres: `str[i]`
  - Longitud: `str.length`
  - Runtime: DashString_concat, DashString_length, DashString_char_at
  - Detección de tipos string vs number para Print correcto
  - Tests: `test_string_ops.dash`
- [x] **Fase 1 completa** - Todos los fundamentos del lenguaje implementados
- [x] **2.1 Imports** - Sistema de módulos implementado:
  - Sintaxis: `import "path/file.dash"`
  - Funciones privadas con `_` prefijo
  - Resolución de paths relativos
  - Protección contra imports circulares
  - Caché de módulos cargados
  - Tests: `test_import_basic.dash`, `lib/math_utils.dash`
- [x] Test suite: 29 tests pasando

### Sesión 4 (Fecha: 2026-01-01)
- [x] **3.1 Amiga Builtins** - 161 funciones nativas implementadas:
  - Graphics: draw_line, draw_rect, draw_circle, draw_text, etc.
  - Colors: set_color, set_pen, get_rgb, etc.
  - Input: key_pressed, mouse_x, mouse_y, joy_button, etc.
  - System: allocmem, freemem, time_delay, etc.
- [x] **4.2 Structs** - Implementado completamente:
  - Definición: `struct Name ... end`
  - Campos con tipos: `field: Type`
  - Constructor automático
  - Acceso a miembros: `obj.field`
  - Asignación: `obj.field = value`
  - Tests: `test_struct.dash`
- [x] **4.3 Enums** - Implementado completamente:
  - Definición: `enum Name ... end`
  - Valores auto-incrementales o explícitos
  - Acceso: `EnumName.VALUE`
  - Tests: `test_new_features.dash`
- [x] **4.1 Optional Types** - Implementado completamente:
  - Parámetros tipados: `func f(x: Int, y: String)`
  - Tipo de retorno: `-> Int`
  - Tipos: Int, String, Bool, Pointer, Void
  - Compatibilidad hacia atrás (tipos opcionales)
- [x] **3.2 FFI @extern** - Implementado:
  - Sintaxis: `@extern("lib") func name(params) -> type`
  - Para librerías custom no en SDK
- [x] Tests gráficos verificados en Amiga real

### Sesión 5 (Fecha: 2026-10-14) — Repaso completo
- [x] Toolchain instalado (`m68k-amigaos-gcc` 6.5.0b + SDK CyberGraphX): los tests compilan y enlazan de verdad
- [x] Repaso por zonas de todo el compilador (detalle en `docs/REPASO_LOOP.md`)
- [x] Ejemplos: de 26/30 a **30/30** compilando
- [x] Builtins: 246 de 318 implementados; los 72 restantes dan error claro (ver `docs/BUILTINS.md`)
- [x] Memoria: strings, arrays y structs salen de un pool de exec liberado al salir
- [x] Corregidos fallos que colgaban el Amiga: doble `CloseWindow`, `graphics.library` sin abrir
- [x] Test suite: 58 tests (normales, `tests/errors/`, `multifile/`, runtime en el PC, documentación)

### Sesión 6 (Fecha: 2026-10-14/15) — Mejoras (rama `mejoras`, detalle en `docs/MEJORAS_LOOP.md`)
- [x] Salida común de error: si falla una apertura se cierra todo lo abierto antes de salir
- [x] Banco de pruebas en FS-UAE sin ventana (`tools/emu_run.py`), tests con salida esperada en A1200, A500 y 3.2
- [x] `-O2` por defecto (probado en emulador), `-O0` para depurar, `--small` (`-Os`), `--stack N`, `--fpu`
- [x] Lenguaje: hex/binario, `break`/`continue`, rangos descendentes y `step`, enums negativos, `a.b.c = x`,
      propiedades booleanas de ventana, `On Key`, `Float`
- [x] Memoria automática: strings con dueño y temporales por vuelta; arrays y structs con referencias
- [x] Los 72 builtins pendientes: ventanas, diálogos ASL, gadgets, bitmaps, bobs, copper, sonido y música
- [x] Optimización medida: hasta x8 en bucles de arrays, x3,4 en interpolación, Float propio en asm,
      funciones `static` (-9 % de tamaño), strings cortos un 29 % más pequeños
- [x] Panel de comparativas: https://claude.ai/artifact/9XyJ1JNSGuDo5q6NCRzM2N (`tools/bench_report.py`)
- [x] Test suite: 103 resultados (233 con `--emu --emu-a500 --emu-32`); ejemplos 30/30
- [x] Conteo de referencias revisado (tarea 30): `--memcheck`, auditoría, `tools/fuzz_refcount.py`, listas dueñas
      de sus elementos, préstamos, sin recursión al liberar; structs y listas hasta −65 % al crearse; `nil`
- [x] Coma fija `Fixed` 16.16 (tarea 31): ×2,6 en multiplicar y como un entero al sumar en un 68000
- [x] Fallos de GCC evitados en `compiler/cflags.py` (`-fbbb` sin `e`/`r`, dirección 0 legible)
- [x] Test suite: 120 resultados (280 con `--emu --emu-a500 --emu-32`); ejemplos 31/31
- [x] Tercera máquina de pruebas: A1200 con AmigaOS 3.2 y Workbench cargado (`--emu-32`), la única que prueba
      ReAction; encontró `ra_get_value`/`ra_set_value` mal y `s[a:b]` sobre strings, ya corregidos

### Sesión 7 (Fecha: 2026-10-15/16) — MUI 5 (rama `mui`, detalle en `docs/MUI_LOOP.md`)
- [x] 67 builtins `mui_` (diseño en `docs/MUI_DISEÑO.md`): aplicación, ventanas, grupos, marcos, columnas, pestañas,
      desplazamiento, texto, botones, campos, casillas, ciclos, deslizadores, barras, listas, menús, imágenes por
      datatypes, zona de dibujo propia con una función Dash y barra, eventos por número, temporizador y señales
- [x] Entorno: SDK fuera de git (`tools/get_mui_sdk.sh`), máquinas con MUI en el banco de pruebas
      (`tools/emu_sys_mui.sh`), pila de 32 KB en programas MUI, comprobación de 68020
- [x] Capturas de pantalla del Amiga emulado (`tools/emu_run.py --screenshot`)
- [x] Textos en Latin-1: los acentos llegaban al Amiga en UTF-8 (`compiler/latin1.py`)
- [x] Ejemplos `mui_hola` y `mui_navegador` (esqueleto de la ventana de dashweb); 33/33
- [x] Test suite: 130 resultados (311 con `--emu --emu-a500 --emu-32`; 193 con `--emu --memcheck`)
- [x] GadTools y ReAction auditados y arreglados (14 fallos: los gadgets `gt_*` y los menús no recibían eventos,
      `blixel` no compilaba, valores leídos con el atributo equivocado, mensajes perdidos, punteros a ventanas
      cerradas, textos copiados para siempre...). Nuevos: `On Menu`, gadgets por número de ciclo, radio, número,
      paleta y entero; menús con marca; ReAction con listbrowser, radio, pestañas, barra, menús y selector de
      ficheros; el `EventLoop` atiende las ventanas de `window_create` (`event_window()`)
- [x] Tests con clics y menús reales por `input.device` (`tests/test_gt_events.dash` y siguientes)
- [x] Test suite: 137 resultados (333 con `--emu --emu-a500 --emu-32`; 204 con `--emu --memcheck`); 425 builtins
- [x] Editor visual de MUI: ficheros `.dashui` (JSON) que el compilador importa (`compiler/dashui.py`) y extensión de VS
      Code en `editor/vscode/` (resaltado, compilar, emulador, editor de ventanas con vista aproximada y captura real
      del Amiga); ejemplo `examples/mui_navegador.dashui`

### Sesión 8 (Fecha: 2026-10-16) — Pendientes (rama `pendientes`)
- [x] `debug_break()` y `tools/emu_run.py --debug`: el depurador de FS-UAE desde un programa (uaelib 15)
- [x] Interpolación con cualquier expresión (`"#{a + 1}"`, `"#{v.length}"`, `"#{f(x)}"`); el resultado es siempre
      texto (`"#{a}#{b}"` con números ya no los suma)
- [x] Listas de `Fixed` (`[Fixed(1.5), 2]`, `var l: [Fixed]`, parámetros, retornos y campos)
- [x] `window_check_close`, `key_pressed`, `key_get` y `key_wait` leen los mensajes en un solo sitio (ninguno tira lo
      que espera otro); `key_pressed` solo mira
- [x] GadTools: atajos con `_` en botones y casillas; gadgets con ancho o alto 0 medidos con la fuente de la pantalla;
      `gadget_width`/`gadget_height`
- [x] ReAction con varias ventanas (hasta 4): `ra_window_use`, `ra_event_window`
- Los `gt_*` siguen siendo de una ventana: para varias, gadgets por número (que ya lo admiten)

### Sesión 9 (Fecha: 2026-10-16/17) — Tareas de dashweb D40-D50 y rendimiento
Desde aquí, lo que le falta a dashweb se pide a Dash como tarea `Dnn` (numeración del plan de dashweb).
- [x] Lenguaje: operadores de bits (`& | ^ ~ << >>`, también en `const`); diccionarios de diccionarios y listas de
      diccionarios; `str_contains` y `str_split`; el `return` se comprueba contra el tipo declarado; un `Bool` se
      escribe `true`/`false` (también los de `@native` y `@extern`)
- [x] Rendimiento: menos copias y préstamos en llamadas y returns, funciones puras sin préstamo de argumentos,
      `for k in d.keys()` sin crear la lista, `str_lower(x) == "..."` sin copia
- [x] Arreglo: `for x in lista` mira la longitud en cada vuelta (sacar elementos dentro del bucle leía memoria
      liberada)
- [x] Gráficos: `image_from_rgb` (D40), transparencias y degradados `gfx_blend_rect`, `gfx_gradient_rect`,
      `gfx_pixel_rgb` (D42), búferes RGB24 para vídeo `gfx_rgb_draw` y `gfx_rgb_draw_scaled` (D43),
      transparencia de las imágenes en pantallas RTG (D50)
- [x] MUI: rellenos en la zona de dibujo, `mui_canvas_update`, doble búfer `mui_canvas_buffered` (D48),
      `mui_window_fullscreen` y `mui_window_own_screen`
- [x] Red: plazos sin espera que no cuentan el tiempo en que el programa no mira (D41)
- [x] Constantes, globales, structs y enums privados por módulo (D45); `task_start`: una función `@native` en otro
      proceso (D47); listas y diccionarios devueltos por funciones conservan el tipo de sus elementos (D49)
- [x] Herramientas: `emu_run.py` con varias capturas (D44), capturas de pantallas RTG, 68040 en el emulador para
      `--fpu` (D46); `compiler/cflags.py` quita también la pasada `s` de `-fbbb` (código erróneo)

### Sesión 10 (Fecha: 2026-10-17/18) — RTG rápido y TLS (D51-D56)
- [x] `gfx_blend_rect` y `gfx_gradient_rect` en RTG por bloques de filas: 35 veces más rápido (D51)
- [x] AmiSSL 5.1 o posterior: se pide la versión del SDK y, si falta, las anteriores (D52)
- [x] `x = d[k]` de un diccionario de diccionarios es un diccionario de su tipo (D53)
- [x] `image_from_rgb` en pantallas RTG sin `picture.datatype` (D54)
- [x] TLS: la sesión de cada servidor se reanuda en la siguiente conexión, `tls_resumed` (D55)
- [x] `-D_DASH_PIXGUARD`: guardas en los búferes de píxeles para cazar escrituras fuera (D56)
- dashweb publica su primera versión de prueba, v0.1.0-alfa (2026-10-18)

### Sesión 11 (Fecha: 2026-10-20) — D57-D61 y Trasfondo; fusiones por pull request
- [x] Fuentes vectoriales: tamaño mínimo 2 (con 0 o 1, diskfont de 3.2 escribe en memoria ajena) y
      `tools/amiga/vectoriales_memoria.dash` para comprobarlo (D57); zona de dibujo con MUI 3.8 (D58)
- [x] `@workbench_output "NIL:"`: sin ventana de consola al arrancar desde el Workbench (D59)
- [x] `net_signal` y `task_signal`: la red y las tareas despiertan al programa por señal (D60)
- [x] La caché de longitudes solo guarda textos hechos por Dash, no los de C (D61)
- [x] Arreglos del tutorial de dashweb: campos de struct llamados `s`; `--autoclose` con MUI
- [x] Trasfondo: CPU de cada tarea (`cpu_start`, `cpu_sample`, `cpu_task_name`, `cpu_task_load`, `cpu_total`,
      `cpu_stop`); dibujo en el fondo del Workbench, detrás de los iconos (`desktop_canvas`,
      `desktop_canvas_on_draw`, `desktop_canvas_update`, `desktop_canvas_update_area`, `desktop_canvas_free`),
      planar y RTG, con y sin backdrop; `break_check` (Ctrl-C sin ventana) y `single_instance` (una copia a la vez)
- Desde aquí, cada rama entra en `main` por un pull request de GitHub (#1 a #12)

### Sesión 12 (Fecha: 2026-10-20) — Extensión de VS Code (rama `ide`, detalle en `docs/IDE_LOOP.md`)
- [x] Tareas 1 a 23: gramática de colores generada desde el compilador (`tools/gen_tmgrammar.py`); servidor de
      lenguaje (`compiler/lsp.py`) con errores al escribir (`fichero:línea:columna`), completar, ayuda de firmas,
      hover, ir a la definición, referencias, símbolos, renombrar, formatear y acciones rápidas
- [x] Compilar y ejecutar: tareas, CodeLens, máquinas del emulador (A1200, A500, 3.2, RTG; FS-UAE o Amiberry),
      salida en vivo, memcheck con `fichero:línea` y perfil en un panel
- [x] Depurar (F5): `./dash --debug` (`-O0 -g` y `#line` hacia el `.dash`), `bgdbserver` en el Amiga y
      `m68k-amigaos-gdb` como adaptador; valores y expresiones en forma de Dash (`tools/gdb/dash.py`); también en
      un Amiga real por la red (`tools/gdb_relay.py`)
- [x] Editor visual: teclado, copiar y pegar, arrastrar, deshacer; de un evento a su código; Ver en Amiga con un
      emulador que se queda encendido (`tools/emu_preview.py`)
- [x] Dash: Nuevo proyecto, guía de primeros pasos, modo restringido, empaquetado 0.2.0

### Sesión 13 (Fecha: 2026-10-20/21) — Vídeo tutorial y caza de errores (detalle en `docs/IDE_VIDEO_LOOP.md`)
- [x] Vídeo de 6 capítulos con subtítulos (382 s), grabado con la extensión instalada. Grabarlo sacó fallos, cada
      uno con su test: `./dash -q` (solo avisos, errores y resultado), rutas con espacios y tildes, BOM y Latin-1
      en las fuentes, dos `./dash` a la vez (cerrojo en `build/`), depurador mucho más rápido (81 s a 0,9 s)
- [x] Versión 0.2.1; antes de fusionar en `main` (#11): 328 sin emulador, 778/778 en el emulador (A1200, A500 y 3.2) y 481/481 con `--memcheck`
- [x] Release `vscode-0.2.1` en GitHub (el `.vsix` y el vídeo); el vídeo, también en YouTube:
      https://youtu.be/_UTJ_0s3xLc

### Sesión 14 (Fecha: 2026-10-20/21) — D62-D67
- [x] Alfa de verdad en las imágenes RGBA en RTG: `image_draw`, `image_draw_part` e `image_scale` mezclan (D62)
- [x] El ratón sobre un `mui_canvas` sin clic: `mui_canvas_on_move`, `mui_canvas_pointer_x`/`_y`/`_inside` (D63)
- [x] Imágenes sin tope: antes, desde la 65 daba 0 (D64)
- [x] `d.get(clave, defecto)`: el valor de un diccionario o el de por defecto, en una sola búsqueda (D65)
- [x] Menos copias de textos: funciones que no liberan nada reciben sus argumentos sin copia (D66)
- [x] `mui_canvas_update_area`: repintar solo una zona de un lienzo, también con búfer (D67)
- [x] Arreglo: `file_eof` mira el siguiente byte sin comérselo; un bucle `while not file_eof(h)` con
      `file_read_byte` perdía un byte de cada dos
- [x] Test suite: 329 resultados sin emulador (2026-10-21); 34 ejemplos

### Sesión 15 (Fecha: 2026-10-21) — arreglos y D68
- [x] Una función con nombre en una variable (`g = doble`, `var g: Func = doble`, también global) se llama con `g(x)`
- [x] `sprite_load` lee el dibujo (marcos de 16 píxeles uno al lado de otro) y `sprite_frame` cambia el marco
- [x] `On Timer` funciona también con ventanas de `window_create`
- [x] `lib/amiga/dos.dash`: `SEEK_*` con los valores de AmigaDOS
- [x] `dos_requesters(on)` y `base64_to_file(texto, fichero)` para dashweb (D68)

### Sesión 16 (Fecha: 2026-10-22/24) — Trasfondo, Ratonera, red y D69-D72 (PR #16 a #36)
- [x] Commodity: `tooltype`, `cx_broker`, `cx_hotkey`, `cx_command` y `cx_wait` (#16)
- [x] Para un medidor: volúmenes (`disks_read`, `disk_*`), interfaces de Roadshow (`net_ifs_read`, `net_if_*`) y
      WiFi (`wifi_read`) (#17); drivers SANA-II con cualquier pila, MiamiDx o AmiTCP también (`net_drivers_read`,
      `net_driver_read`, `net_driver_packets_*`, `wifi_read_device`) (#18, #24); el driver queda abierto entre
      lecturas (#33); bytes sin Roadshow si el driver los cuenta (`net_driver_bytes_*`, `net_driver_has_bytes`) (#35)
- [x] Red: servidor TCP (`net_listen`, `net_accept`, `net_peer`, `net_port`) y UDP (`net_udp_open`, `_send`, `_recv`,
      `_from`), con difusión (#19); la red desde una tarea de `task_start`, una sola dueña a la vez, y
      `_dash_task_wake()` (D69, #21)
- [x] Ratonera: `mouse_curve` (curva de aceleración por ratón: parche de `input.device` e input handler),
      `usb_hid_*` (Poseidon) y `mouse_prefs_*` (#20)
- [x] Comparar textos con `nil` ya no lee la dirección 0, que falla en AmigaOS 4 (D70, #22)
- [x] Catálogos de idioma (`locale.library`): `@catalog`, `tr(id, texto)`, `catalog_open`, `catalog_language`;
      `"tr"` en los `.dashui`; `tools/catalogo.py` hace `.cd`, `.ct` y `.catalog` sin FlexCat (D71, #26)
- [x] Un objeto de un `.dashui` que se llama como una global ya no la pisa: es un campo del struct de la
      ventana (D72, #27)
- [x] `desktop_canvas` con Directory Opus 5 o Scalos de escritorio (#28) y recoge otra vez el fondo cuando el
      escritorio se repinta (#29)
- [x] Ventanas GadTools que caben: `window_create` con flag 8 (tamaño interior), `window_border_top/bottom/left/right`,
      `screen_font_height`, `screen_font_text_width`; los gadgets cuentan desde el interior (#30, #31)
- [x] `@version "Prog 1.2"` (`$VER:` para `C:Version`) y `program_version()`; `clock_read`, `clock_*` y
      `date_text(formato)` con `FormatDate` (#32)
- [x] `file_notify`, `file_changed`, `file_notify_end`, `file_notify_signal` (`cx_wait` despierta con 7);
      `run_program(orden)` y `program_relaunch()` (#34)
- [x] Arreglo: un objeto que llega como `(LONG)` se pasa como puntero a `_dash_obj_set` (#25)
- [x] Extensión de VS Code: casilla "al cambiar" de Ver en Amiga (`dash.emulator.previewOnChange`), en `main` y aún
      sin publicar (#23)
- [x] `docs/REQUERIMIENTOS_FUNCIONALES.md`: RF3.3 dice lo que hay de red y lo que falta (#36)
- [x] El `NetShutdown` de Roadshow (WHDLoad) ya no cierra el programa: su aviso es una señal propia, no Ctrl-C, y
      la red se suelta en `cx_wait`, `mui_wait_event` o la siguiente llamada `net_`; `net_stack_running` sabe
      que Roadshow se apagó (probado con Roadshow 1.15 en FS-UAE)
- [x] `pistorm_temperature()`: la temperatura de la Raspberry Pi de una PiStorm, por el `mailbox.resource` de Emu68
- [x] `desktop_canvas` más barato: copias RTG en el formato de la pantalla y comparadas por filas, velos mezclados
      una vez (`desktop_canvas_veil`, `desktop_canvas_veil_rect`) y `desktop_canvas_drawing`; Trasfondo en RTG del
      99 % de CPU al 22 %
- Trasfondo publica su v0.5 (https://github.com/FreeMEM/trasfondo)
- [x] 660 builtins (86 de MUI); unos 362 resultados sin emulador; 34 ejemplos

---

### Sesión 17 (Fecha: 2026-10-24) — errores sin Guru
- [x] Un campo o un método de `nil` para el programa con `Error: campo de nil (en prog.dash:12)` en vez de leer
      basura o escribir en la dirección 0 (`_DASH_NN` con fichero y línea; `--memcheck` avisa y sigue)
- [x] Las excepciones de la CPU (dirección impar, instrucción ilegal, división por cero, CHK, TRAPV...) no dan
      Guru: `tc_TrapCode` propio de la tarea (`TRAP_RUNTIME`), mensaje con el hunk y la distancia, limpieza
      normal y código 20; sin consola, en un requester. En 68000, 68020 y 3.2
- [x] Tests: `# expect-rc: N`; `tools/emu_run.py` arranca con `FailAt 21`

## Notas y Decisiones

### Decisiones tomadas:
1. **Scope:** Léxico estilo Python/Ruby
2. **Funciones:** Sintaxis Ruby (`func ... end`)
3. **Imports:** `import "ruta.dash"`; lo que empieza por `_` es privado del módulo
4. **Arrays:** Sintaxis Python (`[1, 2, 3]`)
5. **Amiga:** Estrategia híbrida (módulos built-in + FFI)
6. **Memoria:** sin recolector; strings con dueño y temporales por vuelta, arrays y structs con contador
   de referencias (los ciclos se liberan al salir con el pool)
7. **Compilación:** `-O2` por defecto (probado en emulador); Kickstart 3.0+, 68000

### Preguntas abiertas:
- ¿Soporte para OOP? (Hay structs con métodos; herencia, no)
- ¿UI declarativa en Dash? Resuelto de otra forma: ficheros `.dashui` (JSON) del editor visual, importables
  (`docs/MUI_EDITOR.md`)
- ¿Macros/metaprogramación? (No por ahora)

### Pendiente:
- Una lista declarada `var x: Array` pierde el tipo de sus elementos (se leen como enteros): hay que declararla
  con su tipo, `var x: [String]`

### Programas hechos con Dash
- **Tachyon** (antes dashweb, pedido el 2026-10-15): navegador ligero con interfaz MUI: XHTML, CSS, JavaScript
  moderno y HTTPS. Sirve para hacer crecer Dash (lenguaje, librerías, rendimiento) con un programa grande y
  exigente: lo que le falta se pide a Dash como tarea `Dnn`. https://github.com/FreeMEM/tachyon. Primera versión
  de prueba, v0.1.0-alfa, el 2026-10-18.
- **Trasfondo**: monitor del sistema (CPU, memoria, discos, red, WiFi) dibujado en el fondo del Workbench, como
  commodity. https://github.com/FreeMEM/trasfondo, v0.5 publicada.
- **Ratonera** (en desarrollo): una curva de aceleración para cada ratón, también los USB de Poseidon.

---

## Referencias

- [AmigaOS NDK](http://amigadev.elowar.com/)
- [Lark Parser](https://lark-parser.readthedocs.io/)
- [m68k-amigaos-gcc](https://github.com/bebbo/amiga-gcc)
