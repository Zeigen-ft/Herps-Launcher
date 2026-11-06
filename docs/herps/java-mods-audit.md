# Herps Launcher Java mods and modpacks: Step 0 audit

Audit date: 2026-11-03. **Audit only; no application or packaging changes.**

## Scope, repository, and provenance

- Repository: `https://github.com/Zeigen-ft/Herspers-Minecraft`.
- Base: `feature/herps-launcher-cross-platform`, commit
  `5afe89bf9ba7431409beae83afe03913178953fc`.
- Audit branch: `feature/herps-java-compatibility`, created from that existing
  launcher branch. No merge into `main` and no remote push was performed.
- The originally attached `/workspace/Herps-Launcher` checkout contains only an
  MIT `LICENSE` at `bbc4b1927f73048feb0de92a563caa0c89dffe67`; it does not contain
  the launcher. This audit uses the repository expressly named in the supplied
  instructions, cloned to `/workspace/Herspers-Minecraft`.
- No `AGENTS.md` or `CLAUDE.md` exists in the launcher checkout outside generated
  caches. The pinned upstream has its own instructions, read during its audit.
- Engine sources are not vendored at the repository root. `upstream.lock.json`
  pins `Vasysik/horizon-android` commit
  `7301f6fdd7f470b11317276e7a11b4dc615c137a`, Rust **1.95.0**, Horizon **0.7.6**,
  Minecraft Java **26.3**, and JDK **25** for existing resource preparation.
  `python3 tools/prepare_upstream.py` verified the archive SHA-256 and exact
  before/after patch hashes before staging the engine in ignored
  `.cache/herspers-upstream/<commit>-<patch-fingerprint>/`. The fetched original
  remains under `.cache/upstream/<commit>/`.

References below use paths relative to this repository. References prefixed
`ENGINE/` mean that checksum-prepared engine directory, not new vendored files.
Local logs and fixtures mentioned below are ignored validation artifacts and
are not part of the audit commit. No third-party mod JARs, game assets, prepared
Minecraft resources, or generated ports are committed.

## A. Existing launcher architecture

### GUI and navigation

The application uses Python 3.12 and **PySide6 Qt Widgets**, pinned in
`herps_launcher/requirements.txt` (PySide6 Essentials/shiboken6 6.8.3).
`herps_launcher/__main__.py` calls `app.main()`. `app.py:531` constructs the
`QApplication`, applies the stylesheet, creates `Launcher`, acquires the
single-window `QLockFile`, and starts the event loop. The packaged entry point is
`packaging/herps_entry.py`; it also supports an actual offscreen page smoke test.

`Window` hardcodes **Home, Mods, Shaders, Multiplayer, Settings** and registers
their pages in that order (`app.py:75`, `:106`, `:132`). Navigation uses a
`QStackedWidget`. There is no Java Mods or Modpacks page. Future page additions
must update the five-page expectations in tests, `tools/package_herps.py`, and
`.github/workflows/herps-launcher.yml` when authorized; the smoke entry point
currently iterates the actual navigation buttons.

### Mods

`app.py:209` provides import, enable/disable, remove-to-backup, native rebuild,
rollback, metadata/capability details, and build output. Its file dialog accepts
`.hmod` and `.hnmod` only (`:248`). `core.py:136` explicitly rejects Java `.jar`
files rather than treating them as runnable Horizon mods.

- Runtime/content `.hmod`: manifest and WASM validation, supported API/side and
  capability details (`core.py:147`).
- Native-source `.hnmod`: exact game/Horizon/mixin revision validation and an
  explicit trust decision before enabling or building (`core.py:159`,
  `app.py:260`). These builds execute source/build scripts; they must remain
  separate from passive Java analysis.
- Profile-local storage is `horizon-mods/` and `horizon-native-mods/`. Duplicate
  IDs are refused, imported mods start disabled, and enable state is stored as
  `mod.<id>:true/false` in `horizon-mods.txt` (`core.py:325`).
