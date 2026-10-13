"""Business-neutral pages and safe empty/placeholder states."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from html import escape as html_escape
import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QSignalBlocker, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QTabWidget,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
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
    REPORT_FIELD_LABELS,
    build_activity_evidence_view,
    build_home_record_label,
    build_parameter_view,
    build_calculation_basis_view,
    build_quality_view,
    build_record_list_label,
    standard_label,
    build_report_view,
    evidence_names_for,
    format_amount,
    period_label,
    status_label,
    snapshot_state,
    summary_with_trace,
)

from .design_tokens import (
    COMPACT_HOME_PAGE_SIDE_MARGIN,
    HOME_CANVAS_GRADIENT,
    HOME_CONTENT_MAX_WIDTH,
    HOME_PAGE_SIDE_MARGIN,
    WIDE_PAGE_MARGIN,
)
from .excel_import_components import ExcelImportPreviewPanel, create_excel_import_section
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

# These formatters are used only by the historical record presentation.
_SNAPSHOT_LABELS.update(REPORT_FIELD_LABELS)
_SNAPSHOT_LABELS.update({
    "calcinations": "原料煅烧过程", "bakings": "焙烧/炭化过程",
    "graphitizations": "石墨化过程", "fume_incinerations": "烟气焚烧设施",
    "fgd_units": "烟气脱硫设施", "materials": "物料明细", "name": "物料名称",
    "role": "物料用途", "mass_t": "质量（t）", "fixed_carbon_pct": "固定碳含量（%）",
    "volatile_matter_pct": "挥发分含量（%）",
})
_SNAPSHOT_VALUE_LABELS["ratio"] = "比例（0～1）"

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
_SNAPSHOT_INTERNAL_EVIDENCE_KEYS = frozenset({
    "evidence_id", "source_ids", "evidence_ref_ids", "input_id", "enterprise_id",
    "instance_id", "detail_id", "line_id", "parameter_id", "factor_id",
    "source_id", "ingress_provenance",
})


def _snapshot_label(key: object) -> str:
    key_text = str(key)
    if key_text.endswith("电力明细证明"):
        return key_text
    return _SNAPSHOT_LABELS.get(key_text, "其他已保存输入")


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
        "source_version",
        "source_location",
        "selection_reason",
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
            lines.extend(_snapshot_lines(section, indent="  ", excluded_keys=_SNAPSHOT_PROOF_KEYS | _SNAPSHOT_INTERNAL_EVIDENCE_KEYS))
        else:
            lines.extend(_snapshot_lines(section, indent="  "))
    return "\n".join(lines)


def _format_reporting_snapshot(reporting_snapshot: object) -> str:
    if not isinstance(reporting_snapshot, dict) or not reporting_snapshot:
        return "历史记录未保存该信息。"
    return "\n".join(
        _snapshot_lines(reporting_snapshot, excluded_keys=_SNAPSHOT_INTERNAL_EVIDENCE_KEYS)
    )


def _record_summary_markup(summary: str) -> str:
    """Style the already-built frozen-record summary without reinterpreting values."""

    sections: dict[str, list[str]] = {"基本信息": [], "核算结果": []}
    notes: list[str] = []
    current: str | None = None
    for raw_line in summary.splitlines():
        line = raw_line.strip()
        if line in sections:
            current = line
        elif line.startswith("关键提醒：") or line.startswith("标准报告数据 "):
            notes.append(line)
        elif line and current is not None:
            sections[current].append(line)

    info_rows = []
    for line in sections["基本信息"]:
        label, separator, value = line.partition("：")
        if separator:
            info_rows.append(
                "<tr>"
                f'<td style="padding:5px 12px 5px 0;color:#698198;white-space:nowrap">{html_escape(label)}</td>'
                f'<td style="padding:5px 0;color:#213A4F">{html_escape(value)}</td>'
                "</tr>"
            )
        else:
            info_rows.append(
                f'<tr><td colspan="2" style="padding:5px 0;color:#213A4F">{html_escape(line)}</td></tr>'
            )

    result_lines = sections["核算结果"]
    total_line = next(
        (line for line in result_lines if line.startswith("温室气体排放总量：")),
        "历史记录未保存总排放量。",
    )
    other_results = [line for line in result_lines if line != total_line]
    result_rows = []
    for index in range(0, len(other_results), 2):
        cells = other_results[index:index + 2]
        rendered_cells = "".join(
            '<td style="width:50%;vertical-align:top;padding:11px 12px;'
            'border:1px solid #DCEAF3;border-radius:9px;background:#F7FBFE;'
            f'color:#395B73">{html_escape(line)}</td>'
            for line in cells
        )
        if len(cells) == 1:
            rendered_cells += '<td style="width:50%"></td>'
        result_rows.append(f"<tr>{rendered_cells}</tr>")
    note_markup = "".join(
        '<p style="margin:10px 0 0;padding:9px 11px;background:#EFF7FD;'
        'border-left:3px solid #4299C5;color:#47697F">'
        f"{html_escape(note)}</p>"
        for note in notes
    )
    return (
        '<html><body style="font-family:\'Microsoft YaHei UI\',\'Microsoft YaHei\',sans-serif;'
        'font-size:10pt;color:#213A4F">'
        '<h3 style="margin:2px 0 10px;color:#18364F;font-size:12pt">基本信息</h3>'
        '<table width="100%" cellspacing="0" cellpadding="0" '
        'style="border-collapse:collapse;margin-bottom:16px">'
        + "".join(info_rows)
        + '</table><h3 style="margin:6px 0 10px;color:#18364F;font-size:12pt">核算结果</h3>'
        '<div style="padding:14px 16px;border:1px solid #CFE5F3;border-radius:10px;'
        'background:#ECF7FF;color:#155C88;font-size:11pt;font-weight:600">'
        + html_escape(total_line)
        + '</div><table width="100%" cellspacing="8" cellpadding="0" style="margin:3px -8px 0">'
        + "".join(result_rows)
        + "</table>"
        + note_markup
        + "</body></html>"
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
        self.body_layout.setSpacing(22)

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
    layout.setContentsMargins(22, 19, 22, 19)
    layout.setSpacing(12)
    title_label = QLabel(title, card)
    title_label.setObjectName("cardTitle")
    layout.addWidget(title_label)
    return card, layout


class _HomeHillsDecoration(QWidget):
    """Lightweight native decoration matching the V4 landing-page illustration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("homeHillsDecoration")
        self.setFixedSize(295, 78)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.scale(self.width() / 295, self.height() / 78)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setOpacity(0.78)
        painter.setBrush(QColor("#b6d9ec"))
        painter.drawPolygon(QPolygonF((
            QPointF(0, 62), QPointF(44, 45), QPointF(70, 56),
            QPointF(131, 17), QPointF(180, 57), QPointF(228, 35),
            QPointF(270, 60), QPointF(295, 64), QPointF(295, 69),
            QPointF(0, 69),
        )))
        painter.setBrush(QColor("#9bccdc"))
        painter.drawPolygon(QPolygonF((
            QPointF(18, 64), QPointF(74, 54), QPointF(127, 65),
            QPointF(182, 29), QPointF(231, 62), QPointF(277, 54),
            QPointF(295, 65), QPointF(295, 69), QPointF(18, 69),
        )))
        painter.setBrush(QColor("#9bd6d5"))
        painter.drawPolygon(QPolygonF((
            QPointF(111, 63), QPointF(176, 48), QPointF(218, 58),
            QPointF(259, 42), QPointF(292, 64), QPointF(292, 69),
            QPointF(111, 69),
        )))
        painter.setBrush(QColor("#c9e6f3"))
        painter.drawEllipse(0, 65, 295, 12)
        painter.end()


