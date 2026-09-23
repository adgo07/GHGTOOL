"""Presentation field semantics for the GB/T 32151.34 accounting page.

The domain model intentionally keeps its stable, formula-oriented field keys.
This module is the presentation boundary that gives those keys user-facing
names, units, validation metadata, and source locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Iterable


class FieldDataType(str, Enum):
    """Supported presentation input shapes."""

    TEXT = "text"
    QUANTITY = "quantity"
    PERCENTAGE = "percentage"
    INTEGER = "integer"
    ENUM = "enum"
    BOOLEAN = "boolean"
    READONLY_PARAMETER = "readonly_parameter"


@dataclass(frozen=True)
class FieldSpec:
    """A typed, traceable definition for one user-facing field."""

    internal_key: str
    display_name: str
    data_type: FieldDataType
    unit: str = "无"
    min: Decimal | None = None
    max: Decimal | None = None
    required: bool = False
    help_text: str = ""
    standard_symbol: str | None = None
    standard_clause: str = ""
    source_location: str = ""
    advanced: bool = False
    domain_unit: str | None = None

    @property
    def is_numeric(self) -> bool:
        return self.data_type in {
            FieldDataType.QUANTITY,
            FieldDataType.PERCENTAGE,
            FieldDataType.INTEGER,
        }

    @property
    def label(self) -> str:
        """Return a label whose unit is controlled by this definition."""

        if self.unit in {"", "无"}:
            return self.display_name
        return f"{self.display_name}（{self.unit}）"


SOURCE_LABELS = {
    "CAR-SRC-FUEL-001": "化石燃料燃烧（F01）",
    "CAR-SRC-CALCINATION-001": "原料煅烧（P01）",
    "CAR-SRC-BAKING-001": "炭素制品焙烧/炭化（P02）",
    "CAR-SRC-GRAPHITIZATION-001": "炭素制品石墨化（P03）",
    "CAR-SRC-FUME-INCINERATION-001": "烟气焚烧治理（P04A）",
    "CAR-SRC-FGD-001": "烟气脱硫净化（P04B）",
    "CAR-SRC-PURCHASED-ELECTRICITY-001": "购入电力（I01）",
    "CAR-SRC-PURCHASED-HEAT-001": "购入热力/动力（I02）",
    "CAR-SRC-EXPORTED-ELECTRICITY-001": "输出电力（I03）",
    "CAR-SRC-EXPORTED-HEAT-001": "输出热力/动力（I04）",
}


_STANDARD = "GB/T 32151.34—2024"
_RECEIVED_BASIS = "项目确认口径 SM01-DECISION-006；标准映射 B.3-B.5"


def _spec(
    internal_key: str,
    display_name: str,
    data_type: FieldDataType,
    *,
    unit: str = "无",
    minimum: str | int | Decimal | None = None,
    maximum: str | int | Decimal | None = None,
    required: bool = False,
    help_text: str = "",
    standard_symbol: str | None = None,
    standard_clause: str = "",
    source_location: str = "",
    advanced: bool = False,
    domain_unit: str | None = None,
) -> FieldSpec:
    return FieldSpec(
        internal_key=internal_key,
        display_name=display_name,
        data_type=data_type,
        unit=unit,
        min=None if minimum is None else Decimal(str(minimum)),
        max=None if maximum is None else Decimal(str(maximum)),
        required=required,
        help_text=help_text,
        standard_symbol=standard_symbol,
        standard_clause=standard_clause,
        source_location=source_location,
        advanced=advanced,
        domain_unit=domain_unit,
    )


FIELD_SPECS: dict[str, FieldSpec] = {}


def _register(spec: FieldSpec) -> FieldSpec:
    FIELD_SPECS[spec.internal_key] = spec
    return spec


# 01 核算信息 / 02 核算边界
for _item in (
    _spec(
        "standard_id",
        "核算标准",
        FieldDataType.READONLY_PARAMETER,
        help_text="当前页面固定采用 GB/T 32151.34—2024。",
        standard_clause="适用标准",
        source_location=_STANDARD,
    ),
    _spec(
        "enterprise_name",
        "企业名称",
        FieldDataType.TEXT,
        required=True,
        help_text="填写本次核算对应的法人企业或独立核算单位名称。",
        standard_clause="B.1",
        source_location=_STANDARD,
    ),
    _spec(
        "period_type",
        "核算周期类型",
        FieldDataType.ENUM,
        required=True,
        help_text="选择年度核算或月度内部周期结果。",
        standard_clause="B.1",
        source_location=_STANDARD,
    ),
    _spec(
        "period_year",
        "核算年份",
        FieldDataType.INTEGER,
        unit="年",
        minimum=2000,
        maximum=2100,
        required=True,
        help_text="填写核算期所属年份。",
        standard_clause="B.1",
        source_location=_STANDARD,
    ),
    _spec(
        "period_month",
        "核算月份",
        FieldDataType.INTEGER,
        unit="月",
        minimum=1,
        maximum=12,
        required=True,
        help_text="月度核算时填写 1 至 12 月。年度核算时该值不参与计算。",
        standard_clause="B.1",
        source_location=_STANDARD,
    ),
    _spec(
        "boundary_confirmed",
        "核算边界确认",
        FieldDataType.BOOLEAN,
        required=True,
        help_text="确认法人企业/独立核算单位及生产系统边界。",
        standard_clause="4.1",
        source_location=_STANDARD,
    ),
    _spec(
        "other_activity_present",
        "其他行业活动",
        FieldDataType.BOOLEAN,
        help_text="存在本标准未覆盖的其他行业活动时，需要按其他相关标准核算。",
        standard_clause="4.2；CAR-RULE-OTHER-ACTIVITY-001",
        source_location=_STANDARD,
    ),
    _spec(
        "transport_present",
        "上下游运输活动",
        FieldDataType.BOOLEAN,
        help_text="存在上下游运输时，需要按其他相关标准核算。",
        standard_clause="4.2；CAR-RULE-TRANSPORT-001",
        source_location=_STANDARD,
    ),
):
    _register(_item)


# 03 排放源识别
for _source_id, _source_name in SOURCE_LABELS.items():
    _register(
        _spec(
            f"source_status.{_source_id}",
            f"{_source_name}状态",
            FieldDataType.ENUM,
            required=True,
            help_text="选择本次核算是否涉及该排放源。",
            standard_clause="5.1；B.1",
            source_location=_STANDARD,
        )
    )


# F01 燃料燃烧。计量路径由枚举决定，用户不能自由填写单位。
for _item in (
    _spec(
        "fuel_type",
        "燃料种类",
        FieldDataType.ENUM,
        required=True,
        help_text="选择本条燃料明细的种类；相同燃料可按不同计量点分别录入。",
        standard_clause="B.2",
        source_location=_STANDARD,
    ),
    _spec(
        "fuel_id",
        "燃料品种/明细标识",
        FieldDataType.TEXT,
        help_text="填写燃料品种或本条燃料明细的业务标识。",
        standard_symbol="FUEL-KIND",
        standard_clause="B.2",
        source_location=_STANDARD,
    ),
    _spec(
        "fuel_path",
        "燃料计量路径",
        FieldDataType.ENUM,
        required=True,
        help_text="按体积、质量或热量选择燃料活动数据路径。",
        standard_clause="式（1）—式（3）；B.2",
        source_location=_STANDARD,
    ),
    _spec(
        "fuel_activity",
        "燃料活动量",
        FieldDataType.QUANTITY,
        unit="由计量路径确定",
        minimum=0,
        help_text="活动量单位由燃料计量路径确定：10⁴Nm³、t 或 GJ。",
        standard_clause="式（1）—式（3）；B.2",
        source_location=_STANDARD,
    ),
    _spec(
        "fuel_carbon",
        "燃料单位含碳量",
        FieldDataType.QUANTITY,
        unit="由计量路径确定",
        minimum=0,
        help_text="单位由计量路径确定：tC/10⁴Nm³、tC/t 或 tC/GJ。",
        standard_clause="附录 C.1；B.2",
        source_location=_STANDARD,
    ),
    _spec(
        "fuel_oxidation",
        "碳氧化率",
        FieldDataType.PERCENTAGE,
        unit="%",
        minimum=0,
        maximum=100,
        help_text="按百分数输入，系统传入 Domain 前转换为 0—1 比例。",
        standard_symbol="FOx",
        standard_clause="附录 C.1；B.2",
        source_location=_STANDARD,
        domain_unit="ratio",
    ),
    _spec(
        "fuel_source_reference",
        "参数数据来源",
        FieldDataType.TEXT,
        help_text="使用企业实测/检测参数时，填写检测报告、台账或其他来源编号。",
        standard_clause="第5.2.1条；附录C.1",
        source_location=_STANDARD,
    ),
):
    _register(_item)


def _register_process_fields(prefix: str, clause: str, fields: Iterable[tuple[str, str, str, str, str | None]]) -> None:
    for internal_key, name, data_type, unit, symbol in fields:
        is_percentage = data_type == "percentage"
        _register(
            _spec(
                f"{prefix}.{internal_key}",
                name,
                FieldDataType.PERCENTAGE if is_percentage else FieldDataType.QUANTITY,
                unit=unit,
                minimum=0,
                maximum=100 if is_percentage else None,
                help_text=(
                    "按百分数输入，系统传入 Domain 前转换为 0—1 比例。"
                    if is_percentage
                    else "填写本排放源的活动数据；不得输入文字。"
                ),
                standard_symbol=symbol,
                standard_clause=clause,
                source_location=_STANDARD,
                domain_unit="ratio" if is_percentage else unit,
            )
        )


_register_process_fields(
    "calcination",
    "B.3；式（6）",
    (
        ("gc", "待煅烧原料总量", "quantity", "t", "GC"),
        ("wfc", "原料收到基固定碳含量", "percentage", "%", "WFC"),
        ("cc", "煅后料产量", "quantity", "t", "CC"),
        ("ucc", "欠烧煅料回收量", "quantity", "t", "UCC"),
        ("du", "炭粉尘排放量", "quantity", "t", "DU"),
        ("wfc_c", "煅后料收到基固定碳含量", "percentage", "%", "WFC-C"),
        ("wvar", "原料收到基挥发分含量", "percentage", "%", "WVar"),
        ("wvar_c", "煅后料收到基挥发分含量", "percentage", "%", "WVar-C"),
    ),
)
_register_process_fields(
    "baking",
    "B.4；式（7）",
    (
        ("bpm", "填充料消耗量", "quantity", "t", "BPM"),
        ("bpmfc", "填充料收到基固定碳含量", "percentage", "%", "BPMFC"),
        ("bg", "待焙烧/炭化品总量", "quantity", "t", "BG"),
        ("bgfc", "待焙烧品收到基固定碳含量", "percentage", "%", "BGFC"),
        ("bwt", "粉尘、碎屑、副产品的碳输出", "quantity", "tC", "BWT"),
        ("bp", "焙烧/炭化品产量", "quantity", "t", "BP"),
        ("bpfc", "产品收到基固定碳含量", "percentage", "%", "BPFC"),
        ("bpmvar", "填充料收到基挥发分含量", "percentage", "%", "BPMVar"),
        ("bgvar", "待焙烧品收到基挥发分含量", "percentage", "%", "BGVar"),
    ),
)
_register_process_fields(
    "graphitization",
    "B.5；式（8）",
    (
        ("gpm", "保温料和电阻料消耗量", "quantity", "t", "GPM"),
        ("gpmfc", "综合收到基固定碳含量", "percentage", "%", "GPMFC"),
        ("gta", "待石墨化品总量", "quantity", "t", "GTA"),
        ("gtafc", "待石墨化品收到基固定碳含量", "percentage", "%", "GTAFC"),
        ("gwt", "粉尘、碎屑、残块、副产品的碳输出", "quantity", "tC", "GWT"),
        ("gp", "石墨化品产量", "quantity", "t", "GP"),
        ("gpfc", "石墨化产品收到基固定碳含量", "percentage", "%", "GPFC"),
        ("gpmvar", "保温料和电阻料收到基挥发分含量", "percentage", "%", "GPMVar"),
    ),
)
_register_process_fields(
    "fume",
    "B.6；式（9）",
    (
        ("q", "进入焚烧炉烟气流量", "quantity", "Nm³/h", "Q"),
        ("qvar", "沥青烟焦油含量", "quantity", "mg/Nm³", "QVar"),
        ("hm", "沥青烟焦油低位发热量", "quantity", "GJ/t", "HM"),
        ("fch", "沥青烟焦油单位热值碳含量", "quantity", "tC/GJ", "FCh"),
        ("fox", "碳氧化率", "percentage", "%", "FOx"),
        ("duration", "报告期时长", "quantity", "d", "T"),
    ),
)
_register_process_fields(
    "fgd",
    "B.7；式（10）",
    (
        ("cal", "脱硫剂净消耗量", "quantity", "t", "CAL"),
        ("i", "碳酸盐含量", "percentage", "%", "I"),
        ("ef1", "碳酸盐完全转化排放因子", "quantity", "tCO₂/t", "EF1"),
        ("tr", "转化率", "percentage", "%", "TR"),
    ),
)


# 物料基准和成分性质控件。它们是高级字段，但仍然是正式 UI 输入。
for _prefix, _clause in (("calcination", "B.3；8.1"), ("baking", "B.4；8.1"), ("graphitization", "B.5；8.1")):
    for _item in (
        _spec(
            f"{_prefix}.mass_basis",
            "物料质量基准",
            FieldDataType.ENUM,
            required=True,
            help_text="质量基准必须与成分含量基准一致；项目计算统一归一至收到基。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.composition_basis",
            "成分含量基准",
            FieldDataType.ENUM,
            required=True,
            help_text="固定碳和挥发分含量的基准必须明确。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.normalized_basis",
            "收到基归一化基准",
            FieldDataType.ENUM,
            required=True,
            help_text="非收到基数据必须提供换算依据并统一到收到基。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.fixed_carbon_component_kind",
            "固定碳字段性质",
            FieldDataType.ENUM,
            required=True,
            help_text="本字段必须明确为固定碳，不能用总碳或挥发分替代。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.volatile_matter_component_kind",
            "挥发分字段性质",
            FieldDataType.ENUM,
            required=True,
            help_text="本字段必须明确为挥发分，不能与固定碳共用一个性质选择。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.moisture_evidence",
            "数据来源记录",
            FieldDataType.BOOLEAN,
            help_text="非收到基数据须有可追溯的数据来源记录。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.conversion_evidence",
            "换算依据记录",
            FieldDataType.BOOLEAN,
            help_text="非收到基数据须有可追溯的收到基换算依据。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
        _spec(
            f"{_prefix}.evidence_reference",
            "报告/台账编号或来源说明",
            FieldDataType.TEXT,
            help_text="填写报告、台账编号或来源说明；非收到基输入时必填。",
            standard_clause=_clause,
            source_location=_RECEIVED_BASIS,
            advanced=True,
        ),
    ):
        _register(_item)


# I01 多条电力明细：取得方式和电力属性是两个独立枚举维度。
for _item in (
    _spec("electricity.detail_id", "电力明细标识", FieldDataType.TEXT, required=True, standard_clause="B.8", source_location=_STANDARD),
    _spec("electricity.amount", "电量", FieldDataType.QUANTITY, unit="MWh", minimum=0, required=True, standard_clause="B.8；式（12）", source_location=_STANDARD),
    _spec("electricity.acquisition", "电力取得方式", FieldDataType.ENUM, required=True, help_text="外购和自发自用独立于电力属性。", standard_clause="B.8；电力参数规则", source_location=_STANDARD),
    _spec("electricity.attribute", "电力属性", FieldDataType.ENUM, required=True, help_text="常规、非化石能源和化石能源为每条明细的属性。", standard_clause="B.8；电力参数规则", source_location=_STANDARD),
    _spec("electricity.proof_type", "非化石电力证明材料类型", FieldDataType.ENUM, help_text="非化石能源电力须按取得方式提供对应材料。", standard_clause="B.8；电力参数规则", source_location=_STANDARD, advanced=True),
    _spec("electricity.proof_status", "非化石电力证明材料状态", FieldDataType.ENUM, help_text="材料无效或缺失时不得采用零因子。", standard_clause="B.8；电力参数规则", source_location=_STANDARD, advanced=True),
):
    _register(_item)


# I03 / I02 / I04 能源明细和标准参数选择。
for _item in (
    _spec("exported_electricity_id", "输出电力明细标识", FieldDataType.TEXT, standard_clause="B.8；式（15）", source_location=_STANDARD),
    _spec("exported_electricity_amount", "输出电量", FieldDataType.QUANTITY, unit="MWh", minimum=0, standard_clause="B.8；式（15）", source_location=_STANDARD),
    _spec("heat_id", "购入动力明细标识", FieldDataType.TEXT, standard_clause="B.9；式（13）", source_location=_STANDARD),
    _spec("heat_amount", "外购动力总量", FieldDataType.QUANTITY, unit="kg", minimum=0, standard_clause="B.9；式（13）", source_location=_STANDARD),
    _spec("heat_enthalpy", "蒸汽焓值", FieldDataType.QUANTITY, unit="kJ/kg", minimum=0, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD),
    _spec("heat_pressure", "蒸汽压力", FieldDataType.QUANTITY, unit="MPa", minimum=0, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD, advanced=True),
    _spec("heat_temperature", "过热蒸汽温度", FieldDataType.QUANTITY, unit="°C", minimum=0, standard_clause="附录 C.5；B.9", source_location=_STANDARD, advanced=True),
    _spec("heat_steam_kind", "蒸汽状态", FieldDataType.ENUM, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD),
    _spec("heat_factor", "热力排放因子", FieldDataType.READONLY_PARAMETER, unit="tCO₂/GJ", help_text="系统按核算期间自动推荐标准参数；需要更改时可打开高级选择。", standard_clause="附录 C.3；B.9", source_location=_STANDARD),
    _spec("heat_factor_selection_reason", "参数选择理由", FieldDataType.TEXT, help_text="需要改用其他适用值时填写选择理由。", standard_clause="参数选择规则；B.9", source_location=_STANDARD, advanced=True),
    _spec("exported_heat_id", "输出动力明细标识", FieldDataType.TEXT, standard_clause="B.9；式（15）", source_location=_STANDARD),
    _spec("exported_heat_amount", "输出动力总量", FieldDataType.QUANTITY, unit="kg", minimum=0, standard_clause="B.9；式（15）", source_location=_STANDARD),
    _spec("exported_heat_enthalpy", "输出蒸汽焓值", FieldDataType.QUANTITY, unit="kJ/kg", minimum=0, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD),
    _spec("exported_heat_pressure", "输出蒸汽压力", FieldDataType.QUANTITY, unit="MPa", minimum=0, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD, advanced=True),
    _spec("exported_heat_temperature", "输出过热蒸汽温度", FieldDataType.QUANTITY, unit="°C", minimum=0, standard_clause="附录 C.5；B.9", source_location=_STANDARD, advanced=True),
    _spec("exported_heat_steam_kind", "输出蒸汽状态", FieldDataType.ENUM, standard_clause="附录 C.4/C.5；B.9", source_location=_STANDARD),
):
    _register(_item)


CURRENT_UI_INPUT_KEYS = tuple(FIELD_SPECS)


def get_field_spec(internal_key: str) -> FieldSpec:
    try:
        return FIELD_SPECS[internal_key]
    except KeyError as exc:
        raise KeyError(f"没有为 UI 字段建立 FieldSpec：{internal_key}") from exc


def ui_to_domain_value(spec: FieldSpec, value: str | None) -> str | None:
    """Convert a display value to the unit expected by the Domain model."""

    if value is None or not value.strip():
        return None
    if spec.data_type is not FieldDataType.PERCENTAGE:
        return value.strip()
    try:
        return format(Decimal(value.strip()) / Decimal("100"), "f")
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{spec.internal_key} 不是合法百分数：{value}") from exc


def domain_to_ui_value(spec: FieldSpec, value: object) -> str:
    """Convert a Domain ratio value to the percentage shown in the UI."""

    if spec.data_type is not FieldDataType.PERCENTAGE:
        return str(value)
    try:
        return format(Decimal(str(value)) * Decimal("100"), "f")
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{spec.internal_key} 不是合法 Domain 比例：{value}") from exc


def numeric_field_specs() -> tuple[FieldSpec, ...]:
    return tuple(spec for spec in FIELD_SPECS.values() if spec.is_numeric)


__all__ = [
    "CURRENT_UI_INPUT_KEYS",
    "FIELD_SPECS",
    "FieldDataType",
    "FieldSpec",
    "SOURCE_LABELS",
    "domain_to_ui_value",
    "get_field_spec",
    "numeric_field_specs",
    "ui_to_domain_value",
]
