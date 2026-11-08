# Herspers Minecraft Launcher

**Herps Launcher 0.1.0 — prerelease candidate**

The official launcher home is **[Zeigen-ft/Herps-Launcher](https://github.com/Zeigen-ft/Herps-Launcher)**.
This unofficial desktop launcher manages the native Rust Minecraft client,
profiles, saves, supported native content and passive Java-mod inspection.
The game integration currently targets **Minecraft Java Edition 26.3 resources**.
It is not the official Minecraft launcher or a universal Forge/Fabric launcher.

**Start here:** [Quick start](QUICK_START.md) · [Complete installation guide](INSTALLATION.md)

[Downloads and release notes](https://github.com/Zeigen-ft/Herps-Launcher/releases) ·
[CI builds](https://github.com/Zeigen-ft/Herps-Launcher/actions/workflows/herps-launcher.yml) ·
[Prepared release notes](RELEASE_NOTES.md) · [Known limits](docs/HERPS-SUPPORT.md)

Until the owner publishes a prerelease, use the exact successful destination CI
artifacts recorded in [migration/release preparation](docs/migration/README.md).
The repository is currently private: downloads require repository access. This
migration does not change visibility, create a release or create a tag.

## What is included

- Seven pages: Home, Mods, Java Mods, Modpacks, Shaders, Multiplayer and Settings.
- Separate named profiles, existing-save preservation, game discovery and logs.
- Native `.hmod` content management and guarded, trusted `.hnmod` development tools.
- **Chainmail Plate and Boots 0.1.0**, optional and disabled by default; installation
  is restricted to an explicitly confirmed fresh disposable profile.
- **[Flint Survival Starter — native remake stage 1](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_1.md)**
  on the development branch: four native items and five starter recipes, OFF by
  default with fresh-profile guards. The user reports the basic Windows Survival
  checklist PASS; [scope and remaining tests](docs/targeted-porting/FLINT_WINDOWS_PHYSICAL_EVIDENCE.json)
  are recorded separately from CI. Broader native acceptance remains open.
- The inspected FunCraft hotfix's bounded manual world-backup utility.
- **[Flint Gathering — native remake stage 2](docs/targeted-porting/NATIVE_SURVIVAL_STAGE_2.md)**:
  a separate opt-in add-on for stone knapping and knife-cut grass fiber using
  unchanged starter items. The user reports **ALL GOOD** overall;
  [individual-case scope and remaining acceptance](docs/targeted-porting/GATHERING_WINDOWS_USER_REPORT.json)
  are recorded separately from CI. macOS gameplay remains NOT RUN.
- A standalone, passive local RLCraft 2.9.3 archive inspector.

## Supported testing scope

| Target | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Windows x64 | Destination native CI: 415 source tests passed, 14 platform/input skips; 68/68 installed cases. Earlier user-reported launch, both recipes, +1 Armor and inventory persistence; crafting/persistence in Survival and Creative | Rebuilt candidate and remaining physical installation, preservation, failure and gameplay edge cases |
| macOS Intel | Destination native DMG/architecture/helper checks; 426 source tests passed, 3 platform/input skips; 68/68 delivered cases | **All physical gameplay NOT RUN** |
| macOS Apple Silicon | Destination native DMG/architecture/helper checks; 426 source tests passed, 3 platform/input skips; 68/68 delivered cases | **All physical gameplay NOT RUN** |

Destination run [42144749724](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42144749724)
passed all three targets and release-file assembly. Download the
[separate verified packages, guides and checksums](release/0.1.0/README.md);
read the [final migration report](docs/migration/RELEASE_PREPARATION_REPORT.md).
The older Windows report belongs to source run
[42118750443](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42118750443).
Source run [42129264888](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42129264888)
passed all three platforms and 68/68 frozen cases per platform. These results do
not physically accept rebuilt packages or certify every GPU/OS version.

**Earlier loading-logo stalls and initially empty recipe output remain unresolved.**
Later successful launches/crafting did not establish their causes or fixes.
See [the physical evidence](docs/targeted-porting/RLCRAFT_CHAINMAIL_VERIFICATION.md).

## Important limitations

**Full RLCraft and FunCraft compatibility is not supported. Original Forge/Fabric
JAR execution, Java bridges and whole-Modpack Play are not supported.** Java Mods
Build/Test stays disabled. Static analysis or data carry-over is not gameplay proof.
Chainmail is one independently authored native replacement; the FunCraft backup
is another small utility, not execution of either original pack.

Windows packages are unsigned. Mac packages use development/ad hoc signing and
are not notarized unless a package-specific verified receipt explicitly says
otherwise. Obtain Minecraft resources legitimately; game assets, original
modpack binaries, accounts and credentials are not included. Rust/Cargo is not
needed for normal installed use; JDK 25 is needed for resource preparation.

## Development and provenance

The full verified tree and history were imported from
`Zeigen-ft/Herspers-Minecraft`, `feature/herps-java-compatibility`, commit
`962a1ada14ec553c540347c539c2b9c112c0270d`. Both repositories' original histories
are retained. See [migration provenance](docs/migration/README.md),
[developer setup](docs/HERPS-LAUNCHER.md) and [the source lock](upstream.lock.json).
Legacy game-only/Bedrock tools remain for history and regression coverage; they
are not part of this launcher's release downloads. Heavy native builds run from
PR validation or explicit workflow dispatch; historical pipelines remain available
manually without automatically building unrelated products in this repository.

## Licenses and attribution

Launcher code and the new packaging/docs use **[GPLv3](LICENSE)**. The initial
empty destination repository's MIT notice is preserved separately in
[licenses/Herps-Launcher-initial-MIT.txt](licenses/Herps-Launcher-initial-MIT.txt);
it does not relicense imported GPL code. Horizon keeps its MIT license and
notices under [licenses](licenses). Chainmail recipe attribution, Qt/PySide and
other dependency notices are retained. Legacy Cinnabar/Bedrock terms remain
separate; no Bedrock binaries are in this release set.

This project is unofficial and is not endorsed by Mojang, Microsoft, Horizon's
maintainers or third-party mod authors.
