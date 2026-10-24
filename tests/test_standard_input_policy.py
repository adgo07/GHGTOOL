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
    def _parameter(name, value, unit, kind=ParameterSourceKind.MEASURED):
        return ParameterValue(name, value, unit, source_kind=kind, source_id=None, source_version=None,
                              source_location="用户提供的参数", selection_reason="用户明确填写")

    def _calculate(self, *, origin=InputOrigin.CUSTOM, fch_kind=ParameterSourceKind.MEASURED, path=FuelPath.MASS):
        fuel = FuelInput(
            "custom", path, "10",
            self._parameter("fch", "0.03", "tC/GJ", fch_kind),
            self._parameter("fox", "0.98", "ratio", ParameterSourceKind.MEASURED),
            self._parameter("lhv", "8", "GJ/t" if path is FuelPath.MASS else "GJ/10⁴Nm³", ParameterSourceKind.MEASURED),
            fuel_type=FuelType.OTHER if origin is InputOrigin.CUSTOM else FuelType.NATURAL_GAS,
            fuel_label="用户定义的燃料", origin=origin,
            catalog_subject_id="natural_gas" if origin is InputOrigin.CATALOG else None,
        )
        value = CarbonMaterialInput(
            "input.policy", "enterprise.policy", "输入政策测试企业",
            AccountingPeriod(PeriodType.ANNUAL, date(2025,1,1), date(2025,12,31)),
            boundary_confirmed=True, fuel_inputs=(fuel,),
            source_states=(EmissionSourceState(SOURCE_FUEL,EmissionSourceStatus.INVOLVED),),
        )
        if origin is InputOrigin.CATALOG:
            import tempfile
            from pathlib import Path
            from packages.application.carbon_accounting import create_g06_parameter_resolver
            from packages.persistence import SQLiteCatalogRepository, build_catalog_database
            with tempfile.TemporaryDirectory() as directory:
                repository = SQLiteCatalogRepository(build_catalog_database(output_path=Path(directory)/"catalog.sqlite"))
                return CarbonMaterialCalculator(parameter_resolver=create_g06_parameter_resolver(repository)).calculate(value)
        return CarbonMaterialCalculator().calculate(value)

    def test_custom_computed_mass_and_volume_accept_measured_fch(self):
        for path in (FuelPath.MASS, FuelPath.VOLUME):
            with self.subTest(path=path):
                outcome=self._calculate(path=path)
                self.assertFalse(outcome.blocked, outcome.problems)
                self.assertEqual(outcome.result.total_amount,Decimal("8.624000000000000000000000000000000000001"))
                self.assertIsNone(outcome.record)
                self.assertIs(outcome.input.fuel_inputs[0].carbon_content.source_kind, ParameterSourceKind.MEASURED)
                self.assertIs(outcome.input.fuel_inputs[0].oxidation_rate.source_kind, ParameterSourceKind.MEASURED)

    def test_custom_fuel_may_not_claim_a_catalog_default(self):
        outcome=self._calculate(fch_kind=ParameterSourceKind.STANDARD_DEFAULT)
        self.assertTrue(outcome.blocked)
        self.assertIn("CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE",{p.code for p in outcome.problems})
        self.assertTrue(next(
            p for p in outcome.problems if p.code=="CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE"
        ).field_id == "CAR-FLD-F01-custom-CARBON")

    def test_catalog_measured_fch_is_accepted_and_calculated_preserved_but_blocked(self):
        for source_kind in (ParameterSourceKind.MEASURED, ParameterSourceKind.CALCULATED):
            with self.subTest(source_kind=source_kind):
                outcome = self._calculate(origin=InputOrigin.CATALOG, fch_kind=source_kind)
                self.assertEqual(outcome.blocked, source_kind is ParameterSourceKind.CALCULATED, outcome.problems)
                if source_kind is ParameterSourceKind.CALCULATED:
                    self.assertIn("CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE", {problem.code for problem in outcome.problems})
                    self.assertIsNone(outcome.record)
                self.assertEqual(
                    outcome.input.fuel_inputs[0].carbon_content.source_kind,
                    source_kind,
                )

    def test_catalog_legacy_user_defined_fch_is_preserved_but_requires_confirmation_to_recalculate(self):
        outcome = self._calculate(origin=InputOrigin.CATALOG, fch_kind=ParameterSourceKind.USER_DEFINED)
        self.assertTrue(outcome.blocked)
        self.assertIn("CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE", {p.code for p in outcome.problems})
        self.assertIs(
            outcome.input.fuel_inputs[0].carbon_content.source_kind,
            ParameterSourceKind.USER_DEFINED,
        )
        self.assertIsNone(outcome.record)

    def test_catalog_fch_editability_depends_on_explicit_source(self):
        # Missing identity must stay correctable, never silently claim a default.
        self.assertTrue(fuel_input_policy(InputOrigin.CATALOG, direct_carbon=False).fch_editable)
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
            row.fuel_type.confirm_name(force=True)
            self.assertEqual(row.fuel_type.currentText(),"天然气")
            self.assertEqual(row.fuel_type.currentData(),FuelType.NATURAL_GAS)
            # V2 places the business path before parameters and reflows the
            # same inputs; an old fixed row count cannot describe that layout.
            properties = ("fuel_type", "path", "activity", "carbon_basis",
                          "lower_heating_value", "carbon", "oxidation",
                          "lhv_source", "carbon_source", "direct_carbon_source", "oxidation_source")
            controls = {name: getattr(row, name) for name in properties}
            modes = (row.lhv_source, row.carbon_source, row.direct_carbon_source, row.oxidation_source)
            def source_state():
                return [(mode.currentData(), tuple((mode.itemText(i), mode.itemData(i),
                         mode.model().flags(mode.model().index(i, 0))) for i in range(mode.count())))
                        for mode in modes]
            original_sources = source_state()
            row.show()
            for width in (1100, 650, 430, 1100):
                row.resize(width, row.height())
                for _ in range(8):
                    app.processEvents()
                row.resize(row.width(), row.sizeHint().height())
                for _ in range(8):
                    app.processEvents()
                for name, control in controls.items():
                    self.assertIs(getattr(row, name), control)
                    self.assertTrue(row.isAncestorOf(control))
                self.assertEqual(source_state(), original_sources)
                self.assertEqual(row.fuel_type.count(), 1)
                self.assertEqual(row.fuel_type.currentText(), "天然气")
                self.assertEqual(row.fuel_type.currentData(), FuelType.NATURAL_GAS)
                cells = [*row.identity_cells, row.basis_field, *row.parameter_cells,
                         row.carbon_value_field, row.source_reference_control, row.inactive_parameters_toggle]
                visible_cells = [cell for cell in cells if not cell.isHidden()]
                actual_cells = [row.input_grid.itemAt(i).widget() for i in range(row.input_grid.count())]
                self.assertEqual(len(actual_cells), len({id(cell) for cell in actual_cells}))
                self.assertCountEqual([cell for cell in actual_cells if not cell.isHidden()], visible_cells)
                basis_index = row.input_grid.indexOf(row.basis_field)
                self.assertGreaterEqual(basis_index, 0)
                basis_row = row.input_grid.getItemPosition(basis_index)[0]
                for cell in row.parameter_cells:
                    if not cell.isHidden():
                        index = row.input_grid.indexOf(cell)
                        self.assertGreaterEqual(index, 0)
                        self.assertLess(basis_row, row.input_grid.getItemPosition(index)[0])
        finally:
            row.deleteLater();app.processEvents()


if __name__ == "__main__":
    unittest.main()
