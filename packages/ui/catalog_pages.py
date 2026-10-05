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
    """Global parameter/factor search with object and source views."""

    def __init__(
        self,
        service: CatalogQueryService,
        navigate: Navigate,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.FACTORS, parent)
        self._service = service
        self._navigate = navigate
        self.selected_factor_id: str | None = None
        self._results: tuple[ParameterFactorResult, ...] = ()
        self._build_page()
        self._refresh()

    def _build_page(self) -> None:
        self.add_header("参数与排放因子库", "查看核算参数、缺省值及排放因子")
        appendix_card, appendix_layout = _card("GB/T 32151.34—2024 附录 C 参数表", self)
        appendix_hint = QLabel("选择表名查看只读参数；C.1～C.3 来自正式目录，C.4/C.5 直接读取版本化计算器表。", appendix_card)
        appendix_hint.setWordWrap(True)
        appendix_layout.addWidget(appendix_hint)
        appendix_buttons = QHBoxLayout()
        self.appendix_c_buttons: dict[str, QPushButton] = {}
        for table_id, title in (
            ("C.1", "C.1 化石燃料参数"),
            ("C.2", "C.2 碳酸盐因子"),
            ("C.3", "C.3 其他缺省参数"),
            ("C.4", "C.4 饱和蒸汽焓"),
            ("C.5", "C.5 过热蒸汽焓"),
        ):
            button = QPushButton(title, appendix_card)
            button.setObjectName(f"appendix{table_id.replace('.', '')}Button")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, _table=table_id: self._show_appendix_table(_table))
            self.appendix_c_buttons[table_id] = button
            appendix_buttons.addWidget(button)
        appendix_buttons.addStretch(1)
        appendix_layout.addLayout(appendix_buttons)
        self.appendix_table_title = QLabel("", appendix_card)
        self.appendix_table_title.setObjectName("appendixCSelectedTableTitle")
        appendix_layout.addWidget(self.appendix_table_title)
        self.appendix_table_note = QLabel("", appendix_card)
        self.appendix_table_note.setObjectName("appendixCSelectedTableSource")
        self.appendix_table_note.setWordWrap(True)
        appendix_layout.addWidget(self.appendix_table_note)
        self.appendix_table = QTableWidget(appendix_card)
        self.appendix_table.setObjectName("appendixCReadOnlyTable")
        self.appendix_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.appendix_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.appendix_table.verticalHeader().setVisible(False)
        self.appendix_table.horizontalHeader().setStretchLastSection(True)
        self.appendix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.appendix_table.setWordWrap(True)
        appendix_layout.addWidget(self.appendix_table)
        self.body_layout.addWidget(appendix_card)
        self._show_appendix_table("C.1")

        filters, filters_layout = _card("全局搜索和筛选", self)
        search = QLineEdit(filters)
        search.setObjectName("parameterSearch")
        search.setPlaceholderText("搜索标准号、公告、燃料、物料、参数、温室气体……")
        filters_layout.addWidget(search)
        self.search_input = search

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        self.view_mode_filter = QComboBox(filters)
        self.view_mode_filter.setObjectName("parameterViewModeFilter")
        self.view_mode_filter.addItem("按对象", ParameterViewMode.BY_SUBJECT)
        self.view_mode_filter.addItem("按来源", ParameterViewMode.BY_SOURCE)
        filter_row.addWidget(self.view_mode_filter)

        self.subject_filter = QComboBox(filters)
        self.subject_filter.setObjectName("parameterSubjectFilter")
        self.subject_filter.addItem("全部对象", None)
        for subject in self._service.list_subjects():
            self.subject_filter.addItem(subject.name, subject.subject_id)
        filter_row.addWidget(self.subject_filter)

        self.source_filter = QComboBox(filters)
        self.source_filter.setObjectName("parameterSourceFilter")
        self.source_filter.addItem("全部来源", None)
        for source in self._service.list_sources():
            self.source_filter.addItem(source.document_no, source.source_id)
        filter_row.addWidget(self.source_filter)

        self.type_filter = QComboBox(filters)
        self.type_filter.setObjectName("parameterTypeFilter")
        self.type_filter.addItem("全部参数类型", None)
        for parameter_type in ParameterType:
            self.type_filter.addItem(
                self._service.parameter_type_label(parameter_type), parameter_type
            )
        filter_row.addWidget(self.type_filter)

        self.review_filter = QComboBox(filters)
        self.review_filter.setObjectName("parameterReviewFilter")
        self.review_filter.addItem("全部审核状态", None)
        for review_status in ReviewStatus:
            self.review_filter.addItem(
                self._service.review_status_label(review_status), review_status
            )
        filter_row.addWidget(self.review_filter)

        self.year_filter = QComboBox(filters)
        self.year_filter.setObjectName("parameterYearFilter")
        self.year_filter.addItem("全部年份", None)
        for year in self._service.factor_years():
            self.year_filter.addItem(str(year), year)
        filter_row.addWidget(self.year_filter)
        filter_row.addStretch(1)
        filters_layout.addLayout(filter_row)
        self.body_layout.addWidget(filters)

        list_card, list_layout = _card("参数与因子列表", self)
        self.result_summary = QLabel(list_card)
        self.result_summary.setObjectName("secondaryText")
        list_layout.addWidget(self.result_summary)
        self.factor_table = QTableWidget(list_card)
        _configure_table(
            self.factor_table,
            ("对象", "参数/因子", "数值", "单位", "来源", "状态"),
        )
        self.factor_table.setMinimumHeight(250)
        list_layout.addWidget(self.factor_table)
        self.body_layout.addWidget(list_card)

        detail_card, detail_layout = _card("参数/因子详情", self)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.factor_detail_host = QWidget(detail_card)
        self.factor_detail_host.setObjectName("parameterDetailHost")
        self.factor_detail_layout = QVBoxLayout(self.factor_detail_host)
        self.factor_detail_layout.setContentsMargins(20, 20, 20, 20)
        self.factor_detail_layout.setSpacing(16)
        detail_layout.addWidget(self.factor_detail_host)
        self.body_layout.addWidget(detail_card)
        self.body_layout.addStretch(1)

        search.textChanged.connect(self._refresh)
        for combo in (
            self.view_mode_filter,
            self.subject_filter,
            self.source_filter,
            self.type_filter,
            self.review_filter,
            self.year_filter,
        ):
            combo.currentIndexChanged.connect(self._refresh)
        self.factor_table.itemSelectionChanged.connect(self._show_selected_detail)

    def _show_appendix_table(self, table_id: str) -> None:
        for key, button in self.appendix_c_buttons.items():
            button.setChecked(key == table_id)
        if table_id in {"C.4", "C.5"}:
            headers, rows, note = self._steam_appendix_table(table_id)
        else:
            headers, rows, note = self._canonical_appendix_table(table_id)
        self.appendix_table.clear()
        self.appendix_table.setColumnCount(len(headers))
        self.appendix_table.setHorizontalHeaderLabels(headers)
        self.appendix_table.setRowCount(len(rows))
        for row_number, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.appendix_table.setItem(row_number, column, item)
        self.appendix_table.resizeRowsToContents()
        self.appendix_table_title.setText(f"{table_id} · {len(rows)} 行")
        self.appendix_table_note.setText(note)

    def _canonical_appendix_table(self, table_id: str):
        appendix_code = table_id.replace(".", ".")
        all_parameters = tuple(self._service.repository.list_parameters())
        if table_id == "C.3":
            # C.3 electricity and heat values use canonical entries whose
            # provenance correctly points to their originating publications.
            appendix_parameter_ids = {
                "electricity_emission_factor_national",
                "heat_emission_factor_default",
            }
            parameters = tuple(
                parameter for parameter in all_parameters
                if parameter.parameter_id in appendix_parameter_ids
                and STANDARD_ID in parameter.applicable_standard_ids
            )
        else:
            parameters = tuple(
                parameter for parameter in all_parameters
                if f"表{appendix_code}" in parameter.source_location
                and STANDARD_ID in parameter.applicable_standard_ids
            )
        subjects = {item.subject_id: item.name for item in self._service.repository.list_subjects()}
        factors_by_parameter: dict[str, list[object]] = {}
        for factor in self._service.repository.list_factors():
            if factor.review_status is ReviewStatus.VERIFIED and STANDARD_ID in factor.applicable_standard_ids:
                factors_by_parameter.setdefault(factor.parameter_id, []).append(factor)
        rows: list[tuple[str, ...]] = []
        for parameter in sorted(parameters, key=lambda item: (item.subject_id, item.parameter_id)):
            factors = sorted(factors_by_parameter.get(parameter.parameter_id, ()), key=lambda item: (item.factor_year or 0, item.factor_id))
            for factor in factors:
                if table_id == "C.1" and factor.value_type not in {ValueType.STANDARD_DEFAULT, ValueType.STANDARD_SPECIFIED}:
                    continue
                rows.append((
                    subjects.get(parameter.subject_id, parameter.name),
                    parameter.name,
                    format(factor.value, "f"),
                    factor.unit,
                    f"{factor.source_location} · {factor.factor_year}年",
                ))
        note = "来源：GB/T 32151.34—2024 附录 C 表 " + table_id + "；数值和来源定位直接读取 Canonical 参数/因子目录。"
        if table_id == "C.3":
            note += " 电力显示当前正式目录已收录的官方因子；热力缺省参数沿用 GB/T 32150—2025 共用规则，具体来源见表内定位。"
        headers = ("对象", "参数", "数值", "单位", "标准来源与定位")
        return headers, tuple(rows), note

    @staticmethod
    def _steam_appendix_table(table_id: str):
        values = steam_reference_table_rows(table_id)
        if table_id == "C.4":
            rows = tuple((format(pressure, "f"), format(enthalpy, "f")) for pressure, enthalpy in values)
            return (
                ("压力（MPa）", "饱和蒸汽焓（kJ/kg）"), rows,
                f"来源：GB/T 32151.34—2024 附录 C.4，Mapping §9.5；版本化 Calculator {ALGORITHM_VERSION} 只读数据。原文异常事实继续保留，执行口径按冻结 Mapping 采用 1.70 / 1.80 MPa 解释；非官方勘误。",
            )
        temperatures = tuple(sorted({row[0] for row in values}))
        pressures = tuple(sorted({row[1] for row in values}))
        lookup = {(temperature, pressure): enthalpy for temperature, pressure, enthalpy in values}
        headers = ("温度（℃）", *(f"{pressure:g} MPa" for pressure in pressures))
        rows = tuple(
            (format(temperature, "f"), *(format(lookup[(temperature, pressure)], "f") for pressure in pressures))
            for temperature in temperatures
        )
        return (
            headers, rows,
            f"来源：GB/T 32151.34—2024 附录 C.5，Mapping §9.6；版本化 Calculator {ALGORITHM_VERSION} 只读数据。蒸汽焓自动计算留待后续 UAT01-B。",
        )

    def _refresh(self) -> None:
        view_mode = _enum_data(self.view_mode_filter.currentData(), ParameterViewMode)
        subject_id = self.subject_filter.currentData()
        source_id = self.source_filter.currentData()
        parameter_type = _enum_data(self.type_filter.currentData(), ParameterType)
        review_status = _enum_data(self.review_filter.currentData(), ReviewStatus)
        factor_year = self.year_filter.currentData()
        self._results = self._service.search_parameter_factors(
            self.search_input.text(),
            view_mode=view_mode if isinstance(view_mode, ParameterViewMode) else ParameterViewMode.BY_SUBJECT,
            subject_id=subject_id if isinstance(subject_id, str) else None,
            source_id=source_id if isinstance(source_id, str) else None,
            parameter_type=parameter_type if isinstance(parameter_type, ParameterType) else None,
            review_status=review_status if isinstance(review_status, ReviewStatus) else None,
            factor_year=factor_year if isinstance(factor_year, int) else None,
        )
        self.factor_table.setRowCount(0)
        by_source = view_mode is ParameterViewMode.BY_SOURCE
        if by_source:
            self.factor_table.setHorizontalHeaderLabels(
                ("来源", "参数/因子", "对象", "数值", "单位", "审核状态")
            )
        else:
            self.factor_table.setHorizontalHeaderLabels(
                ("对象", "参数/因子", "数值", "单位", "来源", "状态")
            )
        for row_number, result in enumerate(self._results):
            self.factor_table.insertRow(row_number)
            factor = result.factor
            source_name = result.source.document_no if result.source else "—"
            value = _decimal_text(factor.value if factor else None)
            unit = factor.unit if factor else result.parameter.canonical_unit
            state = (
                self._service.value_category_label(self._service.value_category(factor))
                + " · "
                + self._service.review_status_label(factor.review_status)
                if factor
                else self._service.review_status_label(result.parameter.review_status)
            )
            if by_source:
                values = (source_name, result.parameter.name, result.subject.name, value, unit, state)
            else:
                values = (result.subject.name, result.parameter.name, value, unit, source_name, state)
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        factor.factor_id if factor else result.parameter.parameter_id,
                    )
                self.factor_table.setItem(row_number, column, item)
        self.factor_table.resizeRowsToContents()
        self.result_summary.setText(f"共 {len(self._results)} 项参数/因子")
        if self._results:
            self.factor_table.selectRow(0)
            self._show_selected_detail()
        else:
            self._clear_detail("没有找到匹配的参数或因子。")

    def _show_selected_detail(self) -> None:
        row = self.factor_table.currentRow()
        if row < 0 or row >= len(self._results):
            self._clear_detail("请选择一项参数或因子查看详情。")
            return
        result = self._results[row]
        self.selected_factor_id = result.factor.factor_id if result.factor else result.parameter.parameter_id
        self._render_detail(result)

    def _clear_detail(self, message: str) -> None:
        self.selected_factor_id = None
        _replace_layout_contents(self.factor_detail_layout)
        label = QLabel(message, self.factor_detail_host)
        label.setObjectName("emptyStateDescription")
        label.setWordWrap(True)
        self.factor_detail_layout.addWidget(label)
        self.factor_detail_layout.addStretch(1)

    def _render_detail(self, result: ParameterFactorResult) -> None:
        _replace_layout_contents(self.factor_detail_layout)
        parameter = result.parameter
        factor = result.factor
        source = result.source
        heading = QLabel(parameter.name, self.factor_detail_host)
        heading.setObjectName("parameterDetailName")
        heading.setWordWrap(True)
        self.factor_detail_layout.addWidget(heading)

        rows: list[tuple[str, str]] = [
            ("对象", result.subject.name),
            ("参数类型", self._service.parameter_type_label(parameter.parameter_type)),
            ("数值", _decimal_text(factor.value if factor else None)),
            ("单位", factor.unit if factor else parameter.canonical_unit),
            (
                "值分类",
                self._service.value_category_label(self._service.value_category(factor))
                if factor
                else "参数定义",
            ),
            ("数据类别", self._service.value_type_label(factor.value_type) if factor else "暂无已核对数值"),
            (
                "审核状态",
                self._service.review_status_label(factor.review_status if factor else parameter.review_status),
            ),
        ]
        if factor is not None:
            rows.extend(
                (
                    ("因子年度", str(factor.factor_year)),
                    ("适用起始日期", _date_text(factor.valid_from)),
                    ("适用结束日期", _date_text(factor.valid_to)),
                    ("适用标准", self._standard_text(factor.applicable_standard_ids)),
                    ("依据定位", factor.source_location),
                )
            )
        else:
            rows.extend(
                (
                    ("适用标准", self._standard_text(parameter.applicable_standard_ids)),
                    ("依据定位", parameter.source_location),
                )
            )
        self.factor_detail_layout.addWidget(
            _detail_section("参数值", self.factor_detail_host, rows)
        )

        if source is not None:
            self.factor_detail_layout.addWidget(
                _detail_section(
                    "来源追溯",
                    self.factor_detail_host,
                    (
                        ("来源文件", source.document_no),
                        ("来源名称", source.document_name),
                        ("来源类型", self._service.source_type_label(source.source_type)),
                        ("发布单位", source.publisher),
                        ("发布日期", _date_text(source.publication_date)),
                        ("官方页面", "已配置" if source.official_url else "未配置"),
                        ("来源备注", source.notes),
                    ),
                )
            )
            source_button = QPushButton("查看官方来源", self.factor_detail_host)
            source_button.setObjectName("viewFactorSourceButton")
            source_button.setEnabled(bool(source.official_url))
            if source.official_url:
                source_button.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl(source.official_url))
                )
            else:
                source_button.setToolTip("尚未配置来源官方页面。")
            self.factor_detail_layout.addWidget(source_button)
        else:
            self.factor_detail_layout.addWidget(
                _detail_section("来源追溯", self.factor_detail_host, (("来源", "暂无已配置来源。"),))
            )

        self.factor_detail_layout.addWidget(
            _detail_section(
                "数据说明",
                self.factor_detail_host,
                (
                    ("参数说明", parameter.notes or "—"),
                    ("因子说明", factor.notes if factor else "—"),
                ),
            )
        )
        self.factor_detail_layout.addStretch(1)

    def _standard_text(self, standard_ids: tuple[str, ...]) -> str:
        standards = {standard.standard_id: standard for standard, _, _ in self._service.search_standards()}
        return "\n".join(
            f"{standards[standard_id].standard_number} {standards[standard_id].standard_name}"
            for standard_id in standard_ids
            if standard_id in standards
        ) or "—"
