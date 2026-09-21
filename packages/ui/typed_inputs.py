"""Reusable typed Qt Widgets for the accounting presentation layer."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QWidget

from .field_specs import FieldDataType, FieldSpec


class _StrictNumericValidator(QValidator):
    """Validator that rejects complete out-of-range values as Invalid.

    Qt's built-in numeric validators report some out-of-range values as
    ``Intermediate`` so that a user can continue typing.  That is useful for
    unrestricted numeric fields, but it lets a value such as ``101`` appear
    in a 0--100 percentage field.  This adapter delegates to the line edit's
    exact Decimal-aware candidate validation instead.
    """

    def __init__(self, owner: "NumericLineEdit") -> None:
        super().__init__(owner)
        self.owner = owner

    def validate(self, input: str, pos: int) -> tuple[QValidator.State, str, int]:
        return self.owner._candidate_state(input), input, pos


class NumericLineEdit(QLineEdit):
    """A non-negative numeric input with immediate Qt-level validation."""

    def __init__(self, spec: FieldSpec, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.spec = spec
        self._blocked_negative_sequence = False
        self.setProperty("fieldDataType", spec.data_type.value)
        self.setProperty("fieldUnit", spec.unit)
        self.setValidator(_StrictNumericValidator(self))

    @staticmethod
    def _bound(value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value if isinstance(value, Decimal) else Decimal(str(value))

    def _candidate_state(self, text: str) -> QValidator.State:
        """Return the state for a complete edit candidate.

        Empty and trailing-decimal candidates remain Intermediate so normal
        editing is possible.  Any non-numeric character, sign, separator or
        value outside the FieldSpec range is Invalid immediately.
        """

        if text == "":
            return QValidator.State.Intermediate

        if self.spec.data_type is FieldDataType.INTEGER:
            if not all(character in "0123456789" for character in text):
                return QValidator.State.Invalid
            numeric_value = Decimal(text)
            trailing_decimal = False
        else:
            if any(character not in "0123456789." for character in text):
                return QValidator.State.Invalid
            if text.count(".") > 1:
                return QValidator.State.Invalid
            trailing_decimal = text.endswith(".")
            normalized = text[:-1] if trailing_decimal else text
            if not normalized:
                if self._bound(self.spec.min) not in (None, Decimal("0")):
                    return QValidator.State.Invalid
                return QValidator.State.Intermediate
            if normalized == ".":
                normalized = "0."
            elif normalized.startswith("."):
                normalized = "0" + normalized
            try:
                numeric_value = Decimal(normalized)
            except InvalidOperation:
                return QValidator.State.Invalid

        minimum = self._bound(self.spec.min)
        maximum = self._bound(self.spec.max)
        if minimum is not None and numeric_value < minimum:
            return QValidator.State.Invalid
        if maximum is not None and numeric_value > maximum:
            return QValidator.State.Invalid
        if trailing_decimal:
            return QValidator.State.Intermediate
        return QValidator.State.Acceptable

    def _candidate_after_insertion(self, insertion: str) -> str:
        start = self.selectionStart()
        if start < 0:
            start = self.cursorPosition()
        end = start + self.selectionLength()
        current = self.text()
        return current[:start] + insertion + current[end:]

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API name
        """Validate the exact candidate before Qt mutates the line edit."""

        modifiers = event.modifiers()
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
            self._blocked_negative_sequence = False
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self._blocked_negative_sequence = False
            super().keyPressEvent(event)
            return

        insertion = event.text()
        if not insertion:
            self._blocked_negative_sequence = False
            super().keyPressEvent(event)
            return

        if self._blocked_negative_sequence:
            if all(character in "0123456789" for character in insertion):
                event.accept()
                return
            self._blocked_negative_sequence = False

        if insertion in {"-", "−"}:
            # Do not let a rejected minus sign turn the following ``-1`` key
            # sequence into the apparently valid value ``1``.
            self._blocked_negative_sequence = True
            event.accept()
            return

        candidate = self._candidate_after_insertion(insertion)
        if self._candidate_state(candidate) is QValidator.State.Invalid:
            event.accept()
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData) -> None:  # noqa: N802 - Qt API name
        """Reject an invalid paste as a whole, including separators/signs."""

        candidate = self._candidate_after_insertion(source.text())
        if self._candidate_state(candidate) is QValidator.State.Invalid:
            return
        self._blocked_negative_sequence = False
        super().insertFromMimeData(source)

    def setText(self, text: str) -> None:  # noqa: N802 - Qt API name
        """Keep programmatic updates subject to the same UI restrictions."""

        if self._candidate_state(text) is QValidator.State.Invalid:
            text = ""
        self._blocked_negative_sequence = False
        super().setText(text)


def create_text_input(
    parent: QWidget,
    spec: FieldSpec,
    object_name: str,
    placeholder: str = "",
) -> QLineEdit:
    edit = QLineEdit(parent)
    edit.setObjectName(object_name)
    edit.setProperty("fieldSpecKey", spec.internal_key)
    edit.setProperty("fieldDataType", spec.data_type.value)
    edit.setProperty("fieldUnit", spec.unit)
    if placeholder:
        edit.setPlaceholderText(placeholder)
    if spec.help_text:
        edit.setToolTip(spec.help_text)
    return edit


def create_numeric_input(
    parent: QWidget,
    spec: FieldSpec,
    object_name: str,
    placeholder: str = "",
) -> NumericLineEdit:
    edit = NumericLineEdit(spec, parent)
    edit.setObjectName(object_name)
    edit.setProperty("fieldSpecKey", spec.internal_key)
    if placeholder:
        edit.setPlaceholderText(placeholder)
    if spec.help_text:
        edit.setToolTip(spec.help_text)
    return edit


def create_enum_input(parent: QWidget, spec: FieldSpec, object_name: str) -> QComboBox:
    combo = QComboBox(parent)
    combo.setObjectName(object_name)
    combo.setProperty("fieldSpecKey", spec.internal_key)
    combo.setProperty("fieldDataType", spec.data_type.value)
    if spec.help_text:
        combo.setToolTip(spec.help_text)
    return combo


def create_boolean_input(parent: QWidget, spec: FieldSpec, object_name: str) -> QCheckBox:
    checkbox = QCheckBox(parent)
    checkbox.setObjectName(object_name)
    checkbox.setProperty("fieldSpecKey", spec.internal_key)
    checkbox.setProperty("fieldDataType", spec.data_type.value)
    if spec.help_text:
        checkbox.setToolTip(spec.help_text)
    return checkbox


def create_read_only_parameter(parent: QWidget, spec: FieldSpec, object_name: str) -> QLabel:
    """Create a read-only display for a Catalog parameter/factor selection."""

    label = QLabel(parent)
    label.setObjectName(object_name)
    label.setProperty("fieldSpecKey", spec.internal_key)
    label.setProperty("fieldDataType", spec.data_type.value)
    label.setProperty("fieldUnit", spec.unit)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setWordWrap(True)
    if spec.help_text:
        label.setToolTip(spec.help_text)
    return label


def create_typed_input(
    parent: QWidget,
    spec: FieldSpec,
    object_name: str,
    placeholder: str = "",
) -> QWidget:
    """Create the Qt control dictated by a :class:`FieldSpec`."""

    if spec.data_type is FieldDataType.TEXT:
        return create_text_input(parent, spec, object_name, placeholder)
    if spec.data_type in {
        FieldDataType.QUANTITY,
        FieldDataType.PERCENTAGE,
        FieldDataType.INTEGER,
    }:
        return create_numeric_input(parent, spec, object_name, placeholder)
    if spec.data_type is FieldDataType.ENUM:
        return create_enum_input(parent, spec, object_name)
    if spec.data_type is FieldDataType.BOOLEAN:
        return create_boolean_input(parent, spec, object_name)
    if spec.data_type is FieldDataType.READONLY_PARAMETER:
        return create_read_only_parameter(parent, spec, object_name)
    raise ValueError(f"不支持的 UI 字段类型：{spec.data_type}")


__all__ = [
    "NumericLineEdit",
    "create_boolean_input",
    "create_enum_input",
    "create_numeric_input",
    "create_read_only_parameter",
    "create_text_input",
    "create_typed_input",
]
