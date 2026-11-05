# Herps Launcher 0.1.0 — internal release candidates and notes

Updated **2026-11-06, Asia/Singapore**. Branch:
`feature/herps-java-compatibility`. **Public release is not approved.**

## Release-readiness assessment

The first small RLCraft-inspired gameplay replacement has **user-reported
physical Windows evidence in both Survival and Creative**: enabled launch,
both recipes, boots equipped with **+1 Armor**, and both items retained after
completely closing/restarting the game and launcher and reopening the same
world. This report is tied to [Windows run 42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443)
at `8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`, not every subsequent build.
See [exact physical/automated evidence and hashes](../targeted-porting/RLCRAFT_CHAINMAIL_VERIFICATION.md).

An earlier **loading-logo stall** and **initially empty recipe output** remain
unresolved observations. Later launches/crafting succeeded; no cause or fix is
claimed. Reproduce/triage these with logs before stable promotion. This
documentation/candidate preparation step claims no new gameplay fix.

| Target | Physical evidence | Release gate |
| --- | --- | --- |
| Windows x64 | Five reported checks PASS on the original candidate, Survival and Creative | Partial acceptance; remaining edge/preservation cases and startup/crafting observations stay open |
| macOS Intel | Gameplay **NOT RUN** | Native artifact verification and full physical acceptance required |
| macOS Apple Silicon ARM64 | Gameplay **NOT RUN** | Native artifact verification and full physical acceptance required; distinguish runner OS from deployment support |

Unreported physical cases remain **NOT RUN**: wrong inputs/layouts and offsets,
shift/repeated inventory accounting and duplication, chest persistence,
durability, backup restore, cross-profile hash preservation, clean install/
upgrade/removal, failure recovery, developer-tools-absent setup and explicit
graphics/audio/shader/multiplayer checks. CI fixtures cannot pass these gates.
The [Phase 5D security/distribution gates](phase5d-release-readiness.md) remain:
native/Qt dependency and notice/source obligations, warning disposition,
publisher trust and real Gatekeeper/SmartScreen behavior. Those audits are
historical; no fresh all-dependency vulnerability clearance is asserted.

## Release notes

- Optional **Chainmail Plate and Boots 0.1.0**: four iron nuggets in a 2×2 square
  make one plate; four plates in the boots pattern make vanilla chainmail boots.
  The plate uses vanilla nugget artwork with its own item name/ID.
- One data-only native `.hmod`, with MIT/GPL notices. No original JAR, Forge/JVM
  bridge, Java execution or engine rewrite.
- **Disabled by default.** Installation needs an explicitly selected fresh
  disposable named profile and confirmation that games/servers are closed.
  Enable separately on Mods before creating a test world. Existing saves,
  profiles and FunCraft backups retain their safeguards.
- Disabling/removing with saves and launching a saved managed profile with
  missing/modified/disabled content are blocked. Missing-item recovery is
  unverified; do not delete receipts or bypass protections.
- Existing seven-page launcher and FunCraft-hotfix manual backup remain. Java
  Mods Build/Test and whole-Modpack Play remain disabled. **No full RLCraft or
  FunCraft compatibility**, Reskillable gate, extra integration recipes,
  Forge-world migration or arbitrary Java-mod support is claimed.

## Candidate downloads and checksums

Three-platform builds are being prepared from one documentation update with
gameplay/application code unchanged from `8fb33fb`. **Pending builds have no
approved download/hash yet.** The completed table will be on the feature branch:
https://github.com/Zeigen-ft/Herspers-Minecraft/blob/feature/herps-java-compatibility/docs/herps/release-candidates-0.1.0.md

| Target | Build/download | Package SHA-256 | Native verification |
| --- | --- | --- | --- |
| Windows x64 | PENDING new candidate; original verified run linked above | PENDING | Original: 421 source cases, 14 platform skips; 68 installed cases passed without skips |
| macOS Intel x86_64 | PENDING | PENDING | NOT RUN for this candidate |
| macOS Apple Silicon ARM64 | PENDING | PENDING | NOT RUN for this candidate |

Architecture-independent content: `herspers_rl_chainmail-0.1.0.hmod`, 40,002 bytes,
SHA-256 `015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346`.
CI receipts retain `gameplay_verified: false`; the
[separate human ledger](../targeted-porting/CHAINMAIL_WINDOWS_PHYSICAL_EVIDENCE.json)
records the five physical passes. Later candidates need their own acceptance,
even with identical content/application code. Builds have traceable pinned
inputs; bit-for-bit reproducibility of installers/DMGs is not claimed.

