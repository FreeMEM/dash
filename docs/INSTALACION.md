# Guía de Instalación de Dash

*[English](INSTALACION.en.md) | Castellano*
Versión: 2.1 (al día el 2026-10-24)

Este documento describe cómo configurar un entorno de desarrollo completo para programar en Dash, desde cero.

## Requisitos del Sistema Host

- **Sistema Operativo:** Linux (Ubuntu/Debian recomendado), macOS, o Windows con WSL2
- **RAM:** Mínimo 8GB (16GB+ recomendado para compilar el toolchain)
- **Disco:** Mínimo 10GB libres para el toolchain
- **CPU:** Multi-core recomendado (la compilación usa todos los núcleos)

## Requisitos del Amiga

Lo que necesitan los programas hechos con Dash, en un Amiga real o emulado:

- **AmigaOS 3.0 o superior** (Kickstart V39: los pools de memoria de exec).
- **68000 o superior.** Con `./dash --fpu`, un 68020 con FPU 68881/68882.
- **MUI** (`mui_*`): MUI 3.8 (muimaster.library V19) o MUI 5, y un 68020 o superior.
- **Red** (`net_*`): una pila TCP/IP (`bsdsocket.library`: Roadshow, AmiTCP, Miami...).
- **HTTPS** (`tls_*`): además, AmiSSL 5.1 o posterior, que pide un 68020 o superior.
- **ReAction** (`ra_*`): las clases de ReAction de AmigaOS 3.2.
- **Interfaces de red y WiFi** (`net_ifs_read`, `wifi_read`): Roadshow. **USB** (`usb_hid_*`): Poseidon.

La lista completa está en `REQUERIMIENTOS_SISTEMA.md`.

## Paso 1: Instalar Python y Dependencias de Dash

Dash utiliza un transpilador escrito en Python. Se requiere Python 3.10 o superior.

```bash
# Verificar versión de Python
python3 --version

# Instalar la librería lark (parser)
pip install lark --break-system-packages
```

## Paso 2: Instalar Dependencias del Cross-Compiler

El toolchain de compilación cruzada requiere varias herramientas de desarrollo:

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-dev \
    make \
    wget \
    curl \
    openssl \
    git \
    gcc \
    g++ \
    lhasa \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    flex \
    bison \
    gettext \
    texinfo \
    ncurses-dev \
    autoconf \
    rsync \
    libreadline-dev
```

### Fedora/RHEL

```bash
sudo dnf install -y \
    make \
    wget \
    curl \
    openssl \
    lhasa \
    git \
    gcc \
    gcc-c++ \
    python \
    python3-pip \
    python3-devel \
    perl-Pod-Simple \
    gperf \
    patch \
    automake \
    makedepend \
    gmp-devel \
    mpfr-devel \
    libmpc-devel \
    flex \
    bison \
    gettext-devel \
    texinfo \
    ncurses-devel \
    autoconf \
    rsync \
    readline-devel \
    which
```

### Arch Linux

```bash
sudo pacman -S --needed \
    python-pip \
    make \
    wget \
    curl \
    openssl \
    git \
    gcc \
    lhasa \
    gmp \
    mpfr \
    libmpc \
    flex \
    bison \
    gettext \
    texinfo \
    ncurses \
    autoconf \
    rsync \
    readline
```

`curl` y `lhasa` los usan los scripts que bajan el SDK de MUI, AmiSSL y bgdbserver (`tools/get_*.sh`); `openssl`,
`tools/emu_sys_amissl.sh`. Las cabeceras de Python (`python3-dev`, `python3-devel`) son para el GDB del toolchain,
que el depurador de la extensión necesita con Python.

### macOS

```bash
# Instalar Homebrew primero: https://brew.sh/
brew install bash wget make lhasa gmp mpfr libmpc flex gettext gnu-sed texinfo gcc@12 autoconf bison
```

## Paso 3: Compilar el Cross-Compiler (m68k-amigaos-gcc)

Este es el paso más importante y el que más tiempo requiere. Usamos el fork mantenido por BlitterStudio, que es el estándar de facto para desarrollo moderno en Amiga.

### 3.1 Clonar el repositorio

```bash
cd ~
git clone https://github.com/BlitterStudio/m68k-amigaos-gcc.git
cd m68k-amigaos-gcc
```

### 3.2 Descargar submódulos y dependencias

```bash
make update
```

Este comando descarga GCC, Binutils, libnix, NDK y todas las dependencias necesarias.

### 3.3 Crear directorio de instalación

Por defecto el toolchain se instala en `/opt/amiga`. Crea el directorio con permisos de escritura:

```bash
sudo mkdir -p /opt/amiga
sudo chown $USER /opt/amiga
```

### 3.4 Compilar e instalar

La compilación puede tardar entre 30 minutos y 2 horas dependiendo de tu hardware.

```bash
# Compilar usando todos los núcleos disponibles
make all -j$(nproc)

