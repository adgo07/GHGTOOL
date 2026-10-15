"""Strict, review-only loader for business rule candidate JSON bundles.

This module is intentionally not imported by production application modules. It
validates a fixed candidate bundle and delegates rule composition to the existing
G05 domain resolver without changing its production defaults.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from packages.core import (
    EffectiveRuleResolver,
    EffectiveRuleSet,
    IssueLevel,
    ParameterSelectionPolicy,
    ParameterType,
    RuleApplicability,
    RuleContext,
    RuleDefinition,
    RuleEvidenceStatus,
    RuleOrigin,
    RuleRelation,
    ValidationProblem,
)


SCHEMA_VERSION = "1.2"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
_SOURCE_STATES = {"STANDARD_DEFAULT", "CALCULATED", "MEASURED"}
_LOCK_STATES = {"EDITABLE", "LOCKED", "CONDITIONAL", "NOT_APPLICABLE", "PENDING"}
_PACKAGE_KINDS = {"COMMON", "INDUSTRY", "SOFTWARE"}
_FIELD_KINDS = {"text", "quantity", "percentage", "integer", "enum", "boolean",
                "readonly_parameter", "metadata", "status", "report"}
_NUMERIC_FIELD_KINDS = {"quantity", "percentage", "integer", "readonly_parameter"}
_DECIMAL_LITERAL = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
# Integer defaults expressed as strings use plain integer digits with an
# optional all-zero fractional suffix (for example "100" or "-2.00"). JSON
# number values are checked mathematically for integrality; exponent notation
# is intentionally not part of the string form (so "1e0" is rejected).
_INTEGER_DECIMAL_LITERAL = re.compile(r"-?(0|[1-9][0-9]*)(\.0+)?")
_COUNT_BOUND_LITERAL = re.compile(r"(0|[1-9][0-9]*)(\.0+)?")
_CONTEXT_ENUMS = {
    "origin": {"CATALOG", "CUSTOM", "LEGACY_UNSPECIFIED"},
    "business_source": {"STANDARD_DEFAULT", "CALCULATED", "MEASURED"},
    "binding_status": {"VERIFIED", "ABSENT", "PENDING"},
    "component_mode": {"DIRECT", "FCH"},
    "source_path": {"CATALOGUE_TABLE_1", "CATALOGUE_TABLE_2", "CATALOGUE_TABLE_3",
                    "CATALOGUE_TABLE_4", "CATALOGUE_TABLE_5", "NONFOSSIL_ZERO",
                    "SUPPLY_UNIT_MEASURED", "ENTERPRISE_MEASURED", "ENTERPRISE_CALCULATED",
                    "ARBITRARY_OVERRIDE"},
    "direction": {"PURCHASED", "EXPORTED"},
    "attribute": {"CONVENTIONAL", "NONFOSSIL", "FOSSIL"},
    "catalog_table": {"1", "2", "3", "4", "5"},
    "period_type": {"ANNUAL", "MONTHLY", "CUSTOM"},
    "fuel_path": {"MASS", "VOLUME", "HEAT"},
}
_CONTEXT_TEXT_KEYS = {"parameter_id", "binding_id", "standard_id", "region", "province"}
_CONTEXT_TOKEN_KEYS = {"parameter_id", "binding_id", "standard_id"}
_CONTEXT_TAG_KEYS = set(_CONTEXT_ENUMS) | _CONTEXT_TEXT_KEYS
_CONTEXT_RANGE_KEYS = {"carbonate_component_count"}
_APPLICABILITY_SCOPES = {"ALL_ADOPTED", "FILTERED", "NOT_APPLICABLE"}
_RULE_FIELDS = {
    "rule_id", "rule_domain", "relation", "description", "standard_id", "target_id",
    "applicability", "priority", "origin", "evidence_status", "supersedes_rule_ids",
    "conflict_resolved", "resolution_reason", "parameter_id", "selection_policy",
    "required_factor_id", "required_factor_version", "payload", "applies_to_parameter_ids",
    "required_factor_ids", "source_location", "evidence_source_id", "confirmation_id",
}
_APPLICABILITY_FIELDS = {
    "scope", "standard_ids", "regions", "industries", "subject_ids", "parameter_types",
    "emission_source_types", "greenhouse_gases", "period_from", "period_to", "conditions",
    "reason",
}
_DEFAULT_SHAPES = {
    "NONE": {"state"},
    "FIXED": {"state", "value"},
    "BINDING": {"state", "parameter_id"},
    "POLICY": {"state", "policy_id"},
    "PENDING": {"state", "reason"},
}
_SOURCE_SHAPES = {
    "NOT_APPLICABLE": {"state", "reason"},
    "NO_LEGAL_SOURCES": {"state", "reason"},
    "FIXED": {"state", "values"},
    "POLICY": {"state", "policy_id"},
    "PENDING": {"state", "reason"},
}
_PACKAGE_FIELDS = {
    "schema_version", "rule_set_id", "kind", "revision", "base", "dependency", "status",
    "groups", "adopts", "rules", "policies", "fields", "operations", "changes",
}
_FIELD_KEYS = {
    "id", "name", "kind", "unit", "source_qualification", "default", "locking",
    "channel_projections", "basis", "consumers", "cases", "pending", "rule_ids",
}
_OPERATION_KEYS = {
    "key", "operation_id", "name", "initial_context", "action", "changes", "preserves",
    "invalidates", "confirmation", "basis", "cases", "pending", "rule_ids",
}
_CHANGE_KEYS = {"key", "change_type", "before", "after", "reason", "basis", "pending"}


class CandidateBundleError(ValueError):
    """Raised when candidate JSON is incomplete, ambiguous, or unsafe to apply."""


def _fail(path: str, message: str) -> None:
    raise CandidateBundleError(f"{path}: {message}")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    return value


def _keys(value: Any, required: set[str], path: str) -> dict[str, Any]:
    obj = _object(value, path)
    missing = required - set(obj)
    unknown = set(obj) - required
    if missing:
        _fail(path, f"missing required keys: {', '.join(sorted(missing))}")
    if unknown:
        _fail(path, f"unknown keys: {', '.join(sorted(unknown))}")
    return obj


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(path, "must be a non-empty string")
    return value.strip()


def _token(value: Any, path: str) -> str:
    result = _text(value, path)
    if value != result:
        _fail(path, "stable identifiers must not have surrounding whitespace")
    if not _TOKEN.fullmatch(result):
        _fail(path, "must be a stable TOKEN")
    return result


def _nullable_token(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return _token(value, path)


def _enum(value: Any, values: Iterable[str], path: str) -> str:
    result = _text(value, path)
    if value != result:
        _fail(path, "enum values must not have surrounding whitespace")
    allowed = set(values)
    if result not in allowed:
        _fail(path, f"unknown value {result!r}; expected one of {', '.join(sorted(allowed))}")
    return result


def _string_array(value: Any, path: str, *, minimum: int = 0, tokens: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail(path, "must be an array")
    if len(value) < minimum:
        _fail(path, f"must contain at least {minimum} item(s)")
    result = tuple((_token(item, f"{path}[{index}]") if tokens else _text(item, f"{path}[{index}]"))
                   for index, item in enumerate(value))
    if len(set(result)) != len(result):
        _fail(path, "must not contain duplicates")
    return result


def _string_map(value: Any, path: str) -> dict[str, str]:
    obj = _object(value, path)
    result: dict[str, str] = {}
    for key, item in obj.items():
        result[_token(key, f"{path} key")] = _text(item, f"{path}.{key}")
    return result


def _date(value: Any, path: str) -> date | None:
    if value is None:
        return None
    text = _text(value, path)
    if value != text:
        _fail(path, "date values must not have surrounding whitespace")
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise CandidateBundleError(f"{path}: expected ISO date YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        _fail(path, "must use canonical YYYY-MM-DD form")
    return parsed


def _parse_constant(value: str) -> None:
    raise CandidateBundleError(f"JSON non-finite number {value!r} is forbidden")


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateBundleError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            result = json.load(
                stream,
                object_pairs_hook=_object_pairs,
                parse_float=Decimal,
                parse_int=int,
                parse_constant=_parse_constant,
            )
    except CandidateBundleError as exc:
        raise CandidateBundleError(f"{path}: {exc}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError, InvalidOperation) as exc:
        raise CandidateBundleError(f"{path}: cannot read strict JSON: {exc}") from exc
    return _object(result, str(path))


def _decimal_text(value: Any, path: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        _fail(path, "must be a decimal string")
    if value != value.strip():
        _fail(path, "decimal strings must not have surrounding whitespace")
    if not _DECIMAL_LITERAL.fullmatch(value):
        _fail(path, "must use a finite decimal literal")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise CandidateBundleError(f"{path}: invalid decimal string") from exc
    if not parsed.is_finite():
        _fail(path, "must be finite")
    return parsed


def _decimal_is_integral(value: Decimal) -> bool:
    parts = value.as_tuple()
    exponent = parts.exponent
    if exponent >= 0:
        return True
    digits = parts.digits
    fractional_places = -exponent
    return all(digit == 0 for digit in digits[-min(fractional_places, len(digits)):])


def _validate_numeric_default(value: Any, path: str, field_kind: str) -> None:
    if field_kind not in _NUMERIC_FIELD_KINDS:
        return
    if isinstance(value, bool):
        _fail(path, "numeric fields cannot use boolean defaults")
    if isinstance(value, str):
        if field_kind == "integer" and not _INTEGER_DECIMAL_LITERAL.fullmatch(value):
            _fail(path, "integer defaults must use an integral decimal literal")
        number = _decimal_text(value, path)
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, Decimal):
        number = value
    else:
        _fail(path, "numeric defaults must be a finite JSON number or decimal string")
    if not number.is_finite():
        _fail(path, "numeric defaults must be finite")
    if field_kind == "integer" and not _decimal_is_integral(number):
        _fail(path, "integer defaults must be integral")


def _validate_default_for_kind(value: Mapping[str, Any], path: str, field_kind: str) -> None:
    if value["state"] != "FIXED":
        return
    fixed = value["value"]
    if field_kind == "boolean":
        if not isinstance(fixed, bool):
            _fail(path, "boolean fields require a JSON boolean default")
    elif isinstance(fixed, bool):
        _fail(path, "only boolean fields may use boolean defaults")
    if isinstance(fixed, str) and not fixed.strip() and not (field_kind == "text" and fixed == ""):
        _fail(path, "blank defaults are allowed only for explicit empty text values")
    _validate_numeric_default(fixed, path, field_kind)


def _validate_state(value: Any, path: str, *, source: bool = False,
                    allow_boolean: bool = False, allow_empty_string: bool = False) -> dict[str, Any]:
    obj = _object(value, path)
    state = _enum(obj.get("state"), _SOURCE_SHAPES if source else _DEFAULT_SHAPES, f"{path}.state")
    expected = (_SOURCE_SHAPES if source else _DEFAULT_SHAPES)[state]
    if set(obj) != expected:
        _fail(path, f"state {state} requires exactly: {', '.join(sorted(expected))}")
    if state in {"PENDING", "NOT_APPLICABLE", "NO_LEGAL_SOURCES"}:
        _text(obj["reason"], f"{path}.reason")
    elif state == "FIXED" and source:
        values = _string_array(obj["values"], f"{path}.values", minimum=1, tokens=True)
        unknown = set(values) - _SOURCE_STATES
        if unknown:
            _fail(f"{path}.values", f"unknown business sources: {', '.join(sorted(unknown))}")
    elif state == "FIXED":
        fixed = obj["value"]
        if fixed is None or isinstance(fixed, (dict, list)):
            _fail(f"{path}.value", "must be a scalar string, boolean field value, or finite JSON number")
        if isinstance(fixed, bool):
            if not allow_boolean:
                _fail(f"{path}.value", "boolean defaults are valid only for boolean fields")
        elif not isinstance(fixed, (str, int, Decimal)):
            _fail(f"{path}.value", "must be a scalar string, boolean field value, or finite JSON number")
        if isinstance(fixed, Decimal) and not fixed.is_finite():
            _fail(f"{path}.value", "must be finite")
        if isinstance(fixed, str) and not fixed.strip() and not (allow_empty_string and fixed == ""):
            _fail(f"{path}.value", "must not be blank")
    elif state == "BINDING":
        _token(obj["parameter_id"], f"{path}.parameter_id")
    elif state == "POLICY":
        _token(obj["policy_id"], f"{path}.policy_id")
    return dict(obj)


def _validate_locking(value: Any, path: str, *, allow_policy: bool = True) -> dict[str, Any]:
    obj = _object(value, path)
    if obj.get("state") == "POLICY":
        if not allow_policy:
            _fail(path, "locking policy branches must contain a complete value/source locking object")
        policy = _keys(obj, {"state", "policy_id"}, path)
        _token(policy["policy_id"], f"{path}.policy_id")
        return dict(policy)
    obj = _keys(obj, {"value", "source"}, path)
    result: dict[str, dict[str, str]] = {}
    for property_name in ("value", "source"):
        state = _keys(obj[property_name], {"state", "reason"}, f"{path}.{property_name}")
        _enum(state["state"], _LOCK_STATES, f"{path}.{property_name}.state")
        _text(state["reason"], f"{path}.{property_name}.reason")
        result[property_name] = dict(state)
    return result


def _validate_range(value: Any, path: str, context_key: str | None = None) -> dict[str, Any]:
    obj = _object(value, path)
    allowed = {"min", "max", "include_min", "include_max"}
    if set(obj) - allowed:
        _fail(path, f"unknown range keys: {', '.join(sorted(set(obj) - allowed))}")
    if "min" not in obj and "max" not in obj:
        _fail(path, "requires min or max")
    result = dict(obj)
    for bound in ("min", "max"):
        include = "include_" + bound
        if bound in obj:
            _decimal_text(obj[bound], f"{path}.{bound}")
            if context_key == "carbonate_component_count" and not _COUNT_BOUND_LITERAL.fullmatch(obj[bound]):
                _fail(f"{path}.{bound}", "carbonate component count bounds must be non-negative integer literals")
            if include not in obj or not isinstance(obj[include], bool):
                _fail(path, f"{include} must be present with a {bound} bound")
        elif include in obj:
            _fail(path, f"{include} cannot appear without {bound}")
    if "min" in obj and "max" in obj:
        lower = _decimal_text(obj["min"], f"{path}.min")
        upper = _decimal_text(obj["max"], f"{path}.max")
        if lower > upper:
            _fail(path, "min must not exceed max")
        if lower == upper and not (obj["include_min"] and obj["include_max"]):
            _fail(path, "an equal-bound range must include its only value")
    if context_key == "carbonate_component_count":
        _count_integer_domain(result, path)
    return result


def _validate_when(value: Any, path: str) -> dict[str, Any]:
    obj = _keys(value, {"tags", "ranges"}, path)
    tags_obj = _object(obj["tags"], f"{path}.tags")
    tags: dict[str, str] = {}
    for raw_key, raw_value in tags_obj.items():
        key = _token(raw_key, f"{path}.tags key")
        if key not in _CONTEXT_TAG_KEYS:
            _fail(f"{path}.tags.{key}", "context key is not registered")
        if key in _CONTEXT_ENUMS:
            tags[key] = _enum(raw_value, _CONTEXT_ENUMS[key], f"{path}.tags.{key}")
        elif key in _CONTEXT_TOKEN_KEYS:
            tags[key] = _token(raw_value, f"{path}.tags.{key}")
        else:
            tag_text = _text(raw_value, f"{path}.tags.{key}")
            if raw_value != tag_text:
                _fail(f"{path}.tags.{key}", "context tag text must not have surrounding whitespace")
            tags[key] = tag_text
    ranges_obj = _object(obj["ranges"], f"{path}.ranges")
    ranges: dict[str, Any] = {}
    for raw_key, item in ranges_obj.items():
        key = _token(raw_key, f"{path}.ranges key")
        if key not in _CONTEXT_RANGE_KEYS:
            _fail(f"{path}.ranges.{key}", "range context key is not registered")
        ranges[key] = _validate_range(item, f"{path}.ranges.{key}", context_key=key)
    if not tags and not ranges:
        _fail(path, "must declare at least one context tag or range")
    return {"tags": tags, "ranges": ranges}


def _validate_policy(value: Any, path: str) -> dict[str, Any]:
    obj = _keys(value, {"id", "property", "strategy", "branches"}, path)
    policy_id = _token(obj["id"], f"{path}.id")
    property_name = _enum(obj["property"], {"default", "source_qualification", "locking"}, f"{path}.property")
    strategy = _enum(obj["strategy"], {"UNIQUE_CONTEXT_MATCH"}, f"{path}.strategy")
    if not isinstance(obj["branches"], list) or not obj["branches"]:
        _fail(f"{path}.branches", "must be a non-empty array")
    branches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(obj["branches"]):
        branch_path = f"{path}.branches[{index}]"
        branch = _keys(raw, {"id", "when", "value"}, branch_path)
        branch_id = _token(branch["id"], f"{branch_path}.id")
        if branch_id in seen:
            _fail(f"{branch_path}.id", "duplicate branch ID")
        seen.add(branch_id)
        if property_name == "locking":
            outcome = _validate_locking(branch["value"], f"{branch_path}.value", allow_policy=False)
        else:
            outcome = _validate_state(branch["value"], f"{branch_path}.value",
                                      source=property_name == "source_qualification",
                                      allow_boolean=property_name == "default",
                                      allow_empty_string=property_name == "default")
            if outcome["state"] == "POLICY":
                _fail(f"{branch_path}.value.state", "policy branch values must be terminal; nested POLICY is not supported")
        branches.append({"id": branch_id, "when": _validate_when(branch["when"], f"{branch_path}.when"),
                         "value": outcome})
    return {"id": policy_id, "property": property_name, "strategy": strategy, "branches": branches}


def _validate_applicability(value: Any, path: str) -> tuple[RuleApplicability, str, str | None]:
    obj = _keys(value, {
        "scope", "standard_ids", "regions", "industries", "subject_ids", "parameter_types",
        "emission_source_types", "greenhouse_gases", "period_from", "period_to", "conditions", "reason",
    }, path)
    scope = _enum(obj["scope"], _APPLICABILITY_SCOPES, f"{path}.scope")
    standard_ids = _string_array(obj["standard_ids"], f"{path}.standard_ids", tokens=True)
    regions = _string_array(obj["regions"], f"{path}.regions")
    industries = _string_array(obj["industries"], f"{path}.industries")
    subject_ids = _string_array(obj["subject_ids"], f"{path}.subject_ids", tokens=True)
    parameter_types = _string_array(obj["parameter_types"], f"{path}.parameter_types", tokens=True)
    valid_parameter_types = {item.value for item in ParameterType}
    if set(parameter_types) - valid_parameter_types:
        _fail(f"{path}.parameter_types", "contains an unknown ParameterType")
    emission_source_types = _string_array(obj["emission_source_types"], f"{path}.emission_source_types", tokens=True)
    greenhouse_gases = _string_array(obj["greenhouse_gases"], f"{path}.greenhouse_gases", tokens=True)
    period_from = _date(obj["period_from"], f"{path}.period_from")
    period_to = _date(obj["period_to"], f"{path}.period_to")
    if period_from and period_to and period_to < period_from:
        _fail(path, "period_to must be on or after period_from")
    conditions = _string_map(obj["conditions"], f"{path}.conditions")
    reason = obj["reason"]
    if scope == "NOT_APPLICABLE":
        reason = _text(reason, f"{path}.reason")
        if (standard_ids or regions or industries or subject_ids or parameter_types
                or emission_source_types or greenhouse_gases or period_from or period_to or conditions):
            _fail(path, "NOT_APPLICABLE cannot also contain executable filters")
    else:
        if reason is not None:
            _fail(f"{path}.reason", "must be null unless scope is NOT_APPLICABLE")
        if scope == "FILTERED" and not (
            standard_ids or regions or industries or subject_ids or parameter_types
            or emission_source_types or greenhouse_gases or period_from or period_to or conditions
        ):
            _fail(path, "FILTERED requires at least one non-empty condition")
    applicability = RuleApplicability(
        standard_ids=standard_ids,
        regions=regions,
        industries=industries,
        subject_ids=subject_ids,
        parameter_types=tuple(ParameterType(item) for item in parameter_types),
        emission_source_types=emission_source_types,
        greenhouse_gases=greenhouse_gases,
        period_from=period_from,
        period_to=period_to,
        conditions=tuple(sorted(conditions.items())),
    )
    return applicability, scope, reason


def _parse_rule(value: Any, path: str) -> tuple[RuleDefinition, str, str | None]:
    obj = _keys(value, _RULE_FIELDS, path)
    applicability, scope, reason = _validate_applicability(obj["applicability"], f"{path}.applicability")
    def optional_text(key: str) -> str | None:
        value = obj[key]
        return None if value is None else _text(value, f"{path}.{key}")
    def optional_id(key: str) -> str | None:
        return None if obj[key] is None else _token(obj[key], f"{path}.{key}")
    payload = _string_map(obj["payload"], f"{path}.payload")
    priority = obj["priority"]
    if not isinstance(priority, int) or isinstance(priority, bool):
        _fail(f"{path}.priority", "must be an integer")
    rule = RuleDefinition(
        rule_id=_token(obj["rule_id"], f"{path}.rule_id"),
        rule_domain=_token(obj["rule_domain"], f"{path}.rule_domain"),
        relation=RuleRelation(_enum(obj["relation"], {item.value for item in RuleRelation}, f"{path}.relation")),
        description=_text(obj["description"], f"{path}.description"),
        standard_id=optional_id("standard_id"),
        target_id=optional_id("target_id"),
        applicability=applicability,
        priority=priority,
        origin=RuleOrigin(_enum(obj["origin"], {item.value for item in RuleOrigin}, f"{path}.origin")),
        evidence_status=RuleEvidenceStatus(
            _enum(obj["evidence_status"], {item.value for item in RuleEvidenceStatus}, f"{path}.evidence_status")
        ),
        supersedes_rule_ids=_string_array(obj["supersedes_rule_ids"], f"{path}.supersedes_rule_ids", tokens=True),
        conflict_resolved=_boolean(obj["conflict_resolved"], f"{path}.conflict_resolved"),
        resolution_reason=optional_text("resolution_reason"),
        parameter_id=optional_id("parameter_id"),
        selection_policy=(
            None if obj["selection_policy"] is None else ParameterSelectionPolicy(
                _enum(obj["selection_policy"], {item.value for item in ParameterSelectionPolicy},
                      f"{path}.selection_policy")
            )
        ),
        required_factor_id=optional_id("required_factor_id"),
        required_factor_version=optional_id("required_factor_version"),
        payload=tuple(sorted(payload.items())),
        applies_to_parameter_ids=_string_array(
            obj["applies_to_parameter_ids"], f"{path}.applies_to_parameter_ids", tokens=True
        ),
        required_factor_ids=_string_array(obj["required_factor_ids"], f"{path}.required_factor_ids", tokens=True),
        source_location=optional_text("source_location"),
        evidence_source_id=optional_id("evidence_source_id"),
        confirmation_id=optional_id("confirmation_id"),
    )
    return rule, scope, reason


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        _fail(path, "must be a boolean")
    return value


def _coefficient_at(value: Decimal, exponent: int) -> int:
    parts = value.as_tuple()
    coefficient = int("".join(str(digit) for digit in parts.digits) or "0")
    if parts.sign:
        coefficient = -coefficient
    return coefficient * (10 ** (parts.exponent - exponent))


def _decimal_from_coefficient(coefficient: int, exponent: int) -> Decimal:
    sign = 1 if coefficient < 0 else 0
    digits_text = str(abs(coefficient))
    digits = tuple(int(char) for char in digits_text) or (0,)
    return Decimal((sign, digits, exponent))


def _decimal_plus_integer(value: Decimal, amount: int) -> Decimal:
    exponent = min(value.as_tuple().exponent, 0)
    coefficient = _coefficient_at(value, exponent) + amount * (10 ** -exponent)
    return _decimal_from_coefficient(coefficient, exponent)


def _count_integer_domain(bounds: Mapping[str, Any], path: str) -> tuple[Decimal, Decimal | None]:
    lower = Decimal(0)
    upper: Decimal | None = None
    if "min" in bounds:
        raw_lower = bounds["min"]
        if not isinstance(raw_lower, str) or not _COUNT_BOUND_LITERAL.fullmatch(raw_lower):
            _fail(f"{path}.min", "carbonate component count bounds must be non-negative integer literals")
        min_value = _decimal_text(raw_lower, f"{path}.min")
        lower = min_value if bounds["include_min"] else _decimal_plus_integer(min_value, 1)
    if "max" in bounds:
        raw_upper = bounds["max"]
        if not isinstance(raw_upper, str) or not _COUNT_BOUND_LITERAL.fullmatch(raw_upper):
            _fail(f"{path}.max", "carbonate component count bounds must be non-negative integer literals")
        max_value = _decimal_text(raw_upper, f"{path}.max")
        upper = max_value if bounds["include_max"] else _decimal_plus_integer(max_value, -1)
    if upper is not None and (upper < 0 or lower > upper):
        _fail(path, "range contains no non-negative integer carbonate component count")
    return lower, upper


def _exact_midpoint(low: Decimal, high: Decimal) -> Decimal:
    exponent = min(low.as_tuple().exponent, high.as_tuple().exponent)
    summed = _coefficient_at(low, exponent) + _coefficient_at(high, exponent)
    # Division by two is exact after multiplying the coefficient by five and
    # reducing the decimal exponent by one; no ambient Decimal context is used.
    return _decimal_from_coefficient(summed * 5, exponent - 1)


@dataclass(frozen=True)
class CandidatePackage:
    path: Path
    document: Mapping[str, Any]
    rules: Mapping[str, RuleDefinition]
    rule_scopes: Mapping[str, str]
    rule_reasons: Mapping[str, str | None]
    policies: Mapping[str, Mapping[str, Any]]

    @property
    def rule_set_id(self) -> str:
        return str(self.document["rule_set_id"])

    @property
    def kind(self) -> str:
        return str(self.document["kind"])

    @property
    def revision(self) -> str:
        return str(self.document["revision"])


def _known_standard_ids_for(
    package: CandidatePackage,
    packages_by_id: Mapping[str, CandidatePackage],
) -> set[str]:
    """Resolve standard identities from this package's own effective rules only."""
    selected = _effective_rule_ids_for(package, packages_by_id)
    known: set[str] = set()
    for rule_set_id, rule_ids in selected.items():
        candidate = packages_by_id[rule_set_id]
        for rule_id, rule in candidate.rules.items():
            if rule_id not in rule_ids:
                continue
            if rule.standard_id is not None:
                known.add(rule.standard_id)
            known.update(rule.applicability.standard_ids)
    return known


