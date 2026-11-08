# Flint Gathering 0.1.0 — verification

**Windows internal candidate: CI verified and independently audited. The user
reported ALL GOOD for Stage 2 overall; individual physical test results were not
itemized. All Stage 2 macOS acceptance remains NOT RUN. This stage is not fully
accepted and the launcher is not certified for a stable public release.**

Branch: `feature/rlcraft-native-stages`. Build source: `b75897fdf84b06caad2d8c230759483a4e40a0e1`.
[Successful Windows run 42445241045](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045), job `128622672042`, Windows Server 2025 x64.
The earlier user-reported Stage 1 Survival and Chainmail results remain historical
evidence for their earlier candidates; they do not accept this new candidate.

## Download and verify

- [Windows installer and portable package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045/artifacts/13603683988)
- [Separate gathering add-on and native verification](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045/artifacts/13603419525)
- [CI logs and verification receipts](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42445241045/artifacts/13603299814)
- [Exact inner and outer SHA-256 checksums](NATIVE_SURVIVAL_STAGE_2_SHA256SUMS.txt)
- [Beginner installation and real Survival checklist](NATIVE_SURVIVAL_STAGE_2.md)
- [Machine-readable evidence, all skipped cases and failure history](NATIVE_SURVIVAL_STAGE_2_EVIDENCE.json)

