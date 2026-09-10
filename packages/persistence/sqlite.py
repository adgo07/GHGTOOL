"""SQLite migration primitives for the three physically isolated databases."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


DatabaseKind = Literal["catalog", "user", "records"]
DATABASE_KINDS = frozenset({"catalog", "user", "records"})
_MIGRATION_NAME = re.compile(r"^(?P<version>[0-9]+)_(?P<name>[a-z0-9][a-z0-9_.-]*)\.sql$")
_DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00+00:00"


class MigrationError(RuntimeError):
    """Raised when a database cannot be migrated safely."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    path: Path
    sql: str


class MigrationRunner:
    """Discover and apply ordered SQL migrations for one database kind."""

    def __init__(self, migrations_root: str | Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.migrations_root = Path(migrations_root or project_root / "migrations")

    def discover(self, kind: DatabaseKind) -> tuple[Migration, ...]:
        self._check_kind(kind)
        directory = self.migrations_root / kind
        if not directory.is_dir():
            raise MigrationError(f"migration directory does not exist: {directory}")
        migrations: list[Migration] = []
        versions: set[int] = set()
        for path in sorted(directory.glob("*.sql")):
            match = _MIGRATION_NAME.fullmatch(path.name)
            if match is None:
                raise MigrationError(f"invalid migration filename: {path.name}")
            version = int(match.group("version"))
            if version in versions:
                raise MigrationError(f"duplicate migration version {version} for {kind}")
            versions.add(version)
            try:
                sql = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise MigrationError(f"cannot read migration {path}: {exc}") from exc
            migrations.append(Migration(version, match.group("name"), path, sql))
        if not migrations:
            raise MigrationError(f"no migrations found for {kind}")
        return tuple(sorted(migrations, key=lambda item: item.version))

    def apply(
        self,
        connection: sqlite3.Connection,
        kind: DatabaseKind,
        *,
        deterministic: bool = True,
    ) -> str:
        self._check_kind(kind)
        connection.execute("PRAGMA foreign_keys = ON")
        migrations = self.discover(kind)
        try:
            applied = {
                int(row[0]): str(row[1])
                for row in connection.execute("SELECT version, name FROM schema_migrations")
            }
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower():
                raise MigrationError(f"cannot inspect migration history: {exc}") from exc
            applied = {}
        for migration in migrations:
            existing_name = applied.get(migration.version)
            if existing_name is not None:
                if existing_name != migration.name:
                    raise MigrationError(
                        f"migration version {migration.version} name mismatch: "
                        f"{existing_name!r} != {migration.name!r}"
                    )
                continue
            timestamp = _DETERMINISTIC_TIMESTAMP
            if not deterministic:
                timestamp = datetime.now(timezone.utc).isoformat()
            try:
                safe_name = migration.name.replace("'", "''")
                safe_timestamp = timestamp.replace("'", "''")
                connection.executescript(
                    "BEGIN;\n"
                    f"{migration.sql}\n"
                    "INSERT INTO schema_migrations(version, name, applied_at) "
                    f"VALUES ({migration.version}, '{safe_name}', '{safe_timestamp}');\n"
                    "COMMIT;"
                )
            except sqlite3.Error as exc:
                connection.rollback()
                raise MigrationError(f"failed migration {migration.path}: {exc}") from exc
        return f"{max(migration.version for migration in migrations):03d}"

    @staticmethod
    def _check_kind(kind: str) -> None:
        if kind not in DATABASE_KINDS:
            raise MigrationError(f"unknown database kind: {kind!r}")


def initialize_database(
    path: str | Path,
    kind: DatabaseKind,
    *,
    app_version: str = "0.1.0",
    data_version: str = "not_applicable",
    deterministic: bool = True,
    runner: MigrationRunner | None = None,
) -> Path:
    """Create or migrate one isolated database and write independent metadata."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    migration_runner = runner or MigrationRunner()
    connection = sqlite3.connect(destination)
    try:
        schema_version = migration_runner.apply(connection, kind, deterministic=deterministic)
        connection.executemany(
            "INSERT INTO database_metadata(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (
                ("app_version", app_version),
                ("schema_version", schema_version),
                ("data_version", data_version),
            ),
        )
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise MigrationError(f"failed to initialize {destination}: {exc}") from exc
    finally:
        connection.close()
    return destination
