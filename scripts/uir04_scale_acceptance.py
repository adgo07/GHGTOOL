"""Probe the UIR04 page at common Windows display scale factors."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UIR04 scaled Qt layout probe")
    parser.add_argument("--scale", choices=("1.0", "1.25", "1.5"), required=True)
    args = parser.parse_args()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "0")
    os.environ["QT_SCALE_FACTOR"] = args.scale

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QFrame

    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import CatalogQueryService
    from packages.persistence import (
        InMemoryRecordRepository,
        SQLiteCatalogRepository,
        build_catalog_database,
    )
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.ui.view_models import AppRoute

    application = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="uir04-scale-") as directory:
        catalog_path = build_catalog_database(
            DEFAULT_SOURCE_PATH,
            Path(directory) / "catalog.sqlite",
            app_version="1.1.0",
        )
        service = CatalogQueryService(
            SQLiteCatalogRepository(catalog_path),
            as_of=date(2026, 9, 12),
        )
        window = create_main_window(
            AppConfig(catalog_database=catalog_path),
            catalog_service=service,
            record_repository=InMemoryRecordRepository(),
        )
        window.resize(1366, 768)
        window.show()
        application.processEvents()
        shell = window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        application.processEvents()
        page = shell.pages[AppRoute.NEW_ACCOUNTING]
        viewport = shell.main_scroll_area.viewport()
        status_bar = page.findChild(QFrame, "calculationStatusBar")
        failures: list[str] = []
        if shell.main_scroll_area.horizontalScrollBarPolicy() is not Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            failures.append("horizontal scrollbar policy is not AlwaysOff")
        if shell.main_scroll_area.horizontalScrollBar().isVisible():
            failures.append("horizontal scrollbar is visible")
        if page.width() > viewport.width():
            failures.append(f"page width {page.width()} exceeds viewport {viewport.width()}")
        if not page.calculate_button.isVisible():
            failures.append("calculate button is not visible")
        if status_bar is None or not status_bar.isVisible():
            failures.append("compact calculation status bar is not visible")

        source_groups = (
            "fuel",
            "calcination",
            "baking",
            "graphitization",
            "fume",
            "fgd",
            "electricity",
            "heat",
        )
        for group_id in source_groups:
            page._source_toggle_buttons[group_id].click()

        for _ in range(4):
            page._add_fuel_row()
            page._add_process_row("calcination")
            page._add_process_row("baking")
            page._add_process_row("graphitization")
            page._add_process_row("fume")
            page._add_process_row("fgd")
        for kind in ("purchased_electricity", "exported_electricity", "purchased_heat", "exported_heat"):
            for _ in range(2):
                page._add_unified_energy_row(kind=kind)
        for _ in range(4):
            page._add_fgd_component(page._process_rows["fgd"][0])
        application.processEvents()

        def check_vertical_rows(name, host, rows) -> None:
            parent = host
            while parent is not None:
                if parent.layout() is not None:
                    parent.layout().activate()
                parent.updateGeometry()
                parent = parent.parentWidget()
            shell.update_content_geometry()
            application.processEvents()
            rects = [row.geometry() for row in rows]
            if len(rows) != 5:
                failures.append(f"{name}: expected five rows, found {len(rows)}")
            for index, rect in enumerate(rects):
                if rect.width() < 120 or rect.height() < 22:
                    failures.append(f"{name}[{index}]: cramped geometry {rect.width()}x{rect.height()}, host={host.geometry().width()}x{host.geometry().height()}")
                if rect.left() < 0 or rect.right() > host.width():
                    failures.append(f"{name}[{index}]: row width {rect.left()}..{rect.right()} exceeds host width {host.width()}")
                if index and rects[index - 1].bottom() >= rect.top():
                    failures.append(f"{name}: rows {index} and {index + 1} overlap")

        check_vertical_rows("fuel", page.fuel_rows_host, list(page._fuel_rows))
        for family in ("electricity", "heat"):
            host = page._unified_energy_rows_layouts[family].parentWidget()
            check_vertical_rows(f"{family} energy families", host, list(page._energy_family_rows[family]))
        for prefix, rows in page._process_rows.items():
            host = page._process_rows_layout[prefix].parentWidget()
            check_vertical_rows(prefix, host, [row["widget"] for row in rows])
        fgd_unit = page._process_rows["fgd"][0]
        component_rows = [item["_widget"] for item in fgd_unit["components"]]
        check_vertical_rows("FGD components", fgd_unit["component_host"], component_rows)

        page._fuel_rows[-1].remove_button.click()
        for family in ("electricity", "heat"):
            page._remove_unified_energy_row(page._energy_family_rows[family][-1])
        last_process = page._process_rows["calcination"][-1]
        page._remove_process_row("calcination", str(last_process["instance_id"]))
        last_component_id = str(fgd_unit["components"][-1]["component_id"])
        page._remove_fgd_component(fgd_unit, last_component_id)
        application.processEvents()
        for name, count in (
            ("fuel", len(page._fuel_rows)),
            ("electricity family", len(page._energy_family_rows["electricity"])),
            ("heat family", len(page._energy_family_rows["heat"])),
            ("calcination", len(page._process_rows["calcination"])),
            ("FGD components", len(fgd_unit["components"])),
        ):
            if count != 4:
                failures.append(f"{name}: deleting a row did not restore the four-row layout")
        window.close()
        window.deleteLater()
        application.processEvents()
        if failures:
            print(f"scale={args.scale} FAIL: " + "; ".join(failures))
            return 1
    print(f"scale={args.scale} PASS: 1366x768 controls and dynamic rows fit without overlap or horizontal scrolling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
