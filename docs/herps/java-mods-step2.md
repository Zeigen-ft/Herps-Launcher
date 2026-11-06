# Step 2 report: Java Mods GUI

Date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`. Base: Step 1 commit `e4bdf30`.

Step 2 adds a source-launcher Java Mods page and profile-local management of
verified data folder ports. **All Step 1 adapter, CLI, schema and metadata files
remain unchanged.** No Rust engine, packaging, CI, authentication, acquisition,
modpack import UI, or Step 3 work was changed. No push or merge was performed.

## User flows

- Navigation is now Home, Mods, **Java Mods**, Shaders, Multiplayer, Settings.
  Existing pages retain their behavior and the shared dark Qt design.
- **Import Java mod** copies a Fabric, Forge or NeoForge JAR into the selected
  profile and inspects metadata using Step 1. It never starts Java or executes
  imported code. Source hashes and immutable local snapshots are retained.
- **Analyze** invokes the real `PortPackAdapter.check`. Details distinguish the
  original backend verdict from the conservative adapter status and show licence,
  Minecraft requirements, dependencies, mixins, access changes, unsupported
  features, reasons and source/hash evidence. Incomplete evidence is labelled
  explicitly; Unsupported does not automatically mean proven incompatibility.
- **Resolve dependencies** selects the user's own mod folder or instance and
  reruns real analysis. Missing/transitive dependencies and version mismatches
  remain visible. Step 1 validates known hashes and records SHA-256 evidence;
  a computed hash is not claimed to authenticate the publisher. No automatic
  mod download, CurseForge key, or new dependency resolver was added.
- **Port to Herspers · data only** calls the existing single-JAR data-tier
  backend. It installs only a validated, recorded folder port, initially
  disabled. Java code is not converted and gameplay is not labelled tested.
  Restricted ND/NC licences require explicit acknowledgement before even
  analysis, because the underlying check command also carries data locally.
- **View errors** shows actual diagnostic messages and recorded command output,
  stdout, stderr, exit codes and timeouts. Missing executables and filesystem
  failures produce actionable errors without a successful result claim.
- **Local data ports** provides enable/disable, remove-to-backup, open mod
  directory and compatibility details. Existing worlds, mod data, packages,
  source JARs, unrelated settings and other profiles are preserved.
- **Export JSON / Export text** calls Step 1 export and revalidation. Saved
  report status/hash/dependency evidence is rechecked before rendering as well;
  editing a report cannot turn it into a validated native or tested result.
- **Build Mod · Not available yet** and **Test Mod · Not available yet** remain
  disabled. The Java bridge is displayed as unavailable.
- **Select backend** saves the trusted port-pack executable path using existing
  launcher settings. This does not bundle, install or download a binary.

## Operations and cancellation

Archive inspection, hashing, enumeration, report revalidation/export, analysis,
porting and managed file mutations use the existing `Worker(QThread)` and
`Window.start_work` mechanism. The shared helper now accepts optional progress
and failure handlers while preserving existing callers. The UI shows phase
messages and an indeterminate progress bar; it does not fabricate percentage
completion or compatibility results. Profile and conflicting actions remain
locked while a worker/game is active.

Analysis supports **Discard analysis**: an in-flight backend process finishes
or reaches its existing timeout, then the result is discarded before saving.
No thread/process is forcibly terminated. A lock-protected commit boundary
disables discard once result recording begins. Import, installation, enable and
backup operations are not interrupted midway. Cancelled run evidence may remain
locally for diagnosis, but no cancelled result is installed or enabled.

Library enumeration is deferred until the page is selected, so opening Home
does not start unrelated Java work. Saved-report reads and hashes remain off
the GUI thread. A failed load stops retrying automatically and offers an
explicit Refresh action and View errors.

## Real folder-port management

The pinned engine's `crates/horizon-mods/src/manifest.rs` discovers immediate
`horizon-mods/<folder>/horizon-mod.toml` directories. Data-only API 0.2 manifests
with capability `registries` require no WASM executable. The renderer's mod-list
settings use `horizon-mods.txt`, with `mod.<id>:true/false` enable keys.

`JavaModLibrary` uses that existing contract; it does not wrap a data port in a
fake native or WASM mod. It checks report/profile/input identity, Step 1 export
validation, manifest API/side/capabilities, bounded data paths, generated-tree
hash receipts, installed-tree integrity and duplicate runtime/native/folder IDs.
File copies are staged and compared before publication. New registrations start
disabled; a receipt-write failure rolls back the newly copied installation.

Mutations share the launcher's operation lock and a profile library lock.
Profile-owned symlinks/junctions are rejected, while ordinary system ancestors
above the selected support directory (such as macOS's `/var` layout) are allowed.
Enable/disable preserves unknown settings through existing atomic pair helpers.
Removal disables the port and moves its content plus receipt to
`<profile>/java-mods/removed/<unique-id>-<mod-id>/`. It does not delete saves or
`horizon-mod-data`.

Edited imports, generated outputs, installed folders and receipts are preserved
and rejected for review rather than overwritten or deleted silently.

## Observed compatibility behavior

The real owned regression fixture has a recipe, a missing dependency, invalid
class bytes, mixins and an access widener. Rust still reports `works`; the GUI
shows:

```text
Compatibility: Unsupported
Original backend verdict: works (static backend evidence; not a compatibility/test receipt)
Missing / incomplete evidence · insufficient_evidence: ...
Finding · missing_dependency: Required dependency missinglib (>=2) is absent ...
Finding · required_mixins: Mixin declarations require Java hooks unavailable in Horizon ...
Finding · unreadable_classes: Backend read 0 of 1 class files
```

Clean supported data content displays **Requires porting**. Installation status
says **Local data port installed disabled**, and explicitly states that Java
functionality was not converted and gameplay is unverified. Neither the GUI nor
the unchanged backend emits Native compatibility, Tested successfully, or
Compatible through Java bridge for these static operations.

`tools/smoke_herps_native.py` was investigated again. It is a Windows-only
`.hnmod` native rebuild/selection/rollback smoke check using an owned hook. Its
own report leaves `hook_execution_verified` and `gameplay_verified` false. It
cannot substantiate a Java Build Mod or Test Mod action and was not used as one.

## Validation

Python 3.12.14, pinned Qt dependencies, Rust 1.95.0, Linux x86_64. Generated test
JARs are owned synthetic fixtures, local/ignored, never third-party game/mod
files. The actual pinned port-pack executable was enabled for the integration
tests rather than skipped.

```sh
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python \
  -m unittest discover -s tests -v
