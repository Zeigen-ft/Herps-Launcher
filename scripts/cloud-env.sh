# Source this file in the Linux cloud workspace; not needed on a Mac.
export RUSTUP_HOME=/workspace/.rustup
export CARGO_HOME=/workspace/.cargo
export PATH="$CARGO_HOME/bin:$PATH"
export CARGO_TARGET_DIR=/workspace/.horizon-target
export CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-4}
