"""Render the original transparent logo at the current screen DPR."""
from pathlib import Path
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

class BrandLogo(QLabel):
    def __init__(self, path: Path | None, parent=None):
        super().__init__(parent)
        self._source = QPixmap(str(path)) if path else QPixmap()
        self._render_key = None
        self.setFixedSize(180, 48)
        self.setAccessibleName("青舟节能")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.refresh_pixmap()

    def refresh_pixmap(self):
        ratio = self.devicePixelRatioF()
        key = (self.width(), self.height(), ratio)
        if key == self._render_key:
            return
        self._render_key = key
        if self._source.isNull():
            self.setText("青舟节能")
            return
        target = QSize(round(self.width()*ratio), round(self.height()*ratio))
        pixmap = self._source.scaled(target, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
        pixmap.setDevicePixelRatio(ratio)
        self.setPixmap(pixmap)

    def paintEvent(self, event):
        # Paint also follows cross-screen DPR changes without scaling a cached thumbnail.
        self.refresh_pixmap()
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_pixmap()
