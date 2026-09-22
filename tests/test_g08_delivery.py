from __future__ import annotations

import os
import json
import sqlite3
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.persistence import MigrationError, SQLiteRecordRepository, build_catalog_database, initialize_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from scripts.build_standalone import _write_manifest
from scripts.inspect_release import inspect_release
from scripts.verify_release_archive import verify_release_archive

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
        self.assertEqual(project["project"]["version"], "1.1.0")
        self.assertEqual(catalog["manifest"]["schema_version"], "1.0.0")
        self.assertEqual(catalog["manifest"]["data_version"], "2026.09.22-catui01.1")
        self.assertEqual(catalog["manifest"]["app_compatibility"], "1.x")

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
                    "1.1.0",
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

    def test_uploaded_archive_preserves_manifest_file_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "QingzhouCarbonAccounting.exe").write_bytes(b"standalone-stub")
            catalog_path = artifact / "databases" / "catalog.sqlite"
            build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path, app_version="1.1.0")
            (artifact / "migrations").mkdir()
            (artifact / "migrations" / ".gitkeep").write_text("", encoding="utf-8")
            (artifact / "resources" / "icons").mkdir(parents=True)
            (artifact / "resources" / "icons" / ".gitkeep").write_text("", encoding="utf-8")
            with patch("scripts.build_standalone._source_commit", return_value="checkout-sha"), patch.dict(os.environ, {"QZ_PR_HEAD_SHA": "pr-head-sha", "QZ_TESTED_MERGE_SHA": "tested-merge-sha"}, clear=False):
                _write_manifest(
                    artifact,
                    app_version="1.1.0",
                    catalog_meta={
                        "schema_version": "1.0.0",
                        "data_version": "2026.09.20-g08.1",
                    },
                )
            manifest = json.loads((artifact / "build-manifest.json").read_text(encoding="utf-8"))
            manifest_paths = {entry["path"] for entry in manifest["files"]}
            self.assertNotIn("migrations/.gitkeep", manifest_paths)
            self.assertNotIn("resources/icons/.gitkeep", manifest_paths)
            self.assertEqual(manifest["source_commit"], "checkout-sha")
            self.assertEqual(manifest["pr_head_sha"], "pr-head-sha")
            self.assertEqual(manifest["tested_merge_sha"], "tested-merge-sha")
            self.assertGreater(verify_release_archive(artifact), 0)

    def test_fresh_user_gui_calculate_and_reload_record_end_to_end(self) -> None:
        application = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = build_catalog_database(DEFAULT_SOURCE_PATH, root / "catalog.sqlite")
            local_app_data = root / "localappdata"
            with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}, clear=False):
                config = AppConfig(
                    catalog_database=catalog_path,
                    log_directory=root / "logs",
                )
                self.assertFalse(config.resolved_records_database().exists())
                first_window = create_main_window(config)
                first_window.show()
                application.processEvents()
                first_shell = first_window.centralWidget()
                first_shell.navigate(AppRoute.NEW_ACCOUNTING)
                page = first_shell.pages[AppRoute.NEW_ACCOUNTING]
                page.enterprise_name.setText("G08 集成企业")
                page.boundary_confirmed.setChecked(True)
                page.calculate_button.click()
                application.processEvents()
                repository = SQLiteRecordRepository(config.resolved_records_database())
                records = repository.list_all()
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0].input_snapshot.enterprise_name, "G08 集成企业")
                self.assertIn("tCO₂", page.result_total.text())
                first_window.close()
                first_window.deleteLater()
                application.processEvents()

                second_window = create_main_window(config)
                second_window.show()
                application.processEvents()
                second_shell = second_window.centralWidget()
                records_page = second_shell.pages[AppRoute.RECORDS]
                self.assertEqual(records_page.record_list.count(), 1)
                self.assertIn("G08 集成企业", records_page.detail_text.toPlainText())
                self.assertIn("标准版本：2024", records_page.detail_text.toPlainText())
                second_window.close()
                second_window.deleteLater()
                application.processEvents()
    def test_delivery_workflow_and_docs_exist(self) -> None:
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "windows-ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/build_standalone.py", workflow)
        self.assertIn("scripts/inspect_release.py", workflow)
        self.assertIn("scripts/smoke_standalone.py", workflow)
        self.assertIn("scripts/verify_release_archive.py", workflow)
        self.assertIn("windows-python-312-merge-integration", workflow)
        self.assertIn("QZ_PR_HEAD_SHA", workflow)
        self.assertIn("include-hidden-files: false", workflow)
        self.assertTrue((PROJECT_ROOT / "docs" / "DELIVERY.md").is_file())
        self.assertIn("DELIVERY.md", (PROJECT_ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
