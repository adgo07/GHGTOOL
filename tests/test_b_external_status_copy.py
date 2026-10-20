"""源独立接验发现的状态提示：只消费冻结状态，不改变数值。"""
from copy import deepcopy
import unittest
from packages.application.reporting.software_supplement import software_supplement_display

class ExternalStatusCopyTests(unittest.TestCase):
    def test_frozen_status_controls_declaration_note_and_preserves_input(self):
        cases={
            'COMPLETED_ZERO':'外部值已按用户同边界、同期且原结果未计入的声明纳入。',
            'COMPLETED_POSITIVE':'外部值已按用户同边界、同期且原结果未计入的声明纳入。',
            'PENDING':'已选择同边界、同期且原结果未计入的声明；外部数值待补，补充合计尚未形成。',
            'NOT_INCLUDED':'本次未纳入外部补充，草稿不参与合计。',
            'HISTORICAL_NOT_RECORDED':'该历史输入未记录外部补充状态；不补造声明或纳入决定。',
        }
        for state,expected in cases.items():
            with self.subTest(state=state):
                trace={'software_supplement':{'status':state,'original_et_tco2':'100','amount_tco2':'0','supplementary_total_tco2':'100','core_coverage_complete':False}}
                original=deepcopy(trace);rows,notes=software_supplement_display(trace)
                self.assertEqual(notes[0],expected)
                self.assertIn('软件未核验外部计算及完整企业排放。',notes)
                self.assertIn('原炭素结果未证明完整监测覆盖',notes[-1])
                self.assertEqual(trace,original)
                if not state.startswith('COMPLETED_'):
                    self.assertNotIn('外部值已按',notes[0])
                    self.assertNotIn('声明纳入',notes[0])
                    self.assertNotIn('已纳入',str(rows))

    def test_historical_record_without_supplement_node_keeps_no_section(self):
        self.assertIsNone(software_supplement_display({}))
        self.assertIsNone(software_supplement_display(None))

if __name__=='__main__':unittest.main()
