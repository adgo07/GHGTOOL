from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from shiboken6 import isValid


def dispose_test_widget(widget: QWidget) -> None:
    """Destroy an owned fixture after its original close/exit checks.

    Closing hides a QWidget; it does not release its children or popups.
    Dispatch requested DeferredDelete events after assertions have completed.
    Other live windows are never scheduled for deletion, and no product/layout
    refresh is forced. This also finishes earlier explicit deleteLater calls.
    """
    if not isValid(widget):
        return
    name = widget.objectName()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(widget, QEvent.Type.DeferredDelete)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    if isValid(widget):
        raise AssertionError(f"测试夹具未完成销毁：{name}")


def tree_items(tree: QTreeWidget) -> list[QTreeWidgetItem]:
    items: list[QTreeWidgetItem] = []

    def visit(parent: QTreeWidgetItem | None) -> None:
        count = tree.topLevelItemCount() if parent is None else parent.childCount()
        for index in range(count):
            item = tree.topLevelItem(index) if parent is None else parent.child(index)
            items.append(item)
            visit(item)

    visit(None)
    return items


def tree_texts(tree: QTreeWidget) -> list[str]:
    return [item.text(0) for item in tree_items(tree)]
