"""Read-only, snapshot-backed presentation helpers for RS02 record views."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from enum import Enum
import re
from typing import Any

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


def _trace_steps(trace: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(trace, Mapping):
        return ()
    steps = trace.get("formula_steps", ())
    return tuple(step for step in steps if isinstance(step, Mapping)) if isinstance(steps, (tuple, list)) else ()


def build_record_report_model(record,raw,trace,reporting, *, provenance=None,qualification=None):
    from packages.application.reporting import build_report_model
    return build_report_model(record,raw,trace,provenance or {},reporting,qualification or {},snapshot_schema_version=1 if isinstance(raw,Mapping) else 0)


def build_report_view(record: AccountingRecord,raw: object,trace: object,reporting: object) -> str:
    """Compatibility text presentation of the same frozen business tables as Word."""
    from packages.application.reporting.presentation import report_text
    try:
        return report_text(build_record_report_model(record,raw,trace,reporting))
    except ValueError:
        return "此标准尚未提供业务报告表式；可查看已冻结的核算结果。"


def _reporting_value(value: object) -> str:
    if value in (None, "", [], {}):
        return "未填写"
    return str(value)


def build_activity_evidence_view(raw: object, reporting: object, reporting_state: SnapshotState) -> str:
    output = ["活动数据与来源证据", "以下为本次记录保存的活动数据来源证据。"]
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
    output = ["参数与因子来源（均为保存时采用值）"]
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
            lines.append(f"  来源版本：{snapshot.source_version or '未记录'}；因子年份：{snapshot.factor_year or '未记录'}")
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



def business_choice_label(value: object, *, field_name: str | None = None) -> str:
    """Translate saved choices for viewing; never alter their frozen values."""
    from packages.application.reporting.carbon_material_model import _FUEL_NAMES, _SOURCE_NAMES
    if isinstance(value, bool):
        return "是" if value else "否"
    text = str(value.value if isinstance(value, Enum) else value)
    if field_name == "fuel_type" and text in _FUEL_NAMES:
        return _FUEL_NAMES[text]
    names = {
        **_FUEL_NAMES, **_SOURCE_NAMES, **SOURCE_KIND_LABELS, **SOURCE_TYPE_LABELS,
        **SELECTION_LABELS,
        "VOLUME": "体积计量", "MASS": "质量计量", "HEAT": "热量计量",
        "HEAT_CONTENT": "按低位发热量和单位热值含碳量", "DIRECT": "直接采用含碳量",
        "AUTO_SATURATED": "饱和蒸汽参考值", "USER_MANUAL": "独立已知焓值",
        "SATURATED_TABLE": "饱和蒸汽参考表", "SUPERHEATED_IF97": "过热蒸汽物性计算",
        "INSIDE_ENTERPRISE": "企业边界内热源", "OUTSIDE_ENTERPRISE": "企业边界外热源",
        "calcination_feed": "待煅烧原料", "calcined_product": "煅后料",
        "underburn_recovered": "欠煅烧料", "carbon_dust": "炭粉尘",
        "baking_filler": "焙烧填充料", "green_baking_product": "待焙烧/炭化品",
        "baked_product": "焙烧/炭化产品", "baking_byproduct": "焙烧副产品",
        "graphitization_packing": "石墨化保温料和电阻料",
        "green_graphitization_product": "待石墨化品", "graphitized_product": "石墨化产品",
        "graphitization_byproduct": "石墨化副产品",
    }
    if text in names:
        return names[text]
    if re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+", text):
        return "其他已保存选项"
    return text


def business_source_text(text: str) -> str:
    """Keep values/source clauses while translating technical choice tokens."""
    text = text.replace("gbt_32151_34_2024", "GB/T 32151.34—2024")
    parts = re.split(r"(；|\n)", text)
    for index, part in enumerate(parts):
        # A document reference is business evidence, not a choice enum.
        if re.match(r"\s*(?:来源定位|来源参考|来源说明|来源版本|因子年度|标准依据|依据|展示前完整值|采用说明)：", part):
            continue
        parts[index] = re.sub(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b",
                              lambda match: business_choice_label(match.group()), part)
    return _business_warning("".join(parts))


def build_frozen_activity_view(record: AccountingRecord) -> str:
    output = ["核算标准：" + standard_label(record.standard_id),
              "标准版本：" + (record.standard_version or "未记录")]
    for index, activity in enumerate(record.input_snapshot.activities, 1):
        output.append(f"活动数据 {index}：{activity.value} {activity.unit}；"
                      f"{business_choice_label(activity.source_type.value)}")
        if activity.source_reference:
            output.append(f"  来源说明：{activity.source_reference}")
    if not record.input_snapshot.activities:
        output.append("未保存独立活动数据条目；已保存的业务输入见本页。")
    return "\n".join(output)


def _basis_variable_label(name: str, source: str) -> str:
    labels = {
        "fuel_total": "化石燃料排放合计", "qge": "购入电量", "qse": "输出电量",
        "ef2": "电力排放因子", "bgd": "购入蒸汽质量", "bsd": "输出蒸汽质量",
        "ef3": "热力排放因子", "steam_quantity_input": "录入蒸汽量",
        "hm_reference": "保存的参考焓值", "t": "报告期时长",
        "er subtotal": "烟气焚烧排放小计", "ed subtotal": "烟气脱硫排放小计",
        "efu": "化石燃料排放合计", "ec": "原料煅烧排放合计",
        "eb": "焙烧/炭化排放合计", "eg": "石墨化排放合计", "ep": "烟气治理排放合计",
        "ege": "购入电力排放", "egd": "购入热力排放", "ese": "输出电力对应排放",
        "esd": "输出热力对应排放", "es": "直接排放量", "ei": "间接排放量",
        "output_carbon_total": "输出物料含碳量合计",
    }
    if name == "hm" and source in (SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_HEAT):
        return "蒸汽焓值"
    component = re.fullmatch(r"(cal|i|ef1|tr)\[(\d+)\]", name)
    if component:
        term = {"cal": "碳酸盐原料净耗量", "i": "组分含量", "ef1": "二氧化碳质量分数", "tr": "转化率"}[component[1]]
        return f"第 {component[2]} 组分 · {term}"
    return labels.get(name, REPORT_FIELD_LABELS.get(name, "历史业务用量（名称未记录）"))


def build_calculation_basis_view(
    record: AccountingRecord, *, trace: object, provenance: object,
    states: Mapping[str, SnapshotState], display_values: bool = True,
) -> str:
    """Frozen business formulas/values/standard clauses, without technical audit."""
    def value_text(value):
        if display_values:
            try:
                Decimal(str(value))
            except (InvalidOperation, ValueError):
                pass
            else:
                return format_amount(value, "")
        return business_choice_label(value)

    output = [f"企业：{record.input_snapshot.enterprise_name or '未填写'}",
              f"核算标准：{standard_label(record.standard_id)}",
              f"标准版本：{record.standard_version or '未记录'}"]
    if states.get("Trace 快照") is SnapshotState.CORRUPT:
        output.append("无法读取该历史信息。已保存的输入、结果及其他来源仍可查看。")
    for index, step in enumerate(_trace_steps(trace), 1):
        output.append(f"\n计算依据 {index} · {SOURCE_LABELS.get(str(step.get('emission_source_id')), '排放量汇总与换算')}")
        if step.get("calculation_step"):
            expression = business_source_text(str(step["calculation_step"]))
            expression = re.sub(r"；(?:实例|燃料)\s+[^；\n]+", "", expression)
            if "按映射变量代入" in expression:
                expression = "按保存时的物料平衡关系与参数计算；各项业务用量和标准依据列于本条。"
            if display_values:
                expression = re.sub(r"(?<![\w.])-?\d+\.\d{7,}(?:[eE][+-]?\d+)?", lambda match: value_text(match[0]), expression)
            output.append("保存的计算式：" + expression)
        if step.get("standard_location"):
            output.append("标准依据：" + str(step["standard_location"]))
        if step.get("intermediate_result") is not None:
            output.append(f"保存的排放结果：{value_text(step['intermediate_result'])} {step.get('unit') or ''}".strip())
        for number, variable in enumerate(step.get("input_variables") or (), 1):
            if isinstance(variable, Mapping):
                name = str(variable.get("name") or "").lower()
                label = _basis_variable_label(name, str(step.get("emission_source_id") or ""))
                value = value_text(variable.get("value", "未记录"))
                output.append(f"  {label}：{value} {variable.get('unit') or ''}".strip())
        evidence = step.get("calculation_provenance")
        if isinstance(evidence, Mapping):
            for key, label in (("enthalpy_used_kj_per_kg", "采用焓值（kJ/kg）"),
                               ("automatic_reference_enthalpy_kj_per_kg", "保存的参考焓值（kJ/kg）"),
                               ("standard_location", "标准依据")):
                if evidence.get(key) is not None:
                    output.append(f"  {label}：{value_text(evidence[key]) if key != 'standard_location' else evidence[key]}")
    if isinstance(provenance, Mapping):
        rule_set = provenance.get("effective_rule_set")
        rules = rule_set.get("rules", ()) if isinstance(rule_set, Mapping) else ()
        seen = set()
        for rule in rules:
            if not isinstance(rule, Mapping):
                continue
            description = "；".join(str(rule[key]) for key in ("description", "source_location") if rule.get(key))
            description = business_source_text(description)
            if description and description not in seen:
                output.append("标准与业务依据：" + description)
                seen.add(description)
    if display_values:
        output.append("\n以上数值按界面精度显示；悬停本段可查看保存时完整数值。历史记录不会重新核算。")
    else:
        output.append("\n以上为保存时的完整业务数值；历史记录不会重新核算。")
    return "\n".join(output)


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

