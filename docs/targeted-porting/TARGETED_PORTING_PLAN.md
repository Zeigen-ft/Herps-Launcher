# Targeted porting plan — FunCraft hotfix and RLCraft 2.9.3 only

Date: 2026-11-05 (Asia/Singapore). Baseline: `3112e32` on
`feature/herps-java-compatibility`. No universal Java compatibility project.

## Evidence and completion boundary

The [FunCraft report](FUNCRAFT_COMPATIBILITY_REPORT.md) inventories the supplied
ZIP. The [RLCraft report](RLCRAFT_COMPATIBILITY_REPORT.md) documents a blocked
transfer and a 2.8.2 reference mismatch. RLCraft 2.9.3 Phase 1/2 are **incomplete**;
there is no invented mod list or claim that the two versions are identical.

Current engine/launcher boundary:

- `upstream.lock.json` pins Horizon 0.7.6 at
  `7301f6fdd7f470b11317276e7a11b4dc615c137a`, Java Edition 26.3 resources and JDK 25
  for preparation. Old Forge 1.12.2 bytecode/APIs are absent.
- `herps_launcher/core.py` owns installation checks, named/default game folders,
  resource validation, native process launch and an exclusive operation lock.
- Java Mods reads passive metadata through the pinned `horizon-port-pack` and
  conservative Python preflight. That preflight primarily understands modern
  Fabric/Forge/NeoForge manifests, not old `mcmod.info` plus annotation/coremod
  semantics. An old empty dependency list is not a proved empty dependency set.
- Modpacks retains local manifests, resolves files with identity evidence and
  permits a conservative data subset. It does not launch whole packs. Nested
  legacy libraries and `memory_repo` are not a validated Forge installation.
- Existing WASM client APIs offer game-read/HUD/input/recipes/UI; server APIs and
  registry data are bounded. They do not implement Forge events, JVM class loading,
  LaunchWrapper/ASM, mixins, capabilities or arbitrary 1.12.2 world semantics.
- A data format that can be parsed is not gameplay compatibility. Runtime
  callbacks, real rendering and real save/load still require native evidence.

## Classification contract

| Category | Required evidence |
| --- | --- |
| NATIVE COMPATIBLE | Existing Herspers implementation runs unchanged; required dependencies, licensing and genuine gameplay behavior verified |
| DATA PORTABLE | Specific data subset can be adapted with known semantics, permitted rights, output validation and explicit remaining limits |
| SOURCE PORT REQUIRED | Exact source/rights and required supported APIs established; a bounded rewrite is needed |
| ENGINE EXTENSION REQUIRED | A selected behavior requires an identified absent engine API or system; no fake adapter |
| BLOCKED | Missing exact inputs/source/rights, incompatible runtime or insufficient evidence prevents a current port |

The initial whole-mod matrix is deliberately BLOCKED where those prerequisites
are absent. A possible feature-level replacement does not promote the entire
original Java mod or pack. Technical candidates and legal blockers are recorded
separately in the inventory.

## Priority 0 — finish input and licence evidence

1. Obtain the actual RLCraft 2.9.3 manifest and inspectable archive contents.
2. Resolve FunCraft's 154 project/file pairs against the user's exact local
   installation metadata and hashes. Do not infer versions from project names
   or pair the HTML list with manifest entries by order.
3. Audit the 16 embedded JARs, their libraries and six anomalous Maven directory
   attribute sets without relaxing shipped archive safety checks.
4. Inspect exact-version source and licence terms for each selected behavior.
   Asset rights need separate confirmation; a bundled library licence does not
   cover its containing mod or Mojang textures. No binaries/assets are committed.

## Priority 1 — first bounded implementation

Status: implemented as a launcher-side manual stopped-world backup and checksum
verification, with fixture/source/frozen-Linux evidence. See the
[implementation report](INITIAL_IMPLEMENTATION_REPORT.md) and
[installation/test guide](TESTING_MANUAL_BACKUP.md). Native interactive/world-load
acceptance is still open. The design/acceptance contract below remains its scope.

Selected candidate: **manual world backup**, a feature of FTB Backups in FunCraft
(CurseForge project 314904, file 2749104). The archive's `ftbbackups.cfg` enables
backups; the public 1.12 source exposes a manual start operation. This is a small
launcher-side equivalent, independent of Forge/JVM and all original code/assets.

Build one complete operation that snapshots a stopped, disposable profile's
`saves/` tree to a new ZIP, verifies every file hash and exposes the receipt to
the user. Never overwrite a save, automatically delete old backups, or modify
the official/prepared game tree. An empty save folder must not produce a fake
successful backup. Require the user to close external games/servers too.

Keep this operation gated to the exact inspected FunCraft input, using its
SHA-256 plus the required FTB manifest identity. Its availability must not depend
on a Java compatibility status and must not change one. Hold the existing
launcher operation lock during copying, reject linked/unsafe trees, bound size
and entry count, detect source changes, verify the finished archive, and discard
only the new failed output on cancellation/error. Existing profiles/backups
remain intact. Run work in the existing UI worker; no launch/install buttons
become enabled for the whole pack.

Acceptance for this slice: real filesystem round-trip into a separate scratch
folder; matching hashes including binary/Unicode filenames and empty folders;
profile/default data unchanged; running-game/lock rejection; wrong pack, tampered
snapshot, traversal/link, disk/write/verification failures leave no success
receipt and release locks. UI must show honest availability and results while
Modpack Play and Java Build/Test stay disabled. Native Windows/macOS interactive
testing and real world loading remain separate NOT RUN cases when unavailable.

Differences from FTB Backups: manual, stopped-profile worlds only; no in-game
command, live-server coordination, timer, retention policy, external files or
server-wide backup. No claim to implement the complete original mod.

## Priority 2 — next feature candidates, not implementation approval

After exact source/API/licence confirmation, evaluate one of:

- Small client information overlay using existing game-read/HUD APIs, with a
  precise limited contract rather than whole Hwyla/Wawla/JEI equivalence.
- A single recipe whose item IDs exist in 26.3 and whose independent adaptation
  rights are clear. FunCraft's CraftTweaker script mostly references absent
  AE2/Actually Additions/Botania/Forge fluids and ore-dictionary entries, so it
  cannot be copied and labelled functional.
- Explicit, licence-approved resource-pack subsets with old path/metadata
  conversion. Missing licences currently block copying the shipped artwork.

Prioritize by independently testable behavior, rights, stable existing APIs and
small save impact. Nutrition, custom machines, dimensions, mob AI, lighting
rewrites and arbitrary Forge hooks require substantially larger work. Present
the exact engine change and migration/test cost for approval before proceeding.

## Later launcher integration and acceptance

For each exact pack identity, expose original version, detected/unknown mods,
dependency evidence, feature-level progress, rights blockers and any genuinely
available native package. Keep original-mod compatibility, replacement-feature
verification and gameplay acceptance separate. Unknown or edited receipts must
fail closed. Java Mods/Modpacks remain compatible with Phase 5D.

Use disposable profiles/worlds. Test real runtime APIs separately from fixture
logic: resources → launch → rendered behavior → world save/load → relaunch →
crash recovery → performance → disable/uninstall/rollback. Preserve evidence and
differences. No target is fully accepted while required native gameplay tests
are missing. No main merge, tag, release or redistributed proprietary files.

Stop after the first feature and its tests/report. Large engine rewrites, a JVM
bridge, universal compatibility and rewriting all of RLCraft are outside this
iteration.
