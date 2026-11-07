# Native survival remake — stage 1: Flint Survival Starter

Experimental native content for the existing Rust engine. This is the first
playable starter loop in a staged RLCraft-style remake, **not a complete RLCraft
or No Tree Punching port**. It is independent of the original modpack import.
No original Java code, textures or Forge execution is included.

The engine repository was renamed during this work. Its commit and prepared
source bytes remain unchanged; [archive equivalence evidence](UPSTREAM_RENAME_VERIFICATION.json)
records every member comparison. Download metadata and cache identities were
updated while retaining the old archives and source caches.

## Included gameplay

Four new items and five **additive** crafting recipes:

| Input | Output |
| --- | --- |
| One vanilla flint, anywhere in the grid | Two Flint Shards |
| One vanilla wheat, anywhere in the grid | Three Plant Fibers |
| Three Plant Fibers in separate cells, any arrangement | One vanilla string |
| Flint Shard above a vanilla stick in the same column | One Flint Knife |
| Shard and string across the top; a stick under the string | One Flint Hatchet |

Knife pattern (2×2 inventory grid):

```text
shard  empty
stick  empty
```

Hatchet pattern (2×2 inventory grid):

```text
shard  string
empty  stick
```

The knife copies vanilla wooden-sword components with **32 durability points**;
the hatchet copies wooden-axe components with **48 durability points**. The
native components provide weapon/tool behavior. The user reports representative
knife damage/wear and hatchet log-mining/drops/wear PASS; exact durability,
breakage and other interactions still need testing. Repair ingredients are removed rather than
silently allowing wooden-plank repairs. Vanilla tools and recipes are unchanged.

Names distinguish the items from their referenced vanilla artwork: shard looks
like flint, fiber like wheat, knife like a wooden sword, hatchet like a wooden
axe. No Minecraft artwork is distributed in this package.

## Deliberate stage-1 differences

Shards are crafted in a grid; stone-click knapping is not implemented. Fiber is
crafted from wheat; cutting grass for fiber is not implemented. Ordinary vanilla
tree punching remains available. These choices make this stage independently
playable through existing APIs without pretending to implement the original
early-game restrictions. There is no thirst, temperature, skill gate, limb-health
system, new creature or Forge-world conversion. Multiplayer is NOT RUN and the
hosting console does not automatically copy profile mods into its separate server.

## Install the internal candidate

Use [successful Windows run 42383285455](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455),
built from `005fe80c3e11a396fbdbc54d1ad3f9bbbac08d15`:

- [Windows installer and portable package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455/artifacts/13580207560)
- [Separate native starter `.hmod` and engine validation](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42383285455/artifacts/13580237290)
- [Exact SHA-256 checksums](NATIVE_SURVIVAL_STAGE_1_SHA256SUMS.txt)
- [Verification report](NATIVE_SURVIVAL_STAGE_1_VERIFICATION.md)

