"""P3-C Windows Qt automated UI evidence; distinct from human acceptance."""
from __future__ import annotations
import argparse
import ast
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def write_scope_proof(output_dir: Path) -> None:
    """Prove reporting and non-target UI layers match the integrated base."""
    import subprocess

    def git_blob(revision: str, path: str) -> bytes:
        return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)

    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    protected = [
        "packages/application/reporting/model.py",
        "packages/application/reporting/appendix_b.py",
        "packages/application/reporting/appendix_b_layout.json",
        "packages/application/reporting/service.py",
        "packages/infrastructure/reporting/word_renderer.py",
        "packages/ui/report_export.py",
        "packages/ui/shell.py",
        "packages/ui/carbon_material_page.py",
        "packages/ui/catalog_pages.py",
        "packages/standards/carbon_material.py",
        "packages/core/models.py",
        "platform-lock.json",
    ]
    protected_rows = []
    for relative in protected:
        baseline = git_blob(base, relative).replace(b"\r\n", b"\n")
        current = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        protected_rows.append({
            "path": relative,
            "unchanged": hashlib.sha256(baseline).digest() == hashlib.sha256(current).digest(),
            "baseline_sha256": hashlib.sha256(baseline).hexdigest(),
            "current_sha256": hashlib.sha256(current).hexdigest(),
        })
    assert all(item["unchanged"] for item in protected_rows), "protected production file changed"

    def classes(source: bytes) -> dict[str, str]:
        tree = ast.parse(source.decode("utf-8"))
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, ast.ClassDef)
        }

    baseline_classes = classes(git_blob(base, "packages/ui/pages.py"))
    current_classes = classes((ROOT / "packages/ui/pages.py").read_bytes())
    other_names = (set(baseline_classes) | set(current_classes)) - {"RecordLibraryPage"}
    unchanged_classes = [
        {"class": name, "unchanged_ast": baseline_classes.get(name) == current_classes.get(name)}
        for name in sorted(other_names)
    ]
    assert all(item["unchanged_ast"] for item in unchanged_classes), "non-record page class changed"
    sample = output_dir / "P3-C_FormalRecord_Appendix_B.docx"
    proof = {
        "base": base,
        "scope": "GHG-UI-P3-C Presentation",
        "protected_files": protected_rows,
        "unchanged_other_page_classes": unchanged_classes,
        "word_sample": sample.name if sample.exists() else None,
        "word_sample_sha256": hashlib.sha256(sample.read_bytes()).hexdigest() if sample.exists() else None,
    }
    (output_dir / "scope-and-rpt02-proof.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("windows", "offscreen"), default="windows")
    parser.add_argument("--scale", choices=("1.0", "1.25", "1.5"), default="1.0")
    parser.add_argument("--width", type=int, default=1366)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = args.platform
    os.environ["QT_SCALE_FACTOR"] = args.scale
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QTabWidget
    from docx import Document
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import CatalogQueryService
    from packages.application.carbon_accounting import CarbonAccountingUseCase, create_g06_parameter_resolver
    from packages.application.reporting import build_saved_record_report
    from packages.infrastructure.reporting.word_renderer import render_report_docx
    from packages.persistence import SQLiteCatalogRepository, SQLiteRecordRepository, build_catalog_database
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.standards.carbon_material import CarbonMaterialCalculator
    from packages.ui.view_models import AppRoute
    from scripts.rpt02_acceptance_samples import _gui_canonical_input, _formal_record, _frozen_record_payload
    from tests.test_g07_records import _record

    app = QApplication([])
    for font in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"):
        QFontDatabase.addApplicationFont(font)
    app.setFont(QFont("Microsoft YaHei", 10))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{args.platform}-{args.width}x{args.height}-{int(float(args.scale)*100)}"
    evidence = {
        "evidence_type": f"Windows PySide6 {app.platformName()} automated",
        "human_acceptance": "NOT_PERFORMED",
        "os": platform.platform(), "scale": args.scale,
        "requested_logical_size": [args.width, args.height], "checks": [], "captures": [],
        "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT/"packages/ui/pages.py", ROOT/"packages/ui/record_experience.py")},
    }
    def check(value, name):
        evidence["checks"].append({"name": name, "passed": bool(value)})
        assert value, name

    with tempfile.TemporaryDirectory(prefix="p3c-ui-") as directory:
        stage = Path(directory)
        catalog = build_catalog_database(DEFAULT_SOURCE_PATH, stage/"catalog.sqlite")
        catalog_repo = SQLiteCatalogRepository(catalog)
        repo = SQLiteRecordRepository(stage/"records.sqlite")
        calculator = CarbonMaterialCalculator(parameter_resolver=create_g06_parameter_resolver(catalog_repo))
        record = _formal_record(CarbonAccountingUseCase(calculator, repo), _gui_canonical_input())
        for i in range(125):
            repo.create(_record(f"p3c.list-demo.{i:03}", warning=bool(i % 2)))
        before = _frozen_record_payload(repo, record)
        window = create_main_window(
            AppConfig(catalog_database=catalog, records_database=stage/"records.sqlite",
                      projects_database=stage/"projects.sqlite"),
            catalog_service=CatalogQueryService(catalog_repo), record_repository=repo)
        window.resize(args.width, args.height)
        window.show()
        shell = window.centralWidget()
        shell.navigate(AppRoute.RECORDS)
        page = shell.pages[AppRoute.RECORDS]
        def settle():
            for _ in range(4):
                app.processEvents()
                QTest.qWait(30)
            shell.update_content_geometry()
            app.processEvents()
        def capture(name):
            settle()
            target = args.output_dir/f"{prefix}-{name}.png"
            pixmap = window.grab()
            check(pixmap.save(str(target)), f"保存截图 {name}")
            evidence["captures"].append({"file": target.name,
                "logical_window": [window.width(), window.height()],
                "physical_image": [pixmap.width(), pixmap.height()],
                "device_pixel_ratio": pixmap.devicePixelRatio()})
        settle()
        page.search_input.setFocus()
        settle()
        check(app.platformName() == args.platform, "使用指定 Qt 平台")
        check(page.record_list.count() == 126, "完整126条记录")
        check(page.view_stack.currentWidget() is page.list_view, "初始独立列表")
        capture("list")
        page.record_list.setFocus()
        QTest.keyClick(page.record_list, Qt.Key.Key_End)
        check(page.record_list.currentRow() == 125, "键盘访问列表尾项")
        QTest.keyClick(page.record_list, Qt.Key.Key_Return)
        check(page.view_stack.currentWidget() is page.detail_view, "Enter进入独立详情")
        page.back_to_records_button.click()
        page.search_input.setText("p3c.list-demo.124")
        page.search_input.setFocus()
        settle()
        check(page.record_list.count() == 1, "末尾记录真实检索")
        capture("search")
        check(page.open_record(record.record_id), "打开正式Application记录")
        settle()
        check(page.detail_tabs.count() == 2 and len(page.findChildren(QTabWidget)) == 1, "恰好两个页签且无嵌套")
        check([page.detail_tabs.tabText(i) for i in range(2)] == ["基本信息与结果", "输入数据与计算依据"], "页签标签")
        capture("basic-results")
        page.detail_tabs.setCurrentIndex(1)
        capture("input-basis")
        page.input_basis_text.verticalScrollBar().setValue(page.input_basis_text.verticalScrollBar().maximum())
        capture("basis-end")
        check(page.width() <= shell.main_scroll_area.viewport().width(), "页面无横向溢出")
        check(not shell.main_scroll_area.horizontalScrollBar().isVisible(), "无外层横向滚动")
        check(not hasattr(page, "audit_button"), "没有审计详情入口")
        if args.scale == "1.0" and args.width == 1366:
            destination = args.output_dir/"P3-C_FormalRecord_Appendix_B.docx"
            reference = stage/"reference.docx"
            supplementary = {"prepared_on": "2026-10-10"}
            with patch.object(page, "_report_supplementary_dialog", return_value=supplementary), patch(
                "packages.ui.report_export.QFileDialog.getSaveFileName", return_value=(str(destination), "")), patch(
                "packages.ui.report_export.QMessageBox.information"), patch(
                "packages.ui.report_export.QMessageBox.critical") as failure:
                page.export_word_button.click()
                failure.assert_not_called()
            model = build_saved_record_report(repo, record, supplementary_info=supplementary)
            render_report_docx(model, reference)
            check(Document(destination)._element.body.xml == Document(reference)._element.body.xml, "RPT02公共renderer业务内容一致")
            evidence["word_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        check(_frozen_record_payload(repo, record) == before, "查看和导出不修改历史Record与快照")
        check(len(repo.list_all()) == 126, "导出不新增Record")
        window.close()
        window.deleteLater()
        app.processEvents()
    (args.output_dir/f"{prefix}-proof.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    write_scope_proof(args.output_dir)
    print(f"PASS {prefix}: {len(evidence['checks'])} checks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
