# Native survival stage 3 — Woodcutting Progression 0.1.0

Optional native RLCraft-style progression. On 8 November 2026 the user confirmed
**all required Stage 3 Windows checklist tests passed** for run `42472666400`.
This is [user-reported evidence](WOODCUTTING_WINDOWS_USER_REPORT.json), not
Codex-observed gameplay. Optional edge cases and all Mac acceptance remain open.
No original Java mod, bridge or full No Tree Punching implementation is included.

## What changes

With the add-on enabled, **Survival** log breaking requires a **usable Flint
Hatchet or an item in the game's axe tag, held in the main hand**. Empty hands,
knives, swords, pickaxes, empty stacks and broken tools cannot authorize it.
An axe in the off hand alone does not count. A rejected attempt keeps the log
and gives no drops; a message asks for a hatchet or axe. A predicted crack may
briefly show before the server corrects it.

The rule follows the existing `minecraft:logs` block tag, including tagged wood,
stripped logs and stems. It respects earlier cancellations. Allowed breaking
uses the engine's normal drops, wear and updates. It does not implement tree
felling, alter recipes or award items itself. Other modes and non-log blocks
keep their previous behavior. The existing crafting and gathering packages are
unchanged and remain usable without this optional add-on.

**Leaves and dead bushes are not restricted.** Their existing stick drops are
the intended early Survival route. Drops can be random; not every leaf produces
a stick. The automated probe checks owned vanilla-shaped drop fixtures through
the native loader; actual legitimate-resource drops and the complete natural
progression still require physical testing. If sticks cannot be obtained, record
that as BLOCKED/FAIL and stop the trial rather than changing a valuable world.

## Install the internal candidate

Use the [verified Stage 3 Windows test download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42472666400/artifacts/13615181805)
from run **42472666400**, source **`9f196479726ed69e959665a9604133daf58dcde1`**.
Sign in to GitHub, download `Herps-Launcher-0.1.0-Windows-x86_64`, then right-click
the downloaded ZIP → **Extract All**. Open the extracted folder and find
`Herps-Launcher-0.1.0-Windows-x64-Setup.exe`.

Before running it, open PowerShell in that extracted folder and enter:

```powershell
Get-FileHash '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe' -Algorithm SHA256
```

The hash must be exactly:

```text
079af345af99d93d34b54bc4bb6361f849f42ddb6cd9e31adf97f90ec1c89458
```

Stop if it differs. [The verification report](NATIVE_SURVIVAL_STAGE_3_VERIFICATION.md)
has the portable ZIP hash, detailed CI results and remaining limitations.
Earlier installers cannot provide this restriction.
Normal use needs no Rust/Cargo or Visual Studio. Keep existing tested installers
and profiles until this new disposable trial is accepted.

1. Close games and servers; externally back up the complete stopped support
   folder. Follow [INSTALLATION.md](../../INSTALLATION.md) for installation,
   legitimate matching Minecraft 26.3 resources and JDK 25 preparation.
2. Create/select a **new disposable named profile**, for example
   `wood_stage3_trial`. Do not create a world yet.
3. On Modpacks install **Stage 1: Flint Survival Starter**, then **Stage 2: Flint
   Gathering**, then **Stage 3: Woodcutting Progression**, using each confirmation.
4. On Mods explicitly enable the starter, gathering, then woodcutting. All start
   OFF. Only then use Home → ordinary **PLAY** and create a new Survival world.
   Clean startup uses a different diagnostic folder.

The new tag-only package is `herspers_rl_woodcutting-0.1.0.hmod`, **37,184 bytes**,
SHA-256 `52e3586e103e4893f37f2141983a7503fa01dacb494144056f86897089abbc13`.
Its behavior is a small original MIT extension in the candidate's native client;
the content package/launcher are GPLv3. It adds no items, recipes, public hook API,
network service or save schema. Old engine metadata is refused. Both earlier
stages are required. The older three package hashes remain unchanged.

Install refuses default profiles and any profile with saves. Keep all packages
enabled after making worlds; managed disabling/removal is then blocked, and
missing/tampered/disabled dependencies block launch. These are preservation guards,
not recovery tools. Leave them enabled in the game's Mods screen too. Do not
overwrite a save or add this restriction to a previously tested world.

## Real Windows acceptance — required checklist PASS, user reported

The user reports all required numbered checks below passed. No per-case logs,
measurements, exact OS build or profile details were supplied. The instructions
alone are not evidence; the separately retained user reply is the evidence.
For future trials record candidate run/source, installer hash, Windows build,
profile, mode and PASS / FAIL / BLOCKED / NOT RUN. Optional cases stay unconfirmed.

1. In the new Survival world, try an ordinary log with an empty main hand.
   Expect the log to remain, no drops and the axe message. Once tools are
   available, try a knife/pickaxe/sword too. An off-hand-only hatchet must not
   allow the empty or wrong main hand to break the log.
2. Break leaves or dead bushes by hand until you have **two sticks**. Record
   attempts and results. Obtain two flint normally; right-click stone tops to
   make four shards. Craft the knife with a shard above a stick.
3. Cut three short-grass/fern plants with the knife, make string from their
   three fibers, and craft the existing hatchet. Expect one knife, one hatchet
   and two spare shards, with normal knife wear. No wheat is needed for this route.
   All recipes fit the small 2×2 crafting grid in your inventory:

   ```text
   Knife:                 Hatchet:
   [Flint Shard] [empty]  [Flint Shard] [String]
   [Stick]       [empty]  [empty]       [Stick]
   ```

   To make one string, place three Plant Fibers in three separate crafting
   slots. Use the modded **Flint Shard**, not plain vanilla flint, in these recipes.
4. Put the hatchet in the **main hand**. Break logs: check normal drops and wear,
   then make a vanilla axe and repeat. Check ordinary and stripped logs/wood
   where available; optional stems require their own recorded case.
5. Check leaves, bushes, planks and stone remain governed by vanilla behavior.
   Other game modes need separate disposable worlds and their own results.
6. Save/quit and completely close game and launcher. Restart both and reopen
   the same world: verify items, counts, damage and removed blocks persist.
   Chest persistence, exact breakage/repair, enchantments, failures and multiplayer
   are separate unverified cases.
7. Use another fresh profile with **Stages 1 and 2 only** to confirm their old
   recipes/actions and ordinary tree punching. Keep the earlier tested profiles
   untouched. Combined Chainmail gameplay and backup restoration need separate trials.

For failures use Home → **Open launcher and game logs**. Give mode, block/tool,
which hand, counts, expected/actual result and whether the message appeared.
Redact tokens, account details, personal paths and server addresses. Do not
upload copyrighted game resources or valuable saves.

All macOS builds/gameplay for this stage and multiplayer remain NOT RUN. No
thirst, temperature, skills, limb damage, creatures, world generation or original
Forge/Fabric execution is added. Java Mods Build/Test and whole-Modpack Play stay
disabled. Earlier logo stalls and initially empty chainmail output remain
unresolved observations. No public release approval is inferred from testing.
