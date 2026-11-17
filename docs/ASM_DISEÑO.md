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

Registros: d0-d7, a0-a4 y a6. a5 no (es el marco de las funciones de Dash) ni a7/sp. Con `--fpu`, `uses` admite
también fp0-fp7 (`uses fp0-fp3`): el bloque guarda y recupera los que C espera intactos (fp2-fp7); no van en `in`
ni en `out` (un valor pasa por un registro de datos: `fmove.l d0,fp0`, `fmove.s fp0,d0`). Todo registro que el bloque
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
  un texto entre comillas en `dc.w`/`dc.l` es un número), `dc.s 1.5` y `dc.d -2.0` (coma flotante de 32 y 64
  bits), `ds.b n` (`ds.w`, `ds.l`: ceros), `even`, `cnop 0,4` (alinea a 2, 4 u 8),
  `incbin "fichero"[,desde[,cuántos]]` (ruta relativa al `.dash`). `dc.w`, `dc.l`, `ds.w`, `ds.l` y las
  instrucciones se alinean a par solas, como en Devpac (y la etiqueta de delante con ellas); el final del bloque
  también. Los datos del código van entre las instrucciones: el bloque salta por encima (`bra.s .fin`).
- **Secciones**: `section nombre,tipo` o solo el tipo: `code` (o `text`), `data`, `bss`, `data_c` y `bss_c` (las
  dos últimas, en memoria chip: listas del copper, sprites, planos, sonido). Lo que va en una sección de datos
  queda fuera del código, en un hunk aparte, y se guarda entre llamadas (un contador en `bss` sigue la cuenta). En
  una sección de datos solo van datos; en `bss` y `bss_c`, `ds`, `even` y `cnop`. El bloque vuelve al código con
  `code`. Las etiquetas de una sección se usan desde el código con su dirección (`lea tabla,a0`,
  `move.l #tabla,d0`, `dc.l tabla`); `(pc)` y los saltos solo llegan al código del bloque. Una función con un bloque
  con secciones no se copia en línea (sus datos son de un solo sitio).
- **Saltos**: `bra`, `bcc`... sin tamaño eligen solos el corto o el largo; `.s`/`.b` y `.w` lo fijan.
- **Funciones de Dash y del sistema**: `jsr nombre` llama a una función de Dash del programa (o de un módulo) con
  su convención: los argumentos en la pila, de derecha a izquierda, de 4 bytes cada uno (Int, Bool, Pointer); lo
  que devuelve, en d0; el bloque quita los argumentos (`addq.l #8,sp`). La función cambia d0, d1, a0 y a1 (el
  compilador lo sabe solo) y deja como estaban d2-d7 y a2-a6. Una función también vale como dirección:
  `move.l #nombre,d0`, `lea nombre,a0`, `dc.l nombre`. Del runtime, las bases de las librerías que abre:
  `SysBase`, `DOSBase`, `GfxBase` e `IntuitionBase` (`move.l GfxBase,a6` y `jsr -270(a6)` es WaitTOF). Lo demás del
  runtime se llama con una función de Dash que lo use. A una función se llega con `jsr` (no con `bra` ni `bsr`, ni
  con `(pc)`) y sin sumarle nada.

### Funciones enteras: asm func

```ruby
asm func suma_lista(datos: [Int], n: Int) -> Int in a0 = datos, d0 = n - 1 out d1 uses d2
    moveq   #0,d1
.bucle:
    add.l   (a0)+,d1
    dbra    d0,.bucle
end
```

Una función de Dash cuyo cuerpo es un bloque asm. Se llama como cualquier otra (también desde otro bloque, con
`jsr`, y como valor: `vblank_server(al_vblank, datos)`). Sin `in`, los parámetros van en d0, d1, d2... por orden;
con `in`, cada registro con su expresión, como en un bloque. Sin `out`, lo que devuelve sale de d0; `out d1` lo
saca de d1 (solo el registro). Devuelve Int, Bool o Pointer, o nada. `uses` como en un bloque. Por dentro es

```ruby
func suma_lista(datos: [Int], n: Int) -> Int
    asm in a0 = datos, d0 = n - 1 out __dash_asm_r = d1 uses d2
        ...
    end
    return __dash_asm_r
end
```

así que vale todo lo de los bloques (y el compilador puede copiarla en línea si es corta).

### Interrupciones

