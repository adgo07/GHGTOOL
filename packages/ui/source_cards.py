"""Reusable Presentation source cards for the UIR02 accounting page."""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SourceCardPresentationState(str, Enum):
    """UI-only status derived from Domain status and current inputs."""

    NOT_INVOLVED = "未启用"
    COMPLETED = "已完成"
    NEEDS_ATTENTION = "需要处理"
    UNCONFIRMED = "待确认"


class SourceCard(QFrame):
    """One reusable expandable source card.

    The status combo carries the existing Domain enum values supplied by the
    page.  This component never creates or persists a new Domain status; its
    ``presentation_state`` is derived UI metadata only.
    """

    status_changed = Signal(object)
    expansion_changed = Signal(bool)

    def __init__(self, source_id: str, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.source_id = source_id
        self.setObjectName(f"sourceCard_{source_id}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._status_widget: QComboBox | None = None
        self._not_involved_value: object | None = None
        self._involved_value: object | None = None
        self._expanded = False
        self.presentation_state = SourceCardPresentationState.NOT_INVOLVED

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(8)

        header = QWidget(self)
        header.setObjectName(f"sourceCardHeader_{source_id}")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        title_label = QLabel(title, header)
        title_label.setObjectName(f"sourceCardTitle_{source_id}")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)

        self.presentation_state_label = QLabel("未启用", header)
        self.presentation_state_label.setObjectName(f"sourceCardState_{source_id}")
        header_layout.addWidget(self.presentation_state_label)

        self._action_button = QPushButton("启用", header)
        self._action_button.setObjectName(f"sourceCardAction_{source_id}")
        self._action_button.setAutoDefault(False)
        self._action_button.clicked.connect(self._on_action_clicked)
        header_layout.addWidget(self._action_button)

        outer.addWidget(header)

        self.summary_label = QLabel("未启用", self)
        self.summary_label.setObjectName(f"sourceCardSummary_{source_id}")
        self.summary_label.setWordWrap(True)
        outer.addWidget(self.summary_label)

        self.check_result_label = QLabel("", self)
        self.check_result_label.setObjectName(f"sourceCardCheckResult_{source_id}")
        self.check_result_label.setWordWrap(True)
        outer.addWidget(self.check_result_label)

        self.body = QWidget(self)
        self.body.setObjectName(f"sourceCardBody_{source_id}")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 4, 0, 0)
        self.body_layout.setSpacing(10)
        self.body.setVisible(False)
        outer.addWidget(self.body)

    @property
    def status_widget(self) -> QComboBox:
        if self._status_widget is None:
            raise RuntimeError("source card status widget has not been installed")
        return self._status_widget

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def set_status_widget(
        self,
        widget: QComboBox,
        *,
        not_involved_value: object,
        involved_value: object,
    ) -> None:
        """Install the page-owned typed Domain status selector."""

        if self._status_widget is not None:
            raise RuntimeError("source card status widget already installed")
        self._status_widget = widget
        self._not_involved_value = not_involved_value
        self._involved_value = involved_value
        header = self.findChild(QWidget, f"sourceCardHeader_{self.source_id}")
        if header is None:
            raise RuntimeError("source card header is missing")
        # Keep the existing typed Domain enum control as an internal adapter;
        # the ordinary user sees only the single enable/disable action.
        widget.hide()
        widget.currentIndexChanged.connect(lambda _index: self._on_status_changed())
        self._on_status_changed()

    def set_presentation_state(
        self,
        state: SourceCardPresentationState,
        summary: str,
    ) -> None:
        """Update only the UI-derived state and business summary."""

        self.presentation_state = state
        self.presentation_state_label.setText(state.value)
        self.summary_label.setText(summary)
        self._sync_controls()

    def _domain_status(self) -> object | None:
        if self._status_widget is None:
            return None
        return self._status_widget.currentData()

    def _on_status_changed(self) -> None:
        status = self._domain_status()
        if status == self._involved_value:
            self.set_expanded(True)
        else:
            self.set_expanded(False)
        self.status_changed.emit(status)
        self._sync_controls()

    def _sync_controls(self) -> None:
        status = self._domain_status()
        if status == self._not_involved_value:
            self._action_button.setText("启用")
        else:
            self._action_button.setText("停用")

    def set_expanded(self, expanded: bool) -> None:
        status = self._domain_status()
        if expanded and status != self._involved_value:
            expanded = False
        if self._expanded == expanded:
            self.body.setVisible(expanded)
            self._sync_controls()
            return
        self._expanded = expanded
        self.body.setVisible(expanded)
        # Visibility changes alter the page's size hint.  The main scroll host
        # has a fixed geometry, so notify Qt and ask the shell to recalculate
        # its content height after the layout request has settled.
        self.body.updateGeometry()
        self.updateGeometry()
        self.expansion_changed.emit(expanded)
        window = self.window()
        central_widget = getattr(window, "centralWidget", None)
        shell = central_widget() if callable(central_widget) else None
        update_content_geometry = getattr(shell, "update_content_geometry", None)
        if callable(update_content_geometry):
            QTimer.singleShot(0, update_content_geometry)
        self._sync_controls()

    def _on_action_clicked(self) -> None:
        status = self._domain_status()
        target = self._involved_value if status != self._involved_value else self._not_involved_value
        index = self.status_widget.findData(target)
        if index >= 0:
            self.status_widget.setCurrentIndex(index)


__all__ = ["SourceCard", "SourceCardPresentationState"]
