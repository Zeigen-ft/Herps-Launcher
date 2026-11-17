# Native Explored Terrain LOD — Windows test candidate

**Windows automated build/package checks PASS; physical graphics/gameplay acceptance OPEN.**
The experimental feature starts **Off**. This is an internal candidate, not a
public release or full Distant Horizons implementation.

## Download

[Download Herps-Launcher-0.1.0-Windows-x86_64](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44102123363/artifacts/14339754271)
from successful [Windows run 44102123363](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44102123363).
GitHub may require sign-in to download Actions artifacts. Extract this outer ZIP;
it contains both Setup and the portable ZIP. For a first test, use the portable
ZIP in a new short folder. Follow the [beginner quick start](DISTANT-TERRAIN-WINDOWS-QUICKSTART.md).

| Item | Value |
| --- | --- |
| Repository / branch | `Zeigen-ft/Herps-Launcher` / `feature/herps-distant-terrain` |
| Candidate source | `44b21a8f0b70259c5f8a4bd6b6dee5e7ee6d1139` |
| Pinned engine | `7301f6fdd7f470b11317276e7a11b4dc615c137a` |
| Build | Windows x64; optimized `fast` profile; Rust 1.95.0 |
| Automated runner | Windows Server 2025, build 26100; not a physical Windows 11 gameplay test |
| Artifact expiry reported by GitHub | 15 February 2027, 22:21 Singapore time (14:21 UTC), unless deleted earlier |
| Public release | Not created |

## Independently verified checksums

| File/layer | Name or ID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Outer GitHub artifact ZIP | `Herps-Launcher-0.1.0-Windows-x86_64` (ID 14339754271) | 241,042,089 | `0bb48007d691dcc8d30d3ffe76c9437062ebdbd5a8f4ba4ba6ab668a587896d7` |
| Setup installer | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 103,725,667 | `80e5c4e2213816a6c6cb81783113d900a2a237f931dce4b5ed8c921b8d00cc51` |
| Portable ZIP | `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-jnvbb7g6.zip` | 139,212,557 | `20fccef18bba11a6d4066de5b2a8b2f237dca05b0e38bb993eb2491c669e9d7f` |

The outer artifact and every inner installer/portable package were downloaded
and hashed independently. ZIP CRC checks passed. Do not compare the outer
wrapper's hash with the inner portable ZIP's hash. In PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 "C:\path\to\the-downloaded-file.zip"
```

Compare the entire hash against the row for that exact file. The included
`SHA256SUMS` contains the installer and portable package hashes.

## Automated evidence

| Check | Result |
| --- | --- |
| Workflow 44102123363 | **PASS**, final conclusion `success` |
| Launcher/tooling regression | 524 total: **509 passed, 15 skipped**, no failures |
| Delivered Windows workflow fixtures | **98 passed**, no failures/errors/skips; Rust/Cargo/rustup absent from PATH |
| Portable and installed launcher smoke checks | Seven pages opened; bundled helper executed |
| Installer lifecycle | Install/start/reinstall/uninstall PASS; excessive destination length rejected before copy |
| Preservation fixtures | Existing profile/preference, save sentinels, native mod data and FunCraft backup marker preserved |
| Owned native test mod | Compile/select/disable/rollback PASS; clean binary, source cache and save sentinel unchanged; hook execution NOT RUN |
| Independently downloaded packages | Outer digest, inner sizes/hashes and ZIP CRC checks PASS |
| Shipped engine sources | All **41** manifest postimages match exact verified patches; received-only modules and Off default present |
| Existing lightmap CPU probe | 3 passed; separate from graphics/gameplay |
| Existing custom game icon | Nine frames/resource metadata verified; physical visual check NOT RUN |
| Java mod execution / DH JAR | No Java mod executed; Distant Horizons JAR not bundled |

The source regression skips remain documented in its uploaded log. The earlier
[Stage 1 verification](DISTANT-TERRAIN-VERIFICATION.md) records 50 native LOD/
cache/downsampling/mesh/fade cases, 9 graphics-config and 14 UI tests, plus one
resource-dependent ignored native case. That run was source/type-check evidence;
its artifact contains logs, not an installer. This later run builds the actual
Windows packages from the same verified engine overlay:
`ef2fdf978aa5b54112c267906f6bb7f090fe8fdb94a96cf8a24ca07a60e03502`.

[Downloaded packaging/backend evidence](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44102123363/artifacts/14340262857):
795,715 bytes; SHA-256
`737558f045d9eda4ef8d539ca9fefd1ab782dd427d759a72b956bd4d01ba96c7`.
The native compile/rollback result is in `herps-native-smoke.log`. The summarized
[machine-readable receipt](DISTANT-TERRAIN-WINDOWS-CANDIDATE.json) records the
candidate packages and fixture checks. A fixture save is not a played world.

## Open and enable

1. Extract the outer download, then extract its portable ZIP into a new folder.
   Keep the old installation, resources, profiles, worlds and backups.
2. In the new launcher, use **Settings → Switch / update game installation…**
   to select the new `game\Herspers-Minecraft` folder, then validate it. A saved
   selection can otherwise keep launching the old game. Portable builds share
   the launcher's settings location; switching changes this shared selection.
3. Create a disposable profile/world and use normal legitimate resource
   preparation if required. Click **PLAY**.
4. In-game: **Options… → Horizon Settings → Advanced Graphics…**.
   Enable **Explored Terrain LOD**, leave the older **LOD Distance** Off, and
   begin with near distance 4–8 chunks, radius 64, memory 64 MiB, disk 512 MiB,
   and one worker.
5. Explore, move past near distance and look back. Only received terrain can
   appear. No server LOD installation, Java JAR or `.hmod` package is required.

See the quick start for full paths. Before using Setup to replace an existing
installation, close its game/launcher and stop a native host using the same
installation, preserving user data.

## Physical acceptance and limits

All physical candidate checks remain **NOT RUN**: visible distant terrain,
near/far transitions and z-fighting, performance, actual memory/disk behavior,
real save/inventory preservation, relaunch, independent restore and crash
recovery. macOS ARM64/Intel compilation and physical acceptance are **NOT RUN**
for this candidate. No full macOS or Windows gameplay acceptance is claimed.
Use the [full checklist](DISTANT-TERRAIN-MANUAL.md) and report each case as
PASS/FAIL/NOT RUN with run number, GPU, OS and settings. Redact private addresses,
usernames, personal paths and credentials from shared logs.

Stage 1 cannot show never-received terrain or distant changes the client did
not receive. Heightmaps approximate caves, overhangs, foliage and small
structures. Cache pressure or fast travel can leave gaps. CPU LOD budgets do
not cap whole-game RSS, textures or the GPU arena. Disk quotas apply per cache
scope; multiple worlds/dimensions consume more space.

There is no authoritative server world UUID. Reusing the same location/endpoint
and seed can leave stale visual cache data until revisited or cleared. LOD
cache data is expendable rendering data, not blocks or backups.

No Distant Horizons source was adapted. Authentication, licensing/ownership
verification and the Horizon mod system were not changed. No main merge, tag
or public release was created. Original code and existing notices are retained.
