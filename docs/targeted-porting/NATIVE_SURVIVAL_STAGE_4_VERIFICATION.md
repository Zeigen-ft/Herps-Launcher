# Plant Fiber Bandage 0.1.0 — verification

**Implemented; corrected Windows CI and independent delivery audit PASS,
8 November 2026. Physical Stage 4 Windows/macOS gameplay remains NOT RUN.**
Stage 3's separate user-reported checklist PASS applies to its earlier candidate.
Neither report establishes full modpack or macOS acceptance.

## Candidate and download

- Repository: `Zeigen-ft/Herps-Launcher`; branch: `feature/rlcraft-native-stages`.
- Baseline: `d476af25cbe38983f426073ccb023242cd372672`.
- Feature commit: `f0853a275810b46413e63e1c80fbf94460f5bc3f`.
- Initial verification wiring: `8b05b321a1306a6dfdb76e2531d29dacdfa7ef23`.
- **Corrected candidate source: `2ae01f44bdbee7847a1446db20ea1e336fb6a2c3`.**
- [Successful Windows run 42478785820](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820),
  desktop job `128725953322`. Hosted Windows Server 2025 x64, Python 3.12,
  Rust 1.95.0. This is native automated CI, not physical Windows 11 gameplay.
- [Download `Herps-Launcher-0.1.0-Windows-x86_64`](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820/artifacts/13617293283).
  Sign in to GitHub and extract the outer ZIP. Artifact metadata currently
  expires **6 February 2027**.

