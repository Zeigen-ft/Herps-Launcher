# Install Herspers Bedrock 0.3.0 on Windows

This package targets **Windows 10/11, Intel/AMD x64 PCs** and **Minecraft Bedrock 1.26.60, protocol 2225**. It contains a native Rust client, Cinnabar, with its Go networking helper. The independent Herspers launcher starts that unchanged client in a separate process.

You do **not** need Java, a JDK, a manual `server.jar`, or Rust/Go developer tools. Those Java setup instructions belong to the earlier Herspers Java Edition package.

## 1. Download and extract

Open [Actions → Build Bedrock Windows app](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/workflows/bedrock-windows.yml), select a successful run, and download **Herspers-Bedrock-Windows-x64**. Sign in to GitHub if asked.

Extract the downloaded artifact ZIP and the application ZIP inside it. Keep the complete **Herspers-Bedrock** folder together, including its `engine` folder, manifests and licenses. Do not run the EXE from inside a ZIP or copy only the launcher.

Install the [Microsoft Visual C++ v14 x64 Redistributable](https://aka.ms/vc14/vc_redist.x64.exe) if it is missing. This is the engine's runtime prerequisite, not a developer tool; many PCs already have it. The launcher checks for the required runtime DLLs before starting the client and shows this link if they are missing.

Double-click **Herspers-Bedrock.exe** in the extracted folder. Cinnabar's original branding remains visible. The package is unsigned, so Windows may show a publisher warning; review the downloaded file's source before deciding whether to open it.

## 2. Complete the in-app first run

The client opens its own setup screen:

1. Read the Minecraft EULA shown by the app and accept it only if you agree.
2. Let the app download and prepare its pinned vanilla resources. Keep the window open while progress is shown; the first run needs Internet access.
3. Continue to the client menu when preparation finishes.

The launcher does not accept the EULA on your behalf. Minecraft assets are downloaded on your PC, not bundled in this ZIP. This version uses Cinnabar's fixed resource snapshot `v1.26.60.30-preview`; it does not automatically substitute the newest resource pack. Other game/protocol versions cannot be assumed compatible.

## 3. Join a server

Use the client's server menu and a server matching **Bedrock 1.26.60 / protocol 2225**. For online servers, Realms or friends' worlds, use the app's normal Microsoft device-code sign-in and your own account. Follow the Microsoft page opened by the app to finish sign-in.

Account sign-in and individual server/Realm compatibility are not established by package or integrity checks. Cinnabar is a custom client; movement/combat differences can trigger server anticheat. Check that the server permits the client you plan to use.

## 4. Create or import a world

Open the client's **Worlds** tab. Create a new world there, or choose **Import** and select your exported Bedrock **`.mcworld`** archive. Keep a backup of your original world before testing an import.

Natural terrain and vanilla mob behavior use the official **Bedrock Dedicated Server (BDS)** backend. The app handles its local-server setup and download when you first open an appropriate world, after the required EULA consent. You do not need to install a Java server or find a `server.jar`.

The bundled **Dragonfly** backend is a Go server with flat-world support and gameplay parity gaps. It is not a replacement for BDS natural-terrain worlds. Follow any backend/download error shown in the app rather than moving the same world database between different server backends.

Local-world behavior/resource packs, experiments, Education Edition and some world options remain unavailable or unqualified upstream. A world being recognized or imported does not prove every block, entity, add-on or game rule works correctly. Online play and world imports still need personal testing with your account and files.

## Your files and updates

Always launch **Herspers-Bedrock.exe** so this package uses its isolated profile:

```text
%LOCALAPPDATA%\Herspers Bedrock
```

- `config`: client/account configuration.
- `data`: prepared resources, worlds and persistent client data.
- `run`: runtime state.

The old Herspers Java Edition profile and a separately installed Cinnabar profile are not migrated automatically. Account/session data belongs in the local profile; do not include it in a ZIP or bug report.

Upstream self-update checks are disabled for this pinned portable package. To update, use a new complete Herspers Bedrock package from the repository. Keep the user profile and world backups; do not mix engine files from different versions.

## Check a damaged or incomplete extraction

Open PowerShell in the extracted application folder and run:

```powershell
.\Herspers-Bedrock.exe --verify-install
```

This checks engine files against the packaged SHA-256 manifest without starting the game, accepting an EULA or accessing accounts. If it fails, extract the original ZIP into a fresh folder and keep all its files together. The manifest is an integrity check against the package, not independent publisher authentication.

If setup or gameplay fails, keep the exact error message and relevant log text, without account tokens. Build, integrity and startup checks are different from successful rendering, account login, server gameplay or world import on your PC.

## Licensing and source

The Herspers launcher is **GPLv3**. Cinnabar and its upstream components retain their own licenses, including **PolyForm Noncommercial 1.0.0** for Cinnabar. The whole package is not relicensed as GPLv3, and it is not an all-Rust networking stack. Commercial use requires appropriate permission from Cinnabar's licensors.

See the repository's [Bedrock licenses and provenance](BEDROCK-LICENSES.md). Inside the ZIP, read **BEDROCK-LICENSES.txt** and the `licenses/cinnabar` files. Upstream source is [Cinnabar v0.1.31](https://github.com/cinnabar-mc/cinnabar/tree/v0.1.31).
