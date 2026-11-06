# FunCraft hotfix — compatibility and passive inspection report

Date: 2026-11-05 (Asia/Singapore). Baseline: `3112e32`.
Input: `FunCraft - FC-Release 1.1.1 - hotfix.zip`.

**Not playable as the original modpack in Herspers.** No Java code was run and no
whole mod is certified native. The first implemented slice is the limited
manual-backup behavior described in the [initial implementation report](INITIAL_IMPLEMENTATION_REPORT.md).

## Verified input facts

| Field | Observed value |
| --- | --- |
| SHA-256 | `09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e` |
| Compressed bytes | 5,727,544 |
| Total ZIP entries / regular files | 603 / 499 |
| Uncompressed regular-file bytes | 13,130,402 |
| Declared pack | FunCraft - FC / Release 1.1.1 - hotfix |
| Author in manifest | ScaldaYT |
| Minecraft | 1.12.2 |
| Primary loader | Forge 14.23.5.2847 |
| Manifest project/file pairs | 154 |
| Physical JAR paths | 16 |
| Class entries across those JARs, including shaded libraries | 1806 |
| Minecraft/Herspers gameplay | NOT RUN |

The ZIP is a CurseForge manifest plus overrides **with some actual JARs**. It is
neither manifest-only nor a complete installed mod ensemble. The 154 pairs and
16 paths must not be added as unique mods; correspondence/duplicate coverage is
not authenticated. Project labels in `modlist.html` are matched by project ID,
never list position. A CurseForge file ID is not a semantic mod version.

## Data, configuration and runtime evidence

The 499 regular files include 224 CFG, 162 JSON, 53 XML, 16 JAR, 12 PNG, four ZIP,
one ZenScript, one NBT and other metadata/property/text files. The full hashed
path listing and per-JAR evidence are in [funcraft-inventory.json](funcraft-inventory.json).

- `overrides/config/` contains Forge/mod configuration, Nutrition definitions,
  world-generation/recipe settings and machine recipes. These are Java-mod inputs,
  not Herspers configuration. They are not copied into active profiles.
- `overrides/scripts/Recipe_Changes.zs` references AE2 Inscriber, Actually Additions
  Empowerer/Reconstructor, Botania, RFTools, Forge fluid buckets and ore-dictionary
  names. Most referenced items/machines do not exist in the current native game.
  A ZenScript interpreter or the required registries/machines is not present.
- JARs contain old `mcmod.info`, Java annotation candidates, LaunchWrapper tweak
  classes, FML core plugins and access transformers. Phosphor also bundles
  Sponge/ASM mixin machinery. Metadata dependency arrays can omit dependencies
  declared in annotations or coremod behavior.
- Sample byte references demonstrate dependencies on Minecraft/Forge, Guava,
  Netty, ASM and Sponge packages. They are static samples, not a complete class
  linkage proof or a Java execution test. Maven POM dependencies are retained
  separately and can include test/optional scopes or unresolved parent properties.
- The shipped modern Forge/Fabric preflight does not establish support for these
  legacy loader conventions. Six embedded Maven JARs have invalid UNIX type bits
  on empty directory entries. The analysis records the anomalies; the production
  archive policy is not relaxed to accept them.
- Resource packs include `1.14_Textures_1.1.zip` and
  `FunCraft_Jappa_Ores_1.0.1.zip`. There is also an empty ChanceCubes custom-sound
  resource pack and an EnderIO recipe archive. No usable OGG sound files are
  established by this inventory. Old texture paths/pack formats and unavailable
  mod namespaces need adaptation; missing rights block asset copying.

Herspers uses pinned native Horizon 0.7.6 with 26.3 resources. It does not provide
a Forge 1.12.2 JVM, ore dictionary, Forge energy/fluid capabilities, the old block
metadata registry, Java tile-entity rendering or arbitrary ASM transformations.
Import, metadata analysis and backup operations do not resolve that mismatch.

