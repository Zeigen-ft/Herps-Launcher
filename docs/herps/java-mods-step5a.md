# Step 5A report: seven-page packaging and bundled metadata backend

Date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`. Base: Step 4 commit `ec2f3b4`.

This phase changes packaging, executable discovery, packaging smoke evidence,
CI configuration and their tests. It adds no Java conversion capability.
**Native Windows/macOS packages have not been built or executed in this phase.**
Phase 5B and Phase 5C remain subject to separate approval. No push, merge,
publication, public tag or release was performed.

The checkout has no root `AGENTS.md` or `CLAUDE.md`; this absence was checked
before changes. The Step 0 audit, Step 1–3 reports and Step 4 release-readiness
report were read. Existing reports are historical evidence and are unchanged.

## Implemented packaging changes

- `tools/package_herps.py` now requires seven pages, a successful launcher
  process and successful smoke status. A stale report is removed before each
  invocation. Seven pages alone cannot satisfy the packaging guard.
- Packaging builds the existing `horizon-port-pack` crate from the
  checksum-prepared engine pinned by `upstream.lock.json`, verifies the source
  revision/toolchain, and uses Cargo `--locked --release --target`. It does not
  replace or modify Rust conversion logic.
- Cargo output goes to `.cache/port-pack-target`, outside the immutable
  checksum-prepared source. Windows builds use static CRT flags and existing PE
  architecture/system-dependency inspection. macOS builds use existing
  architecture/dependency inspection. A missing or wrong-architecture artifact
  prevents packaging.
- PyInstaller receives the platform helper through `--add-binary` alongside
  `herps-host`. `herps_launcher.javamods` and `herps_launcher.modpacks` are
  explicitly collected. The existing launcher/game arrangement, native-mod
  source option, notices, signing and archive paths remain in use. The Java Mods
  guide is copied into the package as `JAVA-MODS.txt`.
- Package metadata records the pinned source revision, Rust toolchain, target,
  build hash, binary validation, bundled hash/path and passive smoke outcome.
  The bundled hash is measured after PyInstaller processing/signing; it need not
  equal the pre-signing build hash. Gameplay remains unverified.

The configured build matrix is:

| Runner target | Rust target | Bundled filename | Actual target build in Phase 5A |
| --- | --- | --- | --- |
| Windows x64 | `x86_64-pc-windows-msvc` | `horizon-port-pack.exe` | Not performed on this Linux host |
| macOS ARM64 | `aarch64-apple-darwin` | `horizon-port-pack` | Not performed on this Linux host |
| macOS Intel | `x86_64-apple-darwin` | `horizon-port-pack` | Not performed on this Linux host |

The runner-specific build implementation and tests cover all three targets.
This table is a configuration claim, not evidence of successful target builds.
Only a Linux target/toolchain is available locally. No Linux executable is
substituted into a Windows/macOS distribution.

## Discovery and end-user requirements

`bundled_port_pack_candidates()` resolves PyInstaller's `sys._MEIPASS`, an
executable sibling, Windows onedir `_internal`, and macOS app
`Contents/MacOS`, `Contents/Frameworks` and `Contents/Resources` fallbacks. Tests
exercise paths with spaces and platform-specific filenames. Those path tests
simulate platform layouts and do not establish native app-bundle execution.

Frozen applications use bundle locations without falling back to a random
Cargo cache or PATH executable. Explicit selections retain precedence; a stale
selection raises an actionable error instead of silently choosing another
binary. Source mode retains explicit/configured/environment selection,
`CARGO_TARGET_DIR` release/debug discovery and PATH fallback.

Metadata analysis starts the bundled executable directly. Cargo and Rust are
build-time requirements; they are not end-user requirements for Java metadata
analysis. Existing trusted `.hnmod` native builds retain their separate Rust
requirements. Workspaces remain in the selected profile, outside signed app
resources. Executable path and SHA-256 remain part of backend evidence.

## Packaged smoke contract

The existing entry point accepts `--require-port-pack` together with
`--smoke-test`. Packaging and installed Windows smoke now require it.
This mode requires a frozen launcher and rejects an external override as proof
of a bundled backend. It generates two original local Fabric metadata JARs:

1. A supported data recipe: the actual backend must return `works` and the
   adapter must return **Requires porting**.
2. A data recipe with required `missinglib >=2`: the same backend `works`
   verdict must remain **Unsupported**, with `missing_dependency` and
   `insufficient_evidence` diagnostics.

No Java compiler, JVM or imported code runs. These are passive metadata/static
carry checks. The report retains command arguments, actual stdout/stderr,
exit codes, raw check JSON, diagnostics and the bundled executable hash/path.
Successful evidence includes:

```json
{
  "status": "passed",
  "pages_opened": 7,
  "port_pack": {
    "status": "passed",
    "bundled": true,
    "adapter_status": "Requires porting",
    "original_verdict": "works",
    "test_execution": null,
    "gameplay_verified": false,
    "java_bridge_available": false
  }
}
```

This is a field projection of the required contract, not an invented Rust JSON
protocol. A complete report also contains the actual helper path/hash and both
fixture results. The packager independently checks that the reported binary is
inside the bundle, has the expected filename, is executable and matches its
hash. Missing helper evidence, an external path, changed helper bytes, a failed
process or five pages prevents a package success claim.

The workflow retains the three native runner entries, installer/uninstaller,
game/native-mod checks and DMG validation. It builds the pinned helper before
the full Python suite and exports `HERPS_TEST_PORT_PACK`, so integration tests
can exercise the actual native backend. It caches the external target directory
and uploads build/smoke/package evidence plus logs on failure. **The updated
workflow was not dispatched in Phase 5A.**

## Fresh verification

Host: Linux x86_64. Python 3.12.14, pinned launcher requirements, Rust 1.95.0.
Fixtures are locally generated original data/metadata archives. No third-party
JAR, Minecraft assets, prepared proprietary resources or player data was added.

| Check | Passed | Failed | Skipped/ignored | Boundary |
| --- | ---: | ---: | ---: | --- |
| Complete Python suite | 322 | 0 | 14 skipped | 336 discovered, including real backend/Qt integration |
| Pinned port-pack Rust library | 99 | 0 | 0 ignored | Linux execution; bin/doc targets have zero tests |
| Bedrock launcher Rust suite | 10 | 0 | 0 ignored | Linux execution |
| `launcher_windows.rs` unit target | 31 | 0 | 0 ignored | Linux execution with local sockets; not Windows execution |
| `herps_host.rs` unit target | 17 | 0 | 0 ignored | Linux execution |
| Seven-page source smoke | Passed | 0 | None | Actual Qt navigation |
| Actual Linux PyInstaller freeze probe | Passed | 0 | None | Seven pages and actual bundled-helper checks; no game installation |

The full Python suite includes **35 new passing tests**: 15 packaging guards/build
inputs, 13 executable-discovery cases, five entry-point/passive smoke and legacy
preservation cases, and two CI handoff cases. The 14 skips are the existing
12 PowerShell stack-repair cases, one macOS AppleScript compilation case and
one integration case requiring `HORIZON_TEST_APK`. No new case was skipped.

The initial restricted Python run had one failure in the existing native-unit
wrapper because its loopback bind returned `EPERM` (335 tests: 320 passed,
one failed, 14 skipped). The complete final suite ran with local socket access
and passed all 336 cases except the 14 platform/input skips. The added legacy
preservation regression is included in that final count. The restricted failure
is retained in `python-tests-restricted.log`; no assertion was disabled.

The 17 shared private-server cases execute through both Rust unit targets; do
not count them as different native-platform cases. The initial Windows-launcher
unit run was denied local socket access (`EPERM`); the complete target was rerun
with local sockets available and all 31 tests passed. No assertion was weakened.
No native Windows/macOS verification is inferred from those unit tests.

The Linux frozen probe was built using `pyinstaller_command()` with the real
Linux `herps-host` and pinned Linux port-pack executable. The resulting
`.cache/java-mods-step5a/linux-freezer-probe/dist/Herps Launcher/Herps Launcher`
ran `--smoke-test --require-port-pack` successfully, opened seven pages and
recorded its helper at `_internal/horizon-port-pack`. Actual check results were
`packaging_data: works -> Requires porting` and
`packaging_missing: works -> Unsupported`. Both native subprocesses exited zero;
neither result is a Java runtime or gameplay test receipt.

Temporarily removing that probe's bundled helper produced the expected exit 1,
`status: failed`, `bundled: false` and an actionable missing-helper message,
even with the developer Cargo target cache available. The helper was restored.
This expected rejection is a passing negative check, not a remaining suite
failure. The Linux probe omits `--require-installation`, includes no game, and
does not establish a supported Windows/macOS distributable.

Additional checks: duplicate-key-rejecting workflow YAML parsing, embedded
workflow Python syntax and semantic ordering/evidence checks passed. The two
checked-in workflow tests execute the real embedded CI Python with mocked build
boundaries: all three target handoffs preserve literal paths/build evidence;
a failed build cannot export a successful handoff. These two tests are included
in the complete Python total, not additional suite coverage.

Run the full Python suite from the checkout root:

```sh
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python \
  -m unittest discover -s tests -v
