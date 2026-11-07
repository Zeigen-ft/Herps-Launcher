# Native survival stage 1 — implementation and verification

**Implemented and verified by Windows CI; physical gameplay acceptance is open.**
This is a small RLCraft-style native starter, not a complete RLCraft rewrite.

Repository: `Zeigen-ft/Herps-Launcher`; branch `feature/rlcraft-native-stages`.
Baseline: `b292a48c279c2b718a5395fe5558f2ff83dcea30`.
Tested candidate source: **`005fe80c3e11a396fbdbc54d1ad3f9bbbac08d15`**.
Later evidence/guide-only commits do not rebuild or change the tested runtime.

## Implemented

`herspers_rl_flint-0.1.0.hmod`: four native items, five additive recipes and one
creative tab. Flint makes shards, wheat makes plant fiber, three fibers make
string, and shards/sticks/string craft a knife and hatchet. These inherit vanilla
wooden sword/axe components with 32/48 durability and no inherited repair material.
Vanilla models are referenced; no Minecraft textures or original mod code is copied.

Modpacks has a dedicated **Flint Survival Starter** card. Installation requires
explicit consent for the selected fresh disposable named profile, before saves
exist. Content starts OFF and is enabled separately on Mods. Generic import
cannot bypass this path. Saved profiles cannot disable/remove managed content;
missing, edited or disabled managed packages block their launch. Ownership,
settings, locks, rollback/removal backups and namespace checks are profile-local.

Original chainmail content remains exactly 40,002 bytes, SHA-256
`015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346`.
Existing profile/save paths, FunCraft backup operations and Java compatibility
boundaries are retained. Java Mods Build/Test and original whole-Modpack Play
remain disabled. This stage adds no JVM, Forge execution, bridge or new engine API.

## Exact automated results

[Windows native run 42383285455](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455),
job **128435256574**, completed **SUCCESS** on Windows Server 2025 x64.

| Verification | Result |
| --- | --- |
| Source suite with the real bundled-backend build | 451 collected; **436 passed, 15 platform/input skips**, zero failures |
| Actual pinned Rust content/recipe/item probe for flint | **13 cases passed**: registration/tab, model/template copy, vanilla preservation, finite tool/weapon components, hatchet mining rules, five recipes, offsets/mirrors, wrong/extra inputs and stacked-match behavior |
| Existing chainmail native engine probe | **10 cases passed** |
| Installed legacy frozen workflows | **68/68 passed, zero skips** |
| Installed flint frozen workflows | **7/7 passed, zero skips** |
| Delivered navigation | **Seven pages opened** |
| Installer lifecycle | Early overlong-path rejection, install/replacement/uninstall/reinstall and preservation of owned existing profile/save/preference fixtures passed |
| Trusted native-source mod regression | Compile, marker selection, rollback, clean binary, save fixture and source-cache preservation passed |

Both frozen cohorts ran with Cargo, rustc and rustup absent from PATH. The native
SDK regression is separate trusted build-time work; normal starter use needs no
developer Rust/Cargo tools. Native source-mod hook execution in a real world was
not claimed by the compilation/marker regression.

Additional evidence:

- [Portable CI 42383045032](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383045032)
  passed Linux and Windows. Each collected 451 tests: Linux passed 342 with 109
  skips, Windows passed 346 with 105 skips. These jobs lack the optional real
  backend fixture, so they are narrower than the native job above.
- Local full suite: **451 collected, 435 passed, 16 platform/input skips**, no
  failures. The owned loopback fixture ran with the permission needed to bind it.
- A local frozen Linux diagnostic application passed the seven new cases without
  developer tools. It is not a Linux game release or a Windows gameplay test.

The 15 native-source skips are POSIX/Mac cases on Windows, an optional missing
APK, filesystem case-collision construction and symlink fixtures covered with
Windows junction checks. Exact test IDs/reasons are in the evidence JSON. No
case was skipped in either installed frozen cohort.

## Verified downloads

Each Actions link downloads an outer ZIP. Extract it before using or hashing its
inner installer, portable ZIP or `.hmod`. Use this exact run/source, not a
same-named older release.

