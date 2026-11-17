# Native explored-terrain LOD — Stage 1 verification

Status: **implementation and automated checks PASS; interactive acceptance OPEN**.
Branch: `feature/herps-distant-terrain`, based on
`7f6840eb9f4ff7fdc833da1d3d15424b5d08efaa`.
Verified code: `0a52572a5a94c763dc298328fde471c84f66d03f`.
No merge into main, tag or public release was created. The original native
verification run below produced logs only. A later
[Windows installer/portable candidate](DISTANT-TERRAIN-WINDOWS-CANDIDATE.md)
from `44b21a8` is built and independently audited; physical acceptance stays open.

## Implemented behavior

The pinned engine already had native voxel-column LOD meshes, terrain material
and biome tint handling, near-chunk cutouts and 600 ms ordered-dither fades.
Stage 1 adds an original, separate **received/explored terrain only** source to
those APIs. It never uses the legacy generator-backed sampler for this mode.
The existing generated LOD option remains separate and retains its behavior.

* Capture block/biome section snapshots before both normal unload and remote
  chunk-forget/range eviction; resident observations also refresh edited areas.
* Summarize top solid surfaces and optional fluid surfaces with material and
  biome IDs. Coarse reductions preserve meaningful material/tint information,
  average heights deterministically and leave unknown footprints absent.
* Mesh multi-chunk tile scales using the existing simplified native mesher,
  exclude the normal render area, publish replacement cohorts atomically and
  reuse native fades/depth treatment. Approximate terrain is visual only and
  does not supply gameplay raycasts, authoritative blocks or simulation.
* Store versioned, endian-defined, checksummed cache records separately under
  the client profile's `herps-lod-cache/v1/<combined scope fingerprint>/`.
  Bounds, atomic replacement, refreshed records, recency eviction and corrupt
  cache misses protect play and preserve unknown files. Normal close flushes
  the final bounded observation queue. No save/region/inventory files are edited.
* Add an Advanced graphics toggle (Off by default), radius 16–256 chunks
  (default 64), CPU LOD cache budget 8–512 MiB (64), per-scope disk budget
  16–4096 MiB (512) and 1–4 LOD workers (1). Existing graphics settings remain.

Read the short [renderer/chunk-storage design](DISTANT-TERRAIN-ARCHITECTURE.md)
and [manual test/build checklist](DISTANT-TERRAIN-MANUAL.md).

## Final automated evidence

| Check | Result |
| --- | --- |
| [Native Windows run 44093952683](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44093952683) | **PASS** |
| Actual patched native LOD/cache/downsampling/mesh/fade unit tests | 50 passed, 1 ignored |
| Native graphics defaults/config round-trips/clamps | 9 passed |
| Native graphics UI settings/ranges | 14 passed |
| Complete `horizon-client` integration with existing `mods` feature enabled | `cargo check --locked` **PASS**; no mod-system implementation changes |
| Exact overlay/source/default/client-only checks | 4 passed |
| [Platform regression run 44093952949](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44093952949) | Both Windows and Linux jobs **PASS** |
| Windows source/tooling regression | 524 total: 419 passed, 105 skipped |
| Linux source/tooling regression | 524 total: 406 passed, 118 skipped; counts independently read from job 134076058039 |
| Exact pinned patch preparer regression, local | 25 passed |
| Separate codec/cache harness, local | 8 passed using actual staged codec/cache modules with minimal type fixtures; this is additional fixture evidence, not gameplay |

The native mesh case specifically checks a received surface's tint, full-detail
chunk exclusion, missing-region exclusion and the remaining top-face area.
The new cache/source tests cover negative coordinates, multi-scale reduction,
serialization/reopening/refresh, CRC/header/payload damage, truncation and
bounded decompression, recency/quotas, modified registry keys and link refusal.

