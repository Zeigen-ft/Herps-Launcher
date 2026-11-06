# Targeted-porting preparation — Windows candidate and RLCraft inspection

Date: 2026-11-05 (Asia/Singapore). Branch:
`feature/herps-java-compatibility`. Starting commit:
`36fab19720ccd3dc0b0d5961b7a10670f82722c6`.

This records the Windows preparation handoff. The subsequent
[verified RLCraft 2.9.3 investigation](RLCRAFT_COMPATIBILITY_REPORT.md) supersedes
its pending-input statements below; candidate hashes and CI results remain the
historical evidence recorded here. No RLCraft gameplay is thereby accepted.

**Preparation is complete; physical Windows backup/load acceptance and the
actual RLCraft 2.9.3 inspection remain open.** This iteration supplies an internal
Windows x64 candidate with the existing FunCraft-scoped manual backup utility,
an offline RLCraft inspector, bounded private exports and beginner instructions.
Neither original modpack is verified playable. No next gameplay-mod port starts.

## Commits and preservation boundary

| Commit | Reviewable change |
| --- | --- |
| `466202400dcf7eff61eb90b0a46ad60e47fbd6b0` | Standalone RLCraft inventory/export/reassembly, safety tests and Windows guides |
| `a59a7649fa9d2b6c2d3eef02ab7b125429802283` | Require all three backup UI cases in delivered Windows acceptance; preserve an existing backup-folder marker |
| `240d1fde7ccaa51e83d02253fe794fc8a662b0c5` | Correct descriptor/path fingerprint disagreement on Windows; preserve malformed ZIP spelling in a Windows test fixture |
| `2e55a0dd6902507ee2815f28f0d2d6f2d84822f9` | Emit inspector progress/errors as UTF-8; assert captured Unicode output and empty stderr |
| `6bff74319177327d1159ddda978e6852b960f8b0` | Install existing pinned test dependencies and use offscreen Qt in the separate portable CI workflow |
| `91a14cd0ebcc28c7e894173e7dc19c4a3f9498a1` | Reject export data exceeding the declared reassembled total before writing it; test zero bytes written |

The downloadable candidate and inspector are built from **`91a14cd`**. This
documentation/evidence handoff does not change their runtime code.
The [machine-readable ledger](WINDOWS_CANDIDATE_EVIDENCE.json) records full SHAs,
test IDs/skips, failures, artifact hashes and explicit acceptance limitations.

The engine pin, core launcher/profile/PLAY code, Java adapter/library, modpack
service, Inno installation/uninstallation script and package builder remain
unchanged from `36fab19`. The only launcher runtime fix makes backup snapshots
and copies fingerprint the same safely opened file descriptor. Before/after
identity, size, time, content-hash and final-tree checks remain required; unsafe
paths/links, changed files, locks and bounds still fail closed. Existing saves,
profiles and earlier backups are never selected as output destinations.

## Exact downloads

Successful **Build Herps Launcher** run: [**42034782638**](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638), job `127269988665`.
Exact source: `91a14cd0ebcc28c7e894173e7dc19c4a3f9498a1`.
Run started `2026-11-05T13:19:40Z`; final update `2026-11-05T13:47:32Z` (UTC).

| Download (GitHub artifact) | ID | ZIP bytes | ZIP SHA-256 |
| --- | --- | ---: | --- |
| [Herps-Launcher-0.1.0-Windows-x86_64](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638/artifacts/13420240992) | `13420240992` | 238,117,214 | `83c97ba04036137cead5ca591c01017d5a907341603dde999b6ad1a420ff5fe0` |
| [RLCraft-2.9.3-Local-Inspector](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638/artifacts/13420625410) | `13420625410` | 26,736 | `c8ca99670471033c36234bea8bd9f19a44689b5a37633591b85fd8fe8cb0ac3e` |
| [Herps-Launcher-evidence-Windows-x86_64](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638/artifacts/13418804700) | `13418804700` | 672,595 | `d29ac9e73a5ed03f437a5d2bfa5b238745a3696f39b5c8b66b07d13d68640804` |

All three complete downloads were independently hashed; GitHub's artifact
digests match. Extracted installer/portable bytes also match `candidate.json`;
the inspector files match `inspector.json`/`SHA256SUMS`. GitHub currently
reports artifact expiry `2027-02-03T13:19:41Z`.

Optional portable file inside the launcher artifact: `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-pvpa5n1p.zip`
(137,494,544 bytes), SHA-256 `b5c3b8d5096ef838f85584b9accc4666481611fcc41762adc5c5976f47412773`.

