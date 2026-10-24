"""PR59 最终十四张真实 Qt 整窗截图；仅合成数据和隔离临时库。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, qVersion
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QPushButton
from packages.ui.dialogs import MessageBox
from tests.test_pr59_compatibility_navigation import PR59CompatibilityNavigationTests
from packages.standards.carbon_material import FuelType


def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    app = QApplication.instance() or QApplication([])
    # Developer capture only: register fonts already installed on this machine.
    fonts = {name: QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))
             for name in ("msyh.ttc", "msyhbd.ttc", "seguisym.ttf")}
    assert all(value >= 0 for value in fonts.values()), fonts
    case = PR59CompatibilityNavigationTests()
    case.setUpClass()
    case.setUp()
    scenes = []
    source_paths = sorted({p.relative_to(ROOT).as_posix() for folder in ("apps", "packages", "resources")
                           for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
                           and p.suffix in (".py", ".json", ".yaml", ".yml", ".svg")}
                          | {"scripts/capture_pr59_final.py", "tests/test_pr59_compatibility_navigation.py"})
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths}

    def select(page, shell, group):
        page.source_directory.select(group)
        case.pump()
        outer = shell.main_scroll_area
        outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(), QPoint()).y())
        case.pump()

    def snap(name, page, shell, records, target=None):
        case.pump()
        if target is not None:
            case.assert_in_viewport(shell, target)
        window = shell.window()
        image = window.grab()
        assert image.save(str(output / (name + ".png")))
        scenes.append({"name": name, "window": [window.width(), window.height()],
                       "viewport": [shell.main_scroll_area.viewport().width(), shell.main_scroll_area.viewport().height()],
                       "dpr": image.devicePixelRatio(), "records": len(records.list_all()),
                       "target_fully_inside_viewport": target is not None,
                       "target": target.objectName() if target is not None else None})

    try:
        with case.page("fuel", (1680, 1000)) as (page, projects, records, shell):
            page.enterprise_name.setText("合成视觉复核企业")
            page._toggle_source_group("fuel")
            fuel = page._fuel_rows[0]
            fuel.fuel_type.setCurrentIndex(fuel.fuel_type.findData(FuelType.NATURAL_GAS))
            fuel.fuel_type.confirm_name(force=True)
            fuel.activity.setText("123.45")
            select(page, shell, "fuel")
            snap("01-fuel-wide", page, shell, records)
            shell.window().resize(1180, 850)
            select(page, shell, "fuel")
            snap("02-fuel-narrow", page, shell, records)
            for combo in page._source_statuses.values():
                combo.setCurrentIndex(combo.findData("NOT_INVOLVED"))
            page._toggle_source_group("fuel")
            page.period_year.setValue(2025)
            page.boundary_confirmed.setChecked(True)
            page.calculate_button.click()
            case.pump()
            assert len(records.list_all()) == 1
            page.source_directory.results_requested.emit()
            case.pump()
            snap("13-shared-result", page, shell, records)
        for index, size in ((3, (1680, 1000)), (4, (1180, 850))):
            with case.page("material-" + str(index), size) as (page, projects, records, shell):
                process, material = case.material_failure(page)
                select(page, shell, "fuel")
                before = page._capture_form_state()
                case.click_error(page, shell, material["mass"])
                assert page._capture_form_state() == before
                assert not records.list_all()
                snap(f"{index:02}-material-first-error", page, shell, records, material["mass"])
        for index, group in ((5, "baking"), (6, "graphitization"), (10, "fgd"), (11, "electricity"), (12, "heat")):
            with case.page(group, (1680, 1000)) as (page, projects, records, shell):
                page.enterprise_name.setText("合成视觉复核企业")
                page._toggle_source_group(group)
                if group in ("baking", "graphitization"):
                    material = page._process_rows[group][0]["materials"][0]
                    material["name"].setText("合成测试物料")
                    material["mass"].setText("12.5")
                select(page, shell, group)
                snap(f"{index:02}-{group}", page, shell, records)
        for index, value in ((7, "7"), (8, "")):
            name = "legacy-" + str(index)
            project_id = case.save_legacy(name, value)
            with case.page(name, (1180, 850)) as (page, projects, records, shell):
                with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Discard):
                    page.open_project_from_home(project_id)
                assert page._workspace.project_id == project_id
                row = page._process_rows["fume"][0]
                select(page, shell, "fume")
                target = row["fields"]["duration"]
                if not value:
                    page.calculate_button.click()
                    case.pump()
                    case.click_error(page, shell, target)
                else:
                    page._scroll_to_widget(target)
                    case.pump()
                snap(f"{index:02}-legacy-duration", page, shell, records, target)
                if value:
                    with patch.object(MessageBox, "question", return_value=MessageBox.StandardButton.Yes):
                        row["upgrade_button"].click()
                    assert page._fume_execution_version == "FUME_V2"
                    page._scroll_to_widget(row["segment_start"])
                    case.pump()
                    snap("09-explicit-fume-upgrade", page, shell, records, row["segment_start"])
        with case.page("conversion", (1180, 850)) as (page, projects, records, shell):
            process, material = case.material_failure(page, conversion=True)
            toggle = next(button for button in material["widget"].findChildren(QPushButton)
                          if button.text().startswith("数据基准与换算"))
            if toggle.isChecked():
                toggle.click()
            select(page, shell, "fuel")
            before = page._capture_form_state()
            target = material["moisture_received_percent"]
            case.click_error(page, shell, target)
            assert toggle.isChecked() and before == page._capture_form_state()
            snap("14-folded-conversion-first-error", page, shell, records, target)
        assert len(scenes) == 14 and not case.callback_errors
        assert hashes == {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths}
        summary = {"code_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   "source_files_sha256": hashes, "qt": qVersion(), "platform": app.platformName(),
                   "font_registration_developer_process_only": fonts, "scenes": scenes,
                   "callback_errors": case.callback_errors, "synthetic_data_only": True}
        (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        (output / "review.html").write_text('<!doctype html><meta charset="utf-8"><title>PR59 最终复核</title>'
            '<style>body{font:16px sans-serif;margin:24px}img{max-width:100%;border:1px solid #bbb}</style>'
            '<h1>PR59 最终十四张真实 Qt 整窗截图</h1><p>合成输入；offscreen，不代表原生桌面或人工 DPI 验收。</p>'
            + ''.join(f'<h2>{p.stem}</h2><img src="{p.name}">' for p in sorted(output.glob('*.png'))), encoding="utf-8")
        print("PASS: 14 whole-window screenshots; source hashes stable; Qt callback errors 0")
    finally:
        case.tearDown()


if __name__ == "__main__":
    main()
