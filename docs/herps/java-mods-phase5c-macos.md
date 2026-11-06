# Phase 5C: native macOS verification

Date: 2026-11-04, Asia/Singapore. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`. Approved baseline:
`c237d3b3bf5af6ff8a49c849ec38cc90de2dac41`.

**Phase 5C is not fully accepted: native interactive Mac testing is unavailable.**
Automated native CI, offscreen frozen GUI tests and human interactive acceptance
are separate evidence levels. This report does not claim gameplay, quarantine,
Gatekeeper approval or real keyboard/mouse/display acceptance.

## Scope and implementation

The user approved macOS ARM64 and Intel implementation, testing, debugging,
architecture-specific CI dispatch and feature-only commits/pushes. No merge,
tag, release, existing release alteration or Windows improvement is authorized.
No applicable root or checkout AGENTS.md was present at the initial review.
Phase 5A and Phase 5B remain the baseline; their historical results are not
relabelled as macOS verification.

Implementation commit: `7221599373831f8d98d563ee2c960a54bf4609c8`.

- `tools/verify_herps_dmg.py` requires a matching native macOS architecture,
  hashes and verifies the DMG, mounts it read-only, copies both app bundles to
  a path containing spaces, detaches the image and verifies nested signatures
  plus launcher architecture. It launches the delivered copy, not the build
  folder. Errors retain command output and a failed JSON receipt.
- The delivered launcher must open seven pages, discover the matching game,
  and execute the bundled metadata helper with conservative fixture outcomes.
- `packaging/phase5c_acceptance.py` is an opt-in frozen test harness. macOS
  packages include four existing owned-fixture test modules and their fixture
  generators. Production Java Mods/Modpacks services and UI are unchanged.
  Windows PyInstaller inputs retain their existing behavior.
- The frozen suite exercises actual Qt controls/workers and real bundled
  backend operations. File dialogs/confirmation dialogs are automated; some
  deliberate error tests mock subprocess failure. These are automated tests,
  not human interaction or an exhaustive security audit.
- Delivered invocations run with an empty PATH directory and disposable HOME;
  Cargo, rustc and rustup must not be discoverable. The CI builder still has
  developer tools installed. This tests unavailable runtime tool discovery,
  not physical removal of every developer tool from the runner disk.
- Persistent profile/settings/save reload is checked. Existing suite cases
  preserve saves, original inputs, other-profile state and edited files during
  operations. The verifier hashes the persistent support tree before/after
  deleting both copied apps and requires identical data, including a save.
- The existing workflow's two explicit macOS selections each run this verifier
  after DMG creation, retaining evidence even when a preceding step fails.
  No Windows acceptance steps were changed.

## Automated acceptance coverage

The frozen suite loads `test_javamods_ui.py`, `test_modpacks_ui.py`,
`test_javamods_library.py` and `test_modpacks_service.py`. It fails on errors,
failures, skips or fewer than 50 collected cases. The current suite has 62 cases.

Coverage includes Fabric/Forge/NeoForge import; conservative false-positive
Works handling; local dependencies and hashes; responsive workers and busy
profile guards; saved-report tampering; JSON/text export; disabled initial
single-mod data installation; enable/disable and remove-to-backup; duplicate
and changed-file refusal; profile isolation; Modrinth/CurseForge/Prism-style
instances; missing/conflicting hashes; SHA-512 declarations; partial carry;
retained unsupported rows; and disabled unsupported actions.

| Frozen module | Cases |
| --- | ---: |
| Java Mods Qt UI | 15 |
| Modpacks Qt UI | 11 |
| Java mod library/preservation | 14 |
| Modpack service | 22 |
| Total | 62 |

The preexisting seven-page smoke covers Home, Mods, Java Mods, Modpacks,
Shaders, Multiplayer and Settings. Owned Fabric metadata fixtures require
`Requires porting` for supported data and `Unsupported` for a missing dependency,
even when the raw backend reports `works`. `test_execution` remains null.
No imported Java code is executed.

## Local validation and failures

Local host is Linux, not a Mac. Evidence is retained under
`/workspace/work/phase5c/phase5c-evidence/` and
`/workspace/work/phase5c/phase5c-*.log` in this session.
These scratch files are not package payloads or committed source.

| Check | Result | Boundary |
| --- | --- | --- |
| Full source Python suite, socket-enabled rerun | 338 discovered; 324 passed; 14 skipped; 0 failures | Linux regression evidence only |
| Focused Herps tests | 48 discovered; 46 passed; 2 skipped | Backend env absent in this focused invocation; full rerun supplies backend |
| Actual Linux PyInstaller frozen probe | 62 passed; 0 errors/failures/skips | Bundled real Linux helper, empty PATH; no native Mac inference |
| Frozen persistent reload | Passed | Profile/settings/save sentinel, disposable support directory |
| Python compilation and whitespace checks | Passed before implementation commit | Source checks |

Full-suite Linux skips: 12 PowerShell-dependent Windows stack-repair tests,
one macOS AppleScript compilation test and one supplied-APK integration test.
No Java Mods/Modpacks cases skipped with the real helper enabled.

Failures encountered and resolved:

1. The original packaging regression forbade every `--add-data` argument.
   Two macOS subcases failed after adding acceptance fixture source data.
   The updated assertion keeps helpers as binaries, permits exactly four
   macOS fixture modules and retains no data additions on Windows.
2. The new corrupt-DMG test initially counted an incidental platform-version
   subprocess as a DMG command. Its assertion now counts actual hdiutil calls.
3. The first full local run failed the existing native occupied-port test:
   sandbox socket bind returned EPERM. The socket-enabled full rerun passed;
   no Windows production code or assertions were weakened.

4. Initial native ARM64 delivered verification failed because the new verifier
   placed the app path after `lipo -verify_arch arm64`; lipo interpreted the
   path as an architecture name. The inspected receipt confirms DMG verification,
   read-only mount/copy/detach and both deep/strict signature checks passed first.
   Correction `a206a874094f109b3800de85bc33e3827f83a6ce` places the input before
   the flag and retains native architecture verification. Failed command stderr
   is now included in the CI error, not only in the JSON receipt. Both DMG guard
   regression tests passed before the feature-only correction push.

Reproduction (developer Linux environment only):

```sh
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen .local/herps-venv/bin/python \
  -m unittest discover -s tests -v
