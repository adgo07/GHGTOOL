from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    DomainValidationError,
    ActivityData,
    ActivityDataSource,
    CalculationLine,
    CalculationResult,
    IssueLevel,
    ParameterSelectionMethod,
    ParameterSnapshot,
    PeriodType,
    RecordStatus,
    ValidationProblem,
)
from packages.persistence import RecordRepositoryError, SQLiteRecordRepository
from packages.standards.carbon_material import CarbonMaterialCalculator, CarbonMaterialInput, InMemoryRecordRepository
from packages.ui.pages import RecordLibraryPage
from packages.ui.view_models import AppRoute


STANDARD_ID = "gbt_32151_34_2024"
NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def _record(record_id: str, *, warning: bool = False) -> AccountingRecord:
    problem = ValidationProblem(
        "GEN-WARN-DEFAULT",
        IssueLevel.WARNING,
        "采用标准缺省值。",
        "parameter.example",
    )
    accounting_input = AccountingInput(
        input_id=f"input.{record_id}",
        standard_id=STANDARD_ID,
        period=PERIOD,
        enterprise_name="G07 示例企业",
        boundary_component_ids=("boundary.main",),
        activities=(ActivityData("activity.power", "10", "MWh", ActivityDataSource.METER),),
    )
    result = CalculationResult(
        result_id=f"result.{record_id}",
        standard_id=STANDARD_ID,
        algorithm_version="CAR-SM01-G07-TEST",
        lines=(CalculationLine(f"line.{record_id}", "source.energy", "CO2", "1.25", "tCO2"),),
        total_amount="1.25",
        total_unit="tCO2",
        calculated_at=NOW,
        problems=(problem,) if warning else (),
    )
    snapshot = ParameterSnapshot(
        snapshot_id=f"snapshot.{record_id}",
        parameter_id="parameter.example",
        factor_id="factor.example.2026",
        value_used="0.125",
        unit_used="tCO2/MWh",
        source_id="source.example",
        source_version="2026",
        selection_method=ParameterSelectionMethod.SYSTEM_RECOMMENDED,
        selection_reason="G07 测试选择理由。",
        standard_id=STANDARD_ID,
        snapshot_at=NOW,
        factor_version="2026",
        source_location="测试来源第1条",
        factor_year=2026,
    )
    return AccountingRecord(
        record_id=record_id,
        standard_id=STANDARD_ID,
        algorithm_version="CAR-SM01-G07-TEST",
        created_at=NOW,
        input_snapshot=accounting_input,
        calculation_result=result,
        status=RecordStatus.COMPLETED_WITH_WARNINGS if warning else RecordStatus.COMPLETED,
        parameter_snapshots=(snapshot,),
    )


class G07RecordRepositoryTests(unittest.TestCase):
    def test_successful_statuses_and_all_snapshots_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            complete = _record("record.complete")
            warned = _record("record.warned", warning=True)
            repository.create_with_details(
                complete,
                raw_input={"enterprise_name": "G07 示例企业", "source_judgment": "all"},
                effective_rule_set=("CAR-RULE-BASE-001", "CAR-RULE-POWER-001"),
            )
            repository.create(warned)

            self.assertEqual(repository.get(complete.record_id), complete)
            self.assertEqual(repository.get(warned.record_id), warned)
            self.assertEqual(
                tuple(record.record_id for record in repository.list_all()),
                ("record.warned", "record.complete"),
            )
            self.assertEqual(
                repository.get_raw_input_snapshot(complete.record_id),
                {"enterprise_name": "G07 示例企业", "source_judgment": "all"},
            )
            connection = sqlite3.connect(repository.path)
            try:
                row = connection.execute(
                    "SELECT parameter_snapshot_json, warnings_json, effective_rule_set_json "
                    "FROM accounting_records WHERE record_id=?",
                    (complete.record_id,),
                ).fetchone()
            finally:
                connection.close()
            self.assertIn("factor.example.2026", row[0])
            self.assertEqual(json.loads(row[1]), [])
            self.assertEqual(
                json.loads(row[2])["rule_ids"],
                ["CAR-RULE-BASE-001", "CAR-RULE-POWER-001"],
            )

    def test_failed_audit_insert_rolls_back_record_insert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            connection = sqlite3.connect(repository.path)
            try:
                connection.execute(
                    "CREATE TRIGGER reject_g07_audit AFTER INSERT ON audit_log "
                    "BEGIN SELECT RAISE(ABORT, 'forced G07 audit failure'); END"
                )
                connection.commit()
            finally:
                connection.close()
            with self.assertRaises(RecordRepositoryError):
                repository.create(_record("record.rollback"))
            connection = sqlite3.connect(repository.path)
            try:
                count = connection.execute(
                    "SELECT COUNT(*) FROM accounting_records WHERE record_id='record.rollback'"
                ).fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, 0)

    def test_soft_delete_is_audited_and_never_reuses_record_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            record = _record("record.delete")
            repository.create(record)
            self.assertTrue(repository.delete(record.record_id, actor="tester", reason="验收删除"))
            self.assertIsNone(repository.get(record.record_id))
            self.assertEqual(repository.list_all(), ())
            audit = repository.list_audit(record.record_id)
            self.assertEqual([item.action for item in audit], ["CREATE", "DELETE"])
            self.assertEqual(audit[-1].details["reason"], "验收删除")
            with self.assertRaises(DomainValidationError):
                repository.create(record)

    def test_same_input_creates_new_record_and_error_creates_none(self) -> None:
        repository = InMemoryRecordRepository()
        calculator = CarbonMaterialCalculator(record_repository=repository)
        input_value = CarbonMaterialInput(
            input_id="input.same",
            enterprise_id="enterprise.g07",
            enterprise_name="G07 计算企业",
            period=PERIOD,
            boundary_confirmed=True,
        )
        first = calculator.calculate(input_value, calculated_at=NOW)
        second = calculator.calculate(input_value, calculated_at=NOW)
        self.assertTrue(first.successful)
        self.assertTrue(second.successful)
        self.assertNotEqual(first.record.record_id, second.record.record_id)
        self.assertEqual(len(repository.list_all()), 2)

        blocked = calculator.calculate(
            CarbonMaterialInput(
                input_id="input.error",
                enterprise_id="enterprise.g07",
                enterprise_name="G07 错误企业",
                period=PERIOD,
                boundary_confirmed=False,
            ),
            calculated_at=NOW,
        )
        self.assertTrue(blocked.blocked)
        self.assertIsNone(blocked.record)
        self.assertEqual(len(repository.list_all()), 2)


    def test_calculator_writes_sqlite_record_and_full_raw_input_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            calculator = CarbonMaterialCalculator(record_repository=repository)
            input_value = CarbonMaterialInput(
                input_id="input.sqlite",
                enterprise_id="enterprise.g07",
                enterprise_name="G07 持久化企业",
                period=PERIOD,
                boundary_confirmed=True,
            )
            outcome = calculator.calculate(input_value, calculated_at=NOW)
            self.assertTrue(outcome.successful)
            self.assertIsNotNone(outcome.record)
            self.assertEqual(len(repository.list_all()), 1)
            raw = repository.get_raw_input_snapshot(outcome.record.record_id)
            self.assertEqual(raw["input_id"], "input.sqlite")
            self.assertEqual(raw["enterprise_name"], "G07 持久化企业")

