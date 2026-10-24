"""Capture actual Qt with independent per-size stores and explicitly typed scenes.

Synthetic Excel is parsed through the existing adapter; the mixed panel is a
render-only fixture. Project save is isolated. No user stores/desktop/Office/URLs
or Word export are used. Seed calculations only populate temporary Record data.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import date
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True, encoding="utf8").strip()


def sources():
    files = sorted((REPO / "packages/ui").glob("*.py")) + [Path(__file__).resolve()]
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert git("remote", "get-url", "origin").lower().rstrip("/").removesuffix(".git") == "https://github.com/adgo07/ghgtool"
    output = args.output.resolve()
    if output.exists(): parser.error("输出目录已存在，不覆盖既有证据")
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt, qVersion
    from PySide6.QtGui import QFontInfo, QFontDatabase, QFont, QRawFont
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea, QToolButton, QWidget
    from shiboken6 import isValid
    from openpyxl import load_workbook
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application.catalog_queries import CatalogQueryService
    from packages.application.project_workspaces import ProjectWorkspaceService
    from packages.application.carbon_accounting import CarbonAccountingUseCase
    from packages.persistence import (SQLiteCatalogRepository, SQLiteRecordRepository,
        SQLiteProjectWorkspaceRepository, SQLiteSettingsRepository, build_catalog_database)
    from packages.excel.templates import ExcelTemplateService
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.standards.carbon_material import CarbonMaterialCalculator
    from packages.standards.carbon_material_external_co2 import ExternalCO2Input
    from packages.ui.export_location import ExportLocationService
    from packages.ui.view_models import AppRoute
    from tests.test_b1_fuel_lifecycle import fuel_input
    from tests.test_g07_records import _record
    output.mkdir(parents=True)
    app = QApplication.instance() or QApplication([])
    # Headless Qt on this host does not enumerate native fonts. Register existing
    # Windows system fonts in this capture process only; never ship font files.
    font_bootstrap = []
    for name in ("msyh.ttc", "msyhbd.ttc", "seguisym.ttf"):
        path = Path(os.environ["WINDIR"]) / "Fonts" / name
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            font_bootstrap.append({"file": name, "families": QFontDatabase.applicationFontFamilies(font_id),
                                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    raw_font = QRawFont.fromFont(QFont("Microsoft YaHei UI", 10))
    assert raw_font.isValid() and raw_font.supportsCharacter(ord("碳")), "CJK font unavailable; do not publish tofu screenshots"
    errors = []
    old_hook = sys.excepthook
    sys.excepthook = lambda typ, exc, tb: errors.append("".join(traceback.format_exception(typ, exc, tb)))
    summary = {"kind": "actual-Qt-offscreen", "head": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")), "source_sha256": sources(),
        "qt": qVersion(), "pyside": pyside_version, "platform": app.platformName(),
        "font_bootstrap": font_bootstrap, "cjk_glyph_probe": True,
        "catalog_fixture_as_of": "2026-09-12", "data": "synthetic isolated stores",
        "scenes": [], "callback_errors": errors, "status": "RUNNING"}
    window = None
    try:
        with tempfile.TemporaryDirectory(prefix="ghg-business-capture-") as directory:
            base = Path(directory)
            catalog_path = build_catalog_database(DEFAULT_SOURCE_PATH, base / "catalog.sqlite")
            catalog = CatalogQueryService(SQLiteCatalogRepository(catalog_path), as_of=date(2026, 9, 12))
            for width, height in ((1440, 1000), (1180, 800)):
                root = base / str(width)
                root.mkdir()
                records = SQLiteRecordRepository(root / "records.sqlite")
                seed = CarbonAccountingUseCase(CarbonMaterialCalculator(), records)
                record_ids = {}
                for label, amount in (("supplement", "20"), ("pending", None)):
                    result = seed.calculate(replace(fuel_input(), enterprise_name="合成界面验证企业·长中文名称用于检查列表换行及详情标题可读性",
                        external_co2=ExternalCO2Input(True, amount)))
                    assert result.successful, result.problems
                    record_ids[label] = result.record.record_id
                records.create(_record("ui.capture.legacy"))
                projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root / "projects.sqlite"))
                exports = ExportLocationService(SQLiteSettingsRepository(root / "user.sqlite"))
                exports.set_preferred_directory(root / "合成中文导出路径用于检查完整显示与更改按钮" / "报告与输入模板统一位置")
                window = create_main_window(AppConfig(catalog_database=catalog_path), catalog_service=catalog,
                    record_repository=records, project_service=projects, export_location_service=exports)
                window.resize(width, height)
                window.show()
                shell = window.centralWidget()

                def flush():
                    for _ in range(7): app.processEvents()
                    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                    app.processEvents()
                    if errors: raise RuntimeError("Qt callback error: " + errors[-1])

                def grab(name, *, target=None, pane=None, inner_target=None, kind="actual-Qt-synthetic-data"):
                    flush()
                    shell.main_scroll_area.verticalScrollBar().setValue(0)
                    if target is not None:
                        shell.main_scroll_area.ensureWidgetVisible(target, 0, 18)
                    flush()
                    if pane is not None:
                        if inner_target is not None:
                            top = inner_target.mapTo(pane.content, QPoint()).y()
                            pane.scroll_area.verticalScrollBar().setValue(max(0, top - 8))
                        else:
                            pane.scroll_area.verticalScrollBar().setValue(pane.scroll_area.verticalScrollBar().maximum())
                    flush()
                    if inner_target is not None:
                        viewport = pane.scroll_area.viewport()
                        rectangle = QRect(inner_target.mapTo(viewport, QPoint()), inner_target.size())
                        # A heading spans the horizontally scrollable report content;
                        # prove its painted text, rather than trailing empty space, fits.
                        rectangle.setWidth(min(rectangle.width(), inner_target.fontMetrics().horizontalAdvance(inner_target.text()) + 4))
                        assert viewport.rect().contains(rectangle), (name, rectangle.getRect(), viewport.rect().getRect())
                    pixmap = window.grab()
                    filename = f"{width}-{name}.png"
                    if name.startswith("standard-detail-") and name.endswith("-bottom"):
                        previous = output / f"{width}-{name.removesuffix('-bottom')}.png"
                        from PySide6.QtCore import QBuffer, QIODevice
                        buffer = QBuffer()
                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                        pixmap.save(buffer, "PNG")
                        if previous.is_file() and previous.read_bytes() == bytes(buffer.data()):
                            return
                    assert pixmap.save(str(output / filename))
                    current = shell.page_stack.currentWidget()
                    fonts = []
                    for label in current.findChildren(QLabel):
                        if label.isVisible() and label.objectName() in {"pageTitle", "standardDetailName", "recordFrozenTotal", "cardTitle"}:
                            info = QFontInfo(label.font())
                            fonts.append({"name": label.objectName(), "family": info.family(), "pixel_size": info.pixelSize(), "point_size": info.pointSizeF()})
                    summary["scenes"].append({"file": filename, "kind": kind, "window": [window.width(), window.height()],
                        "image": [pixmap.width(), pixmap.height()], "dpr": pixmap.devicePixelRatio(),
                        "font": QFontInfo(window.font()).family(), "effective_fonts": fonts,
                        "outer_scroll": shell.main_scroll_area.verticalScrollBar().value(),
                        "inner_scrolls": [{"name": area.objectName(), "value": area.verticalScrollBar().value(),
                            "maximum": area.verticalScrollBar().maximum()} for area in current.findChildren(QScrollArea) if area.isVisible()],
                        "target_visible": inner_target.text() if inner_target is not None else None,
                        "sha256": hashlib.sha256((output / filename).read_bytes()).hexdigest()})

                shell.navigate(AppRoute.HOME)
                grab("home-protected")
                shell.navigate(AppRoute.STANDARDS)
                standard = shell.pages[AppRoute.STANDARDS]
                standard.search_input.clear()
                grab("standards")
                for standard_id, label in (("gbt_32151_34_2024", "industry"), ("gbt_32150_2025", "general"), ("gbt_32151_7_2023", "unavailable")):
                    standard.search_input.clear()
                    row = next(i for i in range(standard.standard_table.rowCount()) if standard.standard_table.item(i, 0).data(256) == standard_id)
                    standard.standard_table.cellActivated.emit(row, 1)
                    assert standard.view_stack.currentWidget() is standard.detail_host
                    grab("standard-detail-" + label)
                    labels = standard.detail_host.findChildren(QLabel, "standardRequirementText")
                    grab("standard-detail-" + label + "-bottom", target=labels[-1])
                    standard.findChild(QPushButton, "backToStandardListButton").click()
                standard.search_input.setText("不存在的标准")
                assert standard.standard_table.rowCount() == 0
                grab("standard-empty")
                standard.search_input.clear()
                assert standard.standard_table.rowCount() > 0
                shell.navigate(AppRoute.FACTORS)
                factor = shell.pages[AppRoute.FACTORS]
                factor.view_mode_filter.setCurrentIndex(0)
                assert not factor.search_input.isVisible()
                grab("factor-browse")
                factor.view_mode_filter.setCurrentIndex(1)
                factor.search_input.setText("0.11")
                assert factor.search_result_table.rowCount() > 0
                asset_row = next(i for i, item in enumerate(factor._search_results) if item.asset is not None)
                factor.search_result_table.selectRow(asset_row)
                flush()
                assert factor.findChild(QLabel, "parameterReferenceValue") is not None
                assert factor.factor_detail_scroll.height() >= 280
                grab("factor-search")
                toggle = factor.findChild(QToolButton, "parameterDetailTraceToggle")
                if toggle is not None:
                    toggle.setChecked(True)
                    flush()
                    trace = factor.findChild(QWidget, "parameterDetailTrace")
                    assert trace is not None and trace.isVisible()
                    assert toggle.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextBesideIcon
                    trace_top = toggle.mapTo(factor.factor_detail_scroll.widget(), QPoint()).y()
                    factor.factor_detail_scroll.verticalScrollBar().setValue(trace_top)
                    flush()
                    grab("factor-search-trace", target=factor.factor_detail_scroll)
                longest = max((item for item in catalog.search_reference_library("") if item.asset is not None),
                              key=lambda item: len(item.value_text or ""))
                factor.search_input.setText(longest.value_text)
                asset_row = next(i for i, item in enumerate(factor._search_results) if item.key == longest.key)
                factor.search_result_table.selectRow(asset_row)
                flush()
                assert factor.findChild(QLabel, "parameterReferenceValue").text() == format(longest.asset.value, "f")
                grab("factor-longest-registered-value")
                factor.search_input.setText("不存在的参数")
                assert factor.search_result_table.rowCount() == 0
                grab("factor-empty")
                factor.search_input.setText("0.11")
                factor.view_mode_filter.setCurrentIndex(0)
                factor.view_mode_filter.setCurrentIndex(1)
                assert factor.search_input.text() == "0.11" and factor.search_result_table.rowCount() > 0
                shell.navigate(AppRoute.EXCEL_IMPORT)
                imported = shell.pages[AppRoute.EXCEL_IMPORT]
                assert imported._last_preview is None and imported._workspace is None
                assert imported.preview_panel.units.rowCount() == 0 and not imported.calculate_button.isEnabled()
                grab("import-initial")
                grab("import-initial-bottom", target=imported.status_label)
                imported.preview_panel.set_summary("渲染夹具：1个可保存单元、1个需修正单元；未解析Excel", state="warning")
                imported.preview_panel.set_units((("合成全厂单元", "可保存", "1.00 tCO₂"), ("合成工序单元", "需修正", "—")))
                imported.preview_panel.set_details("渲染夹具 B.2!B14：活动量未填写。\n仅验证面板排版，不代表真实工作簿检查结果。")
                grab("import-mixed-render-fixture", kind="render-only-fixture-NOT-workbook-validation")
                grab("import-mixed-render-fixture-bottom", target=imported.status_label, kind="render-only-fixture-NOT-workbook-validation")
                # Real synthetic workbook, through unchanged selection/preview/save signals.
                workbook = load_workbook(BytesIO(ExcelTemplateService.default().read_bytes()))
                fuel = workbook["B.2"]
                fuel["C14"] = "10⁴Nm³"
                fuel["A14"], fuel["B14"] = "天然气", 1.25
                fuel["E14"], fuel["G14"], fuel["J14"], fuel["N14"] = "计算值", "缺省值", "缺省值", "缺省值"
                workbook_path = root / "合成Excel输入.xlsx"
                workbook.save(workbook_path)
                workbook.close()
                imported.import_enterprise_name.setText("合成Excel预览企业")
                imported.import_period_type.setCurrentIndex(imported.import_period_type.findData("ANNUAL"))
                imported.import_period_start.setText("2025-01-01")
                imported.import_period_end.setText("2025-12-31")
                imported.import_boundary_confirmed.setChecked(True)
                imported._select_workbook(workbook_path)
                imported.preview_button.click()
                flush()
                assert imported._last_preview is not None and imported._last_preview.units[0].can_calculate
                assert imported.preview_panel.units.rowCount() == 1 and len(records.list_all()) == 3
                grab("import-valid-synthetic-workbook", kind="actual-adapter-synthetic-workbook")
                grab("import-valid-synthetic-workbook-bottom", target=imported.status_label, kind="actual-adapter-synthetic-workbook")
                imported.project_name.setText("合成Excel项目·仅本次截图临时库")
                imported.save_project_button.click()
                flush()
                assert len(projects.list_all()) == 1 and imported.calculate_button.isEnabled()
                assert len(records.list_all()) == 3
                grab("import-saved-project-bottom", target=imported.status_label, kind="actual-save-temporary-project-NO-formal-Record")
                shell.navigate(AppRoute.RECORDS)
                record_page = shell.pages[AppRoute.RECORDS]
                record_page._back_to_list()
                record_page.search_input.setText("不存在的记录")
                assert len(record_page._records) == 0
                grab("records-empty")
                record_page.search_input.clear()
                assert len(record_page._records) == 3 and record_page.record_list.columnSpan(0, 0) == 1
                grab("records-restored")
                for key in ("supplement", "pending"):
                    assert record_page.open_record(record_ids[key])
                    record_page.detail_tabs.setCurrentIndex(0)
                    assert record_page.detail_tabs.currentIndex() == 0
                    grab("record-summary-" + key)
                    # The existing frozen-model routing puts software supplement
                    # in input/basis; do not move data between tabs for a screenshot.
                    record_page.detail_tabs.setCurrentIndex(1)
                    flush()
                    supplement_heading = next(label for label in record_page.input_basis_view.findChildren(QLabel, "recordReportSectionTitle")
                                              if "外部CO₂软件补充" in label.text())
                    grab("record-software-supplement-" + key, target=record_page.detail_tabs,
                         pane=record_page.input_basis_view, inner_target=supplement_heading)
                    if key == "supplement":
                        record_page.detail_tabs.setCurrentIndex(0)
                        grab("record-summary-bottom", target=record_page.detail_tabs, pane=record_page.summary_view)
                        record_page.detail_tabs.setCurrentIndex(1)
                        grab("record-basis-bottom", target=record_page.detail_tabs, pane=record_page.input_basis_view)
                        if record_page.input_basis_view.audit_toggle is not None:
                            record_page.input_basis_view.audit_toggle.setChecked(True)
                            grab("record-basis-source-bottom", target=record_page.detail_tabs, pane=record_page.input_basis_view)
                    record_page._back_to_list()
                assert record_page.open_record("ui.capture.legacy")
                record_page.detail_tabs.setCurrentIndex(0)
                grab("record-legacy-missing")
                record_page._back_to_list()
                shell.navigate(AppRoute.SETTINGS)
                grab("settings-long-path")
                assert len(records.list_all()) == 3
                window.close()
                window.deleteLater()
                flush()
                assert not isValid(window)
                window = None
            # Compare native checkbox indicators under the unchanged baseline
            # and page-local styles; this is evidence, not a theme modification.
            from PySide6.QtCore import QBuffer, QIODevice
            from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QStyle, QStyleOptionButton
            from packages.ui.design_tokens import application_stylesheet
            from packages.ui.business_page_style import apply_business_page_style
            indicator_hashes = {}
            comparison_images = {}
            for key in ("baseline", "business-page"):
                probe = QWidget()
                probe.setFont(QFont("Microsoft YaHei UI", 10))
                probe.setStyleSheet(application_stylesheet())
                if key == "business-page":
                    apply_business_page_style(probe)
                probe.resize(360, 70)
                check = QCheckBox("已确认组织边界", probe)
                check.setChecked(True)
                QHBoxLayout(probe).addWidget(check)
                probe.show()
                flush()
                option = QStyleOptionButton()
                check.initStyleOption(option)
                indicator = check.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, check)
                pixmap = check.grab()
                filename = f"checkbox-{key}.png"
                assert pixmap.save(str(output / filename))
                comparison_images[filename] = hashlib.sha256((output / filename).read_bytes()).hexdigest()
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                assert pixmap.copy(indicator).save(buffer, "PNG")
                indicator_hashes[key] = hashlib.sha256(bytes(buffer.data())).hexdigest()
                probe.close()
                probe.deleteLater()
                flush()
                assert not isValid(probe)
            baseline_blob = git("rev-parse", "origin/main:packages/ui/design_tokens.py")
            current_blob = git("hash-object", "--path=packages/ui/design_tokens.py", "packages/ui/design_tokens.py")
            assert baseline_blob == current_blob
            assert indicator_hashes["baseline"] == indicator_hashes["business-page"], indicator_hashes
            summary["checkbox_comparison"] = {"images_sha256": comparison_images,
                "indicator_sha256": indicator_hashes, "indicators_identical": True,
                "baseline_theme_blob": baseline_blob, "global_theme_unchanged": True}
            assert summary["source_sha256"] == sources(), "source changed during capture"
            summary["status"] = "CAPTURE_COMPLETED_NOT_RELEASE_ACCEPTANCE"
    except BaseException:
        summary["status"] = "FAILED"
        raise
    finally:
        if window is not None and isValid(window):
            window.close()
            window.deleteLater()
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        sys.excepthook = old_hook
        (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
        scenes = ''.join('<section><h2>' + s['file'] + '</h2><p>' + s['kind'] + '</p><img loading="lazy" src="' + s['file'] + '"></section>' for s in summary['scenes'])
        if summary.get("checkbox_comparison"):
            scenes += '<h2>原有复选框与局部样式对照</h2>' + ''.join(
                '<section><h3>' + filename + '</h3><img src="' + filename + '"></section>'
                for filename in summary["checkbox_comparison"]["images_sha256"])
        (output / "review.html").write_text('<!doctype html><meta charset="utf-8"><title>五页实际Qt</title><style>body{font:16px sans-serif;margin:24px;background:#edf3f8}section{margin:24px 0}img{max-width:100%;border:1px solid #bbb}</style><h1>五页实际Qt离屏图</h1><p>隔离合成数据；混合预览明确为渲染夹具，其他Excel场景使用合成工作簿和既有Adapter；非原生Windows/Office/IME验收。</p>' + scenes, encoding="utf8")
    print("Captured actual Qt pages:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