## Download, verify and install

1. Select the exact architecture and successful run in the completed table.
   Sign in to GitHub if required, download its **Artifacts** ZIP and extract
   into a new empty folder. Artifacts expire; do not substitute another run
   merely because the artifact name matches.
2. Verify the **inner installer/DMG** against this report and extracted
   `SHA256SUMS`. The outer artifact ZIP has a separate hash. Stop on mismatch.
3. Close games/launchers/servers and externally back up existing support data
   before replacing an installation. Keep the previous candidate. Use only new
   disposable profiles; never import a valuable or Forge save.

### Windows 11 x64

In PowerShell, from the extracted folder:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
```

Compare all 64 hexadecimal digits. Install into a short ordinary folder you
own; excessively long destinations are rejected. For portable use, independently
verify/extract the inner application ZIP into a separate folder and run
`Herps Launcher\Herps Launcher.exe`, keeping its `_internal`, game and source
folders together. Install the Microsoft Visual C++ x64 runtime if the package
guide requires it. The candidate is unsigned: review the source/hash and any
per-app Windows prompt; do not disable antivirus/global protection.

### macOS Intel or Apple Silicon

Check **Apple menu → About This Mac**. Choose x86_64/Intel for Intel, and
arm64/Apple Silicon for an Apple chip. Do not infer architecture from the model
name alone. macOS 15 is the baseline candidate target; 12–14 and newer OSes stay
experimental until individually tested. A macOS 26 build must be labelled
experimental and cannot certify macOS 15.

In Terminal, substitute the exact DMG filename from the table:

```bash
shasum -a 256 '/path/to/Herps-Launcher-0.1.0-EXACT-TARGET.dmg'
hdiutil verify '/path/to/Herps-Launcher-0.1.0-EXACT-TARGET.dmg'
```

Open the verified DMG and copy **both `Herps Launcher.app` and `Herspers Minecraft.app`**
to Applications. Eject the DMG; start Herps Launcher from Applications/Finder.
These apps are **ad hoc signed, not Developer ID notarized**. Record downloaded
quarantine/Gatekeeper behavior. If macOS offers **System Settings → Privacy &
Security → Open Anyway**, review the verified source/hash before choosing it.
Do not strip quarantine, disable Gatekeeper or treat CI signature checks as
publisher authentication. Retain `engine-source` separately only for deliberate
trusted native source-mod compilation; this content feature needs no Rust/Cargo.

### Prepare resources and test

Follow [resource preparation](../HERPS-QUICKSTART.md#2-prepare-resources-and-play)
with **JDK 25**, your own matching **Minecraft Java 26.3** files and matching
official server JAR. Windows: run the included game's `Setup.cmd`. Mac:

```bash
"/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
```

This prepares resources; it does not run Java mods. Validate the installation
in Settings. On Home create a fresh named disposable profile. On Modpacks
confirm that profile/closed processes, install chainmail crafting, verify **OFF**
on Mods, then enable explicitly. Use **Home → PLAY** and follow the
[crafting/save-relaunch checklist](../targeted-porting/WINDOWS_CHAINMAIL_ACCEPTANCE.md).
Use the same crafting steps on Mac, while keeping every Mac gameplay case
**NOT RUN** until actually performed. See the
[native acceptance protocol](native-acceptance.md) for installation/input/audio,
preservation and recovery. Keep the pack enabled once saves exist.

## Failures, logs and release decision

For the stall/empty output, retain run/hash, OS/GPU, profile, enabled mod state,
resource version, grid contents and waiting time. Preserve the stopped disposable
profile and logs. Do not invent a cause, overwrite a save or bypass guards.
Home → **Open launcher and game logs** opens the launcher support folder:
Windows `%LOCALAPPDATA%\Herspers Minecraft\herps-launcher`; Mac
`~/Library/Application Support/Herspers Minecraft/herps-launcher`.

Report PASS / FAIL / BLOCKED / NOT RUN per case. Redact credentials/tokens,
private paths/accounts, IPs and server information before sharing excerpts.
Do not upload game resources, proprietary JARs or valuable worlds. Retain the
earlier unsuccessful observations alongside subsequent passes.

**Internal release candidates only.** No main merge, tag, public release or
existing-release change is authorized by this preparation.
