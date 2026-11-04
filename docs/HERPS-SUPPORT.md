# Herps Launcher candidate support contract

Status: internal release-candidate verification, not a stable public release.
Applies to the launcher; a game-only app's macOS 11 declaration is not the Qt
launcher's support floor. Bedrock is a separate product.

| Target | Candidate OS policy | Evidence and remaining gate |
| --- | --- | --- |
| Windows x64 | Windows 11 is the primary candidate target | Native CI builds/installer smoke; real clean-machine desktop/gameplay acceptance pending |
| Windows 10 x64 | Legacy experimental compatibility only | No Windows 10-specific interactive evidence; not stable-supported |
| Mac ARM64 | macOS 15 is the current candidate target | Native delivered-DMG automation; physical interactive acceptance pending |
| Mac Intel x86_64 | macOS 15 is the current candidate target | Native delivered-DMG automation; physical interactive acceptance pending |
| macOS 12–14 | Compatibility targets, experimental until individually tested | Qt 6.8 requires macOS 12+; CI on 15 does not certify older OS versions |
| macOS 11 and older | Launcher unsupported | Game-only package minimum does not establish launcher compatibility |
| Other architectures / Linux desktop | No supported end-user package | Linux tests are developer evidence, not a supported distribution |

No target is declared stable-supported before its manual acceptance gate passes.
Rust/Cargo is not an end-user requirement for passive metadata workflows.
Native source-mod compilation is a separate trusted developer feature requiring
Rust 1.95.0 and platform build tools. Actual native hook execution is experimental.

Supported workflow scope: seven-page launcher; local game discovery/settings;
profile separation; passive Java metadata inspection and conservative diagnostics;
owned/local dependency resolution; supported data-only carry; report exports.
Only fixture-level automated results are currently claimed for new workflows.
Real PLAY/resource preparation, world save/load, graphics/audio/input, shader
rendering and two-machine Tailscale use require the manual evidence checklist.
They must not be marketed as newly certified from offscreen navigation.

Unavailable: Java bytecode execution, Java bridge, universal conversion, packwiz,
Java Build/Test and Modpack Play. Raw `works` is not gameplay compatibility.
CLI pack commands have a narrower surface than the GUI; no parity claim.

Distribution policy: internal CI artifacts only in this phase. No stable release,
public installer publication, signed-publisher trust, notarization, or store
approval is implied. Ad hoc Mac signature validity differs from Gatekeeper trust.
Windows SmartScreen behavior is unverified. Any signing service/credentials or
release publication requires separate approval.

See [manual acceptance](herps/native-acceptance.md),
[Phase 5C evidence](herps/java-mods-phase5c-macos.md) and
[security/distribution review](herps/release-security.md).
