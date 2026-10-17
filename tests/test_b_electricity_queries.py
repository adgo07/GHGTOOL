"""电力查询精确身份与绑定故障注入；不修改正式目录。"""
from dataclasses import replace
from datetime import date
from pathlib import Path
import tempfile
import unittest

from packages.application.catalog_queries import CatalogQueryService
from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.core.models import AccountingPeriod, ParameterType, PeriodType, ReviewStatus
from packages.persistence import SQLiteCatalogRepository, build_catalog_database

PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31))
NATIONAL = "electricity_national_average_2023"


class ElectricityQueryBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.repository = SQLiteCatalogRepository(build_catalog_database(output_path=Path(cls.directory.name) / "catalog.sqlite"))
        cls.resolver = create_g06_parameter_resolver(cls.repository)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def queries(self):
        return UAT03ParameterQueries(CatalogQueryService(self.repository), self.resolver)

    def assert_national_unavailable(self, queries):
        self.assertEqual(queries.electricity_options(None, PERIOD), ())
        self.assertEqual({option.table_number for option in queries.electricity_catalog_options("全国", None, PERIOD)}, {"表4", "表5"})

    def test_unrelated_verified_announcement_cannot_reuse_table_one_identity(self):
        queries = self.queries()
        factor = queries._factors[NATIONAL]
        unrelated = "unrelated-verified-announcement"
        queries._sources[unrelated] = replace(queries._sources[factor.source_id], source_id=unrelated)
        queries._factors[NATIONAL] = replace(factor, source_id=unrelated)
        table_id = "tab-elec-2025-47-1"
        table = replace(queries._table_by_id[table_id], source_id=unrelated)
        queries._table_by_id[table_id] = table
        queries._tables = tuple(table if item.source_table_id == table_id else item for item in queries._tables)
        self.assert_national_unavailable(queries)

    def test_parameter_subject_type_and_review_must_match_official_binding(self):
        for changes in ({"subject_id": "unrelated-subject"}, {"parameter_type": ParameterType.OXIDATION_RATE}, {"review_status": ReviewStatus.PENDING_SOURCE}):
            with self.subTest(changes=changes):
                queries = self.queries()
                parameter_id = queries._factors[NATIONAL].parameter_id
                queries._parameters[parameter_id] = replace(queries._parameters[parameter_id], **changes)
                self.assert_national_unavailable(queries)

    def test_missing_expired_future_and_wrong_year_binding_do_not_fall_back(self):
        for changes in (None, {"valid_to": date(2025, 12, 31)}, {"valid_from": date(2027, 1, 1)}, {"factor_year": 2022}):
            with self.subTest(changes=changes):
                queries = self.queries()
                queries._bindings = tuple(
                    replace(binding, **changes) if binding.factor_id == NATIONAL else binding
                    for binding in queries._bindings
                    if changes is not None or binding.factor_id != NATIONAL
                )
                self.assert_national_unavailable(queries)

    def test_custom_period_requires_complete_binding_coverage_but_annual_uses_overlap(self):
        queries = self.queries()
        queries._bindings = tuple(replace(binding, valid_from=date(2026, 7, 1)) if binding.factor_id == NATIONAL else binding for binding in queries._bindings)
        custom = AccountingPeriod(PeriodType.CUSTOM, PERIOD.start, PERIOD.end)
        self.assertEqual(queries.electricity_options(None, custom), ())
        self.assertEqual(len(queries.electricity_options(None, PERIOD)), 1)

    def test_wrong_table_region_or_level_never_becomes_a_national_candidate(self):
        queries = self.queries()
        queries._bindings = tuple(replace(binding, source_table_id="tab-elec-2025-47-4") if binding.factor_id == NATIONAL else binding for binding in queries._bindings)
        self.assert_national_unavailable(queries)
        for level, region in (("全国", "宁夏"), ("区域", "宁夏"), ("省级", "西北"), ("区域", None), ("未知", None)):
            with self.subTest(level=level, region=region):
                self.assertEqual(queries.electricity_catalog_options(level, region, PERIOD), ())

    def test_five_table_groups_and_nonfossil_zero_remain_separate(self):
        queries = self.queries()
        groups = queries.electricity_regions_by_level(PERIOD)
        self.assertEqual(tuple(groups), ("全国", "区域", "省级"))
        self.assertEqual(tuple(map(len, groups.values())), (1, 7, 30))
        self.assertEqual({option.table_number for option in queries.electricity_catalog_options("全国", None, PERIOD)}, {"表1", "表4", "表5"})
        zero = queries.nonfossil_electricity_factor(PERIOD)
        self.assertIsNotNone(zero)
        self.assertEqual(zero.factor.normalized_value, 0)
        self.assertNotIn(zero.factor.factor_id, {option.factor.factor_id for option in queries.electricity_catalog_options("全国", None, PERIOD)})

