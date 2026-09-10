from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class G00LayoutTest(unittest.TestCase):
    def test_required_skeleton_directories_exist(self) -> None:
        required_directories = (
            "apps/carbon_accounting_desktop",
            "packages/core",
            "packages/ui",
            "packages/standards",
            "packages/reference_data",
            "packages/persistence",
            "packages/audit",
            "specs/common",
            "specs/carbon_accounting",
            "data-source/common",
            "data-source/carbon_accounting",
            "resources/branding",
            "resources/icons",
            "migrations",
            "scripts",
            "build",
            "docs",
            "tests",
        )
        for relative_path in required_directories:
            self.assertTrue((PROJECT_ROOT / relative_path).is_dir(), relative_path)

    def test_core_skeleton_has_no_ui_or_database_dependency(self) -> None:
        core_files = (PROJECT_ROOT / "packages" / "core").rglob("*.py")
        for source_path in core_files:
            source = source_path.read_text(encoding="utf-8")
            self.assertNotIn("PySide6", source)
            self.assertNotIn("sqlite3", source)


if __name__ == "__main__":
    unittest.main()

