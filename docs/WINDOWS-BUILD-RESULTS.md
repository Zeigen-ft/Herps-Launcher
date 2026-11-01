# Windows PC version 0.2.0 build results

[Build Windows PC app run 41304885077](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41304885077) completed successfully on 2026-11-01 for source commit `9d89cce92672d9ade8fa2fc876eaec088b998b9e`.

## Download

[Herspers-Minecraft-Windows-x64](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41304885077/artifacts/13082981412)

The outer GitHub artifact ZIP is 34,110,607 bytes. Its SHA-256, reported by GitHub, is `2119f4867c8e98038ca92b794e02aed1fdd2fa3a6a0779c452c508b35b9e5fb0`. This is GitHub's metadata digest, not an independently recomputed local download digest. Actions artifacts may expire and can require GitHub sign-in.

Extract the downloaded artifact and its inner application ZIP. Keep the complete `Herspers-Minecraft` folder together. It contains the native launcher, setup/play shortcuts, engine/control/preparation EXEs, preparation source inputs, instructions and licenses. Game resources are not included.

## Verified on Windows

The successful job `124843151364` completed:

- Tooling tests and the native Rust launcher test suite.
- Native engine library tests: **112 passed, 3 ignored, 0 failed**.
- Native resource-preparer library tests: **49 passed, 0 failed**.
- An optimized x64 MSVC build from the checksum-pinned Horizon source, preserving Cargo.lock and enabling audio, controllers and mods.
- PE32+ AMD64 executable validation and checks that imported DLLs ship with Windows. The build links the Visual C runtime statically.
- Real startup of the packaged launcher, game, control utility and preparer using their resource-free help/version/Launch API options.
- Launcher version `0.2.0`, Minecraft version `26.3`, and the client's Launch API response.
- The expected missing-resource startup failure, actionable setup instructions, creation of its diagnostic log and refusal to start a game without prepared resources.
- ZIP packaging and artifact upload.

The engine uses upstream's `fast` profile: optimization level 3, no link-time optimization, 16 code-generation units and incremental compilation. Developers can select the release profile instead. Tooling/library tests run before the long build, and the pinned engine build cache is retained for subsequent runs.

The package's metadata is written during assembly, before startup validation. The successful workflow records the later startup checks; it does not establish complete game-runtime testing. Test data is isolated in temporary folders and does not use player saves.

## Remaining validation

Full resource preparation from the player's own installed Java Edition 26.3, interactive launch, world rendering, input, audio, saving and online-server/account compatibility remain untested. This is an unsigned development build for Windows 10/11 Intel/AMD x64 PCs, not a Bedrock-compatible client or Windows-on-ARM package.

Follow [Windows installation](INSTALL-WINDOWS.md) to install JDK 25, prepare the matching game files and start the app. No Rust, Python or Visual Studio is needed to use the prebuilt package.

Mac compatibility was also rechecked successfully in [run 41300915994](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41300915994). The platform-specific test corrections do not change the Mac game runtime.
