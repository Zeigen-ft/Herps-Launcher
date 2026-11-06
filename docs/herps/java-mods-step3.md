# Step 3 report: Modpack importer

Date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`. Base: Step 2 commit `bb82b6b`.

This step adds a Modpacks page and profile-local import/report coordination.
Step 1's adapter, metadata safeguards, schemas and CLI, and Step 2's Java Mods
page/library remain unchanged. No Rust conversion logic, packaging, CI, account,
ownership, acquisition or existing mod/shader/save behavior was changed.
Nothing was pushed, merged or published; Step 4 was not started.

## Formats and actions

| Format | Actual functionality |
| --- | --- |
| Modrinth `.mrpack` | Existing Rust import, local/embedded JAR resolution, conservative analysis, per-file hash checks, coverage and supported data carry. |
| CurseForge ZIP | Existing Rust import; project/file-ID records stay visible. User instance metadata or named/hash-bearing mod lists resolve local files without an API key. |
| Prism/MultiMC instances | Existing Rust instance importer, including `mmc-pack.json` and `.minecraft`/`minecraft` mod directories; a private bounded snapshot is used. |
| packwiz | **Unsupported.** The pinned backend has no packwiz parser. Identified inputs receive an explicit unsupported-format result, not a fabricated inventory or conversion. |

The new navigation order is Home, Mods, Java Mods, **Modpacks**, Shaders,
Multiplayer, Settings. The page follows the existing Qt design and provides:

- Import modpack/archive and Import instance.
- Analyze pack using the Step 1 adapter and real Rust subprocesses.
- Resolve missing files from the user's own folder or instance.
- A coverage table with name, version, conservative compatibility status,
  reason, licence, porting tier and missing dependencies.
- A **Port and Play** group with **Port supported data** and a disabled
  **Play · unavailable** control, with an explanation beside it.
- View errors with per-mod diagnostics, original verdicts, actual stdout,
  stderr, exit codes and timeouts.
- JSON and readable text exports retaining original evidence.
- A trusted backend selector using existing launcher configuration, plus an
  explicit restricted-licence review acknowledgement.

Snapshots, enumeration, hashing, analysis, carry-over, report revalidation and
export run through the existing window worker. Profile/selection changes and
conflicting operations are blocked while it runs. Loading is deferred until
the page is selected; opening Home does not start a modpack job. Progress shows
real operation phases without fabricated percentages or compatibility success.

## Backend reuse and local resolution

`LocalPackAdapter` subclasses the existing Python adapter only to supply local
files and preserve full manifest evidence. It does not replace Rust import,
metadata analysis, classification, conversion or report generation. The allowed
tool operations are `import`, `inventory --offline`, `check`, explicitly selected
`carry`, and `report`. No `fetch`, network-enabled Rust `port`, JVM, Java oracle,
mod test harness or game process is started by this workflow.

The Rust importer writes standard CurseForge IDs as opaque paths without a
`.jar` extension. The integration retains that original output, then normalizes
the local working index so the existing adapter can inspect resolved files.
`minecraftinstance.json` maps `installedAddons` project/file IDs to the user's
local filenames. Known hashes from mod lists/instance metadata are checked.
An opaque placeholder filename alone cannot prove a CurseForge ID match.

When a CurseForge mod list omits entries from its manifest, every original
manifest record is restored to coverage as resolved or explicitly unknown.
Uncorrelated named entries are retained too; uncertain identities are not
silently merged. An ID-only manifest and an unrelated mod folder are insufficient
to infer filenames: supply matching instance metadata or declared hash evidence.

The original Modrinth index is retained, including SHA-512 claims which the Rust
importer otherwise omits from its normalized file record. Every declared
supported hash is checked before a file is used. A correct SHA-1 cannot conceal
a conflicting SHA-512. SHA-512-only indexes can resolve renamed local files.
Unknown or malformed hash declarations fail closed. Hash matches establish
agreement with the supplied declaration, **not authenticated publisher identity**.

Imported archives/instances are immutable-by-receipt private snapshots under the
selected profile. Receipts are in `<profile>/modpacks/imports/<token>/`; source
snapshots and adapter runs use the existing `<profile>/java-mods/runs/` area.
Source, wrapper-report and raw-adapter-report hashes are checked on subsequent
reads. Profile-owned links/junctions and unsafe paths are rejected. Original
worlds, saves, mods and shader folders are not overwritten.

## Compatibility and partial carry-over

All Step 1 safeguards remain active. Raw `works` is evidence, not a native
compatibility or successful-test receipt. Missing dependencies, unreadable
classes, mixins, version mismatches, unsupported features and contradictory
evidence remain **Unsupported**, with reasons and `insufficient_evidence`.
Every unresolved or unsupported mod stays in the table and exported report.

Porting may carry a safe subset while retaining the unsupported remainder.
Candidates must pass the existing adapter's checks; their required dependency
ensemble must also be selected and validated. External metadata alone cannot
satisfy a dependency absent from that carried ensemble. The existing Rust
`carry` command performs conversion in the complete pack context. Existing
carry-gap checks, bounded folder/manifest validation and tree hashes validate
each resulting data folder. Failed validation removes its carried status.

Generated output remains inside its isolated run. **No imported pack content is
automatically installed, enabled or launched in the profile's game.** The Play
control is always disabled because there is no real whole-pack runtime/content
validation and gameplay-test backend. A static report or a valid data folder
cannot unlock it. Existing Home launching remains unchanged.

An observed owned fixture produced this actual report projection:

```json
{
  "status": "Unsupported",
  "summary": "Partial data carry-over: 1/3 rows validated locally. Not fully playable; unresolved/unsupported content remains. Gameplay unverified.",
  "play_enabled": false,
  "rows": [
    {"id": "good", "status": "Requires porting", "carried": true, "missing_dependencies": []},
    {"id": "missing-0", "status": "Unsupported", "carried": false, "missing_dependencies": []},
    {"id": "unsupported", "status": "Unsupported", "carried": false, "missing_dependencies": ["missinglib"]}
  ]
}
```

The unresolved JAR's dependencies are unknown, not proven absent; its row says
the local JAR is missing and its evidence is insufficient. A carried row's reason
specifies folder/manifest/hash validation and explicitly leaves gameplay
unverified. Reports always record `playable_verified: false`,
`test_execution: null` and `java_bridge_available: false`.

Saved views/exports revalidate through Step 1, recheck generated-tree receipts,
rebuild coverage and recompute the summary. Changed inputs, reports or generated
data cannot silently retain a playable, tested or validated-carried claim.

## Validation

Python 3.12.14, the pinned Qt dependencies, Rust 1.95.0, Linux x86_64. Fixtures
are locally generated original archives, JAR metadata and class bytes; no
third-party mod or Minecraft files are committed or redistributed.

```sh
python tools/make_modpack_fixtures.py --output .cache/java-mods-step3/fixtures
source scripts/cloud-env.sh
HERPS_TEST_PORT_PACK=/workspace/.horizon-target/debug/horizon-port-pack \
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python \
  -m unittest discover -s tests -v
