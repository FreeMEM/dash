# Dash, Blitz y AMOS

[English](COMPARATIVA.en.md) · **Castellano**

Dash frente a los lenguajes «fáciles» de siempre (AmiBlitz3 y AMOS Professional) y frente a C (SAS/C y GCC), con los mismos programas medidos en el mismo Amiga emulado.

## En resumen

- Velocidad: Dash va a la par que C con GCC en cálculo y llamadas, y es el más rápido con textos y listas. AmiBlitz3 y AMOS van de 10 a 40 veces más despacio en cálculo, llamadas y listas, y de 1,2 a 2 veces con textos. En coma flotante gana SAS/C (FFP de la ROM). En líneas gana C: Dash va un 8 % detrás en el A1200 y un 19 % en el A500 (dibuja en una ventana); AmiBlitz3 y AMOS, hasta un 66 % en el A500.
- Arranque y tamaño: AmiBlitz3 y SAS/C hacen los ejecutables más pequeños; Dash queda cerca (4-9 KB). AMOS mete su runtime en cada programa: 54 KB y casi un segundo para arrancar en un A1200.
- Memoria: Dash es el que menos ocupa al ejecutarse (17 KB de media), seguido de SAS/C (21 KB), AmiBlitz3 (30 KB) y GCC (39 KB). AMOS necesita unos 170 KB. Con pantalla, Dash y AmiBlitz3 gastan unos 45 KB más que C (Dash dibuja en una ventana).
- Estabilidad: Dash y AMOS paran limpiamente ante una división por cero; C se cuelga y AmiBlitz3 sigue con un resultado falso. Ante un índice fuera de rango, solo AMOS avisa; Dash lo ignora sin corromper memoria; AmiBlitz3 y C escriben fuera de la lista.
- Capacidades: Dash cubre ventanas del sistema (GadTools, MUI, ReAction), RTG, red y TLS desde el propio lenguaje. AMOS manda en juegos con el hardware (AMAL, bobs, música) pero ignora el sistema. AmiBlitz3 llega a todo, a cambio de punteros y memoria a mano.

## Velocidad

Milisegundos de cada programa completo (carga, arranque y trabajo) en FS-UAE a velocidad real. Menos es mejor. La barra es relativa al más lento de cada prueba.

### A1200

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Arranque | 54 | **34** | 862 | 36 | 42 |
| bucle (300.000 vueltas de sumas y una comparación) | **629** | 7.399 | 9.963 | 754 | **629** |
| llamada (100.000 llamadas a una función de dos parámetros) | **219** | 2.115 | 9.080 | 522 | 224 |
| texto (20.000 veces texto + número) | **2.011** | 4.001 | 3.049 | 3.591 | 6.062 |
| lista (100.000 lecturas y escrituras en una lista de 10 con módulo) | **1.563** | 31.375 | 25.837 | 3.159 | 2.399 |
| flotante (20.000 sumas y multiplicaciones de coma flotante) | 486 | 845 | 1.865 | **277** | 497 |
| lineas (2.000 líneas en una pantalla de 320×256 y 32 colores) | 5.009 | 5.818 | 5.694 | **4.652** | 4.654 |

### A500

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Arranque | 169 | **126** | 1.489 | 134 | 148 |
| bucle (300.000 vueltas de sumas y una comparación) | **2.850** | 30.298 | 36.385 | 3.879 | 2.861 |
| llamada (100.000 llamadas a una función de dos parámetros) | **962** | 9.803 | 33.674 | 2.698 | 987 |
| texto (20.000 veces texto + número) | **8.714** | 13.862 | 10.306 | 15.421 | 29.780 |
| lista (100.000 lecturas y escrituras en una lista de 10 con módulo) | **7.527** | 106.401 | 78.128 | 13.437 | 16.586 |
| flotante (20.000 sumas y multiplicaciones de coma flotante) | 2.385 | 3.375 | 5.355 | **1.243** | 2.027 |
| lineas (2.000 líneas en una pantalla de 320×256 y 32 colores) | 6.851 | 9.549 | 9.222 | 5.826 | **5.744** |

