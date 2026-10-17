"""Capture P3-AB Windows Qt offscreen evidence, never native-human evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="标准输入整合 Windows Qt 窗口与缩放核查")
    parser.add_argument("--scale", choices=("1.0", "1.25", "1.5"), required=True)
    parser.add_argument("--width", type=int, choices=(1366, 1920), required=True)
    parser.add_argument("--height", type=int, choices=(768, 1080), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = args.scale

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import CatalogQueryService, ProjectWorkspaceService
    from packages.persistence import InMemoryRecordRepository, SQLiteCatalogRepository, SQLiteProjectWorkspaceRepository, build_catalog_database
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.ui.view_models import AppRoute

    app = QApplication([])
    for font_path in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"):
        QFontDatabase.addApplicationFont(font_path)
    app.setFont(QFont("Microsoft YaHei", 10))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, object] = {
        "evidence_type": "Windows PySide6 native-platform programmatic driver",
        "native_human_acceptance": "OPEN",
        "qt_platform_expected": "windows",
        "requested_logical_window": [args.width, args.height],
        "qt_scale_factor": args.scale,
        "font": "Installed Microsoft YaHei",
        "source_files_sha256": {
            name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ("apps/carbon_accounting_desktop/product.py", "packages/ui/shell.py",
                         "packages/ui/pages.py", "packages/ui/view_models.py", "packages/ui/catalog_pages.py",
                         "packages/ui/carbon_material_fuel.py", "packages/ui/compact_choices.py", "packages/ui/source_cards.py",
                         "packages/application/reporting/presentation.py")
        },
        "captures": [],
        "checks": [],
    }
    prefix = f"{args.width}x{args.height}-{int(float(args.scale)*100)}"
    with tempfile.TemporaryDirectory(prefix="qz-p3-ab-") as directory:
        catalog = build_catalog_database(DEFAULT_SOURCE_PATH, Path(directory) / "catalog.sqlite")
        records = InMemoryRecordRepository()
        window = create_main_window(
            AppConfig(catalog_database=catalog, records_database=Path(directory)/"records.sqlite",
                      projects_database=Path(directory)/"projects.sqlite"),
            catalog_service=CatalogQueryService(SQLiteCatalogRepository(catalog)),
            record_repository=records,
            project_service=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(Path(directory)/"projects.sqlite")),
        )
        window.setFont(QFont("Microsoft YaHei", 10))
        window.resize(args.width, args.height)
        window.show()
        shell = window.centralWidget()

        def settle() -> None:
            for _ in range(6):
                app.processEvents()
                QTest.qWait(15)
            shell.update_content_geometry()
            app.processEvents()

        def capture(name: str) -> None:
            settle()
            pixmap = window.grab()
            filename = f"{prefix}-{name}.png"
            assert pixmap.save(str(args.output_dir / filename)), filename
            evidence["captures"].append({"file": filename, "logical_window": [window.width(), window.height()],
                                         "physical_image": [pixmap.width(), pixmap.height()],
                                         "device_pixel_ratio": pixmap.devicePixelRatio()})

        def check(condition: bool, name: str) -> None:
            evidence["checks"].append({"name": name, "passed": bool(condition)})
            assert condition, name

        settle()
        sidebar = shell.findChild(QFrame, "sidebar")
        check(QApplication.platformName() == "windows", "Windows原生Qt平台")
        check(shell.current_route is AppRoute.HOME and not sidebar.isVisible(), "启动首页无侧栏")
        capture("home")
        accounting = shell.pages[AppRoute.NEW_ACCOUNTING]
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        accounting.enterprise_name.setText("专项合成验收企业")
        shell.navigate(AppRoute.HOME)
        shell.navigate(AppRoute.STANDARDS)
        settle()
        check(sidebar.isVisible(), "业务页显示侧栏")
        page = shell.pages[AppRoute.STANDARDS]
        table = page.standard_table
        check([table.horizontalHeaderItem(i).text() for i in range(table.columnCount())] ==
              ["标准编号", "标准名称", "标准状态", "实施日期", "软件支持"], "标准列表五列")
        capture("standards")
        page.search_input.setText("32151.34")
        settle()
        check(table.rowCount() == 1, "真实目录关键词检索")
        name_item = table.item(0, 1)
        QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, pos=table.visualItemRect(name_item).center())
        settle()
        check(page.selected_standard_id == "gbt_32151_34_2024" and page.detail_host.isVisible(), "名称进入正确详情")
        titles = [label.text() for label in page.detail_host.findChildren(QLabel, "cardTitle") if label.isVisible()]
        check(set(titles) >= {"基本信息", "适用范围", "标准要求"}, "详情连续三分区")
        capture("standard-detail")
        back = page.findChild(QPushButton, "backToStandardListButton")
        back.click()
        settle()
        check(page.search_input.text() == "32151.34" and table.currentRow() == 0, "返回保留查询和选中")
        table.setCurrentCell(0, 0)
        table.setFocus()
        QTest.keyClick(table, Qt.Key.Key_Return)
        settle()
        check(page.detail_host.isVisible() and page.selected_standard_id == "gbt_32151_34_2024", "编号键盘进入正确详情")
        page.findChild(QPushButton, "backToStandardListButton").click()
        page.search_input.setText("不存在的标准")
        settle()
        check(table.rowCount() == 0, "无搜索结果真实空状态")
        capture("standards-empty")
        for route in (AppRoute.FACTORS, AppRoute.RECORDS, AppRoute.EXCEL_IMPORT, AppRoute.HOME, AppRoute.NEW_ACCOUNTING):
            shell.navigate(route)
            settle()
            capture(route.value)
            check(shell.pages[AppRoute.NEW_ACCOUNTING] is accounting and accounting.enterprise_name.text() == "专项合成验收企业",
                  f"{route.value}切换保留核算页及未完成输入")
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        settle()
        row = accounting._fuel_rows[0]
        row.path_choices.group.buttons()[1].click()
        check(row.path.currentData() is not None, "二选控件写入既有业务值")
        accounting._source_toggle_buttons["fuel"].click()
        settle()
        window.findChild(QScrollArea, "mainScrollArea").ensureWidgetVisible(row)
        capture("fuel-entry")
        accounting._source_toggle_buttons["fgd"].click()
        settle()
        window.findChild(QScrollArea, "mainScrollArea").ensureWidgetVisible(accounting._source_cards["CAR-SRC-FGD-001"])
        capture("fgd-entry")
        check(len(records.list_all()) == 0, "界面核查未生成正式记录")
        from packages.application.carbon_accounting import CarbonAccountingUseCase
        excel = shell.pages[AppRoute.EXCEL_IMPORT]
        excel.import_enterprise_name.setText("专项合成验收企业")
        excel.import_period_type.setCurrentIndex(excel.import_period_type.findData("ANNUAL"))
        excel.import_period_start.setText("2026-01-01")
        excel.import_period_end.setText("2026-12-31")
        excel.import_boundary_confirmed.setChecked(True)
        from tests.exb01_fixture_helper import write_valid_appendix_b_workbook
        from openpyxl import load_workbook
        sample = write_valid_appendix_b_workbook(Path(directory) / "synthetic-complete.xlsx", all_sources=True)
        workbook = load_workbook(sample)
        workbook["B.2"]["A4"] = "天然气"
        workbook.save(sample)
        workbook.close()
        excel._preview_workbook(sample)
        check(excel._last_preview is not None, "完整附录B预览")
        shell.navigate(AppRoute.EXCEL_IMPORT)
        capture("excel-preview")
        unit = excel._last_preview.units[0]
        check(unit.can_calculate and len(records.list_all()) == 0, "有效预览零Record")
        outcome = shell.calculation_use_case.calculate(unit.input_value)
        check(outcome.successful and len(records.list_all()) == 1, "正式成功新增一条Record")
        shell.navigate(AppRoute.HOME)
        capture("home-record")
        shell.navigate(AppRoute.RECORDS)
        record_page = shell.pages[AppRoute.RECORDS]
        record_page.open_record(outcome.record.record_id)
        capture("record-detail")
        record_page.detail_tabs.setCurrentIndex(1) if hasattr(record_page, "detail_tabs") else None
        capture("record-tables")
        # Dispose this isolated screenshot fixture; close-confirmation is covered by lifecycle regression.
        accounting.enterprise_name.clear()
        window.hide()
        window.deleteLater()
        app.processEvents()
    manifest = args.output_dir / f"{prefix}.json"
    manifest.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"PASS {prefix}: {len(evidence['checks'])} checks; {len(evidence['captures'])} Windows-platform captures; human OS-DPI acceptance=OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
