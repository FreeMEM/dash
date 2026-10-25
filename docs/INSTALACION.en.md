# Dash Installation Guide

*English | [Castellano](INSTALACION.md)*
Version: 2.1 (up to date as of 2026-10-24)

This document describes how to set up a complete development environment for programming in Dash, from scratch.

## Host System Requirements

- **Operating System:** Linux (Ubuntu/Debian recommended), macOS, or Windows with WSL2
- **RAM:** Minimum 8GB (16GB+ recommended for building the toolchain)
- **Disk:** Minimum 10GB free for the toolchain
- **CPU:** Multi-core recommended (the build uses all cores)

## Amiga Requirements

What programs made with Dash need, on a real or emulated Amiga:

- **AmigaOS 3.0 or higher** (Kickstart V39: exec memory pools).
- **68000 or higher.** With `./dash --fpu`, a 68020 with a 68881/68882 FPU.
- **MUI** (`mui_*`): MUI 3.8 (muimaster.library V19) or MUI 5, and a 68020 or higher.
- **Network** (`net_*`): a TCP/IP stack (`bsdsocket.library`: Roadshow, AmiTCP, Miami...).
- **HTTPS** (`tls_*`): in addition, AmiSSL 5.1 or later, which requires a 68020 or higher.
- **ReAction** (`ra_*`): the AmigaOS 3.2 ReAction classes.
- **Network interfaces and WiFi** (`net_ifs_read`, `wifi_read`): Roadshow. **USB** (`usb_hid_*`): Poseidon.

The full list is in `REQUERIMIENTOS_SISTEMA.md`.

## Step 1: Install Python and Dash Dependencies

Dash uses a transpiler written in Python. Python 3.10 or higher is required.

```bash
# Check the Python version
python3 --version

# Install the lark library (parser)
pip install lark --break-system-packages
```

## Step 2: Install the Cross-Compiler Dependencies

The cross-compilation toolchain requires several development tools:

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

`curl` and `lhasa` are used by the scripts that download the MUI SDK, AmiSSL and bgdbserver (`tools/get_*.sh`); `openssl`,
by `tools/emu_sys_amissl.sh`. The Python headers (`python3-dev`, `python3-devel`) are for the toolchain's GDB,
which the extension's debugger needs with Python support.

### macOS

```bash
# Install Homebrew first: https://brew.sh/
brew install bash wget make lhasa gmp mpfr libmpc flex gettext gnu-sed texinfo gcc@12 autoconf bison
```

## Step 3: Build the Cross-Compiler (m68k-amigaos-gcc)

This is the most important step and the one that takes the longest. We use the fork maintained by BlitterStudio, which is the de facto standard for modern Amiga development.

### 3.1 Clone the repository

```bash
cd ~
git clone https://github.com/BlitterStudio/m68k-amigaos-gcc.git
cd m68k-amigaos-gcc
```

### 3.2 Download submodules and dependencies

```bash
make update
```

This command downloads GCC, Binutils, libnix, the NDK and all the necessary dependencies.

### 3.3 Create the installation directory

By default the toolchain is installed in `/opt/amiga`. Create the directory with write permissions:

```bash
sudo mkdir -p /opt/amiga
sudo chown $USER /opt/amiga
```

### 3.4 Build and install

The build can take between 30 minutes and 2 hours depending on your hardware.

```bash
# Build using all available cores
make all -j$(nproc)

# CyberGraphX headers (the rtg_* functions need them)
make sdk=cgx
```

`make all` also installs `m68k-amigaos-gdb`, the debugger used by the VS Code extension.

**Note:** On macOS, use Homebrew's bash:

```bash
make all -j$(nproc) SHELL=$(brew --prefix)/bin/bash
```

**Note:** If you prefer to install in another directory:

```bash
make all PREFIX=~/amiga-toolchain -j$(nproc)
make sdk=cgx PREFIX=~/amiga-toolchain
export DASH_TOOLCHAIN=~/amiga-toolchain     # where ./dash looks for it (by default, /opt/amiga)
```

`DASH_TOOLCHAIN` is only read by `./dash`. The tests (`tests/run_tests.py`), the emulator screenshot tool
(`tools/amiga/shot.c`, compiled by `tools/emu_run.py`) and `tools/get_amissl.sh` (its `lha`; or `LHA=...`) use
`/opt/amiga` as a fixed path. If the toolchain is somewhere else, a symlink fixes it: `sudo ln -s ~/amiga-toolchain /opt/amiga`.

### 3.5 Verify the installation

```bash
/opt/amiga/bin/m68k-amigaos-gcc --version
```