```


## Native runs and package evidence

Initial runs at `7221599`:

- [Apple Silicon run 41843833064](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41843833064),
  `macos-15`, ARM64, job `126622077292`.
- [Intel run 41843839413](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41843839413),
  `macos-15-intel`, x86_64, job `126622097487`.

Corrected runs at `a206a874094f109b3800de85bc33e3827f83a6ce`:

- [Apple Silicon run 41847857116](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41847857116).
- [Intel run 41847862931](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41847862931).

Initial ARM64 source suite: 338 discovered, 336 passed, 2 skipped, 0 failures.
Skipped: supplied APK absent and case-colliding files not constructible on the
runner filesystem. The initial delivered check failed at lipo before launching
the copied app. Its evidence artifact `13332190966` was downloaded via the
GitHub connector and inspected after the CLI blob download returned Forbidden.
The failed-run DMG SHA-256 was
`b9c83c44f9b0e6c0b268bd01551f0617ecb02d4eacd97259efc62f53ab4f5cab`.
Initial Intel likewise discovered 338 source cases (336 passed, the same two
skipped) and failed the same lipo command after package/signature verification.
No versioned package artifacts uploaded after either initial failure.

| Initial failed-run evidence | Artifact ID | Downloaded archive SHA-256 |
| --- | --- | --- |
| ARM64 | 13332190966 | `3f6c1b762688375747b9cf255dc050365c071d62730d426f2af8ac224cc205c5` |
| Intel | 13333480495 | `5ad19716a7cdde2957af6ea6ab941d647ca9e93a61b498843132fca30590774d` |

Both evidence archive hashes were independently recomputed and match GitHub
metadata. The initial Intel DMG receipt records SHA-256
`3eb2b345a5602b1b58ab5f815225dd8b5a2f6b5c776cbcf8f32f87baf3d37fa6`.
Initial DMG hashes are runner-computed receipt evidence; these failed-run DMGs
were not available as uploaded package artifacts.

### Corrected Apple Silicon result

Run `41847857116` completed successfully at `a206a87`. The inspected native
platform is **macOS 15.8.2 ARM64**. Source tests: 338 discovered, 336 passed,
2 skipped (APK absent; filesystem case collision), no failures. Delivered
seven-page smoke and all **62 frozen acceptance cases passed**, with no
errors/failures/skips. Cargo/rustc/rustup discovery returned null. Persistent
profile/settings/save reload passed; `settings.json` and the owned profile's
`level.dat` retained identical hashes after both app bundles were removed.
Both copied app signatures passed deep/strict verification; launcher ARM64
verification and actual bundled-helper execution passed. The bundled helper
receipt SHA-256 is
`ed1693eccf4460c58ce86c15d23067233df1ed564cce084ceca30c068b018911`.

| Corrected ARM64 deliverable | Artifact ID | Independently computed SHA-256 |
| --- | --- | --- |
| Package artifact ZIP | 13335641930 | `fa6ed3fdbaa1ec333a2e2cabd8ede037a82aa068ece144208408adc93fac3d65` |
| Evidence artifact ZIP | 13336286724 | `88439572da51a59c70a5742d3ca8fcb34bf8fb404cf980842b790e6f0513957a` |
| Inner DMG | Within package ZIP | `c123befd775e0853e391da08039def87ae883284be6da7509a09e3683a19bbb4` |

Both downloaded archive hashes match GitHub metadata. The DMG member was read
from the downloaded artifact and hashed independently; it matches the native
receipt. Full CI logs and all JSON receipts were inspected. Artifact downloads
used the GitHub connector's returned file reference through the inherited
proxy after the CLI blob redirect failed. No network policy was changed or
proxy bypass attempted.

### Corrected Intel result

Run `41847862931` completed successfully at `a206a87`, passing build, package, DMG integrity,
delivered-app and artifact-upload steps. The inspected native platform is
**macOS 15.7.9 x86_64**. Source tests: 338 discovered, 336 passed, 2 skipped
(the same APK/case-collision reasons), no failures. The delivered smoke opened
seven pages with matching game architecture and a bundled helper. All **62
frozen acceptance cases passed**, with no errors/failures/skips. Developer Rust
tools were not discoverable. Persistent reload and exact support-file hashes
after removal of both app bundles passed, including the owned save sentinel.
Deep/strict signatures and native launcher architecture checks passed.
Bundled helper receipt SHA-256:
`7b52b8b85bb64807c8ffa7647852a49e35481bb09605d5c23a6331093d6a0d59`.

| Corrected Intel deliverable | Artifact ID | Independently computed SHA-256 |
| --- | --- | --- |
| Package artifact ZIP | 13337388105 | `b2045aa7f70cc80aefd69015e3379d2a44fd0e04cade721e42f75f3441a63663` |
| Evidence artifact ZIP | 13337059518 | `ec55704d351620d3c8bf2e6eb2aefb5289d5d0ce96bf04617b1df0a87244aa0b` |
| Inner DMG | Within package ZIP | `1c00a434f59f2beeb6b138a6ada5cf037fa3e1aa8a3b4035a562287cf0ae3810` |

Both archive hashes match GitHub metadata; the independently hashed DMG member
matches the native receipt. Full source test logs and all JSON receipts were
inspected. These are architecture-specific development artifacts, not a release;
GitHub reports expiry on 2027-02-02. Windows-only workflow stages were correctly
skipped on both macOS targets. No Windows dispatch was performed in Phase 5C.

Both initial runs dispatched at implementation commit `7221599`, independently, using
`platform=macos-arm64` and `platform=macos-x64`, never `platform=all`.
Configured Python is 3.12 and Rust is 1.95.0; pinned engine revision is
`7301f6fdd7f470b11317276e7a11b4dc615c137a`. Build caches remain outside
checksum-prepared engine source. Native job status alone must not replace
per-case logs, inspected receipts or independently verified download hashes.

Native reproduction uses the existing workflow, on the feature branch only:

```sh
gh workflow run herps-launcher.yml --repo Zeigen-ft/Herspers-Minecraft \
  --ref feature/herps-java-compatibility -f platform=macos-arm64
