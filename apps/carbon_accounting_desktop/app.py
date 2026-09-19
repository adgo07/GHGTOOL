"""G04 public desktop shell for the carbon-accounting application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import QApplication, QMainWindow

from packages.application import CatalogQueryService
from packages.core.repositories import RecordRepository

from .config import AppConfig
from .logging_config import configure_logging
from .product import create_shell
from packages.ui.design_tokens import application_stylesheet


class CarbonAccountingMainWindow(QMainWindow):
    """Main window that enforces the G07 uncomputed-input close gate."""

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        central = self.centralWidget()
        confirm = getattr(central, "confirm_discard_if_needed", None)
        if callable(confirm) and not confirm():
            event.ignore()
            return
        event.accept()


def create_main_window(
    config: AppConfig | None = None,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
) -> QMainWindow:
    """Create the public G04 shell; business algorithms remain outside the UI."""

    app_config = config or AppConfig()
    window = CarbonAccountingMainWindow()
    window.setObjectName("mainWindow")
    window.setWindowTitle(app_config.app_name)
    window.setMinimumSize(1180, 720)
    window.resize(1280, 800)
    window.setStyleSheet(application_stylesheet())
    window.setFont(QFont("Microsoft YaHei UI", 10))
    window.setCentralWidget(create_shell(app_config, catalog_service=catalog_service, record_repository=record_repository))
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""

    qt_args = list(argv) if argv is not None else sys.argv
    application = QApplication(qt_args)
    config = AppConfig()
    logger = configure_logging(config.resolved_log_directory(), config.app_version)
    window = create_main_window(config)
    window.show()
    logger.event("application_started", component="desktop_app", outcome="started")
    exit_code = application.exec()
    logger.event("application_exited", component="desktop_app", outcome="normal")
    logger.close()
    return exit_code
