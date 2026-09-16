"""G06 Qt page for hand-entered GB/T 32151.34 calculations.

The page exposes G06 inputs and G05-backed parameter selection while keeping calculation rules in the Domain layer.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
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
from packages.core.models import AccountingPeriod, ReviewStatus, ValueType
from packages.core.parameter_resolution import ParameterResolutionContext

from .pages import BasePage, Navigate, _card
from .view_models import AppRoute


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


def _field(parent: QWidget, object_name: str, placeholder: str = "") -> QLineEdit:
    edit = QLineEdit(parent)
    edit.setObjectName(object_name)
    edit.setPlaceholderText(placeholder)
    return edit


def _value(edit: QLineEdit) -> str | None:
    text = edit.text().strip()
    return text or None


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

class _ElectricityRow(QWidget):
    def __init__(self, index: int, remove: Callable[[QWidget], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"electricityRow{index}")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.detail_id = _field(self, f"electricityDetailId{index}", f"detail-{index}")
        self.detail_id.setText(f"electricity-detail-{index}")
        self.amount = _field(self, f"electricityAmount{index}", "MWh")
        self.acquisition = QComboBox(self)
        self.acquisition.setObjectName(f"electricityAcquisition{index}")
        self.acquisition.addItem("外购", ElectricityAcquisitionMode.PURCHASED)
        self.acquisition.addItem("自发自用", ElectricityAcquisitionMode.SELF_CONSUMED)
        self.attribute = QComboBox(self)
        self.attribute.setObjectName(f"electricityAttribute{index}")
        self.attribute.addItem("常规电力（电网电力）", ElectricityAttribute.ORDINARY)
        self.attribute.addItem("非化石能源电力", ElectricityAttribute.NONFOSSIL)
        self.attribute.addItem("化石能源电力", ElectricityAttribute.FOSSIL)
        self.proof_type = QComboBox(self)
        self.proof_type.setObjectName(f"electricityProofType{index}")
        for value, label in (
            (ElectricityProofType.NONE, "无证明"),
            (ElectricityProofType.CONTRACT_AND_SETTLEMENT, "合同及结算凭证"),
            (ElectricityProofType.GEC, "GEC"),
            (ElectricityProofType.MONTHLY_ORIGINAL_RECORD, "月度原始记录"),
        ):
            self.proof_type.addItem(label, value)
        self.proof_status = QComboBox(self)
        self.proof_status.setObjectName(f"electricityProofStatus{index}")
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
        self.parameter_status = QLabel("参数状态：待录入", detail_panel)
        self.parameter_status.setObjectName(f"electricityParameterStatus{index}")
        self.parameter_status.setWordWrap(True)
        self.parameter_factor = QLabel("采用因子：尚未解析", detail_panel)
        self.parameter_factor.setObjectName(f"electricityParameterFactor{index}")
        self.parameter_factor.setWordWrap(True)
        self.parameter_source = QLabel("来源：尚未解析", detail_panel)
        self.parameter_source.setObjectName(f"electricityParameterSource{index}")
        self.parameter_source.setWordWrap(True)
        self.parameter_reason = QLabel("选择理由：尚未解析", detail_panel)
        self.parameter_reason.setObjectName(f"electricityParameterReason{index}")
        self.parameter_reason.setWordWrap(True)
        for widget in (self.parameter_status, self.parameter_factor, self.parameter_source, self.parameter_reason):
            detail_layout.addWidget(widget)
        layout.addWidget(detail_panel, 1, 0, 1, 7)

    def show_parameter_state(self, status: str, factor: str, source: str, reason: str) -> None:
        self.parameter_status.setText(status)
        self.parameter_factor.setText(factor)
        self.parameter_source.setText(source)
        self.parameter_reason.setText(reason)

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

    def __init__(
        self,
        catalog_service: CatalogQueryService | None = None,
        calculator: CarbonMaterialCalculator | None = None,
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
            calculator = CarbonMaterialCalculator(parameter_resolver=resolver)
        self.calculator = calculator
        self.standard_id = standard_id
        self._calculation_index = 0
        self._electricity_rows: list[_ElectricityRow] = []
        self._source_statuses: dict[str, QComboBox] = {}
        self._fields: dict[str, QLineEdit] = {}
        self._material_controls: dict[str, dict[str, QWidget]] = {}
        self._heat_factor_records = {}
        self._build_page()

    def set_standard_id(self, standard_id: str) -> None:
        self.standard_id = standard_id
        self.standard_id_label.setText(standard_id)
        if hasattr(self, "heat_factor_selector"):
            self._refresh_heat_factor_details()

    def _build_page(self) -> None:
        self.add_header("新建核算", "GB/T 32151.34-2024 炭素材料生产企业手工核算；结果仅在本阶段内存验证。")

        identity, identity_layout = _card("01 核算信息", self)
        form = QFormLayout()
        self.standard_id_label = QLabel(self.standard_id, identity)
        self.standard_id_label.setObjectName("accountingStandardId")
        form.addRow("核算标准", self.standard_id_label)
        self.enterprise_name = _field(identity, "enterpriseNameInput", "企业名称")
        form.addRow("企业名称", self.enterprise_name)
        self.period_type = QComboBox(identity)
        self.period_type.setObjectName("accountingPeriodType")
        self.period_type.addItem("年度", PeriodType.ANNUAL)
        self.period_type.addItem("月度（内部周期结果）", PeriodType.MONTHLY)
        self.period_type.currentIndexChanged.connect(lambda _index: self._refresh_heat_factor_details())
        form.addRow("核算期间", self.period_type)
        period_row = QWidget(identity)
        period_layout = QHBoxLayout(period_row)
        period_layout.setContentsMargins(0, 0, 0, 0)
        self.period_year = QSpinBox(period_row)
        self.period_year.setObjectName("accountingPeriodYear")
        self.period_year.setRange(2000, 2100)
        self.period_year.setValue(2025)
        self.period_year.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        self.period_month = QSpinBox(period_row)
        self.period_month.setObjectName("accountingPeriodMonth")
        self.period_month.setRange(1, 12)
        self.period_month.setValue(1)
        self.period_month.valueChanged.connect(lambda _value: self._refresh_heat_factor_details())
        period_layout.addWidget(self.period_year)
        period_layout.addWidget(self.period_month)
        form.addRow("年份 / 月份", period_row)
        identity_layout.addLayout(form)
        self.body_layout.addWidget(identity)

        boundary, boundary_layout = _card("02 核算边界", self)
        self.boundary_confirmed = QCheckBox("已确认法人企业/独立核算单位及生产系统边界", boundary)
        self.boundary_confirmed.setObjectName("boundaryConfirmedCheckBox")
        boundary_layout.addWidget(self.boundary_confirmed)
        boundary_hint = QLabel("边界按标准第4.1条结构化确认；未确认不能计算。", boundary)
        boundary_hint.setWordWrap(True)
        boundary_layout.addWidget(boundary_hint)
        self.other_activity_present = QCheckBox("存在本标准未覆盖的其他行业活动（需使用其他标准）", boundary)
        self.other_activity_present.setObjectName("otherIndustryActivityCheckBox")
        boundary_layout.addWidget(self.other_activity_present)
        self.transport_present = QCheckBox("存在上下游运输（需使用其他标准）", boundary)
        self.transport_present.setObjectName("upstreamDownstreamTransportCheckBox")
        boundary_layout.addWidget(self.transport_present)
        self.body_layout.addWidget(boundary)

        sources, sources_layout = _card("03 排放源识别", self)
        source_grid = QGridLayout()
        source_grid.addWidget(QLabel("排放源"), 0, 0)
        source_grid.addWidget(QLabel("本次状态"), 0, 1)
        for row, (source_id, label) in enumerate(SOURCE_LABELS.items(), 1):
            source_grid.addWidget(QLabel(label), row, 0)
            combo = QComboBox(sources)
            combo.setObjectName(f"sourceStatus_{source_id}")
            combo.addItem("不涉及", EmissionSourceStatus.NOT_INVOLVED)
            combo.addItem("涉及", EmissionSourceStatus.INVOLVED)
            combo.addItem("待确认", EmissionSourceStatus.UNCONFIRMED)
            self._source_statuses[source_id] = combo
            source_grid.addWidget(combo, row, 1)
        sources_layout.addLayout(source_grid)
        self.body_layout.addWidget(sources)

        activity, activity_layout = _card("04 活动数据", self)
        self._build_fuel_section(activity_layout)
        self._build_process_section(activity_layout, "煅烧（P01）", "calcination", ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"))
        self._build_process_section(activity_layout, "焙烧/炭化（P02）", "baking", ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"))
        self._build_process_section(activity_layout, "石墨化（P03）", "graphitization", ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"))
        self._build_process_section(activity_layout, "烟气焚烧治理（P04A）", "fume", ("q", "qvar", "hm", "fch", "fox", "duration"))
        self._build_process_section(activity_layout, "烟气脱硫净化（P04B）", "fgd", ("cal", "i", "ef1", "tr"))
        self._build_electricity_section(activity_layout)
        self._build_output_electricity_section(activity_layout)
        self._build_heat_section(activity_layout)
        self._build_output_heat_section(activity_layout)
        self.body_layout.addWidget(activity)

        parameter_card, parameter_layout = _card("05 参数与排放因子", self)
        parameter_label = QLabel("参数选择器接入 G05：候选值、推荐/其他适用/历史分类、来源、审核状态和选择理由均在录入区显示。", parameter_card)
        parameter_label.setWordWrap(True)
        parameter_layout.addWidget(parameter_label)
        self.parameter_selection_status = QLabel("尚未选择参数。", parameter_card)
        self.parameter_selection_status.setObjectName("parameterSelectionStatus")
        self.parameter_selection_status.setWordWrap(True)
        parameter_layout.addWidget(self.parameter_selection_status)
        self.parameter_snapshot_summary = QLabel("尚未计算，暂无参数快照。", parameter_card)
        self.parameter_snapshot_summary.setObjectName("parameterSnapshotSummary")
        self.parameter_snapshot_summary.setWordWrap(True)
        parameter_layout.addWidget(self.parameter_snapshot_summary)
        self.body_layout.addWidget(parameter_card)
        self._refresh_heat_factor_details()

        process_card, process_layout = _card("06 计算过程", self)
        self.trace_output = QLabel("点击“计算排放量”后显示公式、变量和分项结果。", process_card)
        self.trace_output.setObjectName("calculationTrace")
        self.trace_output.setWordWrap(True)
        process_layout.addWidget(self.trace_output)
        self.body_layout.addWidget(process_card)

        result_card, result_layout = _card("07 核算结果", self)
        self.result_total = QLabel("未计算", result_card)
        self.result_total.setObjectName("calculationTotal")
        result_layout.addWidget(self.result_total)
        self.result_breakdown = QLabel("", result_card)
        self.result_breakdown.setObjectName("calculationBreakdown")
        self.result_breakdown.setWordWrap(True)
        result_layout.addWidget(self.result_breakdown)
        self.body_layout.addWidget(result_card)

        quality_card, quality_layout = _card("08 数据质量检查", self)
        self.validation_list = QListWidget(quality_card)
        self.validation_list.setObjectName("calculationValidationList")
        quality_layout.addWidget(self.validation_list)
        self.body_layout.addWidget(quality_card)

        action_row = QHBoxLayout()
        self.check_button = QPushButton("检查数据", self)
        self.check_button.setObjectName("checkAccountingButton")
        self.check_button.clicked.connect(self._run_calculation)
        self.calculate_button = QPushButton("计算排放量", self)
        self.calculate_button.setObjectName("calculateAccountingButton")
        self.calculate_button.clicked.connect(self._run_calculation)
        action_row.addWidget(self.check_button)
        action_row.addWidget(self.calculate_button)
        action_row.addStretch(1)
        self.body_layout.addLayout(action_row)
        self.body_layout.addStretch(1)

    def _build_fuel_section(self, parent_layout: QVBoxLayout) -> None:
        row = QWidget(self)
        layout = QGridLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        labels = ("燃料ID", "路径", "活动量", "单位热值/质量含碳量", "碳氧化率")
        for column, label in enumerate(labels):
            layout.addWidget(QLabel(label), 0, column)
        self._fields["fuel_id"] = _field(row, "fuelIdInput", "natural-gas")
        self._fields["fuel_path"] = QComboBox(row)  # type: ignore[assignment]
        self._fields["fuel_path"].setObjectName("fuelPathInput")  # type: ignore[union-attr]
        for path, label in ((FuelPath.VOLUME, "体积"), (FuelPath.MASS, "质量"), (FuelPath.HEAT, "热量")):
            self._fields["fuel_path"].addItem(label, path)  # type: ignore[union-attr]
        self._fields["fuel_activity"] = _field(row, "fuelActivityInput")
        self._fields["fuel_carbon"] = _field(row, "fuelCarbonInput")
        self._fields["fuel_oxidation"] = _field(row, "fuelOxidationInput")
        for column, key in enumerate(("fuel_id", "fuel_path", "fuel_activity", "fuel_carbon", "fuel_oxidation")):
            layout.addWidget(self._fields[key], 1, column)
        parent_layout.addWidget(row)

    def _build_process_section(self, parent_layout: QVBoxLayout, title: str, prefix: str, fields: tuple[str, ...]) -> None:
        label = QLabel(title, self)
        label.setObjectName(f"{prefix}SectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        for field in fields:
            edit = _field(row, f"{prefix}_{field}")
            self._fields[f"{prefix}.{field}"] = edit
            form.addRow(field, edit)
        parent_layout.addWidget(row)

        if prefix not in {"calcination", "baking", "graphitization"}:
            return

        metadata = QWidget(self)
        metadata_form = QFormLayout(metadata)
        basis_options = (
            (MaterialBasis.UNKNOWN, "未确认"),
            (MaterialBasis.RECEIVED, "收到基"),
            (MaterialBasis.DRY, "干燥基"),
            (MaterialBasis.OTHER_DOCUMENTED, "其他有证基准"),
        )
        mass_basis = QComboBox(metadata)
        mass_basis.setObjectName(f"{prefix}_massBasisSelector")
        composition_basis = QComboBox(metadata)
        composition_basis.setObjectName(f"{prefix}_compositionBasisSelector")
        normalized_basis = QComboBox(metadata)
        normalized_basis.setObjectName(f"{prefix}_normalizedBasisSelector")
        for combo in (mass_basis, composition_basis, normalized_basis):
            for value, label_text in basis_options:
                combo.addItem(label_text, value)
        component_options = (
            (MaterialComponentKind.UNKNOWN, "未确认"),
            (MaterialComponentKind.FIXED_CARBON, "固定碳"),
            (MaterialComponentKind.VOLATILE_MATTER, "挥发分"),
            (MaterialComponentKind.TOTAL_CARBON, "总碳（本字段不可直接采用）"),
        )
        fixed_carbon_component_kind = QComboBox(metadata)
        fixed_carbon_component_kind.setObjectName(f"{prefix}_fixedCarbonComponentKindSelector")
        volatile_matter_component_kind = QComboBox(metadata)
        volatile_matter_component_kind.setObjectName(f"{prefix}_volatileMatterComponentKindSelector")
        for combo in (fixed_carbon_component_kind, volatile_matter_component_kind):
            for value, label_text in component_options:
                combo.addItem(label_text, value)
        moisture_evidence = QCheckBox("已有水分/基准证明", metadata)
        moisture_evidence.setObjectName(f"{prefix}_moistureEvidenceCheckBox")
        conversion_evidence = QCheckBox("已有收到基换算证明", metadata)
        conversion_evidence.setObjectName(f"{prefix}_conversionEvidenceCheckBox")
        evidence_reference = _field(metadata, f"{prefix}_basisEvidenceReferenceInput", "证明编号或来源定位（非收到基必填）")
        self._material_controls[prefix] = {
            "mass_basis": mass_basis,
            "composition_basis": composition_basis,
            "normalized_basis": normalized_basis,
            "fixed_carbon_component_kind": fixed_carbon_component_kind,
            "volatile_matter_component_kind": volatile_matter_component_kind,
            "moisture_evidence": moisture_evidence,
            "conversion_evidence": conversion_evidence,
            "evidence_reference": evidence_reference,
        }
        metadata_form.addRow("物料基准", mass_basis)
        metadata_form.addRow("成分性质基准", composition_basis)
        metadata_form.addRow("归一化基准", normalized_basis)
        metadata_form.addRow("固定碳字段性质", fixed_carbon_component_kind)
        metadata_form.addRow("挥发分字段性质", volatile_matter_component_kind)
        metadata_form.addRow("证据", moisture_evidence)
        metadata_form.addRow("换算证明", conversion_evidence)
        metadata_form.addRow("证明定位", evidence_reference)
        parent_layout.addWidget(metadata)

    def _build_electricity_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("购入电力/多条电力明细（I01；取得方式与电力属性独立）", self)
        label.setObjectName("electricitySectionTitle")
        parent_layout.addWidget(label)
        header = QLabel("明细ID | 电量 MWh | 取得方式 | 电力属性 | 证明类型 | 证明状态 | 操作", self)
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
        self.electricity_rows_layout.addWidget(row)
        row.detail_id.textChanged.connect(lambda _text: self._refresh_electricity_rows())
        row.amount.textChanged.connect(lambda _text: self._refresh_electricity_rows())
        for combo in (row.acquisition, row.attribute, row.proof_type, row.proof_status):
            combo.currentIndexChanged.connect(lambda _index: self._refresh_electricity_rows())

    def _remove_electricity_row(self, row: QWidget) -> None:
        if row in self._electricity_rows:
            self._electricity_rows.remove(row)
            self.electricity_rows_layout.removeWidget(row)
            row.deleteLater()

    def _build_output_electricity_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("输出电力（I03；从间接排放中抵扣）", self)
        label.setObjectName("exportedElectricitySectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        self._fields["exported_electricity_id"] = _field(row, "exportedElectricityLineIdInput", "exported-electricity-1")
        self._fields["exported_electricity_amount"] = _field(row, "exportedElectricityAmountInput", "MWh")
        form.addRow("明细ID", self._fields["exported_electricity_id"])
        form.addRow("输出电量 MWh", self._fields["exported_electricity_amount"])
        parent_layout.addWidget(row)

    def _build_heat_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("购入热力/动力（I02）", self)
        label.setObjectName("heatSectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        for key, label_text in (
            ("heat_id", "明细ID"),
            ("heat_amount", "动力总量 kg"),
            ("heat_enthalpy", "蒸汽焓值 kJ/kg"),
            ("heat_pressure", "饱和/过热蒸汽压力 MPa"),
            ("heat_temperature", "过热蒸汽温度 C"),
        ):
            edit = _field(row, f"{key}Input")
            self._fields[key] = edit
            form.addRow(label_text, edit)
        self._heat_steam_kind = QComboBox(row)
        self._heat_steam_kind.setObjectName("heatSteamKindSelector")
        self._heat_steam_kind.addItem("饱和蒸汽（附录C.4）", SteamKind.SATURATED)
        self._heat_steam_kind.addItem("过热蒸汽（附录C.5）", SteamKind.SUPERHEATED)
        form.addRow("蒸汽状态", self._heat_steam_kind)
        self.heat_factor_selector = QComboBox(row)
        self.heat_factor_selector.setObjectName("heatFactorSelector")
        self.heat_factor_selector.currentIndexChanged.connect(self._refresh_heat_factor_details)
        form.addRow("热力因子候选", self.heat_factor_selector)
        self.heat_factor_metadata = QLabel("尚未加载热力因子候选值。", row)
        self.heat_factor_metadata.setObjectName("heatFactorMetadata")
        self.heat_factor_metadata.setWordWrap(True)
        form.addRow("候选来源与审核", self.heat_factor_metadata)
        self.heat_factor_selection_reason = _field(row, "heatFactorSelectionReasonInput", "自动推荐理由或人工确认理由")
        form.addRow("选择理由", self.heat_factor_selection_reason)
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
        for key, label_text in (
            ("exported_heat_id", "明细ID"),
            ("exported_heat_amount", "动力总量 kg"),
            ("exported_heat_enthalpy", "蒸汽焓值 kJ/kg"),
            ("exported_heat_pressure", "饱和/过热蒸汽压力 MPa"),
            ("exported_heat_temperature", "过热蒸汽温度 C"),
        ):
            edit = _field(row, exported_heat_object_names[key])
            self._fields[key] = edit
            form.addRow(label_text, edit)
        self._exported_heat_steam_kind = QComboBox(row)
        self._exported_heat_steam_kind.setObjectName("exportedHeatSteamKindSelector")
        self._exported_heat_steam_kind.addItem("饱和蒸汽（附录C.4）", SteamKind.SATURATED)
        self._exported_heat_steam_kind.addItem("过热蒸汽（附录C.5）", SteamKind.SUPERHEATED)
        form.addRow("蒸汽状态", self._exported_heat_steam_kind)
        hint = QLabel("I04 与 I02 共用上方 G05 热力因子选择器；输出热力同样必须标记排放源为“涉及”。", row)
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
                f"{category_label} | {record.factor_id} | {record.normalized_value} {record.normalized_unit}",
                record.factor_id,
            )
        if not records:
            self.heat_factor_selector.addItem("目录暂无可用热力因子候选值", None)
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
            self.heat_factor_metadata.setText("目录暂无可用热力因子；输入热力时将由 G05 明确阻断，不能静默猜值。")
            if hasattr(self, "parameter_selection_status"):
                self.parameter_selection_status.setText("热力参数：无可用目录候选值。")
            return
        record = self._heat_factor_records[factor_id]
        category = self.catalog_service.value_category(record)
        metadata = (
            f"{self.catalog_service.value_category_label(category)}；因子 {record.factor_id}；"
            f"值 {record.normalized_value} {record.normalized_unit}；来源 {record.source_id}；"
            f"审核 {_review_status_label(record.review_status)}；定位 {record.source_location}"
        )
        self.heat_factor_metadata.setText(metadata)
        if self._parameter_resolver is not None:
            try:
                resolution = self._parameter_resolver.resolve(self._heat_resolution_context())
            except (DomainValidationError, ValueError):
                resolution = None
            if resolution is not None and resolution.recommended is not None and resolution.recommended.factor_id == factor_id:
                if not self.heat_factor_selection_reason.text().strip():
                    self.heat_factor_selection_reason.setText(resolution.selection_reason)
                status = f"推荐选择：{resolution.selection_reason}"
            else:
                status = "当前候选不是本核算期间的自动推荐值；选择它必须填写人工确认理由。"
            if hasattr(self, "parameter_selection_status"):
                self.parameter_selection_status.setText(status)
    def _period(self) -> AccountingPeriod:
        year = self.period_year.value()
        if _enum(self.period_type.currentData(), PeriodType) is PeriodType.ANNUAL:
            return AccountingPeriod(PeriodType.ANNUAL, __import__("datetime").date(year, 1, 1), __import__("datetime").date(year, 12, 31))
        month = self.period_month.value()
        import calendar
        return AccountingPeriod(PeriodType.MONTHLY, __import__("datetime").date(year, month, 1), __import__("datetime").date(year, month, calendar.monthrange(year, month)[1]))

    def _source_states(self) -> tuple[EmissionSourceState, ...]:
        return tuple(EmissionSourceState(source_id, _enum(combo.currentData(), EmissionSourceStatus)) for source_id, combo in self._source_statuses.items())

    def _fuel(self) -> tuple[FuelInput, ...]:
        fuel_id = _value(self._fields["fuel_id"])
        values = (_value(self._fields["fuel_activity"]), _value(self._fields["fuel_carbon"]), _value(self._fields["fuel_oxidation"]))
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
        values = {field: _value(self._fields[f"{prefix}.{field}"]) for field in field_names}
        if all(value is None for value in values.values()):
            return None
        controls = self._material_controls.get(prefix)
        if controls is None:
            return kind(**values)
        evidence_reference = _value(controls["evidence_reference"])
        return kind(
            **values,
            mass_basis=_enum(controls["mass_basis"].currentData(), MaterialBasis),
            composition_basis=_enum(controls["composition_basis"].currentData(), MaterialBasis),
            normalized_basis=_enum(controls["normalized_basis"].currentData(), MaterialBasis),
            fixed_carbon_component_kind=_enum(controls["fixed_carbon_component_kind"].currentData(), MaterialComponentKind),
            volatile_matter_component_kind=_enum(controls["volatile_matter_component_kind"].currentData(), MaterialComponentKind),
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
            for row in self._electricity_rows:
                row.show_parameter_state(
                    "参数状态：等待完整明细",
                    "采用因子：尚未解析",
                    "来源：尚未解析",
                    "选择理由：补齐明细后解析",
                )

    def _render_electricity_parameter_states(self, details: tuple[ElectricityConsumptionDetail, ...]) -> None:
        waiting = (
            "参数状态：待录入",
            "采用因子：尚未解析",
            "来源：尚未解析",
            "选择理由：录入电量后按本条明细独立解析",
        )
        rows_by_id = {row.detail_id.text().strip(): row for row in self._electricity_rows}
        for row in self._electricity_rows:
            row.show_parameter_state(*waiting)
        if not details:
            return
        if self._parameter_resolver is None:
            for row in self._electricity_rows:
                row.show_parameter_state(
                    "参数状态：参数服务不可用",
                    "采用因子：未解析",
                    "来源：无独立参数快照",
                    "选择理由：无法连接 G05 参数解析服务",
                )
            return
        try:
            resolutions = self._parameter_resolver.resolve_electricity_details(
                details,
                snapshot_at=datetime.now(timezone.utc),
            )
        except (DomainValidationError, InvalidOperation, KeyError, ValueError) as exc:
            for row in self._electricity_rows:
                row.show_parameter_state(
                    "参数状态：解析失败",
                    "采用因子：未解析",
                    "来源：无独立参数快照",
                    f"选择理由：{exc}",
                )
            return
        for resolution in resolutions:
            row = rows_by_id.get(resolution.detail.detail_id)
            if row is None:
                continue
            if resolution.route.value == "DELEGATE_DIRECT_FUEL_PATH":
                reason = resolution.problems[0].message if resolution.problems else "转交直接燃料排放路径"
                row.show_parameter_state(
                    "参数状态：转交直接燃料路径（不进入购电间接排放）",
                    "采用因子：不适用",
                    "来源：直接燃料路径转交",
                    f"选择理由：{reason}",
                )
                continue
            selected = resolution.parameter_resolution.recommended if resolution.parameter_resolution else None
            snapshot = resolution.snapshot
            if selected is not None and snapshot is not None:
                factor = selected.factor
                category = selected.category.value
                method = resolution.parameter_resolution.selection_method.value if resolution.parameter_resolution and resolution.parameter_resolution.selection_method else "UNKNOWN"
                review = self.catalog_service.review_status_label(factor.review_status)
                row.show_parameter_state(
                    f"参数状态：已采用｜{category}｜{method}",
                    f"采用因子：{factor.factor_id} = {factor.value} {factor.unit}",
                    f"来源：{factor.source_id or '未提供'}｜审核状态：{review}｜{factor.source_location or '未提供来源定位'}",
                    f"选择理由：{resolution.parameter_resolution.selection_reason if resolution.parameter_resolution else '按当前规则确定'}",
                )
                continue
            problems = resolution.problems
            display_code = problems[0].code if problems else "GEN-PAR-NO-APPLICABLE-VALUE"
            if display_code == "GEN-VAL-NONFOSSIL-EVIDENCE":
                display_code = "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE"
            reason = problems[0].message if problems else "当前明细未形成可用参数快照"
            row.show_parameter_state(
                f"参数状态：阻断｜{display_code}",
                "采用因子：未采用（不生成快照）",
                "来源：无独立参数快照",
                f"选择理由：{reason}",
            )

    def _selected_heat_parameter_value(self) -> ParameterValue:
        factor_id = self.heat_factor_selector.currentData()
        if not isinstance(factor_id, str) or factor_id not in self._heat_factor_records:
            raise DomainValidationError("热力输入缺少可用的 G05 热力因子候选值 [GEN-PAR-NO-APPLICABLE-VALUE]")
        if self._parameter_resolver is None:
            raise DomainValidationError("热力输入未接入 G05 参数解析服务 [CAR-VAL-PARAMETER-RESOLVER-MISSING]")

        base_resolution = self._parameter_resolver.resolve(self._heat_resolution_context())
        selected_reason = self.heat_factor_selection_reason.text().strip()
        if base_resolution.recommended is not None and base_resolution.recommended.factor_id == factor_id and not base_resolution.blocked:
            resolution = base_resolution
        elif not selected_reason:
            raise DomainValidationError("选择非推荐热力因子时必须填写选择理由 [GEN-PAR-CONFIRMATION-REASON]")
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
            unit=factor.unit,
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

    def _run_calculation(self) -> None:
        self.validation_list.clear()
        if not self.enterprise_name.text().strip():
            self.validation_list.addItem("ERROR：企业名称为必填项 [GEN-VAL-REQUIRED-MISSING]")
            self.result_total.setText("存在输入错误")
            return
        try:
            outcome = self.calculator.calculate(self._input())
        except (DomainValidationError, InvalidOperation, ValueError) as exc:
            self.validation_list.addItem(f"ERROR：{exc}")
            self.result_total.setText("存在输入错误")
            return
        for problem in outcome.problems:
            self.validation_list.addItem(f"{problem.level.value}：{problem.message} [{problem.code}]")
        if not outcome.problems:
            self.validation_list.addItem("INFO：数据检查通过。")
        if outcome.result is None:
            self.result_total.setText("存在错误，未形成成功结果")
            return
        self.result_total.setText(f"总排放量 ET：{outcome.result.total_amount} tCO2")
        by_id = {line.line_id: line.amount for line in outcome.result.lines}
        self.result_breakdown.setText(
            f"直接排放 ES：{by_id.get('CAR-FLD-DIRECT-RESULT', Decimal('0'))} tCO2；"
            f"间接排放 EI：{by_id.get('CAR-FLD-INDIRECT-RESULT', Decimal('0'))} tCO2；"
            f"状态：{'可形成内存核算记录' if outcome.successful else '存在阻断问题'}"
        )
        self.parameter_snapshot_summary.setText(f"已形成 {len(outcome.parameter_snapshots)} 条参数快照；算法版本 {ALGORITHM_VERSION}。")
        trace_lines = [f"{trace.formula_id}：{trace.substitution} = {trace.amount} tCO2" for trace in outcome.traces]
        self.trace_output.setText("\n".join(trace_lines) if trace_lines else "无可展示计算过程。")


NewAccountingPage = CarbonMaterialAccountingPage


__all__ = ["CarbonMaterialAccountingPage", "NewAccountingPage"]
