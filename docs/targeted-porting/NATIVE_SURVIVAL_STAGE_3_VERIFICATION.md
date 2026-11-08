# Woodcutting Progression 0.1.0 — verification

**Implemented; Windows CI and delivery audit PASS, 8 November 2026. Physical
Stage 3 Windows/macOS gameplay: NOT RUN.** Natural progression, real drops/wear
and save/reload remain open. No Stage 3 Mac candidate was built.

## Candidate and source

- Repository: `Zeigen-ft/Herps-Launcher`; branch: `feature/rlcraft-native-stages`.
- Baseline: `24499167a60c104d2f24b8e70b54da3f02892d2e`.
- Implementation: `d2cb7a33ea85c63a0120e16bc766372d34cf8490`.
- **Candidate source: `9f196479726ed69e959665a9604133daf58dcde1`.**
- [Successful Windows run 42472666400](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400),
  first attempt, desktop job `128706897441`. Hosted Windows Server 2025 x64,
  Python 3.12 and Rust 1.95.0. This is not physical Windows 11 acceptance.
- [Download artifact `Herps-Launcher-0.1.0-Windows-x86_64`](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400/artifacts/13615181805).
  Sign in to GitHub and extract the outer ZIP. Metadata currently expires
  **6 February 2027**. No public release was created.