| Download | Artifact |
| --- | --- |
| [Windows installer and portable](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455/artifacts/13580207560) | `Herps-Launcher-0.1.0-Windows-x86_64` |
| [Native starter and its engine validation](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455/artifacts/13580237290) | `RLCraft-Native-Stage1-Flint-0.1.0-Windows-x86_64` |
| [Full native verification evidence](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455/artifacts/13579699533) | `Herps-Launcher-evidence-Windows-x86_64` |

[SHA256SUMS](NATIVE_SURVIVAL_STAGE_1_SHA256SUMS.txt) ·
[Machine-readable evidence](NATIVE_SURVIVAL_STAGE_1_EVIDENCE.json) ·
[Installation and real Survival test procedure](NATIVE_SURVIVAL_STAGE_1.md).

Four original artifact ZIP digests were independently verified, including the
separate unchanged chainmail package. The real installer/portable inner hashes
match the candidate receipt and SHA256SUMS. Both bundled `.hmod` hashes were also
checked inside the actual portable ZIP. No placeholder or simulated installer
was substituted.

| Actual inner file | SHA-256 |
| --- | --- |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | `8f078900216f380956754b25248d51924e202d2a1917c8f92a1547e7337dcae0` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-1lszx5se.zip` | `f7a5d146f913cc6ff130327ed4b982a7040313a3582eb806baf78056e62d456d` |
| `herspers_rl_flint-0.1.0.hmod` (42,887 bytes) | `919745713d5233bcd4cfee4f3da04328d3808eb06b24df966f26b054a69b81cc` |

Windows is unsigned. These are internal experimental test files, not a new public
release. Actions artifacts expire; access follows the repository's permissions.

## Failures found and retained

- Native run **42378825638** stopped at pinned engine preparation before any
  candidate was built. The engine repository had moved from
  `Vasysik/horizon-android` to `starling-client/starling`; GitHub's tar root/hash
  changed. All 4,883 members, including 4,158 regular files, were compared after
  root normalization. Paths, types, modes, sizes, link targets and file hashes
  match. The prepared tree is still
  `1f28fbaa20b871bbc5c678a1668ebc3ea63ce4191be364a0ecebb41824db6a7f`.
  Download metadata/cache identities were repaired without changing engine commit
  `7301f6fdd7f470b11317276e7a11b4dc615c137a`, source bytes or old caches. See
  [equivalence evidence](UPSTREAM_RENAME_VERIFICATION.json).
- Portable run **42378804613** failed one positive Windows assertion comparing
  expanded and shortened `RUNNER~1` paths. The assertion now compares canonical
  paths; subsequent Linux/Windows runs passed.
- Native run **42379641236** passed game compilation, the source suite and the
  existing chainmail probe, then the new probe correctly stopped on a missing
  item-model field in its synthetic resource fixture. The fixture now includes
  relevant model/name defaults; the assertion was retained and the new native
  probe passed. No gameplay package bytes changed and no installer was issued
  from that failed run.
- Local diagnostic fixes covered the expanded packaging-input contract, the
  sandbox's denied owned loopback bind, a new probe's cache-fingerprint/variable
  handling and a spec-relative path in the standalone diagnostic command.
  Successful reruns and source/cache refusal regressions are recorded in JSON.
- Compiler caches are retained after failed Windows verification to avoid
  repeatedly discarding completed compiler work. Hash/source gates stay enforced.

## Remaining acceptance and scope

**New-stage physical Windows Survival/Creative gameplay, real crafting ingredient
consumption, combat, tool wear/breakage, actual world save/load/relaunch and
multiplayer are NOT RUN. New-stage macOS Intel/ARM64 builds and all physical
gameplay are NOT RUN.** CI fixtures and menu clicks do not establish those results.

Earlier user-reported chainmail Windows Survival/Creative passes remain attached
to their original candidate. The earlier loading-logo stall and initially empty
chainmail output remain unresolved; this work does not establish their causes
or fixes. Missing-content recovery, cross-version save migration and valuable-world
installation are not accepted paths.

This stage uses crafting-grid shards and wheat fiber. Stone-click knapping,
grass-fiber harvesting, blocked tree punching, thirst/temperature, skills, limb
health, new creatures/world generation and full RLCraft compatibility remain
future work. Original Forge/Fabric JAR execution and whole-Modpack Play remain
unsupported. Major engine/API changes need approval before implementation.

Main, the source repository and existing release/tag assets were not modified by
this work. No release was published. The next checkpoint is the real disposable
Survival-world procedure before promoting this stage's gameplay claims.
