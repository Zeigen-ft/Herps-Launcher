# Server Dynamic Lighting 0.1.1: custom item-tag detection correction

Status: corrected internal candidate; **0.1.1 physical gameplay retest NOT RUN**.
No full OptiFine compatibility, public release, engine rewrite or Java execution.

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

Fix source commit: `721768671ae2773c11822e209451b2197b0b691f` (local).
Four local package/source tests pass, including a byte-identical rebuild from
the preferred source bundled with the package. The full local regression run
executed 520 tests: 500 passed, 19 skipped, one existing launcher fixture was
blocked from binding its owned loopback port. Rerunning that module with local
loopback permission passed all four tests, including its 31 native cases.

The corrected pack contains 72 command lines and zero custom item-tag files.
Its native parser check and real Windows installation/upgrade fixtures are
**NOT RUN for 0.1.1 yet**, pending the feature-branch CI run. These must not be
inferred from 0.1.0's earlier results. No corrected GitHub artifact is available
at this point.

Automatic approval review rejected pushing `feature/photon-fullbright` because
the user's earlier explicit branch authorization named
`feature/herps-java-compatibility`. No alternative push route was attempted.
The reviewable local fix and report are retained; explicit approval of the
current branch is needed before publishing the change to GitHub and running CI.
`main` remains `b292a48c279c2b718a5395fe5558f2ff83dcea30`.

The local (not Windows-CI-accepted) 0.1.1 Windows bundle SHA-256 is
`8b86a75238e104deb2dcb3c6628fb2f436e541c814cee62eb6d7980719fcf892`;
the inner pack is `b162ce565eddfd497bd5858dff8267a741b61dede739733351f555f24fae4844`.

Real 0.1.1 light placement, visibility to two players, movement cleanup,
dimensions, world/inventory persistence and restart/crash recovery remain
**NOT RUN** until the corrected package is physically retested. Existing macOS
native testing limitations remain. Source-level correction of one confirmed
failure does not establish that every subsequent lighting step works.

Use the [beginner upgrade instructions](SERVER-DYNAMIC-LIGHTING.md). Test with
client-only Dynamic Lights and Photon/fullbright OFF in a dark area, so another
visual feature cannot mask the server pack's behavior. No existing releases,
main-branch changes or unrelated launcher/native gameplay changes are included.