class HomePage(BasePage):
    """Task-first, standard-neutral home backed by saved projects and records."""

    record_requested = Signal(str)
    project_requested = Signal(str)
    project_manager_requested = Signal()

    _ENTRY_DESCRIPTIONS = {
        AppRoute.STANDARDS: "检索标准，查看适用范围与技术要求",
        AppRoute.NEW_ACCOUNTING: "按已开放标准开展核算，管理核算项目",
        AppRoute.EXCEL_IMPORT: "检查已支持标准的工作簿并保存项目",
        AppRoute.RECORDS: "查看历史结果、依据及 Word 报告",
        AppRoute.FACTORS: "浏览来源、核算参数与排放因子",
    }

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
        self._navigate = navigate
        self.entry_buttons: dict[AppRoute, QPushButton] = {}
        self.project_layout: QVBoxLayout
        self.recent_layout: QVBoxLayout
        self.body_layout.setSpacing(0)
        self.body_layout.setContentsMargins(
            HOME_PAGE_SIDE_MARGIN, 36, HOME_PAGE_SIDE_MARGIN, 25
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QWidget#page_home {{ background: {HOME_CANVAS_GRADIENT}; }}"
        )

        self.body_layout.addWidget(
            self._build_home_header(view_model, logo_path)
        )
        self.body_layout.addSpacing(25)
        self.body_layout.addWidget(self._build_entry_cards(view_model, navigate))
        self.body_layout.addSpacing(20)
        self.body_layout.addWidget(self._build_recent_work(navigate))
        self.body_layout.addStretch(1)
        self.body_layout.addWidget(self._build_home_footer(view_model, navigate))
        self.refresh_recent_records()

    def set_page_margin(self, margin: int) -> None:
        compact = margin == COMPACT_HOME_PAGE_SIDE_MARGIN
        self.body_layout.setContentsMargins(
            margin,
            26 if compact else 36,
            margin,
            23 if compact else 25,
        )

    def _icon_label(
        self,
        name: str,
        color: str,
        size: int,
        parent: QWidget,
    ) -> QLabel:
        label = QLabel(parent)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if self._icon_directory is not None:
            icon = load_tinted_icon(
                self._icon_directory / f"{name}.svg",
                color,
                size=size,
            )
            label.setPixmap(icon.pixmap(QSize(size, size)))
        return label

    @staticmethod
    def _apply_home_shadow(widget: QWidget, alpha: int = 14) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(39, 81, 113, alpha))
        widget.setGraphicsEffect(shadow)

    def _build_home_header(
        self,
        view_model: ShellViewModel,
        logo_path: Path | None,
    ) -> QWidget:
        header = QWidget(self)
        header.setObjectName("homeHeader")
        header.setMinimumHeight(130)
        header.setMaximumHeight(130)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(30)

        title_row = QWidget(header)
        title_row.setObjectName("homeTitleRow")
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(21)

        logo_label = QLabel(title_row)
        logo_label.setObjectName("homeLogo")
        logo_label.setAccessibleName("青舟节能")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_label.setFixedSize(186, 52)
        if logo_path is not None:
            logo = QPixmap(str(logo_path))
            if not logo.isNull():
                logo_label.setPixmap(
                    logo.scaled(
                        QSize(186, 52),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if logo_label.pixmap() is None or logo_label.pixmap().isNull():
            logo_label.setText("青舟节能")
        title_layout.addWidget(logo_label)

        divider = QFrame(title_row)
        divider.setObjectName("homeBrandDivider")
        divider.setFixedSize(1, 60)
        divider.setStyleSheet(
            "QFrame#homeBrandDivider { background: #bad0e0; border: none; }"
        )
        title_layout.addWidget(divider)

        title_group = QWidget(title_row)
        title_group.setObjectName("homeTitleGroup")
        title_group_layout = QVBoxLayout(title_group)
        title_group_layout.setContentsMargins(0, 0, 0, 0)
        title_group_layout.setSpacing(6)
        title = QLabel(view_model.home_title, title_group)
        title.setObjectName("pageTitle")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 30px; font-weight: 800; color: #183c57;")
        title.setFixedHeight(42)
        title_group_layout.addWidget(title)
        description = QLabel(view_model.home_description, title_group)
        description.setObjectName("homeDescription")
        description.setWordWrap(True)
        description.setStyleSheet("color: #698198; font-size: 13px;")
        title_group_layout.addWidget(description)
        title_group.setFixedHeight(66)
        title_layout.addWidget(title_group, 1)
        header_layout.addWidget(title_row, 1)
        header_layout.addWidget(
            _HomeHillsDecoration(header),
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        return header

    def _build_entry_cards(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
    ) -> QWidget:
        workspace = QWidget(self)
        workspace.setObjectName("primaryWorkspace")
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        entries = [
            item
            for item in view_model.navigation
            if item.route not in {AppRoute.HOME, AppRoute.SETTINGS}
        ]
        for item in entries:
            button = QPushButton(item.label, workspace)
            button.setObjectName("homeEntryButton")
            button.setProperty("route", item.route.value)
            button.setProperty("primary", item.route is AppRoute.STANDARDS)
            button.setAccessibleName(item.label)
            description = self._ENTRY_DESCRIPTIONS.get(item.route, item.label)
            button.setAccessibleDescription(description)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.setCursor(
                Qt.CursorShape.ArrowCursor
                if item.reserved
                else Qt.CursorShape.PointingHandCursor
            )
            button.setEnabled(not item.reserved)
            if item.reserved:
                button.setToolTip(f"{item.label}当前暂未开放。")

            button_layout = QVBoxLayout(button)
            button_layout.setContentsMargins(18, 23, 18, 18)
            button_layout.setSpacing(0)

            icon_box = QFrame(button)
            icon_box.setObjectName("homeActionIcon")
            icon_box.setFixedSize(43, 43)
            icon_box_layout = QVBoxLayout(icon_box)
            icon_box_layout.setContentsMargins(0, 0, 0, 0)
            entry_icon = self._icon_label(
                item.icon_name,
                "#FFFFFF" if item.route is AppRoute.STANDARDS else "#197cc2",
                24,
                icon_box,
            )
            entry_icon.setObjectName("homeEntryIcon")
            icon_box_layout.addWidget(entry_icon)
            button_layout.addWidget(icon_box)
            button_layout.addSpacing(24)

            title = QLabel(item.label, button)
            title.setObjectName("homeEntryTitle")
            title.setWordWrap(True)
            button_layout.addWidget(title)
            button_layout.addSpacing(8)

            detail = QLabel(description, button)
            detail.setObjectName("homeEntryDescription")
            detail.setWordWrap(True)
            button_layout.addWidget(detail)
            button_layout.addStretch(1)

            arrow = QLabel("›", button)
            arrow.setObjectName("homeEntryArrow")
            arrow.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            button_layout.addWidget(arrow)

            button.setStyleSheet("""
                QPushButton#homeEntryButton {
                    background: #FFFFFF; border: 1px solid #dae7f1; border-radius: 14px;
                    color: transparent; text-align: left; min-height: 180px;
                }
                QPushButton#homeEntryButton:hover {
                    border-color: #a7cce9; background: #FFFFFF;
                }
                QPushButton#homeEntryButton:focus {
                    border: 2px solid #4a9fd5;
                }
                QPushButton#homeEntryButton:disabled {
                    background: #FFFFFF;
                }
                QPushButton#homeEntryButton[primary="true"] {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1679bf, stop:1 #3a97d0);
                    border: 1px solid #1679bf;
                }
                QPushButton#homeEntryButton[primary="true"]:hover {
                    border-color: #348fc2;
                }
                QLabel#homeEntryTitle {
                    color: #18364f; font-size: 17px; font-weight: 700;
                }
                QLabel#homeEntryDescription {
                    color: #698198; font-size: 12px;
                }
                QLabel#homeEntryArrow {
                    color: #83abc8; font-size: 23px; padding-right: 1px;
                }
                QPushButton#homeEntryButton[primary="true"] QLabel#homeEntryTitle,
                QPushButton#homeEntryButton[primary="true"] QLabel#homeEntryDescription,
                QPushButton#homeEntryButton[primary="true"] QLabel#homeEntryArrow {
                    color: #FFFFFF;
                }
                QFrame#homeActionIcon {
                    background: #e9f4fd; border: none; border-radius: 12px;
                }
                QPushButton#homeEntryButton[primary="true"] QFrame#homeActionIcon {
                    background: rgba(255, 255, 255, 0.19);
                }
            """)
            button.setMinimumHeight(180)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.clicked.connect(
                lambda _checked=False, route=item.route: navigate(route)
            )
            layout.addWidget(
                button,
                147 if item.route is AppRoute.STANDARDS else 100,
            )
            self.entry_buttons[item.route] = button
            self._apply_home_shadow(
                button,
                alpha=19 if item.route is AppRoute.STANDARDS else 11,
            )
        return workspace

    def _create_home_card(
        self,
        object_name: str,
        title: str,
        icon_name: str,
        action_text: str,
        action,
    ) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame(self)
        card.setObjectName(object_name)
        card.setMinimumHeight(279)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)

        heading = QWidget(card)
        heading.setObjectName("homeCardHeader")
        heading_layout = QHBoxLayout(heading)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setSpacing(8)
        icon = self._icon_label(icon_name, "#18364f", 18, heading)
        icon.setFixedSize(20, 20)
        heading_layout.addWidget(icon)
        title_label = QLabel(title, heading)
        title_label.setObjectName("homeCardTitle")
        heading_layout.addWidget(title_label)
        heading_layout.addStretch(1)
        action_button = QPushButton(action_text, heading)
        action_button.setObjectName("homeCardAction")
        action_button.setAccessibleName(action_text)
        action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        action_button.clicked.connect(
            lambda _checked=False: action()
        )
        heading_layout.addWidget(action_button)
        card_layout.addWidget(heading)

        content = QWidget(card)
        content.setObjectName(f"{object_name}Content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        card_layout.addWidget(content, 1)
        card.setStyleSheet("""
            QFrame#recentProjectsCard, QFrame#recentRecordsCard {
                background: #FFFFFF; border: 1px solid #dae7f1; border-radius: 14px;
            }
            QLabel#homeCardTitle {
                color: #18364f; font-size: 17px; font-weight: 700;
            }
            QPushButton#homeCardAction {
                border: none; background: transparent; color: #12649a;
                font-size: 13px; font-weight: 600; padding: 4px 2px;
            }
            QPushButton#homeCardAction:hover { text-decoration: underline; }
            QPushButton#homeCardAction:focus {
                border: 2px solid #4a9fd5; border-radius: 4px;
            }
        """)
        self._apply_home_shadow(card)
        if object_name == "recentProjectsCard":
            self.project_layout = content_layout
        else:
            self.recent_layout = content_layout
        return card, content_layout

    def _build_recent_work(self, navigate: Navigate) -> QWidget:
        recent_work = QWidget(self)
        recent_work.setObjectName("recentWorkCard")
        layout = QHBoxLayout(recent_work)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        projects_card, _ = self._create_home_card(
            "recentProjectsCard",
            "继续工作",
            "new",
            "全部项目  ›",
            lambda: self.project_manager_requested.emit(),
        )
        records_card, _ = self._create_home_card(
            "recentRecordsCard",
            "最近核算",
            "records",
            "查看全部  ›",
            lambda: navigate(AppRoute.RECORDS),
        )
        layout.addWidget(projects_card, 94)
        layout.addWidget(records_card, 135)
        return recent_work

    def _build_home_footer(
        self,
        view_model: ShellViewModel,
        navigate: Navigate,
    ) -> QWidget:
        footer = QWidget(self)
        footer.setObjectName("homeFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        settings_item = next(
            item for item in view_model.navigation if item.route is AppRoute.SETTINGS
        )
        settings_button = QPushButton(settings_item.label, footer)
        settings_button.setObjectName("homeSettingsButton")
        settings_button.setProperty("route", settings_item.route.value)
        settings_button.setAccessibleName(settings_item.label)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.setMinimumHeight(32)
        if self._icon_directory is not None:
            settings_button.setIcon(
                load_tinted_icon(
                    self._icon_directory / f"{settings_item.icon_name}.svg",
                    "#197cc2",
                    size=16,
                )
            )
        settings_button.setIconSize(QSize(16, 16))
        settings_button.setStyleSheet("""
            QPushButton#homeSettingsButton {
                border: none; background: transparent; color: #12649a;
                padding: 2px 0; font-size: 12px; font-weight: 600; text-align: left;
            }
            QPushButton#homeSettingsButton:hover { text-decoration: underline; }
            QPushButton#homeSettingsButton:focus {
                border: 2px solid #4a9fd5; border-radius: 4px;
            }
        """)
        settings_button.clicked.connect(
            lambda _checked=False: navigate(AppRoute.SETTINGS)
        )
        layout.addWidget(settings_button)
        layout.addStretch(1)

        brand = QLabel(view_model.product_name, footer)
        brand.setObjectName("homeFooterBrand")
        brand.setStyleSheet("color: #94a6b3; font-size: 11px;")
        layout.addWidget(brand)
        return footer

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _show_project_empty(self, title: str, description: str) -> None:
        self._clear_layout(self.project_layout)
        title_label = QLabel(title)
        title_label.setObjectName("projectRecentStateTitle")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #213a4f; font-size: 16px; font-weight: 700;")
        description_label = QLabel(description)
        description_label.setObjectName("projectRecentStateDescription")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("color: #698198; font-size: 12px;")
        self.project_layout.addStretch(1)
        self.project_layout.addWidget(title_label)
        self.project_layout.addSpacing(4)
        self.project_layout.addWidget(description_label)
        self.project_layout.addStretch(2)

    def _show_record_empty(self, title: str, description: str) -> None:
        self._clear_layout(self.recent_layout)
        title_label = QLabel(title)
        title_label.setObjectName("recordRecentStateTitle")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #213a4f; font-size: 16px; font-weight: 700;")
        description_label = QLabel(description)
        description_label.setObjectName("recordRecentStateDescription")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("color: #698198; font-size: 12px;")
        self.recent_layout.addStretch(1)
        self.recent_layout.addWidget(title_label)
        self.recent_layout.addSpacing(4)
        self.recent_layout.addWidget(description_label)
        self.recent_layout.addStretch(2)

    def _build_project_resume_card(
        self,
        workspace: ProjectWorkspace,
        updated_at: datetime | None,
    ) -> QWidget:
        resume = QFrame()
        resume.setObjectName("resumeProjectCard")
        resume.setStyleSheet("""
            QFrame#resumeProjectCard {
                background: #f1faf9; border: 1px solid #cbe7e5; border-radius: 12px;
            }
            QFrame#homeProjectIconBox {
                background: #e0f3ef; border: none; border-radius: 12px;
            }
            QLabel#recentProjectLabel {
                color: #213a4f; font-size: 14px; font-weight: 700;
            }
            QLabel#homeProjectUpdated, QLabel#homeProjectDescription {
                color: #698198; font-size: 12px;
            }
            QLabel#homeProjectBadge {
                background: #eaf3fc; color: #287ab4; border-radius: 7px;
                padding: 3px 9px; font-size: 11px; font-weight: 680;
            }
            QPushButton#resumeProjectButton {
                background: #197cc2; border: 1px solid #197cc2; border-radius: 8px;
                color: #FFFFFF; padding: 0 12px; min-height: 34px;
                font-size: 12px; font-weight: 650;
            }
            QPushButton#resumeProjectButton:hover {
                background: #12649a; border-color: #12649a;
            }
            QPushButton#resumeProjectButton:focus { border: 2px solid #7ec4ed; }
        """)
        layout = QHBoxLayout(resume)
        layout.setContentsMargins(16, 15, 16, 15)
        layout.setSpacing(12)

        icon_box = QFrame(resume)
        icon_box.setObjectName("homeProjectIconBox")
        icon_box.setFixedSize(46, 46)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(self._icon_label("new", "#168268", 24, icon_box))
        layout.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)

        details = QWidget(resume)
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(4)
        name = QLabel(workspace.name, details)
        name.setObjectName("recentProjectLabel")
        name.setWordWrap(True)
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addWidget(name)

        badge = QLabel("已保存", details)
        badge.setObjectName("homeProjectBadge")
        badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        details_layout.addWidget(badge)

        if updated_at is not None:
            updated = QLabel(
                f"最近修改：{updated_at.astimezone().strftime('%Y-%m-%d %H:%M')}",
                details,
            )
            updated.setObjectName("homeProjectUpdated")
            details_layout.addWidget(updated)

        description = QLabel(
            f"包含 {len(workspace.units)} 个核算单元，打开后可继续编辑。",
            details,
        )
        description.setObjectName("homeProjectDescription")
        description.setWordWrap(True)
        details_layout.addWidget(description)
        layout.addWidget(details, 1)

        button = QPushButton("继续编辑", resume)
        button.setObjectName("resumeProjectButton")
        button.setAccessibleName(f"继续编辑项目：{workspace.name}")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda _checked=False, project_id=workspace.project_id:
                self.project_requested.emit(project_id)
        )
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        return resume

    def _build_recent_record_table(
        self,
        records: tuple[AccountingRecord, ...],
    ) -> QTableWidget:
        table = QTableWidget(len(records), 5)
        table.setObjectName("homeRecentTable")
        table.setAccessibleName("最近核算记录")
        table.setAccessibleDescription(
            "显示最近三条正式核算记录；选择打开可查看不可变记录详情。"
        )
        table.setHorizontalHeaderLabels(
            ("企业 / 项目", "周期", "状态", "日期", "操作")
        )
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setMinimumSectionSize(62)
        for column, width in enumerate((190, 88, 94, 96, 78)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(column, width)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        operation_header = table.horizontalHeaderItem(4)
        if operation_header is not None:
            operation_header.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setStyleSheet("""
            QTableWidget#homeRecentTable {
                border: none; background: transparent; color: #213a4f;
                font-size: 12px; outline: none;
            }
            QTableWidget#homeRecentTable QHeaderView::section {
                background: #f4f8fc; color: #597187; border: none;
                padding: 9px 8px; font-size: 11px; font-weight: 650;
            }
            QTableWidget#homeRecentTable::item {
                border-bottom: 1px solid #edf2f6; padding: 8px;
            }
            QTableWidget#homeRecentTable::item:hover { background: #f9fcff; }
        """)
        table.verticalHeader().setDefaultSectionSize(50)

        for row, record in enumerate(records):
            enterprise = record.input_snapshot.enterprise_name or "未填写企业"
            period = period_label(record)
            name_item = QTableWidgetItem(enterprise)
            name_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            name_item.setToolTip(enterprise)
            table.setItem(row, 0, name_item)
            period_item = QTableWidgetItem(period)
            period_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            table.setItem(row, 1, period_item)

            status_text = status_label(record.status)
            status = QLabel(status_text)
            status.setObjectName("homeRecordStatus")
            status.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            status.setAccessibleName(f"核算状态：{status_text}")
            is_warning = record.status is RecordStatus.COMPLETED_WITH_WARNINGS
            status_color = (
                "background: #fff5e1; color: #956420;"
                if is_warning
                else "background: #e7f6f0; color: #168268;"
            )
            status.setStyleSheet(
                f"QLabel {{ border-radius: 7px; padding: 3px 8px; font-size: 11px; {status_color} }}"
            )
            table.setCellWidget(row, 2, status)

            date_item = QTableWidgetItem(
                record.created_at.astimezone().date().isoformat()
            )
            date_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            table.setItem(row, 3, date_item)

            action = QPushButton("打开  ›")
            action.setObjectName("openRecentRecordButton")
            action.setAccessibleName(f"打开{enterprise} {period}的核算记录")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.setStyleSheet("""
                QPushButton#openRecentRecordButton {
                    border: none; background: transparent; color: #12649a;
                    min-height: 24px; max-height: 24px;
                    padding: 2px; font-size: 12px; font-weight: 600;
                    text-align: left;
                }
                QPushButton#openRecentRecordButton:hover { text-decoration: underline; }
                QPushButton#openRecentRecordButton:focus {
                    border: 2px solid #4a9fd5; border-radius: 4px;
                }
            """)
            action.clicked.connect(
                lambda _checked=False, record_id=record.record_id:
                    self.record_requested.emit(record_id)
            )
            action.setFixedHeight(28)
            action_cell = QWidget(table)
            action_layout = QHBoxLayout(action_cell)
            action_layout.setContentsMargins(4, 0, 4, 0)
            action_layout.setSpacing(0)
            action_layout.addWidget(
                action, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            table.setCellWidget(row, 4, action_cell)
        table.resizeRowsToContents()
        for row in range(table.rowCount()):
            table.setRowHeight(row, 44)
        return table

    def refresh_recent_records(self) -> None:
        """Refresh the real project and immutable-record views from existing services."""

        if self.project_service is None:
            self._show_project_empty("项目暂不可用", "当前无法读取已保存项目。")
        else:
            try:
                projects = tuple(self.project_service.list_all())
                reader = getattr(
                    self.project_service,
                    "list_updated_at_by_project_id",
                    None,
                )
                timestamps = reader() if callable(reader) else {}
                projects = tuple(sorted(
                    projects,
                    key=lambda project: (
                        timestamps[project.project_id].timestamp()
                        if isinstance(timestamps.get(project.project_id), datetime)
                        else 0
                    ),
                    reverse=True,
                ))
            except Exception:
                _LOGGER.exception("Unable to read saved projects for the home page")
                projects = None
                timestamps = {}
            if projects is None:
                self._show_project_empty("项目暂不可用", "本地项目数据当前无法读取。")
            elif not projects:
                self._show_project_empty(
                    "暂无已保存项目",
                    "保存后的项目会显示在这里，可从新建核算中继续编辑。",
                )
            else:
                latest = projects[0]
                self._clear_layout(self.project_layout)
                updated_at = timestamps.get(latest.project_id)
                self.project_layout.addWidget(
                    self._build_project_resume_card(
                        latest,
                        updated_at if isinstance(updated_at, datetime) else None,
                    )
                )
                self.project_layout.addStretch(1)

        if self.record_repository is None:
            self._show_record_empty("记录暂不可用", "当前无法读取核算记录。")
            return
        try:
            records = tuple(sorted(
                self.record_repository.list_all(),
                key=lambda record: record.created_at,
                reverse=True,
            )[:3])
        except Exception:
            _LOGGER.exception("Unable to read formal records for the home page")
            records = None
        if records is None:
            self._show_record_empty("记录暂不可用", "本地核算记录当前无法读取。")
            return
        if not records:
            self._show_record_empty(
                "暂无核算记录",
                "完成一次正式核算后，记录会显示在这里。",
            )
            return
        self._clear_layout(self.recent_layout)
        self.recent_layout.addWidget(self._build_recent_record_table(records))


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


class SettingsPage(BasePage):
    """Standard-neutral settings overview matching the V4 two-column layout."""

    def __init__(
        self,
        view_model: ShellViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.SETTINGS, parent)
        self.add_header(
            "设置",
            "当前主线只保留真实设置入口，暂无已实现的可调整业务设置项。",
        )
        card, card_layout = _card("当前版本", self)
        columns = QWidget(card)
        columns.setObjectName("settingsColumns")
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)

        info = QFrame(columns)
        info.setObjectName("settingsSurface")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(14, 14, 14, 14)
        info_layout.setSpacing(12)
        info_title = QLabel("软件信息", info)
        info_title.setObjectName("cardTitle")
        info_layout.addWidget(info_title)
        facts = (
            ("产品", view_model.product_name),
            ("运行平台", "Windows 桌面版"),
            ("界面技术", "PySide6 · Qt Widgets"),
        )
        for label_text, value_text in facts:
            row = QWidget(info)
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setHorizontalSpacing(14)
            row_layout.setVerticalSpacing(8)
            label = QLabel(label_text, row)
            label.setObjectName("detailFieldLabel")
            value = QLabel(value_text, row)
            value.setObjectName("detailFieldValue")
            value.setWordWrap(True)
            row_layout.addWidget(label, 0, 0)
            row_layout.addWidget(value, 0, 1)
            row_layout.setColumnStretch(1, 1)
            info_layout.addWidget(row)
        info_layout.addStretch(1)

        options = QFrame(columns)
        options.setObjectName("settingsSurface")
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(14, 14, 14, 14)
        options_layout.setSpacing(12)
        options_title = QLabel("可调整项目", options)
        options_title.setObjectName("cardTitle")
        options_layout.addWidget(options_title)
        empty_state = QWidget(options)
        empty_layout = QVBoxLayout(empty_state)
        empty_layout.setContentsMargins(8, 10, 8, 10)
        empty_layout.setSpacing(8)
        empty_title = QLabel("当前版本暂无可调整的设置项", empty_state)
        empty_title.setObjectName("emptyStateTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_description = QLabel(
            "此处仅显示本版本已经开放的设置。",
            empty_state,
        )
        empty_description.setObjectName("emptyStateDescription")
        empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_description.setWordWrap(True)
        empty_layout.addStretch(1)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_description)
        empty_layout.addStretch(1)
        options_layout.addWidget(empty_state, 1)

        columns_layout.addWidget(info, 1)
        columns_layout.addWidget(options, 1)
        card_layout.addWidget(columns, 1)
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
        self._detail_record_id: str | None = None
        self.add_header("核算记录", "搜索已保存的核算记录，查看历史结果和计算依据。")
        self.page_title = self.findChild(QLabel, "pageTitle")
        self.page_description = self.findChild(QLabel, "pageDescription")
        self.view_stack = QStackedWidget(self)
        self.view_stack.setObjectName("recordPageStack")
        self.list_view = QWidget(self.view_stack)
        list_layout = QVBoxLayout(self.list_view)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(16)

        filter_card, filter_layout = _card("搜索与筛选", self.list_view)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        self.search_input = QLineEdit(filter_card)
        self.search_input.setObjectName("recordSearchInput")
        self.search_input.setAccessibleName("搜索核算记录")
        self.search_input.setPlaceholderText("搜索企业名称、期间、标准或记录编号")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.refresh_records)
        filter_row.addWidget(self.search_input, 1)
        self.status_filter = QComboBox(filter_card)
        self.status_filter.setObjectName("recordStatusFilter")
        self.status_filter.setAccessibleName("核算状态筛选")
        self.status_filter.addItem("全部状态", "ALL")
        self.status_filter.addItem("已完成", RecordStatus.COMPLETED.value)
        self.status_filter.addItem("含提醒", RecordStatus.COMPLETED_WITH_WARNINGS.value)
        self.status_filter.currentIndexChanged.connect(self.refresh_records)
        filter_row.addWidget(self.status_filter)
        filter_layout.addLayout(filter_row)
        list_layout.addWidget(filter_card)

        records_card, records_layout = _card("记录列表", self.list_view)
        self.result_count = QLabel(records_card)
        self.result_count.setObjectName("recordResultCount")
        records_layout.addWidget(self.result_count)
        self.record_list = QTableWidget(records_card)
        self.record_list.setObjectName("recordTable")
        self.record_list.setAccessibleName("核算记录列表")
        self.record_list.setAccessibleDescription(
            "按行浏览不可变核算记录；按 Enter 打开记录详情，也可使用行内操作按钮。"
        )
        self.record_list.setColumnCount(7)
        self.record_list.setHorizontalHeaderLabels(
            ("企业 / 项目", "核算期间", "标准", "排放总量", "状态", "日期", "操作")
        )
        self.record_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.record_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.record_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.record_list.setAlternatingRowColors(True)
        self.record_list.setWordWrap(True)
        self.record_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.record_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.record_list.setTabKeyNavigation(True)
        self.record_list.verticalHeader().setVisible(False)
        self.record_list.horizontalHeader().setStretchLastSection(True)
        self.record_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate((230, 150, 205, 165, 100, 125, 115)):
            self.record_list.setColumnWidth(column, width)
        self.record_list.setMinimumHeight(340)
        self.record_list.cellActivated.connect(
            lambda row, _column: self._open_record_row(row)
        )
        self.record_list.cellDoubleClicked.connect(
            lambda row, _column: self._open_record_row(row)
        )
        records_layout.addWidget(self.record_list, 1)
        list_layout.addWidget(records_card, 1)
        self.view_stack.addWidget(self.list_view)

        self.detail_view = QWidget(self.view_stack)
        detail_layout = QVBoxLayout(self.detail_view)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(16)
        detail_header = QHBoxLayout()
        self.back_to_records_button = QPushButton("返回记录列表", self.detail_view)
        self.back_to_records_button.setObjectName("backToRecordListButton")
        self.back_to_records_button.clicked.connect(self._back_to_list)
        detail_header.addWidget(self.back_to_records_button)
        self.detail_heading = QLabel("核算记录详情", self.detail_view)
        self.detail_heading.setObjectName("recordDetailHeading")
        self.detail_heading.setWordWrap(True)
        detail_header.addWidget(self.detail_heading, 1)
        detail_layout.addLayout(detail_header)
        detail_card, detail_card_layout = _card("历史记录 · 只读", self.detail_view)
        self.detail_tabs = QTabWidget(detail_card)
        self.detail_tabs.setObjectName("recordDetailTabs")
        self.summary_text = self._readonly_text("recordSummaryView", self.detail_tabs)
        self.input_basis_text = self._readonly_text("recordInputBasisView", self.detail_tabs)
        self.detail_tabs.addTab(self.summary_text, "基本信息与结果")
        self.detail_tabs.addTab(self.input_basis_text, "输入数据与计算依据")
        detail_card_layout.addWidget(self.detail_tabs, 1)

        actions = QHBoxLayout()
        self.delete_button = QPushButton("删除记录", detail_card)
        self.delete_button.setObjectName("deleteRecordButton")
        self.delete_button.clicked.connect(self._delete_selected)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        self.export_word_button = QPushButton("导出 Word 核算报告", detail_card)
        self.export_word_button.setObjectName("exportWordReportButton")
        self.export_word_button.clicked.connect(self._export_selected_report)
        actions.addWidget(self.export_word_button)
        detail_card_layout.addLayout(actions)
        detail_layout.addWidget(detail_card, 1)
        self.view_stack.addWidget(self.detail_view)
        self.body_layout.addWidget(self.view_stack, 1)
        self.setStyleSheet("""
            QPushButton#backToRecordListButton,
            QPushButton#deleteRecordButton, QPushButton#exportWordReportButton {
                min-height: 36px; padding: 0 16px; border-radius: 8px;
                border: 1px solid #D4E4F0; background: white; font-size: 13px;
            }
            QPushButton#exportWordReportButton { background: #197CC2; border-color: #197CC2; color: white; }
            QPushButton#deleteRecordButton { color: #B42318; }
            QLabel#recordDetailHeading { font-size: 18px; font-weight: 700; color: #18364F; }
            QLabel#recordResultCount { color: #698198; font-size: 12px; }
            QTextEdit#recordSummaryView, QTextEdit#recordInputBasisView {
                border: none; padding: 14px; background: white; font-size: 13px;
            }
            QLabel#recordStatusBadge {
                border-radius: 8px; padding: 4px 9px; font-size: 11px;
                font-weight: 650; background: #E7F6F0; color: #168268;
            }
            QLabel#recordStatusBadge[warning="true"] { background: #FFF5E1; color: #956420; }
            QPushButton#openRecordRowButton {
                min-height: 30px; padding: 0 10px; border-radius: 7px;
                background: transparent; border: 1px solid transparent;
                color: #12649A; font-size: 12px; font-weight: 650;
            }
            QPushButton#openRecordRowButton:hover { background: #EAF4FC; border-color: #D1E6F3; }
            QTabWidget#recordDetailTabs::pane { border: 1px solid #DAE7F1; border-radius: 9px; }
            QTabWidget#recordDetailTabs QTabBar::tab { padding: 0 18px; font-size: 13px; }
        """)
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
            self.record_list.item(self.record_list.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
            if self.record_list.currentRow() >= 0
            and self.record_list.item(self.record_list.currentRow(), 0) is not None
            else None
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
                or query in build_record_list_label(record).casefold()
                or query in record.record_id.casefold()
                or query in record.standard_id.casefold()
                or query in (record.input_snapshot.enterprise_name or "").casefold()
                or query in str(record.input_snapshot.period.start).casefold()
                or query in str(record.input_snapshot.period.end).casefold()
            )
        )
        self.record_list.clearContents()
        self.record_list.setRowCount(0)
        selected_row = -1
        associations = self._workspace_associations()
        for index, record in enumerate(self._records):
            self.record_list.insertRow(index)
            company = record.input_snapshot.enterprise_name or "未填写企业名称"
            workspace = associations.get(record.record_id, "未关联项目")
            result = record.calculation_result
            total = format_amount(result.total_amount, result.total_unit)
            created = record.created_at.date().isoformat()
            values = (
                f"{company}\n{workspace}",
                period_label(record),
                standard_label(record.standard_id),
                total,
                status_label(record.status),
                created,
                "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value or f"记录编号：{record.record_id}")
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, record.record_id)
                item.setData(
                    Qt.ItemDataRole.AccessibleTextRole,
                    f"{self.record_list.horizontalHeaderItem(column).text()}：{value or record.record_id}",
                )
                self.record_list.setItem(index, column, item)
            status_badge = QLabel(status_label(record.status), self.record_list)
            status_badge.setObjectName("recordStatusBadge")
            warning = record.status is RecordStatus.COMPLETED_WITH_WARNINGS
            status_badge.setProperty("warning", "true" if warning else "false")
            status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_badge.setAccessibleName(f"记录状态：{status_label(record.status)}")
            self.record_list.setCellWidget(index, 4, status_badge)
            open_button = QPushButton("查看详情  ›", self.record_list)
            open_button.setObjectName("openRecordRowButton")
            open_button.setAccessibleName(f"打开 {company} 的核算记录详情")
            open_button.clicked.connect(
                lambda _checked=False, selected=index: self._open_record_row(selected)
            )
            self.record_list.setCellWidget(index, 6, open_button)
            self.record_list.setRowHeight(index, 62)
            for column in range(self.record_list.columnCount()):
                item = self.record_list.item(index, column)
                if item is not None:
                    item.setToolTip(
                        f"{item.text()}\n记录编号：{record.record_id}\n核算时间：{record.created_at.isoformat(timespec='seconds')}"
                    )
            if record.record_id == selected_before:
                selected_row = index
        self.result_count.setText(f"{len(self._records)} 条记录 / 共 {len(all_records)} 条 · 历史记录只读")
        self.delete_button.setEnabled(bool(self._records))
        self.export_word_button.setEnabled(bool(self._records))
        if self._records:
            self.record_list.setCurrentCell(selected_row if selected_row >= 0 else 0, 0)
            self.record_list.selectRow(selected_row if selected_row >= 0 else 0)
        else:
            self.record_list.insertRow(0)
            empty = QTableWidgetItem("没有符合条件的记录；可修改关键词或状态筛选。")
            empty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.record_list.setItem(0, 0, empty)
            self.record_list.setSpan(0, 0, 1, self.record_list.columnCount())
            self.record_list.setRowHeight(0, 80)
            self._clear_details("暂无符合条件的核算记录。")
        if self.view_stack.currentWidget() is self.detail_view:
            if any(record.record_id == self._detail_record_id for record in self._records):
                self._show_selected_record(self.record_list.currentRow())
            else:
                self._back_to_list()

    def open_record(self, record_id: str) -> bool:
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.status_filter.blockSignals(True)
        self.status_filter.setCurrentIndex(0)
        self.status_filter.blockSignals(False)
        self.refresh_records(select_record_id=record_id)
        row = self._row_for_record(record_id)
        found = row >= 0
        if found:
            self._open_record_row(row)
        return found

    def _row_for_record(self, record_id: str) -> int:
        for row in range(len(self._records)):
            item = self.record_list.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == record_id:
                return row
        return -1

    def _workspace_associations(self) -> dict[str, str]:
        associations: dict[str, str] = {}
        if self.project_service is None:
            return associations
        try:
            for workspace in self.project_service.list_all():
                for unit in workspace.units:
                    label = f"{workspace.name} / {unit.name}"
                    for record_id in unit.record_ids:
                        associations.setdefault(record_id, label)
        except Exception:
            return {}
        return associations

    def _back_to_list(self) -> None:
        self._detail_record_id = None
        self.view_stack.setCurrentWidget(self.list_view)
        self.record_list.setFocus()
        if self.page_title is not None:
            self.page_title.setText("核算记录")
        if self.page_description is not None:
            self.page_description.setText("搜索已保存的核算记录，查看历史结果和计算依据。")

    def _open_selected_record(self) -> None:
        row = self.record_list.currentRow()
        self._open_record_row(row)

    def _open_record_row(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        self.record_list.setCurrentCell(row, 0)
        self.record_list.selectRow(row)
        self._show_selected_record(row)
        self.detail_tabs.setCurrentIndex(0)
        if self.page_title is not None:
            self.page_title.setText("核算记录详情")
        if self.page_description is not None:
            self.page_description.setText("查看该条不可变记录的正式结果、输入快照和计算依据。")
        self.view_stack.setCurrentWidget(self.detail_view)
        self.back_to_records_button.setFocus()

    def _clear_details(self, message: str) -> None:
        self._detail_record_id = None
        self.summary_text.setPlainText(message)
        self.input_basis_text.setPlainText(message)

    def _show_selected_record(self, row: int) -> None:
        if row < 0 or row >= len(self._records):
            self._clear_details("请选择一条核算记录。")
            return
        record = self._records[row]
        self._detail_record_id = record.record_id
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
        qualification_state = states["qualification"]
        trace = values["trace"] if states["trace"] is SnapshotState.PRESENT else None
        reporting = values["reporting"] if states["reporting"] is SnapshotState.PRESENT else None
        raw = values["raw"] if states["raw"] is SnapshotState.PRESENT else None
        summary = summary_with_trace(
            record, values["qualification"], qualification_state, trace,
            association=self._workspace_association(record.record_id),
        )
        self.summary_text.setHtml(_record_summary_markup(summary))
        if states["raw"] is SnapshotState.LEGACY:
            report_text = "该历史记录生成时尚未保存完整业务输入；可查看以下已固化的核算汇总。\n\n" + build_report_view(record, None, trace, reporting)
        elif states["raw"] is SnapshotState.CORRUPT:
            report_text = "无法读取该历史记录的业务输入快照。\n\n" + build_report_view(record, None, trace, reporting)
        else:
            report_text = build_report_view(record, raw, trace, reporting)
        activity_text = build_activity_evidence_view(raw, reporting, states["reporting"])
        parameter_state = (
            SnapshotState.PRESENT if record.parameter_snapshots else
            SnapshotState.EMPTY if schema_available else SnapshotState.LEGACY
        )
        parameter_text = build_parameter_view(record, evidence_names_for(reporting), parameter_state)
        quality_text = build_quality_view(record, values["qualification"], qualification_state)
        professional = build_calculation_basis_view(
            record, trace=values["trace"], provenance=values["provenance"],
            states={
                "Trace 快照": states["trace"], "Provenance 快照": states["provenance"],
            },
        )
        if states["trace"] is SnapshotState.LEGACY:
            professional += "\n\n该记录生成时未保存完整计算过程快照。"
        professional += (
            f"\n实际输入快照（业务视图）：\n{_format_business_snapshot(values['raw'])}"
            f"\n报告信息与证据快照：\n{_format_reporting_snapshot(values['reporting'])}"
        )
        sections = (
            ("标准报告数据 B.1—B.9", report_text),
            ("活动数据与来源证据", activity_text),
            ("参数与因子来源", parameter_text),
            ("数据质量与提醒", quality_text),
            ("计算过程与来源链", professional),
        )
        self.input_basis_text.setPlainText("\n\n".join(
            f"{title}\n{'─' * 24}\n{content}" for title, content in sections
        ))
        self.detail_heading.setText(record.input_snapshot.enterprise_name or "核算记录详情")

    def _delete_selected(self) -> None:
        row = next((i for i, record in enumerate(self._records) if record.record_id == self._detail_record_id), -1)
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
        self._back_to_list()

    def _report_supplementary_dialog(self, record: AccountingRecord) -> dict[str, object] | None:
        if self.record_repository is None:
            return None
        return report_supplementary_dialog(self, self.record_repository, record)

    def _export_selected_report(self) -> None:
        row = next((i for i, record in enumerate(self._records) if record.record_id == self._detail_record_id), -1)
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
        self._chosen_workbook_path: Path | None = None
        self._preview_units: tuple[object, ...] = ()
        self._preview_workbook_warnings: tuple[object, ...] = ()
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
            "下载模板并选择工作簿，检查预览后保存为项目，再主动进行正式核算；预览不会生成正式记录。",
        )

        self.body_layout.setSpacing(12)

        template_section, template_layout = create_excel_import_section(
            "excelImportTemplateSection", "01 获取模板", self
        )
        template_row = QHBoxLayout()
        self.templateButton = QPushButton("下载附录 B 填报模板", template_section)
        self.templateButton.setObjectName("templateButton")
        self.templateButton.clicked.connect(self._download_template)
        template_row.addWidget(self.templateButton)
        template_row.addWidget(
            QLabel("使用 GB/T 32151.34—2024 附录 B 模板，填写 B.2～B.9 活动数据。", template_section),
            1,
        )
        template_layout.addLayout(template_row)
        self.body_layout.addWidget(template_section)

        file_section, file_layout = create_excel_import_section(
            "excelImportFileSection", "02 选择文件与核算信息", self
        )
        file_row = QHBoxLayout()
        self.selectFileButton = QPushButton("选择 Excel 文件", file_section)
        self.selectFileButton.setObjectName("selectFileButton")
        self.selectFileButton.clicked.connect(self._choose_workbook)
        file_row.addWidget(self.selectFileButton)
        self.selected_file_label = QLabel("尚未选择工作簿", file_section)
        self.selected_file_label.setObjectName("selectedExcelFile")
        self.selected_file_label.setWordWrap(True)
        self.selected_file_label.setAccessibleName("已选择的 Excel 工作簿")
        file_row.addWidget(self.selected_file_label, 1)
        self.preview_button = QPushButton("检查并预览", file_section)
        self.preview_button.setObjectName("previewExcelWorkbookButton")
        self.preview_button.clicked.connect(self._run_selected_workbook_preview)
        file_row.addWidget(self.preview_button)
        file_layout.addLayout(file_row)
        file_layout.addWidget(
            QLabel("以下信息用于新工作簿导入；打开已保存项目时，以项目中保存的信息为准。", file_section)
        )

        context_row = QHBoxLayout()
        context_row.addWidget(QLabel("企业名称（可选）", file_section))
        self.import_enterprise_name = QLineEdit(file_section)
        self.import_enterprise_name.setObjectName("importEnterpriseName")
        self.import_enterprise_name.setPlaceholderText("可留空")
        context_row.addWidget(self.import_enterprise_name, 2)
        context_row.addWidget(QLabel("期间类型", file_section))
        self.import_period_type = QComboBox(file_section)
        self.import_period_type.setObjectName("importPeriodType")
        self.import_period_type.addItem("请选择", None)
        self.import_period_type.addItem("年度", PeriodType.ANNUAL.value)
        self.import_period_type.addItem("月度", PeriodType.MONTHLY.value)
        self.import_period_type.addItem("自定义期间", PeriodType.CUSTOM.value)
        context_row.addWidget(self.import_period_type)
        context_row.addWidget(QLabel("开始日期", file_section))
        self.import_period_start = QLineEdit(file_section)
        self.import_period_start.setObjectName("importPeriodStart")
        self.import_period_start.setPlaceholderText("YYYY-MM-DD")
        self.import_period_start.setMaximumWidth(120)
        context_row.addWidget(self.import_period_start)
        context_row.addWidget(QLabel("结束日期", file_section))
        self.import_period_end = QLineEdit(file_section)
        self.import_period_end.setObjectName("importPeriodEnd")
        self.import_period_end.setPlaceholderText("YYYY-MM-DD")
        self.import_period_end.setMaximumWidth(120)
        context_row.addWidget(self.import_period_end)
        file_layout.addLayout(context_row)

        context_row_two = QHBoxLayout()
        context_row_two.addWidget(QLabel("电力地区", file_section))
        self.import_region = QComboBox(file_section)
        self.import_region.setObjectName("importRegion")
        self.import_region.addItem("全国（使用全国路径）", None)
        context_row_two.addWidget(self.import_region)
        self.import_boundary_confirmed = QCheckBox("我已确认本次核算边界", file_section)
        self.import_boundary_confirmed.setObjectName("importBoundaryConfirmed")
        context_row_two.addWidget(self.import_boundary_confirmed)
        context_row_two.addStretch(1)
        file_layout.addLayout(context_row_two)

        self.fuel_override_panel = QFrame(file_section)
        self.fuel_override_panel.setObjectName("fuelPathOverridePanel")
        self.fuel_override_layout = QVBoxLayout(self.fuel_override_panel)
        self.fuel_override_layout.setContentsMargins(0, 0, 0, 0)
        self.fuel_override_panel.hide()
        file_layout.addWidget(self.fuel_override_panel)

        self.import_period_type.currentIndexChanged.connect(self._refresh_import_regions)
        self.import_period_type.currentIndexChanged.connect(self._import_context_changed)
        self.import_period_start.editingFinished.connect(self._refresh_import_regions)
        self.import_period_end.editingFinished.connect(self._refresh_import_regions)
        self.import_period_start.textChanged.connect(self._import_context_changed)
        self.import_period_end.textChanged.connect(self._import_context_changed)
        self.import_enterprise_name.textChanged.connect(self._import_context_changed)
        self.import_region.currentIndexChanged.connect(self._import_context_changed)
        self.import_boundary_confirmed.stateChanged.connect(self._import_context_changed)
        self.body_layout.addWidget(file_section)

        preview_section, preview_layout = create_excel_import_section(
            "excelImportCheckSection", "03 数据检查与预览", self
        )
        self.preview_panel = ExcelImportPreviewPanel(preview_section)
        self.preview_panel.units.currentCellChanged.connect(self._preview_unit_selection_changed)
        self.preview_panel.set_details(
            "选择工作簿并检查后，这里会显示核算单元状态、需要修正的单元格位置和导入提醒。"
        )
        self.preview_text = self.preview_panel.details
        preview_layout.addWidget(self.preview_panel)
        self.body_layout.addWidget(preview_section)

        action_section, project_layout = create_excel_import_section(
            "excelImportActionSection", "04 保存项目、正式核算与结果", self
        )
        project_layout.addWidget(
            QLabel("预览不会生成正式记录。先保存有效核算单元为项目，再主动执行正式核算。", action_section)
        )
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("项目名称", action_section))
        self.project_name = QLineEdit(action_section)
        self.project_name.setObjectName("excelProjectName")
        self.project_name.setPlaceholderText("可为导入项目填写名称")
        name_row.addWidget(self.project_name, 1)
        self.save_project_button = QPushButton("保存有效核算单元为项目", action_section)
        self.save_project_button.setObjectName("saveExcelProjectButton")
        self.save_project_button.clicked.connect(self._save_preview_as_project)
        name_row.addWidget(self.save_project_button)
        project_layout.addLayout(name_row)

        saved_row = QHBoxLayout()
        saved_row.addWidget(QLabel("已保存项目", action_section))
        self.saved_projects = QComboBox(action_section)
        self.saved_projects.setObjectName("savedExcelProjects")
        saved_row.addWidget(self.saved_projects, 1)
        self.open_project_button = QPushButton("打开项目", action_section)
        self.open_project_button.setObjectName("openExcelProjectButton")
        self.open_project_button.clicked.connect(self._open_selected_project)
        saved_row.addWidget(self.open_project_button)
        project_layout.addLayout(saved_row)

        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("核算单元", action_section))
        self.unit_selector = QComboBox(action_section)
        self.unit_selector.setObjectName("canonicalUnitSelector")
        self.unit_selector.currentIndexChanged.connect(self._selected_unit_changed)
        unit_row.addWidget(self.unit_selector, 1)
        self.calculate_button = QPushButton("正式计算排放量", action_section)
        self.calculate_button.setObjectName("formalCalculateButton")
        self.calculate_button.clicked.connect(self._calculate_selected_unit)
        unit_row.addWidget(self.calculate_button)
        project_layout.addLayout(unit_row)

        record_row = QHBoxLayout()
        record_row.addWidget(QLabel("本单元正式记录", action_section))
        self.unit_record_selector = QComboBox(action_section)
        self.unit_record_selector.setObjectName("unitRecordSelector")
        record_row.addWidget(self.unit_record_selector, 1)
        self.open_record_button = QPushButton("查看核算记录", action_section)
        self.open_record_button.setObjectName("openUnitRecordButton")
        self.open_record_button.clicked.connect(self._open_selected_record)
        record_row.addWidget(self.open_record_button)
        project_layout.addLayout(record_row)

        self.status_label = QLabel(action_section)
        self.status_label.setObjectName("excelWorkflowStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("表格导入操作结果")
        project_layout.addWidget(self.status_label)
        self.body_layout.addWidget(action_section)
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
        target, _ = QFileDialog.getOpenFileName(
            self, "选择附录 B 工作簿", "", "Excel 工作簿 (*.xlsx)"
        )
        if target:
            self._select_workbook(Path(target))

    def _select_workbook(self, path: Path) -> None:
        self._detach_active_project_for_import()
        self._chosen_workbook_path = path
        self.selected_file_label.setText(path.name)
        self.selected_file_label.setToolTip(str(path))
        self.project_name.setText(path.stem)
        self.preview_panel.set_summary("已选择工作簿，请检查并预览。")
        self.preview_panel.set_units(())
        self.preview_panel.set_details(
            "尚未检查该工作簿。点击“检查并预览”后，会显示可保存单元、需修正项目和具体单元格位置。"
        )
        self.status_label.setText("工作簿已选择；尚未导入预览，也未生成项目或正式记录。")
        self._update_controls()

    def _run_selected_workbook_preview(self) -> None:
        if self._chosen_workbook_path is None:
            self.status_label.setText("请先选择 Excel 工作簿。")
            self.preview_panel.set_summary("尚未选择工作簿。", state="warning")
            return
        self._preview_workbook(self._chosen_workbook_path)

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
        self._preview_units = ()
        self._preview_workbook_warnings = ()
        self.preview_panel.set_summary("导入信息已变化，需要重新检查工作簿。", state="warning")
        self.preview_panel.set_units(())
        self.preview_panel.set_details(
            "核算期间、企业、地区或边界信息已修改；请重新检查并预览后再保存项目。"
        )
        self.status_label.setText("导入信息已修改；请重新检查并预览后再保存项目。")
        self._update_controls()

    def _detach_active_project_for_import(self) -> None:
        self._workspace = None
        self._selected_unit_id = None
        self._last_preview = None
        self._last_workbook_path = None
        self._chosen_workbook_path = None
        self._preview_context_key = None
        self._preview_units = ()
        self._preview_workbook_warnings = ()
        self.project_name.setReadOnly(False)
        blocker = QSignalBlocker(self.unit_selector)
        self.unit_selector.clear()
        del blocker
        self.unit_record_selector.clear()
        self._clear_fuel_override_panel()
        self.preview_panel.set_units(())
        self._update_controls()

    def _preview_workbook(self, path: Path, *, preserve_overrides: bool = False) -> None:
        same_source = path == self._last_workbook_path
        if not preserve_overrides or not same_source:
            self._fuel_path_overrides.clear()
            self._clear_fuel_override_panel()
        self._detach_active_project_for_import()
        self._chosen_workbook_path = path
        self.selected_file_label.setText(path.name)
        self.selected_file_label.setToolTip(str(path))
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
            self._chosen_workbook_path = path
            self._preview_units = ()
            self._preview_workbook_warnings = ()
            self.preview_panel.set_summary("工作簿检查未完成。", state="error")
            self.preview_panel.set_units(())
            self.preview_panel.set_details(f"无法预览该工作簿：{exc}")
            self.selected_file_label.setText(path.name)
            self.selected_file_label.setToolTip(str(path))
            self.status_label.setText(f"工作簿无法预览：{exc}")
            self._update_controls()
            return

        self._last_preview = preview
        self._last_workbook_path = path
        self._chosen_workbook_path = path
        self._preview_context_key = preview_context_key
        self.selected_file_label.setText(path.name)
        self.selected_file_label.setToolTip(str(path))
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
        field_label = getattr(message, "field_label", None)
        parts = [str(part) for part in (location, field_label) if part]
        if parts and not all(part in display for part in parts):
            return f"{' · '.join(parts)}：{display}"
        return display

    def _render_import_preview(self, preview) -> None:
        self._preview_units = tuple(preview.units)
        unit_warnings = tuple(message for unit in preview.units for message in unit.warnings)
        self._preview_workbook_warnings = tuple(
            message for message in preview.warnings if message not in unit_warnings
        )
        valid_count = sum(
            1 for unit in preview.units if unit.can_calculate and unit.input_value is not None
        )
        invalid_count = len(preview.units) - valid_count
        reminder_count = len(unit_warnings) + len(self._preview_workbook_warnings)
        self.preview_panel.set_summary(
            f"检查完成：{len(preview.units)} 个核算单元，{valid_count} 个可保存"
            f" · {invalid_count} 个需修正 · {reminder_count} 条提醒。",
            state="error" if invalid_count and not valid_count else (
                "warning" if invalid_count or reminder_count else "success"
            ),
        )
        type_names = {"WHOLE_SITE": "全厂", "PROCESS": "工序", "OTHER": "其他"}
        rows = []
        for unit in self._preview_units:
            unit_type = type_names.get(unit.unit_type.value, "核算单元")
            valid = unit.can_calculate and unit.input_value is not None
            total = (
                format_amount(unit.result.total_amount, unit.result.total_unit)
                if valid and unit.result is not None
                else "—"
            )
            rows.append((f"{unit.name}（{unit_type}）", "可保存" if valid else "需修正", total))
        self.preview_panel.set_units(rows, selectable=True)
        self._preview_unit_selection_changed(self.preview_panel.units.currentRow(), 0, -1, -1)

    def _preview_unit_selection_changed(self, current_row: int, *_args) -> None:
        if not self._preview_units:
            return
        row = current_row if 0 <= current_row < len(self._preview_units) else 0
        unit = self._preview_units[row]
        type_names = {"WHOLE_SITE": "全厂", "PROCESS": "工序", "OTHER": "其他"}
        lines = [
            f"核算单元：{unit.name}（{type_names.get(unit.unit_type.value, '核算单元')}）",
            f"模板版本：{self._last_preview.provenance.template_version if self._last_preview else '附录 B'}",
            f"本工作簿共 {len(self._preview_units)} 个核算单元。",
        ]
        valid = unit.can_calculate and unit.input_value is not None
        if valid and unit.result is not None:
            lines.append(
                "状态：有效，可保存为项目。预览排放总量："
                f"{format_amount(unit.result.total_amount, unit.result.total_unit)}"
            )
        else:
            lines.append("状态：需要修正；该单元不会保存到项目。")
        if unit.errors:
            lines.append("\n需要修正")
            lines.extend(f"- {self._format_import_message(item)}" for item in unit.errors)
        if unit.warnings:
            lines.append("\n单元提醒")
            lines.extend(f"- {self._format_import_message(item)}" for item in unit.warnings)
        if self._preview_workbook_warnings:
            lines.append("\n工作簿提醒")
            lines.extend(
                f"- {self._format_import_message(item)}"
                for item in self._preview_workbook_warnings
            )
        lines.append("\n预览不会保存项目或生成正式记录。")
        self.preview_panel.set_details("\n".join(lines))

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
        self._chosen_workbook_path = None
        self._preview_context_key = None
        self._preview_units = ()
        self._preview_workbook_warnings = ()
        self.selected_file_label.setText("已打开已保存项目；无需重新选择源工作簿")
        self.selected_file_label.setToolTip("")
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
            self.preview_panel.set_summary("请先打开包含核算单元的已保存项目。")
            self.preview_panel.set_units((), selectable=False)
            self.preview_panel.set_details("项目中的核算单元预览和关联记录会显示在这里。")
            return
        try:
            outcome = self.preview_use_case.calculate(unit.canonical_input)
        except Exception as exc:
            self.preview_panel.set_summary("已保存项目中的单元暂时无法预览。", state="error")
            self.preview_panel.set_units(((unit.name, "无法预览", "—"),), selectable=False)
            self.preview_panel.set_details(f"已保存项目中的单元无法预览：{exc}")
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
            total = format_amount(outcome.result.total_amount, outcome.result.total_unit)
            self.preview_panel.set_summary(
                "已保存项目 · 当前为非正式预览；正式记录仅在主动核算成功后新增。",
                state="success",
            )
            self.preview_panel.set_units(((unit.name, "可正式核算", total),), selectable=False)
            lines.append(f"预览排放总量：{total}")
        else:
            self.preview_panel.set_summary("当前项目单元需要修正，尚未生成正式记录。", state="warning")
            self.preview_panel.set_units(((unit.name, "需修正", "—"),), selectable=False)
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
        self.preview_button.setEnabled(
            self._chosen_workbook_path is not None and self._workspace is None
        )

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
    if route is AppRoute.SETTINGS:
        return SettingsPage(view_model, parent)

    placeholders = {
        AppRoute.STANDARDS: (
            "标准库",
            "查看已登记标准、适用范围与核算要求",
            "标准目录当前不可用。",
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
