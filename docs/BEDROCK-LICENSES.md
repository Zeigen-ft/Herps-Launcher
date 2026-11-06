# Bedrock package licenses and provenance

Herspers Bedrock 0.3.0 distributes an independent Rust launcher alongside an unchanged Cinnabar Windows runtime. The launcher starts the engine as a separate process; it does not link GPL launcher code into Cinnabar or relicense Cinnabar's code.

| Component | License and source |
| --- | --- |
| Independent Herspers launcher and project packaging code | GPLv3, under this repository's root [LICENSE](https://github.com/Zeigen-ft/Herspers-Minecraft/blob/main/LICENSE). [Launcher source](https://github.com/Zeigen-ft/Herspers-Minecraft/blob/main/packaging/launcher_bedrock.rs). |
| Cinnabar's own client/helper code | [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/), with upstream notices retained. [Upstream source](https://github.com/cinnabar-mc/cinnabar/tree/f64924fbb27004a1f785a2c131de9531fbcd252a). |
| Cinnabar's third-party libraries and supplied files | Their original licenses apply. See upstream `THIRD_PARTY_NOTICES.md` and the licenses supplied inside the engine payload. |
| Mojang resource files and any downloaded official BDS | Separate Minecraft/Mojang/Microsoft terms; not covered by the launcher's GPL or Cinnabar's PolyForm license. These downloads occur through the client's consent/setup flow. |

The root GPLv3 license is **not a license for the entire combined download**. Cinnabar cannot simply be relabeled GPLv3, and its noncommercial condition still applies when it is redistributed with this launcher. Preserve its license and required notices. Personal, noncommercial uses described in the PolyForm terms are permitted; commercial use needs permission or a suitable license from Cinnabar's licensors.

## Pinned runtime

- Engine: **Cinnabar v0.1.31**.
- Source commit: `f64924fbb27004a1f785a2c131de9531fbcd252a`.
- Upstream Windows distribution: `Cinnabar-x64.msi`, from the [v0.1.31 release](https://github.com/cinnabar-mc/cinnabar/releases/tag/v0.1.31).
- MSI SHA-256: `584f4fa8851571abffce24bbeacadbd5cdbe35053a93b59e8d8673c7170381cb`.
- Game target: **Bedrock 1.26.60**, wire protocol **2225**; native BDS target **1.26.60.6**.
- Resource snapshot fixed by upstream: **`v1.26.60.30-preview`**, `bedrock-samples-v1.26.60.30-preview-full.zip`.

The build verifies the pinned MSI before extracting its engine payload. Original engine executable names, branding, license text, notices and supplied helper files are retained. The package includes a file-level SHA-256 manifest; the Herspers launcher checks it before starting the engine. Neither hash checking nor extraction proves gameplay compatibility by itself.

## Language and runtime boundary

Cinnabar's native client/rendering code is Rust. Its networking/authentication helper and bundled Dragonfly local server are Go. Official BDS, when selected and downloaded by the user, is a separate upstream runtime. No official Minecraft client executable or Android APK is being translated into Rust or run by this launcher.

No Rust or Go installation is required for the prebuilt download. No Java/JDK or manual `server.jar` is required by this Bedrock package. The earlier Herspers Java Edition packages are separate products with separate setup requirements.

## Notices inside the ZIP

The package retains:

- Root `LICENSE` for the independent Herspers project code.
- Cinnabar's original `LICENSE` and `THIRD_PARTY_NOTICES.md` under `licenses/cinnabar`.
- Upstream license/notice files supplied with `engine/resources`.
- The Bedrock installation and mixed-license summaries supplied by this project.

Minecraft, Mojang and Microsoft names belong to their respective owners. Herspers Bedrock and Cinnabar are unofficial projects and are not endorsed by Mojang or Microsoft. Retaining upstream branding identifies the software being run; it does not imply Cinnabar's maintainers endorse this package.
