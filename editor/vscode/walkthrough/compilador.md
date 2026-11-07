# El compilador Dash

La extensión usa el compilador de Dash (el repositorio, con `./dash` y `compiler/`) para compilar, ejecutar en el
emulador y depurar. Si tus programas están dentro de ese repositorio, lo encuentra sola; si no, dile dónde está.

El compilador se construye una vez con `make -C dashc` en la carpeta de Dash (y otra vez tras cada `git pull`). Para
el emulador hacen falta FS-UAE y una ROM de Kickstart (ajustes `dash.emulator.*`). La toolchain del Amiga
(`m68k-amigaos-gcc` en `/opt/amiga`) solo hace falta para programas con C, `./dash --gcc` y depurar con gdb.

Para las ventanas MUI: el SDK de MUI (`tools/get_mui_sdk.sh` del repositorio) y unos ficheros de Workbench con MUI
para el emulador (`tools/emu_sys_mui.sh`, ajuste `dash.emulator.muiSystem`).
