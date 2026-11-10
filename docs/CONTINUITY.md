# Continuity textures in native Herps

Herps' native renderer port targets the **default included textures** from the
user-supplied `continuity-3.0.1+26.3.jar`. This is not Fabric Java execution or a
conversion of the whole Continuity mod. The implemented resource rule methods
are `ctm`, `horizontal` and `top`; all other Continuity methods and arbitrary
third-party connected-texture packs remain outside this input's tested scope.
The newer source also supports opt-in emissive overlays for baked block and
item models; see the pack format and build status below.

The existing unmodified Herps releases do not gain connected textures by copying
the JAR or this extracted pack into a folder. Install a game build containing the
native renderer changes first. Source/compiler checks and in-game rendering are
separate evidence; do not treat extraction or metadata inspection as gameplay
validation. Native Windows/macOS packaging and physical gameplay must be
reported separately for each platform.

## Verified native downloads

**These downloads contain connected textures only. They predate the emissive
source changes and must not be used to test emissive support.**

[Native run 42750869099](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42750869099)
passed Windows x64, Mac Apple Silicon, Mac Intel and final release-file assembly.
The binaries were built from commit
`2571d6b7c2d775c8ef085a0243879caf37ef6698`. Build, CTM tests and delivered-app
checks passed; physical gameplay with prepared vanilla resources remains unverified.

| Platform | CI artifact |
| --- | --- |
| Windows x64 | [Installer and portable package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42750869099/artifacts/13735706335) |
| Mac Apple Silicon | [DMG package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42750869099/artifacts/13733574893) |
| Mac Intel | [DMG package](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42750869099/artifacts/13734339993) |
| All platforms | [Combined release-ready files and checksums](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42750869099/artifacts/13735960937) |

GitHub downloads an **outer ZIP**. Extract it before using the installer or DMG.
For Windows portable use, also extract the complete inner portable ZIP. These are
CI artifacts; no release or tag was published. Existing release downloads linked
elsewhere in the repository predate this change.

The author texture pack is prepared locally from your original JAR using the
instructions below; third-party artwork is not included in the source repository.

## Prepare the pack

Keep the original JAR locally. From the repository root, run:

```sh
python3 tools/prepare_continuity_pack.py \
  /path/to/continuity-3.0.1+26.3.jar \
  /path/to/Continuity-Default-Herps-26.3.zip
```

On Windows, `python` may replace `python3`. The command validates archive paths,
limits and metadata without executing Java or reading Java method bodies. It
extracts the default textures and properties, preserves the provided license,
records the original JAR's SHA-256, and prints the output hash. Repeated runs are
deterministic; a different pre-existing output is preserved and refused.

The **Programmer Art variant is omitted** because the native resource overlay
does not currently preserve the origin needed to evaluate its
`resourceCondition=...@programmer_art` checks. The separate glass-pane culling
companion is also omitted; copying it alone can remove required pane faces.
No Java classes, Fabric entrypoints or mod settings are included. Continuity's
included connected-glass artwork does not add emissive areas by itself.

After installing the rebuilt native game, put the resulting ZIP, unextracted,
in the **active profile's** `resourcepacks` folder and enable it under
**Options → Resource Packs**. The default profile uses:

- Windows: `%LOCALAPPDATA%\Herspers Minecraft\game\resourcepacks`
- macOS: `~/Library/Application Support/Herspers Minecraft/game/resourcepacks`

Use default vanilla artwork rather than Programmer Art or replacement glass
textures. Named profiles have separate resource-pack directories.

### Manual preparation without Python

1. Make a copy of your original JAR and rename the copy with a `.zip` extension.
2. Open that ZIP and copy its `resourcepacks/default` folder into your active
   game's `resourcepacks` folder. Rename the copied folder `Continuity-Default`.
3. Inside that copied folder, remove
   `assets/continuity/optifine/ctm/programmer_art`. Keep the `default` sibling.
4. Replace the copied folder's `pack.mcmeta` with the exact JSON below. Ensure
   the filename remains `pack.mcmeta`, rather than `pack.mcmeta.txt`.
5. Copy `LICENSE_continuity` from the JAR's root into the copied pack folder.
6. Enable `Continuity-Default` in the rebuilt game's **Options → Resource Packs**.

```json
{
  "pack": {
    "pack_format": 97,
    "min_format": [97, 1],
    "max_format": [97, 1],
    "description": "Continuity default textures by PepperCode1 — native Herps CTM"
  }
}
```

