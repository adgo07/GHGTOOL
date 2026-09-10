"""Build catalog.sqlite from a validated canonical JSON source."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.persistence import build_catalog_database  # noqa: E402
from packages.reference_data import DEFAULT_SOURCE_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Qingzhou catalog.sqlite")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=Path("build/databases/catalog.sqlite"))
    parser.add_argument("--app-version", default="0.1.0")
    args = parser.parse_args()
    output = build_catalog_database(args.source, args.output, app_version=args.app_version)
    print(f"built: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
