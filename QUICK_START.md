# Quick start — install and play

**Herps Launcher 0.1.0 is a prerelease candidate.** Read
[INSTALLATION.md](INSTALLATION.md) for the complete guide, requirements, backups,
security prompts and troubleshooting. Minecraft resources are not bundled.

## 1. Download your package

Open [Herps-Launcher Releases](https://github.com/Zeigen-ft/Herps-Launcher/releases).
If no prerelease is published, use the successful destination CI download links
in [the migration report](docs/migration/README.md). Private-repository downloads
require access; ask the owner if you cannot see them.

| Your computer | Release file |
| --- | --- |
| Windows 11, Intel/AMD x64 | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` |
| Mac with Intel processor | `Herps-Launcher-0.1.0-macOS-Intel.dmg` |
| Mac with Apple chip / ARM64 | `Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg` |

Mac: **Apple menu → About This Mac** identifies the processor. Windows:
**Settings → System → About → System type** should say x64-based processor.
Do not use these Windows files as a native Windows-on-ARM package.

Download `SHA256SUMS.txt` too. Verify the file before opening it:

```powershell
# Windows PowerShell, in the download folder:
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
```

```bash
# Mac Terminal; substitute your actual DMG path:
shasum -a 256 "$HOME/Downloads/Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg"
```

Compare all 64 hexadecimal digits with the same filename in `SHA256SUMS.txt`.
Stop if they differ. A CI download is an outer ZIP: extract it before hashing
its installer/DMG. [Full checksum instructions](INSTALLATION.md#verify-downloads).

## 2. Install

- **Windows:** close existing game/launcher/server processes, back up existing
  data, then run the installer. Choose a short folder you own and open **Herps
  Launcher** from Start. The optional portable ZIP must be fully extracted;
  run `Herps Launcher\Herps Launcher.exe`, keeping its supporting folders.
- **Mac:** open the verified DMG and copy **both** `Herps Launcher.app` and
  `Herspers Minecraft.app` into Applications. Eject the DMG, then open Herps Launcher.

Windows is unsigned; Mac apps are ad hoc signed and not notarized. Review only
per-app security prompts for the verified download. Do not disable antivirus or
Gatekeeper. [Security prompts and installation](INSTALLATION.md#install-the-launcher).
**Physical Mac installation/gameplay remains NOT RUN.** Native CI is separate.

## 3. Prepare your own Minecraft resources

1. Install a full **JDK 25** for your CPU; a JRE alone is insufficient.
2. Use the official Minecraft launcher to install and start your legally owned
   **Minecraft Java Edition 26.3** once. Get that exact version's official server
   JAR from Minecraft's official version information. Keep the JAR unextracted.
3. In Herps Launcher → Settings, find the displayed game folder:
   - Windows: open that folder and double-click **Setup.cmd**.
   - Mac: run in Terminal:

     ```bash
     "/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
     ```

4. Select the matching server JAR when asked. Wait for **Resources are ready**.
   Stop on errors; do not substitute a modpack or another version's JAR.
5. Open Settings → **Validate installation**. Use **Find installation…** if needed.

[Detailed resource/JDK instructions](INSTALLATION.md#prepare-legitimate-minecraft-resources).
JDK 25 is for preparation; it does not enable Java mods. No Rust/Cargo is needed.

## 4. Play in a new profile

On Home choose **+ New profile**, name it `first_play`, then select it and click
**PLAY →**. Create a small new world, save/quit normally and wait for the exit
status before closing the launcher. Keep valuable existing worlds backed up.

For optional chainmail crafting, make a **different fresh disposable profile
before creating a world**. Follow [the Chainmail steps](INSTALLATION.md#test-chainmail-plate-and-boots).
The package starts OFF and must be enabled on Mods. Keep it enabled once saves exist.

## If something goes wrong

Use Home → **Open launcher and game logs**. Read
[troubleshooting](INSTALLATION.md#troubleshooting) before deleting or changing
anything. Earlier logo stalls and initially empty crafting output remain
unresolved; later success did not prove a fix. Mac gameplay and unreported
edge cases remain NOT RUN. Full RLCraft/FunCraft and original Forge/Fabric JAR
execution are unsupported. [Backups and updates](INSTALLATION.md#back-up-worlds).
