"""Reusable public AppShell for the Windows desktop products."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QTimer, QSize, Qt
from PySide6.QtGui import QPixmap
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

from .design_tokens import (
    BRAND_AREA_HEIGHT,
    COMPACT_PAGE_MARGIN,
    MAIN_CONTENT_MAX_WIDTH,
    NAV_ITEM_HEIGHT,
    SIDEBAR_WIDTH,
    SIDEBAR_ICON_ACTIVE,
    SIDEBAR_ICON_INACTIVE,
    WIDE_PAGE_MARGIN,
)
from .icons import load_tinted_icon
from .pages import create_page
from .routing import PageRouter
from .view_models import AppRoute, ShellViewModel


PageFactory = Callable[
    [AppRoute, ShellViewModel, Callable[[AppRoute], None], QWidget | None],
    QWidget,
]


class ContentScrollArea(QScrollArea):
    """Scroll area that keeps the main content vertically scrollable only."""

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        central = self.window().centralWidget()
        if isinstance(central, AppShell):
            central.update_content_geometry()


class AppShell(QWidget):
    """Fixed-sidebar shell with route-driven page presentation."""

    def __init__(
        self,
        view_model: ShellViewModel,
        logo_path: Path,
        icon_directory: Path,
        page_factory: PageFactory | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("appShell")
        self.view_model = view_model
        self._logo_path = logo_path
        self._icon_directory = icon_directory
        self._page_factory = page_factory or create_page
        self._navigation_buttons: dict[AppRoute, QPushButton] = {}
        self._icon_names: dict[AppRoute, str] = {}
        self._pages: dict[AppRoute, QWidget] = {}
        self.router = PageRouter((item.route for item in view_model.navigation), self)
        self.router.route_changed.connect(self._show_route)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_main_content(), 1)

        for item in view_model.navigation:
            page = self._page_factory(item.route, view_model, self.navigate, self)
            self._pages[item.route] = page
            self.page_stack.addWidget(page)

        self.router.navigate(AppRoute.HOME)
        QTimer.singleShot(0, self.update_content_geometry)

    @property
    def navigation_buttons(self) -> dict[AppRoute, QPushButton]:
        return dict(self._navigation_buttons)

    @property
    def pages(self) -> dict[AppRoute, QWidget]:
        return dict(self._pages)

    @property
    def current_route(self) -> AppRoute | None:
        return self.router.current_route

    def navigate(self, route: AppRoute) -> None:
        self.router.navigate(route)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        brand_area = QWidget(sidebar)
        brand_area.setObjectName("brandArea")
        brand_area.setFixedHeight(BRAND_AREA_HEIGHT)
        brand_layout = QVBoxLayout(brand_area)
        brand_layout.setContentsMargins(20, 16, 20, 12)
        brand_layout.setSpacing(8)

        logo_label = QLabel(brand_area)
        logo_label.setObjectName("brandLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_label.setFixedHeight(44)
        logo = QPixmap(str(self._logo_path))
        if not logo.isNull():
            logo_label.setPixmap(
                logo.scaled(
                    QSize(176, 44),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo_label.setText("青舟节能")
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
            button.setIcon(
                load_tinted_icon(
                    self._icon_directory / f"{item.icon_name}.svg",
                    SIDEBAR_ICON_INACTIVE,
                )
            )
            button.setIconSize(QSize(18, 18))
            button.setCursor(
                Qt.CursorShape.ArrowCursor
                if item.reserved
                else Qt.CursorShape.PointingHandCursor
            )
            if item.reserved:
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _checked=False, route=item.route: self.navigate(route))
            navigation_layout.addWidget(button)
            self._navigation_buttons[item.route] = button
        sidebar_layout.addWidget(navigation)
        sidebar_layout.addStretch(1)

        settings_row = QWidget(sidebar)
        settings_layout = QVBoxLayout(settings_row)
        settings_layout.setContentsMargins(12, 0, 12, 16)
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

        scroll_host = QWidget()
        scroll_host.setObjectName("scrollHost")
        scroll_layout = QVBoxLayout(scroll_host)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        self.page_stack = QStackedWidget(scroll_host)
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

    def _show_route(self, route: AppRoute) -> None:
        page = self._pages.get(route)
        if page is None:
            return
        self.page_stack.setCurrentWidget(page)
        for item_route, button in self._navigation_buttons.items():
            is_active = item_route is route
            button.setChecked(is_active)
            button.setIcon(
                load_tinted_icon(
                    self._icon_directory / f"{self._icon_names[item_route]}.svg",
                    SIDEBAR_ICON_ACTIVE if is_active else SIDEBAR_ICON_INACTIVE,
                )
            )
        self.update_content_geometry()

    def update_content_geometry(self) -> None:
        if not hasattr(self, "page_stack"):
            return
        available_width = max(0, self.main_scroll_area.viewport().width())
        content_width = min(MAIN_CONTENT_MAX_WIDTH, available_width)
        self.page_stack.setFixedWidth(content_width)
        available_height = max(0, self.main_scroll_area.viewport().height())
        self.page_stack.setMinimumHeight(available_height)
        page_margin = COMPACT_PAGE_MARGIN if self.width() <= 1366 else WIDE_PAGE_MARGIN
        for page in self._pages.values():
            setter = getattr(page, "set_page_margin", None)
            if setter is not None:
                setter(page_margin)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self.update_content_geometry()