class G07UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.repository = SQLiteRecordRepository(Path(self.directory.name) / "records.sqlite")
        self.repository.create(_record("record.ui.one"))
        self.repository.create(_record("record.ui.two", warning=True))
        self.window = create_main_window(
            AppConfig(records_database=Path(self.directory.name) / "records.sqlite"),
            catalog_service=CatalogQueryService.empty(),
            record_repository=self.repository,
        )
        self.window.show()
        self.application.processEvents()
        self.records_page = self.window.centralWidget().pages[AppRoute.RECORDS]
        self.home_page = self.window.centralWidget().pages[AppRoute.HOME]

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()
        self.directory.cleanup()

    def test_record_list_search_filter_and_read_only_detail(self) -> None:
        self.assertIsInstance(self.records_page, RecordLibraryPage)
        self.assertEqual(self.records_page.record_list.count(), 2)
        self.records_page.search_input.setText("G07 示例企业")
        self.application.processEvents()
        self.assertEqual(self.records_page.record_list.count(), 2)
        self.records_page.status_filter.setCurrentIndex(2)
        self.application.processEvents()
        self.assertEqual(self.records_page.record_list.count(), 1)
        self.assertTrue(self.records_page.detail_text.isReadOnly())
        self.assertIn("record.ui.two", self.records_page.detail_text.toPlainText())
        self.assertIn("G07 测试选择理由", self.records_page.detail_text.toPlainText())
        self.assertIsNotNone(self.home_page.findChild(QLabel, "bodyText"))

    def test_leaving_uncomputed_page_requires_confirmation_and_discards_input(self) -> None:
        shell = self.window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        page = shell.pages[AppRoute.NEW_ACCOUNTING]
        page.enterprise_name.setText("未计算企业")
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            shell.navigate(AppRoute.RECORDS)
        self.assertEqual(shell.current_route, AppRoute.NEW_ACCOUNTING)
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            shell.navigate(AppRoute.RECORDS)
        self.assertEqual(shell.current_route, AppRoute.RECORDS)
        self.assertEqual(page.enterprise_name.text(), "")
    def test_ui_delete_requires_confirmation_and_refreshes_active_list(self) -> None:
        self.records_page.search_input.clear()
        self.records_page.record_list.setCurrentRow(0)
        selected_id = self.records_page._records[0].record_id
        with patch(
            "packages.ui.pages.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ) as question:
            self.records_page.delete_button.click()
        question.assert_called_once()
        self.assertIsNone(self.repository.get(selected_id))
        self.assertEqual(self.records_page.record_list.count(), 1)
        self.assertEqual(self.repository.list_audit(selected_id)[-1].action, "DELETE")


if __name__ == "__main__":
    unittest.main()