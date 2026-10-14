"""Connected segmented controls bind stable combo values without owning business state."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QButtonGroup, QComboBox, QHBoxLayout, QToolButton, QLabel, QWidget


class SegmentedChoiceControl(QWidget):
    def __init__(self, combo: QComboBox, indices=None, parent=None, *, values=None):
        super().__init__(parent)
        self.setObjectName(combo.objectName() + "Choices")
        self.combo, self.indices, self.values = combo, indices, values
        self.group = QButtonGroup(self)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(0)
        self.row.addStretch(1)
        self.notice = QLabel(self)
        self.notice.setWordWrap(True)
        self.notice.hide()
        combo.setParent(self)
        combo.hide()
        combo.installEventFilter(self)
        combo.currentIndexChanged.connect(self._sync)
        combo.model().dataChanged.connect(self._sync)
        combo.model().rowsInserted.connect(self._rebuild)
        combo.model().rowsRemoved.connect(self._rebuild)
        self.group.idClicked.connect(combo.setCurrentIndex)
        self.setStyleSheet("""
            QToolButton { min-height:28px; padding:3px 8px; border:1px solid #C8DCEB;
                          border-radius:0; background:#FFFFFF; color:#486A80; font-size:14px; }
            QToolButton:checked { background:#E6F4FB; color:#075985; border-color:#197CC2; }
            QToolButton:focus { border:2px solid #197CC2; }
            QToolButton:disabled { color:#9AA9B3; background:#F3F6F8; }
            QLabel { font-size:12px; color:#92651A; }
        """)
        self._rebuild()

    def _rebuild(self, *_):
        for button in self.group.buttons():
            self.group.removeButton(button)
            self.row.removeWidget(button)
            button.deleteLater()
        for index in range(self.combo.count()):
            if self.indices is not None and index not in self.indices:continue
            if self.values is not None and self.combo.itemData(index) not in self.values:continue
            if self.combo.itemData(index) is None:continue
            button = QToolButton(self)
            button.setText(self.combo.itemText(index))
            button.setCheckable(True)
            button.setAccessibleName(self.combo.itemText(index))
            button.installEventFilter(self)
            self.group.addButton(button, index)
            self.row.insertWidget(self.row.count() - 1, button)
        self.row.removeWidget(self.notice)
        self.row.insertWidget(self.row.count() - 1, self.notice)
        if self.group.buttons():self.setFocusProxy(self.group.buttons()[0])
        self._sync()

    def _sync(self, *_):
        self.group.setExclusive(False)
        for button in self.group.buttons():
            index = self.group.id(button)
            button.setText(self.combo.itemText(index))
            button.setChecked(index == self.combo.currentIndex())
            enabled = bool(self.combo.model().flags(self.combo.model().index(index, 0)) & Qt.ItemFlag.ItemIsEnabled)
            button.setEnabled(self.combo.isEnabled() and enabled)
        self.group.setExclusive(True)
        known = any(self.group.id(button) == self.combo.currentIndex() for button in self.group.buttons())
        legacy = self.combo.currentData() is not None and not known
        self.notice.setVisible(legacy)
        self.notice.setText("历史来源未确认" if legacy else "")
        self.notice.setToolTip(self.combo.currentText() if legacy else "")

    def eventFilter(self, watched, event):
        if watched is self.combo and event.type() == QEvent.Type.EnabledChange:self._sync()
        if watched in self.group.buttons() and event.type() == QEvent.Type.KeyPress:
            if event.key() in {Qt.Key.Key_Left, Qt.Key.Key_Right}:
                buttons = [b for b in self.group.buttons() if b.isEnabled() and not b.isHidden()]
                if buttons:
                    current = buttons.index(watched) if watched in buttons else 0
                    target = buttons[(current + (1 if event.key()==Qt.Key.Key_Right else -1)) % len(buttons)]
                    self.combo.setCurrentIndex(self.group.id(target))
                    target.setFocus()
                return True
        return super().eventFilter(watched,event)


class TwoChoiceControl(SegmentedChoiceControl):
    def __init__(self, combo, indices=(0,1), parent=None):
        super().__init__(combo,indices,parent)
