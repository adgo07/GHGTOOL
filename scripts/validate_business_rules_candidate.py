#!/usr/bin/env python3
"""Validate candidate bundles and optionally emit a development catalog-value snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.application.business_rules_candidate import main as candidate_main

# This whitelist limits the optional audit snapshot to the three R11 review values.
_SNAPSHOT_FIELDS = ("fgd.ratio", "fgd.conversion", "heat.factor")
_DEFAULT_CATALOG_SOURCE = ROOT / "data-source" / "carbon_accounting" / "catalog.json"


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _decimal_text(value: Any) -> str:
    # Decimal values from catalog records stringify without float conversion.
    from decimal import Decimal

    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"catalog value must be a finite Decimal, got {value!r}")
    return str(value)


def _pages(location: str, label: str) -> list[int]:
    patterns = (
        rf"{re.escape(label)}第(\d+)(?:[～~–—-](\d+))?页",
        rf"{re.escape(label)}页(\d+)(?:[～~–—-](\d+))?",
    )
    match = next((candidate for pattern in patterns if (candidate := re.search(pattern, location))), None)
    if not match:
        return []
    start = int(match.group(1))
    end = int(match.group(2) or start)
    if end < start or end - start > 100:
        raise ValueError(f"invalid page range in source location: {location!r}")
    return list(range(start, end + 1))


def _article(location: str) -> str | None:
    match = re.search(r"第([^；;（）()\s]+?)条", location)
    return match.group(1) if match else None


def _binding_reference(field_id: str, technical: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in technical.get("fields", []) if row.get("field_id") == field_id]
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        value = (row.get("policy_branch_values") or {}).get("default")
        if not isinstance(value, dict) or value.get("state") != "BINDING":
            continue
        tags = ((row.get("conditions_by_property") or {}).get("default") or {}).get("tags") or {}
        parameter_id = value.get("parameter_id")
        tagged_parameter_id = tags.get("parameter_id")
        binding_id = tags.get("binding_id")
        if tags.get("binding_status") != "VERIFIED":
            raise ValueError(f"{field_id}: BINDING branch lacks a VERIFIED binding condition")
        if not parameter_id or parameter_id != tagged_parameter_id or not binding_id:
            raise ValueError(f"{field_id}: BINDING branch has incomplete or inconsistent identity tags")
        candidate = {
            "field_id": field_id,
            "rule_set_id": row.get("rule_set_id"),
            "policy_id": (row.get("policy_ids") or {}).get("default"),
            "branch_id": (row.get("condition_ids") or {}).get("default"),
            "parameter_id": parameter_id,
            "binding_id": binding_id,
        }
        candidates[(parameter_id, binding_id)] = candidate
    if len(candidates) != 1:
        raise ValueError(f"{field_id}: expected one exact BINDING reference, found {len(candidates)}")
    return next(iter(candidates.values()))


def _entry_from_catalog(field_id: str, reference: dict[str, Any], service: Any, repository: Any) -> dict[str, Any]:
    from packages.core.models import ReviewStatus

    binding_hits = [item for item in service.list_reference_data_bindings()
                    if item.binding_id == reference["binding_id"]]
    if len(binding_hits) != 1:
        raise ValueError(f"{field_id}: catalog binding must resolve uniquely")
    binding = binding_hits[0]
    if _enum_value(binding.review_status) != ReviewStatus.VERIFIED.value:
        raise ValueError(f"{field_id}: catalog binding is not VERIFIED")

    parameter_hits = [item for item in repository.list_parameters()
                      if item.parameter_id == reference["parameter_id"]]
    if len(parameter_hits) != 1:
        raise ValueError(f"{field_id}: catalog parameter must resolve uniquely")
    parameter = parameter_hits[0]
    if _enum_value(parameter.review_status) != ReviewStatus.VERIFIED.value:
        raise ValueError(f"{field_id}: catalog parameter is not VERIFIED")

    asset_hits = [item for item in service.list_reference_data_assets()
                  if item.asset_id == binding.asset_id]
    if len(asset_hits) != 1:
        raise ValueError(f"{field_id}: catalog asset must resolve uniquely for its binding")
    asset = asset_hits[0]
    if asset.parameter_id != reference["parameter_id"] or asset.parameter_id != parameter.parameter_id:
        raise ValueError(f"{field_id}: binding asset parameter does not match the candidate parameter")
    if asset.unit != parameter.canonical_unit:
        raise ValueError(f"{field_id}: catalog asset unit differs from the parameter canonical unit")

    table_hits = [item for item in service.list_source_tables()
                  if item.source_table_id == binding.source_table_id]
    if len(table_hits) != 1:
        raise ValueError(f"{field_id}: catalog source table must resolve uniquely")
    table = table_hits[0]
    source_hits = [item for item in service.list_sources() if item.source_id == table.source_id]
    if len(source_hits) != 1:
        raise ValueError(f"{field_id}: catalog source document must resolve uniquely")
    source = source_hits[0]
    if _enum_value(source.review_status) != ReviewStatus.VERIFIED.value:
        raise ValueError(f"{field_id}: catalog source document is not VERIFIED")

    rule_set_id = reference.get("rule_set_id") or ""
    marker = ".industry."
    if marker not in rule_set_id:
        raise ValueError(f"{field_id}: cannot derive the candidate standard from its industry rule-set identity")
    standard_id = rule_set_id.split(marker, 1)[1]
    applicable = list(binding.applicable_standard_ids)
    if standard_id not in applicable:
        raise ValueError(f"{field_id}: catalog binding does not explicitly apply to {standard_id}")
    if parameter.applicable_standard_ids and standard_id not in parameter.applicable_standard_ids:
        raise ValueError(f"{field_id}: catalog parameter does not apply to {standard_id}")

    binding_location = binding.source_location or table.source_location
    if not binding_location:
        raise ValueError(f"{field_id}: catalog binding has no source location")
    return {
        **reference,
        "candidate_standard_id": standard_id,
        "asset_id": asset.asset_id,
        "asset_version": asset.asset_version,
        "value": _decimal_text(asset.value),
        "unit": asset.unit,
        "source_value": _decimal_text(asset.source_value),
        "source_unit": asset.source_unit,
        "normalized_value": _decimal_text(asset.normalized_value),
        "normalized_unit": asset.normalized_unit,
        "source_id": source.source_id,
        "source_version": source.version,
        "source_table_id": table.source_table_id,
        "source_table_number": table.display_number,
        "source_table_title": table.title,
        "source_table_location": table.source_location,
        "binding_location": binding_location,
        "article": _article(binding_location),
        "pdf_pages": _pages(binding_location, "PDF"),
        "printed_pages": _pages(binding_location, "印刷"),
        "factor_year": binding.factor_year,
        "valid_from": binding.valid_from.isoformat() if binding.valid_from else None,
        "valid_to": binding.valid_to.isoformat() if binding.valid_to else None,
        "review_status": _enum_value(binding.review_status),
        "applicable_standard_ids": applicable,
    }


def _write_catalog_snapshot(
    snapshot_path: Path,
    catalog_source: Path,
    review_path: Path,
    technical_path: Path,
) -> None:
    from packages.application.catalog_queries import CatalogQueryService
    from packages.persistence.catalog_builder import build_catalog_database
    from packages.persistence.catalog_repository import SQLiteCatalogRepository
    from packages.reference_data import load_validated_catalog

    review_sha = _sha256_lf(review_path)
    review_doc = json.loads(review_path.read_text(encoding="utf-8"))
    technical_doc = json.loads(technical_path.read_text(encoding="utf-8"))
    bound_sha = ((technical_doc.get("metadata") or {}).get("source_compact_sha256"))
    if bound_sha != review_sha:
        raise ValueError("technical projection source_compact_sha256 does not match the exported compact projection")

    validated_catalog = load_validated_catalog(catalog_source)
    manifest = validated_catalog["manifest"]
    catalog_hash = _sha256_lf(catalog_source)
    entries: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="ghg-candidate-catalog-snapshot-") as directory:
        database_path = Path(directory) / "catalog.sqlite"
        build_catalog_database(source_path=catalog_source, output_path=database_path)
        repository = SQLiteCatalogRepository(database_path)
        service = CatalogQueryService(repository)
        for field_id in _SNAPSHOT_FIELDS:
            reference = _binding_reference(field_id, technical_doc)
            entries[field_id] = _entry_from_catalog(field_id, reference, service, repository)

    snapshot = {
        "schema_version": 1,
        "status": "CHECKED",
        "source_compact_sha256": review_sha,
        "catalog": {
            "catalog_id": manifest["catalog_id"],
            "data_version": manifest["data_version"],
            "canonical_source_lf_sha256": catalog_hash,
        },
        "entries": entries,
    }
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a review-only business-rule candidate bundle and optionally emit a development catalog-value snapshot."
    )
    parser.add_argument("--review-json", type=Path, help="write stable review rows as JSON")
    parser.add_argument("--technical-review-json", type=Path, help="write same-source technical details bound to the compact projection SHA256")
    parser.add_argument("--primary-rule-set-id", help="select a primary package when multiple are loaded")
    parser.add_argument("--catalog-snapshot", type=Path, help="write a separate, development-only snapshot of approved catalog references")
    parser.add_argument("--catalog-source", type=Path, default=_DEFAULT_CATALOG_SOURCE,
                        help="canonical catalog JSON source used only with --catalog-snapshot")
    parser.add_argument("paths", nargs="+", type=Path, help="fixed JSON package files in the closed bundle")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.catalog_snapshot and (args.review_json is None or args.technical_review_json is None):
        parser.error("--catalog-snapshot requires both --review-json and --technical-review-json")

    forwarded: list[str] = []
    if args.review_json:
        forwarded.extend(("--review-json", str(args.review_json)))
    if args.technical_review_json:
        forwarded.extend(("--technical-review-json", str(args.technical_review_json)))
    if args.primary_rule_set_id:
        forwarded.extend(("--primary-rule-set-id", args.primary_rule_set_id))
    forwarded.extend(str(path) for path in args.paths)
    result = candidate_main(forwarded)
    if result != 0 or args.catalog_snapshot is None:
        return result
    try:
        _write_catalog_snapshot(
            args.catalog_snapshot,
            args.catalog_source,
            args.review_json,
            args.technical_review_json,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"catalog snapshot generation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
