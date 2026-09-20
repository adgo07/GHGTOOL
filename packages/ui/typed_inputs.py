"""Reusable typed Qt Widgets for the accounting presentation layer."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QValidator
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QWidget

from .field_specs import FieldDataType, FieldSpec


class NumericLineEdit(QLineEdit):
    """A non-negative numeric input with immediate Qt-level validation."""

    def __init__(self, spec: FieldSpec, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.setProperty("fieldDataType", spec.data_type.value)
        self.setProperty("fieldUnit", spec.unit)
        if spec.data_type is FieldDataType.INTEGER:
            minimum = int(spec.min if spec.min is not None else Decimal("0"))
            maximum = int(spec.max if spec.max is not None else Decimal("2147483647"))
            validator: QValidator = QIntValidator(minimum, maximum, self)
        else:
            minimum = float(spec.min if spec.min is not None else Decimal("0"))
            maximum = float(spec.max if spec.max is not None else Decimal("1e18"))
            double_validator = QDoubleValidator(minimum, maximum, 28, self)
            double_validator.setLocale(QLocale.c())
            double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            validator = double_validator
        self.setValidator(validator)

    def setText(self, text: str) -> None:  # noqa: N802 - Qt API name
        """Keep programmatic updates subject to the same UI restrictions."""

        if text:
            state, _normalized, _position = self.validator().validate(text, 0)
            if state is QValidator.State.Invalid:
                text = ""
            elif state is QValidator.State.Intermediate:
                # QDoubleValidator intentionally returns Intermediate for a
                # syntactically valid value just outside its range.  Keep
                # genuinely incomplete decimal input, but reject a complete
                # out-of-range value immediately, including 101% and -1.
                try:
                    numeric_value = Decimal(text)
                except InvalidOperation:
                    numeric_value = None
                if numeric_value is not None and (
                    (self.spec.min is not None and numeric_value < self.spec.min)
                    or (self.spec.max is not None and numeric_value > self.spec.max)
                ):
                    text = ""
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