- Removal disables a package, checks containment, and moves it to
  `<launcher state>/removed/<uuid>-<name>`; mod data is preserved (`core.py:350`).

### Shaders

`app.py:291` imports `.zip`/`.hshader`, selects a pack, restores defaults, and
opens the profile folder. `core.py:359` uses bounded archive inspection, requires
`horizon-shaders.toml` or `shaders/` content, and stores packs in profile-local
`shaderpacks/`. Selection writes the actual upstream `pickedShaderPack` key in
`horizon-graphics.txt`. Import/selection does not prove successful GPU rendering.

### Settings, profiles, and paths

`Launcher` stores `settings.json` under `<support>/herps-launcher/`
(`core.py:251`). Atomic writes use a temporary file, `fsync`, and `os.replace`,
refusing destination symlinks (`:33`). Pair-file updates preserve unknown keys
and make a one-time `.herps-backup` (`:61`). Settings expose the installation,
prepared native source, resolution/distance/backend, and data/log locations
(`app.py:397`).

The default profile reuses `<support>/game`; additional profiles use
`<support>/herps-launcher/profiles/<id>` (`core.py:306`). IDs are restricted to
1–64 lowercase letters, digits, or underscores. Creating a profile does not move
or delete existing saves. Switching is blocked while a game or worker is active
(`app.py:187`). New Java workspaces should derive from `Launcher.game` rather
than introduce independent platform path rules.

`pathlib` and `support_dir()` (`core.py:73`) implement Windows
`%LOCALAPPDATA%/Herspers Minecraft`, macOS
`~/Library/Application Support/Herspers Minecraft`, and a Linux development
fallback. `target()` supports Windows x64 MSVC, macOS ARM64, and macOS Intel;
Linux is not a supported packaged game target (`:84`). `Installation.inspect()`
maps `.app` Contents paths and Windows package/bin paths, checks platform and
architecture, and validates available binary hashes (`:188`).

### Background work, subprocesses, errors, and logs

- `Worker(QThread)` has progress/completion/failure signals and catches
  exceptions (`app.py:41`). `start_work()` checks idle state, disables Play,
  connects build output, and refreshes after completion (`:137`). An 800 ms timer
  polls the game process (`:510`).
- Resource checks capture stdout/stderr with a 120 s timeout; game `Popen` uses
  an argument list, explicit working directory/environment, and a timestamped
  combined log (`core.py:409`, `:432`). Native builds stream decoded output to
  `native-build.log` and the GUI, raising on nonzero exit (`:560`). Tailscale
  status captures JSON/stderr with an 8 s timeout (`:220`).
- `operation.lock` serializes launch/native-build operations (`core.py:293`);
  it does not lock every backend mutation. GUI idle guards separately constrain
  user mutations, and `window.lock` prevents duplicate windows. Exceptions reach Qt warning dialogs
  or the status bar. Pending-session JSON and recent activity preserve exit
  results (`core.py:429`).
- These subprocess helpers are operation-specific. There is no generic typed
  port-pack adapter, artifact schema validator, cancellation contract, or
  port-pack executable setting/discovery helper.
- Existing archive validation bounds entry count and expanded bytes and rejects
  traversal, links, case-colliding names, and Windows-reserved paths
  (`core.py:99`). It is reusable subject to the size/streaming needs of Java
  archives and larger modpacks.

## B. Horizon Port Pack CLI

There is **no root `crates/horizon-port-pack/`** in this launcher repository.
The actual crate exists at `ENGINE/crates/horizon-port-pack/`. Its Cargo package
and automatic binary name are both **`horizon-port-pack`**, version **0.1.0**.
The package declares minimum Rust 1.86; this repository pins and was tested with
1.95.0. The actual executable was built, not inferred from documentation.

`ENGINE/crates/horizon-port-pack/src/main.rs:41` implements a manual parser with
these eight commands:

