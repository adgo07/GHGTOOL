"""Read-only, snapshot-backed presentation helpers for RS02 record views."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from enum import Enum
import re
from typing import Any

from packages.application.reporting.model import frozen_totals
from packages.core.models import AccountingRecord, PeriodType, RecordStatus
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
    verify_record_aggregation,
)


STANDARD_LABELS = {"gbt_32151_34_2024": "GB/T 32151.34—2024"}
SOURCE_LABELS = {
    SOURCE_FUEL: "化石燃料燃烧",
    SOURCE_CALCINATION: "原料煅烧",
    SOURCE_BAKING: "焙烧/炭化",
    SOURCE_GRAPHITIZATION: "石墨化",
    SOURCE_FUME: "烟气焚烧治理",
    SOURCE_FGD: "烟气脱硫净化",
    SOURCE_PURCHASED_ELECTRICITY: "购入电力",
    SOURCE_EXPORTED_ELECTRICITY: "输出电力",
    SOURCE_PURCHASED_HEAT: "购入热力",
    SOURCE_EXPORTED_HEAT: "输出热力",
}
SOURCE_TOTAL_KEYS = {
    SOURCE_FUEL: "fuel",
    SOURCE_CALCINATION: "calcination",
    SOURCE_BAKING: "baking",
    SOURCE_GRAPHITIZATION: "graphitization",
    SOURCE_FUME: None,
    SOURCE_FGD: None,
    SOURCE_PURCHASED_ELECTRICITY: "purchased_electricity",
    SOURCE_EXPORTED_ELECTRICITY: "exported_electricity",
    SOURCE_PURCHASED_HEAT: "purchased_heat",
    SOURCE_EXPORTED_HEAT: "exported_heat",
}
SOURCE_ROWS = (
    ("fuel", "化石燃料燃烧", SOURCE_FUEL, "fuel_inputs", "fuel_id", "燃料"),
    ("calcination", "原料煅烧", SOURCE_CALCINATION, "calcinations", "instance_id", "过程"),
    ("baking", "焙烧/炭化", SOURCE_BAKING, "bakings", "instance_id", "过程"),
    ("graphitization", "石墨化", SOURCE_GRAPHITIZATION, "graphitizations", "instance_id", "过程"),
    ("fume", "烟气焚烧治理", SOURCE_FUME, "fume_incinerations", "instance_id", "设施"),
    ("fgd", "烟气脱硫净化", SOURCE_FGD, "fgd_units", "instance_id", "设施"),
    ("purchased_electricity", "购入电力", SOURCE_PURCHASED_ELECTRICITY, "electricity_details", "detail_id", "来源"),
    ("exported_electricity", "输出电力", SOURCE_EXPORTED_ELECTRICITY, "exported_electricity", "line_id", "来源"),
    ("purchased_heat", "购入热力", SOURCE_PURCHASED_HEAT, "purchased_heat", "line_id", "来源"),
    ("exported_heat", "输出热力", SOURCE_EXPORTED_HEAT, "exported_heat", "line_id", "来源"),
)

FUEL_TYPES = {
    "ANTHRACITE": "无烟煤", "BITUMINOUS_COAL": "烟煤", "LIGNITE": "褐煤",
    "CLEANED_COAL": "洗精煤", "OTHER_CLEANED_COAL": "其他洗煤", "BRIQUETTE": "型煤",
    "OTHER_COAL_PRODUCTS": "其他煤制品", "COKE": "焦炭", "PETROLEUM_COKE": "石油焦",
    "CRUDE_OIL": "原油", "FUEL_OIL": "燃料油", "GASOLINE": "汽油", "DIESEL": "柴油",
    "KEROSENE": "一般煤油", "LIQUEFIED_NATURAL_GAS": "液化天然气",
    "LIQUEFIED_PETROLEUM_GAS": "液化石油气", "NAPHTHA": "石脑油", "TAR": "焦油",
    "CRUDE_BENZENE": "粗苯", "OTHER_PETROLEUM_PRODUCTS": "其他石油制品",
    "NATURAL_GAS": "天然气", "BLAST_FURNACE_GAS": "高炉煤气", "CONVERTER_GAS": "转炉煤气",
    "COKE_OVEN_GAS": "焦炉煤气", "REFINERY_DRY_GAS": "炼厂干气", "OTHER_GAS": "其他煤气",
    "COAL": "煤（历史输入未细分）", "OTHER": "其他燃料（按历史输入记录）",
}
PATH_LABELS = {"MASS": "质量路径", "VOLUME": "体积路径", "HEAT": "热量路径"}
SOURCE_KIND_LABELS = {
    "STANDARD_DEFAULT": "标准缺省值", "STANDARD_SPECIFIED": "标准规定值", "MEASURED": "企业实测值",
    "CALCULATED": "计算值", "OFFICIAL_PUBLISHED": "官方发布值", "USER_DEFINED": "用户指定值",
    "PROJECT_SPECIFIED": "项目指定值",
}
SOURCE_TYPE_LABELS = {
    "MANUAL": "手工录入", "METER": "计量数据", "MEASURED": "实测数据",
    "CALCULATED": "计算数据", "OFFICIAL": "官方数据", "PROXY": "替代数据",
}
SELECTION_LABELS = {
    "SYSTEM_RECOMMENDED": "系统推荐", "STANDARD_REQUIRED": "标准要求",
    "USER_SELECTED_LIBRARY_VALUE": "用户选择目录值", "ENTERPRISE_MEASURED": "企业实测",
    "MANUAL_OVERRIDE": "人工指定", "INTERPOLATED": "插值结果", "DERIVED": "推导值",
}
PERIOD_LABELS = {PeriodType.ANNUAL: "年度", PeriodType.MONTHLY: "月度", PeriodType.CUSTOM: "自定义期间"}
STATUS_LABELS = {
    RecordStatus.COMPLETED: "已完成",
    RecordStatus.COMPLETED_WITH_WARNINGS: "已完成（含提醒）",
}

REPORT_FIELD_LABELS = {
    "activity": "活动数据", "path": "计量路径", "lower_heating_value": "低位发热量", "carbon_content": "单位热值含碳量/含碳量",
    "oxidation_rate": "碳氧化率", "gc": "待煅烧原料总量", "wfc": "原料固定碳含量",
    "cc": "煅后料产量", "ucc": "欠烧煅料回收量", "du": "炭粉尘排放量",
    "wfc_c": "煅后料固定碳含量", "wvar": "原料挥发分含量", "wvar_c": "煅后料挥发分含量",
    "k1": "挥发分折算参数", "bpm": "填充料消耗量", "bpmfc": "填充料固定碳含量",
    "bg": "待焙烧/炭化品总量", "bgfc": "待焙烧品固定碳含量", "bwt": "粉尘、碎屑及副产品碳输出量",
    "bp": "焙烧/炭化品产量", "bpfc": "产品固定碳含量", "bpmvar": "填充料挥发分含量",
    "bgvar": "待焙烧品挥发分含量", "k2": "挥发分折算参数", "gpm": "保温料和电阻料消耗量",
    "gpmfc": "保温料和电阻料固定碳含量", "gta": "待石墨化品总量", "gtafc": "待石墨化品固定碳含量",
    "gwt": "粉尘、碎屑、残块及副产品碳输出量", "gp": "石墨化产品产量", "gpfc": "石墨化产品固定碳含量",
    "gpmvar": "保温料和电阻料挥发分含量", "k3": "挥发分折算参数", "q": "进入焚烧炉烟气流量",
    "qvar": "沥青烟焦油含量", "hm": "沥青烟焦油低位发热量", "fch": "沥青烟焦油单位热值含碳量",
    "fox": "碳氧化率", "duration": "报告期时长", "components": "碳酸盐组分",
    "amount": "消耗量", "carbonate_fraction": "碳酸盐组分含量", "emission_factor": "二氧化碳质量分数",
    "conversion_rate": "转化率", "carbonate_type": "碳酸盐种类", "electricity_amount": "电量",
    "electricity_unit": "电量单位", "acquisition_mode": "取得方式", "attribute": "电力属性",
    "proof_type": "证明类型", "proof_status": "证明状态", "steam_kind": "蒸汽类型",
    "enthalpy": "蒸汽焓值", "pressure_mpa": "蒸汽压力", "temperature_c": "蒸汽温度",
    "unit": "单位",
}

INSTANCE_FIELDS = {
    "instance_id", "fuel_id", "detail_id", "line_id", "input_id", "enterprise_id",
    "evidence_ref_ids", "source_id", "source_version", "parameter_id", "factor_id",
    "factor_year", "source_location", "detail_id", "selection_reason", "formula_id",
}


class SnapshotState(str, Enum):
    PRESENT = "PRESENT"
    EMPTY = "EMPTY"
    LEGACY = "LEGACY"
    CORRUPT = "CORRUPT"


SNAPSHOT_STATE_LABELS = {
    SnapshotState.PRESENT: "已保存",
    SnapshotState.EMPTY: "本次未填写 / 未记录。",
    SnapshotState.LEGACY: "该历史记录生成时尚未保存此信息。",
    SnapshotState.CORRUPT: "无法读取该历史信息。",
}


def standard_label(standard_id: str) -> str:
    return STANDARD_LABELS.get(standard_id, "标准名称未记录")


def period_label(record: AccountingRecord) -> str:
    period = record.input_snapshot.period
    if period.period_type is PeriodType.ANNUAL:
        return f"{period.start.year}年度"
    if period.period_type is PeriodType.MONTHLY:
        return f"{period.start.year}年{period.start.month:02d}月"
    return f"自定义期间 {period.start.isoformat()} 至 {period.end.isoformat()}"


def status_label(status: RecordStatus) -> str:
    return STATUS_LABELS.get(status, "已完成")


def format_amount(value: object, unit: str = "tCO₂") -> str:
    unit = {"tCO2": "tCO₂"}.get(unit, unit)
    if value is None:
        return "历史记录未保存该分项"
    try:
        amount = Decimal(str(value))
        places = 2 if amount.is_zero() else max(2, -amount.adjusted() + 2)
        if places > 12:
            number = f"{amount:.3E}"
        else:
            with localcontext() as context:
                context.prec = max(28, len(amount.as_tuple().digits) + places + 4)
                shown = amount.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
            number = f"{shown:,.2f}" if places == 2 else f"{shown:,.{places}f}".rstrip("0").rstrip(".")
    except (InvalidOperation, ValueError):
        number = str(value)
    return f"{number} {unit}".strip()


def _has_content(value: object, *, omit: frozenset[str] = frozenset()) -> bool:
    if value is None or value == "" or value == [] or value == {}:
        return False
    if isinstance(value, Mapping):
        return any(_has_content(item, omit=omit) for key, item in value.items() if str(key) not in omit)
    if isinstance(value, (list, tuple)):
        return any(_has_content(item, omit=omit) for item in value)
    return True


def snapshot_state(value: object, schema_available: bool, *, read_error: bool = False) -> SnapshotState:
    if read_error:
        return SnapshotState.CORRUPT
    if value is None:
        return SnapshotState.EMPTY if schema_available else SnapshotState.LEGACY
    if not isinstance(value, Mapping):
        return SnapshotState.CORRUPT
    if not _has_content(value):
        return SnapshotState.EMPTY if schema_available else SnapshotState.LEGACY
    return SnapshotState.PRESENT


def snapshot_state_text(value: object, schema_available: bool, *, read_error: bool = False) -> str:
    state = snapshot_state(value, schema_available, read_error=read_error)
    return SNAPSHOT_STATE_LABELS[state]


def _plain_value(value: object, evidence_names: Mapping[str, str] | None = None) -> str:
    if isinstance(value, Mapping):
        if "value" in value and "unit" in value:
            value_unit = {"tCO2": "tCO₂"}.get(str(value.get("unit")), value.get("unit"))
            result = f"{value.get('value')} {value_unit}".strip()
            source_kind = value.get("source_kind")
            source_type = value.get("source_type")
            extras = []
            if source_kind:
                extras.append(SOURCE_KIND_LABELS.get(str(source_kind), "已记录来源类型"))
            if source_type:
                extras.append(SOURCE_TYPE_LABELS.get(str(source_type), "已记录数据来源"))
            if value.get("source_reference"):
                extras.append(f"来源说明：{value['source_reference']}")
            evidence_ids = value.get("evidence_ref_ids", ())
            if isinstance(evidence_ids, (tuple, list)) and evidence_ids:
                names = [
                    (evidence_names or {}).get(str(item), "相关来源证据")
                    for item in evidence_ids
                ]
                extras.append("引用：" + "、".join(dict.fromkeys(names)))
            return "；".join((result, *extras))
        if "evidence_id" in value:
            return ""
        return "；".join(
            f"{REPORT_FIELD_LABELS.get(str(key), '相关信息')}：{_plain_value(item, evidence_names)}"
            for key, item in value.items()
            if str(key) not in INSTANCE_FIELDS and item not in (None, "", [], {})
        )
    if isinstance(value, (tuple, list)):
        return "；".join(_plain_value(item, evidence_names) for item in value if item not in (None, "", [], {}))
    if isinstance(value, bool):
        return "是" if value else "否"
    rendered = str(value)
    return SOURCE_KIND_LABELS.get(rendered, SOURCE_TYPE_LABELS.get(rendered, rendered))


def _evidence_names(reporting: object) -> dict[str, str]:
    result: dict[str, str] = {}
    if not isinstance(reporting, Mapping):
        return result
    index = 0
    for key in ("activity_evidence", "measured_factor_evidence"):
        entries = reporting.get(key, ())
        if not isinstance(entries, (tuple, list)):
            continue
        for entry in entries:
            if isinstance(entry, Mapping) and entry.get("evidence_id"):
                index += 1
                result[str(entry["evidence_id"])] = f"证据{index}"
    return result


def evidence_names_for(reporting: object) -> dict[str, str]:
    """Return business labels for evidence references saved with one record."""

    return _evidence_names(reporting)


def _raw_items(raw: object, plural: str, legacy: str | None = None) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, Mapping):
        return ()
    entries = raw.get(plural)
    if not isinstance(entries, (tuple, list)) and legacy:
        single = raw.get(legacy)
        entries = [single] if isinstance(single, Mapping) else []
    if not isinstance(entries, (tuple, list)):
        return ()
    return tuple(item for item in entries if isinstance(item, Mapping))


def _calculation_snapshot(record: AccountingRecord) -> dict[str, object]:
    return {
        "lines": [
            {
                "line_id": line.line_id,
                "emission_source_id": line.emission_source_id,
                "amount": str(line.amount),
                "unit": line.unit,
            }
            for line in record.calculation_result.lines
        ],
        "total_amount": str(record.calculation_result.total_amount),
    }


def aggregation_errors(record: AccountingRecord, trace: object) -> tuple[str, ...]:
    if not isinstance(trace, Mapping):
        return ("历史记录没有可核验的计算过程快照",)
    return verify_record_aggregation(trace, _calculation_snapshot(record))


def _trace_steps(trace: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(trace, Mapping):
        return ()
    steps = trace.get("formula_steps", ())
    return tuple(step for step in steps if isinstance(step, Mapping)) if isinstance(steps, (tuple, list)) else ()


def _standard_basis(trace: object, source_ids: tuple[str, ...], fallback: str) -> str:
    references: list[str] = []
    for step in _trace_steps(trace):
        if step.get("emission_source_id") not in source_ids:
            continue
        standard = str(step.get("standard_location") or "").strip()
        mapping = str(step.get("mapping_location") or "").strip()
        reference = "；".join(item for item in (standard, mapping) if item)
        if reference and reference not in references:
            references.append(reference)
    return "；".join(references) if references else fallback


def _source_entries(raw: object, collection: str, identity_key: str, legacy: str | None = None) -> tuple[Mapping[str, Any], ...]:
    return _raw_items(raw, collection, legacy)


def _instance_index(entries: tuple[Mapping[str, Any], ...], identity_key: str, instance_id: str | None) -> int | None:
    for index, item in enumerate(entries, 1):
        if instance_id is not None and str(item.get(identity_key, "")) == str(instance_id):
            return index
    return None


def _instance_display(label: str, index: int | None, count: int) -> str:
    if index is None:
        return label
    return f"{label}{index}" if count > 1 else label


def _steps_by_trace(trace: object) -> dict[str, Mapping[str, Any]]:
    return {str(step.get("trace_id")): step for step in _trace_steps(trace) if step.get("trace_id") is not None}


def _step_for_line(line: object, steps: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    line_id = str(getattr(line, "line_id", ""))
    direct = steps.get(line_id)
    if direct is not None:
        return direct
    suffix = line_id.rsplit(".", 1)[-1]
    return steps.get(suffix)


def _line_for_instance(record: AccountingRecord, source_id: str, instance_id: str | None, steps: Mapping[str, Mapping[str, Any]]) -> object | None:
    for line in record.calculation_result.lines:
        if line.emission_source_id != source_id:
            continue
        step = _step_for_line(line, steps)
        if step is not None and str(step.get("process_instance_id") or "") == str(instance_id or ""):
            return line
        if instance_id and line.line_id.endswith("." + str(instance_id)):
            return line
        if instance_id and line.line_id == str(instance_id):
            return line
    return None


def _line_result_text(line: object | None) -> str:
    if line is None:
        return "结果分项未保存"
    return format_amount(getattr(line, "amount"), str(getattr(line, "unit", "tCO₂")))


def _format_report_item(
    item: Mapping[str, Any],
    field_names: tuple[str, ...],
    evidence_names: Mapping[str, str],
) -> list[str]:
    lines: list[str] = []
    for key in field_names:
        value = item.get(key)
        if value in (None, "", [], {}):
            continue
        label = REPORT_FIELD_LABELS.get(key, "相关信息")
        if key == "fuel_type":
            rendered = FUEL_TYPES.get(str(value), "历史燃料类别未记录")
        elif key == "path":
            rendered = PATH_LABELS.get(str(value), "历史路径未记录")
        elif key in {"steam_kind", "acquisition_mode", "attribute", "proof_type", "proof_status"}:
            rendered = _plain_value(value, evidence_names)
        else:
            rendered = _plain_value(value, evidence_names)
        if rendered:
            lines.append(f"{label}：{rendered}")
    return lines


def _format_report_group(
    *,
    title: str,
    raw: object,
    collection: str,
    identity_key: str,
    instance_word: str,
    field_names: tuple[str, ...],
    source_id: str,
    trace: object,
    reporting: object,
    record: AccountingRecord,
    fallback_basis: str,
    legacy: str | None = None,
) -> list[str]:
    entries = _source_entries(raw, collection, identity_key, legacy)
    if not entries:
        return [f"{title}：本次未记录。"]
    evidence_names = _evidence_names(reporting)
    steps = _steps_by_trace(trace)
    output = [title]
    for ordinal, item in enumerate(entries, 1):
        instance_id = str(item.get(identity_key, "")) or None
        label = f"{instance_word}{ordinal}" if len(entries) > 1 else f"本条{instance_word}"
        output.append(f"- {label}")
        output.extend(f"  {line}" for line in _format_report_item(item, field_names, evidence_names))
        result_line = _line_for_instance(record, source_id, instance_id, steps)
        output.append(f"  对应排放结果：{_line_result_text(result_line)}")
    output.append("  标准依据：" + _standard_basis(trace, (source_id,), fallback_basis))
    return output


def _format_components(item: Mapping[str, Any], evidence_names: Mapping[str, str]) -> list[str]:
    components = item.get("components", ())
    if not isinstance(components, (tuple, list)) or not components:
        return ["  碳酸盐组分：本次未记录。"]
    lines = []
    for index, component in enumerate(components, 1):
        if not isinstance(component, Mapping):
            continue
        values = _format_report_item(
            component,
            ("carbonate_type", "amount", "carbonate_fraction", "emission_factor", "conversion_rate"),
            evidence_names,
        )
        lines.append(f"  组分{index}：" + "；".join(values))
    return lines


def _trace_source_subtotals(trace: object) -> Mapping[str, Any]:
    if not isinstance(trace, Mapping):
        return {}
    values = trace.get("source_subtotals", {})
    return values if isinstance(values, Mapping) else {}


def _b1_report(record: AccountingRecord, raw: object, trace: object) -> list[str]:
    subtotals = _trace_source_subtotals(trace)
    lines = ["B.1 排放量汇总与主要排放源分项"]
    totals = frozen_totals(record, trace)
    direct = totals.get("ES") or None
    indirect = totals.get("EI") or None
    total = totals.get("ET") or None
    lines.extend((
        f"- 不包括购入和输出电力、热力影响的直接排放量：{format_amount(direct)}",
        f"- 购入/输出能源对应的净间接排放量：{format_amount(indirect)}",
        f"- 包括购入和输出能源影响后的温室气体排放总量：{format_amount(total)}",
        "主要排放源分项：",
    ))
    subtotal_labels = (
        ("fuel", "化石燃料燃烧"), ("calcination", "原料煅烧"), ("baking", "焙烧/炭化"),
        ("graphitization", "石墨化"), ("gas_control", "烟气治理"),
        ("purchased_electricity", "购入电力"), ("exported_electricity", "输出电力抵扣"),
        ("purchased_heat", "购入热力"), ("exported_heat", "输出热力抵扣"),
    )
    for key, label in subtotal_labels:
        value = subtotals.get(key)
        lines.append(f"  - {label}：{format_amount(value) if value is not None else '历史记录未保存该分项'}")

    steps = _steps_by_trace(trace)
    if isinstance(raw, Mapping):
        for _, label, source_id, collection, identity_key, instance_word in SOURCE_ROWS:
            entries = _source_entries(raw, collection, identity_key)
            if len(entries) < 2:
                continue
            for index, item in enumerate(entries, 1):
                instance_id = str(item.get(identity_key, "")) or None
                amount = _line_for_instance(record, source_id, instance_id, steps)
                lines.append(f"  - {label} {instance_word}{index}：{_line_result_text(amount)}")
    errors = aggregation_errors(record, trace)
    lines.append("历史汇总核对：" + ("通过（汇总与核算分项一致）" if not errors else "无法通过；" + "；".join(errors)))
    lines.append("标准依据：" + _standard_basis(
        trace,
        (SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING, SOURCE_GRAPHITIZATION, SOURCE_FUME,
         SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY, SOURCE_PURCHASED_HEAT,
         SOURCE_EXPORTED_ELECTRICITY, SOURCE_EXPORTED_HEAT),
        "GB/T 32151.34—2024 §5.2.7、§7.3；冻结 Mapping §11、§13.1",
    ))
    return lines


def build_report_view(record: AccountingRecord, raw: object, trace: object, reporting: object) -> str:
    """Build the B.1-B.9 business view only from the selected record's snapshots."""

    evidence_names = _evidence_names(reporting)
    output = _b1_report(record, raw, trace)
    output.extend(("", "B.2 化石燃料活动数据和排放因子"))
    output.extend(_format_report_group(
        title="化石燃料来源", raw=raw, collection="fuel_inputs", identity_key="fuel_id", instance_word="燃料",
        field_names=("fuel_type", "path", "activity", "lower_heating_value", "carbon_content", "oxidation_rate"),
        source_id=SOURCE_FUEL, trace=trace, reporting=reporting, record=record,
        fallback_basis="GB/T 32151.34—2024 §5.2.1、附录C.1、附录B.2；冻结 Mapping §9.2、§13.1",
    ))
    output.extend(("", "B.3 原料煅烧过程"))
    output.extend(_format_report_group(
        title="煅烧过程", raw=raw, collection="calcinations", identity_key="instance_id", instance_word="过程",
        field_names=("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c", "k1"),
        source_id=SOURCE_CALCINATION, trace=trace, reporting=reporting, record=record,
        fallback_basis="GB/T 32151.34—2024 §5.2.2、附录B.3；冻结 Mapping §13.1",
        legacy="calcination",
    ))
    output.extend(("", "B.4 炭素制品焙烧/炭化过程"))
    output.extend(_format_report_group(
        title="焙烧/炭化过程", raw=raw, collection="bakings", identity_key="instance_id", instance_word="过程",
        field_names=("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar", "k2"),
        source_id=SOURCE_BAKING, trace=trace, reporting=reporting, record=record,
        fallback_basis="GB/T 32151.34—2024 §5.2.3、附录B.4；冻结 Mapping §13.1",
        legacy="baking",
    ))
    output.extend(("", "B.5 炭素制品石墨化过程"))
    output.extend(_format_report_group(
        title="石墨化过程", raw=raw, collection="graphitizations", identity_key="instance_id", instance_word="过程",
        field_names=("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar", "k3"),
        source_id=SOURCE_GRAPHITIZATION, trace=trace, reporting=reporting, record=record,
        fallback_basis="GB/T 32151.34—2024 §5.2.4、附录B.5；冻结 Mapping §13.1",
        legacy="graphitization",
    ))
    output.extend(("", "B.6 烟气焚烧治理过程"))
    output.extend(_format_report_group(
        title="烟气焚烧设施", raw=raw, collection="fume_incinerations", identity_key="instance_id", instance_word="设施",
        field_names=("q", "qvar", "hm", "fch", "fox", "duration"),
        source_id=SOURCE_FUME, trace=trace, reporting=reporting, record=record,
        fallback_basis="GB/T 32151.34—2024 §5.2.5.1、附录B.6；冻结 Mapping §13.1",
        legacy="fume_incineration",
    ))
    output.extend(("", "B.7 烟气脱硫净化过程"))
    entries = _source_entries(raw, "fgd_units", "instance_id", "fgd")
    if entries:
        output.append("脱硫设施")
        steps = _steps_by_trace(trace)
        for index, item in enumerate(entries, 1):
            label = f"设施{index}" if len(entries) > 1 else "本条设施"
            output.append(f"- {label}")
            output.extend(_format_components(item, evidence_names))
            output.append(f"  对应排放结果：{_line_result_text(_line_for_instance(record, SOURCE_FGD, str(item.get('instance_id') or ''), steps))}")
        output.append("  标准依据：" + _standard_basis(trace, (SOURCE_FGD,), "GB/T 32151.34—2024 §5.2.5.2、附录C.2、附录B.7；冻结 Mapping §9.3、§13.1"))
    else:
        output.append("烟气脱硫净化：本次未记录。")
    output.extend(("", "B.8 购入和输出电力"))
    for title, collection, source_id, identity_key in (
        ("购入电力来源", "electricity_details", SOURCE_PURCHASED_ELECTRICITY, "detail_id"),
        ("输出电力来源", "exported_electricity", SOURCE_EXPORTED_ELECTRICITY, "line_id"),
    ):
        output.extend(_format_report_group(
            title=title, raw=raw, collection=collection, identity_key=identity_key, instance_word="来源",
            field_names=("electricity_amount", "electricity_unit", "amount", "unit", "acquisition_mode", "attribute", "proof_type", "proof_status"),
            source_id=source_id, trace=trace, reporting=reporting, record=record,
            fallback_basis="GB/T 32151.34—2024 §5.2.6.1、附录B.8；冻结 Mapping §13.1",
        ))
    output.extend(("", "B.9 购入和输出热力"))
    for title, collection, source_id in (
        ("购入热力来源", "purchased_heat", SOURCE_PURCHASED_HEAT),
        ("输出热力来源", "exported_heat", SOURCE_EXPORTED_HEAT),
    ):
        output.extend(_format_report_group(
            title=title, raw=raw, collection=collection, identity_key="line_id", instance_word="来源",
            field_names=("amount", "unit", "enthalpy", "steam_kind", "pressure_mpa", "temperature_c"),
            source_id=source_id, trace=trace, reporting=reporting, record=record,
            fallback_basis="GB/T 32151.34—2024 §5.2.6.2、附录B.9；冻结 Mapping §9.4–§9.6、§13.1",
        ))
    if not isinstance(raw, Mapping):
        output.append("\n本历史记录未保存 B.2-B.9 所需的完整输入快照。")
    return "\n".join(output)


