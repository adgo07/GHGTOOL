"""Integration checks for the RS03 Excel preview and frozen-record export entrypoints."""

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict
from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from openpyxl import load_workbook

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.carbon_accounting import (
    CarbonAccountingPreviewUseCase,
    create_g06_parameter_resolver,
)
from packages.application.reporting import build_saved_record_report
from packages.excel.r2 import ExcelWorkbookImporter, create_template_bytes
from packages.persistence import (
    SQLiteCatalogRepository,
    SQLiteRecordRepository,
    build_catalog_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute


FIXED_CALCULATED_AT = datetime(2024, 12, 31, 12, 34, 56, tzinfo=timezone.utc)
SNAPSHOT_GETTERS = {
    "raw_input": "get_raw_input_snapshot",
    "effective_rule_set": "get_effective_rule_set",
    "trace": "get_trace_snapshot",
    "provenance": "get_provenance_snapshot",
    "reporting": "get_reporting_snapshot",
    "qualification": "get_report_qualification",
}


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_CALCULATED_AT if tz is not None else FIXED_CALCULATED_AT.replace(tzinfo=None)


class Rs03ExcelEntrypointTests(unittest.TestCase):
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
            AppConfig(
                catalog_database=self.catalog,
                records_database=self.records_path,
                projects_database=self.root / "projects.sqlite",
            ),
            record_repository=self.repository,
        )
        self.window.show()
        self.shell = self.window.centralWidget()
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.app.processEvents()
        self.page = self.shell.pages[AppRoute.NEW_ACCOUNTING]
        self.page.period_year.setValue(2025)
        self.page.enterprise_name.setText("RS03 集成验收企业")
        self.page.boundary_confirmed.setChecked(True)
        status = self.page._source_statuses["CAR-SRC-FUEL-001"]
        status.setCurrentIndex(status.findData("INVOLVED"))
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData("NATURAL_GAS"))
        row.path.setCurrentIndex(row.path.findData("VOLUME"))
        row.activity.setText("1.25")

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _workbook(self, year: int = 2025) -> Path:
        workbook = load_workbook(BytesIO(create_template_bytes()))
        basic = workbook["基本信息"]
        basic["B3"] = "RS03 集成验收企业"
        basic["B4"] = "年度"
        basic["B5"] = f"{year}-01-01"
        basic["B6"] = f"{year}-12-31"
        basic["B7"] = "是"
        basic["A13"], basic["B13"], basic["C13"] = "全厂", "全厂", "是"
        fuel = workbook["B.2 化石燃料"]
        fuel["A6"], fuel["B6"], fuel["C6"], fuel["D6"] = "全厂", "天然气", "体积", 1.25
        destination = self.root / f"输入-{year}.xlsx"
        workbook.save(destination)
        workbook.close()
        return destination

    def _record_page(self, record_id: str):
        self.shell.navigate(AppRoute.RECORDS)
        self.app.processEvents()
        page = self.shell.pages[AppRoute.RECORDS]
        self.assertTrue(page.open_record(record_id))
        return page

    def _create_record(self):
        self.page.quick_calculate_button.click()
        self.app.processEvents()
        records = self.repository.list_all()
        self.assertEqual(len(records), 1)
        return records[0]

    def _frozen_state(self, record_id: str) -> dict[str, object]:
        record = self.repository.get(record_id)
        return {
            "record": asdict(record),
            **{
                key: getattr(self.repository, getter)(record_id)
                for key, getter in SNAPSHOT_GETTERS.items()
            },
        }

    @staticmethod
    def _visible_values(workbook) -> set[str]:
        return {
            str(cell.value)
            for sheet in workbook.worksheets
            if sheet.sheet_state == "visible"
            for row in sheet.iter_rows()
            for cell in row
            if cell.value is not None
        }

    def _assert_report_model_cells(self, workbook, report) -> None:
        basic = workbook["基本信息"]
        self.assertEqual(basic["A1"].value, report.standard_name)
        self.assertEqual(basic["B2"].value, report.standard_version)
        self.assertEqual(basic["B3"].value, report.period_text)
        self.assertEqual(basic["B4"].value, report.prepared_on)
        for offset, (label, value) in enumerate(report.basic_information, start=8):
            self.assertEqual(basic.cell(offset, 1).value, label)
            actual = basic.cell(offset, 2).value
            self.assertEqual("" if actual is None else str(actual), "" if value is None else str(value))

        visible = self._visible_values(workbook)
        for value in (*report.notices, report.supplementary_note):
            if value:
                self.assertIn(str(value), visible)

        for section in report.sections:
            if section.section_id == "basic":
                sheet = basic
                self.assertEqual(sheet["A6"].value, section.title)
            else:
                if section.section_id == "evidence":
                    sheet = workbook["数据来源"]
                else:
                    matching_sheets = [
                        candidate for candidate in workbook.worksheets
                        if candidate.sheet_state == "visible" and candidate["A1"].value == section.title
                    ]
                    self.assertEqual(len(matching_sheets), 1, section.title)
                    sheet = matching_sheets[0]
            sheet_values = {
                str(cell.value)
                for row in sheet.iter_rows()
                for cell in row
                if cell.value is not None
            }
            for note in section.notes:
                self.assertIn(note, sheet_values)

            for table in section.tables:
                basic_rows = tuple((
                    row.cells[0].value if len(row.cells) > 0 else "",
                    row.cells[1].value if len(row.cells) > 1 else "",
                ) for row in table.rows)
                is_basic_information_table = (
                    section.section_id == "basic"
                    and tuple(table.columns) == ("项目", "内容")
                    and not any(row.note is not None for row in table.rows)
                    and basic_rows == report.basic_information
                )
                if is_basic_information_table:
                    continue

                source_columns = max([len(table.columns), *(len(row.cells) for row in table.rows), 0])
                has_details = any(cell.unit or cell.source for row in table.rows for cell in row.cells)
                has_notes = any(row.note is not None for row in table.rows)
                headers = [
                    table.columns[index] if index < len(table.columns) else f"未标注列{index + 1}"
                    for index in range(source_columns)
                ]
                if has_details:
                    headers.append("单位与来源说明")
                if has_notes:
                    headers.append("行内说明")
                if not headers:
                    headers.append("内容")
                title_rows = [
                    row_number
                    for row_number in range(1, sheet.max_row)
                    if sheet.cell(row_number, 1).value == table.title
                    and tuple(sheet.cell(row_number + 1, column).value for column in range(1, len(headers) + 1))
                    == tuple(headers)
                ]
                self.assertEqual(len(title_rows), 1, table.title)
                first_data_row = title_rows[0] + 2
                for row_offset, row in enumerate(table.rows):
                    output_row = first_data_row + row_offset
                    for column in range(source_columns):
                        expected = row.cells[column].value if column < len(row.cells) else None
                        actual = sheet.cell(output_row, column + 1).value
                        self.assertEqual("" if actual is None else str(actual), "" if expected is None else str(expected))

                    if has_details:
                        details = []
                        for index, cell in enumerate(row.cells):
                            parts = []
                            if cell.unit:
                                parts.append(f"单位：{cell.unit}")
                            if cell.source:
                                parts.append(f"来源：{cell.source}")
                            if parts:
                                label = table.columns[index] if index < len(table.columns) else f"未标注列{index + 1}"
                                details.append(f"{label}：{'；'.join(parts)}")
                        expected_details = "\n".join(details)
                        actual_details = sheet.cell(output_row, source_columns + 1).value
                        self.assertEqual("" if actual_details is None else actual_details, expected_details)

                    if has_notes:
                        note_column = source_columns + 1 + int(has_details)
                        actual_note = sheet.cell(output_row, note_column).value
                        self.assertEqual("" if actual_note is None else actual_note, row.note or "")

    def test_gui_preview_matches_formal_calculator_metadata_and_never_persists(self) -> None:
        workbook = self._workbook(year=2024)
        self.assertEqual(self.repository.list_all(), ())
        self.shell.navigate(AppRoute.EXCEL_IMPORT)
        self.app.processEvents()
        page = self.shell.pages[AppRoute.EXCEL_IMPORT]
        self.assertIs(page.calculation_use_case, self.page.calculation_use_case)
        self.assertIs(page.calculation_use_case.calculator, self.page.calculation_use_case.calculator)

        with (
            patch("packages.excel.r2.datetime", _FixedDateTime),
            patch("packages.ui.pages.QFileDialog.getOpenFileName", return_value=(str(workbook), "")),
        ):
            page.selectFileButton.click()
            self.app.processEvents()

        preview = page._last_preview
        self.assertIsNotNone(preview)
        self.assertEqual(len(preview.units), 1)
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, unit.errors)
        self.assertIsNotNone(unit.calculation)
        actual = unit.calculation
        self.assertIsNone(actual.record)
        self.assertEqual(preview.provenance.imported_at, FIXED_CALCULATED_AT)
        self.assertEqual(actual.result.calculated_at, FIXED_CALCULATED_AT)

        calculator = self.page.calculation_use_case.calculator
        expected = calculator.calculate(unit.input_value, calculated_at=FIXED_CALCULATED_AT)
        self.assertEqual(asdict(actual), asdict(expected))
        self.assertEqual(actual.evidence.standard_version, calculator.standard_version)
        self.assertTrue(actual.parameter_snapshots)
        warning_codes = {
            problem.code for problem in actual.problems
            if getattr(problem.level, "value", problem.level) == "WARNING"
        }
        self.assertIn("CAR-VAL-STANDARD-IMPLEMENTATION-PERIOD", warning_codes)
        self.assertIn("CAR-VAL-STANDARD-IMPLEMENTATION-PERIOD", {message.code for message in unit.warnings})
        provenance = json.loads(actual.evidence.provenance_snapshot_json)
        expected_identity = calculator.reference_data_identity_provider()
        self.assertEqual(provenance["reference_data"], {"status": "CAPTURED", **expected_identity})
        self.assertEqual(self.repository.list_all(), ())

    def test_r2_importer_uses_preview_calculators_resolver_and_rejects_a_different_one(self) -> None:
        calculator = self.page.calculation_use_case.calculator
        preview_use_case = CarbonAccountingPreviewUseCase(calculator)
        resolver = calculator.parameter_resolver
        importer = ExcelWorkbookImporter(resolver, preview_use_case=preview_use_case)
        self.assertIs(importer.preview_use_case, preview_use_case)
        self.assertIs(importer.parameter_resolver, resolver)
        self.assertIs(importer.preview_use_case.calculator.parameter_resolver, resolver)

        preview = importer.import_preview(self._workbook())
        self.assertTrue(preview.units[0].can_calculate, preview.units[0].errors)
        self.assertTrue(preview.units[0].calculation.parameter_snapshots)
        self.assertEqual(self.repository.list_all(), ())

        different_resolver = create_g06_parameter_resolver(SQLiteCatalogRepository(self.catalog))
        self.assertIsNot(different_resolver, resolver)
        with self.assertRaisesRegex(ValueError, "必须使用同一参数选择服务"):
            ExcelWorkbookImporter(different_resolver, preview_use_case=preview_use_case)

    def test_excel_export_reads_only_frozen_record_after_catalog_is_unavailable(self) -> None:
        record = self._create_record()
        record_before = self._frozen_state(record.record_id)
        supplementary = {
            "prepared_on": date(2026, 10, 7).isoformat(),
            "supplementary_note": "RS03 历史记录导出验证",
        }
        report_before = build_saved_record_report(
            self.repository,
            record,
            supplementary_info=supplementary,
        )
        self._record_page(record.record_id)
        page = self.shell.pages[AppRoute.RECORDS]
        destination = self.root / "历史核算报告.xlsx"
        archived_catalog = self.root / "catalog-unavailable.sqlite"
        self.catalog.rename(archived_catalog)

        with (
            patch.object(page, "_report_supplementary_dialog", return_value=supplementary),
            patch("packages.ui.pages.QFileDialog.getSaveFileName", return_value=(str(destination), "")),
            patch("packages.ui.pages.QMessageBox.information") as success,
            patch("packages.ui.pages.QMessageBox.critical") as failure,
        ):
            page.export_excel_button.click()
            self.app.processEvents()

        failure.assert_not_called()
        success.assert_called_once()
        self.assertTrue(destination.is_file())
        self.assertFalse(self.catalog.exists())
        self.assertTrue(archived_catalog.exists())
        report_after = build_saved_record_report(
            self.repository,
            self.repository.get(record.record_id),
            supplementary_info=supplementary,
        )
        self.assertEqual(asdict(report_after), asdict(report_before))

        workbook = load_workbook(BytesIO(destination.read_bytes()), data_only=False)
        self._assert_report_model_cells(workbook, report_before)
        workbook.close()

        with closing(sqlite3.connect(self.records_path)) as connection:
            history = connection.execute(
                "SELECT format, document_sha256 FROM report_export_history WHERE record_id = ?",
                (record.record_id,),
            ).fetchall()
            audit = connection.execute(
                "SELECT action, details_json FROM audit_log WHERE record_id = ? AND action = 'REPORT_EXPORT'",
                (record.record_id,),
            ).fetchall()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][0], "XLSX")
        digest = sha256(destination.read_bytes()).hexdigest().upper()
        self.assertEqual(history[0][1], digest)
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0][0], "REPORT_EXPORT")
        self.assertEqual(json.loads(audit[0][1])["document_sha256"], digest)
        self.assertEqual(self._frozen_state(record.record_id), record_before)

    def test_excel_export_file_failure_shows_failure_without_success_popup_or_audit(self) -> None:
        record = self._create_record()
        before = self._frozen_state(record.record_id)
        page = self._record_page(record.record_id)
        destination = self.root / "missing-parent" / "未写入报告.xlsx"
        self.assertFalse(destination.parent.exists())

        with (
            patch.object(page, "_report_supplementary_dialog", return_value={"prepared_on": "2026-10-07"}),
            patch("packages.ui.pages.QFileDialog.getSaveFileName", return_value=(str(destination), "")),
            patch("packages.ui.pages.QMessageBox.information") as success,
            patch("packages.ui.pages.QMessageBox.critical") as failure,
        ):
            page.export_excel_button.click()
            self.app.processEvents()

        success.assert_not_called()
        failure.assert_called_once()
        self.assertIn("无法生成 Excel 核算报告", failure.call_args.args[2])
        self.assertFalse(destination.exists())
        self.assertFalse(destination.parent.exists())
        with closing(sqlite3.connect(self.records_path)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM report_export_history WHERE record_id = ?",
                    (record.record_id,),
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM audit_log WHERE record_id = ? AND action = 'REPORT_EXPORT'",
                    (record.record_id,),
                ).fetchone()[0],
                0,
            )
        self.assertEqual(self._frozen_state(record.record_id), before)


if __name__ == "__main__":
    unittest.main()
