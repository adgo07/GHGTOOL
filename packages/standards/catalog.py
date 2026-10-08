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


class CatalogValueCategory(str, Enum):
    """Source-declared display category for coexisting catalog values."""

    RECOMMENDED = "RECOMMENDED"
    OTHER_APPLICABLE = "OTHER_APPLICABLE"
    HISTORICAL = "HISTORICAL"


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
class SourceTableColumnRecord:
    key: str
    label: str
    parameter_type: ParameterType | None = None


@dataclass(frozen=True, slots=True)
class SourceTableCatalogRecord:
    source_table_id: str
    source_id: str
    display_number: str
    title: str
    source_location: str
    layout: str
    columns: tuple[SourceTableColumnRecord, ...]
    provider_id: str | None
    notes: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class ReferenceDataAssetCatalogRecord:
    asset_id: str
    asset_version: str
    parameter_id: str
    subject_id: str
    value: Decimal
    unit: str
    source_value: Decimal
    source_unit: str
    normalized_value: Decimal
    normalized_unit: str
    value_type: ValueType
    notes: str


@dataclass(frozen=True, slots=True)
class ReferenceDataBindingCatalogRecord:
    binding_id: str
    asset_id: str
    source_table_id: str
    binding_type: str
    factor_id: str | None
    source_location: str
    applicable_standard_ids: tuple[str, ...]
    factor_year: int
    valid_from: date | None
    valid_to: date | None
    review_status: ReviewStatus
    notes: str
    region: str | None = None


@dataclass(frozen=True, slots=True)
class ConversionRuleCatalogRecord:
    conversion_id: str
    from_unit: str
    to_unit: str
    multiplier: Decimal
    offset: Decimal
    source_id: str
    source_location: str
    review_status: ReviewStatus
    notes: str


@dataclass(frozen=True, slots=True)
class ReferenceLibrarySearchResult:
    result_type: str
    key: str
    title: str
    subtitle: str
    value_text: str
    unit: str
    asset: ReferenceDataAssetCatalogRecord | None = None
    table: SourceTableCatalogRecord | None = None
    source: SourceCatalogRecord | None = None
    standard: StandardCatalogRecord | None = None
    bindings: tuple[ReferenceDataBindingCatalogRecord, ...] = ()


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

    def list_source_tables(self) -> Sequence[SourceTableCatalogRecord]:
        """Return the source-declared display tables and their layouts."""

    def list_reference_data_assets(self) -> Sequence[ReferenceDataAssetCatalogRecord]:
        """Return immutable shared values independent of their source bindings."""

    def list_reference_data_bindings(self) -> Sequence[ReferenceDataBindingCatalogRecord]:
        """Return all source- and locator-specific bindings for shared values."""

    def list_conversion_rules(self) -> Sequence[ConversionRuleCatalogRecord]:
        """Return source-traceable unit conversion rules for library display."""

class EmptyCatalogRepository(CatalogRepository):
    """Pure empty read adapter used before a catalog is installed."""

    def list_standards(self) -> tuple[StandardCatalogRecord, ...]:
        return ()

    def list_sources(self) -> tuple[SourceCatalogRecord, ...]:
        return ()

    def list_subjects(self) -> tuple[SubjectCatalogRecord, ...]:
        return ()

    def list_parameters(self) -> tuple[ParameterCatalogRecord, ...]:
        return ()

    def list_factors(self) -> tuple[FactorCatalogRecord, ...]:
        return ()

    def list_source_tables(self) -> tuple[SourceTableCatalogRecord, ...]:
        return ()

    def list_reference_data_assets(self) -> tuple[ReferenceDataAssetCatalogRecord, ...]:
        return ()

    def list_reference_data_bindings(self) -> tuple[ReferenceDataBindingCatalogRecord, ...]:
        return ()

    def list_conversion_rules(self) -> tuple[ConversionRuleCatalogRecord, ...]:
        return ()
