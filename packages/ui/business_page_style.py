"""Opt-in, presentation-only styles for the reference/import/record/settings pages.

Not an application theme. Styles are applied once; table reflow stays local.
No business state, timers, assets, dependencies, locale, or business policy.
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QPointF, QRectF
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
        self.verticalHeader().setMinimumSectionSize(44)
        self.verticalHeader().setDefaultSectionSize(48)
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
                height = max(48, self.rowHeight(row), self.sizeHintForRow(row))
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



class BusinessCheckBox(QCheckBox):
    """Locally reinforce the checked indicator; native focus and events remain intact."""
    def paintEvent(self, event):
        super().paintEvent(event)
        checked = self.checkState() != Qt.CheckState.Unchecked
        if not checked and not self.hasFocus():
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        box = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if checked:
            fill = QColor(PRIMARY_BRAND if self.isEnabled() else "#A7BAC8")
            painter.setPen(QPen(fill, 1))
            painter.setBrush(fill)
            painter.drawRoundedRect(QRectF(box).adjusted(.5, .5, -.5, -.5), 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            points = ((.22, .50), (.78, .50)) if self.checkState() == Qt.CheckState.PartiallyChecked else ((.22, .50), (.43, .72), (.79, .28))
            painter.drawPolyline(QPolygonF([QPointF(box.x()+box.width()*x, box.y()+box.height()*y) for x,y in points]))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(PRIMARY_BRAND), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 3, 3)
        painter.end()
