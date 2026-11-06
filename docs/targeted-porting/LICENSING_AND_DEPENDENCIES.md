# Targeted-pack dependency and licensing evidence

Date: 2026-11-05. See the [per-entry CSV](dependency-licensing-inventory.csv) and
[hashed static inventory](funcraft-inventory.json). These contain facts and
evidence references, not bundled mod code or assets. The inspection tool does
not fetch dependencies, run Java, render HTML, or execute scripts from packs.

## FunCraft

154 CurseForge project/file pairs are declared. Their versions, dependencies and
exact-file licences cannot be inferred from those integers or unversioned HTML
labels. Sixteen additional physical JAR paths were inspected; their correspondence
to manifest entries is not authenticated. They include subdirectory loaders,
`memory_repo` libraries, coremods and shaded components. Do not call this 170
unique gameplay mods.

Embedded Maven POMs claim MIT for engine.io-client, socket.io-client and
Java-WebSocket, and Apache-2.0 for rtree-3i-lite. Those are useful scoped claims,
not complete distribution clearance; copyright notices/transitive components
still need review. The MIT text in `org/spongepowered/LICENSE.txt` belongs to the
bundled Sponge component in Phosphor; it is not evidence that all Phosphor code
is MIT. No top-level pack licence or artwork redistribution grant was found.
Do not automatically treat public downloads, a CurseForge modpack listing or a
user upload as permission to modify/republish everything inside.

Known source/location evidence from supplied metadata includes
[Nutrition](https://github.com/WesCook/Nutrition),
[CraftStudioAPI](https://github.com/Leviathan-Studio/CraftStudioAPI),
Orbis' declared Gilded Games GitLab, and project URLs in `modlist.html`.
These locations were discovered, not all checked out or certified for their
exact bundled revisions. Required MC/Forge runtime APIs and undeclared
annotation/class references remain blockers even for permissively licensed JVM
utility libraries. Byte-reference samples are not a complete dependency graph.

## Selected manual-backup feature

The archive identifies FTB Backups as project **314904**, file **2749104**, and
contains `overrides/config/ftbbackups.cfg`. Its exact JAR/version is absent.
The public [1.12 source](https://github.com/FTBTeam/FTB-Backups/tree/4e77b0390fb1f347eac3e6f341233ec8bedd035e)
at `4e77b0390fb1f347eac3e6f341233ec8bedd035e` identifies the same project in
`gradle.properties` and exposes manual backup in `command/CommandStart.java`.
It is a behavior reference, **not a verified match to the manifest file**.
No explicit licence file was present in that revision's 46-entry recursive tree;
no permission to copy or modify its Java code/assets is assumed.

The initial replacement is independently authored Python using the standard
library and existing Herspers guards, under this repository's GPL-3.0 terms.
No original Java source, artwork, configuration file or binary is incorporated.
Only the factual manual-backup behavior/pack identity informs the scope. The
feature must be described as a limited native replacement, not FTB Backups itself
or a compatible execution of its JAR. No new third-party runtime dependency is
needed. User worlds in locally generated backups are private data, never test
fixtures or CI/source uploads.

## RLCraft

The actual 2.9.3 archive is now reconstructed and hash-verified. See the
[updated report](RLCRAFT_COMPATIBILITY_REPORT.md),
[complete artifact matrix](RLCRAFT_293_MOD_MATRIX.md) and
[per-row evidence JSON](rlcraft-2.9.3-inventory.json). The manifest declares 177
mod projects and 10 resource packs; three embedded JARs are inventoried separately.

Public metadata for all 187 selected project/file pairs includes current licence
labels and source links. All 187 dependency tabs were checked; version drift is
visible, including Bountiful's modern Kotlin dependency versus legacy Forgelin
source-family evidence. These are not verified historical binary dependency
closures or licence bindings. No missing mod binaries were downloaded.

There are 36 current ARR, 15 custom and two NonCommercial project labels. Other
MIT/Apache/BSD/GPL/LGPL labels still require their applicable notices, source and
asset scope. XP From Harvest's current ARR label differs from its linked source
repository's LGPL-3.0 default licence; no favourable label is chosen silently.
The three embedded JARs contain no established licence text and are not cleared
by a parent project's terms. No original artifact is distribution-cleared.

The recommended chainmail crafting slice has MIT source at a pinned 1.12.2
revision with version 1.0, matching the selected file's declared version. Its
absent JAR is not authenticated to that source. The
[proposal](RLCRAFT_293_FIRST_GAMEPLAY_FEATURE.md) uses new native definitions,
requires applicable notices for any reused material, and copies no original
JAR/texture. It does not implement RLCraft's skill/integration rules.

The 2XD repository remains a 2.8.2 reference, excluded from all 2.9.3 evidence.
No proprietary binaries, scripts, original assets or user logs are committed.

## Reproduction and gates

Run the passive tool against the unchanged supplied FunCraft archive:

```sh
python tools/inspect_targeted_packs.py --funcraft "/path/FunCraft - FC-Release 1.1.1 - hotfix.zip" --output /tmp/funcraft-inventory
```

It requires the exact input hash and reads bounded archive members without
extracting assets into the project. Some old JARs use invalid UNIX directory
attributes; the inventory records these as anomalies while reading regular
members in memory. It does not weaken the launcher's shipped import checks.

Before any later source/asset port: establish exact content hashes, source
revision, applicable licence and notices, compatible dependency closure, permitted
modification/redistribution and required corresponding-source/replacement duties.
Unknown rights block copying. No paid services, signing, upstream-code changes,
proprietary downloads or generated modpack binaries are part of this iteration.
