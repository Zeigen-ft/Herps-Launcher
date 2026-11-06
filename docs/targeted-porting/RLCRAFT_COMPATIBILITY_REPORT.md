# RLCraft 2.9.3 — verified export and static compatibility assessment

Date: 2026-11-05 UTC. Branch: `feature/herps-java-compatibility`.
Investigation baseline: `a16756fa226c1f196b5e62487408f893035ccbef`.

**The actual user-provided 2.9.3 archive is reconstructed and verified.**
The complete static matrix covers every manifest project/file pair and embedded
JAR. **No original mod or complete modpack is verified playable in Herspers.**
Missing historical binaries, runtime semantics, source/licence binding and
gameplay evidence remain explicit.

- [Complete artifact matrix](RLCRAFT_293_MOD_MATRIX.md)
- [190-row CSV](rlcraft-2.9.3-compatibility-matrix.csv)
- [Hashes, provenance, dependencies, licences and per-row evidence](rlcraft-2.9.3-inventory.json)
- [First gameplay slice and acceptance proposal](RLCRAFT_293_FIRST_GAMEPLAY_FEATURE.md)

## Verified identity and counts

| Fact | Verified value |
| --- | --- |
| Reported original filename | `RLCraft 1.12.2 - Release v2.9.3.zip` |
| Original ZIP SHA-256 | `5caa25d31f47f4ac69846e4faa741811baa9239804747769f6d54f7b1bbf1291` |
| Original compressed bytes | 51,324,367 |
| Entries | **3,723**: 3,383 regular files and 340 directories |
| Uncompressed regular-file bytes | 66,958,133 |
| Declared name / version | **RLCraft / 2.9.3** |
| Minecraft / primary loader | **1.12.2 / Forge 14.23.5.2860** |
| Manifest project/file requirements | **187**, all marked required |
| Manifest project categories | **177 mod projects + 10 resource packs** |
| Additional embedded gameplay mod | **Antique Cities**, `mcmod.info` version 1.2.1 |
| Additional embedded auxiliary JARs | **2**: mcjtytools and llibrary-core |
| Physical JAR paths / class entries | **3 / 82** |
| HTML project labels | **188**; TickProfiler is absent from the manifest |
| Native-compatible / verified data-portable / gameplay-verified artifacts | **0 / 0 / 0** |

Thus **177 manifest mod projects plus one additional embedded mod are identified**.
This is not a claim that 178 gameplay mods load: the 177 projects include
libraries and fixes, JARs can declare several mod IDs, and the complete installed
ensemble was not supplied. The 10 resource packs and two auxiliary JARs are
separate. Do not call the combined 190 matrix rows 190 unique mods.

None of the 187 requested publisher filenames occurs in the outer archive.
This is a manifest/overrides export, not a complete installed mod directory.
Public file metadata supplies requested filenames/versions, not local binary
hashes or proof that every dependency is installed. The original hash matches
the supplied Windows summary and chunks. No authenticated publisher signature
or independently verified official-download hash was provided.

## Export verification and independent reconstruction

All six uploads are accounted for. Five ZIP hashes match every row in
`EXPORT-SHA256SUMS.txt`; that text file's own hash is also recorded. Every export
ZIP is strictly below 32 MiB.

| Upload | Bytes | Verified SHA-256 |
| --- | ---: | --- |
| `00-summary.zip` | 5,846 | `87fb0bbc43673cd07a5a30b080944ea01437c7acf6e63ddcd5fc1f0ab3ae64a0` |
| `EXPORT-SHA256SUMS.txt` | 451 | `45b71d8e5c4c758b1041264fc27e3ee2a70c0d1a6a0a8dcda0aef8b2586c850c` |
| `archive-0001-of-0003.zip` | 25,166,346 | `93a0cf4248d85af4e7cec54dd70387b4526dd7d204b96f4392727e14532646f1` |
| `archive-0002-of-0003.zip` | 25,166,353 | `e9b24f968ab44430131c1553bede9ce59c7fb8ba766ec8a049c618b3c23bc93f` |
| `archive-0003-of-0003.zip` | 993,246 | `012ae42fbf32c54e44eb7c6e3473546385c251ea3daad987af52cff6d41ee5cc` |
| `metadata-0001-of-0001.zip` | 1,449,335 | `f90d7dccad8061b69210ac8ec0e3b42f2fb338ef42124ed2a063726801c0e08c` |

