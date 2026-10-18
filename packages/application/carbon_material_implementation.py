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

    @staticmethod
    def can_upgrade_workspace(workspace):
        return any(getattr(unit.canonical_input, "material_execution_version", None) == "MATERIAL_V1"
                   or any(batch.execution_version != "FGD_V2" for batch in getattr(unit.canonical_input, "fgd_units", ()))
                   or (getattr(unit.canonical_input,"fume_incinerations",()) and getattr(unit.canonical_input,"fume_execution_version","FUME_V1") != "FUME_V2")
                   for unit in workspace.units)

    @staticmethod
    def upgrade_workspace(workspace):
        from dataclasses import replace
        from uuid import uuid4
        from packages.standards.carbon_material import CarbonMaterialInput
        units = []
        unit_ids = {unit.unit_id: f"unit.{uuid4().hex}" for unit in workspace.units}
        for unit in workspace.units:
            value = unit.canonical_input
            if value is not None:
                if not isinstance(value, CarbonMaterialInput) or value.material_execution_version not in {"MATERIAL_V1", "MATERIAL_V2"}:
                    raise ValueError("此项目材料执行组合不支持自动升级；原项目未修改。")
                upgraded_batches = []
                for batch in value.fgd_units:
                    if batch.execution_version not in {"FGD_V1", "FGD_V2"}:
                        raise ValueError("脱硫执行版本未知，原项目未修改。")
                    if batch.execution_version == "FGD_V1":
                        from packages.core.decimal_policy import DecimalPolicy
                        from packages.core.units import UnitService
                        units_service = UnitService(DecimalPolicy())
                        amounts = [units_service.convert(component.amount.value, component.amount.unit, "t")
                                   if component.amount is not None else None for component in batch.components]
                        if amounts and (any(amount is None for amount in amounts) or any(amount != amounts[0] for amount in amounts)):
                            raise ValueError("旧组分用量不同，请先确认本批整剂净耗量，原项目未修改。")
                        batch = replace(batch, facility_id=uuid4().hex, batch_id=uuid4().hex,
                            components=tuple(replace(component, component_id=uuid4().hex) for component in batch.components), execution_version="FGD_V2")
                    upgraded_batches.append(batch)
                value = replace(value, material_execution_version="MATERIAL_V2", fume_execution_version="FUME_V2", fgd_units=tuple(upgraded_batches), fgd=upgraded_batches[0] if len(upgraded_batches)==1 else None)
            units.append(replace(unit, unit_id=unit_ids[unit.unit_id], canonical_input=value, result_snapshot=None, input_fingerprint=None))
        return replace(workspace, project_id=f"project.{uuid4().hex}", name=workspace.name + "（输入规则升级副本）", active_unit_id=unit_ids[workspace.active_unit_id], units=tuple(units))

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
    from .reporting.carbon_material_model import _build_carbon_material_report_model
    return _build_carbon_material_report_model(*args, **kwargs)

def accepts_input(value):
    from packages.standards.carbon_material import CarbonMaterialInput
    return isinstance(value,CarbonMaterialInput)


def input_codec():
    from . import carbon_material_input_codec
    return carbon_material_input_codec


CARBON_MATERIAL_IMPLEMENTATION = StandardImplementation(
    standard_id="gbt_32151_34_2024", version="2024", title="GB/T 32151.34—2024", editor_key="carbon_material",
    calculator_factory=create_calculator, excel_factory=CarbonMaterialExcel, report_factory=create_report, accepts_input=accepts_input, input_codec_factory=input_codec,
    reference_providers=(("CARBON_MATERIAL_C4", steam_reference_view), ("CARBON_MATERIAL_C5", steam_reference_view)),
)
