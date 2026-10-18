"""用实际历史SQLite与已导出Word复核冻结正文；复制数据库，不改原证据。"""
from __future__ import annotations
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch
from zipfile import ZipFile
from packages.application.reporting.model import build_report_model
from packages.core.parameter_resolution import ParameterResolver
from packages.infrastructure.reporting import render_report_docx
from packages.persistence import SQLiteRecordRepository
from packages.standards.carbon_material import CarbonMaterialCalculator


def verify(records: Path, record_id: str, expected_docx: Path) -> dict:
    original_sha = sha256(records.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as directory:
        copy = Path(directory) / "records.sqlite"
        shutil.copy2(records, copy)
        repository = SQLiteRecordRepository(copy)
        count = len(repository.list_all())
        with patch.object(CarbonMaterialCalculator, "calculate", side_effect=AssertionError("历史禁止重算")), \
             patch.object(ParameterResolver, "resolve", side_effect=AssertionError("历史禁止回查Resolver")):
            record = repository.get(record_id)
            model = build_report_model(record,
                raw_input_snapshot=repository.get_raw_input_snapshot(record_id),
                trace_snapshot=repository.get_trace_snapshot(record_id),
                provenance_snapshot=repository.get_provenance_snapshot(record_id),
                reporting_snapshot=repository.get_reporting_snapshot(record_id),
                report_qualification=repository.get_report_qualification(record_id))
            with ZipFile(BytesIO(render_report_docx(model))) as archive:
                actual = archive.read("word/document.xml")
            with ZipFile(expected_docx) as archive:
                expected = archive.read("word/document.xml")
            assert actual == expected, "historical Word document.xml changed"
            assert len(repository.list_all()) == count
    assert sha256(records.read_bytes()).hexdigest() == original_sha
    return {"record_id": record_id, "algorithm_version": record.algorithm_version,
            "records": count, "original_database_unchanged": True,
            "model_sha256": sha256(repr(model).encode()).hexdigest(),
            "document_xml_sha256": sha256(actual).hexdigest(),
            "word_body_bytes_unchanged": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--expected-docx", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.records, args.record_id, args.expected_docx), ensure_ascii=False))
