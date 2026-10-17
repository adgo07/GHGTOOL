"""Pure evaluation of the existing module-local business field policies.

No catalog access, review rendering, UI state, numeric calculation, or new DSL.
The review adapter and adopted production fields use the same final outcome.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any, Mapping

def _uses_unbound_fuel_source_qualification(
    field_id: str, context: Mapping[str, Any] | None,
) -> bool:
    return (
        field_id in frozenset({"fuel.lhv", "fuel.fch"})
        and isinstance(context, Mapping)
        and context.get("origin") in {"CUSTOM", "CATALOG"}
        and context.get("binding_status") == "ABSENT"
    )


def condition_matches(when: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
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
        if not actual.is_finite():
            return False
        if "min" in bounds:
            lower = Decimal(str(bounds["min"]))
            if actual < lower or (actual == lower and not bounds["include_min"]):
                return False
        if "max" in bounds:
            upper = Decimal(str(bounds["max"]))
            if actual > upper or (actual == upper and not bounds["include_max"]):
                return False
    return True


def apply_policy(policy: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    matches = [branch for branch in policy["branches"] if condition_matches(branch["when"], context)]
    if len(matches) == 1:
        branch = matches[0]
        state = deepcopy(branch["value"])
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


def evaluate_field(field: Mapping[str, Any], policies: Mapping[str, Mapping[str, Any]],
                   current: Mapping[str, Any], *, rule_set_id: str) -> dict[str, Any]:
    field_id = field["id"]
    entry_key = f"{rule_set_id}:{field_id}"
    local_problems: list[dict[str, Any]] = []
    state_map: dict[str, Any] = {}
    for property_name, source in (
        ("default_source", field["default_source"]),
        ("default", field["default"]),
        ("source_qualification", field["source_qualification"]),
    ):
        if source["state"] == "POLICY":
            outcome = apply_policy(policies[source["policy_id"]], current)
        else:
            state = source["state"]
            status = (
                "PENDING" if state == "PENDING"
                else "NO_LEGAL_SOURCES" if state == "NO_LEGAL_SOURCES"
                else "RESOLVED"
            )
            outcome = {
                "status": status, "value": deepcopy(source), "condition_id": None,
                "policy_id": None, "message": source.get("reason"),
            }
        state_map[property_name] = outcome
        # A default source is a candidate for explicit initialization. It is
        # informational here and never changes or gates an existing context.
        if property_name != "default_source" and outcome["status"] != "RESOLVED":
            local_problems.append({
                "code": outcome["status"], "entry_key": entry_key, "field_id": field_id,
                "rule_set_id": rule_set_id, "property": property_name,
                "message": outcome["message"] or f"{property_name} is not eligible to execute",
            })
    source_outcome = state_map["source_qualification"]
    resolved_source = source_outcome.get("value")
    invalid_source_message: str | None = None
    if (
        source_outcome["status"] == "MISSING_CONTEXT"
        and isinstance(current.get("source_path"), str)
        and current["source_path"].startswith("CATALOGUE_TABLE_")
    ):
        source_reason = (
            "当前目录表路径的来源身份或绑定信息不完整、不匹配，未能确认与所选目录表、方向及适用属性/地区"
            "精确对应的目录绑定；该路径保持阻断，不回退其他目录值、实测来源或零值。"
        )
        source_outcome = {**source_outcome, "message": source_reason}
        state_map["source_qualification"] = source_outcome
        for problem in local_problems:
            if (
                problem.get("code") == "MISSING_CONTEXT"
                and problem.get("property") == "source_qualification"
            ):
                problem["message"] = source_reason
    if (
        "business_source" in current
        and source_outcome["status"] == "RESOLVED"
        and isinstance(resolved_source, Mapping)
        and resolved_source.get("state") == "NOT_APPLICABLE"
        and source_outcome.get("policy_id") is not None
    ):
        local_problems.append({
            "code": "SOURCE_NOT_APPLICABLE", "entry_key": entry_key, "field_id": field_id,
            "rule_set_id": rule_set_id, "property": "source_qualification",
            "business_source": current["business_source"],
            "message": (
                "this input path has no business_source selection; omit business_source "
                "instead of inferring a measured, calculated, or standard-default source"
            ),
        })
    elif (
        "business_source" in current
        and source_outcome["status"] == "RESOLVED"
        and isinstance(resolved_source, Mapping)
        and resolved_source.get("state") == "FIXED"
        and current["business_source"] not in resolved_source["values"]
    ):
        allowed_sources = list(resolved_source["values"])
        invalid_source_message = (
            f"当前来源“{current['business_source']}”不在此字段当前条件下的有效来源集合中；"
            f"允许来源：{'、'.join(allowed_sources)}。"
        )
        local_problems.append({
            "code": "SOURCE_NOT_ALLOWED", "entry_key": entry_key, "field_id": field_id,
            "rule_set_id": rule_set_id, "property": "source_qualification",
            "business_source": current["business_source"], "allowed_sources": allowed_sources,
            "message": invalid_source_message,
        })
    locking_source = field["locking"]
    if locking_source.get("state") == "POLICY":
        locking_outcome = apply_policy(
            policies[locking_source["policy_id"]], current,
        )
    else:
        locking_outcome = {
            "status": "RESOLVED", "value": deepcopy(locking_source), "condition_id": None,
            "policy_id": None, "message": None,
        }
    locking = locking_outcome["value"] if locking_outcome["status"] == "RESOLVED" else None
    if (
        invalid_source_message is not None
        and isinstance(locking, Mapping)
        and isinstance(locking.get("value"), Mapping)
        and locking["value"].get("state") == "PENDING"
    ):
        locking = {key: dict(value) for key, value in locking.items()}
        locking["value"]["reason"] = (
            f"{invalid_source_message}请先选择合法来源，再继续使用该字段数值。"
        )
        locking_outcome = {**locking_outcome, "value": locking}
    qualification_value = source_outcome.get("value")
    qualified_sources = (
        qualification_value.get("values", [])
        if isinstance(qualification_value, Mapping)
        and qualification_value.get("state") == "FIXED" else []
    )
    selected_source = current.get("business_source")
    if (
        _uses_unbound_fuel_source_qualification(field_id, current)
        and source_outcome["status"] == "RESOLVED"
        and len(qualified_sources) == 1
        and selected_source is not None
        and isinstance(locking, Mapping)
        and isinstance(locking.get("source"), Mapping)
    ):
        source_is_qualified = selected_source in qualified_sources
        locking = {
            **locking,
            "source": {
                "state": "LOCKED" if source_is_qualified else "EDITABLE",
                "reason": (
                    "当前有效来源资格仅包含一个合法来源；来源选择已锁定。"
                    if source_is_qualified else
                    "当前选择不属于有效来源资格；来源选择仍可编辑，以便纠正。"
                ),
            },
        }
        locking_outcome = {**locking_outcome, "value": locking}
    if locking_outcome["status"] != "RESOLVED":
        local_problems.append({
            "code": locking_outcome["status"], "entry_key": entry_key, "field_id": field_id,
            "rule_set_id": rule_set_id, "property": "locking",
            "message": locking_outcome["message"] or "locking policy did not resolve uniquely",
        })
    elif locking is not None:
        for key in ("value", "source"):
            lock_state = locking[key]["state"]
            if lock_state in {"PENDING", "CONDITIONAL"}:
                local_problems.append({
                    "code": "PENDING_LOCKING" if lock_state == "PENDING" else "CONDITIONAL_LOCKING",
                    "entry_key": entry_key, "field_id": field_id,
                    "rule_set_id": rule_set_id, "property": key,
                    "message": locking[key]["reason"],
                })
    return {
        **state_map, "locking": deepcopy(locking) if locking is not None else deepcopy(locking_source),
        "locking_outcome": locking_outcome,
        "status": "BLOCKED" if local_problems else "READY",
        "problems": local_problems,
    }
