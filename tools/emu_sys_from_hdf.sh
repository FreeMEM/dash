#!/bin/sh
# Extract the Workbench files the emulator bench needs (Libs/, Classes/, C/Assign,
# C/MakeDir, C/LoadWB) from an Amiga hard file into a directory for $DASH_EMU_SYS.
#
#   tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/system3.1.hdf ~/.cache/dash-emu/sys31
#   export DASH_EMU_SYS=~/.cache/dash-emu/sys31
#   tools/emu_sys_from_hdf.sh ~/Amiberry/HardDrives/AmigaOS-v3.2.hdf ~/.cache/dash-emu/sys32
#   export DASH_EMU_SYS_32=~/.cache/dash-emu/sys32
#
# The hard file is only read. A file with partitions (RDB, "RDSK") is read from its
# first partition, copied out with dd; one without them is copied whole.
# Classes/ (ReAction: window.class, Gadgets/, Images/) is copied when the disk has it.
# workbench.library and icon.library are on the disk from 3.2 on (3.1 has them in ROM);
# C/LoadWB is for tools/emu_run.py --workbench.
#
# Uses xdftool and rdbtool from amitools (pip install amitools, a venv is enough; or
# set XDFTOOL and RDBTOOL). The files are Workbench's: keep them out of git.
set -e
[ $# -eq 2 ] || { echo "usage: $0 file.hdf outdir" >&2; exit 2; }
XDF=${XDFTOOL:-xdftool}
RDB=${RDBTOOL:-$(dirname "$(command -v "$XDF" 2>/dev/null || echo .)")/rdbtool}
command -v "$XDF" >/dev/null || { echo "xdftool not found (pip install amitools, or set XDFTOOL)" >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if [ "$(head -c 4 "$1")" = "RDSK" ]; then
    [ -x "$RDB" ] || RDB=rdbtool
    # "LogicalDisk: ... cyl_blks=N" and "Partition: #0 'Name' first_cyl last_cyl blocks ..."
    info=$("$RDB" -r "$1" info)
    cyl_blks=$(echo "$info" | sed -n 's/.*cyl_blks=\([0-9]*\).*/\1/p' | head -1)
    set -- "$1" "$2" $(echo "$info" | awk '/^Partition: #0/ {print $4, $6; exit}')
    [ -n "$cyl_blks" ] && [ -n "$4" ] || { echo "$1: no partition #0 in the RDB" >&2; exit 2; }
    dd if="$1" of="$tmp/disk.hdf" bs=512 skip=$(($3 * cyl_blks)) count="$4" status=none
else
    cp "$1" "$tmp/disk.hdf"
fi
mkdir -p "$2/Libs" "$2/C"
for lib in asl diskfont iffparse locale mathieeesingtrans mathieeedoubbas mathieeedoubtrans \
           mathtrans lowlevel commodities datatypes workbench icon; do
    "$XDF" "$tmp/disk.hdf" read "Libs/$lib.library" "$2/Libs/$lib.library" >/dev/null 2>&1 \
        && echo "Libs/$lib.library"
done
for cmd in Assign MakeDir LoadWB; do
    "$XDF" "$tmp/disk.hdf" read "C/$cmd" "$2/C/$cmd" >/dev/null 2>&1 && echo "C/$cmd"
done
if "$XDF" "$tmp/disk.hdf" list Classes >/dev/null 2>&1; then
    rm -rf "$2/Classes"
    "$XDF" "$tmp/disk.hdf" read Classes "$2/Classes" >/dev/null && echo "Classes/"
fi
