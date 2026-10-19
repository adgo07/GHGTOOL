"""PR52-F01: formal immutable Record -> shared B.9 -> Word unit semantics."""
from contextlib import ExitStack
from dataclasses import replace
from decimal import Decimal, localcontext
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.application.reporting.model import build_report_model
from packages.infrastructure.reporting import render_report_docx
from packages.persistence import SQLiteRecordRepository
from packages.standards.carbon_material import (
    CarbonMaterialCalculator, EmissionSourceState, EmissionSourceStatus,
    InputValue, SOURCE_EXPORTED_HEAT, SteamKind,
)
from tests import test_b_heat_runtime as heat_runtime
from tests.test_b_heat_runtime import heat, input_with


class HeatReportUnitTests(unittest.TestCase):
    def setUp(self):
        heat_runtime.HeatRuntimeTests.setUp(self)
        self.database = self.root / 'records.sqlite'
        self.records = SQLiteRecordRepository(self.database)
        self.formal = CarbonAccountingUseCase(self.calc, self.records)

    tearDown = heat_runtime.HeatRuntimeTests.tearDown

    def save(self, pressure, temperature, *, saturated=False, known=False):
        line = heat(amount='1', enthalpy='2800' if known else None,
                    manual_enthalpy=known,
                    steam_kind=SteamKind.SATURATED if saturated else SteamKind.SUPERHEATED,
                    pressure_mpa=pressure, temperature_c=temperature)
        value = input_with(line)
        value = replace(value, exported_heat=(replace(line,line_id='exported',amount=InputValue('.5','t')),),
            source_states=(*value.source_states,EmissionSourceState(SOURCE_EXPORTED_HEAT,EmissionSourceStatus.INVOLVED)))
        result = self.formal.calculate(value)
        self.assertTrue(result.successful,result.problems)
        return result.record.record_id

    def report(self, rid, *, raw=None, record=None):
        import packages.standards.carbon_material_steam_if97 as physics
        before = self.database.read_bytes()
        original = self.records.get_raw_input_snapshot(rid)
        trace = self.records.get_trace_snapshot(rid)
        with ExitStack() as stack:
            stack.enter_context(patch.object(CarbonMaterialCalculator,'calculate',side_effect=AssertionError('frozen calculator')))
            stack.enter_context(patch.object(self.resolver,'resolve',side_effect=AssertionError('frozen resolver')))
            stack.enter_context(patch.object(physics,'_runtime',side_effect=AssertionError('frozen property runtime')))
            model=build_report_model(record or self.records.get(rid),raw_input_snapshot=original if raw is None else raw,
                trace_snapshot=trace,provenance_snapshot=self.records.get_provenance_snapshot(rid),
                reporting_snapshot=self.records.get_reporting_snapshot(rid),report_qualification=self.records.get_report_qualification(rid))
            word=render_report_docx(model)
        self.assertEqual(self.database.read_bytes(),before)
        self.assertEqual(self.records.get_raw_input_snapshot(rid),original)
        self.assertEqual(self.records.get_trace_snapshot(rid),trace)
        table=next(s for s in model.sections if s.section_id=='b9').tables[0]
        headers=''.join(c.value for row in table.header_rows for c in row.cells)
        self.assertIn('MPa',headers);self.assertIn('℃',headers)
        with ZipFile(BytesIO(word)) as z:xml=ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        word_table=next(t for t in xml.findall('.//w:tbl',ns) if '蒸汽压力' in ''.join(t.itertext()))
        word_rows=[[''.join(c.itertext()) for c in r.findall('w:tc',ns)] for r in word_table.findall('w:tr',ns)]
        return table,word_rows

    def test_formal_auto_unit_matrix_both_directions_shared_report_and_word(self):
        cases=[('.0035','MPa','26.85','C'),('3500','Pa','300','K'),
               ('3500','Pa','26.85','C'),('.0035','MPa','300','K'),
               ('.1','MPa',None,None),('100000','Pa',None,None)]
        for p,pu,t,tu in cases:
            with self.subTest(pressure_unit=pu,temperature_unit=tu):
                rid=self.save(InputValue(p,pu),InputValue(t,tu) if t else None,saturated=t is None)
                raw=self.records.get_raw_input_snapshot(rid)
                self.assertEqual(raw['purchased_heat'][0]['pressure_mpa']['unit'],pu)
                table,word_rows=self.report(rid)
                expected=('3.50E-3','26.85') if t else ('0.10','不适用')
                self.assertEqual(len(table.rows),2)
                for direction,row in zip(('购入','输出'),table.rows):
                    self.assertEqual(row.cells[0].value,direction)
                    self.assertEqual((row.cells[3].value,row.cells[4].value),expected)
                    word_row=next(r for r in word_rows if r[0]==direction)
                    self.assertEqual(tuple(word_row[3:5]),expected)

    def test_known_raw_explicit_units_convert_without_property_recalculation(self):
        rid=self.save(InputValue('3500','Pa'),InputValue('300','K'),known=True)
        for ambient in (6,17,60):
            with localcontext() as context:
                context.prec=ambient
                table,_=self.report(rid)
            self.assertEqual((table.rows[0].cells[3].value,table.rows[0].cells[4].value),('3.50E-3','26.85'))

    def test_missing_unknown_or_nonfinite_units_are_not_guessed(self):
        rid=self.save(InputValue('3500','Pa'),InputValue('300','K'),known=True)
        for unit in (None,'','psi'):
            with self.subTest(unit=unit):
                raw=json.loads(json.dumps(self.records.get_raw_input_snapshot(rid)))
                for collection in ('purchased_heat','exported_heat'):
                    for field in ('pressure_mpa','temperature_c'):
                        raw[collection][0][field]['unit']=unit
                table,_=self.report(rid,raw=raw)
                for row in table.rows:
                    self.assertIn('单位',row.cells[3].value)
                    self.assertIn('单位',row.cells[4].value)
        raw=json.loads(json.dumps(self.records.get_raw_input_snapshot(rid)))
        raw['purchased_heat'][0]['pressure_mpa']['value']='NaN'
        table,_=self.report(rid,raw=raw)
        self.assertEqual(table.rows[0].cells[3].value,'历史未记录')

    def test_pre_heat_record_display_path_is_preserved(self):
        rid=self.save(InputValue('.0035','MPa'),InputValue('26.85','C'),known=True)
        record=self.records.get(rid)
        record=replace(record,algorithm_version='CAR-SM01-2026-10-18-FUME.2',
            calculation_result=replace(record.calculation_result,algorithm_version='CAR-SM01-2026-10-18-FUME.2'))
        table,_=self.report(rid,record=record)
        self.assertEqual((table.rows[0].cells[3].value,table.rows[0].cells[4].value),('3.50E-3','26.85'))
