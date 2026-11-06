# Herspers Bedrock 0.3.0 Windows build evidence

The Windows package passed compilation, payload verification and native startup checks. Account login, resource downloads and gameplay remain untested.

| Final Windows result | Value |
| --- | --- |
| Successful workflow run | [41328863931](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41328863931), completed 2026-11-01 16:57 UTC |
| Source commit of that run | `aa8e090efef119a55c08a844fdbd04ec9d00425d` |
| `Herspers-Bedrock-Windows-x64` artifact | [Download artifact 13092278093](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41328863931/artifacts/13092278093) |
| Outer artifact size | 104,974,074 bytes |
| GitHub-reported outer artifact SHA-256 | `153fd0ec51af454d789ba2c5a9686308ae6c8f11b0abcecd98927edb4d16871a` |

The outer artifact contains the application ZIP and `bedrock-startup-results.json`. Extract both ZIP layers and keep the complete application folder. The artifact digest above comes from GitHub metadata; it was not independently recomputed from a local artifact download.

## Pinned software and target

- Product: **Herspers Bedrock 0.3.0**, for Windows 10/11 Intel/AMD x64.
- Client engine: unchanged **Cinnabar v0.1.31**, source commit `f64924fbb27004a1f785a2c131de9531fbcd252a`.
- Upstream MSI SHA-256: `584f4fa8851571abffce24bbeacadbd5cdbe35053a93b59e8d8673c7170381cb`.
- Bedrock target: **1.26.60**, protocol **2225**; native BDS target **1.26.60.6**.
- Vanilla resource snapshot: **`v1.26.60.30-preview`**, prepared through the client's first-run flow.
- Architecture: an independent GPLv3 Rust launcher starts the separately licensed Cinnabar client process. The client is Rust; its networking/authentication helper and Dragonfly server are Go.

The exact source/archive/runtime pins are recorded in [`bedrock-upstream.lock.json`](../bedrock-upstream.lock.json). This package is separate from the earlier Java Edition clients. No Java, JDK or manual `server.jar` preparation is required.

## Portable checks

- The local tooling suite executed **85 tests successfully**, including integration with the supplied Android APK.
- GitHub's portable Linux and Windows tooling checks passed.
- The pinned MSI's size and SHA-256 were verified before payload extraction. Its checksum has not been replaced to make a failing check pass.

The supplied APK check concerns the earlier Horizon source analysis. Bedrock's native startup evidence comes from the separate Windows package checks below.

## Runtime and integrity checks

The upstream runtime imports Visual C++ runtime libraries. The package identifies its required **Microsoft Visual C++ v14 x64 Redistributable** files, documents the official prerequisite, and guards engine startup with an actionable message. The independent Herspers launcher links its own Visual C runtime statically so it can report the prerequisite rather than fail to load itself.

The verified MSI contains **18 license/notice files** using CRLF where the pinned source archive uses LF. Source comparison accepts only the exact source bytes or deterministic LF-to-CRLF rendition for those identified text files. It does not rewrite the extracted MSI payload, normalize executable bytes, accept arbitrary modified text or change the trusted MSI checksum. The per-file manifest records the actual extracted bytes and their raw SHA-256 values; build metadata records the source comparison.

## Passed native Windows checks

The successful [Build Bedrock Windows app run](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/41328863931) passed all of the following before uploading the package artifact:

1. Tooling tests and native launcher tests.
2. Verified MSI/source acquisition and assembly of all 184 original engine payload files with original licenses and notices, x64 PE import checks, and the independent Rust launcher.
3. Native Herspers launcher version and full payload-manifest checks.
4. Startup of the actual Cinnabar client through the wrapper for its resource-free help path, preserving the isolated user profile.
5. Startup of the actual Go networking helper with `-h`.
6. The bundled `assetc` resource planner's `prepare --check` operation.
7. Launch of the actual first-run setup window, observing `first-run-status.json` reach **`awaiting_consent`**, its expected window title and a nonzero Windows window handle, and checking that the window remains open.
8. Confirmation that the test did **not** accept the Minecraft EULA or sign into an account, followed by package/startup-report upload.

**Final outcome: all package, native startup and setup-window checks passed.** This establishes the tested startup behavior, with the gameplay limits below.

## What the consent-screen check does not prove

Reaching `awaiting_consent` exercises the real client setup path. It does not approve an EULA for the user, download and prepare all vanilla resources, authenticate a Microsoft account, join a server or Realm, render a playable world, import a user's `.mcworld`, or verify saving, input and audio.

Those flows need personal testing with the user's account, hardware and world files. Version-matched protocol support is not a guarantee of compatibility with every server, anticheat, world, add-on or preview/release combination. Cinnabar's upstream feature and noncommercial-license limits remain in force.

Use [Bedrock Windows installation](INSTALL-BEDROCK-WINDOWS.md) for first-run setup and [Bedrock licenses](BEDROCK-LICENSES.md) for the GPL launcher/PolyForm engine boundary. No Mojang game assets or account/session files are committed or intentionally bundled in the download.
