"""Native SVG engines retain vector geometry at every display DPR.

Palette variants are shipped SVG assets, with identical geometry. There is no
Python QIconEngine ownership bridge and no runtime raster thumbnail/cache file.
"""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QLabel


def load_tinted_icon(path: Path, color: str, size: int = 18) -> QIcon:
    variant = path.parent / "tinted" / f"{path.stem}-{color.lstrip('#').lower()}.svg"
    return QIcon(str(variant if variant.is_file() else path))


class VectorIconLabel(QLabel):
    """Decorative vector icon rendered directly at its display DPR."""
    def __init__(self, icon, size, parent=None):
        super().__init__(parent)
        self._icon = icon
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        self._icon.paint(painter, self.rect())
        painter.end()