def _effective_rule_ids_for(
    package: CandidatePackage,
    packages_by_id: Mapping[str, CandidatePackage],
) -> dict[str, set[str]]:
    """Return own, adopted COMMON, and fixed SOFTWARE dependency rule IDs."""
    selected: dict[str, set[str] | None] = {package.rule_set_id: None}
    pending = [package]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current.rule_set_id in visited:
            continue
        visited.add(current.rule_set_id)
        for dependency in current.document["dependency"]:
            target = packages_by_id.get(dependency["rule_set_id"])
            if target is not None and target.kind == "SOFTWARE":
                selected[target.rule_set_id] = None
                pending.append(target)
        for adoption in current.document["adopts"]:
            target = packages_by_id.get(adoption["rule_set_id"])
            if target is None or target.kind != "COMMON":
                continue
            allowed = set(adoption["rule_ids"])
            existing = selected.get(target.rule_set_id)
            if target.rule_set_id not in selected:
                selected[target.rule_set_id] = allowed
            elif existing is not None:
                existing.update(allowed)

    result: dict[str, set[str]] = {}
    for rule_set_id, allowed_rule_ids in selected.items():
        candidate = packages_by_id[rule_set_id]
        result[rule_set_id] = set(candidate.rules) if allowed_rule_ids is None else set(allowed_rule_ids)
    return result


