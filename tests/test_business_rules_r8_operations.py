"""Check R8 candidate operations against fixed Mapping vectors, not production calculations."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data-source/carbon_accounting/business-rules"
MAPPING = ROOT / "specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md"


class BusinessRulesR8OperationExpectations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((SOURCE / "software_policy.json").read_text(encoding="utf-8"))
        cls.mapping = MAPPING.read_text(encoding="utf-8")
        cls.operations = {item["operation_id"]: item for item in cls.policy["operations"]}

    def vector(self, vector_id):
        return next(line for line in self.mapping.splitlines() if vector_id in line)

    def text(self, operation_id):
        operation = self.operations[operation_id]
        return "\n".join(
            [operation["action"]]
            + operation["changes"]
            + operation["preserves"]
            + operation["confirmation"]
            + operation["pending"]
        )

    def test_candidate_revision_and_operation_schema(self):
        self.assertEqual(self.policy["revision"], "candidate-2026-10-16-r8")
        self.assertEqual(self.policy["status"], "CANDIDATE")
        self.assertTrue({
            "resolve_parameter_source",
            "formal_calculation_append_record",
            "read_record_render_word",
            "capture_external_co2_supplement",
            "resolve_steam_enthalpy",
        } <= self.operations.keys())
        self.assertIn("每次成功核算各追加一条新Record", self.operations["formal_calculation_append_record"]["action"])
        required_operation_keys = {
            "key", "operation_id", "name", "initial_context", "action", "changes",
            "preserves", "invalidates", "confirmation", "basis", "cases", "pending", "rule_ids",
        }
        self.assertEqual(len(self.operations), len(self.policy["operations"]))
        for operation in self.policy["operations"]:
            with self.subTest(operation=operation["operation_id"]):
                self.assertEqual(set(operation), required_operation_keys)

    def test_issue014_product_choice_is_separate_from_professional_open(self):
        text = self.text("resolve_parameter_source")
        for expected in ("库外值", "默认库内", "非阻断提醒", "来源说明选填",
                         "不得借用Catalog身份", "不自动标记为MEASURED",
                         "专业核验", "OPEN不阻断"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        changes = {item["key"]: item for item in self.policy["changes"]}
        alignment = changes["review.change.electricity_applicability"]
        self.assertIn("out-of-catalog product choice is approved", alignment["pending"][1])
        self.assertNotIn("Table 2/4/5 paths and Issue014 supply-unit", text)
        self.assertNotIn("等待映射/实现对齐", str(alignment))

    def test_issue015_heat_attribution_does_not_guess_unclear_boundary(self):
        vector = self.vector("TV-CAR-POL-006")
        for expected in ("1000kg蒸汽", ".308", "同边界燃料已计", "不再增加购热排放", "边界不明不猜值"):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector)
        text = self.text("formal_calculation_append_record")
        for expected in ("边界外购入蒸汽", "同边界燃料已计", "边界未明", "不猜算", "不自动置零"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_external_co2_states_and_validation_match_vectors(self):
        vector004 = self.vector("TV-CAR-POL-004")
        vector005 = self.vector("TV-CAR-POL-005")
        for expected in ("ES100", "EI20", "ET120", "未纳入草稿5/纳入空/纳入0/纳入5",
                         "补充依次不参与/待补未形成/120/125", "旧Record无字段不造0"):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector004)
        for expected in ("-1/NaN/tCO₂e", "已纳入的非法值/单位", "范围外值ERROR", "禁用草稿不参与"):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector005)
        text = self.text("capture_external_co2_supplement")
        for expected in ("同一企业汇总边界", "同一期间", "非负tCO₂", "纳入但空白",
                         "不造0", "纳入真实0", "一次独立补充合计",
                         "不并入、不覆盖ES、EI或ET", "非有限值", "ERROR"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        formal = self.text("formal_calculation_append_record")
        report = self.text("read_record_render_word")
        self.assertIn("另冻结补充合计", formal)
        self.assertIn("不重算", report)
        self.assertIn("旧Record无该字段", report)
        self.assertIn("不补造0", report)

    def test_material_reminders_and_iapws_candidate_boundary(self):
        vector007 = self.vector("TV-CAR-POL-007")
        for expected in ("必要数值完整", "检测编号、合同附件和长说明全空",
                         "计算型Word可继续", "不称报告全文已核验", "只读不现场重算"):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector007)
        formal = self.text("formal_calculation_append_record")
        report = self.text("read_record_render_word")
        self.assertIn("缺证明/附件或未审核只产生提醒", formal)
        self.assertIn("单位/量纲、数量基准、选定方法及目录身份", formal)
        self.assertIn("不声称报告全文已核验", report)

        vector011 = self.vector("TV-CAR-POL-011")
        vector012 = self.vector("TV-CAR-POL-012")
        self.assertIn("不用旧矩形内插1505.75", vector011)
        self.assertIn("仍.308tCO₂", vector012)
        steam = self.text("resolve_steam_enthalpy")
        for expected in ("iapws.IAPWS97", "候选", "C.4/C.5", "不回退旧表",
                         "合法的已知焓", "辅助失败", "不实现或安装",
                         "不声称生产数值Profile/Conformance已完成"):
            with self.subTest(expected=expected):
                self.assertIn(expected, steam)


if __name__ == "__main__":
    unittest.main()
