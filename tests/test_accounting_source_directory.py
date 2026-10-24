"""C+A navigation must preserve business state and reveal validation targets."""
import unittest
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QPushButton, QRadioButton, QTreeWidgetItem
from packages.ui.compact_choices import SegmentedChoiceControl
from tests import test_accounting_projects_ui as project_fixture


class SourceDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    setUp = project_fixture.AccountingProjectUiTests.setUp
    tearDown = project_fixture.AccountingProjectUiTests.tearDown
    _new_page = project_fixture.AccountingProjectUiTests._new_page

    def pump(self):
        for _ in range(3):
            self.application.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_directory_switches_preserve_complete_state_and_real_controls(self):
        page = self.page
        for group in ("fuel", "electricity", "calcination"):
            page._toggle_source_group(group)
        fuel = page._fuel_rows[0]
        fuel.activity.setText("123.45")
        fuel.source_reference.setText("检测报告 TEST-001 第3页")
        energy = page._energy_family_rows["electricity"][0]
        energy.amount.setText("234.56")
        material = page._process_rows["calcination"][0]["materials"][0]
        material["mass"].setText("345.67")
        initial = page._capture_form_state()
        for _ in range(3):
            for group in ("fuel", "electricity", "calcination"):
                page.source_directory.buttons[group].click()
                self.pump()
                self.assertEqual(page._capture_form_state(), initial)
        self.assertIs(page._fuel_rows[0], fuel)
        self.assertIs(page._energy_family_rows["electricity"][0], energy)
        self.assertIs(page._process_rows["calcination"][0]["materials"][0], material)
        self.assertTrue(all(isinstance(b, QRadioButton) for b in fuel.path_choices.group.buttons()))
        self.assertTrue(all(isinstance(b, QRadioButton) for b in energy.direction_choices.group.buttons()))

    def test_browse_does_not_enable_and_enable_remains_explicit(self):
        page = self.page
        initial = page._capture_form_state()
        for group in ("fuel", "electricity", "calcination"):
            page.source_directory.select(group)
        self.assertEqual(initial, page._capture_form_state())
        page.source_directory.placeholders["fuel"].findChild(QPushButton).click()
        self.assertTrue(page._source_is_enabled("CAR-SRC-FUEL-001"))
        self.assertFalse(page._source_is_enabled("CAR-SRC-CALCINATION-001"))
        self.assertTrue(page.source_directory.placeholders["fuel"].isHidden())
        page._toggle_source_group("fuel")
        self.assertFalse(page.source_directory.placeholders["fuel"].isHidden())

    def test_validation_reveals_directory_without_changing_state(self):
        page = self.page
        page._toggle_source_group("fuel")
        page.source_directory.select("calcination")
        item = QTreeWidgetItem(["缺少活动量"])
        item.setData(0, Qt.ItemDataRole.UserRole, page._fuel_rows[0].activity.objectName())
        item.setData(0, Qt.ItemDataRole.UserRole + 1, "CAR-SRC-FUEL-001")
        initial = page._capture_form_state()
        page._focus_validation_item(item)
        self.pump()
        self.assertTrue(page.source_directory.buttons["fuel"].isChecked())
        self.assertEqual(initial, page._capture_form_state())

    def test_new_rows_and_conversion_keep_scoped_layout(self):
        page = self.page
        fuel = page._add_fuel_row()
        # Existing creation helpers may return None: inspect the owned final row.
        fuel = page._fuel_rows[-1]
        self.assertEqual(fuel.input_grid.columnCount(), 3)
        material = page._add_material_line(page._process_rows["calcination"][0])
        choices = material["widget"].findChildren(SegmentedChoiceControl)
        self.assertTrue(choices)
        self.assertTrue(all(c._radio_style for c in choices))
        conversion = next(b for b in material["widget"].findChildren(QPushButton) if b.text().startswith("数据基准与换算"))
        material["mass"].setText("17.25")
        conversion.click()
        page.source_directory.select("fuel")
        page.source_directory.select("calcination")
        self.assertTrue(conversion.isChecked())
        self.assertEqual(material["mass"].text(), "17.25")
        heat = page._energy_family_rows["heat"][0]
        self.assertTrue(heat.direction_choices._radio_style)

    def test_all_eight_groups_use_single_scroll_and_navigation_is_not_input(self):
        from PySide6.QtWidgets import QScrollArea
        page = self.page
        expected = {group for group, _, _ in page._source_toggle_groups}
        self.assertEqual(set(page.source_directory.cards), expected)
        self.assertEqual(len(expected), 8)
        self.assertFalse(page.source_directory.findChildren(QScrollArea))
        self.assertTrue(page.source_toggle_host.isHidden())
        page._project_dirty = False
        page._input_dirty = False
        initial = page._capture_form_state()
        for group in expected:
            page.source_directory.select(group)
            self.pump()
            self.assertEqual(initial, page._capture_form_state())
            self.assertFalse(page._project_dirty)
            self.assertFalse(page._input_dirty)
        page.source_navigation.setCurrentIndex(2)
        self.assertNotIn("accountingSourceNavigation", page._capture_form_state())
        self.assertEqual(initial, page._capture_form_state())

    def test_unconfirmed_status_and_disclosure_preserve_input(self):
        from packages.standards.carbon_material import EmissionSourceStatus
        page = self.page
        combo = page._source_statuses["CAR-SRC-FUEL-001"]
        combo.setCurrentIndex(combo.findData(EmissionSourceStatus.UNCONFIRMED))
        page._refresh_source_cards()
        self.assertIn("待确认", page.source_directory.buttons["fuel"].text())
        fuel = page._fuel_rows[0]
        fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("DIRECT"))
        initial = page._capture_form_state()
        fuel.inactive_parameters_toggle.click()
        fuel.inactive_parameters_toggle.click()
        self.assertEqual(initial, page._capture_form_state())

    def test_hidden_long_page_does_not_impose_editor_minimum(self):
        page = self.page
        page._toggle_source_group("calcination")
        page._toggle_source_group("fuel")
        page.source_directory.select("calcination")
        self.pump()
        long_height = page.source_directory.stack.minimumSizeHint().height()
        page.source_directory.select("fuel")
        self.pump()
        self.assertLess(page.source_directory.stack.minimumSizeHint().height(), long_height)

    def test_responsive_materials_keep_values_sources_and_ownership(self):
        from packages.ui.responsive_fields import AdaptiveFieldLayout
        from PySide6.QtWidgets import QWidget
        page = self.page
        for prefix in ("calcination", "baking", "graphitization"):
            material = page._process_rows[prefix][0]["materials"][0]
            material["mass"].setText("17.25")
            host = next(w for w in material["widget"].findChildren(QWidget)
                        if isinstance(w.layout(), AdaptiveFieldLayout) and w.layout().maximum_columns == 3)
            grid = host.layout()
            original = page._capture_form_state()
            for width, columns in ((1000, 3), (650, 2), (430, 1), (1000, 3)):
                host.resize(width, 1000)
                grid.reflow()
                self.assertEqual(grid._signature[0], columns)
                self.assertTrue(all(material["widget"].isAncestorOf(cell) for cell in grid.cells))
                self.assertEqual(page._capture_form_state(), original)

    def test_keyboard_browse_and_four_state_switch_are_separate_from_input(self):
        from PySide6.QtTest import QTest
        from packages.standards.carbon_material import EmissionSourceStatus
        page = self.page
        original = page._capture_form_state()
        QTest.keyClick(page.source_directory.buttons["fuel"], Qt.Key.Key_Down)
        self.assertTrue(page.source_directory.buttons["calcination"].isChecked())
        self.assertEqual(original, page._capture_form_state())
        switch = page._source_header_buttons["fuel"][0]
        for state in ("未启用", "已启用", "部分启用", "待确认"):
            switch.set_source_state(state)
            self.assertEqual(switch.label.text(), state)
            self.assertEqual(switch.switch.active, state == "已启用")
            self.assertEqual(original, page._capture_form_state())
        page._refresh_source_cards()
        QTest.keyClick(switch, Qt.Key.Key_Space)
        self.assertTrue(page._source_is_enabled("CAR-SRC-FUEL-001"))

    def test_other_electricity_hides_catalog_fields_without_losing_drafts(self):
        page = self.page
        row = page._energy_family_rows["electricity"][0]
        region = row.region.currentData()
        factor = row.factor_selector.currentData()
        row.factor_mode.setCurrentIndex(row.factor_mode.findData("MANUAL"))
        self.pump()
        self.assertTrue(row.geographic_level_field.isHidden())
        self.assertTrue(row.region_field.isHidden())
        self.assertEqual(row.region.currentData(), region)
        self.assertEqual(row.factor_selector.currentData(), factor)
        row.factor_mode.setCurrentIndex(row.factor_mode.findData("LIBRARY"))
        self.pump()
        self.assertFalse(row.region_field.isHidden())

    def test_shell_reflow_contains_fields_after_resize_disclosure_and_source_switch(self):
        from apps.carbon_accounting_desktop.app import create_main_window
        from apps.carbon_accounting_desktop.config import AppConfig
        from packages.ui.view_models import AppRoute
        from packages.ui.responsive_fields import AdaptiveFieldLayout
        from PySide6.QtWidgets import QWidget, QLineEdit
        import sys
        errors = []
        previous_hook = sys.excepthook
        sys.excepthook = lambda kind, value, trace: errors.append(f"{kind.__name__}: {value}")
        window = create_main_window(AppConfig(log_directory=self.root / "logs"),
            catalog_service=self.catalog_service, record_repository=self.records,
            project_service=self.project_service, calculation_use_case=self.page.calculation_use_case)
        window.resize(1680, 1000)
        window.show()
        shell = window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        page = shell.pages[AppRoute.NEW_ACCOUNTING]
        for group in ("fuel", "calcination", "baking", "graphitization", "fgd"):
            page._toggle_source_group(group)
        def settle():
            for _ in range(8):
                self.pump()
        def assert_contained(card):
            for host in card.findChildren(QWidget):
                grid = host.layout()
                if not isinstance(grid, AdaptiveFieldLayout) or not host.isVisible():
                    continue
                self.assertGreaterEqual(host.height(), grid.minimumSize().height())
                for cell in grid.cells:
                    if cell.isHidden():
                        continue
                    self.assertTrue(host.rect().contains(cell.geometry()), (host.objectName(), host.size(), cell.geometry()))
                    for control in cell.findChildren(QWidget):
                        if isinstance(control, (QLineEdit, SegmentedChoiceControl)) and control.isVisible():
                            self.assertTrue(control.parentWidget().rect().contains(control.geometry()),
                                            (control.objectName(), control.geometry(), control.parentWidget().size()))
        try:
            for width in (1680, 1180, 1440, 1180, 1680):
                window.resize(width, 850)
                for group in ("calcination", "baking", "graphitization", "fgd", "fuel"):
                    page.source_directory.select(group)
                    settle()
                    if group in ("calcination", "baking", "graphitization"):
                        row = page._process_rows[group][0]
                        material = page._add_material_line(row)
                        button = next(b for b in material["widget"].findChildren(QPushButton)
                                      if b.text().startswith("数据基准与换算"))
                        button.click()
                        settle()
                        assert_contained(page.source_directory.cards[group])
                        button.click()
                        page._remove_material_line(row, material["line_id"])
                    elif group == "fgd":
                        unit = page._process_rows["fgd"][0]
                        component = page._add_fgd_component(unit)
                        settle()
                        assert_contained(page.source_directory.cards[group])
                        page._remove_fgd_component(unit, component["component_id"])
                    settle()
                    assert_contained(page.source_directory.cards[group])
                    signature = [(w.size().width(), w.size().height()) for w in page.source_directory.cards[group].findChildren(QWidget)]
                    settle()
                    self.assertEqual(signature, [(w.size().width(), w.size().height()) for w in page.source_directory.cards[group].findChildren(QWidget)])
        finally:
            # This is a temporary window with deliberate unfinished inputs.
            page._project_dirty = False
            window.hide()
            window.deleteLater()
            settle()
            sys.excepthook = previous_hook
        self.assertEqual(errors, [])

    def test_heat_edit_commit_refreshes_only_existing_readonly_preview(self):
        from unittest.mock import patch
        page = self.page
        row = page._energy_family_rows["heat"][0]
        row.heat_boundary.setCurrentIndex(row.heat_boundary.findData("OUTSIDE_ENTERPRISE"))
        row.heat_fuel_accounted.setCurrentIndex(row.heat_fuel_accounted.findData(False))
        with patch.object(page, "_run_calculation") as calculate:
            for mode, value in (("MANUAL", "2800"), ("MANUAL", ""), ("MANUAL", "invalid"),
                                ("AUTO", "0.8"), ("AUTO", ""), ("AUTO", "-1")):
                row.enthalpy_mode.setCurrentIndex(row.enthalpy_mode.findData(mode))
                control = row.enthalpy if mode == "MANUAL" else row.pressure
                control.setText(value)
                before = page._capture_form_state()
                with patch.object(page, "_refresh_unified_energy_row_preview", wraps=page._refresh_unified_energy_row_preview) as preview:
                    control.editingFinished.emit()
                    self.assertEqual(preview.call_count, 1)
                self.assertEqual(before, page._capture_form_state())
                self.assertTrue(row.status.text())
                if mode == "MANUAL" and value == "2800":
                    self.assertNotIn("待填写", row.status.text())
                if mode == "AUTO" and value == "0.8":
                    self.assertIn("IF97焓值", row.status.text())
            calculate.assert_not_called()
        self.assertEqual(len(self.records.list_all()), 0)

    def test_validation_opens_conversion_and_external_disclosures_without_input_changes(self):
        page = self.page
        page._toggle_source_group("calcination")
        material = page._process_rows["calcination"][0]["materials"][0]
        button = next(b for b in material["widget"].findChildren(QPushButton)
                      if b.text().startswith("数据基准与换算"))
        page.source_directory.select("fuel")
        original = page._capture_form_state()
        item = QTreeWidgetItem(["换算信息未完成"])
        item.setData(0, Qt.ItemDataRole.UserRole, material["moisture_received_percent"].objectName())
        item.setData(0, Qt.ItemDataRole.UserRole + 1, "CAR-SRC-CALCINATION-001")
        page._focus_validation_item(item)
        for _ in range(5):
            self.pump()
        self.assertTrue(button.isChecked())
        self.assertTrue(material["moisture_received_percent"].isVisibleTo(page))
        self.assertTrue(page.source_directory.buttons["calcination"].isChecked())
        self.assertEqual(page._capture_form_state(), original)
        external = next(b for b in page.findChildren(QPushButton)
                        if b.text().startswith("填写／查看外部补充明细"))
        item = QTreeWidgetItem(["外部补充值未完成"])
        item.setData(0, Qt.ItemDataRole.UserRole, page.external_amount.objectName())
        page._focus_validation_item(item)
        for _ in range(5):
            self.pump()
        self.assertTrue(external.isChecked())
        self.assertTrue(page.external_amount.isVisibleTo(page))
        self.assertFalse(page.external_included.isChecked())
        self.assertEqual(page._capture_form_state(), original)

    def test_fuel_source_adapters_stay_hidden_while_real_choices_change_original_data(self):
        from PySide6.QtWidgets import QComboBox
        from packages.standards.carbon_material import FuelType
        page = self.page
        legacy = QComboBox(page)
        page._set_fuel_source_visibility(legacy, True)
        self.assertFalse(legacy.isHidden())
        page._set_fuel_source_visibility(legacy, False)
        self.assertTrue(legacy.isHidden())
        legacy.deleteLater()
        page._toggle_source_group("fuel")
        page.source_directory.select("fuel")
        fuel = page._fuel_rows[0]
        fuel.fuel_type.setCurrentIndex(fuel.fuel_type.findData(FuelType.NATURAL_GAS))
        fuel.fuel_type.confirm_name(force=True)
        original = {name: getattr(fuel, name) for name in
                    ("lhv_source", "carbon_source", "oxidation_source", "direct_carbon_source")}
        def choose(name, value):
            combo = original[name]
            choices = [choice for choice in fuel.findChildren(SegmentedChoiceControl) if choice.combo is combo]
            self.assertEqual(len(choices), 1)
            choice = choices[0]
            button = next(button for button in choice.group.buttons()
                          if combo.itemData(choice.group.id(button)) == value)
            self.assertTrue(button.isEnabled())
            self.assertTrue(button.isVisibleTo(fuel))
            button.click()
            self.pump()
            self.assertIs(getattr(fuel, name), combo)
            self.assertEqual(combo.currentData(), value)
            self.assertTrue(combo.isHidden())
            return choice
        fields = (("lhv_source", "lower_heating_value", "388.123456789"),
                  ("carbon_source", "carbon", "0.023456789"),
                  ("oxidation_source", "oxidation", "97.123456789"))
        page.show()
        column_counts = set()
        for width in (1680, 1000):
            page.resize(width, 1000)
            fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("HEAT_CONTENT"))
            for _ in range(5):
                self.pump()
            column_counts.add(len({cell.x() for cell in fuel.identity_cells}))
            for name, edit_name, value in fields:
                choice = choose(name, "STANDARD_DEFAULT")
                self.assertNotIn("CALCULATED", {original[name].itemData(choice.group.id(button))
                                               for button in choice.group.buttons()})
                edit = getattr(fuel, edit_name)
                self.assertTrue(edit.isReadOnly())
                self.assertTrue(fuel.source_reference_control.isHidden())
                choose(name, "MEASURED")
                self.assertFalse(edit.isReadOnly())
                self.assertTrue(edit.isEnabled())
                self.assertFalse(fuel.source_reference_control.isHidden())
                edit.setText(value)
                choose(name, "STANDARD_DEFAULT")
                choose(name, "MEASURED")
                self.assertEqual(edit.text(), value)
                choose(name, "STANDARD_DEFAULT")
            self.assertTrue(fuel.source_reference_control.isHidden())
            fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("DIRECT"))
            self.pump()
            choose("direct_carbon_source", "CALCULATED")
            self.assertFalse(fuel.source_reference_control.isHidden())
            fuel.carbon_direct.setText("4.567890123")
            choose("direct_carbon_source", "MEASURED")
            fuel.carbon_direct.setText("5.678901234")
            choose("direct_carbon_source", "CALCULATED")
            self.assertEqual(fuel.carbon_direct.text(), "4.567890123")
            choose("direct_carbon_source", "MEASURED")
            self.assertEqual(fuel.carbon_direct.text(), "5.678901234")
            self.assertFalse(fuel.source_reference_control.isHidden())
            fuel.inactive_parameters_toggle.setChecked(True)
            self.pump()
            disabled_state = page._capture_form_state()
            for name in ("lhv_source", "carbon_source"):
                choice = next(choice for choice in fuel.findChildren(SegmentedChoiceControl)
                              if choice.combo is original[name])
                self.assertTrue(choice.isVisibleTo(fuel))
                for button in choice.group.buttons():
                    self.assertFalse(button.isEnabled())
                    button.click()
            self.assertEqual(page._capture_form_state(), disabled_state)
            self.assertTrue(all(combo.isHidden() for combo in original.values()))
        self.assertGreaterEqual(len(column_counts), 2, column_counts)
        fuel.activity.setText("12.3456789")
        fuel.source_reference.setText("合成检测报告 SOURCE-TEST")
        saved = page._capture_form_state()
        page.source_directory.select("electricity")
        page.source_directory.select("fuel")
        self.pump()
        self.assertEqual(page._capture_form_state(), saved)
        self.assertTrue(all(combo.isHidden() for combo in original.values()))
        self.assertEqual(len(self.records.list_all()), 0)
