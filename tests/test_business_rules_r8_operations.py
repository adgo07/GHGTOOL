"""Check R8 candidate operations against fixed Mapping vectors, not production calculations."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data-source/carbon_accounting/business-rules"
MAPPING = ROOT / "specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md"
STANDARD = SOURCE / "standards" / "gbt_32151_34_2024.json"


class BusinessRulesR8OperationExpectations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((SOURCE / "software_policy.json").read_text(encoding="utf-8"))
        cls.standard = json.loads(STANDARD.read_text(encoding="utf-8"))
        cls.mapping = MAPPING.read_text(encoding="utf-8")
        cls.policy_operations = {item["operation_id"]: item for item in cls.policy["operations"]}
        cls.standard_operations = {item["operation_id"]: item for item in cls.standard["operations"]}
        cls.operations = {**cls.policy_operations, **cls.standard_operations}

    def vector(self, vector_id):
        return next(line for line in self.mapping.splitlines() if vector_id in line)

    def text(self, operation_id):
        operation = self.operations[operation_id]
        return "\n".join(
            [operation["initial_context"]["object"], operation["action"]]
            + operation["changes"]
            + operation["preserves"]
            + operation["invalidates"]
            + operation["confirmation"]
            + operation["pending"]
        )

    def test_candidate_revision_and_operation_schema(self):
        self.assertEqual(self.policy["revision"], "candidate-2026-10-16-r10")
        self.assertEqual(self.standard["revision"], "candidate-2026-10-16-r10")
        self.assertIn(
            {"rule_set_id": "qz.carbon_accounting.software_policy", "revision": self.policy["revision"]},
            self.standard["dependency"],
        )
        compatibility = {item["key"]: item for item in self.policy["changes"]}["review.change.compatibility_scope"]
        self.assertIn("未改生产codec、受控模板、数据库迁移或历史Record", compatibility["after"])
        self.assertIn("ELECTRICITY_AND_COMPATIBILITY_EVIDENCE.md", compatibility["after"])
        self.assertIn("未来生产接入时仍须", compatibility["pending"][0])
        self.assertEqual(self.policy["status"], "CANDIDATE")
        self.assertTrue({
            "resolve_parameter_source",
            "formal_calculation_append_record",
            "read_record_render_word",
            "capture_external_co2_supplement",
            "resolve_steam_enthalpy",
        } <= self.operations.keys())
        self.assertIn("每次成功核算新增一条正式核算记录", self.operations["formal_calculation_append_record"]["action"])
        required_operation_keys = {
            "key", "operation_id", "name", "initial_context", "action", "changes",
            "preserves", "invalidates", "confirmation", "basis", "cases", "pending", "rule_ids",
        }
        self.assertTrue({
            "calculate_calcination_role_carbon",
            "aggregate_fume_monitoring_segments",
        } <= self.standard_operations.keys())
        self.assertEqual(len(self.policy_operations), len(self.policy["operations"]))
        all_operations = self.policy["operations"] + self.standard["operations"]
        for operation in all_operations:
            with self.subTest(operation=operation["operation_id"]):
                self.assertEqual(set(operation), required_operation_keys)

    def test_toggle_emission_source_expires_current_result_but_allows_valid_recalculation(self):
        operation = self.operations["toggle_emission_source"]
        invalidates = "\n".join(operation["invalidates"])
        self.assertIn("当前草稿对应的输入校验状态、计算结果及结果展示标记为过期（stale）", invalidates)
        self.assertIn("标记为过期（stale）", "\n".join(operation["changes"]))
        self.assertIn("通过现有致命校验时仍可正式重算", invalidates)
        self.assertIn("过期（stale）本身不阻断重算", invalidates)
        self.assertIn("草稿变更不使基于既有不可变正式核算记录的历史查看或Word导出失效", invalidates)
        self.assertNotIn("重新核算前保持不可用", invalidates)
        self.assertIn("过期（stale）本身不是禁用条件", "\n".join(operation["confirmation"]))

        report = self.operations["read_record_render_word"]
        self.assertIn("只读取已保存记录", report["action"])
        self.assertIn("不重新计算", report["action"])

    def test_fch_unit_and_scope_do_not_create_a_heat_activity_entry(self):
        fch = {field["id"]: field for field in self.standard["fields"]}["fuel.fch"]
        self.assertEqual(fch["unit"], "tC/GJ")
        self.assertNotIn("HEAT path", fch["unit"])
        self.assertEqual({item["unit"] for item in fch["channel_projections"]}, {"tC/GJ"})
        for projection in fch["channel_projections"]:
            with self.subTest(channel=projection["channel"]):
                self.assertIn("按热值路径", projection["notes"])
                self.assertIn("活动量可按质量或体积输入", projection["notes"])
                self.assertIn("不新增HEAT活动量入口", projection["notes"])

    def test_review_text_has_no_duplicate_chinese_translation_terms(self):
        for operation in self.policy["operations"] + self.standard["operations"]:
            rendered = self.text(operation["operation_id"]).replace("Canonical", "统一输入").replace("Record", "正式记录")
            with self.subTest(operation=operation["operation_id"]):
                self.assertNotIn("统一输入输入", rendered)
                self.assertNotIn("正式正式记录", rendered)

    def test_issue014_explicit_electricity_other_choice_preserves_validation_and_identity(self):
        text = self.text("resolve_parameter_source")
        for expected in ("electricity.factor", "OTHER", "常规默认仍为目录来源", "非阻断核实提醒",
                         "来源说明文字选填", "留空不阻断", "不赋目录参数/source binding ID",
                         "不自动标记为MEASURED", "有限性", "合法单位/量纲", "OTHER不绕过校验",
                         "不因此开放燃料或其他字段的OTHER"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        changes = {item["key"]: item for item in self.policy["changes"]}
        alignment = changes["review.change.electricity_applicability"]
        self.assertIn("显式选择OTHER", alignment["after"])
        self.assertIn("专业等价证明", alignment["reason"])
        self.assertNotIn("等待映射/实现对齐", str(alignment))
        self.assertNotIn("专业OPEN", text)

    def test_issue018_calcination_uses_role_indexed_existing_content_field(self):
        text = self.text("calculate_calcination_role_carbon")
        for expected in (
            "CAR-FML-CALCINATION-001", "CAR-FLD-P01-WFC-C",
            "CC×WFC-C[CC]", "UCC×WFC-C[UCC]", "DU×WFC-C[DU]",
            "收到基", "挥发分项", "K1", "44/12", "44/16",
            "不新增字段ID", "标准印刷式转录不改", "不表述为标准原式改写",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        changes = {item["key"]: item for item in self.standard["changes"]}
        self.assertIn("按CC/UCC/DU各自质量", changes["review.change.calcination_role_carbon"]["after"])
        self.assertIn("formal Calculator", changes["review.change.calcination_role_carbon"]["pending"][0])
        vector = self.vector("TV-CAR-POL-016")
        for expected in ("WFC-C[CC]=.8", "WFC-C[UCC]=.4", "WFC-C[DU]=.25",
                         "226.8291666666666666666666666666666666667", "162.6625"):
            self.assertIn(expected, vector)

    def test_issue020_p04a_segments_remain_separate_from_annual_coverage(self):
        text = self.text("aggregate_fume_monitoring_segments")
        for expected in (
            "CAR-FML-FUME-INCINERATION-001", "CAR-FLD-P04A-Q", "CAR-FLD-P04A-QVAR",
            "CAR-FLD-P04A-T", "同一烟气排放源实例、同一计量边界", "互不重叠监测段", "本段Q_i、QVar_i与T_i",
            "段间求和", "全年报告时长另行记录", "不同真实设备/排放源实例可有同时段", "不跨对象去重", "不回填", "未覆盖区间保持未覆盖",
            "不默认为0", "不得称为完整全年结果", "不得进行全年回填、年化或外推",
            "不表述为标准新增公式",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        vector = self.vector("TV-CAR-POL-017")
        for expected in (".0704tCO₂", ".1408tCO₂", ".2112tCO₂", "不把未覆盖期默认为零"):
            self.assertIn(expected, vector)

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
        self.assertIn("当前企业汇总边界和核算期间下可选的外部CO₂补充输入", text)
        for expected in ("同一企业汇总边界", "同一期间", "非负tCO₂", "纳入但空白",
                         "不造0", "纳入真实0", "一次独立补充合计",
                         "不并入、不覆盖ES、EI或ET", "非有限值", "ERROR"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        formal = self.text("formal_calculation_append_record")
        report = self.text("read_record_render_word")
        self.assertIn("另列一次冻结合计", formal)
        self.assertIn("不重新计算", report)
        self.assertIn("旧记录无该字段", report)
        self.assertIn("不补造0", report)

    def test_material_reminders_and_iapws_candidate_boundary(self):
        vector007 = self.vector("TV-CAR-POL-007")
        for expected in ("必要数值完整", "检测编号、合同附件和长说明全空",
                         "计算型Word可继续", "不称报告全文已核验", "只读不现场重算"):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector007)
        formal = self.text("formal_calculation_append_record")
        report = self.text("read_record_render_word")
        self.assertIn("证明/附件缺失或尚未审核只产生提醒", formal)
        self.assertIn("单位/量纲、数量基准、选定方法及参数库身份", formal)
        self.assertIn("不声称报告全文已核验", report)

        vector011 = self.vector("TV-CAR-POL-011")
        vector012 = self.vector("TV-CAR-POL-012")
        self.assertIn("不用旧矩形内插1505.75", vector011)
        self.assertIn("仍.308tCO₂", vector012)
        steam = self.text("resolve_steam_enthalpy")
        self.assertIn("已声明状态的外购蒸汽", steam)
        for expected in ("iapws.IAPWS97", "IAPWS97有效域", "压力基准", "不猜值", "不外推",
                         "候选", "C.4/C.5", "不回退旧表", "合法已知焓", "辅助失败",
                         "不实现或安装", "物性数值子配置", "固定依赖版本", "独立数值参照",
                         "不声称生产数值Profile/Conformance已完成"):
            with self.subTest(expected=expected):
                self.assertIn(expected, steam)


if __name__ == "__main__":
    unittest.main()
