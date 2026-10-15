"""Independent expectations from approved V1.2 and actual channel/unit consumers."""
import ast
import json
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from openpyxl import load_workbook
from packages.application.business_rules_candidate import load_bundle, CandidateBundleError
from packages.core.decimal_policy import DecimalPolicy
from packages.core.units import UnitService
from packages.standards.carbon_material import HeatInput
from packages.standards.carbon_material_normalization import MaterialInputLine, MaterialRole, normalize_material_inputs
from packages.ui.field_specs import FIELD_SPECS, FieldDataType

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data-source/carbon_accounting/business-rules'

class CandidateRevisionExpectations(unittest.TestCase):
    def documents(self):
        return [json.loads((SOURCE/p).read_text(encoding='utf-8')) for p in
                ('common/gbt_32150_2025.json','standards/gbt_32151_34_2024.json','software_policy.json')]

    def test_same_identity_target_preserves_confirmed_values_and_separates_old_behavior(self):
        software=self.documents()[2]
        operations={o['operation_id']:o for o in software['operations']}
        same=operations['confirm_same_catalog_identity']
        preserved='\n'.join(same['preserves'])
        self.assertRegex(preserved,r'(已确认|confirmed).*(实测|measured)')
        self.assertRegex(preserved,r'(来源|source)')
        self.assertRegex(preserved,r'(计量|basis|路径)')
        self.assertNotIn('重置默认参数/计量方式','\n'.join(same['changes']))
        self.assertTrue(any('APPROVED_IMPLEMENTATION_V1_2' in b and ('7.1' in b or '§7' in b) for b in same['basis']))
        switch=operations['switch_catalog_identity']
        text='\n'.join(switch['changes']+switch['confirmation']+[switch['action']])
        self.assertRegex(text,r'(初始化|重新确定|default|initialize)')
        self.assertRegex(text,r'离开.*(重选|重新选择)|重新选择.*离开')
        for op_id in ('restore_without_default_init','excel_preview'):
            op=operations[op_id]
            text='\n'.join(op['changes']+op['preserves']+[op['action']])
            self.assertRegex(text,r'(不|禁止|不得).*(初始化|默认)|(restore|import).*(without|no).*init')
        corrections=[c for c in software['changes'] if 'same' in str(c).lower() or '同一身份' in str(c) or '同身份' in str(c)]
        self.assertTrue(corrections,'同身份重置旧事实与批准目标应有具体差异记录')

    def test_source_enablement_is_business_state_and_views_have_no_toggle_consumer(self):
        ops={o['operation_id']:o for o in self.documents()[2]['operations']}
        toggle=ops['toggle_emission_source'];view=ops['presentation_only_views']
        changes='\n'.join(toggle['changes']);invalidates='\n'.join(toggle['invalidates'])
        self.assertIn('INVOLVED',changes);self.assertIn('NOT_INVOLVED',changes)
        self.assertRegex(changes,r'(dirty|变脏|输入脏|标脏)')
        self.assertRegex(invalidates,r'(结果|result)')
        self.assertRegex('\n'.join(toggle['preserves']),r'(草稿|draft)')
        self.assertTrue(any('_toggle_source_group' in c for c in toggle['basis']))
        self.assertFalse(any('_toggle_source_group' in c for c in view['basis']))
        tree=ast.parse((ROOT/'packages/ui/carbon_material_page.py').read_text(encoding='utf-8'))
        method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_toggle_source_group')
        self.assertTrue(any(isinstance(n,ast.Attribute) and n.attr=='_mark_input_dirty' for n in ast.walk(method)))
        self.assertTrue({'INVOLVED','NOT_INVOLVED'} <= {n.attr for n in ast.walk(method) if isinstance(n,ast.Attribute)})

    def test_channel_units_match_percent_inputs_and_raw_material_stage(self):
        fields={f['id']:f for d in self.documents() for f in d['fields']}
        for field_id in ('fuel.oxidation','fgd.ratio','fgd.conversion','material.fixed_carbon','material.volatile_matter'):
            f=fields[field_id]
            for p in f['channel_projections']:
                if p['channel'] in {'GUI','EXCEL'}:
                    with self.subTest(field=field_id,binding=p['binding']):self.assertEqual(p['unit'],'%')
            if field_id.startswith('material.'):
                raw=[p for p in f['channel_projections'] if p['binding'].startswith('domain:MaterialInputLine.')]
                self.assertTrue(raw)
                self.assertTrue(all(p['unit']=='%' for p in raw),'原始物料证据入口仍是百分数')
            else:
                self.assertEqual(f['unit'],'ratio')
                self.assertTrue(all(p['unit']=='ratio' for p in f['channel_projections'] if p['channel']=='DOMAIN'))
        for f in fields.values():
            for p in f['channel_projections']:
                key=p['binding'].removeprefix('field_specs:')
                if p['channel']=='GUI' and key in FIELD_SPECS and FIELD_SPECS[key].data_type is FieldDataType.PERCENTAGE:
                    with self.subTest(field=f['id'],binding=p['binding']):self.assertEqual(p['unit'],'%')
        for field_id in ('heat_amount','exported_heat_amount'):
            self.assertTrue(any(p['channel']=='GUI' and p['unit']=='t' for p in fields[field_id]['channel_projections']),
                '实际蒸汽录入为t，不能把Calculator归一化kg当成当前控件单位')
        for field_id,actual_consumers in (
                ('fuel_activity',('_FuelRow','FuelInput','AppendixBWorkbookImporter')),
                ('electricity.amount',('_UnifiedEnergyRow','ElectricityConsumptionDetail','AppendixBWorkbookImporter')),
                ('exported_electricity_amount',('_UnifiedEnergyRow','ElectricityOutputLine','AppendixBWorkbookImporter'))):
            consumers='\n'.join(fields[field_id]['consumers'])
            for consumer in actual_consumers:self.assertIn(consumer,consumers)
        page_tree=ast.parse((ROOT/'packages/ui/carbon_material_page.py').read_text(encoding='utf-8'))
        self.assertTrue({'_FuelRow','_UnifiedEnergyRow'} <= {
            n.name for n in page_tree.body if isinstance(n,ast.ClassDef)})
        for f in fields.values():
            for projection in f['channel_projections']:
                self.assertNotIn('CarbonMaterialAccountingPage._FuelRow',projection['binding'])
                self.assertNotIn('CarbonMaterialAccountingPage._UnifiedEnergyRow',projection['binding'])
        fuel=fields['fuel_activity']['channel_projections']
        self.assertTrue({'GUI','EXCEL','DOMAIN'} <= {p['channel'] for p in fuel})
        self.assertTrue(any(p['binding']=='domain:FuelInput.activity' for p in fuel))
        self.assertTrue(any(p['channel']=='GUI' and '_FuelRow.activity' in p['binding'] for p in fuel))
        for field_id,domain_binding in (
                ('electricity.amount','domain:ElectricityConsumptionDetail.electricity_amount'),
                ('exported_electricity_amount','domain:ElectricityOutputLine.amount')):
            projections=fields[field_id]['channel_projections']
            self.assertTrue({'GUI','EXCEL','DOMAIN'} <= {p['channel'] for p in projections})
            self.assertTrue(any(p['binding']==domain_binding and p['unit']=='MWh' for p in projections))
            self.assertTrue(any(p['channel']=='GUI' and '_UnifiedEnergyRow.amount' in p['binding']
                                and p['unit']=='MWh' for p in projections))
            self.assertTrue(all(p['unit']=='MWh' for p in projections))
        w=load_workbook(ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v1.xlsx',read_only=True)
        try:
            for sheet,cell in [('B.2','H3'),('B.7','D2'),('B.7','F2')]:self.assertIn('%',w[sheet][cell].value)
        finally:w.close()

    def test_existing_unit_and_material_services_preserve_raw_inputs(self):
        policy=DecimalPolicy(precision=40);units=UnitService(policy)
        with localcontext() as ctx:
            ctx.prec=4
            for display,ratio in [('96','0.96'),('90','0.90'),('95','0.95')]:
                self.assertEqual(units.convert(display,'percent','ratio'),Decimal(ratio))
                self.assertEqual(units.convert(ratio,'ratio','percent'),Decimal(display))
            line=MaterialInputLine('raw',MaterialRole.CALCINATION_FEED,'原料','10',fixed_carbon_percent='80',volatile_matter_percent='10')
            zero_product=MaterialInputLine('product',MaterialRole.CALCINED_PRODUCT,'煅后料','0')
            normalized=normalize_material_inputs('calcination',[line,zero_product],policy=policy)
            self.assertFalse(normalized.problems)
            self.assertEqual(normalized.value('wfc'),Decimal('0.8'))
            self.assertEqual(normalized.value('wvar'),Decimal('0.1'))
            self.assertEqual(line.fixed_carbon_percent,'80');self.assertEqual(line.volatile_matter_percent,'10')
            heat=HeatInput('steam','1.25',enthalpy='2700',unit='t')
            self.assertEqual(heat.amount.unit,'t');self.assertEqual(heat.amount.value,Decimal('1.25'))
            self.assertEqual(units.convert(heat.amount.value,heat.amount.unit,'kg'),Decimal('1250'))
            self.assertEqual(heat.amount.value,Decimal('1.25'))
            self.assertEqual(units.convert('2.5','MWh','MWh'),Decimal('2.5'))

    def test_explicit_default_source_initializes_only_fresh_context(self):
        bundle=load_bundle([SOURCE/p for p in ('common/gbt_32150_2025.json',
            'standards/gbt_32151_34_2024.json','software_policy.json')])
        def initialize(field,context):
            result=bundle.initialize_context(context,field_ids=[field],event='NEW_SELECTION')
            self.assertEqual(len(result['outcomes']),1)
            return next(iter(result['outcomes'].values()))
        catalog=dict(origin='CATALOG',binding_status='VERIFIED',
            parameter_id='natural_gas_oxidation_rate',
            binding_id='binding-natural_gas_oxidation_rate_gbt32151_34_c1')
        fresh=initialize('fuel.oxidation',catalog)
        self.assertEqual(fresh['initialization_status'],'INITIALIZED')
        self.assertEqual(fresh['selected_business_source'],'STANDARD_DEFAULT')
        self.assertEqual(fresh['application']['default']['value'],
            {'state':'BINDING','parameter_id':'natural_gas_oxidation_rate'})
        self.assertEqual(fresh['application']['locking']['value']['state'],'LOCKED')
        self.assertNotIn('business_source',catalog,'readonly initialization cannot mutate caller evidence')
        custom=dict(origin='CUSTOM',binding_status='ABSENT')
        for field in ('fuel.lhv','fuel.fch','fgd.factor'):
            with self.subTest(field=field):
                out=initialize(field,custom)
                self.assertEqual(out['initialization_status'],'NO_AUTOMATIC_SOURCE')
                self.assertIsNone(out['selected_business_source'])
                self.assertNotIn('business_source',out['effective_context'])
        for field in ('fuel.oxidation','fuel.direct_carbon','material.fixed_carbon','material.volatile_matter'):
            with self.subTest(field=field):
                out=initialize(field,custom)
                self.assertEqual(out['selected_business_source'],'MEASURED')
                self.assertEqual(out['application']['default']['value'],{'state':'NONE'})
        single=initialize('fgd.ratio',dict(binding_status='VERIFIED',carbonate_component_count=1,
            parameter_id='car-par-p04b-i',binding_id='binding-fgd_carbonate_content_default_gbt32151_34_2024'))
        self.assertEqual(single['selected_business_source'],'STANDARD_DEFAULT')
        multi=initialize('fgd.ratio',dict(binding_status='ABSENT',carbonate_component_count=2))
        self.assertEqual(multi['selected_business_source'],'MEASURED')
        self.assertEqual(multi['application']['default']['value'],{'state':'NONE'})
        preserved=initialize('fuel.oxidation',dict(catalog,business_source='MEASURED'))
        self.assertEqual(preserved['initialization_status'],'PRESERVED')
        self.assertEqual(preserved['selected_business_source'],'MEASURED')
        self.assertEqual(preserved['application']['default']['value'],{'state':'NONE'})
        self.assertEqual(preserved['application']['locking']['value']['state'],'EDITABLE')
        for event in ('CONFIRMED_IDENTITY_CHANGE','RESELECT_AFTER_LEAVE'):
            with self.subTest(fresh_target_event=event):
                result=bundle.initialize_context(catalog,field_ids=['fuel.oxidation'],event=event)
                self.assertEqual(next(iter(result['outcomes'].values()))['selected_business_source'],'STANDARD_DEFAULT')
            stale=dict(catalog,business_source='MEASURED');before=dict(stale)
            with self.subTest(stale_event=event),self.assertRaises(CandidateBundleError):
                bundle.initialize_context(stale,field_ids=['fuel.oxidation'],event=event)
            self.assertEqual(stale,before,'unsafe stale context must be rejected without mutation')
        for event in ('RESTORE','IMPORT','CONFIRM_SAME_IDENTITY','BLUR','REFRESH_CANDIDATES'):
            with self.subTest(event=event),self.assertRaises(CandidateBundleError):
                bundle.initialize_context(catalog,field_ids=['fuel.oxidation'],event=event)
