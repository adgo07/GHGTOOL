"""GB/T 32151.34-2024 calculation domain for G06.

The module is deliberately platform independent.  It contains the frozen SM01
formula paths, standard-specific input contracts, validation and an in-memory
record boundary used by G06.  Qt and SQLite adapters live outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, fields as dataclass_fields, is_dataclass, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import Callable, Mapping, Sequence
from uuid import uuid4

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError, IssueLevel, ValidationProblem, contains_errors, contains_warnings
from packages.core.models import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    ActivityDataSource,
    ActivitySourceLevel,
    CalculationLine,
    CalculationResult,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    EmissionSourceSelection,
    ParameterSelectionMethod,
    ParameterSnapshot,
    ParameterType,
    PeriodType,
    RecordStatus,
    ValueType,
)
from packages.core.parameter_resolution import (
    ElectricityConsumptionDetail,
    ElectricityResolutionRoute,
    ParameterResolutionContext,
    ParameterResolver,
)
from packages.core.repositories import ParameterRepository, RecordRepository
from packages.standards.carbon_material_normalization import (
    MATERIAL_NORMALIZATION_VERSION,
    MaterialInputLine,
    normalize_material_inputs,
)
from packages.core.units import UnitError, UnitService


STANDARD_ID = "gbt_32151_34_2024"
STANDARD_VERSION = "2024"
ALGORITHM_VERSION = "CAR-SM01-2026-09-13-G06.1"
CO2_ID = "GEN-GAS-CO2"
SOURCE_FUEL = "CAR-SRC-FUEL-001"
SOURCE_CALCINATION = "CAR-SRC-CALCINATION-001"
SOURCE_BAKING = "CAR-SRC-BAKING-001"
SOURCE_GRAPHITIZATION = "CAR-SRC-GRAPHITIZATION-001"
SOURCE_FUME = "CAR-SRC-FUME-INCINERATION-001"
SOURCE_FGD = "CAR-SRC-FGD-001"
SOURCE_PURCHASED_ELECTRICITY = "CAR-SRC-PURCHASED-ELECTRICITY-001"
SOURCE_PURCHASED_HEAT = "CAR-SRC-PURCHASED-HEAT-001"
SOURCE_EXPORTED_ELECTRICITY = "CAR-SRC-EXPORTED-ELECTRICITY-001"
SOURCE_EXPORTED_HEAT = "CAR-SRC-EXPORTED-HEAT-001"

EVIDENCE_SOURCE_ID = "EVID-CAR-PDF-2024-LOCAL"
MAPPING_VERSION = "SM01-2026-09-13-R6"
GREEN_ELECTRICITY_EVIDENCE_CODE = "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE"


class EmissionSourceStatus(str, Enum):
    INVOLVED = "INVOLVED"
    NOT_INVOLVED = "NOT_INVOLVED"
    UNCONFIRMED = "UNCONFIRMED"


class FuelPath(str, Enum):
    VOLUME = "VOLUME"
    MASS = "MASS"
    HEAT = "HEAT"


class FuelType(str, Enum):
    DIESEL = "DIESEL"
    NATURAL_GAS = "NATURAL_GAS"
    COKE_OVEN_GAS = "COKE_OVEN_GAS"
    COAL = "COAL"
    OTHER = "OTHER"
    ANTHRACITE = "ANTHRACITE"
    BITUMINOUS_COAL = "BITUMINOUS_COAL"
    LIGNITE = "LIGNITE"
    CLEANED_COAL = "CLEANED_COAL"
    OTHER_CLEANED_COAL = "OTHER_CLEANED_COAL"
    BRIQUETTE = "BRIQUETTE"
    OTHER_COAL_PRODUCTS = "OTHER_COAL_PRODUCTS"
    COKE = "COKE"
    PETROLEUM_COKE = "PETROLEUM_COKE"
    CRUDE_OIL = "CRUDE_OIL"
    FUEL_OIL = "FUEL_OIL"
    GASOLINE = "GASOLINE"
    KEROSENE = "KEROSENE"
    LIQUEFIED_NATURAL_GAS = "LIQUEFIED_NATURAL_GAS"
    LIQUEFIED_PETROLEUM_GAS = "LIQUEFIED_PETROLEUM_GAS"
    NAPHTHA = "NAPHTHA"
    TAR = "TAR"
    CRUDE_BENZENE = "CRUDE_BENZENE"
    OTHER_PETROLEUM_PRODUCTS = "OTHER_PETROLEUM_PRODUCTS"
    BLAST_FURNACE_GAS = "BLAST_FURNACE_GAS"
    CONVERTER_GAS = "CONVERTER_GAS"
    REFINERY_DRY_GAS = "REFINERY_DRY_GAS"
    OTHER_GAS = "OTHER_GAS"


class MaterialBasis(str, Enum):
    RECEIVED = "RECEIVED"
    DRY = "DRY"
    OTHER_DOCUMENTED = "OTHER_DOCUMENTED"
    UNKNOWN = "UNKNOWN"


class MaterialComponentKind(str, Enum):
    FIXED_CARBON = "FIXED_CARBON"
    VOLATILE_MATTER = "VOLATILE_MATTER"
    TOTAL_CARBON = "TOTAL_CARBON"
    UNKNOWN = "UNKNOWN"


class SteamKind(str, Enum):
    SATURATED = "SATURATED"
    SUPERHEATED = "SUPERHEATED"


class HeatFactorMode(str, Enum):
    STANDARD_DEFAULT = "STANDARD_DEFAULT"
    MEASURED = "MEASURED"


class ParameterSourceKind(str, Enum):
    STANDARD_DEFAULT = "STANDARD_DEFAULT"
    STANDARD_SPECIFIED = "STANDARD_SPECIFIED"
    MEASURED = "MEASURED"
    CALCULATED = "CALCULATED"
    OFFICIAL_PUBLISHED = "OFFICIAL_PUBLISHED"
    USER_DEFINED = "USER_DEFINED"
    PROJECT_SPECIFIED = "PROJECT_SPECIFIED"


@dataclass(frozen=True, slots=True)
class EmissionSourceState:
    source_id: str
    status: EmissionSourceStatus

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise DomainValidationError("source_id is required")
        if not isinstance(self.status, EmissionSourceStatus):
            raise DomainValidationError("status must be an EmissionSourceStatus")


@dataclass(frozen=True, slots=True)
class InputValue:
    value: str | Decimal | int
    unit: str
    source_type: ActivityDataSource = ActivityDataSource.MANUAL
    source_level: ActivitySourceLevel = ActivitySourceLevel.PRIMARY
    source_reference: str | None = None
    evidence_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        policy = DecimalPolicy()
        object.__setattr__(self, "value", policy.parse(self.value))
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise DomainValidationError("input unit is required")
        if not isinstance(self.source_type, ActivityDataSource):
            raise DomainValidationError("source_type must be an ActivityDataSource")
        if not isinstance(self.source_level, ActivitySourceLevel):
            raise DomainValidationError("source_level must be an ActivitySourceLevel")
        if self.source_reference is not None and not self.source_reference.strip():
            raise DomainValidationError("source_reference cannot be blank")
        evidence_ids = tuple(self.evidence_ref_ids)
        if any(not isinstance(item, str) or not item.strip() for item in evidence_ids):
            raise DomainValidationError("evidence_ref_ids must contain nonblank identifiers")
        object.__setattr__(self, "evidence_ref_ids", evidence_ids)
        object.__setattr__(self, "unit", self.unit.strip())


@dataclass(frozen=True, slots=True)
class ParameterValue:
    parameter_id: str
    value: str | Decimal | int
    unit: str
    source_kind: ParameterSourceKind = ParameterSourceKind.STANDARD_DEFAULT
    source_id: str | None = EVIDENCE_SOURCE_ID
    source_version: str | None = MAPPING_VERSION
    source_location: str | None = None
    selection_reason: str = "按 GB/T 32151.34-2024 映射采用。"
    factor_id: str | None = None
    factor_year: int | None = None
    evidence_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_id, str) or not self.parameter_id.strip():
            raise DomainValidationError("parameter_id is required")
        object.__setattr__(self, "value", DecimalPolicy().parse(self.value))
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise DomainValidationError("parameter unit is required")
        if not isinstance(self.source_kind, ParameterSourceKind):
            raise DomainValidationError("source_kind must be a ParameterSourceKind")
        if self.source_id is not None and not self.source_id.strip():
            raise DomainValidationError("source_id cannot be blank")
        if self.source_version is not None and not self.source_version.strip():
            raise DomainValidationError("source_version cannot be blank")
        if not self.selection_reason.strip():
            raise DomainValidationError("selection_reason is required")
        if self.factor_year is not None and self.factor_year < 1:
            raise DomainValidationError("factor_year must be positive")
        evidence_ids = tuple(self.evidence_ref_ids)
        if any(not isinstance(item, str) or not item.strip() for item in evidence_ids):
            raise DomainValidationError("evidence_ref_ids must contain nonblank identifiers")
        object.__setattr__(self, "evidence_ref_ids", evidence_ids)
        object.__setattr__(self, "unit", self.unit.strip())


@dataclass(frozen=True, slots=True)
class ActivityDataEvidence:
    """Reusable, standard-specific evidence for activity-data provenance."""

    evidence_id: str
    applies_to: str
    source_ids: tuple[str, ...] = ()
    source_reference: str | None = None
    monitoring_location: str | None = None
    monitoring_method: str | None = None
    instrument: str | None = None
    accuracy: str | None = None
    recording_frequency: str | None = None
    acquisition_time: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        _validate_instance_id(self.evidence_id)
        if not self.applies_to.strip():
            raise DomainValidationError("activity evidence scope is required")
        source_ids = tuple(self.source_ids)
        for source_id in source_ids:
            _validate_instance_id(source_id)
        if len(source_ids) != len(set(source_ids)):
            raise DomainValidationError("activity evidence source IDs must be unique")
        object.__setattr__(self, "source_ids", source_ids)


@dataclass(frozen=True, slots=True)
class MeasuredFactorEvidence:
    """Reusable sampling/testing evidence for measured or user-defined factors."""

    evidence_id: str
    applies_to: str
    source_ids: tuple[str, ...] = ()
    source_reference: str | None = None
    sampling_method: str | None = None
    sampling_frequency: str | None = None
    testing_method: str | None = None
    testing_frequency: str | None = None
    referenced_standard: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        _validate_instance_id(self.evidence_id)
        if not self.applies_to.strip():
            raise DomainValidationError("measured factor evidence scope is required")
        source_ids = tuple(self.source_ids)
        for source_id in source_ids:
            _validate_instance_id(source_id)
        if len(source_ids) != len(set(source_ids)):
            raise DomainValidationError("measured factor evidence source IDs must be unique")
        object.__setattr__(self, "source_ids", source_ids)


@dataclass(frozen=True, slots=True)
class CarbonReportingData:
    """Optional report-oriented information fixed in each new record snapshot."""

    organization_nature: str | None = None
    industry: str | None = None
    social_credit_code: str | None = None
    legal_representative: str | None = None
    preparer_name: str | None = None
    preparer_contact: str | None = None
    boundary_description: str | None = None
    products_and_process: str | None = None
    emission_source_identification: str | None = None
    other_report_information: str | None = None
    activity_evidence: tuple[ActivityDataEvidence, ...] = ()
    measured_factor_evidence: tuple[MeasuredFactorEvidence, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "organization_nature", "industry", "social_credit_code", "legal_representative",
            "preparer_name", "preparer_contact", "boundary_description", "products_and_process",
            "emission_source_identification", "other_report_information",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise DomainValidationError(f"{name} must be text")
        activity = tuple(self.activity_evidence)
        factors = tuple(self.measured_factor_evidence)
        if any(not isinstance(item, ActivityDataEvidence) for item in activity):
            raise DomainValidationError("activity_evidence must contain ActivityDataEvidence values")
        if any(not isinstance(item, MeasuredFactorEvidence) for item in factors):
            raise DomainValidationError("measured_factor_evidence must contain MeasuredFactorEvidence values")
        ids = tuple(item.evidence_id for item in (*activity, *factors))
        if len(ids) != len(set(ids)):
            raise DomainValidationError("evidence IDs must be unique within reporting data")
        object.__setattr__(self, "activity_evidence", activity)
        object.__setattr__(self, "measured_factor_evidence", factors)


def _attach_evidence_references(value: object, activity_ids: tuple[str, ...], factor_ids: tuple[str, ...]) -> object:
    """Copy shared evidence references into source values without changing values."""
    if isinstance(value, InputValue) and activity_ids:
        return replace(value, evidence_ref_ids=tuple(dict.fromkeys((*value.evidence_ref_ids, *activity_ids))))
    if isinstance(value, ParameterValue) and value.source_kind in {
        ParameterSourceKind.MEASURED, ParameterSourceKind.USER_DEFINED,
    } and factor_ids:
        return replace(value, evidence_ref_ids=tuple(dict.fromkeys((*value.evidence_ref_ids, *factor_ids))))
    if isinstance(value, tuple):
        return tuple(_attach_evidence_references(item, activity_ids, factor_ids) for item in value)
    if isinstance(value, list):
        return [_attach_evidence_references(item, activity_ids, factor_ids) for item in value]
    if isinstance(value, dict):
        return {key: _attach_evidence_references(item, activity_ids, factor_ids) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        updates = {
            item.name: _attach_evidence_references(getattr(value, item.name), activity_ids, factor_ids)
            for item in dataclass_fields(value)
        }
        if any(updates[item.name] is not getattr(value, item.name) for item in dataclass_fields(value)):
            return replace(value, **updates)
    return value


def _coerce_input(value: object, default_unit: str) -> InputValue | None:
    if value is None:
        return None
    if isinstance(value, InputValue):
        return value
    if isinstance(value, ParameterValue):
        return InputValue(value.value, value.unit, evidence_ref_ids=value.evidence_ref_ids)
    return InputValue(value, default_unit)  # type: ignore[arg-type]


def _validate_instance_id(value: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value.isascii()
        or not all(char.isalnum() or char in "_.:-" for char in value)
    ):
        raise DomainValidationError("instance_id must be a stable ASCII token")


def _coerce_parameter(
    value: object,
    parameter_id: str,
    default_unit: str,
    *,
    source_location: str | None = None,
) -> ParameterValue | None:
    if value is None:
        return None
    if isinstance(value, ParameterValue):
        return value
    if isinstance(value, InputValue):
        return ParameterValue(
            parameter_id,
            value.value,
            value.unit,
            ParameterSourceKind.MEASURED,
            source_id=value.source_reference,
            source_version=MAPPING_VERSION,
            source_location=source_location,
            selection_reason="采用企业输入的实测/活动数据参数。",
            evidence_ref_ids=value.evidence_ref_ids,
        )
    return ParameterValue(parameter_id, value, default_unit, source_location=source_location)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class FuelInput:
    fuel_id: str
    path: FuelPath
    activity: object | None = None
    carbon_content: object | None = None
    oxidation_rate: object | None = None
    lower_heating_value: object | None = None
    electricity_detail_id: str | None = None
    fuel_type: FuelType | None = None
    fuel_label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fuel_id, str) or not self.fuel_id.strip():
            raise DomainValidationError("fuel_id is required")
        if not isinstance(self.path, FuelPath):
            raise DomainValidationError("path must be a FuelPath")
        if self.fuel_type is not None and not isinstance(self.fuel_type, FuelType):
            raise DomainValidationError("fuel_type must be a FuelType")
        if self.fuel_label is not None and (
            not isinstance(self.fuel_label, str) or not self.fuel_label.strip()
        ):
            raise DomainValidationError("fuel_label must be a non-blank string when supplied")
        activity_unit = {
            FuelPath.VOLUME: "ten_thousand_Nm3",
            FuelPath.MASS: "t",
            FuelPath.HEAT: "GJ",
        }[self.path]
        carbon_unit = {
            FuelPath.VOLUME: "tC/10^4Nm3",
            FuelPath.MASS: "tC/t",
            FuelPath.HEAT: "tC/GJ",
        }[self.path]
        object.__setattr__(self, "activity", _coerce_input(self.activity, activity_unit))
        object.__setattr__(self, "carbon_content", _coerce_parameter(self.carbon_content, f"CAR-PAR-{self.fuel_id}-CARBON", carbon_unit, source_location="附录C.1；第5.2.1条"))
        object.__setattr__(self, "oxidation_rate", _coerce_parameter(self.oxidation_rate, f"CAR-PAR-{self.fuel_id}-OXIDATION", "ratio", source_location="附录C.1；第5.2.1条"))
        lhv_unit = {
            FuelPath.VOLUME: "GJ/10⁴Nm³",
            FuelPath.MASS: "GJ/t",
            FuelPath.HEAT: "GJ/GJ",
        }[self.path]
        object.__setattr__(self, "lower_heating_value", _coerce_parameter(self.lower_heating_value, f"CAR-PAR-{self.fuel_id}-LHV", lhv_unit, source_location="附录C.1；第5.2.1条"))
        if self.electricity_detail_id is not None and not self.electricity_detail_id.strip():
            raise DomainValidationError("electricity_detail_id cannot be blank")

    @classmethod
    def volume(cls, fuel_id: str, afv: object, fcv: object, fox: object) -> "FuelInput":
        return cls(fuel_id, FuelPath.VOLUME, afv, fcv, fox)

    @classmethod
    def mass(cls, fuel_id: str, afm: object, fcm: object, fox: object) -> "FuelInput":
        return cls(fuel_id, FuelPath.MASS, afm, fcm, fox)

    @classmethod
    def heat(cls, fuel_id: str, afh: object, fch: object, fox: object) -> "FuelInput":
        return cls(fuel_id, FuelPath.HEAT, afh, fch, fox)


@dataclass(frozen=True, slots=True)
class CalcinationInput:
    gc: object | None = None
    wfc: object | None = None
    cc: object | None = None
    ucc: object | None = None
    du: object | None = None
    wfc_c: object | None = None
    wvar: object | None = None
    wvar_c: object | None = None
    k1: object | None = None
    mass_basis: MaterialBasis = MaterialBasis.RECEIVED
    composition_basis: MaterialBasis = MaterialBasis.RECEIVED
    normalized_basis: MaterialBasis | None = MaterialBasis.RECEIVED
    component_kind: MaterialComponentKind = MaterialComponentKind.FIXED_CARBON
    moisture_evidence: bool = False
    conversion_evidence: bool = False
    carbon_output_included_in_input: bool = False
    fixed_carbon_component_kind: MaterialComponentKind | None = None
    volatile_matter_component_kind: MaterialComponentKind | None = None
    instance_id: str = "calcination-1"
    material_rows: tuple[MaterialInputLine, ...] | None = None

    def __post_init__(self) -> None:
        _validate_instance_id(self.instance_id)
        for field in ("mass_basis", "composition_basis"):
            if not isinstance(getattr(self, field), MaterialBasis):
                raise DomainValidationError(f"{field} must be a MaterialBasis")
        if self.normalized_basis is not None and not isinstance(self.normalized_basis, MaterialBasis):
            raise DomainValidationError("normalized_basis must be a MaterialBasis")
        if not isinstance(self.component_kind, MaterialComponentKind):
            raise DomainValidationError("component_kind must be a MaterialComponentKind")
        fixed_kind = self.fixed_carbon_component_kind if self.fixed_carbon_component_kind is not None else self.component_kind
        volatile_kind = self.volatile_matter_component_kind if self.volatile_matter_component_kind is not None else MaterialComponentKind.VOLATILE_MATTER
        if not isinstance(fixed_kind, MaterialComponentKind):
            raise DomainValidationError("fixed_carbon_component_kind must be a MaterialComponentKind")
        if not isinstance(volatile_kind, MaterialComponentKind):
            raise DomainValidationError("volatile_matter_component_kind must be a MaterialComponentKind")
        object.__setattr__(self, "fixed_carbon_component_kind", fixed_kind)
        object.__setattr__(self, "volatile_matter_component_kind", volatile_kind)
        for name in ("gc", "cc", "ucc", "du"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "t"))
        for name in ("wfc", "wfc_c", "wvar", "wvar_c"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "ratio"))
        object.__setattr__(self, "k1", _coerce_parameter(self.k1, "CAR-PAR-K1", "ratio", source_location="第5.2.2条；一般取0.35"))
        if self.material_rows is not None:
            rows = tuple(self.material_rows)
            if any(not isinstance(item, MaterialInputLine) for item in rows):
                raise DomainValidationError("material_rows must contain MaterialInputLine values")
            object.__setattr__(self, "material_rows", rows)


@dataclass(frozen=True, slots=True)
class BakingInput:
    bpm: object | None = None
    bpmfc: object | None = None
    bg: object | None = None
    bgfc: object | None = None
    bwt: object | None = None
    bp: object | None = None
    bpfc: object | None = None
    bpmvar: object | None = None
    bgvar: object | None = None
    k2: object | None = None
    mass_basis: MaterialBasis = MaterialBasis.RECEIVED
    composition_basis: MaterialBasis = MaterialBasis.RECEIVED
    normalized_basis: MaterialBasis | None = MaterialBasis.RECEIVED
    component_kind: MaterialComponentKind = MaterialComponentKind.FIXED_CARBON
    moisture_evidence: bool = False
    conversion_evidence: bool = False
    carbon_output_included_in_input: bool = False
    fixed_carbon_component_kind: MaterialComponentKind | None = None
    volatile_matter_component_kind: MaterialComponentKind | None = None
    instance_id: str = "baking-1"
    material_rows: tuple[MaterialInputLine, ...] | None = None

    def __post_init__(self) -> None:
        _validate_instance_id(self.instance_id)
        for field in ("mass_basis", "composition_basis"):
            if not isinstance(getattr(self, field), MaterialBasis):
                raise DomainValidationError(f"{field} must be a MaterialBasis")
        if self.normalized_basis is not None and not isinstance(self.normalized_basis, MaterialBasis):
            raise DomainValidationError("normalized_basis must be a MaterialBasis")
        if not isinstance(self.component_kind, MaterialComponentKind):
            raise DomainValidationError("component_kind must be a MaterialComponentKind")
        fixed_kind = self.fixed_carbon_component_kind if self.fixed_carbon_component_kind is not None else self.component_kind
        volatile_kind = self.volatile_matter_component_kind if self.volatile_matter_component_kind is not None else MaterialComponentKind.VOLATILE_MATTER
        if not isinstance(fixed_kind, MaterialComponentKind):
            raise DomainValidationError("fixed_carbon_component_kind must be a MaterialComponentKind")
        if not isinstance(volatile_kind, MaterialComponentKind):
            raise DomainValidationError("volatile_matter_component_kind must be a MaterialComponentKind")
        object.__setattr__(self, "fixed_carbon_component_kind", fixed_kind)
        object.__setattr__(self, "volatile_matter_component_kind", volatile_kind)
        for name in ("bpm", "bg", "bp"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "t"))
        object.__setattr__(self, "bwt", _coerce_input(self.bwt, "tC"))
        for name in ("bpmfc", "bgfc", "bpfc", "bpmvar", "bgvar"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "ratio"))
        object.__setattr__(self, "k2", _coerce_parameter(self.k2, "CAR-PAR-K2", "ratio", source_location="第5.2.3条；一般取0.35"))
        if self.material_rows is not None:
            rows = tuple(self.material_rows)
            if any(not isinstance(item, MaterialInputLine) for item in rows):
                raise DomainValidationError("material_rows must contain MaterialInputLine values")
            object.__setattr__(self, "material_rows", rows)


@dataclass(frozen=True, slots=True)
class GraphitizationInput:
    gpm: object | None = None
    gpmfc: object | None = None
    gta: object | None = None
    gtafc: object | None = None
    gwt: object | None = None
    gp: object | None = None
    gpfc: object | None = None
    gpmvar: object | None = None
    k3: object | None = None
    mass_basis: MaterialBasis = MaterialBasis.RECEIVED
    composition_basis: MaterialBasis = MaterialBasis.RECEIVED
    normalized_basis: MaterialBasis | None = MaterialBasis.RECEIVED
    component_kind: MaterialComponentKind = MaterialComponentKind.FIXED_CARBON
    moisture_evidence: bool = False
    conversion_evidence: bool = False
    furnace_loss_included: bool = False
    fixed_carbon_component_kind: MaterialComponentKind | None = None
    volatile_matter_component_kind: MaterialComponentKind | None = None
    instance_id: str = "graphitization-1"
    material_rows: tuple[MaterialInputLine, ...] | None = None

    def __post_init__(self) -> None:
        _validate_instance_id(self.instance_id)
        for field in ("mass_basis", "composition_basis"):
            if not isinstance(getattr(self, field), MaterialBasis):
                raise DomainValidationError(f"{field} must be a MaterialBasis")
        if self.normalized_basis is not None and not isinstance(self.normalized_basis, MaterialBasis):
            raise DomainValidationError("normalized_basis must be a MaterialBasis")
        if not isinstance(self.component_kind, MaterialComponentKind):
            raise DomainValidationError("component_kind must be a MaterialComponentKind")
        fixed_kind = self.fixed_carbon_component_kind if self.fixed_carbon_component_kind is not None else self.component_kind
        volatile_kind = self.volatile_matter_component_kind if self.volatile_matter_component_kind is not None else MaterialComponentKind.VOLATILE_MATTER
        if not isinstance(fixed_kind, MaterialComponentKind):
            raise DomainValidationError("fixed_carbon_component_kind must be a MaterialComponentKind")
        if not isinstance(volatile_kind, MaterialComponentKind):
            raise DomainValidationError("volatile_matter_component_kind must be a MaterialComponentKind")
        object.__setattr__(self, "fixed_carbon_component_kind", fixed_kind)
        object.__setattr__(self, "volatile_matter_component_kind", volatile_kind)
        for name in ("gpm", "gta", "gp"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "t"))
        object.__setattr__(self, "gwt", _coerce_input(self.gwt, "tC"))
        for name in ("gpmfc", "gtafc", "gpfc", "gpmvar"):
            object.__setattr__(self, name, _coerce_input(getattr(self, name), "ratio"))
        object.__setattr__(self, "k3", _coerce_parameter(self.k3, "CAR-PAR-K3", "ratio", source_location="第5.2.4条；一般取0.35"))
        if self.material_rows is not None:
            rows = tuple(self.material_rows)
            if any(not isinstance(item, MaterialInputLine) for item in rows):
                raise DomainValidationError("material_rows must contain MaterialInputLine values")
            object.__setattr__(self, "material_rows", rows)


@dataclass(frozen=True, slots=True)
class FumeIncinerationInput:
    q: object | None = None
    qvar: object | None = None
    hm: object | None = None
    fch: object | None = None
    fox: object | None = None
    duration: object | None = None
    instance_id: str = "fume-1"

    def __post_init__(self) -> None:
        _validate_instance_id(self.instance_id)
        object.__setattr__(self, "q", _coerce_input(self.q, "Nm3/h"))
        object.__setattr__(self, "qvar", _coerce_input(self.qvar, "mg/Nm3"))
        object.__setattr__(self, "hm", _coerce_input(self.hm, "GJ/t"))
        object.__setattr__(self, "fch", _coerce_parameter(self.fch, "CAR-PAR-P04A-FCH", "tC/GJ", source_location="第5.2.5.1条"))
        object.__setattr__(self, "fox", _coerce_input(self.fox, "ratio"))
        object.__setattr__(self, "duration", _coerce_input(self.duration, "d"))


@dataclass(frozen=True, slots=True)
class CarbonateComponent:
    amount: object
    carbonate_fraction: object
    emission_factor: object | None
    conversion_rate: object = 1
    carbonate_type: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _coerce_input(self.amount, "t"))
        if not isinstance(self.carbonate_fraction, ParameterValue):
            object.__setattr__(self, "carbonate_fraction", _coerce_input(self.carbonate_fraction, "ratio"))
        object.__setattr__(self, "emission_factor", _coerce_parameter(self.emission_factor, "CAR-PAR-P04B-EF1", "tCO2/t", source_location="第5.2.5.2条、附录C.2"))
        if not isinstance(self.conversion_rate, ParameterValue):
            object.__setattr__(self, "conversion_rate", _coerce_input(self.conversion_rate, "ratio"))
        if self.carbonate_type is not None and not self.carbonate_type.strip():
            raise DomainValidationError("carbonate_type cannot be blank")


@dataclass(frozen=True, slots=True)
class FGDInput:
    components: tuple[CarbonateComponent, ...] = ()
    cal: object | None = None
    i: object | None = None
    ef1: object | None = None
    tr: object | None = None
    carbonate_type: str | None = None
    instance_id: str = "fgd-1"

    def __post_init__(self) -> None:
        _validate_instance_id(self.instance_id)
        components = tuple(self.components)
        if any(not isinstance(item, CarbonateComponent) for item in components):
            raise DomainValidationError("components must contain CarbonateComponent values")
        if not components and self.cal is not None:
            components = (
                CarbonateComponent(
                    self.cal,
                    self.i,
                    self.ef1,
                    self.tr,
                    self.carbonate_type,
                ),
            )
        object.__setattr__(self, "components", components)


@dataclass(frozen=True, slots=True)
class ElectricityOutputLine:
    line_id: str
    amount: object
    factor: ParameterValue | None = None
    unit: str = "MWh"

    def __post_init__(self) -> None:
        if not self.line_id.strip():
            raise DomainValidationError("line_id is required")
        object.__setattr__(self, "amount", _coerce_input(self.amount, self.unit))


@dataclass(frozen=True, slots=True)
class HeatInput:
    line_id: str
    amount: object
    enthalpy: object | None = None
    factor: ParameterValue | None = None
    unit: str = "kg"
    steam_kind: SteamKind = SteamKind.SATURATED
    pressure_mpa: object | None = None
    temperature_c: object | None = None
    manual_enthalpy: bool | None = None
    factor_mode: HeatFactorMode | None = None
    factor_source_note: str | None = None
    steam_amount_t: object | None = None

    def __post_init__(self) -> None:
        if not self.line_id.strip():
            raise DomainValidationError("line_id is required")
        if not isinstance(self.steam_kind, SteamKind):
            raise DomainValidationError("steam_kind must be a SteamKind")
        manual = self.enthalpy is not None if self.manual_enthalpy is None else self.manual_enthalpy
        if not isinstance(manual, bool):
            raise DomainValidationError("manual_enthalpy must be a boolean")
        if not manual and self.enthalpy is not None:
            raise DomainValidationError("automatic enthalpy mode cannot include a manual enthalpy value")
        if self.factor_mode is not None and not isinstance(self.factor_mode, HeatFactorMode):
            raise DomainValidationError("factor_mode must be a HeatFactorMode")
        if self.factor_source_note is not None and not isinstance(self.factor_source_note, str):
            raise DomainValidationError("factor_source_note must be text")
        if self.factor_source_note is not None and not self.factor_source_note.strip():
            object.__setattr__(self, "factor_source_note", None)
        object.__setattr__(self, "manual_enthalpy", manual)
        object.__setattr__(self, "amount", _coerce_input(self.amount, self.unit))
        object.__setattr__(self, "enthalpy", _coerce_input(self.enthalpy, "kJ/kg"))
        object.__setattr__(self, "pressure_mpa", _coerce_input(self.pressure_mpa, "MPa"))
        object.__setattr__(self, "temperature_c", _coerce_input(self.temperature_c, "C"))
        object.__setattr__(self, "steam_amount_t", _coerce_input(self.steam_amount_t, "t"))


@dataclass(frozen=True, slots=True)
class CarbonMaterialInput:
    input_id: str
    enterprise_id: str
    enterprise_name: str | None
    period: AccountingPeriod
    boundary_confirmed: bool = False
    boundary_component_ids: tuple[str, ...] = ()
    source_states: tuple[EmissionSourceState, ...] = ()
    fuel_inputs: tuple[FuelInput, ...] = ()
    calcination: CalcinationInput | None = None
    baking: BakingInput | None = None
    graphitization: GraphitizationInput | None = None
    fume_incineration: FumeIncinerationInput | None = None
    fgd: FGDInput | None = None
    electricity_details: tuple[ElectricityConsumptionDetail, ...] = ()
    exported_electricity: tuple[ElectricityOutputLine, ...] = ()
    purchased_heat: tuple[HeatInput, ...] = ()
    exported_heat: tuple[HeatInput, ...] = ()
    other_activity_present: bool = False
    transport_present: bool = False
    calcinations: tuple[CalcinationInput, ...] = ()
    bakings: tuple[BakingInput, ...] = ()
    graphitizations: tuple[GraphitizationInput, ...] = ()
    fume_incinerations: tuple[FumeIncinerationInput, ...] = ()
    fgd_units: tuple[FGDInput, ...] = ()
    reporting_data: CarbonReportingData = CarbonReportingData()

    def __post_init__(self) -> None:
        for field in ("input_id", "enterprise_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise DomainValidationError(f"{field} is required")
        if self.enterprise_name is not None and (
            not isinstance(self.enterprise_name, str) or not self.enterprise_name.strip()
        ):
            raise DomainValidationError("enterprise_name must be a non-blank string when supplied")
        if not isinstance(self.period, AccountingPeriod):
            raise DomainValidationError("period must be an AccountingPeriod")
        if not isinstance(self.reporting_data, CarbonReportingData):
            raise DomainValidationError("reporting_data must be CarbonReportingData")
        if not isinstance(self.boundary_confirmed, bool):
            raise DomainValidationError("boundary_confirmed must be bool")
        object.__setattr__(self, "boundary_component_ids", tuple(self.boundary_component_ids))
        states = tuple(self.source_states)
        if any(not isinstance(item, EmissionSourceState) for item in states):
            raise DomainValidationError("source_states must contain EmissionSourceState values")
        if len({item.source_id for item in states}) != len(states):
            raise DomainValidationError("source state IDs must be unique")
        object.__setattr__(self, "source_states", states)
        for name in ("fuel_inputs", "electricity_details", "exported_electricity", "purchased_heat", "exported_heat"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for plural_name, legacy_name, expected_type, stable_name in (
            ("calcinations", "calcination", CalcinationInput, "calcination"),
            ("bakings", "baking", BakingInput, "baking"),
            ("graphitizations", "graphitization", GraphitizationInput, "graphitization"),
            ("fume_incinerations", "fume_incineration", FumeIncinerationInput, "fume"),
            ("fgd_units", "fgd", FGDInput, "fgd"),
        ):
            items = tuple(getattr(self, plural_name))
            legacy_item = getattr(self, legacy_name)
            if legacy_item is not None:
                if not isinstance(legacy_item, expected_type):
                    raise DomainValidationError(f"{legacy_name} must be a {expected_type.__name__}")
                if items and legacy_item not in items:
                    raise DomainValidationError(f"supply {plural_name} or {legacy_name}, not conflicting values")
                if not items:
                    items = (legacy_item,)
            if any(not isinstance(item, expected_type) for item in items):
                raise DomainValidationError(f"{plural_name} must contain {expected_type.__name__} values")
            instance_ids = tuple(item.instance_id for item in items)
            if len(set(instance_ids)) != len(instance_ids):
                raise DomainValidationError(f"{plural_name} instance IDs must be unique")
            object.__setattr__(self, plural_name, items)
            object.__setattr__(self, legacy_name, items[0] if items else None)
        if len({item.fuel_id for item in self.fuel_inputs}) != len(self.fuel_inputs):
            raise DomainValidationError("fuel IDs must be unique")
        if len({item.detail_id for item in self.electricity_details}) != len(self.electricity_details):
            raise DomainValidationError("electricity detail IDs must be unique")
        if len({item.line_id for item in (*self.exported_electricity, *self.purchased_heat, *self.exported_heat)}) != len((*self.exported_electricity, *self.purchased_heat, *self.exported_heat)):
            raise DomainValidationError("energy line IDs must be unique")
        input_sources = {
            "fuel_inputs": SOURCE_FUEL,
            "calcinations": SOURCE_CALCINATION,
            "bakings": SOURCE_BAKING,
            "graphitizations": SOURCE_GRAPHITIZATION,
            "fume_incinerations": SOURCE_FUME,
            "fgd_units": SOURCE_FGD,
            "electricity_details": SOURCE_PURCHASED_ELECTRICITY,
            "exported_electricity": SOURCE_EXPORTED_ELECTRICITY,
            "purchased_heat": SOURCE_PURCHASED_HEAT,
            "exported_heat": SOURCE_EXPORTED_HEAT,
        }
        for name, source_id in input_sources.items():
            activity_ids = tuple(
                item.evidence_id for item in self.reporting_data.activity_evidence
                if source_id in item.source_ids and any((item.source_reference, item.monitoring_location,
                    item.monitoring_method, item.instrument, item.accuracy, item.recording_frequency,
                    item.acquisition_time, item.note))
            )
            factor_ids = tuple(
                item.evidence_id for item in self.reporting_data.measured_factor_evidence
                if source_id in item.source_ids and any((item.source_reference, item.sampling_method,
                    item.sampling_frequency, item.testing_method, item.testing_frequency,
                    item.referenced_standard, item.reason))
            )
            object.__setattr__(
                self,
                name,
                _attach_evidence_references(getattr(self, name), activity_ids, factor_ids),
            )
        for plural_name, legacy_name in (
            ("calcinations", "calcination"), ("bakings", "baking"),
            ("graphitizations", "graphitization"), ("fume_incinerations", "fume_incineration"),
            ("fgd_units", "fgd"),
        ):
            items = getattr(self, plural_name)
            object.__setattr__(self, legacy_name, items[0] if items else None)

    def status_for(self, source_id: str, payload_present: bool) -> EmissionSourceStatus:
        explicit = next((item.status for item in self.source_states if item.source_id == source_id), None)
        if explicit is not None:
            return explicit
        return EmissionSourceStatus.INVOLVED if payload_present else EmissionSourceStatus.NOT_INVOLVED


@dataclass(frozen=True, slots=True)
class CalculationTrace:
    trace_id: str
    formula_id: str
    source_id: str
    variables: tuple[tuple[str, Decimal, str], ...]
    substitution: str
    amount: Decimal
    unit: str = "tCO2"
    instance_id: str | None = None
    standard_location: str | None = None
    mapping_location: str | None = None
    provenance: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class SteamEnthalpyEvaluation:
    value: Decimal
    reference_value: Decimal | None
    source: str
    table_id: str | None
    interpolated: bool
    pressure_bounds: tuple[Decimal, Decimal] | None = None
    temperature_bounds: tuple[Decimal, Decimal] | None = None


@dataclass(frozen=True, slots=True)
class ReportQualification:
    rule_id: str
    eligible: bool
    level: str
    code: str | None
    message: str
    scope: str = "annual_period_only"


@dataclass(frozen=True, slots=True)
class CarbonMaterialCalculationOutcome:
    input: CarbonMaterialInput
    result: CalculationResult | None
    problems: tuple[ValidationProblem, ...]
    parameter_snapshots: tuple[ParameterSnapshot, ...]
    traces: tuple[CalculationTrace, ...]
    algorithm_version: str = ALGORITHM_VERSION
    record: AccountingRecord | None = None
    report_qualification: ReportQualification | None = None

    @property
    def blocked(self) -> bool:
        return contains_errors(self.problems)

    @property
    def successful(self) -> bool:
        return not self.blocked and self.result is not None


class InMemoryRecordRepository(RecordRepository):
    """Ephemeral record store used by tests and callers without records.sqlite."""

    def __init__(self) -> None:
        self._records: dict[str, AccountingRecord] = {}
        self._deleted: set[str] = set()
        self._audit: list[dict[str, object]] = []
        self._details: dict[str, dict[str, object]] = {}
        self._detail_schema_records: set[str] = set()

    def create(self, record: AccountingRecord) -> None:
        if record.record_id in self._records:
            raise DomainValidationError(f"record already exists: {record.record_id}")
        self._records[record.record_id] = record
        self._audit.append({"record_id": record.record_id, "action": "CREATE", "actor": "system"})

    def create_with_details(
        self,
        record: AccountingRecord,
        *,
        raw_input: object | None = None,
        effective_rule_set: Sequence[str] = (),
        trace_snapshot: object | None = None,
        provenance_snapshot: object | None = None,
        reporting_snapshot: object | None = None,
        report_qualification: object | None = None,
    ) -> None:
        self.create(record)
        self._details[record.record_id] = {
            "raw_input": _snapshot_value(raw_input if raw_input is not None else record.input_snapshot),
            "effective_rule_set": {"rule_ids": tuple(sorted(set(effective_rule_set)))},
            "trace_snapshot": _snapshot_value(trace_snapshot) if trace_snapshot else None,
            "provenance_snapshot": _snapshot_value(provenance_snapshot) if provenance_snapshot else None,
            "reporting_snapshot": _snapshot_value(reporting_snapshot) if reporting_snapshot else None,
            "report_qualification": _snapshot_value(report_qualification) if report_qualification else None,
        }
        if any(value is not None for value in (
            raw_input, trace_snapshot, provenance_snapshot, reporting_snapshot, report_qualification,
        )):
            self._detail_schema_records.add(record.record_id)

    def _detail(self, record_id: str, key: str) -> dict[str, object] | None:
        details = self._details.get(record_id)
        value = details.get(key) if details else None
        return value if isinstance(value, dict) else None

    def get_raw_input_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "raw_input")

    def get_effective_rule_set(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "effective_rule_set")

    def get_trace_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "trace_snapshot")

    def get_provenance_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "provenance_snapshot")

    def get_reporting_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "reporting_snapshot")

    def get_report_qualification(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "report_qualification")

    def get_snapshot_schema_version(self, record_id: str) -> int:
        return int(record_id in self._detail_schema_records)

    def get(self, record_id: str) -> AccountingRecord | None:
        if record_id in self._deleted:
            return None
        return self._records.get(record_id)

    def list_all(self) -> tuple[AccountingRecord, ...]:
        return tuple(record for record_id, record in self._records.items() if record_id not in self._deleted)

    def delete(self, record_id: str, *, actor: str, reason: str) -> bool:
        if not actor.strip() or not reason.strip():
            raise DomainValidationError("delete actor and reason are required")
        if record_id not in self._records or record_id in self._deleted:
            return False
        self._deleted.add(record_id)
        self._audit.append({"record_id": record_id, "action": "DELETE", "actor": actor, "reason": reason})
        return True

    def list_audit(self, record_id: str | None = None) -> tuple[dict[str, object], ...]:
        if record_id is None:
            return tuple(self._audit)
        return tuple(item for item in self._audit if item.get("record_id") == record_id)


def _d(value: str | Decimal | int) -> Decimal:
    return DecimalPolicy().parse(value)


def _trace_variable(name: str, value: object) -> tuple[str, Decimal, str] | None:
    if isinstance(value, (InputValue, ParameterValue)):
        return name, value.value, value.unit
    if isinstance(value, (Decimal, int, str)) and not isinstance(value, bool):
        try:
            return name, DecimalPolicy().parse(value), ""
        except ValueError:
            return None
    return None


def _snapshot_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (Decimal, date, datetime)):
        return str(value) if isinstance(value, Decimal) else value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _snapshot_value(getattr(value, item.name)) for item in dataclass_fields(value)}
    if isinstance(value, dict):
        return {str(key): _snapshot_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_snapshot_value(item) for item in value]
    return value


_TRACE_LOCATIONS = {
    "CAR-FML-FUEL-001": ("第5.2.1条；附录C.1；附录B.2", "SM01-2026-09-13-R6 §7.2、§8、§9.2、§13.1"),
    "CAR-FML-CALCINATION-001": ("第5.2.2条；附录B.3", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-BAKING-001": ("第5.2.3条；附录B.4", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-GRAPHITIZATION-001": ("第5.2.4条；附录B.5", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-FUME-INCINERATION-001": ("第5.2.5.1条；附录B.6", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-FGD-001": ("第5.2.5.2条；附录C.2；附录B.7", "SM01-2026-09-13-R6 §7.2、§8、§9.3、§13.1"),
    "CAR-FML-GAS-CONTROL-TOTAL-001": ("第5.2.5.3条", "SM01-2026-09-13-R6 §7.2、§11"),
    "CAR-FML-PURCHASED-ELECTRICITY-001": ("第5.2.6.1条；附录B.8", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-EXPORTED-ELECTRICITY-001": ("第5.2.6.1条；附录B.8", "SM01-2026-09-13-R6 §7.2、§8、§13.1"),
    "CAR-FML-PURCHASED-HEAT-001": ("第5.2.6.2条；附录C.4/C.5；附录B.9", "SM01-2026-09-13-R6 §7.2、§8、§9.4–§9.6、§13.1"),
    "CAR-FML-EXPORTED-HEAT-001": ("第5.2.6.2条；附录C.4/C.5；附录B.9", "SM01-2026-09-13-R6 §7.2、§8、§9.4–§9.6、§13.1"),
    "CAR-FML-DIRECT-001": ("第5.2.7.1条；附录B.1", "SM01-2026-09-13-R6 §7.2、§11、§13.1"),
    "CAR-FML-INDIRECT-001": ("第5.2.7.2条；附录B.1", "SM01-2026-09-13-R6 §7.2、§11、§13.1"),
    "CAR-FML-TOTAL-001": ("第5.2.7.3条；附录B.1", "SM01-2026-09-13-R6 §7.2、§11、§13.1"),
}


def verify_record_aggregation(trace_snapshot: Mapping[str, object], calculation_snapshot: Mapping[str, object]) -> tuple[str, ...]:
    """Check saved arithmetic closure using only persisted Record values."""
    if trace_snapshot.get("trace_schema_version") != 1:
        return ("unsupported or missing trace schema version",)
    source = trace_snapshot.get("source_subtotals")
    aggregate = trace_snapshot.get("aggregations")
    if not isinstance(source, Mapping) or not isinstance(aggregate, Mapping):
        return ("saved source subtotals or aggregates are missing",)
    policy = DecimalPolicy()
    try:
        lines = calculation_snapshot.get("lines")
        if not isinstance(lines, list):
            return ("saved calculation lines are missing",)
        by_source: dict[str, Decimal] = {}
        for item in lines:
            if not isinstance(item, Mapping):
                continue
            source_id = str(item.get("emission_source_id", ""))
            by_source[source_id] = policy.add(by_source.get(source_id, Decimal("0")), str(item.get("amount")))
        line_subtotals = {
            "fuel": by_source.get(SOURCE_FUEL, Decimal("0")),
            "calcination": by_source.get(SOURCE_CALCINATION, Decimal("0")),
            "baking": by_source.get(SOURCE_BAKING, Decimal("0")),
            "graphitization": by_source.get(SOURCE_GRAPHITIZATION, Decimal("0")),
            "gas_control": policy.add(by_source.get(SOURCE_FUME, Decimal("0")), by_source.get(SOURCE_FGD, Decimal("0"))),
            "purchased_electricity": by_source.get(SOURCE_PURCHASED_ELECTRICITY, Decimal("0")),
            "purchased_heat": by_source.get(SOURCE_PURCHASED_HEAT, Decimal("0")),
            "exported_electricity": by_source.get(SOURCE_EXPORTED_ELECTRICITY, Decimal("0")),
            "exported_heat": by_source.get(SOURCE_EXPORTED_HEAT, Decimal("0")),
        }
        for key, amount in line_subtotals.items():
            if Decimal(str(source.get(key))) != amount:
                return (f"saved source subtotal {key} differs from persisted calculation lines",)
        es = Decimal("0")
        for key in ("fuel", "calcination", "baking", "graphitization", "gas_control"):
            es = policy.add(es, str(source[key]))
        ei = policy.subtract(
            policy.add(str(source["purchased_electricity"]), str(source["purchased_heat"])),
            policy.add(str(source["exported_electricity"]), str(source["exported_heat"])),
        )
        et = policy.add(es, ei)
        expected = {"ES": es, "EI": ei, "ET": et}
        for name, amount in expected.items():
            if Decimal(str(aggregate.get(name))) != amount:
                return (f"saved trace aggregate {name} does not close",)
        by_id = {str(item.get("line_id")): Decimal(str(item.get("amount"))) for item in lines if isinstance(item, Mapping)}
        stored = {
            "ES": by_id.get("CAR-FLD-DIRECT-RESULT"),
            "EI": by_id.get("CAR-FLD-INDIRECT-RESULT"),
            "ET": by_id.get("CAR-FLD-TOTAL-RESULT"),
        }
        for name, amount in expected.items():
            if stored[name] != amount:
                return (f"saved calculation result {name} differs from persisted aggregation",)
        if Decimal(str(calculation_snapshot.get("total_amount"))) != et:
            return ("saved calculation total differs from persisted ET",)
    except (KeyError, ValueError, ArithmeticError) as exc:
        return (f"saved trace contains invalid arithmetic values: {exc}",)
    return ()


def _mul(*values: str | Decimal | int) -> Decimal:
    policy = DecimalPolicy()
    result = Decimal("1")
    for value in values:
        result = policy.multiply(result, value)
    return result


def fuel_volume_emission(afv: str | Decimal | int, fcv: str | Decimal | int, fox: str | Decimal | int) -> Decimal:
    return _mul(afv, fcv, fox, Decimal(44) / Decimal(12))


def fuel_mass_emission(afm: str | Decimal | int, fcm: str | Decimal | int, fox: str | Decimal | int) -> Decimal:
    return _mul(afm, fcm, fox, Decimal(44) / Decimal(12))


def fuel_heat_emission(afh: str | Decimal | int, fch: str | Decimal | int, fox: str | Decimal | int) -> Decimal:
    return _mul(afh, fch, fox, Decimal(44) / Decimal(12))


def fuel_energy_from_volume(afv: str | Decimal | int, hv: str | Decimal | int) -> Decimal:
    return _mul(afv, hv)


def fuel_energy_from_mass(afm: str | Decimal | int, hm: str | Decimal | int) -> Decimal:
    return _mul(afm, hm)


def calcination_emission(gc: object, wfc: object, cc: object, ucc: object, du: object, wfc_c: object, wvar: object, wvar_c: object, k1: object) -> Decimal:
    fixed = (_d(gc) * _d(wfc) - (_d(cc) + _d(ucc) + _d(du)) * _d(wfc_c)) * Decimal(44) / Decimal(12)
    methane_carbon = (_d(gc) * _d(wvar) - _d(cc) * _d(wvar_c)) * _d(k1) * Decimal(44) / Decimal(16)
    return fixed + methane_carbon


def baking_emission(bpm: object, bpmfc: object, bg: object, bgfc: object, bwt: object, bp: object, bpfc: object, bpmvar: object, bgvar: object, k2: object) -> Decimal:
    fixed = (_d(bpm) * _d(bpmfc) + _d(bg) * _d(bgfc) - _d(bwt) - _d(bp) * _d(bpfc)) * Decimal(44) / Decimal(12)
    methane_carbon = (_d(bpm) * _d(bpmvar) + _d(bg) * _d(bgvar)) * _d(k2) * Decimal(44) / Decimal(16)
    return fixed + methane_carbon


def graphitization_emission(gpm: object, gpmfc: object, gta: object, gtafc: object, gwt: object, gp: object, gpfc: object, gpmvar: object, k3: object) -> Decimal:
    fixed = (_d(gpm) * _d(gpmfc) + _d(gta) * _d(gtafc) - _d(gwt) - _d(gp) * _d(gpfc)) * Decimal(44) / Decimal(12)
    methane_carbon = _d(gpm) * _d(gpmvar) * _d(k3) * Decimal(44) / Decimal(16)
    return fixed + methane_carbon


def fume_incineration_emission(q: object, qvar: object, hm: object, fch: object, fox: object, duration: object) -> Decimal:
    return _mul(q, qvar, hm, fch, fox, duration, 24, Decimal(44) / Decimal(12), Decimal("1e-9"))


def fgd_emission(components: Sequence[CarbonateComponent] | Sequence[tuple[object, object, object, object]]) -> Decimal:
    total = Decimal("0")
    for component in components:
        if isinstance(component, CarbonateComponent):
            values = (component.amount, component.carbonate_fraction, component.emission_factor, component.conversion_rate)
        else:
            values = component
        total += _mul(values[0].value if isinstance(values[0], InputValue) else values[0], values[1].value if isinstance(values[1], InputValue) else values[1], values[2].value if isinstance(values[2], ParameterValue) else values[2], values[3].value if isinstance(values[3], InputValue) else values[3])
    return total


def purchased_electricity_emission(quantity_mwh: object, factor: object) -> Decimal:
    return _mul(quantity_mwh, factor)


def purchased_heat_emission(quantity_kg: object, enthalpy_kj_per_kg: object, factor_tco2_per_gj: object) -> Decimal:
    return _mul(quantity_kg, enthalpy_kj_per_kg, factor_tco2_per_gj, Decimal("1e-6"))


def direct_emission(fuel: object, calcination: object, baking: object, graphitization: object, gas_control: object) -> Decimal:
    return _d(fuel) + _d(calcination) + _d(baking) + _d(graphitization) + _d(gas_control)


def indirect_emission(purchased_electricity: object, purchased_heat: object, exported_electricity: object, exported_heat: object) -> Decimal:
    return _d(purchased_electricity) + _d(purchased_heat) - _d(exported_electricity) - _d(exported_heat)


def total_emission(direct: object, indirect: object) -> Decimal:
    return _d(direct) + _d(indirect)


_SATURATED_STEAM = (
    (Decimal("0.001"), Decimal("2513.8")), (Decimal("0.002"), Decimal("2533.2")),
    (Decimal("0.003"), Decimal("2545.2")), (Decimal("0.004"), Decimal("2554.1")),
    (Decimal("0.005"), Decimal("2561.2")), (Decimal("0.007"), Decimal("2572.2")),
    (Decimal("0.008"), Decimal("2576.7")), (Decimal("0.009"), Decimal("2580.8")),
    (Decimal("0.010"), Decimal("2584.4")), (Decimal("0.015"), Decimal("2598.9")),
    (Decimal("0.020"), Decimal("2609.6")), (Decimal("0.025"), Decimal("2618.1")),
    (Decimal("0.030"), Decimal("2625.3")), (Decimal("0.040"), Decimal("2636.8")),
    (Decimal("0.050"), Decimal("2645.0")), (Decimal("0.060"), Decimal("2653.6")),
    (Decimal("0.070"), Decimal("2660.2")), (Decimal("0.080"), Decimal("2666.0")),
    (Decimal("0.090"), Decimal("2671.1")), (Decimal("0.10"), Decimal("2675.7")),
    (Decimal("0.12"), Decimal("2683.8")), (Decimal("0.14"), Decimal("2690.8")),
    (Decimal("0.16"), Decimal("2696.8")), (Decimal("0.18"), Decimal("2702.1")),
    (Decimal("0.20"), Decimal("2706.9")), (Decimal("0.25"), Decimal("2717.2")),
    (Decimal("0.30"), Decimal("2725.5")), (Decimal("0.35"), Decimal("2732.5")),
    (Decimal("0.40"), Decimal("2738.5")), (Decimal("0.45"), Decimal("2743.8")),
    (Decimal("0.50"), Decimal("2748.5")), (Decimal("0.60"), Decimal("2756.4")),
    (Decimal("0.70"), Decimal("2762.9")), (Decimal("0.80"), Decimal("2768.4")),
    (Decimal("0.90"), Decimal("2773.0")), (Decimal("1.00"), Decimal("2777.0")),
    (Decimal("1.10"), Decimal("2780.4")), (Decimal("1.20"), Decimal("2783.4")),
    (Decimal("1.30"), Decimal("2786.0")), (Decimal("1.40"), Decimal("2788.4")),
    (Decimal("1.60"), Decimal("2792.2")), (Decimal("1.70"), Decimal("2793.8")),
    (Decimal("1.80"), Decimal("2795.1")), (Decimal("1.90"), Decimal("2796.4")),
    (Decimal("2.00"), Decimal("2797.4")), (Decimal("2.20"), Decimal("2799.1")),
    (Decimal("2.40"), Decimal("2800.4")), (Decimal("2.60"), Decimal("2801.2")),
    (Decimal("2.80"), Decimal("2801.7")), (Decimal("3.00"), Decimal("2801.9")),
    (Decimal("3.50"), Decimal("2801.3")), (Decimal("4.00"), Decimal("2799.4")),
    (Decimal("5.00"), Decimal("2792.8")), (Decimal("6.00"), Decimal("2783.3")),
    (Decimal("7.00"), Decimal("2771.4")), (Decimal("8.00"), Decimal("2757.5")),
    (Decimal("9.00"), Decimal("2741.8")), (Decimal("10.0"), Decimal("2724.4")),
    (Decimal("11.0"), Decimal("2705.4")), (Decimal("12.0"), Decimal("2684.8")),
    (Decimal("13.0"), Decimal("2662.4")), (Decimal("14.0"), Decimal("2638.3")),
    (Decimal("15.0"), Decimal("2611.6")), (Decimal("16.0"), Decimal("2582.7")),
    (Decimal("17.0"), Decimal("2550.8")), (Decimal("18.0"), Decimal("2514.4")),
    (Decimal("19.0"), Decimal("2470.1")), (Decimal("20.0"), Decimal("2413.9")),
    (Decimal("21.0"), Decimal("2340.2")), (Decimal("22.0"), Decimal("2192.5")),
)

_SUPERHEATED_PRESSURES = tuple(
    Decimal(value) for value in ("0.01", "0.1", "0.5", "1", "3", "5", "7", "10", "14", "20", "25", "30")
)
_SUPERHEATED_STEAM = tuple(
    (Decimal(temperature), tuple(Decimal(value) for value in values.split()))
    for temperature, values in (
        ("0", "0 0.1 0.5 1 3 5 7.1 10.1 14.1 20.1 25.1 30"),
        ("10", "42 42.1 42.5 43 44.9 46.9 48.8 51.7 55.6 61.3 66.1 70.8"),
        ("20", "83.9 84 84.3 84.8 86.7 88.6 90.4 93.2 97 102.5 107.1 111.7"),
        ("40", "167.4 167.5 167.9 168.3 170.1 171.9 173.6 176.3 179.8 185.1 189.4 193.8"),
        ("60", "2611.3 251.2 251.2 251.9 253.6 255.3 256.9 259.4 262.8 267.8 272 276.1"),
        ("80", "2649.3 335 335.3 335.7 337.3 338.8 340.4 342.8 346 350.8 354.8 358.7"),
        ("100", "2687.3 2676.5 419.4 419.7 421.2 422.7 424.2 426.5 429.5 434 437.8 441.6"),
        ("120", "2725.4 2716.8 503.9 504.3 505.7 507.1 508.5 510.6 513.5 517.7 521.3 524.9"),
        ("140", "2763.6 2756.6 589.2 589.5 590.8 592.1 593.4 595.4 598 602 605.4 603.1"),
        ("160", "2802 2796.2 2767.3 675.7 676.9 678 679.2 681 683.4 687.1 690.2 693.3"),
        ("180", "2840.6 2835.7 2812.1 2777.3 764.1 765.2 766.2 767.8 769.9 773.1 775.9 778.7"),
        ("200", "2879.3 2875.2 2855.5 2827.5 853 853.8 854.6 855.9 857.7 860.4 862.8 856.2"),
        ("220", "2918.3 2914.7 2898 2874.9 943.9 944.4 945.0 946 947.2 949.3 951.2 953.1"),
        ("240", "2957.4 2954.3 2939.9 2920.5 2823 1037.8 1038.0 1038.4 1039.1 1040.3 1041.5 1024.8"),
        ("260", "2996.8 2994.1 2981.5 2964.8 2885.5 1135 1134.7 1134.3 1134.1 1134 1134.3 1134.8"),
        ("280", "3036.5 3034 3022.9 3008.3 2941.8 2857 1236.7 1235.2 1233.5 1231.6 1230.5 1229.9"),
        ("300", "3076.3 3074.1 3064.2 3051.3 2994.2 2925.4 2839.2 1343.7 1339.5 1334.6 1331.5 1329"),
        ("350", "3177 3175.3 3167.6 3157.7 3115.7 3069.2 3017.0 2924.2 2753.5 1648.4 1626.4 1611.3"),
        ("400", "3279.4 3278 3217.8 3264 3231.6 3196.9 3159.7 3098.5 3004 2820.1 2583.2 2159.1"),
        ("420", "3320.96 3319.68 3313.8 3306.6 3276.9 3245.4 3211.0 3155.98 3072.72 2917.02 2730.76 2424.7"),
        ("440", "3362.52 3361.36 3355.9 3349.3 3321.9 3293.2 3262.3 3213.46 3141.44 3013.94 2878.32 2690.3"),
        ("450", "3383.3 3382.2 3377.1 3370.7 3344.4 3316.8 3288.0 3242.2 3175.8 3062.4 2952.1 2823.1"),
        ("460", "3404.42 3403.34 3398.3 3392.1 3366.8 3340.4 3312.4 3268.58 3205.24 3097.96 2994.68 2875.26"),
        ("480", "3446.66 3445.62 3440.9 3435.1 3411.6 3387.2 3361.3 3321.34 3264.12 3169.08 3079.84 2979.58"),
        ("500", "3488.9 3487.9 3483.7 3478.3 3456.4 3433.8 3410.2 3374.1 3323 3240.2 3165 3083.9"),
        ("520", "3531.82 3530.9 3526.9 3521.86 3501.28 3480.12 3458.6 3425.1 3378.4 3303.7 3237 3166.1"),
        ("540", "3574.74 3573.9 3570.1 3565.42 3546.16 3526.44 3506.4 3475.4 3432.5 3364.6 3304.7 3241.7"),
        ("550", "3593.2 3595.4 3591.7 3587.2 3568.6 3549.6 3530.2 3500.4 3459.2 3394.3 3337.3 3277.7"),
        ("560", "3618 3617.22 3613.64 3609.24 3591.18 3572.76 3554.1 3525.4 3485.8 3423.6 3369.2 3312.6"),
        ("580", "3661.6 3660.86 3657.52 3653.32 3636.34 3619.08 3601.6 3574.9 3538.2 3480.9 3431.2 3379.8"),
        ("600", "3705.2 3704.5 3701.4 3697.4 3681.5 3665.4 3649.0 3624 3589.8 3536.9 3491.2 3444.2"),
    )
)


def _bracket(value: Decimal, keys: Sequence[Decimal]) -> tuple[int, int, bool]:
    if value < keys[0] or value > keys[-1]:
        raise ValueError("steam state is outside the C.5 table")
    for index, key in enumerate(keys):
        if value == key:
            return index, index, True
        if value < key:
            return index - 1, index, False
    raise ValueError("steam state is outside the C.5 table")


def _linear_interpolate(
    value: Decimal,
    low_key: Decimal,
    high_key: Decimal,
    low_value: Decimal,
    high_value: Decimal,
    *,
    policy: DecimalPolicy,
) -> Decimal:
    if low_key == high_key:
        return low_value
    position = policy.divide(policy.subtract(value, low_key), policy.subtract(high_key, low_key))
    delta = policy.subtract(high_value, low_value)
    return policy.add(low_value, policy.multiply(position, delta))


def superheated_steam_enthalpy(
    pressure_mpa: object,
    temperature_c: object,
    *,
    policy: DecimalPolicy | None = None,
) -> tuple[Decimal, bool, tuple[Decimal, Decimal]]:
    profile = policy or DecimalPolicy()
    pressure = _d(pressure_mpa)
    temperature = _d(temperature_c)
    pressure_low, pressure_high, pressure_exact = _bracket(pressure, _SUPERHEATED_PRESSURES)
    temperatures = tuple(row[0] for row in _SUPERHEATED_STEAM)
    temperature_low, temperature_high, temperature_exact = _bracket(temperature, temperatures)
    if pressure_exact and temperature_exact:
        return _SUPERHEATED_STEAM[temperature_low][1][pressure_low], False, (pressure, pressure)
    low_row = _linear_interpolate(
        pressure,
        _SUPERHEATED_PRESSURES[pressure_low],
        _SUPERHEATED_PRESSURES[pressure_high],
        _SUPERHEATED_STEAM[temperature_low][1][pressure_low],
        _SUPERHEATED_STEAM[temperature_low][1][pressure_high],
        policy=profile,
    )
    if temperature_exact:
        return low_row, True, (_SUPERHEATED_PRESSURES[pressure_low], _SUPERHEATED_PRESSURES[pressure_high])
    high_row = _linear_interpolate(
        pressure,
        _SUPERHEATED_PRESSURES[pressure_low],
        _SUPERHEATED_PRESSURES[pressure_high],
        _SUPERHEATED_STEAM[temperature_high][1][pressure_low],
        _SUPERHEATED_STEAM[temperature_high][1][pressure_high],
        policy=profile,
    )
    return _linear_interpolate(
        temperature,
        temperatures[temperature_low],
        temperatures[temperature_high],
        low_row,
        high_row,
        policy=profile,
    ), True, (_SUPERHEATED_PRESSURES[pressure_low], _SUPERHEATED_PRESSURES[pressure_high])


def saturated_steam_enthalpy(
    pressure_mpa: object,
    *,
    policy: DecimalPolicy | None = None,
) -> tuple[Decimal, bool, tuple[Decimal, Decimal]]:
    profile = policy or DecimalPolicy()
    pressure = _d(pressure_mpa)
    for key, enthalpy in _SATURATED_STEAM:
        if pressure == key:
            return enthalpy, False, (key, key)
    for (low_pressure, low_enthalpy), (high_pressure, high_enthalpy) in zip(_SATURATED_STEAM, _SATURATED_STEAM[1:]):
        if low_pressure <= pressure <= high_pressure:
            pressure_delta = profile.subtract(pressure, low_pressure)
            span = profile.subtract(high_pressure, low_pressure)
            ratio = profile.divide(pressure_delta, span)
            enthalpy_delta = profile.subtract(high_enthalpy, low_enthalpy)
            return profile.add(low_enthalpy, profile.multiply(ratio, enthalpy_delta)), True, (low_pressure, high_pressure)
    raise ValueError("steam pressure is outside the C.4 table")


def steam_reference_table_rows(table_id: str) -> tuple[tuple[Decimal, ...], ...]:
    """Return read-only projections of the Calculator's versioned C.4/C.5 tables."""

    if table_id == "C.4":
        return tuple((pressure, enthalpy) for pressure, enthalpy in _SATURATED_STEAM)
    if table_id == "C.5":
        return tuple(
            (temperature, pressure, enthalpy)
            for temperature, enthalpies in _SUPERHEATED_STEAM
            for pressure, enthalpy in zip(_SUPERHEATED_PRESSURES, enthalpies)
        )
    raise ValueError("table_id must be C.4 or C.5")


