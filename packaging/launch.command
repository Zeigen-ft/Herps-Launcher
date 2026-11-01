#!/bin/bash
set -euo pipefail

if [ "$(uname -s)" != Darwin ]; then
    echo "Herspers Minecraft requires macOS." >&2
    exit 1
fi
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
bundle_resources="$here"
binaries="$here/../MacOS"
support="$HOME/Library/Application Support/Herspers Minecraft"
resources="$support/resources/26.3"
game="$support/game"
mkdir -p "$game" "$support/logs"
export HORIZON_HOME="$support"
export HORIZON_LAUNCHER_NO_SELF_UPDATE=1

if ! "$binaries/horizon-prepare" --check --root "$bundle_resources/preparation" --output "$resources" > "$support/logs/resources-check.log" 2>&1; then
    /usr/bin/osascript - "$bundle_resources/prepare.command" <<'APPLESCRIPT'
on run argv
    display dialog "Game resources need preparation from your installed Minecraft Java Edition 26.3. Open this preparation script in Terminal first:" & return & return & item 1 of argv with title "Herspers Minecraft" buttons {"OK"} default button "OK"
end run
APPLESCRIPT
    exit 1
fi

cd "$game"
exec "$binaries/horizon-client" --resources "$resources" --game-dir "$game" "$@" >> "$support/logs/launcher.log" 2>&1
