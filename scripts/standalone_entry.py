"""PyInstaller entry point and isolated G08 image-resource probe."""
from __future__ import annotations
import json
import os
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


def entry() -> int:
    output = os.environ.get("QZ_G08_IMAGE_PROBE_PATH")
    if output:
        from PySide6.QtWidgets import QApplication
        application = QApplication.instance() or QApplication([])
        result = verify_image_resources()
        with Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream)
        return 0
    return main()


if __name__ == "__main__":
    raise SystemExit(entry())
