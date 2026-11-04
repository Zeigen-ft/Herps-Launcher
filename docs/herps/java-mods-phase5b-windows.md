# Phase 5B: Windows native verification

Updated: **2026-11-04, Asia/Singapore**. Repository:
`Zeigen-ft/Herspers-Minecraft`. Branch: `feature/herps-java-compatibility`.
Phase 5A implementation: `187541a15c4f040880d896e050ce1f47e0a9e77b`.

The feature branch was pushed with explicit user approval and the existing
**Build Herps Launcher** workflow was dispatched for **Windows x64 only**.
The first Windows run built port-pack successfully but failed two Python
harness cases before game/package/installation stages. Two test-only
corrections were pushed and the second Windows run **completed successfully**
at `ef7e79c67313baf38ca2b2eee36ebd63f276365a`. It built the native helper and game,
created the launcher ZIP and installer, installed the launcher, executed its
seven-page offscreen GUI/bundled-helper smoke, uninstalled it, and passed the
owned native-mod build/selection/rollback smoke. Full log and artifact downloads
remain blocked by the cloud environment's network policy; final per-test totals
and artifact contents are therefore unverified. Phase 5C was not started.

## Guidance, branch and authorization

`AGENTS.md` and `CLAUDE.md` are absent from the checkout and applicable root
ancestors; neither filename is tracked. The Step 0 audit, Step 1–3 reports,
Step 4 readiness report and [Phase 5A report](java-mods-step5a.md) were read.
The initial Phase 5B preflight at `abea538` recorded a Linux-only local host,
an unpublished feature ref and unavailable API access. Authentication and
repository reads subsequently worked; the user explicitly approved a
non-force feature-only push and a Windows-only dispatch.

Before pushing, the working tree was clean on the requested branch, HEAD was
`abea538f91dfd231a7792b5f8df69cc0bbc1e5f8`, and ancestry checks confirmed both
`abea538` and all Phase 5A changes. Only `feature/herps-java-compatibility` was
pushed; remote verification matched that exact initial commit. The later
harness correction is `ef7e79c67313baf38ca2b2eee36ebd63f276365a` on the same
feature branch. There was no force-push, merge, tag, release or macOS dispatch.
Remote `main` remained `8c35f56ad7e25b8035a8b1cbe57f2fe168e85550` in the saved
ref verification. Final remote checks after the successful run again returned
feature `ef7e79c67313baf38ca2b2eee36ebd63f276365a` and that unchanged `main` hash.
The subsequent report-only commit is local; the Windows-tested remote feature
ref remains `ef7e79c`.

The Actions permissions-settings endpoint returned HTTP 403 during earlier
connection checks. It was not used as a prerequisite for dispatch. Both actual
workflow dispatches succeeded; no permission bypass was attempted.

## Workflow and commands actually used

The existing workflow is `.github/workflows/herps-launcher.yml`, named
**Build Herps Launcher**. Its `platform` input supports `all`, `windows`,
`macos-arm64` and `macos-x64`. Explicit `platform=windows` selects only
`desktop (windows-latest, x86_64, x64)`; macOS build steps are excluded.
The feature ref is outside the automatic push filter, so dispatch was explicit.

The resume used a non-force push of the feature ref, verified remote refs,
and dispatched the existing workflow. Recorded CLI commands are:

```sh
git -c push.followTags=false push --no-follow-tags origin refs/heads/feature/herps-java-compatibility:refs/heads/feature/herps-java-compatibility
git ls-remote --heads origin refs/heads/feature/herps-java-compatibility refs/heads/main
gh workflow run 405128974 --repo Zeigen-ft/Herspers-Minecraft \
  --ref feature/herps-java-compatibility -f platform=windows
gh run watch 41730246430 --repo Zeigen-ft/Herspers-Minecraft --interval 30 --exit-status
gh run view 41730246430 --repo Zeigen-ft/Herspers-Minecraft \
  --json databaseId,headSha,headBranch,event,status,conclusion,jobs,url
gh run watch 41731537780 --repo Zeigen-ft/Herspers-Minecraft --interval 30 --exit-status
```

Native workflow build commands include:

```powershell
python -m pip install -r herps_launcher/requirements.txt
rustup toolchain install 1.95.0 --profile minimal
python tools/ci_run.py herps-tests.log python -m unittest discover -s tests -v
python tools/ci_run.py herps-game-build.log pwsh -NoLogo -NoProfile -File scripts/build_windows.ps1
$sourceRoot = python tools/prepare_upstream.py
python tools/ci_run.py herps-package.log python tools/package_herps.py --game dist/windows-x86_64/Herspers-Minecraft --source "$sourceRoot"
```

