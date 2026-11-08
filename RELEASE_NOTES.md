# Herps Launcher 0.1.0 — prerelease candidate

Official home: https://github.com/Zeigen-ft/Herps-Launcher

## Development candidate — native survival stage 4

[Plant Fiber Bandage 0.1.0](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_4.md)
adds an independently authored recipe: three Plant Fibers plus one string make
one bandage. Hold use for two seconds for five seconds of ordinary Regeneration I.
It supplies no food and uses vanilla effect refreshing; it is not First Aid's
limb model or full RLCraft compatibility. A fresh disposable profile and unchanged
Flint Starter are required. The new package starts OFF. No engine changes or
earlier package changes are introduced. Corrected Windows native run
[42478785820](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820)
passed at `2ae01f44bdbee7847a1446db20ea1e336fb6a2c3`: 485 source tests passed
with 15 recorded skips, all 98 frozen workflow tests passed, and all native content,
installer and SDK checks passed. Eight artifact hashes and delivered contents
were independently audited. The first native run caught a stack-size schema
error; it was corrected without changing the engine or previous packages.
[Download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820/artifacts/13617293283),
[checksums](docs/targeted-porting/BANDAGE_WINDOWS_SHA256SUMS.txt) and
[complete verification/failure report](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_4_VERIFICATION.md).
Physical Windows/macOS Stage 4 gameplay and new Mac builds remain **NOT RUN**.
No public release is created. The separate Stage 3 user report does not accept Stage 4.

## Development candidate — native survival stage 3

[Woodcutting Progression 0.1.0](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_3.md)
adds an optional Survival log-breaking requirement: use a main-hand Flint Hatchet
or axe. Existing drops/wear, other modes and non-log blocks keep their prior path.
Install all three stages in a fresh disposable profile before creating a world.
The new package starts OFF; no earlier package is upgraded or automatically enabled.
Windows native run [42472666400](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400)
passed at `9f196479726ed69e959665a9604133daf58dcde1`: 471 source tests passed
with 15 recorded skips, all 90 frozen workflow tests passed, and the native
content, installer and SDK regressions passed. All seven artifact digests and
delivered package/source hashes were independently checked.
[Installer/portable download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400/artifacts/13615181805),
[checksums](docs/targeted-porting/WOODCUTTING_WINDOWS_SHA256SUMS.txt) and
[verification](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_3_VERIFICATION.md) are available.
The user now reports **all required Stage 3 Windows checklist tests passed**;
[verbatim reply and scope](docs/targeted-porting/WOODCUTTING_WINDOWS_USER_REPORT.json).
Codex did not observe the testing; optional edge cases and all Stage 3 macOS
builds/gameplay remain open/NOT RUN. Automated false gameplay flags are unchanged.
This is not full RLCraft/FunCraft or No Tree Punching, and does not publish a release.

## Development candidate — native survival stage 2

[Flint Gathering 0.1.0](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_2.md) adds opt-in
stone-top flint knapping and knife-cut short-grass/fern fiber in Survival. Install
the unchanged starter first, then the add-on, in a fresh disposable profile.
Both start disabled. This candidate carries a small original native extension;
normal use needs no Rust tools. The user replied **ALL GOOD** after receiving
this candidate and guide: [overall feedback and scope](docs/targeted-porting/GATHERING_WINDOWS_USER_REPORT.json).
Individual physical cases remain unconfirmed; macOS gameplay remains **NOT RUN**.
See [verification](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_2_VERIFICATION.md).
Windows native CI run [42445241045](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045) passed;
[installer/portable download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045/artifacts/13603683988) and
[SHA-256 checksums](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_2_SHA256SUMS.txt)
are available for internal testing. Native Mac Stage 2 builds remain NOT RUN.
This development candidate does not replace or alter owner-published releases.

## Earlier migration release preparation

**Prepared for the repository owner to publish manually. This file does not
create a GitHub Release or a tag.** Suggested tag: `v0.1.0`; mark the release
**prerelease**, not stable. The owner has since made the repository public and
published releases; the earlier instructions below do not republish those assets.

## Install and play

- [Complete installation guide](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/INSTALLATION.md)
- [Quick start](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/QUICK_START.md)
- Offline `INSTALLATION.md` and `QUICK_START.md` are included as release assets
  and inside the packaged documentation.

Choose Windows x64, Mac Intel or Mac Apple Silicon. Verify each actual download
against **SHA256SUMS.txt** before opening it. The release-preparation CI bundle
contains real native-built packages, exact source/asset provenance, guides and
licence notices; extract the bundle and upload its individual files.

