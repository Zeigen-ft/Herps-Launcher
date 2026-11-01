# Supplied APK: static analysis and macOS rebuild route

Input: `Horizon-Android-0.7.6-armeabi-v7a.apk` (30,309,690 bytes).

SHA-256: `f432e75cffb7f8ca147fe325e51aa410038c8257c38a822277ed9762ba3127db`.

## Evidence

The manifest declares package `dev.horizon.android`, version 0.7.6, version code 28, minimum Android SDK 27 and target 35. Its activity extends `android.app.NativeActivity`; the other substantive Java class is an Android documents provider. The DEX is only 7,056 bytes.

Most application code is `lib/armeabi-v7a/libhorizon_android.so`, a 36,534,256-byte, stripped ELF32 ARM library. Its required libraries are `libdl.so`, `libandroid.so`, `liblog.so`, `libaaudio.so`, `libm.so` and `libc.so`. These dependencies and the Android ABI prevent direct execution on either Mac architecture. Renaming the APK, converting its ZIP container, or using Rosetta does not port this binary.

The library embeds Horizon version 0.7.6 and diagnostic source prefix `7301f6fdd7f4`, plus a link to `Vasysik/horizon-android`. The public `v0.7.6` tag resolves to `7301f6fdd7f470b11317276e7a11b4dc615c137a`, matching that prefix. This identifies a plausible exact-source rebuild route; an embedded string is not publisher authentication or proof of bit-for-bit source/binary equivalence.

The APK's MIT license credits Ludovic Marie and the Horizon contributors. Notices identify Rust's wgpu/winit stack. Source inspection confirms Metal is enabled on macOS and the desktop application uses native macOS windowing, audio and controller backends. The Android JNI, document provider, AAudio and phone lifecycle entrypoints are not used by a desktop build.

The source README explicitly identifies **Minecraft Java Edition 26.3**, and `engine-data.zip/horizon-resources.json` identifies Minecraft 26.3, schema 7, data version 5023 and client/server JAR fingerprints. The APK therefore does not establish Bedrock compatibility. Supporting Bedrock networking, worlds or behavior would be additional implementation work.

## Implementation in this repository

`upstream.lock.json` pins the full source commit and the SHA-256 of the source archive fetched over verified HTTPS. The original application source is fetched as a build dependency, not copied out of a decompiler. Its dependency lockfile and bundled wgpu/winit patches remain intact.

The build command targets `aarch64-apple-darwin` and `x86_64-apple-darwin`. The packages contain the desktop game, control utility, resource preparer and the original preparation source inputs/notices. Game resources are prepared locally from the player's own matching Java Edition install using JDK 25. APK-generated resource tables, textures, worlds, credentials and game JARs are excluded from Git and app distribution.

## Validation boundaries

Static APK inspection executed no APK or native code. The audit tool uses only Python's standard library and tests include malformed ELF headers, dependency table bounds and unsafe ZIP members.

On the Linux cloud host, the recovered source's library suites produced:

- `horizon-core`: 112 passed, 3 ignored.
- `horizon-prepare`: 49 passed, 0 ignored.

Command: `cargo +1.95.0 test --locked -p horizon-core -p horizon-prepare --lib`, with an external Cargo target directory and four build jobs.

The desktop client also passed `cargo +1.95.0 check --locked -p horizon-client --bin horizon-client --no-default-features` on Linux. This omits audio/controllers and checks types; it does not produce a playable executable or validate the macOS-specific paths.

These tests validate portable components. They do not prove macOS compilation, Metal rendering, input, audio, multiplayer or gameplay correctness. The macOS workflow and smoke script must run on Macs before calling the apps ready. Linux bundle staging is explicitly marked unverified and never substitutes for a real signed Mac artifact.
