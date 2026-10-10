from __future__ import annotations

from contextlib import closing
import os
import json
from hashlib import sha256
import sqlite3
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import ProjectWorkspaceService
from packages.persistence import (
    MigrationError,
    SQLiteProjectWorkspaceRepository,
    SQLiteRecordRepository,
    build_catalog_database,
    initialize_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from scripts.build_standalone import (
    _remove_unpacked_docx_template,
    _validate_approved_template_inputs,
    _write_manifest,
)
from scripts.inspect_release import (
    APPROVED_TEMPLATE_PATH,
    APPROVED_TEMPLATE_SHA256,
    REPORT_LAYOUT_PATH,
    inspect_release,
)
from scripts.verify_release_archive import verify_release_archive

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class G08DeliveryTests(unittest.TestCase):
    def test_project_database_startup_failure_is_explained_to_user(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            logger = unittest.mock.Mock()
            with (
                patch.dict(os.environ, {"LOCALAPPDATA": directory}, clear=False),
                patch("apps.carbon_accounting_desktop.app.QApplication", return_value=object()),
                patch("apps.carbon_accounting_desktop.app.configure_logging", return_value=logger),
                patch(
                    "apps.carbon_accounting_desktop.app.SQLiteProjectWorkspaceRepository",
                    side_effect=MigrationError("projects database is incompatible"),
                ),
                patch("apps.carbon_accounting_desktop.app.QMessageBox.critical") as critical,
            ):
                from apps.carbon_accounting_desktop.app import main

                self.assertEqual(main([]), 1)
            critical.assert_called_once()
            self.assertIn("核算记录数据库未被修改", critical.call_args.args[2])
            logger.close.assert_called_once()

    def test_final_version_and_catalog_manifest(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)
        catalog = json.loads(
            (PROJECT_ROOT / "data-source" / "carbon_accounting" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(project["project"]["version"], "1.1.0")
        self.assertEqual(catalog["manifest"]["schema_version"], "1.1.0")
        self.assertEqual(catalog["manifest"]["data_version"], "2026.10.08-electricity2023.1")
        self.assertEqual(catalog["manifest"]["app_compatibility"], "1.x")
        build_source = (PROJECT_ROOT / "scripts" / "build_standalone.py").read_text(encoding="utf-8")
        self.assertIn('"projects": "003"', build_source)

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
                    4,
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
            (artifact / "user-report.docx").touch()
            runtime_template = artifact / "docx" / "templates" / "default.docx"
            runtime_template.parent.mkdir(parents=True)
            runtime_template.touch()
            issues = inspect_release(artifact)
            self.assertTrue(any("unexpected database file" in issue for issue in issues))
            forbidden_documents = [
                issue for issue in issues if "forbidden source/document/secret file" in issue
            ]
            self.assertTrue(any("source.pdf" in issue for issue in forbidden_documents))
            self.assertTrue(any("user-report.docx" in issue for issue in forbidden_documents))
            self.assertFalse(any("docx/templates/default.docx" in issue for issue in forbidden_documents))

    def test_build_accepts_only_the_exact_approved_template_resource(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            template = source / "resources" / APPROVED_TEMPLATE_PATH.relative_to("resources")
            template.parent.mkdir(parents=True)
            template.write_bytes((PROJECT_ROOT / APPROVED_TEMPLATE_PATH).read_bytes())
            _validate_approved_template_inputs(source)
            self.assertEqual(
                sha256(template.read_bytes()).hexdigest(),
                APPROVED_TEMPLATE_SHA256,
            )
            (template.parent / "user-template.xlsx").write_bytes(b"user content")
            with self.assertRaisesRegex(RuntimeError, "only the approved template"):
                _validate_approved_template_inputs(source)
            (template.parent / "user-template.xlsx").unlink()
            (template.parent / "user-template.xlsm").write_bytes(b"user macro workbook")
            with self.assertRaisesRegex(RuntimeError, "only the approved template"):
                _validate_approved_template_inputs(source)
            (template.parent / "user-template.xlsm").unlink()
            template.write_bytes(b"tampered approved template")
            with self.assertRaisesRegex(RuntimeError, "unexpected hash"):
                _validate_approved_template_inputs(source)

    def test_office_documents_and_unapproved_resources_are_not_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            template = source / APPROVED_TEMPLATE_PATH
            template.parent.mkdir(parents=True)
            template.write_bytes((PROJECT_ROOT / APPROVED_TEMPLATE_PATH).read_bytes())
            for filename in ("user.docm", "user.odt", "user.ods", "user.bin"):
                with self.subTest(filename=filename):
                    unexpected = source / "resources" / filename
                    unexpected.write_bytes(b"user data")
                    with self.assertRaises(RuntimeError):
                        _validate_approved_template_inputs(source)
                    self.assertIn(f"unexpected resource file: resources/{filename}", inspect_release(source))
                    unexpected.unlink()

    def test_release_audit_rejects_template_hash_and_path_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "QingzhouCarbonAccounting.exe").write_bytes(b"standalone-stub")
            build_catalog_database(DEFAULT_SOURCE_PATH, artifact / "databases" / "catalog.sqlite")
            template = artifact / APPROVED_TEMPLATE_PATH
            template.parent.mkdir(parents=True)
            template.write_bytes((PROJECT_ROOT / APPROVED_TEMPLATE_PATH).read_bytes())
            template.write_bytes(b"tampered approved template")
            issues = inspect_release(artifact)
            self.assertIn(
                f"approved Excel template hash mismatch: {APPROVED_TEMPLATE_PATH.as_posix()}",
                issues,
            )
            unexpected = artifact / "resources" / "user-template.xlsx"
            unexpected.write_bytes(b"user workbook")
            issues = inspect_release(artifact)
            self.assertIn(
                "unexpected Excel workbook file: resources/user-template.xlsx",
                issues,
            )
            macro_workbook = artifact / "resources" / "user-template.xlsm"
            macro_workbook.write_bytes(b"user macro workbook")
            issues = inspect_release(artifact)
            self.assertIn(
                "unexpected Excel workbook file: resources/user-template.xlsm",
                issues,
            )

    def test_release_artifact_keeps_rpt02_layout_with_exact_exb01_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            (artifact / "QingzhouCarbonAccounting.exe").write_bytes(b"standalone-stub")
            build_catalog_database(
                DEFAULT_SOURCE_PATH,
                artifact / "databases" / "catalog.sqlite",
            )
            template = artifact / APPROVED_TEMPLATE_PATH
            template.parent.mkdir(parents=True)
            template.write_bytes((PROJECT_ROOT / APPROVED_TEMPLATE_PATH).read_bytes())
            layout_path = artifact / REPORT_LAYOUT_PATH
            layout_path.parent.mkdir(parents=True)
            source_layout_path = PROJECT_ROOT / REPORT_LAYOUT_PATH
            layout_path.write_bytes(source_layout_path.read_bytes())

            with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
                package_data = tomllib.load(stream)["tool"]["setuptools"]["package-data"]
            self.assertIn("*.json", package_data["packages.application.reporting"])

            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            source_layout = json.loads(source_layout_path.read_text(encoding="utf-8"))
            self.assertEqual(layout, source_layout)
            self.assertEqual(layout["version"], "2.0.0")
            self.assertEqual(
                layout["approved_sha256"],
                "c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4",
            )
            self.assertEqual(
                layout["formula_free_sha256"],
                "78042e02b57701cfcb3b4a3fb86dbb6ec8e4fa66ec74cfed768433153d5fdc7e",
            )
            self.assertEqual(set(layout["tables"]), {f"b{index}" for index in range(1, 10)})
            self.assertEqual(
                sha256(template.read_bytes()).hexdigest(),
                APPROVED_TEMPLATE_SHA256,
            )

            _write_manifest(
                artifact,
                app_version="1.1.0",
                catalog_meta={
                    "schema_version": "1.1.0",
                    "data_version": "2026.10.08-electricity2023.1",
                },
            )
            manifest = json.loads((artifact / "build-manifest.json").read_text(encoding="utf-8"))
            manifest_paths = {entry["path"] for entry in manifest["files"]}
            self.assertIn(REPORT_LAYOUT_PATH.as_posix(), manifest_paths)
            self.assertIn(APPROVED_TEMPLATE_PATH.as_posix(), manifest_paths)
            self.assertEqual(inspect_release(artifact), ())
            self.assertFalse((artifact / "docs").exists())

            original_workbook = artifact / "docs" / layout["approved_template"]
            original_workbook.parent.mkdir(parents=True)
            original_workbook.write_bytes(b"RPT02 original approved workbook")
            sample_report = artifact / "docs" / "rpt02" / "samples" / "sample.docx"
            sample_report.parent.mkdir(parents=True)
            sample_report.write_bytes(b"RPT02 acceptance sample")
            _write_manifest(
                artifact,
                app_version="1.1.0",
                catalog_meta={
                    "schema_version": "1.1.0",
                    "data_version": "2026.10.08-electricity2023.1",
                },
            )
            issues = inspect_release(artifact)
            self.assertIn(
                f"unexpected Excel workbook file: docs/{layout['approved_template']}",
                issues,
            )
            self.assertIn(
                "forbidden source/document/secret file: docs/rpt02/samples/sample.docx",
                issues,
            )

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
            approved_template = artifact / APPROVED_TEMPLATE_PATH
            approved_template.parent.mkdir(parents=True, exist_ok=True)
            approved_template.write_bytes((PROJECT_ROOT / APPROVED_TEMPLATE_PATH).read_bytes())
            reporting_layout = artifact / REPORT_LAYOUT_PATH
            reporting_layout.parent.mkdir(parents=True, exist_ok=True)
            reporting_layout.write_bytes((PROJECT_ROOT / REPORT_LAYOUT_PATH).read_bytes())
            templates = artifact / "docx" / "templates"
            templates.mkdir(parents=True)
            (templates / "default.docx").write_bytes(b"runtime-template")
            unpacked_template = templates / "default-docx-template" / "_rels"
            unpacked_template.mkdir(parents=True)
            (unpacked_template / ".rels").write_text("redundant", encoding="utf-8")
            _remove_unpacked_docx_template(artifact)
            self.assertFalse((templates / "default-docx-template").exists())
            self.assertTrue((templates / "default.docx").is_file())
            with patch("scripts.build_standalone._source_commit", return_value="checkout-sha"), patch.dict(os.environ, {"QZ_PR_HEAD_SHA": "pr-head-sha", "QZ_TESTED_MERGE_SHA": "tested-merge-sha"}, clear=False):
                _write_manifest(
                    artifact,
                    app_version="1.1.0",
                    catalog_meta={
                        "schema_version": "1.1.0",
                        "data_version": "2026.10.08-electricity2023.1",
                    },
                )
            manifest = json.loads((artifact / "build-manifest.json").read_text(encoding="utf-8"))
            manifest_paths = {entry["path"] for entry in manifest["files"]}
            self.assertNotIn("migrations/.gitkeep", manifest_paths)
            self.assertNotIn("resources/icons/.gitkeep", manifest_paths)
            self.assertIn(APPROVED_TEMPLATE_PATH.as_posix(), manifest_paths)
            self.assertIn(REPORT_LAYOUT_PATH.as_posix(), manifest_paths)
            template_entry = next(
                entry for entry in manifest["files"]
                if entry["path"] == APPROVED_TEMPLATE_PATH.as_posix()
            )
            self.assertEqual(template_entry["sha256"], APPROVED_TEMPLATE_SHA256)
            self.assertEqual(manifest["source_commit"], "checkout-sha")
            self.assertEqual(manifest["pr_head_sha"], "pr-head-sha")
            self.assertEqual(manifest["tested_merge_sha"], "tested-merge-sha")
            with closing(sqlite3.connect(catalog_path)) as connection:
                catalog_schema_version = connection.execute(
                    "SELECT value FROM database_metadata WHERE key='schema_version'"
                ).fetchone()[0]
            self.assertEqual(manifest["database_schema_versions"]["catalog"], catalog_schema_version)
            self.assertGreater(verify_release_archive(artifact), 0)
            manifest["database_schema_versions"]["catalog"] = "001"
            (artifact / "build-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn(
                "manifest catalog database schema version does not match packaged database",
                inspect_release(artifact),
            )

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
                self.assertFalse(config.resolved_projects_database().exists())
                first_project_service = ProjectWorkspaceService(
                    SQLiteProjectWorkspaceRepository(config.resolved_projects_database())
                )
                first_window = create_main_window(config, project_service=first_project_service)
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
                self.assertTrue(config.resolved_projects_database().is_file())
                with patch(
                    "packages.ui.carbon_material_page.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Discard,
                ):
                    first_window.close()
                first_window.deleteLater()
                application.processEvents()

                second_project_service = ProjectWorkspaceService(
                    SQLiteProjectWorkspaceRepository(config.resolved_projects_database())
                )
                second_window = create_main_window(config, project_service=second_project_service)
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
