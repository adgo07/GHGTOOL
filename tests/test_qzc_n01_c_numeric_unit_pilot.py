from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import unittest

from packages.core import DecimalPolicy
from packages.core.units import UnitService
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    BakingInput,
    CarbonMaterialCalculator,
    InputValue,
    baking_emission,
    calcination_emission,
    direct_emission,
    fuel_volume_emission,
    fume_incineration_emission,
    graphitization_emission,
    saturated_steam_enthalpy,
    superheated_steam_enthalpy,
)
from packages.standards.carbon_numeric_authority import NUMERIC_AUTHORITY_VERSION
from tests.pilot_support.n01_c_quantity import (
    EquivalenceBasisCandidate,
    ExtendedQuantityCandidate,
    MinimalQuantityCandidate,
    RationalCoefficientCandidate,
    apply_gwp_candidate,
    apply_rational_transformation,
)


VECTOR_PATH = Path("conformance/numeric/qz.carbon_accounting/gbt32151_34_n01c.json")


def _graph_kwargs() -> dict[str, str]:
    return {
        "gpm": "10", "gpmfc": "0.005", "gta": "100", "gtafc": "0.007",
        "gwt": "0.05", "gp": "95", "gpfc": "0.006", "gpmvar": "0.10", "k3": "0.35",
    }


def _bake_kwargs() -> dict[str, str]:
    return {
        "bpm": "10", "bpmfc": "0.005", "bg": "100", "bgfc": "0.007",
        "bwt": "0.05", "bp": "95", "bpfc": "0.006", "bpmvar": "0.10",
        "bgvar": "0.02", "k2": "0.35",
    }


def _calc_kwargs() -> dict[str, str]:
    return {
        "gc": "100", "wfc": "0.008", "cc": "70", "ucc": "5", "du": "1",
        "wfc_c": "0.002", "wvar": "0.10", "wvar_c": "0.02", "k1": "0.35",
    }


def _formula_snapshot(policy: DecimalPolicy | None = None) -> dict[str, Decimal]:
    kwargs = {"policy": policy} if policy is not None else {}
    fuel = fuel_volume_emission("2", "0.015", "0.98", **kwargs)
    calcination = calcination_emission(**_calc_kwargs(), **kwargs)
    baking = baking_emission(**_bake_kwargs(), **kwargs)
    graphitization = graphitization_emission(**_graph_kwargs(), **kwargs)
    fume = fume_incineration_emission("1000", "10", "30", "0.02", "0.98", "1", **kwargs)
    saturated = saturated_steam_enthalpy("1.75", **kwargs)[0]
    superheated = superheated_steam_enthalpy("1.23456789", "333.333333", **kwargs)[0]
    representative_total = direct_emission(
        fuel, calcination, baking, graphitization, fume, **kwargs
    )
    return {
        "fuel": fuel,
        "calcination": calcination,
        "baking": baking,
        "graphitization": graphitization,
        "fume": fume,
        "saturated_steam": saturated,
        "superheated_steam": superheated,
        "representative_total": representative_total,
    }


