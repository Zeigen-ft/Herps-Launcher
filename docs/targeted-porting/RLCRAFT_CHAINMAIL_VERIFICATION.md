# Chainmail Plate and Boots 0.1.0 — verification

Updated **2026-11-06, Asia/Singapore**. Branch:
`feature/herps-java-compatibility`. Approved baseline:
`4520bb66a13257ac45cc4de8a7de1b6c67718eff`; verified gameplay implementation:
`8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`.

**Five user-reported physical Windows checks PASS. Crafting and inventory
persistence were confirmed in both Survival and Creative.**
Complete native acceptance and all Mac gameplay remain open. See the
[release notes, current candidate hashes and installation instructions](../herps/release-candidates-0.1.0.md).

## Implemented scope and safeguards

One code-free API 0.2 `.hmod`: four vanilla iron nuggets in a square make one
Chainmail Plate; four plates in the boots pattern make vanilla chainmail boots.
The plate uses an iron-nugget template and vanilla artwork references. MIT
attribution to Kfir Awad (2019) and the new definitions' GPL notice are included.
No original JAR, Java/Forge execution, texture copy or engine rewrite is included.

`herspers_rl_chainmail-0.1.0.hmod`: **40,002 bytes**, SHA-256:

```text
015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346
```

Installation requires explicit confirmation of a fresh named disposable profile
and closed games/servers. It starts disabled; enable separately on Mods before
creating a world. Existing saves, namespace collisions, links, busy operations
and changed package bytes fail closed. Disabling/removing with saves is blocked;
missing/changed/disabled managed content blocks launching that saved profile.
Empty-profile removal retains a package/receipt backup. These safeguards remain.

## User-reported physical Windows evidence

The user personally tested [run 42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443)
at source `8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`. When asked about game
mode they confirmed **both Survival and Creative**. Report received 2026-11-06;
execution date was not supplied. Windows 11 x64 was previously offered; exact
OS build/CPU/GPU and screenshots/logs were not supplied with this report.
These are **user-reported physical results**, not gameplay observed by Codex
or performed by CI.

| Physical check | Result | Observation |
| --- | --- | --- |
| Launch with native content enabled | PASS | Minecraft launched |
| Four iron nuggets → Chainmail Plate | PASS | Plate produced |
| Four plates → Chainmail Boots | PASS | Boots produced |
| Equip boots | PASS | Equipped successfully and displayed **+1 Armor** |
| Full exit/restart and same-world reopen | PASS | Completely closed Minecraft and Herspers Launcher; restarted both; reopened the same world; plate and boots remained in inventory |

**Unresolved observations:** an earlier loading-logo stall and initially empty
recipe output occurred. Later launches/crafting succeeded. No reproduction
rate, cause, diagnosis or fix is established. Later success does not resolve
these observations. Retain them as release-readiness issues and preserve logs
and reproduction details on recurrence.

The [physical ledger](CHAINMAIL_WINDOWS_PHYSICAL_EVIDENCE.json) records the exact
scope. CI receipts retain `gameplay_verified: false`; the human report is separate.
It does not physically accept later rebuilt installers/DMGs, even with unchanged
application code/content hash. Neither whole modpack is accepted.

## Completed automation and original Windows hashes

Run **42118750443**, job **127565239851**, succeeded:

- Windows source: **421 collected, 407 passed, 14 platform/input skips**, no
  failures. Local Linux: **421 collected, 406 passed, 15 skips**.
- Pinned native package/content loader and recipe matcher: **10 headless cases
  passed** (template/name/model, plate offsets, boots rows, invalid inputs/cells,
  stacked match count). Owned synthetic resources were used; this does not test
  real shift consumption, prepared legitimate resources or world persistence.
- Installed frozen suite: **68 passed, zero failures/skips**; seven pages,
  bundled helper, chainmail controls and FunCraft backup cases passed. Cargo,
  rustc and rustup were absent from PATH.
- Installer path rejection, install/replacement/uninstall/reinstall and existing
  profile/settings/save/backup sentinels passed. Owned native-mod compilation,
  binary selection/rollback and source/clean-binary preservation passed, with
  hook execution/gameplay explicitly unverified by that regression.

Complete artifacts and members were downloaded and independently SHA-256 hashed;
values match GitHub metadata, `candidate.json`, `SHA256SUMS` and installed receipts:

