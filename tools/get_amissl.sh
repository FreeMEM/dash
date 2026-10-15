#!/bin/sh
# Download AmiSSL 5 (OS3 user files and SDK) from its official GitHub releases into
# ~/.cache/dash-amissl and extract it there (x/AmiSSL). Nothing of it goes to git.
# Programs that use tls_* need it to compile (headers) and to run (libraries, AmiSSL:).
set -e
version=${AMISSL_VERSION:-5.27}
dir=${DASH_AMISSL_DIR:-$HOME/.cache/dash-amissl}
mkdir -p "$dir/dl" "$dir/x"
for part in OS3 SDK; do
  f="AmiSSL-$version-$part.lha"
  [ -f "$dir/dl/$f" ] || curl -sfL -o "$dir/dl/$f" "https://github.com/jens-maus/amissl/releases/download/$version/$f"
done
if [ "$version" = 5.27 ]; then
  (cd "$dir/dl" && sha256sum -c - <<EOS
722476cfbf21c0caf6ff4a77e32ee8baf67d3045db0e9ff2ccce6c782bed5847  AmiSSL-5.27-OS3.lha
5003bef8c5930354d16b0ce7196d71b2811891c42fad38a9238c5ce4098ad42a  AmiSSL-5.27-SDK.lha
EOS
  )
fi
lha=${LHA:-/opt/amiga/bin/lha}
(cd "$dir/x" && for f in "$dir"/dl/AmiSSL-$version-*.lha; do "$lha" xqf "$f"; done)
echo "AmiSSL $version in $dir/x/AmiSSL (SDK: $dir/x/AmiSSL/Developer)"
