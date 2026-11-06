# Native acceptance protocol — Windows x64, Mac ARM64 and Mac Intel

Current recorded outcomes are in the [release-readiness notes](release-candidates-0.1.0.md).
Five chainmail Windows checks are user-reported PASS in Survival/Creative;
unreported cases and all Mac gameplay remain NOT RUN.

All cases are **NOT RUN** until performed on a native interactive OS session.
Use a physical machine for real graphics/input/audio testing. A native VM may
provide installation/UI evidence but must be identified; CI/offscreen tests
and simulated child processes never establish gameplay or physical hardware behavior.

For each target record tester, date/time/timezone, OS/build, CPU, GPU/driver,
physical/VM status, RAM, standard/admin account, exact source commit, candidate
file/hash (verify SHA256SUMS), signing/quarantine state, case result, log/screenshot
locations and reproduction steps. Use PASS / FAIL / BLOCKED / NOT RUN; never
silently omit cases. Preserve screenshots without account tokens or private data.

Use only disposable profiles/worlds and legally owned matching resources.
Make an external backup of any existing data being used; record sentinel hashes.
Do not place assets, third-party JARs, worlds or credentials in source or CI uploads.

## Installation and first launch

- Windows 11 x64: download and verify installer/portable ZIP separately; record
  SmartScreen and antivirus behavior, VC++ prerequisite error/success, per-user
  installation without elevation, paths containing spaces/non-ASCII, shortcuts.
- Mac ARM64 and Intel on macOS 15: verify the DMG, record quarantine/Gatekeeper
  behavior as downloaded, copy both apps to Applications and launch from Finder.
  Do not strip quarantine silently. Record ad hoc versus Developer ID signatures.
- Confirm all seven pages render; use real keyboard/mouse, file dialogs, scaling,
  progress/cancel/errors. Run with Rust/Cargo absent from the end-user setup.
- Test missing/wrong-architecture helper and stale explicit backend configuration;
  require actionable errors, no false compatibility status, preserved existing data.

## Resource preparation and actual game operation

1. Record legitimate Minecraft Java 26.3 installation, matching official server
   JAR and JDK 25 used for the separate resource preparer. Test wrong/missing
   input rejection first; retain resource-check errors.
2. Prepare resources with Setup.cmd / prepare.command. Verify completion, then
   PLAY through the launcher. Confirm this is a real rendered game process.
3. Create a disposable world, record a distinctive change and save/exit normally.
   Confirm exit code/log and launcher readiness. Relaunch and verify that change.
4. Switch named profiles; confirm isolated worlds/settings. Use clean startup
   and confirm existing profile data is unchanged.
5. Test a supported owned data fixture in-engine, observe its intended behavior,
   retain game logs, disable/remove to backup and verify rollback. Metadata/folder
   checks alone do not pass this case; do not claim arbitrary Java mod equivalence.
6. Verify graphics/input/audio for advertised support. Test shaders per actual
   backend; test private hosting/join/save/shutdown on two Tailscale computers
   if these capabilities are included in the stable release contract.

## Preservation and recovery

- Seed default and named profiles, settings, saves, mods, mod data and shaders.
  Run import/analyze/dependency resolution/export/data carry/enable/disable/backup
  via the installed UI. Confirm conservative statuses and disabled unsupported actions.
- Restart the app, replace/upgrade using a complete candidate, uninstall/remove
  apps and reinstall. Compare hashes; settings and worlds must remain accessible.
  CI same-version replacement is not proof of migration from every historical version.
- Exercise missing resources, backend timeout/failure, locked/read-only output,
  insufficient disk space, interrupted operation and a crashed game.
- After all relevant processes are closed, validate documented stale-lock recovery;
  never remove locks while another launcher/game is using that profile.
- Confirm logs remain actionable and contain no credentials before sharing.

## Release gate

Any data-loss, arbitrary unintended file-write, unsafe execution boundary,
installer failure or core resource/PLAY/save/relaunch defect blocks that target.
Record lesser issues with an explicit scope decision. Unsupported features stay
disabled. A target passes only with all required case evidence; outstanding
hardware cases mean native acceptance remains incomplete. Publication requires
separate approval even after acceptance passes.
