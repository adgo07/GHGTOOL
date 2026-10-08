"""Regression for recovering an Excel record link without changing saved navigation."""

from __future__ import annotations

from contextlib import closing
from io import BytesIO
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
from packages.application import ProjectWorkspaceService
from packages.core.models import RecordStatus
from packages.excel.r2 import create_template_bytes
from packages.persistence import (
    SQLiteProjectWorkspaceRepository,
    SQLiteRecordRepository,
    build_catalog_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute


class Rs03PendingLinkRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        catalog_path = build_catalog_database(DEFAULT_SOURCE_PATH, self.root / "catalog.sqlite")
        self.records_path = self.root / "records.sqlite"
        self.projects_path = self.root / "projects.sqlite"
        self.records = SQLiteRecordRepository(self.records_path)
        self.projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(self.projects_path))
        self.window = create_main_window(
            AppConfig(
                catalog_database=catalog_path,
                records_database=self.records_path,
                projects_database=self.projects_path,
            ),
            record_repository=self.records,
            project_service=self.projects,
        )
        self.window.show()
        self.app.processEvents()
        self.shell = self.window.centralWidget()
        self.page = self.shell.pages[AppRoute.EXCEL_IMPORT]
        self.workbook_path = self._two_valid_unit_workbook()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _two_valid_unit_workbook(self) -> Path:
        workbook = load_workbook(BytesIO(create_template_bytes()))
        basic = workbook["基本信息"]
        basic["B3"] = "待恢复关联企业"
        basic["B4"] = "年度"
        basic["B5"] = "2025-01-01"
        basic["B6"] = "2025-12-31"
        basic["B7"] = "是"
        basic["A13"], basic["B13"], basic["C13"] = "一号单元", "全厂", "是"
        basic["A14"], basic["B14"], basic["C14"] = "二号单元", "工序", "是"
        fuel = workbook["B.2 化石燃料"]
        fuel["A6"], fuel["B6"], fuel["C6"], fuel["D6"] = "一号单元", "天然气", "体积", 1.25
        fuel["E6"], fuel["F6"] = "生产/能源台账", "来源-A"
        fuel["A7"], fuel["B7"], fuel["C7"], fuel["D7"] = "二号单元", "天然气", "体积", 2.75
        fuel["E7"], fuel["F7"] = "生产/能源台账", "来源-B"
        destination = self.root / "双单元导入.xlsx"
        workbook.save(destination)
        workbook.close()
        return destination

    def test_recovery_keeps_saved_u1_active_and_restores_u2_record_for_selection(self) -> None:
        with patch("packages.ui.pages.QMessageBox.warning"):
            self.page._preview_workbook(self.workbook_path)
        preview = self.page._last_preview
        self.assertIsNotNone(preview)
        self.assertEqual(len(preview.units), 2)
        self.assertTrue(all(unit.can_calculate for unit in preview.units))

        self.page.project_name.setText("双单元关联恢复项目")
        self.page.save_project_button.click()
        self.app.processEvents()
        workspace = self.projects.list_all()[0]
        units_by_name = {unit.name: unit for unit in workspace.units}
        u1 = units_by_name["一号单元"]
        u2 = units_by_name["二号单元"]
        self.assertEqual(workspace.active_unit_id, u1.unit_id)
        self.assertEqual(self.records.list_all(), ())
        self.assertTrue(self.page.open_project(workspace.project_id))

        u2_index = self.page.unit_selector.findData(u2.unit_id)
        self.assertGreaterEqual(u2_index, 0)
        self.page.unit_selector.setCurrentIndex(u2_index)
        self.app.processEvents()
        self.assertEqual(self.page._selected_unit().unit_id, u2.unit_id)

        with closing(sqlite3.connect(self.projects_path)) as connection:
            connection.execute(
                "CREATE TRIGGER fail_project_update BEFORE UPDATE ON projects "
                "BEGIN SELECT RAISE(ABORT, 'test project write failure'); END"
            )
            connection.commit()

        created_record_ids: list[str] = []
        self.page.record_created.connect(created_record_ids.append)
        with patch("packages.ui.pages.QMessageBox.warning"):
            self.page.calculate_button.click()
            self.app.processEvents()
        self.assertIn("项目关联失败", self.page.status_label.text())
        self.assertEqual(len(created_record_ids), 1)
        record_id = created_record_ids[0]
        records_after_calculation = self.records.list_all()
        self.assertEqual(len(records_after_calculation), 1)
        original_record = self.records.get(record_id)
        self.assertIsNotNone(original_record)
        self.assertIn(original_record.status, {RecordStatus.COMPLETED, RecordStatus.COMPLETED_WITH_WARNINGS})

        pending_workspace = self.page._workspace
        self.assertEqual(pending_workspace.active_unit_id, u2.unit_id)
        pending_u2 = next(unit for unit in pending_workspace.units if unit.unit_id == u2.unit_id)
        self.assertEqual(pending_u2.record_ids, (record_id,))
        self.assertEqual(pending_u2.result_snapshot["record_id"], record_id)

        with closing(sqlite3.connect(self.projects_path)) as connection:
            connection.execute("DROP TRIGGER fail_project_update")
            connection.commit()

        # This later explicit save records the user's still-current U1 selection.
        current_workspace = self.projects.get(workspace.project_id)
        self.assertEqual(current_workspace.active_unit_id, u1.unit_id)
        self.projects.save(current_workspace)

        recovered_service = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(self.projects_path))
        recovered = recovered_service.get(workspace.project_id)
        self.assertEqual(recovered.active_unit_id, u1.unit_id)
        recovered_units = {unit.unit_id: unit for unit in recovered.units}
        self.assertEqual(recovered_units[u1.unit_id].record_ids, ())
        self.assertEqual(recovered_units[u2.unit_id].record_ids, (record_id,))
        self.assertEqual(recovered_units[u2.unit_id].result_snapshot, pending_u2.result_snapshot)
        self.assertEqual(recovered_units[u2.unit_id].input_fingerprint, pending_u2.input_fingerprint)
        self.assertEqual(recovered_units[u2.unit_id].canonical_input, pending_u2.canonical_input)
        self.assertEqual(recovered_units[u2.unit_id].ingress_provenance, pending_u2.ingress_provenance)
        self.assertEqual(self.records.list_all(), records_after_calculation)
        self.assertEqual(self.records.get(record_id), original_record)

        # Reopening selects the saved U1, while U2 and its frozen Record remain available.
        self.page.project_service = recovered_service
        self.page._refresh_saved_projects()
        self.assertTrue(self.page.open_project(workspace.project_id))
        self.assertEqual(self.page.unit_selector.currentData(), u1.unit_id)
        recovered_u2_index = self.page.unit_selector.findData(u2.unit_id)
        self.assertGreaterEqual(recovered_u2_index, 0)
        self.page.unit_selector.setCurrentIndex(recovered_u2_index)
        self.app.processEvents()
        self.assertEqual(self.page._selected_unit().unit_id, u2.unit_id)
        self.assertIn("二号单元", self.page.preview_text.toPlainText())
        self.assertEqual(self.page.unit_record_selector.count(), 1)
        self.assertEqual(self.page.unit_record_selector.currentData(), record_id)
        self.assertTrue(self.page.open_record_button.isEnabled())

        requested_record_ids: list[str] = []
        self.page.record_requested.connect(requested_record_ids.append)
        self.page.open_record_button.click()
        self.assertEqual(requested_record_ids, [record_id])


if __name__ == "__main__":
    unittest.main()
