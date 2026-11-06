# Phase 5D — Native acceptance and candidate hardening

Updated: 2026-11-06, Asia/Singapore.

## Current addendum — physical Windows chainmail evidence

The user personally tested Chainmail Plate and Boots 0.1.0 from
[Windows run 42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443),
source `8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`, and confirmed Survival **and**
Creative: native-enabled launch, four nuggets → plate, four plates → boots,
equipping boots with **+1 Armor**, and both items retained after completely
closing/restarting Minecraft and Herspers Launcher and reopening the same world.
These are user-reported physical PASS, distinct from CI. Exact OS build/hardware,
execution date and supporting logs/screenshots were not supplied.

Earlier loading-logo stall and initially empty recipe output remain unresolved;
later successful launches/crafting do not establish causes or fixes. Untested
edge/preservation/installation/recovery cases and **all Mac gameplay remain
NOT RUN**. See [current readiness, release notes, candidates and install instructions](release-candidates-0.1.0.md)
and [the detailed evidence](../targeted-porting/RLCRAFT_CHAINMAIL_VERIFICATION.md).
Neither full RLCraft nor FunCraft compatibility or stable/public release is approved.

The Phase 5D tables and dependency reviews below are **historical evidence at
their stated commits**. The addendum supersedes blanket statements that no
physical Windows gameplay has ever been reported; it does not accept all Phase
5D cases or transfer the report to later candidates/Macs. Original CI receipts
keep gameplay false, and historical security/distribution gates remain open.

Baseline: `4bcb4564abae7cbeb12f8f1645dd58ae858c5339` on
`feature/herps-java-compatibility`. This is an internal verification milestone,
not approval for a stable public release. Interactive acceptance and actual
Minecraft gameplay are not established by automated tests.

## Historical Phase 5D assessment summary

| Target | Automated result | Native interactive / gameplay |
| --- | --- | --- |
| Windows x64 | Passed; installed lifecycle and 62 frozen cases; hashes inspected | NOT RUN on Windows 11; CI host was Server 2025 |
| Mac Intel, macOS 15.7.9 | Passed; delivered DMG and 62 frozen cases; hashes inspected | NOT RUN |
| Mac ARM64, macOS 15 | Two attempts could not acquire a hosted runner; no new execution | NOT RUN |
| Mac ARM64, macOS 26.6.2 | Passed experimentally; delivered DMG and 62 frozen cases; hashes inspected | NOT RUN; does not replace macOS 15 acceptance |

The implementation is ready for further native acceptance work. It is not
approved for stable publication. Candidate artifacts are internal CI evidence.

## Implemented hardening

- Candidate [support matrix](../HERPS-SUPPORT.md): Windows 11 x64 and macOS 15
  ARM64/Intel are primary candidates, not yet stable-certified. Windows 10 and
  macOS 12–14 are experimental; macOS 11 is not a launcher support claim.
- [Native manual acceptance protocol](native-acceptance.md): installation,
  quarantine/SmartScreen, actual desktop input, resource preparation, PLAY,
  world save/load/relaunch, profile preservation, recovery and evidence fields.
- Windows packages now include the existing 62-case frozen Java Mods/Modpacks
  suite. The old Phase 5C entry point remains supported; --native-acceptance is
  available on all targets. Test output goes to a real file because Windows
  windowed executables have no sys.stderr.
- A native Windows verifier installs into a disposable path with spaces,
  checks shortcuts and seven-page/bundled-helper smoke, runs installed workflows
  with Rust tools absent from PATH, and checks existing data through same-version
  replacement, uninstall and reinstall. Default/named saves, profile registration,
  an unknown preference, shader/mod-data sentinels and newly persisted settings
  are checked. This is not historical-version migration or physical-user testing.
- Only three explicitly named Windows symlink-fixture cases may skip if symlink
  construction is unavailable. Their IDs/reasons remain in the receipt; all
  other frozen skips fail acceptance. macOS still permits no frozen skips.
