"""材料共享资格与原五字段采用范围隔离。"""
import unittest
from pathlib import Path
from packages.standards.carbon_material_business_policy import (
    evaluate_material_field, material_policy_identity, fuel_power_policy_identity,
)
from packages.standards.carbon_material_input_policy import parameter_source_policy
from scripts.project_fuel_power_rules import verify_projection
from scripts.project_material_rules import verify_material_projection

class MaterialPolicyTests(unittest.TestCase):
    def test_exact_projection_and_separate_adoption(self):
        verify_projection()
        verify_material_projection()
        self.assertEqual(len(fuel_power_policy_identity()["adopted_fields"]), 5)
        self.assertEqual(material_policy_identity()["adopted_fields"],
                         ["material.fixed_carbon", "material.volatile_matter"])

    def test_source_paths_and_missing_definition(self):
        for field in material_policy_identity()["adopted_fields"]:
            measured = parameter_source_policy(field)
            self.assertEqual(measured.allowed_sources, ("MEASURED", "CALCULATED"))
            self.assertEqual(measured.default_source, "MEASURED")
            calculated = parameter_source_policy(field, business_source="CALCULATED",
                input_basis="DEFINED_RECEIVED_BASIS_CONVERSION")
            self.assertEqual(calculated.outcome_status, "READY")
            missing = parameter_source_policy(field, business_source="CALCULATED")
            self.assertEqual(missing.outcome_status, "BLOCKED")
            default = parameter_source_policy(field, business_source="STANDARD_DEFAULT")
            self.assertEqual(default.allowed_sources, ())

    def test_nested_results_do_not_modify_resource(self):
        context={"binding_status":"ABSENT", "business_source":"MEASURED"}
        first=evaluate_material_field("material.fixed_carbon", context)
        first["source_qualification"]["value"]["values"].clear()
        again=evaluate_material_field("material.fixed_carbon", context)
        self.assertEqual(again["source_qualification"]["value"]["values"], ["MEASURED", "CALCULATED"])

if __name__ == "__main__":
    unittest.main()
