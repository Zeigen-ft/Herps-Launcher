# Windows Java 0.2.2 build results

[Native Windows build 41390658796](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41390658796) succeeded for source commit [`7fe369fc7a0b930f9c3e0663de6904db366964ec`](https://github.com/Zeigen-ft/Herspers-Minecraft/commit/7fe369fc7a0b930f9c3e0663de6904db366964ec).

## Download

Open [the successful run's Artifacts section](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41390658796#artifacts) and download **Herspers-Minecraft-Windows-x64**. GitHub sign-in may be required. Extract the outer artifact ZIP and the inner application ZIP, keeping the complete application folder together.

The package contains native **Herspers Minecraft 0.2.2**, the unchanged pinned Horizon 0.7.6 engine/preparer with the 16 MiB main-stack setting, **Host-Tailscale.cmd**, **Join-Tailscale.cmd**, and **HOSTING-TAILSCALE.txt**. Previously prepared resources remain outside the application and can be reused.

## Verified

- Native Windows tooling and launcher unit tests, including private-address validation, configuration/EULA preservation, canonical-setting idempotence, backups and Windows file replacement.
- Native engine and preparer library tests and the locked x64 MSVC build.
- PE architecture/system-DLL checks, the required game stack reserve, packaging and artifact upload.
- Packaged executable help/version/Launch API startup, missing-resource handling, and presence of the new helpers and hosting guide.
- The private configuration fixture was parsed and rewritten by the **real game server's `--dedicated --initSettings` preflight**, without assets or opening a server port. It retained `online-mode=false` and `server-ip=100.64.1.2`, did not accept an EULA, and a second configuration pass left canonical settings unchanged.

Local Linux validation additionally completed 108 tooling tests with two expected skips (the supplied-APK integration and macOS-only AppleScript compilation), and warning-free MSVC-target metadata checks for the launcher and unit tests.

## Player-side validation

An actual two-PC Tailscale session, full world rendering/gameplay and the players' Tailscale sharing/firewall configuration were not tested by CI. The native build checks do not establish those outcomes. Follow [private hosting](HOSTING-TAILSCALE.md), stop the old server before starting the new host, and join its printed Tailscale address on both PCs.

This release does not change client authentication requirements for unrelated public servers. Its host starter configures an owned server for private Tailscale access.