# Cabeceras de CyberGraphX (las funciones rtg_* las necesitan)
make sdk=cgx
```

`make all` instala también `m68k-amigaos-gdb`, el depurador que usa la extensión de VS Code.

**Nota:** En macOS, usa el bash de Homebrew:

```bash
make all -j$(nproc) SHELL=$(brew --prefix)/bin/bash
```

**Nota:** Si prefieres instalar en otro directorio:

```bash
make all PREFIX=~/amiga-toolchain -j$(nproc)
make sdk=cgx PREFIX=~/amiga-toolchain
export DASH_TOOLCHAIN=~/amiga-toolchain     # dónde lo busca ./dash (por defecto, /opt/amiga)
```

`DASH_TOOLCHAIN` solo lo lee `./dash`. Los tests (`tests/run_tests.py`), la captura de pantalla del emulador
(`tools/amiga/shot.c`, que compila `tools/emu_run.py`) y `tools/get_amissl.sh` (su `lha`; o `LHA=...`) usan
`/opt/amiga` fijo. Si el toolchain está en otro sitio, un enlace lo arregla: `sudo ln -s ~/amiga-toolchain /opt/amiga`.

### 3.5 Verificar la instalación

```bash
/opt/amiga/bin/m68k-amigaos-gcc --version
```

Deberías ver algo como:

```
m68k-amigaos-gcc (GCC) 6.5.0b
Copyright (C) 2017 Free Software Foundation, Inc.
```

### 3.6 Añadir al PATH (opcional pero recomendado)

Para no tener que escribir la ruta completa cada vez:

```bash
# Añadir al final de ~/.bashrc (o ~/.zshrc en macOS)
echo 'export PATH="/opt/amiga/bin:$PATH"' >> ~/.bashrc

# Recargar la configuración
source ~/.bashrc

# Verificar
m68k-amigaos-gcc --version
```

### 3.7 Ramas de GCC disponibles

El repositorio ofrece varias versiones de GCC:

| Rama | Versión GCC | Características |
|------|-------------|-----------------|
| `amiga6` | 6.5.0b | Por defecto; la que usa Dash |
| `amiga10.4` | 10.4.0 | Soporta parámetros en registros |
| `amiga13.4` | 13.4.0 | Soporta parámetros en registros |
| `amiga15.2` | 15.2.0 | Soporta parámetros en registros |
| `amiga16.2` | 16.2.0 | La de desarrollo del toolchain |

(Lista del README del toolchain en agosto de 2026; puede cambiar.)

Dash se prueba con `amiga6` (GCC 6.5.0b); con otra rama, sin probar. Para usar una versión diferente (hazlo antes de compilar):

```bash
make branch branch=amiga13.4 mod=gcc
make all -j$(nproc)
```

## Paso 4: elf2hunk (normalmente no hace falta)

El cross-compiler de bebbo (`m68k-amigaos-gcc`, el de esta guía) ya genera ejecutables en formato Hunk, el que
usa AmigaOS, y `./dash` los deja tal cual. `elf2hunk` solo hace falta con un GCC que genere ELF; si `./dash`
encuentra un ELF y tiene `elf2hunk`, lo convierte.

### Opción A: Desde la extensión de VS Code (más fácil)

Si usas VS Code, instala la extensión `bartmanabyss.amiga-debug`. El binario estará en:

```
~/.vscode/extensions/bartmanabyss.amiga-debug-*/bin/linux/elf2hunk
```

Darle permisos de ejecución:

```bash
chmod +x ~/.vscode/extensions/bartmanabyss.amiga-debug-*/bin/linux/elf2hunk
```

### Opción B: Compilar desde el código fuente

```bash
cd ~
git clone https://github.com/bebbo/elf2hunk.git
cd elf2hunk
make
sudo cp elf2hunk /opt/amiga/bin/
```

## Paso 5: Verificación Final

Ejecuta este script para verificar que todo está correctamente instalado:

```bash
#!/bin/bash
echo "=== Verificación del Entorno Dash ==="

