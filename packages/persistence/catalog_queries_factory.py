"""Infrastructure composition for read-only catalog query services."""

from __future__ import annotations

from pathlib import Path

from packages.application.catalog_queries import CatalogQueryService
from packages.persistence.catalog_repository import CatalogRepositoryError, SQLiteCatalogRepository
from packages.standards.catalog import EmptyCatalogRepository


def create_catalog_query_service(path: str | Path | None) -> CatalogQueryService:
    """Create a query service, degrading safely when the optional catalog is absent."""
    if path is None:
        return CatalogQueryService(EmptyCatalogRepository())
    try:
        repository = SQLiteCatalogRepository(path)
    except CatalogRepositoryError:
        return CatalogQueryService(EmptyCatalogRepository())
    return CatalogQueryService(repository)


__all__ = ["create_catalog_query_service"]
