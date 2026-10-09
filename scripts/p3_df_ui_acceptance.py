"""Capture P3-DF Qt offscreen evidence for the D/F presentation surfaces.

This script deliberately exercises the production Catalog, application and
calculator paths with an isolated temporary database.  It does not represent
native Windows acceptance: the manifest keeps that boundary explicit.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


WINDOWS = {
    (1366, 768),
    (1920, 1080),
}
SCALES = ("1.0", "1.25", "1.5")
SOURCE_IDS = {
    "CAR-SRC-FUEL-001": "fuel",
    "CAR-SRC-CALCINATION-001": "calcination",
    "CAR-SRC-BAKING-001": "baking",
    "CAR-SRC-GRAPHITIZATION-001": "graphitization",
    "CAR-SRC-FUME-INCINERATION-001": "fume",
    "CAR-SRC-FGD-001": "fgd",
    "CAR-SRC-PURCHASED-ELECTRICITY-001": "electricity",
    "CAR-SRC-EXPORTED-ELECTRICITY-001": "electricity",
    "CAR-SRC-PURCHASED-HEAT-001": "heat",
    "CAR-SRC-EXPORTED-HEAT-001": "heat",
}
SOURCE_FILES = (
    "scripts/p3_df_ui_acceptance.py",
    "apps/carbon_accounting_desktop/app.py",
    "packages/ui/catalog_pages.py",
    "packages/ui/carbon_material_page.py",
    "packages/ui/shell.py",
    "packages/ui/view_models.py",
    "packages/ui/design_tokens.py",
)


def _lf_sha256(path: Path) -> str:
    """Hash source after normalising line endings to Git's LF form."""

    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _source_hashes() -> dict[str, str]:
    return {
        name: _lf_sha256(ROOT / name)
        for name in SOURCE_FILES
        if (ROOT / name).is_file()
    }


