"""PyInstaller entrypoint; imports shared code without relative entrypoint imports."""
import sys
import json


def port_pack_smoke(launcher, directory, evidence):
    """Exercise the bundled native helper with owned, passive metadata fixtures."""
    from dataclasses import asdict
    from pathlib import Path
    import zipfile
    from herps_launcher.core import GAME
    from herps_launcher.javamods.adapter import (
        PortPackAdapter, REQUIRES_PORTING, UNSUPPORTED, bundled_port_pack_candidates,
    )

    evidence.update(status="failed", bundled=False)
    if not getattr(sys, "frozen", False):
        raise ValueError("Bundled port-pack verification requires a frozen launcher")
    adapter = PortPackAdapter(launcher)
    discovery = adapter._new("packaging-discovery")
    binary = adapter._binary(discovery)
    evidence.update(discovery.raw_evidence["backend"])
    if binary.resolve() not in {p.resolve() for p in bundled_port_pack_candidates()}:
        raise ValueError("Packaging smoke selected an external port-pack instead of the bundled executable")
    evidence["bundled"] = True
    adapter = PortPackAdapter(launcher, executable=binary)
    evidence["checks"] = []
    for broken in (False, True):
        mod_id = "packaging_missing" if broken else "packaging_data"
        metadata = {"schemaVersion": 1, "id": mod_id, "name": "Owned packaging fixture",
                    "version": "1", "license": "MIT", "depends": {"minecraft": GAME}}
        if broken:
            metadata["depends"]["missinglib"] = ">=2"
        jar = Path(directory) / f"{mod_id}.jar"
        with zipfile.ZipFile(jar, "w") as archive:
            archive.writestr("fabric.mod.json", json.dumps(metadata))
            archive.writestr(f"data/{mod_id}/recipe/owned.json", json.dumps({
                "type": "minecraft:crafting_shapeless", "ingredients": ["minecraft:red_dye"],
                "result": {"id": "minecraft:red_dye"}}))
        result = adapter.check(jar)
        row = result.mods[0] if result.mods else None
        original = row.check.verdict if row and row.check else None
        diagnostics = [asdict(d) for d in result.diagnostics + (row.diagnostics if row else [])]
        evidence["checks"].append({"fixture": mod_id, "adapter_status": result.status,
            "original_verdict": original, "diagnostics": diagnostics,
            "commands": [asdict(c) for c in result.commands],
            "original_check": row.raw_evidence.get("check") if row else None,
            "test_execution": result.to_dict()["test_execution"]})
        expected = UNSUPPORTED if broken else REQUIRES_PORTING
        if (result.status != expected or original != "works" or not result.commands
                or any(c.exit_code != 0 for c in result.commands)):
            raise ValueError(f"Bundled metadata smoke failed for {mod_id}: {diagnostics}")
        if broken and not {"missing_dependency", "insufficient_evidence"}.issubset({d["code"] for d in diagnostics}):
            raise ValueError("Bundled adapter did not retain false-positive Works safeguards")
    evidence.update(status="passed", adapter_status=REQUIRES_PORTING,
                    original_verdict="works", test_execution=None,
                    gameplay_verified=False, java_bridge_available=False)


if __name__ == "__main__":
    if "--woodcutting-acceptance" in sys.argv:
        from woodcutting_acceptance import run
        raise SystemExit(run(sys.argv[sys.argv.index("--smoke-report") + 1]))
    if "--gathering-acceptance" in sys.argv:
        from gathering_acceptance import run
        raise SystemExit(run(sys.argv[sys.argv.index("--smoke-report") + 1]))
    if "--flint-acceptance" in sys.argv:
        from flint_acceptance import run
        raise SystemExit(run(sys.argv[sys.argv.index("--smoke-report") + 1]))
    if "--phase5c-acceptance" in sys.argv or "--native-acceptance" in sys.argv:
        from phase5c_acceptance import run
        raise SystemExit(run(sys.argv[sys.argv.index("--smoke-report") + 1]))
    if "--smoke-test" in sys.argv:
        import tempfile
        from pathlib import Path
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QTest
        from herps_launcher.app import Window, STYLE
        from herps_launcher.core import Launcher
        report = {"status": "failed", "pages_opened": 0}
        result = 1
        try:
            app = QApplication([])
            app.setStyleSheet(STYLE)
            with tempfile.TemporaryDirectory() as temporary:
                launcher = Launcher(Path(temporary))
                if "--require-installation" in sys.argv:
                    installation = launcher.installation()
                    report["installation"] = str(installation.root)
                    report["architecture"] = installation.metadata["architecture"]
                if "--require-port-pack" in sys.argv:
                    report["port_pack"] = {}
                    port_pack_smoke(launcher, Path(temporary), report["port_pack"])
                window = Window(launcher)
                window.show()
                for i, button in enumerate(window.nav):
                    QTest.mouseClick(button, __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.MouseButton.LeftButton)
                    app.processEvents()
                    assert window.pages.currentIndex() == i, f"Page {i} did not open"
                    report["pages_opened"] += 1
                window.close()
            report["status"] = "passed"
            result = 0
        except Exception as error:
            report["error"] = str(error)
        if "--smoke-report" in sys.argv:
            report_path = Path(sys.argv[sys.argv.index("--smoke-report") + 1])
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
        raise SystemExit(result)
    from herps_launcher.app import main
    raise SystemExit(main())
