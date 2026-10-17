"""Windows Qt programmatic evidence; not human or OS-input acceptance."""
from __future__ import annotations
import argparse, hashlib, json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("1", "1.25", "1.5"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = args.scale
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.persistence import build_catalog_database, InMemoryRecordRepository
    from packages.ui.view_models import AppRoute
    from packages.standards.carbon_material import FuelType
    from packages.ui.compact_choices import SegmentedChoiceControl
    app = QApplication([])
    app.setFont(QFont("Microsoft YaHei", 10))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    evidence = {"type": "Windows Qt programmatic driver / QWidget.grab", "human_acceptance": "OPEN",
                "scale": args.scale, "checks": [], "captures": [], "sources": {}}
    for name in ("packages/ui/carbon_material_page.py", "packages/ui/carbon_material_fuel.py", "packages/ui/compact_choices.py", "packages/ui/field_specs.py", "packages/standards/carbon_material_input_policy.py"):
        evidence["sources"][name] = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="pr46-source-qa-") as folder:
        base = Path(folder)
        records = InMemoryRecordRepository()
        config = AppConfig(catalog_database=build_catalog_database(output_path=base/"catalog.sqlite"),
                           records_database=base/"records.sqlite", projects_database=base/"projects.sqlite")
        window = create_main_window(config, record_repository=records)
        window.resize(1366, 768)
        window.show()
        shell = window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        page = shell.pages[AppRoute.NEW_ACCOUNTING]
        page.enterprise_name.setText("来源控件专项合成企业")
        def settle():
            for _ in range(4):
                app.processEvents()
                QTest.qWait(20)
        def check(value, label):
            evidence["checks"].append({"label": label, "passed": bool(value)})
            assert value, label
        def capture(label, widget):
            shell.main_scroll_area.ensureWidgetVisible(widget)
            settle()
            pixmap = window.grab()
            file = f"source-{args.scale}-{label}.png"
            assert pixmap.save(str(args.output_dir/file))
            evidence["captures"].append({"file": file, "pixels": [pixmap.width(), pixmap.height()], "dpr": pixmap.devicePixelRatio()})
        check(app.platformName() == "windows", "实际Windows Qt平台")
        settle()
        if not page._source_is_enabled("CAR-SRC-FUEL-001"):
            page._toggle_source_group("fuel")
        row = page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
        row.fuel_type.confirm_name(force=True)
        check(row.carbon_source.currentData() == "STANDARD_DEFAULT" and row.carbon.isReadOnly(), "目录FCh初始缺省锁定")
        capture("fuel-default", row)
        row.carbon_source.setCurrentIndex(row.carbon_source.findData("MEASURED"))
        check(not row.carbon.isReadOnly() and row.carbon.text() == "", "目录FCh改源留空可编辑")
        row.carbon.setText("0.01234567890123456789")
        capture("fuel-manual", row)
        row.fuel_type.setEditText("企业混合燃料")
        row.fuel_type.confirm_name(force=True)
        check(all(not edit.text() for edit in (row.carbon, row.lower_heating_value, row.oxidation)), "自定义燃料数值全部手填")
        capture("fuel-custom", row)
        if not page._source_is_enabled("CAR-SRC-FGD-001"):
            page._toggle_source_group("fgd")
        unit = page._process_rows["fgd"][0]
        unit["reagent_name"].setText("专项合成脱硫剂")
        first = unit["components"][0]
        first["carbonate_type"].setEditText("CaCO3")
        first["carbonate_type"].confirm_name(force=True)
        check(first["ef1"].isReadOnly() and first["ef1_source"].currentData() == "STANDARD_DEFAULT", "匹配C2因子锁定")
        check((first["i"].text(), first["tr"].text()) == ("90", "100"), "单组分通用缺省90和100")
        capture("fgd-single", unit["widget"])
        second = page._add_fgd_component(unit)
        check(first["i_source"].currentData() == "STANDARD_DEFAULT" and first["i"].text() == "90", "新增组分保留原90草稿")
        control = next(item for item in first["_widget"].findChildren(SegmentedChoiceControl) if item.combo is first["i_source"])
        check(control.values == frozenset({"MEASURED"}) and control.notice.text() == "历史来源不适用，请确认", "多组分首行明确确认提示")
        check(second["i"].text() == "" and second["tr"].text() == "100", "新组分I留空TR通用默认")
        capture("fgd-multiple-pending", unit["widget"])
        first["i_source"].setCurrentIndex(first["i_source"].findData("MEASURED"))
        first["i"].setText("60.1234567890123456789")
        page._remove_fgd_component(unit, second["component_id"])
        check(first["i"].text() == "60.1234567890123456789" and first["i_source"].currentData() == "MEASURED", "删除组分保留实测")
        capture("fgd-single-measured", unit["widget"])
        if not page._source_is_enabled("CAR-SRC-CALCINATION-001"):
            page._toggle_source_group("calcination")
        material_unit = page._process_rows["calcination"][0]
        material = material_unit["materials"][0]
        material["name"].setText("专项合成煅烧物料")
        check(material["fixed_carbon_source"].currentText() == "实测值", "物料成分唯一实测来源")
        capture("material-measured", material_unit["widget"])
        check(len(records.list_all()) == 0, "展示核查不生成Record")
        window.hide()
        window.deleteLater()
        app.processEvents()
    (args.output_dir/f"source-{args.scale}.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"PASS scale={args.scale}: {len(evidence['checks'])} checks, {len(evidence['captures'])} captures; human acceptance OPEN")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
