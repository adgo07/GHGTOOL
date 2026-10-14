from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from apps.carbon_accounting_desktop.product import carbon_accounting_view_model
from packages.application.project_workspaces import (
    AccountingUnitType,
    AccountingUnitWorkspace,
    ProjectWorkspace,
    ProjectWorkspaceService,
)
from packages.core import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    CalculationLine,
    CalculationResult,
    PeriodType,
    RecordStatus,
)
from packages.persistence import SQLiteProjectWorkspaceRepository, SQLiteRecordRepository
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute
import packages.ui.shell as shell_module
import packages.ui.pages as pages_module


class PaintProbe(QObject):
    def __init__(self, started: float) -> None:
        super().__init__()
        self.started = started
        self.first_paint: float | None = None

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Paint and self.first_paint is None:
            self.first_paint = time.perf_counter()
        return False


def make_record(index: int) -> AccountingRecord:
    standard_id = "gbt_32151_34_2024"
    created = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=index)
    period = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))
    input_snapshot = AccountingInput(
        input_id=f"input.bench-{index:05d}",
        standard_id=standard_id,
        period=period,
        enterprise_name=f"临时基准企业-{index:05d}",
    )
    result = CalculationResult(
        result_id=f"result.bench-{index:05d}",
        standard_id=standard_id,
        algorithm_version="CAR-SM01-NAV-BENCH",
        lines=(CalculationLine(f"line.bench-{index:05d}", "source.energy", "CO2", "10.25", "tCO2"),),
        total_amount="10.25",
        total_unit="tCO2",
        calculated_at=created,
    )
    return AccountingRecord(
        record_id=f"record.bench-{index:05d}",
        standard_id=standard_id,
        algorithm_version="CAR-SM01-NAV-BENCH",
        created_at=created,
        input_snapshot=input_snapshot,
        calculation_result=result,
        status=RecordStatus.COMPLETED,
        standard_version="2024",
    )


def time_list_all(repository, repeats: int) -> float:
    values = []
    for _ in range(repeats):
        started = time.perf_counter()
        repository.list_all()
        values.append((time.perf_counter() - started) * 1000)
    return statistics.median(values)


def time_list_summaries(repository, repeats: int) -> float:
    values = []
    for _ in range(repeats):
        started = time.perf_counter()
        repository.list_summaries()
        values.append((time.perf_counter() - started) * 1000)
    return statistics.median(values)


