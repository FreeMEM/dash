# Ensamblador en línea en Dash

Encargo de Forja (FORJA_LOOP 5.1), decidido por el usuario: Dash tiene ensamblador 68k en línea, para demos. El
mismo fuente da el mismo resultado por los dos caminos: `./dash` (directo a hunk, con un ensamblador propio en
`dashc/src/asm68k.c`) y `./dash --gcc` (el bloque pasa al `as` de GCC dentro de un `__asm__`).

## Sintaxis

Un bloque `asm ... end` dentro de una función o de `Main`. La línea de `asm` dice qué entra y qué sale; el cuerpo es
ensamblador con la sintaxis de Motorola (Devpac, ASM-One, vasm):

```ruby
func suma_lista(datos: Pointer, n: Int) -> Int
    asm in a0 = datos, d0 = n - 1 out total = d1
        moveq   #0,d1
    .bucle:
        add.l   (a0)+,d1        ; un comentario
        dbra    d0,.bucle
    end
    return total
end
```

- `in r = expresión, ...`: antes del bloque, cada registro recibe el valor de una expresión de Dash.
- `out variable = r, ...`: después, cada variable recibe lo que quedó en el registro (un Int; una variable nueva
  queda declarada como Int).
- `uses r, ...`: los demás registros que el bloque cambia. Admite listas como las de `movem`: `uses d2-d4/a1`.
- Las tres partes son opcionales, en cualquier orden, cada una una vez. Una expresión de `in` con la palabra `in`
  dentro (`x in lista`) va entre paréntesis.
- El bloque acaba en la primera línea que solo tiene `end`.

Registros: d0-d7, a0-a4 y a6. a5 no (es el marco de las funciones de Dash) ni a7/sp. Todo registro que el bloque
cambie tiene que estar en `in`, `out` o `uses`; los demás deben quedar como estaban (el bloque puede guardarlos él
mismo en la pila). Los códigos de condición y la memoria siempre se pueden cambiar. La pila tiene que quedar como
estaba, y el bloque acaba por abajo: nada de `rts` ni de saltos fuera.

Qué recibe un registro de `in`, según el tipo de la expresión:

| Tipo | Valor |
|------|-------|
| Int, Bool, Pointer, enum | el número (Bool: 1 o 0) |
| Fixed | sus 32 bits (16.16) |
| String | la dirección de su primer carácter |
| lista (`[Int]`...) | la dirección de su primer elemento, de 4 bytes cada uno (0 si es `nil`) |
| struct | su dirección (la forma de un struct por dentro no es fija: mejor pasar sus campos) |
| Float, Double | error: se pasa `Int(x)` o `Fixed(x)` |

### El cuerpo

Una instrucción por línea: `[etiqueta:] instrucción[.tamaño] operandos [; comentario]`. Una línea que empieza por
`*` es un comentario. Mayúsculas o minúsculas en instrucciones y registros, como se quiera; las etiquetas sí las
distinguen. Los operandos pueden llevar espacios (`move.l d0, d1`).

- **Etiquetas**: `nombre:` (o `nombre` sin dos puntos en la columna 1). Pueden empezar por punto (`.bucle`). Son
  del bloque: dos bloques pueden usar el mismo nombre.
- **Números**: `123`, `$1F`, `0x1F`, `%1010`, `0b1010`, `'A'` (hasta 4 caracteres). Expresiones con `+ - * / << >>
  & | ^ ~` y paréntesis, con la prioridad de C. Los nombres valen etiquetas, constantes del bloque y `const` de Dash.
- **Constantes del bloque**: `ANCHO equ 320` o `ANCHO = 320`.
- **Datos**: `dc.b 1,2,"texto",0` (el texto tal cual, sin escapes), `dc.w`, `dc.l` (con etiquetas: `dc.l tabla`;
  un texto entre comillas en `dc.w`/`dc.l` es un número), `ds.b n` (`ds.w`, `ds.l`: ceros), `even`,
  `incbin "fichero"[,desde[,cuántos]]` (ruta relativa al `.dash`). `dc.w`, `dc.l`, `ds.w`, `ds.l` y las
  instrucciones se alinean a par solas, como en Devpac (y la etiqueta de delante con ellas); el final del bloque
  también. Los datos van entre el código: el bloque salta por encima (`bra.s .fin`). No son memoria chip (para el
  copper o los sprites, se copian a memoria chip). Sin `cnop` ni alinear a 4: el directo acorta saltos de antes
  del bloque al final de la función y el bloque se mueve de 2 en 2 bytes.
