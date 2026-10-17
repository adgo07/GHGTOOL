"""Formal-path tests for output-electricity source identity and snapshots."""
from dataclasses import asdict, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from packages.application.canonical_input_codec import decode_canonical_input, encode_canonical_input
from packages.application.carbon_accounting import CarbonAccountingUseCase, create_g06_parameter_resolver
from packages.application.catalog_queries import CatalogQueryService
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.core.models import (
    AccountingPeriod,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    PeriodType,
    ValueType,
)
from packages.core.parameter_resolution import ElectricityConsumptionDetail
from packages.persistence import SQLiteCatalogRepository, SQLiteRecordRepository, build_catalog_database
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    ElectricityOutputLine,
    ParameterSourceKind,
    ParameterValue,
    SOURCE_EXPORTED_ELECTRICITY,
    SOURCE_PURCHASED_ELECTRICITY,
)


PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31))
CALCULATED_AT = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
STANDARD_ID = "gbt_32151_34_2024"

# Fixed expectations come from the five supported official table entries.
# Source metadata itself is read from the actual catalog repository below.
TABLE_CASES = (
    ("全国", None, "表1", "electricity_emission_factor_national", "electricity_national_average_2023", "0.5306"),
    ("区域", "西北", "表2", "electricity_emission_factor_regional_average", "electricity_regional_average_2023_05", "0.5543"),
    ("省级", "宁夏", "表3", "electricity_emission_factor_provincial_average", "electricity_provincial_average_2023_29", "0.6187"),
    ("全国", None, "表4", "electricity_emission_factor_national_average_excluding_market_nonfossil", "electricity_national_average_excluding_market_nonfossil_2023_01", "0.6096"),
    ("全国", None, "表5", "electricity_emission_factor_national_fossil", "electricity_national_fossil_2023_01", "0.8273"),
)

SOURCE_KIND_BY_VALUE_TYPE = {
    ValueType.STANDARD_SPECIFIED: ParameterSourceKind.STANDARD_SPECIFIED,
    ValueType.STANDARD_DEFAULT: ParameterSourceKind.STANDARD_DEFAULT,
    ValueType.GOVERNMENT_PUBLISHED: ParameterSourceKind.OFFICIAL_PUBLISHED,
    ValueType.SCIENTIFIC_REFERENCE: ParameterSourceKind.USER_DEFINED,
    ValueType.MEASURED: ParameterSourceKind.MEASURED,
    ValueType.DERIVED: ParameterSourceKind.CALCULATED,
    ValueType.SYSTEM_CONSTANT: ParameterSourceKind.CALCULATED,
    ValueType.HISTORICAL: ParameterSourceKind.USER_DEFINED,
}


