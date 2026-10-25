"""Energy presentation preserves source choices and saved heat boundaries."""
import unittest
from PySide6.QtWidgets import QApplication
from tests import test_accounting_projects_ui as project_fixture


class EnergyPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
    setUp = project_fixture.AccountingProjectUiTests.setUp
    tearDown = project_fixture.AccountingProjectUiTests.tearDown
    _new_page = project_fixture.AccountingProjectUiTests._new_page

    def test_new_external_heat_is_compact_and_disclosure_does_not_write(self):
        page = self.page
        row = page._energy_family_rows['heat'][0]
        self.assertEqual(row.heat_boundary.currentData(), 'OUTSIDE_ENTERPRISE')
        self.assertIs(row.heat_fuel_accounted.currentData(), False)
        self.assertTrue(row.heat_boundary_group.isHidden())
        before = page._capture_form_state()
        page._project_dirty = page._input_dirty = False
        row.heat_special_toggle.setChecked(True)
        self.assertFalse(row.heat_boundary_field.isHidden())
        row.heat_special_toggle.setChecked(False)
        self.assertEqual(before, page._capture_form_state())
        self.assertFalse(page._project_dirty)
        self.assertFalse(page._input_dirty)

    def test_internal_heat_and_output_keep_boundary_and_accounted_drafts(self):
        page = self.page
        row = page._energy_family_rows['heat'][0]
        row.heat_boundary.setCurrentIndex(row.heat_boundary.findData('INSIDE_ENTERPRISE'))
        row.heat_fuel_accounted.setCurrentIndex(row.heat_fuel_accounted.findData(True))
        self.assertTrue(row.heat_special_toggle.isChecked())
        self.assertIn('不重复计购热', row.status.text())
        row.kind.setCurrentIndex(row.kind.findData('exported_heat'))
        self.assertEqual(row.heat_boundary.currentData(), 'INSIDE_ENTERPRISE')
        self.assertIs(row.heat_fuel_accounted.currentData(), True)
        self.assertTrue(row.heat_special_toggle.isHidden())
        self.assertIn('输出热力', row.heat_boundary_summary.text())
        row.kind.setCurrentIndex(row.kind.findData('purchased_heat'))
        self.assertTrue(row.heat_special_toggle.isChecked())
        self.assertIn('不重复计购热', row.status.text())

    def test_missing_old_boundary_restores_unknown_instead_of_new_default(self):
        page = self.page
        saved = page._capture_form_state()
        heat = next(item for item in saved['energy_rows'] if item['kind'] == 'purchased_heat')
        heat.pop('heat_boundary', None)
        heat.pop('heat_fuel_accounted', None)
        page._restore_form_state(saved)
        row = page._energy_family_rows['heat'][0]
        self.assertEqual(row.heat_boundary.currentData(), 'UNCONFIRMED')
        self.assertIsNone(row.heat_fuel_accounted.currentData())
        self.assertTrue(row.heat_special_toggle.isChecked())
        self.assertIn('未明确前不能核算', row.status.text())

    def test_factor_choices_show_actual_value_first_and_keep_original_options(self):
        row = self.page._energy_family_rows['electricity'][0]
        options = [row.factor_selector.itemData(i) for i in range(row.factor_selector.count())]
        actual = [(i, option) for i, option in enumerate(options) if getattr(option, 'factor', None) is not None]
        self.assertTrue(actual)
        for index, option in actual:
            self.assertTrue(row.factor_selector.itemText(index).startswith(str(option.factor.value)))
            self.assertIn(str(option.factor.factor_year), row.factor_selector.itemText(index))
            self.assertEqual(row.factor_selector.model().item(index).isEnabled(), option.selectable)
        chosen = row.factor_selector.currentData()
        self.assertIsNotNone(chosen)
        self.assertIn(str(chosen.factor.factor_year), row.factor_explanation.text())
        row.factor_mode.setCurrentIndex(row.factor_mode.findData('MANUAL'))
        self.assertTrue(row.region_group.isHidden())
        self.assertEqual(options, [row.factor_selector.itemData(i) for i in range(row.factor_selector.count())])