- The Windows installer rejects destinations whose payload paths exceed its
  legacy Windows path budget before copying; native rejection/lifecycle results
  are reported separately below. It does not promise arbitrary-length paths.
- CI path filters now include both delivered verifiers, the acceptance harness
  and release-evidence generator. Feature runs remain explicit workflow dispatches.
- Notarization evidence now lives beside the final DMG and binds its final hash.
  Submission, stapling and staple validation must succeed before true is recorded.
  Embedded package metadata records not-requested or points to the sidecar;
  it no longer falsely asserts false after a successful optional notarization.
  No signing credentials, services or real notarization were used in this phase.
- Packaging includes pinned Python dependency/version/license inventory and
  discovered notices. PySide6/shiboken wheel manifests exposed no license texts;
  LGPLv3/GPLv3 and the explicit Qt/PySide notice are now included.
- Offline guide links were reviewed: package root guides now point into a bundled
  documentation tree, with corresponding license files, rather than referring
  to absent relative documents.
- Per-platform resolved Python dependency snapshots include active transitive
  build tools; Qt name-normalization is regression-tested so explicit notices
  remain present for PySide6_Essentials as well as its hyphenated spelling.
- Internal candidate evidence records exact source commit, requirements/upstream
  lock hashes, file sizes and SHA256SUMS. No release or public installer promotion
  is performed. Recipe replayability and traceability are established separately
  from bit-for-bit reproducibility, which is not claimed.

## Local verification

Linux source suite at initial hardening commit: **342 discovered, 328 passed,
14 skipped, no failures** on the socket-enabled rerun. Skips: 12 PowerShell
Windows stack-repair tests, one macOS AppleScript test and one supplied-APK test.
The restricted first run failed the existing occupied-port native unit because
socket binding returned EPERM; no production Windows code/assertion was changed
for that environmental failure. The network/socket-enabled rerun passed.

Actual Linux PyInstaller probe: **62 frozen cases, zero failures/errors/skips**,
no Cargo/rustc/rustup on PATH, profile/settings/save reload passed. These results
validate the cross-platform harness, not native Windows/Mac acceptance.

The actual pinned horizon-prepare Rust library suite also passed **49 tests,
zero failures and zero ignored** on Linux, using owned fixtures and --locked
--offline. This validates resource-validation/preparation library logic, not
preparation of the user's official game resources or real world loading.

After offline-documentation changes, the five focused release-evidence tests
passed. These exercise failed notarization receipts, successful-path ordering
with a mocked signing boundary, candidate hash/claim guards, offline-document
inclusion, and rejection of non-Windows installation. Mocked notarization
success is not evidence of Apple notarization. Syntax/whitespace and new
relative documentation links passed inspection.

## Dependency, security and licensing review

An isolated pip-audit scan of all seven exact requirements reported **no known
vulnerabilities** at scan time: PySide6-Essentials 6.8.3, shiboken6 6.8.3,
PyInstaller 6.12.0, altgraph 0.17.5, packaging 26.3,
pyinstaller-hooks-contrib 2026.9 and setuptools 84.2.1. It used --no-deps and
--disable-pip against the explicit pinned list; no dependency upgrade occurred.
It warned that fully hashed requirements are preferable. Results cover these
Python distribution records, not every embedded Qt or Rust/native component.

RustSec review used cargo-audit 0.22.2 with database commit
`965bf9ad083b58e6340d65829d85217b18be9290` (1,403 advisories). It exited 1
because the workspace lock matched four zip 2.4.2 advisories:
RUSTSEC-2026-0367, -0368, -0369 and -0429 (unsafe extraction/permissions,
symlink traversal and extraction denial of service). Raw upstream and prepared
Cargo.lock bytes were verified identical. A conservative lock-graph closure
from horizon-client, horizon-prepare and horizon-port-pack did NOT include
zip 2.4.2; its consumer is horizon-android, outside these packages. Desktop
roots use zip 9.1.3, outside the advisory affected range. No broad dependency
upgrade or engine-pin change was made or required by that raw finding.

