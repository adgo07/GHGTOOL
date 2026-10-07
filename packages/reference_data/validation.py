"""Validation and loading for the canonical reference-data source."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from packages.core.decimal_policy import DecimalPolicy, DecimalPolicyError
from packages.core.models import OfficialStatus, ParameterType, ReviewStatus, SourceType, ValueType
from packages.core.units import UnitError, UnitService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "specs" / "common" / "canonical_catalog.schema.json"
DEFAULT_SOURCE_PATH = PROJECT_ROOT / "data-source" / "carbon_accounting" / "catalog.json"


G01_CANONICAL_ENUM_VALUES = {
    "official_status": frozenset(item.value for item in OfficialStatus),
    "source_type": frozenset(item.value for item in SourceType),
    "review_status": frozenset(item.value for item in ReviewStatus),
    "parameter_type": frozenset(item.value for item in ParameterType),
    "value_type": frozenset(item.value for item in ValueType),
}


class CanonicalValidationError(ValueError):
    """Raised when canonical data cannot be safely consumed."""

    def __init__(self, errors: list[str] | tuple[str, ...] | str) -> None:
        if isinstance(errors, str):
            normalized = (errors,)
        else:
            normalized = tuple(errors)
        self.errors = normalized
        super().__init__("canonical catalog validation failed: " + "; ".join(normalized))


class _JsonSchemaValidator:
    """Small dependency-free subset of JSON Schema used by the frozen schema."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def validate(self, value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
        expected = schema.get("type")
        if expected is not None and not self._matches_type(value, expected):
            self.errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
            return

        if "enum" in schema and value not in schema["enum"]:
            self.errors.append(f"{path}: value is not in enum")

        if isinstance(value, str):
            minimum = schema.get("minLength")
            if minimum is not None and len(value) < minimum:
                self.errors.append(f"{path}: string is shorter than {minimum}")
            pattern = schema.get("pattern")
            if pattern is not None and re.search(pattern, value) is None:
                self.errors.append(f"{path}: string does not match required pattern")
            self._validate_format(value, schema.get("format"), path)

        if isinstance(value, int) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                self.errors.append(f"{path}: integer is below minimum")
            if "maximum" in schema and value > schema["maximum"]:
                self.errors.append(f"{path}: integer is above maximum")

        if isinstance(value, dict):
            required = schema.get("required", ())
            for key in required:
                if key not in value:
                    self.errors.append(f"{path}: missing required property {key!r}")
            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                for key in value:
                    if key not in properties:
                        self.errors.append(f"{path}: unknown property {key!r}")
            for key, child in value.items():
                if key in properties:
                    self.validate(child, properties[key], f"{path}.{key}")

        if isinstance(value, list):
            if schema.get("uniqueItems") and len({self._stable(item) for item in value}) != len(value):
                self.errors.append(f"{path}: array items must be unique")
            item_schema = schema.get("items")
            if item_schema is not None:
                for index, item in enumerate(value):
                    self.validate(item, item_schema, f"{path}[{index}]")

    @staticmethod
    def _matches_type(value: Any, expected: str | list[str]) -> bool:
        expected_types = [expected] if isinstance(expected, str) else expected
        for type_name in expected_types:
            if type_name == "object" and isinstance(value, dict):
                return True
            if type_name == "array" and isinstance(value, list):
                return True
            if type_name == "string" and isinstance(value, str):
                return True
            if type_name == "integer" and isinstance(value, int) and not isinstance(value, bool):
                return True
            if type_name == "boolean" and isinstance(value, bool):
                return True
            if type_name == "null" and value is None:
                return True
        return False

    def _validate_format(self, value: str, format_name: str | None, path: str) -> None:
        if format_name == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                self.errors.append(f"{path}: invalid ISO date")
        elif format_name == "uri":
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                self.errors.append(f"{path}: URI must be an absolute HTTP(S) URL")

    @staticmethod
    def _stable(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


_COMPOUND_UNITS = frozenset(
    {
        "kgCO2/kWh",
        "tCO2/MWh",
        "tCO2/GJ",
        "tC/GJ",
        "tC/10^4Nm3",
        "GJ/10^4Nm3",
        "GJ/t",
        "tC/t",
        "tCO2/10^4Nm3",
        "tCO2/t",
    }
)


def _normalize_compound_unit(unit: str) -> str:
    return (
        unit.strip()
        .replace("₂", "2")
        .replace("³", "3")
        .replace("⁴", "^4")
        .replace(" ", "")
    )


def _known_unit(unit: str, units: UnitService) -> bool:
    try:
        units.resolve(unit)
        return True
    except UnitError:
        return _normalize_compound_unit(unit) in _COMPOUND_UNITS


def _compound_conversion(value: Decimal, from_unit: str, to_unit: str) -> Decimal | None:
    source = _normalize_compound_unit(from_unit)
    target = _normalize_compound_unit(to_unit)
    if source not in _COMPOUND_UNITS or target not in _COMPOUND_UNITS:
        return None
    if source == target:
        return value
    if {source, target} == {"kgCO2/kWh", "tCO2/MWh"}:
        return value
    return None


def _reject_floats(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, float):
        errors.append(f"{path}: binary floating-point values are not accepted")
    elif isinstance(value, dict):
        for key, child in value.items():
            _reject_floats(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_floats(child, f"{path}[{index}]", errors)


def _unique_ids(
    rows: list[dict[str, Any]],
    field: str,
    collection: str,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row_number, row in enumerate(rows):
        stable_id = row.get(field)
        if not isinstance(stable_id, str):
            continue
        if stable_id in index:
            errors.append(f"$.{collection}[{row_number}].{field}: duplicate stable ID {stable_id!r}")
        else:
            index[stable_id] = row
    return index


def _parse_decimal(value: Any, path: str, policy: DecimalPolicy, errors: list[str]) -> Decimal | None:
    try:
        return policy.parse(value)
    except DecimalPolicyError as exc:
        errors.append(f"{path}: {exc}")
        return None


def _validate_g01_enum(value: Any, field: str, path: str, errors: list[str]) -> None:
    if value not in G01_CANONICAL_ENUM_VALUES[field]:
        errors.append(f"{path}: value {value!r} is not a G01 {field} value")


def _cross_validate(catalog: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = DecimalPolicy()
    units = UnitService(policy)
    _reject_floats(catalog, "$", errors)

    sources = _unique_ids(list(catalog.get("sources", [])), "source_id", "sources", errors)
    subjects = _unique_ids(list(catalog.get("subjects", [])), "subject_id", "subjects", errors)
    standards = _unique_ids(list(catalog.get("standards", [])), "standard_id", "standards", errors)
    parameters = _unique_ids(list(catalog.get("parameters", [])), "parameter_id", "parameters", errors)
    factors = _unique_ids(list(catalog.get("factors", [])), "factor_id", "factors", errors)
    source_tables = _unique_ids(list(catalog.get("source_tables", [])), "source_table_id", "source_tables", errors)
    assets = _unique_ids(list(catalog.get("reference_data_assets", [])), "asset_id", "reference_data_assets", errors)
    bindings = _unique_ids(list(catalog.get("reference_data_bindings", [])), "binding_id", "reference_data_bindings", errors)
    conversions = _unique_ids(
        list(catalog.get("conversion_rules", [])), "conversion_id", "conversion_rules", errors
    )
    del conversions

    for row_number, source in enumerate(catalog.get("sources", [])):
        _validate_g01_enum(
            source.get("source_type"),
            "source_type",
            f"$.sources[{row_number}].source_type",
            errors,
        )
        _validate_g01_enum(
            source.get("review_status"),
            "review_status",
            f"$.sources[{row_number}].review_status",
            errors,
        )
        if source.get("source_type") in {"OFFICIAL_STANDARD", "GOVERNMENT_PUBLICATION", "SCIENTIFIC_REFERENCE"}:
            url = source.get("official_url")
            if not isinstance(url, str) or not url.startswith("https://"):
                errors.append(f"$.sources[{row_number}].official_url: official HTTPS URL is required")

    for row_number, standard in enumerate(catalog.get("standards", [])):
        _validate_g01_enum(
            standard.get("official_status"),
            "official_status",
            f"$.standards[{row_number}].official_status",
            errors,
        )
        source_id = standard.get("official_source_id")
        source = sources.get(source_id)
        if source is None:
            errors.append(f"$.standards[{row_number}].official_source_id: unknown source {source_id!r}")
        elif standard.get("official_source_url") != source.get("official_url"):
            errors.append(f"$.standards[{row_number}].official_source_url: does not match source URL")
        for reference in standard.get("base_standard_ids", []):
            if reference not in standards:
                errors.append(f"$.standards[{row_number}].base_standard_ids: unknown standard {reference!r}")
        if standard.get("calculation_status") == "PLANNED":
            if standard.get("standard_id") == "gbt_32151_34_2024":
                if standard.get("emission_source_refs"):
                    errors.append(
                        f"$.standards[{row_number}]: planned industry standard cannot carry emission-source references"
                    )
            elif standard.get("parameter_refs") or standard.get("emission_source_refs"):
                errors.append(f"$.standards[{row_number}]: planned standard cannot carry calculation references")
        for reference in standard.get("parameter_refs", []):
            parameter = parameters.get(reference)
            if parameter is None:
                errors.append(f"$.standards[{row_number}].parameter_refs: unknown parameter {reference!r}")
            elif standard.get("standard_id") not in parameter.get("applicable_standard_ids", []):
                errors.append(
                    f"$.standards[{row_number}].parameter_refs: parameter {reference!r} is not applicable"
                )

    for row_number, parameter in enumerate(catalog.get("parameters", [])):
        _validate_g01_enum(
            parameter.get("parameter_type"),
            "parameter_type",
            f"$.parameters[{row_number}].parameter_type",
            errors,
        )
        _validate_g01_enum(
            parameter.get("review_status"),
            "review_status",
            f"$.parameters[{row_number}].review_status",
            errors,
        )
        if parameter.get("subject_id") not in subjects:
            errors.append(f"$.parameters[{row_number}].subject_id: unknown subject")
        if parameter.get("source_id") not in sources:
            errors.append(f"$.parameters[{row_number}].source_id: unknown source")
        if not _known_unit(parameter.get("canonical_unit", ""), units):
            errors.append(f"$.parameters[{row_number}].canonical_unit: unknown unit")
        for standard_id in parameter.get("applicable_standard_ids", []):
            if standard_id not in standards:
                errors.append(f"$.parameters[{row_number}].applicable_standard_ids: unknown standard")

    for row_number, factor in enumerate(catalog.get("factors", [])):
        _validate_g01_enum(
            factor.get("value_type"),
            "value_type",
            f"$.factors[{row_number}].value_type",
            errors,
        )
        _validate_g01_enum(
            factor.get("review_status"),
            "review_status",
            f"$.factors[{row_number}].review_status",
            errors,
        )
        parameter = parameters.get(factor.get("parameter_id"))
        if parameter is None:
            errors.append(f"$.factors[{row_number}].parameter_id: unknown parameter")
        if factor.get("subject_id") not in subjects:
            errors.append(f"$.factors[{row_number}].subject_id: unknown subject")
        if parameter is not None and factor.get("subject_id") != parameter.get("subject_id"):
            errors.append(f"$.factors[{row_number}].subject_id: does not match parameter subject")
        if factor.get("source_id") not in sources:
            errors.append(f"$.factors[{row_number}].source_id: unknown source")
        for unit_field in ("unit", "source_unit", "normalized_unit"):
            if not _known_unit(factor.get(unit_field, ""), units):
                errors.append(f"$.factors[{row_number}].{unit_field}: unknown unit")
        source_value = _parse_decimal(
            factor.get("source_value"), f"$.factors[{row_number}].source_value", policy, errors
        )
        normalized_value = _parse_decimal(
            factor.get("normalized_value"), f"$.factors[{row_number}].normalized_value", policy, errors
        )
        value = _parse_decimal(factor.get("value"), f"$.factors[{row_number}].value", policy, errors)
        if value is not None and normalized_value is not None and value != normalized_value:
            errors.append(f"$.factors[{row_number}].value: must equal normalized_value")
        if factor.get("unit") != factor.get("normalized_unit"):
            errors.append(f"$.factors[{row_number}].unit: must equal normalized_unit")
        if source_value is not None and normalized_value is not None:
            converted = _compound_conversion(
                source_value, factor.get("source_unit", ""), factor.get("normalized_unit", "")
            )
            if converted is None:
                try:
                    converted = units.convert(
                        source_value, factor.get("source_unit", ""), factor.get("normalized_unit", "")
                    )
                except UnitError as exc:
                    errors.append(f"$.factors[{row_number}]: unit normalization failed: {exc}")
                    converted = None
            if converted is not None and converted != normalized_value:
                errors.append(f"$.factors[{row_number}]: normalized_value does not match unit conversion")
        for standard_id in factor.get("applicable_standard_ids", []):
            if standard_id not in standards:
                errors.append(f"$.factors[{row_number}].applicable_standard_ids: unknown standard")

    for row_number, table in enumerate(catalog.get("source_tables", [])):
        path = f"$.source_tables[{row_number}]"
        if table.get("source_id") not in sources:
            errors.append(f"{path}.source_id: unknown source")
        layout = table.get("layout")
        provider_id = table.get("provider_id")
        if layout == "provider" and not provider_id:
            errors.append(f"{path}.provider_id: provider layout requires a registered provider")
        if layout != "provider" and provider_id is not None:
            errors.append(f"{path}.provider_id: only provider tables may name a provider")
        for column_number, column in enumerate(table.get("columns", [])):
            parameter_type = column.get("parameter_type")
            if parameter_type is not None:
                _validate_g01_enum(
                    parameter_type,
                    "parameter_type",
                    f"{path}.columns[{column_number}].parameter_type",
                    errors,
                )

    for row_number, asset in enumerate(catalog.get("reference_data_assets", [])):
        path = f"$.reference_data_assets[{row_number}]"
        parameter = parameters.get(asset.get("parameter_id"))
        if parameter is None:
            errors.append(f"{path}.parameter_id: unknown parameter")
        if asset.get("subject_id") not in subjects:
            errors.append(f"{path}.subject_id: unknown subject")
        if parameter is not None and asset.get("subject_id") != parameter.get("subject_id"):
            errors.append(f"{path}.subject_id: does not match parameter subject")
        _validate_g01_enum(asset.get("value_type"), "value_type", f"{path}.value_type", errors)
        for unit_field in ("unit", "source_unit", "normalized_unit"):
            if not _known_unit(asset.get(unit_field, ""), units):
                errors.append(f"{path}.{unit_field}: unknown unit")
        source_value = _parse_decimal(asset.get("source_value"), f"{path}.source_value", policy, errors)
        normalized_value = _parse_decimal(asset.get("normalized_value"), f"{path}.normalized_value", policy, errors)
        value = _parse_decimal(asset.get("value"), f"{path}.value", policy, errors)
        if value is not None and normalized_value is not None and value != normalized_value:
            errors.append(f"{path}.value: must equal normalized_value")
        if asset.get("unit") != asset.get("normalized_unit"):
            errors.append(f"{path}.unit: must equal normalized_unit")
        if source_value is not None and normalized_value is not None:
            converted = _compound_conversion(source_value, asset.get("source_unit", ""), asset.get("normalized_unit", ""))
            if converted is None:
                try:
                    converted = units.convert(source_value, asset.get("source_unit", ""), asset.get("normalized_unit", ""))
                except UnitError as exc:
                    errors.append(f"{path}: unit normalization failed: {exc}")
                    converted = None
            if converted is not None and converted != normalized_value:
                errors.append(f"{path}: normalized_value does not match unit conversion")

    binding_count_by_factor: dict[str, int] = {}
    used_asset_ids: set[str] = set()
    for row_number, binding in enumerate(catalog.get("reference_data_bindings", [])):
        path = f"$.reference_data_bindings[{row_number}]"
        asset = assets.get(binding.get("asset_id"))
        table = source_tables.get(binding.get("source_table_id"))
        if asset is None:
            errors.append(f"{path}.asset_id: unknown reference data asset")
        else:
            used_asset_ids.add(asset["asset_id"])
        if table is None:
            errors.append(f"{path}.source_table_id: unknown source table")
        for standard_id in binding.get("applicable_standard_ids", []):
            if standard_id not in standards:
                errors.append(f"{path}.applicable_standard_ids: unknown standard")
        _validate_g01_enum(binding.get("review_status"), "review_status", f"{path}.review_status", errors)
        valid_from = binding.get("valid_from")
        valid_to = binding.get("valid_to")
        try:
            start = date.fromisoformat(valid_from) if valid_from else None
            end = date.fromisoformat(valid_to) if valid_to else None
            if start is not None and end is not None and start > end:
                errors.append(f"{path}: applicability dates are out of order")
        except (TypeError, ValueError):
            # JSON Schema reports malformed date text; avoid secondary validator failures.
            pass
        factor_id = binding.get("factor_id")
        if binding.get("binding_type") == "STANDARD_REFERENCE":
            if factor_id is not None:
                errors.append(f"{path}.factor_id: standard reference bindings do not create resolver candidates")
            continue
        factor = factors.get(factor_id)
        if factor is None:
            errors.append(f"{path}.factor_id: factor-source binding must reference a known factor")
            continue
        binding_count_by_factor[factor_id] = binding_count_by_factor.get(factor_id, 0) + 1
        if table is not None and table.get("source_id") != factor.get("source_id"):
            errors.append(f"{path}.source_table_id: factor-source table must match the factor source")
        if binding.get("source_location") != factor.get("source_location"):
            errors.append(f"{path}.source_location: must preserve the factor's precise locator")
        if binding.get("applicable_standard_ids") != factor.get("applicable_standard_ids"):
            errors.append(f"{path}.applicable_standard_ids: must preserve factor applicability")
        if binding.get("factor_year") != factor.get("factor_year"):
            errors.append(f"{path}.factor_year: must preserve factor year")
        if binding.get("valid_from") != factor.get("valid_from") or binding.get("valid_to") != factor.get("valid_to"):
            errors.append(f"{path}: must preserve factor applicability dates")
        if binding.get("review_status") != factor.get("review_status"):
            errors.append(f"{path}.review_status: must preserve factor review status")
        if asset is not None:
            for field in ("parameter_id", "subject_id", "value", "unit", "source_value", "source_unit", "normalized_value", "normalized_unit", "value_type"):
                if asset.get(field) != factor.get(field):
                    errors.append(f"{path}.asset_id: asset content does not match factor field {field!r}")

    for factor_id in factors:
        if binding_count_by_factor.get(factor_id) != 1:
            errors.append(f"$.factors: factor {factor_id!r} must have exactly one source binding")
    for asset_id in assets:
        if asset_id not in used_asset_ids:
            errors.append(f"$.reference_data_assets: asset {asset_id!r} has no source binding")

    for row_number, rule in enumerate(catalog.get("conversion_rules", [])):
        _validate_g01_enum(
            rule.get("review_status"),
            "review_status",
            f"$.conversion_rules[{row_number}].review_status",
            errors,
        )
        from_unit = rule.get("from_unit", "")
        to_unit = rule.get("to_unit", "")
        if not _known_unit(from_unit, units):
            errors.append(f"$.conversion_rules[{row_number}].from_unit: unknown unit")
        if not _known_unit(to_unit, units):
            errors.append(f"$.conversion_rules[{row_number}].to_unit: unknown unit")
        multiplier = _parse_decimal(
            rule.get("multiplier"), f"$.conversion_rules[{row_number}].multiplier", policy, errors
        )
        offset = _parse_decimal(rule.get("offset"), f"$.conversion_rules[{row_number}].offset", policy, errors)
        if multiplier is None or offset is None:
            continue
        if offset != 0:
            errors.append(f"$.conversion_rules[{row_number}].offset: only zero offset is allowed")
        try:
            expected = units.conversion_factor(from_unit, to_unit)
        except UnitError:
            expected = None
        if expected is not None and multiplier != expected:
            errors.append(f"$.conversion_rules[{row_number}]: multiplier does not match UnitService")
        elif expected is None:
            compound = _compound_conversion(Decimal("1"), from_unit, to_unit)
            if compound is None or multiplier != compound:
                errors.append(f"$.conversion_rules[{row_number}]: unsupported conversion bridge")
        if rule.get("source_id") not in sources:
            errors.append(f"$.conversion_rules[{row_number}].source_id: unknown source")

    return errors


def validate_catalog(
    catalog: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a decoded canonical catalog and return it unchanged."""

    if not isinstance(catalog, dict):
        raise CanonicalValidationError("$: top-level value must be an object")
    if schema is None:
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_validator = _JsonSchemaValidator()
    schema_validator.validate(catalog, schema)
    if schema_validator.errors:
        raise CanonicalValidationError(schema_validator.errors)
    errors = _cross_validate(catalog)
    if errors:
        raise CanonicalValidationError(errors)
    return catalog


def load_validated_catalog(
    source_path: str | Path = DEFAULT_SOURCE_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Load only the JSON canonical format and validate it before use."""

    source = Path(source_path)
    if source.suffix.lower() in {".yaml", ".yml"}:
        raise CanonicalValidationError("G02 uses JSON as the canonical format; YAML requires an approved loader")
    try:
        catalog = json.loads(source.read_text(encoding="utf-8"))
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalValidationError(str(exc)) from exc
    return validate_catalog(catalog, schema)
