# Explored Terrain LOD — corrected Windows test candidate

**Automated build/package checks PASS; physical visual/gameplay retest NOT RUN.**
This is an internal, experimental candidate. It starts Off and is not a public release.

[Download the corrected Windows x64 candidate](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44171833781/artifacts/14370852822)
from successful [run 44171833781](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44171833781).
Sign in to GitHub if needed. Extract the outer download, then use the portable
ZIP inside it in a new empty folder. The [beginner guide](DISTANT-TERRAIN-WINDOWS-QUICKSTART.md)
includes installation selection and exact graphics menu labels.

| Identity | Value |
| --- | --- |
| Branch | `feature/herps-distant-terrain` |
| Candidate source | `a95e004746abe0ebdbe404a0becb1fa3e803a7b0` |
| Pinned engine | `7301f6fdd7f470b11317276e7a11b4dc615c137a` |
| Native build | Windows x64, Rust 1.95.0, optimized `fast` profile |
| Automated runner | `Windows-2025Server-10.0.26100-SP0`; not physical Windows 11 gameplay |
| Reported artifact expiry | 16 February 2027, 04:40 Singapore time, unless deleted earlier |

## Independently audited downloads

| Layer | Name or ID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Outer GitHub artifact ZIP | `Herps-Launcher-0.1.0-Windows-x86_64` (ID 14370852822) | 241,045,484 | `f350dfc5c1c36a4bc9c3cd22f209936486e0755817b0eb2b6c06d5f84395147d` |
| Setup installer | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 103,719,620 | `e1a5e4171c5841115be4da81b357d40aaa9a7a8f31439d784992f540bdfdfa37` |
| Portable ZIP | `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-2dckr9gh.zip` | 139,224,054 | `d960d40234ac2f45566e3ae77030c9b80906cde00d0e59210f03ac027abd53d9` |

The outer digest, ZIP CRCs, inner package sizes and every package SHA-256
were independently checked. All **41** shipped engine source postimages match
the exact manifest. The observed-only mesher is included, and the feature's
Off default is preserved. The original DH JAR/Photon archive is not bundled.
Do not compare the outer wrapper's hash with the inner portable ZIP's hash.

```powershell
Get-FileHash -Algorithm SHA256 "C:\path\to\the-downloaded-file.zip"
```

Use the row for that exact file. Inner hashes are also in `SHA256SUMS`.

## What changed and passed

The [edge-wall fix and retest checklist](DISTANT-TERRAIN-EDGE-FIX.md) explain the
reproducible defect: missing observed terrain was treated as air beside
world-floor-extruded heightmaps. The observed-only path now omits artificial
bottom caps and unknown-edge side curtains, keeps known cliffs, and limits
near-boundary skirts to 1–16 blocks. Legacy voxel LOD remains separate. No
cache migration, save edits or server changes are required.

| Automated evidence | Result |
| --- | --- |
| Corrected candidate workflow | PASS, final `success` |
| Candidate source/tooling suite | 509 passed / 15 skipped (524 total), no failures |
| Delivered workflow fixtures without Rust/Cargo/rustup on PATH | 98 passed; no failures/errors/skips |
| Portable/installed/reinstalled launcher smoke | Seven pages and bundled helper checked |
| Windows lifecycle | Install/start/reinstall/uninstall and excessive-path rejection PASS |
| Data-preservation fixtures | Profile/preferences, save sentinels, native mod data and FunCraft backup marker preserved |
| Owned native mod rebuild/selection/rollback | PASS; save sentinel, source and clean binary unchanged; hook execution NOT RUN |
| Existing fullbright CPU probe | 3 passed; not a physical graphics test |
| Existing custom icon | Nine resource frames/metadata verified; physical appearance NOT RUN |
| Independent download/source audit | Outer/inner hashes, CRCs, all 41 manifest postimages PASS |

Separate [native CI evidence](DISTANT-TERRAIN-EDGE-CI.json) records **56** LOD/
cache/mesh/fade tests, **9** graphics-config and **14** UI tests, and the full
client integration type check. One resource-dependent native test remains
ignored. Separate tooling jobs passed Windows 419/105 skipped and Linux
406/118 skipped (524 total each). Candidate/platform skips are retained in
uploaded logs. None of these results is real gameplay or visual acceptance.

[Packaging/backend evidence](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44171833781/artifacts/14371002590):
780,357 bytes; SHA-256 `bbfc23b5ee3725b2d6e57ab12d98375123d4a08110387e4c5f0b9fc9a2b855ef`.
The [machine-readable package receipt](DISTANT-TERRAIN-EDGE-WINDOWS-CANDIDATE.json)
records package hashes and preservation fixtures. Native rollback evidence is
in `herps-native-smoke.log`. A sentinel `level.dat` is not a played world.

## Physical retest and limitations

The user reported poor visuals and supplied screenshots after the initial
candidate delivery. The exact previous run/settings were not reconfirmed.
This correction fixes a reproducible mechanism consistent with those images;
it does **not** establish that every reported artifact or performance issue is
resolved. Corrected-candidate graphics, frame rate, real save/relaunch/recovery
and macOS ARM64/Intel acceptance are **NOT RUN**.

Retest in a disposable profile/world: older LOD Distance Off, Explored Terrain
LOD On, near 4–8, radius 64. Explore a coast, move beyond near range and look
back. Check tall water/ground curtains separately from missing coverage, real
cliffs, seams/flicker, performance and reopen/inventory preservation. Record
PASS/FAIL/NOT RUN with candidate/run, OS/GPU and settings; redact private log data.

Terrain never received by the client remains absent. Strict coarse-cell
coverage can leave rectangular gaps; caves, overhangs, foliage and small
structures remain approximations. CPU LOD budgets do not cap whole-game/GPU
memory. Disk quotas apply per scope, and same-endpoint/same-seed world resets
can leave stale visual cache until revisited/cleared. LOD cache is rendering
data, not a save or backup. Existing caches need not be deleted for this fix.

No DH source/JAR execution, server streaming, auth/licensing/ownership changes,
Horizon mod-system implementation changes, main merge, tag or public release
were introduced. macOS builds for this correction were not requested or run.
