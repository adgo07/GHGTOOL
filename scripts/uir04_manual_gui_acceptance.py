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
from packages.persistence import (  # noqa: E402
    InMemoryRecordRepository,
    SQLiteCatalogRepository,
    build_catalog_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH  # noqa: E402
from packages.standards.carbon_material import (  # noqa: E402
    EmissionSourceStatus,
    FuelPath,
    FuelType,
    MaterialBasis,
)
from packages.standards.carbon_material_normalization import MaterialRole
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
    groups = {
        F01: "fuel",
        P01: "calcination",
        I01: "electricity",
        "CAR-SRC-EXPORTED-ELECTRICITY-001": "electricity",
        "CAR-SRC-PURCHASED-HEAT-001": "heat",
        "CAR-SRC-EXPORTED-HEAT-001": "heat",
    }
    if not page._source_is_enabled(source_id):
        page._source_toggle_buttons[groups[source_id]].click()
def _validation_text(page) -> str:
    """Collect all user-facing validation labels from the grouped tree."""

    labels: list[str] = []

    def visit(parent) -> None:
        count = page.validation_list.topLevelItemCount() if parent is None else parent.childCount()
        for index in range(count):
            item = page.validation_list.topLevelItem(index) if parent is None else parent.child(index)
            labels.append(item.text(0))
            visit(item)

    visit(None)
    return "\n".join(labels)


def _scenario_a(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景A燃料购电企业")
        page.period_year.setValue(2026)
        page.boundary_confirmed.setChecked(True)
        _involve(page, F01)
        fuel = page._fuel_rows[0]
        natural_gas = fuel.fuel_type.findData(FuelType.NATURAL_GAS)
        if natural_gas >= 0:
            fuel.fuel_type.setCurrentIndex(natural_gas)
        else:
            fuel.fuel_type.setEditText("天然气")
        fuel.path.setCurrentIndex(fuel.path.findData(FuelPath.MASS))
        fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("DIRECT"))
        fuel.activity.setText("10")
        fuel.carbon_direct.setText("0.0153")
        fuel.direct_carbon_source.setCurrentIndex(fuel.direct_carbon_source.findData("MEASURED"))
        fuel.oxidation.setText("94")
        fuel.oxidation_source.setCurrentIndex(fuel.oxidation_source.findData("USER_DEFINED"))
        _involve(page, I01)
        row = next(row for row in page._energy_family_rows["electricity"] if row.kind.currentData() == "purchased_electricity")
        row.line_id.setText("grid-ordinary")
        row.amount.setText("20")
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.ORDINARY))
        page._run_calculation()
        assert page.result_card.isVisible(), {
            "validation": _validation_text(page),
            "professional_details": page.validation_professional_details.text(),
        }
        assert len(repository.list_all()) == 1
        return (
            f"场景A PASS：燃料直接含碳量+购入常规电力完成计算；结果={page.result_total.text()}；"
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
        process = page._process_rows["calcination"][0]
        feed, = process["materials"]
        feed["role"].setCurrentIndex(feed["role"].findData(MaterialRole.CALCINATION_FEED))
        feed["name"].setText("煅烧原料")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("50")
        feed["volatile_matter"].setText("10")
        product = page._add_material_line(process)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("70")
        product["fixed_carbon"].setText("25")
        product["volatile_matter"].setText("2")
        page._run_calculation()
        assert page.result_card.isVisible(), _validation_text(page)
        assert len(repository.list_all()) == 1
        return f"场景B PASS：原料煅烧物料行按收到基默认口径完成；{page.result_status.text()}"
    finally:
        _close_page(application, window)
def _scenario_c(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景C历史口径兼容企业")
        page.boundary_confirmed.setChecked(True)
        _involve(page, P01)
        process = page._process_rows["calcination"][0]
        feed, = process["materials"]
        feed["role"].setCurrentIndex(feed["role"].findData(MaterialRole.CALCINATION_FEED))
        feed["name"].setText("煅烧原料")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("50")
        feed["volatile_matter"].setText("10")
        product = page._add_material_line(process)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("70")
        product["fixed_carbon"].setText("25")
        product["volatile_matter"].setText("2")

        # Simulate a saved legacy project carrying non-received-basis rows.
        # Preserve those values; missing conversion evidence must block by the
        # Domain rule instead of relabeling the rows as received-basis inputs.
        controls = page._material_controls["calcination"]
        for key in ("mass_basis", "composition_basis"):
            controls[key].setCurrentIndex(controls[key].findData(MaterialBasis.DRY))
        controls["normalized_basis"].setCurrentIndex(
            controls["normalized_basis"].findData(MaterialBasis.RECEIVED)
        )
        current = page._input().calcinations[0]
        assert current.mass_basis is MaterialBasis.DRY
        assert current.composition_basis is MaterialBasis.DRY
        assert current.normalized_basis is MaterialBasis.RECEIVED
        assert not current.moisture_evidence
        assert not current.conversion_evidence
        assert current.material_rows

        page._run_calculation()
        messages = _validation_text(page)
        assert page.result_card.isHidden(), messages
        assert page.quality_card.isVisible(), messages
        assert "换算依据" in messages, messages
        assert len(repository.list_all()) == 0
        return "场景C PASS：旧DRY物料及归一口径原值保留；缺少换算证据时按规则阻断且不生成记录。"
    finally:
        _close_page(application, window)
def _scenario_d(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.enterprise_name.setText("场景D非化石电力企业")
        page.period_year.setValue(2026)
        page.boundary_confirmed.setChecked(True)
        _involve(page, I01)
        row = next(row for row in page._energy_family_rows["electricity"] if row.kind.currentData() == "purchased_electricity")
        row.line_id.setText("purchased-nonfossil")
        row.amount.setText("20")
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.NONFOSSIL))
        assert not hasattr(row, "proof_type")
        assert not hasattr(row, "proof_status")
        page._run_calculation()
        assert page.result_card.isVisible(), _validation_text(page)
        assert len(repository.list_all()) == 1
        return f"场景D PASS：非化石购电无需证明字段仍可完成核算；{row.status.text()}；{page.result_status.text()}"
    finally:
        _close_page(application, window)
def _scenario_e(application: QApplication, catalog_service: CatalogQueryService, catalog_path: Path) -> str:
    window, page, repository = _open_page(application, catalog_service, catalog_path)
    try:
        page.boundary_confirmed.setChecked(True)
        page._run_calculation()
        assert page.result_card.isVisible(), _validation_text(page)
        assert len(repository.list_all()) == 1
        assert repository.list_all()[0].input_snapshot.enterprise_name is None
        return f"场景E PASS：企业名称留空仍可成功核算；记录数={len(repository.list_all())}；状态={page.result_status.text()}"
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