Warnings needing disposition: ttf-parser 0.25.1 unmaintained
(RUSTSEC-2026-0192), Tokio 1.53.2 AsyncFd I/O safety (RUSTSEC-2026-0386),
and yanked clipboard-win 5.4.1. The lock closure deliberately overapproximates
optional/platform edges; it does not prove affected Tokio APIs are reachable
in a desktop build. Initial offline target-tree resolution was blocked by an
uncached addr2line crate; no lockfile was changed to suppress it. The checked
archive extraction calls in the standalone server also use the fixed zip line.
Target-specific cargo tree resolution then succeeded for Windows MSVC,
Mac ARM64 and Mac Intel, selecting horizon-client, horizon-prepare and
horizon-port-pack with horizon-client/mods and normal/build edges. Tokio 1.53.2
was absent on all three (cargo reported nothing to print). Thus the Tokio
warning is not demonstrated in the intended desktop build graph. The font
parser maintenance and Windows clipboard yanked-version warnings still need
risk disposition. Optional bundled engine source retains workspace entries;
this exclusion applies to the selected desktop binaries. No advisory waiver
was silently added to configuration. These results do not replace an exact
native linked-component review.

The review confirmed passive Java inspection, bounded archive/path handling,
conservative evidence/status checks, profile guards, backup removal and trusted
native-code warnings. Native builds remain full-permission execution, not a
sandbox. Receipt hashes are integrity checks, not publisher authentication.
See the [bounded security/distribution review](release-security.md).

Remaining distribution gates: native/transitive vulnerability inventory,
complete Qt third-party notices and corresponding-source/library-replacement
review, publisher trust policy, Gatekeeper/SmartScreen behavior and approved
secure distribution. License text inclusion alone is not a legal certification.

## Native candidate runs

Initial implementation: `594440c83b02e89b06b081b16a24681d1c769096`.
[Three-platform run 41860230975](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41860230975)
was dispatched explicitly with platform=all. Its Windows source suite passed
342 discovered cases (329 passed, 13 skipped). Skips were three owned POSIX process fixtures,
eight Mac shell/dialog cases, one missing APK and one filesystem case-collision
fixture. Package/installer creation succeeded; installer lifecycle failed at
its first setup invocation with exit 5, before frozen workflows ran. No installer
log had been collected, so a specific root cause is not claimed. The inspected
failure evidence archive `13340321311` has SHA-256
`5452b8d6d538b44bf3efdef1dcd09e6c56e4e1e4ee739ad1fdbe77ee6354db7b`.
Mac jobs were still queued when this diagnostic run was superseded.

Correction `57d751789bd5e2e1eb7b8380cd14448a89cbfccb` adds persistent installer logs
and the Start-Process invocation used successfully in Phase 5B, bundles offline
docs, extends filters for delivered inputs, and strengthens preexisting named
profile/preferences checks. Five focused release tests and the 53-case Herps
subset passed locally (two real-backend smoke skips in that subset invocation).
[Corrected three-platform run 41862145912](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41862145912)
was dispatched at that exact commit. Polling initially continued to show queued
jobs. Later direct job and artifact responses showed the Windows job had failed
at installation again and both Mac jobs had been cancelled without execution.
The final assessment uses inspected receipts, not the earlier queue view.

The corrected installer log establishes the actual failure: the test's long
Windows TEMP destination exceeded the legacy file/directory path limits for a
nested `preparation/tools/fixtures/.../has_structure/igloo.json`. Inno Setup
suppressed the Abort/Retry/Ignore dialog, aborted with exit 5 and rolled back.
The Start-Process change alone did not fix that condition. Corrected-run evidence
artifact `13339609817` has SHA-256
`0c7a1a22a79f6b3baf258ea1a21250b4044ad3362bef6576f45ca44e95e7382d`.

