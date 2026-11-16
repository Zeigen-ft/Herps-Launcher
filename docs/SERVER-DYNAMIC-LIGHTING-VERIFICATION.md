# Herps 26.3 server lighting: internal test candidate

Status: **experimental; native server runtime and physical multiplayer acceptance NOT RUN**.
This is a separate data-only add-on, not a new launcher executable, OptiFine
implementation, Java compatibility bridge, or public release.

## Input and scope

The user selected **Herps native server, 26.3**. Their uploaded
`dynamic-lighting-1.0.jar` was inspected only as ZIP data:

| Input fact | Verified value |
| --- | --- |
| SHA-256 | `f4c66fc343c03532be4028859e8a0bd510c182348b8649b63301865f99239e82` |
| Size | 242,779 bytes |
| ZIP entries | 84 |
| Java classes | 0 |
| Metadata author/license | quillphen / AGPL-3.0-only |
| Declared datapack formats | 48 through 128 |

Its reachable functions place real light blocks; it is not merely a client
rendering effect. Static inspection also found malformed legacy commands,
overlapping tier tests, a disable function whose flag is ignored by its tick
function, and a broad cleanup fill. These are observations from source, not
an executed diagnosis of the original pack. The original JAR and its commands
were never executed or installed into an existing world.

The small adaptation uses existing native commands and datapack loading;
there are no engine/runtime changes. It includes held main/offhand items,
bounded nearby drops, four light tiers and owner-tagged cleanup in the three
standard dimensions. It only places in ordinary air; no underwater, cave_air,
void_air, mob/on-fire or full OptiFine behavior is claimed. See the
[installation and acceptance guide](SERVER-DYNAMIC-LIGHTING.md).

## Preservation boundaries

* The user explicitly selects an existing, stopped, disposable world.
* The installer verifies the pack SHA-256 and holds the world's native-style
  byte-range session lock throughout copying and installation.
* Every persistent world file is copied to a new sibling backup and verified
  against its source SHA-256. Transient `session.lock` is excluded explicitly.
* Existing saves are never restored over or overwritten; existing installs,
  links/junctions and active locks are refused. The installer does not start
  the server, accept its EULA, change authentication, or edit server settings.
* Lighting starts disabled on first load. Real light blocks may affect spawning
  and light checks. Cleanup only applies to loaded, owner-tagged markers and
  matching temporary light states; there is no broad fill.
* Unloaded chunks and identical user replacement of an owned light remain
  limitations. Keep the pack installed but disabled while visiting old areas
  before removal. Use the pre-test backup for a complete independent rollback.

Existing launcher, profile, native gameplay stages, FunCraft backups, resource
recovery and icon code are unchanged. RLCraft development remains paused.

## Automated verification

Candidate source: `2420d31201a7693d0c1e94984c0bf118a5f2df7e` on
`feature/photon-fullbright`. Native parser source remains the checksum-pinned
engine `7301f6fdd7f470b11317276e7a11b4dc615c137a` with existing patches.

The separate Windows CI checks package dependency closure, safe mutation
boundaries, disabled defaults, tier ordering, complete preferred source and
byte-identical bundle rebuilding; it then exercises installation with Windows
PowerShell 5 and parses every function using the actual native command parser.
No uploaded Java or original datapack code is run.

Final candidate runs both **PASS**:

| Evidence | Result |
| --- | --- |
| [Windows add-on run 43913856821](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43913856821) | Four package/source tests; 20 Windows installer assertions; 36 commands parsed at native permission 2; three deliberately invalid commands rejected |
| [Regression run 43913856837](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43913856837) | Windows: 415 passes, 105 skips; Linux: 402 passes, 118 skips; 520 total cases per job |
| Independent downloaded-artifact audit | GitHub outer digest, every inner file hash and pack checked; delivered Windows pack and bundle byte-identical to Linux rebuild |

Windows CI is automated runner evidence, **not physical Windows 11 gameplay**.
The native test is command parsing only; it does not start a game server or
prove that real lighting and network updates work.

## Download and checksums

Artifact: **Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test**, ID **14248758756**,
[download from the successful run](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43913856821/artifacts/14248758756).
GitHub sign-in may be required. The artifact expires **2027-02-14 17:01:15 UTC**.
Extract the outer artifact, then the inner Windows test bundle. Do not confuse
the outer artifact ZIP with the inner bundle when checking hashes.

