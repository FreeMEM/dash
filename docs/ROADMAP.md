# D.A.S.H. Language - Hoja de Ruta de Desarrollo
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

**Versión del documento:** 2.0
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

## Estado Actual (v2.0)

### Implementado ✅

- [x] Definición de ventanas (`Window ... end`)
- [x] Bloque principal (`Main ... end`)
- [x] Comandos básicos (`Print`, `Wait`, `Stop`)
- [x] Event Loop con `On Close`
- [x] Variables (asignación declara, estilo Python)
- [x] Expresiones aritméticas (`+`, `-`, `*`, `/`, `%`)
- [x] Expresiones lógicas (`and`, `or`, `not`)
- [x] Comparaciones (`==`, `!=`, `<`, `>`, `<=`, `>=`)
- [x] Control de flujo (`if`/`else`/`end`, `while`/`end`)
- [x] Comentarios (`# ...`)
- [x] Tipos inferidos (LONG, STRPTR, BOOL)

### Arquitectura del Compilador ✅

```
Source (.dash) → Parser (Lark) → AST → Analyzer → CodeGen → C → GCC → Amiga Executable
```

- `grammar.py` - Gramática Lark
- `transformer.py` - Parse tree → AST
- `ast_nodes.py` - Definición de nodos AST
- `analyzer.py` - Análisis semántico, tabla de símbolos
- `codegen.py` - Generación de código C

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
- Funciones deben definirse antes de usarse (o forward declaration)

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
- ¿Funciones como valores? No en v3.0 (futuro)
- ¿Closures? No en v3.0 (futuro)

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

# Operaciones (fase posterior)
numeros.push(6)
ultimo = numeros.pop()
```

**Reglas:**
- Arrays son homogéneos (todos elementos mismo tipo)
- Índices base 0
- Bounds checking en runtime (error si fuera de rango)
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
- [x] `runtime/dash_array.h`: Runtime library para arrays
- [x] Tests: `test_array_basic.dash`, `test_array_ops.dash`

**Consideraciones:**
- Arrays de arrays (matrices): Fase posterior
- Slicing (`arr[1:3]`): Fase posterior

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

# Interpolación (fase posterior)
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
- [x] `runtime/dash_string.h`: DashString_concat, DashString_length, DashString_char_at
- [x] Tests: `test_string_ops.dash`

**Consideraciones:**
- Memory management de strings concatenados (caller debe liberar)
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
- `import "file.dash"` - carga el archivo y hace disponibles sus funciones públicas
- Funciones privadas (con `_` al inicio) NO son importadas
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
    # _internal()       # Error - función no definida
end
```

### 2.2 Exports
**Estado:** ⬜ No implementado (decisión: no necesario)

**Nota:** Se decidió usar el enfoque estilo Python donde todo es público por defecto, excepto funciones que empiezan con `_` que son privadas. Esto simplifica el lenguaje sin necesidad de keyword `export`.

---

## Fase 3: Soporte Amiga

**Objetivo:** Acceso completo a las APIs de AmigaOS.

### Estrategia: Híbrida (A + B)

Combinar:
- **Módulos Built-in** (Estrategia A): API de alto nivel, el compilador conoce y optimiza
- **FFI** (Estrategia B): Escape hatch para acceso directo cuando sea necesario

### 3.1 Módulos Built-in
**Estado:** ✅ Completado (161 funciones)
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

**Ejemplo - amiga/graphics:**
```ruby
import Graphics from "amiga/graphics"

Main
    MyWindow.open

    # API de alto nivel
    Graphics.pen(MyWindow, 1)        # SetAPen
    Graphics.move(MyWindow, 10, 10)  # Move
    Graphics.line(MyWindow, 100, 50) # Draw
    Graphics.rect(MyWindow, 20, 20, 80, 60)  # RectFill
    Graphics.text(MyWindow, "Hola")  # Text

    # ...
end
```

**Implementación:**
El compilador traduce `Graphics.line(win, x, y)` a:
```c
Move(win->RPort, currentX, currentY);
Draw(win->RPort, x, y);
```

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

**Tipos soportados:** `Int`, `String`, `Bool`, `Pointer`, `Void`

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
- Constructores con `AllocMem` para heap allocation
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

Para soportar arrays, strings, y otras features, necesitamos una pequeña runtime library en C que se linkea con cada programa Dash.

**Archivos:**
```
runtime/
├── dash_runtime.h     # Headers
├── dash_array.c       # Operaciones de array
├── dash_string.c      # Operaciones de string
└── dash_memory.c      # Gestión de memoria (wrappers de AllocMem/FreeMem)
```

**Consideraciones Amiga:**
- Usar `AllocMem`/`FreeMem` de exec.library
- Memoria CHIP vs FAST según necesidad
- Pool de memoria para eficiencia

---

## Testing

### Estructura de Tests
```
tests/
├── test_*.dash          # Todos los tests en directorio raíz
├── lib/                 # Módulos de librería para tests de import
│   └── math_utils.dash
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

---

## Notas y Decisiones

### Decisiones tomadas:
1. **Scope:** Léxico estilo Python/Ruby
2. **Funciones:** Sintaxis Ruby (`func ... end`)
3. **Imports:** Estilo ES6 (`import X from "y"`)
4. **Arrays:** Sintaxis Python (`[1, 2, 3]`)
5. **Amiga:** Estrategia híbrida (módulos built-in + FFI)

### Preguntas abiertas:
- ¿Garbage collection o gestión manual con helpers?
- ¿Soporte para OOP? (Probablemente no en v3.0)
- ¿Macros/metaprogramación? (Probablemente no en v3.0)

---

## Referencias

- [AmigaOS NDK](http://amigadev.elowar.com/)
- [Lark Parser](https://lark-parser.readthedocs.io/)
- [m68k-amigaos-gcc](https://github.com/bebbo/amiga-gcc)
