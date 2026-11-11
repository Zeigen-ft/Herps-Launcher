# Photon fullbright verification

Tested code/candidate commit: **`4d6831152512aeb9e26f9b6993415bdbcd479719`**.
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
specific/source-only skips remain skips.

## Windows candidate — verified download

Successful run **[43062810811](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43062810811)**,
artifact **[Herps-Launcher-0.1.0-Windows-x86_64](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43062810811/artifacts/13879871388)**.
Sign in to GitHub with repository access if required. The download expires
**9 February 2027** according to the current artifact metadata.

| File | Bytes | Independently verified SHA-256 |
| --- | ---: | --- |
| Outer GitHub artifact ZIP | 238,835,061 | `e876d202d9816d18dff72a145fd09bfbd20aebcd01893df0e8da67a773c92fbf` |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` inside it | 102,694,780 | `fd85ed3ac70b2e87effdad81b5bccc06623d34c7b3bf82f01949a0cd84e97dd1` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-wi2vzqt1.zip` inside it | 138,036,439 | `8302cd38f912980ef29a43456d7153858ba967b6048cd2535f5b6eca3bb77a62` |

[Checksum file](PHOTON-CANDIDATE-SHA256SUMS.txt) ·
[machine-readable CI/audit results](PHOTON-CI.json) ·
[evidence artifact](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43062810811/artifacts/13880266143).
The evidence ZIP is 827,261 bytes, SHA-256
`d8feaab62c2b861086d8cc79ee666e3137d2518d45962dc2ceac1bebf182291c`.

Both artifact ZIPs were downloaded and checked against GitHub's digests and all
outer ZIP entry CRCs. Both actual package hashes also match `candidate.json`
and `SHA256SUMS` inside the artifact. The portable package's engine source has
lightmap SHA-256 `7f05b1a35be3efd82b6830684f2bc61e21dc2cee4eddb96299a3d854719c6f84`,
identical to the locally verified production module. The original Photon ZIP
is not bundled. These are internal, unsigned test packages, not a public release.

### Install the Windows candidate

1. Close the launcher and game, and back up valued worlds. Extract the **outer
   GitHub artifact ZIP once** into a new folder.
2. Open PowerShell there and run:

   ```powershell
   Get-FileHash -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe' -Algorithm SHA256
   ```

   Compare with the installer hash above. Stop if it differs.
3. Run that `Setup.exe` and follow the installer. Keep existing game data;
   no deletion or clean reset is needed. For security warnings and the general
   installation procedure, see [INSTALLATION.md](../INSTALLATION.md).
4. Open the installed Herps Launcher, select a disposable test profile and follow
   the [Photon activation and OFF/ON/OFF checklist](PHOTON.md). Use your own
   original Photon ZIP; it is a separate file from the installer/portable ZIP.

The portable ZIP is an alternative: extract it into a new folder and run
`Herps Launcher/Herps Launcher.exe`. Do not extract over another installation.
Neither route requires Rust/Cargo on the player's PC. Real Windows 11 operation
still needs the physical checks below. The package contains the build-time
version of this report; this branch's current report adds the final audit receipts.

## CI results and skipped coverage

| Check | Result |
| --- | --- |
| Windows candidate source/integration tests with real backend | **498 passed, 15 skipped**, 513 collected |
| Windows standalone production CPU lightmap probe | **3 passed, 0 skipped**; private ZIP absent in CI |
| Windows full-renderer lightmap unit tests | **3 passed, 2 ignored**, 849 other library tests filtered out |
| Existing Chainmail, Flint, Gathering, Woodcutting and Bandage native checks | **PASS**; no RLCraft development resumed |
| Delivered installed workflow/native-content cases | **98 passed, 0 skipped, 0 failures/errors** |
| Install, startup, reinstall, uninstall and profile/preference preservation fixtures | **PASS** |
| Owned native mod compile/select/rollback smoke | **PASS** |
| Portable CI run [43062810196](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43062810196) | Linux **395 passed / 118 skipped**; Windows **408 passed / 105 skipped** |
| Legacy experimental shader run 43062809459 | **SKIPPED**, existing repository-name job guard |
| Manual prerelease-file assembly job | **SKIPPED**; direct Windows candidate artifact verified instead |

All 98 delivered installed cases ran with `cargo`, `rustc` and `rustup` absent
from PATH. Those cases exercise disposable fixtures, launcher navigation,
inspection/content workflows, backups and preservation safeguards; **they are not
real gameplay**. Source/platform skips remain skips, and the broad renderer
library was not run beyond its selected lightmap tests. No GPU/FPS acceptance
is inferred from compilation or white CPU texels.

The first sandboxed engine-preparation attempt could not reach the proxy; an
existing checksum-verified source archive was used successfully. The initial
loopback-bind source-test failure and successful permitted rerun are recorded
above. GitHub CLI artifact transfer failed; connector download references then
succeeded and the actual bytes were verified. These environment/transfer failures
are separate from the successful application tests.

## Remaining physical and private-input tests

No macOS candidate is requested for this change; macOS builds/acceptance are
**NOT RUN**. All physical Windows and macOS visual/gameplay/preservation tests
are **NOT RUN**. Use the [installation and OFF/ON/OFF checklist](PHOTON.md).

Two explicit private-archive integration tests remain in the full renderer
(Fullbright UB 7.0 and Photon). They are ignored unless deliberately invoked
with their original inputs; automated CI cannot run private copyrighted inputs.
CPU-only and CI results must not be treated as physical gameplay acceptance.