echo -n "Python 3: "
python3 --version 2>/dev/null || echo "NO INSTALADO"

echo -n "Librería lark: "
python3 -c "import lark; print('OK')" 2>/dev/null || echo "NO INSTALADA"

tc=${DASH_TOOLCHAIN:-/opt/amiga}

echo -n "Cross-compiler: "
"$tc/bin/m68k-amigaos-gcc" --version 2>/dev/null | head -1 | grep . || echo "NO INSTALADO"

echo -n "GDB (depurador de VS Code): "
"$tc/bin/m68k-amigaos-gdb" --version 2>/dev/null | head -1 | grep . || echo "NO INSTALADO"

echo "=== Fin de verificación ==="
```

Y un programa de prueba: `./dash examples/hola.dash -o bin/hola`.

`./dash` compila con `gcc -O2` (opciones en `compiler/cflags.py`). `DASH_CFLAGS` añade opciones a gcc, para
probar: `DASH_CFLAGS="-Os" ./dash prog.dash -o bin/prog`.

## Paso 6: Probar en un emulador (opcional)

Dash ejecuta los programas en **FS-UAE** sin ventana y recoge su salida: `tools/emu_run.py` y los tests con
`--emu`. Instala FS-UAE con el gestor de paquetes (`fs-uae` en Arch, Debian y Ubuntu).

Con una ROM de Kickstart 3.1 (tuya, de un Amiga o de Amiga Forever) los resultados son los del Amiga real; sin
ella se usa la ROM AROS que trae FS-UAE:

```bash
export DASH_KICKSTART=~/roms/kick31_a1200.rom          # A1200 con 3.1 (--emu)
export DASH_KICKSTART_A500=~/roms/kick31_a500.rom      # A500 con 68000 (--emu-a500)
export DASH_KICKSTART_32=~/roms/kick323_a1200.rom      # A1200 con AmigaOS 3.2 (--emu-32 y rtg)
```

Algunos programas necesitan ficheros de un Workbench que no están en la ROM (`asl.library`, las clases de
ReAction, los datatypes). Se sacan de un disco duro de Amiberry o WinUAE con `tools/emu_sys_from_hdf.sh`, que usa
`xdftool` de amitools (basta un entorno virtual de Python):

```bash
python3 -m venv ~/.cache/amitools && ~/.cache/amitools/bin/pip install amitools
export XDFTOOL=~/.cache/amitools/bin/xdftool RDBTOOL=~/.cache/amitools/bin/rdbtool
tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/system3.1.hdf ~/.cache/dash-emu/sys31
tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/AmigaOS-v3.2.hdf ~/.cache/dash-emu/sys32
export DASH_EMU_SYS=~/.cache/dash-emu/sys31 DASH_EMU_SYS_32=~/.cache/dash-emu/sys32
```

La máquina `rtg` (un 68040 con tarjeta gráfica) usa la ROM 3.2 y `DASH_EMU_SYS_32_RTG`: un Workbench 3.2 con
Picasso96 en una pantalla de 16 bits. Dash no trae script para hacerlo (Tachyon, el navegador hecho con Dash, tiene
`tools/emu_sys_rtg.sh` en [su repositorio](https://github.com/FreeMEM/tachyon)); sin él, los tests `# rtg` se
saltan.

Prueba: `python3 tools/emu_run.py examples/hola.dash` y `python3 tests/run_tests.py --emu`. Opciones de
`tools/emu_run.py`:

- `--machine a1200|a500|a1200-32|rtg`: la máquina, con su ROM y su sistema de las variables de arriba.
- `--emulator amiberry`: Amiberry en lugar de FS-UAE (solo A1200 y A500). Su `bsdsocket` da sucesos de sockets.
- `--screenshot SEGUNDOS fichero.png`: una captura de la pantalla del Amiga.
- `--debug ORDEN`: el depurador del emulador desde un `debug_break()` del programa (ver el manual de referencia).
- `--gdbserver PUERTO`: el programa bajo `bgdbserver`, para `m68k-amigaos-gdb` (lo usa la extensión, paso 9).

## Paso 7: MUI (opcional)

Los programas con `mui_*` necesitan el SDK de MUI 5 para compilar (no se puede copiar al repositorio por su
licencia):

```bash
tools/get_mui_sdk.sh                                   # en ~/.cache/dash-mui/x (o en la carpeta que se le pase)
```

