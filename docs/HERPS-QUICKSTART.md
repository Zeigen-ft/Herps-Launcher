# Use or integrate Herps Launcher

Herps Launcher manages **Herspers Minecraft Java Edition 26.3**. Choose a route:

- **Use Java Mods or Modpacks:** use the source feature branch described below,
  then follow [Java Mods](#java-mods-source-only) or [Modpacks](#modpacks-source-only).
- **Install the complete app:** follow steps 1–3 below.
- **Connect an existing Herspers game:** follow [Connect an existing installation](#connect-an-existing-installation).
- **Work on the source or integrate the feature branch:** follow [Source and repository integration](#source-and-repository-integration).

Bedrock is a separate application. These instructions use the Java Edition packages.

**Java Mods and Modpacks are available in source on
`feature/herps-java-compatibility`.** Phase 5B verified Windows builds and limited
installed offscreen smoke. The [Phase 5C report](herps/java-mods-phase5c-macos.md)
records macOS CI evidence; full native interactive acceptance and gameplay
remain unverified. The downloads below are historical packages from the earlier
launcher workflow. Phase 5A requires seven pages and a bundled
`horizon-port-pack`; see the [Phase 5A report](herps/java-mods-step5a.md) for
implementation and the Phase 5B/5C reports for native verification boundaries.
No GitHub Release was published for this feature branch. CI artifacts are
verification builds, not production releases.

For the current internal candidate hashes and native/manual acceptance status,
read [Phase 5D](herps/phase5d-release-readiness.md) and the
[support matrix](HERPS-SUPPORT.md). Use the [manual protocol](herps/native-acceptance.md)
for testing; the disposable CI installer verifier is not for personal machines.

## 1. Download your platform package

For the earlier packaged launcher, sign in to GitHub if prompted, download the
artifact, and **extract its outer ZIP**. These historical artifact links were
not revalidated during the Java Mods documentation work and may have expired:

| Your computer | Download | File to open after extraction |
| --- | --- | --- |
| Windows 10/11, Intel or AMD x64 | [Windows package](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41571739445/artifacts/13202422947) | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` |
| Mac with an Apple M-series chip | [Apple Silicon package](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41571739445/artifacts/13202148293) | The `.dmg` file |
| Mac with an Intel processor | [Intel package](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41571739445/artifacts/13202408890) | The `.dmg` file |

On a Mac, **Apple menu → About This Mac** shows whether you have an Apple chip or Intel processor. Herps Launcher requires macOS 12 or later.

### Windows installation

1. Install the [Microsoft Visual C++ x64 runtime](https://aka.ms/vc14/vc_redist.x64.exe) if it is missing.
2. Run the extracted `-Setup.exe` and choose an installation folder. Enable the optional desktop shortcut if wanted.
3. Open **Herps Launcher** from the Start Menu or desktop shortcut.
4. Continue to [Prepare resources and play](#2-prepare-resources-and-play).

For a portable installation, extract the inner application ZIP instead of running the installer. Open `Herps Launcher/Herps Launcher.exe` and keep its `_internal`, `game`, and `engine-source` folders with it.

The Windows build is unsigned. If Windows displays a publisher warning, review the download source. If you trust this build and Windows offers the option, choose **More info → Run anyway**.

### Mac installation

1. Open the extracted DMG.
2. Copy **both** `Herps Launcher.app` and `Herspers Minecraft.app` into **Applications**.
3. Open **Herps Launcher** from Applications.
4. If macOS blocks this development build, review **System Settings → Privacy & Security** after attempting to open it; on macOS 12, use **System Preferences → Security & Privacy**. Use **Open Anyway** if offered and you trust this build. These apps have ad hoc signatures and are not notarized.
5. Continue to resource preparation below.

If you intend to build native mods, also copy the complete `engine-source` folder out of the DMG to a permanent location, such as Documents. The launcher will need that folder after the DMG is ejected.

## 2. Prepare resources and play

If your Herspers Java 26.3 resources are already prepared on this computer, go directly to step 6.

1. Install a full **JDK 25**, including `java` and `javac`.
2. Install and launch your own **Minecraft Java Edition 26.3** once through the official launcher.
3. Have that exact version's matching official **server JAR** available. Keep the `.jar` file unextracted; it is a preparation input, and you do not need to start a server.
4. Run the existing preparation command for your platform:
   - **Windows:** in Herps Launcher, open **Settings** and find the displayed **Herspers folder / .app** path. Open that folder in File Explorer and double-click **Setup.cmd**. In the portable package, it is under `Herps Launcher/game/Herspers-Minecraft`.
   - **Mac:** open Terminal and run:

     ```bash
     "/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
     ```

5. Select or enter the matching server JAR when asked. Keep the preparation window open until it says **Resources are ready**. If it fails, resolve the displayed error before continuing.
6. Open **Herps Launcher → Settings → Validate installation**. If the game was not found, use **Find installation…** as described below.
7. Open **Home**, select the **default** profile, and click **PLAY →**.
8. After leaving the game, wait for its exit code to appear in the launcher. You can then press PLAY again.

Package validation checks the installed binaries; PLAY separately checks the prepared resources. Minecraft assets are not included. Custom Minecraft-folder instructions are in the [Windows guide](INSTALL-WINDOWS.md#command-line-setup-or-a-custom-installation-folder) and [Mac guide](INSTALL-MACOS.md#if-your-minecraft-installation-is-in-a-different-folder).

## Connect an existing installation

1. Close the game and its old launcher.
2. Open **Herps Launcher → Settings → Find installation…**.
3. Select the complete compatible package:
   - **Windows:** the `Herspers-Minecraft` folder containing `upstream.lock.json`, `build-metadata.json`, `bin`, and `Setup.cmd`.
   - **Mac:** the whole `Herspers Minecraft.app` bundle.
4. Click **Validate installation** and check the version and architecture shown.
5. Open **Home**, select **default**, and press **PLAY →**. Previously prepared resources and existing Herspers saves are reused.

**Find installation…** saves the selected path immediately. If you type a path manually, click **Save settings**. Select the Herspers package rather than `.minecraft`, a bare executable, `bin`, or `Contents/MacOS`: `.minecraft` is an input to resource preparation, while the selected package contains the runnable Herspers client.

This integration launches the existing client directly. It does not inject files into the official Minecraft launcher or require the original Horizon Launcher.

### Existing saves and profiles

The **default** profile uses existing Herspers game data:

| Platform | Default game data |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Herspers Minecraft\game` |
| Mac | `~/Library/Application Support/Herspers Minecraft/game` |

Use **Settings → Open game data and saves** to open the selected profile's folder. **Home → + New profile** creates a separate game folder; it does not automatically copy existing worlds. Close the game and wait for any build to finish before changing profiles, mods, shaders, or settings.

## 3. Install mods or shaders

### Runtime/content mods: `.hmod`

1. Choose your profile on **Home**.
2. Open **Mods → Import mod…** and select the `.hmod` file.
3. Select the imported mod's row and review its API, side, and capabilities. Imports start disabled.
4. Click **Enable / disable** to turn it on.
5. Return to **Home → PLAY →**.

Forge/Fabric/NeoForge `.jar` files cannot be loaded directly as `.hmod` files.
The source-only Java Mods page can inspect them and carry supported data; it
does not execute Java code. **Remove to backup** removes a Horizon package from
the profile while retaining a backup and its mod data.

### Native-source mods: `.hnmod`

1. Install Rust **1.95.0** using rustup and the native build tools: Visual Studio C++ Build Tools plus Windows SDK on Windows, or Xcode Command Line Tools on Mac.
2. In **Settings → Prepared native source**, paste the full path to the matching, complete `engine-source` folder **without surrounding quotes**. Review the other visible settings and click **Save settings**.
3. Import the `.hnmod` through **Mods → Import mod…**.
4. Select the row, review its source/compatibility, and enable it only if you trust it.
5. Click **Rebuild native mods…**, review the trust prompt, and wait for **Native build completed**. Compilation can take several minutes; its output appears in the Mods log panel.
6. Return to **Home → PLAY →**. The selected profile uses the matching rebuilt binary.

Native mods execute build scripts and game code with your permissions. Each supported platform/architecture needs its own build. Use **Roll back · disable all native mods** to select the original game binary again. If the enabled native-mod set changes, rebuild when requested. See [the compatibility contract](HERPS-LAUNCHER.md#mods-and-native-builds) for exact revision requirements. Windows native compilation and rollback were exercised in CI; Mac native-mod compilation remains unverified.

### Java Mods (source only)

Analysis needs the source launcher and a trusted `horizon-port-pack` binary built
from the pinned engine. It does not need Java execution, Minecraft assets or a
running game. Build/discovery instructions are in the
[Java Mods guide](herps/java-mods.md#prepare-the-source-launcher).

1. On **Home**, choose a profile; stop any game or background operation first.
2. Open **Java Mods → Select backend…** if the trusted tool is not discovered.
3. Choose **Import Java mod…** and select your own Fabric, Forge or NeoForge
   `.jar`. The launcher makes a profile-local copy and reads metadata only.
4. Select the row and click **Analyze**. Review the original backend verdict,
   conservative status, reasons, dependencies, mixins and unsupported features.
5. If files are missing, click **Resolve dependencies…**, choose your own mod
   folder or instance, and inspect the new result. No mod downloads or API keys
   are required. A present file still needs the correct version and evidence.
6. Review each licence. Restricted, non-commercial or no-derivatives content
   requires acknowledgement before the backend's local data carry-over; that
   acknowledgement grants no modification or redistribution rights.
7. For supported data-only content, use **Port to Herspers · data only**. A
   validated folder port appears under **Local data ports**, initially disabled.
   Use **Enable / disable**, **View compatibility details**, **Open mod directory**
   or **Remove to backup** there. Removal preserves saves, mod data and the
   imported JAR. Edited ports are preserved and rejected for review.
8. Use **View errors**, **Export JSON…** or **Export text…** for real diagnostics
   and evidence. Keep the retained input/run files for later revalidation.

**Requires porting** means a data-tier candidate, not native compatibility or
tested gameplay. **Unsupported** may mean missing evidence or known unsupported
features; inspect the reason and `insufficient_evidence` diagnostics. A Rust
`works` verdict can overlook dependencies or unreadable classes and is never
promoted directly to successful compatibility. Java code/loaders, a Java bridge,
universal conversion and Java **Build Mod / Test Mod** actions are unavailable.
A standalone JAR requiring a dependency ensemble may remain blocked even after
local files are supplied; a complete pack can carry only a validated subset.

### Modpacks (source only)

1. Open **Modpacks** in the same selected profile and choose the trusted backend
   if necessary.
2. Use **Import modpack…** for a Modrinth `.mrpack` or CurseForge ZIP, or
   **Import instance…** for your own Prism/MultiMC instance directory.
   **packwiz is not supported by the current backend.**
3. Click **Analyze pack**. The coverage table retains every indexed mod and
   unresolved manifest entry: name, version, compatibility, reason, licence,
   porting tier and missing dependencies. An unknown dependency list for a
   missing JAR does not prove that it has no dependencies.
4. Use **Resolve missing files…** with your own mod folder or installed instance.
   Known declared hashes are checked, including Modrinth SHA-512. A match is
   not authenticated publisher identity. CurseForge ID-only manifests need
   matching `minecraftinstance.json` metadata or hash/name evidence; renaming
   an arbitrary JAR to a placeholder cannot resolve an ID. No API key is needed.
5. Review licences before checking **I reviewed restricted licences**. Use
   **Port supported data…** to carry only the validated dependency/content
   subset into its private run folder. Unsupported and missing rows stay visible.
6. Review the summary, **View errors**, and export JSON/text evidence. Pack
   output is not automatically installed or enabled in existing game folders.

The **Port and Play** group always keeps **Play · unavailable** disabled.
Partial carry-over, a valid folder or an original `works` verdict does not
establish a fully playable modpack. There is no verified whole-pack content/
gameplay validation backend. Existing Home launching is a separate workflow.

| Feature | Source status | Verification |
| --- | --- | --- |
| Java JAR inspection, local resolution and reports | Available in source | Automated tests with owned fixtures; Windows/macOS unverified |
| Supported data-tier carry and Java Mods backup management | Available in source | Folder/hash/preservation tests; gameplay unverified |
| `.mrpack`, CurseForge ZIP and Prism/MultiMC coverage | Available in source | Real pinned backend + Qt tests; native platforms unverified |
| Java execution/bridge, universal conversion, packwiz, Java Build/Test, Modpack Play | Not available yet | No working backend; no success claim |

See the [full workflows and CLI examples](herps/java-mods.md) and
[release-readiness evidence](herps/java-mods-release-readiness.md).

### Shader packs

1. Open **Shaders → Import pack…** and choose a compatible shader `.zip` or `.hshader`.
2. Select its row and click **Select pack**.
3. Return to **Home → PLAY →**. The game loads and validates the selected pack on the actual GPU.
4. If it fails, close the game, click **Shaders → Restore default shaders**, and launch again.

Shader import/selection does not establish successful rendering. Mac uses Metal; Windows backend preferences are under Settings. Fullbright/resource-pack ZIPs belong in the game's resource-pack system; see [shader and resource-pack instructions](SHADERS.md).

## Play with a friend over Tailscale

1. Prepare resources on both computers, connect Tailscale, and grant the friend access to the host computer through your tailnet or device sharing.
2. On both computers, open **Multiplayer → Refresh Tailscale status** and check that it reports connected.
3. On the host, stop any old server with `stop`, then click **Open existing hosting console**. Read and accept the EULA if you agree, and keep that console open.
4. Copy the host address printed there, including the port, for example `100.80.12.34:25565`. Use the host's actual printed address.
5. On **both** computers, enter that address in **Host address**, enter different **Private player name** values of 3–16 letters, digits, or underscores, and click **JOIN →**. The host joins this way too.
6. Use **Save favorite** to keep the address. When finished, leave the game and type **stop** in the server console to save and shut down.

The host's Tailscale address is required; the private server binds to that address. The existing Herspers private-server behavior is preserved. An end-to-end two-computer session has not yet been verified. See [hosting details and troubleshooting](HOSTING-TAILSCALE.md).

## Source and repository integration

### Run the launcher from source

Use Python **3.12**. A compatible prebuilt Herspers game package is required for
Home gameplay, but not passive Java metadata analysis. The checkout includes no
compiled game binaries. In the existing checkout containing the local feature
history, preserve your changes and select:

```sh
git switch feature/herps-java-compatibility
git log -1 --oneline
```

In an isolated cloud task, use its existing checkout; no additional worktree is needed.
The new feature commits are local. A clone of `main` or the older cross-platform
branch does not establish that this implementation is present; transferring or
publishing its history requires a separate approved repository workflow.

**Windows, PowerShell:**

```powershell
py -3.12 -m venv .local\herps-venv
.\.local\herps-venv\Scripts\python.exe -m pip install -r herps_launcher\requirements.txt
.\.local\herps-venv\Scripts\python.exe -m herps_launcher
```

**Mac:**

```bash
python3.12 -m venv .local/herps-venv
.local/herps-venv/bin/python -m pip install -r herps_launcher/requirements.txt
.local/herps-venv/bin/python -m herps_launcher
```

Connect your prebuilt game through **Settings → Find installation…** when using
Home. Earlier downloaded packages bundle their Python runtime. The new Java
Mods/Modpacks source workflow additionally needs the separately built trusted
port-pack executable; it is not supplied by those historical packages.

Source-mode Mac hosting additionally needs its helper compiled at the path the development launcher uses:

```bash
mkdir -p .cache
rustc +1.95.0 --edition=2021 packaging/herps_host.rs -o .cache/herps-host
```

### Build distributable packages

`tools/package_herps.py` now builds the pinned `horizon-port-pack` for the native
Windows x64, macOS ARM64 or macOS x64 host and includes it with Python/Qt.
Packaging requires seven pages and actual bundled-helper metadata checks.
End users do not need Cargo/Rust for Java metadata analysis. Source development
and existing trusted native-mod builds have their own build requirements.
The [Phase 5A report](herps/java-mods-step5a.md) records Linux packaging-probe
evidence. See [Phase 5B](herps/java-mods-phase5b-windows.md) and
[Phase 5C](herps/java-mods-phase5c-macos.md) for native results. Full native
interactive acceptance remains open; these are not a production release.

The existing workflow's dispatch syntax for its older remote branch is:

```sh
gh workflow run herps-launcher.yml --repo Zeigen-ft/Herspers-Minecraft --ref feature/herps-launcher-cross-platform -f platform=all
```

It requires authenticated GitHub CLI access. This example does not publish the
local Java compatibility branch or prove that a new package works. Future
approved native verification should cover `windows`, `macos-arm64` and
`macos-x64`, inspect conclusions and retain installed-application evidence.

### Feature branch and release status

The Java Mods and Modpacks implementation is on
**`feature/herps-java-compatibility`**, preserving the older cross-platform
launcher. Steps 0–3 were committed locally; Step 4 updates documentation and
verification. No push, merge into `main`, publication or release was performed.
Source availability and passing fixture tests do not establish distributable or
gameplay readiness.

Keep `herps_launcher/`, its pinned requirements, `tools/package_herps.py`, `tools/ci_run.py`, `tools/smoke_herps_native.py`, the `packaging/herps*` files and shared `packaging/private_server.rs`, launcher tests, the Herps workflow, and the existing source locks, patches and engine fetch/build/package tools together. The launcher relies on the repository's source lock and engine package metadata; copying only the GUI file is insufficient.

## If a step fails

| Symptom | Next step |
| --- | --- |
| No installation found | Use **Find installation…** and choose the complete compatible Herspers package. |
| Resource validation failed | Run the selected game's preparation command with JDK 25 and the exact matching game files; inspect `resources-check.log` in the launcher data folder. |
| Native mods need rebuilding | Set the matching prepared source folder, check Rust/build-tool availability, and run **Rebuild native mods…**. |
| Shader failure | Use **Restore default shaders** before retrying. |
| Game exits with an error | Use **Home → Open launcher and game logs** and inspect the newest run log. |
| Java/pack backend missing | Select a trusted pinned executable with **Select backend…**; historical packages do not bundle it. |
| Original verdict says `works` but status is Unsupported | Read the conservative reasons: missing files/dependencies, unreadable classes, mixins or incomplete evidence remain blockers. |
| CurseForge ZIP still has unresolved IDs | Supply a matching installed instance or declared hash/name evidence; no API-key lookup or filename guessing is performed. |
| Modpack Play or Java Build/Test is disabled | These actions have no working validation/execution backend and are intentionally unavailable. |

For validation results and remaining limits—including gameplay, shader rendering, live multiplayer and signing—see [the full launcher guide](HERPS-LAUNCHER.md#verification-boundaries).
