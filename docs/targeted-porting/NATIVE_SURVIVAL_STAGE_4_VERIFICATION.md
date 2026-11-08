# Plant Fiber Bandage 0.1.0 — verification

Implementation and Windows candidate verification are in progress. **Physical
Windows/macOS Stage 4 gameplay: NOT RUN.** Stage 3 acceptance is not advanced.

This adds one independently authored data-only native item and one shapeless
recipe through the existing content/consumable API. No engine patch, public API,
Java execution, bridge, new asset, save schema or new health model is introduced.
The earlier four package hashes must remain unchanged.

The intended native probe checks real package parsing, item/components, recipes
in both grids, wrong inputs, earlier content and native Regeneration scheduling,
refreshing and effect-save tuples using owned fixtures. It does not execute held
use in a world or verify heart recovery, physical inventory consumption or world
persistence. Installed frozen and existing SDK/lifecycle checks remain required.

Final run IDs, source, hashes, failures and all skipped cases will be recorded
after required checks finish. No successful candidate or physical pass is implied.
See [installation and physical checklist](NATIVE_SURVIVAL_STAGE_4.md).

First native run `42477849660` at `8b05b321a1306a6dfdb76e2531d29dacdfa7ef23`
failed because the new definition put `minecraft:max_stack_size` in `components`.
The existing API requires top-level `max_stack_size`. The corrected package is
39,277 bytes, SHA-256 `dad328e28bc8d7d79d2002d5651af29dc77997bd3f00910c6e4021182b217ee1`.
An actual local native parser rejects the original and accepts the corrected
definition (two checks); full local tests pass, 481/500 with 19 skips.
The failed evidence ZIP (artifact `13616561074`, 23,982 bytes) was downloaded
and verified as `8276b7aa842772966b275d56d2c4c1dd2175daa88f6af9c35e61a2d4fb34453e`.
No earlier package or engine patch changed. A fresh native candidate is required.