El SDK queda en `~/.cache/dash-mui/x/SDK/MUI`, que es donde lo busca `./dash`. Si lo descomprimes en otra carpeta,
pon esa ruta (la que acaba en `x/SDK/MUI`) en `DASH_MUI_SDK`.

Para probarlos en el emulador, un sistema con MUI instalado:

```bash
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys31mui ~/.cache/dash-emu/sys31
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys32mui ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_MUI=~/.cache/dash-emu/sys31mui DASH_EMU_SYS_32_MUI=~/.cache/dash-emu/sys32mui
```

`tools/emu_sys_mui.sh` toma MUI de `~/.cache/dash-mui/x/MUI` (lo deja ahí `tools/get_mui_sdk.sh`; otra carpeta:
`DASH_MUI_DIR`).

Para probar con MUI 3.8: un sistema como esos con el MUI 3.8 de Aminet (`mui38usr.lha`) en lugar de MUI 5, por
ejemplo `~/.cache/dash-emu/sys32rtg38` (el sistema RTG de Tachyon con MUI 3.8; hecho a mano, sin script), en
`DASH_EMU_SYS_32_MUI`. Con 3.8 todos los tests de MUI pasan salvo los de pantalla completa (el marco de 4 y 3
píxeles) y el de la versión de muimaster.

En el Amiga, MUI 3.8 (muimaster.library V19) o MUI 5 instalado y un 68020 o superior.

## Paso 8: Red y HTTPS (opcional)

`net_*` usa la `bsdsocket.library` del sistema (en FS-UAE, la que emula con la red del PC). `tls_*` necesita
AmiSSL 5.1 o posterior:

```bash
tools/get_amissl.sh                                    # SDK y librerías en ~/.cache/dash-amissl
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys31ssl ~/.cache/dash-emu/sys31
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys32ssl ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_SSL=~/.cache/dash-emu/sys31ssl DASH_EMU_SYS_32_SSL=~/.cache/dash-emu/sys32ssl
```

`./dash` busca las cabeceras de AmiSSL en `~/.cache/dash-amissl/x/AmiSSL/Developer` (otra carpeta: `DASH_AMISSL_SDK`).
Los dos scripts usan `~/.cache/dash-amissl` (otra: `DASH_AMISSL_DIR`).

Lo demás de la red (servidor TCP, UDP, interfaces de Roadshow, drivers SANA-II, WiFi) no necesita nada al
compilar. En FS-UAE se prueba con su `bsdsocket`; los sucesos de sockets (`net_signal`), con Amiberry
(`--emulator amiberry`).

## Paso 8b: Catálogos de idioma (opcional)

Los programas con `@catalog` y `tr(id, texto)` usan `locale.library`. Los ficheros de traducción se hacen con
`tools/catalogo.py` (solo Python, sin FlexCat):

```bash
python3 tools/catalogo.py cd programa.dash ventana.dashui -o Programa.cd           # los textos del programa
python3 tools/catalogo.py ct Programa.cd --language english --name Programa.catalog -o english.ct
python3 tools/catalogo.py catalog english.ct -o Catalogs/english/Programa.catalog  # el catálogo para el Amiga
```

## Paso 9: Extensión de VS Code (opcional)

Resaltado de Dash, errores mientras se escribe, compilar y ejecutar en el emulador desde el editor, depurador
(F5) y el editor visual de ventanas MUI (`.dashui`). Necesita VS Code 1.86 o posterior.

