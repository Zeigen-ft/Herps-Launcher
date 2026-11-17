# Explored Terrain LOD — unknown-edge wall correction

Status: native correction checks **PASS**; corrected Windows candidate
[44171833781](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44171833781)
passed packaging/lifecycle checks and independent download auditing.
Physical visual acceptance stays **OPEN**; corrected-candidate retest **NOT RUN**.
[Download and exact hashes](DISTANT-TERRAIN-EDGE-WINDOWS-CANDIDATE.md).

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

1. Keep older LOD Distance Off; turn Explored Terrain LOD On, near 4–8, radius 64.
2. Explore a coast, move away, and inspect cached land/water boundaries from above.
3. Confirm tall ground/water curtains are absent; known cliffs still show.
4. Cross the near/far boundary slowly; report holes, seams or flicker separately.
5. Close/reopen the same world and check inventory/world preservation.
6. Report candidate/run, settings, Windows/GPU and any performance regression.

Do not claim the screenshots' causes are fully resolved until a physical retest
passes. macOS rendering/gameplay and untested edge cases remain NOT RUN.

## Verified native evidence

[Native Windows run 44170889270](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44170889270)
passed at `a95e004746abe0ebdbe404a0becb1fa3e803a7b0`: **56** LOD/cache/mesh/
fade tests, **9** graphics-config and **14** graphics-UI tests, and the complete
native client integration type check. One resource-dependent native case remains
ignored. All six new edge cases passed. The legacy-path regression explicitly
retains its old faces while the observed path omits artificial curtains.

[Tooling regression run 44170889304](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44170889304)
passed both jobs: Windows 419 passed / 105 skipped; Linux 406 passed / 118 skipped
(524 total each). Local exact patch/source guards passed 4 cases and the patch
preparer suite passed 25. The unrelated shader workflow remained skipped by its
existing repository guard. Local standalone Rust formatting was not available;
actual Rust compilation/tests above passed on Windows.

The [independently audited native log/JSON artifact](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/44170889270/artifacts/14367602882)
is 4,389 bytes; SHA-256
`2209b1ae811cd1ee86ae2985b1ebee7ce948f9e3299bdfdd2f1919be7a2ce52b`.
It contains logs, not an installer. The [native CI receipt](DISTANT-TERRAIN-EDGE-CI.json)
records the exact overlay and counts. Candidate build/install tests and physical
visual/gameplay acceptance are separate.

## Corrected candidate verification

Run 44171833781 finished successfully at the same code commit. Its source/tooling
suite passed **509** cases with **15** skips (524 total); delivered Windows
workflow fixtures passed **98** cases without Rust/Cargo/rustup on PATH.
Installation/start/reinstall/uninstall, existing-data sentinels, native rebuild/
selection/rollback and the bundled helper passed. The complete downloaded ZIP
and both inner packages passed SHA-256/size/CRC auditing. All 41 shipped source
postimages match the verified manifest. See the linked candidate receipt for
filenames, hashes, artifact expiry and exact fixture limits.

The workspace executor briefly disconnected during CI and recovered; the CI
job continued. Audit helpers and pending work were retained. No extra source
changes or CI retries were needed. This transport interruption is not a game
failure or a physical test result. No CI failures occurred for the correction.
