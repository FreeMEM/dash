# dashc: prueba de concepto de Dash autosuficiente

[English](README.en.md)

`dashc` compila un `.dash` a un ejecutable de Amiga sin compilador de C: genera código 68000, lo
enlaza con el runtime (ya compilado y metido dentro de `dashc`) y escribe el fichero Hunk. Está escrito
en C y el mismo código se compila para el PC y para el Amiga.

```bash
make                     # dashc para este ordenador
./dashc prog.dash -o prog
make amiga               # build/dashc.amiga: dashc que corre en el Amiga (68000, OS 2.0+)
make test                # tests/*.dash con dashc y con ./dash: misma salida en A1200 y A500 (FS-UAE)
python3 bench/bench_run.py   # velocidad frente a ./dash (gcc -O2) en A500 y A1200 a velocidad real
make runtime             # rehace runtime/dashrt.o con el gcc de bebbo (va en git: no hace falta para lo demás)
```

## Qué entiende

Enteros (decimal, `0x`, `$`, `0b`), `Bool`, `const`, globales con `var x: Int = valor fijo`,
variables locales, funciones con parámetros y `return`, `if`/`elif`/`else`, `while`, `for` con rango
(`step`, hacia atrás), `break`, `continue`, `and`/`or`/`not` con cortocircuito, todos los operadores de
enteros y `Print` de un entero, un Bool o un texto literal (en Latin-1).

Falta todo lo demás: textos en variables, arrays, structs, Float, builtins, ventanas, `@native`...

## Cómo está hecho

| Fichero | Qué hace |
|---------|----------|
| `src/lexer.c`, `src/parser.c` | Del texto al árbol, con la gramática de `compiler/grammar.py` |
| `src/gen68k.c` | Código 68000: el valor en d0, llamadas como las de C; cada función se genera dos veces para poner en d2-d7 las variables más usadas |
| `src/hunk.c` | Lee el objeto Hunk del runtime, junta los hunks y escribe el ejecutable |
| `runtime/rt.c`, `runtime/rt_math.s` | Arranque, `Print`, multiplicar y dividir de 32 bits en un 68000 |

## Lo comprobado

- Los siete tests dan la misma salida que el Dash de Python en A1200 y A500 con la ROM 3.1.
- `build/dashc.amiga` compila los siete dentro de un A500 y de un A1200 emulados; los ejecutables
  salen idénticos byte a byte a los del PC y funcionan.
- Los ejecutables ocupan entre 1,7 y 4,7 KB (con gcc, entre 6 y 9,5 KB).
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
