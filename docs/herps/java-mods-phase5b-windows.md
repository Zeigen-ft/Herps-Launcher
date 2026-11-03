# Phase 5B: Windows native verification — blocked at preflight

Date: 2026-11-03. Repository: `Zeigen-ft/Herspers-Minecraft`.
Branch: `feature/herps-java-compatibility`.
Implementation awaiting verification: `187541a15c4f040880d896e050ce1f47e0a9e77b`.

**No Windows build, installation or runtime verification was performed.**
This report records the actual environment/access checks and the remaining
Windows acceptance work. It is not a completed native-verification report.
Phase 5C was not started. Nothing was pushed, merged, tagged or released, and
no remote workflow was dispatched.

## Guidance and environment

The checkout and its `/workspace`/filesystem-root ancestors contain no
`AGENTS.md` or `CLAUDE.md`; neither filename is tracked in this repository.
The Step 0 audit, Step 1–3 reports, Step 4 release-readiness report and
[Phase 5A report](java-mods-step5a.md) were read before writing this report.

Observed execution environment:

| Item | Observation | Windows verification meaning |
| --- | --- | --- |
| OS | Linux, kernel `6.18.57` | No Windows OS/version available to record |
| Architecture | `x86_64` | Host CPU architecture, not a Windows runner |
| Python | `3.12.14` | Linux interpreter only |
| Rust | `1.95.0`, host `x86_64-unknown-linux-gnu` | Linux toolchain only |
| Installed Rust targets | `x86_64-unknown-linux-gnu` | Windows MSVC target unavailable locally |
| Native Windows tools | `cl`, `link.exe`, `ISCC.exe`, `powershell`, `pwsh` absent from PATH | No local Windows build/installer execution |
| Managed environment capabilities | No attached Windows execution capability reported | No alternate Windows machine available through the current tools |
| Local branch | `feature/herps-java-compatibility`, clean at `187541a` before this report | Prior implementation preserved |

Installing a Windows cross target or using a Linux frozen probe would not
provide native Windows runtime evidence. Neither is substituted for the
requested Windows machine. Launcher dependencies and the helper have prior
Linux evidence in Phase 5A; their Windows installation/build remains unverified.

## Remote branch and Actions access

The initial successful read-only command was:

```sh
git ls-remote --heads origin \
  refs/heads/feature/herps-java-compatibility \
  refs/heads/feature/herps-launcher-cross-platform
```

It returned exit 0 and only:

```text
5afe89bf9ba7431409beae83afe03913178953fc refs/heads/feature/herps-launcher-cross-platform
```

There was no `refs/heads/feature/herps-java-compatibility` in that successful
response. Therefore the local implementation was not accessible to Actions
through its requested branch at the time of that check. Dispatching the older
cross-platform branch would test different code and cannot verify Phase 5B.

GitHub Actions/API probes also failed:

```text
gh workflow list --repo Zeigen-ft/Herspers-Minecraft --json id,name,path,state
could not get workflows: Get "https://api.github.com/repos/Zeigen-ft/Herspers-Minecraft/actions/workflows?per_page=50&page=1": Forbidden

gh api repos/Zeigen-ft/Herspers-Minecraft --jq '{full_name,default_branch,permissions,private}'
Get "https://api.github.com/repos/Zeigen-ft/Herspers-Minecraft": Forbidden
```

Both commands exited 1. The observed network configuration lists `github.com`
but not `api.github.com`; these responses do not establish authenticated
Actions or repository-write access. Subsequent Git read probes exited 128 with
`fatal: could not read Username for 'https://github.com': No such device or address`.
The initial successful ref listing must not be treated as proof of current
write/dispatch access. No credential values were inspected or requested, and
no interactive login or access-policy bypass was attempted.

Initial restricted-sandbox network attempts also failed to reach the proxy.
The ref/API results above came from read-only commands with permitted network
execution; the API refusal persisted. This is an access/preflight failure,
not a Windows build or test failure.

The user explicitly requires approval before pushing. Their recommendation
about permitting a feature-only push was not treated as an explicit grant.
Only the local report is committed. A feature-only push needs approval;
working authenticated GitHub Actions access is also required before dispatch.

## Existing workflow: reviewed scope, not executed results

The local `.github/workflows/herps-launcher.yml` defines `windows-latest`,
Python 3.12 x64, Rust 1.95.0 and a Windows-only dispatch selection. After
approval and access are available, the intended commands are:

```sh
git push origin HEAD:refs/heads/feature/herps-java-compatibility
gh workflow run herps-launcher.yml \
  --repo Zeigen-ft/Herspers-Minecraft \
  --ref feature/herps-java-compatibility -f platform=windows
```

**These commands were not run.** Recheck the remote feature ref immediately
before any approved push; do not force-push or overwrite unrelated work. The
workflow push filter currently excludes this feature branch, so publishing
that ref alone does not start its Windows build. Capture the actual dispatched
run ID and verify its `headSha` against the intended feature commit.

