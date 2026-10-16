"""Independent R8 business expectations; no production adoption or calculation."""
from pathlib import Path
import unittest

from packages.application.business_rules_candidate import CandidateBundleError, load_bundle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data-source/carbon_accounting/business-rules"


class CandidateBusinessPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle([
            SOURCE / "common/gbt_32150_2025.json",
            SOURCE / "standards/gbt_32151_34_2024.json",
            SOURCE / "software_policy.json",
        ])

    def outcome(self, field, **context):
        result = self.bundle.apply_context(context, field_ids=[field])
        self.assertEqual(len(result["outcomes"]), 1)
        return next(iter(result["outcomes"].values()))

    def test_lhv_fch_and_oxidation_use_only_bound_default_or_measured(self):
        unbound = dict(origin="CUSTOM", binding_status="ABSENT", business_source="MEASURED")
        for field in ("fuel.lhv", "fuel.fch", "fuel.oxidation"):
            with self.subTest(field=field):
                out = self.outcome(field, **unbound)
                self.assertEqual(out["default"]["value"], {"state": "NONE"})
                self.assertEqual(out["source_qualification"]["value"]["values"], ["MEASURED"])
                self.assertEqual(out["default_source"]["value"]["source"], "MEASURED")
                self.assertEqual(out["locking"]["value"]["state"], "EDITABLE")
                self.assertEqual(out["status"], "READY")
                calculated = self.outcome(
                    field, origin="CUSTOM", binding_status="ABSENT", business_source="CALCULATED"
                )
                self.assertEqual(calculated["status"], "BLOCKED")
                self.assertIn("SOURCE_NOT_ALLOWED", {p["code"] for p in calculated["problems"]})

        bound_contexts = [
            ("fuel.lhv", "natural_gas_lhv", "binding-natural_gas_lhv_gbt32151_34_c1"),
            ("fuel.fch", "natural_gas_carbon_content", "binding-natural_gas_carbon_content_gbt32151_34_c1"),
            ("fuel.oxidation", "natural_gas_oxidation_rate", "binding-natural_gas_oxidation_rate_gbt32151_34_c1"),
        ]
        for field, parameter, binding in bound_contexts:
            context = dict(
                origin="CATALOG", binding_status="VERIFIED", parameter_id=parameter,
                binding_id=binding,
            )
            with self.subTest(field=field, source="STANDARD_DEFAULT"):
                standard = self.outcome(field, **context, business_source="STANDARD_DEFAULT")
                self.assertEqual(standard["status"], "READY")
                self.assertEqual(standard["default"]["value"], {"state": "BINDING", "parameter_id": parameter})
                self.assertEqual(standard["locking"]["value"]["state"], "LOCKED")
            with self.subTest(field=field, source="MEASURED"):
                measured = self.outcome(field, **context, business_source="MEASURED")
                self.assertEqual(measured["status"], "READY")
                self.assertEqual(measured["default"]["value"], {"state": "NONE"})
                self.assertEqual(measured["locking"]["value"]["state"], "EDITABLE")
            calculated = self.outcome(field, **context, business_source="CALCULATED")
            self.assertEqual(calculated["status"], "BLOCKED")

    def test_fcm_fcv_keep_legal_calculated_source(self):
        for origin in ("CATALOG", "CUSTOM"):
            out = self.outcome(
                "fuel.direct_carbon", origin=origin, binding_status="ABSENT",
                business_source="CALCULATED",
            )
            self.assertEqual(out["status"], "READY")
            self.assertEqual(out["source_qualification"]["value"]["values"], ["CALCULATED", "MEASURED"])
            self.assertEqual(out["default"]["value"], {"state": "NONE"})
            self.assertEqual(out["locking"]["value"]["state"], "EDITABLE")
            self.assertEqual(out["locking"]["source"]["state"], "EDITABLE")

    def test_material_calculation_requires_a_defined_supported_path(self):
        for field in ("material.fixed_carbon", "material.volatile_matter"):
            measured = self.outcome(field, binding_status="ABSENT", business_source="MEASURED")
            self.assertEqual(measured["status"], "READY")
            self.assertEqual(measured["source_qualification"]["value"]["values"], ["MEASURED", "CALCULATED"])
            self.assertEqual(measured["default"]["value"], {"state": "NONE"})
            self.assertEqual(measured["locking"]["value"]["state"], "EDITABLE")
            self.assertEqual(measured["locking"]["source"]["state"], "EDITABLE")

            measured_with_path = self.outcome(
                field, binding_status="ABSENT", business_source="MEASURED",
                material_calculation_path="DEFINED_RECEIVED_BASIS_CONVERSION",
            )
            self.assertEqual(measured_with_path["status"], "READY")
            self.assertEqual(measured_with_path["source_qualification"]["value"]["values"], ["MEASURED", "CALCULATED"])
            self.assertEqual(measured_with_path["locking"]["source"]["state"], "EDITABLE")

            undefined = self.outcome(field, binding_status="ABSENT", business_source="CALCULATED")
            self.assertEqual(undefined["status"], "BLOCKED")
            self.assertEqual(undefined["source_qualification"]["status"], "MISSING_CONTEXT")

            supported = self.outcome(
                field, binding_status="ABSENT", business_source="CALCULATED",
                material_calculation_path="DEFINED_RECEIVED_BASIS_CONVERSION",
            )
            self.assertEqual(supported["status"], "READY")
            self.assertEqual(supported["source_qualification"]["value"]["values"], ["MEASURED", "CALCULATED"])
            self.assertEqual(supported["default"]["value"], {"state": "NONE"})
            self.assertEqual(supported["locking"]["value"]["state"], "EDITABLE")
            self.assertEqual(supported["locking"]["source"]["state"], "EDITABLE")
            reason = supported["locking"]["value"]["reason"]
            self.assertIn("不代表已提供必要数量/性质", reason)
            self.assertIn("缺水分、基准或数值时消费者仍须阻断", reason)

            with self.assertRaises(CandidateBundleError):
                self.outcome(
                    field, binding_status="ABSENT", business_source="CALCULATED",
                    material_calculation_path="UNDEFINED_CHEMICAL_FORMULA",
                )
            with self.assertRaises(CandidateBundleError):
                self.outcome(
                    field, binding_status="ABSENT", business_source="CALCULATED",
                    material_method="RECEIVED_BASIS_CONVERSION",
                )

            standard = self.outcome(
                field, binding_status="ABSENT", business_source="STANDARD_DEFAULT"
            )
            self.assertEqual(standard["status"], "BLOCKED")
            self.assertEqual(standard["source_qualification"]["value"]["state"], "NO_LEGAL_SOURCES")
            self.assertEqual(standard["locking"]["value"]["state"], "PENDING")

    def test_fgd_batch_count_and_tr_are_independent_of_c2_species(self):
        one = self.outcome(
            "fgd.ratio", binding_status="VERIFIED", parameter_id="car-par-p04b-i",
            binding_id="binding-fgd_carbonate_content_default_gbt32151_34_2024",
            carbonate_component_count=1, business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(one["default"]["value"], {"state": "BINDING", "parameter_id": "car-par-p04b-i"})
        self.assertEqual(one["locking"]["value"]["state"], "LOCKED")

        many = self.outcome(
            "fgd.ratio", binding_status="ABSENT", carbonate_component_count=2,
            business_source="MEASURED",
        )
        self.assertEqual(many["default"]["value"], {"state": "NONE"})
        self.assertEqual(many["source_qualification"]["value"]["values"], ["MEASURED"])
        self.assertEqual(many["status"], "READY")

        tr = self.outcome(
            "fgd.conversion", binding_status="VERIFIED", parameter_id="car-par-p04b-tr",
            binding_id="binding-fgd_conversion_rate_default_gbt32151_34_2024",
            carbonate_component_count=2, business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(tr["status"], "READY")
        self.assertEqual(tr["default"]["value"], {"state": "BINDING", "parameter_id": "car-par-p04b-tr"})
        self.assertEqual(tr["locking"]["value"]["state"], "LOCKED")

        factor = self.outcome(
            "fgd.factor", origin="CATALOG", binding_status="VERIFIED",
            parameter_id="car-par-c2-caco3", binding_id="binding-carbonate_caco3_gbt32151_34_c2",
            business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(factor["default"]["value"], {"state": "BINDING", "parameter_id": "car-par-c2-caco3"})
        self.assertEqual(factor["locking"]["source"]["state"], "LOCKED")

    def test_exact_catalog_bindings_for_all_five_electricity_tables_are_selectable(self):
        cases = [
            ("1", "electricity_emission_factor_national", "binding-electricity_national_average_2023", "CONVENTIONAL", {}),
            ("2", "electricity_emission_factor_regional_average", "binding-electricity_regional_average_2023_01", "CONVENTIONAL", {"region": "华北"}),
            ("3", "electricity_emission_factor_provincial_average", "binding-electricity_provincial_average_2023_29", "CONVENTIONAL", {"province": "宁夏"}),
            ("4", "electricity_emission_factor_national_average_excluding_market_nonfossil", "binding-electricity_national_average_excluding_market_nonfossil_2023_01", "CONVENTIONAL", {}),
            ("5", "electricity_emission_factor_national_fossil", "binding-electricity_national_fossil_2023_01", "FOSSIL", {}),
        ]
        for table, parameter, binding, attribute, extra in cases:
            for direction in ("PURCHASED", "EXPORTED"):
                with self.subTest(table=table, direction=direction):
                    context = dict(
                        origin="CATALOG", binding_status="VERIFIED", business_source="STANDARD_DEFAULT",
                        source_path=f"CATALOGUE_TABLE_{table}", parameter_id=parameter,
                        binding_id=binding, catalog_table=table, direction=direction, **extra,
                    )
                    if direction == "PURCHASED":
                        context["attribute"] = attribute
                    out = self.outcome("electricity.factor", **context)
                    self.assertEqual(out["status"], "READY")
                    self.assertEqual(out["source_qualification"]["value"], {"state": "FIXED", "values": ["STANDARD_DEFAULT"]})
                    self.assertEqual(out["default"]["value"], {"state": "BINDING", "parameter_id": parameter})
                    self.assertEqual(out["default_source"]["value"]["source"], "STANDARD_DEFAULT")
                    self.assertEqual(out["locking"]["value"]["state"], "LOCKED")
                    self.assertEqual(out["locking"]["source"]["state"], "LOCKED")

    def test_missing_or_mismatched_electricity_binding_never_falls_back(self):
        for table in ("1", "2", "3", "4", "5"):
            with self.subTest(table=table):
                missing = self.outcome(
                    "electricity.factor", source_path=f"CATALOGUE_TABLE_{table}",
                    direction="PURCHASED", binding_status="ABSENT", business_source="STANDARD_DEFAULT",
                )
                self.assertEqual(missing["status"], "BLOCKED")
                self.assertEqual(missing["default"]["status"], "PENDING")

        wrong_region = self.outcome(
            "electricity.factor", origin="CATALOG", binding_status="VERIFIED",
            business_source="STANDARD_DEFAULT", source_path="CATALOGUE_TABLE_2",
            parameter_id="electricity_emission_factor_regional_average",
            binding_id="binding-electricity_regional_average_2023_01", catalog_table="2",
            region="华南", direction="PURCHASED", attribute="CONVENTIONAL",
        )
        self.assertEqual(wrong_region["status"], "BLOCKED")
        self.assertNotEqual((wrong_region["default"]["value"] or {}).get("state"), "BINDING")

    def test_nonfossil_zero_is_purchase_only_and_is_not_an_override_alias(self):
        purchase = self.outcome(
            "electricity.factor", source_path="NONFOSSIL_ZERO", direction="PURCHASED",
            origin="CATALOG", binding_status="VERIFIED", parameter_id="electricity_emission_factor_nonfossil",
            binding_id="binding-electricity_nonfossil_zero_gbt32151_34_2024",
            attribute="NONFOSSIL", business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(purchase["status"], "READY")
        self.assertEqual(purchase["default"]["value"], {"state": "BINDING", "parameter_id": "electricity_emission_factor_nonfossil"})
        exported = self.outcome(
            "electricity.factor", source_path="NONFOSSIL_ZERO", direction="EXPORTED",
            origin="CATALOG", binding_status="VERIFIED", business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(exported["status"], "BLOCKED")

        missing_zero = self.outcome(
            "electricity.factor", source_path="NONFOSSIL_ZERO", direction="PURCHASED",
            binding_status="ABSENT", attribute="NONFOSSIL", business_source="STANDARD_DEFAULT",
        )
        self.assertEqual(missing_zero["status"], "BLOCKED")
        self.assertNotEqual((missing_zero["default"]["value"] or {}).get("state"), "BINDING")

        for attribute in ("CONVENTIONAL", "FOSSIL"):
            with self.subTest(manual_purchase_attribute=attribute):
                base = dict(origin="CUSTOM", binding_status="ABSENT")
                override = self.outcome(
                    "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="PURCHASED",
                    attribute=attribute, **base,
                )
                self.assertEqual(override["status"], "READY")
                self.assertEqual(
                    override["source_qualification"]["value"],
                    {"state": "FIXED", "values": ["OTHER"]},
                )
                self.assertEqual(override["default_source"]["value"]["state"], "NONE")
                self.assertEqual(override["default"]["value"], {"state": "NONE"})
                self.assertEqual(override["locking"]["value"]["state"], "EDITABLE")
                self.assertEqual(override["locking"]["source"]["state"], "EDITABLE")

                selected_other = self.outcome(
                    "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="PURCHASED",
                    attribute=attribute, business_source="OTHER", **base,
                )
                self.assertEqual(selected_other["status"], "READY")
                self.assertEqual(selected_other["source_qualification"]["value"]["values"], ["OTHER"])
                self.assertEqual(selected_other["default"]["value"], {"state": "NONE"})

                for source in ("STANDARD_DEFAULT", "CALCULATED", "MEASURED"):
                    forged = self.outcome(
                        "electricity.factor", source_path="ARBITRARY_OVERRIDE",
                        direction="PURCHASED", attribute=attribute, business_source=source, **base,
                    )
                    self.assertEqual(forged["status"], "BLOCKED")
                    self.assertIn("SOURCE_NOT_ALLOWED", {p["code"] for p in forged["problems"]})

        missing_attribute = self.outcome(
            "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="PURCHASED",
        )
        self.assertEqual(missing_attribute["status"], "BLOCKED")
        self.assertEqual(missing_attribute["source_qualification"]["status"], "MISSING_CONTEXT")

        nonfossil_manual = self.outcome(
            "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="PURCHASED",
            attribute="NONFOSSIL", origin="CUSTOM", binding_status="ABSENT",
        )
        self.assertEqual(nonfossil_manual["status"], "BLOCKED")
        self.assertEqual(nonfossil_manual["source_qualification"]["value"]["state"], "NO_LEGAL_SOURCES")
        self.assertEqual(nonfossil_manual["default"]["value"], {"state": "NONE"})
        self.assertEqual(nonfossil_manual["locking"]["value"]["state"], "LOCKED")

        exported_manual = self.outcome(
            "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="EXPORTED",
            attribute="NONFOSSIL", origin="CUSTOM", binding_status="ABSENT",
        )
        self.assertEqual(exported_manual["status"], "READY")
        self.assertEqual(
            exported_manual["source_qualification"]["value"],
            {"state": "FIXED", "values": ["OTHER"]},
        )
        self.assertEqual(exported_manual["default_source"]["value"]["state"], "NONE")
        self.assertEqual(exported_manual["default"]["value"], {"state": "NONE"})
        self.assertEqual(exported_manual["locking"]["value"]["state"], "EDITABLE")
        self.assertEqual(exported_manual["locking"]["source"]["state"], "EDITABLE")

        selected_export = self.outcome(
            "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="EXPORTED",
            attribute="NONFOSSIL", business_source="OTHER", origin="CUSTOM", binding_status="ABSENT",
        )
        self.assertEqual(selected_export["status"], "READY")
        self.assertEqual(selected_export["source_qualification"]["value"]["values"], ["OTHER"])

        forged_export = self.outcome(
            "electricity.factor", source_path="ARBITRARY_OVERRIDE", direction="EXPORTED",
            attribute="NONFOSSIL", business_source="MEASURED", origin="CUSTOM", binding_status="ABSENT",
        )
        self.assertEqual(forged_export["status"], "BLOCKED")
        self.assertIn("SOURCE_NOT_ALLOWED", {p["code"] for p in forged_export["problems"]})

    def test_issue014_professional_paths_remain_separate_and_pending(self):
        for path in ("SUPPLY_UNIT_MEASURED", "ENTERPRISE_MEASURED", "ENTERPRISE_CALCULATED"):
            for direction in ("PURCHASED", "EXPORTED"):
                with self.subTest(path=path, direction=direction):
                    out = self.outcome(
                        "electricity.factor", source_path=path, direction=direction,
                        business_source="MEASURED",
                    )
                    self.assertEqual(out["status"], "BLOCKED")
                    self.assertEqual(out["source_qualification"]["status"], "PENDING")

    def test_heat_measured_source_takes_priority_without_an_empty_value_fallback(self):
        context = dict(
            origin="CATALOG", binding_status="VERIFIED", parameter_id="heat_emission_factor_default",
            binding_id="binding-heat_default_2025", direction="PURCHASED", business_source="MEASURED",
        )
        out = self.outcome("heat.factor", **context)
        self.assertEqual(out["status"], "READY")
        self.assertEqual(out["default"]["value"], {"state": "NONE"})
        self.assertEqual(out["locking"]["value"]["state"], "EDITABLE")
        self.assertEqual(out["locking"]["source"]["state"], "EDITABLE")

        unbound = self.outcome(
            "heat.factor", origin="CUSTOM", binding_status="ABSENT",
            direction="PURCHASED", business_source="MEASURED",
        )
        self.assertEqual(unbound["default"]["value"], {"state": "NONE"})
        self.assertEqual(unbound["locking"]["value"]["state"], "EDITABLE")
