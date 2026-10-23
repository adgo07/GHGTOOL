"""PyInstaller entry point and isolated G08 image-resource probe."""
from __future__ import annotations
import json
import argparse
import sys
from pathlib import Path
from apps.carbon_accounting_desktop.app import main


def verify_image_resources() -> dict[str, list[int]]:
    """Decode actual PNG/SVG assets without opening a native window or database."""
    from importlib.resources import files
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication
    if QApplication.instance() is None:
        raise RuntimeError("image probe requires an application context")
    result = {}
    for relative in ("branding/qingzhou_logo.png", "icons/home.svg"):
        image = QPixmap(str(files("resources").joinpath(*relative.split("/"))))
        if image.isNull() or image.width() <= 0 or image.height() <= 0:
            raise RuntimeError(f"standalone image resource failed to load: {relative}")
        result[relative] = [image.width(), image.height()]
    return result


def verify_chinese_resources() -> dict:
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication
    from packages.ui.chinese import initialize_chinese
    from packages.ui.dialogs import MessageBox
    status = initialize_chinese(QApplication.instance())
    if not status["loaded"]:
        raise RuntimeError(f"packaged Chinese initialization failed: {status}")
    if getattr(sys, "frozen", False) and not Path(status["path"]).resolve().is_relative_to(Path(sys._MEIPASS).resolve()):
        raise RuntimeError("translation is outside the actual package")
    translated = QCoreApplication.translate("QPlatformTheme", "Cancel")
    if translated != "取消":
        raise RuntimeError("Qt Cancel translation was not installed")
    box = MessageBox()
    button = box.addButton(MessageBox.StandardButton.Cancel)
    if button.text() != "取消":
        raise RuntimeError("packaged safe Cancel button is not Chinese")
    return {"loaded": True, "qt_cancel": translated, "safe_cancel": button.text()}


def entry() -> int:
    if "--probe-images" in sys.argv[1:] or "--probe-chinese" in sys.argv[1:]:
        parser = argparse.ArgumentParser(description="Isolated packaged PNG/SVG diagnostic")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--probe-images", type=Path)
        group.add_argument("--probe-chinese", type=Path)
        args = parser.parse_args()
        output = args.probe_images or args.probe_chinese
        from PySide6.QtWidgets import QApplication
        application = QApplication.instance() or QApplication([])
        result = verify_image_resources() if args.probe_images else verify_chinese_resources()
        with Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream)
        return 0
    return main()


if __name__ == "__main__":
    raise SystemExit(entry())
