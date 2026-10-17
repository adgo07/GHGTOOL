"""SQLite adapter for user settings stored in the existing user.sqlite database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from packages.core.models import SettingEntry, Settings

from .sqlite import MigrationError, initialize_database


class SettingsRepositoryError(RuntimeError):
    """Raised when user settings cannot be safely read or written."""


class SQLiteSettingsRepository:
    """Persist settings in the existing user_settings table."""

    def __init__(self, path: str | Path, *, app_version: str = "1.1.0") -> None:
        try:
            self.path = initialize_database(
                path,
                "user",
                app_version=app_version,
                data_version="not_applicable",
                deterministic=False,
            )
        except (MigrationError, OSError) as exc:
            raise SettingsRepositoryError(f"cannot initialize user settings database: {exc}") from exc

    def load(self) -> Settings:
        try:
            connection = sqlite3.connect(self.path)
            try:
                rows = connection.execute(
                    "SELECT key, value FROM user_settings ORDER BY key"
                ).fetchall()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise SettingsRepositoryError("cannot read user settings") from exc
        return Settings(
            settings_id="user.settings",
            entries=tuple(SettingEntry(str(key), str(value)) for key, value in rows),
        )

    def save(self, settings: Settings) -> None:
        updated_at = datetime.now(timezone.utc).isoformat()
        try:
            connection = sqlite3.connect(self.path)
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.executemany(
                    "INSERT INTO user_settings(key, value, updated_at) VALUES (?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET "
                    "value=excluded.value, updated_at=excluded.updated_at",
                    ((entry.key, entry.value, updated_at) for entry in settings.entries),
                )
                connection.commit()
            except sqlite3.Error:
                connection.rollback()
                raise
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise SettingsRepositoryError("cannot save user settings") from exc


__all__ = ["SQLiteSettingsRepository", "SettingsRepositoryError"]
