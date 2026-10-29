"""Product window preferences, independent of business project recovery."""
import json
import logging
from PySide6.QtCore import QObject, QRect, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from packages.core.models import SettingEntry, Settings

KEY = "desktop.window_geometry.v1"
_LOG = logging.getLogger(__name__)

def bounded_geometry(rect: QRect, available: QRect, frame_width=0, frame_height=0) -> QRect:
    """Fit a client rectangle including non-client chrome into one work area."""
    width = max(1, min(rect.width(), available.width()-frame_width))
    height = max(1, min(rect.height(), available.height()-frame_height))
    x = min(max(rect.x(), available.left()), available.right()+1-width-frame_width)
    y = min(max(rect.y(), available.top()), available.bottom()+1-height-frame_height)
    return QRect(x, y, width, height)

class WindowGeometry(QObject):
    def __init__(self, window, repository=None):
        super().__init__(window)
        self.window = window
        self.repository = repository
        self._maximized = False
        self._first_launch = True
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        rect = QRect(0, 0, 1280, 800)
        rect.moveCenter(area.center())
        if repository is not None:
            try:
                values = {e.key:e.value for e in repository.load().entries}
                saved = json.loads(values.get(KEY, "null"))
                if isinstance(saved, dict):
                    coords = saved.get("normal")
                    if isinstance(coords, list) and len(coords) == 4 and all(type(v) is int and abs(v) < 2**30 for v in coords) and coords[2] > 0 and coords[3] > 0:
                        rect = QRect(*coords)
                        self._first_launch = False
                        screen = QGuiApplication.screenAt(rect.center()) or screen
                        area = screen.availableGeometry()
                        self._maximized = bool(saved.get("maximized", False))
            except (ValueError, TypeError, KeyError, OSError, RuntimeError):
                _LOG.warning("窗口位置设置无法读取，使用默认位置", exc_info=True)
        window.setMinimumSize(min(960, area.width()), min(600, area.height()))
        window.setGeometry(bounded_geometry(rect, area))
        self._initial = True

    def shown(self):
        QTimer.singleShot(0, self.window, self._settle_initial)

    def _settle_initial(self):
        self.fit()
        if self._initial and self._first_launch:
            area = self.window.screen().availableGeometry()
            frame = self.window.frameGeometry()
            frame.moveCenter(area.center())
            self.window.move(frame.topLeft())
        if self._initial:
            self._initial = False
            if self._maximized:
                self.window.showMaximized()
        handle = self.window.windowHandle()
        if handle is not None and not getattr(self, "_connected", False):
            self._connected = True
            handle.screenChanged.connect(self._screen_changed)
            for screen in QGuiApplication.screens():
                screen.availableGeometryChanged.connect(self._screen_changed)
            QGuiApplication.instance().screenRemoved.connect(self._screen_changed)

    def _screen_changed(self, *_args):
        self.fit()

    def fit(self):
        w = self.window
        screen = QGuiApplication.screenAt(w.frameGeometry().center()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        frame = w.frameGeometry()
        dx = max(0, frame.width()-w.width())
        dy = max(0, frame.height()-w.height())
        w.setMinimumSize(min(960, max(1, area.width()-dx)), min(600, max(1, area.height()-dy)))
        if not w.isMaximized():
            # QWidget.pos() is the top-left of the outer frame for a window.
            client = QRect(w.pos(), w.size())
            fitted = bounded_geometry(client, area, dx, dy)
            w.resize(fitted.size())
            w.move(fitted.topLeft())

    def save(self):
        if self.repository is None:
            return
        w = self.window
        rect = w.normalGeometry() if w.isMaximized() else w.geometry()
        payload = json.dumps({"normal":[rect.x(),rect.y(),rect.width(),rect.height()], "maximized":w.isMaximized()})
        try:
            current = self.repository.load()
            self.repository.save(Settings(settings_id=current.settings_id, entries=(SettingEntry(KEY, payload),)))
        except (OSError, RuntimeError):
            _LOG.warning("窗口位置设置无法保存", exc_info=True)
