"""Local standard isolation, lazy services and immutable report dispatch."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QWidget

from packages.application.standard_registry import StandardImplementation, StandardRegistry, StandardRuntime, default_standard_registry
from packages.application.catalog_queries import CatalogQueryService
from packages.application.reporting.model import build_report_model
from packages.ui.standard_editors import STANDARD_EDITORS
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute
from apps.carbon_accounting_desktop.product import carbon_accounting_view_model


class StandardDispatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def fake(self, identifier="test_only"):
        return StandardImplementation(identifier, "test", "测试专用标准", identifier,
            Mock(return_value=SimpleNamespace(calculate=Mock())), Mock(), report_factory=Mock(return_value="test report"))

    def test_unknown_standard_and_version_never_fall_back(self):
        registry = default_standard_registry()
        runtime = StandardRuntime(CatalogQueryService.empty(), registry=registry)
        for identifier, version in (("missing", None), (registry.default_standard_id, "2099")):
            with self.assertRaisesRegex(ValueError, "尚未开放"):
                registry.require(identifier, version)
        with self.assertRaises(ValueError):
            runtime.services("missing")
        self.assertEqual(runtime._services, {})

    def test_fake_standard_services_are_lazy_cached_and_isolated(self):
        fake = self.fake()
        runtime = StandardRuntime(CatalogQueryService.empty(), registry=StandardRegistry((fake,)))
        fake.calculator_factory.assert_not_called()
        with patch("packages.application.carbon_material_implementation.create_calculator", side_effect=AssertionError("carbon constructed")):
            first = runtime.services(fake.standard_id)
            self.assertIs(runtime.services(fake.standard_id), first)
            runtime.excel(fake.standard_id)
        fake.calculator_factory.assert_called_once_with(runtime.catalog)
        fake.excel_factory.assert_called_once_with(runtime.catalog, first[2])
        self.assertIsNone(first[1])  # no silent in-memory formal record store

    def test_fake_standard_editor_routes_without_carbon_construction(self):
        fake = self.fake()
        runtime = StandardRuntime(CatalogQueryService.empty(), registry=StandardRegistry((fake,)))
        editor = Mock(side_effect=lambda *_args, **_kwargs: QWidget())
        with patch.dict(STANDARD_EDITORS, {fake.editor_key: editor}):
            shell = AppShell(carbon_accounting_view_model(), Path("absent-logo"), Path("absent-icons"), standard_runtime=runtime)
            try:
                self.assertEqual(set(shell._pages), {AppRoute.HOME})
                fake.calculator_factory.assert_not_called()
                shell._request_standard_accounting(fake.standard_id)
                editor.assert_called_once()
                self.assertEqual(shell.current_route, AppRoute.NEW_ACCOUNTING)
                self.assertEqual(shell.selected_standard_id, fake.standard_id)
                with self.assertRaises(ValueError):
                    shell._request_standard_accounting("missing")
                self.assertEqual(shell.selected_standard_id, fake.standard_id)
            finally:
                shell.deleteLater()
                self.app.processEvents()

    def test_report_uses_recorded_standard_without_carbon_projection(self):
        fake = self.fake()
        record = SimpleNamespace(standard_id=fake.standard_id, standard_version=fake.version)
        registry = StandardRegistry((fake,))
        self.assertEqual(build_report_model(record, {}, {}, {}, {}, {}, standard_registry=registry), "test report")
        fake.report_factory.assert_called_once_with(record, {}, {}, {}, {}, {})
        with self.assertRaises(ValueError):
            build_report_model(SimpleNamespace(standard_id="missing", standard_version=None), {}, {}, {}, {}, {})

    def test_switching_standard_preserves_each_editor_draft(self):
        first, second = self.fake("test_one"), self.fake("test_two")
        runtime = StandardRuntime(CatalogQueryService.empty(), registry=StandardRegistry((first, second)))
        def editor(*_args, **_kwargs):
            widget = QWidget()
            widget.draft = ""
            return widget
        with patch.dict(STANDARD_EDITORS, {first.editor_key: editor, second.editor_key: editor}):
            shell = AppShell(carbon_accounting_view_model(), Path("absent-logo"), Path("absent-icons"), standard_runtime=runtime)
            try:
                shell._request_standard_accounting(first.standard_id)
                first_page = shell.pages[AppRoute.NEW_ACCOUNTING]
                first_page.draft = "半填输入"
                shell._request_standard_accounting(second.standard_id)
                self.assertIsNot(shell.pages[AppRoute.NEW_ACCOUNTING], first_page)
                shell._request_standard_accounting(first.standard_id)
                self.assertIs(shell.pages[AppRoute.NEW_ACCOUNTING], first_page)
                self.assertEqual(first_page.draft, "半填输入")
            finally:
                shell.deleteLater()
                self.app.processEvents()

    def test_fake_excel_page_uses_registered_adapter(self):
        from packages.ui.pages import ExcelImportPage
        fake = self.fake()
        binding = SimpleNamespace(
            template_button_label="下载测试模板", template_description="测试表式",
            regions=lambda _period: (),
        )
        fake.excel_factory.return_value = binding
        runtime = StandardRuntime(CatalogQueryService.empty(), registry=StandardRegistry((fake,)))
        page = ExcelImportPage(standard_runtime=runtime, standard_id=fake.standard_id)
        try:
            self.assertIs(page.excel_adapter, binding)
            self.assertEqual(page.templateButton.text(), "下载测试模板")
            self.assertNotIn("附录 B", page.templateButton.text())
            fake.excel_factory.assert_called_once()
        finally:
            page.deleteLater()
            self.app.processEvents()

    def test_public_composition_does_not_construct_carbon_standard(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("apps/carbon_accounting_desktop/app.py", "packages/ui/shell.py", "packages/ui/pages.py"):
            source = (root / name).read_text(encoding="utf-8")
            self.assertNotIn("CarbonMaterialCalculator(", source, name)
            self.assertNotIn("AppendixBWorkbookImporter(", source, name)
            self.assertNotIn("from packages.standards.carbon_material import", source, name)

    def test_registry_rejects_duplicate_implementations(self):
        fake = self.fake()
        with self.assertRaises(ValueError):
            StandardRegistry((fake, fake))
