"""Exercise the V2 GUI through saved, immutable formal records."""
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal, localcontext
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.persistence import SQLiteRecordRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from packages.standards.carbon_material_normalization import MaterialRole


class UAT03FormalWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        catalog = build_catalog_database(DEFAULT_SOURCE_PATH, root / "catalog.sqlite")
        self.records = SQLiteRecordRepository(root / "records.sqlite")
        self.window = create_main_window(
            AppConfig(catalog_database=catalog, records_database=root / "records.sqlite",
                      projects_database=root / "projects.sqlite"),
            record_repository=self.records,
        )
        self.window.show()
        shell = self.window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.app.processEvents()
        self.page = shell.pages[AppRoute.NEW_ACCOUNTING]
        self.page.period_year.setValue(2025)
        self.page.enterprise_name.setText("V2正式链验收企业")
        self.page.boundary_confirmed.setChecked(True)
        for status in self.page._source_statuses.values():
            status.setCurrentIndex(status.findData("NOT_INVOLVED"))
        self.page._toggle_source_group("electricity")
        self.row = self.page._energy_family_rows["electricity"][0]
        self.row.amount.setText("12.34567890123456789")

    def tearDown(self):
        self.page._project_dirty = False
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _calculate(self):
        before = len(self.records.list_all())
        self.page.quick_calculate_button.click()
        self.app.processEvents()
        records = self.records.list_all()
        problems = [self.page.validation_list.topLevelItem(i).text(0)
                    for i in range(self.page.validation_list.topLevelItemCount())]
        self.assertEqual(len(records), before + 1, problems)
        return self.records.get(self.page._latest_record_id)

    def test_catalog_manual_catalog_switch_freezes_actual_factor_without_borrowed_identity(self):
        self.assertGreater(self.row.factor_selector.count(), 0)
        library = self._calculate()
        library_factor = next(s for s in library.parameter_snapshots if "electricity" in s.parameter_id.lower())
        self.assertIsNotNone(library_factor.factor_id)
        self.assertIsNotNone(library_factor.source_id)
        before = asdict(library)
        self.row.factor_mode.setCurrentIndex(self.row.factor_mode.findData("MANUAL"))
        self.row.manual_factor.setText("0.1234567890123456789")
        manual = self._calculate()
        factor = next(s for s in manual.parameter_snapshots if "electricity" in s.parameter_id.lower())
        self.assertEqual(factor.value_used, Decimal("0.1234567890123456789"))
        for name in ("factor_id", "source_id", "source_version", "factor_year"):
            self.assertIsNone(getattr(factor, name))
        with localcontext() as context:
            context.prec = 40
            expected = Decimal("12.34567890123456789") * Decimal("0.1234567890123456789")
        self.assertEqual(manual.calculation_result.total_amount, expected)
        self.assertEqual(asdict(self.records.get(library.record_id)), before)
        self.row.factor_mode.setCurrentIndex(self.row.factor_mode.findData("LIBRARY"))
        restored = self._calculate()
        restored_factor = next(s for s in restored.parameter_snapshots if "electricity" in s.parameter_id.lower())
        self.assertEqual(restored_factor.factor_id, library_factor.factor_id)
        self.assertEqual(restored_factor.value_used, library_factor.value_used)
        self.assertEqual(len(self.records.list_all()), 3)

    def test_word_entrypoint_uses_saved_record_and_is_disabled_after_input_changes(self):
        self.assertFalse(self.page.export_report_button.isEnabled())
        record = self._calculate()
        self.assertTrue(self.page.export_report_button.isEnabled())
        before = asdict(record)
        with patch("packages.ui.carbon_material_page.export_saved_record_report") as export:
            self.page.export_report_button.click()
            export.assert_called_once()
            self.assertEqual(export.call_args.args[2].record_id, record.record_id)
            self.row.amount.setText("13.1234567890123456789")
            self.app.processEvents()
            self.assertFalse(self.page.export_report_button.isEnabled())
            self.page._export_latest_record_report()
            self.assertEqual(export.call_count, 1)
        self.assertEqual(asdict(self.records.get(record.record_id)), before)
        refreshed = self._calculate()
        self.assertNotEqual(refreshed.record_id, record.record_id)
        self.assertTrue(self.page.export_report_button.isEnabled())

    def test_carbonate_default_and_user_factor_have_distinct_frozen_sources(self):
        self.page._toggle_source_group("electricity")
        self.page._toggle_source_group("fgd")
        unit = self.page._process_rows["fgd"][0]
        component = unit["components"][0]
        selector = component["carbonate_type"]
        self.assertTrue(selector.isEditable())
        selector.setEditText("CaCO3")
        component["cal"].setText("12.3456789")
        component["i"].setText("92.3456789")
        component["tr"].setText("98.7654321")
        expected = self.page._carbonate_option_for_text("CaCO3").factor
        standard = self._calculate()
        snapshot = next(s for s in standard.parameter_snapshots if s.factor_id == expected.factor_id)
        self.assertEqual(snapshot.value_used, expected.value)
        self.assertEqual(snapshot.source_id, expected.source_id)
        before = asdict(standard)
        saved = self.page._capture_form_state()
        self.page._restore_form_state(saved)
        component = self.page._process_rows["fgd"][0]["components"][0]
        selector = component["carbonate_type"]
        restored = self._calculate()
        restored_factor = next(s for s in restored.parameter_snapshots if s.factor_id == expected.factor_id)
        self.assertEqual(restored_factor.value_used, expected.value)
        component["ef1"].setText("0.5123456789123456789")
        manual = self._calculate()
        snapshot = next(s for s in manual.parameter_snapshots if s.unit_used == "tCO2/t" and s.value_used == Decimal("0.5123456789123456789"))
        self.assertEqual(snapshot.value_used, Decimal("0.5123456789123456789"))
        self.assertIsNone(snapshot.factor_id)
        self.assertIsNone(snapshot.source_id)
        self.assertEqual(asdict(self.records.get(standard.record_id)), before)
        selector.setEditText("企业自定义碳酸盐")
        self.assertIsNone(self.page._carbonate_option_for_text(selector.currentText()))
        self.assertEqual(component["ef1"].text(), "")

    def test_exported_electricity_manual_factor_is_deducted_with_domain_unit_and_own_source(self):
        purchased = self._calculate()
        output = self.page._add_unified_energy_row(kind="exported_electricity", line_id="output.actual")
        output.amount.setText("3.25")
        output.factor_mode.setCurrentIndex(output.factor_mode.findData("MANUAL"))
        output.manual_factor.setText("0.1234567890123456789")
        record = self._calculate()
        with localcontext() as context:
            context.prec = 40
            expected = purchased.calculation_result.total_amount - Decimal("3.25") * Decimal("0.1234567890123456789")
        self.assertEqual(record.calculation_result.total_amount, expected)
        snapshot = next(s for s in record.parameter_snapshots if s.value_used == Decimal("0.1234567890123456789"))
        self.assertEqual(snapshot.unit_used, "tCO2/MWh")
        self.assertIsNone(snapshot.factor_id)
        self.assertIsNone(snapshot.source_id)
        self.assertEqual(asdict(self.records.get(purchased.record_id)), asdict(purchased))

    def test_restored_dry_basis_and_conversion_evidence_are_frozen_without_reinterpretation(self):
        self.page._toggle_source_group("calcination")
        process = self.page._process_rows["calcination"][0]
        feed = process["materials"][0]
        product = self.page._add_material_line(process)
        for material, role, name, mass, fixed, volatile in (
            (feed, MaterialRole.CALCINATION_FEED, "历史干基原料", "100", "50", "10"),
            (product, MaterialRole.CALCINED_PRODUCT, "历史干基产品", "70", "25", "2"),
        ):
            material["role"].setCurrentIndex(material["role"].findData(role))
            for field, value in (("name", name), ("mass", mass), ("fixed_carbon", fixed), ("volatile_matter", volatile)):
                material[field].setText(value)
        controls = self.page._material_controls["calcination"]
        for field, value in (("mass_basis", "DRY"), ("composition_basis", "DRY"), ("normalized_basis", "RECEIVED")):
            controls[field].setCurrentIndex(controls[field].findData(value))
        controls["moisture_evidence"].setChecked(True)
        controls["conversion_evidence"].setChecked(True)
        controls["evidence_reference"].setText("旧项目换算依据记录")
        state = self.page._capture_form_state()
        self.page._restore_form_state(state)
        record = self._calculate()
        raw = self.records.get_raw_input_snapshot(record.record_id)["calcinations"][0]
        self.assertEqual(raw["mass_basis"], "DRY")
        self.assertEqual(raw["composition_basis"], "DRY")
        self.assertEqual(raw["normalized_basis"], "RECEIVED")
        self.assertTrue(raw["moisture_evidence"])
        self.assertTrue(raw["conversion_evidence"])
        self.assertEqual(self.page._material_controls["calcination"]["evidence_reference"].text(), "旧项目换算依据记录")
        controls = self.page._material_controls["calcination"]
        controls["conversion_evidence"].setChecked(False)
        before = len(self.records.list_all())
        self.page.quick_calculate_button.click()
        self.app.processEvents()
        self.assertEqual(len(self.records.list_all()), before)
        self.assertTrue(any(problem.code == "CAR-VAL-MATERIAL-BASIS-CONVERSION" for problem in self.page.calculator.calculate(self.page._input()).problems))
        self.assertEqual(self.records.get_raw_input_snapshot(record.record_id)["calcinations"][0], raw)
