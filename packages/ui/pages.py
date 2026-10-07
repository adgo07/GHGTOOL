"""Business-neutral pages and safe empty/placeholder states."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QTextEdit,
    QTabWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from packages.application.catalog_queries import CatalogQueryService
from packages.application.reporting import build_saved_record_report
from packages.core.models import AccountingRecord, RecordStatus
from packages.core.repositories import RecordRepository
from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.infrastructure.reporting import render_report_docx
from .record_experience import (
    SnapshotState,
    build_activity_evidence_view,
    build_home_record_label,
    build_parameter_view,
    build_professional_view,
    build_quality_view,
    build_record_list_label,
    build_report_view,
    evidence_names_for,
    format_amount,
    snapshot_state,
    summary_with_trace,
)

from .design_tokens import WIDE_PAGE_MARGIN
from .view_models import AppRoute, ShellViewModel


Navigate = Callable[[AppRoute], None]


_SNAPSHOT_LABELS = {
    "input_id": "输入编号",
    "enterprise_id": "企业编号",
    "enterprise_name": "企业名称",
    "period": "核算期间",
    "accounting_period": "核算期间",
    "period_type": "期间类型",
    "start": "开始日期",
    "end": "结束日期",
    "boundary_confirmed": "核算边界确认",
    "boundary_component_ids": "边界范围",
    "source_states": "排放源状态",
    "emission_sources": "排放源状态",
    "source_judgment": "排放源判断",
    "status": "状态",
    "fuel_inputs": "燃料活动数据",
    "calcination": "煅烧活动数据",
    "baking": "焙烧/炭化活动数据",
    "graphitization": "石墨化活动数据",
    "fume_incineration": "烟气焚烧治理活动数据",
    "fgd": "烟气脱硫净化活动数据",
    "electricity_details": "电力明细",
    "exported_electricity": "输出电力",
    "purchased_heat": "外购热力",
    "exported_heat": "输出热力",
    "other_activity_present": "其他行业活动",
    "transport_present": "上下游运输",
    "fuel_id": "燃料编号",
    "path": "燃料路径",
    "activity": "活动量",
    "activity_amount": "活动量",
    "carbon_content": "含碳量",
    "oxidation_rate": "氧化率",
    "lower_heating_value": "低位发热量",
    "electricity_detail_id": "关联电力明细",
    "detail_id": "明细编号",
    "electricity_amount": "用电量",
    "amount": "数量",
    "electricity_unit": "用电量单位",
    "unit": "单位",
    "acquisition_mode": "取得方式",
    "attribute": "电力属性",
    "proof_type": "证明类型",
    "proof_status": "证明状态",
    "proof": "证明材料",
    "proof_reference": "证明编号/定位",
    "evidence": "证明材料",
    "evidence_reference": "证明编号/定位",
    "mass_basis": "质量基准",
    "composition_basis": "成分基准",
    "normalized_basis": "折算基准",
    "component_kind": "成分性质",
    "fixed_carbon_component_kind": "固定碳成分性质",
    "volatile_matter_component_kind": "挥发分成分性质",
    "moisture_evidence": "水分修正证明",
    "conversion_evidence": "换算证明",
    "carbon_output_included_in_input": "碳产品是否计入投入",
    "furnace_loss_included": "炉损是否计入",
    "value": "数值",
    "source_type": "数据来源类型",
    "source_level": "数据来源级别",
    "source_reference": "数据来源说明",
    "parameter_id": "参数编号",
    "source_kind": "参数来源类型",
    "source_id": "来源编号",
    "source_version": "来源版本",
    "source_location": "来源定位",
    "selection_reason": "选择理由",
    "factor_id": "因子编号",
    "factor_year": "因子年份",
    "line_id": "明细编号",
    "enthalpy": "焓值",
    "steam_kind": "蒸汽类型",
    "pressure_mpa": "压力",
    "temperature_c": "温度",
    "components": "碳酸盐组分",
    "cal": "碳酸盐用量",
    "i": "碳酸盐含量",
    "ef1": "排放因子",
    "tr": "转化率",
    "reporting_data": "报告信息与数据来源",
    "organization_nature": "单位性质",
    "industry": "所属行业",
    "social_credit_code": "统一社会信用代码",
    "legal_representative": "法定代表人",
    "preparer_name": "填报负责人",
    "preparer_contact": "负责人联系方式",
    "boundary_description": "核算边界说明",
    "products_and_process": "主要产品/工艺流程",
    "emission_source_identification": "排放源识别说明",
    "other_report_information": "其他报告说明",
    "activity_evidence": "活动数据来源证据",
    "measured_factor_evidence": "实测因子证据",
    "applies_to": "适用范围",
    "monitoring_location": "监测地点",
    "monitoring_method": "获取/监测方法",
    "instrument": "仪器/计量设备",
    "accuracy": "设备精度",
    "recording_frequency": "记录频次",
    "acquisition_time": "数据取得时间",
    "sampling_method": "取样方法",
    "sampling_frequency": "取样频次",
    "testing_method": "检测方法",
    "testing_frequency": "检测频次",
    "referenced_standard": "依据标准",
    "reason": "采用理由/说明",
}

_SNAPSHOT_VALUE_LABELS = {
    "ANNUAL": "年度",
    "MONTHLY": "月度",
    "PRIMARY": "原始数据",
    "SECONDARY": "次级数据",
    "PROXY": "替代数据",
    "MANUAL": "手工录入",
    "METER": "计量数据",
    "INVOLVED": "涉及",
    "NOT_INVOLVED": "不涉及",
    "UNCONFIRMED": "未确认",
    "PURCHASED": "外购",
    "SELF_CONSUMED": "自发自用",
    "ORDINARY": "常规电力",
    "NONFOSSIL": "非化石能源电力",
    "FOSSIL": "化石能源电力",
    "NONE": "无证明",
    "CONTRACT_AND_SETTLEMENT": "合同及结算凭证",
    "GEC": "绿证",
    "MONTHLY_ORIGINAL_RECORD": "月度原始记录",
    "NOT_PROVIDED": "未提供",
    "VALID": "有效",
    "INVALID": "无效",
    "RECEIVED": "收到基",
    "DRY": "干基",
    "OTHER_DOCUMENTED": "其他有证明基准",
    "UNKNOWN": "未确认",
    "FIXED_CARBON": "固定碳",
    "VOLATILE_MATTER": "挥发分",
    "TOTAL_CARBON": "总碳",
    "SATURATED": "饱和蒸汽",
    "SUPERHEATED": "过热蒸汽",
    "STANDARD_DEFAULT": "标准缺省值",
    "STANDARD_SPECIFIED": "标准规定值",
    "MEASURED": "实测值",
    "CALCULATED": "计算值",
    "OFFICIAL_PUBLISHED": "官方发布值",
    "USER_DEFINED": "用户指定值",
    "PROJECT_SPECIFIED": "项目指定值",
}

_SNAPSHOT_ACTIVITY_KEYS = (
    "activity_amount",
    "fuel_inputs",
    "calcination",
    "baking",
    "graphitization",
    "fume_incineration",
    "fgd",
    "purchased_heat",
    "exported_heat",
    "exported_electricity",
)
_SNAPSHOT_SOURCE_KEYS = ("source_states", "emission_sources", "source_judgment")
_SNAPSHOT_ELECTRICITY_KEYS = ("electricity_details",)
_SNAPSHOT_PROOF_KEYS = frozenset(
    {"proof", "proof_type", "proof_status", "proof_reference", "evidence", "evidence_reference"}
)
_SNAPSHOT_INTERNAL_EVIDENCE_KEYS = frozenset({"evidence_id", "source_ids", "evidence_ref_ids"})


def _snapshot_label(key: object) -> str:
    key_text = str(key)
    if key_text.endswith("电力明细证明"):
        return key_text
    return _SNAPSHOT_LABELS.get(key_text, f"其他信息（{key_text}）")


def _snapshot_scalar(value: Any) -> str:
    if value is None:
        return "未填写"
    if isinstance(value, bool):
        return "是" if value else "否"
    return _SNAPSHOT_VALUE_LABELS.get(str(value), str(value))


def _snapshot_measurement(value: dict[str, Any]) -> str:
    amount = _snapshot_scalar(value.get("value"))
    unit = value.get("unit")
    text = f"{amount} {unit}".strip() if unit else amount
    extras = []
    for key in (
        "source_type",
        "source_level",
        "source_reference",
        "source_kind",
        "source_id",
        "source_version",
        "source_location",
        "selection_reason",
        "factor_id",
        "factor_year",
    ):
        if value.get(key) not in (None, "", [], {}):
            extras.append(f"{_snapshot_label(key)}：{_snapshot_scalar(value[key])}")
    return "；".join((text, *extras))


def _snapshot_lines(
    value: Any,
    *,
    indent: str = "",
    excluded_keys: frozenset[str] = _SNAPSHOT_INTERNAL_EVIDENCE_KEYS,
) -> list[str]:
    if isinstance(value, dict):
        if "value" in value and "unit" in value:
            return [f"{indent}{_snapshot_measurement(value)}"]
        lines: list[str] = []
        paired_keys: set[str] = set()
        for amount_key, unit_key, label in (
            ("electricity_amount", "electricity_unit", "用电量"),
            ("amount", "unit", "数量"),
        ):
            if value.get(amount_key) not in (None, "", [], {}) and value.get(unit_key) not in (None, "", [], {}):
                lines.append(
                    f"{indent}{label}：{_snapshot_scalar(value[amount_key])} {_snapshot_scalar(value[unit_key])}"
                )
                paired_keys.update((amount_key, unit_key))
        for key, item in value.items():
            if str(key) in excluded_keys or str(key) in paired_keys or item in (None, "", [], {}):
                continue
            label = _snapshot_label(key)
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}{label}：")
                lines.extend(_snapshot_lines(item, indent=indent + "  ", excluded_keys=excluded_keys))
            else:
                lines.append(f"{indent}{label}：{_snapshot_scalar(item)}")
        return lines or [f"{indent}未记录"]
    if isinstance(value, list):
        lines = []
        for index, item in enumerate(value, 1):
            lines.append(f"{indent}第{index}项：")
            lines.extend(_snapshot_lines(item, indent=indent + "  ", excluded_keys=excluded_keys))
        return lines or [f"{indent}未记录"]
    return [f"{indent}{_snapshot_scalar(value)}"]


def _format_business_snapshot(raw_snapshot: object) -> str:
    """Render the immutable raw snapshot as business-oriented read-only sections."""

    if not isinstance(raw_snapshot, dict):
        return "无法读取历史输入快照。"

    lines: list[str] = []
    activity = {key: raw_snapshot[key] for key in _SNAPSHOT_ACTIVITY_KEYS if key in raw_snapshot}
    sources = {key: raw_snapshot[key] for key in _SNAPSHOT_SOURCE_KEYS if key in raw_snapshot}
    electricity = {key: raw_snapshot[key] for key in _SNAPSHOT_ELECTRICITY_KEYS if key in raw_snapshot}
    proof = {key: raw_snapshot[key] for key in raw_snapshot if key in _SNAPSHOT_PROOF_KEYS}
    for index, detail in enumerate(raw_snapshot.get("electricity_details") or (), 1):
        if isinstance(detail, dict):
            detail_proof = {key: detail[key] for key in detail if key in _SNAPSHOT_PROOF_KEYS}
            if detail_proof:
                proof[f"第{index}条电力明细证明"] = detail_proof

    consumed = set(activity) | set(sources) | set(electricity) | set(proof) | {"reporting_data"}
    other = {key: value for key, value in raw_snapshot.items() if key not in consumed}
    sections = (
        ("活动数据", activity),
        ("排放源", sources),
        ("电力明细", electricity),
        ("证明状态", proof),
        ("其他输入", other),
    )
    for title, section in sections:
        lines.append(f"【{title}】")
        if title == "电力明细":
            lines.extend(_snapshot_lines(section, indent="  ", excluded_keys=_SNAPSHOT_PROOF_KEYS))
        else:
            lines.extend(_snapshot_lines(section, indent="  "))
    return "\n".join(lines)


def _format_reporting_snapshot(reporting_snapshot: object) -> str:
    if not isinstance(reporting_snapshot, dict) or not reporting_snapshot:
        return "历史记录未保存该信息。"
    return "\n".join(
        _snapshot_lines(reporting_snapshot, excluded_keys=_SNAPSHOT_INTERNAL_EVIDENCE_KEYS)
    )


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
        excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
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
                row = QLabel(str(standard.title or "标准名称未记录"), recent_standards)
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
                "可以通过“新建核算”手工开始，或使用 Excel 模板预览。\n预览不会保存项目或生成正式核算记录。",
                self.recent_work,
            )
            empty_description.setObjectName("emptyStateDescription")
            empty_description.setWordWrap(True)
            self.recent_layout.addWidget(empty_description)
            self.recent_layout.addStretch(1)
            return
        for record in records:
            row = QLabel(build_home_record_label(record), self.recent_work)
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
    """Snapshot-backed business views over immutable calculation records."""

    def __init__(
        self,
        record_repository: RecordRepository | None,
        parent: QWidget | None = None,
        project_service=None,
    ) -> None:
        super().__init__(AppRoute.RECORDS, parent)
        self.record_repository = record_repository
        self.project_service = project_service
        self._records: tuple[AccountingRecord, ...] = ()
        self.add_header("核算记录", "按业务信息查看已保存的核算结果和标准报告数据；历史记录只读。")

        filter_card, filter_layout = _card("检索与筛选", self)
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit(filter_card)
        self.search_input.setObjectName("recordSearchInput")
        self.search_input.setPlaceholderText("搜索企业名称、期间或记录编号")
        self.search_input.textChanged.connect(self.refresh_records)
        filter_row.addWidget(self.search_input, 1)
        self.status_filter = QComboBox(filter_card)
        self.status_filter.setObjectName("recordStatusFilter")
        self.status_filter.addItem("全部状态", "ALL")
        self.status_filter.addItem("已完成", RecordStatus.COMPLETED.value)
        self.status_filter.addItem("含提醒", RecordStatus.COMPLETED_WITH_WARNINGS.value)
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

        detail_card, detail_layout = _card("核算记录详情（只读）", content)
        self.detail_tabs = QTabWidget(detail_card)
        self.summary_text = self._readonly_text("recordSummaryView", self.detail_tabs)
        self.report_text = self._readonly_text("recordReportView", self.detail_tabs)
        self.activity_text = self._readonly_text("recordActivityEvidenceView", self.detail_tabs)
        self.parameter_text = self._readonly_text("recordParameterView", self.detail_tabs)
        self.quality_text = self._readonly_text("recordQualityView", self.detail_tabs)
        self.detail_tabs.addTab(self.summary_text, "基本信息与结果")
        self.detail_tabs.addTab(self.report_text, "标准报告数据")
        self.detail_tabs.addTab(self.activity_text, "活动数据与证据")
        self.detail_tabs.addTab(self.parameter_text, "参数与因子")
        self.detail_tabs.addTab(self.quality_text, "数据质量与提醒")
        detail_layout.addWidget(self.detail_tabs, 1)

        self.audit_dialog = QDialog(self)
        self.audit_dialog.setObjectName("recordAuditDialog")
        self.audit_dialog.setWindowTitle("核算记录审计详情（只读）")
        self.audit_dialog.resize(780, 560)
        audit_layout = QVBoxLayout(self.audit_dialog)
        self.detail_text = self._readonly_text("recordDetailView", self.audit_dialog)
        audit_layout.addWidget(self.detail_text)
        self.audit_button = QPushButton("查看审计详情", detail_card)
        self.audit_button.setObjectName("openRecordAuditButton")
        self.audit_button.clicked.connect(self.audit_dialog.open)
        detail_layout.addWidget(self.audit_button)
        self.delete_button = QPushButton("删除记录", detail_card)
        self.delete_button.setObjectName("deleteRecordButton")
        self.delete_button.clicked.connect(self._delete_selected)
        detail_layout.addWidget(self.delete_button)
        self.export_word_button = QPushButton("导出 Word 核算报告", detail_card)
        self.export_word_button.setObjectName("exportWordReportButton")
        self.export_word_button.clicked.connect(self._export_selected_report)
        detail_layout.addWidget(self.export_word_button)
        content_layout.addWidget(detail_card, 2)
        self.body_layout.addWidget(content, 1)
        self.refresh_records()

    @staticmethod
    def _readonly_text(object_name: str, parent: QWidget) -> QTextEdit:
        text = QTextEdit(parent)
        text.setObjectName(object_name)
        text.setReadOnly(True)
        return text

    def _read_snapshot(self, method_name: str, record_id: str) -> tuple[object, bool]:
        getter = getattr(self.record_repository, method_name, None)
        if not callable(getter):
            return None, False
        try:
            return getter(record_id), False
        except Exception:
            return None, True

    def _workspace_association(self, record_id: str) -> str:
        if self.project_service is None:
            return "当前无工作区关联"
        try:
            for workspace in self.project_service.list_all():
                for unit in workspace.units:
                    if record_id in unit.record_ids:
                        return f"{workspace.name} / {unit.name}"
        except Exception:
            return "当前工作区关系暂不可用"
        return "当前无工作区关联"

    def refresh_records(self, *_args: object, select_record_id: str | None = None) -> None:
        selected_before = select_record_id or (
            self.record_list.currentItem().data(Qt.ItemDataRole.UserRole)
            if self.record_list.currentItem() is not None else None
        )
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
                or query in str(record.input_snapshot.period.start).casefold()
                or query in str(record.input_snapshot.period.end).casefold()
            )
        )
        self.record_list.clear()
        selected_row = -1
        for index, record in enumerate(self._records):
            self.record_list.addItem(build_record_list_label(record))
            self.record_list.item(index).setData(Qt.ItemDataRole.UserRole, record.record_id)
            if record.record_id == selected_before:
                selected_row = index
        self.delete_button.setEnabled(bool(self._records))
        self.export_word_button.setEnabled(bool(self._records))
        if self._records:
            self.record_list.setCurrentRow(selected_row if selected_row >= 0 else 0)
        else:
            self._clear_details("暂无符合条件的核算记录。")

    def open_record(self, record_id: str) -> bool:
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.status_filter.blockSignals(True)
        self.status_filter.setCurrentIndex(0)
        self.status_filter.blockSignals(False)
        self.refresh_records(select_record_id=record_id)
        return self.record_list.currentItem() is not None and self.record_list.currentItem().data(Qt.ItemDataRole.UserRole) == record_id

    def _clear_details(self, message: str) -> None:
        for widget in (self.summary_text, self.report_text, self.activity_text, self.parameter_text, self.quality_text, self.detail_text):
            widget.setPlainText(message)

    def _show_selected_record(self, row: int) -> None:
        if row < 0 or row >= len(self._records):
            self._clear_details("请选择一条核算记录。")
            return
        record = self._records[row]
        getters = {
            "raw": "get_raw_input_snapshot",
            "rules": "get_effective_rule_set",
            "trace": "get_trace_snapshot",
            "provenance": "get_provenance_snapshot",
            "reporting": "get_reporting_snapshot",
            "qualification": "get_report_qualification",
        }
        values: dict[str, object] = {}
        errors: dict[str, bool] = {}
        for key, method in getters.items():
            values[key], errors[key] = self._read_snapshot(method, record.record_id)
        schema_getter = getattr(self.record_repository, "get_snapshot_schema_version", None)
        try:
            schema_available = bool(schema_getter(record.record_id)) if callable(schema_getter) else False
        except Exception:
            schema_available = False
        states = {
            key: snapshot_state(values[key], schema_available, read_error=errors[key])
            for key in ("raw", "trace", "provenance", "reporting", "qualification")
        }
        if not schema_available and not errors["raw"]:
            states["raw"] = SnapshotState.LEGACY
        report_state = states["raw"]
        qualification_state = states["qualification"]
        trace = values["trace"] if states["trace"] is SnapshotState.PRESENT else None
        reporting = values["reporting"] if states["reporting"] is SnapshotState.PRESENT else None
        raw = values["raw"] if states["raw"] is SnapshotState.PRESENT else None
        self.summary_text.setPlainText(summary_with_trace(
            record, values["qualification"], qualification_state, trace,
            association=self._workspace_association(record.record_id),
        ))
        if states["raw"] is SnapshotState.LEGACY:
            report_text = "该历史记录生成时尚未保存完整业务输入；可查看以下已固化的核算汇总。\n\n" + build_report_view(record, None, trace, reporting)
        elif states["raw"] is SnapshotState.CORRUPT:
            report_text = "无法读取该历史记录的业务输入快照。\n\n" + build_report_view(record, None, trace, reporting)
        else:
            report_text = build_report_view(record, raw, trace, reporting)
        self.report_text.setPlainText(report_text)
        self.activity_text.setPlainText(build_activity_evidence_view(raw, reporting, states["reporting"]))
        parameter_state = (
            SnapshotState.PRESENT if record.parameter_snapshots else
            SnapshotState.EMPTY if schema_available else SnapshotState.LEGACY
        )
        self.parameter_text.setPlainText(build_parameter_view(
            record, evidence_names_for(reporting), parameter_state,
        ))
        self.quality_text.setPlainText(build_quality_view(
            record, values["qualification"], qualification_state,
        ))
        try:
            audit = self.record_repository.list_audit(record.record_id) if self.record_repository is not None else ()
        except Exception:
            audit = ("无法读取历史审计日志。",)
        rule_value = values["rules"]
        professional = build_professional_view(
            record,
            raw=values["raw"],
            rules=rule_value,
            trace=values["trace"],
            provenance=values["provenance"],
            reporting=values["reporting"],
            qualification=values["qualification"],
            states={
                "实际输入快照": states["raw"], "Trace 快照": states["trace"],
                "Provenance 快照": states["provenance"], "报告信息快照": states["reporting"],
                "年度报告资格快照": states["qualification"],
            },
            audit=audit,
        )
        if states["trace"] is SnapshotState.LEGACY:
            professional += "\n\n该记录生成时未保存完整计算过程快照。"
        professional += (
            f"\n\n标准编号（稳定 ID）：{record.standard_id}"
            f"\n标准版本：{record.standard_version or '未记录'}"
            f"\n实际输入快照（业务视图）：\n{_format_business_snapshot(values['raw'])}"
            f"\n报告信息与证据快照：\n{_format_reporting_snapshot(values['reporting'])}"
        )
        self.detail_text.setPlainText(professional)

    def _delete_selected(self) -> None:
        row = self.record_list.currentRow()
        if row < 0 or row >= len(self._records) or self.record_repository is None:
            return
        record = self._records[row]
        answer = QMessageBox.question(
            self,
            "确认删除核算记录",
            f"将删除 {record.input_snapshot.enterprise_name or '未填写企业'} 的 {record.input_snapshot.period.start} 至 {record.input_snapshot.period.end} 核算记录。审计信息会保留，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete = getattr(self.record_repository, "delete", None)
        if callable(delete):
            delete(record.record_id, actor="current_user", reason="用户二次确认删除")
        self.refresh_records()

    def _report_supplementary_dialog(self, record: AccountingRecord) -> dict[str, object] | None:
        reporting_getter = getattr(self.record_repository, "get_reporting_snapshot", None)
        reporting = reporting_getter(record.record_id) if callable(reporting_getter) else {}
        reporting = reporting if isinstance(reporting, dict) else {}
        history_getter = getattr(self.record_repository, "get_latest_report_export_supplementary", None)
        previous = history_getter(record.record_id) if callable(history_getter) else {}
        previous = previous if isinstance(previous, dict) else {}
        fields = (
            ("enterprise_name", "企业名称", reporting.get("enterprise_name", record.input_snapshot.enterprise_name or "")),
            ("social_credit_code", "统一社会信用代码", reporting.get("social_credit_code", "")),
            ("legal_representative", "法定代表人", reporting.get("legal_representative", "")),
            ("address", "地址", reporting.get("address", "")),
            ("contact_person", "联系人", reporting.get("contact_person", "")),
            ("preparer_name", "编制人", reporting.get("preparer_name", "")),
            ("phone", "联系电话", reporting.get("preparer_contact", "")),
            ("products_and_process", "主要产品及工艺", reporting.get("products_and_process", "")),
        )
        dialog = QDialog(self)
        dialog.setWindowTitle("报告补充信息")
        dialog.setMinimumWidth(520)
        form = QFormLayout(dialog)
        widgets: dict[str, QLineEdit] = {}
        for key, label, fallback in fields:
            edit = QLineEdit(dialog)
            edit.setText(str(fallback or previous.get(key, "") or ""))
            widgets[key] = edit
            form.addRow(label, edit)
        prepared_on = QDateEdit(dialog)
        prepared_on.setCalendarPopup(True)
        prepared_on.setDisplayFormat("yyyy-MM-dd")
        try:
            parsed_date = QDate.fromString(str(previous.get("prepared_on") or date.today().isoformat()), "yyyy-MM-dd")
            prepared_on.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
        except ValueError:
            prepared_on.setDate(QDate.currentDate())
        form.addRow("编制日期", prepared_on)
        note = QTextEdit(dialog)
        note.setMaximumHeight(90)
        note.setPlainText(str(reporting.get("other_report_information", "") or previous.get("supplementary_note", "") or ""))
        form.addRow("补充说明", note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        result: dict[str, object] = {key: edit.text().strip() for key, edit in widgets.items()}
        result["prepared_on"] = prepared_on.date().toString("yyyy-MM-dd")
        result["supplementary_note"] = note.toPlainText().strip()
        return result

    def _export_selected_report(self) -> None:
        row = self.record_list.currentRow()
        if row < 0 or row >= len(self._records) or self.record_repository is None:
            return
        record = self._records[row]
        supplementary = self._report_supplementary_dialog(record)
        if supplementary is None:
            return
        default_name = f"温室气体核算报告_{record.input_snapshot.period.start}_{record.input_snapshot.period.end}.docx"
        target, _ = QFileDialog.getSaveFileName(self, "保存 Word 核算报告", default_name, "Word 文档 (*.docx)")
        if not target:
            return
        path = Path(target)
        if path.suffix.lower() != ".docx":
            path = path.with_suffix(".docx")
        try:
            report = build_saved_record_report(self.record_repository, record, supplementary_info=supplementary)
            document_bytes = render_report_docx(report)
            path.write_bytes(document_bytes)
            history_writer = getattr(self.record_repository, "record_report_export", None)
            if callable(history_writer):
                history_writer(
                    record.record_id,
                    export_id=f"report-export.{uuid4().hex}",
                    format="DOCX",
                    template_version=report.schema_version,
                    document_filename=path.name,
                    document_sha256=hashlib.sha256(document_bytes).hexdigest(),
                    supplementary_info=supplementary,
                    actor="current_user",
                )
        except Exception as exc:
            QMessageBox.critical(self, "报告导出失败", f"无法生成 Word 核算报告：{exc}")
            return
        QMessageBox.information(self, "报告已导出", f"Word 核算报告已保存到：\n{path}")

class ExcelImportPage(BasePage):
    """R2 workbook template download and read-only per-unit calculation preview."""

    def __init__(self, parent: QWidget | None = None, catalog_service: CatalogQueryService | None = None) -> None:
        super().__init__(AppRoute.EXCEL_IMPORT, parent)
        self.catalog_service = catalog_service or CatalogQueryService.empty()
        self.add_header("Excel 导入预览", "下载标准 R2 模板并预览各核算单元。预览不会保存项目或生成正式核算记录。")
        card, layout = _card("模板与预览", self)
        button_row = QHBoxLayout()
        self.templateButton = QPushButton("下载 R2 模板", card)
        self.templateButton.setObjectName("templateButton")
        self.templateButton.clicked.connect(self._download_template)
        button_row.addWidget(self.templateButton)
        self.selectFileButton = QPushButton("选择并预览工作簿", card)
        self.selectFileButton.setObjectName("selectFileButton")
        self.selectFileButton.clicked.connect(self._choose_workbook)
        button_row.addWidget(self.selectFileButton)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        self.preview_text = QTextEdit(card)
        self.preview_text.setObjectName("excelImportPreview")
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(300)
        self.preview_text.setPlainText("尚未选择工作簿。")
        layout.addWidget(self.preview_text)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)

    def _download_template(self) -> None:
        from packages.excel.r2 import write_template

        target, _ = QFileDialog.getSaveFileName(self, "保存 Excel R2 模板", "GB_T_32151_34_2024_R2.xlsx", "Excel 工作簿 (*.xlsx)")
        if not target:
            return
        path = Path(target)
        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")
        try:
            write_template(path)
        except Exception as exc:
            QMessageBox.critical(self, "模板保存失败", f"无法生成 Excel R2 模板：{exc}")
            return
        QMessageBox.information(self, "模板已保存", f"Excel R2 模板已保存到：\n{path}")

    def _choose_workbook(self) -> None:
        target, _ = QFileDialog.getOpenFileName(self, "选择 Excel R2 工作簿", "", "Excel 工作簿 (*.xlsx)")
        if not target:
            return
        try:
            from packages.excel.r2 import ExcelWorkbookImporter

            resolver = None
            if self.catalog_service.has_data:
                from packages.application.carbon_accounting import create_g06_parameter_resolver

                resolver = create_g06_parameter_resolver(self.catalog_service.repository)
            preview = ExcelWorkbookImporter(resolver).import_preview(target)
        except Exception as exc:
            self.preview_text.setPlainText(f"无法预览该工作簿：{exc}")
            QMessageBox.warning(self, "工作簿无法预览", str(exc))
            return
        unit_type_names = {"WHOLE_SITE": "全厂", "PROCESS": "工序", "OTHER": "其他"}
        def friendly_message(message: str) -> str:
            import re

            return re.sub(r"(?:CAR|GEN)-(?:FLD|VAL|PAR|FML|SRC|RULE)-[A-Z0-9_.-]+", "对应数据项", message)

        lines = [f"模板版本：{preview.provenance.template_version}", f"独立核算单元：{len(preview.units)}", ""]
        for unit in preview.units:
            lines.append(f"{unit.name}（{unit_type_names.get(unit.unit_type.value, '核算单元')}）")
            if unit.result is not None:
                lines.append(f"  预览排放总量：{format_amount(unit.result.total_amount, unit.result.total_unit)}")
            else:
                lines.append("  当前输入不能形成预览结果；请按下方错误修正。")
            for message in unit.errors:
                lines.append(f"  需要修正：{friendly_message(message.message)}")
            for message in unit.warnings:
                lines.append(f"  提醒：{friendly_message(message.message)}")
        if preview.warnings:
            lines.append("\n工作簿提醒")
            lines.extend(f"- {friendly_message(message.message)}" for message in preview.warnings)
        lines.append("\n以上均为独立预览；不会写入工作区或正式核算记录。")
        self.preview_text.setPlainText("\n".join(lines))


def create_page(
    route: AppRoute,
    view_model: ShellViewModel,
    navigate: Navigate,
    parent: QWidget | None = None,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
    project_service=None,
    calculation_use_case: CarbonAccountingUseCase | None = None,
) -> QWidget:
    """Create exactly one page for a validated public route."""

    if route is AppRoute.HOME:
        return HomePage(view_model, navigate, parent, record_repository=record_repository)
    if route is AppRoute.EXCEL_IMPORT:
        return ExcelImportPage(parent, catalog_service=catalog_service)
    if route is AppRoute.STANDARDS:
        from .catalog_pages import StandardLibraryPage

        return StandardLibraryPage(catalog_service or CatalogQueryService.empty(), navigate, parent)
    if route is AppRoute.FACTORS:
        from .catalog_pages import ParameterFactorLibraryPage

        return ParameterFactorLibraryPage(
            catalog_service or CatalogQueryService.empty(), navigate, parent
        )
    if route is AppRoute.RECORDS:
        return RecordLibraryPage(record_repository, parent, project_service=project_service)
    if route is AppRoute.NEW_ACCOUNTING:
        from .carbon_material_page import CarbonMaterialAccountingPage

        return CarbonMaterialAccountingPage(
            catalog_service=catalog_service or CatalogQueryService.empty(),
            record_repository=record_repository,
            project_service=project_service,
            calculation_use_case=calculation_use_case,
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