## Included functionality

- Seven-page launcher with game discovery, settings and logs.
- Existing default saves plus isolated named profiles and preservation guards.
- Supported native `.hmod` content and separate trusted `.hnmod` development tools.
- **Chainmail Plate and Boots 0.1.0**, bundled but OFF by default. Install only
  into an explicitly confirmed fresh disposable named profile. Enable on Mods
  before creating a world; keep enabled once saves exist.
- Four iron nuggets in a square → one plate; four plates in the boots pattern
  → vanilla chainmail boots. Vanilla nugget artwork is reused by reference.
- Existing FunCraft-hotfix manual stopped-world backup and verification utility.
- Standalone local RLCraft 2.9.3 inspector; it reads archives as untrusted data
  and does not execute mod code.

## Evidence and known issues

The source repository's run
[42129264888](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42129264888)
passed all three native targets and 68/68 frozen cases per platform. Destination
CI results, source commits and checksums are recorded separately in the prepared
release bundle and [migration report](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/docs/migration/README.md).
A successful build/offscreen test is not physical gameplay.

The user reports Windows PASS on source run
[42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443):
launch with chainmail enabled, both recipes, boots equipped with **+1 Armor**, and
plate/boots retained after fully closing/restarting Minecraft and the launcher
and reopening the same world. Crafting and persistence were confirmed in both
**Survival and Creative**. This report is not automatically transferred to each
new installer hash or to other hardware.

**Earlier loading-logo stall and initially empty crafting output remain unresolved.**
Later launches/crafting succeeded; no cause or fix has been established.

**macOS physical gameplay is NOT RUN.** Unreported Windows edge cases also remain
NOT RUN: clean resource preparation/install/upgrade, detailed input/audio/shaders,
shift/repeated consumption, chest persistence, durability, cross-profile hashes,
backup restoration, missing-content and crash/disk/lock recovery. Follow the guide
and report actual results rather than promoting CI fixtures to gameplay passes.

## Compatibility limits

- **Full RLCraft and FunCraft compatibility is NOT supported.** These are small
  native replacements, not execution of the original packs.
- **Original Forge/Fabric JAR execution is NOT supported.** No Java bridge,
  universal conversion, Java Mods Build/Test or whole-Modpack Play is implemented.
- No Reskillable Defense gate, other armor/integration recipes, Forge-save
  migration or verified missing-item recovery.
- Minecraft Java **26.3 resources must be obtained legitimately by the user**.
  Full **JDK 25** is required for preparation; no Minecraft assets or proprietary
  third-party modpack binaries are distributed here. Normal use needs no Rust/Cargo.
- Windows is **unsigned**. macOS is **ad hoc/development signed, not notarized**
  unless a specific asset has new verified evidence proving otherwise.
- Windows 11 x64 and macOS 15 Intel/ARM64 are candidate targets, not blanket
  hardware certification. Lower/newer OSes have the experimental/unsupported
  status in the installation guide. Exact minimum RAM/GPU/storage is unmeasured.
- Build inputs/provenance are pinned and hashes recorded. **Bit-for-bit
  reproducibility and stable public-release readiness are not claimed.**

## Licensing and migration

The complete verified project/history is migrated from source commit
`962a1ada14ec553c540347c539c2b9c112c0270d`. The original repository is preserved.
The destination seed commit and its MIT notice are retained separately; imported
launcher code remains GPLv3. Horizon, Qt/PySide, the recipe source and dependencies
retain their own notices. See `LICENSE`, `THIRD_PARTY_NOTICES.md` and `LICENSES.zip`.
Historical security/distribution gates remain; this migration is not a new full
native/transitive vulnerability or legal-clearance certification.

## Destination build and downloads

Destination run [42144749724](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724)
passed all three native targets and release assembly from
`ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb`. Every delivered cohort passed 68/68
with zero skips. The source suites passed 415/429 on Windows (14 platform/input
skips) and 426/429 on each Mac (3 platform/input skips). These are automated checks.

[Separate downloads and publishing instructions](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/release/0.1.0/README.md)
· [Exact prepared release notes and hashes](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/release/0.1.0/RELEASE_NOTES.md)
· [Verification report](https://github.com/Zeigen-ft/Herps-Launcher/blob/main/docs/migration/RELEASE_PREPARATION_REPORT.md).
The prepared CI notes/guides and packages remain byte-identical to their checksum
manifest; this repository page also links the final migration evidence.
