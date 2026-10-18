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


class FGDDomainSpecialistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FGDResolverSpecialistTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        FGDResolverSpecialistTests.tearDownClass.__func__(cls)

    resolve = FGDResolverSpecialistTests.resolve
    mutated_resolver = FGDResolverSpecialistTests.mutated_resolver
    targets = FGDResolverSpecialistTests.targets

    def parameter(self, field, label="CaCO3", *, value=None, unit=None, custom=False):
        from packages.standards.carbon_material import ParameterValue, ParameterSourceKind
        if value is not None:
            return ParameterValue("test.fgd." + field, value, unit or ("tCO2/t" if field == "fgd.factor" else "ratio"),
                                  ParameterSourceKind.MEASURED, "TEST-FGD-M", "2026", "独立测试实测数值", "独立测试")
        selected = self.resolve(field, carbonate_type=label, origin="CUSTOM" if custom else "CATALOG")
        factor = selected.factor
        self.assertIsNotNone(factor)
        return ParameterValue(factor.parameter_id, factor.value, factor.unit,
                              ParameterSourceKind.STANDARD_SPECIFIED if field == "fgd.factor" else ParameterSourceKind.STANDARD_DEFAULT,
                              factor.source_id, factor.version, factor.source_location,
                              "真实Resolver已选因子", factor.factor_id, factor.factor_year)

    def component(self, label="CaCO3", amount="10", *, fraction=None, conversion=None,
                  factor=None, component_id="component-A", custom=False):
        from packages.standards.carbon_material import CarbonateComponent, InputOrigin
        return CarbonateComponent(amount,
            self.parameter("fgd.ratio", label, value=fraction, custom=custom),
            self.parameter("fgd.factor", label, value=factor, custom=custom),
            self.parameter("fgd.conversion", label, value=conversion, custom=custom),
            label, InputOrigin.CUSTOM if custom else InputOrigin.CATALOG, component_id)

    def batch(self, components, batch_id="batch-A", facility_id="facility-A", **kwargs):
        from packages.standards.carbon_material import FGDInput
        defaults = dict(instance_id=batch_id, reagent_name="同名脱硫剂", facility_id=facility_id,
                        facility_name="同名设施", batch_id=batch_id, execution_version="FGD_V2")
        defaults.update(kwargs)
        return FGDInput(components=tuple(components), **defaults)

    def payload(self, *batches):
        from packages.standards.carbon_material import CarbonMaterialInput
        return CarbonMaterialInput("fgd-specialist", "enterprise.fgd", "脱硫测试", PERIOD,
            boundary_confirmed=True, fgd_units=tuple(batches), material_execution_version="MATERIAL_V2")

    def calculate(self, *batches, policy=None):
        from packages.standards.carbon_material import CarbonMaterialCalculator
        return CarbonMaterialCalculator(policy=policy, parameter_resolver=self.resolver).calculate(self.payload(*batches))

    def assert_rejected_without_record(self, *batches, code=None, resolver=None):
        from packages.application.carbon_accounting import CarbonAccountingUseCase
        from packages.persistence import SQLiteRecordRepository
        from packages.standards.carbon_material import CarbonMaterialCalculator
        with tempfile.TemporaryDirectory(prefix="record-", dir=self.root) as directory:
            path = Path(directory) / "records.sqlite"
            repository = SQLiteRecordRepository(path)
            usecase = CarbonAccountingUseCase(CarbonMaterialCalculator(parameter_resolver=resolver or self.resolver), repository)
            result = usecase.calculate(self.payload(*batches))
            self.assertTrue(result.blocked, result.problems)
            self.assertIsNone(result.record)
            self.assertEqual(SQLiteRecordRepository(path).list_all(), ())
            if code:
                self.assertIn(code, {problem.code for problem in result.problems})
            return result

    def test_eleven_c2_formal_single_batches_match_independent_table(self):
        from packages.application.carbon_accounting import CarbonAccountingUseCase
        from packages.persistence import SQLiteRecordRepository
        from packages.standards.carbon_material import CarbonMaterialCalculator
        with tempfile.TemporaryDirectory(prefix="eleven-records-", dir=self.root) as directory:
            path = Path(directory) / "records.sqlite"
            usecase = CarbonAccountingUseCase(CarbonMaterialCalculator(parameter_resolver=self.resolver), SQLiteRecordRepository(path))
            for index, (label, _key, _factor, expected) in enumerate(C2, 1):
                with self.subTest(species=label):
                    outcome = usecase.calculate(self.payload(self.batch((self.component(label),))))
                    self.assertTrue(outcome.successful, outcome.problems)
                    self.assertEqual(outcome.result.total_amount, Decimal(expected))
                    self.assertEqual(outcome.record.algorithm_version, "CAR-SM01-2026-10-18-HEAT.1")
                    self.assertEqual(len(SQLiteRecordRepository(path).list_all()), index)

    def mixed_components(self):
        return (self.component("CaCO3", fraction=".4", conversion=".8", component_id="ca"),
                self.component("MgCO3", fraction=".3", conversion=".9", component_id="mg"))

    def test_mixed_batch_whole_reagent_denominator_is_not_renormalized(self):
        result = self.calculate(self.batch(self.mixed_components()))
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, Decimal("2.8174"))

    def test_same_facility_two_batches_do_not_add_their_fractions(self):
        result = self.calculate(self.batch((self.component(amount="10"),), "batch-A"),
                                self.batch((self.component(amount="20"),), "batch-B"))
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, Decimal("11.88"))

    def test_same_batch_id_in_different_facilities_is_independent(self):
        first = self.batch((self.component(),), facility_id="facility-A", instance_id="row-A")
        second = self.batch((self.component(),), facility_id="facility-B", instance_id="row-B")
        result = self.calculate(first, second)
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, Decimal("7.92"))

    def test_batch_fraction_exact_one_is_valid_but_above_one_is_not(self):
        from dataclasses import replace
        ca = self.component(fraction=".5", component_id="ca")
        mg = self.component("MgCO3", fraction=".5", component_id="mg")
        equal = self.calculate(self.batch((ca, mg)))
        self.assertTrue(equal.successful, equal.problems)
        self.assertEqual(equal.result.total_amount, Decimal("4.81"))
        too_high = replace(mg, carbonate_fraction=self.parameter("fgd.ratio", value=".500000000000000000000000000001"))
        self.assert_rejected_without_record(self.batch((ca, too_high)), code="CAR-VAL-CARBONATE-SUM")

    def test_same_batch_cal_inconsistency_is_rejected_without_record(self):
        from dataclasses import replace
        components = self.mixed_components()
        self.assert_rejected_without_record(self.batch((components[0], replace(components[1], amount="12"))),
                                            code="CAR-VAL-FGD-BATCH-AMOUNT")

    def test_mass_units_are_normalized_once_before_same_batch_check(self):
        from dataclasses import replace
        from packages.standards.carbon_material import InputValue
        components = self.mixed_components()
        result = self.calculate(self.batch((components[0], replace(components[1], amount=InputValue("10000", "kg")))))
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, Decimal("2.8174"))

    def test_blank_and_zero_are_distinct_for_cal_i_tr_and_ef(self):
        from dataclasses import replace
        component = self.component(custom=True, label="未登记物种", factor=".5", fraction="0", conversion="0")
        for field in ("amount", "carbonate_fraction", "conversion_rate", "emission_factor"):
            with self.subTest(missing=field):
                self.assert_rejected_without_record(self.batch((replace(component, **{field: None}),)))
        for field in ("amount", "carbonate_fraction", "conversion_rate", "emission_factor"):
            with self.subTest(zero=field):
                if field == "amount":
                    changed = replace(component, amount="0")
                else:
                    policy_field = {"carbonate_fraction": "fgd.ratio", "conversion_rate": "fgd.conversion", "emission_factor": "fgd.factor"}[field]
                    changed = replace(component, **{field: self.parameter(policy_field, value="0")})
                result = self.calculate(self.batch((changed,)))
                self.assertTrue(result.successful, result.problems)
                self.assertEqual(result.result.total_amount, Decimal("0"))

    def test_duplicate_component_or_facility_batch_ids_never_create_record(self):
        from dataclasses import replace
        components = self.mixed_components()
        duplicate_component = replace(components[1], component_id=components[0].component_id)
        self.assert_rejected_without_record(self.batch((components[0], duplicate_component)), code="CAR-VAL-FGD-IDENTITY")
        first = self.batch((self.component(),), instance_id="row-A")
        second = replace(first, instance_id="row-B")
        self.assert_rejected_without_record(first, second, code="CAR-VAL-FGD-BATCH-DUPLICATE")

    def test_missing_stable_identity_and_unknown_version_never_create_record(self):
        from dataclasses import replace
        batch = self.batch((self.component(),))
        for changed in (replace(batch, facility_id=None), replace(batch, batch_id=None),
                        replace(batch, components=(replace(batch.components[0], component_id=None),))):
            self.assert_rejected_without_record(changed, code="CAR-VAL-FGD-IDENTITY")
        self.assert_rejected_without_record(replace(batch, execution_version="FGD_FUTURE"), code="CAR-VAL-FGD-VERSION")

    def test_custom_measured_ef_uses_independent_general_i_and_tr(self):
        result = self.calculate(self.batch((self.component("未登记物种", factor=".5", custom=True),)))
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, Decimal("4.5"))

    def test_measured_and_default_i_same_value_are_not_interchangeable_in_multicomponent_batch(self):
        ca = self.component(fraction=None, component_id="ca")
        mg = self.component("MgCO3", fraction=".1", component_id="mg")
        self.assert_rejected_without_record(self.batch((ca, mg)))

    def test_corrupt_asset_unit_year_or_period_is_rejected_by_formal_application(self):
        # Input was built from the genuine catalog before its isolated copy is
        # corrupted. Formal Application must re-check; successful API tests
        # alone are not evidence that a caller cannot bypass the boundary.
        batch = self.batch((self.component(),))
        for field, factor_id, other, bad_unit in self.targets():
            for kind, statements in (
                ("asset", (("UPDATE reference_data_bindings SET asset_id=? WHERE binding_id=?", ("asset-" + other, "binding-" + factor_id)),)),
                ("unit", (("UPDATE factor_values SET unit=?, normalized_unit=? WHERE factor_id=?", (bad_unit, bad_unit, factor_id)),
                          ("UPDATE reference_data_assets SET unit=?, normalized_unit=? WHERE asset_id=?", (bad_unit, bad_unit, "asset-" + factor_id)))),
                ("year", (("UPDATE factor_values SET factor_year=? WHERE factor_id=?", (2099, factor_id)),
                          ("UPDATE reference_data_bindings SET factor_year=? WHERE binding_id=?", (2099, "binding-" + factor_id)))),
                ("period", (("UPDATE factor_values SET valid_to=? WHERE factor_id=?", ("2025-12-31", factor_id)),
                            ("UPDATE reference_data_bindings SET valid_to=? WHERE binding_id=?", ("2025-12-31", "binding-" + factor_id)))),
            ):
                with self.subTest(field=field, corruption=kind):
                    self.assert_rejected_without_record(batch, resolver=self.mutated_resolver(*statements))

    def test_actual_declared_profile_is_consumed_independently_of_ambient_decimal(self):
        from decimal import localcontext, ROUND_DOWN, ROUND_HALF_UP
        from packages.core.decimal_policy import DecimalPolicy
        from packages.standards import carbon_material as module
        from packages.standards._numeric_authority import current_declared_numeric_profile
        component = self.component("未登记物种", amount="9.87654321098765432109876543210987654321",
            fraction=".123456789012345678901234567890123456789",
            conversion=".987654321098765432109876543210987654321",
            factor=".555555555555555555555555555555555555555", custom=True)
        batch = self.batch((component,))
        policy = DecimalPolicy(precision=50)
        consumed = []
        original = module.fgd_emission
        def observed(components):
            consumed.append(current_declared_numeric_profile())
            return original(components)
        with patch.object(module, "fgd_emission", observed):
            with localcontext() as context:
                context.prec = 6
                context.rounding = ROUND_DOWN
                low = self.calculate(batch, policy=policy)
            with localcontext() as context:
                context.prec = 70
                high = self.calculate(batch, policy=policy)
        self.assertTrue(low.successful, low.problems)
        self.assertTrue(high.successful, high.problems)
        self.assertEqual(consumed, [policy, policy])
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_HALF_UP
            expected = (Decimal("9.87654321098765432109876543210987654321")
                * Decimal(".123456789012345678901234567890123456789")
                * Decimal(".555555555555555555555555555555555555555")
                * Decimal(".987654321098765432109876543210987654321"))
        self.assertEqual(low.result.total_amount, expected)
        self.assertEqual(high.result.total_amount, expected)
        self.assertNotEqual(self.calculate(batch).result.total_amount, expected)

    def test_old_codec_1_and_2_restore_without_fabricating_new_identities(self):
        import json
        from packages.application import carbon_material_input_codec as codec
        original = self.payload(self.batch((self.component(),)))
        def strip_new_fields(node):
            if isinstance(node, dict):
                if node.get("type") == "fgd_input" and node.get("$kind") == "dataclass":
                    for key in ("facility_id", "facility_name", "batch_id", "execution_version"):
                        node["fields"].pop(key, None)
                if node.get("type") == "carbonate_component" and node.get("$kind") == "dataclass":
                    node["fields"].pop("component_id", None)
                for child in node.values():
                    strip_new_fields(child)
            elif isinstance(node, list):
                for child in node:
                    strip_new_fields(child)
        for version in (1, 2):
            with self.subTest(version=version):
                document = json.loads(codec.encode_canonical_input(original))
                document["version"] = version
                strip_new_fields(document)
                payload = json.dumps(document, ensure_ascii=False)
                restored = codec.decode_canonical_input(payload)
                self.assertIsNone(restored.fgd_units[0].facility_id)
                self.assertIsNone(restored.fgd_units[0].batch_id)
                self.assertIsNone(restored.fgd_units[0].components[0].component_id)
                self.assertEqual(restored.fgd_units[0].execution_version, "FGD_V1")
                self.assertEqual(restored.fgd_units[0].components[0].amount.value, Decimal("10"))
                self.assertEqual(json.loads(payload), document)


if __name__ == "__main__":
    unittest.main()