| Inner file | Bytes | SHA-256 |
| --- | ---: | --- |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 102,646,686 | `079af345af99d93d34b54bc4bb6361f849f42ddb6cd9e31adf97f90ec1c89458` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-3xds63sm.zip` | 137,923,695 | `dc09ab91d5e7dd8b745ff528653b38625525d3058f6e2072cc173c35d3b2647c` |

The installer is unsigned. Fully extract the portable ZIP and run
`Herps Launcher\Herps Launcher.exe`, keeping supporting folders. Normal use
needs no Rust/Cargo or Visual Studio. Prepare legitimate matching Minecraft 26.3
resources with JDK 25. Follow [installation and the physical Survival checklist](NATIVE_SURVIVAL_STAGE_3.md).

The outer launcher artifact is 238,681,921 bytes, SHA-256
`f20bfc23e9a0f55d717cb401424c7e6a27edaacce9a835393d40e19c580a59c1`.
It differs from the inner portable ZIP. [All checksums](WOODCUTTING_WINDOWS_SHA256SUMS.txt)
and [detailed machine-readable evidence](WOODCUTTING_WINDOWS_CI_EVIDENCE.json)
are retained. Post-build documentation updates do not change the candidate's
source or bytes; its bundled guides contain the build-time pending-verification snapshot.

## Implemented scope

The separate tag-only `.hmod` opts into an original native guard at existing
authoritative dig-start and destroy-block hooks. Survival logs require a usable
main-hand Flint Hatchet or an item in `minecraft:axes`. Bare hands, wrong tools,
empty/broken tools and an off-hand-only axe are rejected. Earlier cancellation
is respected. Other modes and non-logs retain their previous paths; permitted
breaking uses existing drops/wear. No new item, recipe, save schema, public
hook API, Java execution or bridge is introduced.

Installation starts OFF and requires explicit consent, a fresh named disposable
profile before any saves, and both unchanged earlier Flint packages. Enabling
and launch require intact enabled dependencies and the new engine metadata.
Old engines, tampering, default/saved profiles and active sessions are guarded.
Managed removal/disabling is blocked once saves exist. These guards are not a
sandbox for arbitrary user-authored mods/data packs.

## Automated results

| Cohort | Passed | Skipped | Scope |
| --- | ---: | ---: | --- |
| Local source, real pinned helper | 468 / 486 | 18 | Linux/Qt owned fixtures |
| Portable CI Linux | 371 / 486 | 115 | Real helper not staged; Qt integration unavailable |
| Portable CI Windows | 381 / 486 | 105 | Real helper not staged |
| Native Windows source, real helper | 471 / 486 | 15 | Full platform-appropriate source suite |
| Existing delivered workflows | 68 / 68 | 0 | Seven pages, Java analysis/data carry-over, backup and Chainmail safeguards |
| Delivered Flint / Gathering / Woodcutting | 7 / 7; 7 / 7; 8 / 8 | 0 | Frozen app; developer tools absent from PATH |
| Local frozen Woodcutting diagnostic | 8 / 8 | 0 | Linux diagnostic, not the Windows candidate |
| Native Chainmail / Flint probes | 10 / 10; 13 / 13 | 0 | Existing recipes/components |
| Native Gathering probe / Rust policy | 4 / 4; 12 / 12 | 0 | Existing Stage 2 behavior |
| Native Woodcutting probe / Rust policy | 8 / 8; 9 / 9 | 0 | Native tags/owned loot and progression policy |
| Installer lifecycle and native SDK | Required assertions passed | 0 | Install/reinstall/uninstall/preservation; owned mod compile/select/rollback |

Cohorts overlap; they are not unique gameplay cases. The installed workflow total
is **90**, zero errors/failures/skips. Receipts confirm seven pages, bundled helper,
preserved save/preference fixtures, overlong destination refusal before copying
and waiting for the resolved uninstaller's process tree. SDK proof confirms the
compiled marker, selection/rollback and unchanged save/source/clean binary;
`hook_execution_verified` and `gameplay_verified` remain false.

[Portable run 42472651265](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472651265)
passed both jobs. Full skip IDs/reasons are in the evidence JSON. Native Windows'
15 skips comprise 8 Mac-shell, 3 POSIX-process, 1 supplied-APK, 1 case-collision
and 2 POSIX-link fixtures; Windows junction cases run separately. Local skips
are 12 unavailable PowerShell cases, 4 Windows-junction cases, APK and AppleScript.
Portable jobs lack the real backend; Linux also skips Qt integration. The native
Windows and local full runs supply real-backend coverage. Skips are not passes.

The new native probe checks tag-only/no-code content, unchanged item components,
earlier stages not enabling the rule, native log/axe tags, hatchet/seven owned axe
fixtures and unrestricted non-logs. It evaluates unchanged owned leaf/bush stick
loot with 2,048 deterministic seeds each. Those vanilla-shaped fixtures are
independently authored; they are not legitimate prepared resource tables or a world.

## Independent delivery audit

All **seven** outer artifacts were downloaded, matched to GitHub digest/byte count
and inspected with bounded extraction. The existing candidate validator's source,
installer, legacy workflow, native content and SDK contract passed. All four
embedded `.hmod` pins match standalone packages; the earlier three packages are unchanged.

The actual shipped client is x64 PE32+, has at least a 16 MiB stack reserve,
matches its metadata hash and contains the new opt-in tag/message. Shipped source
postimages, provenance, both feature flags and MIT/GPL notices were verified.

- Upstream: `7301f6fdd7f470b11317276e7a11b4dc615c137a`.
- Patch fingerprint: `d0a7d4c2601c6f8590ff378be7281969136ffdad42c38d5a388fd53350956052`.
- Windows source tree: `a9af4d2a23fada2285b9dd5a547afad6e3036e77b9dc8c5da1d5cbf89719cda7`.
- [Separate Woodcutting artifact](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400/artifacts/13615047937):
  `herspers_rl_woodcutting-0.1.0.hmod`, 37,184 bytes, SHA-256
  `52e3586e103e4893f37f2141983a7503fa01dacb494144056f86897089abbc13`.
  Install using the candidate's dedicated Modpacks card.

## Failures, warnings and acceptance limits

No source, probe, installed workflow, lifecycle or SDK failures occurred in this
candidate run. The combined `gh` portable-run log duplicated Windows output under
the Linux job. Per-job connector logs established correct Linux counts; the audit
records this correction, with no code/build change. Actions emitted Node.js 20/24
migration and `punycode`/`url.parse` deprecation warnings without failing checks.
The auxiliary shader workflow and manual-prerelease preparation job were skipped
by existing conditions. Mac packaging/DMG and failure-cache steps were skipped
in this successful Windows-only dispatch. No signing, notarization or bit-for-bit
reproducibility is claimed: the pinned recipe and delivered checksums are recorded.

**NOT RUN:** physical Windows Stage 3 gameplay; natural early sticks/flint with
legitimate resources; knapping/fiber/crafting; log rejection/harvesting/main/off-hand;
real drops/wear/breakage/repair/enchantments; full-restart inventory/chest/block
persistence; actual-user profile preservation; combined Chainmail gameplay;
Stage 3 backup restore, crash/disk-full recovery, multiplayer; and every Stage 3
Mac build/interactive/gameplay case. Earlier user feedback remains scoped to the
earlier candidates and does not accept this one.

Earlier logo stalls and initially empty Chainmail output remain unresolved
observations. Full RLCraft/FunCraft/No Tree Punching, Forge/Fabric JAR execution,
thirst, temperature, skills, limb damage, creatures and world generation remain
unsupported/unimplemented. Java Mods Build/Test and whole-Modpack Play stay disabled.

Only the development branch is pushed. `main` remains
`b292a48c279c2b718a5395fe5558f2ff83dcea30`; no tag/release was created or existing
release altered. Work stops at this candidate, evidence and manual checklist.
No next gameplay feature has begun.
