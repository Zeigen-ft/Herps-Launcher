# Chainmail Plate and Boots — implementation verification

Baseline: `4520bb66a13257ac45cc4de8a7de1b6c67718eff`, feature branch
`feature/herps-java-compatibility`. Independent native replacement for the
[approved small gameplay proposal](RLCRAFT_293_FIRST_GAMEPLAY_FEATURE.md).

Implemented: a code-free API 0.2 `.hmod`, one iron-nugget-template plate,
four nuggets in a square → one plate, four plates in the boots pattern → one
vanilla chainmail boots item. Includes MIT attribution to Kfir Awad (2019) and
the new definitions' GPL notice. No original JAR or texture is shipped.

Package SHA-256:
`015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346`
(40,002 bytes). ZIP metadata/order and LF-normalised text are deterministic.

Installation requires explicit confirmation of a fresh named disposable
profile and closed games/servers. It starts disabled and requires a separate
enable on Mods. Existing saves, namespace collisions, linked paths, busy
operations and changed package bytes fail closed. Removing/disabling with
saves is blocked; missing/changed/disabled managed content blocks launching
that saved profile. Empty-profile removal retains a backup.

Local automated validation: **420 tests, 405 passed, 15 platform skips**.
Pinned native `Package::read` / `Content::read` also passed on Linux.
Windows candidate, native recipe matcher and installed frozen acceptance:
**pending CI in this build-time copy**. The feature branch's current copy of
this report will record the completed run, downloads, hashes and failures:
https://github.com/Zeigen-ft/Herspers-Minecraft/blob/feature/herps-java-compatibility/docs/targeted-porting/RLCRAFT_CHAINMAIL_VERIFICATION.md

Physical Windows 11 survival crafting, graphics/audio, equipping, actual shift
consumption, prepared legitimate resource IDs and custom-item save/load/relaunch:
**NOT RUN**. macOS ARM64/Intel acceptance: **NOT RUN**. No real gameplay or full
RLCraft compatibility is claimed. Headless fixtures are not gameplay evidence.

Follow the [Windows survival acceptance guide](WINDOWS_CHAINMAIL_ACCEPTANCE.md).
Stop on bad consumption, duplication, missing items, corrupted saves or any
cross-profile change. Keep test content enabled while its worlds exist.

Unsupported: Forge/Java execution, arbitrary ore aliases, Reskillable Defense
gate, other armor recipes, Wolf Armor/Varied Commodities/Lycanites integration,
old save migration and complete modpack Play. Java Mods Build/Test and imported
whole-Modpack Play remain disabled. No engine source change, main merge, tag or
public release is part of this work.
