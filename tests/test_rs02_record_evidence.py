from __future__ import annotations

import tempfile
import unittest
import runpy
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from packages.core.models import AccountingPeriod, PeriodType
from packages.persistence.records_repository import RecordRepositoryError, SQLiteRecordRepository
from packages.standards.carbon_material import (
    ActivityDataEvidence,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonReportingData,
    CalcinationInput,
    EmissionSourceState,
    EmissionSourceStatus,
    FuelInput,
    FuelPath,
    GraphitizationInput,
    InputValue,
    MeasuredFactorEvidence,
    ParameterSourceKind,
    ParameterValue,
    SOURCE_FUEL,
    SOURCE_GRAPHITIZATION,
    InMemoryRecordRepository,
    verify_record_aggregation,
)

_PRESENTATION = runpy.run_path(str(Path(__file__).resolve().parents[1] / "packages" / "ui" / "record_experience.py"))
SnapshotState = _PRESENTATION["SnapshotState"]


NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)
STANDARD_ID = "gbt_32151_34_2024"


def _input(period_type: PeriodType = PeriodType.ANNUAL, *, reporting_data: CarbonReportingData | None = None, **kwargs: object) -> CarbonMaterialInput:
    if period_type is PeriodType.ANNUAL:
        period = AccountingPeriod(period_type, date(2025, 1, 1), date(2025, 12, 31))
    elif period_type is PeriodType.MONTHLY:
        period = AccountingPeriod(period_type, date(2025, 3, 1), date(2025, 3, 31))
    else:
        period = AccountingPeriod(period_type, date(2025, 3, 2), date(2025, 4, 5))
    return CarbonMaterialInput(
        input_id=f"input.rs02.{period_type.value.lower()}",
        enterprise_id="enterprise.rs02",
        enterprise_name="RS02 证据快照企业",
        period=period,
        boundary_confirmed=bool(kwargs.pop("boundary_confirmed", True)),
        reporting_data=reporting_data or CarbonReportingData(),
        **kwargs,
    )


def _calculation_snapshot(record) -> dict[str, object]:
    result = record.calculation_result
    return {
        "lines": [
            {
                "line_id": item.line_id,
                "emission_source_id": item.emission_source_id,
                "amount": str(item.amount),
                "unit": item.unit,
            }
            for item in result.lines
        ],
        "total_amount": str(result.total_amount),
    }


