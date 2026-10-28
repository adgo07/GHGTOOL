"""Reusable public AppShell for the Windows desktop products."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from PySide6.QtCore import QEvent, QTimer, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from packages.application import CarbonAccountingUseCase, resolve_formal_record_repository
from packages.application.catalog_queries import CatalogQueryService
from packages.core.repositories import RecordRepository
from packages.application.project_workspaces import ProjectWorkspaceService
from packages.application.standard_registry import StandardRuntime

from .design_tokens import (
    BRAND_AREA_HEIGHT,
    COMPACT_HOME_PAGE_SIDE_MARGIN,
    HOME_CANVAS_GRADIENT,
    HOME_CONTENT_MAX_WIDTH,
    HOME_PAGE_SIDE_MARGIN,
    MAIN_CONTENT_MAX_WIDTH,
    NAV_ITEM_HEIGHT,
    NAV_ITEM_RADIUS,
    PAGE_BACKGROUND,
    SIDEBAR_WIDTH,
    responsive_page_margin,
)
from .icons import load_tinted_icon
from .branding import BrandLogo
from .pages import create_page
from .export_location import ExportLocationService
from .routing import PageRouter
from .view_models import AppRoute, ShellViewModel


PageFactory = Callable[
    [AppRoute, ShellViewModel, Callable[[AppRoute], None], QWidget | None],
    QWidget,
]


_SIDEBAR_BACKGROUND = (
    "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
    "stop:0 #E6F2FC, stop:0.48 #EDF6FD, stop:1 #E6F2FB)"
)
_SIDEBAR_MUTED_TEXT = "#516F86"
_SIDEBAR_ACTIVE = "#116FAE"
_SIDEBAR_ACTIVE_BACKGROUND = "#D6EBF9"


class ContentHost(QWidget):
    """Paint the canvas on a sibling of the pages, without repolishing editors."""

    def __init__(self) -> None:
        super().__init__()
        self.background_layer = QWidget(self)
        self.background_layer.setObjectName("scrollCanvas")
        self.background_layer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.background_layer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.background_layer.lower()

    def set_background(self, background: str) -> None:
        style = f"QWidget#scrollCanvas {{ background: {background}; }}"
        if self.background_layer.styleSheet() != style:
            self.background_layer.setStyleSheet(style)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self.background_layer.setGeometry(self.rect())
        self.background_layer.lower()


class ContentScrollArea(QScrollArea):
    """Scroll area that keeps the main content vertically scrollable only."""

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        central = self.window().centralWidget()
        if isinstance(central, AppShell):
            central.update_content_geometry()


class CurrentPageStack(QStackedWidget):
    """A page stack whose size hint follows the page currently being shown."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.currentChanged.connect(lambda _index: self.updateGeometry())

    def sizeHint(self) -> QSize:  # type: ignore[override]
        current = self.currentWidget()
        if current is None:
            return super().sizeHint()
        hint = current.sizeHint()
        minimum = current.minimumSizeHint()
        return QSize(max(hint.width(), minimum.width()), max(hint.height(), minimum.height()))

    def minimumSizeHint(self) -> QSize:  # type: ignore[override]
        current = self.currentWidget()
        if current is None:
            return super().minimumSizeHint()
        return current.minimumSizeHint()

    def event(self, event: QEvent) -> bool:  # type: ignore[override]
        handled = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest:
            central_widget = getattr(self.window(), "centralWidget", None)
            shell = central_widget() if callable(central_widget) else None
            if isinstance(shell, AppShell):
                shell.update_content_geometry()
        return handled


class _PageAccess(Mapping):
    """Compatibility mapping; reading a route explicitly creates its page."""
    def __init__(self, shell):
        self.shell = shell

    def __getitem__(self, route):
        if route not in tuple(self):
            raise KeyError(route)
        return self.shell._ensure_page(route)

    def __iter__(self):
        return (item.route for item in self.shell.view_model.navigation)

    def __len__(self):
        return len(self.shell.view_model.navigation)


