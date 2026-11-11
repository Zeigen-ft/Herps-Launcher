# Java shader packs in Herspers 0.2.3

Herspers loads original Java shader ZIPs through its Rust renderer. Version 0.2.3 includes the compatibility changes; download each original pack from its author and keep the ZIP unchanged.

## Install a pack in Herspers

1. Use the Java **0.2.3** application. Earlier 0.2.2 downloads do not contain these compatibility fixes. Previously prepared resources can be reused.
2. Download an original shader ZIP from its author. The exact tested inputs are [Complementary Reimagined r5.5.1](https://github.com/ComplementaryDevelopment/ComplementaryReimagined/releases/download/latest/ComplementaryReimagined_r5.5.1.zip) and [Complementary Unbound r5.5.1](https://github.com/ComplementaryDevelopment/ComplementaryReimagined/releases/download/latest/ComplementaryUnbound_r5.5.1.zip). Keep each ZIP unextracted. These packs are by [Complementary Development](https://www.complementary.dev/).
3. Open **Options → Horizon Settings → Shader Packs → Open Pack Folder** in Herspers. Copy the ZIP there and select it in the Shader Packs menu. One pack runs at a time; selecting it again turns it off.

On Windows, the folder is:

```text
%LOCALAPPDATA%\Herspers Minecraft\game\shaderpacks
```

On macOS, it is `~/Library/Application Support/Herspers Minecraft/game/shaderpacks`. Shader packs go in `shaderpacks`, rather than `mods` or `resourcepacks`. The screenshot's Android catalogue is a separate launcher interface. Herspers does not bundle that catalogue or the three author packs.

These instructions apply to the Java client. The separate Bedrock 0.3.0 download has not received these shader changes. Use the game logs to check for shader errors.

## Fullbright Ubiquitous (the uploaded ZIP)

**Fullbright-UB-26.3 fub-7.0.zip**, by WRP, is a resource pack. Keep your original ZIP unextracted and copy it to:

```text
%LOCALAPPDATA%\Herspers Minecraft\game\resourcepacks
```

On macOS, use `~/Library/Application Support/Herspers Minecraft/game/resourcepacks`. In the game, open **Options → Resource Packs**, move Fullbright to the selected side and confirm. Remove it there to restore the normal lightmap. If another selected resource pack replaces `shaders/core/lightmap.fsh`, the higher-priority effective resource wins.

Herspers implements this exact pack's constant-white lightmap behavior in Rust. It does not compile arbitrary resource-pack lightmap programs. The compatibility profile is matched by the uploaded lightmap shader's SHA-256, independently of the ZIP's filename; the application's separate Fullbright option remains independent. Shader packs that calculate their own lighting can affect the combined appearance.

The uploaded ZIP and its artwork are not bundled or published; use the file you supplied. Its archive and lightmap fingerprints are recorded in the validation lock.

## Current scope

The uploaded **Photon [3.1.2-M1] by PrecisionZero** is also a fullbright
**resource pack**, distinct from the unrelated Iris Photon shader product.
The [Photon guide](PHOTON.md) explains the new fingerprint support, private-ZIP
installation, [candidate verification](PHOTON-VERIFICATION.md) and visual tests
that remain NOT RUN. Do not import that ZIP through the launcher's Shaders page.

| Pack | Exact input | Evidence and remaining work |
| --- | --- | --- |
| Complementary Reimagined | r5.5.1, original author release | Main programs translate for Overworld, Nether and End. Required GPU pipelines build in both terrain modes; custom noise/cloud-water inputs reach the renderer. An original terrain scene draws through actual shadow, geometry and post passes and produces finite, nonconstant GPU output. Full visual/gameplay parity remains unverified. |
| Complementary Unbound | r5.5.1, original author release | Same compatibility work and limits as Reimagined. |
| BSL Shaders | Not yet pinned | Official download/metadata access is blocked in the cloud environment. Its exact artifact, license and rendering behavior remain unverified. |

The exact author URLs and SHA-256 values used for the two Complementary shader inputs are in [the validation lock](https://github.com/Zeigen-ft/Herspers-Minecraft/blob/main/docs/shader-packs.lock.json). They are validation inputs downloaded into ignored `.cache/shader-packs`; they are not redistributed in the repository or native application packages. The r5.5.1 archives carry Complementary License Agreement 1.5. The author's current source repository carries a newer agreement, so the license is recorded per artifact.

## Implemented image inputs

- Global `texture.noise` / `texture.noisetex` images.
- Per-stage `texture.<stage>.<sampler>` encoded PNG images, including `gbuffers` overrides for translucent terrain and standard buffer aliases (`gaux4` / `colortex7`).
- Actual image dimensions, PNG colour/alpha conversion, repeat sampling and deduplicated uploads for shared images. Sampler overrides do not change render-target identities or buffer flips.
- Limits: 64 declarations, 16 MiB encoded bytes per image, 64 MiB aggregate encoded bytes, 64 MiB aggregate decoded pixels and the device's texture-size limit. Unsupported raw/3D descriptors and invalid images produce diagnostics.

## Known limits

The Rust renderer now supplies the packs' camera split/history, relative-eye, lightning and player-mood inputs. Camera splits use floor plus a nonnegative fractional remainder in double precision. Lightning uses camera-relative, world-aligned coordinates as described by the [current shader-format documentation](https://github.com/IrisShaders/docs/tree/main). The otherwise undocumented `velocity` value is defined in Herspers as actual player displacement speed in blocks per second; this is a Herspers convention, rather than a claim about another implementation's units.

`currentRenderedItemId` follows each rendered hand, dropped item, held item and framed item through `item.properties` mappings. Empty arms and passes outside item drawing use zero. Armor equipment and trim paths still lack item-level metadata, so full armor-specific shader effects are not established. Geometry/compute stages and several non-2D texture types remain unsupported. A successfully compiled pipeline cannot prove that every effect looks correct.

The cloud uses Mesa 25.0.7 software Vulkan (llvmpipe, LLVM 19.1.7) for isolated pipeline/readback checks. Both Complementary packs passed all 12 pack/dimension/terrain combinations, preserving 264 required pipeline creations. Both packs also draw original synthetic terrain through real shadow, geometry and post passes; final float pixels and terrain depth are read back and checked. An original hand fixture checks actual per-draw item IDs and changes across frames. HLSL and Metal shader source generation is checked for loaded programs, including entry-point reflection. These checks do not validate GTX 960 performance, native Windows/DX12 behavior, complete world rendering or every shader option. Real gameplay checks need the player's prepared game resources and target hardware.

## Developer validation

Use the existing isolated checkout; no extra Git worktree is needed. Prepare the tracked engine patches, then run the asset-free tests:

```sh
source scripts/cloud-env.sh
source_dir=$(python3 tools/prepare_upstream.py)
cd "$source_dir"
cargo +1.95.0 test --locked -p horizon-shaders --lib
cargo +1.95.0 test --locked -p horizon-shader-api
cargo +1.95.0 test --locked -p horizon-client-render --lib custom_texture_tests --no-default-features
```

With a verified Vulkan adapter and the two original ZIPs in `HORIZON_TEST_SHADER_PACKS`, explicitly run all ignored renderer checks. They fail if the adapter or required packs are missing; they do not silently pass:

```sh
cargo +1.95.0 test --locked -p horizon-client-render --lib custom_texture_tests --no-default-features -- --ignored --nocapture
```

The real-pack pipeline test additionally needs the original ZIPs listed in the lock file under `HORIZON_TEST_SHADER_PACKS`. It builds actual renderer geometry layouts in all three dimensions and both terrain paths. Intentional outputless cloud suppression is distinguished from skipped/failed required programs. Keep full-world tests in fresh isolated game homes, away from player saves.

BSL is by CaptTatsu: [author site](https://capttatsu.com/), [official Modrinth project](https://modrinth.com/shader/bsl-shaders). Its original ZIP is still needed to finish BSL-specific validation. The running cloud environment denies these official download hosts; the required domains are saved in the environment configuration draft but are not yet applied. Do not substitute an unverified mirror or relabel a different shader as BSL.
