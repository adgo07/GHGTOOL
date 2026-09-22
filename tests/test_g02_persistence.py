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
            self.assertNotIn("standard_scopes", catalog_tables)
            self.assertNotIn("user_settings", catalog_tables)
            self.assertIn("user_settings", user_tables)
            self.assertNotIn("source_documents", user_tables)
            self.assertIn("accounting_records", records_tables)
            self.assertIn("audit_log", records_tables)
            self.assertNotIn("source_documents", records_tables)

            self.assertEqual(_metadata(paths["catalog"])["schema_version"], "001")
            self.assertEqual(_metadata(paths["catalog"])["data_version"], "2026.09.22-catui01.1")
            self.assertEqual(_metadata(paths["user"])["data_version"], "not_applicable")
            self.assertEqual(_metadata(paths["records"])["data_version"], "not_applicable")
            connection = sqlite3.connect(paths["catalog"])
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM standard_catalog").fetchone()[0], 9)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM source_documents").fetchone()[0], 12)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM parameter_definitions").fetchone()[0], 7)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM factor_values").fetchone()[0], 7)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM conversion_rules").fetchone()[0], 13)
            finally:
                connection.close()

    def test_catalog_sqlite_uses_g01_enums_and_distinguished_responsibilities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = build_catalog_database(DEFAULT_SOURCE_PATH, Path(directory) / "catalog.sqlite")
            connection = sqlite3.connect(path)
            try:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(standard_catalog)")
                }
                self.assertIn("official_status", columns)
                self.assertIn("issuing_authority", columns)
                self.assertIn("competent_authority", columns)
                self.assertIn("technical_committee", columns)
                self.assertNotIn("status", columns)
                self.assertNotIn("authority", columns)

                standard = connection.execute(
                    "SELECT official_status, issuing_authority, competent_authority, "
                    "technical_committee, parameter_refs_json, notes "
                    "FROM standard_catalog WHERE standard_id=?",
                    ("gbt_32151_34_2024",),
                ).fetchone()
                self.assertEqual(standard[0], "ACTIVE")
                self.assertEqual(standard[1], "国家市场监督管理总局、国家标准化管理委员会")
                self.assertEqual(standard[2], "中国钢铁工业协会")
                self.assertEqual(standard[3], "中国钢铁工业协会")
                self.assertEqual(standard[5], "适用于炭素材料生产企业温室气体排放量的核算。")
                refs = json.loads(standard[4])
                self.assertIn("natural_gas_lhv", refs)
                self.assertIn("electricity_emission_factor_nonfossil", refs)

                nonfossil = connection.execute(
                    "SELECT parameter_id, source_id, source_location, value, unit, "
                    "value_type, factor_year, valid_from "
                    "FROM factor_values WHERE factor_id=?",
                    ("electricity_nonfossil_zero_gbt32151_34_2024",),
                ).fetchone()
                self.assertEqual(nonfossil[0], "electricity_emission_factor_nonfossil")
                self.assertEqual(nonfossil[1], "SRC-32151-34-2024")
                self.assertEqual(
                    nonfossil[2],
                    "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22",
                )
                self.assertEqual(nonfossil[3:6], ("0", "tCO₂/MWh", "STANDARD_SPECIFIED"))
                self.assertEqual(nonfossil[6:], (2024, "2025-03-01"))
                source = connection.execute(
                    "SELECT source_type, publisher FROM source_documents WHERE source_id=?",
                    ("SRC-ELEC-2023-47",),
                ).fetchone()
                self.assertEqual(source, ("GOVERNMENT_PUBLICATION", "生态环境部、国家统计局"))

                heat = connection.execute(
                    "SELECT source_id, source_location, value, value_type FROM factor_values WHERE factor_id=?",
                    ("heat_default_2025",),
                ).fetchone()
                self.assertEqual(heat[0], "SRC-32150-2025")
                self.assertIn("7.5.6", heat[1])
                self.assertIn("7.5.7", heat[1])
                self.assertEqual(heat[2:], ("0.11", "STANDARD_DEFAULT"))

                ddl = "\n".join(
                    row[0]
                    for row in connection.execute(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
                    )
                )
                for enum_value in (
                    "GOVERNMENT_PUBLICATION",
                    "SCIENTIFIC_REFERENCE",
                    "ABOLISHED",
                    "DEPRECATED",
                    "STANDARD_DEFAULT",
                    "GOVERNMENT_PUBLISHED",
                ):
                    self.assertIn(enum_value, ddl)
                for legacy_value in ("OFFICIAL_NOTICE", "SCIENTIFIC_REPORT", "RETIRED", "PENDING_REVIEW"):
                    self.assertNotIn(legacy_value, ddl)
            finally:
                connection.close()

    def test_migration_is_idempotent_and_preserves_user_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user.sqlite"
            initialize_database(path, "user", app_version="1.0.0")
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
