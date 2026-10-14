"""P3-C Presentation acceptance: navigation, full list and immutable actions."""
from __future__ import annotations

from dataclasses import asdict, replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
)

from packages.persistence import SQLiteRecordRepository
from packages.ui.pages import RecordLibraryPage
from scripts.rpt02_acceptance_samples import build_acceptance_case
from tests.test_g07_records import _record


def _business_table(page, table_id: str, *, summary: bool = False) -> QTableWidget:
    pane = page.summary_view if summary else page.input_basis_view
    return next(
        card.table_widget
        for card in pane.report_table_cards
        if card.table_widget.property("reportTableId") == table_id
    )


def _table_text(table: QTableWidget) -> str:
    return "\n".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )


class P3CRecordUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repo = SQLiteRecordRepository(Path(self.directory.name) / "records.sqlite")
        self.repo.create(_record("p3c.one"))
        self.repo.create(_record("p3c.two", warning=True))
        self.page = RecordLibraryPage(self.repo)
        self.page.resize(1000, 760)
        self.page.show()
        self.app.processEvents()

    def tearDown(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def test_list_opens_independent_detail_with_two_continuous_tabs(self):
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)
        self.assertEqual(
            [self.page.record_list.horizontalHeaderItem(column).text()
             for column in range(self.page.record_list.columnCount())],
            ["企业 / 项目", "核算期间", "标准", "排放总量", "状态", "日期", "操作"],
        )
        self.page.search_input.setText("p3c.two")
        self.page.record_list.cellWidget(self.page.record_list.currentRow(), 6).click()
        self.assertIs(self.page.view_stack.currentWidget(), self.page.detail_view)
        self.assertEqual([self.page.detail_tabs.tabText(i) for i in range(2)],
                         ["基本信息与结果", "输入数据与计算依据"])
        self.assertEqual(self.page.detail_tabs.count(), 2)
        self.assertEqual(len(self.page.findChildren(QTabWidget)), 1)
        self.assertTrue(self.page.input_basis_view.isReadOnly())
        self.assertIsNone(self.page.findChild(QPushButton, "openRecordAuditButton"))
        self.assertIsNone(self.page.findChild(QDialog, "recordAuditDialog"))
        self.page.back_to_records_button.click()
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)
        self.assertEqual(self.page.search_input.text(), "p3c.two")
        self.assertEqual(self.page.record_list.rowCount(), 1)

    def test_all_126_records_are_accessible_and_keyboard_opens_last(self):
        for index in range(124):
            base = _record(f"p3c.more.{index:03}")
            self.repo.create(replace(base, input_snapshot=replace(
                base.input_snapshot, enterprise_name=f"列表演示企业 {index:03}")))
        self.page.refresh_records()
        self.assertEqual(self.page.record_list.rowCount(), 126)
        self.assertIn("共 126 条", self.page.result_count.text())
        self.page.record_list.setFocus()
        QTest.keyClick(
            self.page.record_list,
            Qt.Key.Key_End,
            Qt.KeyboardModifier.ControlModifier,
        )
        self.assertEqual(self.page.record_list.currentRow(), 125)
        selected = self.page._records[-1]
        QTest.keyClick(self.page.record_list, Qt.Key.Key_Return)
        self.assertIs(self.page.view_stack.currentWidget(), self.page.detail_view)
        self.assertEqual(self.page._detail_record_id, selected.record_id)
        self.page.back_to_records_button.click()
        self.page.search_input.setText("p3c.more.123")
        self.assertEqual(self.page.record_list.rowCount(), 1)
        self.page.search_input.clear()
        self.assertEqual(self.page.record_list.rowCount(), 126)

    def test_display_standard_and_period_search_status_and_empty_results(self):
        self.page.search_input.setText("GB/T 32151.34")
        self.assertEqual(self.page.record_list.rowCount(), 2)
        self.page.search_input.setText("2025年度")
        self.assertEqual(self.page.record_list.rowCount(), 2)
        self.page.status_filter.setCurrentIndex(2)
        self.assertEqual(self.page.record_list.rowCount(), 1)
        self.page.search_input.setText("不存在的企业")
        self.assertEqual(self.page.record_list.rowCount(), 1)
        self.assertEqual(len(self.page._records), 0)
        self.assertFalse(self.page.export_word_button.isEnabled())
        self.assertFalse(self.page.open_record("missing-record"))
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)

    def test_frozen_basis_is_complete_and_viewing_does_not_write(self):
        record, raw, trace, provenance, reporting, qualification = build_acceptance_case("GUI")
        reporting = dict(reporting)
        reporting["activity_evidence"] = [{
            "source_ids": ["CAR-SRC-FUEL-001"],
            "source_reference": "燃料计量台账-001",
            "monitoring_method": "计量器具",
            "recording_frequency": "连续记录",
            "note": "验收演示证据",
        }]
        self.repo.create_with_details(
            record, raw_input=raw, trace_snapshot=trace, provenance_snapshot=provenance,
            reporting_snapshot=reporting, report_qualification=qualification)
        before = (asdict(self.repo.get(record.record_id)), self.repo.get_raw_input_snapshot(record.record_id),
                  self.repo.get_trace_snapshot(record.record_id), self.repo.get_provenance_snapshot(record.record_id),
                  self.repo.list_audit(record.record_id))
        with patch.object(self.repo, "list_audit", side_effect=AssertionError("No audit-log UI")), patch(
            "packages.standards.carbon_material.CarbonMaterialCalculator.calculate",
            side_effect=AssertionError("No historical recalculation")):
            self.assertTrue(self.page.open_record(record.record_id))
        self.assertEqual(
            {card.table_widget.property("reportTableId") for card in self.page.summary_view.report_table_cards},
            {"basic-info", "b1"},
        )
        detail_ids = {
            card.table_widget.property("reportTableId")
            for card in self.page.input_basis_view.report_table_cards
        }
        self.assertTrue({
            "b2", "b3-1", "b3-2", "b4-1", "b5-1", "b6", "b7", "b8", "b9", "evidence-register",
        }.issubset(detail_ids))
        detail_titles = "\n".join(
            label.text() for label in self.page.input_basis_view.findChildren(type(self.page.detail_heading))
            if label.objectName() == "recordReportSectionTitle"
        )
        for section in ("B.2", "B.3", "B.4", "B.5", "B.6", "B.7", "B.8", "B.9", "数据来源及支撑信息"):
            self.assertIn(section, detail_titles)
        b2 = _business_table(self.page, "b2")
        self.assertEqual(b2.editTriggers(), QAbstractItemView.EditTrigger.NoEditTriggers)
        self.assertEqual(b2.rowSpan(0, 0), 2)
        self.assertEqual(b2.columnSpan(0, 1), 2)
        self.assertNotIn("来源定位：", _table_text(b2))
        evidence = _business_table(self.page, "evidence-register")
        self.assertIn("燃料计量台账-001", _table_text(evidence))
        self.assertTrue(self.page.input_basis_view.audit_panel.isHidden())
        self.assertNotIn("审计日志：", self.page.input_basis_view.audit_text.toPlainText())
        self.assertNotIn("'formula_steps':", self.page.input_basis_view.audit_text.toPlainText())
        self.assertNotIn("instance_id", self.page.input_basis_view.audit_text.toPlainText())
        self.assertNotIn("其他信息（gtafc）", _table_text(_business_table(self.page, "b2")))
        first_tab_text = _table_text(_business_table(self.page, "b1", summary=True))
        self.assertIn("7.30", first_tab_text)
        self.assertIn("9.70", first_tab_text)
        self.page.input_basis_view.audit_toggle.click()
        self.assertFalse(self.page.input_basis_view.audit_panel.isHidden())
        self.assertGreater(self.page.input_basis_view.audit_table.rowCount(), 0)
        self.assertIn("来源定位：", _table_text(self.page.input_basis_view.audit_table))
        after = (asdict(self.repo.get(record.record_id)), self.repo.get_raw_input_snapshot(record.record_id),
                 self.repo.get_trace_snapshot(record.record_id), self.repo.get_provenance_snapshot(record.record_id),
                 self.repo.list_audit(record.record_id))
        self.assertEqual(before, after)

    def test_corrupt_trace_is_explicit_and_does_not_prevent_saved_inputs(self):
        with patch.object(self.repo, "get_trace_snapshot", side_effect=ValueError("corrupt")):
            self.assertTrue(self.page.open_record("p3c.one"))
        self.assertIn("无法读取该历史信息", self.page.input_basis_view.audit_text.toPlainText())
        self.assertIn("G07 测试选择理由", self.page.input_basis_view.audit_text.toPlainText())

    def test_export_is_bound_to_loaded_detail_and_uses_public_helper(self):
        self.assertTrue(self.page.open_record("p3c.one"))
        other = next(i for i, record in enumerate(self.page._records) if record.record_id == "p3c.two")
        self.page.record_list.setCurrentCell(other, 0)
        with patch("packages.ui.pages.export_saved_record_report") as exporter:
            self.page.export_word_button.click()
        self.assertEqual(exporter.call_args.args[2].record_id, "p3c.one")
        self.page.back_to_records_button.click()
        with patch("packages.ui.pages.export_saved_record_report") as exporter:
            self.page.export_word_button.click()
        exporter.assert_not_called()

    def test_delete_cancel_preserves_record_and_confirm_keeps_audit(self):
        self.page.open_record("p3c.one")
        audit = self.repo.list_audit("p3c.one")
        with patch("packages.ui.pages.QMessageBox.question", return_value=QMessageBox.StandardButton.No):
            self.page.delete_button.click()
        self.assertIsNotNone(self.repo.get("p3c.one"))
        self.assertEqual(self.repo.list_audit("p3c.one"), audit)
        with patch("packages.ui.pages.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes):
            self.page.delete_button.click()
        self.assertIsNone(self.repo.get("p3c.one"))
        self.assertEqual(self.repo.list_audit("p3c.one")[-1].action, "DELETE")
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)

    def test_external_deleted_detail_returns_to_list(self):
        self.page.open_record("p3c.one")
        self.repo.delete("p3c.one", actor="test", reason="external deletion")
        self.page.refresh_records()
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)
        self.assertIsNone(self.page._detail_record_id)


if __name__ == "__main__":
    unittest.main()
