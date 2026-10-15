#!/bin/sh
# Make an emulated system with AmiSSL 5 for the tests that use tls_*: a copy of a
# Workbench files directory (default $DASH_EMU_SYS) plus SYS:AmiSSL (Libs, Certs) and the
# assigns of its installer, and a test CA in AmiSSL:Certs so that the runner's HTTPS
# test server (certificate signed by that CA) is trusted.
#
#   tools/get_amissl.sh
#   tools/emu_sys_amissl.sh ~/.cache/dash-emu/sys31ssl
#   export DASH_EMU_SYS_NET=~/.cache/dash-emu/sys31ssl
#
# The test CA is made once in ~/.cache/dash-amissl/testca (openssl on the PC).
set -e
[ $# -ge 1 ] || { echo "usage: $0 outdir [workbench-files-dir]" >&2; exit 2; }
out=$1
base=${2:-$DASH_EMU_SYS}
dir=${DASH_AMISSL_DIR:-$HOME/.cache/dash-amissl}
ssl=$dir/x/AmiSSL
[ -d "$base/Libs" ] || { echo "no Workbench files in '$base' (set DASH_EMU_SYS)" >&2; exit 2; }
[ -f "$ssl/Libs/AmigaOS3/amisslmaster.library" ] || { echo "no AmiSSL in $ssl (tools/get_amissl.sh)" >&2; exit 2; }
ca=$dir/testca
if [ ! -f "$ca/ca.pem" ]; then
  mkdir -p "$ca"
  openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=Dash test CA" \
      -keyout "$ca/ca.key" -out "$ca/ca.pem" 2>/dev/null
fi
rm -rf "$out"
mkdir -p "$out/AmiSSL/Libs/AmiSSL" "$out/S"
cp -r "$base"/. "$out"/
cp "$ssl/Libs/AmigaOS3/amisslmaster.library" "$out/AmiSSL/Libs/"
cp "$ssl"/Libs/AmigaOS3/AmiSSL/68020-40/*.library "$out/AmiSSL/Libs/AmiSSL/"
cp -r "$ssl/Certs" "$out/AmiSSL/Certs"
cp "$ca/ca.pem" "$out/AmiSSL/Certs/$(openssl x509 -hash -noout -in "$ca/ca.pem").0"   # default verify paths: Certs
cat >> "$out/S/Startup-Extra" <<'EOS'
C:Assign AmiSSL: SYS:AmiSSL
C:Assign LIBS: AmiSSL:Libs ADD
EOS
echo "$out: Workbench files of $base + AmiSSL ($(ls "$out/AmiSSL/Libs/AmiSSL"))"
