"""Audited JSON contracts: evidence must be typed without inventing success."""
from copy import deepcopy
import unittest

from herps_launcher.javamods.models import (
    CheckResult, CoverageRow, InventoryRecord, SchemaError,
    parse_coverage, parse_inventory,
)


def check_fixture():
    # Actual shape from the audit's false-positive Fabric fixture.
    return {
        "mod_id": "fabricprobe", "name": "Fabric probe", "version": "1",
        "loader": "fabric", "license": "MIT", "verdict": "works",
        "summary": "Content only: 1 recipe port.", "ports": ["1 recipe"],
        "skipped": [], "depends": ["missinglib"], "namespaces": ["fabricprobe"],
        "code": {"classes": 0, "features": {}, "events": [], "examples": {}},
    }


def inventory_fixture():
    return {
        "key": "fabricprobe", "name": "Fabric probe", "version": "1",
        "path": "mods/probe.jar", "class": "unknown", "tier": "none",
        "confidence": "unknown", "source": "file", "license": "MIT",
        "client": "", "server": "", "depends": [], "missing": ["missinglib"],
        "layer": 0, "jar": "/owned/fixture.jar",
        "info": {
            "mod_id": "fabricprobe", "name": "Fabric probe", "version": "1",
            "license": "MIT", "depends": ["missinglib"],
            "census": dict.fromkeys(("blockstates", "item_models", "recipes", "loot_tables",
                                     "tags", "worldgen", "structures", "languages", "textures",
                                     "sounds", "classes", "mixin_configs"), 0),
        },
    }


def coverage_fixture():
    return {"key": "ruby", "name": "Ruby audit fixture", "class": "content", "tier": "data",
            "license": "MIT", "license_kind": "permissive", "status": "partial",
            "reason": "1 blocks, 1 items; harness not run"}


class PortPackSchemaTests(unittest.TestCase):
    def test_actual_works_shape_retains_missing_dependency_without_status_translation(self):
        value = check_fixture()
        result = CheckResult.parse(value)
        self.assertEqual(result.verdict, "works")
        self.assertEqual(result.depends, ["missinglib"])
        self.assertEqual(result.code.classes, 0)
        self.assertEqual(result.raw, value)
        self.assertFalse(hasattr(result, "status"))

    def test_raw_evidence_preserves_unknown_fields_and_is_independent_of_input(self):
        value = check_fixture()
        value["new_evidence"] = {"notes": ["unreviewed"]}
        value["code"]["future"] = {"census": 4}
        result = CheckResult.parse(value)
        value["new_evidence"]["notes"].append("mutated")
        value["code"]["future"]["census"] = 0
        value["depends"].clear()
        self.assertEqual(result.raw["new_evidence"], {"notes": ["unreviewed"]})
        self.assertEqual(result.code.raw["future"], {"census": 4})
        self.assertEqual(result.depends, ["missinglib"])

    def test_every_required_check_field_is_validated(self):
        for field in check_fixture():
            with self.subTest(field=field):
                value = check_fixture()
                del value[field]
                with self.assertRaisesRegex(SchemaError, "missing required field"):
                    CheckResult.parse(value)

    def test_unexpected_check_verdict_loader_or_field_type_is_rejected(self):
        for field, bad in (("verdict", "tested"), ("loader", "bridge"), ("name", None),
                           ("ports", "one recipe"), ("depends", [3])):
            with self.subTest(field=field, bad=bad):
                value = check_fixture()
                value[field] = bad
                with self.assertRaises(SchemaError):
                    CheckResult.parse(value)

    def test_invalid_nested_code_fields_and_counts_are_rejected(self):
        for field, bad in (("classes", True), ("classes", -1), ("classes", 1.5),
                           ("features", {"mixin": False}), ("features", []),
                           ("events", [None]), ("examples", {"mixin": "not-an-array"})):
            with self.subTest(field=field, bad=bad):
                value = check_fixture()
                value["code"][field] = bad
                with self.assertRaises(SchemaError):
                    CheckResult.parse(value)

    def test_inventory_keeps_missing_ids_distinct_from_in_pack_dependencies(self):
        result = parse_inventory([inventory_fixture()])[0]
        self.assertEqual(result.depends, [])
        self.assertEqual(result.missing, ["missinglib"])
        self.assertEqual(result.info.depends, ["missinglib"])
        self.assertEqual(result.info.census.mixin_configs, 0)
        self.assertEqual(result.class_, "unknown")

    def test_optional_inventory_omission_survives_in_raw_evidence(self):
        value = inventory_fixture()
        for field in ("missing", "jar", "info"):
            del value[field]
        result = InventoryRecord.parse(value)
        self.assertEqual(result.missing, [])
        self.assertEqual(result.categories, [])
        self.assertIsNone(result.jar)
        self.assertIsNone(result.info)
        self.assertNotIn("missing", result.raw)
        self.assertNotIn("jar", result.raw)
        self.assertNotIn("info", result.raw)

    def test_optional_inventory_wrong_types_and_explicit_null_are_rejected(self):
        for field, bad in (("categories", "content"), ("missing", None),
                           ("jar", None), ("info", None), ("info", {})):
            with self.subTest(field=field, bad=bad):
                value = inventory_fixture()
                value[field] = bad
                with self.assertRaises(SchemaError):
                    InventoryRecord.parse(value)

    def test_inventory_requires_all_typed_census_counts(self):
        value = inventory_fixture()
        for field in value["info"]["census"]:
            with self.subTest(field=field):
                bad = deepcopy(value)
                bad["info"]["census"][field] = False
                with self.assertRaises(SchemaError):
                    InventoryRecord.parse(bad)
        del value["info"]["census"]["classes"]
        with self.assertRaises(SchemaError):
            InventoryRecord.parse(value)

    def test_artifact_arrays_reject_objects_and_duplicate_keys(self):
        for parser, value in ((parse_inventory, inventory_fixture()),
                              (parse_coverage, coverage_fixture())):
            with self.subTest(parser=parser.__name__):
                with self.assertRaises(SchemaError):
                    parser(value)
                with self.assertRaisesRegex(SchemaError, "duplicate record key"):
                    parser([value, deepcopy(value)])
                self.assertEqual(parser([]), [])

    def test_coverage_retains_partial_reason_without_success_translation(self):
        value = coverage_fixture()
        value["future"] = ["raw evidence"]
        result = CoverageRow.parse(value)
        self.assertEqual(result.status, "partial")
        self.assertIn("harness not run", result.reason)
        self.assertEqual(result.raw, value)
        for status in ("ported", "not-yet", "not-needed"):
            value["status"] = status
            self.assertEqual(CoverageRow.parse(value).status, status)
        value["status"] = "Tested successfully"
        with self.assertRaises(SchemaError):
            CoverageRow.parse(value)

    def test_coverage_missing_fields_and_wrong_reason_type_are_rejected(self):
        for field in coverage_fixture():
            with self.subTest(field=field):
                value = coverage_fixture()
                del value[field]
                with self.assertRaises(SchemaError):
                    CoverageRow.parse(value)
        value = coverage_fixture()
        value["reason"] = []
        with self.assertRaises(SchemaError):
            CoverageRow.parse(value)


if __name__ == "__main__":
    unittest.main()
