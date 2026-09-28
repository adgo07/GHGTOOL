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
from .carbon_numeric_authority import install_carbon_numeric_authority


# QZC-N01-C: GB/T 32151.34 formula expressions remain in carbon_material.py,
# while this narrow installer supplies their declared Decimal execution context.
install_carbon_numeric_authority()


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
