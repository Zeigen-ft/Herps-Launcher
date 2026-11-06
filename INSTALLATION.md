# Complete installation and user guide

**Herspers Minecraft Launcher / Herps Launcher 0.1.0 — prerelease candidate**

Official home: [Zeigen-ft/Herps-Launcher](https://github.com/Zeigen-ft/Herps-Launcher).
For a shorter route, read [QUICK_START.md](QUICK_START.md).

This launcher starts a native Rust game client using **Minecraft Java Edition
26.3 resources**. It does not run original Forge/Fabric mods. Obtain Minecraft
and its resources legitimately; no game assets, accounts or third-party modpack
binaries are included.

## What has actually been verified

- **Verified by native CI:** architecture/build checks, package integrity,
  seven-page launcher navigation, bundled helpers, installed frozen workflows
  and preservation of owned synthetic test files. See
  [migration evidence](docs/migration/README.md) for destination results and hashes.
- **User-reported physical Windows PASS:** launch with native chainmail content,
  both recipes, boots equipped with **+1 Armor**, and plate/boots retained in
  inventory after fully closing/restarting Minecraft and the launcher and
  reopening the same world. Crafting and persistence were confirmed in both
  **Survival and Creative** on source run 42118750443. This is not certification
  of every rebuilt file, computer, inventory edge case or installation method.
- **NOT RUN:** all physical Mac gameplay, and unreported physical installation,
  resource-preparation, graphics/audio/shader, backup restore, failure recovery,
  shift-crafting and cross-profile preservation cases.
- **Unresolved:** an earlier loading-logo stall and initially empty crafting
  output. Later launches/crafting succeeded; their causes are not established
  or claimed fixed.

Instructions marked **documented / manual NOT RUN** match the implemented
workflow but are not claimed to have been personally tested on your hardware.
**Estimate** means planning advice, not a measured requirement or compatibility
promise. There are **no verified Windows/macOS installation screenshots available**
for this guide; no simulated or invented screenshots are presented.

## System requirements

No measured minimum RAM, CPU speed, free disk space or GPU model is established.
Use the estimates below as a starting point for a small disposable test world.

| Requirement | Minimum/target and evidence | Recommended planning estimate |
| --- | --- | --- |
| Windows OS/CPU | Windows 11 on Intel/AMD **x64** is the primary candidate target. User previously identified a Windows 11 x64 PC; exact build/CPU/GPU was not supplied. Native CI used Windows Server 2025 x64 | Current Windows 11 updates and vendor GPU drivers; not a claim that every PC is verified |
| Mac Intel | **x86_64** package; macOS **15** candidate baseline. Source CI ran macOS 15.7.9; physical gameplay NOT RUN | Stay within a recorded CI baseline for first testing; individual models still require testing |
| Mac Apple Silicon | **ARM64** package; macOS **15** candidate baseline. Source CI ran macOS 15.8.2; physical gameplay NOT RUN | An Apple chip with current supported drivers/OS; newer OS acceptance remains experimental |
| Older/newer OSes | Windows 10 x64 is legacy/experimental. Qt 6.8 requires macOS 12+, but 12–14 are experimental, not verified launcher targets. macOS 11 and older are unsupported. macOS 26/newer remains experimental | Do not downgrade a Mac just for this guide; record the actual OS and treat an untested combination as experimental |
| CPU | Correct 64-bit architecture is required. No minimum clock/core count has been measured | Four logical cores or more — **estimate** |
| Memory | No measured minimum; **8 GB RAM is a planning estimate**, not a verified floor | **16 GB or more — estimate**, particularly for preparation and larger worlds |
| Free disk | No measured minimum; **10 GB free is an initial estimate**, not a guarantee. Resources/worlds/backups vary | **20 GB+ on an SSD — estimate**; keep extra space for independent backups and updates |
| Graphics | Windows code offers Auto/Vulkan/DX12/OpenGL preferences; Mac uses Metal. No GPU/driver minimum or all-backend gameplay acceptance is established | Current vendor drivers; use Auto first. Optional shaders need separate testing |
| Java/tools | Full **JDK 25** for resource preparation, including `java` and `javac`. Normal installed use and chainmail need no Rust, Cargo, Python, Visual Studio or Xcode | Use a JDK matching the package CPU. Trusted native source-mod development is a separate advanced feature |
| Network/licence | Initial downloads, legally owned matching Minecraft Java files and official server JAR are required | A reliable connection for setup; account/server capabilities are not universally supported |

There is no native 32-bit Windows or Windows ARM64 package in this release set.
Running x64 Windows code through ARM emulation is not verified. Choose the native
Mac architecture rather than assuming Rosetta compatibility.

## Download the correct files

1. Open [the repository's Releases page](https://github.com/Zeigen-ft/Herps-Launcher/releases).
   The owner publishes releases manually. If none exists, use the successful
   **destination** CI links in [the migration report](docs/migration/README.md).
   The destination is currently private; only authorized users can access its
   releases/artifacts. This guide does not change repository visibility.
2. Check the version, prerelease label, source commit and known issues. Do not
   substitute older game-only or Bedrock packages with similar names.
3. Identify your computer:
   - Windows: Start → Settings → System → About → **System type**. Choose x64
     for a 64-bit Intel/AMD processor, not an ARM-based processor.
   - Mac: Apple menu → **About This Mac**. Intel means Intel; an Apple chip
     means Apple Silicon/ARM64. A model name alone is not enough.
4. Download the correct file plus `SHA256SUMS.txt`:

| Computer | Intended release asset |
| --- | --- |
| Windows x64 installer | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` |
| Windows x64 portable alternative | `Herps-Launcher-0.1.0-Windows-x64-Portable.zip` |
| macOS Intel | `Herps-Launcher-0.1.0-macOS-Intel.dmg` |
| macOS Apple Silicon | `Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg` |
| Optional standalone native content | `herspers_rl_chainmail-0.1.0.hmod` — already bundled; use the launcher's guarded installer |
| Guides/notices | `INSTALLATION.md`, `QUICK_START.md`, release notes and licence notices |

CI artifacts are **outer ZIP downloads**. Extract the outer ZIP into a new empty
folder first. Platform CI members may retain longer build filenames; the release
bundle maps those real files to the names above without changing their contents.
Always use the matching manifest. The original app names inside the DMGs stay
`Herps Launcher.app` and `Herspers Minecraft.app`.

## Verify downloads

Do this before running an installer or opening a DMG. Compare the hash against
`SHA256SUMS.txt` from the same release/run, not a different build's notes.
A matching hash proves integrity, not an authenticated publisher signature.

### Windows

1. In File Explorer open the download folder. Click its address bar, type
   `powershell`, and press Enter.
2. Run:

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
   ```

3. Compare all **64 hexadecimal digits** with the same filename in
   `SHA256SUMS.txt`; upper/lowercase letters are equivalent. For portable use,
   replace the filename with the portable ZIP's name. Stop and redownload from
   the exact trusted run if any digit differs.

### Mac

Open Terminal and run, substituting your actual file path/architecture:

```bash
shasum -a 256 "$HOME/Downloads/Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg"
hdiutil verify "$HOME/Downloads/Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg"
```

For Intel use the Intel filename. Compare all 64 digits with the manifest.
`hdiutil verify` is an additional DMG-integrity check, not proof of notarization.
The outer CI artifact ZIP and inner installer/DMG have **different** hashes.

## Install the launcher

**Documented / physical installation NOT RUN.** Native CI tested disposable
installation/copy/removal workflows, not your machine's prompts or permissions.
If updating, [back up the complete support folder](#back-up-worlds) first.

### Windows installer

1. Close all Minecraft clients, Herps launchers and servers normally.
2. Extract the CI outer ZIP if applicable. Do not run files from inside a ZIP.
3. Run the verified `Herps-Launcher-0.1.0-Windows-x64-Setup.exe`.
4. Choose a short ordinary folder you own. The installer checks payload path
   length; if rejected, choose a shorter path rather than changing Windows policy.
5. Select the optional desktop shortcut if wanted; finish installation.
6. Open **Herps Launcher** from Start or its shortcut. If the package reports a
   missing Visual C++ runtime, install the official
   [Microsoft Visual C++ x64 runtime](https://aka.ms/vc14/vc_redist.x64.exe).

The Windows package is **unsigned**. Review its repository, version and hash
before trusting a per-app Windows prompt. Do not disable antivirus or SmartScreen
globally. If your organization blocks it, ask its administrator; do not bypass policy.

### Windows portable ZIP

Extract the **complete** portable ZIP into a separate ordinary folder. Open
`Herps Launcher\Herps Launcher.exe`. Keep `_internal`, game, engine-source and
other supplied folders together. Moving only the EXE breaks the installation.
Portable packaging does not move your saves into the application folder: normal
user data still uses the support folder listed below.

### macOS Intel and Apple Silicon

1. Open the verified DMG for your CPU.
2. Copy **both** `Herps Launcher.app` and `Herspers Minecraft.app` to Applications.
   When updating, replace application bundles only, after backing up data.
3. Eject the DMG. Open **Herps Launcher** from Applications/Finder, not from the
   mounted image; temporary image paths disappear when it is ejected.
4. If game discovery fails, use Settings → **Find installation…** and choose
   `/Applications/Herspers Minecraft.app` as a whole bundle. Validate it.

Mac apps are **ad hoc/development signed, not Apple-notarized**, unless a
specific new package has verified receipts proving otherwise. Native CI's
strict signature check is not Developer ID or Gatekeeper trust. If macOS offers
**System Settings → Privacy & Security → Open Anyway** after an attempted launch,
review the trusted source/hash before choosing that per-app exception. On older
experimental macOS versions the menu wording differs. Do not remove quarantine
attributes, disable Gatekeeper or treat a “damaged”/blocked message as safe to ignore.
Record the exact message and use the failure-reporting steps below.

Normal chainmail/metadata use needs neither `engine-source` nor Rust. Retain the
optional engine-source folder separately only for trusted native development.

## Prepare legitimate Minecraft resources

**Documented workflow; clean physical preparation acceptance NOT RUN.** Successful
Windows gameplay indicates a working prepared setup, not that every setup path
or input error has been tested. All Mac physical preparation/gameplay is NOT RUN.

1. Use your legitimate Minecraft account and the
   [official Minecraft launcher/download information](https://www.minecraft.net/en-us/download).
2. Install **Minecraft Java Edition 26.3** and launch that exact version once
   through the official launcher. Bedrock files, another Java version, a modpack
   archive, a friend's copied assets or a random server JAR are not substitutes.
3. Obtain that exact version's **official server JAR** from Minecraft's official
   version information. Keep the `.jar` file unextracted. It is an input to the
   preparer; you do not need to host a server.
4. Install/configure a full **JDK 25** as described next.
5. In Herps Launcher → Settings find the displayed **Herspers folder / .app**:
   - Windows: open the displayed game folder in File Explorer and run **Setup.cmd**.
     In a portable layout it is inside `Herps Launcher\game\Herspers-Minecraft`.
   - Mac: open Terminal and run:

     ```bash
     "/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
     ```

6. Select/paste the full path to the matching server JAR when asked. Windows
   **Copy as path** is useful; surrounding quotes are accepted. Do not select
   an extracted `META-INF` directory or a saves folder.
7. Keep the preparation window open until it says **Resources are ready**.
   If it rejects a version/hash/JDK, retain the error and fix the input; do not
   disable checks or download unofficial replacement assets.
8. Open Settings → **Validate installation**. Use **Find installation…** for the
   complete game folder/app if it is not discovered. Save settings if edited.

A custom official Minecraft folder can be supplied to the game's existing setup
command: server JAR first, Minecraft installation folder second. See the
[Windows details](docs/INSTALL-WINDOWS.md#command-line-setup-or-a-custom-installation-folder)
and [Mac details](docs/INSTALL-MACOS.md#if-your-minecraft-installation-is-in-a-different-folder).
Those pages include historical game-only instructions; this guide's launcher
installation and current release files take precedence.

Resource preparation may use Java/JDK tooling. It does **not** implement Java
mod execution, run the RLCraft/FunCraft mods or unlock Java Mods Build/Test.
The launcher is not a new Microsoft account manager; online authentication and
multiplayer capabilities have separate limits/testing requirements.

## Configure JDK 25

Choose a **JDK**, not just a JRE, matching Windows x64, Mac Intel x64 or Mac ARM64.
An example official distribution is
[Eclipse Temurin JDK 25](https://adoptium.net/temurin/releases/?version=25).
Use its installer and distribution instructions. Installer screens and your
system's environment settings are **documented / manual NOT RUN**, not screenshots
or claims of tested behavior.

### Windows JDK check

Open a **new** PowerShell window after installation:

```powershell
java -version
javac -version
```

Both should identify version **25**. If multiple JDKs are installed, the preparer
also searches installed JDK folders and `JAVA_HOME`. For a temporary explicit
choice, replace the example with the actual JDK 25 folder on your PC:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\YOUR-ACTUAL-JDK-25-FOLDER'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
java -version
javac -version
```

Then, from that same window, open the actual game folder and run the command
below. This temporary choice affects only that window
and its child processes; it does not change other applications' Java settings.

```powershell
.\Setup.cmd
```

### Mac JDK check

In Terminal:

```bash
/usr/libexec/java_home -V
export JAVA_HOME="$(/usr/libexec/java_home -v 25)"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
javac -version
"/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
```

If `java_home` cannot find 25, install the full matching-architecture JDK first.
Do not paste a path from another person's computer. This configuration is
**documented / Mac manual NOT RUN**; native game CI did not establish your JDK setup.

## Launch Minecraft for the first time

1. Finish resource preparation and installation validation first.
2. On **Home**, click **+ New profile** and use `first_play` for a disposable
   unmodded test. A new profile does not copy existing worlds.
3. Verify `first_play` is selected; click **PLAY →**. Wait for a real game window.
   The in-game UI may retain Horizon branding; that is the integrated native engine.
4. Create a small new world. Move, look around, test sound and save/quit normally.
   These observations are tests for you to perform, not preclaimed passes.
5. Wait for the launcher's exit status before launching again or changing files.
   Reopen the world and check your changes. Close normally before taking backups.

**Clean startup** uses a separate isolated game folder; it is a diagnostic session,
not your selected profile's worlds/mods. Use ordinary PLAY for chainmail testing.
Never run multiple clients/servers against the same saves at the same time.

## Create and manage profiles

The seven pages are **Home, Mods, Java Mods, Modpacks, Shaders, Multiplayer,
Settings**. Profile selection and **+ New profile** are on Home.

- Names use 1–64 lowercase letters, digits or underscores, for example
  `chainmail_trial_01`. Use unique names.
- Select a profile only while the launcher is idle. Running games/builds lock
  profile changes to protect data. Wait for completion instead of editing settings.
- `default` reuses the existing normal game folder; named profiles are isolated.
- A new profile starts without a copy of your worlds. The UI does not provide
  a general rename/delete/migrate-profile wizard; do not invent one by renaming folders.
- In Settings choose **Open game data and saves** to open the currently selected
  profile's actual folder. Do this before any manual copy operation.

| Data | Windows | macOS |
| --- | --- | --- |
| Entire support folder | `%LOCALAPPDATA%\Herspers Minecraft` | `~/Library/Application Support/Herspers Minecraft` |
| Default game folder | `game` inside support | `game` inside support |
| Named profile | `herps-launcher\profiles\NAME` inside support | `herps-launcher/profiles/NAME` inside support |
| Named worlds | `saves\WORLD` inside that profile | `saves/WORLD` inside that profile |

Moving the GitHub repository does **not** rename these folders or migrate/delete
existing user data. Logs, profile registration, targeted-content receipts and
backups also live in the support tree; back up the complete tree before updates.

## Install and safely manage native mods

**Java Mods/Modpacks pages do not run original Forge/Fabric JARs.** Import/analyze
is passive inspection, and supported data carry-over is a limited transformation.
Java Build/Test and whole-Modpack Play remain disabled. Do not treat a backend
`works` verdict as real gameplay proof or a complete port.

For another trusted `.hmod` supported by this exact engine:

1. Close the game/server, back up data and select a disposable named profile.
2. Open **Mods → Import mod…**, choose the original trusted `.hmod`, and review
   its identity/API/capabilities. Imported packages start disabled.
3. Select it and use **Enable / disable** only after reviewing it. Restart the
   game through ordinary PLAY and test its intended behavior.
4. To remove supported ordinary mods, use **Remove to backup** instead of deleting
   files. Read errors and preserve edited packages. Enabling/disabling/removing
   is profile-local, not global.

A `.hmod` may contain code; do not assume every package is data-only. Only the
bundled Chainmail package has the reviewed scope described below. `.hnmod`
packages are **trusted native source code**, need the exact pinned engine/mixin
revision and developer Rust/platform tools, and may execute with your permissions.
They are not sandboxed. Rebuild/rollback tools are advanced and are not required
for ordinary installation or chainmail. Do not compile unknown source to “fix” a mod.

Removing custom-item content can damage item persistence. For chainmail the
launcher blocks disable/removal once saves exist. Keep it enabled; never delete
its receipt or edit hashes/settings to bypass a safety error. Other mods need
case-specific testing and backup; this guide cannot certify arbitrary packages.

## Test Chainmail Plate and Boots

**This is a small native replacement, not complete RLCraft.** Installation uses
the bundled package and needs no RLCraft JAR or archive import.

1. Close all games and servers. On Home create/select a **fresh disposable**
   profile, such as `chainmail_trial_01`. **Do not create a world yet.**
2. Open Modpacks → **Chainmail Plate and Boots**. Read the selected profile name,
   confirm it is disposable with no saves and all games/servers closed, then
   click **Install chainmail crafting · disabled initially…** and confirm.
3. Open Mods. Verify **OFF — Chainmail Plate and Boots (experimental) 0.1.0**.
   Select it and click **Enable / disable** once so it says **ON**.
   Do not use generic import to bypass the dedicated install; do not click Rebuild.
4. Use Home → ordinary **PLAY**, then make a new Survival or Creative world.
5. Arrange four iron nuggets in a square:

   ```text
   nugget  nugget
   nugget  nugget
   ```

   Taking the output should produce **one Chainmail Plate**. It deliberately
   resembles a vanilla nugget; inspect its name. Count ingredients/output.
6. On a 3×3 crafting table put four plates in the boots pattern:

   ```text
   plate  empty  plate
   plate  empty  plate
   empty  empty  empty
   ```

   The output should be vanilla **Chainmail Boots**. User-reported Windows
   equipment displayed **+1 Armor**. No RLCraft Defense-level gate is implemented.
7. Keep an additional plate and the boots in inventory. Save/quit, close the
   game and launcher fully, restart both, select the same profile/world and
   check the items. User reported this PASS in Survival and Creative on the
   earlier Windows candidate; repeat for new packages/hardware.
8. Wrong layouts/ingredients, shift-click consumption, duplication, chest
   persistence and armor damage/durability remain physical **NOT RUN** unless
   you actually test/report them. All Mac gameplay is **NOT RUN**.

The package is `herspers_rl_chainmail-0.1.0.hmod`, 40,002 bytes, SHA-256:
`015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346`.
Do not disable/remove it once this profile has saves. A missing/changed/disabled
managed package blocks launching that saved profile to protect custom items.
Missing-content recovery is not verified; use a new empty profile for removal tests.

## Save worlds

Use the game's normal **Save and Quit** control. Wait for the game to finish
saving and close, then wait for the launcher's exit status. Merely closing a
window forcefully is not a verified save procedure. Do not back up or move saves
while any client, server, backup tool or second launcher is writing them.

One Windows inventory-persistence case is reported PASS; this does not certify
all worlds, large saves, crash recovery, update migration or cloud-sync behavior.

## Back up worlds

**Documented manual backup/restore procedure; physical restore acceptance NOT RUN.**

### General backup for any supported native profile

1. Save/quit and stop all games/servers normally. Use Settings → **Open game data
   and saves** to identify your selected profile, then close the launcher too.
2. Open the **entire support folder** from the table above. Windows: paste
   `%LOCALAPPDATA%\Herspers Minecraft` into File Explorer's address bar. Mac:
   Finder → Go → Go to Folder, paste `~/Library/Application Support/Herspers Minecraft`.
3. Copy the complete support folder to a **new separately named backup folder**
   on another drive/location. Keep multiple dated copies; do not overwrite the
   only backup or put it inside the source folder. This retains worlds, mods,
   registration, settings, chainmail ownership receipts and existing FunCraft backups.
4. Wait for copying to finish. Check that the backup has the intended world's
   `saves/WORLD/level.dat` plus its other files. File presence alone is not proof
   the backup can load. Preserve the stopped original while testing a restoration.

### FunCraft-hotfix targeted archive backup

This optional UI feature is available **only for the exact previously inspected
FunCraft 1.1.1 hotfix ZIP**, SHA-256
`09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e`.
It is not a universal Backup button and does not make FunCraft playable.

1. With the correct profile selected, use Modpacks → **Import modpack…** for
   your own exact archive, then select that retained import.
2. Stop all clients/servers. Use **Back up stopped worlds…** and confirm only
   when those processes are closed. Record the generated archive path/hash.
3. Use **Verify world backup…** on that `worlds.zip` before restoring it.
4. Keep its manifest/receipt and external copies. Verification checks bounded
   archive integrity, not real world loading. No live/timed backup or one-click
   in-place restore is implemented.

The bounded utility refuses totals over 512 MiB, individual files over 128 MiB,
or more than 10,000 entries and refuses unsafe/changing trees. A refusal protects
existing data; do not delete world files to force a pass. Use a complete stopped
manual copy for a larger world. [Detailed backup acceptance](docs/targeted-porting/WINDOWS_BACKUP_ACCEPTANCE.md).

## Restore supported native backups safely

1. Keep the original world and backup untouched. Close all game/server processes.
2. For your own verified `worlds.zip`, independently extract to a **new empty
   scratch folder**. It contains `backup-manifest.json` and `saves/`. For a manual
   support-folder copy, locate the intended profile's `saves/WORLD` inside it.
   Do not run scripts found in archives or use a Forge/RLCraft world as a native save.
3. Create a **new disposable target profile** in Home. Identify its actual folder
   in Settings. If it already contains any saved world, stop and choose another.
4. **For a chainmail world, install and enable the same bundled chainmail feature
   in that fresh empty profile BEFORE copying any save.** Fresh-profile installation
   is intentionally blocked after saves exist. Keep required content enabled.
5. Close the launcher. Copy only the desired native world folder into the new
   profile's empty `saves` directory. The result should be
   `saves/WORLD/level.dat`, not `saves/saves/WORLD/level.dat`. Stop at any merge/
   replace prompt; never overwrite another world. Do not copy the backup manifest
   into a world, or copy an old receipt with a different profile name.
6. Reopen the launcher, select the target profile and use the same compatible
   game/resources/content. Load only the disposable restored world. Check location,
   distinctive blocks/items, then save/exit/reload. Record actual observations.
7. Keep the stopped original and independent backup until restoration is proven.
   A successful ZIP check or matching hash alone does not pass gameplay restoration.

In-place valuable-world restoration, arbitrary version conversion, Forge save
migration and missing-mod recovery are not supported/verified. Ask for review
rather than disabling guards if the target cannot be made safely compatible.

## Update without losing worlds

**CI checked same-version replacement/removal preservation; physical upgrades
and arbitrary historical-version migration remain NOT RUN.**

1. Save/quit, stop clients/servers/launchers and make an external full-support
   backup as above. Keep the previous complete installer/package and required mods.
2. Read the new version's known issues and verify its own SHA256SUMS.
3. Windows: run its verified installer with old instances closed, or extract a
   portable build into a **different** folder. Do not merge random files from
   different portable versions. Mac: replace **both** application bundles together.
4. Do not move/delete the support folder. In the launcher validate/reselect the
   complete game installation if its path changed.
5. Test a fresh disposable profile first. Keep chainmail enabled in any saved
   chainmail profile; do not update by removing that custom content.
6. Only after checking the new package, open a backed-up compatible world. Check
   the world/items and save/relaunch. If anything fails, stop and preserve logs
   and backup copies; do not repeatedly rewrite the only valuable save.

A GitHub-repository migration alone does not change data paths. Historical
engine/native-mod version changes need separate compatibility review.

## Uninstall while preserving data

**Native CI preservation passed with owned sentinels; physical removal NOT RUN.**

- Windows installer: save/close everything and back up support data. Use Windows
  Settings → Apps → Installed apps → **Herps Launcher → Uninstall**. Remove the
  application, not the support folder. Portable: remove only the extracted app
  folder after backing up; it is not the normal support folder.
- Mac: close everything, back up support data, then move the two app bundles out
  of Applications/to Trash. Do not delete `~/Library/Application Support/Herspers Minecraft`.
- Keep worlds, profile settings, native packages/receipts and backups. Reinstall
  a compatible package and validate its game path before trying the backed-up profile.
  Do not manually delete data just to remove a shortcut or “reset” an error.

## Troubleshooting

| Problem | Safe checks / action | Evidence limit |
| --- | --- | --- |
| Loading-logo freeze/stall | Record run/hash, profile, enabled mods, resource version, GPU/driver and duration. Check logs. Compare a fresh unmodded disposable profile with default shaders/Auto graphics. Do not delete existing saves or receipts | Earlier stall is **unresolved**; later launches succeeded but no cause/fix is established |
| Missing resources / PLAY refuses | Run the game's Setup.cmd/prepare.command with full JDK 25 and exact official 26.3 files; retain resource-check errors; validate the complete installation | Clean physical preparation paths are NOT RUN |
| JDK missing/wrong Java | Check both `java -version` and `javac -version`; select the full matching JDK 25, reopen the shell/setup window, use explicit JAVA_HOME if necessary | Setup screens vary; no invented screenshots |
| Empty crafting output | Check selected disposable profile, mod ON before launch, ordinary PLAY, recipe ingredients/pattern and correct resource/game version. A plate looks like a nugget: inspect its name. Restart normally after enabling | Earlier empty output is **unresolved**; these are diagnostic checks, not a proven fix |
| Cannot install/disable/remove chainmail | Installation needs a fresh named disposable profile with no saves. Disable/remove is blocked with saves; keep content enabled. Do not edit receipts/hashes to bypass | Missing-item recovery NOT RUN |
| Installer rejects a path | Choose a shorter ordinary application folder; preserve data. Extract complete packages first and use x64 on Windows | CI tested path rejection before copying; arbitrary long paths are not promised |
| App/helper/game missing or wrong architecture | Re-extract the complete verified package, keep supporting folders, select correct CPU, reselect whole game folder/app in Settings | Do not mix different builds or move only the executable |
| Mac security blocks app | Check exact source/hash and per-app security message. These packages are not notarized. Record the prompt; do not disable Gatekeeper or strip quarantine | Downloaded Gatekeeper/Finder acceptance NOT RUN |
| Missing VC++ runtime / graphics driver | Install the official x64 runtime if requested and update the GPU vendor driver; keep Auto first | No universal GPU or shader certification |
| Profile/operation locked after failure | Close all clients/servers/other launchers and retain logs; use documented recovery/review. Never delete a lock while a process may still own the profile | Do not treat a stale-file guess as safe proof |
| Backup is blocked or verification fails | Keep source/backup untouched. Respect size/path/concurrency checks; use stopped full-folder copying for large worlds | No live/timed backup or automatic save conversion |

If a disposable test becomes unresponsive, prefer normal closing. Forced
termination can lose unsaved changes; never experiment on the only valuable copy.
There is no guaranteed timeout or universal cache-deletion fix for the logo stall.

## Collect logs and report a problem

Home → **Open launcher and game logs** opens the launcher support directory.
Useful records include `herps-launcher/logs/`, `resources-check.log`, the selected
profile's `horizon-mods.txt` and retained import/backup receipts. State the exact
file/run/hash, OS/build, CPU/GPU/driver, profile name, steps, expected/actual
result, mode, item counts and whether the machine is physical or virtual.
Use **PASS / FAIL / BLOCKED / NOT RUN**. Keep earlier failures alongside later passes.

Review excerpts before sharing. Redact passwords/tokens, account details,
personal paths, private IPs/server addresses and unrelated data. Do not upload
your whole support folder, valuable worlds, copyrighted game assets or proprietary
mod JARs. No credentials are needed to report a basic crafting failure.

## Known limitations and notices

- **No full RLCraft or FunCraft modpack compatibility.** This release has a small
  native chainmail replacement and a separate bounded FunCraft backup utility.
- No original Forge/Fabric Java bytecode execution, Java bridge, universal
  conversion, packwiz support, Java Mods Build/Test or whole-Modpack Play.
- No Reskillable Defense gate, extra armor/integration recipes, Forge-world
  migration or verified missing-content recovery.
- All physical Mac gameplay and unreported Windows edge cases remain NOT RUN.
  Native CI, an integrity hash or an offscreen menu is not real gameplay.
- Windows is unsigned; Mac development signatures are not notarization/publisher
  trust. Full reproducibility and broad hardware support are not claimed.
- Current source, licence and dependency review limits are in
  [support](docs/HERPS-SUPPORT.md), [security](docs/herps/release-security.md) and
  [release notes](RELEASE_NOTES.md). The imported launcher is GPLv3; Horizon and
  dependencies keep their own licences. Include notices when redistributing.