Each Actions download is an outer ZIP; extract it first. The Windows artifact
contains `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` and a longer-named portable
ZIP. Use the installer, or fully extract that inner portable ZIP before use.
For example, in PowerShell opened in the extracted download folder:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
```

Expected installer SHA-256:
`8f078900216f380956754b25248d51924e202d2a1917c8f92a1547e7337dcae0`.
The standalone package is `herspers_rl_flint-0.1.0.hmod`, **42,887 bytes**, SHA-256
`919745713d5233bcd4cfee4f3da04328d3808eb06b24df966f26b054a69b81cc`.
It is already bundled with the new candidate; use the dedicated installer card.

Older published
installers do not have this new guarded installer/card. Do not replace a released
installer/checksum with this experimental build.

1. Back up the complete stopped support folder using the existing
   [installation guide](../../INSTALLATION.md#back-up-worlds). Keep valuable
   worlds and their previous launcher/content versions untouched.
2. Install/extract the candidate normally. Prepare your own legitimate
   Minecraft Java 26.3 resources with JDK 25 and validate the installation.
   If your existing 26.3 resources already pass validation, reuse them; no new
   resource export is required by this data-only stage.
3. On Home create/select a **new disposable named profile**, such as
   `flint_stage1_trial`. Do not create a world yet.
4. Open Modpacks and scroll to **Native survival remake · Stage 1: Flint Survival Starter**.
   Confirm the selected profile is disposable and all clients/servers are closed.
   Click **Install flint survival starter · disabled initially…** and confirm.
5. Open **Mods**, select **Flint Survival Starter**, and enable it explicitly.
   It starts OFF. Do not import an original RLCraft ZIP or enable Java Build/Test.
6. Use Home → ordinary **PLAY** and create a new **Survival** world. Clean startup
   uses a different diagnostic folder and is not the selected modded profile.

Install is refused for default profiles and profiles with saves. Installation,
settings and ownership receipts are profile-local. Once saves exist, disabling or
removing managed content is blocked; missing/edited/disabled content blocks that
profile's launch. Keep it enabled. These guards are not a missing-item recovery tool.
The original Chainmail Plate and Boots 0.1.0 package and hash are unchanged.

## Physical Windows acceptance checklist

The user reported **ALL PASS** for the shorter chat Survival checklist on
8 November 2026. Its scope covers launch, five recipes, representative tool use,
wrong/repeated/shift crafting and full-restart item/damage persistence. See
[the physical report](FLINT_WINDOWS_PHYSICAL_EVIDENCE.json). Chest, repair,
breakage, combined-mod and preservation/failure cases below remain open; the reply
did not reconfirm the exact installer, OS build or mode separately.

1. Obtain **two flint, two wheat and two sticks** through normal survival play.
   Existing vanilla wood gathering remains available. Confirm the profile/mod
   name and record starting counts.
2. Craft both flints into four shards and both wheats into six fibers, then take
   **one** string from three fibers. Craft the knife and
   hatchet with the patterns above. Expect one of each tool and exact ingredient
   use, leaving two spare shards and three spare fibers. Invalid ingredients/
   layouts must give no output or consumption.
3. Compare the hatchet on ordinary logs against a wooden axe and an empty hand.
   Check normal drops and tool wear. Use the knife as a sword, check damage/wear,
   and record results. Tool durability points are not a promise of the same
   number of uses: attacking/mining can consume different amounts.
4. Test repeated/stacked crafting separately for correct counts and no duplication.
   Check tool breakage and that wooden planks are not accepted as inherited repair
   ingredients. Combining identical damaged tools is a separate untested case;
   this stage does not claim to disable every possible repair operation.
5. Keep both tools, a spare shard and fiber in inventory. Save and quit normally.
   Close the game and launcher completely. Reopen the same profile/world and
   confirm names, counts and previously accumulated durability damage remain.
6. Test chest persistence and another save/reload separately. Hash external
   backups/other profiles before/after to check preservation. Never overwrite an
   existing save to test restoration.
7. For an optional coexistence check, use another fresh disposable profile and
   install/enable both chainmail and flint **before** creating a world. Repeat
   both crafting loops and the full restart/inventory checks. Keep your earlier
   chainmail world untouched; this combined physical case is NOT RUN.

Use PASS / FAIL / BLOCKED / NOT RUN. An automated NBT/resource/recipe fixture is
not real survival, combat, rendering, ingredient consumption or world loading.
All physical macOS gameplay also remains NOT RUN. Existing earlier logo stalls
and initially empty chainmail recipe output are not claimed fixed by this work.

For a failure use Home → **Open launcher and game logs**. Supply candidate run,
commit/package hash, OS/GPU, selected profile, mode, exact grid/item counts and
expected/actual result. Review excerpts and redact account details, tokens and
personal paths; do not upload copyrighted game resources or valuable worlds.

## Following stages

1. Retain the reported basic starter-loop passes; finish remaining physical edge
   cases, adjust verified defects and preserve installed content identity.
2. Evaluate grass-fiber harvesting and stone knapping against the existing
   native hooks, with one exact behavior and preservation test at a time.
3. Treat thirst/temperature, skills/limb damage and combat as separate saved-state
   features. Any required major engine/API change needs approval before it starts.
4. Creatures, structures and world generation need separate source/asset rights,
   native implementation, performance and real save/load evidence. No stage
   automatically certifies the original 177-mod RLCraft pack.
