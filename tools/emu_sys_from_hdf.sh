#!/bin/sh
# Extract the Workbench files the emulator bench needs (Libs/, C/Assign, C/MakeDir)
# from an Amiga hard file (.hdf, no RDB) into a directory for $DASH_EMU_SYS.
#
#   tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/system3.1.hdf ~/.cache/dash-emu/sys31
#   export DASH_EMU_SYS=~/.cache/dash-emu/sys31
#
# Uses xdftool from amitools (pip install amitools, a venv is enough). The hard
# file is copied first and only read. The files are Workbench's: keep them out of git.
set -e
[ $# -eq 2 ] || { echo "usage: $0 file.hdf outdir" >&2; exit 2; }
XDF=${XDFTOOL:-xdftool}
command -v "$XDF" >/dev/null || { echo "xdftool not found (pip install amitools, or set XDFTOOL)" >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp "$1" "$tmp/disk.hdf"
mkdir -p "$2/Libs" "$2/C"
for lib in asl diskfont iffparse locale mathieeesingtrans mathieeedoubbas mathieeedoubtrans \
           mathtrans lowlevel commodities datatypes; do
    "$XDF" "$tmp/disk.hdf" read "Libs/$lib.library" "$2/Libs/$lib.library" >/dev/null 2>&1 \
        && echo "Libs/$lib.library"
done
for cmd in Assign MakeDir; do
    "$XDF" "$tmp/disk.hdf" read "C/$cmd" "$2/C/$cmd" >/dev/null 2>&1 && echo "C/$cmd"
done