The preceding workflow Python step calls `build_port_pack(target())` and
exports `HERPS_TEST_PORT_PACK` for real native integration tests. It builds the
pinned existing Rust crate with `--locked --release`, external target cache and
PE architecture/dependency inspection. Configured output is
`.cache/port-pack-target/x86_64-pc-windows-msvc/release/horizon-port-pack.exe`.
Package output is under `dist/herps/`. The installed executable used by the
successful second run is
`$env:RUNNER_TEMP/Herps-Launcher-Installed/Herps Launcher/Herps Launcher.exe`.
The helper's filename is `horizon-port-pack.exe`, collected into PyInstaller's
bundle; the exact installed helper path/hash is recorded in the smoke receipt,
whose contents could not be downloaded. Run 1 did not produce an installer.

## Run 1: native helper built; Python harness failed

[Run 41730246430](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41730246430),
[Windows job 126245378325](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41730246430/job/126245378325).
The verified `headSha` is `abea538f91dfd231a7792b5f8df69cc0bbc1e5f8` and event
is `workflow_dispatch`. The job ran from `2026-11-03T22:22:39Z` to
`2026-11-03T22:28:14Z` (2026-11-04 morning in Singapore).

| Stage | Actual outcome |
| --- | --- |
| Python setup, pinned Rust installation, launcher dependencies | Passed workflow steps |
| Windows x64 port-pack build/validation | Passed workflow step |
| Complete Python source/Qt/backend suite | **336 discovered: 321 passed, 2 failed, 13 skipped** |
| Windows game build | Skipped after Python failure |
| Launcher ZIP and Inno Setup installer build | Skipped after Python failure |
| Installer, installed EXE/GUI and uninstall | Skipped; not executed |
| Native `.hnmod` compilation/rollback smoke | Skipped after Python failure |
| Evidence upload | Passed; artifact metadata available |

These were real Windows test failures, not Linux results. The retained watcher
output shows the exact failures:

- `test_windows_build_is_locked_pinned_native_static_and_outside_prepared_tree`:
  the assertion compared the same Windows temp location through its long
  `runneradmin` and short `RUNNER~1` aliases. Actual manifest path was resolved;
  the test's expected path was not.
- `test_port_enable_disable_and_backup_preserve_saves_and_original_import`:
  `wait_idle()` exceeded its unchanged 10-second deadline with a worker still
  present (`Background operation did not finish`). Its Qt test loop lacked the
  explicit Python GIL yield already used by Modpacks tests.

The correction resolves the expected manifest/cache paths and retains the
outside-prepared-tree assertion. The Java UI harness now processes Qt events
and calls `time.sleep(0.005)` between passes. It does not lengthen the deadline,
remove assertions or alter production code. Local focused checks using real
Linux port-pack and offscreen Qt passed **15 packaging + 15 Java UI tests**,
with no failures/skips. These local passes do not replace a Windows rerun.

The initial automatic [Portable tooling checks run 41730160464](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41730160464)
at `abea538` passed its Ubuntu job and failed its Windows job on the same
long/short Windows path assertion. Its retained failure annotation reports
**336 tests: 226 passed, 1 failed, 109 skipped**, in 59.755 seconds.
The corrected [Portable tooling checks run 41731482701](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41731482701)
passed at `ef7e79c`, including both Ubuntu `tooling` and Windows
`windows-tooling`. This workflow does not install the full launcher requirements
or build port-pack, so its optional integration skips must not be confused with
the main launcher workflow's native backend/Qt coverage. Exact corrected-run
totals were not downloaded.

The exact 13 Windows skip reasons require full test-log collection; the watcher
summary establishes the count, not every individual skipped case. Exact runner
OS/image version and resolved Python patch version also require full runner
logs. `windows-latest`/x64 and successful configured Python 3.12/Rust 1.95.0
steps are confirmed; no unavailable OS/image detail is invented.

## Run 2: corrected harness, Windows only

[Run 41731537780](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41731537780),
[Windows job 126249878859](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41731537780/job/126249878859).
API-confirmed tested commit:
`ef7e79c67313baf38ca2b2eee36ebd63f276365a`.

The run and its single Windows job both finished with `conclusion=success`.
Job duration was **45m57s**, from `2026-11-03T22:31:33Z` to
`2026-11-03T23:17:30Z` (2026-11-04 06:31:33–07:17:30 Asia/Singapore).
Runner name: `GitHub Actions 1000000126`, label `windows-latest`, configured
architecture `x86_64` with x64 Python. The exact Windows OS/image version and
Python patch version remain unavailable without the runner log. Python 3.12,
Rust 1.95.0 and launcher dependency setup steps succeeded. Native MSVC builds
succeeded; exact native build-tool versions were not retrieved.

