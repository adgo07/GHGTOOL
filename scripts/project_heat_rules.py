"""机械投影批准的 heat.factor，数值仍由真实 Resolver 提供。"""
from pathlib import Path
from scripts.project_fuel_power_rules import ROOT, projected_bytes

HEAT_ADOPTION_ID = "GHGTOOL_HEAT_R11_V1"
HEAT_RUNTIME_PATH = Path("resources/business_rules/heat.json")

def projected_heat_bytes(root=ROOT):
    return projected_bytes(root, adopted_fields=("heat.factor",), adoption_id=HEAT_ADOPTION_ID)

def verify_heat_projection(root=ROOT):
    if (root / HEAT_RUNTIME_PATH).read_bytes() != projected_heat_bytes(root):
        raise ValueError("热力运行资源与批准Canonical机械投影不一致。")

if __name__ == "__main__":
    verify_heat_projection()
    print("heat Canonical projection: PASS")