def _reporting_value(value: object) -> str:
    if value in (None, "", [], {}):
        return "未填写"
    return str(value)


def build_activity_evidence_view(raw: object, reporting: object, reporting_state: SnapshotState) -> str:
    output = ["活动数据与来源证据", "各业务活动数据按 B.2—B.9 分类展示在“标准报告数据”页；此处集中显示本次记录固定的证据块，避免重复展开。"]
    if reporting_state is SnapshotState.LEGACY:
        return "\n".join((*output, SNAPSHOT_STATE_LABELS[SnapshotState.LEGACY]))
    if reporting_state is SnapshotState.CORRUPT:
        return "\n".join((*output, SNAPSHOT_STATE_LABELS[SnapshotState.CORRUPT]))
    if not isinstance(reporting, Mapping):
        return "\n".join((*output, SNAPSHOT_STATE_LABELS[SnapshotState.EMPTY]))
    evidence_found = False
    evidence_names = _evidence_names(reporting)
    for key, title in (
        ("activity_evidence", "活动数据来源证据"),
        ("measured_factor_evidence", "实测因子来源证据"),
    ):
        items = reporting.get(key, ())
        if not isinstance(items, (tuple, list)) or not items:
            continue
        output.append(f"\n{title}")
        for item in items:
            if not isinstance(item, Mapping):
                continue
            evidence_found = True
            evidence_id = str(item.get("evidence_id") or "")
            evidence_name = evidence_names.get(evidence_id, "来源证据")
            output.append(f"{evidence_name}：{_reporting_value(item.get('applies_to'))}")
            for field, label in (
                ("source_reference", "来源/报告定位"), ("monitoring_location", "监测地点"),
                ("monitoring_method", "监测方法"), ("instrument", "仪器/计量设备"),
                ("accuracy", "设备精度"), ("recording_frequency", "记录频次"),
                ("acquisition_time", "数据取得时间"), ("sampling_method", "取样方法"),
                ("sampling_frequency", "取样频次"), ("testing_method", "检测方法"),
                ("testing_frequency", "检测频次"), ("referenced_standard", "依据标准"),
                ("reason", "采用理由/说明"), ("note", "补充说明"),
            ):
                value = item.get(field)
                if value not in (None, "", [], {}):
                    output.append(f"  {label}：{value}")
            source_ids = item.get("source_ids", ())
            if isinstance(source_ids, (tuple, list)) and source_ids:
                output.append("  适用排放源：" + "、".join(SOURCE_LABELS.get(str(item_id), "其他已记录排放源") for item_id in source_ids))
    if not evidence_found:
        output.append("\n" + SNAPSHOT_STATE_LABELS[SnapshotState.EMPTY])
    if isinstance(raw, Mapping):
        report = raw.get("reporting_data")
        if isinstance(report, Mapping):
            short_fields = (
                ("boundary_description", "核算边界说明"), ("products_and_process", "主要产品/工艺流程"),
                ("emission_source_identification", "排放源识别说明"),
                ("other_report_information", "其他报告说明"),
            )
            values = [f"{label}：{report[key]}" for key, label in short_fields if report.get(key) not in (None, "", [], {})]
            if values:
                output.append("\n报告说明")
                output.extend(values)
    return "\n".join(output)


