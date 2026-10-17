"""Development-only checks for the business-rule review asset manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

DEFINITION_ASSET_HASH_POLICY = "UTF8_TEXT_CRLF_TO_LF_SHA256"
EXPECTED_DEFINITION_ASSETS = (
    "data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json",
    "data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json",
    "data-source/carbon_accounting/business-rules/software_policy.json",
    "specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CHECKS = _REPOSITORY_ROOT / "docs/architecture/business-rules/evidence/review-artifact-checks.json"


def definition_text_sha256(content: bytes) -> str:
    """Hash UTF-8 text bytes after replacing CRLF pairs with LF; preserve all other bytes."""
    if not isinstance(content, bytes):
        raise TypeError("definition text must be provided as bytes")
    content.decode("utf-8")
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def verify_definition_assets(root: str | Path, checks: Mapping[str, Any]) -> int:
    """Verify every registered definition asset against its normalized text hash."""
    if checks.get("definition_assets_hash_policy") != DEFINITION_ASSET_HASH_POLICY:
        raise ValueError(
            "definition_assets_hash_policy must be " + DEFINITION_ASSET_HASH_POLICY
        )
    recorded = checks.get("definition_assets_sha256")
    if not isinstance(recorded, Mapping):
        raise ValueError("definition_assets_sha256 must be an object")
    expected_paths = set(EXPECTED_DEFINITION_ASSETS)
    recorded_paths = set(recorded)
    if recorded_paths != expected_paths:
        missing = sorted(expected_paths - recorded_paths)
        extra = sorted(recorded_paths - expected_paths)
        raise ValueError(f"definition asset list mismatch: missing={missing}, extra={extra}")

    root_path = Path(root)
    for relative in EXPECTED_DEFINITION_ASSETS:
        content = (root_path / relative).read_bytes()
        actual = definition_text_sha256(content)
        expected = recorded[relative]
        if not isinstance(expected, str) or actual != expected:
            raise ValueError(
                f"SHA-256 mismatch for {relative}: expected {expected!r}, got {actual}"
            )
    return len(EXPECTED_DEFINITION_ASSETS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the checked-in business-rule definition asset hashes."
    )
    parser.add_argument("--root", type=Path, default=_REPOSITORY_ROOT)
    parser.add_argument("--checks", type=Path, default=_DEFAULT_CHECKS)
    args = parser.parse_args(argv)
    try:
        checks = json.loads(args.checks.read_text(encoding="utf-8"))
        count = verify_definition_assets(args.root, checks)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"definition asset check failed: {exc}\n")
    print(
        f"Verified {count} definition assets with "
        f"{DEFINITION_ASSET_HASH_POLICY}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())