# Windows: install Herps Launcher and prepare Minecraft 26.3

This is the shortest supported Windows x64 installation route for **Herps Launcher 0.1.0 (prerelease candidate)**. For full requirements, backup instructions, platform limitations and security guidance, see [INSTALLATION.md](INSTALLATION.md).

> Herps Launcher is an unofficial launcher for a **native Rust client** using legitimately obtained Minecraft Java Edition 26.3 resources. It does **not** run original Forge/Fabric JARs or full RLCraft/FunCraft. Clean physical resource preparation on every PC has **not** been verified.

## Before starting

- Windows 11 x64 on Intel/AMD is the primary candidate target. Windows 10 is experimental.
- Have a legitimate Minecraft Java Edition installation and access to the **matching official 26.3 server JAR**.
- Have a **full JDK 25**, not only a Java runtime. Open PowerShell and check both:

  ```powershell
  java -version
  javac -version
  ```

  Both should show 25.x. If `javac` is missing, configure/install a full JDK 25. [JDK details](INSTALLATION.md#configure-jdk-25).

## Install and prepare (one pass)

1. **Back up existing data if updating.** Close the game and launchers. Copy `%LOCALAPPDATA%\Herspers Minecraft` to a separate dated backup outside the source folder. Never remove `%APPDATA%\.minecraft` to troubleshoot Herps.
2. **Download the Windows x64 package** from [Releases](https://github.com/Zeigen-ft/Herps-Launcher/releases), or if none is published, use a successful [CI workflow run](https://github.com/Zeigen-ft/Herps-Launcher/actions/workflows/herps-launcher.yml) you have access to. The CI artifact is an **outer ZIP**; extract it first. The release-ready artifact contains multiple platform files and is not itself a Windows installer.
3. **Verify the actual installer** against the `SHA256SUMS.txt` included for the **same run/release**. In PowerShell, from the extracted folder:

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe'
   ```

   Use the actual filename if different. **The GitHub Actions artifact ZIP SHA-256 is not the installer SHA-256.** If the file checksum does not match its manifest, stop.
4. **Run the verified Windows setup EXE**, choose a short writable installation path and open **Herps Launcher**. Alternatively, fully extract the portable ZIP and run `Herps Launcher\Herps Launcher.exe` without separating it from its support folders. Windows builds are unsigned; do not globally disable security protections.
5. **Prepare official Minecraft inputs.** Use the official Minecraft launcher to install and start **Java Edition 26.3** once. Obtain the matching **official 26.3 server JAR** from official version information; keep it as a `.jar`, not an extracted folder.
6. **Run preparation.** In Herps Launcher → **Settings**, open the displayed Herspers game folder and run **Setup.cmd**. In a portable installation, it is under `Herps Launcher\game\Herspers-Minecraft`. Provide the matching server JAR path when prompted. Wait for **Resources are ready**.
7. **Validate and play.** In Settings choose **Validate installation** (or **Find installation…** if necessary). On Home create a new disposable profile `first_play`, select it, click **PLAY →**, create a small world and save/quit normally.

No Python, Rust, Cargo or developer compiler is needed for ordinary installed play.

## If preparation reports an unknown 26.3 JSON / SHA-1

Example symptom: `26.3.json is not a 26.3 version file Horizon knows`. This is **not** evidence that JDK 25 is missing, and reinstalling Java alone will not resolve the metadata mismatch.

1. **Stop preparation and close the launchers.** Preserve the full error and logs; do not edit `%APPDATA%\.minecraft\versions\26.3\26.3.json` or bypass hash validation.
2. **Prefer the supported Horizon preparation flow** to download the official version metadata. Retry `Setup.cmd` with the matching official server JAR.
3. **Only if the preparer explicitly supplies an official Mojang metadata URL and a target manifest path**, download that exact URL and save its response to the exact requested path as `manifest.json` (not `manifest.json.txt`). The preparation folder name is attempt-specific; do not hard-code another user's hash-named folder. Do not substitute a random version JSON.
4. If retrying a failed attempt, close the game and launcher and **rename** `%LOCALAPPDATA%\Herspers Minecraft\preparation` to `preparation-old` rather than deleting it. Then retry. Note that a new preparation attempt may create a **new target folder**; use the path from the *current* error.
5. If the **same hash rejection persists even with the official file**, collect logs and report the version, observed SHA-1, requested Mojang URL, and run/commit to the maintainers. Horizon's accepted metadata list or launcher integration may need a code update. Do **not** disable integrity checks.

If you cannot find `Setup.cmd`, the official 26.3 server JAR, or the intended game folder, stop and consult [the full guide](INSTALLATION.md#prepare-legitimate-minecraft-resources) instead of guessing.

## Final checks

- `java -version` and `javac -version` both show JDK 25.
- Preparation says **Resources are ready**.
- **Validate installation** succeeds.
- The new disposable profile launches and its new world saves and reopens.

For logs, backup/restore, unsigned installers, platform support and known unresolved gameplay issues, see [INSTALLATION.md](INSTALLATION.md). This document is installation guidance, **not** a claim that the 26.3 metadata mismatch has been fixed in code.
