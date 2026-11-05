# Windows 11 acceptance — a real world backed up and loaded separately

Use the exact downloads/checksums in the
[current Windows candidate report](NEXT_PHASE_PREPARATION_REPORT.md).
All cases below start **NOT RUN**. Native CI uses owned fixture bytes and
offscreen UI; it cannot pass real gameplay/world-load cases. This procedure
tests one FunCraft-scoped backup utility for native Herspers worlds, not the
original FunCraft gameplay, FTB Backups JAR, RLCraft or Forge-world conversion.

## 1. Record and protect

- Record tester, date/time/timezone, physical PC or VM, Windows build (`winver`),
  CPU/RAM, GPU/driver and standard/admin account. Record whether Rust/Cargo is
  already installed; do not install it to perform this test.
- Use the **exact successful Windows run, candidate source SHA and Setup EXE
  SHA-256 in this phase's final verification report**. Version 0.1.0 filenames
  are reused across candidates; do not substitute an older installer.
- Close every game, launcher and server. Copy
  `%LOCALAPPDATA%\Herspers Minecraft` to an external backup before using existing
  data. Keep it private. Do not move/delete the original.
- Use disposable profiles/worlds only. If a destination already has a world,
  stop and choose a new profile/folder. Never merge or overwrite saves.

## 2. Install the verified candidate

1. Sign in to GitHub if necessary, download the exact Windows artifact and
   **Extract All**. Check the downloaded ZIP and extracted Setup EXE hashes with
   `Get-FileHash -Algorithm SHA256 -LiteralPath "<full file path>"`.
2. Run the verified Setup EXE using the default short per-user folder. Keep an
   installer log if desired: open PowerShell in the extracted folder and run:

   ```powershell
   & '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe' "/LOG=$env:TEMP\Herps-backup-candidate-install.log"
   ```

   The log will be `%TEMP%\Herps-backup-candidate-install.log`.
3. Record any VC++ prerequisite error, unexpected elevation, SmartScreen or
   antivirus warning. Review the source/hash before deciding whether to trust
   this unsigned candidate. Do not disable security controls to pass acceptance.
4. Launch through the installed Start-menu shortcut. Check all seven pages:
   Home, Mods, Java Mods, Modpacks, Shaders, Multiplayer and Settings.
5. The installed app bundles its passive helper. No Python, Rust or Cargo is
   needed for launcher backup/import. Python 3.12 is separately required only
   for the [local RLCraft inspector](WINDOWS_RLCRAFT_INSPECTION.md).
   To record the Rust tools currently on PATH, run this read-only check:

   ```powershell
   foreach ($tool in 'cargo','rustc','rustup') {
       $found = Get-Command $tool -ErrorAction SilentlyContinue
       if ($found) { "$tool : $($found.Source)" } else { "$tool : absent from PATH" }
   }
   ```

   If tools are already installed, record that limitation; do not uninstall them
   or claim a physical test without developer tools. CI separately tests their
   absence from PATH. Native source-mod compilation is outside this checklist.

## 3. Create a real disposable native world

