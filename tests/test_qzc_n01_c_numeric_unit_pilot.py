from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import json
import unittest

from packages.core import DecimalPolicy
from packages.standards.carbon_material import (
    baking_emission,
    calcination_emission,
    fuel_volume_emission,
    fume_incineration_emission,
    graphitization_emission,
    saturated_steam_enthalpy,
    superheated_steam_enthalpy,
)


class N01CBeforeFixCharacterizationTests(unittest.TestCase):
    """Characterize the pre-fix authoritative arithmetic before N01-C changes it.

    This first Pilot commit deliberately records the defect as a passing
    characterization: production results currently depend on the caller's
    ambient Decimal context.  The follow-up Numeric authority fix must invert
    these assertions and prove context independence.
    """

    def _formula_snapshot(self, precision: int, rounding: str) -> dict[str, str]:
        with localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            fuel = fuel_volume_emission("2", "0.015", "0.98")
            calcination = calcination_emission(
                gc="100", wfc="0.008", cc="70", ucc="5", du="1",
                wfc_c="0.002", wvar="0.10", wvar_c="0.02", k1="0.35",
            )
            baking = baking_emission(
                bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
                bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
            )
            graphitization = graphitization_emission(
                gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
                gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
            )
            fume = fume_incineration_emission("1000", "10", "30", "0.02", "0.98", "1")
            saturated = saturated_steam_enthalpy("1.75")[0]
            superheated = superheated_steam_enthalpy("1.23456789", "333.333333")[0]
            total = fuel + calcination + baking + graphitization + fume
            return {
                "fuel": str(fuel),
                "calcination": str(calcination),
                "baking": str(baking),
                "graphitization": str(graphitization),
                "fume": str(fume),
                "saturated_steam": str(saturated),
                "superheated_steam": str(superheated),
                "representative_total": str(total),
            }

    def test_declared_decimal_policy_is_40_half_up_display_2(self) -> None:
        policy = DecimalPolicy()
        self.assertEqual(policy.precision, 40)
        self.assertEqual(policy.rounding, ROUND_HALF_UP)
        self.assertEqual(policy.display_places, 2)
        self.assertEqual(policy.round_for_display("1.235"), Decimal("1.24"))

    def test_before_fix_authoritative_results_depend_on_ambient_context(self) -> None:
        p28 = self._formula_snapshot(28, ROUND_HALF_EVEN)
        p40 = self._formula_snapshot(40, ROUND_HALF_UP)
        adversarial = self._formula_snapshot(16, ROUND_DOWN)
        print("N01C_BEFORE_FIX_CONTEXT=" + json.dumps(
            {"28_HALF_EVEN": p28, "40_HALF_UP": p40, "16_DOWN": adversarial},
            ensure_ascii=False,
            sort_keys=True,
        ))

        # The defect is real when at least the repeating-coefficient paths and
        # an interpolation path drift under external context changes.
        self.assertNotEqual(p28["fuel"], p40["fuel"])
        self.assertNotEqual(p28["baking"], p40["baking"])
        self.assertNotEqual(p28["graphitization"], p40["graphitization"])
        self.assertNotEqual(p28["fume"], p40["fume"])
        self.assertNotEqual(p28["superheated_steam"], p40["superheated_steam"])
        self.assertNotEqual(adversarial["representative_total"], p40["representative_total"])

    def test_before_fix_precision_sensitivity_28_34_40_50_is_recorded(self) -> None:
        values = {
            precision: self._formula_snapshot(precision, ROUND_HALF_UP)
            for precision in (28, 34, 40, 50)
        }
        print("N01C_BEFORE_FIX_PRECISION=" + json.dumps(values, ensure_ascii=False, sort_keys=True))
        self.assertNotEqual(values[28]["graphitization"], values[40]["graphitization"])
        self.assertNotEqual(values[40]["graphitization"], values[50]["graphitization"])
        # Although the full Decimal tails differ, the current display policy is
        # stable for all four candidate working precisions on this vector.
        policy = DecimalPolicy()
        displays = {
            precision: policy.format_for_display(Decimal(snapshot["representative_total"]))
            for precision, snapshot in values.items()
        }
        self.assertEqual(len(set(displays.values())), 1)


if __name__ == "__main__":
    unittest.main()
