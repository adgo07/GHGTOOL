"""Returned runtime and candidate policy values must not mutate definitions."""
from copy import deepcopy
from pathlib import Path
import unittest

from packages.application.business_rules_candidate import load_bundle
from packages.standards.carbon_material_business_policy import _document, evaluate_fuel_power_field
from scripts.project_fuel_power_rules import ROOT, SOURCE_PATHS


class BusinessFieldPolicyIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(ROOT / path for path in SOURCE_PATHS)

    def _candidate_outcome(self, field_id, context):
        result = self.bundle.apply_context(context, field_ids=[field_id])
        key = f"{self.bundle.primary.rule_set_id}:{field_id}"
        return result["outcomes"][key]

    def test_mutating_allowed_values_and_nested_locking_does_not_change_runtime_or_candidate(self):
        _document.cache_clear()
        self.addCleanup(_document.cache_clear)
        runtime_definition = deepcopy(_document())
        candidate_definition = (
            deepcopy(self.bundle.primary.document),
            deepcopy(self.bundle.primary.policies),
        )

        for field_id in ("fuel.lhv", "fuel.fch"):
            context = {
                "origin": "CUSTOM",
                "binding_status": "ABSENT",
                "business_source": "MEASURED",
            }
            runtime = evaluate_fuel_power_field(field_id, context)
            candidate = self._candidate_outcome(field_id, context)
            self.assertEqual(runtime, candidate)
            self.assertEqual(runtime["source_qualification"]["value"]["values"], ["MEASURED"])
            self.assertEqual(runtime["locking"]["value"]["state"], "EDITABLE")

            for returned in (runtime, candidate):
                returned["source_qualification"]["value"]["values"].append("CALCULATED")
                returned["locking"]["value"]["state"] = "LOCKED"
                returned["locking"]["value"]["reason"] = "caller mutation"
                returned["locking"]["source"]["reason"] = "caller mutation"

            self.assertEqual(_document(), runtime_definition)
            self.assertEqual(self.bundle.primary.document, candidate_definition[0])
            self.assertEqual(self.bundle.primary.policies, candidate_definition[1])

            runtime_again = evaluate_fuel_power_field(field_id, context)
            candidate_again = self._candidate_outcome(field_id, context)
            self.assertEqual(runtime_again, candidate_again)
            self.assertEqual(runtime_again["source_qualification"]["value"]["values"], ["MEASURED"])
            self.assertEqual(runtime_again["locking"]["value"]["state"], "EDITABLE")
            self.assertEqual(runtime_again["status"], "READY")
            invalid_context = {**context, "business_source": "CALCULATED"}
            self.assertEqual(evaluate_fuel_power_field(field_id, invalid_context)["status"], "BLOCKED")
            self.assertEqual(self._candidate_outcome(field_id, invalid_context)["status"], "BLOCKED")

        direct_context = {"origin": "CUSTOM", "business_source": "CALCULATED"}
        runtime_direct = evaluate_fuel_power_field("fuel.direct_carbon", direct_context)
        candidate_direct = self._candidate_outcome("fuel.direct_carbon", direct_context)
        self.assertEqual(runtime_direct, candidate_direct)
        self.assertEqual(runtime_direct["status"], "READY")
        self.assertEqual(
            runtime_direct["source_qualification"]["value"]["values"],
            ["CALCULATED", "MEASURED"],
        )


if __name__ == "__main__":
    unittest.main()
