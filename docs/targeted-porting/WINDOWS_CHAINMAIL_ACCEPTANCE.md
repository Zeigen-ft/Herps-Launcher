# Windows 11: test Chainmail Plate and Boots

This is an **internal experimental candidate**, not complete RLCraft support.
The user reports enabled launch, both recipes, +1 Armor equipment and inventory
persistence after a full game/launcher restart PASS in Survival and Creative
on run 42118750443. Other cases below remain NOT RUN; this checklist must not
be treated as wholly passed. Earlier logo-stall/empty-output observations are
unresolved. Use the exact candidate and
checksums linked in [the verification report](RLCRAFT_CHAINMAIL_VERIFICATION.md).

## 1. Install and prepare

1. Close every launcher, game and server. Make an external copy of your existing
   `%LOCALAPPDATA%\Herspers Minecraft` folder while everything is stopped. Keep
   existing saves and FunCraft backups; this feature does not replace backups.
2. Sign into GitHub, open the exact successful Actions run in the report, and
   download `Herps-Launcher-0.1.0-Windows-x86_64` from its **Artifacts** section.
   Extract the download into a new empty folder. Do not run an older candidate.
3. In PowerShell, check the installer against the report and bundled `SHA256SUMS`:

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
   ```

   Use the **actual installer filename** in the report if it differs. Stop if
   the hash differs. Install into a separate ordinary folder you own; do not
   overwrite another running installation. This candidate is unsigned. Do not
   disable antivirus or Windows security to run an unexpected download.
4. Follow the [resource-preparation quickstart](../HERPS-QUICKSTART.md#2-prepare-resources-and-play):
   run the included game's `Setup.cmd` with **JDK 25** and your own matching
   **Minecraft Java 26.3** files. Preparation does not run Java mods. Keep your
   accounts and game files private. Do not use a Forge 1.12.2 world or RLCraft JARs.
5. Start **Herps Launcher**. On Home choose **New profile…**, and use a fresh name
   such as `chainmail_trial_01` (lowercase letters, digits, underscores). Check
   that the selected profile is this new one. **Do not create a world yet.**

## 2. Explicitly install, then enable

1. Open **Modpacks**. Under **Chainmail Plate and Boots**, read the selected
   profile name. Confirm that this profile is disposable, has no saved worlds,
   and every game/server is closed. Tick the confirmation and click
   **Install chainmail crafting · disabled initially…**. Confirm the dialog.
   You do not need to import the RLCraft archive.
2. Open **Mods**. It must list **OFF — Chainmail Plate and Boots (experimental)
   0.1.0**. No other profile should acquire it. This default-off check is required.
3. Select that entry and click **Enable / disable** once. It must now say **ON**.
   Do not click **Rebuild native mods**; this is content, not a source patch.
4. In Settings, use **Open game data and saves**. The selected profile must be
   under `herps-launcher\profiles\chainmail_trial_01`, separate from `game` and
   every existing profile. Its `horizon-mods` folder contains
   `herspers_rl_chainmail-0.1.0.hmod`, SHA-256:

   ```text
   015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346
   ```

5. Leave Java Mods **Build/Test** and whole-Modpack **Play** disabled. Launch
   this individual replacement with **Home → PLAY**. Use ordinary PLAY for
   this test; Clean startup uses a separate isolated session.

## 3. Test an actual survival world

Record screenshots/video, observations and exact counts. Do not mark a case
passed from logs, automated fixtures or a successful download alone.

1. Create a **new Survival** world, for example `ChainmailTrial01`, with cheats
   off. Move, look around, break/place a block, and listen for block/footstep
   sounds. Record rendering glitches, silence, hangs or crashes.
2. Obtain iron and a crafting table through normal survival play. Convert two
   iron ingots into **18 iron nuggets**. Use the actual grid, rather than relying
   on recipe-book discovery (no advancement/discovery behavior was added).
3. Arrange four nuggets in a 2×2 square:

   ```text
   n n
   n n
   ```

   The output must be **1 Chainmail Plate**. The plate intentionally resembles a
   vanilla iron nugget; verify its **name**, not just its icon. Take the output:
   four nuggets must disappear. Repeat until you have four plates. You must now
   have **4 plates and 2 nuggets**, with no extra output.
4. On the 3×3 crafting table arrange the four plates as boots (top or bottom two
   rows, middle column empty):

   ```text
   p . p
   p . p
   . . .
   ```

   Taking the output must consume exactly four plates and give exactly **one
   pair of vanilla chainmail boots**. You must still have two nuggets. Equip and
   unequip the boots; check the armor display and normal walking. No RLCraft
   Defense-level restriction is implemented or claimed.
5. Obtain additional iron. Try a missing nugget, a gold nugget in the square,
   a 2×2 plate square, or an extra plate in the boots' middle column. There must
   be no output and no consumed items. Test the plate square at each corner of
   the 3×3 grid and boots on either pair of rows.
6. For shift crafting, place **4 nuggets in each of the four square cells**
   (16 total), then Shift-click the output. Expect **4 plates**, all 16 nuggets
   consumed, no duplication and no lost unrelated stacks. Arrange one plate in
   each boots cell and Shift-click: expect one pair of boots, all four plates
   consumed. Count inventory and grid before/after; stop if they differ.
7. Craft **one extra plate from four additional nuggets**. Keep both an extra
   plate and boots, including a plate in a chest if possible. Note counts,
   equipment slot, location and a recognisable placed block/sign.
8. **Save and Quit**, then load the same world. Verify every item/count and
   location. Quit the game normally, close the launcher, reopen it, select the
   same profile, press PLAY, load the same world and verify again. Test graphics,
   audio and moving/equipping after relaunch. Record both successful and failed
   observations; this is the required custom-item persistence evidence.

## 4. Preservation and recovery

Keep this pack **enabled** in the test profile once any saves exist. The launcher
blocks disabling/removing it and blocks launching a saved profile with missing,
changed or disabled managed content. Missing-item recovery in the engine is
unverified. Do not delete the package/ownership receipt, edit the enable setting,
or bypass the guard with another executable. A rejection is expected; data loss
is never an acceptable test result. Use only empty new disposable profiles for
enable/disable/removal testing. Removal there retains a package/receipt backup.

With all processes stopped, compare hashes of valuable profiles, original
imports and FunCraft backup archives to your external copy. Do not start those
worlds during this test, as normal gameplay legitimately changes their files.
Preservation requires identical untouched data; report any difference.

The installed launcher/game must also work without **cargo**, **rustc** or
**rustup** discoverable in the launching terminal. No rebuild or dependency fetch
should occur. Do not uninstall useful tools just for this test; use a clean
standard-user environment or temporarily remove their directories from that
terminal's PATH. JDK 25 for resource preparation is a separate requirement.

## 5. Report safely

Home → **Open launcher and game logs** opens
`%LOCALAPPDATA%\Herspers Minecraft\herps-launcher`. Keep relevant `logs\*.log`,
`resources-check.log`, screenshots and the selected profile's
`horizon-mods.txt`. The install receipt is at
`targeted-content\rlcraft-chainmail\chainmail_trial_01\receipt.json` under that
launcher folder. This receipt proves file installation, not gameplay success.

Send the source commit, Actions run/artifact, installer/package hashes, Windows
version, GPU/driver, profile name, steps, expected/actual counts, exit code and
test outcomes (**PASS / FAIL / NOT RUN**). On failure, stop playing and preserve
the stopped disposable profile plus its content locally. Do not overwrite a
save to retry; use another fresh disposable profile. Review logs before sharing:
redact account tokens, credentials, email, personal usernames/paths, IP addresses
and private server details. Share only necessary excerpts; do not upload your
whole support folder, valuable saves, copyrighted game files or proprietary mods.
