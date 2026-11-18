# Herps Launcher

A desktop launcher for the native Rust **Herspers Minecraft** client, with
profiles, saves and supported native content. Targets **Minecraft Java Edition
26.3 resources**. Current packages are **prerelease candidates**.

[Downloads](release/0.1.0/README.md) · [Quick start](QUICK_START.md) ·
[Complete installation guide](INSTALLATION.md) · [Support matrix](docs/HERPS-SUPPORT.md)

## Run Herps Launcher

1. **Download** the verified Windows x64, Mac Intel or Mac Apple Silicon package.
   Check its SHA-256. This branch's latest Windows build is
   [here](docs/DISTANT-TERRAIN-EDGE-WINDOWS-CANDIDATE.md).
2. **Install.** Windows: run Setup or extract the entire portable ZIP. Mac: copy
   **both apps** from the DMG to Applications.
3. **Get the requirements.** Install **JDK 25**, install/start your owned
   **Minecraft Java 26.3** once in the official launcher, and obtain the matching
   official server JAR.
4. **Prepare resources.** Run the bundled `Setup.cmd` on Windows or
   `prepare.command` on Mac. Select the unextracted server JAR and wait for
   **Resources are ready**. [Exact paths](QUICK_START.md#3-prepare-minecraft-resources--first-time-only).
5. **Validate.** Open Herps Launcher → **Settings**, select the bundled game and
   choose **Validate installation**. Check this selection after updating.
6. **Play.** Home → **+ New profile** → select profile → **PLAY**.
   Start with a test world, then save and quit normally.

## Run Herspers Minecraft directly — Windows

1. Open the bundled `game\Herspers-Minecraft` folder or a verified standalone package.
2. Keep the entire folder together and finish resource setup using `Setup.cmd`.
3. Open **`Play.cmd`** or **`Herspers-Minecraft.exe`**.
4. Create a test world, save and quit, then reopen.

Use **Herps Launcher → PLAY** for launcher-managed profiles.
[Step-by-step guide](QUICK_START.md#run-herspers-minecraft-directly--windows).

## Profiles, mods and multiplayer

- **Profiles:** create/select them on Home. Keep existing worlds backed up.
- **Native mods:** use Mods and follow each package's profile requirements.
  [Chainmail Plate and Boots](INSTALLATION.md#test-chainmail-plate-and-boots)
  starts disabled and requires an explicitly selected fresh disposable profile.
- **Servers:** use Multiplayer to connect. [Private Windows hosting](docs/INSTALL-WINDOWS.md#5-play-with-a-friend-using-tailscale).
- **Backups:** [create and restore backups safely](INSTALLATION.md#back-up-worlds).
- **Errors:** Home → **Open launcher and game logs**;
  [troubleshooting](INSTALLATION.md#troubleshooting).

## Optional development features

- [Native survival stages 1–4](docs/targeted-porting/NATIVE_SURVIVAL_STATUS.md): development paused.
- [Better Leaves](docs/BETTER-LEAVES.md) · [Photon native lighting](docs/PHOTON.md)
- [Server dynamic lighting](docs/SERVER-DYNAMIC-LIGHTING.md): user reports basic
  Windows lighting works in 0.1.1; broader acceptance remains open.
- [Experimental explored-terrain LOD](docs/DISTANT-TERRAIN-EDGE-FIX.md): Off by default;
  corrected-candidate physical retesting remains NOT RUN.

## Known limits

- Minecraft resources are **not bundled**. Obtain them legitimately.
- JDK 25 is needed for preparation; Rust/Cargo is not needed for normal play.
- Original Forge/Fabric JAR execution, Java bridges, Java Mods Build/Test and
  whole-Modpack Play are unsupported. Full RLCraft/FunCraft compatibility is unsupported.
- Windows packages are unsigned; Mac packages are ad hoc signed and not notarized
  unless a package-specific receipt states otherwise. **All physical Mac gameplay
  remains NOT RUN.** CI does not establish gameplay acceptance.
- Earlier loading-logo stalls and initially empty crafting output have unresolved
  causes. [Physical evidence](docs/targeted-porting/RLCRAFT_CHAINMAIL_VERIFICATION.md).
- User reports cover specific earlier Windows Chainmail/Survival candidates;
  Stage 4 and unreported edge cases remain open. See each feature's evidence.

## Development and licenses

[Developer setup](docs/HERPS-LAUNCHER.md) · [Source lock](upstream.lock.json) ·
[Migration and verification](docs/migration/README.md) · [Release notes](RELEASE_NOTES.md)

The original histories from `Zeigen-ft/Herspers-Minecraft` and this repository
are retained. Launcher code and new packaging/docs use [GPLv3](LICENSE).
Horizon and dependency notices remain under [licenses](licenses);
the initial destination MIT notice is preserved separately. Legacy Bedrock
terms are separate; no Bedrock binaries are included in the launcher packages.

Unofficial project; not endorsed by Mojang, Microsoft, Horizon's maintainers
or third-party mod authors.