def build_parameter_view(record: AccountingRecord, evidence_names: Mapping[str, str], state: SnapshotState) -> str:
    if state is SnapshotState.LEGACY:
        return SNAPSHOT_STATE_LABELS[SnapshotState.LEGACY]
    if state is SnapshotState.CORRUPT:
        return SNAPSHOT_STATE_LABELS[SnapshotState.CORRUPT]
    if not record.parameter_snapshots:
        return SNAPSHOT_STATE_LABELS[SnapshotState.EMPTY]
    output = ["参数与因子来源（均为本 Record 冻结快照）"]
    for snapshot in record.parameter_snapshots:
        source_kind = SELECTION_LABELS.get(snapshot.selection_method.value, "已记录选择方式")
        lines = [f"- {snapshot.value_used} {snapshot.unit_used}；{source_kind}"]
        if snapshot.source_location:
            lines.append(f"  依据：{snapshot.source_location}")
        elif snapshot.source_id is None:
            lines.append("  来源说明：未提供")
        if snapshot.selection_reason:
            lines.append(f"  采用说明：{snapshot.selection_reason}")
        if snapshot.source_id or snapshot.factor_id:
            lines.append("  详细来源编号见专业信息。")
        names = [evidence_names[item] for item in snapshot.evidence_ref_ids if item in evidence_names]
        if names:
            lines.append("  关联证据：" + "、".join(dict.fromkeys(names)))
        output.extend(lines)
    return "\n".join(output)