Pinned engine: `7301f6fdd7f470b11317276e7a11b4dc615c137a`.
Rust: `1.95.0`. Prepared overlay fingerprint:
`ef2fdf978aa5b54112c267906f6bb7f090fe8fdb94a96cf8a24ca07a60e03502`.
Native tests/type-check use no world assets, Java execution or real server.

## Failures, fixes and skipped checks

* First native run [44092304262](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44092304262)
  passed the initial 49 LOD tests, 9 settings tests and 14 UI tests, then failed
  the game type-check on three integration errors: two incorrect registry field
  accesses and an optional retiring chunk passed where a slice was expected.
  These were fixed in `a674dd12136ea0d8e0f0820f49ca2f1458161585`.
  Corrected run [44093556363](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44093556363)
  passed before the additional direct heightmap mesh regression was added.
* An initial static source guard also matched `std::process::id()` used only
  by a unit-test temporary-directory helper. It now checks production source
  separately. No imported code was executed.
* The local full regression ran 524 tests: 504 passed, 19 skipped and one
  pre-existing launcher fixture could not bind its owned loopback port in the
  sandbox. A permitted rerun of that module passed all four tests, including
  its 31 native cases; no production behavior was changed to mask the restriction.
* The native ignored test requires `HORIZON_TEST_RESOURCES` (prepared game
  models/textures). It was **NOT RUN**. Do not infer resource-backed rendering
  or gameplay from the other unit tests.
* The existing separate shader-compatibility workflow was skipped by its
  pre-existing repository guard. No shader/graphics acceptance is inferred.
  Other source-suite skips reflect unavailable host/backend/fixture cases.

## Verification artifact

Artifact **Herps-Distant-Terrain-Stage1-Verification-Windows**, ID **14332468382**:
[download verification logs and JSON](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44093952683/artifacts/14332468382).
It contains `distant-terrain-native.log` and
`.cache/distant-terrain-verification.json`. The downloaded ZIP was independently
checked against GitHub's digest and its JSON identifies the verified commit and
overlay above. **This artifact is not a launcher/game installer.**

ZIP size: 9,408 bytes. SHA-256:
`730d9e18edb638039342c7bddbc38cb1a360fcc5e36d050bde00582608d15952`.
The receipt is also retained in [DISTANT-TERRAIN-CI.json](DISTANT-TERRAIN-CI.json).

## Remaining acceptance and limitations

Every physical Windows/macOS graphics/gameplay, seam/z-fighting, frame-rate,
save/relaunch/restore and crash-recovery checklist case is **NOT RUN**. Native
macOS compilation and a release-profile game binary are also **NOT RUN** for
this stage. The later Windows candidate uses the optimized `fast` build profile
and has passed automated packaging/lifecycle checks. This is an experimental
feature branch.

The CPU budget covers bounded derived LOD data and working reserves, not total
game RSS, full-detail chunks, textures or the GPU arena. Captures retain only
block/biome sections and obey an eight-entry/byte limit; rapid travel or small
budgets can omit captures/geometry. Disk quotas are per combined world/dimension
scope, with a 4,096-record cap and one bounded temporary record during atomic
replacement. Multiple scopes use additional disk space; cache I/O performance
at large scope counts still needs profiling.

The standard protocol has no authoritative world UUID. Profile, local world
path or remote endpoint, received seed, dimension and actual registry mappings
separate normal scopes. Reusing the same location/endpoint and seed can replay
stale visual data until revisited or manually cleared. Distant edits that the
client never receives remain unknown. Heightmaps approximate caves, overhangs,
small structures and foliage. No LOD cell samples beyond the supported bounded
footprint are guessed.

No Distant Horizons source was adapted and no JAR was executed. New code is an
original extension of the existing native renderer. No server streaming,
authentication, licensing/ownership verification or Horizon mod-system files
were changed, and the existing upstream lock and licence notices remain intact.
`main` remains `b292a48c279c2b718a5395fe5558f2ff83dcea30`.