```

Final Python result: **268 tests; 254 passed; 0 failed/errors; 14 skipped**.
This includes all 239 Step 1/existing tests and **29 new passing Step 2 tests**:
15 GUI tests and 14 library/preservation tests. The existing Qt test now asserts
all six navigation entries and checks each page's actual registration. Existing
Home/Mods/Shaders/Multiplayer/Settings and Step 1 tests passed.

Skipped separately: 12 PowerShell-dependent Windows stack-repair cases, one
macOS AppleScript compilation case and one supplied-APK integration case.
No new Step 2 tests were skipped in this run.

Rust tests were run fresh with the pinned toolchain and locked/offline Cargo:

| Target | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| Pinned `horizon-port-pack` library | 99 | 0 | 0 |
| Repository Bedrock launcher | 10 | 0 | 0 |
| `packaging/launcher_windows.rs` unit target | 31 | 0 | 0 |
| `packaging/herps_host.rs` unit target | 17 | 0 | 0 |

The 17 shared private-server tests run through both native targets; do not
interpret those as different tests. Port-pack's binary/doctest targets each
contain zero tests, separately from the 99 executed library tests. Local socket
tests ran with the required execution permissions. No Rust assertion was disabled.

Source UI smoke returned **`{"status":"passed","pages_opened":6}`**.
Python compilation, dependency consistency and whitespace checks passed.
Step 1 backend files were compared with `e4bdf30` and have no changes.

Logs:

- `.cache/java-mods-step2/python-tests.log`
- `.cache/java-mods-step2/launcher-smoke.json`
- `/tmp/herps-step2-ui.log`
- `/tmp/herps-step2-library.log`
- `/tmp/herps-step2-rust-{port-pack,bedrock,launcher-windows,herps-host}.log`

### Named regressions

`tests/test_javamods_ui.py` includes:

- `test_java_mods_registration_preserves_all_existing_pages`
- `test_fabric_forge_neoforge_imports_retain_local_copies_without_execution`
- `test_actual_false_positive_works_is_rendered_as_unsupported_with_full_evidence`
- `test_resolve_dependencies_uses_user_directory_and_retains_hash_evidence`
- `test_missing_binary_failure_is_visible_without_a_success_claim`
- `test_failed_subprocess_shows_exit_stdout_stderr_and_raw_diagnostics`
- `test_json_and_readable_exports_preserve_actual_backend_evidence`
- `test_imports_and_selection_are_isolated_per_profile`
- `test_background_analysis_keeps_event_loop_live_and_blocks_profile_mutations`
- `test_cancelled_analysis_discards_new_report_after_passive_worker_finishes`
- `test_cancel_is_unavailable_once_result_recording_begins`
- `test_saved_report_is_revalidated_before_rendering_after_profile_reload`
- `test_ui_never_promotes_forged_saved_success_statuses`
- `test_failed_library_load_stops_retrying_and_keeps_actionable_error`
- `test_port_enable_disable_and_backup_preserve_saves_and_original_import`

Library tests additionally cover changed imported/generated/installed files,
forged reports, duplicate engine IDs, profile escapes, trusted system layouts,
operation locks and receipt-write rollback. Every individual outcome is recorded
in the full Python log.

## Screenshots

Actual source Qt widgets, rendered offscreen at 1130×790 with owned fixtures:

- `/workspace/artifacts/herps-java-mods-unsupported.png`: original `works` verdict
  alongside Unsupported, incomplete evidence and metadata findings.
- `/workspace/artifacts/herps-java-mods-data-port.png`: local folder port OFF,
  Requires porting and explicit unverified-gameplay wording.

Screenshots and generated content are artifacts outside tracked source.

## Changed files

- `herps_launcher/app.py`: sixth page, shared worker callbacks and truthful
  package-count wording; existing pages retained.
- `herps_launcher/javamods/page.py`: Java Mods Qt page.
- `herps_launcher/javamods/library.py`: profile import and data-port management.
- `tests/test_herps_ui.py`: six-page navigation regression.
- `tests/test_javamods_ui.py`: real Qt/adapter integration regressions.
- `tests/test_javamods_library.py`: file/profile preservation regressions.
- `docs/herps/java-mods-step2.md`: this report.

## Unverified and known limitations

- Windows x64/macOS ARM64/macOS Intel native GUI execution, installation,
  signing, GPU rendering, live Tailscale gameplay and Minecraft gameplay were
  not verified on this Linux host. Unrelated full-engine/oracle/gameplay suites
  were not run. Repo-local Rust unit targets and relevant port-pack tests ran.
- **Packaging remains unchanged, as requested.**
  `tools/package_herps.py:33` and `.github/workflows/herps-launcher.yml:110`
  still require five pages. The source smoke now correctly reports six, so
  those old distribution checks will reject the new UI until a separately
  approved packaging update. No new packaged build is claimed ready.
- A trusted port-pack binary is still required separately; no executable was
  bundled. Missing binary errors are visible with a backend selector.
- Only data-tier carry-over is available. Required Java code/loaders/bridges,
  mixins and access changes remain unsupported. Template availability and
  behavior on a real game installation have not been tested.
- Individual JAR ports with required local dependency ensembles remain blocked
  by Step 1. No modpack input or modpack import UI was added to bypass that
  safeguard. Port management is restricted to engine-compatible IDs and
  validated API 0.2 data-only folder content.
- Cancellation discards analysis only at the safe boundary described above;
  it does not stop an in-flight subprocess or interrupt installation. Large
  inputs use the existing backend/library bounds and may take time to verify.

**Step 2 ends with a local feature-branch commit. Stop and await approval for
Step 3.**
