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
        self.assertEqual(self.policy["revision"], "adoption-2026-10-17-fuel-power1")
        self.assertEqual(self.standard["revision"], "adoption-2026-10-17-fuel-power1")
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

    def test_direct_fuel_path_uses_field_qualification_without_double_heat_conversion(self):
        operation = self.text("change_fuel_path_unit")
        for expected in (
            "fuel.direct_carbon", "source_qualification", "单位质量/体积直接含碳量",
            "不重复乘低位发热量或FCh",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, operation)
        self.assertNotIn("DIRECT路径使用实测直接含碳量", operation)

        field = next(item for item in self.standard["fields"] if item["id"] == "fuel.direct_carbon")
        self.assertEqual(field["unit"], "MASS: tC/t; VOLUME: tC/10^4Nm3")
        qualification = next(
            item for item in self.standard["policies"]
            if item["id"] == field["source_qualification"]["policy_id"]
        )
        allowed_by_origin = {
            branch["when"]["tags"]["origin"]: set(branch["value"]["values"])
            for branch in qualification["branches"]
        }
        self.assertEqual(allowed_by_origin["CATALOG"], {"CALCULATED", "MEASURED"})
        self.assertEqual(allowed_by_origin["CUSTOM"], {"CALCULATED", "MEASURED"})
        self.assertEqual(allowed_by_origin["LEGACY_UNSPECIFIED"], {"MEASURED"})

    def test_source_switch_restores_scoped_draft_and_resolves_default_binding_explicitly(self):
        resolver = self.text("resolve_parameter_source")
        for expected in (
            "现有Resolver", "当前采用的标准/通则版本", "完整核算上下文", "真实适用绑定",
            "无适用绑定", "不借用其他对象", "不回填0",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, resolver)

        switch = self.text("switch_source_isolated_draft")
        for expected in (
            "同一参数对象、字段、单位和来源的有效草稿", "显式切回STANDARD_DEFAULT",
            "新对象初始化、同身份确认和RESTORE各按各自操作处理",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, switch)

        same_identity = self.text("confirm_same_catalog_identity")
        restore = self.text("restore_without_default_init")
        self.assertIn("不触发新建初始化", same_identity)
        self.assertIn("RESTORE不触发default_source或数值默认初始化", restore)

    def test_unconfirmed_name_requires_existing_confirm_or_cancel_before_calculation(self):
        edit = self.text("edit_name_draft")
        formal = self.text("formal_calculation_append_record")
        same_identity = self.text("confirm_same_catalog_identity")
        self.assertIn("不因每次按键", edit)
        self.assertIn("现有确认/取消交互", edit)
        self.assertIn("确认新身份后进入switch_catalog_identity", edit)
        self.assertIn("取消后仍显示并使用原已确认身份", edit)
        for expected in ("未确认名称草稿", "未决时不调用核算", "显示新名称却按旧身份"):
            with self.subTest(expected=expected):
                self.assertIn(expected, formal)
        self.assertIn("同身份确认不应用数值默认或default_source", same_identity)

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
        self.assertIn("正式Calculator实现与验收仍需后续独立完成", changes["review.change.calcination_role_carbon"]["pending"][0])
        vector = self.vector("TV-CAR-POL-016")
        for expected in ("WFC-C[CC]=.8", "WFC-C[UCC]=.4", "WFC-C[DU]=.25",
                         "226.8291666666666666666666666666666666667", "162.6625"):
            self.assertIn(expected, vector)

    def test_issue020_p04a_segments_separate_calculation_from_annual_coverage(self):
        text = self.text("aggregate_fume_monitoring_segments")
        for expected in (
            "CAR-FML-FUME-INCINERATION-001", "CAR-FLD-P04A-Q", "CAR-FLD-P04A-QVAR",
            "CAR-FLD-P04A-T", "同一烟气排放源实例", "同一计量边界", "监测段不得重叠",
            "T_i", "小时", "÷24", "归一一次", "×24", "适用于该段",
            "不同适用设备或排放源实例", "同时段", "分别计算并汇总", "不跨实例去重",
            "存在缺口", "仍可计算已覆盖段", "年度覆盖不完整", "不得默认为0",
            "不年化", "不外推", "不表述为标准新增公式",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        vector017 = self.vector("TV-CAR-POL-017")
        for expected in (".0704tCO₂", ".1408tCO₂", ".2112tCO₂", "不把未覆盖期默认为零"):
            self.assertIn(expected, vector017)
        vector018 = self.vector("TV-CAR-POL-018")
        for expected in (
            "完整覆盖", "空档", "重叠10d", "同期独立监测", "同实例/同边界重叠为ERROR",
            "仍可计算已覆盖段合计", "24h÷24=1d", "式(9)乘`24`一次",
            "不表示生产Calculator已接管",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, vector018)

        operation = self.standard_operations["aggregate_fume_monitoring_segments"]
        self.assertTrue(any("R11" in basis for basis in operation["basis"]))
        self.assertTrue({"TV-CAR-POL-017", "TV-CAR-POL-018"} <= set(operation["cases"]))

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
        for expected in ("同一企业汇总边界", "同一期间", "非负tCO₂", "纳入但留空时",
                         "补充合计保持待补", "不造0", "纳入真实0", "一次独立补充合计",
                         "不并入、不覆盖ES、EI或ET", "非有限值", "ERROR"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        formal = self.text("formal_calculation_append_record")
        report = self.text("read_record_render_word")
        self.assertIn("另列一次冻结合计", formal)
        self.assertIn("不重新计算", report)
        self.assertIn("旧记录无该字段", report)
        self.assertIn("不补造0", report)
        confirmation = "\n".join(self.operations["capture_external_co2_supplement"]["confirmation"])
        self.assertIn("空白时只将该补充合计标为待补", confirmation)
        self.assertIn("不构成炭素部分核算的缺失必需值", confirmation)
        self.assertIn("核心炭素输入自身缺少必需值/基准时仍为ERROR", confirmation)
        self.assertIn("补充实际填写后", confirmation)
        self.assertNotIn("纳入但空白仍为ERROR", confirmation)

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
