from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from packages.persistence import (
    MigrationError,
    MigrationRunner,
    build_all_databases,
    build_catalog_database,
    initialize_database,
)
from packages.reference_data import DEFAULT_SOURCE_PATH, load_validated_catalog
from packages.reference_data.validation import CanonicalValidationError


def _tables(path: Path) -> set[str]:
    connection = sqlite3.connect(path)
    try:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()


def _metadata(path: Path) -> dict[str, str]:
    connection = sqlite3.connect(path)
    try:
        return dict(connection.execute("SELECT key, value FROM database_metadata"))
    finally:
        connection.close()


def _rows(path: Path, table: str, order_column: str) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            f"SELECT * FROM {table} ORDER BY {order_column}"
        ).fetchall()
    finally:
        connection.close()


class PersistenceTests(unittest.TestCase):
    def test_builds_three_physically_separate_databases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = build_all_databases(directory)
            self.assertEqual(set(paths), {"catalog", "user", "records"})
            self.assertTrue(all(path.is_file() for path in paths.values()))

            catalog_tables = _tables(paths["catalog"])
            user_tables = _tables(paths["user"])
            records_tables = _tables(paths["records"])
            self.assertIn("source_documents", catalog_tables)
            self.assertIn("parameter_definitions", catalog_tables)
            self.assertIn("catalog_manifest", catalog_tables)
            self.assertNotIn("user_settings", catalog_tables)
            self.assertIn("user_settings", user_tables)
            self.assertNotIn("source_documents", user_tables)
            self.assertIn("accounting_records", records_tables)
            self.assertIn("audit_log", records_tables)
            self.assertNotIn("source_documents", records_tables)

            self.assertEqual(_metadata(paths["catalog"])["data_version"], "2026.09.11-g02")
            self.assertEqual(_metadata(paths["user"])["data_version"], "not_applicable")
            self.assertEqual(_metadata(paths["records"])["data_version"], "not_applicable")
            connection = sqlite3.connect(paths["catalog"])
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM standard_catalog").fetchone()[0], 9)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM source_documents").fetchone()[0], 12)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM parameter_definitions").fetchone()[0], 6)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM factor_values").fetchone()[0], 6)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM conversion_rules").fetchone()[0], 13)
            finally:
                connection.close()

    def test_migration_is_idempotent_and_preserves_user_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user.sqlite"
            initialize_database(path, "user", app_version="0.1.0")
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    "INSERT INTO user_settings(key, value, updated_at) VALUES (?, ?, ?)",
                    ("window.geometry", "800x600", "2026-09-11T00:00:00+00:00"),
                )
                connection.commit()
            finally:
                connection.close()
            initialize_database(path, "user", app_version="0.2.0")
            connection = sqlite3.connect(path)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0],
                    1,
                )
                self.assertEqual(
                    connection.execute("SELECT value FROM user_settings WHERE key='window.geometry'").fetchone()[0],
                    "800x600",
                )
            finally:
                connection.close()
            self.assertEqual(_metadata(path)["app_version"], "0.2.0")

    def test_rebuilding_catalog_has_same_logical_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.sqlite"
            second = Path(directory) / "second.sqlite"
            build_catalog_database(DEFAULT_SOURCE_PATH, first)
            build_catalog_database(DEFAULT_SOURCE_PATH, second)
            for table, column in (
                ("source_documents", "source_id"),
                ("subject_catalog", "subject_id"),
                ("standard_catalog", "standard_id"),
                ("parameter_definitions", "parameter_id"),
                ("factor_values", "factor_id"),
                ("conversion_rules", "conversion_id"),
            ):
                self.assertEqual(_rows(first, table, column), _rows(second, table, column))

    def test_builder_rejects_invalid_canonical_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            catalog = load_validated_catalog()
            catalog["factors"][0]["unit"] = "not-a-unit"
            source.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(CanonicalValidationError):
                build_catalog_database(source, Path(directory) / "catalog.sqlite")

    def test_migration_runner_rejects_unknown_kind(self) -> None:
        with self.assertRaises(MigrationError):
            MigrationRunner().discover("unknown")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
