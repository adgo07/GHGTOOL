from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree

from openpyxl import load_workbook

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.excel.r2 import (
    ELECTRICITY_HEADERS,
    FGD_HEADERS,
    FUEL_HEADERS,
    FUME_HEADERS,
    HEAT_HEADERS,
    MATERIAL_HEADERS,
    METADATA_SHEET,
    SOURCE_IDS,
    UNIT_HEADERS,
    ExcelWorkbookImporter,
    WorkbookFatalError,
    create_template_bytes,
)
from packages.persistence.catalog_builder import build_catalog_database
from packages.persistence.catalog_repository import SQLiteCatalogRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    EmissionSourceStatus,
    FuelPath,
    FuelType,
    ParameterSourceKind,
)


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _set_row(sheet, headers: tuple[str, ...], row: int, values: dict[str, object]) -> None:
    for header, value in values.items():
        try:
            column = headers.index(header) + 1
        except ValueError as exc:
            raise AssertionError(f"unknown template header: {header}") from exc
        sheet.cell(row, column, value)


def _rewrite_numeric_lexeme(path: Path, sheet_name: str, cell_reference: str, lexical_value: str) -> None:
    """Change only the saved OOXML number text, as Excel/LibreOffice would store it."""
    output = BytesIO()
    with ZipFile(path, "r") as original:
        workbook_root = ElementTree.fromstring(original.read("xl/workbook.xml"))
        rels_root = ElementTree.fromstring(original.read("xl/_rels/workbook.xml.rels"))
        targets = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in rels_root.findall(f"{{{_PKG_REL_NS}}}Relationship")
        }
        member = None
        for node in workbook_root.findall(f"{{{_MAIN_NS}}}sheets/{{{_MAIN_NS}}}sheet"):
            if node.attrib["name"] == sheet_name:
                target = targets[node.attrib[f"{{{_REL_NS}}}id"]]
                member = target.lstrip("/") if target.startswith("/") else target
                if not member.startswith("xl/"):
                    member = f"xl/{member}"
                break
        if member is None:
            raise AssertionError(f"worksheet not found in OOXML: {sheet_name}")

        with ZipFile(output, "w", ZIP_DEFLATED) as rewritten:
            for info in original.infolist():
                data = original.read(info.filename)
                if info.filename == member:
                    sheet_root = ElementTree.fromstring(data)
                    cell = sheet_root.find(f".//{{{_MAIN_NS}}}c[@r='{cell_reference}']")
                    value = cell.find(f"{{{_MAIN_NS}}}v") if cell is not None else None
                    if value is None:
                        raise AssertionError(f"test cell has no saved number: {sheet_name}!{cell_reference}")
                    value.text = lexical_value
                    data = ElementTree.tostring(sheet_root, encoding="utf-8", xml_declaration=True)
                rewritten.writestr(info, data)
    path.write_bytes(output.getvalue())


def _outcome_value_semantics(outcome):
    result = outcome.result
    result_values = None if result is None else (
        result.standard_id,
        result.algorithm_version,
        tuple(
            (line.emission_source_id, line.greenhouse_gas_id, line.amount, line.unit)
            for line in result.lines
        ),
        result.total_amount,
        result.total_unit,
    )
    problem_values = tuple(
        (item.code, item.level.value, item.field_id, item.details)
        for item in outcome.problems
    )
    trace_values = tuple(
        (
            item.formula_id,
            item.source_id,
            item.variables,
            item.substitution,
            item.amount,
            item.unit,
            item.standard_location,
            item.mapping_location,
            item.provenance,
        )
        for item in outcome.traces
    )
    snapshot_values = tuple(
        (
            item.parameter_id,
            item.value_used,
            item.unit_used,
            item.source_id,
            item.source_version,
            item.selection_method,
            item.standard_id,
            item.factor_version,
            item.source_location,
            item.factor_id,
            item.factor_year,
        )
        for item in outcome.parameter_snapshots
    )
    return outcome.successful, problem_values, result_values, trace_values, snapshot_values


class MainIntegrationExcelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._catalog_directory = tempfile.TemporaryDirectory()
        catalog_path = Path(cls._catalog_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path)
        cls.resolver = create_g06_parameter_resolver(SQLiteCatalogRepository(catalog_path))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._catalog_directory.cleanup()

    def _new_workbook(self, unit_names: tuple[str, ...] = ("全厂单元",)):
        workbook = load_workbook(BytesIO(create_template_bytes()))
        basic = workbook["基本信息"]
        basic["B3"] = "集成测试企业"
        basic["B4"] = "年度"
        basic["B5"] = "2025-01-01"
        basic["B6"] = "2025-12-31"
        basic["B7"] = "是"
        for row, name in enumerate(unit_names, start=13):
            _set_row(basic, UNIT_HEADERS, row, {
                UNIT_HEADERS[0]: name,
                UNIT_HEADERS[1]: "全厂",
                UNIT_HEADERS[2]: "是",
                UNIT_HEADERS[3]: "已确认边界",
            })
        return workbook

    def _save(self, workbook, directory: str, filename: str = "input.xlsx") -> Path:
        path = Path(directory) / filename
        workbook.save(path)
        workbook.close()
        return path

    def _complete_source_workbook(self):
        workbook = self._new_workbook()
        unit = "全厂单元"

        _set_row(workbook["B.2 化石燃料"], FUEL_HEADERS, 6, {
            FUEL_HEADERS[0]: unit,
            FUEL_HEADERS[1]: "天然气",
            FUEL_HEADERS[2]: "体积",
            FUEL_HEADERS[3]: 1.25,
            FUEL_HEADERS[4]: "计量/仪表记录",
            FUEL_HEADERS[5]: "燃气计量表",
        })

        for sheet_name, rows in (
            ("B.3 原料煅烧", (
                ("待煅烧原料", "煅烧原料", 100, 90, 5),
                ("煅后料", "煅后料", 80, 95, 1),
            )),
            ("B.4 焙烧／炭化", (
                ("待焙烧/炭化品", "生坯", 50, 88, 4),
                ("焙烧/炭化产品", "焙烧品", 45, 92, 2),
            )),
            ("B.5 石墨化", (
                ("待石墨化品", "石墨化生料", 40, 90, 3),
                ("石墨化产品", "石墨产品", 35, 96, 1),
            )),
        ):
            for row, (category, name, mass, fixed, volatile) in enumerate(rows, start=6):
                _set_row(workbook[sheet_name], MATERIAL_HEADERS, row, {
                    MATERIAL_HEADERS[0]: unit,
                    MATERIAL_HEADERS[1]: f"{sheet_name}过程",
                    MATERIAL_HEADERS[2]: category,
                    MATERIAL_HEADERS[3]: name,
                    MATERIAL_HEADERS[4]: mass,
                    MATERIAL_HEADERS[5]: fixed,
                    MATERIAL_HEADERS[6]: "实测值",
                    MATERIAL_HEADERS[7]: volatile,
                    MATERIAL_HEADERS[8]: "实测值",
                })

        _set_row(workbook["B.6 烟气焚烧"], FUME_HEADERS, 6, {
            FUME_HEADERS[0]: unit,
            FUME_HEADERS[1]: "焚烧设施一",
            FUME_HEADERS[2]: 100,
            FUME_HEADERS[3]: 100,
            FUME_HEADERS[4]: 10,
            FUME_HEADERS[5]: Decimal("0.014"),
            FUME_HEADERS[6]: Decimal("0.98"),
            FUME_HEADERS[7]: 365,
            FUME_HEADERS[8]: "检测报告",
            FUME_HEADERS[9]: "烟气监测报告",
            FUME_HEADERS[10]: "实测值",
            FUME_HEADERS[11]: "焚烧参数报告",
        })

        _set_row(workbook["B.7 烟气脱硫"], FGD_HEADERS, 6, {
            FGD_HEADERS[0]: unit,
            FGD_HEADERS[1]: "脱硫设施一",
            FGD_HEADERS[2]: "CaCO₃",
            FGD_HEADERS[3]: 2,
        })

        _set_row(workbook["B.8 电力"], ELECTRICITY_HEADERS, 6, {
            ELECTRICITY_HEADERS[0]: unit,
            ELECTRICITY_HEADERS[1]: "购入",
            ELECTRICITY_HEADERS[2]: 100,
            ELECTRICITY_HEADERS[4]: "结算记录",
            ELECTRICITY_HEADERS[5]: "电费单",
            ELECTRICITY_HEADERS[8]: "购入",
            ELECTRICITY_HEADERS[9]: "常规",
            ELECTRICITY_HEADERS[10]: "无",
            ELECTRICITY_HEADERS[11]: "未提供",
        })
        _set_row(workbook["B.8 电力"], ELECTRICITY_HEADERS, 7, {
            ELECTRICITY_HEADERS[0]: unit,
            ELECTRICITY_HEADERS[1]: "输出",
            ELECTRICITY_HEADERS[2]: 2,
            ELECTRICITY_HEADERS[3]: Decimal("0.5"),
            ELECTRICITY_HEADERS[4]: "计量/仪表记录",
            ELECTRICITY_HEADERS[5]: "输出电量记录",
            ELECTRICITY_HEADERS[6]: "实测值",
            ELECTRICITY_HEADERS[7]: "输出电力因子报告",
        })

        for row, direction, amount, factor, reference in (
            (6, "购入", 1000, Decimal("0.11"), "购入热力因子报告"),
            (7, "输出", 250, Decimal("0.12"), "输出热力因子报告"),
        ):
            _set_row(workbook["B.9 热力"], HEAT_HEADERS, row, {
                HEAT_HEADERS[0]: unit,
                HEAT_HEADERS[1]: direction,
                HEAT_HEADERS[2]: amount,
                HEAT_HEADERS[3]: "饱和蒸汽",
                HEAT_HEADERS[4]: 2675,
                HEAT_HEADERS[7]: factor,
                HEAT_HEADERS[8]: "结算记录",
                HEAT_HEADERS[9]: f"{direction}热力结算单",
                HEAT_HEADERS[10]: "实测值",
                HEAT_HEADERS[11]: reference,
            })
        return workbook

    def test_each_b2_to_b9_sheet_maps_current_headers_into_domain_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(self._complete_source_workbook(), directory)
            preview = ExcelWorkbookImporter(self.resolver).import_preview(path)

        self.assertEqual(len(preview.units), 1)
        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, tuple((item.code, item.message) for item in unit.errors))
        value = unit.input_value
        self.assertEqual(len(value.fuel_inputs), 1)
        self.assertIs(value.fuel_inputs[0].fuel_type, FuelType.NATURAL_GAS)
        self.assertIs(value.fuel_inputs[0].path, FuelPath.VOLUME)
        self.assertEqual(value.fuel_inputs[0].activity.value, Decimal("1.25"))

        self.assertEqual(len(value.calcinations), 1)
        self.assertEqual(tuple(item.mass_t for item in value.calcinations[0].material_rows), (Decimal("100"), Decimal("80")))
        self.assertEqual(len(value.bakings), 1)
        self.assertEqual(tuple(item.role.value for item in value.bakings[0].material_rows), ("green_baking_product", "baked_product"))
        self.assertEqual(len(value.graphitizations), 1)
        self.assertEqual(tuple(item.role.value for item in value.graphitizations[0].material_rows), ("green_graphitization_product", "graphitized_product"))

        self.assertEqual(len(value.fume_incinerations), 1)
        self.assertEqual(value.fume_incinerations[0].q.value, Decimal("100"))
        self.assertEqual(value.fume_incinerations[0].fch.value, Decimal("0.014"))
        self.assertEqual(len(value.fgd_units), 1)
        self.assertEqual(value.fgd_units[0].components[0].carbonate_type, "CaCO₃")
        self.assertEqual(value.fgd_units[0].components[0].amount.value, Decimal("2"))

        self.assertEqual(len(value.electricity_details), 1)
        self.assertEqual(value.electricity_details[0].electricity_amount, Decimal("100"))
        self.assertEqual(len(value.exported_electricity), 1)
        self.assertEqual(value.exported_electricity[0].amount.value, Decimal("2"))
        self.assertEqual(value.exported_electricity[0].factor.value, Decimal("0.5"))
        self.assertEqual(len(value.purchased_heat), 1)
        self.assertEqual(value.purchased_heat[0].amount.value, Decimal("1000"))
        self.assertEqual(value.purchased_heat[0].enthalpy.value, Decimal("2675"))
        self.assertEqual(value.purchased_heat[0].factor.value, Decimal("0.11"))
        self.assertEqual(len(value.exported_heat), 1)
        self.assertEqual(value.exported_heat[0].amount.value, Decimal("250"))
        self.assertEqual(value.exported_heat[0].factor.value, Decimal("0.12"))

        states = {item.source_id: item.status for item in value.source_states}
        self.assertEqual(set(states), set(SOURCE_IDS))
        self.assertTrue(all(item is EmissionSourceStatus.INVOLVED for item in states.values()))

    def test_all_source_preview_matches_shared_calculator_full_values_not_a_golden_case(self) -> None:
        """Adapter/domain value parity only; this fixture is not an RS04 Golden Case."""
        with tempfile.TemporaryDirectory() as directory:
            path = self._save(self._complete_source_workbook(), directory)
            preview = ExcelWorkbookImporter(self.resolver).import_preview(path)

        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, tuple((item.code, item.message) for item in unit.errors))
        reference = CarbonMaterialCalculator(
            parameter_resolver=self.resolver,
        ).calculate(unit.input_value, calculated_at=preview.provenance.imported_at)
        self.assertTrue(reference.successful, reference.problems)
        self.assertEqual(_outcome_value_semantics(unit.calculation), _outcome_value_semantics(reference))
        self.assertIsNone(unit.calculation.record)

    def test_one_bad_unit_does_not_block_a_valid_unit_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workbook = self._new_workbook(("有效单元", "错误单元"))
            _set_row(workbook["B.2 化石燃料"], FUEL_HEADERS, 6, {
                FUEL_HEADERS[0]: "有效单元",
                FUEL_HEADERS[1]: "天然气",
                FUEL_HEADERS[2]: "体积",
                FUEL_HEADERS[3]: 0,
            })
            _set_row(workbook["B.2 化石燃料"], FUEL_HEADERS, 7, {
                FUEL_HEADERS[0]: "错误单元",
                FUEL_HEADERS[1]: "天然气",
                FUEL_HEADERS[2]: "体积",
                FUEL_HEADERS[3]: "=1+1",
            })
            path = self._save(workbook, directory)
            preview = ExcelWorkbookImporter(self.resolver).import_preview(path)

        by_name = {item.name: item for item in preview.units}
        self.assertEqual(set(by_name), {"有效单元", "错误单元"})
        self.assertTrue(by_name["有效单元"].can_calculate, by_name["有效单元"].errors)
        self.assertEqual(by_name["有效单元"].result.total_amount, Decimal(0))
        self.assertEqual(by_name["有效单元"].errors, ())
        self.assertFalse(by_name["错误单元"].can_calculate)
        self.assertIsNone(by_name["错误单元"].result)
        self.assertIn(
            ("EXCEL-FORMULA-REJECTED", "B.2 化石燃料!D7"),
            {(item.code, item.location) for item in by_name["错误单元"].errors},
        )

    def test_unrecognized_metadata_and_missing_required_sheet_are_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for case in ("metadata", "sheet"):
                with self.subTest(case=case):
                    workbook = self._new_workbook()
                    if case == "metadata":
                        metadata = workbook[METADATA_SHEET]
                        for row in range(1, metadata.max_row + 1):
                            if metadata.cell(row, 1).value == "template_version":
                                metadata.cell(row, 2).value = "unsupported"
                                break
                        else:
                            self.fail("template_version metadata field missing")
                    else:
                        del workbook["B.9 热力"]
                    path = self._save(workbook, directory, f"{case}.xlsx")
                    with self.assertRaises(WorkbookFatalError):
                        ExcelWorkbookImporter(self.resolver).import_preview(path)

    def test_ooxml_nan_and_infinity_values_are_rejected_by_real_import_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for index, lexeme in enumerate(("NaN", "Infinity", "-Infinity")):
                with self.subTest(lexeme=lexeme):
                    workbook = self._new_workbook()
                    _set_row(workbook["B.2 化石燃料"], FUEL_HEADERS, 6, {
                        FUEL_HEADERS[0]: "全厂单元",
                        FUEL_HEADERS[1]: "天然气",
                        FUEL_HEADERS[2]: "体积",
                        FUEL_HEADERS[3]: 1,
                    })
                    path = self._save(workbook, directory, f"nonfinite-{index}.xlsx")
                    _rewrite_numeric_lexeme(path, "B.2 化石燃料", "D6", lexeme)
                    try:
                        unit = ExcelWorkbookImporter(self.resolver).import_preview(path).units[0]
                    except WorkbookFatalError as exc:
                        # The bundled openpyxl may reject these malformed numeric
                        # lexemes before the adapter can report a cell-level error.
                        self.assertIn("结构无法解析", str(exc))
                    else:
                        self.assertIn("EXCEL-NUMBER-NONFINITE", {item.code for item in unit.errors})
                        self.assertFalse(unit.can_calculate)
                        self.assertIsNone(unit.result)

    def test_saved_numeric_lexemes_and_custom_parameters_keep_exact_decimal_value(self) -> None:
        expected = {
            "D6": "1.23000000000000",
            "G6": "389.123456789012",
            "J6": "0.01234567890123",
            "M6": "0.98765432109876",
        }
        with tempfile.TemporaryDirectory() as directory:
            workbook = self._new_workbook()
            _set_row(workbook["B.2 化石燃料"], FUEL_HEADERS, 6, {
                FUEL_HEADERS[0]: "全厂单元",
                FUEL_HEADERS[1]: "天然气",
                FUEL_HEADERS[2]: "体积",
                FUEL_HEADERS[3]: 1,
                FUEL_HEADERS[4]: "计量/仪表记录",
                FUEL_HEADERS[5]: "燃气计量表",
                FUEL_HEADERS[6]: 389,
                FUEL_HEADERS[7]: "实测值",
                FUEL_HEADERS[8]: "低位发热量报告",
                FUEL_HEADERS[9]: Decimal("0.01"),
                FUEL_HEADERS[10]: "实测值",
                FUEL_HEADERS[11]: "含碳量报告",
                FUEL_HEADERS[12]: Decimal("0.98"),
                FUEL_HEADERS[13]: "实测值",
                FUEL_HEADERS[14]: "氧化率报告",
            })
            path = self._save(workbook, directory)
            for cell_reference, lexeme in expected.items():
                _rewrite_numeric_lexeme(path, "B.2 化石燃料", cell_reference, lexeme)
            preview = ExcelWorkbookImporter(self.resolver).import_preview(path)

        unit = preview.units[0]
        self.assertTrue(unit.can_calculate, tuple((item.code, item.message) for item in unit.errors))
        evidence = {(item.sheet, item.cell): item for item in preview.numeric_evidence}
        fuel = unit.input_value.fuel_inputs[0]
        consumed = {
            "D6": fuel.activity.value,
            "G6": fuel.lower_heating_value.value,
            "J6": fuel.carbon_content.value,
            "M6": fuel.oxidation_rate.value,
        }
        for cell_reference, lexeme in expected.items():
            with self.subTest(cell=cell_reference):
                item = evidence[("B.2 化石燃料", cell_reference)]
                self.assertEqual(item.serialized_numeric_text, lexeme)
                self.assertEqual(str(item.normalized_decimal), lexeme)
                self.assertEqual(str(consumed[cell_reference]), lexeme)
        self.assertIs(fuel.lower_heating_value.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(fuel.carbon_content.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(fuel.oxidation_rate.source_kind, ParameterSourceKind.MEASURED)


if __name__ == "__main__":
    unittest.main()
