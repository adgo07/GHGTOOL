from __future__ import annotations

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


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
