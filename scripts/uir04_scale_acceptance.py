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
    parser.add_argument("--scale", choices=("1.25", "1.5"), required=True)
    args = parser.parse_args()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "0")
    os.environ["QT_SCALE_FACTOR"] = args.scale

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QFrame

    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import CatalogQueryService
    from packages.persistence import SQLiteCatalogRepository, build_catalog_database
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.standards.carbon_material import InMemoryRecordRepository
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
        window.close()
        window.deleteLater()
        application.processEvents()
        if failures:
            print(f"scale={args.scale} FAIL: " + "; ".join(failures))
            return 1
    print(f"scale={args.scale} PASS: 1366x768 controls visible without horizontal scrolling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
