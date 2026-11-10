# Sintaxis de Dash en una página

Resumen al día del lenguaje para escribir código Dash. Referencia completa: `docs/QUICK_REFERENCE.md` y
`docs/MANUAL_REFERENCIA.md`; la lista real de builtins es `docs/BUILTINS.md`.

## Estructura de un programa
```ruby
import "lib/math_utils.dash"   # imports (rutas relativas)

const MAX = 100                # constantes
enum State IDLE, RUN end       # enums (también uno por línea, con "= N" opcional)
struct Player x: Int end       # structs
Window Win title "App" end     # ventanas
func f() end                   # funciones

Main
    # punto de entrada
end
```

## Variables y tipos (primera asignación declara)
```ruby
x = 10
nombre = "Dash"
activo = true
nums = [1, 2, 3]
p = Player(10, 20)
var lista: Nodo = nil          # nil (C NULL) para structs, Array y String; x == nil, x = nil
f = Fixed(1.5)                 # coma fija 16.16 (DashFixed): Fixed*Int entero, Fixed*Fixed _dash_fx_mul
x = 1.5                        # Float (por software, runtime/softfloat)
c = 0xDFF000                   # literales hex y binarios (0b1010)
```

## Control de flujo
```ruby
if cond
else
end

while cond
end

for i in (1..10)               # (3..1) cuenta hacia atrás; (0..10 step 5), (10..1 step -3)
    if i in (3..5) or i in [7, 9]   # in: rango, lista, texto, diccionario; not in; 1 <= i <= 10
        Print i
    end
    if i == 5
        continue               # también break
    end
end

for item in array
end
```

## Funciones (tipos opcionales)
```ruby
func suma(a, b)
    return a + b
end

func doble(x: Int) -> Int      # tipos: Int, Float, String, Bool, Array, Pointer, Void, Func, struct, enum (otro: error)
    return x * 2
end

doble_l = fn(x) -> x * 2       # lambda (soporte parcial, ver examples/test_lambda.dash)
```

## Arrays y strings
```ruby
arr = [1, 2, 3, 4, 5]
arr[2] = 99
n = arr.length
trozo = arr[1:3]               # slicing: [a:b], [:b], [a:] (también en strings: s[5:])

s = "Hola, " + nombre          # concatenación
c = nombre[0]                  # carácter
m = "Hola #{nombre}!"          # interpolación
```

## Structs con métodos y enums
```ruby
struct Enemy
    x: Int = 0
    health: Int = 100

    func move(dx)
        self.x = self.x + dx
    end
end

e = Enemy(10, 50)
e.move(5)

enum State
    IDLE = 0
    RUNNING = 1
end
st = State.RUNNING
```

## FFI
```ruby
@extern("mylib.library")
func MyFunc(x: Int) -> Int

@native func peek(addr: Pointer) -> Int
"""
    return (LONG)*(volatile UBYTE *)addr;
"""
end
```

## Ventanas y eventos
```ruby
MiVentana.open

EventLoop
    On Close
        Stop
    end
    On Key "a"                 # On Key sin texto: cualquier tecla (key_raw())
        Print "tecla a"
    end
end
```

Comandos: `Print`, `Wait`, `Stop`.

## Scope léxico

- Variables declaradas en bloques (if/while/for) son locales a ese bloque
- Se puede acceder y modificar variables del scope padre
- Las variables del bloque hijo NO son visibles en el padre
- Funciones con prefijo `_` en un módulo importado son privadas

## Qué C genera

| Dash | C |
|------|---|
| número | `LONG` |
| string | `STRPTR` |
| boolean | `BOOL` |
| array | `DashArrayLong` (runtime, con bounds checking) |
| struct | `struct` C con constructor generado |
