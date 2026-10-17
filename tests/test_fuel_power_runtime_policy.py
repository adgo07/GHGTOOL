"""Independent outcomes and deployment protection for the limited adoption."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packages.core.business_field_policy import apply_policy
from packages.standards.carbon_material_business_policy import (
    BusinessPolicyConfigurationError, _decode_resource, _document,
    evaluate_fuel_power_field, electricity_catalogue_parameters,
)
from scripts.project_fuel_power_rules import (
    ADOPTED_FIELDS, ROOT, RUNTIME_PATH, SOURCE_PATHS, projected_bytes, verify_projection,
)
from scripts.inspect_release import BUSINESS_RULES_PATH, inspect_release


class FuelPowerRuntimePolicyTests(unittest.TestCase):
    def test_projection_is_reproducible_and_limited_to_five_fields(self):
        verify_projection()
        document = _decode_resource((ROOT / RUNTIME_PATH).read_bytes())
        self.assertEqual(set(document["fields"]), set(ADOPTED_FIELDS))
        self.assertEqual(len(document["sources"]), 3)
        self.assertEqual(document["fields"]["fuel.lhv"]["revision"], "adoption-2026-10-17-fuel-power1")
        self.assertNotIn(b"channel_projections", (ROOT / RUNTIME_PATH).read_bytes())
        self.assertNotIn(b"review.operation", (ROOT / RUNTIME_PATH).read_bytes())

    def test_build_detects_changed_source_and_changed_resource_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (*SOURCE_PATHS, RUNTIME_PATH.as_posix()):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            verify_projection(root)
            source = root / SOURCE_PATHS[1]
            source.write_bytes(source.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "differs"):
                verify_projection(root)
            source.write_bytes((ROOT / SOURCE_PATHS[1]).read_bytes())
            (root / RUNTIME_PATH).write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "differs"):
                verify_projection(root)

    def test_missing_or_tampered_runtime_resource_never_uses_old_policy(self):
        with self.assertRaises(BusinessPolicyConfigurationError):
            _decode_resource(b"{}")
        _document.cache_clear()
        with patch("packages.standards.carbon_material_business_policy.files", side_effect=FileNotFoundError):
            with self.assertRaises(BusinessPolicyConfigurationError):
                evaluate_fuel_power_field("fuel.fch", {"origin": "CUSTOM"})
        _document.cache_clear()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIn("missing fuel/power runtime rules: resources/business_rules/fuel_power.json", inspect_release(root))
            resource = root / BUSINESS_RULES_PATH
            resource.parent.mkdir(parents=True)
            resource.write_bytes(b"{}")
            self.assertIn("fuel/power runtime rules hash mismatch: resources/business_rules/fuel_power.json", inspect_release(root))

    def test_unbound_and_illegal_sources_keep_correction_possible(self):
        for field in ("fuel.lhv", "fuel.fch", "fuel.oxidation"):
            out = evaluate_fuel_power_field(field, {"origin": "CUSTOM", "binding_status": "ABSENT", "business_source": "MEASURED"})
            self.assertEqual(out["status"], "READY")
            self.assertEqual(out["source_qualification"]["value"]["values"], ["MEASURED"])
            self.assertEqual(out["default"]["value"], {"state": "NONE"})
        out = evaluate_fuel_power_field("fuel.fch", {"origin": "CUSTOM", "binding_status": "ABSENT", "business_source": "CALCULATED"})
        self.assertEqual(out["status"], "BLOCKED")
        self.assertEqual(out["locking"]["source"]["state"], "EDITABLE")
        self.assertIn("SOURCE_NOT_ALLOWED", {item["code"] for item in out["problems"]})
        direct = evaluate_fuel_power_field("fuel.direct_carbon", {"origin": "CUSTOM", "business_source": "CALCULATED"})
        self.assertEqual(direct["status"], "READY")
        self.assertEqual(direct["source_qualification"]["value"]["values"], ["CALCULATED", "MEASURED"])

    def test_exact_binding_and_selected_source_control_effective_lock(self):
        context = {"origin": "CATALOG", "binding_status": "VERIFIED", "parameter_id": "natural_gas_carbon_content", "binding_id": "binding-natural_gas_carbon_content_gbt32151_34_c1"}
        out = evaluate_fuel_power_field("fuel.fch", {**context, "business_source": "STANDARD_DEFAULT"})
        self.assertEqual(out["status"], "READY")
        self.assertEqual(out["locking"]["value"]["state"], "LOCKED")
        measured = evaluate_fuel_power_field("fuel.fch", {**context, "business_source": "MEASURED"})
        self.assertEqual(measured["default_source"]["value"]["source"], "STANDARD_DEFAULT")
        self.assertEqual(measured["default"]["value"], {"state": "NONE"})
        self.assertEqual(measured["locking"]["value"]["state"], "EDITABLE")
        mismatch = evaluate_fuel_power_field("fuel.fch", {**context, "binding_id": "wrong", "business_source": "STANDARD_DEFAULT"})
        self.assertEqual(mismatch["status"], "BLOCKED")

    def test_electricity_five_tables_and_other_zero_are_independent(self):
        self.assertEqual(electricity_catalogue_parameters(), (
            ("1", "electricity_emission_factor_national", None),
            ("2", "electricity_emission_factor_regional_average", "region"),
            ("3", "electricity_emission_factor_provincial_average", "province"),
            ("4", "electricity_emission_factor_national_average_excluding_market_nonfossil", None),
            ("5", "electricity_emission_factor_national_fossil", None),
        ))
        common = {"source_path": "ARBITRARY_OVERRIDE", "direction": "PURCHASED", "attribute": "CONVENTIONAL", "business_source": "OTHER"}
        ordinary = evaluate_fuel_power_field("electricity.factor", common)
        self.assertEqual(ordinary["status"], "READY")
        self.assertEqual(ordinary["default_source"]["value"]["state"], "NONE")
        nonfossil = evaluate_fuel_power_field("electricity.factor", {**common, "attribute": "NONFOSSIL"})
        self.assertEqual(nonfossil["status"], "BLOCKED")
        exported = evaluate_fuel_power_field("electricity.factor", {**common, "direction": "EXPORTED", "attribute": "NONFOSSIL"})
        self.assertEqual(exported["status"], "READY")

    def test_missing_ambiguous_and_malformed_context_fail_explicitly(self):
        missing = evaluate_fuel_power_field("fuel.fch", {})
        self.assertEqual(missing["status"], "BLOCKED")
        self.assertIn("MISSING_CONTEXT", {p["code"] for p in missing["problems"]})
        with self.assertRaises(ValueError):
            evaluate_fuel_power_field("fuel.fch", {"binding_status": True})
        with self.assertRaises(ValueError):
            evaluate_fuel_power_field("heat.factor", {})
        policy = {"id": "p", "property": "default", "branches": [
            {"id": "a", "when": {"tags": {}, "ranges": {}}, "value": {"state": "NONE"}},
            {"id": "b", "when": {"tags": {}, "ranges": {}}, "value": {"state": "NONE"}},
        ]}
        self.assertEqual(apply_policy(policy, {})["status"], "AMBIGUOUS_POLICY_MATCH")

    def test_review_and_runtime_use_identical_final_outcomes(self):
        from packages.application.business_rules_candidate import load_bundle
        bundle = load_bundle(ROOT / path for path in SOURCE_PATHS)
        for field_id, entry in _document()["fields"].items():
            contexts = [branch["when"]["tags"] for policy in entry["policies"].values() for branch in policy["branches"]]
            for context in contexts:
                if any(key in context for key in ("carbonate_component_count",)):
                    continue
                expected = next(iter(bundle.apply_context(context, field_ids=[field_id])["outcomes"].values()))
                self.assertEqual(evaluate_fuel_power_field(field_id, context), expected)
