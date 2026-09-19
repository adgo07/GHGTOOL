"""Business-neutral pages and safe empty/placeholder states."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import AccountingRecord, RecordStatus
from packages.core.repositories import RecordRepository

from .design_tokens import WIDE_PAGE_MARGIN
from .view_models import AppRoute, ShellViewModel


Navigate = Callable[[AppRoute], None]


class BasePage(QWidget):
    """Page base with the common title/body layout and responsive margin hook."""

    def __init__(self, route: AppRoute, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.route = route
        self.setObjectName(f"page_{route.value}")
        self.body_layout = QVBoxLayout(self)
        self.body_layout.setContentsMargins(
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
            WIDE_PAGE_MARGIN,
        )
        self.body_layout.setSpacing(24)

    def set_page_margin(self, margin: int) -> None:
        self.body_layout.setContentsMargins(margin, margin, margin, margin)

    def add_header(self, title: str, description: str) -> None:
        header = QWidget(self)
        header.setObjectName("pageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_label = QLabel(title, header)
        title_label.setObjectName("pageTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)

        description_label = QLabel(description, header)
        description_label.setObjectName("pageDescription")
        description_label.setWordWrap(True)
        header_layout.addWidget(description_label)
        self.body_layout.addWidget(header)


def _card(title: str, parent: QWidget) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame(parent)
    card.setObjectName("card")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)
    title_label = QLabel(title, card)
    title_label.setObjectName("cardTitle")
    layout.addWidget(title_label)
    return card, layout


class HomePage(BasePage):
    """Professional workbench home with records-backed recent-work sections."""

    def __init__(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
        parent: QWidget | None = None,
        record_repository: RecordRepository | None = None,
    ) -> None:
        super().__init__(AppRoute.HOME, parent)
        self.record_repository = record_repository
        self.add_header(view_model.home_title, view_model.home_description)

        workspace = QWidget(self)
        workspace.setObjectName("primaryWorkspace")
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(24)

        start_panel, start_layout = _card("开始", workspace)
        start_panel.setObjectName("startPanel")
        start_panel.setFixedWidth(320)

        primary_button = QPushButton(view_model.primary_action_label, start_panel)
        primary_button.setObjectName("primaryButton")
        primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        primary_button.clicked.connect(lambda: navigate(AppRoute.NEW_ACCOUNTING))
        start_layout.addWidget(primary_button)

        excel_button = QPushButton(view_model.excel_action_label, start_panel)
        excel_button.setObjectName("reservedButton")
        excel_button.setProperty("reserved", True)
        excel_button.setCursor(Qt.CursorShape.ArrowCursor)
        excel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        excel_button.clicked.connect(lambda: navigate(AppRoute.EXCEL_IMPORT))
        start_layout.addWidget(excel_button)

        standards_button = QPushButton(view_model.standards_action_label, start_panel)
        standards_button.setObjectName("secondaryButton")
        standards_button.setCursor(Qt.CursorShape.PointingHandCursor)
        standards_button.clicked.connect(lambda: navigate(AppRoute.STANDARDS))
        start_layout.addWidget(standards_button)
        start_layout.addStretch(1)

        self.recent_work, self.recent_layout = _card("最近核算记录", workspace)
        self.recent_work.setObjectName("recentWorkCard")
        workspace_layout.addWidget(start_panel)
        workspace_layout.addWidget(self.recent_work, 1)
        self.body_layout.addWidget(workspace)
        self.refresh_recent_records()

        recent_standards, standards_layout = _card("最近使用标准", self)
        recent_standards.setObjectName("recentStandardsCard")
        if view_model.recent_standards:
            for standard in view_model.recent_standards[:5]:
                row = QLabel(f"{standard.standard_id}\n{standard.title}", recent_standards)
                row.setObjectName("bodyText")
                row.setWordWrap(True)
                standards_layout.addWidget(row)
        else:
            empty_standards = QLabel("暂无最近使用标准", recent_standards)
            empty_standards.setObjectName("emptyStateDescription")
            standards_layout.addWidget(empty_standards)
        self.body_layout.addWidget(recent_standards)

        status = QLabel(view_model.status_summary, self)
        status.setObjectName("statusSummary")
        status.setWordWrap(True)
        self.body_layout.addWidget(status)
        self.body_layout.addStretch(1)

    def refresh_recent_records(self) -> None:
        """Refresh the home card from the active records repository."""

        while self.recent_layout.count() > 1:
            item = self.recent_layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        records = tuple(self.record_repository.list_all()[:8]) if self.record_repository is not None else ()
        if not records:
            empty_title = QLabel("尚无核算记录", self.recent_work)
            empty_title.setObjectName("emptyStateTitle")
            self.recent_layout.addWidget(empty_title)
            empty_description = QLabel(
                "可以通过“新建核算”手工开始。\nExcel 导入功能将在后续版本开放。",
                self.recent_work,
            )
            empty_description.setObjectName("emptyStateDescription")
            empty_description.setWordWrap(True)
            self.recent_layout.addWidget(empty_description)
            self.recent_layout.addStretch(1)
            return
        for record in records:
            period = f"{record.input_snapshot.period.start} 至 {record.input_snapshot.period.end}"
            row = QLabel(
                f"{record.input_snapshot.enterprise_name or '未填写企业'} · {period} · "
                f"{record.standard_id} · {record.calculation_result.total_amount} "
                f"{record.calculation_result.total_unit} · {record.status.value}",
                self.recent_work,
            )
            row.setObjectName("bodyText")
            row.setWordWrap(True)
            self.recent_layout.addWidget(row)
        self.recent_layout.addStretch(1)

class PlaceholderPage(BasePage):
    """Reachable G03 route with no later-stage business implementation."""

    def __init__(
        self,
        route: AppRoute,
        title: str,
        description: str,
        message: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(route, parent)
        self.add_header(title, description)
        card, layout = _card("当前版本", self)
        message_label = QLabel(message, card)
        message_label.setObjectName("emptyStateDescription")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        layout.addStretch(1)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)


class RecordLibraryPage(BasePage):
    """Read-only record ledger with searchable, auditable deletion."""

    def __init__(self, record_repository: RecordRepository | None, parent: QWidget | None = None) -> None:
        super().__init__(AppRoute.RECORDS, parent)
        self.record_repository = record_repository
        self._records: tuple[AccountingRecord, ...] = ()
        self.add_header("核算记录", "查看成功核算的不可编辑历史记录；删除只做软删除并保留审计证据。")

        filter_card, filter_layout = _card("检索与筛选", self)
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit(filter_card)
        self.search_input.setObjectName("recordSearchInput")
        self.search_input.setPlaceholderText("搜索企业名称、记录编号或标准编号")
        self.search_input.textChanged.connect(self.refresh_records)
        filter_row.addWidget(self.search_input, 1)
        self.status_filter = QComboBox(filter_card)
        self.status_filter.setObjectName("recordStatusFilter")
        self.status_filter.addItem("全部状态", "ALL")
        self.status_filter.addItem("已完成", RecordStatus.COMPLETED.value)
        self.status_filter.addItem("含警告", RecordStatus.COMPLETED_WITH_WARNINGS.value)
        self.status_filter.currentIndexChanged.connect(self.refresh_records)
        filter_row.addWidget(self.status_filter)
        filter_layout.addLayout(filter_row)
        self.body_layout.addWidget(filter_card)

        content = QWidget(self)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        self.record_list = QListWidget(content)
        self.record_list.setObjectName("recordList")
        self.record_list.currentRowChanged.connect(self._show_selected_record)
        content_layout.addWidget(self.record_list, 1)

        detail_card, detail_layout = _card("只读详情", content)
        self.detail_text = QTextEdit(detail_card)
        self.detail_text.setObjectName("recordDetailView")
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        self.delete_button = QPushButton("删除记录", detail_card)
        self.delete_button.setObjectName("deleteRecordButton")
        self.delete_button.clicked.connect(self._delete_selected)
        detail_layout.addWidget(self.delete_button)
        content_layout.addWidget(detail_card, 2)
        self.body_layout.addWidget(content, 1)
        self.refresh_records()

    def refresh_records(self, *_args: object) -> None:
        all_records = tuple(self.record_repository.list_all()) if self.record_repository is not None else ()
        query = self.search_input.text().strip().casefold()
        status = self.status_filter.currentData()
        self._records = tuple(
            record
            for record in all_records
            if (status == "ALL" or record.status.value == status)
            and (
                not query
                or query in record.record_id.casefold()
                or query in record.standard_id.casefold()
                or query in (record.input_snapshot.enterprise_name or "").casefold()
            )
        )
        self.record_list.clear()
        for record in self._records:
            period = f"{record.input_snapshot.period.start} 至 {record.input_snapshot.period.end}"
            self.record_list.addItem(
                f"{record.input_snapshot.enterprise_name or '未填写企业'} · {period} · "
                f"{record.calculation_result.total_amount} {record.calculation_result.total_unit} · "
                f"{record.status.value}"
            )
            self.record_list.item(self.record_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, record.record_id
            )
        self.delete_button.setEnabled(bool(self._records))
        if self._records:
            self.record_list.setCurrentRow(0)
        else:
            self.detail_text.setPlainText("暂无符合条件的核算记录。")

    def _show_selected_record(self, row: int) -> None:
        if row < 0 or row >= len(self._records):
            self.detail_text.clear()
            return
        record = self._records[row]
        warnings = tuple(
            problem
            for problem in (*record.problems, *record.calculation_result.problems)
            if problem.level.value == "WARNING"
        )
        snapshots = "\n".join(
            f"- {item.parameter_id}：{item.value_used} {item.unit_used}；"
            f"因子 {item.factor_id or '无'}；来源 {item.source_id or '无'}；"
            f"理由 {item.selection_reason}"
            for item in record.parameter_snapshots
        ) or "- 无参数快照"
        source_judgments = "\n".join(
            f"- {item.source_id}：{'涉及' if item.included else '不涉及'}"
            for item in record.input_snapshot.emission_sources
        ) or "- 未记录排放源判断"
        result_lines = "\n".join(
            f"- {item.line_id}：{item.amount} {item.unit}"
            for item in record.calculation_result.lines
        ) or "- 无结果分项"
        warning_text = "\n".join(f"- {item.code}：{item.message}" for item in warnings) or "- 无"
        raw_snapshot = getattr(self.record_repository, "get_raw_input_snapshot", lambda _record_id: None)(record.record_id)
        rule_snapshot = getattr(self.record_repository, "get_effective_rule_set", lambda _record_id: None)(record.record_id)
        raw_fields = ", ".join(sorted(raw_snapshot)) if isinstance(raw_snapshot, dict) else "未由当前仓储暴露"
        rule_ids = ", ".join(str(item) for item in (rule_snapshot or {}).get("rule_ids", ())) or "未记录额外规则 ID"
        self.detail_text.setPlainText(
            f"记录编号：{record.record_id}\n"
            f"创建时间：{record.created_at.isoformat()}\n"
            f"企业名称：{record.input_snapshot.enterprise_name or '未填写企业'}\n"
            f"核算期间：{record.input_snapshot.period.start} 至 {record.input_snapshot.period.end}\n"
            f"标准版本：{record.standard_id}\n"
            f"算法版本：{record.algorithm_version}\n"
            f"状态：{record.status.value}\n"
            f"总排放量：{record.calculation_result.total_amount} {record.calculation_result.total_unit}\n"
            f"\n排放源判断：\n{source_judgments}\n"
            f"\n有效规则集：\n- {rule_ids}\n"
            f"原始输入快照字段：{raw_fields}\n"
            f"\n结果分项：\n{result_lines}\n"
            f"\n参数来源快照：\n{snapshots}\n"
            f"\n警告：\n{warning_text}\n"
            "\n本详情只读；历史记录不会被重新计算或覆盖。"
        )
    def _delete_selected(self) -> None:
        row = self.record_list.currentRow()
        if row < 0 or row >= len(self._records) or self.record_repository is None:
            return
        record = self._records[row]
        answer = QMessageBox.question(
            self,
            "确认删除核算记录",
            f"将删除记录 {record.record_id}。该操作不会物理删除审计证据，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete = getattr(self.record_repository, "delete", None)
        if callable(delete):
            delete(record.record_id, actor="current_user", reason="用户二次确认删除")
        self.refresh_records()

class ExcelImportPage(BasePage):
    """Non-interactive Excel placeholder; no file or import action is wired."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(AppRoute.EXCEL_IMPORT, parent)
        self.add_header("Excel 导入", "通过标准化模板快速导入核算数据")

        card, layout = _card("功能预留，当前版本暂未开放。", self)
        controls = QWidget(card)
        controls.setObjectName("disabledImportControls")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        file_input = QLineEdit(controls)
        file_input.setObjectName("reservedInput")
        file_input.setPlaceholderText("文件选择将在后续版本开放")
        file_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        controls_layout.addWidget(file_input)
        self.file_input = file_input

        standard_input = QComboBox(controls)
        standard_input.setObjectName("reservedInput")
        standard_input.addItem("标准选择将在后续版本开放")
        standard_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        controls_layout.addWidget(standard_input)
        self.standard_input = standard_input

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        for object_name, label in (
            ("selectFileButton", "选择文件"),
            ("templateButton", "模板下载"),
            ("nextButton", "下一步"),
            ("importButton", "导入"),
        ):
            button = QPushButton(label, controls)
            button.setObjectName("reservedControl")
            button.setProperty("controlName", object_name)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button_row.addWidget(button)
            setattr(self, object_name, button)
        controls_layout.addLayout(button_row)
        controls.setEnabled(False)
        layout.addWidget(controls)
        layout.addStretch(1)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)