```text
horizon-port-pack import <pack> <work>
horizon-port-pack inventory <work> [--offline]
horizon-port-pack fetch <work> [--from <folder>] [<mod id>...]
horizon-port-pack carry <work> [--resources <prepared>] [<mod id>...]
horizon-port-pack check <jar> <out>
horizon-port-pack report <work>
horizon-port-pack port <pack> <work> [--from <folder>] [--resources <prepared>]
horizon-port-pack upgrade-datapack <pack> (<out> | --world <world>)
```

**Measured `--help`: exit 1, empty stdout, usage prefixed with `error:` on
stderr.** Each subcommand with missing arguments behaves the same way. There is
no implemented `--help`, per-command help, `--version`, or `--json` protocol.
`--from`, `--resources`, `--world`, and `--offline` are removed globally before
dispatch; unknown flags are not consistently rejected. An adapter must construct
known argument lists rather than pass arbitrary options through.

| Command | Required inputs | Actual outputs and side effects |
| --- | --- | --- |
| `import` | Pack source and writable work directory | Writes `pack.json`; stages embedded resource packs and resource-pack report. Reads Modrinth `.mrpack`, CurseForge ZIP, Prism/MultiMC/plain instance folders, and Crash Assistant JSON. No implemented packwiz parser. |
| `inventory` | `<work>/pack.json`; optionally cached Modrinth metadata and local JARs | Writes `inventory.json` and `inventory.csv`; normally queries Modrinth and writes `modrinth.json`. `--offline` skips that metadata query. |
| `fetch` | `pack.json`, `inventory.json`; optional user folder/IDs | Writes `fetch.json` and JARs under `jars/`. Defaults to portable content/data records; named IDs override selection. Local folder lookup can fall back to downloads. |
| `carry` | `inventory.json` with JAR/info records; optional oracle facts/resources/IDs | Writes `mods/<key>/carry/`, `carry-report.json`, and `outside/`. Defaults to all content-classified records, not exactly fetch's portable subset. |
| `check` | JAR and writable output directory | Performs data carry-over into `carry/`, normally writes `carry-report.json`/`outside/`, and writes `check.json`. It is not a read-only analysis command. |
| `report` | `pack.json`, `inventory.json`; reads carry reports and optional harness results | Writes `coverage.json` and `coverage.md`. Does not run a gameplay test. |
| `port` | Pack source/work directory; optional local JAR folder/prepared resources | Import → inventory → resource-pack fetch → portable JAR fetch → offline inventory → data carry → report. May fetch loader JARs. Valid-path execution was not attempted. |
| `upgrade-datapack` | Existing pack ZIP/folder and output directory or world | Rewrites supported 26.2 datapack/worldgen formats for 26.3. Not general Java mod conversion; inspected only. |

There is no special required process cwd once built. Relative inputs and stored
instance paths resolve against cwd, so the adapter should normalize inputs to
absolute paths. Fixture commands ran from
`/workspace/Herspers-Minecraft/.cache/java-mods-audit`, with absolute binary,
input, and output paths. Work/output directories must be writable and isolated
per profile/import; engine/app directories must not be used as mutable workspaces.

`--resources` means **prepared Horizon game resources**, not engine source.
`facts.json` provides vanilla block defaults; `items.json` can constrain oracle
items. Missing files can be logged and ignored, leaving constraints unenforced
(`pipeline.rs:92`). Optional `oracle/facts.json` is a separate input.

**`--offline` is not a complete network-disable switch.** It controls initial
inventory in `port`, whose later resource-pack/mod-JAR/loader fetch can still network.
`fetch --from` is also not local-only. The successful fixture fetch used an
already-present synthetic JAR and an empty instance loader: 0 downloads, 0
copies, 1 present. Do not generalize that result to a safe local-only fetch API.
The optional NeoForge oracle and mod-port harness execute original Java mods;
they were not run and must not be wired into the requested passive analysis.

Stdout is human progress/summary text, stderr is an `error: ...` string, and
success/failure normally use 0/1. Compatibility is a separate result: a negative
`check` verdict also returns 0. `fetch` can return 0 while individual files
failed, and `carry` can log per-mod errors and continue. Validate each artifact
and record; process success is insufficient.

