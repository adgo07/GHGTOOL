"""Real modal tests in a fresh Qt process, never the discover process's event loop."""
import unittest
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QDialog
from packages.ui.dialogs import MessageBox, InputDialog

class DialogProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def invoke(self, kind, call, action):
        errors = []
        original = kind.exec
        def run(box):
            def operate():
                try:
                    self.assertTrue(box.isVisible())
                    self.assertIs(self.app.activeModalWidget(), box)
                    action(box)
                except BaseException as exc:
                    errors.append(exc)
                    box.reject()
            timer = QTimer(box)
            timer.setSingleShot(True)
            timer.timeout.connect(operate)
            timer.start(0)
            return original(box)
        with patch.object(kind, 'exec', run):
            result = call()
        if errors:
            raise errors[0]
        return result

    def test_message(self):
        b = MessageBox.StandardButton
        for action in ('escape', 'close', 'enter', 'discard'):
            def operate(box):
                self.assertEqual(box.defaultButton().text(), '保存后退出')
                self.assertEqual(box.escapeButton().text(), '取消')
                self.assertIn('QMessageBox QPushButton', box.styleSheet())
                if action == 'escape': QTest.keyClick(box, Qt.Key.Key_Escape)
                elif action == 'close': box.close()
                elif action == 'enter': QTest.keyClick(box, Qt.Key.Key_Return)
                else: box.button(b.Discard).click()
            result = self.invoke(MessageBox, lambda: MessageBox.question(None, '退出软件', '保存修改？',
                b.Save | b.Discard | b.Cancel, b.Save, button_texts={b.Save:'保存后退出', b.Discard:'不保存退出'}), operate)
            self.assertEqual(result, {'enter':b.Save,'discard':b.Discard}.get(action,b.Cancel))
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_input(self):
        for accepted in (False, True):
            def operate(box):
                box.setTextValue('中文名称')
                box.accept() if accepted else box.reject()
            self.assertEqual(self.invoke(InputDialog, lambda: InputDialog.getText(None,'添加','名称'),operate),
                             ('中文名称',accepted))
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_lifetime(self):
        parent = QWidget()
        baseline = len(parent.findChildren(QDialog))
        b = MessageBox.StandardButton
        for _ in range(5):
            self.assertEqual(self.invoke(MessageBox, lambda: MessageBox.question(parent,'确认','操作？'),
                lambda box: box.button(b.No).click()),b.No)
            self.assertEqual(self.invoke(InputDialog, lambda: InputDialog.getText(parent,'名称','输入',text='保留'),
                lambda box: box.reject()),('保留',False))
            self.assertEqual(self.invoke(InputDialog, lambda: InputDialog.getItem(parent,'类型','选择',['甲','乙'],1,False),
                lambda box: box.reject()),('乙',False))
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.assertEqual(len(parent.findChildren(QDialog)),baseline)
        for kind, call in ((MessageBox,lambda:MessageBox.question(parent,'确认','操作？')),
                           (InputDialog,lambda:InputDialog.getText(parent,'名称','输入')),
                           (InputDialog,lambda:InputDialog.getItem(parent,'类型','选择',['甲']))):
            with patch.object(kind,'exec',side_effect=RuntimeError('injected')):
                with self.assertRaisesRegex(RuntimeError,'injected'): call()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.assertEqual(len(parent.findChildren(QDialog)),baseline)
        parent.deleteLater()

if __name__ == '__main__':
    unittest.main()
