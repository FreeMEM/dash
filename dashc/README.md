# dashc: prueba de concepto de Dash autosuficiente

[English](README.en.md)

`dashc` compila un `.dash` a un ejecutable de Amiga sin compilador de C: genera código 68000, lo
enlaza con el runtime (ya compilado y metido dentro de `dashc`) y escribe el fichero Hunk. Está escrito
en C y el mismo código se compila para el PC y para el Amiga. El runtime es el de `./dash` (memoria,
textos, listas, objetos con contador de referencias, errores): se saca de `compiler/codegen.py`, así que
los programas se comportan igual, también en memoria.

```bash
make                     # dashc para este ordenador
./dashc prog.dash -o prog
make amiga               # build/dashc.amiga: dashc que corre en el Amiga (68000, OS 2.0+)
make test                # tests/*.dash con dashc y con ./dash: misma salida en A1200 y A500 (FS-UAE)
python3 bench/bench_run.py   # velocidad frente a ./dash (gcc -O2) en A500 y A1200 a velocidad real
make runtime             # rehace runtime/dashrt.o con el gcc de bebbo y ./dash (va en git: no hacen falta para lo demás)
```

## Qué entiende

Enteros (decimal, `0x`, `$`, `0b`), `Bool`, `const`, globales con `var`, variables locales, funciones
con parámetros y `return`, `if`/`elif`/`else`, `while`, `for` con rango (`step`, hacia atrás), `break`,
`continue`, `and`/`or`/`not` con cortocircuito, todos los operadores de enteros y `Print`.

- Textos (Latin-1): variables, `+` (también con números), interpolación `#{...}`, `s[i]`, `s[a:b]`,
  `.length`, comparaciones, parámetros y valores devueltos.
- Listas `[...]` y tipos `[T]`: `a[i]`, `a[i] = v`, `push`, `pop`, `insert`, `remove`, `clear`,
  `.length`, trozos, `for x in lista`; de números, textos, structs o listas.
- Structs con valores por defecto, campos, métodos con `self`, `nil` (un campo de nil para el programa
  con el mismo error que `./dash`), structs recursivos y en listas.

Falta: diccionarios, métodos de texto (`find`, `upper`...), `sort`, lambdas, enums, Float y Fixed,
builtins, ventanas, `@native`, `import`.

## Depurar

`dashc --debug prog.dash -o prog` (o `./dash --debug`) pone una instrucción `NOP` al principio de cada línea y
añade al ejecutable un `HUNK_DEBUG` con ficheros, líneas, funciones, variables, globales y campos de los structs
(`dashc --debug-info prog` lo enseña). Sin copiar funciones en línea y con todas las variables en el marco, para que
el depurador las encuentre; el programa hace lo mismo que sin `--debug`.

Los builtins `dbg_*` depuran un programa así desde otro (Forja, el IDE), compilado con cualquiera de los dos
Dash (`./dash` o `./dash --c`):

```ruby
dbg_start("Work:prog", "")              # cargado y en pausa antes de su primera línea
dbg_break("prog.dash", 12)              # un punto de parada (por el final del nombre del fichero)
dbg_continue()
if dbg_wait(0) == 3                     # 3: parado en una línea; 4: acabado
    Print "#{dbg_function()} #{dbg_line()}: p = " + dbg_value(0, "p")
end
dbg_next()                              # dbg_step entra en las funciones; dbg_out sale de esta
dbg_end(5000)                           # lo acaba (su limpieza de siempre); dbg_rc() da su código
```

| Builtin | Qué hace |
|---------|----------|
| `dbg_start(prog, args)`, `dbg_error()` | Cargar en pausa; por qué falló |
| `dbg_state()`, `dbg_wait(ms)`, `dbg_signal()` | Estado (0 nada, 1 en pausa al empezar, 2 corriendo, 3 parado, 4 acabado); esperar; la señal que llega al parar o acabar (para `mui_wait_event_signals`) |
| `dbg_break(fichero, línea)`, `dbg_unbreak(...)` | Puntos de parada |
| `dbg_continue()`, `dbg_step()`, `dbg_next()`, `dbg_out()`, `dbg_pause()` | Seguir, entrar, pasar, salir, parar en la siguiente línea |
| `dbg_end(ms)`, `dbg_rc()`, `dbg_output()` | Acabarlo, su código, lo que ha escrito |
| `dbg_file()`, `dbg_line()`, `dbg_function()` | Dónde está parado |
| `dbg_frames()`, `dbg_frame_function/line/file(i)` | La pila de llamadas (0, donde está) |
| `dbg_vars(i)`, `dbg_var_name/type(i, k)`, `dbg_globals()`, `dbg_global_name(g)` | Las variables de cada marco y las globales |
| `dbg_value(i, expr)`, `dbg_value_type(i, expr)` | El valor como texto (`"p.hijos[0].x"`) y su tipo |
| `dbg_reg(n)`, `dbg_peek(dir, tamaño)` | Registros (0-7 d0-d7, 8-15 a0-a7, 16 el PC) y memoria |

