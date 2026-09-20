from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from apps.carbon_accounting_desktop.logging_config import configure_logging


class StructuredLoggingTest(unittest.TestCase):
    def test_only_safe_operational_tokens_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            logger = configure_logging(Path(directory), app_version="1.0.0")
            try:
                logger.event(
                    "application_started",
                    component="desktop_app",
                    outcome="started",
                    enterprise_name="不应写入日志的企业",
                    activity_data="123.45",
                    license_key="SECRET-KEY",
                )

                payload = json.loads(logger.log_path.read_text(encoding="utf-8"))
            finally:
                logger.close()

        self.assertEqual(payload["event"], "application_started")
        self.assertEqual(payload["component"], "desktop_app")
        self.assertEqual(payload["outcome"], "started")
        self.assertNotIn("enterprise_name", payload)
        self.assertNotIn("activity_data", payload)
        self.assertNotIn("license_key", payload)
        self.assertNotIn("不应写入日志的企业", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("123.45", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("SECRET-KEY", json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
