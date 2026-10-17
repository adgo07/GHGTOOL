from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


FIELD_CONTAINER_OBJECT_NAME = "labeledField"
FIELD_TITLE_OBJECT_NAME = "detailFieldLabel"
FIELD_UNIT_HINT_OBJECT_NAME = "fieldUnitHint"


def labeled_field(
    title: str,
    control: QWidget,
    unit_hint: str | None = None,
) -> QWidget:
    """Place a persistent, visible title and optional unit above one control.

    The returned widget owns both the title and control. Add or hide the returned
    widget as a single form item so its label cannot be left behind on its own.
    """
    if not isinstance(control, QWidget):
        raise TypeError("control must be a QWidget")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must not be empty")

    field = QWidget()
    field.setObjectName(FIELD_CONTAINER_OBJECT_NAME)

    heading = QWidget(field)
    heading_layout = QHBoxLayout(heading)
    heading_layout.setContentsMargins(0, 0, 0, 0)
    heading_layout.setSpacing(8)

    title_label = QLabel(title, heading)
    title_label.setObjectName(FIELD_TITLE_OBJECT_NAME)
    title_label.setWordWrap(True)
    title_label.setBuddy(control)
    heading_layout.addWidget(title_label, 1)

    if unit_hint is not None and str(unit_hint).strip():
        unit_label = QLabel(str(unit_hint), heading)
        unit_label.setObjectName(FIELD_UNIT_HINT_OBJECT_NAME)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        heading_layout.addWidget(unit_label, 0)

    layout = QVBoxLayout(field)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    layout.addWidget(heading)
    layout.addWidget(control)
    return field


def set_labeled_field_visible(field: QWidget, visible: bool) -> None:
    """Show or hide a labeled field, its title, unit hint, and control together."""
    if not isinstance(field, QWidget):
        raise TypeError("field must be a QWidget")
    field.setVisible(bool(visible))
