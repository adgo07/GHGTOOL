from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.carbon_accounting_desktop.config import AppConfig
from packages.persistence import MigrationError, initialize_database
from scripts.inspect_release import inspect_release


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class G08DeliveryTests(unittest.TestCase):
    def test_final_version_and_catalog_manifest(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)
        catalog = json.loads(
            (PROJECT_ROOT / "data-source" / "carbon_accounting" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(project["project"]["version"], "1.0.0")
        self.assertEqual(catalog["manifest"]["schema_version"], "1.0.0")
        self.assertEqual(catalog["manifest"]["data_version"], "2026.09.20-g08.1")

    def test_frozen_runtime_resolves_bundled_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            bundled_catalog = bundle / "databases" / "catalog.sqlite"
            bundled_catalog.parent.mkdir(parents=True)
            bundled_catalog.touch()
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", str(bundle), create=True
            ):
                self.assertEqual(AppConfig().resolved_catalog_database(), bundled_catalog)

    def test_unknown_future_migration_version_is_safe_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "user.sqlite"
            initialize_database(database, "user")
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "INSERT INTO schema_migrations(version, name, applied_at) "
                    "VALUES (?, ?, ?)",
                    (999, "future_migration", "2099-01-01T00:00:00+00:00"),
                )
                connection.commit()
            finally:
                connection.close()
            with self.assertRaises(MigrationError):
                initialize_database(database, "user")

    def test_repeated_initialization_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "records.sqlite"
            initialize_database(database, "records")
            initialize_database(database, "records")
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0],
                    2,
                )
                self.assertEqual(
                    dict(connection.execute("SELECT key, value FROM database_metadata"))["app_version"],
                    "1.0.0",
                )
            finally:
                connection.close()

    def test_unopenable_database_fails_as_migration_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_directory = Path(directory) / "records.sqlite"
            database_directory.mkdir()
            with self.assertRaises(MigrationError):
                initialize_database(database_directory, "records")

    def test_release_audit_rejects_user_and_source_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "QingzhouCarbonAccounting.exe").touch()
            (artifact / "records.sqlite").touch()
            (artifact / "source.pdf").touch()
            issues = inspect_release(artifact)
            self.assertTrue(any("unexpected database file" in issue for issue in issues))
            self.assertTrue(any("forbidden source/document/secret file" in issue for issue in issues))

    def test_delivery_workflow_and_docs_exist(self) -> None:
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "windows-ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/build_standalone.py", workflow)
        self.assertIn("scripts/inspect_release.py", workflow)
        self.assertIn("scripts/smoke_standalone.py", workflow)
        self.assertTrue((PROJECT_ROOT / "docs" / "DELIVERY.md").is_file())
        self.assertIn("DELIVERY.md", (PROJECT_ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()