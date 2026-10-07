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
from packages.application.project_workspaces import (
    AccountingUnitType,
    AccountingUnitWorkspace,
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
from packages.core.parameter_resolution import ParameterResolutionContext
from packages.core.repositories import RecordRepository

from .pages import BasePage, Navigate, _card
from .field_specs import SOURCE_LABELS, get_field_spec, ui_to_domain_value
from .source_cards import SourceCard, SourceCardPresentationState
from .typed_inputs import NumericLineEdit, create_read_only_parameter, create_typed_input
from .view_models import AppRoute


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


class _FuelRow(QWidget):
    def __init__(self, index: int, remove: Callable[[QWidget], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"fuelRow{index}")
        self.row_key = uuid4().hex
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.internal_id = QLineEdit(f"fuel-{self.row_key}", self)
        self.internal_id.setObjectName("fuelIdInput" if index == 1 else f"fuelIdInput{index}")
        self.internal_id.hide()
        self.fuel_type = create_typed_input(self, get_field_spec("fuel_type"), f"fuelType{index}")
        for label, value in _FUEL_TYPE_OPTIONS:
            self.fuel_type.addItem(label, value)
        self.path = create_typed_input(self, get_field_spec("fuel_path"), f"fuelPathInput{index}")
        for value, label in ((FuelPath.VOLUME, "体积"), (FuelPath.MASS, "质量"), (FuelPath.HEAT, "热量（历史路径）")):
            self.path.addItem(label, value)
        path_item = self.path.model().item(2) if hasattr(self.path.model(), "item") else None
        if path_item is not None:
            path_item.setEnabled(False)
        self.custom_name = QLineEdit(self)
        self.custom_name.setObjectName(f"fuelCustomName{index}")
        self.custom_name.setPlaceholderText("填写具体燃料名称或煤种")
        self.activity = create_typed_input(self, get_field_spec("fuel_activity"), f"fuelActivityInput{index}")
        self.carbon = create_typed_input(self, get_field_spec("fuel_carbon"), f"fuelCarbonInput{index}")
        self.oxidation = create_typed_input(self, get_field_spec("fuel_oxidation"), f"fuelOxidationInput{index}")
        self.lower_heating_value = create_typed_input(
            self,
            get_field_spec("fuel_lhv"),
            f"fuelLhvInput{index}",
        )
        self.source_reference = create_typed_input(
            self,
            get_field_spec("fuel_source_reference"),
            f"fuelSourceReference{index}",
        )
        self.source_reference.setPlaceholderText("实测/检测资料编号")
        self.lhv_source = self._source_combo(index, "lhv")
        self.carbon_source = self._source_combo(index, "carbon")
        self.oxidation_source = self._source_combo(index, "oxidation")
        self.lhv_control = self._parameter_control(self.lhv_source, self.lower_heating_value)
        self.carbon_control = self._parameter_control(self.carbon_source, self.carbon)
        self.oxidation_control = self._parameter_control(self.oxidation_source, self.oxidation)
        self.parameter_summary = QLabel("参数来源待确定", self)
        self.parameter_summary.setObjectName(f"fuelParameterSummary{index}")
        self.parameter_summary.setWordWrap(True)
        self.remove_button = QPushButton("删除本条燃料", self)
        self.remove_button.setObjectName(f"removeFuelButton{index}")
        self.remove_button.clicked.connect(lambda: remove(self))
        self.fuel_type_label = QLabel("燃料种类", self)
        self.path_label = QLabel("计量方式", self)
        self.custom_name_label = QLabel("具体名称", self)
        self.activity_label = QLabel("活动量", self)
        self.lhv_label = QLabel("低位发热量", self)
        self.carbon_label = QLabel("单位含碳量", self)
        self.oxidation_label = QLabel("碳氧化率（%）", self)
        self.source_reference_label = QLabel("来源说明/编号", self)
        layout.addRow(self.fuel_type_label, self.fuel_type)
        layout.addRow(self.path_label, self.path)
        layout.addRow(self.custom_name_label, self.custom_name)
        layout.addRow(self.activity_label, self.activity)
        layout.addRow(self.lhv_label, self.lhv_control)
        layout.addRow(self.carbon_label, self.carbon_control)
        layout.addRow(self.oxidation_label, self.oxidation_control)
        layout.addRow(self.source_reference_label, self.source_reference)
        footer = QWidget(self)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addWidget(self.parameter_summary, 1)
        footer_layout.addWidget(self.remove_button)
        layout.addRow(footer)
        self._update_custom_name_visibility()
        self._last_default_values: tuple[str, str, str] | None = None
        self.parameter_source = "AUTO"

    @staticmethod
    def _source_combo(index: int, key: str) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName(f"fuel{key.title()}Source{index}")
        combo.addItem("请选择来源", None)
        combo.addItem("缺省值", "STANDARD_DEFAULT")
        combo.addItem("计算值", "CALCULATED")
        combo.addItem("实测值", "MEASURED")
        combo.setMinimumWidth(94)
        return combo

    @staticmethod
    def _parameter_control(source: QComboBox, edit: QWidget) -> QWidget:
        control = QWidget()
        row = QHBoxLayout(control)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(source)
        row.addWidget(edit, 1)
        return control

    def _update_custom_name_visibility(self) -> None:
        value = self.fuel_type.currentData()
        needs_name = value in {FuelType.COAL, FuelType.OTHER}
        self.custom_name_label.setVisible(needs_name)
        self.custom_name.setVisible(needs_name)


class CarbonMaterialAccountingPage(BasePage):
    """Long, scrollable G06 work sheet for the only implemented industry standard."""

    record_created = Signal(str)
    record_requested = Signal(str)

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
        self._electricity_rows: list[_ElectricityRow] = []
        self._electricity_row_serial = 0
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

    def set_standard_id(self, standard_id: str) -> None:
        self.standard_id = standard_id
        self.standard_id_label.setText("GB/T 32151.34—2024《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》")
        if hasattr(self, "heat_factor_selector"):
            self._refresh_heat_factor_details()

    def _build_page(self) -> None:
        self.add_header("新建核算", "GB/T 32151.34-2024 炭素材料生产企业手工核算；成功计算后立即形成不可编辑核算记录。")

        identity, identity_layout = _card("01 核算信息与核算边界", self)
        form = QFormLayout()
        self.standard_id_label = QLabel("GB/T 32151.34—2024《温室气体排放核算与报告要求 第34部分：炭素材料生产企业》", identity)
        self.standard_id_label.setObjectName("accountingStandardId")
        form.addRow("核算标准", self.standard_id_label)
        self.enterprise_name = create_typed_input(
            identity,
            get_field_spec("enterprise_name"),
            "enterpriseNameInput",
            "企业名称",
        )
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
        self.period_year = QSpinBox(period_row)
        self.period_year.setObjectName("accountingPeriodYear")
        self.period_year.setProperty("fieldSpecKey", "period_year")
        self.period_year.setRange(2000, 2100)
        self.period_year.setValue(2025)
        self.period_year.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_year.valueChanged.connect(lambda _value: self._refresh_fuel_defaults())
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
        form.addRow("自定义周期", self.custom_period_row)
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

        source_activity, source_activity_layout = _card("02 排放源与活动数据", self)
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

        process_card, process_layout = _card("06 计算过程", self)
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

        result_card, result_layout = _card("07 核算结果", self)
        self.result_card = result_card
        self.result_total = QLabel("未计算", result_card)
        self.result_total.setObjectName("calculationTotal")
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
        result_actions.addStretch(1)
        result_layout.addLayout(result_actions)
        result_card.setVisible(False)
        self.body_layout.addWidget(result_card)

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
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setSpacing(12)
        self.confirmed_source_count = QLabel("已确认排放源：0", status_bar)
        self.confirmed_source_count.setObjectName("confirmedSourceCount")
        self.error_count = QLabel("错误：0", status_bar)
        self.error_count.setObjectName("calculationErrorCount")
        self.reminder_count = QLabel("提醒：0", status_bar)
        self.reminder_count.setObjectName("calculationReminderCount")
        self.calculation_status_hint = QLabel("填写完成后点击“计算排放量”，软件会集中检查并反馈问题。", status_bar)
        self.calculation_status_hint.setObjectName("calculationStatusHint")
        self.calculation_status_hint.setWordWrap(True)
        status_layout.addWidget(self.confirmed_source_count)
        status_layout.addWidget(self.error_count)
        status_layout.addWidget(self.reminder_count)
        status_layout.addWidget(self.calculation_status_hint, 1)

        self.calculate_button = QPushButton("计算排放量", self)
        self.calculate_button.setObjectName("calculateAccountingButton")
        self.calculate_button.setProperty("primary", True)
        self.calculate_button.clicked.connect(self._run_calculation)
        status_layout.addWidget(self.calculate_button)
        self.body_layout.addWidget(status_bar)
        self.body_layout.addStretch(1)
        self._refresh_source_cards()

    def _build_project_unit_controls(self) -> None:
        card, layout = _card("核算单元", self)
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
                values[name] = widget.currentIndex()
            elif isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QDateEdit):
                values[name] = widget.date().toString("yyyy-MM-dd")
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
                "path": row.path.currentIndex(),
                "activity": row.activity.text(),
                "carbon": row.carbon.text(),
                "oxidation": row.oxidation.text(),
                "lower_heating_value": row.lower_heating_value.text(),
                "source_reference": row.source_reference.text(),
                "fuel_label": row.custom_name.text(),
                "lhv_source": row.lhv_source.currentIndex(),
                "carbon_source": row.carbon_source.currentIndex(),
                "oxidation_source": row.oxidation_source.currentIndex(),
                "parameter_source": row.parameter_source,
            }
            for row in self._fuel_rows
        ]
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
            for combo, key in ((row.fuel_type, "type"), (row.path, "path")):
                index = stored.get(key)
                if isinstance(index, int) and 0 <= index < combo.count():
                    combo.setCurrentIndex(index)
            for widget, key in ((row.activity, "activity"), (row.carbon, "carbon"),
                                (row.oxidation, "oxidation"), (row.lower_heating_value, "lower_heating_value"),
                                (row.source_reference, "source_reference")):
                widget.setText(str(stored.get(key, "")))
            row.custom_name.setText(str(stored.get("fuel_label", "")))
            for combo, key in (
                (row.lhv_source, "lhv_source"),
                (row.carbon_source, "carbon_source"),
                (row.oxidation_source, "oxidation_source"),
            ):
                index = stored.get(key)
                if isinstance(index, int) and 0 <= index < combo.count():
                    combo.setCurrentIndex(index)
            stored_source = stored.get("parameter_source")
            if stored_source in {"AUTO", "MEASURED", "STANDARD_DEFAULT"}:
                row.parameter_source = str(stored_source)
            if not any(key in stored for key in ("lhv_source", "carbon_source", "oxidation_source")):
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
                    combo.setCurrentIndex(max(0, combo.findData(mode)))
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
        self._workspace = workspace
        self.project_name.setText(workspace.name)
        self._active_unit_index = next(i for i, unit in enumerate(workspace.units) if unit.unit_id == workspace.active_unit_id)
        self._refresh_unit_selector(workspace.active_unit_id)
        self._restore_form_state(workspace.units[self._active_unit_index].form_state)
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
        self.view_record_button.setEnabled(bool(self._latest_record_id))
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
        """Build all ten source cards through one shared Presentation path."""

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
            card.status_changed.connect(lambda _status, _source_id=source_id: self._refresh_source_cards())
            parent_layout.addWidget(card)

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

    def _add_fuel_row(self) -> None:
        self._fuel_row_serial += 1
        row = _FuelRow(self._fuel_row_serial, self._remove_fuel_row, self)
        self._fuel_rows.append(row)
        self.fuel_rows_layout.addWidget(row)
        self._bind_fuel_aliases(self._fuel_rows[0])
        row.fuel_type.currentIndexChanged.connect(lambda _index, _row=row: self._on_fuel_type_changed(_row, initialize_defaults=True))
        row.path.currentIndexChanged.connect(lambda _index, _row=row: self._refresh_fuel_row(_row, initialize_defaults=True))
        for combo in (row.lhv_source, row.carbon_source, row.oxidation_source):
            combo.currentIndexChanged.connect(lambda _index, _row=row: self._refresh_fuel_row(_row))
            combo.currentIndexChanged.connect(self._mark_input_dirty)
        row.custom_name.textChanged.connect(self._mark_input_dirty)
        row.custom_name.textChanged.connect(lambda *_args: self._refresh_source_cards())
        for widget in (row.activity, row.carbon, row.oxidation, row.lower_heating_value, row.source_reference):
            if isinstance(widget, QLineEdit):
                if isinstance(widget, NumericLineEdit):
                    widget.defer_range_validation_to_domain()
                widget.textChanged.connect(self._mark_input_dirty)
                widget.textChanged.connect(lambda *_args: self._refresh_source_cards())
        row.source_reference.textChanged.connect(lambda *_args, _row=row: self._refresh_source_cards())
        row.fuel_type.currentIndexChanged.connect(self._mark_input_dirty)
        row.path.currentIndexChanged.connect(self._mark_input_dirty)
        row.fuel_type.currentIndexChanged.connect(lambda *_args: self._refresh_source_cards())
        row.path.currentIndexChanged.connect(lambda *_args: self._refresh_source_cards())
        self._on_fuel_type_changed(row, initialize_defaults=True)

    def _on_fuel_type_changed(self, row: _FuelRow, *, initialize_defaults: bool = False) -> None:
        if not self._restoring_workspace and not row.activity.text().strip():
            try:
                fuel_type = _enum(row.fuel_type.currentData(), FuelType)
            except (TypeError, ValueError):
                fuel_type = None
            if fuel_type in _FUEL_C1_SUBJECT_IDS:
                standard_path = _FUEL_C1_ACTIVITY_PATH.get(fuel_type, FuelPath.MASS)
                path_index = row.path.findData(standard_path)
                if path_index >= 0 and row.path.currentIndex() != path_index:
                    row.path.setCurrentIndex(path_index)
        row._update_custom_name_visibility()
        self._refresh_fuel_row(row, initialize_defaults=initialize_defaults)

    def _remove_fuel_row(self, row: QWidget) -> None:
        if row not in self._fuel_rows:
            return
        if len(self._fuel_rows) == 1:
            assert isinstance(row, _FuelRow)
            row.activity.clear()
            row.carbon.clear()
            row.oxidation.clear()
            row.lower_heating_value.clear()
            row.source_reference.clear()
            row.custom_name.clear()
            for combo in (row.lhv_source, row.carbon_source, row.oxidation_source):
                combo.setCurrentIndex(0)
            row.internal_id.setText(f"fuel-{uuid4().hex}")
            self._refresh_fuel_row(row)
        else:
            self._fuel_rows.remove(row)  # type: ignore[arg-type]
            self.fuel_rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
            self._bind_fuel_aliases(self._fuel_rows[0])
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

    def _fuel_default_factors(self, row: _FuelRow) -> tuple[object | None, object, object] | None:
        try:
            fuel_type = _enum(row.fuel_type.currentData(), FuelType)
            path = _enum(row.path.currentData(), FuelPath)
        except (TypeError, ValueError):
            return None
        subject_id = _FUEL_C1_SUBJECT_IDS.get(fuel_type)
        if subject_id is None:
            return None
        if path is not FuelPath.HEAT and path is not _FUEL_C1_ACTIVITY_PATH.get(fuel_type, FuelPath.MASS):
            return None
        lhv_factor = self._canonical_default_factor(f"{subject_id}_lhv") if path is not FuelPath.HEAT else None
        carbon_factor = self._canonical_default_factor(f"{subject_id}_carbon_content")
        oxidation_factor = self._canonical_default_factor(f"{subject_id}_oxidation_rate")
        if carbon_factor is None or oxidation_factor is None:
            return None
        if path is not FuelPath.HEAT and lhv_factor is None:
            return None
        return lhv_factor, carbon_factor, oxidation_factor

    def _refresh_fuel_defaults(self) -> None:
        # Date edits can temporarily produce an invalid interval while users
        # set the start and end dates in sequence. Preserve selected defaults
        # until the interval becomes valid again.
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
        model = combo.model()
        item = model.item(1) if hasattr(model, "item") else None
        if item is not None:
            item.setEnabled(available)

    def _refresh_fuel_row(self, row: _FuelRow, *, initialize_defaults: bool = False) -> None:
        try:
            path = _enum(row.path.currentData(), FuelPath)
        except (TypeError, ValueError):
            path = None
        activity_unit = {FuelPath.VOLUME: "10⁴ Nm³", FuelPath.MASS: "t", FuelPath.HEAT: "GJ"}.get(path, "")
        factors = self._fuel_default_factors(row)
        lhv_factor, carbon_factor, oxidation_factor = factors if factors is not None else (None, None, None)
        default_values = {
            "lhv": "" if lhv_factor is None else str(lhv_factor.value),
            "carbon": "" if carbon_factor is None else str(carbon_factor.value),
            "oxidation": "" if oxidation_factor is None else str(oxidation_factor.value * Decimal("100")),
        }
        field_map = (
            ("lhv", row.lhv_source, row.lower_heating_value, lhv_factor),
            ("carbon", row.carbon_source, row.carbon, carbon_factor),
            ("oxidation", row.oxidation_source, row.oxidation, oxidation_factor),
        )
        for key, combo, edit, factor in field_map:
            available = factor is not None
            self._set_fuel_default_option(combo, available)
            prior_mode = combo.currentData()
            if initialize_defaults and prior_mode is None and available:
                combo.setCurrentIndex(combo.findData("STANDARD_DEFAULT"))
                prior_mode = "STANDARD_DEFAULT"
            is_default = prior_mode == "STANDARD_DEFAULT" and available
            edit.setReadOnly(is_default or path is FuelPath.HEAT and key == "lhv")
            if is_default:
                value = default_values[key]
                if edit.text().strip() != value:
                    # A prior standard-default value is replaced only while
                    # the user keeps the explicit default source selected.
                    edit.setText(value)
            elif prior_mode in {"CALCULATED", "MEASURED"}:
                edit.setReadOnly(False)
            elif row._last_default_values is not None:
                old = row._last_default_values[("lhv", "carbon", "oxidation").index(key)]
                if old and edit.text().strip() == old:
                    edit.clear()
            if combo is row.lhv_source:
                combo.setEnabled(path is not FuelPath.HEAT)
                edit.setEnabled(path is not FuelPath.HEAT)
        if path is FuelPath.HEAT and row.lower_heating_value.text().strip():
            row.lower_heating_value.clear()
            row.lhv_source.setCurrentIndex(0)
        row._last_default_values = (
            default_values["lhv"], default_values["carbon"], default_values["oxidation"]
        ) if factors is not None else None

        lhv_unit = {FuelPath.VOLUME: "GJ/10⁴ Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}.get(path, "")
        direct_carbon_unit = {FuelPath.VOLUME: "tC/10⁴ Nm³", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ"}.get(path, "")
        has_lhv = bool(row.lower_heating_value.text().strip()) or (
            row.lhv_source.currentData() == "STANDARD_DEFAULT" and lhv_factor is not None
        )
        row.activity_label.setText(f"活动量（{activity_unit}）")
        row.lhv_label.setText(f"低位发热量（{lhv_unit}）")
        row.carbon_label.setText(
            "单位热值含碳量（tC/GJ）" if has_lhv or path is FuelPath.HEAT
            else f"单位含碳量（{direct_carbon_unit}）"
        )
        modes = (row.lhv_source.currentData(), row.carbon_source.currentData(), row.oxidation_source.currentData())
        if factors is None:
            row.parameter_summary.setText(
                "该燃料/计量方式无已核验的标准缺省参数；请逐项选择计算值或实测值，填写参数及来源编号。"
            )
        elif all(mode == "STANDARD_DEFAULT" for mode in modes):
            row.parameter_summary.setText("已按 GB/T 32151.34—2024 附录 C.1 使用标准缺省参数。")
        elif any(mode in {"MEASURED", "CALCULATED"} for mode in modes):
            sources = []
            if "MEASURED" in modes:
                sources.append("实测值")
            if "CALCULATED" in modes:
                sources.append("计算值")
            if "STANDARD_DEFAULT" in modes:
                sources.append("缺省值")
            row.parameter_summary.setText(
                f"各参数按所选来源记录（{'、'.join(sources)}）；实测值或计算值需填写资料编号。"
            )
        else:
            row.parameter_summary.setText("请为低位发热量、单位含碳量和碳氧化率分别选择数据来源。")
        row.parameter_source = "STANDARD_DEFAULT" if all(mode in {"STANDARD_DEFAULT", None} for mode in modes) and "STANDARD_DEFAULT" in modes else (
            "MEASURED" if "MEASURED" in modes else "CALCULATED" if "CALCULATED" in modes else "AUTO"
        )

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
                    ("固定碳含量（%）", 1), ("数据来源", 1),
                    ("挥发分（%）", 1), ("数据来源", 1), ("", 0),
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
        self._bind_process_aliases(prefix)
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
        for widget, stretch in (
            (role, 2), (name, 2), (mass, 1), (carbon, 1),
            (carbon_source, 1), (volatile, 1), (volatile_source, 1), (remove, 0),
        ):
            row_layout.addWidget(widget, stretch)
            self._wire_dirty_tracking(widget)
        for widget in (name, mass, carbon, volatile):
            widget.textChanged.connect(lambda *_args, _row=process_row: self._refresh_material_summary(_row))
        for widget in (role, carbon_source, volatile_source):
            widget.currentIndexChanged.connect(lambda *_args, _row=process_row: self._refresh_material_summary(_row))
        material = {
            "line_id": line_id,
            "widget": container,
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
        if not isinstance(materials, list):
            return
        for material in tuple(materials):
            if not isinstance(material, dict) or material.get("line_id") != line_id:
                continue
            widget = material.get("widget")
            if isinstance(widget, QWidget):
                widget.setParent(None)
                widget.deleteLater()
            materials.remove(material)
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
        format_value = _display_compact_decimal
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

    def _add_fgd_component(self, unit: dict[str, object], *, component_id: str | None = None) -> dict[str, object]:
        component_id = component_id or uuid4().hex
        components = unit["components"]
        assert isinstance(components, list)
        first = not components and len(self._process_rows["fgd"]) == 0
        unit_index = self._process_rows["fgd"].index(unit) + 1 if unit in self._process_rows["fgd"] else len(self._process_rows["fgd"]) + 1
        component_host = unit["component_host"]
        component_layout = unit["component_layout"]
        assert isinstance(component_host, QWidget) and isinstance(component_layout, QVBoxLayout)
        container = QWidget(component_host)
        container.setObjectName(f"fgdComponent{component_id}")
        form = QFormLayout(container)
        widgets: dict[str, QWidget] = {}
        for field in ("cal", "i", "ef1", "tr"):
            spec = get_field_spec(f"fgd.{field}")
            name = f"fgd_{field}" if first else f"fgd_{unit['instance_id']}_{component_id}_{field}"
            edit = create_typed_input(container, spec, name)
            widgets[field] = edit
            form.addRow(spec.label, edit)
            self._wire_dirty_tracking(edit)
        selector = QComboBox(container)
        selector.setObjectName("fgdCarbonateTypeSelector" if first else f"fgd_{unit['instance_id']}_{component_id}_carbonateTypeSelector")
        selector.setProperty("fieldSpecKey", "fgd.ef1")
        selector.addItem("未选择碳酸盐种类", None)
        for label, parameter_id in _C2_CARBONATES:
            selector.addItem(label, parameter_id)
        widgets["carbonate_type"] = selector
        form.addRow("脱硫剂中的碳酸盐种类", selector)
        self._wire_dirty_tracking(selector)
        source_ref = create_typed_input(container, get_field_spec("fgd.factor_source_reference"), "fgdFactorSourceReferenceInput" if first else f"fgd_{unit['instance_id']}_{component_id}_factorSourceReference")
        source_ref.setPlaceholderText("实测因子或手工参数的资料编号")
        widgets["factor_source_reference"] = source_ref
        form.addRow("参数来源编号", source_ref)
        self._wire_dirty_tracking(source_ref)
        remove = QPushButton("删除组分", container)
        remove.setObjectName(f"remove_fgd_component_{unit['instance_id']}_{component_id}")
        remove.clicked.connect(lambda _checked=False, _unit=unit, _id=component_id: self._remove_fgd_component(_unit, _id))
        form.addRow(remove)
        component_layout.addWidget(container)
        widgets["_widget"] = container
        # The stable component ID is state, not an ordinary editable field.
        component_id_widget = QLineEdit(component_id, container)
        component_id_widget.hide()
        widgets["_component_id"] = component_id_widget
        widgets["component_id"] = component_id
        components.append(widgets)
        self._bind_process_aliases("fgd")
        return widgets

    def _remove_fgd_component(self, unit: dict[str, object], component_id: str) -> None:
        components = unit["components"]
        assert isinstance(components, list)
        for component in tuple(components):
            if component.get("component_id") == component_id:
                widget = component.get("_widget")
                if isinstance(widget, QWidget):
                    widget.setParent(None)
                    widget.deleteLater()
                components.remove(component)
        self._refresh_source_cards()

    def _remove_process_row(self, prefix: str, instance_id: str) -> None:
        rows = self._process_rows[prefix]
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
        self._bind_process_aliases(prefix)
        self._refresh_source_cards()

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
        self.custom_period_row.setVisible(index == 13)
        if 1 <= index <= 12:
            blocker = QSignalBlocker(self.period_month)
            self.period_month.setValue(index)
            del blocker
        self._refresh_heat_factor_details()
        self._refresh_fuel_defaults()

    def _sync_period_choice_from_month(self, month: int) -> None:
        if 1 <= month <= 12:
            blocker = QSignalBlocker(self.period_type)
            self.period_type.setCurrentIndex(month)
            del blocker
            self.custom_period_row.setVisible(False)
        self._refresh_heat_factor_details()
        self._refresh_fuel_defaults()

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
        return tuple(EmissionSourceState(source_id, _enum(combo.currentData(), EmissionSourceStatus)) for source_id, combo in self._source_statuses.items())

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
                ]
                if not active_components:
                    continue
                active += 1
                for component in active_components:
                    amount = component.get("cal")
                    factor = component.get("ef1")
                    selector = component.get("carbonate_type")
                    source_ref = component.get("factor_source_reference")
                    type_or_factor = (
                        isinstance(selector, QComboBox) and isinstance(selector.currentData(), str)
                    ) or (self._input_has_value(factor) and self._input_has_value(source_ref))
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
            complete = present and all(row.carbon.text().strip() and row.oxidation.text().strip() for row in active_rows)
            invalid = any(
                not row.activity.hasAcceptableInput()
                or bool(row.carbon.text().strip() and not row.carbon.hasAcceptableInput())
                or bool(row.oxidation.text().strip() and not row.oxidation.hasAcceptableInput())
                for row in active_rows
            )
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
            active_rows = [row for row in self._electricity_rows if row.amount.text().strip()]
            present = bool(active_rows)
            complete = present and all(
                row.detail_id.text().strip()
                and row.amount.hasAcceptableInput()
                and self._electricity_resolution_states.get(row.detail_id.text().strip()) == "RESOLVED"
                for row in active_rows
            )
            invalid = any(
                row.amount.text().strip()
                and (
                    not row.amount.hasAcceptableInput()
                    or self._electricity_resolution_states.get(row.detail_id.text().strip())
                    in {"BLOCKED", "DELEGATED", "ERROR"}
                )
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条电力明细" if active_rows else "尚未录入电力明细"
        elif source_id == "CAR-SRC-PURCHASED-HEAT-001":
            active_rows = [row for row in self._heat_rows["heat"] if self._input_has_value(row.get("amount"))]
            present = bool(active_rows)
            complete = present and all(self._heat_row_profile_complete(row) for row in active_rows)
            invalid = any(
                isinstance(row.get("amount"), QLineEdit) and not row["amount"].hasAcceptableInput()
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条热力来源" if present else "尚未录入热力活动数据"
        elif source_id == "CAR-SRC-EXPORTED-ELECTRICITY-001":
            active_rows = [row for row in self._output_electricity_rows if self._input_has_value(row.get("amount"))]
            present = bool(active_rows)
            complete = present and all(
                not self._input_has_value(row.get("measured")) or self._input_has_value(row.get("source"))
                for row in active_rows
            )
            invalid = any(
                isinstance(row.get("amount"), QLineEdit) and not row["amount"].hasAcceptableInput()
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条输出电力来源" if present else "尚未录入输出电力"
        elif source_id == "CAR-SRC-EXPORTED-HEAT-001":
            active_rows = [row for row in self._heat_rows["exported_heat"] if self._input_has_value(row.get("amount"))]
            present = bool(active_rows)
            complete = present and all(self._heat_row_profile_complete(row) for row in active_rows)
            invalid = any(
                isinstance(row.get("amount"), QLineEdit) and not row["amount"].hasAcceptableInput()
                for row in active_rows
            )
            summary = f"{len(active_rows)} 条输出热力来源" if present else "尚未录入输出热力"

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
    ) -> ParameterValue | None:
        source_kind = source.currentData()
        if source_kind == "STANDARD_DEFAULT":
            return CarbonMaterialAccountingPage._parameter_value_from_factor(
                factor, "采用当前核算期适用的 GB/T 32151.34—2024 附录 C.1 标准缺省值。"
            ) if factor is not None else None
        if source_kind not in {"CALCULATED", "MEASURED"} or value is None:
            return None
        reference = row.source_reference.text().strip()
        kind = ParameterSourceKind.CALCULATED if source_kind == "CALCULATED" else ParameterSourceKind.MEASURED
        source_name = "计算依据" if kind is ParameterSourceKind.CALCULATED else "实测/检测资料"
        return ParameterValue(
            parameter_id=f"enterprise_fuel_{row.row_key}_{suffix}",
            value=value,
            unit=unit,
            source_kind=kind,
            source_id=f"USER-FUEL-SOURCE-{row.row_key}" if reference else None,
            source_version="user-input" if reference else None,
            source_location=f"{source_name}编号：{reference}" if reference else None,
            selection_reason=f"用户选择{source_name}参数；来源编号：{reference or '未提供'}。",
        )

    def _fuel(self) -> tuple[FuelInput, ...]:
        fuels: list[FuelInput] = []
        for row in self._fuel_rows:
            activity = row.activity.text().strip()
            path = _enum(row.path.currentData(), FuelPath)
            defaults = self._fuel_default_factors(row)
            lhv_factor, carbon_factor, oxidation_factor = defaults if defaults is not None else (None, None, None)
            lhv_unit = {FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}[path]
            lhv_value_num = row.lower_heating_value.text().strip() or None
            carbon_value_num = row.carbon.text().strip() or None
            oxidation_value_num = _ui_value("fuel_oxidation", row.oxidation)
            has_lhv = lhv_value_num is not None or (
                row.lhv_source.currentData() == "STANDARD_DEFAULT" and lhv_factor is not None
            )
            carbon_unit = "tC/GJ" if has_lhv or path is FuelPath.HEAT else {
                FuelPath.VOLUME: "tC/10^4Nm3", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ"
            }[path]
            lhv_value = self._fuel_parameter(
                row=row, source=row.lhv_source, edit=row.lower_heating_value,
                suffix="lhv", unit=lhv_unit, factor=lhv_factor, value=lhv_value_num,
            ) if path is not FuelPath.HEAT else None
            carbon_value = self._fuel_parameter(
                row=row, source=row.carbon_source, edit=row.carbon,
                suffix="carbon", unit=carbon_unit, factor=carbon_factor, value=carbon_value_num,
            )
            oxidation_value = self._fuel_parameter(
                row=row, source=row.oxidation_source, edit=row.oxidation,
                suffix="oxidation", unit="ratio", factor=oxidation_factor,
                value=Decimal(str(oxidation_value_num)) if oxidation_value_num is not None else None,
            )
            fuels.append(FuelInput(
                fuel_id=row.internal_id.text().strip() or f"fuel-{row.row_key}",
                path=path,
                activity=activity or None,
                carbon_content=carbon_value,
                oxidation_rate=oxidation_value,
                lower_heating_value=lhv_value,
                fuel_type=_enum(row.fuel_type.currentData(), FuelType),
                fuel_label=row.custom_name.text().strip() or None,
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
                selected_parameter_id = selector.currentData()  # type: ignore[union-attr]
                carbonate_type = selector.currentText() if selected_parameter_id else None  # type: ignore[union-attr]
                ef_text = values["ef1"]
                if ef_text is not None:
                    factor_parameter_id = selected_parameter_id or "fgd_carbonate_emission_factor_measured"
                    factor_value = ParameterValue(
                        factor_parameter_id,
                        ef_text,
                        "tCO2/t",
                        ParameterSourceKind.MEASURED,
                        "USER-FGD-SOURCE" if source_ref else None,
                        "user-input",
                        f"企业检测/技术资料编号：{source_ref}" if source_ref else None,
                        f"企业提供可追溯因子；资料编号：{source_ref}" if source_ref else "企业提供的实测因子。",
                    )
                elif isinstance(selected_parameter_id, str):
                    factor = self._canonical_default_factor(selected_parameter_id, value_type=ValueType.STANDARD_SPECIFIED)
                    factor_value = self._parameter_value_from_factor(factor, "按选择的碳酸盐种类采用GB/T 32151.34—2024附录C.2对应值。") if factor is not None else None
                else:
                    factor_value = None

                def fgd_ratio(field: str, parameter_id: str) -> ParameterValue | None:
                    raw = values[field]
                    if raw is None:
                        factor = self._canonical_default_factor(parameter_id)
                        return self._parameter_value_from_factor(factor, "未提供企业实测值，采用GB/T 32151.34—2024标准一般取值。") if factor is not None else None
                    return ParameterValue(
                        parameter_id, Decimal(str(raw)), "ratio", ParameterSourceKind.MEASURED,
                        "USER-FGD-SOURCE" if source_ref else None, "user-input",
                        f"企业检测/技术资料编号：{source_ref}" if source_ref else None,
                        f"企业提供实测值；资料编号：{source_ref}" if source_ref else "企业提供的参数值。",
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
        for row in self._electricity_rows:
            detail = row.build(enterprise_id, period)
            if detail is not None:
                details.append(detail)
        result = tuple(details)
        if render:
            self._render_electricity_parameter_states(result)
        return result

    def _refresh_electricity_rows(self) -> None:
        try:
            self._electricity("enterprise.current", self._period())
        except (DomainValidationError, InvalidOperation, ValueError):
            self._electricity_resolution_states.clear()
            for row in self._electricity_rows:
                if row.amount.text().strip():
                    self._electricity_resolution_states[row.detail_id.text().strip()] = "ERROR"
                row.show_parameter_state(
                    "电力因子：等待完整明细",
                    "电力因子：尚未确定",
                    "来源说明：尚未确定",
                    "采用依据：请补齐本条明细后重新检查。",
                )
            self._refresh_source_cards()

    def _render_electricity_parameter_states(self, details: tuple[ElectricityConsumptionDetail, ...]) -> None:
        self._electricity_resolution_states.clear()
        waiting = (
            "电力因子：待录入",
            "电力因子：尚未确定",
            "来源说明：尚未确定",
            "采用依据：录入电量后按本条明细自动确定",
        )
        rows_by_id = {row.detail_id.text().strip(): row for row in self._electricity_rows}
        for row in self._electricity_rows:
            row.show_parameter_state(*waiting)
        if not details:
            return
        if self._parameter_resolver is None:
            for row in self._electricity_rows:
                if row.amount.text().strip():
                    self._electricity_resolution_states[row.detail_id.text().strip()] = "ERROR"
                row.show_parameter_state(
                    "电力因子：暂不可用",
                    "电力因子：尚未确定",
                    "来源说明：暂未取得标准参数",
                    "采用依据：当前无法取得适用的标准参数。",
                    "专业说明：参数服务暂不可用；未形成参数快照。",
                )
            return
        try:
            resolutions = self._parameter_resolver.resolve_electricity_details(
                details,
                snapshot_at=datetime.now(timezone.utc),
            )
        except (DomainValidationError, InvalidOperation, KeyError, ValueError) as exc:
            for row in self._electricity_rows:
                if row.amount.text().strip():
                    self._electricity_resolution_states[row.detail_id.text().strip()] = "ERROR"
                row.show_parameter_state(
                    "电力因子：暂未确定",
                    "电力因子：尚未确定",
                    "来源说明：暂不可用",
                    "采用依据：当前明细信息不足，无法确定适用参数。",
                    f"专业说明：{exc}",
                )
            return
        for resolution in resolutions:
            row = rows_by_id.get(resolution.detail.detail_id)
            if row is None:
                continue
            if resolution.route.value == "DELEGATE_DIRECT_FUEL_PATH":
                self._electricity_resolution_states[resolution.detail.detail_id] = "DELEGATED"
                reason = resolution.problems[0].message if resolution.problems else "转交直接燃料排放路径"
                row.show_parameter_state(
                    "电力因子：不适用",
                    "电力因子：不进入购电路径",
                    "来源说明：本明细按直接排放路径处理",
                    "采用依据：自发自用化石能源电力不重复计入购入电力。",
                    f"专业说明：{reason}",
                )
                continue
            selected = resolution.parameter_resolution.recommended if resolution.parameter_resolution else None
            snapshot = resolution.snapshot
            if selected is not None and snapshot is not None:
                self._electricity_resolution_states[resolution.detail.detail_id] = "RESOLVED"
                factor = selected.factor
                category = self.catalog_service.value_category_label(selected.category)
                review = self.catalog_service.review_status_label(factor.review_status)
                row.show_parameter_state(
                    "电力因子：已确定",
                    f"电力因子：{factor.value} {factor.unit} · {category}",
                    f"来源说明：{review} · 已按当前标准规则确定",
                    "采用依据：按核算期间、取得方式和电力属性自动确定。",
                    (
                        "专业详情（只读）\n"
                        f"参数 ID：{factor.parameter_id}\n"
                        f"因子 ID：{factor.factor_id}\n"
                        f"标准条款：B.8；电力参数规则\n"
                        f"参数来源：{factor.source_id or '未提供'}；来源定位：{factor.source_location or '未提供'}\n"
                        f"审核状态：{review}\n"
                        f"选择理由：{resolution.parameter_resolution.selection_reason if resolution.parameter_resolution else '按当前规则确定'}"
                    ),
                )
                continue
            problems = resolution.problems
            self._electricity_resolution_states[resolution.detail.detail_id] = "BLOCKED"
            display_code = problems[0].code if problems else "GEN-PAR-NO-APPLICABLE-VALUE"
            if display_code == "GEN-VAL-NONFOSSIL-EVIDENCE":
                display_code = "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE"
            reason = problems[0].message if problems else "当前明细未形成可用参数快照"
            row.show_parameter_state(
                "电力因子：需要处理",
                "电力因子：未采用",
                "来源说明：暂无可用的标准参数",
                "采用依据：请检查取得方式、电力属性和相应材料状态。",
                f"专业说明：校验代码 {display_code}；{reason}",
            )

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
        result: list[HeatInput] = []
        direction = "purchased_heat" if prefix == "heat" else "exported_heat"
        for row in self._heat_rows[prefix]:
            amount = _value(row["amount"])
            measured = _value(row["measured"])
            source_note = _value(row["source"])
            factor_mode_widget = row.get("factor_mode")
            factor_mode = (
                _enum(factor_mode_widget.currentData(), HeatFactorMode)
                if isinstance(factor_mode_widget, QComboBox)
                else HeatFactorMode.STANDARD_DEFAULT
            )
            if factor_mode is HeatFactorMode.MEASURED and measured is not None:
                factor = ParameterValue(
                    "heat_emission_factor_measured", measured, "tCO2/GJ", ParameterSourceKind.MEASURED,
                    "USER-HEAT-SOURCE" if source_note else None,
                    "user-input",
                    f"实测热力因子来源说明：{source_note}" if source_note else None,
                    f"{direction}逐来源实测热力因子。",
                )
            else:
                factor = None
                if row.get("legacy_factor_override"):
                    selector, reason = row.get("factor"), row.get("reason")
                    if isinstance(selector, QComboBox) and isinstance(reason, QWidget):
                        factor = self._selected_heat_parameter_value_for(
                            selector, reason, energy_direction=direction,
                        )
            enthalpy_mode_widget = row.get("enthalpy_mode")
            manual_enthalpy = isinstance(enthalpy_mode_widget, QComboBox) and enthalpy_mode_widget.currentData() == "MANUAL"
            result.append(HeatInput(
                _value(row["id"]) or str(row["default_line_id"]),
                amount,
                _value(row["enthalpy"]) if manual_enthalpy else None,
                factor,
                unit="t",
                steam_kind=_enum(row["steam"].currentData(), SteamKind),  # type: ignore[union-attr]
                pressure_mpa=_value(row["pressure"]),
                temperature_c=_value(row["temperature"]),
                manual_enthalpy=manual_enthalpy,
                factor_mode=_enum(factor_mode, HeatFactorMode),
                factor_source_note=source_note,
                steam_amount_t=InputValue(amount, "t") if amount is not None else None,
            ))
        return tuple(result)

    def _exported_electricity(self) -> tuple[ElectricityOutputLine, ...]:
        result: list[ElectricityOutputLine] = []
        for row in self._output_electricity_rows:
            amount = _value(row["amount"])
            selected_factor_id = row["factor"].currentData()  # type: ignore[union-attr]
            measured = _value(row["measured"])
            source_reference = _value(row["source"])
            factor_value: ParameterValue | None = None
            if measured is not None:
                factor_value = ParameterValue(
                    "electricity_emission_factor_measured", measured, "tCO2/MWh",
                    ParameterSourceKind.MEASURED,
                    "USER-EXPORTED-ELECTRICITY-SOURCE" if source_reference else None,
                    "user-input" if source_reference else None,
                    f"企业实测/检测资料编号：{source_reference}" if source_reference else None,
                    f"逐来源实测排放因子；来源编号：{source_reference or '未提供'}。",
                )
            elif isinstance(selected_factor_id, str):
                factor = self._electricity_factor_records.get(selected_factor_id)
                factor_value = self._parameter_value_from_factor(factor, "输出电力来源采用已核验目录因子。") if factor is not None else None
            result.append(ElectricityOutputLine(
                _value(row["id"]) or str(row["default_line_id"]), amount, factor_value,
            ))
        return tuple(result)

    def _input(self, *, increment: bool = True, render_electricity: bool = True) -> CarbonMaterialInput:
        if increment:
            self._calculation_index += 1
        period = self._period()
        enterprise_name = self.enterprise_name.text().strip()
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
        self._refresh_unit_result_summary()
        self._refresh_live_feedback()

    def _reset_for_new_accounting(self) -> None:
        """Restore every G06 control to the initial new-accounting state."""

        self._calculation_index = 0
        self.enterprise_name.clear()
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
        self.custom_period_row.setVisible(False)
        self._refresh_heat_factor_details()
        self.validation_list.clear()
        self.quality_card.setVisible(False)
        self.process_card.setVisible(False)
        self.result_card.setVisible(False)
        self._latest_record_id = None
        self.view_record_button.setEnabled(False)
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
            "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE": "非化石电力明细缺少有效证明材料，无法采用相应参数。",
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
            "GEN-VAL-NONFOSSIL-EVIDENCE": "非化石电力明细缺少有效证明材料，请补充证明信息。",
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
                    ("CARBON", row.carbon), ("FOX", row.oxidation),
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
        self.view_record_button.setEnabled(False)
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
            self.view_record_button.setEnabled(True)
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
                    self.project_save_status.setText(
                        "核算记录已生成，但项目关联尚未完成；恢复信息将保留并可重试。"
                    )
                    QMessageBox.critical(
                        self,
                        "核算记录关联失败",
                        "成功核算记录已经安全保存在记录库中，不会撤销或删除。"
                        "项目关联未完成；请检查项目数据文件后重新打开软件或再次保存项目。\n\n"
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