Commit `1066092d15a8287cb3855a344650e93996acb433` adds payload-derived UTF-16
file/directory budgets to the installer compiler and a PrepareToInstall guard.
Unsupported destinations are rejected with a shorter-folder instruction BEFORE
file copying. It does not enable unrestricted Windows long paths or change
system registry policy. The verifier requires rejection of an overlong path
without changing seeded data, then executes the successful lifecycle in a short
RUNNER_TEMP path that still contains spaces. Local final suite: **345 discovered,
331 passed, 14 platform/input skips, zero failures**. Focused final subset:
55 discovered, 53 passed, two backend-env skips. UTF-16/non-BMP path budgeting
and Qt notice name-normalization have regression coverage.

Independent runs at that same final implementation commit:

- [Windows 41868081178](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41868081178).
- [Mac ARM64 41868087286](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41868087286).
- [Mac Intel 41868094624](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41868094624).

Native results and internal candidate hashes are recorded below only after
inspection. Earlier failed/cancelled attempts are not release acceptance.
ARM64's first independent attempt was cancelled before any steps ran. Its
check-run annotation states: "The job was not acquired by Runner of type hosted
even after multiple attempts", with macOS ARM64 capacity notices. A same-commit
retry was requested on the existing runner type. This is infrastructure evidence,
not a compiler/application failure, and no paid runner or billing change was made.

## Inspected successful candidate results

### Windows x64

Run 41868081178 completed successfully on **Windows Server 2025 x64, build
26100**. This is native Windows CI evidence, not physical Windows 11 acceptance.
345 source cases: 332 passed, 13 explicitly recorded platform/input skips.
The installed frozen suite executed all **62 cases with zero failures/skips**.
Seven-page navigation, actual bundled helper execution, no developer tools on
PATH, profile/settings reload and all preservation checks passed.

The negative installation log contains the path-budget rejection and **no file
copy entries**. Valid installation, same-version replacement, uninstall,
reinstall and final uninstall passed. Both default/named save sentinels, shader
and mod-data files survived; profile registration and the unknown preference
were retained. Settings selection changes during the workflows were intentional;
full support-file hashes were compared across replacement/uninstall/reinstall.
The final native-mod proof passed compilation/marker/selection/rollback,
preserving the save sentinel, clean binary and source cache. It explicitly
leaves hook_execution_verified and gameplay_verified false.

| Windows deliverable | Artifact ID | Independently verified SHA-256 |
| --- | --- | --- |
| Outer candidate artifact ZIP | 13344443296 | `fde28ecfba49e6fe9dd4fc7d523641bcca685427f6b031a20e4d746008708dcb` |
| Evidence archive | 13344777645 | `7ff19aee916755be41110283107700786a9c9256b5ac39aa2232288f109459e9` |
| Inner Setup EXE | Within candidate | `2c0c92eeefacb5f45dbfbfa963ff16a356019d874d6d35853cda8af3624e5d64` |
| Inner portable ZIP | Within candidate | `96739154688e1e7a23197b44ace2c3559bde27c3be3d4a67aa0b1233869f3e77` |

Both outer hashes match GitHub metadata; inner hashes match candidate.json and
the actual installer execution receipt. The large package download needed a
retry; an early read of its incomplete local transfer failed. Only the completed
transfer was used for the independent hashes above. The resolved Windows
snapshot includes pefile 2023.2.7 and pywin32-ctypes 0.2.3 in addition to the
seven root dependencies. A scan of all nine versions found no known advisories.

### Mac Intel

