"""PR59: actual legacy project recovery and first-click viewport navigation."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from shiboken6 import isValid
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import ProjectWorkspaceService
from packages.application.canonical_input_codec import encode_canonical_input, decode_canonical_input
from packages.persistence import (SQLiteProjectWorkspaceRepository, SQLiteRecordRepository,
    SQLiteSettingsRepository, build_catalog_database)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import MaterialBasis
from packages.ui.dialogs import MessageBox
from packages.ui.export_location import ExportLocationService
from packages.ui.view_models import AppRoute
from tests import test_b_fume_chain as fume_fixture


class PR59CompatibilityNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="pr59-navigation-")
        self.root = Path(self.directory.name)
        self.callback_errors = []
        self.old_hook = sys.excepthook
        sys.excepthook = lambda typ, exc, tb: self.callback_errors.append(
            "".join(traceback.format_exception(typ, exc, tb)))

    def tearDown(self):
        self.pump()
        sys.excepthook = self.old_hook
        self.directory.cleanup()
        self.assertEqual(self.callback_errors, [])

    def pump(self):
        for _ in range(16):
            self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    @contextmanager
    def page(self, name, size=(1180, 850)):
        root = self.root / name
        root.mkdir(exist_ok=True)
        catalog = root / "catalog.sqlite"
        if not catalog.exists():
            build_catalog_database(DEFAULT_SOURCE_PATH, catalog)
        projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root / "projects.sqlite"))
        records = SQLiteRecordRepository(root / "records.sqlite")
        window = create_main_window(AppConfig(catalog_database=catalog,
            records_database=root / "records.sqlite", projects_database=root / "projects.sqlite"),
            project_service=projects, record_repository=records,
            export_location_service=ExportLocationService(SQLiteSettingsRepository(root / "user.sqlite")))
        window.resize(*size)
        window.show()
        shell = window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.pump()
        try:
            yield shell.pages[AppRoute.NEW_ACCOUNTING], projects, records, shell
        finally:
            if isValid(window):
                window.hide()
                window.deleteLater()
            self.pump()
            self.assertFalse(isValid(window))

    @staticmethod
    def items(tree):
        def walk(item):
            yield item
            for index in range(item.childCount()):
                yield from walk(item.child(index))
        for index in range(tree.topLevelItemCount()):
            yield from walk(tree.topLevelItem(index))

    def actual_error(self, page, target):
        matches = [item for item in self.items(page.validation_list)
                   if item.data(0, Qt.ItemDataRole.UserRole) == target.objectName()]
        self.assertTrue(matches, [(item.text(0), item.data(0, Qt.ItemDataRole.UserRole))
                                 for item in self.items(page.validation_list)])
        return matches[0]

    def click_error(self, page, shell, target):
        item = self.actual_error(page, target)
        shell.main_scroll_area.ensureWidgetVisible(page.validation_list)
        page.validation_list.scrollToItem(item)
        self.pump()
        rect = page.validation_list.visualItemRect(item)
        point = page.validation_list.viewport().mapTo(shell.main_scroll_area.viewport(), rect.center())
        self.assertTrue(shell.main_scroll_area.viewport().rect().contains(point), "error entry itself must be visible")
        QTest.mouseClick(page.validation_list.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
        self.pump()

    def assert_in_viewport(self, shell, target):
        viewport = shell.main_scroll_area.viewport()
        rectangle = QRect(target.mapTo(viewport, QPoint(0, 0)), target.size())
        self.assertTrue(target.isVisibleTo(viewport), "target must be shown")
        self.assertTrue(viewport.rect().contains(rectangle),
            f"target {rectangle.getRect()} outside actual viewport {viewport.rect().getRect()}")

    def save_legacy(self, name, duration):
        with self.page(name) as (page, projects, records, shell):
            fume_fixture.FumeQtExcelTests.prepare(page)
            fume_fixture.FumeQtExcelTests.fill(page._process_rows["fume"][0], duration=duration)
            row = page._process_rows["fume"][0]
            state = page._capture_form_state()
            # Old form-state predates segment controls and the execution marker.
            for key in ("fume_execution_version", "fume_identities"):
                state.pop(key, None)
            for key in ("segment_start", "segment_end", "duration_unit", "source_selector", "boundary_selector"):
                state.pop(row[key].objectName(), None)
            page._restore_form_state(state)
            page.project_name.setText("合成旧烟气项目")
            self.assertTrue(page._save_project())
            project_id = page._workspace.project_id
            value = page._input(increment=False)
            encoded = json.loads(encode_canonical_input(value))
            payload = encoded["payload"]
            payload["version"] = 3
            fields = payload["value"]["fields"]
            for key in ("fume_segments", "fume_execution_version", "external_co2"):
                fields.pop(key, None)
            for item in fields["fume_incinerations"]["items"]:
                item["fields"].pop("source_name", None)
                item["fields"].pop("boundary_name", None)
            encoded["input_version"] = 3
            legacy = decode_canonical_input(json.dumps(encoded))
            self.assertEqual(legacy.fume_execution_version, "FUME_V1")
            workspace = projects.new_workspace("旧Canonical对照")
            projects.save(replace(workspace, units=(replace(workspace.units[0], canonical_input=legacy),)))
            reopened = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(self.root / name / "projects.sqlite"))
            self.assertEqual(reopened.get(workspace.project_id).units[0].canonical_input, legacy)
            self.assertEqual(len(records.list_all()), 0)
            return project_id

    def test_legacy_project_duration_edit_cancel_upgrade_and_explicit_upgrade_preserve_values(self):
        project_id = self.save_legacy("legacy-seven", "7")
        with self.page("legacy-seven") as (page, projects, records, shell):
            with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Discard):
                self.assertTrue(page.open_project_from_home(project_id))
            self.assertEqual(page._workspace.project_id, project_id)
            page.source_directory.select("fume")
            self.pump()
            row = page._process_rows["fume"][0]
            duration = row["fields"]["duration"]
            self.assertEqual(duration.text(), "7")
            self.assertTrue(duration.isVisibleTo(page), "legacy duration must remain editable")
            self.assertFalse(duration.isReadOnly())
            self.assertIn("时长（天）", "\n".join(label.text() for label in row["widget"].findChildren(QLabel)))
            before = page._capture_form_state()
            with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.No):
                row["upgrade_button"].click()
            self.assertEqual(before, page._capture_form_state())
            self.assertTrue(duration.isVisibleTo(page))
            duration.setFocus()
            duration.selectAll()
            QTest.keyClicks(duration, "8")
            self.assertEqual(page._input(increment=False).fume_incinerations[0].duration.value, Decimal("8"))
            self.assertEqual(page._input(increment=False).fume_execution_version, "FUME_V1")
            page.calculate_button.click()
            self.pump()
            self.assertEqual(len(records.list_all()), 1)
            # Preserve the existing V1 p40 operation order, including its full
            # value beyond the 0.56 presentation; never round the Calculator.
            self.assertEqual(records.list_all()[0].calculation_result.total_amount,
                             Decimal("0.5632000000000000000000000000000000000001"))
            duration.setText("7")
            page.calculate_button.click()
            self.pump()
            self.assertEqual(len(records.list_all()), 2)
            original = page._capture_form_state()
            original.pop("fume_upgrade_original_state", None)
            with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Yes):
                row["upgrade_button"].click()
            self.assertEqual(page._fume_execution_version, "FUME_V2")
            self.assertEqual(page._fume_upgrade_original_state, original)
            self.assertEqual(duration.text(), "7")
            self.assertTrue(duration.isVisibleTo(page))
            self.assertEqual(len(records.list_all()), 2)

    def test_missing_legacy_duration_error_is_visible_and_can_be_completed_under_v1(self):
        project_id = self.save_legacy("legacy-missing", "")
        with self.page("legacy-missing") as (page, projects, records, shell):
            with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Discard):
                self.assertTrue(page.open_project_from_home(project_id))
            self.assertEqual(page._workspace.project_id, project_id)
            page.source_directory.select("fume")
            self.pump()
            target = page._process_rows["fume"][0]["fields"]["duration"]
            page.calculate_button.click()
            self.pump()
            self.assertEqual(len(records.list_all()), 0)
            self.click_error(page, shell, target)
            self.assert_in_viewport(shell, target)
            self.assertIs(self.app.focusWidget(), target)
            target.setText("7")
            page.calculate_button.click()
            self.pump()
            self.assertEqual(page._fume_execution_version, "FUME_V1")
            self.assertEqual(len(records.list_all()), 1)
            self.assertEqual(records.list_all()[0].calculation_result.total_amount, Decimal("0.4928"))

    def test_first_actual_material_error_click_reveals_target_in_narrow_and_wide_viewport(self):
        for size in ((1180, 850), (1680, 1000)):
            with self.subTest(size=size), self.page(str(size[0]), size) as (page, projects, records, shell):
                page.enterprise_name.setText("合成错误定位")
                page.period_year.setValue(2025)
                page.boundary_confirmed.setChecked(True)
                for combo in page._source_statuses.values():
                    combo.setCurrentIndex(combo.findData("NOT_INVOLVED"))
                page._toggle_source_group("calcination")
                material = page._process_rows["calcination"][0]["materials"][3]
                material["name"].setText("第四物料")
                material["fixed_carbon"].setText("90")
                page.calculate_button.click()
                self.pump()
                page.source_directory.select("fuel")
                self.pump()
                before = page._capture_form_state()
                dirty = (page._input_dirty, page._project_dirty)
                self.click_error(page, shell, material["mass"])
                self.assert_in_viewport(shell, material["mass"])
                self.assertIs(self.app.focusWidget(), material["mass"])
                self.assertEqual(before, page._capture_form_state())
                self.assertEqual(dirty, (page._input_dirty, page._project_dirty))
                self.assertEqual(len(records.list_all()), 0)

    def material_failure(self, page, *, conversion=False):
        page.enterprise_name.setText("合成定位生命周期")
        page.period_year.setValue(2025)
        page.boundary_confirmed.setChecked(True)
        for combo in page._source_statuses.values():
            combo.setCurrentIndex(combo.findData("NOT_INVOLVED"))
        page._toggle_source_group("calcination")
        process = page._process_rows["calcination"][0]
        material = process["materials"][3]
        material["name"].setText("第四物料")
        material["fixed_carbon"].setText("90")
        if conversion:
            material["mass"].setText("10")
            material["volatile_matter"].setText("5")
            for name in ("mass_basis", "composition_basis"):
                material[name].setCurrentIndex(material[name].findData(MaterialBasis.DRY))
            method = material["conversion_method"]
            index = method.findData("DRY_TO_RECEIVED_MOISTURE")
            self.assertGreaterEqual(index, 0)
            method.setCurrentIndex(index)
        page.calculate_button.click()
        self.pump()
        return process, material

    def test_actual_folded_conversion_error_enters_narrow_and_wide_viewport(self):
        for size in ((1180, 850), (1680, 1000)):
            with self.subTest(size=size), self.page("conversion-" + str(size[0]), size) as (page, projects, records, shell):
                process, material = self.material_failure(page, conversion=True)
                toggle = next(button for button in material["widget"].findChildren(QPushButton)
                              if button.text().startswith("数据基准与换算"))
                if toggle.isChecked():
                    toggle.click()
                self.assertFalse(toggle.isChecked())
                page.source_directory.select("fuel")
                self.pump()
                before = page._capture_form_state()
                dirty = (page._input_dirty, page._project_dirty)
                target = material["moisture_received_percent"]
                self.click_error(page, shell, target)
                self.assertTrue(toggle.isChecked())
                self.assert_in_viewport(shell, target)
                self.assertIs(self.app.focusWidget(), target)
                self.assertEqual(before, page._capture_form_state())
                self.assertEqual(dirty, (page._input_dirty, page._project_dirty))
                self.assertEqual(len(records.list_all()), 0)

    def test_rapid_real_error_requests_finish_only_at_latest_target(self):
        with self.page("rapid") as (page, projects, records, shell):
            process, last = self.material_failure(page)
            first = process["materials"][0]
            first["name"].setText("第一原料")
            first["fixed_carbon"].setText("85")
            page.calculate_button.click()
            self.pump()
            before = page._capture_form_state()
            dirty = (page._input_dirty, page._project_dirty)
            page._focus_validation_item(self.actual_error(page, last["mass"]))
            page._focus_validation_item(self.actual_error(page, first["mass"]))
            self.pump()
            self.assertIs(self.app.focusWidget(), first["mass"])
            self.assert_in_viewport(shell, first["mass"])
            self.assertEqual(before, page._capture_form_state())
            self.assertEqual(dirty, (page._input_dirty, page._project_dirty))
            self.assertEqual(len(records.list_all()), 0)

    def test_browsing_away_and_back_cancels_obsolete_error_focus(self):
        with self.page("source-cancel") as (page, projects, records, shell):
            process, material = self.material_failure(page)
            before = page._capture_form_state()
            dirty = (page._input_dirty, page._project_dirty)
            page._focus_validation_item(self.actual_error(page, material["mass"]))
            page.source_directory.buttons["baking"].click()
            page.source_directory.buttons["calcination"].click()
            page.source_directory.buttons["calcination"].setFocus()
            self.pump()
            self.assertIs(self.app.focusWidget(), page.source_directory.buttons["calcination"])
            self.assertEqual(page.source_directory._selected, "calcination")
            self.assertEqual(before, page._capture_form_state())
            self.assertEqual(dirty, (page._input_dirty, page._project_dirty))
            self.assertEqual(len(records.list_all()), 0)

    def test_deleted_target_and_route_change_cancel_pending_navigation(self):
        with self.page("delete-cancel") as (page, projects, records, shell):
            process, material = self.material_failure(page)
            target = material["mass"]
            page._focus_validation_item(self.actual_error(page, target))
            page._remove_material_line(process, material["line_id"])
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            after_explicit_delete = page._capture_form_state()
            dirty = (page._input_dirty, page._project_dirty)
            self.pump()
            self.assertFalse(isValid(target))
            self.assertEqual(after_explicit_delete, page._capture_form_state())
            self.assertEqual(dirty, (page._input_dirty, page._project_dirty))
            next_target = process["materials"][0]["mass"]
            page._scroll_to_widget(next_target, focus=True)
            shell.navigate(AppRoute.STANDARDS)
            self.pump()
            self.assertEqual(shell.router.current_route, AppRoute.STANDARDS)
            self.assertIsNot(self.app.focusWidget(), next_target)
            self.assertEqual(len(records.list_all()), 0)

    def test_destroyed_owner_cancels_queued_scroll_and_focus(self):
        with self.page("owner-destroy") as (page, projects, records, shell):
            process, material = self.material_failure(page)
            page._focus_validation_item(self.actual_error(page, material["mass"]))
            window = page.window()
            window.hide()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(window, QEvent.Type.DeferredDelete)
            self.pump()
            self.assertFalse(isValid(page))
            self.assertEqual(len(records.list_all()), 0)


if __name__ == "__main__":
    unittest.main()
