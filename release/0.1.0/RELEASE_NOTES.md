# Herps Launcher 0.1.0 — prerelease candidate

Official home: https://github.com/Zeigen-ft/Herps-Launcher

**Prepared for the repository owner to publish manually. This file does not
create a GitHub Release or a tag.** Suggested tag: `v0.1.0`; mark the release
**prerelease**, not stable. The destination is private unless its owner changes
visibility separately; private releases are not public downloads.

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

## Verified destination build

Source: `ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb`. All three native targets passed; each delivered frozen cohort passed 68/68 with zero skips.

The DMG/installer names are release-facing copies of real CI files; internal app names and bytes were preserved.

| File | SHA-256 |
| --- | --- |
| `Herps-Launcher-0.1.0-Windows-x64-Portable.zip` | `6442f72ec57b9237abb25a7e7da3ba8d450624d5680aa7ac08e133137c8c7942` |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | `f9e7bfbb6cf1fd374b222a41bf6f2a014da6b17bc30d01d05a5320e36c625a2c` |
| `Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg` | `bb4e7a0d5077d8230498195fdc7250fd243da5885f7eb39773739ff37449b891` |
| `Herps-Launcher-0.1.0-macOS-Intel.dmg` | `8803bae8124490ab69fbdb137222cef34cd01432ff5c1005b7dd13b29894867e` |
| `LICENSES.zip` | `1cf80a4f9ee276306348647f92f114e33c9bd81d66152caa016368cc7761c3b6` |
| `RLCraft-2.9.3-Local-Inspector.zip` | `25dbf5eecd60507f353913a4e500d04b7edb5adacea11bb4500c6ab8d77ea34c` |
| `herspers_rl_chainmail-0.1.0.hmod` | `015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346` |