def instrument_method(target, method_name: str, metrics: dict[str, float | int], count_key: str, time_key: str) -> None:
    original = getattr(target, method_name)

    def measured(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            metrics[count_key] = int(metrics.get(count_key, 0)) + 1
            metrics[time_key] = float(metrics.get(time_key, 0.0)) + (time.perf_counter() - started) * 1000

    setattr(target, method_name, measured)


def timed_transition(shell: AppShell, route: AppRoute, app: QApplication, metrics: dict[str, float | int]) -> dict[str, object]:
    for key in ("repository_calls", "summary_calls", "repository_ms", "projects_calls", "projects_ms", "timestamps_calls", "timestamps_ms", "ensure_calls", "ensure_ms", "route_calls", "route_ms", "filter_calls", "filter_ms", "layout_calls", "layout_ms", "icons_calls", "icons_ms"):
        metrics[key] = 0
    button = shell.navigation_buttons[route]
    selected_at: list[float] = []

    def selected(checked: bool) -> None:
        if checked and not selected_at:
            selected_at.append(time.perf_counter())

    button.toggled.connect(selected)
    started = time.perf_counter()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    returned = time.perf_counter()
    selected_latency = ((selected_at[0] - started) * 1000) if selected_at else None
    click_return_latency = (returned - started) * 1000
    page = shell._pages.get(route)
    painted_latency = None
    if page is not None:
        probe = PaintProbe(started)
        page.installEventFilter(probe)
        for _ in range(4):
            app.processEvents()
        QTest.qWait(3)
        app.processEvents()
        if probe.first_paint is not None:
            painted_latency = (probe.first_paint - started) * 1000
        page.removeEventFilter(probe)
    page_visible = bool(page is not None and shell.page_stack.currentWidget() is page and page.isVisible())
    rows = getattr(getattr(page, "record_list", None), "rowCount", lambda: None)()
    checked = button.isChecked()
    try:
        button.toggled.disconnect(selected)
    except (TypeError, RuntimeError):
        pass
    return {
        "selected_state_ms": round(selected_latency, 3) if selected_latency is not None else None,
        "click_handler_return_ms": round(click_return_latency, 3),
        "first_page_paint_ms": round(painted_latency, 3) if painted_latency is not None else None,
        "page_visible_after_event_pump": page_visible,
        "table_rows_including_empty_state": rows,
        "records_read_calls": int(metrics["repository_calls"]) + int(metrics["summary_calls"]),
        "record_summary_query_calls": int(metrics["summary_calls"]),
        "records_read_ms": round(float(metrics["repository_ms"]), 3),
        "projects_read_calls": int(metrics["projects_calls"]),
        "projects_read_ms": round(float(metrics["projects_ms"]), 3),
        "project_timestamps_calls": int(metrics["timestamps_calls"]),
        "project_timestamps_ms": round(float(metrics["timestamps_ms"]), 3),
        "ensure_page_calls": int(metrics["ensure_calls"]),
        "ensure_page_ms": round(float(metrics["ensure_ms"]), 3),
        "route_handler_calls": int(metrics["route_calls"]),
        "route_handler_ms": round(float(metrics["route_ms"]), 3),
        "record_filter_render_calls": int(metrics["filter_calls"]),
        "record_filter_render_ms": round(float(metrics["filter_ms"]), 3),
        "layout_calls": int(metrics["layout_calls"]),
        "layout_ms": round(float(metrics["layout_ms"]), 3),
        "navigation_icon_loads": int(metrics["icons_calls"]),
        "navigation_icon_load_ms": round(float(metrics["icons_ms"]), 3),
        "selected_after_click": checked,
        "loaded_pages": len(shell._pages),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure desktop route navigation with temporary SQLite data.")
    parser.add_argument("--records", type=int, default=200)
    parser.add_argument("--projects", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="ghg-navigation-bench-") as directory:
        root = Path(directory)
        records = SQLiteRecordRepository(root / "records.sqlite")
        project_repository = SQLiteProjectWorkspaceRepository(root / "projects.sqlite")
        projects = ProjectWorkspaceService(project_repository)

        for index in range(args.records):
            records.create(make_record(index))
        for index in range(args.projects):
            unit_id = f"unit.bench-{index:05d}"
            workspace = ProjectWorkspace(
                project_id=f"project.bench-{index:05d}",
                name=f"临时基准项目-{index:05d}",
                active_unit_id=unit_id,
                units=(
                    AccountingUnitWorkspace(
                        unit_id=unit_id,
                        name="全厂",
                        unit_type=AccountingUnitType.WHOLE_SITE,
                        position=0,
                        form_state={"benchmark": index, "padding": "x" * 128},
                    ),
                ),
            )
            projects.save(workspace)

        records_reference_ms = time_list_all(records, max(1, min(args.repeats, 3)))
        summary_reference_ms = time_list_summaries(records, max(1, min(args.repeats, 3)))
        metrics: dict[str, float | int] = {}
        instrument_method(records, "list_all", metrics, "repository_calls", "repository_ms")
        instrument_method(records, "list_summaries", metrics, "summary_calls", "repository_ms")
        instrument_method(projects, "list_all", metrics, "projects_calls", "projects_ms")
        instrument_method(projects, "list_updated_at_by_project_id", metrics, "timestamps_calls", "timestamps_ms")

        icon_original = shell_module.load_tinted_icon

        def timed_icon(*icon_args, **icon_kwargs):
            started = time.perf_counter()
            try:
                return icon_original(*icon_args, **icon_kwargs)
            finally:
                metrics["icons_calls"] = int(metrics.get("icons_calls", 0)) + 1
                metrics["icons_ms"] = float(metrics.get("icons_ms", 0.0)) + (time.perf_counter() - started) * 1000

        shell_module.load_tinted_icon = timed_icon
        original_show_route = shell_module.AppShell._show_route
        def measured_show_route(instance, route):
            started = time.perf_counter()
            try:
                return original_show_route(instance, route)
            finally:
                metrics["route_calls"] = int(metrics.get("route_calls", 0)) + 1
                metrics["route_ms"] = float(metrics.get("route_ms", 0.0)) + (time.perf_counter() - started) * 1000
        shell_module.AppShell._show_route = measured_show_route

        original_apply_filters = pages_module.RecordLibraryPage._apply_filters
        def measured_apply_filters(instance, *filter_args, **filter_kwargs):
            started = time.perf_counter()
            try:
                return original_apply_filters(instance, *filter_args, **filter_kwargs)
            finally:
                metrics["filter_calls"] = int(metrics.get("filter_calls", 0)) + 1
                metrics["filter_ms"] = float(metrics.get("filter_ms", 0.0)) + (time.perf_counter() - started) * 1000
        pages_module.RecordLibraryPage._apply_filters = measured_apply_filters

        shell_started = time.perf_counter()
        shell = AppShell(
            carbon_accounting_view_model(),
            Path("resources/logo.png"),
            Path("resources/icons"),
            record_repository=records,
            project_service=projects,
        )
        loaded_pages_after_start = len(shell._pages)
        window = QMainWindow()
        window.setCentralWidget(shell)
        window.resize(1280, 840)
        window.show()
        app.processEvents()
        shell_construction_ms = (time.perf_counter() - shell_started) * 1000

        original_ensure = shell._ensure_page

        def measured_ensure(route):
            started = time.perf_counter()
            try:
                return original_ensure(route)
            finally:
                metrics["ensure_calls"] = int(metrics.get("ensure_calls", 0)) + 1
                metrics["ensure_ms"] = float(metrics.get("ensure_ms", 0.0)) + (time.perf_counter() - started) * 1000

        shell._ensure_page = measured_ensure
        original_layout = shell._apply_content_geometry

        def measured_layout():
            started = time.perf_counter()
            try:
                return original_layout()
            finally:
                metrics["layout_calls"] = int(metrics.get("layout_calls", 0)) + 1
                metrics["layout_ms"] = float(metrics.get("layout_ms", 0.0)) + (time.perf_counter() - started) * 1000

        shell._apply_content_geometry = measured_layout

        shell.navigate(AppRoute.STANDARDS)
        app.processEvents()
        cold = timed_transition(shell, AppRoute.RECORDS, app, metrics)

        cached = []
        for _ in range(args.repeats):
            shell.navigate(AppRoute.STANDARDS)
            app.processEvents()
            cached.append(timed_transition(shell, AppRoute.RECORDS, app, metrics))

        same_route = timed_transition(shell, AppRoute.RECORDS, app, metrics)

        result = {
            "data": {
                "synthetic_records": args.records,
                "synthetic_projects": args.projects,
                "records_returned_by_list_all": len(records.list_all()),
                "sqlite_record_list_all_median_ms": round(records_reference_ms, 3),
                "sqlite_record_summary_median_ms": round(summary_reference_ms, 3),
            },
            "startup": {
                "shell_and_home_construction_ms": round(shell_construction_ms, 3),
                "loaded_pages_after_start": loaded_pages_after_start,
            },
            "cold_first_records_route": cold,
            "cached_records_route_median": {
                key: round(statistics.median(float(item[key]) for item in cached), 3)
                for key in (
                    "selected_state_ms",
                    "click_handler_return_ms",
                    "first_page_paint_ms",
                    "records_read_ms",
                    "projects_read_ms",
                    "ensure_page_ms",
                    "layout_ms",
                    "navigation_icon_load_ms",
                )
            },
            "same_route_click": same_route,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        shell_module.load_tinted_icon = icon_original
        shell_module.AppShell._show_route = original_show_route
        pages_module.RecordLibraryPage._apply_filters = original_apply_filters
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()



