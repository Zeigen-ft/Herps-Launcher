# First gameplay recommendation — chainmail plate to boots

**Approved slice implemented; physical gameplay acceptance remains NOT RUN.**
See the [implementation verification](RLCRAFT_CHAINMAIL_VERIFICATION.md) and
[Windows survival test guide](WINDOWS_CHAINMAIL_ACCEPTANCE.md).
See the [verified archive report](RLCRAFT_COMPATIBILITY_REPORT.md) and
[complete artifact matrix](RLCRAFT_293_MOD_MATRIX.md).

## Proposed behavior

Implement one independently authored native **content `.hmod`** with:

1. One namespaced chainmail-plate item, using a vanilla item template.
2. A recipe: four vanilla iron nuggets in a 2×2 square → one plate.
3. A recipe: four plates in the normal boots pattern → one vanilla
   `minecraft:chainmail_boots` item.

This is real crafting/gameplay, with no Java execution, script interpreter,
source patch, compatibility bridge or new engine API. Keep Java Build/Test and
whole-Modpack Play disabled. It is a feature replacement, not a whole RLCraft port.

## Source and rights evidence

The actual manifest requests **project 319746 / file 2701067**,
`craftablechainmail-1.0.jar`. The source moved from Leo40Git to ModsByLeo.
Its 1.12.2 branch is pinned to
`0561a6cb57ad40edc1bf1ec7a1642e23096254fa`:

- [Build metadata](https://github.com/ModsByLeo/CraftableChainmail/blob/0561a6cb57ad40edc1bf1ec7a1642e23096254fa/build.gradle) declares version 1.0, Minecraft 1.12.2/Forge and Java 8.
- [MIT licence](https://github.com/ModsByLeo/CraftableChainmail/blob/0561a6cb57ad40edc1bf1ec7a1642e23096254fa/LICENSE) is present at that revision.
- The [plate recipe](https://github.com/ModsByLeo/CraftableChainmail/blob/0561a6cb57ad40edc1bf1ec7a1642e23096254fa/src/main/resources/assets/craftablechainmail/recipes/chainmail_plate.json) uses Forge's `nuggetIron` ingredient.
- The [boots recipe](https://github.com/ModsByLeo/CraftableChainmail/blob/0561a6cb57ad40edc1bf1ec7a1642e23096254fa/src/main/resources/assets/craftablechainmail/recipes/chainmail_boots.json) consumes plates and produces vanilla boots.

This is source-version correspondence, not an authenticated match to the absent
JAR. Retain applicable MIT copyright/permission notices for material actually
reused. Prefer new native definitions/namespacing and a vanilla-template display;
copy no textures or original JAR. The publisher page's separate
modpack-distribution wording does not clear the original artifact/assets.

## Existing native path

The pinned engine's
[content API 0.2](https://github.com/Vasysik/horizon-android/blob/7301f6fdd7f470b11317276e7a11b4dc615c137a/docs/mods.md#content-mods-api-02)
supports template-based items and recipes. Use the active 26.3 conventions:
singular `data/<id>/recipe/`, result `id` and the supported ingredient format.
Do not copy old `assets/.../recipes`, `result.item` or `forge:ore_shaped` JSON.

Explicitly map the old iron-nugget ore entry to `minecraft:iron_nugget` for this
vanilla-only slice. Arbitrary Forge ore aliases remain unsupported. Validate
the actual prepared-resource IDs, template/name/model fallback and recipe
behavior before packaging. A vanilla template avoids copying the old texture.

An installed runtime user should need the launcher/game and legitimate prepared
resources, without Rust/Cargo, Forge or a mod JVM. Developer/CI packaging remains
a separate trusted operation. No new Java Mods execution button is involved.

## Scope and differences from RLCraft

- Plate and boots only. Other armor pieces and original advancement/recipe-book
  discovery behavior are excluded or require an explicitly revised contract.
- No Reskillable. Supplied `overrides/config/reskillable.cfg` lines 218–221 gate
  chainmail equipment at Defense 4. This slice does not reproduce that rule or
  original RLCraft progression/balance.
- No Wolf Armor, Varied Commodities or Lycanites integration. `Shiv.zs` uses
  plates in wolf armor at line 1274, a chain skirt at 1442–1444 and a Lycanites
  saddle at 1908. Those recipes/dependencies are excluded.
- No Forge save migration, old pack installation, custom combat or extra slots.
- Preserve Phase 5D behavior, source imports, profile isolation, existing saves
  and FunCraft backups. Install only an owned package in an opted-in disposable
  profile and keep it disabled by default.

## Sequence after explicit implementation approval

1. Freeze the behavior, namespaced package identity, source references/notices
   and test contract. Confirm existing engine support without changing it.
2. Author only the minimal item/recipes/notices; own new files exclusively and
   preserve unknown settings, original imports and all existing content.
3. Validate schema/IDs, namespace collisions, disabled start and profile-local
   installation/removal. Do not relax archive/data guards to make it load.
4. Build an internal Windows candidate and separately authorized Mac targets,
   recording source/package hashes and all failures/skips.
5. Run automated checks and the genuine gameplay acceptance below, separately.
6. Report and stop. Any major engine change, signing service/credentials or
   release publication requires approval.

## Acceptance — all currently NOT RUN

Use an externally backed-up **new disposable native profile/world**. Never use
a valuable save or old RLCraft/Forge world. Record initial hashes and logs.

| Case | Required observation |
| --- | --- |
| Disabled start | Existing unmodded profiles/recipes behave as before; nothing activates in another profile |
| Enable/restart | Content loads without errors; item IDs/name/display are correct |
| Real survival crafting | Two ingots → 18 nuggets; consume 16 nuggets to make four plates, then four plates → one pair of boots; two nuggets remain |
| Wrong inputs/layout | No output or ingredient consumption for an invalid grid |
| Stack/shift crafting | Exact consumption/output with no duplication or lost stacks |
| Equip/use | Boots have normal vanilla behavior; no Defense gate is falsely claimed |
| Save/load/relaunch | Craft an extra plate from additional materials; save with plate and boots present, exit, reload/relaunch and verify item IDs/counts |
| Preservation | Another profile's save hashes, settings/imports and earlier backups remain intact |
| Missing/disabled content | Test only on a backed-up disposable world; establish custom-plate persistence/recovery. No silent item discard or valuable-world exposure |
| No developer tools | Runtime works without Rust/Cargo and makes no build/dependency fetch attempt |
| Platforms | Record physical Windows 11 x64; record macOS ARM64 and Intel separately when tested; keep CI evidence distinct |

Data loss, bad consumption, duplication, save corruption, failure to relaunch or
cross-profile mutation blocks acceptance. If custom-item persistence requires a
major engine change, stop for approval; do not hide the limitation or discard
data to pass. Parsing/registry fixtures, successful packaging and synthetic files
cannot substitute for real crafting and world-load observations.

Until that evidence exists, keep this feature experimental/unverified and the
original whole-mod row BLOCKED. No complete RLCraft acceptance is implied.
