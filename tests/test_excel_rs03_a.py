from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openpyxl import load_workbook
from PySide6.QtWidgets import QApplication

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.application.catalog_queries import CatalogQueryService
from packages.core.parameter_resolution import ParameterResolver
from packages.excel.gbt32151_34_v1 import (
    FUEL_LABEL_BY_TYPE,
    FUEL_C1_SUBJECT_IDS,
    CARBONATE_LABELS,
    SOURCE_LABELS,
    SOURCE_IDS,
    TEMPLATE_ID,
    TEMPLATE_VERSION,
    ExcelWorkbookImporter,
    WorkbookFatalError,
    _CellReader,
    _UnitContext,
    create_template_bytes,
    significant_digit_count,
    write_template,
)
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    EmissionSourceStatus,
    FuelType,
    InMemoryRecordRepository,
    SOURCE_FUEL,
)
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.pages import ExcelImportPage


class ExcelRS03ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_root = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_root.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(cls.catalog_path), as_of=date(2026, 9, 12)
        )
        cls.resolver = create_g06_parameter_resolver(cls.catalog_service.repository)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_root.cleanup()

    def new_book(self):
        return load_workbook(BytesIO(create_template_bytes()), data_only=False)

    def add_unit(self, workbook, name: str, unit_type: str = "全厂", *, enabled: str = "是") -> int:
        sheet = workbook["核算单元"]
        row = sheet.max_row + 1
        sheet.append((name, unit_type, enabled, "示例企业", "年度", date(2025, 1, 1), date(2025, 12, 31), "是", "主生产系统", "否", "否"))
        for source in SOURCE_IDS:
            state = "涉及" if source == SOURCE_FUEL else "不涉及"
            workbook["排放源"].append((name, SOURCE_LABELS[source], state))
        return row

    def add_fuel(self, workbook, unit_name: str, amount, *, fuel: FuelType = FuelType.NATURAL_GAS, path: str = "体积", carbon=None, oxidation=None, lhv=None, source_ref=None, activity_evidence=None, parameter_evidence=None) -> int:
        sheet = workbook["化石燃料"]
        row = sheet.max_row + 1
        sheet.append((unit_name, FUEL_LABEL_BY_TYPE[fuel], path, amount, carbon, oxidation, lhv, source_ref, activity_evidence, parameter_evidence))
        return row

    @staticmethod
    def set_source_status(workbook, unit_name: str, source_id: str, state: str) -> None:
        sheet = workbook["排放源"]
        source_label = SOURCE_LABELS[source_id]
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row, 1).value == unit_name and sheet.cell(row, 2).value == source_label:
                sheet.cell(row, 3).value = state
                return
        raise AssertionError(f"source state row missing: {unit_name}/{source_label}")

    @staticmethod
    def append_by_header(workbook, sheet_name: str, values: dict[str, object]) -> int:
        sheet = workbook[sheet_name]
        headers = [cell.value for cell in sheet[1]]
        sheet.append([values.get(header) for header in headers])
        return sheet.max_row

    def save_book(self, workbook) -> Path:
        path = Path(self.temp_root.name) / f"book-{len(list(Path(self.temp_root.name).glob('book-*.xlsx')))}.xlsx"
        workbook.save(path)
        workbook.close()
        return path

    def test_template_is_generated_at_runtime_with_one_standard_metadata(self) -> None:
        content = create_template_bytes()
        self.assertGreater(len(content), 1000)
        generated = Path(self.temp_root.name) / "runtime.xlsx"
        write_template(generated)
        workbook = load_workbook(generated, data_only=False)
        self.assertEqual(workbook["__metadata__"]["B2"].value, TEMPLATE_ID)
        self.assertEqual(workbook["__metadata__"]["B3"].value, TEMPLATE_VERSION)
        self.assertEqual(workbook["__metadata__"]["B4"].value, "gbt_32151_34_2024")
        self.assertEqual(workbook["__metadata__"]["B5"].value, "2024")
        self.assertEqual(workbook["__metadata__"].sheet_state, "hidden")
        self.assertIn("单位性质", tuple(cell.value for cell in workbook["报告信息"][1]))
        self.assertIn("关联排放源", tuple(cell.value for cell in workbook["证据来源"][1]))
        workbook.close()
        self.assertFalse(tuple((Path(__file__).parents[1] / "resources").rglob("*.xlsx")))

    def test_partial_success_multi_unit_source_warning_and_no_record_persistence(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "全厂", "全厂")
        self.add_unit(workbook, "石墨化工序", "工序")
        self.add_unit(workbook, "无效工序", "其他")
        self.add_fuel(workbook, "全厂", 1)
        self.add_fuel(workbook, "石墨化工序", 2)
        self.add_fuel(workbook, "无效工序", Decimal("1.234567890123456"))
        workbook["煅烧"].append(("全厂", "误填", None, None, None, None, None, None, None, None, None))
        workbook.create_sheet("现场说明")["A1"] = "自定义页签内容"
        path = self.save_book(workbook)

        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertEqual([unit.unit_type.value for unit in preview.units], ["WHOLE_SITE", "PROCESS", "OTHER"])
        whole, process, invalid = preview.units
        self.assertTrue(whole.can_calculate)
        self.assertTrue(process.can_calculate)
        self.assertEqual(process.result.total_amount, whole.result.total_amount * Decimal("2"))
        self.assertFalse(invalid.can_calculate)
        self.assertIsNone(invalid.result)
        self.assertTrue(any(item.code == "EXCEL-NUMBER-SIGNIFICANT-DIGITS" for item in invalid.errors))
        self.assertIsNone(whole.calculation.record)
        self.assertTrue(any(item.code == "EXCEL-SOURCE-DATA-IGNORED" for item in whole.warnings))
        self.assertTrue(any(item.code == "EXCEL-UNKNOWN-SHEET" for item in preview.warnings))
        self.assertEqual(len(preview.provenance.workbook_sha256), 64)
        self.assertEqual(preview.provenance.ingress_policy_id, "GHGTOOL_EXCEL_INGRESS_V1")

    def test_default_c1_is_selected_from_canonical_and_no_ambiguous_coal_guess(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "天然气单元")
        self.add_fuel(workbook, "天然气单元", Decimal("1.5"), fuel=FuelType.NATURAL_GAS, path="体积")
        self.add_unit(workbook, "未指定煤种")
        self.add_fuel(workbook, "未指定煤种", Decimal("1"), fuel=FuelType.COAL, path="质量")
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        natural_gas, unknown_coal = preview.units
        self.assertTrue(natural_gas.can_calculate)
        fuel = natural_gas.input_value.fuel_inputs[0]
        self.assertEqual(fuel.carbon_content.source_kind.value, "STANDARD_DEFAULT")
        self.assertEqual(fuel.lower_heating_value.source_kind.value, "STANDARD_DEFAULT")
        self.assertEqual(fuel.oxidation_rate.source_kind.value, "STANDARD_DEFAULT")
        self.assertFalse(unknown_coal.can_calculate)
        self.assertIsNone(unknown_coal.input_value.fuel_inputs[0].carbon_content)
        self.assertFalse(any("煤" in issue.message and "默认" in issue.message for issue in unknown_coal.warnings))

    def test_all_current_standard_fuel_types_have_c1_default_parameter_sources(self) -> None:
        for fuel_type, subject in FUEL_C1_SUBJECT_IDS.items():
            with self.subTest(fuel=fuel_type.value):
                for suffix in ("carbon_content", "oxidation_rate", "lhv"):
                    parameter_id = f"{subject}_{suffix}"
                    factors = self.resolver.repository.list_factors(parameter_id)
                    self.assertTrue(
                        any(
                            factor.review_status.value == "VERIFIED"
                            and "gbt_32151_34_2024" in factor.applicable_standard_ids
                            for factor in factors
                        ),
                        parameter_id,
                    )

    def test_numeric_text_formula_date_blank_zero_and_ratio_semantics(self) -> None:
        cases = [
            ("text", "123.45", "EXCEL-NUMBER-CELL-REQUIRED"),
            ("text_chinese", "一百", "EXCEL-NUMBER-CELL-REQUIRED"),
            ("text_unit", "1,234 t", "EXCEL-NUMBER-CELL-REQUIRED"),
            ("text_fullwidth", "１２３", "EXCEL-NUMBER-CELL-REQUIRED"),
            ("dash", "—", "EXCEL-NUMBER-CELL-REQUIRED"),
            ("formula", "=1+2", "EXCEL-FORMULA-REJECTED"),
            ("date", date(2025, 1, 2), "EXCEL-NUMBER-CELL-REQUIRED"),
            ("too_many_digits", Decimal("1234567890123456"), "EXCEL-NUMBER-SIGNIFICANT-DIGITS"),
        ]
        for label, value, expected_code in cases:
            with self.subTest(label=label):
                workbook = self.new_book()
                self.add_unit(workbook, "全厂")
                self.add_fuel(workbook, "全厂", value)
                path = self.save_book(workbook)
                unit = ExcelWorkbookImporter(self.resolver).import_preview(path).units[0]
                self.assertFalse(unit.can_calculate)
                self.assertIn(expected_code, {issue.code for issue in unit.errors})

        workbook = self.new_book()
        self.add_unit(workbook, "零活动量")
        self.add_fuel(workbook, "零活动量", 0)
        path = self.save_book(workbook)
        zero_preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertTrue(zero_preview.units[0].can_calculate)
        self.assertEqual(zero_preview.units[0].input_value.fuel_inputs[0].activity.value, Decimal("0"))
        self.assertIn(Decimal("0"), [item.normalized_decimal for item in zero_preview.numeric_evidence])

        workbook = self.new_book()
        self.add_unit(workbook, "科学计数法")
        self.add_fuel(workbook, "科学计数法", Decimal("1E-6"))
        path = self.save_book(workbook)
        exponent_preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertTrue(exponent_preview.units[0].can_calculate)
        self.assertEqual(exponent_preview.units[0].input_value.fuel_inputs[0].activity.value, Decimal("0.000001"))

        workbook = self.new_book()
        self.add_unit(workbook, "空活动量")
        self.add_fuel(workbook, "空活动量", None)
        path = self.save_book(workbook)
        blank_preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertFalse(blank_preview.units[0].can_calculate)
        self.assertTrue(any("缺少输入" in issue.message for issue in blank_preview.units[0].errors))

    def test_percent_is_stored_numeric_ratio_not_inferred_from_cell_format(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "比例单元")
        row = self.add_fuel(workbook, "比例单元", 1, oxidation=Decimal("0.98"), source_ref="检测报告-1")
        workbook["化石燃料"].cell(row, 6).number_format = "0%"
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertTrue(preview.units[0].can_calculate)
        self.assertEqual(preview.units[0].input_value.fuel_inputs[0].oxidation_rate.value, Decimal("0.98"))

        workbook = self.new_book()
        self.add_unit(workbook, "误用百分数")
        self.add_fuel(workbook, "误用百分数", 1, oxidation=98, source_ref="检测报告-2")
        workbook["化石燃料"].cell(2, 6).number_format = "0%"
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        self.assertFalse(preview.units[0].can_calculate)
        self.assertTrue(any("0 到 1" in issue.message for issue in preview.units[0].errors))

    def test_multiple_fuel_process_fgd_electricity_and_heat_entries_use_one_calculator(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "多明细单元")
        for source_id in (
            "CAR-SRC-CALCINATION-001", "CAR-SRC-BAKING-001", "CAR-SRC-GRAPHITIZATION-001",
            "CAR-SRC-FUME-INCINERATION-001", "CAR-SRC-FGD-001", "CAR-SRC-PURCHASED-ELECTRICITY-001",
            "CAR-SRC-EXPORTED-ELECTRICITY-001", "CAR-SRC-PURCHASED-HEAT-001", "CAR-SRC-EXPORTED-HEAT-001",
        ):
            self.set_source_status(workbook, "多明细单元", source_id, "涉及")
        self.add_fuel(workbook, "多明细单元", 1, fuel=FuelType.NATURAL_GAS, path="体积")
        self.add_fuel(workbook, "多明细单元", 2, fuel=FuelType.ANTHRACITE, path="质量")

        for index in (1, 2):
            self.append_by_header(workbook, "煅烧", {
                "核算单元": "多明细单元", "实例名称": f"煅烧{index}", "GC 投入量（t）": 10,
                "WFC 固定碳比例": Decimal("0.8"), "CC 煅后焦用量（t）": 1,
                "UCC 外购煅后焦用量（t）": 1, "DU 粉尘用量（t）": 1,
                "WFC_C 煅后焦固定碳比例": Decimal("0.75"), "WVAR 挥发分比例": Decimal("0.05"),
                "WVAR_C 煅后焦挥发分比例": Decimal("0.05"),
            })
            self.append_by_header(workbook, "焙烧炭化", {
                "核算单元": "多明细单元", "实例名称": f"焙烧{index}", "BPM 生坯用量（t）": 10,
                "BPMFC 生坯固定碳比例": Decimal("0.8"), "BG 焦粉用量（t）": 1,
                "BGFC 焦粉固定碳比例": Decimal("0.8"), "BWT 焦油沥青用量（tC）": 0,
                "BP 石油焦用量（t）": 1, "BPFC 石油焦固定碳比例": Decimal("0.5"),
                "BPMVAR 生坯挥发分比例": Decimal("0.05"), "BGVAR 焦粉挥发分比例": Decimal("0.05"),
            })
            self.append_by_header(workbook, "石墨化", {
                "核算单元": "多明细单元", "实例名称": f"石墨化{index}", "GPM 生坯用量（t）": 10,
                "GPMFC 生坯固定碳比例": Decimal("0.8"), "GTA 焦油沥青用量（t）": 1,
                "GTAFC 焦油沥青固定碳比例": Decimal("0.8"), "GWT 焦油用量（tC）": 0,
                "GP 石油焦用量（t）": 1, "GPFC 石油焦固定碳比例": Decimal("0.5"),
                "GPMVAR 生坯挥发分比例": Decimal("0.05"),
            })
        self.append_by_header(workbook, "烟气焚烧", {
            "核算单元": "多明细单元", "实例名称": "焚烧线一", "Q 烟气流量（Nm³/h）": 1,
            "QVAR 烟气含碳量（mg/Nm³）": 10, "HM 低位发热量（GJ/t）": 1,
            "FCH 单位热值含碳量（tC/GJ）": Decimal("0.02"), "FOX 碳氧化率": Decimal("0.9"),
            "运行时间（d）": 100, "参数来源编号": "焚烧因子检测-1",
        })
        # Two carbonate components in one facility total 90%; a second facility
        # uses the official 90%/100% defaults directly.
        for facility, kind, fraction in (("脱硫设施A", "CaCO₃", Decimal("0.4")), ("脱硫设施A", "MgCO₃", Decimal("0.5")), ("脱硫设施B", "Na₂CO₃", None)):
            self.append_by_header(workbook, "烟气脱硫", {
                "核算单元": "多明细单元", "设施名称": facility, "碳酸盐种类": kind,
                "碳酸盐用量（t）": 1, "碳酸盐含量比例": fraction,
                "参数来源编号": "脱硫检测-1" if fraction is not None else None,
            })
        for direction, amount, factor, source in (("输出", 2, Decimal("0.5"), "输出电力-1"), ("输出", 3, Decimal("0.4"), "输出电力-2")):
            self.append_by_header(workbook, "电力", {
                "核算单元": "多明细单元", "方向": direction, "电量（MWh）": amount,
                "排放因子（tCO₂/MWh）": factor, "参数来源编号": source,
            })
        # Purchased electricity is resolved through the same G05 resolver.
        for amount in (100, 200):
            self.append_by_header(workbook, "电力", {
                "核算单元": "多明细单元", "方向": "购入", "电量（MWh）": amount,
                "取得方式": "购入", "电力属性": "常规", "证明类型": "无", "证明状态": "未提供",
            })
        for direction, amount, factor, source in (
            ("购入", 1000, Decimal("0.11"), "购入热力-1"),
            ("购入", 2000, Decimal("0.12"), "购入热力-2"),
            ("输出", 500, Decimal("0.11"), "输出热力-1"),
        ):
            self.append_by_header(workbook, "热力", {
                "核算单元": "多明细单元", "方向": direction, "热力数量（kg）": amount,
                "蒸汽类型": "饱和蒸汽", "焓值（kJ/kg）": 2675, "排放因子（tCO₂/GJ）": factor,
                "参数来源编号": source,
            })
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, tuple(issue.message for issue in unit.errors))
        self.assertEqual(len(unit.input_value.fuel_inputs), 2)
        self.assertEqual(len(unit.input_value.calcinations), 2)
        self.assertEqual(len(unit.input_value.bakings), 2)
        self.assertEqual(len(unit.input_value.graphitizations), 2)
        self.assertEqual(len(unit.input_value.fume_incinerations), 1)
        self.assertEqual(len(unit.input_value.fgd_units), 2)
        self.assertEqual(len(unit.input_value.fgd_units[0].components), 2)
        self.assertEqual(len(unit.input_value.electricity_details), 2)
        self.assertEqual(len(unit.input_value.exported_electricity), 2)
        self.assertEqual(len(unit.input_value.purchased_heat), 2)
        self.assertEqual(len(unit.input_value.exported_heat), 1)
        self.assertIsNotNone(unit.result)
        self.assertEqual(unit.calculation.algorithm_version, CarbonMaterialCalculator().calculate(unit.input_value).algorithm_version)
        self.assertIsNone(unit.calculation.record)

    def test_complete_c2_parameter_table_and_c4_c5_calculator_anchors(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "C2完整表")
        self.set_source_status(workbook, "C2完整表", "CAR-SRC-FGD-001", "涉及")
        self.set_source_status(workbook, "C2完整表", "CAR-SRC-FUEL-001", "不涉及")
        for index, kind in enumerate(CARBONATE_LABELS, 1):
            self.append_by_header(workbook, "烟气脱硫", {
                "核算单元": "C2完整表", "设施名称": f"设施{index}", "碳酸盐种类": kind,
                "碳酸盐用量（t）": 1,
            })
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, tuple(issue.message for issue in unit.errors))
        factors = [component.emission_factor for facility in unit.input_value.fgd_units for component in facility.components]
        self.assertEqual(len(factors), 11)
        for factor in factors:
            self.assertEqual(factor.source_kind.value, "STANDARD_SPECIFIED")
            self.assertEqual(factor.source_id, "SRC-32151-34-2024")
            self.assertTrue(factor.source_version)
            self.assertIn("C.2", factor.source_location)

        from packages.standards.carbon_material import saturated_steam_enthalpy, superheated_steam_enthalpy
        for pressure in (Decimal("1.7"), Decimal("1.8")):
            enthalpy, interpolated, _endpoints = saturated_steam_enthalpy(pressure)
            self.assertIsInstance(enthalpy, Decimal)
            self.assertFalse(interpolated)
        self.assertEqual(saturated_steam_enthalpy("1.70")[0], Decimal("2793.8"))
        superheated_anchor, superheated_interpolated, superheated_endpoints = superheated_steam_enthalpy("1.5", "325")
        self.assertGreater(superheated_anchor, Decimal("3000"))
        self.assertTrue(superheated_interpolated)
        self.assertEqual(superheated_endpoints, (Decimal("1"), Decimal("3")))
        self.assertEqual(superheated_steam_enthalpy("1", "300")[0], Decimal("3051.3"))

        workbook = self.new_book()
        self.add_unit(workbook, "蒸汽锚点")
        self.set_source_status(workbook, "蒸汽锚点", "CAR-SRC-FUEL-001", "不涉及")
        self.set_source_status(workbook, "蒸汽锚点", "CAR-SRC-PURCHASED-HEAT-001", "涉及")
        for index, steam, pressure, temperature in (
            (1, "饱和蒸汽", Decimal("1.75"), None),
            (2, "过热蒸汽", Decimal("1.5"), Decimal("325")),
        ):
            self.append_by_header(workbook, "热力", {
                "核算单元": "蒸汽锚点", "方向": "购入", "热力数量（kg）": 1000,
                "蒸汽类型": steam, "压力（MPa）": pressure, "温度（℃）": temperature,
                "排放因子（tCO₂/GJ）": Decimal("0.11"), "参数来源编号": f"蒸汽因子-{index}",
            })
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        steam_unit = preview.units[0]
        self.assertTrue(steam_unit.can_calculate, tuple(issue.message for issue in steam_unit.errors))
        self.assertEqual(len(steam_unit.input_value.purchased_heat), 2)
        self.assertTrue(any("线性内插" in warning.message for warning in steam_unit.warnings))

    def test_significant_digit_count_keeps_serialized_trailing_zeroes(self) -> None:
        self.assertEqual(significant_digit_count(Decimal("0")), 1)
        self.assertEqual(significant_digit_count(Decimal("0.0012300")), 5)
        self.assertEqual(significant_digit_count(Decimal("123456789012345")), 15)
        self.assertEqual(significant_digit_count(Decimal("1.234567890123456")), 16)
        self.assertEqual(significant_digit_count(Decimal("1E-6")), 1)
        self.assertEqual(significant_digit_count(Decimal("1.2300E+4")), 5)

    def test_nonfinite_raw_numeric_lexeme_is_rejected_even_if_openpyxl_loads_none(self) -> None:
        from openpyxl import Workbook

        cell = Workbook().active["A1"]
        ctx = _UnitContext("单元", "u", self._unit_type(), "e", "企业", None, False, (), False, False)
        reader = _CellReader({("测试", "A1"): "NaN"})
        self.assertIsNone(reader.number(ctx, "测试", 1, cell))
        self.assertEqual(ctx.errors[-1].code, "EXCEL-NUMBER-NONFINITE")
        self.assertEqual(reader.evidence[0].serialized_numeric_text, "NaN")
        for nonfinite in ("Infinity", "-Infinity"):
            context = _UnitContext("单元", "u", self._unit_type(), "e", "企业", None, False, (), False, False)
            reader = _CellReader({("测试", "A1"): nonfinite})
            self.assertIsNone(reader.number(context, "测试", 1, cell))
            self.assertEqual(context.errors[-1].code, "EXCEL-NUMBER-NONFINITE")

    @staticmethod
    def _unit_type():
        from packages.application.project_workspaces import AccountingUnitType
        return AccountingUnitType.WHOLE_SITE

    def test_unknown_metadata_or_missing_core_sheet_is_workbook_fatal(self) -> None:
        workbook = self.new_book()
        workbook["__metadata__"]["B2"] = "9.0"
        path = self.save_book(workbook)
        with self.assertRaises(WorkbookFatalError):
            ExcelWorkbookImporter(self.resolver).import_preview(path)

        workbook = self.new_book()
        workbook.remove(workbook["电力"])
        path = self.save_book(workbook)
        with self.assertRaises(WorkbookFatalError):
            ExcelWorkbookImporter(self.resolver).import_preview(path)

    def test_runtime_template_data_validation_does_not_change_ingress_authority(self) -> None:
        workbook = load_workbook(BytesIO(create_template_bytes()), data_only=False)
        self.assertGreater(len(workbook["化石燃料"].data_validations.dataValidation), 0)
        self.assertEqual(workbook["化石燃料"]["F2"].number_format, "0.00%")
        workbook.close()

    def test_ui_preview_displays_business_result_breakdown_and_cell_locations(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "预览单元")
        self.add_fuel(workbook, "预览单元", Decimal("1"), fuel=FuelType.DIESEL, path="质量")
        path = self.save_book(workbook)
        page = ExcelImportPage(catalog_service=self.catalog_service)
        page.file_input.setText(str(path))
        with patch("packages.ui.pages.QMessageBox.information") as information:
            page._preview_workbook()
        displayed = information.call_args.args[2]
        self.assertIn("直接排放：", displayed)
        self.assertIn("净间接排放：", displayed)
        self.assertIn("排放总量：", displayed)
        self.assertNotIn("CAR-", displayed)
        issue = type("Issue", (), {"location": "化石燃料!D2", "message": "请输入有效数值。"})()
        self.assertEqual(page._format_excel_issue(issue, "· "), "· 化石燃料!D2：请输入有效数值。")
        internal_issue = type("Issue", (), {
            "location": "排放源!C2", "message": "排放源 CAR-SRC-FUEL-001 已标记涉及但缺少输入。"
        })()
        display_text = page._format_excel_issue(internal_issue, "· ")
        self.assertIn("化石燃料", display_text)
        self.assertNotIn("CAR-", display_text)
        page.close()

    def test_gui_and_excel_equivalent_canonical_fuel_share_fingerprint_and_calculation(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "企业A")
        self.add_fuel(workbook, "企业A", Decimal("1.25"), fuel=FuelType.DIESEL, path="质量")
        path = self.save_book(workbook)
        excel_preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        excel_input = excel_preview.units[0].input_value
        self.assertTrue(excel_preview.units[0].can_calculate)

        page = CarbonMaterialAccountingPage(
            catalog_service=self.catalog_service,
            record_repository=InMemoryRecordRepository(),
        )
        page.enterprise_name.setText("示例企业")
        page.boundary_confirmed.setChecked(True)
        for source_id, combo in page._source_statuses.items():
            target = EmissionSourceStatus.INVOLVED if source_id == SOURCE_FUEL else EmissionSourceStatus.NOT_INVOLVED
            combo.setCurrentIndex(combo.findData(target))
        row = page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.DIESEL))
        row.activity.setText("1.25")
        gui_input = page._input(increment=False, render_electricity=False)
        page.close()

        excel_fuel = excel_input.fuel_inputs[0]
        gui_fuel = replace(gui_input.fuel_inputs[0], fuel_id=excel_fuel.fuel_id)
        gui_equivalent = replace(
            gui_input,
            enterprise_id=excel_input.enterprise_id,
            boundary_component_ids=excel_input.boundary_component_ids,
            fuel_inputs=(gui_fuel,),
        )
        # This is the same fingerprint function used by the existing GUI result snapshot.
        self.assertEqual(
            CarbonMaterialAccountingPage._fingerprint_business_input(excel_input, scope="calculation"),
            CarbonMaterialAccountingPage._fingerprint_business_input(gui_equivalent, scope="calculation"),
        )
        excel_outcome = CarbonMaterialCalculator(parameter_resolver=self.resolver, record_repository=InMemoryRecordRepository()).calculate(excel_input)
        gui_outcome = CarbonMaterialCalculator(parameter_resolver=self.resolver, record_repository=InMemoryRecordRepository()).calculate(gui_equivalent)
        self.assertEqual(excel_outcome.result.total_amount, gui_outcome.result.total_amount)

        changed_workbook = self.new_book()
        self.add_unit(changed_workbook, "企业A")
        self.add_fuel(changed_workbook, "企业A", Decimal("1.26"), fuel=FuelType.DIESEL, path="质量")
        changed_path = self.save_book(changed_workbook)
        changed_input = ExcelWorkbookImporter(self.resolver).import_preview(changed_path).units[0].input_value
        excel_normalized = replace(
            excel_input,
            enterprise_id="enterprise.test",
            boundary_component_ids=("boundary.test",),
            fuel_inputs=(replace(excel_input.fuel_inputs[0], fuel_id="fuel.test"),),
        )
        changed_normalized = replace(
            changed_input,
            enterprise_id="enterprise.test",
            boundary_component_ids=("boundary.test",),
            fuel_inputs=(replace(changed_input.fuel_inputs[0], fuel_id="fuel.test"),),
        )
        self.assertNotEqual(
            CarbonMaterialAccountingPage._fingerprint_business_input(excel_normalized, scope="calculation"),
            CarbonMaterialAccountingPage._fingerprint_business_input(changed_normalized, scope="calculation"),
        )
        changed_result = CarbonMaterialCalculator(parameter_resolver=self.resolver, record_repository=InMemoryRecordRepository()).calculate(changed_input).result
        self.assertNotEqual(excel_outcome.result.total_amount, changed_result.total_amount)

    def test_excel_adapter_imports_without_qt_or_widget_dependencies(self) -> None:
        root = str(Path(__file__).parents[1])
        script = "import sys; import packages.excel.gbt32151_34_v1; print('PySide6' in sys.modules)"
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=root, capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), "False")

    def test_evidence_is_shared_and_numeric_cell_provenance_is_preserved(self) -> None:
        workbook = self.new_book()
        self.add_unit(workbook, "证据单元")
        workbook["证据来源"].append(("证据单元", "电表月报", "活动数据", "燃料活动量", "化石燃料", "MTR-2025-01", "配电室", "电表抄录", "电表-1", "0.5级", "月", "2025-01", None, "原件归档"))
        self.add_fuel(workbook, "证据单元", Decimal("1.25"), activity_evidence="电表月报")
        path = self.save_book(workbook)
        preview = ExcelWorkbookImporter(self.resolver).import_preview(path)
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate)
        self.assertEqual(len(unit.input_value.reporting_data.activity_evidence), 1)
        self.assertTrue(unit.input_value.fuel_inputs[0].activity.evidence_ref_ids)
        evidence = next(item for item in preview.numeric_evidence if item.sheet == "化石燃料")
        self.assertEqual(evidence.raw_cell_type, "n")
        self.assertEqual(evidence.normalized_decimal, Decimal("1.25"))
        self.assertIsNone(unit.calculation.record)
        self.assertEqual(len(preview.provenance.workbook_sha256), 64)


if __name__ == "__main__":
    unittest.main()
