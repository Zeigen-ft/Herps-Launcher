# Targeted pack porting — initial iteration results

Date: 2026-11-05, Asia/Singapore. Branch:
`feature/herps-java-compatibility`. Baseline: `3112e32`.

Inspection/plan commit: `038f9f4378def1cde7f5c37c6e62b0a1d87600ad`.
Implemented code/test commit: `018490526da46b607f6cec46d762a825e7fecc27`.
The following documentation handoff changes no tested implementation code.

**One limited feature is implemented: manual, verified backups of stopped
Herspers profile worlds, gated to the inspected FunCraft hotfix input.** This is
an independent launcher-side equivalent of one FTB Backups behavior. It does not
execute the original mod, port FunCraft gameplay, convert Forge worlds or make
either pack playable. Work stops after this slice.

## Requested deliverables and actual status

| Deliverable | Result / boundary |
| --- | --- |
| Architecture/runtime inspection | Native pinned Horizon 0.7.6 / 26.3 and launcher boundaries documented in the plan |
| [FunCraft report](FUNCRAFT_COMPATIBILITY_REPORT.md) | Actual hash-matched ZIP inspected; 154 manifest rows and 16 physical JAR rows inventoried separately |
| [RLCraft report](RLCRAFT_COMPATIBILITY_REPORT.md) | **Blocked/incomplete** for 2.9.3: upload transfer rejected; alternate repository declares 2.8.2 |
| [Prioritized plan](TARGETED_PORTING_PLAN.md) | Input/licensing gates, narrow feature architecture, later candidates, approval and acceptance boundaries |
| [Dependency/licensing inventory](LICENSING_AND_DEPENDENCIES.md) | Per-entry CSV plus hashed JSON; unknown exact versions, dependencies and rights explicitly retained |
| First feature and tests | Manual snapshot creation, checksum verification and profile-local UI; original mod compatibility unchanged |
| Installation/test instructions | [Source setup and manual backup/recovery guide](TESTING_MANUAL_BACKUP.md) |
| Actual game/world/native acceptance | **NOT RUN**, not inferred from import or sentinel bytes |

The original whole-mod FunCraft rows remain BLOCKED for legacy runtime, exact
input/dependency/source/rights evidence. No row is promoted to NATIVE COMPATIBLE
because a replacement utility exists. RLCraft's per-mod 2.9.3 matrix cannot be
completed honestly without its actual contents. The 118 entries in the linked
2.8.2 reference are not substituted for them.

## The implemented feature

`herps_launcher/modpacks/targeted_backup.py` contains independently authored
GPL-3.0 Python and standard-library ZIP/filesystem operations. It incorporates
no FTB source, mod code, original assets or configurations. No new third-party
dependency, engine extension, Java runtime or native mixin is introduced.

- Revalidate the managed import and require FunCraft's exact archive SHA-256,
  original name/version and project/file pair 314904/2749104. Renaming a pack,
  supplying another version or editing an import cannot opt in.
- Require external games/servers to be closed, reject a running managed child
  or pending session, and hold the existing launcher operation lock. This is
  stopped-profile backup, not a live-server save/flush protocol.
- Read only the current profile's `saves/` tree. Check regular files, portable
  paths, links/junctions, case collisions, depth and bounded sizes/counts.
- Stream to a new private staging ZIP outside all game folders, fingerprint
  sources before/after, and independently validate every archived file/hash.
  Publish `worlds.zip` only after verification. No prior backup is overwritten.
- On handled failures discard only the newly owned output, retain earlier
  archives and release the shared lock, including a cleanup-error path.
- Verification reads archives without extraction or restore. Extra receipt
  claims never become Java/gameplay acceptance. Integrity is not authenticity
  or proof that an arbitrary save is valid/loadable.

The Modpacks page exposes the original pack name/version, exact-target feature
availability and the two operation controls. It uses the existing worker and
idle guards. Scrolling keeps the new panel and existing analysis/export controls
reachable at 1130×790 and 900×640. Java Build/Test and Modpack Play remain disabled.
Existing Java Mods/Modpacks dependency/coverage reports remain conservative.

Differences from FTB Backups: manual only, stopped local profile worlds only;
no timer, live-server integration, in-game command, automatic pruning, extra-file
selection, whole-server backup or automatic in-place restoration. Initial limits
are 512 MiB total, 128 MiB per file, 10,000 entries and 32 source path components.
The feature does not adapt old Forge saves to the current native game format.

## Verification evidence

The [machine-readable ledger](verification-evidence.json) binds source hashes,
input/helper hashes, test IDs, skips, receipt/log hashes and the local probe hash.

| Check | Result |
| --- | --- |
| Final Linux source regressions | **376 run; 362 passed; 14 skipped; 0 failures/errors**, 23.927 seconds |
| New file/ZIP backup tests | **21 passed**, including real byte round trip, isolation, tampering, bounds, running-child/lock refusal and injected failures |
| Passive inspection tests | **5 passed**, including target hash, project-ID association, path/link rejection and recorded legacy directory anomalies |
| Modpacks Qt tests | **14 passed**, including existing 11 and 3 new backup/layout cases; offscreen automation |
| Actual supplied FunCraft + real pinned helper | Imported with production input hash guard, empty PATH, verified backup and scratch unzip; all owned sentinels/settings preserved |
| Frozen Linux PyInstaller probe | **65 passed; 0 skips/failures/errors**; persistent reload passed; cargo/rustc/rustup absent from PATH |
| Source invariants | Engine pin, core game launch/profile code, Java adapter/library, modpack service and installer construction unchanged from baseline |
| Native Windows/macOS tests for this new feature | **NOT RUN** |
| Actual resources, game launch, world creation/load and gameplay for these packs | **NOT RUN** |

