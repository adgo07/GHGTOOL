"""Adopted fuel/power field expression adapter; values still come from Resolver.

The resource is a mechanically checked projection, never another editable source.
This low-level evaluator does not verify caller-supplied Catalog identities.
Production callers must use the Resolver-produced context, not synthesize VERIFIED.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any, Mapping

from packages.core.business_field_policy import evaluate_field

RUNTIME_RESOURCE = "business_rules/fuel_power.json"
RUNTIME_SHA256 = "691b6a20fff83e54194e9591a15bdc6a1ced3d6af5e3c1d9d5db49e4fbebcf79"
ADOPTION_ID = "GHGTOOL_FUEL_POWER_R11_V1"


class BusinessPolicyConfigurationError(ValueError):
    """The approved runtime expression is missing or inconsistent; no fallback."""


def _decode_resource(content: bytes) -> dict[str, Any]:
    if sha256(content).hexdigest() != RUNTIME_SHA256:
        raise BusinessPolicyConfigurationError("燃料与电力业务规则资源校验失败，请重新安装完整软件。")
    document = json.loads(content)
    if document["format_version"] != 1 or document["adoption_id"] != ADOPTION_ID:
        raise BusinessPolicyConfigurationError("燃料与电力业务规则版本不兼容。")
    return document


@lru_cache(maxsize=1)
def _document() -> dict[str, Any]:
    try:
        return _decode_resource(files("resources").joinpath(RUNTIME_RESOURCE).read_bytes())
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BusinessPolicyConfigurationError("燃料与电力业务规则资源缺失或损坏。") from exc


def fuel_power_policy_identity() -> dict[str, Any]:
    """Freeze only the adopted field subset and exact execution resource identity."""
    document = _document()
    return {
        "adoption_id": ADOPTION_ID,
        "resource_sha256": RUNTIME_SHA256,
        "adopted_fields": sorted(document["fields"]),
        "sources": [{key: source[key] for key in ("rule_set_id", "revision", "sha256")}
                    for source in document["sources"]],
    }


def evaluate_fuel_power_field(field_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    """Return the same four-property final outcome as the review evaluator.

    Missing or mismatched binding context stays BLOCKED; it never falls back to
    another fuel, table, a measured source, or zero. This does not initialize or
    mutate an existing selection, and defaults are candidates, not write commands.
    """
    try:
        entry = _document()["fields"][field_id]
    except KeyError as exc:
        raise ValueError("此字段尚未采用燃料与电力共享规则。") from exc
    return _evaluate_entry(entry, context)


def _evaluate_entry(entry, context):
    current = dict(context)
    tag_keys = {key for policy in entry["policies"].values()
                for branch in policy["branches"] for key in branch["when"]["tags"]}
    for key, value in current.items():
        if key not in tag_keys or not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError("业务规则上下文包含未知字段或无效文本：" + str(key))
    return evaluate_field(entry["field"], entry["policies"], current, rule_set_id=entry["rule_set_id"])


def adopted_binding_conditions(field_id: str) -> tuple[dict[str, str], ...]:
    """Read exact approved binding identities from source qualification, no values.

    Returned tags are conditions to verify, not proof that a Catalog binding is
    valid. Copies prevent a caller from modifying the cached execution resource.
    """
    entry = _document()["fields"][field_id]
    source = entry["field"]["source_qualification"]
    if source["state"] != "POLICY":
        return ()
    return tuple(dict(branch["when"]["tags"])
                 for branch in entry["policies"][source["policy_id"]]["branches"]
                 if branch["when"]["tags"].get("binding_status") == "VERIFIED")


def electricity_catalogue_parameters() -> tuple[tuple[str, str, str | None], ...]:
    """Unique (table number, parameter ID, geography tag) from adopted conditions."""
    return tuple(sorted({
        (tags["catalog_table"], tags["parameter_id"],
         "province" if "province" in tags else "region" if "region" in tags else None)
        for tags in adopted_binding_conditions("electricity.factor") if "catalog_table" in tags
    }))


FUEL_FIELD_TYPES = {
    "fuel.lhv": "LOWER_HEATING_VALUE",
    "fuel.fch": "CARBON_CONTENT_PER_HEAT",
    "fuel.oxidation": "OXIDATION_RATE",
}


def fuel_source_context(field_id, *, resolver, origin, subject_id, accounting_period,
                        selected_factor_id=None) -> dict[str, str]:
    """Produce fuel context from real Resolver output and verified associations.

    A selection is preserved through confirmed_factor_id. Omitting it is only
    for displaying/initializing a new choice or explicitly returning to default.
    This does not change any input or selected business source.
    """
    from packages.core.models import ParameterType
    from packages.core.parameter_resolution import ParameterResolutionContext

    origin_value = getattr(origin, "value", origin) or "LEGACY_UNSPECIFIED"
    if origin_value not in {"CATALOG", "CUSTOM", "LEGACY_UNSPECIFIED"}:
        raise ValueError("未知燃料身份。")
    context = {"origin": origin_value}
    if field_id == "fuel.direct_carbon":
        return context
    if field_id not in FUEL_FIELD_TYPES:
        raise ValueError("此字段不是已采用的燃料参数。")
    if origin_value == "CUSTOM":
        return {**context, "binding_status": "ABSENT"}
    if origin_value != "CATALOG" or resolver is None or not subject_id:
        return {**context, "binding_status": "PENDING"}
    parameter_type = ParameterType(FUEL_FIELD_TYPES[field_id])
    parameter_id = resolver.reference_parameter_id(subject_id, parameter_type)
    if parameter_id is None:
        return {**context, "binding_status": "PENDING"}
    resolution = resolver.resolve(ParameterResolutionContext(
        parameter_id=parameter_id, standard_id="gbt_32151_34_2024",
        subject_id=subject_id, parameter_type=parameter_type, accounting_period=accounting_period,
        confirmed_factor_id=selected_factor_id,
        confirmation_reason="保留当前明确选择的燃料参数" if selected_factor_id else None,
    ))
    association = resolver.reference_binding_for(resolution)
    binding = association.binding
    if binding is None:
        return {**context, "binding_status": "ABSENT" if association.status == "ABSENT" else "PENDING"}
    # Association must also satisfy the exact adopted field condition; a valid
    # binding for some other table or concept does not grant this field a default.
    exact = any(tags["parameter_id"] == binding.parameter_id and tags["binding_id"] == binding.binding_id
                for tags in adopted_binding_conditions(field_id))
    if not exact:
        return {**context, "binding_status": "PENDING"}
    return {**context, "binding_status": "VERIFIED", "parameter_id": binding.parameter_id,
            "binding_id": binding.binding_id}


def electricity_source_context(resolver, resolution, *, direction: str, attribute: str) -> dict[str, str]:
    """Project the actual selected factor's association into adopted conditions.

    Direction and attribute are caller business facts and are never overwritten
    by a branch's expected value. In particular exported electricity cannot
    acquire the purchased nonfossil zero path by switching a display label.
    """
    if direction not in {"PURCHASED", "EXPORTED"} or attribute not in {"CONVENTIONAL", "NONFOSSIL", "FOSSIL"}:
        raise ValueError("电力方向或属性无效。")
    current = {"origin": "CATALOG", "direction": direction, "attribute": attribute}
    association = resolver.reference_binding_for(resolution)
    binding = association.binding
    if binding is None:
        return {**current, "binding_status": "ABSENT" if association.status == "ABSENT" else "PENDING"}
    conditions = [tags for tags in adopted_binding_conditions("electricity.factor")
                  if tags["parameter_id"] == binding.parameter_id and tags["binding_id"] == binding.binding_id
                  and tags.get("direction") == direction
                  and ("attribute" not in tags or tags["attribute"] == attribute)]
    if len(conditions) != 1:
        return {**current, "binding_status": "PENDING"}
    return {**conditions[0], **current, "binding_status": "VERIFIED"}


MATERIAL_RUNTIME_RESOURCE = "business_rules/material.json"
MATERIAL_ADOPTION_ID = "GHGTOOL_MATERIAL_R11_V1"
MATERIAL_RUNTIME_SHA256 = "1737efec0f3b27bc14b373d4e70f8870f162a3bef6a702931207f4dc6cd93c02"


@lru_cache(maxsize=1)
def _material_document():
    try:
        content = files("resources").joinpath(MATERIAL_RUNTIME_RESOURCE).read_bytes()
        if sha256(content).hexdigest() != MATERIAL_RUNTIME_SHA256:
            raise BusinessPolicyConfigurationError("材料业务规则资源校验失败，请重新安装完整软件。")
        document = json.loads(content)
        if document["format_version"] != 1 or document["adoption_id"] != MATERIAL_ADOPTION_ID:
            raise BusinessPolicyConfigurationError("材料业务规则版本不兼容。")
        return document
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BusinessPolicyConfigurationError("材料业务规则资源缺失或损坏。") from exc


def material_policy_identity():
    document = _material_document()
    return {"adoption_id": MATERIAL_ADOPTION_ID, "resource_sha256": MATERIAL_RUNTIME_SHA256,
            "adopted_fields": sorted(document["fields"]),
            "sources": [{key: source[key] for key in ("rule_set_id", "revision", "sha256")}
                        for source in document["sources"]]}


def evaluate_material_field(field_id: str, context: Mapping[str, Any]):
    try:
        entry = _material_document()["fields"][field_id]
    except KeyError as exc:
        raise ValueError("此字段尚未采用材料共享规则。") from exc
    return _evaluate_entry(entry, context)


FGD_RUNTIME_RESOURCE = "business_rules/fgd.json"
FGD_ADOPTION_ID = "GHGTOOL_FGD_R11_V1"
FGD_RUNTIME_SHA256 = "560c7151e797c47aeb0da698440ed773d1335d8498fbda35aac9e2781fa7bce7"


@lru_cache(maxsize=1)
def _fgd_document():
    try:
        content = files("resources").joinpath(FGD_RUNTIME_RESOURCE).read_bytes()
        if sha256(content).hexdigest() != FGD_RUNTIME_SHA256:
            raise BusinessPolicyConfigurationError("脱硫业务规则资源校验失败，请重新安装完整软件。")
        document = json.loads(content)
        if document["format_version"] != 1 or document["adoption_id"] != FGD_ADOPTION_ID:
            raise BusinessPolicyConfigurationError("脱硫业务规则版本不兼容。")
        return document
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BusinessPolicyConfigurationError("脱硫业务规则资源缺失或损坏。") from exc


def fgd_policy_identity():
    document = _fgd_document()
    return {"adoption_id": FGD_ADOPTION_ID, "resource_sha256": FGD_RUNTIME_SHA256,
            "adopted_fields": sorted(document["fields"]),
            "sources": [{key: source[key] for key in ("rule_set_id", "revision", "sha256")}
                        for source in document["sources"]]}


def fgd_binding_conditions(field_id):
    entry = _fgd_document()["fields"][field_id]
    source = entry["field"]["source_qualification"]
    return tuple(dict(branch["when"]["tags"])
                 for branch in entry["policies"][source["policy_id"]]["branches"]
                 if branch["when"]["tags"].get("binding_status") == "VERIFIED")


def evaluate_fgd_field(field_id, context):
    entry = _fgd_document()["fields"][field_id]
    tags = {key for policy in entry["policies"].values()
            for branch in policy["branches"] for key in branch["when"]["tags"]}
    ranges = {key for policy in entry["policies"].values()
              for branch in policy["branches"] for key in branch["when"]["ranges"]}
    for key, value in context.items():
        if key in ranges:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("脱硫有效组分数无效。")
        elif key not in tags or not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError("脱硫来源上下文包含未知或无效字段：" + str(key))
    return evaluate_field(entry["field"], entry["policies"], context, rule_set_id=entry["rule_set_id"])


from dataclasses import dataclass


@dataclass(frozen=True)
class FGDFieldResolution:
    """One real resolution supplies both qualification and adopted value."""
    context: Mapping[str, Any]
    factor: Any = None
    resolution: Any = None


def resolve_fgd_field(field_id, *, resolver, origin, carbonate_type=None,
                      accounting_period=None, component_count=1, selected_factor_id=None):
    from packages.core.models import ParameterType
    from packages.core.parameter_resolution import ParameterResolutionContext
    from .carbon_material_input_policy import carbonate_c2_identity
    origin_value = getattr(origin, "value", origin) or "LEGACY_UNSPECIFIED"
    if origin_value not in {"CATALOG", "CUSTOM", "LEGACY_UNSPECIFIED"}:
        raise ValueError("未知碳酸盐身份。")
    current = {"binding_status": "PENDING"}
    if field_id == "fgd.ratio":
        if isinstance(component_count, bool) or not isinstance(component_count, int) or component_count < 1:
            raise ValueError("脱硫有效组分数无效。")
        current["carbonate_component_count"] = component_count
        if component_count > 1:
            return FGDFieldResolution({**current, "binding_status": "ABSENT"})
    if field_id == "fgd.factor":
        identity = carbonate_c2_identity(carbonate_type) if origin_value == "CATALOG" else None
        if origin_value == "CUSTOM":
            return FGDFieldResolution({"binding_status": "ABSENT"})
        current["origin"] = origin_value
        if identity is None:
            return FGDFieldResolution(current)
        parameter_id, subject_id, kind = identity.parameter_id, identity.subject_id, ParameterType.PROCESS_CO2_FACTOR
    elif field_id in {"fgd.ratio", "fgd.conversion"}:
        parameter_id = "car-par-p04b-i" if field_id == "fgd.ratio" else "car-par-p04b-tr"
        subject_id, kind = "fgd", ParameterType.PROCESS_DEFAULT_PARAMETER
    else:
        raise ValueError("未知脱硫字段。")
    if resolver is None:
        return FGDFieldResolution(current)
    resolution = resolver.resolve(ParameterResolutionContext(
        parameter_id=parameter_id, standard_id="gbt_32151_34_2024", subject_id=subject_id,
        parameter_type=kind, accounting_period=accounting_period,
        confirmed_factor_id=selected_factor_id,
        confirmation_reason="保留当前明确选择的脱硫参数" if selected_factor_id else None,
    ))
    association = resolver.reference_binding_for(resolution)
    binding = association.binding
    if binding is None:
        return FGDFieldResolution({**current, "binding_status": "ABSENT" if association.status == "ABSENT" else "PENDING"}, resolution=resolution)
    if not any(tags["binding_id"] == binding.binding_id and tags["parameter_id"] == binding.parameter_id
               for tags in fgd_binding_conditions(field_id)):
        return FGDFieldResolution(current, resolution=resolution)
    return FGDFieldResolution({**current, "binding_status": "VERIFIED", "binding_id": binding.binding_id,
                               "parameter_id": binding.parameter_id}, resolution.recommended.factor, resolution)


HEAT_RUNTIME_RESOURCE = "business_rules/heat.json"
HEAT_ADOPTION_ID = "GHGTOOL_HEAT_R11_C3_V2"
HEAT_RUNTIME_SHA256 = "2f472b6a4774076472e0fae19e552986d67f4ed3ca29f63cd496d31002f215de"


@lru_cache(maxsize=1)
def _heat_document():
    try:
        content = files("resources").joinpath(HEAT_RUNTIME_RESOURCE).read_bytes()
        if sha256(content).hexdigest() != HEAT_RUNTIME_SHA256:
            raise BusinessPolicyConfigurationError("热力业务规则资源校验失败，请重新安装完整软件。")
        document = json.loads(content)
        if document["format_version"] != 1 or document["adoption_id"] != HEAT_ADOPTION_ID:
            raise BusinessPolicyConfigurationError("热力业务规则版本不兼容。")
        return document
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BusinessPolicyConfigurationError("热力业务规则资源缺失或损坏。") from exc


def heat_policy_identity():
    document = _heat_document()
    return {"adoption_id": HEAT_ADOPTION_ID, "resource_sha256": HEAT_RUNTIME_SHA256,
            "adopted_fields": sorted(document["fields"]),
            "sources": [{key: source[key] for key in ("rule_set_id", "revision", "sha256")}
                        for source in document["sources"]]}


def evaluate_heat_factor(context):
    return _evaluate_entry(_heat_document()["fields"]["heat.factor"], context)


def heat_source_context(resolver, resolution, *, business_source):
    """仅核验同次实际选择的目录绑定，不另行解析或以数值猜测身份。"""
    current = {"origin": "CATALOG", "binding_status": "ABSENT", "business_source": business_source}
    if resolver is None or resolution is None:
        return current
    association = resolver.reference_binding_for(resolution)
    binding = association.binding
    entry = _heat_document()["fields"]["heat.factor"]
    source = entry["field"]["source_qualification"]
    conditions = [branch["when"]["tags"]
                  for branch in entry["policies"][source["policy_id"]]["branches"]
                  if branch["when"]["tags"].get("binding_status") == "VERIFIED"]
    if binding is not None and any(tags["binding_id"] == binding.binding_id
                                   and tags["parameter_id"] == binding.parameter_id for tags in conditions):
        return {**current, "binding_status": "VERIFIED", "binding_id": binding.binding_id,
                "parameter_id": binding.parameter_id}
    return current


def heat_binding_conditions():
    entry = _heat_document()["fields"]["heat.factor"]
    source = entry["field"]["source_qualification"]
    return tuple(dict(branch["when"]["tags"])
                 for branch in entry["policies"][source["policy_id"]]["branches"]
                 if branch["when"]["tags"].get("binding_status") == "VERIFIED")
