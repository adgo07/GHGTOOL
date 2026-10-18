"""Issue015/017 独立业务预期；自动 IF97/整链验收不由本文件冒充。

Mapping TV-CAR-POL-006/012：1000kg×2800kJ/kg=2800000kJ=2.8GJ，
2.8GJ×.11tCO2/GJ=.308tCO2。单位等价与源边界分别核验。
"""
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import unittest
from unittest.mock import patch

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitService
from packages.standards._numeric_authority import declared_numeric_profile
from packages.standards.carbon_material import (
    CarbonMaterialCalculator, HeatInput, InputValue, SteamEnthalpyEvaluation,
    SteamKind, purchased_heat_emission,
)
from packages.standards.carbon_material_heat import (
    KNOWN_ENTHALPY_METHOD_VERSION, classify_heat_boundary, evaluate_known_enthalpy,
)

PROFILE = "GHGTOOL_CARBON_DECIMAL40_CURRENT"
POLICY = DecimalPolicy()


def known(enthalpy="2800", **kwargs):
    return HeatInput("steam-1", "1000", enthalpy=enthalpy, manual_enthalpy=True, **kwargs)


def evaluate(line, *, policy=POLICY, profile=PROFILE):
    return evaluate_known_enthalpy(line, policy=policy, numeric_profile_id=profile)


class KnownEnthalpyTests(unittest.TestCase):
    def test_original_formula_independent_0308_expected(self):
        line = known()
        adopted = evaluate(line)
        # 原式由既有helper执行；预期来自以上独立量纲推导，不从其输出反制。
        with declared_numeric_profile(POLICY):
            amount = purchased_heat_emission("1000", adopted.value, ".11")
        self.assertEqual(amount, Decimal(".308"))
        self.assertEqual(adopted.value, Decimal("2800"))

    def test_supported_specific_energy_units_are_equivalent(self):
        expected = Decimal("2800")
        for value, unit in (("2800", "kJ/kg"), (".0028", "GJ/kg"), ("2.8", "GJ/t")):
            with self.subTest(unit=unit):
                line = known(InputValue(value, unit))
                result = evaluate(line)
                self.assertEqual(result.value, expected)
                self.assertEqual(line.enthalpy.value, Decimal(value))
                self.assertEqual(line.enthalpy.unit, unit)

    def test_mass_t_and_kg_equivalence_uses_existing_mass_unit_service(self):
        units = UnitService(POLICY)
        adopted = evaluate(known()).value
        with declared_numeric_profile(POLICY):
            kg_result = purchased_heat_emission(units.convert("1000", "kg", "kg"), adopted, ".11")
            t_result = purchased_heat_emission(units.convert("1", "t", "kg"), adopted, ".11")
        self.assertEqual(t_result, kg_result)
        self.assertEqual(t_result, Decimal(".308"))

    def test_result_is_existing_type_without_table_or_automatic_reference(self):
        result = evaluate(known())
        self.assertIsInstance(result, SteamEnthalpyEvaluation)
        self.assertEqual(result.source, "USER_MANUAL")
        self.assertIsNone(result.reference_value)
        self.assertIsNone(result.table_id)
        self.assertFalse(result.interpolated)
        self.assertIsNone(result.pressure_bounds)
        self.assertIsNone(result.temperature_bounds)
        self.assertEqual(KNOWN_ENTHALPY_METHOD_VERSION, "CAR-HEAT-KNOWN-017.1")

    def test_auxiliary_auto_failure_and_invalid_pressure_do_not_block_known_value(self):
        line = known(pressure_mpa=InputValue("999999", "MPa"), temperature_c="-1000",
                     steam_kind=SteamKind.SUPERHEATED)
        with patch.object(CarbonMaterialCalculator, "_steam_reference", side_effect=AssertionError("不得访问自动参考")), \
                patch("packages.standards.carbon_material.saturated_steam_enthalpy", side_effect=AssertionError("不得访问C.4")), \
                patch("packages.standards.carbon_material.superheated_steam_enthalpy", side_effect=AssertionError("不得访问C.5")):
            self.assertEqual(evaluate(line).value, Decimal("2800"))

    def test_amount_factor_and_evidence_are_not_required_to_invent_known_enthalpy(self):
        line = HeatInput("known-alone", None, enthalpy="2800", manual_enthalpy=True)
        self.assertEqual(evaluate(line).value, Decimal("2800"))
        self.assertIsNone(line.amount)
        self.assertIsNone(line.factor)

    def test_zero_and_negative_finite_values_are_preserved_for_c_warning(self):
        for value in ("0", "-1", "-0.0001"):
            with self.subTest(value=value):
                self.assertEqual(evaluate(known(value)).value, Decimal(value))

    def test_missing_known_value_does_not_fall_back_to_pressure_or_other_numbers(self):
        line = HeatInput("missing", "1000", enthalpy=None, manual_enthalpy=True,
                         pressure_mpa="1", temperature_c="300")
        with self.assertRaises(DomainValidationError):
            evaluate(line)

    def test_automatic_path_cannot_be_used_as_known_value(self):
        line = HeatInput("auto", "1000", manual_enthalpy=False, pressure_mpa="1")
        with self.assertRaisesRegex(DomainValidationError, "路径"):
            evaluate(line)

    def test_wrong_or_unapproved_specific_energy_units_fail(self):
        for unit in ("kg", "GJ", "J/kg", "kWh/kg", "MPa", "heat_kj_per_kg"):
            with self.subTest(unit=unit):
                with self.assertRaises(DomainValidationError):
                    evaluate(known(InputValue("2800", unit)))

    def test_direct_helper_revalidates_nonfinite_float_and_boolean_values(self):
        # 模拟损坏/绕过构造门禁的领域载荷，正式helper仍不得消费非法值。
        for value in (Decimal("NaN"), Decimal("Infinity"), "NaN", "", None, 2800.0, True):
            with self.subTest(value=value):
                line = known()
                object.__setattr__(line.enthalpy, "value", value)
                with self.assertRaises(DomainValidationError):
                    evaluate(line)

    def test_declared_policy_propagates_and_caller_context_cannot_change_adoption(self):
        raw = "2.1234567890123456789012345678901234567890123456789"
        line = known(InputValue(raw, "GJ/t"))
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_DOWN)):
            policy = DecimalPolicy(precision=precision, rounding=rounding)
            with localcontext() as context:
                context.prec, context.rounding = precision, rounding
                expected = (Decimal(raw) * Decimal("1000")) / Decimal("1")
            for ambient in (6, 17, 60):
                with self.subTest(precision=precision, ambient=ambient):
                    with localcontext() as context:
                        context.prec, context.rounding = ambient, ROUND_DOWN
                        result = evaluate(line, policy=policy, profile=f"TEST_P{precision}_{rounding}")
                        self.assertEqual(result.value, expected)
                        self.assertEqual(context.prec, ambient)
                        self.assertEqual(context.rounding, ROUND_DOWN)
        self.assertEqual(line.enthalpy.value, Decimal(raw))

    def test_invalid_profile_claim_or_missing_declaration_fails(self):
        for profile in ("", " ", None, " leading"):
            with self.subTest(profile=profile):
                with self.assertRaises(DomainValidationError):
                    evaluate(known(), profile=profile)
        for policy in (None, DecimalPolicy(precision=28), DecimalPolicy(rounding=ROUND_DOWN)):
            with self.subTest(policy=policy):
                with self.assertRaises(DomainValidationError):
                    evaluate(known(), policy=policy)

    def test_input_and_result_remain_immutable(self):
        line = known()
        result = evaluate(line)
        with self.assertRaises(FrozenInstanceError):
            result.value = Decimal(0)
        self.assertEqual(line.enthalpy.value, Decimal("2800"))