You should see something like:

```
m68k-amigaos-gcc (GCC) 6.5.0b
Copyright (C) 2017 Free Software Foundation, Inc.
```

### 3.6 Add to PATH (optional but recommended)

So you do not have to type the full path every time:

```bash
# Append to the end of ~/.bashrc (or ~/.zshrc on macOS)
echo 'export PATH="/opt/amiga/bin:$PATH"' >> ~/.bashrc

# Reload the configuration
source ~/.bashrc

# Verify
m68k-amigaos-gcc --version
```

### 3.7 Available GCC branches

The repository offers several GCC versions:

| Branch | GCC version | Features |
|------|-------------|-----------------|
| `amiga6` | 6.5.0b | Default; the one Dash uses |
| `amiga10.4` | 10.4.0 | Supports register parameters |
| `amiga13.4` | 13.4.0 | Supports register parameters |
| `amiga15.2` | 15.2.0 | Supports register parameters |
| `amiga16.2` | 16.2.0 | The toolchain's development branch |

(List from the toolchain README in August 2026; it may change.)

Dash is tested with `amiga6` (GCC 6.5.0b); other branches are untested. To use a different version (do this before building):

```bash
make branch branch=amiga13.4 mod=gcc
make all -j$(nproc)
```

## Step 4: elf2hunk (not usually needed)

bebbo's cross-compiler (`m68k-amigaos-gcc`, the one in this guide) already produces executables in Hunk format, the one
AmigaOS uses, and `./dash` leaves them as they are. `elf2hunk` is only needed with a GCC that produces ELF; if `./dash`
finds an ELF and has `elf2hunk`, it converts it.

### Option A: From the VS Code extension (easiest)

If you use VS Code, install the `bartmanabyss.amiga-debug` extension. The binary will be in:

```
~/.vscode/extensions/bartmanabyss.amiga-debug-*/bin/linux/elf2hunk
```

Make it executable:

```bash
chmod +x ~/.vscode/extensions/bartmanabyss.amiga-debug-*/bin/linux/elf2hunk
```

### Option B: Build from source

```bash
cd ~
git clone https://github.com/bebbo/elf2hunk.git
cd elf2hunk
make
sudo cp elf2hunk /opt/amiga/bin/
```

## Step 5: Final Check

Run this script to check that everything is installed correctly:

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

And a test program: `./dash examples/hola.dash -o bin/hola`.

`./dash` compiles with `gcc -O2` (options in `compiler/cflags.py`). `DASH_CFLAGS` adds options to gcc, for
experimenting: `DASH_CFLAGS="-Os" ./dash prog.dash -o bin/prog`.

## Step 6: Test in an emulator (optional)

Dash runs programs in **FS-UAE** without a window and collects their output: `tools/emu_run.py` and the tests with
`--emu`. Install FS-UAE with your package manager (`fs-uae` on Arch, Debian and Ubuntu).

With a Kickstart 3.1 ROM (your own, from an Amiga or from Amiga Forever) the results are those of a real Amiga; without
one, the AROS ROM that comes with FS-UAE is used:

```bash
export DASH_KICKSTART=~/roms/kick31_a1200.rom          # A1200 with 3.1 (--emu)
export DASH_KICKSTART_A500=~/roms/kick31_a500.rom      # A500 with 68000 (--emu-a500)
export DASH_KICKSTART_32=~/roms/kick323_a1200.rom      # A1200 with AmigaOS 3.2 (--emu-32 and rtg)
```

Some programs need Workbench files that are not in the ROM (`asl.library`, the ReAction
classes, the datatypes). They are extracted from an Amiberry or WinUAE hard disk with `tools/emu_sys_from_hdf.sh`, which uses
amitools' `xdftool` (a Python virtual environment is enough):

```bash
python3 -m venv ~/.cache/amitools && ~/.cache/amitools/bin/pip install amitools
export XDFTOOL=~/.cache/amitools/bin/xdftool RDBTOOL=~/.cache/amitools/bin/rdbtool
tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/system3.1.hdf ~/.cache/dash-emu/sys31
tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/AmigaOS-v3.2.hdf ~/.cache/dash-emu/sys32
export DASH_EMU_SYS=~/.cache/dash-emu/sys31 DASH_EMU_SYS_32=~/.cache/dash-emu/sys32
```

