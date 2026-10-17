"""Mechanically project only adopted fuel/power fields for the Windows runtime."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.application.business_rules_candidate import load_bundle

SOURCE_PATHS = (
    "data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json",
    "data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json",
    "data-source/carbon_accounting/business-rules/software_policy.json",
)
RUNTIME_PATH = Path("resources/business_rules/fuel_power.json")
ADOPTED_FIELDS = ("fuel.direct_carbon", "fuel.lhv", "fuel.fch", "fuel.oxidation", "electricity.factor")
PROPERTIES = ("source_qualification", "default_source", "default", "locking")


def projected_bytes(root: Path = ROOT, *, adopted_fields=ADOPTED_FIELDS, adoption_id="GHGTOOL_FUEL_POWER_R11_V1") -> bytes:
    bundle = load_bundle(root / name for name in SOURCE_PATHS)
    entries = {}
    for package, field in bundle._field_entries():
        if field["id"] not in adopted_fields:
            continue
        if field["id"] in entries:
            raise ValueError("Ambiguous adopted runtime field: " + field["id"])
        policy_ids = {field[key]["policy_id"] for key in PROPERTIES if field[key]["state"] == "POLICY"}
        entries[field["id"]] = {
            "rule_set_id": package.rule_set_id,
            "revision": package.revision,
            "field": {"id": field["id"], **{key: field[key] for key in PROPERTIES}},
            "policies": {key: package.policies[key] for key in sorted(policy_ids)},
        }
    if set(entries) != set(adopted_fields):
        raise ValueError("Missing adopted fuel/power field")
    document = {
        "format_version": 1,
        "adoption_id": adoption_id,
        "sources": [
            {"path": name, "sha256": sha256((root / name).read_bytes()).hexdigest(),
             "rule_set_id": package.rule_set_id, "revision": package.revision,
             "dependency": package.document["dependency"], "adopts": package.document["adopts"]}
            for name, package in zip(SOURCE_PATHS, bundle.packages)
        ],
        "fields": entries,
    }
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def verify_projection(root: Path = ROOT) -> None:
    if (root / RUNTIME_PATH).read_bytes() != projected_bytes(root):
        raise ValueError("Fuel/power runtime resource differs from the adopted Canonical projection")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        target = ROOT / RUNTIME_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(projected_bytes())
    else:
        verify_projection()
    print("fuel/power Canonical projection: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
