from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from packages.application.carbon_accounting import (
    CarbonAccountingPreviewUseCase,
    CarbonAccountingUseCase,
    RecordPersistenceError,
    RecordRepositoryConfigurationError,
)
from packages.core.errors import IssueLevel, ValidationProblem, contains_errors
from packages.core.models import (
    AccountingInput,
    AccountingPeriod,
    CalculationResult,
    PeriodType,
    RecordStatus,
)
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.persistence.records_repository import SQLiteRecordRepository


NOW = datetime(2026, 10, 7, 8, 30, tzinfo=timezone.utc)
STANDARD_ID = "gbt_32151_34_2024"
ALGORITHM_VERSION = "carbon_material_test_v1"


@dataclass(frozen=True)
class _Evidence:
    input_snapshot: AccountingInput
    standard_version: str
    effective_rule_ids: tuple[str, ...]
    raw_input_snapshot_json: str
    trace_snapshot_json: str
    provenance_snapshot_json: str
    reporting_snapshot_json: str
    report_qualification_json: str


@dataclass(frozen=True)
class _Outcome:
    input: object
    result: CalculationResult | None
    problems: tuple[ValidationProblem, ...]
    parameter_snapshots: tuple[object, ...]
    traces: tuple[object, ...]
    algorithm_version: str
    record: object | None
    report_qualification: object | None
    evidence: _Evidence | None

    @property
    def blocked(self) -> bool:
        return contains_errors(self.problems)

    @property
    def successful(self) -> bool:
        return not self.blocked and self.result is not None


class _QueueCalculator:
    def __init__(self, *outcomes: _Outcome) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[tuple[object, datetime | None]] = []

    def calculate(self, input_value: object, *, calculated_at: datetime | None = None) -> _Outcome:
        self.calls.append((input_value, calculated_at))
        return self.outcomes.pop(0)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reporting_snapshot(marker: str) -> dict[str, object]:
    return {
        "organization_nature": "有限责任公司",
        "industry": "炭素材料制造",
        "social_credit_code": "913300000000000000",
        "legal_representative": "张某",
        "preparer_name": "李某",
        "preparer_contact": "contact@example.invalid",
        "boundary_description": "主生产系统",
        "products_and_process": "炭素材料生产",
        "emission_source_identification": "燃料与过程排放",
        "other_report_information": f"报告备注-{marker}",
        "activity_evidence": [{"evidence_id": f"activity.{marker}", "source_reference": "计量台账第1页"}],
        "measured_factor_evidence": [{"evidence_id": f"factor.{marker}", "reason": "采用企业实测值"}],
    }


def _outcome(
    marker: str,
    *,
    warnings: bool = False,
    blocked: bool = False,
    reporting: dict[str, object] | None = None,
) -> _Outcome:
    input_snapshot = AccountingInput(
        input_id=f"input.usecase.{marker}",
        standard_id=STANDARD_ID,
        period=AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
        enterprise_name="Application 测试企业",
        boundary_component_ids=("boundary.production",),
    )
    problems = (
        ValidationProblem("TEST-BLOCKED", IssueLevel.ERROR, "输入未通过致命校验。"),
    ) if blocked else (
        ValidationProblem("TEST-WARNING", IssueLevel.WARNING, "存在非阻断提醒。"),
    ) if warnings else ()
    result = None if blocked else CalculationResult(
        result_id=f"result.usecase.{marker}",
        standard_id=STANDARD_ID,
        algorithm_version=ALGORITHM_VERSION,
        lines=(),
        total_amount="1.25",
        total_unit="tCO2",
        calculated_at=NOW,
        problems=problems,
    )
    report_payload = reporting if reporting is not None else _reporting_snapshot(marker)
    evidence = None if blocked else _Evidence(
        input_snapshot=input_snapshot,
        standard_version="2024",
        effective_rule_ids=("CAR-RULE-TEST-001", "CAR-RULE-TEST-002"),
        raw_input_snapshot_json=_json({"input_id": input_snapshot.input_id, "source_text": f"raw-{marker}"}),
        trace_snapshot_json=_json({"trace_schema_version": 1, "trace_marker": marker}),
        provenance_snapshot_json=_json({"catalog_identity": f"catalog-{marker}"}),
        reporting_snapshot_json=_json(report_payload),
        report_qualification_json=_json({"eligible": True, "marker": marker}),
    )
    return _Outcome(
        input=input_snapshot,
        result=result,
        problems=problems,
        parameter_snapshots=(),
        traces=(),
        algorithm_version=ALGORITHM_VERSION,
        record=None,
        report_qualification=None,
        evidence=evidence,
    )


