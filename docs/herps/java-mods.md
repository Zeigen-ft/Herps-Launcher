# Java Mods and Modpacks

These workflows are available in the source launcher on
`feature/herps-java-compatibility`. They inspect Java mod metadata and carry
supported data into Horizon folder mods. They do not execute Java bytecode,
convert arbitrary Java gameplay, or establish tested gameplay compatibility.

The source launcher has seven pages: Home, Mods, Java Mods, Modpacks, Shaders,
Multiplayer and Settings. Native Windows/macOS execution of the new workflows
remains unverified. Phase 5A implements seven-page packaging and native helper
bundling; the [Phase 5A report](java-mods-step5a.md) distinguishes Linux source
and frozen-probe evidence from the native builds still pending. Older downloadable
packages do not contain these additions. See the
[quickstart](../HERPS-QUICKSTART.md) for source setup and existing game
installation instructions.

## Prepare the source launcher

Run the source launcher with Python 3.12 and the pinned
`herps_launcher/requirements.txt` dependencies. Analysis and porting require a
trusted `horizon-port-pack` executable built from the repository's pinned engine
source with Rust 1.95.0. A JDK is not needed for passive mod analysis; the existing
game resource-preparation workflow is separate. New packaging builds include the
matching helper automatically; packaged metadata analysis requires no Cargo,
Rust or JDK on the end user's machine. Native package verification is pending.
Frozen launchers search their bundled resource/application directories instead
of developer Cargo caches or PATH. An explicit backend selection overrides
discovery; clear an obsolete selection or reinstall if the helper is missing.

For a developer build, run these existing commands from the repository root:

```sh
python tools/prepare_upstream.py
cargo +1.95.0 build --locked --manifest-path "/printed/prepared/source/Cargo.toml" --target-dir ".cache/port-pack-target" -p horizon-port-pack --bin horizon-port-pack
```

Replace `/printed/prepared/source` with the source directory printed by the
first command. Keep the target directory outside that checksum-prepared source
tree so generated files do not invalidate its fingerprint. With the example
above run from the repository root, the binary is
`.cache/port-pack-target/debug/horizon-port-pack.exe` on Windows or
`.cache/port-pack-target/debug/horizon-port-pack` on macOS/Linux. Build with the
native toolchain for the computer that will run it. Rust 1.95.0 must already be
installed; the build command does not install that toolchain for you.

Open **Java Mods → Select backend…** or **Modpacks → Select backend…** and select
that executable. Both pages use the same launcher setting. The selector does
not install or download a helper. The launcher records the chosen binary path
and hash; port-pack has no usable version-query protocol, so choose a trusted
build of the pinned source.

Select your profile on **Home** before importing. A new profile separates game
data and does not copy existing worlds. Close the game and wait for any worker
to finish before changing profiles, enabling content, or removing a port.

## Import and inspect one Java mod

1. Open **Java Mods → Import Java mod…** and select a Fabric, Forge or NeoForge
   `.jar` that you are entitled to use.
2. Select the imported row. The launcher keeps a private copy and displays the
   mod ID, name, version, loader, Minecraft requirement, declared licence,
   dependencies, mixins, access changes and class-file census.
3. Click **Analyze**. Wait for the worker to finish, then review both the
   conservative compatibility status and the **Original backend verdict**.
4. Use **View errors** to inspect actual diagnostics, command stdout/stderr,
   exit codes and timeouts. Export the report when you need the complete raw
   evidence; long text may be shortened on screen.

Import and analysis never start a JVM, run a mod, decompile Java, execute a
native build, or launch a Java oracle. Metadata inspection is bounded and
class-file method bodies are not interpreted. Unsupported or unreadable class
metadata remains a limitation rather than being counted as successful analysis.

Importing does not enable a JAR in the game. Forge/Fabric/NeoForge JARs are not
the existing `.hmod` or `.hnmod` formats managed by the **Mods** page.

## Read compatibility evidence

