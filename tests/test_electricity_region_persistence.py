from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from packages.persistence import build_catalog_database, initialize_database
from packages.persistence.catalog_repository import SQLiteCatalogRepository
from packages.reference_data import load_validated_catalog


class ElectricityRegionPersistenceTests(unittest.TestCase):
    def _make_legacy_catalog(self, directory: Path) -> Path:
        path = build_catalog_database(output_path=directory / "catalog.sqlite")
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("ALTER TABLE reference_data_bindings DROP COLUMN region")
            connection.execute("DELETE FROM schema_migrations WHERE version=3")
            connection.execute("UPDATE database_metadata SET value='002' WHERE key='schema_version'")
            connection.commit()
        return path

    def test_optional_region_round_trips_without_changing_factors(self) -> None:
        catalog = load_validated_catalog()
        binding = next(item for item in catalog["reference_data_bindings"]
                       if item["factor_id"] == "electricity_national_average_2023")
        binding["region"] = "全国"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "catalog.json"
            source.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            path = build_catalog_database(source, Path(directory) / "catalog.sqlite")
            repository = SQLiteCatalogRepository(path)
            actual = next(item for item in repository.list_reference_data_bindings()
                          if item.binding_id == binding["binding_id"])
            self.assertEqual(actual.region, "全国")
            factor = next(item for item in repository.list_factors()
                          if item.factor_id == actual.factor_id)
            self.assertEqual(str(factor.value), "0.5306")
            self.assertEqual(factor.parameter_id, "electricity_emission_factor_national")

    def test_read_only_repository_can_read_002_without_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._make_legacy_catalog(Path(directory))
            before = path.read_bytes()
            bindings = SQLiteCatalogRepository(path).list_reference_data_bindings()
            self.assertTrue(bindings)
            self.assertTrue(all(item.region is None for item in bindings))
            self.assertEqual(path.read_bytes(), before)

    def test_region_migration_preserves_existing_binding_rows_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._make_legacy_catalog(Path(directory))
            before = SQLiteCatalogRepository(path).list_reference_data_bindings()
            initialize_database(path, "catalog")
            initialize_database(path, "catalog")
            after = SQLiteCatalogRepository(path).list_reference_data_bindings()
            self.assertEqual(after, before)
            with closing(sqlite3.connect(path)) as connection:
                versions = connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
                self.assertEqual(versions, [(1,), (2,), (3,)])
                metadata = dict(connection.execute("SELECT key,value FROM database_metadata"))
                self.assertEqual(metadata["schema_version"], "003")


if __name__ == "__main__":
    unittest.main()
