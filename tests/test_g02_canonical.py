from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from packages.reference_data import (
    DEFAULT_SOURCE_PATH,
    CanonicalValidationError,
    load_validated_catalog,
    validate_catalog,
)


class CanonicalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_validated_catalog()

    def test_approved_minimal_catalog_loads(self) -> None:
        self.assertEqual(len(self.catalog["standards"]), 9)
        self.assertEqual(len(self.catalog["sources"]), 12)
        self.assertEqual(len(self.catalog["parameters"]), 6)
        self.assertEqual(len(self.catalog["factors"]), 6)
        self.assertEqual(self.catalog["manifest"]["canonical_format"], "JSON")
        self.assertNotIn("full_text", json.dumps(self.catalog, ensure_ascii=False))
        self.assertTrue(DEFAULT_SOURCE_PATH.is_file())

    def test_all_standards_have_official_source_url(self) -> None:
        for standard in self.catalog["standards"]:
            self.assertTrue(standard["official_source_url"].startswith("https://"))
            self.assertIn(standard["official_source_id"], {
                source["source_id"] for source in self.catalog["sources"]
            })

    def test_planned_standards_have_no_rules_or_parameter_references(self) -> None:
        planned = [
            standard
            for standard in self.catalog["standards"]
            if standard["standard_id"] != "gbt_32150_2025"
        ]
        self.assertEqual(len(planned), 8)
        for standard in planned:
            self.assertEqual(standard["calculation_status"], "PLANNED")
            self.assertEqual(standard["parameter_refs"], [])
            self.assertEqual(standard["emission_source_refs"], [])

    def test_duplicate_stable_id_blocks_validation(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["sources"].append(copy.deepcopy(catalog["sources"][0]))
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_missing_source_blocks_validation(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["factors"][0]["source_id"] = "SRC-MISSING"
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_unknown_unit_blocks_validation(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["parameters"][0]["canonical_unit"] = "MJ/unknown"
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_float_and_unknown_property_block_validation(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["factors"][0]["value"] = 389.31
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

        catalog = copy.deepcopy(self.catalog)
        catalog["factors"][0]["unexpected"] = "must be rejected"
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_schema_type_error_blocks_before_cross_reference_checks(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["factors"] = "not-an-array"
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_wrong_normalized_value_blocks_validation(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["factors"][3]["normalized_value"] = "0.5307"
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_yaml_is_not_silently_accepted(self) -> None:
        with self.assertRaises(CanonicalValidationError):
            from packages.reference_data import load_validated_catalog

            load_validated_catalog(Path("catalog.yaml"))


if __name__ == "__main__":
    unittest.main()
