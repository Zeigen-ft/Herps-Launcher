# Windows resource recovery and game icon candidate

## Physical failure reported on 12 November 2026

The user reported Photon selection showing **Resource reload failed**, then
missing text glyphs and background graphics when an older profile was opened
with the newer application. Four supplied logs identify Horizon 0.7.6 and a
GeForce GTX 960. Three contain Windows error **448**, “The path cannot be
traversed because it contains an untrusted mount point.” Two subsequently save
a crash report. The fourth log reaches resource/world loading on Vulkan.
That successful startup does **not** prove Photon was selected or working.
The logs do not identify an exact launcher commit or include the earlier toast's
full reload exception; they establish a real resource-path failure that the
previous automated fixtures did not catch.

The screenshot and logs are **physical failure evidence**, not acceptance.
Previous CPU/source/installer passes remain valid only within their documented
automated scopes. Old-profile upgrade and Photon visual acceptance are blocked
pending a successful physical retest.

## Implemented correction

The resource-pack overlay used Windows directory junctions for untouched
resource directories, including font and title textures. A junction can be
created successfully and later fail traversal under Windows trust policy.

The Windows overlay now uses ordinary directories, hard-linked files where
possible, and copied files as the existing fallback. It creates no directory
mount points and does not weaken Windows security policy. It uses the new
`windows-files-v7` cache namespace, leaving old resource-pack cache trees untouched. It does
not delete/move/reset profiles, saves, settings, resource preparation, installed
mods or FunCraft backups. The first activation may rebuild more files; cross-volume
fallbacks may copy resource data. No performance gain is claimed.

Windows regression coverage uses an owned old-profile fixture with a dangling
legacy junction, font/panorama files and a world-preservation sentinel. It checks
new output directories have no reparse-point attribute, files are readable,
cache reuse/deselection work, and original resources, world and old cache remain
unchanged. This avoids requiring an actual restrictive trust policy in CI;
the user's exact Windows policy still requires a physical retest.

## Supplied game icon

