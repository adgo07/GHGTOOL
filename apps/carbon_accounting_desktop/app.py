"""G00 minimal PySide6 application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from .config import AppConfig
from .logging_config import configure_logging


def create_main_window(config: AppConfig | None = None) -> QMainWindow:
    """Create the G00 placeholder window; no business page is implemented."""

    app_config = config or AppConfig()
    window = QMainWindow()
    window.setObjectName("g00MainWindow")
    window.setWindowTitle(app_config.app_name)
    window.setMinimumSize(800, 480)
    window.resize(960, 600)

    content = QWidget(window)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(32, 32, 32, 32)
    layout.setSpacing(16)

    logo_label = QLabel(content)
    logo_label.setObjectName("brandLogo")
    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo = QPixmap(str(app_config.logo_path()))
    if not logo.isNull():
        logo_label.setPixmap(
            logo.scaled(
                420,
                110,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    else:
        logo_label.setText("青舟节能")
    layout.addWidget(logo_label)

    title_label = QLabel("G00 工程骨架", content)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setObjectName("skeletonTitle")
    layout.addWidget(title_label)

    description_label = QLabel(
        "最小可启动窗口已就绪。业务页面与核算功能将按阶段交接基线实施。",
        content,
    )
    description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    description_label.setWordWrap(True)
    description_label.setObjectName("skeletonDescription")
    layout.addWidget(description_label)
    layout.addStretch(1)

    window.setCentralWidget(content)
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""

    qt_args = list(argv) if argv is not None else sys.argv
    application = QApplication(qt_args)
    config = AppConfig()
    logger = configure_logging(config.resolved_log_directory(), config.app_version)
    window = create_main_window(config)
    window.show()
    logger.event("application_started", component="desktop_app", outcome="started")
    exit_code = application.exec()
    logger.event("application_exited", component="desktop_app", outcome="normal")
    logger.close()
    return exit_code