| Display or field | Meaning |
| --- | --- |
| **Requires porting** | A supported data-only candidate passed the available static checks. It has not become native Java compatibility or tested gameplay. |
| **Unsupported** with `insufficient_evidence` | Evidence is missing, contradictory or insufficient. Read the specific findings; unknown compatibility is not proof of incompatibility. |
| **Unsupported** with a concrete finding | A missing dependency, version conflict, required Java loader/code, mixin, access change, malformed class or other unsupported feature blocks the operation. Additional incomplete-evidence reasons may also apply. |
| Original backend `works`, `partly` or `no` | The Rust tool's static finding, preserved as evidence. `works` alone does not prove compatibility. |
| `test_execution: null`, `playable_verified: false` | No real mod/gameplay test has been recorded. |

The audited tool can report `works` despite missing dependencies or unreadable
classes. The launcher cross-checks those findings and keeps the result
Unsupported. It never upgrades that verdict to **Native compatibility**,
**Tested successfully**, or **Compatible through Java bridge**.

Dependency version evaluation supports a limited numeric exact/comparator,
wildcard and Maven-range subset. Unknown constraint syntax, missing Minecraft
ranges, newer/preview class formats and incomplete metadata fail closed. This
is not a complete Fabric/Maven dependency solver.

## Resolve dependencies from your own files

On **Java Mods**, click **Resolve dependencies…** and select your own mod folder
or Minecraft instance. The launcher reruns analysis with those files, checks
dependency IDs, supported version constraints and transitive requirements, and
records local file hashes. Missing files or mismatched versions remain visible;
selecting a directory is not itself a successful resolution.

Source SHA-256 receipts detect changes to imported snapshots. Where a pack
supplies known hashes, the Modpacks workflow checks those declarations as
described below. A matching hash means agreement with the supplied declaration;
it does not authenticate a publisher or grant a licence.

No automatic restricted-mod download or CurseForge API key is required. Keep
your original files and import a fresh copy if a saved snapshot changes.

## Carry one mod's supported data

1. Review the analysis and licence before continuing.
2. Click **Port to Herspers · data only**.
3. If a complete supported single-mod data port is produced and validated, the
   launcher registers a Horizon API 0.2 folder mod under this profile's
   `horizon-mods/<id>/`. It starts **disabled**.
4. Open **Java Mods → Local data ports**, select the row, and use **View
   compatibility details** before deciding whether to enable it.

This reuses the existing Rust data carry-over. Java classes, mixins, custom
Java gameplay or a compatibility bridge have not been converted. Folder,
manifest and hash validation are not gameplay tests; vanilla-template behavior
on a real installation remains unverified.

A standalone JAR with required local dependencies cannot establish the carried
dependency ensemble and remains blocked for standalone porting. The Modpacks
workflow can assess an actual pack/instance and carry a validated subset in
that pack context.

### Enable, disable and remove a data port

The **Local data ports** tab provides **Enable / disable**, **Open mod
directory**, **View compatibility details** and **Remove to backup**.

Enable/disable updates the existing `horizon-mods.txt` setting while preserving
unrelated entries. Removal disables the port and moves its content and receipt
to `java-mods/removed/<unique-id>-<id>/` inside the selected profile. It does not
delete worlds, `horizon-mod-data`, source JARs or another profile's files. There
is no automatic restore button; preserve the backup for review rather than
moving edited files blindly into the active mod folder.

Duplicate runtime/native/folder IDs and changed generated or installed files
are refused. The launcher preserves edits instead of overwriting them. Use
**View errors** for the affected path, retain the edited data, and reanalyse or
reimport clean inputs as appropriate.

## Import and analyse a modpack

Use **Modpacks** for the complete pack coverage workflow. Every unresolved or
unsupported source entry remains visible, including uncertain CurseForge IDs.

### Modrinth `.mrpack`

1. Click **Import modpack…** and select the `.mrpack` archive.
2. Click **Analyze pack**. Embedded local JARs can be inspected; unresolved
   indexed files remain in the table.