## Whole-mod classification matrix — manifest requirements

Every manifest row below is currently **BLOCKED**: its exact local JAR/version,
source/licence scope and full dependency/API closure are not verified, and the
original Forge runtime is unavailable. This classification is current readiness,
not a claim that all individual behaviors are impossible to reimplement.
`Unknown` dependencies must not be displayed as an empty dependency list.

All rows require legacy Minecraft/Forge; exact additional APIs and effort remain
unestimated until source inspection. Pairs below are direct `manifest.json`
evidence; names come from the matching project URL in `modlist.html`.

| Mod / author label | Exact identity | Version | Dependencies / APIs | Classification | Effort |
| --- | --- | --- | --- | --- | --- |
| AppleCore (by squeek502) | CF 224472 / 2679415 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Just Enough Resources (JER) (by way2muchnoise) | CF 240630 / 2728585 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Just Enough Energistics (JEE) (by TheRealp455w0rd) | CF 310812 / 2783832 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Better Builder's Wands (by Portablejim) | CF 238403 / 2443194 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Hwyla (by TehNut) | CF 253449 / 2568751 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| CoralReef (by primetoxinz) | CF 248994 / 2560552 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Faucets and Filters (by Dreadwing93) | CF 268490 / 2486623 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Bad Wither No Cookie - Reloaded (by Kreezxil) | CF 261251 / 2638317 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thermal Cultivation (by TeamCoFH) | CF 271835 / 2715791 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| LemonLib (by Lemonszz) | CF 306926 / 2639879 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| LunatriusCore (by Lunatrius) | CF 225605 / 2489549 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Stackie (by Lunatrius) | CF 225606 / 2489553 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Just Enough HarvestCraft (JEHC) (by mrAppleXZ) | CF 267939 / 2723786 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Cosmetic Armor Reworked (by LainMI) | CF 237307 / 2697672 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Shadowfacts' Forgelin (by ShadowfactsDev) | CF 248453 / 2785465 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Actually Additions (by Ellpeck) | CF 228404 / 2774057 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Clothesline (by jamieswhiteshirt_) | CF 300262 / 2754456 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Morpheus (by Quetzi) | CF 69118 / 2664449 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Vials (by LordJoda) | CF 269083 / 2537151 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Tesla Core Lib (by face_of_cat) | CF 254602 / 2580052 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Botania (by Vazkii) | CF 225643 / 2782181 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| AtomicStryker's Infernal Mobs (by atomicstrykergrumpy) | CF 227875 / 2771611 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Gas Conduits (by pupnewfster) | CF 309756 / 2755340 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| More Overlays (by FeldiM245) | CF 243478 / 2745657 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Fabrication (by MrTJP) | CF 230111 / 2745547 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Sky Resources 2 (by Bartz24) | CF 243482 / 2758220 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MrTJPCore (by MrTJP) | CF 229002 / 2735197 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thermal Foundation (by TeamCoFH) | CF 222880 / 2715788 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Mekanism (by bradyaidanc) | CF 268560 / 2755008 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Redstone Flux (by TeamCoFH) | CF 270789 / 2623090 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Mekanism Generators (by bradyaidanc) | CF 268566 / 2755010 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Mekanism Tools (by bradyaidanc) | CF 268567 / 2755011 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Hammer (Lib) Core (by Zeitheron) | CF 247401 / 2803815 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| CoFH Core (by TeamCoFH) | CF 69162 / 2716100 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Ender Storage 1.8.+ (by covers1624) | CF 245174 / 2755787 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| TombManyGraves 2 API (by M4thG33k) | CF 294202 / 2563073 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| ComputerCraft (by DanTwoHundred) | CF 67504 / 2478952 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Integration (by MrTJP) | CF 229045 / 2745548 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| TombManyPlugins - Cosmetic Armor Reworked (by M4thG33k) | CF 294214 / 2563120 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Lighting (by MrTJP) | CF 229046 / 2745549 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Mechanical (by MrTJP) | CF 229048 / 2745550 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - World (by MrTJP) | CF 229049 / 2745551 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Compat (by MrTJP) | CF 229050 / 2745546 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| CoFH World (by TeamCoFH) | CF 271384 / 2715784 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| The Erebus (by vadis365) | CF 220698 / 2727867 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| p455w0rd's Library (by TheRealp455w0rd) | CF 255232 / 2745046 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Placebo (by Shadows_of_Fire) | CF 283644 / 2694382 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| iChunUtil (by ohaiiChun) | CF 229060 / 2684000 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| The Magic Mirror (by tboshoven) | CF 323750 / 2722088 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Placeable Items (by Ferdz_) | CF 227951 / 2543705 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Better Advancements (by way2muchnoise) | CF 272515 / 2685984 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Wireless Redstone CBE (by covers1624) | CF 260824 / 2755798 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Bookshelf (by DarkhaxDev) | CF 228525 / 2727800 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| EnderCore (by tterrag1098) | CF 231868 / 2822401 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Moar Tinkers (by AshuraNoYami) | CF 263624 / 2579934 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Snad (by TheRoBrit) | CF 241344 / 2480458 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| WanionLib (by WanionCane) | CF 253043 / 2651482 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| AE2 Stuff (by bdew) | CF 225194 / 2491032 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| RFTools (by McJty) | CF 224641 / 2745848 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Pam's HarvestCraft (by pamharvestcraft) | CF 221857 / 2771840 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| OpenBlocks Elevator (by vsngarcia) | CF 250832 / 2788813 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Idō (by bagu_chan) | CF 322131 / 2751053 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thermal Dynamics (by TeamCoFH) | CF 227443 / 2716138 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| PTRLib (by RazzleberryFox) | CF 291499 / 2685154 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Waila Harvestability (by squeek502) | CF 79287 / 2481605 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| FTB Backups (by LatvianModder) | CF 314904 / 2749104 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| PlusTiC (by landmaster_phuong0429) | CF 260327 / 2789248 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Biome Paint Tools (by Zeitheron) | CF 254204 / 2578653 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| BiblioCraft (by Nuchaz) | CF 228027 / 2574880 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Block Drops (JEI Addon) (by KidsDontPlay) | CF 244181 / 2509046 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Chisel (by tterrag1098) | CF 235279 / 2619468 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| JEI Integration (by SnowShock35) | CF 265917 / 2491927 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Statues: Rechiseled (by Lemonszz) | CF 311592 / 2664963 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Spice of Life: Carrot Edition (by lordcazsius) | CF 277616 / 2731062 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| FlameLib (by Cursed1nferno) | CF 313267 / 2668970 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MysticalLib (by EpicSquid319) | CF 277064 / 2780930 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Xtones (by TehNut) | CF 257573 / 2531411 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Chest Transporter (by cubex2) | CF 78778 / 2524058 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Wawla - What Are We Looking At (by DarkhaxDev) | CF 224712 / 2707185 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| ConnectedTexturesMod (by tterrag1098) | CF 267602 / 2642375 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| CraftTweaker (by Jaredlll08) | CF 239197 / 2724129 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Champions (by TheIllusiveC4) | CF 307152 / 2743445 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Crafting Tweaks (by BlayTheNinth) | CF 233071 / 2562139 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Just Enough Vehicles (by Ozelot5836) | CF 327775 / 2742862 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Custom Main Menu (by Lumien231) | CF 226406 / 2638282 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Quark (by Vazkii) | CF 243121 / 2759240 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| AutoRegLib (by Vazkii) | CF 250363 / 2746011 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thaumcraft (by Azanor13) | CF 223628 / 2629023 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Torchmaster (by xalcon) | CF 254268 / 2769534 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| McJtyLib (by McJty) | CF 233105 / 2745846 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| stimmedcow : NoMoreRecipeConflict (by GotoLink) | CF 238123 / 2671230 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Mantle (by mDiyo) | CF 74924 / 2713386 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| UniDict (by WanionCane) | CF 244258 / 2652588 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Inventory Tweaks (by Kobata) | CF 223094 / 2482481 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MrCrayfish's Furniture Mod (by MrCrayfish) | CF 55438 / 2749993 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Obfuscate (by MrCrayfish) | CF 289380 / 2625165 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Biomes O' Plenty (by Forstride) | CF 220318 / 2715506 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Controlling (by Jaredlll08) | CF 250398 / 2731319 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Resource Loader (by Lumien231) | CF 226447 / 2477566 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Tinkers' Tool Leveling (by bonusboni) | CF 250957 / 2630860 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thaumic JEI (by Buuz135) | CF 285492 / 2705304 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| BdLib (by bdew) | CF 70496 / 2518031 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Blood Magic  (by WayofTime) | CF 224791 / 2778627 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Cooking for Blockheads (by BlayTheNinth) | CF 231484 / 2733516 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Project Red - Base (by MrTJP) | CF 228702 / 2745545 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MTLib (by Jaredlll08) | CF 253211 / 2684561 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| SwingThroughGrass (by exidex) | CF 264353 / 2508268 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| TAIGA (Tinkers alloying addon) (by zkafaceTV) | CF 247661 / 2626416 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MrCrayfish's Vehicle Mod (by MrCrayfish) | CF 286660 / 2762988 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| AppleSkin (by squeek502) | CF 248787 / 2496585 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| FTB Utilities (by LatvianModder) | CF 237102 / 2783727 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Fast Leaf Decay (by olafskiii) | CF 230976 / 2463272 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Bountiful (by ejektaflex) | CF 309516 / 2672350 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Blockcraftery (by EpicSquid319) | CF 278882 / 2716712 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| ModTweaker (by Jaredlll08) | CF 220954 / 2693544 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Just Enough Items (JEI) (by mezz) | CF 238222 / 2682936 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Baubles (by Azanor13) | CF 227083 / 2518667 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Iron Chests (by ProgWML6) | CF 228756 / 2747935 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Translocators 1.8.+ (by covers1624) | CF 247695 / 2755795 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| ReAuth (by TechnicianLP) | CF 237701 / 2560638 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Thermal Innovation (by TeamCoFH) | CF 291737 / 2715787 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Applied Energistics 2 (by AlgorithmX2) | CF 223794 / 2747063 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| The Aether II (by GildedGames) | CF 223796 / 2760246 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| FTB Library (by LatvianModder) | CF 237167 / 2783045 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Diet Hoppers (by RWTema) | CF 278385 / 2482543 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Cubic Villager (by a1lic) | CF 238287 / 2519431 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Redstone Arsenal (by TeamCoFH) | CF 70631 / 2715786 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Chameleon (by Texelsaur) | CF 230497 / 2450900 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Dark Utilities (by DarkhaxDev) | CF 242195 / 2694889 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Guide-API (by TehNut) | CF 228832 / 2645992 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Extended Crafting (by BlakeBr0) | CF 268387 / 2777071 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Tinker's JEI (by Possible_triangle) | CF 291786 / 2701203 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Tomb Many Graves 2 (by M4thG33k) | CF 262823 / 2619249 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Toast Control (by Shadows_of_Fire) | CF 271740 / 2707353 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Mouse Tweaks (by YaLTeR) | CF 60089 / 2671937 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Storage Drawers (by Texelsaur) | CF 223852 / 2777929 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| BountifulBaubles (by Cursed1nferno) | CF 313536 / 2741478 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MMD OreSpawn (by jriwanek) | CF 245586 / 2702565 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Railcraft (by Covert_Jaguar) | CF 51195 / 2687757 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| AnimalNet (by MrMarnic) | CF 305748 / 2753985 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Fairy Lights (by pau101) | CF 233342 / 2738484 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Cucumber Library (by BlakeBr0) | CF 272335 / 2645867 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Ender IO (by CrazyPants_MC) | CF 64578 / 2809869 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| CodeChicken Lib 1.8.+ (by covers1624) | CF 242818 / 2779848 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Overlord (by The_Fireplace) | CF 251732 / 2631782 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| JourneyMap (by techbrew) | CF 32274 / 2755458 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Catwalks 4 (by dmf444) | CF 296851 / 2610569 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MalisisDoors (by Ordinastie) | CF 223891 / 2526674 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Forge MultiPart CBE (by covers1624) | CF 258426 / 2755790 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| MalisisCore (by Ordinastie) | CF 223896 / 2680892 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Astral Sorcery (by HellFirePvP) | CF 241721 / 2757379 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Tinkers Construct (by mDiyo) | CF 74072 / 2731543 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| Unlimited Chisel Works (by asiekierka) | CF 278493 / 2762540 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |
| FoamFix for Minecraft (by asiekierka) | CF 278494 / 2695388 | Unknown; JAR identity unresolved | Dependencies unknown; MC 1.12.2 / Forge, exact APIs unverified | BLOCKED | Unestimated |

