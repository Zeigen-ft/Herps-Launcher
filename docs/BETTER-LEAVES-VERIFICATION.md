# Better Leaves 9.6 — Herps verification

**Rebuilt; Windows/Linux automated validation and delivery audit PASS,
8 November 2026. Real visual, gameplay and FPS acceptance remains NOT RUN.**
RLCraft-style development is paused; its branch remains at
`fcd5f96637f9e93601ab7c1bd199993737257235`. No further RLCraft stage was started.

## Download and provenance

- Branch: `feature/better-leaves-resource-pack`.
- Source: **`555b71997dc402241aa3136454087dc132dba4fd`**.
- [Successful native asset run 42486330922](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42486330922).
- [Windows download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42486330922/artifacts/13619507718)
  (`Herps-Better-Leaves-9.6-MC26.3-Windows`).
- [Linux download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42486330922/artifacts/13620085468)
  contains the **identical** resource-pack ZIP, not a Linux launcher.
- Actual inner file: `Herps-Better-Leaves-9.6-MC26.3.zip`, **84,532 bytes**.
- SHA-256: `2743be9a74c34051db28ac3ccbdfc7c991fa729f2c7ca6386b1ac97fa48e2400`.
- Current artifact expiry: 6 February 2027. No public GitHub Release was created.

[Installation/undo and physical checklist](BETTER-LEAVES.md) ·
[all hashes](BETTER-LEAVES-SHA256SUMS.txt) ·
[machine-readable evidence, complete skips and corrections](BETTER-LEAVES-VERIFICATION.json).

The supplied original `Better-Leaves-9.6.zip` is 1,977,146 bytes, with 4,717 entries,
SHA-256 `cbeeccd774f910ed270dbe9651d789a8f785d055499f846e466d86f9cae91e90`.
It contains JSON, PNG and metadata/licence/readme data. Archive instructions were
treated as data; no contained script or Java code was executed. Motschen's MIT
copyright/permission notice is retained verbatim. The focused pack preserves all
108 included upstream asset files byte-for-byte and its supplied icon/license.

## What changed

Metadata now targets the pinned Minecraft 26.3 resource format **97.1** rather
than asserting a broad, untested range. Fourteen vanilla leaf blockstates retain
56 numbered world models, 14 canonical leaf item models, ten shared parents and
14 leaf textures. Unsupported Java-mod overrides and unused legacy models are
omitted. No Minecraft mod, new block, collision/drop rule, engine patch or launcher
feature is implemented. The archive has 113 payload files, no code or data pack.

Existing Herps builds with the pinned engine can use its existing in-game
resource-pack menu. No launcher reinstall or developer tools are needed. Pack
installation/selection is manual and profile-local; this work did not install or
enable it in any real user profile. RLCraft mods, worlds and backups are retained.

## Automated evidence

| Cohort | Passed | Skipped | Scope |
| --- | ---: | ---: | --- |
| Final local full suite, pinned helper and Qt | 494 / 513 | 19 | Existing launcher regressions plus new pack tests |
| Portable CI Linux | 395 / 513 | 118 | Helper absent; Qt integration unavailable there |
| Portable CI Windows | 408 / 513 | 105 | Helper absent |
| Focused pack safety/build suite, each OS | 13 / 13 | 0 | ZIP paths/links/limits, source pins, model closure, deterministic build and preserved output |
| Native assets, each OS | 9 / 9 | 0 | Actual pinned model/blockstate/metadata functions and PNG decoder |
| Independent delivery audit | All assertions passed | 0 | Four artifact digests; both packs; all 113 file hashes/CRC/source pins |

[Portable run 42486330791](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42486330791)
passed both jobs. Full IDs/reasons for the portable and local skips are retained
in the JSON. Skips are not passes. Local skips comprise 12 unavailable PowerShell,
5 Windows-junction, one supplied-APK and one AppleScript case; full local testing
supplies real-helper/Qt coverage absent from the portable jobs. No new launcher
binary was built, so earlier installed-app evidence remains scoped to its runs.

Native verification uses engine commit `7301f6fdd7f470b11317276e7a11b4dc615c137a`,
Rust **1.95.0**, and registry versions/checksums within that engine's pinned lock.
It parses 80 model definitions, resolves child texture aliases, parses 14 weighted
blockstates, and bakes 224 rotated world variants into 2,240 quads. Each variant
has six cube faces plus four unculled fringe faces, finite coordinates and valid
UVs. The 14 canonical item models produce 84 quads whose UVs crop the central
16×16 region of the 32×32 textures. It preserves tint indices and decodes all 14
RGBA leaf textures with transparent/opaque pixels through the pinned PNG decoder.

Resource-format checks compile unmodified production parsing helpers extracted
from `packs.rs`, with the actual native version constants. An independently
authored empty parent substitutes for the vanilla base in the CPU fixture;
actual base resources and display transforms are not tested. This does **not** execute
the game, GPU, in-game selection/reload, actual item rendering, a real world or
performance testing. All corresponding false flags remain false.

Both downloadable packs match each other and the local rebuild from the exact
original upload. Every ZIP payload hash matches the build manifest and curated
upstream source pins; ZIP CRCs and MIT attribution match. Native Windows/Linux
report source is `555b719`; later guide/report commits do not change these bytes.

## Corrections and limitations

1. Local development initially checked parent texture aliases before applying
   child bindings; the validator was corrected. An initial metadata-helper probe
   also included a UI wrapper without its UI dependencies; extraction was limited
   to the unmodified pure production format helpers. Neither required asset or
   engine edits. These development observations are retained in the JSON.
2. First native run `42485250468` and portable run `42485250378` at `9eb3462`
   failed on the Windows malicious-backslash ZIP test. Windows normalized the
   fixture name before it reached validation. Commit `9dc7997` preserves raw
   fixture names and rejects original/normalized filename differences, including
   NUL truncation. The assertions were strengthened. Linux native checks passed;
   Windows native validation was NOT RUN in that first run. Corrected runs
   `42485658480`/`42485658486` passed both platforms.
3. Final dependency inspection then identified the separate item-model roots.
   Commit `555b719` retains the supplied canonical models and adds native cropped-UV
   checks. The earlier world-only pack (`ac2d2160…`) is superseded by the final
   `2743be9a…` pack. All final checks were rerun on both platforms.

Expected duplicate-name warnings in intentionally malicious ZIP fixtures and
GitHub Actions runtime deprecation warnings do not represent visual verification
or pack failures. No performance improvement is claimed from the author's Lite
description; additional geometry can cost FPS. Leaf-replacing visual packs can
conflict and need separate testing. Declared assets do not add missing blocks or
provide Java mod compatibility.

**NOT RUN:** physical Windows 11, macOS Intel or Apple Silicon appearance, actual
pack selection/reload, transparency/shadows/held-item display, world save/reload
with the pack, GPU/driver/FPS behavior and other-pack combinations. These require
the user's legitimate prepared resources and native interactive evidence.

Main remains `b292a48c279c2b718a5395fe5558f2ff83dcea30`; the paused RLCraft branch
remains `fcd5f96637f9e93601ab7c1bd199993737257235`. No main merge, tag, public
release or existing-release change occurred. No real profile or save was changed.
