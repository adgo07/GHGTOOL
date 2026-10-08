"""Regression for truthful project-recovery feedback after a formal record is saved."""

from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import ProjectWorkspaceService
from packages.core.models import RecordStatus
from packages.persistence import (
    SQLiteProjectWorkspaceRepository,
    SQLiteRecordRepository,
    build_catalog_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute


class Pr35PendingMarkerFailureTests(unittest.TestCase):
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
        self.projects = ProjectWorkspaceService(
            SQLiteProjectWorkspaceRepository(self.projects_path)
        )
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
        self.page = self.window.centralWidget().pages[AppRoute.NEW_ACCOUNTING]
        self.page.enterprise_name.setText("PR35恢复状态测试企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.project_name.setText("PR35恢复状态测试项目")
        self.page.save_project_button.click()
        self.app.processEvents()
        workspaces = self.projects.list_all()
        self.assertEqual(len(workspaces), 1)
        self.workspace = workspaces[0]
        self.assertEqual(self.records.list_all(), ())

    def tearDown(self) -> None:
        self.page._project_dirty = False
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def _fail_sql(self, trigger_name: str, table: str, operation: str, message: str) -> None:
        with closing(sqlite3.connect(self.projects_path)) as connection:
            connection.execute(
                f"CREATE TRIGGER {trigger_name} BEFORE {operation} ON {table} "
                f"BEGIN SELECT RAISE(ABORT, '{message}'); END"
            )
            connection.commit()

    def _calculate_once(self) -> tuple[list[str], object]:
        created_record_ids: list[str] = []
        self.page.record_created.connect(created_record_ids.append)
        with patch("packages.ui.carbon_material_page.QMessageBox.critical") as dialog:
            self.page.calculate_button.click()
            self.app.processEvents()
        self.assertEqual(len(created_record_ids), 1)
        record_id = created_record_ids[0]
        saved_records = self.records.list_all()
        self.assertEqual(len(saved_records), 1)
        record = self.records.get(record_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertIn(
            record.status,
            {RecordStatus.COMPLETED, RecordStatus.COMPLETED_WITH_WARNINGS},
        )
        self.assertEqual(saved_records[0], record)
        dialog.assert_called_once()
        return created_record_ids, dialog.call_args.args[2]

    def test_marker_insert_failure_reports_no_recovery_marker_and_keeps_record(self) -> None:
        self._fail_sql(
            "fail_pending_marker_insert",
            "pending_record_links",
            "INSERT",
            "test marker insert failure",
        )

        created_record_ids, dialog_text = self._calculate_once()

        self.assertIn("恢复标记未写入", self.page.project_save_status.text())
        self.assertIn("恢复标记写入失败", dialog_text)
        self.assertNotIn("恢复标记已经写入", dialog_text)
        self.assertEqual(len(self.records.list_all()), 1)
        self.assertEqual(created_record_ids, [self.records.list_all()[0].record_id])
        persisted_workspace = self.projects.get(self.workspace.project_id)
        self.assertIsNotNone(persisted_workspace)
        assert persisted_workspace is not None
        self.assertNotIn(
            created_record_ids[0],
            tuple(record_id for unit in persisted_workspace.units for record_id in unit.record_ids),
        )
        with closing(sqlite3.connect(self.projects_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM pending_record_links").fetchone()[0],
                0,
            )

    def test_marker_cleanup_failure_reports_saved_link_and_retained_marker(self) -> None:
        self._fail_sql(
            "fail_pending_marker_delete",
            "pending_record_links",
            "DELETE",
            "test marker cleanup failure",
        )

        created_record_ids, dialog_text = self._calculate_once()
        record_id = created_record_ids[0]

        self.assertIn("已生成并关联到项目", self.page.project_save_status.text())
        self.assertIn("恢复标记未能清理", self.page.project_save_status.text())
        self.assertIn("项目关联已经保存", dialog_text)
        self.assertIn("标记仍待恢复流程处理", dialog_text)
        self.assertEqual(len(self.records.list_all()), 1)
        persisted_workspace = self.projects.get(self.workspace.project_id)
        self.assertIsNotNone(persisted_workspace)
        assert persisted_workspace is not None
        self.assertIn(
            record_id,
            tuple(record_id for unit in persisted_workspace.units for record_id in unit.record_ids),
        )
        with closing(sqlite3.connect(self.projects_path)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM pending_record_links WHERE record_id=?",
                    (record_id,),
                ).fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()
