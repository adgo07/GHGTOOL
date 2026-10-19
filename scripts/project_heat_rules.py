"""只投影热力字段及Owner批准C.3资格补齐；原R11审阅资产和其他采用身份不变。"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from scripts.project_fuel_power_rules import ROOT, projected_bytes

HEAT_ADOPTION_ID = "GHGTOOL_HEAT_R11_C3_V2"
HEAT_RUNTIME_PATH = Path("resources/business_rules/heat.json")
ADOPTION_PATH = Path("data-source/carbon_accounting/business-rules/heat_c3_adoption.json")


def projected_heat_bytes(root=ROOT):
    content = (root / ADOPTION_PATH).read_bytes()
    if b"\r" in content:
        raise ValueError("热力Canonical采用文件须为LF原字节；请修正源文件，不归一化来源哈希。")
    adoption = json.loads(content)
    if (set(adoption) != {"format_version", "adoption_id", "rule_set_id", "revision", "field_id", "base_binding_id", "additional_binding_id", "parameter_id", "authority", "owner_message_id"}
            or adoption["format_version"] != 1 or adoption["adoption_id"] != HEAT_ADOPTION_ID
            or adoption["field_id"] != "heat.factor"):
        raise ValueError("热力来源采用文件版本或结构错误")
    document = json.loads(projected_bytes(root, adopted_fields=("heat.factor",), adoption_id=HEAT_ADOPTION_ID))
    entry = document["fields"]["heat.factor"]
    for policy in entry["policies"].values():
        additions = []
        for branch in policy["branches"]:
            tags = branch["when"]["tags"]
            if tags.get("binding_id") == adoption["base_binding_id"]:
                if tags.get("parameter_id") != adoption["parameter_id"]:
                    raise ValueError("原热力绑定的参数身份不一致")
                extra = deepcopy(branch)
                extra["id"] += "_c3_adoption"
                extra["when"]["tags"]["binding_id"] = adoption["additional_binding_id"]
                additions.append(extra)
        if not additions:
            raise ValueError("热力属性缺少可补齐的准确绑定分支")
        policy["branches"].extend(additions)
    document["sources"].append({"path": ADOPTION_PATH.as_posix(), "sha256": sha256(content).hexdigest(),
        "rule_set_id": adoption["rule_set_id"], "revision": adoption["revision"]})
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))+"\n").encode()


def verify_heat_projection(root=ROOT):
    if (root / HEAT_RUNTIME_PATH).read_bytes() != projected_heat_bytes(root):
        raise ValueError("热力运行资源与批准Canonical机械投影不一致。")


if __name__ == "__main__":
    verify_heat_projection()
    print("heat Canonical projection: PASS")
