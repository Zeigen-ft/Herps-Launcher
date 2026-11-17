# Stage 1: received-terrain LOD architecture

This describes the pinned native engine at
`7301f6fdd7f470b11317276e7a11b4dc615c137a` and the Herps Stage 1 patch.
The engine already has generated far-terrain LOD. Stage 1 adds a separate,
default-off **Explored Terrain LOD** mode whose source is restricted to chunks
the client has received. It reuses the native renderer instead of loading Java
or implementing the Distant Horizons protocol.

## Normal chunks: receive/load, mesh, unload

* `crates/horizon-client-render/src/world.rs` keeps resident columns in
  `World::chunks` as shared `Arc<Chunk>` values. A chunk covers 16×16 block
  columns and is divided vertically into sections. Normal blocks, lighting,
  entities and simulation remain authoritative here.
* `streaming.rs` coordinates chunk generation/loading, lighting and meshing.
  Mesh workers use `Mesher`, neighbor-aware `Region` inputs and reusable
  `MeshScratch`/`MeshTables` to produce `SectionMesh` terrain vertices. Finished
  section meshes return through `Streaming::update` and are uploaded by the
  game to the renderer's terrain arena. `Streaming::free` returns discarded
  mesh allocations to a worker rather than freeing a large batch in a frame.
* In local worlds, normal persistence stays in the existing save subsystem.
  `Game::update_world` receives unloaded `Arc<Chunk>` values, queues modified
  chunks through `save_later`, unloads entities and removes the corresponding
  GPU columns. Stage 1 does not replace that save path.
* For multiplayer, `game/remote.rs` applies ordinary server chunk/light
  packets. `NoTerrain` does not generate a server world. A
  `ForgetLevelChunk` packet or resized/moved remote storage calls
  `Streaming::forget`, which removes the resident column and returns its
  `Arc<Chunk>` before GPU/allocator cleanup.

## Stage 1 capture and cache

`game/visited_lod.rs` creates an `ObservedSource` only for the new mode.
`Game::update_world` observes received/resident chunk updates and prioritizes
columns that are leaving. The two remote unload paths capture the returned
chunk before it is freed. Background work summarizes each horizontal column's
top solid surface, optional water surface, block-state ID and biome ID.

The renderer derives top material/color and biome tint from those IDs and the
active resources. Cache data is a visual approximation; it is not a second
world store, collision map, block-interaction source or simulation input.

`lod/observed.rs` implements the existing `LodSource`/`LodSampler` interface.
It reads only observed summaries and their disk cache. It never asks a terrain
generator or server to supply unseen terrain. A tile has a 16×16 sample grid;
wider cells reduce known footprints into 2×2, 4×4 and 8×8 chunk-scale tiles.
Reduction uses deterministic surface/material voting and averaged heights;
missing chunks remain missing instead of borrowing an invented corner sample.
Footprints larger than 8×8 chunks remain absent in this stage.

`lod/visited_cache.rs` stores disposable, versioned `HVLD` records under:

```text
<client game/profile directory>/herps-lod-cache/v1/<opaque scope fingerprint>/
```

The scope includes local world path or remote endpoint/advertised hashed biome
seed, dimension and engine/registry identity. Records include coordinates,
bounded lengths and a checksum; writes stage a complete file and replace it
atomically. Corrupt/incompatible data is a cache miss. Quota eviction removes
only this format's owned records, leaving unknown files and actual saves alone.
The legacy generated-terrain cache remains separate.

The remote protocol supplies no authoritative persistent world UUID. Replacing
a world at the same endpoint with the same advertised hashed seed can therefore
leave stale *visual* cache data until revisited or manually cleared. Moving a
local save changes its path identity. These fingerprints are not authentication
or ownership verification.

## Rendering and resource limits

The existing `lod.rs` tile planner and `lod/mesh.rs` mesher produce simplified
terrain meshes. Stage 1 excludes the normal full-detail render area, even while
a normal mesh is still loading, and caps the outer range at the configured LOD
radius. No LOD geometry enters `World::chunks`.

`gfx/lod.rs` queues and uploads the far meshes in the existing terrain passes.
Its approximately 600 ms ordered-dither transitions and depth treatment are
reused when detail levels change. The received-only unload path avoids holding
full-detail GPU chunks indefinitely if cache pressure prevents a replacement.
Boundary appearance and absence of visible z-fighting still require the manual
graphics checklist; a code path or CPU test does not establish visual acceptance.

Configuration is independent of the legacy generated **LOD Distance** option:

| Setting | Default | Range |
| --- | ---: | --- |
| Explored Terrain LOD (`visitedLod`) | Off | Off/On |
| `visitedLodRadius` | 64 chunks | 16–256 chunks |
| `lodMemoryMiB` | 64 MiB | 8–512 MiB |
| `lodDiskMiB` | 512 MiB | 16–4096 MiB per cache scope |
| `lodWorkers` | 1 | 1–4 |

Memory accounting covers derived LOD cache/working data, with bounded queued
observations and transient worker allocations; it is not a cap on the game's
total RSS, full chunks, textures or GPU arena. The disk limit is per world and
dimension scope, so multiple retained scopes use additional space. Eviction or
rapid travel can leave visual gaps; receiving those chunks again can refill
the cache. Limits and exact acceptance evidence belong in the verification
report, not assumptions about the player's hardware.

## Scope and verification

The new extension is original Rust code around the existing native APIs. No
Distant Horizons source or JAR is adapted or executed. Server streaming,
authentication, licensing/ownership checks and the Horizon mod system are
outside this change. Existing generated LOD behavior remains a separate mode.

Use [the manual checklist](DISTANT-TERRAIN-MANUAL.md) for actual terrain,
transition, preservation, budget and platform acceptance. Native parsing,
serialization/mesh tests and CI compilation are automated evidence; all
interactive graphics/gameplay cases remain **NOT RUN** until observed.
