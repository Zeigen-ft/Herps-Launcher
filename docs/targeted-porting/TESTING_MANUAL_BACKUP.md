# Test the first FunCraft replacement feature

This is a **manual backup of stopped Herspers profile worlds**, independently
written to preserve one FTB Backups behavior. It is not an executable port of
FTB Backups, a Forge/JVM bridge, a 1.12.2 world converter or a playable FunCraft
package. No compatible whole-pack installer has been produced.

## Use the implementation from source

The historical Phase 5D Windows installer recorded at `3112e32` does **not**
contain this new feature. Use the feature-branch checkout containing the initial
implementation report. Keep any existing checkout changes and user worlds;
there is no need to merge into main or replace the installed game.

On Windows, install Python 3.12, open PowerShell in that checkout and run:

```powershell
py -3.12 -m venv .local\herps-venv
.\.local\herps-venv\Scripts\python.exe -m pip install -r herps_launcher\requirements.txt
.\.local\herps-venv\Scripts\python.exe -m herps_launcher
```

Use the already verified Phase 5D Windows `horizon-port-pack.exe` as the passive
helper: **Modpacks → Select backend…**. In a default installation it is under
`%LOCALAPPDATA%\Programs\Herps Launcher\Herps Launcher\_internal`. Its Phase 5D
SHA-256 is `73042cc1bda5f31e52f7b4430243056fc5cf5ff9de55ff72cd581a853f3bdd5f`.
Verify it with `Get-FileHash` before selecting it. Use the actual custom install
path if different. Do not select code or executables supplied inside a modpack.
The source launcher needs Python/Qt; the passive helper and backup operation
need no end-user Rust/Cargo, Java mod runtime or native source rebuild.

On macOS the same source feature uses Python 3.12 and the platform's trusted
Phase 5D helper; the Windows binary cannot be used there. Native interactive
acceptance of this new feature has not been performed on either OS.

## Prepare a disposable test

1. Close all games, launchers and servers. Make a separate external backup of
   `%LOCALAPPDATA%\Herspers Minecraft` before using any existing data.
2. Start the source launcher. Create/select a named profile such as
   `funcraft_trial`. Do not use a valuable world.
3. Import the original `FunCraft - FC-Release 1.1.1 - hotfix.zip` through
   **Modpacks → Import modpack…**. Its exact SHA-256 must be
   `09db709ff9ddcdabdf080ba814afe3c3c453e32dfde38356b99a00bed58ee12e`.
4. Select its row. The targeted-replacement panel should show the original
   pack name/version and the limited manual-backup feature. Other ZIPs, renamed
   packs, edited imports and RLCraft cannot unlock it.
5. If you have legitimate prepared 26.3 resources and a working game installation,
   use Home PLAY in this profile, create a disposable world, make a recognizable
   change, save and quit normally. Wait for the launcher to record the exit.
   Follow the [existing preparation guide](../HERPS-QUICKSTART.md#2-prepare-resources-and-play).
   If the game cannot run, mark real-world backup/load acceptance BLOCKED;
   synthetic files are not substitutes for real gameplay evidence.

Importing does not install or activate the Java mods. Missing dependencies and
unsupported classifications remain visible in the existing analysis workflow.
No restricted-licence/data-port acknowledgement is needed for this independently
authored backup operation; do not grant rights to the original content implicitly.

## Create and verify a backup

1. Ensure **every** game/server using the profile is closed, including programs
   started outside Herps Launcher. The launcher cannot stop or flush external
   processes automatically.
2. Open Modpacks, select the inspected FunCraft import, and click
   **Back up stopped worlds…**. Scroll the page if controls are below the viewport.
3. Read the confirmation. Cancel if any process is still using the saves.
4. Wait for checksum verification to finish. A success result includes profile,
   file count, size, archive hash and location. Empty/missing saves fail visibly.
5. Backups are created outside the game folders:

   ```text
   %LOCALAPPDATA%\Herspers Minecraft\herps-launcher\targeted-backups\funcraft\<profile>\<timestamp-random>\worlds.zip
   ```

6. Click **Verify world backup…**, select that ZIP, and confirm its integrity
   result. Verification reads files/checksums without extracting or launching them.
7. Copy an important backup to another drive and retain its SHA-256. Local backups
   on the same drive do not protect against loss of that drive.

Original saves, options, mods, other profiles and previous backups must remain
unchanged. Existing archives are not overwritten or pruned. Modpack **Play ·
unavailable** and Java **Build Mod / Test Mod** must remain disabled.

Initial limits: 512 MiB total save bytes, 128 MiB per file, 10,000 file/directory
entries and 32 path components. Linked/junction/special files, unsafe or
case-colliding paths and observed concurrent changes are rejected. Larger worlds
are outside this slice; do not remove files to force them under the limits.

## Check recovery in a separate profile

There is deliberately **no automatic in-place restore**.

1. Close all game/server processes and verify the backup first.
2. Extract your own verified ZIP into a new scratch folder, preserving it and the
   original profile unchanged. It contains `backup-manifest.json` and `saves/`.
3. Create a new, empty profile such as `funcraft_restore`.
4. Use Settings → Open game data and saves for that new profile. While idle, copy
   the extracted `saves/` into it. Stop if it already contains worlds; do not merge
   or overwrite existing data.
5. Use the same compatible native game/resources to reopen the restored test
   world and verify the distinctive change. Record the result separately from
   archive integrity. This does not migrate a legacy Forge world.
6. Check that the original profile/world remains intact. Retain the backup when
   rolling the source feature back; it is an ordinary ZIP with a checksum inventory.

A failed operation must not claim success or delete an earlier backup. Disk,
read and verification errors should remain actionable. A forced process/power
failure may leave a private `worlds.partial` or a stale launcher lock. These are
not verified backups. Follow the existing stale-lock recovery only after all
games/launchers/servers are closed; never remove a live operation's lock.

## Developer reproduction and reporting

Run the supplied-input smoke using a trusted native helper:

```sh
python tools/smoke_targeted_backup.py --funcraft "/path/FunCraft - FC-Release 1.1.1 - hotfix.zip" --backend "/path/trusted/horizon-port-pack" --report /tmp/targeted-backup.json
```

It creates disposable fixtures, empties PATH for the operation, performs a real
helper import and a filesystem/ZIP round trip, and removes its temporary data.
It never uses your actual saves. The result is automated integrity evidence,
not gameplay. On Windows use the trusted `.exe` path and a writable report path.

Record PASS / FAIL / BLOCKED / NOT RUN, date/time, OS/CPU, source commit, input and
helper hashes, profile, exact steps, error text and backup hash. Screenshot the
UI result and retain its JSON details. Share only reviewed/redacted receipts and
necessary logs. Do not upload private backups/worlds, the complete support folder,
Minecraft assets, account tokens or mod JARs by default.
