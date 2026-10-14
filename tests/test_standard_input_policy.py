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

    def test_catalog_explicit_measured_and_calculated_fch_are_accepted(self):
        for source_kind in (ParameterSourceKind.MEASURED, ParameterSourceKind.CALCULATED):
            with self.subTest(source_kind=source_kind):
                outcome = self._calculate(origin=InputOrigin.CATALOG, fch_kind=source_kind)
                self.assertFalse(outcome.blocked, outcome.problems)
                self.assertEqual(
                    outcome.input.fuel_inputs[0].carbon_content.source_kind,
                    source_kind,
                )

    def test_catalog_legacy_user_defined_fch_is_preserved_without_renaming(self):
        outcome = self._calculate(origin=InputOrigin.CATALOG, fch_kind=ParameterSourceKind.USER_DEFINED)
        self.assertFalse(outcome.blocked, outcome.problems)
        self.assertIs(
            outcome.input.fuel_inputs[0].carbon_content.source_kind,
            ParameterSourceKind.USER_DEFINED,
        )

    def test_catalog_fch_editability_depends_on_explicit_source(self):
        self.assertFalse(fuel_input_policy(InputOrigin.CATALOG, direct_carbon=False).fch_editable)
        self.assertTrue(fuel_input_policy(
            InputOrigin.CATALOG, direct_carbon=False, carbon_source_kind="MEASURED"
        ).fch_editable)
        self.assertTrue(fuel_input_policy(
            InputOrigin.CATALOG, direct_carbon=False, carbon_source_kind="CALCULATED"
        ).fch_editable)

    def test_direct_policy_does_not_require_lhv_or_fch(self):
        policy=fuel_input_policy(InputOrigin.CUSTOM,direct_carbon=True)
        self.assertEqual(policy.required_parameters,("carbon_content","oxidation_rate"))
        self.assertFalse(policy.default_parameters_allowed)

    def test_fuel_alias_matching_is_normalized_and_ambiguous_names_fail(self):
        from types import SimpleNamespace
        from packages.standards.carbon_material_input_policy import match_fuel_option, fuel_path_for_unit
        gas=SimpleNamespace(label="天然气",aliases=("NG",))
        self.assertIs(match_fuel_option((gas,),"ｎｇ"),gas)
        self.assertIsNone(match_fuel_option((gas,),"库外燃料"))
        self.assertIsNone(match_fuel_option((gas,SimpleNamespace(label="另一燃料",aliases=("NG",))),"NG"))
        self.assertEqual(fuel_path_for_unit("10⁴Nm³"),"VOLUME")
        self.assertEqual(fuel_path_for_unit("t"),"MASS")
        self.assertIsNone(fuel_path_for_unit("GJ"))

    def test_fuel_editor_lists_only_canonical_options_and_searches_aliases(self):
        from PySide6.QtWidgets import QApplication
        from packages.ui.carbon_material_fuel import _FuelRow
        from types import SimpleNamespace
        app=QApplication.instance() or QApplication([])
        option=SimpleNamespace(label="天然气",aliases=("NG","Natural Gas"),fuel_type=FuelType.NATURAL_GAS,subject_id="natural_gas")
        row=_FuelRow(1,lambda _row:None,fuel_options=(option,))
        try:
            self.assertEqual(row.fuel_type.count(),1)
            self.assertEqual(row.fuel_type.itemText(0),"天然气")
            row.fuel_type.setEditText("NG")
            row._accept_search_match("NG")
            self.assertEqual(row.fuel_type.currentText(),"天然气")
            self.assertEqual(row.input_grid.rowCount(),3) # two input bands + optional evidence
        finally:
            row.deleteLater();app.processEvents()


if __name__ == "__main__":
    unittest.main()