def _find_row(table: object, predicate) -> int:
    row_count = int(table.rowCount())
    column_count = int(table.columnCount())
    for row in range(row_count):
        values = tuple(
            table.item(row, column).text() if table.item(row, column) is not None else ""
            for column in range(column_count)
        )
        if predicate(values):
            return row
    raise AssertionError(f"未找到真实目录行；当前行数={row_count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="P3-DF 参数与因子库及新建核算 Qt 离屏验收")
    parser.add_argument("--scale", choices=SCALES, required=True)
    parser.add_argument("--width", type=int, choices=(1366, 1920), required=True)
    parser.add_argument("--height", type=int, choices=(768, 1080), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.width, args.height) not in WINDOWS:
        parser.error("--width/--height 只支持 1366x768 或 1920x1080")

    # These variables must be set before QApplication is constructed.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = args.scale

    from PySide6.QtCore import QCoreApplication, QEvent, Qt
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QToolButton,
        QWidget,
    )

    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import CatalogQueryService, ProjectWorkspaceService
    from packages.persistence import (
        InMemoryRecordRepository,
        SQLiteCatalogRepository,
        SQLiteProjectWorkspaceRepository,
        build_catalog_database,
    )
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.standards.carbon_material import FuelPath
    from packages.ui.view_models import AppRoute

    app = QApplication.instance() or QApplication([])
    for font_path in (
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ):
        QFontDatabase.addApplicationFont(font_path)
    app.setFont(QFont("Microsoft YaHei", 10))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{args.width}x{args.height}-{int(float(args.scale) * 100)}"
    evidence: dict[str, object] = {
        "evidence_type": "Windows PySide6 offscreen automated",
        "native_human_acceptance": "OPEN",
        "native_evidence_boundary": "离屏 Qt 截图和模拟缩放不能替代原生 Windows 鼠标、键盘、DPI 与窗口验收。",
        "requested_logical_window": [args.width, args.height],
        "qt_scale_factor": args.scale,
        "font": "Microsoft YaHei primary with Segoe UI regular/bold registered for offscreen Unicode-subscript fallback",
        "fixture": {
            "name": "P3-DF-real-calculation-fuel-and-electricity",
            "catalog": "DEFAULT_SOURCE_PATH copied to an isolated temporary catalog.sqlite",
            "record_repository": "InMemoryRecordRepository",
            "calculation": "真实 CarbonAccountingUseCase/CarbonMaterialCalculator 路径，非 mock、非预置结果",
            "user_data_impact": "zero; projects.sqlite/catalog.sqlite/records.sqlite all remain temporary or in-memory",
        },
        "source_files_sha256_lf": _source_hashes(),
        "captures": [],
        "checks": [],
    }

    def check(condition: bool, name: str) -> None:
        checks = evidence["checks"]
        assert isinstance(checks, list)
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    with tempfile.TemporaryDirectory(prefix="qz-p3-df-") as directory:
        directory_path = Path(directory)
        catalog_path = build_catalog_database(DEFAULT_SOURCE_PATH, directory_path / "catalog.sqlite")
        records = InMemoryRecordRepository()
        project_database = directory_path / "projects.sqlite"
        catalog_service = CatalogQueryService(SQLiteCatalogRepository(catalog_path))
        project_service = ProjectWorkspaceService(
            SQLiteProjectWorkspaceRepository(project_database)
        )
        window = create_main_window(
            AppConfig(
                catalog_database=catalog_path,
                records_database=directory_path / "records.sqlite",
                projects_database=project_database,
            ),
            catalog_service=catalog_service,
            record_repository=records,
            project_service=project_service,
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
            output = args.output_dir / filename
            check(pixmap.save(str(output)), f"截图写入：{filename}")
            logical = [window.width(), window.height()]
            physical = [pixmap.width(), pixmap.height()]
            logical_ratio = logical[0] / logical[1]
            image_ratio = physical[0] / physical[1]
            captures = evidence["captures"]
            assert isinstance(captures, list)
            captures.append(
                {
                    "file": filename,
                    "logical_window": logical,
                    "physical_image": physical,
                    "device_pixel_ratio": pixmap.devicePixelRatio(),
                    "logical_ratio": round(logical_ratio, 8),
                    "image_ratio": round(image_ratio, 8),
                }
            )
            check(abs(image_ratio - logical_ratio) < 0.01, f"截图宽高比：{filename}")

        # D — source-file browsing, backed by the real catalog database.
        shell.navigate(AppRoute.FACTORS)
        settle()
        factors = shell.pages[AppRoute.FACTORS]
        browse_mode = factors.view_mode_filter.findData("browse")
        factors.view_mode_filter.setCurrentIndex(0 if browse_mode < 0 else browse_mode)
        source_index = factors.source_filter.findData("SRC-32151-34-2024")
        check(source_index >= 0, "D：真实 GB/T 32151.34 来源文件存在")
        factors.source_filter.setCurrentIndex(source_index)
        table_index = factors.table_filter.findText("C.1", Qt.MatchFlag.MatchContains)
        check(table_index >= 0, "D：真实来源表 C.1 存在")
        factors.table_filter.setCurrentIndex(table_index)
        settle()
        source_table = factors.factor_table
        check(source_table.rowCount() >= 20, "D：来源表真实多行数据显示")
        check(source_table.columnCount() == 5, "D：来源表列结构真实显示")
        check(
            source_table.item(0, 0) is not None and bool(source_table.item(0, 0).text().strip()),
            "D：来源表第一列有真实值",
        )
        check(
            source_table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers,
            "D：来源表只读",
        )
        check(
            all(
                not bool(source_table.item(row, column).flags() & Qt.ItemFlag.ItemIsEditable)
                for row in range(source_table.rowCount())
                for column in range(source_table.columnCount())
                if source_table.item(row, column) is not None
            ),
            "D：来源表单元格不可编辑",
        )
        source_scrollbar = source_table.verticalScrollBar()
        check(source_scrollbar.maximum() > 0, "D：长来源表可滚动")
        source_scrollbar.setValue(source_scrollbar.maximum())
        settle()
        check(source_scrollbar.value() == source_scrollbar.maximum(), "D：长来源表滚动位置可访问")
        capture("d-source-browse")

        # D — full-library search and a real registered parameter detail.
        search_mode = factors.view_mode_filter.findData("search")
        factors.view_mode_filter.setCurrentIndex(1 if search_mode < 0 else search_mode)
        factors.search_input.setText("0.11")
        settle()
        search_table = factors.search_result_table
        check(search_table.rowCount() > 0, "D：全库搜索返回真实结果")
        heat_row = _find_row(
            search_table,
            lambda values: values[0] == "参数值" and "外购热力" in values[1],
        )
        search_table.selectRow(heat_row)
        settle()
        check(
            search_table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers,
            "D：全库搜索表只读",
        )
        # Search rows are populated by the presentation model; the table-level
        # NoEditTriggers contract is the stable read-only boundary.
        detail_host = factors.findChild(QWidget, "parameterDetailHost")
        check(detail_host is not None, "D：参数只读详情容器存在")
        trace_toggle = factors.findChild(QToolButton, "parameterDetailTraceToggle")
        if trace_toggle is not None and not trace_toggle.isChecked():
            trace_toggle.click()
            settle()
        check(trace_toggle is not None and trace_toggle.isChecked(), "D：完整来源追溯可展开")
        detail_text = "\n".join(label.text() for label in factors.findChildren(QLabel) if label.isVisible())
        check("0.11" in detail_text and "tCO₂/GJ" in detail_text, "D：详情显示真实数值和单位")
        check("7.5.6" in detail_text and "表C.3" in detail_text, "D：详情显示真实来源定位")
        check(
            not (detail_host.findChildren(QLineEdit) if detail_host is not None else ()),
            "D：详情没有可编辑输入框",
        )
        factor_detail_scroll = factors.findChild(QScrollArea, "parameterDetailScroll")
        check(factor_detail_scroll is not None, "D：详情长内容滚动容器存在")
        assert factor_detail_scroll is not None
        capture("d-search-detail")
        detail_scrollbar = factor_detail_scroll.verticalScrollBar()
        detail_scrollbar.setValue(detail_scrollbar.maximum())
        settle()
        check(
            detail_scrollbar.value() == detail_scrollbar.maximum(),
            "D：完整来源追溯滚动位置可访问",
        )
        capture("d-source-trace")

        factors.search_input.setText("P3-DF不存在的资料")
        settle()
        check(search_table.rowCount() == 0, "D：全库搜索真实空状态")
        empty_description = factors.findChild(QLabel, "emptyStateDescription")
        check(
            empty_description is not None and "没有找到" in empty_description.text(),
            "D：空状态使用业务化反馈",
        )
        capture("d-search-empty")

        # F — empty state and preservation of the existing in-memory page.
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        settle()
        accounting = shell.pages[AppRoute.NEW_ACCOUNTING]
        check(not accounting.result_card.isVisible(), "F：未计算时结果区域为空态")
        check(not accounting.process_card.isVisible(), "F：未计算时过程区域隐藏")
        check(not accounting.quality_card.isVisible(), "F：未计算时问题区域隐藏")
        status_bar = accounting.findChild(QWidget, "calculationStatusBar")
        check(status_bar is not None and status_bar.isVisible(), "F：未计算时状态栏可见")
        check("计算排放量" in accounting.calculation_status_hint.text(), "F：未计算时操作提示真实可见")
        shell.main_scroll_area.verticalScrollBar().setValue(0)
        capture("f-empty")

        accounting.enterprise_name.setText("P3-DF状态保留测试企业")
        accounting.period_year.setValue(2026)
        shell.navigate(AppRoute.HOME)
        shell.navigate(AppRoute.FACTORS)
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        settle()
        check(
            accounting.enterprise_name.text() == "P3-DF状态保留测试企业"
            and accounting.period_year.value() == 2026,
            "F：切换业务页面保留未完成输入状态",
        )

        # F — multiple real UI detail rows, without inventing a result.
        for source_id in (
            "CAR-SRC-FUEL-001",
            "CAR-SRC-PURCHASED-ELECTRICITY-001",
        ):
            group_button = accounting._source_toggle_buttons[SOURCE_IDS[source_id]]
            if not accounting._source_is_enabled(source_id):
                group_button.click()
        accounting.add_fuel_button.click()
        add_electricity = accounting.findChild(QPushButton, "addUnifiedElectricityRow")
        check(add_electricity is not None, "F：新增电力明细入口存在")
        assert add_electricity is not None
        add_electricity.click()
        settle()
        check(len(accounting._fuel_rows) >= 2, "F：多个燃料明细真实生成")
        check(len(accounting._energy_family_rows["electricity"]) >= 2, "F：多个电力明细真实生成")
        check(
            any(row.remove_button.isVisible() for row in accounting._fuel_rows[1:]),
            "F：次级燃料明细具备删除控制",
        )
        long_form_scroll = shell.main_scroll_area.verticalScrollBar()
        check(long_form_scroll.maximum() > 0, "F：长核算表单可滚动")
        long_form_scroll.setValue(long_form_scroll.maximum())
        settle()
        check(long_form_scroll.value() == long_form_scroll.maximum(), "F：长核算表单滚动位置可访问")
        capture("f-multiple-details")

        # Reset only the isolated presentation fixture before the formal result.
        reset = getattr(accounting, "_reset_for_new_accounting", None)
        check(callable(reset), "F：测试fixture可重置")
        assert callable(reset)
        reset()
        settle()
        check(len(records.list_all()) == 0, "F：正式计算前隔离记录库为空")

        # Explicit fixture from the supported fuel/electricity path.  The
        # expected total below is computed by the real calculator immediately
        # before the UI invokes the formal Application use case.
        accounting.enterprise_name.setText("P3-DF真实计算测试企业")
        accounting.period_year.setValue(2026)
        accounting.boundary_confirmed.setChecked(True)
        fuel_toggle = accounting._source_toggle_buttons[SOURCE_IDS["CAR-SRC-FUEL-001"]]
        if not accounting._source_is_enabled("CAR-SRC-FUEL-001"):
            fuel_toggle.click()
        fuel = accounting._fuel_rows[0]
        fuel_index = fuel.fuel_type.findText("烟煤", Qt.MatchFlag.MatchContains)
        check(fuel_index >= 0, "F：真实计算fixture可选用目录燃料")
        fuel.fuel_type.setCurrentIndex(fuel_index)
        fuel.path.setCurrentIndex(fuel.path.findData(FuelPath.MASS))
        fuel.activity.setText("10")
        fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("DIRECT"))
        fuel.carbon_direct.setText("0.2")
        fuel.direct_carbon_source.setCurrentIndex(fuel.direct_carbon_source.findData("MEASURED"))
        fuel.source_reference.setText("燃料检测报告-P3-DF")

        electricity_toggle = accounting._source_toggle_buttons[
            SOURCE_IDS["CAR-SRC-PURCHASED-ELECTRICITY-001"]
        ]
        if not accounting._source_is_enabled("CAR-SRC-PURCHASED-ELECTRICITY-001"):
            electricity_toggle.click()
        electricity = accounting._energy_family_rows["electricity"][0]
        electricity.line_id.setText("p3-df-grid-ordinary")
        electricity.amount.setText("20")
        electricity.attribute.setCurrentIndex(electricity.attribute.findData("ORDINARY"))
        settle()

        fixture_input = accounting._input()
        expected = accounting.calculator.calculate(
            fixture_input,
            calculated_at=datetime(2026, 10, 10, tzinfo=timezone.utc),
        )
        check(expected.successful and expected.result is not None, "F：明确fixture由真实Calculator成功计算")
        assert expected.result is not None
        expected_total = expected.result.total_amount
        accounting.calculate_button.click()
        settle()
        saved_records = records.list_all()
        check(len(saved_records) == 1, "F：正式计算新增一条隔离Record")
        record = saved_records[0]
        check(record.calculation_result.total_amount == expected_total, "F：正式结果等于真实Calculator结果")
        check(accounting.result_card.isVisible(), "F：真实计算结果卡片可见")
        display_total = expected_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        check(f"{display_total:.2f}" in accounting.result_total.text(), "F：结果显示真实两位小数")
        check("温室气体排放总量：" in accounting.result_total.text(), "F：结果显示业务化总量")
        check("已完成" in accounting.result_status.text(), "F：结果显示正式完成状态")
        check(record.status.value in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}, "F：Record状态合法")
        check(accounting.view_record_button.isEnabled(), "F：正式Record查看入口可用")
        check(not accounting.result_total.findChildren(QLineEdit), "F：正式结果总量不可编辑")
        scroll_to_result = getattr(accounting, "_scroll_to_widget", None)
        check(callable(scroll_to_result), "F：结果卡定位接口存在")
        assert callable(scroll_to_result)
        scroll_to_result(accounting.result_card)
        settle()
        capture("f-real-result")

        accounting.view_breakdown_button.click()
        settle()
        check(accounting.result_line_details.isVisible(), "F：正式结果可展开分项")
        check("分项结果" in accounting.result_line_details.text(), "F：分项结果业务内容真实显示")
        scroll_to_result(accounting.result_card)
        settle()
        capture("f-real-result-details")

        # Avoid close-confirmation dialogs: this is an isolated offscreen
        # fixture, so hide and defer destruction rather than calling close().
        window.hide()
        window.deleteLater()
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        gc.collect()

    captures = evidence["captures"]
    assert isinstance(captures, list)
    check(len(captures) >= 6, "D/F：至少六组离屏原图已生成")
    manifest = args.output_dir / f"{prefix}.json"
    with manifest.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    checks = evidence["checks"]
    captures = evidence["captures"]
    assert isinstance(checks, list) and isinstance(captures, list)
    print(f"PASS {prefix}: {len(checks)} checks; {len(captures)} offscreen screenshots; native=OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