def build_quality_view(record: AccountingRecord, qualification: object, qualification_state: SnapshotState) -> str:
    output = [f"核算状态：{status_label(record.status)}"]
    if qualification_state is SnapshotState.PRESENT and isinstance(qualification, Mapping):
        eligible = qualification.get("eligible")
        if eligible is True:
            output.append("年度报告资格：符合年度报告周期要求。")
        elif eligible is False:
            output.append("年度报告资格：不符合年度报告周期要求。")
        else:
            output.append("年度报告资格：本次未记录判定结果。")
        if qualification.get("message"):
            output.append(str(qualification["message"]))
    else:
        output.append("年度报告资格：" + SNAPSHOT_STATE_LABELS[qualification_state])
    warnings = tuple(
        problem for problem in (*record.problems, *record.calculation_result.problems)
        if problem.level.value in {"WARNING", "INFO"}
    )
    output.append("\n重要提醒")
    output.extend(f"- {_business_warning(problem.message)}" for problem in warnings) if warnings else output.append("- 无需处理的提醒。")
    output.append("\n报告资格与核算状态分别展示；不符合年度报告周期不代表核算失败。")
    return "\n".join(output)


def _business_warning(message: str) -> str:
    return re.sub(r"\b(?:CAR|GEN|STD)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b", "相关输入项", message)


