# Step 1 report: Java mods subprocess adapter

Date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`, following audit commit `712fd90`.
This step adds backend/CLI integration only. No Java Mods GUI, Modpacks UI,
packaging changes, Java bridge, native gameplay conversion, or merge into main.

## Implemented behavior

`herps_launcher/javamods/` wraps the existing pinned `horizon-port-pack`; it does
not reimplement its porting engine. Python supplements the audited tool's lossy
results with bounded metadata safety checks, typed artifact validation, retained
raw evidence, and conservative compatibility decisions.

- Parse actual **file** JSON (`check.json`, `inventory.json`, `coverage.json`),
  preserve raw artifact text/JSON/SHA-256 and stdout/stderr/exit/timeout evidence.
  Reject absent/invalid fields, duplicate keys, nonfinite numbers, invalid enums,
  contradictory identities/counts, and incomplete results. No stdout JSON
  protocol or working `--version`/`--help` is assumed.
- Read Fabric/Forge/NeoForge JSON/TOML, declared dependencies and constraints,
  mixin/access-change/entrypoint/coremod declarations, and structural class-file
  metadata only. Skip method attributes, including Code; no bytecode execution,
  decompilation, JVM, oracle, harness, native build, or game launch.
- Detect missing and transitive dependencies, wrong versions, unknown constraint
  syntax, unreadable/unsupported class files, nested/ambiguous archives, unsafe
  paths, unknown/contradictory inventory, and unhandled carry evidence. Retain
  missing pack rows and unsupported content instead of silently omitting them.
- Reuse Launcher profile paths, configuration, archive checks, hashes and atomic
  writes. Runs are isolated in `<Launcher.game>/java-mods/runs/<unique-id>/`.
  Snapshot user files, check declared SHA-1 where supplied, retain SHA-256,
  reject duplicate IDs and linked workspaces, and keep ports local and disabled.
- Resolve files only from a user-provided directory/instance. Do not call
  `fetch` or the network-enabled Rust `port` pipeline. Pack operations use the
  existing `import`, `inventory --offline`, `check`, explicitly selected `carry`,
  and `report` commands. No CurseForge API key is required.
- Gate restricted/ND/NC carry-over before Rust check (which itself writes a
  port). The explicit licence acknowledgement does not grant redistribution
  rights. Unknown licences remain insufficient evidence.
- Export JSON or readable text with raw evidence. Recheck retained snapshot
  hashes and dependency closure; forged Native/Tested claims and missing or
  contradictory evidence become Unsupported. Export does not run a mod test.

Status rules: clean, supported data-only input can be **Requires porting**.
Any unresolved/unsupported/contradictory evidence is **Unsupported**, with
explicit reasons and `insufficient_evidence`. The adapter never emits **Native
compatibility**, **Tested successfully**, or **Compatible through Java bridge**.
It has no real mod-test or compilation backend, so it does not fabricate a
**Build failed** receipt for an analysis/subprocess error. `test_execution` is
null; `java_bridge_available` and `playable_verified` are false.

## Commands

With Python 3.12 and a trusted binary built from the audited pinned engine:

```sh
python -m herps_launcher check MOD.jar --port-pack /path/to/horizon-port-pack
python -m herps_launcher analyze-pack PACK_OR_INSTANCE --dependencies USER_MODS --port-pack /path/to/horizon-port-pack
python -m herps_launcher port MOD_OR_PACK --dependencies USER_MODS --port-pack /path/to/horizon-port-pack
python -m herps_launcher export-report RUN/report.json compatibility.json --format json
python -m herps_launcher export-report RUN/report.json compatibility.txt --format text
```

Both `python -m herps_launcher` with a command and
`python -m herps_launcher.javamods` dispatch headlessly without importing Qt.
Starting `python -m herps_launcher` with no arguments still starts the existing
GUI. Flags follow the command: `--profile EXISTING_PROFILE`, `--support-dir DIR`,
`--timeout SECONDS`, and `--acknowledge-restricted-license` where appropriate.
An explicit CLI profile does not overwrite the GUI's saved selection.

Binary discovery supports explicit `--port-pack`, existing launcher configuration
`port_pack_binary`, `HERPS_PORT_PACK`, the active `CARGO_TARGET_DIR`, PATH, and
frozen resource locations. No binary is newly bundled. Its hash/path and audited
source revision are recorded; no unsupported version attestation is claimed.

Analysis/port commands return 0 for a supported Requires-porting candidate and 1
for Unsupported; argparse usage errors return 2. Report-export success returns
0 even if the exported compatibility status is Unsupported. No command return
code establishes tested compatibility.

## Actual JSON examples

The owned `false_positive` fixture contains a recipe, missing required
`missinglib >=2`, malformed class bytes, declared mixins and an access widener.
The real Rust process returned **0** and wrote this exact check artifact:

```json
{
  "mod_id": "false_positive",
  "name": "Owned false_positive fixture",
  "version": "1",
  "loader": "fabric",
  "license": "MIT",
  "verdict": "works",
  "summary": "Content only: 1 recipe port.",
  "ports": [
    "1 recipe"
  ],
  "skipped": [],
  "depends": [
    "missinglib"
  ],
  "namespaces": [
    "false_positive"
  ],
  "code": {
    "classes": 0,
    "features": {},
    "events": [],
    "examples": {}
  }
}
```

The launcher CLI returned **1**. This projection from the actual adapter JSON
retains the raw Works evidence above while producing these statuses/diagnostics:

```json
{
  "run": {
    "status": "Unsupported",
    "test_execution": null,
    "java_bridge_available": false,
    "playable_verified": false
  },
  "mod": {
    "id": "false_positive",
    "status": "Unsupported",
    "diagnostics": [
      {
        "code": "unreadable_classes",
        "message": "Unreadable, truncated, preview, or unsupported class metadata: false_positive/Owned.class"
      },
      {
        "code": "required_mixins",
        "message": "Mixin declarations require Java hooks unavailable in Horizon: owned.mixins.json"
      },
      {
        "code": "unsupported_feature",
        "message": "Access wideners/transformers require unsupported Java access changes: owned.accesswidener"
      },
      {
        "code": "missing_dependency",
        "message": "Required dependency missinglib (>=2) is absent from user-provided files"
      },
      {
        "code": "unsupported_feature",
        "message": "Java class code cannot run through a Java bridge; only data-tier carry-over is available"
      },
      {
        "code": "unreadable_classes",
        "message": "Backend read 0 of 1 class files"
      },
      {
        "code": "missing_dependency",
        "message": "Backend requires unresolved dependency missinglib"
      },
      {
        "code": "insufficient_evidence",
        "message": "Static port-pack verdict does not establish full compatibility; unresolved or contradictory evidence remains"
      }
    ]
  }
}
```

Full captured example: ignored `.cache/java-mods-step1/false-positive-cli.json`;
fixture generator source: `tools/make_javamods_fixtures.py`. The displayed JSON
is observed output, not a proposed schema. Generated JARs are local/ignored.

## Validation

Final commands run from the repository root:

```sh
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python \
  tools/ci_run.py .cache/java-mods-step1/python-tests.log \
  /workspace/.herps-audit-venv/bin/python -m unittest discover -s tests -v