Run 41868094624 completed successfully on **macOS 15.7.9 x86_64**. Source suite:
345 discovered, 343 passed, two skipped (APK absent; filesystem cannot create
case-colliding fixtures), zero failures. The delivered DMG copy passed all
seven pages, bundled-helper checks and **62 frozen cases with zero skips**.
No Rust tools were discoverable. Persistent reload and app-removal preservation
passed. DMG integrity, native architecture and deep/strict signatures passed.
This does not establish Gatekeeper trust, notarization or interactive acceptance.

| Intel deliverable | Artifact ID | Independently verified SHA-256 |
| --- | --- | --- |
| Outer candidate artifact ZIP | 13347810432 | `3ed738fd26e566e80828780f4d3302c2ac642c510315a6264943f01cb316f8e5` |
| Evidence archive | 13347780503 | `5add35e0980efb73f95d1f6e1fdf0e981ae6ca7dcb43df250aaf10399c987925` |
| Inner DMG | Within candidate | `5f5491966255bb7743a6b5f8ec61b2326e8c448f6b56db8af1d19e78fc42c523` |

Outer hashes match GitHub metadata; the inner DMG matches candidate.json and
the native delivered receipt. The eight-package resolved snapshot includes
macholib 1.16.4; its full scan found no known advisories.

### ARM64 capacity and experimental fallback

Both macOS 15 attempts ended before execution with hosted-capacity failure.
GitHub's documented standard macos-26 ARM64 label is used as an explicit
experimental fallback in run 41930710396 at **81e9905**. No large/xlarge or paid
runner type was selected. Build caches are OS-qualified to avoid mixing SDK
outputs across 15 and 26. macOS 26 evidence cannot substitute for latest-candidate
macOS 15 acceptance. The prior Phase 5C macOS 15 baseline remains historical.

81e9905 adds the optional runner, stricter early-rejection log checks and a CI-only
installer-verifier guard. The strict log validator was also executed against the
actual successful Windows log; it rejects copy-then-rollback as early rejection.
The personal-machine guard has regression coverage. Manual testers use the
protocol, not the destructive disposable installer harness. Launcher application,
installer payload construction and engine code are unchanged from 1066092.
Final local regressions at that hardening step: **347 run, 333 passed, 14 skips,
zero failures**. A machine-readable evidence ledger is in
[phase5d-evidence.json](phase5d-evidence.json).

### Experimental ARM64/macOS 26 result

[Run 41930710396](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41930710396)
completed successfully at 81e9905 on **macOS 26.6.2 ARM64**. Source suite:
347 discovered, 345 passed, two skipped (APK absent; case-colliding filesystem
fixture), zero failures. Seven-page delivered navigation, native bundled helper,
DMG integrity, architecture/signatures, persistent reload and app-removal
preservation all passed. All **62 frozen cases passed without failures/skips**,
with Cargo/rustc/rustup absent from PATH. The eight resolved Python dependencies
match the Intel version set and their fresh audit found no known advisories.

| ARM64/26 deliverable | Artifact ID | Independently verified SHA-256 |
| --- | --- | --- |
| Outer candidate artifact ZIP | 13373530525 | `12456cf9561be2eb7ec4a921e4ec92625b34f62c0d2bc7fd94200c660b8ce84b` |
| Evidence archive | 13372079838 | `4edf56a189681b59b4b2f38651ca3963cdfcf7dc6339b5e8caf6b27f3a97b53a` |
| Inner DMG | Within candidate | `fdbd4593304130e07d42c4f9cf485ce605e95f53c12e3f6fbd8292e741202a4a` |

Outer hashes match GitHub metadata; the DMG matches candidate.json and the
native delivered receipt. Both Mac candidates remain ad hoc development builds,
not Apple-notarized releases. This adds experimental macOS 26 ARM64 evidence;
it does NOT establish latest-candidate execution on macOS 15 ARM64.

### Candidate provenance and replay

