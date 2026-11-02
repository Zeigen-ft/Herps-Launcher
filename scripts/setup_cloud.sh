#!/usr/bin/env bash
# Prepare portable development checks. Native Mac app builds require macOS.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
[[ "$(uname -s)" == Linux ]] || { echo 'Use build_macos.sh on a Mac.' >&2; exit 1; }
source "$root/scripts/cloud-env.sh"
mkdir -p /workspace/.setup
if [[ ! -x "$CARGO_HOME/bin/rustup" ]]; then
  curl --fail --location --max-time 60 https://sh.rustup.rs -o /workspace/.setup/rustup-init.sh
  sh /workspace/.setup/rustup-init.sh -y --no-modify-path --default-toolchain 1.95.0 --profile minimal
fi
rustup toolchain install 1.95.0 --profile minimal
source_dir=$(python3 "$root/tools/prepare_upstream.py")
cd "$root"
python3 -m unittest discover -s tests -v
for script in scripts/*.sh packaging/*.command; do bash -n "$script"; done
cd "$source_dir"
cargo +1.95.0 test --locked -p horizon-core -p horizon-prepare --lib
cargo +1.95.0 check --locked -p horizon-client --bin horizon-client --no-default-features
