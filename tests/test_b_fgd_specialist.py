"""Independent FGD policy/Resolver expectations: Mapping 9.1/9.3 and Issue016.

Table values below are literal Mapping evidence, never derived from a current
Calculator. Batch/GUI/full-record consumers remain with the integration owner.
"""
from contextlib import closing
from copy import deepcopy
from datetime import date
from decimal import Decimal
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.core.models import AccountingPeriod, PeriodType
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.standards.carbon_material_business_policy import (
    BusinessPolicyConfigurationError, _fgd_document, evaluate_fgd_field,
    fgd_binding_conditions, fgd_policy_identity, resolve_fgd_field,
)
from scripts.project_fgd_rules import verify_fgd_projection

# Exact C.2 identities and values, Mapping 9.3, PDF27/printed19.
C2 = (
    ("CaCO3", "caco3", "0.440", "3.96"),
    ("MgCO3", "mgco3", "0.522", "4.698"),
    ("Na2CO3", "na2co3", "0.415", "3.735"),
    ("NaHCO3", "nahco3", "0.524", "4.716"),
    ("FeCO3", "feco3", "0.380", "3.42"),
    ("MnCO3", "mnco3", "0.383", "3.447"),
    ("BaCO3", "baco3", "0.223", "2.007"),
    ("Li2CO3", "li2co3", "0.595", "5.355"),
    ("K2CO3", "k2co3", "0.318", "2.862"),
    ("SrCO3", "srco3", "0.298", "2.682"),
    ("CaMg(CO3)2", "camgco3_2", "0.477", "4.293"),
)
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31))
CA_FACTOR = "carbonate_caco3_gbt32151_34_c2"
CA_BINDING = "binding-" + CA_FACTOR
CA_ASSET = "asset-" + CA_FACTOR


class FGDResolverSpecialistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="ghg-fgd-M-")
        cls.root = Path(cls.temporary.name)
        cls.catalog_path = build_catalog_database(output_path=cls.root / "catalog.sqlite")
        cls.repository = SQLiteCatalogRepository(cls.catalog_path)
        cls.resolver = create_g06_parameter_resolver(cls.repository)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def resolve(self, field="fgd.factor", **kwargs):
        defaults = dict(resolver=self.resolver, origin="CATALOG", carbonate_type="CaCO3", accounting_period=PERIOD)
        defaults.update(kwargs)
        return resolve_fgd_field(field, **defaults)

    def outcome(self, field, resolved, source="STANDARD_DEFAULT"):
        return evaluate_fgd_field(field, {**resolved.context, "business_source": source})

    def mutated_resolver(self, *statements):
        # Only a private copy is changed; no user/reference database is opened.
        directory = tempfile.TemporaryDirectory(prefix="corrupt-", dir=self.root)
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "catalog.sqlite"
        shutil.copyfile(self.catalog_path, path)
        with closing(sqlite3.connect(path)) as connection:
            with connection:
                for query, args in statements:
                    connection.execute(query, args)
        return create_g06_parameter_resolver(SQLiteCatalogRepository(path))

    def assert_no_default(self, field, resolver):
        selected = self.resolve(field, resolver=resolver)
        self.assertNotEqual(selected.context["binding_status"], "VERIFIED")
        self.assertIsNone(selected.factor)
        self.assertEqual(self.outcome(field, selected)["status"], "BLOCKED")
        return selected

    def test_all_eleven_c2_bindings_values_and_locks_use_the_actual_resolution(self):
        for label, key, expected_factor, expected_ten_tonnes in C2:
            with self.subTest(species=label):
                selected = self.resolve(carbonate_type=label)
                self.assertEqual(selected.context["binding_status"], "VERIFIED")
                self.assertEqual(selected.context["binding_id"], f"binding-carbonate_{key}_gbt32151_34_c2")
                self.assertEqual(selected.factor.value, Decimal(expected_factor))
                self.assertEqual(selected.factor.unit, "tCO2/t")
                self.assertEqual(selected.factor.factor_year, 2024)
                self.assertIs(selected.factor, selected.resolution.recommended.factor)
                association = self.resolver.reference_binding_for(selected.resolution)
                self.assertEqual(association.status, "VERIFIED")
                self.assertEqual(association.binding.binding_id, selected.context["binding_id"])
                outcome = self.outcome("fgd.factor", selected)
                self.assertEqual(outcome["status"], "READY")
                self.assertEqual(outcome["source_qualification"]["value"]["values"], ["STANDARD_DEFAULT"])
                self.assertEqual(outcome["locking"]["value"]["state"], "LOCKED")
                self.assertEqual(outcome["locking"]["source"]["state"], "LOCKED")
                # Literal independent example for the 10t/.9/1 case.
                self.assertEqual(Decimal("10") * Decimal(".9") * Decimal(expected_factor), Decimal(expected_ten_tonnes))

    def test_i_and_tr_general_bindings_apply_to_custom_species_independently(self):
        for field, factor_id, expected in (
            ("fgd.ratio", "fgd_carbonate_content_default_gbt32151_34_2024", ".9"),
            ("fgd.conversion", "fgd_conversion_rate_default_gbt32151_34_2024", "1"),
        ):
            with self.subTest(field=field):
                selected = self.resolve(field, origin="CUSTOM", carbonate_type="未登记物种")
                self.assertEqual(selected.context["binding_status"], "VERIFIED")
                self.assertEqual(selected.context["binding_id"], "binding-" + factor_id)
                self.assertEqual(selected.factor.subject_id, "fgd")
                self.assertEqual(selected.factor.value, Decimal(expected))
                self.assertEqual(self.outcome(field, selected)["status"], "READY")
                measured = self.outcome(field, selected, "MEASURED")
                self.assertEqual(measured["status"], "READY")
                self.assertEqual(measured["default"]["value"]["state"], "NONE")
                self.assertEqual(measured["locking"]["value"]["state"], "EDITABLE")

    def test_multi_component_ratio_does_not_copy_single_component_default(self):
        single = self.resolve("fgd.ratio", component_count=1)
        multi = self.resolve("fgd.ratio", component_count=2)
        self.assertEqual(single.factor.value, Decimal(".9"))
        self.assertIsNone(multi.factor)
        self.assertEqual(self.outcome("fgd.ratio", multi)["status"], "BLOCKED")
        self.assertEqual(self.outcome("fgd.ratio", multi, "MEASURED")["status"], "READY")
        returned = self.resolve("fgd.ratio", component_count=1)
        self.assertEqual(returned.context, single.context)
        self.assertEqual(returned.factor, single.factor)
        # This API establishes eligibility only, not a GUI draft write command.

    def test_custom_unmatched_factor_accepts_measured_and_never_chemical_or_default(self):
        custom = self.resolve(origin="CUSTOM", carbonate_type="CaCO2")
        self.assertIsNone(custom.factor)
        self.assertEqual(self.outcome("fgd.factor", custom, "MEASURED")["status"], "READY")
        for invalid_source in ("STANDARD_DEFAULT", "CALCULATED", "USER_DEFINED"):
            self.assertEqual(self.outcome("fgd.factor", custom, invalid_source)["status"], "BLOCKED")

    def test_unconfirmed_or_invalid_catalog_identity_is_not_guessed(self):
        for origin, label in (("LEGACY_UNSPECIFIED", "CaCO3"), ("CATALOG", "CaCO2")):
            with self.subTest(origin=origin, species=label):
                result = self.resolve(origin=origin, carbonate_type=label)
                self.assertIsNone(result.factor)
                self.assertEqual(self.outcome("fgd.factor", result)["status"], "BLOCKED")

    def test_missing_resolver_or_wrong_selected_factor_never_silently_reselects(self):
        self.assert_no_default("fgd.factor", None)
        selected = self.resolve(selected_factor_id="carbonate_mgco3_gbt32151_34_c2")
        self.assertIsNone(selected.factor)
        self.assertEqual(self.outcome("fgd.factor", selected)["status"], "BLOCKED")

    def targets(self):
        return (
            ("fgd.factor", CA_FACTOR, "carbonate_mgco3_gbt32151_34_c2", "tCO2/GJ"),
            ("fgd.ratio", "fgd_carbonate_content_default_gbt32151_34_2024", "fgd_conversion_rate_default_gbt32151_34_2024", "t"),
            ("fgd.conversion", "fgd_conversion_rate_default_gbt32151_34_2024", "fgd_carbonate_content_default_gbt32151_34_2024", "t"),
        )

    def test_wrong_asset_is_not_a_valid_binding_for_any_fgd_field(self):
        for field, factor_id, other, _unit in self.targets():
            with self.subTest(field=field):
                resolver = self.mutated_resolver((
                    "UPDATE reference_data_bindings SET asset_id=? WHERE binding_id=?",
                    ("asset-" + other, "binding-" + factor_id),
                ))
                self.assert_no_default(field, resolver)

    def test_wrong_units_even_when_factor_and_asset_agree_are_rejected(self):
        for field, factor_id, _other, unit in self.targets():
            with self.subTest(field=field):
                resolver = self.mutated_resolver(
                    ("UPDATE factor_values SET unit=?, normalized_unit=? WHERE factor_id=?", (unit, unit, factor_id)),
                    ("UPDATE reference_data_assets SET unit=?, normalized_unit=? WHERE asset_id=?", (unit, unit, "asset-" + factor_id)),
                )
                self.assert_no_default(field, resolver)

    def test_wrong_year_even_when_binding_and_factor_agree_is_rejected(self):
        for field, factor_id, _other, _unit in self.targets():
            with self.subTest(field=field):
                resolver = self.mutated_resolver(
                    ("UPDATE factor_values SET factor_year=? WHERE factor_id=?", (2099, factor_id)),
                    ("UPDATE reference_data_bindings SET factor_year=? WHERE binding_id=?", (2099, "binding-" + factor_id)),
                )
                self.assert_no_default(field, resolver)

    def test_expired_period_does_not_return_an_automatic_current_default(self):
        for field, factor_id, _other, _unit in self.targets():
            with self.subTest(field=field):
                resolver = self.mutated_resolver(
                    ("UPDATE factor_values SET valid_to=? WHERE factor_id=?", ("2025-12-31", factor_id)),
                    ("UPDATE reference_data_bindings SET valid_to=? WHERE binding_id=?", ("2025-12-31", "binding-" + factor_id)),
                )
                self.assert_no_default(field, resolver)

    def test_wrong_table_is_not_accepted_merely_because_official_source_matches(self):
        resolver = self.mutated_resolver((
            "UPDATE reference_data_bindings SET source_table_id=? WHERE binding_id=?", ("tab-32151-34-c1", CA_BINDING),
        ))
        self.assert_no_default("fgd.factor", resolver)

    def test_binding_absence_does_not_invent_a_default(self):
        resolver = self.mutated_resolver(("DELETE FROM reference_data_bindings WHERE binding_id=?", (CA_BINDING,)))
        self.assert_no_default("fgd.factor", resolver)

    def test_invalid_component_counts_are_not_treated_as_one(self):
        for count in (0, -1, True, 1.0, "1"):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    self.resolve("fgd.ratio", component_count=count)

    def test_configuration_projection_and_return_values_are_isolated(self):
        verify_fgd_projection()
        original = fgd_policy_identity()
        self.assertEqual(original["adopted_fields"], ["fgd.conversion", "fgd.factor", "fgd.ratio"])
        altered = deepcopy(original)
        altered["adopted_fields"].append("not-adopted")
        self.assertEqual(fgd_policy_identity(), original)
        conditions = fgd_binding_conditions("fgd.factor")
        conditions[0]["binding_id"] = "changed"
        self.assertNotIn("changed", [row["binding_id"] for row in fgd_binding_conditions("fgd.factor")])
        selected = self.resolve()
        first = self.outcome("fgd.factor", selected)
        first["source_qualification"]["value"]["values"].append("CALCULATED")
        self.assertNotIn("CALCULATED", self.outcome("fgd.factor", selected)["source_qualification"]["value"]["values"])

    def test_missing_resource_never_falls_back_to_the_old_boolean_policy(self):
        _fgd_document.cache_clear()
        try:
            with patch("packages.standards.carbon_material_business_policy.files", side_effect=FileNotFoundError):
                with self.assertRaises(BusinessPolicyConfigurationError):
                    evaluate_fgd_field("fgd.factor", {"binding_status": "ABSENT", "business_source": "MEASURED"})
        finally:
            _fgd_document.cache_clear()


if __name__ == "__main__":
    unittest.main()
