# Herspers engine patches

`upstream.json` pins original engine changes over the archive in `upstream.lock.json`. Each entry identifies an exact file preimage, unified diff and result SHA-256. No third-party shader-pack programs are included.

For the supplied game artwork, entries whose `patch` names a `.png`, `.ico` or
`.icns` file are literal binary image replacements, limited to 4 MiB and to a
target with the same image extension. They use the same exact pre/postimage,
path protection and provenance checks; source code and Cargo.lock cannot use
that replacement path. The original user image and conversion provenance are
in `packaging/icons`.

Builds call `python3 tools/prepare_upstream.py`. It verifies the original archive, unpacks it into a separate temporary tree, checks and applies each patch, and atomically retains the result under `.cache/herspers-upstream/<commit>-<patch-hash>`. The original source cache and archive remain intact. `Cargo.lock` cannot be patched. A prepared tree with edits or unknown provenance is preserved and refused; use a fresh cache location for deliberate experiments.

The shader changes supply camera/player frame inputs and per-draw rendered-item IDs, and load encoded image inputs declared by the public `texture.*` properties format, bind per-stage sampler overrides, preserve logical render attachments, and retain the default noise texture when no override is supplied. Texture count, encoded/decoded memory and device dimensions are bounded. Tests use original generated images/programs; opt-in tests consume external packs as unchanged black-box inputs.

Underlying Horizon code is MIT licensed, copyright Ludovic Marie and the Horizon contributors, with its original license retained in `licenses/Horizon-LICENSE.txt` and copied into native packages. These engine patch additions follow that component's MIT license; the independent Herspers launchers and development tools retain the repository's GPLv3 license. Complementary and BSL remain separate products under their authors' terms.