def create_page(
    route: AppRoute,
    view_model: ShellViewModel,
    navigate: Navigate,
    parent: QWidget | None = None,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
) -> QWidget:
    """Create exactly one page for a validated public route."""

    if route is AppRoute.HOME:
        return HomePage(view_model, navigate, parent, record_repository=record_repository)
    if route is AppRoute.EXCEL_IMPORT:
        return ExcelImportPage(parent)
    if route is AppRoute.STANDARDS:
        from .catalog_pages import StandardLibraryPage

        return StandardLibraryPage(catalog_service or CatalogQueryService.empty(), navigate, parent)
    if route is AppRoute.FACTORS:
        from .catalog_pages import ParameterFactorLibraryPage

        return ParameterFactorLibraryPage(
            catalog_service or CatalogQueryService.empty(), navigate, parent
        )
    if route is AppRoute.RECORDS:
        return RecordLibraryPage(record_repository, parent)
    if route is AppRoute.NEW_ACCOUNTING:
        from .carbon_material_page import CarbonMaterialAccountingPage

        return CarbonMaterialAccountingPage(
            catalog_service=catalog_service or CatalogQueryService.empty(),
            record_repository=record_repository,
            parent=parent,
        )

    placeholders = {
        AppRoute.STANDARDS: (
            "标准库",
            "查看 GB/T 32151 系列标准及核算要求",
            "标准库详细查询将在后续阶段实现。当前版本仅提供公共导航入口。",
        ),

        AppRoute.RECORDS: (
            "核算记录",
            "查看历史核算结果",
            "核算记录台账将在后续阶段实现。",
        ),
        AppRoute.FACTORS: (
            "参数与因子库",
            "查看核算参数、缺省值及排放因子",
            "参数与排放因子查询将在后续阶段实现。",
        ),
        AppRoute.SETTINGS: (
            "设置",
            "管理软件级低频功能",
            "设置项将在后续阶段按统一规范实现。",
        ),
    }
    try:
        title, description, message = placeholders[route]
    except KeyError as exc:
        raise ValueError(f"unsupported G03 route: {route!r}") from exc
    return PlaceholderPage(route, title, description, message, parent)
