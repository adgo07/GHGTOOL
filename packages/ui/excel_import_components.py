"""Presentation-only components for the Appendix B workbook import page."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .design_tokens import (
    BORDER,
    CARD_BACKGROUND,
    CARD_BORDER,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    STATUS_ABOLISHED,
    STATUS_CURRENT,
    STATUS_UPCOMING,
    SURFACE_MUTED,
)


def create_excel_import_section(
    object_name: str,
    title: str,
    parent: QWidget,
) -> tuple[QFrame, QVBoxLayout]:
    """Create a compact, consistently styled task region for Excel import."""

    section = QFrame(parent)
    section.setObjectName(object_name)
    section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    section.setStyleSheet(
        f"QFrame#{object_name} {{ background: {CARD_BACKGROUND}; border: 1px solid {CARD_BORDER}; border-radius: 8px; }}\n"
        "QLabel#excelImportSectionTitle { font-size: 15px; font-weight: 600; }"
    )
    layout = QVBoxLayout(section)
    layout.setContentsMargins(14, 10, 14, 12)
    layout.setSpacing(8)
    heading = QLabel(title, section)
    heading.setObjectName("excelImportSectionTitle")
    layout.addWidget(heading)
    return section, layout


class ExcelImportPreviewPanel(QFrame):
    """Show workbook/unit checks and cell-location details without business logic."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("excelImportPreviewPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.summary = QLabel("尚未检查工作簿。", self)
        self.summary.setObjectName("excelImportSummary")
        self.summary.setWordWrap(True)
        self.summary.setAccessibleName("工作簿检查状态")
        layout.addWidget(self.summary)

        self.units = QTableWidget(0, 3, self)
        self.units.setObjectName("excelImportUnitTable")
        self.units.setHorizontalHeaderLabels(("核算单元", "检查状态", "预览排放总量"))
        self.units.verticalHeader().setVisible(False)
        self.units.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.units.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.units.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.units.setAlternatingRowColors(True)
        self.units.setWordWrap(True)
        self.units.setMinimumHeight(66)
        self.units.setMaximumHeight(190)
        header = self.units.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.units.setStyleSheet(
            f"QTableWidget#excelImportUnitTable {{ background: {CARD_BACKGROUND}; border: 1px solid {BORDER}; gridline-color: {BORDER}; selection-background-color: {SURFACE_MUTED}; selection-color: {PRIMARY_TEXT}; }}\n"
            f"QTableWidget#excelImportUnitTable QHeaderView::section {{ background: {SURFACE_MUTED}; color: {SECONDARY_TEXT}; border: none; border-bottom: 1px solid {BORDER}; padding: 6px; font-weight: 600; }}"
        )
        self.units.setAccessibleName("核算单元检查结果")
        self.units.setAccessibleDescription("每行显示一个核算单元的检查状态和非正式预览总量；选择行可查看错误位置和提醒。")
        layout.addWidget(self.units)

        self.details = QTextEdit(self)
        self.details.setObjectName("excelImportPreview")
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(96)
        self.details.setMaximumHeight(130)
        self.details.setPlaceholderText("选择核算单元后，这里显示需要修正的单元格位置和导入提醒。")
        self.details.setAccessibleName("导入检查详情")
        self.details.setStyleSheet(
            f"QTextEdit#excelImportPreview {{ background: {SURFACE_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px; color: {PRIMARY_TEXT}; }}"
        )
        layout.addWidget(self.details)

    def set_summary(self, text: str, *, state: str = "info") -> None:
        self.summary.setText(text)
        color = {
            "success": STATUS_CURRENT,
            "error": STATUS_ABOLISHED,
            "warning": STATUS_UPCOMING,
        }.get(state, SECONDARY_TEXT)
        self.summary.setStyleSheet(f"color: {color}; font-weight: 600; padding: 2px 0;")

    def set_units(
        self,
        rows: Iterable[tuple[str, str, str]],
        *,
        selectable: bool = True,
    ) -> None:
        values = tuple(rows)
        self.units.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
            if selectable
            else QAbstractItemView.SelectionMode.NoSelection
        )
        self.units.setRowCount(len(values))
        for row_index, row_values in enumerate(values):
            for column_index, text in enumerate(row_values):
                item = QTableWidgetItem(text)
                flags = Qt.ItemFlag.ItemIsEnabled
                if selectable:
                    flags |= Qt.ItemFlag.ItemIsSelectable
                item.setFlags(flags)
                self.units.setItem(row_index, column_index, item)
            self.units.setRowHeight(row_index, 34)
        self.units.setFixedHeight(min(190, 66 + max(0, len(values) - 1) * 34))
        self.units.clearSelection()
        if values and selectable:
            self.units.selectRow(0)

    def set_details(self, text: str) -> None:
        self.details.setPlainText(text)


__all__ = ["ExcelImportPreviewPanel", "create_excel_import_section"]
