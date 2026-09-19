"""Persistence adapters for the canonical catalog and isolated databases."""

from .catalog_repository import CatalogRepositoryError, EmptyCatalogRepository, SQLiteCatalogRepository
from .records_repository import AuditEntry, RecordRepositoryError, SQLiteRecordRepository
from .catalog_builder import build_all_databases, build_catalog_database
from .sqlite import MigrationError, MigrationRunner, initialize_database

__all__ = [
    "AuditEntry",
    "CatalogRepositoryError",
    "EmptyCatalogRepository",
    "MigrationError",
    "MigrationRunner",
    "RecordRepositoryError",
    "SQLiteCatalogRepository",
    "SQLiteRecordRepository",
    "build_all_databases",
    "build_catalog_database",
    "initialize_database",
]