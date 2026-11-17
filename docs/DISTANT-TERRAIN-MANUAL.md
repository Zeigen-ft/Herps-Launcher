# Native explored-terrain LOD: Stage 1 manual checks

This is an experimental client rendering feature for Herps. It stores a coarse
view of terrain the client has actually received and can show that view beyond
the normal full-detail render distance. It does not request new terrain from a
server, simulate distant chunks or execute Distant Horizons/Java code. It is
off by default. Nothing in this checklist is a physical PASS until a tester
runs it and records the result.

Use a disposable profile and world first. Keep your normal world backup. Record
the candidate commit/run, OS, GPU, normal render distance and LOD settings with
each test. Source/CPU/CI tests are separate evidence from what you see in-game.

## Enable it

1. Start the candidate and open its graphics settings, then **Advanced**.
2. For a focused Stage 1 test, leave the older **LOD Distance** option **Off**.
   That separate existing option can generate far terrain for local worlds;
   the new **Explored Terrain LOD** option is the received-terrain-only mode.
3. Set **Explored Terrain LOD** to **On**. Begin with the defaults below and a
   normal full-detail render distance of about 4–8 chunks.
4. Walk around to receive chunks, then move far enough away that the first
   area leaves full-detail range. Look back from a hill or other clear view.
   Terrain that has never reached this client remains absent from the cache.

The settings are saved in `horizon-graphics.txt` in the current client
game/profile folder, beside `options.txt`. Close the game before editing the
file by hand. The new settings are:

```text
visitedLod:false
visitedLodRadius:64
lodMemoryMiB:64
lodDiskMiB:512
lodWorkers:1
```

Change the first value to `true` to enable the feature. The supported bounds
are radius **16–256 chunks**, LOD memory **8–512 MiB**, disk cache
**16–4096 MiB**, and LOD workers **1–4**. Invalid numbers fall back to defaults;
valid out-of-range numbers are clamped. These budgets apply to LOD data, not
all of Minecraft's textures, full chunks, normal worker threads or total game
memory. The client can recreate the LOD worker/cache when its limits change;
radius changes apply during subsequent world updates. A cache rebuild can
temporarily remove far terrain until results return.

## Cache location and preservation

Stage 1 stores its disposable rendering cache under:

```text
<current client game/profile folder>/herps-lod-cache/v1/<opaque-scope-fingerprint>/
```

It does not replace world region files, inventory data or normal chunk storage.
The fingerprints distinguish local world paths or remote server contexts,
dimensions and the engine/registry identity used by the client. They are not
the server's authoritative world UUID: that value is not available in the
current protocol. A reset world on the same server address with the same
advertised hashed biome seed can temporarily show stale cached terrain until
the client revisits it or its LOD cache is removed. Do not treat cached terrain
as proof of the current world state.

To reset LOD data, close the client and remove only the relevant directory
inside `herps-lod-cache`. Do not delete `saves`, `region`, `playerdata`,
`datapacks`, resource-preparation files or launcher profile configuration.
The next visit must receive chunks again before their distant terrain returns.

## Manual acceptance checklist

Fill in PASS, FAIL or NOT RUN for every row. If a test was not observed, leave
it NOT RUN. Report the first console/log error and surrounding lines; redact
private addresses, usernames, personal paths and credentials before sharing.

