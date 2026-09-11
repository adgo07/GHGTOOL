"""Platform-neutral view models used by the desktop presentation layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppRoute(str, Enum):
    """The seven public G03 routes in their frozen navigation order."""

    HOME = "home"
    STANDARDS = "standards"
    NEW_ACCOUNTING = "new_accounting"
    EXCEL_IMPORT = "excel_import"
    RECORDS = "records"
    FACTORS = "factors"
    SETTINGS = "settings"


@dataclass(frozen=True, slots=True)
class NavigationItemViewModel:
    route: AppRoute
    label: str
    icon_name: str
    reserved: bool = False


@dataclass(frozen=True, slots=True)
class RecentRecordViewModel:
    company_name: str
    period: str
    standard: str
    emissions: str
    status: str


@dataclass(frozen=True, slots=True)
class RecentStandardViewModel:
    standard_id: str
    title: str


@dataclass(frozen=True, slots=True)
class ShellViewModel:
    product_name: str
    home_title: str
    home_description: str
    navigation: tuple[NavigationItemViewModel, ...]
    recent_records: tuple[RecentRecordViewModel, ...] = ()
    recent_standards: tuple[RecentStandardViewModel, ...] = ()
    status_summary: str = "暂无核算记录 · 暂无企业 · 暂无待处理事项"
    primary_action_label: str = "＋ 新建核算"
    standards_action_label: str = "查看标准库"
    excel_action_label: str = "Excel 导入（暂未开放）"

    def __post_init__(self) -> None:
        routes = tuple(item.route for item in self.navigation)
        if routes != tuple(AppRoute):
            raise ValueError("navigation must contain the seven G03 routes in order")