The resulting pack folder must contain `pack.mcmeta` and `assets` directly.
This carries over the selected default texture data; it does not execute the
original Fabric mod.

## Emissive block and item textures

An emissive resource pack supplies this file:

```properties
# assets/minecraft/optifine/emissive.properties
suffix.emissive=_e
```

For a base image such as `assets/minecraft/textures/block/stone.png`, add
`stone_e.png` beside it. Only the overlay's visible pixels stay bright in dark
lighting. Leave its other pixels transparent. Other valid suffixes and resource
namespaces work too; each sibling stays in its base image's namespace.

The native implementation preserves the ordinary base, UVs, model and biome
tints, and overlay alpha. Emissive overlays bypass lightmap darkness, ambient
occlusion and directional shading while retaining fog and occlusion by other
geometry. They do not illuminate nearby blocks. Animated siblings keep their
own `.png.mcmeta`. A selected connected-texture tile can have its own sibling,
for example `assets/example/optifine/ctm/glass/0_e.png`; the original sprite's
emissive image is not applied to a different CTM tile.

Baked item models support overlays in inventory/GUI, held and world rendering,
including namespaced atlas aliases. The base retains its enchantment glint;
the added emissive overlay does not add a second glint. Special item renderers,
entity skins, armour and arbitrary Continuity CTM methods are outside this
implementation's scope.

Solid overlays use alpha cutout; translucent bases retain alpha blending.
Packs enabling emissive textures use classic transparency to keep coplanar
overlays ordered correctly. The saved improved-transparency preference is
preserved and takes effect again after those packs are removed and reloaded.
Custom shader packs control their own lighting and are not covered by the
native emissive guarantee.

The emissive changes passed the local checks below; native packages are
undergoing rebuild. The older verified artifacts above remain the
connected-texture baseline until a new run is recorded here. No physical
gameplay validation is claimed.

### Emissive source validation

- All 36 checksum-locked patch postimages prepared successfully and match the
  tested development tree. Patch digest:
  `c4a7462190943e897755cc19eadc974f7d84b58f1bde80e0681858d8296c58e6`.
- Full Linux renderer library: **863 passed, 27 ignored**. The ignored local
  input/GPU benchmark cases retain their existing opt-in gates.
- Mandatory software-Vulkan rasterization exercised solid/translucent terrain
  and items with black, dim and bright lightmaps. All four GPU cases ran with
  `HERPS_REQUIRE_EMISSIVE_GPU=1`; missing adapters could not silently pass.
- Item GUI/world/tint/glint/reload regressions: **4 passed**.
- Linux client compiled from the saved source with `--no-default-features`; its
  isolated `--help` smoke check passed.
- Launcher/source/packaging Python suite with the real native helper:
  **423 passed, 17 skipped** (440 total).

Native CI now runs the config, sprites, block mesh, item atlas, material order,
GPU and item-model regressions before packaging. Each run saves a
`herps-native-engine-tests.json` receipt tied to the patch and source tree
digests. Headless GPU availability is explicitly recorded separately from
passing CPU tests and from physical gameplay.

## Attribution and repository contents

Continuity is by **PepperCode1**, with `LGPL-3.0-only` declared in the supplied
JAR's `fabric.mod.json`. Its provided `LICENSE_continuity` is copied unchanged
into the extracted pack. See the author's project and source at
<https://github.com/PepperCode1/Continuity>. The extraction does not relicense
its artwork or properties. The repository does not contain the JAR, author
textures or generated extracted pack; tests use small synthetic fixtures.

The native implementation is original Rust code based on the public connected
texture file format and resource input, not a translation of Continuity's Java
implementation.

## Build and validate the engine

The original archive SHA-256 remains enforced. Upstream was renamed, changing
GitHub's generated archive bytes; an explicit Git-source mode verifies the
unchanged pinned commit, its tree and blob hashes, and every patch preimage and
postimage instead. See [source preparation](../patches/README.md).

The **Build Herps Launcher** workflow, with `platform: all`, prepares that
verified Git source and runs the new rule, sprite and section-mesher tests on
Windows x64, Mac ARM64 and Mac Intel before packaging. This source change does
not publish a release or supply signing/notarization credentials. A successful
Linux development build does not establish native package or gameplay results.

For a Linux developer check from the existing checkout:

