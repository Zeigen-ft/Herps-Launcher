# Java Mods and Modpacks release readiness

Assessment date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`. Implementation assessed: `c04874d`.
Step 4 changes documentation only; application, tests, dependencies, packaging
scripts and CI remain unchanged.

**Source workflows are implemented and tested with owned fixtures on Linux.
A distributable Windows/macOS release is not ready.** The seven-page source UI
passes smoke validation, but packaging still rejects its page count, the
port-pack executable is not bundled, native target verification has not been
performed for these additions, and gameplay compatibility remains unverified.
No push, merge, publication or release was performed.

## Completed features and evidence

| Capability | Source status | Evidence from automated tests | Windows/macOS status |
| --- | --- | --- | --- |
| Fabric/Forge/NeoForge JAR import and passive metadata inspection | Available in source | Three-loader import, structural class metadata and malformed/archive tests | Native execution unverified |
| Conservative compatibility and dependency analysis | Available in source | Real false-positive `works`, unreadable-class, missing/transitive dependency, mixin and version regressions | Native execution unverified |
| Single-mod data carry and disabled-by-default installation | Available in source | Actual Rust carry, folder/manifest/hash receipts and duplicate-ID checks | Native execution/gameplay unverified |
| Enable/disable and remove-to-backup | Available in source | Real engine setting keys, preserved saves/mod data/settings, rollback and edited-file rejection | Native execution unverified |
| Modrinth, CurseForge and Prism/MultiMC GUI imports | Available in source | Real importer, original-manifest reconciliation, local ID/hash resolution and embedded-file fixtures | Native execution unverified |
| Partial data carry with complete coverage | Available in source | Validated-subset/dependency-ensemble tests; missing/unsupported rows retained; no automatic activation | Native execution/gameplay unverified |
| JSON/text export and saved-report revalidation | Available in source | Real raw evidence, changed snapshot/output and forged-status regressions | Native execution unverified |
| Seven-page navigation and worker responsiveness | Available in source | Real Qt controls, profile guards and source-entry smoke | Native packaged execution unverified |

These are implementation and fixture-test claims. Data folder validation does
not establish Java runtime compatibility, original gameplay equivalence,
successful rendering or a fully playable pack. Raw backend `works` remains
visible as evidence and cannot alone become Native compatibility or Tested
successfully. Missing evidence remains Unsupported with explicit reasons and
`insufficient_evidence`.

## Unsupported features

The following remain **Not available yet**, with no release claim:

- Java bytecode execution and required Java loaders/hooks.
- Universal Java mod conversion or translation of arbitrary gameplay code.
- A Java compatibility bridge, including Compatible through Java bridge.
- packwiz import: the pinned Rust backend has no parser.
- Java mod Build Mod and Test Mod actions: the controls remain disabled.
- Modpack Play: the control remains disabled because complete runtime/content
  and gameplay validation is unavailable.

`tools/smoke_herps_native.py` compiles an owned Windows `.hnmod` fixture. It
explicitly leaves hook execution and gameplay unverified and is not a Java
Build/Test backend. It was inspected, not run as a Java compatibility test.

## Fresh Step 4 verification

Host: Linux x86_64, Python 3.12.14, pinned launcher requirements, Rust 1.95.0.
Tests used locally generated original fixtures and the real pinned executable
`/workspace/.horizon-target/debug/horizon-port-pack`. No imported Java mod code,
JVM, oracle or game was executed during analysis.

| Check | Passed | Failed | Skipped/ignored | Scope |
| --- | ---: | ---: | ---: | --- |
| Full repository Python suite | 287 | 0 | 14 skipped | 301 discovered, including actual Qt/backend integration |
| Relevant `horizon-port-pack` Rust library suite | 99 | 0 | 0 ignored | Pinned source, Cargo locked/offline |
| Bedrock launcher Rust suite | 10 | 0 | 0 ignored | Repository-local Cargo target |
| `launcher_windows.rs` Rust unit target | 31 | 0 | 0 ignored | Compiled/executed on Linux; local sockets permitted |
| `herps_host.rs` Rust unit target | 17 | 0 | 0 ignored | Includes shared private-server tests |
| Existing packaging Python subset | 57 | 0 | 0 skipped | Repeats cases already included in the full Python suite |
| Seven-page source smoke | Passed | 0 | None | Actual Qt source entry point; no required game installation |

The shared 17 private-server tests execute through both native Rust unit
targets; do not count them as different platform tests. Port-pack binary and
doctest targets each contain zero tests, separately from its 99 executed library
tests. These Linux native-unit runs are not Windows/macOS application runs.

The 14 Python skips were 12 PowerShell-dependent Windows stack-repair tests,
one macOS AppleScript compilation test and one supplied-APK integration test.
No Java Mods/Modpacks case was skipped with the real executable enabled.

Full Python command, from the checkout root:

```sh
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python \
  -m unittest discover -s tests -v
