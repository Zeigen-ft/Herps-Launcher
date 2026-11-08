# Native survival stage 4 — Plant Fiber Bandage 0.1.0

An optional, independently authored native survival feature. **All physical
Stage 4 gameplay is NOT RUN.** The user reports Stage 3's required Windows
checklist PASS; optional cases and Mac acceptance remain open.
This does not implement First Aid's limb health, wounds or body-part selection.
No original Java mod code/assets are included or executed.

## What to install

Use the [verified Windows test download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42478785820/artifacts/13617293283)
from run **42478785820**, source **`2ae01f44bdbee7847a1446db20ea1e336fb6a2c3`**.
Sign in to GitHub, download `Herps-Launcher-0.1.0-Windows-x86_64`, then right-click
the downloaded ZIP → **Extract All**. Find `Herps-Launcher-0.1.0-Windows-x64-Setup.exe`
in the extracted folder. Open PowerShell in that folder and verify it before running:

```powershell
Get-FileHash '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe' -Algorithm SHA256
```

The hash must be exactly:

```text
90e052befc716e74084c429a3b066a7624674a90a9efa81d9b73146b172572be
```

Stop if it differs. [The verification report](NATIVE_SURVIVAL_STAGE_4_VERIFICATION.md)
has the portable ZIP hash, CI results and remaining limits.
Close games/servers and back up existing
data. Keep earlier tested profiles untouched. See [INSTALLATION.md](../../INSTALLATION.md)
for legitimate matching Minecraft 26.3 resources and JDK 25 preparation.

1. Create/select a **new named disposable profile before creating any worlds**.
2. On Modpacks install **Flint Survival Starter**, then **Plant Fiber Bandage**.
   Confirm the correct disposable profile and that games/servers are closed.
3. Both start OFF. On Mods enable Flint Starter, then Bandage. Both must stay
   enabled and unchanged after making saves. Normal play requires no Rust/Cargo.
4. Gathering and Woodcutting are optional for this independent bandage trial.
   To test the whole current progression, install/enable them in order **before
   world creation** too. Their previous acceptance is not extended by this guide.
5. Use ordinary Home → **PLAY**, then create a new Survival world. Clean startup
   uses a separate diagnostic folder and does not test enabled profile content.

The package is `herspers_rl_bandage-0.1.0.hmod`, 39,277 bytes, SHA-256
`dad328e28bc8d7d79d2002d5651af29dc77997bd3f00910c6e4021182b217ee1`.
The paper artwork is a vanilla identifier reference: inspect the tooltip for
**Plant Fiber Bandage** instead of assuming ordinary paper is the new item.
Generic importing is refused; use the dedicated Modpacks card.

## Craft and use

Three **Plant Fibers**, each in a separate crafting slot, plus **one string**
produce **one Plant Fiber Bandage**. Any arrangement in the small 2×2 inventory
grid works. The unchanged starter recipe turns one wheat into three fibers;
three fibers make string. Thus two wheat can make six fibers: use three to make
string and the remaining three with that string for one bandage. Gathering's
knife-cut plants provide the alternative route if you enable that earlier stage.

Hold **use/right mouse button for two seconds** to complete use. The item uses
the existing consumable API, no eating particles/food and no custom limb model.
It grants ordinary **Regeneration I for five seconds** and consumes one in Survival.
The stack limit is 16. It has no special hand animation and may be used/wasted
at full health. Repeated use follows vanilla effect refreshing rather than
stacking levels. It does not remove poison, provide hunger or replace medical mods.

## Physical Windows checklist — every case NOT RUN

Record PASS / FAIL / BLOCKED / NOT RUN with the candidate run, source/installer
hash, Windows version, selected profile, mode and before/after counts.

1. Craft using three separate fiber slots and one string: check the output's
   name and count. Wrong inputs/amounts must not produce a bandage. Test 2×2
   first, then 3×3 separately. Check ordinary starter recipes still work.
2. Take controlled damage in this disposable world. Wait for ordinary recovery
   to settle and record health/food. Hold a bandage in the main hand and use it
   for two seconds. Check one item is consumed, the Regeneration effect appears
   briefly and health can recover over five seconds. Natural hunger healing,
   other effects or further damage can make this inconclusive: record them.
   A data/fixture check does not establish physical heart recovery.
3. Interrupt use early by releasing the button. Check that an incomplete use
   does not consume an item or grant a new effect. Test item switching, off-hand
   use, repeated use and full-health use as separate cases; do not infer passes.
4. At full hunger check use is possible; it should supply no food. In a separate
   Creative trial confirm the usual retained-item behavior. Record mode each time.
5. Keep unused bandages in inventory and a chest. Save/quit and completely close
   game/launcher. Restart both and load the same world; check counts and other
   starter items. Effect save/load/expiry is a separate timing-sensitive case.
6. Compare an untouched earlier profile and its external backup. Check unrelated
   worlds and FunCraft backups remain intact. Do not overwrite/restore onto an
   existing save. Combined-stage gameplay and restoration need separate trials.

Use Home → **Open launcher and game logs** for failures. Give the exact recipe,
item name, hand, hold duration, health/food, other active effects and counts.
Redact tokens, account details, personal paths and server addresses; do not upload
copyrighted resources or valuable saves. Earlier startup stalls and initially
empty Chainmail output remain unresolved observations.

All Stage 4 Mac builds/gameplay and multiplayer remain NOT RUN. Java Mods
Build/Test and whole-Modpack Play stay disabled. Full RLCraft/FunCraft/First Aid,
thirst, temperature, skills, new creatures and world generation remain unsupported.
