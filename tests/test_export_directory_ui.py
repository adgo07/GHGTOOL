from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import SettingEntry, Settings
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.ui import report_export
from packages.ui.export_location import ExportLocationService
from packages.ui.pages import ExcelImportPage, SettingsPage
from packages.ui.view_models import AppRoute


class MemorySettingsRepository:
    def __init__(self, entries=()):
        self.settings = Settings("user.settings", tuple(entries))

    def load(self):
        return self.settings

    def save(self, settings):
        self.settings = settings


class ExportDirectoryUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_app_config_accepts_an_existing_user_database_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            user_database = Path(directory) / "data" / "user.sqlite"
            config = AppConfig(user_database=user_database)
            self.assertEqual(config.resolved_user_database(), user_database)
            self.assertFalse(user_database.exists())

    def test_settings_page_saves_the_shared_directory_through_shell_injection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = MemorySettingsRepository(
                (SettingEntry("window.geometry", "1200x800"),)
            )
            service = ExportLocationService(
                repository,
                documents_location_provider=lambda: root / "Documents",
            )
            window = create_main_window(
                AppConfig(user_database=root / "user.sqlite"),
                catalog_service=CatalogQueryService.empty(),
                record_repository=InMemoryRecordRepository(),
                export_location_service=service,
            )
            shell = window.centralWidget()
            shell.navigate(AppRoute.SETTINGS)
            self.application.processEvents()
            page = shell.pages[AppRoute.SETTINGS]
            self.assertIsInstance(page, SettingsPage)
            self.assertEqual(
                page.export_directory_path.text(),
                str(root / "Documents" / "青舟温室气体核算" / "导出文件"),
            )

            selected = root / "用户选择的导出目录"
            with patch(
                "packages.ui.pages.QFileDialog.getExistingDirectory",
                return_value=str(selected),
            ) as dialog:
                page.choose_export_directory_button.click()

            self.assertEqual(service.display_directory(), selected)
            self.assertEqual(
                {entry.key: entry.value for entry in repository.load().entries}[
                    "window.geometry"
                ],
                "1200x800",
            )
            self.assertEqual(page.export_directory_path.text(), str(selected))
            dialog.assert_called_once()
            window.close()
            window.deleteLater()
            self.application.processEvents()

    def test_template_save_as_confirms_overwrite_and_keeps_global_setting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            global_directory = root / "GlobalExports"
            repository = MemorySettingsRepository()
            service = ExportLocationService(
                repository,
                documents_location_provider=lambda: root / "Documents",
            )
            service.set_preferred_directory(global_directory)
            page = ExcelImportPage()
            page.export_location_service = service
            alternate_directory = root / "OneOff"
            alternate_directory.mkdir()
            target = alternate_directory / "approved-copy.xlsx"
            target.write_bytes(b"previous")

            with (
                patch(
                    "packages.ui.pages.choose_export_path",
                    return_value=(str(target), "Excel 工作簿 (*.xlsx)"),
                ),
                patch(
                    "packages.ui.pages.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.No,
                ) as question,
            ):
                page.templateButton.click()

            question.assert_called_once()
            self.assertEqual(target.read_bytes(), b"previous")
            self.assertEqual(service.display_directory(), global_directory)

            with (
                patch(
                    "packages.ui.pages.choose_export_path",
                    return_value=(str(target), "Excel 工作簿 (*.xlsx)"),
                ),
                patch(
                    "packages.ui.pages.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ) as question,
                patch("packages.ui.pages.show_export_success") as success,
            ):
                page.templateButton.click()

            question.assert_called_once()
            self.assertEqual(
                target.read_bytes(),
                page.excel_adapter.templates.read_bytes(page.standard_id),
            )
            self.assertEqual(service.display_directory(), global_directory)
            self.assertEqual(success.call_args.args[-1], target)
            page.close()

    def test_word_save_as_confirms_existing_docx_and_keeps_atomic_audit_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository_settings = MemorySettingsRepository()
            service = ExportLocationService(
                repository_settings,
                documents_location_provider=lambda: root / "Documents",
            )
            global_directory = root / "GlobalExports"
            service.set_preferred_directory(global_directory)
            target = root / "alternate" / "same-name.docx"
            target.parent.mkdir()
            target.write_bytes(b"old report")

            class AuditRepository:
                def __init__(self):
                    self.entries = []

                def record_report_export(self, record_id, **values):
                    self.entries.append((record_id, values))

            audit_repository = AuditRepository()
            record = SimpleNamespace(record_id="record.export.same-name")
            parent = QWidget()
            dialog = lambda *_args: (str(target), "Word 文档 (*.docx)")
            with (
                patch.object(report_export, "report_export_filename", return_value=target.name),
                patch.object(
                    report_export,
                    "build_saved_record_report",
                    return_value=SimpleNamespace(schema_version="report-schema-1"),
                ),
                patch.object(report_export.QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as confirm,
                patch.object(report_export, "show_export_success") as success,
            ):
                cancelled = report_export.export_saved_record_report(
                    parent,
                    audit_repository,
                    record,
                    supplementary_dialog=lambda _record: {},
                    file_dialog=dialog,
                    export_location_service=service,
                    renderer=lambda _model: b"new report bytes",
                )
                self.assertFalse(cancelled)
                self.assertEqual(target.read_bytes(), b"old report")
                self.assertEqual(audit_repository.entries, [])
                confirm.assert_called_once()
                success.assert_not_called()

            with (
                patch.object(report_export, "report_export_filename", return_value=target.name),
                patch.object(
                    report_export,
                    "build_saved_record_report",
                    return_value=SimpleNamespace(schema_version="report-schema-1"),
                ),
                patch.object(report_export.QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as confirm,
                patch.object(report_export, "show_export_success") as success,
            ):
                exported = report_export.export_saved_record_report(
                    parent,
                    audit_repository,
                    record,
                    supplementary_dialog=lambda _record: {},
                    file_dialog=dialog,
                    export_location_service=service,
                    renderer=lambda _model: b"new report bytes",
                )

            self.assertTrue(exported)
            confirm.assert_called_once()
            self.assertEqual(target.read_bytes(), b"new report bytes")
            self.assertEqual(audit_repository.entries[0][0], record.record_id)
            self.assertEqual(
                audit_repository.entries[0][1]["template_version"],
                "report-schema-1",
            )
            self.assertEqual(service.display_directory(), global_directory)
            self.assertFalse(list(target.parent.glob(".ghg-report-*.tmp")))
            success.assert_called_once()
            parent.close()


if __name__ == "__main__":
    unittest.main()
