"""GB/T 32151.34-2024 calculation domain for G06.

The module is deliberately platform independent.  It contains the frozen SM01
formula paths, standard-specific input contracts, validation and an in-memory
record boundary used by G06.  Qt and SQLite adapters live outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping, Sequence

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
from packages.core.units import UnitError, UnitService


STANDARD_ID = "gbt_32151_34_2024"
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
        object.__setattr__(self, "unit", self.unit.strip())


def _coerce_input(value: object, default_unit: str) -> InputValue | None:
    if value is None:
        return None
    if isinstance(value, InputValue):
        return value
    if isinstance(value, ParameterValue):
        return InputValue(value.value, value.unit)
    return InputValue(value, default_unit)  # type: ignore[arg-type]


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

    def __post_init__(self) -> None:
        if not isinstance(self.fuel_id, str) or not self.fuel_id.strip():
            raise DomainValidationError("fuel_id is required")
        if not isinstance(self.path, FuelPath):
            raise DomainValidationError("path must be a FuelPath")
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
        object.__setattr__(self, "lower_heating_value", _coerce_parameter(self.lower_heating_value, f"CAR-PAR-{self.fuel_id}-LHV", "GJ", source_location="附录C.1；第5.2.1条"))
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

    def __post_init__(self) -> None:
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

    def __post_init__(self) -> None:
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

    def __post_init__(self) -> None:
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


@dataclass(frozen=True, slots=True)
class FumeIncinerationInput:
    q: object | None = None
    qvar: object | None = None
    hm: object | None = None
    fch: object | None = None
    fox: object | None = None
    duration: object | None = None

    def __post_init__(self) -> None:
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
    emission_factor: object
    conversion_rate: object = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _coerce_input(self.amount, "t"))
        object.__setattr__(self, "carbonate_fraction", _coerce_input(self.carbonate_fraction, "ratio"))
        object.__setattr__(self, "emission_factor", _coerce_parameter(self.emission_factor, "CAR-PAR-P04B-EF1", "tCO2/t", source_location="第5.2.5.2条、附录C.2"))
        object.__setattr__(self, "conversion_rate", _coerce_input(self.conversion_rate, "ratio"))


@dataclass(frozen=True, slots=True)
class FGDInput:
    components: tuple[CarbonateComponent, ...] = ()
    cal: object | None = None
    i: object | None = None
    ef1: object | None = None
    tr: object | None = None

    def __post_init__(self) -> None:
        components = tuple(self.components)
        if any(not isinstance(item, CarbonateComponent) for item in components):
            raise DomainValidationError("components must contain CarbonateComponent values")
        if not components and self.cal is not None:
            components = (
                CarbonateComponent(
                    self.cal,
                    self.i if self.i is not None else Decimal("0.90"),
                    self.ef1 if self.ef1 is not None else Decimal("0.44"),
                    self.tr if self.tr is not None else Decimal("1"),
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

    def __post_init__(self) -> None:
        if not self.line_id.strip():
            raise DomainValidationError("line_id is required")
        if not isinstance(self.steam_kind, SteamKind):
            raise DomainValidationError("steam_kind must be a SteamKind")
        object.__setattr__(self, "amount", _coerce_input(self.amount, self.unit))
        object.__setattr__(self, "enthalpy", _coerce_input(self.enthalpy, "kJ/kg"))
        object.__setattr__(self, "pressure_mpa", _coerce_input(self.pressure_mpa, "MPa"))
        object.__setattr__(self, "temperature_c", _coerce_input(self.temperature_c, "C"))


@dataclass(frozen=True, slots=True)
class CarbonMaterialInput:
    input_id: str
    enterprise_id: str
    enterprise_name: str
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

    def __post_init__(self) -> None:
        for field in ("input_id", "enterprise_id", "enterprise_name"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise DomainValidationError(f"{field} is required")
        if not isinstance(self.period, AccountingPeriod):
            raise DomainValidationError("period must be an AccountingPeriod")
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
        if len({item.fuel_id for item in self.fuel_inputs}) != len(self.fuel_inputs):
            raise DomainValidationError("fuel IDs must be unique")
        if len({item.detail_id for item in self.electricity_details}) != len(self.electricity_details):
            raise DomainValidationError("electricity detail IDs must be unique")
        if len({item.line_id for item in (*self.exported_electricity, *self.purchased_heat, *self.exported_heat)}) != len((*self.exported_electricity, *self.purchased_heat, *self.exported_heat)):
            raise DomainValidationError("energy line IDs must be unique")

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


@dataclass(frozen=True, slots=True)
class CarbonMaterialCalculationOutcome:
    input: CarbonMaterialInput
    result: CalculationResult | None
    problems: tuple[ValidationProblem, ...]
    parameter_snapshots: tuple[ParameterSnapshot, ...]
    traces: tuple[CalculationTrace, ...]
    algorithm_version: str = ALGORITHM_VERSION
    record: AccountingRecord | None = None

    @property
    def blocked(self) -> bool:
        return contains_errors(self.problems)

    @property
    def successful(self) -> bool:
        return not self.blocked and self.result is not None


class InMemoryRecordRepository(RecordRepository):
    """G06-only record boundary; no SQLite or formal persistence is used."""

    def __init__(self) -> None:
        self._records: dict[str, AccountingRecord] = {}

    def create(self, record: AccountingRecord) -> None:
        if record.record_id in self._records:
            raise DomainValidationError(f"record already exists: {record.record_id}")
        self._records[record.record_id] = record

    def get(self, record_id: str) -> AccountingRecord | None:
        return self._records.get(record_id)

    def list_all(self) -> tuple[AccountingRecord, ...]:
        return tuple(self._records.values())


def _d(value: str | Decimal | int) -> Decimal:
    return DecimalPolicy().parse(value)


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


def _linear_interpolate(value: Decimal, low_key: Decimal, high_key: Decimal, low_value: Decimal, high_value: Decimal) -> Decimal:
    if low_key == high_key:
        return low_value
    return low_value + (value - low_key) / (high_key - low_key) * (high_value - low_value)


def superheated_steam_enthalpy(pressure_mpa: object, temperature_c: object) -> tuple[Decimal, bool, tuple[Decimal, Decimal]]:
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
    )
    if temperature_exact:
        return low_row, True, (_SUPERHEATED_PRESSURES[pressure_low], _SUPERHEATED_PRESSURES[pressure_high])
    high_row = _linear_interpolate(
        pressure,
        _SUPERHEATED_PRESSURES[pressure_low],
        _SUPERHEATED_PRESSURES[pressure_high],
        _SUPERHEATED_STEAM[temperature_high][1][pressure_low],
        _SUPERHEATED_STEAM[temperature_high][1][pressure_high],
    )
    return _linear_interpolate(
        temperature,
        temperatures[temperature_low],
        temperatures[temperature_high],
        low_row,
        high_row,
    ), True, (_SUPERHEATED_PRESSURES[pressure_low], _SUPERHEATED_PRESSURES[pressure_high])


def saturated_steam_enthalpy(pressure_mpa: object) -> tuple[Decimal, bool, tuple[Decimal, Decimal]]:
    pressure = _d(pressure_mpa)
    for key, enthalpy in _SATURATED_STEAM:
        if pressure == key:
            return enthalpy, False, (key, key)
    for (low_pressure, low_enthalpy), (high_pressure, high_enthalpy) in zip(_SATURATED_STEAM, _SATURATED_STEAM[1:]):
        if low_pressure <= pressure <= high_pressure:
            ratio = (pressure - low_pressure) / (high_pressure - low_pressure)
            return low_enthalpy + ratio * (high_enthalpy - low_enthalpy), True, (low_pressure, high_pressure)
    raise ValueError("steam pressure is outside the C.4 table")


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
        policy: DecimalPolicy | None = None,
        unit_service: UnitService | None = None,
    ) -> None:
        self.policy = policy or DecimalPolicy()
        self.units = unit_service or UnitService(self.policy)
        self.parameter_resolver = parameter_resolver
        self.record_repository = record_repository or InMemoryRecordRepository()

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

    def _parameter(self, value: ParameterValue | None, expected_unit: str, field_id: str, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime, *, required: bool = True) -> Decimal | None:
        if value is None:
            if required:
                problems.append(_problem("GEN-VAL-REQUIRED-MISSING", IssueLevel.ERROR, f"缺少参数 {field_id}。", field_id))
            return None
        try:
            if value.unit != expected_unit:
                problems.append(_problem("GEN-VAL-UNIT-INCOMPATIBLE", IssueLevel.ERROR, f"参数 {field_id} 单位 {value.unit} 与要求 {expected_unit} 不一致。", field_id))
                return None
            if value.source_id is None or value.source_version is None or value.source_location is None:
                problems.append(_problem("CAR-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {field_id} 缺少来源、版本或定位。", field_id))
            snapshot_id = f"{field_id}.parameter-snapshot"
            snapshots.append(
                ParameterSnapshot(
                    snapshot_id=snapshot_id,
                    parameter_id=value.parameter_id,
                    factor_id=value.factor_id,
                    value_used=value.value,
                    unit_used=value.unit,
                    source_id=value.source_id,
                    source_version=value.source_version,
                    selection_method=_parameter_method(value.source_kind),
                    selection_reason=value.selection_reason,
                    standard_id=STANDARD_ID,
                    snapshot_at=snapshot_at,
                    factor_version=value.source_version,
                    source_location=value.source_location,
                    factor_year=value.factor_year,
                )
            )
            if value.source_kind is ParameterSourceKind.USER_DEFINED:
                problems.append(_problem("GEN-VAL-CUSTOM-FACTOR", IssueLevel.WARNING, f"参数 {field_id} 使用用户自定义值。", field_id))
            if value.source_kind is ParameterSourceKind.MEASURED and value.source_location is None:
                problems.append(_problem("GEN-VAL-MEASURED-NO-TEST-INFO", IssueLevel.WARNING, f"参数 {field_id} 缺少检测/取样信息。", field_id))
            return value.value
        except DomainValidationError as exc:
            problems.append(_problem("GEN-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {field_id} 无法形成快照：{exc}", field_id))
            return None

    def _default_parameter(self, parameter_id: str, value: str, field_id: str, source_location: str, code: str, problems: list[ValidationProblem]) -> ParameterValue:
        problems.append(_problem(code, IssueLevel.WARNING, f"{field_id} 未填写，采用标准缺省值 {value}。", field_id))
        return ParameterValue(parameter_id, value, "ratio", source_location=source_location, selection_reason=f"未提供企业值，按 {source_location} 的标准一般取值采用。")

    def _default_ratio_snapshot(
        self,
        *,
        parameter_id: str,
        value: str,
        field_id: str,
        code: str,
        source_location: str,
        snapshots: list[ParameterSnapshot],
        problems: list[ValidationProblem],
        snapshot_at: datetime,
    ) -> None:
        """Record a mapping default that is not represented as a ParameterValue."""
        problems.append(_problem(code, IssueLevel.WARNING, f"{field_id} 未填写，采用标准缺省值 {value}。", field_id))
        snapshots.append(
            ParameterSnapshot(
                snapshot_id=f"{field_id}.parameter-snapshot",
                parameter_id=parameter_id,
                factor_id=None,
                value_used=value,
                unit_used="ratio",
                source_id=EVIDENCE_SOURCE_ID,
                source_version=MAPPING_VERSION,
                selection_method=ParameterSelectionMethod.STANDARD_REQUIRED,
                selection_reason=f"未提供企业值，按 {source_location} 的标准一般取值采用。",
                standard_id=STANDARD_ID,
                snapshot_at=snapshot_at,
                factor_version=MAPPING_VERSION,
                source_location=source_location,
            )
        )

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

    def _required_parameter(self, item: object, attr: str, parameter_id: str, default: str, field_id: str, source_location: str, code: str, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime) -> Decimal | None:
        value = getattr(item, attr)
        if value is None:
            value = self._default_parameter(parameter_id, default, field_id, source_location, code, problems)
        return self._parameter(value, "ratio", field_id, snapshots, problems, snapshot_at)

    def _resolve_parameter(self, context: ParameterResolutionContext, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime, *, detail_id: str | None = None) -> Decimal | None:
        if self.parameter_resolver is None:
            problems.append(_problem("CAR-VAL-PARAMETER-RESOLVER-MISSING", IssueLevel.ERROR, f"参数 {context.parameter_id} 没有接入 G05 参数解析服务。", context.parameter_id))
            return None
        resolution = self.parameter_resolver.resolve(context)
        problems.extend(resolution.warnings)
        if resolution.blocked or resolution.recommended is None or resolution.selection_method is None:
            return None
        try:
            snapshot = resolution.to_snapshot(f"{detail_id or context.parameter_id}.parameter-snapshot", snapshot_at, detail_id=detail_id)
            snapshots.append(snapshot)
        except DomainValidationError as exc:
            problems.append(_problem("GEN-VAL-FACTOR-SOURCE", IssueLevel.ERROR, f"参数 {context.parameter_id} 无法形成快照：{exc}", context.parameter_id))
            return None
        return resolution.recommended.factor.value

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
        carbon_unit = {FuelPath.VOLUME: "tC/10^4Nm3", FuelPath.MASS: "tC/t", FuelPath.HEAT: "tC/GJ"}[item.path]
        carbon = self._parameter(item.carbon_content, carbon_unit, f"CAR-FLD-F01-{item.fuel_id}-CARBON", snapshots, problems, snapshot_at)
        fox = self._ratio(item.oxidation_rate, f"CAR-FLD-F01-{item.fuel_id}-FOX", problems)
        if activity is None or carbon is None or fox is None:
            return None
        return {
            FuelPath.VOLUME: fuel_volume_emission(activity, carbon, fox),
            FuelPath.MASS: fuel_mass_emission(activity, carbon, fox),
            FuelPath.HEAT: fuel_heat_emission(activity, carbon, fox),
        }[item.path]

    def _heat_factor(self, line_id: str, explicit: ParameterValue | None, snapshots: list[ParameterSnapshot], problems: list[ValidationProblem], snapshot_at: datetime) -> Decimal | None:
        if explicit is not None:
            return self._parameter(explicit, "tCO2/GJ", f"CAR-FLD-HEAT-{line_id}-EF3", snapshots, problems, snapshot_at)
        if self.parameter_resolver is None:
            problems.append(_problem("CAR-VAL-HEAT-FACTOR-DEFAULT", IssueLevel.WARNING, f"热力明细 {line_id} 未提供排放因子，采用映射中的标准缺省值 0.11。", line_id))
            fallback = ParameterValue("heat_emission_factor_default", "0.11", "tCO2/GJ", source_location="第5.2.6.2条、附录C.3", selection_reason="未接入目录解析器时使用映射中的标准缺省热力因子。")
            return self._parameter(fallback, "tCO2/GJ", f"CAR-FLD-HEAT-{line_id}-EF3", snapshots, problems, snapshot_at)
        resolved = self._resolve_parameter(
            ParameterResolutionContext(
                parameter_id="heat_emission_factor_default",
                standard_id=STANDARD_ID,
                parameter_type=ParameterType.HEAT_EMISSION_FACTOR,
                subject_id="purchased_heat",
            ),
            snapshots,
            problems,
            snapshot_at,
            detail_id=line_id,
        )
        if resolved is not None:
            return resolved
        return None

    def _enthalpy(self, line: HeatInput, problems: list[ValidationProblem]) -> Decimal | None:
        if line.enthalpy is not None:
            return self._quantity(line.enthalpy, "kJ/kg", f"CAR-FLD-HEAT-{line.line_id}-HM", problems)
        if line.pressure_mpa is None:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, f"热力明细 {line.line_id} 缺少蒸汽焓值或压力状态。", line.line_id))
            return None
        if line.steam_kind is SteamKind.SUPERHEATED and line.temperature_c is None:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, f"过热蒸汽明细 {line.line_id} 缺少温度状态。", line.line_id))
            return None
        try:
            if line.steam_kind is SteamKind.SUPERHEATED:
                enthalpy, interpolated, endpoints = superheated_steam_enthalpy(line.pressure_mpa.value, line.temperature_c.value)
                table_id = "C.5"
            else:
                enthalpy, interpolated, endpoints = saturated_steam_enthalpy(line.pressure_mpa.value)
                table_id = "C.4"
        except ValueError as exc:
            problems.append(_problem("CAR-VAL-STEAM-STATE", IssueLevel.ERROR, str(exc), line.line_id))
            return None
        if interpolated:
            problems.append(_problem("CAR-VAL-STEAM-INTERPOLATION", IssueLevel.INFO, f"蒸汽明细 {line.line_id} 使用 {table_id} 邻近状态线性内插。", line.line_id, (("low_pressure_mpa", str(endpoints[0])), ("high_pressure_mpa", str(endpoints[1])), ("algorithm_version", ALGORITHM_VERSION))))
        return enthalpy

    def calculate(self, input_value: CarbonMaterialInput, *, calculated_at: datetime | None = None) -> CarbonMaterialCalculationOutcome:
        if not isinstance(input_value, CarbonMaterialInput):
            raise DomainValidationError("input_value must be a CarbonMaterialInput")
        snapshot_at = calculated_at or datetime.now(timezone.utc)
        if snapshot_at.tzinfo is None:
            raise DomainValidationError("calculated_at must be timezone-aware")
        problems: list[ValidationProblem] = []
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
                if fuel.fuel_id in seen_paths:
                    problems.append(_problem("CAR-VAL-FUEL-PATH-DUPLICATE", IssueLevel.ERROR, f"燃料 {fuel.fuel_id} 按多个路径重复计入。", fuel.fuel_id))
                seen_paths[fuel.fuel_id] = fuel.path
                amount = self._fuel(fuel, snapshots, problems, snapshot_at)
                if amount is not None:
                    fuel_total += amount
                    lines.append(CalculationLine(f"{SOURCE_FUEL}.{fuel.fuel_id}", SOURCE_FUEL, CO2_ID, amount, "tCO2"))
            if input_value.fuel_inputs:
                traces.append(CalculationTrace("CAR-F01", "CAR-FML-FUEL-001", SOURCE_FUEL, (("fuel_total", fuel_total, "tCO2"),), "EFu = sum(EFu(f))", fuel_total))

        def process_value(source_id: str, payload: object | None, fn, formula_id: str, line_id: str, default_codes: tuple[str, ...] = ()) -> Decimal:
            status = self._source_check(input_value, source_id, payload is not None, problems)
            if status is not EmissionSourceStatus.INVOLVED or payload is None:
                return Decimal("0")
            self._basis(payload, source_id, problems)
            values: dict[str, Decimal] = {}
            field_defs = {
                CalcinationInput: (("gc", "t"), ("wfc", "ratio"), ("cc", "t"), ("ucc", "t"), ("du", "t"), ("wfc_c", "ratio"), ("wvar", "ratio"), ("wvar_c", "ratio")),
                BakingInput: (("bpm", "t"), ("bpmfc", "ratio"), ("bg", "t"), ("bgfc", "ratio"), ("bwt", "tC"), ("bp", "t"), ("bpfc", "ratio"), ("bpmvar", "ratio"), ("bgvar", "ratio")),
                GraphitizationInput: (("gpm", "t"), ("gpmfc", "ratio"), ("gta", "t"), ("gtafc", "ratio"), ("gwt", "tC"), ("gp", "t"), ("gpfc", "ratio"), ("gpmvar", "ratio")),
            }
            for attr, unit in field_defs[type(payload)]:
                raw = getattr(payload, attr)
                if unit == "ratio":
                    value = self._ratio(raw, f"{line_id}-{attr}", problems)
                else:
                    value = self._quantity(raw, unit, f"{line_id}-{attr}", problems)
                if value is not None:
                    values[attr] = value
            if isinstance(payload, CalcinationInput):
                k1 = self._required_parameter(payload, "k1", "CAR-PAR-K1", "0.35", "CAR-FLD-P01-K1", "第5.2.2条；一般取0.35", "CAR-VAL-K1-DEFAULT", snapshots, problems, snapshot_at)
                if k1 is not None: values["k1"] = k1
            elif isinstance(payload, BakingInput):
                k2 = self._required_parameter(payload, "k2", "CAR-PAR-K2", "0.35", "CAR-FLD-P02-K2", "第5.2.3条；一般取0.35", "CAR-VAL-K2-DEFAULT", snapshots, problems, snapshot_at)
                if k2 is not None: values["k2"] = k2
            else:
                k3 = self._required_parameter(payload, "k3", "CAR-PAR-K3", "0.35", "CAR-FLD-P03-K3", "第5.2.4条；一般取0.35", "CAR-VAL-K3-DEFAULT", snapshots, problems, snapshot_at)
                if k3 is not None: values["k3"] = k3
            if len(values) < len(field_defs[type(payload)]) + 1:
                return Decimal("0")
            amount = fn(**values)
            if amount < 0:
                problems.append(_problem("CAR-VAL-MATERIAL-BALANCE-NEGATIVE", IssueLevel.ERROR, f"{source_id} 物料平衡结果为负。", source_id))
            if getattr(payload, "carbon_output_included_in_input", False):
                problems.append(_problem("CAR-VAL-CARBON-OUTPUT-DUPLICATE", IssueLevel.ERROR, f"{source_id} 的碳输出已在输入/产量中重复使用。", source_id))
            lines.append(CalculationLine(line_id, source_id, CO2_ID, amount, "tCO2"))
            traces.append(CalculationTrace(line_id, formula_id, source_id, tuple((key, value, "ratio" if key.startswith("w") or key.startswith("b") and key.endswith(("fc", "var")) else "") for key, value in values.items()), f"{formula_id} 按映射变量代入", amount))
            return amount

        calc_total = process_value(SOURCE_CALCINATION, input_value.calcination, calcination_emission, "CAR-FML-CALCINATION-001", "CAR-FLD-P01-RESULT")
        bake_total = process_value(SOURCE_BAKING, input_value.baking, baking_emission, "CAR-FML-BAKING-001", "CAR-FLD-P02-RESULT")
        if input_value.graphitization is not None and input_value.graphitization.furnace_loss_included:
            problems.append(_problem("CAR-VAL-GRAPHITIZATION-FURNACE-LOSS", IssueLevel.ERROR, "石墨化炉本身炭质材料氧化烧损不得计入石墨化排放。", SOURCE_GRAPHITIZATION))
        graph_total = process_value(SOURCE_GRAPHITIZATION, input_value.graphitization, graphitization_emission, "CAR-FML-GRAPHITIZATION-001", "CAR-FLD-P03-RESULT")

        fume_status = self._source_check(input_value, SOURCE_FUME, input_value.fume_incineration is not None, problems)
        fume_total = Decimal("0")
        if fume_status is EmissionSourceStatus.INVOLVED and input_value.fume_incineration is not None:
            item = input_value.fume_incineration
            q = self._quantity(item.q, "Nm3/h", "CAR-FLD-P04A-Q", problems)
            qvar = self._quantity(item.qvar, "mg/Nm3", "CAR-FLD-P04A-QVAR", problems)
            hm = self._quantity(item.hm, "GJ/t", "CAR-FLD-P04A-HM", problems)
            fch = self._parameter(item.fch, "tC/GJ", "CAR-FLD-P04A-FCH", snapshots, problems, snapshot_at)
            fox = self._ratio(item.fox, "CAR-FLD-P04A-FOX", problems)
            duration = self._quantity(item.duration, "d", "CAR-FLD-P04A-T", problems)
            if None not in (q, qvar, hm, fch, fox, duration):
                fume_total = fume_incineration_emission(q, qvar, hm, fch, fox, duration)
                lines.append(CalculationLine("CAR-FLD-P04A-RESULT", SOURCE_FUME, CO2_ID, fume_total, "tCO2"))
                traces.append(CalculationTrace("CAR-P04A", "CAR-FML-FUME-INCINERATION-001", SOURCE_FUME, (), "ER = Q×QVar×HM×FCh×FOx×T×24×44/12×10⁻⁹", fume_total))

        fgd_status = self._source_check(input_value, SOURCE_FGD, input_value.fgd is not None, problems)
        fgd_total = Decimal("0")
        if fgd_status is EmissionSourceStatus.INVOLVED and input_value.fgd is not None:
            components = input_value.fgd.components
            if not components:
                problems.append(
                    _problem(
                        "GEN-VAL-REQUIRED-MISSING",
                        IssueLevel.ERROR,
                        "脱硫净化缺少至少一条碳酸盐组分。",
                        SOURCE_FGD,
                    )
                )
            if input_value.fgd.cal is not None and input_value.fgd.i is None:
                self._default_ratio_snapshot(
                    parameter_id="CAR-PAR-P04B-I",
                    value="0.90",
                    field_id="CAR-FLD-P04B-I-0",
                    code="CAR-VAL-I-DEFAULT",
                    source_location="第5.2.5.2条；一般取90%",
                    snapshots=snapshots,
                    problems=problems,
                    snapshot_at=snapshot_at,
                )
            if input_value.fgd.cal is not None and input_value.fgd.tr is None:
                self._default_ratio_snapshot(
                    parameter_id="CAR-PAR-P04B-TR",
                    value="1",
                    field_id="CAR-FLD-P04B-TR-0",
                    code="CAR-VAL-TR-DEFAULT",
                    source_location="第5.2.5.2条；一般取100%",
                    snapshots=snapshots,
                    problems=problems,
                    snapshot_at=snapshot_at,
                )
            fractions = Decimal("0")
            for index, component in enumerate(components):
                fraction = self._ratio(component.carbonate_fraction, f"CAR-FLD-P04B-I-{index}", problems)
                if fraction is not None:
                    fractions += fraction
            if fractions > Decimal("1"):
                problems.append(_problem("CAR-VAL-CARBONATE-SUM", IssueLevel.ERROR, "多种碳酸盐组分含量合计不得超过100%。", SOURCE_FGD))
            validated: list[CarbonateComponent] = []
            for index, component in enumerate(components):
                amount = self._quantity(component.amount, "t", f"CAR-FLD-P04B-CAL-{index}", problems)
                fraction = self._ratio(component.carbonate_fraction, f"CAR-FLD-P04B-I-{index}", problems)
                factor = self._parameter(component.emission_factor, "tCO2/t", f"CAR-FLD-P04B-EF1-{index}", snapshots, problems, snapshot_at)
                conversion = self._ratio(component.conversion_rate, f"CAR-FLD-P04B-TR-{index}", problems)
                if None not in (amount, fraction, factor, conversion):
                    validated.append(CarbonateComponent(amount, fraction, factor, conversion))
            if validated:
                fgd_total = fgd_emission(validated)
                lines.append(CalculationLine("CAR-FLD-P04B-RESULT", SOURCE_FGD, CO2_ID, fgd_total, "tCO2"))
                traces.append(CalculationTrace("CAR-P04B", "CAR-FML-FGD-001", SOURCE_FGD, (), "ED = sum(CAL×I×EF1×TR)", fgd_total))

        gas_total = fume_total + fgd_total
        if fume_status is EmissionSourceStatus.INVOLVED or fgd_status is EmissionSourceStatus.INVOLVED:
            lines.append(CalculationLine("CAR-FLD-GAS-CONTROL-RESULT", "CAR-SRC-GAS-CONTROL-001", CO2_ID, gas_total, "tCO2"))
            traces.append(CalculationTrace("CAR-P04", "CAR-FML-GAS-CONTROL-TOTAL-001", "CAR-SRC-GAS-CONTROL-001", (), "EP = sum(ER) + sum(ED)", gas_total))

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
                    traces.append(CalculationTrace(detail.detail_id, "CAR-FML-PURCHASED-ELECTRICITY-001", SOURCE_PURCHASED_ELECTRICITY, (("QGe", quantity, "MWh"), ("EF2", resolution.result.recommended.factor.value, resolution.result.recommended.factor.unit)), "EGe = QGe × EF2", amount))

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
                    traces.append(CalculationTrace(line.line_id, "CAR-FML-EXPORTED-ELECTRICITY-001", SOURCE_EXPORTED_ELECTRICITY, (), "ESe = QSe × EF2", amount))

        heat_payload = bool(input_value.purchased_heat)
        heat_status = self._source_check(input_value, SOURCE_PURCHASED_HEAT, heat_payload, problems)
        purchased_heat_total = Decimal("0")
        if heat_status is EmissionSourceStatus.INVOLVED:
            for line in input_value.purchased_heat:
                quantity = self._quantity(line.amount, "kg", line.line_id, problems)
                enthalpy = self._enthalpy(line, problems)
                factor = self._heat_factor(line.line_id, line.factor, snapshots, problems, snapshot_at)
                if None not in (quantity, enthalpy, factor):
                    amount = purchased_heat_emission(quantity, enthalpy, factor)
                    purchased_heat_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-HEAT-PURCHASED-RESULT.{line.line_id}", SOURCE_PURCHASED_HEAT, CO2_ID, amount, "tCO2"))
                    traces.append(CalculationTrace(line.line_id, "CAR-FML-PURCHASED-HEAT-001", SOURCE_PURCHASED_HEAT, (), "EGd = BGd × HM × EF3 / 10⁶", amount))

        exported_heat_status = self._source_check(input_value, SOURCE_EXPORTED_HEAT, bool(input_value.exported_heat), problems)
        exported_heat_total = Decimal("0")
        if exported_heat_status is EmissionSourceStatus.INVOLVED:
            for line in input_value.exported_heat:
                quantity = self._quantity(line.amount, "kg", line.line_id, problems)
                enthalpy = self._enthalpy(line, problems)
                factor = self._heat_factor(line.line_id, line.factor, snapshots, problems, snapshot_at)
                if None not in (quantity, enthalpy, factor):
                    amount = purchased_heat_emission(quantity, enthalpy, factor)
                    exported_heat_total += amount
                    lines.append(CalculationLine(f"CAR-FLD-HEAT-EXPORTED-RESULT.{line.line_id}", SOURCE_EXPORTED_HEAT, CO2_ID, amount, "tCO2"))
                    traces.append(CalculationTrace(line.line_id, "CAR-FML-EXPORTED-HEAT-001", SOURCE_EXPORTED_HEAT, (), "ESd = BSd × HM × EF3 / 10⁶", amount))

        direct_total = direct_emission(fuel_total, calc_total, bake_total, graph_total, gas_total)
        indirect_total = indirect_emission(purchased_power_total, purchased_heat_total, exported_power_total, exported_heat_total)
        grand_total = total_emission(direct_total, indirect_total)
        lines.extend((
            CalculationLine("CAR-FLD-DIRECT-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, direct_total, "tCO2"),
            CalculationLine("CAR-FLD-INDIRECT-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, indirect_total, "tCO2"),
            CalculationLine("CAR-FLD-TOTAL-RESULT", "CAR-RULE-TOTAL-001", CO2_ID, grand_total, "tCO2"),
        ))
        traces.extend((
            CalculationTrace("CAR-DIRECT", "CAR-FML-DIRECT-001", "CAR-RULE-TOTAL-001", (), "ES = EFu + EC + EB + EG + EP", direct_total),
            CalculationTrace("CAR-INDIRECT", "CAR-FML-INDIRECT-001", "CAR-RULE-TOTAL-001", (), "EI = EGe + EGd - ESe - ESd", indirect_total),
            CalculationTrace("CAR-TOTAL", "CAR-FML-TOTAL-001", "CAR-RULE-TOTAL-001", (), "ET = ES + EI", grand_total),
        ))
        calculation_result = CalculationResult("result." + input_value.input_id, STANDARD_ID, ALGORITHM_VERSION, tuple(lines), grand_total, "tCO2", snapshot_at, tuple(problems))
        record: AccountingRecord | None = None
        if not contains_errors(problems):
            generic_input = AccountingInput(
                input_id=input_value.input_id,
                standard_id=STANDARD_ID,
                period=input_value.period,
                enterprise_name=input_value.enterprise_name,
                boundary_component_ids=input_value.boundary_component_ids,
                emission_sources=tuple(EmissionSourceSelection(item.source_id, item.status is EmissionSourceStatus.INVOLVED) for item in input_value.source_states),
            )
            status = RecordStatus.COMPLETED_WITH_WARNINGS if contains_warnings(problems) else RecordStatus.COMPLETED
            record = AccountingRecord("record." + input_value.input_id, STANDARD_ID, ALGORITHM_VERSION, snapshot_at, generic_input, calculation_result, status, tuple(snapshots), tuple(problems))
            self.record_repository.create(record)
        return CarbonMaterialCalculationOutcome(input_value, calculation_result, tuple(problems), tuple(snapshots), tuple(traces), ALGORITHM_VERSION, record)


__all__ = [
    "ALGORITHM_VERSION", "MAPPING_VERSION", "GREEN_ELECTRICITY_EVIDENCE_CODE", "STANDARD_ID", "CarbonMaterialCalculationOutcome", "CarbonMaterialCalculator", "CarbonMaterialInput", "CarbonateComponent", "CalcinationInput", "BakingInput", "GraphitizationInput", "FumeIncinerationInput", "FGDInput", "FuelInput", "HeatInput", "ElectricityOutputLine", "EmissionSourceState", "EmissionSourceStatus", "FuelPath", "InputValue", "MaterialBasis", "MaterialComponentKind", "ParameterSourceKind", "ParameterValue", "SteamKind", "InMemoryRecordRepository", "baking_emission", "calcination_emission", "direct_emission", "fgd_emission", "fuel_energy_from_mass", "fuel_energy_from_volume", "fuel_heat_emission", "fuel_mass_emission", "fuel_volume_emission", "fume_incineration_emission", "graphitization_emission", "indirect_emission", "purchased_electricity_emission", "purchased_heat_emission", "saturated_steam_enthalpy", "superheated_steam_enthalpy", "total_emission",
]
