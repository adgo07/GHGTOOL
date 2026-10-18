"""机械投影本包采用的脱硫字段，保留燃料/电力原采用身份。"""
from __future__ import annotations
import argparse
from pathlib import Path
from scripts.project_fuel_power_rules import ROOT, projected_bytes

FGD_FIELDS = ("fgd.ratio", "fgd.factor", "fgd.conversion")
FGD_ADOPTION_ID = "GHGTOOL_FGD_R11_V1"
FGD_RUNTIME_PATH = Path("resources/business_rules/fgd.json")


def projected_fgd_bytes(root: Path = ROOT) -> bytes:
    return projected_bytes(root, adopted_fields=FGD_FIELDS, adoption_id=FGD_ADOPTION_ID)


def verify_fgd_projection(root: Path = ROOT) -> None:
    if (root / FGD_RUNTIME_PATH).read_bytes() != projected_fgd_bytes(root):
        raise ValueError("脱硫运行资源与批准Canonical机械投影不一致。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        (ROOT / FGD_RUNTIME_PATH).write_bytes(projected_fgd_bytes())
    else:
        verify_fgd_projection()
    print("fgd Canonical projection: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
