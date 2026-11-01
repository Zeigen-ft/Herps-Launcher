# Install Herspers Minecraft on a Mac

This guide is for the **Java Edition Mac app**. The separate Herspers Bedrock 0.3.0 package currently supports Windows x64. You do not need Rust or Xcode to use a prebuilt Mac package.

Both Mac builds passed compilation and ad hoc signing checks. Installation, resource preparation and gameplay still need testing on a Mac. These are development builds, and they are not Apple-notarized.

## 1. Download the correct build

Open **Apple menu → About This Mac**:

- If it shows an Apple **M-series chip**, download [Apple Silicon / arm64](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41295959995/artifacts/13079675808).
- If it shows an **Intel processor**, download [Intel / x86_64](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41295959995/artifacts/13079341512).

Sign in to GitHub if asked. Open the downloaded ZIP, then open the application ZIP inside it. You should now have **Herspers Minecraft.app**.

Move the app into **Applications**. The commands below assume this location:

```text
/Applications/Herspers Minecraft.app
```

The app declares macOS 11 or newer as its minimum version. Compatibility with individual Mac models and macOS versions still needs testing.

## 2. Install the preparation requirements

You need:

- **JDK 25**, including both `java` and `javac`. For example, install [Eclipse Temurin JDK 25](https://adoptium.net/temurin/releases/?version=25) for macOS, choosing **aarch64** for Apple Silicon or **x64** for Intel. A JRE alone is insufficient.
- Your own installed **Minecraft Java Edition 26.3**. Launch that exact version once through the official Minecraft launcher so its game files and assets are present.
- The matching official **Minecraft Java Edition 26.3 server JAR**, downloaded from that version's official download information. Keep it somewhere you can find, such as Downloads. You will select this file during preparation; you do not need to start a server.

The uploaded Android app and this rebuild target Java Edition 26.3. A Bedrock installation or a different Java Edition version does not supply the required files. Minecraft assets are not included in the Mac download.

## 3. Prepare the game resources

Open **Terminal** from **Applications → Utilities**, paste this command and press Return:

```bash
"/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command"
```

A file picker will ask you to choose your Minecraft Java Edition 26.3 server JAR. Select the downloaded `.jar` file and wait for preparation to finish. Keep Terminal open while it runs.

Successful preparation ends with:

```text
Resources are ready. You can now open Herspers Minecraft.app.
```

If it reports an error instead, keep the full error message for troubleshooting. The preparation script checks that the game files match the pinned version.

### If your Minecraft installation is in a different folder

The default installation folder is:

```text
~/Library/Application Support/minecraft
```

To use another location, pass the server JAR as the first argument and your Minecraft folder as the second. Replace both example paths with your actual paths:

```bash
"/Applications/Herspers Minecraft.app/Contents/Resources/prepare.command" \
  "/absolute/path/to/server.jar" \
  "/absolute/path/to/minecraft"
```

## 4. Open the app

Open **Applications → Herspers Minecraft** after preparation succeeds.

If macOS blocks this downloaded development build, open **System Settings → Privacy & Security** and review the message for Herspers Minecraft. Use **Open Anyway** if that option is offered and you trust the downloaded build. On older macOS versions, the equivalent controls are in **System Preferences → Security & Privacy**. This app has ad hoc signatures, not Apple Developer ID signing or notarization.

If it says resources need preparation, repeat step 3 and check that Terminal reaches the success message.

### If Terminal shows only “button returned:OK” and “Process completed”

The older launcher stopped after its resource check failed and its setup dialog was dismissed. The game has not started. That message alone does not identify whether resources are missing or the bundled preparer could not run.

Run the preparation command in step 3 if you have not prepared resources. To see the actual check error, run:

```bash
cat "$HOME/Library/Application Support/Herspers Minecraft/logs/resources-check.log"
```

Updated launchers print the failure in Terminal and offer **Prepare resources** and **Show log** buttons. Preparation opens in Terminal; keep it open until it reports success, then open the app again. If preparation itself fails, use its error message to diagnose the missing requirement.

## Files and troubleshooting

The app keeps its data outside Applications, under:

```text
~/Library/Application Support/Herspers Minecraft
```

- `game/`: saves and game settings.
- `resources/26.3/`: prepared game resources.
- `preparation/`: preparation inputs and scratch files.
- `logs/resources-check.log`: startup resource-check results.
- `logs/launcher.log`: game startup output.

If Terminal reports **JDK 25 is required**, check that you installed the JDK for your Mac architecture, rather than only a JRE. If it reports **Minecraft folder not found**, launch the pinned Java Edition version once or use the alternate folder command above. If a JAR fails verification, use the matching official 26.3 file.

For a startup failure, include the exact error and relevant log text when reporting it. Do not include account tokens or private session files. Successful compilation alone does not establish working gameplay, audio, input or online-server compatibility.

To build from source instead of using a downloaded app, see [Build on a Mac](../README.md#build-on-a-mac). Build evidence and remaining validation limits are recorded in [Mac build results](MACOS-BUILD-RESULTS.md).
