from __future__ import annotations

from contextlib import ExitStack
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext, localcontext
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from packages.core import AccountingPeriod, PeriodType
from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitService
import packages.standards.carbon_material as carbon_material
from packages.standards._numeric_authority import (
    ORIGINAL_CALCULATE,
    current_declared_numeric_profile,
    declared_numeric_profile,
)
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    BakingInput,
    CalcinationInput,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    FuelInput,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatInput,
    ParameterValue,
    SteamKind,
    baking_emission,
    calcination_emission,
    fume_incineration_emission,
    graphitization_emission,
    superheated_steam_enthalpy,
    total_emission,
)

ROOT = Path(__file__).resolve().parents[1]
VECTOR_PATH = ROOT / "conformance" / "numeric" / "qz.carbon_accounting" / "gbt32151_34_n01c.json"
SNAPSHOT_AT = datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc)
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def _fuel_only_input(activity: str = "1") -> CarbonMaterialInput:
    return CarbonMaterialInput(
        input_id="n01c.context",
        enterprise_id="enterprise.n01c",
        enterprise_name="N01-C",
        period=PERIOD,
        boundary_confirmed=True,
        fuel_inputs=(FuelInput.mass("fuel.context", activity, "1", "1"),),
    )


def _full_profile_input() -> CarbonMaterialInput:
    """Exercise all R1 representative authoritative formula families."""

    return CarbonMaterialInput(
        input_id="n01c.r1.full-profile",
        enterprise_id="enterprise.n01c.r1",
        enterprise_name="N01-C-R1",
        period=PERIOD,
        boundary_confirmed=True,
        fuel_inputs=(FuelInput.mass("fuel.profile", "1", "1", "1"),),
        calcination=CalcinationInput(
            gc="100",
            wfc="0.008",
            cc="70",
            ucc="5",
            du="1",
            wfc_c="0.002",
            wvar="0.10",
            wvar_c="0.02",
            k1="0.35",
        ),
        baking=BakingInput(
            bpm="10",
            bpmfc="0.005",
            bg="100",
            bgfc="0.007",
            bwt="0.05",
            bp="95",
            bpfc="0.006",
            bpmvar="0.10",
            bgvar="0.02",
            k2="0.35",
        ),
        graphitization=GraphitizationInput(
            gpm="10",
            gpmfc="0.005",
            gta="100",
            gtafc="0.007",
            gwt="0.05",
            gp="95",
            gpfc="0.006",
            gpmvar="0.10",
            k3="0.35",
        ),
        fume_incineration=FumeIncinerationInput(
            q="1000",
            qvar="10",
            hm="30",
            fch="0.02",
            fox="0.98",
            duration="1",
        ),
        purchased_heat=(
            HeatInput(
                line_id="heat.profile",
                amount="1000",
                factor=ParameterValue(
                    "heat.profile.factor",
                    "0.11",
                    "tCO2/GJ",
                    source_location="N01-C-R1 profile fixture",
                ),
                steam_kind=SteamKind.SUPERHEATED,
                pressure_mpa="1.5",
                temperature_c="325",
            ),
        ),
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


def _explicit_context_value(precision: int, fn, rounding: str = ROUND_HALF_UP):
    with localcontext() as context:
        context.prec = precision
        context.rounding = rounding
        return fn()


def _declared_profile_value(precision: int, fn, rounding: str = ROUND_HALF_UP):
    policy = DecimalPolicy(precision=precision, rounding=rounding)
    with declared_numeric_profile(policy):
        return fn()


def _representative_formulae():
    return {
        "44/12": lambda: Decimal(44) / Decimal(12),
        "fuel": lambda: carbon_material.fuel_volume_emission("2", "0.015", "0.98"),
        "calcination": lambda: calcination_emission(
            gc="100", wfc="0.008", cc="70", ucc="5", du="1", wfc_c="0.002",
            wvar="0.10", wvar_c="0.02", k1="0.35",
        ),
        "baking": lambda: baking_emission(
            bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
            bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
        ),
        "graphitization": lambda: graphitization_emission(
            gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
            gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
        ),
        "fume": lambda: fume_incineration_emission("1000", "10", "30", "0.02", "0.98", "1"),
        "steam": lambda: superheated_steam_enthalpy("1.5", "325")[0],
        "total": lambda: total_emission(
            baking_emission(
                bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
                bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
            ),
            graphitization_emission(
                gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
                gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
            ),
        ),
    }


def _full_calculator_values(precision: int, rounding: str = ROUND_HALF_UP) -> dict[str, Decimal]:
    policy = DecimalPolicy(precision=precision, rounding=rounding)
    outcome = CarbonMaterialCalculator(policy=policy).calculate(_full_profile_input(), calculated_at=SNAPSHOT_AT)
    if not outcome.successful or outcome.result is None:
        raise AssertionError(f"R1 full profile calculation failed: {outcome.problems!r}")
    line_map = {line.line_id: line.amount for line in outcome.result.lines}
    with declared_numeric_profile(policy):
        steam = superheated_steam_enthalpy("1.5", "325")[0]
    return {
        "44/12": policy.divide("44", "12"),
        "fuel": line_map["CAR-SRC-FUEL-001.fuel.profile"],
        "calcination": line_map["CAR-FLD-P01-RESULT"],
        "baking": line_map["CAR-FLD-P02-RESULT"],
        "graphitization": line_map["CAR-FLD-P03-RESULT"],
        "fume": line_map["CAR-FLD-P04A-RESULT"],
        "steam": steam,
        "total": outcome.result.total_amount,
    }


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

    def test_before_fix_original_calculator_depends_on_ambient_context(self) -> None:
        results = []
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_HALF_EVEN)):
            with localcontext() as context:
                context.prec = precision
                context.rounding = rounding
                calculator = CarbonMaterialCalculator()
                outcome = ORIGINAL_CALCULATE(calculator, _fuel_only_input(), calculated_at=SNAPSHOT_AT)
                self.assertTrue(outcome.successful)
                results.append(outcome.result.total_amount)
        self.assertNotEqual(results[0], results[1])
        self.assertNotEqual(results[0], results[2])
        print("N01C_BEFORE_FIX_AMBIENT", [str(value) for value in results])

    def test_ambient_context_independence_is_separate_from_declared_profile(self) -> None:
        vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))["vectors"]
        expected_by_precision = {
            int(v["requested_numeric_profile"]["precision"]): Decimal(v["expected_total"])
            for v in vectors
            if v["kind"] == "profile_propagation"
        }
        observations: dict[int, list[str]] = {}
        ambient_profiles = (
            (28, ROUND_HALF_EVEN),
            (34, ROUND_HALF_EVEN),
            (40, ROUND_HALF_UP),
            (50, ROUND_HALF_EVEN),
        )
        for declared_precision in (28, 34, 40, 50):
            values = []
            for ambient_precision, ambient_rounding in ambient_profiles:
                with localcontext() as context:
                    context.prec = ambient_precision
                    context.rounding = ambient_rounding
                    outcome = CarbonMaterialCalculator(
                        policy=DecimalPolicy(precision=declared_precision, rounding=ROUND_HALF_UP)
                    ).calculate(_fuel_only_input(), calculated_at=SNAPSHOT_AT)
                    self.assertTrue(outcome.successful)
                    values.append(outcome.result.total_amount)
            self.assertTrue(all(value == values[0] for value in values[1:]))
            self.assertEqual(values[0], expected_by_precision[declared_precision])
            observations[declared_precision] = [str(value) for value in values]
        print("N01C_R1_AMBIENT_INDEPENDENCE", json.dumps(observations, ensure_ascii=False, sort_keys=True))

    def test_declared_profile_propagates_across_authoritative_helpers(self) -> None:
        target_names = (
            "_mul",
            "fuel_mass_emission",
            "calcination_emission",
            "baking_emission",
            "graphitization_emission",
            "fume_incineration_emission",
            "superheated_steam_enthalpy",
            "purchased_heat_emission",
            "direct_emission",
            "indirect_emission",
            "total_emission",
        )
        audit: dict[int, list[tuple[str, int | None, str | None, int, str]]] = {}
        for precision in (28, 34, 40, 50):
            seen: list[tuple[str, int | None, str | None, int, str]] = []
            originals = {name: getattr(carbon_material, name) for name in target_names}

            def make_probe(name: str):
                original = originals[name]

                def probe(*args, **kwargs):
                    active = current_declared_numeric_profile()
                    seen.append(
                        (
                            name,
                            None if active is None else active.precision,
                            None if active is None else active.rounding,
                            getcontext().prec,
                            getcontext().rounding,
                        )
                    )
                    return original(*args, **kwargs)

                return probe

            with ExitStack() as stack:
                for name in target_names:
                    stack.enter_context(patch.object(carbon_material, name, side_effect=make_probe(name)))
                outcome = CarbonMaterialCalculator(
                    policy=DecimalPolicy(precision=precision, rounding=ROUND_HALF_UP)
                ).calculate(_full_profile_input(), calculated_at=SNAPSHOT_AT)
            self.assertTrue(outcome.successful)
            self.assertTrue(set(target_names).issubset({entry[0] for entry in seen}))
            for name, active_precision, active_rounding, context_precision, context_rounding in seen:
                self.assertEqual(active_precision, precision, name)
                self.assertEqual(active_rounding, ROUND_HALF_UP, name)
                self.assertEqual(context_precision, precision, name)
                self.assertEqual(context_rounding, ROUND_HALF_UP, name)
            audit[precision] = seen
        printable = {
            precision: [
                {
                    "helper": name,
                    "active_precision": active_precision,
                    "active_rounding": active_rounding,
                    "context_precision": context_precision,
                    "context_rounding": context_rounding,
                }
                for name, active_precision, active_rounding, context_precision, context_rounding in entries
            ]
            for precision, entries in audit.items()
        }
        print("N01C_R1_PROFILE_PROPAGATION_AUDIT", json.dumps(printable, ensure_ascii=False, sort_keys=True))

    def test_profile_mismatch_between_calculator_and_unit_service_fails(self) -> None:
        calculator = CarbonMaterialCalculator(
            policy=DecimalPolicy(precision=50, rounding=ROUND_HALF_UP),
            unit_service=UnitService(DecimalPolicy(precision=40, rounding=ROUND_HALF_UP)),
        )
        with self.assertRaisesRegex(DomainValidationError, "numeric profile mismatch"):
            calculator.calculate(_fuel_only_input(), calculated_at=SNAPSHOT_AT)

    def test_profile_propagation_conformance_vectors_execute(self) -> None:
        vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))["vectors"]
        propagation = [v for v in vectors if v["kind"] == "profile_propagation"]
        self.assertEqual({v["case_id"] for v in propagation}, {"N01C-P28", "N01C-P34", "N01C-P40", "N01C-P50", "N01C-P60"})
        for vector in propagation:
            requested = vector["requested_numeric_profile"]
            effective = vector["effective_numeric_profile"]
            self.assertEqual(requested, effective)
            policy = DecimalPolicy(
                precision=int(requested["precision"]),
                rounding=requested["rounding_mode"],
            )
            outcome = CarbonMaterialCalculator(policy=policy).calculate(_fuel_only_input(), calculated_at=SNAPSHOT_AT)
            self.assertTrue(outcome.successful)
            self.assertEqual(outcome.result.total_amount, Decimal(vector["expected_total"]))

    def test_true_full_calculator_precision_sensitivity_28_34_40_50_60(self) -> None:
        observations = {
            precision: _full_calculator_values(precision)
            for precision in (28, 34, 40, 50, 60)
        }
        for name in observations[40]:
            self.assertLessEqual(abs(observations[40][name] - observations[50][name]), Decimal("1E-38"), name)
            self.assertLessEqual(abs(observations[50][name] - observations[60][name]), Decimal("1E-48"), name)
        self.assertNotEqual(observations[28]["44/12"], observations[40]["44/12"])
        self.assertNotEqual(observations[34]["fuel"], observations[40]["fuel"])
        self.assertNotEqual(observations[28]["total"], observations[40]["total"])
        printable = {
            precision: {name: str(value) for name, value in values.items()}
            for precision, values in observations.items()
        }
        print("N01C_R1_TRUE_PRECISION_SENSITIVITY", json.dumps(printable, ensure_ascii=False, sort_keys=True))

    def test_formula_helpers_use_declared_profile_for_precision_sensitivity(self) -> None:
        sensitivity: dict[str, dict[int, str]] = {}
        for name, fn in _representative_formulae().items():
            values: dict[int, Decimal] = {}
            for precision in (28, 34, 40, 50, 60):
                values[precision] = _declared_profile_value(precision, fn)
            sensitivity[name] = {precision: str(value) for precision, value in values.items()}
            self.assertLessEqual(abs(values[40] - values[50]), Decimal("1E-38"), name)
            self.assertLessEqual(abs(values[50] - values[60]), Decimal("1E-48"), name)
        print("N01C_R1_FORMULA_PRECISION_SENSITIVITY", json.dumps(sensitivity, ensure_ascii=False, sort_keys=True))

    def test_rounding_mode_sensitivity_at_precision_40_is_measured(self) -> None:
        sensitivity: dict[str, dict[str, str]] = {}
        for name, fn in _representative_formulae().items():
            half_up = _declared_profile_value(40, fn, ROUND_HALF_UP)
            half_even = _declared_profile_value(40, fn, ROUND_HALF_EVEN)
            sensitivity[name] = {"ROUND_HALF_UP": str(half_up), "ROUND_HALF_EVEN": str(half_even)}
            self.assertEqual(half_up, half_even, name)
        print("N01C_R1_ROUNDING_MODE_REPRESENTATIVE", json.dumps(sensitivity, ensure_ascii=False, sort_keys=True))

    def test_rounding_mode_reaches_authoritative_mul_when_halfway_is_hit(self) -> None:
        activity = "1.0000000000000000000000000005"
        half_up = CarbonMaterialCalculator(
            policy=DecimalPolicy(precision=28, rounding=ROUND_HALF_UP)
        ).calculate(_fuel_only_input(activity), calculated_at=SNAPSHOT_AT)
        half_even = CarbonMaterialCalculator(
            policy=DecimalPolicy(precision=28, rounding=ROUND_HALF_EVEN)
        ).calculate(_fuel_only_input(activity), calculated_at=SNAPSHOT_AT)
        self.assertTrue(half_up.successful)
        self.assertTrue(half_even.successful)
        self.assertEqual(half_up.result.total_amount, Decimal("3.666666666666666666666666671"))
        self.assertEqual(half_even.result.total_amount, Decimal("3.666666666666666666666666667"))
        self.assertNotEqual(half_up.result.total_amount, half_even.result.total_amount)
        print(
            "N01C_R1_AUTHORITATIVE_ROUNDING_EVIDENCE",
            {
                "ROUND_HALF_UP": str(half_up.result.total_amount),
                "ROUND_HALF_EVEN": str(half_even.result.total_amount),
            },
        )


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
            if coefficient["rational_expression"] == "44/12":
                self.assertEqual(evaluated, Decimal("3.666666666666666666666666666666666666667"))
            else:
                self.assertEqual(evaluated, Decimal("2.75"))
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
        source = (ROOT / "packages" / "standards" / "carbon_material.py").read_text(encoding="utf-8")
        self.assertNotIn("is_close(", source)
        self.assertIn('if amount < 0:', source)
        self.assertIn('if fractions > Decimal("1"):', source)
        self.assertIn('if value == key:', source)

    def test_tolerance_taxonomy_is_test_only_for_confirmed_is_close_call(self) -> None:
        production_hits = []
        test_hits = []
        audit = {key: set() for key in ("is_close", "tolerance", "abs", "approximate", "interpol")}
        for path in ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT).as_posix()
            lowered = text.lower()
            for key, needle in (
                ("is_close", "is_close("),
                ("tolerance", "tolerance"),
                ("abs", "abs("),
                ("approximate", "approx"),
                ("interpol", "interpol"),
            ):
                if needle in lowered:
                    audit[key].add(rel)
            if "is_close(" not in text:
                continue
            if rel.startswith("tests/"):
                test_hits.append(rel)
            elif rel != "packages/core/decimal_policy.py":
                production_hits.append(rel)
        self.assertEqual(production_hits, [])
        self.assertIn("tests/test_g01_decimal_units.py", test_hits)
        self.assertIn("packages/standards/carbon_material.py", audit["interpol"])
        printable = {key: sorted(value) for key, value in audit.items()}
        print("N01C_TOLERANCE_SCAN", json.dumps(printable, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