def _problem(code: str, level: IssueLevel, message: str, field_id: str | None = None, details: tuple[tuple[str, str], ...] = ()) -> ValidationProblem:
    return ValidationProblem(code, level, message, field_id, details)


def _parameter_method(source_kind: ParameterSourceKind) -> ParameterSelectionMethod:
    return {
        ParameterSourceKind.STANDARD_DEFAULT: ParameterSelectionMethod.STANDARD_REQUIRED,
        ParameterSourceKind.STANDARD_SPECIFIED: ParameterSelectionMethod.STANDARD_REQUIRED,
        ParameterSourceKind.MEASURED: ParameterSelectionMethod.ENTERPRISE_MEASURED,
        ParameterSourceKind.CALCULATED: ParameterSelectionMethod.DERIVED,
        ParameterSourceKind.OFFICIAL_PUBLISHED: ParameterSelectionMethod.SYSTEM_RECOMMENDED,
        ParameterSourceKind.USER_DEFINED: ParameterSelectionMethod.MANUAL_OVERRIDE,
        ParameterSourceKind.PROJECT_SPECIFIED: ParameterSelectionMethod.MANUAL_OVERRIDE,
    }[source_kind]


class CarbonMaterialCalculator:
    """Calculate the frozen ten-source GB/T 32151.34 model in memory."""

    def __init__(
        self,
        *,
        parameter_resolver: ParameterResolver | None = None,
        record_repository: RecordRepository | None = None,
        standard_version: str = STANDARD_VERSION,
        policy: DecimalPolicy | None = None,
        unit_service: UnitService | None = None,
        reference_data_identity_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        self.policy = policy or DecimalPolicy()
        self.units = unit_service or UnitService(self.policy)
        self.parameter_resolver = parameter_resolver
        self.record_repository = record_repository or InMemoryRecordRepository()
        self.standard_version = standard_version
        self.reference_data_identity_provider = reference_data_identity_provider
        self._effective_rule_ids: set[str] = set()

    @staticmethod
    def _report_qualification(period: AccountingPeriod) -> ReportQualification:
        if period.period_type is PeriodType.ANNUAL:
            return ReportQualification(
                "CAR-VAL-ANNUAL-REPORT-PERIOD", True, "INFO", None,
                "核算期间为完整年度，可进入年度标准报告资格检查。",
            )
        return ReportQualification(
            "CAR-VAL-ANNUAL-REPORT-PERIOD", False, "ERROR",
            "CAR-VAL-ANNUAL-REPORT-PERIOD",
            "月度或自定义期间可以核算和保存记录，但不符合标准年度报告周期。",
        )

    def _effective_rule_snapshot(self) -> dict[str, object]:
        configured = getattr(self.parameter_resolver, "rule_definitions", ()) if self.parameter_resolver else ()
        selected = tuple(rule for rule in configured if rule.rule_id in self._effective_rule_ids)
        body = {
            "rule_ids": tuple(sorted(self._effective_rule_ids)),
            "rules": _snapshot_value(selected),
        }
        stable = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return body | {"snapshot_identity": hashlib.sha256(stable.encode("utf-8")).hexdigest()}

    def _reference_data_snapshot(self, parameter_snapshots: Sequence[ParameterSnapshot]) -> dict[str, object]:
        if self.reference_data_identity_provider is None:
            resolved = _snapshot_value(tuple(parameter_snapshots))
            serialized = json.dumps(resolved, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            return {
                "status": "CAPTURED" if parameter_snapshots else "NO_REFERENCED_PARAMETERS",
                "identity_scope": "resolved_record_parameter_snapshots",
                "content_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            }
        try:
            return {"status": "CAPTURED", **dict(self.reference_data_identity_provider())}
        except Exception as exc:  # a missing optional catalog must not hide calculator outcomes
            resolved = _snapshot_value(tuple(parameter_snapshots))
            serialized = json.dumps(resolved, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            return {
                "status": "FALLBACK_TO_RESOLVED_PARAMETERS",
                "identity_scope": "resolved_record_parameter_snapshots",
                "content_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
                "reason": type(exc).__name__,
            }

    def _provenance_snapshot(
        self,
        record: AccountingRecord,
        rule_snapshot: dict[str, object],
        parameter_snapshots: Sequence[ParameterSnapshot],
    ) -> dict[str, object]:
        return {
            "provenance_schema_version": 1,
            "standard": {"standard_id": record.standard_id, "version": record.standard_version},
            "mapping": {"version": MAPPING_VERSION, "status": "FROZEN"},
            "calculator": {"algorithm_version": record.algorithm_version},
            "effective_rule_set": rule_snapshot,
            "reference_data": self._reference_data_snapshot(parameter_snapshots),
            "numeric_provenance": {
                "contract": "Qingzhou Numeric Contract v1 (project compatibility/adoption)",
                "profile_id": "GHGTOOL_CARBON_DECIMAL40_CURRENT",
                "precision": self.policy.precision,
                "rounding": self.policy.rounding,
                "display_places": self.policy.display_places,
                "formal_comparison": "full-value exact comparison",
                "business_epsilon": None,
            },
        }

    def _trace_snapshot(
        self,
        record: AccountingRecord,
        traces: Sequence[CalculationTrace],
        parameter_snapshots: Sequence[ParameterSnapshot],
        source_subtotals: Mapping[str, Decimal],
    ) -> dict[str, object]:
        steps: list[dict[str, object]] = []
        configured_rules = getattr(self.parameter_resolver, "rule_definitions", ()) if self.parameter_resolver else ()
        rule_definitions = {rule.rule_id: rule for rule in configured_rules}
        for trace in traces:
            standard_location, mapping_location = _TRACE_LOCATIONS.get(
                trace.formula_id, (trace.standard_location or "", trace.mapping_location or "")
            )
            instance_id = trace.instance_id
            related_parameters = [
                item for item in parameter_snapshots
                if self._parameter_belongs_to_trace(item.detail_id, trace.formula_id, trace.trace_id, instance_id)
            ]
            rule_ids = [trace.source_id] if trace.source_id.startswith("CAR-RULE-") else sorted(self._effective_rule_ids)
            rule_references = [
                {
                    "rule_id": rule_id,
                    "source_location": (
                        rule_definitions[rule_id].source_location
                        if rule_id in rule_definitions
                        else standard_location
                    ),
                    "mapping_location": mapping_location,
                }
                for rule_id in rule_ids
            ]
            steps.append({
                "trace_id": trace.trace_id,
                "process_instance_id": instance_id,
                "formula_id": trace.formula_id,
                "emission_source_id": trace.source_id,
                "input_variables": [
                    {"name": name, "value": str(value), "unit": unit}
                    for name, value, unit in trace.variables
                ],
                "parameter_references": _snapshot_value(tuple(related_parameters)),
                "rule_references": rule_references,
                "intermediate_result": str(trace.amount),
                "unit": trace.unit,
                "calculation_step": trace.substitution,
                "calculation_provenance": dict(trace.provenance),
                "standard_location": trace.standard_location or standard_location,
                "mapping_location": trace.mapping_location or mapping_location,
            })
        direct = Decimal("0")
        for key in ("fuel", "calcination", "baking", "graphitization", "gas_control"):
            direct = self.policy.add(direct, source_subtotals[key])
        indirect = self.policy.subtract(
            self.policy.add(source_subtotals["purchased_electricity"], source_subtotals["purchased_heat"]),
            self.policy.add(source_subtotals["exported_electricity"], source_subtotals["exported_heat"]),
        )
        total = self.policy.add(direct, indirect)
        return {
            "trace_schema_version": 1,
            "standard_id": record.standard_id,
            "standard_version": record.standard_version,
            "mapping_version": MAPPING_VERSION,
            "calculated_at": record.created_at.isoformat(),
            "formula_steps": steps,
            "parameter_snapshots": _snapshot_value(tuple(parameter_snapshots)),
            "effective_rule_ids": sorted(self._effective_rule_ids),
            "source_subtotals": {key: str(value) for key, value in source_subtotals.items()},
            "aggregations": {"ES": str(direct), "EI": str(indirect), "ET": str(total)},
            "calculation_lines": _snapshot_value(record.calculation_result.lines),
        }

    @staticmethod
    def _parameter_belongs_to_trace(
        detail_id: str | None,
        formula_id: str,
        trace_id: str,
        instance_id: str | None,
    ) -> bool:
        """Associate snapshots by their full detail identity, never a substring."""

        if not detail_id:
            return False
        if detail_id == trace_id:
            return True
        if instance_id is None:
            return False
        exact_prefixes = {
            "CAR-FML-FUEL-001": (f"CAR-FLD-F01-{instance_id}-",),
            "CAR-FML-CALCINATION-001": (f"CAR-FLD-P01-RESULT-{instance_id}-",),
            "CAR-FML-BAKING-001": (f"CAR-FLD-P02-RESULT-{instance_id}-",),
            "CAR-FML-GRAPHITIZATION-001": (f"CAR-FLD-P03-RESULT-{instance_id}-",),
            "CAR-FML-FUME-INCINERATION-001": (f"CAR-FLD-P04A-{instance_id}-",),
            "CAR-FML-FGD-001": (f"CAR-FLD-P04B-{instance_id}-",),
            "CAR-FML-EXPORTED-ELECTRICITY-001": (f"CAR-FLD-POWER-EXPORTED-EF.{instance_id}",),
            "CAR-FML-PURCHASED-HEAT-001": (f"CAR-FLD-HEAT-{instance_id}-",),
            "CAR-FML-EXPORTED-HEAT-001": (f"CAR-FLD-HEAT-{instance_id}-",),
        }.get(formula_id, ())
        if formula_id == "CAR-FML-EXPORTED-ELECTRICITY-001":
            prefix = exact_prefixes[0]
            return detail_id == prefix or detail_id.startswith(prefix + "-")
        return any(detail_id.startswith(prefix) for prefix in exact_prefixes)

    def _quantity(self, value: InputValue | None, expected_unit: str, field_id: str, problems: list[ValidationProblem], *, nonnegative: bool = True) -> Decimal | None:
        if value is None:
            problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, f"缺少必填字段 {field_id}。", field_id))
            return None
        try:
            if nonnegative and value.value < 0:
                problems.append(_problem("CAR-VAL-NONNEGATIVE", IssueLevel.ERROR, f"字段 {field_id} 不得为负数。", field_id))
            if value.unit != expected_unit:
                converted = self.units.convert(value.value, value.unit, expected_unit)
            else:
                converted = value.value
            if value.source_level is ActivitySourceLevel.PROXY:
                problems.append(_problem("GEN-VAL-PROXY-DATA", IssueLevel.WARNING, f"字段 {field_id} 使用替代数据。", field_id))
            return converted
        except (UnitError, ValueError) as exc:
            problems.append(_problem("GEN-VAL-UNIT-INCOMPATIBLE", IssueLevel.ERROR, f"字段 {field_id} 单位 {value.unit} 无法转换为 {expected_unit}：{exc}", field_id))
            return None

    def _ratio(self, value: InputValue | None, field_id: str, problems: list[ValidationProblem], *, required: bool = True) -> Decimal | None:
        if value is None:
            if required:
                problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, f"缺少百分比/比例字段 {field_id}。", field_id))
            return None
        try:
            converted = self.units.convert(value.value, value.unit, "ratio") if value.unit != "ratio" else value.value
        except (UnitError, ValueError) as exc:
            problems.append(_problem("GEN-VAL-UNIT-INCOMPATIBLE", IssueLevel.ERROR, f"字段 {field_id} 不是可识别的比例：{exc}", field_id))
            return None
        if not Decimal("0") <= converted <= Decimal("1"):
            problems.append(_problem("CAR-VAL-PERCENT-RANGE", IssueLevel.ERROR, f"字段 {field_id} 必须处于 0% 到 100% 范围内。", field_id))
        return converted

    @staticmethod
    def _check_parameter_semantics(value: Decimal, expected_unit: str, field_id: str, problems: list[ValidationProblem]) -> None:
        """Apply the one Domain gate for numeric ParameterValues, regardless of provenance."""
        if expected_unit == "ratio":
            if not Decimal("0") <= value <= Decimal("1"):
                problems.append(_problem("CAR-VAL-PARAMETER-RATIO-RANGE", IssueLevel.ERROR, f"参数 {field_id} 必须处于 0 到 1 之间。", field_id))
            return
        nonnegative_units = {
            "tC/GJ", "tC/t", "tC/10^4Nm3", "tCO2/GJ", "tCO2/t",
            "tCO2/MWh", "tCO₂/MWh", "GJ", "GJ/t", "GJ/10⁴Nm³", "GJ/GJ", "kJ/kg",
        }
        if expected_unit in nonnegative_units and value < 0:
            problems.append(_problem("CAR-VAL-PARAMETER-NONNEGATIVE", IssueLevel.ERROR, f"参数 {field_id} 不得为负数。", field_id))

    def _parameter(self, value: ParameterValue | None, expected_unit: str, field_id: str, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime, *, required: bool = True) -> Decimal | None:
        if value is None:
            if required:
                problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, f"缺少参数 {field_id}。", field_id))
            return None
        try:
            converted = self.units.convert(value.value, value.unit, expected_unit) if value.unit != expected_unit else value.value
        except (UnitError, ValueError) as exc:
            problems.append(_problem("GEN-VAL-UNIT-INCOMPATIBLE", IssueLevel.ERROR, f"参数 {field_id} 单位 {value.unit} 无法转换为 {expected_unit}：{exc}", field_id))
            return None
        try:
            self._check_parameter_semantics(converted, expected_unit, field_id, problems)
            if value.source_id is None or value.source_version is None or value.source_location is None:
                problems.append(_problem("CAR-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {field_id} 缺少来源、版本或定位。", field_id))
            snapshot_id = f"{field_id}.parameter-snapshot"
            snapshots.append(
                ParameterSnapshot(
                    snapshot_id=snapshot_id,
                    parameter_id=value.parameter_id,
                    factor_id=value.factor_id,
                    value_used=converted,
                    unit_used=expected_unit,
                    source_id=value.source_id,
                    source_version=value.source_version,
                    selection_method=_parameter_method(value.source_kind),
                    selection_reason=value.selection_reason,
                    standard_id=STANDARD_ID,
                    snapshot_at=snapshot_at,
                    factor_version=value.source_version,
                    source_location=value.source_location,
                    factor_year=value.factor_year,
                    detail_id=field_id,
                    evidence_ref_ids=value.evidence_ref_ids,
                )
            )
            if value.source_kind is ParameterSourceKind.USER_DEFINED:
                problems.append(_problem("GEN-VAL-CUSTOM-FACTOR", IssueLevel.WARNING, f"参数 {field_id} 使用用户自定义值。", field_id))
            if value.source_kind is ParameterSourceKind.MEASURED and value.source_location is None:
                problems.append(_problem("GEN-VAL-MEASURED-NO-TEST-INFO", IssueLevel.WARNING, f"参数 {field_id} 缺少检测/取样信息。", field_id))
            return converted
        except DomainValidationError as exc:
            problems.append(_problem("GEN-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {field_id} 无法形成快照：{exc}", field_id))
            return None

    def _basis(self, item: object, field_id: str, problems: list[ValidationProblem]) -> None:
        mass_basis = getattr(item, "mass_basis")
        composition_basis = getattr(item, "composition_basis")
        normalized = getattr(item, "normalized_basis")
        fixed_kind = getattr(item, "fixed_carbon_component_kind", getattr(item, "component_kind"))
        volatile_kind = getattr(item, "volatile_matter_component_kind", MaterialComponentKind.VOLATILE_MATTER)
        if fixed_kind is not MaterialComponentKind.FIXED_CARBON:
            problems.append(_problem("CAR-VAL-MATERIAL-COMPONENT-KIND", IssueLevel.ERROR, f"{field_id} 的固定碳字段性质必须为 FIXED_CARBON。", f"{field_id}.fixed-carbon"))
        if volatile_kind is not MaterialComponentKind.VOLATILE_MATTER:
            problems.append(_problem("CAR-VAL-MATERIAL-COMPONENT-KIND", IssueLevel.ERROR, f"{field_id} 的挥发分字段性质必须为 VOLATILE_MATTER。", f"{field_id}.volatile-matter"))
        if mass_basis is MaterialBasis.UNKNOWN or composition_basis is MaterialBasis.UNKNOWN or mass_basis is not composition_basis:
            problems.append(_problem("CAR-VAL-MATERIAL-BASIS-CONSISTENCY", IssueLevel.ERROR, f"{field_id} 的物料和成分基准未知或不一致。", field_id))
        elif mass_basis is not MaterialBasis.RECEIVED:
            if not getattr(item, "moisture_evidence") or not getattr(item, "conversion_evidence") or normalized is not MaterialBasis.RECEIVED:
                problems.append(_problem("CAR-VAL-MATERIAL-BASIS-CONVERSION", IssueLevel.ERROR, f"{field_id} 非收到基数据缺少水分/换算证据或未归一为收到基。", field_id))

    def _required_parameter(self, item: object, attr: str, parameter_id: str, field_id: str, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime) -> Decimal | None:
        value = getattr(item, attr)
        if value is None:
            problems.append(_problem("GEN-PAR-STANDARD-DEFAULT-MISSING", IssueLevel.ERROR, f"缺少已核验的标准缺省参数 {parameter_id}。", field_id))
            return None
        return self._parameter(value, "ratio", field_id, snapshots, problems, snapshot_at)

    def _resolve_parameter(self, context: ParameterResolutionContext, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime, *, detail_id: str | None = None) -> Decimal | None:
        if self.parameter_resolver is None:
            problems.append(_problem("CAR-VAL-PARAMETER-RESOLVER-MISSING", IssueLevel.ERROR, f"参数 {context.parameter_id} 没有接入 G05 参数解析服务。", context.parameter_id))
            return None
        resolution = self.parameter_resolver.resolve(context)
        self._effective_rule_ids.update(resolution.effective_rules.rule_ids)
        problems.extend(resolution.warnings)
        if resolution.blocked or resolution.recommended is None or resolution.selection_method is None:
            return None
        try:
            snapshot = resolution.to_snapshot(f"{detail_id or context.parameter_id}.parameter-snapshot", snapshot_at, detail_id=detail_id)
            snapshots.append(snapshot)
        except DomainValidationError as exc:
            problems.append(_problem("GEN-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {context.parameter_id} 无法形成快照：{exc}", context.parameter_id))
            return None
        factor = resolution.recommended.factor
        self._check_parameter_semantics(factor.value, factor.unit, context.parameter_id, problems)
        return factor.value

    @staticmethod
    def _map_electricity_resolution_problems(
        detail_id: str,
        resolution_problems: Sequence[ValidationProblem],
    ) -> tuple[ValidationProblem, ...]:
        """Translate the generic G05 proof gate into the frozen G06 code."""

        return tuple(
            ValidationProblem(
                GREEN_ELECTRICITY_EVIDENCE_CODE,
                problem.level,
                problem.message,
                detail_id,
                problem.details,
            )
            if problem.code == "GEN-VAL-NONFOSSIL-EVIDENCE"
            else problem
            for problem in resolution_problems
        )

    def _source_check(self, input_value: CarbonMaterialInput, source_id: str, payload_present: bool, problems: list[ValidationProblem]) -> EmissionSourceStatus:
        status = input_value.status_for(source_id, payload_present)
        if status is EmissionSourceStatus.UNCONFIRMED:
            problems.append(_problem("GEN-VAL-SOURCE-UNCONFIRMED", IssueLevel.ERROR, f"排放源 {source_id} 尚未确认是否涉及。", source_id))
        if status is EmissionSourceStatus.NOT_INVOLVED and payload_present:
            problems.append(_problem("CAR-VAL-SOURCE-CONFLICT", IssueLevel.ERROR, f"排放源 {source_id} 标记为不涉及但仍有输入。", source_id))
        if status is EmissionSourceStatus.INVOLVED and not payload_present:
            problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, f"排放源 {source_id} 已标记涉及但缺少输入。", source_id))
        return status

    def _fuel(self, item: FuelInput, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime) -> Decimal | None:
        activity = self._quantity(item.activity, {FuelPath.VOLUME: "ten_thousand_Nm3", FuelPath.MASS: "t", FuelPath.HEAT: "GJ"}[item.path], f"CAR-FLD-F01-{item.fuel_id}-ACTIVITY", problems)
        if item.lower_heating_value is not None:
            lhv_unit = {FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.MASS: "GJ/t", FuelPath.HEAT: "GJ/GJ"}[item.path]
            lhv = self._parameter(item.lower_heating_value, lhv_unit, f"CAR-FLD-F01-{item.fuel_id}-LHV", snapshots, problems, snapshot_at)
        else:
            lhv = None
        carbon_unit = "tC/GJ" if lhv is not None or item.path is FuelPath.HEAT else {
            FuelPath.VOLUME: "tC/10^4Nm3", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ"
        }[item.path]
        carbon = self._parameter(item.carbon_content, carbon_unit, f"CAR-FLD-F01-{item.fuel_id}-CARBON", snapshots, problems, snapshot_at)
        fox = self._parameter(item.oxidation_rate, "ratio", f"CAR-FLD-F01-{item.fuel_id}-FOX", snapshots, problems, snapshot_at)
        if item.path is FuelPath.HEAT and item.lower_heating_value is not None:
            problems.append(_problem(
                "CAR-VAL-FUEL-LHV-NOT-APPLICABLE",
                IssueLevel.ERROR,
                "热量路径的活动量已经是热量，不应再填写低位发热量；请清空该字段。",
                f"CAR-FLD-F01-{item.fuel_id}-LHV",
            ))
            return None
        if activity is None or carbon is None or fox is None:
            return None
        if lhv is not None:
            energy = fuel_energy_from_volume(activity, lhv) if item.path is FuelPath.VOLUME else fuel_energy_from_mass(activity, lhv)
            return fuel_heat_emission(energy, carbon, fox)
        return {
            FuelPath.VOLUME: fuel_volume_emission(activity, carbon, fox),
            FuelPath.MASS: fuel_mass_emission(activity, carbon, fox),
            FuelPath.HEAT: fuel_heat_emission(activity, carbon, fox),
        }[item.path]

    def _heat_factor(self, line: HeatInput, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime, *, energy_direction: str) -> Decimal | None:
        explicit = line.factor
        if explicit is not None:
            factor = self._parameter(explicit, "tCO2/GJ", f"CAR-FLD-HEAT-{line.line_id}-EF3", snapshots, problems, snapshot_at)
            is_measured = (
                line.factor_mode is HeatFactorMode.MEASURED
                or explicit.source_kind is ParameterSourceKind.MEASURED
            )
            if is_measured and line.factor_source_note is None:
                problems.append(_problem(
                    "CAR-VAL-FACTOR-SOURCE",
                    IssueLevel.WARNING,
                    "实测热力因子未填写来源说明；本次仍按您提供的数值计算。",
                    f"CAR-FLD-HEAT-{line.line_id}-EF3",
                ))
            return factor
        if line.factor_mode is HeatFactorMode.MEASURED:
            problems.append(_problem(
                "CAR-VAL-HEAT-FACTOR-MISSING",
                IssueLevel.ERROR,
                "您选择了使用实测热力因子，请填写因子数值。",
                f"CAR-FLD-HEAT-{line.line_id}-EF3",
            ))
            return None
        if self.parameter_resolver is None:
            problems.append(_problem(
                "CAR-VAL-HEAT-FACTOR-DEFAULT",
                IssueLevel.ERROR,
                "当前无法从标准参数目录读取热力排放因子；请检查参数目录，或提供有依据的实测因子。",
                f"CAR-FLD-HEAT-{line.line_id}-EF3",
            ))
            return None
        resolved = self._resolve_parameter(
            ParameterResolutionContext(
                parameter_id="heat_emission_factor_default",
                standard_id=STANDARD_ID,
                parameter_type=ParameterType.HEAT_EMISSION_FACTOR,
                subject_id="purchased_heat",
                emission_source_type=energy_direction,
                extra_context=(("energy_direction", energy_direction),),
            ),
            snapshots,
            problems,
            snapshot_at,
            detail_id=line.line_id,
        )
        if resolved is not None:
            return resolved
        return None

    def _steam_reference(self, line: HeatInput) -> SteamEnthalpyEvaluation | None:
        if line.pressure_mpa is None:
            return None
        if line.steam_kind is SteamKind.SUPERHEATED and line.temperature_c is None:
            return None
        pressure = line.pressure_mpa.value
        try:
            if line.steam_kind is SteamKind.SUPERHEATED:
                temperature = line.temperature_c.value
                enthalpy, interpolated, pressure_bounds = superheated_steam_enthalpy(pressure, temperature, policy=self.policy)
                pressure_low, pressure_high, _ = _bracket(pressure, _SUPERHEATED_PRESSURES)
                temperatures = tuple(row[0] for row in _SUPERHEATED_STEAM)
                temperature_low, temperature_high, _ = _bracket(temperature, temperatures)
                return SteamEnthalpyEvaluation(
                    enthalpy,
                    enthalpy,
                    "STANDARD_TABLE",
                    "C.5",
                    interpolated,
                    pressure_bounds,
                    (temperatures[temperature_low], temperatures[temperature_high]),
                )
            enthalpy, interpolated, pressure_bounds = saturated_steam_enthalpy(pressure, policy=self.policy)
            return SteamEnthalpyEvaluation(
                enthalpy, enthalpy, "STANDARD_TABLE", "C.4", interpolated, pressure_bounds,
            )
        except ValueError:
            raise

    def _enthalpy(self, line: HeatInput, problems: list[ValidationProblem]) -> SteamEnthalpyEvaluation | None:
        field_id = f"CAR-FLD-HEAT-{line.line_id}-HM"
        if line.manual_enthalpy:
            if line.enthalpy is None:
                problems.append(_problem("CAR-VAL-STEAM-ENTHALPY-MISSING", IssueLevel.ERROR, "请填写手动蒸汽焓值，或切换为自动计算。", field_id))
                return None
            enthalpy = self._quantity(line.enthalpy, "kJ/kg", field_id, problems, nonnegative=False)
            if enthalpy is None:
                return None
            if enthalpy <= 0:
                problems.append(_problem("CAR-VAL-STEAM-MANUAL-RANGE", IssueLevel.WARNING, "手动蒸汽焓值不大于0，请确认；本次仍按您填写的数值计算。", field_id))
            reference: SteamEnthalpyEvaluation | None = None
            if line.pressure_mpa is not None and (line.steam_kind is SteamKind.SATURATED or line.temperature_c is not None):
                try:
                    reference = self._steam_reference(line)
                except ValueError:
                    table_name = "附录 C.4" if line.steam_kind is SteamKind.SATURATED else "附录 C.5"
                    problems.append(_problem("CAR-VAL-STEAM-REFERENCE", IssueLevel.WARNING, f"当前蒸汽状态超出{table_name}范围，无法确定自动参考焓值；本次仍采用您填写的焓值。", field_id))
            if reference is not None:
                threshold = self.policy.multiply(reference.value, Decimal("0.01"))
                difference = self.policy.subtract(enthalpy, reference.value).copy_abs()
                if difference > threshold:
                    table_name = "附录 C.4" if line.steam_kind is SteamKind.SATURATED else "附录 C.5"
                    problems.append(_problem(
                        "CAR-VAL-STEAM-MANUAL-DEVIATION",
                        IssueLevel.WARNING,
                        f"您填写的蒸汽焓值为 {enthalpy} kJ/kg，按 GB/T 32151.34—2024 {table_name} 计算的参考值为 {reference.value} kJ/kg，请确认。若继续计算，本次采用您填写的 {enthalpy} kJ/kg。",
                        field_id,
                    ))
            return SteamEnthalpyEvaluation(
                value=enthalpy,
                reference_value=reference.value if reference else None,
                source="USER_MANUAL",
                table_id=reference.table_id if reference else ("C.4" if line.steam_kind is SteamKind.SATURATED else "C.5"),
                interpolated=reference.interpolated if reference else False,
                pressure_bounds=reference.pressure_bounds if reference else None,
                temperature_bounds=reference.temperature_bounds if reference else None,
            )

        if line.pressure_mpa is None:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, "自动计算蒸汽焓值需要填写蒸汽压力（绝压）。", f"CAR-FLD-HEAT-{line.line_id}-PRESSURE"))
            return None
        if line.steam_kind is SteamKind.SUPERHEATED and line.temperature_c is None:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, "自动计算过热蒸汽焓值需要填写蒸汽温度。", f"CAR-FLD-HEAT-{line.line_id}-TEMPERATURE"))
            return None
        try:
            reference = self._steam_reference(line)
        except ValueError:
            message = (
                "蒸汽压力超出附录 C.4 范围，请调整压力或改为手动填写焓值。"
                if line.steam_kind is SteamKind.SATURATED
                else "蒸汽压力或温度超出附录 C.5 范围，请调整蒸汽状态或改为手动填写焓值。"
            )
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, message, f"CAR-FLD-HEAT-{line.line_id}-PRESSURE"))
            return None
        if reference is None:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, "当前压力和温度无法确定蒸汽焓值。", line.line_id))
            return None
        if reference.interpolated:
            details = [
                ("low_pressure_mpa", str(reference.pressure_bounds[0])),
                ("high_pressure_mpa", str(reference.pressure_bounds[1])),
                ("algorithm_version", ALGORITHM_VERSION),
            ] if reference.pressure_bounds else [("algorithm_version", ALGORITHM_VERSION)]
            if reference.temperature_bounds:
                details.extend((
                    ("low_temperature_c", str(reference.temperature_bounds[0])),
                    ("high_temperature_c", str(reference.temperature_bounds[1])),
                ))
            problems.append(_problem("CAR-VAL-STEAM-INTERPOLATION", IssueLevel.INFO, f"蒸汽明细 {line.line_id} 使用 {reference.table_id} 邻近状态线性内插。", line.line_id, tuple(details)))
        return reference

    @staticmethod
    def _steam_trace_provenance(line: HeatInput, evaluation: SteamEnthalpyEvaluation) -> tuple[tuple[str, str], ...]:
        entries: list[tuple[str, str]] = [
            ("enthalpy_source", "用户手动填写" if evaluation.source == "USER_MANUAL" else "标准表自动确定"),
            ("standard", "GB/T 32151.34—2024"),
            ("table", evaluation.table_id or ""),
            ("pressure_basis", "绝压（MPa）"),
            ("enthalpy_used_kj_per_kg", str(evaluation.value)),
        ]
        if evaluation.reference_value is not None:
            entries.append(("automatic_reference_enthalpy_kj_per_kg", str(evaluation.reference_value)))
        if line.steam_amount_t is not None:
            entries.append(("input_steam_amount_t", str(line.steam_amount_t.value)))
        if line.factor_mode is not None:
            entries.append(("heat_factor_source", "企业实测值" if line.factor_mode is HeatFactorMode.MEASURED else "标准缺省值"))
        if line.factor_source_note:
            entries.append(("heat_factor_source_note", line.factor_source_note))
        if evaluation.pressure_bounds is not None:
            entries.extend((
                ("pressure_lower_node_mpa", str(evaluation.pressure_bounds[0])),
                ("pressure_upper_node_mpa", str(evaluation.pressure_bounds[1])),
            ))
        if evaluation.temperature_bounds is not None:
            entries.extend((
                ("temperature_lower_node_c", str(evaluation.temperature_bounds[0])),
                ("temperature_upper_node_c", str(evaluation.temperature_bounds[1])),
            ))
        if evaluation.interpolated:
            entries.append(("interpolation", "线性内插；" + ALGORITHM_VERSION))
        return tuple(entries)

    def calculate(self, input_value: CarbonMaterialInput, *, calculated_at: datetime | None = None) -> CarbonMaterialCalculationOutcome:
        if not isinstance(input_value, CarbonMaterialInput):
            raise DomainValidationError("input_value must be a CarbonMaterialInput")
        snapshot_at = calculated_at or datetime.now(timezone.utc)
        self._effective_rule_ids = set()
        if snapshot_at.tzinfo is None:
            raise DomainValidationError("calculated_at must be timezone-aware")
        problems: list[ValidationProblem] = []
        report_qualification = self._report_qualification(input_value.period)
        snapshots: list[ParameterSnapshot] = []
        traces: list[CalculationTrace] = []
        lines: list[CalculationLine] = []
        if not input_value.boundary_confirmed:
            problems.append(_problem("CAR-VAL-BOUNDARY-UNCONFIRMED", IssueLevel.ERROR, "必须确认本次核算边界。", "CAR-RULE-BOUNDARY-001"))
        if input_value.other_activity_present or input_value.transport_present:
            problems.append(_problem("CAR-VAL-OTHER-STANDARD", IssueLevel.ERROR, "存在本标准未覆盖的其他活动或上下游运输，需要其他标准核算；本次不并入炭素标准结果。", "CAR-RULE-OTHER-ACTIVITY-001"))

        fuel_status = self._source_check(input_value, SOURCE_FUEL, bool(input_value.fuel_inputs), problems)
        fuel_total = Decimal("0")
        if fuel_status is EmissionSourceStatus.INVOLVED:
            seen_paths: dict[str, FuelPath] = {}
            for fuel in input_value.fuel_inputs:
                if fuel.fuel_type in {FuelType.COAL, FuelType.OTHER} and not fuel.fuel_label:
                    problems.append(_problem(
                        "GEN-VAL-REQUIRED-MISSING",
                        IssueLevel.ERROR,
                        "请填写燃料名称或具体煤种。",
                        f"CAR-FLD-F01-{fuel.fuel_id}-FUEL-NAME",
                    ))
                if fuel.fuel_id in seen_paths:
                    problems.append(_problem("CAR-VAL-FUEL-PATH-DUPLICATE", IssueLevel.ERROR, f"燃料 {fuel.fuel_id} 按多个路径重复计入。", fuel.fuel_id))
                seen_paths[fuel.fuel_id] = fuel.path
                amount = self._fuel(fuel, snapshots, problems, snapshot_at)
                if amount is not None:
                    fuel_total += amount
                    lines.append(CalculationLine(f"{SOURCE_FUEL}.{fuel.fuel_id}", SOURCE_FUEL, CO2_ID, amount, "tCO2"))
                    fuel_variables = tuple(
                        item for name, value in (
                            ("activity", fuel.activity), ("lower_heating_value", fuel.lower_heating_value),
                            ("carbon_content", fuel.carbon_content), ("oxidation_rate", fuel.oxidation_rate),
                        ) if (item := _trace_variable(name, value)) is not None
                    )
                    traces.append(CalculationTrace(
                        fuel.fuel_id, "CAR-FML-FUEL-001", SOURCE_FUEL, fuel_variables,
                        f"EFu = 单条燃料活动量和参数的排放结果；燃料 {fuel.fuel_id}", amount,
                        instance_id=fuel.fuel_id,
                    ))
            if input_value.fuel_inputs:
                traces.append(CalculationTrace("CAR-F01", "CAR-FML-FUEL-001", SOURCE_FUEL, (("fuel_total", fuel_total, "tCO2"),), "EFu = sum(EFu(f))", fuel_total))

        def process_values(source_id: str, payloads: tuple[object, ...], fn, formula_id: str, line_id: str) -> Decimal:
            status = self._source_check(input_value, source_id, bool(payloads), problems)
            if status is not EmissionSourceStatus.INVOLVED:
                return Decimal("0")
            total = Decimal("0")
            field_defs = {
                CalcinationInput: (("gc", "t"), ("wfc", "ratio"), ("cc", "t"), ("ucc", "t"), ("du", "t"), ("wfc_c", "ratio"), ("wvar", "ratio"), ("wvar_c", "ratio")),
                BakingInput: (("bpm", "t"), ("bpmfc", "ratio"), ("bg", "t"), ("bgfc", "ratio"), ("bwt", "tC"), ("bp", "t"), ("bpfc", "ratio"), ("bpmvar", "ratio"), ("bgvar", "ratio")),
                GraphitizationInput: (("gpm", "t"), ("gpmfc", "ratio"), ("gta", "t"), ("gtafc", "ratio"), ("gwt", "tC"), ("gp", "t"), ("gpfc", "ratio"), ("gpmvar", "ratio")),
            }
            for payload in payloads:
                instance_id = payload.instance_id
                field_line_prefix = f"{line_id}-{instance_id}"
                instance_line_id = line_id if len(payloads) == 1 else f"{line_id}.{instance_id}"
                problem_count = len(problems)
                material_provenance: tuple[tuple[str, str], ...] = ()
                if payload.material_rows is not None:
                    normalization = normalize_material_inputs(
                        "calcination" if isinstance(payload, CalcinationInput)
                        else "baking" if isinstance(payload, BakingInput)
                        else "graphitization",
                        payload.material_rows,
                        policy=self.policy,
                    )
                    for issue in normalization.problems:
                        suffix = issue.field_id
                        field_id = f"{field_line_prefix}-material-{suffix}"
                        problems.append(_problem(issue.code, IssueLevel.ERROR, issue.message, field_id))
                    material_provenance = (("material.normalization_version", MATERIAL_NORMALIZATION_VERSION),) + tuple(
                        entry
                        for material in normalization.included_lines
                        for entry in (
                            (f"material.{material.line_id}.role", material.role.value),
                            (f"material.{material.line_id}.name", material.name),
                            (f"material.{material.line_id}.mass_t", "" if material.mass_t is None else str(material.mass_t)),
                            (f"material.{material.line_id}.fixed_carbon_percent", "" if material.fixed_carbon_percent is None else str(material.fixed_carbon_percent)),
                            (f"material.{material.line_id}.fixed_carbon_source", material.fixed_carbon_source.value),
                            (f"material.{material.line_id}.volatile_matter_percent", "" if material.volatile_matter_percent is None else str(material.volatile_matter_percent)),
                            (f"material.{material.line_id}.volatile_matter_source", material.volatile_matter_source.value),
                        )
                    )
                    if any(problem.level is IssueLevel.ERROR for problem in problems[problem_count:]):
                        continue
                    normalized_units = {
                        CalcinationInput: {"gc": "t", "wfc": "ratio", "cc": "t", "ucc": "t", "du": "t", "wfc_c": "ratio", "wvar": "ratio", "wvar_c": "ratio"},
                        BakingInput: {"bpm": "t", "bpmfc": "ratio", "bg": "t", "bgfc": "ratio", "bwt": "tC", "bp": "t", "bpfc": "ratio", "bpmvar": "ratio", "bgvar": "ratio"},
                        GraphitizationInput: {"gpm": "t", "gpmfc": "ratio", "gta": "t", "gtafc": "ratio", "gwt": "tC", "gp": "t", "gpfc": "ratio", "gpmvar": "ratio"},
                    }[type(payload)]
                    payload = replace(
                        payload,
                        **{
                            name: InputValue(value, normalized_units[name])
                            for name, value in normalization.values
                        },
                    )
                self._basis(payload, f"{source_id}.{instance_id}", problems)
                values: dict[str, Decimal] = {}
                for attr, unit in field_defs[type(payload)]:
                    raw = getattr(payload, attr)
                    field_id = f"{field_line_prefix}-{attr}"
                    if unit == "ratio":
                        value = self._ratio(raw, field_id, problems)
                    else:
                        value = self._quantity(raw, unit, field_id, problems)
                    if value is not None:
                        values[attr] = value
                if isinstance(payload, CalcinationInput):
                    k1 = self._required_parameter(payload, "k1", "CAR-PAR-K1", f"{field_line_prefix}-k1", snapshots, problems, snapshot_at)
                    if k1 is not None: values["k1"] = k1
                elif isinstance(payload, BakingInput):
                    k2 = self._required_parameter(payload, "k2", "CAR-PAR-K2", f"{field_line_prefix}-k2", snapshots, problems, snapshot_at)
                    if k2 is not None: values["k2"] = k2
                else:
                    k3 = self._required_parameter(payload, "k3", "CAR-PAR-K3", f"{field_line_prefix}-k3", snapshots, problems, snapshot_at)
                    if k3 is not None: values["k3"] = k3
                if len(values) < len(field_defs[type(payload)]) + 1 or any(problem.level is IssueLevel.ERROR for problem in problems[problem_count:]):
                    continue
                amount = fn(**values)
                if amount < 0:
                    problems.append(_problem("CAR-VAL-MATERIAL-BALANCE-NEGATIVE", IssueLevel.ERROR, f"{source_id} 物料平衡结果为负。", f"{source_id}.{instance_id}"))
                if getattr(payload, "carbon_output_included_in_input", False):
                    problems.append(_problem("CAR-VAL-CARBON-OUTPUT-DUPLICATE", IssueLevel.ERROR, f"{source_id} 的碳输出已在输入/产量中重复使用。", f"{source_id}.{instance_id}"))
                lines.append(CalculationLine(instance_line_id, source_id, CO2_ID, amount, "tCO2"))
                traces.append(CalculationTrace(instance_line_id, formula_id, source_id, tuple((key, value, "ratio" if key.startswith("w") or key.startswith("b") and key.endswith(("fc", "var")) else "") for key, value in values.items()), f"{formula_id} 按映射变量代入；实例 {instance_id}", amount, instance_id=instance_id, provenance=material_provenance))
                total += amount
            return total

        calc_total = process_values(SOURCE_CALCINATION, input_value.calcinations, calcination_emission, "CAR-FML-CALCINATION-001", "CAR-FLD-P01-RESULT")
        bake_total = process_values(SOURCE_BAKING, input_value.bakings, baking_emission, "CAR-FML-BAKING-001", "CAR-FLD-P02-RESULT")
        for item in input_value.graphitizations:
            if item.furnace_loss_included:
                problems.append(_problem("CAR-VAL-GRAPHITIZATION-FURNACE-LOSS", IssueLevel.ERROR, "石墨化炉本身炭质材料氧化烧损不得计入石墨化排放。", f"{SOURCE_GRAPHITIZATION}.{item.instance_id}"))
        graph_total = process_values(SOURCE_GRAPHITIZATION, input_value.graphitizations, graphitization_emission, "CAR-FML-GRAPHITIZATION-001", "CAR-FLD-P03-RESULT")

        fume_status = self._source_check(input_value, SOURCE_FUME, bool(input_value.fume_incinerations), problems)
        fume_total = Decimal("0")
        if fume_status is EmissionSourceStatus.INVOLVED:
            for item in input_value.fume_incinerations:
                prefix = f"CAR-FLD-P04A-{item.instance_id}"
                problem_count = len(problems)
                q = self._quantity(item.q, "Nm3/h", f"{prefix}-Q", problems)
                qvar = self._quantity(item.qvar, "mg/Nm3", f"{prefix}-QVAR", problems)
                hm = self._quantity(item.hm, "GJ/t", f"{prefix}-HM", problems)
                fch = self._parameter(item.fch, "tC/GJ", f"{prefix}-FCH", snapshots, problems, snapshot_at)
                fox = self._ratio(item.fox, f"{prefix}-FOX", problems)
                duration = self._quantity(item.duration, "d", f"{prefix}-T", problems)
                if None in (q, qvar, hm, fch, fox, duration) or any(problem.level is IssueLevel.ERROR for problem in problems[problem_count:]):
                    continue
                amount = fume_incineration_emission(q, qvar, hm, fch, fox, duration)
                line_id = "CAR-FLD-P04A-RESULT" if len(input_value.fume_incinerations) == 1 else f"CAR-FLD-P04A-RESULT.{item.instance_id}"
                lines.append(CalculationLine(line_id, SOURCE_FUME, CO2_ID, amount, "tCO2"))
                fume_variables = tuple(
                    item_value for name, value in (("Q", q), ("QVar", qvar), ("HM", hm), ("FCh", fch), ("FOx", fox), ("T", duration))
                    if (item_value := _trace_variable(name, value)) is not None
                )
                traces.append(CalculationTrace(line_id, "CAR-FML-FUME-INCINERATION-001", SOURCE_FUME, fume_variables, f"ER = Q×QVar×HM×FCh×FOx×T×24×44/12×10⁻⁹；实例 {item.instance_id}", amount, instance_id=item.instance_id))
                fume_total += amount

        fgd_status = self._source_check(input_value, SOURCE_FGD, bool(input_value.fgd_units), problems)
        fgd_total = Decimal("0")
        if fgd_status is EmissionSourceStatus.INVOLVED:
            for unit in input_value.fgd_units:
                if not unit.components:
                    problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, "脱硫净化缺少至少一条碳酸盐组分。", f"{SOURCE_FGD}.{unit.instance_id}"))
                    continue
                problem_count = len(problems)
                fractions = Decimal("0")
                validated: list[CarbonateComponent] = []
                for index, component in enumerate(unit.components):
                    component_prefix = f"CAR-FLD-P04B-{unit.instance_id}-{index}"
                    amount = self._quantity(component.amount, "t", f"{component_prefix}-CAL", problems)
                    fraction_field = f"{component_prefix}-I"
                    if isinstance(component.carbonate_fraction, ParameterValue):
                        fraction = self._parameter(component.carbonate_fraction, "ratio", fraction_field, snapshots, problems, snapshot_at)
                    else:
                        fraction = self._ratio(component.carbonate_fraction, fraction_field, problems)
                    if isinstance(component.emission_factor, ParameterValue):
                        factor = self._parameter(component.emission_factor, "tCO2/t", f"{component_prefix}-EF1", snapshots, problems, snapshot_at)
                    else:
                        factor = None
                        problems.append(_problem("CAR-VAL-CARBONATE-FACTOR-MISSING", IssueLevel.ERROR, "请选择脱硫剂中的碳酸盐种类，或提供可追溯的排放因子。", f"{component_prefix}-EF1"))
                    conversion_field = f"{component_prefix}-TR"
                    if isinstance(component.conversion_rate, ParameterValue):
                        conversion = self._parameter(component.conversion_rate, "ratio", conversion_field, snapshots, problems, snapshot_at)
                    else:
                        conversion = self._ratio(component.conversion_rate, conversion_field, problems)
                    if None not in (amount, fraction, factor, conversion):
                        validated.append(CarbonateComponent(amount, fraction, factor, conversion, component.carbonate_type))
                        fractions += fraction
                if fractions > Decimal("1"):
                    problems.append(_problem("CAR-VAL-CARBONATE-SUM", IssueLevel.ERROR, "同一脱硫设施的多种碳酸盐组分含量合计不得超过100%。", f"{SOURCE_FGD}.{unit.instance_id}"))
                if any(problem.level is IssueLevel.ERROR for problem in problems[problem_count:]):
                    continue
                amount = fgd_emission(validated)
                line_id = "CAR-FLD-P04B-RESULT" if len(input_value.fgd_units) == 1 else f"CAR-FLD-P04B-RESULT.{unit.instance_id}"
                lines.append(CalculationLine(line_id, SOURCE_FGD, CO2_ID, amount, "tCO2"))
                component_variables = tuple(
                    item_value
                    for index, component in enumerate(validated, 1)
                    for name, value in (
                        (f"CAL[{index}]", component.amount), (f"I[{index}]", component.carbonate_fraction),
                        (f"EF1[{index}]", component.emission_factor), (f"TR[{index}]", component.conversion_rate),
                    )
                    if (item_value := _trace_variable(name, value)) is not None
                )
                traces.append(CalculationTrace(line_id, "CAR-FML-FGD-001", SOURCE_FGD, component_variables, f"ED = sum(CAL×I×EF1×TR)；设施 {unit.instance_id} 内独立汇总", amount, instance_id=unit.instance_id))
                fgd_total += amount

        gas_total = fume_total + fgd_total
        if fume_status is EmissionSourceStatus.INVOLVED or fgd_status is EmissionSourceStatus.INVOLVED:
            lines.append(CalculationLine("CAR-FLD-GAS-CONTROL-RESULT", "CAR-SRC-GAS-CONTROL-001", CO2_ID, gas_total, "tCO2"))
            traces.append(CalculationTrace("CAR-P04", "CAR-FML-GAS-CONTROL-TOTAL-001", "CAR-SRC-GAS-CONTROL-001", (("ER subtotal", fume_total, "tCO2"), ("ED subtotal", fgd_total, "tCO2")), "EP = sum(ER) + sum(ED)", gas_total))

        linked_fossil_details = {
            fuel.electricity_detail_id
            for fuel in input_value.fuel_inputs
            if fuel.electricity_detail_id
        }
        self_fossil_details = [
            detail
            for detail in input_value.electricity_details
            if detail.acquisition_mode is ElectricityAcquisitionMode.SELF_CONSUMED
            and detail.attribute is ElectricityAttribute.FOSSIL
        ]
        for detail in self_fossil_details:
            if detail.detail_id not in linked_fossil_details:
                problems.append(
                    _problem(
                        "GEN-VAL-SELF-CONSUMED-FOSSIL-ROUTE",
                        IssueLevel.ERROR,
                        f"自发自用化石能源电力明细 {detail.detail_id} 必须转交燃料直接排放路径；本阶段不在购入电力路径重复计算。",
                        detail.detail_id,
                    )
                )
            else:
                problems.append(
                    _problem(
                        "CAR-ROUTE-SELF-CONSUMED-FOSSIL",
                        IssueLevel.INFO,
                        f"电力明细 {detail.detail_id} 已转交燃料直接排放路径，未进入间接排放。",
                        detail.detail_id,
                    )
                )
        power_payload = any(
            not (
                detail.acquisition_mode is ElectricityAcquisitionMode.SELF_CONSUMED
                and detail.attribute is ElectricityAttribute.FOSSIL
            )
            for detail in input_value.electricity_details
        )
        power_status = self._source_check(input_value, SOURCE_PURCHASED_ELECTRICITY, power_payload, problems)
        purchased_power_total = Decimal("0")
        if power_status is EmissionSourceStatus.INVOLVED:
            if self.parameter_resolver is None:
                problems.append(_problem("CAR-VAL-PARAMETER-RESOLVER-MISSING", IssueLevel.ERROR, "购入电力需要接入 G05 参数解析服务。", SOURCE_PURCHASED_ELECTRICITY))
            else:
                for detail in input_value.electricity_details:
                    if detail.acquisition_mode is ElectricityAcquisitionMode.SELF_CONSUMED and detail.attribute is ElectricityAttribute.ORDINARY:
                        problems.append(_problem("CAR-VAL-ELECTRICITY-ATTRIBUTE", IssueLevel.ERROR, "自发自用常规电力不能直接进入购入电力路径；应明确非化石证明或转交燃料路径。", detail.detail_id))
                        continue
                    resolution = self.parameter_resolver.resolve_electricity_details((detail,), snapshot_at=snapshot_at)[0]
                    if resolution.parameter_resolution is not None:
                        self._effective_rule_ids.update(resolution.parameter_resolution.effective_rules.rule_ids)
                    if resolution.route is ElectricityResolutionRoute.DELEGATE_DIRECT_FUEL_PATH:
                        continue
                    problems.extend(self._map_electricity_resolution_problems(detail.detail_id, resolution.problems))
                    if resolution.blocked or resolution.snapshot is None or resolution.result is None or resolution.result.recommended is None:
                        continue
                    snapshots.append(resolution.snapshot)
                    quantity = self._quantity(InputValue(detail.electricity_amount, detail.electricity_unit), "MWh", detail.detail_id, problems)
                    if quantity is None:
                        continue
                    amount = purchased_electricity_emission(quantity, resolution.result.recommended.factor.value)
                    purchased_power_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-PWR-PURCHASED-RESULT.{detail.detail_id}", SOURCE_PURCHASED_ELECTRICITY, CO2_ID, amount, "tCO2"))
                    traces.append(CalculationTrace(detail.detail_id, "CAR-FML-PURCHASED-ELECTRICITY-001", SOURCE_PURCHASED_ELECTRICITY, (("QGe", quantity, "MWh"), ("EF2", resolution.result.recommended.factor.value, resolution.result.recommended.factor.unit)), "EGe = QGe × EF2", amount, instance_id=detail.detail_id))

        exported_power_status = self._source_check(input_value, SOURCE_EXPORTED_ELECTRICITY, bool(input_value.exported_electricity), problems)
        exported_power_total = Decimal("0")
        if exported_power_status is EmissionSourceStatus.INVOLVED:
            for line in input_value.exported_electricity:
                quantity = self._quantity(line.amount, "MWh", line.line_id, problems)
                factor = line.factor
                if factor is not None:
                    factor_value = self._parameter(factor, "tCO2/MWh", f"CAR-FLD-POWER-EXPORTED-EF.{line.line_id}", snapshots, problems, snapshot_at)
                else:
                    factor_value = self._resolve_parameter(ParameterResolutionContext(parameter_id="electricity_emission_factor_national", standard_id=STANDARD_ID, parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR, subject_id="purchased_electricity", electricity_acquisition_mode=ElectricityAcquisitionMode.PURCHASED, electricity_attribute=ElectricityAttribute.ORDINARY, extra_context=(("energy_direction", "exported"),)), snapshots, problems, snapshot_at, detail_id=line.line_id)
                if quantity is not None and factor_value is not None:
                    amount = purchased_electricity_emission(quantity, factor_value)
                    exported_power_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-POWER-EXPORTED-RESULT.{line.line_id}", SOURCE_EXPORTED_ELECTRICITY, CO2_ID, amount, "tCO2"))
                    traces.append(CalculationTrace(line.line_id, "CAR-FML-EXPORTED-ELECTRICITY-001", SOURCE_EXPORTED_ELECTRICITY, (("QSe", quantity, "MWh"), ("EF2", factor_value, "tCO2/MWh")), "ESe = QSe × EF2", amount, instance_id=line.line_id))

        heat_payload = bool(input_value.purchased_heat)
        heat_status = self._source_check(input_value, SOURCE_PURCHASED_HEAT, heat_payload, problems)
        purchased_heat_total = Decimal("0")
        if heat_status is EmissionSourceStatus.INVOLVED:
            for line in input_value.purchased_heat:
                quantity = self._quantity(line.amount, "kg", line.line_id, problems)
                enthalpy = self._enthalpy(line, problems)
                factor = self._heat_factor(line, snapshots, problems, snapshot_at, energy_direction="purchased_heat")
                if None not in (quantity, enthalpy, factor):
                    amount = purchased_heat_emission(quantity, enthalpy.value, factor)
                    purchased_heat_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-HEAT-PURCHASED-RESULT.{line.line_id}", SOURCE_PURCHASED_HEAT, CO2_ID, amount, "tCO2"))
                    variables = [("BGd", quantity, "kg"), ("HM", enthalpy.value, "kJ/kg"), ("EF3", factor, "tCO2/GJ")]
                    if line.steam_amount_t is not None:
                        variables.append(("steam_quantity_input", line.steam_amount_t.value, "t"))
                    if enthalpy.reference_value is not None and enthalpy.source == "USER_MANUAL":
                        variables.append(("HM_reference", enthalpy.reference_value, "kJ/kg"))
                    traces.append(CalculationTrace(
                        line.line_id, "CAR-FML-PURCHASED-HEAT-001", SOURCE_PURCHASED_HEAT,
                        tuple(variables),
                        "EGd = BGd × HM × EF3 / 10⁶；焓值来源：" + ("用户手动填写" if enthalpy.source == "USER_MANUAL" else f"GB/T 32151.34—2024 附录 {enthalpy.table_id} 自动确定"),
                        amount,
                        instance_id=line.line_id,
                        provenance=self._steam_trace_provenance(line, enthalpy),
                    ))

        exported_heat_status = self._source_check(input_value, SOURCE_EXPORTED_HEAT, bool(input_value.exported_heat), problems)
        exported_heat_total = Decimal("0")
        if exported_heat_status is EmissionSourceStatus.INVOLVED:
            for line in input_value.exported_heat:
                quantity = self._quantity(line.amount, "kg", line.line_id, problems)
                enthalpy = self._enthalpy(line, problems)
                factor = self._heat_factor(line, snapshots, problems, snapshot_at, energy_direction="exported_heat")
                if None not in (quantity, enthalpy, factor):
                    amount = purchased_heat_emission(quantity, enthalpy.value, factor)
                    exported_heat_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-HEAT-EXPORTED-RESULT.{line.line_id}", SOURCE_EXPORTED_HEAT, CO2_ID, amount, "tCO2"))
                    variables = [("BSd", quantity, "kg"), ("HM", enthalpy.value, "kJ/kg"), ("EF3", factor, "tCO2/GJ")]
                    if line.steam_amount_t is not None:
                        variables.append(("steam_quantity_input", line.steam_amount_t.value, "t"))
                    if enthalpy.reference_value is not None and enthalpy.source == "USER_MANUAL":
                        variables.append(("HM_reference", enthalpy.reference_value, "kJ/kg"))
                    traces.append(CalculationTrace(
                        line.line_id, "CAR-FML-EXPORTED-HEAT-001", SOURCE_EXPORTED_HEAT,
                        tuple(variables),
                        "ESd = BSd × HM × EF3 / 10⁶；焓值来源：" + ("用户手动填写" if enthalpy.source == "USER_MANUAL" else f"GB/T 32151.34—2024 附录 {enthalpy.table_id} 自动确定"),
                        amount,
                        instance_id=line.line_id,
                        provenance=self._steam_trace_provenance(line, enthalpy),
                    ))

        calculation_result: CalculationResult | None = None
        record: AccountingRecord | None = None
        if not contains_errors(problems):
            direct_total = direct_emission(fuel_total, calc_total, bake_total, graph_total, gas_total)
            indirect_total = indirect_emission(purchased_power_total, purchased_heat_total, exported_power_total, exported_heat_total)
            grand_total = total_emission(direct_total, indirect_total)
            lines.extend((
                CalculationLine("CAR-FLD-DIRECT-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, direct_total, "tCO2"),
                CalculationLine("CAR-FLD-INDIRECT-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, indirect_total, "tCO2"),
                CalculationLine("CAR-FLD-TOTAL-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, grand_total, "tCO2"),
            ))
            traces.extend((
                CalculationTrace("CAR-DIRECT", "CAR-FML-DIRECT-001", "CAR-RULE-TOTAL-001", (("EFu", fuel_total, "tCO2"), ("EC", calc_total, "tCO2"), ("EB", bake_total, "tCO2"), ("EG", graph_total, "tCO2"), ("EP", gas_total, "tCO2")), "ES = EFu + EC + EB + EG + EP", direct_total),
                CalculationTrace("CAR-INDIRECT", "CAR-FML-INDIRECT-001", "CAR-RULE-TOTAL-001", (("EGe", purchased_power_total, "tCO2"), ("EGd", purchased_heat_total, "tCO2"), ("ESe", exported_power_total, "tCO2"), ("ESd", exported_heat_total, "tCO2")), "EI = EGe + EGd - ESe - ESd", indirect_total),
                CalculationTrace("CAR-TOTAL", "CAR-FML-TOTAL-001", "CAR-RULE-TOTAL-001", (("ES", direct_total, "tCO2"), ("EI", indirect_total, "tCO2")), "ET = ES + EI", grand_total),
            ))
            calculation_result = CalculationResult("result." + input_value.input_id, STANDARD_ID, ALGORITHM_VERSION, tuple(lines), grand_total, "tCO2", snapshot_at, tuple(problems))
            factor_evidence_ids = tuple(item.evidence_id for item in input_value.reporting_data.measured_factor_evidence)
            snapshots = [
                replace(
                    item,
                    evidence_ref_ids=tuple(dict.fromkeys((*item.evidence_ref_ids, *factor_evidence_ids))),
                )
                if item.selection_method in {ParameterSelectionMethod.ENTERPRISE_MEASURED, ParameterSelectionMethod.MANUAL_OVERRIDE}
                else item
                for item in snapshots
            ]
            generic_input = AccountingInput(
                input_id=input_value.input_id,
                standard_id=STANDARD_ID,
                period=input_value.period,
                enterprise_name=input_value.enterprise_name,
                boundary_component_ids=input_value.boundary_component_ids,
                emission_sources=tuple(EmissionSourceSelection(item.source_id, item.status is EmissionSourceStatus.INVOLVED) for item in input_value.source_states),
            )
            status = RecordStatus.COMPLETED_WITH_WARNINGS if contains_warnings(problems) else RecordStatus.COMPLETED
            record = AccountingRecord(
                f"record.{input_value.input_id}.{uuid4().hex}",
                STANDARD_ID,
                ALGORITHM_VERSION,
                snapshot_at,
                generic_input,
                calculation_result,
                status,
                tuple(snapshots),
                tuple(problems),
                self.standard_version,
            )
            create_with_details = getattr(self.record_repository, "create_with_details", None)
            if callable(create_with_details):
                rule_snapshot = self._effective_rule_snapshot()
                source_subtotals = {
                    "fuel": fuel_total,
                    "calcination": calc_total,
                    "baking": bake_total,
                    "graphitization": graph_total,
                    "gas_control": gas_total,
                    "purchased_electricity": purchased_power_total,
                    "purchased_heat": purchased_heat_total,
                    "exported_electricity": exported_power_total,
                    "exported_heat": exported_heat_total,
                }
                trace_snapshot = self._trace_snapshot(record, traces, snapshots, source_subtotals)
                provenance_snapshot = self._provenance_snapshot(record, rule_snapshot, snapshots)
                create_with_details(
                    record,
                    raw_input=input_value,
                    effective_rule_set=tuple(sorted(self._effective_rule_ids)),
                    trace_snapshot=trace_snapshot,
                    provenance_snapshot=provenance_snapshot,
                    reporting_snapshot=_snapshot_value(input_value.reporting_data),
                    report_qualification=_snapshot_value(report_qualification),
                )
            else:
                self.record_repository.create(record)
        return CarbonMaterialCalculationOutcome(input_value, calculation_result, tuple(problems), tuple(snapshots), tuple(traces), ALGORITHM_VERSION, record, report_qualification)


__all__ = [
    "ALGORITHM_VERSION", "MAPPING_VERSION", "GREEN_ELECTRICITY_EVIDENCE_CODE", "STANDARD_ID", "STANDARD_VERSION", "ActivityDataEvidence", "CarbonReportingData", "MeasuredFactorEvidence", "ReportQualification", "verify_record_aggregation", "CarbonMaterialCalculationOutcome", "CarbonMaterialCalculator", "CarbonMaterialInput", "CarbonateComponent", "CalcinationInput", "BakingInput", "GraphitizationInput", "FumeIncinerationInput", "FGDInput", "FuelInput", "FuelPath", "FuelType", "HeatFactorMode", "HeatInput", "ElectricityOutputLine", "EmissionSourceState", "EmissionSourceStatus", "InputValue", "MaterialBasis", "MaterialComponentKind", "ParameterSourceKind", "ParameterValue", "SteamEnthalpyEvaluation", "SteamKind", "InMemoryRecordRepository", "baking_emission", "calcination_emission", "direct_emission", "fgd_emission", "fuel_energy_from_mass", "fuel_energy_from_volume", "fuel_heat_emission", "fuel_mass_emission", "fuel_volume_emission", "fume_incineration_emission", "graphitization_emission", "indirect_emission", "purchased_electricity_emission", "purchased_heat_emission", "saturated_steam_enthalpy", "steam_reference_table_rows", "superheated_steam_enthalpy", "total_emission",
]
