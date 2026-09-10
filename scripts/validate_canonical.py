"""Validate the canonical JSON source from the command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.reference_data import (  # noqa: E402
    DEFAULT_SCHEMA_PATH,
    DEFAULT_SOURCE_PATH,
    CanonicalValidationError,
    load_validated_catalog,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Qingzhou canonical catalog JSON")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    args = parser.parse_args()
    try:
        catalog = load_validated_catalog(args.source, args.schema)
    except CanonicalValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        "valid: "
        f"{len(catalog['standards'])} standards, "
        f"{len(catalog['sources'])} sources, "
        f"{len(catalog['parameters'])} parameters, "
        f"{len(catalog['factors'])} factors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
