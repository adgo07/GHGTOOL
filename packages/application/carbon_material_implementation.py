"""The one currently implemented standard, adapted to local dispatch."""
from .standard_registry import StandardImplementation

def create_calculator(catalog):
    from .carbon_accounting import create_g06_parameter_resolver
    from packages.standards.carbon_material import CarbonMaterialCalculator
    return CarbonMaterialCalculator(
        parameter_resolver=create_g06_parameter_resolver(catalog.repository),
        standard_version=catalog.standard_version("gbt_32151_34_2024") or "2024",
        standard_implementation_date=catalog.standard_implementation_date("gbt_32151_34_2024"),
        reference_data_identity_provider=catalog.reference_data_identity,
    )

class CarbonMaterialExcel:
    template_button_label = "下载附录 B 填报模板"
    template_description = "使用 GB/T 32151.34—2024 附录 B 模板，填写 B.2～B.9 活动数据。"
    template_dialog_title = "保存 GB/T 32151.34—2024 附录 B 模板"
    template_filename = "GB_T_32151_34_2024_Appendix_B.xlsx"
    path_error_code = "EXB01_FUEL_PATH_REQUIRED"

    def __init__(self, catalog, preview):
        from packages.excel.templates import ExcelTemplateService
        self.catalog = catalog
        self.preview = preview
        self.templates = ExcelTemplateService.default()

    def context(self, **values):
        from packages.excel.appendix_b import AppendixBImportContext
        return AppendixBImportContext(**values)

    def import_preview(self, path, context):
        from packages.excel.appendix_b import AppendixBWorkbookImporter
        return AppendixBWorkbookImporter(preview_use_case=self.preview, catalog_service=self.catalog).import_preview(path, context=context)

    def regions(self, period):
        from .uat03_parameter_queries import UAT03ParameterQueries
        resolver = self.preview.calculator.parameter_resolver
        return UAT03ParameterQueries(self.catalog, resolver).electricity_regions(period) if resolver is not None else ()

    @property
    def path_labels(self):
        from packages.standards.carbon_material import FuelPath
        return {FuelPath.VOLUME: "体积计量", FuelPath.MASS: "质量计量"}

    def parse_path(self, value):
        from packages.standards.carbon_material import FuelPath
        try:
            return FuelPath(value)
        except (TypeError, ValueError):
            return None

def steam_reference_view(table, source_label):
    from packages.standards.carbon_material import ALGORITHM_VERSION, steam_reference_table_rows
    values = steam_reference_table_rows(table.display_number)
    if table.provider_id == "CARBON_MATERIAL_C4":
        rows = tuple((format(pressure, "f"), format(enthalpy, "f")) for pressure, enthalpy in values)
        headers = tuple(column.label for column in table.columns)
    else:
        temperatures = tuple(sorted({row[0] for row in values}))
        pressures = tuple(sorted({row[1] for row in values}))
        lookup = {(temperature, pressure): enthalpy for temperature, pressure, enthalpy in values}
        headers = (table.columns[0].label, *(f"{pressure:g} MPa" for pressure in pressures))
        rows = tuple((format(temperature, "f"), *(format(lookup[(temperature, pressure)], "f") for pressure in pressures)) for temperature in temperatures)
    note = f"来源：{source_label} {table.source_location}。只读数据来自版本化计算器（{ALGORITHM_VERSION}）。{table.notes}"
    return headers, rows, note

def create_report(*args, **kwargs):
    from .reporting.model import _build_carbon_material_report_model
    return _build_carbon_material_report_model(*args, **kwargs)

CARBON_MATERIAL_IMPLEMENTATION = StandardImplementation(
    standard_id="gbt_32151_34_2024", version="2024", title="GB/T 32151.34—2024", editor_key="carbon_material",
    calculator_factory=create_calculator, excel_factory=CarbonMaterialExcel, report_factory=create_report,
    reference_providers=(("CARBON_MATERIAL_C4", steam_reference_view), ("CARBON_MATERIAL_C5", steam_reference_view)),
)
