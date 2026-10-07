"""Integration checks for the real GUI ingress, SQLite records and R2 preview."""

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict
from datetime import date
from io import BytesIO
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from docx import Document
from openpyxl import load_workbook

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.reporting import build_saved_record_report
from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.excel.r2 import ExcelWorkbookImporter, create_template_bytes
from packages.persistence import SQLiteCatalogRepository, SQLiteRecordRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import EmissionSourceStatus, FuelPath, FuelType
from packages.ui.view_models import AppRoute


class MainIntegrationUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.catalog = build_catalog_database(DEFAULT_SOURCE_PATH, self.root / "catalog.sqlite")
        self.records_path = self.root / "records.sqlite"
        self.repository = SQLiteRecordRepository(self.records_path)
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog), record_repository=self.repository,
        )
        self.window.show()
        self.shell = self.window.centralWidget()
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.app.processEvents()
        self.page = self.shell.pages[AppRoute.NEW_ACCOUNTING]
        self.page.period_year.setValue(2025)
        self.page.enterprise_name.setText("集成验收企业")
        self.page.boundary_confirmed.setChecked(True)
        status = self.page._source_statuses["CAR-SRC-FUEL-001"]
        status.setCurrentIndex(status.findData(EmissionSourceStatus.INVOLVED))
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
        row.path.setCurrentIndex(row.path.findData(FuelPath.VOLUME))
        row.activity.setText("1.25")

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _workbook(self) -> Path:
        workbook = load_workbook(BytesIO(create_template_bytes()))
        basic = workbook["基本信息"]
        basic["B3"] = "集成验收企业"
        basic["B4"], basic["B5"], basic["B6"], basic["B7"] = "年度", "2025-01-01", "2025-12-31", "是"
        basic["A13"], basic["B13"], basic["C13"] = "全厂", "全厂", "是"
        fuel = workbook["B.2 化石燃料"]
        fuel["A6"], fuel["B6"], fuel["C6"], fuel["D6"] = "全厂", "天然气", "体积", 1.25
        destination = self.root / "输入.xlsx"
        workbook.save(destination)
        workbook.close()
        return destination

    def test_gui_and_excel_have_exact_results_and_preview_does_not_save(self) -> None:
        self.page.quick_calculate_button.click()
        self.app.processEvents()
        record = self.repository.list_all()[0]
        preview = ExcelWorkbookImporter(
            create_g06_parameter_resolver(SQLiteCatalogRepository(self.catalog)),
        ).import_preview(self._workbook())
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, unit.errors)
        self.assertEqual(record.calculation_result.total_amount, unit.result.total_amount)
        self.assertEqual(
            tuple((line.amount, line.unit) for line in record.calculation_result.lines),
            tuple((line.amount, line.unit) for line in unit.result.lines),
        )
        self.assertIsNone(unit.calculation.record)
        self.assertEqual(len(self.repository.list_all()), 1)
        excel_page = self.shell.pages[AppRoute.EXCEL_IMPORT]
        with patch("packages.ui.pages.QFileDialog.getOpenFileName", return_value=(str(self._workbook()), "")):
            excel_page.selectFileButton.click()
        text = excel_page.preview_text.toPlainText()
        self.assertIn("预览排放总量：", text)
        self.assertIn("tCO₂", text)
        self.assertNotIn(str(unit.result.total_amount), text)
        self.assertEqual(len(self.repository.list_all()), 1)

    def test_repeated_success_appends_and_failed_input_preserves_saved_records(self) -> None:
        self.page.quick_calculate_button.click()
        self.page.quick_calculate_button.click()
        records = self.repository.list_all()
        self.assertEqual(len(records), 2)
        self.assertNotEqual(records[0].record_id, records[1].record_id)
        originals = tuple(asdict(record) for record in records)
        self.page._fuel_rows[0].activity.setText("-1")
        self.page.quick_calculate_button.click()
        self.assertIn("未完成", self.page.calculation_status_hint.text())
        reopened = SQLiteRecordRepository(self.records_path)
        self.assertEqual(tuple(asdict(record) for record in reopened.list_all()), originals)

    def test_word_export_after_catalog_change_uses_frozen_record(self) -> None:
        self.page.quick_calculate_button.click()
        record = self.repository.list_all()[0]
        original = asdict(record)
        model = build_saved_record_report(self.repository, record)
        self.shell.navigate(AppRoute.RECORDS)
        record_page = self.shell.pages[AppRoute.RECORDS]
        self.assertTrue(record_page.open_record(record.record_id))
        destination = self.root / "核算报告.docx"
        self.catalog.rename(self.root / "catalog-unavailable.sqlite")
        with (
            patch.object(record_page, "_report_supplementary_dialog", return_value={"prepared_on": date(2026, 10, 7).isoformat()}),
            patch("packages.ui.pages.QFileDialog.getSaveFileName", return_value=(str(destination), "")),
            patch("packages.ui.pages.QMessageBox.information") as success,
            patch("packages.ui.pages.QMessageBox.critical") as failure,
        ):
            record_page.export_word_button.click()
        failure.assert_not_called()
        success.assert_called_once()
        self.assertTrue(destination.is_file())
        document = Document(destination)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("B.1", text)
        self.assertIn("B.9", text)
        self.assertEqual(asdict(self.repository.get(record.record_id)), original)
        self.assertEqual(asdict(build_saved_record_report(self.repository, record)), asdict(model))
        with closing(sqlite3.connect(self.records_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM report_export_history").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