Final API output from `gh run view`:

```json
{
  "conclusion": "success",
  "headSha": "ef7e79c67313baf38ca2b2eee36ebd63f276365a",
  "status": "completed",
  "url": "https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41731537780"
}
```

The saved final job metadata confirms these completed stages:

| Stage | Observed result | UTC interval, 2026-11-03 |
| --- | --- | --- |
| Native Windows x64 port-pack build/validation | Passed | 22:32:20–22:34:39 |
| Full Windows source Python/Qt/backend test step | Passed; exact final totals await log collection | 22:34:39–22:35:32 |
| Native Windows game build | Passed | 22:35:32–22:57:11 |
| Launcher packaging, packaged smoke and Inno Setup creation | Passed | 22:57:11–22:59:12 |
| Actual installation, installed EXE smoke, shortcuts and uninstall | Passed | 22:59:12–22:59:29 |
| Owned native `.hnmod` compilation, selection and rollback | Passed | 22:59:29–23:15:10 |
| Versioned package artifact upload | Passed | 23:15:10–23:15:20 |
| Packaging/backend evidence upload | Passed | 23:15:20–23:15:23 |

These correspond to 2026-11-04 morning in Singapore. The successful installed
step actually ran the Inno Setup installer, launched `Herps Launcher.exe` with
`--smoke-test --require-installation --require-port-pack`, required seven pages
and bundled-helper fixture evidence, checked shortcuts, and executed the
uninstaller. This is actual Windows installed-EXE execution in offscreen Qt
mode, separately from build success. It does not cover the entire installed
Java Mods/Modpacks acceptance matrix or gameplay. JSON receipts and full logs
remain subject to the download limitation below.

The installed smoke exercises locally generated Fabric fixtures through the
bundled executable: data-only `works` remains `Requires porting`, and `works`
with a missing dependency remains `Unsupported`. It opens Home, Mods,
Java Mods, Modpacks, Shaders, Multiplayer and Settings. This confirms those
pages can be constructed and navigated in the installed frozen application;
it does not establish every interactive operation on each page.

The native-mod smoke builds an owned `.hnmod`, checks its native marker/static
PE/stack requirements, selects the rebuilt client, restores the original
selection, and verifies a save sentinel, clean binary and source cache are
preserved. It does not launch Minecraft or execute the native hook.

| Test/check set | Passed | Failed | Skipped / unverified |
| --- | --- | --- | --- |
| First Windows Python run | 321 | 2 | 13 skipped; exact reasons not retrieved |
| Corrected Windows Python/Qt/backend run | Suite step passed | No suite failure | Exact passed/skipped totals and individual test logs unavailable |
| Corrected Windows workflow | 1 job, 18 successful steps | 0 jobs/steps | 4 macOS-only steps correctly skipped; no macOS job |
| Focused Linux harness rerun | 30 tests | 0 | 0 skipped |
| Initial automatic Portable Windows job at `abea538` | 226 tests | 1 | 109 skipped; same path-alias assertion |
| Automatic Portable tooling checks at `ef7e79c` | 2 jobs | 0 jobs | Per-test totals/skips unavailable |
| Port-pack library and standalone host Rust suites on Windows | Unverified | No result | Not explicitly run by this workflow |

Successful Windows suite status is not a substitute for unavailable per-test
counts. In particular, the first run's 13 skips are not assumed to be the second
run's skip count. Final check annotations contain one Node.js 20 action-runtime
deprecation warning and no error annotations; it did not fail the run.

## Evidence availability and network limitation

Local evidence is under `.cache/java-mods-phase5b-windows/resume/`:
`evidence.json`, `run-41730246430.json`, `run-watch.log`,
`artifacts-41730246430.json`, `annotations-41730246430.json`,
`portable-run-41730160464.json`, `annotations-126245072742.json`,
`portable-run-41731482701.json`, `run-watch-41731537780.log`,
`run-41731537780.json`, `job-126249878859.json`,
`annotations-41731537780.json`, `artifacts-41731537780.json`,
`linux-packaging-harness-fixes.log` and `linux-java-ui-harness-fixes.log`.
The saved watcher contains the first run's failed-test traces and exact summary.
Run 1's uploaded evidence artifact is
`Herps-Launcher-evidence-Windows-x86_64`, ID **13276382053**, **10015 bytes**.
Its presence/size are API metadata; contents were not downloaded successfully.

