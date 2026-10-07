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

REPORT_SCHEMA_VERSION = "1.0.0"


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

_PATH_NAMES = {"VOLUME": "体积", "MASS": "质量", "HEAT": "热量"}
_MATERIAL_NAMES = {
    "calcination_feed": "待煅烧原料", "calcined_product": "煅后料",
    "underburn_recovered": "欠烧煅料", "carbon_dust": "碳粉尘",
    "baking_filler": "填充料", "green_baking_product": "待焙烧/炭化品",
    "baked_product": "焙烧/炭化产品", "baking_byproduct": "粉尘/碎屑/副产品",
    "graphitization_packing": "保温料/电阻料", "green_graphitization_product": "待石墨化品",
    "graphitized_product": "石墨化产品", "graphitization_byproduct": "粉尘/碎屑/残块/副产品",
}
_BUSINESS_SOURCE_NAMES = {
    SOURCE_FUEL: "化石燃料燃烧", SOURCE_CALCINATION: "原料煅烧", SOURCE_BAKING: "焙烧/炭化",
    SOURCE_GRAPHITIZATION: "石墨化", SOURCE_FUME: "烟气焚烧", SOURCE_FGD: "烟气脱硫",
    SOURCE_PURCHASED_ELECTRICITY: "购入电力", SOURCE_EXPORTED_ELECTRICITY: "输出电力",
    SOURCE_PURCHASED_HEAT: "购入热力", SOURCE_EXPORTED_HEAT: "输出热力",
}
_VARIABLE_NAMES = {
    "gc": "待煅烧原料数量", "wfc": "待煅烧原料固定碳含量", "cc": "煅后料数量",
    "ucc": "欠烧煅料数量", "du": "碳粉尘数量", "wfc_c": "输出物料固定碳含量",
    "wvar": "待煅烧原料挥发分", "wvar_c": "煅后料挥发分", "k1": "煅烧系数",
    "bpm": "填充料数量", "bpmfc": "填充料固定碳含量", "bg": "待焙烧/炭化品数量",
    "bgfc": "待焙烧/炭化品固定碳含量", "bwt": "粉尘/副产品碳量", "bp": "焙烧/炭化产品数量",
    "bpfc": "焙烧/炭化产品固定碳含量", "bpmvar": "填充料挥发分", "bgvar": "待焙烧/炭化品挥发分", "k2": "焙烧系数",
    "gpm": "保温料/电阻料数量", "gpmfc": "保温料/电阻料固定碳含量", "gta": "待石墨化品数量",
    "gtafc": "待石墨化品固定碳含量", "gwt": "粉尘/副产品碳量", "gp": "石墨化产品数量",
    "gpfc": "石墨化产品固定碳含量", "gpmvar": "保温料/电阻料挥发分", "k3": "石墨化系数",
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
    if isinstance(value, Mapping) and "value" in value:
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


def _source_description(snapshot: Mapping[str, Any] | None) -> str | None:
    return _snapshot_source(snapshot)


def _activity_source(value: object) -> str | None:
    activity = _mapping(value)
    parts = [
        _enum(activity.get("source_type"), _SOURCE_NAMES),
        _text(activity.get("source_reference")),
    ]
    return "；".join(part for part in parts if part) or None


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
            parameter_snapshots[item.detail_id] = {
                "value_used": item.value_used, "unit_used": item.unit_used,
                "selection_method": item.selection_method.value, "source_location": item.source_location,
                "source_version": item.source_version, "source_id": item.source_id, "factor_year": item.factor_year,
            }
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

    line_by_id = {line.line_id: line for line in record.calculation_result.lines}
    aggregations = _mapping(trace.get("aggregations"))
    subtotals = _mapping(trace.get("source_subtotals"))
    def result_line(identifier: str) -> str:
        line = line_by_id.get(identifier)
        return _display_amount(line.amount) if line else ""

    def aggregation_or_line(key: str, identifier: str) -> str:
        value = aggregations.get(key)
        return _display_amount(value if value is not None else result_line(identifier))

    b1_values = [
        ("直接排放量", ReportCell(aggregation_or_line("ES", "CAR-FLD-DIRECT-RESULT"), "tCO₂")),
        ("净间接排放量", ReportCell(aggregation_or_line("EI", "CAR-FLD-INDIRECT-RESULT"), "tCO₂")),
        ("温室气体排放总量", ReportCell(_display_amount(aggregations.get("ET") if aggregations.get("ET") is not None else record.calculation_result.total_amount), "tCO₂")),
    ]
    source_names = (
        ("fuel", "化石燃料燃烧"), ("calcination", "原料煅烧"), ("baking", "焙烧/炭化"),
        ("graphitization", "石墨化"), ("gas_control", "烟气治理"),
        ("purchased_electricity", "购入电力"), ("exported_electricity", "输出电力抵扣"),
        ("purchased_heat", "购入热力"), ("exported_heat", "输出热力抵扣"),
    )
    b1_values.extend((label, ReportCell(_display_amount(subtotals.get(key)), "tCO₂")) for key, label in source_names if key in subtotals)
    sections: list[ReportSection] = [
        ReportSection("basic", "企业及核算基本情况", (_table("basic-info", "报告基本信息", ("项目", "内容"), basic_rows),)),
        ReportSection("b1", "B.1 温室气体排放量汇总", (_table("b1-summary", "排放量汇总", ("项目", "排放量"), b1_values),)),
    ]

    fuel_rows: list[Sequence[ReportCell | str]] = []
    for item in _entries(raw, "fuel_inputs"):
        fuel_id = _text(item.get("fuel_id"))
        activity = _mapping(item.get("activity"))
        lhv = _parameter_cell(item.get("lower_heating_value"), parameter_snapshots, f"CAR-FLD-F01-{fuel_id}-LHV")
        carbon = _parameter_cell(item.get("carbon_content"), parameter_snapshots, f"CAR-FLD-F01-{fuel_id}-CARBON")
        oxidation = _parameter_cell(item.get("oxidation_rate"), parameter_snapshots, f"CAR-FLD-F01-{fuel_id}-FOX")
        fuel_name = _enum(item.get("fuel_type"), _FUEL_NAMES)
        if item.get("fuel_label"):
            fuel_name = _text(item.get("fuel_label"))
        emission = next((line.amount for line in record.calculation_result.lines if line.emission_source_id == SOURCE_FUEL and line.line_id == f"{SOURCE_FUEL}.{fuel_id}"), None)
        if emission is None:
            emission = next((step.get("intermediate_result") for step in _trace_steps(trace) if step.get("emission_source_id") == SOURCE_FUEL and step.get("process_instance_id") == fuel_id), "")
        fuel_rows.append((
            ReportCell(fuel_name), ReportCell(_enum(item.get("path"), _PATH_NAMES)),
            ReportCell(_text(activity.get("value")), _text(activity.get("unit")) or None, _activity_source(activity)),
            lhv, carbon, oxidation, ReportCell(_display_amount(emission), "tCO₂" if emission != "" else None),
        ))
    sections.append(ReportSection("b2", "B.2 化石燃料活动数据和排放因子", (_table(
        "b2-fuels", "燃料明细", ("燃料品种", "计量方式", "活动量", "低位发热量/来源", "单位热值含碳量/来源", "碳氧化率/来源", "排放量"), fuel_rows, landscape=True,
    ),)))

    process_specs = (
        ("b3", "B.3 原料煅烧", "calcinations", "calcination", SOURCE_CALCINATION, "calcination"),
        ("b4", "B.4 焙烧/炭化", "bakings", "baking", SOURCE_BAKING, "baking"),
        ("b5", "B.5 石墨化", "graphitizations", "graphitization", SOURCE_GRAPHITIZATION, "graphitization"),
    )
    for section_id, title, collection, process_name, source_id, _trace_source in process_specs:
        tables: list[ReportTable] = []
        for ordinal, process in enumerate(_entries(raw, collection, process_name), 1):
            instance_id = process.get("instance_id")
            materials = process.get("material_rows", ())
            rows: list[Sequence[ReportCell | str]] = []
            for material in materials if isinstance(materials, (list, tuple)) else ():
                mat = _mapping(material)
                rows.append((
                    ReportCell(_enum(mat.get("role"), _MATERIAL_NAMES)), ReportCell(_text(mat.get("name"))),
                    ReportCell(_text(mat.get("mass_t")), "t"), ReportCell(_text(mat.get("fixed_carbon_percent")), "%", _enum(mat.get("fixed_carbon_source"), _SOURCE_NAMES)),
                    ReportCell(_text(mat.get("volatile_matter_percent")), "%", _enum(mat.get("volatile_matter_source"), _SOURCE_NAMES)),
                ))
            instance_step = _step_for_instance(trace, source_id, instance_id)
            if instance_step is None:
                instance_step = next((step for step in _trace_steps(trace) if _text(step.get("process_instance_id")) == _text(instance_id)), None)
            tables.append(_table(f"{section_id}-{ordinal}-materials", f"过程单元{ordinal}实际物料", ("物料类别", "物料名称", "数量", "固定碳含量/来源", "挥发分/来源"), rows))
            variables = _mapping(instance_step)
            variable_rows = []
            inputs = variables.get("input_variables", ())
            for value in inputs if isinstance(inputs, (list, tuple)) else ():
                if not isinstance(value, Mapping):
                    continue
                name = _text(value.get("name"))
                variable_rows.append((ReportCell(_VARIABLE_NAMES.get(name, "其他核算参数")), ReportCell(_text(value.get("value")), _text(value.get("unit")) or None)))
            variable_rows.append((ReportCell("本过程排放量"), ReportCell(_step_result(instance_step), "tCO₂")))
            tables.append(_table(f"{section_id}-{ordinal}-summary", f"过程单元{ordinal}汇总及结果", ("项目", "值"), variable_rows))
        sections.append(ReportSection(section_id, title, tuple(tables), ("排放量按Record及Trace中已保存的过程结果列示。",)))

    fume_rows: list[Sequence[ReportCell | str]] = []
    for item in _entries(raw, "fume_incinerations", "fume_incineration"):
        iid = item.get("instance_id")
        step = _step_for_instance(trace, SOURCE_FUME, iid)
        fch = _parameter_cell(item.get("fch"), parameter_snapshots, f"CAR-FLD-P04A-{_text(iid)}-FCH")
        fume_rows.append((ReportCell(f"设施{len(fume_rows) + 1}"), ReportCell(_text(_mapping(item.get("q")).get("value")), "Nm³/h"), ReportCell(_text(_mapping(item.get("qvar")).get("value")), "mg/Nm³"), ReportCell(_text(_mapping(item.get("hm")).get("value")), "GJ/t"), fch, ReportCell(_text(_mapping(item.get("fox")).get("value"))), ReportCell(_text(_mapping(item.get("duration")).get("value")), "d"), ReportCell(_step_result(step), "tCO₂")))
    sections.append(ReportSection("b6", "B.6 烟气焚烧治理", (_table("b6-fume", "烟气焚烧设施", ("设施", "烟气流量", "焦油含量", "低位发热量", "单位热值含碳量/来源", "碳氧化率", "运行时间", "排放量"), fume_rows, landscape=True),)))

    fgd_rows: list[Sequence[ReportCell | str]] = []
    for unit_ordinal, unit in enumerate(_entries(raw, "fgd_units", "fgd"), 1):
        iid = unit.get("instance_id")
        step = next((item for item in _trace_steps(trace) if item.get("emission_source_id") == SOURCE_FGD and _text(item.get("process_instance_id")) == _text(iid)), None)
        for component_index, component in enumerate(unit.get("components", ()) if isinstance(unit.get("components"), (list, tuple)) else ()):
            comp = _mapping(component)
            detail_prefix = f"CAR-FLD-P04B-{_text(iid)}-{component_index}"
            fgd_rows.append((ReportCell(f"设施{unit_ordinal}"), ReportCell(_text(comp.get("carbonate_type"))), ReportCell(_text(_mapping(comp.get("amount")).get("value")), "t"), _parameter_cell(comp.get("carbonate_fraction"), parameter_snapshots, f"{detail_prefix}-I"), _parameter_cell(comp.get("emission_factor"), parameter_snapshots, f"{detail_prefix}-EF1"), _parameter_cell(comp.get("conversion_rate"), parameter_snapshots, f"{detail_prefix}-TR"), ReportCell(_step_result(step) if component_index == 0 else "", "tCO₂" if component_index == 0 else None)))
    sections.append(ReportSection("b7", "B.7 烟气脱硫净化", (_table("b7-fgd", "脱硫剂及碳酸盐组分", ("设施/批次", "碳酸盐种类", "消耗量", "组分含量/来源", "排放因子/来源", "转化率/来源", "设施排放量"), fgd_rows, landscape=True),)))

    electricity_rows: list[Sequence[ReportCell | str]] = []
    for collection, direction, source_id in (("electricity_details", "购入", SOURCE_PURCHASED_ELECTRICITY), ("exported_electricity", "输出", SOURCE_EXPORTED_ELECTRICITY)):
        for item in _entries(raw, collection):
            identity = _text(item.get("detail_id") or item.get("line_id"))
            step = _step_for_instance(trace, source_id, identity)
            amount = item.get("electricity_amount", item.get("amount"))
            factor = _parameter_cell(item.get("factor"), parameter_snapshots, f"CAR-FLD-POWER-EXPORTED-EF.{identity}")
            snapshot = next((snap for snap in record.parameter_snapshots if snap.detail_id == identity), None)
            if snapshot is not None and collection == "electricity_details":
                factor = ReportCell(_text(snapshot.value_used), snapshot.unit_used, _snapshot_source(parameter_snapshots.get(identity)))
            electricity_kind = _enum(item.get("attribute"), {"ORDINARY": "常规电力", "NONFOSSIL": "非化石电力", "FOSSIL": "化石能源电力"})
            activity_source = _activity_source(item.get("electricity_amount"))
            electricity_rows.append((ReportCell(direction), ReportCell(electricity_kind), ReportCell(_text(amount), _text(item.get("electricity_unit") or item.get("unit") or "MWh"), activity_source), factor, ReportCell(_step_result(step), "tCO₂")))
    sections.append(ReportSection("b8", "B.8 购入和输出电力", (_table("b8-electricity", "电力来源明细", ("方向", "电力属性", "电量/来源", "排放因子/来源", "对应排放量"), electricity_rows),)))

    heat_rows: list[Sequence[ReportCell | str]] = []
    for collection, direction, source_id in (("purchased_heat", "购入", SOURCE_PURCHASED_HEAT), ("exported_heat", "输出", SOURCE_EXPORTED_HEAT)):
        for item in _entries(raw, collection):
            iid = _text(item.get("line_id"))
            step = _step_for_instance(trace, source_id, iid)
            provenance = _mapping(_mapping(step).get("calculation_provenance"))
            amount = item.get("steam_amount_t") if item.get("steam_amount_t") is not None else item.get("amount")
            heat_factor = next((snap for snap in record.parameter_snapshots if snap.detail_id == f"CAR-FLD-HEAT-{iid}-EF3"), None)
            heat_source = _snapshot_source(parameter_snapshots.get(f"CAR-FLD-HEAT-{iid}-EF3")) if heat_factor else None
            enthalpy = _mapping(item.get("enthalpy"))
            used_enthalpy = _text(provenance.get("enthalpy_used_kj_per_kg")) or _text(enthalpy.get("value"))
            enthalpy_source = _text(provenance.get("enthalpy_source"))
            table_name = _text(provenance.get("table"))
            if table_name:
                enthalpy_source = f"{enthalpy_source}；GB/T 32151.34—2024 附录{table_name}"
            heat_rows.append((
                ReportCell(direction), ReportCell(_text(amount), "t", _activity_source(item.get("amount"))), ReportCell(_enum(item.get("steam_kind"), {"SATURATED": "饱和蒸汽", "SUPERHEATED": "过热蒸汽"})),
                ReportCell(_text(_mapping(item.get("pressure_mpa")).get("value")), "MPa（绝压）"), ReportCell(_text(_mapping(item.get("temperature_c")).get("value")), "℃"),
                ReportCell(used_enthalpy, "kJ/kg", enthalpy_source), ReportCell(_text(provenance.get("automatic_reference_enthalpy_kj_per_kg")), "kJ/kg" if provenance.get("automatic_reference_enthalpy_kj_per_kg") else None, "自动参考值" if provenance.get("automatic_reference_enthalpy_kj_per_kg") else None),
                ReportCell(_text(heat_factor.value_used) if heat_factor else "", "tCO₂/GJ", heat_source), ReportCell(_step_result(step), "tCO₂"),
            ))
    sections.append(ReportSection("b9", "B.9 购入和输出热力", (_table("b9-heat", "热力来源明细", ("方向", "蒸汽量", "蒸汽类型", "压力", "温度", "采用焓值/来源", "自动参考焓值", "排放因子/来源", "对应排放量"), heat_rows, landscape=True),)))

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
    )


__all__ = ["REPORT_SCHEMA_VERSION", "ReportCell", "ReportModel", "ReportRow", "ReportSection", "ReportTable", "build_report_model"]