The 14 final source skips are 12 PowerShell stack-repair cases, one macOS
AppleScript case and one supplied-APK case. They are listed individually in the
ledger. None of the new backup/inspection/Qt cases skipped on this Linux host.
Existing Rust wrapper tests used the installed pinned 1.95.0 toolchain and owned
process fixtures; they are not new gameplay evidence or unrelated feature work.

The actual-input smoke invoked **only** the trusted helper's `import` command
(exit 0); no Java, mod scripts, native mod code, fetch, check/carry conversion,
proprietary download or game was executed. Its save bytes are deliberately owned
test sentinels, not valid Minecraft worlds. Empty PATH demonstrates the tested
operation does not find Rust/Cargo there; source testing still uses Python.

The frozen probe confirms packaging/importability and Qt/filesystem workflows.
It is a local **Linux developer probe**, not an end-user Linux distribution,
new Windows EXE/installer, Mac DMG or native interactive certification. Its helper
binary is bundled for passive tests; it contains no real game installation.

| Recorded input/artifact | SHA-256 |
| --- | --- |
| Supplied FunCraft ZIP | `09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e` |
| Trusted Linux helper used in the probe | `41568d0cc7ebd7306f2f44fc9a646b7d80d0581b4b92fedc8d074d9706dadb8e` |
| Local Linux probe executable only | `8ed5613c56aa95bf56689e647e84cb1d3a25a67183506b3474644c78947fcd82` |

The executable hash is not a whole-bundle or publisher-trust claim. Generated
probe binaries and temporary backup ZIPs are not committed. No new native CI
build was dispatched for this iteration; the older Phase 5D native candidates
do not contain the later feature. Bit-for-bit reproducibility is not claimed.

## Failures, corrections and environment limits

- RLCraft transfer: service rejected the upload over 32 MiB. No hash/content
  inspection of that ZIP is claimed. The user-supplied alternate repository
  identifies 2.8.2/Forge 14.23.5.2838 at a pinned commit; the mismatch remains open.
- Initial FunCraft count of 151 in a progress message was corrected by parsing
  the manifest: **154** entries. Reports use the parsed value.
- Six old Maven JARs failed the production archive directory-type check during
  the first analysis attempt. A metadata-only bounded inspector records those
  invalid empty-directory attributes while reading ordinary members in memory;
  production import policy was not weakened and no affected JAR is marked supported.
- The first CSV used CRLF endings that failed the whitespace check. Output now
  explicitly uses LF; generated inventories reproduce and whitespace checks pass.
- One early backup unit case switched profiles without supplying that profile's
  managed pack import. It failed closed. The owned test setup was corrected;
  cross-profile token rejection remains covered in production behavior/tests.
- An offscreen probe used `Window.width()` despite the existing width field
  being a spin box. The probe now uses `Window.size()`; no unrelated app change.
- Offscreen inspection caught clipped new-panel text/buttons. The page now
  scrolls, with explicit reachability assertions at both tested window sizes.
- Review found the 32-component source limit initially counted the added ZIP
  `saves/` container too. Validation now handles the container separately;
  a real filesystem boundary test accepts 32 and rejects 33 source components.
- An initial source run lacked Rust on PATH and skipped two wrapper classes;
  the final run uses the existing pinned toolchain and has only the 14 genuine
  platform/input skips listed above. No tests were weakened to suppress this.
- The first frozen-harness command omitted its required `--smoke-report` flag,
  exiting before tests. Corrected invocation passed all 65 cases; no production
  CLI/parser change was made for that invocation error.
- Write, verification, publication and cleanup failures are intentionally
  injected in owned fixtures. They verify lock/output/preservation behavior;
  they are not physical disk-full, power-loss or native process-crash acceptance.

## Remaining blockers and next work

1. Obtain the actual RLCraft 2.9.3 manifest, mod list and inspectable archive
   portions with provenance. Finish its per-mod matrix rather than using 2.8.2.
2. Supply exact missing FunCraft JARs/instance metadata locally; correlate IDs,
   versions and full dependencies. Verify source/licences for each selected next
   code or asset slice. Unknown rights still block copying/redistribution.
3. Run native Windows 11 and Mac acceptance for this source feature, then real
   native-world backup → separate-profile restore → load → retained marker.
   Actual graphics/audio, resource preparation, launcher PLAY/save/relaunch,
   crash/power-loss behavior and game performance remain open. No worlds used
   here were real gameplay saves; no FPS/engine-performance claim is made.
4. Rebuild/verify native installer/DMG candidates before any claim that this later
   code is included in them. Preserve Phase 5D trust/licensing/publication gates.
5. After reviewing this first slice and the remaining evidence, select one next
   behavior. Seek explicit approval before a major engine extension/rewrite;
   a JVM bridge, universal conversion and rewriting all RLCraft are out of scope.

**Stopped after the one initial feature.** No whole-pack compatible package,
Java execution, main merge, tag, release, paid service or upstream-engine change
was introduced. Phase 5D/native gameplay acceptance remains open.