| File/layer | Bytes | SHA-256 |
| --- | ---: | --- |
| GitHub artifact ZIP (outer wrapper) | 42,339 | `e2d04664dd5f5e96da8d3098a4a05dbc6b179f0b6e1d576837132a24da7430cf` |
| `Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test.zip` (inner bundle) | 59,506 | `2f8277a983170cddb594a8e7cf1c1c32d336bd1f1124138afccd9fd8859d5c18` |
| `Herps-Server-Dynamic-Lighting-0.1.0.zip` (datapack inside bundle) | 18,165 | `11dff393eb1e85e5692eeb009226d04478a5f745f0ba623cabf8cfe9cda8fe8d` |

The bundle includes its installer, beginner README, AGPL license/notices,
complete preferred source and inner-file `SHA256SUMS.txt`. See the
[machine-readable receipt](SERVER-DYNAMIC-LIGHTING-CI.json). This is a separate
add-on for an existing Herps 26.3 installation; no new launcher build is needed.
The previous Windows resource-recovery launcher candidate remains run
[43167905016](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43167905016);
its [verification report](WINDOWS-RESOURCE-RECOVERY.md) retains its separate
installer checksums and acceptance limitations.

The local full regression run executed 520 tests: 500 passed, 19 skipped and
one existing native launcher test failed because the sandbox prohibited its
owned loopback port. Rerunning that test module with loopback permission passed
all four tests, including its 31 native cases. This was an environment restriction;
no production code was changed to mask it.

An earlier tooling run at `8c510280c0bf058afc450d95baa4412eeabc92b3`,
[43912315635](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43912315635),
passed both jobs: Windows ran 520 tests with 105 skips (415 passes); Linux ran
520 with 118 skips (402 passes). Missing backend/native/host-specific fixtures
remain skips, not acceptance evidence. The final candidate repeats these counts.

## Failures and corrections

* The first attempt to dispatch a newly added workflow by name returned HTTP
  404 because it was not registered on the default branch. A path-filtered
  push trigger was added only on this feature branch; main was not modified.
* Run [43912129286](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43912129286)
  passed its 20 Windows installer assertions but the step failed because an
  expected corrupt-pack refusal left the child exit code as 1. The fixture
  harness now exits 0 only after all assertions and cleanup complete.
* Corrected run [43912315579](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43912315579)
  passed: four package tests, 20 Windows filesystem/installer assertions,
  all 36 native command parses at permission level 2 and rejection of three
  deliberately invalid commands. It contains the earlier guide; use the final
  documented candidate below rather than treating the old bundle as current.
* Run [43912775810](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43912775810)
  passed CI, but independent artifact comparison exposed different Windows/Unix
  ZIP host metadata. Its extracted pack contents matched; its cross-platform
  archive checksums did not. The builder now pins that metadata to Unix=3 and
  the regression checks both nested archives. The old bundle is superseded.
* Direct CLI artifact retrieval encountered a temporary-download HTTP 403.
  Retrieval through the GitHub connector succeeded; only validated artifact
  bytes, not temporary signed URLs, belong in the verification receipts.

## Open native acceptance

Every item below is **NOT RUN**, regardless of successful CI:

* Real native dedicated-server world startup with this pack and console enable.
* Actual server lighting visible to two connected players with client-only
  dynamic lights disabled; main/offhand, drops and tier transitions.
* Movement, logout, death, teleport, dimensions, cleanup and normal/crash restart.
* World, inventory and player preservation after real gameplay and save/reload.
* Restore into a separate world and load/play that restored world.
* Long-session performance, many players/items, flicker, custom dimensions,
  interactions with other datapacks and physical macOS hosting/client testing.

The previous resource-recovery candidate's physical old-profile/Photon retest
also remains open. This separate server pack does not establish that those
earlier loading and rendering observations are resolved on the user's PC.

OptiFine shaders, zoom, connected textures, a complete native OptiFine remake,
Java mod execution and full RLCraft/FunCraft compatibility are not implemented
by this pack. No original proprietary mods were downloaded, and no public
release, tag or main-branch merge was created.
