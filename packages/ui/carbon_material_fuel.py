"""Compact fuel editor for the carbon-material standard."""
from collections.abc import Callable
from uuid import uuid4
from PySide6.QtCore import Qt, QEvent, QSignalBlocker
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox, QCompleter, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout
from packages.standards.carbon_material import FuelPath
from packages.standards.carbon_material_input_policy import InputOrigin, parameter_source_policy
from .compact_choices import TwoChoiceControl, SegmentedChoiceControl
from .name_selector import NameSelector
from .field_specs import get_field_spec
from .typed_inputs import create_typed_input


class FuelParameterDrafts:
    """Presentation drafts scoped to a confirmed identity and quantity path.

    This store never selects a source or supplies calculation values. Callers
    explicitly restore drafts after a business operation has been confirmed.
    """

    def __init__(self) -> None:
        self._values: dict[tuple[str, str, str, str, str], str] = {}

    @staticmethod
    def _context(identity: str, path: str, basis: str) -> tuple[str, str, str]:
        if not all(isinstance(value, str) and value for value in (identity, path, basis)):
            raise ValueError("fuel draft context requires a confirmed identity, path and basis")
        return identity, path, basis

    def save(self, identity: str, path: str, basis: str, field: str, source: str, value: str) -> None:
        context = self._context(identity, path, basis)
        if not all(isinstance(item, str) for item in (field, source, value)) or not field or not source:
            raise ValueError("fuel draft field, source and text must be explicit")
        self._values[(*context, field, source)] = value

    def load(self, identity: str, path: str, basis: str, field: str, source: str) -> str | None:
        # None and an explicitly empty draft are different states.
        return self._values.get((*self._context(identity, path, basis), field, source))

    def remember_selection(self, identity: str, path: str, basis: str, field: str,
                           source: str | None) -> None:
        """Remember a chosen source without granting it current eligibility.

        The reserved source key is presentation metadata, never a business
        source. Empty text records an explicitly unselected source.
        """
        if source is not None and (not isinstance(source, str) or not source):
            raise ValueError("fuel source selection must be explicit text or None")
        self.save(identity, path, basis, field, "__selection__", source or "")

    def selection(self, identity: str, path: str, basis: str, field: str) -> str | None:
        """Return a remembered source, '' for unselected, or None if never saved."""
        return self.load(identity, path, basis, field, "__selection__")

    def export(self) -> list[dict[str, str]]:
        return [
            dict(zip(("identity", "path", "basis", "field", "source", "value"), (*key, value)))
            for key, value in self._values.items()
        ]

    def restore(self, values: object, *, legacy_context: tuple[str, str, str] | None = None) -> None:
        """Read old pairs only when the saved confirmed context is known.

        Unknown context is never guessed from a current or pending selector.
        Invalid entries are ignored without changing valid retained drafts.
        """
        self._values.clear()
        if not isinstance(values, list):
            return
        for item in values:
            if not isinstance(item, dict):
                continue
            if any(key in item for key in ("identity", "path", "basis")):
                context = tuple(item.get(key) for key in ("identity", "path", "basis"))
            elif legacy_context is not None:
                context = legacy_context
            else:
                continue
            try:
                self.save(*context, item.get("field"), item.get("source"), item.get("value"))
            except (TypeError, ValueError):
                continue

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

        self.fuel_type = NameSelector(self)
        self.fuel_type.setObjectName(f"fuelType{index}")
        self.fuel_type.setProperty("fieldSpecKey", "fuel_type")
        self.fuel_type.setEditable(True)
        self.fuel_type.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.fuel_type.setPlaceholderText("搜索或输入燃料名称")
        self.fuel_type.lineEdit().setPlaceholderText("搜索或输入燃料名称")
        self.fuel_type.setMinimumWidth(190)
        self.fuel_type.lineEdit().setMaxLength(120)
        search_terms = []
        for option in self._fuel_options:
            label = option.label.strip()
            if not label or label in {"煤", "煤炭", "其他", "其它"}:
                continue
            self.fuel_type.addItem(label, option.fuel_type)
            self.fuel_type.setItemData(self.fuel_type.count() - 1, option.subject_id, Qt.ItemDataRole.UserRole + 1)
            search_terms.extend((label, *option.aliases))
        self.fuel_type.set_search_names((option.label, option.aliases) for option in self._fuel_options)
        self._committed_name = self.fuel_type.currentText().strip()
        self.fuel_type.lineEdit().installEventFilter(self)
        self._legacy_custom_identity = False
        self._activity_drafts = {}

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
        self.fuel_type_label = QLabel("燃料种类", self)
        self.path_label = QLabel("计量方式", self)
        self.activity_label = QLabel("活动量", self)
        self.carbon_basis_label = QLabel("含碳量方式", self)

        self.lower_heating_value = create_typed_input(self, get_field_spec("fuel_lhv"), f"fuelLhvInput{index}")
        self.carbon = create_typed_input(self, get_field_spec("fuel_carbon"), f"fuelCarbonInput{index}")
        self.carbon_direct = create_typed_input(self, get_field_spec("fuel_carbon"), f"fuelMeasuredCarbonInput{index}")
        self.oxidation = create_typed_input(self, get_field_spec("fuel_oxidation"), f"fuelOxidationInput{index}")
        self.source_reference = create_typed_input(self, get_field_spec("fuel_source_reference"), f"fuelSourceReference{index}")
        self.source_reference.setPlaceholderText("填写本条燃料的检测报告编号、页码或来源定位")

        self.carbon_basis = QComboBox(self)
        self.carbon_basis.setObjectName(f"fuelCarbonBasis{index}")
        self.carbon_basis.addItem("按热值计算", "HEAT_CONTENT")
        self.carbon_basis.addItem("直接含碳量", "DIRECT")
        self.lhv_source = self._source_combo(index, "lhv")
        self.carbon_source = self._source_combo(index, "carbon")
        direct_policy = parameter_source_policy("fuel.direct_carbon", origin=InputOrigin.CUSTOM)
        self.direct_carbon_source = self._source_combo(index, "directCarbon", values=direct_policy.allowed_sources)
        self.direct_carbon_source.setCurrentIndex(self.direct_carbon_source.findData(direct_policy.default_source))
        self.oxidation_source = self._source_combo(index, "oxidation")
        self._legacy_oxidation_source_index = self.oxidation_source.findData("USER_DEFINED")
        self.lhv_control = self._parameter_control(self.lhv_source, self.lower_heating_value)
        self.carbon_control = self._parameter_control(self.carbon_source, self.carbon)
        self.direct_carbon_control = self._parameter_control(self.direct_carbon_source, self.carbon_direct)
        self.oxidation_control = self._parameter_control(self.oxidation_source, self.oxidation)
        self.lhv_label = QLabel("低位发热量", self)
        self.carbon_label = QLabel("单位热值含碳量", self)
        self.direct_carbon_label = QLabel("直接单位含碳量", self)
        self.oxidation_label = QLabel("碳氧化率（%）", self)
        self.source_reference_label = QLabel("实测报告/来源定位", self)
        self.source_reference_control = QWidget(self)
        source_layout = QVBoxLayout(self.source_reference_control)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(5)
        source_layout.addWidget(self.source_reference_label)
        source_layout.addWidget(self.source_reference)
        self.source_reference_control.hide()
        self.calculated_carbon_label = QLineEdit(self)
        self.calculated_carbon_label.setReadOnly(True)
        self.calculated_carbon_label.setPlaceholderText("待计算")
        self.calculated_carbon_label.setObjectName(f"fuelCalculatedCarbon{index}")
        self.calculated_carbon_label.setAccessibleName("按低位发热量计算的单位活动量含碳量，仅供查看")

        carbon_value_cell = QWidget(self)
        carbon_value_layout = QVBoxLayout(carbon_value_cell)
        carbon_value_layout.setContentsMargins(0, 0, 0, 0)
        carbon_value_layout.setSpacing(5)
        self.carbon_basis_choices = TwoChoiceControl(self.carbon_basis, parent=self)
        self.carbon_calc_cell = QWidget(self)
        calc_layout = QVBoxLayout(self.carbon_calc_cell)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(0)
        calc_layout.addWidget(self.calculated_carbon_label)
        self.carbon_direct_cell = self.direct_carbon_control
        carbon_value_layout.addWidget(self.carbon_calc_cell, 2)
        carbon_value_layout.addWidget(self.carbon_direct_cell, 2)
        carbon_value_layout.addWidget(self.carbon_basis_choices)
        self.carbon_direct_cell.hide()
        self.carbon_basis_label.hide()

        self.lhv_cell = self.lhv_control
        self.oxidation_cell = self.oxidation_control
        self.source_cell = self.source_reference
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        # Compact C+A layout; source qualification remains on the original combos.
        self.path_choices = TwoChoiceControl(self.path, parent=self)
        for column, (label, widget) in enumerate(((self.fuel_type_label, self.fuel_type), (self.path_label, self.path_choices), (self.activity_label, self.activity))):
            grid.addWidget(self._field_cell(label, widget), 0, column, Qt.AlignmentFlag.AlignTop)
        for column, (label, widget) in enumerate(((self.lhv_label, self.lhv_control), (self.carbon_label, self.carbon_control), (self.oxidation_label, self.oxidation_control))):
            grid.addWidget(self._field_cell(label, widget), 1, column, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self._field_cell(self.direct_carbon_label, carbon_value_cell), 2, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.source_reference_control, 2, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        for control in self.findChildren(SegmentedChoiceControl):
            control.set_radio_style()
        self.input_grid = grid
        outer.addLayout(grid)
        self._last_path = getattr(self.path.currentData(), "value", self.path.currentData())
        activity_notice = QHBoxLayout()
        self.activity_draft_notice = QLabel(self)
        self.activity_draft_notice.setWordWrap(True)
        self.restore_activity_button = QPushButton("恢复当前燃料原单位活动量", self)
        self.activity_draft_notice.hide()
        self.restore_activity_button.hide()
        activity_notice.addWidget(self.activity_draft_notice, 1)
        activity_notice.addWidget(self.restore_activity_button)
        outer.addLayout(activity_notice)

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
        self._active_source_modes: dict[str, str | None] = {}
        self._parameter_source_drafts: dict[tuple[str, str], str] = {}
        self.parameter_drafts = FuelParameterDrafts()
        self.parameter_source = "AUTO"

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
    def _source_combo(index: int, key: str, values=("STANDARD_DEFAULT", "CALCULATED", "MEASURED")) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName(f"fuel{key.title()}Source{index}")
        labels = {"STANDARD_DEFAULT":"缺省值", "CALCULATED":"计算值", "MEASURED":"实测值"}
        for value in values:combo.addItem(labels[value], value)
        combo.addItem("历史填写来源（需确认）", "USER_DEFINED")
        combo.view().setRowHidden(combo.count()-1, True)
        return combo

    @staticmethod
    def _parameter_control(source: QComboBox, edit: QWidget) -> QWidget:
        control = QWidget()
        row = QVBoxLayout(control)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)
        row.addWidget(edit)
        row.addWidget(SegmentedChoiceControl(source, parent=control, values={"STANDARD_DEFAULT", "CALCULATED", "MEASURED"}))
        return control

    def _update_custom_name_visibility(self) -> None:
        # The searchable combo itself accepts custom text; the compatibility
        # editor remains hidden and is read only by the legacy state adapter.
        self.custom_name_label.hide()
        self.custom_name.hide()

    def eventFilter(self, watched, event):
        if (watched is self.fuel_type.lineEdit() and event.type() == QEvent.Type.KeyPress
                and event.key() == Qt.Key.Key_Escape):
            # Cancel only the pending text. Never re-confirm or reset the
            # previously confirmed identity, parameter values or source modes.
            blockers = (QSignalBlocker(self.fuel_type), QSignalBlocker(watched))
            index = self.fuel_type.findText(self._committed_name)
            if index >= 0:
                self.fuel_type.setCurrentIndex(index)
            else:
                self.fuel_type.setEditText(self._committed_name)
            self.fuel_type.restore_confirmation(self._committed_name)
            del blockers
            return True
        return super().eventFilter(watched, event)


