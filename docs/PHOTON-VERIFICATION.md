# Photon fullbright verification

Branch: `feature/photon-fullbright`, based on Better Leaves commit
`98f961ed85db4cbc5a8c40a207af14dc6188e4ba`. RLCraft work remains paused.
No public release, main merge or proprietary pack redistribution is authorized
or performed by this work.

## Inspected input

- Original `Photon [3.1.2-M1].zip`: 3,657 bytes, nine entries (five files).
- Archive SHA-256: `a51dc9c24afa8d98f75fa88abe6308774625cd10a126c62e4b1fa4d0254ab79e`.
- Only shader: `assets/minecraft/shaders/core/lightmap.fsh`, 216 bytes.
- Fragment SHA-256: `cfeeb9abd871b1ac5a0e3b84a8f1a47182838880b33e3b6a7a08cbf95048a86a`.
- Metadata: Minecraft resource format 97, permitted range 97–98; target engine
  uses 97.1 for Minecraft 26.3.
- Author: PrecisionZero; All Rights Reserved. Personal modification is allowed
  by the supplied licence; redistribution requires written author permission.
- The uploaded fragment writes constant white. This is a fullbright resource
  pack, distinct from the unrelated Iris Photon shader product.

## Implemented behavior

An exact second allowlisted fragment fingerprint selects the existing native
white lightmap. Unknown fragments keep normal lighting. Fullbright UB 7.0,
the separate native Fullbright switch, effective overlay priority and normal
lighting generation remain in place. No third-party GLSL is copied or executed.
The new matcher does not install packs or write profile/world data.

## Automated evidence

Local CPU probe: **4 passed, 0 failed, 0 skipped**. The three production tests
check both reviewed fingerprints and 64 one-byte-mutated digests; missing,
unknown and oversized files; all 256 white lightmap texels under darkness and
night vision, and restoration of normal lighting. The private-input case reads
the verified actual uploaded fragment and checks recognition, white output,
unrelated replacement, reselection, removal and the independent native switch.
The actual production lightmap code and engine `Sky` type are compiled with
Rust 1.95.0 and registry dependencies from the engine lock.

This probe operates on a prepared **effective resource file**. It does not
exercise resource-pack UI, real GPU textures, a loaded world or save/relaunch.
The exact private archive remains local, outside tracked source/artifacts.
Machine-readable local evidence: [PHOTON-LOCAL-CPU.json](PHOTON-LOCAL-CPU.json).

The first generic regression attempt encountered the sandbox's socket-bind
restriction in the existing private-server occupied-port test. This is retained
as an environment failure, not attributed to Photon. The permitted full rerun
completed **513 collected: 494 passed, 19 skipped**, with no failures. Platform-
specific/source-only skips remain skips. Windows CI results are pending.

## Candidate and remaining tests

Windows build and delivered-package validation: **PENDING**.
Use no older build as proof of this new resource-pack fingerprint support.
No macOS candidate is requested for this change; macOS builds/acceptance are
**NOT RUN**. All physical Windows and macOS visual/gameplay/preservation tests
are **NOT RUN**. Use the [installation and OFF/ON/OFF checklist](PHOTON.md).

Two explicit private-archive integration tests remain in the full renderer
(Fullbright UB 7.0 and Photon). They are ignored unless deliberately invoked
with their original inputs; automated CI cannot run private copyrighted inputs.
CPU-only and CI results must not be treated as physical gameplay acceptance.