Each Actions download is an outer ZIP; extract it first. GitHub may require sign-in.
The actual inner files are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 102,628,756 | `e4c3d3584a743e0482d8f69dd447e1d0a9b599b9946657c82139e1d9f0fd887c` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-2pipvzot.zip` | 137,859,123 | `edefc6a331cd008a8ab7670f2032b6f99510835e3fd273aa4fd1cc2a70457013` |

All six successful Actions artifact ZIPs were downloaded and checked against
GitHub's recorded sizes and SHA-256 digests. The installer/portable hashes were
also checked against `candidate.json`, `SHA256SUMS` and the installed lifecycle
receipt. All three frozen bundled `.hmod` files match their reviewed pins.
The actual x64 game PE contains the opt-in gathering tag and retains the 16 MiB
stack setting. Every shipped engine patch postimage matches the current manifest;
the new MIT source/license is included. These are artifact checks, not gameplay.

## Implemented behavior and preservation

A separate OFF-by-default `.hmod` opts a fresh, explicitly selected disposable
profile into two native Survival actions: top-face stone/cobblestone knapping
(one plain flint to two existing shards), and right-click knife cutting of short
grass/ferns (one fiber, plant removal and normal one-point tool wear).
The extension uses the existing authoritative item-use hook, inventory helpers
and block setter. It adds no public hook API, dependency, network service or save
schema. Native code uses MIT; the tag package and launcher/tools use GPLv3.

Full output space is required before consuming/removing/wearing anything.
Inventory snapshots roll back incomplete insertions or rejected plant writes.
Earlier claims are respected and non-Survival actors are excluded. Existing
recipes and vanilla tree punching remain. This is not full No Tree Punching.

The original packages remain exact:

| Package | SHA-256 |
| --- | --- |
| `herspers_rl_chainmail-0.1.0.hmod` | `015c3d553a6a2bcfed4412559b9b83bc3ef65599d539a7686e65577ec4c5c346` |
| `herspers_rl_flint-0.1.0.hmod` | `919745713d5233bcd4cfee4f3da04328d3808eb06b24df966f26b054a69b81cc` |
| `herspers_rl_gathering-0.1.0.hmod` (37,136 bytes) | `177c3f4eefedd4f0e4eda4e54634efeee555e4b22dd13e0ec022733328fb87fd` |

Install refuses default or saved profiles. The starter must be installed first
and enabled before gathering can be enabled. Old engine metadata is refused.
Managed disabling/removal after saves, missing content and invalid ownership
receipts fail closed. Synthetic preservation sentinels cover existing worlds,
other profiles, unknown preferences and FunCraft backups. They are not real
world restoration or missing-item recovery tests.

## Automated evidence

| Check | Passed | Skipped / limits |
| --- | ---: | --- |
| Local Linux source regressions with real port-pack | 454 of 471 | 17 OS/input skips |
| Portable Windows CI, run 42445183241 | 366 of 471 | 105 unavailable-backend/platform/input skips |
| Portable Linux CI, same run | 359 of 471 | 112 unavailable-Qt/backend/platform/input skips |
| Native Windows source regressions, real backend | 456 of 471 | 15 OS/input skips |
| Gathering native package/tag loader | 4 of 4 | Owned resource fixtures; not a live world |
| Actual gathering transaction rules | 12 of 12 | Owned inventory/block doubles; not Game adapter execution |
| Legacy native Chainmail / Flint probes | 10 / 13 | Synthetic resources/recipe/tool components |
| Installed frozen legacy / Flint / Gathering cohorts | 68 / 7 / 7 | Zero skips; Rust/Cargo/rustup absent from PATH |
| Seven-page navigation and bundled helper | PASS | Actual frozen Windows app, offscreen automation |
| Install, replacement, uninstall, reinstall, final uninstall | PASS | Actual Inno on Windows; owned preservation fixtures |
| Trusted native source-mod compile/select/rollback | PASS | Marker compiled; hook execution and gameplay NOT RUN |
| Local frozen Linux gathering diagnostic | 7 of 7 | Zero skips; no bundled game; not a distribution build |

The native lifecycle now waits for Inno's process tree, resolves that install's
actual uninstaller from its log, confirms completion and checks launcher/shortcut
removal plus preservation. This successful run used `unins000.exe` for both
uninstalls; focused tests also verify correct selection of a legitimate `unins001.exe`.
No gameplay, GPU rendering, audio, resource preparation with legitimate Minecraft
inputs, or completely uninstalled developer-tool environment is inferred from CI.

The patch fingerprint is
`228db2d44d7ee8b86244e08fd04e4c41ab296e325c5f34485074dcd5975b7b81`.
Windows prepared-tree SHA-256 is
`3612d6ab73801d094b640c0e1c7cf3a6e3eb139b4672d2e9976c8c74f7147b6e`;
the Linux tree is recorded separately because executable mode metadata differs.
Old prepared caches remain intact. Compiler input pins and Cargo.lock are unchanged.

## Failures and corrections retained

1. Run `42440395269` at `56e1f86`: Linux UI test import failed when optional Qt
   was unavailable. `aaa9fdd` makes that cohort skip cleanly; native/frozen
   Windows cohorts still require zero skips. Corrected portable CI passed.
2. Native run `42440409389` was cancelled early to supersede the optional-Qt
   test correction. No candidate was accepted from it.
3. Native run `42440562327` at `aaa9fdd`: the new owned vanilla fixture omitted
   `repairable`, which the starter deliberately removes. The native validator
   rejected the incomplete fixture. Game compile, source tests, older native
   probes and 12 rules passed. `e212526` supplies relevant vanilla defaults;
   gameplay code and `.hmod` pins did not change.
4. Run `42442682957`, attempt 1 at `e212526`: **Codex mistakenly inferred a
   stalled runner from an empty live-step API response and cancelled it**.
   Recovered completed-job logs show normal execution through native gathering
   and installed tests; cancellation interrupted the SDK build. No runner-startup
   failure is asserted. Rerunning removed that attempt's artifact; its completed
   logs remain the evidence source. The report records this limitation.
5. Same run, attempt 2: final uninstall failed with WinError 2 because the harness
   assumed `unins000.exe` while a legitimate reinstall created `unins001.exe`.
   Logs show reinstall beginning before the prior temporary uninstaller child
   completed. `b75897f` resolves the actual entry, waits for the process tree,
   records failed spawn arguments and checks final completion/removal. Six
   focused tests and the full native lifecycle now pass. The failed evidence ZIP
   was independently hashed and is recorded. A redundant immutable-key compiler
   cache save warned; it was not the verification failure.
6. The independent audit initially expected the new MIT license below the app
   folder; the existing offline-documentation layout puts it at ZIP root under
   `native/rlcraft_gathering/LICENSE`. The exact license text was verified there;
   no package change was needed.

## User report — separate from CI

On 8 November 2026 the user replied **ALL GOOD** to the supplied Windows candidate
and linked Survival guide. [The exact report and scope](GATHERING_WINDOWS_USER_REPORT.json)
record overall positive feedback, without promoting it to individual checklist
passes. Codex did not observe the testing; no screenshots, logs, counts, test date,
OS build, explicit game mode or exact downloaded member/hash were supplied.
Windows x64, Survival and run 42445241045 are the preceding instructions/context,
not independently reconfirmed details. In particular, full-restart persistence,
main/off-hand, full-inventory and other edge-case results remain individually
unconfirmed. Existing automated receipts retain their original false gameplay
and interactive flags. No new code or package was built for this report update.

## Remaining acceptance and release limits

The overall positive reply does not separately confirm real Survival actions,
main/off-hand counts, invalid/full-inventory cases, repeated use,
breakage/enchantments, chest/inventory persistence or plant persistence after full
restart. Those detailed results still need explicit confirmation. Combined
Chainmail/Flint/Gathering gameplay, physical install/update/uninstall,
backup restore, cross-profile hashes, crashes/disk-full recovery and multiplayer
remain unverified. No Stage 2 Mac binaries were built; all physical macOS cases
remain NOT RUN. No screenshots or real gameplay evidence were invented.

Earlier loading-logo stalls and initially empty chainmail recipe output remain
unresolved observations. No cause or fix is claimed. Full RLCraft/FunCraft,
original Java/Forge execution, world conversion, thirst, temperature, skills,
limb health, new creatures and world generation remain unsupported/unimplemented.
Java Mods Build/Test and whole-Modpack Play remain disabled.

The candidate now has **overall user-reported positive feedback**; detailed
Windows acceptance, full native acceptance and stable public publication remain
open. No next gameplay port has begun.
Main, tags and existing releases were not modified; no public release was created.
