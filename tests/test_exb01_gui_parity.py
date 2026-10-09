"""Real Qt input and Appendix-B input share formal, persisted business totals."""
from decimal import Decimal
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from openpyxl import load_workbook
from PySide6.QtWidgets import QApplication
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.core.models import PeriodType
from packages.excel.templates import ExcelTemplateService
from packages.persistence import SQLiteRecordRepository, SQLiteProjectWorkspaceRepository, build_catalog_database
from packages.application import ProjectWorkspaceService
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute


class AppendixBGuiParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_gui_and_workbook_save_same_es_et_and_preview_writes_no_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = build_catalog_database(DEFAULT_SOURCE_PATH, root / "catalog.sqlite")
            records = SQLiteRecordRepository(root / "records.sqlite")
            window = create_main_window(
                AppConfig(catalog_database=catalog, records_database=root / "records.sqlite",
                          projects_database=root / "projects.sqlite"),
                record_repository=records,
                project_service=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root / "projects.sqlite")),
            )
            window.show()
            shell = window.centralWidget()
            shell.navigate(AppRoute.NEW_ACCOUNTING)
            self.app.processEvents()
            gui = shell.pages[AppRoute.NEW_ACCOUNTING]
            try:
                gui.period_year.setValue(2025)
                gui.enterprise_name.setText("Excel与界面正式核算一致性")
                gui.boundary_confirmed.setChecked(True)
                for status in gui._source_statuses.values():
                    status.setCurrentIndex(status.findData("NOT_INVOLVED"))
                gui._toggle_source_group("electricity")
                row = gui._energy_family_rows["electricity"][0]
                row.amount.setText("12.34")
                row.factor_mode.setCurrentIndex(row.factor_mode.findData("MANUAL"))
                row.manual_factor.setText("0.5")
                gui.quick_calculate_button.click()
                self.app.processEvents()
                self.assertEqual(len(records.list_all()), 1)
                gui_record = records.get(gui._latest_record_id)

                workbook = load_workbook(BytesIO(ExcelTemplateService.default().read_bytes()))
                workbook["B.8"]["B3"] = "电网电力"
                workbook["B.8"]["C3"] = Decimal("12.34")
                workbook["B.8"]["D3"] = Decimal("0.5")
                source = root / "实际界面一致性.xlsx"
                workbook.save(source)  # Disposable test input; never the downloadable master.
                workbook.close()
                shell.navigate(AppRoute.EXCEL_IMPORT)
                self.app.processEvents()
                excel = shell.pages[AppRoute.EXCEL_IMPORT]
                excel.import_period_type.setCurrentIndex(excel.import_period_type.findData(PeriodType.ANNUAL))
                excel.import_period_start.setText("2025-01-01")
                excel.import_period_end.setText("2025-12-31")
                excel.import_boundary_confirmed.setChecked(True)
                with patch("packages.ui.pages.QMessageBox.warning") as warning:
                    excel._preview_workbook(source)
                    self.assertIsNotNone(excel._last_preview, warning.call_args)
                    self.assertEqual(len(excel._last_preview.units), 1)
                    unit = excel._last_preview.units[0]
                    self.assertTrue(unit.can_calculate, unit.errors)
                    self.assertEqual(len(records.list_all()), 1)
                    excel._save_preview_as_project()
                    self.assertEqual(len(records.list_all()), 1)
                    self.assertTrue(excel.calculate_button.isEnabled(), (excel.status_label.text(), warning.call_args, excel._workspace, excel.unit_selector.currentData()))
                    excel.calculate_button.click()
                    self.app.processEvents()
                    self.assertEqual(len(records.list_all()), 2, warning.call_args)
                excel_record = next(r for r in records.list_all() if r.record_id != gui_record.record_id)
                def totals(record):
                    return {line.line_id: line.amount for line in record.calculation_result.lines
                            if line.line_id in {"CAR-FLD-DIRECT-RESULT", "CAR-FLD-TOTAL-RESULT"}}
                expected = {"CAR-FLD-DIRECT-RESULT": Decimal("0"),
                            "CAR-FLD-TOTAL-RESULT": Decimal("6.17")}
                self.assertEqual(totals(gui_record), expected)
                self.assertEqual(totals(excel_record), expected)
                self.assertEqual(excel_record.calculation_result.total_amount, Decimal("6.17"))
                self.assertEqual(gui_record.calculation_result.total_amount, Decimal("6.17"))
                self.assertTrue(excel.open_project(excel._workspace.project_id))
                self.assertFalse(excel.import_period_start.isEnabled())
                self.assertFalse(excel.import_enterprise_name.isEnabled())
                self.assertFalse(excel.import_boundary_confirmed.isEnabled())
                self.assertIn("2025-01-01 至 2025-12-31", excel.preview_text.toPlainText())
                with patch("packages.ui.pages.QMessageBox.warning"):
                    excel._preview_workbook(root / "missing.xlsx")
                self.assertTrue(excel.import_period_start.isEnabled())
                self.assertFalse(excel.calculate_button.isEnabled())
                self.assertIsNone(excel._workspace)
                self.assertEqual(len(records.list_all()), 2)
            finally:
                gui._project_dirty = False
                window.close()
                window.deleteLater()
                self.app.processEvents()