Windows/Intel candidates were built from 1066092; the ARM64/26 fallback from
81e9905. Git comparison confirms the launcher application tree and package-builder
source are unchanged between them. 81e9905 changes CI/verifier checks and support
documentation. The core herps_launcher tree is also unchanged from baseline
4bcb456. Each candidate records its own exact source commit, input hashes,
resolved platform dependencies and package checksums. Input hashes cover raw
checkout bytes: the Windows requirements/upstream-lock hashes differ because
of CRLF checkout normalization; their LF-normalized content matches the Macs.
Replay uses that commit
and its recorded runner/target, not a floating branch tip. These are traceable,
rebuildable recipes. Byte-for-byte reproducibility is not established: runner
images, timestamps, signing and temporary package paths can vary.

All successful package archives, evidence archives and executable/DMG members
listed above were downloaded and independently hashed. JSON receipts, installer
logs, source test logs, dependency inventories and native-mod proof were inspected.
The final report/evidence handoff adds documentation only after these builds;
it does not change the tested application or package construction code.
No stable release, merge, tag or existing release modification was performed.

## Gameplay and hardware boundaries

The available executor is Linux. No matching native game installation,
prepared Minecraft 26.3 resources or supplied assets were available. Existing
owned process fixtures exercise resource-check failure, lock release, launch
arguments, child logging/exit and relaunch; they do not run Minecraft.

At the historical Phase 5D commits, **real resource preparation, rendered game startup, world save/load, gameplay,
shader rendering, native hook execution and live two-machine multiplayer remain
unverified.** A Windows 11 x64 manual-test machine is available. A Mac has also been offered,
but its chip and installed OS are not yet confirmed; it is not recorded as
ARM64/Intel acceptance evidence. No manual case has been run
in that earlier session. The current addendum records the later bounded Windows
report. Intel hardware coverage remains unconfirmed.

Physical Windows/Mac testing is required for the manual protocol's
real hardware graphics/input/audio cases. Native CI/offscreen UI and synthetic
save sentinels cannot pass those cases. Ordinary Finder/Start-menu launch,
quarantine, system Applications permissions and real end-user upgrades also
need native interactive evidence.

Java runtime execution, bridges, universal conversion, packwiz, Java Build/Test
and Modpack Play remain unavailable. No unrelated feature work was undertaken.

## Release decision

**NOT READY for stable public release.** Automated candidate hardening is
separate from native manual/gameplay acceptance. Do not merge into main, tag,
publish a release or promote these internal artifacts without separate approval.
The next work, in priority order:

1. Complete the remaining Windows 11 manual acceptance and investigate the
   unresolved logo-stall/initially-empty-output observations. Retain the five
   reported chainmail passes separately. Use the verified installer and
   disposable profiles: actual resource preparation, PLAY, world save/load,
   exit/relaunch, desktop dialogs, failure recovery and real preservation cases.
2. Confirm the offered Mac's chip/OS, test the matching candidate interactively,
   and obtain Intel physical hardware coverage. Run true graphics/input/audio
   cases on actual hardware. Repeat macOS 15 ARM64 CI when capacity permits,
   or explicitly revise the eventual support contract before promotion.
3. Complete exact native/Qt notice/source/replacement review; disposition the
   font-parser maintenance and Windows clipboard yanked-version warnings;
   refresh vulnerability scans before promotion. No broad engine update was made.
4. Validate distribution trust (Gatekeeper/SmartScreen and chosen signing policy)
   with downloaded artifacts. Real credentialed signing/notarization requires
   separate approval; the optional path's unit mocks are not that evidence.
5. Freeze a final acceptance cohort, resolve all data-loss/installation/core-launch
   defects, retain hashes/logs and seek explicit publication approval. Fully hashed
   build-tool inputs and bit-for-bit reproducibility remain additional hardening,
   not claims established by the current resolved-version snapshots.

Java runtime/bridge work, packwiz, universal conversion, automatic updates and
CLI/GUI feature convergence are separate future projects. They need not delay
an accurately scoped launcher release once the actual acceptance gates pass.
**Phase 5D native acceptance remains open.**