The trusted repository inspector is unchanged from code commit `91a14cd`.
Its LF source SHA-256 is
`883de714d6e80b9e1814e91f37a3b08f16791d4d3dfb33ffbe135f9624910912`.
Reassembly verified dataset names, numbering, counts, offsets, lengths,
per-payload/full hashes and the actual root 2.9.3 identity. Outputs were new owned
scratch paths; nothing was restored into a launcher profile.

Reassembled metadata ZIP SHA-256:
`a3a4355aea54c49828f949231a5f4a218010f4ea2a7cd5f6c697af6dd1e84632`.
Independent reinspection reproduced all six metadata members **byte for byte**:
manifest, HTML list, outer listing, SHA-256 manifest, nested listing and dependency
inventory. Their hashes and reconstruction receipt are retained in the JSON.

Only trusted Python parsing/hashing ran. No archive Java code, mod entrypoint,
ZenScript, native extension, installer or bundled command ran. No missing mod
binary was downloaded. Originals and assets remain outside the repository;
committed outputs contain analysis and facts.

## Complete matrix and classification meaning

All **187 manifest rows** were matched to public CurseForge metadata by numeric
**Project ID and requested File ID**, not HTML order. Public filenames, declared
versions, current licence labels, source links and dependency-tab observations
are retained per row. Three embedded JARs have separate hashes/static evidence.

Every original artifact is currently **BLOCKED** under the existing readiness
contract. Parsing metadata, finding source or proposing a replacement does not
promote a row to NATIVE COMPATIBLE. No subset is marked DATA PORTABLE before
rights, conversion and actual native output are validated. This does not mean
all individual features need an engine rewrite: priority/port-route fields
separate their feasibility.

API profiles are **role-based source-review worklists** for missing binaries,
not complete bytecode linkage proofs. Exact transitive APIs for the missing
original binaries remain unverified. Direct references are available for the
three delivered JARs.

## Dependencies and required Forge APIs

The dependency tabs at all 187 requested-file URLs were inspected, including
pagination. They expose **51 RequiredDependency, 74 OptionalDependency,
6 Incompatible and 1 Tool** relationships. These current public observations
are not a frozen release graph or verified dependency closure. An empty list
never proves an absence of dependencies.

Observed relationships include Ice and Fire → LLibrary, Scaling Health → Silent
Lib, LootTweaker → CraftTweaker, CompatSkills → Reskillable, ModTweaker → MTLib,
and Dynamic Surroundings: HUDs → OreLib. Typed edges are in JSON; required and
optional references are also in CSV.

