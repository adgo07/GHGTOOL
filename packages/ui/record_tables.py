"""Compact Qt views for the frozen business report tables on saved records."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from packages.application.reporting.types import ReportCell, ReportSection, ReportTable


def _cell_text(cell: ReportCell) -> str:
    value = cell.value
    if cell.unit:
        value = f"{value} {cell.unit}".strip()
    if cell.source:
        value = f"{value}（{cell.source}）" if value else cell.source
    return value


def _header_rows(report: ReportTable) -> tuple[tuple[ReportCell, ...], ...]:
    if report.header_rows:
        return tuple(row.cells for row in report.header_rows)
    return (tuple(ReportCell(value) for value in report.columns),)


def _covered_cells(merges: Iterable[tuple[int, int, int, int]]) -> set[tuple[int, int]]:
    return {
        (row, column)
        for top, left, bottom, right in merges
        for row in range(top, bottom + 1)
        for column in range(left, right + 1)
        if (row, column) != (top, left)
    }


def _apply_merges(
    widget: QTableWidget,
    merges: Iterable[tuple[int, int, int, int]],
    *,
    row_offset: int = 0,
) -> None:
    for top, left, bottom, right in merges:
        widget.setSpan(top + row_offset, left, bottom - top + 1, right - left + 1)


def _column_labels(report: ReportTable) -> tuple[str, ...]:
    rows = _header_rows(report)
    labels: list[str] = []
    for column in range(len(report.columns)):
        label = next(
            (row[column].value for row in reversed(rows) if column < len(row) and row[column].value),
            report.columns[column],
        )
        labels.append(label)
    return tuple(labels)


class ReportTableCard(QFrame):
    """A report table rendered with its frozen headings, merges, and notes."""

    def __init__(self, report: ReportTable, parent: QWidget | None = None) -> None:
        from PySide6.QtGui import QColor
        super().__init__(parent)
        self.report = report
        self.setObjectName("recordReportTableCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame#recordReportTableCard { border: 1px solid #DCE7EF; border-radius: 7px; background: white; }"
            "QLabel#recordReportTableTitle { color: #18364F; font-size: 16px; font-weight: 600; }"
            "QLabel#recordReportContext { color: #5B7287; font-size: 13px; }"
            "QLabel#recordReportFootnote { color: #5B6874; font-size: 13px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        if report.context_label:
            context = QLabel(report.context_label, self)
            context.setObjectName("recordReportContext")
            context.setWordWrap(True)
            layout.addWidget(context)
        title = QLabel(report.title, self)
        title.setObjectName("recordReportTableTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        headers = _header_rows(report)
        header_count = len(headers)
        row_count = header_count + len(report.rows)
        column_count = len(report.columns)
        table = QTableWidget(row_count, column_count, self)
        table.setObjectName("recordBusinessTable")
        table.setProperty("reportTableId", report.table_id)
        table.setAccessibleName(report.title)
        table.setAccessibleDescription("来自已保存核算记录的只读报告表。来源类别和依据可通过单元格提示及本页业务依据查看。")
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        table.setTabKeyNavigation(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)
        table.setTextElideMode(Qt.TextElideMode.ElideNone)
        table.verticalHeader().setVisible(False)
        table.setHorizontalHeaderLabels(_column_labels(report))
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.setStyleSheet(
            "QTableWidget#recordBusinessTable { font-size: 14px; gridline-color: #DCE5EC; border: 1px solid #DCE5EC; }"
            "QTableWidget#recordBusinessTable::item { padding: 7px 8px; }"
            "QTableWidget#recordBusinessTable::item:selected { background: #EDF5FA; color: #18364F; }"
        )

        hidden_header_cells = _covered_cells(report.header_merges)
        for row_index, row in enumerate(headers):
            for column_index in range(column_count):
                if (row_index, column_index) in hidden_header_cells:
                    continue
                cell = row[column_index] if column_index < len(row) else ReportCell()
                item = QTableWidgetItem(_cell_text(cell))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setBackground(QColor("#F2F7FB"))
                table.setItem(row_index, column_index, item)

        hidden_body_cells = _covered_cells(report.body_merges)
        visible_headers = _column_labels(report)
        for row_index, row in enumerate(report.rows):
            for column_index in range(column_count):
                if (row_index, column_index) in hidden_body_cells:
                    continue
                cell = row.cells[column_index] if column_index < len(row.cells) else ReportCell()
                item = QTableWidgetItem(_cell_text(cell))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                row_context = " / ".join(
                    value.value for value in row.cells[: min(3, len(row.cells))]
                    if value.value and value.value not in {"—", "不适用"}
                )
                accessible_text = f"{visible_headers[column_index]}：{_cell_text(cell)}"
                if row_context:
                    accessible_text = f"{row_context}；{accessible_text}"
                item.setData(Qt.ItemDataRole.AccessibleTextRole, accessible_text)
                if cell.source_detail:
                    from .record_experience import business_source_text
                    item.setToolTip(business_source_text(cell.source_detail))
                    item.setData(
                        Qt.ItemDataRole.AccessibleDescriptionRole,
                        business_source_text(cell.source_detail),
                    )
                table.setItem(header_count + row_index, column_index, item)

        _apply_merges(table, report.header_merges)
        _apply_merges(table, report.body_merges, row_offset=header_count)
        weights = report.column_weights or tuple(1.0 for _ in range(column_count))
        total_weight = sum(max(0.1, value) for value in weights)
        target_width = max(620, min(1280, 92 * column_count))
        table_width = 0
        table.ensurePolished()
        metrics = table.fontMetrics()
        for column, weight in enumerate(weights):
            width = max(66, min(240, round(target_width * max(0.1, weight) / total_weight)))
            # Preserve frozen header text and merges; size only the visual cell.
            header_width = max((metrics.horizontalAdvance(line)
                for row in range(header_count)
                if table.item(row, column) is not None and table.columnSpan(row, column) == 1
                for line in table.item(row, column).text().splitlines()), default=0)
            width = max(width, min(240, header_width + 40))
            table.setColumnWidth(column, width)
            table_width += width
        table.setMinimumWidth(table_width + 4)
        table.resizeRowsToContents()
        content_height = table.horizontalHeader().height() + table.verticalHeader().length() + 6
        table.setMinimumHeight(max(90, content_height))
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(table)
        self.table_widget = table

        for footnote in (*report.footnotes, *(row.note for row in report.rows if row.note)):
            label = QLabel(footnote, self)
            label.setObjectName("recordReportFootnote")
            label.setWordWrap(True)
            layout.addWidget(label)


class RecordReportTab(QWidget):
    """Scrollable read-only report table pane, with a collapsed audit section."""

    def __init__(
        self,
        object_name: str,
        *,
        include_audit: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.include_audit = include_audit
        self.report_table_cards: list[ReportTableCard] = []
        self.business_basis_labels: list[QLabel] = []
        self.setObjectName(object_name)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName(f"{object_name}ScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget(self.scroll_area)
        self.content.setObjectName(f"{object_name}Content")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content)
        outer.addWidget(self.scroll_area)
        self.audit_text: QTextEdit | None = None
        self.audit_table: QTableWidget | None = None
        self.audit_panel: QWidget | None = None
        self.audit_toggle: QToolButton | None = None
        self._clear_layout()

    def isReadOnly(self) -> bool:
        """Expose the pane's read-only contract to accessibility and UI tests."""
        return True

    def _clear_layout(self) -> None:
        while (item := self.content_layout.takeAt(0)) is not None:
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        self.report_table_cards = []
        self.business_basis_labels = []
        self.audit_text = None
        self.audit_table = None
        self.audit_panel = None
        self.audit_toggle = None

    def clear(self, message: str) -> None:
        self._clear_layout()
        label = QLabel(message, self.content)
        label.setObjectName("recordReportEmptyMessage")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)
        self.content_layout.addStretch(1)

    def set_sections(
        self,
        sections: Sequence[ReportSection],
        *,
        notices: Sequence[str] = (),
        audit_sections: Sequence[tuple[str, str]] = (),
        audit_tables: Sequence[ReportTable] = (),
        business_sections: Sequence[tuple[str, str]] = (),
    ) -> None:
        self._clear_layout()
        sections = tuple(sections)
        for notice in dict.fromkeys(item for item in notices if item):
            label = QLabel(notice, self.content)
            label.setObjectName("recordReportNotice")
            label.setWordWrap(True)
            label.setStyleSheet(
                "QLabel#recordReportNotice { padding: 8px 10px; color: #765316; "
                "background: #FFF7E8; border: 1px solid #F0D9A8; border-radius: 6px; }"
            )
            self.content_layout.addWidget(label)

        all_tables = tuple(audit_tables) or tuple(table for section in sections for table in section.tables)
        for section in sections:
            if section.title:
                heading = QLabel(section.title, self.content)
                heading.setObjectName("recordReportSectionTitle")
                heading.setWordWrap(True)
                heading.setStyleSheet("font-size: 17px; font-weight: 600; color: #18364F; padding-top: 3px;")
                self.content_layout.addWidget(heading)
            for report in section.tables:
                card = ReportTableCard(report, self.content)
                self.report_table_cards.append(card)
                self.content_layout.addWidget(card)
            for note in section.notes:
                note_label = QLabel(note, self.content)
                note_label.setObjectName("recordReportSectionNote")
                note_label.setWordWrap(True)
                note_label.setStyleSheet("color: #536A7B; font-size: 13px; padding: 1px 3px;")
                self.content_layout.addWidget(note_label)

        for title, content in business_sections:
            if not content:
                continue
            heading = QLabel(title, self.content)
            heading.setObjectName("recordBusinessBasisHeading")
            heading.setWordWrap(True)
            heading.setStyleSheet("font-size: 16px; font-weight: 600; color: #18364F; padding-top: 8px;")
            self.content_layout.addWidget(heading)
            label = QLabel(content, self.content)
            label.setObjectName("recordBusinessBasisText")
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            label.setStyleSheet("font-size: 14px; color: #233749; padding: 3px;")
            self.content_layout.addWidget(label)
            self.business_basis_labels.append(label)
        if self.include_audit:
            self._add_audit_panel(all_tables, audit_sections)
        self.content_layout.addStretch(1)

    def _add_audit_panel(
        self,
        tables: Sequence[ReportTable],
        audit_sections: Sequence[tuple[str, str]],
    ) -> None:
        audit_rows: list[tuple[str, str, str, str]] = []
        for report in tables:
            header_labels = _column_labels(report)
            for row in report.rows:
                row_label = " / ".join(
                    cell.value for cell in row.cells[: min(3, len(row.cells))]
                    if cell.value and cell.value not in {"—", "不适用"}
                ) or "本表记录"
                for column, cell in enumerate(row.cells):
                    if cell.source_detail:
                        audit_rows.append((
                            report.title,
                            row_label,
                            header_labels[column] if column < len(header_labels) else report.columns[column],
                            cell.source_detail,
                        ))

        toggle = QToolButton(self.content)
        toggle.setObjectName("recordReportAuditToggle")
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toggle.setArrowType(Qt.ArrowType.RightArrow)
        toggle.setText(f"查看来源与计算审计（{len(audit_rows)} 项来源明细）")
        toggle.setAccessibleName("展开来源与计算审计")
        toggle.setStyleSheet(
            "QToolButton#recordReportAuditToggle { color: #12649A; border: none; padding: 8px 3px; "
            "font-size: 12px; font-weight: 650; text-align: left; }"
        )
        self.content_layout.addWidget(toggle)

        panel = QWidget(self.content)
        panel.setObjectName("recordReportAuditPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(6, 2, 6, 8)
        panel_layout.setSpacing(8)
        if audit_rows:
            audit_table = QTableWidget(len(audit_rows), 4, panel)
            audit_table.setObjectName("recordReportAuditTable")
            audit_table.setHorizontalHeaderLabels(("业务表", "行项目", "项目", "来源及依据"))
            audit_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            audit_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            audit_table.setWordWrap(True)
            audit_table.setAlternatingRowColors(True)
            audit_table.verticalHeader().setVisible(False)
            audit_table.horizontalHeader().setStretchLastSection(True)
            audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            audit_table.horizontalHeaderItem(3).setText("来源及依据")
            for row_index, values in enumerate(audit_rows):
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    audit_table.setItem(row_index, column, item)
            audit_table.resizeRowsToContents()
            audit_height = audit_table.horizontalHeader().height() + audit_table.verticalHeader().length() + 6
            audit_table.setMinimumHeight(max(100, audit_height))
            panel_layout.addWidget(audit_table)
            self.audit_table = audit_table
        if audit_sections:
            audit_text = QTextEdit(panel)
            audit_text.setObjectName("recordAuditText")
            audit_text.setReadOnly(True)
            audit_text.setMinimumHeight(120)
            audit_text.setMaximumHeight(300)
            audit_text.setPlainText("\n\n".join(
                f"{title}\n{content}" for title, content in audit_sections if content
            ))
            panel_layout.addWidget(audit_text)
            self.audit_text = audit_text
        if not audit_rows and not audit_sections:
            empty = QLabel("该记录没有可展开的额外来源审计信息。", panel)
            empty.setWordWrap(True)
            panel_layout.addWidget(empty)
        panel.setVisible(False)
        self.content_layout.addWidget(panel)
        toggle.toggled.connect(lambda checked: self._toggle_audit(checked, toggle, panel))
        self.audit_panel = panel
        self.audit_toggle = toggle

    @staticmethod
    def _toggle_audit(checked: bool, toggle: QToolButton, panel: QWidget) -> None:
        panel.setVisible(checked)
        toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        toggle.setAccessibleName("收起来源与计算审计" if checked else "展开来源与计算审计")


__all__ = ["RecordReportTab", "ReportTableCard"]
