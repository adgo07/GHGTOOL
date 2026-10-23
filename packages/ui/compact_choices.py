"""Connected segmented controls bind stable combo values without owning business state."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QButtonGroup, QComboBox, QHBoxLayout, QToolButton, QRadioButton, QLabel, QWidget


def _choice_value(value):
    value = getattr(value, "value", value)
    return None if value is None else str(value)


class SegmentedChoiceControl(QWidget):
    def __init__(self, combo: QComboBox, indices=None, parent=None, *, values=None):
        super().__init__(parent)
        self.setObjectName(combo.objectName() + "Choices")
        self.combo, self.indices = combo, indices
        self.values = None if values is None else frozenset(_choice_value(value) for value in values)
        self._radio_style = False
        self.group = QButtonGroup(self)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(0)
        self.row.addStretch(1)
        self.single_label = QLabel(self)
        self.single_label.setObjectName("singleAllowedChoiceLabel")
        self.single_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.single_label.setAccessibleDescription("当前唯一适用来源；如需更改，请选择一个适用来源。")
        self.notice = QLabel(self)
        self.notice.setObjectName("choiceConfirmationNotice")
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
            QToolButton { min-height:32px; padding:4px 10px; border:1px solid #C8DCEB;
                          border-radius:0; background:#FFFFFF; color:#486A80; font-size:14px; }
            QToolButton[segmentPosition="first"] {
                border-top-left-radius:7px; border-bottom-left-radius:7px;
            }
            QToolButton[segmentPosition="middle"], QToolButton[segmentPosition="last"] {
                border-left:0;
            }
            QToolButton[segmentPosition="last"] {
                border-top-right-radius:7px; border-bottom-right-radius:7px;
            }
            QToolButton[segmentPosition="single"] { border-radius:7px; }
            QToolButton:checked { background:#E6F4FB; color:#075985; border-color:#197CC2; }
            QToolButton:focus { border:2px solid #197CC2; }
            QToolButton:disabled { color:#9AA9B3; background:#F3F6F8; }
            QLabel#singleAllowedChoiceLabel {
                min-height:32px; padding:4px 10px; border:1px solid #C8DCEB;
                border-radius:7px; background:#F3F6F8; color:#486A80; font-size:14px;
            }
            QLabel#singleAllowedChoiceLabel:disabled { color:#9AA9B3; }
            QLabel#choiceConfirmationNotice { font-size:12px; color:#92651A; }
        """)
        self._rebuild()

    def set_radio_style(self):
        """Presentation only: retain the combo, policy filters and signal adapter."""
        if self._radio_style:
            return
        self._radio_style = True
        self.row.setSpacing(14)
        self.single_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet("""
            QRadioButton {font-size:14px;spacing:7px;min-height:30px;color:#344E61;}
            QRadioButton::indicator {width:14px;height:14px;border:1px solid #93A8B6;border-radius:8px;background:white;}
            QRadioButton::indicator:checked {background:#147BB5;border:3px solid #CEE5F3;}
            QRadioButton:focus {outline:1px solid #197CC2;}
            QRadioButton:disabled {color:#9BA8B0;}
            QLabel#singleAllowedChoiceLabel {font-size:13px;color:#526A7A;min-height:30px;border:0;padding:0;}
            QLabel#choiceConfirmationNotice {color:#936026;font-size:12px;}
        """)
        self._rebuild()

    def set_allowed_values(self, values):
        """Restrict visible choices without changing the combo's stored selection."""
        normalized = None if values is None else frozenset(_choice_value(value) for value in values)
        if normalized == self.values:
            self._sync()
            return
        self.values = normalized
        self._rebuild()

    def _allowed_indices(self):
        indices = []
        for index in range(self.combo.count()):
            if self.indices is not None and index not in self.indices:
                continue
            value = _choice_value(self.combo.itemData(index))
            if value is None or self.values is not None and value not in self.values:
                continue
            indices.append(index)
        return indices

    def _rebuild(self, *_):
        for button in self.group.buttons():
            self.group.removeButton(button)
            self.row.removeWidget(button)
            button.hide()
            button.deleteLater()
        self.row.removeWidget(self.single_label)
        self.row.removeWidget(self.notice)
        allowed = self._allowed_indices()
        if len(allowed) == 1 and self.combo.currentIndex() == allowed[0]:
            index = allowed[0]
            self.single_label.setText(self.combo.itemText(index))
            self.single_label.setAccessibleName("当前来源：" + self.combo.itemText(index))
            enabled = bool(self.combo.model().flags(self.combo.model().index(index, 0)) & Qt.ItemFlag.ItemIsEnabled)
            self.single_label.setEnabled(self.combo.isEnabled() and enabled)
            self.row.insertWidget(self.row.count() - 1, self.single_label)
        elif not allowed:
            self.single_label.setText("暂无适用来源")
            self.single_label.setAccessibleName("暂无适用来源")
            self.single_label.setEnabled(False)
            self.row.insertWidget(self.row.count() - 1, self.single_label)
        else:
            for position, index in enumerate(allowed):
                value = _choice_value(self.combo.itemData(index))
                button = QRadioButton(self) if self._radio_style else QToolButton(self)
                button.setText(self.combo.itemText(index))
                button.setCheckable(True)
                button.setAccessibleName(self.combo.itemText(index))
                button.setProperty(
                    "segmentPosition",
                    "single" if len(allowed) == 1 else "first" if position == 0 else "last" if position == len(allowed) - 1 else "middle",
                )
                button.installEventFilter(self)
                self.group.addButton(button, index)
                self.row.insertWidget(self.row.count() - 1, button)
        self.row.insertWidget(self.row.count() - 1, self.notice)
        self.single_label.hide()
        self.notice.hide()
        self._sync()

    def _sync(self, *_):
        allowed = self._allowed_indices()
        expected_buttons = (
            allowed
            if len(allowed) > 1 or len(allowed) == 1 and self.combo.currentIndex() != allowed[0]
            else []
        )
        if [self.group.id(button) for button in self.group.buttons()] != expected_buttons:
            self._rebuild()
            return
        self.group.setExclusive(False)
        for button in self.group.buttons():
            index = self.group.id(button)
            button.setText(self.combo.itemText(index))
            button.setChecked(index == self.combo.currentIndex())
            enabled = bool(self.combo.model().flags(self.combo.model().index(index, 0)) & Qt.ItemFlag.ItemIsEnabled)
            button.setEnabled(self.combo.isEnabled() and enabled)
        self.group.setExclusive(True)
        known = self.combo.currentIndex() in allowed
        current_value = self.combo.currentData()
        legacy = current_value is not None and not known
        self.notice.setVisible(legacy)
        self.notice.setText("历史来源不适用，请确认" if legacy else "")
        self.notice.setToolTip(self.combo.currentText() if legacy else "")
        self.notice.setAccessibleName(self.notice.text())
        if len(allowed) == 1 and self.combo.currentIndex() == allowed[0]:
            self.single_label.setText(self.combo.itemText(allowed[0]))
            self.single_label.setAccessibleName("当前来源：" + self.combo.itemText(allowed[0]))
            self.single_label.setVisible(True)
        elif not allowed:
            self.single_label.setText("暂无适用来源")
            self.single_label.setAccessibleName("暂无适用来源")
            self.single_label.setEnabled(False)
            self.single_label.setVisible(True)
        else:
            self.single_label.hide()
        buttons = self.group.buttons()
        for position, button in enumerate(buttons):
            if len(buttons) == 1:
                segment_position = "single"
            elif position == 0:
                segment_position = "first"
            elif position == len(buttons) - 1:
                segment_position = "last"
            else:
                segment_position = "middle"
            button.setProperty("segmentPosition", segment_position)
            button.style().unpolish(button)
            button.style().polish(button)
        self.single_label.setMinimumHeight(32)
        if self.group.buttons():self.setFocusProxy(self.group.buttons()[0])
        elif not self.single_label.isHidden():self.setFocusProxy(self.single_label)
        else:self.setFocusProxy(None)

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