3. Click **Resolve missing files…** and select your own mod folder or installed
   instance if files are missing.
4. Review each row and the playable-status summary.

The GUI service retains the original index and checks declared hashes,
including SHA-512-only indexes and conflicting SHA-1/SHA-512 claims. Renamed
local files can match by a known hash. It does not download missing mods.

### CurseForge ZIP

1. Click **Import modpack…** and choose the CurseForge ZIP.
2. Analyse it, then select **Resolve missing files…** and choose your own
   installed instance or a folder containing the identifiable required files.
3. Review every unresolved project/file-ID entry and any hash mismatch.

An ID-only CurseForge manifest does not necessarily contain filenames or
hashes. A matching instance's `minecraftinstance.json` can associate
`installedAddons` project/file IDs with local filenames. Named/hash-bearing mod
lists also help resolve user files. A random folder and a renamed
`curseforge-<project>-<file>.jar` do not prove that identity. Supply sufficient
instance metadata or declared hash evidence; the launcher does not guess or
request an API key.

If a mod list omits manifest entries, those entries stay visible as unknown or
unresolved. Named entries that cannot be correlated are retained separately;
the report does not silently claim that they are the same mod.

### Prism/MultiMC instance

Click **Import instance…** and select the complete instance directory, including
`mmc-pack.json` where present and its `.minecraft` or `minecraft` mod directory.
Click **Analyze pack**, then resolve any missing files from your own folders.
The importer snapshots relevant local metadata/content; it does not overwrite
or move the instance's worlds and saves.

### packwiz

Packwiz import is **not available yet**. The pinned Rust importer has no
packwiz parser. Identified packwiz input receives an explicit Unsupported result,
without a fabricated inventory or port.

### Coverage table and partial carry-over

The table includes **Name**, **Version**, **Compatibility**, **Reason**,
**Licence**, **Porting tier** and **Missing dependencies**. Unknown names,
versions, licences and dependencies remain uncertain. “None recorded” on an
unreadable or missing JAR does not establish a complete dependency analysis.
Select a row for its original evidence, and use **View errors** for diagnostics
and process output.

The **Port and Play** group contains two separate controls:

- **Port supported data…** carries only the subset that passes the existing
  safeguards and has a validated dependency ensemble. Generated folders and
  their validation receipts remain in the isolated run.
- **Play · unavailable** stays disabled. No complete modpack runtime/content
  validation and gameplay-test backend exists, so even a fully carried static
  data subset cannot unlock it.

A summary such as “Partial data carry-over: 1/3 rows validated locally” does not
mean that the pack is fully playable. Unsupported and missing content remains
listed. Modpack output is not automatically installed, enabled or launched in
the profile's existing game; original mods and shaders remain untouched.

## Licence review

Review each mod's declared licence and your intended use. Java Mods prompts
before processing restricted/non-commercial/no-derivatives content. Modpacks
has an **I reviewed restricted licences** acknowledgement with a warning.
Unknown licences remain insufficient evidence.

Acknowledgement is not a grant of modification or redistribution rights. Even
the backend's `check` command writes local data carry-over, so licence review
applies before analysis that invokes it. Keep generated ports local and do not
commit or redistribute third-party JARs, ports or Minecraft resources. This
workflow does not alter authentication, ownership verification or existing
game-resource acquisition.

## Export and preserve reports

On either page, select the analysed item and choose **Export JSON…** or **Export
text…**. Exports include conservative results and raw evidence, not simulated
builds or test receipts. The launcher rechecks retained input hashes,
dependencies and relevant output-tree receipts. Changed or missing evidence can
become Unsupported or block export.

Keep the profile's snapshots, reports and receipts together. A portable exported
report documents its recorded evidence; it is not an attestation that the mod
works on another computer. Deleting or editing retained run files can invalidate
future revalidation.

## Profiles and storage

The existing launcher path helpers select support directories:

