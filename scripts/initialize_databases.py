"""Build the isolated catalog, user, records and projects databases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.persistence import build_all_databases  # noqa: E402
from packages.reference_data import DEFAULT_SOURCE_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Qingzhou catalog/user/records/projects databases")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=Path("build/databases"))
    parser.add_argument("--app-version", default="1.1.0")
    args = parser.parse_args()
    paths = build_all_databases(args.output_dir, args.source, app_version=args.app_version)
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
