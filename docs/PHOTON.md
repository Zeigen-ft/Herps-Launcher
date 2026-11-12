# Photon 3.1.2-M1 fullbright for Herps

This supports your uploaded **Photon [3.1.2-M1].zip by PrecisionZero**.
It is a Minecraft 26.3 **resource pack** whose one shader requests a white
lightmap. It is a different product from the full Iris Photon shader pack.
There are no new shadows, reflections, bloom or cinematic effects in this upload.
RLCraft development remains paused.

Herps implements the lighting effect using its existing native Rust lightmap.
It recognizes only the exact reviewed fragment fingerprint, keeps normal
lighting for unknown fragments, and preserves Fullbright UB 7.0 support.
No GLSL from this ZIP is compiled or executed. Selection stays optional; no
pack is installed or enabled automatically. Gameplay light levels, mob spawning
rules and world data are not altered by this rendering change.

## Use it

The original ZIP, artwork and shader cannot be included in a download: the
author's licence reserves redistribution rights. Keep **your own uploaded ZIP**.
Written author permission is required before redistributing any of its contents.
The compatibility code contains fingerprints and original Rust only.

The new original-ZIP recognition needs the **Photon Windows test candidate**
identified in [Windows resource recovery](WINDOWS-RESOURCE-RECOVERY.md).
The earlier candidate has a reported resource-path failure; its historical
[verification](PHOTON-VERIFICATION.md) does not accept physical gameplay.
Older builds can instead
use their existing **Options → Horizon Settings → Extras → Fullbright** switch
for the native lighting effect. Exact on-screen wording still needs physical
confirmation. Neither route is visually accepted by these automated tests.

1. Close the game and back up valued worlds. Start with a disposable test profile.
2. In Herps Launcher, select that profile. Open **Settings → Open game data and
   saves**. This locates the selected profile; do not assume the default profile's
   folder is the right one.
3. Create a `resourcepacks` folder there if needed. Copy your unchanged
   `Photon [3.1.2-M1].zip` into it. **Do not unzip it.** Do not import this file
   through the launcher's Shaders page or put it in `shaderpacks` or `mods`.
4. Start ordinary **PLAY**, open **Options → Resource Packs**, select Photon
   and apply the change. Interactive reload remains unverified on physical hardware.
5. For an isolated test, turn the separate **Fullbright** switch **OFF** and
   disable other lighting/shader packs temporarily. The separate switch can
   otherwise keep everything bright after Photon is deselected.
6. Visit a dark, enclosed area in your disposable world. Compare Photon OFF,
   ON, and OFF again from the same position. Enabled should brighten blocks and
   entities; disabled should restore normal lighting. This remains **NOT RUN**
   until you report the result.
7. Save and quit; completely close both applications, restart and reopen the
   same profile/world. Check selection, inventory and world preservation.
8. To undo, deselect Photon in Resource Packs and apply. With the game closed,
   remove only its ZIP if desired. Keep saves, other packs and profile files.

Other packs that replace `assets/minecraft/shaders/core/lightmap.fsh` compete
by resource priority: the effective fragment is the one recognized. Shader
packs that perform their own lighting can change the appearance. Fog and
post-processing are separate from the lightmap; a white lightmap does not
prove that every pixel will be white or every scene equally bright.

## Check your original ZIP

In Windows PowerShell, in the folder containing the file:

```powershell
Get-FileHash -LiteralPath '.\Photon [3.1.2-M1].zip' -Algorithm SHA256
```

Expect exactly **3,657 bytes** and:

```text
a51dc9c24afa8d98f75fa88abe6308774625cd10a126c62e4b1fa4d0254ab79e
```

The brackets require `-LiteralPath`. Do not edit/re-save the shader: its exact
CRLF bytes are fingerprinted. Renaming the ZIP does not change its contents.

## Report your visual result

Report OS version, GPU/driver, candidate run, selected profile, other packs,
Fullbright switch state, and OFF/ON/OFF results. Check cave blocks, entities,
normal play, resource reload, save/relaunch and another profile's unchanged
pack selection. Windows and both Mac architectures are separate acceptance
targets; all remain **NOT RUN** for this Photon change.

If it stays bright when disabled, check the separate Fullbright switch and
other active packs first. If it stays dark, confirm candidate version, hash,
profile folder and pack priority. These are diagnostic checks, not claims that
all failures are fixed. Collect launcher/game logs from the selected profile
and redact usernames, private paths, server addresses and tokens. Do not share
the copyrighted ZIP, game resources or valuable worlds in a failure report.

## Developer verification

```text
python tools/verify_fullbright.py --fetch
python tools/verify_fullbright.py --photon "path/to/Photon [3.1.2-M1].zip"
```

The first command runs three CPU tests from the actual pinned renderer source.
The second adds one private-input CPU case without uploading the ZIP. The tool
also uses the engine's exact `Sky` type and verifies probe dependencies are a
subset of the pinned lock. These are not pack-screen, GPU or gameplay checks.
Two opt-in full-client overlay tests remain in the renderer; set the appropriate
private input variable and run them explicitly in a complete renderer build.

No Java bridge, arbitrary core-shader execution, engine rewrite or release is
included. This does not add Java-modpack compatibility.
