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