The `rtg` machine (a 68040 with a graphics card) uses the 3.2 ROM and `DASH_EMU_SYS_32_RTG`: a Workbench 3.2 with
Picasso96 on a 16-bit screen. Dash does not ship a script to make it (Tachyon, the browser made with Dash, has
`tools/emu_sys_rtg.sh` in [its repository](https://github.com/FreeMEM/tachyon)); without it, the `# rtg` tests are
skipped.

Try it: `python3 tools/emu_run.py examples/hola.dash` and `python3 tests/run_tests.py --emu`. Options of
`tools/emu_run.py`:

- `--machine a1200|a500|a1200-32|rtg`: the machine, with its ROM and its system from the variables above.
- `--emulator amiberry`: Amiberry instead of FS-UAE (A1200 and A500 only). Its `bsdsocket` provides socket events.
- `--screenshot SEGUNDOS fichero.png`: a screenshot of the Amiga screen.
- `--debug ORDEN`: the emulator's debugger from a `debug_break()` in the program (see the reference manual).
- `--gdbserver PUERTO`: the program under `bgdbserver`, for `m68k-amigaos-gdb` (used by the extension, step 9).

## Step 7: MUI (optional)

Programs with `mui_*` need the MUI 5 SDK to compile (it cannot be copied into the repository because of its
licence):

```bash
tools/get_mui_sdk.sh                                   # into ~/.cache/dash-mui/x (or into the folder passed to it)
```

The SDK ends up in `~/.cache/dash-mui/x/SDK/MUI`, which is where `./dash` looks for it. If you unpack it into another folder,
put that path (the one ending in `x/SDK/MUI`) in `DASH_MUI_SDK`.

To test them in the emulator, a system with MUI installed:

```bash
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys31mui ~/.cache/dash-emu/sys31
tools/emu_sys_mui.sh ~/.cache/dash-emu/sys32mui ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_MUI=~/.cache/dash-emu/sys31mui DASH_EMU_SYS_32_MUI=~/.cache/dash-emu/sys32mui
```

`tools/emu_sys_mui.sh` takes MUI from `~/.cache/dash-mui/x/MUI` (`tools/get_mui_sdk.sh` puts it there; another folder:
`DASH_MUI_DIR`).

To test with MUI 3.8: a system like those with MUI 3.8 from Aminet (`mui38usr.lha`) instead of MUI 5, for
example `~/.cache/dash-emu/sys32rtg38` (Tachyon's RTG system with MUI 3.8; made by hand, without a script), in
`DASH_EMU_SYS_32_MUI`. With 3.8 all the MUI tests pass except the full-screen ones (the frame of 4 and 3
pixels) and the muimaster version one.

On the Amiga, MUI 3.8 (muimaster.library V19) or MUI 5 installed and a 68020 or higher.

## Step 8: Network and HTTPS (optional)

`net_*` uses the system's `bsdsocket.library` (in FS-UAE, the one it emulates using the PC's network). `tls_*` needs
AmiSSL 5.1 or later:

```bash
tools/get_amissl.sh                                    # SDK and libraries in ~/.cache/dash-amissl
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys31ssl ~/.cache/dash-emu/sys31
tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys32ssl ~/.cache/dash-emu/sys32
export DASH_EMU_SYS_SSL=~/.cache/dash-emu/sys31ssl DASH_EMU_SYS_32_SSL=~/.cache/dash-emu/sys32ssl
```

`./dash` looks for the AmiSSL headers in `~/.cache/dash-amissl/x/AmiSSL/Developer` (another folder: `DASH_AMISSL_SDK`).
Both scripts use `~/.cache/dash-amissl` (another one: `DASH_AMISSL_DIR`).

The rest of the networking (TCP server, UDP, Roadshow interfaces, SANA-II drivers, WiFi) needs nothing at
compile time. In FS-UAE it is tested with its `bsdsocket`; socket events (`net_signal`), with Amiberry
(`--emulator amiberry`).

## Step 8b: Language catalogs (optional)

Programs with `@catalog` and `tr(id, texto)` use `locale.library`. The translation files are made with
`tools/catalogo.py` (Python only, no FlexCat):

```bash
python3 tools/catalogo.py cd programa.dash ventana.dashui -o Programa.cd           # the program's strings
python3 tools/catalogo.py ct Programa.cd --language english --name Programa.catalog -o english.ct
python3 tools/catalogo.py catalog english.ct -o Catalogs/english/Programa.catalog  # the catalog for the Amiga
```

## Step 9: VS Code extension (optional)

Dash highlighting, errors as you type, compiling and running in the emulator from the editor, debugger
(F5) and the visual editor for MUI windows (`.dashui`). It needs VS Code 1.86 or later.

1. Download `dash-mui-editor-0.2.1.vsix` from the
   [vscode-0.2.1](https://github.com/FreeMEM/dash/releases/tag/vscode-0.2.1) release.
2. In VS Code, **Extensions: Install from VSIX...** and choose the file. Or in the terminal:
   `code --install-extension dash-mui-editor-0.2.1.vsix`.
3. If your project is not inside the Dash folder, put that folder (the one with `./dash`) in the
   `dash.path` setting, or use **Dash: Elegir la carpeta del compilador**.

Settings (`dash.*`):

| Setting | What for |
|---|---|
| `dash.path` | Dash folder. Empty: searched for by going up from the file. |
| `dash.python` | The Python for the language server (`python3`; needs lark). |
| `dash.languageServer.enabled` | Errors as you type, autocompletion and navigation. |
| `dash.editor.autoEnd` | Adds a block's `end` when you press Enter. |
| `dash.emulator.machine` | Machine: `a1200`, `a500`, `a1200-32` or `rtg`. |
| `dash.emulator.program` | Emulator: `fs-uae` or `amiberry`. |
| `dash.emulator.window` | Show the emulator window. |
| `dash.emulator.autoclose` | Seconds after which the program closes by itself (0: never). |
| `dash.emulator.kickstart`, `kickstartA500`, `kickstart32` | ROM for each machine (`DASH_KICKSTART`, `_A500`, `_32`). |
| `dash.emulator.system`, `system32`, `systemRtg` | Workbench files (`DASH_EMU_SYS`, `_32`, `_32_RTG`). |
| `dash.emulator.muiSystem`, `muiSystem32` | Workbench with MUI for "Ver en Amiga" (`DASH_EMU_SYS_MUI`, `_32_MUI`). |
| `dash.emulator.previewOnChange` | "Ver en Amiga" again, automatically, after each change in the window editor. It is in the repository, not yet in 0.2.1. |
| `dash.debug.gdb` | The `m68k-amigaos-gdb` (by default `/opt/amiga/bin/m68k-amigaos-gdb`). |

The ROM and Workbench files are those from steps 6 and 7.

The debugger (F5) needs `m68k-amigaos-gdb` with Python (installed by `make all`, step 3) and `bgdbserver`,
which runs inside the Amiga:

```bash
tools/get_bgdbserver.sh            # into ~/.cache/dash-debug/x/bgdbserver/bgdbserver (or DASH_BGDBSERVER)
```

Downloading it once is enough: the extension takes it to the emulated Amiga by itself. To debug on a real Amiga, copy `bgdbserver` there along with the
program from **Dash: Preparar para un Amiga real**; the Amiga needs a TCP/IP stack. The steps are in the
extension's README (`editor/vscode/README.md`).

To build the package from source:

```bash
cd editor/vscode
npm install                                            # development tools, in node_modules
npm test
npm run package                                        # dash-mui-editor-<versión>.vsix
```

## Troubleshooting

### GDB error during the build (but GCC gets installed)

Sometimes the GDB (debugger) build fails with errors such as:

```
PySys_SetPath was not declared in this scope
make binutils gdb...failed
```

For compiling programs this is not critical: GCC installs fine. But the VS Code extension's debugger does
need `m68k-amigaos-gdb` with Python. And the runtime libraries (newlib, libnix) may not have been installed.
With the current fork (gdb 18) it builds fine on CachyOS, with Python.

**Solution:** Run the library installation manually:

```bash
cd ~/m68k-amigaos-gcc
make libnix -j$(nproc)
```

This will build and install newlib and libnix, which are needed to compile programs.

### Error: "_ansi.h: No such file or directory"

This error when compiling means the runtime libraries are not installed:

```
fatal error: _ansi.h: No such file or directory
```

**Solution:** Run `make libnix` as described above.

### Error: "cannot find -lamiga"

The toolchain was not built correctly or the AmigaOS libraries are missing. Run `make all` again in the toolchain directory.

### Warning: "elf2hunk not found"

It only appears with a GCC that produces ELF (bebbo's, used in this guide, produces Hunk). Put `elf2hunk` in the PATH (step 4).

### The toolchain build fails completely

1. Make sure you have all the dependencies installed
2. Check that you have enough disk space (>10GB)
3. Try `make clean` and then `make all` again

### Permission error on /opt/amiga

Use `sudo` or build with a different PREFIX in your home directory (and `DASH_TOOLCHAIN`, step 3.4).

## Next Step

Once the environment is installed, see the Dash documentation to start programming:
- `docs/DOCUMENTACION_LENGUAJE.md` - Complete language documentation
- `docs/QUICK_REFERENCE.md` - Quick reference
- `docs/MANUAL_REFERENCIA.md` - Reference manual
- `docs/BUILTINS.md` - List of builtins
