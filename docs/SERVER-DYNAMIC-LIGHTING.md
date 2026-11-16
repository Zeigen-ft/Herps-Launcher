# Herps 26.3 server dynamic lighting — experimental 0.1.0

This is a small native server datapack adapted from your Dynamic Lighting 1.0
upload. It contains no Java code and needs no Forge, Fabric, Java mod loader,
Rust compiler, or OptiFine installation. It is **not full OptiFine** and is not
yet accepted for an important or public server. Physical multiplayer lighting,
save/restart and cleanup tests are **NOT RUN** until you test them.

## What it does

When enabled, held main-hand/offhand items and dropped items near players
create temporary, real light blocks in ordinary air. Light tiers are:

* 15: lantern, glowstone, sea lantern, jack o'lantern, shroomlight, beacon, froglights.
* 14: torch, campfire, lava bucket, end rod.
* 10: soul torch/lantern/campfire, redstone torch, glow berries.
* 7: blaze rod/powder, glowstone dust, glow ink sac.

Higher light tiers take priority in the same cell. Held light is placed at
head height. Dropped items are limited to the nearest 32 within 24 blocks of
each player. Water, solid blocks, cave_air, void_air and existing light blocks
are never replaced. This version does not implement underwater, mob,
on-fire, shader, zoom, connected-texture or other OptiFine features.

These are **server light blocks**, so they can affect spawning and other light
checks. They are different from Options → Horizon Settings → Extras → Dynamic
Lights, which is a separate, render-only client setting. Leave that client
setting OFF for the first server test, so it cannot hide a server-pack failure.
Clients must actually connect to this server; no JAR goes in a Herps mods folder.

## Before installing (Windows 11)

1. Use your Herps 26.3 candidate with resources already prepared. The launcher
   candidate and resource preparation are separate from this small add-on.
2. Make a **new disposable server world** using your existing private host
   setup. Do not experiment on your only world. If you have not hosted before,
   see docs/HOSTING-TAILSCALE.md in the repository. Do not change your real
   server's authentication, port or network settings for this pack.
3. Start that world once, then type `stop` in the host console. Wait until the
   host process closes. Close any other game or host using that world.
4. Find that world's folder: it contains `level.dat` and `session.lock`.
   Hosting prints the server folder. Existing default host locations are
   `%LOCALAPPDATA%\Herspers Minecraft\servers\tailscale` or the older
   `%USERPROFILE%\Documents\Herspers-Server`. Search **inside your selected
   test server folder** for `level.dat`; do not assume the server folder itself
   is the world. Custom server/world locations can differ.
5. Download the Windows test bundle from the successful server-lighting Actions
   run, extract its outer artifact ZIP, then extract
   `Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test.zip` into a new folder.
   Do not run anything from inside a ZIP. Check its checksum against the run's
   `SHA256SUMS.txt` using PowerShell:

   `Get-FileHash -Algorithm SHA256 "C:\path\Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test.zip"`

## Install and turn on

1. Double-click `Install-Lighting.cmd`. No administrator permission is needed.
   The command uses Windows PowerShell for this local script only; it does not
   change your permanent PowerShell policy. If your managed PC blocks scripts,
   ask its administrator rather than disabling system security.
2. Paste the full disposable **world** folder path when asked.
3. Confirm that the host is closed and type `INSTALL TEST PACK` exactly.
4. Wait for `VERIFIED BACKUP`, then `INSTALLED`. Copy the backup location.
   A complete file copy and SHA-256 manifest are stored in the sibling
   `.herps-lighting-backups` folder. Only transient `session.lock` is excluded.
   The installer refuses existing packs, active world locks and links/junctions.
   A failed backup prevents pack installation. It does not start the server.
5. Restart the **same disposable host**. In the server console, without a `/`,
   type `datapack list enabled`. Check for
   `file/Herps-Server-Dynamic-Lighting-0.1.0.zip`.