class N01CNumericAuthorityTests(unittest.TestCase):
    def test_declared_policy_and_algorithm_version_are_explicit(self) -> None:
        policy = DecimalPolicy()
        self.assertEqual(policy.precision, 40)
        self.assertEqual(policy.rounding, ROUND_HALF_UP)
        self.assertEqual(policy.display_places, 2)
        self.assertEqual(policy.round_for_display("1.235"), Decimal("1.24"))
        self.assertEqual(ALGORITHM_VERSION, NUMERIC_AUTHORITY_VERSION)

    def test_half_up_is_real_but_representative_formulas_are_not_tie_sensitive(self) -> None:
        half_up = DecimalPolicy(precision=28, rounding=ROUND_HALF_UP)
        half_even = DecimalPolicy(precision=28, rounding=ROUND_HALF_EVEN)
        tie = "1.0000000000000000000000000005"
        self.assertEqual(
            half_up.multiply(tie, "1"),
            Decimal("1.000000000000000000000000001"),
        )
        self.assertEqual(
            half_even.multiply(tie, "1"),
            Decimal("1.000000000000000000000000000"),
        )
        # The real representative formulas do not hit a HALF_UP/HALF_EVEN tie
        # at 40 digits on these vectors; rounding mode remains explicitly frozen.
        self.assertEqual(
            _formula_snapshot(DecimalPolicy(40, rounding=ROUND_HALF_UP)),
            _formula_snapshot(DecimalPolicy(40, rounding=ROUND_HALF_EVEN)),
        )

    def test_after_fix_external_ambient_context_cannot_change_authoritative_results(self) -> None:
        snapshots: dict[str, dict[str, str]] = {}
        for name, precision, rounding in (
            ("28_HALF_EVEN", 28, ROUND_HALF_EVEN),
            ("40_HALF_UP", 40, ROUND_HALF_UP),
            ("16_DOWN", 16, ROUND_DOWN),
        ):
            with localcontext() as context:
                context.prec = precision
                context.rounding = rounding
                snapshots[name] = {key: str(value) for key, value in _formula_snapshot().items()}
        print("N01C_AFTER_FIX_CONTEXT=" + json.dumps(snapshots, ensure_ascii=False, sort_keys=True))
        self.assertEqual(snapshots["28_HALF_EVEN"], snapshots["40_HALF_UP"])
        self.assertEqual(snapshots["16_DOWN"], snapshots["40_HALF_UP"])

    def test_precision_28_34_40_50_sensitivity_is_bounded_and_display_stable(self) -> None:
        snapshots = {
            precision: _formula_snapshot(DecimalPolicy(precision=precision, rounding=ROUND_HALF_UP))
            for precision in (28, 34, 40, 50)
        }
        serializable = {
            str(precision): {key: str(value) for key, value in values.items()}
            for precision, values in snapshots.items()
        }
        print("N01C_PRECISION_SENSITIVITY=" + json.dumps(serializable, ensure_ascii=False, sort_keys=True))

        # 40 retains twelve guard digits beyond the minimum 28.  On the current
        # representative formula set its difference from a 50-digit reference
        # is far below any displayed digit and no exact/finite path drifts.
        for key in snapshots[40]:
            delta = abs(snapshots[40][key] - snapshots[50][key])
            self.assertLess(delta, Decimal("1e-37"), (key, delta))
        display_policy = DecimalPolicy()
        for key in snapshots[28]:
            displays = {
                display_policy.format_for_display(snapshots[precision][key])
                for precision in (28, 34, 40, 50)
            }
            self.assertEqual(len(displays), 1, (key, displays))

    def test_business_ratio_boundary_remains_exact_not_close(self) -> None:
        calculator = CarbonMaterialCalculator()
        equal_problems = []
        below_problems = []
        above_problems = []
        self.assertEqual(
            calculator._ratio(InputValue("1", "ratio"), "equal", equal_problems),
            Decimal("1"),
        )
        self.assertEqual(
            calculator._ratio(
                InputValue("0.9999999999999999999999999999", "ratio"),
                "below",
                below_problems,
            ),
            Decimal("0.9999999999999999999999999999"),
        )
        calculator._ratio(
            InputValue("1.0000000000000000000000000001", "ratio"),
            "above",
            above_problems,
        )
        self.assertFalse(equal_problems)
        self.assertFalse(below_problems)
        self.assertTrue(any(problem.code == "CAR-VAL-PERCENT-RANGE" for problem in above_problems))


