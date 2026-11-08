# Better Leaves 9.6 for Herps

RLCraft development is [paused](targeted-porting/NATIVE_SURVIVAL_STATUS.md).
This is a separate optional **resource pack**, built for the launcher's existing
Minecraft **26.3** engine and resource format **97.1**. A launcher reinstall,
Java mod loader or Rust tools are not needed to use it.

The pack adapts the supplied `Better-Leaves-9.6.zip` by Motschen (MIT). Its
included 92 asset files remain byte-identical: 14 leaf blockstate definitions,
56 child models, eight shared models and 14 leaf textures. Metadata is narrowed
to the actual target version; unused models and Java-mod namespace overrides
are omitted. No engine, gameplay, block ID, collision, drop or world data changes.
The original MIT copyright/permission notice is retained.

## Download and install

The verified ZIP/download and CI evidence will be recorded below after cross-OS
verification. **Visual/FPS acceptance remains NOT RUN.**

1. Back up valued worlds and begin with a disposable named test profile.
2. Select that profile in Herps Launcher. On **Settings** choose **Open game data
   and saves**. Close running games, then create a `resourcepacks` folder there
   if it does not exist. Do not replace existing packs or other files.
3. Put `Herps-Better-Leaves-9.6-MC26.3.zip` into that folder **without unzipping it**.
   A GitHub Actions download has an outer wrapper ZIP: extract the wrapper once
   to find this actual inner pack and `SHA256SUMS.txt`.
4. Start the game through ordinary **PLAY**. Use the game's **Options → Resource
   Packs** screen to select Herps Better Leaves and apply the change; wait for
   resource reload. Keep existing pack choices unless deliberately testing order.
5. Use cutout/transparent leaves in Video Settings for the intended foliage.
   The engine persists `cutoutLeaves`; exact menu wording and rendered results
   still need physical checking. Clean startup uses a separate diagnostic profile.

All 14 supplied targets are retained: acacia, azalea, birch, cherry, dark oak,
flowering azalea, jungle, mangrove, oak, orange poplar, pale oak, red poplar,
spruce and yellow poplar leaves. Check types actually available in your prepared
game; assets do not add missing blocks or implement any Java mod.

## Real visual trial — NOT RUN

Compare the same scene with the pack enabled/disabled. Check fuller leaf geometry,
transparency, colours, shadows, held leaf blocks and no missing-texture squares.
Walk around and through foliage to check culling/flicker. Note GPU/driver,
graphics choices, other packs, location and FPS; no performance gain is claimed.
Check normal block breaking/drops, save/quit, fully restart both apps and reopen
the same world. Verify pack selection, worlds and other profiles remain intact.
Windows and macOS visual tests remain separate and NOT RUN until reported.

Undo by deselecting this pack in the in-game resource-pack screen and allowing
reload. With the game closed, move only its ZIP out of `resourcepacks` if desired.
Leave `options.txt`, saves, other packs and native mods in place. Texture packs
that replace leaves can conflict: this source is Lite-style and supplies its own
32×32 leaf textures. Test other pack combinations separately.

For a failure, collect launcher/game logs and record the leaf type, GPU/driver,
enabled packs and settings. Redact account details, tokens, private paths and
server addresses. Do not upload copyrighted resources or valuable saves.

## Rebuild and verification

The original upload SHA-256 is
`cbeeccd774f910ed270dbe9651d789a8f785d055499f846e466d86f9cae91e90`.
The builder can use the curated, individually pinned source or the exact original:

```text
python tools/build_better_leaves.py
python tools/build_better_leaves.py --original "path/to/Better-Leaves-9.6.zip"
```

The native verifier compiles the pinned engine's model/blockstate baker, PNG
decoder and unmodified metadata-format helpers. It checks 224 variants and
2,240 baked quads, including four unculled fringe quads per variant. The empty
vanilla parent used in the probe is an owned fixture; the installed pack instead
uses the user's legitimate Minecraft resources. No GPU, real world, interactive
pack selection or actual performance is verified by that probe. No untrusted
scripts or Java code are executed.
