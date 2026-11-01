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

if "$binaries/horizon-prepare" --check --root "$bundle_resources/preparation" --output "$resources" > "$support/logs/resources-check.log" 2>&1; then
    :
else
    check_status=$?
    echo "Herspers Minecraft: resource check failed (exit $check_status). The game has not started." >&2
    cat "$support/logs/resources-check.log" >&2
    echo "Full resource-check log: $support/logs/resources-check.log" >&2
    if choice=$(/usr/bin/osascript - "$support/logs/resources-check.log" <<'APPLESCRIPT'
on run argv
    set messageText to "This Mac app uses Minecraft Java Edition 26.3. Its game-resource check did not pass." & return & return & "If resources have not been prepared, choose Prepare resources. Preparation requires JDK 25 and your matching Minecraft game files." & return & return & "Choose Show log to see the actual error." & return & return & item 1 of argv
    return button returned of (display dialog messageText with title "Herspers Minecraft setup" buttons {"Quit", "Show log", "Prepare resources"} default button "Prepare resources" cancel button "Quit")
end run
APPLESCRIPT
    ); then
        case "$choice" in
            "Prepare resources")
                if /usr/bin/open -a Terminal "$bundle_resources/prepare.command"; then
                    echo "Preparation opened in Terminal. Open Herspers Minecraft again after preparation succeeds."
                else
                    echo "Could not open preparation. Run this script in Terminal: $bundle_resources/prepare.command" >&2
                fi
                ;;
            "Show log") /usr/bin/open -a TextEdit "$support/logs/resources-check.log" || true ;;
        esac
    fi
    exit "$check_status"
fi

cd "$game"
if "$binaries/horizon-client" --resources "$resources" --game-dir "$game" "$@" >> "$support/logs/launcher.log" 2>&1; then
    exit 0
else
    game_status=$?
    echo "Herspers Minecraft: the game exited with code $game_status." >&2
    /usr/bin/tail -n 30 "$support/logs/launcher.log" >&2
    echo "Full game log: $support/logs/launcher.log" >&2
    if choice=$(/usr/bin/osascript - "$support/logs/launcher.log" <<'APPLESCRIPT'
on run argv
    return button returned of (display dialog "The game stopped with an error. Choose Show log to see its startup output." & return & return & item 1 of argv with title "Herspers Minecraft" buttons {"Close", "Show log"} default button "Show log")
end run
APPLESCRIPT
    ); then
        if [ "$choice" = "Show log" ]; then
            /usr/bin/open -a TextEdit "$support/logs/launcher.log" || true
        fi
    fi
    exit "$game_status"
fi
