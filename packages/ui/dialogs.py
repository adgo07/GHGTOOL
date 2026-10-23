"""Small Qt dialog adapters: explicit labels, unchanged Qt return identities."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from .design_tokens import message_button_stylesheet


class MessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOption(QMessageBox.Option.DontUseNativeDialog, True)
        self.setStyleSheet(message_button_stylesheet())

    def addButton(self, button, *args):
        result = super().addButton(button, *args)
        if isinstance(button, QMessageBox.StandardButton):
            labels = {self.StandardButton.Ok: "确定", self.StandardButton.Close: "关闭",
                      self.StandardButton.Cancel: "取消", self.StandardButton.Yes: "确认",
                      self.StandardButton.No: "取消", self.StandardButton.Save: "保存",
                      self.StandardButton.Discard: "不保存"}
            if button in labels:
                result.setText(labels[button])
        return result

    @classmethod
    def _show(cls, parent, title, text, icon, buttons, default, *, button_texts=None, informative_text=""):
        box = cls(parent)
        try:
            box.setWindowTitle(title)
            box.setText(text)
            box.setInformativeText(informative_text)
            box.setIcon(icon)
            for standard in cls.StandardButton:
                if standard != cls.StandardButton.NoButton and buttons & standard:
                    button = box.addButton(standard)
                    if button_texts and standard in button_texts:
                        button.setText(button_texts[standard])
            if default != cls.StandardButton.NoButton:
                box.setDefaultButton(default)
            for escape in (cls.StandardButton.Cancel, cls.StandardButton.No, cls.StandardButton.Close, cls.StandardButton.Ok):
                if buttons & escape:
                    box.setEscapeButton(escape)
                    break
            return cls.StandardButton(box.exec())
        finally:
            box.deleteLater()

    @classmethod
    def question(cls, parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                 defaultButton=QMessageBox.StandardButton.No, **kwargs):
        return cls._show(parent, title, text, cls.Icon.Question, buttons, defaultButton, **kwargs)

    @classmethod
    def information(cls, parent, title, text, buttons=QMessageBox.StandardButton.Ok,
                    defaultButton=QMessageBox.StandardButton.Ok):
        return cls._show(parent, title, text, cls.Icon.Information, buttons, defaultButton)

    @classmethod
    def warning(cls, parent, title, text, buttons=QMessageBox.StandardButton.Ok,
                defaultButton=QMessageBox.StandardButton.Ok):
        return cls._show(parent, title, text, cls.Icon.Warning, buttons, defaultButton)

    @classmethod
    def critical(cls, parent, title, text, buttons=QMessageBox.StandardButton.Ok,
                 defaultButton=QMessageBox.StandardButton.Ok):
        return cls._show(parent, title, text, cls.Icon.Critical, buttons, defaultButton)


class InputDialog(QInputDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInputMode(QInputDialog.InputMode.TextInput)
        self.findChild(QLineEdit).setMinimumWidth(320)
        self.setOkButtonText("确定")
        self.setCancelButtonText("取消")

    @classmethod
    def getText(cls, parent, title, label, echo=QLineEdit.EchoMode.Normal, text="", *, confirm_text="确定"):
        box = cls(parent)
        try:
            box.setWindowTitle(title)
            box.setLabelText(label)
            box.setOkButtonText(confirm_text)
            box.setTextEchoMode(echo)
            box.setTextValue(text)
            accepted = box.exec() == cls.DialogCode.Accepted
            return box.textValue(), accepted
        finally:
            box.deleteLater()

    @classmethod
    def getItem(cls, parent, title, label, items, current=0, editable=True, *, confirm_text="确定"):
        box = cls(parent)
        try:
            box.setWindowTitle(title)
            box.setLabelText(label)
            box.setOkButtonText(confirm_text)
            box.setComboBoxItems(list(items))
            box.setComboBoxEditable(editable)
            if items:
                box.setTextValue(items[current])
            accepted = box.exec() == cls.DialogCode.Accepted
            return box.textValue(), accepted
        finally:
            box.deleteLater()
