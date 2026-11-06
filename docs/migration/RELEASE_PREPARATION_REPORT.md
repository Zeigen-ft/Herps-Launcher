# Migration and 0.1.0 release preparation — 6 November 2026

**Migration, native CI and release-file preparation PASS. Stable public-release
acceptance remains open. No release, tag or visibility change was made.**

Official repository: https://github.com/Zeigen-ft/Herps-Launcher

## Source, history and preservation

- Imported `Zeigen-ft/Herspers-Minecraft`, `feature/herps-java-compatibility`,
  `962a1ada14ec553c540347c539c2b9c112c0270d`: all 203 original files and its full
  74-commit ancestry. Destination seed `bbc4b19` is also retained.
- [Migration PR #1](https://github.com/Zeigen-ft/Herps-Launcher/pull/1) merged as
  `568bcd9c5fd4e4a42a2269a49b65c6680503d224` after validation. Its tree exactly
  matches tested head `ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb`.
- Imported GPL root licence is unchanged. The destination's original MIT notice
  remains separately under `licenses/Herps-Launcher-initial-MIT.txt`.
- Runtime/gameplay code, native content, engine patches, scripts and source locks
  remain unchanged from the imported source. Adjustments cover packaging offline
  guides, controlled CI, release-file collection and documentation.
- Source checkout remains clean at `962a1ad`. Read-only remote checks confirm
  original feature head `962a1ada14ec553c540347c539c2b9c112c0270d` and original
  main head `8c35f56ad7e25b8035a8b1cbe57f2fe168e85550` are unchanged.
- No existing user-data paths, saves, profile guards or FunCraft backup behavior
  changed. No proprietary resources or original modpack binaries were added.

## Exact automated evidence

Native destination run:
[42144749724](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724),
source `ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb`.

| Target / job | Source regression result | Delivered frozen result | Conclusion |
| --- | --- | --- | --- |
| Windows x64 / 127653395212 | 429 collected; 415 passed; 14 platform/input skips; zero failures | 68/68; zero skips | PASS |
| macOS Intel / 127653395473 | 429 collected; 426 passed; 3 platform/input skips; zero failures | 68/68; zero skips | PASS |
| macOS ARM64 / 127653395487 | 429 collected; 426 passed; 3 platform/input skips; zero failures | 68/68; zero skips | PASS |
| Release-file assembly / 127687294567 | All three native receipts, hashes, source and false gameplay/publication flags checked | 15-file set produced | PASS |

Actual runner versions were Windows Server 2025 x64, macOS 15.7.9 Intel and
macOS 15.8.2 ARM64. They do not establish acceptance on every Windows/Mac model
or on macOS 26. Hardware minima remain unmeasured.

Delivered checks include seven-page navigation, native bundled helper execution,
limited supported Java metadata/data-carry-over workflows, isolated profiles,
save/preservation fixtures and the FunCraft backup and chainmail cohorts.
The frozen environment hid Cargo, rustc and rustup from PATH. Windows tested
installation/replacement/removal with synthetic owned data, overlong-path rejection
and existing native-build rollback safeguards. Macs tested mounted real DMGs,
exact architecture, helper use and preservation after application removal.
Windows also passed the pinned engine's ten native recipe/registry probe cases.
None of these are physical gameplay or manual installer/security-prompt acceptance.

The Windows source-suite skips cover owned POSIX child fixtures, Mac Bash cases,
an unavailable optional APK, unavailable case-collision fixture and a symlink
case covered separately by Windows junction checks. Mac skips cover that optional
APK, filesystem case collision and Windows junction behavior. Exact test IDs and
reasons are retained in [RELEASE_VERIFICATION.json](RELEASE_VERIFICATION.json).
All 68 delivered cases ran on each platform; source skips are not concealed.

Additional checks:

- Local full suite with real pinned helper and offscreen Qt: 429 collected,
  414 passed, 15 platform/input skips, no failures.
- Final targeted rerun: 17/17 release-collection, guide-shipping and existing
  release-evidence regressions passed (8 collection cases plus 9 release cases).
  These are validation contracts, not gameplay.
- Portable checks passed on migration PR run 42144749563, merge run 42169516304
  and exporter commit run 42169744482, both Linux and Windows jobs.
- [Read-only export run 42169772706](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706),
  job 127734611277, passed at `a7d42bc058890bc4842c56054cd870a87c59610f`.
  It verified the original native run/artifact and every release checksum before
  uploading six smaller downloads. No native executable was rebuilt or executed.
- Historical game-only, Bedrock and shader jobs were intentionally not repeated
  automatically in the destination; no new results are claimed for them.

## Download and hash verification

[Download index](../../release/0.1.0/README.md) ·
[SHA256SUMS.txt](../../release/0.1.0/SHA256SUMS.txt) ·
[Asset/source inventory](../../release/0.1.0/ASSETS.json) ·
[Original CI manifest](../../release/0.1.0/RELEASE_MANIFEST.json).

Nine original native/evidence/content ZIPs were downloaded and matched to their
GitHub SHA-256 digests. All three native receipt contracts passed independently.
All six separate export ZIPs were then downloaded, matched to GitHub digests,
and every one of the 14 checksummed release files was hashed independently.
The copied native files are byte-identical to the original CI packages; only
release-facing outer filenames changed where needed. Checksums, sizes, original
filenames, links and expiration are recorded in the inventory.

| Release file | SHA-256 |
| --- | --- |
| Windows x64 Setup | `f9e7bfbb6cf1fd374b222a41bf6f2a014da6b17bc30d01d05a5320e36c625a2c` |
| Windows x64 Portable | `6442f72ec57b9237abb25a7e7da3ba8d450624d5680aa7ac08e133137c8c7942` |
| macOS Intel DMG | `8803bae8124490ab69fbdb137222cef34cd01432ff5c1005b7dd13b29894867e` |
| macOS Apple Silicon DMG | `bb4e7a0d5077d8230498195fdc7250fd243da5885f7eb39773739ff37449b891` |
| Chainmail 0.1.0 `.hmod` | `015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346` |

The combined artifact is a 518,599,788-byte ZIP, SHA-256
`63f167633fb593f5574281f766ba8ed6663d2f4ffb3ce5678851d5fb29fa16ca`.
Its full transfer through the local connector timed out twice; a redirected CLI
attempt returned HTTP 403. The GitHub export runner fetched that exact artifact
and verified its individual files. All smaller exported archives were successfully
downloaded and hashed locally. Two local downloads initially exhausted workspace
disk space; redundant task caches were removed and successful retries passed hashes.
These were verification-transport failures, not application/CI passes or failures.

A local reconstruction retained identical native files, guides, notices and
release manifest. Its auxiliary inspector receipt recorded the local merge HEAD
and different JSON ordering, so that inspector ZIP and appended notes/checksums
differed. Only original CI outputs are selected for distribution. Bit-for-bit
reproducibility across arbitrary checkouts/platforms is not claimed.
A local YAML check first used a venv without PyYAML; host Python then parsed the
workflow and executed its real-file validation successfully.

## Physical evidence and remaining acceptance

The user's Windows PASS report remains attached to original source run
[42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443),
source `8fb33fb04b6a3a7dd94d83ca81b08267efe7d4c9`: enabled launch, both chainmail
recipes, boots equipped with **+1 Armor**, and items retained after fully closing
and restarting both applications and reopening the same world. Crafting and
persistence were confirmed in **Survival and Creative**. These are user-reported
results, not observed by Codex. No screenshots/logs or exact hardware/build were
supplied. They do not automatically physically accept new binary hashes.

Earlier loading-logo stall and initially empty recipe output remain **unresolved**.
Later success does not establish a cause or verified fix.

**All macOS physical gameplay is NOT RUN.** Physical testing still needs Windows
11 x64, Mac Intel and Mac ARM64 testers. Clean installation/resource preparation,
input, graphics/audio, complete world/save/load, backups/restoration, update/
uninstall preservation and failure recovery require the documented manual checks.
Unreported Windows cases such as shift-crafting, repeated ingredient counts,
chest persistence, durability and missing-content/crash recovery remain NOT RUN.

## Documentation and release gates

[INSTALLATION.md](../../INSTALLATION.md) covers verified versus estimated system
requirements, architecture choice, installation/security prompts, legitimate
resources, JDK 25, first launch, profiles/native mods, chainmail, saving/backups/
non-overwriting restore, updates/uninstall, troubleshooting and hashes.
[QUICK_START.md](../../QUICK_START.md) provides the short route. Both match the
actual release-file copies and are shipped inside packaged documentation and as
separate release-ready assets. No real native installation screenshots were
available; none were invented. README and prepared release notes link both guides.

The bounded history scan found no high-confidence secret patterns in 430 source
blobs and no forbidden binary paths. Windows portable member inspection and
existing native packaging checks retain the no-bundled-Minecraft-resource boundary.
This is not a full malware, current vulnerability or legal audit. Historical
[security/distribution gates](../herps/release-security.md) remain: complete native/
transitive dependency review, Qt notices/library-replacement/corresponding-source
obligations and risk disposition before broader distribution.

Windows is **unsigned**; Macs use **development/ad hoc signatures and are not
notarized**. No credentials or new paid services were used. Private repository
access and expiring Actions downloads are additional distribution limits.
Original Forge/Fabric execution, Java bridges/Build-Test, whole-Modpack Play and
full RLCraft/FunCraft compatibility stay unsupported/disabled.

Ready for owner review as an internal prerelease candidate. **Not accepted as a
stable public release.** Follow the [manual publishing steps](../../release/0.1.0/README.md#owner-publish-manually)
only when the owner chooses; no GitHub Release or tag was created here.
