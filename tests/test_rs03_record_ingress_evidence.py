"""Formal records freeze Excel ingress evidence independently of mutable projects."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from packages.application.carbon_accounting import CarbonAccountingUseCase, RecordPersistenceError
from packages.persistence.records_repository import SQLiteRecordRepository
from tests.test_carbon_accounting_usecase import _QueueCalculator, _outcome

class RecordIngressEvidenceTests(unittest.TestCase):
    def test_ingress_evidence_is_frozen_and_gui_default_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRecordRepository(Path(directory)/"records.sqlite")
            evidence={"workbook_sha256":"a"*64,"numeric_cells":[{"sheet":"B.2 化石燃料","cell":"D6","raw_value":"1.2345678901234567890123456789","normalized_value":"1.2345678901234567890123456789"}]}
            original=_outcome("excel")
            service=CarbonAccountingUseCase(_QueueCalculator(original,_outcome("gui")),repo)
            excel=service.calculate(original.input,ingress_provenance=evidence)
            evidence["numeric_cells"][0]["raw_value"]="changed"
            frozen=repo.get_raw_input_snapshot(excel.record.record_id)
            self.assertEqual(frozen["ingress_provenance"]["numeric_cells"][0]["raw_value"],"1.2345678901234567890123456789")
            self.assertEqual(frozen["source_text"],"raw-excel")
            self.assertNotIn("ingress_provenance",original.evidence.raw_input_snapshot_json)
            gui=service.calculate(original.input)
            self.assertNotIn("ingress_provenance",repo.get_raw_input_snapshot(gui.record.record_id))
            self.assertEqual(len(repo.list_all()),2)

    def test_invalid_ingress_never_calls_calculator_or_writes_record(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRecordRepository(Path(directory)/"records.sqlite")
            calc=_QueueCalculator(_outcome("invalid"))
            service=CarbonAccountingUseCase(calc,repo)
            for payload in ({"number":1.25},{"number":Decimal("1.25")},{1:"non-string key"},{"number":float("nan")},{"tuple":("1",)}):
                with self.subTest(payload=payload),self.assertRaises(ValueError):
                    service.calculate(object(),ingress_provenance=payload)
            self.assertEqual(calc.calls,[])
            self.assertEqual(repo.list_all(),())

    def test_ingress_cannot_overwrite_existing_raw_input_key(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRecordRepository(Path(directory)/"records.sqlite")
            outcome=_outcome("collision")
            outcome=replace(outcome,evidence=replace(outcome.evidence,raw_input_snapshot_json='{"ingress_provenance":{"original":"true"}}'))
            service=CarbonAccountingUseCase(_QueueCalculator(outcome),repo)
            with self.assertRaises(RecordPersistenceError):
                service.calculate(object(),ingress_provenance={"new":"true"})
            self.assertEqual(repo.list_all(),())