| Inner file | Bytes | SHA-256 |
| --- | ---: | --- |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 102,665,294 | `90e052befc716e74084c429a3b066a7624674a90a9efa81d9b73146b172572be` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-8sd_8t2u.zip` | 137,979,941 | `cc78e69b5ce87c2550b29c853fd2973021e5aafa5429a6f35172e4af9a07aef7` |

The installer is unsigned. Fully extract the portable ZIP, retain its support
folders and open `Herps Launcher\Herps Launcher.exe`. Normal play needs no
Rust/Cargo or Visual Studio. Legitimate matching Minecraft 26.3 resources and
JDK 25 preparation remain required. Use [the beginner installation/test guide](NATIVE_SURVIVAL_STAGE_4.md).

The outer launcher artifact is 238,748,950 bytes, SHA-256
`fa23b639fe69e8b619ae33f667c9f18fc40ff1f1e6ee4ff747ccf660c8d0ece3`.
It differs from the inner portable ZIP. [All hashes](BANDAGE_WINDOWS_SHA256SUMS.txt)
and [detailed evidence](BANDAGE_WINDOWS_CI_EVIDENCE.json) include all eight artifacts,
skipped cases, the failed attempt and the independent delivery audit.
Post-build reports do not change binary source or bytes; bundled offline guides
contain the build-time pending-verification snapshot and predate the Stage 3 reply.

## Implemented feature

One independently authored `.hmod` adds one item, one creative tab and one
shapeless recipe: **three Plant Fibers in separate slots + one string → one
Plant Fiber Bandage**. It fits the 2×2 inventory grid and uses unchanged Flint
Starter fiber. Hold use for 40 game ticks (normally two seconds) for ordinary
Regeneration I lasting 100 ticks (normally five seconds). Stack limit 16;
no food, use remainder, eating particles or special hand animation. Full-health
use may waste the item. Repeated use follows vanilla effect refresh semantics.

It starts OFF and installs only with explicit consent in a fresh named
disposable profile before saves. The pinned installation and intact Flint Starter
are required; enabling/play also requires the starter enabled. Saved-profile
removal/disable and missing/tampered dependencies are guarded. Old user profiles,
worlds and FunCraft backups are preserved by the existing paths and regressions.

No new engine patch, public API, save schema, dependency, Java execution/bridge,
limb-health model or original mod code/assets is introduced. The earlier four
packages remain byte-identical. Artwork references the user's prepared vanilla
paper texture; GPL notices and corresponding content are included. The engine
still contains the earlier Gathering/Woodcutting patches; Stage 4 adds none.

## Automated results

| Cohort | Passed | Skipped | Scope |
| --- | ---: | ---: | --- |
| Corrected local source, real pinned helper | 481 / 500 | 19 | Linux/Qt owned fixtures |
| Corrected portable CI Linux | 382 / 500 | 118 | Real helper absent; Qt integration unavailable |
| Corrected portable CI Windows | 395 / 500 | 105 | Real helper absent |
| Native Windows source, real helper | 485 / 500 | 15 | Full platform-appropriate source suite |
| Delivered existing workflows | 68 / 68 | 0 | Seven pages, passive Java analysis/data carry-over, backups, Chainmail guards |
| Delivered Flint / Gathering / Woodcutting / Bandage | 7 / 7; 7 / 7; 8 / 8; 8 / 8 | 0 | Frozen app, Rust tools absent from PATH |
| Corrected local frozen Bandage | 8 / 8 | 0 | Linux diagnostic, not the Windows candidate |
| Local native content parser | 2 / 2 | 0 | Reject original schema error; accept corrected definition |
| Native Chainmail / Flint | 10 / 10; 13 / 13 | 0 | Existing recipes/components |
| Native Gathering / policy | 4 / 4; 12 / 12 | 0 | Prior native behavior |
| Native Woodcutting / policy | 8 / 8; 9 / 9 | 0 | Prior native behavior |
| Native Bandage | 12 / 12 | 0 | Actual loader, recipes, consumable/effect kernels, owned fixtures |
| Installer lifecycle and SDK | Required assertions passed | 0 | Install/reinstall/uninstall and preservation; owned native compile/select/rollback |

Cohorts overlap; they are not unique gameplay cases. Delivered workflow total:
**98**, zero failures/errors/skips. Receipts verify bundled helper, seven-page
navigation, installation/start, overlong-path refusal and preserved save/preference
fixtures through reinstall/uninstall. SDK proof verifies compiled marker,
selection/rollback and unchanged save/source/clean binary; its hook-execution
and gameplay flags remain false.

[Corrected portable run 42478785971](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785971)
passed both jobs; earlier run `42477849844` also passed before the native schema
failure. The evidence retains every skipped test ID/reason for both runs, the
corrected local source suite and native Windows source suite. Windows' 15 skips
are 8 Mac-shell, 3 POSIX-process, 1 supplied-APK, 1 case-collision and 2 POSIX-link
fixtures; Windows junction tests run separately. Local skips are 12 unavailable
PowerShell, 5 Windows-junction, APK and AppleScript cases. Portable jobs omit
the real helper, and Linux Qt is unavailable there; full local/native Windows
runs supply that coverage. Skips remain skips.

The bandage native probe verifies one item/recipe/tab without code, unchanged
vanilla/starter components and earlier opt-in tags, stack/nonfood/remainder
properties, 40-tick use metadata, 100-tick level-0 guaranteed Regeneration,
all four-cell placements in both crafting grids, wrong inputs/counts and
read-only stacked matching. Actual native effect kernels emit two Heal(1.0)
actions over 100 ticks, expire, round-trip saved effect tuples, refresh without
stacking and preserve stronger effects. This is not proof of applied player
health, held-use execution, physical item consumption or an actual saved world.

## Independent artifact audit

All **eight** outer ZIPs were downloaded and matched to GitHub's byte counts
and SHA-256 digests, then inspected with bounded extraction. The existing
candidate validator's provenance, installer, legacy/frozen, native content and
SDK contract passed. All five embedded `.hmod` pins match standalone packages;
the older Chainmail, Flint, Gathering and Woodcutting package bytes are unchanged.
Delivered bandage notice/GPL license and prepared-source postimages were checked.

The actual shipped client is x64 PE32+, retains at least a 16 MiB stack reserve
and matches its build-metadata hash. Baseline opt-in tags/messages are present;
the new behavior uses the existing consumable/effect implementation.
Upstream remains `7301f6fdd7f470b11317276e7a11b4dc615c137a`.
Patch fingerprint remains `d0a7d4c2601c6f8590ff378be7281969136ffdad42c38d5a388fd53350956052`;
Windows prepared-source tree remains `a9af4d2a23fada2285b9dd5a547afad6e3036e77b9dc8c5da1d5cbf89719cda7`.

[Separate Bandage artifact](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820/artifacts/13617576944):
`herspers_rl_bandage-0.1.0.hmod`, 39,277 bytes, SHA-256
`dad328e28bc8d7d79d2002d5651af29dc77997bd3f00910c6e4021182b217ee1`.
Install through the dedicated Modpacks card in the matching candidate.

## Failures, warnings and physical acceptance

1. First native run `42477849660` at `8b05b32` failed in native content validation:
   the new definition put `minecraft:max_stack_size` inside `components`; the
   existing API requires top-level `max_stack_size`. Commit `2ae01f4` fixes that
   definition and only the new unreleased package pin. The original package
   SHA was `e54492c274559deadf83746d1160644d1d180a3ca4ddf1ca35539df947a9035c`.
   The failed evidence ZIP, artifact `13616561074`, is 23,982 bytes, SHA-256
   `8276b7aa842772966b275d56d2c4c1dd2175daa88f6af9c35e61a2d4fb34453e`.
   It was downloaded and preserved. That run did not reach installer/SDK checks.
   The fresh corrected run passes all requirements; no assertion was weakened.
2. A local rerun inside the sandbox failed the existing Windows-launcher
   occupied-port fixture with loopback PermissionDenied (30/31 native subtests
   passed). The unchanged full suite passed with the approved sandbox override:
   481 passes, 19 skips. This was an environment limitation, not a product fix.
3. Actions emitted Node.js migration and `punycode`/`url.parse` deprecation
   warnings. The small local parser emitted unused platform-patch notices;
   its registry dependencies were verified as a subset of the pinned lock.
   Mac packaging/DMG, failure-cache and manual-prerelease preparation steps were
   skipped by existing conditions in the successful Windows-only run.

**NOT RUN for Stage 4:** physical Survival crafting, actual held use and
interruption, real health/food behavior, main/off-hand, Creative/repeated use,
inventory/chest/world persistence after complete restart, actual-user profile
and backup preservation, combined-stage gameplay, crash/disk-full recovery,
multiplayer and every new Mac build/interactive/gameplay case.

The user separately confirmed **all required Stage 3 Windows checklist tests
passed** for run `42472666400`; [verbatim report and limits](WOODCUTTING_WINDOWS_USER_REPORT.json).
That is user-reported evidence for its earlier candidate, not acceptance of
Stage 4 or Codex-observed gameplay. Automated false flags retain their meaning.

Earlier logo stalls and initially empty Chainmail output remain unresolved.
Full RLCraft/FunCraft/First Aid, original Forge/Fabric JAR execution, limb health,
thirst, temperature, skills, creatures and world generation remain unsupported.
Java Mods Build/Test and whole-Modpack Play stay disabled. Builds have pinned
recipes and exact recorded hashes, not a bit-for-bit reproducibility guarantee.
No signing/notarization or stable public acceptance is claimed.

Only the development branch is pushed. Main remains
`b292a48c279c2b718a5395fe5558f2ff83dcea30`. No main merge, tag, public release
or existing-release mutation was performed. Work stops after this candidate,
evidence and physical test guide; no next gameplay stage has begun.
