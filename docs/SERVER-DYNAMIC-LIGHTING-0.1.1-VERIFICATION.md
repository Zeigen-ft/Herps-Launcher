# Server Dynamic Lighting 0.1.1: custom item-tag detection correction

Status: corrected internal candidate; **CI PASS; basic Windows server lighting PASS (user-reported)**.
Broader native acceptance remains open.
No full OptiFine compatibility, public release, engine rewrite or Java execution.

## User's successful 0.1.1 retest — 17 November 2026

After confirming the 0.1.1 ZIP was present in the server world's `datapacks`
folder and receiving the restart/enable/torch test instructions, the user
reported: **“it now works”**. Record the basic server-lighting symptom as
**PASS — user-reported**, resolving their earlier “still nothing” observation
at this scope. This was the user's physical Windows server test, not a CI
simulation or an independently observed Codex gameplay session.

The brief report does not itemize hand/slot, resource-pack settings, world
position or time, every supported light item, player count, cleanup or restart
checks. Do not infer those individual passes. The user confirmed the installed
filename/version; the installed file's SHA-256 was not returned. The expected
download and checksums below identify the supplied candidate.

See the [structured user report](SERVER-DYNAMIC-LIGHTING-0.1.1-WINDOWS-USER-REPORT.json).
Two-player visibility, dropped items/offhand/tier edge cases, movement cleanup,
dimensions, disable/uninstall cleanup, save/restart/crash recovery, independent
restore and macOS gameplay remain **NOT RUN in the recorded evidence**.

## Confirmed 0.1.0 failure on the user's Windows server

The user reported the following on 17 November 2026. These are physical native
server observations, distinct from automated parsing and installer fixtures.

| Check | Actual report |
| --- | --- |
| Installer | `VERIFIED BACKUP` and `INSTALLED` reported |
| Pack discovery | `datapack list enabled`: vanilla plus the 0.1.0 ZIP |
| Activation | `#enabled has 1 [herps_dl]` |
| Main-hand torch via direct vanilla item check | `Test passed. Count: 1` |
| Same check via `#herps_dl:level14` | `Unknown item tag 'herps_dl:level14'` |
| Visible lighting | User reports “still nothing”: **FAIL** |
| Last marker score | Not supplied; do not infer a value |

The pack's source function used the rejected tag command. The native engine
silently discards errors inside functions, so “Running function” did not prove
those commands succeeded. Source inspection also shows its chat command item
registry built from base resources rather than the world's custom item tags.
The previous probe incorrectly seeded all four custom tags and therefore
missed the delivered registry mismatch. This was a verification gap.

## Correction

* Use direct vanilla item IDs for main/offhand and bounded dropped-item checks.
  Retain the same 22 items, light tiers, stronger-first order, ordinary-air-only
  placement, owned-marker cleanup and disabled default for fresh installations.
* Remove the unused custom item tags from the pack. No engine patch is needed.
* Validate the corrected commands with the pinned native parser and only
  built-in item IDs. Explicitly reject the original custom-tag command.
* Add a stopped-world upgrade path: accept only the two exact known 0.1.0 ZIP
  hashes, back up and verify the entire current world, stage the new ZIP, then
  archive the old pack outside active `datapacks` before installing the new one.
  Failed final placement attempts to restore the archived old pack. Existing
  world and inventory files are not overwritten. Modified old packs are refused.
* Preserve the existing enable score. Disable before stopping for an upgrade;
  enable explicitly afterward. Do not leave both versions active.

The legacy regression fixture is the exact audited data-only 0.1.0 pack from
source `2420d31201a7693d0c1e94984c0bf118a5f2df7e`, SHA-256
`11dff393eb1e85e5692eeb009226d04478a5f745f0ba623cabf8cfe9cda8fe8d`.
It includes AGPL notices and plain-text function definitions, not Java code.
The earlier Windows-host ZIP metadata variant is also recognized by hash.

## Automated and native acceptance

Fix source commit: `721768671ae2773c11822e209451b2197b0b691f`.
CI candidate: `eaa948738d3c54499acc58c92c152236502c54c8` on
`feature/photon-fullbright`. Its extra changes are verification documentation.
Four local package/source tests pass, including a byte-identical rebuild from
the preferred source bundled with the package. The full local regression run
executed 520 tests: 500 passed, 19 skipped, one existing launcher fixture was
blocked from binding its owned loopback port. Rerunning that module with local
loopback permission passed all four tests, including its 31 native cases.