class PR46ElectricitySourceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_directory = tempfile.TemporaryDirectory()
        catalog_path = Path(cls.catalog_directory.name) / "catalog.sqlite"
        cls.catalog = SQLiteCatalogRepository(build_catalog_database(output_path=catalog_path))
        cls.resolver = create_g06_parameter_resolver(cls.catalog)
        cls.queries = UAT03ParameterQueries(CatalogQueryService(cls.catalog), cls.resolver)

    @classmethod
    def tearDownClass(cls):
        cls.catalog_directory.cleanup()

    def setUp(self):
        self.record_directory = tempfile.TemporaryDirectory()
        self.records_path = Path(self.record_directory.name) / "records.sqlite"
        self.records = SQLiteRecordRepository(self.records_path)
        self.formal = CarbonAccountingUseCase(
            CarbonMaterialCalculator(parameter_resolver=self.resolver), self.records,
        )

    def tearDown(self):
        self.record_directory.cleanup()

    def _option(self, case):
        level, region, table, parameter_id, factor_id, value = case
        option = next(
            item for item in self.queries.electricity_catalog_options(level, region, PERIOD)
            if item.table_number == table
        )
        factor = option.factor
        self.assertEqual(
            (factor.parameter_id, factor.factor_id, factor.normalized_value, factor.factor_year),
            (parameter_id, factor_id, Decimal(value), 2023),
        )
        return option

    @staticmethod
    def _parameter_from_catalog(option):
        factor = option.factor
        return ParameterValue(
            parameter_id=factor.parameter_id,
            value=factor.normalized_value,
            unit=factor.normalized_unit,
            source_kind=SOURCE_KIND_BY_VALUE_TYPE[factor.value_type],
            source_id=factor.source_id,
            source_version=str(factor.factor_year),
            source_location=factor.source_location,
            selection_reason=option.selection_reason,
            factor_id=factor.factor_id,
            factor_year=factor.factor_year,
        )

    def _input_for_case(self, case, *, input_id=None, include_output=True):
        option = self._option(case)
        table = case[2]
        region = case[1]
        detail_id = f"purchase.{table[-1]}"
        detail = ElectricityConsumptionDetail(
            detail_id, "enterprise.pr46", STANDARD_ID, PERIOD, "100", "MWh",
            ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY,
            region=region, selected_factor_id=option.factor.factor_id,
            factor_selection_reason=f"明确选择{table}",
        )
        output = (
            (ElectricityOutputLine(
                f"export.{table[-1]}", "100", self._parameter_from_catalog(option), region=region,
            ),)
            if include_output else ()
        )
        value = CarbonMaterialInput(
            input_id or f"input.{table[-1]}", "enterprise.pr46", None, PERIOD,
            boundary_confirmed=True, electricity_details=(detail,), exported_electricity=output,
        )
        return value, option

    def _reopen(self):
        return SQLiteRecordRepository(self.records_path)

    def _seed_old_record(self):
        input_value, _ = self._input_for_case(TABLE_CASES[0], input_id="input.old-record", include_output=False)
        outcome = self.formal.calculate(input_value, calculated_at=CALCULATED_AT)
        self.assertTrue(outcome.successful, outcome.problems)
        old_record = self.records.get(outcome.record.record_id)
        self.assertIsNotNone(old_record)
        return old_record.record_id, asdict(old_record)

    def _assert_old_record_unchanged(self, record_id, expected):
        reopened = self._reopen()
        self.assertEqual(asdict(reopened.get(record_id)), expected)

    def test_five_official_tables_can_be_purchased_and_exported_with_frozen_catalog_values(self):
        old_record_id, old_record = self._seed_old_record()
        expected_count = 1
        for case in TABLE_CASES:
            with self.subTest(table=case[2]):
                input_value, option = self._input_for_case(case)
                outcome = self.formal.calculate(input_value, calculated_at=CALCULATED_AT)
                self.assertTrue(outcome.successful, outcome.problems)
                record = self._reopen().get(outcome.record.record_id)
                self.assertEqual(record.calculation_result.total_amount, Decimal("0"))
                for source_id in (SOURCE_PURCHASED_ELECTRICITY, SOURCE_EXPORTED_ELECTRICITY):
                    amounts = [
                        line.amount for line in record.calculation_result.lines
                        if line.emission_source_id == source_id
                    ]
                    self.assertEqual(amounts, [Decimal("100") * option.factor.normalized_value])
                for detail_id in (f"purchase.{case[2][-1]}", f"export.{case[2][-1]}"):
                    snapshot = next(item for item in record.parameter_snapshots if item.detail_id == detail_id)
                    self.assertEqual(snapshot.parameter_id, option.factor.parameter_id)
                    self.assertEqual(snapshot.factor_id, option.factor.factor_id)
                    self.assertEqual(snapshot.value_used, option.factor.normalized_value)
                    self.assertEqual(snapshot.source_id, option.factor.source_id)
                    self.assertEqual(snapshot.factor_year, option.factor.factor_year)
                expected_count += 1
                reopened = self._reopen()
                self.assertEqual(len(reopened.list_all()), expected_count)
                self._assert_old_record_unchanged(old_record_id, old_record)

    def test_inconsistent_official_output_claims_roundtrip_without_records_or_input_mutation(self):
        old_record_id, old_record = self._seed_old_record()
        case = TABLE_CASES[0]
        option = self._option(case)
        canonical = self._parameter_from_catalog(option)
        malformed = (
            ("official_id_wrong_value", replace(canonical, value=Decimal("0.99"))),
            ("official_id_measured_wrong_value", replace(
                canonical, value=Decimal("0.99"), source_kind=ParameterSourceKind.MEASURED,
            )),
            ("official_id_measured_source_only", replace(
                canonical, source_kind=ParameterSourceKind.MEASURED,
            )),
            ("missing_id_claimed_standard_default", replace(
                canonical, factor_id=None, source_kind=ParameterSourceKind.STANDARD_DEFAULT,
            )),
            ("wrong_unit", replace(canonical, unit="kgCO2/MWh")),
            ("wrong_source_id", replace(canonical, source_id="SRC-UNRELATED")),
            ("wrong_source_version", replace(canonical, source_version="unrelated-version")),
            ("wrong_source_location", replace(canonical, source_location="unrelated table")),
            ("wrong_factor_year", replace(canonical, factor_year=2024)),
            ("wrong_parameter_id", replace(
                canonical, parameter_id="electricity_emission_factor_national_fossil",
            )),
        )
        purchased, _ = self._input_for_case(case, input_id="input.invalid-base", include_output=False)
        for name, factor in malformed:
            with self.subTest(mismatch=name):
                line = ElectricityOutputLine(f"invalid.{name}", "100", factor, region=case[1])
                original = replace(
                    purchased, input_id=f"input.invalid.{name}", exported_electricity=(line,),
                )
                payload = encode_canonical_input(original)
                roundtripped = decode_canonical_input(payload)
                self.assertEqual(roundtripped, original)
                self.assertEqual(encode_canonical_input(roundtripped), payload)

                outcome = self.formal.calculate(roundtripped, calculated_at=CALCULATED_AT)
                self.assertFalse(outcome.successful, outcome.problems)
                self.assertIsNone(outcome.result)
                self.assertIsNone(outcome.record)
                self.assertEqual(roundtripped, original)
                self.assertEqual(encode_canonical_input(roundtripped), payload)
                reopened = self._reopen()
                self.assertEqual(len(reopened.list_all()), 1)
                self.assertEqual(reopened.list_all()[0].record_id, old_record_id)
                self.assertEqual(asdict(reopened.get(old_record_id)), old_record)

    def test_independent_other_output_accepts_optional_explanation_and_freezes_no_catalog_identity(self):
        old_record_id, old_record = self._seed_old_record()
        case = TABLE_CASES[0]
        for explanation in (None, "企业另行提供的排放因子说明"):
            with self.subTest(explanation=explanation):
                factor = ParameterValue(
                    parameter_id=case[3], value="0.99", unit="tCO2/MWh",
                    source_kind=ParameterSourceKind.USER_DEFINED,
                    source_id=None, source_version=None, source_location=explanation,
                    selection_reason="用户手动填写并采用本条输出电力因子。",
                    factor_id=None, factor_year=None,
                )
                line_id = "other.with-note" if explanation else "other.no-note"
                input_value = CarbonMaterialInput(
                    f"input.{line_id}", "enterprise.pr46", None, PERIOD,
                    boundary_confirmed=True,
                    exported_electricity=(ElectricityOutputLine(line_id, "100", factor),),
                )
                outcome = self.formal.calculate(input_value, calculated_at=CALCULATED_AT)
                self.assertTrue(outcome.successful, outcome.problems)
                record = self._reopen().get(outcome.record.record_id)
                self.assertEqual(record.calculation_result.total_amount, Decimal("-99"))
                snapshot = next(
                    item for item in record.parameter_snapshots
                    if item.detail_id == f"CAR-FLD-POWER-EXPORTED-EF.{line_id}"
                )
                self.assertIsNone(snapshot.factor_id)
                self.assertIsNone(snapshot.source_id)
                self.assertEqual(snapshot.value_used, Decimal("0.99"))
                self.assertEqual(snapshot.source_location, explanation)
                self._assert_old_record_unchanged(old_record_id, old_record)

    def test_purchased_other_is_independent_and_invalid_or_mixed_selection_writes_no_record(self):
        from packages.core.models import DomainValidationError
        from packages.core.parameter_resolution import UserProvidedParameterValue
        old_id, old = self._seed_old_record()
        expected_count = 1
        for description in (None, "企业填报资料"):
            detail = ElectricityConsumptionDetail(
                "purchase.other", "enterprise.pr46", STANDARD_ID, PERIOD, "100", "MWh",
                ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY,
                factor_override=UserProvidedParameterValue("0.99", "tCO₂/MWh", source_reference=description),
            )
            value = CarbonMaterialInput("purchase.other", "enterprise.pr46", None, PERIOD,
                                       boundary_confirmed=True, electricity_details=(detail,))
            restored = decode_canonical_input(encode_canonical_input(value))
            outcome = self.formal.calculate(restored, calculated_at=CALCULATED_AT)
            self.assertTrue(outcome.successful, outcome.problems)
            expected_count += 1
            record = self._reopen().get(outcome.record.record_id)
            self.assertEqual(record.calculation_result.total_amount, Decimal("99"))
            self.assertTrue(all(item.factor_id is None and item.source_id is None for item in record.parameter_snapshots))
            self.assertEqual(len(self._reopen().list_all()), expected_count)
        invalid_details = (
            replace(detail, factor_override=UserProvidedParameterValue("0.99", "kg")),
            replace(detail, factor_override=None, selected_factor_id="missing-historical-factor",
                    factor_selection_reason="历史目录选择"),
        )
        for invalid_detail in invalid_details:
            value = replace(value, electricity_details=(invalid_detail,))
            restored = decode_canonical_input(encode_canonical_input(value))
            outcome = self.formal.calculate(restored, calculated_at=CALCULATED_AT)
            self.assertFalse(outcome.successful)
            self.assertIsNone(outcome.record)
            self.assertEqual(len(self._reopen().list_all()), expected_count)
        with self.assertRaises(DomainValidationError):
            replace(detail, selected_factor_id="electricity_national_average_2023", factor_selection_reason="混用")
        self.assertEqual(len(self._reopen().list_all()), expected_count)
        self._assert_old_record_unchanged(old_id, old)


if __name__ == "__main__":
    unittest.main()
