# Flint Gathering 0.1.0 — verification

Implemented; native Windows candidate verification pending. **New physical
Windows gameplay and all native/physical macOS Stage 2 acceptance: NOT RUN.**

A separate `.hmod` tag opts a profile into a small extension using the existing
authoritative item-use hook, inventory helpers and block setter. Absent the tag,
the prior starter is unchanged. No public API, dependency or save schema is added.
The original Chainmail and Flint packages retain their identities and exact bytes.

Local Linux automated results: **465 collected, 448 passed, 17 platform/input
skips, zero failures**, with the real pinned port-pack helper. These include two
Qt add-on tests and managed-package/dependency/preservation safeguards. The actual
Rust transaction rules separately passed **12/12, zero skips**, on owned
inventory/block doubles. These do not execute the Game adapter in a live world.

Native Windows CI separately checks full client compilation, the native package
and item-tag loader, transaction rules, installed frozen workflows with developer
tools absent from PATH, existing installation lifecycle and both older packages.
Run IDs, delivered artifact hashes and final results will be recorded when known.

Automated refusals cover old engine metadata, absent/disabled starter, generic
import, default/saved profiles, missing consent, busy session, changed ownership
receipts/content, and failed receipt writes. Synthetic preservation sentinels
cover starter content, other profiles and FunCraft backups; they are not a real
backup restoration or gameplay. Old source caches remain intact.

The new tag-only package is 37,136 bytes, SHA-256
`177c3f4eefedd4f0e4eda4e54634efeee555e4b22dd13e0ec022733328fb87fd`.
See [installation and the physical checklist](NATIVE_SURVIVAL_STAGE_2.md).

Runtime hand/permission interactions, breakage, full inventories, coexistence and
save/load need new physical results. Earlier loading-logo/empty chainmail output
observations remain unresolved. Full RLCraft/FunCraft compatibility is unsupported.
Main, published releases and tags are not modified by this work.