## C. Actual JSON artifacts

The following are the actual pinned Rust serialization contracts, checked
against generated fixture outputs. They are **files**, not JSON stdout. None
has a schema-version discriminator or a structured error envelope. `?` below
denotes a field that can be omitted; it is descriptive type notation, not JSON.

### `check.json`

`check.rs:34` serializes all these fields (none optional):

```text
mod_id, name, version, loader, license, verdict, summary: string
ports, skipped, depends, namespaces: string[]
code: {
  classes: nonnegative integer,
  features: object<string, nonnegative integer>,
  events: string[],
  examples: object<string, string[]>
}
```

`verdict` is `works | partly | no`, displayed by the CLI as Works, Partly,
Doesn't run. `loader` is `neoforge | forge | fabric | quilt | ""`; detecting
Quilt's filename does not establish full Quilt metadata support. Empty strings,
arrays and maps are valid. Feature names declared in `classes.rs:150` are
`block-behaviour`, `block-shape`, `item-behaviour`, `block-entity`, `menu`,
`entity`, `screen`, `renderer`, `worldgen`, `recipe`, `effect`, `enchantment`,
`particle`, `command`, `network`, `events`, `mixin`, `unread`.

There is no Minecraft version/range, dependency version constraint, detailed
access widener/transformer metadata, validation-error list, build outcome or
runtime test result. `classes.rs` passively parses class headers, constant pools,
superclasses/interfaces and declared method names. It skips method attributes
(including `Code`), does not inspect opcodes, and skips rather than validates
the class-file version. It does not execute or decompile Java. Its census
silently drops parse failures via `filter_map(parse)`
(`classes.rs:355`). The `unread` enum does not guarantee that invalid bytes are
reported.

Exact observed Fabric fixture `check.json`:

```json
{
  "mod_id": "fabricprobe",
  "name": "Fabric probe",
  "version": "1",
  "loader": "fabric",
  "license": "MIT",
  "verdict": "works",
  "summary": "Content only: 1 recipe port.",
  "ports": ["1 recipe"],
  "skipped": [],
  "depends": ["missinglib"],
  "namespaces": ["fabricprobe"],
  "code": {"classes": 0, "features": {}, "events": [], "examples": {}}
}
```

That JAR deliberately contained an invalid `.class`, a mixin declaration, an
access widener, and an absent required dependency. Its independent inventory
census counted **one class file and one mixin config**, and `missing` contained
`missinglib`. Thus `works` and empty `skipped` do not establish complete analysis
or compatibility. The fixture's Minecraft/loader version constraints and
Fabric API dependency were not preserved by `check`.

### `inventory.json`

Top-level **array of records**, not an object (`inventory.rs:16`):

```text
key, name, version, path, class, tier, confidence, source, license, client, server: string
depends: string[]                 # dependency IDs that are inside the pack
layer: nonnegative integer
categories?: string[]             # omitted when empty
missing?: string[]                # absent required dependency IDs; omitted when empty
jar?: string                     # path; omitted for None
info?: {
  mod_id, name, version, license: string,
  depends: string[],
  census: {
    blockstates, item_models, recipes, loot_tables, tags, worldgen, structures,
    languages, textures, sounds, classes, mixin_configs: nonnegative integer
  }
}
```

`jar` and `info` may be absent independently: a present but unreadable JAR may
retain its path without metadata. Inventory suppresses metadata-reader errors
with `jar::read(j).ok()`. Documented confidence values are `known`, `sides`,
`categories`, `jar`, `kind`, `guess`, `unknown`; sources are `modrinth`,
`curseforge`, `file`. Class/tier remain string fields, not serialized enums.

The observed Ruby/Fabric records both had `missing: ["missinglib"]` but
`depends: []`, because that dependency was outside the pack. Their nested
`info.depends` retained the missing ID. Another probe with an absent JAR returned
0 and an unknown/none/unknown classification; `categories`, `missing`, `jar`,
and `info` were all omitted. An omitted `missing` must not be mistaken for a
complete successful dependency analysis when JAR metadata is unavailable.

