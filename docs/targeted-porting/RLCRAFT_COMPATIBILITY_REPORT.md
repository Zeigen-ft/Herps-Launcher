# RLCraft 2.9.3 — inspection blocked; reference version mismatch

Date: 2026-11-05 (Asia/Singapore). Repository baseline: `3112e32`.
Requested input: `RLCraft 1.12.2 - Release v2.9.3.zip`.

**The requested ZIP could not be inspected.** The upload service refused its
transfer because it exceeds the executor's 32 MiB transfer limit. Its checksum,
manifest, mod count, loader version, embedded JARs, configuration, assets,
entrypoints, dependency graph and exact licences are therefore **unknown**.
The filename is a user-supplied label, not proof of archive contents.

## User-supplied alternate repository

The user supplied <https://github.com/2XD/RL-Craft>. Read-only metadata inspection
at commit `8519c53bd0bca16e2be6b76b4f38df0320a75577` found:

| Evidence | Observed reference value |
| --- | --- |
| `manifest.json` name/version | RLCraft **2.8.2** |
| Minecraft | 1.12.2 |
| Loader | Forge 14.23.5.2838 |
| CurseForge file requirements | 118 |
| Complete recursive tree | 1,951 entries; `truncated: false` |
| Contents | `mods/`, configurations, scripts, resource packs, resources and structures |
| README | Describes original RLCraft plus extra tweaks |

This is **not evidence for the requested 2.9.3 archive**. No JARs, assets or
proprietary content were fetched from that repository. Its README or any bundled
server instructions were treated as data, not commands to execute. The tree's
presence of JARs does not prove their sources or redistribution rights.

Pinned references:

- [Manifest](https://github.com/2XD/RL-Craft/blob/8519c53bd0bca16e2be6b76b4f38df0320a75577/manifest.json)
- [README](https://github.com/2XD/RL-Craft/blob/8519c53bd0bca16e2be6b76b4f38df0320a75577/README.md)
- [Tree](https://github.com/2XD/RL-Craft/tree/8519c53bd0bca16e2be6b76b4f38df0320a75577)

## Current compatibility matrix

| Target | Version / dependencies / required APIs | Classification | Effort | Evidence |
| --- | --- | --- | --- | --- |
| Requested RLCraft pack and every individual 2.9.3 mod | Unknown until the actual manifest and local files can be inspected | BLOCKED | Unestimated | Transfer rejected; reference is a different version |

An individual-mod 2.9.3 matrix cannot honestly be produced from the available
evidence. This row is a **blocking record, not a completed per-mod inventory**.
The 118 reference-version mods must not be relabelled as 2.9.3. No mod is marked
NATIVE COMPATIBLE, DATA PORTABLE or verified playable.

## Required next input and investigation

Obtain `manifest.json` and `modlist.html` from the actual ZIP, followed by a
complete path/size/SHA-256 listing and inspectable portions of its configurations,
scripts, assets and any included JARs. Smaller archive parts must each fit the
transfer limit and retain their provenance; a metadata-only copy does not prove
the original binaries. Record the original full ZIP SHA-256 on the user's PC.

Then perform the same passive inventory as FunCraft: correlate project/file IDs
to exact local JAR hashes; enumerate classes/hooks and transitive requirements;
check exact-version source/licence scope; classify each entry conservatively.
Do not download missing proprietary mod files automatically. Any world migration
from old Minecraft versions requires a separate, backed-up acceptance case.

## Decision

No RLCraft implementation, Java execution, asset conversion or installation is
enabled by this investigation. Actual game launch, world creation/load, save
preservation, crash recovery and performance tests are **NOT RUN** for RLCraft.
The [prioritized plan](TARGETED_PORTING_PLAN.md) keeps this target blocked until
its exact input becomes available.
