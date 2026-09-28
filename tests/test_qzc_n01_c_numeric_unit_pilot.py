from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import unittest

from packages.core import AccountingPeriod, PeriodType
from packages.core.decimal_policy import DecimalPolicy
from packages.core.units import UnitService
from packages.standards import _carbon_material_impl as legacy_impl
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    BakingInput,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    FuelInput,
    GraphitizationInput,
    InputValue,
    calcination_emission,
    fume_incineration_emission,
    graphitization_emission,
    superheated_steam_enthalpy,
)

ROOT = Path(__file__).resolve().parents[1]
VECTOR_PATH = ROOT / "conformance" / "numeric" / "qz.carbon_accounting" / "gbt32151_34_n01c.json"
SNAPSHOT_AT = datetime(2026, 9, 29, 0, 0, tzinfo=timezone.utc)
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def _fuel_only_input() -> CarbonMaterialInput:
    return CarbonMaterialInput(
        input_id="n01c.context",
        enterprise_id="enterprise.n01c",
        enterprise_name="N01-C",
        period=PERIOD,
        boundary_confirmed=True,
        fuel_inputs=(FuelInput.mass("fuel.context", "1", "1", "1"),),
    )


def _candidate_validate(quantity: dict[str, object]) -> None:
    unit_id = quantity.get("unit_id")
    quantity_type = quantity.get("quantity_type")
    if quantity_type in {"substance_mass", "co2e_mass"} and unit_id not in {"kg", "t"}:
        raise ValueError("mass quantity requires mass unit")
    if quantity_type == "substance_mass" and not quantity.get("substance_id"):
        raise ValueError("substance_mass requires substance_id")
    if quantity_type == "co2e_mass" and not quantity.get("equivalence_basis"):
        raise ValueError("co2e_mass requires equivalence_basis")
    Decimal(str(quantity["value"]))


def _explicit_context_value(precision: int, fn, *args):
    with localcontext() as context:
        context.prec = precision
        context.rounding = ROUND_HALF_UP
        return fn(*args)


class N01CNumericPolicyCoverageTests(unittest.TestCase):
    def test_decimal_policy_is_declared(self) -> None:
        policy = DecimalPolicy()
        self.assertEqual(policy.precision, 40)
        self.assertEqual(policy.rounding, ROUND_HALF_UP)
        self.assertEqual(policy.display_places, 2)
        self.assertEqual(policy.format_for_display("1.235"), "1.24")

    def test_half_up_has_real_working_precision_effect_on_halfway_case(self) -> None:
        half_up = DecimalPolicy(precision=28, rounding=ROUND_HALF_UP)
        half_even = DecimalPolicy(precision=28, rounding=ROUND_HALF_EVEN)
        left = "1.000000000000000000000000000"
        right = "0.0000000000000000000000000005"
        self.assertEqual(half_up.add(left, right), Decimal("1.000000000000000000000000001"))
        self.assertEqual(half_even.add(left, right), Decimal("1.000000000000000000000000000"))

    def test_before_fix_legacy_calculator_depends_on_ambient_context(self) -> None:
        results = []
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_HALF_EVEN)):
            with localcontext() as context:
                context.prec = precision
                context.rounding = rounding
                outcome = legacy_impl.CarbonMaterialCalculator().calculate(
                    _fuel_only_input(), calculated_at=SNAPSHOT_AT
                )
                self.assertTrue(outcome.successful)
                results.append(outcome.result.total_amount)
        self.assertNotEqual(results[0], results[1])
        self.assertNotEqual(results[0], results[2])
        print("N01C_BEFORE_FIX_AMBIENT", [str(value) for value in results])

    def test_after_fix_authoritative_calculator_ignores_ambient_context(self) -> None:
        results = []
        for precision, rounding in ((28, ROUND_HALF_EVEN), (34, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_HALF_EVEN)):
            with localcontext() as context:
                context.prec = precision
                context.rounding = rounding
                outcome = CarbonMaterialCalculator().calculate(
                    _fuel_only_input(), calculated_at=SNAPSHOT_AT
                )
                self.assertTrue(outcome.successful)
                self.assertEqual(outcome.algorithm_version, ALGORITHM_VERSION)
                results.append(outcome.result.total_amount)
        self.assertTrue(all(value == results[0] for value in results[1:]))
        self.assertEqual(
            results[0],
            Decimal("3.666666666666666666666666666666666666667"),
        )
        print("N01C_AFTER_FIX_AMBIENT", [str(value) for value in results])

    def test_precision_28_34_40_50_sensitivity_on_representative_formulas(self) -> None:
        formulae = {
            "fuel": lambda: legacy_impl.fuel_volume_emission("2", "0.015", "0.98"),
            "baking": lambda: legacy_impl.baking_emission(
                bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
                bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
            ),
            "graphitization": lambda: graphitization_emission(
                gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
                gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
            ),
            "fume": lambda: fume_incineration_emission("1000", "10", "30", "0.02", "0.98", "1"),
            "steam": lambda: superheated_steam_enthalpy("1.5", "325")[0],
            "total": lambda: legacy_impl.total_emission(
                legacy_impl.baking_emission(
                    bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
                    bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
                ),
                legacy_impl.graphitization_emission(
                    gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
                    gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
                ),
            ),
        }
        sensitivity: dict[str, dict[int, str]] = {}
        for name, fn in formulae.items():
            values: dict[int, Decimal] = {}
            for precision in (28, 34, 40, 50):
                values[precision] = _explicit_context_value(precision, fn)
            sensitivity[name] = {precision: str(value) for precision, value in values.items()}
            self.assertLessEqual(abs(values[40] - values[50]), Decimal("1E-38"), name)
        print("N01C_PRECISION_SENSITIVITY", json.dumps(sensitivity, ensure_ascii=False, sort_keys=True))

    def test_calculator_supports_explicit_28_34_40_50_profiles(self) -> None:
        values: dict[int, Decimal] = {}
        for precision in (28, 34, 40, 50):
            calculator = CarbonMaterialCalculator(policy=DecimalPolicy(precision=precision))
            values[precision] = calculator.calculate(
                _fuel_only_input(), calculated_at=SNAPSHOT_AT
            ).result.total_amount
        self.assertNotEqual(values[28], values[40])
        self.assertNotEqual(values[34], values[40])
        self.assertLessEqual(abs(values[40] - values[50]), Decimal("1E-39"))


