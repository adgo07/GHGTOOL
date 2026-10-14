"""Two-choice presentation binding; typed combo remains the state adapter."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QButtonGroup, QComboBox, QHBoxLayout, QRadioButton, QWidget


class TwoChoiceControl(QWidget):
    """Keep established combo values/legacy reads while presenting two radio choices."""

    def __init__(self, combo: QComboBox, indices=(0, 1), parent=None):
        super().__init__(parent)
        self.setObjectName(combo.objectName() + "Choices")
        self.combo = combo
        self.group = QButtonGroup(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for index in indices:
            button = QRadioButton(combo.itemText(index), self)
            button.setAccessibleName(combo.itemText(index))
            self.group.addButton(button, index)
            layout.addWidget(button)
        combo.setParent(self)
        combo.hide()
        combo.installEventFilter(self)
        combo.currentIndexChanged.connect(self._sync)
        self.group.idClicked.connect(combo.setCurrentIndex)
        self.setFocusProxy(self.group.buttons()[0])
        self._sync()

    def _sync(self, *_):
        self.group.setExclusive(False)
        for button in self.group.buttons():
            index = self.group.id(button)
            button.setChecked(index == self.combo.currentIndex())
            item_enabled = bool(self.combo.model().flags(self.combo.model().index(index, 0)) & Qt.ItemFlag.ItemIsEnabled)
            button.setEnabled(self.combo.isEnabled() and item_enabled)
        self.group.setExclusive(True)

    def eventFilter(self, watched, event):
        if watched is self.combo and event.type() == QEvent.Type.EnabledChange:
            self._sync()
        return super().eventFilter(watched, event)
