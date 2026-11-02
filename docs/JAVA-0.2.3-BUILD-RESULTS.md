# Java 0.2.3 shader build results

[Windows build 41467802883](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41467802883) passed for source commit [`674665b`](https://github.com/Zeigen-ft/Herspers-Minecraft/commit/674665b5519748cda523b8b01b980ee64b52b3a5). Download **Herspers-Minecraft-Windows-x64** from its Artifacts section, sign in to GitHub if asked, and extract both ZIP layers. Previously prepared Java 26.3 resources and saves remain outside the application folder and can be reused.

The [Mac build](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41467803275) is still in progress. Its new shader package is not yet validated by a successful native build.

The application contains the pinned Horizon 0.7.6 engine with 20 checksum-locked Rust source patches, not the earlier unchanged engine. The patch fingerprint is `4e1401f7860dfd7f4de8c45147958fe6a39ea53f65e4968c8907b277789243da`; **engine-patches.json** and build metadata record its provenance. The Windows package retains the 16 MiB main stack and Tailscale host/join helpers, and includes **SHADERS.txt**.

## Verified

- Native Windows tooling, launcher, engine/preparer and shader-library checks; PE architecture/import/stack checks; packaging and executable startup/configuration smoke tests; artifact upload.
- [Shader workflow 41466026846](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41466026846) passed against the same engine patch set in source commit `990352b`. The subsequent source changes correct test temporary paths and improve CI diagnostics; they do not change the engine patches.
- [Portable tooling workflow 41468569223](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41468569223) passed.
- Locally, 132 repository checks passed with two expected skips; all 132 also passed with an aliased temporary directory matching macOS's system-path behavior. The shader/API suites passed 80 tests, with one optional legacy corpus check ignored.
- The complete renderer suite passed 829 tests with 26 ignored using the verified software Vulkan driver. Four GPU checks were then explicitly exercised within a nine-test renderer run: custom image sampling, all required author-pack pipelines, actual terrain/shadow/post rendering, and distinct hand-item IDs across frames.
- Original Complementary Reimagined and Unbound r5.5.1 passed all 12 pack/dimension/terrain combinations, including HLSL and Metal source generation and entry-point reflection. No unknown-uniform or missing-biome fallback was allowed by those checks.
- Each pack drew three original synthetic 64×48 frames. Readback found 782 terrain-depth pixels and finite, nonconstant final color output. These are generated test scenes, not Minecraft gameplay screenshots.
- Fullbright passed two lighting/profile unit tests and an explicitly run integration with the user's exact ZIP, covering pack discovery, overlay precedence and removal.

The first Mac attempt exposed test fixtures using the `/var` system alias, which intentionally strict link checks refused. Normal test roots now resolve to their physical paths; production link rejection and explicit symlink tests remain intact.

## Pack installation and limits

Read [SHADERS.md](SHADERS.md), included as **SHADERS.txt** in the application. Original Complementary ZIPs go in **Shader Packs**; the supplied Fullbright ZIP goes in **Resource Packs**. Author packs and artwork are not bundled in the application download.

BSL's official download hosts remain blocked in the running cloud environment. Its original artifact, exact version and compatibility have not been validated. Its required domains are saved in a configuration draft, which has not been applied to the runtime.

Full-world gameplay, exact visual parity, native DX12/Metal shader execution and GTX 960 performance remain untested. Armor/trim-specific item metadata, geometry/compute stages and non-2D texture types remain incomplete. See [the machine-readable validation record](SHADER-VALIDATION.json) for exact inputs and scope.
