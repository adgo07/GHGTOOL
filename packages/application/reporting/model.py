"""Immutable, presentation-independent report structure built from saved records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from decimal import ROUND_HALF_UP, localcontext
import re
from typing import Any, Mapping, Sequence

from packages.core.models import AccountingRecord
from packages.standards.carbon_material import (
    SOURCE_BAKING,
    SOURCE_CALCINATION,
    SOURCE_EXPORTED_ELECTRICITY,
    SOURCE_EXPORTED_HEAT,
    SOURCE_FGD,
    SOURCE_FUME,
    SOURCE_FUEL,
    SOURCE_GRAPHITIZATION,
    SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_PURCHASED_HEAT,
)

REPORT_SCHEMA_VERSION = "2.0.0"


@dataclass(frozen=True, slots=True)
class ReportCell:
    value: str = ""
    unit: str | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class ReportRow:
    cells: tuple[ReportCell, ...]
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReportTable:
    table_id: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[ReportRow, ...]
    landscape: bool = False
    header_rows: tuple[ReportRow, ...] = ()
    header_merges: tuple[tuple[int, int, int, int], ...] = ()
    body_merges: tuple[tuple[int, int, int, int], ...] = ()
    footnotes: tuple[str, ...] = ()
    column_weights: tuple[float, ...] = ()
    context_label: str | None = None


@dataclass(frozen=True, slots=True)
class ReportSection:
    section_id: str
    title: str
    tables: tuple[ReportTable, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportModel:
    schema_version: str
    record_id: str
    standard_name: str
    standard_version: str
    period_text: str
    prepared_on: str
    basic_information: tuple[tuple[str, str], ...]
    sections: tuple[ReportSection, ...]
    notices: tuple[str, ...]
    supplementary_note: str | None = None
    layout_id: str = ""
    template_sha256: str = ""


_SOURCE_NAMES = {
    "STANDARD_DEFAULT": "标准缺省值",
    "STANDARD_SPECIFIED": "标准规定值",
    "STANDARD_REQUIRED": "标准规定值",
    "OFFICIAL_PUBLISHED": "官方发布值",
    "ENTERPRISE_MEASURED": "企业实测值",
    "MEASURED": "实测值",
    "MANUAL_OVERRIDE": "用户手动填写",
    "USER_SELECTED_LIBRARY_VALUE": "从标准参数库选择",
    "SYSTEM_RECOMMENDED": "软件按标准推荐",
    "INTERPOLATED": "标准表内插值",
    "DERIVED": "依据输入数据计算",
    "CALCULATED": "计算值",
    "USER_DEFINED": "用户提供值",
    "USER_PROVIDED": "用户提供值",
    "CHEMICAL_CALCULATION": "化学计算",
    "METER": "计量器具",
    "PRODUCTION_LEDGER": "生产台账",
    "ENERGY_BILL": "能源账单",
    "TEST_REPORT": "检测报告",
    "STATEMENT": "结算单",
    "MANUAL": "手工录入",
    "OTHER": "其他来源",
}

_FUEL_NAMES = {
    "ANTHRACITE": "无烟煤", "BITUMINOUS_COAL": "烟煤", "LIGNITE": "褐煤",
    "CLEANED_COAL": "洗精煤", "OTHER_CLEANED_COAL": "其他洗煤", "BRIQUETTE": "型煤",
    "OTHER_COAL_PRODUCTS": "其他煤制品", "COKE": "焦炭", "PETROLEUM_COKE": "石油焦",
    "CRUDE_OIL": "原油", "FUEL_OIL": "燃料油", "GASOLINE": "汽油", "DIESEL": "柴油",
    "KEROSENE": "一般煤油", "LIQUEFIED_NATURAL_GAS": "液化天然气", "LIQUEFIED_PETROLEUM_GAS": "液化石油气",
    "NAPHTHA": "石脑油", "TAR": "焦油", "CRUDE_BENZENE": "粗苯", "NATURAL_GAS": "天然气",
    "BLAST_FURNACE_GAS": "高炉煤气", "CONVERTER_GAS": "转炉煤气", "COKE_OVEN_GAS": "焦炉煤气",
    "REFINERY_DRY_GAS": "炼厂干气", "OTHER_GAS": "其他煤气", "OTHER_PETROLEUM_PRODUCTS": "其他石油制品", "COAL": "具体煤种",
    "OTHER": "其他燃料",
}

_BUSINESS_SOURCE_NAMES = {
    SOURCE_FUEL: "化石燃料燃烧", SOURCE_CALCINATION: "原料煅烧", SOURCE_BAKING: "焙烧/炭化",
    SOURCE_GRAPHITIZATION: "石墨化", SOURCE_FUME: "烟气焚烧", SOURCE_FGD: "烟气脱硫",
    SOURCE_PURCHASED_ELECTRICITY: "购入电力", SOURCE_EXPORTED_ELECTRICITY: "输出电力",
    SOURCE_PURCHASED_HEAT: "购入热力", SOURCE_EXPORTED_HEAT: "输出热力",
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _entries(raw: object, key: str, legacy: str | None = None) -> tuple[Mapping[str, Any], ...]:
    data = _mapping(raw)
    value = data.get(key)
    if not isinstance(value, (list, tuple)) and legacy:
        item = data.get(legacy)
        value = (item,) if isinstance(item, Mapping) else ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return _text(value.get("value"))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _display_amount(value: object) -> str:
    """Round a frozen result for presentation without changing its saved Decimal."""

    if value in (None, ""):
        return ""
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception:
        return _text(value)
    if not decimal_value.is_finite():
        return _text(value)
    with localcontext() as context:
        context.prec = max(50, len(decimal_value.as_tuple().digits) + 8)
        return format(decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _enum(value: object, names: Mapping[str, str]) -> str:
    text = _text(value)
    if text in names:
        return names[text]
    if re.fullmatch(r"[A-Z][A-Z0-9_]*", text):
        return "其他"
    return text


def _source_label(value: object) -> str:
    text = _text(value)
    return {"user-input": "用户录入", "gbt_32151_34_2024": "GB/T 32151.34—2024"}.get(text, text)


def _snapshot_source(snapshot: Mapping[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    pieces = [_enum(snapshot.get("selection_method"), _SOURCE_NAMES)]
    for field in ("source_location", "source_version", "factor_year"):
        value = snapshot.get(field)
        if value not in (None, ""):
            pieces.append(_source_label(value))
    return "；".join(piece for piece in pieces if piece)


def _parameter_cell(raw_value: object, snapshots: Mapping[str, Mapping[str, Any]], detail_id: str) -> ReportCell:
    snapshot = snapshots.get(detail_id)
    if snapshot is not None:
        return ReportCell(_text(snapshot.get("value_used")), _text(snapshot.get("unit_used")) or None, _snapshot_source(snapshot))
    parameter = _mapping(raw_value)
    source_kind = _enum(parameter.get("source_kind"), _SOURCE_NAMES)
    source_parts = [source_kind, _text(parameter.get("source_location")), _source_label(parameter.get("source_version"))]
    return ReportCell(_text(parameter.get("value")), _text(parameter.get("unit")) or None, "；".join(item for item in source_parts if item) or None)


def _trace_steps(trace: object) -> tuple[Mapping[str, Any], ...]:
    values = _mapping(trace).get("formula_steps", ())
    return tuple(item for item in values if isinstance(item, Mapping)) if isinstance(values, (tuple, list)) else ()


def _step_for_instance(trace: object, source_id: str, instance_id: object) -> Mapping[str, Any] | None:
    target = _text(instance_id)
    return next((step for step in _trace_steps(trace) if step.get("emission_source_id") == source_id and _text(step.get("process_instance_id")) == target), None)


def _step_result(step: Mapping[str, Any] | None) -> str:
    return _display_amount(step.get("intermediate_result")) if step else ""


def _table(table_id: str, title: str, columns: Sequence[str], values: Sequence[Sequence[ReportCell | str]], *, landscape: bool = False) -> ReportTable:
    unit_names = {
        "ten_thousand_Nm3": "10⁴ Nm³", "tCO2": "tCO₂", "tCO2/GJ": "tCO₂/GJ", "tCO2/t": "tCO₂/t",
        "tC/10^4Nm3": "tC/10⁴ Nm³", "tC/t": "tC/t", "tCO2/MWh": "tCO₂/MWh",
        "GJ/GJ": "GJ/GJ", "Nm3/h": "Nm³/h", "mg/Nm3": "mg/Nm³", "C": "℃", "ratio": "比例值",
    }

    def cell(value: ReportCell | str) -> ReportCell:
        result = value if isinstance(value, ReportCell) else ReportCell(str(value))
        unit = unit_names.get(result.unit, result.unit) if result.unit else None
        return ReportCell(result.value, unit, result.source)

    rows = tuple(ReportRow(tuple(cell(value) for value in row)) for row in values)
    return ReportTable(table_id, title, tuple(columns), rows, landscape)


def _activity_source(value: object) -> str | None:
    activity = _mapping(value)
    parts = [
        _enum(activity.get("source_type"), _SOURCE_NAMES),
        _text(activity.get("source_reference")),
    ]
    return "；".join(part for part in parts if part) or None


def frozen_totals(record: AccountingRecord, trace: object) -> dict[str, str]:
    """Display the recorded ES/EI/ET; never derive a missing historical total."""
    aggregate = _mapping(_mapping(trace).get("aggregations"))
    lines = {line.line_id: line.amount for line in record.calculation_result.lines}
    result = {}
    for key, identifier in (("ES", "CAR-FLD-DIRECT-RESULT"), ("EI", "CAR-FLD-INDIRECT-RESULT"), ("ET", "CAR-FLD-TOTAL-RESULT")):
        value = aggregate.get(key)
        if value is None:
            value = lines.get(identifier)
        if value is None and key == "ET":
            value = record.calculation_result.total_amount
        result[key] = _display_amount(value)
    return result


def _snapshot_mapping(item) -> dict[str, Any]:
    return {
        "value_used": item.value_used, "unit_used": item.unit_used,
        "selection_method": item.selection_method.value, "source_location": item.source_location,
        "source_version": item.source_version, "source_id": item.source_id,
        "factor_year": item.factor_year,
    }


def build_report_model(
    record: AccountingRecord,
    raw_input_snapshot: object,
    trace_snapshot: object,
    provenance_snapshot: object,
    reporting_snapshot: object,
    report_qualification: object,
    *,
    supplementary_info: Mapping[str, object] | None = None,
    snapshot_schema_version: int = 1,
    today: date | None = None,
) -> ReportModel:
    """Build a report solely from the selected immutable record and its snapshots."""

    supplementary = dict(supplementary_info or {})
    reporting = _mapping(reporting_snapshot)
    raw = _mapping(raw_input_snapshot)
    trace = _mapping(trace_snapshot)
    parameter_snapshots: dict[str, Mapping[str, Any]] = {}
    for item in record.parameter_snapshots:
        if item.detail_id:
            parameter_snapshots[item.detail_id] = _snapshot_mapping(item)
    period = record.input_snapshot.period
    period_text = f"{period.start.isoformat()} 至 {period.end.isoformat()}"
    chosen = lambda key, fallback=None: _text(supplementary[key]) if key in supplementary else _text(fallback)
    enterprise_name = chosen("enterprise_name", record.input_snapshot.enterprise_name)
    prepared_on = chosen("prepared_on", (today or date.today()).isoformat())
    basic_rows = (
        ("报告主体", enterprise_name),
        ("企业名称", enterprise_name),
        ("统一社会信用代码", chosen("social_credit_code", reporting.get("social_credit_code"))),
        ("地址", chosen("address", reporting.get("address"))),
        ("企业性质", _text(reporting.get("organization_nature"))),
        ("所属行业", _text(reporting.get("industry"))),
        ("法定代表人", chosen("legal_representative", reporting.get("legal_representative"))),
        ("联系人", chosen("contact_person", reporting.get("contact_person"))),
        ("编制人", chosen("preparer_name", reporting.get("preparer_name"))),
        ("联系电话", chosen("phone", reporting.get("preparer_contact"))),
        ("核算期间", period_text),
        ("核算边界", _text(reporting.get("boundary_description")) or "按本次核算记录保存的边界确认"),
        ("主要产品及工艺", _text(reporting.get("products_and_process"))),
        ("排放源识别说明", _text(reporting.get("emission_source_identification"))),
        ("核算依据", "GB/T 32151.34—2024；" + _text(record.standard_version or "标准版本未记录")),
        ("编制日期", prepared_on),
        ("其他说明", chosen("supplementary_note", reporting.get("other_report_information"))),
    )

    from .appendix_b import build_appendix_b_sections, APPROVED_TEMPLATE_SHA256, LAYOUT_ID

    sections: list[ReportSection] = [
        ReportSection("basic", "企业及核算基本情况", (_table("basic-info", "报告基本信息", ("项目", "内容"), basic_rows),)),
        *build_appendix_b_sections(record, raw, trace, parameter_snapshots, enterprise_name=enterprise_name),
    ]

    evidence_rows: list[Sequence[ReportCell | str]] = []
    for evidence_type, collection in (("活动数据", "activity_evidence"), ("实测因子", "measured_factor_evidence")):
        for item in _entries(reporting, collection):
            source_names = "、".join(
                _BUSINESS_SOURCE_NAMES[source_id]
                for source_id in item.get("source_ids", ())
                if source_id in _BUSINESS_SOURCE_NAMES
            )
            applies_to = _text(item.get("applies_to"))
            if applies_to.startswith(("CAR-", "EVID-")):
                applies_to = ""
            details = (
                ("监测位置", "monitoring_location"), ("监测方法", "monitoring_method"),
                ("仪器", "instrument"), ("准确度", "accuracy"),
                ("记录频次", "recording_frequency"), ("采集时间", "acquisition_time"),
                ("采样方法", "sampling_method"), ("采样频次", "sampling_frequency"),
                ("检测方法", "testing_method"), ("检测频次", "testing_frequency"),
                ("引用标准", "referenced_standard"),
            )
            detail_text = "；".join(f"{label}：{_source_label(item[key]) if key == 'referenced_standard' else _text(item[key])}" for label, key in details if item.get(key) not in (None, ""))
            evidence_rows.append((
                ReportCell(evidence_type), ReportCell("；".join(value for value in (source_names, applies_to) if value)),
                ReportCell(_text(item.get("source_reference"))), ReportCell(detail_text),
                ReportCell(_text(item.get("note") or item.get("reason"))),
            ))
    if evidence_rows:
        sections.append(ReportSection("evidence", "数据来源及支撑信息", (_table(
            "evidence-register", "记录内保存的数据来源信息", ("信息类型", "适用业务", "来源/编号", "方法与质量信息", "说明"), evidence_rows, landscape=True,
        ),), ("本节内容来自该核算记录保存的报告信息快照。",)))

    notices: list[str] = []
    for problem in (*record.problems, *record.calculation_result.problems):
        if getattr(getattr(problem, "level", None), "value", "") == "WARNING" and getattr(problem, "message", ""):
            message = str(problem.message)
            if message not in notices:
                notices.append(message)
    if snapshot_schema_version == 0 or not raw:
        notices.append("本历史记录生成时未保存完整业务输入快照；本报告仅列出该记录已冻结的核算结果和可取得的信息。")
    qualification = _mapping(report_qualification)
    if qualification and not qualification.get("eligible", True):
        notices.append(_text(qualification.get("message")) or "该核算期间不满足年度报告资格要求。")
    if _mapping(provenance_snapshot) == {}:
        notices.append("历史来源快照不完整；报告未使用当前参数库补齐历史值。")
    return ReportModel(
        schema_version=REPORT_SCHEMA_VERSION,
        record_id=record.record_id,
        standard_name="GB/T 32151.34—2024 炭素材料生产企业温室气体排放核算报告",
        standard_version=record.standard_version or "未记录",
        period_text=period_text,
        prepared_on=prepared_on,
        basic_information=basic_rows,
        sections=tuple(sections),
        notices=tuple(notices),
        supplementary_note=_text(supplementary.get("supplementary_note")) or None,
        template_sha256=APPROVED_TEMPLATE_SHA256,
        layout_id=LAYOUT_ID,
    )


__all__ = ["REPORT_SCHEMA_VERSION", "ReportCell", "ReportModel", "ReportRow", "ReportSection", "ReportTable", "build_report_model"]
