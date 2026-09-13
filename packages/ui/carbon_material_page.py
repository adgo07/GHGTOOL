"""G06 Qt page for hand-entered GB/T 32151.34 calculations.

The page only assembles typed Domain input and renders structured results.  No
formula or parameter-selection logic is implemented in this presentation file.
"""

from __future__ import annotations

from collections.abc import Callable
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
    MaterialBasis,
    ParameterValue,
)
from packages.core.models import AccountingPeriod

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
        if calculator is None:
            resolver = None
            try:
                resolver = create_g06_parameter_resolver(self.catalog_service._repository)  # application boundary only
            except (AttributeError, KeyError, TypeError, ValueError):
                resolver = None
            calculator = CarbonMaterialCalculator(parameter_resolver=resolver)
        self.calculator = calculator
        self.standard_id = standard_id
        self._calculation_index = 0
        self._electricity_rows: list[_ElectricityRow] = []
        self._source_statuses: dict[str, QComboBox] = {}
        self._fields: dict[str, QLineEdit] = {}
        self._build_page()

    def set_standard_id(self, standard_id: str) -> None:
        self.standard_id = standard_id
        self.standard_id_label.setText(standard_id)

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
        form.addRow("核算期间", self.period_type)
        period_row = QWidget(identity)
        period_layout = QHBoxLayout(period_row)
        period_layout.setContentsMargins(0, 0, 0, 0)
        self.period_year = QSpinBox(period_row)
        self.period_year.setObjectName("accountingPeriodYear")
        self.period_year.setRange(2000, 2100)
        self.period_year.setValue(2025)
        self.period_month = QSpinBox(period_row)
        self.period_month.setObjectName("accountingPeriodMonth")
        self.period_month.setRange(1, 12)
        self.period_month.setValue(1)
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
        self._build_heat_section(activity_layout)
        self.body_layout.addWidget(activity)

        parameter_card, parameter_layout = _card("05 参数与排放因子", self)
        parameter_label = QLabel("电力和热力因子通过 G05 参数解析服务选择；标准缺省参数使用时会在校验结果和快照中标明来源。", parameter_card)
        parameter_label.setWordWrap(True)
        parameter_layout.addWidget(parameter_label)
        self.parameter_snapshot_summary = QLabel("尚未计算，暂无参数快照。", parameter_card)
        self.parameter_snapshot_summary.setObjectName("parameterSnapshotSummary")
        self.parameter_snapshot_summary.setWordWrap(True)
        parameter_layout.addWidget(self.parameter_snapshot_summary)
        self.body_layout.addWidget(parameter_card)

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

    def _remove_electricity_row(self, row: QWidget) -> None:
        if row in self._electricity_rows:
            self._electricity_rows.remove(row)
            self.electricity_rows_layout.removeWidget(row)
            row.deleteLater()

    def _build_heat_section(self, parent_layout: QVBoxLayout) -> None:
        label = QLabel("购入热力/动力（I02）", self)
        label.setObjectName("heatSectionTitle")
        parent_layout.addWidget(label)
        row = QWidget(self)
        form = QFormLayout(row)
        for key, label_text in (("heat_id", "明细ID"), ("heat_amount", "动力总量 kg"), ("heat_enthalpy", "蒸汽焓值 kJ/kg"), ("heat_pressure", "饱和蒸汽压力 MPa"), ("heat_factor", "热力因子 tCO2/GJ")):
            edit = _field(row, f"{key}Input")
            self._fields[key] = edit
            form.addRow(label_text, edit)
        parent_layout.addWidget(row)

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
        values = {field: _value(self._fields[f"{prefix}.{field}"]) for field in {
            "calcination": ("gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c"),
            "baking": ("bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar"),
            "graphitization": ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"),
            "fume": ("q", "qvar", "hm", "fch", "fox", "duration"),
            "fgd": ("cal", "i", "ef1", "tr"),
        }[prefix]}
        if all(value is None for value in values.values()):
            return None
        return kind(**values)

    def _electricity(self, enterprise_id: str, period: AccountingPeriod) -> tuple[ElectricityConsumptionDetail, ...]:
        details: list[ElectricityConsumptionDetail] = []
        for row in self._electricity_rows:
            detail = row.build(enterprise_id, period)
            if detail is not None:
                details.append(detail)
        return tuple(details)

    def _heat(self) -> tuple[HeatInput, ...]:
        amount = _value(self._fields["heat_amount"])
        if amount is None:
            return ()
        enthalpy = _value(self._fields["heat_enthalpy"])
        pressure = _value(self._fields["heat_pressure"])
        factor = _value(self._fields["heat_factor"])
        factor_value = ParameterValue("heat_emission_factor_default", factor, "tCO2/GJ", source_location="用户输入；待复核") if factor is not None else None
        return (HeatInput(_value(self._fields["heat_id"]) or "heat-1", amount, enthalpy, factor_value, pressure_mpa=pressure),)

    def _input(self) -> CarbonMaterialInput:
        self._calculation_index += 1
        period = self._period()
        enterprise_name = self.enterprise_name.text().strip() or "未填写企业"
        enterprise_id = "enterprise.current"
        return CarbonMaterialInput(
            input_id=f"input.{self._calculation_index}",
            enterprise_id=enterprise_id,
            enterprise_name=enterprise_name,
            period=period,
            boundary_confirmed=self.boundary_confirmed.isChecked(),
            boundary_component_ids=("main-production-system",),
            source_states=self._source_states(),
            fuel_inputs=self._fuel(),
            calcination=self._process("calcination", CalcinationInput),
            baking=self._process("baking", BakingInput),
            graphitization=self._process("graphitization", GraphitizationInput),
            fume_incineration=self._process("fume", FumeIncinerationInput),
            fgd=self._process("fgd", FGDInput),
            electricity_details=self._electricity(enterprise_id, period),
            purchased_heat=self._heat(),
        )

    def _run_calculation(self) -> None:
        self.validation_list.clear()
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
