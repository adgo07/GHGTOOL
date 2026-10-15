"""Command line entry point for the strict candidate bundle validator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.application.business_rules_candidate import main

if __name__ == "__main__":
    raise SystemExit(main())
