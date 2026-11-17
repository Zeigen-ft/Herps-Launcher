# Explored Terrain LOD — unknown-edge wall correction

Status: implementation staged; native verification and corrected Windows
candidate **PENDING**. Physical visual acceptance **OPEN / user-reported failure**.

After Windows candidate 44102123363 was delivered, the user supplied two
screenshots and reported poor results: abrupt terrain cutoffs and tall blue
boundary faces. Exact candidate/toggle settings and frame-rate results were
not reconfirmed. Do not infer a successful graphics test from prior CI.

Source review found a reproducible mesh defect consistent with the screenshots:
received heightmaps reconstruct solid spans from MIN_Y and water from the
seabed. The voxel mesher interprets empty/unknown neighboring samples as air,
exposing those artificial full-depth sides and the synthetic bottom cap.
The old near/full-detail seal can also extend to MIN_Y.

The correction adds an observed-only meshing policy. It omits bottom caps and
sides facing empty/unknown samples, keeps real height differences between known
neighbors, and bounds the opaque near-boundary skirt to one local step
(1–16 blocks). The legacy voxel/generated LOD policy remains separate.
No cache format, world data, server behavior or support boundary changes.
Existing rendering caches need not be deleted for this mesh-only correction.

Six new native regressions cover unknown land edges (including negative tiles
and multiple levels), ocean curtains, empty tile halos, known cliffs and
cross-tile steps, finite near seals/top exclusions, and shared water faces.
These are CPU mesh tests, not simulated gameplay acceptance.

Unseen terrain still remains absent. Coarse cells whose required footprint is
not cached can remain missing, so rectangular coverage cutoffs are still a
Stage 1 limitation. This fix must not fill gaps by guessing terrain or add
server requests. Sparse-coverage improvement, complete visual transitions and
performance require separate verification.

Before accepting a corrected candidate, repeat on a disposable profile/world:

1. Keep older LOD Distance Off; turn Explored Terrain LOD On, near 4–8, radius64.
2. Explore a coast, move away, and inspect cached land/water boundaries from above.
3. Confirm tall ground/water curtains are absent; known cliffs still show.
4. Cross the near/far boundary slowly; report holes, seams or flicker separately.
5. Close/reopen the same world and check inventory/world preservation.
6. Report candidate/run, settings, Windows/GPU and any performance regression.

Do not claim the screenshots' causes are fully resolved until a physical retest
passes. macOS rendering/gameplay and untested edge cases remain NOT RUN.
