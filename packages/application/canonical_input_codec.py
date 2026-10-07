"""Lossless, allowlisted JSON codec for saved carbon-accounting inputs.

The format is an implementation detail of GHGTOOL projects. It is deliberately
versioned here and is not a cross-product Workspace contract.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from typing import Any

from packages.core.models import (
    AccountingPeriod,
    ActivityDataSource,
    ActivitySourceLevel,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
    PeriodType,
)
from packages.core.parameter_resolution import ElectricityConsumptionDetail
from packages.standards.carbon_material import (
    ActivityDataEvidence,
    BakingInput,
    CarbonMaterialInput,
    CarbonReportingData,
    CarbonateComponent,
    CalcinationInput,
    EmissionSourceState,
    EmissionSourceStatus,
    ElectricityOutputLine,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatFactorMode,
    HeatInput,
    InputValue,
    MaterialBasis,
    MaterialComponentKind,
    MeasuredFactorEvidence,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
)
from packages.standards.carbon_material_normalization import (
    MaterialDataSource,
    MaterialInputLine,
    MaterialRole,
)


CANONICAL_INPUT_CODEC_VERSION = 1
_CODEC_ID = "ghgtool.carbon_material_input"


class CanonicalInputCodecError(ValueError):
    """Raised when canonical input JSON is invalid or uses an unknown type."""


_DATACLASSES: dict[str, type[Any]] = {
    "accounting_period": AccountingPeriod,
    "activity_data_evidence": ActivityDataEvidence,
    "baking_input": BakingInput,
    "carbon_material_input": CarbonMaterialInput,
    "carbon_reporting_data": CarbonReportingData,
    "carbonate_component": CarbonateComponent,
    "calcination_input": CalcinationInput,
    "electricity_consumption_detail": ElectricityConsumptionDetail,
    "emission_source_state": EmissionSourceState,
    "electricity_output_line": ElectricityOutputLine,
    "fgd_input": FGDInput,
    "fuel_input": FuelInput,
    "fume_incineration_input": FumeIncinerationInput,
    "graphitization_input": GraphitizationInput,
    "heat_input": HeatInput,
    "input_value": InputValue,
    "material_input_line": MaterialInputLine,
    "measured_factor_evidence": MeasuredFactorEvidence,
    "parameter_value": ParameterValue,
}
_ENUMS: dict[str, type[Enum]] = {
    "activity_data_source": ActivityDataSource,
    "activity_source_level": ActivitySourceLevel,
    "electricity_acquisition_mode": ElectricityAcquisitionMode,
    "electricity_attribute": ElectricityAttribute,
    "electricity_proof_status": ElectricityProofStatus,
    "electricity_proof_type": ElectricityProofType,
    "emission_source_status": EmissionSourceStatus,
    "fuel_path": FuelPath,
    "fuel_type": FuelType,
    "heat_factor_mode": HeatFactorMode,
    "material_basis": MaterialBasis,
    "material_component_kind": MaterialComponentKind,
    "material_data_source": MaterialDataSource,
    "material_role": MaterialRole,
    "parameter_source_kind": ParameterSourceKind,
    "period_type": PeriodType,
    "steam_kind": SteamKind,
}
_DATACLASS_IDS = {value: key for key, value in _DATACLASSES.items()}
_ENUM_IDS = {value: key for key, value in _ENUMS.items()}


def _encode_value(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise CanonicalInputCodecError("Decimal values must be finite")
        return {"$kind": "decimal", "value": str(value)}
    if isinstance(value, datetime):
        return {"$kind": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"$kind": "date", "value": value.isoformat()}
    if isinstance(value, Enum):
        enum_id = _ENUM_IDS.get(type(value))
        if enum_id is None:
            raise CanonicalInputCodecError(f"unsupported enum type: {type(value).__name__}")
        return {"$kind": "enum", "type": enum_id, "value": value.value}
    if isinstance(value, float):
        raise CanonicalInputCodecError(
            "floating-point values are not allowed in canonical input; use Decimal"
        )
    if isinstance(value, tuple):
        return {"$kind": "tuple", "items": [_encode_value(item) for item in value]}
    if isinstance(value, list):
        return {"$kind": "list", "items": [_encode_value(item) for item in value]}
    if isinstance(value, dict):
        pairs: list[list[object]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalInputCodecError("mapping keys must be strings")
            pairs.append([key, _encode_value(item)])
        return {"$kind": "mapping", "items": pairs}
    if is_dataclass(value) and not isinstance(value, type):
        dataclass_id = _DATACLASS_IDS.get(type(value))
        if dataclass_id is None:
            raise CanonicalInputCodecError(f"unsupported dataclass type: {type(value).__name__}")
        return {
            "$kind": "dataclass",
            "type": dataclass_id,
            "fields": {
                field.name: _encode_value(getattr(value, field.name))
                for field in fields(value)
            },
        }
    raise CanonicalInputCodecError(f"unsupported canonical input value: {type(value).__name__}")


def _expect_object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CanonicalInputCodecError(f"invalid {label} object")
    return value


def _decode_value(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if not isinstance(value, dict) or not isinstance(value.get("$kind"), str):
        raise CanonicalInputCodecError("canonical values must use a known tagged encoding")
    kind = value["$kind"]
    if kind == "decimal":
        node = _expect_object(value, {"$kind", "value"}, "decimal")
        if not isinstance(node["value"], str):
            raise CanonicalInputCodecError("decimal value must be a string")
        try:
            decimal_value = Decimal(node["value"])
        except Exception as exc:
            raise CanonicalInputCodecError("invalid decimal value") from exc
        if not decimal_value.is_finite():
            raise CanonicalInputCodecError("Decimal values must be finite")
        return decimal_value
    if kind in {"date", "datetime"}:
        node = _expect_object(value, {"$kind", "value"}, kind)
        if not isinstance(node["value"], str):
            raise CanonicalInputCodecError(f"{kind} value must be a string")
        try:
            return date.fromisoformat(node["value"]) if kind == "date" else datetime.fromisoformat(node["value"])
        except ValueError as exc:
            raise CanonicalInputCodecError(f"invalid {kind} value") from exc
    if kind in {"tuple", "list"}:
        node = _expect_object(value, {"$kind", "items"}, kind)
        if not isinstance(node["items"], list):
            raise CanonicalInputCodecError(f"{kind} items must be an array")
        items = [_decode_value(item) for item in node["items"]]
        return tuple(items) if kind == "tuple" else items
    if kind == "mapping":
        node = _expect_object(value, {"$kind", "items"}, "mapping")
        if not isinstance(node["items"], list):
            raise CanonicalInputCodecError("mapping items must be an array")
        result: dict[str, object] = {}
        for pair in node["items"]:
            if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str):
                raise CanonicalInputCodecError("mapping entries must be string-key pairs")
            if pair[0] in result:
                raise CanonicalInputCodecError("mapping contains a duplicate key")
            result[pair[0]] = _decode_value(pair[1])
        return result
    if kind == "enum":
        node = _expect_object(value, {"$kind", "type", "value"}, "enum")
        enum_type = _ENUMS.get(node["type"]) if isinstance(node["type"], str) else None
        if enum_type is None or not isinstance(node["value"], str):
            raise CanonicalInputCodecError("unknown enum type or invalid enum value")
        try:
            return enum_type(node["value"])
        except ValueError as exc:
            raise CanonicalInputCodecError("enum value is not recognized") from exc
    if kind == "dataclass":
        node = _expect_object(value, {"$kind", "type", "fields"}, "dataclass")
        dataclass_type = _DATACLASSES.get(node["type"]) if isinstance(node["type"], str) else None
        if dataclass_type is None or not isinstance(node["fields"], dict):
            raise CanonicalInputCodecError("unknown dataclass type or invalid fields")
        declared_fields = {field.name for field in fields(dataclass_type)}
        if set(node["fields"]) != declared_fields:
            raise CanonicalInputCodecError(f"fields do not match {node['type']} schema")
        decoded = {
            name: _decode_value(field_value)
            for name, field_value in node["fields"].items()
        }
        try:
            return dataclass_type(**decoded)
        except (TypeError, ValueError) as exc:
            raise CanonicalInputCodecError(f"invalid {node['type']} value: {exc}") from exc
    raise CanonicalInputCodecError(f"unknown canonical value tag: {kind}")


def _reject_constant(value: str) -> None:
    raise CanonicalInputCodecError(f"invalid JSON constant: {value}")


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalInputCodecError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def encode_canonical_input(input_value: CarbonMaterialInput) -> str:
    """Encode one complete immutable domain input as deterministic typed JSON."""

    if not isinstance(input_value, CarbonMaterialInput):
        raise CanonicalInputCodecError("input_value must be a CarbonMaterialInput")
    document = {
        "codec": _CODEC_ID,
        "version": CANONICAL_INPUT_CODEC_VERSION,
        "value": _encode_value(input_value),
    }
    try:
        return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise CanonicalInputCodecError(f"cannot encode canonical input: {exc}") from exc


def decode_canonical_input(payload: str) -> CarbonMaterialInput:
    """Decode typed JSON using only the fixed domain type allowlist above."""

    if not isinstance(payload, str):
        raise CanonicalInputCodecError("canonical input payload must be text")
    try:
        document = json.loads(
            payload,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise CanonicalInputCodecError(f"invalid canonical input JSON: {exc}") from exc
    if not isinstance(document, dict) or set(document) != {"codec", "version", "value"}:
        raise CanonicalInputCodecError("invalid canonical input envelope")
    if document["codec"] != _CODEC_ID:
        raise CanonicalInputCodecError("unrecognized canonical input codec")
    if type(document["version"]) is not int or document["version"] != CANONICAL_INPUT_CODEC_VERSION:
        raise CanonicalInputCodecError("unsupported canonical input codec version")
    try:
        input_value = _decode_value(document["value"])
    except (RecursionError, KeyError, TypeError) as exc:
        raise CanonicalInputCodecError(f"invalid typed canonical input: {exc}") from exc
    if not isinstance(input_value, CarbonMaterialInput):
        raise CanonicalInputCodecError("canonical input payload did not contain CarbonMaterialInput")
    return input_value


__all__ = [
    "CANONICAL_INPUT_CODEC_VERSION",
    "CanonicalInputCodecError",
    "decode_canonical_input",
    "encode_canonical_input",
]