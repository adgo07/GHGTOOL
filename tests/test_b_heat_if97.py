"""CoolProp8/IF97专属Conformance与产品相态门禁。

官方IAPWS R7-97(2012) Table15/PDF17页给9位有效数字h，绝对容差
5e-6kJ/kg仅核验打印参考末位；正式相态/域/错误断言精确，无业务epsilon。
https://iapws.org/technical-guidance/release/IF97-Rev.download
30MPa/700K只验证底层库，不作为产品超临界流体支持声明。
"""
from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import unittest
import math
from unittest.mock import patch

import CoolProp
import CoolProp.CoolProp as cp
import numpy

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitDefinition, UnitService
from packages.standards.carbon_material import SteamKind
from packages.standards.carbon_material_steam_if97 import (
    evaluate_if97_steam, PROPERTY_PROFILE_ID, METHOD_VERSION, IMPLEMENTATION_REVISION,
)

D = Decimal
PROFILE = "GHGTOOL_CARBON_DECIMAL40_CURRENT"
POLICY = DecimalPolicy()
REFERENCE_TOLERANCE = D("0.000005")


def evaluate(p="0.1", t="226.85", kind=SteamKind.SUPERHEATED, *, policy=POLICY, profile=PROFILE):
    return evaluate_if97_steam(steam_kind=kind, pressure_mpa=D(p),
                               temperature_c=None if t is None else D(t),
                               policy=policy, numeric_profile_id=profile)


class IF97OfficialReferenceTests(unittest.TestCase):
    def test_table15_all_three_official_points_verify_actual_backend(self):
        for pressure_mpa, kelvin, expected in ((".0035", "300", "2549.91145"),
                                               (".0035", "700", "3335.68375"),
                                               ("30", "700", "2631.49474")):
            with self.subTest(p=pressure_mpa, t=kelvin):
                # 直接核验真实底层库，独立官方预期不由provider输出生成。
                state = cp.AbstractState("IF97", "Water")
                state.update(cp.PT_INPUTS, float(D(pressure_mpa)*D("1000000")), float(kelvin))
                actual = D(repr(float(state.hmass()))) / D("1000")
                self.assertLessEqual(abs(actual-D(expected)), REFERENCE_TOLERANCE)
                self.assertEqual(state.backend_name(), "IF97Backend")
        self.assertEqual(CoolProp.__version__, "8.0.0")
        self.assertEqual(numpy.__version__, "2.3.3")
        self.assertEqual(cp.get_global_param_string("gitrevision"), IMPLEMENTATION_REVISION)

    def test_table36_official_saturation_temperature_points(self):
        # 官方Table36/PDF36页；参考末位0.000001K，仅数值验收。
        for p, expected in ((".1", "372.755919"), ("1", "453.035632"), ("10", "584.149488")):
            with self.subTest(p=p):
                state = cp.AbstractState("IF97", "Water")
                state.update(cp.PQ_INPUTS, float(D(p)*D("1000000")), 1.0)
                self.assertLessEqual(abs(D(repr(float(state.T())))-D(expected)), D(".0000005"))

    def test_two_in_product_domain_official_points_use_same_reference(self):
        for temperature_c, expected in (("26.85", "2549.91145"), ("426.85", "3335.68375")):
            with self.subTest(temperature_c=temperature_c):
                result = evaluate(".0035", temperature_c)
                self.assertLessEqual(abs(result.enthalpy_kj_per_kg-D(expected)), REFERENCE_TOLERANCE)
                self.assertNotEqual(result.numeric_profile_id, PROFILE)

    def test_supercritical_reference_point_does_not_extend_product_scope(self):
        with self.assertRaises(DomainValidationError):
            evaluate("30", "426.85")


