# Phase 5D security, dependency and distribution review

This is a bounded engineering review, not a security or legal certification.

## Established controls

- Java inspection is passive; no imported bytecode, Java oracle or arbitrary
  build script is executed by metadata analysis. Native helper code is trusted.
- Archives reject traversal, nonportable/reserved names, duplicate/case-folded
  names, unsupported file types and excessive entries/bytes. Folder imports
  have bounded copy/hash checks and linked-path guards.
- Hash receipts revalidate snapshots, reports and generated output. Unknown
  constraints/evidence remain conservative. Hashes do not authenticate publishers.
- Profile mutations use guards/locks; data ports start disabled, refuse edits
  and duplicate IDs, and remove to backup. Atomic writes preserve unknown settings.
- Native builds execute full-permission code only through an explicit trust
  warning. This is not a sandbox. Review native sources and their build tools.
- Game resources are verified separately; no proprietary assets or login tokens
  are shipped. Existing ownership/resource requirements are not bypassed.

## Dependency and notice inventory

Python requirements are exact-version pinned; CI uses Python 3.12 and Rust 1.95.0,
locked Rust builds and checksum-prepared upstream source. Candidate receipts
record source commit, requirements/upstream-lock hashes and final archive hashes.
This makes the recipe traceable; timestamps/signing and tool/runner differences
mean byte-for-byte reproducibility has not been established.

Packaging generates python-dependencies.json and copies discovered license/notice
files into python-notices. PySide6/shiboken6 wheel manifests exposed no license
text in the local review, so LGPLv3, GPLv3 and a Qt/PySide notice are explicitly
included. See ../../licenses/Qt-PySide-NOTICE.md for source locations and rights.
The generated inventory includes Python build tools, not just runtime modules.
It is not an exact linked-native SBOM or a completed Qt third-party legal review.

A Phase 5D pip-audit scan of the seven pinned Python distributions reported no
known vulnerabilities. This narrow database result does not certify embedded
Qt/native libraries or Rust dependencies; full native/transitive review remains open.

Before public distribution verify actual bundled Qt modules/native dependencies,
complete original copyright notices, GPL corresponding-source delivery and LGPL
library replacement/relinking requirements. A mod license acknowledgement grants
no redistribution rights. Keep generated restricted ports local. No source offer,
commercial license or notarization claim is inferred from an inventory.

## Remaining release gates

- Complete native manual and real gameplay acceptance on declared targets.
- Review current vulnerabilities for Python, Rust, Qt and native libraries;
  a Python-only scan does not cover Rust transitive/native dependencies.
- Verify OS publisher trust, quarantine, SmartScreen and selected signing policy.
  Default Mac builds remain ad hoc; no paid signing or credentials are used here.
- Decide and document secure distribution/checksum provenance and incident support.
- Preserve clean evidence and explicitly review all failures/skips before promotion.

The notarization result is an external final-DMG-hash-bound receipt; a package's
embedded metadata records not-requested or refers to that receipt. Successful
submission, stapling AND staple validation are required before true is recorded.
Changing an already submitted DMG's contents to update metadata would invalidate
its evidence; the sidecar avoids that. The signed/notarized path still requires
real credentialed validation in a separately approved phase.
