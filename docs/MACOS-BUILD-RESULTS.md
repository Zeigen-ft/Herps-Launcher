# Native macOS build results

[Build macOS apps run 41295959995](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41295959995) completed successfully on 2026-11-01 for commit `861a9c258c754745d939a2d29e2885016ff62822`. The independent Portable tooling checks run `41295959907` also succeeded.

| Target | Job | Artifact | GitHub artifact archive size |
| --- | --- | --- | --- |
| Apple Silicon / arm64 | `124816750588` | `13079675808` | 31,120,747 bytes |
| Intel / x86_64 | `124816750863` | `13079341512` | 34,721,541 bytes |

Both jobs successfully completed the tooling tests, native release build, architecture verification, system-library checks, ad hoc signing, signature verification and artifact upload. The build script uses the checksum-pinned Horizon source, preserved Cargo.lock, audio/controllers/mods, native game/control/preparation binaries and a native C app entrypoint. The packaging invocation did not use `--stage-only`.

The authenticated GitHub API reports the following SHA-256 digests for the outer artifact ZIPs:

- arm64: `1f44a919d9a9c0534ce9a916d08dce29633ab7be3c02e978f8afa85a57b4db8f`
- x86_64: `20e43f736a8e4b0b4cf929365e22d609f4ee4b39259b7191cc15c935e4df14d6`

These digests are recorded from GitHub metadata. Downloading the actual artifact bytes into the Linux environment was denied at `productionresultssa30.blob.core.windows.net`, so the digests were not independently recomputed here. Raw job logs were unavailable at `results-receiver.actions.githubusercontent.com`. Job/step completion and artifact metadata were retrieved successfully through GitHub's API.

## Downloads

- [Apple Silicon artifact](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41295959995/artifacts/13079675808)
- [Intel artifact](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41295959995/artifacts/13079341512)

GitHub sign-in is required. Extract the downloaded artifact, then its inner application ZIP. It contains `Herspers Minecraft.app`. Actions artifacts can expire; these are build artifacts, not a permanent GitHub Release.

## What remains untested

The workflow did not run the app, prepare game resources, or execute the 1,500-world-frame smoke test. No gameplay readiness, sound/input correctness, online-server compatibility or Bedrock compatibility is claimed. Ad hoc signing is not Developer ID signing or Apple notarization.

Before playing, follow README.md to prepare resources using JDK 25 and the player's installed Minecraft Java Edition 26.3 plus matching server JAR. Then run `scripts/smoke_macos.sh` on each supported architecture and test the app interactively.
