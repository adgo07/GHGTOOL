"""Immutable, platform-independent domain models for G01."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .decimal_policy import DecimalPolicy
from .errors import DomainValidationError, ValidationProblem, contains_errors, contains_warnings


_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
_DEFAULT_POLICY = DecimalPolicy()


def _require_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise DomainValidationError(f"{field_name} must be a stable identifier")
    return value


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} is required")
    return value


def _normalize_tuple(values: tuple | list | None, field_name: str) -> tuple:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise DomainValidationError(f"{field_name} must be a sequence, not text")
    return tuple(values)


def _normalize_decimal(value: str | Decimal | int, field_name: str) -> Decimal:
    try:
        return _DEFAULT_POLICY.parse(value)
    except ValueError as exc:
        raise DomainValidationError(f"{field_name} is not a valid decimal") from exc


def _require_unit(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise DomainValidationError("unit is required")
    return value.strip()


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware")
    return value


class OfficialStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UPCOMING = "UPCOMING"
    ABOLISHED = "ABOLISHED"
    UNKNOWN = "UNKNOWN"


class SourceType(str, Enum):
    OFFICIAL_STANDARD = "OFFICIAL_STANDARD"
    GOVERNMENT_PUBLICATION = "GOVERNMENT_PUBLICATION"
    SCIENTIFIC_REFERENCE = "SCIENTIFIC_REFERENCE"
    OTHER = "OTHER"


class ReviewStatus(str, Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_INTERPRETATION = "VERIFIED_WITH_INTERPRETATION"
    PENDING_SOURCE = "PENDING_SOURCE"
    DEPRECATED = "DEPRECATED"


class ParameterType(str, Enum):
    EMISSION_FACTOR = "EMISSION_FACTOR"
    GWP = "GWP"
    LOWER_HEATING_VALUE = "LOWER_HEATING_VALUE"
    CARBON_CONTENT_PER_HEAT = "CARBON_CONTENT_PER_HEAT"
    OXIDATION_RATE = "OXIDATION_RATE"
    COMPOSITION = "COMPOSITION"
    PROCESS_CO2_FACTOR = "PROCESS_CO2_FACTOR"
    ELECTRICITY_EMISSION_FACTOR = "ELECTRICITY_EMISSION_FACTOR"
    HEAT_EMISSION_FACTOR = "HEAT_EMISSION_FACTOR"
    PROCESS_DEFAULT_PARAMETER = "PROCESS_DEFAULT_PARAMETER"
    STEAM_ENTHALPY = "STEAM_ENTHALPY"
    SYSTEM_CONVERSION = "SYSTEM_CONVERSION"


class ValueType(str, Enum):
    STANDARD_SPECIFIED = "STANDARD_SPECIFIED"
    STANDARD_DEFAULT = "STANDARD_DEFAULT"
    GOVERNMENT_PUBLISHED = "GOVERNMENT_PUBLISHED"
    SCIENTIFIC_REFERENCE = "SCIENTIFIC_REFERENCE"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    SYSTEM_CONSTANT = "SYSTEM_CONSTANT"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True, slots=True)
class Standard:
    standard_id: str
    standard_family_id: str
    standard_number: str
    standard_name: str
    version: str
    publication_date: date | None = None
    implementation_date: date | None = None
    abolition_date: date | None = None
    official_status: OfficialStatus = OfficialStatus.UNKNOWN
    official_source_url: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.standard_id, "standard_id")
        _require_id(self.standard_family_id, "standard_family_id")
        _require_id(self.version, "version")
        _require_text(self.standard_number, "standard_number")
        _require_text(self.standard_name, "standard_name")
        if self.official_source_url is not None and not self.official_source_url.startswith(("http://", "https://")):
            raise DomainValidationError("official_source_url must be an HTTP(S) URL")
        if self.publication_date and self.implementation_date and self.implementation_date < self.publication_date:
            raise DomainValidationError("implementation_date cannot precede publication_date")
        if self.abolition_date and self.implementation_date and self.abolition_date < self.implementation_date:
            raise DomainValidationError("abolition_date cannot precede implementation_date")


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_id: str
    source_type: SourceType
    document_no: str
    document_name: str
    publisher: str
    publication_date: date | None = None
    source_effective_from: date | None = None
    source_effective_to: date | None = None
    version: str = "v1"
    revision: str | None = None
    official_url: str | None = None
    review_status: ReviewStatus = ReviewStatus.PENDING_SOURCE
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.source_id, "source_id")
        _require_id(self.version, "version")
        _require_text(self.document_no, "document_no")
        _require_text(self.document_name, "document_name")
        _require_text(self.publisher, "publisher")
        if self.official_url is not None and not self.official_url.startswith(("http://", "https://")):
            raise DomainValidationError("official_url must be an HTTP(S) URL")
        if self.source_effective_from and self.source_effective_to and self.source_effective_to < self.source_effective_from:
            raise DomainValidationError("source effective dates are out of order")


@dataclass(frozen=True, slots=True)
class Parameter:
    parameter_id: str
    subject_id: str
    parameter_type: ParameterType
    name: str
    default_unit: str
    version: str
    description: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.parameter_id, "parameter_id")
        _require_id(self.subject_id, "subject_id")
        _require_id(self.version, "version")
        _require_text(self.name, "name")
        _require_unit(self.default_unit)


@dataclass(frozen=True, slots=True)
class Factor:
    factor_id: str
    parameter_id: str
    subject_id: str
    parameter_type: ParameterType
    value: str | Decimal | int
    unit: str
    version: str
    value_type: ValueType
    review_status: ReviewStatus
    source_id: str | None = None
    source_location: str | None = None
    applicable_standard_ids: tuple[str, ...] = ()
    valid_from: date | None = None
    valid_to: date | None = None

    def __post_init__(self) -> None:
        _require_id(self.factor_id, "factor_id")
        _require_id(self.parameter_id, "parameter_id")
        _require_id(self.subject_id, "subject_id")
        _require_id(self.version, "version")
        _require_unit(self.unit)
        object.__setattr__(self, "value", _normalize_decimal(self.value, "value"))
        object.__setattr__(self, "applicable_standard_ids", _normalize_tuple(self.applicable_standard_ids, "applicable_standard_ids"))
        for standard_id in self.applicable_standard_ids:
            _require_id(standard_id, "applicable_standard_id")
        if self.source_id is not None:
            _require_id(self.source_id, "source_id")
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise DomainValidationError("factor validity dates are out of order")


class ActivityDataSource(str, Enum):
    METER = "METER"
    PRODUCTION_LEDGER = "PRODUCTION_LEDGER"
    ENERGY_BILL = "ENERGY_BILL"
    TEST_REPORT = "TEST_REPORT"
    STATEMENT = "STATEMENT"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class ActivityData:
    activity_id: str
    value: str | Decimal | int
    unit: str
    source_type: ActivityDataSource
    source_reference: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.activity_id, "activity_id")
        _require_unit(self.unit)
        object.__setattr__(self, "value", _normalize_decimal(self.value, "value"))


class PeriodType(str, Enum):
    ANNUAL = "ANNUAL"
    MONTHLY = "MONTHLY"


@dataclass(frozen=True, slots=True)
class AccountingPeriod:
    period_type: PeriodType
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise DomainValidationError("period start cannot be after period end")
        if self.period_type is PeriodType.ANNUAL:
            if self.start.month != 1 or self.start.day != 1 or self.end.month != 12 or self.end.day != 31 or self.start.year != self.end.year:
                raise DomainValidationError("annual period must cover one calendar year")
        elif self.period_type is PeriodType.MONTHLY:
            last_day = calendar.monthrange(self.start.year, self.start.month)[1]
            if self.start.day != 1 or self.end.year != self.start.year or self.end.month != self.start.month or self.end.day != last_day:
                raise DomainValidationError("monthly period must cover one calendar month")
        else:
            raise DomainValidationError("unsupported accounting period type")


@dataclass(frozen=True, slots=True)
class EmissionSourceSelection:
    source_id: str
    included: bool

    def __post_init__(self) -> None:
        _require_id(self.source_id, "source_id")


@dataclass(frozen=True, slots=True)
class AccountingInput:
    input_id: str
    standard_id: str
    period: AccountingPeriod
    enterprise_name: str | None = None
    boundary_component_ids: tuple[str, ...] = ()
    emission_sources: tuple[EmissionSourceSelection, ...] = ()
    activities: tuple[ActivityData, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.input_id, "input_id")
        _require_id(self.standard_id, "standard_id")
        if self.enterprise_name is not None and not self.enterprise_name.strip():
            raise DomainValidationError("enterprise_name cannot be blank")
        boundary_ids = _normalize_tuple(self.boundary_component_ids, "boundary_component_ids")
        for boundary_id in boundary_ids:
            _require_id(boundary_id, "boundary_component_id")
        object.__setattr__(self, "boundary_component_ids", boundary_ids)
        sources = _normalize_tuple(self.emission_sources, "emission_sources")
        activities = _normalize_tuple(self.activities, "activities")
        if len({source.source_id for source in sources}) != len(sources):
            raise DomainValidationError("emission source IDs must be unique")
        if len({activity.activity_id for activity in activities}) != len(activities):
            raise DomainValidationError("activity IDs must be unique")
        object.__setattr__(self, "emission_sources", sources)
        object.__setattr__(self, "activities", activities)


@dataclass(frozen=True, slots=True)
class CalculationLine:
    line_id: str
    emission_source_id: str
    greenhouse_gas_id: str
    amount: str | Decimal | int
    unit: str

    def __post_init__(self) -> None:
        _require_id(self.line_id, "line_id")
        _require_id(self.emission_source_id, "emission_source_id")
        _require_id(self.greenhouse_gas_id, "greenhouse_gas_id")
        _require_unit(self.unit)
        object.__setattr__(self, "amount", _normalize_decimal(self.amount, "amount"))


@dataclass(frozen=True, slots=True)
class CalculationResult:
    result_id: str
    standard_id: str
    algorithm_version: str
    lines: tuple[CalculationLine, ...]
    total_amount: str | Decimal | int
    total_unit: str
    calculated_at: datetime
    problems: tuple[ValidationProblem, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.result_id, "result_id")
        _require_id(self.standard_id, "standard_id")
        _require_id(self.algorithm_version, "algorithm_version")
        _require_unit(self.total_unit)
        _require_aware_datetime(self.calculated_at, "calculated_at")
        lines = _normalize_tuple(self.lines, "lines")
        if len({line.line_id for line in lines}) != len(lines):
            raise DomainValidationError("calculation line IDs must be unique")
        object.__setattr__(self, "lines", lines)
        object.__setattr__(self, "total_amount", _normalize_decimal(self.total_amount, "total_amount"))
        object.__setattr__(self, "problems", _normalize_tuple(self.problems, "problems"))


class ParameterSelectionMethod(str, Enum):
    SYSTEM_RECOMMENDED = "SYSTEM_RECOMMENDED"
    STANDARD_REQUIRED = "STANDARD_REQUIRED"
    USER_SELECTED_LIBRARY_VALUE = "USER_SELECTED_LIBRARY_VALUE"
    ENTERPRISE_MEASURED = "ENTERPRISE_MEASURED"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    INTERPOLATED = "INTERPOLATED"
    DERIVED = "DERIVED"


@dataclass(frozen=True, slots=True)
class ParameterSnapshot:
    snapshot_id: str
    parameter_id: str
    factor_id: str | None
    value_used: str | Decimal | int
    unit_used: str
    source_id: str | None
    source_version: str | None
    selection_method: ParameterSelectionMethod
    selection_reason: str
    standard_id: str
    snapshot_at: datetime

    def __post_init__(self) -> None:
        _require_id(self.snapshot_id, "snapshot_id")
        _require_id(self.parameter_id, "parameter_id")
        _require_id(self.standard_id, "standard_id")
        _require_unit(self.unit_used)
        object.__setattr__(self, "value_used", _normalize_decimal(self.value_used, "value_used"))
        _require_text(self.selection_reason, "selection_reason")
        _require_aware_datetime(self.snapshot_at, "snapshot_at")
        if self.factor_id is not None:
            _require_id(self.factor_id, "factor_id")
        if self.source_id is not None:
            _require_id(self.source_id, "source_id")
        if self.source_version is not None:
            _require_id(self.source_version, "source_version")


class RecordStatus(str, Enum):
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"


@dataclass(frozen=True, slots=True)
class AccountingRecord:
    record_id: str
    standard_id: str
    algorithm_version: str
    created_at: datetime
    input_snapshot: AccountingInput
    calculation_result: CalculationResult
    status: RecordStatus
    parameter_snapshots: tuple[ParameterSnapshot, ...] = ()
    problems: tuple[ValidationProblem, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.record_id, "record_id")
        _require_id(self.standard_id, "standard_id")
        _require_id(self.algorithm_version, "algorithm_version")
        _require_aware_datetime(self.created_at, "created_at")
        if self.input_snapshot.standard_id != self.standard_id:
            raise DomainValidationError("record and input standard IDs must match")
        if self.calculation_result.standard_id != self.standard_id:
            raise DomainValidationError("record and result standard IDs must match")
        if self.calculation_result.algorithm_version != self.algorithm_version:
            raise DomainValidationError("record and result algorithm versions must match")
        snapshots = _normalize_tuple(self.parameter_snapshots, "parameter_snapshots")
        problems = _normalize_tuple(self.problems, "problems")
        if len({snapshot.snapshot_id for snapshot in snapshots}) != len(snapshots):
            raise DomainValidationError("parameter snapshot IDs must be unique")
        for snapshot in snapshots:
            if snapshot.standard_id != self.standard_id:
                raise DomainValidationError("parameter snapshot standard IDs must match the record")
        object.__setattr__(self, "parameter_snapshots", snapshots)
        object.__setattr__(self, "problems", problems)

        all_problems = problems + self.calculation_result.problems
        if contains_errors(all_problems):
            raise DomainValidationError("ERROR validation problems cannot create a record")
        expected_status = (
            RecordStatus.COMPLETED_WITH_WARNINGS
            if contains_warnings(all_problems)
            else RecordStatus.COMPLETED
        )
        if self.status is not expected_status:
            raise DomainValidationError("record status does not match its validation problems")


@dataclass(frozen=True, slots=True)
class SettingEntry:
    key: str
    value: str

    def __post_init__(self) -> None:
        _require_id(self.key, "setting key")


@dataclass(frozen=True, slots=True)
class Settings:
    settings_id: str
    entries: tuple[SettingEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.settings_id, "settings_id")
        entries = _normalize_tuple(self.entries, "entries")
        if len({entry.key for entry in entries}) != len(entries):
            raise DomainValidationError("setting keys must be unique")
        object.__setattr__(self, "entries", entries)
