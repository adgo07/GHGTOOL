"""PR46合并基线保护：Issue010五表选择，不代表规则候选生产接管。"""
from dataclasses import asdict, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from packages.application.carbon_accounting import (
    CarbonAccountingPreviewUseCase, CarbonAccountingUseCase, create_g06_parameter_resolver,
)
from packages.application.catalog_queries import CatalogQueryService
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.core.models import AccountingPeriod, ElectricityAcquisitionMode, ElectricityAttribute, PeriodType
from packages.core.parameter_resolution import ElectricityConsumptionDetail
from packages.persistence import SQLiteCatalogRepository, SQLiteRecordRepository, build_catalog_database
from packages.standards.carbon_material import (
    CarbonMaterialCalculator, CarbonMaterialInput, ElectricityOutputLine,
    ParameterSourceKind, ParameterValue, SOURCE_EXPORTED_ELECTRICITY, SOURCE_PURCHASED_ELECTRICITY,
)

STANDARD_ID = "gbt_32151_34_2024"
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31))
NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
# 独立固定期望：100MWh，不从候选JSON/生产公式推导预期结果。
CASES = (
    ("全国", None, "表1", "electricity_emission_factor_national", "electricity_national_average_2023", "0.5306", "53.06"),
    ("全国", None, "表4", "electricity_emission_factor_national_average_excluding_market_nonfossil", "electricity_national_average_excluding_market_nonfossil_2023_01", "0.6096", "60.96"),
    ("全国", None, "表5", "electricity_emission_factor_national_fossil", "electricity_national_fossil_2023_01", "0.8273", "82.73"),
    ("区域", "西北", "表2", "electricity_emission_factor_regional_average", "electricity_regional_average_2023_05", "0.5543", "55.43"),
    ("省级", "宁夏", "表3", "electricity_emission_factor_provincial_average", "electricity_provincial_average_2023_29", "0.6187", "61.87"),
)