gh workflow run herps-launcher.yml --repo Zeigen-ft/Herspers-Minecraft \
  --ref feature/herps-java-compatibility -f platform=macos-x64
```

On each matching runner the delivered verification command is:

```sh
python tools/verify_herps_dmg.py --dmg /path/to/package.dmg \
  --arch arm64 --output /path/to/evidence
# Use --arch x86_64 on the native Intel runner.
```

The verifier leaves `delivered-dmg.json`, `delivered-smoke.json` and
`frozen-acceptance.json`. The first contains actual command outputs, package
hash, nested receipt data and persistent-file hashes. Per-test IDs, skips and
failure traces are in the frozen receipt. GitHub's evidence artifact also
retains source tests/build/package logs and pre/post-packaging helper hashes.
Build and bundled helper hashes may differ after signing; each is identified
at its own stage. GitHub artifact ZIP hashes and inner DMG hashes are distinct.

## Interactive acceptance remains open

A tester on each native architecture must use the exact hashed DMG and record:

1. Mac model, CPU, macOS version, package hash and actual signature status.
2. Download/quarantine and Gatekeeper behavior without silently stripping
   quarantine or claiming notarization. No signing credentials were requested.
3. Normal desktop launch and seven-page visibility, rendering, keyboard/mouse
   navigation, file dialogs and background progress/error/cancel behavior.
4. Supported Java Mods/Modpacks import, dependency selection, analysis, exports
   and backup flows with owned fixtures, including unsupported results.
5. Clean and existing profiles/settings/saves across restart, app replacement
   and app removal, on an end-user machine without Rust/Cargo requirements.

The workflow builds the pinned port-pack executable but does not explicitly
run its separate 99-test Rust library suite or the standalone host's 17-test
suite. Source Python wrappers run their existing native-unit targets; the
source suite pass is not a claim that every Rust workspace target was tested.
Node action-runtime deprecation warnings are retained in the CI logs and did
not constitute test failures. No unrelated action-version updates were made.

No suitable interactive Mac is attached to this session. Offscreen CI is not
accepted as a substitute. Installation into system `/Applications`, OS-specific
permissions, quarantine/translocation, minimum macOS 11 compatibility and real
hardware/display behavior remain unverified unless separately evidenced.

Java runtime execution, Java bridges, universal conversion, packwiz, Java
Build/Test and Modpack Play remain unavailable. Gameplay, GPU rendering and
live multiplayer are outside this phase. Legitimate game resource preparation
is separate; no proprietary resources, third-party mod JARs, credentials or
local ports were committed. No Developer ID/notarization claim is made.

## Handoff and stop point

Automated ARM64/Intel native verification is separate from the still-open
interactive checklist above. **Phase 5C remains incomplete for full acceptance.**
The report and guide reconciliation are documentation-only changes after the
native-tested implementation `a206a87`; the delivered executable code is
unchanged by that handoff commit. Changes are committed/pushed only to
`feature/herps-java-compatibility`. No merge, tag, GitHub Release, existing
release alteration, signing credential use or unsupported feature implementation
was performed. The historical Phase 5A/5B reports are unchanged.