class CarbonAccountingUseCaseTests(unittest.TestCase):
    def test_real_domain_calculator_preview_and_sqlite_formal_record(self) -> None:
        from dataclasses import replace

        from packages.standards.carbon_material import (
            CarbonMaterialCalculator,
            CarbonMaterialInput,
            CarbonReportingData,
        )

        reporting = CarbonReportingData(
            organization_nature="有限责任公司",
            industry="炭素材料制造",
            social_credit_code="913300000000000000",
            legal_representative="张某",
            preparer_name="李某",
            preparer_contact="contact@example.invalid",
            boundary_description="主生产系统",
            products_and_process="炭素材料生产",
            emission_source_identification="燃料与过程排放",
            other_report_information="真实Domain报告快照",
        )
        input_value = CarbonMaterialInput(
            input_id="input.application.real",
            enterprise_id="enterprise.application.real",
            enterprise_name="真实 Domain 测试企业",
            period=AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
            boundary_confirmed=True,
            reporting_data=reporting,
        )
        calculator = CarbonMaterialCalculator()

        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            preview_outcome = CarbonAccountingPreviewUseCase(calculator).calculate(
                input_value, calculated_at=NOW
            )
            self.assertTrue(preview_outcome.successful, preview_outcome.problems)
            self.assertIsNone(preview_outcome.record)
            self.assertEqual(repository.list_all(), ())

            formal_outcome = CarbonAccountingUseCase(calculator, repository).calculate(
                input_value, calculated_at=NOW
            )
            self.assertTrue(formal_outcome.successful, formal_outcome.problems)
            self.assertIsNotNone(formal_outcome.evidence)
            self.assertIsNotNone(formal_outcome.record)
            assert formal_outcome.evidence is not None
            assert formal_outcome.record is not None
            stored = repository.get(formal_outcome.record.record_id)
            self.assertEqual(stored, formal_outcome.record)
            self.assertEqual(len(repository.list_all()), 1)

            evidence = formal_outcome.evidence
            self.assertEqual(
                repository.get_raw_input_snapshot(formal_outcome.record.record_id),
                json.loads(evidence.raw_input_snapshot_json),
            )
            trace = repository.get_trace_snapshot(formal_outcome.record.record_id)
            provenance = repository.get_provenance_snapshot(formal_outcome.record.record_id)
            reporting_snapshot = repository.get_reporting_snapshot(formal_outcome.record.record_id)
            qualification = repository.get_report_qualification(formal_outcome.record.record_id)
            self.assertEqual(trace, json.loads(evidence.trace_snapshot_json))
            self.assertEqual(provenance, json.loads(evidence.provenance_snapshot_json))
            self.assertEqual(reporting_snapshot, json.loads(evidence.reporting_snapshot_json))
            self.assertEqual(qualification, json.loads(evidence.report_qualification_json))
            assert reporting_snapshot is not None
            for field in (
                "organization_nature", "industry", "social_credit_code", "legal_representative",
                "preparer_name", "preparer_contact", "boundary_description", "products_and_process",
                "emission_source_identification", "other_report_information",
                "activity_evidence", "measured_factor_evidence",
            ):
                self.assertIn(field, reporting_snapshot)

            blocked_input = replace(
                input_value,
                input_id="input.application.real.blocked",
                boundary_confirmed=False,
            )
            blocked_outcome = CarbonAccountingUseCase(calculator, repository).calculate(
                blocked_input, calculated_at=NOW
            )
            self.assertTrue(blocked_outcome.blocked)
            self.assertIsNone(blocked_outcome.record)
            self.assertEqual(len(repository.list_all()), 1)
    def test_preview_only_calls_the_pure_calculator_and_returns_its_outcome(self) -> None:
        expected = _outcome("preview")
        calculator = _QueueCalculator(expected)
        preview = CarbonAccountingPreviewUseCase(calculator)  # type: ignore[arg-type]
        input_value = object()

        actual = preview.calculate(input_value, calculated_at=NOW)  # type: ignore[arg-type]

        self.assertIs(actual, expected)
        self.assertIsNone(actual.record)
        self.assertEqual(calculator.calls, [(input_value, NOW)])

    def test_success_persists_complete_snapshots_and_warning_status(self) -> None:
        expected = _outcome("warning", warnings=True)
        calculator = _QueueCalculator(expected)
        repository = InMemoryRecordRepository()
        use_case = CarbonAccountingUseCase(calculator, repository)  # type: ignore[arg-type]

        actual = use_case.calculate(object(), calculated_at=NOW)  # type: ignore[arg-type]

        self.assertIsNotNone(actual.record)
        assert actual.record is not None
        self.assertEqual(actual.record.status, RecordStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(repository.get(actual.record.record_id), actual.record)
        self.assertEqual(
            repository.get_raw_input_snapshot(actual.record.record_id),
            {"input_id": "input.usecase.warning", "source_text": "raw-warning"},
        )
        self.assertEqual(
            repository.get_effective_rule_set(actual.record.record_id),
            {"rule_ids": ("CAR-RULE-TEST-001", "CAR-RULE-TEST-002")},
        )
        self.assertEqual(
            repository.get_trace_snapshot(actual.record.record_id),
            {"trace_schema_version": 1, "trace_marker": "warning"},
        )
        self.assertEqual(
            repository.get_provenance_snapshot(actual.record.record_id),
            {"catalog_identity": "catalog-warning"},
        )
        self.assertEqual(
            repository.get_reporting_snapshot(actual.record.record_id),
            _reporting_snapshot("warning"),
        )
        self.assertEqual(
            repository.get_report_qualification(actual.record.record_id),
            {"eligible": True, "marker": "warning"},
        )

    def test_repeated_successes_append_new_records_and_blocked_outcome_is_unchanged(self) -> None:
        first = _outcome("first")
        second = _outcome("second")
        blocked = _outcome("blocked", blocked=True)
        calculator = _QueueCalculator(first, second, blocked)
        repository = InMemoryRecordRepository()
        use_case = CarbonAccountingUseCase(calculator, repository)  # type: ignore[arg-type]

        first_result = use_case.calculate(object())  # type: ignore[arg-type]
        second_result = use_case.calculate(object())  # type: ignore[arg-type]
        blocked_result = use_case.calculate(object())  # type: ignore[arg-type]

        self.assertEqual(len(repository.list_all()), 2)
        self.assertNotEqual(first_result.record.record_id, second_result.record.record_id)  # type: ignore[union-attr]
        self.assertEqual(blocked_result, blocked)
        self.assertIsNone(blocked_result.record)

    def test_missing_or_legacy_repository_is_rejected_during_configuration(self) -> None:
        calculator = _QueueCalculator(_outcome("unused"))
        with self.assertRaises(TypeError):
            CarbonAccountingUseCase(calculator)  # type: ignore[call-arg]
        with self.assertRaises(RecordRepositoryConfigurationError):
            CarbonAccountingUseCase(calculator, None)  # type: ignore[arg-type]

        class LegacyRepository:
            def create(self, record: object) -> None:
                pass

            def get(self, record_id: str) -> None:
                return None

            def list_all(self) -> tuple[()]:
                return ()

        with self.assertRaisesRegex(RecordRepositoryConfigurationError, "create_with_details"):
            CarbonAccountingUseCase(calculator, LegacyRepository())  # type: ignore[arg-type]

    def test_sqlite_snapshot_failure_rolls_back_and_is_not_returned_as_formal_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "records.sqlite"
            repository = SQLiteRecordRepository(database)
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "CREATE TRIGGER reject_record_snapshot BEFORE INSERT ON accounting_records "
                    "WHEN NEW.raw_input_snapshot_json <> '{}' OR NEW.trace_snapshot_json <> '{}' "
                    "BEGIN SELECT RAISE(ABORT, 'test snapshot failure'); END"
                )
                connection.commit()
            finally:
                connection.close()

            use_case = CarbonAccountingUseCase(_QueueCalculator(_outcome("sqlite-fail")), repository)  # type: ignore[arg-type]
            with self.assertRaises(RecordPersistenceError) as caught:
                use_case.calculate(object())  # type: ignore[arg-type]

            self.assertIsNotNone(caught.exception.__cause__)
            self.assertIn("test snapshot failure", str(caught.exception.__cause__))
            self.assertEqual(repository.list_all(), ())
            connection = sqlite3.connect(database)
            try:
                count = connection.execute("SELECT COUNT(*) FROM accounting_records").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, 0)

    def test_saved_evidence_is_stable_across_later_calculations(self) -> None:
        repository = InMemoryRecordRepository()
        use_case = CarbonAccountingUseCase(
            _QueueCalculator(_outcome("before"), _outcome("after")),  # type: ignore[arg-type]
            repository,
        )

        first = use_case.calculate(object())  # type: ignore[arg-type]
        assert first.record is not None
        saved_before = {
            "raw": repository.get_raw_input_snapshot(first.record.record_id),
            "trace": repository.get_trace_snapshot(first.record.record_id),
            "provenance": repository.get_provenance_snapshot(first.record.record_id),
            "reporting": repository.get_reporting_snapshot(first.record.record_id),
            "qualification": repository.get_report_qualification(first.record.record_id),
        }
        use_case.calculate(object())  # type: ignore[arg-type]
        saved_after = {
            "raw": repository.get_raw_input_snapshot(first.record.record_id),
            "trace": repository.get_trace_snapshot(first.record.record_id),
            "provenance": repository.get_provenance_snapshot(first.record.record_id),
            "reporting": repository.get_reporting_snapshot(first.record.record_id),
            "qualification": repository.get_report_qualification(first.record.record_id),
        }
        self.assertEqual(saved_after, saved_before)


if __name__ == "__main__":
    unittest.main()
