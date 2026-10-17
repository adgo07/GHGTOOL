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
RUNTIME_SHA256 = "a88bb47f534deefebaa49a8e502b98259d9fadfd3a922abdb562e53661ed7107"
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
