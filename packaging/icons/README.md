# Supplied game icon

`game-source.png` is the user's original upload, byte for byte. Although the
uploaded filename was `download.ico`, its signature is PNG, 1254×1254 RGBA.
The green H and orange centre are preserved; conversion only resamples for
standard icon sizes and encodes the platform containers. Source/derived hashes
and the conversion tool version are in `provenance.json`.
Git attributes explicitly protect these binary assets from the text-patch
directory's line-ending normalization.

Committed build assets:

- `patches/assets/game.ico`: Windows file icon, nine sizes from 16 to 256 pixels.
- `patches/assets/game-window.png`: 64-pixel native game window/taskbar image.
- `patches/assets/game.icns`: macOS game bundle icon.

The source stager checks their pre/postimage hashes before replacing Horizon's
original game icon assets. It preserves the original upstream archive. Windows
also embeds and verifies the icon on the native `Herspers-Minecraft.exe` entrypoint.
The independent Qt **Herps Launcher** application and its desktop shortcut keep
their existing icon; this change is for the game, as requested.

Developer regeneration: `python tools/build_game_icons.py`, using Pillow at the
version recorded in provenance. Normal builds consume committed assets and need
no Pillow dependency. Verify asset hashes in `patches/upstream.json` afterward.
The supplied artwork is distinct from upstream Horizon branding; no third-party
authorship or licence transfer is inferred from its filename.

Windows resource bytes can be verified automatically. Actual Explorer/taskbar
appearance and Mac Dock/Finder appearance still require native manual checking;
OS icon caches may retain the previous image until the application is restarted.
