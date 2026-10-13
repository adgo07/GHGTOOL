"""Independent .34 input-policy examples, including formal validation."""
from datetime import date
from decimal import Decimal
import unittest
from packages.core.models import AccountingPeriod, PeriodType
from packages.standards.carbon_material_input_policy import InputOrigin, fuel_input_policy
from packages.standards.carbon_material import (
    CarbonMaterialCalculator, CarbonMaterialInput, FuelInput, FuelPath, FuelType,
    ParameterValue, ParameterSourceKind, SOURCE_FUEL, EmissionSourceState, EmissionSourceStatus,
)


class StandardInputPolicyTests(unittest.TestCase):
    @staticmethod
    def _parameter(name, value, unit, kind=ParameterSourceKind.USER_DEFINED):
        return ParameterValue(name, value, unit, source_kind=kind, source_id=None, source_version=None,
                              source_location="用户提供的参数", selection_reason="用户明确填写")

    def _calculate(self, *, origin=InputOrigin.CUSTOM, fch_kind=ParameterSourceKind.USER_DEFINED, path=FuelPath.MASS):
        fuel = FuelInput(
            "custom", path, "10",
            self._parameter("fch", "0.03", "tC/GJ", fch_kind),
            self._parameter("fox", "0.98", "ratio"),
            self._parameter("lhv", "8", "GJ/t" if path is FuelPath.MASS else "GJ/10⁴Nm³"),
            fuel_type=FuelType.OTHER if origin is InputOrigin.CUSTOM else FuelType.NATURAL_GAS,
            fuel_label="用户定义的燃料", origin=origin,
        )
        value = CarbonMaterialInput(
            "input.policy", "enterprise.policy", "输入政策测试企业",
            AccountingPeriod(PeriodType.ANNUAL, date(2025,1,1), date(2025,12,31)),
            boundary_confirmed=True, fuel_inputs=(fuel,),
            source_states=(EmissionSourceState(SOURCE_FUEL,EmissionSourceStatus.INVOLVED),),
        )
        return CarbonMaterialCalculator().calculate(value)

    def test_custom_computed_mass_and_volume_accept_filled_fch_with_true_source(self):
        for path in (FuelPath.MASS, FuelPath.VOLUME):
            with self.subTest(path=path):
                outcome=self._calculate(path=path)
                self.assertFalse(outcome.blocked, outcome.problems)
                self.assertEqual(outcome.result.total_amount,Decimal("8.624000000000000000000000000000000000001"))
                self.assertIsNone(outcome.record)
                self.assertTrue(all(p.source_kind is ParameterSourceKind.USER_DEFINED
                                    for p in (outcome.input.fuel_inputs[0].carbon_content,
                                              outcome.input.fuel_inputs[0].oxidation_rate)))

    def test_custom_fuel_may_not_claim_a_catalog_default(self):
        outcome=self._calculate(fch_kind=ParameterSourceKind.STANDARD_DEFAULT)
        self.assertTrue(outcome.blocked)
        self.assertIn("CAR-VAL-CUSTOM-FUEL-DEFAULT",{p.code for p in outcome.problems})
        self.assertTrue(next(p for p in outcome.problems if p.code=="CAR-VAL-CUSTOM-FUEL-DEFAULT").field_id.endswith("-CARBON"))

    def test_catalog_fuel_may_not_bypass_fch_readonly_through_formal_input(self):
        outcome=self._calculate(origin=InputOrigin.CATALOG)
        self.assertTrue(outcome.blocked)
        self.assertIn("CAR-VAL-CATALOG-FCH-READONLY",{p.code for p in outcome.problems})

    def test_direct_policy_does_not_require_lhv_or_fch(self):
        policy=fuel_input_policy(InputOrigin.CUSTOM,direct_carbon=True)
        self.assertEqual(policy.required_parameters,("carbon_content","oxidation_rate"))
        self.assertFalse(policy.default_parameters_allowed)


if __name__ == "__main__":
    unittest.main()
