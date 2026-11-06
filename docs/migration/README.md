# Official-home migration and release preparation

Destination: https://github.com/Zeigen-ft/Herps-Launcher

Imported source: `Zeigen-ft/Herspers-Minecraft`, branch
`feature/herps-java-compatibility`, commit
`962a1ada14ec553c540347c539c2b9c112c0270d`. All 203 files were initially imported
byte-for-byte. The source repository is not changed by this migration.

Both histories are preserved through a merge of unrelated roots: the destination
initial commit `bbc4b1927f73048feb0de92a563caa0c89dffe67` and the complete 74-commit
source ancestry. The destination's original MIT notice is retained under
`licenses/Herps-Launcher-initial-MIT.txt`; the imported root GPL licence is retained.
This is not a GPL-to-MIT relicense.

[Provenance](PROVENANCE.json) · [bounded source-history scan](SOURCE_HISTORY_SCAN.json)
· [verbatim original README](SOURCE_README_962a1ad.txt)

The archived README is plain text to preserve original bytes/relative links;
read it in the [original source context](https://github.com/Zeigen-ft/Herspers-Minecraft/blob/962a1ada14ec553c540347c539c2b9c112c0270d/README.md).
Historical source-repository CI/evidence links remain historical and are not
relabelled as destination runs.

## Scope

Launcher/gameplay code, profile/save paths, safety guards, FunCraft utilities,
Chainmail definitions and existing tests are retained. Adaptations cover the
new README/guides/notices, offline-document inclusion, controlled CI triggers
and a release-file collector that copies real native packages without changing
binary/DMG bytes. No new gameplay feature or Java bridge is introduced.

Heavy desktop validation runs on PRs or manual dispatch. Destination main pushes
run portable checks but do not automatically repeat all native/legacy builds.
Historical game-only/Bedrock/shader workflows remain manually runnable; their
automatic jobs remain limited to the old source repository. All jobs retain
read-only repository permissions; no workflow publishes a release or creates a tag.
Cold native builds have a longer timeout without selecting paid larger runners.

## Validation status

[Migration PR #1](https://github.com/Zeigen-ft/Herps-Launcher/pull/1) was merged
after destination native validation. Merge `568bcd9c5fd4e4a42a2269a49b65c6680503d224`
has exactly the tested `ada1c0fcec013ec15d2e8bff865a8bbb1eb875eb` file tree and
preserves both histories. Later changes add the read-only download exporter and
final documentation/evidence; launcher/gameplay code and content are unchanged.

Destination run [42144749724](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724)
passed Windows x64, macOS Intel, macOS ARM64 and release assembly. Each delivered
platform passed 68/68 frozen cases with zero skips. Source suites passed with
14 Windows and 3-per-Mac platform/input skips; exact cases are recorded.

Read the [final report](RELEASE_PREPARATION_REPORT.md),
[machine-readable evidence](RELEASE_VERIFICATION.json) and
[download index](../../release/0.1.0/README.md). All six separate download ZIPs
and all 14 checksummed release files were independently verified. The original
repository's working tree and remote branch heads remain unchanged. No release,
tag or visibility change was made. This is a prepared prerelease candidate;
stable public-release acceptance remains open.

Source baseline: run 42129264888 passed Windows x64, macOS Intel and Apple Silicon,
with 68/68 frozen cases each. User-reported physical Windows crafting/persistence
was in Survival and Creative on run 42118750443. Earlier stall/empty-output
observations remain unresolved. All Mac physical gameplay remains NOT RUN.

## Owner: manually publish the prerelease

1. Review the final report, known issues and licence/distribution gates.
2. Download/extract the exact [separate exports](../../release/0.1.0/README.md),
   or **Herps-Launcher-0.1.0-release-ready** from destination run 42144749724.
   Do not substitute source-repository artifacts or another same-named build.
   Verify its `SHA256SUMS.txt` and provenance. The separate guides ZIP contains
   `release-files/`; use that folder's files. `EXPORT_VERIFICATION.json` is
   additional export provenance, outside the original 15-file release set.
3. In GitHub → **Zeigen-ft/Herps-Launcher → Releases → Draft a new release**,
   choose/create `v0.1.0` targeting the validated destination main commit. No tag
   or release is created by this automation.
4. Use a title such as **Herps Launcher 0.1.0 — Prerelease candidate**. Paste the
   bundle's `RELEASE_NOTES.md`, including installation-guide links and limitations.
5. Upload the bundle's individual installer, two DMGs, portable ZIP, `.hmod`,
   inspector ZIP, `SHA256SUMS.txt`, guides, licence/notices and provenance files.
   Both `INSTALLATION.md` and `QUICK_START.md` must be downloadable release assets.
6. Mark **This is a prerelease**. Do not mark it a stable/latest release. Review
   all hashes and known issues. Save a draft first if you want further review;
   publish only when you personally decide to do so.
7. The repository is private: release links remain restricted to authorized
   users unless you separately choose a visibility/distribution policy. This
   task does not change visibility, enroll signing services or publish publicly.

macOS is not notarized; Windows is unsigned. Full RLCraft/FunCraft and original
Forge/Fabric JAR execution are unsupported. Read the complete
[installation guide](../../INSTALLATION.md) and [release notes](../../RELEASE_NOTES.md).