```

Relevant Rust commands use the prepared source path retained in
`.cache/java-mods-step5a/prepared-source.txt`:

```sh
source scripts/cloud-env.sh
ENGINE=$(cat .cache/java-mods-step5a/prepared-source.txt)
cargo +1.95.0 test --locked --offline --manifest-path "$ENGINE/Cargo.toml" -p horizon-port-pack
cargo +1.95.0 test --locked --offline --manifest-path bedrock/launcher/Cargo.toml
rustc +1.95.0 --edition=2021 --test packaging/launcher_windows.rs -o /tmp/herps-step5a-windows-unit
/tmp/herps-step5a-windows-unit
rustc +1.95.0 --edition=2021 --test packaging/herps_host.rs -o /tmp/herps-step5a-host-unit
/tmp/herps-step5a-host-unit
```

Logs remain local under `.cache/java-mods-step5a/`, including
`rust-{port-pack,bedrock,windows,windows-with-sockets,host}.log` and the
`linux-freezer-probe/build.log`, `python-tests.log`,
`python-tests-restricted.log`, `source-smoke.{json,log}`,
`linux-frozen-smoke.{json,log}`, and `linux-frozen-missing-helper.{json,log}`.
These ignored artifacts are not published packages or redistributable
compatibility certifications. Dependency consistency, Python compilation,
documentation link/anchor checks and whitespace checks also passed.

Named new regression coverage includes:

- `test_obsolete_five_page_report_is_rejected`
- `test_stale_report_is_removed_before_process_invocation`
- `test_missing_or_changed_bundled_helper_is_rejected`
- `test_wrong_architecture_artifact_is_rejected_without_execution`
- `test_windows_meipass_executable_with_spaces_records_actual_backend_hash`
- `test_macos_application_frameworks_resources_and_macos_layouts`
- `test_missing_bundled_helper_does_not_use_unrelated_cargo_or_path_binary`
- `test_source_cargo_release_and_debug_fallbacks`
- `test_real_bundled_helper_checks_data_and_rejects_false_positive_works`
- `test_missing_java_helper_leaves_existing_mods_shaders_and_saves_functional`
- `test_failed_native_backend_build_cannot_export_a_successful_handoff`

Existing Mods, Shaders, profiles, save preservation and all Java Mods/Modpacks
regressions remain part of the complete Python suite.

## Changed files

- `.github/workflows/herps-launcher.yml`
- `tools/package_herps.py`
- `packaging/herps_entry.py`
- `herps_launcher/javamods/adapter.py` (discovery only)
- `tests/test_herps_entry.py`
- `tests/test_herps_packaging.py`
- `tests/test_herps_packaging_workflow.py`
- `tests/test_javamods_discovery.py`
- `docs/herps/java-mods-step5a.md`
- `docs/HERPS-QUICKSTART.md`, `docs/HERPS-LAUNCHER.md`,
  `docs/herps/java-mods.md`: current packaging/discovery guidance and native
  verification limits; previous reports remain unchanged.

## Remaining limits and stop point

Source packaging paths and tests are implemented. **Distributable release
readiness remains unverified** until real Windows x64/macOS ARM64/macOS Intel
builds and installed-app acceptance are performed. Installer/DMG creation,
native ABI/runtime dependencies, signing/notarization/Gatekeeper, permissions,
actual Tailscale integration and preservation during native install/uninstall
need their respective approved phases. No screenshots of native applications
are claimed.

Java bytecode execution, universal conversion, Java compatibility bridge,
packwiz import, Java Build/Test and Modpack Play remain unavailable. A static
`works` verdict cannot become Native compatibility or Tested successfully.
Data-tier carry is local and does not establish gameplay compatibility. The
documented narrower headless pack surface remains unchanged; no CLI/service
feature convergence was attempted in this packaging phase.

Existing `.hmod`/`.hnmod`, shader, Tailscale, profile/save, game installation,
authentication and licensing behavior is preserved. Packaging adds the trusted
native metadata helper and Python feature modules; it does not add proprietary
Minecraft game files, user mod JARs, local ports or credentials. The existing
verified custom game-binary package continues to be supplied through `--game`.
Mod licences and local-only port restrictions remain in force.

**Commit Phase 5A locally, then stop. Phase 5B, Phase 5C and Phase 5D require
the user's separate approval. Do not push, merge, tag, publish or release.**