## Memoria y tamaño

Tamaño del ejecutable y memoria que ocupa al ejecutarse (el mayor descenso de memoria libre mientras corre, sin los 64 KB de pila del proceso).

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Ejecutable vacío | 4.336 B | 476 B | 54.160 B | 1.424 B | 3.352 B |
| Ejecutable medio | 5.905 B | 9.100 B | 55.593 B | 8.610 B | 11.738 B |
| Memoria al ejecutar (media) (A1200) | 16.566 B | 30.265 B | 169.156 B | 20.932 B | 38.502 B |
| Con pantalla (líneas) (A1200) | 113.272 B | 118.208 B | 187.888 B | 67.952 B | 68.264 B |

## Por qué salen así

**Dash y GCC.** Dash no compila mejor que GCC: genera C y lo compila el mismo GCC, y donde hacen lo mismo empatan (bucle y llamadas). Gana donde usa su runtime en lugar de la librería C. Para pasar un número a texto saca dos cifras por división, en vez del sprintf genérico de libnix, que va leyendo el formato. Para el resto (%) usa la división de 16 bits del 68000 cuando los números caben, en vez de la rutina de 32 bits de libgcc. Y escribe con Printf de dos.library, sin los búferes del printf de C: por eso gasta menos memoria. Un programador de C podría hacer lo mismo a mano; la prueba mide lo que sale escribiendo lo normal en cada lenguaje.

**SAS/C.** Un compilador de 1995 que optimiza menos que GCC 6. GCC mete la función dentro del bucle y SAS/C la llama de verdad: las llamadas cuestan más del doble (522 ms frente a 224), y el bucle, un 20 % más. Gana en coma flotante porque con MATH=FFP usa el formato rápido de Motorola de la ROM (mathffp.library), con menos precisión que el IEEE de los demás. Su sprintf es más rápido que el de libnix y sus ejecutables son pequeños.

**AmiBlitz3.** Hace los ejecutables más pequeños (476 bytes uno vacío), porque solo enlaza las rutinas que usas, y es el que antes arranca. Con enteros va de 6 a 13 veces más despacio que C (con GCC). Está compilado con -r, que según su ayuda optimiza el tamaño, y con el resto de opciones por defecto: sin afinar y sin mirar el código que genera. Sin su depurador no comprueba nada: dividir por cero da 2147483647 y un índice fuera de rango escribe en otra memoria.

**AMOS Pro.** Su compilador copia en cada ejecutable las rutinas de su librería y sus datos de sistema (lo dice al compilar). Por eso un programa vacío ocupa 54 KB, tarda casi un segundo en arrancar mientras monta su propio sistema de pantallas, y usa unos 165 KB. Lo más lento son los procedimientos: de 34 a 41 veces más que C. A cambio, comprueba los errores igual que su intérprete: ante una división por cero o un índice fuera de rango, para con un error.

## Estabilidad

Qué pasa ante dos fallos típicos, en un A1200 emulado con OS 3.1. Cada prueba en un arranque propio.

|  | División por cero | Índice fuera de rango |
|---|---|---|
| Dash | Mensaje de error y salida limpia (código 20); el Amiga sigue | Lee 0 y no escribe; sigue sin avisar |
| AmiBlitz3 | Da 2147483647 y sigue sin avisar | Escribe fuera de la lista y sigue |
| AMOS Pro | Para con error (código 20); el Amiga sigue | Para con error (código 20); el Amiga sigue |
| SAS/C 6.59 | El Amiga se cuelga | Escribe fuera de la lista y sigue |
| GCC 6.5 | El Amiga se cuelga | Escribe fuera de la lista y sigue |

## Qué cubre cada uno

Según la documentación de cada uno y lo que trae Coffin OS R65; no está todo medido.