class HeatBoundaryTests(unittest.TestCase):
    def classify(self, boundary, accounted=None, direction="purchased_heat"):
        return classify_heat_boundary(energy_direction=direction, source_boundary=boundary,
                                      fuel_emissions_accounted=accounted)

    def test_external_heat_is_purchased_with_false_or_unstated_supplier_fuel(self):
        for accounted in (False, None):
            with self.subTest(accounted=accounted):
                self.assertEqual(self.classify("OUTSIDE_ENTERPRISE", accounted), "PURCHASED")

    def test_external_heat_conflicting_enterprise_fuel_is_rejected_not_deleted(self):
        with self.assertRaisesRegex(DomainValidationError, "冲突"):
            self.classify("OUTSIDE_ENTERPRISE", True)

    def test_internal_already_accounted_returns_dispatch_without_requiring_heat_values(self):
        status = self.classify("INSIDE_ENTERPRISE", True)
        self.assertEqual(status, "INTERNAL_ALREADY_ACCOUNTED")
        # C按分派标识跳过重复购热；正式保留原燃料10需由整链测试证明。
        self.assertIsInstance(status, str)

    def test_internal_unaccounted_or_unknown_is_not_assumed_zero(self):
        for accounted in (False, None):
            with self.subTest(accounted=accounted):
                with self.assertRaises(DomainValidationError):
                    self.classify("INSIDE_ENTERPRISE", accounted)

    def test_unknown_boundaries_do_not_borrow_display_name(self):
        for boundary in ("UNCONFIRMED", "自备", "", None, "INSIDE", " outside_enterprise "):
            with self.subTest(boundary=boundary):
                with self.assertRaises(DomainValidationError):
                    self.classify(boundary, True)

    def test_exported_heat_does_not_require_purchased_qualification(self):
        for boundary in ("INSIDE_ENTERPRISE", "OUTSIDE_ENTERPRISE", "UNCONFIRMED", None):
            for accounted in (True, False, None):
                with self.subTest(boundary=boundary, accounted=accounted):
                    self.assertEqual(self.classify(boundary, accounted, "exported_heat"), "EXPORTED")
        # 原外送公式结果单独0.308；净间接可抵扣，不被015变为豁免或置零。
        with declared_numeric_profile(POLICY):
            exported = purchased_heat_emission("1000", evaluate(known()).value, ".11")
        self.assertEqual(exported, Decimal(".308"))

    def test_unknown_direction_and_nonboolean_accounting_flags_fail(self):
        for direction in ("", "purchased", "PURCHASED_HEAT", None):
            with self.subTest(direction=direction):
                with self.assertRaises(DomainValidationError):
                    self.classify("OUTSIDE_ENTERPRISE", False, direction)
        for accounted in (0, 1, "True", "False", ""):
            with self.subTest(accounted=accounted):
                with self.assertRaises(DomainValidationError):
                    self.classify("INSIDE_ENTERPRISE", accounted)


if __name__ == "__main__":
    unittest.main()