class RS02RecordEvidenceTests(unittest.TestCase):
    def test_success_persists_versioned_trace_provenance_reporting_and_restarts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.sqlite"
            identity = {"catalog_id": "catalog-test", "data_version": "test-1", "content_sha256": "a" * 64}
            repository = SQLiteRecordRepository(path)
            calculator = CarbonMaterialCalculator(
                record_repository=repository,
                reference_data_identity_provider=lambda: identity,
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
                other_report_information="报告说明快照",
                activity_evidence=(ActivityDataEvidence(
                    "evidence.activity.shared", "年度燃料计量", (SOURCE_FUEL,),
                    source_reference="计量台账第1页", monitoring_location="燃料计量点",
                    monitoring_method="连续计量", instrument="流量计A", accuracy="0.5级",
                    recording_frequency="每日", acquisition_time="2025年度", note="复核完成",
                ),),
                measured_factor_evidence=(MeasuredFactorEvidence(
                    "evidence.factor.shared", "燃料含碳量", (SOURCE_FUEL,),
                    source_reference="检测报告第3页", sampling_method="分层取样",
                    sampling_frequency="每批次", testing_method="实验室检测",
                    testing_frequency="每批次", referenced_standard="检测依据标准",
                    reason="采用企业实测值",
                ),),
            )
            measured_carbon = ParameterValue(
                "CAR-PAR-FUEL-CARBON", "0.015", "tC/t",
                source_kind=ParameterSourceKind.MEASURED,
                source_id="enterprise-test-report", source_version="2025-test-1",
                source_location="检测报告第3页", selection_reason="采用企业实测含碳量",
            )
            input_value = _input(
                reporting_data=reporting,
                fuel_inputs=(FuelInput.mass("fuel.coke", "2", measured_carbon, "0.98"),),
            )

            outcome = calculator.calculate(input_value, calculated_at=NOW)
            self.assertTrue(outcome.successful)
            record_id = outcome.record.record_id
            trace_before = repository.get_trace_snapshot(record_id)
            provenance_before = repository.get_provenance_snapshot(record_id)
            reporting_before = repository.get_reporting_snapshot(record_id)
            qualification_before = repository.get_report_qualification(record_id)
            self.assertEqual(trace_before["trace_schema_version"], 1)
            self.assertEqual(provenance_before["provenance_schema_version"], 1)
            self.assertEqual(provenance_before["mapping"]["version"], "SM01-2026-09-13-R6")
            self.assertEqual(provenance_before["reference_data"]["content_sha256"], "a" * 64)
            self.assertEqual(reporting_before["social_credit_code"], "913300000000000000")
            self.assertEqual(qualification_before["eligible"], True)
            self.assertTrue(any(
                item.evidence_ref_ids == ("evidence.factor.shared",)
                for item in repository.get(record_id).parameter_snapshots
                if item.selection_method.value == "ENTERPRISE_MEASURED"
            ))
            raw = repository.get_raw_input_snapshot(record_id)
            self.assertEqual(raw["fuel_inputs"][0]["activity"]["evidence_ref_ids"], ["evidence.activity.shared"])
            self.assertEqual(raw["fuel_inputs"][0]["carbon_content"]["evidence_ref_ids"], ["evidence.factor.shared"])
            self.assertEqual(verify_record_aggregation(trace_before, _calculation_snapshot(repository.get(record_id))), ())
            self.assertEqual(repository.get_snapshot_schema_version(record_id), 1)

            identity["content_sha256"] = "b" * 64
            restarted = SQLiteRecordRepository(path)
            self.assertEqual(restarted.get(record_id), repository.get(record_id))
            self.assertEqual(restarted.get_trace_snapshot(record_id), trace_before)
            self.assertEqual(restarted.get_provenance_snapshot(record_id), provenance_before)
            self.assertEqual(restarted.get_reporting_snapshot(record_id), reporting_before)
            self.assertEqual(restarted.get_report_qualification(record_id), qualification_before)
            self.assertEqual(restarted.get_provenance_snapshot(record_id)["reference_data"]["content_sha256"], "a" * 64)

    def test_multi_instance_trace_keeps_stable_process_identity_and_subtotals(self) -> None:
        repository = SQLiteRecordRepository(Path(tempfile.mkdtemp()) / "records.sqlite")
        calculator = CarbonMaterialCalculator(record_repository=repository)
        result = calculator.calculate(_input(calcinations=(
            CalcinationInput(gc="100", wfc="0.008", cc="70", ucc="5", du="1", wfc_c="0.002", wvar="0.10", wvar_c="0.02", k1="0.35", instance_id="calcination-a"),
            CalcinationInput(gc="80", wfc="0.009", cc="60", ucc="4", du="1", wfc_c="0.003", wvar="0.08", wvar_c="0.02", k1="0.35", instance_id="calcination-b"),
        )), calculated_at=NOW)
        self.assertTrue(result.successful)
        trace = repository.get_trace_snapshot(result.record.record_id)
        instances = {
            step["process_instance_id"]
            for step in trace["formula_steps"]
            if step["formula_id"] == "CAR-FML-CALCINATION-001"
        }
        self.assertEqual(instances, {"calcination-a", "calcination-b"})
        self.assertEqual(verify_record_aggregation(trace, _calculation_snapshot(repository.get(result.record.record_id))), ())

    def test_parameter_snapshots_match_exactly_prefixed_process_instances(self) -> None:
        repository = SQLiteRecordRepository(Path(tempfile.mkdtemp()) / "records.sqlite")
        first = GraphitizationInput(
            gpm="0", gpmfc="0", gta="0", gtafc="0", gwt="0", gp="0", gpfc="0", gpmvar="0",
            k3=ParameterValue("CAR-PAR-K3", "0.35", "ratio", source_location="附录C.3"),
            instance_id="graph-1",
        )
        second = GraphitizationInput(
            gpm="0", gpmfc="0", gta="0", gtafc="0", gwt="0", gp="0", gpfc="0", gpmvar="0",
            k3=ParameterValue("CAR-PAR-K3", "0.40", "ratio", source_location="附录C.3"),
            instance_id="graph-10",
        )
        outcome = CarbonMaterialCalculator(record_repository=repository).calculate(
            _input(
                graphitizations=(first, second),
                source_states=(EmissionSourceState(SOURCE_GRAPHITIZATION, EmissionSourceStatus.INVOLVED),),
            ),
            calculated_at=NOW,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        trace = repository.get_trace_snapshot(outcome.record.record_id)
        steps = {
            step["process_instance_id"]: step
            for step in trace["formula_steps"]
            if step["formula_id"] == "CAR-FML-GRAPHITIZATION-001"
        }
        first_details = {item["detail_id"] for item in steps["graph-1"]["parameter_references"]}
        second_details = {item["detail_id"] for item in steps["graph-10"]["parameter_references"]}
        self.assertEqual(first_details, {"CAR-FLD-P03-RESULT-graph-1-k3"})
        self.assertEqual(second_details, {"CAR-FLD-P03-RESULT-graph-10-k3"})
        matches = CarbonMaterialCalculator._parameter_belongs_to_trace
        formula = "CAR-FML-EXPORTED-ELECTRICITY-001"
        self.assertTrue(matches("CAR-FLD-POWER-EXPORTED-EF.line-1", formula, "trace-1", "line-1"))
        self.assertFalse(matches("CAR-FLD-POWER-EXPORTED-EF.line-10", formula, "trace-1", "line-1"))
        self.assertTrue(matches("CAR-FLD-POWER-EXPORTED-EF.line-10", formula, "trace-10", "line-10"))

    def test_read_only_report_view_uses_record_snapshots_and_business_language(self) -> None:
        repository = InMemoryRecordRepository()
        reporting = CarbonReportingData(
            activity_evidence=(ActivityDataEvidence(
                "evidence.fuel", "年度燃料计量", (SOURCE_FUEL,), source_reference="燃料台账第1页",
            ),),
        )
        activity = InputValue("2", "t", source_reference="燃料台账第1页", evidence_ref_ids=("evidence.fuel",))
        carbon = ParameterValue(
            "CAR-PAR-FUEL-CARBON", "0.02", "tC/t", source_location="附录C.1",
            evidence_ref_ids=("evidence.fuel",),
        )
        outcome = CarbonMaterialCalculator(record_repository=repository).calculate(
            _input(
                reporting_data=reporting,
                source_states=(EmissionSourceState(SOURCE_FUEL, EmissionSourceStatus.INVOLVED),),
                fuel_inputs=(FuelInput("coke-line", FuelPath.MASS, activity, carbon, "0.98"),),
            ),
            calculated_at=NOW,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        raw = repository.get_raw_input_snapshot(outcome.record.record_id)
        trace = repository.get_trace_snapshot(outcome.record.record_id)
        frozen_reporting = repository.get_reporting_snapshot(outcome.record.record_id)
        report = _PRESENTATION["build_report_view"](outcome.record, raw, trace, frozen_reporting)
        activity_view = _PRESENTATION["build_activity_evidence_view"](raw, frozen_reporting, SnapshotState.PRESENT)
        self.assertIn("B.1 排放量汇总与主要排放源分项", report)
        self.assertIn("B.2 化石燃料活动数据和排放因子", report)
        self.assertIn("质量路径", report)
        self.assertIn("证据1", report)
        self.assertIn("历史汇总核对：通过", report)
        self.assertNotIn("CAR-FML-", report)
        self.assertNotIn("CAR-FLD-", report)
        self.assertIn("证据1：年度燃料计量", activity_view)
        self.assertEqual(activity_view.count("年度燃料计量"), 1)

    def test_snapshot_states_distinguish_present_empty_legacy_and_corrupt(self) -> None:
        snapshot_state = _PRESENTATION["snapshot_state"]
        self.assertIs(snapshot_state({"value": "saved"}, True), SnapshotState.PRESENT)
        self.assertIs(snapshot_state({}, True), SnapshotState.EMPTY)
        self.assertIs(snapshot_state(None, False), SnapshotState.LEGACY)
        self.assertIs(snapshot_state("unexpected-root", True), SnapshotState.CORRUPT)
        self.assertIs(snapshot_state(None, True, read_error=True), SnapshotState.CORRUPT)

    def test_snapshot_schema_distinguishes_legacy_migration_defaults_from_corruption(self) -> None:
        database = Path(tempfile.mkdtemp()) / "records.sqlite"
        repository = SQLiteRecordRepository(database)
        outcome = CarbonMaterialCalculator(record_repository=InMemoryRecordRepository()).calculate(
            _input(), calculated_at=NOW,
        )
        repository.create(outcome.record)

        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE accounting_records SET raw_input_snapshot_json = '{}', "
                "trace_snapshot_json = '{}', provenance_snapshot_json = '{}', "
                "reporting_snapshot_json = '{}', report_qualification_json = '{}' WHERE record_id = ?",
                (outcome.record.record_id,),
            )
        self.assertEqual(repository.get_snapshot_schema_version(outcome.record.record_id), 0)
        self.assertEqual(repository.get_reporting_snapshot(outcome.record.record_id), {})

        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE accounting_records SET reporting_snapshot_json = ? WHERE record_id = ?",
                ("not-json", outcome.record.record_id),
            )
        self.assertEqual(repository.get_snapshot_schema_version(outcome.record.record_id), 1)
        with self.assertRaises(RecordRepositoryError):
            repository.get_reporting_snapshot(outcome.record.record_id)
        self.assertIs(
            _PRESENTATION["snapshot_state"](None, True, read_error=True),
            SnapshotState.CORRUPT,
        )

        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE accounting_records SET reporting_snapshot_json = ? WHERE record_id = ?",
                ('"unexpected-root"', outcome.record.record_id),
            )
        self.assertIs(
            _PRESENTATION["snapshot_state"](
                repository.get_reporting_snapshot(outcome.record.record_id), True,
            ),
            SnapshotState.CORRUPT,
        )

    def test_monthly_and_custom_period_save_record_with_separate_qualification_error(self) -> None:
        for period_type in (PeriodType.MONTHLY, PeriodType.CUSTOM):
            with self.subTest(period_type=period_type):
                repository = SQLiteRecordRepository(Path(tempfile.mkdtemp()) / "records.sqlite")
                outcome = CarbonMaterialCalculator(record_repository=repository).calculate(
                    _input(period_type), calculated_at=NOW
                )
                self.assertTrue(outcome.successful)
                self.assertIsNotNone(outcome.record)
                self.assertFalse(outcome.report_qualification.eligible)
                self.assertEqual(outcome.report_qualification.code, "CAR-VAL-ANNUAL-REPORT-PERIOD")
                self.assertFalse(any(problem.code == "CAR-VAL-ANNUAL-REPORT-PERIOD" for problem in outcome.problems))
                self.assertEqual(repository.get_report_qualification(outcome.record.record_id)["level"], "ERROR")
                view = _PRESENTATION["build_quality_view"](
                    outcome.record,
                    repository.get_report_qualification(outcome.record.record_id),
                    SnapshotState.PRESENT,
                )
                self.assertIn("核算状态：已完成", view)
                self.assertIn("年度报告资格：不符合年度报告周期要求", view)
                self.assertNotIn("核算状态：核算失败", view)

    def test_fatal_calculator_error_still_creates_no_record_and_legacy_trace_is_absent(self) -> None:
        repository = SQLiteRecordRepository(Path(tempfile.mkdtemp()) / "records.sqlite")
        calculator = CarbonMaterialCalculator(record_repository=repository)
        failed = calculator.calculate(_input(boundary_confirmed=False), calculated_at=NOW)
        self.assertFalse(failed.successful)
        self.assertIsNone(failed.record)
        self.assertEqual(repository.list_all(), ())

        legacy_repository = SQLiteRecordRepository(Path(tempfile.mkdtemp()) / "legacy.sqlite")
        # A successful record written through the base create API has no new RS02-A details.
        succeeded = CarbonMaterialCalculator(record_repository=InMemoryRecordRepository()).calculate(_input(), calculated_at=NOW)
        legacy_record = succeeded.record
        legacy_repository.create(legacy_record)
        self.assertEqual(legacy_repository.get_trace_snapshot(legacy_record.record_id), {})
        self.assertEqual(legacy_repository.get_provenance_snapshot(legacy_record.record_id), {})
        self.assertEqual(legacy_repository.get_snapshot_schema_version(legacy_record.record_id), 0)


if __name__ == "__main__":
    unittest.main()
