"""Runtime template and auditable XLSX ingress for GB/T 32151.34—2024.

This is an Infrastructure/Excel adapter. It produces standard-specific domain
inputs and delegates all business validation and arithmetic to the existing
Domain Calculator. It does not import Qt or persist Projects/Records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName

from packages.application.project_workspaces import AccountingUnitType
from packages.core.errors import DomainValidationError, IssueLevel
from packages.core.models import (
    AccountingPeriod,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
    PeriodType,
    ReviewStatus,
    ValueType,
)
from packages.core.parameter_resolution import (
    ElectricityConsumptionDetail,
    ParameterResolver,
)
from packages.standards.carbon_material import (
    STANDARD_ID,
    STANDARD_VERSION,
    ActivityDataEvidence,
    BakingInput,
    CalcinationInput,
    CarbonMaterialCalculationOutcome,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonReportingData,
    CarbonateComponent,
    EmissionSourceState,
    EmissionSourceStatus,
    ElectricityOutputLine,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatInput,
    MaterialBasis,
    MaterialComponentKind,
    MeasuredFactorEvidence,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
    InMemoryRecordRepository,
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


TEMPLATE_ID = "GHGTOOL_GBT_32151_34_2024"
TEMPLATE_VERSION = "1.0.0"
INGRESS_POLICY_ID = "GHGTOOL_EXCEL_INGRESS_V1"
METADATA_SHEET = "__metadata__"

SHEETS: Mapping[str, tuple[str, ...]] = {
    "说明": ("用途", "填写说明"),
    "核算单元": (
        "核算单元名称", "类型", "是否启用", "企业名称", "核算期间类型", "开始日期", "结束日期",
        "边界已确认", "边界说明", "其他行业活动", "上下游运输",
    ),
    "排放源": ("核算单元", "排放源", "状态"),
    "报告信息": (
        "核算单元", "单位性质", "所属行业", "统一社会信用代码", "法定代表人", "填报负责人",
        "负责人联系方式", "核算边界说明", "主要产品/工艺流程", "排放源识别说明", "其他报告说明",
    ),
    "化石燃料": (
        "核算单元", "燃料种类", "计量路径", "活动量", "单位热值含碳量", "碳氧化率",
        "低位发热量", "参数来源编号", "活动数据证据", "参数证据",
    ),
    "煅烧": (
        "核算单元", "实例名称", "GC 投入量（t）", "WFC 固定碳比例", "CC 煅后焦用量（t）",
        "UCC 外购煅后焦用量（t）", "DU 粉尘用量（t）", "WFC_C 煅后焦固定碳比例",
        "WVAR 挥发分比例", "WVAR_C 煅后焦挥发分比例", "K1", "质量基准", "成分基准",
        "折算基准", "固定碳成分性质", "水分修正证据", "基准换算证据", "碳输出计入投入",
        "活动数据证据", "参数证据",
    ),
    "焙烧炭化": (
        "核算单元", "实例名称", "BPM 生坯用量（t）", "BPMFC 生坯固定碳比例", "BG 焦粉用量（t）",
        "BGFC 焦粉固定碳比例", "BWT 焦油沥青用量（tC）", "BP 石油焦用量（t）",
        "BPFC 石油焦固定碳比例", "BPMVAR 生坯挥发分比例", "BGVAR 焦粉挥发分比例", "K2",
        "质量基准", "成分基准", "折算基准", "固定碳成分性质", "水分修正证据", "基准换算证据",
        "碳输出计入投入", "活动数据证据", "参数证据",
    ),
    "石墨化": (
        "核算单元", "实例名称", "GPM 生坯用量（t）", "GPMFC 生坯固定碳比例", "GTA 焦油沥青用量（t）",
        "GTAFC 焦油沥青固定碳比例", "GWT 焦油用量（tC）", "GP 石油焦用量（t）",
        "GPFC 石油焦固定碳比例", "GPMVAR 生坯挥发分比例", "K3", "质量基准", "成分基准",
        "折算基准", "固定碳成分性质", "水分修正证据", "基准换算证据", "炉损计入",
        "活动数据证据", "参数证据",
    ),
    "烟气焚烧": (
        "核算单元", "实例名称", "Q 烟气流量（Nm³/h）", "QVAR 烟气含碳量（mg/Nm³）",
        "HM 低位发热量（GJ/t）", "FCH 单位热值含碳量（tC/GJ）", "FOX 碳氧化率",
        "运行时间（d）", "参数来源编号", "活动数据证据", "参数证据",
    ),
    "烟气脱硫": (
        "核算单元", "设施名称", "碳酸盐种类", "碳酸盐用量（t）", "碳酸盐含量比例",
        "排放因子（tCO₂/t）", "转化率", "参数来源编号", "活动数据证据", "参数证据",
    ),
    "电力": (
        "核算单元", "方向", "电量（MWh）", "取得方式", "电力属性", "证明类型", "证明状态",
        "排放因子（tCO₂/MWh）", "参数来源编号", "活动数据证据", "参数证据",
    ),
    "热力": (
        "核算单元", "方向", "热力数量（kg）", "蒸汽类型", "焓值（kJ/kg）", "压力（MPa）",
        "温度（℃）", "排放因子（tCO₂/GJ）", "参数来源编号", "活动数据证据", "参数证据",
    ),
    "证据来源": (
        "核算单元", "证据名称", "证据类别", "适用范围", "关联排放源", "来源编号", "监测地点",
        "监测/取样方法", "仪器", "精度", "记录/取样频次", "取得/检测时间", "引用标准", "说明",
    ),
    METADATA_SHEET: ("key", "value"),
}

REQUIRED_SHEETS = frozenset(SHEETS)

SOURCE_LABELS: Mapping[str, str] = {
    SOURCE_FUEL: "化石燃料",
    SOURCE_CALCINATION: "煅烧",
    SOURCE_BAKING: "焙烧/炭化",
    SOURCE_GRAPHITIZATION: "石墨化",
    SOURCE_FUME: "烟气焚烧",
    SOURCE_FGD: "烟气脱硫",
    SOURCE_PURCHASED_ELECTRICITY: "购入电力",
    SOURCE_EXPORTED_ELECTRICITY: "输出电力",
    SOURCE_PURCHASED_HEAT: "购入热力",
    SOURCE_EXPORTED_HEAT: "输出热力",
}
SOURCE_IDS = tuple(SOURCE_LABELS)
LABEL_TO_SOURCE = {label: source_id for source_id, label in SOURCE_LABELS.items()}

UNIT_TYPE_LABELS = {
    "全厂": AccountingUnitType.WHOLE_SITE,
    "工序": AccountingUnitType.PROCESS,
    "其他": AccountingUnitType.OTHER,
}
FUEL_TYPE_LABELS: Mapping[str, FuelType] = {
    "无烟煤": FuelType.ANTHRACITE,
    "烟煤": FuelType.BITUMINOUS_COAL,
    "褐煤": FuelType.LIGNITE,
    "洗精煤": FuelType.CLEANED_COAL,
    "其他洗煤": FuelType.OTHER_CLEANED_COAL,
    "型煤": FuelType.BRIQUETTE,
    "其他煤制品": FuelType.OTHER_COAL_PRODUCTS,
    "焦炭": FuelType.COKE,
    "石油焦": FuelType.PETROLEUM_COKE,
    "原油": FuelType.CRUDE_OIL,
    "燃料油": FuelType.FUEL_OIL,
    "汽油": FuelType.GASOLINE,
    "柴油": FuelType.DIESEL,
    "一般煤油": FuelType.KEROSENE,
    "液化天然气": FuelType.LIQUEFIED_NATURAL_GAS,
    "液化石油气": FuelType.LIQUEFIED_PETROLEUM_GAS,
    "石脑油": FuelType.NAPHTHA,
    "焦油": FuelType.TAR,
    "粗苯": FuelType.CRUDE_BENZENE,
    "天然气": FuelType.NATURAL_GAS,
    "高炉煤气": FuelType.BLAST_FURNACE_GAS,
    "转炉煤气": FuelType.CONVERTER_GAS,
    "焦炉煤气": FuelType.COKE_OVEN_GAS,
    "炼厂干气": FuelType.REFINERY_DRY_GAS,
    "其他煤气": FuelType.OTHER_GAS,
    "煤（需选择具体煤种）": FuelType.COAL,
    "其他燃料（无统一标准缺省值）": FuelType.OTHER,
}
FUEL_LABEL_BY_TYPE = {value: key for key, value in FUEL_TYPE_LABELS.items()}
FUEL_C1_SUBJECT_IDS = {
    fuel_type: fuel_type.value.lower()
    for fuel_type in FuelType
    if fuel_type not in {FuelType.COAL, FuelType.OTHER}
}
FUEL_PATH_LABELS = {"体积": FuelPath.VOLUME, "质量": FuelPath.MASS, "热量": FuelPath.HEAT}
PERIOD_LABELS = {"年度": PeriodType.ANNUAL, "月度": PeriodType.MONTHLY, "自定义": PeriodType.CUSTOM}
YES_NO = {"是": True, "否": False}
SOURCE_STATE_LABELS = {
    "涉及": EmissionSourceStatus.INVOLVED,
    "不涉及": EmissionSourceStatus.NOT_INVOLVED,
    "待确认": EmissionSourceStatus.UNCONFIRMED,
}
CARBONATE_LABELS = {
    "CaCO₃": "car-par-c2-caco3", "MgCO₃": "car-par-c2-mgco3", "Na₂CO₃": "car-par-c2-na2co3",
    "NaHCO₃": "car-par-c2-nahco3", "FeCO₃": "car-par-c2-feco3", "MnCO₃": "car-par-c2-mnco3",
    "BaCO₃": "car-par-c2-baco3", "Li₂CO₃": "car-par-c2-li2co3", "K₂CO₃": "car-par-c2-k2co3",
    "SrCO₃": "car-par-c2-srco3", "CaMg(CO₃)₂": "car-par-c2-camgco3-2",
}
CARBONATE_LABEL_BY_PARAMETER = {value: key for key, value in CARBONATE_LABELS.items()}

PROCESS_SHEETS: Mapping[str, tuple[type, tuple[str, ...], tuple[str, ...], str]] = {
    "煅烧": (CalcinationInput, ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c", "k1"), ("GC 投入量（t）", "WFC 固定碳比例", "CC 煅后焦用量（t）", "UCC 外购煅后焦用量（t）", "DU 粉尘用量（t）", "WFC_C 煅后焦固定碳比例", "WVAR 挥发分比例", "WVAR_C 煅后焦挥发分比例", "K1"), SOURCE_CALCINATION),
    "焙烧炭化": (BakingInput, ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar", "k2"), ("BPM 生坯用量（t）", "BPMFC 生坯固定碳比例", "BG 焦粉用量（t）", "BGFC 焦粉固定碳比例", "BWT 焦油沥青用量（tC）", "BP 石油焦用量（t）", "BPFC 石油焦固定碳比例", "BPMVAR 生坯挥发分比例", "BGVAR 焦粉挥发分比例", "K2"), SOURCE_BAKING),
    "石墨化": (GraphitizationInput, ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar", "k3"), ("GPM 生坯用量（t）", "GPMFC 生坯固定碳比例", "GTA 焦油沥青用量（t）", "GTAFC 焦油沥青固定碳比例", "GWT 焦油用量（tC）", "GP 石油焦用量（t）", "GPFC 石油焦固定碳比例", "GPMVAR 生坯挥发分比例", "K3"), SOURCE_GRAPHITIZATION),
}


class WorkbookFatalError(ValueError):
    """The workbook cannot safely be interpreted as this supported template."""


@dataclass(frozen=True, slots=True)
class WorkbookProvenance:
    workbook_sha256: str
    template_id: str
    template_version: str
    standard_id: str
    standard_version: str
    ingress_policy_id: str
    imported_at: datetime


@dataclass(frozen=True, slots=True)
class NumericCellEvidence:
    sheet: str
    cell: str
    raw_cell_type: str
    workbook_value_repr: str
    serialized_numeric_text: str
    normalized_decimal: Decimal


@dataclass(frozen=True, slots=True)
class ImportMessage:
    code: str
    message: str
    location: str | None = None


@dataclass(frozen=True, slots=True)
class UnitCalculationPreview:
    unit_id: str
    name: str
    unit_type: AccountingUnitType
    input_value: CarbonMaterialInput | None
    calculation: CarbonMaterialCalculationOutcome | None
    errors: tuple[ImportMessage, ...] = ()
    warnings: tuple[ImportMessage, ...] = ()

    @property
    def can_calculate(self) -> bool:
        return self.input_value is not None and self.calculation is not None and self.calculation.successful and not self.errors

    @property
    def result(self):
        return self.calculation.result if self.can_calculate and self.calculation else None


@dataclass(frozen=True, slots=True)
class WorkbookImportPreview:
    provenance: WorkbookProvenance
    units: tuple[UnitCalculationPreview, ...]
    warnings: tuple[ImportMessage, ...]
    numeric_evidence: tuple[NumericCellEvidence, ...]


def _dv_list(sheet, formula: str, *, cells: str) -> None:
    validation = DataValidation(type="list", formula1=formula, allow_blank=True)
    validation.errorTitle = "请选择列表中的业务选项"
    validation.error = "请使用下拉选项；导入时仍会重新校验。"
    sheet.add_data_validation(validation)
    validation.add(cells)


def _prepare_sheet(sheet, headers: Sequence[str]) -> None:
    sheet.append(headers)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{sheet.cell(1, len(headers)).coordinate}1"
    sheet.row_dimensions[1].height = 34
    for cell in sheet[1]:
        cell.font = Font(name="Microsoft YaHei", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="176B64")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for index, header in enumerate(headers, start=1):
        sheet.column_dimensions[sheet.cell(1, index).column_letter].width = min(max(len(header) * 2.2, 16), 34)


def create_template_bytes() -> bytes:
    """Generate the current `.xlsx` template in memory at runtime."""

    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, headers in SHEETS.items():
        sheet = workbook.create_sheet(name)
        _prepare_sheet(sheet, headers)

    workbook["说明"].append(("模板用途", "GB/T 32151.34—2024 一个标准一套模板；可登记多个独立核算单元。"))
    workbook["说明"].append(("核算单元", "填写全厂、工序或其他；每个单元单独校验和预览，不跨单元汇总。"))
    workbook["说明"].append(("排放源状态", "每个启用单元必须为十类排放源逐项选择“涉及 / 不涉及 / 待确认”。"))
    workbook["说明"].append(("数值输入", "数值必须录入 Excel 数值单元格，最多 15 位有效数字；比例按实际 0～1 数值录入。"))
    workbook["说明"].append(("公式与文本", "正式数值不接受公式、文本数字或推测性清洗；请粘贴为数值。"))
    workbook["说明"].append(("参数来源", "标准参数可留空由现有 Canonical 参数解析；企业实测/指定值须登记可追溯来源。"))
    workbook["说明"].append(("多余数据", "未启用/不涉及/无法关联单元的数据会忽略并给出警告；有效单元可继续预览。"))
    workbook["说明"].append(("Evidence", "在“证据来源”登记一次，再在业务明细的证据引用列填写证据名称。"))
    workbook["说明"].append(("边界", "预览不保存项目或正式核算记录；RS03-B 再实现正式导入闭环。"))

    workbook["__metadata__"].append(("template_id", TEMPLATE_ID))
    workbook["__metadata__"].append(("template_version", TEMPLATE_VERSION))
    workbook["__metadata__"].append(("standard_id", STANDARD_ID))
    workbook["__metadata__"].append(("standard_version", STANDARD_VERSION))
    workbook["__metadata__"].append(("ingress_policy_id", INGRESS_POLICY_ID))
    workbook["__metadata__"].sheet_state = "hidden"

    workbook.defined_names.add(DefinedName("UnitNames", attr_text="'核算单元'!$A$2:$A$500"))
    for sheet_name in ("排放源", "报告信息", "化石燃料", "煅烧", "焙烧炭化", "石墨化", "烟气焚烧", "烟气脱硫", "电力", "热力", "证据来源"):
        sheet = workbook[sheet_name]
        _dv_list(sheet, "=UnitNames", cells=f"A2:A500")
    _dv_list(workbook["核算单元"], '"全厂,工序,其他"', cells="B2:B500")
    _dv_list(workbook["核算单元"], '"是,否"', cells="C2:C500")
    _dv_list(workbook["核算单元"], '"年度,月度,自定义"', cells="E2:E500")
    _dv_list(workbook["核算单元"], '"是,否"', cells="H2:H500")
    _dv_list(workbook["核算单元"], '"是,否"', cells="J2:K500")
    _dv_list(workbook["排放源"], '"化石燃料,煅烧,焙烧/炭化,石墨化,烟气焚烧,烟气脱硫,购入电力,输出电力,购入热力,输出热力"', cells="B2:B500")
    _dv_list(workbook["排放源"], '"涉及,不涉及,待确认"', cells="C2:C500")
    _dv_list(workbook["化石燃料"], '"' + ",".join(FUEL_TYPE_LABELS) + '"', cells="B2:B500")
    _dv_list(workbook["化石燃料"], '"体积,质量,热量"', cells="C2:C500")
    for name in PROCESS_SHEETS:
        process_sheet = workbook[name]
        _dv_list(process_sheet, '"收到基,干燥基,其他已记录基准"', cells="L2:M500" if name != "石墨化" else "L2:M500")
        _dv_list(process_sheet, '"收到基,其他已记录基准"', cells="N2:N500")
        _dv_list(process_sheet, '"固定碳,总碳,未知"', cells="O2:O500")
        _dv_list(process_sheet, '"是,否"', cells=("R2:R500" if name == "石墨化" else "R2:R500"))
    _dv_list(workbook["烟气焚烧"], '"是,否"', cells="G2:G500")
    _dv_list(workbook["烟气脱硫"], '"' + ",".join(CARBONATE_LABELS) + '"', cells="C2:C500")
    _dv_list(workbook["电力"], '"购入,输出"', cells="B2:B500")
    _dv_list(workbook["电力"], '"购入,自发自用"', cells="D2:D500")
    _dv_list(workbook["电力"], '"常规,非化石,化石"', cells="E2:E500")
    _dv_list(workbook["电力"], '"无,合同和结算,GEC,月度原始记录"', cells="F2:F500")
    _dv_list(workbook["电力"], '"未提供,有效,无效"', cells="G2:G500")
    _dv_list(workbook["热力"], '"购入,输出"', cells="B2:B500")
    _dv_list(workbook["热力"], '"饱和蒸汽,过热蒸汽"', cells="D2:D500")
    _dv_list(workbook["证据来源"], '"活动数据,参数因子"', cells="C2:C500")

    ratio_columns = {
        "化石燃料": ("F",), "煅烧": ("D", "H", "I", "J"), "焙烧炭化": ("D", "F", "I", "J", "K"),
        "石墨化": ("D", "F", "I", "J"), "烟气焚烧": ("G",), "烟气脱硫": ("E", "G"),
    }
    for sheet_name, columns in ratio_columns.items():
        sheet = workbook[sheet_name]
        for column in columns:
            validation = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True)
            validation.errorTitle = "比例范围为 0～1"
            validation.error = "请录入 0 到 1 之间的实际比例数值。"
            sheet.add_data_validation(validation)
            validation.add(f"{column}2:{column}500")
            for row in range(2, 501):
                sheet[f"{column}{row}"].number_format = "0.00%"

    for sheet in workbook.worksheets:
        if sheet.title != METADATA_SHEET:
            sheet.sheet_view.showGridLines = False
            if sheet.title != "说明":
                for row in sheet.iter_rows(min_row=2, max_row=200, max_col=sheet.max_column):
                    for cell in row:
                        cell.fill = PatternFill("solid", fgColor="FFF2CC")
                        cell.alignment = Alignment(vertical="center")
    numeric_columns = {
        "化石燃料": ("D", "E", "F", "G"),
        "煅烧": ("C", "D", "E", "F", "G", "H", "I", "J", "K"),
        "焙烧炭化": ("C", "D", "E", "F", "G", "H", "I", "J", "K", "L"),
        "石墨化": ("C", "D", "E", "F", "G", "H", "I", "J", "K"),
        "烟气焚烧": ("C", "D", "E", "F", "G", "H"),
        "烟气脱硫": ("D", "E", "F", "G"),
        "电力": ("C", "H"),
        "热力": ("C", "E", "F", "G", "H"),
    }
    ratio_cells = {
        "化石燃料": {"F"}, "煅烧": {"D", "H", "I", "J", "K"},
        "焙烧炭化": {"D", "F", "I", "J", "K", "L"},
        "石墨化": {"D", "F", "I", "J", "K"}, "烟气焚烧": {"G"},
        "烟气脱硫": {"E", "G"},
    }
    for sheet_name, columns in numeric_columns.items():
        for column in columns:
            if column in ratio_cells.get(sheet_name, set()):
                continue
            validation = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
            validation.errorTitle = "数值不能为负"
            validation.error = "请录入非负数值；导入时仍会重新校验。"
            workbook[sheet_name].add_data_validation(validation)
            validation.add(f"{column}2:{column}500")
    import io
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def write_template(destination: str | Path) -> Path:
    """Write a freshly generated template to the user-selected destination."""

    path = Path(destination)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("模板文件扩展名必须为 .xlsx")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(create_template_bytes())
    return path


def significant_digit_count(value: Decimal) -> int:
    """Count coefficient digits, excluding sign/decimal/exponent and leading zeroes.

    Trailing zeroes present in the serialized XLSX numeric token count as
    significant. Zero itself counts as one digit.
    """

    if not value.is_finite():
        raise ValueError("numeric value must be finite")
    digits = list(value.as_tuple().digits)
    while len(digits) > 1 and digits[0] == 0:
        digits.pop(0)
    return len(digits) if any(digits) else 1


_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def _worksheet_xml_paths(archive: ZipFile) -> dict[str, str]:
    workbook_root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    rels_root = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        node.attrib["Id"]: node.attrib["Target"]
        for node in rels_root.findall(f"{{{_NS_PKG_REL}}}Relationship")
    }
    paths: dict[str, str] = {}
    for node in workbook_root.findall(f"{{{_NS_MAIN}}}sheets/{{{_NS_MAIN}}}sheet"):
        sheet_name = node.attrib["name"]
        target = rel_targets[node.attrib[f"{{{_NS_REL}}}id"]]
        if target.startswith("/"):
            path = target.lstrip("/")
        elif target.startswith("xl/"):
            path = target
        else:
            path = f"xl/{target}"
        paths[sheet_name] = path
    return paths


def _serialized_numeric_values(source: bytes) -> dict[tuple[str, str], str]:
    """Read numeric `<v>` text from the actual stored worksheet XML."""

    values: dict[tuple[str, str], str] = {}
    import io
    with ZipFile(io.BytesIO(source)) as archive:
        for sheet_name, member in _worksheet_xml_paths(archive).items():
            root = ElementTree.fromstring(archive.read(member))
            for cell in root.findall(f".//{{{_NS_MAIN}}}c"):
                ref = cell.attrib.get("r")
                if not ref or cell.attrib.get("t") not in (None, "n"):
                    continue
                value_node = cell.find(f"{{{_NS_MAIN}}}v")
                if value_node is not None and value_node.text is not None:
                    values[(sheet_name, ref)] = value_node.text
    return values


@dataclass(slots=True)
class _UnitContext:
    name: str
    unit_id: str
    unit_type: AccountingUnitType
    enterprise_id: str
    enterprise_name: str
    period: AccountingPeriod | None
    boundary_confirmed: bool
    boundary_components: tuple[str, ...]
    other_activity: bool
    transport: bool
    source_states: dict[str, EmissionSourceStatus] = field(default_factory=dict)
    errors: list[ImportMessage] = field(default_factory=list)
    warnings: list[ImportMessage] = field(default_factory=list)
    payloads: dict[str, list[object]] = field(default_factory=dict)
    report_values: dict[str, str | None] = field(default_factory=dict)
    activity_evidence: list[ActivityDataEvidence] = field(default_factory=list)
    factor_evidence: list[MeasuredFactorEvidence] = field(default_factory=list)
    evidence_names: dict[str, str] = field(default_factory=dict)


class _CellReader:
    def __init__(self, numeric_xml: Mapping[tuple[str, str], str]):
        self.numeric_xml = numeric_xml
        self.evidence: list[NumericCellEvidence] = []

    @staticmethod
    def location(sheet: str, row: int, column: int) -> str:
        from openpyxl.utils import get_column_letter
        return f"{sheet}!{get_column_letter(column)}{row}"

    def error(self, ctx: _UnitContext, code: str, message: str, location: str) -> None:
        ctx.errors.append(ImportMessage(code, message, location))

    def number(
        self,
        ctx: _UnitContext,
        sheet: str,
        row: int,
        cell,
        *,
        required: bool = False,
    ) -> Decimal | None:
        location = f"{sheet}!{cell.coordinate}"
        value = cell.value
        if cell.data_type == "f":
            self.error(ctx, "EXCEL-FORMULA-REJECTED", "正式核算输入不接受公式单元格，请复制并粘贴为数值后重新导入。", location)
            return None
        serialized = self.numeric_xml.get((sheet, cell.coordinate))
        if value is None and serialized is None:
            if required:
                self.error(ctx, "EXCEL-NUMBER-REQUIRED", "此数值为必填项。", location)
            return None
        if cell.data_type != "n" or isinstance(value, (bool, date, datetime)):
            self.error(ctx, "EXCEL-NUMBER-CELL-REQUIRED", "此字段必须是 Excel 数值单元格；文本数字、公式和日期均不接受。", location)
            return None
        if serialized is None:
            self.error(ctx, "EXCEL-NUMERIC-SERIALIZATION-MISSING", "无法取得工作簿保存的数值单元格证据。", location)
            return None
        try:
            normalized = Decimal(serialized)
        except InvalidOperation:
            self.error(ctx, "EXCEL-NUMBER-INVALID", "此数值单元格不是有效的十进制数。", location)
            return None
        if not normalized.is_finite():
            self.evidence.append(NumericCellEvidence(
                sheet, cell.coordinate, cell.data_type, repr(value), serialized, normalized,
            ))
            self.error(ctx, "EXCEL-NUMBER-NONFINITE", "NaN 和 Infinity 不能作为正式核算数值。", location)
            return None
        self.evidence.append(NumericCellEvidence(
            sheet=sheet,
            cell=cell.coordinate,
            raw_cell_type=cell.data_type,
            workbook_value_repr=repr(value),
            serialized_numeric_text=serialized,
            normalized_decimal=normalized,
        ))
        digits = significant_digit_count(normalized)
        if digits > 15:
            self.error(ctx, "EXCEL-NUMBER-SIGNIFICANT-DIGITS", f"此数值有 {digits} 位有效数字，Excel 导入最多接受 15 位；不会自动舍入或截断。", location)
            return None
        return normalized

    def text(
        self,
        ctx: _UnitContext,
        sheet: str,
        cell,
        *,
        required: bool = False,
    ) -> str | None:
        location = f"{sheet}!{cell.coordinate}"
        value = cell.value
        if cell.data_type == "f":
            self.error(ctx, "EXCEL-FORMULA-REJECTED", "正式核算输入不接受公式单元格，请复制并粘贴为数值后重新导入。", location)
            return None
        if value is None:
            if required:
                self.error(ctx, "EXCEL-TEXT-REQUIRED", "此字段为必填项。", location)
            return None
        if not isinstance(value, str):
            self.error(ctx, "EXCEL-TEXT-CELL-REQUIRED", "此字段必须以文字填写。", location)
            return None
        value = value.strip()
        if not value and required:
            self.error(ctx, "EXCEL-TEXT-REQUIRED", "此字段为必填项。", location)
        return value or None


def _read_headers(workbook, sheet_name: str) -> tuple[object, ...]:
    sheet = workbook[sheet_name]
    return tuple(cell.value for cell in sheet[1])


def _cell_for(sheet, row: int, header: str):
    for column, cell in enumerate(sheet[row], start=1):
        if column > sheet.max_column:
            break
        if sheet.cell(1, column).value == header:
            return cell
    raise WorkbookFatalError(f"工作表“{sheet.title}”缺少列“{header}”")


def _row_blank(sheet, row: int) -> bool:
    return not any(cell.value is not None for cell in sheet[row])


def _rows(sheet) -> Iterable[int]:
    for row in range(2, sheet.max_row + 1):
        if not _row_blank(sheet, row):
            yield row


def _location(sheet: str, row: int, header: str, workbook) -> str:
    return f"{sheet}!{_cell_for(workbook[sheet], row, header).coordinate}"


def _date_value(reader: _CellReader, ctx: _UnitContext, sheet, row: int, header: str) -> date | None:
    cell = _cell_for(sheet, row, header)
    if cell.data_type == "f":
        reader.error(ctx, "EXCEL-FORMULA-REJECTED", "正式核算输入不接受公式单元格，请复制并粘贴为数值后重新导入。", f"{sheet.title}!{cell.coordinate}")
        return None
    value = cell.value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    reader.error(ctx, "EXCEL-DATE-INVALID", "日期请使用 Excel 日期单元格或 YYYY-MM-DD。", f"{sheet.title}!{cell.coordinate}")
    return None


def _enum_value(
    reader: _CellReader,
    ctx: _UnitContext,
    sheet,
    row: int,
    header: str,
    mapping: Mapping[str, object],
    *,
    required: bool = False,
):
    cell = _cell_for(sheet, row, header)
    value = reader.text(ctx, sheet.title, cell, required=required)
    if value is None:
        return None
    result = mapping.get(value)
    if result is None:
        reader.error(ctx, "EXCEL-OPTION-INVALID", f"“{header}”的值不在模板选项中。", f"{sheet.title}!{cell.coordinate}")
    return result


def _split_refs(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(dict.fromkeys(item.strip() for item in re.split(r"[;,，；、\n]", value) if item.strip()))


def _parse_metadata(workbook) -> dict[str, str]:
    sheet = workbook[METADATA_SHEET]
    metadata: dict[str, str] = {}
    for row in _rows(sheet):
        key, value = sheet.cell(row, 1).value, sheet.cell(row, 2).value
        if isinstance(key, str) and isinstance(value, str):
            metadata[key] = value
    return metadata


def _factor_for(resolver: ParameterResolver | None, parameter_id: str, period: AccountingPeriod | None):
    if resolver is None:
        return None
    try:
        factors = resolver.repository.list_factors(parameter_id)
    except (AttributeError, TypeError):
        return None
    matches = [
        factor for factor in factors
        if factor.parameter_id == parameter_id
        and STANDARD_ID in factor.applicable_standard_ids
        and factor.review_status is ReviewStatus.VERIFIED
        and factor.value_type in {ValueType.STANDARD_DEFAULT, ValueType.STANDARD_SPECIFIED}
        and not (
            period is not None and (
                (factor.valid_from is not None and factor.valid_from > period.end)
                or (factor.valid_to is not None and factor.valid_to < period.start)
                or (period.period_type is PeriodType.CUSTOM and (
                    (factor.valid_from is not None and period.start < factor.valid_from)
                    or (factor.valid_to is not None and period.end > factor.valid_to)
                ))
            )
        )
    ]
    return sorted(matches, key=lambda factor: factor.factor_id)[0] if matches else None


_PARAMETER_SOURCE_KINDS = {
    ValueType.STANDARD_DEFAULT: ParameterSourceKind.STANDARD_DEFAULT,
    ValueType.STANDARD_SPECIFIED: ParameterSourceKind.STANDARD_SPECIFIED,
    ValueType.GOVERNMENT_PUBLISHED: ParameterSourceKind.OFFICIAL_PUBLISHED,
    ValueType.MEASURED: ParameterSourceKind.MEASURED,
    ValueType.DERIVED: ParameterSourceKind.CALCULATED,
    ValueType.SYSTEM_CONSTANT: ParameterSourceKind.CALCULATED,
    ValueType.SCIENTIFIC_REFERENCE: ParameterSourceKind.USER_DEFINED,
    ValueType.HISTORICAL: ParameterSourceKind.USER_DEFINED,
}


def _parameter_from_factor(factor, reason: str) -> ParameterValue | None:
    if factor is None:
        return None
    return ParameterValue(
        parameter_id=factor.parameter_id,
        value=factor.value,
        unit=factor.unit,
        source_kind=_PARAMETER_SOURCE_KINDS[factor.value_type],
        source_id=factor.source_id,
        source_version=str(factor.version),
        source_location=factor.source_location,
        selection_reason=reason,
        factor_id=factor.factor_id,
        factor_year=factor.factor_year,
    )


def _make_parameter(
    value: Decimal | None,
    *,
    parameter_id: str,
    unit: str,
    source_reference: str | None,
    evidence_ids: tuple[str, ...],
    default: ParameterValue | None,
    ctx: _UnitContext,
    location: str,
) -> ParameterValue | None:
    if value is None:
        return default
    if default is not None and value == default.value and not source_reference:
        return default
    if not source_reference:
        ctx.errors.append(ImportMessage("EXCEL-PARAMETER-SOURCE-REQUIRED", "企业实测或自定义参数必须填写可追溯的参数来源编号。", location))
        return ParameterValue(parameter_id, value, unit, ParameterSourceKind.USER_DEFINED, None, None, None, "用户提供的参数值。", evidence_ref_ids=evidence_ids)
    return ParameterValue(
        parameter_id,
        value,
        unit,
        ParameterSourceKind.MEASURED,
        f"USER-EXCEL-{hashlib.sha256(source_reference.encode('utf-8')).hexdigest()[:12]}",
        "user-input",
        f"企业实测/技术资料编号：{source_reference}",
        f"用户提供并引用来源编号：{source_reference}。",
        evidence_ref_ids=evidence_ids,
    )


def _stable_token(prefix: str, *parts: object) -> str:
    payload = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def _collect_evidence(
    workbook,
    contexts: Mapping[str, _UnitContext],
    reader: _CellReader,
    global_warnings: list[ImportMessage],
) -> None:
    sheet = workbook["证据来源"]
    fields = {
        "单位性质": "organization_nature", "所属行业": "industry", "统一社会信用代码": "social_credit_code",
        "法定代表人": "legal_representative", "填报负责人": "preparer_name", "负责人联系方式": "preparer_contact",
        "核算边界说明": "boundary_description", "主要产品/工艺流程": "products_and_process",
        "排放源识别说明": "emission_source_identification", "其他报告说明": "other_report_information",
    }
    for row in _rows(sheet):
        raw_name = sheet.cell(row, 1).value
        if not isinstance(raw_name, str) or not raw_name.strip():
            if any(cell.value is not None for cell in sheet[row][1:]):
                global_warnings.append(ImportMessage("EXCEL-ORPHAN-EVIDENCE", "证据行未填写核算单元，已忽略。", f"证据来源!A{row}"))
            continue
        name = raw_name.strip()
        ctx = contexts.get(name)
        if ctx is None:
            global_warnings.append(ImportMessage("EXCEL-ORPHAN-EVIDENCE", f"证据行无法关联到启用核算单元“{name}”，已忽略。", f"证据来源!A{row}"))
            continue
        ref_name = reader.text(ctx, sheet.title, _cell_for(sheet, row, "证据名称"), required=True)
        kind = _enum_value(reader, ctx, sheet, row, "证据类别", {"活动数据": "activity", "参数因子": "factor"}, required=True)
        if ref_name is None or kind is None:
            continue
        evidence_id = _stable_token("ev", ctx.unit_id, row, ref_name)
        if ref_name in ctx.evidence_names:
            reader.error(ctx, "EXCEL-EVIDENCE-DUPLICATE", f"证据名称“{ref_name}”在该核算单元内重复。", f"证据来源!B{row}")
            continue
        ctx.evidence_names[ref_name] = evidence_id
        applies_to = reader.text(ctx, sheet.title, _cell_for(sheet, row, "适用范围")) or "本单元所选排放源"
        source_reference = reader.text(ctx, sheet.title, _cell_for(sheet, row, "来源编号"))
        source_labels = _split_refs(reader.text(ctx, sheet.title, _cell_for(sheet, row, "关联排放源")))
        source_ids: list[str] = []
        for source_label in source_labels:
            source_id = LABEL_TO_SOURCE.get(source_label)
            if source_id is None:
                reader.error(ctx, "EXCEL-EVIDENCE-SOURCE-INVALID", f"证据关联排放源“{source_label}”不在支持列表中。", f"证据来源!E{row}")
            else:
                source_ids.append(source_id)
        monitoring_location = reader.text(ctx, sheet.title, _cell_for(sheet, row, "监测地点"))
        method = reader.text(ctx, sheet.title, _cell_for(sheet, row, "监测/取样方法"))
        instrument = reader.text(ctx, sheet.title, _cell_for(sheet, row, "仪器"))
        accuracy = reader.text(ctx, sheet.title, _cell_for(sheet, row, "精度"))
        frequency = reader.text(ctx, sheet.title, _cell_for(sheet, row, "记录/取样频次"))
        acquisition_time = reader.text(ctx, sheet.title, _cell_for(sheet, row, "取得/检测时间"))
        referenced_standard = reader.text(ctx, sheet.title, _cell_for(sheet, row, "引用标准"))
        note = reader.text(ctx, sheet.title, _cell_for(sheet, row, "说明"))
        if kind == "activity":
            ctx.activity_evidence.append(ActivityDataEvidence(
                evidence_id=evidence_id,
                applies_to=applies_to,
                source_ids=tuple(source_ids),
                source_reference=source_reference,
                monitoring_location=monitoring_location,
                monitoring_method=method,
                instrument=instrument,
                accuracy=accuracy,
                recording_frequency=frequency,
                acquisition_time=acquisition_time,
                note=note,
            ))
        else:
            ctx.factor_evidence.append(MeasuredFactorEvidence(
                evidence_id=evidence_id,
                applies_to=applies_to,
                source_ids=tuple(source_ids),
                source_reference=source_reference,
                sampling_method=method,
                sampling_frequency=frequency,
                testing_method=method,
                testing_frequency=frequency,
                referenced_standard=referenced_standard,
                reason=note,
            ))

    report_sheet = workbook["报告信息"]
    for row in _rows(report_sheet):
        unit_name = reader.text(_ctx_placeholder(), report_sheet.title, _cell_for(report_sheet, row, "核算单元"))
        if not unit_name:
            if any(cell.value is not None for cell in report_sheet[row][1:]):
                global_warnings.append(ImportMessage("EXCEL-ORPHAN-REPORT", "报告信息未填写核算单元，已忽略。", f"报告信息!A{row}"))
            continue
        ctx = contexts.get(unit_name)
        if ctx is None:
            global_warnings.append(ImportMessage("EXCEL-ORPHAN-REPORT", f"报告信息无法关联到启用核算单元“{unit_name}”，已忽略。", f"报告信息!A{row}"))
            continue
        if ctx.report_values:
            ctx.errors.append(ImportMessage("EXCEL-REPORT-DUPLICATE", "同一核算单元的报告信息只能填写一行。", f"报告信息!A{row}"))
            continue
        for header, field_name in fields.items():
            ctx.report_values[field_name] = reader.text(ctx, report_sheet.title, _cell_for(report_sheet, row, header))


def _ctx_placeholder() -> _UnitContext:
    """Scratch context for a row that can only be reported globally."""

    return _UnitContext("", "", AccountingUnitType.OTHER, "", "", None, False, (), False, False)


def _load_unit_contexts(
    workbook,
    workbook_sha: str,
    reader: _CellReader,
    global_warnings: list[ImportMessage],
) -> tuple[dict[str, _UnitContext], set[str]]:
    sheet = workbook["核算单元"]
    contexts: dict[str, _UnitContext] = {}
    disabled: set[str] = set()
    for row in _rows(sheet):
        if sheet.cell(row, 1).data_type == "f":
            global_warnings.append(ImportMessage("EXCEL-UNIT-FORMULA", "核算单元名称不接受公式，请直接填写文字。", f"核算单元!A{row}"))
            continue
        name_value = sheet.cell(row, 1).value
        if not isinstance(name_value, str) or not name_value.strip():
            global_warnings.append(ImportMessage("EXCEL-UNIT-NAME-MISSING", "核算单元行缺少名称，已忽略该行及其无法关联的数据。", f"核算单元!A{row}"))
            continue
        name = name_value.strip()
        if name in contexts or name in disabled:
            target = contexts.get(name)
            if target:
                target.errors.append(ImportMessage("EXCEL-UNIT-DUPLICATE", f"核算单元名称“{name}”重复。", f"核算单元!A{row}"))
            else:
                global_warnings.append(ImportMessage("EXCEL-UNIT-DUPLICATE", f"核算单元名称“{name}”重复，重复行已忽略。", f"核算单元!A{row}"))
            continue
        scratch = _UnitContext(name, "", AccountingUnitType.OTHER, "", "", None, False, (), False, False)
        unit_type = _enum_value(reader, scratch, sheet, row, "类型", UNIT_TYPE_LABELS, required=True)
        enabled = _enum_value(reader, scratch, sheet, row, "是否启用", YES_NO, required=True)
        if enabled is False:
            disabled.add(name)
            continue
        period_type = _enum_value(reader, scratch, sheet, row, "核算期间类型", PERIOD_LABELS, required=True)
        start = _date_value(reader, scratch, sheet, row, "开始日期")
        end = _date_value(reader, scratch, sheet, row, "结束日期")
        period = None
        if start is not None and end is not None and period_type is not None:
            try:
                period = AccountingPeriod(period_type, start, end)
            except (DomainValidationError, ValueError) as exc:
                scratch.errors.append(ImportMessage("EXCEL-PERIOD-INVALID", f"核算期间无效：{exc}", f"核算单元!F{row}:G{row}"))
        enterprise_name = reader.text(scratch, sheet.title, _cell_for(sheet, row, "企业名称"), required=True)
        boundary_confirmed = _enum_value(reader, scratch, sheet, row, "边界已确认", YES_NO, required=True)
        boundary_text = reader.text(scratch, sheet.title, _cell_for(sheet, row, "边界说明"))
        other_activity = _enum_value(reader, scratch, sheet, row, "其他行业活动", YES_NO)
        transport = _enum_value(reader, scratch, sheet, row, "上下游运输", YES_NO)
        row_id = _stable_token("excel-unit", workbook_sha, row, name)
        components = (_stable_token("boundary", row_id, boundary_text),) if boundary_text else ()
        ctx = _UnitContext(
            name=name,
            unit_id=row_id,
            unit_type=unit_type if isinstance(unit_type, AccountingUnitType) else AccountingUnitType.OTHER,
            enterprise_id=_stable_token("enterprise", row_id),
            enterprise_name=enterprise_name or name,
            period=period,
            boundary_confirmed=boundary_confirmed is True,
            boundary_components=components,
            other_activity=other_activity is True,
            transport=transport is True,
            errors=list(scratch.errors),
        )
        contexts[name] = ctx
    return contexts, disabled


def _row_context(
    reader: _CellReader,
    sheet,
    row: int,
    contexts: Mapping[str, _UnitContext],
    disabled: set[str],
    global_warnings: list[ImportMessage],
) -> _UnitContext | None:
    raw_unit = sheet.cell(row, 1).value
    has_payload = any(cell.value is not None for cell in sheet[row][1:])
    if raw_unit is None or not str(raw_unit).strip():
        if has_payload:
            global_warnings.append(ImportMessage("EXCEL-ORPHAN-DATA", f"“{sheet.title}”存在未关联核算单元的数据，已忽略。", f"{sheet.title}!A{row}"))
        return None
    unit_name = str(raw_unit).strip()
    if unit_name in disabled:
        if has_payload:
            global_warnings.append(ImportMessage("EXCEL-DISABLED-UNIT-DATA", f"核算单元“{unit_name}”未启用，其“{sheet.title}”数据已忽略。", f"{sheet.title}!A{row}"))
        return None
    ctx = contexts.get(unit_name)
    if ctx is None:
        if has_payload:
            global_warnings.append(ImportMessage("EXCEL-UNKNOWN-UNIT-DATA", f"“{sheet.title}”的数据无法关联到启用核算单元“{unit_name}”，已忽略。", f"{sheet.title}!A{row}"))
        return None
    return ctx


def _row_has_payload(sheet, row: int) -> bool:
    return any(cell.value is not None for cell in sheet[row][1:])


def _unit_wants_source(ctx: _UnitContext, source_id: str, sheet_name: str, row: int, global_warnings: list[ImportMessage], sheet) -> bool:
    status = ctx.source_states.get(source_id)
    if status is EmissionSourceStatus.NOT_INVOLVED:
        if _row_has_payload(sheet, row):
            ctx.warnings.append(ImportMessage(
                "EXCEL-SOURCE-DATA-IGNORED",
                f"{ctx.name}的{SOURCE_LABELS[source_id]}已标记为“不涉及”，检测到该页数据，本次核算已忽略。",
                f"{sheet_name}!A{row}",
            ))
        return False
    return True


def _evidence_ids(ctx: _UnitContext, reader: _CellReader, sheet, row: int, header: str) -> tuple[str, ...]:
    refs = _split_refs(reader.text(ctx, sheet.title, _cell_for(sheet, row, header)))
    ids: list[str] = []
    for ref in refs:
        evidence_id = ctx.evidence_names.get(ref)
        if evidence_id is None:
            cell = _cell_for(sheet, row, header)
            reader.error(ctx, "EXCEL-EVIDENCE-REFERENCE-UNKNOWN", f"未找到证据名称“{ref}”；请先在“证据来源”登记。", f"{sheet.title}!{cell.coordinate}")
        else:
            ids.append(evidence_id)
    return tuple(ids)


def _source_state_rows(workbook, contexts: Mapping[str, _UnitContext], disabled: set[str], reader: _CellReader, warnings: list[ImportMessage]) -> None:
    sheet = workbook["排放源"]
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None:
            continue
        source_id = _enum_value(reader, ctx, sheet, row, "排放源", LABEL_TO_SOURCE, required=True)
        status = _enum_value(reader, ctx, sheet, row, "状态", SOURCE_STATE_LABELS, required=True)
        if not isinstance(source_id, str) or not isinstance(status, EmissionSourceStatus):
            continue
        if source_id in ctx.source_states:
            reader.error(ctx, "EXCEL-SOURCE-STATE-DUPLICATE", f"“{SOURCE_LABELS[source_id]}”状态重复填写。", f"排放源!A{row}")
        else:
            ctx.source_states[source_id] = status


def _parse_fuels(workbook, contexts, disabled, reader, warnings, resolver) -> None:
    sheet = workbook["化石燃料"]
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None or not _unit_wants_source(ctx, SOURCE_FUEL, sheet.title, row, warnings, sheet):
            continue
        if not _row_has_payload(sheet, row):
            continue
        fuel_type = _enum_value(reader, ctx, sheet, row, "燃料种类", FUEL_TYPE_LABELS, required=True)
        path = _enum_value(reader, ctx, sheet, row, "计量路径", FUEL_PATH_LABELS, required=True)
        if not isinstance(fuel_type, FuelType) or not isinstance(path, FuelPath):
            continue
        activity = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "活动量"))
        carbon_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "单位热值含碳量"))
        oxidation_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "碳氧化率"))
        lhv_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "低位发热量"))
        source_reference = reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号"))
        activity_evidence_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
        factor_evidence_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
        subject = FUEL_C1_SUBJECT_IDS.get(fuel_type)
        default_carbon = _parameter_from_factor(
            _factor_for(resolver, f"{subject}_carbon_content", ctx.period) if subject else None,
            "采用 GB/T 32151.34—2024 附录 C.1 对应燃料的单位热值含碳量。",
        )
        default_oxidation = _parameter_from_factor(
            _factor_for(resolver, f"{subject}_oxidation_rate", ctx.period) if subject else None,
            "采用 GB/T 32151.34—2024 附录 C.1 对应燃料的碳氧化率。",
        )
        default_lhv = _parameter_from_factor(
            _factor_for(resolver, f"{subject}_lhv", ctx.period) if subject and path is not FuelPath.HEAT else None,
            "采用 GB/T 32151.34—2024 附录 C.1 对应燃料的低位发热量。",
        )
        if default_lhv is not None:
            expected_path = FuelPath.VOLUME if default_lhv.unit == "GJ/10⁴Nm³" else FuelPath.MASS if default_lhv.unit == "GJ/t" else None
            if expected_path is not None and path is not expected_path and path is not FuelPath.HEAT:
                reader.error(ctx, "EXCEL-FUEL-PATH-MISMATCH", f"所选燃料的附录 C.1 低位发热量单位与“{FUEL_PATH_LABELS and next((k for k,v in FUEL_PATH_LABELS.items() if v is path), path.value)}”路径不一致；请选择“{next(k for k, v in FUEL_PATH_LABELS.items() if v is expected_path)}”或录入有依据的实测参数。", f"化石燃料!{_cell_for(sheet, row, '计量路径').coordinate}")
        carbon_unit = "tC/GJ" if path is FuelPath.HEAT or default_carbon is not None or default_lhv is not None or lhv_value is not None else {
            FuelPath.VOLUME: "tC/10^4Nm3", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ",
        }[path]
        lhv_unit = {FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}[path]
        carbon = _make_parameter(
            carbon_value, parameter_id=f"{subject or 'fuel'}_carbon_content", unit=carbon_unit,
            source_reference=source_reference, evidence_ids=factor_evidence_ids, default=default_carbon,
            ctx=ctx, location=_location(sheet.title, row, "单位热值含碳量", workbook),
        )
        oxidation = _make_parameter(
            oxidation_value, parameter_id=f"{subject or 'fuel'}_oxidation_rate", unit="ratio",
            source_reference=source_reference, evidence_ids=factor_evidence_ids, default=default_oxidation,
            ctx=ctx, location=_location(sheet.title, row, "碳氧化率", workbook),
        )
        lhv = _make_parameter(
            lhv_value, parameter_id=f"{subject or 'fuel'}_lhv", unit=lhv_unit,
            source_reference=source_reference, evidence_ids=factor_evidence_ids, default=default_lhv,
            ctx=ctx, location=_location(sheet.title, row, "低位发热量", workbook),
        )
        if activity is None and carbon_value is None and oxidation_value is None and lhv_value is None:
            # A row with only a chosen type/path is an empty template row.
            continue
        if path is FuelPath.HEAT and lhv is not None:
            reader.error(ctx, "EXCEL-FUEL-LHV-NOT-APPLICABLE", "热量路径的活动量已经是热量，不应填写低位发热量。", _location(sheet.title, row, "低位发热量", workbook))
            lhv = None
        fuel_id = _stable_token("fuel", ctx.unit_id, row)
        ctx.payloads.setdefault("fuel_inputs", []).append(FuelInput(
            fuel_id=fuel_id,
            fuel_type=fuel_type,
            path=path,
            activity=None if activity is None else _activity(activity, {FuelPath.VOLUME: "ten_thousand_Nm3", FuelPath.MASS: "t", FuelPath.HEAT: "GJ"}[path], activity_evidence_ids),
            carbon_content=carbon,
            oxidation_rate=oxidation,
            lower_heating_value=lhv,
        ))


def _activity(value: Decimal | None, unit: str, evidence_ids: tuple[str, ...] = ()):
    from packages.standards.carbon_material import InputValue
    return None if value is None else InputValue(value, unit, evidence_ref_ids=evidence_ids)


def _enum_labels(enum_type) -> dict[str, object]:
    return {item.value: item for item in enum_type}


def _source_reference(ctx: _UnitContext, reader: _CellReader, sheet, row: int) -> str | None:
    return reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号"))


def _process_default(resolver, parameter_id: str, period: AccountingPeriod | None, reason: str) -> ParameterValue | None:
    return _parameter_from_factor(_factor_for(resolver, parameter_id, period), reason)


def _basis_values(reader: _CellReader, ctx: _UnitContext, sheet, row: int):
    basis_labels = {
        "收到基": MaterialBasis.RECEIVED,
        "干燥基": MaterialBasis.DRY,
        "其他已记录基准": MaterialBasis.OTHER_DOCUMENTED,
    }
    component_labels = {
        "固定碳": MaterialComponentKind.FIXED_CARBON,
        "总碳": MaterialComponentKind.TOTAL_CARBON,
        "挥发分": MaterialComponentKind.VOLATILE_MATTER,
        "未知": MaterialComponentKind.UNKNOWN,
    }
    mass_basis = _enum_value(reader, ctx, sheet, row, "质量基准", basis_labels)
    composition_basis = _enum_value(reader, ctx, sheet, row, "成分基准", basis_labels)
    normalized_basis = _enum_value(reader, ctx, sheet, row, "折算基准", basis_labels)
    component_kind = _enum_value(reader, ctx, sheet, row, "固定碳成分性质", component_labels)
    return (
        mass_basis or MaterialBasis.RECEIVED,
        composition_basis or MaterialBasis.RECEIVED,
        normalized_basis or MaterialBasis.RECEIVED,
        component_kind or MaterialComponentKind.FIXED_CARBON,
    )


def _parse_processes(workbook, contexts, disabled, reader, warnings, resolver) -> None:
    basis_columns = ("质量基准", "成分基准", "折算基准", "固定碳成分性质", "水分修正证据", "基准换算证据", "碳输出计入投入")
    for sheet_name, (input_type, attrs, headers, source_id) in PROCESS_SHEETS.items():
        sheet = workbook[sheet_name]
        for row in _rows(sheet):
            ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
            if ctx is None or not _unit_wants_source(ctx, source_id, sheet_name, row, warnings, sheet):
                continue
            if not _row_has_payload(sheet, row):
                continue
            numbers = {
                attr: reader.number(ctx, sheet_name, row, _cell_for(sheet, row, header))
                for attr, header in zip(attrs, headers, strict=True)
            }
            # Do not treat a named-but-empty row as an involved business instance.
            if all(value is None for key, value in numbers.items() if key != attrs[-1]):
                continue
            instance_label = reader.text(ctx, sheet_name, _cell_for(sheet, row, "实例名称"))
            instance_id = _stable_token("instance", ctx.unit_id, sheet_name, row, instance_label or "")
            activity_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
            factor_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
            if "k1" in attrs:
                k_parameter_id, k_unit, reason = "car-par-k1", "K1", "采用 Canonical 中 GB/T 32151.34—2024 标准一般取值 K1。"
            elif "k2" in attrs:
                k_parameter_id, k_unit, reason = "car-par-k2", "K2", "采用 Canonical 中 GB/T 32151.34—2024 标准一般取值 K2。"
            else:
                k_parameter_id, k_unit, reason = "car-par-k3", "K3", "采用 Canonical 中 GB/T 32151.34—2024 标准一般取值 K3。"
            default = _process_default(resolver, k_parameter_id, ctx.period, reason)
            source_ref = reader.text(ctx, sheet_name, _cell_for(sheet, row, "参数证据"))
            if source_ref and source_ref in ctx.evidence_names:
                source_ref = next((
                    evidence.source_reference for evidence in (*ctx.activity_evidence, *ctx.factor_evidence)
                    if evidence.evidence_id == ctx.evidence_names[source_ref]
                ), source_ref)
            k_value = _make_parameter(
                numbers[attrs[-1]], parameter_id=k_parameter_id, unit="ratio", source_reference=source_ref,
                evidence_ids=factor_ids, default=default, ctx=ctx,
                location=_location(sheet_name, row, headers[-1], workbook),
            )
            for key, value in tuple(numbers.items()):
                if key == attrs[-1]:
                    continue
                if value is not None:
                    unit = "ratio" if "fc" in key or "var" in key else "tC" if key in {"bwt", "gwt"} else "t"
                    numbers[key] = _activity(value, unit, activity_ids)
            numbers[attrs[-1]] = k_value
            mass_basis, composition_basis, normalized_basis, component_kind = _basis_values(reader, ctx, sheet, row)
            moisture = _enum_value(reader, ctx, sheet, row, "水分修正证据", YES_NO)
            conversion = _enum_value(reader, ctx, sheet, row, "基准换算证据", YES_NO)
            flags_header = "炉损计入" if sheet_name == "石墨化" else "碳输出计入投入"
            flag = _enum_value(reader, ctx, sheet, row, flags_header, YES_NO)
            if moisture and not activity_ids:
                ctx.errors.append(ImportMessage("EXCEL-BASIS-EVIDENCE-REQUIRED", "选择水分修正时，请先在“证据来源”登记并引用相应活动数据证据。", f"{sheet_name}!{_cell_for(sheet, row, '水分修正证据').coordinate}"))
            if conversion and not activity_ids:
                ctx.errors.append(ImportMessage("EXCEL-BASIS-EVIDENCE-REQUIRED", "选择基准换算时，请先在“证据来源”登记并引用相应活动数据证据。", f"{sheet_name}!{_cell_for(sheet, row, '基准换算证据').coordinate}"))
            process_arguments = dict(
                **numbers,
                mass_basis=mass_basis,
                composition_basis=composition_basis,
                normalized_basis=normalized_basis,
                component_kind=component_kind,
                moisture_evidence=bool(moisture and activity_ids),
                conversion_evidence=bool(conversion and activity_ids),
                instance_id=instance_id,
            )
            if sheet_name == "石墨化":
                process_arguments["furnace_loss_included"] = bool(flag)
            else:
                process_arguments["carbon_output_included_in_input"] = bool(flag)
            payload = input_type(**process_arguments)
            ctx.payloads.setdefault({SOURCE_CALCINATION: "calcinations", SOURCE_BAKING: "bakings", SOURCE_GRAPHITIZATION: "graphitizations"}[source_id], []).append(payload)


def _parse_fume(workbook, contexts, disabled, reader, warnings, resolver) -> None:
    sheet = workbook["烟气焚烧"]
    headers = ("Q 烟气流量（Nm³/h）", "QVAR 烟气含碳量（mg/Nm³）", "HM 低位发热量（GJ/t）", "FCH 单位热值含碳量（tC/GJ）", "FOX 碳氧化率", "运行时间（d）")
    attrs = ("q", "qvar", "hm", "fch", "fox", "duration")
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None or not _unit_wants_source(ctx, SOURCE_FUME, sheet.title, row, warnings, sheet) or not _row_has_payload(sheet, row):
            continue
        values = {attr: reader.number(ctx, sheet.title, row, _cell_for(sheet, row, header)) for attr, header in zip(attrs, headers, strict=True)}
        if all(value is None for value in values.values()):
            continue
        activity_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
        factor_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
        source_ref = reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号"))
        fch_value = _make_parameter(
            values["fch"], parameter_id="CAR-PAR-P04A-FCH", unit="tC/GJ", source_reference=source_ref,
            evidence_ids=factor_ids, default=None, ctx=ctx,
            location=_location(sheet.title, row, "FCH 单位热值含碳量（tC/GJ）", workbook),
        )
        for key, value in tuple(values.items()):
            if key == "fch":
                values[key] = fch_value
            elif value is not None:
                values[key] = _activity(value, "ratio" if key == "fox" else {"q": "Nm3/h", "qvar": "mg/Nm3", "hm": "GJ/t", "duration": "d"}[key], activity_ids)
        name = reader.text(ctx, sheet.title, _cell_for(sheet, row, "实例名称"))
        ctx.payloads.setdefault("fume_incinerations", []).append(FumeIncinerationInput(
            **values, instance_id=_stable_token("fume", ctx.unit_id, row, name or ""),
        ))


def _parse_fgd(workbook, contexts, disabled, reader, warnings, resolver) -> None:
    sheet = workbook["烟气脱硫"]
    components: dict[tuple[str, str], list[CarbonateComponent]] = {}
    row_counts: dict[tuple[str, str], int] = {}
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None or not _unit_wants_source(ctx, SOURCE_FGD, sheet.title, row, warnings, sheet) or not _row_has_payload(sheet, row):
            continue
        name = reader.text(ctx, sheet.title, _cell_for(sheet, row, "设施名称")) or f"烟气治理设施{row}"
        carbonate_label = reader.text(ctx, sheet.title, _cell_for(sheet, row, "碳酸盐种类"))
        if carbonate_label is not None and carbonate_label not in CARBONATE_LABELS:
            reader.error(ctx, "EXCEL-CARBONATE-INVALID", "碳酸盐种类不在标准 C.2 列表中。", _location(sheet.title, row, "碳酸盐种类", workbook))
        amount = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "碳酸盐用量（t）"))
        fraction_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "碳酸盐含量比例"))
        factor_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "排放因子（tCO₂/t）"))
        conversion_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "转化率"))
        if amount is None and fraction_value is None and factor_value is None and conversion_value is None and carbonate_label is None:
            continue
        activity_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
        factor_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
        source_ref = reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号"))
        carbonate_parameter = CARBONATE_LABELS.get(carbonate_label or "")
        default_fraction = _parameter_from_factor(_factor_for(resolver, "car-par-p04b-i", ctx.period), "采用 GB/T 32151.34—2024 烟气脱硫碳酸盐含量标准缺省值。")
        default_conversion = _parameter_from_factor(_factor_for(resolver, "car-par-p04b-tr", ctx.period), "采用 GB/T 32151.34—2024 烟气脱硫转化率标准缺省值。")
        default_factor = _parameter_from_factor(_factor_for(resolver, carbonate_parameter, ctx.period), "按所选碳酸盐种类采用 GB/T 32151.34—2024 附录 C.2 对应因子。") if carbonate_parameter else None
        fraction = _make_parameter(
            fraction_value, parameter_id="car-par-p04b-i", unit="ratio", source_reference=source_ref,
            evidence_ids=factor_ids, default=default_fraction, ctx=ctx,
            location=_location(sheet.title, row, "碳酸盐含量比例", workbook),
        )
        conversion = _make_parameter(
            conversion_value, parameter_id="car-par-p04b-tr", unit="ratio", source_reference=source_ref,
            evidence_ids=factor_ids, default=default_conversion, ctx=ctx,
            location=_location(sheet.title, row, "转化率", workbook),
        )
        factor = _make_parameter(
            factor_value,
            parameter_id=carbonate_parameter or "fgd_carbonate_emission_factor_measured",
            unit="tCO2/t", source_reference=source_ref, evidence_ids=factor_ids,
            default=default_factor, ctx=ctx,
            location=_location(sheet.title, row, "排放因子（tCO₂/t）", workbook),
        )
        key = (ctx.name, name)
        row_counts[key] = row
        components.setdefault(key, []).append(CarbonateComponent(
            amount=_activity(amount, "t", activity_ids),
            carbonate_fraction=fraction,
            emission_factor=factor,
            conversion_rate=conversion,
            carbonate_type=carbonate_label,
        ))
    for (unit_name, facility_name), unit_components in components.items():
        ctx = contexts[unit_name]
        instance = _stable_token("fgd", ctx.unit_id, facility_name)
        ctx.payloads.setdefault("fgd_units", []).append(FGDInput(components=tuple(unit_components), instance_id=instance))


def _parse_electricity(workbook, contexts, disabled, reader, warnings) -> None:
    sheet = workbook["电力"]
    direction_map = {"购入": "purchased", "输出": "exported"}
    acquisition_map = {"购入": ElectricityAcquisitionMode.PURCHASED, "自发自用": ElectricityAcquisitionMode.SELF_CONSUMED}
    attribute_map = {"常规": ElectricityAttribute.ORDINARY, "非化石": ElectricityAttribute.NONFOSSIL, "化石": ElectricityAttribute.FOSSIL}
    proof_type_map = {
        "无": ElectricityProofType.NONE,
        "合同和结算": ElectricityProofType.CONTRACT_AND_SETTLEMENT,
        "GEC": ElectricityProofType.GEC,
        "月度原始记录": ElectricityProofType.MONTHLY_ORIGINAL_RECORD,
    }
    proof_status_map = {"未提供": ElectricityProofStatus.NOT_PROVIDED, "有效": ElectricityProofStatus.VALID, "无效": ElectricityProofStatus.INVALID}
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None or not _row_has_payload(sheet, row):
            continue
        direction = _enum_value(reader, ctx, sheet, row, "方向", direction_map, required=True)
        source_id = SOURCE_PURCHASED_ELECTRICITY if direction == "purchased" else SOURCE_EXPORTED_ELECTRICITY
        if direction not in {"purchased", "exported"}:
            continue
        if not _unit_wants_source(ctx, source_id, sheet.title, row, warnings, sheet):
            continue
        amount = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "电量（MWh）"), required=True)
        if amount is None:
            continue
        activity_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
        factor_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
        factor_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "排放因子（tCO₂/MWh）"))
        if direction == "purchased":
            acquisition = _enum_value(reader, ctx, sheet, row, "取得方式", acquisition_map, required=True)
            attribute = _enum_value(reader, ctx, sheet, row, "电力属性", attribute_map, required=True)
            proof_type = _enum_value(reader, ctx, sheet, row, "证明类型", proof_type_map, required=True)
            proof_status = _enum_value(reader, ctx, sheet, row, "证明状态", proof_status_map, required=True)
            if not isinstance(acquisition, ElectricityAcquisitionMode) or not isinstance(attribute, ElectricityAttribute):
                continue
            if not isinstance(proof_type, ElectricityProofType):
                proof_type = ElectricityProofType.NONE
            if not isinstance(proof_status, ElectricityProofStatus):
                proof_status = ElectricityProofStatus.NOT_PROVIDED
            if ctx.period is None:
                ctx.errors.append(ImportMessage("EXCEL-PERIOD-REQUIRED", "电力明细需要有效核算期间。", f"电力!A{row}"))
                continue
            ctx.payloads.setdefault("electricity_details", []).append(ElectricityConsumptionDetail(
                detail_id=_stable_token("electricity", ctx.unit_id, row),
                enterprise_id=ctx.enterprise_id,
                standard_id=STANDARD_ID,
                accounting_period=ctx.period,
                electricity_amount=amount,
                electricity_unit="MWh",
                acquisition_mode=acquisition,
                attribute=attribute,
                proof_type=proof_type,
                proof_status=proof_status,
            ))
        else:
            factor = _make_parameter(
                factor_value,
                parameter_id="electricity_emission_factor_measured",
                unit="tCO2/MWh",
                source_reference=reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号")),
                evidence_ids=factor_ids,
                default=None,
                ctx=ctx,
                location=_location(sheet.title, row, "排放因子（tCO₂/MWh）", workbook),
            )
            ctx.payloads.setdefault("exported_electricity", []).append(ElectricityOutputLine(
                line_id=_stable_token("power-output", ctx.unit_id, row),
                amount=_activity(amount, "MWh", activity_ids),
                factor=factor,
                unit="MWh",
            ))


def _parse_heat(workbook, contexts, disabled, reader, warnings) -> None:
    sheet = workbook["热力"]
    directions = {"购入": "purchased", "输出": "exported"}
    steam_kinds = {"饱和蒸汽": SteamKind.SATURATED, "过热蒸汽": SteamKind.SUPERHEATED}
    for row in _rows(sheet):
        ctx = _row_context(reader, sheet, row, contexts, disabled, warnings)
        if ctx is None or not _row_has_payload(sheet, row):
            continue
        direction = _enum_value(reader, ctx, sheet, row, "方向", directions, required=True)
        source_id = SOURCE_PURCHASED_HEAT if direction == "purchased" else SOURCE_EXPORTED_HEAT
        if direction not in {"purchased", "exported"}:
            continue
        if not _unit_wants_source(ctx, source_id, sheet.title, row, warnings, sheet):
            continue
        amount = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "热力数量（kg）"), required=True)
        steam_kind = _enum_value(reader, ctx, sheet, row, "蒸汽类型", steam_kinds, required=True)
        enthalpy = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "焓值（kJ/kg）"))
        pressure = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "压力（MPa）"))
        temperature = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "温度（℃）"))
        factor_value = reader.number(ctx, sheet.title, row, _cell_for(sheet, row, "排放因子（tCO₂/GJ）"))
        if amount is None or not isinstance(steam_kind, SteamKind):
            continue
        activity_ids = _evidence_ids(ctx, reader, sheet, row, "活动数据证据")
        factor_ids = _evidence_ids(ctx, reader, sheet, row, "参数证据")
        factor = _make_parameter(
            factor_value, parameter_id="heat_emission_factor_measured", unit="tCO2/GJ",
            source_reference=reader.text(ctx, sheet.title, _cell_for(sheet, row, "参数来源编号")),
            evidence_ids=factor_ids, default=None, ctx=ctx,
            location=_location(sheet.title, row, "排放因子（tCO₂/GJ）", workbook),
        )
        line_id = _stable_token("heat", ctx.unit_id, direction, row)
        heat = HeatInput(
            line_id=line_id,
            amount=_activity(amount, "kg", activity_ids),
            enthalpy=_activity(enthalpy, "kJ/kg", activity_ids),
            factor=factor,
            unit="kg",
            steam_kind=steam_kind,
            pressure_mpa=_activity(pressure, "MPa", activity_ids),
            temperature_c=_activity(temperature, "C", activity_ids),
        )
        ctx.payloads.setdefault("purchased_heat" if direction == "purchased" else "exported_heat", []).append(heat)


def _make_carbon_input(ctx: _UnitContext) -> CarbonMaterialInput:
    missing_sources = [source for source in SOURCE_IDS if source not in ctx.source_states]
    for source in missing_sources:
        ctx.errors.append(ImportMessage("EXCEL-SOURCE-STATE-MISSING", f"请为“{SOURCE_LABELS[source]}”明确选择涉及状态。"))
        ctx.source_states[source] = EmissionSourceStatus.UNCONFIRMED
    report = CarbonReportingData(
        **ctx.report_values,
        activity_evidence=tuple(ctx.activity_evidence),
        measured_factor_evidence=tuple(ctx.factor_evidence),
    )
    return CarbonMaterialInput(
        input_id=f"input.{ctx.unit_id}",
        enterprise_id=ctx.enterprise_id,
        enterprise_name=ctx.enterprise_name,
        period=ctx.period,
        boundary_confirmed=ctx.boundary_confirmed,
        boundary_component_ids=ctx.boundary_components,
        source_states=tuple(EmissionSourceState(source_id, ctx.source_states[source_id]) for source_id in SOURCE_IDS),
        other_activity_present=ctx.other_activity,
        transport_present=ctx.transport,
        fuel_inputs=tuple(ctx.payloads.get("fuel_inputs", ())),
        calcinations=tuple(ctx.payloads.get("calcinations", ())),
        bakings=tuple(ctx.payloads.get("bakings", ())),
        graphitizations=tuple(ctx.payloads.get("graphitizations", ())),
        fume_incinerations=tuple(ctx.payloads.get("fume_incinerations", ())),
        fgd_units=tuple(ctx.payloads.get("fgd_units", ())),
        electricity_details=tuple(ctx.payloads.get("electricity_details", ())),
        exported_electricity=tuple(ctx.payloads.get("exported_electricity", ())),
        purchased_heat=tuple(ctx.payloads.get("purchased_heat", ())),
        exported_heat=tuple(ctx.payloads.get("exported_heat", ())),
        reporting_data=report,
    )


class ExcelWorkbookImporter:
    """Parse a supported workbook into independent unit previews.

    `parameter_resolver` is the same application resolver used by the desktop
    Calculator. No Qt, widget names, project persistence, or Record database are
    referenced by this module.
    """

    def __init__(self, parameter_resolver: ParameterResolver | None = None):
        self.parameter_resolver = parameter_resolver

    def import_preview(self, file_path: str | Path) -> WorkbookImportPreview:
        path = Path(file_path)
        if path.suffix.lower() != ".xlsx":
            raise WorkbookFatalError("仅支持 .xlsx 工作簿。")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise WorkbookFatalError(f"无法读取工作簿：{exc}") from exc
        digest = hashlib.sha256(content).hexdigest().upper()
        try:
            import io
            workbook = load_workbook(io.BytesIO(content), data_only=False, read_only=False)
            numeric_xml = _serialized_numeric_values(content)
        except (BadZipFile, KeyError, OSError, ValueError, ElementTree.ParseError) as exc:
            raise WorkbookFatalError(f"工作簿损坏或结构无法解析：{exc}") from exc
        try:
            missing = sorted(REQUIRED_SHEETS - set(workbook.sheetnames))
            if missing:
                raise WorkbookFatalError(f"缺少模板核心工作表：{', '.join(missing)}")
            for sheet_name, headers in SHEETS.items():
                actual = _read_headers(workbook, sheet_name)
                if tuple(actual[:len(headers)]) != tuple(headers):
                    raise WorkbookFatalError(f"工作表“{sheet_name}”的模板列结构不受支持。")
            metadata = _parse_metadata(workbook)
            expected = {
                "template_id": TEMPLATE_ID,
                "template_version": TEMPLATE_VERSION,
                "standard_id": STANDARD_ID,
                "standard_version": STANDARD_VERSION,
                "ingress_policy_id": INGRESS_POLICY_ID,
            }
            for key, expected_value in expected.items():
                if metadata.get(key) != expected_value:
                    raise WorkbookFatalError(f"工作簿 {key} 不匹配或版本无法识别。")

            warnings: list[ImportMessage] = []
            extra_sheets = sorted(set(workbook.sheetnames) - REQUIRED_SHEETS)
            for name in extra_sheets:
                warnings.append(ImportMessage("EXCEL-UNKNOWN-SHEET", f"发现自定义页签“{name}”，该页签不参与核算。", name))
            reader = _CellReader(numeric_xml)
            contexts, disabled = _load_unit_contexts(workbook, digest, reader, warnings)
            _collect_evidence(workbook, contexts, reader, warnings)
            _source_state_rows(workbook, contexts, disabled, reader, warnings)
            _parse_fuels(workbook, contexts, disabled, reader, warnings, self.parameter_resolver)
            _parse_processes(workbook, contexts, disabled, reader, warnings, self.parameter_resolver)
            _parse_fume(workbook, contexts, disabled, reader, warnings, self.parameter_resolver)
            _parse_fgd(workbook, contexts, disabled, reader, warnings, self.parameter_resolver)
            _parse_electricity(workbook, contexts, disabled, reader, warnings)
            _parse_heat(workbook, contexts, disabled, reader, warnings)

            imported_at = datetime.now(timezone.utc)
            provenance = WorkbookProvenance(
                workbook_sha256=digest,
                template_id=metadata["template_id"],
                template_version=metadata["template_version"],
                standard_id=metadata["standard_id"],
                standard_version=metadata["standard_version"],
                ingress_policy_id=metadata["ingress_policy_id"],
                imported_at=imported_at,
            )
            previews: list[UnitCalculationPreview] = []
            for ctx in contexts.values():
                if ctx.period is None:
                    ctx.errors.append(ImportMessage("EXCEL-PERIOD-REQUIRED", "请填写有效的核算期间。"))
                    input_value = None
                else:
                    try:
                        input_value = _make_carbon_input(ctx)
                    except (DomainValidationError, TypeError, ValueError) as exc:
                        ctx.errors.append(ImportMessage("EXCEL-DOMAIN-INPUT-INVALID", f"无法构造该核算单元的业务输入：{exc}"))
                        input_value = None
                calculation = None
                if input_value is not None and not ctx.errors:
                    calculator = CarbonMaterialCalculator(
                        parameter_resolver=self.parameter_resolver,
                        record_repository=InMemoryRecordRepository(),
                    )
                    outcome = calculator.calculate(input_value, calculated_at=imported_at)
                    calculation = outcome
                    for problem in outcome.problems:
                        if getattr(problem.level, "value", "ERROR") == "ERROR":
                            ctx.errors.append(ImportMessage(problem.code, problem.message, problem.field_id))
                        else:
                            ctx.warnings.append(ImportMessage(problem.code, problem.message, problem.field_id))
                    # The preview never exposes or persists the ephemeral Record.
                    from dataclasses import replace
                    calculation = replace(outcome, record=None)
                previews.append(UnitCalculationPreview(
                    unit_id=ctx.unit_id,
                    name=ctx.name,
                    unit_type=ctx.unit_type,
                    input_value=input_value,
                    calculation=calculation,
                    errors=tuple(ctx.errors),
                    warnings=tuple(ctx.warnings),
                ))
            return WorkbookImportPreview(provenance, tuple(previews), tuple(warnings), tuple(reader.evidence))
        finally:
            workbook.close()


__all__ = [
    "TEMPLATE_ID", "TEMPLATE_VERSION", "INGRESS_POLICY_ID", "WorkbookFatalError", "WorkbookProvenance",
    "NumericCellEvidence", "ImportMessage", "UnitCalculationPreview", "WorkbookImportPreview",
    "ExcelWorkbookImporter", "create_template_bytes", "write_template", "significant_digit_count",
]