| Test | Steps and expected evidence | Result |
| --- | --- | --- |
| Default-off baseline | In a fresh profile, verify Explored Terrain LOD is Off. Play, leave and reopen a world. No Stage 1 workers/cache writes should begin while it remains disabled. Keep the separate legacy LOD option Off for this check. | NOT RUN |
| Explore and look back | With a short normal render distance, walk a recognizable route, then look back from beyond that distance. Only previously received terrain should appear as simplified far geometry. Compare hills, water and biome colors against full-detail terrain. | NOT RUN |
| Unvisited areas | Face unexplored areas outside full-detail range. Confirm the system does not invent terrain or make extra server terrain requests. Empty areas are expected until visited. | NOT RUN |
| Ring and return transition | Move slowly across the full-detail/LOD boundary in both directions, then sprint and teleport across it. Look for overlapping surfaces, z-fighting, flashing, gaps or visible tile edges. The existing renderer's approximately 600 ms fade should be checked visually, not assumed from code. | NOT RUN |
| Coarse geometry | Inspect flat terrain, hills, sharp cliffs, trees, coastline and water from several distances. Check the 2×2, 4×4 and 8×8 chunk-scale reductions for plausible heights/colors and no fabricated coverage over unknown cells. Record distracting artifacts. | NOT RUN |
| Current edits | Revisit a cached area, change its surface in a disposable world and leave again. Check that the refreshed distant view eventually replaces the older view. Distant edits that the client has not received can remain stale. | NOT RUN |
| Reopen cache | Explore an area, leave full-detail range, exit normally and reopen the same profile/world. Check that persisted far terrain returns without needing Java tools. | NOT RUN |
| Profile/world isolation | Use two disposable worlds with different terrain at the same coordinates and two separate profiles. Verify that one world's cached view does not appear in the other. | NOT RUN |
| Dimension isolation | Visit at least Overworld and Nether, then return. Check that the dimensions do not reuse each other's terrain and that unsupported visual conditions are reported clearly. | NOT RUN |
| Disabled behavior | Turn Explored Terrain LOD Off. Confirm the new far geometry disappears, normal full-detail terrain still renders, and the client remains usable. Repeat during active cache work. | NOT RUN |
| Memory/worker budget | Set the smallest supported limits and explore enough terrain to apply pressure. Monitor the feature's allocations and LOD worker count, distinguish them from the whole game's RSS/other threads, and record frame stalls or growing usage. Repeat with larger limits. | NOT RUN |
| Disk eviction | Use a disposable cache and a small disk limit. Explore enough terrain to require eviction. Check that the LOD cache stays bounded and that evicted terrain can be learned again after visiting. Keep normal saves intact. | NOT RUN |
| Invalid config | Close the game, copy `horizon-graphics.txt`, then try missing keys, invalid text, negative numbers and very large values for the five new fields. Reopen and verify safe defaults/clamps and a working options screen. Restore the copied settings afterward. | NOT RUN |
| Corrupt cache | With the client closed, copy its disposable LOD cache, then truncate one cache file inside that directory. Reopen. It should skip unusable LOD data without corrupting or restoring over the real world. Never alter vanilla region files for this test. | NOT RUN |
| Disconnect/reconnect | On an existing test server, explore, disconnect and reconnect; close/relaunch the client too. Confirm the server/world still work. This test exercises ordinary received chunks only; there is no Stage 1 server streaming extension. | NOT RUN |
| Save/profile preservation | Create a real disposable world, place recognizable blocks, retain named inventory items, save and close both game and launcher, then reopen. Verify world, inventory and profile selection. This requires real gameplay evidence. | NOT RUN |
| Failure recovery | Only on a disposable copy, interrupt the client during LOD cache work and reopen. Check that a partial cache write is ignored and world loading still works. Do not call a normal restart a crash-recovery PASS. | NOT RUN |
| Platform validation | Repeat applicable checks on physical Windows x64, macOS ARM64 and macOS Intel. A native CI build or offscreen fixture is not proof of interactive graphics acceptance. | NOT RUN |

## Known Stage 1 limits

* Only received/explored terrain is available. There is no server-side LOD
  generation, custom LOD streaming protocol or automatic knowledge of distant
  world edits.
* Coarse surfaces are approximations. Fine buildings, caves/overhangs, foliage,
  transparent materials, emissive blocks and flowing fluids may lose detail or
  require further work. Do not rely on the cache for navigation or safety.
* Cached colors/tints depend on the resources active when the client captured
  terrain. Resource-pack, graphics or world changes can require a cache reset.
* The same-address/same-seed remote world-reset ambiguity described above is
  unresolved; this is a rendering cache, not an authoritative world identity.
* Memory and disk limits intentionally evict data. A small budget can leave
  holes in a previously explored route; revisiting can repopulate it.
* No Distant Horizons source/JAR is used by this original extension. It is not
  a complete Distant Horizons port and does not claim compatibility with that
  mod's Java clients, cache files or network protocol.
* Authentication, ownership/resource verification, licensing checks and the
  Horizon mod system are outside this stage. Existing behavior is preserved.

Stop at a reproducible failure and report it with the candidate identifier and
settings. Do not mark Stage 1 fully accepted while the physical checklist is
open, and do not merge unfinished work into `main`.