def build_professional_view(
    record: AccountingRecord,
    *,
    raw: object,
    rules: object,
    trace: object,
    provenance: object,
    reporting: object,
    qualification: object,
    states: Mapping[str, SnapshotState],
    audit: object = (),
) -> str:
    warnings = tuple(
        problem for problem in (*record.problems, *record.calculation_result.problems)
        if problem.level.value == "WARNING"
    )
    output = [
        f"Record ID：{record.record_id}",
        f"创建时间：{record.created_at.isoformat()}",
        f"标准 ID：{record.standard_id}",
        f"标准版本：{record.standard_version or '未记录'}",
        f"算法版本：{record.algorithm_version}",
        f"状态枚举：{record.status.value}",
        f"总量：{record.calculation_result.total_amount} {record.calculation_result.total_unit}",
        "\n排放源稳定 ID：",
    ]
    output.extend(f"- {item.source_id}：{'纳入' if item.included else '未纳入'}" for item in record.input_snapshot.emission_sources)
    output.append("\n有效规则集：")
    rule_ids = rules.get("rule_ids", ()) if isinstance(rules, Mapping) else ()
    output.extend(f"- {value}" for value in rule_ids) if rule_ids else output.append("- 历史规则快照未记录")
    for title, value in (
        ("实际输入快照", raw), ("Trace 快照", trace), ("Provenance 快照", provenance),
        ("报告信息快照", reporting), ("年度报告资格快照", qualification),
    ):
        output.append(f"\n{title}状态：{states.get(title, SnapshotState.LEGACY).value}")
        output.append(repr(value) if value is not None else SNAPSHOT_STATE_LABELS[states.get(title, SnapshotState.LEGACY)])
    output.append("\n参数快照：")
    for item in record.parameter_snapshots:
        output.append(
            f"- {item.parameter_id}={item.value_used} {item.unit_used}; factor={item.factor_id}; "
            f"source={item.source_id}@{item.source_version}; detail={item.detail_id}; "
            f"location={item.source_location}; evidence={','.join(item.evidence_ref_ids)}"
        )
    if isinstance(trace, Mapping):
        output.append("\n公式/映射依据：")
        for step in _trace_steps(trace):
            output.append(
                f"- {step.get('trace_id')} / {step.get('process_instance_id')} / {step.get('formula_id')}: "
                f"{step.get('calculation_step')} = {step.get('intermediate_result')} {step.get('unit')}; "
                f"standard={step.get('standard_location')}; mapping={step.get('mapping_location')}; "
                f"parameters={step.get('parameter_references')}"
            )
    output.append("\n校验与警告：")
    output.extend(f"- {problem.code}：{problem.message}" for problem in warnings) if warnings else output.append("- 无警告")
    output.append("\n审计日志：")
    if isinstance(audit, (tuple, list)) and audit:
        output.extend(f"- {item}" for item in audit)
    else:
        output.append("- 未提供审计日志")
    output.append("\n历史记录为不可变快照；此页面不会查询当前目录或重新计算。")
    return "\n".join(output)