`int_server_add(intb, f, datos)` pone `f(datos)` en una cadena de interrupciones de exec (AddIntServer): 5 VBlank,
4 copper, 3 CIA-A, 13 CIA-B; `vblank_server(f, datos)` es la del VBlank. Devuelve el servidor (0 si no puede);
`int_server_remove(servidor)` lo quita, y al salir del programa (también tras un error) se quitan todos. El
servidor del runtime recibe a1 = sus datos, llama a `f` como a una función de C (`datos` en la pila) y vuelve con
d0 = 0 y Z puesto: la cadena sigue (el VBlank del sistema también). `f` corre en la interrupción: lo normal es una
`asm func`; si es de Dash, solo cuentas y peek/poke (ni Print, ni textos, ni listas). Ejemplo:
`examples/asm_copper.dash` (una lista del copper en `data_c` que un servidor de VBlank en asm mueve en cada imagen).
Las del audio son manejadores (SetIntVector), no servidores: no están.

### Instrucciones

Todas las del 68000, con todos sus modos de direccionamiento (los dos estilos de Motorola: `4(a0)` y `(4,a0)`;
`8(a0,d1.w)` y `(8,a0,d1.l)`; `tabla(pc)`; `$dff180` absoluto, `4.w` corto), y los alias de siempre (`dbra`, `bhs`,
`blo`, `shs`, `slo`; `add #n` es `addi`, `add` a un `An` es `adda`, `move` a un `An` es `movea`...).

Del 68020, con `--cpu 68020` o más (o `--fpu`; por `--gcc` el aviso sale al compilar el C, con la línea del `.dash`): `muls.l`/`mulu.l` (32 y 64 bits), `divs.l`/`divu.l`/`divsl.l`/
`divul.l`, `extb.l`, los campos de bits (`bfextu d0{4:8},d1`, `bfexts`, `bfins`, `bfset`, `bfclr`, `bfchg`,
`bftst`, `bfffo`), saltos de 32 bits (`bra.l`), `link.l`, `rtd`, `chk.l`, índice con escala (`(a0,d0.l*4)`),
desplazamientos grandes en `(d,An,Xn)`, la indirección de memoria (`([bd,An,Xn],od)`, `([bd,An],Xn,od)`, también
con `pc`), `cas`, `cas2` (`cas2.l d0:d1,d2:d3,(a0):(a1)`), `cmp2`, `chk2`, `pack`, `unpk`, `trapcc` (`trapeq`,
`trapne.w #n`), `bkpt` y `movec` (sfc, dfc, cacr, usp, vbr, caar, msp, isp). Sin la opción da un error que lo dice.

De la FPU (68881/68882, la del 68040), con `--fpu`: `fmove` (con todos los formatos: `.b .w .l .s .d .x`; a y desde
`fpcr`, `fpsr` y `fpiar` con `.l`), `fmovem` (`fmovem.x fp2-fp7,-(sp)`, `fmovem.l fpcr/fpsr,-(sp)`), las
operaciones (`fadd fsub fmul fdiv fmod frem fscale fsglmul fsgldiv fcmp ftst`, y las de un operando: `fsqrt fabs
fneg fint fintrz fsin fcos ftan fasin facos fatan fsinh fcosh ftanh fetox fetoxm1 ftwotox ftentox flogn flognp1
flog10 flog2 fgetexp fgetman`, también como `fsqrt.x fp0`), `fsincos.x <ea>,fpc:fps`, `fmovecr`, `fbcc` (`fbeq`,
`fblt`...: `.w`, o `.l` si no llega), `fdbcc`, `fscc`, `ftrapcc`, `fnop`, `fsave` y `frestore`. Un inmediato de
`.s`, `.d` o `.x` es un número (`fmul.s #2.5,fp1`, `fmove.d #-2.7,fp2`; un entero vale lo que dice: `#3` es 3.0).
En el 68040 las transcendentes (`fsin`, `fetox`...) las hace 68040.library (la carga SetPatch). No están: el
formato `.p` (BCD), las listas dinámicas de `fmovem` (con Dn) y las del 68040 (`fsadd`, `fdmove`...).

No están: la MMU, `callm`, `rtm`, `moves` y lo del 68040 (`move16`).

## Los dos caminos

**Directo (`./dash`)**: dashc lee el bloque en el léxico (`asm_extract`, igual que el preprocesado de Python) y lo
cambia por llamadas internas: `__dash_asm(n, entradas...)` y, por cada salida, `var = __dash_asm_out(n, j)`. Así
el resto del compilador ve las asignaciones (registros, rangos, bucles). Al generar:

1. Reserva en la pila tantos huecos como el mayor de entradas y salidas, y deja ahí cada entrada.
2. `movem.l` guarda los registros de d2-d7/a2-a6 que el bloque toca (los de las variables de Dash y los que C
   espera intactos); con `uses fp2...`, `fmovem.x` guarda los de la FPU.
