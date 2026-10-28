"""Wheel protection scoped to actual editors, never to QApplication/window."""
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QWidget, QComboBox, QAbstractSpinBox, QDateTimeEdit

class _EditorWheelGuard(QObject):
    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.Wheel:
            return False
        if isinstance(watched, QComboBox) and watched.view().isVisible():
            return False
        if isinstance(watched, QDateTimeEdit):
            calendar = watched.calendarWidget()
            if calendar is not None and calendar.isVisible():
                return False
        event.ignore()
        return True

def protect_wheel_inputs(page):
    """Attach lifetime-owned guards once to existing single-value editors.

    Dynamic accounting editors also retain the existing page wheel handling.
    """
    for control in page.findChildren(QWidget):
        if not isinstance(control, (QComboBox, QAbstractSpinBox)):
            continue
        if getattr(control, "_editor_wheel_guard", None) is None:
            guard = _EditorWheelGuard(control)
            control._editor_wheel_guard = guard
            control.installEventFilter(guard)
