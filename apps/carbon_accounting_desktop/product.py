"""Carbon-accounting product configuration for the shared G04 shell."""

from __future__ import annotations

from packages.application import CatalogQueryService, ProjectWorkspaceService, create_catalog_query_service
from packages.core.repositories import RecordRepository
from packages.persistence import SQLiteProjectWorkspaceRepository, SQLiteRecordRepository

from .config import AppConfig
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute, NavigationItemViewModel, ShellViewModel


def carbon_accounting_view_model() -> ShellViewModel:
    """Return the stable shell model; catalog data is queried separately."""

    return ShellViewModel(
        product_name="温室气体排放核算",
        home_title="温室气体排放核算",
        home_description="基于 GB/T 32151 系列标准开展企业温室气体排放核算",
        navigation=(
            NavigationItemViewModel(AppRoute.HOME, "首页", "home"),
            NavigationItemViewModel(AppRoute.STANDARDS, "标准库", "standards"),
            NavigationItemViewModel(AppRoute.NEW_ACCOUNTING, "新建核算", "new"),
            NavigationItemViewModel(
                AppRoute.EXCEL_IMPORT,
                "Excel 导入（暂未开放）",
                "excel",
                reserved=True,
            ),
            NavigationItemViewModel(AppRoute.RECORDS, "核算记录", "records"),
            NavigationItemViewModel(AppRoute.FACTORS, "参数与因子库", "factors"),
            NavigationItemViewModel(AppRoute.SETTINGS, "设置", "settings"),
        ),
    )


def create_shell(
    config: AppConfig,
    catalog_service: CatalogQueryService | None = None,
    record_repository: RecordRepository | None = None,
    project_service: ProjectWorkspaceService | None = None,
) -> AppShell:
    """Build the product shell while keeping database access in the application edge."""

    if record_repository is None:
        record_repository = SQLiteRecordRepository(
            config.resolved_records_database(),
            app_version=config.app_version,
        )

    return AppShell(
        carbon_accounting_view_model(),
        logo_path=config.logo_path(),
        icon_directory=config.icons_directory(),
        catalog_service=catalog_service or create_catalog_query_service(
            config.resolved_catalog_database()
        ),
        record_repository=record_repository,
        project_service=project_service,
    )
