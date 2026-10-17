from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

from packages.core.models import SettingEntry, Settings
from packages.ui.export_location import (
    EXPORT_DIRECTORY_SETTING_KEY,
    ExportLocationService,
    choose_export_path,
    report_export_filename,
    sanitize_filename_component,
    template_export_filename,
)


class MemorySettingsRepository:
    def __init__(self, entries=()):
        self.settings = Settings("user.settings", tuple(entries))

    def load(self):
        return self.settings

    def save(self, settings):
        self.settings = settings


class ExportLocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_default_uses_system_documents_and_creates_folder_on_export_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            documents = Path(directory) / "Documents"
            service = ExportLocationService(
                documents_location_provider=lambda: documents,
            )

            self.assertEqual(
                service.display_directory(),
                documents / "青舟温室气体核算" / "导出文件",
            )
            self.assertFalse(service.display_directory().exists())
            target = service.prepare_dialog_path("附录B模板_2.0.0.xlsx")

            self.assertEqual(
                target,
                documents / "青舟温室气体核算" / "导出文件" / "附录B模板_2.0.0.xlsx",
            )
            self.assertTrue(target.parent.is_dir())

    def test_default_directory_does_not_depend_on_the_process_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_cwd = root / "first"
            second_cwd = root / "second"
            first_cwd.mkdir()
            second_cwd.mkdir()
            documents = root / "Documents"
            service = ExportLocationService(documents_location_provider=lambda: documents)
            original_cwd = Path.cwd()
            try:
                os.chdir(first_cwd)
                first = service.display_directory()
                os.chdir(second_cwd)
                second = service.display_directory()
            finally:
                os.chdir(original_cwd)

            expected = documents / "青舟温室气体核算" / "导出文件"
            self.assertEqual(first, expected)
            self.assertEqual(second, expected)
            self.assertFalse(expected.exists())

    def test_template_filename_includes_template_version(self):
        self.assertEqual(
            template_export_filename("GB/T 32151.34—2024", "2.0.0"),
            "GB_T 32151.34—2024_附录B输入模板_v2.0.0.xlsx",
        )

    def test_shared_save_dialog_uses_default_path_and_leaves_overwrite_to_caller(self):
        parent = QWidget()
        with tempfile.TemporaryDirectory() as directory:
            documents = Path(directory) / "Documents"
            service = ExportLocationService(
                documents_location_provider=lambda: documents,
            )
            selected = str(Path(directory) / "chosen.docx")
            with patch(
                "packages.ui.export_location.QFileDialog.getSaveFileName",
                return_value=(selected, "Word 文档 (*.docx)"),
            ) as dialog:
                result = choose_export_path(
                    parent,
                    "保存报告",
                    "报告.docx",
                    "Word 文档 (*.docx)",
                    location_service=service,
                )

            self.assertEqual(result[0], selected)
            self.assertEqual(
                dialog.call_args.args[2],
                str(documents / "青舟温室气体核算" / "导出文件" / "报告.docx"),
            )
            self.assertEqual(
                dialog.call_args.kwargs["options"],
                QFileDialog.Option.DontConfirmOverwrite,
            )
        parent.close()

    def test_setting_is_saved_with_other_user_settings_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = MemorySettingsRepository((SettingEntry("window.geometry", "800x600"),))
            service = ExportLocationService(
                repo,
                documents_location_provider=lambda: Path(directory) / "Documents",
            )
            chosen = Path(directory) / "Exports"

            self.assertEqual(service.set_preferred_directory(chosen), chosen)
            loaded = {entry.key: entry.value for entry in repo.load().entries}
            self.assertEqual(loaded["window.geometry"], "800x600")
            self.assertEqual(loaded[EXPORT_DIRECTORY_SETTING_KEY], str(chosen))
            self.assertEqual(service.display_directory(), chosen)

    def test_permission_failure_warns_and_requires_file_dialog_selection(self):
        parent = QWidget()
        with tempfile.TemporaryDirectory() as directory:
            documents = Path(directory) / "Documents"
            service = ExportLocationService(
                documents_location_provider=lambda: documents,
            )
            selected = str(Path(directory) / "chosen.docx")

            with (
                patch.object(service, "prepare_dialog_path", side_effect=PermissionError("denied")),
                patch("packages.ui.export_location.QMessageBox.warning") as warning,
            ):
                result = choose_export_path(
                    parent,
                    "保存报告",
                    "报告.docx",
                    "Word 文档 (*.docx)",
                    location_service=service,
                    file_dialog=lambda *args: (selected, "Word 文档 (*.docx)"),
                )

            self.assertEqual(result[0], selected)
            warning.assert_called_once()
            self.assertIn("明确选择", warning.call_args.args[2])
            self.assertEqual(
                warning.call_args.args[0].windowTitle(),
                parent.windowTitle(),
            )
        parent.close()

    def test_filename_has_business_context_and_windows_safe_components(self):
        record = SimpleNamespace(
            record_id="record.1234567890",
            standard_id="GB_T_32151.34_2024",
            standard_version="v2024",
            input_snapshot=SimpleNamespace(
                enterprise_name='青舟/材料:厂*',
                period=SimpleNamespace(start="2026-01-01", end="2026-12-31"),
            ),
        )

        filename = report_export_filename(record)

        self.assertIn("青舟_材料_厂_", filename)
        self.assertIn("2026-01-01_2026-12-31", filename)
        self.assertIn("GB_T_32151.34_2024_v2024", filename)
        self.assertIn("34567890", filename)
        self.assertTrue(filename.endswith(".docx"))
        self.assertEqual(sanitize_filename_component("CON"), "_CON")


if __name__ == "__main__":
    unittest.main()
