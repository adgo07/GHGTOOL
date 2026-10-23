"""One-time Simplified Chinese Qt initialization; no global locale change."""
from __future__ import annotations

import hashlib
from pathlib import Path
import PySide6
from PySide6.QtCore import QTranslator, qVersion
from PySide6.QtWidgets import QApplication

from packages.qt_chinese_resource import TRANSLATION_RELATIVE, TRANSLATION_SHA256, TRANSLATION_QT_VERSION


def translation_path() -> Path:
    return Path(PySide6.__file__).resolve().parent / "translations" / "qtbase_zh_CN.qm"


def load_translator(path: Path) -> QTranslator:
    if qVersion() != TRANSLATION_QT_VERSION:
        raise RuntimeError("Qt 版本与已验证中文资源不匹配")
    if hashlib.sha256(path.read_bytes()).hexdigest() != TRANSLATION_SHA256:
        raise RuntimeError("中文资源校验失败")
    translator = QTranslator()
    if not translator.load(str(path)) or translator.isEmpty():
        raise RuntimeError("中文资源加载失败")
    return translator


def initialize_chinese(application: QApplication) -> dict[str, object]:
    """Keep the translator alive on the application; an error is safe degradation."""
    if hasattr(application, "_qz_chinese_status"):
        return application._qz_chinese_status
    path = translation_path()
    status: dict[str, object] = {"loaded": False, "path": str(path), "qt": qVersion()}
    try:
        translator = load_translator(path)
        if not application.installTranslator(translator):
            raise RuntimeError("中文资源安装失败")
        application._qz_chinese_translator = translator
        status["loaded"] = True
    except (OSError, RuntimeError) as exc:
        status["error"] = str(exc)
        status["error_type"] = "resource_io_error" if isinstance(exc, OSError) else "resource_validation_error"
    application._qz_chinese_status = status
    return status


def report_chinese_failure(application: QApplication, logger) -> None:
    status = initialize_chinese(application)
    if status["loaded"] or getattr(application, "_qz_chinese_notified", False):
        return
    application._qz_chinese_notified = True
    try:
        logger.event("chinese_translation_unavailable", component="desktop_app",
                     outcome="degraded", error_type=str(status.get("error_type", "resource_unavailable")))
    except OSError:
        pass
    from .dialogs import MessageBox
    MessageBox.warning(None, "中文提示资源不可用",
                       "部分系统提示未能加载中文。项目保存功能不受此问题影响，请检查软件资源。")

