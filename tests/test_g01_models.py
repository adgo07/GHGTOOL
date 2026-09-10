from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from dataclasses import FrozenInstanceError, replace
import unittest

from packages.core import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    ActivityData,
    ActivityDataSource,
    CalculationLine,
    CalculationResult,
    DomainValidationError,
    Factor,
    IssueLevel,
    OfficialStatus,
    Parameter,
    ParameterSelectionMethod,
    ParameterSnapshot,
    ParameterType,
    PeriodType,
    RecordStatus,
    ReviewStatus,
    Standard,
    SourceDocument,
    SourceType,
    ValueType,
    ValidationProblem,
    contains_errors,
)


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
STANDARD_ID = "gbt_32151_34_2024"


def annual_period() -> AccountingPeriod:
    return AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def accounting_input() -> AccountingInput:
    return AccountingInput(
        input_id="input-001",
        standard_id=STANDARD_ID,
        period=annual_period(),
        enterprise_name="示例企业",
        boundary_component_ids=("boundary.main",),
        activities=(ActivityData("activity.energy", "12.5", "MWh", ActivityDataSource.METER),),
    )


def calculation_result(problems: tuple[ValidationProblem, ...] = ()) -> CalculationResult:
    return CalculationResult(
        result_id="result-001",
        standard_id=STANDARD_ID,
        algorithm_version="1.0",
        lines=(CalculationLine("line-001", "source.energy", "CO2", "1.25", "tCO2"),),
        total_amount="1.25",
        total_unit="tCO2",
        calculated_at=NOW,
        problems=problems,
    )


