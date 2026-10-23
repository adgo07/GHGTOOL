"""Reproducible offscreen PR-A views; no user database or desktop control."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--accounting", action="store_true")
    args = parser.parse_args()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    if dirty:
        raise RuntimeError("capture requires a clean committed worktree")
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import qVersion
    from PySide6.QtGui import QFontInfo, QFontDatabase, QFont
    from PySide6.QtWidgets import QApplication, QPushButton
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.persistence import build_catalog_database
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.ui.chinese import initialize_chinese
    from packages.qt_chinese_resource import TRANSLATION_RELATIVE, TRANSLATION_SHA256
    from packages.ui.dialogs import MessageBox, InputDialog
    application = QApplication([])
    # Offscreen Qt does not enumerate Windows fonts; use installed fonts only.
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("msyh.ttc", "msyhbd.ttc", "seguisym.ttf"):
        if QFontDatabase.addApplicationFont(str(fonts / name)) < 0:
            raise RuntimeError("offscreen Chinese font unavailable")
    application.setFont(QFont("Microsoft YaHei", 9))
    status = initialize_chinese(application)
    if not status["loaded"]:
        raise RuntimeError(str(status))
    errors = []
    sys.excepthook = lambda kind, value, tb: errors.append(f"{kind.__name__}: {value}")
    summary = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)),
               "python": platform.python_version(), "os": platform.platform(), "qt": qVersion(),
               "platform": application.platformName(), "translation": {"loaded": status["loaded"], "relative_path": TRANSLATION_RELATIVE, "sha256": TRANSLATION_SHA256}, "scenes": []}
    def capture(widget, name):
        widget.show()
        for _ in range(4): application.processEvents()
        pixmap = widget.grab()
        if not pixmap.save(str(args.output / f"{name}.png")):
            raise RuntimeError("capture failed")
        summary["scenes"].append({"name": name, "logical_size": [widget.width(), widget.height()],
            "pixels": [pixmap.width(), pixmap.height()], "dpr": widget.devicePixelRatioF(),
            "font": QFontInfo(widget.font()).family(),
            "buttons": [{"text": b.text(), "rect": [b.x(), b.y(), b.width(), b.height()],
                         "enabled": b.isEnabled()} for b in widget.findChildren(QPushButton) if b.isVisible()]})
        widget.hide()
    with tempfile.TemporaryDirectory(prefix="qz-ui-review-") as directory:
        os.environ["LOCALAPPDATA"] = directory
        root = Path(directory)
        catalog = build_catalog_database(DEFAULT_SOURCE_PATH, root / "catalog.sqlite")
        window = create_main_window(AppConfig(catalog_database=catalog, log_directory=root / "logs"))
        if args.accounting:
            from packages.ui.view_models import AppRoute
            from PySide6.QtWidgets import QScrollArea
            window.resize(1440, 1000)
            window.show()
            shell = window.centralWidget()
            shell.navigate(AppRoute.NEW_ACCOUNTING)
            page = shell.pages[AppRoute.NEW_ACCOUNTING]
            capture(window, "accounting-top")
            window.show()
            page.project_unit_toggle.setChecked(True)
            capture(window, "accounting-project")
            window.show()
            page.project_unit_toggle.setChecked(False)
            page._toggle_source_group("fuel")
            scroll = window.findChild(QScrollArea, "mainScrollArea")
            for _ in range(4): application.processEvents()
            scroll.ensureWidgetVisible(page._fuel_rows[0], 0, 20)
            capture(window, "accounting-fuel")
            window.show()
            page._toggle_source_group("electricity")
            for _ in range(4): application.processEvents()
            scroll.ensureWidgetVisible(page._unified_energy_cards["electricity"], 0, 20)
            capture(window, "accounting-electricity")
            summary["callback_errors"] = errors
            (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            window.hide()
            window.deleteLater()
            if errors:
                raise RuntimeError(str(errors))
            return
        capture(window, "home")
        box = MessageBox(window)
        box.setWindowTitle("退出软件")
        box.setText("当前项目有未保存的修改。是否保存后退出？")
        box.setInformativeText("已生成的核算记录不会受影响。")
        box.setIcon(MessageBox.Icon.Question)
        for button, text in ((MessageBox.StandardButton.Save, "保存后退出"),
                             (MessageBox.StandardButton.Discard, "不保存退出"),
                             (MessageBox.StandardButton.Cancel, "取消")):
            box.addButton(button).setText(text)
        box.setDefaultButton(MessageBox.StandardButton.Save)
        box.setEscapeButton(MessageBox.StandardButton.Cancel)
        capture(box, "exit")
        startup = MessageBox()
        startup.setWindowTitle("核算记录数据无法打开")
        startup.setText("核算记录数据库无法创建或安全迁移。请检查记录数据文件后重试。")
        startup.setIcon(MessageBox.Icon.Critical)
        startup.addButton(MessageBox.StandardButton.Ok)
        capture(startup, "startup-error")
        dialog = InputDialog(window)
        dialog.setWindowTitle("修改核算单元名称")
        dialog.setLabelText("核算单元名称")
        dialog.setOkButtonText("保存名称")
        dialog.setTextValue("长中文名称示例：炭素材料生产企业石墨化工序")
        capture(dialog, "input-name")
        window.close()
    summary["callback_errors"] = errors
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors:
        raise RuntimeError(str(errors))


if __name__ == "__main__":
    main()
