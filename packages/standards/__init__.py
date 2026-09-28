"""Platform-neutral standard catalog read models for G04."""

from .catalog import (
    CatalogRepository,
    CatalogStandardType,
    CatalogStatus,
    CatalogValueCategory,
    FactorCatalogRecord,
    ParameterCatalogRecord,
    ParameterFactorResult,
    ParameterViewMode,
    SourceCatalogRecord,
    StandardCatalogRecord,
    StandardDetail,
    SubjectCatalogRecord,
)
from ._numeric_authority import install_declared_decimal_context

# QZC-N01-C: make the GB/T 32151.34 authoritative calculation entry point
# independent from the caller's ambient Decimal context.  The installer is
# idempotent and does not alter UnitService or the standard formula bodies.
install_declared_decimal_context()

__all__ = [
    "CatalogRepository",
    "CatalogStandardType",
    "CatalogStatus",
    "CatalogValueCategory",
    "FactorCatalogRecord",
    "ParameterCatalogRecord",
    "ParameterFactorResult",
    "ParameterViewMode",
    "SourceCatalogRecord",
    "StandardCatalogRecord",
    "StandardDetail",
    "SubjectCatalogRecord",
]