6. Type `function herps_dl:enable`. It starts disabled on its first load.
   Your enabled/disabled choice is saved by the world's scoreboard on normal
   shutdown. Do not remove the `herps_dl` objective or kill its markers manually.

## Short real-server acceptance test (not yet verified on hardware)

Use a disposable world and preferably two real connected players. Record the
candidate/run, pack checksum, client settings and actual results. Do not mark
these passed merely because installation or automated validation succeeded.

1. With client Dynamic Lights OFF, go somewhere dark. Hold a torch in the main
   hand. Check the surrounding world lights up. Ask a second player to observe.
2. Swap to the offhand, then an ordinary non-glowing item. Check light follows
   you and disappears behind you. Test lantern (15), torch (14), soul torch
   (10), and blaze rod (7). Hold bright and dim items together: bright wins.
3. Drop a torch nearby. Check it lights the ground; pick it up and check cleanup.
   Try two sources in the same cell and a transition from bright to dim.
4. Walk, sprint, teleport, die/respawn, change dimensions, disconnect/rejoin.
   Confirm no stuck lights, marker buildup, console errors or severe lag.
5. Test at ordinary air next to water and solid blocks. They must remain intact.
   Existing manually placed light blocks must remain intact. No underwater
   lighting is expected. A source in cave_air/void_air intentionally does nothing.
6. Type `function herps_dl:disable`. Loaded owned lights should disappear.
   With the client setting still OFF, verify it is really dark again. Re-enable.
7. Type `save-all`, then `stop`. Restart and reconnect. Verify the world, builds,
   inventory and lighting behavior are preserved. Test abrupt-stop recovery
   only on a separate disposable copy; it is not verified by a normal restart.
8. Report each test PASS/FAIL/NOT RUN. More players, 32+ nearby drops, long
   sessions, custom dimensions, macOS hosting and cross-version worlds remain
   unverified unless explicitly tested.

## Disable, uninstall, and preserve the world

Run `function herps_dl:disable` while the pack is still installed. Visit every
area/dimension where you used it, allowing cleanup while chunks load. Then
`save-all`, `stop`, and close the host. Remove **only** the named pack ZIP from
that test world's `datapacks` folder. Never use a broad `/fill ... air replace
light`; it could destroy unrelated lighting. Keep the backup.

Only loaded chunks can be cleaned. If chunks remain unloaded, retain this pack
disabled until those chunks have loaded and been cleaned. Removing it earlier
can leave saved lights/markers. The pack checks marker ownership and matching
light level, but cannot distinguish another person's identical replacement of
an owned light in the same cell. Avoid editing those cells during the test.

To restore, keep the server stopped, copy the backup's `world` folder to a
**new, empty, separately named disposable world location**, verify its files
against `manifest.json`, and point a separate test host to that copy. Never copy
over an existing save. Do not combine pre-test and post-test region files.
There is no automated restore or production-world migration in this installer.

## If something fails

* No light: check the correct host/world and enabled datapack, run the enable
  function, use a listed item over ordinary air, and keep client-only dynamic
  lighting OFF during diagnosis. Do not install the original JAR into Herps.
* Installation stops: stop the host; check the world path, available disk
  space, checksum and console message. Links, junctions and already-installed
  copies are deliberately refused. Keep the backup even after a failure.
* Errors or lag: disable the pack before stopping; preserve the console log.
  Do not keep retrying on an important world. Cleanup/replacement happens every
  tick, so server performance and visual flicker require real testing.
* Share the first error, surrounding console lines and your test results.
  Redact usernames, tokens, private addresses and personal file paths. Do not
  upload your world or credentials. Say whether one or two players tested.

## License and source

AGPL-3.0-only, adapted from quillphen's Dynamic Lighting 1.0. See NOTICE.txt and
LICENSE.txt. Full preferred source is in `source/`; with Python 3.11+ a developer
can rebuild using `python source/tools/build_server_lighting.py --output output`.
Players do not need Python. No OptiFine or proprietary mod is redistributed.
