"""Regression for recovering an Excel record link without changing saved navigation."""

from __future__ import annotations

from contextlib import closing
from dataclasses import replace
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
from packages.excel.templates import ExcelTemplateService
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
        self.workbook_path = self._appendix_b_workbook()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _set_import_context(self) -> None:
        self.page.import_enterprise_name.setText("待恢复关联企业")
        self.page.import_period_type.setCurrentIndex(self.page.import_period_type.findData("ANNUAL"))
        self.page.import_period_start.setText("2025-01-01")
        self.page.import_period_end.setText("2025-12-31")
        self.page.import_boundary_confirmed.setChecked(True)

    def _appendix_b_workbook(self) -> Path:
        workbook = load_workbook(BytesIO(ExcelTemplateService.default().read_bytes()))
        fuel = workbook["B.2"]
        fuel["A14"], fuel["B14"] = "天然气", 1.25
        fuel["D14"], fuel["F14"], fuel["I14"] = "计算值", "缺省值", "缺省值"
        destination = self.root / "导入工作簿.xlsx"
        workbook.save(destination)
        workbook.close()
        return destination

    def test_pending_link_recovery_preserves_legacy_r2_evidence_and_record(self) -> None:
        self._set_import_context()
        with patch("packages.ui.pages.QMessageBox.warning"):
            self.page._preview_workbook(self.workbook_path)
        preview = self.page._last_preview
        self.assertIsNotNone(preview)
        self.assertEqual(len(preview.units), 1)
        self.assertTrue(preview.units[0].can_calculate, preview.units[0].errors)
        self.assertEqual(self.records.list_all(), ())

        self.page.project_name.setText("单元关联恢复项目")
        self.page.save_project_button.click()
        self.app.processEvents()
        workspace = self.projects.list_all()[0]
        self.assertEqual(len(workspace.units), 1)
        unit = workspace.units[0]

        # A generic project JSON round-trip must keep the historical EXCEL_R2 source readable.
        legacy_provenance = dict(unit.ingress_provenance)
        legacy_provenance["source"] = "EXCEL_R2"
        legacy_workspace = replace(
            workspace,
            units=(replace(unit, ingress_provenance=legacy_provenance),),
        )
        self.projects.save(legacy_workspace)
        self.assertTrue(self.page.open_project(workspace.project_id))
        self.assertEqual(self.page._selected_unit().ingress_provenance["source"], "EXCEL_R2")
        self.assertEqual(self.records.list_all(), ())

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
        raw = self.records.get_raw_input_snapshot(record_id)
        self.assertEqual(raw["ingress_provenance"]["source"], "EXCEL_R2")

        pending_workspace = self.page._workspace
        pending_unit = pending_workspace.units[0]
        self.assertEqual(pending_unit.record_ids, (record_id,))
        self.assertEqual(pending_unit.result_snapshot["record_id"], record_id)

        with closing(sqlite3.connect(self.projects_path)) as connection:
            connection.execute("DROP TRIGGER fail_project_update")
            connection.commit()

        current_workspace = self.projects.get(workspace.project_id)
        self.assertEqual(current_workspace.active_unit_id, unit.unit_id)
        self.projects.save(current_workspace)

        recovered_service = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(self.projects_path))
        recovered = recovered_service.get(workspace.project_id)
        self.assertEqual(recovered.active_unit_id, unit.unit_id)
        recovered_unit = recovered.units[0]
        self.assertEqual(recovered_unit.record_ids, (record_id,))
        self.assertEqual(recovered_unit.result_snapshot, pending_unit.result_snapshot)
        self.assertEqual(recovered_unit.input_fingerprint, pending_unit.input_fingerprint)
        self.assertEqual(recovered_unit.canonical_input, pending_unit.canonical_input)
        self.assertEqual(recovered_unit.ingress_provenance["source"], "EXCEL_R2")
        self.assertEqual(self.records.list_all(), records_after_calculation)
        self.assertEqual(self.records.get(record_id), original_record)

        self.page.project_service = recovered_service
        self.page._refresh_saved_projects()
        self.assertTrue(self.page.open_project(workspace.project_id))
        self.assertEqual(self.page.unit_selector.currentData(), unit.unit_id)
        self.assertEqual(self.page.unit_record_selector.count(), 1)
        self.assertEqual(self.page.unit_record_selector.currentData(), record_id)
        self.assertTrue(self.page.open_record_button.isEnabled())

        requested_record_ids: list[str] = []
        self.page.record_requested.connect(requested_record_ids.append)
        self.page.open_record_button.click()
        self.assertEqual(requested_record_ids, [record_id])


if __name__ == "__main__":
    unittest.main()
