from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.standards.carbon_material import InMemoryRecordRepository


class MinimalApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_window_loads_logo_and_exits_normally(self) -> None:
        window = create_main_window(AppConfig(log_directory=Path("tests")), record_repository=InMemoryRecordRepository())
        logo_label = window.findChild(QLabel, "brandLogo")
        self.assertIsNotNone(logo_label)
        assert logo_label is not None
        self.assertFalse(logo_label.pixmap().isNull())

        window.show()
        self.application.processEvents()
        QTimer.singleShot(0, self.application.quit)
        exit_code = self.application.exec()
        self.assertEqual(exit_code, 0)
        window.close()


if __name__ == "__main__":
    unittest.main()