```

The relevant Rust suites used Rust 1.95.0, locked dependencies and the existing
checksum-prepared engine. The whole unrelated game workspace and oracle/parity
harnesses were not run. No new tests or assertions were introduced/modified in
this documentation step.

Additional checks:

- Source smoke returned `{"status":"passed","pages_opened":7}`.
- Actual launcher `check`, local-instance `analyze-pack`, single-JAR `port`, and
  JSON/text `export-report` examples completed with expected exit 0; analysis
  results were Requires porting, with no test execution or bridge claim.
- All four launcher command help pages parsed successfully. The raw Rust
  tool's exit-1 `--help` usage behavior remains documented, not invented away.
- Documentation local links/anchors, documented command names, named test
  references, feature-status terminology and formatting were checked.
- Python compilation, dependency consistency and whitespace checks passed.

Evidence is retained under `.cache/java-mods-step4/`:
`python-tests.log`, `rust-{port-pack,bedrock,windows,host}.log`,
`packaging-tests.log`, `packaging-source-smoke.json`, `packaging-validation.json`,
`package-help.log`, `package-host-guard.log`, `cli-documentation-checks.json`
and `documentation-consistency.json`. These are local verification artifacts,
not published builds.

## Packaging blockers and proposed changes

### Five-page guards reject the source launcher

Two exact checks still expect five pages:

| File and location | Current condition | Proposed modification only |
| --- | --- | --- |
| `tools/package_herps.py:33`, `smoke()` | `report.get("pages_opened") != 5` | Change expected count to `7`; preserve nonzero-exit and `status != "passed"` rejection. |
| `.github/workflows/herps-launcher.yml:110`, installed Windows smoke | `$report.pages_opened -ne 5` | Change expected count to `7`; retain process/status, installation, shortcuts and uninstall checks. |

`packaging/herps_entry.py` already iterates actual navigation buttons and
records their count; it needs no count edit. Current navigation/source tests
already assert all seven names and pages. A future packaging change should keep
those checks and add installed Java Mods/Modpacks fixture exercises.

This mismatch was reproduced non-destructively: the actual successful
seven-page source report was supplied to `tools.package_herps.smoke` while the
native-process boundary was mocked to return zero. The guard rejected it with:

```text
ValueError: Packaged launcher smoke test failed: no successful smoke report
```

This is **one confirmed packaging-guard incompatibility**, not a failed unit
suite and not a native package execution. `tools/package_herps.py --help` returned
0. Invoking packaging on Linux with a nonexistent input returned the expected
host-guard error, `Game builds require Windows x64 or macOS ARM64/x64`, before
package output. It does not validate a real game package.

No packaging or CI file was modified. No Windows ZIP/installer or macOS DMG
was built, installed, signed or declared ready in Step 4.

### Bundle the real port-pack executable

The current `tools/package_herps.py:43`–`:64` builds and adds `herps-host` only;
optional `--source` copies engine source, not a compiled port-pack executable.
The future native build/package change needs:

| Platform | Rust target | Bundled executable |
| --- | --- | --- |
| Windows x64 | `x86_64-pc-windows-msvc` | `horizon-port-pack.exe` |
| macOS ARM64 | `aarch64-apple-darwin` | `horizon-port-pack` |
| macOS Intel | `x86_64-apple-darwin` | `horizon-port-pack` |

1. On each matching native runner, build package/binary `horizon-port-pack`
   with Rust 1.95.0 and `--locked` from the checksum-prepared source matching
   `upstream.lock.json` commit `7301f6fdd7f470b11317276e7a11b4dc615c137a`.
   Keep Cargo's target directory outside the checksum-prepared source tree;
   otherwise generated files invalidate its fingerprint. Reuse external target
   caches appropriately and verify architecture/runtime dependencies. Do not
   substitute a Linux binary or disable verification.
2. Add the validated executable through the existing PyInstaller
   `--add-binary` mechanism alongside the host helper. A proposed pair is
   `--add-binary`, `f"{port_pack}{os.pathsep}."`, following the current helper's
   argument convention. This is a future script change, not a supported new
   packaging option today.
3. Use the implemented frozen lookup in
   `herps_launcher/javamods/adapter.py:153`: `sys._MEIPASS`/executable-relative
   discovery. Verify the actual Windows onedir and macOS bundle layouts on
   their native hosts; do not guess a fixed Contents path. Keep mutable work
   files in per-profile directories outside signed bundles.
4. Preserve macOS executable permissions and include the helper before final
   signing. Verify signatures of nested code and the finished app. If Developer
   ID/notarization is used, validate and record the real results. Never infer
   notarization from a source smoke or static package metadata.
5. Record the built helper's source revision and checksum in package evidence,
   retain applicable notices/source obligations, and run owned-fixture commands
   through the **bundled** executable in an installed application. Its current
   `--help` exits 1 and has no version protocol; do not use an assumed zero-exit
   version/help probe as the only readiness test.
6. Test missing/wrong-architecture helpers, paths containing spaces, clean and
   existing profiles, permissions and actionable errors. A stale user-configured
   backend path must not be confused with verified bundled discovery.

### Headless pack commands have a narrower scope

The public launcher CLI still constructs the Step 1 `PortPackAdapter`, while
the Modpacks page uses `ModpackLibrary`/`LocalPackAdapter`. Enhanced CurseForge
ID reconciliation, complete original-manifest recovery, embedded-file handling,
partial-subset coordination and original-index SHA-512 checks are service/GUI
features. They must not be advertised as CLI parity.

The guide uses a local Prism/MultiMC instance for CLI pack examples and directs
these enhanced pack workflows to the GUI. Before wider release, either converge
the CLI on the same guarded service or explicitly restrict/support-test its
narrower surface. Step 4 documents this gap and does not change implementation.
CLI `port` keeps run-local output; Java Mods GUI porting additionally installs
a validated single-mod folder disabled. Generic CLI export accepts its profile's
Step 1 `report.json`, not the Modpacks service's wrapper as a new CLI format.

## Native platform verification still required

For Windows x64, macOS ARM64 and macOS Intel separately, retain evidence for:

- Native helper/game/launcher builds, architecture/dependency checks, bundled
  helper discovery and actual helper execution with owned fixtures.
- Seven-page installed UI navigation, responsive workers, errors/timeouts,
  profile switching, dependency resolution and report exports.
- Single-mod disabled installation, explicit enable/disable, backup removal,
  hash/tampering checks and preservation of existing saves/mods/shaders.
- Complete/missing/conflicting-hash pack fixtures, CurseForge instance mappings,
  retained unsupported rows, partial carry and a disabled Play control.
- Windows installer/portable layout, shortcuts, startup/uninstall, runtime
  prerequisites and paths with spaces. macOS app/DMG integrity, executable bits,
  signing/Gatekeeper behavior and notarization only when actually performed.

Historical native run `41571739445` documents an earlier five-page launcher at
source commit `2aee3c77a3c03e91a680f3342267c435a392d737`. Its external results
and artifacts were not rechecked here and do not verify Steps 1–3. The new
feature history is local; no remote availability or publication is implied.

## Gameplay verification still required

Use legitimate prepared game resources and disposable profiles/worlds, not
real player saves. Verify a supported data fixture on the actual engine:
loading, expected data behavior, unsupported-file handling, logs and rollback
must be observed and recorded. Check intended platform renderers separately.
Folder/manifest/hash checks cannot establish template availability or original
Java behavior. A machine's successful game startup is not a modpack equivalence
test. Any future test-status backend needs real execution records and precise
scope before a Tested successfully status can be exposed.

No Minecraft gameplay, Java mod execution, live two-computer multiplayer,
GPU shader rendering or original third-party mod compatibility was tested in
Step 4. These capabilities remain unverified; a Java bridge and universal
conversion remain unavailable regardless of data-fixture outcomes.

## Security and licensing limits

Analysis remains passive: metadata/class-file structure is read, method bodies
are not interpreted, Java code is not decompiled or executed, and no imported
oracle/build script is launched. The port-pack executable itself is trusted
native code running with user permissions. Profile separation and input/path
checks are not an operating-system sandbox or an exhaustive security audit.

Declared hashes detect agreement and later changes, not authenticated publisher
identity. Conservative status/schema/hash guards preserve unknown/contradictory
evidence instead of replacing it with success. Retain source snapshots, output
receipts and reports for revalidation; edited material is preserved/refused.

Record/review each mod's licence. ND/NC/restricted acknowledgements grant no
modification or redistribution rights. Even raw `check` generates local data
carry-over; keep generated ports local. Do not include user JARs, third-party
ports, proprietary game files, prepared resources or credentials in a package
or source commit. Preserve the repository GPLv3 obligations, existing Horizon
notices and applicable Qt/PySide6/dependency distribution terms; review the
actual components being shipped. Authentication and ownership checks are
unchanged. No signing credential or secret was requested or embedded.

## Recommended next milestone

An explicitly approved **packaging and native acceptance** milestone should
first fix both page-count guards, bundle the pinned helper, address the
documented CLI/service scope gap, and run the native fixture/installation matrix
above. Preserve all conservative statuses and disabled unsupported actions.
Follow that with separately scoped gameplay validation of supported data
fixtures. Packwiz, Java runtime/bridge work and mod Build/Test are separate
backend projects, not release-label or documentation changes.

Step 4 ends with local documentation and verification evidence. No production
release is approved by these source results. Stop after the local commit and
await the user's next instruction.