| Original Windows deliverable | Download / SHA-256 |
| --- | --- |
| Candidate `Herps-Launcher-0.1.0-Windows-x86_64` outer ZIP | [13458724088](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443/artifacts/13458724088), `688329c04d4497d79c545d19a77c49621f3a1364ee6e413c37164192628280c2` |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | `3943c72dd0bf8eb6dd45918c95696816de9891390c1173fccb4778156dae29b2` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-f1te66bc.zip` | `82f28bde3df89c7d90c870bd7b735de1b7b7ea39dca3e1298ae2acbfef5efefd` |
| Evidence outer ZIP | [13459478436](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443/artifacts/13459478436), `7455021f090d2f0f3329b4031f5ddf09f0c193589d8a85c872edfad95704dd37` |
| Standalone content/validation outer ZIP | [13458724093](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443/artifacts/13458724093), `0266a4086a995db1087c863edc3a9f80967e0eec40b4952c8e323ff963b6964a` |

The user identified the run, not installer versus portable use. Both hashes are
provided without inventing that choice. Artifacts expire; see the current notes
for newly prepared candidates and their own provenance/checksums.

## Remaining physical cases

**NOT RUN:** clean resource preparation from official matching files, all
invalid ingredients/layouts/offsets, exact repeated/shift-click
consumption and duplication, chest persistence, armor damage/durability,
cross-profile/save/backup hash preservation, physical backup restoration,
clean installation/upgrade/removal, missing-content/crash/disk/lock recovery,
developer-tools-absent physical setup, explicit graphics/audio/shaders and
multiplayer. **All macOS Intel/Apple Silicon gameplay remains NOT RUN.**

Follow the [Windows checklist](WINDOWS_CHAINMAIL_ACCEPTANCE.md). Keep the pack
enabled once saves exist. Stop on bad consumption, duplication, missing items,
save corruption or cross-profile changes. Never bypass content guards or use
valuable saves. A few passing observations cannot accept the remaining cases.

## Failed and superseded implementation attempts

- Initial local UI checks caught worker callback/layout errors, corrected before
  the verified candidate. An existing native port test hit socket EPERM in the
  sandbox; the permitted rerun passed without changing production port behavior.
- Run 42116385250 was superseded after backend regressions passed, to include
  malformed-receipt hardening that preserves metadata and displays an error.
- [42117119229](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42117119229)
  passed Windows regressions/game build, then failed because the external probe
  omitted pinned vendored winit/wgpu-hal overrides. Those overrides are retained now.
- Portable run 42118293976 found a Windows short/canonical-path fixture assertion;
  corrected before the final candidate. Candidate 42118293889 was superseded.
- Final portable run 42118746719 passed Linux/Windows: 421 cases each, 105/104
  explicitly recorded backend/platform skips. Full Windows run 42118750443 supplied
  real-backend/frozen coverage. Failed/superseded runs are not gameplay acceptance.

## Compatibility and release boundary

Unsupported: Forge/Java execution, bridges, arbitrary ore aliases, Reskillable
Defense gate, other armor recipes, Wolf Armor/Varied Commodities/Lycanites
integration and old-save migration. Java Mods Build/Test and whole-Modpack Play
stay disabled. FunCraft's manual backup is a separate small replacement;
**no full RLCraft or FunCraft compatibility is claimed**.

**Internal candidates only; public release not approved.** The two unresolved
observations, remaining physical cases and security/distribution gates remain.
No main merge, tag, new engine feature or public release is included.

## Fresh three-platform internal candidate set

[Run 42129264888](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42129264888) completed Windows x64, macOS 15 Intel and macOS 15
Apple Silicon candidates at `5bb63ec18088f2c7ae22b11bd63c7f092d91a6ff`. All packages/evidence were downloaded
and independently hashed. Each delivered launcher passed the 68-case frozen
cohort with no developer Rust tools on PATH; full per-platform counts, skipped
cases, artifact IDs, architecture and install instructions are in the
[release notes](../herps/release-candidates-0.1.0.md) and
[evidence index](../herps/release-candidates-0.1.0-evidence.json).

Application/content/build code is unchanged from `8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`. These
are fresh CI-verified candidates, not a transfer of the user's physical report
to new hashes or to Macs. All Mac gameplay and unreported physical cases remain
NOT RUN. The earlier stall/empty-output observations remain unresolved.