### `coverage.json` / `coverage.md`

`report.rs:39` writes a top-level **array of rows**, all fields present:

```text
key, name, class, tier, license, license_kind, status, reason: string
```

Status values are `ported | partial | not-yet | not-needed`; license families
include `permissive`, `copyleft`, `all-rights-reserved`, `restricted`, `custom`,
`unknown`. There is no mod version, dependency/missing list, source, timestamp,
or overall playable-status field. Join inventory and check data rather than
export only these rows. Classification-based `not-needed` for libraries or
performance mods does not prove equivalent replacement of their behavior.

Exact observed carried Ruby row:

```json
{
  "key": "ruby",
  "name": "Ruby audit fixture",
  "class": "content",
  "tier": "data",
  "license": "MIT",
  "license_kind": "permissive",
  "status": "partial",
  "reason": "1 blocks, 1 items; harness not run"
}
```

The missing dependency was not included in that row/reason. The Fabric row was
`not-yet`, tier `none`, class `unknown`. Totals: **0 ported, 1 partial, 1
not-yet, 0 not-needed**. These rows are not the launcher's requested status enum
and must not be relabeled as tested native gameplay success.

### Other artifacts and measured failures

`fetch.json` contains `files`, an array of `{key: string, file: string,
how: string, detail?: string}`. `how` is `present | downloaded | local |
needs-key | not-found | failed`; empty detail is omitted. Import writes
`pack.json`, including pack identity/format/Minecraft/loader strings, indexed
files, and override counts; its instance fixture had empty version/loader
strings. These inputs are necessary for inventory/report even when the tool
does not complain about an empty version.

| Probe | Exit | Actual outcome |
| --- | --- | --- |
| NeoForge fixture with one block/item/recipe and required `missinglib` | 0 | `verdict: works`, `depends: ["missinglib"]`, `skipped: []`; carry used nearest vanilla block templates. |
| Fabric fixture described above | 0 | `works` despite invalid class, mixin/access-widener declaration and missing dependency. |
| Empty Fabric metadata-only JAR | 0 | `verdict: no`; "Nothing to port: it has no blocks, items, recipes or worldgen." |
| Local instance import → offline inventory → already-present fetch → carry → report | 0 each | One content mod carried; coverage remains partial/not-yet. No Java runtime harness was run. |
| Missing JAR | 1 | `error: <path>: No such file or directory (os error 2)` on this Linux host. |
| Invalid ZIP | 1 | `error: <path>: invalid Zip archive: Could not find EOCD`. |
| Report in absent work directory | 1 | Error opening `<work>/pack.json`. |
| `{}` pack JSON | 1 | Missing required `name` field, with JSON line/column. |
| Inventory object instead of array, with valid pack input | 1 | `invalid type: map, expected a sequence at line 1 column 0`. |
| Inventory of absent JAR | 0 | Unknown record with no JAR metadata, not an analysis success. |

Errors are not JSON and OS-specific wording varies. After a failed operation,
outputs may be absent or leftover; use fresh workspaces and verify provenance
instead of parsing stale artifacts as the latest successful result.

## D. Windows and macOS packaging

`tools/package_herps.py` currently accepts `--game`, optional `--source`, and
`--output`. It builds only `herps-host` with Rust 1.95.0 and passes that helper
through PyInstaller `--add-binary` (`:43`). **It does not build, copy, discover,
or verify `horizon-port-pack`.** Native game scripts build the client, ctl, and
preparer, not port-pack.

| Native runner | Rust target | Required future tool artifact |
| --- | --- | --- |
| Windows x64 | `x86_64-pc-windows-msvc` | `horizon-port-pack.exe` |
| macOS ARM64 | `aarch64-apple-darwin` | `horizon-port-pack` |
| macOS Intel | `x86_64-apple-darwin` | `horizon-port-pack` |