```sh
source scripts/cloud-env.sh
export HERPS_UPSTREAM_GIT_SOURCE=/path/to/clean/pinned/upstream-checkout
source_dir=$(python3 tools/prepare_upstream.py)
cargo +1.95.0 test --locked --manifest-path "$source_dir/Cargo.toml" \
  -p horizon-client-render --lib connected_textures::tests
cargo +1.95.0 test --locked --manifest-path "$source_dir/Cargo.toml" \
  -p horizon-client-render --lib sprites::ctm_resource_tests
cargo +1.95.0 test --locked --manifest-path "$source_dir/Cargo.toml" \
  -p horizon-client-render --lib mesher::continuity_tests
HERPS_CONTINUITY_PACK=/path/to/Continuity-Default-Herps-26.3.zip \
  cargo +1.95.0 test --locked --manifest-path "$source_dir/Cargo.toml" \
  -p horizon-client-render --lib \
  mesher::continuity_tests::uploaded_default_pack_loads_all_42_rules_and_changes_real_glass_mesh \
  -- --ignored --exact --nocapture
```

The final command explicitly runs the otherwise ignored local-input test. It
loads all 42 extracted rules and checks actual section-mesh sprite selection
with the supplied images and generated fixture resources. It does not use the
player's prepared vanilla resources or prove physical gameplay.

For the broader renderer suite on a cloud machine without a suitable Vulkan
driver, the installed Chromium SwiftShader ICD can provide software Vulkan:

```sh
mkdir -p /workspace/.local/vulkan-runtime /workspace/.local/vulkan-cache
chmod 700 /workspace/.local/vulkan-runtime
export VK_DRIVER_FILES=/usr/lib/chromium/vk_swiftshader_icd.json
export VK_ICD_FILENAMES="$VK_DRIVER_FILES"
export XDG_RUNTIME_DIR=/workspace/.local/vulkan-runtime
export XDG_CACHE_HOME=/workspace/.local/vulkan-cache
cargo +1.95.0 test --locked --manifest-path "$source_dir/Cargo.toml" \
  -p horizon-client-render --lib
```

Use this only where that installed ICD exists; otherwise use a suitable native
Vulkan, Metal or DX12 adapter. GLES cannot run the existing optical-flow storage
format and post-processing depth-texture checks. Do not disable those tests to
claim a passing renderer suite.

## Connected-texture baseline evidence

- Verified Git-source preparation and its repeat run passed; the original
  archive pin was not changed. All 26 patch postimages verified.
- The Linux development client compiled from the saved prepared source with
  `--no-default-features`, and its `--help` smoke check passed.
- Native CTM rules: 12 passed. Resource-sprite tests: 2 passed. Generated real
  section-mesher tests: 4 passed. The exact uploaded-pack test was also run
  explicitly and passed, loading all 42 rules.
- Renderer library suite with software Vulkan: 847 passed, 27 ignored.
- Launcher/source/packaging Python suite using the real native helper:
  423 passed, 17 skipped.
- Strict Clippy remains blocked by existing upstream warnings promoted to
  errors in unchanged files (`camera.rs`, `graphics_ui.rs`, `post_chain.rs`,
  and dependency code). No lint suppression or unrelated upstream edits were
  added to make it pass.

Windows x64, Mac ARM64 and Mac Intel packages have now passed native build and
delivered-app verification in run 42750869099, including the final checksum and
release-file assembly gate. The first native run,
[42747948172](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42747948172),
reached the Python integration suite and exposed test-fixture portability issues:
macOS temporary paths through `/var`, Windows Git line endings, and Windows ZIP
filename normalization. Those cases are corrected without weakening source
or archive validation. The source/pack fixtures now run before costly native
compilation as well as in the full suite.

The next native run,
[42749476219](https://github.com/Zeigen-ft/Herps-Launcher/actions/runs/42749476219),
passed those suites on Mac ARM64 but exposed a Windows race in two sprite tests
that shared a clock-based temporary directory. A forced timestamp collision
reproduced the missing-file error. Their fixture now reserves unique directories
with an atomic counter and exclusive creation; both unchanged test bodies pass
concurrently without depending on clock precision.

Pushes to `codex/continuity-default-textures` in this repository trigger all three
native targets and, after success, assembly of release-ready files. Other push
guards are unchanged. This is internal CI artifact preparation, not release
publication. This cloud instance still denies the GitHub API; public workflow
and job pages provide status and failure annotations for diagnosis. Physical
gameplay with prepared vanilla resources remains unverified on every platform.