class IF97AllowedStateTests(unittest.TestCase):
    def test_dry_saturated_is_explicit_quality_one_not_unknown_mixture(self):
        result = evaluate(".1", None, SteamKind.SATURATED)
        state = cp.AbstractState("IF97", "Water")
        state.update(cp.PQ_INPUTS, 100000.0, 1.0)
        self.assertEqual(state.Q(), 1.0)
        self.assertEqual(result.actual_phase, "IF97Backend:"+str(state.phase()))
        self.assertEqual(result.declared_state, "SATURATED")
        self.assertIsNone(result.temperature_c)
        self.assertIsNone(result.input_temperature_lexeme)
        self.assertEqual(result.enthalpy_kj_per_kg, D(repr(float(state.hmass())))/D("1000"))

    def test_real_saturation_boundary_rejects_as_superheated_without_tolerance(self):
        state = cp.AbstractState("IF97", "Water")
        state.update(cp.PQ_INPUTS, 100000.0, 1.0)
        saturation_c = POLICY.subtract(D(repr(float(state.T()))), "273.15")
        for t in (POLICY.subtract(saturation_c, ".01"), saturation_c):
            with self.subTest(t=t):
                with self.assertRaises(DomainValidationError):
                    evaluate(".1", str(t))
        result = evaluate(".1", str(POLICY.add(saturation_c, ".01")))
        self.assertEqual(result.declared_state, "SUPERHEATED")
        self.assertIn("iphase_gas", result.actual_phase)

    def test_below_critical_pressure_high_temperature_vapor_is_superheated(self):
        result = evaluate("1", "540")
        self.assertIn("iphase_supercritical_gas", result.actual_phase)
        self.assertEqual(result.pressure_mpa, D("1"))

    def test_temperature_upper_domain_boundary(self):
        result = evaluate(".1", "2000")  # 2273.15K：IF97高温域上界
        self.assertTrue(result.enthalpy_kj_per_kg.is_finite())
        with self.assertRaises(DomainValidationError):
            evaluate(".1", "2000.0000000000000000000000000000000000000000000000000001")

    def test_working_pressure_cannot_round_to_critical_and_adjacent_value_is_valid(self):
        raw = "22.06399999999999999999999999999999999999"
        self.assertLess(D(raw), D("22.064"))
        self.assertEqual(float(str(POLICY.multiply(D(raw), D("1000000")))), 22064000.0)
        # 真实后端仍会把临界工作点标为Q=1/twophase，不能仅信粗phase标签。
        critical = cp.AbstractState("IF97", "Water")
        critical.update(cp.PQ_INPUTS, 22064000.0, 1.0)
        self.assertEqual(critical.Q(), 1.0)
        for kind in (SteamKind.SATURATED, SteamKind.SUPERHEATED):
            with self.subTest(kind=kind), self.assertRaisesRegex(DomainValidationError, "临界"):
                evaluate(raw, None if kind is SteamKind.SATURATED else "426.85", kind)
        adjacent_pa = math.nextafter(22064000.0, 0.0)
        adjacent_mpa = POLICY.divide(D(repr(adjacent_pa)), D("1000000"))
        result = evaluate(str(adjacent_mpa), None, SteamKind.SATURATED)
        self.assertEqual(result.working_pressure_pa_lexeme, repr(adjacent_pa))
        self.assertEqual(result.quality_lexeme, "1")

    def test_working_temperature_fold_to_saturation_is_rejected_and_adjacent_is_valid(self):
        saturation = cp.AbstractState("IF97", "Water")
        saturation.update(cp.PQ_INPUTS, 100000.0, 1.0)
        tsat = D(repr(float(saturation.T())))
        raw_c = POLICY.add(POLICY.subtract(tsat, D("273.15")), D("1e-30"))
        self.assertGreater(POLICY.add(raw_c, D("273.15")), tsat)
        self.assertEqual(float(str(POLICY.add(raw_c, D("273.15")))), float(tsat))
        with self.assertRaisesRegex(DomainValidationError, "工作温度"):
            evaluate(".1", str(raw_c))
        # Tsat之上的首个ULP在真实库仍被标为非气相，不伪造合法状态。
        first_k = math.nextafter(float(tsat), math.inf)
        first = cp.AbstractState("IF97", "Water")
        first.update(cp.PT_INPUTS, 100000.0, first_k)
        self.assertNotIn(first.phase(), (cp.iphase_gas, cp.iphase_supercritical_gas))
        with self.assertRaises(DomainValidationError):
            evaluate(".1", str(POLICY.subtract(D(repr(first_k)), D("273.15"))))
        # 已核实际气相中的相邻可表示K都允许，且不夹值/抬温。
        legal_k = float(str(POLICY.add(tsat, D(".01"))))
        for adjacent_k in (legal_k, math.nextafter(legal_k, math.inf)):
            adjacent_c = POLICY.subtract(D(repr(adjacent_k)), D("273.15"))
            result = evaluate(".1", str(adjacent_c))
            self.assertEqual(result.working_temperature_k_lexeme, repr(adjacent_k))
            self.assertIn("iphase_gas", result.actual_phase)

    def test_critical_and_supercritical_pressure_rejected_for_both_paths(self):
        for p in ("22.064", "22.06400000000000000000001", "30", "100"):
            for kind in (SteamKind.SATURATED, SteamKind.SUPERHEATED):
                with self.subTest(p=p, kind=kind):
                    with self.assertRaises(DomainValidationError):
                        evaluate(p, None if kind is SteamKind.SATURATED else "426.85", kind)

    def test_liquid_pseudo_superheated_and_below_domain_are_rejected(self):
        for p, t in ((".1", "90"), ("1", "100"), (".1", "-273.15")):
            with self.subTest(p=p, t=t):
                with self.assertRaises(DomainValidationError):
                    evaluate(p, t)
        with self.assertRaises(DomainValidationError):
            evaluate(".000001", None, SteamKind.SATURATED)
        # 一般Region2公式域不代替具体IF97后端API域：真实后端对此低压拒绝。
        with self.assertRaises(DomainValidationError):
            evaluate(".0001", "26.85")

    def test_saturated_extra_temperature_and_missing_superheated_temperature_fail(self):
        with self.assertRaises(DomainValidationError):
            evaluate(".1", "99.6", SteamKind.SATURATED)
        with self.assertRaises(DomainValidationError):
            evaluate(".1", None)

    def test_unsupported_declared_states_and_invalid_input_numbers_fail(self):
        for kind in ("SATURATED", "WET", "LIQUID", None):
            with self.subTest(kind=kind):
                with self.assertRaises(DomainValidationError):
                    evaluate(".1", "226.85", kind)
        for p in ("0", "-1", "NaN", "Infinity"):
            with self.subTest(p=p):
                with self.assertRaises(DomainValidationError):
                    evaluate(p)
        for t in ("NaN", "Infinity"):
            with self.subTest(t=t):
                with self.assertRaises(DomainValidationError):
                    evaluate(".1", t)
        with self.assertRaises(DomainValidationError):
            evaluate_if97_steam(steam_kind=SteamKind.SUPERHEATED, pressure_mpa=.1,
                               temperature_c=D("226.85"), policy=POLICY, numeric_profile_id=PROFILE)