## Physical bundled JARs — separate evidence, not extra authenticated projects

Versions below are metadata, Maven-coordinate or filename claims; see the JSON
for their provenance. The POM declarations and full header/class/notice samples
are retained in the JSON/CSV. Absence of a declared dependency is not proof of
absence. These original JVM files are all blocked; utility libraries do not
become native-compatible merely because they are not gameplay mods.

| Physical JAR | Version evidence | Classes | Required API evidence | Hooks / changes | Classification |
| --- | --- | --- | --- | --- | --- |
| `overrides/mods/Nutrition-1.12.2-4.4.0.jar` | 1.12.2-4.4.0 | 49 | com/google/common/, io/netty/, net/minecraft/, net/minecraftforge/ | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/1.12.2/ChickenASM-1.12-1.0.2.7.jar` | Filename only | 27 | com/google/common/, net/minecraft/, net/minecraftforge/, org/objectweb/asm/ | codechicken.asm.internal.Tweaker | BLOCKED |
| `overrides/mods/1.12.2/CraftStudio-1.0.0.93-mc1.12-alpha.jar` | 1.0.0 | 51 | io/netty/, net/minecraft/, net/minecraftforge/ | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/1.12.2/engine.io-client-1.0.0.jar` | Filename only | 96 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/1.12.2/json-20090211.jar` | Filename only | 19 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/1.12.2/okhttp-3.8.1.jar` | Filename only | 201 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/1.12.2/okio-1.13.0.jar` | Filename only | 43 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/memory_repo/com/enderio/core/EnderCore/1.12.2-0.5.65/EnderCore-1.12.2-0.5.65-core.jar` | com.enderio.core:EnderCore:1.12.2-0.5.65:core | 19 | com/google/common/, net/minecraft/, net/minecraftforge/, org/objectweb/asm/ | com.enderio.core.common.transform.EnderCorePlugin | BLOCKED |
| `overrides/mods/memory_repo/com/gildedgames/orbis-lib/1.12.2-0.2.0+build127/orbis-lib-1.12.2-0.2.0+build127.jar` | 1.12.2-0.2.0+build127 | 474 | com/google/common/, io/netty/, net/minecraft/, net/minecraftforge/ | orbis-lib_at.cfg | BLOCKED |
| `overrides/mods/memory_repo/com/jamieswhiteshirt/clothesline-hooks/1.12.2-0.0.1.2/clothesline-hooks-1.12.2-0.0.1.2.jar` | com.jamieswhiteshirt:clothesline-hooks:1.12.2-0.0.1.2 | 19 | com/google/common/, net/minecraft/, net/minecraftforge/, org/objectweb/asm/ | com.jamieswhiteshirt.clothesline.hooks.plugin.FMLLoadingPlugin | BLOCKED |
| `overrides/mods/memory_repo/com/jamieswhiteshirt/rtree-3i-lite/0.3.0/rtree-3i-lite-0.3.0.jar` | com.jamieswhiteshirt:rtree-3i-lite:0.3.0 | 28 | com/google/common/ | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/memory_repo/info/loenwind/autoconfig/AutoConfig/1.12.2-1.0.2/AutoConfig-1.12.2-1.0.2.jar` | info.loenwind.autoconfig:AutoConfig:1.12.2-1.0.2 | 52 | io/netty/, net/minecraft/, net/minecraftforge/ | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/memory_repo/info/loenwind/autosave/AutoSave/1.12.2-1.0.11/AutoSave-1.12.2-1.0.11.jar` | info.loenwind.autosave:AutoSave:1.12.2-1.0.11 | 61 | com/google/common/, net/minecraft/, net/minecraftforge/ | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/memory_repo/io/socket/socket.io-client/1.0.0/socket.io-client-1.0.0.jar` | Filename only | 60 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |
| `overrides/mods/memory_repo/me/jellysquid/mods/phosphor/1.12.2-0.2.6+build50/phosphor-1.12.2-0.2.6+build50.jar` | 1.12.2-0.2.6+build50 | 538 | com/google/common/, net/minecraft/, net/minecraftforge/, org/objectweb/asm/, org/spongepowered/asm/ | me.jellysquid.mods.phosphor.core.PhosphorFMLLoadingPlugin, org.spongepowered.asm.launch.MixinTweaker, phosphor_at.cfg; mixin JSON present | BLOCKED |
| `overrides/mods/memory_repo/org/java-websocket/Java-WebSocket/1.3.8/Java-WebSocket-1.3.8.jar` | Filename only | 69 | JVM/library dependencies; no native runtime | No entrypoint proved by headers; annotation/dependency review incomplete | BLOCKED |

## Feature-level opportunities and legal gates

| Candidate behavior | Potential technical route | Current gate |
| --- | --- | --- |
| FTB Backups manual world snapshot | Independent launcher operation; no engine change | Manual stopped-world backup implemented and fixture-verified; original JAR remains unsupported |
| Hwyla/Wawla information overlay | Existing game-read/HUD APIs for a precisely limited subset | Exact source/rights and intended fields need review; no whole-mod equivalence |
| JEI-like recipe browsing | Existing engine recipe/UI facilities | Native vanilla recipes do not imply modded machines or 1.12 recipes |
| Old resource-pack subset | Explicit path/schema conversion | Artwork rights and target assets unresolved; no copying |
| Nutrition | Player nutrition state, food events, effects, persistence and UI | Engine API/state work, source/licence and save design required |
| Phosphor/coremods | Reimplement algorithms against native lighting/game systems | Engine extension/rewrite; JVM/ASM cannot be reused as executable native code |
| Machines, dimensions, modded mobs and linked recipe progression | Native registries, world systems, AI, renderers and integration tests | Large interconnected project; not this iteration |

The [licensing/dependency inventory](LICENSING_AND_DEPENDENCIES.md) records known
scoped POM/notice claims and unknown rights. No mod JAR, configuration/artwork,
Mojang asset or generated modpack binary is committed or redistributed.

## Verification and remaining blockers

The passive tool read the actual hash-matched archive without executing Java,
ZenScript, classes, coremods, scripts or HTML instructions. This verifies an
inventory only. The original pack's installation, full dependency resolution,
assets/logic adaptation, actual gameplay, world conversion/save/load, native
renderer/audio behavior, crash recovery and performance are **NOT RUN**.

Current whole-pack compatibility remains unsupported. The targeted iteration implements
one manual backup behavior and stops after that implementation; it must not mark
FTB Backups itself or FunCraft as native-compatible. RLCraft's separate evidence
gap does not disappear because FunCraft can be inspected.
