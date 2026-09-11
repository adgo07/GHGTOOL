"""Runtime tinting for the shared SVG navigation icons."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


def load_tinted_icon(path: Path, color: str, size: int = 18) -> QIcon:
    """Load an SVG icon and apply one tokenized foreground color."""

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return QIcon()
    pixmap = pixmap.scaled(
        QSize(size, size),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return QIcon(pixmap)
