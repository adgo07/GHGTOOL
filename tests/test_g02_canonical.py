from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from packages.core.models import OfficialStatus, ParameterType, ReviewStatus, SourceType, ValueType
from packages.reference_data import (
    DEFAULT_SOURCE_PATH,
    DEFAULT_SCHEMA_PATH,
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

    def test_canonical_schema_enums_match_g01_domain_enums(self) -> None:
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        properties = schema["properties"]

        def enum_values(collection: str, field: str) -> set[str]:
            return set(properties[collection]["items"]["properties"][field]["enum"])

        self.assertEqual(enum_values("sources", "source_type"), {item.value for item in SourceType})
        self.assertEqual(enum_values("sources", "review_status"), {item.value for item in ReviewStatus})
        self.assertEqual(enum_values("standards", "official_status"), {item.value for item in OfficialStatus})
        self.assertEqual(enum_values("parameters", "parameter_type"), {item.value for item in ParameterType})
        self.assertEqual(enum_values("parameters", "review_status"), {item.value for item in ReviewStatus})
        self.assertEqual(enum_values("factors", "value_type"), {item.value for item in ValueType})
        self.assertEqual(enum_values("factors", "review_status"), {item.value for item in ReviewStatus})
        self.assertEqual(enum_values("conversion_rules", "review_status"), {item.value for item in ReviewStatus})

    def test_canonical_rows_use_only_g01_domain_enum_values(self) -> None:
        self.assertTrue(
            all(source["source_type"] in {item.value for item in SourceType} for source in self.catalog["sources"])
        )
        self.assertTrue(
            all(standard["official_status"] in {item.value for item in OfficialStatus}
                for standard in self.catalog["standards"])
        )
        self.assertTrue(
            all(parameter["parameter_type"] in {item.value for item in ParameterType}
                for parameter in self.catalog["parameters"])
        )
        self.assertTrue(
            all(factor["value_type"] in {item.value for item in ValueType} for factor in self.catalog["factors"])
        )
        self.assertNotIn("OFFICIAL_NOTICE", json.dumps(self.catalog, ensure_ascii=False))
        self.assertNotIn("SCIENTIFIC_REPORT", json.dumps(self.catalog, ensure_ascii=False))
        self.assertNotIn('"value_type": "OFFICIAL"', json.dumps(self.catalog, ensure_ascii=False))
        self.assertNotIn('"value_type": "DEFAULT"', json.dumps(self.catalog, ensure_ascii=False))

    def test_all_standards_have_official_source_url(self) -> None:
        for standard in self.catalog["standards"]:
            self.assertTrue(standard["official_source_url"].startswith("https://"))
            self.assertIn(standard["official_source_id"], {
                source["source_id"] for source in self.catalog["sources"]
            })

    def test_planned_standards_keep_scope_and_industry_parameter_references(self) -> None:
        planned = [
            standard
            for standard in self.catalog["standards"]
            if standard["standard_id"] not in {"gbt_32150_2025", "gbt_32151_34_2024"}
        ]
        self.assertEqual(len(planned), 7)
        for standard in planned:
            self.assertEqual(standard["calculation_status"], "PLANNED")
            self.assertEqual(standard["parameter_refs"], [])
            self.assertEqual(standard["emission_source_refs"], [])

        industry = next(
            standard for standard in self.catalog["standards"]
            if standard["standard_id"] == "gbt_32151_34_2024"
        )
        self.assertEqual(industry["calculation_status"], "PLANNED")
        self.assertEqual(
            industry["parameter_refs"],
            [
                "natural_gas_lhv",
                "natural_gas_carbon_content",
                "natural_gas_oxidation_rate",
            ],
        )

    def test_standard_names_and_responsibilities_are_officially_distinguished(self) -> None:
        by_id = {standard["standard_id"]: standard for standard in self.catalog["standards"]}
        expected_names = {
            "gbt_32151_7_2023": "碳排放核算与报告要求 第7部分：平板玻璃生产企业",
            "gbt_32151_8_2023": "碳排放核算与报告要求 第8部分：水泥生产企业",
            "gbt_32151_13_2023": "碳排放核算与报告要求 第13部分：独立焦化企业",
        }
        for standard_id, expected_name in expected_names.items():
            self.assertEqual(by_id[standard_id]["standard_name"], expected_name)

        for standard in self.catalog["standards"]:
            self.assertNotIn("status", standard)
            self.assertNotIn("authority", standard)
            for field in ("issuing_authority", "competent_authority", "technical_committee"):
                self.assertTrue(standard[field])
        self.assertEqual(by_id["gbt_32150_2025"]["issuing_authority"],
                         "国家市场监督管理总局、国家标准化管理委员会")
        self.assertEqual(by_id["gbt_32150_2025"]["competent_authority"], "生态环境部")
        self.assertEqual(by_id["gbt_32150_2025"]["technical_committee"], "生态环境部")
        self.assertEqual(by_id["gbt_32151_34_2024"]["competent_authority"], "中国钢铁工业协会")
        self.assertEqual(by_id["gbt_32151_34_2024"]["technical_committee"], "中国钢铁工业协会")

    def test_standard_parameter_references_must_be_applicable(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        common_rules = next(
            standard for standard in catalog["standards"]
            if standard["standard_id"] == "gbt_32150_2025"
        )
        common_rules["parameter_refs"].append("natural_gas_lhv")
        with self.assertRaises(CanonicalValidationError):
            validate_catalog(catalog)

    def test_joint_electricity_notice_and_heat_factor_have_precise_sources(self) -> None:
        sources = {source["source_id"]: source for source in self.catalog["sources"]}
        electricity = sources["SRC-ELEC-2023-47"]
        self.assertEqual(electricity["source_type"], SourceType.GOVERNMENT_PUBLICATION.value)
        self.assertEqual(electricity["publisher"], "生态环境部、国家统计局")
        self.assertIn("联合发布", electricity["notes"])

        heat_source = sources["SRC-32150-2025"]
        heat_factor = next(factor for factor in self.catalog["factors"] if factor["factor_id"] == "heat_default_2025")
        heat_parameter = next(
            parameter for parameter in self.catalog["parameters"]
            if parameter["parameter_id"] == "heat_emission_factor_default"
        )
        self.assertEqual(heat_factor["source_id"], heat_source["source_id"])
        self.assertEqual(heat_parameter["source_id"], heat_source["source_id"])
        self.assertEqual(heat_source["official_url"],
                         "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=6E4997D6B3118055931BC13C71B9A452")
        self.assertEqual(heat_source["source_type"], SourceType.OFFICIAL_STANDARD.value)
        self.assertIn("7.5.6", heat_factor["source_location"])
        self.assertIn("7.5.7", heat_factor["source_location"])
        self.assertIn("7.5.6", heat_parameter["source_location"])
        self.assertIn("7.5.7", heat_parameter["source_location"])
        self.assertEqual(
            set(heat_factor["applicable_standard_ids"]),
            {"gbt_32150_2025", "gbt_32151_34_2024"},
        )
        self.assertEqual(
            set(heat_parameter["applicable_standard_ids"]),
            {"gbt_32150_2025", "gbt_32151_34_2024"},
        )
        self.assertEqual(heat_factor["value"], "0.11")
        self.assertEqual(heat_factor["factor_year"], 2025)
        self.assertEqual(heat_factor["valid_from"], "2026-07-01")
        self.assertEqual(heat_factor["value_type"], ValueType.STANDARD_DEFAULT.value)

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
