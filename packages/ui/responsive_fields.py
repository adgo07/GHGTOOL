"""Small responsive input grid for the six-field fume business form."""
from __future__ import annotations

from PySide6.QtCore import Qt, QObject, QEvent, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget


class ResponsiveFieldGrid(QWidget):
    """Keep each label with its input while adapting between two and three columns."""

    def __init__(self, parent: QWidget | None = None, *, three_column_width: int = 900):
        super().__init__(parent)
        self._three_column_width = three_column_width
        self._cells: list[QWidget] = []
        self._columns = 0
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(8)

    def add_field(self, label: str, field: QWidget) -> None:
        cell = QWidget(self)
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        caption = QLabel(label, cell)
        caption.setWordWrap(True)
        caption.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(caption)
        layout.addWidget(field)
        self._cells.append(cell)
        self._relayout(force=True)

    def _relayout(self, *, force: bool = False) -> None:
        columns = 3 if self.width() >= self._three_column_width else (2 if self.width() >= 540 else 1)
        if columns == self._columns and not force:
            return
        while self._grid.count():
            self._grid.takeAt(0)
        for column in range(3):
            self._grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, cell in enumerate(self._cells):
            self._grid.addWidget(cell, index // columns, index % columns)
        self._columns = columns
        self.updateGeometry()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._relayout()


class _GridResizeFilter(QObject):
    def __init__(self, grid, host):
        super().__init__(host)
        self.grid = grid
        self.pending = False

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Hide, QEvent.Type.LayoutRequest):
            if not self.pending:
                self.pending = True
                QTimer.singleShot(0, self, self.refresh)
        return False

    def refresh(self):
        self.pending = False
        self.grid.reflow()


class AdaptiveFieldLayout(QGridLayout):
    """Reflow existing field cells; no input state or widget reconstruction.

    Only actual available editor width determines the column count. Hidden
    conditional fields do not leave holes. Resize/visibility events coalesce.
    """
    def __init__(self, host, *, maximum_columns=3):
        super().__init__(host)
        self.maximum_columns = maximum_columns
        self.cells = []
        self._signature = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setHorizontalSpacing(16)
        self.setVerticalSpacing(10)
        self._filter = _GridResizeFilter(self, host)
        host.installEventFilter(self._filter)

    def set_cells(self, cells):
        for cell in cells:
            if cell not in self.cells:
                cell.installEventFilter(self._filter)
                self.addWidget(cell)
        self.cells = list(cells)
        self.reflow()

    def reflow(self):
        host = self.parentWidget()
        if host is None:
            return
        columns = min(self.maximum_columns, 3 if host.width() >= 820 else (2 if host.width() >= 540 else 1))
        cells = [cell for cell in self.cells if not cell.isHidden()]
        signature = (columns, tuple(map(id, cells)))
        changed = signature != self._signature
        if changed:
            self._signature = signature
            while self.count():
                self.takeAt(0)
            for col in range(3):
                self.setColumnStretch(col, int(col < columns))
            for index, cell in enumerate(cells):
                self.addWidget(cell, index // columns, index % columns, Qt.AlignmentFlag.AlignTop)
        # The shell sizes its single scroll host from sizeHint. Reserve the
        # complete reflowed height before it measures the page; otherwise Qt
        # can compress nested labels/inputs during a wide-to-narrow transition.
        required = max(self.minimumSize().height(), self.heightForWidth(host.width()) if self.hasHeightForWidth() else self.sizeHint().height())
        if host.minimumHeight() != required:
            host.setMinimumHeight(required)
            changed = True
        if changed:
            host.updateGeometry()
            # This editor lives several levels below the shell's measured
            # page. Invalidate the existing ancestor layouts bottom-up so a
            # single coalesced shell pass sees the new natural height.
            ancestor = host.parentWidget()
            while ancestor is not None:
                if ancestor.layout() is not None:
                    ancestor.layout().invalidate()
                ancestor.updateGeometry()
                ancestor = ancestor.parentWidget()