The workflow's build/package commands include:

```powershell
python -m pip install -r herps_launcher/requirements.txt
rustup toolchain install 1.95.0 --profile minimal
python tools/ci_run.py herps-tests.log python -m unittest discover -s tests -v
python tools/ci_run.py herps-game-build.log pwsh -NoLogo -NoProfile -File scripts/build_windows.ps1
$sourceRoot = python tools/prepare_upstream.py
python tools/ci_run.py herps-package.log python tools/package_herps.py --game dist/windows-x86_64/Herspers-Minecraft --source "$sourceRoot"
```

Its preceding Python step calls `build_port_pack(target())`, performs the
locked native build/PE validation and exports `HERPS_TEST_PORT_PACK` for the
source integration tests. Installer creation uses Inno Setup 6. These are
reviewed configuration, not successful command outputs on Windows.

If successful, existing checks would cover source Python/Qt integration,
package creation, seven-page frozen navigation, bundled-helper discovery/hash,
two owned Fabric metadata fixtures (data-only and missing dependency), game
installation discovery, installation/shortcuts/uninstall and a separate owned
`.hnmod` build/selection/rollback smoke. They do not establish all requested
workflows in the installed frozen application.

Before a complete Phase 5B success claim, additional installed-app evidence
must cover Java imports, dependency resolution, unreadable classes, mixins,
version mismatches, data-port management/backup and both report formats;
Modrinth/CurseForge/Prism imports, hashes, coverage and partial carry; persistent
profiles/settings/logs; existing mod/shader operations; and save/profile
preservation through installation and uninstall. A source-test pass must stay
separate from an installed-app pass. Verify bundled metadata analysis with
developer Cargo/Rust locations removed from the subprocess environment.

The workflow builds port-pack but does not explicitly run its 99 Rust library
tests or the standalone host's 17 tests. Its Python wrappers include Windows
launcher and Bedrock Rust unit suites. Run and record all relevant available
Rust suites on the actual Windows runner. Capture screenshots where possible;
record any headless-runner or live Tailscale/GPU/gameplay limitation explicitly.

## Results and remaining evidence

| Check | Phase 5B result |
| --- | --- |
| Local implementation/branch and host preflight | Completed; Linux-only host confirmed |
| Initial remote branch lookup | Completed; requested branch absent in successful listing |
| Subsequent Git / Actions API access | Failed as recorded above; dispatch/write access unverified |
| Local CI handoff regression tests | 2 passed, 0 failed, 0 skipped on Linux with mocked build boundaries |
| Windows runner OS/version, tools and dependencies | Unverified; no Windows job started |
| Native port-pack/game/launcher build | Not run; no Windows binaries generated |
| ZIP/Inno Setup installer creation | Not run; no Windows installer generated |
| Installation, packaged runtime and uninstall | Not run; a Windows installer could not be executed here |
| Seven-page navigation, Java Mods, Modpacks, existing pages on Windows | Unverified |
| Windows Python tests and relevant Rust tests | **0 executed in this phase**; not converted into skipped test cases |
| Windows screenshots and runtime logs | Unavailable; no native application executed |
| Minecraft gameplay, shader rendering, live Tailscale session | Unverified |

There are no Windows test pass/fail/skip totals because no Windows suite was
launched. The failed access probes above are recorded separately. Historical
Phase 5A Linux results (322 Python passes, 14 skips; Rust 99/10/31/17) were not
rerun or relabelled as Windows results. The two existing workflow handoff tests
were run with `python -m unittest discover -s tests -p 'test_herps_packaging_workflow.py' -v`;
these validate literal-path/evidence handoff and failed-build rejection, not
native builds. This phase changes only documentation; report references,
recorded commit/host consistency and whitespace also passed local checks.

Raw local preflight evidence is retained under
`.cache/java-mods-phase5b-windows/`: `host-preflight.json`, `remote-heads.json`,
`remote-heads.txt`, `remote-heads.stderr`, `actions-api.json`, and
`repository-api.json`, `linux-workflow-handoff.log`, and `report-validation.json`.
The later saved Git probes failed authentication; the
initial successful listing is transcribed above from the tool result. No
native run ID, artifact path, installed binary path or screenshot is invented.

Java execution/bridge, universal conversion, packwiz, Java Build/Test and
Modpack Play remain unavailable. Static `works` cannot establish Native
compatibility or Tested successfully. All ports remain local. Application,
backend, packaging, workflow, authentication, licences and user data were
unchanged by this preflight report.

Phase 5B remains blocked pending explicit feature-only push approval and
working GitHub Actions access, or an actual accessible Windows x64 machine.
Resume Phase 5B only when those prerequisites are satisfied. Do not begin
Phase 5C, merge, tag or publish a release.
