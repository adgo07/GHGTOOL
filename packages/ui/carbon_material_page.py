"""G06 Qt page for hand-entered GB/T 32151.34 calculations.

The page keeps calculation rules in the Domain layer while presenting
business-language summaries and optional professional details.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, timezone
from dataclasses import dataclass, fields as dataclass_fields, is_dataclass, replace
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from enum import Enum
import hashlib
import json
import logging
import re
from uuid import uuid4

from PySide6.QtCore import QDate, QEvent, QSignalBlocker, QTimer, Qt, Signal
from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QApplication,
    QAbstractSpinBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
    QDateEdit,
    QInputDialog,
)

from packages.application.carbon_accounting import (
    CarbonAccountingUseCase,
    resolve_formal_record_repository,
    RecordPersistenceError,
    create_g06_parameter_resolver,
)
from packages.application.catalog_queries import CatalogQueryService
from packages.application.enterprise_history import list_enterprise_name_candidates
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.application.project_workspaces import (
    AccountingUnitType,
    AccountingUnitWorkspace,
    ProjectRecordAssociationError,
    ProjectWorkspace,
    ProjectWorkspaceService,
)
from packages.core import (
    DomainValidationError,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityConsumptionDetail,
    ElectricityProofStatus,
    ElectricityProofType,
    ParameterType,
    PeriodType,
)
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    STANDARD_ID,
    STANDARD_VERSION,
    BakingInput,
    CalcinationInput,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonateComponent,
    ActivityDataEvidence,
    CarbonReportingData,
    EmissionSourceState,
    EmissionSourceStatus,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatFactorMode,
    HeatInput,
    InputValue,
    ElectricityOutputLine,
    MaterialBasis,
    MaterialComponentKind,
    MeasuredFactorEvidence,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
    saturated_steam_enthalpy,
    superheated_steam_enthalpy,
)
from packages.standards.carbon_material_normalization import (
    MaterialDataSource,
    MaterialInputLine,
    MaterialRole,
    normalize_material_inputs,
)
from packages.core.models import AccountingPeriod, RecordStatus, ReviewStatus, ValueType
from packages.core.parameter_resolution import (
    NATIONAL_ELECTRICITY_PARAMETER_ID,
    PROVINCIAL_ELECTRICITY_PARAMETER_ID,
    ParameterResolutionContext,
    UserProvidedParameterValue,
)
from packages.core.repositories import RecordRepository

from .pages import BasePage, Navigate, _card
from .report_export import export_saved_record_report
from .field_specs import SOURCE_LABELS, get_field_spec, ui_to_domain_value
from .source_cards import SourceCard, SourceCardPresentationState
from .responsive_fields import ResponsiveFieldGrid
from .typed_inputs import NumericLineEdit, create_read_only_parameter, create_typed_input
from .view_models import AppRoute
from .design_tokens import BORDER, CARD_BACKGROUND, PRIMARY_BRAND, PRIMARY_TEXT, SECONDARY_TEXT, SURFACE_MUTED


_LOGGER = logging.getLogger(__name__)


_PROCESS_DEFAULT_PARAMETERS = {
    "calcination": ("CAR-PAR-K1", "第5.2.2条"),
    "baking": ("CAR-PAR-K2", "第5.2.3条"),
    "graphitization": ("CAR-PAR-K3", "第5.2.4条"),
}
_PROCESS_MATERIAL_ROLES: dict[str, tuple[tuple[str, MaterialRole], ...]] = {
    "calcination": (
        ("原料", MaterialRole.CALCINATION_FEED),
        ("煅后料", MaterialRole.CALCINED_PRODUCT),
        ("欠烧煅料", MaterialRole.UNDERBURN_RECOVERED),
        ("碳粉尘", MaterialRole.CARBON_DUST),
    ),
    "baking": (
        ("填充料", MaterialRole.BAKING_FILLER),
        ("待焙烧/炭化品", MaterialRole.GREEN_BAKING_PRODUCT),
        ("焙烧/炭化产品", MaterialRole.BAKED_PRODUCT),
        ("粉尘/碎屑/副产品", MaterialRole.BAKING_BYPRODUCT),
    ),
    "graphitization": (
        ("保温料/电阻料", MaterialRole.GRAPHITIZATION_PACKING),
        ("待石墨化品", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT),
        ("石墨化产品", MaterialRole.GRAPHITIZED_PRODUCT),
        ("粉尘/碎屑/残块/副产品", MaterialRole.GRAPHITIZATION_BYPRODUCT),
    ),
}
_PROCESS_MATERIAL_DEFAULT_ROLE = {
    "calcination": MaterialRole.CALCINATION_FEED,
    "baking": MaterialRole.GREEN_BAKING_PRODUCT,
    "graphitization": MaterialRole.GREEN_GRAPHITIZATION_PRODUCT,
}
_REPORT_SOURCE_OPTIONS = (
    ("燃料", "CAR-SRC-FUEL-001"),
    ("煅烧", "CAR-SRC-CALCINATION-001"),
    ("焙烧/炭化", "CAR-SRC-BAKING-001"),
    ("石墨化", "CAR-SRC-GRAPHITIZATION-001"),
    ("烟气焚烧", "CAR-SRC-FUME-INCINERATION-001"),
    ("烟气脱硫", "CAR-SRC-FGD-001"),
    ("购入电力", "CAR-SRC-PURCHASED-ELECTRICITY-001"),
    ("输出电力", "CAR-SRC-EXPORTED-ELECTRICITY-001"),
    ("购入热力", "CAR-SRC-PURCHASED-HEAT-001"),
    ("输出热力", "CAR-SRC-EXPORTED-HEAT-001"),
)
_FUEL_C1_SUBJECT_IDS = {
    FuelType.ANTHRACITE: "anthracite",
    FuelType.BITUMINOUS_COAL: "bituminous_coal",
    FuelType.LIGNITE: "lignite",
    FuelType.CLEANED_COAL: "cleaned_coal",
    FuelType.OTHER_CLEANED_COAL: "other_cleaned_coal",
    FuelType.BRIQUETTE: "briquette",
    FuelType.OTHER_COAL_PRODUCTS: "other_coal_products",
    FuelType.COKE: "coke",
    FuelType.PETROLEUM_COKE: "petroleum_coke",
    FuelType.CRUDE_OIL: "crude_oil",
    FuelType.FUEL_OIL: "fuel_oil",
    FuelType.GASOLINE: "gasoline",
    FuelType.DIESEL: "diesel",
    FuelType.KEROSENE: "kerosene",
    FuelType.LIQUEFIED_NATURAL_GAS: "liquefied_natural_gas",
    FuelType.LIQUEFIED_PETROLEUM_GAS: "liquefied_petroleum_gas",
    FuelType.NAPHTHA: "naphtha",
    FuelType.TAR: "tar",
    FuelType.CRUDE_BENZENE: "crude_benzene",
    FuelType.OTHER_PETROLEUM_PRODUCTS: "other_petroleum_products",
    FuelType.NATURAL_GAS: "natural_gas",
    FuelType.BLAST_FURNACE_GAS: "blast_furnace_gas",
    FuelType.CONVERTER_GAS: "converter_gas",
    FuelType.COKE_OVEN_GAS: "coke_oven_gas",
    FuelType.REFINERY_DRY_GAS: "refinery_dry_gas",
    FuelType.OTHER_GAS: "other_gas",
}
_FUEL_C1_ACTIVITY_PATH = {
    FuelType.NATURAL_GAS: FuelPath.VOLUME,
    FuelType.BLAST_FURNACE_GAS: FuelPath.VOLUME,
    FuelType.CONVERTER_GAS: FuelPath.VOLUME,
    FuelType.COKE_OVEN_GAS: FuelPath.VOLUME,
    FuelType.OTHER_GAS: FuelPath.VOLUME,
    FuelType.REFINERY_DRY_GAS: FuelPath.MASS,
}
_FUEL_TYPE_OPTIONS = (
    ("柴油", FuelType.DIESEL),
    ("天然气", FuelType.NATURAL_GAS),
    ("焦炉煤气", FuelType.COKE_OVEN_GAS),
    ("煤（需选择具体煤种）", FuelType.COAL),
    ("其他 / 手动输入", FuelType.OTHER),
    ("无烟煤", FuelType.ANTHRACITE),
    ("烟煤", FuelType.BITUMINOUS_COAL),
    ("褐煤", FuelType.LIGNITE),
    ("洗精煤", FuelType.CLEANED_COAL),
    ("其他洗煤", FuelType.OTHER_CLEANED_COAL),
    ("型煤", FuelType.BRIQUETTE),
    ("其他煤制品", FuelType.OTHER_COAL_PRODUCTS),
    ("焦炭", FuelType.COKE),
    ("石油焦", FuelType.PETROLEUM_COKE),
    ("原油", FuelType.CRUDE_OIL),
    ("燃料油", FuelType.FUEL_OIL),
    ("汽油", FuelType.GASOLINE),
    ("一般煤油", FuelType.KEROSENE),
    ("液化天然气", FuelType.LIQUEFIED_NATURAL_GAS),
    ("液化石油气", FuelType.LIQUEFIED_PETROLEUM_GAS),
    ("石脑油", FuelType.NAPHTHA),
    ("焦油", FuelType.TAR),
    ("粗苯", FuelType.CRUDE_BENZENE),
    ("其他石油制品", FuelType.OTHER_PETROLEUM_PRODUCTS),
    ("高炉煤气", FuelType.BLAST_FURNACE_GAS),
    ("转炉煤气", FuelType.CONVERTER_GAS),
    ("炼厂干气", FuelType.REFINERY_DRY_GAS),
    ("其他煤气", FuelType.OTHER_GAS),
)
_C2_CARBONATES = (
    ("CaCO₃", "car-par-c2-caco3"),
    ("MgCO₃", "car-par-c2-mgco3"),
    ("Na₂CO₃", "car-par-c2-na2co3"),
    ("NaHCO₃", "car-par-c2-nahco3"),
    ("FeCO₃", "car-par-c2-feco3"),
    ("MnCO₃", "car-par-c2-mnco3"),
    ("BaCO₃", "car-par-c2-baco3"),
    ("Li₂CO₃", "car-par-c2-li2co3"),
    ("K₂CO₃", "car-par-c2-k2co3"),
    ("SrCO₃", "car-par-c2-srco3"),
    ("CaMg(CO₃)₂", "car-par-c2-camgco3-2"),
)
_INTERNAL_TOKEN_RE = re.compile(r"\b(?:CAR|GEN)-[A-Z0-9-]+\b")
_INTERNAL_VARIABLE_RE = re.compile(r"\b(?:k[123]|resolver|candidate)\b", re.IGNORECASE)

def _field(parent: QWidget, object_name: str, placeholder: str = "") -> QLineEdit:
    edit = QLineEdit(parent)
    edit.setObjectName(object_name)
    edit.setPlaceholderText(placeholder)
    return edit


def _value(edit: QLineEdit) -> str | None:
    text = edit.text().strip()
    return text or None


def _ui_value(internal_key: str, edit: QLineEdit) -> str | None:
    return ui_to_domain_value(get_field_spec(internal_key), _value(edit))


def _enum(value: object, enum_type):
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        return enum_type(value)
    raise ValueError(f"unexpected enum value: {value!r}")



def _parameter_source_kind(value_type: ValueType) -> ParameterSourceKind:
    return {
        ValueType.STANDARD_SPECIFIED: ParameterSourceKind.STANDARD_SPECIFIED,
        ValueType.STANDARD_DEFAULT: ParameterSourceKind.STANDARD_DEFAULT,
        ValueType.GOVERNMENT_PUBLISHED: ParameterSourceKind.OFFICIAL_PUBLISHED,
        ValueType.MEASURED: ParameterSourceKind.MEASURED,
        ValueType.DERIVED: ParameterSourceKind.CALCULATED,
        # ParameterSourceKind deliberately has no SYSTEM_CONSTANT member;
        # catalog system constants are surfaced as a project-specified source
        # while retaining the original ValueType in the selector metadata.
        ValueType.SYSTEM_CONSTANT: ParameterSourceKind.PROJECT_SPECIFIED,
    }.get(value_type, ParameterSourceKind.PROJECT_SPECIFIED)


def _review_status_label(status: ReviewStatus) -> str:
    return {
        ReviewStatus.VERIFIED: "已核对",
        ReviewStatus.VERIFIED_WITH_INTERPRETATION: "已核对（含规则解释）",
        ReviewStatus.PENDING_SOURCE: "待核对来源",
        ReviewStatus.DEPRECATED: "已弃用",
    }[status]


def _domain_unit(unit: str) -> str:
    """Translate display-safe Unicode subscripts to the Domain unit spelling."""

    return unit.replace("₂", "2").replace("³", "3").replace("⁴", "4")


def _display_unit(unit: str) -> str:
    """Return the business-facing spelling of a calculation unit."""

    return unit.replace("tCO2", "tCO₂")


def _display_amount(value: Decimal, unit: str) -> str:
    """Format a Domain amount for ordinary UI display without mutating it."""

    amount = Decimal(str(value))
    if amount.is_zero():
        amount = abs(amount)
    return f"{_display_compact_decimal(amount)} {_display_unit(unit)}"


def _display_compact_decimal(value: Decimal) -> str:
    """Format only the UI copy, without reducing the authoritative Decimal."""

    amount = Decimal(str(value))
    if amount.is_zero():
        return "0.00"
    places = max(2, -amount.adjusted() + 2)
    if places > 12:
        return f"{amount:.3E}"
    with localcontext() as context:
        context.prec = max(28, len(amount.as_tuple().digits) + places + 4)
        rounded = amount.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    if rounded.is_zero():
        return f"{amount:.3E}"
    return f"{rounded:.2f}" if places == 2 else format(rounded, "f").rstrip("0").rstrip(".")

class _ElectricityRow(QWidget):
    def __init__(
        self,
        index: int,
        remove: Callable[[QWidget], None],
        parent: QWidget | None = None,
        *,
        row_key: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.row_key = row_key or uuid4().hex
        self.setObjectName(f"electricityRow{index}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self.detail_id = create_typed_input(
            self,
            get_field_spec("electricity.detail_id"),
            f"electricityDetailId{index}",
            f"detail-{index}",
        )
        self.detail_id.setText(f"electricity-detail-{index}")
        self.detail_id.hide()
        self.amount = create_typed_input(
            self,
            get_field_spec("electricity.amount"),
            f"electricityAmount{index}",
            "MWh",
        )
        self.acquisition = create_typed_input(
            self,
            get_field_spec("electricity.acquisition"),
            f"electricityAcquisition{index}",
        )
        self.acquisition.addItem("外购", ElectricityAcquisitionMode.PURCHASED)
        self.acquisition.addItem("自发自用", ElectricityAcquisitionMode.SELF_CONSUMED)
        self.attribute = create_typed_input(
            self,
            get_field_spec("electricity.attribute"),
            f"electricityAttribute{index}",
        )
        self.attribute.addItem("常规电力（电网电力）", ElectricityAttribute.ORDINARY)
        self.attribute.addItem("非化石能源电力", ElectricityAttribute.NONFOSSIL)
        self.attribute.addItem("化石能源电力", ElectricityAttribute.FOSSIL)
        self.proof_type = create_typed_input(
            self,
            get_field_spec("electricity.proof_type"),
            f"electricityProofType{index}",
        )
        for value, label in (
            (ElectricityProofType.NONE, "无证明"),
            (ElectricityProofType.CONTRACT_AND_SETTLEMENT, "合同及结算凭证"),
            (ElectricityProofType.GEC, "GEC"),
            (ElectricityProofType.MONTHLY_ORIGINAL_RECORD, "月度原始记录"),
        ):
            self.proof_type.addItem(label, value)
        self.proof_status = create_typed_input(
            self,
            get_field_spec("electricity.proof_status"),
            f"electricityProofStatus{index}",
        )
        self.proof_status.addItem("未提供", ElectricityProofStatus.NOT_PROVIDED)
        self.proof_status.addItem("有效", ElectricityProofStatus.VALID)
        self.proof_status.addItem("无效", ElectricityProofStatus.INVALID)
        remove_button = QPushButton("删除", self)
        remove_button.setObjectName(f"removeElectricityButton{index}")
        remove_button.clicked.connect(lambda: remove(self))
        form.addRow("用电量（MWh）", self.amount)
        form.addRow("取得方式", self.acquisition)
        form.addRow("电力属性", self.attribute)
        form.addRow("证明类型", self.proof_type)
        form.addRow("证明状态", self.proof_status)
        layout.addLayout(form)
        layout.addWidget(remove_button, 0, Qt.AlignmentFlag.AlignRight)

        detail_panel = QWidget(self)
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.parameter_status = QLabel("电力因子：待录入", detail_panel)
        self.parameter_status.setObjectName(f"electricityParameterStatus{index}")
        self.parameter_status.setWordWrap(True)
        self.parameter_factor = QLabel("电力因子：尚未确定", detail_panel)
        self.parameter_factor.setObjectName(f"electricityParameterFactor{index}")
        self.parameter_factor.setWordWrap(True)
        self.parameter_source = QLabel("来源说明：尚未确定", detail_panel)
        self.parameter_source.setObjectName(f"electricityParameterSource{index}")
        self.parameter_source.setWordWrap(True)
        self.parameter_reason = QLabel("采用依据：尚未确定", detail_panel)
        self.parameter_reason.setObjectName(f"electricityParameterReason{index}")
        self.parameter_reason.setWordWrap(True)
        self.professional_details = QLabel("", detail_panel)
        self.professional_details.setObjectName(f"electricityProfessionalDetails{index}")
        self.professional_details.setWordWrap(True)
        self.professional_details.setVisible(False)
        for widget in (
            self.parameter_status,
            self.parameter_factor,
            self.parameter_source,
            self.parameter_reason,
            self.professional_details,
        ):
            detail_layout.addWidget(widget)
        layout.addWidget(detail_panel)

    def show_parameter_state(
        self,
        status: str,
        factor: str,
        source: str,
        reason: str,
        professional_details: str = "",
    ) -> None:
        self.parameter_status.setText(status)
        self.parameter_factor.setText(factor)
        self.parameter_source.setText(source)
        self.parameter_reason.setText(reason)
        self.professional_details.setText(professional_details)

    def set_professional_details_visible(self, visible: bool) -> None:
        self.professional_details.setVisible(visible)

    def build(self, enterprise_id: str, period: AccountingPeriod) -> ElectricityConsumptionDetail | None:
        amount = _value(self.amount)
        return ElectricityConsumptionDetail(
            detail_id=self.detail_id.text().strip(),
            enterprise_id=enterprise_id,
            standard_id=STANDARD_ID,
            accounting_period=period,
            electricity_amount=amount,
            electricity_unit="MWh",
            acquisition_mode=_enum(self.acquisition.currentData(), ElectricityAcquisitionMode),
            attribute=_enum(self.attribute.currentData(), ElectricityAttribute),
            proof_type=_enum(self.proof_type.currentData(), ElectricityProofType),
            proof_status=_enum(self.proof_status.currentData(), ElectricityProofStatus),
        )



class _UnifiedEnergyRow(QWidget):
    """One visual list row for purchased/exported electricity and heat."""

    ELECTRICITY_KINDS = (("购入", "purchased_electricity"), ("输出", "exported_electricity"))
    HEAT_KINDS = (("购入", "purchased_heat"), ("输出", "exported_heat"))

    def __init__(self, index: int, family: str, remove: Callable[[QWidget], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.row_key = uuid4().hex
        self.family = family
        self.kinds = self.HEAT_KINDS if family == "heat" else self.ELECTRICITY_KINDS
        self.setObjectName(f"unifiedEnergyRow{index}")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(4)

        main = QHBoxLayout()
        self.kind = QComboBox(self)
        self.kind.setObjectName(f"energyDirection{index}")
        for label, value in self.kinds:
            self.kind.addItem(label, value)
        self.line_id = QLineEdit(f"energy-{self.row_key}", self)
        self.line_id.setObjectName(f"energyLineId{index}")
        self.line_id.hide()
        self.amount = create_typed_input(self, get_field_spec("electricity.amount"), f"energyAmount{index}")
        self.amount.setPlaceholderText("填写电量或热力量")
        self.unit_label = QLabel("MWh", self)
        self.remove_button = QPushButton("删除", self)
        self.remove_button.setObjectName(f"removeEnergyRow{index}")
        self.remove_button.clicked.connect(lambda _checked=False: remove(self))
        main.addWidget(self.kind, 2)
        main.addWidget(self.amount, 2)
        main.addWidget(self.unit_label)
        main.addStretch(1)
        main.addWidget(self.remove_button)
        outer.addLayout(main)

        self.electricity_details = QWidget(self)
        electricity = QHBoxLayout(self.electricity_details)
        electricity.setContentsMargins(0, 0, 0, 0)
        electricity.setSpacing(6)
        self.attribute = QComboBox(self.electricity_details)
        self.attribute.setObjectName(f"energyElectricityAttribute{index}")
        self.attribute.addItem("购入电网电力", ElectricityAttribute.ORDINARY)
        self.attribute.addItem("购入非化石电力", ElectricityAttribute.NONFOSSIL)
        self.attribute.addItem("自发自用（不计入）", "SELF_CONSUMED_EXCLUDED")
        self.legacy_attribute_notice = QLabel("历史电力属性已保留", self.electricity_details)
        self.legacy_attribute_notice.setObjectName(f"energyLegacyElectricityAttribute{index}")
        self.legacy_attribute_notice.hide()
        self.legacy_attribute: ElectricityAttribute | None = None
        self.legacy_acquisition_mode: ElectricityAcquisitionMode | None = None
        self.legacy_proof_type: ElectricityProofType | None = None
        self.legacy_proof_status: ElectricityProofStatus | None = None
        self.legacy_measured_factor = False
        self.region = QComboBox(self.electricity_details)
        self.region.setObjectName(f"energyElectricityRegion{index}")
        self.factor_mode = QComboBox(self.electricity_details)
        self.factor_mode.setObjectName(f"energyElectricityFactorMode{index}")
        self.factor_mode.addItem("参数库候选", "LIBRARY")
        self.factor_mode.addItem("企业手填", "MANUAL")
        self.factor_selector = QComboBox(self.electricity_details)
        self.factor_selector.setObjectName(f"energyElectricityFactor{index}")
        self.manual_factor = QLineEdit(self.electricity_details)
        self.manual_factor.setObjectName(f"energyElectricityManualFactor{index}")
        self.manual_factor.setPlaceholderText("电力因子")
        self.electricity_source = QLineEdit(self.electricity_details)
        self.electricity_source.setObjectName(f"energyElectricitySource{index}")
        self.electricity_source.setPlaceholderText("手填因子来源说明（可选）")
        electricity.addWidget(self.attribute)
        electricity.addWidget(self.legacy_attribute_notice)
        electricity.addWidget(self.region)
        electricity.addWidget(self.factor_mode)
        electricity.addWidget(self.factor_selector, 2)
        electricity.addWidget(self.manual_factor)
        electricity.addWidget(self.electricity_source, 2)
        outer.addWidget(self.electricity_details)

        self.heat_details = QWidget(self)
        heat = QHBoxLayout(self.heat_details)
        heat.setContentsMargins(0, 0, 0, 0)
        heat.setSpacing(6)
        self.heat_kind = QComboBox(self.heat_details)
        self.heat_kind.setObjectName(f"energyHeatKind{index}")
        self.heat_kind.addItem("饱和蒸汽", SteamKind.SATURATED)
        self.heat_kind.addItem("过热蒸汽", SteamKind.SUPERHEATED)
        self.heat_kind.addItem("热水（暂不支持）", "HOT_WATER")
        self.heat_kind.addItem("其他（暂不支持）", "OTHER")
        for disabled_index in (2, 3):
            item = self.heat_kind.model().item(disabled_index)
            if item is not None:
                item.setEnabled(False)
        self.pressure = create_typed_input(self.heat_details, get_field_spec("heat_pressure"), f"energyHeatPressure{index}", "绝压 MPa")
        self.temperature = create_typed_input(self.heat_details, get_field_spec("heat_temperature"), f"energyHeatTemperature{index}", "℃（过热蒸汽）")
        self.enthalpy_mode = QComboBox(self.heat_details)
        self.enthalpy_mode.setObjectName(f"energyHeatEnthalpyMode{index}")
        self.enthalpy_mode.addItem("按标准表自动取焓", "AUTO")
        self.enthalpy_mode.addItem("手动填写焓值", "MANUAL")
        self.enthalpy = create_typed_input(self.heat_details, get_field_spec("heat_enthalpy"), f"energyHeatEnthalpy{index}", "kJ/kg")
        self.heat_factor_mode = QComboBox(self.heat_details)
        self.heat_factor_mode.setObjectName(f"energyHeatFactorMode{index}")
        self.heat_factor_mode.addItem("标准缺省热力因子", HeatFactorMode.STANDARD_DEFAULT)
        self.heat_factor_mode.addItem("实测热力因子", HeatFactorMode.MEASURED)
        self.measured_heat_factor = QLineEdit(self.heat_details)
        self.measured_heat_factor.setObjectName(f"energyHeatMeasuredFactor{index}")
        self.measured_heat_factor.setPlaceholderText("tCO₂/GJ")
        self.heat_source = QLineEdit(self.heat_details)
        self.heat_source.setObjectName(f"energyHeatSource{index}")
        self.heat_source.setPlaceholderText("实测来源（可选）")
        for widget in (self.heat_kind, self.pressure, self.temperature, self.enthalpy_mode, self.enthalpy, self.heat_factor_mode, self.measured_heat_factor, self.heat_source):
            heat.addWidget(widget, 1)
        outer.addWidget(self.heat_details)

        self.status = QLabel("参数状态：等待录入", self)
        self.status.setObjectName(f"energyParameterState{index}")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)
        self.electricity_source.hide()
        self.manual_factor.hide()
        self.temperature.hide()
        self.enthalpy.hide()
        self.measured_heat_factor.hide()
        self.heat_source.hide()

class _FuelRow(QWidget):
    """Compact two-line fuel entry with separate heat-based and direct-carbon paths."""

    def __init__(
        self,
        index: int,
        remove: Callable[[QWidget], None],
        parent: QWidget | None = None,
        fuel_options: tuple[object, ...] = (),
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"fuelRow{index}")
        self.row_key = uuid4().hex
        self._fuel_options = tuple(fuel_options)
        self._default_selection_reasons: dict[str, str] = {}
        self._legacy_default_values: tuple[str, str, str] | None = None
        self._legacy_source = "AUTO"
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(5)

        header = QHBoxLayout()
        self.title_label = QLabel(f"燃料 {index}", self)
        self.title_label.setObjectName(f"fuelTitle{index}")
        header.addWidget(self.title_label)
        self.parameter_summary = QLabel("参数来源待确定", self)
        self.parameter_summary.setObjectName(f"fuelParameterSummary{index}")
        self.parameter_summary.setWordWrap(True)
        self.parameter_summary.hide()
        header.addStretch(1)
        self.remove_button = QPushButton("删除", self)
        self.remove_button.setObjectName(f"removeFuelButton{index}")
        self.remove_button.clicked.connect(lambda: remove(self))
        header.addWidget(self.remove_button)
        outer.addLayout(header)

        self.internal_id = QLineEdit(f"fuel-{self.row_key}", self)
        self.internal_id.setObjectName("fuelIdInput" if index == 1 else f"fuelIdInput{index}")
        self.internal_id.hide()

        self.fuel_type = QComboBox(self)
        self.fuel_type.setObjectName(f"fuelType{index}")
        self.fuel_type.setProperty("fieldSpecKey", "fuel_type")
        self.fuel_type.setEditable(True)
        self.fuel_type.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.fuel_type.setPlaceholderText("搜索或输入燃料名称")
        self.fuel_type.setMinimumWidth(190)
        self.fuel_type.lineEdit().setMaxLength(120)
        seen: set[tuple[str, str]] = set()
        for option in self._fuel_options:
            label = str(getattr(option, "label", "")).strip()
            fuel_type = getattr(option, "fuel_type", None)
            subject_id = str(getattr(option, "subject_id", ""))
            if not label or label.strip() in {"煤", "煤炭", "其他", "其它"}:
                continue
            aliases = tuple(getattr(option, "aliases", ()) or ())
            for candidate in (label, *aliases):
                candidate = str(candidate).strip()
                key = (candidate, subject_id)
                if not candidate or key in seen:
                    continue
                seen.add(key)
                self.fuel_type.addItem(candidate, fuel_type)
                self.fuel_type.setItemData(self.fuel_type.count() - 1, subject_id, Qt.ItemDataRole.UserRole + 1)
        if self.fuel_type.completer() is not None:
            self.fuel_type.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.fuel_type.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        self.path = create_typed_input(self, get_field_spec("fuel_path"), f"fuelPathInput{index}")
        self.path.addItem("体积", FuelPath.VOLUME)
        self.path.addItem("质量", FuelPath.MASS)
        # Retained as an invisible, disabled legacy value so old workspaces restore
        # without offering heat activity as a new-accounting choice.
        self.path.addItem("", FuelPath.HEAT)
        path_item = self.path.model().item(2) if hasattr(self.path.model(), "item") else None
        if path_item is not None:
            path_item.setEnabled(False)
        self.path.view().setRowHidden(2, True)

        self.activity = create_typed_input(self, get_field_spec("fuel_activity"), f"fuelActivityInput{index}")
        self.activity.setPlaceholderText("活动量")
        self.fuel_type_label = QLabel("燃料种类 / 自定义名称", self)
        self.path_label = QLabel("计量方式", self)
        self.activity_label = QLabel("活动量", self)
        self.carbon_basis_label = QLabel("含碳量方式", self)

        self.lower_heating_value = create_typed_input(self, get_field_spec("fuel_lhv"), f"fuelLhvInput{index}")
        self.carbon = create_typed_input(self, get_field_spec("fuel_carbon"), f"fuelCarbonInput{index}")
        self.carbon_direct = create_typed_input(self, get_field_spec("fuel_carbon"), f"fuelMeasuredCarbonInput{index}")
        self.oxidation = create_typed_input(self, get_field_spec("fuel_oxidation"), f"fuelOxidationInput{index}")
        self.source_reference = create_typed_input(self, get_field_spec("fuel_source_reference"), f"fuelSourceReference{index}")
        self.source_reference.setPlaceholderText("按需填写检测/台账来源说明")

        self.carbon_basis = QComboBox(self)
        self.carbon_basis.setObjectName(f"fuelCarbonBasis{index}")
        self.carbon_basis.addItem("按热值计算", "HEAT_CONTENT")
        self.carbon_basis.addItem("直接实测", "DIRECT")
        self.lhv_source = self._source_combo(index, "lhv")
        self.lhv_source.clear()
        self.lhv_source.addItem("标准缺省", "STANDARD_DEFAULT")
        self.lhv_source.addItem("实测/检测", "MEASURED")
        self.carbon_source = self._source_combo(index, "carbon")
        self.carbon_source.clear()
        self.carbon_source.addItem("标准缺省", "STANDARD_DEFAULT")
        self.direct_carbon_source = self._source_combo(index, "directCarbon")
        self.direct_carbon_source.clear()
        self.direct_carbon_source.addItem("实测/检测", "MEASURED")
        self.oxidation_source = self._source_combo(index, "oxidation")
        self.oxidation_source.clear()
        self.oxidation_source.addItem("标准缺省", "STANDARD_DEFAULT")
        self.oxidation_source.addItem("用户自填", "USER_DEFINED")
        self.lhv_control = self._parameter_control(self.lhv_source, self.lower_heating_value)
        self.carbon_control = self._parameter_control(self.carbon_source, self.carbon)
        self.direct_carbon_control = self._parameter_control(self.direct_carbon_source, self.carbon_direct)
        self.oxidation_control = self._parameter_control(self.oxidation_source, self.oxidation)
        self.lhv_label = QLabel("低位发热量", self)
        self.carbon_label = QLabel("单位热值含碳量", self)
        self.direct_carbon_label = QLabel("实测单位含碳量", self)
        self.oxidation_label = QLabel("碳氧化率", self)
        self.source_reference_label = QLabel("来源资料", self)
        self.calculated_carbon_label = QLabel("按热值计算：待录入", self)
        self.calculated_carbon_label.setObjectName(f"fuelCalculatedCarbon{index}")
        self.calculated_carbon_label.setAccessibleName("按低位发热量计算的单位活动量含碳量，仅供查看")
        self.calculated_carbon_label.setWordWrap(False)

        carbon_value_cell = QWidget(self)
        carbon_value_layout = QHBoxLayout(carbon_value_cell)
        carbon_value_layout.setContentsMargins(0, 0, 0, 0)
        carbon_value_layout.setSpacing(5)
        carbon_value_layout.addWidget(self.carbon_basis, 1)
        self.carbon_calc_cell = QWidget(self)
        calc_layout = QVBoxLayout(self.carbon_calc_cell)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(0)
        calc_layout.addWidget(self.calculated_carbon_label)
        self.carbon_direct_cell = self.direct_carbon_control
        carbon_value_layout.addWidget(self.carbon_calc_cell, 2)
        carbon_value_layout.addWidget(self.carbon_direct_cell, 2)
        self.carbon_direct_cell.hide()
        self.carbon_basis_label.hide()
        self.source_reference_label.hide()

        self.lhv_cell = self.lhv_control
        self.oxidation_cell = self.oxidation_control
        self.source_cell = self.source_reference
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        for column, label in enumerate((self.fuel_type_label, self.path_label, self.activity_label, self.lhv_label, self.carbon_label, self.direct_carbon_label, self.oxidation_label)):
            grid.addWidget(label, 0, column)
        for column, widget in enumerate((self.fuel_type, self.path, self.activity, self.lhv_control, self.carbon_control, carbon_value_cell, self.oxidation_control)):
            grid.addWidget(widget, 1, column)
        self.source_reference.hide()
        grid.addWidget(self.source_reference, 2, 0, 1, 3)
        grid.addWidget(self.lhv_source, 2, 3)
        grid.addWidget(self.carbon_source, 2, 4)
        grid.addWidget(self.oxidation_source, 2, 6)
        for column, stretch in enumerate((3, 1, 2, 2, 2, 3, 1)):
            grid.setColumnStretch(column, stretch)
        outer.addLayout(grid)

        # Backward-compatible, hidden legacy free-text field. New input lives in
        # the searchable fuel selector and is matched to Catalog text exactly.
        self.custom_name = QLineEdit(self)
        self.custom_name.setObjectName(f"fuelCustomName{index}")
        self.custom_name.setPlaceholderText("填写具体燃料名称或煤种")
        self.custom_name.hide()
        self.custom_name_label = QLabel("具体名称", self)
        self.custom_name_label.hide()

        self._update_custom_name_visibility()
        self._last_default_values: tuple[str, str, str] | None = None
        # Old workspace source choices can exceed the reduced V2 selectors.
        # Preserve those choices as hidden compatibility metadata.
        self._legacy_source_modes: dict[str, str] = {}
        self.parameter_source = "AUTO"

    def _carbon_basis_row(self) -> QWidget:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(QLabel("含碳量方式", row))
        layout.addWidget(self.carbon_basis)
        layout.addStretch(1)
        self._carbon_basis_control = row
        return row

    @staticmethod
    def _field_cell(label: QLabel, widget: QWidget) -> QWidget:
        cell = QWidget(label.parentWidget())
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(label)
        layout.addWidget(widget)
        return cell

    @staticmethod
    def _source_combo(index: int, key: str) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName(f"fuel{key.title()}Source{index}")
        combo.addItem("标准缺省", "STANDARD_DEFAULT")
        combo.addItem("计算值", "CALCULATED")
        combo.addItem("实测/检测", "MEASURED")
        combo.addItem("用户自填", "USER_DEFINED")
        combo.setMinimumWidth(94)
        return combo

    @staticmethod
    def _parameter_control(source: QComboBox, edit: QWidget) -> QWidget:
        control = QWidget()
        row = QHBoxLayout(control)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(edit, 1)
        return control

    def _update_custom_name_visibility(self) -> None:
        # The searchable combo itself accepts custom text; the compatibility
        # editor remains hidden and is read only by the legacy state adapter.
        self.custom_name_label.hide()
        self.custom_name.hide()


class _SearchableEnterpriseCombo(QComboBox):
    """Editable recent-name selector with the legacy line-edit convenience API."""

    def text(self) -> str:
        return self.currentText()

    def setText(self, value: str) -> None:
        self.setEditText(value)

    def clear(self) -> None:
        self.setEditText("")


class CarbonMaterialAccountingPage(BasePage):
    """Long, scrollable G06 work sheet for the only implemented industry standard."""

    record_created = Signal(str)
    record_requested = Signal(str)
    canonical_project_requested = Signal(str)

    def __init__(
        self,
        catalog_service: CatalogQueryService | None = None,
        calculator: CarbonMaterialCalculator | None = None,
        record_repository: RecordRepository | None = None,
        standard_id: str = STANDARD_ID,
        project_service: ProjectWorkspaceService | None = None,
        parent: QWidget | None = None,
        calculation_use_case: CarbonAccountingUseCase | None = None,
    ) -> None:
        super().__init__(AppRoute.NEW_ACCOUNTING, parent)
        self.catalog_service = catalog_service or CatalogQueryService.empty()
        self.project_service = project_service
        self.calculation_use_case = calculation_use_case
        self.record_repository = resolve_formal_record_repository(calculation_use_case, record_repository)
        resolver = None
        try:
            resolver = create_g06_parameter_resolver(self.catalog_service.repository)
        except (AttributeError, KeyError, TypeError, ValueError):
            resolver = None
        self._parameter_resolver = resolver
        try:
            self._uat03_parameter_queries = UAT03ParameterQueries(self.catalog_service, resolver) if resolver is not None else None
        except (AttributeError, KeyError, TypeError, ValueError):
            _LOGGER.warning("UAT03 catalog parameter choices are unavailable", exc_info=True)
            self._uat03_parameter_queries = None
        standard_implementation_date = self.catalog_service.standard_implementation_date(standard_id)
        use_case_calculator = getattr(calculation_use_case, "calculator", None)
        if use_case_calculator is not None:
            calculator = use_case_calculator
        elif calculator is None:
            catalog_version = self.catalog_service.standard_version(standard_id)
            calculator = CarbonMaterialCalculator(
                parameter_resolver=resolver,
                standard_version=catalog_version or STANDARD_VERSION,
                standard_implementation_date=standard_implementation_date,
                reference_data_identity_provider=self.catalog_service.reference_data_identity,
            )
        self.calculator = calculator
        self.standard_id = standard_id
        self._calculation_index = 0
        self._latest_record_id: str | None = None
        self._latest_record = None
        self._latest_record_fingerprint: str | None = None
        self._electricity_rows: list[_ElectricityRow] = []
        self._electricity_row_serial = 0
        self._energy_rows: list[_UnifiedEnergyRow] = []
        self._energy_family_rows: dict[str, list[_UnifiedEnergyRow]] = {"electricity": [], "heat": []}
        self._energy_row_serial = 0
        self._unified_energy_cards: dict[str, QWidget] = {}
        self._unified_energy_rows_layouts: dict[str, QVBoxLayout] = {}
        self._fuel_rows: list[_FuelRow] = []
        self._fuel_row_serial = 0
        self._process_rows: dict[str, list[dict[str, object]]] = {
            key: [] for key in ("calcination", "baking", "graphitization", "fume", "fgd")
        }
        self._process_row_serials = {key: 0 for key in self._process_rows}
        self._process_rows_layout: dict[str, QVBoxLayout] = {}
        self._process_sections: dict[str, tuple[str, tuple[str, ...]]] = {}
        self._business_row_serial = 0
        self._output_electricity_row_serial = 0
        self._output_electricity_rows: list[dict[str, object]] = []
        self._heat_row_serials = {"heat": 1, "exported_heat": 1}
        self._heat_rows: dict[str, list[dict[str, object]]] = {"heat": [], "exported_heat": []}
        self._electricity_factor_records = {}
        self._source_statuses: dict[str, QComboBox] = {}
        self._source_cards: dict[str, SourceCard] = {}
        self._source_toggle_buttons: dict[str, QPushButton] = {}
        self._source_toggle_groups: tuple[tuple[str, str, tuple[str, ...]], ...] = (
            ("fuel", "化石燃料", ("CAR-SRC-FUEL-001",)),
            ("calcination", "原料煅烧", ("CAR-SRC-CALCINATION-001",)),
            ("baking", "焙烧/炭化", ("CAR-SRC-BAKING-001",)),
            ("graphitization", "石墨化", ("CAR-SRC-GRAPHITIZATION-001",)),
            ("fume", "烟气焚烧", ("CAR-SRC-FUME-INCINERATION-001",)),
            ("fgd", "烟气脱硫", ("CAR-SRC-FGD-001",)),
            ("electricity", "购入/输出电力", ("CAR-SRC-PURCHASED-ELECTRICITY-001", "CAR-SRC-EXPORTED-ELECTRICITY-001")),
            ("heat", "购入/输出热力", ("CAR-SRC-PURCHASED-HEAT-001", "CAR-SRC-EXPORTED-HEAT-001")),
        )
        self._advanced_process_buttons: list[QPushButton] = []
        self._fields: dict[str, QLineEdit] = {}
        self._material_controls: dict[str, dict[str, QWidget]] = {}
        self._heat_factor_records = {}
        self._legacy_heat_controls: dict[str, QWidget] = {}
        self._professional_detail_widgets: list[QWidget] = []
        # Presentation-only feedback from the existing G05/Domain paths.
        # These caches never become part of CarbonMaterialInput or persistence.
        self._electricity_resolution_states: dict[str, str] = {}
        self._known_source_errors: set[str] = set()
        self._validation_count_override: tuple[int, int] | None = None
        self._calculation_has_result = False
        self._stale_result_notice = False
        self._workspace = project_service.new_workspace() if project_service is not None else ProjectWorkspaceService.new_workspace()
        self._active_unit_index = 0
        self._project_dirty = False
        self._restoring_workspace = False
        self._unit_outcomes: dict[str, dict[str, object]] = {}
        self._geometry_refresh_pending = False
        self._build_page()
        self._default_form_state = self._capture_form_state()
        self._input_dirty = False
        self._project_dirty = False
        self._install_dirty_tracking()
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

    def eventFilter(self, watched: object, event: QEvent) -> bool:  # type: ignore[override]
        """Keep the main page scrollable when the pointer rests on a closed input."""

        if event.type() != QEvent.Type.Wheel or not isinstance(watched, QWidget):
            return super().eventFilter(watched, event)
        control = watched
        while control is not None and control is not self:
            if isinstance(control, (QComboBox, QAbstractSpinBox)):
                break
            control = control.parentWidget()
        if control is None or control is self or not self.isAncestorOf(control):
            return super().eventFilter(watched, event)
        if isinstance(control, QComboBox) and control.view().isVisible():
            return super().eventFilter(watched, event)
        if isinstance(control, QDateEdit) and control.calendarWidget().isVisible():
            return super().eventFilter(watched, event)
        scroll_area = self.window().findChild(QScrollArea, "mainScrollArea")
        if scroll_area is None:
            return super().eventFilter(watched, event)
        delta = event.pixelDelta().y() or event.angleDelta().y() / 120 * 3 * scroll_area.verticalScrollBar().singleStep()
        scrollbar = scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() - round(delta))
        event.accept()
        return True

    def _schedule_layout_refresh(self) -> None:
        if self._geometry_refresh_pending:
            return
        self._geometry_refresh_pending = True
        QTimer.singleShot(0, self, self._refresh_content_geometry)

    def _refresh_content_geometry(self) -> None:
        self._geometry_refresh_pending = False
        layout = self.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
        self.updateGeometry()
        central = getattr(self.window(), "centralWidget", None)
        shell = central() if callable(central) else None
        refresh = getattr(shell, "update_content_geometry", None)
        if callable(refresh):
            refresh()

    def _refresh_enterprise_candidates(self) -> None:
        combo = getattr(self, "enterprise_name", None)
        if not isinstance(combo, QComboBox):
            return
        current = combo.currentText()
        candidates = list_enterprise_name_candidates(self.record_repository, self.project_service)
        blocker = QSignalBlocker(combo)
        line_blocker = QSignalBlocker(combo.lineEdit())
        QComboBox.clear(combo)
        combo.addItems(candidates)
        combo.setEditText(current)
        if combo.completer() is not None:
            combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        del line_blocker
        del blocker

    def set_standard_id(self, standard_id: str) -> None:
        self.standard_id = standard_id
        self.standard_id_label.setText("GB/T 32151.34—2024《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》")
        if hasattr(self, "heat_factor_selector"):
            self._refresh_heat_factor_details()

    def _build_page(self) -> None:
        self.body_layout.setSpacing(16)
        self.add_header("新建核算", "")
        page_description = self.findChild(QLabel, "pageDescription")
        if page_description is not None:
            page_description.hide()

        identity, identity_layout = _card("核算信息与边界", self)
        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.standard_id_label = QLabel("GB/T 32151.34—2024《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》", identity)
        self.standard_id_label.setObjectName("accountingStandardId")
        self.standard_id_label.setWordWrap(True)
        form.addRow("核算标准", self.standard_id_label)
        self.enterprise_name = _SearchableEnterpriseCombo(identity)
        self.enterprise_name.setObjectName("enterpriseNameInput")
        self.enterprise_name.setProperty("fieldSpecKey", "enterprise_name")
        self.enterprise_name.setEditable(True)
        self.enterprise_name.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.enterprise_name.setPlaceholderText("输入企业名称，可从最近使用记录中选择")
        self.enterprise_name.setMaxVisibleItems(12)
        self.enterprise_name.lineEdit().setMaxLength(160)
        self._refresh_enterprise_candidates()
        form.addRow("企业名称（可选填）", self.enterprise_name)
        self.period_type = create_typed_input(identity, get_field_spec("period_type"), "accountingPeriodType")
        self.period_type.addItem("全年", PeriodType.ANNUAL)
        for month in range(1, 13):
            self.period_type.addItem(f"{month}月", (PeriodType.MONTHLY, month))
        self.period_type.addItem("自定义", PeriodType.CUSTOM)
        self.period_type.currentIndexChanged.connect(self._on_period_choice_changed)
        period_row = QWidget(identity)
        period_layout = QHBoxLayout(period_row)
        period_layout.setContentsMargins(0, 0, 0, 0)
        period_layout.setSpacing(10)
        self.period_year = QSpinBox(period_row)
        self.period_year.setObjectName("accountingPeriodYear")
        self.period_year.setProperty("fieldSpecKey", "period_year")
        self.period_year.setRange(2000, 2100)
        self.period_year.setValue(2025)
        self.period_year.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_year.valueChanged.connect(lambda _value: self._refresh_fuel_defaults())
        self.period_year.valueChanged.connect(lambda _value: self._refresh_energy_parameters())
        self.period_month = QSpinBox(period_row)
        self.period_month.setObjectName("accountingPeriodMonth")
        self.period_month.setProperty("fieldSpecKey", "period_month")
        self.period_month.setRange(1, 12)
        self.period_month.setValue(1)
        self.period_month.hide()
        self.period_month.valueChanged.connect(self._sync_period_choice_from_month)
        self.period_year.setPrefix("年份 ")
        self.period_type.setMinimumWidth(140)
        period_layout.addWidget(self.period_year)
        period_layout.addWidget(self.period_type)
        period_layout.addStretch(1)
        form.addRow("核算周期", period_row)
        self.custom_period_row = QWidget(identity)
        custom_layout = QHBoxLayout(self.custom_period_row)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(QLabel("开始日期"))
        self.period_start = QDateEdit(self.custom_period_row)
        self.period_start.setObjectName("accountingPeriodStart")
        self.period_start.setCalendarPopup(True)
        self.period_start.setDisplayFormat("yyyy-MM-dd")
        self.period_start.setDate(QDate(2025, 1, 1))
        custom_layout.addWidget(self.period_start)
        custom_layout.addWidget(QLabel("结束日期"))
        self.period_end = QDateEdit(self.custom_period_row)
        self.period_end.setObjectName("accountingPeriodEnd")
        self.period_end.setCalendarPopup(True)
        self.period_end.setDisplayFormat("yyyy-MM-dd")
        self.period_end.setDate(QDate(2025, 12, 31))
        custom_layout.addWidget(self.period_end)
        self.custom_period_hint = QLabel("自定义日期仅用于内部周期计算，不代表标准报告周期。", self.custom_period_row)
        self.custom_period_hint.setWordWrap(True)
        custom_layout.addWidget(self.custom_period_hint, 1)
        self.custom_period_row.setVisible(False)
        self.period_start.dateChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_end.dateChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_start.dateChanged.connect(lambda _value: self._refresh_fuel_defaults())
        self.period_end.dateChanged.connect(lambda _value: self._refresh_fuel_defaults())
        self.period_start.dateChanged.connect(lambda _value: self._refresh_energy_parameters())
        self.period_end.dateChanged.connect(lambda _value: self._refresh_energy_parameters())
        form.addRow("自定义周期", self.custom_period_row)
        self.custom_period_label = form.labelForField(self.custom_period_row)
        if self.custom_period_label is not None:
            self.custom_period_label.setObjectName("customPeriodLabel")
            self.custom_period_label.hide()
        identity_layout.addLayout(form)

        # Keep the boundary facts in the Domain input and saved workspace,
        # while applying the safe product default without a redundant box.
        self.boundary_confirmed = create_typed_input(
            identity,
            get_field_spec("boundary_confirmed"),
            "boundaryConfirmedCheckBox",
        )
        self.boundary_confirmed.setChecked(True)
        self.boundary_confirmed.hide()
        self.other_activity_present = create_typed_input(
            identity,
            get_field_spec("other_activity_present"),
            "otherIndustryActivityCheckBox",
        )
        self.other_activity_present.hide()
        self.transport_present = create_typed_input(
            identity,
            get_field_spec("transport_present"),
            "upstreamDownstreamTransportCheckBox",
        )
        self.transport_present.hide()
        self.scope_exclusion_notice = QWidget(identity)
        scope_layout = QHBoxLayout(self.scope_exclusion_notice)
        scope_layout.setContentsMargins(0, 0, 0, 0)
        self.scope_exclusion_label = QLabel(
            "已保存的项目标记了本标准未覆盖的行业活动或上下游运输。请单独核算后，再确认本次边界不含这些活动。",
            self.scope_exclusion_notice,
        )
        self.scope_exclusion_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_exclusion_label, 1)
        self.scope_exclusion_acknowledge = QPushButton("确认本次边界不含上述活动", self.scope_exclusion_notice)
        self.scope_exclusion_acknowledge.setObjectName("confirmExcludedActivitiesButton")
        self.scope_exclusion_acknowledge.clicked.connect(self._acknowledge_out_of_scope_activities)
        scope_layout.addWidget(self.scope_exclusion_acknowledge)
        self.scope_exclusion_notice.setVisible(False)
        identity_layout.addWidget(self.scope_exclusion_notice)

        self.report_data_toggle = QCheckBox("补充报告信息与数据来源（可选，不影响普通周期计算）", identity)
        self.report_data_toggle.setObjectName("reportDataDetailsToggle")
        identity_layout.addWidget(self.report_data_toggle)
        self.report_data_details = QWidget(identity)
        self.report_data_details.setObjectName("reportDataDetails")
        report_layout = QVBoxLayout(self.report_data_details)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_form = QFormLayout()
        self.reporting_fields: dict[str, QLineEdit] = {}
        for key, label in (
            ("organization_nature", "单位性质"),
            ("industry", "所属行业"),
            ("social_credit_code", "统一社会信用代码"),
            ("legal_representative", "法定代表人"),
            ("preparer_name", "填报负责人"),
            ("preparer_contact", "负责人联系方式"),
            ("boundary_description", "核算边界说明"),
            ("products_and_process", "主要产品/工艺流程"),
            ("emission_source_identification", "排放源识别说明"),
            ("other_report_information", "其他报告说明"),
        ):
            edit = QLineEdit(self.report_data_details)
            edit.setObjectName(f"report_{key}")
            edit.setPlaceholderText("可留空；作为本次输入和新记录的报告资料快照")
            self.reporting_fields[key] = edit
            report_form.addRow(label, edit)
        report_layout.addWidget(QLabel("年度报告主体与说明", self.report_data_details))
        report_layout.addLayout(report_form)

        self.activity_evidence_fields: dict[str, QLineEdit] = {}
        activity_form = QFormLayout()
        for key, label in (
            ("applies_to", "适用范围说明"), ("source_reference", "来源/凭证定位"),
            ("monitoring_location", "监测地点"), ("monitoring_method", "获取/监测方法"),
            ("instrument", "仪器/计量设备"), ("accuracy", "设备精度"),
            ("recording_frequency", "记录频次"), ("acquisition_time", "数据取得时间"),
            ("note", "补充说明"),
        ):
            edit = QLineEdit(self.report_data_details)
            edit.setObjectName(f"activity_evidence_{key}")
            edit.setPlaceholderText("可选")
            self.activity_evidence_fields[key] = edit
            activity_form.addRow(label, edit)
        report_layout.addWidget(QLabel("可复用活动数据证据", self.report_data_details))
        report_layout.addLayout(activity_form)
        activity_scope_grid = QGridLayout()
        self.activity_evidence_sources: dict[str, QCheckBox] = {}
        for index, (label, source_id) in enumerate(_REPORT_SOURCE_OPTIONS):
            check = QCheckBox(label, self.report_data_details)
            check.setObjectName(f"activityEvidenceSource{index}")
            self.activity_evidence_sources[source_id] = check
            activity_scope_grid.addWidget(check, index // 5, index % 5)
        report_layout.addWidget(QLabel("证据适用的排放源", self.report_data_details))
        report_layout.addLayout(activity_scope_grid)

        self.factor_evidence_fields: dict[str, QLineEdit] = {}
        factor_form = QFormLayout()
        for key, label in (
            ("applies_to", "适用范围说明"), ("source_reference", "来源/检测报告定位"),
            ("sampling_method", "取样方法"), ("sampling_frequency", "取样频次"),
            ("testing_method", "检测方法"), ("testing_frequency", "检测频次"),
            ("referenced_standard", "依据标准"), ("reason", "采用理由/说明"),
        ):
            edit = QLineEdit(self.report_data_details)
            edit.setObjectName(f"factor_evidence_{key}")
            edit.setPlaceholderText("可选；标准缺省值无需重复填写")
            self.factor_evidence_fields[key] = edit
            factor_form.addRow(label, edit)
        report_layout.addWidget(QLabel("可复用实测因子证据", self.report_data_details))
        report_layout.addLayout(factor_form)
        factor_scope_grid = QGridLayout()
        self.factor_evidence_sources: dict[str, QCheckBox] = {}
        for index, (label, source_id) in enumerate(_REPORT_SOURCE_OPTIONS):
            check = QCheckBox(label, self.report_data_details)
            check.setObjectName(f"factorEvidenceSource{index}")
            self.factor_evidence_sources[source_id] = check
            factor_scope_grid.addWidget(check, index // 5, index % 5)
        report_layout.addWidget(QLabel("实测因子证据适用的排放源", self.report_data_details))
        report_layout.addLayout(factor_scope_grid)
        self.report_data_details.setVisible(False)
        self.report_data_toggle.toggled.connect(self.report_data_details.setVisible)
        identity_layout.addWidget(self.report_data_details)
        self.body_layout.addWidget(identity)

        self._build_project_unit_controls()

        source_activity, source_activity_layout = _card("排放源与活动数据", self)
        source_activity.setProperty("dfActivityRegion", True)
        source_activity_layout.setSpacing(12)
        source_navigation_row = QHBoxLayout()
        self.source_navigation = QComboBox(source_activity)
        self.source_navigation.setObjectName("accountingSourceNavigation")
        self.source_navigation.addItem("快速定位排放源", None)
        source_navigation_row.addWidget(self.source_navigation, 1)
        self.quick_calculate_button = QPushButton("检查并计算", source_activity)
        self.quick_calculate_button.setObjectName("quickCalculateAccountingButton")
        self.quick_calculate_button.clicked.connect(self._run_calculation)
        source_navigation_row.addWidget(self.quick_calculate_button)
        source_activity_layout.addLayout(source_navigation_row)
        self._build_source_cards(source_activity_layout)
        for source_id in self._source_cards:
            self.source_navigation.addItem(SOURCE_LABELS[source_id], source_id)
        self.source_navigation.currentIndexChanged.connect(self._jump_to_source)
        self.body_layout.addWidget(source_activity)

        process_card, process_layout = _card("计算依据", self)
        self.process_card = process_card
        self.trace_output = QLabel("点击“计算排放量”后显示分项计算结果。", process_card)
        self.trace_output.setObjectName("calculationTrace")
        self.trace_output.setWordWrap(True)
        process_layout.addWidget(self.trace_output)
        self.trace_professional_details = QLabel(
            "",
            process_card,
        )
        self.trace_professional_details.setObjectName("calculationTraceProfessionalDetails")
        self.trace_professional_details.setWordWrap(True)
        process_layout.addWidget(self.trace_professional_details)
        self._register_professional_details(self.trace_professional_details)
        process_card.setVisible(False)
        self.body_layout.addWidget(process_card)

        result_card, result_layout = _card("核算结果", self)
        self.result_card = result_card
        self.result_total = QLabel("未计算", result_card)
        self.result_total.setObjectName("calculationTotal")
        self.result_total.setWordWrap(True)
        result_layout.addWidget(self.result_total)
        self.result_status = QLabel("状态：尚未计算", result_card)
        self.result_status.setObjectName("calculationStatus")
        result_layout.addWidget(self.result_status)
        self.report_qualification_status = QLabel("年度报告资格：尚未计算", result_card)
        self.report_qualification_status.setObjectName("reportQualificationStatus")
        result_layout.addWidget(self.report_qualification_status)
        self.report_changes_status = QLabel("", result_card)
        self.report_changes_status.setObjectName("reportChangesStatus")
        result_layout.addWidget(self.report_changes_status)
        self.result_breakdown = QLabel("", result_card)
        self.result_breakdown.setObjectName("calculationBreakdown")
        self.result_breakdown.setWordWrap(True)
        result_layout.addWidget(self.result_breakdown)
        self.result_line_details = QLabel("", result_card)
        self.result_line_details.setObjectName("calculationLineDetails")
        self.result_line_details.setWordWrap(True)
        self.result_line_details.setVisible(False)
        result_layout.addWidget(self.result_line_details)
        result_actions = QHBoxLayout()
        self.view_breakdown_button = QPushButton("查看分项结果", result_card)
        self.view_breakdown_button.setObjectName("viewBreakdownButton")
        self.view_breakdown_button.clicked.connect(self._toggle_result_line_details)
        self.view_record_button = QPushButton("查看正式核算记录", result_card)
        self.view_record_button.setObjectName("viewAccountingRecordButton")
        self.view_record_button.setEnabled(False)
        self.view_record_button.clicked.connect(self._open_latest_record)
        result_actions.addWidget(self.view_breakdown_button)
        result_actions.addWidget(self.view_record_button)
        self.export_report_button = QPushButton("导出核算报告（Word）", result_card)
        self.export_report_button.setObjectName("exportAccountingReportButton")
        self.export_report_button.setEnabled(False)
        self.export_report_button.clicked.connect(self._export_latest_record_report)
        result_actions.addWidget(self.export_report_button)
        result_actions.addStretch(1)
        result_layout.addLayout(result_actions)
        result_card.setVisible(False)
        self.body_layout.insertWidget(self.body_layout.indexOf(process_card), result_card)

        quality_card, quality_layout = _card("问题汇总", self)
        self.quality_card = quality_card
        self.validation_list = QTreeWidget(quality_card)
        self.validation_list.setObjectName("calculationValidationList")
        self.validation_list.setHeaderHidden(True)
        self.validation_list.setRootIsDecorated(True)
        self.validation_list.setUniformRowHeights(False)
        self.validation_list.itemClicked.connect(self._focus_validation_item)
        quality_layout.addWidget(self.validation_list)
        quality_card.setVisible(False)
        self.body_layout.addWidget(quality_card)

        status_bar = QFrame(self)
        status_bar.setObjectName("calculationStatusBar")
        status_layout = QGridLayout(status_bar)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setHorizontalSpacing(16)
        status_layout.setVerticalSpacing(4)
        status_layout.setColumnStretch(3, 1)
        self.confirmed_source_count = QLabel("已确认排放源：0", status_bar)
        self.confirmed_source_count.setObjectName("confirmedSourceCount")
        self.error_count = QLabel("错误：0", status_bar)
        self.error_count.setObjectName("calculationErrorCount")
        self.reminder_count = QLabel("提醒：0", status_bar)
        self.reminder_count.setObjectName("calculationReminderCount")
        self.calculation_status_hint = QLabel("填写完成后点击“计算排放量”，软件会集中检查并反馈问题。", status_bar)
        self.calculation_status_hint.setObjectName("calculationStatusHint")
        self.calculation_status_hint.setWordWrap(True)
        status_layout.addWidget(self.confirmed_source_count, 0, 0)
        status_layout.addWidget(self.error_count, 0, 1)
        status_layout.addWidget(self.reminder_count, 0, 2)
        status_layout.addWidget(self.calculation_status_hint, 1, 0, 1, 4)

        self.calculate_button = QPushButton("计算排放量", self)
        self.calculate_button.setObjectName("calculateAccountingButton")
        self.calculate_button.setProperty("primary", True)
        self.calculate_button.clicked.connect(self._run_calculation)
        status_layout.addWidget(self.calculate_button, 0, 4, 2, 1)
        self.body_layout.addWidget(status_bar)
        self.body_layout.addStretch(1)
        self._apply_accounting_style()
        self._refresh_source_cards()

    def _apply_accounting_style(self) -> None:
        """Page-local visuals; exclude optional report fields and export controls."""
        self.setStyleSheet(f"""
            QFrame[dfActivityRegion="true"] QLineEdit,
            QFrame[dfActivityRegion="true"] QComboBox,
            QComboBox#enterpriseNameInput, QComboBox#accountingPeriodType,
            QSpinBox#accountingPeriodYear, QDateEdit#accountingPeriodStart,
            QDateEdit#accountingPeriodEnd {{
                min-height: 28px; padding: 3px 8px;
                border: 1px solid {BORDER}; border-radius: 6px;
                background: {CARD_BACKGROUND}; color: {PRIMARY_TEXT}; font-size: 14px;
            }}
            QComboBox#enterpriseNameInput QLineEdit {{
                border: none; padding: 0; background: transparent;
            }}
            QFrame[dfActivityRegion="true"] QLineEdit:focus,
            QFrame[dfActivityRegion="true"] QComboBox:focus,
            QComboBox#enterpriseNameInput:focus, QComboBox#accountingPeriodType:focus,
            QSpinBox#accountingPeriodYear:focus, QDateEdit#accountingPeriodStart:focus,
            QDateEdit#accountingPeriodEnd:focus {{ border-color: {PRIMARY_BRAND}; }}
            QFrame[dfActivityRegion="true"] QLineEdit:read-only {{
                background: {SURFACE_MUTED}; color: {SECONDARY_TEXT};
            }}
            QFrame[dfActivityRegion="true"] QLineEdit:disabled,
            QFrame[dfActivityRegion="true"] QComboBox:disabled {{
                background: {SURFACE_MUTED}; color: {SECONDARY_TEXT};
            }}
            QFrame[dfActivityRegion="true"] QPushButton {{
                min-height: 32px; padding: 2px 12px;
                border: 1px solid {BORDER}; border-radius: 6px;
                background: {CARD_BACKGROUND}; color: {PRIMARY_TEXT}; font-size: 14px;
            }}
            QFrame[dfActivityRegion="true"] QPushButton:hover,
            QFrame[dfActivityRegion="true"] QPushButton:focus {{
                border-color: {PRIMARY_BRAND}; background: {SURFACE_MUTED};
            }}
            QFrame[dfActivityRegion="true"] QPushButton[sourceState="已启用"] {{
                border-color: {PRIMARY_BRAND}; background: #E6F4FB;
                color: #075985; font-weight: 600;
            }}
            QFrame[dfActivityRegion="true"] QPushButton[sourceState="部分启用"] {{
                border-color: #B54708; background: #FFFAEB; color: #92400E;
            }}
            QFrame[dfActivityRegion="true"] QPushButton:disabled {{
                color: {SECONDARY_TEXT}; background: {SURFACE_MUTED};
            }}
            QPushButton#quickCalculateAccountingButton {{
                border-color: {PRIMARY_BRAND}; color: {PRIMARY_BRAND}; font-weight: 600;
            }}
            QFrame#unifiedElectricityCard, QFrame#unifiedHeatCard {{
                border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE_MUTED};
            }}
            QLabel#unifiedElectricityTitle, QLabel#unifiedHeatTitle {{
                font-size: 16px; font-weight: 600; color: {PRIMARY_TEXT};
            }}
            QLabel#unifiedEnergyHelp, QLabel#parameterSnapshotSummary {{
                color: {SECONDARY_TEXT}; font-size: 13px;
            }}
            QLabel#calculationTotal {{ font-size: 24px; font-weight: 600; color: {PRIMARY_BRAND}; }}
            QLabel#calculationTrace, QLabel#calculationBreakdown {{ font-size: 14px; }}
        """)

    def _build_project_unit_controls(self) -> None:
        toggle = QPushButton("展开项目与核算单元", self)
        toggle.setObjectName("projectUnitControlsToggle")
        toggle.setCheckable(True)
        toggle.setAccessibleName("项目与核算单元")
        card, layout = _card("项目与核算单元", self)
        card.setObjectName("projectUnitControlsCard")
        card.setVisible(False)
        toggle.toggled.connect(card.setVisible)
        toggle.toggled.connect(
            lambda expanded: toggle.setText("收起项目与核算单元" if expanded else "展开项目与核算单元")
        )
        self.project_unit_toggle = toggle
        self.project_unit_card = card
        self.body_layout.addWidget(toggle)
        self.body_layout.addWidget(card)
        project_row = QHBoxLayout()
        project_row.addWidget(QLabel("项目名称", card))
        self.project_name = QLineEdit(self._workspace.name, card)
        self.project_name.setObjectName("accountingProjectName")
        project_row.addWidget(self.project_name, 1)
        self.save_project_button = QPushButton("保存项目", card)
        self.save_project_button.setObjectName("saveAccountingProjectButton")
        self.save_project_button.clicked.connect(self._save_project)
        project_row.addWidget(self.save_project_button)
        self.saved_projects = QComboBox(card)
        self.saved_projects.setObjectName("savedAccountingProjects")
        project_row.addWidget(self.saved_projects)
        self.open_project_button = QPushButton("打开", card)
        self.open_project_button.setObjectName("openAccountingProjectButton")
        self.open_project_button.clicked.connect(self._open_selected_project)
        project_row.addWidget(self.open_project_button)
        self.delete_project_button = QPushButton("删除项目", card)
        self.delete_project_button.setObjectName("deleteAccountingProjectButton")
        self.delete_project_button.clicked.connect(self._delete_selected_project)
        project_row.addWidget(self.delete_project_button)
        layout.addLayout(project_row)

        unit_row = QHBoxLayout()
        self.unit_selector = QComboBox(card)
        self.unit_selector.setObjectName("accountingUnitSelector")
        self.unit_selector.currentIndexChanged.connect(self._switch_unit)
        unit_row.addWidget(self.unit_selector, 1)
        self.add_unit_button = QPushButton("添加核算单元", card)
        self.add_unit_button.setObjectName("addAccountingUnitButton")
        self.add_unit_button.clicked.connect(self._add_accounting_unit)
        unit_row.addWidget(self.add_unit_button)
        self.rename_unit_button = QPushButton("修改名称", card)
        self.rename_unit_button.setObjectName("renameAccountingUnitButton")
        self.rename_unit_button.clicked.connect(self._rename_accounting_unit)
        unit_row.addWidget(self.rename_unit_button)
        self.delete_unit_button = QPushButton("删除单元", card)
        self.delete_unit_button.setObjectName("deleteAccountingUnitButton")
        self.delete_unit_button.clicked.connect(self._delete_accounting_unit)
        unit_row.addWidget(self.delete_unit_button)
        layout.addLayout(unit_row)
        self.manage_process_button = QPushButton("管理多过程实例", card)
        self.manage_process_button.setObjectName("manageProcessInstancesButton")
        self.manage_process_button.setCheckable(True)
        self.manage_process_button.toggled.connect(
            lambda visible: [button.setVisible(visible) for button in self._advanced_process_buttons]
        )
        layout.addWidget(self.manage_process_button)
        self.unit_result_summary = QLabel("当前核算单元尚无成功计算结果。", card)
        self.unit_result_summary.setObjectName("accountingUnitResultSummary")
        self.unit_result_summary.setWordWrap(True)
        layout.addWidget(self.unit_result_summary)
        self.project_save_status = QLabel("项目尚未保存。", card)
        self.project_save_status.setObjectName("accountingProjectSaveStatus")
        layout.addWidget(self.project_save_status)
        self._refresh_unit_selector()
        self._refresh_saved_projects()

    def _unit(self) -> AccountingUnitWorkspace:
        return self._workspace.units[self._active_unit_index]

    def _refresh_unit_selector(self, selected_unit_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.unit_selector)
        self.unit_selector.clear()
        for unit in self._workspace.units:
            label = {
                AccountingUnitType.WHOLE_SITE: "全厂",
                AccountingUnitType.PROCESS: "生产工序",
                AccountingUnitType.OTHER: "其他核算范围",
            }[unit.unit_type]
            self.unit_selector.addItem(f"{unit.name}（{label}）", unit.unit_id)
        target = selected_unit_id or self._workspace.active_unit_id
        index = self.unit_selector.findData(target)
        self.unit_selector.setCurrentIndex(max(0, index))
        self._active_unit_index = self.unit_selector.currentIndex()
        del blocker
        self._refresh_unit_result_summary()

    def _refresh_saved_projects(self) -> None:
        blocker = QSignalBlocker(self.saved_projects)
        current_id = self.saved_projects.currentData()
        self.saved_projects.clear()
        if self.project_service is not None:
            try:
                workspaces = self.project_service.list_all()
            except Exception as exc:
                self._show_project_store_error("读取已保存项目", exc)
                workspaces = ()
            for workspace in workspaces:
                self.saved_projects.addItem(workspace.name, workspace.project_id)
        index = self.saved_projects.findData(current_id)
        if index >= 0:
            self.saved_projects.setCurrentIndex(index)
        del blocker
        enabled = self.project_service is not None and self.saved_projects.count() > 0
        self.open_project_button.setEnabled(enabled)
        self.delete_project_button.setEnabled(enabled)

    def _show_project_store_error(self, action: str, exc: Exception) -> None:
        self.project_save_status.setText(
            f"{action}失败；核算记录数据库未受影响。请检查项目数据文件后重试。"
        )
        QMessageBox.critical(
            self,
            "核算项目数据无法使用",
            f"{action}失败。项目数据可能损坏、被占用或不可写；"
            "既有核算记录没有被修改。\n\n"
            f"详细信息：{exc}",
        )

    def _workspace_with_current_form(self) -> ProjectWorkspace:
        units = list(self._workspace.units)
        units[self._active_unit_index] = replace(
            units[self._active_unit_index],
            form_state=self._capture_form_state(),
        )
        return replace(
            self._workspace,
            name=self.project_name.text().strip() or self._workspace.name,
            active_unit_id=units[self._active_unit_index].unit_id,
            units=tuple(units),
        )

    def _workspace_for_record_link(self, completed_unit: AccountingUnitWorkspace) -> ProjectWorkspace:
        """Build the smallest durable snapshot needed to recover one record link.

        Other units keep their last explicitly saved state. Unsaved input from
        unrelated units is deliberately not persisted by a successful calculation.
        """

        if self.project_service is None:
            return self._workspace
        persisted = self.project_service.get(self._workspace.project_id)
        if persisted is None:
            only_unit = replace(completed_unit, position=0)
            return ProjectWorkspace(
                project_id=self._workspace.project_id,
                name=self.project_name.text().strip() or self._workspace.name,
                active_unit_id=only_unit.unit_id,
                units=(only_unit,),
            )
        units = list(persisted.units)
        for index, saved_unit in enumerate(units):
            if saved_unit.unit_id == completed_unit.unit_id:
                units[index] = replace(
                    saved_unit,
                    form_state=completed_unit.form_state,
                    result_snapshot=completed_unit.result_snapshot,
                    record_ids=completed_unit.record_ids,
                    input_fingerprint=completed_unit.input_fingerprint,
                )
                break
        else:
            units.append(replace(completed_unit, position=len(units)))
        return replace(
            persisted,
            active_unit_id=completed_unit.unit_id,
            units=tuple(units),
        )

    @staticmethod
    def _energy_combo_value(combo: QComboBox) -> str | None:
        value = combo.currentData()
        return getattr(value, "value", value) if value is not None else None

    def _energy_row_state(self, row: _UnifiedEnergyRow) -> dict[str, object]:
        factor_option = row.factor_selector.currentData()
        factor = getattr(factor_option, "factor", None)
        return {
            "row_key": row.row_key,
            "family": row.family,
            "line_id": row.line_id.text(),
            "kind": row.kind.currentData(),
            "amount": row.amount.text(),
            "attribute": row.legacy_attribute.value if row.legacy_attribute is not None else self._energy_combo_value(row.attribute),
            "legacy_attribute": row.legacy_attribute.value if row.legacy_attribute is not None else None,
            "legacy_acquisition_mode": row.legacy_acquisition_mode.value if row.legacy_acquisition_mode is not None else None,
            "legacy_measured_factor": row.legacy_measured_factor,
            "proof_type": row.legacy_proof_type.value if row.legacy_proof_type is not None else None,
            "proof_status": row.legacy_proof_status.value if row.legacy_proof_status is not None else None,
            "region": row.region.currentData(),
            "factor_mode": row.factor_mode.currentData(),
            "factor_id": getattr(factor, "factor_id", None),
            "manual_factor": row.manual_factor.text(),
            "electricity_source": row.electricity_source.text(),
            "heat_kind": self._energy_combo_value(row.heat_kind),
            "pressure": row.pressure.text(),
            "temperature": row.temperature.text(),
            "enthalpy_mode": row.enthalpy_mode.currentData(),
            "enthalpy": row.enthalpy.text(),
            "heat_factor_mode": self._energy_combo_value(row.heat_factor_mode),
            "measured_heat_factor": row.measured_heat_factor.text(),
            "heat_source": row.heat_source.text(),
        }

    def _restore_unified_energy_rows(self, saved_rows: object) -> None:
        if not isinstance(saved_rows, list):
            saved_rows = []
        for old_row in tuple(self._energy_rows):
            self._remove_unified_energy_row(old_row, force=True)
        normalized: list[dict[str, object]] = []
        for item in saved_rows:
            if not isinstance(item, dict):
                continue
            saved = dict(item)
            kind = str(saved.get("kind", "purchased_electricity"))
            if kind == "self_consumed_electricity":
                saved["kind"] = kind = "purchased_electricity"
                # Preserve a stored legacy Canonical acquisition/attribute pair.
                # Previous V2 rows already marked as excluded stay on the V2 path.
                legacy_attribute = saved.get("legacy_attribute", saved.get("attribute"))
                if saved.get("attribute") != "SELF_CONSUMED_EXCLUDED" and legacy_attribute is not None:
                    saved.setdefault("legacy_acquisition_mode", ElectricityAcquisitionMode.SELF_CONSUMED.value)
                    saved.setdefault("legacy_attribute", legacy_attribute)
            if kind not in {value for _, value in _UnifiedEnergyRow.ELECTRICITY_KINDS + _UnifiedEnergyRow.HEAT_KINDS}:
                continue
            normalized.append(saved)
        if not normalized:
            normalized = [{"kind": "purchased_electricity"}, {"kind": "purchased_heat"}]
        present_families = {
            "heat" if str(saved.get("kind", "")).endswith("heat") else "electricity"
            for saved in normalized
        }
        if "electricity" not in present_families:
            normalized.append({"kind": "purchased_electricity"})
        if "heat" not in present_families:
            normalized.append({"kind": "purchased_heat"})
        for saved in normalized:
            kind = str(saved.get("kind", "purchased_electricity"))
            line_id = saved.get("line_id")
            row = self._add_unified_energy_row(kind=kind, line_id=str(line_id) if line_id else None)
            row_key = saved.get("row_key")
            if isinstance(row_key, str) and row_key:
                row.row_key = row_key
            row.amount.setText(str(saved.get("amount", "")))
            attribute = saved.get("attribute")
            attribute_index = row.attribute.findData(attribute)
            if attribute_index < 0:
                try:
                    attribute_index = row.attribute.findData(ElectricityAttribute(attribute))
                except (TypeError, ValueError):
                    attribute_index = -1
            if attribute_index >= 0:
                row.attribute.setCurrentIndex(attribute_index)
            legacy_attribute = saved.get("legacy_attribute", attribute)
            try:
                legacy_value = ElectricityAttribute(legacy_attribute)
            except (TypeError, ValueError):
                legacy_value = None
            if legacy_value is ElectricityAttribute.FOSSIL:
                row.legacy_attribute = legacy_value
            raw_acquisition = saved.get("legacy_acquisition_mode")
            try:
                row.legacy_acquisition_mode = ElectricityAcquisitionMode(raw_acquisition) if raw_acquisition is not None else None
            except (TypeError, ValueError):
                row.legacy_acquisition_mode = None
            legacy_measured_factor = saved.get("legacy_measured_factor") is True
            for key, enum_type, attr_name in (
                ("proof_type", ElectricityProofType, "legacy_proof_type"),
                ("proof_status", ElectricityProofStatus, "legacy_proof_status"),
            ):
                raw = saved.get(key)
                try:
                    setattr(row, attr_name, enum_type(raw) if raw is not None else None)
                except (TypeError, ValueError):
                    pass
            self._refresh_energy_region_options(row)
            region_index = row.region.findData(saved.get("region"))
            if region_index >= 0:
                row.region.setCurrentIndex(region_index)
            mode_index = row.factor_mode.findData(saved.get("factor_mode"))
            if mode_index >= 0:
                row.factor_mode.setCurrentIndex(mode_index)
            row.manual_factor.setText(str(saved.get("manual_factor", "")))
            row.electricity_source.setText(str(saved.get("electricity_source", "")))
            self._refresh_energy_factor_options(row)
            factor_id = saved.get("factor_id")
            if factor_id:
                factor_index = next(
                    (i for i in range(row.factor_selector.count())
                     if getattr(getattr(row.factor_selector.itemData(i), "factor", None), "factor_id", None) == factor_id),
                    -1,
                )
                if factor_index >= 0:
                    row.factor_selector.setCurrentIndex(factor_index)
            try:
                heat_kind_value = SteamKind(saved.get("heat_kind"))
                heat_index = row.heat_kind.findData(heat_kind_value)
                if heat_index >= 0:
                    row.heat_kind.setCurrentIndex(heat_index)
            except (TypeError, ValueError):
                pass
            row.pressure.setText(str(saved.get("pressure", "")))
            row.temperature.setText(str(saved.get("temperature", "")))
            mode_index = row.enthalpy_mode.findData(saved.get("enthalpy_mode"))
            if mode_index >= 0:
                row.enthalpy_mode.setCurrentIndex(mode_index)
            row.enthalpy.setText(str(saved.get("enthalpy", "")))
            try:
                factor_mode = HeatFactorMode(saved.get("heat_factor_mode"))
                factor_index = row.heat_factor_mode.findData(factor_mode)
                if factor_index >= 0:
                    row.heat_factor_mode.setCurrentIndex(factor_index)
            except (TypeError, ValueError):
                pass
            row.measured_heat_factor.setText(str(saved.get("measured_heat_factor", "")))
            row.heat_source.setText(str(saved.get("heat_source", "")))
            # Restore programmatic edits first, then reinstate the migration marker.
            # User edits after restoration clear it through the connected signals.
            row.legacy_measured_factor = legacy_measured_factor
            self._refresh_energy_factor_options(row)
            self._refresh_unified_energy_row(row)
        self._refresh_repeat_delete_controls()

    def _migrate_legacy_energy_rows(self) -> None:
        migrated: list[dict[str, object]] = []
        for row in self._electricity_rows:
            amount = row.amount.text().strip()
            detail_id = row.detail_id.text().strip()
            attr = _enum(row.attribute.currentData(), ElectricityAttribute)
            acquisition = _enum(row.acquisition.currentData(), ElectricityAcquisitionMode)
            if not amount and detail_id in {"", "electricity-detail-1"} and attr is ElectricityAttribute.ORDINARY:
                continue
            migrated.append({
                "kind": "purchased_electricity",
                "line_id": detail_id or f"legacy-electricity-{len(migrated) + 1}",
                "amount": amount,
                "attribute": attr.value,
                "legacy_attribute": attr.value if attr is ElectricityAttribute.FOSSIL else None,
                "legacy_acquisition_mode": acquisition.value if acquisition is ElectricityAcquisitionMode.SELF_CONSUMED else None,
                "proof_type": _enum(row.proof_type.currentData(), ElectricityProofType).value,
                "proof_status": _enum(row.proof_status.currentData(), ElectricityProofStatus).value,
            })
        for row in self._output_electricity_rows:
            amount = _value(row.get("amount"))
            line_id = _value(row.get("id")) or str(row.get("default_line_id", ""))
            factor = row.get("factor")
            factor_id = factor.currentData() if isinstance(factor, QComboBox) else None
            measured = _value(row.get("measured"))
            source = _value(row.get("source"))
            if amount is None and not factor_id and measured is None and line_id == "exported-electricity-1":
                continue
            migrated.append({
                "kind": "exported_electricity", "line_id": line_id or f"legacy-exported-electricity-{len(migrated)+1}",
                "amount": "" if amount is None else str(amount),
                "factor_id": factor_id,
                "factor_mode": "MANUAL" if measured is not None else "LIBRARY",
                "manual_factor": "" if measured is None else str(measured),
                "electricity_source": source or "",
                "legacy_measured_factor": measured is not None,
            })
        for prefix, kind in (("heat", "purchased_heat"), ("exported_heat", "exported_heat")):
            for row in self._heat_rows[prefix]:
                amount = _value(row.get("amount"))
                pressure = _value(row.get("pressure"))
                temperature = _value(row.get("temperature"))
                enthalpy = _value(row.get("enthalpy"))
                measured = _value(row.get("measured"))
                source = _value(row.get("source"))
                line_id = _value(row.get("id")) or str(row.get("default_line_id", ""))
                default_id = "heat-1" if prefix == "heat" else "exported-heat-1"
                if all(value is None for value in (amount, pressure, temperature, enthalpy, measured)) and line_id == default_id:
                    continue
                steam = row.get("steam")
                steam_kind = _enum(steam.currentData(), SteamKind).value if isinstance(steam, QComboBox) else SteamKind.SATURATED.value
                enthalpy_mode = row.get("enthalpy_mode")
                factor_mode = row.get("factor_mode")
                migrated.append({
                    "kind": kind, "line_id": line_id or f"legacy-{kind}-{len(migrated)+1}",
                    "amount": "" if amount is None else str(amount),
                    "heat_kind": steam_kind,
                    "pressure": "" if pressure is None else str(pressure),
                    "temperature": "" if temperature is None else str(temperature),
                    "enthalpy": "" if enthalpy is None else str(enthalpy),
                    "enthalpy_mode": enthalpy_mode.currentData() if isinstance(enthalpy_mode, QComboBox) else "AUTO",
                    "heat_factor_mode": self._energy_combo_value(factor_mode) if isinstance(factor_mode, QComboBox) else HeatFactorMode.STANDARD_DEFAULT.value,
                    "measured_heat_factor": "" if measured is None else str(measured),
                    "heat_source": source or "",
                })
        self._restore_unified_energy_rows(migrated)

    def _capture_form_state(self) -> dict[str, object]:
        values: dict[str, object] = {}
        excluded = {
            "accountingProjectName", "savedAccountingProjects", "accountingUnitSelector",
            "showProfessionalDetailsCheckBox", "accountingPeriodMonth",
        }
        for widget in self.findChildren(QWidget):
            name = widget.objectName()
            if not name or name in excluded:
                continue
            if (
                name.startswith("fuel")
                or name.startswith("removeFuelButton")
                or name.startswith("electricity")
                or name.startswith("removeElectricityButton")
            ):
                continue
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QComboBox):
                values[name] = widget.currentText() if name == "enterpriseNameInput" else widget.currentIndex()
            elif isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QDateEdit):
                values[name] = widget.date().toString("yyyy-MM-dd")
        values["energy_rows"] = [self._energy_row_state(row) for row in self._energy_rows]
        values["electricity_rows"] = [
            {
                "row_key": row.row_key,
                "detail_id": row.detail_id.text(),
                "amount": row.amount.text(),
                "acquisition": row.acquisition.currentIndex(),
                "attribute": row.attribute.currentIndex(),
                "proof_type": row.proof_type.currentIndex(),
                "proof_status": row.proof_status.currentIndex(),
            }
            for row in self._electricity_rows
        ]
        # Retain the count for projects saved by the first Post-V1 implementation.
        values["electricity_row_count"] = len(self._electricity_rows)
        values["fuel_rows"] = [
            {
                "row_key": row.row_key,
                "id": row.internal_id.text(),
                "type": row.fuel_type.currentIndex(),
                "type_value": row.fuel_type.currentData().value if isinstance(row.fuel_type.currentData(), FuelType) else None,
                "fuel_name": row.fuel_type.currentText(),
                "fuel_subject_id": row.fuel_type.currentData(Qt.ItemDataRole.UserRole + 1),
                "path": row.path.currentIndex(),
                "carbon_basis": row.carbon_basis.currentIndex(),
                "activity": row.activity.text(),
                "carbon": row.carbon.text(),
                "carbon_direct": row.carbon_direct.text(),
                "oxidation": row.oxidation.text(),
                "lower_heating_value": row.lower_heating_value.text(),
                "source_reference": row.source_reference.text(),
                "fuel_label": row.custom_name.text(),
                # Keep the legacy numeric indices for old workspace readers and
                # persist the actual semantic source modes for V2 round-trips.
                "lhv_source": row.lhv_source.currentIndex(),
                "carbon_source": row.carbon_source.currentIndex(),
                "direct_carbon_source": row.direct_carbon_source.currentIndex(),
                "oxidation_source": row.oxidation_source.currentIndex(),
                "lhv_source_kind": self._fuel_source_mode(row, "lhv"),
                "carbon_source_kind": self._fuel_source_mode(row, "carbon"),
                "direct_carbon_source_kind": self._fuel_source_mode(row, "direct_carbon"),
                "oxidation_source_kind": self._fuel_source_mode(row, "oxidation"),
                "parameter_source": row.parameter_source,
            }
            for row in self._fuel_rows
        ]
        values["fgd_carbonate_texts"] = {
            str(component.get("component_id")): component["carbonate_type"].currentText()
            for unit in self._process_rows.get("fgd", ())
            for component in unit.get("components", ())
            if isinstance(component, dict) and component.get("component_id") and isinstance(component.get("carbonate_type"), QComboBox)
        }
        values["fgd_factor_provenance"] = {
            str(component.get("component_id")): {
                "mode": component.get("factor_mode"),
                "factor_id": component.get("catalog_factor_id"),
            }
            for unit in self._process_rows.get("fgd", ())
            for component in unit.get("components", ())
            if isinstance(component, dict) and component.get("component_id")
        }
        values["process_instances"] = {
            prefix: [
                {
                    "instance_id": str(row["instance_id"]),
                    "component_ids": [
                        str(component["component_id"])
                        for component in row.get("components", [])
                        if isinstance(component, dict) and component.get("component_id")
                    ],
                    "material_ids": [
                        str(material["line_id"])
                        for material in row.get("materials", [])
                        if isinstance(material, dict) and material.get("line_id")
                    ],
                }
                for row in rows
            ]
            for prefix, rows in self._process_rows.items()
        }
        values["exported_electricity_line_ids"] = [
            str(_value(row["id"]) or row["default_line_id"])
            for row in self._output_electricity_rows
        ]
        values["heat_line_ids"] = {
            prefix: [str(_value(row["id"]) or row["default_line_id"]) for row in rows]
            for prefix, rows in self._heat_rows.items()
        }
        values["heat_legacy_factor_overrides"] = {
            prefix: [bool(row.get("legacy_factor_override")) for row in rows]
            for prefix, rows in self._heat_rows.items()
        }
        values["business_fingerprint_version"] = 2
        values["steam_input_version"] = 2
        return values

    def _restore_form_state(self, state: dict[str, object]) -> None:
        self._restoring_workspace = True
        active_before_restore = self._unit() if self._workspace.units else None
        legacy_fingerprint_matches = bool(
            active_before_restore is not None
            and active_before_restore.input_fingerprint
            and state.get("business_fingerprint_version") != 2
            and active_before_restore.input_fingerprint == self._fingerprint_state(state)
        )
        default_state = self._default_form_state
        for row in tuple(self._electricity_rows):
            self._remove_electricity_row(row)
        self._electricity_row_serial = 0
        stored_electricity_rows = state.get("electricity_rows")
        if isinstance(stored_electricity_rows, list):
            for stored in stored_electricity_rows or [{}]:
                row_key = str(stored.get("row_key", "")) if isinstance(stored, dict) else ""
                self._add_electricity_row(row_key=row_key or None)
            for row, stored in zip(self._electricity_rows, stored_electricity_rows):
                if not isinstance(stored, dict):
                    continue
                row.detail_id.setText(str(stored.get("detail_id", row.detail_id.text())))
                row.amount.setText(str(stored.get("amount", "")))
                for combo, key in (
                    (row.acquisition, "acquisition"),
                    (row.attribute, "attribute"),
                    (row.proof_type, "proof_type"),
                    (row.proof_status, "proof_status"),
                ):
                    index = stored.get(key)
                    if isinstance(index, int) and 0 <= index < combo.count():
                        combo.setCurrentIndex(index)
        else:
            electricity_count = state.get("electricity_row_count", default_state.get("electricity_row_count", 1))
            try:
                electricity_count = max(1, int(electricity_count))
            except (TypeError, ValueError):
                electricity_count = 1
            for _ in range(electricity_count):
                self._add_electricity_row()
        for row in tuple(self._fuel_rows):
            self.fuel_rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._fuel_rows.clear()
        self._fuel_row_serial = 0
        self._fields.pop("fuel_id", None)
        self._fields.pop("fuel_path", None)
        self._fields.pop("fuel_activity", None)
        self._fields.pop("fuel_carbon", None)
        self._fields.pop("fuel_oxidation", None)
        stored_fuel_rows = state.get("fuel_rows", default_state.get("fuel_rows", []))
        if not isinstance(stored_fuel_rows, list):
            stored_fuel_rows = default_state.get("fuel_rows", [])
        if not isinstance(stored_fuel_rows, list):
            stored_fuel_rows = []
        for _ in range(max(1, len(stored_fuel_rows))):
            self._add_fuel_row()
        for row, stored in zip(self._fuel_rows, stored_fuel_rows):
            if not isinstance(stored, dict):
                continue
            stored_row_key = stored.get("row_key")
            if isinstance(stored_row_key, str) and stored_row_key:
                row.row_key = stored_row_key
            row.internal_id.setText(str(stored.get("id", row.internal_id.text())))
            fuel_name = stored.get("fuel_name")
            type_value = stored.get("type_value")
            selected_fuel_type = None
            if isinstance(type_value, str):
                try:
                    selected_fuel_type = FuelType(type_value)
                except ValueError:
                    selected_fuel_type = None
            if selected_fuel_type is None:
                old_index = stored.get("type")
                if isinstance(old_index, int) and 0 <= old_index < len(_FUEL_TYPE_OPTIONS):
                    selected_fuel_type = _FUEL_TYPE_OPTIONS[old_index][1]
            if isinstance(fuel_name, str):
                row.fuel_type.setEditText(fuel_name)
            elif selected_fuel_type is not None:
                selected_index = row.fuel_type.findData(selected_fuel_type)
                if selected_index >= 0:
                    row.fuel_type.setCurrentIndex(selected_index)
                else:
                    row.fuel_type.setEditText(str(stored.get("fuel_label", "")))
            for key in ("path", "carbon_basis"):
                combo = row.path if key == "path" else row.carbon_basis
                index = stored.get(key)
                if isinstance(index, int) and 0 <= index < combo.count():
                    combo.setCurrentIndex(index)
            for widget, key in ((row.activity, "activity"), (row.carbon, "carbon"),
                                (row.carbon_direct, "carbon_direct"),
                                (row.oxidation, "oxidation"), (row.lower_heating_value, "lower_heating_value"),
                                (row.source_reference, "source_reference")):
                widget.setText(str(stored.get(key, "")))
            row.custom_name.setText(str(stored.get("fuel_label", "")))
            row._legacy_source_modes.clear()
            source_controls = (
                ("lhv", row.lhv_source),
                ("carbon", row.carbon_source),
                ("direct_carbon", row.direct_carbon_source),
                ("oxidation", row.oxidation_source),
            )
            legacy_source_indexes = {
                0: "STANDARD_DEFAULT", 1: "CALCULATED", 2: "MEASURED", 3: "USER_DEFINED",
            }
            for source_key, combo in source_controls:
                stored_index_key = f"{source_key}_source"
                # Direct carbon had a separate control in intermediate V2 state;
                # its historical four-item order is still understood here.
                stored_kind = stored.get(f"{source_key}_source_kind")
                if stored_kind not in {
                    "STANDARD_DEFAULT", "CALCULATED", "MEASURED", "USER_DEFINED",
                    "OFFICIAL_PUBLISHED", "PROJECT_SPECIFIED",
                }:
                    index = stored.get(stored_index_key)
                    stored_kind = legacy_source_indexes.get(index) if isinstance(index, int) else None
                if stored_kind is None and source_key == "direct_carbon":
                    basis_index = stored.get("carbon_basis")
                    if basis_index == 1:
                        legacy_carbon_index = stored.get("carbon_source")
                        stored_kind = legacy_source_indexes.get(legacy_carbon_index) if isinstance(legacy_carbon_index, int) else None
                if stored_kind is None:
                    continue
                combo_index = combo.findData(stored_kind)
                if combo_index >= 0:
                    combo.setCurrentIndex(combo_index)
                    row._legacy_source_modes.pop(source_key, None)
                else:
                    row._legacy_source_modes[source_key] = str(stored_kind)
            stored_source = stored.get("parameter_source")
            if stored_source in {"AUTO", "MEASURED", "STANDARD_DEFAULT"}:
                row.parameter_source = str(stored_source)
            if not any(
                key in stored for key in (
                    "lhv_source", "carbon_source", "oxidation_source", "direct_carbon_source",
                    "lhv_source_kind", "carbon_source_kind", "oxidation_source_kind", "direct_carbon_source_kind",
                )
            ):
                legacy_factors = self._fuel_default_factors(row)
                legacy_factor_map = dict(zip(("lhv", "carbon", "oxidation"), legacy_factors or (None, None, None)))
                legacy_inputs = {
                    "lhv": row.lower_heating_value.text().strip(),
                    "carbon": row.carbon.text().strip(),
                    "oxidation": row.oxidation.text().strip(),
                }
                legacy_defaults = {
                    "lhv": "" if legacy_factor_map["lhv"] is None else str(legacy_factor_map["lhv"].value),
                    "carbon": "" if legacy_factor_map["carbon"] is None else str(legacy_factor_map["carbon"].value),
                    "oxidation": "" if legacy_factor_map["oxidation"] is None else str(legacy_factor_map["oxidation"].value * Decimal("100")),
                }
                for key, combo in (("lhv", row.lhv_source), ("carbon", row.carbon_source), ("oxidation", row.oxidation_source)):
                    value = legacy_inputs[key]
                    if not value and legacy_factor_map[key] is not None:
                        mode = "STANDARD_DEFAULT"
                    elif value and value == legacy_defaults[key] and not row.source_reference.text().strip():
                        mode = "STANDARD_DEFAULT"
                    elif value:
                        mode = "MEASURED"
                    else:
                        mode = None
                    self._restore_fuel_source_mode(row, key, mode)
            row._update_custom_name_visibility()
            self._refresh_fuel_row(row)

        stored_processes = state.get("process_instances", default_state.get("process_instances", {}))
        if not isinstance(stored_processes, dict):
            stored_processes = default_state.get("process_instances", {})
        for prefix, rows in self._process_rows.items():
            for old_row in tuple(rows):
                old_widget = old_row.get("widget")
                if isinstance(old_widget, QWidget):
                    old_widget.setParent(None)
                    old_widget.deleteLater()
            rows.clear()
            self._material_controls.pop(prefix, None)
            for key in tuple(self._material_controls):
                if key.startswith(f"{prefix}@"):
                    self._material_controls.pop(key, None)
            for key in tuple(self._fields):
                if key.startswith(f"{prefix}@") or key.startswith(f"{prefix}."):
                    self._fields.pop(key, None)
            saved_rows = stored_processes.get(prefix, []) if isinstance(stored_processes, dict) else []
            if not isinstance(saved_rows, list):
                saved_rows = []
            for saved in saved_rows:
                if not isinstance(saved, dict):
                    continue
                instance_id = saved.get("instance_id")
                if not isinstance(instance_id, str) or not instance_id:
                    continue
                component_ids = saved.get("component_ids", [])
                if not isinstance(component_ids, list) or any(not isinstance(value, str) for value in component_ids):
                    component_ids = []
                material_ids = saved.get("material_ids", [])
                if not isinstance(material_ids, list) or any(not isinstance(value, str) for value in material_ids):
                    material_ids = []
                self._add_process_row(
                    prefix,
                    instance_id=instance_id,
                    component_ids=tuple(component_ids),
                    material_ids=tuple(material_ids),
                )
            self._bind_process_aliases(prefix)

        stored_output_ids = state.get("exported_electricity_line_ids", default_state.get("exported_electricity_line_ids", []))
        if not isinstance(stored_output_ids, list) or any(not isinstance(item, str) for item in stored_output_ids):
            stored_output_ids = default_state.get("exported_electricity_line_ids", [])
        if not stored_output_ids:
            stored_output_ids = ["exported-electricity-1"]
        while len(self._output_electricity_rows) > len(stored_output_ids):
            row = self._output_electricity_rows[-1]
            widget = row["widget"]
            if isinstance(widget, QWidget):
                self._remove_output_electricity_row(widget)
        while len(self._output_electricity_rows) < len(stored_output_ids):
            self._add_output_electricity_row(line_id=stored_output_ids[len(self._output_electricity_rows)])
        for row, line_id in zip(self._output_electricity_rows, stored_output_ids):
            if line_id:
                row["default_line_id"] = line_id
        self._bind_output_electricity_aliases()

        stored_heat_ids = state.get("heat_line_ids", default_state.get("heat_line_ids", {}))
        if not isinstance(stored_heat_ids, dict):
            stored_heat_ids = default_state.get("heat_line_ids", {})
        for prefix, rows in self._heat_rows.items():
            saved_ids = stored_heat_ids.get(prefix, []) if isinstance(stored_heat_ids, dict) else []
            if not isinstance(saved_ids, list) or any(not isinstance(item, str) for item in saved_ids):
                saved_ids = default_state.get("heat_line_ids", {}).get(prefix, [])
            if not saved_ids:
                saved_ids = [f"{prefix.replace('_', '-')}-1"]
            while len(rows) > len(saved_ids):
                row_widget = rows[-1]["widget"]
                if isinstance(row_widget, QWidget):
                    self._remove_heat_row(prefix, row_widget)
            while len(rows) < len(saved_ids):
                self._add_heat_row(prefix, line_id=saved_ids[len(rows)])
            for row, line_id in zip(rows, saved_ids):
                if line_id:
                    row["default_line_id"] = line_id
            self._bind_heat_aliases(prefix)
        legacy_steam_state = not isinstance(state.get("steam_input_version"), int) or state.get("steam_input_version", 0) < 2
        by_name: dict[str, QWidget] = {}
        for widget in self.findChildren(QWidget):
            if widget.objectName():
                by_name[widget.objectName()] = widget
        def apply_values(values: dict[str, object]) -> None:
            for name, value in values.items():
                widget = by_name.get(name)
                if widget is None:
                    continue
                if isinstance(widget, QLineEdit) and isinstance(value, str):
                    widget.setText(value)
                elif isinstance(widget, QComboBox) and name == "enterpriseNameInput" and isinstance(value, str):
                    widget.setEditText(value)
                elif isinstance(widget, QComboBox) and isinstance(value, int) and 0 <= value < widget.count():
                    widget.setCurrentIndex(value)
                elif isinstance(widget, QSpinBox) and isinstance(value, int):
                    widget.setValue(value)
                elif isinstance(widget, QCheckBox) and isinstance(value, bool):
                    widget.setChecked(value)
                elif isinstance(widget, QDateEdit) and isinstance(value, str):
                    parsed = QDate.fromString(value, "yyyy-MM-dd")
                    if parsed.isValid():
                        widget.setDate(parsed)

        # A blank unit must not inherit controls from the previously active unit.
        apply_values(default_state)
        apply_values(state)
        c2_texts = state.get("fgd_carbonate_texts", default_state.get("fgd_carbonate_texts", {}))
        c2_provenance = state.get("fgd_factor_provenance", {})
        if not isinstance(c2_provenance, dict):
            c2_provenance = {}
        if isinstance(c2_texts, dict):
            for unit in self._process_rows.get("fgd", ()):
                for component in unit.get("components", ()):
                    if not isinstance(component, dict):
                        continue
                    selector = component.get("carbonate_type")
                    component_id = component.get("component_id")
                    text = c2_texts.get(str(component_id)) if component_id else None
                    if isinstance(selector, QComboBox) and isinstance(text, str):
                        selector.setEditText(text)
                    factor_widget = component.get("ef1")
                    option = self._carbonate_option_for_text(selector.currentText()) if isinstance(selector, QComboBox) else None
                    saved = c2_provenance.get(str(component_id), {}) if component_id else {}
                    mode = saved.get("mode") if isinstance(saved, dict) else None
                    factor_id = saved.get("factor_id") if isinstance(saved, dict) else None
                    if mode == "CATALOG":
                        if option is not None and option.factor.factor_id == factor_id and isinstance(factor_widget, QLineEdit):
                            if not factor_widget.text().strip():
                                blocker = QSignalBlocker(factor_widget)
                                factor_widget.setText(str(option.factor.value))
                                del blocker
                            component["factor_mode"] = "CATALOG"
                            component["catalog_factor_id"] = option.factor.factor_id
                        else:
                            if isinstance(factor_widget, QLineEdit):
                                blocker = QSignalBlocker(factor_widget)
                                factor_widget.clear()
                                del blocker
                            component["factor_mode"] = None
                            component["catalog_factor_id"] = None
                    elif mode in {"USER_DEFINED", "MEASURED"}:
                        component["factor_mode"] = mode
                        component["catalog_factor_id"] = None
                    elif isinstance(factor_widget, QLineEdit) and factor_widget.text().strip():
                        # Older workspaces persisted a factor amount without a
                        # source selection. Preserve its previous measured-value
                        # meaning; never relabel it as a catalog default.
                        component["factor_mode"] = "MEASURED"
                        component["catalog_factor_id"] = None
                    else:
                        component["factor_mode"] = None
                        component["catalog_factor_id"] = None
        if legacy_steam_state:
            self._convert_legacy_steam_amounts_to_tonnes()
            for prefix, rows in self._heat_rows.items():
                for row in rows:
                    enthalpy = row.get("enthalpy")
                    mode = row.get("enthalpy_mode")
                    if isinstance(enthalpy, QLineEdit) and enthalpy.text().strip() and isinstance(mode, QComboBox):
                        mode.setCurrentIndex(mode.findData("MANUAL"))
                    self._set_legacy_heat_factor_mode(row)
        else:
            legacy_overrides = state.get("heat_legacy_factor_overrides", {})
            if isinstance(legacy_overrides, dict):
                for prefix, rows in self._heat_rows.items():
                    values = legacy_overrides.get(prefix, [])
                    if isinstance(values, list):
                        for row, value in zip(rows, values):
                            row["legacy_factor_override"] = value is True
        self._refresh_all_heat_enthalpy_previews()
        if isinstance(state.get("energy_rows"), list):
            self._restore_unified_energy_rows(state.get("energy_rows"))
        elif not state and isinstance(default_state.get("energy_rows"), list):
            self._restore_unified_energy_rows(default_state.get("energy_rows"))
        else:
            self._migrate_legacy_energy_rows()
        self.boundary_confirmed.setChecked(True)
        self.scope_exclusion_notice.setVisible(
            self.other_activity_present.isChecked() or self.transport_present.isChecked()
        )
        self.validation_list.clear()
        self.quality_card.setVisible(False)
        self.process_card.setVisible(False)
        self.result_card.setVisible(False)
        self.result_line_details.setVisible(False)
        self._calculation_has_result = False
        for card in self._source_cards.values():
            card.check_result_label.clear()
        self._restoring_workspace = False
        self._input_dirty = False
        self._refresh_heat_factor_details()
        self._refresh_electricity_rows()
        self._refresh_source_cards()
        if legacy_fingerprint_matches and active_before_restore is not None and active_before_restore.result_snapshot is not None:
            migrated_fingerprint = self._current_business_fingerprint()
            if migrated_fingerprint is not None:
                current_unit = self._unit()
                units = list(self._workspace.units)
                units[self._active_unit_index] = replace(
                    current_unit,
                    form_state=self._capture_form_state(),
                    input_fingerprint=migrated_fingerprint,
                )
                self._workspace = replace(self._workspace, units=tuple(units))
        self._restore_unit_result()

    def _switch_unit(self, index: int) -> None:
        if self._restoring_workspace or index < 0 or index >= len(self._workspace.units):
            return
        if index == self._active_unit_index:
            return
        self._workspace = self._workspace_with_current_form()
        selected = self._workspace.units[index]
        self._active_unit_index = index
        self._workspace = replace(self._workspace, active_unit_id=selected.unit_id)
        self._restore_form_state(selected.form_state)
        self._project_dirty = True
        self.project_save_status.setText(f"项目有未保存的修改（当前单元：{selected.name}）。")

    def _add_accounting_unit(self) -> None:
        kinds = ("全厂", "生产工序", "其他核算范围")
        kind, accepted = QInputDialog.getItem(self, "添加核算单元", "单元类型", kinds, 1, False)
        if not accepted:
            return
        name, accepted = QInputDialog.getText(self, "添加核算单元", "核算单元名称")
        if not accepted or not name.strip():
            return
        self._workspace = self._workspace_with_current_form()
        unit = AccountingUnitWorkspace(
            unit_id=f"unit.{uuid4().hex}",
            name=name.strip(),
            unit_type={"全厂": AccountingUnitType.WHOLE_SITE, "生产工序": AccountingUnitType.PROCESS, "其他核算范围": AccountingUnitType.OTHER}[kind],
            position=len(self._workspace.units),
            form_state={},
        )
        self._workspace = replace(self._workspace, active_unit_id=unit.unit_id, units=(*self._workspace.units, unit))
        self._refresh_unit_selector(unit.unit_id)
        self._restore_form_state(unit.form_state)
        for row in self._fuel_rows:
            self._refresh_fuel_row(row, initialize_defaults=True)
        self._project_dirty = True
        self.project_save_status.setText("项目有未保存的修改。")

    def _rename_accounting_unit(self) -> None:
        unit = self._unit()
        name, accepted = QInputDialog.getText(self, "修改核算单元名称", "核算单元名称", text=unit.name)
        if not accepted or not name.strip():
            return
        units = list(self._workspace.units)
        units[self._active_unit_index] = replace(unit, name=name.strip())
        self._workspace = replace(self._workspace, units=tuple(units))
        self._refresh_unit_selector(unit.unit_id)
        self._project_dirty = True
        self.project_save_status.setText("项目有未保存的修改。")

    def _delete_accounting_unit(self) -> None:
        if len(self._workspace.units) <= 1:
            QMessageBox.information(self, "无法删除", "项目必须至少保留一个核算单元。")
            return
        unit = self._unit()
        answer = QMessageBox.question(self, "删除核算单元", f"删除“{unit.name}”的未保存项目数据？历史核算记录不会删除。")
        if answer != QMessageBox.StandardButton.Yes:
            return
        units = [item for item in self._workspace.units if item.unit_id != unit.unit_id]
        target = units[max(0, self._active_unit_index - 1)]
        self._workspace = replace(self._workspace, active_unit_id=target.unit_id, units=tuple(units))
        self._refresh_unit_selector(target.unit_id)
        self._restore_form_state(target.form_state)
        self._project_dirty = True
        self.project_save_status.setText("项目有未保存的修改。历史核算记录未删除。")

    def _save_project(self) -> bool:
        name = self.project_name.text().strip()
        if not name:
            QMessageBox.warning(self, "项目名称不能为空", "请填写项目名称后再保存。")
            return False
        self._workspace = self._workspace_with_current_form()
        if self.project_service is not None:
            try:
                self.project_service.save(self._workspace)
            except Exception as exc:
                QMessageBox.critical(self, "保存失败", f"项目未能保存：{exc}")
                return False
        self._project_dirty = False
        self._input_dirty = False
        self.project_save_status.setText("项目已保存；历史核算记录仍独立保存。")
        self._refresh_saved_projects()
        self._refresh_enterprise_candidates()
        return True

    def _open_selected_project(self) -> None:
        if self.project_service is None:
            return
        project_id = self.saved_projects.currentData()
        try:
            workspace = self.project_service.get(str(project_id)) if project_id else None
        except Exception as exc:
            self._show_project_store_error("打开项目", exc)
            return
        if workspace is None:
            return
        if self._project_dirty and not self._confirm_save_discard_cancel("打开其他项目"):
            return
        if any(unit.canonical_input is not None for unit in workspace.units):
            self.canonical_project_requested.emit(workspace.project_id)
            return
        self._workspace = workspace
        self.project_name.setText(workspace.name)
        self._active_unit_index = next(i for i, unit in enumerate(workspace.units) if unit.unit_id == workspace.active_unit_id)
        self._refresh_unit_selector(workspace.active_unit_id)
        self._restore_form_state(workspace.units[self._active_unit_index].form_state)
        self._refresh_enterprise_candidates()
        self._project_dirty = False
        self.project_save_status.setText("已打开已保存项目。")

    def _delete_selected_project(self) -> None:
        if self.project_service is None:
            return
        project_id = self.saved_projects.currentData()
        if not project_id:
            return
        answer = QMessageBox.question(self, "删除项目", "删除所选项目及其未完成输入？既有核算记录和审计不会删除。")
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = self.project_service.delete(str(project_id))
        if deleted and str(project_id) == self._workspace.project_id:
            self._workspace = self.project_service.new_workspace()
            self.project_name.setText(self._workspace.name)
            self._active_unit_index = 0
            self._refresh_unit_selector(self._workspace.active_unit_id)
            self._restore_form_state({})
            self._project_dirty = False
            self._input_dirty = False
            self.project_save_status.setText("项目已删除；历史核算记录和审计未删除。")
        self._refresh_saved_projects()

    def _refresh_unit_result_summary(self) -> None:
        if not hasattr(self, "unit_result_summary"):
            return
        unit = self._workspace.units[self._active_unit_index]
        if unit.result_snapshot is None:
            self.unit_result_summary.setText(f"{unit.name}：尚无成功计算结果。")
            return
        is_calculation_stale = self._calculation_result_is_stale(unit)
        current_fingerprint = self._current_business_fingerprint() if hasattr(self, "enterprise_name") else None
        report_changed = current_fingerprint is None or current_fingerprint != unit.input_fingerprint
        if is_calculation_stale:
            state = "计算输入已变更，上一计算结果已过期"
        elif report_changed:
            state = "报告信息已修改，需重新生成正式记录才能固化这些变化"
        else:
            state = "上次成功结果"
        self.unit_result_summary.setText(
            f"{unit.name}：{state} {unit.result_snapshot.get('total_display', '—')}。重新计算会新增记录，不覆盖历史记录。"
        )

    @staticmethod
    def _fingerprint_state(state: dict[str, object]) -> str:
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def _fingerprint_business_input(cls, input_value: object, *, scope: str = "all") -> str:
        tuple_sort_keys = {
            "source_states": "source_id",
            "fuel_inputs": "fuel_id",
            "electricity_details": "detail_id",
            "exported_electricity": "line_id",
            "purchased_heat": "line_id",
            "exported_heat": "line_id",
            "calcinations": "instance_id",
            "bakings": "instance_id",
            "graphitizations": "instance_id",
            "fume_incinerations": "instance_id",
            "fgd_units": "instance_id",
        }
        legacy_process_aliases = {"calcination", "baking", "graphitization", "fume_incineration", "fgd"}
        presentation_metadata = {
            "source_reference", "source_location", "selection_reason", "evidence_ref_ids",
        }

        def normalize(
            value: object,
            field_name: str | None = None,
            *,
            root: bool = False,
            numeric_value: bool = False,
            report_payload: bool = False,
        ) -> object:
            if value is None or isinstance(value, (str, bool, int)):
                if numeric_value and isinstance(value, str):
                    try:
                        decimal = Decimal(value)
                        rendered = format(decimal, "f")
                        if "." in rendered:
                            rendered = rendered.rstrip("0").rstrip(".")
                        return "0" if rendered in {"-0", ""} else rendered
                    except InvalidOperation:
                        return value
                return value
            if isinstance(value, Decimal):
                if not value.is_finite():
                    raise ValueError("business input contains a non-finite Decimal")
                rendered = format(value, "f")
                if "." in rendered:
                    rendered = rendered.rstrip("0").rstrip(".")
                return "0" if rendered in {"-0", ""} else rendered
            if isinstance(value, float):
                raise TypeError("business fingerprints do not accept float values")
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if is_dataclass(value):
                result: dict[str, object] = {}
                wrapper_fields = {item.name for item in dataclass_fields(value)}
                is_value_wrapper = "value" in wrapper_fields and bool(wrapper_fields & {"unit", "source_kind"})
                for data_field in dataclass_fields(value):
                    if root and data_field.name == "input_id":
                        continue
                    if root and data_field.name in legacy_process_aliases:
                        continue
                    if root and scope == "calculation" and data_field.name == "reporting_data":
                        continue
                    if root and scope == "reporting" and data_field.name != "reporting_data":
                        continue
                    if scope == "calculation" and data_field.name in presentation_metadata:
                        continue
                    if scope == "reporting" and not root and not report_payload and data_field.name not in presentation_metadata:
                        continue
                    result[data_field.name] = normalize(
                        getattr(value, data_field.name), data_field.name,
                        numeric_value=is_value_wrapper and data_field.name == "value",
                        report_payload=report_payload or (root and data_field.name == "reporting_data"),
                    )
                return result
            if isinstance(value, Mapping):
                result = {}
                is_value_wrapper = "value" in value and bool({"unit", "source_kind"} & set(value))
                for key, item in value.items():
                    key_text = str(key)
                    if root and key_text == "input_id":
                        continue
                    if root and key_text in legacy_process_aliases:
                        continue
                    if root and scope == "calculation" and key_text == "reporting_data":
                        continue
                    if root and scope == "reporting" and key_text != "reporting_data":
                        continue
                    if scope == "calculation" and key_text in presentation_metadata:
                        continue
                    if scope == "reporting" and not root and not report_payload and key_text not in presentation_metadata:
                        continue
                    result[key_text] = normalize(
                        item, key_text, numeric_value=is_value_wrapper and key_text == "value",
                        report_payload=report_payload or (root and key_text == "reporting_data"),
                    )
                return result
            if isinstance(value, (tuple, list)):
                normalized_values = [normalize(item) for item in value]
                sort_key = tuple_sort_keys.get(field_name or "")
                if sort_key:
                    normalized_values.sort(key=lambda item: str(item.get(sort_key, "")) if isinstance(item, dict) else "")
                elif field_name == "components":
                    normalized_values.sort(
                        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    )
                return normalized_values
            raise TypeError(f"unsupported business fingerprint value: {type(value).__name__}")

        payload = json.dumps(normalize(input_value, root=True), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _current_business_fingerprint(self) -> str | None:
        try:
            return self._fingerprint_business_input(self._input(increment=False, render_electricity=False))
        except (DomainValidationError, InvalidOperation, TypeError, ValueError):
            return None

    def _current_calculation_fingerprint(self) -> str | None:
        try:
            return self._fingerprint_business_input(
                self._input(increment=False, render_electricity=False), scope="calculation",
            )
        except (DomainValidationError, InvalidOperation, TypeError, ValueError):
            return None

    def _saved_calculation_fingerprint(self, unit) -> str | None:
        result = unit.result_snapshot or {}
        saved = result.get("calculation_fingerprint")
        if isinstance(saved, str) and saved:
            return saved
        record_id = result.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            record_id = unit.record_ids[-1] if unit.record_ids else None
        getter = getattr(self.record_repository, "get_raw_input_snapshot", None)
        if not record_id or not callable(getter):
            return None
        try:
            raw_snapshot = getter(record_id)
            if isinstance(raw_snapshot, Mapping):
                return self._fingerprint_business_input(raw_snapshot, scope="calculation")
        except Exception:
            return None
        return None

    def _saved_business_fingerprint(self, unit) -> str | None:
        result = unit.result_snapshot or {}
        record_id = result.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            record_id = unit.record_ids[-1] if unit.record_ids else None
        getter = getattr(self.record_repository, "get_raw_input_snapshot", None)
        if not record_id or not callable(getter):
            return None
        try:
            raw_snapshot = getter(record_id)
            if isinstance(raw_snapshot, Mapping):
                return self._fingerprint_business_input(raw_snapshot)
        except Exception:
            return None
        return None

    def _calculation_result_is_stale(self, unit) -> bool:
        current = self._current_calculation_fingerprint()
        saved = self._saved_calculation_fingerprint(unit)
        if current is not None and saved is not None:
            return current != saved
        full = self._current_business_fingerprint()
        return not unit.input_fingerprint or full is None or full != unit.input_fingerprint

    def _restore_unit_result(self) -> None:
        result = self._unit().result_snapshot
        if not result:
            self._stale_result_notice = False
            self.result_card.setVisible(False)
            self.process_card.setVisible(False)
            self._calculation_has_result = False
            self._refresh_unit_result_summary()
            return
        unit = self._unit()
        if self._calculation_result_is_stale(unit):
            self._stale_result_notice = True
            self.result_card.setVisible(False)
            self.process_card.setVisible(False)
            self._calculation_has_result = False
            self._refresh_unit_result_summary()
            return
        self._stale_result_notice = False
        self.result_card.setVisible(True)
        self.result_total.setText(f"温室气体排放总量：{result.get('total_display', '—')}")
        self.result_status.setText(f"核算状态：{result.get('status_label', '已完成')}")
        self.result_breakdown.setText(str(result.get("breakdown", "")))
        self.report_qualification_status.setText(
            "年度报告资格：" + str(result.get("report_qualification", "历史记录未保存该信息。"))
        )
        self.report_changes_status.setText("")
        self.result_line_details.setText(str(result.get("line_details", "")))
        self.trace_professional_details.setText(str(result.get("trace_details", "")))
        self.parameter_snapshot_summary.setText(
            str(result.get("parameter_snapshot_summary", "历史参数快照已保留在核算记录中。"))
        )
        self.result_line_details.setVisible(bool(result.get("show_breakdown", False)))
        self._calculation_has_result = True
        self._latest_record_id = result.get("record_id") or (unit.record_ids[-1] if unit.record_ids else None)
        self._latest_record = self._record_for_report()
        self._latest_record_fingerprint = self._saved_business_fingerprint(unit)
        self.view_record_button.setEnabled(bool(self._latest_record_id))
        self._sync_report_export_gate()
        if self._current_business_fingerprint() != unit.input_fingerprint:
            self.report_changes_status.setText("报告资料已修改，需重新计算生成正式记录才能固化这些变化。")
        self._refresh_unit_result_summary()

    def _confirm_save_discard_cancel(self, action: str) -> bool:
        answer = QMessageBox.question(
            self,
            "保存项目修改？",
            f"当前核算项目有未保存修改。是否先保存再{action}？",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self._save_project()
        return answer == QMessageBox.StandardButton.Discard

    def confirm_project_close(self) -> bool:
        if self.project_service is None or not self._project_dirty:
            return True
        return self._confirm_save_discard_cancel("关闭软件")

    def _register_professional_details(self, widget: QWidget) -> None:
        self._professional_detail_widgets.append(widget)
        widget.hide()

    def _set_professional_details_visible(self, visible: bool) -> None:
        for widget in self._professional_detail_widgets:
            widget.hide()
        for row in self._electricity_rows:
            row.set_professional_details_visible(False)
        for controls in self._material_controls.values():
            details = controls.get("professional_details")
            if details is not None:
                details.hide()

    def _toggle_result_line_details(self) -> None:
        visible = not self.result_line_details.isVisible()
        self.result_line_details.setVisible(visible)
        self.view_breakdown_button.setText("收起分项结果" if visible else "查看分项结果")

    def _open_latest_record(self) -> None:
        record_id = self._latest_record_id
        if record_id:
            self.record_requested.emit(record_id)

    def _record_for_report(self):
        record = self._latest_record
        if record is not None and getattr(record, "record_id", None) == self._latest_record_id:
            return record
        record_id = self._latest_record_id
        getter = getattr(self.record_repository, "get", None)
        if record_id and callable(getter):
            try:
                return getter(record_id)
            except Exception:
                _LOGGER.warning("Unable to load the saved record for report export", exc_info=True)
        return None

    def _sync_report_export_gate(self) -> None:
        button = getattr(self, "export_report_button", None)
        if button is None:
            return
        record = self._record_for_report()
        current = self._current_business_fingerprint() if record is not None else None
        fresh = bool(
            self._calculation_has_result
            and not self._stale_result_notice
            and record is not None
            and current is not None
            and self._latest_record_fingerprint is not None
            and current == self._latest_record_fingerprint
        )
        button.setEnabled(fresh)

    def _export_latest_record_report(self) -> None:
        self._sync_report_export_gate()
        if not self.export_report_button.isEnabled():
            return
        record = self._record_for_report()
        if record is not None:
            export_saved_record_report(self, self.record_repository, record)

    def _scroll_to_widget(self, widget: QWidget) -> None:
        scroll_area = self.window().findChild(QScrollArea, "mainScrollArea")
        if scroll_area is not None:
            scroll_area.ensureWidgetVisible(widget)

    def _jump_to_source(self, _index: int) -> None:
        source_id = self.source_navigation.currentData()
        card = self._source_cards.get(source_id)
        if card is not None:
            QTimer.singleShot(0, self, lambda: self._scroll_to_widget(card))

    def _focus_validation_item(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        target_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(target_name, str):
            return
        source_id = item.data(0, Qt.ItemDataRole.UserRole + 1)
        card = self._source_cards.get(source_id) if isinstance(source_id, str) else None
        if card is not None:
            card.set_expanded(True)
        widget = self.findChild(QWidget, target_name)
        if widget is None and card is not None:
            widget = card
        if widget is not None:
            QTimer.singleShot(0, self, lambda _widget=widget: (self._scroll_to_widget(_widget), _widget.setFocus()))

    def _focus_first_error(self) -> None:
        for index in range(self.validation_list.topLevelItemCount()):
            root = self.validation_list.topLevelItem(index)
            if root.data(0, Qt.ItemDataRole.UserRole + 2) != "必须修正":
                continue
            item = root
            while item.childCount():
                item = item.child(0)
            self._focus_validation_item(item)
            return
        self._scroll_to_widget(self.quality_card)

    def _acknowledge_out_of_scope_activities(self) -> None:
        self.other_activity_present.setChecked(False)
        self.transport_present.setChecked(False)
        self.scope_exclusion_notice.setVisible(False)
        self._mark_input_dirty()

    def _build_source_cards(self, parent_layout: QVBoxLayout) -> None:
        """Build eight visible source selectors over the ten legacy Domain states."""

        selector_scroll = QScrollArea(self)
        selector_scroll.setObjectName("accountingSourceToggleScroll")
        selector_scroll.setWidgetResizable(True)
        selector_scroll.setFrameShape(QFrame.Shape.NoFrame)
        selector_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        selector_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selector_host = QWidget(selector_scroll)
        selector_host.setObjectName("accountingSourceToggleRow")
        self.source_toggle_host = selector_host
        self.source_toggle_scroll = selector_scroll
        selector_layout = QHBoxLayout(selector_host)
        selector_layout.setContentsMargins(0, 2, 0, 2)
        selector_layout.setSpacing(8)
        for group_id, label, _source_ids in self._source_toggle_groups:
            button = QPushButton(selector_host)
            button.setObjectName(f"sourceToggle_{group_id}")
            button.setMinimumHeight(36)
            button.setAccessibleName(label)
            button.clicked.connect(lambda _checked=False, _group=group_id: self._toggle_source_group(_group))
            selector_layout.addWidget(button)
            self._source_toggle_buttons[group_id] = button
        selector_layout.addStretch(1)
        selector_scroll.setWidget(selector_host)
        parent_layout.addWidget(selector_scroll)

        source_definitions = (
            ("CAR-SRC-FUEL-001", lambda layout: self._build_fuel_section(layout)),
            (
                "CAR-SRC-CALCINATION-001",
                lambda layout: self._build_process_section(
                    layout,
                    "煅烧（P01）",
                    "calcination",
                    ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"),
                ),
            ),
            (
                "CAR-SRC-BAKING-001",
                lambda layout: self._build_process_section(
                    layout,
                    "焙烧/炭化（P02）",
                    "baking",
                    ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"),
                ),
            ),
            (
                "CAR-SRC-GRAPHITIZATION-001",
                lambda layout: self._build_process_section(
                    layout,
                    "石墨化（P03）",
                    "graphitization",
                    ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"),
                ),
            ),
            (
                "CAR-SRC-FUME-INCINERATION-001",
                lambda layout: self._build_process_section(
                    layout,
                    "烟气焚烧治理（P04A）",
                    "fume",
                    ("q", "qvar", "hm", "fch", "fox", "duration"),
                ),
            ),
            (
                "CAR-SRC-FGD-001",
                lambda layout: self._build_process_section(
                    layout,
                    "烟气脱硫净化（P04B）",
                    "fgd",
                    ("cal", "i", "ef1", "tr"),
                ),
            ),
            ("CAR-SRC-PURCHASED-ELECTRICITY-001", lambda layout: self._build_electricity_section(layout)),
            ("CAR-SRC-PURCHASED-HEAT-001", lambda layout: self._build_heat_section(layout)),
            ("CAR-SRC-EXPORTED-ELECTRICITY-001", lambda layout: self._build_output_electricity_section(layout)),
            ("CAR-SRC-EXPORTED-HEAT-001", lambda layout: self._build_output_heat_section(layout)),
        )
        for source_id, builder in source_definitions:
            card = SourceCard(source_id, SOURCE_LABELS[source_id], self)
            source_spec = get_field_spec(f"source_status.{source_id}")
            combo = create_typed_input(card, source_spec, f"sourceStatus_{source_id}")
            combo.addItem("未启用", EmissionSourceStatus.NOT_INVOLVED)
            combo.addItem("已启用", EmissionSourceStatus.INVOLVED)
            combo.addItem("待确认", EmissionSourceStatus.UNCONFIRMED)
            self._source_statuses[source_id] = combo
            self._source_cards[source_id] = card
            card.set_status_widget(
                combo,
                not_involved_value=EmissionSourceStatus.NOT_INVOLVED,
                involved_value=EmissionSourceStatus.INVOLVED,
            )
            builder(card.body_layout)
            combo.currentIndexChanged.connect(self._mark_input_dirty)
            card.status_changed.connect(lambda _status, _source_id=source_id: self._refresh_source_cards())
            header = card.findChild(QWidget, f"sourceCardHeader_{source_id}")
            if header is not None:
                header.hide()
            card.summary_label.hide()
            card.check_result_label.hide()
            parent_layout.addWidget(card)

        self._build_unified_energy_section(parent_layout)

        parameter_summary = QWidget(self)
        parameter_summary_layout = QVBoxLayout(parameter_summary)
        parameter_summary_layout.setContentsMargins(0, 8, 0, 0)
        parameter_summary_title = QLabel("本次计算参数状态（只读）", parameter_summary)
        parameter_summary_title.setObjectName("parameterSummaryTitle")
        parameter_summary_layout.addWidget(parameter_summary_title)
        self.parameter_snapshot_summary = QLabel("尚未计算，暂无参数快照。", parameter_summary)
        self.parameter_snapshot_summary.setObjectName("parameterSnapshotSummary")
        self.parameter_snapshot_summary.setWordWrap(True)
        parameter_summary_layout.addWidget(self.parameter_snapshot_summary)
        parent_layout.addWidget(parameter_summary)

        self._refresh_source_cards()

    def _build_unified_energy_section(self, parent_layout: QVBoxLayout) -> None:
        for family, title, hint, add_label in (
            ("electricity", "购入/输出电力", "逐条填写电量、方向和购入电力属性。停用排放源时保留输入，计算不计入。", "新增电力来源"),
            ("heat", "购入/输出热力", "逐条填写热力量、方向和蒸汽参数。停用排放源时保留输入，计算不计入。", "新增热力来源"),
        ):
            card = QFrame(self)
            card.setObjectName("unifiedElectricityCard" if family == "electricity" else "unifiedHeatCard")
            card.setProperty("energyFamily", family)
            card.setFrameShape(QFrame.Shape.StyledPanel)
            layout = QVBoxLayout(card)
            heading = QLabel(title, card)
            heading.setObjectName("unifiedElectricityTitle" if family == "electricity" else "unifiedHeatTitle")
            layout.addWidget(heading)
            help_text = QLabel(hint, card)
            help_text.setObjectName("unifiedEnergyHelp")
            help_text.setWordWrap(True)
            layout.addWidget(help_text)
            host = QWidget(card)
            rows_layout = QVBoxLayout(host)
            rows_layout.setContentsMargins(0, 0, 0, 0)
            rows_layout.setSpacing(2)
            layout.addWidget(host)
            add_row = QPushButton(add_label, card)
            add_row.setObjectName("addUnifiedElectricityRow" if family == "electricity" else "addUnifiedHeatRow")
            add_row.clicked.connect(lambda _checked=False, _family=family: self._add_unified_energy_row(
                kind="purchased_electricity" if _family == "electricity" else "purchased_heat"
            ))
            layout.addWidget(add_row, 0, Qt.AlignmentFlag.AlignLeft)
            parent_layout.addWidget(card)
            self._unified_energy_cards[family] = card
            self._unified_energy_rows_layouts[family] = rows_layout
            self._add_unified_energy_row(
                kind="purchased_electricity" if family == "electricity" else "purchased_heat"
            )

    def _add_unified_energy_row(
        self,
        *,
        kind: str = "purchased_electricity",
        line_id: str | None = None,
    ) -> _UnifiedEnergyRow:
        legacy_self_consumed = kind == "self_consumed_electricity"
        if legacy_self_consumed:
            kind = "purchased_electricity"
        if kind in {value for _, value in _UnifiedEnergyRow.HEAT_KINDS}:
            family = "heat"
        elif kind in {value for _, value in _UnifiedEnergyRow.ELECTRICITY_KINDS}:
            family = "electricity"
        else:
            kind = "purchased_electricity"
            family = "electricity"
        rows_layout = self._unified_energy_rows_layouts.get(family)
        if rows_layout is None:
            raise RuntimeError("unified energy sections are not initialized")
        self._energy_row_serial += 1
        row = _UnifiedEnergyRow(self._energy_row_serial, family, self._remove_unified_energy_row, self)
        row.kind.setCurrentIndex(max(0, row.kind.findData(kind)))
        if legacy_self_consumed:
            row.attribute.setCurrentIndex(max(0, row.attribute.findData("SELF_CONSUMED_EXCLUDED")))
        if line_id:
            row.line_id.setText(line_id)
        self._energy_rows.append(row)
        self._energy_family_rows[family].append(row)
        rows_layout.addWidget(row)
        for widget in (
            row.kind, row.amount, row.attribute, row.region, row.factor_mode, row.factor_selector,
            row.manual_factor, row.electricity_source, row.heat_kind, row.pressure, row.temperature,
            row.enthalpy_mode, row.enthalpy, row.heat_factor_mode, row.measured_heat_factor, row.heat_source,
        ):
            self._wire_dirty_tracking(widget)
        row.kind.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.kind.currentIndexChanged.connect(self._refresh_source_cards)
        row.region.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_energy_factor_options(_row))
        row.attribute.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.factor_mode.currentIndexChanged.connect(lambda *_args, _row=row: self._clear_legacy_measured_factor_on_edit(_row))
        row.factor_mode.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.manual_factor.textChanged.connect(lambda *_args, _row=row: self._clear_legacy_measured_factor_on_edit(_row))
        row.heat_kind.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.enthalpy_mode.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.heat_factor_mode.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        row.amount.textChanged.connect(lambda *_args: self._refresh_source_cards())
        row.amount.textChanged.connect(lambda *_args: self._refresh_electricity_rows())
        row.factor_selector.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_unified_energy_row(_row))
        self._refresh_energy_region_options(row)
        self._refresh_energy_factor_options(row)
        self._refresh_unified_energy_row(row)
        self._refresh_repeat_delete_controls()
        if hasattr(self, "result_card") and not self._restoring_workspace:
            self._mark_input_dirty()
        return row

    def _remove_unified_energy_row(self, row: QWidget, *, force: bool = False) -> None:
        if not isinstance(row, _UnifiedEnergyRow) or row not in self._energy_rows:
            return
        family_rows = self._energy_family_rows.get(row.family, [])
        if not force and (not family_rows or row is family_rows[0] or len(family_rows) <= 1):
            return
        self._energy_rows.remove(row)
        family_rows.remove(row)
        rows_layout = self._unified_energy_rows_layouts.get(row.family)
        if rows_layout is not None:
            rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._refresh_repeat_delete_controls()
        self._refresh_source_cards()
        if hasattr(self, "result_card") and not self._restoring_workspace:
            self._mark_input_dirty()

    def _refresh_energy_region_options(self, row: _UnifiedEnergyRow) -> None:
        combo = row.region
        old = combo.currentData()
        try:
            period = self._period()
            queries = self._uat03_parameter_queries
            regions = queries.electricity_regions(period) if queries is not None else ()
            preferred = queries.preferred_electricity_region(period) if queries is not None else None
        except (AttributeError, DomainValidationError, TypeError, ValueError):
            regions, preferred = (), None
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItem("全国平均", None)
        for region in regions:
            combo.addItem(f"{region}地区平均", region)
        wanted = old if old is not None else preferred
        index = combo.findData(wanted)
        combo.setCurrentIndex(index if index >= 0 else 0)
        del blocker

    def _refresh_energy_factor_options(self, row: _UnifiedEnergyRow) -> None:
        selector = row.factor_selector
        old = selector.currentData()
        old_id = getattr(getattr(old, "factor", None), "factor_id", None)
        try:
            period = self._period()
            queries = self._uat03_parameter_queries
            region = row.region.currentData()
            options = queries.electricity_options(region, period) if queries is not None else ()
        except (AttributeError, DomainValidationError, TypeError, ValueError):
            options = ()
        blocker = QSignalBlocker(selector)
        selector.clear()
        for option in options:
            factor = option.factor
            year = f" · {factor.factor_year}" if factor.factor_year is not None else ""
            selector.addItem(f"{option.label}：{factor.value} {factor.unit}{year}", option)
        if not options:
            selector.addItem("当前期间暂无适用目录候选", None)
        index = next(
            (i for i in range(selector.count()) if getattr(getattr(selector.itemData(i), "factor", None), "factor_id", None) == old_id),
            0,
        )
        selector.setCurrentIndex(index)
        selector.setEnabled(bool(options))
        del blocker
        self._refresh_unified_energy_row(row)

    @staticmethod
    def _clear_legacy_measured_factor_on_edit(row: _UnifiedEnergyRow) -> None:
        row.legacy_measured_factor = False

    def _clear_legacy_energy_attribute(self, row: _UnifiedEnergyRow) -> None:
        if row.legacy_attribute is None:
            return
        row.legacy_attribute = None
        self._refresh_unified_energy_row(row)

    def _refresh_unified_energy_row(self, row: _UnifiedEnergyRow) -> None:
        kind = row.kind.currentData()
        electricity = row.family == "electricity"
        heat = row.family == "heat"
        output = kind in {"exported_electricity", "exported_heat"}
        row.electricity_details.setVisible(electricity)
        row.heat_details.setVisible(heat)
        row.unit_label.setText("MWh" if electricity else "t")
        row.amount.setPlaceholderText("电量（MWh）" if electricity else "热力量（t）")
        row.amount.setProperty("fieldUnit", "MWh" if electricity else "t")
        row.attribute.setVisible(electricity and not output and row.legacy_attribute is None and row.legacy_acquisition_mode is None)
        row.legacy_attribute_notice.setVisible(electricity and not output and (row.legacy_attribute is not None or row.legacy_acquisition_mode is not None))
        attribute_data = row.attribute.currentData()
        self_consumed = attribute_data == "SELF_CONSUMED_EXCLUDED"
        try:
            attribute = _enum(attribute_data, ElectricityAttribute)
        except (TypeError, ValueError):
            attribute = ElectricityAttribute.ORDINARY
        row.region.setVisible(electricity and (output or (not self_consumed and attribute is ElectricityAttribute.ORDINARY)))
        manual = row.factor_mode.currentData() == "MANUAL"
        can_select_factor = electricity and (
            output or (not self_consumed and attribute is ElectricityAttribute.ORDINARY)
        )
        show_factor_controls = can_select_factor
        row.factor_mode.setVisible(show_factor_controls)
        row.factor_selector.setVisible(show_factor_controls and not manual)
        row.manual_factor.setVisible(show_factor_controls and manual)
        row.electricity_source.setVisible(show_factor_controls and manual)
        row.heat_kind.setVisible(heat)
        try:
            steam_kind = _enum(row.heat_kind.currentData(), SteamKind)
        except (TypeError, ValueError):
            steam_kind = SteamKind.SATURATED
        manual_enthalpy = row.enthalpy_mode.currentData() == "MANUAL"
        row.temperature.setVisible(heat and steam_kind is SteamKind.SUPERHEATED and not manual_enthalpy)
        row.enthalpy_mode.setVisible(heat)
        row.enthalpy.setVisible(heat and manual_enthalpy)
        row.pressure.setVisible(heat and not manual_enthalpy)
        row.heat_factor_mode.setVisible(heat)
        try:
            measured_heat = _enum(row.heat_factor_mode.currentData(), HeatFactorMode) is HeatFactorMode.MEASURED
        except (TypeError, ValueError):
            measured_heat = False
        row.measured_heat_factor.setVisible(heat and measured_heat)
        row.heat_source.setVisible(heat and measured_heat)
        if self_consumed:
            row.status.setText("自发自用电量保留在项目中，不计入本次正式核算输入。")
        elif electricity:
            row.status.setText("电力因子：待录入")
        self._refresh_unified_energy_row_preview(row)

    def _refresh_unified_energy_row_preview(self, row: _UnifiedEnergyRow) -> None:
        if row.family != "heat":
            return
        try:
            heat_kind = _enum(row.heat_kind.currentData(), SteamKind)
            if row.enthalpy_mode.currentData() == "MANUAL":
                enthalpy_text = row.enthalpy.text().strip()
                status = "热力来源：手动焓值待填写" if not enthalpy_text else "热力来源：使用手动焓值"
            else:
                pressure_text = row.pressure.text().strip()
                temperature_text = row.temperature.text().strip()
                if not pressure_text or (heat_kind is SteamKind.SUPERHEATED and not temperature_text):
                    missing = "蒸汽压力（绝压）" if not pressure_text else "过热蒸汽温度"
                    status = f"热力来源：请填写{missing}"
                else:
                    pressure = self.calculator.policy.parse(pressure_text)
                    if heat_kind is SteamKind.SUPERHEATED:
                        reference = superheated_steam_enthalpy(pressure, self.calculator.policy.parse(temperature_text), policy=self.calculator.policy)[0]
                    else:
                        reference = saturated_steam_enthalpy(pressure, policy=self.calculator.policy)[0]
                    status = f"热力来源：自动取焓 {self.calculator.policy.format_for_display(reference, 1)} kJ/kg"
        except (ValueError, InvalidOperation, DomainValidationError):
            status = "热力来源：压力或温度格式无效或超出标准表范围"
        row.status.setText(status)

    def _energy_source_is_enabled(self, source_id: str) -> bool:
        return source_id in self._source_statuses and _enum(
            self._source_statuses[source_id].currentData(), EmissionSourceStatus
        ) is EmissionSourceStatus.INVOLVED

    def _energy_electricity_parameter_unit(self, region: str | None) -> tuple[str, str]:
        parameter_id = PROVINCIAL_ELECTRICITY_PARAMETER_ID if region else NATIONAL_ELECTRICITY_PARAMETER_ID
        for parameter in self.catalog_service.repository.list_parameters():
            if parameter.parameter_id == parameter_id:
                return parameter_id, str(getattr(parameter, "canonical_unit", getattr(parameter, "default_unit", "tCO2/MWh")))
        return parameter_id, "tCO2/MWh"

    def _toggle_source_group(self, group_id: str) -> None:
        group = next((item for item in self._source_toggle_groups if item[0] == group_id), None)
        if group is None:
            return
        source_ids = group[2]
        current = [
            _enum(self._source_statuses[source_id].currentData(), EmissionSourceStatus) is EmissionSourceStatus.INVOLVED
            for source_id in source_ids if source_id in self._source_statuses
        ]
        # A partially restored legacy group is made consistently enabled by a
        # deliberate click; a fully enabled group is deliberately disabled.
        target_enabled = not bool(current) or not all(current)
        target = EmissionSourceStatus.INVOLVED if target_enabled else EmissionSourceStatus.NOT_INVOLVED
        for source_id in source_ids:
            combo = self._source_statuses.get(source_id)
            if combo is not None:
                index = combo.findData(target)
                if index >= 0:
                    combo.setCurrentIndex(index)
        self._mark_input_dirty()
        self._refresh_source_cards()

    def _refresh_source_toggle_buttons(self) -> None:
        total_width = 0
        for group_id, label, source_ids in self._source_toggle_groups:
            button = self._source_toggle_buttons.get(group_id)
            if button is None:
                continue
            states = [
                _enum(self._source_statuses[source_id].currentData(), EmissionSourceStatus) is EmissionSourceStatus.INVOLVED
                for source_id in source_ids if source_id in self._source_statuses
            ]
            enabled_count = sum(states)
            if enabled_count == len(states) and states:
                state = "已启用"
            elif enabled_count:
                state = "部分启用"
            else:
                state = "未启用"
            button.setText(f"{state} | {label}")
            button.setMinimumWidth(max(118, button.fontMetrics().horizontalAdvance(button.text()) + 30))
            total_width += button.minimumWidth()
            button.setProperty("sourceState", state)
            button.setAccessibleDescription(f"{label}排放源，当前{state}；点击切换。")
            button.setToolTip(f"{label}：{state}。点击切换。")
            button.style().unpolish(button)
            button.style().polish(button)
        host = getattr(self, "source_toggle_host", None)
        if isinstance(host, QWidget):
            layout = host.layout()
            spacing = layout.spacing() if layout is not None else 0
            margins = layout.contentsMargins() if layout is not None else None
            horizontal_margins = margins.left() + margins.right() if margins is not None else 0
            button_count = len(self._source_toggle_groups)
            host.setMinimumWidth(total_width + max(0, button_count - 1) * max(0, spacing) + horizontal_margins)

    def _build_fuel_section(self, parent_layout: QVBoxLayout) -> None:
        self.fuel_rows_host = QWidget(self)
        self.fuel_rows_layout = QVBoxLayout(self.fuel_rows_host)
        self.fuel_rows_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.addWidget(self.fuel_rows_host)
        self.add_fuel_button = QPushButton("添加燃料", self)
        self.add_fuel_button.setObjectName("addFuelButton")
        self.add_fuel_button.clicked.connect(self._add_fuel_row)
        parent_layout.addWidget(self.add_fuel_button)
        self._add_fuel_row()

    def _bind_fuel_aliases(self, row: _FuelRow | None) -> None:
        if row is None:
            return
        self._fields.update({
            "fuel_id": row.internal_id,
            "fuel_path": row.path,  # type: ignore[dict-item]
            "fuel_activity": row.activity,
            "fuel_carbon": row.carbon,
            "fuel_oxidation": row.oxidation,
        })

    def _fuel_catalog_options(self) -> tuple[object, ...]:
        queries = self._uat03_parameter_queries
        if queries is None:
            return ()
        try:
            return tuple(queries.fuel_options())
        except (AttributeError, KeyError, TypeError, ValueError):
            _LOGGER.warning("Unable to list C.1 fuel choices", exc_info=True)
            return ()

    def _bind_fuel_aliases(self, row: _FuelRow | None) -> None:
        if row is None:
            return
        direct = row.carbon_basis.currentData() == "DIRECT"
        self._fields.update({
            "fuel_id": row.internal_id,
            "fuel_path": row.path,  # type: ignore[dict-item]
            "fuel_activity": row.activity,
            "fuel_carbon": row.carbon_direct if direct else row.carbon,
            "fuel_oxidation": row.oxidation,
        })

    def _add_fuel_row(self) -> None:
        self._fuel_row_serial += 1
        row = _FuelRow(
            self._fuel_row_serial,
            self._remove_fuel_row,
            self,
            fuel_options=self._fuel_catalog_options(),
        )
        self._fuel_rows.append(row)
        self.fuel_rows_layout.addWidget(row)
        row.remove_button.setVisible(len(self._fuel_rows) > 1)
        self._bind_fuel_aliases(self._fuel_rows[0])
        row.fuel_type.currentIndexChanged.connect(lambda _index, _row=row: self._on_fuel_type_changed(_row, initialize_defaults=True))
        row.fuel_type.editTextChanged.connect(lambda _text, _row=row: self._on_fuel_type_changed(_row, initialize_defaults=True))
        row.path.currentIndexChanged.connect(lambda _index, _row=row: self._refresh_fuel_row(_row, initialize_defaults=True))
        row.carbon_basis.currentIndexChanged.connect(lambda _index, _row=row: self._on_fuel_basis_changed(_row))
        for source_key, combo in (
            ("lhv", row.lhv_source),
            ("carbon", row.carbon_source),
            ("direct_carbon", row.direct_carbon_source),
            ("oxidation", row.oxidation_source),
        ):
            combo.currentIndexChanged.connect(
                lambda _index, _row=row, _key=source_key: self._on_fuel_source_mode_changed(_row, _key)
            )
            combo.currentIndexChanged.connect(self._mark_input_dirty)
        row.source_reference.textChanged.connect(self._mark_input_dirty)
        row.source_reference.textChanged.connect(lambda *_args: self._refresh_source_cards())
        for widget in (row.activity, row.carbon, row.carbon_direct, row.oxidation, row.lower_heating_value):
            if isinstance(widget, QLineEdit):
                if isinstance(widget, NumericLineEdit):
                    widget.defer_range_validation_to_domain()
                widget.textChanged.connect(self._mark_input_dirty)
                widget.textChanged.connect(lambda *_args: self._refresh_source_cards())
        row.fuel_type.currentIndexChanged.connect(self._mark_input_dirty)
        row.fuel_type.editTextChanged.connect(self._mark_input_dirty)
        row.path.currentIndexChanged.connect(self._mark_input_dirty)
        row.carbon_basis.currentIndexChanged.connect(self._mark_input_dirty)
        row.path.currentIndexChanged.connect(lambda *_args: self._refresh_source_cards())
        if hasattr(self, "result_card") and not self._restoring_workspace:
            self._mark_input_dirty()
        self._refresh_repeat_delete_controls()
        self._refresh_fuel_row(row, initialize_defaults=True)

    def _fuel_option_for_row(self, row: _FuelRow):
        text = row.fuel_type.currentText().strip()
        if not text:
            return None
        for option in row._fuel_options:
            if text == str(getattr(option, "label", "")) or text in tuple(getattr(option, "aliases", ()) or ()):
                return option
        return None

    @staticmethod
    def _fuel_source_mode(row: _FuelRow, source_key: str) -> str | None:
        return row._legacy_source_modes.get(source_key) or {
            "lhv": row.lhv_source,
            "carbon": row.carbon_source,
            "direct_carbon": row.direct_carbon_source,
            "oxidation": row.oxidation_source,
        }[source_key].currentData()

    @staticmethod
    def _restore_fuel_source_mode(row: _FuelRow, source_key: str, mode: str | None) -> None:
        combo = {
            "lhv": row.lhv_source,
            "carbon": row.carbon_source,
            "direct_carbon": row.direct_carbon_source,
            "oxidation": row.oxidation_source,
        }[source_key]
        index = combo.findData(mode)
        if index >= 0:
            combo.setCurrentIndex(index)
            row._legacy_source_modes.pop(source_key, None)
        elif mode:
            row._legacy_source_modes[source_key] = mode

    def _on_fuel_source_mode_changed(self, row: _FuelRow, source_key: str) -> None:
        if self._restoring_workspace:
            return
        row._legacy_source_modes.pop(source_key, None)
        self._refresh_fuel_row(row)

    def _on_fuel_basis_changed(self, row: _FuelRow) -> None:
        self._bind_fuel_aliases(self._fuel_rows[0] if self._fuel_rows else None)
        # Switching carbon basis only changes the active input path. Catalog
        # values and the hidden calculated-path inputs remain intact for return.
        self._refresh_fuel_row(row)
        self._mark_input_dirty()

    def _recommended_fuel_activity_path(self, row: _FuelRow) -> FuelPath | None:
        option = self._fuel_option_for_row(row)
        if option is None:
            return None
        queries = self._uat03_parameter_queries
        if queries is not None:
            try:
                defaults = queries.fuel_defaults(option.subject_id, self._period())
                factor = defaults.lower_heating_value.factor if defaults.lower_heating_value is not None else None
            except (AttributeError, DomainValidationError, KeyError, TypeError, ValueError):
                factor = None
            if factor is None:
                return None
            unit = _domain_unit(str(factor.unit)).casefold()
            if unit == _domain_unit("GJ/t").casefold():
                return FuelPath.MASS
            if unit in {_domain_unit("GJ/10⁴Nm³").casefold(), _domain_unit("GJ/10⁴ Nm³").casefold()}:
                return FuelPath.VOLUME
            return None
        # Compatibility fallback for standalone pages without a Catalog/Resolver.
        fuel_type = getattr(option, "fuel_type", None)
        return _FUEL_C1_ACTIVITY_PATH.get(fuel_type) if isinstance(fuel_type, FuelType) else None

    def _on_fuel_type_changed(self, row: _FuelRow, *, initialize_defaults: bool = False) -> None:
        if not self._restoring_workspace and not row.activity.text().strip():
            standard_path = self._recommended_fuel_activity_path(row)
            if standard_path is not None:
                path_index = row.path.findData(standard_path)
                if path_index >= 0 and row.path.currentIndex() != path_index:
                    row.path.setCurrentIndex(path_index)
        row._update_custom_name_visibility()
        self._refresh_fuel_row(row, initialize_defaults=initialize_defaults)

    def _remove_fuel_row(self, row: QWidget) -> None:
        if row not in self._fuel_rows or not self._fuel_rows or row is self._fuel_rows[0]:
            return
        if len(self._fuel_rows) == 1:
            return
        else:
            self._fuel_rows.remove(row)  # type: ignore[arg-type]
            self.fuel_rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
            self._bind_fuel_aliases(self._fuel_rows[0])
            self._fuel_rows[0].remove_button.hide()
            self._mark_input_dirty()
        self._refresh_source_cards()

    def _canonical_default_factor(self, parameter_id: str, *, value_type: ValueType = ValueType.STANDARD_DEFAULT) -> object | None:
        parameter_id = parameter_id.lower()
        try:
            factors = tuple(self.catalog_service.repository.list_factors())
            period = self._period()
        except (AttributeError, TypeError, ValueError, DomainValidationError):
            return None
        candidates = [
            factor for factor in factors
            if factor.parameter_id == parameter_id
            and STANDARD_ID in factor.applicable_standard_ids
            and factor.review_status is ReviewStatus.VERIFIED
            and factor.value_type is value_type
            and not (
                (factor.valid_from is not None and factor.valid_from > period.end)
                or (factor.valid_to is not None and factor.valid_to < period.start)
                or (
                    period.period_type is PeriodType.CUSTOM
                    and ((factor.valid_from is not None and period.start < factor.valid_from)
                         or (factor.valid_to is not None and period.end > factor.valid_to))
                )
            )
        ]
        return sorted(candidates, key=lambda factor: factor.factor_id)[0] if candidates else None

    @staticmethod
    def _parameter_value_from_factor(factor: object, reason: str) -> ParameterValue:
        return ParameterValue(
            factor.parameter_id,
            factor.value,
            factor.unit,
            _parameter_source_kind(factor.value_type),
            factor.source_id,
            str(factor.factor_year),
            factor.source_location,
            reason,
            factor.factor_id,
            factor.factor_year,
        )

    def _fuel_default_factors(self, row: _FuelRow) -> tuple[object | None, object | None, object | None] | None:
        option = self._fuel_option_for_row(row)
        queries = self._uat03_parameter_queries
        if option is None or queries is None:
            row._default_selection_reasons = {}
            return None
        try:
            defaults = queries.fuel_defaults(option.subject_id, self._period())
        except (AttributeError, DomainValidationError, KeyError, TypeError, ValueError):
            row._default_selection_reasons = {}
            return None
        resolved = {
            "lhv": defaults.lower_heating_value,
            "carbon": defaults.carbon_content_per_heat,
            "oxidation": defaults.oxidation_rate,
        }
        row._default_selection_reasons = {
            key: item.selection_reason for key, item in resolved.items() if item is not None
        }
        factors = {key: item.factor if item is not None else None for key, item in resolved.items()}
        try:
            path = _enum(row.path.currentData(), FuelPath)
        except (TypeError, ValueError):
            return None
        lhv = factors["lhv"]
        if lhv is not None:
            expected_unit = {
                FuelPath.VOLUME: "GJ/10⁴Nm³",
                FuelPath.MASS: "GJ/t",
                FuelPath.HEAT: "GJ/GJ",
            }[path]
            if _domain_unit(str(lhv.unit)) != _domain_unit(expected_unit):
                factors["lhv"] = None
        if not any(factors.values()):
            return None
        return factors["lhv"], factors["carbon"], factors["oxidation"]

    def _refresh_energy_parameters(self) -> None:
        for row in tuple(self._energy_family_rows.get("electricity", ())):
            self._refresh_energy_region_options(row)
            self._refresh_energy_factor_options(row)
        self._refresh_carbonate_options()

    def _refresh_fuel_defaults(self) -> None:
        try:
            period = self._period()
        except (DomainValidationError, TypeError, ValueError):
            return
        if period.start > period.end:
            return
        for row in getattr(self, "_fuel_rows", ()):
            self._refresh_fuel_row(row)

    @staticmethod
    def _set_fuel_default_option(combo: QComboBox, available: bool) -> None:
        index = combo.findData("STANDARD_DEFAULT")
        model = combo.model()
        item = model.item(index) if index >= 0 and hasattr(model, "item") else None
        if item is not None:
            item.setEnabled(available)

    def _refresh_fuel_row(self, row: _FuelRow, *, initialize_defaults: bool = False) -> None:
        try:
            path = _enum(row.path.currentData(), FuelPath)
        except (TypeError, ValueError):
            path = FuelPath.MASS
        direct = row.carbon_basis.currentData() == "DIRECT"
        factors = self._fuel_default_factors(row)
        lhv_factor, carbon_factor, oxidation_factor = factors if factors is not None else (None, None, None)
        default_values = {
            "lhv": "" if lhv_factor is None else str(lhv_factor.value),
            "carbon": "" if carbon_factor is None else str(carbon_factor.value),
            "oxidation": "" if oxidation_factor is None else str(oxidation_factor.value * Decimal("100")),
        }
        modes = {
            "lhv": self._fuel_source_mode(row, "lhv"),
            "carbon": self._fuel_source_mode(row, "carbon"),
            "oxidation": self._fuel_source_mode(row, "oxidation"),
            "direct_carbon": self._fuel_source_mode(row, "direct_carbon"),
        }
        previous = row._last_default_values or ("", "", "")
        current = {
            "lhv": row.lower_heating_value.text().strip(),
            "carbon": row.carbon.text().strip(),
            "oxidation": row.oxidation.text().strip(),
        }
        factors_by_key = {"lhv": lhv_factor, "carbon": carbon_factor, "oxidation": oxidation_factor}
        edits = {"lhv": row.lower_heating_value, "carbon": row.carbon, "oxidation": row.oxidation}
        combos = {"lhv": row.lhv_source, "carbon": row.carbon_source, "oxidation": row.oxidation_source}

        for key in ("lhv", "carbon", "oxidation"):
            factor = factors_by_key[key]
            source_combo = combos[key]
            edit = edits[key]
            has_legacy_mode = key in row._legacy_source_modes
            mode = modes[key]
            self._set_fuel_default_option(source_combo, factor is not None)
            if (
                initialize_defaults and factor is not None and not has_legacy_mode
                and mode in {None, "STANDARD_DEFAULT"}
                and (not current[key] or current[key] == previous[("lhv", "carbon", "oxidation").index(key)])
            ):
                mode = "STANDARD_DEFAULT"
                self._restore_fuel_source_mode(row, key, mode)
                modes[key] = mode
            if mode == "STANDARD_DEFAULT" and factor is not None:
                if edit.text().strip() != default_values[key]:
                    edit.setText(default_values[key])
                edit.setReadOnly(True)
            elif mode == "STANDARD_DEFAULT" and factor is None:
                # A newly selected unmatched/custom fuel must not keep stale
                # catalog defaults. Legacy source selections, however, retain
                # the saved values and provenance verbatim for old projects.
                if not has_legacy_mode:
                    previous_value = previous[("lhv", "carbon", "oxidation").index(key)]
                    if previous_value and edit.text().strip() == previous_value:
                        edit.clear()
                    fallback = "MEASURED" if key == "lhv" else "USER_DEFINED" if key == "oxidation" else None
                    if fallback is not None and row.fuel_type.currentText().strip():
                        index = source_combo.findData(fallback)
                        if index >= 0:
                            source_combo.setCurrentIndex(index)
                            modes[key] = fallback
                edit.setReadOnly(key == "carbon")
            else:
                edit.setReadOnly(key == "carbon")

        direct_mode = modes["direct_carbon"]
        if direct_mode is None:
            direct_mode = "MEASURED"
        row.direct_carbon_source.hide()
        row.oxidation_source.hide()
        row.source_reference.hide()
        row.source_reference_label.hide()
        row.parameter_summary.hide()
        row.carbon_basis_label.hide()

        activity_unit = {FuelPath.VOLUME: "10⁴ Nm³", FuelPath.MASS: "t", FuelPath.HEAT: "GJ"}[path]
        lhv_unit = {FuelPath.VOLUME: "GJ/10⁴ Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}[path]
        direct_carbon_unit = {FuelPath.VOLUME: "tC/10⁴Nm³", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ"}[path]
        row.carbon_basis.setEnabled(path in {FuelPath.VOLUME, FuelPath.MASS})
        row.lhv_control.setVisible(path is not FuelPath.HEAT)
        row.lhv_control.setEnabled(not direct and path is not FuelPath.HEAT)
        row.lhv_source.setVisible(not direct and path is not FuelPath.HEAT)
        row.carbon_control.setEnabled(not direct)
        row.carbon_source.setVisible(carbon_factor is not None and not direct)
        row.carbon_calc_cell.setVisible(not direct)
        row.carbon_direct_cell.setVisible(direct)
        row.lower_heating_value.setEnabled(not direct and path is not FuelPath.HEAT)
        row.activity_label.setText(f"活动量（{activity_unit}）")
        row.activity.setProperty("fieldUnit", activity_unit)
        row.lhv_label.setText(f"低位发热量（{lhv_unit}）")
        row.carbon_label.setText("单位热值含碳量（tC/GJ）")
        row.direct_carbon_label.setText(f"单位活动量含碳量（{direct_carbon_unit}）")
        row.carbon_label.setVisible(True)
        row.direct_carbon_label.setVisible(True)
        row.carbon_direct.setProperty("fieldUnit", direct_carbon_unit)

        expected_path = self._recommended_fuel_activity_path(row)
        unit_mismatch = bool(
            not direct and expected_path is not None and path in {FuelPath.VOLUME, FuelPath.MASS}
            and path is not expected_path
        )
        mismatch_message = "当前计量单位与该燃料的 C.1 缺省口径不同，请核实单位或选择直接实测。"
        row.activity.setToolTip(mismatch_message if unit_mismatch else "")
        if not direct:
            try:
                lhv_text = row.lower_heating_value.text().strip()
                carbon_text = row.carbon.text().strip()
                if lhv_text and carbon_text:
                    policy = self.calculator.policy
                    derived = policy.multiply(policy.parse(lhv_text), policy.parse(carbon_text))
                    result_text = f"{policy.format_for_display(derived, 2)} {direct_carbon_unit}"
                else:
                    result_text = "计算值待录入"
            except (DomainValidationError, InvalidOperation, ValueError):
                result_text = "请检查数值"
            row.calculated_carbon_label.setText(
                f"{result_text} · 计量口径请核实" if unit_mismatch else result_text
            )
            row.calculated_carbon_label.setToolTip(mismatch_message if unit_mismatch else "")
        else:
            row.calculated_carbon_label.setText("")
            row.calculated_carbon_label.setToolTip("")

        effective_modes = (
            modes["lhv"] if not direct and path is not FuelPath.HEAT else None,
            modes["carbon"] if not direct else direct_mode,
            modes["oxidation"],
        )
        if direct:
            row.parameter_summary.setText("直接实测单位活动量含碳量；氧化率采用可用缺省值或按需填写。")
        elif factors is None:
            row.parameter_summary.setText("当前燃料/周期无已解析的 C.1 缺省项；请补充可追溯的实测数据。")
        elif all(mode == "STANDARD_DEFAULT" for mode in effective_modes):
            row.parameter_summary.setText("C.1 缺省参数已按核算期从参数库解析。")
        else:
            row.parameter_summary.setText("单位热值含碳量来自参数库；热值和氧化率按所选来源记录。")
        row.parameter_source = "STANDARD_DEFAULT" if all(mode in {"STANDARD_DEFAULT", None} for mode in effective_modes) and "STANDARD_DEFAULT" in effective_modes else (
            "MEASURED" if "MEASURED" in effective_modes else "USER_DEFINED" if "USER_DEFINED" in effective_modes else "AUTO"
        )
        row._last_default_values = (
            default_values["lhv"], default_values["carbon"], default_values["oxidation"],
        )
        self._bind_fuel_aliases(self._fuel_rows[0] if self._fuel_rows else None)
        self._refresh_source_cards()

    def _build_process_section(self, parent_layout: QVBoxLayout, title: str, prefix: str, fields: tuple[str, ...]) -> None:
        self._process_sections[prefix] = (title, fields)
        host = QWidget(self)
        host.setObjectName(f"{prefix}_instances")
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        self._process_rows_layout[prefix] = host_layout
        parent_layout.addWidget(host)
        buttons = QHBoxLayout()
        add_button = QPushButton(f"新增{title.split('（')[0]}", host)
        add_button.setObjectName(f"add_{prefix}_instance")
        add_button.clicked.connect(lambda _checked=False, _prefix=prefix: self._add_process_row(_prefix))
        add_button.setVisible(self.manage_process_button.isChecked())
        self._advanced_process_buttons.append(add_button)
        buttons.addWidget(add_button)
        buttons.addStretch(1)
        parent_layout.addLayout(buttons)
        self._add_process_row(prefix)

    def _build_business_field(self, parent: QWidget, prefix: str, field: str, instance_id: str, *, first: bool) -> QWidget:
        spec = get_field_spec(f"{prefix}.{field}")
        name = f"{prefix}_{field}" if first else f"{prefix}_{instance_id}_{field}"
        widget = create_typed_input(parent, spec, name)
        self._wire_dirty_tracking(widget)
        return widget

    def _add_process_row(
        self,
        prefix: str,
        *,
        instance_id: str | None = None,
        component_ids: tuple[str, ...] | None = None,
        material_ids: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        if prefix not in self._process_rows_layout:
            return {}
        rows = self._process_rows[prefix]
        if instance_id is None:
            serial = self._process_row_serials[prefix]
            existing_ids = {str(row.get("instance_id", "")) for row in rows}
            while True:
                serial += 1
                instance_id = f"{prefix}-{serial}"
                if instance_id not in existing_ids:
                    break
            self._process_row_serials[prefix] = serial
        else:
            restored_serial = instance_id.rsplit("-", 1)
            if len(restored_serial) == 2 and restored_serial[0] == prefix and restored_serial[1].isdigit():
                self._process_row_serials[prefix] = max(self._process_row_serials[prefix], int(restored_serial[1]))
        first = not rows
        fields = self._process_sections[prefix][1]
        host = QWidget(self)
        host.setObjectName(f"{prefix}Instance{instance_id}")
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 8, 0, 8)
        title, _ = self._process_sections[prefix]
        display_title = title.split("（")[0]
        toolbar = QHBoxLayout()
        title_label = QLabel(f"{display_title} {len(rows) + 1}", host)
        toolbar.addWidget(title_label)
        toolbar.addStretch(1)
        remove_button = QPushButton("删除本条", host)
        remove_button.setObjectName(f"remove_{prefix}_{instance_id}")
        remove_button.clicked.connect(lambda _checked=False, _prefix=prefix, _id=instance_id: self._remove_process_row(_prefix, _id))
        toolbar.addWidget(remove_button)
        host_layout.addLayout(toolbar)
        row: dict[str, object] = {
            "prefix": prefix,
            "instance_id": instance_id,
            "widget": host,
            "title": title_label,
            "display_title": display_title,
            "remove_button": remove_button,
            "fields": {},
            "components": [],
            "materials": [],
        }
        if prefix == "fgd":
            component_host = QWidget(host)
            component_layout = QVBoxLayout(component_host)
            component_layout.setContentsMargins(0, 0, 0, 0)
            host_layout.addWidget(component_host)
            row["component_host"] = component_host
            row["component_layout"] = component_layout
            add_component = QPushButton("新增碳酸盐组分", host)
            add_component.setObjectName(f"add_fgd_component_{instance_id}")
            add_component.clicked.connect(lambda _checked=False, _row=row: self._add_fgd_component(_row))
            host_layout.addWidget(add_component)
            for component_id in component_ids or ():
                self._add_fgd_component(row, component_id=component_id)
            if component_ids is None:
                self._add_fgd_component(row)
        else:
            field_groups = {
                "calcination": (("投入数据", ("gc", "wfc", "wvar")), ("产出数据", ("cc", "ucc", "du", "wfc_c", "wvar_c"))),
                "baking": (("投入数据", ("bpm", "bpmfc", "bg", "bgfc", "bpmvar", "bgvar")), ("产出数据", ("bwt", "bp", "bpfc"))),
                "graphitization": (("投入数据", ("gpm", "gpmfc", "gta", "gtafc", "gpmvar")), ("产出数据", ("gwt", "gp", "gpfc"))),
            }.get(prefix, (("活动数据", fields),))
            widgets: dict[str, QWidget] = {}
            if prefix == "fume":
                responsive_fields = ResponsiveFieldGrid(host)
                responsive_fields.setObjectName(f"{prefix}_{instance_id}_responsiveFields")
                for field in fields:
                    spec = get_field_spec(f"{prefix}.{field}")
                    edit = self._build_business_field(responsive_fields, prefix, field, instance_id, first=first)
                    widgets[field] = edit
                    responsive_fields.add_field(spec.label, edit)
                host_layout.addWidget(responsive_fields)
                row["responsive_fields"] = responsive_fields
            else:
                for group_name, group_fields in field_groups:
                    group = QWidget(host)
                    group_layout = QVBoxLayout(group)
                    group_layout.setContentsMargins(0, 0, 0, 0)
                    group_layout.addWidget(QLabel(group_name, group))
                    form_row = QWidget(group)
                    form = QFormLayout(form_row)
                    for field in group_fields:
                        spec = get_field_spec(f"{prefix}.{field}")
                        edit = self._build_business_field(form_row, prefix, field, instance_id, first=first)
                        widgets[field] = edit
                        form.addRow(spec.label, edit)
                    group_layout.addWidget(form_row)
                    host_layout.addWidget(group)
                    if prefix in _PROCESS_MATERIAL_ROLES:
                        # Kept hidden under their historical object names so old
                        # Workspace form_state_json values remain readable.
                        group.hide()
            row["fields"] = widgets
            if prefix in _PROCESS_DEFAULT_PARAMETERS:
                controls_key = f"{prefix}@{instance_id}"
                self._build_material_controls(host_layout, prefix, instance_id=instance_id, controls_key=controls_key, first=first)
                row["controls_key"] = controls_key
            if prefix in _PROCESS_MATERIAL_ROLES:
                material_host = QWidget(host)
                material_layout = QVBoxLayout(material_host)
                material_layout.setContentsMargins(0, 0, 0, 0)
                material_header = QHBoxLayout()
                for label, stretch in (
                    ("物料类别", 2), ("物料名称", 2), ("数量（t）", 1),
                    ("固定碳含量（%）", 1), ("挥发分（%）", 1), ("", 0),
                ):
                    caption = QLabel(label, material_host)
                    caption.setWordWrap(True)
                    caption.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    material_header.addWidget(caption, stretch if stretch else 0)
                material_layout.addLayout(material_header)
                material_rows_host = QWidget(material_host)
                material_rows_layout = QVBoxLayout(material_rows_host)
                material_rows_layout.setContentsMargins(0, 0, 0, 0)
                material_layout.addWidget(material_rows_host)
                summary = QLabel("软件汇总值：等待录入物料。", material_host)
                summary.setObjectName(f"{prefix}_{instance_id}_materialSummary")
                summary.setWordWrap(True)
                material_layout.addWidget(summary)
                add_material = QPushButton("新增物料", material_host)
                add_material.setObjectName(f"add_{prefix}_material_{instance_id}")
                add_material.clicked.connect(lambda _checked=False, _row=row: self._add_material_line(_row))
                material_layout.addWidget(add_material)
                host_layout.addWidget(material_host)
                row["materials_host"] = material_host
                row["materials_layout"] = material_rows_layout
                row["material_summary"] = summary
                for material_id in material_ids or ():
                    self._add_material_line(row, line_id=material_id)
                if not row["materials"]:
                    self._add_material_line(row)
            flags: dict[str, QCheckBox] = {}
            if prefix in {"calcination", "baking"}:
                checkbox = QCheckBox("高级检查：产品中的碳已在本过程重复计入", host)
                checkbox.setObjectName(f"{prefix}_carbonOutputIncludedInInput" if first else f"{prefix}_{instance_id}_carbonOutputIncludedInInput")
                advanced_check = QWidget(host)
                advanced_layout = QVBoxLayout(advanced_check)
                advanced_layout.setContentsMargins(0, 0, 0, 0)
                explanation = QLabel("防重复计碳：同一份产品碳不能在不同过程重复扣减。仅发现重复计入时才勾选；勾选后会阻断计算。", advanced_check)
                explanation.setWordWrap(True)
                advanced_layout.addWidget(explanation)
                advanced_layout.addWidget(checkbox)
                advanced_check.hide()
                advanced_button = QPushButton("防重复计碳检查", host)
                advanced_button.setCheckable(True)
                advanced_button.toggled.connect(advanced_check.setVisible)
                host_layout.addWidget(advanced_button)
                host_layout.addWidget(advanced_check)
                flags["carbon_output_included_in_input"] = checkbox
                self._wire_dirty_tracking(checkbox)
            elif prefix == "graphitization":
                checkbox = QCheckBox("炉体炭质材料氧化烧损已计入本过程（标准禁止）", host)
                checkbox.setObjectName(f"{prefix}_furnaceLossIncluded" if first else f"{prefix}_{instance_id}_furnaceLossIncluded")
                host_layout.addWidget(checkbox)
                flags["furnace_loss_included"] = checkbox
                self._wire_dirty_tracking(checkbox)
            row["flags"] = flags
        self._process_rows_layout[prefix].addWidget(host)
        rows.append(row)
        remove_button.setVisible(len(rows) > 1)
        self._bind_process_aliases(prefix)
        self._refresh_repeat_delete_controls()
        self._refresh_source_cards()
        return row

    def _add_material_line(self, process_row: dict[str, object], *, line_id: str | None = None) -> dict[str, object]:
        prefix = str(process_row.get("prefix", ""))
        if not prefix:
            return {}
        material_rows = process_row.get("materials")
        layout = process_row.get("materials_layout")
        parent = process_row.get("materials_host")
        if not isinstance(material_rows, list) or not isinstance(layout, QVBoxLayout) or not isinstance(parent, QWidget):
            return {}
        used_ids = {str(item.get("line_id", "")) for item in material_rows if isinstance(item, dict)}
        line_id = line_id or uuid4().hex
        while line_id in used_ids:
            line_id = uuid4().hex

        container = QWidget(parent)
        container.setObjectName(f"{prefix}_material_{line_id}")
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(6)
        role = QComboBox(container)
        role.setObjectName(f"{prefix}_materialRole_{line_id}")
        for label, value in _PROCESS_MATERIAL_ROLES[prefix]:
            role.addItem(label, value)
        default_role = _PROCESS_MATERIAL_DEFAULT_ROLE[prefix]
        role.setCurrentIndex(max(0, role.findData(default_role)))
        name = QLineEdit(container)
        name.setObjectName(f"{prefix}_materialName_{line_id}")
        name.setPlaceholderText("如：煅烧石油焦")
        mass = QLineEdit(container)
        mass.setObjectName(f"{prefix}_materialMass_{line_id}")
        mass.setPlaceholderText("数量")
        carbon = QLineEdit(container)
        carbon.setObjectName(f"{prefix}_materialFixedCarbon_{line_id}")
        carbon.setPlaceholderText("固定碳")
        carbon_source = QComboBox(container)
        carbon_source.setObjectName(f"{prefix}_materialFixedCarbonSource_{line_id}")
        self._populate_material_source_combo(carbon_source)
        volatile = QLineEdit(container)
        volatile.setObjectName(f"{prefix}_materialVolatile_{line_id}")
        volatile.setPlaceholderText("挥发分")
        volatile_source = QComboBox(container)
        volatile_source.setObjectName(f"{prefix}_materialVolatileSource_{line_id}")
        self._populate_material_source_combo(volatile_source)
        for widget, label in (
            (role, "物料类别"), (name, "物料名称"), (mass, "物料数量（t）"),
            (carbon, "固定碳含量（%）"), (carbon_source, "固定碳数据来源"),
            (volatile, "挥发分（%）"), (volatile_source, "挥发分数据来源"),
        ):
            widget.setProperty("businessFieldLabel", label)
        remove = QPushButton("删除", container)
        remove.setObjectName(f"remove_{prefix}_material_{line_id}")
        remove.clicked.connect(lambda _checked=False, _row=process_row, _id=line_id: self._remove_material_line(_row, _id))
        carbon_source.hide()
        volatile_source.hide()
        for widget, stretch in ((role, 2), (name, 2), (mass, 1), (carbon, 1), (volatile, 1), (remove, 0)):
            row_layout.addWidget(widget, stretch)
            self._wire_dirty_tracking(widget)
        self._wire_dirty_tracking(carbon_source)
        self._wire_dirty_tracking(volatile_source)
        for widget in (name, mass, carbon, volatile):
            widget.textChanged.connect(lambda *_args, _row=process_row: self._refresh_material_summary(_row))
        for widget in (role, carbon_source, volatile_source):
            widget.currentIndexChanged.connect(lambda *_args, _row=process_row: self._refresh_material_summary(_row))
        material = {
            "line_id": line_id,
            "widget": container,
            "remove_button": remove,
            "role": role,
            "name": name,
            "mass": mass,
            "fixed_carbon": carbon,
            "fixed_carbon_source": carbon_source,
            "volatile_matter": volatile,
            "volatile_matter_source": volatile_source,
        }
        layout.addWidget(container)
        material_rows.append(material)
        remove.setVisible(len(material_rows) > 1)
        for edit in (mass, carbon, volatile):
            edit.setValidator(QDoubleValidator(-1.0e15, 1.0e15, 12, edit))
            validator = edit.validator()
            if isinstance(validator, QDoubleValidator):
                validator.setLocale(QLocale.c())
        self._refresh_material_summary(process_row)
        self._refresh_source_cards()
        return material

    @staticmethod
    def _populate_material_source_combo(combo: QComboBox) -> None:
        # Current Canonical data has no standard defaults for process material
        # composition. The measured path is therefore the truthful default.
        combo.addItem("实测值", MaterialDataSource.MEASURED)
        combo.addItem("化学计算", MaterialDataSource.CHEMICAL_CALCULATION)
        combo.setCurrentIndex(0)

    def _remove_material_line(self, process_row: dict[str, object], line_id: str) -> None:
        materials = process_row.get("materials")
        if not isinstance(materials, list) or not materials:
            return
        if materials[0].get("line_id") == line_id:
            return
        for material in tuple(materials):
            if not isinstance(material, dict) or material.get("line_id") != line_id:
                continue
            widget = material.get("widget")
            if isinstance(widget, QWidget):
                widget.setParent(None)
                widget.deleteLater()
            materials.remove(material)
        for index, material in enumerate(materials):
            button = material.get("remove_button") if isinstance(material, dict) else None
            if isinstance(button, QWidget):
                button.setVisible(index > 0)
        self._refresh_material_summary(process_row)
        self._refresh_source_cards()

    def _material_inputs(self, process_row: dict[str, object]) -> tuple[MaterialInputLine, ...]:
        result: list[MaterialInputLine] = []
        material_rows = process_row.get("materials", [])
        if not isinstance(material_rows, list):
            return ()
        for row in material_rows:
            if not isinstance(row, dict):
                continue
            role = row.get("role")
            fixed_source = row.get("fixed_carbon_source")
            volatile_source = row.get("volatile_matter_source")
            if not isinstance(role, QComboBox) or not isinstance(fixed_source, QComboBox) or not isinstance(volatile_source, QComboBox):
                continue
            result.append(MaterialInputLine(
                line_id=str(row.get("line_id", "")),
                role=_enum(role.currentData(), MaterialRole),
                name=_value(row.get("name")) or "",
                mass_t=_value(row.get("mass")),
                fixed_carbon_percent=_value(row.get("fixed_carbon")),
                fixed_carbon_source=_enum(fixed_source.currentData(), MaterialDataSource),
                volatile_matter_percent=_value(row.get("volatile_matter")),
                volatile_matter_source=_enum(volatile_source.currentData(), MaterialDataSource),
            ))
        return tuple(result)

    def _refresh_material_summary(self, process_row: dict[str, object]) -> None:
        summary = process_row.get("material_summary")
        if not isinstance(summary, QLabel):
            return
        prefix = str(process_row.get("prefix", ""))
        if not prefix:
            return
        materials = self._material_inputs(process_row)
        active = tuple(
            line for line in materials
            if any(value is not None and str(value).strip() for value in (
                line.name, line.mass_t, line.fixed_carbon_percent, line.volatile_matter_percent,
            ))
        )
        if not active:
            row_fields = process_row.get("fields", {})
            legacy = []
            if isinstance(row_fields, dict):
                for key, widget in row_fields.items():
                    if isinstance(widget, QLineEdit) and widget.text().strip():
                        try:
                            label = get_field_spec(f"{prefix}.{key}").label
                        except KeyError:
                            label = str(key)
                        legacy.append(f"{label}：{widget.text().strip()}")
            if legacy:
                summary.setText("旧项目汇总值（继续使用）：" + "；".join(legacy) + "。新增物料明细后将按明细自动汇总。")
            else:
                summary.setText("软件汇总值：等待录入物料。")
            return
        normalized = normalize_material_inputs(prefix, active, policy=self.calculator.policy)
        if normalized.problems:
            summary.setText("软件汇总值：请补齐或修正物料数量和成分数值。")
            return
        values = dict(normalized.values)
        policy = self.calculator.policy
        format_value = lambda value: self.calculator.policy.format_for_display(value, 2)
        if prefix == "calcination":
            text = (
                f"原料 {format_value(values['gc'])} t · 固定碳 {format_value(policy.multiply(values['wfc'], Decimal('100')))}% · 挥发分 {format_value(policy.multiply(values['wvar'], Decimal('100')))}%；"
                f"输出 {format_value(policy.add(policy.add(values['cc'], values['ucc']), values['du']))} t · 固定碳 {format_value(policy.multiply(values['wfc_c'], Decimal('100')))}% · 挥发分 {format_value(policy.multiply(values['wvar_c'], Decimal('100')))}%"
            )
        elif prefix == "baking":
            text = (
                f"填充料 {format_value(values['bpm'])} t（固定碳 {format_value(policy.multiply(values['bpmfc'], Decimal('100')))}%、挥发分 {format_value(policy.multiply(values['bpmvar'], Decimal('100')))}%）；"
                f"待焙烧/炭化品 {format_value(values['bg'])} t（固定碳 {format_value(policy.multiply(values['bgfc'], Decimal('100')))}%、挥发分 {format_value(policy.multiply(values['bgvar'], Decimal('100')))}%）；"
                f"产品 {format_value(values['bp'])} t（固定碳 {format_value(policy.multiply(values['bpfc'], Decimal('100')))}%）；"
                f"粉尘/副产品碳 {format_value(values['bwt'])} tC"
            )
        else:
            text = (
                f"保温/电阻料 {format_value(values['gpm'])} t（固定碳 {format_value(policy.multiply(values['gpmfc'], Decimal('100')))}%、挥发分 {format_value(policy.multiply(values['gpmvar'], Decimal('100')))}%）；"
                f"待石墨化品 {format_value(values['gta'])} t（固定碳 {format_value(policy.multiply(values['gtafc'], Decimal('100')))}%）；"
                f"产品 {format_value(values['gp'])} t（固定碳 {format_value(policy.multiply(values['gpfc'], Decimal('100')))}%）；"
                f"粉尘/副产品碳 {format_value(values['gwt'])} tC"
            )
        summary.setText("物料汇总（仅供查看）：\n" + text.replace("；", "\n"))

    def _carbonate_options(self) -> tuple[object, ...]:
        queries = self._uat03_parameter_queries
        if queries is None:
            return ()
        try:
            return tuple(queries.carbonate_options(self._period()))
        except (AttributeError, DomainValidationError, KeyError, TypeError, ValueError):
            return ()

    @staticmethod
    def _normalized_catalog_name(value: str) -> str:
        return " ".join(value.strip().casefold().split())

    def _carbonate_option_for_text(self, text: str):
        wanted = self._normalized_catalog_name(text)
        if not wanted:
            return None
        for option in self._carbonate_options():
            names = (str(getattr(option, "label", "")), *(getattr(option, "aliases", ()) or ()))
            if any(self._normalized_catalog_name(str(name)) == wanted for name in names):
                return option
        return None

    def _populate_carbonate_selector(self, selector: QComboBox, *, text: str | None = None) -> None:
        previous = selector.currentText() if text is None else text
        blocker = QSignalBlocker(selector)
        selector.setEditable(True)
        selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        selector.clear()
        selector.addItem("未选择碳酸盐种类", None)
        seen: set[tuple[str, str]] = set()
        for option in self._carbonate_options():
            for label in (str(option.label), *(getattr(option, "aliases", ()) or ())):
                label = str(label).strip()
                key = (label.casefold(), str(option.subject_id))
                if not label or key in seen:
                    continue
                seen.add(key)
                selector.addItem(label, option)
        selector.setCurrentIndex(0)
        if previous and previous != "未选择碳酸盐种类":
            index = selector.findText(previous, Qt.MatchFlag.MatchExactly)
            if index >= 0:
                selector.setCurrentIndex(index)
            else:
                selector.setEditText(previous)
        selector.setPlaceholderText("搜索或输入碳酸盐名称/化学式")
        selector.lineEdit().setMaxLength(120)
        completer = selector.completer()
        if completer is not None:
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
        del blocker

    def _on_fgd_carbonate_text_changed(self, component: dict[str, object]) -> None:
        if self._restoring_workspace:
            return
        selector = component.get("carbonate_type")
        factor_edit = component.get("ef1")
        if not isinstance(selector, QComboBox) or not isinstance(factor_edit, QLineEdit):
            return
        option = self._carbonate_option_for_text(selector.currentText())
        if option is None:
            blocker = QSignalBlocker(factor_edit)
            factor_edit.clear()
            del blocker
            component["factor_mode"] = None
            component["catalog_factor_id"] = None
            return
        blocker = QSignalBlocker(factor_edit)
        factor_edit.setText(str(option.factor.value))
        del blocker
        component["factor_mode"] = "CATALOG"
        component["catalog_factor_id"] = option.factor.factor_id

    @staticmethod
    def _on_fgd_factor_value_changed(component: dict[str, object]) -> None:
        if component.get("factor_mode") == "CATALOG":
            component["factor_mode"] = "USER_DEFINED"
            component["catalog_factor_id"] = None
        elif component.get("factor_mode") not in {"MEASURED", "USER_DEFINED"}:
            component["factor_mode"] = "USER_DEFINED"

    def _refresh_carbonate_options(self) -> None:
        for unit in self._process_rows.get("fgd", ()):
            for component in unit.get("components", ()):
                selector = component.get("carbonate_type") if isinstance(component, dict) else None
                if isinstance(selector, QComboBox):
                    self._populate_carbonate_selector(selector)

    def _add_fgd_component(self, unit: dict[str, object], *, component_id: str | None = None) -> dict[str, object]:
        component_id = component_id or uuid4().hex
        components = unit["components"]
        assert isinstance(components, list)
        first = not components and len(self._process_rows["fgd"]) == 0
        component_host = unit["component_host"]
        component_layout = unit["component_layout"]
        assert isinstance(component_host, QWidget) and isinstance(component_layout, QVBoxLayout)
        container = QWidget(component_host)
        container.setObjectName(f"fgdComponent{component_id}")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(3)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        widgets: dict[str, QWidget] = {}
        field_labels = {
            "cal": "脱硫剂用量（t）",
            "carbonate_type": "碳酸盐种类",
            "i": "碳酸盐含量（%）",
            "ef1": "排放因子（tCO₂/t）",
            "tr": "转化率（%）",
        }
        for column, field in enumerate(("cal", "carbonate_type", "i", "ef1", "tr")):
            label = QLabel(field_labels[field], container)
            label.setWordWrap(True)
            grid.addWidget(label, 0, column)
            if field == "carbonate_type":
                selector = QComboBox(container)
                selector.setObjectName("fgdCarbonateTypeSelector" if first else f"fgd_{unit['instance_id']}_{component_id}_carbonateTypeSelector")
                selector.setProperty("fieldSpecKey", "fgd.ef1")
                self._populate_carbonate_selector(selector, text="未选择碳酸盐种类")
                widgets[field] = selector
                self._wire_dirty_tracking(selector)
            else:
                spec = get_field_spec(f"fgd.{field}")
                name = f"fgd_{field}" if first else f"fgd_{unit['instance_id']}_{component_id}_{field}"
                edit = create_typed_input(container, spec, name)
                widgets[field] = edit
                self._wire_dirty_tracking(edit)
            grid.addWidget(widgets[field], 1, column)
            grid.setColumnStretch(column, (2, 2, 1, 1, 1)[column])
        outer.addLayout(grid)
        footer = QHBoxLayout()
        source_ref = create_typed_input(container, get_field_spec("fgd.factor_source_reference"), "fgdFactorSourceReferenceInput" if first else f"fgd_{unit['instance_id']}_{component_id}_factorSourceReference")
        source_ref.setPlaceholderText("实测因子来源说明（可选）")
        widgets["factor_source_reference"] = source_ref
        self._wire_dirty_tracking(source_ref)
        source_ref.hide()
        widgets["ef1"].textChanged.connect(lambda text, _ref=source_ref: _ref.setVisible(bool(text.strip())))
        footer.addWidget(source_ref, 1)
        remove = QPushButton("删除组分", container)
        remove.setObjectName(f"remove_fgd_component_{unit['instance_id']}_{component_id}")
        remove.clicked.connect(lambda _checked=False, _unit=unit, _id=component_id: self._remove_fgd_component(_unit, _id))
        footer.addWidget(remove)
        outer.addLayout(footer)
        component_layout.addWidget(container)
        widgets["_widget"] = container
        widgets["remove_button"] = remove
        component_id_widget = QLineEdit(component_id, container)
        component_id_widget.hide()
        widgets["_component_id"] = component_id_widget
        widgets["component_id"] = component_id
        widgets["factor_mode"] = None
        widgets["catalog_factor_id"] = None
        selector = widgets["carbonate_type"]
        factor_edit = widgets["ef1"]
        assert isinstance(selector, QComboBox) and isinstance(factor_edit, QLineEdit)
        selector.currentTextChanged.connect(lambda _text, _component=widgets: self._on_fgd_carbonate_text_changed(_component))
        factor_edit.textChanged.connect(lambda _text, _component=widgets: self._on_fgd_factor_value_changed(_component))
        components.append(widgets)
        remove.setVisible(len(components) > 1)
        self._bind_process_aliases("fgd")
        return widgets

    def _remove_fgd_component(self, unit: dict[str, object], component_id: str) -> None:
        components = unit["components"]
        assert isinstance(components, list)
        if not components or components[0].get("component_id") == component_id:
            return
        for component in tuple(components):
            if component.get("component_id") == component_id:
                widget = component.get("_widget")
                if isinstance(widget, QWidget):
                    widget.setParent(None)
                    widget.deleteLater()
                components.remove(component)
        self._refresh_repeat_delete_controls()
        self._refresh_source_cards()

    def _remove_process_row(self, prefix: str, instance_id: str) -> None:
        rows = self._process_rows[prefix]
        if not rows or str(rows[0].get("instance_id")) == instance_id:
            return
        for row in tuple(rows):
            if row.get("instance_id") == instance_id:
                widget = row.get("widget")
                if isinstance(widget, QWidget):
                    widget.setParent(None)
                    widget.deleteLater()
                rows.remove(row)
        for index, row in enumerate(rows, start=1):
            title = row.get("title")
            display_title = row.get("display_title")
            if isinstance(title, QLabel) and isinstance(display_title, str):
                title.setText(f"{display_title} {index}")
        self._refresh_repeat_delete_controls()
        self._bind_process_aliases(prefix)
        self._refresh_source_cards()

    def _refresh_repeat_delete_controls(self) -> None:
        for index, row in enumerate(getattr(self, "_fuel_rows", ())):
            row.remove_button.setVisible(index > 0)
        for rows in getattr(self, "_energy_family_rows", {}).values():
            for index, row in enumerate(rows):
                row.remove_button.setVisible(index > 0)
        for rows in self._process_rows.values():
            for index, row in enumerate(rows):
                button = row.get("remove_button")
                if isinstance(button, QWidget):
                    button.setVisible(index > 0)
                materials = row.get("materials", [])
                if isinstance(materials, list):
                    for material_index, material in enumerate(materials):
                        remove = material.get("remove_button") if isinstance(material, dict) else None
                        if isinstance(remove, QWidget):
                            remove.setVisible(material_index > 0)
                components = row.get("components", [])
                if isinstance(components, list):
                    for component_index, component in enumerate(components):
                        remove = component.get("remove_button") if isinstance(component, dict) else None
                        if isinstance(remove, QWidget):
                            remove.setVisible(component_index > 0)

    def _bind_process_aliases(self, prefix: str) -> None:
        rows = self._process_rows[prefix]
        if not rows:
            return
        if prefix == "fgd":
            components = rows[0].get("components", [])
            if components:
                for key in ("cal", "i", "ef1", "tr", "factor_source_reference"):
                    self._fields[f"fgd.{key}"] = components[0][key]  # type: ignore[index]
                self._carbonate_type_selector = components[0]["carbonate_type"]  # type: ignore[assignment,index]
            return
        fields = rows[0].get("fields", {})
        for key, widget in fields.items():  # type: ignore[union-attr]
            self._fields[f"{prefix}.{key}"] = widget

    def _wire_dirty_tracking(self, widget: QWidget) -> None:
        if widget.property("dirtyTracked"):
            return
        widget.setProperty("dirtyTracked", True)
        if isinstance(widget, NumericLineEdit):
            widget.defer_range_validation_to_domain()
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self._mark_input_dirty)
            widget.textChanged.connect(lambda *_args: self._refresh_source_cards())
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._mark_input_dirty)
            widget.currentIndexChanged.connect(lambda *_args: self._refresh_source_cards())
            if widget.isEditable():
                widget.editTextChanged.connect(self._mark_input_dirty)
                widget.editTextChanged.connect(lambda *_args: self._refresh_source_cards())
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(self._mark_input_dirty)
            widget.valueChanged.connect(lambda *_args: self._refresh_source_cards())
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(self._mark_input_dirty)
            widget.toggled.connect(lambda *_args: self._refresh_source_cards())

    def _build_material_controls(self, parent_layout: QVBoxLayout, prefix: str, *, instance_id: str, controls_key: str, first: bool) -> None:
        """Build business-language basis controls with conditional expansion.

        The hidden widgets keep the existing Domain input contract and object
        names for compatibility.  Users see the standard received-basis
        summary by default; only a non-standard or inconsistent basis expands
        the conversion section.
        """

        suffix = "" if first else f"_{instance_id}"
        metadata = QWidget(self)
        metadata.setObjectName(f"{prefix}{suffix}_otherNecessaryData")
        metadata_layout = QVBoxLayout(metadata)
        metadata_layout.setContentsMargins(0, 8, 0, 0)
        summary_row = QHBoxLayout()
        basis_summary = QLabel("数据口径：收到基", metadata)
        basis_summary.setObjectName(f"{prefix}{suffix}_basisSummary")
        basis_summary.setWordWrap(True)
        summary_row.addWidget(basis_summary, 1)
        edit_button = QPushButton("修改", metadata)
        edit_button.setObjectName(f"{prefix}{suffix}_basisEditButton")
        edit_button.clicked.connect(lambda _checked=False, _key=controls_key: self._toggle_basis_editor(_key))
        summary_row.addWidget(edit_button)
        metadata_layout.addLayout(summary_row)

        default_parameter_id, _default_clause = _PROCESS_DEFAULT_PARAMETERS[prefix]
        default_factor = self._canonical_default_factor(default_parameter_id)
        default_summary = (
            f"挥发分折算系数：{default_factor.value}（标准一般取值，依据{_default_clause}；用于本过程物料计算）"
            if default_factor is not None
            else "当前目录暂无已核验的标准缺省参数；计算时会提示并阻断。"
        )
        parameter_summary = QLabel(default_summary, metadata)
        parameter_summary.setObjectName(f"{prefix}{suffix}_parameterSummary")
        parameter_summary.setWordWrap(True)
        metadata_layout.addWidget(parameter_summary)

        basis_editor = QWidget(metadata)
        basis_editor.setObjectName(f"{prefix}{suffix}_basisAndConversionEditor")
        basis_editor_layout = QFormLayout(basis_editor)
        basis_editor_layout.setContentsMargins(0, 8, 0, 0)
        basis_editor_title = QLabel("数据口径与换算", basis_editor)
        basis_editor_title.setObjectName(f"{prefix}{suffix}_basisAndConversionTitle")
        basis_editor_title.setWordWrap(True)
        basis_editor_layout.addRow(basis_editor_title)

        basis_options = (
            (MaterialBasis.UNKNOWN, "未确认"),
            (MaterialBasis.RECEIVED, "收到基"),
            (MaterialBasis.DRY, "干燥基"),
            (MaterialBasis.OTHER_DOCUMENTED, "其他有证基准"),
        )
        mass_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.mass_basis"), f"{prefix}{suffix}_massBasisSelector")
        composition_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.composition_basis"), f"{prefix}{suffix}_compositionBasisSelector")
        normalized_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.normalized_basis"), f"{prefix}{suffix}_normalizedBasisSelector")
        for combo in (mass_basis, composition_basis, normalized_basis):
            for value, label_text in basis_options:
                combo.addItem(label_text, value)
        basis_editor_layout.addRow("质量数据基准", mass_basis)
        basis_editor_layout.addRow("成分含量基准", composition_basis)

        component_options = (
            (MaterialComponentKind.UNKNOWN, "未确认"),
            (MaterialComponentKind.FIXED_CARBON, "固定碳"),
            (MaterialComponentKind.VOLATILE_MATTER, "挥发分"),
            (MaterialComponentKind.TOTAL_CARBON, "总碳（本字段不可直接采用）"),
        )
        fixed_carbon_component_kind = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.fixed_carbon_component_kind"),
            f"{prefix}{suffix}_fixedCarbonComponentKindSelector",
        )
        volatile_matter_component_kind = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.volatile_matter_component_kind"),
            f"{prefix}{suffix}_volatileMatterComponentKindSelector",
        )
        for combo in (fixed_carbon_component_kind, volatile_matter_component_kind):
            for value, label_text in component_options:
                combo.addItem(label_text, value)
        normalized_basis.setVisible(False)
        fixed_carbon_component_kind.setVisible(False)
        volatile_matter_component_kind.setVisible(False)

        automatic_component_summary = QLabel(
            "固定碳字段和挥发分字段由字段定义自动识别，不需要用户选择字段性质。",
            basis_editor,
        )
        automatic_component_summary.setObjectName(f"{prefix}{suffix}_automaticComponentSummary")
        automatic_component_summary.setWordWrap(True)
        basis_editor_layout.addRow("字段性质", automatic_component_summary)

        moisture_evidence = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.moisture_evidence"),
            f"{prefix}{suffix}_moistureEvidenceCheckBox",
        )
        moisture_evidence.setText("数据来源已记录")
        moisture_evidence.setObjectName(f"{prefix}{suffix}_moistureEvidenceCheckBox")
        conversion_evidence = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.conversion_evidence"),
            f"{prefix}{suffix}_conversionEvidenceCheckBox",
        )
        conversion_evidence.setText("换算依据已提供")
        conversion_evidence.setObjectName(f"{prefix}{suffix}_conversionEvidenceCheckBox")
        evidence_reference = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.evidence_reference"),
            f"{prefix}{suffix}_basisEvidenceReferenceInput",
            "报告/台账编号或来源说明（非收到基必填）",
        )
        basis_editor.setVisible(False)
        basis_warning = QLabel("", basis_editor)
        basis_warning.setObjectName(f"{prefix}{suffix}_basisWarning")
        basis_warning.setWordWrap(True)
        basis_editor_layout.addRow("提示", basis_warning)
        basis_editor_layout.addRow("数据来源", moisture_evidence)
        basis_editor_layout.addRow("换算依据", conversion_evidence)
        basis_editor_layout.addRow("报告/台账编号或来源说明", evidence_reference)

        professional_details = QLabel("", metadata)
        professional_details.setObjectName(f"{prefix}{suffix}_professionalDetails")
        professional_details.setWordWrap(True)
        metadata_layout.addWidget(basis_editor)
        metadata_layout.addWidget(professional_details)

        controls = {
            "mass_basis": mass_basis,
            "composition_basis": composition_basis,
            "normalized_basis": normalized_basis,
            "fixed_carbon_component_kind": fixed_carbon_component_kind,
            "volatile_matter_component_kind": volatile_matter_component_kind,
            "moisture_evidence": moisture_evidence,
            "conversion_evidence": conversion_evidence,
            "evidence_reference": evidence_reference,
            "basis_editor": basis_editor,
            "basis_summary": basis_summary,
            "basis_warning": basis_warning,
            "basis_edit_button": edit_button,
            "parameter_summary": parameter_summary,
            "professional_details": professional_details,
        }
        self._material_controls[controls_key] = controls
        if first:
            self._material_controls[prefix] = controls
        for widget in (mass_basis, composition_basis, moisture_evidence, conversion_evidence, evidence_reference):
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda _index, _key=controls_key: self._refresh_material_basis_display(_key))
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(lambda _checked, _key=controls_key: self._refresh_material_basis_display(_key))
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _text, _key=controls_key: self._refresh_material_basis_display(_key))
            self._wire_dirty_tracking(widget)
        self._register_professional_details(professional_details)
        parent_layout.addWidget(metadata)
        metadata.hide()
        self._refresh_material_basis_display(controls_key)

    @staticmethod
    def _basis_label(value: MaterialBasis) -> str:
        return {
            MaterialBasis.UNKNOWN: "未确认",
            MaterialBasis.RECEIVED: "收到基",
            MaterialBasis.DRY: "干燥基",
            MaterialBasis.OTHER_DOCUMENTED: "其他有证基准",
        }[value]

    @staticmethod
    def _component_kind_label(value: MaterialComponentKind) -> str:
        return {
            MaterialComponentKind.UNKNOWN: "未确认",
            MaterialComponentKind.FIXED_CARBON: "固定碳",
            MaterialComponentKind.VOLATILE_MATTER: "挥发分",
            MaterialComponentKind.TOTAL_CARBON: "总碳",
        }[value]

    def _material_basis_value(
        self,
        controls: dict[str, QWidget],
        key: str,
        default: MaterialBasis,
    ) -> MaterialBasis:
        value = controls[key].currentData()  # type: ignore[union-attr]
        try:
            value = _enum(value, MaterialBasis)
        except (TypeError, ValueError):
            return default
        if value is MaterialBasis.UNKNOWN:
            return default
        return value

    def _material_component_value(
        self,
        controls: dict[str, QWidget],
        key: str,
        default: MaterialComponentKind,
    ) -> MaterialComponentKind:
        value = controls[key].currentData()  # type: ignore[union-attr]
        try:
            value = _enum(value, MaterialComponentKind)
        except (TypeError, ValueError):
            return default
        if value is MaterialComponentKind.UNKNOWN:
            return default
        return value

    def _toggle_basis_editor(self, controls_key: str) -> None:
        controls = self._material_controls[controls_key]
        editor = controls["basis_editor"]
        requires_expansion = self._basis_requires_expansion(controls_key)
        visible = not editor.isVisible() or requires_expansion
        if visible or not requires_expansion:
            editor.setVisible(visible)
        self._refresh_material_basis_display(controls_key)

    def _basis_requires_expansion(self, controls_key: str) -> bool:
        controls = self._material_controls[controls_key]
        mass = self._material_basis_value(controls, "mass_basis", MaterialBasis.RECEIVED)
        composition = self._material_basis_value(controls, "composition_basis", MaterialBasis.RECEIVED)
        return mass is not MaterialBasis.RECEIVED or composition is not MaterialBasis.RECEIVED or mass is not composition

    def _refresh_material_basis_display(self, controls_key: str) -> None:
        prefix = controls_key.split("@", 1)[0]
        controls = self._material_controls.get(controls_key)
        if controls is None:
            return
        mass = self._material_basis_value(controls, "mass_basis", MaterialBasis.RECEIVED)
        composition = self._material_basis_value(controls, "composition_basis", MaterialBasis.RECEIVED)
        mass_label = self._basis_label(mass)
        composition_label = self._basis_label(composition)
        if mass is MaterialBasis.RECEIVED and composition is MaterialBasis.RECEIVED:
            summary = "数据口径：收到基"
        elif mass is composition:
            summary = f"数据口径：{mass_label}（需要换算为收到基）"
        else:
            summary = f"数据口径：不一致（质量数据：{mass_label}；成分含量：{composition_label}）"
        controls["basis_summary"].setText(summary)  # type: ignore[union-attr]

        requires_expansion = self._basis_requires_expansion(controls_key)
        editor = controls["basis_editor"]
        if requires_expansion:
            editor.setVisible(True)
        controls["basis_edit_button"].setText("收起" if editor.isVisible() and not requires_expansion else "修改")  # type: ignore[union-attr]

        warning = ""
        if mass is not composition:
            warning = (
                f"数据基准不一致：质量数据使用“{mass_label}”，成分含量使用“{composition_label}”。"
                "两者不能直接计算；请提供统一口径的换算依据和报告/台账编号或来源说明。"
            )
        elif mass is not MaterialBasis.RECEIVED:
            missing: list[str] = []
            if not controls["moisture_evidence"].isChecked():  # type: ignore[union-attr]
                missing.append("数据来源记录")
            if not controls["conversion_evidence"].isChecked():  # type: ignore[union-attr]
                missing.append("换算依据")
            if not _value(controls["evidence_reference"]):  # type: ignore[arg-type]
                missing.append("报告/台账编号或来源说明")
            warning = (
                f"当前数据为“{mass_label}”，标准计算需要统一到收到基，不能静默换算。"
                "请提供数据来源记录、换算依据和报告/台账编号或来源说明。"
            )
            if missing:
                warning += f" 当前还缺少：{'、'.join(missing)}。"
        elif editor.isVisible():
            warning = "默认按收到基处理；如使用其他基准，请填写对应的来源和换算信息。"
        controls["basis_warning"].setText(warning)  # type: ignore[union-attr]

        field_names = {
            "calcination": ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"),
            "baking": ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"),
            "graphitization": ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"),
        }[prefix]
        parameter_id, default_clause = _PROCESS_DEFAULT_PARAMETERS[prefix]
        default_factor = self._canonical_default_factor(parameter_id)
        detail_lines = [
            "专业详情（只读）",
            f"数据基准转换：质量数据 {mass_label}；成分含量 {composition_label}；内部归一目标：收到基。",
            "固定碳字段性质：固定碳（由字段定义自动确定）。",
            "挥发分字段性质：挥发分（由字段定义自动确定）。",
            (
                f"标准默认参数：{default_factor.value}（比例）；参数 ID：{parameter_id}；"
                f"标准条款：{default_clause}；参数来源：{default_factor.source_id}；"
                f"版本：{default_factor.factor_year}；定位：{default_factor.source_location}。"
                if default_factor is not None
                else f"标准默认参数：缺少已核验Catalog值；参数 ID：{parameter_id}；标准条款：{default_clause}。"
            ),
        ]
        for field in field_names:
            spec = get_field_spec(f"{prefix}.{field}")
            symbol = spec.standard_symbol or "未单列符号"
            detail_lines.append(
                f"{spec.display_name}（{symbol}）：标准条款 {spec.standard_clause}；来源定位：{spec.source_location}。"
            )
        controls["professional_details"].setText("\n".join(detail_lines))  # type: ignore[union-attr]

    def _build_electricity_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("购入电力/多条电力明细（I01；取得方式与电力属性独立）", self)
        label.setObjectName("electricitySectionTitle")
        parent_layout.addWidget(label)
        header = QLabel(
            " | ".join(
                (
                    get_field_spec("electricity.detail_id").label,
                    get_field_spec("electricity.amount").label,
                    get_field_spec("electricity.acquisition").label,
                    get_field_spec("electricity.attribute").label,
                    get_field_spec("electricity.proof_type").label,
                    get_field_spec("electricity.proof_status").label,
                    "操作",
                )
            ),
            self,
        )
        header.setWordWrap(True)
        parent_layout.addWidget(header)
        rows_host = QWidget(self)
        self.electricity_rows_layout = QVBoxLayout(rows_host)
        self.electricity_rows_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.addWidget(rows_host)
        buttons = QHBoxLayout()
        add_button = QPushButton("新增电力明细", self)
        add_button.setObjectName("addElectricityButton")
        add_button.clicked.connect(self._add_electricity_row)
        remove_button = QPushButton("删除最后一条", self)
        remove_button.setObjectName("removeLastElectricityButton")
        remove_button.clicked.connect(lambda: self._remove_electricity_row(self._electricity_rows[-1]) if self._electricity_rows else None)
        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)
        buttons.addStretch(1)
        parent_layout.addLayout(buttons)
        self._add_electricity_row()

    def _add_electricity_row(self, *, row_key: str | None = None) -> None:
        self._electricity_row_serial += 1
        row = _ElectricityRow(
            self._electricity_row_serial,
            self._remove_electricity_row,
            self,
            row_key=row_key,
        )
        self._electricity_rows.append(row)
        row.set_professional_details_visible(False)
        self.electricity_rows_layout.addWidget(row)
        row.detail_id.textChanged.connect(lambda _text: self._refresh_electricity_rows())
        row.amount.textChanged.connect(lambda _text: self._refresh_electricity_rows())
        for combo in (row.acquisition, row.attribute, row.proof_type, row.proof_status):
            combo.currentIndexChanged.connect(lambda _index: self._refresh_electricity_rows())
        row.detail_id.textChanged.connect(self._mark_input_dirty)
        row.amount.textChanged.connect(self._mark_input_dirty)
        row.detail_id.textChanged.connect(lambda _text: self._refresh_source_cards())
        row.amount.textChanged.connect(lambda _text: self._refresh_source_cards())
        for combo in (row.acquisition, row.attribute, row.proof_type, row.proof_status):
            combo.currentIndexChanged.connect(self._mark_input_dirty)
            combo.currentIndexChanged.connect(lambda _index: self._refresh_source_cards())
        if hasattr(self, "result_card") and not self._restoring_workspace:
            self._mark_input_dirty()

    def _remove_electricity_row(self, row: QWidget) -> None:
        if row in self._electricity_rows:
            self._electricity_rows.remove(row)
            self.electricity_rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
            self._refresh_source_cards()
            if hasattr(self, "result_card") and not self._restoring_workspace:
                self._mark_input_dirty()

    def _build_output_electricity_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("输出电力（从间接排放中抵扣）", self)
        label.setObjectName("exportedElectricitySectionTitle")
        parent_layout.addWidget(label)
        self._output_electricity_host = QWidget(self)
        self._output_electricity_layout = QVBoxLayout(self._output_electricity_host)
        self._output_electricity_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.addWidget(self._output_electricity_host)
        add_button = QPushButton("新增输出电力来源", self)
        add_button.setObjectName("addExportedElectricityButton")
        add_button.clicked.connect(lambda: self._add_output_electricity_row())
        parent_layout.addWidget(add_button)
        self._add_output_electricity_row(first=True)

    def _add_output_electricity_row(self, *, first: bool = False, line_id: str | None = None) -> dict[str, object]:
        existing_ids = {
            _value(row["id"]) or str(row["default_line_id"])
            for row in self._output_electricity_rows
        }
        if line_id is None:
            while True:
                self._output_electricity_row_serial += 1
                line_id = f"exported-electricity-{self._output_electricity_row_serial}"
                if line_id not in existing_ids:
                    break
        else:
            serial = line_id.rsplit("-", 1)
            if len(serial) == 2 and serial[0] == "exported-electricity" and serial[1].isdigit():
                self._output_electricity_row_serial = max(self._output_electricity_row_serial, int(serial[1]))
        row_widget = QWidget(self._output_electricity_host)
        row_widget.setObjectName("exportedElectricityRow" if first else f"exportedElectricityRow_{line_id}")
        form = QFormLayout(row_widget)
        object_suffix = "" if first else f"_{line_id}"
        line_id_widget = create_typed_input(
            row_widget, get_field_spec("exported_electricity_id"),
            "exportedElectricityLineIdInput" if first else f"exportedElectricityLineIdInput_{line_id}",
            "可选：填写来源名称或凭证编号",
        )
        amount_widget = create_typed_input(
            row_widget, get_field_spec("exported_electricity_amount"),
            "exportedElectricityAmountInput" if first else f"exportedElectricityAmountInput_{line_id}", "MWh",
        )
        factor_selector = QComboBox(row_widget)
        factor_selector.setObjectName(f"exportedElectricityFactorSelector{object_suffix}")
        factor_selector.addItem("自動采用适用标准因子", None)
        self._populate_factor_combo(factor_selector, "electricity_emission_factor_national")
        measured_value = QLineEdit(row_widget)
        measured_value.setObjectName(f"exportedElectricityMeasuredFactor{object_suffix}")
        measured_value.setPlaceholderText("可选：本来源实测排放因子（tCO₂/MWh）")
        source_reference = QLineEdit(row_widget)
        source_reference.setObjectName(f"exportedElectricityFactorSource{object_suffix}")
        source_reference.setPlaceholderText("填写实测来源编号")
        form.addRow("来源标识", line_id_widget)
        form.addRow("输出电量", amount_widget)
        form.addRow("适用排放因子", factor_selector)
        form.addRow("实测因子", measured_value)
        form.addRow("实测来源", source_reference)
        remove_button = QPushButton("删除本条来源", row_widget)
        remove_button.setObjectName(f"removeExportedElectricity{object_suffix}")
        remove_button.clicked.connect(lambda _checked=False, _row=row_widget: self._remove_output_electricity_row(_row))
        form.addRow(remove_button)
        self._output_electricity_layout.addWidget(row_widget)
        row = {
            "widget": row_widget,
            "id": line_id_widget,
            "default_line_id": line_id,
            "amount": amount_widget,
            "factor": factor_selector,
            "measured": measured_value,
            "source": source_reference,
        }
        self._output_electricity_rows.append(row)
        if first:
            self._fields["exported_electricity_id"] = line_id_widget
            self._fields["exported_electricity_amount"] = amount_widget
        for widget in row.values():
            if isinstance(widget, QWidget):
                self._wire_dirty_tracking(widget)
        self._refresh_source_cards()
        return row

    def _remove_output_electricity_row(self, widget: QWidget) -> None:
        if len(self._output_electricity_rows) <= 1:
            return
        for row in tuple(self._output_electricity_rows):
            if row.get("widget") is widget:
                self._output_electricity_rows.remove(row)
                widget.setParent(None)
                widget.deleteLater()
        self._bind_output_electricity_aliases()
        self._refresh_source_cards()

    def _bind_output_electricity_aliases(self) -> None:
        if not self._output_electricity_rows:
            return
        self._fields["exported_electricity_id"] = self._output_electricity_rows[0]["id"]  # type: ignore[assignment]
        self._fields["exported_electricity_amount"] = self._output_electricity_rows[0]["amount"]  # type: ignore[assignment]

    def _populate_factor_combo(self, selector: QComboBox, parameter_id: str) -> None:
        factors = sorted(self.catalog_service.list_parameter_factors(parameter_id), key=lambda item: (-(item.factor_year or 0), item.factor_id))
        if parameter_id == "electricity_emission_factor_national":
            self._electricity_factor_records = {item.factor_id: item for item in factors}
        for item in factors:
            selector.addItem(f"{item.normalized_value} {item.normalized_unit} · {item.factor_id}", item.factor_id)

    def _build_heat_section(self, parent_layout: QVBoxLayout) -> None:
        parent_layout.addWidget(QLabel("购入热力/动力", self))
        self.heat_rows_host = QWidget(self)
        self.heat_rows_layout = QVBoxLayout(self.heat_rows_host)
        self.heat_rows_layout.setContentsMargins(0, 0, 0, 0)
        row = self._create_heat_row("heat", first=True, line_id="heat-1")
        self.heat_rows_layout.addWidget(row["widget"])
        parent_layout.addWidget(self.heat_rows_host)
        self._heat_rows["heat"].append(row)
        self._bind_heat_aliases("heat")
        self._heat_steam_kind = row["steam"]
        self.heat_measured_factor = row["measured"]
        self.heat_factor_source_reference = row["source"]
        add_button = QPushButton("新增购入热力来源", self)
        add_button.setObjectName("addPurchasedHeatButton")
        add_button.clicked.connect(lambda: self._add_heat_row("heat"))
        parent_layout.addWidget(add_button)
        self._build_legacy_heat_parameter_controls("heat", row["widget"])
        row["factor"] = self.heat_factor_selector
        row["reason"] = self.heat_factor_selection_reason
        self._populate_heat_factor_selector()

    def _build_output_heat_section(self, parent_layout: QVBoxLayout) -> None:
        parent_layout.addWidget(QLabel("输出热力/动力（从间接排放中抵扣）", self))
        self.exported_heat_rows_host = QWidget(self)
        self.exported_heat_rows_layout = QVBoxLayout(self.exported_heat_rows_host)
        self.exported_heat_rows_layout.setContentsMargins(0, 0, 0, 0)
        row = self._create_heat_row("exported_heat", first=True, line_id="exported-heat-1")
        self.exported_heat_rows_layout.addWidget(row["widget"])
        parent_layout.addWidget(self.exported_heat_rows_host)
        self._heat_rows["exported_heat"].append(row)
        self._bind_heat_aliases("exported_heat")
        self._exported_heat_steam_kind = row["steam"]
        self.exported_heat_measured_factor = row["measured"]
        self.exported_heat_factor_source_reference = row["source"]
        self._build_legacy_heat_parameter_controls("exported_heat", row["widget"])
        row["factor"] = self.exported_heat_factor_selector
        row["reason"] = self.exported_heat_factor_reason
        add_button = QPushButton("新增输出热力来源", self)
        add_button.setObjectName("addExportedHeatButton")
        add_button.clicked.connect(lambda: self._add_heat_row("exported_heat"))
        parent_layout.addWidget(add_button)
        self._populate_heat_factor_selector()

    def _build_legacy_heat_parameter_controls(self, prefix: str, parent: QWidget) -> None:
        """Keep legacy factor controls hidden so saved Project state still restores."""
        compatibility = QWidget(parent)
        compatibility.setObjectName(f"{prefix}LegacyParameterControls")
        compatibility_layout = QVBoxLayout(compatibility)
        if prefix == "heat":
            self.heat_factor_selector = QComboBox(compatibility)
            self.heat_factor_selector.setObjectName("heatFactorSelector")
            self.heat_factor_selector.setProperty("fieldSpecKey", "heat_factor")
            self.heat_factor_selector.currentIndexChanged.connect(self._refresh_heat_factor_details)
            self.heat_factor_metadata = create_read_only_parameter(compatibility, get_field_spec("heat_factor"), "heatFactorMetadata")
            self.parameter_selection_status = QLabel("", compatibility)
            self.parameter_selection_status.setObjectName("parameterSelectionStatus")
            self.heat_factor_professional_details = QLabel("", compatibility)
            self.heat_factor_professional_details.setObjectName("heatFactorProfessionalDetails")
            self.heat_factor_selection_reason = QLineEdit(compatibility)
            self.heat_factor_selection_reason.setObjectName("heatFactorSelectionReasonInput")
            self.heat_factor_advanced_panel = compatibility
            self._heat_factor_advanced_panel = compatibility
            self.heat_factor_edit_button = QPushButton("", compatibility)
        else:
            self.exported_heat_factor_selector = QComboBox(compatibility)
            self.exported_heat_factor_selector.setObjectName("exportedHeatFactorSelector")
            self.exported_heat_factor_reason = QLineEdit(compatibility)
            self.exported_heat_factor_reason.setObjectName("exportedHeatFactorReasonInput")
        for widget in compatibility.findChildren(QWidget):
            self._wire_dirty_tracking(widget)
        compatibility.hide()
        self._legacy_heat_controls[prefix] = compatibility

    def _populate_heat_combo(self, selector: QComboBox) -> None:
        selector.clear()
        for factor_id, record in self._heat_factor_records.items():
            category = self.catalog_service.value_category(record)
            category_label = self.catalog_service.value_category_label(category)
            selector.addItem(f"{category_label}：{record.normalized_value} {record.normalized_unit}", factor_id)
        if not selector.count():
            selector.addItem("暂无可用的标准热力参数", None)
            selector.setEnabled(False)

    def _create_heat_row(self, prefix: str, *, first: bool, line_id: str) -> dict[str, object]:
        line_prefix = prefix.replace("_", "-")
        container = QWidget(self)
        container.setObjectName(f"{prefix}Line_{line_id}")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 6)
        form = QFormLayout()
        layout.addLayout(form)
        names = {
            "heat": ("heat_id", "heat_amount", "heat_enthalpy", "heat_pressure", "heat_temperature", "heat_steam_kind"),
            "exported_heat": ("exported_heat_id", "exported_heat_amount", "exported_heat_enthalpy", "exported_heat_pressure", "exported_heat_temperature", "exported_heat_steam_kind"),
        }[prefix]
        keys = names
        if first:
            object_names = {
                "heat": ("heat_idInput", "heat_amountInput", "heat_enthalpyInput", "heat_pressureInput", "heat_temperatureInput", "heatSteamKindSelector"),
                "exported_heat": ("exportedHeatLineIdInput", "exportedHeatAmountInput", "exportedHeatEnthalpyInput", "exportedHeatPressureInput", "exportedHeatTemperatureInput", "exportedHeatSteamKindSelector"),
            }[prefix]
        else:
            object_names = (
                f"{prefix}LineId_{line_id}", f"{prefix}Amount_{line_id}",
                f"{prefix}Enthalpy_{line_id}", f"{prefix}Pressure_{line_id}",
                f"{prefix}Temperature_{line_id}", f"{prefix}SteamKind_{line_id}",
            )
        visible_name = "购入热力来源1" if prefix == "heat" and first else "输出热力来源1" if first else ""
        source_name = create_typed_input(container, get_field_spec(keys[0]), object_names[0], visible_name)
        source_name.setPlaceholderText("可选：填写来源名称或用途")
        amount = create_typed_input(container, get_field_spec(keys[1]), object_names[1])
        amount.setPlaceholderText("例如：12.5")
        pressure = create_typed_input(container, get_field_spec(keys[3]), object_names[3])
        pressure.setPlaceholderText("例如：1.4")
        temperature = create_typed_input(container, get_field_spec(keys[4]), object_names[4])
        temperature.setPlaceholderText("例如：250")
        enthalpy = create_typed_input(container, get_field_spec(keys[2]), object_names[2])
        enthalpy.setPlaceholderText("例如：2810")
        steam = QComboBox(container)
        steam.setObjectName(object_names[5])
        steam.addItem("饱和蒸汽", SteamKind.SATURATED)
        steam.addItem("过热蒸汽", SteamKind.SUPERHEATED)
        enthalpy_mode = QComboBox(container)
        enthalpy_mode.setObjectName(f"{prefix}EnthalpyMode_{line_id}" if not first else ("heatEnthalpyModeSelector" if prefix == "heat" else "exportedHeatEnthalpyModeSelector"))
        enthalpy_mode.addItem("自动计算", "AUTO")
        enthalpy_mode.addItem("手动填写焓值", "MANUAL")
        factor_mode = QComboBox(container)
        factor_mode.setObjectName(f"{prefix}FactorMode_{line_id}" if not first else ("heatFactorModeSelector" if prefix == "heat" else "exportedHeatFactorModeSelector"))
        default_factor = self._canonical_default_factor("heat_emission_factor_default")
        factor_value = getattr(default_factor, "value", None)
        factor_display = self.calculator.policy.format_for_display(factor_value, 2) if factor_value is not None else "暂无"
        factor_mode.addItem(f"标准缺省值（{factor_display} tCO₂/GJ）", HeatFactorMode.STANDARD_DEFAULT)
        factor_mode.addItem("使用实测值", HeatFactorMode.MEASURED)
        measured = QLineEdit(container)
        measured_name = (
            "heatMeasuredFactorInput" if prefix == "heat" and first else
            "exportedHeatMeasuredFactorInput" if prefix == "exported_heat" and first else
            f"{prefix}MeasuredFactor_{line_id}"
        )
        if prefix == "heat" and not first:
            measured_name = f"heatMeasuredFactor_{line_id}"
        measured.setObjectName(measured_name)
        measured.setPlaceholderText("例如：0.11")
        factor_source = QLineEdit(container)
        factor_source_name = (
            "heatFactorSourceReferenceInput" if prefix == "heat" and first else
            "exportedHeatFactorSourceReferenceInput" if prefix == "exported_heat" and first else
            f"{prefix}FactorSource_{line_id}"
        )
        if prefix == "heat" and not first:
            factor_source_name = f"heatFactorSource_{line_id}"
        factor_source.setObjectName(factor_source_name)
        factor_source.setPlaceholderText("可选：简短来源说明")
        preview = QLabel("自动计算焓值：请填写蒸汽压力（绝压）。", container)
        preview.setObjectName(f"{prefix}EnthalpyPreview_{line_id}")
        preview.setWordWrap(True)
        form.addRow("来源名称（可选）", source_name)
        form.addRow("蒸汽类型", steam)
        form.addRow("蒸汽量（t）", amount)
        form.addRow("蒸汽压力（MPa，绝压）", pressure)
        form.addRow("蒸汽温度（℃）", temperature)
        form.addRow("焓值方式", enthalpy_mode)
        enthalpy_label = QLabel("手动填写焓值（kJ/kg）", container)
        form.addRow(enthalpy_label, enthalpy)
        form.addRow("自动参考值", preview)
        form.addRow("热力排放因子", factor_mode)
        form.addRow("实测排放因子（tCO₂/GJ）", measured)
        form.addRow("实测来源说明（可选）", factor_source)
        enthalpy.hide()
        enthalpy_label.hide()
        temperature_label = form.labelForField(temperature)
        if temperature_label is not None:
            temperature_label.hide()
        temperature.hide()
        measured_label = form.labelForField(measured)
        source_label = form.labelForField(factor_source)
        measured.hide()
        factor_source.hide()
        if measured_label is not None:
            measured_label.hide()
        if source_label is not None:
            source_label.hide()

        row: dict[str, object] = {
            "widget": container,
            "id": source_name,
            "default_line_id": line_id,
            "amount": amount,
            "enthalpy": enthalpy,
            "enthalpy_label": enthalpy_label,
            "pressure": pressure,
            "temperature": temperature,
            "temperature_label": temperature_label,
            "steam": steam,
            "enthalpy_mode": enthalpy_mode,
            "preview": preview,
            "factor_mode": factor_mode,
            "measured": measured,
            "measured_label": measured_label,
            "source": factor_source,
            "source_label": source_label,
            "factor": None,
            "reason": None,
            "legacy_factor_override": False,
        }
        if not first:
            compatibility = QWidget(container)
            compatibility_layout = QFormLayout(compatibility)
            selector = QComboBox(compatibility)
            selector.setObjectName(
                f"heatFactorSelector_{line_id}" if prefix == "heat"
                else f"exported_heatFactorSelector_{line_id}"
            )
            reason = QLineEdit(compatibility)
            reason.setObjectName(
                f"heatFactorReason_{line_id}" if prefix == "heat"
                else f"exported_heatFactorReason_{line_id}"
            )
            compatibility_layout.addRow(selector)
            compatibility_layout.addRow(reason)
            compatibility.hide()
            row["factor"] = selector
            row["reason"] = reason
        if not first:
            remove = QPushButton("删除本条来源", container)
            remove.setObjectName(f"remove_{prefix}_{line_id}")
            remove.clicked.connect(lambda _checked=False, _prefix=prefix, _widget=container: self._remove_heat_row(_prefix, _widget))
            layout.addWidget(remove)
        for widget in (source_name, amount, pressure, temperature, enthalpy, steam, enthalpy_mode, factor_mode, measured, factor_source):
            self._wire_dirty_tracking(widget)
        for widget in (pressure, temperature, steam, enthalpy_mode, factor_mode):
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda *_args, _row=row: self._refresh_heat_row_presentation(_row))
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda *_args, _row=row: self._refresh_heat_row_presentation(_row))
        factor_mode.currentIndexChanged.connect(lambda *_args, _row=row: _row.__setitem__("legacy_factor_override", False))
        self._refresh_heat_row_presentation(row)
        return row

    def _refresh_heat_row_presentation(self, row: dict[str, object]) -> None:
        mode = row.get("enthalpy_mode")
        manual = isinstance(mode, QComboBox) and mode.currentData() == "MANUAL"
        enthalpy = row.get("enthalpy")
        enthalpy_label = row.get("enthalpy_label")
        if isinstance(enthalpy_label, QWidget):
            enthalpy_label.setVisible(manual)
        if isinstance(enthalpy, QWidget):
            enthalpy.setVisible(manual)
        steam = row.get("steam")
        try:
            steam_kind = _enum(steam.currentData(), SteamKind) if isinstance(steam, QComboBox) else None
        except ValueError:
            steam_kind = None
        superheated = steam_kind is SteamKind.SUPERHEATED
        temperature = row.get("temperature")
        temperature_label = row.get("temperature_label")
        if isinstance(temperature, QWidget):
            temperature.setVisible(superheated)
        if isinstance(temperature_label, QWidget):
            temperature_label.setVisible(superheated)
        factor_mode = row.get("factor_mode")
        try:
            selected_factor_mode = _enum(factor_mode.currentData(), HeatFactorMode) if isinstance(factor_mode, QComboBox) else None
        except ValueError:
            selected_factor_mode = None
        measured_mode = selected_factor_mode is HeatFactorMode.MEASURED
        for key in ("measured", "measured_label", "source", "source_label"):
            part = row.get(key)
            if isinstance(part, QWidget):
                part.setVisible(measured_mode)
        self._refresh_heat_row_preview(row)

    def _refresh_heat_row_preview(self, row: dict[str, object]) -> None:
        preview = row.get("preview")
        pressure_widget = row.get("pressure")
        temperature_widget = row.get("temperature")
        steam_widget = row.get("steam")
        mode_widget = row.get("enthalpy_mode")
        if not isinstance(preview, QLabel) or not isinstance(pressure_widget, QLineEdit) or not isinstance(steam_widget, QComboBox):
            return
        pressure_text = pressure_widget.text().strip()
        try:
            kind = _enum(steam_widget.currentData(), SteamKind)
        except ValueError:
            preview.setText("自动计算焓值：请选择蒸汽类型。")
            return
        temperature_text = temperature_widget.text().strip() if isinstance(temperature_widget, QLineEdit) else ""
        try:
            if not pressure_text or (kind is SteamKind.SUPERHEATED and not temperature_text):
                missing = "蒸汽压力（绝压）" if not pressure_text else "过热蒸汽温度"
                preview.setText(f"自动计算焓值：请填写{missing}。")
                return
            policy = self.calculator.policy
            pressure = policy.parse(pressure_text)
            if kind is SteamKind.SUPERHEATED:
                reference = superheated_steam_enthalpy(pressure, policy.parse(temperature_text), policy=policy)[0]
                table_name = "附录 C.5"
            else:
                reference = saturated_steam_enthalpy(pressure, policy=policy)[0]
                table_name = "附录 C.4"
        except (ValueError, InvalidOperation, DomainValidationError):
            preview.setText("自动计算焓值：当前压力或温度超出标准表范围，或格式无效。")
            return
        formatted = policy.format_for_display(reference, 1)
        manual = isinstance(mode_widget, QComboBox) and mode_widget.currentData() == "MANUAL"
        if manual:
            preview.setText(f"按{table_name}计算的参考焓值：{formatted} kJ/kg；本次将采用手动填写值。")
        else:
            preview.setText(f"自动计算焓值：{formatted} kJ/kg（{table_name}）。")

    def _refresh_all_heat_enthalpy_previews(self) -> None:
        for rows in self._heat_rows.values():
            for row in rows:
                self._refresh_heat_row_presentation(row)

    def _convert_legacy_steam_amounts_to_tonnes(self) -> None:
        policy = self.calculator.policy
        for rows in self._heat_rows.values():
            for row in rows:
                amount = row.get("amount")
                if not isinstance(amount, QLineEdit) or not amount.text().strip():
                    continue
                try:
                    tonnes = policy.divide(policy.parse(amount.text().strip()), Decimal("1000"))
                except (InvalidOperation, ValueError, DomainValidationError):
                    continue
                amount.setText(format(tonnes, "f"))

    def _set_legacy_heat_factor_mode(self, row: dict[str, object]) -> None:
        mode = row.get("factor_mode")
        measured = row.get("measured")
        selector = row.get("factor")
        if isinstance(mode, QComboBox):
            selected_mode = HeatFactorMode.MEASURED if _value(measured) is not None else HeatFactorMode.STANDARD_DEFAULT
            mode.setCurrentIndex(max(0, mode.findData(selected_mode)))
        selected_factor = selector.currentData() if isinstance(selector, QComboBox) else None
        default_factor = self._canonical_default_factor("heat_emission_factor_default")
        default_id = getattr(default_factor, "factor_id", None)
        row["legacy_factor_override"] = isinstance(selected_factor, str) and selected_factor != default_id
        self._refresh_heat_row_presentation(row)

    def _add_heat_row(self, prefix: str, *, line_id: str | None = None) -> dict[str, object]:
        rows = self._heat_rows[prefix]
        line_prefix = prefix.replace("_", "-")
        existing_ids = {_value(row["id"]) or str(row["default_line_id"]) for row in rows}
        if line_id is None:
            while True:
                self._heat_row_serials[prefix] += 1
                line_id = f"{line_prefix}-{self._heat_row_serials[prefix]}"
                if line_id not in existing_ids:
                    break
        else:
            serial = line_id.rsplit("-", 1)
            if len(serial) == 2 and serial[0] == line_prefix and serial[1].isdigit():
                self._heat_row_serials[prefix] = max(self._heat_row_serials[prefix], int(serial[1]))
        host = self.heat_rows_layout if prefix == "heat" else self.exported_heat_rows_layout
        row = self._create_heat_row(prefix, first=False, line_id=line_id)
        container = row["widget"]
        selector = row.get("factor")
        if isinstance(selector, QComboBox):
            self._populate_heat_combo(selector)
        host.addWidget(container)
        rows.append(row)
        self._refresh_source_cards()
        return row

    def _remove_heat_row(self, prefix: str, widget: QWidget) -> None:
        rows = self._heat_rows[prefix]
        if len(rows) <= 1:
            return
        for row in tuple(rows):
            if row.get("widget") is widget:
                rows.remove(row)
                widget.setParent(None)
                widget.deleteLater()
        self._bind_heat_aliases(prefix)
        self._refresh_source_cards()

    def _bind_heat_aliases(self, prefix: str) -> None:
        if not self._heat_rows[prefix]:
            return
        field_names = ("heat_id", "heat_amount", "heat_enthalpy", "heat_pressure", "heat_temperature") if prefix == "heat" else ("exported_heat_id", "exported_heat_amount", "exported_heat_enthalpy", "exported_heat_pressure", "exported_heat_temperature")
        for key, value in zip(field_names, ("id", "amount", "enthalpy", "pressure", "temperature")):
            self._fields[key] = self._heat_rows[prefix][0][value]  # type: ignore[assignment]

    def _populate_heat_factor_selector(self) -> None:
        records = sorted(
            self.catalog_service.list_parameter_factors("heat_emission_factor_default"),
            key=lambda item: (-(item.factor_year or 0), item.factor_id),
        )
        self._heat_factor_records = {item.factor_id: item for item in records}
        for rows in self._heat_rows.values():
            for row in rows:
                selector = row.get("factor")
                if isinstance(selector, QComboBox):
                    self._populate_heat_combo(selector)
        if hasattr(self, "heat_factor_selector") and not self._heat_rows["heat"]:
            self._populate_heat_combo(self.heat_factor_selector)
        if hasattr(self, "exported_heat_factor_selector") and not self._heat_rows["exported_heat"]:
            self._populate_heat_combo(self.exported_heat_factor_selector)
        self._refresh_heat_factor_details()

    def _heat_resolution_context(self, *, energy_direction: str = "purchased_heat", confirmed_factor_id: str | None = None, confirmation_reason: str | None = None) -> ParameterResolutionContext:
        return ParameterResolutionContext(
            parameter_id="heat_emission_factor_default",
            standard_id=self.standard_id,
            accounting_period=self._period(),
            parameter_type=ParameterType.HEAT_EMISSION_FACTOR,
            subject_id="purchased_heat",
            emission_source_type=energy_direction,
            confirmed_factor_id=confirmed_factor_id,
            confirmation_reason=confirmation_reason,
            extra_context=(("energy_direction", energy_direction),),
        )

    def _refresh_heat_factor_details(self) -> None:
        if not hasattr(self, "heat_factor_selector"):
            return
        self._refresh_heat_factor_default_labels()
        factor_id = self.heat_factor_selector.currentData()
        if factor_id is None or factor_id not in self._heat_factor_records:
            self.heat_factor_metadata.setText("推荐热力因子：暂无可用的标准参数；填写热力数据时会明确提示。")
            if hasattr(self, "parameter_selection_status"):
                self.parameter_selection_status.setText("采用依据：当前没有可用的标准热力参数。")
            return
        record = self._heat_factor_records[factor_id]
        category = self.catalog_service.value_category(record)
        category_label = self.catalog_service.value_category_label(category)
        self.heat_factor_metadata.setText(
            f"推荐热力因子：{record.normalized_value} {record.normalized_unit} · "
            f"{category_label} · {_review_status_label(record.review_status)}"
        )
        professional_lines = (
            "专业详情（只读）",
            f"参数 ID：{record.parameter_id}",
            f"因子 ID：{record.factor_id}",
            f"标准条款：{get_field_spec('heat_factor').standard_clause}",
            f"参数来源：{record.source_id or '未提供'}；来源定位：{record.source_location or '未提供'}",
            f"审核状态：{_review_status_label(record.review_status)}",
        )
        self.heat_factor_professional_details.setText("\n".join(professional_lines))
        if self._parameter_resolver is not None:
            try:
                resolution = self._parameter_resolver.resolve(self._heat_resolution_context())
            except (DomainValidationError, ValueError):
                resolution = None
            if resolution is not None and resolution.recommended is not None and resolution.recommended.factor_id == factor_id:
                if not self.heat_factor_selection_reason.text().strip():
                    self.heat_factor_selection_reason.setText(resolution.selection_reason)
                status = f"采用依据：按当前核算期间自动推荐的{category_label}。"
            else:
                status = "采用依据：当前选择不是自动推荐值；请在高级参数选择中填写理由。"
            if hasattr(self, "parameter_selection_status"):
                self.parameter_selection_status.setText(status)

    def _refresh_heat_factor_default_labels(self) -> None:
        factor = self._canonical_default_factor("heat_emission_factor_default")
        value = getattr(factor, "value", None)
        display = self.calculator.policy.format_for_display(value, 2) if value is not None else "暂无适用值"
        label = f"标准缺省值（{display} tCO₂/GJ）"
        for rows in self._heat_rows.values():
            for row in rows:
                selector = row.get("factor_mode")
                if not isinstance(selector, QComboBox):
                    continue
                index = selector.findData(HeatFactorMode.STANDARD_DEFAULT)
                if index >= 0:
                    selector.setItemText(index, label)

    def _toggle_heat_parameter_advanced(self) -> None:
        visible = not self._heat_factor_advanced_panel.isVisible()
        self._heat_factor_advanced_panel.setVisible(visible)
        self.heat_factor_edit_button.setText("收起参数选择" if visible else "更改参数")

    def _on_period_choice_changed(self, index: int) -> None:
        is_custom = index == 13
        self.custom_period_row.setVisible(is_custom)
        self.custom_period_label.setVisible(is_custom)
        if 1 <= index <= 12:
            blocker = QSignalBlocker(self.period_month)
            self.period_month.setValue(index)
            del blocker
        self._refresh_heat_factor_details()
        self._refresh_fuel_defaults()
        self._refresh_energy_parameters()

    def _sync_period_choice_from_month(self, month: int) -> None:
        if 1 <= month <= 12:
            blocker = QSignalBlocker(self.period_type)
            self.period_type.setCurrentIndex(month)
            del blocker
            self.custom_period_row.setVisible(False)
            self.custom_period_label.setVisible(False)
        self._refresh_heat_factor_details()
        self._refresh_fuel_defaults()
        self._refresh_energy_parameters()

    def _period(self) -> AccountingPeriod:
        year = self.period_year.value()
        index = self.period_type.currentIndex()
        if index == 0:
            return AccountingPeriod(PeriodType.ANNUAL, date(year, 1, 1), date(year, 12, 31))
        if 1 <= index <= 12:
            month = index
            import calendar
            return AccountingPeriod(PeriodType.MONTHLY, date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]))
        return AccountingPeriod(
            PeriodType.CUSTOM,
            self.period_start.date().toPython(),
            self.period_end.date().toPython(),
        )

    def _source_states(self) -> tuple[EmissionSourceState, ...]:
        statuses = {
            source_id: _enum(combo.currentData(), EmissionSourceStatus)
            for source_id, combo in self._source_statuses.items()
        }
        direction_sources = {
            ("electricity", "purchased_electricity"): "CAR-SRC-PURCHASED-ELECTRICITY-001",
            ("electricity", "exported_electricity"): "CAR-SRC-EXPORTED-ELECTRICITY-001",
            ("heat", "purchased_heat"): "CAR-SRC-PURCHASED-HEAT-001",
            ("heat", "exported_heat"): "CAR-SRC-EXPORTED-HEAT-001",
        }
        active_directions: set[tuple[str, str]] = set()
        for family, rows in self._energy_family_rows.items():
            for row in rows:
                if family == "electricity":
                    kind = str(row.kind.currentData())
                    attribute = row.attribute.currentData()
                    if kind == "purchased_electricity" and attribute == "SELF_CONSUMED_EXCLUDED":
                        continue
                    has_partial_input = (
                        bool(row.amount.text().strip())
                        or kind == "exported_electricity"
                        or attribute != ElectricityAttribute.ORDINARY
                        or row.factor_mode.currentData() == "MANUAL"
                        or bool(row.manual_factor.text().strip())
                        or bool(row.electricity_source.text().strip())
                    )
                else:
                    kind = str(row.kind.currentData())
                    try:
                        steam_kind = _enum(row.heat_kind.currentData(), SteamKind)
                    except (TypeError, ValueError):
                        steam_kind = SteamKind.SATURATED
                    try:
                        factor_mode = _enum(row.heat_factor_mode.currentData(), HeatFactorMode)
                    except (TypeError, ValueError):
                        factor_mode = HeatFactorMode.STANDARD_DEFAULT
                    has_partial_input = (
                        bool(row.amount.text().strip())
                        or kind == "exported_heat"
                        or bool(row.pressure.text().strip())
                        or bool(row.temperature.text().strip())
                        or bool(row.enthalpy.text().strip())
                        or row.enthalpy_mode.currentData() == "MANUAL"
                        or steam_kind is SteamKind.SUPERHEATED
                        or factor_mode is HeatFactorMode.MEASURED
                        or bool(row.measured_heat_factor.text().strip())
                        or bool(row.heat_source.text().strip())
                    )
                if has_partial_input:
                    active_directions.add((family, kind))
        for direction, source_id in direction_sources.items():
            if statuses.get(source_id) is EmissionSourceStatus.INVOLVED and direction not in active_directions:
                statuses[source_id] = EmissionSourceStatus.NOT_INVOLVED
        return tuple(EmissionSourceState(source_id, status) for source_id, status in statuses.items())

    def _source_is_enabled(self, source_id: str) -> bool:
        combo = self._source_statuses[source_id]
        return _enum(combo.currentData(), EmissionSourceStatus) is EmissionSourceStatus.INVOLVED

    def _source_id_for_problem_field(self, field_id: str | None) -> str | None:
        """Map an existing Domain problem field to a Presentation source card.

        This is ownership metadata for the UI only.  It does not decide whether
        a problem exists or reproduce any Domain validation rule.  Dynamic line
        IDs are resolved from the current page input so errors such as
        ``heat-1`` remain attributable to the correct card.
        """

        if not field_id:
            return None
        source_ids = tuple(self._source_cards)
        for source_id in source_ids:
            if field_id == source_id or field_id.startswith(f"{source_id}."):
                return source_id

        dynamic_field_owners: dict[str, str] = {}
        process_owners = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
            "fume": "CAR-SRC-FUME-INCINERATION-001",
            "fgd": "CAR-SRC-FGD-001",
        }
        for prefix, source_id in process_owners.items():
            for row in self._process_rows.get(prefix, ()):
                instance_id = str(row.get("instance_id", ""))
                if instance_id and instance_id in field_id:
                    return source_id
        for row in self._energy_rows:
            line_id = row.line_id.text().strip()
            if not line_id:
                continue
            kind = row.kind.currentData()
            if kind == "exported_electricity":
                dynamic_field_owners[line_id] = "CAR-SRC-EXPORTED-ELECTRICITY-001"
            elif kind == "exported_heat":
                dynamic_field_owners[line_id] = "CAR-SRC-EXPORTED-HEAT-001"
            elif row.family == "heat":
                dynamic_field_owners[line_id] = "CAR-SRC-PURCHASED-HEAT-001"
            else:
                dynamic_field_owners[line_id] = "CAR-SRC-PURCHASED-ELECTRICITY-001"
        for row in self._electricity_rows:
            detail_id = row.detail_id.text().strip()
            if detail_id:
                dynamic_field_owners[detail_id] = "CAR-SRC-PURCHASED-ELECTRICITY-001"
        for row in self._output_electricity_rows:
            line_id = _value(row.get("id"))
            if line_id:
                dynamic_field_owners[line_id] = "CAR-SRC-EXPORTED-ELECTRICITY-001"
        for prefix, source_id in (("heat", "CAR-SRC-PURCHASED-HEAT-001"), ("exported_heat", "CAR-SRC-EXPORTED-HEAT-001")):
            for row in self._heat_rows[prefix]:
                line_id = _value(row.get("id"))
                if line_id:
                    dynamic_field_owners[line_id] = source_id
        for field_key, source_id, default_id in (
            ("heat_id", "CAR-SRC-PURCHASED-HEAT-001", "heat-1"),
            ("exported_electricity_id", "CAR-SRC-EXPORTED-ELECTRICITY-001", "exported-electricity-1"),
            ("exported_heat_id", "CAR-SRC-EXPORTED-HEAT-001", "exported-heat-1"),
        ):
            if self._field_has_value(f"{field_key}") or self._field_has_value(f"{field_key.replace('_id', '_amount')}"):
                dynamic_field_owners[_value(self._fields[field_key]) or default_id] = source_id

        for dynamic_id, source_id in dynamic_field_owners.items():
            if field_id == dynamic_id or field_id.startswith(f"{dynamic_id}."):
                return source_id
            if source_id in {
                "CAR-SRC-PURCHASED-HEAT-001",
                "CAR-SRC-EXPORTED-HEAT-001",
            } and field_id.startswith(f"CAR-FLD-HEAT-{dynamic_id}-"):
                return source_id

        field_prefix_owners = (
            ("CAR-FLD-F01-", "CAR-SRC-FUEL-001"),
            ("CAR-FLD-P01-", "CAR-SRC-CALCINATION-001"),
            ("CAR-FLD-P02-", "CAR-SRC-BAKING-001"),
            ("CAR-FLD-P03-", "CAR-SRC-GRAPHITIZATION-001"),
            ("CAR-FLD-P04A-", "CAR-SRC-FUME-INCINERATION-001"),
            ("CAR-FLD-P04B-", "CAR-SRC-FGD-001"),
            ("CAR-FLD-PWR-PURCHASED-", "CAR-SRC-PURCHASED-ELECTRICITY-001"),
            ("CAR-FLD-POWER-EXPORTED-", "CAR-SRC-EXPORTED-ELECTRICITY-001"),
            ("CAR-FLD-HEAT-PURCHASED-", "CAR-SRC-PURCHASED-HEAT-001"),
            ("CAR-FLD-HEAT-EXPORTED-", "CAR-SRC-EXPORTED-HEAT-001"),
        )
        return next((source_id for prefix, source_id in field_prefix_owners if field_id.startswith(prefix)), None)

    def _source_ids_for_domain_errors(self, problems: tuple[object, ...]) -> set[str]:
        return {
            source_id
            for problem in problems
            if getattr(getattr(problem, "level", None), "value", None) == "ERROR"
            for source_id in (self._source_id_for_problem_field(getattr(problem, "field_id", None)),)
            if source_id is not None
        }

    @staticmethod
    def _input_has_value(widget: QWidget | None) -> bool:
        return isinstance(widget, QLineEdit) and bool(widget.text().strip())

    def _field_has_value(self, key: str) -> bool:
        return self._input_has_value(self._fields.get(key))

    def _field_has_error(self, key: str) -> bool:
        widget = self._fields.get(key)
        if not isinstance(widget, QLineEdit) or not widget.text().strip():
            return False
        return not widget.hasAcceptableInput()

    def _process_card_profile(self, prefix: str, fields: tuple[str, ...]) -> tuple[bool, bool, bool]:
        active = 0
        all_complete = True
        any_invalid = False
        for row in self._process_rows.get(prefix, ()):
            row_fields = row.get("fields", {})
            if prefix == "fgd":
                components = row.get("components", [])
                assert isinstance(components, list)
                active_components = [
                    component for component in components
                    if any(self._input_has_value(component.get(field)) for field in ("cal", "i", "ef1", "tr"))
                    or (
                        isinstance(component.get("carbonate_type"), QComboBox)
                        and bool(component["carbonate_type"].currentText().strip())
                        and component["carbonate_type"].currentText().strip() != "未选择碳酸盐种类"
                    )
                ]
                if not active_components:
                    continue
                active += 1
                for component in active_components:
                    amount = component.get("cal")
                    factor = component.get("ef1")
                    selector = component.get("carbonate_type")
                    source_ref = component.get("factor_source_reference")
                    carbonate_text = selector.currentText().strip() if isinstance(selector, QComboBox) else ""
                    option = self._carbonate_option_for_text(carbonate_text)
                    catalog_selected = (
                        option is not None
                        and component.get("factor_mode") == "CATALOG"
                        and component.get("catalog_factor_id") == option.factor.factor_id
                    )
                    type_or_factor = (
                        (option is not None and (catalog_selected or self._input_has_value(factor)))
                        or bool(carbonate_text and self._input_has_value(factor))
                    )
                    fields_complete = self._input_has_value(amount) and type_or_factor
                    fields_invalid = any(
                        isinstance(component.get(key), QLineEdit)
                        and component[key].text().strip()
                        and not component[key].hasAcceptableInput()
                        for key in ("cal", "i", "ef1", "tr")
                    )
                    all_complete = all_complete and fields_complete
                    any_invalid = any_invalid or fields_invalid
                continue
            assert isinstance(row_fields, dict)
            material_rows = self._material_inputs(row) if prefix in _PROCESS_MATERIAL_ROLES else ()
            material_active = any(
                any(value is not None and str(value).strip() for value in (
                    line.name, line.mass_t, line.fixed_carbon_percent, line.volatile_matter_percent,
                ))
                for line in material_rows
            )
            if material_active:
                normalized = normalize_material_inputs(prefix, material_rows, policy=self.calculator.policy)
                active += 1
                all_complete = all_complete and not normalized.problems
                any_invalid = any_invalid or bool(normalized.problems)
                continue
            controls_key = str(row.get("controls_key", prefix))
            present_fields = [self._input_has_value(row_fields.get(field)) for field in fields]
            if not any(present_fields):
                continue
            active += 1
            row_complete = all(present_fields)
            row_invalid = any(
                isinstance(row_fields.get(field), QLineEdit)
                and row_fields[field].text().strip()
                and not row_fields[field].hasAcceptableInput()
                for field in fields
            )
            controls = self._material_controls.get(controls_key)
            if controls is not None:
                basis_keys = ("mass_basis", "composition_basis", "normalized_basis")
                component_keys = ("fixed_carbon_component_kind", "volatile_matter_component_kind")
                basis_defaults = {key: MaterialBasis.RECEIVED for key in basis_keys}
                component_defaults = {
                    "fixed_carbon_component_kind": MaterialComponentKind.FIXED_CARBON,
                    "volatile_matter_component_kind": MaterialComponentKind.VOLATILE_MATTER,
                }
                row_complete = row_complete and all(
                    (
                        self._material_basis_value(controls, key, basis_defaults[key])
                        if key in basis_defaults
                        else self._material_component_value(controls, key, component_defaults[key])
                    ) is not None
                    for key in basis_keys + component_keys
                )
            all_complete = all_complete and row_complete
            any_invalid = any_invalid or row_invalid
        return active > 0, active > 0 and all_complete, any_invalid

    def _derive_source_card_state(self, source_id: str) -> tuple[SourceCardPresentationState, str]:
        status = _enum(self._source_statuses[source_id].currentData(), EmissionSourceStatus)
        if status is EmissionSourceStatus.NOT_INVOLVED:
            return SourceCardPresentationState.NOT_INVOLVED, "未启用"
        if status is EmissionSourceStatus.UNCONFIRMED:
            return SourceCardPresentationState.UNCONFIRMED, "待确认"

        present = False
        complete = False
        invalid = False
        summary = "尚未录入活动数据"
        if source_id == "CAR-SRC-FUEL-001":
            active_rows = [row for row in self._fuel_rows if row.activity.text().strip()]
            present = bool(active_rows)
            row_ready: list[bool] = []
            row_invalid: list[bool] = []
            for row in active_rows:
                direct = row.carbon_basis.currentData() == "DIRECT"
                carbon_edit = row.carbon_direct if direct else row.carbon
                carbon_ready = bool(carbon_edit.text().strip()) and carbon_edit.hasAcceptableInput()
                try:
                    path = _enum(row.path.currentData(), FuelPath)
                except (TypeError, ValueError):
                    path = FuelPath.MASS
                if not direct and path is not FuelPath.HEAT:
                    lhv_ready = bool(row.lower_heating_value.text().strip()) and row.lower_heating_value.hasAcceptableInput()
                else:
                    lhv_ready = True
                oxidation_ready = bool(row.oxidation.text().strip()) and row.oxidation.hasAcceptableInput()
                row_ready.append(bool(row.fuel_type.currentText().strip()) and carbon_ready and lhv_ready and oxidation_ready)
                row_invalid.append(
                    not row.activity.hasAcceptableInput()
                    or bool(carbon_edit.text().strip() and not carbon_edit.hasAcceptableInput())
                    or bool(row.lower_heating_value.text().strip() and not row.lower_heating_value.hasAcceptableInput())
                    or bool(row.oxidation.text().strip() and not row.oxidation.hasAcceptableInput())
                )
            complete = present and all(row_ready)
            invalid = any(row_invalid)
            summary = f"{len(active_rows)} 条燃料明细" if present else "尚未录入燃料"
        elif source_id in {
            "CAR-SRC-CALCINATION-001",
            "CAR-SRC-BAKING-001",
            "CAR-SRC-GRAPHITIZATION-001",
            "CAR-SRC-FUME-INCINERATION-001",
            "CAR-SRC-FGD-001",
        }:
            process_by_source = {
                "CAR-SRC-CALCINATION-001": ("calcination", ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c")),
                "CAR-SRC-BAKING-001": ("baking", ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar")),
                "CAR-SRC-GRAPHITIZATION-001": ("graphitization", ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar")),
                "CAR-SRC-FUME-INCINERATION-001": ("fume", ("q", "qvar", "hm", "fch", "fox", "duration")),
                "CAR-SRC-FGD-001": ("fgd", ("cal", "i", "ef1", "tr")),
            }
            prefix, fields = process_by_source[source_id]
            present, complete, invalid = self._process_card_profile(prefix, fields)
            summary = f"{len(self._process_rows[prefix])} 条过程实例 · 已录入活动数据" if present else "尚未录入活动数据"
        elif source_id == "CAR-SRC-PURCHASED-ELECTRICITY-001":
            active_rows = [
                row for row in self._energy_family_rows.get("electricity", ())
                if row.kind.currentData() == "purchased_electricity"
                and row.attribute.currentData() != "SELF_CONSUMED_EXCLUDED"
                and (
                    bool(row.amount.text().strip())
                    or row.attribute.currentData() != ElectricityAttribute.ORDINARY
                    or row.factor_mode.currentData() == "MANUAL"
                    or bool(row.manual_factor.text().strip())
                    or bool(row.electricity_source.text().strip())
                )
            ]
            present = bool(active_rows)
            complete = present and all(
                bool(row.amount.text().strip())
                and row.amount.hasAcceptableInput()
                and self._electricity_resolution_states.get(row.line_id.text().strip()) == "RESOLVED"
                for row in active_rows
            )
            invalid = any(
                (bool(row.amount.text().strip()) and not row.amount.hasAcceptableInput())
                or self._electricity_resolution_states.get(row.line_id.text().strip()) in {"BLOCKED", "DELEGATED", "ERROR"}
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条电力明细" if active_rows else "尚未录入电力明细"
        elif source_id == "CAR-SRC-PURCHASED-HEAT-001":
            active_rows = [
                row for row in self._energy_family_rows.get("heat", ())
                if row.kind.currentData() == "purchased_heat"
                and (
                    bool(row.amount.text().strip())
                    or bool(row.pressure.text().strip())
                    or bool(row.temperature.text().strip())
                    or bool(row.enthalpy.text().strip())
                    or row.enthalpy_mode.currentData() == "MANUAL"
                    or row.heat_kind.currentData() == SteamKind.SUPERHEATED
                    or _enum(row.heat_factor_mode.currentData(), HeatFactorMode) is HeatFactorMode.MEASURED
                    or bool(row.measured_heat_factor.text().strip())
                    or bool(row.heat_source.text().strip())
                )
            ]
            present = bool(active_rows)
            complete = present and all(
                bool(row.amount.text().strip())
                and row.amount.hasAcceptableInput()
                and self._unified_heat_row_profile_complete(row)
                for row in active_rows
            )
            invalid = any(
                (bool(row.amount.text().strip()) and not row.amount.hasAcceptableInput())
                or not self._unified_heat_row_profile_complete(row)
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条热力来源" if present else "尚未录入热力活动数据"
        elif source_id == "CAR-SRC-EXPORTED-ELECTRICITY-001":
            active_rows = [
                row for row in self._energy_family_rows.get("electricity", ())
                if row.kind.currentData() == "exported_electricity"
            ]
            present = bool(active_rows)
            complete = present and all(
                bool(row.amount.text().strip())
                and row.amount.hasAcceptableInput()
                and (
                    row.factor_mode.currentData() != "MANUAL"
                    or (bool(row.manual_factor.text().strip()) and row.manual_factor.hasAcceptableInput())
                )
                for row in active_rows
            )
            invalid = any(
                (bool(row.amount.text().strip()) and not row.amount.hasAcceptableInput())
                or (row.factor_mode.currentData() == "MANUAL" and bool(row.manual_factor.text().strip()) and not row.manual_factor.hasAcceptableInput())
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条输出电力来源" if active_rows else "尚未录入输出电力"
        elif source_id == "CAR-SRC-EXPORTED-HEAT-001":
            active_rows = [
                row for row in self._energy_family_rows.get("heat", ())
                if row.kind.currentData() == "exported_heat"
                and (
                    bool(row.amount.text().strip())
                    or bool(row.pressure.text().strip())
                    or bool(row.temperature.text().strip())
                    or bool(row.enthalpy.text().strip())
                    or row.enthalpy_mode.currentData() == "MANUAL"
                    or row.heat_kind.currentData() == SteamKind.SUPERHEATED
                    or _enum(row.heat_factor_mode.currentData(), HeatFactorMode) is HeatFactorMode.MEASURED
                    or bool(row.measured_heat_factor.text().strip())
                    or bool(row.heat_source.text().strip())
                )
            ]
            present = bool(active_rows)
            complete = present and all(
                bool(row.amount.text().strip())
                and row.amount.hasAcceptableInput()
                and self._unified_heat_row_profile_complete(row)
                for row in active_rows
            )
            invalid = any(
                (bool(row.amount.text().strip()) and not row.amount.hasAcceptableInput())
                or not self._unified_heat_row_profile_complete(row)
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条输出热力来源" if active_rows else "尚未录入输出热力"

        # A card may only report completed after a real existing validation run
        # has stopped reporting a source-scoped error.  This deliberately
        # consumes Domain feedback instead of reproducing Domain rules here.
        if source_id in self._known_source_errors:
            invalid = True
        if invalid or not present or (present and not complete):
            return SourceCardPresentationState.NEEDS_ATTENTION, f"{summary} · 需要处理"
        if complete:
            return SourceCardPresentationState.COMPLETED, f"{summary} · 已完成"
        return SourceCardPresentationState.NEEDS_ATTENTION, f"{summary} · 需要处理"

    @staticmethod
    def _unified_heat_row_profile_complete(row: _UnifiedEnergyRow) -> bool:
        manual_enthalpy = row.enthalpy_mode.currentData() == "MANUAL"
        try:
            steam_kind = _enum(row.heat_kind.currentData(), SteamKind)
            factor_mode = _enum(row.heat_factor_mode.currentData(), HeatFactorMode)
        except (TypeError, ValueError):
            return False
        if manual_enthalpy:
            enthalpy_ready = bool(row.enthalpy.text().strip()) and row.enthalpy.hasAcceptableInput()
        else:
            enthalpy_ready = bool(row.pressure.text().strip()) and row.pressure.hasAcceptableInput()
            if steam_kind is SteamKind.SUPERHEATED:
                enthalpy_ready = enthalpy_ready and bool(row.temperature.text().strip()) and row.temperature.hasAcceptableInput()
        if factor_mode is HeatFactorMode.MEASURED:
            factor_ready = bool(row.measured_heat_factor.text().strip()) and row.measured_heat_factor.hasAcceptableInput()
        else:
            factor_ready = True
        return enthalpy_ready and factor_ready

    @staticmethod
    def _heat_row_profile_complete(row: dict[str, object]) -> bool:
        enthalpy_mode = row.get("enthalpy_mode")
        manual = isinstance(enthalpy_mode, QComboBox) and enthalpy_mode.currentData() == "MANUAL"
        steam = row.get("steam")
        try:
            steam_kind = _enum(steam.currentData(), SteamKind) if isinstance(steam, QComboBox) else None
        except ValueError:
            steam_kind = None
        is_saturated = steam_kind is SteamKind.SATURATED
        enthalpy_ready = (
            bool(_value(row.get("enthalpy"))) if manual
            else bool(_value(row.get("pressure"))) and (is_saturated or bool(_value(row.get("temperature"))))
        )
        factor_mode = row.get("factor_mode")
        try:
            selected_factor_mode = _enum(factor_mode.currentData(), HeatFactorMode) if isinstance(factor_mode, QComboBox) else None
        except ValueError:
            selected_factor_mode = None
        measured = selected_factor_mode is HeatFactorMode.MEASURED
        factor_ready = bool(_value(row.get("measured"))) if measured else True
        return enthalpy_ready and factor_ready

    def _refresh_source_cards(self, *_args: object) -> None:
        if not self._source_cards or not hasattr(self, "heat_factor_selector"):
            return
        for source_id, card in self._source_cards.items():
            state, summary = self._derive_source_card_state(source_id)
            card.set_presentation_state(state, summary)
            header = card.findChild(QWidget, f"sourceCardHeader_{source_id}")
            if header is not None:
                header.hide()
            card.summary_label.hide()
            card.check_result_label.hide()
            is_energy_adapter = source_id in {
                "CAR-SRC-PURCHASED-ELECTRICITY-001", "CAR-SRC-EXPORTED-ELECTRICITY-001",
                "CAR-SRC-PURCHASED-HEAT-001", "CAR-SRC-EXPORTED-HEAT-001",
            }
            card.setVisible(
                not is_energy_adapter
                and _enum(self._source_statuses[source_id].currentData(), EmissionSourceStatus) is EmissionSourceStatus.INVOLVED
            )
        energy_families = {
            "electricity": ("CAR-SRC-PURCHASED-ELECTRICITY-001", "CAR-SRC-EXPORTED-ELECTRICITY-001"),
            "heat": ("CAR-SRC-PURCHASED-HEAT-001", "CAR-SRC-EXPORTED-HEAT-001"),
        }
        for family, source_ids in energy_families.items():
            card = self._unified_energy_cards.get(family)
            if card is not None:
                card.setVisible(any(self._energy_source_is_enabled(source_id) for source_id in source_ids))
        self._refresh_source_toggle_buttons()
        self._refresh_live_feedback()
        self._schedule_layout_refresh()

    def _refresh_live_feedback(self) -> None:
        """Show the most recent Domain feedback without duplicating its rules."""

        if not hasattr(self, "confirmed_source_count"):
            return
        confirmed = sum(
            _enum(combo.currentData(), EmissionSourceStatus) is EmissionSourceStatus.INVOLVED
            for combo in self._source_statuses.values()
        )
        if self._validation_count_override is not None:
            errors, reminders = self._validation_count_override
        else:
            errors = 0
            reminders = 0
        self.confirmed_source_count.setText(f"已确认排放源：{confirmed}")
        self.error_count.setText(f"错误：{errors}")
        self.reminder_count.setText(f"提醒：{reminders}")
        if errors:
            self.calculation_status_hint.setText(f"未完成：请修正{errors}项问题。点击问题可定位到输入项。")
        elif reminders:
            self.calculation_status_hint.setText(
                f"已生成核算记录，含{reminders}项非致命提醒。"
                if self._calculation_has_result else "仍有待确认或未完成的排放源；可继续填写后计算。"
            )
        elif self._stale_result_notice:
            self.calculation_status_hint.setText("输入已修改，原核算结果已过期；请重新计算，新记录不会覆盖旧记录。")
        elif self._calculation_has_result:
            self.calculation_status_hint.setText("结果已生成；如修改输入，请重新计算以形成新的记录。")
        else:
            self.calculation_status_hint.setText("填写完成后点击“计算排放量”，软件会集中检查并反馈问题。")

    def _fuel_row_uses_standard_defaults(self, row: _FuelRow) -> bool:
        # A supplied enterprise source is an explicit measured-data choice even
        # when its values happen to equal the standard defaults.
        if row.parameter_source == "MEASURED" or row.source_reference.text().strip():
            return False
        factors = self._fuel_default_factors(row)
        if factors is None:
            return False
        lhv_factor, carbon_factor, oxidation_factor = factors
        try:
            lhv = row.lower_heating_value.text().strip()
            carbon = Decimal(row.carbon.text().strip())
            oxidation = ui_to_domain_value(get_field_spec("fuel_oxidation"), row.oxidation.text().strip())
            expected_lhv = "" if lhv_factor is None else str(lhv_factor.value)
            return lhv == expected_lhv and carbon == carbon_factor.value and Decimal(str(oxidation)) == oxidation_factor.value
        except (InvalidOperation, TypeError, ValueError):
            return False

    @staticmethod
    def _fuel_parameter(
        *, row: _FuelRow, source: QComboBox, edit: QLineEdit, suffix: str,
        unit: str, factor: object | None, value: str | Decimal | None,
        source_kind: str | None = None,
    ) -> ParameterValue | None:
        source_kind = source_kind if source_kind is not None else source.currentData()
        if source_kind == "STANDARD_DEFAULT":
            reason = row._default_selection_reasons.get(suffix) or (
                "采用当前核算期经参数解析器选出的 GB/T 32151.34—2024 附录 C.1 缺省值。"
            )
            return CarbonMaterialAccountingPage._parameter_value_from_factor(factor, reason) if factor is not None else None
        if source_kind not in {"CALCULATED", "MEASURED", "USER_DEFINED"} or value is None:
            return None
        reference = row.source_reference.text().strip()
        kind = {
            "CALCULATED": ParameterSourceKind.CALCULATED,
            "MEASURED": ParameterSourceKind.MEASURED,
            "USER_DEFINED": ParameterSourceKind.USER_DEFINED,
        }[str(source_kind)]
        source_name = {
            ParameterSourceKind.CALCULATED: "计算依据",
            ParameterSourceKind.MEASURED: "实测/检测资料",
            ParameterSourceKind.USER_DEFINED: "用户指定来源",
        }[kind]
        return ParameterValue(
            parameter_id=f"enterprise_fuel_{row.row_key}_{suffix}",
            value=value,
            unit=unit,
            source_kind=kind,
            source_id=None,
            source_version=None,
            source_location=f"{source_name}：{reference}" if reference else None,
            selection_reason=f"用户选择{source_name}参数；来源编号：{reference or '未提供'}。",
        )

    def _fuel(self) -> tuple[FuelInput, ...]:
        fuels: list[FuelInput] = []
        for row in self._fuel_rows:
            activity = row.activity.text().strip()
            path = _enum(row.path.currentData(), FuelPath)
            direct = row.carbon_basis.currentData() == "DIRECT"
            defaults = self._fuel_default_factors(row)
            lhv_factor, carbon_factor, oxidation_factor = defaults if defaults is not None else (None, None, None)
            lhv_unit = {FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}[path]
            lhv_value_num = row.lower_heating_value.text().strip() or None
            carbon_edit = row.carbon_direct if direct else row.carbon
            carbon_source = row.direct_carbon_source if direct else row.carbon_source
            carbon_value_num = carbon_edit.text().strip() or None
            oxidation_value_num = _ui_value("fuel_oxidation", row.oxidation)
            carbon_unit = {
                FuelPath.VOLUME: "tC/10^4Nm3",
                FuelPath.MASS: "tC/t",
                FuelPath.HEAT: "tC/GJ",
            }[path] if direct else "tC/GJ"
            lhv_value = self._fuel_parameter(
                row=row, source=row.lhv_source, edit=row.lower_heating_value,
                suffix="lhv", unit=lhv_unit, factor=lhv_factor, value=lhv_value_num,
                source_kind=self._fuel_source_mode(row, "lhv"),
            ) if not direct and path is not FuelPath.HEAT else None
            carbon_value = self._fuel_parameter(
                row=row, source=carbon_source, edit=carbon_edit,
                suffix="direct_carbon" if direct else "carbon",
                unit=carbon_unit,
                factor=None if direct else carbon_factor,
                value=carbon_value_num,
                source_kind=self._fuel_source_mode(row, "direct_carbon" if direct else "carbon"),
            )
            oxidation_value = self._fuel_parameter(
                row=row, source=row.oxidation_source, edit=row.oxidation,
                suffix="oxidation", unit="ratio", factor=oxidation_factor,
                value=Decimal(str(oxidation_value_num)) if oxidation_value_num is not None else None,
                source_kind=self._fuel_source_mode(row, "oxidation"),
            )
            selected_option = self._fuel_option_for_row(row)
            visible_name = row.fuel_type.currentText().strip()
            legacy_name = row.custom_name.text().strip()
            if selected_option is None:
                fuel_type = FuelType.OTHER if visible_name or legacy_name else None
                fuel_label = visible_name or legacy_name or None
            else:
                fuel_type = selected_option.fuel_type
                fuel_label = selected_option.label if fuel_type is None else None
            fuels.append(FuelInput(
                fuel_id=row.internal_id.text().strip() or f"fuel-{row.row_key}",
                path=path,
                activity=activity or None,
                carbon_content=carbon_value,
                oxidation_rate=oxidation_value,
                lower_heating_value=lhv_value,
                fuel_type=fuel_type,
                fuel_label=fuel_label,
            ))
        return tuple(fuels)

    def _process(self, prefix: str, kind, row: dict[str, object] | None = None):
        row = row or (self._process_rows[prefix][0] if self._process_rows[prefix] else None)
        if row is None:
            return None
        instance_id = str(row["instance_id"])
        if prefix == "fgd":
            components: list[CarbonateComponent] = []
            for component in row.get("components", []):
                assert isinstance(component, dict)
                values = {
                    field: _ui_value(f"fgd.{field}", component[field])
                    for field in ("cal", "i", "ef1", "tr")
                }
                selector = component["carbonate_type"]
                source_ref = _value(component["factor_source_reference"])
                carbonate_text = selector.currentText().strip() if isinstance(selector, QComboBox) else ""
                option = self._carbonate_option_for_text(carbonate_text)
                carbonate_type = option.label if option is not None else carbonate_text or None
                ef_text = values["ef1"]
                factor_mode = component.get("factor_mode")
                catalog_selected = (
                    factor_mode == "CATALOG"
                    and option is not None
                    and component.get("catalog_factor_id") == option.factor.factor_id
                )
                if catalog_selected:
                    factor_value = self._parameter_value_from_factor(option.factor, option.selection_reason)
                elif ef_text is not None:
                    source_kind = ParameterSourceKind.MEASURED if factor_mode == "MEASURED" else ParameterSourceKind.USER_DEFINED
                    factor_value = ParameterValue(
                        parameter_id="fgd_carbonate_emission_factor_user",
                        value=ef_text,
                        unit="tCO2/t",
                        source_kind=source_kind,
                        source_id=None,
                        source_version=None,
                        source_location=f"用户来源说明：{source_ref}" if source_ref else None,
                        selection_reason="用户为本组分填写碳酸盐排放因子。",
                    )
                else:
                    factor_value = None

                def fgd_ratio(field: str, parameter_id: str) -> ParameterValue | None:
                    raw = values[field]
                    if raw is None:
                        factor = self._canonical_default_factor(parameter_id)
                        return self._parameter_value_from_factor(
                            factor, "未提供企业实测值，采用经目录审核的标准一般取值。"
                        ) if factor is not None else None
                    return ParameterValue(
                        parameter_id=parameter_id,
                        value=Decimal(str(raw)),
                        unit="ratio",
                        source_kind=ParameterSourceKind.USER_DEFINED,
                        source_id=None,
                        source_version=None,
                        source_location=f"用户来源说明：{source_ref}" if source_ref else None,
                        selection_reason="用户为本组分提供比例参数。",
                    )

                components.append(CarbonateComponent(
                    values["cal"],
                    fgd_ratio("i", "CAR-PAR-P04B-I"),
                    factor_value,
                    fgd_ratio("tr", "CAR-PAR-P04B-TR"),
                    carbonate_type,
                ))
            return kind(components=tuple(components), instance_id=instance_id) if components else None

        field_names = {
            "calcination": ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"),
            "baking": ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"),
            "graphitization": ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"),
            "fume": ("q", "qvar", "hm", "fch", "fox", "duration"),
            "fgd": ("cal", "i", "ef1", "tr"),
        }[prefix]
        widgets = row.get("fields", {})
        assert isinstance(widgets, dict)
        values = {field: _ui_value(f"{prefix}.{field}", widgets[field]) for field in field_names}

        if prefix in _PROCESS_DEFAULT_PARAMETERS:
            default_parameter_id = _PROCESS_DEFAULT_PARAMETERS[prefix][0]
            factor = self._canonical_default_factor(default_parameter_id)
            parameter_name = {"calcination": "k1", "baking": "k2", "graphitization": "k3"}[prefix]
            values[parameter_name] = (
                self._parameter_value_from_factor(factor, "未提供企业实测值，采用GB/T 32151.34—2024标准一般取值。")
                if factor is not None else None
            )
        controls_key = row.get("controls_key", prefix)
        controls = self._material_controls.get(str(controls_key))
        material_lines = self._material_inputs(row) if prefix in _PROCESS_MATERIAL_ROLES else ()
        has_material_input = any(
            any(value is not None and str(value).strip() for value in (
                line.name, line.mass_t, line.fixed_carbon_percent, line.volatile_matter_percent,
            ))
            for line in material_lines
        )
        if has_material_input:
            normalized = normalize_material_inputs(prefix, material_lines, policy=self.calculator.policy)
            for name, value in normalized.values:
                unit = get_field_spec(f"{prefix}.{name}").domain_unit
                if unit:
                    values[name] = InputValue(value, unit)
        if controls is None:
            return kind(
                **values,
                instance_id=instance_id,
                **({"material_rows": material_lines} if has_material_input else {}),
            )
        evidence_reference = _value(controls["evidence_reference"])
        mass_basis = self._material_basis_value(controls, "mass_basis", MaterialBasis.RECEIVED)
        composition_basis = self._material_basis_value(controls, "composition_basis", MaterialBasis.RECEIVED)
        normalized_basis = self._material_basis_value(controls, "normalized_basis", MaterialBasis.RECEIVED)
        fixed_kind = self._material_component_value(
            controls,
            "fixed_carbon_component_kind",
            MaterialComponentKind.FIXED_CARBON,
        )
        volatile_kind = self._material_component_value(
            controls,
            "volatile_matter_component_kind",
            MaterialComponentKind.VOLATILE_MATTER,
        )
        flags = row.get("flags", {})
        assert isinstance(flags, dict)
        optional_flags: dict[str, bool] = {}
        if prefix in {"calcination", "baking"}:
            flag = flags.get("carbon_output_included_in_input")
            optional_flags["carbon_output_included_in_input"] = flag.isChecked() if isinstance(flag, QCheckBox) else False
        elif prefix == "graphitization":
            flag = flags.get("furnace_loss_included")
            optional_flags["furnace_loss_included"] = flag.isChecked() if isinstance(flag, QCheckBox) else False
        return kind(
            **values,
            instance_id=instance_id,
            material_rows=material_lines if has_material_input else None,
            mass_basis=_enum(mass_basis, MaterialBasis),
            composition_basis=_enum(composition_basis, MaterialBasis),
            normalized_basis=_enum(normalized_basis, MaterialBasis),
            fixed_carbon_component_kind=_enum(fixed_kind, MaterialComponentKind),
            volatile_matter_component_kind=_enum(volatile_kind, MaterialComponentKind),
            moisture_evidence=controls["moisture_evidence"].isChecked() and evidence_reference is not None,
            conversion_evidence=controls["conversion_evidence"].isChecked() and evidence_reference is not None,
            **optional_flags,
        )

    def _process_instances(self, prefix: str, kind) -> tuple[object, ...]:
        return tuple(
            item
            for row in self._process_rows[prefix]
            if (item := self._process(prefix, kind, row)) is not None
        )

    def _electricity(self, enterprise_id: str, period: AccountingPeriod, *, render: bool = True) -> tuple[ElectricityConsumptionDetail, ...]:
        details: list[ElectricityConsumptionDetail] = []
        for row in self._energy_family_rows.get("electricity", ()):
            kind = row.kind.currentData()
            if kind != "purchased_electricity":
                continue
            if row.legacy_acquisition_mode is None and row.attribute.currentData() == "SELF_CONSUMED_EXCLUDED":
                continue
            amount = _value(row.amount)
            if amount is None:
                continue
            acquisition = row.legacy_acquisition_mode or ElectricityAcquisitionMode.PURCHASED
            attribute = row.legacy_attribute or _enum(row.attribute.currentData(), ElectricityAttribute)
            region = row.region.currentData() if acquisition is ElectricityAcquisitionMode.PURCHASED and attribute is ElectricityAttribute.ORDINARY else None
            selected_factor_id = None
            selection_reason = None
            factor_override = None
            if acquisition is ElectricityAcquisitionMode.PURCHASED and attribute is ElectricityAttribute.ORDINARY:
                if row.factor_mode.currentData() == "MANUAL":
                    value = row.manual_factor.text().strip()
                    if not value:
                        raise DomainValidationError("请填写本条普通购入电力的手动排放因子，或切换为参数库候选。")
                    parameter_id, unit = self._energy_electricity_parameter_unit(region)
                    factor_override = UserProvidedParameterValue(
                        value=value,
                        unit=unit,
                        source_reference=row.electricity_source.text().strip() or None,
                        selection_reason="在统一本次购电明细中手动填写并采用电力因子。",
                    )
                else:
                    option = row.factor_selector.currentData()
                    factor = getattr(option, "factor", None)
                    if factor is not None:
                        selected_factor_id = factor.factor_id
                        selection_reason = option.selection_reason
            details.append(ElectricityConsumptionDetail(
                detail_id=row.line_id.text().strip(),
                enterprise_id=enterprise_id,
                standard_id=STANDARD_ID,
                accounting_period=period,
                electricity_amount=amount,
                electricity_unit="MWh",
                acquisition_mode=acquisition,
                attribute=attribute,
                proof_type=row.legacy_proof_type or ElectricityProofType.NONE,
                proof_status=row.legacy_proof_status or ElectricityProofStatus.NOT_PROVIDED,
                region=region,
                selected_factor_id=selected_factor_id,
                factor_selection_reason=selection_reason,
                factor_override=factor_override,
            ))
        result = tuple(details)
        if render:
            self._render_electricity_parameter_states(result)
        return result

    def _refresh_electricity_rows(self) -> None:
        try:
            self._electricity("enterprise.current", self._period())
        except (DomainValidationError, InvalidOperation, ValueError) as exc:
            self._electricity_resolution_states.clear()
            for row in self._energy_family_rows.get("electricity", ()):
                if row.kind.currentData() == "purchased_electricity" and row.attribute.currentData() != "SELF_CONSUMED_EXCLUDED" and row.amount.text().strip():
                    self._electricity_resolution_states[row.line_id.text().strip()] = "ERROR"
                    row.status.setText(f"电力因子：需要处理 · {exc}")
            self._refresh_source_cards()

    def _render_electricity_parameter_states(self, details: tuple[ElectricityConsumptionDetail, ...]) -> None:
        self._electricity_resolution_states.clear()
        energy_rows = {
            row.line_id.text().strip(): row for row in self._energy_family_rows.get("electricity", ())
            if row.kind.currentData() == "purchased_electricity" and row.attribute.currentData() != "SELF_CONSUMED_EXCLUDED"
        }
        for row in energy_rows.values():
            row.status.setText("电力因子：待录入")
        if not details:
            return
        if self._parameter_resolver is None:
            for detail in details:
                row = energy_rows.get(detail.detail_id)
                self._electricity_resolution_states[detail.detail_id] = "ERROR"
                if row is not None:
                    row.status.setText("电力因子：当前参数服务不可用")
            return
        try:
            resolutions = self._parameter_resolver.resolve_electricity_details(
                details,
                snapshot_at=datetime.now(timezone.utc),
            )
        except (DomainValidationError, InvalidOperation, KeyError, ValueError) as exc:
            for detail in details:
                row = energy_rows.get(detail.detail_id)
                self._electricity_resolution_states[detail.detail_id] = "ERROR"
                if row is not None:
                    row.status.setText(f"电力因子：暂未确定 · {exc}")
            return
        for resolution in resolutions:
            detail_id = resolution.detail.detail_id
            row = energy_rows.get(detail_id)
            if resolution.route.value == "DELEGATE_DIRECT_FUEL_PATH":
                self._electricity_resolution_states[detail_id] = "DELEGATED"
                if row is not None:
                    row.status.setText("电力因子：自发自用化石能源电力转入直接燃料排放路径")
                continue
            selected = resolution.parameter_resolution.recommended if resolution.parameter_resolution else None
            snapshot = resolution.snapshot
            if selected is not None and snapshot is not None:
                self._electricity_resolution_states[detail_id] = "RESOLVED"
                if row is not None:
                    factor = selected.factor
                    category_value = getattr(selected.category, "value", selected.category)
                    is_user_provided = category_value == "USER_PROVIDED"
                    category = "用户手动填写" if is_user_provided else self.catalog_service.value_category_label(selected.category)
                    display_value = self.calculator.policy.format_for_display(Decimal(str(factor.value)), 2)
                    source_summary = (
                        factor.source_location or ("本次用户填写" if is_user_provided else "来源资料见记录快照")
                    )
                    row.status.setText(
                        f"电力因子：已确定 {display_value} {factor.unit} · {category} · {source_summary}"
                    )
                continue
            self._electricity_resolution_states[detail_id] = "BLOCKED"
            if row is not None:
                problem = resolution.problems[0] if resolution.problems else None
                message = getattr(problem, "message", "当前明细未形成可用参数快照")
                row.status.setText(f"电力因子：需要处理 · {message}")

    def _selected_heat_parameter_value_for(self, selector: QComboBox, reason_widget: QWidget, *, energy_direction: str) -> ParameterValue | None:
        factor_id = selector.currentData()
        if not isinstance(factor_id, str) or factor_id not in self._heat_factor_records:
            return None
        if self._parameter_resolver is None:
            return ParameterValue(
                "unresolved_heat_emission_factor", Decimal("0"), "tCO2/GJ",
                ParameterSourceKind.USER_DEFINED, None, None, None,
                "当前选择的热力参数无法解析，请检查参数服务和来源资料。",
            )

        base_resolution = self._parameter_resolver.resolve(self._heat_resolution_context(energy_direction=energy_direction))
        selected_reason = _value(reason_widget) or ""
        if base_resolution.recommended is not None and base_resolution.recommended.factor_id == factor_id and not base_resolution.blocked:
            resolution = base_resolution
        elif not selected_reason:
            factor_record = self._heat_factor_records.get(factor_id)
            return ParameterValue(
                getattr(factor_record, "parameter_id", "unconfirmed_heat_emission_factor"),
                getattr(factor_record, "value", Decimal("0")),
                _domain_unit(getattr(factor_record, "unit", "tCO2/GJ")),
                _parameter_source_kind(getattr(factor_record, "value_type", ValueType.STANDARD_DEFAULT)),
                None, None, None,
                "选择非推荐热力参数时需要填写采用理由。",
            )
        else:
            resolution = self._parameter_resolver.resolve(
                self._heat_resolution_context(
                    energy_direction=energy_direction,
                    confirmed_factor_id=factor_id,
                    confirmation_reason=selected_reason,
                )
            )
        if resolution.blocked or resolution.recommended is None:
            factor_record = self._heat_factor_records.get(factor_id)
            return ParameterValue(
                getattr(factor_record, "parameter_id", "unresolved_heat_emission_factor"),
                getattr(factor_record, "value", Decimal("0")),
                _domain_unit(getattr(factor_record, "unit", "tCO2/GJ")),
                _parameter_source_kind(getattr(factor_record, "value_type", ValueType.STANDARD_DEFAULT)),
                None, None, None,
                "当前热力参数无法形成可用来源快照，请检查参数资料。",
            )
        factor = resolution.recommended.factor
        return ParameterValue(
            parameter_id=factor.parameter_id,
            value=factor.value,
            unit=_domain_unit(factor.unit),
            source_kind=_parameter_source_kind(factor.value_type),
            source_id=factor.source_id,
            source_version=factor.version,
            source_location=factor.source_location,
            selection_reason=resolution.selection_reason,
            factor_id=factor.factor_id,
            factor_year=factor.factor_year,
        )

    def _heat(self, prefix: str) -> tuple[HeatInput, ...]:
        expected_kind = "purchased_heat" if prefix == "heat" else "exported_heat"
        direction = expected_kind
        result: list[HeatInput] = []
        for row in self._energy_family_rows.get("heat", ()):
            if row.kind.currentData() != expected_kind:
                continue
            amount = _value(row.amount)
            if amount is None:
                continue
            factor_mode = _enum(row.heat_factor_mode.currentData(), HeatFactorMode)
            source_note = row.heat_source.text().strip() or None
            factor: ParameterValue | None = None
            if factor_mode is HeatFactorMode.MEASURED:
                measured = row.measured_heat_factor.text().strip()
                if not measured:
                    raise DomainValidationError("请填写本条热力来源的实测排放因子，或选择标准缺省因子。")
                factor = ParameterValue(
                    "heat_emission_factor_measured",
                    measured,
                    "tCO2/GJ",
                    ParameterSourceKind.MEASURED,
                    source_id=None,
                    source_version=None,
                    source_location=f"实测来源说明：{source_note}" if source_note else None,
                    selection_reason="用户为本条热力来源填写实测排放因子。",
                )
            manual_enthalpy = row.enthalpy_mode.currentData() == "MANUAL"
            steam_kind = _enum(row.heat_kind.currentData(), SteamKind)
            result.append(HeatInput(
                line_id=row.line_id.text().strip(),
                amount=amount,
                enthalpy=_value(row.enthalpy) if manual_enthalpy else None,
                factor=factor,
                unit="t",
                steam_kind=steam_kind,
                pressure_mpa=_value(row.pressure) if not manual_enthalpy else None,
                temperature_c=_value(row.temperature) if steam_kind is SteamKind.SUPERHEATED and not manual_enthalpy else None,
                manual_enthalpy=manual_enthalpy,
                factor_mode=factor_mode,
                factor_source_note=source_note,
                steam_amount_t=InputValue(amount, "t"),
            ))
        return tuple(result)

    def _exported_electricity(self) -> tuple[ElectricityOutputLine, ...]:
        result: list[ElectricityOutputLine] = []
        for row in self._energy_family_rows.get("electricity", ()):
            if row.kind.currentData() != "exported_electricity":
                continue
            amount = _value(row.amount)
            if amount is None:
                continue
            region = row.region.currentData()
            factor_value: ParameterValue | None = None
            if row.factor_mode.currentData() == "MANUAL":
                raw = row.manual_factor.text().strip()
                if not raw:
                    raise DomainValidationError("请填写本条输出电力的手动排放因子，或切换为参数库候选。")
                source_reference = row.electricity_source.text().strip()
                if row.legacy_measured_factor:
                    factor_value = ParameterValue(
                        parameter_id="electricity_emission_factor_measured",
                        value=raw,
                        unit="tCO2/MWh",
                        source_kind=ParameterSourceKind.MEASURED,
                        source_id="USER-EXPORTED-ELECTRICITY-SOURCE" if source_reference else None,
                        source_version="user-input" if source_reference else None,
                        source_location=f"企业实测/检测资料编号：{source_reference}" if source_reference else None,
                        selection_reason=f"逐来源实测排放因子；来源编号：{source_reference or '未提供'}。",
                    )
                else:
                    parameter_id, unit = self._energy_electricity_parameter_unit(region)
                    factor_value = ParameterValue(
                        parameter_id=parameter_id,
                        value=raw,
                        unit=_domain_unit(unit),
                        source_kind=ParameterSourceKind.USER_DEFINED,
                        source_id=None,
                        source_version=None,
                        source_location=source_reference or None,
                        selection_reason="用户手动填写并采用本条输出电力因子。",
                    )
            else:
                option = row.factor_selector.currentData()
                factor = getattr(option, "factor", None)
                if factor is not None:
                    factor_value = self._parameter_value_from_factor(factor, option.selection_reason)
            result.append(ElectricityOutputLine(
                line_id=row.line_id.text().strip(), amount=amount, factor=factor_value,
                region=region,
            ))
        return tuple(result)

    def _input(self, *, increment: bool = True, render_electricity: bool = True) -> CarbonMaterialInput:
        if increment:
            self._calculation_index += 1
        period = self._period()
        enterprise_name = self.enterprise_name.currentText().strip()
        enterprise_id = "enterprise.current"
        return CarbonMaterialInput(
            input_id=f"input.{self._calculation_index}" if increment else "fingerprint",
            enterprise_id=enterprise_id,
            enterprise_name=enterprise_name or None,
            period=period,
            boundary_confirmed=self.boundary_confirmed.isChecked(),
            boundary_component_ids=("main-production-system",),
            other_activity_present=self.other_activity_present.isChecked(),
            transport_present=self.transport_present.isChecked(),
            source_states=self._source_states(),
            fuel_inputs=self._fuel() if self._source_is_enabled("CAR-SRC-FUEL-001") else (),
            calcinations=self._process_instances("calcination", CalcinationInput) if self._source_is_enabled("CAR-SRC-CALCINATION-001") else (),
            bakings=self._process_instances("baking", BakingInput) if self._source_is_enabled("CAR-SRC-BAKING-001") else (),
            graphitizations=self._process_instances("graphitization", GraphitizationInput) if self._source_is_enabled("CAR-SRC-GRAPHITIZATION-001") else (),
            fume_incinerations=self._process_instances("fume", FumeIncinerationInput) if self._source_is_enabled("CAR-SRC-FUME-INCINERATION-001") else (),
            fgd_units=self._process_instances("fgd", FGDInput) if self._source_is_enabled("CAR-SRC-FGD-001") else (),
            electricity_details=self._electricity(enterprise_id, period, render=render_electricity) if self._source_is_enabled("CAR-SRC-PURCHASED-ELECTRICITY-001") else (),
            exported_electricity=self._exported_electricity() if self._source_is_enabled("CAR-SRC-EXPORTED-ELECTRICITY-001") else (),
            purchased_heat=self._heat("heat") if self._source_is_enabled("CAR-SRC-PURCHASED-HEAT-001") else (),
            exported_heat=self._heat("exported_heat") if self._source_is_enabled("CAR-SRC-EXPORTED-HEAT-001") else (),
            reporting_data=self._reporting_data(),
        )

    def _reporting_data(self) -> CarbonReportingData:
        report_values = {
            key: _value(edit)
            for key, edit in self.reporting_fields.items()
        }
        activity_values = {key: _value(edit) for key, edit in self.activity_evidence_fields.items()}
        factor_values = {key: _value(edit) for key, edit in self.factor_evidence_fields.items()}
        activity_has_evidence = any(value for key, value in activity_values.items() if key != "applies_to")
        factor_has_evidence = any(value for key, value in factor_values.items() if key != "applies_to")
        activity: tuple[ActivityDataEvidence, ...] = ()
        if activity_has_evidence:
            activity = (ActivityDataEvidence(
                evidence_id="evidence.activity.shared",
                applies_to=activity_values.get("applies_to") or "本记录所选排放源活动数据",
                source_ids=tuple(source_id for source_id, check in self.activity_evidence_sources.items() if check.isChecked()),
                source_reference=activity_values.get("source_reference"),
                monitoring_location=activity_values.get("monitoring_location"),
                monitoring_method=activity_values.get("monitoring_method"),
                instrument=activity_values.get("instrument"),
                accuracy=activity_values.get("accuracy"),
                recording_frequency=activity_values.get("recording_frequency"),
                acquisition_time=activity_values.get("acquisition_time"),
                note=activity_values.get("note"),
            ),)
        measured: tuple[MeasuredFactorEvidence, ...] = ()
        if factor_has_evidence:
            measured = (MeasuredFactorEvidence(
                evidence_id="evidence.factor.shared",
                applies_to=factor_values.get("applies_to") or "本记录所选排放源的实测/用户指定因子",
                source_ids=tuple(source_id for source_id, check in self.factor_evidence_sources.items() if check.isChecked()),
                source_reference=factor_values.get("source_reference"),
                sampling_method=factor_values.get("sampling_method"),
                sampling_frequency=factor_values.get("sampling_frequency"),
                testing_method=factor_values.get("testing_method"),
                testing_frequency=factor_values.get("testing_frequency"),
                referenced_standard=factor_values.get("referenced_standard"),
                reason=factor_values.get("reason"),
            ),)
        return CarbonReportingData(
            **report_values,
            activity_evidence=activity,
            measured_factor_evidence=measured,
        )

    def _install_dirty_tracking(self) -> None:
        for widget in self.findChildren(QWidget):
            if widget.objectName() in {"showProfessionalDetailsCheckBox", "accountingSourceNavigation"}:
                continue
            self._wire_dirty_tracking(widget)

    def _mark_input_dirty(self, *_args: object) -> None:
        if getattr(self, "_restoring_workspace", False):
            return
        self._input_dirty = True
        self._project_dirty = True
        self._validation_count_override = None
        self._known_source_errors.clear()
        if hasattr(self, "validation_list"):
            self.validation_list.clear()
            self.quality_card.setVisible(False)
            for card in self._source_cards.values():
                card.check_result_label.clear()
        unit = self._unit()
        calculation_stale = unit.result_snapshot is None or self._calculation_result_is_stale(unit)
        self._stale_result_notice = calculation_stale and unit.result_snapshot is not None
        self._calculation_has_result = not calculation_stale
        if hasattr(self, "result_card") and calculation_stale:
            self.result_card.setVisible(False)
            self.process_card.setVisible(False)
            self.result_line_details.setVisible(False)
            self.view_breakdown_button.setText("查看分项结果")
        elif hasattr(self, "result_card"):
            self.report_changes_status.setText("报告资料已修改，需重新计算生成正式记录才能固化这些变化。")
        if calculation_stale and hasattr(self, "report_changes_status"):
            self.report_changes_status.clear()
        self._sync_report_export_gate()
        self._refresh_unit_result_summary()
        self._refresh_live_feedback()

    def _reset_for_new_accounting(self) -> None:
        """Restore every G06 control to the initial new-accounting state."""

        self._calculation_index = 0
        self.enterprise_name.setText("")
        self._refresh_enterprise_candidates()
        self.period_type.setCurrentIndex(0)
        self.period_year.setValue(2025)
        self.period_month.setValue(1)
        self.period_start.setDate(QDate(2025, 1, 1))
        self.period_end.setDate(QDate(2025, 12, 31))
        self.boundary_confirmed.setChecked(True)
        self.other_activity_present.setChecked(False)
        self.transport_present.setChecked(False)
        for combo in self._source_statuses.values():
            combo.setCurrentIndex(0)
        # Remove stale secondary entries so the next form starts with one row.
        for row in tuple(self._fuel_rows[1:]):
            self._remove_fuel_row(row)
        for prefix, rows in self._process_rows.items():
            while len(rows) > 1:
                self._remove_process_row(prefix, str(rows[-1]["instance_id"]))
            for row in rows:
                flags = row.get("flags", {})
                if isinstance(flags, dict):
                    for flag in flags.values():
                        if isinstance(flag, QCheckBox):
                            flag.setChecked(False)
            if prefix == "fgd" and rows:
                components = rows[0].get("components", [])
                if isinstance(components, list):
                    while len(components) > 1:
                        self._remove_fgd_component(rows[0], str(components[-1]["component_id"]))
                    if not components:
                        self._add_fgd_component(rows[0])
        while len(self._output_electricity_rows) > 1:
            widget = self._output_electricity_rows[-1]["widget"]
            if isinstance(widget, QWidget):
                self._remove_output_electricity_row(widget)
        for prefix, rows in self._heat_rows.items():
            while len(rows) > 1:
                widget = rows[-1]["widget"]
                if isinstance(widget, QWidget):
                    self._remove_heat_row(prefix, widget)
        for widget in self._fields.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        for row in self._fuel_rows:
            row.lower_heating_value.clear()
            row.source_reference.clear()
            row.custom_name.clear()
            for combo in (row.lhv_source, row.carbon_source, row.oxidation_source):
                combo.setCurrentIndex(0)
            self._on_fuel_type_changed(row, initialize_defaults=True)
        for edit in (*self.reporting_fields.values(), *self.activity_evidence_fields.values(), *self.factor_evidence_fields.values()):
            edit.clear()
        self.report_data_toggle.setChecked(False)
        for check in (*self.activity_evidence_sources.values(), *self.factor_evidence_sources.values()):
            check.setChecked(False)
        for row in self._output_electricity_rows:
            row["id"].setText("exported-electricity-1")  # type: ignore[union-attr]
            row["factor"].setCurrentIndex(0)  # type: ignore[union-attr]
            row["measured"].clear()  # type: ignore[union-attr]
            row["source"].clear()  # type: ignore[union-attr]
        for prefix, rows in self._heat_rows.items():
            default_id = "heat-1" if prefix == "heat" else "exported-heat-1"
            for row in rows:
                row["id"].setText(default_id)  # type: ignore[union-attr]
                row["factor"].setCurrentIndex(0)  # type: ignore[union-attr]
                row["reason"].clear()  # type: ignore[union-attr]
                row["measured"].clear()  # type: ignore[union-attr]
                row["source"].clear()  # type: ignore[union-attr]
        for controls in self._material_controls.values():
            for key in ("mass_basis", "composition_basis", "normalized_basis", "fixed_carbon_component_kind", "volatile_matter_component_kind"):
                controls[key].setCurrentIndex(0)  # type: ignore[union-attr]
            controls["moisture_evidence"].setChecked(False)  # type: ignore[union-attr]
            controls["conversion_evidence"].setChecked(False)  # type: ignore[union-attr]
            controls["evidence_reference"].clear()  # type: ignore[union-attr]
        self._electricity_resolution_states.clear()
        self._known_source_errors.clear()
        self._validation_count_override = None
        self._calculation_has_result = False
        self._stale_result_notice = False
        self.heat_factor_selection_reason.clear()
        for row in tuple(self._electricity_rows):
            self._remove_electricity_row(row)
        self._add_electricity_row()
        self._restore_unified_energy_rows(self._default_form_state.get("energy_rows", []))
        self.custom_period_row.setVisible(False)
        self.custom_period_label.setVisible(False)
        self._refresh_heat_factor_details()
        self.validation_list.clear()
        self.quality_card.setVisible(False)
        self.process_card.setVisible(False)
        self.result_card.setVisible(False)
        self._latest_record_id = None
        self._latest_record = None
        self._latest_record_fingerprint = None
        self.view_record_button.setEnabled(False)
        self.export_report_button.setEnabled(False)
        self.result_total.setText("未计算")
        self.result_status.setText("核算状态：尚未计算")
        self.report_qualification_status.setText("年度报告资格：尚未计算")
        self.report_changes_status.clear()
        self.result_breakdown.clear()
        self.result_line_details.clear()
        self.result_line_details.setVisible(False)
        self.view_breakdown_button.setText("查看分项结果")
        self.parameter_snapshot_summary.setText("尚未计算，暂无参数快照。")
        self.trace_output.setText("点击“计算排放量”后显示分项计算结果。")
        self.trace_professional_details.clear()
        self.scope_exclusion_notice.hide()
        self._input_dirty = False
        self._refresh_live_feedback()

    def confirm_discard_if_needed(self) -> bool:
        """Compatibility hook; navigation and close retain in-memory input without prompting."""

        return True

    @staticmethod
    def _problem_level_label(problem: object) -> str:
        level = getattr(getattr(problem, "level", None), "value", "ERROR")
        return {
            "ERROR": "错误",
            "WARNING": "提示",
            "INFO": "信息",
        }.get(str(level), "提示")

    @classmethod
    def _sanitize_business_message(cls, message: str) -> str:
        business_message = message.replace(
            "非收到基数据缺少水分/换算证据",
            "非收到基数据缺少数据来源记录或换算依据",
        )
        business_message = business_message.replace("换算证据", "换算依据")
        business_message = business_message.replace("证据", "数据来源或换算依据")
        business_message = business_message.replace("G05", "电力参数规则")
        business_message = business_message.replace("resolver", "参数服务")
        business_message = business_message.replace("candidate", "适用值")
        business_message = _INTERNAL_TOKEN_RE.sub("相关业务项目", business_message)
        business_message = _INTERNAL_VARIABLE_RE.sub("参数规则", business_message)
        return business_message

    def _business_problem_message(self, problem: object) -> str:
        code = str(getattr(problem, "code", ""))
        if code == "CAR-VAL-FACTOR-SOURCE" and getattr(getattr(problem, "level", None), "value", "") == "WARNING":
            return "企业参数来源说明未提供；本次仍按已录入的数值计算，建议补充资料以便追溯。"
        if code == "CAR-VAL-HEAT-FACTOR-DEFAULT":
            factor = self._canonical_default_factor("heat_emission_factor_default")
            if factor is not None:
                value = self.calculator.policy.format_for_display(factor.value, 2)
                return f"当前无法读取热力参数服务；标准缺省值 {value} tCO₂/GJ 暂不可供本次计算使用，请检查参数服务后重试。"
            return "当前无法取得适用的热力标准缺省值，请检查核算期间和标准参数目录，或提供有依据的实测因子。"
        fixed_messages = {
            "CAR-VAL-MATERIAL-BASIS-CONVERSION": "材料数据的口径或换算资料不完整，当前不能直接计算。请补充数据来源、换算依据和报告/台账编号或来源说明。",
            "CAR-VAL-MATERIAL-BASIS-CONSISTENCY": "质量数据和成分含量的数据口径不一致，当前不能直接计算。请统一两项口径并提供换算依据。",
            "CAR-VAL-MATERIAL-COMPONENT-KIND": "固定碳或挥发分字段性质与标准要求不一致，请检查对应字段。",
            "CAR-VAL-BOUNDARY-UNCONFIRMED": "核算边界尚未确认，请确认本次核算边界。",
            "CAR-VAL-OTHER-STANDARD": "发现当前标准未覆盖的其他活动或上下游运输，请改用适用标准核算。",
            "CAR-VAL-STEAM-STATE": "购入热力的蒸汽状态资料不完整，请补充焓值或压力等必要数据。",
            "CAR-VAL-PARAMETER-RESOLVER-MISSING": "暂时无法取得适用的标准参数，请检查参数数据后重试。",
            "GEN-PAR-STANDARD-DEFAULT-MISSING": "当前无法取得适用的标准缺省参数，请检查标准参数目录后重试。",
            "CAR-VAL-PARAMETER-NONNEGATIVE": "含碳量、热值或排放因子不能为负数，请核对录入值和参数来源。",
            "CAR-VAL-PARAMETER-RATIO-RANGE": "比例参数须在0到1之间，请核对录入值。",
            "CAR-VAL-CARBONATE-FACTOR-MISSING": "请选择脱硫剂中的碳酸盐种类，或提供可追溯的排放因子。",
            "CAR-VAL-FACTOR-SOURCE": "参数缺少可核对的来源、版本或条款定位，请补充来源资料。",
            "GEN-VAL-FACTOR-SOURCE": "参数来源资料不完整，请补充来源说明或资料编号。",
            "GEN-VAL-UNIT-INCOMPATIBLE": "录入数值的单位与所需单位不一致，请核对后重试。",
            "CAR-VAL-PERCENT-RANGE": "比例须在0%到100%之间，请核对录入值。",
            "CAR-VAL-FUEL-LHV-NOT-APPLICABLE": "热量路径的活动量已经是热量，不需要低位发热量；请清空低位发热量后重试。",
            "GEN-PAR-NO-APPLICABLE-VALUE": "当前明细没有可用的适用参数，请补充或检查参数资料。",
            "GEN-VAL-REQUIRED-MISSING": "必填信息不完整，请补充后再试。",
        }
        if code in fixed_messages:
            return fixed_messages[code]
        return self._sanitize_business_message(str(getattr(problem, "message", "当前数据需要检查。")))

    def _process_instance_message_prefix(self, problem: object) -> tuple[str, str | None]:
        field_id = str(getattr(problem, "field_id", "") or "")
        code = str(getattr(problem, "code", ""))
        process_labels = {
            "calcination": "煅烧过程",
            "baking": "焙烧/炭化过程",
            "graphitization": "石墨化过程",
            "fume": "烟气焚烧过程",
            "fgd": "烟气脱硫设施",
        }
        field_aliases = {
            "fume": {"Q": "q", "QVAR": "qvar", "HM": "hm", "FCH": "fch", "FOX": "fox", "T": "duration"},
            "fgd": {"CAL": "cal", "I": "i", "EF1": "ef1", "TR": "tr"},
        }
        for prefix, rows in self._process_rows.items():
            for index, row in enumerate(rows, start=1):
                instance_id = str(row.get("instance_id", ""))
                if not instance_id or instance_id not in field_id:
                    continue
                context = f"{process_labels[prefix]} {index}："
                missing_label = None
                if code == "GEN-VAL-REQUIRED-MISSING":
                    field_name = field_id.rsplit("-", 1)[-1]
                    field_name = field_aliases.get(prefix, {}).get(field_name, field_name.lower())
                    try:
                        missing_label = get_field_spec(f"{prefix}.{field_name}").label
                    except KeyError:
                        if prefix == "fgd":
                            missing_label = "碳酸盐组分"
                return context, missing_label
        return "", None

    def _add_validation_problem(self, problem: object, technical_lines: list[str]) -> None:
        level = str(getattr(getattr(problem, "level", None), "value", "ERROR"))
        code = str(getattr(problem, "code", "未提供代码"))
        raw_message = str(getattr(problem, "message", "当前数据需要检查。"))
        field_id = str(getattr(problem, "field_id", "") or "")
        source_id = self._source_id_for_problem_field(field_id)
        source_label = SOURCE_LABELS.get(source_id or "", "核算信息")
        context, missing_label = self._process_instance_message_prefix(problem)
        target_name = self._validation_target_name(field_id, source_id)
        business_message = self._business_problem_message(problem)
        field_label = missing_label or self._validation_field_label(target_name)
        if field_label:
            business_message = f"{field_label}：{business_message}"
        bucket = "必须修正" if level == "ERROR" else "提醒"
        root = self._validation_root(bucket)
        source_item = self._validation_child(root, source_label, ("source", source_id or "general"))
        source_item.setData(0, Qt.ItemDataRole.UserRole + 1, source_id)
        parent = source_item
        if context:
            context_label = context.rstrip("：")
            parent = self._validation_child(source_item, context_label, ("instance", context_label))
        item = QTreeWidgetItem([business_message])
        item.setData(0, Qt.ItemDataRole.UserRole, target_name)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, source_id)
        item.setToolTip(0, "点击定位到需要处理的输入项。" if target_name else "")
        parent.addChild(item)
        for node in (root, source_item, parent):
            self.validation_list.expandItem(node)
        self._update_validation_root_labels()
        technical_lines.append(f"{level}：{raw_message} [{code}]")

    def _validation_root(self, label: str) -> QTreeWidgetItem:
        for index in range(self.validation_list.topLevelItemCount()):
            item = self.validation_list.topLevelItem(index)
            if item.data(0, Qt.ItemDataRole.UserRole + 2) == label:
                return item
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.ItemDataRole.UserRole + 2, label)
        self.validation_list.addTopLevelItem(item)
        return item

    @staticmethod
    def _validation_child(parent: QTreeWidgetItem, label: str, key: tuple[str, str]) -> QTreeWidgetItem:
        for index in range(parent.childCount()):
            item = parent.child(index)
            if item.data(0, Qt.ItemDataRole.UserRole + 2) == key:
                return item
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.ItemDataRole.UserRole + 2, key)
        parent.addChild(item)
        return item

    @classmethod
    def _tree_leaf_count(cls, item: QTreeWidgetItem) -> int:
        if item.childCount() == 0:
            return 1
        return sum(cls._tree_leaf_count(item.child(index)) for index in range(item.childCount()))

    def _update_validation_root_labels(self) -> None:
        for index in range(self.validation_list.topLevelItemCount()):
            root = self.validation_list.topLevelItem(index)
            root_label = str(root.data(0, Qt.ItemDataRole.UserRole + 2))
            root.setText(0, f"{root_label}（{self._tree_leaf_count(root)}）")

    def _validation_field_label(self, target_name: str | None) -> str | None:
        if not target_name:
            return None
        widget = self.findChild(QWidget, target_name)
        business_label = widget.property("businessFieldLabel") if widget is not None else None
        if isinstance(business_label, str):
            return business_label
        key = widget.property("fieldSpecKey") if widget is not None else None
        if isinstance(key, str):
            try:
                return get_field_spec(key).label
            except KeyError:
                return None
        labels = {
            "fuelcustomname": "具体燃料名称",
            "fuelactivity": "活动量",
            "fuelcarbon": "单位含碳量",
            "fueloxidation": "碳氧化率",
            "fuellhv": "低位发热量",
            "electricityamount": "用电量（MWh）",
        }
        return next((label for marker, label in labels.items() if marker in target_name.lower()), None)

    def _validation_target_name(self, field_id: str, source_id: str | None) -> str | None:
        upper = field_id.upper()
        for row in self._fuel_rows:
            fuel_id = row.internal_id.text().strip()
            if fuel_id and fuel_id in field_id:
                for suffix, widget in (
                    ("ACTIVITY", row.activity), ("LHV", row.lower_heating_value),
                    ("CARBON", row.carbon_direct if row.carbon_basis.currentData() == "DIRECT" else row.carbon), ("FOX", row.oxidation),
                    ("FUEL-NAME", row.custom_name),
                ):
                    if upper.endswith(suffix):
                        return widget.objectName()
        process_aliases = {
            "calcination": {},
            "baking": {},
            "graphitization": {},
            "fume": {"Q": "q", "QVAR": "qvar", "HM": "hm", "FCH": "fch", "FOX": "fox", "T": "duration"},
        }
        for prefix in ("calcination", "baking", "graphitization", "fume"):
            for row in self._process_rows[prefix]:
                instance_id = str(row.get("instance_id", ""))
                if instance_id and instance_id in field_id:
                    materials = row.get("materials", [])
                    if isinstance(materials, list):
                        for material in materials:
                            if not isinstance(material, dict):
                                continue
                            material_id = str(material.get("line_id", ""))
                            if not material_id or material_id not in field_id:
                                continue
                            suffix = field_id.rsplit(material_id, 1)[-1].lower()
                            key = next((name for marker, name in (
                                (".fixed_carbon", "fixed_carbon"),
                                (".volatile_matter", "volatile_matter"),
                                (".mass", "mass"),
                                (".name", "name"),
                                (".role", "role"),
                            ) if marker in suffix), None)
                            widget = material.get(key) if key else None
                            if isinstance(widget, QWidget):
                                return widget.objectName()
                    if "material-" in field_id:
                        add_button = self.findChild(QWidget, f"add_{prefix}_material_{instance_id}")
                        if add_button is not None:
                            return add_button.objectName()
                    for key, widget in row.get("fields", {}).items():
                        aliases = process_aliases[prefix]
                        if (upper.endswith(str(key).upper()) or any(
                            alias == upper.rsplit("-", 1)[-1] and actual == key
                            for alias, actual in aliases.items()
                        )) and isinstance(widget, QWidget):
                            return widget.objectName()
        for row in self._process_rows["fgd"]:
            instance_id = str(row.get("instance_id", ""))
            if not instance_id or instance_id not in field_id:
                continue
            suffix = field_id.rsplit(f"{instance_id}-", 1)[-1].split("-")
            components = row.get("components", [])
            if suffix and suffix[0].isdigit() and isinstance(components, list):
                component_index = int(suffix[0])
                if component_index < len(components) and isinstance(components[component_index], dict):
                    component = components[component_index]
                    field_name = suffix[-1].lower()
                    field_map = {"cal": "cal", "i": "i", "ef1": "ef1", "tr": "tr"}
                    widget_key = field_map.get(field_name)
                    selector = component.get("carbonate_type")
                    source_reference = component.get("factor_source_reference")
                    factor_edit = component.get("ef1")
                    if field_name == "ef1" and isinstance(selector, QComboBox) and selector.currentData() is None:
                        return selector.objectName()
                    if field_name == "ef1" and isinstance(factor_edit, QLineEdit) and factor_edit.text().strip() and isinstance(source_reference, QLineEdit) and not source_reference.text().strip():
                        return source_reference.objectName()
                    widget = component.get(widget_key) if widget_key else None
                    if isinstance(widget, QWidget):
                        return widget.objectName()
                    if isinstance(selector, QWidget):
                        return selector.objectName()
            button = self.findChild(QWidget, f"add_fgd_component_{instance_id}")
            if button is not None:
                return button.objectName()
        for row in self._electricity_rows:
            detail_id = row.detail_id.text().strip()
            if detail_id and detail_id in field_id:
                return row.amount.objectName()
        for row in self._output_electricity_rows:
            line_id = _value(row.get("id")) or str(row.get("default_line_id", ""))
            if line_id and line_id in field_id:
                if _value(row.get("measured")) is not None and not _value(row.get("source")):
                    widget = row.get("source")
                    return widget.objectName() if isinstance(widget, QWidget) else None
                widget = row.get("factor")
                if isinstance(widget, QWidget):
                    return widget.objectName()
                widget = row.get("amount")
                return widget.objectName() if isinstance(widget, QWidget) else None
        for prefix, rows in self._heat_rows.items():
            for row in rows:
                line_id = _value(row.get("id")) or str(row.get("default_line_id", ""))
                if line_id and line_id in field_id:
                    if upper.endswith("EF3"):
                        mode = row.get("factor_mode")
                        try:
                            selected_mode = _enum(mode.currentData(), HeatFactorMode) if isinstance(mode, QComboBox) else None
                        except ValueError:
                            selected_mode = None
                        widget = row.get("measured") if selected_mode is HeatFactorMode.MEASURED else mode
                        if isinstance(widget, QWidget):
                            return widget.objectName()
                    for suffix, key in (("AMOUNT", "amount"), ("HM", "enthalpy"), ("PRESSURE", "pressure"), ("TEMPERATURE", "temperature")):
                        widget = row.get(key)
                        if upper.endswith(suffix) and isinstance(widget, QWidget):
                            return widget.objectName()
                    widget = row.get("amount")
                    return widget.objectName() if isinstance(widget, QWidget) else None
        # Static Domain field IDs resolve to the ordinary field widget through
        # its stable field-spec key, without exposing that key to the user.
        tail = upper.rsplit("-", 1)[-1].lower()
        candidates = tuple(self._fields.items())
        for key, widget in candidates:
            if not isinstance(widget, QWidget):
                continue
            spec_key = widget.property("fieldSpecKey")
            if isinstance(spec_key, str) and spec_key.rsplit(".", 1)[-1].lower() == tail:
                return widget.objectName()
        if source_id and source_id in self._source_cards:
            return self._source_cards[source_id].objectName()
        return None

    def _run_calculation(self) -> None:
        self._stale_result_notice = False
        self.validation_list.clear()
        self._known_source_errors.clear()
        self._validation_count_override = None
        self._calculation_has_result = False
        self._latest_record_id = None
        self._latest_record = None
        self._latest_record_fingerprint = None
        self.view_record_button.setEnabled(False)
        self.export_report_button.setEnabled(False)
        self.result_card.setVisible(False)
        self.process_card.setVisible(False)
        self.quality_card.setVisible(False)
        self.result_line_details.setVisible(False)
        self.view_breakdown_button.setText("查看分项结果")
        self.result_total.setText("未生成结果")
        self.result_status.setText("核算状态：尚未生成记录")
        for card in self._source_cards.values():
            card.check_result_label.clear()
        self._refresh_source_cards()
        technical_lines: list[str] = []
        if self.calculation_use_case is None:
            self._show_formal_calculation_error(
                "正式核算服务尚未配置，无法计算并保存核算记录。"
            )
            return
        try:
            outcome = self.calculation_use_case.calculate(self._input())
        except RecordPersistenceError as exc:
            _LOGGER.exception("Formal carbon-accounting record persistence failed: %s", exc)
            self._show_formal_calculation_error(f"未能保存核算记录：{exc}")
            return
        except (DomainValidationError, InvalidOperation, ValueError) as exc:
            raw_message = str(exc)
            _LOGGER.error("Carbon-material calculation input validation failed: %s", raw_message)
            root = self._validation_root("必须修正")
            source = self._validation_child(root, "核算信息", ("source", "general"))
            source.addChild(QTreeWidgetItem([self._sanitize_business_message(raw_message)]))
            self._update_validation_root_labels()
            self.validation_list.expandAll()
            self.quality_card.setVisible(True)
            self._validation_count_override = (1, 0)
            self._refresh_live_feedback()
            self._schedule_layout_refresh()
            QTimer.singleShot(0, self, self._focus_first_error)
            return
        self._known_source_errors = self._source_ids_for_domain_errors(outcome.problems)
        error_count = 0
        reminder_count = 0
        source_problem_counts: dict[str, int] = {}
        for problem in outcome.problems:
            self._add_validation_problem(problem, technical_lines)
            level = str(getattr(getattr(problem, "level", None), "value", "ERROR"))
            if level == "ERROR":
                error_count += 1
            elif level in {"WARNING", "INFO"}:
                reminder_count += 1
            source_id = self._source_id_for_problem_field(getattr(problem, "field_id", None))
            if source_id is not None:
                source_problem_counts[source_id] = source_problem_counts.get(source_id, 0) + 1
        if technical_lines:
            _LOGGER.warning("Carbon-material calculation validation: %s", " | ".join(technical_lines))
        self.quality_card.setVisible(bool(outcome.problems))
        self._validation_count_override = (error_count, reminder_count)
        self._refresh_source_cards()
        for source_id, card in self._source_cards.items():
            count = source_problem_counts.get(source_id, 0)
            card.check_result_label.setText(f"{count} 项待处理" if count else "")
        if outcome.result is None or outcome.blocked:
            self.result_total.setText("未生成结果")
            self.result_status.setText("核算状态：请按上方问题修正后重新计算")
            self.quality_card.setVisible(True)
            if self.validation_list.topLevelItemCount():
                self.validation_list.expandAll()
            self._refresh_live_feedback()
            self._schedule_layout_refresh()
            QTimer.singleShot(0, self, self._focus_first_error)
            return
        if outcome.record is None:
            self._show_formal_calculation_error(
                "未能保存核算记录：当前正式核算服务未返回已保存的核算记录。"
            )
            return
        self._calculation_has_result = True
        self.result_card.setVisible(True)
        self.result_total.setText(
            f"温室气体排放总量：{_display_amount(outcome.result.total_amount, outcome.result.total_unit)}"
        )
        by_id = {line.line_id: line.amount for line in outcome.result.lines}
        status_label = (
            "已完成（含提醒）"
            if outcome.record is not None and outcome.record.status is RecordStatus.COMPLETED_WITH_WARNINGS
            else "已完成"
            if outcome.record is not None
            else "已计算但存在需要处理的问题"
        )
        self.result_status.setText(f"核算状态：{status_label}")
        qualification = outcome.report_qualification
        qualification_text = (
            ("符合年度报告周期要求。" if qualification.eligible else "不符合年度报告周期要求。")
            + qualification.message
            if qualification is not None else "历史信息未保存。"
        )
        self.report_qualification_status.setText(
            "年度报告资格：" + qualification_text
        )
        self.report_changes_status.clear()
        self.result_breakdown.setText(
            f"直接排放量：{_display_amount(by_id.get('CAR-FLD-DIRECT-RESULT', Decimal('0')), outcome.result.total_unit)}；"
            f"购入/输出能源对应的净间接排放量：{_display_amount(by_id.get('CAR-FLD-INDIRECT-RESULT', Decimal('0')), outcome.result.total_unit)}；"
            f"记录：{'已生成不可编辑核算记录' if outcome.record is not None else '未生成记录'}\n"
            "需要查看标准报告资料时，可打开正式核算记录。"
        )
        line_details = []
        for line in outcome.result.lines:
            if line.line_id in {
                "CAR-FLD-DIRECT-RESULT",
                "CAR-FLD-INDIRECT-RESULT",
                "CAR-FLD-TOTAL-RESULT",
            }:
                continue
            source_label = SOURCE_LABELS.get(line.emission_source_id, "其他排放源")
            line_details.append(f"{source_label}：{_display_amount(line.amount, line.unit)}")
        for trace in outcome.traces:
            if trace.formula_id not in {"CAR-FML-PURCHASED-HEAT-001", "CAR-FML-EXPORTED-HEAT-001"}:
                continue
            provenance = dict(trace.provenance)
            used = provenance.get("enthalpy_used_kj_per_kg")
            if used is None:
                continue
            source_label = "购入热力" if trace.formula_id == "CAR-FML-PURCHASED-HEAT-001" else "输出热力"
            used_display = self.calculator.policy.format_for_display(used, 1)
            table = provenance.get("table", "C.4/C.5")
            source = provenance.get("enthalpy_source", "标准表自动确定")
            if source == "用户手动填写":
                description = f"来源：用户手动填写；本次按您填写的 {used_display} kJ/kg 计算。"
                reference = provenance.get("automatic_reference_enthalpy_kj_per_kg")
                if reference is not None:
                    description += f"按当前蒸汽状态依据附录 {table} 计算的参考值为 {self.calculator.policy.format_for_display(reference, 1)} kJ/kg。"
            else:
                description = f"来源：根据 GB/T 32151.34—2024 附录 {table} 自动确定。"
            line_details.append(f"{source_label}蒸汽焓值：{used_display} kJ/kg；{description}")
            warnings = [
                problem.message for problem in outcome.problems
                if problem.code == "CAR-VAL-STEAM-MANUAL-DEVIATION"
                and isinstance(problem.field_id, str)
                and trace.trace_id in problem.field_id
            ]
            line_details.extend(f"提醒：{message}" for message in warnings)
        self.result_line_details.setText(
            "分项结果：\n" + "\n".join(line_details) if line_details else "分项结果：本次没有单独排放源明细。"
        )
        self.parameter_snapshot_summary.setText(f"已形成 {len(outcome.parameter_snapshots)} 条参数快照（只读）。")
        if outcome.record is not None:
            self._input_dirty = False
            self._latest_record_id = outcome.record.record_id
            self._latest_record = outcome.record
            self._latest_record_fingerprint = self._fingerprint_business_input(outcome.input)
            self.view_record_button.setEnabled(True)
            self._refresh_enterprise_candidates()
            self._sync_report_export_gate()
            self.record_created.emit(outcome.record.record_id)
        trace_lines = [
            f"{trace.formula_id}：{trace.substitution} = {_display_amount(trace.amount, 'tCO2')}"
            for trace in outcome.traces
        ]
        self.trace_professional_details.setText("\n".join(trace_lines) if trace_lines else "无可展示计算过程。")
        self.trace_output.setText("计算追溯和参数快照已保存在本次正式核算记录中。")
        if outcome.record is not None:
            state = self._capture_form_state()
            fingerprint = self._fingerprint_business_input(outcome.input)
            calculation_fingerprint = self._fingerprint_business_input(outcome.input, scope="calculation")
            reporting_fingerprint = self._fingerprint_business_input(outcome.input, scope="reporting")
            active = self._unit()
            result_snapshot = {
                "total": str(outcome.result.total_amount),
                "total_display": _display_amount(outcome.result.total_amount, outcome.result.total_unit),
                "status_label": status_label,
                "breakdown": self.result_breakdown.text(),
                "line_details": self.result_line_details.text(),
                "trace_details": self.trace_professional_details.text(),
                "parameter_snapshot_summary": self.parameter_snapshot_summary.text(),
                "record_id": outcome.record.record_id,
                "report_qualification": qualification_text,
                "calculation_fingerprint": calculation_fingerprint,
                "reporting_fingerprint": reporting_fingerprint,
            }
            updated_unit = replace(
                active,
                form_state=state,
                result_snapshot=result_snapshot,
                record_ids=(*active.record_ids, outcome.record.record_id),
                input_fingerprint=fingerprint,
            )
            units = list(self._workspace.units)
            units[self._active_unit_index] = updated_unit
            self._workspace = replace(self._workspace, units=tuple(units))
            self._project_dirty = True
            self._refresh_unit_result_summary()
            if self.project_service is not None:
                try:
                    association_workspace = self._workspace_for_record_link(updated_unit)
                    self.project_service.save_after_record(
                        association_workspace,
                        outcome.record.record_id,
                    )
                except Exception as exc:
                    if isinstance(exc, ProjectRecordAssociationError):
                        if exc.association_saved:
                            status = "核算记录已生成并关联到项目，但恢复标记未能清理，待再次检查。"
                            recovery_detail = "项目关联已经保存，但恢复标记清理失败；标记仍待恢复流程处理。"
                        elif exc.recovery_pending:
                            status = "核算记录已生成；项目关联未保存，但恢复标记已保存，可重新打开软件继续恢复。"
                            recovery_detail = "项目关联尚未保存，恢复标记已经写入；重新打开软件可继续恢复。"
                        else:
                            status = "核算记录已生成；项目关联未保存，恢复标记未写入。请点击“保存项目”保存当前关联。"
                            recovery_detail = "项目关联尚未保存，恢复标记写入失败；请点击“保存项目”保存当前关联。"
                    else:
                        status = "核算记录已生成，但项目关联处理失败；请查看详情并核对项目保存状态。"
                        recovery_detail = "无法确认项目恢复标记状态；请核对项目保存状态。"
                    self.project_save_status.setText(status)
                    QMessageBox.critical(
                        self,
                        "核算记录关联失败",
                        "成功核算记录已经安全保存在记录库中，不会撤销或删除。"
                        f"{recovery_detail}\n\n"
                        f"详细信息：{exc}",
                    )
                else:
                    self._project_dirty = association_workspace != self._workspace
                    self.project_save_status.setText(
                        "核算记录已生成并关联到当前核算单元。"
                        + ("其他未保存的项目修改仍需点击“保存项目”。" if self._project_dirty else "")
                    )
                    self._refresh_saved_projects()
            else:
                self.project_save_status.setText("核算记录已生成；当前项目未配置持久化服务。")
            self._refresh_unit_result_summary()
        QTimer.singleShot(0, self, lambda: self._scroll_to_widget(self.result_card))
        self._refresh_live_feedback()
        self._schedule_layout_refresh()

    def _show_formal_calculation_error(self, message: str) -> None:
        """Show a workflow or persistence failure without presenting a result."""

        root = self._validation_root("未能保存核算记录")
        section = self._validation_child(root, "核算记录", ("record", "persistence"))
        section.addChild(QTreeWidgetItem([self._sanitize_business_message(message)]))
        self._update_validation_root_labels()
        self.validation_list.expandAll()
        self.result_total.setText("未生成结果")
        self.result_status.setText("核算状态：未能保存核算记录")
        self.project_save_status.setText("未建立新的项目关联。")
        self.quality_card.setVisible(True)
        self._validation_count_override = (1, 0)
        self._refresh_live_feedback()
        self._schedule_layout_refresh()


NewAccountingPage = CarbonMaterialAccountingPage


__all__ = ["CarbonMaterialAccountingPage", "NewAccountingPage"]
