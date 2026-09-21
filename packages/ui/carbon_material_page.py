"""G06 Qt page for hand-entered GB/T 32151.34 calculations.

The page keeps calculation rules in the Domain layer while presenting
business-language summaries and optional professional details.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.application.catalog_queries import CatalogQueryService
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
    EmissionSourceState,
    EmissionSourceStatus,
    FGDInput,
    FuelInput,
    FuelPath,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatInput,
    ElectricityOutputLine,
    MaterialBasis,
    MaterialComponentKind,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
)
from packages.core.models import AccountingPeriod, RecordStatus, ReviewStatus, ValueType
from packages.core.parameter_resolution import ParameterResolutionContext
from packages.core.repositories import RecordRepository

from .pages import BasePage, Navigate, _card
from .field_specs import SOURCE_LABELS, get_field_spec, ui_to_domain_value
from .source_cards import SourceCard, SourceCardPresentationState
from .typed_inputs import create_read_only_parameter, create_typed_input
from .view_models import AppRoute


_PROCESS_DEFAULT_PARAMETERS = {
    "calcination": ("0.35", "比例", "CAR-PAR-K1", "第5.2.2条；一般取0.35"),
    "baking": ("0.35", "比例", "CAR-PAR-K2", "第5.2.3条；一般取0.35"),
    "graphitization": ("0.35", "比例", "CAR-PAR-K3", "第5.2.4条；一般取0.35"),
}
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


_DISPLAY_QUANTUM = Decimal("0.01")


def _display_unit(unit: str) -> str:
    """Return the business-facing spelling of a calculation unit."""

    return unit.replace("tCO2", "tCO₂")


def _display_amount(value: Decimal, unit: str) -> str:
    """Format a Domain amount for ordinary UI display without mutating it."""

    amount = Decimal(str(value))
    if amount.is_zero():
        amount = abs(amount)
    with localcontext() as context:
        context.prec = max(28, len(amount.as_tuple().digits) + 4)
        rounded = amount.quantize(_DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)
    return f"{rounded:.2f} {_display_unit(unit)}"

class _ElectricityRow(QWidget):
    def __init__(self, index: int, remove: Callable[[QWidget], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"electricityRow{index}")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.detail_id = create_typed_input(
            self,
            get_field_spec("electricity.detail_id"),
            f"electricityDetailId{index}",
            f"detail-{index}",
        )
        self.detail_id.setText(f"electricity-detail-{index}")
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
        for column, widget in enumerate((self.detail_id, self.amount, self.acquisition, self.attribute, self.proof_type, self.proof_status, remove_button)):
            layout.addWidget(widget, 0, column)

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
        layout.addWidget(detail_panel, 1, 0, 1, 7)

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
        if amount is None:
            return None
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


class CarbonMaterialAccountingPage(BasePage):
    """Long, scrollable G06 work sheet for the only implemented industry standard."""

    record_created = Signal(str)

    def __init__(
        self,
        catalog_service: CatalogQueryService | None = None,
        calculator: CarbonMaterialCalculator | None = None,
        record_repository: RecordRepository | None = None,
        standard_id: str = STANDARD_ID,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(AppRoute.NEW_ACCOUNTING, parent)
        self.catalog_service = catalog_service or CatalogQueryService.empty()
        resolver = None
        try:
            resolver = create_g06_parameter_resolver(self.catalog_service.repository)
        except (AttributeError, KeyError, TypeError, ValueError):
            resolver = None
        self._parameter_resolver = resolver
        if calculator is None:
            catalog_version = self.catalog_service.standard_version(standard_id)
            calculator = CarbonMaterialCalculator(
                parameter_resolver=resolver,
                record_repository=record_repository,
                standard_version=catalog_version or STANDARD_VERSION,
            )
        self.calculator = calculator
        self.standard_id = standard_id
        self._calculation_index = 0
        self._electricity_rows: list[_ElectricityRow] = []
        self._source_statuses: dict[str, QComboBox] = {}
        self._source_cards: dict[str, SourceCard] = {}
        self._fields: dict[str, QLineEdit] = {}
        self._material_controls: dict[str, dict[str, QWidget]] = {}
        self._heat_factor_records = {}
        self._professional_detail_widgets: list[QWidget] = []
        # Presentation-only feedback from the existing G05/Domain paths.
        # These caches never become part of CarbonMaterialInput or persistence.
        self._electricity_resolution_states: dict[str, str] = {}
        self._known_source_errors: set[str] = set()
        self._validation_count_override: tuple[int, int] | None = None
        self._calculation_has_result = False
        self._build_page()
        self._input_dirty = False
        self._install_dirty_tracking()

    def set_standard_id(self, standard_id: str) -> None:
        self.standard_id = standard_id
        self.standard_id_label.setText(standard_id)
        if hasattr(self, "heat_factor_selector"):
            self._refresh_heat_factor_details()

    def _build_page(self) -> None:
        self.add_header("新建核算", "GB/T 32151.34-2024 炭素材料生产企业手工核算；成功计算后立即形成不可编辑核算记录。")

        identity, identity_layout = _card("01 核算信息与核算边界", self)
        form = QFormLayout()
        self.standard_id_label = QLabel(self.standard_id, identity)
        self.standard_id_label.setObjectName("accountingStandardId")
        form.addRow(get_field_spec("standard_id").label, self.standard_id_label)
        self.enterprise_name = create_typed_input(
            identity,
            get_field_spec("enterprise_name"),
            "enterpriseNameInput",
            "企业名称",
        )
        form.addRow(get_field_spec("enterprise_name").label, self.enterprise_name)
        self.period_type = create_typed_input(identity, get_field_spec("period_type"), "accountingPeriodType")
        self.period_type.addItem("年度", PeriodType.ANNUAL)
        self.period_type.addItem("月度（内部周期结果）", PeriodType.MONTHLY)
        self.period_type.currentIndexChanged.connect(lambda _index: self._refresh_heat_factor_details())
        form.addRow(get_field_spec("period_type").label, self.period_type)
        period_row = QWidget(identity)
        period_layout = QHBoxLayout(period_row)
        period_layout.setContentsMargins(0, 0, 0, 0)
        self.period_year = QSpinBox(period_row)
        self.period_year.setObjectName("accountingPeriodYear")
        self.period_year.setProperty("fieldSpecKey", "period_year")
        self.period_year.setRange(2000, 2100)
        self.period_year.setValue(2025)
        self.period_year.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_month = QSpinBox(period_row)
        self.period_month.setObjectName("accountingPeriodMonth")
        self.period_month.setProperty("fieldSpecKey", "period_month")
        self.period_month.setRange(1, 12)
        self.period_month.setValue(1)
        self.period_month.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        period_layout.addWidget(self.period_year)
        period_layout.addWidget(self.period_month)
        form.addRow(
            f"{get_field_spec('period_year').label} / {get_field_spec('period_month').label}",
            period_row,
        )
        identity_layout.addLayout(form)

        boundary = QWidget(identity)
        boundary_layout = QVBoxLayout(boundary)
        boundary_layout.setContentsMargins(0, 12, 0, 0)
        boundary_title = QLabel("核算边界", boundary)
        boundary_title.setObjectName("accountingBoundaryTitle")
        boundary_layout.addWidget(boundary_title)
        self.boundary_confirmed = create_typed_input(
            boundary,
            get_field_spec("boundary_confirmed"),
            "boundaryConfirmedCheckBox",
        )
        self.boundary_confirmed.setText("已确认法人企业/独立核算单位及生产系统边界")
        self.boundary_confirmed.setObjectName("boundaryConfirmedCheckBox")
        boundary_layout.addWidget(self.boundary_confirmed)
        boundary_hint = QLabel("边界按标准第4.1条结构化确认；未确认不能计算。", boundary)
        boundary_hint.setWordWrap(True)
        boundary_layout.addWidget(boundary_hint)
        self.other_activity_present = create_typed_input(
            boundary,
            get_field_spec("other_activity_present"),
            "otherIndustryActivityCheckBox",
        )
        self.other_activity_present.setText("存在本标准未覆盖的其他行业活动（需使用其他标准）")
        self.other_activity_present.setObjectName("otherIndustryActivityCheckBox")
        boundary_layout.addWidget(self.other_activity_present)
        self.transport_present = create_typed_input(
            boundary,
            get_field_spec("transport_present"),
            "upstreamDownstreamTransportCheckBox",
        )
        self.transport_present.setText("存在上下游运输（需使用其他标准）")
        self.transport_present.setObjectName("upstreamDownstreamTransportCheckBox")
        boundary_layout.addWidget(self.transport_present)
        identity_layout.addWidget(boundary)
        self.body_layout.addWidget(identity)

        presentation_options = QWidget(self)
        presentation_options_layout = QHBoxLayout(presentation_options)
        presentation_options_layout.setContentsMargins(0, 0, 0, 0)
        self.show_professional_details = QCheckBox("显示专业详情", presentation_options)
        self.show_professional_details.setObjectName("showProfessionalDetailsCheckBox")
        self.show_professional_details.setToolTip("默认只显示业务录入信息；打开后查看标准条款、来源和参数审计信息。")
        self.show_professional_details.toggled.connect(self._set_professional_details_visible)
        presentation_options_layout.addWidget(self.show_professional_details)
        presentation_options_layout.addWidget(
            QLabel("普通录入按标准默认值自动处理，异常口径和换算信息会在需要时展开。", presentation_options)
        )
        presentation_options_layout.addStretch(1)
        self.body_layout.addWidget(presentation_options)

        source_activity, source_activity_layout = _card("02 排放源与活动数据", self)
        self._build_source_cards(source_activity_layout)
        self.body_layout.addWidget(source_activity)

        process_card, process_layout = _card("06 计算过程", self)
        self.process_card = process_card
        self.trace_output = QLabel("点击“计算排放量”后显示分项计算结果。", process_card)
        self.trace_output.setObjectName("calculationTrace")
        self.trace_output.setWordWrap(True)
        process_layout.addWidget(self.trace_output)
        self.trace_professional_details = QLabel(
            "打开“显示专业详情”后可查看公式和变量代入信息。",
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
        self.view_process_button = QPushButton("查看计算过程", result_card)
        self.view_process_button.setObjectName("viewProcessButton")
        self.view_process_button.clicked.connect(self._toggle_process_details)
        result_actions.addWidget(self.view_breakdown_button)
        result_actions.addWidget(self.view_process_button)
        result_actions.addStretch(1)
        result_layout.addLayout(result_actions)
        result_card.setVisible(False)
        self.body_layout.addWidget(result_card)

        quality_card, quality_layout = _card("08 数据质量检查", self)
        self.quality_card = quality_card
        self.validation_list = QListWidget(quality_card)
        self.validation_list.setObjectName("calculationValidationList")
        self.validation_list.itemClicked.connect(self._focus_validation_item)
        quality_layout.addWidget(self.validation_list)
        self.validation_professional_details = QLabel(
            "打开“显示专业详情”后可查看原始校验信息和内部定位。",
            quality_card,
        )
        self.validation_professional_details.setObjectName("calculationValidationProfessionalDetails")
        self.validation_professional_details.setWordWrap(True)
        quality_layout.addWidget(self.validation_professional_details)
        self._register_professional_details(self.validation_professional_details)
        quality_card.setVisible(False)
        self.body_layout.addWidget(quality_card)

        self.check_button = QPushButton("检查数据", self)
        self.check_button.setObjectName("checkAccountingButton")
        self.check_button.clicked.connect(self._run_calculation)
        self.check_button.setVisible(False)

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
        self.calculation_status_hint = QLabel("填写数据后将自动更新基础检查结果。", status_bar)
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

    def _register_professional_details(self, widget: QWidget) -> None:
        self._professional_detail_widgets.append(widget)
        widget.setVisible(getattr(self, "show_professional_details", None) is not None and self.show_professional_details.isChecked())

    def _set_professional_details_visible(self, visible: bool) -> None:
        for widget in self._professional_detail_widgets:
            widget.setVisible(visible)
        for row in self._electricity_rows:
            row.set_professional_details_visible(visible)
        for controls in self._material_controls.values():
            details = controls.get("professional_details")
            if details is not None:
                details.setVisible(visible)
        if hasattr(self, "trace_professional_details") and not self.trace_professional_details.text().strip():
            self.trace_professional_details.setText("暂无专业计算过程信息。")

    def _toggle_result_line_details(self) -> None:
        visible = not self.result_line_details.isVisible()
        self.result_line_details.setVisible(visible)
        self.view_breakdown_button.setText("收起分项结果" if visible else "查看分项结果")

    def _toggle_process_details(self) -> None:
        visible = not self.process_card.isVisible()
        self.process_card.setVisible(visible)
        self.view_process_button.setText("收起计算过程" if visible else "查看计算过程")
        if visible:
            self._scroll_to_widget(self.process_card)

    def _scroll_to_widget(self, widget: QWidget) -> None:
        scroll_area = self.window().findChild(QScrollArea, "mainScrollArea")
        if scroll_area is not None:
            scroll_area.ensureWidgetVisible(widget)

    def _focus_validation_item(self, item: QListWidgetItem) -> None:
        source_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(source_id, str):
            return
        card = self._source_cards.get(source_id)
        if card is None:
            return
        card.set_expanded(True)
        self._scroll_to_widget(card)

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
            combo.addItem("不涉及", EmissionSourceStatus.NOT_INVOLVED)
            combo.addItem("涉及", EmissionSourceStatus.INVOLVED)
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
        row = QWidget(self)
        layout = QGridLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        fuel_keys = ("fuel_id", "fuel_path", "fuel_activity", "fuel_carbon", "fuel_oxidation")
        for column, key in enumerate(fuel_keys):
            layout.addWidget(QLabel(get_field_spec(key).label), 0, column)
        self._fields["fuel_id"] = create_typed_input(row, get_field_spec("fuel_id"), "fuelIdInput", "natural-gas")  # type: ignore[assignment]
        self._fields["fuel_path"] = create_typed_input(row, get_field_spec("fuel_path"), "fuelPathInput")  # type: ignore[assignment]
        for path, label in ((FuelPath.VOLUME, "体积"), (FuelPath.MASS, "质量"), (FuelPath.HEAT, "热量")):
            self._fields["fuel_path"].addItem(label, path)  # type: ignore[union-attr]
        self._fields["fuel_activity"] = create_typed_input(row, get_field_spec("fuel_activity"), "fuelActivityInput")  # type: ignore[assignment]
        self._fields["fuel_carbon"] = create_typed_input(row, get_field_spec("fuel_carbon"), "fuelCarbonInput")  # type: ignore[assignment]
        self._fields["fuel_oxidation"] = create_typed_input(row, get_field_spec("fuel_oxidation"), "fuelOxidationInput")  # type: ignore[assignment]
        for column, key in enumerate(("fuel_id", "fuel_path", "fuel_activity", "fuel_carbon", "fuel_oxidation")):
            layout.addWidget(self._fields[key], 1, column)
        parent_layout.addWidget(row)

    def _build_process_section(self, parent_layout: QVBoxLayout, title: str, prefix: str, fields: tuple[str, ...]) -> None:
        field_groups = {
            "calcination": (
                ("投入数据", ("gc", "wfc", "wvar")),
                ("产出数据", ("cc", "ucc", "du", "wfc_c", "wvar_c")),
            ),
            "baking": (
                ("投入数据", ("bpm", "bpmfc", "bg", "bgfc", "bpmvar", "bgvar")),
                ("产出数据", ("bwt", "bp", "bpfc")),
            ),
            "graphitization": (
                ("投入数据", ("gpm", "gpmfc", "gta", "gtafc", "gpmvar")),
                ("产出数据", ("gwt", "gp", "gpfc")),
            ),
        }.get(prefix, (("活动数据", fields),))
        for group_name, group_fields in field_groups:
            group = QWidget(self)
            group.setObjectName(f"{prefix}_{group_name}")
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_title = QLabel(group_name, group)
            group_title.setObjectName(f"{prefix}_{group_name}_title")
            group_layout.addWidget(group_title)
            row = QWidget(group)
            form = QFormLayout(row)
            for field in group_fields:
                spec = get_field_spec(f"{prefix}.{field}")
                edit = create_typed_input(row, spec, f"{prefix}_{field}")
                self._fields[f"{prefix}.{field}"] = edit
                form.addRow(spec.label, edit)
            group_layout.addWidget(row)
            parent_layout.addWidget(group)

        if prefix not in {"calcination", "baking", "graphitization"}:
            return

        self._build_material_controls(parent_layout, prefix)

    def _build_material_controls(self, parent_layout: QVBoxLayout, prefix: str) -> None:
        """Build business-language basis controls with conditional expansion.

        The hidden widgets keep the existing Domain input contract and object
        names for compatibility.  Users see the standard received-basis
        summary by default; only a non-standard or inconsistent basis expands
        the conversion section.
        """

        metadata = QWidget(self)
        metadata.setObjectName(f"{prefix}_otherNecessaryData")
        metadata_layout = QVBoxLayout(metadata)
        metadata_layout.setContentsMargins(0, 8, 0, 0)
        summary_row = QHBoxLayout()
        basis_summary = QLabel("数据口径：收到基", metadata)
        basis_summary.setObjectName(f"{prefix}_basisSummary")
        basis_summary.setWordWrap(True)
        summary_row.addWidget(basis_summary, 1)
        edit_button = QPushButton("修改", metadata)
        edit_button.setObjectName(f"{prefix}_basisEditButton")
        edit_button.clicked.connect(lambda _checked=False, _prefix=prefix: self._toggle_basis_editor(_prefix))
        summary_row.addWidget(edit_button)
        metadata_layout.addLayout(summary_row)

        default_value, default_unit, _default_parameter_id, _default_clause = _PROCESS_DEFAULT_PARAMETERS[prefix]
        parameter_summary = QLabel(
            f"默认排放参数：{default_value}（{default_unit}）· 标准默认",
            metadata,
        )
        parameter_summary.setObjectName(f"{prefix}_parameterSummary")
        parameter_summary.setWordWrap(True)
        metadata_layout.addWidget(parameter_summary)

        basis_editor = QWidget(metadata)
        basis_editor.setObjectName(f"{prefix}_basisAndConversionEditor")
        basis_editor_layout = QFormLayout(basis_editor)
        basis_editor_layout.setContentsMargins(0, 8, 0, 0)
        basis_editor_title = QLabel("数据口径与换算", basis_editor)
        basis_editor_title.setObjectName(f"{prefix}_basisAndConversionTitle")
        basis_editor_title.setWordWrap(True)
        basis_editor_layout.addRow(basis_editor_title)

        basis_options = (
            (MaterialBasis.UNKNOWN, "未确认"),
            (MaterialBasis.RECEIVED, "收到基"),
            (MaterialBasis.DRY, "干燥基"),
            (MaterialBasis.OTHER_DOCUMENTED, "其他有证基准"),
        )
        mass_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.mass_basis"), f"{prefix}_massBasisSelector")
        composition_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.composition_basis"), f"{prefix}_compositionBasisSelector")
        normalized_basis = create_typed_input(basis_editor, get_field_spec(f"{prefix}.normalized_basis"), f"{prefix}_normalizedBasisSelector")
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
            f"{prefix}_fixedCarbonComponentKindSelector",
        )
        volatile_matter_component_kind = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.volatile_matter_component_kind"),
            f"{prefix}_volatileMatterComponentKindSelector",
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
        automatic_component_summary.setObjectName(f"{prefix}_automaticComponentSummary")
        automatic_component_summary.setWordWrap(True)
        basis_editor_layout.addRow("字段性质", automatic_component_summary)

        moisture_evidence = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.moisture_evidence"),
            f"{prefix}_moistureEvidenceCheckBox",
        )
        moisture_evidence.setText("数据来源已记录")
        moisture_evidence.setObjectName(f"{prefix}_moistureEvidenceCheckBox")
        conversion_evidence = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.conversion_evidence"),
            f"{prefix}_conversionEvidenceCheckBox",
        )
        conversion_evidence.setText("换算依据已提供")
        conversion_evidence.setObjectName(f"{prefix}_conversionEvidenceCheckBox")
        evidence_reference = create_typed_input(
            basis_editor,
            get_field_spec(f"{prefix}.evidence_reference"),
            f"{prefix}_basisEvidenceReferenceInput",
            "报告/台账编号或来源说明（非收到基必填）",
        )
        basis_editor.setVisible(False)
        basis_warning = QLabel("", basis_editor)
        basis_warning.setObjectName(f"{prefix}_basisWarning")
        basis_warning.setWordWrap(True)
        basis_editor_layout.addRow("提示", basis_warning)
        basis_editor_layout.addRow("数据来源", moisture_evidence)
        basis_editor_layout.addRow("换算依据", conversion_evidence)
        basis_editor_layout.addRow("报告/台账编号或来源说明", evidence_reference)

        professional_details = QLabel("", metadata)
        professional_details.setObjectName(f"{prefix}_professionalDetails")
        professional_details.setWordWrap(True)
        metadata_layout.addWidget(basis_editor)
        metadata_layout.addWidget(professional_details)

        self._material_controls[prefix] = {
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
        for widget in (mass_basis, composition_basis, moisture_evidence, conversion_evidence, evidence_reference):
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda _index, _prefix=prefix: self._refresh_material_basis_display(_prefix))
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(lambda _checked, _prefix=prefix: self._refresh_material_basis_display(_prefix))
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _text, _prefix=prefix: self._refresh_material_basis_display(_prefix))
        self._register_professional_details(professional_details)
        parent_layout.addWidget(metadata)
        self._refresh_material_basis_display(prefix)

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

    def _toggle_basis_editor(self, prefix: str) -> None:
        controls = self._material_controls[prefix]
        editor = controls["basis_editor"]
        requires_expansion = self._basis_requires_expansion(prefix)
        visible = not editor.isVisible() or requires_expansion
        if visible or not requires_expansion:
            editor.setVisible(visible)
        self._refresh_material_basis_display(prefix)

    def _basis_requires_expansion(self, prefix: str) -> bool:
        controls = self._material_controls[prefix]
        mass = self._material_basis_value(controls, "mass_basis", MaterialBasis.RECEIVED)
        composition = self._material_basis_value(controls, "composition_basis", MaterialBasis.RECEIVED)
        return mass is not MaterialBasis.RECEIVED or composition is not MaterialBasis.RECEIVED or mass is not composition

    def _refresh_material_basis_display(self, prefix: str) -> None:
        controls = self._material_controls.get(prefix)
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

        requires_expansion = self._basis_requires_expansion(prefix)
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
        default_value, default_unit, parameter_id, default_clause = _PROCESS_DEFAULT_PARAMETERS[prefix]
        detail_lines = [
            "专业详情（只读）",
            f"数据基准转换：质量数据 {mass_label}；成分含量 {composition_label}；内部归一目标：收到基。",
            "固定碳字段性质：固定碳（由字段定义自动确定）。",
            "挥发分字段性质：挥发分（由字段定义自动确定）。",
            f"标准默认参数：{default_value}（{default_unit}）；参数 ID：{parameter_id}；"
            f"标准条款：{default_clause}；参数来源：标准默认值；选择理由：按适用标准默认规则采用。",
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

    def _add_electricity_row(self) -> None:
        row = _ElectricityRow(len(self._electricity_rows) + 1, self._remove_electricity_row, self)
        self._electricity_rows.append(row)
        row.set_professional_details_visible(self.show_professional_details.isChecked())
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

    def _remove_electricity_row(self, row: QWidget) -> None:
        if row in self._electricity_rows:
            self._electricity_rows.remove(row)
            self.electricity_rows_layout.removeWidget(row)
            row.deleteLater()
            self._refresh_source_cards()

    def _build_output_electricity_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("输出电力（I03；从间接排放中抵扣）", self)
        label.setObjectName("exportedElectricitySectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        self._fields["exported_electricity_id"] = create_typed_input(
            row,
            get_field_spec("exported_electricity_id"),
            "exportedElectricityLineIdInput",
            "exported-electricity-1",
        )
        self._fields["exported_electricity_amount"] = create_typed_input(
            row,
            get_field_spec("exported_electricity_amount"),
            "exportedElectricityAmountInput",
            "MWh",
        )
        form.addRow(get_field_spec("exported_electricity_id").label, self._fields["exported_electricity_id"])
        form.addRow(get_field_spec("exported_electricity_amount").label, self._fields["exported_electricity_amount"])
        parent_layout.addWidget(row)

    def _build_heat_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("购入热力/动力（I02）", self)
        label.setObjectName("heatSectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        for key in (
            "heat_id",
            "heat_amount",
            "heat_enthalpy",
            "heat_pressure",
            "heat_temperature",
        ):
            edit = create_typed_input(row, get_field_spec(key), f"{key}Input")
            self._fields[key] = edit
            form.addRow(get_field_spec(key).label, edit)
        self._heat_steam_kind = create_typed_input(row, get_field_spec("heat_steam_kind"), "heatSteamKindSelector")
        self._heat_steam_kind.addItem("饱和蒸汽（附录C.4）", SteamKind.SATURATED)
        self._heat_steam_kind.addItem("过热蒸汽（附录C.5）", SteamKind.SUPERHEATED)
        form.addRow(get_field_spec("heat_steam_kind").label, self._heat_steam_kind)
        self.heat_factor_selector = QComboBox(row)
        self.heat_factor_selector.setObjectName("heatFactorSelector")
        self.heat_factor_selector.setProperty("fieldSpecKey", "heat_factor")
        self.heat_factor_selector.setToolTip(get_field_spec("heat_factor").help_text)
        self.heat_factor_selector.currentIndexChanged.connect(self._refresh_heat_factor_details)
        self.heat_factor_metadata = create_read_only_parameter(row, get_field_spec("heat_factor"), "heatFactorMetadata")
        self.heat_factor_metadata.setText("推荐热力因子：尚未加载")
        form.addRow("热力参数摘要（只读）", self.heat_factor_metadata)
        self.parameter_selection_status = QLabel("采用依据：按核算期间自动确定标准默认值。", row)
        self.parameter_selection_status.setObjectName("parameterSelectionStatus")
        self.parameter_selection_status.setWordWrap(True)
        form.addRow("采用依据", self.parameter_selection_status)
        self.heat_factor_edit_button = QPushButton("更改参数", row)
        self.heat_factor_edit_button.setObjectName("heatFactorEditButton")
        self.heat_factor_edit_button.clicked.connect(self._toggle_heat_parameter_advanced)
        form.addRow("", self.heat_factor_edit_button)

        self.heat_factor_professional_details = QLabel("", row)
        self.heat_factor_professional_details.setObjectName("heatFactorProfessionalDetails")
        self.heat_factor_professional_details.setWordWrap(True)

        advanced_panel = QWidget(row)
        advanced_panel.setObjectName("heatFactorAdvancedPanel")
        advanced_form = QFormLayout(advanced_panel)
        advanced_form.addRow("高级参数选择", QLabel("需要更改自动推荐值时，请选择其他适用值并填写理由。", advanced_panel))
        advanced_form.addRow("选择其他适用值", self.heat_factor_selector)
        self.heat_factor_selection_reason = create_typed_input(
            advanced_panel,
            get_field_spec("heat_factor_selection_reason"),
            "heatFactorSelectionReasonInput",
            "选择其他适用值时填写理由",
        )
        advanced_form.addRow("参数选择理由", self.heat_factor_selection_reason)
        advanced_panel.setVisible(False)
        form.addRow("", advanced_panel)
        form.addRow("专业详情", self.heat_factor_professional_details)
        self._register_professional_details(self.heat_factor_professional_details)
        self._heat_factor_advanced_panel = advanced_panel
        parent_layout.addWidget(row)
        self._populate_heat_factor_selector()

    def _build_output_heat_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("输出热力/动力（I04；从间接排放中抵扣）", self)
        label.setObjectName("exportedHeatSectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        exported_heat_object_names = {
            "exported_heat_id": "exportedHeatLineIdInput",
            "exported_heat_amount": "exportedHeatAmountInput",
            "exported_heat_enthalpy": "exportedHeatEnthalpyInput",
            "exported_heat_pressure": "exportedHeatPressureInput",
            "exported_heat_temperature": "exportedHeatTemperatureInput",
        }
        for key in exported_heat_object_names:
            edit = create_typed_input(row, get_field_spec(key), exported_heat_object_names[key])
            self._fields[key] = edit
            form.addRow(get_field_spec(key).label, edit)
        self._exported_heat_steam_kind = create_typed_input(
            row,
            get_field_spec("exported_heat_steam_kind"),
            "exportedHeatSteamKindSelector",
        )
        self._exported_heat_steam_kind.addItem("饱和蒸汽（附录C.4）", SteamKind.SATURATED)
        self._exported_heat_steam_kind.addItem("过热蒸汽（附录C.5）", SteamKind.SUPERHEATED)
        form.addRow(get_field_spec("exported_heat_steam_kind").label, self._exported_heat_steam_kind)
        hint = QLabel("I04 与 I02 共用上方热力参数摘要；输出热力同样必须标记排放源为“涉及”。", row)
        hint.setWordWrap(True)
        form.addRow("参数路径", hint)
        parent_layout.addWidget(row)

    def _populate_heat_factor_selector(self) -> None:
        records = sorted(
            self.catalog_service.list_parameter_factors("heat_emission_factor_default"),
            key=lambda item: (-(item.factor_year or 0), item.factor_id),
        )
        self._heat_factor_records = {item.factor_id: item for item in records}
        self.heat_factor_selector.clear()
        for record in records:
            category = self.catalog_service.value_category(record)
            category_label = self.catalog_service.value_category_label(category)
            self.heat_factor_selector.addItem(
                f"{category_label}：{record.normalized_value} {record.normalized_unit}",
                record.factor_id,
            )
        if not records:
            self.heat_factor_selector.addItem("暂无可用的标准热力参数", None)
            self.heat_factor_selector.setEnabled(False)
        self._refresh_heat_factor_details()

    def _heat_resolution_context(self, *, confirmed_factor_id: str | None = None, confirmation_reason: str | None = None) -> ParameterResolutionContext:
        return ParameterResolutionContext(
            parameter_id="heat_emission_factor_default",
            standard_id=self.standard_id,
            accounting_period=self._period(),
            parameter_type=ParameterType.HEAT_EMISSION_FACTOR,
            subject_id="purchased_heat",
            confirmed_factor_id=confirmed_factor_id,
            confirmation_reason=confirmation_reason,
        )

    def _refresh_heat_factor_details(self) -> None:
        if not hasattr(self, "heat_factor_selector"):
            return
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

    def _toggle_heat_parameter_advanced(self) -> None:
        visible = not self._heat_factor_advanced_panel.isVisible()
        self._heat_factor_advanced_panel.setVisible(visible)
        self.heat_factor_edit_button.setText("收起参数选择" if visible else "更改参数")
    def _period(self) -> AccountingPeriod:
        year = self.period_year.value()
        if _enum(self.period_type.currentData(), PeriodType) is PeriodType.ANNUAL:
            return AccountingPeriod(PeriodType.ANNUAL, __import__("datetime").date(year, 1, 1), __import__("datetime").date(year, 12, 31))
        month = self.period_month.value()
        import calendar
        return AccountingPeriod(PeriodType.MONTHLY, __import__("datetime").date(year, month, 1), __import__("datetime").date(year, month, calendar.monthrange(year, month)[1]))

    def _source_states(self) -> tuple[EmissionSourceState, ...]:
        return tuple(EmissionSourceState(source_id, _enum(combo.currentData(), EmissionSourceStatus)) for source_id, combo in self._source_statuses.items())

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
        for row in self._electricity_rows:
            detail_id = row.detail_id.text().strip()
            if detail_id:
                dynamic_field_owners[detail_id] = "CAR-SRC-PURCHASED-ELECTRICITY-001"
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
        keys = tuple(f"{prefix}.{field}" for field in fields)
        present = any(self._field_has_value(key) for key in keys)
        complete = present and all(self._field_has_value(key) for key in keys)
        invalid = any(self._field_has_error(key) for key in keys)
        controls = self._material_controls.get(prefix)
        if present and controls is not None:
            basis_keys = ("mass_basis", "composition_basis", "normalized_basis")
            component_keys = ("fixed_carbon_component_kind", "volatile_matter_component_kind")
            basis_defaults = {
                "mass_basis": MaterialBasis.RECEIVED,
                "composition_basis": MaterialBasis.RECEIVED,
                "normalized_basis": MaterialBasis.RECEIVED,
            }
            component_defaults = {
                "fixed_carbon_component_kind": MaterialComponentKind.FIXED_CARBON,
                "volatile_matter_component_kind": MaterialComponentKind.VOLATILE_MATTER,
            }
            complete = complete and all(
                (
                    self._material_basis_value(controls, key, basis_defaults[key])
                    if key in basis_defaults
                    else self._material_component_value(controls, key, component_defaults[key])
                )
                is not None
                for key in basis_keys + component_keys
            )
        return present, complete, invalid

    def _derive_source_card_state(self, source_id: str) -> tuple[SourceCardPresentationState, str]:
        status = _enum(self._source_statuses[source_id].currentData(), EmissionSourceStatus)
        if status is EmissionSourceStatus.NOT_INVOLVED:
            return SourceCardPresentationState.NOT_INVOLVED, "未启用 · 不涉及"
        if status is EmissionSourceStatus.UNCONFIRMED:
            return SourceCardPresentationState.UNCONFIRMED, "待确认 · 尚未确定是否涉及"

        present = False
        complete = False
        invalid = False
        summary = "尚未录入活动数据"
        if source_id == "CAR-SRC-FUEL-001":
            keys = ("fuel_id", "fuel_activity", "fuel_carbon", "fuel_oxidation")
            present = any(self._field_has_value(key) for key in keys)
            complete = present and all(self._field_has_value(key) for key in keys)
            invalid = any(self._field_has_error(key) for key in keys)
            summary = "1 种燃料" if present else "尚未录入燃料"
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
            summary = "已录入活动数据" if present else "尚未录入活动数据"
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
            present = self._field_has_value("heat_amount")
            complete = present and bool(self.heat_factor_selector.currentData())
            invalid = self._field_has_error("heat_amount")
            summary = "已录入热力活动数据" if present else "尚未录入热力活动数据"
        elif source_id == "CAR-SRC-EXPORTED-ELECTRICITY-001":
            present = self._field_has_value("exported_electricity_amount")
            complete = present
            invalid = self._field_has_error("exported_electricity_amount")
            summary = "已录入输出电力" if present else "尚未录入输出电力"
        elif source_id == "CAR-SRC-EXPORTED-HEAT-001":
            present = self._field_has_value("exported_heat_amount")
            complete = present and self._field_has_value("exported_heat_enthalpy")
            invalid = self._field_has_error("exported_heat_amount") or self._field_has_error("exported_heat_enthalpy")
            summary = "已录入输出热力" if present else "尚未录入输出热力"

        # A card may only report completed after a real existing validation run
        # has stopped reporting a source-scoped error.  This deliberately
        # consumes Domain feedback instead of reproducing Domain rules here.
        if source_id in self._known_source_errors:
            invalid = True
        if invalid or (present and not complete):
            return SourceCardPresentationState.NEEDS_ATTENTION, f"{summary} · 需要处理"
        if complete:
            return SourceCardPresentationState.COMPLETED, f"{summary} · 已完成"
        return SourceCardPresentationState.FILLING, f"{summary} · 填写中"

    def _refresh_source_cards(self, *_args: object) -> None:
        if not self._source_cards or not hasattr(self, "heat_factor_selector"):
            return
        for source_id, card in self._source_cards.items():
            state, summary = self._derive_source_card_state(source_id)
            card.set_presentation_state(state, summary)
        self._refresh_live_feedback()

    def _refresh_live_feedback(self) -> None:
        """Refresh lightweight Presentation feedback without invoking Domain calculation."""

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
            if not self.enterprise_name.text().strip():
                errors += 1
            if not self.boundary_confirmed.isChecked():
                errors += 1
            if self.other_activity_present.isChecked():
                errors += 1
            if self.transport_present.isChecked():
                errors += 1
            for card in self._source_cards.values():
                if card.presentation_state is SourceCardPresentationState.NEEDS_ATTENTION:
                    errors += 1
                elif card.presentation_state in {
                    SourceCardPresentationState.FILLING,
                    SourceCardPresentationState.UNCONFIRMED,
                }:
                    reminders += 1
        self.confirmed_source_count.setText(f"已确认排放源：{confirmed}")
        self.error_count.setText(f"错误：{errors}")
        self.reminder_count.setText(f"提醒：{reminders}")
        if errors:
            self.calculation_status_hint.setText("请先处理错误，再计算排放量。")
        elif reminders:
            self.calculation_status_hint.setText("仍有待确认或未完成的排放源；可继续填写后计算。")
        elif self._calculation_has_result:
            self.calculation_status_hint.setText("结果已生成；如修改输入，请重新计算以形成新的记录。")
        else:
            self.calculation_status_hint.setText("基础检查已通过，可以计算排放量。")

    def _fuel(self) -> tuple[FuelInput, ...]:
        fuel_id = _value(self._fields["fuel_id"])
        values = (
            _value(self._fields["fuel_activity"]),
            _value(self._fields["fuel_carbon"]),
            _ui_value("fuel_oxidation", self._fields["fuel_oxidation"]),
        )
        if fuel_id is None and all(value is None for value in values):
            return ()
        path = _enum(self._fields["fuel_path"].currentData(), FuelPath)  # type: ignore[union-attr]
        return (FuelInput(fuel_id or "fuel-1", path, *values),)

    def _process(self, prefix: str, kind):
        field_names = {
            "calcination": ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"),
            "baking": ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"),
            "graphitization": ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"),
            "fume": ("q", "qvar", "hm", "fch", "fox", "duration"),
            "fgd": ("cal", "i", "ef1", "tr"),
        }[prefix]
        values = {
            field: _ui_value(f"{prefix}.{field}", self._fields[f"{prefix}.{field}"])
            for field in field_names
        }
        if all(value is None for value in values.values()):
            return None
        controls = self._material_controls.get(prefix)
        if controls is None:
            return kind(**values)
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
        return kind(
            **values,
            mass_basis=_enum(mass_basis, MaterialBasis),
            composition_basis=_enum(composition_basis, MaterialBasis),
            normalized_basis=_enum(normalized_basis, MaterialBasis),
            fixed_carbon_component_kind=_enum(fixed_kind, MaterialComponentKind),
            volatile_matter_component_kind=_enum(volatile_kind, MaterialComponentKind),
            moisture_evidence=controls["moisture_evidence"].isChecked() and evidence_reference is not None,
            conversion_evidence=controls["conversion_evidence"].isChecked() and evidence_reference is not None,
        )

    def _electricity(self, enterprise_id: str, period: AccountingPeriod) -> tuple[ElectricityConsumptionDetail, ...]:
        details: list[ElectricityConsumptionDetail] = []
        for row in self._electricity_rows:
            detail = row.build(enterprise_id, period)
            if detail is not None:
                details.append(detail)
        result = tuple(details)
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

    def _selected_heat_parameter_value(self) -> ParameterValue:
        factor_id = self.heat_factor_selector.currentData()
        if not isinstance(factor_id, str) or factor_id not in self._heat_factor_records:
            raise DomainValidationError("热力输入缺少可用的标准热力参数 [GEN-PAR-NO-APPLICABLE-VALUE]")
        if self._parameter_resolver is None:
            raise DomainValidationError("热力输入暂时无法取得标准参数 [CAR-VAL-PARAMETER-RESOLVER-MISSING]")

        base_resolution = self._parameter_resolver.resolve(self._heat_resolution_context())
        selected_reason = self.heat_factor_selection_reason.text().strip()
        if base_resolution.recommended is not None and base_resolution.recommended.factor_id == factor_id and not base_resolution.blocked:
            resolution = base_resolution
        elif not selected_reason:
            raise DomainValidationError("选择其他热力参数时必须填写选择理由 [GEN-PAR-CONFIRMATION-REASON]")
        else:
            resolution = self._parameter_resolver.resolve(
                self._heat_resolution_context(
                    confirmed_factor_id=factor_id,
                    confirmation_reason=selected_reason,
                )
            )
        if resolution.blocked or resolution.recommended is None:
            first_error = next((problem for problem in resolution.warnings if problem.level.value == "ERROR"), None)
            if first_error is not None:
                raise DomainValidationError(f"{first_error.message} [{first_error.code}]")
            raise DomainValidationError("当前热力因子选择无法形成参数快照 [GEN-PAR-NO-APPLICABLE-VALUE]")
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

    def _heat(self, prefix: str, factor: ParameterValue | None) -> tuple[HeatInput, ...]:
        amount = _value(self._fields[f"{prefix}_amount"])
        if amount is None:
            return ()
        if factor is None:
            raise DomainValidationError(f"{prefix} 已填写热力总量但没有选择排放因子 [GEN-VAL-REQUIRED-MISSING]")
        steam_kind = _enum(
            (self._heat_steam_kind if prefix == "heat" else self._exported_heat_steam_kind).currentData(),
            SteamKind,
        )
        return (
            HeatInput(
                _value(self._fields[f"{prefix}_id"]) or f"{prefix}-1",
                amount,
                _value(self._fields[f"{prefix}_enthalpy"]),
                factor,
                steam_kind=steam_kind,
                pressure_mpa=_value(self._fields[f"{prefix}_pressure"]),
                temperature_c=_value(self._fields[f"{prefix}_temperature"]),
            ),
        )

    def _exported_electricity(self) -> tuple[ElectricityOutputLine, ...]:
        amount = _value(self._fields["exported_electricity_amount"])
        if amount is None:
            return ()
        return (
            ElectricityOutputLine(
                _value(self._fields["exported_electricity_id"]) or "exported-electricity-1",
                amount,
            ),
        )

    def _input(self) -> CarbonMaterialInput:
        self._calculation_index += 1
        period = self._period()
        enterprise_name = self.enterprise_name.text().strip()
        enterprise_id = "enterprise.current"
        has_heat = _value(self._fields["heat_amount"]) is not None or _value(self._fields["exported_heat_amount"]) is not None
        heat_factor = self._selected_heat_parameter_value() if has_heat else None
        return CarbonMaterialInput(
            input_id=f"input.{self._calculation_index}",
            enterprise_id=enterprise_id,
            enterprise_name=enterprise_name,
            period=period,
            boundary_confirmed=self.boundary_confirmed.isChecked(),
            boundary_component_ids=("main-production-system",),
            other_activity_present=self.other_activity_present.isChecked(),
            transport_present=self.transport_present.isChecked(),
            source_states=self._source_states(),
            fuel_inputs=self._fuel(),
            calcination=self._process("calcination", CalcinationInput),
            baking=self._process("baking", BakingInput),
            graphitization=self._process("graphitization", GraphitizationInput),
            fume_incineration=self._process("fume", FumeIncinerationInput),
            fgd=self._process("fgd", FGDInput),
            electricity_details=self._electricity(enterprise_id, period),
            exported_electricity=self._exported_electricity(),
            purchased_heat=self._heat("heat", heat_factor),
            exported_heat=self._heat("exported_heat", heat_factor),
        )

    def _install_dirty_tracking(self) -> None:
        for widget in self.findChildren(QWidget):
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

    def _mark_input_dirty(self, *_args: object) -> None:
        self._input_dirty = True
        self._validation_count_override = None
        self._calculation_has_result = False
        if hasattr(self, "result_card"):
            self.result_card.setVisible(False)
            self.process_card.setVisible(False)
            self.result_line_details.setVisible(False)
            self.view_breakdown_button.setText("查看分项结果")
            self.view_process_button.setText("查看计算过程")
        self._refresh_live_feedback()

    def _reset_for_new_accounting(self) -> None:
        """Restore every G06 control to the initial new-accounting state."""

        self._calculation_index = 0
        self.enterprise_name.clear()
        self.period_type.setCurrentIndex(0)
        self.period_year.setValue(2025)
        self.period_month.setValue(1)
        self.boundary_confirmed.setChecked(False)
        self.other_activity_present.setChecked(False)
        self.transport_present.setChecked(False)
        for combo in self._source_statuses.values():
            combo.setCurrentIndex(0)
        for widget in self._fields.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
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
        self.heat_factor_selection_reason.clear()
        for row in tuple(self._electricity_rows):
            self._remove_electricity_row(row)
        self._add_electricity_row()
        self._refresh_heat_factor_details()
        self.validation_list.clear()
        self.quality_card.setVisible(False)
        self.process_card.setVisible(False)
        self.result_card.setVisible(False)
        self.result_total.setText("未计算")
        self.result_status.setText("状态：尚未计算")
        self.result_breakdown.clear()
        self.result_line_details.clear()
        self.result_line_details.setVisible(False)
        self.view_breakdown_button.setText("查看分项结果")
        self.view_process_button.setText("查看计算过程")
        self.parameter_snapshot_summary.setText("尚未计算，暂无参数快照。")
        self.trace_output.setText("点击“计算排放量”后显示分项计算结果。")
        self.trace_professional_details.setText("打开“显示专业详情”后可查看公式和变量代入信息。")
        self.validation_professional_details.setText("打开“显示专业详情”后可查看原始校验信息和内部定位。")
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

    @classmethod
    def _business_problem_message(cls, problem: object) -> str:
        code = str(getattr(problem, "code", ""))
        fixed_messages = {
            "CAR-VAL-MATERIAL-BASIS-CONVERSION": "材料数据的口径或换算资料不完整，当前不能直接计算。请补充数据来源、换算依据和报告/台账编号或来源说明。",
            "CAR-VAL-MATERIAL-BASIS-CONSISTENCY": "质量数据和成分含量的数据口径不一致，当前不能直接计算。请统一两项口径并提供换算依据。",
            "CAR-VAL-MATERIAL-COMPONENT-KIND": "固定碳或挥发分字段性质与标准要求不一致，请检查对应字段。",
            "CAR-VAL-BOUNDARY-UNCONFIRMED": "核算边界尚未确认，请确认本次核算边界。",
            "CAR-VAL-OTHER-STANDARD": "发现当前标准未覆盖的其他活动或上下游运输，请改用适用标准核算。",
            "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE": "非化石电力明细缺少有效证明材料，无法采用相应参数。",
            "CAR-VAL-STEAM-STATE": "购入热力的蒸汽状态资料不完整，请补充焓值或压力等必要数据。",
            "CAR-VAL-PARAMETER-RESOLVER-MISSING": "暂时无法取得适用的标准参数，请检查参数数据后重试。",
            "GEN-PAR-NO-APPLICABLE-VALUE": "当前明细没有可用的适用参数，请补充或检查参数资料。",
            "GEN-VAL-REQUIRED-MISSING": "必填信息不完整，请补充后再试。",
        }
        if code in fixed_messages:
            return fixed_messages[code]
        return cls._sanitize_business_message(str(getattr(problem, "message", "当前数据需要检查。")))

    def _add_validation_problem(self, problem: object, technical_lines: list[str]) -> None:
        level = str(getattr(getattr(problem, "level", None), "value", "ERROR"))
        code = str(getattr(problem, "code", "未提供代码"))
        raw_message = str(getattr(problem, "message", "当前数据需要检查。"))
        item = QListWidgetItem(
            f"{self._problem_level_label(problem)}：{self._business_problem_message(problem)}"
        )
        item.setData(
            Qt.ItemDataRole.UserRole,
            self._source_id_for_problem_field(getattr(problem, "field_id", None)),
        )
        self.validation_list.addItem(item)
        technical_lines.append(f"{level}：{raw_message} [{code}]")

    def _run_calculation(self) -> None:
        self.validation_list.clear()
        self._known_source_errors.clear()
        self._validation_count_override = None
        self._calculation_has_result = False
        self.result_card.setVisible(False)
        self.process_card.setVisible(False)
        self.quality_card.setVisible(False)
        self.result_line_details.setVisible(False)
        self.view_breakdown_button.setText("查看分项结果")
        self.view_process_button.setText("查看计算过程")
        self._refresh_source_cards()
        technical_lines: list[str] = []
        if not self.enterprise_name.text().strip():
            item = QListWidgetItem("错误：企业名称为必填项，请填写企业名称。")
            self.validation_list.addItem(item)
            technical_lines.append("ERROR：企业名称为必填项 [GEN-VAL-REQUIRED-MISSING]")
            self.validation_professional_details.setText("\n".join(technical_lines))
            self.result_total.setText("存在输入错误")
            self.result_status.setText("状态：存在需要处理的问题")
            self.quality_card.setVisible(True)
            self._validation_count_override = (1, 0)
            self._refresh_live_feedback()
            return
        try:
            outcome = self.calculator.calculate(self._input())
        except (DomainValidationError, InvalidOperation, ValueError) as exc:
            raw_message = str(exc)
            self.validation_list.addItem(f"错误：{self._sanitize_business_message(raw_message)}")
            technical_lines.append(f"ERROR：{raw_message}")
            self.validation_professional_details.setText("\n".join(technical_lines))
            self.result_total.setText("存在输入错误")
            self.result_status.setText("状态：存在需要处理的问题")
            self.quality_card.setVisible(True)
            self._validation_count_override = (1, 0)
            self._refresh_live_feedback()
            return
        self._known_source_errors = self._source_ids_for_domain_errors(outcome.problems)
        self._refresh_source_cards()
        error_count = 0
        reminder_count = 0
        for problem in outcome.problems:
            self._add_validation_problem(problem, technical_lines)
            level = str(getattr(getattr(problem, "level", None), "value", "ERROR"))
            if level == "ERROR":
                error_count += 1
            elif level in {"WARNING", "INFO"}:
                reminder_count += 1
        if not outcome.problems:
            self.validation_list.addItem(QListWidgetItem("信息：数据检查通过。"))
            technical_lines.append("INFO：数据检查通过。")
        self.validation_professional_details.setText("\n".join(technical_lines) if technical_lines else "暂无原始校验信息。")
        self.quality_card.setVisible(bool(outcome.problems))
        self._validation_count_override = (error_count, reminder_count)
        if outcome.result is None or outcome.blocked:
            self.result_total.setText("存在错误，未形成成功结果")
            self.result_status.setText("状态：存在需要处理的问题")
            self.quality_card.setVisible(True)
            self._refresh_live_feedback()
            return
        self._calculation_has_result = True
        self.result_card.setVisible(True)
        self.result_total.setText(
            f"总排放量 ET：{_display_amount(outcome.result.total_amount, outcome.result.total_unit)}"
        )
        by_id = {line.line_id: line.amount for line in outcome.result.lines}
        status_label = (
            "已完成（含提醒）"
            if outcome.record is not None and outcome.record.status is RecordStatus.COMPLETED_WITH_WARNINGS
            else "已完成"
            if outcome.record is not None
            else "已计算但存在需要处理的问题"
        )
        self.result_status.setText(f"状态：{status_label}")
        self.result_breakdown.setText(
            f"直接排放 ES：{_display_amount(by_id.get('CAR-FLD-DIRECT-RESULT', Decimal('0')), outcome.result.total_unit)}；"
            f"间接排放 EI：{_display_amount(by_id.get('CAR-FLD-INDIRECT-RESULT', Decimal('0')), outcome.result.total_unit)}；"
            f"记录：{'已生成不可编辑核算记录' if outcome.record is not None else '未生成记录'}"
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
        self.result_line_details.setText(
            "分项结果：\n" + "\n".join(line_details) if line_details else "分项结果：本次没有单独排放源明细。"
        )
        self.parameter_snapshot_summary.setText(f"已形成 {len(outcome.parameter_snapshots)} 条参数快照（只读）。")
        if outcome.record is not None:
            self._input_dirty = False
            self.record_created.emit(outcome.record.record_id)
        trace_lines = [
            f"{trace.formula_id}：{trace.substitution} = {_display_amount(trace.amount, 'tCO2')}"
            for trace in outcome.traces
        ]
        self.trace_professional_details.setText("\n".join(trace_lines) if trace_lines else "无可展示计算过程。")
        self.trace_output.setText(
            "计算过程已完成；如需查看公式和变量代入信息，请打开“显示专业详情”。"
            if trace_lines
            else "本次没有形成可展示的计算明细。"
        )
        self._refresh_live_feedback()


NewAccountingPage = CarbonMaterialAccountingPage


__all__ = ["CarbonMaterialAccountingPage", "NewAccountingPage"]
