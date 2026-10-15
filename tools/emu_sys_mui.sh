#!/bin/sh
# Make an emulated system with MUI 5 for tools/emu_run.py and the test runner:
# a copy of a Workbench files directory (default $DASH_EMU_SYS) plus SYS:MUI
# (Libs, Images, Locale) and the assigns its installer adds to User-Startup.
#
#   tools/get_mui_sdk.sh
#   tools/emu_sys_mui.sh ~/.cache/dash-emu/sys31mui
#   export DASH_EMU_SYS_MUI=~/.cache/dash-emu/sys31mui
#
# Keep the result out of git (Workbench and MUI files).
set -e
[ $# -ge 1 ] || { echo "usage: $0 outdir [workbench-files-dir]" >&2; exit 2; }
out=$1
base=${2:-$DASH_EMU_SYS}
mui=${DASH_MUI_DIR:-$HOME/.cache/dash-mui/x/MUI}
[ -d "$base/Libs" ] || { echo "no Workbench files in '$base' (set DASH_EMU_SYS)" >&2; exit 2; }
[ -f "$mui/Libs/muimaster.library" ] || { echo "no MUI in $mui (tools/get_mui_sdk.sh)" >&2; exit 2; }
rm -rf "$out"
mkdir -p "$out/MUI" "$out/S"
cp -r "$base"/. "$out"/
for d in Libs Images Locale; do cp -r "$mui/$d" "$out/MUI/$d"; done
cat > "$out/S/Startup-Extra" <<'EOS'
C:Assign MUI: SYS:MUI
C:Assign LIBS: MUI:Libs ADD
C:Assign LOCALE: MUI:Locale ADD
EOS
echo "$out: Workbench files of $base + MUI"
