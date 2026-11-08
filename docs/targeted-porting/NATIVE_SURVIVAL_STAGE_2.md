# Native survival stage 2 — Flint Gathering 0.1.0

Experimental, optional native gathering. The user replied **ALL GOOD** after
receiving this Windows candidate and guide. This is overall user-reported positive
feedback; individual test cases were not itemized. See [the report](GATHERING_WINDOWS_USER_REPORT.json).
**macOS gameplay remains NOT RUN; full native acceptance remains open.**
Stage 1 results remain evidence for that earlier candidate. This is not original
No Tree Punching or full RLCraft.

## New actions

In **Survival** only, with both starter and gathering enabled:

| Action | Result |
| --- | --- |
| Hold ordinary flint; right-click the **top** of stone or cobblestone. | Consume one flint; put two existing Flint Shards into inventory. Stone stays. |
| Hold the existing Flint Knife; right-click **short grass or a small fern**. | Remove that plant; put one existing Plant Fiber into inventory; apply one point of normal knife wear. |

These are right-click actions. Ordinary left-click breaking keeps its previous
behavior. Tall grass, large ferns, crops, flowers, dirt and side/bottom stone faces
do not gain these actions. Creative, Adventure and Spectator are excluded.
Renamed/component-modified vanilla flint is refused; damaged knives still work.
Normal durability/enchantment handling applies; precise breakage needs testing.
Cutting awards fiber instead of vanilla seeds. There is no new custom sound.

There must already be room for the **whole** output. Otherwise nothing is
consumed, removed or worn, even if consuming the last flint could free a slot.
No overflow is dropped. Existing shard/wheat/fiber/tool recipes and vanilla tree
punching remain. No thirst, temperature, skills, limb damage, mobs/world generation,
Java/Forge execution, bridge, new network dependency or save format is added.

## Install in a new test profile

Use [successful Windows run 42445241045](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045), built from
`b75897fdf84b06caad2d8c230759483a4e40a0e1`. Download the [Windows artifact](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045/artifacts/13603683988).
Extract the outer ZIP. Use `Herps-Launcher-0.1.0-Windows-x64-Setup.exe`, or fully extract
its inner portable ZIP before starting it. GitHub may require sign-in.
An old Stage 1 installer cannot supply these interactions. Normal use needs no
Rust/Cargo or Visual Studio installation.

In PowerShell opened in the extracted download folder:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
```

Expected installer SHA-256:
`e4c3d3584a743e0482d8f69dd447e1d0a9b599b9946657c82139e1d9f0fd887c`.
[All checksums](NATIVE_SURVIVAL_STAGE_2_SHA256SUMS.txt) and
[the automated report](NATIVE_SURVIVAL_STAGE_2_VERIFICATION.md) are separate from
the user report and the detailed physical checklist below.

1. Close all games/servers and externally back up the stopped support folder.
   Keep tested Stage 1/Chainmail profiles and valuable worlds untouched.
2. Install/extract the new internal Windows x64 candidate. Validate its installation.
   Reuse legitimate matching Minecraft 26.3 resources if they pass validation;
   preparation still needs JDK 25. Follow [INSTALLATION.md](../../INSTALLATION.md).
3. On Home create/select a **new disposable named profile**, such as
   `flint_stage2_trial`. Do not create a world yet.
4. On Modpacks install **Stage 1: Flint Survival Starter** with its confirmation,
   then **Stage 2: Flint Gathering** with its separate confirmation. Each starts OFF.
5. On Mods enable **Flint Survival Starter first**, then **Flint Gathering**.
6. Use Home → ordinary **PLAY** and create a new Survival world. Clean startup
   uses a separate diagnostic folder, not this selected modded profile.

A short new Survival route is **two flint + two sticks + three short-grass/fern
plants**. Knap the flint into four shards, craft one knife, cut three plants,
craft their three fibers into string, then craft the hatchet. Expect one knife,
one hatchet and two spare shards, with normal knife wear from cutting. Wheat is
still a supported alternate recipe, but this route does not require it. This
route is a manual test instruction, not a claim that it has passed.

The add-on `herspers_rl_gathering-0.1.0.hmod` is 37,136 bytes; SHA-256:
`177c3f4eefedd4f0e4eda4e54634efeee555e4b22dd13e0ec022733328fb87fd`.
It supplies an opt-in item tag, not executable code. A small original MIT engine
extension uses the existing item-use hook; it adds no public hook API. Older
client metadata is refused. Starter and Chainmail package bytes remain unchanged.

Install is refused for default profiles or any profile with saves. Keep both
packages enabled after creating worlds. Managed disabling/removal is then blocked;
missing/tampered/disabled content or a missing starter blocks launch. This is not
a missing-item recovery tool. Leave both enabled in the in-game Mods screen too;
restart after content changes. Never overwrite an existing save for a test.

## Real Windows checklist — individual results still to confirm

The overall reply **ALL GOOD** does not identify which of these steps were run.
No separate case is marked PASS from that reply. For detailed evidence, record
PASS / FAIL / BLOCKED / NOT RUN, candidate run/source commit, installer hash,
Windows build, profile name and mode. No programming tools are required.

1. Launch a new Survival world with both packages enabled. Obtain flint normally.
   Record counts. Right-click a stone **top** once: exactly one fewer flint,
   two more shards, stone unchanged. Repeat on cobblestone and with two flints.
   Check main hand and off hand separately: never consume the other hand's item.
   Holding the button can repeat actions; every conversion must cost one flint.
2. Try dirt, a stone side, an unrelated held item and opening a chest: no shards
   or consumption, and ordinary interactions still work.
3. Craft the existing knife. Right-click short grass, then a small fern. Each
   disappears once, gives one fiber and applies normal one-point knife wear
   without enchantments. Clicking the now-empty position gives no second fiber.
   Nearby plants stay unchanged. Try ordinary left-click/empty-hand grass breaking.
4. Fill inventory with disposable stacks. With no output space, repeat both:
   no lost flint, removed plant, output or wear. Test a shard stack with only one
   free space too. Make enough room and retry.
5. Verify all five previous Stage 1 recipes and tool use still work. Keep items
   and the worn knife in inventory and a chest. Save/quit, completely close both
   game and launcher, restart both and open the same world. Verify counts,
   names, removed plants and knife damage. Test exact knife breakage separately.
6. In another **fresh** disposable profile install Stage 1 only before making a
   world. Old recipes should work; new right-click actions should not. Combined
   Chainmail, backup restore, cross-profile hashes and installation lifecycle
   need their own results. Leave previously tested worlds untouched.

Use Home → **Open launcher and game logs** for failures. Give exact steps,
starting/ending counts, block/face, hand and expected/actual result. Review log
excerpts and redact tokens, account identifiers, personal paths and server
addresses. Do not upload copyrighted resources or valuable saves.

All physical macOS gameplay, multiplayer and dedicated-server distribution are
NOT RUN. Native builds/owned fixtures are not gameplay. Earlier loading-logo
stalls and initially empty chainmail output remain unresolved observations.
Public release approval is not inferred from development or either stage's user feedback.
