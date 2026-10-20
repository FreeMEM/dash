#!/bin/sh
# Download bgdbserver 1.3 (Stefan "Bebbo" Franke's gdbserver for AmigaOS, GPLv3) from Aminet and unpack
# it into ~/.cache/dash-debug (or $1). It runs inside the Amiga (emulated or real, with bsdsocket.library)
# and m68k-amigaos-gdb connects to it by TCP: the debugger of the VS Code extension (docs/IDE_LOOP.md).
#
#   tools/get_bgdbserver.sh            # -> ~/.cache/dash-debug/x/bgdbserver/bgdbserver
#
# GPLv3: kept out of this repository (it is not linked with Dash programs; it is a tool that runs them).
# Needs lha (or lhasa) and curl.
set -e
URL=https://aminet.net/dev/debug/bgdbserver.lha
SHA=3cecf10390e8d47ac3acca0b6992f990f060a97593541bd75078dcc4049c7dc5
dest=${1:-$HOME/.cache/dash-debug}
lha=$(command -v lha || command -v lhasa || true)
[ -n "$lha" ] || { echo "lha or lhasa not found" >&2; exit 2; }
mkdir -p "$dest/dl"
arc="$dest/dl/bgdbserver.lha"
if [ ! -f "$arc" ] || [ "$(sha256sum "$arc" | cut -d' ' -f1)" != "$SHA" ]; then
    curl -fsSL -o "$arc.part" "$URL"
    mv "$arc.part" "$arc"
fi
[ "$(sha256sum "$arc" | cut -d' ' -f1)" = "$SHA" ] || { echo "$arc: wrong SHA-256 (a new version on Aminet?)" >&2; exit 1; }
rm -rf "$dest/x"
mkdir -p "$dest/x"
(cd "$dest/x" && "$lha" xq "$arc")
[ -f "$dest/x/bgdbserver/bgdbserver" ] || { echo "no bgdbserver in $arc" >&2; exit 1; }
echo "bgdbserver in $dest/x/bgdbserver/bgdbserver"
