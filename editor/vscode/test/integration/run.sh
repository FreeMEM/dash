#!/bin/sh
# npm run test:vscode: the tests of test/integration inside the installed VS Code (Code - OSS), with a
# profile and extension folder of their own, so the user's are not touched.
here=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
export DASH_IT_RESULT="$tmp/result.txt"
mkdir -p "$tmp/ws"                   # a folder open in the window: VS Code's tasks need one
# the Electron of Code - OSS directly: the `code` launcher hands over to a running VS Code and does not wait
run_code() {
    if [ -x /usr/lib/electron42/electron ] && [ -f /usr/lib/code/code.mjs ]; then
        /usr/lib/electron42/electron /usr/lib/code/code.mjs "$@"
    else
        code --wait "$@"
    fi
}
# DASH_IT_FLAGS: more options for VS Code (--ozone-platform=headless: no window on the screen; the tests that
# type are then skipped)
run_code ${DASH_IT_FLAGS} --new-window --user-data-dir "$tmp/user" --extensions-dir "$tmp/ext" --disable-workspace-trust \
     --skip-welcome --skip-release-notes --disable-telemetry \
     --extensionDevelopmentPath="$here" --extensionTestsPath="$here/test/integration/index.js" "$tmp/ws" >"$tmp/log" 2>&1
cat "$DASH_IT_RESULT" 2>/dev/null || { echo "FAIL no result"; tail -20 "$tmp/log"; }
grep -q '^FAIL' "$DASH_IT_RESULT" 2>/dev/null && rc=1 || rc=0
[ -f "$DASH_IT_RESULT" ] || rc=1
rm -rf "$tmp"
exit $rc
