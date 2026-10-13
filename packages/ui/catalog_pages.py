"""G04 catalog pages backed by the application query service."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from enum import Enum

from PySide6.QtCore import QEvent, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import ParameterType, ReviewStatus
from packages.core.models import ValueType
from packages.standards.carbon_material import ALGORITHM_VERSION, STANDARD_ID, steam_reference_table_rows
from packages.standards.catalog import (
    CatalogStandardType,
    CatalogStatus,
    ParameterFactorResult,
    ParameterViewMode,
    StandardCatalogRecord,
    StandardDetail,
)

from .pages import BasePage, Navigate, _card
from .design_tokens import BORDER, CARD_BACKGROUND, PRIMARY_BRAND, PRIMARY_TEXT, SECONDARY_TEXT, SURFACE_MUTED
from .view_models import AppRoute


def _date_text(value: object) -> str:
    return value.isoformat() if value is not None else "—"


def _decimal_text(value: Decimal | None) -> str:
    return format(value, "f") if value is not None else "—"


def _configure_table(table: QTableWidget, headers: Iterable[str]) -> None:
    header_values = tuple(headers)
    table.setColumnCount(len(header_values))
    table.setHorizontalHeaderLabels(header_values)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(False)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.setWordWrap(True)
    table.setObjectName("catalogTable")


def _replace_layout_contents(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.deleteLater()


def _detail_section(
    title: str,
    parent: QWidget,
    rows: Iterable[tuple[str, str]],
) -> QFrame:
    card, layout = _card(title, parent)
    for label_text, value_text in rows:
        row = QWidget(card)
        row_layout = QGridLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setHorizontalSpacing(20)
        row_layout.setVerticalSpacing(8)
        label = QLabel(label_text, row)
        label.setObjectName("detailFieldLabel")
        value = QLabel(value_text or "—", row)
        value.setObjectName("detailFieldValue")
        value.setWordWrap(True)
        row_layout.addWidget(label, 0, 0)
        row_layout.addWidget(value, 0, 1)
        row_layout.setColumnStretch(1, 1)
        layout.addWidget(row)
    return card


def _text_section(title: str, parent: QWidget, text: str) -> QFrame:
    card, layout = _card(title, parent)
    description = QLabel(text, card)
    description.setObjectName("detailParagraph")
    description.setWordWrap(True)
    layout.addWidget(description)
    return card


def _enum_data(value: object, enum_type: type[Enum]) -> Enum | None:
    """Restore a domain enum after Qt converts str-enum user data to text."""

    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        try:
            return enum_type(value)
        except ValueError:
            return None
    return None


class StandardLibraryPage(BasePage):
    """Searchable standard list and independent, read-only detail view."""

    accounting_requested = Signal(str)

    def __init__(
        self,
        service: CatalogQueryService,
        navigate: Navigate,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.STANDARDS, parent)
        self._service = service
        self.selected_standard_id: str | None = None
        self._standards_by_id: dict[str, StandardCatalogRecord] = {}
        self._saved_list_scroll: tuple[int | None, int, int] | None = None
        self._build_page()
        self._refresh()

    def _build_page(self) -> None:
        self.add_header("标准库", "查看已登记标准、适用范围与核算要求")
        self.page_title = self.findChild(QLabel, "pageTitle")
        self.page_description = self.findChild(QLabel, "pageDescription")

        self.view_stack = QStackedWidget(self)
        self.view_stack.setObjectName("standardViewStack")

        self.list_view = QWidget(self.view_stack)
        self.list_view.setObjectName("standardListView")
        list_layout = QVBoxLayout(self.list_view)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(16)

        filters, filters_layout = _card("搜索和筛选", self.list_view)
        search = QLineEdit(filters)
        search.setObjectName("standardSearch")
        search.setPlaceholderText("按标准编号、名称或适用对象搜索")
        filters_layout.addWidget(search)
        self.search_input = search

        self.status_filter = QComboBox(filters)
        self.status_filter.setObjectName("standardStatusFilter")
        for status, label in (
            (CatalogStatus.ALL, "全部状态"),
            (CatalogStatus.CURRENT, "现行"),
            (CatalogStatus.UPCOMING, "即将实施"),
            (CatalogStatus.ABOLISHED, "已废止"),
            (CatalogStatus.UNKNOWN, "待核对"),
        ):
            self.status_filter.addItem(label, status)
        filters_layout.addWidget(self.status_filter)
        list_layout.addWidget(filters)

        list_card, list_card_layout = _card("标准列表", self.list_view)
        self.result_summary = QLabel(list_card)
        self.result_summary.setObjectName("secondaryText")
        list_card_layout.addWidget(self.result_summary)
        self.standard_table = QTableWidget(list_card)
        _configure_table(
            self.standard_table,
            ("标准编号", "标准名称", "标准状态", "实施日期", "软件支持"),
        )
        self.standard_table.setObjectName("standardLibraryTable")
        self.standard_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.standard_table.verticalHeader().setDefaultSectionSize(46)
        self.standard_table.setStyleSheet(f"""
            QTableWidget#standardLibraryTable {{
                color: {PRIMARY_TEXT}; font-size: 13px;
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                selection-background-color: #E6F4FB;
                selection-color: {PRIMARY_TEXT};
            }}
            QTableWidget#standardLibraryTable::item {{ padding: 7px 9px; }}
            QTableWidget#standardLibraryTable::item:hover {{ background: #F4FAFE; }}
            QTableWidget#standardLibraryTable QHeaderView::section {{
                background: {SURFACE_MUTED}; color: {SECONDARY_TEXT};
                border: none; border-bottom: 1px solid {BORDER};
                padding: 10px 9px; font-size: 12px; font-weight: 650;
            }}
        """)
        standard_header = self.standard_table.horizontalHeader()
        standard_header.setStretchLastSection(False)
        for column, width in enumerate((180, 460, 112, 124, 190)):
            standard_header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.standard_table.setColumnWidth(column, width)
        standard_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.standard_table.setMouseTracking(True)
        self.standard_table.viewport().setMouseTracking(True)
        self.standard_table.viewport().installEventFilter(self)
        self.standard_table.setAccessibleName("标准列表")
        self.standard_table.setAccessibleDescription("选择标准编号或名称，再按 Enter 键打开标准详情。")
        self.standard_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.standard_table.setMinimumHeight(250)
        list_card_layout.addWidget(self.standard_table)
        list_layout.addWidget(list_card)
        list_layout.addStretch(1)
        self.view_stack.addWidget(self.list_view)

        self.detail_host = QWidget(self.view_stack)
        self.detail_host.setObjectName("standardDetailHost")
        self.detail_layout = QVBoxLayout(self.detail_host)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(16)
        self.view_stack.addWidget(self.detail_host)
        self.view_stack.setCurrentWidget(self.list_view)
        self.body_layout.addWidget(self.view_stack)
        self.body_layout.addStretch(1)

        search.textChanged.connect(self._refresh)
        self.status_filter.currentIndexChanged.connect(self._refresh)
        self.standard_table.cellClicked.connect(self._open_detail_from_cell)
        self.standard_table.cellActivated.connect(self._open_detail_from_cell)

    @staticmethod
    def _software_support_label(standard: StandardCatalogRecord) -> str:
        if (
            standard.standard_id == STANDARD_ID
            and standard.calculation_status == "IMPLEMENTED"
        ):
            return "已实现核算（未正式支持）"
        if (
            standard.calculation_status == "COMMON_RULES_ONLY"
            and standard.standard_type is CatalogStandardType.COMMON_RULES
        ):
            return "配套通则"
        return "核算未开放"

    def _refresh(self) -> None:
        status = _enum_data(self.status_filter.currentData(), CatalogStatus)
        results = self._service.search_standards(
            self.search_input.text(),
            status=status if isinstance(status, CatalogStatus) else CatalogStatus.ALL,
        )
        self._standards_by_id = {
            standard.standard_id: standard for standard, _, _ in results
        }
        self.selected_standard_id = None
        self.standard_table.setRowCount(0)
        for row_number, (standard, visible_status, _) in enumerate(results):
            self.standard_table.insertRow(row_number)
            values = (
                standard.standard_number,
                standard.standard_name,
                self._service.status_label(visible_status),
                _date_text(standard.implementation_date),
                self._software_support_label(standard),
            )
            for column, value in enumerate(values):
                if column == 2:
                    badge = QLabel(value, self.standard_table)
                    badge.setObjectName("standardStatusBadge")
                    badge.setAccessibleName(f"标准状态：{value}")
                    badge.setAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                    colors = {
                        CatalogStatus.CURRENT: ("#e7f6f0", "#168268"),
                        CatalogStatus.UPCOMING: ("#fff5e1", "#956420"),
                        CatalogStatus.ABOLISHED: ("#f0f3f6", "#647788"),
                        CatalogStatus.UNKNOWN: ("#f0f3f6", "#647788"),
                    }
                    background, foreground = colors.get(
                        visible_status, ("#f0f3f6", "#647788")
                    )
                    badge.setStyleSheet(
                        "QLabel#standardStatusBadge {"
                        f"background: {background}; color: {foreground};"
                        "border-radius: 7px; padding: 3px 8px; font-size: 11px;"
                        "}"
                    )
                    self.standard_table.setCellWidget(row_number, column, badge)
                    continue
                item = QTableWidgetItem(value)
                if column in (0, 1):
                    item.setData(Qt.ItemDataRole.UserRole, standard.standard_id)
                    item.setData(
                        Qt.ItemDataRole.AccessibleTextRole,
                        f"{value}，按 Enter 键打开标准详情",
                    )
                    font = item.font()
                    font.setUnderline(False)
                    font.setWeight(QFont.Weight.DemiBold)
                    item.setFont(font)
                    item.setForeground(QColor("#12618D"))
                    item.setToolTip(f"{value}\n点击打开标准详情")
                self.standard_table.setItem(row_number, column, item)
        self.standard_table.resizeRowsToContents()
        self.result_summary.setText(
            f"共 {len(results)} 项标准" if results else "没有找到匹配的标准。"
        )
        self.standard_table.clearSelection()

    def _set_standard_hover(self, row: int, column: int) -> None:
        previous = getattr(self, "_hovered_standard_cell", None)
        if previous is not None:
            old_item = self.standard_table.item(*previous)
            if old_item is not None:
                old_font = old_item.font()
                old_font.setUnderline(False)
                old_item.setFont(old_font)
                old_item.setForeground(QColor("#12618D"))
        self._hovered_standard_cell = None
        if row < 0 or column not in (0, 1):
            return
        item = self.standard_table.item(row, column)
        if item is not None:
            font = item.font()
            font.setUnderline(True)
            item.setFont(font)
            item.setForeground(QColor("#0B5F91"))
            self._hovered_standard_cell = (row, column)

    def eventFilter(self, watched: object, event: object) -> bool:  # type: ignore[override]
        if watched is self.standard_table.viewport():
            event_type = event.type()  # type: ignore[attr-defined]
            if event_type == QEvent.Type.MouseMove:
                position = event.position().toPoint()  # type: ignore[attr-defined]
                index = self.standard_table.indexAt(position)
                self._set_standard_hover(index.row(), index.column())
                self.standard_table.viewport().setCursor(
                    Qt.CursorShape.PointingHandCursor
                    if index.isValid() and index.column() in (0, 1)
                    else Qt.CursorShape.ArrowCursor
                )
            elif event_type == QEvent.Type.Leave:
                self._set_standard_hover(-1, -1)
                self.standard_table.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        return super().eventFilter(watched, event)  # type: ignore[arg-type]

    def _open_detail_from_cell(self, row: int, column: int) -> None:
        if column not in (0, 1):
            return
        item = self.standard_table.item(row, column)
        standard_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not isinstance(standard_id, str):
            return
        detail = self._service.get_standard_detail(standard_id)
        if detail is None:
            return
        self.selected_standard_id = standard_id
        self._saved_list_scroll = self._capture_list_scroll()
        self._render_detail(detail)
        self.view_stack.setCurrentWidget(self.detail_host)
        self._schedule_scroll_restore(main_value=0)

    def _main_scroll_area(self) -> QScrollArea | None:
        return self.window().findChild(QScrollArea, "mainScrollArea")

    def _capture_list_scroll(self) -> tuple[int | None, int, int]:
        scroll_area = self._main_scroll_area()
        main_value = (
            scroll_area.verticalScrollBar().value()
            if scroll_area is not None
            else None
        )
        return (
            main_value,
            self.standard_table.verticalScrollBar().value(),
            self.standard_table.horizontalScrollBar().value(),
        )

    def _schedule_scroll_restore(
        self,
        *,
        main_value: int | None,
        table_vertical_value: int | None = None,
        table_horizontal_value: int | None = None,
    ) -> None:
        def restore() -> None:
            scroll_area = self._main_scroll_area()
            if scroll_area is not None and main_value is not None:
                scroll_bar = scroll_area.verticalScrollBar()
                scroll_bar.setValue(min(main_value, scroll_bar.maximum()))
            if table_vertical_value is not None:
                scroll_bar = self.standard_table.verticalScrollBar()
                scroll_bar.setValue(min(table_vertical_value, scroll_bar.maximum()))
            if table_horizontal_value is not None:
                scroll_bar = self.standard_table.horizontalScrollBar()
                scroll_bar.setValue(min(table_horizontal_value, scroll_bar.maximum()))

        # Let the stacked view and its ancestors process LayoutRequest events first.
        QTimer.singleShot(0, self, lambda: QTimer.singleShot(0, self, restore))

    def _return_to_list(self) -> None:
        self.view_stack.setCurrentWidget(self.list_view)
        if self.page_title is not None:
            self.page_title.setText("标准库")
        if self.page_description is not None:
            self.page_description.setText("查看已登记标准、适用范围与核算要求")
        saved = self._saved_list_scroll
        self._schedule_scroll_restore(
            main_value=saved[0] if saved is not None else 0,
            table_vertical_value=saved[1] if saved is not None else 0,
            table_horizontal_value=saved[2] if saved is not None else 0,
        )

    def _add_basic_information(self, detail: StandardDetail) -> None:
        standard = detail.standard
        card, layout = _card("基本信息", self.detail_host)
        rows = (
            ("标准编号", standard.standard_number, "standardDetailNumber"),
            ("标准名称", standard.standard_name, "standardDetailName"),
            ("版本", standard.version, "standardDetailVersion"),
            ("标准状态", self._service.status_label(detail.status), "standardDetailStatus"),
            ("发布日期", _date_text(standard.publication_date), "standardPublicationDate"),
            ("实施日期", _date_text(standard.implementation_date), "standardImplementationDate"),
            ("废止日期", _date_text(standard.abolition_date), "standardAbolitionDate"),
            ("软件支持", self._software_support_label(standard), "standardSoftwareSupport"),
        )
        for label_text, value_text, object_name in rows:
            row = QWidget(card)
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setHorizontalSpacing(20)
            row_layout.setVerticalSpacing(8)
            label = QLabel(label_text, row)
            label.setObjectName("detailFieldLabel")
            value = QLabel(value_text or "—", row)
            value.setObjectName(object_name)
            value.setWordWrap(True)
            row_layout.addWidget(label, 0, 0)
            row_layout.addWidget(value, 0, 1)
            row_layout.setColumnStretch(1, 1)
            layout.addWidget(row)
        self.detail_layout.addWidget(card)

    def _render_detail(self, detail: StandardDetail) -> None:
        _replace_layout_contents(self.detail_layout)
        standard = detail.standard
        supported = (
            standard.standard_id == STANDARD_ID
            and standard.calculation_status == "IMPLEMENTED"
        )
        if self.page_title is not None:
            self.page_title.setText("标准详情")
        if self.page_description is not None:
            self.page_description.setText(
                "单页连续呈现基本信息、适用范围和标准要求，不设置详情页签。"
            )

        navigation_host = QWidget(self.detail_host)
        navigation_host.setObjectName("standardDetailActions")
        navigation_row = QHBoxLayout(navigation_host)
        navigation_row.setContentsMargins(0, 0, 0, 0)
        back_button = QPushButton("返回标准列表", navigation_host)
        back_button.setObjectName("backToStandardListButton")
        back_button.setMinimumHeight(36)
        back_button.setStyleSheet(
            "QPushButton#backToStandardListButton { border: 1px solid #C8D3DB; border-radius: 8px; padding: 7px 14px; background: #FFFFFF; color: #17445D; }"
            "QPushButton#backToStandardListButton:hover { background: #F2F7FA; }"
            "QPushButton#backToStandardListButton:focus { border: 2px solid #12618D; }"
        )
        back_button.clicked.connect(self._return_to_list)
        navigation_row.addWidget(back_button)
        can_start = (
            standard.standard_id == STANDARD_ID
            and detail.status is CatalogStatus.CURRENT
        )
        if can_start:
            accounting_label = "按此标准核算"
            accounting_tooltip = ""
        elif (
            standard.calculation_status == "COMMON_RULES_ONLY"
            and standard.standard_type is CatalogStandardType.COMMON_RULES
        ):
            accounting_label = "配套通则，不单独核算"
            accounting_tooltip = "通则作为配套规则使用，不单独发起核算。"
        elif standard.calculation_status == "IMPLEMENTED":
            accounting_label = "当前状态下不可新建核算"
            accounting_tooltip = "当前标准状态不满足新建核算条件。"
        else:
            accounting_label = "核算模块待开发"
            accounting_tooltip = "当前版本尚未开放该标准的核算模块。"
        accounting_button = QPushButton(accounting_label, navigation_host)
        accounting_button.setObjectName("startAccountingButton")
        accounting_button.setEnabled(can_start)
        accounting_button.setProperty("standardId", standard.standard_id)
        if can_start:
            accounting_button.clicked.connect(
                lambda: self.accounting_requested.emit(standard.standard_id)
            )
        else:
            accounting_button.setToolTip(accounting_tooltip)
        navigation_row.addStretch(1)
        self.detail_layout.addWidget(navigation_host)

        summary_card, summary_layout = _card(standard.standard_number, self.detail_host)
        summary_row = QWidget(summary_card)
        summary_layout_row = QHBoxLayout(summary_row)
        summary_layout_row.setContentsMargins(0, 0, 0, 0)
        summary_layout_row.setSpacing(14)
        name = QLabel(standard.standard_name, summary_row)
        name.setObjectName("standardSummaryName")
        name.setWordWrap(True)
        summary_layout_row.addWidget(name, 1)
        status = QLabel(self._service.status_label(detail.status), summary_row)
        status.setObjectName("statusBadge")
        status.setProperty("catalogStatus", detail.status.value)
        summary_layout_row.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)
        support_text = self._software_support_label(standard)
        support = QLabel(support_text, summary_row)
        support.setObjectName("standardSupportBadge")
        support.setProperty("implemented", supported)
        summary_layout_row.addWidget(support, 0, Qt.AlignmentFlag.AlignVCenter)
        accounting_button.setParent(summary_row)
        accounting_button.setMinimumHeight(37)
        summary_layout_row.addWidget(accounting_button, 0, Qt.AlignmentFlag.AlignVCenter)
        summary_layout.addWidget(summary_row)
        self.detail_layout.addWidget(summary_card)
        self._add_basic_information(detail)

        scope_text = (
            standard.notes
            if standard.notes.strip().startswith("适用于")
            else "当前目录尚未录入可核验的适用范围信息。"
        )
        self.detail_layout.addWidget(
            _text_section(
                "适用范围",
                self.detail_host,
                scope_text,
            )
        )
        requirements, requirements_layout = _card("标准要求", self.detail_host)
        requirement_cards = QWidget(requirements)
        requirement_grid = QGridLayout(requirement_cards)
        requirement_grid.setContentsMargins(0, 0, 0, 0)
        requirement_grid.setHorizontalSpacing(14)
        requirement_grid.setVerticalSpacing(14)
        requirement_text = (
            (
                "化石燃料、煅烧、焙烧／炭化、石墨化、烟气治理、购入／输出电力与热力。",
                "按正式行业标准及现有输入模型，区分活动量、实测数据与标准缺省值。",
                "使用已实现的行业核算流程，并由冻结记录生成标准专属报告。",
            )
            if supported
            else (
                "当前仅显示目录信息，不提供正式业务核算。",
                "尚未建立该行业可执行输入与计算规则。",
                "当前仅展示目录，不开放按此标准新建核算。",
            )
        )
        for column, (title, body) in enumerate(
            zip(("适用业务", "活动数据", "核算与报告"), requirement_text)
        ):
            mini = QFrame(requirement_cards)
            mini.setObjectName("standardRequirementCard")
            mini_layout = QVBoxLayout(mini)
            mini_layout.setContentsMargins(14, 14, 14, 14)
            mini_layout.setSpacing(8)
            heading = QLabel(title, mini)
            heading.setObjectName("standardRequirementTitle")
            description = QLabel(body, mini)
            description.setObjectName("standardRequirementText")
            description.setWordWrap(True)
            mini_layout.addWidget(heading)
            mini_layout.addWidget(description, 1)
            requirement_grid.addWidget(mini, 0, column)
        requirement_grid.setColumnStretch(0, 1)
        requirement_grid.setColumnStretch(1, 1)
        requirement_grid.setColumnStretch(2, 1)
        requirements_layout.addWidget(requirement_cards)

        source_row = QWidget(requirements)
        source_layout = QHBoxLayout(source_row)
        source_layout.setContentsMargins(0, 4, 0, 0)
        has_official_url = bool(standard.official_source_url)
        source_note = QLabel(
            "标准原文入口仅使用已核验的官方来源。"
            if has_official_url
            else "当前目录未配置标准官方页面，暂不能打开原文。",
            source_row,
        )
        source_note.setObjectName(
            "standardSourceNote" if has_official_url else "officialSourceUnavailable"
        )
        source_note.setWordWrap(True)
        source_layout.addWidget(source_note, 1)
        source_button = QPushButton("查看标准原文", source_row)
        source_button.setObjectName("viewOfficialSourceButton")
        source_button.setProperty("officialSourceUrl", standard.official_source_url or "")
        source_button.setEnabled(has_official_url)
        if standard.official_source_url:
            source_button.clicked.connect(
                lambda _checked=False, url=standard.official_source_url: QDesktopServices.openUrl(QUrl(url))
            )
        else:
            source_button.setToolTip("当前目录未配置标准官方页面，暂不能打开原文。")
        source_layout.addWidget(source_button)
        requirements_layout.addWidget(source_row)
        self.detail_layout.addWidget(requirements)
        self.detail_layout.addStretch(1)


class ParameterFactorLibraryPage(BasePage):
    """Browse source documents and search one shared reference-data library."""

    def __init__(
        self,
        service: CatalogQueryService,
        navigate: Navigate,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.FACTORS, parent)
        self._service = service
        self._navigate = navigate
        self._search_results = ()
        self._build_page()
        self._refresh_sources()
        self._refresh_tables()

    def _build_page(self) -> None:
        self.body_layout.setSpacing(16)
        self.add_header(
            "参数与因子库",
            "全库检索与按来源浏览使用同一份只读登记数据，切换后显示不同视图。",
        )

        mode_card, mode_layout = _card("查询方式", self)
        mode_row = QHBoxLayout()
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.setSpacing(10)
        mode_buttons = QWidget(mode_card)
        mode_buttons_layout = QHBoxLayout(mode_buttons)
        mode_buttons_layout.setContentsMargins(0, 0, 0, 0)
        mode_buttons_layout.setSpacing(4)
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)
        self.search_mode_button = QPushButton("全库搜索", mode_buttons)
        self.search_mode_button.setObjectName("referenceLibraryModeButton")
        self.search_mode_button.setCheckable(True)
        self.search_mode_button.setAccessibleName("全库搜索")
        self.browse_mode_button = QPushButton("按来源浏览", mode_buttons)
        self.browse_mode_button.setObjectName("referenceLibraryModeButton")
        self.browse_mode_button.setCheckable(True)
        self.browse_mode_button.setAccessibleName("按来源浏览")
        self.mode_button_group.addButton(self.search_mode_button, 1)
        self.mode_button_group.addButton(self.browse_mode_button, 0)
        mode_buttons_layout.addWidget(self.search_mode_button)
        mode_buttons_layout.addWidget(self.browse_mode_button)
        mode_row.addWidget(mode_buttons, 0)

        self.search_input = QLineEdit(mode_card)
        self.search_input.setObjectName("referenceLibrarySearch")
        self.search_input.setPlaceholderText("点击查看全部参数，输入即时筛选")
        self.search_input.setAccessibleName("参数与因子搜索")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(280)
        mode_row.addWidget(self.search_input, 1)
        self.search_category_filter = QComboBox(mode_card)
        self.search_category_filter.setObjectName("referenceLibraryCategoryFilter")
        self.search_category_filter.setAccessibleName("数据类别")
        for label, value in (
            ("全部类别", None),
            ("参数值", "parameter"),
            ("排放因子", "factor"),
            ("参考数据", "reference"),
        ):
            self.search_category_filter.addItem(label, value)
        self.search_category_filter.setMinimumWidth(150)
        mode_row.addWidget(self.search_category_filter, 0)
        mode_layout.addLayout(mode_row)
        self.view_mode_filter = QComboBox(self)
        self.view_mode_filter.setObjectName("referenceLibraryMode")
        self.view_mode_filter.addItem("按标准/文件查看", "browse")
        self.view_mode_filter.addItem("全库搜索", "search")
        self.view_mode_filter.setAccessibleName("参数与因子库查看方式")
        self.view_mode_filter.hide()
        self.body_layout.addWidget(mode_card)

        self.browse_card, browse_layout = _card("按来源浏览登记资料", self)
        browse_layout.setSpacing(10)
        browse_notice = QLabel(
            "此模式按资料文件、表格顺序浏览，完整展示原始登记信息；不同于全库搜索结果视图。",
            self.browse_card,
        )
        browse_notice.setObjectName("sourceBrowseNotice")
        browse_notice.setWordWrap(True)
        browse_layout.addWidget(browse_notice)
        browse_filters = QHBoxLayout()
        browse_filters.setContentsMargins(0, 0, 0, 0)
        browse_filters.setSpacing(8)
        browse_filters.addWidget(QLabel("来源资料", self.browse_card))
        self.source_filter = QComboBox(self.browse_card)
        self.source_filter.setObjectName("sourceDocumentFilter")
        self.source_filter.setAccessibleName("来源资料")
        self.source_filter.setMinimumContentsLength(18)
        self.source_filter.setMinimumWidth(250)
        browse_filters.addWidget(self.source_filter, 2)
        browse_filters.addWidget(QLabel("表格", self.browse_card))
        self.table_filter = QComboBox(self.browse_card)
        self.table_filter.setObjectName("sourceTableFilter")
        self.table_filter.setAccessibleName("资料表格")
        self.table_filter.setMinimumContentsLength(18)
        self.table_filter.setMinimumWidth(250)
        browse_filters.addWidget(self.table_filter, 2)
        browse_layout.addLayout(browse_filters)
        self.browse_table_title = QLabel("", self.browse_card)
        self.browse_table_title.setObjectName("sourceTableTitle")
        self.browse_table_title.setWordWrap(True)
        browse_layout.addWidget(self.browse_table_title)
        self.browse_table_note = QLabel("", self.browse_card)
        self.browse_table_note.setObjectName("sourceTableNote")
        self.browse_table_note.setWordWrap(True)
        browse_layout.addWidget(self.browse_table_note)
        self.factor_table = QTableWidget(self.browse_card)
        self.factor_table.setObjectName("sourceTableView")
        self.factor_table.setAccessibleName("来源资料表")
        self.factor_table.setAccessibleDescription("按原登记表结构浏览参数与参考值；表格只读。")
        self.factor_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.factor_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.factor_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.factor_table.verticalHeader().setVisible(False)
        self.factor_table.horizontalHeader().setStretchLastSection(True)
        self.factor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.factor_table.setWordWrap(True)
        self.factor_table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.factor_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.factor_table.setMinimumHeight(300)
        browse_layout.addWidget(self.factor_table)
        self.body_layout.addWidget(self.browse_card)

        self.search_card, search_layout = _card("全库搜索", self)
        search_layout.setSpacing(10)
        self.search_source_filter = QComboBox(self)
        self.search_source_filter.setObjectName("searchSourceDocumentFilter")
        self.search_source_filter.setAccessibleName("搜索范围：来源文件")
        self.search_source_filter.addItem("全部资料", None)
        self.search_source_filter.hide()
        self.result_summary = QLabel("", self.search_card)
        self.result_summary.setObjectName("referenceLibrarySummary")
        self.result_summary.setWordWrap(True)
        search_layout.addWidget(self.result_summary)
        self.search_splitter = QSplitter(Qt.Orientation.Horizontal, self.search_card)
        self.search_splitter.setObjectName("referenceLibrarySplitter")
        self.search_splitter.setChildrenCollapsible(False)
        self.search_source_panel, source_list_layout = _card("来源筛选", self.search_splitter)
        self.search_source_list = QListWidget(self.search_source_panel)
        self.search_source_list.setObjectName("referenceLibrarySourceList")
        self.search_source_list.setAccessibleName("来源筛选")
        self.search_source_list.setAccessibleDescription("按资料来源筛选全库搜索结果。")
        self.search_source_list.setMinimumWidth(190)
        self.search_source_list.setMinimumHeight(320)
        source_list_layout.addWidget(self.search_source_list)

        self.search_results_panel = QWidget(self.search_splitter)
        results_layout = QVBoxLayout(self.search_results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(10)
        self.search_results_splitter = QSplitter(Qt.Orientation.Vertical, self.search_results_panel)
        self.search_results_splitter.setObjectName("referenceLibraryResultsSplitter")
        self.search_results_splitter.setChildrenCollapsible(False)
        self.search_result_table = QTableWidget(self.search_results_splitter)
        _configure_table(
            self.search_result_table,
            ("参数名称", "数值", "单位", "类别"),
        )
        self.search_result_table.setObjectName("catalogTable")
        self.search_result_table.setAccessibleName("参数与因子搜索结果")
        self.search_result_table.setAccessibleDescription("选择一行查看只读参数详情和完整来源追溯。")
        self.search_result_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.search_result_table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.search_result_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.search_result_table.setMinimumHeight(260)
        self.search_result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate((340, 145, 125, 130)):
            self.search_result_table.setColumnWidth(column, width)
        self.factor_detail_host = QWidget(self.search_results_splitter)
        self.factor_detail_host.setObjectName("parameterDetailHost")
        self.factor_detail_layout = QVBoxLayout(self.factor_detail_host)
        self.factor_detail_layout.setContentsMargins(12, 12, 12, 12)
        self.factor_detail_layout.setSpacing(12)
        self.factor_detail_scroll = QScrollArea(self.search_results_splitter)
        self.factor_detail_scroll.setObjectName("parameterDetailScroll")
        self.factor_detail_scroll.setMinimumWidth(320)
        self.factor_detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.factor_detail_scroll.setWidgetResizable(True)
        self.factor_detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.factor_detail_scroll.setWidget(self.factor_detail_host)
        self.search_results_splitter.addWidget(self.search_result_table)
        self.search_results_splitter.addWidget(self.factor_detail_scroll)
        self.search_results_splitter.setStretchFactor(0, 3)
        self.search_results_splitter.setStretchFactor(1, 2)
        self.search_results_splitter.setSizes([420, 280])
        results_layout.addWidget(self.search_results_splitter)
        self.search_splitter.addWidget(self.search_source_panel)
        self.search_splitter.addWidget(self.search_results_panel)
        self.search_splitter.setStretchFactor(0, 0)
        self.search_splitter.setStretchFactor(1, 1)
        self.search_splitter.setSizes([210, 1100])
        search_layout.addWidget(self.search_splitter)
        self.body_layout.addWidget(self.search_card)
        self.body_layout.addStretch(1)

        self._apply_library_style()

        self.view_mode_filter.currentIndexChanged.connect(self._change_mode)
        self.mode_button_group.idClicked.connect(self.view_mode_filter.setCurrentIndex)
        self.source_filter.currentIndexChanged.connect(self._refresh_tables)
        self.table_filter.currentIndexChanged.connect(self._show_source_table)
        self.search_input.textChanged.connect(self._refresh_search)
        self.search_source_filter.currentIndexChanged.connect(self._refresh_search)
        self.search_category_filter.currentIndexChanged.connect(self._refresh_search)
        self.search_source_list.currentRowChanged.connect(self._select_search_source)
        self.search_result_table.itemSelectionChanged.connect(self._show_selected_search_detail)
        self._change_mode()

    def _apply_library_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#referenceLibraryModeBar {{
                background: transparent;
            }}
            QLabel#referenceLibraryModeLabel {{
                color: {SECONDARY_TEXT};
                font-size: 13px;
            }}
            QLineEdit#referenceLibrarySearch,
            QComboBox#referenceLibraryCategoryFilter,
            QComboBox#referenceLibraryMode,
            QComboBox#sourceDocumentFilter,
            QComboBox#sourceTableFilter,
            QComboBox#searchSourceDocumentFilter {{
                min-height: 36px;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0 10px;
                background: {CARD_BACKGROUND};
                color: {PRIMARY_TEXT};
            }}
            QLineEdit#referenceLibrarySearch:focus,
            QComboBox#referenceLibraryCategoryFilter:focus,
            QComboBox#referenceLibraryMode:focus,
            QComboBox#sourceDocumentFilter:focus,
            QComboBox#sourceTableFilter:focus,
            QComboBox#searchSourceDocumentFilter:focus {{
                border: 1px solid {PRIMARY_BRAND};
                padding: 0 10px;
            }}
            QPushButton#referenceLibraryModeButton {{
                min-height: 36px;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 14px;
                background: {CARD_BACKGROUND};
                color: {SECONDARY_TEXT};
                font-weight: 600;
            }}
            QPushButton#referenceLibraryModeButton:hover {{
                border-color: {PRIMARY_BRAND};
                color: {PRIMARY_BRAND};
                background: #F4FAFE;
            }}
            QPushButton#referenceLibraryModeButton:checked {{
                border-color: {PRIMARY_BRAND};
                background: #E6F4FB;
                color: {PRIMARY_BRAND};
                font-weight: 700;
            }}
            QListWidget#referenceLibrarySourceList {{
                border: none;
                background: transparent;
                outline: none;
                color: {SECONDARY_TEXT};
                font-size: 13px;
            }}
            QListWidget#referenceLibrarySourceList::item {{
                min-height: 34px;
                padding: 4px 10px;
                border-radius: 7px;
            }}
            QListWidget#referenceLibrarySourceList::item:hover {{
                background: #F3F8FC;
                color: {PRIMARY_BRAND};
            }}
            QListWidget#referenceLibrarySourceList::item:selected {{
                background: #E6F4FB;
                color: {PRIMARY_BRAND};
                font-weight: 700;
            }}
            QTableWidget#sourceTableView {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                gridline-color: {BORDER};
                selection-background-color: #E6F4FB;
                selection-color: {PRIMARY_TEXT};
            }}
            QTableWidget#sourceTableView QHeaderView::section {{
                background: {SURFACE_MUTED};
                color: {SECONDARY_TEXT};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 8px;
                font-weight: 600;
            }}
            QTableWidget#catalogTable {{
                background: {CARD_BACKGROUND};
                border: 1px solid {BORDER};
                selection-background-color: #E6F4FB;
                selection-color: {PRIMARY_TEXT};
            }}
            QTableWidget#catalogTable QHeaderView::section {{
                background: {SURFACE_MUTED};
                color: {SECONDARY_TEXT};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 9px 10px;
                font-weight: 650;
            }}
            QScrollArea#parameterDetailScroll {{
                border: 1px solid {BORDER};
                background: {CARD_BACKGROUND};
            }}
            QToolButton#parameterDetailTraceToggle {{
                min-height: 34px;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0 12px;
                color: {PRIMARY_BRAND};
                background: {CARD_BACKGROUND};
                text-align: left;
            }}
            QToolButton#parameterDetailTraceToggle:hover {{
                background: {SURFACE_MUTED};
                border-color: {PRIMARY_BRAND};
            }}
            QLabel#referenceLibrarySummary,
            QLabel#sourceTableTitle,
            QLabel#sourceTableNote {{
                color: {SECONDARY_TEXT};
                font-size: 13px;
            }}
            QLabel#sourceBrowseNotice {{
                color: #47697F;
                background: #EFF7FD;
                border-left: 3px solid #4299C5;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 9px 11px;
                font-size: 12px;
            }}
            """
        )

    def _refresh_sources(self) -> None:
        sources = self._service.list_sources()
        source_by_id = {source.source_id: source for source in sources}
        table_source_ids = {table.source_id for table in self._service.list_source_tables()}
        self.source_filter.clear()
        self.search_source_filter.blockSignals(True)
        self.search_source_filter.clear()
        self.search_source_filter.addItem("全部来源", None)
        self.search_source_list.blockSignals(True)
        self.search_source_list.clear()
        all_sources_item = QListWidgetItem("全部来源")
        all_sources_item.setData(Qt.ItemDataRole.UserRole, None)
        self.search_source_list.addItem(all_sources_item)
        for source in sources:
            index = self.search_source_filter.count()
            self.search_source_filter.addItem(source.document_no, source.source_id)
            self.search_source_filter.setItemData(
                index,
                f"{source.document_no} · {source.document_name}",
                Qt.ItemDataRole.ToolTipRole,
            )
            source_item = QListWidgetItem(source.document_no)
            source_item.setData(Qt.ItemDataRole.UserRole, source.source_id)
            source_item.setToolTip(f"{source.document_no} · {source.document_name}")
            self.search_source_list.addItem(source_item)
            if source.source_id in table_source_ids:
                index = self.source_filter.count()
                self.source_filter.addItem(
                    f"{source.document_no} · {source.document_name}", source.source_id
                )
                self.source_filter.setItemData(
                    index,
                    f"{source.document_no} · {source.document_name} · {source.publisher}",
                    Qt.ItemDataRole.ToolTipRole,
                )
        self.search_source_filter.blockSignals(False)
        self.search_source_list.setCurrentRow(0)
        self.search_source_list.blockSignals(False)
        preferred = next(
            (index for index in range(self.source_filter.count())
             if "32151.34" in self.source_filter.itemText(index)),
            0,
        )
        if self.source_filter.count():
            self.source_filter.setCurrentIndex(preferred)
        if not source_by_id:
            self.browse_table_note.setText("当前没有可查看的标准资料。")

    def _change_mode(self, *_args: object) -> None:
        is_browse = self.view_mode_filter.currentData() != "search"
        self.browse_mode_button.setChecked(is_browse)
        self.search_mode_button.setChecked(not is_browse)
        self.browse_card.setVisible(is_browse)
        self.search_card.setVisible(not is_browse)
        if not is_browse:
            self._refresh_search()

    def _select_search_source(self, row: int) -> None:
        item = self.search_source_list.item(row) if row >= 0 else None
        source_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        index = self.search_source_filter.findData(source_id)
        if index >= 0 and self.search_source_filter.currentIndex() != index:
            self.search_source_filter.setCurrentIndex(index)

    def _refresh_tables(self, *_args: object) -> None:
        source_id = self.source_filter.currentData()
        self.table_filter.blockSignals(True)
        self.table_filter.clear()
        for table in self._service.list_source_tables(source_id if isinstance(source_id, str) else None):
            index = self.table_filter.count()
            self.table_filter.addItem(f"{table.display_number} · {table.title}", table.source_table_id)
            self.table_filter.setItemData(
                index,
                f"{table.display_number} · {table.title} · {table.source_location}",
                Qt.ItemDataRole.ToolTipRole,
            )
        self.table_filter.blockSignals(False)
        if self.table_filter.count():
            self.table_filter.setCurrentIndex(0)
            self._show_source_table()
        else:
            self.factor_table.clear()
            self.factor_table.setRowCount(0)
            self.browse_table_title.setText("")
            self.browse_table_note.setText("该资料没有登记可浏览的参数表。")

    def _show_source_table(self, *_args: object) -> None:
        table_id = self.table_filter.currentData()
        if not isinstance(table_id, str):
            return
        table = next((item for item in self._service.list_source_tables() if item.source_table_id == table_id), None)
        view = self._service.get_source_table_view(table_id)
        if table is None or view is None:
            return
        headers, rows, note = view
        self.factor_table.clear()
        self.factor_table.setColumnCount(len(headers))
        self.factor_table.setHorizontalHeaderLabels(headers)
        self.factor_table.setRowCount(len(rows))
        for row_number, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(str(value))
                item.setData(
                    Qt.ItemDataRole.AccessibleTextRole,
                    f"{headers[column]}：{value}",
                )
                self.factor_table.setItem(row_number, column, item)
        self.factor_table.resizeRowsToContents()
        self.browse_table_title.setText(f"{table.display_number} · {table.title} · {len(rows)} 行")
        self.browse_table_note.setText(note)

    def _asset_display_name(self, result: object) -> str:
        asset = getattr(result, "asset", None)
        if asset is None:
            return getattr(result, "title", "—")
        parameter = self._display_parameters.get(asset.parameter_id)
        subject = self._display_subjects.get(asset.subject_id)
        if parameter is None:
            return getattr(result, "title", "—")
        return f"{parameter.name}（{subject.name}）" if subject else parameter.name

    def _asset_condition_text(self, result: object) -> str:
        asset = getattr(result, "asset", None)
        if asset is None:
            return "—"
        subject = self._display_subjects.get(asset.subject_id)
        parts: list[str] = []
        if subject is not None:
            parts.append(subject.name)
        regions = tuple(
            dict.fromkeys(
                binding.region
                for binding in getattr(result, "bindings", ())
                if binding.region
            )
        )
        if regions:
            parts.append("地区：" + "、".join(regions))
        years = tuple(
            dict.fromkeys(
                str(binding.factor_year)
                for binding in getattr(result, "bindings", ())
                if binding.factor_year
            )
        )
        if years:
            parts.append("年度：" + "、".join(years))
        periods = tuple(
            dict.fromkeys(
                f"{_date_text(binding.valid_from)} 至 {_date_text(binding.valid_to)}"
                for binding in getattr(result, "bindings", ())
                if binding.valid_from is not None or binding.valid_to is not None
            )
        )
        if periods:
            parts.append("有效期：" + "；".join(periods))
        return "；".join(parts) or "—"

    def _reference_category(self, result: object) -> str:
        if getattr(result, "result_type", "") != "asset":
            return "reference"
        asset = getattr(result, "asset", None)
        parameter = (
            self._display_parameters.get(asset.parameter_id)
            if asset is not None
            else None
        )
        factor_types = {
            ParameterType.EMISSION_FACTOR,
            ParameterType.ELECTRICITY_EMISSION_FACTOR,
            ParameterType.HEAT_EMISSION_FACTOR,
            ParameterType.PROCESS_CO2_FACTOR,
        }
        return (
            "factor"
            if parameter is not None and parameter.parameter_type in factor_types
            else "parameter"
        )

    def _refresh_search(self, *_args: object) -> None:
        # One read per refresh; these mappings only label the existing query results.
        self._display_parameters = {
            item.parameter_id: item for item in self._service.repository.list_parameters()
        }
        self._display_subjects = {
            item.subject_id: item for item in self._service.repository.list_subjects()
        }
        source_id = self.search_source_filter.currentData()
        results = self._service.search_reference_library(
            self.search_input.text(), source_id=source_id if isinstance(source_id, str) else None
        )
        category_filter = self.search_category_filter.currentData()
        self._search_results = tuple(
            result
            for result in results
            if category_filter is None or self._reference_category(result) == category_filter
        )
        self.search_result_table.setRowCount(0)
        for row_number, result in enumerate(self._search_results):
            self.search_result_table.insertRow(row_number)
            category = (
                {
                    "standard": "标准",
                    "source": "来源文件",
                    "table": "标准表",
                }.get(result.result_type, "资料")
                if self._reference_category(result) == "reference"
                else "排放因子"
                if self._reference_category(result) == "factor"
                else "参数值"
            )
            display_name = (
                self._asset_display_name(result)
                if result.result_type == "asset"
                else result.title
            )
            values = (
                display_name,
                result.value_text or "—",
                result.unit or "—",
                category,
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, result.key)
                item.setToolTip(text)
                item.setData(
                    Qt.ItemDataRole.AccessibleTextRole,
                    f"{self.search_result_table.horizontalHeaderItem(column).text()}：{text}",
                )
                self.search_result_table.setItem(row_number, column, item)
        self.search_result_table.resizeRowsToContents()
        self.result_summary.setText(f"找到 {len(self._search_results)} 项资料或参数值")
        if self._search_results:
            self.search_result_table.selectRow(0)
            self._show_selected_search_detail()
        else:
            self._clear_search_detail("没有找到匹配的资料或参数值。")

    def _show_selected_search_detail(self) -> None:
        row = self.search_result_table.currentRow()
        if row < 0 or row >= len(self._search_results):
            self._clear_search_detail("选择一项资料或参数值查看来源。")
            return
        self._render_search_detail(self._search_results[row])

    def _clear_search_detail(self, message: str) -> None:
        _replace_layout_contents(self.factor_detail_layout)
        label = QLabel(message, self.factor_detail_host)
        label.setObjectName("emptyStateDescription")
        label.setWordWrap(True)
        self.factor_detail_layout.addWidget(label)
        self.factor_detail_layout.addStretch(1)

    def _render_search_detail(self, result: object) -> None:
        _replace_layout_contents(self.factor_detail_layout)
        heading = QLabel(result.title, self.factor_detail_host)
        heading.setObjectName("parameterDetailName")
        heading.setWordWrap(True)
        self.factor_detail_layout.addWidget(heading)
        if result.standard is not None:
            standard = result.standard
            source = next((item for item in self._service.list_sources()
                           if item.source_id == standard.official_source_id), None)
            rows = (
                ("标准编号", standard.standard_number),
                ("标准名称", standard.standard_name),
                ("状态", self._service.status_label(self._service.standard_status(standard))),
                ("实施日期", _date_text(standard.implementation_date)),
                ("發布部門", standard.issuing_authority or "—"),
                ("官方資料", source.document_no if source else "—"),
            )
            self.factor_detail_layout.addWidget(_detail_section("标准信息", self.factor_detail_host, rows))
            url = standard.official_source_url or (source.official_url if source else None)
            if url:
                button = QPushButton("打开标准官方页面", self.factor_detail_host)
                button.setObjectName("openOfficialReferenceButton")
                button.clicked.connect(lambda _checked=False, target=url: QDesktopServices.openUrl(QUrl(target)))
                self.factor_detail_layout.addWidget(button)
        elif result.source is not None:
            source = result.source
            rows = (
                ("资料文件", source.document_no),
                ("资料名称", source.document_name),
                ("发布机构", source.publisher),
                ("发布日期", _date_text(source.publication_date)),
                ("生效日期", _date_text(source.effective_from)),
                ("资料核对", self._service.review_status_label(source.review_status)),
                ("说明", source.notes or "—"),
            )
            self.factor_detail_layout.addWidget(_detail_section("来源文件", self.factor_detail_host, rows))
            if source.official_url:
                button = QPushButton("打开官方来源页面", self.factor_detail_host)
                button.setObjectName("openOfficialReferenceButton")
                button.clicked.connect(lambda _checked=False, target=source.official_url: QDesktopServices.openUrl(QUrl(target)))
                self.factor_detail_layout.addWidget(button)
        elif result.result_type == "table" and result.table is not None:
            source = next((item for item in self._service.list_sources() if item.source_id == result.table.source_id), None)
            rows = (
                ("资料文件", source.document_no if source else "标准资料"),
                ("表格", f"{result.table.display_number} · {result.table.title}"),
                ("依据定位", result.table.source_location),
                ("说明", result.table.notes or "—"),
            )
            self.factor_detail_layout.addWidget(_detail_section("表格来源", self.factor_detail_host, rows))
            button = QPushButton("按原表结构查看", self.factor_detail_host)
            button.setObjectName("openRegisteredTableButton")
            button.clicked.connect(lambda: self._open_registered_table(result.table.source_table_id))
            self.factor_detail_layout.addWidget(button)
        elif result.asset is not None:
            asset = result.asset
            parameter = next((item for item in self._service.repository.list_parameters() if item.parameter_id == asset.parameter_id), None)
            subject = next((item for item in self._service.repository.list_subjects() if item.subject_id == asset.subject_id), None)
            rows = (
                ("参数", parameter.name if parameter else "—"),
                ("适用对象", subject.name if subject else "—"),
                *((("地区", "、".join(dict.fromkeys(binding.region for binding in result.bindings if binding.region))),) if any(binding.region for binding in result.bindings) else ()),
                ("数值", format(asset.value, "f")),
                ("单位", asset.unit),
                ("适用条件", self._asset_condition_text(result)),
                ("数据类型", self._service.value_type_label(asset.value_type)),
            )
            self.factor_detail_layout.addWidget(_detail_section("参数值", self.factor_detail_host, rows))

            trace_toggle = QToolButton(self.factor_detail_host)
            trace_toggle.setObjectName("parameterDetailTraceToggle")
            trace_toggle.setCheckable(True)
            trace_toggle.setChecked(False)
            trace_toggle.setArrowType(Qt.ArrowType.RightArrow)
            trace_toggle.setText("查看完整来源、期间与定位")
            trace_toggle.setAccessibleName("完整来源、期间与定位")
            trace_toggle.setAccessibleDescription(
                "展开查看来源有效期、数据类型、精确定位、原始值及官方来源入口。"
            )
            self.factor_detail_layout.addWidget(trace_toggle)

            trace_host = QWidget(self.factor_detail_host)
            trace_host.setObjectName("parameterDetailTrace")
            trace_layout = QVBoxLayout(trace_host)
            trace_layout.setContentsMargins(0, 0, 0, 0)
            trace_layout.setSpacing(10)
            trace_host.setVisible(False)

            binding_rows = []
            tables = {item.source_table_id: item for item in self._service.list_source_tables()}
            sources = {item.source_id: item for item in self._service.list_sources()}
            for binding in result.bindings:
                table = tables.get(binding.source_table_id)
                source = sources.get(table.source_id) if table else None
                label = f"{source.document_no} · {table.display_number}" if source and table else "标准资料"
                binding_rows.append((label, binding.source_location))
            if binding_rows:
                trace_layout.addWidget(_detail_section("来源定位", trace_host, binding_rows))

            source_ids = tuple(
                dict.fromkeys(
                    tables[binding.source_table_id].source_id
                    for binding in result.bindings
                    if binding.source_table_id in tables
                )
            )
            source_rows = []
            for source_id in source_ids:
                source = sources.get(source_id)
                if source is None:
                    continue
                source_rows.extend(
                    (
                        ("来源文件", f"{source.document_no} · {source.document_name}"),
                        ("发布机构", source.publisher or "—"),
                        (
                            "来源有效期",
                            f"{_date_text(source.effective_from)} 至 {_date_text(source.effective_to)}",
                        ),
                        ("资料版本", source.version or "—"),
                        ("资料核对", self._service.review_status_label(source.review_status)),
                    )
                )
            if source_rows:
                trace_layout.addWidget(_detail_section("来源信息", trace_host, source_rows))

            standard_numbers = []
            standards = {
                item.standard_id: item
                for item in self._service.repository.list_standards()
            }
            if parameter is not None:
                standard_numbers = [
                    standards[standard_id].standard_number
                    for standard_id in parameter.applicable_standard_ids
                    if standard_id in standards
                ]
            period_rows = []
            binding_periods = tuple(
                dict.fromkeys(
                    f"{_date_text(binding.valid_from)} 至 {_date_text(binding.valid_to)}"
                    for binding in result.bindings
                    if binding.valid_from is not None or binding.valid_to is not None
                )
            )
            binding_years = tuple(
                dict.fromkeys(
                    str(binding.factor_year)
                    for binding in result.bindings
                    if binding.factor_year
                )
            )
            if binding_periods:
                period_rows.append(("因子适用期间", "；".join(binding_periods)))
            if binding_years:
                period_rows.append(("因子年度", "、".join(binding_years)))
            if standard_numbers:
                period_rows.append(("适用标准", "、".join(standard_numbers)))
            period_rows.extend(
                (
                    ("参数定位", parameter.source_location if parameter else "—"),
                    ("数据说明", asset.notes or (parameter.notes if parameter else "—") or "—"),
                    ("资源版本", asset.asset_version or "—"),
                    ("原始值", f"{format(asset.source_value, 'f')} {asset.source_unit}"),
                    ("归一化值", f"{format(asset.normalized_value, 'f')} {asset.normalized_unit}"),
                )
            )
            trace_layout.addWidget(_detail_section("参数追溯", trace_host, period_rows))

            for source_id in source_ids:
                source = sources.get(source_id)
                if source is None:
                    continue
                source_button = QPushButton(f"打开来源：{source.document_no}", trace_host)
                source_button.setObjectName("viewFactorSourceButton")
                source_button.setProperty("officialSourceUrl", source.official_url)
                source_button.setEnabled(bool(source.official_url))
                if source.official_url:
                    source_button.clicked.connect(lambda _checked=False, url=source.official_url: QDesktopServices.openUrl(QUrl(url)))
                else:
                    source_button.setToolTip("该资料尚未配置官方页面。")
                trace_layout.addWidget(source_button)

            self.factor_detail_layout.addWidget(trace_host)

            def toggle_trace(checked: bool) -> None:
                trace_host.setVisible(checked)
                trace_toggle.setArrowType(
                    Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
                )
                trace_toggle.setText(
                    "收起完整来源、期间与定位"
                    if checked
                    else "查看完整来源、期间与定位"
                )

            trace_toggle.toggled.connect(toggle_trace)
        self.factor_detail_layout.addStretch(1)

    def _open_registered_table(self, source_table_id: str) -> None:
        self.view_mode_filter.setCurrentIndex(0)
        for index in range(self.source_filter.count()):
            source_id = self.source_filter.itemData(index)
            if any(table.source_table_id == source_table_id and table.source_id == source_id
                   for table in self._service.list_source_tables()):
                self.source_filter.setCurrentIndex(index)
                break
        for index in range(self.table_filter.count()):
            if self.table_filter.itemData(index) == source_table_id:
                self.table_filter.setCurrentIndex(index)
                break
