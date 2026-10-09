"""Carbon-accounting product configuration for the shared G04 shell."""

from __future__ import annotations

from packages.application import (
    CarbonAccountingUseCase,
    resolve_formal_record_repository,
    CatalogQueryService,
    ProjectWorkspaceService,
)
from packages.persistence.catalog_queries_factory import create_catalog_query_service
from packages.core.repositories import RecordRepository

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
                "表格导入",
                "excel",
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
    calculation_use_case: CarbonAccountingUseCase | None = None,
) -> AppShell:
    """Build the product shell from services composed by the desktop entry point."""

    record_repository = resolve_formal_record_repository(calculation_use_case, record_repository)

    return AppShell(
        carbon_accounting_view_model(),
        logo_path=config.logo_path(),
        icon_directory=config.icons_directory(),
        catalog_service=catalog_service or create_catalog_query_service(
            config.resolved_catalog_database()
        ),
        record_repository=record_repository,
        project_service=project_service,
        calculation_use_case=calculation_use_case,
    )
