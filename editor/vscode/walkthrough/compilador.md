# El compilador Dash

La extensión usa el compilador de Dash (el repositorio, con `./dash` y `compiler/`) para compilar, ejecutar en el
emulador y depurar. Si tus programas están dentro de ese repositorio, lo encuentra sola; si no, dile dónde está.

Hace falta también la toolchain del Amiga (`m68k-amigaos-gcc` en `/opt/amiga`) y, para el emulador, FS-UAE y una
ROM de Kickstart (ajustes `dash.emulator.*`).

Para las ventanas MUI: el SDK de MUI (`tools/get_mui_sdk.sh` del repositorio) y unos ficheros de Workbench con MUI
para el emulador (`tools/emu_sys_mui.sh`, ajuste `dash.emulator.muiSystem`).
