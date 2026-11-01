# Herspers Minecraft

A macOS rebuild project based on the open-source Horizon Android 0.7.6 app supplied by the user. Targets **Apple Silicon and Intel** as separate native `.app` packages.

The supplied APK is a Rust implementation of **Minecraft Java Edition 26.3**, according to its source and resource metadata. It is not the official Bedrock engine. This project does not currently provide Bedrock protocol or world-format compatibility.

## Current status

- APK inspected without executing it; its embedded build ID matches public source commit `7301f6fdd7f470b11317276e7a11b4dc615c137a`.
- Source fetching, static inspection, and portable packaging tests run on Linux.
- Recovered engine/resource-preparer library tests: 161 passed, 3 ignored.
- macOS compilation, signing checks, app launch and gameplay are **not yet verified**. The current workspace is Linux; no playable Mac binary is claimed.

## Build on a Mac

Requires macOS 11+, Apple's Command Line Tools (`xcode-select --install`), Python 3.9+, and Rust installed using [rustup](https://rustup.rs/). The build script installs the pinned Rust 1.95.0 toolchain and target libraries, fetches checksum-locked source, builds the game and preparation tools with audio/controllers/mods, checks binary architectures and library dependencies, then signs ad hoc and packages each app.

```sh
bash scripts/build_macos.sh both
# Or: arm64 / x86_64
```

Expected first-build outputs: `dist/arm64/Herspers Minecraft.app` and `dist/x86_64/Herspers Minecraft.app`, plus architecture-specific ZIPs. Repeated builds preserve existing packages and use fresh `build.*` subdirectories. These are separate builds, not a universal executable. They use the existing Horizon desktop engine and Metal renderer. The in-game interface keeps Horizon's branding.

The manual **Build macOS apps** GitHub Actions workflow performs the same builds once this repository is hosted on GitHub. It uploads build artifacts; it does not publish a release or establish gameplay readiness. Build both versions and test on the corresponding Macs before distribution. Ad hoc signing is not Developer ID signing or Apple notarization.

## Prepare game resources and play

The app does not ship Minecraft assets or reuse the generated game tables from the APK. Install and launch your own **Minecraft Java Edition 26.3** once, have its matching server JAR available, and install **JDK 25** for resource preparation.

After building, run the app's bundled preparation command in Terminal:

```sh
"dist/arm64/Herspers Minecraft.app/Contents/Resources/prepare.command" "/absolute/path/server.jar"
```

Use `dist/x86_64` for Intel. The command accepts the Minecraft installation directory as a second argument if it differs from `~/Library/Application Support/minecraft`. It verifies the pinned game files through Horizon's preparer. Prepared resources, scratch files, and game saves live under `~/Library/Application Support/Herspers Minecraft`, outside the application and source tree.

Open the resulting app after preparation succeeds. This build uses the desktop client's own UI; it does not include the separate upstream auto-updating launcher or implement a new account manager. Online server access must be tested separately with the appropriate account/session support.

For a representative isolated world-rendering check on each Mac:

```sh
bash scripts/smoke_macos.sh "dist/arm64/Herspers Minecraft.app" \
  "$HOME/Library/Application Support/Herspers Minecraft/resources/26.3"
```

This requires 1,500 rendered world frames, generated/meshed chunks, a player and no reported error. It does not touch existing player saves.

## Inspect and test on Linux or macOS

```sh
python3 tools/inspect_apk.py /path/Horizon-Android-0.7.6-armeabi-v7a.apk
python3 tools/fetch_upstream.py
python3 -m unittest discover -s tests -v
# Include the real APK integration test when the file is available:
HORIZON_TEST_APK=/path/Horizon-Android-0.7.6-armeabi-v7a.apk python3 -m unittest discover -s tests -v
```

Dependencies and fetched source stay in ignored `.cache/`; upstream `Cargo.lock` is preserved and builds use `--locked`. A source-cache stamp records origin, not subsequent local edits. Keep an unmodified cache for reproducible builds. See [APK analysis](docs/APK-ANALYSIS.md), [source lock](upstream.lock.json), and [machine-readable audit](docs/apk-audit.json).

## Attribution

Horizon is MIT licensed, copyright Ludovic Marie and the Horizon contributors. Its license and third-party notices are retained under [licenses](licenses). The packaging step also copies applicable upstream license texts into the app. Minecraft game files have separate terms and are not covered by Horizon's MIT license. This project is unofficial and is not endorsed by Mojang, Microsoft, or Horizon's maintainers.
