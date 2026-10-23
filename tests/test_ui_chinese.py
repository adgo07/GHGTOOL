from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication, QLineEdit
from packages.ui.chinese import initialize_chinese, load_translator, translation_path, report_chinese_failure
from packages.ui.dialogs import MessageBox, InputDialog
from scripts.standalone_entry import verify_chinese_resources


class ChineseUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_translation_is_real_idempotent_and_does_not_set_locale(self):
        before = QLocale().name()
        first = initialize_chinese(self.app)
        self.assertTrue(first["loaded"])
        translator = self.app._qz_chinese_translator
        self.assertIs(initialize_chinese(self.app), first)
        self.assertIs(self.app._qz_chinese_translator, translator)
        self.assertEqual(QLocale().name(), before)
        self.assertEqual(verify_chinese_resources()["qt_cancel"], "取消")
        editor = QLineEdit("示例")
        texts = [a.text() for a in editor.createStandardContextMenu().actions()]
        self.assertTrue(any("复制" in text for text in texts), texts)

    def test_missing_corrupt_and_mismatched_resources_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.qm"
            with self.assertRaises(OSError):
                load_translator(path)
            path.write_bytes(b"corrupt")
            with self.assertRaises(RuntimeError):
                load_translator(path)
        with patch("packages.ui.chinese.qVersion", return_value="6.12.0"), self.assertRaises(RuntimeError):
            load_translator(translation_path())

    def test_degraded_notice_once_and_safe_explicit_buttons(self):
        initialize_chinese(self.app)
        original = self.app._qz_chinese_status
        self.app._qz_chinese_status = {"loaded": False, "error": "missing"}
        self.app._qz_chinese_notified = False
        logger = Mock()
        try:
            with patch.object(MessageBox, "warning") as warning:
                report_chinese_failure(self.app, logger)
                report_chinese_failure(self.app, logger)
                warning.assert_called_once()
                logger.event.assert_called_once()
            box = MessageBox()
            self.assertEqual(box.addButton(MessageBox.StandardButton.Cancel).text(), "取消")
            dialog = InputDialog()
            self.assertEqual(dialog.okButtonText(), "确定")
            self.assertEqual(dialog.cancelButtonText(), "取消")
        finally:
            self.app._qz_chinese_status = original
            self.app._qz_chinese_notified = False

    def run_modal_process(self, case):
        environment = os.environ.copy()
        environment['QT_QPA_PLATFORM'] = 'offscreen'
        result = subprocess.run([sys.executable, '-B', '-m', 'tests.ui_dialog_process',
                                 f'DialogProcessTests.test_{case}', '-v'],
                                cwd=Path(__file__).resolve().parents[1], env=environment,
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dialog_cancel_escape_close_and_save_default(self):
        self.run_modal_process('message')

    def test_name_dialog_cancel_and_accept(self):
        self.run_modal_process('input')

    def test_parented_dialogs_release_on_return_cancel_and_exception(self):
        self.run_modal_process('lifetime')

    def test_save_failure_does_not_close_or_discard(self):
        from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
        page = Mock()
        for saved in (False, True):
            page._save_project.return_value = saved
            with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Save):
                self.assertEqual(CarbonMaterialAccountingPage._confirm_save_discard_cancel(page, "关闭软件"), saved)
        with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Cancel):
            self.assertFalse(CarbonMaterialAccountingPage._confirm_save_discard_cancel(page, "关闭软件"))

    def test_failed_initialization_is_not_retried(self):
        from types import SimpleNamespace
        application = SimpleNamespace()
        with patch("packages.ui.chinese.load_translator", side_effect=FileNotFoundError("missing")) as load:
            first = initialize_chinese(application)
            self.assertFalse(first["loaded"])
            self.assertEqual(first["error_type"], "resource_io_error")
            self.assertIs(initialize_chinese(application), first)
            load.assert_called_once()

    def test_translation_pruning_and_audit_reject_missing_corrupt_extra(self):
        from scripts.build_standalone import _keep_chinese_translation_only
        from scripts.inspect_release import inspect_release
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            qm = root / "PySide6/translations/qtbase_zh_CN.qm"
            qm.parent.mkdir(parents=True)
            qm.write_bytes(translation_path().read_bytes())
            extra = qm.with_name("qtbase_de.qm")
            extra.write_bytes(b"other language")
            self.assertIn("unexpected Qt translation resource", inspect_release(root))
            _keep_chinese_translation_only(root)
            self.assertEqual(list(qm.parent.glob("*.qm")), [qm])
            self.assertNotIn("missing or mismatched Simplified Chinese translation", inspect_release(root))
            qm.write_bytes(b"corrupt")
            self.assertIn("missing or mismatched Simplified Chinese translation", inspect_release(root))
            qm.unlink()
            self.assertIn("missing or mismatched Simplified Chinese translation", inspect_release(root))