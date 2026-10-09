"""Small responsive input grid for the six-field fume business form."""
from __future__ import annotations

from PySide6.QtCore import Qt
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
        columns = 3 if self.width() >= self._three_column_width else 2
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
