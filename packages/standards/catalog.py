"""Platform-neutral catalog read models and repository contract for G04."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Protocol

from packages.core.models import OfficialStatus, ParameterType, ReviewStatus, SourceType, ValueType


class CatalogStandardType(str, Enum):
    """Publicly queryable standard categories stored by the catalog."""

    COMMON_RULES = "COMMON_RULES"
    INDUSTRY = "INDUSTRY"


class CatalogStatus(str, Enum):
    """Status values exposed by the standard-library filters."""

    ALL = "ALL"
    CURRENT = "CURRENT"
    UPCOMING = "UPCOMING"
    ABOLISHED = "ABOLISHED"
    UNKNOWN = "UNKNOWN"


class ParameterViewMode(str, Enum):
    """The two supported primary views over the same catalog data."""

    BY_SUBJECT = "BY_SUBJECT"
    BY_SOURCE = "BY_SOURCE"


@dataclass(frozen=True, slots=True)
class SourceCatalogRecord:
    source_id: str
    source_type: SourceType
    document_no: str
    document_name: str
    publisher: str
    publication_date: date
    effective_from: date | None
    effective_to: date | None
    region: str
    version: str
    official_url: str | None
    review_status: ReviewStatus
    notes: str


@dataclass(frozen=True, slots=True)
class SubjectCatalogRecord:
    subject_id: str
    subject_type: str
    name: str
    aliases: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class StandardCatalogRecord:
    standard_id: str
    standard_number: str
    standard_name: str
    standard_type: CatalogStandardType
    version: str
    official_status: OfficialStatus
    publication_date: date
    implementation_date: date
    ics: str
    ccs: str
    issuing_authority: str
    competent_authority: str
    technical_committee: str
    official_source_id: str
    official_source_url: str | None
    base_standard_ids: tuple[str, ...]
    parameter_refs: tuple[str, ...]
    emission_source_refs: tuple[str, ...]
    calculation_status: str
    notes: str
    abolition_date: date | None = None


@dataclass(frozen=True, slots=True)
class ParameterCatalogRecord:
    parameter_id: str
    parameter_type: ParameterType
    name: str
    canonical_unit: str
    subject_id: str
    source_id: str
    source_location: str
    review_status: ReviewStatus
    applicable_standard_ids: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class FactorCatalogRecord:
    factor_id: str
    parameter_id: str
    subject_id: str
    value: Decimal
    unit: str
    source_value: Decimal
    source_unit: str
    normalized_value: Decimal
    normalized_unit: str
    source_id: str
    source_location: str
    factor_year: int
    valid_from: date | None
    valid_to: date | None
    value_type: ValueType
    review_status: ReviewStatus
    applicable_standard_ids: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class StandardDetail:
    standard: StandardCatalogRecord
    status: CatalogStatus
    source: SourceCatalogRecord | None
    base_standards: tuple[StandardCatalogRecord, ...]
    parameters: tuple[ParameterCatalogRecord, ...]
    factors: tuple[FactorCatalogRecord, ...]


@dataclass(frozen=True, slots=True)
class ParameterFactorResult:
    parameter: ParameterCatalogRecord
    factor: FactorCatalogRecord | None
    subject: SubjectCatalogRecord
    source: SourceCatalogRecord | None


class CatalogRepository(Protocol):
    """Read-only repository used by the G04 application query service."""

    def list_standards(self) -> Sequence[StandardCatalogRecord]:
        """Return all immutable standard versions."""

    def list_sources(self) -> Sequence[SourceCatalogRecord]:
        """Return all source documents."""

    def list_subjects(self) -> Sequence[SubjectCatalogRecord]:
        """Return all catalog subjects and aliases."""

    def list_parameters(self) -> Sequence[ParameterCatalogRecord]:
        """Return all parameter definitions."""

    def list_factors(self) -> Sequence[FactorCatalogRecord]:
        """Return all immutable factor values."""
