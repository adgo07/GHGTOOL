"""Opt-in, presentation-only styles for the reference/import/record/settings pages.

Not an application theme. Styles are applied once; table reflow stays local.
No business state, timers, assets, dependencies, locale, or business policy.
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel, QStyle, QStyleOptionButton, QStyledItemDelegate,
    QStyleOptionViewItem, QTableWidget, QVBoxLayout, QWidget)
from .design_tokens import BORDER, CARD_BACKGROUND, PRIMARY_BRAND, PRIMARY_TEXT, SECONDARY_TEXT, SURFACE_MUTED


class _CellWidgetDelegate(QStyledItemDelegate):
    """Keep model/accessibility text, but paint it only once under cell widgets."""
    def paint(self, painter, option, index):
        if self.parent().indexWidget(index) is None:
            return super().paint(painter, option, index)
        cell = QStyleOptionViewItem(option)
        self.initStyleOption(cell, index)
        cell.text = ""
        style = cell.widget.style() if cell.widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, cell, painter, cell.widget)


class ReadableTable(QTableWidget):
    """Reflow wrapped rows when their actual column widths change, without timers."""
    def __init__(self, parent=None, *, row_padding=0):
        super().__init__(parent)
        self._row_padding = row_padding
        self._fitting_rows = False
        self.verticalHeader().setMinimumSectionSize(40)
        self.setItemDelegate(_CellWidgetDelegate(self))
        self.horizontalHeader().sectionResized.connect(
            self._fit_rows, Qt.ConnectionType.QueuedConnection)

    def resizeRowsToContents(self):
        self._fit_rows()

    def _fit_rows(self, *_args):
        if self._fitting_rows:
            return
        self._fitting_rows = True
        try:
            super().resizeRowsToContents()
            # Qt's wrapped-item hint can omit stylesheet paint insets.
            # Keep space for the last line instead of clipping at the grid edge.
            for row in range(self.rowCount()):
                # Stretch headers can settle during the native resize pass.
                # Include the hint at the final width before adding paint space.
                height = max(self.rowHeight(row), self.sizeHintForRow(row))
                self.setRowHeight(row, height + self._row_padding)
        finally:
            self._fitting_rows = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_rows()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_rows()


def surface(title: str, parent: QWidget, name: str = "businessSurface") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName(name)
    frame.setProperty("businessSurface", True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    if title:
        heading = QLabel(title, frame)
        heading.setObjectName("cardTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)
    return frame, layout


def apply_business_page_style(page: QWidget) -> None:
    """Append scoped UI styles once; do not restyle on navigation/input/refresh."""
    if page.property("businessVisualApplied"):
        return
    page.setProperty("businessVisualApplied", True)
    page.setStyleSheet(page.styleSheet() + f"""
        QLabel#pageTitle {{ font-size:24px; font-weight:600; color:{PRIMARY_TEXT}; }}
        QLabel#pageDescription, QLabel#secondaryText,
        QLabel#recordResultCount, QLabel#exportDirectoryStatus {{ font-size:13px; color:{SECONDARY_TEXT}; }}
        QFrame[businessSurface="true"] {{ background:{CARD_BACKGROUND}; border:1px solid {BORDER}; border-radius:10px; }}
        QLabel#cardTitle {{ font-size:16px; font-weight:600; }}
        QLabel#detailFieldLabel {{ font-size:13px; color:{SECONDARY_TEXT}; }}
        QLabel#detailFieldValue, QLabel#detailParagraph {{ font-size:14px; color:{PRIMARY_TEXT}; }}
        QLineEdit, QComboBox {{ min-height:20px; padding:8px 10px;
            border:1px solid {BORDER}; border-radius:6px; background:white; font-size:14px; }}
        QComboBox {{ padding-right:30px; }}
        QLineEdit:focus, QComboBox:focus {{ border:1px solid {PRIMARY_BRAND}; }}
        QLineEdit[readOnly="true"] {{ background:{SURFACE_MUTED}; color:{PRIMARY_TEXT}; }}
        QLineEdit:disabled, QComboBox:disabled {{ background:#F3F5F7; color:#778B9B; border-color:#E1E7EC; }}
        QPushButton {{ min-height:20px; padding:8px 14px; border:1px solid {BORDER};
            border-radius:6px; background:white; font-size:14px; font-weight:400; }}
        QPushButton:focus {{ border:1px solid {PRIMARY_BRAND}; }}
        QPushButton[visualRole="primary"], QPushButton#exportWordReportButton {{
            background:{PRIMARY_BRAND}; border-color:{PRIMARY_BRAND}; color:white; font-weight:600; }}
        QPushButton[visualRole="primary"]:hover, QPushButton#exportWordReportButton:hover {{ background:#126BA9; }}
        QPushButton#deleteRecordButton {{ color:#B42318; background:white; }}
        QPushButton#openRecordRowButton {{ min-height:20px; padding:4px 6px; font-size:13px;
            color:{PRIMARY_BRAND}; border:1px solid transparent; background:transparent; font-weight:400; }}
        QPushButton#openRecordRowButton:hover {{ background:#EAF4FC; border-color:#D1E6F3; }}
        QPushButton#openRecordRowButton:focus {{ border-color:{PRIMARY_BRAND}; }}
        QPushButton:disabled, QPushButton[visualRole="primary"]:disabled,
        QPushButton#exportWordReportButton:disabled {{ background:#F3F5F7; color:#778B9B; border-color:#E1E7EC; }}
        QTableWidget {{ font-size:14px; background:white; border:1px solid {BORDER};
            gridline-color:#EAF0F5; selection-background-color:#EAF4FB; selection-color:{PRIMARY_TEXT}; }}
        QTableWidget QHeaderView::section {{ font-size:13px; font-weight:500; padding:9px 10px;
            color:#526B7E; background:{SURFACE_MUTED}; border:none; border-bottom:1px solid {BORDER}; }}
        QTableWidget::item {{ padding:8px 10px; }}
        QTableWidget:focus {{ border:1px solid {PRIMARY_BRAND}; }}
        QLabel#recordFrozenTotal {{ font-size:26px; font-weight:600; color:{PRIMARY_TEXT}; }}
        QLabel#recordFrozenIdentity {{ font-size:13px; color:{SECONDARY_TEXT}; }}
        QLabel#recordDetailHeading {{ font-size:18px; font-weight:600; }}
        QLabel#recordStatusBadge {{ border-radius:5px; padding:4px 7px; font-size:12px;
            font-weight:400; background:#E7F6F0; color:#168268; }}
        QLabel#recordStatusBadge[warning="true"] {{ background:#FFF5E1; color:#956420; }}
        QTabWidget#recordDetailTabs::pane {{ border:1px solid {BORDER}; border-radius:8px; }}
        QTabBar::tab {{ min-height:22px; padding:8px 16px; font-size:14px; font-weight:500; }}
        QCheckBox {{ font-size:14px; spacing:8px; }}
        QToolButton {{ font-size:13px; }}
        QLabel#excelWorkflowStatus {{ font-size:13px; color:#526B7E; }}
    """)


class BusinessCheckBox(QCheckBox):
    """Locally reinforce the checked indicator; native focus and events remain intact."""
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.isChecked():
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        box = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#FFFFFF"), 2.0,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        points = ((.22, .50), (.78, .50)) if self.checkState() == Qt.CheckState.PartiallyChecked else ((.22, .50), (.43, .72), (.79, .28))
        painter.drawPolyline(QPolygonF([QPointF(box.x()+box.width()*x, box.y()+box.height()*y) for x,y in points]))
        painter.end()
