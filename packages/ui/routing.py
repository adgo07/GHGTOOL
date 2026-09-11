"""Small route controller for the public desktop shell."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QObject, Signal

from .view_models import AppRoute


class PageRouter(QObject):
    """Validate and publish route changes without knowing page business logic."""

    route_changed = Signal(object)

    def __init__(self, routes: Iterable[AppRoute], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._routes = frozenset(routes)
        if not self._routes:
            raise ValueError("at least one route is required")
        self._current_route: AppRoute | None = None

    @property
    def current_route(self) -> AppRoute | None:
        return self._current_route

    def navigate(self, route: AppRoute) -> None:
        if route not in self._routes:
            raise ValueError(f"unsupported route: {route!r}")
        if route == self._current_route:
            return
        self._current_route = route
        self.route_changed.emit(route)
