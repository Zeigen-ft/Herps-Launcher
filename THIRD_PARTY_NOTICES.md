# Licences and third-party notices

The original Flint Gathering engine extension in `native/rlcraft_gathering/`
uses the MIT license retained beside its sources. Its tag-only `.hmod`, launcher
integration and tools use this repository's GPLv3 license. No original Java mod
source, Minecraft artwork or Forge implementation is included in this extension.

The launcher and independent packaging/tools are GPLv3; see [LICENSE](LICENSE).
Do not describe the imported launcher as MIT merely because the initial empty
Herps-Launcher repository used MIT. That notice remains at
[licenses/Herps-Launcher-initial-MIT.txt](licenses/Herps-Launcher-initial-MIT.txt).

The native Horizon engine retains its MIT copyright/licence and notices:
[Horizon licence](licenses/Horizon-LICENSE.txt) and
[Horizon third-party notices](licenses/Horizon-THIRD_PARTY_NOTICES.md).
The engine source/toolchain/resource version is pinned in [upstream.lock.json](upstream.lock.json).

Qt/PySide/shiboken have their own LGPL/GPL/commercial obligations. See
[Qt/PySide notice](licenses/Qt-PySide-NOTICE.md), [LGPLv3](licenses/LGPL-3.0.txt),
[GPLv3](LICENSE), and each platform package's resolved dependency
inventory/harvested notices. A licence file alone is not a complete corresponding-
source/library-replacement or legal certification. The historical
[security/distribution review](docs/herps/release-security.md) identifies open gates.

Chainmail recipe behavior is adapted from Craftable Chainmail's MIT source at
`0561a6cb57ad40edc1bf1ec7a1642e23096254fa`, copyright (c) 2019 Kfir Awad.
The native pack includes its permission notice and the new definitions' GPL
notice. It includes no original JAR/texture or Forge execution; artwork is a
reference to the user's prepared vanilla resources. See
[content notices](content/rlcraft_chainmail/NOTICE.txt).

Minecraft resources, trademarks and third-party modpacks retain their respective
rights. They are not bundled or relicensed. The project is unofficial and not
endorsed by Mojang/Microsoft or original mod authors.

Legacy Bedrock tools/history retain Cinnabar's separate PolyForm Noncommercial
terms where applicable; see [Bedrock licences](docs/BEDROCK-LICENSES.md). No
Cinnabar/Bedrock binaries are part of this launcher release set.

The CI release bundle includes `LICENSES.zip` with repository notices and
platform dependency/notice evidence. Review obligations before wider distribution;
no fresh full-dependency vulnerability or licensing clearance is asserted.
