# Guía de Instalación de Dash
Versión: 2.0

Este documento describe cómo configurar un entorno de desarrollo completo para programar en Dash, desde cero.

## Requisitos del Sistema Host

- **Sistema Operativo:** Linux (Ubuntu/Debian recomendado), macOS, o Windows con WSL2
- **RAM:** Mínimo 8GB (16GB+ recomendado para compilar el toolchain)
- **Disco:** Mínimo 10GB libres para el toolchain
- **CPU:** Multi-core recomendado (la compilación usa todos los núcleos)

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
    make \
    wget \
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
    git \
    gcc \
    gcc-c++ \
    python \
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
    rsync \
    readline-devel \
    which
```

### Arch Linux

```bash
sudo pacman -S --needed \
    make \
    wget \
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
```

**Nota:** En macOS, usa el bash de Homebrew:

```bash
make all -j$(nproc) SHELL=$(brew --prefix)/bin/bash
```

**Nota:** Si prefieres instalar en otro directorio:

```bash
make all PREFIX=/home/tu_usuario/amiga-toolchain -j$(nproc)
```

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
| `amiga6` | 6.5.0b | Por defecto, muy estable |
| `amiga13.3` | 13.3.0 | Soporta parámetros en registros |
| `amiga15.2` | 15.2.0 | Última versión disponible |

Para usar una versión diferente (hazlo antes de compilar):

```bash
make branch branch=amiga13.3 mod=gcc
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

echo -n "Cross-compiler: "
/opt/amiga/bin/m68k-amigaos-gcc --version 2>/dev/null | head -1 || echo "NO INSTALADO"

echo -n "elf2hunk: "
which elf2hunk 2>/dev/null || ls ~/.vscode/extensions/bartmanabyss.amiga-debug-*/bin/linux/elf2hunk 2>/dev/null || echo "NO ENCONTRADO"

echo "=== Fin de verificación ==="
```

## Paso 6: Probar en un emulador (opcional)

Dash ejecuta los programas en **FS-UAE** sin ventana y recoge su salida: `tools/emu_run.py` y los tests con
`--emu`. Instala FS-UAE con el gestor de paquetes (`fs-uae` en Arch, Debian y Ubuntu).

Con una ROM de Kickstart 3.1 (tuya, de un Amiga o de Amiga Forever) los resultados son los del Amiga real; sin
ella se usa la ROM AROS que trae FS-UAE:

```bash
export DASH_KICKSTART=~/roms/kick31_a1200.rom          # A1200 con 3.1 (--emu)
export DASH_KICKSTART_A500=~/roms/kick31_a500.rom      # A500 con 68000 (--emu-a500)
export DASH_KICKSTART_32=~/roms/kick323_a1200.rom      # A1200 con AmigaOS 3.2 (--emu-32)
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

Prueba: `python3 tools/emu_run.py examples/hola.dash` y `python3 tests/run_tests.py --emu`. Con
`--screenshot SEGUNDOS fichero.png` se guarda una captura de la pantalla del Amiga, y con `--debug ORDEN` se
usa el depurador del emulador desde un `debug_break()` del programa (ver el manual de referencia).

## Paso 7: MUI (opcional)

Los programas con `mui_*` necesitan el SDK de MUI 5 para compilar (no se puede copiar al repositorio por su
licencia):

```bash
tools/get_mui_sdk.sh                                   # en ~/.cache/dash-mui (o DASH_MUI_SDK)
```

Para probarlos en el emulador, un sistema con MUI instalado:

```bash
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys31mui ~/.cache/dash-emu/sys31
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys32mui ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_MUI=~/.cache/dash-emu/sys31mui DASH_EMU_SYS_32_MUI=~/.cache/dash-emu/sys32mui
```

Para probar con MUI 3.8: un sistema como esos con el MUI 3.8 de Aminet (`mui38usr.lha`) en lugar de MUI 5, por
ejemplo `~/.cache/dash-emu/sys32rtg38` (el sistema RTG de dashweb con MUI 3.8; hecho a mano, sin script), en
`DASH_EMU_SYS_32_MUI`. Con 3.8 todos los tests de MUI pasan salvo los de pantalla completa (el marco de 4 y 3
píxeles) y el de la versión de muimaster.

En el Amiga, MUI 3.8 o 5 instalado y un 68020 o superior.

## Paso 8: Red y HTTPS (opcional)

`net_*` usa la `bsdsocket.library` del sistema (en FS-UAE, la que emula con la red del PC). `tls_*` necesita
AmiSSL 5:

```bash
tools/get_amissl.sh                                    # SDK y librerías en ~/.cache/dash-amissl
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys31ssl ~/.cache/dash-emu/sys31
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys32ssl ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_SSL=~/.cache/dash-emu/sys31ssl DASH_EMU_SYS_32_SSL=~/.cache/dash-emu/sys32ssl
```

## Paso 9: Extensión de VS Code (opcional)

Resaltado de Dash, compilar y ejecutar en el emulador desde el editor, y el editor visual de ventanas MUI
(`.dashui`):

```bash
cd editor/vscode
npm install                                            # herramientas de desarrollo, en node_modules
npm test
npm run package                                        # dash-mui-editor-<versión>.vsix
code --install-extension dash-mui-editor-*.vsix
```

En los ajustes de VS Code: `dash.path` (carpeta de Dash, si no se encuentra sola), `dash.emulator.kickstart`,
`dash.emulator.system` y `dash.emulator.muiSystem` (los mismos ficheros que en los pasos 6 y 7).

## Solución de Problemas

### Error en GDB durante la compilación (pero GCC se instala)

Es común que la compilación de GDB (debugger) falle con errores como:

```
PySys_SetPath was not declared in this scope
make binutils gdb...failed
```

**Esto NO es crítico.** GCC (el compilador) se instala correctamente, pero las librerías de runtime (newlib, libnix) pueden no haberse instalado.

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

Asegúrate de que `elf2hunk` está en tu PATH o usa la ruta completa.

### La compilación del toolchain falla completamente

1. Asegúrate de tener todas las dependencias instaladas
2. Verifica que tienes suficiente espacio en disco (>10GB)
3. Intenta con `make clean` y luego `make all` de nuevo

### Error de permisos en /opt/amiga

Usa `sudo` o compila con un PREFIX diferente en tu directorio home.

## Siguiente Paso

Una vez instalado el entorno, consulta la documentación de Dash para empezar a programar:
- `docs/DOCUMENTACION_LENGUAJE.md` - Documentación completa del lenguaje
- `docs/CHULETA_LENGUAJE.md` - Referencia rápida