class N01CQuantityUnitTests(unittest.TestCase):
    def test_pure_unit_conversions_remain_unit_only(self) -> None:
        units = UnitService()
        cases = (
            ("1", "t", "kg", "1000"),
            ("1000", "kg", "t", "1"),
            ("1", "MWh", "GJ", "3.6"),
            ("1", "ten_thousand_Nm3", "Nm3", "10000"),
            ("1", "percent", "ratio", "0.01"),
        )
        for value, source, target, expected in cases:
            with self.subTest(source=source, target=target):
                self.assertEqual(units.convert(value, source, target), Decimal(expected))

    def test_legacy_tc_to_tco2_bridge_is_characterized_not_promoted(self) -> None:
        units = UnitService()
        legacy = units.convert("1", "tC", "tCO2")
        self.assertEqual(
            legacy,
            DecimalPolicy().divide("44", "12"),
        )
        # The legacy API remains during this Pilot because D-011 has not frozen
        # a replacement, but the candidate trace below classifies 44/12 as a
        # stoichiometric transformation, not an ordinary unit multiplier.
        coefficient = RationalCoefficientCandidate(
            "stoich.co2_from_c.44_12", "STOICHIOMETRIC", "44", "12",
            "CAR-FML-FUEL-001", "SRC-32151-34-2024", "GB/T 32151.34—2024 第5.2.1条",
        )
        source = ExtendedQuantityCandidate("1", "substance_mass", "t", substance_id="C")
        output, trace = apply_rational_transformation(
            source, coefficient, output_substance_id="CO2"
        )
        self.assertEqual(output.value, legacy)
        self.assertEqual(output.substance_id, "CO2")
        self.assertEqual(trace.coefficient["rational_expression"], "44/12")
        self.assertEqual(trace.coefficient["coefficient_type"], "STOICHIOMETRIC")

    def test_minimal_and_extended_quantity_candidates_round_trip(self) -> None:
        minimal = MinimalQuantityCandidate("1.00", "mass_carbon", "t")
        self.assertEqual(MinimalQuantityCandidate(**minimal.as_json()), minimal)
        for substance in ("C", "CO2", "CH4"):
            quantity = ExtendedQuantityCandidate(
                "12.500", "substance_mass", "t", substance_id=substance
            )
            restored = ExtendedQuantityCandidate(**quantity.as_json())
            self.assertEqual(restored, quantity)
        with self.assertRaises(ValueError):
            MinimalQuantityCandidate("1", "mass_carbon", "MWh")
        with self.assertRaises(ValueError):
            ExtendedQuantityCandidate("1", "co2e_mass", "t")

    def test_gwp_candidate_is_provenanced_and_candidate_only(self) -> None:
        basis = EquivalenceBasisCandidate(
            method_id="GWP",
            factor_id="gwp_co2_ar6_100",
            factor_value="1",
            time_horizon_years=100,
            assessment_id="IPCC-AR6-WGI",
            source_id="SRC-IPCC-AR6-WGI",
            source_location="Chapter 7 Table 7.15 / Supplementary Table 7.SM.7",
            factor_year=2021,
        )
        co2 = ExtendedQuantityCandidate("1", "substance_mass", "t", substance_id="CO2")
        co2e, trace = apply_gwp_candidate(co2, basis)
        self.assertEqual(co2e.value, Decimal("1"))
        self.assertEqual(co2e.quantity_type, "co2e_mass")
        self.assertTrue(trace.candidate_only)
        self.assertEqual(trace.coefficient["coefficient_type"], "CHARACTERIZATION_FACTOR")
        self.assertEqual(trace.coefficient["time_horizon_years"], 100)


class N01CToleranceInventoryTests(unittest.TestCase):
    def test_is_close_is_not_used_by_business_packages(self) -> None:
        business_calls: list[str] = []
        for path in Path("packages").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), 1):
                if ".is_close(" in line:
                    business_calls.append(f"{path}:{line_number}:{line.strip()}")
        self.assertEqual(business_calls, [])

    def test_known_tolerances_are_test_assertions_not_business_boundaries(self) -> None:
        g01 = Path("tests/test_g01_decimal_units.py").read_text(encoding="utf-8")
        g06 = Path("tests/test_g06_carbon_material.py").read_text(encoding="utf-8")
        self.assertIn("is_close", g01)
        self.assertIn("1E-38", g01)
        self.assertIn("1e-24", g06)
        carbon = Path("packages/standards/carbon_material.py").read_text(encoding="utf-8")
        self.assertNotIn("is_close", carbon)
        self.assertNotIn("tolerance", carbon.casefold())
        self.assertIn("_linear_interpolate", carbon)


