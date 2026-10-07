"""G04 public desktop shell for the carbon-accounting application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from packages.application import (
    CarbonAccountingUseCase,
    resolve_formal_record_repository,
    CatalogQueryService,
    ProjectWorkspaceService,
)
from packages.persistence.catalog_queries_factory import create_catalog_query_service
from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.core.repositories import RecordRepository
from packages.persistence import (
    MigrationError,
    ProjectWorkspaceRepositoryError,
    RecordRepositoryError,
    SQLiteProjectWorkspaceRepository,
    SQLiteRecordRepository,
)
from packages.standards.carbon_material import (
    STANDARD_ID,
    STANDARD_VERSION,
    CarbonMaterialCalculator,
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
    calculation_use_case: CarbonAccountingUseCase | None = None,
) -> QMainWindow:
    """Create the desktop shell and compose its formal calculation workflow."""

    app_config = config or AppConfig()
    catalog = catalog_service or create_catalog_query_service(
        app_config.resolved_catalog_database()
    )
    records = resolve_formal_record_repository(calculation_use_case, record_repository)
    if records is None:
        records = SQLiteRecordRepository(
            app_config.resolved_records_database(),
            app_version=app_config.app_version,
        )

    formal_use_case = calculation_use_case
    if formal_use_case is None and callable(getattr(records, "create_with_details", None)):
        calculator = CarbonMaterialCalculator(
            parameter_resolver=create_g06_parameter_resolver(catalog.repository),
            standard_version=catalog.standard_version(STANDARD_ID) or STANDARD_VERSION,
            standard_implementation_date=catalog.standard_implementation_date(STANDARD_ID),
            reference_data_identity_provider=catalog.reference_data_identity,
        )
        formal_use_case = CarbonAccountingUseCase(calculator, records)

    window = CarbonAccountingMainWindow()
    window.setObjectName("mainWindow")
    window.setWindowTitle(app_config.app_name)
    window.setMinimumSize(1180, 720)
    window.resize(1280, 800)
    window.setStyleSheet(application_stylesheet())
    window.setFont(QFont("Microsoft YaHei UI", 10))
    window.setCentralWidget(create_shell(
        app_config,
        catalog_service=catalog,
        record_repository=records,
        project_service=project_service,
        calculation_use_case=formal_use_case,
    ))
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""

    qt_args = list(argv) if argv is not None else sys.argv
    application = QApplication(qt_args)
    config = AppConfig()
    logger = configure_logging(config.resolved_log_directory(), config.app_version)
    try:
        record_repository = SQLiteRecordRepository(
            config.resolved_records_database(),
            app_version=config.app_version,
        )
    except (MigrationError, OSError, RecordRepositoryError) as exc:
        logger.event(
            "records_database_initialization_failed",
            component="record_store",
            outcome="failed",
            error_type="migration_error" if isinstance(exc, MigrationError) else "filesystem_error",
        )
        QMessageBox.critical(
            None,
            "核算记录数据无法打开",
            "核算记录数据库无法创建或安全迁移。请检查记录数据文件后重试。\n\n"
            f"详细信息：{exc}",
        )
        logger.close()
        return 1
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
    window = create_main_window(
        config,
        record_repository=record_repository,
        project_service=project_service,
    )
    window.show()
    logger.event("application_started", component="desktop_app", outcome="started")
    exit_code = application.exec()
    logger.event("application_exited", component="desktop_app", outcome="normal")
    logger.close()
    return exit_code