- **Saltos**: `bra`, `bcc`... sin tamaño eligen solos el corto o el largo; `.s`/`.b` y `.w` lo fijan.

### Instrucciones

Todas las del 68000, con todos sus modos de direccionamiento (los dos estilos de Motorola: `4(a0)` y `(4,a0)`;
`8(a0,d1.w)` y `(8,a0,d1.l)`; `tabla(pc)`; `$dff180` absoluto, `4.w` corto), y los alias de siempre (`dbra`, `bhs`,
`blo`, `shs`, `slo`; `add #n` es `addi`, `add` a un `An` es `adda`, `move` a un `An` es `movea`...).

Del 68020, con `--cpu 68020` o más (o `--fpu`; por `--gcc` el aviso sale al compilar el C, con la línea del `.dash`): `muls.l`/`mulu.l` (32 y 64 bits), `divs.l`/`divu.l`/`divsl.l`/
`divul.l`, `extb.l`, los campos de bits (`bfextu d0{4:8},d1`, `bfexts`, `bfins`, `bfset`, `bfclr`, `bfchg`,
`bftst`, `bfffo`), saltos de 32 bits (`bra.l`), `link.l`, `rtd`, `chk.l`, índice con escala (`(a0,d0.l*4)`) y
desplazamientos grandes en `(d,An,Xn)`. Sin ellas da un error que lo dice. No están: la FPU, la MMU, la
indirección de memoria (`([...])`), `cas`, `cas2`, `chk2`, `cmp2`, `pack`, `unpk`, `trapcc`, `callm`, `movec`.

## Los dos caminos

**Directo (`./dash`)**: dashc lee el bloque en el léxico (`asm_extract`, igual que el preprocesado de Python) y lo
cambia por llamadas internas: `__dash_asm(n, entradas...)` y, por cada salida, `var = __dash_asm_out(n, j)`. Así
el resto del compilador ve las asignaciones (registros, rangos, bucles). Al generar:

1. Reserva en la pila tantos huecos como el mayor de entradas y salidas, y deja ahí cada entrada.
2. `movem.l` guarda los registros de d2-d7/a2-a6 que el bloque toca (los de las variables de Dash y los que C
   espera intactos).
3. Carga cada entrada en su registro desde la pila, ensambla el cuerpo en el sitio (`asm68k.c`: dos o más pasadas
   hasta que los saltos y las etiquetas no cambian; reubicaciones al hunk de código para `dc.l etiqueta`,
   `lea etiqueta,a0`...), deja cada salida en su hueco, recupera los registros y cada `__dash_asm_out` saca la suya.

**Por C (`./dash --gcc`)**: Python lee el bloque igual (`compiler/asm68k.py`), comprueba lo mismo (instrucciones,
tamaños, número de operandos, nombres, registros) y lo pasa a un `__asm__ volatile` con variables `register ...
__asm__("d0")` para las entradas y salidas, y `uses` como registros pisados (más `"cc"` y `"memory"`). El texto
va normalizado para el `as` de binutils (que entiende la sintaxis de Motorola con registros sin `%`): números en
decimal (su `|` es un comentario y su `%` el de las plantillas de GCC), etiquetas `.L` con `%=` (únicas aunque GCC
copie la función), `dc.b "texto"` en bytes, `even` y `cnop` como `.even` y `.balign`, `incbin` con su ruta
completa. Las instrucciones del 68020 piden `--cpu 68020`: el C lleva un `#error` que lo dice si no.

Las entradas se calculan antes en temporales `volatile` (el fallo de GCC 6 con `register asm` y las llamadas a
libgcc, ver AGENTS.md).

**DashOS (AArch64)**: un bloque `asm` es 68k: error claro.

## Pendiente (no en esta versión)

- Funciones enteras en ensamblador (`@asm func`) y llamar desde el bloque a funciones de Dash o del runtime.
- Secciones en memoria chip (`section data_c`): `hunk.c` aún no admite hunks con memoria chip.
- FPU (`fmove`...), las instrucciones del 68020 de la lista de arriba y la indirección de memoria.
- Interrupciones en ensamblador (un servidor de VBlank).
