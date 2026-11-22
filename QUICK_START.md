# Quick start

Herps Launcher manages profiles and starts the native Herspers Minecraft client.
Packages are prerelease candidates. Minecraft resources are not included.

## 1. Download

Choose your platform from the [verified packages](release/0.1.0/README.md):
**Windows x64**, **Mac Intel**, or **Mac Apple Silicon**.
For the current development branch, use the
[verified Windows candidate](docs/DISTANT-TERRAIN-EDGE-WINDOWS-CANDIDATE.md).

Download the matching checksum file. Compare your installer/ZIP/DMG's SHA-256
using [these instructions](INSTALLATION.md#verify-downloads).
For Actions downloads, extract the outer artifact ZIP first.

## 2. Install

- **Windows:** run the Setup installer, or fully extract the portable ZIP.
  Keep all files together; open `Herps Launcher.exe`.
- **Mac:** open the DMG and copy **both** `Herps Launcher.app` and
  `Herspers Minecraft.app` into Applications. Eject the DMG and open Herps Launcher.

Back up existing worlds before replacing an installation. Close its game,
launcher and any server using those binaries. Review verified-app security
prompts; do not disable antivirus or Gatekeeper.

### Updating a Windows client for smoother terrain and display recovery

1. Download **Herps-Client-Update-Windows-x64** from the candidate's Actions run. Extract the ZIP and compare the setup file's SHA-256 with its accompanying checksum.
2. Close the game and launcher. If this PC also hosts a server using the same installation, type `stop` in its console and wait for it to finish saving. Run Setup over the existing install.
3. Open **Herps Launcher** from Start. Choose **Settings → Use game bundled with this launcher** to select the updated client, then select your usual profile. **Stable FPS · 60 FPS / 8 chunks** is optional.
4. Join your usual server. If the picture stops updating while gameplay continues, press **Ctrl + Shift + F8** once with the game window focused. This refreshes the Windows display in place. If menus or textures still look wrong, keep a screenshot and the client log from that session.

## 3. Prepare Minecraft resources — first time only

1. Install a full **JDK 25** matching your CPU.
2. Install your legally owned **Minecraft Java Edition 26.3** through the official
   Minecraft launcher and start that version once.
3. Obtain its matching **official 26.3 server JAR**. Keep it unextracted.
4. Run the bundled preparation tool:
   - **Windows:** open the bundled `game\Herspers-Minecraft` folder and double-click `Setup.cmd`.
   - **Mac:** open Terminal and run:

     ```bash
     "/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
     ```

5. Select the original server JAR when prompted. Wait for **Resources are ready**.
   If setup reports an error, fix that error before continuing.

The server JAR is a preparation input; you do not need to host a server.
[JDK and preparation details](INSTALLATION.md#prepare-legitimate-minecraft-resources).

## 4. Play through Herps Launcher

1. In **Settings**, select the bundled game folder/app and click **Validate installation**.
   After an update, check that the selected installation points to the new build.
2. On **Home**, choose **+ New profile** and name it `first_play`.
3. Select the profile and click **PLAY**.
4. Create a test world. Use **Save & Quit**, then reopen it to check your setup.

To join a server, use the launcher's **Multiplayer** page with the intended profile.

## Run Herspers Minecraft directly — Windows

Use the bundled `game\Herspers-Minecraft` folder or a verified standalone package.

1. Fully extract the game folder. Keep `bin`, `preparation` and the starter files together.
2. Complete the JDK/resource preparation above using `Setup.cmd`.
3. Open `Play.cmd` or `Herspers-Minecraft.exe`.
4. Create a test world, save and quit normally, then reopen.

**For launcher-managed profiles, use Herps Launcher → PLAY instead.** Direct
`Play.cmd` uses the standalone data workflow.

## Mods, backups and problems

- Install only supported native content. Follow the package's profile requirements;
  keep required mods enabled once a world uses them.
- [Chainmail setup](INSTALLATION.md#test-chainmail-plate-and-boots) ·
  [Backups and restore](INSTALLATION.md#back-up-worlds)
- Open **Home → Open launcher and game logs** for failures. Redact personal paths,
  credentials and private server addresses before sharing.
- [Troubleshooting](INSTALLATION.md#troubleshooting) · [Complete guide](INSTALLATION.md)

No Rust/Cargo is needed for normal play. Original Forge/Fabric JAR execution and
full RLCraft/FunCraft compatibility are unsupported. Physical Mac gameplay remains
NOT RUN; earlier startup stalls and empty crafting output have unresolved causes.

## Join a private game with your own name

1. Connect to the host's Tailscale network. Open **Herps Launcher → Multiplayer**.
2. Under **In-Game Player Name**, enter a name such as `CJ_Corto` and click **Save player name**. Each player needs a different name. Keep yours to keep using the same offline inventory.
3. Enter the host's address and click **JOIN**. You can also use **Home → PLAY → Multiplayer** after saving your name. A signed-in account uses its account identity.
4. If disconnected, read the message before returning to the server list. Rejoin the same address with the same name. See [Multiplayer troubleshooting](INSTALLATION.md#private-multiplayer-troubleshooting).
