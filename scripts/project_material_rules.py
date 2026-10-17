"""机械投影本包采用的材料字段，保留燃料/电力原采用身份。"""
from __future__ import annotations
import argparse
from pathlib import Path
from scripts.project_fuel_power_rules import ROOT, projected_bytes

MATERIAL_FIELDS = ("material.fixed_carbon", "material.volatile_matter")
MATERIAL_ADOPTION_ID = "GHGTOOL_MATERIAL_R11_V1"
MATERIAL_RUNTIME_PATH = Path("resources/business_rules/material.json")


def projected_material_bytes(root: Path = ROOT) -> bytes:
    return projected_bytes(root, adopted_fields=MATERIAL_FIELDS, adoption_id=MATERIAL_ADOPTION_ID)


def verify_material_projection(root: Path = ROOT) -> None:
    if (root / MATERIAL_RUNTIME_PATH).read_bytes() != projected_material_bytes(root):
        raise ValueError("材料运行资源与批准Canonical机械投影不一致。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        (ROOT / MATERIAL_RUNTIME_PATH).write_bytes(projected_material_bytes())
    else:
        verify_material_projection()
    print("material Canonical projection: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
