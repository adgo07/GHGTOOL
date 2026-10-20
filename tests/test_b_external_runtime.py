"""Issue016独立预期、正式Record、payload与封套身份回归。"""
from dataclasses import replace
from decimal import Decimal, localcontext, ROUND_DOWN, ROUND_HALF_UP
import json
import unittest
from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.standards.carbon_material_external_co2 import ExternalCO2Input, evaluate_external_co2_supplement
from packages.standards.carbon_material import CarbonMaterialCalculator
from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.persistence import InMemoryRecordRepository
from packages.application import carbon_material_input_codec as industry
from packages.application import canonical_input_codec as envelope
from tests.test_b1_fuel_lifecycle import fuel_input

PROFILE='GHGTOOL_CARBON_DECIMAL40_CURRENT'
def evaluate(value,**changes):
    options=dict(carbon_total_tco2=Decimal('100'),carbon_complete=True,policy=DecimalPolicy(),numeric_profile_id=PROFILE)
    options.update(changes)
    return evaluate_external_co2_supplement(value,**options)

class ExternalRuntimeTests(unittest.TestCase):
    def test_independent_state_matrix_and_disabled_invalid_drafts(self):
        cases=[(None,'HISTORICAL_NOT_RECORDED',None),
               (ExternalCO2Input(False,'bad',unit='tCO2e'),'NOT_INCLUDED',None),
               (ExternalCO2Input(True,None),'PENDING',None),
               (ExternalCO2Input(True,'  '),'PENDING',None),
               (ExternalCO2Input(True,'0'),'COMPLETED_ZERO','100'),
               (ExternalCO2Input(True,'20'),'COMPLETED_POSITIVE','120')]
        for value,status,total in cases:
            with self.subTest(status=status):
                result=evaluate(value)
                self.assertEqual(result['status'],status)
                self.assertEqual(None if result['supplementary_total_tco2'] is None else Decimal(result['supplementary_total_tco2']),None if total is None else Decimal(total))
                self.assertEqual(result['original_et_tco2'],'100')
                self.assertFalse(result['external_calculation_verified'])
                self.assertFalse(result['enterprise_completeness_verified'])

    def test_enabled_invalid_values_units_and_known_facts_block(self):
        for raw in ('-1','NaN','Infinity','-Infinity','abc','1_000','1,000'):
            with self.subTest(raw=raw),self.assertRaises(DomainValidationError):evaluate(ExternalCO2Input(True,raw))
        for unit in ('tC','tCO2e','kgCO2',''):
            with self.subTest(unit=unit),self.assertRaises(DomainValidationError):evaluate(ExternalCO2Input(True,'20',unit=unit))
        for fact in ('known_scope_violation','known_period_mismatch','known_previously_counted'):
            with self.subTest(fact=fact),self.assertRaises(DomainValidationError):evaluate(ExternalCO2Input(True,None,**{fact:True}))

    def test_declared_profile_full_precision_and_ambient_independence(self):
        et=Decimal('100.1234567890123456789012345678901234567')
        ext=ExternalCO2Input(True,'0.0000000000000000000000000000000000001')
        for precision in (6,17,60):
            with localcontext() as context:
                context.prec=precision;context.rounding=ROUND_DOWN
                result=evaluate(ext,carbon_total_tco2=et)
            self.assertEqual(result['original_et_tco2'],str(et))
            self.assertEqual(Decimal(result['supplementary_total_tco2']),Decimal('100.1234567890123456789012345678901234568'))
        with self.assertRaises(DomainValidationError):evaluate(ext,policy=DecimalPolicy(precision=50))

    def test_partial_core_and_pending_are_independent_dimensions(self):
        formed=evaluate(ExternalCO2Input(True,'20'),carbon_complete=False)
        pending=evaluate(ExternalCO2Input(True,None),carbon_complete=False)
        self.assertEqual(formed['status'],'COMPLETED_POSITIVE')
        self.assertEqual(formed['supplementary_total_tco2'],'120')
        self.assertFalse(formed['core_coverage_complete'])
        self.assertFalse(formed['enterprise_completeness_verified'])
        self.assertEqual(pending['status'],'PENDING')
        self.assertIsNone(pending['supplementary_total_tco2'])

    def test_formal_original_et_unchanged_add_once_and_append_each_click(self):
        store=InMemoryRecordRepository();service=CarbonAccountingUseCase(CarbonMaterialCalculator(),store)
        # Independent governing formula under the declared40-digit operation order.
        with localcontext() as reference:
            reference.prec=40;reference.rounding=ROUND_HALF_UP
            expected_et=Decimal('10')*Decimal('8')*Decimal('.03')*Decimal('.98')*(Decimal('44')/Decimal('12'))
            expected_sum=expected_et+Decimal('20')
        value=replace(fuel_input(),external_co2=ExternalCO2Input(True,'20','其他已核算活动'))
        for count in (1,2):
            result=service.calculate(value)
            self.assertTrue(result.successful,result.problems)
            self.assertEqual(result.result.total_amount,expected_et)
            self.assertEqual(len(store.list_all()),count)
            node=json.loads(result.evidence.trace_snapshot_json)['software_supplement']
            self.assertEqual(Decimal(node['original_et_tco2']),expected_et)
            self.assertEqual(Decimal(node['supplementary_total_tco2']),expected_sum)
            self.assertFalse(any(line.emission_source_id=='CAR-SUP-OTHER-ACTIVITY-CO2' for line in result.result.lines))
        failed=service.calculate(replace(value,external_co2=ExternalCO2Input(True,'-1')))
        self.assertFalse(failed.successful)
        self.assertEqual(len(store.list_all()),2)
        self.assertTrue(any(p.code=='CAR-VAL-EXTERNAL-CO2-INPUT' for p in failed.problems))

    def test_activity_and_transport_declarations_do_not_block_or_clear(self):
        for changes in ({'other_activity_present':True},{'transport_present':True}):
            value=replace(fuel_input(),**changes)
            result=CarbonMaterialCalculator().calculate(value)
            self.assertTrue(result.successful,result.problems)
            self.assertTrue(any(p.code=='CAR-VAL-OTHER-STANDARD' and p.level.value=='WARNING' for p in result.problems))
            self.assertTrue(getattr(result.input,next(iter(changes))))

    def test_actual_partial_fume_and_external_status_are_frozen_separately(self):
        from tests import test_b_fume_chain as chain, test_b_fume_segments as fixtures
        with localcontext() as reference:
            reference.prec=40;reference.rounding=ROUND_HALF_UP
            expected_et=Decimal('1000')*1000*40*Decimal('.02')*1*1*24*(Decimal(44)/12)*Decimal('1e-9')
            expected_sum=expected_et+Decimal(20)
        for raw,status,total in [('20','COMPLETED_POSITIVE',expected_sum),(None,'PENDING',None)]:
            store=InMemoryRecordRepository()
            result=CarbonAccountingUseCase(CarbonMaterialCalculator(),store).calculate(chain.payload(fixtures.segment(),external_co2=ExternalCO2Input(True,raw)))
            self.assertTrue(result.successful,result.problems)
            self.assertEqual(result.result.total_amount,expected_et)
            node=json.loads(result.evidence.trace_snapshot_json)['software_supplement']
            self.assertFalse(node['core_coverage_complete']);self.assertEqual(node['status'],status)
            self.assertEqual(None if node['supplementary_total_tco2'] is None else Decimal(node['supplementary_total_tco2']),total)
            self.assertFalse(node['enterprise_completeness_verified'])

    def test_payload6_envelope2_legacy_missing_and_disabled_draft_roundtrip(self):
        value=replace(fuel_input(),external_co2=ExternalCO2Input(False,'NaN','草稿',unit='tC'))
        text=envelope.encode_canonical_input(value);document=json.loads(text)
        self.assertEqual((document['version'],document['input_version'],document['payload']['version']),(2,6,6))
        self.assertEqual(envelope.decode_canonical_input(text),value)
        legacy=json.loads(industry.encode_canonical_input(value));legacy['value']['fields'].pop('external_co2')
        for version in (1,2,3,4,5):
            legacy['version']=version
            restored=industry.decode_canonical_input(json.dumps(legacy))
            self.assertIsNone(restored.external_co2)
            self.assertIsNone(industry.decode_canonical_input(industry.encode_canonical_input(restored)).external_co2)
        document['input_version']=5
        with self.assertRaises(envelope.CanonicalInputCodecError):envelope.decode_canonical_input(json.dumps(document))
        bad=json.loads(industry.encode_canonical_input(value));bad['version']=5
        with self.assertRaises(industry.CanonicalInputCodecError):industry.decode_canonical_input(json.dumps(bad))
