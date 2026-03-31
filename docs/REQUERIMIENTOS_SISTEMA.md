# Requisitos del Sistema para Dash
Versión: 2.0

Este documento especifica los requisitos de software y hardware para el desarrollo con Dash y para la ejecución de los binarios generados.

## 1. Requisitos del Entorno de Desarrollo (Host)

Estos son los requisitos para la máquina donde se escribirá y compilará el código de Dash.

-   **Sistema Operativo:**
    -   Linux (Recomendado)
    -   macOS
    -   Windows (con WSL - Windows Subsystem for Linux)

-   **Software:**
    -   **Python:** Versión 3.10 o superior.
    -   **Librería `lark`:** Necesaria para el parser del lenguaje. Se puede instalar vía `pip install lark --break-system-packages`.
    -   **Cadena de Herramientas de Compilación Cruzada (Cross-Compiler):**
        -   Para `m68k` (Amiga Clásico): `m68k-amigaos-gcc` de [BlitterStudio](https://github.com/BlitterStudio/m68k-amigaos-gcc). Este toolchain se instalará por defecto en `/opt/amiga`.
        -   Para `PPC` (AmigaOS 4): `ppc-amigaos-gcc` (instalado con el mismo toolchain si se configura).
    -   **Utilidad `elf2hunk`:** Necesaria para convertir los ejecutables ELF generados por `m68k-amigaos-gcc` al formato Hunk compatible con AmigaOS. Puede obtenerse de la extensión de VS Code `bartmanabyss.amiga-debug`.

## 2. Requisitos de la Plataforma de Destino (Target)

Estos son los requisitos para la máquina (real o emulada) donde se ejecutarán los programas creados con Dash.

-   **Hardware:**
    -   Un ordenador Commodore Amiga o un emulador compatible (FS-UAE, WinUAE, etc.).
    -   **Arquitectura:**
        -   Motorola 68000 (m68k) para Amiga clásico (OCS, ECS, AGA).
        -   PowerPC (PPC) para AmigaOS 4.x y sistemas compatibles.
    -   **Memoria:** La cantidad de memoria RAM necesaria dependerá de la complejidad de la aplicación. Dash está diseñado para ser eficiente y generar binarios pequeños.

-   **Sistema Operativo:**
    -   **AmigaOS 2.0 (v37)** o superior, debido al uso de funciones modernas como `OpenWindowTags`.
    -   Para el soporte de redes, se requiere una pila TCP/IP instalada (ej. AmiTCP, Genesis, Roadshow).
    -   Para la reproducción de módulos, puede ser necesaria la `ptplay.library`.
