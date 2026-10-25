# Dash, Blitz and AMOS

**English** · [Castellano](COMPARATIVA.md)

Dash against the classic “easy” languages (AmiBlitz3 and AMOS Professional) and against C (SAS/C and GCC), with the same programs measured on the same emulated Amiga.

## Summary

- Speed: Dash is on par with C (GCC) for arithmetic and calls, and the fastest with strings and lists. AmiBlitz3 and AMOS are 10 to 40 times slower for arithmetic, calls and lists, and 1.2 to 2 times slower with strings. SAS/C wins floating point (the ROM's FFP). C wins drawing lines: Dash is 8 % behind on the A1200 and 19 % on the A500 (it draws in a window); AmiBlitz3 and AMOS up to 66 % on the A500.
- Startup and size: AmiBlitz3 and SAS/C make the smallest executables; Dash is close (4-9 KB). AMOS puts its runtime in every program: 54 KB and almost a second to start on an A1200.
- Memory: Dash uses the least while running (17 KB on average), then SAS/C (21 KB), AmiBlitz3 (30 KB) and GCC (39 KB). AMOS needs about 170 KB. With a screen, Dash and AmiBlitz3 use about 45 KB more than C (Dash draws in a window).
- Stability: Dash and AMOS stop cleanly on a division by zero; C hangs the Amiga and AmiBlitz3 goes on with a wrong result. On an index out of range only AMOS reports it; Dash ignores it without corrupting memory; AmiBlitz3 and C write outside the list.
- Features: Dash covers system windows (GadTools, MUI, ReAction), RTG, networking and TLS from the language itself. AMOS rules hardware games (AMAL, bobs, music) but ignores the OS. AmiBlitz3 reaches everything, at the cost of pointers and manual memory.

## Speed

Milliseconds for each whole program (load, start and work) in FS-UAE at real speed. Lower is better. The bar is relative to the slowest in each test.

### A1200

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Startup | 54 | **34** | 862 | 36 | 42 |
| bucle (300,000 loops of additions and a comparison) | **629** | 7,399 | 9,963 | 754 | **629** |
| llamada (100,000 calls to a two-parameter function) | **219** | 2,115 | 9,080 | 522 | 224 |
| texto (20,000 times string + number) | **2,011** | 4,001 | 3,049 | 3,591 | 6,062 |
| lista (100,000 reads and writes in a 10-element list with modulo) | **1,563** | 31,375 | 25,837 | 3,159 | 2,399 |
| flotante (20,000 floating point additions and multiplications) | 486 | 845 | 1,865 | **277** | 497 |
| lineas (2,000 lines on a 320×256, 32-color screen) | 5,009 | 5,818 | 5,694 | **4,652** | 4,654 |

### A500

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Startup | 169 | **126** | 1,489 | 134 | 148 |
| bucle (300,000 loops of additions and a comparison) | **2,850** | 30,298 | 36,385 | 3,879 | 2,861 |
| llamada (100,000 calls to a two-parameter function) | **962** | 9,803 | 33,674 | 2,698 | 987 |
| texto (20,000 times string + number) | **8,714** | 13,862 | 10,306 | 15,421 | 29,780 |
| lista (100,000 reads and writes in a 10-element list with modulo) | **7,527** | 106,401 | 78,128 | 13,437 | 16,586 |
| flotante (20,000 floating point additions and multiplications) | 2,385 | 3,375 | 5,355 | **1,243** | 2,027 |
| lineas (2,000 lines on a 320×256, 32-color screen) | 6,851 | 9,549 | 9,222 | 5,826 | **5,744** |

## Memory and size

Executable size and memory used while running (the largest drop of free memory while it runs, minus the 64 KB stack of the process).

| | Dash | AmiBlitz3 | AMOS Pro | SAS/C 6.59 | GCC 6.5 |
|---|---:|---:|---:|---:|---:|
| Empty executable | 4,336 B | 476 B | 54,160 B | 1,424 B | 3,352 B |
| Typical executable | 5,905 B | 9,100 B | 55,593 B | 8,610 B | 11,738 B |
| Memory while running (mean) (A1200) | 16,566 B | 30,265 B | 169,156 B | 20,932 B | 38,502 B |
| With a screen (lines) (A1200) | 113,272 B | 118,208 B | 187,888 B | 67,952 B | 68,264 B |

## Stability

What happens on two typical bugs, on an emulated A1200 with OS 3.1. Each test in its own boot.

|  | Division by zero | Index out of range |
|---|---|---|
| Dash | Error message and clean exit (code 20); the Amiga goes on | Reads 0 and does not write; goes on silently |
| AmiBlitz3 | Gives 2147483647 and goes on silently | Writes outside the list and goes on |
| AMOS Pro | Stops with an error (code 20); the Amiga goes on | Stops with an error (code 20); the Amiga goes on |
| SAS/C 6.59 | The Amiga hangs | Writes outside the list and goes on |
| GCC 6.5 | The Amiga hangs | Writes outside the list and goes on |

## What each one covers

From each one's documentation and what Coffin OS R65 ships; not all of it is measured.

|  | Dash | AmiBlitz3 | AMOS Pro | SAS/C | GCC (C) | VBCC | Assembler |
|---|---|---|---|---|---|---|---|
| Status | In development (2026) | Open source, 3.11 (2026) | Open source since 2019; last release 1993 | Commercial, discontinued 1995 | bebbo 6.5, in development | 0.9h (2022) | ASM-One, DevPac |
| How it works | Translates to C, compiled with GCC on the PC | Compiler on the Amiga | Interpreter with IDE + compiler | Compiler on the Amiga | Cross compiler on the PC | On the Amiga or the PC | Assembler |
| CPU | 68000; --cpu 020-060 | 68000 (IDE: 020) | 68000; AGA unofficial | 68000-060 | 68000-060 | 68000-060 | Any |
| Structures | structs, lists, dictionaries | NEWTYPE, linked lists, pointers | No (arrays only) | structs, pointers | structs, pointers | structs, pointers | By hand |
| Memory | Automatic (reference counting) | Strings automatic; the rest by hand | Automatic | By hand | By hand | By hand | By hand |
| Numbers | Int, Float, Fixed 16.16 | Long, Quick 16.16, FFP Float | Integer, Float (double optional) | All of C's | All of C's | All of C's | By hand |
| System windows | Intuition, GadTools, MUI, ReAction | Intuition, GadTools (includes) | No: its own screens | Through OS libraries | Through OS libraries | Through OS libraries | Through OS libraries |
| Graphics cards (RTG) | Yes (P96, CGX) | With includes | No | With libraries | With libraries | With libraries | With libraries |
| Hardware (copper, sprites, blitter) | Yes | Yes (Blitz mode) | Yes, plus AMAL for animation | By hand | By hand | By hand | Yes |
| Networking and TLS | bsdsocket and AmiSSL | bsdsocket and http (includes) | No | With libraries | With libraries | With libraries | By hand |
| Runtime errors | Message and clean exit, no Guru | With the debugger; without it, no | Error message | Guru | Guru | Guru | Guru |
| Where you write it | VS Code on the PC (and emulator) | Its own IDE on the Amiga | Its own IDE on the Amiga | Amiga | PC | Amiga or PC | Amiga |

## How it was measured

- Machines: FS-UAE at real (cycle-exact) speed, Kickstart 3.1. A1200: 68020 at 14 MHz with 8 MB fast RAM. A500: 68000 at 7 MHz.
- Compilers: Dash 528c3cc (default, -O2); AmiBlitz3 3.11.4 with -r; AMOS Professional Compiler 2.0 (TYPE=1 INCLIB); SAS/C 6.59 with OPTIMIZE and MATH=FFP; bebbo's GCC 6.5 with -O2 and libnix. The ones in Coffin OS R65, copied from its image mounted read only (AMOS lacked AMOSPro_Compiler_Config and AMOSPro_Interpreter_Config: taken from the official AMOS Pro repository).
- Measuring: a C program runs each executable, times it with the EClock and samples AvailMem every 1/50 s for the memory peak. One run per program (the emulator is deterministic).
- Same algorithm everywhere. In C, “texto” is sprintf into a fixed buffer (C has no dynamic strings). AmiBlitz3 with DEFTYPE .l and default options: not tuned.
- Not measured yet: VBCC (Coffin's lacks the AmigaOS target), ADE's GCC 2.95 and assembler.
- The lines test found a Dash bug: on a 68000, opening its own screen gave a Guru (SA_Pens). Fixed in PR #55; Dash's A500 lines figure is with the fix.

Each language's programs, the timer (timeit.c), the data and this generator are in tools/comparativa.