The corrected pack contains 72 command lines and zero custom item-tag files.
Final results for **0.1.1**, independently of 0.1.0's historical CI:

| Evidence | Result |
| --- | --- |
| [Windows candidate run 44011990720](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44011990720) | **PASS**: four package/source tests; 30 Windows installation/upgrade assertions |
| Native parser in the same run | **PASS**: all 72 commands at permission level 2 with no supplied custom tags; four invalid/unsupported commands rejected, including the original failing item-tag command |
| [Regression run 44011990685](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44011990685) | **PASS**: Windows 415 passed / 105 skipped; Linux 402 passed / 118 skipped; 520 total per job |
| Independent artifact audit | **PASS**: actual GitHub outer digest, every inner-file hash, expected pack contents and byte-identical Windows/Linux bundle rebuild |

Windows fixtures cover fresh install, duplicate refusal, native-style active
world lock, junction refusal, corrupted new pack, independent backup copying,
recognized 0.1.0 upgrade, old pack archival, preserved world bytes and refusal
of modified old packs. They are automated filesystem fixtures, not real world
loading/gameplay. The native check parses commands; it does not execute a
server world. Host-only/backend-dependent regression skips remain skips.

Automatic approval review initially rejected pushing `feature/photon-fullbright` because
the user's earlier explicit branch authorization named
`feature/herps-java-compatibility`. No alternative push route was attempted.
The user subsequently explicitly approved this branch and Windows CI on
17 November 2026. The push and CI then succeeded. The approval block is resolved;
`main` remains `b292a48c279c2b718a5395fe5558f2ff83dcea30`.

## Corrected download and verified checksums

Artifact **Herps-Server-Dynamic-Lighting-0.1.1-Windows-Test**, ID **14297431150**:
[download from run 44011990720](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44011990720/artifacts/14297431150).
GitHub sign-in may be required. This is an internal test artifact, not a public
release. It expires on 15 February 2027 at 11:41:42 Singapore time (03:41:42 UTC).

| Layer | Bytes | SHA-256 |
| --- | ---: | --- |
| GitHub artifact ZIP (outer wrapper) | 44,348 | `d0f349f734ed132a343a2c5f58d75ac25f87f6dada447f5d641d8a4c6ced7aee` |
| `Herps-Server-Dynamic-Lighting-0.1.1-Windows-Test.zip` (inner bundle) | 62,324 | `8b86a75238e104deb2dcb3c6628fb2f436e541c814cee62eb6d7980719fcf892` |
| `Herps-Server-Dynamic-Lighting-0.1.1.zip` (datapack) | 17,540 | `b162ce565eddfd497bd5858dff8267a741b61dede739733351f555f24fae4844` |

Extract the outer artifact, then the inner bundle. Run the **new** bundle's
`Install-Lighting.cmd` after disabling and stopping the same disposable host.
Keep your original pre-test backup; the upgrade makes a separate fresh backup.
No launcher reinstall, Rust/Cargo or Java mod loader is required for this fix.
The bundle includes its complete preferred source, AGPL license/notices,
README and `SHA256SUMS.txt`. See the
[machine-readable CI receipt](SERVER-DYNAMIC-LIGHTING-0.1.1-CI.json).

The user now reports that basic real 0.1.1 server lighting works. Visibility
to two players, movement cleanup, dimensions, world/inventory persistence and
restart/crash recovery remain **NOT RUN in the recorded evidence**. Existing
macOS native testing limitations remain. The successful basic retest does not
accept every supported item, cleanup path or recovery scenario. The candidate's
bundled guide reflects the pre-retest evidence at build time; this report and
the separate user report record the later physical observation.

Use the [beginner upgrade instructions](SERVER-DYNAMIC-LIGHTING.md). Test with
client-only Dynamic Lights and Photon/fullbright OFF outdoors at night, so another
visual feature cannot mask the server pack's behavior. No existing releases,
main-branch changes or unrelated launcher/native gameplay changes are included.