@dataclass(frozen=True)
class CandidateBundle:
    """A validated, review-only set of packages and their fixed dependencies."""

    packages: tuple[CandidatePackage, ...]
    primary_rule_set_id: str

    @property
    def primary(self) -> CandidatePackage:
        return next(package for package in self.packages if package.rule_set_id == self.primary_rule_set_id)

    def _selected_packages(self) -> list[CandidatePackage]:
        """Return package scope independently of whether a package has field rows."""
        by_id = {package.rule_set_id: package for package in self.packages}
        primary = self.primary
        adopted_ids = {item["rule_set_id"] for item in primary.document["adopts"]}
        reachable: set[str] = set()
        pending = [primary.rule_set_id]
        while pending:
            current_id = pending.pop()
            if current_id in reachable:
                continue
            reachable.add(current_id)
            current = by_id[current_id]
            pending.extend(item["rule_set_id"] for item in current.document["dependency"])

        selected: list[CandidatePackage] = [primary]
        for package in self.packages:
            if package.rule_set_id == primary.rule_set_id:
                continue
            if package.kind == "COMMON" and package.rule_set_id in adopted_ids:
                selected.append(package)
            elif package.kind == "SOFTWARE" and package.rule_set_id in reachable:
                selected.append(package)
        return selected

    def _field_entries(self) -> list[tuple[CandidatePackage, Mapping[str, Any]]]:
        """Select fields governed by the primary, adopted common, or declared software packages."""
        primary = self.primary
        adopted = {
            item["rule_set_id"]: set(item["rule_ids"])
            for item in primary.document["adopts"]
        }
        entries: list[tuple[CandidatePackage, Mapping[str, Any]]] = []
        for package in self._selected_packages():
            fields = package.document["fields"]
            if package.kind == "COMMON" and package.rule_set_id in adopted and package is not primary:
                allowed = adopted[package.rule_set_id]
                fields = [
                    field for field in fields
                    if field["rule_ids"] and set(field["rule_ids"]) <= allowed
                ]
            entries.extend((package, item) for item in fields)
        return entries

    def _policy(self, package: CandidatePackage, policy_id: str) -> Mapping[str, Any]:
        try:
            return package.policies[policy_id]
        except KeyError as exc:
            raise CandidateBundleError(f"{package.path}: field references unknown policy {policy_id!r}") from exc

    @staticmethod
    def _condition_matches(when: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        for key, expected in when["tags"].items():
            if key not in context or context[key] != expected:
                return False
        for key, bounds in when["ranges"].items():
            if key not in context:
                return False
            raw = context[key]
            if isinstance(raw, bool) or not isinstance(raw, (Decimal, int)):
                return False
            actual = raw if isinstance(raw, Decimal) else Decimal(raw)
            if "min" in bounds:
                lower = _decimal_text(bounds["min"], f"range.{key}.min")
                if actual < lower or (actual == lower and not bounds["include_min"]):
                    return False
            if "max" in bounds:
                upper = _decimal_text(bounds["max"], f"range.{key}.max")
                if actual > upper or (actual == upper and not bounds["include_max"]):
                    return False
        return True

    def _apply_policy(self, policy: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
        matches = [branch for branch in policy["branches"] if self._condition_matches(branch["when"], context)]
        if len(matches) == 1:
            branch = matches[0]
            state = dict(branch["value"])
            if policy["property"] == "locking":
                status = "RESOLVED"
                message = None
            else:
                status = (
                    state["state"] if state["state"] in {"PENDING", "NO_LEGAL_SOURCES"}
                    else "RESOLVED"
                )
                message = state.get("reason") if status != "RESOLVED" else None
            return {"status": status, "value": state, "condition_id": branch["id"],
                    "policy_id": policy["id"], "message": message}
        if len(matches) > 1:
            return {"status": "AMBIGUOUS_POLICY_MATCH", "value": None, "condition_id": None,
                    "policy_id": policy["id"], "message": "More than one policy branch matched"}
        return {"status": "MISSING_CONTEXT", "value": None, "condition_id": None,
                "policy_id": policy["id"], "message": "No unique policy branch matched; context is incomplete"}

    def _known_standard_ids(self) -> set[str]:
        return _known_standard_ids_for(self.primary, {item.rule_set_id: item for item in self.packages})

    def apply_context(
        self,
        context: Mapping[str, Any] | None = None,
        *,
        field_ids: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Resolve selected fields; blocked states remain local to their field and property."""
        current = {} if context is None else _object(dict(context), "context")
        allowed_keys = _CONTEXT_TAG_KEYS | _CONTEXT_RANGE_KEYS
        unknown_context = set(current) - allowed_keys
        if unknown_context:
            raise CandidateBundleError(
                f"context: unregistered keys: {', '.join(sorted(unknown_context))}"
            )
        for key, value in current.items():
            _token(key, "context key")
            if key in _CONTEXT_TAG_KEYS:
                if key in _CONTEXT_ENUMS:
                    _enum(value, _CONTEXT_ENUMS[key], f"context.{key}")
                elif key in _CONTEXT_TOKEN_KEYS:
                    _token(value, f"context.{key}")
                    if key == "standard_id" and value not in self._known_standard_ids():
                        raise CandidateBundleError(
                            f"context.standard_id: {value!r} is not registered by this package's effective rules"
                        )
                else:
                    if _text(value, f"context.{key}") != value:
                        raise CandidateBundleError(f"context.{key}: text tag must not have surrounding whitespace")
            else:
                if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
                    raise CandidateBundleError(f"context.{key}: use a finite Decimal or integer")
                if isinstance(value, Decimal) and not value.is_finite():
                    raise CandidateBundleError(f"context.{key}: decimal value must be finite")
                if key == "carbonate_component_count":
                    numeric = Decimal(value)
                    if numeric < 0 or not _decimal_is_integral(numeric):
                        raise CandidateBundleError(
                            f"context.{key}: use a finite non-negative integer count"
                        )

        entries = self._field_entries()
        selected_ids = None if field_ids is None else {_token(item, "field_ids[]") for item in field_ids}
        if selected_ids is not None:
            if not selected_ids:
                raise CandidateBundleError("field_ids: when provided, at least one field is required")
            qualified_entries = {
                f"{package.rule_set_id}:{field['id']}": (package, field)
                for package, field in entries
            }
            bare_entries: dict[str, list[tuple[CandidatePackage, Mapping[str, Any]]]] = {}
            for package, field in entries:
                bare_entries.setdefault(field["id"], []).append((package, field))
            unknown_selected = {
                item for item in selected_ids if item not in qualified_entries and item not in bare_entries
            }
            if unknown_selected:
                raise CandidateBundleError(
                    f"field_ids: unknown fields: {', '.join(sorted(unknown_selected))}"
                )
            selected_keys: set[str] = set()
            for selected in selected_ids:
                if selected in qualified_entries:
                    package, field = qualified_entries[selected]
                    selected_keys.add(f"{package.rule_set_id}:{field['id']}")
                else:
                    matches = bare_entries[selected]
                    if len(matches) > 1:
                        raise CandidateBundleError(
                            f"field_ids: ambiguous unqualified field ID {selected!r}; use a package-qualified ID"
                        )
                    package, field = matches[0]
                    selected_keys.add(f"{package.rule_set_id}:{field['id']}")
            entries = [
                (package, field) for package, field in entries
                if f"{package.rule_set_id}:{field['id']}" in selected_keys
            ]

        outcomes: dict[str, Any] = {}
        problems: list[dict[str, Any]] = []
        overall = "READY"
        for package, field in entries:
            field_id = field["id"]
            entry_key = f"{package.rule_set_id}:{field_id}"
            local_problems: list[dict[str, Any]] = []
            state_map: dict[str, Any] = {}
            for property_name, source in (
                ("default", field["default"]),
                ("source_qualification", field["source_qualification"]),
            ):
                if source["state"] == "POLICY":
                    outcome = self._apply_policy(self._policy(package, source["policy_id"]), current)
                else:
                    state = source["state"]
                    status = (
                        "PENDING" if state == "PENDING"
                        else "NO_LEGAL_SOURCES" if state == "NO_LEGAL_SOURCES"
                        else "RESOLVED"
                    )
                    outcome = {
                        "status": status, "value": dict(source), "condition_id": None,
                        "policy_id": None, "message": source.get("reason"),
                    }
                state_map[property_name] = outcome
                if outcome["status"] != "RESOLVED":
                    local_problems.append({
                        "code": outcome["status"], "entry_key": entry_key, "field_id": field_id,
                        "rule_set_id": package.rule_set_id, "property": property_name,
                        "message": outcome["message"] or f"{property_name} is not eligible to execute",
                    })
            source_outcome = state_map["source_qualification"]
            resolved_source = source_outcome.get("value")
            if (
                "business_source" in current
                and source_outcome["status"] == "RESOLVED"
                and isinstance(resolved_source, Mapping)
                and resolved_source.get("state") == "FIXED"
                and current["business_source"] not in resolved_source["values"]
            ):
                allowed_sources = list(resolved_source["values"])
                local_problems.append({
                    "code": "SOURCE_NOT_ALLOWED", "entry_key": entry_key, "field_id": field_id,
                    "rule_set_id": package.rule_set_id, "property": "source_qualification",
                    "business_source": current["business_source"], "allowed_sources": allowed_sources,
                    "message": (
                        f"business_source {current['business_source']!r} is not allowed for this field; "
                        f"allowed sources are {allowed_sources!r}"
                    ),
                })
            locking_source = field["locking"]
            if locking_source.get("state") == "POLICY":
                locking_outcome = self._apply_policy(
                    self._policy(package, locking_source["policy_id"]), current,
                )
            else:
                locking_outcome = {
                    "status": "RESOLVED", "value": dict(locking_source), "condition_id": None,
                    "policy_id": None, "message": None,
                }
            locking = locking_outcome["value"] if locking_outcome["status"] == "RESOLVED" else None
            if locking_outcome["status"] != "RESOLVED":
                local_problems.append({
                    "code": locking_outcome["status"], "entry_key": entry_key, "field_id": field_id,
                    "rule_set_id": package.rule_set_id, "property": "locking",
                    "message": locking_outcome["message"] or "locking policy did not resolve uniquely",
                })
            elif locking is not None:
                for key in ("value", "source"):
                    lock_state = locking[key]["state"]
                    if lock_state in {"PENDING", "CONDITIONAL"}:
                        local_problems.append({
                            "code": "PENDING_LOCKING" if lock_state == "PENDING" else "CONDITIONAL_LOCKING",
                            "entry_key": entry_key, "field_id": field_id,
                            "rule_set_id": package.rule_set_id, "property": key,
                            "message": locking[key]["reason"],
                        })
            if local_problems:
                overall = "BLOCKED"
                problems.extend(local_problems)
            outcomes[entry_key] = {
                **state_map, "locking": dict(locking) if locking is not None else dict(locking_source),
                "locking_outcome": locking_outcome,
                "status": "BLOCKED" if local_problems else "READY",
                "problems": local_problems,
            }
        return {"status": overall, "outcomes": outcomes, "problems": problems}

    def _representative_context(self, when: Mapping[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = dict(when["tags"])
        for key, bounds in when["ranges"].items():
            if key == "carbonate_component_count":
                lower, _ = _count_integer_domain(bounds, f"representative_context.{key}")
                result[key] = lower
                continue
            low = _decimal_text(bounds["min"], f"range.{key}.min") if "min" in bounds else None
            high = _decimal_text(bounds["max"], f"range.{key}.max") if "max" in bounds else None
            if low is not None and high is not None:
                if low == high:
                    result[key] = low
                elif bounds["include_min"]:
                    result[key] = low
                elif bounds["include_max"]:
                    result[key] = high
                else:
                    result[key] = _exact_midpoint(low, high)
            elif low is not None:
                result[key] = low if bounds["include_min"] else _decimal_plus_integer(low, 1)
            elif high is not None:
                result[key] = high if bounds["include_max"] else _decimal_plus_integer(high, -1)
        return result

    @staticmethod
    def _intersect_conditions(
        whens: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, Any] | None, str | None]:
        tags: dict[str, str] = {}
        range_parts: dict[str, dict[str, list[tuple[Decimal, str, bool]]]] = {}
        for when in whens:
            for key, value in when["tags"].items():
                if key in tags and tags[key] != value:
                    return None, f"conflicting tag {key}: {tags[key]!r} versus {value!r}"
                tags[key] = value
            for key, bounds in when["ranges"].items():
                parts = range_parts.setdefault(key, {"min": [], "max": []})
                for bound in ("min", "max"):
                    if bound in bounds:
                        parts[bound].append((
                            _decimal_text(bounds[bound], f"intersection.{key}.{bound}"),
                            bounds[bound], bounds[f"include_{bound}"],
                        ))

        ranges: dict[str, Any] = {}
        for key, parts in range_parts.items():
            merged: dict[str, Any] = {}
            lower: Decimal | None = None
            upper: Decimal | None = None
            lower_included = True
            upper_included = True
            if parts["min"]:
                lower = max(item[0] for item in parts["min"])
                equal = [item for item in parts["min"] if item[0] == lower]
                lower_included = all(item[2] for item in equal)
                merged["min"] = equal[0][1]
                merged["include_min"] = lower_included
            if parts["max"]:
                upper = min(item[0] for item in parts["max"])
                equal = [item for item in parts["max"] if item[0] == upper]
                upper_included = all(item[2] for item in equal)
                merged["max"] = equal[0][1]
                merged["include_max"] = upper_included
            if lower is not None and upper is not None:
                if lower > upper:
                    return None, f"empty numeric range intersection for {key}"
                if lower == upper and not (lower_included and upper_included):
                    return None, f"empty numeric range intersection for {key}: boundary is excluded"
            if key == "carbonate_component_count":
                try:
                    _count_integer_domain(merged, f"intersection.{key}")
                except CandidateBundleError as exc:
                    return None, str(exc)
            ranges[key] = merged
        return {"tags": tags, "ranges": ranges}, None

    def review_rows(self) -> dict[str, Any]:
        """Return flat review rows with branch conditions and field-local outcomes."""
        field_rows: list[dict[str, Any]] = []
        operation_rows: list[dict[str, Any]] = []
        change_rows: list[dict[str, Any]] = []
        selected_entries = self._field_entries()
        selected_packages = self._selected_packages()
        adopted_common = {
            item["rule_set_id"]: set(item["rule_ids"])
            for item in self.primary.document["adopts"]
        }
        for package, field in selected_entries:
            policies_by_property: dict[str, Mapping[str, Any]] = {}
            for prop in ("default", "source_qualification", "locking"):
                source = field[prop]
                if source.get("state") == "POLICY":
                    policies_by_property[prop] = self._policy(package, source["policy_id"])
            property_order = list(policies_by_property)
            compatible_scenarios: list[tuple[dict[str, Mapping[str, Any]], dict[str, Any]]] = []
            participating: dict[str, set[str]] = {
                prop: set() for prop in property_order
            }

            def collect_compatible(
                index: int,
                chosen: dict[str, Mapping[str, Any]],
                combined_when: dict[str, Any],
            ) -> None:
                if index == len(property_order):
                    compatible_scenarios.append((dict(chosen), combined_when))
                    for chosen_prop, chosen_branch in chosen.items():
                        participating[chosen_prop].add(chosen_branch["id"])
                    return
                prop = property_order[index]
                policy = policies_by_property[prop]
                for branch in policy["branches"]:
                    merged_when, conflict = self._intersect_conditions(
                        [combined_when, branch["when"]],
                    )
                    if conflict is not None:
                        continue
                    chosen[prop] = branch
                    collect_compatible(index + 1, chosen, merged_when or {"tags": {}, "ranges": {}})
                    del chosen[prop]

            collect_compatible(0, {}, {"tags": {}, "ranges": {}})
            review_scenarios: list[
                tuple[dict[str, Mapping[str, Any]], dict[str, Any] | None, dict[str, Any] | None]
            ] = [
                (branches, merged_when, None)
                for branches, merged_when in compatible_scenarios
            ]
            for prop, policy in policies_by_property.items():
                for branch in policy["branches"]:
                    if branch["id"] in participating[prop]:
                        continue
                    review_scenarios.append(({}, None, {
                        "property": prop,
                        "policy_id": policy["id"],
                        "branch_id": branch["id"],
                        "when": branch["when"],
                        "value": branch["value"],
                        "reason": "This branch has no compatible conjunction with the other field policies.",
                    }))

            for branches_by_property, merged_when, uncomposable in review_scenarios:
                conditions_by_property = {
                    prop: branch["when"] for prop, branch in branches_by_property.items()
                }
                entry_key = f"{package.rule_set_id}:{field['id']}"
                branch_values = {
                    prop: branch["value"] for prop, branch in branches_by_property.items()
                }
                if uncomposable is not None:
                    conditions_by_property = {
                        uncomposable["property"]: uncomposable["when"],
                    }
                    branch_values = {uncomposable["property"]: uncomposable["value"]}
                    field_problems = [{
                        "code": "UNCOMPOSABLE_BRANCH", "entry_key": entry_key,
                        "field_id": field["id"], "rule_set_id": package.rule_set_id,
                        "property": uncomposable["property"],
                        "message": uncomposable["reason"],
                    }]
                    default_value = dict(field["default"])
                    source_value = dict(field["source_qualification"])
                    locking_value = dict(field["locking"])
                    locking_outcome = {
                        "status": "UNCOMPOSABLE_BRANCH", "value": None,
                        "condition_id": None, "policy_id": None,
                        "message": uncomposable["reason"],
                    }
                    evaluation_status = "UNCOMPOSABLE_BRANCH"
                else:
                    context = self._representative_context(merged_when or {"tags": {}, "ranges": {}})
                    applied = self.apply_context(context, field_ids=[entry_key])
                    outcome = applied["outcomes"][entry_key]
                    field_problems = outcome["problems"]
                    default_value = outcome["default"]["value"]
                    source_value = outcome["source_qualification"]["value"]
                    locking_value = outcome["locking"]
                    locking_outcome = outcome["locking_outcome"]
                    evaluation_status = outcome["status"]

                if uncomposable is not None:
                    review_property = "UNCOMPOSABLE"
                    policy_id = uncomposable["policy_id"]
                    condition_id = uncomposable["branch_id"]
                    review_key = (
                        f"field|{package.rule_set_id}|{package.revision}|{field['id']}|"
                        f"UNCOMPOSABLE|{policy_id}|{condition_id}"
                    )
                elif len(branches_by_property) == 0:
                    review_property, policy_id, condition_id = "BASE", None, None
                    review_key = (
                        f"field|{package.rule_set_id}|{package.revision}|{field['id']}|BASE|BASE|BASE"
                    )
                elif len(branches_by_property) == 1:
                    prop, branch = next(iter(branches_by_property.items()))
                    policy = policies_by_property[prop]
                    review_property, policy_id, condition_id = prop, policy["id"], branch["id"]
                    review_key = (
                        f"field|{package.rule_set_id}|{package.revision}|{field['id']}|"
                        f"{review_property}|{policy_id}|{condition_id}"
                    )
                else:
                    review_property, policy_id, condition_id = "COMBINED", None, None
                    branch_signature = ";".join(
                        f"{prop}={policies_by_property[prop]['id']}:{branches_by_property[prop]['id']}"
                        for prop in policies_by_property
                    )
                    review_key = (
                        f"field|{package.rule_set_id}|{package.revision}|{field['id']}|"
                        f"COMBINED|{branch_signature}"
                    )
                pending = list(field["pending"])
                pending.extend(f"{problem['code']}: {problem['message']}" for problem in field_problems)
                field_rows.append({
                    "key": review_key, "review_key": review_key, "revision": package.revision,
                    "rule_set_id": package.rule_set_id, "field_id": field["id"], "condition_id": condition_id,
                    "condition": (
                        uncomposable["when"] if uncomposable else
                        merged_when if merged_when is not None and policies_by_property else None
                    ),
                    "condition_status": "UNCOMPOSABLE_BRANCH" if uncomposable else "INTERSECTED",
                    "condition_conflict": uncomposable["reason"] if uncomposable else None,
                    "conditions_by_property": conditions_by_property,
                    "policy_id": policy_id,
                    "policy_ids": {prop: policy["id"] for prop, policy in policies_by_property.items()},
                    "condition_ids": (
                        {uncomposable["property"]: uncomposable["branch_id"]}
                        if uncomposable else
                        {prop: branch["id"] for prop, branch in branches_by_property.items()}
                    ),
                    "uncomposable_branch": uncomposable,
                    "policy_branch_values": branch_values,
                    "property": review_property,
                    "name": field["name"], "kind": field["kind"], "unit": field["unit"],
                    "source": source_value, "default": default_value,
                    "locking": locking_value, "locking_outcome": locking_outcome,
                    "channels": field["channel_projections"],
                    "basis": list(field["basis"]), "consumers": list(field["consumers"]),
                    "cases": list(field["cases"]), "pending": pending, "rule_ids": list(field["rule_ids"]),
                    "evaluation_status": evaluation_status, "evaluation_problems": field_problems,
                })
        for package in selected_packages:
            operations = package.document["operations"]
            if package.kind == "COMMON" and package.rule_set_id in adopted_common and package is not self.primary:
                allowed = adopted_common[package.rule_set_id]
                operations = [
                    operation for operation in operations
                    if operation["rule_ids"] and set(operation["rule_ids"]) <= allowed
                ]
            for operation in operations:
                row = dict(operation)
                row.update({
                    "review_key": f"operation|{package.rule_set_id}|{package.revision}|{operation['operation_id']}",
                    "revision": package.revision, "rule_set_id": package.rule_set_id,
                })
                operation_rows.append(row)
            for change in package.document["changes"]:
                row = dict(change)
                row.update({
                    "review_key": f"change|{package.rule_set_id}|{package.revision}|{change['key']}",
                    "revision": package.revision, "rule_set_id": package.rule_set_id,
                    "scope_note": "Package change log; common-package entries may include non-adopted rules.",
                })
                change_rows.append(row)
        return {
            "metadata": {
                "revision": self.primary.revision, "base": self.primary.document["base"],
                "dependency": list(self.primary.document["dependency"]),
                "status": self.primary.document["status"], "rule_set_id": self.primary.rule_set_id,
            },
            "fields": field_rows, "operations": operation_rows, "changes": change_rows,
        }

    def resolve_rules(self, context: RuleContext) -> EffectiveRuleSet:
        """Resolve adopted common and primary industry snapshots with the existing resolver."""
        if not isinstance(context, RuleContext):
            raise CandidateBundleError("context must be a core RuleContext")
        primary = self.primary
        common_rules: list[RuleDefinition] = []
        industry_rules: list[RuleDefinition] = []
        if primary.kind == "INDUSTRY":
            adopted_by_set = {item["rule_set_id"]: set(item["rule_ids"]) for item in primary.document["adopts"]}
            for package in self.packages:
                if package.kind != "COMMON" or package.rule_set_id not in adopted_by_set:
                    continue
                adopted_ids = adopted_by_set[package.rule_set_id]
                common_rules.extend(
                    rule for rule_id, rule in package.rules.items()
                    if rule_id in adopted_ids and package.rule_scopes[rule_id] != "NOT_APPLICABLE"
                )
            industry_rules.extend(
                rule for rule_id, rule in primary.rules.items()
                if primary.rule_scopes[rule_id] != "NOT_APPLICABLE"
            )
        elif primary.kind == "COMMON":
            common_rules.extend(
                rule for rule_id, rule in primary.rules.items()
                if primary.rule_scopes[rule_id] != "NOT_APPLICABLE"
            )
        else:
            raise CandidateBundleError("SOFTWARE packages do not define formal rule resolution")
        result = EffectiveRuleResolver().resolve(common_rules, industry_rules, context)
        pending_problems = tuple(
            ValidationProblem(
                "CANDIDATE-RULE-PENDING", IssueLevel.ERROR,
                f"Rule {rule.rule_id} has evidence status {rule.evidence_status.value}; candidate execution is blocked.",
                rule.rule_id,
            )
            for rule in result.rules if rule.evidence_status is not RuleEvidenceStatus.VERIFIED
        )
        return replace(result, problems=(*result.problems, *pending_problems))


def _parse_package(path: Path, raw: Mapping[str, Any]) -> CandidatePackage:
    doc = _keys(raw, _PACKAGE_FIELDS, str(path))
    if doc["schema_version"] != SCHEMA_VERSION:
        _fail(f"{path}.schema_version", f"must equal {SCHEMA_VERSION}")
    _token(doc["rule_set_id"], f"{path}.rule_set_id")
    kind = _enum(doc["kind"], _PACKAGE_KINDS, f"{path}.kind")
    revision = _token(doc["revision"], f"{path}.revision")
    if revision.lower() in {"latest", "*"} or "*" in revision:
        _fail(f"{path}.revision", "must identify a fixed revision, not latest or *")
    _text(doc["base"], f"{path}.base")
    _enum(doc["status"], {"CANDIDATE"}, f"{path}.status")
    for collection in ("dependency", "groups", "adopts", "rules", "policies", "fields", "operations", "changes"):
        if not isinstance(doc[collection], list):
            _fail(f"{path}.{collection}", "must be an array")
    dependencies: list[dict[str, str]] = []
    for index, value in enumerate(doc["dependency"]):
        entry_path = f"{path}.dependency[{index}]"
        entry = _keys(value, {"rule_set_id", "revision"}, entry_path)
        dep_id = _token(entry["rule_set_id"], f"{entry_path}.rule_set_id")
        dep_revision = _token(entry["revision"], f"{entry_path}.revision")
        if dep_revision.lower() in {"latest", "*"} or "*" in dep_revision:
            _fail(f"{entry_path}.revision", "must be fixed")
        dependencies.append({"rule_set_id": dep_id, "revision": dep_revision})
    if len({item["rule_set_id"] for item in dependencies}) != len(dependencies):
        _fail(f"{path}.dependency", "contains duplicate rule_set_id")
    if kind in {"COMMON", "SOFTWARE"} and doc["adopts"]:
        _fail(f"{path}.adopts", f"{kind} packages cannot declare adopts")
    if kind == "INDUSTRY" and not doc["adopts"]:
        _fail(f"{path}.adopts", "INDUSTRY packages must adopt fixed common rule sets")

    rules: dict[str, RuleDefinition] = {}
    rule_scopes: dict[str, str] = {}
    rule_reasons: dict[str, str | None] = {}
    for index, item in enumerate(doc["rules"]):
        rule_path = f"{path}.rules[{index}]"
        rule, scope, reason = _parse_rule(item, rule_path)
        if rule.rule_id in rules:
            _fail(f"{rule_path}.rule_id", "duplicate rule ID")
        rules[rule.rule_id] = rule
        rule_scopes[rule.rule_id] = scope
        rule_reasons[rule.rule_id] = reason
    groups: dict[str, tuple[str, ...]] = {}
    for index, item in enumerate(doc["groups"]):
        item_path = f"{path}.groups[{index}]"
        group = _keys(item, {"id", "rule_ids"}, item_path)
        group_id = _token(group["id"], f"{item_path}.id")
        ids = _string_array(group["rule_ids"], f"{item_path}.rule_ids", minimum=1, tokens=True)
        if group_id in groups:
            _fail(f"{item_path}.id", "duplicate group ID")
        if set(ids) - set(rules):
            _fail(f"{item_path}.rule_ids", "references unknown local rules")
        groups[group_id] = ids
    adopted_ids: set[str] = set()
    for index, item in enumerate(doc["adopts"]):
        item_path = f"{path}.adopts[{index}]"
        adopt = _keys(item, {"rule_set_id", "revision", "group_ids", "rule_ids"}, item_path)
        _token(adopt["rule_set_id"], f"{item_path}.rule_set_id")
        adopt_revision = _token(adopt["revision"], f"{item_path}.revision")
        if adopt_revision.lower() in {"latest", "*"} or "*" in adopt_revision:
            _fail(f"{item_path}.revision", "must be fixed")
        if adopt["rule_set_id"] in adopted_ids:
            _fail(f"{item_path}.rule_set_id", "duplicate adoption")
        adopted_ids.add(adopt["rule_set_id"])
        _string_array(adopt["group_ids"], f"{item_path}.group_ids", tokens=True)
        _string_array(adopt["rule_ids"], f"{item_path}.rule_ids", minimum=1, tokens=True)
    policies: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(doc["policies"]):
        policy = _validate_policy(item, f"{path}.policies[{index}]")
        if policy["id"] in policies:
            _fail(f"{path}.policies[{index}].id", "duplicate policy ID")
        policies[policy["id"]] = policy

    field_ids: set[str] = set()
    for index, item in enumerate(doc["fields"]):
        item_path = f"{path}.fields[{index}]"
        field = _keys(item, _FIELD_KEYS, item_path)
        field_id = _token(field["id"], f"{item_path}.id")
        if field_id in field_ids:
            _fail(f"{item_path}.id", "duplicate field ID")
        field_ids.add(field_id)
        _text(field["name"], f"{item_path}.name")
        field_kind = _enum(field["kind"], _FIELD_KINDS, f"{item_path}.kind")
        _text(field["unit"], f"{item_path}.unit")
        default = _validate_state(field["default"], f"{item_path}.default",
                                  allow_boolean=field_kind == "boolean",
                                  allow_empty_string=field_kind == "text")
        _validate_default_for_kind(default, f"{item_path}.default.value", field_kind)
        _validate_state(field["source_qualification"], f"{item_path}.source_qualification", source=True)
        locking = _validate_locking(field["locking"], f"{item_path}.locking")
        if not isinstance(field["channel_projections"], list) or not field["channel_projections"]:
            _fail(f"{item_path}.channel_projections", "must be a non-empty array")
        projections: set[tuple[str, str]] = set()
        for projection_index, raw_projection in enumerate(field["channel_projections"]):
            projection_path = f"{item_path}.channel_projections[{projection_index}]"
            projection = _keys(raw_projection, {"channel", "label", "unit", "binding", "notes"}, projection_path)
            channel = _token(projection["channel"], f"{projection_path}.channel")
            _text(projection["label"], f"{projection_path}.label")
            _text(projection["unit"], f"{projection_path}.unit")
            binding = _token(projection["binding"], f"{projection_path}.binding")
            _text(projection["notes"], f"{projection_path}.notes")
            if (channel, binding) in projections:
                _fail(projection_path, "duplicate channel/binding projection")
            projections.add((channel, binding))
        for name in ("basis", "consumers", "cases"):
            _string_array(field[name], f"{item_path}.{name}", minimum=1)
        _string_array(field["pending"], f"{item_path}.pending")
        _string_array(field["rule_ids"], f"{item_path}.rule_ids", tokens=True)
        for state_name in ("default", "source_qualification"):
            value_state = field[state_name]
            if value_state["state"] == "POLICY":
                policy = policies.get(value_state["policy_id"])
                if policy is None:
                    _fail(f"{item_path}.{state_name}.policy_id", "references unknown local policy")
                expected_property = "default" if state_name == "default" else "source_qualification"
                if policy["property"] != expected_property:
                    _fail(f"{item_path}.{state_name}.policy_id", "policy property does not match field state")
                if state_name == "default":
                    for branch in policy["branches"]:
                        branch_value = branch["value"]
                        if branch_value["state"] == "FIXED":
                            _validate_default_for_kind(
                                branch_value,
                                f"{item_path}.{state_name}.policy:{policy['id']}:{branch['id']}.value",
                                field_kind,
                            )
        if locking.get("state") == "POLICY":
            policy = policies.get(locking["policy_id"])
            if policy is None:
                _fail(f"{item_path}.locking.policy_id", "references unknown local policy")
            if policy["property"] != "locking":
                _fail(f"{item_path}.locking.policy_id", "policy property does not match field locking")
    operation_ids: set[str] = set()
    operation_keys: set[str] = set()
    for index, item in enumerate(doc["operations"]):
        item_path = f"{path}.operations[{index}]"
        operation = _keys(item, _OPERATION_KEYS, item_path)
        op_id = _token(operation["operation_id"], f"{item_path}.operation_id")
        key = _token(operation["key"], f"{item_path}.key")
        if op_id in operation_ids or key in operation_keys:
            _fail(item_path, "duplicate operation_id or review key")
        operation_ids.add(op_id)
        operation_keys.add(key)
        _text(operation["name"], f"{item_path}.name")
        _string_map(operation["initial_context"], f"{item_path}.initial_context")
        _text(operation["action"], f"{item_path}.action")
        for name in ("changes", "preserves", "invalidates", "confirmation", "pending"):
            _string_array(operation[name], f"{item_path}.{name}")
        _string_array(operation["basis"], f"{item_path}.basis", minimum=1)
        _string_array(operation["cases"], f"{item_path}.cases", minimum=1)
        _string_array(operation["rule_ids"], f"{item_path}.rule_ids", tokens=True)
    change_keys: set[str] = set()
    for index, item in enumerate(doc["changes"]):
        item_path = f"{path}.changes[{index}]"
        change = _keys(item, _CHANGE_KEYS, item_path)
        key = _token(change["key"], f"{item_path}.key")
        if key in change_keys:
            _fail(f"{item_path}.key", "duplicate review key")
        change_keys.add(key)
        _token(change["change_type"], f"{item_path}.change_type")
        _text(change["before"], f"{item_path}.before")
        _text(change["after"], f"{item_path}.after")
        _text(change["reason"], f"{item_path}.reason")
        _string_array(change["basis"], f"{item_path}.basis", minimum=1)
        _string_array(change["pending"], f"{item_path}.pending")

    return CandidatePackage(path, doc, rules, rule_scopes, rule_reasons, policies)


def _validate_package_set(packages: Sequence[CandidatePackage], primary_rule_set_id: str | None = None) -> CandidateBundle:
    if not packages:
        _fail("bundle", "at least one package path is required")
    by_id: dict[str, CandidatePackage] = {}
    global_rule_ids: dict[str, CandidatePackage] = {}
    for package in packages:
        if package.rule_set_id in by_id:
            _fail(str(package.path), f"duplicate rule_set_id {package.rule_set_id!r}")
        by_id[package.rule_set_id] = package
        for rule_id in package.rules:
            if rule_id in global_rule_ids:
                _fail(str(package.path), f"rule_id {rule_id!r} is duplicated across packages")
            global_rule_ids[rule_id] = package

    graph: dict[str, set[str]] = {package.rule_set_id: set() for package in packages}
    for package in packages:
        doc = package.document
        dependencies = {item["rule_set_id"]: item["revision"] for item in doc["dependency"]}
        for dep_id, revision in dependencies.items():
            target = by_id.get(dep_id)
            if target is None:
                _fail(str(package.path), f"dependency {dep_id!r} is not present in load_bundle(paths)")
            if target.revision != revision:
                _fail(str(package.path), f"dependency {dep_id!r} revision mismatch")
            graph[package.rule_set_id].add(dep_id)
        adopted_rules: set[str] = set()
        for index, adopt in enumerate(doc["adopts"]):
            adopt_path = f"{package.path}.adopts[{index}]"
            target_id = adopt["rule_set_id"]
            target = by_id.get(target_id)
            if target is None:
                _fail(adopt_path, f"adopted rule set {target_id!r} is not present in load_bundle(paths)")
            if target.kind != "COMMON":
                _fail(adopt_path, "INDUSTRY may adopt only COMMON packages")
            if target.revision != adopt["revision"]:
                _fail(adopt_path, "adopted revision does not match the loaded fixed revision")
            if dependencies.get(target_id) != target.revision:
                _fail(adopt_path, "adopted package must also appear in dependency with the same revision")
            group_map = {item["id"]: set(item["rule_ids"]) for item in target.document["groups"]}
            group_ids = set(adopt["group_ids"])
            if group_ids - set(group_map):
                _fail(adopt_path, f"unknown groups: {', '.join(sorted(group_ids - set(group_map)))}")
            declared = set(adopt["rule_ids"])
            if declared - set(target.rules):
                _fail(adopt_path, f"unknown adopted rules: {', '.join(sorted(declared - set(target.rules)))}")
            group_members = set().union(*(group_map[group_id] for group_id in group_ids)) if group_ids else set()
            if not group_members <= declared:
                _fail(adopt_path, "adopt.rule_ids must include every member of each adopted fixed group")
            adopted_rules.update(declared)
            graph[package.rule_set_id].add(target_id)
        if package.kind == "INDUSTRY" and not adopted_rules:
            _fail(str(package.path), "industry package must explicitly adopt at least one common rule")
        effective_rule_ids = set().union(*_effective_rule_ids_for(package, by_id).values())
        for rule_id, rule in package.rules.items():
            for target_rule_id in rule.supersedes_rule_ids:
                if target_rule_id not in global_rule_ids:
                    _fail(str(package.path), f"rule {rule_id!r} supersedes missing rule {target_rule_id!r}")
                if target_rule_id not in effective_rule_ids:
                    _fail(
                        str(package.path),
                        f"rule {rule_id!r} supersedes rule {target_rule_id!r} outside this package's effective rule scope",
                    )
        for collection_name in ("fields", "operations"):
            for item in doc[collection_name]:
                for rule_id in item["rule_ids"]:
                    if rule_id not in global_rule_ids:
                        _fail(str(package.path), f"{collection_name} references missing rule {rule_id!r}")
                    if rule_id not in effective_rule_ids:
                        _fail(
                            str(package.path),
                            f"{collection_name} references rule {rule_id!r} outside this package's effective rule scope",
                        )
        if package.kind == "INDUSTRY":
            common_references = {
                rule_id for collection in ("fields", "operations") for item in doc[collection]
                for rule_id in item["rule_ids"] if global_rule_ids[rule_id].kind == "COMMON"
            }
            if common_references - adopted_rules:
                _fail(str(package.path), "field/operation references common rules not explicitly adopted")

    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            _fail("dependency", f"dependency cycle includes {node!r}")
        if node in visited:
            return
        visiting.add(node)
        for target in graph[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)

    for package in packages:
        known_standard_ids = _known_standard_ids_for(package, by_id)
        for policy in package.policies.values():
            for branch in policy["branches"]:
                standard_id = branch["when"]["tags"].get("standard_id")
                if standard_id is not None and standard_id not in known_standard_ids:
                    _fail(
                        f"{package.path}.policies.{policy['id']}.branches.{branch['id']}.when.tags.standard_id",
                        f"standard identity {standard_id!r} is not registered by this package's effective rules",
                    )

    if primary_rule_set_id is not None:
        primary = by_id.get(primary_rule_set_id)
        if primary is None:
            _fail("primary_rule_set_id", f"unknown package {primary_rule_set_id!r}")
    else:
        industries = [package for package in packages if package.kind == "INDUSTRY"]
        primary = industries[0] if industries else packages[0]
        if len(industries) > 1:
            _fail("primary_rule_set_id", "select one primary industry package when more than one is loaded")
    return CandidateBundle(tuple(packages), primary.rule_set_id)


def load_bundle(paths: Iterable[str | Path], *, primary_rule_set_id: str | None = None) -> CandidateBundle:
    """Load all packages in a closed bundle; no network/latest lookup is performed."""
    parsed = [_parse_package(Path(path), _read_json(Path(path))) for path in paths]
    return _validate_package_set(parsed, primary_rule_set_id)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > (2**53 - 1):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and inspect a review-only business-rule candidate bundle.")
    parser.add_argument("--review-json", type=Path, help="write stable review rows as JSON")
    parser.add_argument("--primary-rule-set-id", help="select a primary package when multiple are loaded")
    parser.add_argument("paths", nargs="+", type=Path, help="fixed JSON package files in the closed bundle")
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.paths, primary_rule_set_id=args.primary_rule_set_id)
        if args.review_json:
            args.review_json.parent.mkdir(parents=True, exist_ok=True)
            args.review_json.write_text(
                json.dumps(_json_safe(bundle.review_rows()), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            review = bundle.review_rows()
            print(json.dumps({
                "status": "VALID", "primary_rule_set_id": bundle.primary.rule_set_id,
                "fields": len(review["fields"]), "operations": len(review["operations"]),
                "changes": len(review["changes"]),
            }, ensure_ascii=False))
        return 0
    except (CandidateBundleError, OSError, ValueError) as exc:
        print(f"candidate validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