class DomainModelTest(unittest.TestCase):
    def test_stable_ids_are_separate_from_display_names(self) -> None:
        standard = Standard(
            standard_id=STANDARD_ID,
            standard_family_id="gbt_32151_34",
            standard_number="GB/T 32151.34-2024",
            standard_name="温室气体排放核算与报告要求 第34部分：炭素材料生产企业",
            version="2024",
            official_status=OfficialStatus.ACTIVE,
        )
        self.assertNotEqual(standard.standard_id, standard.standard_name)
        self.assertEqual(standard.version, "2024")

    def test_domain_enum_fields_reject_raw_strings(self) -> None:
        standard = Standard(
            standard_id=STANDARD_ID,
            standard_family_id="gbt_32151_34",
            standard_number="GB/T 32151.34-2024",
            standard_name="炭素材料生产企业",
            version="2024",
        )
        source = SourceDocument(
            source_id="source.enum",
            source_type=SourceType.OFFICIAL_STANDARD,
            document_no="DOC-1",
            document_name="测试来源",
            publisher="测试发布者",
        )
        parameter = Parameter(
            "param.enum",
            "subject.enum",
            ParameterType.LOWER_HEATING_VALUE,
            "测试参数",
            "GJ",
            "2024",
        )
        factor = Factor(
            "factor.enum",
            parameter.parameter_id,
            parameter.subject_id,
            parameter.parameter_type,
            "1",
            "GJ",
            "2024",
            ValueType.STANDARD_DEFAULT,
            ReviewStatus.VERIFIED,
        )
        snapshot = ParameterSnapshot(
            "snapshot.enum",
            parameter.parameter_id,
            factor.factor_id,
            "1",
            "GJ",
            None,
            None,
            ParameterSelectionMethod.STANDARD_REQUIRED,
            "测试原因",
            STANDARD_ID,
            NOW,
        )
        record = AccountingRecord(
            "record.enum",
            STANDARD_ID,
            "1.0",
            NOW,
            accounting_input(),
            calculation_result(),
            RecordStatus.COMPLETED,
            (snapshot,),
        )
        raw_enum_cases = (
            ("ValidationProblem.level", lambda: ValidationProblem("ENUM.RAW", "ERROR", "测试")),
            ("Standard.official_status", lambda: replace(standard, official_status="ACTIVE")),
            ("SourceDocument.source_type", lambda: replace(source, source_type="OFFICIAL_STANDARD")),
            ("SourceDocument.review_status", lambda: replace(source, review_status="PENDING_SOURCE")),
            ("Parameter.parameter_type", lambda: replace(parameter, parameter_type="LOWER_HEATING_VALUE")),
            ("Factor.parameter_type", lambda: replace(factor, parameter_type="LOWER_HEATING_VALUE")),
            ("Factor.value_type", lambda: replace(factor, value_type="STANDARD_DEFAULT")),
            ("Factor.review_status", lambda: replace(factor, review_status="VERIFIED")),
            ("ActivityData.source_type", lambda: ActivityData("activity.enum", "1", "GJ", "METER")),
            ("AccountingPeriod.period_type", lambda: AccountingPeriod("ANNUAL", date(2025, 1, 1), date(2025, 12, 31))),
            (
                "ParameterSnapshot.selection_method",
                lambda: replace(snapshot, selection_method="STANDARD_REQUIRED"),
            ),
            ("AccountingRecord.status", lambda: replace(record, status="COMPLETED")),
        )
        for field_name, factory in raw_enum_cases:
            with self.subTest(field_name=field_name):
                with self.assertRaises(DomainValidationError):
                    factory()

    def test_period_and_factor_invariants(self) -> None:
        monthly = AccountingPeriod(PeriodType.MONTHLY, date(2024, 2, 1), date(2024, 2, 29))
        self.assertEqual(monthly.end.day, 29)
        with self.assertRaises(DomainValidationError):
            AccountingPeriod(PeriodType.MONTHLY, date(2024, 2, 2), date(2024, 2, 29))

        parameter = Parameter("param.lhv.ng", "fuel.natural_gas", ParameterType.LOWER_HEATING_VALUE, "低位发热量", "GJ", "1")
        factor = Factor(
            factor_id="factor.lhv.ng.2024",
            parameter_id=parameter.parameter_id,
            subject_id=parameter.subject_id,
            parameter_type=parameter.parameter_type,
            value="389.31",
            unit="GJ",
            version="2024",
            value_type=ValueType.STANDARD_DEFAULT,
            review_status=ReviewStatus.VERIFIED,
            source_id="SRC-32151-34-2024",
            applicable_standard_ids=(STANDARD_ID,),
        )
        self.assertEqual(factor.value, Decimal("389.31"))
        with self.assertRaises(FrozenInstanceError):
            factor.value = Decimal("1")  # type: ignore[misc]

    def test_problem_levels_and_record_status(self) -> None:
        info = ValidationProblem("INPUT.SOURCE_INFO", IssueLevel.INFO, "已记录数据来源", "activity.energy")
        warning = ValidationProblem("PARAM.DEFAULT_USED", IssueLevel.WARNING, "采用标准缺省值", "param.lhv.ng")
        error = ValidationProblem("INPUT.REQUIRED", IssueLevel.ERROR, "缺少必填活动数据", "activity.energy")
        self.assertFalse(info.blocks_record)
        self.assertTrue(error.blocks_record)
        self.assertTrue(contains_errors((error,)))

        complete = AccountingRecord(
            record_id="record-001",
            standard_id=STANDARD_ID,
            algorithm_version="1.0",
            created_at=NOW,
            input_snapshot=accounting_input(),
            calculation_result=calculation_result((info,)),
            status=RecordStatus.COMPLETED,
        )
        self.assertEqual(complete.status, RecordStatus.COMPLETED)

        warned = AccountingRecord(
            record_id="record-002",
            standard_id=STANDARD_ID,
            algorithm_version="1.0",
            created_at=NOW,
            input_snapshot=accounting_input(),
            calculation_result=calculation_result((warning,)),
            status=RecordStatus.COMPLETED_WITH_WARNINGS,
        )
        self.assertEqual(warned.status, RecordStatus.COMPLETED_WITH_WARNINGS)

        with self.assertRaises(DomainValidationError):
            AccountingRecord(
                record_id="record-003",
                standard_id=STANDARD_ID,
                algorithm_version="1.0",
                created_at=NOW,
                input_snapshot=accounting_input(),
                calculation_result=calculation_result((error,)),
                status=RecordStatus.COMPLETED,
            )

    def test_parameter_snapshot_is_immutable_and_versioned(self) -> None:
        snapshot = ParameterSnapshot(
            snapshot_id="snapshot-001",
            parameter_id="param.lhv.ng",
            factor_id="factor.lhv.ng.2024",
            value_used="389.31",
            unit_used="GJ",
            source_id="SRC-32151-34-2024",
            source_version="2024",
            selection_method=ParameterSelectionMethod.STANDARD_REQUIRED,
            selection_reason="当前行业标准直接规定",
            standard_id=STANDARD_ID,
            snapshot_at=NOW,
        )
        self.assertEqual(snapshot.value_used, Decimal("389.31"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.value_used = Decimal("1")  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
