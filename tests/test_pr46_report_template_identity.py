"""Acceptance checks for frozen input-template identity in Word report metadata."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from packages.application.reporting import build_saved_record_report
from packages.persistence.catalog_repository import SQLiteCatalogRepository
from packages.persistence.records_repository import _record_from_payload
from packages.standards.carbon_material import CarbonMaterialCalculator
from scripts.rpt02_acceptance_samples import build_acceptance_case


class _FrozenRecordRepository:
    """Read-only snapshot stand-in matching the report repository surface."""

    def __init__(
        self,
        record,
        *,
        raw_input,
        trace=None,
        provenance=None,
        reporting=None,
        qualification=None,
        schema_version=1,
    ):
        self.record = record
        self._snapshots = {
            "raw": deepcopy(raw_input),
            "trace": deepcopy(trace or {}),
            "provenance": deepcopy(provenance or {}),
            "reporting": deepcopy(reporting or {}),
            "qualification": deepcopy(qualification or {}),
        }
        self.schema_version = schema_version

    def _read(self, key, record_id):
        if record_id != self.record.record_id:
            raise AssertionError("report requested another Record")
        return deepcopy(self._snapshots[key])

    def get_raw_input_snapshot(self, record_id):
        return self._read("raw", record_id)

    def get_trace_snapshot(self, record_id):
        return self._read("trace", record_id)

    def get_provenance_snapshot(self, record_id):
        return self._read("provenance", record_id)

    def get_reporting_snapshot(self, record_id):
        return self._read("reporting", record_id)

    def get_report_qualification(self, record_id):
        return self._read("qualification", record_id)

    def get_snapshot_schema_version(self, record_id):
        if record_id != self.record.record_id:
            raise AssertionError("report requested another Record")
        return self.schema_version


def _report_from_frozen_record(repository, record):
    with (
        patch.object(
            CarbonMaterialCalculator,
            "calculate",
            side_effect=AssertionError("historical report must not recalculate"),
        ),
        patch.object(
            SQLiteCatalogRepository,
            "list_parameters",
            side_effect=AssertionError("historical report must not query Catalog"),
        ),
        patch.object(
            SQLiteCatalogRepository,
            "list_factors",
            side_effect=AssertionError("historical report must not query Catalog"),
        ),
    ):
        return build_saved_record_report(repository, record)


def _synthetic_record():
    record, raw, trace, provenance, reporting, qualification = build_acceptance_case("GUI")
    return record, raw, trace, provenance, reporting, qualification


class ReportTemplateIdentityTests(unittest.TestCase):
    def test_excel_versions_follow_frozen_provenance_without_reusing_workbook_hash(self):
        record, base_raw, trace, provenance, reporting, qualification = _synthetic_record()
        for version, marker in (("2.3.0", "a"), ("2.2.0", "b"), ("2.1.0", "c")):
            with self.subTest(version=version):
                source_workbook_sha256 = marker * 64
                raw = deepcopy(base_raw)
                raw["ingress_provenance"] = {
                    "source": "EXCEL_APPENDIX_B",
                    "workbook": {
                        "sha256": source_workbook_sha256,
                        "template_id": "GHGTOOL_GBT_32151_34_2024_APPENDIX_B",
                        "template_version": version,
                    },
                }
                repository = _FrozenRecordRepository(
                    record,
                    raw_input=raw,
                    trace=trace,
                    provenance=provenance,
                    reporting=reporting,
                    qualification=qualification,
                )

                model = _report_from_frozen_record(repository, record)

                self.assertEqual(model.input_template_version, version)
                # WorkbookProvenance freezes the user-filled workbook digest,
                # not a digest of the approved template master.
                self.assertEqual(model.input_template_sha256, "")
                self.assertNotEqual(model.input_template_sha256, source_workbook_sha256)
                self.assertEqual(repository.get_raw_input_snapshot(record.record_id), raw)

    def test_historical_r2_record_keeps_its_frozen_version_without_fabricated_master_hash(self):
        bundle_path = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "rpt02"
            / "samples"
            / "records-and-snapshots.json"
        )
        bundle_bytes_before = bundle_path.read_bytes()
        bundle = json.loads(bundle_bytes_before)
        entry = next(
            item
            for item in bundle["records"]
            if item["origin"] == "EXCEL_R2_PREVIEW_TO_FORMAL_USE_CASE"
        )
        snapshots = entry["snapshots"]
        record = _record_from_payload(entry["record"])
        raw = snapshots["raw_input"]
        frozen_raw_before = deepcopy(raw)
        frozen_record_before = asdict(record)
        ingress = raw["ingress_provenance"]
        self.assertEqual(ingress["source"], "EXCEL_R2")
        self.assertEqual(ingress["workbook"]["template_version"], "2.0.0")
        workbook_sha256 = ingress["workbook"]["sha256"]
        repository = _FrozenRecordRepository(
            record,
            raw_input=raw,
            trace=snapshots["trace"],
            provenance=snapshots["provenance"],
            reporting=snapshots["reporting"],
            qualification=snapshots["qualification"],
        )

        model = _report_from_frozen_record(repository, record)

        self.assertEqual(model.input_template_version, "2.0.0")
        self.assertEqual(model.input_template_sha256, "")
        self.assertNotEqual(model.input_template_sha256, workbook_sha256)
        self.assertEqual(repository.get_raw_input_snapshot(record.record_id), frozen_raw_before)
        self.assertEqual(asdict(record), frozen_record_before)
        self.assertEqual(bundle_path.read_bytes(), bundle_bytes_before)

    def test_gui_r2_without_workbook_details_and_legacy_records_emit_no_template_identity(self):
        record, base_raw, trace, provenance, reporting, qualification = _synthetic_record()
        cases = {
            "gui": deepcopy(base_raw),
            "r2-without-workbook": {
                **deepcopy(base_raw),
                "ingress_provenance": {"source": "EXCEL_R2"},
            },
            "legacy-without-ingress": {},
        }
        for name, raw in cases.items():
            with self.subTest(case=name):
                repository = _FrozenRecordRepository(
                    record,
                    raw_input=raw,
                    trace=trace,
                    provenance=provenance,
                    reporting=reporting,
                    qualification=qualification,
                    schema_version=0 if name == "legacy-without-ingress" else 1,
                )

                model = _report_from_frozen_record(repository, record)

                self.assertEqual(model.input_template_version, "")
                self.assertEqual(model.input_template_sha256, "")
                self.assertEqual(repository.get_raw_input_snapshot(record.record_id), raw)


if __name__ == "__main__":
    unittest.main()