```

Python final result: **239 discovered; 225 passed; 0 failures/errors; 14 skipped**.
This includes all 159 existing cases (145 pass/14 skip), plus **80 new passing
adapter/schema/metadata/CLI tests**. All five existing Qt widget tests ran and
passed; real-binary Java adapter tests were enabled, not skipped.

Skipped separately: 12 Windows stack-repair tests require PowerShell, one
AppleScript compilation test requires macOS, and one supplied-APK integration
test requires `HORIZON_TEST_APK`. No third-party APK or game resources were
acquired for this step.

Rust final results (Linux host, Rust 1.95.0):

| Target | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| Pinned `horizon-port-pack` library | 99 | 0 | 0 |
| Repository Bedrock launcher Cargo tests | 10 | 0 | 0 |
| `packaging/launcher_windows.rs` native unit target | 31 | 0 | 0 |
| `packaging/herps_host.rs` native unit target | 17 | 0 | 0 |

The 17 shared private-server tests execute through both host and Windows
launcher targets. Port-pack's binary and doctest targets separately have zero
tests; they are not counted as coverage. One initial restricted-sandbox native
socket test failed with EPERM; rerunning the complete target with local socket
access passed 31/31. Final failures are zero; no assertion was weakened.

Rust commands used the existing pinned toolchain/locks:

```sh
cargo +1.95.0 test --locked --offline --manifest-path "$ENGINE/Cargo.toml" -p horizon-port-pack
cargo +1.95.0 test --locked --offline --manifest-path bedrock/launcher/Cargo.toml
rustc +1.95.0 --edition=2021 --test packaging/launcher_windows.rs -o /tmp/herps-step1-launcher-unit
/tmp/herps-step1-launcher-unit
rustc +1.95.0 --edition=2021 --test packaging/herps_host.rs -o /tmp/herps-step1-host-unit
/tmp/herps-step1-host-unit
```

Logs: `.cache/java-mods-step1/python-tests.log`,
`/tmp/herps-step1-rust-port-pack.log`, `/tmp/herps-step1-rust-bedrock.log`,
`/tmp/herps-step1-rust-launcher-windows-escalated.log`, and
`/tmp/herps-step1-rust-herps-host.log`. Also checked source UI smoke (five pages),
dependency consistency, Python compilation, shell syntax and staged whitespace.

### Named regression tests

In `tests/test_javamods_adapter.py`, the real pinned binary produces Works for
the original critical fixtures; these tests assert it cannot become a successful
compatibility status:

- `test_actual_works_with_missing_dependency_stays_unsupported`
- `test_actual_works_with_unreadable_class_stays_unsupported`
- `test_actual_works_with_required_mixins_stays_unsupported`
- `test_actual_works_with_access_widener_stays_unsupported`
- `test_actual_works_with_minecraft_version_mismatch_stays_unsupported`
- `test_contradictory_works_identity_cannot_become_a_successful_status`
- `test_works_cannot_hide_kept_custom_recipes_or_unreadable_carry_files`
- `test_unknown_inventory_class_or_confidence_cannot_hide_behind_works`
- `test_missing_transitive_dependency_blocks_apparently_successful_parent`
- `test_readable_java_class_in_dependency_is_not_treated_as_data_only`
- `test_mrpack_same_filename_with_wrong_hash_is_not_accepted`
- `test_uppercase_declared_sha1_matches_the_same_local_file`
- `test_standalone_port_cannot_prove_carry_of_satisfied_dependency_ensemble`
- `test_fully_local_pack_port_uses_real_carry_without_claiming_playability`
- `test_symlinked_profile_ancestor_cannot_escape_profile`

In `tests/test_javamods_cli.py`:

- `test_cli_dispatch_never_imports_qt_or_the_gui`
- `test_export_demotes_forged_native_tested_and_missing_check_claims`
- `test_export_revalidates_dependencies_after_diagnostics_and_status_are_forged`
- `test_export_rejects_changed_or_missing_input_snapshot_as_insufficient`
- `test_export_rejects_duplicate_and_nonfinite_json_evidence`

Metadata/schema cases include
`test_false_positive_works_fixture_exposes_all_suppressed_evidence`,
`test_duplicate_dependency_keys_cannot_hide_a_missing_dependency`,
`test_required_loader_never_becomes_a_working_java_bridge`,
`test_unknown_version_constraint_is_insufficient_evidence`,
`test_actual_works_shape_retains_missing_dependency_without_status_translation`,
and `test_every_required_check_field_is_validated`.
All individual names/results are present in the full Python test log.

## Changed files

- `herps_launcher/__main__.py`: headless command dispatch; no-argument GUI retained.
- `herps_launcher/javamods/{__init__,__main__,adapter,cli,metadata,models}.py`:
  adapter, schemas, passive safeguards, CLI and local evidence reports.
- `tools/make_javamods_fixtures.py`: owned local fixture generator.
- `tests/test_javamods_{adapter,cli,metadata,models}.py`: 80 new tests.
- `docs/herps/java-mods-step1.md`: this report.

No Rust engine source, lockfile, requirements, existing GUI page, packaging,
authentication, acquisition, ownership or existing mod/shader/game behavior was
changed. No third-party JARs or generated ports are committed. Step 1 is committed
locally on the feature branch; the resulting commit hash is reported in chat.

## Remaining limitations and stop point

- No native compatibility or gameplay testing is implemented. Java code,
  required loaders/bridges, mixins and access changes remain unsupported. Even
  structurally readable Java classes are not evidence of executable behavior.
- Version evaluation intentionally supports a limited numeric exact/comparator,
  wildcard and Maven-range subset. Unknown syntax, missing ranges or newer/
  preview class formats fail closed. This is not a full Fabric/Maven resolver.
- Data-tier ports remain local folder mods inside run workspaces, never enabled
  or installed automatically. A standalone JAR with required local dependencies
  cannot establish ensemble carry; use a complete local instance/pack port.
  Neither a carried folder nor Requires porting means fully playable.
- Carry uses the pinned tool's static defaults, without running its Java oracle
  or supplying prepared game tables. Vanilla-template availability and behavior
  on an actual installation have not been validated.
- Missing files, pack overrides, manifest discrepancies and unsupported rows
  remain explicit blockers. No unrestricted automatic downloads, packwiz parser,
  Java oracle execution, conversion bridge or build/test button was added.
  Step 3's full importer/UI is not implemented by these backend commands.
- Import snapshots are bounded (512 MiB/4096 files for instances, 32 path levels;
  existing archive reader uses its entry limits, with 64 MiB expanded per JAR).
  Larger inputs need a separately reviewed streaming implementation.
- Windows/macOS native executables, packaging, code signing, real rendering,
  two-computer multiplayer and Minecraft gameplay remain unverified here.
  All repo-local Rust unit targets and the relevant port-pack suite ran;
  unrelated full-engine/game/oracle harness suites did not run.
- Export requires retained source snapshots to re-establish candidate evidence;
  deleting/moving a run or altering its inputs conservatively invalidates it.

**STOP after Step 1. Step 2 and all GUI/packaging changes require new approval.**