class PR46BaselineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.catalog = SQLiteCatalogRepository(build_catalog_database(output_path=Path(cls.directory.name) / "catalog.sqlite"))
        cls.resolver = create_g06_parameter_resolver(cls.catalog)
        cls.queries = UAT03ParameterQueries(CatalogQueryService(cls.catalog), cls.resolver)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.record_directory = tempfile.TemporaryDirectory()
        self.records = SQLiteRecordRepository(Path(self.record_directory.name) / "records.sqlite")
        calculator = CarbonMaterialCalculator(parameter_resolver=self.resolver)
        self.formal = CarbonAccountingUseCase(calculator, self.records)
        self.preview = CarbonAccountingPreviewUseCase(calculator)

    def tearDown(self):
        self.record_directory.cleanup()

    def _input(self, case):
        level, region, table, parameter_id, factor_id, value, _ = case
        option = next(o for o in self.queries.electricity_catalog_options(level, region, PERIOD) if o.table_number == table)
        self.assertEqual((option.factor.parameter_id, option.factor.factor_id, option.factor.normalized_value, option.factor.factor_year),
                         (parameter_id, factor_id, Decimal(value), 2023))
        # 这是当前Catalog的精确关联核对；Record模型未声称冻结binding_id。
        binding = next(b for b in self.catalog.list_reference_data_bindings() if b.binding_id == f"binding-{factor_id}")
        self.assertEqual((binding.factor_id, binding.factor_year, binding.region), (factor_id, 2023, region or "全国"))
        source_table = next(t for t in self.catalog.list_source_tables() if t.source_table_id == binding.source_table_id)
        self.assertEqual((source_table.source_table_id, source_table.display_number, source_table.source_id),
                         (f"tab-elec-2025-47-{table[-1]}", table, "SRC-ELEC-2023-47"))
        self.assertEqual(binding.source_location, option.factor.source_location)
        detail = ElectricityConsumptionDetail(
            f"power.{table[-1]}", "enterprise.pr46", STANDARD_ID, PERIOD, "100", "MWh",
            ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY,
            region=region, selected_factor_id=factor_id, factor_selection_reason=f"显式选择{table}",
        )
        return CarbonMaterialInput(f"input.{table[-1]}", "enterprise.pr46", None, PERIOD,
                                   boundary_confirmed=True, electricity_details=(detail,)), option.factor

    def _assert_snapshot(self, record, case, factor, detail_id):
        snapshot = next(s for s in record.parameter_snapshots if s.detail_id == detail_id)
        self.assertEqual((snapshot.parameter_id, snapshot.factor_id, snapshot.factor_year,
                          snapshot.source_id, snapshot.source_location, snapshot.value_used),
                         (case[3], case[4], 2023, "SRC-ELEC-2023-47", factor.source_location, Decimal(case[5])))

    def test_five_table_100_mwh_preview_and_append_freeze_actual_values(self):
        frozen = []
        for case in CASES:
            with self.subTest(table=case[2]):
                input_value, factor = self._input(case)
                before = len(self.records.list_all())
                preview = self.preview.calculate(input_value, calculated_at=NOW)
                self.assertTrue(preview.successful, preview.problems)
                self.assertIsNone(preview.record)
                self.assertEqual(preview.result.total_amount, Decimal(case[6]))
                self.assertEqual(len(self.records.list_all()), before)
                record_ids = []
                for _ in range(2):
                    outcome = self.formal.calculate(input_value, calculated_at=NOW)
                    self.assertTrue(outcome.successful, outcome.problems)
                    record = self.records.get(outcome.record.record_id)
                    self.assertEqual(record.calculation_result.total_amount, Decimal(case[6]))
                    self._assert_snapshot(record, case, factor, input_value.electricity_details[0].detail_id)
                    record_ids.append(record.record_id)
                    frozen.append((record.record_id, asdict(record)))
                self.assertNotEqual(*record_ids)
                self.assertEqual(len(self.records.list_all()), before + 2)
        for record_id, saved in frozen:
            self.assertEqual(asdict(self.records.get(record_id)), saved)

    def test_same_factor_purchase_and_output_are_independent_and_output_deducts(self):
        for case in CASES:
            with self.subTest(table=case[2]):
                input_value, factor = self._input(case)
                parameter = ParameterValue(
                    parameter_id=case[3], value=case[5], unit="tCO2/MWh",
                    source_kind=ParameterSourceKind.OFFICIAL_PUBLISHED, source_id="SRC-ELEC-2023-47",
                    source_version="2023", source_location=factor.source_location,
                    selection_reason=f"显式选择{case[2]}", factor_id=case[4], factor_year=2023,
                )
                input_value = replace(input_value, exported_electricity=(ElectricityOutputLine("power.output", "100", parameter, region=case[1]),))
                outcome = self.formal.calculate(input_value, calculated_at=NOW)
                self.assertTrue(outcome.successful, outcome.problems)
                record = self.records.get(outcome.record.record_id)
                for source in (SOURCE_PURCHASED_ELECTRICITY, SOURCE_EXPORTED_ELECTRICITY):
                    lines = [line.amount for line in record.calculation_result.lines if line.emission_source_id == source]
                    self.assertEqual(lines, [Decimal(case[6])])
                self.assertEqual(record.calculation_result.total_amount, Decimal("0"))
                self._assert_snapshot(record, case, factor, "power.output")

    def test_unavailable_or_out_of_period_selection_blocks_without_record_or_fallback(self):
        input_value, _ = self._input(CASES[0])
        original = input_value.electricity_details[0]
        expired_period = AccountingPeriod(PeriodType.CUSTOM, date(2025, 12, 29), date(2025, 12, 30))
        invalid_inputs = (
            replace(input_value, electricity_details=(replace(original, selected_factor_id="missing-catalog-factor"),)),
            replace(input_value, period=expired_period, electricity_details=(replace(original, accounting_period=expired_period),)),
        )
        for invalid in invalid_inputs:
            with self.subTest(period=invalid.period, factor=invalid.electricity_details[0].selected_factor_id):
                for use_case in (self.preview, self.formal):
                    outcome = use_case.calculate(invalid, calculated_at=NOW)
                    self.assertFalse(outcome.successful)
                    self.assertIsNone(outcome.record)
                    self.assertIsNone(outcome.result)
                    self.assertEqual(self.records.list_all(), ())
