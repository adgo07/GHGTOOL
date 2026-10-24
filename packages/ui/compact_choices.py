"""Connected segmented controls bind stable combo values without owning business state."""
from .design_tokens import ACCOUNTING_COLORS
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
        self.setStyleSheet(f"\n            QToolButton {{ min-height:32px; padding:4px 10px; border:1px solid {ACCOUNTING_COLORS['choice_border']};\n                          border-radius:0; background:{ACCOUNTING_COLORS['white']}; color:{ACCOUNTING_COLORS['choice_text']}; font-size:14px; }}\n            QToolButton[segmentPosition=\"first\"] {{\n                border-top-left-radius:7px; border-bottom-left-radius:7px;\n            }}\n            QToolButton[segmentPosition=\"middle\"], QToolButton[segmentPosition=\"last\"] {{\n                border-left:0;\n            }}\n            QToolButton[segmentPosition=\"last\"] {{\n                border-top-right-radius:7px; border-bottom-right-radius:7px;\n            }}\n            QToolButton[segmentPosition=\"single\"] {{ border-radius:7px; }}\n            QToolButton:checked {{ background:{ACCOUNTING_COLORS['source_active_surface']}; color:{ACCOUNTING_COLORS['choice_selected_text']}; border-color:{ACCOUNTING_COLORS['brand']}; }}\n            QToolButton:focus {{ border:2px solid {ACCOUNTING_COLORS['brand']}; }}\n            QToolButton:disabled {{ color:{ACCOUNTING_COLORS['choice_disabled_text']}; background:{ACCOUNTING_COLORS['choice_disabled_surface']}; }}\n            QLabel#singleAllowedChoiceLabel {{\n                min-height:32px; padding:4px 10px; border:1px solid {ACCOUNTING_COLORS['choice_border']};\n                border-radius:7px; background:{ACCOUNTING_COLORS['choice_disabled_surface']}; color:{ACCOUNTING_COLORS['choice_text']}; font-size:14px;\n            }}\n            QLabel#singleAllowedChoiceLabel:disabled {{ color:{ACCOUNTING_COLORS['choice_disabled_text']}; }}\n            QLabel#choiceConfirmationNotice {{ font-size:12px; color:{ACCOUNTING_COLORS['choice_notice']}; }}\n        ")
        self._rebuild()

    def set_radio_style(self):
        """Presentation only: retain the combo, policy filters and signal adapter."""
        if self._radio_style:
            return
        self._radio_style = True
        self.row.setSpacing(14)
        self.single_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet(f"\n            QRadioButton {{font-size:14px;spacing:7px;min-height:30px;color:{ACCOUNTING_COLORS['radio_text']};}}\n            QRadioButton::indicator {{width:14px;height:14px;border:1px solid {ACCOUNTING_COLORS['radio_border']};border-radius:8px;background:white;}}\n            QRadioButton::indicator:checked {{background:{ACCOUNTING_COLORS['radio_selected']};border:3px solid {ACCOUNTING_COLORS['radio_selected_border']};}}\n            QRadioButton:focus {{outline:1px solid {ACCOUNTING_COLORS['brand']};}}\n            QRadioButton:disabled {{color:{ACCOUNTING_COLORS['radio_disabled_text']};}}\n            QLabel#singleAllowedChoiceLabel {{font-size:13px;color:{ACCOUNTING_COLORS['single_choice_text']};min-height:30px;border:0;padding:0;}}\n            QLabel#choiceConfirmationNotice {{color:{ACCOUNTING_COLORS['radio_notice']};font-size:12px;}}\n        ")
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