The successful run uploaded these two artifacts, both unexpired when inspected:

| Artifact | ID | Bytes | Evidence level |
| --- | --- | --- | --- |
| `Herps-Launcher-0.1.0-Windows-x86_64` | 13280171178 | 234645738 | Upload succeeded; API metadata retained |
| `Herps-Launcher-evidence-Windows-x86_64` | 13280295995 | 60585 | Upload succeeded; API metadata retained |

GitHub reports package archive SHA-256
`ae8c71a7955891929db29ad58ce8417f6f0acb6b144320b71f43c9fcc2e31be4`
and evidence archive SHA-256
`a515fe86d9f44e6cca52a25b43b8123982af9a5c9197ab7447bf63f5a48a887b`.
These are server-reported digests, not locally verified file hashes. The workflow
uploads the ZIP/Setup EXE/native proof separately from build/test logs and
package/installed-smoke receipts. Archive members were not inspected locally.

Full log/artifact download redirects were blocked because the selected
network allowlist lacked `results-receiver.actions.githubusercontent.com` and
`productionresultssa0.blob.core.windows.net`. A supported environment draft
adds only those two hosts while preserving all four current allowed hosts.
Saving that draft does **not** apply it: user review, save and publish remain
required. No direct-route, alternate-host or permissions bypass was attempted.
Partial status/watcher output is retained and clearly separated from unavailable
full logs and artifact contents. A final completed-run log download returned
`failed to get run log: Get "https://results-receiver.actions.githubusercontent.com/[redacted]": Forbidden`.
The evidence download also returned `Forbidden` at the blob host above.
This is a cloud network restriction on redirected downloads, not a failed
workflow dispatch or a reason to change GitHub repository permissions. The
draft has not taken effect. Until it is reviewed/saved/published in environment
settings, full logs, artifact contents, exact final test counts and individual
skip reasons remain uncollected. No native screenshots were captured.

## Verification boundaries and remaining work

Build success, package generation, installation and actual installed EXE
execution are separate claims. Existing packaged/installed smoke opens all
seven pages, checks game installation discovery, and executes two owned Fabric
metadata fixtures through the bundled helper. Its success establishes that
limited installed smoke; the full frozen GUI acceptance matrix remains open.

Java Mods and Modpacks source integration covers imports, conservative results,
dependencies, mixins, unreadable classes, version/hash failures, local resolution,
data carry, coverage/export and preservation cases. The complete Windows source
suite step passed, but individual case/skip logs could not be collected. Full installed
Java/pack GUI import/resolution/export/backup, persistent profiles/settings,
no-Rust environment validation and save-preserving uninstall remain unverified.
The installed launcher used its bundled helper, and frozen discovery excludes
Cargo/PATH fallbacks by default, but the CI machine itself had Rust installed.
The native-mod save sentinel verifies rebuild/rollback preservation only; the
installer/uninstaller did not test existing profiles or saves with sentinels.

The workflow builds port-pack but does not explicitly execute its 99 Rust
library tests or the standalone host's 17 tests. Existing Python wrappers run
Windows-launcher and Bedrock Rust unit targets; their exact native test totals
and any skips remain unverified without the Windows log. Historical Linux Rust
passes are not relabelled native.
Minecraft gameplay, original Java behavior, GPU shader rendering and live
Tailscale multiplayer remain unverified. Native rebuild proof itself leaves
`hook_execution_verified` and `gameplay_verified` false.

Java bytecode execution/bridge, universal conversion and packwiz remain
unavailable. Java Build/Test and Modpack Play stay disabled. Static `works`
cannot become Native compatibility or Tested successfully without the required
evidence. Imported Java code was not executed during metadata analysis.
No third-party JARs, Minecraft assets, local ports or credentials were added.

## Changed files and stop point

- `tests/test_herps_packaging.py`: canonical path comparisons in the test harness.
- `tests/test_javamods_ui.py`: explicit worker GIL yield in the test wait loop.
- `docs/herps/java-mods-phase5b-windows.md`: this evidence report.

Final local documentation checks passed: relative links exist, no draft
placeholders remain, run/step totals and artifact metadata/digests match the
saved API responses, required commits are ancestors of the feature branch,
and `git diff --check` reports no whitespace errors.

Production launcher/backend, packaging and workflow behavior remain unchanged.
The feature branch alone was pushed as authorized. No merge, tag, release,
macOS build or Phase 5C work was performed. The final report is committed
separately; its commit hash is provided in the handoff. Stop after Phase 5B
and await approval for Phase 5C.
