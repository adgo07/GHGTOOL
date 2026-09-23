"""G04 public desktop shell for the carbon-accounting application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from packages.application import CatalogQueryService, ProjectWorkspaceService
from packages.core.repositories import RecordRepository
from packages.persistence import (
    MigrationError,
    ProjectWorkspaceRepositoryError,
    SQLiteProjectWorkspaceRepository,
)

from .config import AppConfig
from .logging_config import configure_logging
from .product import create_shell
from packages.ui.design_tokens import application_stylesheet


class CarbonAccountingMainWindow(QMainWindow):
    """Main window that asks how to handle unsaved project state before closing."""

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        shell = self.centralWidget()
        confirm = getattr(shell, "confirm_before_close", None)
        if callable(confirm) and not confirm():
            event.ignore()
            return
        event.accept()


def create_main_window(
    config: AppConfig | None = None,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
    project_service: ProjectWorkspaceService | None = None,
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
    window.setCentralWidget(create_shell(
        app_config,
        catalog_service=catalog_service,
        record_repository=record_repository,
        project_service=project_service,
    ))
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""

    qt_args = list(argv) if argv is not None else sys.argv
    application = QApplication(qt_args)
    config = AppConfig()
    logger = configure_logging(config.resolved_log_directory(), config.app_version)
    try:
        project_service = ProjectWorkspaceService(
            SQLiteProjectWorkspaceRepository(
                config.resolved_projects_database(),
                app_version=config.app_version,
            )
        )
    except (MigrationError, OSError, ProjectWorkspaceRepositoryError) as exc:
        logger.event(
            "projects_database_initialization_failed",
            component="project_store",
            outcome="failed",
            error_type="migration_error" if isinstance(exc, MigrationError) else "filesystem_error",
        )
        QMessageBox.critical(
            None,
            "核算项目数据无法打开",
            "项目数据文件无法创建或安全迁移。核算记录数据库未被修改。\n\n"
            f"详细信息：{exc}",
        )
        logger.close()
        return 1
    window = create_main_window(config, project_service=project_service)
    window.show()
    logger.event("application_started", component="desktop_app", outcome="started")
    exit_code = application.exec()
    logger.event("application_exited", component="desktop_app", outcome="normal")
    logger.close()
    return exit_code