class N01CUnitQuantitySemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.units = UnitService()
        self.vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))["vectors"]

    def test_pure_unit_conversion_vectors_execute(self) -> None:
        for vector in self.vectors:
            if vector["kind"] != "unit_conversion":
                continue
            with self.subTest(case_id=vector["case_id"]):
                actual = self.units.convert(vector["value"], vector["from_unit"], vector["to_unit"])
                self.assertEqual(actual, Decimal(vector["expected"]))

    def test_legacy_tc_to_tco2_bridge_is_characterized_not_reclassified(self) -> None:
        actual = self.units.convert("1", "tC", "tCO2")
        expected = self.units.policy.divide("44", "12")
        self.assertEqual(actual, expected)
        self.assertEqual(self.units.definition("tC").dimension, "mass_carbon")
        self.assertEqual(self.units.definition("tCO2").dimension, "mass_co2")
        self.assertNotEqual(self.units.definition("tC").dimension, self.units.definition("tCO2").dimension)

    def test_quantity_candidate_c_co2_ch4_and_co2e_round_trip(self) -> None:
        quantities = [v["quantity"] for v in self.vectors if v["kind"] == "quantity_candidate"]
        self.assertEqual({q.get("substance_id") for q in quantities if q["quantity_type"] == "substance_mass"}, {"C", "CO2", "CH4"})
        for quantity in quantities:
            _candidate_validate(quantity)
            encoded = json.dumps(quantity, ensure_ascii=False, sort_keys=True)
            decoded = json.loads(encoded)
            self.assertEqual(decoded, quantity)

    def test_invalid_semantic_combination_is_rejected(self) -> None:
        invalid = next(v for v in self.vectors if v["kind"] == "invalid_quantity_candidate")
        with self.assertRaisesRegex(ValueError, invalid["expected_error"]):
            _candidate_validate(invalid["quantity"])

    def test_stoichiometric_coefficients_are_structured_rationals(self) -> None:
        coefficients = [v for v in self.vectors if v["kind"] == "quantity_transformation"]
        self.assertEqual({v["coefficient"]["rational_expression"] for v in coefficients}, {"44/12", "44/16"})
        for vector in coefficients:
            coefficient = vector["coefficient"]
            self.assertEqual(coefficient["coefficient_type"], "STOICHIOMETRIC")
            evaluated = DecimalPolicy().divide(coefficient["numerator"], coefficient["denominator"])
            self.assertGreater(evaluated, 0)
            self.assertNotEqual(vector["input_quantity"]["substance_id"], vector["output_quantity"]["substance_id"])

    def test_gwp_vector_is_candidate_only_and_has_provenance(self) -> None:
        vector = next(v for v in self.vectors if v["kind"] == "gwp_candidate")
        self.assertTrue(vector["candidate_only"])
        self.assertEqual(vector["gwp"]["value"], "1")
        self.assertEqual(vector["gwp"]["time_horizon_years"], 100)
        self.assertEqual(vector["gwp"]["assessment"], "IPCC_AR6")
        self.assertEqual(vector["gwp"]["source_id"], "SRC-IPCC-AR6-WGI")
        self.assertEqual(vector["result"]["quantity_type"], "co2e_mass")

    def test_display_value_never_changes_exact_business_comparison(self) -> None:
        vector = next(v for v in self.vectors if v["kind"] == "display_separation")
        value = Decimal(vector["calculation_value"])
        limit = Decimal(vector["comparison_limit"])
        display = DecimalPolicy().format_for_display(value, vector["display_places"])
        self.assertEqual(display, vector["display_value"])
        self.assertEqual(value <= limit, vector["expected_lte"])

    def test_business_boundaries_are_exact_and_is_close_is_not_called_by_calculator(self) -> None:
        source = (ROOT / "packages" / "standards" / "_carbon_material_impl.py").read_text(encoding="utf-8")
        self.assertNotIn("is_close(", source)
        self.assertIn('if amount < 0:', source)
        self.assertIn('if fractions > Decimal("1"):', source)
        self.assertIn('if value == key:', source)

    def test_tolerance_taxonomy_is_test_only_for_confirmed_is_close_call(self) -> None:
        production_hits = []
        test_hits = []
        for path in ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "is_close(" not in text:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("tests/"):
                test_hits.append(rel)
            elif rel != "packages/core/decimal_policy.py":
                production_hits.append(rel)
        self.assertEqual(production_hits, [])
        self.assertIn("tests/test_g01_decimal_units.py", test_hits)


if __name__ == "__main__":
    unittest.main()
