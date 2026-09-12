"""Persistence adapters for the canonical catalog and isolated databases."""

from .catalog_repository import CatalogRepositoryError, EmptyCatalogRepository, SQLiteCatalogRepository

__all__ = [
    "CatalogRepositoryError",
    "EmptyCatalogRepository",
    "SQLiteCatalogRepository",
]
"""Persistence primitives for the isolated catalog, user, and records databases."""

from .catalog_builder import build_all_databases, build_catalog_database
from .sqlite import MigrationError, MigrationRunner, initialize_database

__all__ = [
    "MigrationError",
    "MigrationRunner",
    "build_all_databases",
    "build_catalog_database",
    "initialize_database",
]