One observed required target, **Kotlin for Forge**, is absent from the manifest.
It appears on Bountiful's requested-file dependency tab although the selected
file is `Bountiful-1.12.2-2.2.3.jar`. The inspected
[legacy source family](https://github.com/ejektaflex/Bountiful/blob/a44a57e0968bf2aa8a924a420b35f301ec377019/src/main/kotlin/ejektaflex/bountiful/BountifulInfo.kt)
identifies **2.2.2**, Forge 1.12 and Forgelin; its
[build file](https://github.com/ejektaflex/Bountiful/blob/a44a57e0968bf2aa8a924a420b35f301ec377019/build.gradle.kts)
uses Forgelin 1.8.2. This is not a source match to the selected 2.2.3 binary.
Record **metadata/version drift unresolved**; do not install modern Kotlin for
Forge, replace Forgelin or declare the original pack broken from this evidence.
All other observed required targets have project references in the manifest;
version compatibility remains unproved. None of the six observed incompatible
targets is selected in this manifest.

| Area | Original interfaces / remaining work |
| --- | --- |
| Loader/libraries | JVM, Forge FML lifecycle, `@Mod`, event bus, sided proxies, dependency/version handling and library APIs |
| Content/recipes | Forge registries, legacy Item/Block/ItemStack metadata, OreDictionary, recipes, tile entities, containers and persistence |
| Survival/combat | Living/player events, damage/effects/attributes, capabilities, equipment, authoritative packets and saved state |
| Entities/worldgen | Entity registration/AI/animation, spawning, biomes, chunks, structures and persistent IDs |
| UI/rendering | Forge overlays/tooltips/container events, inventory rules and old model/GL/audio assumptions |
| Bootstrap/fixes | LaunchWrapper/FML core plugins, `IClassTransformer`, ASM/Mixin and exact old Minecraft internals |
| Scripts/assets | ZenScript, legacy IDs/ore names, custom loot, structures, models, textures and sounds; adapt only approved pieces |

These are API families, not an assertion that every row uses every interface.
Per-row profiles narrow the worklist. Rust game types/native hooks do not make
those original Java classes executable.

### Delivered JAR evidence

| File | Static evidence and blocker |
| --- | --- |
| `antiquecities-1.2.1.jar` | 5 classes; empty `mcmod.info` dependency array, but constants identify required Antique Atlas/Lost Cities integration. References include AtlasAPI, TileAPI, LostCityEvent.PreExplosionEvent, Forge lifecycle/event bus and old chunk/world classes. An unusual Lost Cities range spelling remains unvalidated by Forge execution. |
| `mcjtytools-0.0.21.jar` | 17 classes; Maven coordinate declared. References include Forge/Minecraft inventory, item, NBT, entity, command, tile-entity and world types. Utility dependency, not another verified gameplay mod. No embedded licence text or exact-source binding established. |
| `llibrary-core-1.0.11-1.12.2.jar` | 60 classes; manifest FML core plugin LLibraryPlugin. References include LaunchWrapper, ASM, Forge hooks and old client/model/renderer classes. Parent project terms do not automatically clear this exact core JAR. |

Full hashes, metadata and reference samples are in the matrix/JSON. The public
Antique Cities source family is reachable and MIT-licensed, but its inspected
source VERSION is 1.0; it does not authenticate the embedded 1.2.1 binary.

## Configuration, scripts and assets

The outer listing includes 1,393 JSON, 488 CFG, 510 PNG, 9 OGG, 7 ZenScript,
381 TML, 211 RCST, 73 RCIG, 39 schematic and 6 nested ZIP files. These are file
counts, not mod counts. Cached configuration for Biomes O' Plenty does not add
that mod to the manifest. Six log files remain private input data, not commands
or committed report content.

Scripts reference CraftTweaker/LootTweaker, old item/ore IDs and missing mod
systems. Reading them does not implement ZenScript. The included RLHats ZIP
declares resource `pack_format: 3`; a successful ZIP read does not certify it for
26.3. Resource/structure conversion, target IDs, rendering features and separate
artwork/sound rights remain gates.

## Source availability and licensing

Of 187 manifest projects, **155 advertise a Source URL**: 152 GitHub-linked
projects and three other source hosts. Those GitHub links resolve to 149 distinct
repositories; **147 are publicly reachable** after resolving renames. The
advertised HelpFixer and Phosphor URLs returned 404, without ruling out other
mirrors. Other source hosts were recorded as publisher links without independent
retrieval. The remaining 32 projects advertise no Source URL in the retrieved
metadata; issue trackers do not automatically prove complete source availability.

Repository reachability/default-branch licence metadata does not establish
exact 1.12.2 release source or binary correspondence. Per-row evidence records
that distinction, including renamed repositories.

Current publisher licence labels across the 187 projects:

| Current publisher label | Projects |
| --- | ---: |
| MIT License | 82 |
| All Rights Reserved | 36 |
| GNU Lesser General Public License version 3 (LGPLv3) | 20 |
| Custom License | 15 |
| GNU General Public License version 3 (GPLv3) | 12 |
| GNU Lesser General Public License version 2.1 (LGPLv2.1) | 8 |
| Apache License version 2.0 | 5 |
| WTFPL | 4 |
| BSD License | 2 |
| Creative Commons Attribution-NonCommercial 3.0 Unported | 2 |
| GNU General Public License version 2 (GPLv2) | 1 |

These are current declarations, not exact-binary/asset clearance. MIT/Apache/BSD
reuse still requires applicable notices; GPL/LGPL reuse requires applicable
version/source/distribution obligations. Custom/ARR/NonCommercial terms need
individual review. Do not choose the most permissive conflicting label: XP From
Harvest currently says ARR on CurseForge while its linked repository default
licence is LGPL-3.0. No artifact is distribution-cleared by this analysis.

The recommended feature's
[1.12.2 Craftable Chainmail source](https://github.com/ModsByLeo/CraftableChainmail/tree/0561a6cb57ad40edc1bf1ec7a1642e23096254fa)
identifies version 1.0 and has an explicit
[MIT licence](https://github.com/ModsByLeo/CraftableChainmail/blob/0561a6cb57ad40edc1bf1ec7a1642e23096254fa/LICENSE).
The selected file is project 319746/file 2701067, `craftablechainmail-1.0.jar`.
Source-version correspondence is useful, but no local JAR hash authenticates that
build. The publisher page also has separate modpack-distribution wording; this
proposal redistributes neither its JAR nor assets. Author native definitions and
retain applicable MIT notices for material actually reused.

## Native feasibility and priorities

The pinned engine is Horizon 0.7.6 / 26.3 at
`7301f6fdd7f470b11317276e7a11b4dc615c137a`. Its
[active contract](https://github.com/Vasysik/horizon-android/blob/7301f6fdd7f470b11317276e7a11b4dc615c137a/docs/mods.md)
documents **content `.hmod`** and **Rust source-patching `.hnmod`**. Native mods
run with player privileges and need trusted source builds. Legacy WIT SDK files
do not establish a usable WASM runtime path; this corrects the earlier plan's
assumption about those interfaces.

| Priority | Candidate | Why / limits |
| --- | --- | --- |
| **P1** | **Chainmail plate → boots crafting slice** | One template-based item and two recipes through content API 0.2. Source/licence inspected. No JVM, Forge bridge, combat hook or engine rewrite. See the concrete proposal. |
| P2 | One independently worded vanilla-enchantment tooltip | Small read-only QoL feature; native tooltip hook API 12 is documented. Versioned source/rights, trusted Rust build and real hook evidence still required. |
| P3 | Another isolated recipe/loot adaptation | Establish supported 26.3 IDs, semantics and rights. Do not translate entire ZenScript files or assume ore-dictionary parity. |
| Later | Scoped HUD/atlas feature | Prove native hook/render/data coverage. A health number does not implement First Aid's limb model; an overlay does not establish Atlas/Neat parity. |
| Defer | Temperature/thirst, skills, combat, inventory transfers | Persistent authoritative state, duplication prevention, input and balance testing; isolate one precise contract first. |
| Defer | Dragons/Lycanites/Parasites and world generation | Large AI/rendering/registry/generator/save/licensing/performance dependencies; approval needed for major engine changes. |
| No automatic port | Old coremod/performance patches | First demonstrate an equivalent native defect or measurable need. |

The first slice excludes Reskillable's Defense 4 gate, other armor recipes and
plate integrations in wolf armor, chain skirts and Lycanites saddles. Those
integrations are visible in supplied configuration/scripts. Crafting success
would establish neither those behaviors nor whole-pack progression/balance.

## Remaining evidence and stop point

Static reconstruction and complete matrix coverage are finished. Exact missing
JAR annotations, full transitive linkage, source/binary binding and historical
release/asset rights are not. Obtain further binaries only if lawfully supplied
by the user; this investigation downloads none.

Original RLCraft launch, rendered gameplay, world creation/load, combat, save
migration, crash recovery and performance were **NOT RUN**. Proposed crafting
and physical Windows/macOS acceptance are also **NOT RUN**: this turn produces
recommendations only. Historical Phase 5D CI is launcher/package evidence, not
RLCraft acceptance.

The 2XD/RL-Craft reference at
[`8519c53`](https://github.com/2XD/RL-Craft/tree/8519c53bd0bca16e2be6b76b4f38df0320a75577)
declares **2.8.2** and is excluded from all 2.9.3 rows/counts. Java Build/Test and
whole-Modpack Play remain disabled. No gameplay implementation, world conversion,
major engine rewrite, main merge, tag or release begins. Work stops at this
report and recommendation.
