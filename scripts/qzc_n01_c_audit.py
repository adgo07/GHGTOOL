"""Emit a reproducible static inventory for QZC-N01-C.

This is evidence only.  It classifies syntactic tolerance/numeric-boundary
markers without changing business behavior or declaring any platform Contract.
"""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOTS = (Path("packages"), Path("tests"))
PATTERNS = {
    "is_close": re.compile(r"\bis_close\s*\("),
    "tolerance": re.compile(r"\btolerance\b", re.IGNORECASE),
    "abs_difference": re.compile(r"\babs\s*\([^\n]*-"),
    "approximate": re.compile(r"\bapprox(?:imate|imately|imation)?\b", re.IGNORECASE),
    "interpolation": re.compile(r"interpolat", re.IGNORECASE),
}


def category_for(path: Path, line: str, marker: str) -> str:
    normalized = path.as_posix()
    if normalized.startswith("tests/"):
        return "test_assertion"
    if marker == "interpolation":
        return "lookup/interpolation"
    if "round_for_display" in line or "format_for_display" in line:
        return "display"
    if marker in {"is_close", "tolerance", "abs_difference", "approximate"}:
        return "business_or_algorithmic_review"
    return "unclassified"


def build_inventory() -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for root in ROOTS:
        for path in sorted(root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), 1):
                for marker, pattern in PATTERNS.items():
                    if pattern.search(line):
                        inventory.append(
                            {
                                "path": path.as_posix(),
                                "line": line_number,
                                "marker": marker,
                                "category": category_for(path, line, marker),
                                "text": line.strip(),
                            }
                        )
    return inventory


def main() -> int:
    inventory = build_inventory()
    business_is_close = [
        item for item in inventory
        if item["marker"] == "is_close"
        and str(item["path"]).startswith("packages/")
        and not (
            item["path"] == "packages/core/decimal_policy.py"
            and str(item["text"]).startswith("def is_close")
        )
    ]
    payload = {
        "pilot_id": "N01-C",
        "inventory_count": len(inventory),
        "business_is_close_calls": business_is_close,
        "inventory": inventory,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if business_is_close else 0


if __name__ == "__main__":
    raise SystemExit(main())
