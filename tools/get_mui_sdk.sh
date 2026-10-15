#!/bin/sh
# Download MUI 5 for AmigaOS 3 (user files and SDK) from the official GitHub releases
# (amiga-mui/muidev) and unpack it into ~/.cache/dash-mui (or $1).
#
#   tools/get_mui_sdk.sh                 # -> ~/.cache/dash-mui/x/{MUI,SDK}
#   export DASH_MUI_SDK=~/.cache/dash-mui/x/SDK/MUI   # the default ./dash looks at
#
# The archive may only be redistributed complete and unmodified: keep it and its
# files out of git. Needs lha (or lhasa) and curl.
set -e
VER=5.0-20210831
URL=https://github.com/amiga-mui/muidev/releases/download/MUI-$VER/MUI-$VER-os3.lha
SHA=8a869a037db465828dbe42fa7854114121280ed2691afa61fe53a25bf427a847
dest=${1:-$HOME/.cache/dash-mui}
lha=$(command -v lha || command -v lhasa || true)
[ -n "$lha" ] || { echo "lha or lhasa not found" >&2; exit 2; }
mkdir -p "$dest/dl"
arc="$dest/dl/MUI-$VER-os3.lha"
if [ ! -f "$arc" ] || [ "$(sha256sum "$arc" | cut -d' ' -f1)" != "$SHA" ]; then
    curl -fsSL -o "$arc.part" "$URL"
    mv "$arc.part" "$arc"
fi
[ "$(sha256sum "$arc" | cut -d' ' -f1)" = "$SHA" ] || { echo "$arc: wrong SHA-256" >&2; exit 1; }
rm -rf "$dest/x"
mkdir -p "$dest/x"
(cd "$dest/x" && "$lha" xq "$arc")
[ -f "$dest/x/SDK/MUI/C/include/libraries/mui.h" ] || { echo "no SDK in $arc" >&2; exit 1; }
echo "MUI $VER in $dest/x (SDK: $dest/x/SDK/MUI)"