| Platform | Default support directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Herspers Minecraft` |
| macOS | `~/Library/Application Support/Herspers Minecraft` |

The default profile uses `<support>/game`; additional profiles use
`<support>/herps-launcher/profiles/<id>`. Relevant locations inside the selected
profile are:

| Location | Purpose |
| --- | --- |
| `java-mods/imports/` | Private single-JAR snapshots and import receipts. |
| `java-mods/runs/` | Adapter runs, raw reports and local carry outputs. |
| `java-mods/ports/` | Receipts for installed single-mod data ports. |
| `java-mods/removed/` | Removed data-port content and backup receipts. |
| `modpacks/imports/` | Pack import receipts referring to private run snapshots. |
| `horizon-mods/<id>/` | Registered single-mod data folder, initially disabled. |

Profile-owned links/junctions, edited snapshots and ambiguous IDs are rejected.
Imports use bounded file counts, sizes and archive expansion limits; oversized
inputs may require a separately reviewed streaming implementation.

## Actual command-line interfaces

From the repository root, use your source virtual environment's Python. The
following are implemented launcher commands; replace the example paths with
your own paths and place options after the command:

```sh
python -m herps_launcher check "/your/mod.jar" --port-pack "/your/horizon-port-pack" --dependencies "/your/mods"
python -m herps_launcher analyze-pack "/your/PrismInstance" --port-pack "/your/horizon-port-pack"
python -m herps_launcher port "/your/data-only-mod.jar" --port-pack "/your/horizon-port-pack"
python -m herps_launcher export-report "/your/profile/java-mods/runs/RUN/report.json" "/your/compatibility.json" --format json
python -m herps_launcher export-report "/your/profile/java-mods/runs/RUN/report.json" "/your/compatibility.txt" --format text
```

The equivalent headless entry point is `python -m herps_launcher.javamods`.
Use `--profile EXISTING_PROFILE` for an existing profile, `--support-dir DIR`
for its support root and `--timeout SECONDS` for the subprocess deadline.
Export requires the report to belong to the selected profile. Restricted
content requires explicit `--acknowledge-restricted-license` after licence
review. The no-argument `python -m herps_launcher` starts the GUI.

These CLI commands use the **basic Step 1 adapter**. They do not call the newer
Modpacks GUI service: CurseForge ID reconciliation, enhanced embedded-file
handling, partial-subset coordination and the original-index SHA-512 checks
described above are GUI/service features. Use the **Modpacks page** for those
pack workflows; do not assume CLI parity. CLI `port` produces local run output
and does not register a Java Mods library installation.

Launcher check/analyse/port returns 0 for a supported Requires-porting candidate
and 1 for Unsupported. Usage errors return 2. Export returns 0 when the export
succeeds even if its compatibility status is Unsupported. None of these exit
codes means tested compatibility.

The existing Rust tool also has these actual commands:

```text
horizon-port-pack import <pack> <work>
horizon-port-pack inventory <work> --offline
horizon-port-pack check <jar> <out>
horizon-port-pack carry <work> [<mod id>...]
horizon-port-pack report <work>
```

They write JSON **files**, including `check.json`, `inventory.json` and
`coverage.json`; their stdout is human-oriented progress. There is no `--json`
flag. The pinned tool's `--help` returns an exit-1 usage error, and it has no
working version-query command. Raw Rust `port`/`fetch` may download files;
`--offline` is not a complete network-disable switch. The GUI uses controlled
local operations instead. See the [audit](java-mods-audit.md) for the full exact
CLI and JSON contracts.

## Feature status and evidence

“Available in source” describes implementation, not a ready installer or proven
gameplay. Automated evidence below uses owned fixtures and the real pinned tool
on Linux; Windows/macOS runtime execution remains unverified.

| Feature | Source status | Automated evidence | Windows/macOS |
| --- | --- | --- | --- |
| Fabric/Forge/NeoForge import and passive metadata inspection | Available in source | Three-loader import and structural metadata tests | Unverified |
| Conservative compatibility rendering and dependency checks | Available in source | Actual false-positive `works`, missing/transitive dependencies, version and mixin regressions | Unverified |
| Single-mod local data carry, enable/disable and backup | Available in source | Real folder carry, receipt/hash checks and preservation tests | Unverified |
| Modrinth, CurseForge and Prism/MultiMC GUI import | Available in source | Real importer fixtures, complete coverage and local resolution tests | Unverified |
| Partial pack data carry with Play disabled | Available in source | Validated-subset and no-Play regressions | Unverified |
| JSON/text report export and revalidation | Available in source | Real backend evidence, tampering and changed-tree regressions | Unverified |
| Seven-page source navigation | Available in source | Actual Qt navigation and source smoke | Unverified |
| Distribution of these new workflows | Not ready | Packaging checks and binary bundling remain blockers | Unverified |
| Java bytecode execution or universal Java mod conversion | Not available yet | No working implementation | Unavailable |
| Java compatibility bridge | Not available yet | Explicitly unavailable; no working bridge | Unavailable |
| packwiz import | Not available yet | Explicit unsupported-format regression | Unavailable |
| Java mod Build/Test actions | Not available yet | Disabled-control regressions; native `.hnmod` smoke is unrelated | Unavailable |
| Modpack Play | Not available yet | Permanently disabled with unverified-playability reason | Unavailable |

Evidence includes
`test_actual_works_with_missing_dependency_stays_unsupported`,
`test_actual_false_positive_works_is_rendered_as_unsupported_with_full_evidence`,
`test_real_data_folder_uses_engine_setting_starts_disabled_and_backs_up`,
`test_curseforge_modlist_cannot_silently_remove_manifest_only_entries`,
`test_correct_sha1_cannot_hide_a_conflicting_known_sha512`, and
`test_partial_port_has_data_outputs_but_play_remains_disabled`.
The [Step 1](java-mods-step1.md), [Step 2](java-mods-step2.md) and
[Step 3](java-mods-step3.md) reports contain more test names and observed output.
The [Step 4 readiness report](java-mods-release-readiness.md) records the earlier
assessment. Use the [Phase 5A report](java-mods-step5a.md) for packaging changes,
current verification totals and remaining native verification requirements.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Missing backend | Source mode needs a trusted matching executable. New packaging includes the helper: clear obsolete overrides or reinstall a verified package. Do not select a source folder or JAR. |
| `works` alongside Unsupported | Read the conservative findings; static backend verdicts can omit missing dependencies or unreadable classes. |
| Missing dependencies/files | Select your own folder or instance, rerun analysis, and review version/hash failures. CurseForge ID-only inputs may need instance metadata. |
| Hash mismatch | Preserve the source, obtain the correct file through your authorised source, and import/reanalyse it. Do not edit the expected hash to force a pass. |
| Unknown licence or restricted-licence gate | Review the actual licence and your rights; acknowledgement alone grants no permission. |
| Malformed JSON, nonzero exit or timeout | Use View errors and export the retained evidence. The CLI has an explicit positive `--timeout`; no failed process is treated as compatibility success. |
| Source/output/installed tree changed | Keep your edits and receipts for review. Reimport clean inputs; the library refuses to overwrite modified content. |
| Standalone port requires dependencies | Use the actual Modpacks pack/instance workflow; a standalone check cannot establish ensemble carry. |
| Build, Test or Play disabled | These actions are not available yet; static carry-over cannot enable them. |
| New pages absent from an older download | Use the feature-branch source workflow; no newly verified distributable containing these pages/helper is claimed. |

Long work runs in a worker. **Discard analysis** on Java Mods waits for the
current tool call/timeout and discards its result before recording; it does not
kill a process. It becomes unavailable once recording begins. Import, managed
mutations and pack carry are not forcibly interrupted. None of these workflows
constitutes real native-platform or Minecraft gameplay verification.
