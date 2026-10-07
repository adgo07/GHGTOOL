"""G04 catalog pages backed by the application query service."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from enum import Enum

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import ParameterType, ReviewStatus
from packages.core.models import ValueType
from packages.standards.carbon_material import ALGORITHM_VERSION, STANDARD_ID, steam_reference_table_rows
from packages.standards.catalog import (
    CatalogStatus,
    ParameterFactorResult,
    ParameterViewMode,
    StandardDetail,
)

from .pages import BasePage, Navigate, _card
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
    """Searchable standard list with a safe, vertically readable detail view."""

    accounting_requested = Signal(str)

    def __init__(
        self,
        service: CatalogQueryService,
        navigate: Navigate,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.STANDARDS, parent)
        self._service = service
        self._navigate = navigate
        self.selected_standard_id: str | None = None
        self._standards_by_id: dict[str, object] = {}
        self._build_page()
        self._refresh()

    def _build_page(self) -> None:
        self.add_header("标准库", "查看 GB/T 32151 系列标准及核算要求")

        filters, filters_layout = _card("搜索和筛选", self)
        search = QLineEdit(filters)
        search.setObjectName("standardSearch")
        search.setPlaceholderText("按标准编号、名称、行业、企业类型或排放源搜索")
        filters_layout.addWidget(search)
        self.search_input = search

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

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
        filter_row.addWidget(self.status_filter)

        self.industry_filter = QComboBox(filters)
        self.industry_filter.setObjectName("standardIndustryFilter")
        for industry in self._service.industry_options():
            self.industry_filter.addItem(industry, industry)
        filter_row.addWidget(self.industry_filter)

        self.year_filter = QComboBox(filters)
        self.year_filter.setObjectName("standardYearFilter")
        self.year_filter.addItem("全部年份", None)
        for year in self._service.publication_years():
            self.year_filter.addItem(str(year), year)
        filter_row.addWidget(self.year_filter)
        filter_row.addStretch(1)
        filters_layout.addLayout(filter_row)
        self.body_layout.addWidget(filters)

        list_card, list_layout = _card("标准列表", self)
        self.result_summary = QLabel(list_card)
        self.result_summary.setObjectName("secondaryText")
        list_layout.addWidget(self.result_summary)
        self.standard_table = QTableWidget(list_card)
        _configure_table(
            self.standard_table,
            ("标准编号", "标准名称", "状态", "发布日期", "实施日期"),
        )
        self.standard_table.setMinimumHeight(250)
        list_layout.addWidget(self.standard_table)
        self.body_layout.addWidget(list_card)

        detail_card, detail_layout = _card("标准详情", self)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_host = QWidget(detail_card)
        self.detail_host.setObjectName("standardDetailHost")
        self.detail_layout = QVBoxLayout(self.detail_host)
        self.detail_layout.setContentsMargins(20, 20, 20, 20)
        self.detail_layout.setSpacing(16)
        detail_layout.addWidget(self.detail_host)
        self.body_layout.addWidget(detail_card)
        self.body_layout.addStretch(1)

        search.textChanged.connect(self._refresh)
        self.status_filter.currentIndexChanged.connect(self._refresh)
        self.industry_filter.currentIndexChanged.connect(self._refresh)
        self.year_filter.currentIndexChanged.connect(self._refresh)
        self.standard_table.itemSelectionChanged.connect(self._show_selected_detail)

    def _refresh(self) -> None:
        status = _enum_data(self.status_filter.currentData(), CatalogStatus)
        industry = self.industry_filter.currentData()
        year = self.year_filter.currentData()
        results = self._service.search_standards(
            self.search_input.text(),
            status=status if isinstance(status, CatalogStatus) else CatalogStatus.ALL,
            industry=industry if isinstance(industry, str) else "全部",
            publication_year=year if isinstance(year, int) else None,
        )
        self._standards_by_id = {standard.standard_id: standard for standard, _, _ in results}
        self.standard_table.setRowCount(0)
        for row_number, (standard, visible_status, _) in enumerate(results):
            self.standard_table.insertRow(row_number)
            values = (
                standard.standard_number,
                standard.standard_name,
                self._service.status_label(visible_status),
                _date_text(standard.publication_date),
                _date_text(standard.implementation_date),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, standard.standard_id)
                self.standard_table.setItem(row_number, column, item)
        self.standard_table.resizeRowsToContents()
        self.result_summary.setText(f"共 {len(results)} 项标准")
        if results:
            self.standard_table.selectRow(0)
            self._show_selected_detail()
        else:
            self._clear_detail("没有找到匹配的标准。")

    def _show_selected_detail(self) -> None:
        row = self.standard_table.currentRow()
        if row < 0:
            self._clear_detail("请选择一项标准查看详情。")
            return
        item = self.standard_table.item(row, 0)
        standard_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not isinstance(standard_id, str):
            self._clear_detail("请选择一项标准查看详情。")
            return
        detail = self._service.get_standard_detail(standard_id)
        if detail is None:
            self._clear_detail("该标准详情暂不可用。")
            return
        self.selected_standard_id = standard_id
        self._render_detail(detail)

    def _clear_detail(self, message: str) -> None:
        self.selected_standard_id = None
        _replace_layout_contents(self.detail_layout)
        label = QLabel(message, self.detail_host)
        label.setObjectName("emptyStateDescription")
        label.setWordWrap(True)
        self.detail_layout.addWidget(label)
        self.detail_layout.addStretch(1)

    def _render_detail(self, detail: StandardDetail) -> None:
        _replace_layout_contents(self.detail_layout)
        standard = detail.standard
        header = QWidget(self.detail_host)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        number_label = QLabel(standard.standard_number, header)
        number_label.setObjectName("standardDetailNumber")
        header_layout.addWidget(number_label)
        name_label = QLabel(standard.standard_name, header)
        name_label.setObjectName("standardDetailName")
        name_label.setWordWrap(True)
        header_layout.addWidget(name_label)
        status_label = QLabel(self._service.status_label(detail.status), header)
        status_label.setObjectName("statusBadge")
        status_label.setProperty("catalogStatus", detail.status.value)
        header_layout.addWidget(status_label)

        action_row = QHBoxLayout()
        source_button = QPushButton("查看标准原文", header)
        source_button.setObjectName("viewOfficialSourceButton")
        source_button.setProperty("officialSourceUrl", standard.official_source_url or "")
        source_button.setEnabled(bool(standard.official_source_url))
        if standard.official_source_url:
            source_button.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(standard.official_source_url))
            )
        else:
            source_button.setToolTip("尚未配置标准官方页面。")
        action_row.addWidget(source_button)

        can_start = (
            standard.standard_id == "gbt_32151_34_2024"
            and detail.status is CatalogStatus.CURRENT
        )
        accounting_button = QPushButton(
            "按此标准核算" if can_start else "核算模块待开发",
            header,
        )
        accounting_button.setObjectName("startAccountingButton")
        accounting_button.setEnabled(can_start)
        accounting_button.setProperty("standardId", standard.standard_id)
        if can_start:
            accounting_button.clicked.connect(
                lambda: self.accounting_requested.emit(standard.standard_id)
            )
        else:
            accounting_button.setToolTip("当前版本仅开放已实现的首个行业核算标准。")
        action_row.addWidget(accounting_button)
        action_row.addStretch(1)
        header_layout.addLayout(action_row)
        self.detail_layout.addWidget(header)

        self.detail_layout.addWidget(
            _detail_section(
                "基本信息与官方来源",
                self.detail_host,
                (
                    ("标准编号", standard.standard_number),
                    ("标准名称", standard.standard_name),
                    ("当前状态", self._service.status_label(detail.status)),
                    ("发布日期", _date_text(standard.publication_date)),
                    ("实施日期", _date_text(standard.implementation_date)),
                    ("废止日期", _date_text(standard.abolition_date)),
                    ("发布单位", standard.issuing_authority),
                ),
            )
        )

        verified_placeholder = "暂无已核对的结构化数据。"
        relation_rows = [
            (
                "基础标准 / 通则",
                (
                    "\n".join(
                        f"{item.standard_number} {item.standard_name}"
                        for item in detail.base_standards
                    )
                    if detail.base_standards
                    else verified_placeholder
                ),
            ),
            (
                "替代关系",
                verified_placeholder,
            ),
            (
                "规范性引用文件",
                verified_placeholder,
            ),
        ]
        self.detail_layout.addWidget(
            _detail_section("标准关系", self.detail_host, relation_rows)
        )

        scope_text = (
            standard.notes
            if standard.notes.strip().startswith("适用于")
            else "当前目录尚未录入可追溯的范围原文。"
        )
        self.detail_layout.addWidget(
            _text_section(
                "适用范围",
                self.detail_host,
                scope_text,
            )
        )

        self._add_parameter_section(detail)
        self.detail_layout.addStretch(1)

    def _add_parameter_section(self, detail: StandardDetail) -> None:
        card, layout = _card("参数与因子", self.detail_host)
        if not detail.parameters:
            empty = QLabel("该标准当前没有已核对的参数引用。", card)
            empty.setObjectName("emptyStateDescription")
            empty.setWordWrap(True)
            layout.addWidget(empty)
        else:
            source_by_id = {source.source_id: source for source in self._service.list_sources()}
            factors_by_parameter: dict[str, list[object]] = {}
            for factor in detail.factors:
                factors_by_parameter.setdefault(factor.parameter_id, []).append(factor)
            table = QTableWidget(card)
            _configure_table(table, ("参数/因子", "类型", "数值", "单位", "来源", "依据"))
            for parameter in detail.parameters:
                factors = factors_by_parameter.get(parameter.parameter_id) or [None]
                for factor in factors:
                    row = table.rowCount()
                    table.insertRow(row)
                    source = source_by_id.get(factor.source_id if factor else parameter.source_id)
                    values = (
                        parameter.name,
                        self._service.parameter_type_label(parameter.parameter_type),
                        _decimal_text(factor.value if factor else None),
                        factor.unit if factor else parameter.canonical_unit,
                        source.document_no if source else "—",
                        factor.source_location if factor else parameter.source_location,
                    )
                    for column, value in enumerate(values):
                        table.setItem(row, column, QTableWidgetItem(value))
            table.resizeRowsToContents()
            layout.addWidget(table)
        view_button = QPushButton("查看参数与因子库", card)
        view_button.setObjectName("viewFactorsButton")
        view_button.clicked.connect(lambda: self._navigate(AppRoute.FACTORS))
        layout.addWidget(view_button)
        self.detail_layout.addWidget(card)


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
        self.add_header("参数与因子注册库", "按标准资料查看原表，或在全库搜索已登记的参数与参考值。")
        mode_card, mode_layout = _card("查看方式", self)
        self.view_mode_filter = QComboBox(mode_card)
        self.view_mode_filter.setObjectName("referenceLibraryMode")
        self.view_mode_filter.addItem("按标准/文件查看", "browse")
        self.view_mode_filter.addItem("全库搜索", "search")
        mode_layout.addWidget(self.view_mode_filter)
        self.body_layout.addWidget(mode_card)

        self.browse_card, browse_layout = _card("标准与文件", self)
        browse_filters = QHBoxLayout()
        browse_filters.addWidget(QLabel("资料文件", self.browse_card))
        self.source_filter = QComboBox(self.browse_card)
        self.source_filter.setObjectName("sourceDocumentFilter")
        browse_filters.addWidget(self.source_filter, 2)
        browse_filters.addWidget(QLabel("表格", self.browse_card))
        self.table_filter = QComboBox(self.browse_card)
        self.table_filter.setObjectName("sourceTableFilter")
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
        self.factor_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.factor_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.factor_table.verticalHeader().setVisible(False)
        self.factor_table.horizontalHeader().setStretchLastSection(True)
        self.factor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.factor_table.setWordWrap(True)
        self.factor_table.setMinimumHeight(300)
        browse_layout.addWidget(self.factor_table)
        self.body_layout.addWidget(self.browse_card)

        self.search_card, search_layout = _card("全库搜索", self)
        filters = QHBoxLayout()
        self.search_input = QLineEdit(self.search_card)
        self.search_input.setObjectName("referenceLibrarySearch")
        self.search_input.setPlaceholderText("搜索文件、表号、参数、适用对象或数值")
        filters.addWidget(self.search_input, 3)
        self.search_source_filter = QComboBox(self.search_card)
        self.search_source_filter.setObjectName("searchSourceDocumentFilter")
        self.search_source_filter.addItem("全部资料", None)
        for source in self._service.list_sources():
            self.search_source_filter.addItem(source.document_no, source.source_id)
        filters.addWidget(self.search_source_filter, 2)
        search_layout.addLayout(filters)
        self.result_summary = QLabel("", self.search_card)
        self.result_summary.setObjectName("referenceLibrarySummary")
        search_layout.addWidget(self.result_summary)
        self.search_splitter = QSplitter(Qt.Orientation.Horizontal, self.search_card)
        self.search_splitter.setObjectName("referenceLibrarySplitter")
        self.search_result_table = QTableWidget(self.search_splitter)
        _configure_table(self.search_result_table, ("类别", "资料或参数", "数值", "单位", "来源"))
        self.search_result_table.setObjectName("catalogTable")
        self.search_result_table.setMinimumHeight(320)
        self.factor_detail_host = QWidget(self.search_splitter)
        self.factor_detail_host.setObjectName("parameterDetailHost")
        self.factor_detail_layout = QVBoxLayout(self.factor_detail_host)
        self.factor_detail_layout.setContentsMargins(12, 12, 12, 12)
        self.factor_detail_layout.setSpacing(12)
        self.search_splitter.addWidget(self.search_result_table)
        self.search_splitter.addWidget(self.factor_detail_host)
        self.search_splitter.setStretchFactor(0, 3)
        self.search_splitter.setStretchFactor(1, 2)
        search_layout.addWidget(self.search_splitter)
        self.body_layout.addWidget(self.search_card)
        self.body_layout.addStretch(1)

        self.view_mode_filter.currentIndexChanged.connect(self._change_mode)
        self.source_filter.currentIndexChanged.connect(self._refresh_tables)
        self.table_filter.currentIndexChanged.connect(self._show_source_table)
        self.search_input.textChanged.connect(self._refresh_search)
        self.search_source_filter.currentIndexChanged.connect(self._refresh_search)
        self.search_result_table.itemSelectionChanged.connect(self._show_selected_search_detail)
        self._change_mode()

    def _refresh_sources(self) -> None:
        sources = self._service.list_sources()
        source_by_id = {source.source_id: source for source in sources}
        table_source_ids = {table.source_id for table in self._service.list_source_tables()}
        for source in sources:
            if source.source_id in table_source_ids:
                self.source_filter.addItem(
                    f"{source.document_no} · {source.document_name}", source.source_id
                )
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
        self.browse_card.setVisible(is_browse)
        self.search_card.setVisible(not is_browse)
        if not is_browse:
            self._refresh_search()

    def _refresh_tables(self, *_args: object) -> None:
        source_id = self.source_filter.currentData()
        self.table_filter.blockSignals(True)
        self.table_filter.clear()
        for table in self._service.list_source_tables(source_id if isinstance(source_id, str) else None):
            self.table_filter.addItem(f"{table.display_number} · {table.title}", table.source_table_id)
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
                self.factor_table.setItem(row_number, column, item)
        self.factor_table.resizeRowsToContents()
        self.browse_table_title.setText(f"{table.display_number} · {table.title} · {len(rows)} 行")
        self.browse_table_note.setText(note)

    def _refresh_search(self, *_args: object) -> None:
        source_id = self.search_source_filter.currentData()
        self._search_results = self._service.search_reference_library(
            self.search_input.text(), source_id=source_id if isinstance(source_id, str) else None
        )
        self.search_result_table.setRowCount(0)
        for row_number, result in enumerate(self._search_results):
            self.search_result_table.insertRow(row_number)
            source_label = result.subtitle
            category = {
                "standard": "标准",
                "source": "来源文件",
                "table": "标准表",
                "asset": "参数值",
            }.get(result.result_type, "资料")
            values = (
                category,
                result.title,
                result.value_text or "—",
                result.unit or "—",
                source_label,
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, result.key)
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
                ("适用对象", subject.name if subject else "—"),
                ("参数", parameter.name if parameter else "—"),
                ("数值", f"{format(asset.value, 'f')} {asset.unit}"),
                ("数值类别", self._service.value_type_label(asset.value_type)),
                ("版本", asset.asset_version),
                ("数据说明", asset.notes or "—"),
            )
            self.factor_detail_layout.addWidget(_detail_section("参数值", self.factor_detail_host, rows))
            binding_rows = []
            tables = {item.source_table_id: item for item in self._service.list_source_tables()}
            sources = {item.source_id: item for item in self._service.list_sources()}
            for binding in result.bindings:
                table = tables.get(binding.source_table_id)
                source = sources.get(table.source_id) if table else None
                label = f"{source.document_no} · {table.display_number}" if source and table else "标准资料"
                binding_rows.append((label, binding.source_location))
            if binding_rows:
                self.factor_detail_layout.addWidget(_detail_section("来源与定位", self.factor_detail_host, binding_rows))
            source_ids = tuple(dict.fromkeys(
                tables[binding.source_table_id].source_id
                for binding in result.bindings if binding.source_table_id in tables
            ))
            for source_id in source_ids:
                source = sources.get(source_id)
                if source is None:
                    continue
                source_button = QPushButton(f"打开来源：{source.document_no}", self.factor_detail_host)
                source_button.setObjectName("viewFactorSourceButton")
                source_button.setProperty("officialSourceUrl", source.official_url)
                source_button.setEnabled(bool(source.official_url))
                if source.official_url:
                    source_button.clicked.connect(lambda _checked=False, url=source.official_url: QDesktopServices.openUrl(QUrl(url)))
                else:
                    source_button.setToolTip("该资料尚未配置官方页面。")
                self.factor_detail_layout.addWidget(source_button)
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
