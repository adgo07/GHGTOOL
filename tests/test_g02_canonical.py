from __future__ import annotations

import copy
import json
import unittest
from decimal import Decimal
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
        self.assertEqual(len(self.catalog["parameters"]), 98)
        self.assertEqual(len(self.catalog["factors"]), 99)
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
        self.assertEqual(industry["calculation_status"], "IMPLEMENTED")
        self.assertEqual(len(industry["emission_source_refs"]), 10)
        self.assertEqual(len(industry["parameter_refs"]), 95)
        self.assertTrue({
            "natural_gas_lhv",
            "natural_gas_carbon_content",
            "natural_gas_oxidation_rate",
            "electricity_emission_factor_nonfossil",
        }.issubset(set(industry["parameter_refs"])))

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
        industry_notes = by_id["gbt_32151_34_2024"]["notes"]
        self.assertEqual(industry_notes, "适用于炭素材料生产企业温室气体排放量的核算。")

    def test_gbt_32151_34_c1_and_c2_reference_data_are_complete_and_traceable(self) -> None:
        c1_expected = {
            "anthracite": ("26.7", "0.0274", "0.94"),
            "bituminous_coal": ("19.570", "0.0261", "0.93"),
            "lignite": ("11.9", "0.028", "0.96"),
            "cleaned_coal": ("26.334", "0.02541", "0.90"),
            "other_cleaned_coal": ("12.545", "0.02541", "0.90"),
            "briquette": ("17.460", "0.0336", "0.90"),
            "other_coal_products": ("17.460", "0.0336", "0.98"),
            "coke": ("28.435", "0.0295", "0.93"),
            "petroleum_coke": ("32.5", "0.02750", "0.98"),
            "crude_oil": ("41.816", "0.0201", "0.98"),
            "fuel_oil": ("41.816", "0.0211", "0.98"),
            "gasoline": ("43.070", "0.0189", "0.98"),
            "diesel": ("42.652", "0.0202", "0.98"),
            "kerosene": ("43.070", "0.0196", "0.98"),
            "liquefied_natural_gas": ("51.498", "0.0153", "0.98"),
            "liquefied_petroleum_gas": ("50.179", "0.0172", "0.98"),
            "naphtha": ("44.5", "0.0200", "0.98"),
            "tar": ("33.453", "0.0220", "0.98"),
            "crude_benzene": ("41.816", "0.0227", "0.98"),
            "other_petroleum_products": ("41.031", "0.0200", "0.98"),
            "natural_gas": ("389.31", "0.0153", "0.99"),
            "blast_furnace_gas": ("33.00", "0.07080", "0.99"),
            "converter_gas": ("84.00", "0.04960", "0.99"),
            "coke_oven_gas": ("179.81", "0.01358", "0.99"),
            "refinery_dry_gas": ("45.998", "0.0182", "0.99"),
            "other_gas": ("52.270", "0.0122", "0.99"),
        }
        factor_by_parameter = {item["parameter_id"]: item for item in self.catalog["factors"]}
        industry = next(item for item in self.catalog["standards"] if item["standard_id"] == "gbt_32151_34_2024")
        volume_fuels = {
            "natural_gas", "blast_furnace_gas", "converter_gas", "coke_oven_gas", "other_gas",
        }
        for subject_id, (lhv, carbon, oxidation) in c1_expected.items():
            for suffix, expected in (("lhv", lhv), ("carbon_content", carbon), ("oxidation_rate", oxidation)):
                parameter_id = f"{subject_id}_{suffix}"
                with self.subTest(parameter_id=parameter_id):
                    self.assertIn(parameter_id, industry["parameter_refs"])
                    factor = factor_by_parameter[parameter_id]
                    expected_unit = (
                        "GJ/10⁴Nm³" if subject_id in volume_fuels else "GJ/t"
                    ) if suffix == "lhv" else "tC/GJ" if suffix == "carbon_content" else "ratio"
                    self.assertEqual(Decimal(factor["normalized_value"]), Decimal(expected))
                    self.assertEqual(factor["normalized_unit"], expected_unit)
                    self.assertEqual(factor["source_id"], "SRC-32151-34-2024")
                    self.assertIn("附录C表C.1", factor["source_location"])
                    self.assertEqual(factor["factor_year"], 2024)

        c2_expected = {
            "caco3": "0.440", "mgco3": "0.522", "na2co3": "0.415", "nahco3": "0.524",
            "feco3": "0.380", "mnco3": "0.383", "baco3": "0.223", "li2co3": "0.595",
            "k2co3": "0.318", "srco3": "0.298", "camgco3_2": "0.477",
        }
        c2 = [item for item in self.catalog["parameters"] if item["parameter_id"].startswith("car-par-c2-")]
        self.assertEqual(len(c2), 11)
        for suffix, expected in c2_expected.items():
            parameter_id = f"car-par-c2-{suffix.replace('_2', '-2')}"
            with self.subTest(parameter_id=parameter_id):
                factor = factor_by_parameter[parameter_id]
                self.assertEqual(Decimal(factor["normalized_value"]), Decimal(expected))
                self.assertEqual(factor["normalized_unit"], "tCO2/t")
                self.assertEqual(factor["value_type"], ValueType.STANDARD_SPECIFIED.value)
                self.assertEqual(factor["source_id"], "SRC-32151-34-2024")
                self.assertEqual(factor["factor_year"], 2024)
                self.assertIn("附录C表C.2", factor["source_location"])

        defaults = {item["parameter_id"]: factor_by_parameter[item["parameter_id"]]["normalized_value"] for item in self.catalog["parameters"]}
        for parameter_id, expected in (
            ("car-par-k1", "0.35"),
            ("car-par-k2", "0.35"),
            ("car-par-k3", "0.35"),
            ("car-par-p04b-i", "0.90"),
            ("car-par-p04b-tr", "1"),
        ):
            factor = factor_by_parameter[parameter_id]
            with self.subTest(parameter_id=parameter_id):
                self.assertEqual(defaults[parameter_id], expected)
                self.assertEqual(factor["source_id"], "SRC-32151-34-2024")
                self.assertEqual(factor["factor_year"], 2024)
                self.assertIn("第5.2.", factor["source_location"])
                self.assertEqual(factor["value_type"], ValueType.STANDARD_DEFAULT.value)
        source = next(item for item in self.catalog["sources"] if item["source_id"] == "SRC-32151-34-2024")
        self.assertEqual(source["document_no"], "GB/T 32151.34—2024")
        self.assertEqual(source["version"], "2024")
        self.assertIn("60B034B025E9E4BC97A6FD7E18946923B696012FED0D4A3A8E901FB530136738", source["notes"])
        self.assertIn("C.4定位：PDF第27–28页、印刷页19–20", source["notes"])
        self.assertIn("C.5定位：PDF第29页、印刷页21", source["notes"])
        self.assertIn("1.70 MPa及1.80 MPa解释", source["notes"])
        self.assertIn("1.40 MPa/195.04 ℃", source["notes"])
        self.assertIn("不宣称官方勘误", source["notes"])
        self.assertIn("1.70 MPa=2793.8 kJ/kg", source["notes"])
        self.assertIn("3.0 MPa/350 ℃=3115.7 kJ/kg", source["notes"])

    def test_reference_registry_shares_equal_values_and_keeps_source_locators(self) -> None:
        assets = {item["asset_id"]: item for item in self.catalog["reference_data_assets"]}
        heat_asset = assets["asset-heat_default_2025"]
        heat_bindings = [
            item for item in self.catalog["reference_data_bindings"]
            if item["asset_id"] == heat_asset["asset_id"]
        ]
        tables = {item["source_table_id"]: item for item in self.catalog["source_tables"]}
        source_ids = {tables[item["source_table_id"]]["source_id"] for item in heat_bindings}
        locators = {item["source_location"] for item in heat_bindings}
        self.assertEqual(heat_asset["value"], "0.11")
        self.assertEqual(source_ids, {"SRC-32150-2025", "SRC-32151-34-2024"})
        self.assertEqual(len(locators), 2)
        self.assertEqual(len(self.catalog["source_tables"]), 14)
        self.assertEqual(len(self.catalog["reference_data_assets"]), 98)
        self.assertEqual(len(self.catalog["reference_data_bindings"]), 100)
        self.assertNotIn("weight", json.dumps(self.catalog["reference_data_bindings"]).lower())

    def test_standard_implementation_date_is_not_c3_factor_validity(self) -> None:
        standard = next(item for item in self.catalog["standards"] if item["standard_id"] == "gbt_32151_34_2024")
        c3_factor = next(item for item in self.catalog["factors"] if item["factor_id"] == "heat_default_gbt32151_34_c3")
        c3_binding = next(item for item in self.catalog["reference_data_bindings"] if item["factor_id"] == c3_factor["factor_id"])
        electricity = next(item for item in self.catalog["factors"] if item["factor_id"] == "electricity_national_average_2023")

        self.assertEqual(standard["implementation_date"], "2025-03-01")
        self.assertEqual(c3_factor["normalized_value"], "0.11")
        self.assertIsNone(c3_factor["valid_from"])
        self.assertIsNone(c3_binding["valid_from"])
        self.assertEqual(c3_factor["applicable_standard_ids"], [standard["standard_id"]])
        self.assertIsNotNone(electricity["valid_from"])

    def test_different_source_value_is_a_separate_immutable_asset_version(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        source = copy.deepcopy(next(item for item in catalog["sources"] if item["source_id"] == "SRC-32151-34-2024"))
        source.update({
            "source_id": "SRC-TEST-HEAT-C",
            "document_no": "测试权威资料C",
            "document_name": "测试热力因子资料",
            "publisher": "测试机构",
            "publication_date": "2026-01-01",
            "effective_from": None,
            "effective_to": None,
            "official_url": "https://example.com/heat-c",
            "version": "test",
            "notes": "测试夹具，不进入正式目录。",
        })
        catalog["sources"].append(source)
        table = copy.deepcopy(next(item for item in catalog["source_tables"] if item["source_table_id"] == "tab-32151-34-c3"))
        table.update({
            "source_table_id": "tab-test-heat-c",
            "source_id": "SRC-TEST-HEAT-C",
            "display_number": "表C",
            "title": "测试热力因子表",
            "source_location": "测试权威资料C 表C",
            "sort_order": 100,
        })
        catalog["source_tables"].append(table)
        factor = copy.deepcopy(next(item for item in catalog["factors"] if item["factor_id"] == "heat_default_gbt32151_34_c3"))
        factor.update({
            "factor_id": "heat_default_test_source_c",
            "value": "0.12",
            "source_value": "0.12",
            "normalized_value": "0.12",
            "source_id": "SRC-TEST-HEAT-C",
            "source_location": "测试权威资料C 表C；第2页",
            "factor_year": 2026,
            "notes": "独立来源的不同值，测试时使用单独资产版本。",
        })
        catalog["factors"].append(factor)
        asset = copy.deepcopy(next(item for item in catalog["reference_data_assets"] if item["asset_id"] == "asset-heat_default_2025"))
        asset.update({
            "asset_id": "asset-heat_default_test_source_c",
            "asset_version": "2",
            "value": "0.12",
            "source_value": "0.12",
            "normalized_value": "0.12",
            "notes": "单独值版本。",
        })
        catalog["reference_data_assets"].append(asset)
        binding = copy.deepcopy(next(item for item in catalog["reference_data_bindings"] if item["factor_id"] == "heat_default_gbt32151_34_c3"))
        binding.update({
            "binding_id": "binding-heat-default-test-source-c",
            "asset_id": "asset-heat_default_test_source_c",
            "source_table_id": "tab-test-heat-c",
            "factor_id": "heat_default_test_source_c",
            "source_location": factor["source_location"],
            "factor_year": 2026,
            "notes": "测试来源与定位。",
        })
        catalog["reference_data_bindings"].append(binding)

        validated = validate_catalog(catalog)
        values = [item for item in validated["reference_data_assets"] if item["parameter_id"] == "heat_emission_factor_default"]
        self.assertEqual(len(values), 2)
        self.assertEqual({item["value"] for item in values}, {"0.11", "0.12"})
        self.assertNotEqual(values[0]["asset_id"], values[1]["asset_id"])

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

    def test_nonfossil_electricity_parameter_and_factor_are_independent(self) -> None:
        parameters = {item["parameter_id"]: item for item in self.catalog["parameters"]}
        factors = {item["factor_id"]: item for item in self.catalog["factors"]}
        industry = next(
            item for item in self.catalog["standards"]
            if item["standard_id"] == "gbt_32151_34_2024"
        )

        nonfossil = parameters["electricity_emission_factor_nonfossil"]
        zero = factors["electricity_nonfossil_zero_gbt32151_34_2024"]
        national_factors = [
            item for item in factors.values()
            if item["parameter_id"] == "electricity_emission_factor_national"
        ]
        self.assertEqual(nonfossil["canonical_unit"], "tCO₂/MWh")
        self.assertEqual(nonfossil["source_id"], "SRC-32151-34-2024")
        self.assertEqual(
            nonfossil["source_location"],
            "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22",
        )
        self.assertIn("electricity_emission_factor_nonfossil", industry["parameter_refs"])
        self.assertNotIn("electricity_nonfossil_zero_gbt32151_34_2024", {item["factor_id"] for item in national_factors})
        self.assertEqual(zero["parameter_id"], "electricity_emission_factor_nonfossil")
        self.assertEqual(zero["value"], "0")
        self.assertEqual(zero["unit"], "tCO₂/MWh")
        self.assertEqual(zero["source_id"], "SRC-32151-34-2024")
        self.assertEqual(zero["factor_year"], 2024)
        self.assertEqual(zero["valid_from"], "2025-03-01")
        self.assertEqual(
            zero["source_location"],
            "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22",
        )
        self.assertEqual(self.catalog["manifest"]["schema_version"], "1.1.0")
        self.assertEqual(self.catalog["manifest"]["data_version"], "2026.10.06-pf01.1")
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
