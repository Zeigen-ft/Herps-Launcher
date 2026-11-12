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
`windows-files-v7` cache namespace, leaving old cache trees untouched. It does
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
launcher icon is unchanged. [Asset provenance](../packaging/icons/README.md).

## Verification and download

Candidate build: **PENDING**. Download links and independently verified hashes
will be recorded after native Windows CI passes. Local tests pass for binary
asset staging/path protection and macOS bundle icon layout; these are not native
Mac validation. No public release or main merge is part of this work.

## Retest safely after the corrected candidate is available

1. Close the game and launcher. Keep a backup of valued worlds/profile data;
   do not delete the old profile, old cache or prepared resources.
2. Install/extract the corrected candidate in the normal way, retaining existing
   data. Open the previous profile first at the title screen. Check text,
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