3. Carga cada entrada en su registro desde la pila, ensambla el cuerpo en el sitio (`asm68k.c`: dos o más pasadas
   hasta que los saltos y las etiquetas no cambian; reubicaciones al hunk de código para `dc.l etiqueta`,
   `lea etiqueta,a0`...), deja cada salida en su hueco, recupera los registros y cada `__dash_asm_out` saca la suya.

Las secciones de datos van a los hunks del programa: `data` al de datos, `bss` al BSS (`obj->bss`), y `data_c` y
`bss_c` a dos hunks propios que `hunk.c` escribe con MEMF_CHIP (el bit 30 del tamaño en la tabla del HUNK_HEADER). Las
reubicaciones de un long de los datos van en `obj->srelocs`; las que apuntan al código se escriben al final
(`asm_resolve`), cuando el código ya no se mueve. `jsr nombre` es un `jsr` absoluto reubicado a la etiqueta de la
función (que pasa a generarse aunque nadie más la llame); `GfxBase`, un long reubicado al símbolo `_GfxBase` del
runtime. `cnop` en el código: el bloque lleva delante nops de sobra y `resolve_fixups`, con los saltos ya en su
tamaño, quita los que hagan falta para que empiece alineado (el hunk empieza alineado a 8).

**Por C (`./dash --gcc`)**: Python lee el bloque igual (`compiler/asm68k.py`), comprueba lo mismo (instrucciones,
tamaños, número de operandos, nombres, registros) y lo pasa a un `__asm__ volatile` con variables `register ...
__asm__("d0")` para las entradas y salidas, y `uses` como registros pisados (más `"cc"` y `"memory"`). El texto
va normalizado para el `as` de binutils (que entiende la sintaxis de Motorola con registros sin `%`): números en
decimal (su `|` es un comentario y su `%` el de las plantillas de GCC), etiquetas `.L` con `%=` (únicas aunque GCC
copie la función), `dc.b "texto"` en bytes, `dc.s`/`dc.d` en longs, `even` y `cnop` como `.even` y `.balign`/
`.balignw` (con nops), `incbin` con su ruta completa. Las instrucciones del 68020 piden `--cpu 68020` y las de la
FPU `--fpu`: el C lleva un `#error` que lo dice si no. Un inmediato `.s`/`.d` va como `#0r1.5`; uno `.x`, la
instrucción entera en `.word` (gcc llama a `as` sin `-m68881` y así escribe 10 bytes, no 12).

Las secciones van con `.section .data`, `.bss`, `.datachip` y `.bsschip` (y `.text` para volver: este `as` no
tiene `.pushsection`). El `ld` de bebbo junta `.datachip` y `.bsschip` en hunks aparte, al final, pero sin
MEMF_CHIP: `compiler/cflags.py` (`fix_chip_hunks`) lo pone en el ejecutable después de enlazar. La función con
secciones lleva `noinline, noclone`. `jsr nombre` pasa la función como operando `"i"` (`%cN` escribe su símbolo):
así GCC la guarda y sabe que se llama; el bloque pierde además d0, d1, a0 y a1. `asm func` se extrae igual que en
el directo (las mismas líneas).

Para comprobar el ensamblador del directo se compararon sus bytes con los del `as` de binutils, instrucción por
instrucción (FPU, 68020 y 68000), y los de `./dash` con los de `./dash --gcc`. Difieren solo en lo que los dos hacen
bien de otra forma: `as` pone `bd` de 32 bits en `([etiqueta,pc])` hacia delante, y el campo Dh de `muls.l d0,d1`.

Las entradas se calculan antes en temporales `volatile` (el fallo de GCC 6 con `register asm` y las llamadas a
libgcc, ver AGENTS.md).

**DashOS (AArch64)**: un bloque `asm` es 68k: error claro.

## Pendiente

- Las interrupciones del audio (son manejadores, SetIntVector, y quitarlos sin romper audio.device pide cuidado).
- La MMU, `callm`/`rtm`, `moves`, `move16` y las operaciones del 68040 (`fsadd`...); el formato `.p` (BCD).
- Pasar Float o Double por registros de la FPU en `in`/`out` (ahora se pasan los bits por un registro de datos).

Hecho en la segunda parte (lo pidió el usuario, para demos): `asm func`, `jsr` a funciones de Dash y las bases de
librería, secciones (también en memoria chip), `cnop`, `dc.s`/`dc.d`, la FPU, lo demás del 68020 y los servidores de
interrupción. Pruebas: `tests/test_asm2.dash` y `tests/test_asm_fpu.dash` (y sus `_directo`), en el A1200, el A500
y el 68040.
