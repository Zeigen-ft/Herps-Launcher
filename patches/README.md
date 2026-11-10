# Herspers engine patches

`upstream.json` pins original engine changes over the archive in `upstream.lock.json`. Each entry identifies an exact file preimage, unified diff and result SHA-256. No third-party shader-pack programs are included.

Builds call `python3 tools/prepare_upstream.py`. It verifies the original archive, unpacks it into a separate temporary tree, checks and applies each patch, and atomically retains the result under `.cache/herspers-upstream/<commit>-<patch-hash>`. The original source cache and archive remain intact. `Cargo.lock` cannot be patched. A prepared tree with edits or unknown provenance is preserved and refused; use a fresh cache location for deliberate experiments.

The shader changes supply camera/player frame inputs and per-draw rendered-item IDs, and load encoded image inputs declared by the public `texture.*` properties format, bind per-stage sampler overrides, preserve logical render attachments, and retain the default noise texture when no override is supplied. Texture count, encoded/decoded memory and device dimensions are bounded. Tests use original generated images/programs; opt-in tests consume external packs as unchanged black-box inputs.

Underlying Horizon code is MIT licensed, copyright Ludovic Marie and the Horizon contributors, with its original license retained in `licenses/Horizon-LICENSE.txt` and copied into native packages. These engine patch additions follow that component's MIT license; the independent Herspers launchers and development tools retain the repository's GPLv3 license. Complementary and BSL remain separate products under their authors' terms.

## Verified Git source when a generated archive changes

A hosting-side repository rename can change the archive prefix and therefore its
SHA-256 even when the pinned Git commit is unchanged. Do not update the archive
checksum to accept that download. Instead, explicitly prepare from a clean Git
checkout at the exact commit recorded in `upstream.lock.json`:

```sh
python3 tools/prepare_upstream.py --git-source /path/to/pristine/engine-checkout
```

This mode checks the full HEAD, hashes the committed object bytes (commit, every
tree and every blob), checks actual checkout files against those blobs, and rejects
local changes, missing files and extra files (including ignored build outputs).
Git replacement refs are disabled. Links may only name a sibling regular file and
are materialized as files; submodules and unsafe paths are refused. The verified
objects are exported into a fresh staging tree before the existing patch preimage
and postimage SHA-256 checks run. Neither the source checkout nor `Cargo.lock` is
changed. Archive mode retains its original strict checksum verification.

For scripts that call the preparer internally, set the explicit
`HERPS_UPSTREAM_GIT_SOURCE` environment variable to that checkout. An explicit
`--git-source` overrides this variable; an explicit `--archive` selects archive
verification instead. With no flag or variable, archive mode remains the default.
The native launcher CI prepares this verified Git source before any engine builds,
runs both connected-texture rule and mesh-integration test suites, and retains
source-verification provenance with package evidence. No CI build or gameplay
success is established merely by configuring those steps.

Git-prepared caches have a `-git` suffix and record the verified commit/tree in
`source_verification` in `.herspers-prepared.json`. Keep Cargo outputs outside the
prepared tree (for example, pass `--target-dir /workspace/.horizon-target`) so its
retained content digest stays valid. Repeat the preparation command after changes
to the patch manifest; it reuses an intact matching cache or creates a new one.