class IF97NumericAndFailureTests(unittest.TestCase):
    def test_mpa_pa_and_c_kelvin_bridge_equivalence_is_explicit(self):
        units = UnitService(POLICY, (
            UnitDefinition("pressure_pa", "Pa", "pressure", D("1")),
            UnitDefinition("pressure_mpa", "MPa", "pressure", D("1000000")),
        ))
        pressure = units.convert("100000", "Pa", "MPa")
        temperature = POLICY.subtract("500", "273.15")
        expected = evaluate(".1", "226.85")
        result = evaluate(str(pressure), str(temperature))
        self.assertEqual(result.enthalpy_kj_per_kg, expected.enthalpy_kj_per_kg)
        self.assertEqual(result.pressure_mpa, expected.pressure_mpa)
        self.assertEqual(result.temperature_c, expected.temperature_c)
        # pressure_mpa为已归一绝压，不存在猜大气压/表压输入的第二接口。

    def test_independent_property_profile_and_full_runtime_identity_are_frozen(self):
        result = evaluate()
        self.assertEqual(result.numeric_profile_id, PROPERTY_PROFILE_ID)
        self.assertEqual(result.implementation, "Python CoolProp IF97 backend")
        self.assertEqual(result.implementation_version, "8.0.0")
        self.assertEqual(result.implementation_revision, IMPLEMENTATION_REVISION)
        self.assertEqual(result.dependency_versions, (("CoolProp", "8.0.0"), ("numpy", "2.3.3")))
        self.assertEqual(result.method_version, METHOD_VERSION)
        self.assertEqual(D(result.output_enthalpy_lexeme), result.enthalpy_kj_per_kg)
        self.assertEqual(result.input_pressure_lexeme, "0.1")
        self.assertEqual(result.input_temperature_lexeme, "226.85")
        with self.assertRaises(FrozenInstanceError):
            result.enthalpy_kj_per_kg = D(0)

    def test_normalized_input_library_working_lexemes_and_adoption_are_distinct(self):
        result = evaluate(".1", "226.85")
        state = cp.AbstractState("IF97", "Water")
        state.update(cp.PT_INPUTS, 100000.0, 500.0)
        self.assertEqual(result.input_pressure_lexeme, "0.1")
        self.assertEqual(result.input_temperature_lexeme, "226.85")
        self.assertEqual(result.working_pressure_pa_lexeme, "100000.0")
        self.assertEqual(result.working_temperature_k_lexeme, "500.0")
        self.assertEqual(result.library_output_j_per_kg_lexeme, repr(float(state.hmass())))
        self.assertEqual(D(result.output_enthalpy_lexeme), POLICY.divide(
            D(result.library_output_j_per_kg_lexeme), "1000"))
        self.assertIsNone(result.quality_lexeme)
        saturated = evaluate(".1", None, SteamKind.SATURATED)
        self.assertEqual(saturated.quality_lexeme, "1")
        self.assertIsNone(saturated.working_temperature_k_lexeme)

    def test_binary64_output_uses_decimal_lexeme_not_decimal_float(self):
        state = cp.AbstractState("IF97", "Water")
        state.update(cp.PT_INPUTS, 100000.0, 500.0)
        expected = POLICY.divide(D(repr(float(state.hmass()))), "1000")
        self.assertEqual(evaluate().enthalpy_kj_per_kg, expected)
        # expected保留17位左右binary64词法精度，不冒称40位物性有效精度。

    def test_declared_profiles_and_ambient_contexts_do_not_change_physical_adoption(self):
        baseline = evaluate()
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_DOWN)):
            policy = DecimalPolicy(precision=precision, rounding=rounding)
            for ambient in (6, 17, 60):
                with self.subTest(precision=precision, ambient=ambient):
                    with localcontext() as context:
                        context.prec, context.rounding = ambient, ROUND_DOWN
                        result = evaluate(policy=policy, profile=f"TEST_P{precision}_{rounding}")
                        self.assertEqual(result.enthalpy_kj_per_kg, baseline.enthalpy_kj_per_kg)
                        self.assertEqual(result.actual_phase, baseline.actual_phase)
                        self.assertEqual(result.working_pressure_pa_lexeme, baseline.working_pressure_pa_lexeme)
                        self.assertEqual(result.working_temperature_k_lexeme, baseline.working_temperature_k_lexeme)
                        self.assertEqual(result.library_output_j_per_kg_lexeme, baseline.library_output_j_per_kg_lexeme)
                        self.assertEqual(context.prec, ambient)

    def test_mismatched_or_missing_calling_profile_is_rejected(self):
        for policy, profile in ((None, PROFILE), (DecimalPolicy(precision=28), PROFILE),
                                (POLICY, PROPERTY_PROFILE_ID), (POLICY, ""), (POLICY, None)):
            with self.subTest(profile=profile, policy=policy):
                with self.assertRaises(DomainValidationError):
                    evaluate(policy=policy, profile=profile)

    def test_missing_or_wrong_runtime_never_falls_back_to_old_table(self):
        with patch("packages.standards.carbon_material_steam_if97.import_module", side_effect=ImportError("missing")), \
                patch("packages.standards.carbon_material.saturated_steam_enthalpy", side_effect=AssertionError("旧表禁止")), \
                patch("packages.standards.carbon_material.superheated_steam_enthalpy", side_effect=AssertionError("旧表禁止")):
            with self.assertRaisesRegex(DomainValidationError, "无旧表"):
                evaluate()
        with patch.object(CoolProp, "__version__", "7.0.0"):
            with self.assertRaisesRegex(DomainValidationError, "版本"):
                evaluate()
        with patch.object(numpy, "__version__", "0.0.0"):
            with self.assertRaisesRegex(DomainValidationError, "版本"):
                evaluate()

    def test_backend_failure_does_not_return_a_partial_or_fabricated_result(self):
        with patch.object(cp, "AbstractState", side_effect=ValueError("backend failed")):
            with self.assertRaises(DomainValidationError):
                evaluate()


if __name__ == "__main__":
    unittest.main()
