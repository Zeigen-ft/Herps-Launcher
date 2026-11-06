# Herps Launcher 0.1.0 — verified download files

**Prerelease candidate. No GitHub Release or tag has been created.**
Sign into an account with access to this private repository before downloading.
These Actions downloads currently expire on **4 February 2027**. They are not
permanent public release URLs. The owner will publish/upload manually if approved.

## Download

Each link downloads an **outer ZIP**. Extract it to get the actual file below.
Do not run installers inside ZIPs. The portable download contains another ZIP;
extract that complete inner portable ZIP before running the launcher.

| Download | Actual file after extraction | Bytes |
| --- | --- | ---: |
| [Windows x64 installer](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480642033) | `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` | 102,636,657 |
| [Windows x64 portable](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480746663) | `Herps-Launcher-0.1.0-Windows-x64-Portable.zip` | 137,733,840 |
| [macOS Intel](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480771423) | `Herps-Launcher-0.1.0-macOS-Intel.dmg` | 166,550,044 |
| [macOS Apple Silicon](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480492694) | `Herps-Launcher-0.1.0-macOS-Apple-Silicon.dmg` | 159,407,599 |
| [Optional separate chainmail package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480597213) | `herspers_rl_chainmail-0.1.0.hmod` | 40,002 |
| [Checksums, guides, release notes and notices](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706/artifacts/13480547286) | `release-files/` contains the ten remaining release files; an extra `EXPORT_VERIFICATION.json` documents the export | — |

Alternatively download the original
[combined 15-file bundle](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724/artifacts/13474495737)
(518,599,788-byte outer ZIP). The individual files are the same.

[SHA256SUMS.txt](SHA256SUMS.txt) · [Manifest](RELEASE_MANIFEST.json) ·
[Machine-readable asset/download index](ASSETS.json) ·
[Exact CI-prepared release notes](RELEASE_NOTES.md) ·
[Complete installation guide](../../INSTALLATION.md) · [Quick start](../../QUICK_START.md).

The checksum manifest has **14 entries** for the other 14 files in the 15-file
set; it does not hash itself. Outer Actions ZIP digests differ from inner file
hashes. All six export ZIP digests and all 14 release hashes were independently
checked. The binary source is `ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb` in native
run [42144749724](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724).
Run [42169772706](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42169772706)
only verified/copied those files; it did not rebuild executables.

## Install and test

Use the [complete guide](../../INSTALLATION.md) or [quick start](../../QUICK_START.md).
Windows is unsigned. Mac apps are development/ad hoc signed and **not notarized**.
Install both Mac app bundles. JDK 25 and your legitimate Minecraft Java 26.3
resources are needed for preparation; normal installed use needs no Rust/Cargo.

Chainmail is OFF by default. Use the dedicated Modpacks installer only for an
explicitly selected fresh disposable named profile, enable it before creating a
world, and keep it enabled once that profile contains saves. Do not use a full
RLCraft/FunCraft ZIP as an executable modpack.

The user's earlier Windows gameplay report is preserved, including Survival and
Creative crafting/persistence. It does not automatically accept these rebuilt
files. Mac physical gameplay and unreported Windows edge cases remain **NOT RUN**.
Earlier loading-logo stalls and initially empty output remain unresolved.

## Owner: publish manually

1. Review the [final report](../../docs/migration/RELEASE_PREPARATION_REPORT.md),
   licensing/security gates and known issues. Keep the prerelease designation.
2. Download the four platform files, optional `.hmod` and guides/notices ZIP, or
   the combined bundle. Put the original **15 release files** together in an
   empty folder. Use files inside `release-files/`, not the outer ZIP wrappers.
   Do not replace the checksummed CI README/release notes with later edited copies.
3. Verify every entry in `SHA256SUMS.txt`. Use the manifest's exact source and
   hashes; do not substitute a newer same-named artifact. Keep all notices.
4. In this repository choose **Releases → Draft a new release**. When you decide
   to publish, create `v0.1.0` targeting the reviewed destination `main` commit.
   Executables were built from the recorded ancestor above; later main changes
   are export/evidence documentation, not a new native build.
5. Paste the bundle's `RELEASE_NOTES.md`. It links both beginner guides. Upload
   the installer, portable ZIP, both DMGs, `.hmod`, inspector ZIP, `SHA256SUMS.txt`,
   `INSTALLATION.md`, `QUICK_START.md`, README, release notes, LICENSE,
   `LICENSES.zip`, third-party notices and `RELEASE_MANIFEST.json`.
6. Mark **This is a prerelease**, review the draft, then publish only when you
   personally choose. The repository is still private; decide visibility/access
   separately. No signing, notarization, stable acceptance or public access is
   implied by this preparation.