class N01CConformanceVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
        cls.vectors = cls.document["vectors"]

    def test_every_vector_has_unique_id_and_required_categories_exist(self) -> None:
        ids = [vector["case_id"] for vector in self.vectors]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({
            "unit", "quantity", "coefficient", "gwp", "formula", "boundary",
            "display", "context", "precision", "invalid", "serialization",
        }.issubset({vector["category"] for vector in self.vectors}))

    def test_vectors_execute(self) -> None:
        units = UnitService()
        executed: list[str] = []
        for vector in self.vectors:
            operation = vector["operation"]
            case_id = vector["case_id"]
            with self.subTest(case_id=case_id):
                if operation == "convert":
                    data = vector["input"]
                    actual = units.convert(data["value"], data["from_unit"], data["to_unit"])
                    self.assertEqual(actual, Decimal(vector["expected"]))
                elif operation == "minimal_quantity":
                    MinimalQuantityCandidate(**vector["input"])
                elif operation == "extended_quantity":
                    ExtendedQuantityCandidate(**vector["input"])
                elif operation in {"c_to_co2", "coefficient_value"}:
                    data = vector["coefficient"]
                    coefficient = RationalCoefficientCandidate(
                        data["coefficient_id"], data["coefficient_type"], data["numerator"],
                        data["denominator"], data["formula_id"], data["source_id"],
                        data["source_location"],
                    )
                    self.assertEqual(coefficient.expression, data["rational_expression"])
                    if operation == "c_to_co2":
                        source = ExtendedQuantityCandidate(
                            vector["input"]["value"], "substance_mass",
                            vector["input"]["unit_id"], substance_id="C",
                        )
                        output, trace = apply_rational_transformation(
                            source, coefficient, output_substance_id="CO2"
                        )
                        self.assertEqual(output.value, Decimal(vector["expected"]))
                        self.assertEqual(trace.coefficient["coefficient_type"], "STOICHIOMETRIC")
                    else:
                        self.assertEqual(coefficient.value(), Decimal(vector["expected"]))
                elif operation == "gwp_to_co2e_candidate":
                    data = vector["gwp"]
                    basis = EquivalenceBasisCandidate(
                        "GWP", data["factor_id"], data["value"], data["time_horizon_years"],
                        data["assessment_id"], data["source_id"], data["source_location"],
                        data["factor_year"],
                    )
                    source = ExtendedQuantityCandidate(**vector["input"])
                    output, trace = apply_gwp_candidate(source, basis)
                    self.assertEqual(str(output.value), vector["expected"]["value"])
                    self.assertEqual(output.quantity_type, vector["expected"]["quantity_type"])
                    self.assertTrue(trace.candidate_only)
                elif operation == "fuel_volume":
                    self.assertEqual(
                        fuel_volume_emission(**vector["input"]), Decimal(vector["expected"])
                    )
                elif operation == "graphitization":
                    self.assertEqual(
                        graphitization_emission(**_graph_kwargs()), Decimal(vector["expected"])
                    )
                elif operation == "fume":
                    self.assertEqual(
                        fume_incineration_emission(**vector["input"]), Decimal(vector["expected"])
                    )
                elif operation == "exact_ratio_boundary":
                    values = {key: Decimal(value) for key, value in vector["input"].items()}
                    self.assertTrue(values["equal"] == Decimal("1"))
                    self.assertTrue(values["below"] < Decimal("1"))
                    self.assertTrue(values["above"] > Decimal("1"))
                elif operation == "display_separation":
                    policy = DecimalPolicy()
                    self.assertEqual(policy.parse(vector["input"]), Decimal(vector["expected_calculation"]))
                    self.assertEqual(policy.format_for_display(vector["input"]), vector["expected_display"])
                elif operation == "ambient_invariance":
                    snapshots = []
                    rounding_map = {
                        "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
                        "ROUND_HALF_UP": ROUND_HALF_UP,
                        "ROUND_DOWN": ROUND_DOWN,
                    }
                    for context_spec in vector["contexts"]:
                        with localcontext() as context:
                            context.prec = context_spec["precision"]
                            context.rounding = rounding_map[context_spec["rounding"]]
                            snapshots.append(_formula_snapshot())
                    self.assertTrue(all(snapshot == snapshots[0] for snapshot in snapshots[1:]))
                elif operation == "precision_sensitivity":
                    snapshots = {
                        precision: _formula_snapshot(DecimalPolicy(precision=precision))
                        for precision in vector["precisions"]
                    }
                    candidate = snapshots[vector["candidate_precision"]]
                    reference = snapshots[vector["reference_precision"]]
                    self.assertTrue(
                        all(abs(candidate[key] - reference[key]) < Decimal("1e-37") for key in candidate)
                    )
                elif operation == "reject_minimal_quantity":
                    with self.assertRaises(ValueError):
                        MinimalQuantityCandidate(**vector["input"])
                elif operation == "reject_extended_quantity":
                    with self.assertRaises(ValueError):
                        ExtendedQuantityCandidate(**vector["input"])
                elif operation == "quantity_round_trip":
                    value = ExtendedQuantityCandidate(**vector["input"])
                    self.assertEqual(ExtendedQuantityCandidate(**value.as_json()), value)
                else:
                    self.fail(f"unhandled conformance operation: {operation}")
                executed.append(case_id)
        self.assertEqual(len(executed), len(self.vectors))
        print("N01C_CONFORMANCE_EXECUTED=" + json.dumps(executed))


if __name__ == "__main__":
    unittest.main()
