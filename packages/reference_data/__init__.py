"""Reserved reference-data package for later Goals."""
"""Canonical reference-data loading and validation."""

from .validation import (
    DEFAULT_SCHEMA_PATH,
    DEFAULT_SOURCE_PATH,
    CanonicalValidationError,
    load_validated_catalog,
    validate_catalog,
)

__all__ = [
    "DEFAULT_SCHEMA_PATH",
    "DEFAULT_SOURCE_PATH",
    "CanonicalValidationError",
    "load_validated_catalog",
    "validate_catalog",
]
