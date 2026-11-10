# Continuity included textures in native Herps

Herps' native renderer port targets the **default included textures** from the
user-supplied `continuity-3.0.1+26.3.jar`. This is not Fabric Java execution or a
conversion of the whole Continuity mod. The implemented resource rule methods
are `ctm`, `horizontal` and `top`; all other Continuity methods and arbitrary
third-party connected-texture packs remain outside this input's tested scope.

The existing unmodified Herps releases do not gain connected textures by copying
the JAR or this extracted pack into a folder. Install a game build containing the
native renderer changes first. Source/compiler checks and in-game rendering are
separate evidence; do not treat extraction or metadata inspection as gameplay
validation. Native Windows/macOS packaging and physical gameplay must be
reported separately for each platform.

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
No Java classes, Fabric entrypoints or mod settings are included. This pack does
not implement Continuity's arbitrary emissive-texture features.

After installing the rebuilt native game, put the resulting ZIP, unextracted,
in the **active profile's** `resourcepacks` folder and enable it under
**Options → Resource Packs**. The default profile uses:

- Windows: `%LOCALAPPDATA%\Herspers Minecraft\game\resourcepacks`
- macOS: `~/Library/Application Support/Herspers Minecraft/game/resourcepacks`

Use default vanilla artwork rather than Programmer Art or replacement glass
textures. Named profiles have separate resource-pack directories.

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

## Current local evidence and remaining gates

- Verified Git-source preparation and its repeat run passed; the original
  archive pin was not changed. All 26 patch postimages verified.
- The Linux development client compiled from the saved prepared source with
  `--no-default-features`, and its `--help` smoke check passed.
- Native CTM rules: 12 passed. Resource-sprite tests: 2 passed. Generated real
  section-mesher tests: 4 passed. The exact uploaded-pack test was also run
  explicitly and passed, loading all 42 rules.
- Renderer library suite with software Vulkan: 847 passed, 27 ignored.
- Launcher/source/packaging Python suite using the real native helper:
  422 passed, 17 skipped.
- Strict Clippy remains blocked by existing upstream warnings promoted to
  errors in unchanged files (`camera.rs`, `graphics_ui.rs`, `post_chain.rs`,
  and dependency code). No lint suppression or unrelated upstream edits were
  added to make it pass.

Windows x64, Mac ARM64 and Mac Intel installers have **not** been built for this
change. This cloud instance denies HTTPS access to `api.github.com`, so the native
Actions runs could not be started. Add that domain to the environment's allowed
destinations before resuming the native build/verification workflow. No release
has been published, and physical gameplay with prepared vanilla resources is
still unverified on every platform.