1. On Home create/select `funcraft_accept_src`.
2. In Settings validate the bundled native installation. For real PLAY, prepare
   legitimate matching Minecraft Java 26.3 resources using the existing Setup.cmd
   and JDK 25 instructions in the [quickstart](../HERPS-QUICKSTART.md#2-prepare-resources-and-play).
   The JDK is for preparation, not Java mod execution.
3. Keep native/runtime mods disabled, shaders at default and renderer on auto.
   Press Home **PLAY** and confirm a real rendered game window.
4. Create a new world named `Backup_Acceptance_Source`. Make a distinctive block
   arrangement and record a screenshot, location and any relevant inventory.
   Check movement, input, graphics and audible in-game effects separately.
5. Save/leave the world and quit normally. Wait for the launcher to record the
   exit code and become idle. Close all separately started games/servers too.
6. Use Settings → **Open game data and saves** and record this profile's folder.
   Its `saves/` must contain the real new world. Do not substitute a dummy
   `level.dat` or synthetic test directory. If resources/PLAY/world saving fail,
   record FAIL and mark dependent backup/load acceptance BLOCKED.

## 4. Back up the stopped source profile

1. In the same profile, open Modpacks and import the exact original
   `FunCraft - FC-Release 1.1.1 - hotfix.zip` (SHA-256
   `09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e`).
   Import keeps a local inspection snapshot; it does not activate the Java pack.
2. Select its row. Confirm the targeted panel shows the FunCraft name/version
   and the limited manual backup feature. Scroll if needed.
3. Click **Back up stopped worlds…**. Confirm all game/server processes using
   the profile are closed. Cancel otherwise; this is not a live-server backup.
4. Wait for a completed result with archive location, file count and SHA-256.
   The source saves must remain in place; no previous backup may disappear.
5. Click **Verify world backup…** and select the new archive. Record the integrity
   result and hash. Verification reads every member and never loads a world.
6. Copy this backup to another drive. Default local location:

   ```text
   %LOCALAPPDATA%\Herspers Minecraft\herps-launcher\targeted-backups\funcraft\funcraft_accept_src\<timestamp-random>\worlds.zip
   ```

Java Mods Build/Test and Modpack **Play · unavailable** must remain disabled.
Successful archive integrity is not a claim that FunCraft or the world works.
Limits remain 512 MiB total, 128 MiB per file, 10,000 entries and 32 source path
components. A larger test world is BLOCKED by scope; do not delete its files to
force a pass.

## 5. Independently extract and compare

1. Keep every game/server closed. Right-click your own verified `worlds.zip` in
   File Explorer → **Extract All**, choosing a **new empty scratch folder**.
   This independent Windows extraction does not use the launcher's verifier.
2. Confirm it contains `backup-manifest.json` and `saves/` with the test world.
3. Before opening either world again, compare the stopped source `saves/` tree
   with the extracted `saves/`. This optional read-only PowerShell helper hashes
   every file. Paste folder paths into the prompts without surrounding quotes:

   ```powershell
   $sourceSaves = Get-Item -LiteralPath (Read-Host 'Full path to stopped source profile saves folder')
   $extractedSaves = Get-Item -LiteralPath (Read-Host 'Full path to scratch extracted saves folder')
   function Get-SaveHashes($folder) {
       Get-ChildItem -LiteralPath $folder.FullName -Recurse -File -Force | ForEach-Object {
           [PSCustomObject]@{
               File = $_.FullName.Substring($folder.FullName.TrimEnd('\').Length + 1)
               SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
           }
       } | Sort-Object File
   }
   $sourceHashes = @(Get-SaveHashes $sourceSaves)
   $extractedHashes = @(Get-SaveHashes $extractedSaves)
   if ($sourceHashes.Count -eq 0) { throw 'No source save files; this is not a real-world acceptance pass.' }
   $difference = Compare-Object $sourceHashes $extractedHashes -Property File,SHA256
   if ($difference) { $difference; throw 'Save contents differ. Stop before restoring.' }
   'All extracted save file hashes match the stopped source.'
   ```

Record differences or an inability to compare; do not silently mark this check
passed. This helper changes no files. Do not run scripts found inside a modpack.

## 6. Load only in a separate disposable profile

1. In Home create/select **`funcraft_accept_restored`**. Do not reuse an existing
   profile. Settings → Open game data and saves identifies its separate folder.
2. While all games remain stopped, confirm that destination contains no saves.
   Copy the scratch folder's **`saves` folder** into this new profile's game
   folder. If the new profile already has an empty `saves` folder, open it and
   copy only the extracted test-world folder into that empty folder; avoid
   creating `saves\saves`. Enable File Explorer → View → Show → Hidden items
   when checking emptiness. Do not copy the backup manifest into a world or
   overwrite anything. Stop if any save is already present or any merge/replace
   prompt appears; choose another new disposable profile.
3. Return to Home with `funcraft_accept_restored` selected. Use the same compatible
   native installation/resources and press PLAY. Open the restored test world.
4. Verify the distinctive marker, location and relevant inventory. Save/exit
   normally, wait for the exit code, relaunch and verify it again.
5. Confirm the original source profile/world remains present. It must not have
   been moved or overwritten. The two profiles should now have independent worlds.
   With both games stopped, repeat section 5's comparison between the original
   source `saves/` and the unchanged scratch extraction: they must still match.
   Compare the original source here, not the restored copy that gameplay has
   legitimately updated.

Only an actual successful load and marker observation can pass restore gameplay
acceptance. A matching hash, valid ZIP, test log, menu or synthetic file cannot.

## 7. Preservation, failure handling and final record

After another external backup, optionally test same-version replacement and
uninstall/reinstall with all processes closed. Record hashes of both profiles'
saves and the backup ZIP before installation changes and compare them **before
reopening worlds**. App removal must not remove support data or earlier backups.
This is not evidence of migration from every historical version.

If an operation fails, retain the exact error, screenshot and timestamp. Use
Home → **Open launcher and game logs**. Useful files are under
`%LOCALAPPDATA%\Herspers Minecraft\herps-launcher`: `logs/`, `resources-check.log`
and `activity.json`. Copy the backup result JSON displayed in Modpacks details.
Never delete a live operation lock. Resolve stale locks only after confirming
all related processes are closed; forced power/process-loss acceptance is still
separate from automated injected-error tests.

For each case record **PASS / FAIL / BLOCKED / NOT RUN**, candidate source commit,
run/artifact/hash, machine details, profile paths (redacted for sharing), steps,
expected/actual behavior, exit code and evidence filenames. Review shared logs
for credentials, private addresses and personal paths. Do not upload whole worlds,
backups, account data, Minecraft assets or the complete support folder by default.

Any data loss, unintended overwrite, bad archive creation, inability to reopen
the restored world or core PLAY/save/relaunch defect blocks Windows acceptance.
No release or complete modpack support is approved by this procedure.
