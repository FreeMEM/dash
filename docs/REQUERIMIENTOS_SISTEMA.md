# Requisitos del Sistema para Dash
Versión: 3.0 (al día el 2026-10-24)

Este documento especifica los requisitos de software y hardware para el desarrollo con Dash y para la ejecución
de los binarios generados. Cómo instalarlo todo: `INSTALACION.md`.

> Cambios desde los requisitos originales (versión 2.0): los programas piden AmigaOS 3.0 o superior (no 2.0);
> no hay versión PPC ni `ppc-amigaos-gcc` (los programas son de 68k); el gcc de bebbo genera Hunk
> directamente y ya no hace falta `elf2hunk`; los módulos suenan con una rutina propia, sin `ptplay.library`.

## 1. Requisitos del Entorno de Desarrollo (Host)

Estos son los requisitos para la máquina donde se escribe y compila el código de Dash.

-   **Sistema Operativo:**
    -   Linux. Es donde se desarrolla y se prueba (CachyOS/Arch; las órdenes de Ubuntu/Debian y Fedora están
        en `INSTALACION.md`).
    -   macOS y Windows con WSL2: `INSTALACION.md` da los pasos del toolchain, pero Dash no se prueba ahí.

-   **Software:**
    -   **Python:** 3.10 o superior, con la librería `lark` (`pip install lark --break-system-packages`).
    -   **Compilador cruzado:** `m68k-amigaos-gcc` 6.5.0b de bebbo
        ([BlitterStudio/m68k-amigaos-gcc](https://github.com/BlitterStudio/m68k-amigaos-gcc), rama `amiga6`),
        en `/opt/amiga` (otra carpeta: `DASH_TOOLCHAIN`), con las cabeceras de CyberGraphX (`make sdk=cgx`).
        Dash solo se prueba con esa versión.
    -   **Para MUI:** el SDK de MUI 5, que baja `tools/get_mui_sdk.sh` (no va en el repositorio por su licencia).
    -   **Para TLS:** el SDK de AmiSSL, que baja `tools/get_amissl.sh`.
    -   **Opcional:**
        -   FS-UAE (o Amiberry) y una ROM de Kickstart 3.1, para ejecutar los programas y los tests en un Amiga
            emulado (`tools/emu_run.py`, `tests/run_tests.py --emu`); sin ROM se usa la AROS de FS-UAE.
        -   VS Code 1.86 o posterior, para la extensión de Dash (`editor/vscode`); el depurador usa
            `m68k-amigaos-gdb` (lo instala el toolchain) y `bgdbserver` (`tools/get_bgdbserver.sh`).
        -   `curl` y `lhasa` para los scripts que bajan SDKs, y amitools (`xdftool`) para sacar los ficheros de un
            Workbench de un disco duro (`tools/emu_sys_from_hdf.sh`).

## 2. Requisitos de la Plataforma de Destino (Target)

Estos son los requisitos para la máquina (real o emulada) donde se ejecutan los programas creados con Dash.

-   **Hardware:**
    -   Un Commodore Amiga (OCS, ECS o AGA) o un emulador (FS-UAE, WinUAE, Amiberry...).
    -   **CPU:** 68000 o superior. Piden un 68020 o superior: MUI (`mui_*`), TLS (`tls_*`) y los programas
        compilados con `./dash --fpu` (además, FPU 68881/68882).
    -   **Tarjeta gráfica:** opcional. Las funciones `rtg_*` piden CyberGraphX o Picasso96; el dibujo normal, las
        imágenes y el fondo del Workbench funcionan también en pantallas RTG.
    -   **Memoria:** depende del programa. Cada programa pide 16 KB de pila (32 KB con MUI, 64 KB con TLS).

-   **Sistema Operativo:**
    -   **AmigaOS 3.0 (Kickstart V39)** o superior: el runtime usa los pools de memoria de exec. Se prueba en
        AmigaOS 3.1 (A500 y A1200) y 3.2 (A1200 y un 68040 con tarjeta gráfica), emulados.
    -   **MUI:** MUI 3.8 (muimaster.library V19) o MUI 5.
    -   **ReAction** (`ra_*`): las clases de ReAction de AmigaOS 3.2.
    -   **Red** (`net_*`): una pila TCP/IP con `bsdsocket.library` (Roadshow, AmiTCP, MiamiDx...).
    -   **TLS** (`tls_*`): además, AmiSSL 5.1 o posterior.
    -   **Interfaces de red y WiFi** (`net_ifs_read`, `wifi_read`): Roadshow. Los drivers SANA-II
        (`net_drivers_read`, `net_driver_read`, `wifi_read_device`) valen con cualquier pila.
    -   **USB** (`usb_hid_*`): Poseidon.
    -   **Imágenes** (`image_load`): ILBM siempre (su datatype viene con el sistema); PNG, JPEG, GIF y BMP, si
        están sus datatypes (AmigaOS 3.2 los trae).
    -   **Catálogos de idioma** (`@catalog`, `tr`) y `date_text`: `locale.library`, que trae el sistema.
    -   **Commodities** (`cx_*`): `commodities.library`, que trae el sistema.
