# Dash para DashOS: AArch64 big-endian (plan y bitácora)

DashOS (`~/Projects/dashos`, su `PLAN.md`, "Dash en los dos sistemas") necesita que el mismo programa Dash compile
para AmigaOS 3.x (hunks de 68k) y para DashOS (ELF de AArch64 big-endian). Rama `aarch64`, worktree
`.worktrees/aarch64`.

## Decisiones (usuario, 2026-11-03)

- **Capa común y un generador por procesador.** `dashc/src/gen68k.c` se parte en el recorrido del programa, que
  decide qué hacer, y el generador de 68k, que escribe las instrucciones. El de AArch64 es otro generador detrás de
  la misma interfaz. Cada cambio del lenguaje se hace una vez.
- **Punteros de 32 bits solo en las estructuras de Amiga.** Los programas nativos usan punteros de 64 bits. Las
  estructuras que comparte la caja Amiga se marcan y guardan sus punteros en 32 bits; el código los convierte al
  leerlos y escribirlos. En 68k la marca no cambia nada.
- **Runtime sin sistema debajo.** El runtime pide la memoria y escribe la salida a través de unas pocas funciones
  de plataforma, que pone quien lo aloja (DashOS, o el arnés de pruebas).
- **El camino de 68k no se toca.** Cada paso del reparto deja los ejecutables de 68k idénticos byte a byte
  (`dashc/tests/identicos.py`) y el C de `./dash --gcc` idéntico.

## Herramientas

- `clang --target=aarch64_be-none-elf` y `ld.lld` (clang 23 del sistema): compilan el runtime en C para ARM.
- `qemu-aarch64_be` (modo usuario): ejecuta en el PC los programas de prueba. Para eso hay una plataforma de
  pruebas que habla con Linux (write, exit, mmap). DashOS pondrá la suya.
- `dashc/tests/identicos.py`: 2310 compilaciones de 68k (tests, ejemplos, 6 juegos de opciones) contra un dashc de
  referencia, en un segundo. `--guardar` fija la referencia.

## Fases

| Fase | Qué | Cómo se prueba |
|---|---|---|
| A0 | Red de seguridad: `identicos.py` | 2310/2310 idénticos con la referencia de `origin/main` |
| A1 | Capa de plataforma en el runtime (memoria, salida, salida del programa, errores) | C de Amiga idéntico; el runtime compila para ARM sin sistema |
| A2 | `./dash --gcc --dashos`: por C con clang, a ELF de AArch64 big-endian | Tests con `# expect-out` en `qemu-aarch64_be`, misma salida que en el A1200 |
| A3 | Reparto de `gen68k.c`: recorrido común + interfaz de objetivo + generador de 68k | `identicos.py` tras cada paso; `make -C dashc test` al final |
| A4 | Codificador de AArch64 y escritor de ELF (enlaza el runtime, un `.o` ELF) | Enteros, funciones, control y `Print`, contra A2 |
| A5 | Cobertura en ARM: textos, listas, structs, diccionarios, Float y Double (FPU de ARM) | Los tests de A2 por el camino directo, misma salida |
| A6 | Structs de Amiga con punteros de 32 bits, en los dos caminos | Tests en ARM; en 68k, ejecutables idénticos |
| A7 | Builtins de DashOS | Cuando DashOS tenga su API (S11). Fuera de este bucle |

Con A2 hecho, el camino por C es el oráculo del directo, como hoy `./dash --gcc` lo es del directo de 68k.

## Preguntas abiertas

- Nombre de la opción: `--dashos` (propuesta).
- Marca de las estructuras de Amiga: `@amiga struct X` (propuesta). Va en la gramática de los dos caminos.

## Bitácora

- 2026-11-03: plan. A0 hecha: `dashc/tests/identicos.py`, 2310/2310 idénticos. dashc compila 277 de 385 programas
  del corpus (tests, ejemplos y los suyos); el resto da error en los dos y también se compara.