|  | Dash | AmiBlitz3 | AMOS Pro | SAS/C | GCC (C) | VBCC | Ensamblador |
|---|---|---|---|---|---|---|---|
| Estado | En desarrollo (2026) | Código abierto, 3.11 (2026) | Código abierto desde 2019; última versión 1993 | Comercial, cerrado en 1995 | bebbo 6.5, en desarrollo | 0.9h (2022) | ASM-One, DevPac |
| Cómo funciona | Pasa a C y compila con GCC en el PC | Compilador en el Amiga | Intérprete con IDE + compilador | Compilador en el Amiga | Compilador cruzado en el PC | En el Amiga o en el PC | Ensamblador |
| CPU | 68000; --cpu 020-060 | 68000 (IDE: 020) | 68000; AGA no oficial | 68000-060 | 68000-060 | 68000-060 | Cualquiera |
| Estructuras | struct, listas, diccionarios | NEWTYPE, listas enlazadas, punteros | No (solo arrays) | struct, punteros | struct, punteros | struct, punteros | A mano |
| Memoria | Automática (conteo de referencias) | Textos automáticos; el resto a mano | Automática | A mano | A mano | A mano | A mano |
| Números | Int, Float, Fixed 16.16 | Long, Quick 16.16, Float FFP | Entero, Float (doble opcional) | Todos los de C | Todos los de C | Todos los de C | A mano |
| Ventanas del sistema | Intuition, GadTools, MUI, ReAction | Intuition, GadTools (includes) | No: pantallas propias | Con las librerías del SO | Con las librerías del SO | Con las librerías del SO | Con las librerías del SO |
| Tarjeta gráfica (RTG) | Sí (P96, CGX) | Con includes | No | Con librerías | Con librerías | Con librerías | Con librerías |
| Hardware (copper, sprites, blitter) | Sí | Sí (modo Blitz) | Sí, y AMAL para animar | A mano | A mano | A mano | Sí |
| Red y TLS | bsdsocket y AmiSSL | bsdsocket y http (includes) | No | Con librerías | Con librerías | Con librerías | A mano |
| Errores en ejecución | Mensaje y salida limpia, sin Guru | Con el depurador; sin él, no | Mensaje de error | Guru | Guru | Guru | Guru |
| Dónde se programa | VS Code en el PC (y emulador) | IDE propio en el Amiga | IDE propio en el Amiga | Amiga | PC | Amiga o PC | Amiga |

## Cómo se midió

- Máquinas: FS-UAE a velocidad real (ciclo a ciclo), Kickstart 3.1. A1200: 68020 a 14 MHz con 8 MB de fast RAM. A500: 68000 a 7 MHz.
- Compiladores: Dash 528c3cc (por defecto, -O2); AmiBlitz3 3.11.4 con -r; AMOS Professional Compiler 2.0 (TYPE=1 INCLIB); SAS/C 6.59 con OPTIMIZE y MATH=FFP; GCC 6.5 de bebbo con -O2 y libnix. Los de Coffin OS R65, copiados de la imagen en modo solo lectura (a AMOS le faltaban AMOSPro_Compiler_Config y AMOSPro_Interpreter_Config: los del repositorio oficial de AMOS Pro).
- Medida: un programa en C lanza cada ejecutable y toma el tiempo con el EClock y el pico de memoria muestreando AvailMem cada 1/50 s. Una pasada por programa (el emulador es determinista).
- Mismo algoritmo en todos. En C, «texto» es sprintf en un búfer fijo (C no tiene textos dinámicos). AmiBlitz3 con DEFTYPE .l y opciones por defecto: no lo he afinado.
- Sin medir todavía: VBCC (el de Coffin no trae instalado el target de AmigaOS), el GCC 2.95 de ADE y el ensamblador.
- La prueba de líneas destapó un fallo de Dash: en un 68000, abrir una pantalla propia daba un Guru (SA_Pens). Arreglado en el PR #55; la cifra de Dash en líneas del A500 es con el arreglo.

Los programas de cada lenguaje, el medidor (timeit.c), los datos y este generador están en tools/comparativa.
