"""Nested FGD/material fields must remain inside their actual allocated bodies."""
import unittest
import os
from pathlib import Path
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QPoint,QCoreApplication,QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QLineEdit,QPushButton,QWidget
from tests import test_accounting_projects_ui as fixture
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.ui.view_models import AppRoute


class AccountingEntryLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AccountingProjectUiTests.setUpClass.__func__(cls)
        if not QFontDatabase.families():
            for name in ('msyh.ttc', 'msyhbd.ttc', 'seguisym.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / name))

    @classmethod
    def tearDownClass(cls):
        fixture.AccountingProjectUiTests.tearDownClass.__func__(cls)
    setUp=fixture.AccountingProjectUiTests.setUp
    tearDown=fixture.AccountingProjectUiTests.tearDown
    _new_page=fixture.AccountingProjectUiTests._new_page
    def pump(self):
        for _ in range(16):self.application.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        QTest.qWait(80)
        for _ in range(8):self.application.processEvents()

    def assert_body_contains_fields_and_separates_sections(self,host):
        body=host._entry_body
        for field in body.findChildren(QLineEdit):
            if field.isVisibleTo(body):
                rect=field.rect().translated(field.mapTo(body,QPoint()))
                self.assertTrue(body.rect().contains(rect),(field.objectName(),rect.getRect(),body.rect().getRect()))
        previous=None
        for i in range(body.layout().count()):
            widget=body.layout().itemAt(i).widget()
            if widget is None or widget.isHidden():continue
            rect=widget.rect().translated(widget.mapTo(body,QPoint()))
            if previous is not None:self.assertLess(previous.bottom(),rect.top(),(previous.getRect(),rect.getRect()))
            previous=rect

    def test_nested_fields_and_add_buttons_do_not_overlap_after_width_changes(self):
        window=create_main_window(AppConfig(log_directory=self.root/'logs'),catalog_service=self.catalog_service,record_repository=self.records,project_service=self.project_service,calculation_use_case=self.page.calculation_use_case)
        window.show();shell=window.centralWidget();shell.navigate(AppRoute.NEW_ACCOUNTING);page=shell.pages[AppRoute.NEW_ACCOUNTING]
        try:
            page.source_directory.buttons['fgd'].click()
            unit=page._process_rows['fgd'][0]
            unit['reagent_name'].setText('合成脱硫剂批次的较长身份名称')
            page._add_and_reveal_entry(page._add_fgd_component,unit)
            for width,height in ((1440,1000),(1180,800),(1440,1000)):
                window.resize(width,height);self.pump()
                for component in unit['components']:self.assert_body_contains_fields_and_separates_sections(component['_widget'])
                add=unit['widget'].findChild(QPushButton,'add_fgd_component_'+unit['instance_id'])
                last=unit['components'][-1]['_widget'];last_bottom=last.mapTo(unit['widget'],QPoint(0,last.height())).y()
                self.assertLessEqual(last_bottom,add.mapTo(unit['widget'],QPoint()).y(), {'unit':unit['widget'].size().toTuple(),'unit_body':unit['widget']._entry_body.size().toTuple(),'component_host':unit['component_host'].size().toTuple(),'component_host_min':unit['component_host'].minimumSizeHint().toTuple(),'last':last.size().toTuple(),'last_min':last.minimumSizeHint().toTuple(),'component_host_rect':unit['component_host'].geometry().getRect(),'component_layout_rect':unit['component_host'].layout().geometry().getRect(),'component_layout_margins':unit['component_host'].layout().contentsMargins().top(),'component_layout_spacing':unit['component_host'].layout().spacing(),'children':[(c['_widget'].geometry().getRect(),c['_widget'].minimumHeight(),c['_widget'].parentWidget().objectName()) for c in unit['components']],'add_rect':add.geometry().getRect(),'body_layout_rect':unit['widget']._entry_body.layout().geometry().getRect()})
            page.source_directory.buttons['calcination'].click()
            material=page._process_rows['calcination'][0]['materials'][0]
            toggle=next(button for button in material['widget'].findChildren(QPushButton) if button.text().startswith('数据基准与换算'))
            toggle.setChecked(True)
            for width,height in ((1180,800),(1440,1000)):
                window.resize(width,height);self.pump();self.assert_body_contains_fields_and_separates_sections(material['widget'])
            page.source_directory.buttons['electricity'].click()
            row = page._energy_family_rows['electricity'][0]
            for width, height in ((1180, 800), (1440, 1000)):
                window.resize(width, height)
                self.pump()
                viewport = page.source_directory.editor_scroll.viewport()
                for field in (row._entry_header, row.factor_selector, row.factor_value, row.factor_explanation):
                    self.assertTrue(field.isVisibleTo(viewport))
                    rect = field.rect().translated(field.mapTo(viewport, QPoint()))
                    self.assertGreaterEqual(rect.left(), 0, (field.objectName(), rect.getRect()))
                    self.assertLess(rect.right(), viewport.width(), (field.objectName(), rect.getRect(), viewport.size().toTuple()))
            self.assertEqual(len(self.records.list_all()),0)
        finally:window.hide();window.deleteLater();self.pump()

    def test_natural_gas_wide_to_narrow_reflow_never_clips_controls_inside_editor(self):
        from packages.standards.carbon_material import FuelType
        window = create_main_window(AppConfig(log_directory=self.root/'fuel-logs'), catalog_service=self.catalog_service, record_repository=self.records, project_service=self.project_service, calculation_use_case=self.page.calculation_use_case)
        try:
            window.show()
            shell = window.centralWidget()
            shell.navigate(AppRoute.NEW_ACCOUNTING)
            page = shell.pages[AppRoute.NEW_ACCOUNTING]
            page.source_directory.buttons['fuel'].click()
            row = page._fuel_rows[0]
            row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
            row.fuel_type.confirm_name(force=True)
            row.activity.setText('123.45')
            before = page._capture_form_state()
            for width, height in ((1440, 1000), (1180, 800), (1440, 1000)):
                window.resize(width, height)
                self.pump()
                directory = page.source_directory
                viewport = directory.editor_scroll.viewport()
                self.assertFalse(directory.navigation_panel.isHidden())
                for field in (row.oxidation_control, row.calculated_carbon_label):
                    rect = field.rect().translated(field.mapTo(viewport, QPoint()))
                    self.assertTrue(viewport.rect().contains(rect), (width, field.objectName(), rect.getRect(), viewport.size().toTuple(), directory.editor_scroll.sizeHint().toTuple()))
                buttons = [b for b in page.fuel_rows_host.parentWidget().findChildren(QPushButton) if b.text() == '添加燃料']
                self.assertEqual(len(buttons), 1)
                rect = buttons[0].rect().translated(buttons[0].mapTo(viewport, QPoint()))
                self.assertTrue(viewport.rect().contains(rect), ('add', width, rect.getRect(), viewport.size().toTuple()))
            self.assertEqual(before, page._capture_form_state())
            self.assertFalse(self.records.list_all())
        finally:
            window.hide()
            window.deleteLater()
            self.pump()
