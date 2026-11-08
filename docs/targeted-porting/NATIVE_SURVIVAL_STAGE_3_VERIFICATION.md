# Woodcutting Progression 0.1.0 — verification

Implemented; native Windows build and verification pending. **All new physical
Windows/macOS gameplay and the natural stick-to-hatchet progression: NOT RUN.**
No Stage 3 Mac candidate has been built. Full native acceptance remains open.

The opt-in tag enables a small native guard at the existing dig-start and
destroy-block hooks. Survival logs require a usable main-hand hatchet/axe.
Earlier cancellation, non-log blocks and other modes retain their prior paths.
There is no custom drop or serialization path, public API change or Java bridge.
Existing packages, item IDs and profile/world/backup safeguards are preserved.

Local source regressions: **486 collected, 468 passed, 18 platform/input skips,
zero failures** using the real pinned port-pack helper. The actual Rust
progression policy also passed **9/9**, zero skips. These are automated checks,
not live Game hook execution or real gameplay.

The Windows workflow adds an eight-case native package/tag/policy/owned-loot
probe and an eight-case installed frozen workflow cohort with developer tools
absent from PATH. Existing source, installer, older content and SDK regressions
remain required. Native results, run IDs, hashes and any failures will be
recorded after the complete run finishes; no successful candidate is implied yet.

The new `.hmod` is 37,184 bytes, SHA-256
`52e3586e103e4893f37f2141983a7503fa01dacb494144056f86897089abbc13`.
See [installation and the physical checklist](NATIVE_SURVIVAL_STAGE_3.md).
The native fixture uses independently authored vanilla-shaped leaf/bush loot;
it does not establish the behavior of the user's legitimate prepared resources.

Physical early sticks, knapping/cutting/crafting, log rejection/harvesting,
main/off-hand, wear/breakage, full restart, preservation, failures and all macOS
cases remain open. Full RLCraft/FunCraft and No Tree Punching are unsupported.
The prior user reports remain scoped to their earlier stages. Earlier logo stalls
and initially empty chainmail output are not claimed resolved.

Only the development branch is changed. No release/tag or main merge is made.
