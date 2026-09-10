from __future__ import annotations

import unittest
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1] / "packages" / "core"


class DomainDependencyTest(unittest.TestCase):
    def test_domain_sources_have_no_desktop_or_sqlite_imports(self) -> None:
        forbidden_tokens = ("PySide6", "sqlite3", "win32api", "winreg")
        for source_path in CORE_ROOT.rglob("*.py"):
            source = source_path.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                self.assertNotIn(token, source, str(source_path))


if __name__ == "__main__":
    unittest.main()

