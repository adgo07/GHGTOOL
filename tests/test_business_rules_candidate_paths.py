"""Independent business expectations for A candidate definitions; no production adoption."""
from pathlib import Path
import unittest
from packages.application.business_rules_candidate import load_bundle

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data-source/carbon_accounting/business-rules"

class CandidateBusinessPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=load_bundle([SOURCE/"common/gbt_32150_2025.json",
            SOURCE/"standards/gbt_32151_34_2024.json",SOURCE/"software_policy.json"])

    def outcome(self,field,**context):
        result=self.bundle.apply_context(context,field_ids=[field])
        self.assertEqual(len(result["outcomes"]),1)
        return next(iter(result["outcomes"].values()))

    def test_custom_fuel_has_no_borrowed_defaults_and_oxidation_excludes_calculated(self):
        context=dict(origin="CUSTOM",binding_status="ABSENT",business_source="MEASURED")
        for field in ("fuel.lhv","fuel.fch","fuel.oxidation","fuel.direct_carbon"):
            with self.subTest(field=field):
                out=self.outcome(field,**context)
                self.assertEqual(out["default"]["value"],{"state":"NONE"})
                self.assertNotIn("STANDARD_DEFAULT",out["source_qualification"]["value"]["values"])
                self.assertEqual(out["locking"]["value"]["state"],"EDITABLE")
                self.assertEqual(out["status"],"READY")
        oxidation=self.outcome("fuel.oxidation",**context)
        self.assertEqual(oxidation["source_qualification"]["value"]["values"],["MEASURED"])
        direct=self.outcome("fuel.direct_carbon",**context)
        self.assertEqual(direct["source_qualification"]["value"]["values"],["MEASURED"])

    def test_catalog_fch_can_explicitly_change_source_without_permanent_lock(self):
        context=dict(origin="CATALOG",binding_status="VERIFIED",parameter_id="natural_gas_carbon_content",
                     binding_id="binding-natural_gas_carbon_content_gbt32151_34_c1")
        standard=self.outcome("fuel.fch",**context,business_source="STANDARD_DEFAULT")
        measured=self.outcome("fuel.fch",**context,business_source="MEASURED")
        self.assertEqual(standard["default"]["value"],{"state":"BINDING","parameter_id":"natural_gas_carbon_content"})
        self.assertEqual(standard["locking"]["value"]["state"],"LOCKED")
        self.assertEqual(standard["locking"]["source"]["state"],"EDITABLE")
        self.assertEqual(measured["locking"]["value"]["state"],"EDITABLE")
        self.assertEqual(measured["default"]["value"],{"state":"NONE"})
        self.assertEqual(measured["status"],"READY")

    def test_fgd_single_and_multi_component_defaults_are_not_copied(self):
        one=self.outcome("fgd.ratio",binding_status="VERIFIED",parameter_id="car-par-p04b-i",
            binding_id="binding-fgd_carbonate_content_default_gbt32151_34_2024",
            carbonate_component_count=1,business_source="STANDARD_DEFAULT")
        self.assertEqual(one["default"]["value"],{"state":"BINDING","parameter_id":"car-par-p04b-i"})
        self.assertEqual(one["locking"]["value"]["state"],"LOCKED")
        many=self.outcome("fgd.ratio",binding_status="ABSENT",carbonate_component_count=2,business_source="MEASURED")
        self.assertEqual(many["default"]["value"],{"state":"NONE"})
        self.assertEqual(many["source_qualification"]["value"]["values"],["MEASURED"])
        self.assertEqual(many["locking"]["source"]["state"],"LOCKED")
        self.assertEqual(many["locking"]["value"]["state"],"EDITABLE")
        self.assertEqual(many["status"],"READY")

    def test_c2_exact_factor_is_locked_but_unbound_measured_is_not_default(self):
        matched=self.outcome("fgd.factor",origin="CATALOG",binding_status="VERIFIED",
            parameter_id="car-par-c2-caco3",binding_id="binding-carbonate_caco3_gbt32151_34_c2",
            business_source="STANDARD_DEFAULT")
        self.assertEqual(matched["default"]["value"],{"state":"BINDING","parameter_id":"car-par-c2-caco3"})
        self.assertEqual(matched["locking"]["value"]["state"],"LOCKED")
        self.assertEqual(matched["locking"]["source"]["state"],"LOCKED")
        unmatched=self.outcome("fgd.factor",origin="CUSTOM",binding_status="ABSENT",business_source="MEASURED")
        self.assertEqual(unmatched["default"]["value"],{"state":"NONE"})
        self.assertEqual(unmatched["locking"]["value"]["state"],"EDITABLE")

    def test_power_direction_catalog_locks_and_nonfossil_output_is_not_zero(self):
        context=dict(origin="CATALOG",binding_status="VERIFIED",source_path="CATALOGUE_TABLE_3",
            parameter_id="electricity_emission_factor_provincial_average",
            binding_id="binding-electricity_provincial_average_2023_29",catalog_table="3",province="宁夏",
            business_source="STANDARD_DEFAULT")
        purchase=self.outcome("electricity.factor",**context,direction="PURCHASED",attribute="CONVENTIONAL")
        export=self.outcome("electricity.factor",**context,direction="EXPORTED")
        export_with_irrelevant_attribute=self.outcome("electricity.factor",**context,direction="EXPORTED",attribute="NONFOSSIL")
        for out in (purchase,export,export_with_irrelevant_attribute):
            self.assertEqual(out["status"],"READY")
            self.assertEqual(out["default"]["value"],{"state":"BINDING","parameter_id":"electricity_emission_factor_provincial_average"})
            self.assertEqual(out["locking"]["value"]["state"],"LOCKED")
            self.assertEqual(out["locking"]["source"]["state"],"LOCKED")
        zero_output=self.outcome("electricity.factor",source_path="NONFOSSIL_ZERO",direction="EXPORTED",
            origin="CATALOG",binding_status="VERIFIED",business_source="STANDARD_DEFAULT")
        self.assertEqual(zero_output["status"],"BLOCKED")

    def test_missing_binding_and_issue014_do_not_enable_fallback_or_block_other_fields(self):
        missing=self.outcome("electricity.factor",source_path="CATALOGUE_TABLE_3",direction="PURCHASED",
                             binding_status="ABSENT",business_source="STANDARD_DEFAULT")
        self.assertEqual(missing["status"],"BLOCKED")
        self.assertEqual(missing["default"]["status"],"PENDING")
        for path in ("SUPPLY_UNIT_MEASURED","ENTERPRISE_MEASURED","ENTERPRISE_CALCULATED"):
            for direction in ("PURCHASED","EXPORTED"):
                with self.subTest(path=path,direction=direction):
                    out=self.outcome("electricity.factor",source_path=path,direction=direction,business_source="MEASURED")
                    self.assertEqual(out["status"],"BLOCKED")
                    self.assertEqual(out["source_qualification"]["status"],"PENDING")
                    forged=self.outcome("electricity.factor",source_path=path,direction=direction,
                        binding_status="VERIFIED",business_source="MEASURED")
                    self.assertEqual(forged["status"],"BLOCKED")
                    self.assertEqual(forged["source_qualification"]["status"],"PENDING")
        fuel=self.outcome("fuel.direct_carbon",origin="CUSTOM",binding_status="ABSENT",business_source="MEASURED")
        self.assertEqual(fuel["status"],"READY")

    def test_unbound_heat_has_no_automatic_factor(self):
        out=self.outcome("heat.factor",origin="CUSTOM",binding_status="ABSENT",direction="PURCHASED",business_source="MEASURED")
        self.assertEqual(out["default"]["value"],{"state":"NONE"})
        self.assertEqual(out["locking"]["value"]["state"],"EDITABLE")

    def test_selected_business_source_must_belong_to_resolved_qualification(self):
        cases=[("fgd.ratio",dict(binding_status="ABSENT",carbonate_component_count=2,business_source="STANDARD_DEFAULT")),
               ("fuel.oxidation",dict(origin="CUSTOM",binding_status="ABSENT",business_source="CALCULATED"))]
        for field,context in cases:
            with self.subTest(field=field):
                out=self.outcome(field,**context)
                self.assertEqual(out["status"],"BLOCKED")
                self.assertIn("SOURCE_NOT_ALLOWED",{p["code"] for p in out["problems"]})

    def test_selected_manual_sources_do_not_inherit_catalog_default_values(self):
        cases=[
            ("fuel.lhv", "natural_gas_lhv", "binding-natural_gas_lhv_gbt32151_34_c1", ("MEASURED","CALCULATED"), {}),
            ("fuel.fch", "natural_gas_carbon_content", "binding-natural_gas_carbon_content_gbt32151_34_c1", ("MEASURED","CALCULATED"), {}),
            ("fuel.oxidation", "natural_gas_oxidation_rate", "binding-natural_gas_oxidation_rate_gbt32151_34_c1", ("MEASURED",), {}),
            ("fgd.ratio", "car-par-p04b-i", "binding-fgd_carbonate_content_default_gbt32151_34_2024", ("MEASURED",), {"carbonate_component_count":1}),
            ("fgd.conversion", "car-par-p04b-tr", "binding-fgd_conversion_rate_default_gbt32151_34_2024", ("MEASURED",), {}),
            ("heat.factor", "heat_emission_factor_default", "binding-heat_default_2025", ("MEASURED",), {"direction":"PURCHASED"}),
        ]
        for field,parameter,binding,sources,extra in cases:
            for source in sources:
                with self.subTest(field=field,source=source):
                    out=self.outcome(field,origin="CATALOG",binding_status="VERIFIED",
                        parameter_id=parameter,binding_id=binding,business_source=source,**extra)
                    self.assertEqual(out["default"]["value"],{"state":"NONE"},
                        "选择实测/计算后不得把目录缺省当作当前来源默认值")
                    self.assertEqual(out["locking"]["value"]["state"],"EDITABLE")
                    self.assertEqual(out["status"],"READY")