class AppShell(QWidget):
    """Route-driven shell with a sidebar on business pages only."""

    def __init__(
        self,
        view_model: ShellViewModel,
        logo_path: Path,
        icon_directory: Path,
        page_factory: PageFactory | None = None,
        parent: QWidget | None = None,
        catalog_service: CatalogQueryService | None = None,
        record_repository: RecordRepository | None = None,
        project_service: ProjectWorkspaceService | None = None,
        calculation_use_case: CarbonAccountingUseCase | None = None,
        standard_runtime=None,
        export_location_service: ExportLocationService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("appShell")
        self.view_model = view_model
        self._logo_path = logo_path
        self._icon_directory = icon_directory
        self.catalog_service = catalog_service or CatalogQueryService.empty()
        self.record_repository = resolve_formal_record_repository(calculation_use_case, record_repository)
        self.project_service = project_service
        self._injected_calculation_use_case = calculation_use_case
        self.standard_runtime = standard_runtime or StandardRuntime(self.catalog_service, self.record_repository, calculation_use_case)
        self.export_location_service = export_location_service
        self.selected_standard_id: str | None = None
        self._custom_page_factory = page_factory
        self._page_factory = page_factory or create_page
        self._navigation_buttons: dict[AppRoute, QPushButton] = {}
        self._icon_names: dict[AppRoute, str] = {}
        self._navigation_icon_cache: dict[tuple[AppRoute, bool], QIcon] = {}
        self._scroll_positions: dict[AppRoute, int] = {}
        self._visible_route: AppRoute | None = None
        self._settings_from_home = False
        self._pages: dict[AppRoute, QWidget] = {}
        self._standard_pages: dict[tuple[AppRoute, str], QWidget] = {}
        self._content_geometry_refresh_pending = False
        self._pending_route_scroll_restore = False
        self.router = PageRouter((item.route for item in view_model.navigation), self)
        self.router.route_changed.connect(self._show_route)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self._sidebar = self._build_sidebar()
        root_layout.addWidget(self._sidebar)
        root_layout.addWidget(self._build_main_content(), 1)

        if self._custom_page_factory is not None:
            for item in view_model.navigation:
                self._ensure_page(item.route)

        self.router.navigate(AppRoute.HOME)
        QTimer.singleShot(0, self, self.update_content_geometry)

    def _ensure_page(self, route: AppRoute) -> QWidget:
        standard_id = None
        if self._custom_page_factory is None and route in (AppRoute.NEW_ACCOUNTING, AppRoute.EXCEL_IMPORT):
            standard_id = self.selected_standard_id or self.standard_runtime.registry.default_standard_id
            self.standard_runtime.registry.require(standard_id)
            cached = self._standard_pages.get((route, standard_id))
            if cached is not None:
                self._pages[route] = cached
                return cached
        elif route in self._pages:
            return self._pages[route]
        if self._custom_page_factory is None:
            page = create_page(
                route,
                self.view_model,
                self.navigate,
                self.page_stack if route is AppRoute.NEW_ACCOUNTING else self,
                catalog_service=self.catalog_service,
                record_repository=self.record_repository,
                project_service=self.project_service,
                calculation_use_case=self._injected_calculation_use_case,
                logo_path=self._logo_path,
                icon_directory=self._icon_directory,
                standard_runtime=self.standard_runtime,
                standard_id=self.selected_standard_id,
            )
        else:
            page = self._page_factory(route, self.view_model, self.navigate, self)
        self._pages[route] = page
        if standard_id is not None:
            self._standard_pages[(route, standard_id)] = page
        self.page_stack.addWidget(page)
        accounting_requested = getattr(page, "accounting_requested", None)
        if accounting_requested is not None:
            accounting_requested.connect(self._request_standard_accounting)
        record_created = getattr(page, "record_created", None)
        if record_created is not None:
            record_created.connect(self._refresh_record_views)
        record_requested = getattr(page, "record_requested", None)
        if record_requested is not None:
            record_requested.connect(self._request_record_view)
        project_requested = getattr(page, "project_requested", None)
        if project_requested is not None:
            project_requested.connect(self._request_home_project)
        project_manager_requested = getattr(page, "project_manager_requested", None)
        if project_manager_requested is not None:
            project_manager_requested.connect(self._request_home_project_manager)
        canonical_project_requested = getattr(page, "canonical_project_requested", None)
        if canonical_project_requested is not None:
            canonical_project_requested.connect(self._request_canonical_project)
        return page

    @property
    def navigation_buttons(self) -> dict[AppRoute, QPushButton]:
        return dict(self._navigation_buttons)

    @property
    def pages(self) -> Mapping[AppRoute, QWidget]:
        return _PageAccess(self)

    @property
    def calculation_use_case(self):
        """Compatibility access explicitly requests the selected formal service."""
        standard_id = self.selected_standard_id or self.standard_runtime.registry.default_standard_id
        return self.standard_runtime.services(standard_id)[1]

    @property
    def current_route(self) -> AppRoute | None:
        return self.router.current_route

    def confirm_discard_if_needed(self) -> bool:
        """Compatibility hook; in-memory input remains while the application runs."""

        return True

    def confirm_before_close(self) -> bool:
        """Offer explicit save, discard or cancel for unsaved project changes."""

        pages = {page for (route, _standard), page in self._standard_pages.items() if route is AppRoute.NEW_ACCOUNTING}
        for page in pages:
            prompt = getattr(page, "confirm_project_close", None)
            if callable(prompt) and not prompt():
                return False
        return True

    def navigate(self, route: AppRoute) -> None:
        """Switch pages without discarding the active new-accounting input."""

        self.router.navigate(route)

    def _refresh_record_views(self, _record_id: str | None = None) -> None:
        for page in set((*self._pages.values(), *self._standard_pages.values())):
            invalidate = getattr(page, "invalidate_record_views", None)
            if callable(invalidate):
                invalidate(projects=True)
        current = self._pages.get(self.router.current_route)
        refresh = getattr(current, "refresh_if_dirty", None)
        if callable(refresh):
            refresh()

    def _invalidate_project_views(self) -> None:
        for page in set((*self._pages.values(), *self._standard_pages.values())):
            invalidate_projects = getattr(page, "invalidate_project_data", None)
            if callable(invalidate_projects):
                invalidate_projects()
            invalidate_associations = getattr(page, "invalidate_project_associations", None)
            if callable(invalidate_associations):
                invalidate_associations()

    def _request_record_view(self, record_id: str) -> None:
        page = self._ensure_page(AppRoute.RECORDS)
        open_record = getattr(page, "open_record", None)
        if callable(open_record):
            open_record(record_id)
        self.navigate(AppRoute.RECORDS)

    def _request_canonical_project(self, project_id: str) -> None:
        self.navigate(AppRoute.EXCEL_IMPORT)
        page = self._pages.get(AppRoute.EXCEL_IMPORT)
        open_project = getattr(page, "open_project", None)
        if callable(open_project):
            open_project(project_id)

    def _request_home_project(self, project_id: str) -> None:
        page = self._ensure_page(AppRoute.NEW_ACCOUNTING)
        open_project = getattr(page, "open_project_from_home", None)
        if not project_id or not callable(open_project):
            return
        self.navigate(AppRoute.NEW_ACCOUNTING)
        open_project(project_id)

    def _request_home_project_manager(self) -> None:
        page = self._ensure_page(AppRoute.NEW_ACCOUNTING)
        show_manager = getattr(page, "show_project_manager", None)
        if not callable(show_manager):
            return
        self.navigate(AppRoute.NEW_ACCOUNTING)
        show_manager()

        card = getattr(page, "project_unit_card", None)
        if card is not None:
            QTimer.singleShot(
                0,
                self,
                lambda: self.main_scroll_area.ensureWidgetVisible(card, 0, 18),
            )

    def _request_standard_accounting(self, standard_id: str) -> None:
        """Route only the implemented industry standard to its dedicated page."""

        if not self.standard_runtime.registry.supports(standard_id):
            return
        self.selected_standard_id = standard_id
        self.navigate(AppRoute.NEW_ACCOUNTING)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(
            f"""
            QFrame#sidebar {{ background: {_SIDEBAR_BACKGROUND}; }}
            QWidget#brandArea, QLabel#brandLogo, QLabel#sidebarProductName {{ background: transparent; }}
            QLabel#sidebarProductName {{ color: #537891; font-size: 11px; font-weight: 650; }}
            QPushButton#navButton {{
                background: transparent; min-height:44px; max-height:44px; border:1px solid transparent; border-radius: {NAV_ITEM_RADIUS}px;
                color: {_SIDEBAR_MUTED_TEXT}; font-size: 13px; font-weight: 600;
                padding: 0 13px; text-align: left;
            }}
            QPushButton#navButton:hover {{ background: rgba(255, 255, 255, 0.78); color: #0F6DA7; }}
            QPushButton#navButton:checked {{
                background: {_SIDEBAR_ACTIVE_BACKGROUND}; border-left: 3px solid #298CCB;
                color: {_SIDEBAR_ACTIVE}; font-weight: 700; padding-left: 10px;
            }}
            QPushButton#navButton:focus {{ border: 1px solid {_SIDEBAR_ACTIVE}; }}
            QPushButton#navButton[reserved="true"] {{ color: #98A2B3; }}
            QPushButton#navButton[reserved="true"]:hover {{ background: rgba(255, 255, 255, 0.45); color: #91A3B2; }}
            """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 24, 0, 18)
        sidebar_layout.setSpacing(0)

        brand_area = QWidget(sidebar)
        brand_area.setObjectName("brandArea")
        brand_area.setFixedHeight(BRAND_AREA_HEIGHT)
        brand_layout = QVBoxLayout(brand_area)
        brand_layout.setContentsMargins(7, 10, 7, 19)
        brand_layout.setSpacing(6)

        logo_label = BrandLogo(self._logo_path, brand_area)
        logo_label.setObjectName("brandLogo")
        brand_layout.addWidget(logo_label)

        product_label = QLabel(self.view_model.product_name, brand_area)
        product_label.setObjectName("sidebarProductName")
        product_label.setWordWrap(True)
        brand_layout.addWidget(product_label)
        sidebar_layout.addWidget(brand_area)

        navigation = QWidget(sidebar)
        navigation.setObjectName("navigationArea")
        navigation_layout = QVBoxLayout(navigation)
        navigation_layout.setContentsMargins(12, 0, 12, 0)
        navigation_layout.setSpacing(4)
        for item in self.view_model.navigation:
            button = QPushButton(item.label, navigation)
            button.setObjectName("navButton")
            button.setProperty("route", item.route.value)
            button.setProperty("reserved", item.reserved)
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setFixedHeight(NAV_ITEM_HEIGHT)
            self._icon_names[item.route] = item.icon_name
            muted_icon = load_tinted_icon(
                self._icon_directory / f"{item.icon_name}.svg",
                _SIDEBAR_MUTED_TEXT,
            )
            self._navigation_icon_cache[(item.route, False)] = muted_icon
            button.setIcon(muted_icon)
            button.setIconSize(QSize(18, 18))
            button.setCursor(
                Qt.CursorShape.ArrowCursor
                if item.reserved
                else Qt.CursorShape.PointingHandCursor
            )
            if item.reserved:
                button.setEnabled(False)
                button.setToolTip("当前暂未开放")
            button.clicked.connect(lambda _checked=False, route=item.route: self._navigation_clicked(route))
            navigation_layout.addWidget(button)
            self._navigation_buttons[item.route] = button
        sidebar_layout.addWidget(navigation)
        sidebar_layout.addStretch(1)

        settings_row = QWidget(sidebar)
        settings_layout = QVBoxLayout(settings_row)
        settings_row.setStyleSheet("QWidget { border-top: 1px solid #D4E5F1; }")
        settings_layout.setContentsMargins(12, 12, 12, 0)
        settings_layout.setSpacing(0)
        settings_button = self._navigation_buttons[AppRoute.SETTINGS]
        navigation_layout.removeWidget(settings_button)
        settings_button.setParent(settings_row)
        settings_layout.addWidget(settings_button)
        sidebar_layout.addWidget(settings_row)
        return sidebar

    def _build_main_content(self) -> QFrame:
        main_content = QFrame(self)
        main_content.setObjectName("mainContent")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.main_scroll_area = ContentScrollArea(main_content)
        self.main_scroll_area.setObjectName("mainScrollArea")
        self.main_scroll_area.setWidgetResizable(True)
        self.main_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.main_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_host = ContentHost()
        scroll_host.setObjectName("scrollHost")
        self.scroll_host = scroll_host
        scroll_layout = QVBoxLayout(scroll_host)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        self.page_stack = CurrentPageStack(scroll_host)
        self.page_stack.setObjectName("pageStack")
        self.page_stack.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred,
        )
        scroll_layout.addWidget(
            self.page_stack,
            0,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        scroll_layout.addStretch(1)
        self.main_scroll_area.setWidget(scroll_host)
        main_layout.addWidget(self.main_scroll_area)
        return main_content

    def _navigation_clicked(self, route: AppRoute) -> None:
        self.navigate(route)
        button = self._navigation_buttons.get(route)
        if button is not None and self.router.current_route is route:
            button.setChecked(True)

    def _navigation_icon(self, route: AppRoute, active: bool) -> QIcon:
        key = (route, active)
        icon = self._navigation_icon_cache.get(key)
        if icon is None:
            color = _SIDEBAR_ACTIVE if active else _SIDEBAR_MUTED_TEXT
            icon = load_tinted_icon(
                self._icon_directory / f"{self._icon_names[route]}.svg",
                color,
            )
            self._navigation_icon_cache[key] = icon
        return icon

    def _show_route(self, route: AppRoute) -> None:
        previous_route = self._visible_route
        if previous_route is not None and previous_route is not route:
            self._scroll_positions[previous_route] = self.main_scroll_area.verticalScrollBar().value()
            if previous_route in (AppRoute.NEW_ACCOUNTING, AppRoute.EXCEL_IMPORT):
                self._invalidate_project_views()
        page = self._ensure_page(route)
        background = HOME_CANVAS_GRADIENT if route is AppRoute.HOME else PAGE_BACKGROUND
        self.scroll_host.set_background(background)
        if route is AppRoute.SETTINGS and previous_route is not AppRoute.SETTINGS:
            self._settings_from_home = previous_route is AppRoute.HOME
        self._sidebar.setVisible(route is not AppRoute.HOME and not (
            route is AppRoute.SETTINGS and self._settings_from_home))
        if route is AppRoute.SETTINGS:
            back = getattr(page, "home_back_button", None)
            if back is not None:
                back.setVisible(self._settings_from_home)
        self.page_stack.setCurrentWidget(page)
        self._visible_route = route
        for item_route, button in self._navigation_buttons.items():
            is_active = item_route is route
            button.setChecked(is_active)
            button.setIcon(self._navigation_icon(item_route, is_active))
        refresh = getattr(page, "refresh_if_dirty", None)
        if callable(refresh):
            refresh()
        self._pending_route_scroll_restore = True
        self.update_content_geometry()
        self._restore_content_scroll_position(route)

    def _restore_content_scroll_position(self, route: AppRoute | None = None) -> None:
        if not hasattr(self, "main_scroll_area"):
            return
        active_route = route or self._visible_route
        if active_route is None:
            return
        scrollbar = self.main_scroll_area.verticalScrollBar()
        target = self._scroll_positions.get(active_route, scrollbar.minimum())
        scrollbar.setValue(max(scrollbar.minimum(), min(target, scrollbar.maximum())))

    def _reset_content_scroll_position(self) -> None:
        self._restore_content_scroll_position()

    def update_content_geometry(self) -> None:
        if not hasattr(self, "page_stack"):
            return
        self._apply_content_geometry()
        if self._content_geometry_refresh_pending:
            return
        self._content_geometry_refresh_pending = True
        QTimer.singleShot(0, self, self._settle_content_geometry)

    def _settle_content_geometry(self) -> None:
        """Coalesce layout settling and restore the active route's scroll position."""

        self._content_geometry_refresh_pending = False
        self._apply_content_geometry()
        if self._pending_route_scroll_restore:
            self._pending_route_scroll_restore = False
            self._restore_content_scroll_position()

    def _apply_content_geometry(self) -> None:
        if not hasattr(self, "page_stack"):
            return
        available_width = max(0, self.main_scroll_area.viewport().width())
        current_route = self.router.current_route
        content_max_width = (
            HOME_CONTENT_MAX_WIDTH
            if current_route is AppRoute.HOME
            else MAIN_CONTENT_MAX_WIDTH + 2 * responsive_page_margin(available_width)
        )
        content_width = min(content_max_width, available_width)
        self.page_stack.setFixedWidth(content_width)
        route = self.router.current_route
        page = self.page_stack.currentWidget()
        setter = getattr(page, "set_page_margin", None)
        if setter is not None:
            if route is AppRoute.HOME:
                margin = (
                    COMPACT_HOME_PAGE_SIDE_MARGIN
                    if self.width() <= 1240
                    else HOME_PAGE_SIDE_MARGIN
                )
            else:
                margin = responsive_page_margin(available_width)
            setter(margin)
        available_height = max(0, self.main_scroll_area.viewport().height())
        self.page_stack.setMinimumHeight(available_height)
        self.page_stack.adjustSize()
        content_height = max(available_height, self.page_stack.sizeHint().height())
        self.scroll_host.setFixedHeight(content_height)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self.update_content_geometry()
