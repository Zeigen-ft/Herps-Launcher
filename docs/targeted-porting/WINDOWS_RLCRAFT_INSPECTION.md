# Inspect your RLCraft 2.9.3 ZIP on Windows 11

This tool reads the original ZIP as untrusted data. It hashes files and records
metadata without running Java, mod code, scripts or a game. It does not install
the pack, download missing mods, change worlds or upload anything automatically.
It needs **Python 3.12 for Windows**, not Rust, Cargo, Java or developer build tools.

## Download and run

1. Open successful [Actions run 42034782638](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638) or its direct
   [**RLCraft-2.9.3-Local-Inspector** download](https://github.com/Zeigen-ft/Herspers-Minecraft/actions/runs/42034782638/artifacts/13420625410)
   (artifact `13420625410`, source `91a14cd0ebcc28c7e894173e7dc19c4a3f9498a1`).
   Use File Explorer → **Extract All** and keep its files together.
   These are internal test artifacts; GitHub sign-in may be required.
   Download ZIP SHA-256: `c8ca99670471033c36234bea8bd9f19a44689b5a37633591b85fd8fe8cb0ac3e`.
2. Install Python 3.12 from <https://www.python.org/downloads/windows/> if needed.
   Choose the standard Python installer/launcher. Open PowerShell and run
   `py -3.12 --version` to confirm it is available. No administrator shell is
   required for the inspector.
3. In the extracted inspector folder, open `inspector.json` in Notepad. Record
   `source_commit` and `script_sha256`. Open PowerShell in that folder (type
   `powershell` into File Explorer's address bar) and check:

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath .\inspect_rlcraft_293.py
   ```

   The expected delivered Windows script hash is:

   ```text
   cccc155cf8b3acc812b1f3db26d1c7a4775dd9c1783c2a706a7d3bd7f6aca957
   ```

   Compare all 64 characters with that value and `script_sha256`. Stop if
   they differ. Do not use an inspector script supplied inside a modpack.
   The Windows artifact uses CRLF line endings, so its hash differs from
   a Linux LF source checkout. See the [full evidence report](NEXT_PHASE_PREPARATION_REPORT.md).
4. Double-click **Inspect-RLCraft.cmd**. It starts the trusted Python inspector
   and asks for a path. It never runs the ZIP's own scripts.
5. Find your original **RLCraft 1.12.2 - Release v2.9.3.zip** in File Explorer.
   Right-click → **Copy as path**, paste into the inspector window, and press Enter.
   Keep the ZIP unextracted. Surrounding double quotes are accepted.
6. Wait for hashing/export to finish. Large archives may take several minutes
   and need space for local report/export copies. Leave the original untouched.

Alternatively, run the same operation from PowerShell in the inspector folder:

```powershell
py -3.12 .\inspect_rlcraft_293.py "C:\Users\YourName\Downloads\RLCraft 1.12.2 - Release v2.9.3.zip"
```

Replace the example path with the actual file. To choose another new output
folder, add `--output "D:\RLCraft-inspection-new"`. Existing output folders are
refused rather than overwritten. The tool never needs a launcher support/profile
folder; keep the inspection output outside your saves.

## Return the output to Codex

The default output is a new `RLCraft-2.9.3-inspection-<timestamp>` folder beside
the original ZIP. Successful output includes:

- **00-summary.zip**: identity, full original ZIP SHA-256, bounds, counts and
  the exact numbered export list. Upload this first.
- **metadata-0001-of-....zip** (and any further metadata parts): complete outer
  path/size/CRC/SHA-256 listing, nested-JAR listing, original manifest/mod list and
  dependency/licensing/hook evidence. Missing declarations remain unknown.
- **archive-0001-of-....zip**, **archive-0002-of-....zip**, etc.: inert byte chunks
  of the original uploaded ZIP. These allow Codex to recover and inspect the
  exact original, including assets/configurations, without asking you to run it.
- **EXPORT-SHA256SUMS.txt**: hashes of the completed export bundles.

Upload **every numbered ZIP separately**, together with 00-summary.zip and the
small EXPORT-SHA256SUMS.txt. Do not combine them into one large archive. Each
export uses at most a 24 MiB payload and is checked to be **strictly below 32 MiB**.
Keep all part numbers, including metadata parts. A part on its own is incomplete.

No original archive entries are extracted onto your PC by the inspector. Export
parts use fixed filenames (`part.json`, `payload.bin`). They are data to inspect,
not programs to open/run. You do not need to reassemble them on Windows.

The local report files are also available for review in Notepad: `inspection.json`,
`files.jsonl`, `files.sha256`, `nested-files.jsonl`, `dependency-inventory.json`,
`manifest.json`, and possibly `modlist.html`. Avoid opening untrusted HTML in a
browser; the inspector parses its text only. Large raw reports may exceed the
upload limit; return their metadata bundles instead.

## If it stops or reports a mismatch

Send **inspection-failed.json** if present, plus the exact error text. A failed
run has no completed export ZIPs. Missing files, unsafe/encrypted archives,
resource limits, disk errors and changed inputs are not silently ignored.
No inspection is claimed complete when a bound prevents it.

The ZIP must itself declare RLCraft **2.9.3**, Minecraft **1.12.2**, and a Forge
loader. Renaming 2.8.2 or using the 2XD/RL-Craft reference does not satisfy that
check. Publisher authenticity is not established merely by those declarations.
If the legitimate archive uses an unexpected declaration, return the failure;
do not edit its manifest to force a match.

Missing JARs/CurseForge IDs, unreadable metadata, unresolved nested libraries and
annotation candidates stay visible as unknown dependencies. The inspector never
reports a verified dependency closure, licence clearance or gameplay support.

Exports contain private copies of the original pack, potentially including
copyrighted assets, configuration and code. Review what you share and attach
them only for this private inspection. Do not commit them to GitHub or publish
them. Share no account credentials, unrelated logs, saves or support folders.

## For Codex: reconstruct the exact input

After receiving all parts in an owned working directory, run the same trusted
script (standard Python only):

```sh
python inspect_rlcraft_293.py --assemble /path/to/parts --output /path/to/new-original.zip
python inspect_rlcraft_293.py --assemble /path/to/parts --dataset metadata --output /path/to/new-metadata.zip
```

The tool verifies part numbering, offsets, lengths and SHA-256 checksums, then
the complete original hash. It rechecks the original manifest's 2.9.3 identity.
Compare the result with 00-summary.zip and the user's original ZIP hash. Existing
output files are never overwritten. Reassembly does not extract or execute mod
files; inspect the resulting ZIP as untrusted data.