Cómo va (`DEBUGGER_RUNTIME` de `compiler/codegen.py`, plan en `docs/DEPURADOR_LOOP.md`): el programa corre en un proceso hijo con su
manejador de excepciones; un punto de parada cambia el `NOP` de la línea por `TRAP #15`, y al seguir no hay nada que
reponer. Paso a paso, todas las líneas paran y se mira el marco (`a5`). No usa el bit de traza de la CPU, así que
funciona igual en un 68000, en FS-UAE y en Emu68.

Límites: una tarea de `task_start` que pase por una línea con `TRAP` cae (no tiene el manejador); un programa que
espera sin pasar por ninguna línea (en `mui_wait_event`) no acaba con `dbg_end` hasta que vuelve a su código; la
salida se lee antes de `dbg_end`. Tests: `python3 tests/depurar.py [--a500] [--c]`.

`tools/amiga/dbgserver.dash` pone estos builtins en la red: depura un programa y atiende órdenes de una línea por
TCP (su protocolo está al principio del fichero). Es el depurador de la extensión de VS Code
(`editor/vscode/dashDebug.js`); `tools/emu_run.py --dbgserver PUERTO prog` lo arranca en el emulador. Tests:
`python3 tests/depurar_vscode.py [--a500]` (el servidor y, con node, el adaptador de VS Code).

## Cómo está hecho

| Fichero | Qué hace |
|---------|----------|
| `src/lexer.c`, `src/parser.c` | Del texto al árbol, con la gramática de `compiler/grammar.py` |
| `src/gen68k.c` | Código 68000: el valor en d0, llamadas como las de C; cada función se genera dos veces para poner en d2-d7 las variables más usadas |
| `src/hunk.c` | Lee el objeto Hunk del runtime, junta los hunks a los que se llega y escribe el ejecutable (con `DASHC_MAPA=1`, lista lo que entra del runtime, su tamaño y quién lo trajo) |
| `runtime/gen_lib.py` | Saca el runtime de `./dash` del C que genera para `runtime/cocina.dash`, sin lo de libnix |
| `runtime/api.c` | Arranque y salida, `Print`, y con nombre `dl_*` lo que llama el código de dashc |
| `runtime/rt_math.s`, `runtime/rt_libc.c` | `_dash_start`, multiplicar y dividir de 32 bits, lo poco de libc que hace falta |

## Lo comprobado

- Los doce tests dan la misma salida y el mismo código de salida que el Dash de Python en A1200 y
  A500 con la ROM 3.1, también los que crean decenas de miles de textos, listas y structs en un A500.
- `build/dashc.amiga` compila los doce dentro de un A500 emulado; los ejecutables salen idénticos byte
  a byte a los del PC (con el mismo nombre de fuente, que va dentro para los errores) y funcionan.
- Los ejecutables ocupan entre 12 y 16 KB, porque llevan el runtime entero (con gcc, entre 6 y 17 KB):
  falta enlazar solo lo que se usa.
- Velocidad (`bench/bench_enteros.dash`, veces el tiempo de gcc `-O2`; menos de 1 es más rápido):
  de media 0,92 en A500 y 0,97 en A1200 (el emulador varía un 3 % entre medidas). Lo más lento,
  1,05 (bucles anidados: gcc deduce que si i < j, i == j es falso); lo más rápido, la recursión
  (fib, 0,55 y 0,70).
- Optimizaciones, como las de gcc: variables en d2-d7; una función pequeña o llamada desde un solo
  sitio se copia donde se llama (no si es recursiva), y la de una línea, como expresión; un `for` o
  un `while` que solo suma 1 cuenta con `dbra`; `i * k` en un bucle se lleva sumando; una variable
  asignada una sola vez con un valor fijo es una constante; el índice de un `for` tiene rango
  conocido y con él la división y el producto de 16 bits van sin comprobaciones; multiplicar y
  dividir prueban en línea el caso de 16 bits; en 68020 o mejor, el runtime usa `divs.l` y `muls.l`;
  los saltos que llegan con 8 bits van en su forma corta.