def build_record_summary(
    record: AccountingRecord,
    qualification: object,
    qualification_state: SnapshotState,
    trace: object,
    *,
    association: str = "当前无工作区关联",
) -> str:
    period = record.input_snapshot.period
    boundary = "已记录核算边界分项" if record.input_snapshot.boundary_component_ids else "历史记录未保存边界分项"
    source_lines = []
    for item in record.input_snapshot.emission_sources:
        if item.included:
            source_lines.append(f"- {SOURCE_LABELS.get(item.source_id, '其他已记录排放源')}")
    source_text = "、".join(line.removeprefix("- ") for line in source_lines) if source_lines else "无已启用排放源"
    output = [
        "基本信息",
        f"企业：{record.input_snapshot.enterprise_name or '未填写企业'}",
        f"核算期间：{period_label(record)}（{period.start.isoformat()} 至 {period.end.isoformat()}）",
        f"核算边界：{boundary}",
        f"核算标准：{standard_label(record.standard_id)} {record.standard_version or ''}".strip(),
        f"核算状态：{status_label(record.status)}",
        f"年度报告资格：{_qualification_label(qualification, qualification_state)}",
        f"所属工作区：{association}（当前工作区关系，不属于不可变 Record 快照）",
        f"已启用排放源：{source_text}",
        "\n核算结果",
    ]
    totals = frozen_totals(record, trace)
    total = totals.get("ET") or None
    direct = totals.get("ES") or None
    indirect = totals.get("EI") or None
    output.extend((
        f"温室气体排放总量：{format_amount(total)}",
        f"直接排放量：{format_amount(direct)}",
        f"购入/输出能源对应的净间接排放量：{format_amount(indirect)}",
        "标准报告数据 B.1—B.9 及逐项依据见“标准报告数据”页。",
    ))
    component_lines = [
        f"- {SOURCE_LABELS.get(line.emission_source_id, '其他排放源')}：{format_amount(line.amount, line.unit)}"
        for line in record.calculation_result.lines
        if line.line_id not in {"CAR-FLD-DIRECT-RESULT", "CAR-FLD-INDIRECT-RESULT", "CAR-FLD-TOTAL-RESULT"}
    ]
    if component_lines:
        output.extend(("\n排放源构成", *component_lines))
    if record.status is RecordStatus.COMPLETED_WITH_WARNINGS:
        output.append("\n关键提醒：本次核算含非致命提醒，详见“数据质量与提醒”。")
    return "\n".join(output)


def _qualification_label(value: object, state: SnapshotState) -> str:
    if state is SnapshotState.PRESENT and isinstance(value, Mapping):
        eligible = value.get("eligible")
        if eligible is True:
            return "符合年度报告周期要求"
        if eligible is False:
            return "不符合年度报告周期要求（仍可作为内部核算结果）"
    return SNAPSHOT_STATE_LABELS[state]


def summary_with_trace(
    record: AccountingRecord,
    qualification: object,
    qualification_state: SnapshotState,
    trace: object,
    *,
    association: str = "当前无工作区关联",
) -> str:
    return build_record_summary(record, qualification, qualification_state, trace, association=association)


def build_home_record_label(record: AccountingRecord) -> str:
    return " · ".join((
        record.input_snapshot.enterprise_name or "未填写企业",
        period_label(record),
        standard_label(record.standard_id),
        format_amount(record.calculation_result.total_amount, record.calculation_result.total_unit),
        status_label(record.status),
    ))


def build_record_list_label(record: AccountingRecord) -> str:
    return build_home_record_label(record)

