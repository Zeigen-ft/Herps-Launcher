#!/usr/bin/env bash
# Native macOS builds from the source identified in the supplied APK.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
arch=${1:-both}
case "$arch" in
  arm64) targets=(aarch64-apple-darwin) ;;
  x86_64) targets=(x86_64-apple-darwin) ;;
  both) targets=(aarch64-apple-darwin x86_64-apple-darwin) ;;
  *) echo 'Usage: build_macos.sh [arm64|x86_64|both]' >&2; exit 2 ;;
esac
[[ "$(uname -s)" == Darwin ]] || { echo 'A Mac with the Apple SDK is required; Linux cannot validate this build.' >&2; exit 1; }
command -v python3 >/dev/null
command -v cargo >/dev/null
command -v rustup >/dev/null
xcrun --sdk macosx --show-sdk-path >/dev/null
toolchain=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["rust_toolchain"])' "$root/upstream.lock.json")
export HORIZON_VERSION
HORIZON_VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["horizon_version"])' "$root/upstream.lock.json")
export MACOSX_DEPLOYMENT_TARGET=11.0
export CARGO_TARGET_DIR="$root/.cache/target"
export CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-4}
source_dir=$(python3 "$root/tools/fetch_upstream.py")
rustup toolchain install "$toolchain" --profile minimal
for target in "${targets[@]}"; do
  rustup target add --toolchain "$toolchain" "$target"
  cargo "+$toolchain" build --locked --release --manifest-path "$source_dir/Cargo.toml" \
    --target "$target" -p horizon-client -p horizon-prepare \
    --bin horizon-client --bin horizon-ctl --bin horizon-prepare --features horizon-client/mods
  case "$target" in aarch64-*) cpu=arm64 ;; *) cpu=x86_64 ;; esac
  package_output="$root/dist/$cpu"
  if [[ -e "$package_output/Herspers Minecraft.app" || -e "$package_output/herspers-minecraft-macos-$cpu.zip" ]]; then
    # Keep earlier packages intact when reusing the compiled Cargo outputs.
    package_output=$(mktemp -d "$package_output/build.XXXXXX")
  fi
  python3 "$root/tools/package_macos.py" --source "$source_dir" \
    --binaries "$CARGO_TARGET_DIR/$target/release" --arch "$cpu" --output "$package_output"
done