```

Full Python result: **301 tests; 287 passed; 0 failures/errors; 14 skipped**.
All 268 existing Step 1/2/tooling tests were included; 33 new tests passed
(22 service tests and 11 actual Qt tests). The real pinned executable was enabled,
so the new integration tests were not skipped. Navigation tests now assert all
seven pages; all previous launcher/Java Mods regression tests passed.

Skipped separately: 12 PowerShell-dependent Windows stack-repair tests, one
macOS AppleScript compilation test, and one supplied-APK integration test.
No new Step 3 case was skipped in this run.

Fresh relevant Rust results:

| Target | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| Pinned `horizon-port-pack` library | 99 | 0 | 0 |
| Bedrock launcher Cargo unit suite | 10 | 0 | 0 |
| `launcher_windows.rs` unit target | 31 | 0 | 0 |
| `herps_host.rs` unit target | 17 | 0 | 0 |

The 17 shared private-server tests execute through both native targets.
Port-pack's binary and doctest targets each have zero tests, separate from its
99 executed library tests. Cargo used `--locked --offline`; local-socket checks
ran with the required execution permissions. No assertions were disabled.

Source navigation smoke returned **`{"status":"passed","pages_opened":7}`**.
Python compilation, dependency consistency and whitespace checks passed.
Step 1/2 backend/GUI implementation files were compared against `bb82b6b` and
remain unchanged; only common navigation/worker notifications were extended.

One initial focused UI run had a worker timeout because its Qt test wait loop
starved Python worker hashing of the GIL. Stack capture identified hashing,
not a deadlock. The harness now yields between Qt event passes; its deadline
and assertions were unchanged. Final focused and full runs passed.

Logs: `.cache/java-mods-step3/python-tests.log`,
`.cache/java-mods-step3/launcher-smoke.json`,
`.cache/java-mods-step3/rust-{port-pack,bedrock,windows,host}.log`, and
`/tmp/herps-step3-focused.log`. The fixture matrix covers real Modrinth,
CurseForge and instance imports, missing files, hash mismatches, unsupported
mods, missing dependencies, partial data carry and explicit packwiz rejection.

Named regressions include:

- `test_curseforge_modlist_cannot_silently_remove_manifest_only_entries`
- `test_renaming_an_unrelated_jar_to_a_curseforge_placeholder_cannot_prove_identity`
- `test_sha512_only_index_resolves_renamed_local_file_without_losing_hash_evidence`
- `test_correct_sha1_cannot_hide_a_conflicting_known_sha512`
- `test_original_works_false_positive_retains_missing_dependency_and_unsupported_features`
- `test_partial_data_carry_preserves_unsupported_rows_and_never_becomes_playable`
- `test_packwiz_is_explicitly_unsupported_without_inventing_a_parser`
- `test_pack_storage_is_profile_isolated_and_existing_game_files_are_untouched`
- `test_saved_pack_report_cannot_forge_playable_or_tested_success`
- `test_seventh_page_registration_preserves_all_existing_pages`
- `test_partial_port_has_data_outputs_but_play_remains_disabled`

The full log records every individual test name/result. Screenshots of actual
Qt widgets with owned fixtures are at
`/workspace/artifacts/herps-modpacks-analysis.png` and
`/workspace/artifacts/herps-modpacks-partial-carry.png`.

## Changed files

- `herps_launcher/modpacks/{__init__,service,page}.py`: import coordination,
  evidence/coverage and the new Qt page.
- `herps_launcher/app.py`: seventh page and shared busy/profile notifications.
- `tools/make_modpack_fixtures.py`: owned local fixture generator.
- `tests/test_modpacks_service.py`, `tests/test_modpacks_ui.py`: new regressions.
- `tests/test_herps_ui.py`, `tests/test_javamods_ui.py`: seven-page expectations.
- `docs/herps/java-mods-step3.md`: this report.

## Outstanding limits and stop point

- packwiz parsing is unavailable in the pinned backend; no replacement was
  invented. CurseForge ID-only inputs require user metadata sufficient to
  identify files. There are no automatic restricted downloads or API keys.
- Static data carry is not Java gameplay conversion. No Java bridge, native
  compatibility, real test success or fully playable pack is claimed. Play is
  disabled and existing game content is untouched.
- **Packaging is unchanged.** `tools/package_herps.py:33` and the installed
  Windows workflow still require five pages; the source launcher now has seven.
  Those distribution checks remain an outstanding failure until an approved
  packaging update. No packaged build was run or declared ready.
- Windows/macOS native execution, signing/notarization, real shader rendering,
  live multiplayer and Minecraft gameplay remain unverified on this Linux host.
  Unrelated full-engine/oracle/gameplay suites were not run; all repo-local
  Python tests and relevant Rust suites were run.
- Imports use the existing bounded local snapshot/archive limits. Operations
  complete or time out in the worker; pack carry is not forcibly interrupted.

**Commit locally on the feature branch, then stop. Step 4 requires approval.**
