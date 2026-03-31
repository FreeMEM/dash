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

## Paso 4: Instalar elf2hunk

Los ejecutables generados por el cross-compiler están en formato ELF, pero AmigaOS necesita el formato Hunk. La utilidad `elf2hunk` realiza esta conversión.

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

### Error: "elf2hunk: command not found"

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
