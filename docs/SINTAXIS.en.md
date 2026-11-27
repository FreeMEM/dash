# Dash syntax on one page

An up-to-date summary of the language for writing Dash code. Full reference: `docs/QUICK_REFERENCE.en.md` and
`docs/MANUAL_REFERENCIA.en.md`; the real list of builtins is `docs/BUILTINS.en.md`.

<!-- indice -->
<a id="index"></a>

**Index**

- [Structure of a program](#structure-of-a-program)
- [Variables and types (the first assignment declares)](#variables-and-types-the-first-assignment-declares)
- [Control flow](#control-flow)
- [Functions (optional types)](#functions-optional-types)
- [Arrays and strings](#arrays-and-strings)
- [Structs with methods, and enums](#structs-with-methods-and-enums)
- [FFI](#ffi)
- [Inline assembler (68000, Motorola syntax; docs/ASM_DISEÑO.md)](#inline-assembler-68000-motorola-syntax-docsasm_diseñomd)
- [Windows and events](#windows-and-events)
- [Lexical scope](#lexical-scope)
- [What C it makes](#what-c-it-makes)
<!-- /indice -->

<a id="structure-of-a-program"></a>

## Structure of a program
```ruby
import "lib/math_utils.dash"   # imports (relative paths)

const MAX = 100                # constants
enum State IDLE, RUN end       # enums (also one per line, with an optional "= N")
struct Player x: Int end       # structs
Window Win title "App" end     # windows
func f() end                   # functions

Main
    # entry point
end
```

[Back to the index](#index)

<a id="variables-and-types-the-first-assignment-declares"></a>

## Variables and types (the first assignment declares)
```ruby
x = 10
name = "Dash"
active = true
nums = [1, 2, 3]
p = Player(10, 20)
var list: Node = nil           # nil (C NULL) for structs, Array and String; x == nil, x = nil
f = Fixed(1.5)                 # 16.16 fixed point (DashFixed): Fixed*Int integer, Fixed*Fixed _dash_fx_mul
x = 1.5                        # Float (in software, runtime/softfloat)
c = 0xDFF000                   # hex and binary literals (0b1010)
```

[Back to the index](#index)

<a id="control-flow"></a>

## Control flow
```ruby
if cond
else
end

while cond
end

for i in (1..10)               # (3..1) counts down; (0..10 step 5), (10..1 step -3)
    if i in (3..5) or i in [7, 9]   # in: range, list, text, dictionary; not in; 1 <= i <= 10
        Print i
    end
    if i == 5
        continue               # also break
    end
end

for item in array
end
```

[Back to the index](#index)

<a id="functions-optional-types"></a>

## Functions (optional types)
```ruby
func add(a, b)
    return a + b
end

func double(x: Int) -> Int     # types: Int, Float, String, Bool, Array, Pointer, Void, Func, struct, enum (other: error)
    return x * 2
end

double_l = fn(x) -> x * 2      # lambda (partial support, see examples/test_lambda.dash)
```

[Back to the index](#index)

<a id="arrays-and-strings"></a>

## Arrays and strings
```ruby
arr = [1, 2, 3, 4, 5]
arr[2] = 99
n = arr.length
part = arr[1:3]                # slicing: [a:b], [:b], [a:] (also in strings: s[5:])
arr.push(6)                    # also pop(), insert(i, x), remove(i), clear(), sort(f)
yes = arr.has(99)              # true if it is there: as 99 in arr

s = "Hello, " + name           # concatenation
c = name[0]                    # character
m = "Hello #{name}!"           # interpolation
```

[Back to the index](#index)

<a id="structs-with-methods-and-enums"></a>

## Structs with methods, and enums
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
boss().x = 0                   # the field of what a function returns (-> Enemy)

enum State
    IDLE = 0
    RUNNING = 1
end
st = State.RUNNING
```

[Back to the index](#index)

<a id="ffi"></a>

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

[Back to the index](#index)

<a id="inline-assembler-68000-motorola-syntax-docsasm_diseñomd"></a>

## Inline assembler (68000, Motorola syntax; docs/ASM_DISEÑO.md)
```ruby
func add(a: Int, b: Int) -> Int
    asm in d0 = a, d1 = b out r = d0 uses d2     # in: register = value; out: variable = register
        move.l  d1,d2                           ; ; starts a comment; labels .x: or x:
        add.l   d2,d0                           ; registers: d0-d7, a0-a4, a6 (not a5 nor sp)
    end                                          # ends at the line that only says end
    return r
end
```
A string goes in as the address of its characters and a list as the address of its first element. Data:
`dc.b/w/l`, `dc.s/d`, `ds`, `even`, `cnop 0,4`, `incbin "f"`; constants `X equ 5` and Dash's `const`. Sections:
`data`, `bss`, `data_c`/`bss_c` (chip memory), `code` to go back. `jsr name` calls a Dash function (arguments on the
stack, result in d0); `GfxBase`, `DOSBase`... are the bases. 68020 instructions (`muls.l`, `bfextu`, `([a0],4)`...),
with `--cpu 68020`; the FPU (`fmove`, `fadd`, `fbeq`... and `uses fp2`), with `--fpu`. `asm` is not reserved:
outside that line it is just a name (`func asm(x)`), like `int` or `default`.
```ruby
asm func add(a: Int, b: Int) -> Int     # a function in asm: parameters in d0, d1...; returns d0 (or out d1)
    add.l   d1,d0
end
s = vblank_server(my_vblank, data)       # my_vblank(data) on each VBlank; int_server_remove(s) or at exit
```

[Back to the index](#index)

<a id="windows-and-events"></a>

## Windows and events
```ruby
MyWindow.open

EventLoop
    On Close
        Stop
    end
    On Key "a"                 # On Key without text: any key (key_raw())
        Print "key a"
    end
end
```

Commands: `Print`, `Wait`, `Stop`.

[Back to the index](#index)

<a id="lexical-scope"></a>

## Lexical scope

- Variables declared in blocks (if/while/for) are local to that block
- Variables of the parent scope can be read and changed
- The variables of a child block are NOT visible in the parent
- Functions with a `_` prefix in an imported module are private

[Back to the index](#index)

<a id="what-c-it-makes"></a>

## What C it makes

| Dash | C |
|------|---|
| number | `LONG` |
| string | `STRPTR` |
| boolean | `BOOL` |
| array | `DashArrayLong` (runtime, with bounds checking) |
| struct | C `struct` with a generated constructor |

[Back to the index](#index)
