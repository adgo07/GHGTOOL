"""Business-neutral pages and safe empty/placeholder states."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QSignalBlocker, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
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
from packages.application.canonical_input_codec import encode_canonical_input
from packages.application.project_workspaces import (
    AccountingUnitWorkspace,
    ProjectRecordAssociationError,
    ProjectWorkspace,
    ProjectWorkspaceService,
)
from packages.core.models import AccountingPeriod, AccountingRecord, PeriodType, RecordStatus
from packages.core.repositories import RecordRepository
from packages.application.carbon_accounting import (
    CarbonAccountingPreviewUseCase,
    CarbonAccountingUseCase,
    RecordPersistenceError,
    create_g06_parameter_resolver,
    resolve_formal_record_repository,
)
from packages.standards.carbon_material import CarbonMaterialCalculator, FuelPath, STANDARD_ID, STANDARD_VERSION
from .report_export import export_saved_record_report, report_supplementary_dialog
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
from .icons import load_tinted_icon
from .view_models import AppRoute, ShellViewModel


Navigate = Callable[[AppRoute], None]
_LOGGER = logging.getLogger(__name__)


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
    """Task-first home with saved projects and immutable records as recent work."""

    record_requested = Signal(str)

    def __init__(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
        parent: QWidget | None = None,
        record_repository: RecordRepository | None = None,
        project_service: ProjectWorkspaceService | None = None,
        logo_path: Path | None = None,
        icon_directory: Path | None = None,
    ) -> None:
        super().__init__(AppRoute.HOME, parent)
        self.record_repository = record_repository
        self.project_service = project_service
        self._icon_directory = icon_directory
        self.entry_buttons: dict[AppRoute, QPushButton] = {}
        self.project_layout: QVBoxLayout
        self.recent_layout: QVBoxLayout

        self._build_home_header(view_model, navigate, logo_path, icon_directory)

        workspace = QWidget(self)
        workspace.setObjectName("primaryWorkspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(16)

        start_panel, start_layout = _card("常用入口", workspace)
        start_panel.setObjectName("startPanel")
        entry_grid_widget = QWidget(start_panel)
        entry_grid = QGridLayout(entry_grid_widget)
        entry_grid.setContentsMargins(0, 0, 0, 0)
        entry_grid.setHorizontalSpacing(12)
        entry_grid.setVerticalSpacing(12)
        entry_routes = [
            item
            for item in view_model.navigation
            if item.route not in {AppRoute.HOME, AppRoute.SETTINGS}
        ]
        for index, item in enumerate(entry_routes):
            button = QPushButton(item.label, entry_grid_widget)
            button.setObjectName("homeEntryButton")
            button.setProperty("route", item.route.value)
            button.setProperty("primary", item.route is AppRoute.NEW_ACCOUNTING)
            button.setAccessibleName(item.label)
            button.setCursor(
                Qt.CursorShape.ArrowCursor
                if item.reserved
                else Qt.CursorShape.PointingHandCursor
            )
            button.setEnabled(not item.reserved)
            if item.reserved:
                button.setToolTip(f"{item.label}当前暂未开放。")
            if icon_directory is not None:
                button.setIcon(
                    load_tinted_icon(
                        icon_directory / f"{item.icon_name}.svg",
                        "#FFFFFF" if item.route is AppRoute.NEW_ACCOUNTING else "#12618D",
                        size=20,
                    )
                )
            button.setIconSize(QSize(20, 20))
            button.setMinimumHeight(68)
            button.setStyleSheet(
                """
                QPushButton#homeEntryButton {
                    background: #FFFFFF; border: 1px solid #D8E3EC; border-radius: 8px;
                    color: #182F43; font-size: 15px; font-weight: 600;
                    padding: 0 18px; text-align: left;
                }
                QPushButton#homeEntryButton:hover {
                    background: #F5F8FB; border-color: #12618D;
                }
                QPushButton#homeEntryButton:focus {
                    border: 2px solid #12618D;
                }
                QPushButton#homeEntryButton[primary="true"] {
                    background: #12618D; border-color: #12618D; color: #FFFFFF;
                }
                QPushButton#homeEntryButton[primary="true"]:hover {
                    background: #0D5278; border-color: #0D5278;
                QPushButton#homeEntryButton[primary="true"]:focus {
                    border: 2px solid #9DD8F7;
                }
                }
                QPushButton#homeEntryButton:disabled {
                    background: #F2F4F7; border-color: #E4E7EC; color: #98A2B3;
                }
                """
            )
            button.clicked.connect(
                lambda _checked=False, route=item.route: navigate(route)
            )
            entry_grid.addWidget(button, index // 3, index % 3)
            self.entry_buttons[item.route] = button
        for column in range(3):
            entry_grid.setColumnStretch(column, 1)
        start_layout.addWidget(entry_grid_widget)
        workspace_layout.addWidget(start_panel)
        self.body_layout.addWidget(workspace)

        recent_work = QWidget(self)
        recent_work.setObjectName("recentWorkCard")
        recent_layout = QVBoxLayout(recent_work)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(12)
        recent_title = QLabel("最近工作", recent_work)
        recent_title.setObjectName("sectionTitle")
        recent_layout.addWidget(recent_title)

        recent_columns = QWidget(recent_work)
        recent_columns_layout = QHBoxLayout(recent_columns)
        recent_columns_layout.setContentsMargins(0, 0, 0, 0)
        recent_columns_layout.setSpacing(16)
        projects_card, self.project_layout = _card("已保存项目", recent_columns)
        projects_card.setObjectName("recentProjectsCard")
        records_card, self.recent_layout = _card("核算记录", recent_columns)
        records_card.setObjectName("recentRecordsCard")
        recent_columns_layout.addWidget(projects_card, 1)
        recent_columns_layout.addWidget(records_card, 1)
        recent_layout.addWidget(recent_columns)
        self.body_layout.addWidget(recent_work)

        status = QLabel(view_model.status_summary, self)
        status.setObjectName("statusSummary")
        status.setWordWrap(True)
        self.body_layout.addWidget(status)
        self.body_layout.addStretch(1)

    def _build_home_header(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
        logo_path: Path | None,
        icon_directory: Path | None,
    ) -> None:
        header = QWidget(self)
        header.setObjectName("homeHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        logo_label = QLabel(header)
        logo_label.setObjectName("homeLogo")
        logo_label.setAccessibleName("青舟")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_label.setFixedSize(176, 44)
        if logo_path is not None:
            logo = QPixmap(str(logo_path))
            if not logo.isNull():
                logo_label.setPixmap(
                    logo.scaled(
                        QSize(176, 44),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if logo_label.pixmap() is None or logo_label.pixmap().isNull():
            logo_label.setText("青舟")
        layout.addWidget(logo_label)

        title_group = QWidget(header)
        title_layout = QVBoxLayout(title_group)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        title = QLabel(view_model.home_title, title_group)
        title.setObjectName("pageTitle")
        title.setWordWrap(True)
        description = QLabel(view_model.home_description, title_group)
        description.setObjectName("pageDescription")
        description.setWordWrap(True)
        title_layout.addWidget(title)
        title_layout.addWidget(description)
        layout.addWidget(title_group, 1)

        settings_item = next(
            item for item in view_model.navigation if item.route is AppRoute.SETTINGS
        )
        settings_button = QPushButton(settings_item.label, header)
        settings_button.setObjectName("homeSettingsButton")
        settings_button.setProperty("route", settings_item.route.value)
        settings_button.setAccessibleName(settings_item.label)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.setMinimumHeight(40)
        if icon_directory is not None:
            settings_button.setIcon(
                load_tinted_icon(
                    icon_directory / f"{settings_item.icon_name}.svg",
                    "#526A7D",
                )
            )
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setStyleSheet(
            """
            QPushButton#homeSettingsButton {
                background: #FFFFFF; border: 1px solid #D8E3EC; border-radius: 6px;
                color: #182F43; padding: 0 14px; font-size: 14px;
            }
            QPushButton#homeSettingsButton:hover {
                background: #F5F8FB; border-color: #12618D;
            }
            QPushButton#homeSettingsButton:focus {
                border: 2px solid #12618D;
            }
            """
        )
        settings_button.clicked.connect(lambda _checked=False: navigate(AppRoute.SETTINGS))
        layout.addWidget(settings_button, 0, Qt.AlignmentFlag.AlignTop)
        self.body_layout.addWidget(header)

    def _clear_recent_items(self, layout: QVBoxLayout) -> None:
        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _show_recent_empty(
        self,
        layout: QVBoxLayout,
        title: str,
        description: str,
        object_name: str,
    ) -> None:
        self._clear_recent_items(layout)
        empty_title = QLabel(title)
        empty_title.setObjectName(f"{object_name}Title")
        empty_title.setWordWrap(True)
        layout.addWidget(empty_title)
        empty_description = QLabel(description)
        empty_description.setObjectName(f"{object_name}Description")
        empty_description.setWordWrap(True)
        layout.addWidget(empty_description)
        layout.addStretch(1)

    def _recent_item_row(
        self,
        label_text: str,
        action_text: str,
        row_name: str,
        button_name: str,
        action,
        parent: QWidget,
    ) -> QWidget:
        row = QWidget(parent)
        row.setObjectName(row_name)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        label = QLabel(label_text, row)
        label.setObjectName("bodyText")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row_layout.addWidget(label, 1)
        button = QPushButton(action_text, row)
        button.setObjectName(button_name)
        button.setAccessibleName(f"{action_text}：{label_text}")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(36)
        button.setStyleSheet(
            """
            QPushButton {
                background: #FFFFFF; border: 1px solid #D8E3EC; border-radius: 6px;
                color: #12618D; padding: 0 12px;
            }
            QPushButton:hover { background: #F5F8FB; border-color: #12618D; }
            QPushButton:focus { border: 2px solid #12618D; }
            """
        )
        button.clicked.connect(action)
        row_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def refresh_recent_records(self) -> None:
        """Refresh recent projects and records from their existing read services."""

        if self.project_service is None:
            self._show_recent_empty(
                self.project_layout,
                "项目暂不可用",
                "当前无法读取已保存项目。",
                "projectRecentState",
            )
        else:
            try:
                projects = self.project_service.list_all()
                reader = getattr(self.project_service, "list_updated_at_by_project_id", None)
                timestamps = reader() if callable(reader) else {}
                projects = sorted(
                    projects,
                    key=lambda project: (
                        timestamps[project.project_id].timestamp()
                        if project.project_id in timestamps
                        else 0
                    ),
                    reverse=True,
                )[:5]
            except Exception:
                _LOGGER.exception("Unable to read saved projects for the home page")
                projects = None
            if projects is None:
                self._show_recent_empty(
                    self.project_layout,
                    "项目暂不可用",
                    "本地项目数据当前无法读取。",
                    "projectRecentState",
                )
            elif not projects:
                self._show_recent_empty(
                    self.project_layout,
                    "暂无已保存项目",
                    "保存后的项目会显示在这里；请在“新建核算”的项目列表中打开。",
                    "projectRecentState",
                )
            else:
                self._clear_recent_items(self.project_layout)
                for project in projects:
                    label = QLabel(project.name, self.project_layout.parentWidget())
                    label.setObjectName("recentProjectLabel")
                    label.setWordWrap(True)
                    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    self.project_layout.addWidget(label)
                self.project_layout.addStretch(1)

        if self.record_repository is None:
            self._show_recent_empty(
                self.recent_layout,
                "记录暂不可用",
                "当前无法读取核算记录。",
                "recordRecentState",
            )
            return
        try:
            records = sorted(
                self.record_repository.list_all(),
                key=lambda record: record.created_at,
                reverse=True,
            )[:5]
        except Exception:
            _LOGGER.exception("Unable to read formal records for the home page")
            records = None
        if records is None:
            self._show_recent_empty(
                self.recent_layout,
                "记录暂不可用",
                "本地核算记录当前无法读取。",
                "recordRecentState",
            )
            return
        if not records:
            self._show_recent_empty(
                self.recent_layout,
                "暂无核算记录",
                "完成一次正式核算后，记录会显示在这里。",
                "recordRecentState",
            )
            return

        self._clear_recent_items(self.recent_layout)
        for record in records:
            label = build_home_record_label(record)
            row = self._recent_item_row(
                label,
                "查看记录",
                "recentRecordRow",
                "openRecentRecordButton",
                lambda _checked=False, record_id=record.record_id:
                    self.record_requested.emit(record_id),
                self.recent_layout.parentWidget(),
            )
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
        export_actions = QHBoxLayout()
        export_actions.addWidget(self.export_word_button)
        detail_layout.addLayout(export_actions)
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
        if self.record_repository is None:
            return None
        return report_supplementary_dialog(self, self.record_repository, record)

    def _export_selected_report(self) -> None:
        row = self.record_list.currentRow()
        if row < 0 or row >= len(self._records) or self.record_repository is None:
            return
        export_saved_record_report(
            self,
            self.record_repository,
            self._records[row],
            supplementary_dialog=self._report_supplementary_dialog,
        )

class ExcelImportPage(BasePage):
    """Appendix B import, saved canonical projects, formal calculation and record access."""

    record_created = Signal(str)
    record_requested = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        catalog_service: CatalogQueryService | None = None,
        calculation_use_case: CarbonAccountingUseCase | None = None,
        project_service: ProjectWorkspaceService | None = None,
        record_repository: RecordRepository | None = None,
    ) -> None:
        super().__init__(AppRoute.EXCEL_IMPORT, parent)
        self.calculation_use_case = calculation_use_case
        self.project_service = project_service
        self.record_repository = resolve_formal_record_repository(calculation_use_case, record_repository)
        self.catalog_service = catalog_service or CatalogQueryService.empty()
        self._last_preview = None
        self._last_workbook_path: Path | None = None
        self._workspace: ProjectWorkspace | None = None
        self._selected_unit_id: str | None = None
        self._fuel_path_overrides: dict[str, FuelPath] = {}
        self._fuel_override_combos: dict[str, QComboBox] = {}
        self._preview_context_key: tuple[object, ...] | None = None

        if calculation_use_case is not None:
            self.preview_use_case = CarbonAccountingPreviewUseCase(calculation_use_case.calculator)
        else:
            resolver = None
            try:
                resolver = create_g06_parameter_resolver(self.catalog_service.repository)
            except (AttributeError, KeyError, TypeError, ValueError):
                pass
            try:
                calculator = CarbonMaterialCalculator(
                    parameter_resolver=resolver,
                    standard_version=self.catalog_service.standard_version(STANDARD_ID) or STANDARD_VERSION,
                    standard_implementation_date=self.catalog_service.standard_implementation_date(STANDARD_ID),
                    reference_data_identity_provider=self.catalog_service.reference_data_identity,
                )
            except (AttributeError, TypeError, ValueError):
                calculator = CarbonMaterialCalculator(parameter_resolver=resolver)
            self.preview_use_case = CarbonAccountingPreviewUseCase(calculator)

        self.add_header(
            "表格导入",
            "填写核算期间并确认边界后，选择附录 B 工作簿预览；预览不写入项目或正式记录。保存项目后可明确启动正式核算。",
        )

        import_card, import_layout = _card("模板与预览", self)
        import_row = QHBoxLayout()
        self.templateButton = QPushButton("下载附录 B 模板", import_card)
        self.templateButton.setObjectName("templateButton")
        self.templateButton.clicked.connect(self._download_template)
        import_row.addWidget(self.templateButton)
        self.selectFileButton = QPushButton("选择并预览工作簿", import_card)
        self.selectFileButton.setObjectName("selectFileButton")
        self.selectFileButton.clicked.connect(self._choose_workbook)
        import_row.addWidget(self.selectFileButton)
        import_row.addStretch(1)
        import_layout.addLayout(import_row)

        import_layout.addWidget(QLabel("以下信息用于新工作簿导入；已保存项目使用项目中的核算信息。", import_card))
        context_row = QHBoxLayout()
        context_row.addWidget(QLabel("企业名称（可选）", import_card))
        self.import_enterprise_name = QLineEdit(import_card)
        self.import_enterprise_name.setObjectName("importEnterpriseName")
        self.import_enterprise_name.setPlaceholderText("可留空")
        context_row.addWidget(self.import_enterprise_name, 2)
        context_row.addWidget(QLabel("期间类型", import_card))
        self.import_period_type = QComboBox(import_card)
        self.import_period_type.setObjectName("importPeriodType")
        self.import_period_type.addItem("请选择", None)
        self.import_period_type.addItem("年度", PeriodType.ANNUAL.value)
        self.import_period_type.addItem("月度", PeriodType.MONTHLY.value)
        self.import_period_type.addItem("自定义期间", PeriodType.CUSTOM.value)
        context_row.addWidget(self.import_period_type)
        context_row.addWidget(QLabel("开始日期", import_card))
        self.import_period_start = QLineEdit(import_card)
        self.import_period_start.setObjectName("importPeriodStart")
        self.import_period_start.setPlaceholderText("YYYY-MM-DD")
        self.import_period_start.setMaximumWidth(120)
        context_row.addWidget(self.import_period_start)
        context_row.addWidget(QLabel("结束日期", import_card))
        self.import_period_end = QLineEdit(import_card)
        self.import_period_end.setObjectName("importPeriodEnd")
        self.import_period_end.setPlaceholderText("YYYY-MM-DD")
        self.import_period_end.setMaximumWidth(120)
        context_row.addWidget(self.import_period_end)
        import_layout.addLayout(context_row)

        context_row_two = QHBoxLayout()
        context_row_two.addWidget(QLabel("电力地区", import_card))
        self.import_region = QComboBox(import_card)
        self.import_region.setObjectName("importRegion")
        self.import_region.addItem("全国（使用全国路径）", None)
        context_row_two.addWidget(self.import_region)
        self.import_boundary_confirmed = QCheckBox("我已确认本次核算边界", import_card)
        self.import_boundary_confirmed.setObjectName("importBoundaryConfirmed")
        context_row_two.addWidget(self.import_boundary_confirmed)
        context_row_two.addStretch(1)
        import_layout.addLayout(context_row_two)

        self.fuel_override_panel = QFrame(import_card)
        self.fuel_override_panel.setObjectName("fuelPathOverridePanel")
        self.fuel_override_layout = QVBoxLayout(self.fuel_override_panel)
        self.fuel_override_layout.setContentsMargins(0, 0, 0, 0)
        self.fuel_override_panel.hide()
        import_layout.addWidget(self.fuel_override_panel)

        self.import_period_type.currentIndexChanged.connect(self._refresh_import_regions)
        self.import_period_type.currentIndexChanged.connect(self._import_context_changed)
        self.import_period_start.editingFinished.connect(self._refresh_import_regions)
        self.import_period_end.editingFinished.connect(self._refresh_import_regions)
        self.import_period_start.textChanged.connect(self._import_context_changed)
        self.import_period_end.textChanged.connect(self._import_context_changed)
        self.import_enterprise_name.textChanged.connect(self._import_context_changed)
        self.import_region.currentIndexChanged.connect(self._import_context_changed)
        self.import_boundary_confirmed.stateChanged.connect(self._import_context_changed)

        self.preview_text = QTextEdit(import_card)
        self.preview_text.setObjectName("excelImportPreview")
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(250)
        self.preview_text.setPlainText("尚未选择工作簿。")
        import_layout.addWidget(self.preview_text)
        self.body_layout.addWidget(import_card)

        project_card, project_layout = _card("已保存的 Excel 项目", self)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("项目名称", project_card))
        self.project_name = QLineEdit(project_card)
        self.project_name.setObjectName("excelProjectName")
        self.project_name.setPlaceholderText("可为导入项目填写名称")
        name_row.addWidget(self.project_name, 1)
        self.save_project_button = QPushButton("保存有效核算单元", project_card)
        self.save_project_button.setObjectName("saveExcelProjectButton")
        self.save_project_button.clicked.connect(self._save_preview_as_project)
        name_row.addWidget(self.save_project_button)
        project_layout.addLayout(name_row)

        saved_row = QHBoxLayout()
        self.saved_projects = QComboBox(project_card)
        self.saved_projects.setObjectName("savedExcelProjects")
        saved_row.addWidget(self.saved_projects, 1)
        self.open_project_button = QPushButton("打开项目", project_card)
        self.open_project_button.setObjectName("openExcelProjectButton")
        self.open_project_button.clicked.connect(self._open_selected_project)
        saved_row.addWidget(self.open_project_button)
        project_layout.addLayout(saved_row)

        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("核算单元", project_card))
        self.unit_selector = QComboBox(project_card)
        self.unit_selector.setObjectName("canonicalUnitSelector")
        self.unit_selector.currentIndexChanged.connect(self._selected_unit_changed)
        unit_row.addWidget(self.unit_selector, 1)
        self.calculate_button = QPushButton("正式计算排放量", project_card)
        self.calculate_button.setObjectName("formalCalculateButton")
        self.calculate_button.clicked.connect(self._calculate_selected_unit)
        unit_row.addWidget(self.calculate_button)
        project_layout.addLayout(unit_row)

        record_row = QHBoxLayout()
        record_row.addWidget(QLabel("本单元正式记录", project_card))
        self.unit_record_selector = QComboBox(project_card)
        self.unit_record_selector.setObjectName("unitRecordSelector")
        record_row.addWidget(self.unit_record_selector, 1)
        self.open_record_button = QPushButton("查看核算记录", project_card)
        self.open_record_button.setObjectName("openUnitRecordButton")
        self.open_record_button.clicked.connect(self._open_selected_record)
        record_row.addWidget(self.open_record_button)
        project_layout.addLayout(record_row)

        self.status_label = QLabel(project_card)
        self.status_label.setObjectName("excelWorkflowStatus")
        self.status_label.setWordWrap(True)
        project_layout.addWidget(self.status_label)
        self.body_layout.addWidget(project_card)
        self.body_layout.addStretch(1)

        self._refresh_saved_projects()
        self._update_controls()
        if self.calculation_use_case is None:
            self.status_label.setText("正式核算尚未配置；当前可以预览工作簿并保存项目。")
        elif self.project_service is None:
            self.status_label.setText("项目存储尚未配置；正式计算按钮保持禁用。")
        elif self._workspace is None and self.saved_projects.count() == 0:
            self.status_label.setText("暂无已保存的 Excel 项目；保存项目后可在此处重新打开。")

    def _download_template(self) -> None:
        from packages.excel.templates import ExcelTemplateService

        service = ExcelTemplateService.default()
        template = service.get(STANDARD_ID)
        target, _ = QFileDialog.getSaveFileName(
            self,
            "保存 GB/T 32151.34—2024 附录 B 模板",
            "GB_T_32151_34_2024_Appendix_B.xlsx",
            "Excel 工作簿 (*.xlsx)",
        )
        if not target:
            return
        path = Path(target)
        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")
        try:
            service.copy_to(path, standard_id=STANDARD_ID)
        except Exception:
            _LOGGER.exception("Unable to copy approved Appendix B template to %s", path)
            QMessageBox.critical(
                self,
                "模板未保存",
                f"无法保存附录 B 模板。\n目标位置：\n{path}\n请检查文件夹和权限后重试。",
            )
            return
        QMessageBox.information(
            self,
            "模板已保存",
            f"{template.standard_version} 附录 B 模板已保存到：\n{path}",
        )

    def _choose_workbook(self) -> None:
        target, _ = QFileDialog.getOpenFileName(self, "选择附录 B 工作簿", "", "Excel 工作簿 (*.xlsx)")
        if target:
            self._preview_workbook(Path(target))

    def _period_for_import(self) -> AccountingPeriod:
        period_value = self.import_period_type.currentData()
        try:
            period_type = PeriodType(period_value)
        except (TypeError, ValueError) as exc:
            raise ValueError("请选择核算期间类型。") from exc
        try:
            start = date.fromisoformat(self.import_period_start.text().strip())
            end = date.fromisoformat(self.import_period_end.text().strip())
        except ValueError as exc:
            raise ValueError("请按 YYYY-MM-DD 填写开始日期和结束日期。") from exc
        try:
            return AccountingPeriod(period_type=period_type, start=start, end=end)
        except ValueError as exc:
            period_labels = {
                PeriodType.ANNUAL: "年度期间应覆盖同一自然年的 1 月 1 日至 12 月 31 日。",
                PeriodType.MONTHLY: "月度期间应覆盖同一自然月的首日至末日。",
                PeriodType.CUSTOM: "自定义期间的结束日期不能早于开始日期。",
            }
            raise ValueError(period_labels.get(period_type, "核算期间无效。")) from exc

    def _refresh_import_regions(self, *_args) -> None:
        selected = self.import_region.currentData()
        regions: tuple[str, ...] = ()
        try:
            period = self._period_for_import()
            resolver = self.preview_use_case.calculator.parameter_resolver
            if resolver is not None:
                from packages.application.uat03_parameter_queries import UAT03ParameterQueries

                regions = UAT03ParameterQueries(self.catalog_service, resolver).electricity_regions(period)
        except (AttributeError, TypeError, ValueError):
            regions = ()
        blocker = QSignalBlocker(self.import_region)
        self.import_region.clear()
        self.import_region.addItem("全国（使用全国路径）", None)
        for region in regions:
            self.import_region.addItem(region, region)
        selected_index = self.import_region.findData(selected)
        self.import_region.setCurrentIndex(max(0, selected_index))
        del blocker

    def _build_import_context(self):
        from packages.excel.appendix_b import AppendixBImportContext

        enterprise_name = self.import_enterprise_name.text().strip() or None
        return AppendixBImportContext(
            period=self._period_for_import(),
            enterprise_name=enterprise_name,
            region=self.import_region.currentData(),
            boundary_confirmed=self.import_boundary_confirmed.isChecked(),
            fuel_path_overrides=dict(self._fuel_path_overrides),
        )

    def _clear_fuel_override_panel(self) -> None:
        self._fuel_override_combos.clear()
        self.repreview_with_fuel_paths_button = None
        while self.fuel_override_layout.count():
            item = self.fuel_override_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            nested = item.layout()
            if nested is not None:
                while nested.count():
                    child_item = nested.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()
                nested.deleteLater()
        self.fuel_override_panel.hide()

    def _show_fuel_path_choices(self, preview) -> None:
        self._clear_fuel_override_panel()
        if not preview.units:
            return
        errors = [
            item
            for item in preview.units[0].errors
            if item.code == "EXB01_FUEL_PATH_REQUIRED"
        ]
        if not errors:
            return
        heading = QLabel(
            "有燃料的计量路径需要说明。请选择体积或质量计量，再重新预览。",
            self.fuel_override_panel,
        )
        heading.setWordWrap(True)
        self.fuel_override_layout.addWidget(heading)
        path_labels = {
            FuelPath.VOLUME: "体积计量",
            FuelPath.MASS: "质量计量",
        }
        for error in errors:
            row = QHBoxLayout()
            label = QLabel(error.field_label or "燃料计量路径", self.fuel_override_panel)
            label.setWordWrap(True)
            row.addWidget(label, 1)
            selector = QComboBox(self.fuel_override_panel)
            selector.setObjectName(f"fuelPathOverride_{error.location.replace('!', '_').replace('.', '_')}")
            selector.addItem("请选择", None)
            for fuel_path, display in path_labels.items():
                selector.addItem(display, fuel_path.value)
            selected = self._fuel_path_overrides.get(error.location)
            selector.setCurrentIndex(max(0, selector.findData(selected)))
            selector.currentIndexChanged.connect(self._update_fuel_override_button)
            self._fuel_override_combos[error.location] = selector
            row.addWidget(selector)
            self.fuel_override_layout.addLayout(row)
        self.repreview_with_fuel_paths_button = QPushButton(
            "按所选路径重新预览",
            self.fuel_override_panel,
        )
        self.repreview_with_fuel_paths_button.setObjectName("retryFuelPathPreviewButton")
        self.repreview_with_fuel_paths_button.clicked.connect(self._repreview_with_fuel_paths)
        self.fuel_override_layout.addWidget(self.repreview_with_fuel_paths_button)
        self.fuel_override_panel.show()
        self._update_fuel_override_button()

    @staticmethod
    def _fuel_path_from_widget(value) -> FuelPath | None:
        try:
            return value if isinstance(value, FuelPath) else FuelPath(value)
        except (TypeError, ValueError):
            return None

    def _update_fuel_override_button(self, *_args) -> None:
        button = getattr(self, "repreview_with_fuel_paths_button", None)
        if button is not None:
            button.setEnabled(
                bool(self._fuel_override_combos)
                and all(
                    self._fuel_path_from_widget(combo.currentData()) is not None
                    for combo in self._fuel_override_combos.values()
                )
            )

    def _repreview_with_fuel_paths(self) -> None:
        if self._last_workbook_path is None:
            return
        self._fuel_path_overrides = {
            location: fuel_path
            for location, combo in self._fuel_override_combos.items()
            if (fuel_path := self._fuel_path_from_widget(combo.currentData())) is not None
        }
        self._preview_workbook(self._last_workbook_path, preserve_overrides=True)

    def _import_context_key(self) -> tuple[object, ...] | None:
        try:
            period = self._period_for_import()
        except ValueError:
            return None
        overrides = tuple(
            sorted((location, path.value) for location, path in self._fuel_path_overrides.items())
        )
        return (
            period.period_type.value,
            period.start.isoformat(),
            period.end.isoformat(),
            self.import_enterprise_name.text().strip() or None,
            self.import_region.currentData(),
            self.import_boundary_confirmed.isChecked(),
            overrides,
        )

    def _import_context_changed(self, *_args) -> None:
        if self._last_preview is None or self._preview_context_key is None:
            return
        if self._import_context_key() == self._preview_context_key:
            return
        self._last_preview = None
        self._preview_context_key = None
        self.preview_text.setPlainText(
            "核算期间、企业、地区或边界信息已修改，请重新预览工作簿。"
        )
        self.status_label.setText("导入信息已修改；请重新预览后再保存项目。")
        self._update_controls()

    def _detach_active_project_for_import(self) -> None:
        self._workspace = None
        self._selected_unit_id = None
        self._last_preview = None
        self._last_workbook_path = None
        self._preview_context_key = None
        self.project_name.setReadOnly(False)
        blocker = QSignalBlocker(self.unit_selector)
        self.unit_selector.clear()
        del blocker
        self.unit_record_selector.clear()
        self._clear_fuel_override_panel()
        self._update_controls()

    def _preview_workbook(self, path: Path, *, preserve_overrides: bool = False) -> None:
        same_source = path == self._last_workbook_path
        if not preserve_overrides or not same_source:
            self._fuel_path_overrides.clear()
            self._clear_fuel_override_panel()
        self._detach_active_project_for_import()
        self.project_name.setText(path.stem)
        try:
            from packages.excel.appendix_b import AppendixBWorkbookImporter

            context = self._build_import_context()
            preview = AppendixBWorkbookImporter(
                preview_use_case=self.preview_use_case,
                catalog_service=self.catalog_service,
            ).import_preview(path, context=context)
            preview_context_key = self._import_context_key()
        except Exception as exc:
            self._last_preview = None
            self._preview_context_key = None
            self._last_workbook_path = None
            self.preview_text.setPlainText(f"无法预览该工作簿：{exc}")
            self.status_label.setText(f"工作簿无法预览：{exc}")
            QMessageBox.warning(self, "工作簿无法预览", str(exc))
            self._update_controls()
            return

        self._last_preview = preview
        self._last_workbook_path = path
        self._preview_context_key = preview_context_key
        self._show_fuel_path_choices(preview)
        self._workspace = None
        self._selected_unit_id = None
        self.project_name.setReadOnly(False)
        self.project_name.setText(path.stem)
        blocker = QSignalBlocker(self.unit_selector)
        self.unit_selector.clear()
        del blocker
        self.unit_record_selector.clear()
        self._render_import_preview(preview)
        valid_count = sum(1 for unit in preview.units if unit.can_calculate)
        invalid_count = len(preview.units) - valid_count
        self.status_label.setText(
            f"预览完成：{valid_count} 个有效单元可保存，{invalid_count} 个无效单元将保持未保存。"
            if valid_count
            else "预览完成：没有有效核算单元可保存；请修正工作簿后重新预览。"
        )
        self._update_controls()

    @staticmethod
    def _friendly_import_message(message: str) -> str:
        import re

        return re.sub(r"(?:CAR|GEN)-(?:FLD|VAL|PAR|FML|SRC|RULE)-[A-Z0-9_.-]+", "对应数据项", message)

    @classmethod
    def _format_import_message(cls, message) -> str:
        display = cls._friendly_import_message(message.message)
        location = getattr(message, "location", None)
        if location and location not in message.message:
            return f"{location}：{display}"
        return display

    def _render_import_preview(self, preview) -> None:
        unit_type_names = {"WHOLE_SITE": "全厂", "PROCESS": "工序", "OTHER": "其他"}
        lines = [
            f"模板版本：{preview.provenance.template_version}",
            f"独立核算单元：{len(preview.units)}",
            "",
        ]
        for unit in preview.units:
            lines.append(f"{unit.name}（{unit_type_names.get(unit.unit_type.value, '核算单元')}）")
            if unit.can_calculate and unit.result is not None:
                lines.append(f"  预览排放总量：{format_amount(unit.result.total_amount, unit.result.total_unit)}")
                lines.append("  状态：有效，可保存为项目")
            else:
                lines.append("  状态：无效，未保存")
            for message in unit.errors:
                lines.append(f"  需要修正：{self._format_import_message(message)}")
            for message in unit.warnings:
                lines.append(f"  提醒：{self._format_import_message(message)}")
        unit_warnings = tuple(message for unit in preview.units for message in unit.warnings)
        workbook_warnings = tuple(message for message in preview.warnings if message not in unit_warnings)
        if workbook_warnings:
            lines.append("\n工作簿提醒")
            lines.extend(f"- {self._format_import_message(message)}" for message in workbook_warnings)
        lines.append("\n预览本身不写入项目或正式记录；请使用上方按钮保存有效单元。")
        self.preview_text.setPlainText("\n".join(lines))

    @staticmethod
    def _plain_json_value(value):
        if isinstance(value, Enum):
            return ExcelImportPage._plain_json_value(value.value)
        if value is None or isinstance(value, (bool, int, str)):
            return value
        if isinstance(value, float):
            return str(value)
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if is_dataclass(value):
            result = {"type": type(value).__name__}
            result.update({field.name: ExcelImportPage._plain_json_value(getattr(value, field.name)) for field in fields(value)})
            return result
        if isinstance(value, Mapping):
            return {str(key): ExcelImportPage._plain_json_value(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [ExcelImportPage._plain_json_value(item) for item in value]
        return str(value)

    @staticmethod
    def _collect_source_evidence(value, path: str = "input") -> list[dict[str, object]]:
        evidence_fields = {
            "source_reference", "source_type", "source_kind", "source_ids", "evidence_ref_ids",
            "source_location", "monitoring_location", "applies_to", "source_level", "source_version",
            "source_id", "factor_id", "reason", "note",
        }
        found: list[dict[str, object]] = []
        if is_dataclass(value):
            value_fields = fields(value)
            names = {item.name for item in value_fields}
            if names & evidence_fields:
                found.append({
                    "path": path,
                    "type": type(value).__name__,
                    "values": ExcelImportPage._plain_json_value(value),
                })
            for item in value_fields:
                found.extend(ExcelImportPage._collect_source_evidence(getattr(value, item.name), f"{path}.{item.name}"))
        elif isinstance(value, Mapping):
            for key, item in value.items():
                found.extend(ExcelImportPage._collect_source_evidence(item, f"{path}.{key}"))
        elif isinstance(value, (tuple, list)):
            for index, item in enumerate(value):
                found.extend(ExcelImportPage._collect_source_evidence(item, f"{path}[{index}]"))
        return found

    def _numeric_cell_evidence_for_unit(self, preview, unit) -> list[dict[str, object]]:
        return [
            {
                "sheet": item.sheet,
                "cell": item.cell,
                "raw_cell_type": item.raw_cell_type,
                "workbook_value_repr": item.workbook_value_repr,
                "raw_numeric_lexical": item.serialized_numeric_text,
                "normalized_decimal_lexical": str(item.normalized_decimal),
                "accounting_unit_id": item.accounting_unit_id,
            }
            for item in preview.numeric_evidence
            if item.accounting_unit_id in (None, unit.unit_id)
        ]

    def _build_ingress_provenance(self, preview, unit) -> dict[str, object]:
        source_path = self._last_workbook_path
        return {
            "source": "EXCEL_APPENDIX_B",
            "workbook": {
                "sha256": preview.provenance.workbook_sha256,
                "file_name": source_path.name if source_path is not None else None,
                "template_id": preview.provenance.template_id,
                "template_version": preview.provenance.template_version,
                "standard_id": preview.provenance.standard_id,
                "standard_version": preview.provenance.standard_version,
                "ingress_policy_id": preview.provenance.ingress_policy_id,
                "imported_at": preview.provenance.imported_at.isoformat(),
                **(
                    {"canonical_path": preview.provenance.canonical_path}
                    if getattr(preview.provenance, "canonical_path", None) is not None
                    else {}
                ),
            },
            "accounting_unit": {
                "importer_unit_id": unit.unit_id,
                "name": unit.name,
                "unit_type": unit.unit_type.value,
            },
            "numeric_cell_evidence": self._numeric_cell_evidence_for_unit(preview, unit),
            "canonical_source_evidence": self._collect_source_evidence(unit.input_value),
            "unit_warnings": [self._plain_json_value(message) for message in unit.warnings],
            "workbook_warnings": [self._plain_json_value(message) for message in preview.warnings],
        }

    def _save_preview_as_project(self) -> None:
        if self.project_service is None:
            self.status_label.setText("项目存储尚未配置，无法保存项目。")
            return
        preview = self._last_preview
        if preview is None:
            self.status_label.setText("请先选择并预览工作簿。")
            return
        if self._preview_context_key is None or self._import_context_key() != self._preview_context_key:
            self._import_context_changed()
            self.status_label.setText("导入信息已修改；请重新预览后再保存项目。")
            return
        valid_units = [unit for unit in preview.units if unit.can_calculate and unit.input_value is not None]
        if not valid_units:
            self.status_label.setText("没有有效核算单元；项目未保存，也未生成正式记录。")
            return
        name = self.project_name.text().strip()
        if not name:
            name = self._last_workbook_path.stem if self._last_workbook_path is not None else "Excel 导入项目"
        units = tuple(
            AccountingUnitWorkspace(
                unit_id=f"unit.{uuid4().hex}",
                name=unit.name,
                unit_type=unit.unit_type,
                position=index,
                form_state={},
                canonical_input=unit.input_value,
                ingress_provenance=self._build_ingress_provenance(preview, unit),
                input_fingerprint=hashlib.sha256(
                    encode_canonical_input(unit.input_value).encode("utf-8")
                ).hexdigest(),
            )
            for index, unit in enumerate(valid_units)
        )
        workspace = ProjectWorkspace(
            project_id=f"project.{uuid4().hex}",
            name=name,
            active_unit_id=units[0].unit_id,
            units=units,
        )
        try:
            self.project_service.save(workspace)
        except Exception as exc:
            self.status_label.setText(f"项目保存失败；未生成正式记录：{exc}")
            QMessageBox.warning(self, "项目保存失败", str(exc))
            return
        self._last_preview = None
        self._preview_context_key = None
        self._workspace = workspace
        self._refresh_saved_projects(workspace.project_id)
        self.open_project(workspace.project_id)
        invalid_count = len(preview.units) - len(valid_units)
        self.status_label.setText(
            f"项目“{name}”已保存，包含 {len(valid_units)} 个有效单元；"
            f"{invalid_count} 个无效单元未保存。尚未生成正式核算记录。"
        )

    def _refresh_saved_projects(self, selected_project_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.saved_projects)
        previous = selected_project_id or self.saved_projects.currentData()
        self.saved_projects.clear()
        workspaces = ()
        if self.project_service is not None:
            try:
                workspaces = self.project_service.list_all()
            except Exception as exc:
                self.status_label.setText(f"无法读取已保存项目：{exc}")
        for workspace in workspaces:
            if any(unit.canonical_input is not None for unit in workspace.units):
                self.saved_projects.addItem(workspace.name, workspace.project_id)
        index = self.saved_projects.findData(previous)
        if index >= 0:
            self.saved_projects.setCurrentIndex(index)
        del blocker
        self.open_project_button.setEnabled(self.project_service is not None and self.saved_projects.count() > 0)

    def _open_selected_project(self) -> None:
        project_id = self.saved_projects.currentData()
        if project_id:
            self.open_project(str(project_id))

    def open_project(self, project_id: str) -> bool:
        if self.project_service is None:
            self.status_label.setText("项目存储尚未配置，无法打开项目。")
            return False
        try:
            workspace = self.project_service.get(project_id)
        except Exception as exc:
            self.status_label.setText(f"打开项目失败：{exc}")
            QMessageBox.warning(self, "项目打开失败", str(exc))
            return False
        if workspace is None:
            self.status_label.setText("未找到所选项目；请刷新项目列表后重试。")
            return False
        canonical_units = [unit for unit in workspace.units if unit.canonical_input is not None]
        if not canonical_units:
            self.status_label.setText("所选项目没有可打开的 Excel 核算单元。")
            return False

        self._workspace = workspace
        self._last_preview = None
        self._last_workbook_path = None
        self._preview_context_key = None
        self._clear_fuel_override_panel()
        self.project_name.setText(workspace.name)
        self.project_name.setReadOnly(True)
        self._selected_unit_id = workspace.active_unit_id if any(unit.unit_id == workspace.active_unit_id for unit in canonical_units) else canonical_units[0].unit_id
        blocker = QSignalBlocker(self.unit_selector)
        self.unit_selector.clear()
        for index, unit in enumerate(canonical_units, 1):
            self.unit_selector.addItem(f"{unit.name}（核算单元 {index}）", unit.unit_id)
        selected_index = self.unit_selector.findData(self._selected_unit_id)
        if selected_index >= 0:
            self.unit_selector.setCurrentIndex(selected_index)
        del blocker
        self._update_controls()
        self._selected_unit_changed()
        self.status_label.setText(f"已打开项目“{workspace.name}”；原工作簿不是重新打开所必需的。")
        return True

    def _selected_unit(self):
        if self._workspace is None:
            return None
        unit_id = self.unit_selector.currentData()
        if not unit_id:
            return None
        return next((unit for unit in self._workspace.units if unit.unit_id == unit_id), None)

    def _selected_unit_changed(self, *_args) -> None:
        unit = self._selected_unit()
        blocker = QSignalBlocker(self.unit_record_selector)
        self.unit_record_selector.clear()
        if unit is not None:
            for index, record_id in enumerate(unit.record_ids, 1):
                self.unit_record_selector.addItem(f"第 {index} 次正式核算", record_id)
        del blocker
        self._update_controls()
        if unit is None or unit.canonical_input is None:
            return
        try:
            outcome = self.preview_use_case.calculate(unit.canonical_input)
        except Exception as exc:
            self.preview_text.setPlainText(f"已保存项目中的单元无法预览：{exc}")
            return
        lines = [
            f"已保存项目：{self._workspace.name}",
            f"核算单元：{unit.name}",
            f"企业：{unit.canonical_input.enterprise_name or '未填写'}",
            "核算期间：" + {"ANNUAL": "年度", "MONTHLY": "月度", "CUSTOM": "自定义期间"}.get(
                unit.canonical_input.period.period_type.value, "核算期间"
            ) + f" · {unit.canonical_input.period.start.isoformat()} 至 {unit.canonical_input.period.end.isoformat()}",
            "当前展示为同一计算器生成的预览值；预览不生成正式核算记录。",
        ]
        if outcome.successful and outcome.result is not None:
            lines.append(f"预览排放总量：{format_amount(outcome.result.total_amount, outcome.result.total_unit)}")
        else:
            lines.append("当前输入未通过核算校验；本次预览没有生成正式记录。")
        for problem in outcome.problems:
            lines.append(f"- {self._friendly_import_message(problem.message)}")
        provenance = unit.ingress_provenance or {}
        workbook = provenance.get("workbook")
        if isinstance(workbook, dict):
            lines.append(f"导入工作簿：{workbook.get('file_name') or '来源名称未记录'}")
            lines.append(f"已保留数值来源单元格：{len(provenance.get('numeric_cell_evidence', []))}")
        self.preview_text.setPlainText("\n".join(lines))

    def _update_controls(self) -> None:
        for control in (
            self.import_enterprise_name, self.import_period_type,
            self.import_period_start, self.import_period_end,
            self.import_region, self.import_boundary_confirmed,
        ):
            control.setEnabled(self._workspace is None)
        valid_import = self._last_preview is not None and any(unit.can_calculate for unit in self._last_preview.units)
        self.save_project_button.setEnabled(self.project_service is not None and valid_import)
        unit = self._selected_unit()
        can_calculate = (
            self.calculation_use_case is not None
            and self.project_service is not None
            and unit is not None
            and unit.canonical_input is not None
        )
        self.calculate_button.setEnabled(can_calculate)
        self.open_record_button.setEnabled(self.record_repository is not None and self.unit_record_selector.count() > 0)
        self.open_project_button.setEnabled(self.project_service is not None and self.saved_projects.count() > 0)

    def _calculate_selected_unit(self) -> None:
        unit = self._selected_unit()
        if self.calculation_use_case is None or self.project_service is None or self._workspace is None or unit is None or unit.canonical_input is None:
            self.status_label.setText("正式核算未配置或尚未打开已保存的核算单元。")
            self._update_controls()
            return
        try:
            outcome = self.calculation_use_case.calculate(
                unit.canonical_input,
                ingress_provenance=unit.ingress_provenance,
            )
        except RecordPersistenceError:
            _LOGGER.exception("Unable to persist formal record for the selected Excel unit")
            self.status_label.setText("正式记录保存失败；本次未标记为完成。请检查核算记录页面后重试；如仍失败，请保存诊断信息以便排查。")
            QMessageBox.warning(self, "正式记录保存失败", self.status_label.text())
            return
        except Exception:
            _LOGGER.exception("Formal calculation failed for the selected Excel unit")
            self.status_label.setText("正式核算未能完成；请检查核算记录页面后再决定是否重试。")
            QMessageBox.warning(self, "正式核算未完成", self.status_label.text())
            return
        if not outcome.successful:
            messages = "；".join(self._friendly_import_message(problem.message) for problem in outcome.problems)
            self.status_label.setText(f"本次核算未通过校验，未生成正式记录。{messages}")
            return
        record = outcome.record
        if record is None:
            self.status_label.setText("计算结果未附带已保存的正式记录；请检查正式核算配置。")
            return

        self.record_created.emit(record.record_id)
        result = outcome.result
        encoded_input = encode_canonical_input(unit.canonical_input)
        result_snapshot = {
            "record_id": record.record_id,
            "total_amount": str(result.total_amount) if result is not None else str(record.calculation_result.total_amount),
            "total_unit": result.total_unit if result is not None else record.calculation_result.total_unit,
            "status": record.status.value,
            "calculated_at": record.created_at.isoformat(),
        }
        updated_unit = replace(
            unit,
            result_snapshot=result_snapshot,
            record_ids=unit.record_ids + (record.record_id,),
            input_fingerprint=hashlib.sha256(encoded_input.encode("utf-8")).hexdigest(),
        )
        updated_workspace = replace(
            self._workspace,
            active_unit_id=unit.unit_id,
            units=tuple(updated_unit if candidate.unit_id == unit.unit_id else candidate for candidate in self._workspace.units),
        )
        self._workspace = updated_workspace
        try:
            self.project_service.save_after_record(updated_workspace, record.record_id)
        except ProjectRecordAssociationError as exc:
            _LOGGER.exception("Project association state for saved record %s", record.record_id)
            if exc.association_saved:
                message = "正式记录已保存，项目关联也已保存，但恢复标记未能清理；可在核算记录页面查看该记录。"
            elif exc.recovery_pending:
                message = "正式记录已保存，但项目关联失败；恢复信息已保留，项目关联待恢复。可在核算记录页面查看该记录。"
            else:
                message = "正式记录已保存，但项目关联和恢复信息均未保存。请在核算记录页面查看该记录，并保存诊断信息以便排查项目关联。"
            self.status_label.setText(message)
            QMessageBox.warning(self, "正式记录已保存，项目关联待处理", message)
            self._selected_unit_changed()
            return
        except Exception:
            _LOGGER.exception("Project association state is unknown for saved record %s", record.record_id)
            message = "正式记录已保存，但项目关联状态无法确认。请先在核算记录页面检查该记录，并保存诊断信息以便排查。"
            self.status_label.setText(message)
            QMessageBox.warning(self, "项目关联状态无法确认", message)
            self._selected_unit_changed()
            return

        self.status_label.setText("正式核算已完成并新增一条不可编辑记录；项目已保存该记录关联。")
        self._selected_unit_changed()

    def _open_selected_record(self) -> None:
        record_id = self.unit_record_selector.currentData()
        if not record_id:
            self.status_label.setText("所选核算单元尚无正式记录。")
            return
        if self.record_repository is None:
            self.status_label.setText("记录存储尚未配置，无法打开正式记录。")
            return
        self.record_requested.emit(str(record_id))

def create_page(
    route: AppRoute,
    view_model: ShellViewModel,
    navigate: Navigate,
    parent: QWidget | None = None,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
    project_service=None,
    calculation_use_case: CarbonAccountingUseCase | None = None,
    logo_path: Path | None = None,
    icon_directory: Path | None = None,
) -> QWidget:
    """Create exactly one page for a validated public route."""

    if route is AppRoute.HOME:
        return HomePage(
            view_model,
            navigate,
            parent,
            record_repository=record_repository,
            project_service=project_service,
            logo_path=logo_path,
            icon_directory=icon_directory,
        )
    if route is AppRoute.EXCEL_IMPORT:
        return ExcelImportPage(
            parent,
            catalog_service=catalog_service,
            calculation_use_case=calculation_use_case,
            project_service=project_service,
            record_repository=record_repository,
        )
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
            "软件当前可调整的选项",
            "当前版本暂无可调整的设置项。",
        ),
    }
    try:
        title, description, message = placeholders[route]
    except KeyError as exc:
        raise ValueError(f"unsupported G03 route: {route!r}") from exc
    return PlaceholderPage(route, title, description, message, parent)
