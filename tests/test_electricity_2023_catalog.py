from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from packages.application.catalog_queries import CatalogQueryService
from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.core.models import AccountingPeriod, ElectricityAcquisitionMode, ElectricityAttribute, PeriodType
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import load_validated_catalog
from packages.ui.catalog_pages import ParameterFactorLibraryPage
from tests.test_g05_multi_electricity import _detail, SNAPSHOT_AT

SOURCE = 'SRC-ELEC-2023-47'
# Official attachment tables 1-5, checked independently against the supplied workbook.
EXPECTED = (
    (('全国', '0.5306'),),
    tuple(zip(('华北','东北','华东','华中','西北','南方','西南'),
              ('0.6361','0.5122','0.5500','0.5271','0.5543','0.4042','0.2472'))),
    tuple(zip(('北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','陕西','甘肃','青海','宁夏','新疆'),
              ('0.5554','0.6796','0.6516','0.6634','0.6479','0.4878','0.4671','0.5229','0.5737','0.5827','0.4974','0.6553','0.4211','0.5836','0.6191','0.5897','0.4044','0.4976','0.4419','0.4476','0.3648','0.5581','0.1564','0.5683','0.1333','0.6335','0.4471','0.1796','0.6187','0.6021'))),
    (('全国', '0.6096'),),
    (('全国', '0.8273'),),
)


class Electricity2023CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = build_catalog_database(output_path=Path(cls.temp.name) / 'catalog.sqlite')
        cls.repo = SQLiteCatalogRepository(cls.path)
        cls.service = CatalogQueryService(cls.repo)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_forty_official_values_and_regions_are_exact(self):
        catalog = load_validated_catalog()
        factors = {f['factor_id']: f for f in catalog['factors'] if f['source_id'] == SOURCE}
        self.assertEqual(len(factors), 40)
        for number, expected in enumerate(EXPECTED, 1):
            bindings = [b for b in catalog['reference_data_bindings']
                        if b['source_table_id'] == f'tab-elec-2025-47-{number}']
            actual = {b['region']: factors[b['factor_id']]['source_value'] for b in bindings}
            self.assertEqual(len(bindings), len(expected))
            self.assertEqual(actual, dict(expected))
            for binding in bindings:
                factor = factors[binding['factor_id']]
                self.assertEqual(factor['factor_year'], 2023)
                self.assertEqual(factor['source_unit'], 'kgCO₂/kWh')
                self.assertEqual(factor['unit'], 'tCO₂/MWh')
                self.assertEqual(factor['value'], factor['source_value'])
                self.assertEqual(factor['normalized_value'], factor['source_value'])
                self.assertIn(binding['region'], binding['source_location'])

    def test_source_table_projection_keeps_five_categories_and_row_order(self):
        tables = self.service.list_source_tables(SOURCE)
        self.assertEqual(len(tables), 5)
        for table, expected in zip(tables, EXPECTED):
            headers, rows, _ = self.service.get_source_table_view(table.source_table_id)
            self.assertIn('地区', headers)
            pairs = tuple((r[headers.index('地区')], r[headers.index('数值')]) for r in rows)
            self.assertEqual(pairs, expected)
        self.assertIn('不包括市场化交易', tables[3].title)
        self.assertIn('化石能源', tables[4].title)

    def test_region_search_titles_and_source_filter_are_unambiguous(self):
        for region in ('北京', '华北', '宁夏'):
            assets = [x for x in self.service.search_reference_library(region, source_id=SOURCE)
                      if x.result_type == 'asset']
            self.assertEqual(len(assets), 1)
            self.assertIn(region, assets[0].title)
            self.assertEqual({b.region for b in assets[0].bindings}, {region})
        assets = [x for x in self.service.search_reference_library('全国', source_id=SOURCE)
                  if x.result_type == 'asset']
        self.assertEqual(len(assets), 3)
        self.assertEqual({x.value_text for x in assets}, {'0.5306', '0.6096', '0.8273'})
        self.assertEqual(len({x.title for x in assets}), 3)

    def test_national_resolver_candidates_remain_unchanged(self):
        factors = self.service.list_parameter_factors('electricity_emission_factor_national')
        self.assertEqual([f.factor_id for f in factors], ['electricity_national_average_2023'])
        detail = replace(_detail('detail.library-regression', '20',
                                 ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
                         accounting_period=AccountingPeriod(PeriodType.ANNUAL, date(2026,1,1), date(2026,12,31)))
        result = create_g06_parameter_resolver(self.repo).resolve_electricity_details((detail,), snapshot_at=SNAPSHOT_AT)[0].result
        self.assertIsNotNone(result)
        self.assertEqual(result.recommended.factor.factor_id, 'electricity_national_average_2023')
        self.assertEqual(result.recommended.factor.value, Decimal('0.5306'))
        self.assertEqual(result.alternatives, ())

    def test_page_browses_all_tables_and_shows_region_in_search_detail(self):
        page = ParameterFactorLibraryPage(self.service, lambda *_args: None)
        try:
            page.source_filter.setCurrentIndex(page.source_filter.findData(SOURCE))
            self.assertEqual(page.table_filter.count(), 5)
            for number, expected in enumerate(EXPECTED, 1):
                page.table_filter.setCurrentIndex(page.table_filter.findData(f'tab-elec-2025-47-{number}'))
                self.app.processEvents()
                table = page.factor_table
                self.assertEqual(table.rowCount(), len(expected))
                headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
                col = headers.index('地区')
                self.assertEqual([table.item(r,col).text() for r in range(table.rowCount())], [x[0] for x in expected])
                self.assertTrue(all(not table.item(r,col).flags() & Qt.ItemFlag.ItemIsEditable for r in range(table.rowCount())))
            page.search_input.setText('宁夏')
            self.app.processEvents()
            row = next(i for i,x in enumerate(page._search_results) if x.result_type == 'asset')
            page.search_result_table.selectRow(row)
            page._show_selected_search_detail()
            labels = [label.text() for label in page.factor_detail_host.findChildren(QLabel)]
            self.assertIn('地区', labels)
            self.assertIn('宁夏', labels)
        finally:
            page.close()
            page.deleteLater()
            self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
