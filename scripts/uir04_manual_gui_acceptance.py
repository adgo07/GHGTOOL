"""Run the five UIR04 GUI acceptance scenarios with an isolated catalog.

This is a deterministic acceptance probe for the Windows Qt page.  It drives
the same visible widgets a user operates, prints the observed business labels,
and leaves no database outside the temporary directory.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from apps.carbon_accounting_desktop.app import create_main_window  # noqa: E402
from apps.carbon_accounting_desktop.config import AppConfig  # noqa: E402
from packages.application import CatalogQueryService  # noqa: E402
from packages.core import (  # noqa: E402
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
)
from packages.persistence import SQLiteCatalogRepository, build_catalog_database  # noqa: E402
from packages.reference_data import DEFAULT_SOURCE_PATH  # noqa: E402
from packages.standards.carbon_material import (  # noqa: E402
    EmissionSourceStatus,
    InMemoryRecordRepository,
    MaterialBasis,
)
from packages.ui.view_models import AppRoute  # noqa: E402


F01 = "CAR-SRC-FUEL-001"
I01 = "CAR-SRC-PURCHASED-ELECTRICITY-001"
P01 = "CAR-SRC-CALCINATION-001"


def _configure_console_encoding() -> None:
    """Keep Chinese business observations printable on Windows runners."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _open_page(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path):
    repository = InMemoryRecordRepository()
    window = create_main_window(
        AppConfig(catalog_database=catalog_path),
        catalog_service=catalog_service,
        record_repository=repository,
    )
    window.show()
    application.processEvents()
    shell = window.centralWidget()
    shell.navigate(AppRoute.NEW_ACCOUNTING)
    application.processEvents()
    return window, shell.pages[AppRoute.NEW_ACCOUNTING], repository


def _close_page(application: QApplication, window) -> None:
    window.close()
    window.deleteLater()
    application.processEvents()


def _involve(page, source_id: str) -> None:
    combo = page._source_statuses[source_id]
    combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))


def _scenario_a(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景A燃料购电企业")
        page.period_year.setValue(2026)
        page.boundary_confirmed.setChecked(True)
        _involve(page, F01)
        for key, value in (
            ("fuel_id", "natural-gas"),
            ("fuel_activity", "10"),
            ("fuel_carbon", "0.2"),
            ("fuel_oxidation", "98"),
        ):
            page._fields[key].setText(value)
        _involve(page, I01)
        row = page._electricity_rows[0]
        row.detail_id.setText("grid-ordinary")
        row.amount.setText("20")
        row.acquisition.setCurrentIndex(row.acquisition.findData(ElectricityAcquisitionMode.PURCHASED))
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.ORDINARY))
        page._run_calculation()
        assert page.result_card.isVisible()
        assert len(repository.list_all()) == 1
        return (
            f"场景A PASS：燃料+购入常规电力完成计算；结果={page.result_total.text()}；"
            f"记录数={len(repository.list_all())}；状态={page.result_status.text()}"
        )
    finally:
        _close_page(application, window)


def _scenario_b(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景B收到基企业")
        page.boundary_confirmed.setChecked(True)
        _involve(page, P01)
        for field, value in {
            "gc": "100",
            "wfc": "50",
            "cc": "70",
            "ucc": "5",
            "du": "1",
            "wfc_c": "25",
            "wvar": "10",
            "wvar_c": "2",
        }.items():
            page._fields[f"calcination.{field}"].setText(value)
        page._run_calculation()
        assert page.result_card.isVisible()
        assert len(repository.list_all()) == 1
        return f"场景B PASS：原料煅烧收到基默认口径完成；{page.result_status.text()}"
    finally:
        _close_page(application, window)


def _scenario_c(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景C基准差异企业")
        page.boundary_confirmed.setChecked(True)
        _involve(page, P01)
        for field, value in {
            "gc": "100",
            "wfc": "50",
            "cc": "70",
            "ucc": "5",
            "du": "1",
            "wfc_c": "25",
            "wvar": "10",
            "wvar_c": "2",
        }.items():
            page._fields[f"calcination.{field}"].setText(value)
        controls = page._material_controls["calcination"]
        controls["mass_basis"].setCurrentIndex(controls["mass_basis"].findData(MaterialBasis.DRY))
        controls["composition_basis"].setCurrentIndex(
            controls["composition_basis"].findData(MaterialBasis.RECEIVED)
        )
        page._run_calculation()
        text = "\n".join(
            page.validation_list.item(index).text()
            for index in range(page.validation_list.count())
        )
        assert "不能直接计算" in text
        assert not page.result_card.isVisible()
        assert len(repository.list_all()) == 0
        return f"场景C PASS：干基/收到基差异被阻断；实际提示={text}"
    finally:
        _close_page(application, window)


def _scenario_d(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景D非化石电力企业")
        page.period_year.setValue(2026)
        page.boundary_confirmed.setChecked(True)
        _involve(page, I01)
        row = page._electricity_rows[0]
        row.detail_id.setText("purchased-nonfossil")
        row.amount.setText("20")
        row.acquisition.setCurrentIndex(row.acquisition.findData(ElectricityAcquisitionMode.PURCHASED))
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.NONFOSSIL))
        row.proof_type.setCurrentIndex(
            row.proof_type.findData(ElectricityProofType.CONTRACT_AND_SETTLEMENT)
        )
        row.proof_status.setCurrentIndex(row.proof_status.findData(ElectricityProofStatus.VALID))
        page._run_calculation()
        assert page.result_card.isVisible()
        assert "已确定" in row.parameter_status.text()
        assert len(repository.list_all()) == 1
        return f"场景D PASS：有效非化石电力证明通过；{row.parameter_status.text()}；{page.result_status.text()}"
    finally:
        _close_page(application, window)


def _scenario_e(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.calculate_button.click()
        application.processEvents()
        text = "\n".join(
            page.validation_list.item(index).text()
            for index in range(page.validation_list.count())
        )
        assert "企业名称为必填项" in text
        assert not page.result_card.isVisible()
        assert len(repository.list_all()) == 0
        return f"场景E PASS：缺少企业名称被阻断；错误计数={page.error_count.text()}；提示={text}"
    finally:
        _close_page(application, window)


def main() -> int:
    _configure_console_encoding()
    application = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="uir04-gui-") as directory:
        catalog_path = build_catalog_database(
            DEFAULT_SOURCE_PATH,
            Path(directory) / "catalog.sqlite",
            app_version="1.1.0",
        )
        service = CatalogQueryService(
            SQLiteCatalogRepository(catalog_path),
            as_of=__import__("datetime").date(2026, 9, 12),
        )
        observations = (
            _scenario_a(application, service, catalog_path),
            _scenario_b(application, service, catalog_path),
            _scenario_c(application, service, catalog_path),
            _scenario_d(application, service, catalog_path),
            _scenario_e(application, service, catalog_path),
        )
    print("UIR04 人工 GUI 验收脚本观察结果")
    for observation in observations:
        print(observation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