Delivered Windows `inspect_rlcraft_293.py` SHA-256:

```text
cccc155cf8b3acc812b1f3db26d1c7a4775dd9c1783c2a706a7d3bd7f6aca957
```

The delivered script has Windows CRLF line endings; its bytes match the
committed source after newline normalization. Use the **delivered hash**
above when verifying the Windows artifact, not the LF checkout hash.

These are temporary **GitHub Actions test artifacts**, not releases. Sign in to
GitHub if asked, open the successful run, scroll to **Artifacts**, and choose the
exact name above. Use File Explorer **Extract All** on the download. Artifact
retention/permissions may later prevent downloading it; record that as a
limitation instead of substituting an older 0.1.0 build.

For launcher installation use the extracted
`Herps-Launcher-0.1.0-Windows-x64-Setup.exe`. Check its full SHA-256 with:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "C:\Users\YourName\Downloads\EXTRACTED-FOLDER\Herps-Launcher-0.1.0-Windows-x64-Setup.exe"
```

Expected **Setup EXE** SHA-256 (102,492,025 bytes):

```text
17d66a9f36b9684d3c0223e1a26ad4d893efb3d3343133f84d9e682134516bbb
```

Compare all 64 hexadecimal characters before running it. The launcher bundles
Python/Qt and its passive helper; launcher backup/import does not require an
end-user Python, Rust/Cargo or Java installation. Real game resource preparation
still has the existing legitimate Minecraft/JDK requirements. The separate
inspector needs Python 3.12, as explained below. No signing credentials or paid
services were used. SmartScreen/antivirus trust on a physical PC is unverified.

## Automated verification

| Check | Observed result |
| --- | --- |
| Final local Linux regressions | **397 run; 383 passed; 14 skipped; 0 failures/errors**, 22.374 s |
| Final Windows packaging source tests | **397 run; 384 passed; 13 skipped; 0 failures/errors**, 59.408 s |
| RLCraft inspector safety/export/reassembly | **18 passed** on Windows, including actual 24 MiB payload boundaries, Unicode standalone CLI, 2.8.2 rejection, corrupt/missing/mixed parts and zero-write size-bound rejection |
| Backup filesystem/safety tests | **22 passed** on Windows; source tree/backup isolation, binary/Unicode/empty-directory round trip, links/locks/running-child rejection, changed inputs and injected failures |
| Candidate evidence/staging guards | **2 passed** on Windows |
| Modpacks Qt source workflows | **14 passed** on Windows; includes all 3 backup/layout/cancellation cases |
| Delivered frozen Java Mods/Modpacks workflows | **65 passed; 0 skipped/failures/errors**, required backup cases present, persistent reload verified; Rust tools absent from PATH |
| Installed/reinstalled seven-page navigation + bundled helper | **Passed** with owned passive fixtures |
| Installer replacement/uninstall/reinstall and existing backup marker preservation | **Passed**, eight recorded fixture files retained |
| Existing native compile/select/rollback regression | **Passed**; hook execution/gameplay explicitly false |
| Separate portable CI: tooling | **397 run; 296 passed; 101 skipped; 0 failures/errors**, 25.078 s |
| Separate portable CI: windows-tooling | **397 run; 297 passed; 100 skipped; 0 failures/errors**, 38.923 s |

Separate repaired tooling workflow: [run 42034721374](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034721374), source `91a14cd0ebcc28c7e894173e7dc19c4a3f9498a1`. It does not supply a real port-pack backend; unavailable
backend/Qt/platform cases remain skipped there. The Windows packaging workflow
above supplies the real bundled helper and executes the full required cohort.

Final local skips: 12 PowerShell stack-repair cases, one macOS AppleScript
case and one supplied-APK integration. Final Windows source skips: three
POSIX process fixtures, eight macOS Bash/dialog cases, one supplied-APK case
and one case-colliding-filesystem fixture. All new inspector/backup/candidate
guard/Modpacks Qt cases execute on Windows. Every skip ID/reason, including
the separate tooling jobs, is retained in the ledger. macOS packaging steps
are intentionally skipped by this Windows-only dispatch.

Evidence ZIP locations: `herps-tests.log`,
`dist/herps/phase5d-evidence/windows-lifecycle.json`, `installed-workflows.json`,
`installed-smoke.json`, `reinstalled-smoke.json`, and `installer-long-path.log`.
`native-build-proof.json` is in the launcher artifact. Source logs contain no
standalone-child Unicode decoding/thread warning in the final run.

CI uses **Windows Server 2025 x64, build 26100**, Python 3.12.10 and offscreen Qt.
It is native Windows execution, not physical Windows 11 gameplay. The installed
candidate opens all seven pages, executes the bundled pinned helper, completes
the 65 frozen Java Mods/Modpacks cases and retains persistent profile/settings/
save fixtures with `cargo`, `rustc` and `rustup` absent from PATH. All three
required backup UI cases are present and pass; old or skipped cohorts fail the
acceptance guard. Java Build/Test and whole-Modpack Play remain disabled.

The lifecycle receipt verifies early rejection of an overlong installation
destination **before copying**, installation to a path with spaces, preservation
of an existing selected profile and unknown preference, same-version replacement,
uninstall, reinstall, renewed seven-page/helper startup, and final uninstall.
Eight recorded files remain unchanged across those latter lifecycle operations:
default/named save sentinels, settings, options, shader/data fixtures and an
existing backup-folder marker. These are owned test bytes, not real worlds or
proof of every historical-version migration. Settings are intentionally changed
by the acceptance harness before that final preservation snapshot.

The existing owned native-mod regression compiles, finds its marker, selects the
built binary and rolls back without changing the clean binary/source cache/save
fixture. Its receipt explicitly records **hook execution and gameplay false**.
It is baseline regression coverage, not another targeted gameplay-mod port.

The actual supplied FunCraft ZIP was also imported on Linux with the trusted
pinned helper, the production input hash guard and an empty PATH. Backup
verification, independent scratch extraction and source/settings/sentinel
preservation pass. Only helper `import` runs. No Java/mod code, game, conversion
or dependency download runs. Its `level.dat` contains deliberately invalid owned
sentinel bytes; this is filesystem integrity evidence only.

## Failures and corrections retained

1. Windows packaging run
   [42024491267](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42024491267)
   at `a59a764` stopped during source tests: **395 run, 380 passed, 13 skipped,
   one failure and one error**. No installer was built. The backup compared
   path-stat and descriptor-fstat values that disagree on Windows. Fingerprinting
   now consistently uses the same descriptor. A malformed ZIP test also let
   Windows normalize a backslash before writing it; the fixture now retains the
   hostile spelling, without weakening the inspector's rejection.
2. Run
   [42026401212](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42026401212)
   at `240d1fd` passed packaging and 65 frozen cases, but detailed log review
   found a child-output `UnicodeDecodeError` that its standalone inspector test
   did not assert against. It is superseded for this handoff. `2e55a0d` makes
   redirected CLI output UTF-8 and requires complete captured Unicode progress,
   no stderr and a completed summary. The corrected `2e55a0d` run is retained as an intermediate result; the final
   `91a14cd` run includes the additional reassembly bound and must contain no
   such warning.
3. Static safety review found that reassembly needed to enforce the declared
   total before writing each payload. `91a14cd` adds that guard. Its regression
   supplies a validly hashed part with an undersized total declaration and
   checks that the temporary output is still zero bytes when discarded.
4. The separate **Portable tooling checks** runs at `a59a764`, `240d1fd` and
   `2e55a0d` failed because their environments did not install the existing
   launcher test requirements: Linux lacked `packaging.requirements`; Windows
   lacked PySide6-Essentials distribution metadata. `6bff743` installs the
   existing pinned requirements and sets offscreen Qt/UTF-8. No dependency
   version or launcher behavior is changed. The first Windows tooling attempt
   also encountered the same two backup/ZIP-fixture defects described above.
   Run IDs, exact failed cases and final results are retained in the ledger.

The failed first Windows evidence ZIP is artifact `13414120210`, SHA-256
`195157eff2c9c464f03268570471878429a7d830c4454b3314e761ae31e3ebc7`.
Skipped tests remain visible; they are never counted as passes. Deliberately
hostile fixtures and injected disk/write/verification failures are expected
negative test outcomes, distinct from the unexpected failures listed here.

## RLCraft 2.9.3: what the local tool establishes

Follow [Inspect your RLCraft ZIP on Windows](WINDOWS_RLCRAFT_INSPECTION.md).
Download the inspector artifact, extract it once, install Python 3.12, verify
the delivered script hash, double-click `Inspect-RLCraft.cmd`, and paste the
original ZIP's **Copy as path** value. Nothing is uploaded automatically.

The standalone standard-library program inspects the ZIP as untrusted data;
it does not extract member paths, load Java classes, execute scripts/mods, fetch
dependencies or touch launcher profiles. It records:

- Full original SHA-256 and root manifest identity. It requires RLCraft 2.9.3,
  Minecraft 1.12.2 and the bounded legacy Forge loader family. Renaming a 2.8.2
  ZIP fails. These declarations do not authenticate its publisher.
- Complete outer member path/size/CRC/SHA-256 listing, plus bounded nested-JAR
  path/hash listings and metadata. Inventory covers CurseForge project/file
  requirements, HTML labels, legacy `mcmod.info`, available Maven declarations
  and licence scopes, FML/coremod/tweaker/transformer/mixin evidence, and bounded
  class-string dependency/entrypoint candidates. Candidates are not resolved
  runtime dependencies. Missing JARs/metadata, unreadable scans, nested-library
  closure and absent licences remain explicit unknowns.
- Original manifest/mod-list copies, `files.jsonl`, `files.sha256`,
  `nested-files.jsonl`, `dependency-inventory.json` and inspection receipt.
- `00-summary.zip`, all numbered `metadata-*.zip` / `archive-*.zip`, and
  `EXPORT-SHA256SUMS.txt`. Numbered exports use 24 MiB payloads inside fixed-name
  ZIP members; every completed ZIP is checked **strictly below 32 MiB**.
  Reassembly checks numbering, lengths, offsets, per-part/full checksums and
  actual 2.9.3 identity, publishing only a new output file.

Bounds include a 4 GiB source, 8 GiB declared outer data, 100,000 outer entries,
32 MiB central directory before member-table allocation, 2 MiB metadata reads
and 128 MiB JAR metadata scans. Nested scans also have per-JAR/aggregate entry,
expanded-byte and class-scan limits. A completed outer listing does not imply
complete dependency closure. Bounds/unsafe inputs fail visibly or leave explicit
blocked metadata; none silently becomes gameplay support. Existing output
folders/files are refused; failures cannot retain completed export bundles.

Return the summary first, then **every numbered ZIP separately**, plus the
checksum text. Keep these exports private: they include original copyrighted
pack bytes. Do not publish or commit them. Codex can reconstruct the exact
original without asking the user to run its contents. The supplied `2XD/RL-Craft`
repository declares **2.8.2** and remains excluded as 2.9.3 evidence. Until the
actual output arrives, its checksum/mod count/versions/dependency graph/rights
and complete per-mod compatibility matrix remain unknown.

## Physical Windows acceptance — still NOT RUN

Use the [Windows 11 real-world backup acceptance guide](WINDOWS_BACKUP_ACCEPTANCE.md).
It covers verified installation, seven-page navigation, legitimate resource
preparation, PLAY, graphics/audio/input, real world creation and a distinctive
marker, save/exit, stopped-profile backup and verification, then **independent
File Explorer extraction into a new scratch folder**. Compare hashes before
copying only `saves/` into a **different new empty disposable profile**. Load the
world, observe the marker, save/exit/relaunch and verify both profiles remain
independent. Stop on any merge/replace prompt. Never overwrite an existing save.

Every manual case starts NOT RUN; failures block dependent cases. Record machine,
Windows build, exact source/run/artifact/hash, steps, expected/actual result,
exit codes, screenshots and reviewed logs. Do not share credentials, complete
support folders, Minecraft assets or private worlds/backups by default. Archive
integrity alone cannot pass real-world load/gameplay acceptance.

## Remaining limits and stop point

- Physical Windows 11 resource preparation, PLAY, rendered graphics/audio/input,
  real save/load/relaunch and independent restored-world marker verification are
  open. Real crash/power-loss, antivirus/SmartScreen, performance and wider
  hardware/historical-upgrade behavior are also unverified.
- No new macOS candidate or physical Mac acceptance was performed. Prior Phase
  5D results are historical evidence only; ARM64 and Intel manual gates remain.
- Backup scope remains manual, stopped native-profile worlds only: 512 MiB
  total, 128 MiB/file, 10,000 entries, 32 path components; no live/timed/server
  backup, pruning, automatic in-place restore or legacy Forge-world migration.
- Java runtime execution/bridges, Java Mods Build/Test, whole-Modpack Play,
  arbitrary Forge/mixin features and universal compatibility remain unavailable.
  No FunCraft or RLCraft whole-mod row is promoted by this backup utility.
- Exact RLCraft input, dependency/source/licensing review and the prior
  [security/distribution gates](../herps/release-security.md) remain prerequisites
  to a future public release. Builds record a pinned recipe and exact hashes;
  they are not claimed bit-for-bit reproducible or publicly release-ready.

Only the feature branch is updated. `main`, tags and existing releases are
unchanged; no release or public installer was published. Work stops here before
choosing or implementing the next gameplay-mod behavior.