1. Baja `dash-mui-editor-0.2.1.vsix` de la release
   [vscode-0.2.1](https://github.com/FreeMEM/dash/releases/tag/vscode-0.2.1).
2. En VS Code, **Extensions: Install from VSIX...** y elige el fichero. O en la terminal:
   `code --install-extension dash-mui-editor-0.2.1.vsix`.
3. Si tu proyecto no está dentro de la carpeta de Dash, pon esa carpeta (la que tiene `./dash`) en el ajuste
   `dash.path`, o usa **Dash: Elegir la carpeta del compilador**.

Ajustes (`dash.*`):

| Ajuste | Para qué |
|---|---|
| `dash.path` | Carpeta de Dash. Vacío: se busca subiendo desde el fichero. |
| `dash.python` | El Python del servidor de lenguaje (`python3`; necesita lark). |
| `dash.languageServer.enabled` | Errores mientras se escribe, autocompletado y navegación. |
| `dash.editor.autoEnd` | Añade el `end` de un bloque al pulsar Intro. |
| `dash.emulator.machine` | Máquina: `a1200`, `a500`, `a1200-32` o `rtg`. |
| `dash.emulator.program` | Emulador: `fs-uae` o `amiberry`. |
| `dash.emulator.window` | Ver la ventana del emulador. |
| `dash.emulator.autoclose` | Segundos tras los que el programa se cierra solo (0: no). |
| `dash.emulator.kickstart`, `kickstartA500`, `kickstart32` | ROM de cada máquina (`DASH_KICKSTART`, `_A500`, `_32`). |
| `dash.emulator.system`, `system32`, `systemRtg` | Ficheros de Workbench (`DASH_EMU_SYS`, `_32`, `_32_RTG`). |
| `dash.emulator.muiSystem`, `muiSystem32` | Workbench con MUI para "Ver en Amiga" (`DASH_EMU_SYS_MUI`, `_32_MUI`). |
| `dash.emulator.previewOnChange` | "Ver en Amiga" otra vez, solo, tras cada cambio en el editor de ventanas. Está en el repositorio, aún no en la 0.2.1. |
| `dash.debug.gdb` | El `m68k-amigaos-gdb` (por defecto `/opt/amiga/bin/m68k-amigaos-gdb`). |

Los ficheros de ROM y Workbench son los de los pasos 6 y 7.

Para el depurador (F5) hacen falta `m68k-amigaos-gdb` con Python (lo instala `make all`, paso 3) y `bgdbserver`,
que corre dentro del Amiga:

```bash
tools/get_bgdbserver.sh            # en ~/.cache/dash-debug/x/bgdbserver/bgdbserver (o DASH_BGDBSERVER)
```

Basta bajarlo una vez: la extensión lo lleva sola al Amiga emulado. Para depurar en un Amiga de verdad, copia allí `bgdbserver` y el
programa de **Dash: Preparar para un Amiga real**; el Amiga necesita una pila TCP/IP. Los pasos están en el
README de la extensión (`editor/vscode/README.md`).

Para hacer el paquete desde el código:

```bash
cd editor/vscode
npm install                                            # herramientas de desarrollo, en node_modules
npm test
npm run package                                        # dash-mui-editor-<versión>.vsix
```

## Solución de Problemas

### Error en GDB durante la compilación (pero GCC se instala)

A veces la compilación de GDB (debugger) falla con errores como:

```
PySys_SetPath was not declared in this scope
make binutils gdb...failed
```

Para compilar programas no es crítico: GCC se instala bien. Pero el depurador de la extensión de VS Code sí
necesita `m68k-amigaos-gdb` con Python. Y las librerías de runtime (newlib, libnix) pueden no haberse instalado.
Con el fork actual (gdb 18) en CachyOS compila bien, con Python.

**Solución:** Ejecuta manualmente la instalación de las librerías:

```bash
cd ~/m68k-amigaos-gcc
make libnix -j$(nproc)
```

Esto compilará e instalará newlib y libnix, que son necesarias para compilar programas.

### Error: "_ansi.h: No such file or directory"

Este error al compilar indica que las librerías de runtime no están instaladas:

```
fatal error: _ansi.h: No such file or directory
```

**Solución:** Ejecuta `make libnix` como se indica arriba.

### Error: "cannot find -lamiga"

El toolchain no se compiló correctamente o faltan las librerías de AmigaOS. Vuelve a ejecutar `make all` en el directorio del toolchain.

### Aviso: "elf2hunk not found"

Solo sale con un GCC que genera ELF (el de bebbo de esta guía genera Hunk). Pon `elf2hunk` en el PATH (paso 4).

### La compilación del toolchain falla completamente

1. Asegúrate de tener todas las dependencias instaladas
2. Verifica que tienes suficiente espacio en disco (>10GB)
3. Intenta con `make clean` y luego `make all` de nuevo

### Error de permisos en /opt/amiga

Usa `sudo` o compila con un PREFIX diferente en tu directorio home (y `DASH_TOOLCHAIN`, paso 3.4).

## Siguiente Paso

Una vez instalado el entorno, consulta la documentación de Dash para empezar a programar:
- `docs/DOCUMENTACION_LENGUAJE.md` - Documentación completa del lenguaje
- `docs/QUICK_REFERENCE.md` - Referencia rápida
- `docs/MANUAL_REFERENCIA.md` - Manual de referencia
- `docs/BUILTINS.md` - Lista de builtins
