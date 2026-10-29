"""Reusable Presentation source cards for the UIR02 accounting page."""

from __future__ import annotations

from enum import Enum

from .design_tokens import ACCOUNTING_COLORS
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
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
        self._expand_button = QPushButton("展开", header)
        self._expand_button.setObjectName(f"sourceCardExpand_{source_id}")
        self._expand_button.clicked.connect(lambda: self.set_expanded(not self._expanded))
        header_layout.addWidget(self._expand_button)

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
        *,
        show_summary: bool = True,
    ) -> None:
        """Update only the UI-derived state and business summary."""

        self.presentation_state = state
        if self.presentation_state_label.text() != state.value:
            self.presentation_state_label.setText(state.value)
        if self.summary_label.text() != summary:
            self.summary_label.setText(summary)
        summary_visible = show_summary and state is not SourceCardPresentationState.NOT_INVOLVED
        if self.summary_label.isHidden() == summary_visible:
            self.summary_label.setVisible(summary_visible)
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
        action_text = "启用" if status == self._not_involved_value else "停用"
        if self._action_button.text() != action_text:
            self._action_button.setText(action_text)
        expand_visible = status == self._involved_value
        if self._expand_button.isHidden() == expand_visible:
            self._expand_button.setVisible(expand_visible)
        expand_text = "收起" if self._expanded else "展开"
        if self._expand_button.text() != expand_text:
            self._expand_button.setText(expand_text)

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
            QTimer.singleShot(0, self, update_content_geometry)
        self._sync_controls()

    def _on_action_clicked(self) -> None:
        status = self._domain_status()
        target = self._involved_value if status != self._involved_value else self._not_involved_value
        index = self.status_widget.findData(target)
        if index >= 0:
            self.status_widget.setCurrentIndex(index)


__all__ = ["SourceCard", "SourceCardPresentationState"]


class _SourceSwitch(QWidget):
    """Decorative switch; the enclosing accessible button owns interaction."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.active = False
        self.state = "未启用"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        colors = {"已启用": ACCOUNTING_COLORS['brand'], "部分启用": ACCOUNTING_COLORS['source_selected'], "待确认": ACCOUNTING_COLORS['pending_indicator']}
        painter.setBrush(QColor(colors.get(self.state, ACCOUNTING_COLORS['switch_inactive'])))
        painter.drawRoundedRect(0, 1, 36, 18, 9, 9)
        painter.setBrush(QColor(ACCOUNTING_COLORS['white']))
        if self.state == "部分启用":
            painter.setBrush(QColor(ACCOUNTING_COLORS['brand']))
            painter.drawRoundedRect(12, 8, 12, 4, 2, 2)
        elif self.state == "待确认":
            painter.setPen(QColor(ACCOUNTING_COLORS['pending_glyph']))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "?")
        else:
            painter.drawEllipse(21 if self.active else 3, 4, 12, 12)


class SourceToggleButton(QPushButton):
    """Single-line source name with a switch and explicit status below."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        self.title_label = QLabel(title, self)
        self.title_label.setWordWrap(False)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_label.setStyleSheet(f"background: transparent; color: {ACCOUNTING_COLORS['primary_text']}; font-size: 16px; font-weight: 600;")
        layout.addWidget(self.title_label)
        status_row = QHBoxLayout()
        status_row.setSpacing(7)
        self.switch = _SourceSwitch(self)
        status_row.addWidget(self.switch)
        self.state_label = QLabel(self)
        self.state_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.state_label.setStyleSheet(f"background: transparent; color: {ACCOUNTING_COLORS['state_text']}; font-size: 13px;")
        status_row.addWidget(self.state_label)
        status_row.addStretch(1)
        layout.addLayout(status_row)

    def set_source_state(self, state):
        self.setText(f"{state} | {self._title}")
        self.switch.state = state
        self.switch.active = state == "已启用"
        self.switch.update()
        self.state_label.setText(("✓ " if self.switch.active else "") + state)

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        painter = QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, option, painter, self)


class SourceHeaderSwitch(QPushButton):
    """Compact header switch sharing the same state as the source selector."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("sourceHeaderSwitch")
        self.setAccessibleName(title + "排放源开关")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumWidth(142)
        self.setStyleSheet(f"\n            QPushButton#sourceHeaderSwitch {{ min-height:36px; padding:0px 10px; border:2px solid {ACCOUNTING_COLORS['switch_border']}; border-radius:8px; background:{ACCOUNTING_COLORS['switch_surface']}; }}\n            QPushButton#sourceHeaderSwitch[state=\"已启用\"] {{ background:{ACCOUNTING_COLORS['source_active_surface']}; border-color:{ACCOUNTING_COLORS['brand']}; }}\n            QPushButton#sourceHeaderSwitch[state=\"部分启用\"] {{ background:{ACCOUNTING_COLORS['source_active_surface']}; border-color:{ACCOUNTING_COLORS['brand']}; }}\n            QPushButton#sourceHeaderSwitch[state=\"待确认\"] {{ background:{ACCOUNTING_COLORS['pending_surface']}; border-color:{ACCOUNTING_COLORS['pending_border']}; }}\n            QPushButton#sourceHeaderSwitch:hover {{ border:2px solid {ACCOUNTING_COLORS['source_hover_border']}; background:{ACCOUNTING_COLORS['source_selected']}; }}\n            QPushButton#sourceHeaderSwitch[state=\"待确认\"]:hover {{ background:{ACCOUNTING_COLORS['pending_hover']}; }}\n            QPushButton#sourceHeaderSwitch[state=\"未启用\"]:hover {{ background:{ACCOUNTING_COLORS['source_inactive_hover']}; }}\n            QPushButton#sourceHeaderSwitch:focus {{ border:2px solid {ACCOUNTING_COLORS['source_active_text']}; }}\n            QPushButton#sourceHeaderSwitch:pressed {{ background:{ACCOUNTING_COLORS['source_selected']}; }}\n        ")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2,0,2,0)
        layout.setSpacing(7)
        self.switch = _SourceSwitch(self)
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setStyleSheet(f"background:transparent; color:{ACCOUNTING_COLORS['source_active_text']}; font-size:14px; font-weight:600;")
        layout.addWidget(self.switch)
        layout.addWidget(self.label)

    def sizeHint(self):
        return super().sizeHint().expandedTo(self.layout().sizeHint())

    def minimumSizeHint(self):
        return self.sizeHint()

    def set_source_state(self,state):
        self.switch.state = state
        self.switch.active = state == "已启用"
        self.switch.update()
        self.label.setText(state)
        color = ACCOUNTING_COLORS['pending_text'] if state == "待确认" else (ACCOUNTING_COLORS['inactive_text'] if state == "未启用" else ACCOUNTING_COLORS['source_active_text'])
        self.label.setStyleSheet(f"background:transparent;color:{color};font-size:14px;font-weight:600;")
        self.setToolTip(f"当前{state}；点击切换，停用保留已有输入。")
        if self.property("state") != state:
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)
        self.updateGeometry()
        self.setAccessibleDescription(f"当前{state}；点击切换，停用保留数据。")

    def paintEvent(self,event):
        option = QStyleOptionButton(); self.initStyleOption(option); option.text=""
        painter=QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton,option,painter,self)
