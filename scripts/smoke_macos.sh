#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: smoke_macos.sh APP_PATH PREPARED_RESOURCES' >&2; exit 2; }
[[ "$(uname -s)" == Darwin ]] || { echo 'This smoke test requires a Mac and Metal.' >&2; exit 1; }
app=$(cd "$1" && pwd)
resources=$(cd "$2" && pwd)
client="$app/Contents/MacOS/horizon-client"
[[ -x "$client" ]] || { echo "Missing game binary: $client" >&2; exit 1; }
scratch=$(mktemp -d "${TMPDIR:-/tmp}/herspers-smoke.XXXXXX")
echo "Isolated test files and logs: $scratch"
export HORIZON_HOME="$scratch/game" HORIZON_LAUNCHER_HOME="$scratch/launcher"
export XDG_DATA_HOME="$scratch/data" XDG_CONFIG_HOME="$scratch/config"
export HORIZON_LAUNCHER_NO_SELF_UPDATE=1 HORIZON_NO_AUDIO=1
mkdir -p "$HORIZON_HOME" "$HORIZON_LAUNCHER_HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME"
cd "$HORIZON_HOME"
if "$client" --resources "$resources" --offscreen --world smoke --seed 1 \
  --render-distance 4 --world-frames 1500 --timeout-seconds 180 \
  --smoke-report "$scratch/smoke.json" > "$scratch/client.log" 2>&1; then
  :
else
  status=$?
  tail -40 "$scratch/client.log" >&2
  exit "$status"
fi
python3 - "$scratch/smoke.json" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    report = json.load(stream)
print(json.dumps(report, indent=2))
if (report.get("error") is not None or report.get("frames", 0) < 1500
        or report.get("generated", 0) <= 0 or not report.get("chunks")
        or not report.get("meshed_sections") or not report.get("player")):
    sys.exit("FAIL: the smoke run did not draw a complete world")
print("PASS: 1500 world frames, generated and meshed chunks, player present, no reported error")
PY