The uploaded `download.ico` is actually PNG. Its bytes are preserved as
`packaging/icons/game-source.png`, SHA-256
`a2e0fda7cd2d16507cc29221495476d1da75d811a77229217e8e641e9aa31965`.
True Windows ICO, native game-window PNG and macOS ICNS assets are generated
without redesigning the artwork. Windows builds embed and read back the actual
game executable/entrypoint resource images. macOS packaging copies the icon and
sets `CFBundleIconFile`; native Mac appearance is NOT RUN. The independent Qt
launcher icon is unchanged. [Asset provenance](https://github.com/Zeigen-ft/Herps-Launcher/blob/4dff066cf488ba603e5aef85564c11713434ee64/packaging/icons/README.md).

## Verification and download

Successful Windows run **43167905016** completed all validation and post-job steps.

Tested code commit **`4dff066cf488ba603e5aef85564c11713434ee64`** includes
resource fix **`026e281c84baf179e10e2a4b82e7eb27b63ac930`** and the supplied icon.

[Download Windows recovery candidate](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43167905016/artifacts/13923915521),
artifact **Herps-Launcher-0.1.0-Windows-x86_64**, from
[run 43167905016](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43167905016).
Sign in with repository access if required. Current expiry: **10 February 2027**.
This is an internal unsigned candidate; no release or tag is published.

| Download/file | Bytes | Independently verified SHA-256 |
| --- | ---: | --- |
| Outer GitHub artifact ZIP | 240,758,221 | `597e8c5f27e3ff886af545603accf05f7133cc626059b53b7437b2e9bb889461` |
| `Herps-Launcher-0.1.0-Windows-x64-Setup.exe` inside it | 103,547,219 | `7c76ccded04141b3ab7fd2d07466aed40e3e5d28b06742924406fa52056a020b` |
| `Herps-Launcher-0.1.0-x86_64-pc-windows-msvc-dxrrq0oo.zip` inside it | 139,105,451 | `201c887565b47f7af69ceff8e234a45b7ce6a96e559d13f0140a2347d28b6d37` |
| Evidence artifact ZIP | 814,427 | `399e0425d0305a4a45f1aaa310b3fb2ea266d7ee372a97e48cd2b4ad01547786` |

[Checksums](WINDOWS-RESOURCE-RECOVERY-SHA256SUMS.txt) ·
[Machine-readable audit/results](WINDOWS-RESOURCE-RECOVERY-CI.json) ·
[Evidence download](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/43167905016/artifacts/13924155280).
Both outer ZIPs passed SHA-256 and entry-CRC checks. The actual installer/portable
hashes match both embedded receipts. All **30** modified engine-source/asset
postimages inside the portable archive match the current pinned manifest.
The actual packaged game executable's SHA-256 also matches the native Windows
icon read-back receipt: all **9** supplied icon images match, with ICO SHA-256
`c56671c5ba81b77e7df9e90afc02efbd91c72fa462f00815190d2caa1cd1cc38`.
That check loads the PE as data and does not execute it or prove visual appearance.
The original Photon ZIP/artwork/GLSL remain external user inputs, not bundled.

Extract the outer download **once** to a new folder, open PowerShell there, and run:

```powershell
Get-FileHash -LiteralPath '.\Herps-Launcher-0.1.0-Windows-x64-Setup.exe' -Algorithm SHA256
```

Compare with the installer row, then close both applications and run Setup.exe.
The portable alternative is the inner ZIP: extract it to a new folder and run
`Herps Launcher/Herps Launcher.exe`; keep the supplied folders together.
Neither normal route needs Rust/Cargo. Check the selected game installation
in Settings as described below. The bundled report is the build-time version;
this repository report adds the final post-build receipts.

| Verification | Result and scope |
| --- | --- |
| Native Windows source/desktop suite | **501 passed, 15 skipped** (516 collected); skipped cases listed in machine report |
| Windows renderer lightmap cases | **3 passed, 2 ignored** private-archive cases; 850 other tests filtered |
| Windows resource-overlay suite | **15 passed, 1 ignored** real-resource benchmark; 839 other tests filtered |
| New Windows old-cache/font/panorama/no-reparse/preservation regression | **PASS**, explicitly executed |
| Actual native game and entrypoint icon resource verification | **PASS**, real Windows PE resources; visual display NOT RUN |
| Existing Chainmail/Flint/Gathering/Woodcutting/Bandage native checks | **PASS**, unchanged gameplay features |
| Installed workflow/native-content cases | **98 passed, no failures/errors/skips**, with cargo/rustc/rustup absent from PATH |
| Installation/start/reinstall/uninstall/profile preservation fixtures | **PASS**, disposable data; not gameplay |
| Owned native mod compile/select/rollback | **PASS** |
| Portable Linux/Windows run 43167905387 | Linux **398 passed / 118 skipped**; Windows **411 passed / 105 skipped** |
| Local source regressions / exact private Photon CPU input | **497 passed / 19 skipped**; **4 passed / 0 skipped**, respectively |
| Local macOS bundle layout | **16 passed** on Linux fixtures; native Mac build/signing/display NOT RUN |

The real-resource performance benchmark was ignored because it needs prepared
Minecraft resources and real pack paths. The private full-client Photon/UB
integration tests remain ignored in CI. Source/platform skips remain skips.
No real gameplay, GPU appearance, FPS or exact reproduction of the user's
restrictive Windows trust policy is inferred from these results. Windows
**physical recovery is still NOT RUN**; the previous failure remains recorded.
Native Mac builds and all Mac physical acceptance remain NOT RUN.
The legacy experimental shader workflow was skipped by its existing repository
job guard; no full shader/GPU acceptance is claimed. Manual public-release file
assembly/publication is outside this candidate verification.

## Retest safely after the corrected candidate is available

1. Close the game and launcher. Keep a backup of valued worlds/profile data;
   do not delete the old profile, old cache or prepared resources.
2. Install/extract the corrected candidate in the normal way, retaining existing
   data. In **Settings**, check the **Herspers folder / .app** path. An explicitly
   selected older/portable game installation is intentionally preserved across
   launcher updates: if it points to the old copy, choose **Switch / update game
   installation…**, select the new candidate's `Herps Launcher/game/Herspers-Minecraft`
   folder, and use **Validate installation**. This selects the game binaries;
   it does not replace profile/save data. Open the previous profile at the title screen. Check text,
   buttons, panorama/background and profile selection before opening a valued world.
3. As an independent comparison, **Home → Clean startup** uses its own diagnostic
   game folder; it does not reset the selected profile. Do not treat a successful
   clean startup as proof the old profile is fixed.
4. In an explicitly selected disposable profile, place the original unchanged
   Photon ZIP in `resourcepacks`. Disable other lighting/shader packs and turn
   the separate Fullbright option OFF. Apply Photon, then test OFF → ON → OFF
   in the same dark area. Check both font/background readability and lighting.
5. Save/quit, close both applications, restart and reopen the same disposable
   world. Check world/inventory and pack-selection preservation. Check a second
   profile was not changed. Test Better Leaves together only after Photon alone.
6. Check the native game's Windows file/window/taskbar icon. Launcher shortcuts
   use the independent launcher icon. Mac Finder/Dock tests remain separate.

All these physical retests are **NOT RUN** until reported. If failure persists,
use **Home → Open launcher and game logs → logs**, select the newest `.log`, and
record the exact `resource reload failed`/error-448 lines. Redact private paths,
tokens, server details and account information. Do not upload game assets or
valuable worlds. Do not disable Windows mount-point protection or run as admin
as a proposed fix.
