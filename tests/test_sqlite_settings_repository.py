from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from packages.core.models import SettingEntry
from packages.ui.export_location import ExportLocationService
from packages.core.repositories import SettingsRepository
from packages.persistence import SQLiteSettingsRepository, initialize_database


class SQLiteSettingsRepositoryTests(unittest.TestCase):
    def test_reads_and_updates_existing_user_settings_table(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "user.sqlite"
            initialize_database(database, "user")
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "INSERT INTO user_settings(key, value, updated_at) VALUES (?, ?, ?)",
                    ("window.geometry", "800x600", "2026-10-14T00:00:00+00:00"),
                )
                connection.commit()
            finally:
                connection.close()

            repository = SQLiteSettingsRepository(database)
            self.assertIsInstance(repository, SettingsRepository)
            existing = repository.load()
            self.assertEqual(existing.entries, (SettingEntry("window.geometry", "800x600"),))
            service = ExportLocationService(
                repository,
                documents_location_provider=lambda: Path(directory) / "Documents",
            )
            service.set_preferred_directory(Path(directory) / "Exports")

            loaded = {entry.key: entry.value for entry in repository.load().entries}
            self.assertEqual(loaded["window.geometry"], "800x600")
            self.assertEqual(loaded["export.directory"], str(Path(directory) / "Exports"))
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='user_settings'"
                    ).fetchone()[0],
                    1,
                )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
