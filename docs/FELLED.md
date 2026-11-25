# Felled-style tree felling for Herps 26.3

This is native engine source for Herps Launcher and Minecraft Java 26.3. It uses
the pinned Horizon commit 7301f6fdd7f470b11317276e7a11b4dc615c137a. Raiiiden's
Felled 0.1.5 is the behavioral reference. This implementation uses Herps' own
block models, audio and particles.

## Build and enable

Apply the source patch to Herps Launcher at
b292a48c279c2b718a5395fe5558f2ff83dcea30, then use its normal native build.

- On Windows, run `pwsh -File scripts/build_windows.ps1`
- On Apple Silicon, run `bash scripts/build_macos.sh arm64`
- On an Intel Mac, run `bash scripts/build_macos.sh x86_64`

The commit is unchanged in the upstream lock. GitHub now serves its archive
under a `starling-` root after the upstream repository rename. The refreshed
archive was compared against all 4,159 blobs and modes in the pinned Git tree.
If your checkout cached the previous archive, move its generated
`.cache/upstream` folder aside before preparing again.

Both features start disabled. Use a disposable profile and an empty file for
each feature you want to enable.

| Mode | File and location |
| --- | --- |
| Client visuals | `felled-client.enabled` beside the profile's `options.txt` |
| Single-player server | `felled-server.enabled` in the same profile folder |
| Dedicated server | `felled-server.enabled` in the server working directory, beside `server.properties` |

Reconnect to reload the client flag. Restart the server to reload the server flag.
Remove the flag files to disable the features. Dedicated installations use the
rebuilt Herps engine for `--dedicated`. A server flag affects future cuts. Logs
already moved by the server are saved as normal blocks.

## What happens in game

Chop a qualifying tree's base with an axe. Sneak to chop normally. The scanner
needs a rooted trunk and a natural-looking crown with non-persistent leaves.
A 2×2 trunk waits until half the base has been cut. Branches and nearby leaves
are bounded by scan limits.

With the server flag enabled, a permitted base break can move the remaining tree
to a clear, grounded landing. Horizontal log axes follow the fall direction.
Foliage that would land inside terrain is shed. If every landing is blocked,
the base break proceeds normally. Landed logs can be walked on and
harvested with the usual server rules. A Herps client with visuals enabled
animates the server-directed fall and plays local impact effects. Other clients
on that server see the final blocks through vanilla block updates.

With only the client flag, the window plays a temporary local effect after the
server confirms your own base break. Standing blocks are hidden briefly in that
window's mesh. The server still controls collision, block state and drops.

## Parity limits

The server commits the landed blocks during the cut, and Herps clients animate
that move. Felled's Jolt rigid bodies, crushing damage, mid-fall collision and
riding, trunk snapping, buoyancy, fire, attachments, and its configuration are
outside this implementation. The natural-tree check uses block states as a
heuristic, so some player builds can resemble trees.

Original behavior reference [Felled by Raiiiden](https://www.curseforge.com/minecraft/mc-mods/felled).
