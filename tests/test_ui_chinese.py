from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QLocale, QTimer, Qt
from PySide6.QtTest import QTest
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

    def test_dialog_cancel_escape_close_and_save_default(self):
        button = MessageBox.StandardButton
        for action in ("escape", "close", "enter", "discard"):
            seen = []
            def operate():
                box = self.app.activeModalWidget()
                seen.append((box.defaultButton().text(), box.escapeButton().text(), box.styleSheet()))
                if action == "escape": QTest.keyClick(box, Qt.Key.Key_Escape)
                elif action == "close": box.close()
                elif action == "enter": QTest.keyClick(box, Qt.Key.Key_Return)
                else: box.button(button.Discard).click()
            QTimer.singleShot(0, operate)
            result = MessageBox.question(None, "退出软件", "保存修改？", button.Save | button.Discard | button.Cancel,
                                         button.Save, button_texts={button.Save: "保存后退出", button.Discard: "不保存退出"})
            self.assertEqual(result, {"enter": button.Save, "discard": button.Discard}.get(action, button.Cancel))
            self.assertEqual(seen[0][:2], ("保存后退出", "取消"))
            self.assertIn("QMessageBox QPushButton", seen[0][2])

    def test_name_dialog_cancel_and_accept(self):
        for accepted in (False, True):
            def operate():
                box = self.app.activeModalWidget()
                box.setTextValue("中文名称")
                box.accept() if accepted else box.reject()
            QTimer.singleShot(0, operate)
            self.assertEqual(InputDialog.getText(None, "添加", "名称"), ("中文名称", accepted))

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