Windows delivery places the game inside
`Herps Launcher/game/Herspers-Minecraft`; optional prepared source is in
`Herps Launcher/engine-source`. ZIP output is wrapped by an Inno Setup installer
that recursively copies the payload (`packaging/herps-windows.iss:24`). macOS
ships sibling `Herps Launcher.app` and `Herspers Minecraft.app` plus optional
sibling `engine-source` in a DMG. Qt requires macOS 12+ even though the engine
script's deployment target is 11. Optional Developer ID and notarytool profile
support exists; the currently generated metadata still records
`gameplay_verified: false` and `notarized: false`.

When separately authorized, reuse the existing native CI runners, pinned Rust,
and Cargo lock to build the tool for each target; validate architecture/runtime
dependencies and checksum, then add it via PyInstaller's existing binary
mechanism. A single resource locator must cover source mode and frozen Qt
applications (including PyInstaller's resource directory); current code has no
`sys._MEIPASS` port-pack lookup. Run the tool with writable per-profile working
directories, never inside signed application resources. Preserve executable bits
and include the helper before final macOS signing/notarization. Verify the actual
CLI usage/fixture artifacts in the installed package, including paths with
spaces and missing/wrong-architecture executable cases. `--help` success must
not be assumed without checking this tool's exit behavior.

No packaging changes or Windows/macOS builds were made in Step 0. Linux tests
cannot establish native installer, DMG, signing, or ABI compatibility.

### Existing native build/test backend is not Java conversion

`core.py:510` provides a real trusted `.hnmod` rebuild: exact source/tree/patch
validation, pinned `horizon-mixins`, separate staging, dependency-lock checks,
engine compilation, declared post-build commands, and checksum receipts. It
executes trusted native source; do not call it while inspecting imported JARs.

`tools/smoke_herps_native.py:61` is **Windows-only**. It generates an owned
`.hnmod`, compiles a native client, checks an injected binary marker, verifies
selection/rollback, and preserves save/source/original-binary sentinels. It needs
a real game package, matching prepared source, and a private target cache. Its
report explicitly leaves `hook_execution_verified` and `gameplay_verified`
false (`:109`). It neither imports nor tests a Java mod. It is unsuitable as
evidence for a Java **Build Mod**, **Test Mod**, or **Tested successfully** action.
Mac native compilation and live two-computer Tailscale play remain unverified in
the existing launcher documentation as well as this audit.

## E. Gaps and recommended Step 1

### Reuse and preserve

Reuse the existing Rust tools instead of rebuilding their functionality in
Python. Reuse `Launcher.game`, config/state and atomic writes, SHA-256 helpers,
archive path checks, Qt workers/signals and details/log patterns, and native
rollback/preservation patterns where appropriate. Keep `.hmod`/`.hnmod`, shaders,
profiles/saves, multiplayer and launching behavior intact. Do not route JARs
through current native-mod trust/build code.

Missing GUI/backend interfaces include Java Mods and Modpacks navigation,
Fabric/Forge/NeoForge details, typed subprocess/artifact handling, per-profile
Java import/port records, dependency resolution with retained hash evidence,
licence review, JSON/text report export, and explicit missing-binary/malformed
output handling. There is no working Java bridge. No launcher CLI commands
`check`, `analyze-pack`, `port`, or `export-report` exist. Java/pack-specific
launcher tests and native packaged port-pack tests do not exist.

### Confirmed backend limitations

- Reusable passive metadata/census, pack import, dependency-layer classification,
  data carry and coverage/licence reporting exist **in the pinned Rust crate**;
  the launcher has not integrated them. Preserve that reuse while addressing
  their incomplete diagnostics.
- Dependency IDs are available but constraints are discarded (`jar.rs:111`),
  and Fabric dependency names beginning with `fabric` are broadly filtered.
  Missing dependencies need independent retention and user-file resolution.
- Local fetch verifies SHA-1 when supplied during lookup, otherwise may match
  filenames/instance mappings. Existing `record.jar` paths short-circuit that
  hash recheck (`fetch.rs:132`). Independently verify known hashes before
  displaying "verified"; file presence is insufficient.
- Static `works` can coexist with missing dependencies, ignored class errors,
  mixins, and access wideners. Detect incomplete analysis and join evidence
  across artifacts. There is no basis for universal conversion, native Java
  bytecode execution, or a Java bridge.
- Carry output is a **local folder content mod**, not a converted `.hnmod` or
  translated Java gameplay. Vanilla templates can approximate content; full
  behavior, custom rendering, entities/machines/networking and complex mixins
  cannot be inferred as working. Preserve outside/unhandled content evidence.
- Modrinth/CurseForge/instance import exists; **packwiz is not implemented** in
  the pinned importer. CurseForge-only files can require user-provided local
  files; do not add API-key requirements or silently drop them.
- Licence strings/families are recorded, but classification is informational:
  CLI carry/check do not implement an ND/NC pre-port warning/confirmation gate.
  Because even `check` carries content, that policy must be handled before the
  adapter invokes it or before exposing a distinct analysis-only path.
- No portable local-only switch covers the full `port` pipeline. Optional
  oracle/harness tools execute original Java mods and are excluded from passive
  analysis. Their existence is not permission or evidence for Build/Test actions.

### Step 1 plan (recommendation only; approval required)

1. Add new `herps_launcher/javamods/` modules around the verified pinned CLI,
   keeping existing Mods/Shaders code behavior unchanged. Establish a binary
   locator and explicit version/provenance checks; fail clearly when unavailable.
2. Allocate isolated per-profile work directories beneath `Launcher.game`, use
   absolute paths and argument arrays, and capture stdout, stderr, exit status,
   timeouts, and logs. Restrict analysis to passive metadata/class-file reading;
   never run Java bytecode, build scripts, mixins, or a native rebuild implicitly.
3. Parse the actual file artifacts, validate types/required fields, reject stale
   outputs after failures, and retain detailed evidence and original raw
   findings. Do not expect a JSON stdout protocol that does not exist.
4. Gate operations on their audited side effects and local inputs. A nominal
   offline flag is insufficient if a downstream operation can still download
   resource-pack archives, mod JARs, or loader JARs. Add safe local preconditions or report a
   backend gap rather than silently enabling unsafe orchestration.
5. Present only evidence-supported statuses: Native compatibility, Requires
   porting, Unsupported, Build failed, Tested successfully. Unknown maps to
   Unsupported with a specific explanation and an explicit unknown/proven-
   incompatible distinction in report details. Reserve Compatible through Java
   bridge as unavailable. Static heuristic verdicts cannot establish runtime
   compatibility or successful testing.
6. Preserve missing/unresolved dependencies, mixins, unsupported APIs and parse
   failures; retain licence information and warn before no-derivatives or
   non-commercial porting. Keep generated ports local. No restricted automatic
   mod downloads or CurseForge API keys; use user-provided files and hashes.
7. Expose launcher `check`, `analyze-pack`, `port`, and `export-report` commands
   only for genuinely supported behavior. Use locally generated fixture JARs
   and packs (no third-party JAR commits) for subprocess/schema/error, archive,
   isolation, dependency, licence and truthful-status tests. Run all current
   tests and relevant Rust tests; native binary distribution remains a required
   later integration task rather than an assumed installed capability.

Later approved steps should add the Qt Java Mods page, supported pack-import
flows, explicit per-mod and whole-pack limitations, and documentation. packwiz,
Java gameplay conversion/bridges, Build/Test actions and Port and Play must stay
unavailable wherever the audited backend supplies no real implementation.

## F. Validation and verification boundaries

The audit host is Linux x86_64, Python 3.12.14, pinned Rust 1.95.0, with the
unmodified pinned launcher requirements installed in
`/workspace/.herps-audit-venv`. Rust is activated through
`source scripts/cloud-env.sh`. Network checks in the restricted command sandbox
could not reach the proxy; permitted commands outside that sandbox successfully
used the existing HTTPS proxy/authentication. No token or new secret was needed.

### Existing launcher/tooling tests

Working directory: `/workspace/Herspers-Minecraft`.

```sh
source scripts/cloud-env.sh
QT_QPA_PLATFORM=offscreen /workspace/.herps-audit-venv/bin/python tools/ci_run.py \
  .cache/java-mods-audit/python-tests.log \
  /workspace/.herps-audit-venv/bin/python -m unittest discover -s tests -v
```

Result: **159 discovered; 145 passed, 0 failed/errors, 14 skipped**, exit 0.
All **19 launcher core tests and five actual Qt widget tests passed**. The suite
also compiled and ran native launcher Rust tests and exercised the Bedrock
launcher Cargo unit suite; these portable fixture checks are not native Windows
game execution. Existing regression coverage includes profile/save preservation,
mod import/enable/backup and native validation/staging, shader selection/reset,
settings/key preservation, locks, actual owned POSIX child launch/log/exit and
relaunch, Tailscale status UI, address validation, and packaging/source safety.

Skipped separately: 12 Windows stack-repair tests need PowerShell; one
AppleScript compilation test needs macOS; one supplied-APK integration test needs
`HORIZON_TEST_APK`. No failure was converted into a skip. No new tests were
introduced because this step changes documentation only.

Additional checks, exit 0:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=. /workspace/.herps-audit-venv/bin/python \
  packaging/herps_entry.py --smoke-test \
  --smoke-report .cache/java-mods-audit/launcher-smoke.json
# {"status":"passed","pages_opened":5}; source UI only, no required installation
for script in scripts/*.sh packaging/*.command; do bash -n "$script" || exit; done
/workspace/.herps-audit-venv/bin/python -m pip check
```

### Rust and CLI validation

From this repository, with `source scripts/cloud-env.sh` and `ENGINE` set to the
checksum-prepared source path described above:

```sh
cargo +1.95.0 build --locked --manifest-path "$ENGINE/Cargo.toml" -p horizon-port-pack --bin horizon-port-pack
cargo +1.95.0 test --locked --offline --manifest-path "$ENGINE/Cargo.toml" -p horizon-port-pack
```

Both returned 0. **99 library tests passed, 0 failed, 0 ignored**; binary and
documentation targets each ran zero tests, separately from those 99 actual
tests. Build/test logs: `/tmp/herps-port-pack-build.log` and
`/tmp/herps-port-pack-tests.log`. The built executable is
`/workspace/.horizon-target/debug/horizon-port-pack`, a Linux development
executable, not a Windows/macOS deliverable.

The local generator `.cache/java-mods-audit/probe.py` created owned synthetic
NeoForge/Fabric JARs with JSON/TOML, recipes/assets, and deliberately invalid
class bytes; no Java code was compiled or executed. The probe log is
`/tmp/herps-port-pack-probe.log`, with raw results/artifacts under
`.cache/java-mods-audit/`. It exercised successful local import, offline
inventory, already-present local fetch, carry, check and report, as well as
usage/missing/malformed input failures. Additional probes verified a negative
check verdict, an absent inventory JAR, and malformed inventory handling. Exact
outcomes and diagnostic limitations are in sections B/C. Valid-path `port` was
deliberately not run because it can download resource-pack archives, mod JARs,
and loader JARs (it does not prepare proprietary Minecraft game resources);
its behavior was inspected in source. A generated local fixture is not a
third-party compatibility certification.

### Unverified and out of scope

No real Minecraft gameplay, Java-to-native gameplay conversion, working Java
bridge, native hook execution, GPU shader rendering, two-machine multiplayer,
Windows x64/macOS ARM64/macOS Intel runtime/package tests, signing/notarization,
third-party mod compatibility, restricted mod fetching, or full playable modpack
was verified. No authentication, licensing/ownership checks, sign-in, or
proprietary resource-acquisition behavior was changed. No future step is
implemented. **Stop after the audit commit and await approval for Step 1.**
