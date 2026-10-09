"""GB/T 32151.34—2024 Appendix B Excel ingress adapter."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
import re
from io import BytesIO
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from packages.application.project_workspaces import AccountingUnitType
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.core.decimal_policy import DecimalPolicy
from packages.core.models import (
    AccountingPeriod, ActivityDataSource, ElectricityAcquisitionMode,
    ElectricityAttribute, ElectricityProofStatus, ElectricityProofType,
    ParameterType, ValueType,
)
from packages.core.parameter_resolution import (
    ElectricityConsumptionDetail, ParameterResolutionContext,
    UserProvidedParameterValue,
)
from packages.standards.carbon_material import (
    STANDARD_ID, STANDARD_VERSION, BakingInput, CalcinationInput,
    CarbonMaterialInput, CarbonReportingData, CarbonateComponent,
    EmissionSourceState, EmissionSourceStatus, ElectricityOutputLine,
    FGDInput, FuelInput, FuelPath, FuelType, FumeIncinerationInput,
    GraphitizationInput, HeatFactorMode, HeatInput, InputValue,
    ParameterSourceKind, ParameterValue, SteamKind,
    SOURCE_BAKING, SOURCE_CALCINATION, SOURCE_EXPORTED_ELECTRICITY,
    SOURCE_EXPORTED_HEAT, SOURCE_FGD, SOURCE_FUME, SOURCE_FUEL,
    SOURCE_GRAPHITIZATION, SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_PURCHASED_HEAT,
)
from packages.standards.carbon_material_normalization import MaterialDataSource, MaterialRole, MaterialInputLine
from packages.excel.ingress import (
    ImportMessage, UnitCalculationPreview, WorkbookCellReader,
    WorkbookFatalError, WorkbookImportPreview, WorkbookProvenance,
    read_worksheet_numeric_lexemes,
)
from packages.excel.templates import ExcelTemplateService


EXCEL_APPENDIX_B = "EXCEL_APPENDIX_B"
INGRESS_POLICY_ID = "GHGTOOL_EXCEL_APPENDIX_B_V1"
_SOURCE_IDS = (
    SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING, SOURCE_GRAPHITIZATION,
    SOURCE_FUME, SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_EXPORTED_ELECTRICITY, SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_HEAT,
)
_FUEL_TYPES = {
    "无烟煤": FuelType.ANTHRACITE, "烟煤": FuelType.BITUMINOUS_COAL,
    "褐煤": FuelType.LIGNITE, "其他煤制品": FuelType.OTHER_COAL_PRODUCTS,
    "燃料油": FuelType.FUEL_OIL, "汽油": FuelType.GASOLINE,
    "柴油": FuelType.DIESEL, "液化天然气": FuelType.LIQUEFIED_NATURAL_GAS,
    "液化石油气": FuelType.LIQUEFIED_PETROLEUM_GAS,
    "其他石油制品": FuelType.OTHER_PETROLEUM_PRODUCTS,
    "天然气": FuelType.NATURAL_GAS, "高炉煤气": FuelType.BLAST_FURNACE_GAS,
    "焦炉煤气": FuelType.COKE_OVEN_GAS, "其他煤气": FuelType.OTHER_GAS,
    "其他能源品种": FuelType.OTHER,
}
_PROCESS_META = {
    "B.3": (SOURCE_CALCINATION, CalcinationInput, "car-par-k1", "k1", 0),
    "B.4": (SOURCE_BAKING, BakingInput, "car-par-k2", "k2", 1),
    "B.5": (SOURCE_GRAPHITIZATION, GraphitizationInput, "car-par-k3", "k3", 2),
}
_APPENDIX_TABLE_WIDTHS = {
    "B.2": 10,
    "B.3": 5,
    "B.4": 5,
    "B.5": 5,
    "B.6": 7,
    "B.7": 7,
    "B.8": 5,
    "B.9": 7,
}


@dataclass(frozen=True, slots=True)
class AppendixBImportContext:
    period: AccountingPeriod
    boundary_confirmed: bool
    enterprise_name: str | None = None
    enterprise_id: str | None = None
    region: str | None = None
    fuel_path_overrides: Mapping[str, FuelPath] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.period, AccountingPeriod):
            raise ValueError("必须明确选择有效核算期间。")
        if not isinstance(self.boundary_confirmed, bool):
            raise ValueError("必须明确确认核算边界状态。")
        for name in ("enterprise_name", "enterprise_id", "region"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} 不能是空白文字。")
            if value is not None:
                object.__setattr__(self, name, value.strip())
        overrides = dict(self.fuel_path_overrides)
        for location, path in overrides.items():
            if not isinstance(location, str) or not re.fullmatch(r"B\.2!B\d+", location):
                raise ValueError("燃料单位选择必须按 B.2!B<行号> 精确指定。")
            if not isinstance(path, FuelPath):
                raise ValueError("燃料单位选择必须使用 FuelPath。")
        object.__setattr__(self, "fuel_path_overrides", MappingProxyType(overrides))


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}-{sha256(raw).hexdigest()[:20]}"


def _has_value(cell) -> bool:
    return cell.value is not None and cell.value != ""


def _is_appendix_footer_row(worksheet, row: int) -> bool:
    """Recognize only marked footer rows whose merges span the whole table.

    Activity labels are user-editable in several Appendix B tables. Prefix-only
    checks can therefore mistake valid names such as "A Sample Batch" or a
    fuel beginning with "使用提示" for a footer and silently discard activity.
    The approved master marks footer rows with a full-width merge; preserve that
    structure and require one of its known footnote/prompt markers as evidence.
    """
    value = worksheet[f"A{row}"].value
    if not isinstance(value, str):
        return False
    table_width = _APPENDIX_TABLE_WIDTHS.get(worksheet.title)
    if table_width is None:
        return False

    spans = sorted(
        (area.min_col, area.max_col)
        for area in worksheet.merged_cells.ranges
        if area.min_row == row and area.max_row == row
    )
    covered_through = 0
    for first, last in spans:
        if first > covered_through + 1:
            break
        covered_through = max(covered_through, last)
        if covered_through >= table_width:
            break
    if covered_through < table_width:
        return False

    text = value.strip()
    if text.startswith(("使用提示：", "数据提示：", "备注：", "数据来源：")):
        return True
    if text == "排放量（tCO₂）" or text.startswith("排放量自动计算并只读"):
        return True
    return re.match(r"^[ab]\s{2,}(?:若|对于|填写|报告主体)", text) is not None


def _factor_value(factor):
    if factor is None:
        return None
    normalized = getattr(factor, "normalized_value", None)
    return normalized if normalized is not None else getattr(factor, "value", None)


def _domain_factor_unit(factor) -> str:
    unit = getattr(factor, "normalized_unit", None) or factor.unit
    return {
        "tCO₂/MWh": "tCO2/MWh",
        "tCO₂/GJ": "tCO2/GJ",
        "tCO₂/t": "tCO2/t",
    }.get(unit, unit)


def _parameter_value(factor, reason: str, *, unit: str | None = None,
                     source_version: str | None = None) -> ParameterValue:
    kinds = {
        ValueType.STANDARD_DEFAULT: ParameterSourceKind.STANDARD_DEFAULT,
        ValueType.STANDARD_SPECIFIED: ParameterSourceKind.STANDARD_SPECIFIED,
        ValueType.GOVERNMENT_PUBLISHED: ParameterSourceKind.OFFICIAL_PUBLISHED,
        ValueType.MEASURED: ParameterSourceKind.MEASURED,
        ValueType.DERIVED: ParameterSourceKind.CALCULATED,
        ValueType.SYSTEM_CONSTANT: ParameterSourceKind.CALCULATED,
        ValueType.SCIENTIFIC_REFERENCE: ParameterSourceKind.USER_DEFINED,
        ValueType.HISTORICAL: ParameterSourceKind.USER_DEFINED,
    }
    factor_year = getattr(factor, "factor_year", None)
    if source_version is None:
        source_version = getattr(factor, "source_version", None)
        if source_version is None:
            candidate = getattr(factor, "version", None)
            # The Catalog-to-Resolver bridge currently places factor_year in
            # Factor.version. Preserve it as factor_year, not as a source edition.
            if candidate is not None and str(candidate) != str(factor_year):
                source_version = candidate
    parameter_unit = unit or _domain_factor_unit(factor)
    return ParameterValue(
        factor.parameter_id, _factor_value(factor), parameter_unit, kinds[factor.value_type],
        factor.source_id, source_version, factor.source_location, reason,
        factor.factor_id, factor_year,
    )


def _user_parameter(value: Decimal, parameter_id: str, unit: str, location: str,
                    source_kind: ParameterSourceKind = ParameterSourceKind.USER_DEFINED,
                    *, selection_reason: str | None = None) -> ParameterValue:
    return ParameterValue(
        parameter_id=parameter_id, value=value, unit=unit, source_kind=source_kind,
        source_id=None, source_version=None, source_location=location,
        selection_reason=selection_reason or "工作簿提供未核验来源；本次按用户提供值进入现有计算链。",
    )


class AppendixBWorkbookImporter:
    """Convert one approved 9-sheet workbook into one canonical preview unit."""

    def __init__(self, *, preview_use_case, catalog_service,
                 template_service: ExcelTemplateService | None = None) -> None:
        self.policy = DecimalPolicy()
        self.preview_use_case = preview_use_case
        self.catalog_service = catalog_service
        self.template_service = template_service or ExcelTemplateService.default()
        try:
            self._template_numeric_lexemes = read_worksheet_numeric_lexemes(
                self.template_service.read_bytes(STANDARD_ID)
            )
        except (AttributeError, TypeError, ValueError):
            self._template_numeric_lexemes = {}
        self.resolver = getattr(getattr(preview_use_case, "calculator", None), "parameter_resolver", None)
        self.queries = UAT03ParameterQueries(catalog_service, self.resolver) if self.resolver else None
        try:
            repository = catalog_service.repository
            self.parameters = {p.parameter_id.lower(): p for p in repository.list_parameters()}
            self.sources = {source.source_id: source for source in repository.list_sources()}
        except (AttributeError, TypeError):
            self.parameters = {}
            self.sources = {}

    def import_preview(self, file_path: str | Path, *,
                       context: AppendixBImportContext) -> WorkbookImportPreview:
        if not isinstance(context, AppendixBImportContext):
            raise ValueError("必须提供 AppendixBImportContext，并明确核算期间和边界确认状态。")
        path = Path(file_path)
        try:
            content = path.read_bytes()
            canonical_path = str(path.resolve())
        except OSError as exc:
            raise WorkbookFatalError("无法读取所选 Excel 文件。") from exc
        digest = sha256(content).hexdigest()
        reader = WorkbookCellReader(content, workbook_sha256=digest, canonical_path=canonical_path)
        try:
            workbook = load_workbook(BytesIO(content), data_only=False)
        except (BadZipFile, InvalidFileException, OSError, ValueError) as exc:
            raise WorkbookFatalError("文件不是可读取的 Excel 工作簿，或内部结构已损坏。") from exc

        errors: list[ImportMessage] = []
        warnings: list[ImportMessage] = []
        involved: set[str] = set()
        fuels: list[FuelInput] = []
        processes: tuple[list, list, list] = ([], [], [])
        fumes: list[FumeIncinerationInput] = []
        fgd: list[FGDInput] = []
        purchased_power: list[ElectricityConsumptionDetail] = []
        exported_power: list[ElectricityOutputLine] = []
        purchased_heat: list[HeatInput] = []
        exported_heat: list[HeatInput] = []
        try:
            try:
                self.template_service.validate_structure(workbook, STANDARD_ID)
            except ValueError as exc:
                raise WorkbookFatalError(str(exc)) from exc
            unit_id = _stable_id("appendix-b-unit", digest)
            enterprise_id = context.enterprise_id or _stable_id("appendix-b-enterprise", digest)

            self._parse_fuels(workbook, context, reader, errors, warnings, fuels, involved, unit_id)
            self._parse_processes(workbook, context, reader, errors, warnings, processes, involved, unit_id)
            self._parse_fumes(workbook, context, reader, errors, warnings, fumes, involved, unit_id)
            self._parse_fgd(workbook, context, reader, errors, warnings, fgd, involved, unit_id)
            self._parse_power(workbook, context, reader, errors, warnings, purchased_power,
                              exported_power, involved, unit_id, enterprise_id)
            self._parse_heat(workbook, context, reader, errors, warnings, purchased_heat,
                             exported_heat, involved, unit_id)

            states = tuple(EmissionSourceState(
                source_id,
                EmissionSourceStatus.INVOLVED if source_id in involved else EmissionSourceStatus.NOT_INVOLVED,
            ) for source_id in _SOURCE_IDS)
            canonical = CarbonMaterialInput(
                input_id=_stable_id("appendix-b-input", digest),
                enterprise_id=enterprise_id,
                enterprise_name=context.enterprise_name,
                period=context.period,
                boundary_confirmed=context.boundary_confirmed,
                boundary_component_ids=(_stable_id("appendix-b-boundary", digest),),
                source_states=states,
                fuel_inputs=tuple(fuels),
                calcinations=tuple(processes[0]),
                bakings=tuple(processes[1]),
                graphitizations=tuple(processes[2]),
                fume_incinerations=tuple(fumes),
                fgd_units=tuple(fgd),
                electricity_details=tuple(purchased_power),
                exported_electricity=tuple(exported_power),
                purchased_heat=tuple(purchased_heat),
                exported_heat=tuple(exported_heat),
            )
            imported_at = datetime.now(timezone.utc)
            calculation = (
                self.preview_use_case.calculate(canonical, calculated_at=imported_at)
                if not errors else None
            )
            if calculation is not None:
                for problem in getattr(calculation, "problems", ()):
                    level = getattr(getattr(problem, "level", None), "value", getattr(problem, "level", None))
                    message = ImportMessage(
                        code=getattr(problem, "code", "EXB01_CALCULATION_ISSUE"),
                        message=getattr(problem, "message", "共享计算器返回了未说明的问题。"),
                    )
                    if str(level).upper() == "ERROR":
                        errors.append(message)
                    else:
                        warnings.append(message)
            template = self.template_service.get(STANDARD_ID)
            unit = UnitCalculationPreview(
                unit_id=unit_id,
                name=context.enterprise_name or path.stem or "附录B工作簿",
                unit_type=AccountingUnitType.WHOLE_SITE,
                input_value=canonical,
                calculation=calculation,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )
            return WorkbookImportPreview(
                provenance=WorkbookProvenance(
                    workbook_sha256=digest,
                    template_id=template.template_id,
                    template_version=template.template_version,
                    standard_id=template.standard_id,
                    standard_version=template.standard_version,
                    ingress_policy_id=INGRESS_POLICY_ID,
                    imported_at=imported_at,
                    canonical_path=canonical_path,
                    source=EXCEL_APPENDIX_B,
                ),
                units=(unit,),
                warnings=tuple(warnings),
                numeric_evidence=tuple(reader.evidence),
            )
        finally:
            workbook.close()

    def _parameter_value(self, factor, reason: str, *, unit: str | None = None) -> ParameterValue:
        source = self.sources.get(getattr(factor, "source_id", None))
        source_version = getattr(source, "version", None)
        return _parameter_value(factor, reason, unit=unit, source_version=source_version)

    def _default_factor(self, parameter_id: str, period: AccountingPeriod, *,
                        subject_id: str | None = None, direction: str | None = None,
                        region: str | None = None,
                        electricity_attribute: ElectricityAttribute | None = None,
                        electricity_acquisition_mode: ElectricityAcquisitionMode | None = None):
        if self.resolver is None:
            return None
        parameter = self.parameters.get(parameter_id.lower())
        if parameter is None:
            return None
        ctx = ParameterResolutionContext(
            parameter_id=parameter.parameter_id,
            standard_id=STANDARD_ID,
            accounting_period=period,
            subject_id=subject_id or parameter.subject_id,
            region=region,
            parameter_type=parameter.parameter_type,
            electricity_attribute=electricity_attribute,
            electricity_acquisition_mode=electricity_acquisition_mode,
            emission_source_type=direction,
            extra_context=(("energy_direction", direction),) if direction else (),
        )
        try:
            resolved = self.resolver.resolve(ctx)
        except (AttributeError, TypeError, ValueError):
            return None
        return resolved.recommended.factor if not resolved.blocked and resolved.recommended else None

    def _fuel_option(self, label: str):
        kind = _FUEL_TYPES.get(label)
        if self.queries is None or kind is None:
            return None
        options = [item for item in self.queries.fuel_options() if item.fuel_type is kind]
        return options[0] if len(options) == 1 else None

    def _fuel_defaults(self, option, period):
        if self.queries is None or option is None:
            return None, None, None
        try:
            defaults = self.queries.fuel_defaults(option.subject_id, period)
        except (AttributeError, TypeError, ValueError):
            return None, None, None
        return tuple(
            item.factor if item else None for item in (
                defaults.lower_heating_value,
                defaults.carbon_content_per_heat,
                defaults.oxidation_rate,
            )
        )

    @staticmethod
    def _fuel_path(label, row, default_lhv, context, errors):
        location = f"B.2!B{row}"
        override = context.fuel_path_overrides.get(location)
        if override is FuelPath.HEAT:
            errors.append(ImportMessage(
                "EXB01_FUEL_PATH_UNSUPPORTED",
                f"“{label}”的消耗量单位栏只支持吨或万立方米，不支持热量路径。",
                location, f"燃料“{label}”的消耗量单位",
            ))
            return None
        if override is not None:
            return override
        unit = getattr(default_lhv, "unit", None)
        if unit == "GJ/t":
            return FuelPath.MASS
        if unit == "GJ/10⁴Nm³":
            return FuelPath.VOLUME
        errors.append(ImportMessage(
            "EXB01_FUEL_PATH_REQUIRED",
            f"“{label}”第 {row} 行的消耗量单位无法从工作簿唯一确定；请明确选择吨或万立方米。",
            location, f"燃料“{label}”的消耗量单位",
        ))
        return None


    def _parse_fuels(self, workbook, context, reader, errors, warnings, output, involved, unit_id):
        sheet = workbook["B.2"]
        stop = next(
            (r for r in range(4, sheet.max_row + 1) if _is_appendix_footer_row(sheet, r)),
            sheet.max_row + 1,
        )
        for row in range(4, stop):
            if not any(_has_value(sheet[f"{col}{row}"]) for col in "BCEGH"):
                continue
            label = reader.text(workbook, "B.2", f"A{row}", errors, required=True, field_label="燃料品种")
            if not label:
                continue
            fuel_type = _FUEL_TYPES.get(label, FuelType.OTHER)
            option = self._fuel_option(label)
            default_lhv, default_carbon, default_oxidation = self._fuel_defaults(option, context.period)
            path = self._fuel_path(label, row, default_lhv, context, errors)
            activity = reader.number(workbook, "B.2", f"B{row}", errors, required=True, field_label=f"燃料“{label}”消耗量")
            route = reader.text(workbook, "B.2", f"D{row}", errors, required=True, field_label=f"燃料“{label}”碳含量路径")
            if route not in {"计算值", "实测值"}:
                if route is not None:
                    errors.append(ImportMessage("EXB01_FUEL_CARBON_ROUTE_INVALID", "碳含量路径只能是“计算值”或“实测值”。", f"B.2!D{row}", "碳含量路径"))
                route = None
            lhv_cell = f"B.2!E{row}"
            carbon_cell = f"B.2!G{row}"
            direct_cell = f"B.2!C{row}"
            lhv_source = reader.text(workbook, "B.2", f"F{row}", errors, field_label="低位发热量来源")
            oxidation_source = reader.text(workbook, "B.2", f"I{row}", errors, field_label="碳氧化率来源")

            if route == "实测值":
                direct = reader.number(workbook, "B.2", f"C{row}", errors, required=True, field_label="直接含碳量")
                reader.observe_unused(workbook, "B.2", f"E{row}", warnings, field_label="低位发热量", reason="实测直接含碳路径不采用低位发热量；原始数值保留为证据。")
                reader.observe_unused(workbook, "B.2", f"G{row}", warnings, field_label="单位热值含碳量", reason="实测直接含碳路径不采用单位热值含碳量；原始数值保留为证据。")
                lhv_parameter = None
                carbon_parameter = (
                    _user_parameter(direct, f"enterprise_fuel_{unit_id}_{row}_carbon", "tC/10^4Nm3" if path is FuelPath.VOLUME else "tC/t", direct_cell, ParameterSourceKind.MEASURED)
                    if direct is not None else None
                )
                if direct is not None:
                    self._warn_missing_source(warnings, direct_cell, f"燃料“{label}”直接含碳量")
            elif route == "计算值":
                reader.observe_unused(workbook, "B.2", f"C{row}", warnings, field_label="直接含碳量", reason="计算路径不采用直接含碳量；原始数值保留为证据。")
                lhv_value = reader.number(workbook, "B.2", f"E{row}", errors, field_label="低位发热量")
                carbon_value = reader.number(workbook, "B.2", f"G{row}", errors, field_label="单位热值含碳量")
                lhv_unit = {FuelPath.MASS: "GJ/t", FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.HEAT: "GJ/GJ"}[path] if path else "GJ/t"
                lhv_parameter = self._parameter_with_source(
                    lhv_value, lhv_source, default_lhv,
                    option.subject_id + "_lhv" if option else f"enterprise_fuel_{unit_id}_{row}_lhv",
                    lhv_unit, lhv_cell, f"B.2!F{row}", errors, warnings, "低位发热量",
                )
                carbon_parameter = self._factor_cell(
                    carbon_value, default_carbon,
                    option.subject_id + "_carbon_content" if option else f"enterprise_fuel_{unit_id}_{row}_carbon",
                    "tC/GJ", carbon_cell, warnings, "单位热值含碳量",
                )
            else:
                continue

            if path is None or activity is None:
                continue
            oxidation_value = reader.number(workbook, "B.2", f"H{row}", errors, field_label="碳氧化率")
            oxidation_parameter = self._parameter_with_source(
                oxidation_value, oxidation_source, default_oxidation,
                option.subject_id + "_oxidation_rate" if option else f"enterprise_fuel_{unit_id}_{row}_oxidation",
                "ratio", f"B.2!H{row}", f"B.2!I{row}", errors, warnings, "碳氧化率", percent=True,
            )
            if route == "计算值" and lhv_parameter is not None:
                expected_unit = {FuelPath.MASS: "GJ/t", FuelPath.VOLUME: "GJ/10⁴Nm³", FuelPath.HEAT: "GJ/GJ"}[path]
                if lhv_parameter.unit != expected_unit:
                    errors.append(ImportMessage("EXB01_FUEL_PATH_PARAMETER_UNIT_MISMATCH", "低位发热量目录单位与消耗量单位不一致；请更正单位，或选择实测参数路径。", f"B.2!B{row}", "消耗量单位"))
            if route == "计算值" and lhv_parameter is None:
                errors.append(ImportMessage("EXB01_FUEL_LHV_REQUIRED", "计算路径缺少低位发热量；请填写实测值或使用可核验的目录缺省值。", lhv_cell, "低位发热量"))
            if carbon_parameter is None:
                errors.append(ImportMessage("EXB01_FUEL_CARBON_REQUIRED", "当前路径缺少所需含碳量。", carbon_cell if route == "计算值" else direct_cell, "含碳量"))
            if oxidation_parameter is None:
                errors.append(ImportMessage("EXB01_FUEL_OXIDATION_REQUIRED", "缺少碳氧化率；请填写数值或确认当前期间的目录缺省值。", f"B.2!H{row}", "碳氧化率"))
            output.append(FuelInput(
                fuel_id=_stable_id("fuel", unit_id, row),
                path=path,
                activity=InputValue(activity, "ten_thousand_Nm3" if path is FuelPath.VOLUME else "t", source_reference=f"B.2!B{row}"),
                carbon_content=carbon_parameter,
                oxidation_rate=oxidation_parameter,
                lower_heating_value=lhv_parameter,
                fuel_type=fuel_type,
                fuel_label=label if fuel_type is FuelType.OTHER else None,
            ))
            involved.add(SOURCE_FUEL)

    def _parameter_with_source(self, value, source_label, default_factor, parameter_id, unit,
                               value_location, source_location, errors, warnings, label, percent=False):
        if source_label not in (None, "缺省值", "实测值"):
            errors.append(ImportMessage("EXB01_PARAMETER_SOURCE_INVALID", "来源只能选择“缺省值”或“实测值”。", source_location, label))
        if source_label == "缺省值":
            if value is None:
                return self._parameter_value(default_factor, "采用当前期间 Resolver 核验的标准缺省参数。") if default_factor else None
            normalized = self.policy.divide(value, Decimal("100")) if percent else value
            if default_factor is None or normalized != _factor_value(default_factor):
                errors.append(ImportMessage(
                    "EXB01_DEFAULT_PARAMETER_MISMATCH",
                    "选择“缺省值”时请清空数值，或确保其与当前期间核验值完全一致；其他数值请改选“实测值”。",
                    value_location, label,
                ))
                return self._parameter_value(default_factor, "采用当前期间 Resolver 核验的标准缺省参数。") if default_factor else None
            return self._parameter_value(default_factor, "数值与当前期间 Resolver 核验值完全一致。")
        if source_label == "实测值":
            if value is None:
                errors.append(ImportMessage("EXB01_MEASURED_PARAMETER_REQUIRED", "选择“实测值”后必须填写参数。", value_location, label))
                return None
            normalized = self.policy.divide(value, Decimal("100")) if percent else value
            self._warn_missing_source(warnings, value_location, label)
            return _user_parameter(normalized, parameter_id, unit, value_location, ParameterSourceKind.MEASURED)
        if value is None:
            warnings.append(ImportMessage("EXB01_PARAMETER_SOURCE_UNSPECIFIED", "来源选择为空；此提醒不阻断计算。", source_location, label))
            return self._parameter_value(default_factor, "来源栏为空，采用当前期间 Resolver 核验的标准缺省参数。") if default_factor else None
        normalized = self.policy.divide(value, Decimal("100")) if percent else value
        if default_factor is not None and normalized == _factor_value(default_factor):
            warnings.append(ImportMessage("EXB01_PARAMETER_SOURCE_UNSPECIFIED", "来源选择为空；数值与已核验缺省值一致，已绑定该目录参数。", source_location, label))
            return self._parameter_value(default_factor, "数值与当前期间 Resolver 核验值完全一致。")
        self._warn_missing_source(warnings, value_location, label)
        return _user_parameter(normalized, parameter_id, unit, value_location)

    def _factor_cell(self, value, default_factor, parameter_id, unit, location, warnings, label):
        if value is None:
            return self._parameter_value(default_factor, "采用当前期间 Resolver 核验的标准缺省参数。") if default_factor else None
        if default_factor is not None and value == _factor_value(default_factor):
            return self._parameter_value(default_factor, "数值与当前期间 Resolver 核验值完全一致。")
        warnings.append(ImportMessage("EXB01_SOURCE_REFERENCE_MISSING", "此列没有来源字段；数值作为用户提供参数，来源待补充。", location, label))
        return _user_parameter(value, parameter_id, unit, location)

    @staticmethod
    def _warn_missing_source(warnings, location, label):
        warnings.append(ImportMessage("EXB01_SOURCE_REFERENCE_MISSING", "工作簿未提供外部来源说明；此提醒不阻断预览或计算。", location, label))

    def _parse_power(self, workbook, context, reader, errors, warnings, purchased, exported, involved, unit_id, enterprise_id):
        ws = workbook["B.8"]
        stop = next((r for r in range(3, ws.max_row + 1)
                     if _is_appendix_footer_row(ws, r)), ws.max_row + 1)
        for row in range(3, stop):
            if not any(_has_value(ws[f"{col}{row}"]) for col in "BCD"):
                continue
            direction = reader.text(workbook, "B.8", f"A{row}", errors, required=True, field_label="电力方向")
            label = reader.text(
                workbook, "B.8", f"B{row}", errors,
                required=direction == "购入", field_label="电力属性",
            )
            valid_direction = direction in {"购入", "输出"}
            valid_label = (
                label in {"电网电力", "非化石电力"}
                if direction == "购入"
                else label is None or label in {"电网电力", "非化石电力"}
            )
            if not valid_direction and direction is not None:
                errors.append(ImportMessage("EXB01_ELECTRICITY_DIRECTION_INVALID", "电力方向只能是“购入”或“输出”。", f"B.8!A{row}", "电力方向"))
            if valid_direction and not valid_label and label is not None:
                errors.append(ImportMessage("EXB01_ELECTRICITY_ATTRIBUTE_INVALID", "电力属性只能选择“电网电力”或“非化石电力”；输出行可留空。", f"B.8!B{row}", "电力属性"))
            if direction == "输出" and label is not None and valid_label:
                warnings.append(ImportMessage(
                    "EXB01_OUTPUT_ATTRIBUTE_NOT_APPLICABLE",
                    f"输出电力不适用购入电力属性；B列原文“{label}”仅作为填报证据保留，不用于选择输出因子。",
                    f"B.8!B{row}", "电力属性",
                ))
            if not valid_direction or not valid_label:
                reader.observe_unused(workbook, "B.8", f"C{row}", warnings, field_label="电量")
                reader.observe_unused(workbook, "B.8", f"D{row}", warnings, field_label="电力排放因子")
                continue
            amount = reader.number(workbook, "B.8", f"C{row}", errors, required=True, field_label="电量")
            if amount is None:
                reader.observe_unused(workbook, "B.8", f"D{row}", warnings, field_label="电力排放因子")
                continue
            factor_value = reader.number(workbook, "B.8", f"D{row}", errors, field_label="电力排放因子")

            nonfossil_purchase = direction == "购入" and label == "非化石电力"
            region = context.region if direction == "输出" or label == "电网电力" else None
            direction_token = "purchased" if direction == "购入" else "exported"
            parameter_id = "electricity_emission_factor_nonfossil" if nonfossil_purchase else (
                "electricity_emission_factor_provincial_average" if region else "electricity_emission_factor_national"
            )
            default = self._default_factor(
                parameter_id,
                context.period,
                region=region,
                direction=direction_token,
                electricity_attribute=(
                    ElectricityAttribute.NONFOSSIL if nonfossil_purchase
                    else ElectricityAttribute.ORDINARY
                ),
                electricity_acquisition_mode=ElectricityAcquisitionMode.PURCHASED,
            )
            resolver_unit = self._parameter_unit(parameter_id, "tCO₂/MWh")

            if nonfossil_purchase:
                if default is None:
                    errors.append(ImportMessage(
                        "EXB01_NONFOSSIL_FACTOR_UNRESOLVED",
                        "当前 Resolver 没有可用的非化石电力零因子；请核验目录，不回退到普通电网因子。",
                        f"B.8!D{row}", "电力排放因子",
                    ))
                elif factor_value is not None and factor_value != _factor_value(default):
                    errors.append(ImportMessage(
                        "EXB01_NONFOSSIL_FACTOR_MISMATCH",
                        "非化石电力排放因子只能采用当前 Resolver 核验值；此单元格数值与核验值不一致。",
                        f"B.8!D{row}", "电力排放因子",
                    ))
                purchased.append(ElectricityConsumptionDetail(
                    detail_id=_stable_id("power", unit_id, row), enterprise_id=enterprise_id,
                    standard_id=STANDARD_ID, accounting_period=context.period,
                    electricity_amount=amount, electricity_unit="MWh",
                    acquisition_mode=ElectricityAcquisitionMode.PURCHASED,
                    attribute=ElectricityAttribute.NONFOSSIL, region=None,
                ))
                involved.add(SOURCE_PURCHASED_ELECTRICITY)
                continue

            if direction == "购入":
                selected_id = default.factor_id if default is not None and (
                    factor_value is None or factor_value == _factor_value(default)
                ) else None
                override = None
                if factor_value is not None and selected_id is None:
                    override = UserProvidedParameterValue(
                        factor_value, resolver_unit, source_reference=f"B.8!D{row}",
                        selection_reason="附录B提供未核验来源的电力排放因子。",
                    )
                    self._warn_missing_source(warnings, f"B.8!D{row}", "电力排放因子")
                elif factor_value is None and default is None:
                    errors.append(ImportMessage("EXB01_ELECTRICITY_FACTOR_UNRESOLVED", "当前期间和地区没有可用的核验电力因子；请补充地区或更正核算期间。", f"B.8!D{row}", "电力排放因子"))
                purchased.append(ElectricityConsumptionDetail(
                    detail_id=_stable_id("power", unit_id, row), enterprise_id=enterprise_id,
                    standard_id=STANDARD_ID, accounting_period=context.period,
                    electricity_amount=amount, electricity_unit="MWh",
                    acquisition_mode=ElectricityAcquisitionMode.PURCHASED,
                    attribute=ElectricityAttribute.ORDINARY, region=region,
                    selected_factor_id=selected_id,
                    factor_selection_reason="采用当前 Resolver 推荐的核验电力因子。" if selected_id else None,
                    factor_override=override,
                ))
                involved.add(SOURCE_PURCHASED_ELECTRICITY)
                continue

            output_attribute_note = (
                f"；B列原文“{label}”按 PR37 作为不适用购入属性的填报证据保留"
                if label is not None else ""
            )
            if factor_value is None:
                parameter = self._parameter_value(
                    default, f"采用当前 Resolver 核验的输出电力适用因子{output_attribute_note}。"
                ) if default is not None else None
                if parameter is None:
                    errors.append(ImportMessage("EXB01_ELECTRICITY_FACTOR_UNRESOLVED", "当前期间和地区没有可用的核验输出电力因子；请填写可追溯的因子值。", f"B.8!D{row}", "电力排放因子"))
            elif default is not None and factor_value == _factor_value(default):
                parameter = self._parameter_value(
                    default, f"数值与当前 Resolver 核验的输出电力因子完全一致{output_attribute_note}。"
                )
            else:
                self._warn_missing_source(warnings, f"B.8!D{row}", "输出电力因子")
                parameter = _user_parameter(
                    factor_value, parameter_id, "tCO2/MWh", f"B.8!D{row}",
                    selection_reason=(
                        "附录B提供未核验来源的输出电力排放因子" + output_attribute_note + "。"
                    ),
                )
            exported.append(ElectricityOutputLine(
                line_id=_stable_id("power-export", unit_id, row),
                amount=InputValue(amount, "MWh", source_reference=f"B.8!C{row}"),
                factor=parameter, unit="MWh", region=region,
            ))
            involved.add(SOURCE_EXPORTED_ELECTRICITY)

    def _parameter_unit(self, parameter_id, fallback):
        # Resolver overrides are validated in the Catalog's declared canonical unit.
        parameter = self.parameters.get(parameter_id.lower())
        return str(getattr(parameter, "canonical_unit", getattr(parameter, "default_unit", fallback))) if parameter else fallback

    def _is_template_numeric_seed(self, reader, sheet: str, cell_ref: str) -> bool:
        expected = self._template_numeric_lexemes.get((sheet, cell_ref))
        actual = reader.numeric_lexemes.get((sheet, cell_ref))
        return expected is not None and actual == expected

    def _parse_heat(self, workbook, context, reader, errors, warnings, purchased, exported, involved, unit_id):
        ws = workbook["B.9"]
        stop = next((r for r in range(3, ws.max_row + 1)
                     if _is_appendix_footer_row(ws, r)), ws.max_row + 1)
        for row in range(3, stop):
            if _has_value(ws[f"F{row}"]):
                reader.observe_unused(workbook, "B.9", f"F{row}", warnings, field_label="蒸汽焓值", reason="焓值为模板只读/自动路径；工作簿内容不作为正式焓值。")
            factor_is_template_seed = self._is_template_numeric_seed(reader, "B.9", f"G{row}")
            active = any(_has_value(ws[f"{col}{row}"]) for col in "BCDE") or (
                _has_value(ws[f"G{row}"]) and not factor_is_template_seed
            )
            if not active:
                continue

            direction = reader.text(workbook, "B.9", f"A{row}", errors, required=True, field_label="热力方向")
            kind_label = reader.text(workbook, "B.9", f"B{row}", errors, required=True, field_label="热力类别")
            if direction not in {"购入", "输出"}:
                if direction is not None:
                    errors.append(ImportMessage("EXB01_HEAT_DIRECTION_INVALID", "热力方向只能是“购入”或“输出”。", f"B.9!A{row}", "热力方向"))
                for col, label in (("C", "动力总量"), ("D", "蒸汽压力"), ("E", "蒸汽温度"), ("G", "热力排放因子")):
                    reader.observe_unused(workbook, "B.9", f"{col}{row}", warnings, field_label=label)
                continue
            if kind_label not in {"饱和蒸汽", "过热蒸汽"}:
                if kind_label is not None:
                    errors.append(ImportMessage("EXB01_HEAT_KIND_UNSUPPORTED", "当前正式模型只支持饱和蒸汽或过热蒸汽；热水及其他热力需要另行核验口径。", f"B.9!B{row}", "热力类别"))
                for col, label in (("C", "动力总量"), ("D", "蒸汽压力"), ("E", "蒸汽温度"), ("G", "热力排放因子")):
                    reader.observe_unused(workbook, "B.9", f"{col}{row}", warnings, field_label=label)
                continue

            amount = reader.number(workbook, "B.9", f"C{row}", errors, required=True, field_label="动力总量")
            pressure = reader.number(workbook, "B.9", f"D{row}", errors, required=True, field_label="蒸汽压力")
            if kind_label == "饱和蒸汽":
                reader.observe_unused(workbook, "B.9", f"E{row}", warnings, field_label="蒸汽温度", reason="饱和蒸汽自动焓值路径不采用温度；原始内容仅保留为证据。")
                temperature = None
                steam_kind = SteamKind.SATURATED
            else:
                temperature = reader.number(workbook, "B.9", f"E{row}", errors, required=True, field_label="蒸汽温度")
                steam_kind = SteamKind.SUPERHEATED
            if factor_is_template_seed:
                reader.observe_unused(workbook, "B.9", f"G{row}", warnings, field_label="热力排放因子", reason="模板预置展示值不是来源凭证；正式缺省因子由 Resolver 按核算期间和方向核验。")
                factor_value = None
            else:
                factor_value = reader.number(workbook, "B.9", f"G{row}", errors, field_label="热力排放因子")
            if amount is None:
                continue

            direction_token = "purchased_heat" if direction == "购入" else "exported_heat"
            default = self._default_factor("heat_emission_factor_default", context.period, direction=direction_token)
            if factor_value is not None and default is not None and factor_value == _factor_value(default):
                # Keep the line on the Calculator's Resolver path so it can bind
                # the factor for this exact heat direction.
                factor = None
                factor_mode = HeatFactorMode.STANDARD_DEFAULT
            elif factor_value is not None:
                self._warn_missing_source(warnings, f"B.9!G{row}", "热力排放因子")
                factor = _user_parameter(factor_value, "heat_emission_factor_measured", "tCO2/GJ", f"B.9!G{row}")
                factor_mode = HeatFactorMode.MEASURED
            else:
                factor = None
                factor_mode = HeatFactorMode.STANDARD_DEFAULT

            heat = HeatInput(
                line_id=_stable_id("heat", unit_id, row),
                amount=InputValue(amount, "t", source_reference=f"B.9!C{row}"),
                enthalpy=None, factor=factor, unit="t", steam_kind=steam_kind,
                pressure_mpa=pressure, temperature_c=temperature, manual_enthalpy=False,
                factor_mode=factor_mode,
            )
            if direction == "购入":
                purchased.append(heat)
                involved.add(SOURCE_PURCHASED_HEAT)
            else:
                exported.append(heat)
                involved.add(SOURCE_EXPORTED_HEAT)

    def _parse_processes(self, workbook, context, reader, errors, warnings, outputs, involved, unit_id):
        for sheet_name, meta in _PROCESS_META.items():
            source_id, model_type, default_parameter_id, parameter_name, index = meta
            ws = workbook[sheet_name]
            stop = next((r for r in range(4, ws.max_row + 1)
                         if _is_appendix_footer_row(ws, r)), ws.max_row + 1)
            active_by_group = {}
            current_group = None
            group_positions = {}
            for row in range(4, stop):
                a = ws[f"A{row}"].value
                if isinstance(a, str) and a.strip():
                    current_group = " ".join(a.split())
                if current_group is None:
                    if any(_has_value(ws[f"{col}{row}"]) for col in "CD"):
                        errors.append(ImportMessage(
                            "EXB01_PROCESS_GROUP_REQUIRED",
                            "该活动行缺少可识别的附录B过程分组；请恢复 A 列组标签。",
                            f"{sheet_name}!A{row}", "过程分组",
                        ))
                    continue
                group_positions[current_group] = group_positions.get(current_group, 0) + 1
                if any(_has_value(ws[f"{col}{row}"]) for col in "CD"):
                    name = reader.text(workbook, sheet_name, f"B{row}", errors, field_label="物料名称")
                    active_by_group.setdefault(current_group, []).append((row, group_positions[current_group], name))
            material_records = {}
            for group, rows in active_by_group.items():
                for row, position, name in rows:
                    role_kind = self._dynamic_process_role(sheet_name, group, position)
                    if role_kind is None:
                        errors.append(ImportMessage("EXB01_PROCESS_ROW_UNMAPPED", "该活动行无法依据附录B的过程分组和固定角色槽唯一映射；请恢复明确的过程分组结构。", f"{sheet_name}!B{row}", "物料名称"))
                        continue
                    role, component = role_kind
                    if not name:
                        errors.append(ImportMessage("EXB01_PROCESS_MATERIAL_NAME_REQUIRED", "活动行缺少物料名称。", f"{sheet_name}!B{row}", "物料名称"))
                        continue
                    mass = reader.number(workbook, sheet_name, f"C{row}", errors, required=_has_value(ws[f"D{row}"]), field_label="活动数据")
                    percentage = reader.number(workbook, sheet_name, f"D{row}", errors, field_label="碳/挥发分含量")
                    source = reader.text(workbook, sheet_name, f"E{row}", errors, field_label="碳/挥发分来源")
                    if source not in (None, "实测值"):
                        errors.append(ImportMessage("EXB01_PROCESS_SOURCE_UNSUPPORTED", "该表的碳/挥发分来源仅支持“实测值”。", f"{sheet_name}!E{row}", "碳/挥发分来源"))
                    key = (role, name)
                    record = material_records.setdefault(key, {"masses": [], "fixed": [], "volatile": []})
                    if mass is not None:
                        record["masses"].append((row, mass))
                    if percentage is not None:
                        record[component].append((row, percentage))
            material_rows = []
            for ordinal, ((role, name), values) in enumerate(material_records.items(), 1):
                masses = values["masses"]
                if len(masses) > 1:
                    if len({mass for _, mass in masses}) > 1:
                        errors.append(ImportMessage("EXB01_PROCESS_PAIRED_MASS_MISMATCH", "同名物料的碳与挥发分行活动数据必须完全一致；不能相加或猜测。", f"{sheet_name}!C{masses[-1][0]}", "活动数据"))
                    mass = masses[0][1]
                else:
                    mass = masses[0][1] if masses else None
                for comp in ("fixed", "volatile"):
                    if len(values[comp]) > 1:
                        errors.append(ImportMessage("EXB01_PROCESS_DUPLICATE_COMPONENT", "同一过程、物料名称和组分出现多个活动行，无法判断是否为新增过程实例。", f"{sheet_name}!D{values[comp][1][0]}", "碳/挥发分含量"))
                fixed = values["fixed"][0][1] if values["fixed"] else None
                volatile = values["volatile"][0][1] if values["volatile"] else None
                material_rows.append(MaterialInputLine(
                    line_id=_stable_id("material", unit_id, sheet_name, ordinal), role=role, name=name, mass_t=mass,
                    fixed_carbon_percent=fixed, fixed_carbon_source=MaterialDataSource.MEASURED,
                    volatile_matter_percent=volatile, volatile_matter_source=MaterialDataSource.MEASURED,
                ))
            if not material_rows:
                continue
            factor = self._default_factor(default_parameter_id, context.period)
            parameter = self._parameter_value(factor, "采用当前期间 Resolver 核验的标准一般参数。") if factor else None
            instance_id = {"B.3": "calcination-1", "B.4": "baking-1", "B.5": "graphitization-1"}[sheet_name]
            process = model_type(instance_id=instance_id, material_rows=tuple(material_rows), **{parameter_name: parameter})
            outputs[index].append(process)
            involved.add(source_id)

    @staticmethod
    def _dynamic_process_role(sheet, group, position):
        normalized_group = "".join((group or "").split())
        if sheet == "B.3":
            slots = {
                "进入煅烧炉的碳": ((MaterialRole.CALCINATION_FEED, "fixed"),),
                "进入煅烧炉的挥发分": ((MaterialRole.CALCINATION_FEED, "volatile"),),
                "输出煅烧炉的碳": (
                    (MaterialRole.CALCINED_PRODUCT, "fixed"),
                    (MaterialRole.UNDERBURN_RECOVERED, "fixed"),
                    (MaterialRole.CARBON_DUST, "fixed"),
                ),
                "输出煅烧炉的挥发分": ((MaterialRole.CALCINED_PRODUCT, "volatile"),),
            }
        elif sheet == "B.4":
            slots = {
                "进入焙烧(炭化)的碳a": (
                    (MaterialRole.BAKING_FILLER, "fixed"),
                    (MaterialRole.GREEN_BAKING_PRODUCT, "fixed"),
                ),
                "进入焙烧(炭化)的挥发分": (
                    (MaterialRole.BAKING_FILLER, "volatile"),
                    (MaterialRole.GREEN_BAKING_PRODUCT, "volatile"),
                ),
                "输出焙烧(炭化)炉的碳": (
                    (MaterialRole.BAKING_BYPRODUCT, "fixed"),
                    (MaterialRole.BAKED_PRODUCT, "fixed"),
                ),
            }
        elif sheet == "B.5":
            slots = {
                "进入石墨化炉的碳": (
                    (MaterialRole.GRAPHITIZATION_PACKING, "fixed"),
                    (MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "fixed"),
                ),
                "进入石墨化炉的挥发分": ((MaterialRole.GRAPHITIZATION_PACKING, "volatile"),),
                "输出石墨化炉的碳": (
                    (MaterialRole.GRAPHITIZATION_BYPRODUCT, "fixed"),
                    (MaterialRole.GRAPHITIZED_PRODUCT, "fixed"),
                ),
            }
        else:
            return None
        group_slots = slots.get(normalized_group)
        if not group_slots:
            return None
        if len(group_slots) == 1:
            return group_slots[0]
        return group_slots[position - 1] if 1 <= position <= len(group_slots) else None

    def _parse_fumes(self, workbook, context, reader, errors, warnings, output, involved, unit_id):
        ws = workbook["B.6"]
        if not any(_has_value(ws[f"{col}3"]) for col in "ABCDEF"):
            return
        labels = ("烟气流量", "焦油含量", "低位发热量", "单位热值含碳量", "碳氧化率", "报告期时长")
        values = [
            reader.number(workbook, "B.6", f"{col}3", errors, required=True, field_label=label)
            for col, label in zip("ABCDEF", labels)
        ]
        if any(value is None for value in values):
            return
        q, qvar, hm, fch_value, fox_pct, duration = values
        fch_default = self._default_factor("CAR-PAR-P04A-FCH", context.period)
        fch = self._factor_cell(
            fch_value, fch_default, "CAR-PAR-P04A-FCH", "tC/GJ",
            "B.6!D3", warnings, "单位热值含碳量",
        )
        fox = self.policy.divide(fox_pct, Decimal("100"))
        output.append(FumeIncinerationInput(
            q=InputValue(q, "Nm3/h", source_reference="B.6!A3"),
            qvar=InputValue(qvar, "mg/Nm3", source_reference="B.6!B3"),
            hm=InputValue(hm, "GJ/t", source_reference="B.6!C3"),
            fch=fch, fox=fox, duration=InputValue(duration, "d", source_reference="B.6!F3"),
            instance_id="fume-1",
        ))
        involved.add(SOURCE_FUME)

    def _carbonate_option(self, label, period):
        if self.queries is None:
            return None
        import unicodedata
        normalize = lambda value: "".join(unicodedata.normalize("NFKC", str(value)).split()).casefold()
        target = normalize(label)
        matches = [item for item in self.queries.carbonate_options(period)
                   if target in {normalize(item.label), *(normalize(alias) for alias in item.aliases)}]
        return matches[0] if len(matches) == 1 else None

    def _parse_fgd(self, workbook, context, reader, errors, warnings, output, involved, unit_id):
        ws = workbook["B.7"]
        stop = next((row for row in range(3, ws.max_row + 1)
                     if _is_appendix_footer_row(ws, row)), ws.max_row + 1)
        merge_rows: dict[int, list[object]] = {1: [], 2: []}
        for area in ws.merged_cells.ranges:
            if area.min_col in merge_rows and area.min_row >= 3 and area.max_row < stop:
                merge_rows[area.min_col].append(area)
        a_ranges = sorted(merge_rows[1], key=lambda item: item.min_row)
        b_ranges = sorted(merge_rows[2], key=lambda item: item.min_row)
        a_bounds = {(item.min_row, item.max_row): item for item in a_ranges}
        b_bounds = {(item.min_row, item.max_row): item for item in b_ranges}
        merged_rows = {
            row for item in (*a_ranges, *b_ranges)
            for row in range(item.min_row, item.max_row + 1)
        }
        groups: list[tuple[int, int, bool]] = []
        for bounds, a_range in a_bounds.items():
            if bounds in b_bounds:
                groups.append((bounds[0], bounds[1], True))
            else:
                errors.append(ImportMessage(
                    "EXB01_FGD_BATCH_STRUCTURE_INVALID",
                    "A 列批次名称与 B 列消耗量的合并范围必须一致。",
                    f"B.7!A{a_range.min_row}", "碳酸盐批次名称",
                ))
        for bounds, b_range in b_bounds.items():
            if bounds not in a_bounds:
                errors.append(ImportMessage(
                    "EXB01_FGD_BATCH_STRUCTURE_INVALID",
                    "A 列批次名称与 B 列消耗量的合并范围必须一致。",
                    f"B.7!B{b_range.min_row}", "批次消耗量",
                ))

        explicit_starts: list[int] = []
        for row in range(3, stop):
            if row in merged_rows:
                continue
            has_name = _has_value(ws[f"A{row}"])
            has_amount = _has_value(ws[f"B{row}"])
            if has_name and has_amount:
                explicit_starts.append(row)
            elif has_name:
                errors.append(ImportMessage(
                    "EXB01_FGD_BATCH_BOUNDARY_INVALID",
                    "新增批次边界必须在同一行明确填写批次名称和消耗量。",
                    f"B.7!B{row}", "批次消耗量",
                ))
            elif has_amount:
                errors.append(ImportMessage(
                    "EXB01_FGD_BATCH_BOUNDARY_INVALID",
                    "新增批次边界必须在同一行明确填写批次名称和消耗量。",
                    f"B.7!A{row}", "碳酸盐批次名称",
                ))

        all_starts = sorted([start for start, _, _ in groups] + explicit_starts)
        for index, start in enumerate(explicit_starts):
            next_start = next((item for item in all_starts if item > start), stop)
            groups.append((start, next_start - 1, False))
        groups.sort(key=lambda item: item[0])
        grouped_rows = {row for start, end, _ in groups for row in range(start, end + 1)}
        for row in range(3, stop):
            if row in grouped_rows:
                continue
            if any(_has_value(ws[f"{col}{row}"]) for col in "DEF"):
                errors.append(ImportMessage(
                    "EXB01_FGD_BATCH_BOUNDARY_REQUIRED",
                    "该碳酸盐组分数据没有落在明确的 A/B 批次合并组或新批次边界内。",
                    f"B.7!C{row}", "碳酸盐组分",
                ))

        carbonate_content_default = self._default_factor("CAR-PAR-P04B-I", context.period)
        ratio_tr_default = self._default_factor("CAR-PAR-P04B-TR", context.period)
        for ordinal, (start, end, _merged) in enumerate(groups, 1):
            batch_name = reader.text(workbook, "B.7", f"A{start}", errors, field_label="碳酸盐批次名称")
            amount = reader.number(workbook, "B.7", f"B{start}", errors, field_label="脱硫剂消耗量")
            component_rows = []
            active = amount is not None or batch_name is not None
            for row in range(start, end + 1):
                label = reader.text(workbook, "B.7", f"C{row}", errors, field_label="碳酸盐组分")
                # The static labels CaCO₃/MgCO₃/其他 are catalog/UI defaults, not activity evidence.
                row_active = any(_has_value(ws[f"{col}{row}"]) for col in "DEF")
                if not row_active:
                    continue
                active = True
                fraction_pct = reader.number(workbook, "B.7", f"D{row}", errors, field_label="碳酸盐组分含量")
                factor_value = reader.number(workbook, "B.7", f"E{row}", errors, field_label="碳酸盐排放因子")
                conversion_pct = reader.number(workbook, "B.7", f"F{row}", errors, field_label="转化率")
                if not label:
                    errors.append(ImportMessage("EXB01_CARBONATE_LABEL_REQUIRED", "请明确碳酸盐组分名称。", f"B.7!C{row}", "碳酸盐组分"))
                    continue
                fraction_location = f"B.7!D{row}"
                if fraction_pct is not None:
                    normalized_fraction = self.policy.divide(fraction_pct, Decimal("100"))
                    if carbonate_content_default is not None and normalized_fraction == _factor_value(carbonate_content_default):
                        fraction_value = self._parameter_value(
                            carbonate_content_default, "填报值与当前 Resolver 核验的碳酸盐含量缺省值完全一致。"
                        )
                    else:
                        self._warn_missing_source(warnings, fraction_location, "碳酸盐组分含量")
                        fraction_value = _user_parameter(
                            normalized_fraction, "carbonate_fraction", "ratio", fraction_location,
                            ParameterSourceKind.MEASURED,
                        )
                elif not _has_value(ws[f"D{row}"]):
                    if carbonate_content_default is None:
                        errors.append(ImportMessage(
                            "EXB01_CARBONATE_CONTENT_UNRESOLVED",
                            "碳酸盐组分含量为空，且当前 Resolver 没有可用的标准缺省参数。",
                            fraction_location, "碳酸盐组分含量",
                        ))
                        fraction_value = None
                    else:
                        fraction_value = self._parameter_value(
                            carbonate_content_default, "碳酸盐组分含量留空，采用当前期间 Resolver 核验的标准缺省值。"
                        )
                        warnings.append(ImportMessage(
                            "EXB01_STANDARD_DEFAULT_APPLIED",
                            f"碳酸盐组分含量留空；已采用并记录 Resolver 核验的标准缺省参数 {carbonate_content_default.parameter_id}。",
                            fraction_location, "碳酸盐组分含量",
                        ))
                else:
                    # A present but invalid cell already has a blocking reader diagnostic;
                    # do not disguise it as a Resolver default.
                    fraction_value = None
                option = None if label == "其他" else self._carbonate_option(label, context.period)
                if label != "其他" and option is None and factor_value is None:
                    errors.append(ImportMessage("EXB01_CARBONATE_FACTOR_UNRESOLVED", f"“{label}”无法唯一匹配经核验的 C.2 碳酸盐因子；请提供因子或更正组分名称。", f"B.7!C{row}", "碳酸盐组分"))
                if factor_value is not None:
                    if option is not None and factor_value == _factor_value(option.factor):
                        factor = self._parameter_value(option.factor, option.selection_reason)
                    else:
                        self._warn_missing_source(warnings, f"B.7!E{row}", "碳酸盐排放因子")
                        factor = _user_parameter(factor_value, "fgd_carbonate_emission_factor_user", "tCO2/t", f"B.7!E{row}")
                else:
                    factor = self._parameter_value(option.factor, option.selection_reason) if option else None
                if label == "其他" and factor is None:
                    errors.append(ImportMessage("EXB01_CUSTOM_CARBONATE_FACTOR_REQUIRED", "“其他”碳酸盐需要填写对应排放因子。", f"B.7!E{row}", "碳酸盐排放因子"))
                conversion_location = f"B.7!F{row}"
                if conversion_pct is not None:
                    normalized_conversion = self.policy.divide(conversion_pct, Decimal("100"))
                    if ratio_tr_default is not None and normalized_conversion == _factor_value(ratio_tr_default):
                        conversion = self._parameter_value(
                            ratio_tr_default, "填报值与当前 Resolver 核验的转化率缺省值完全一致。"
                        )
                    else:
                        self._warn_missing_source(warnings, conversion_location, "脱硫转化率")
                        conversion = _user_parameter(
                            normalized_conversion, "CAR-PAR-P04B-TR", "ratio", conversion_location,
                            ParameterSourceKind.MEASURED,
                        )
                elif not _has_value(ws[f"F{row}"]):
                    if ratio_tr_default is None:
                        errors.append(ImportMessage(
                            "EXB01_CARBONATE_CONVERSION_UNRESOLVED",
                            "脱硫转化率为空，且当前 Resolver 没有可用的标准缺省参数。",
                            conversion_location, "脱硫转化率",
                        ))
                        conversion = None
                    else:
                        conversion = self._parameter_value(
                            ratio_tr_default, "脱硫转化率留空，采用当前期间 Resolver 核验的标准缺省值。"
                        )
                        warnings.append(ImportMessage(
                            "EXB01_STANDARD_DEFAULT_APPLIED",
                            f"脱硫转化率留空；已采用并记录 Resolver 核验的标准缺省参数 {ratio_tr_default.parameter_id}。",
                            conversion_location, "脱硫转化率",
                        ))
                else:
                    conversion = None
                component = CarbonateComponent(
                    amount=InputValue(amount, "t", source_reference=f"B.7!B{start}") if amount is not None else None,
                    carbonate_fraction=fraction_value,
                    emission_factor=factor,
                    conversion_rate=conversion,
                    carbonate_type=option.label if option else label,
                )
                component_rows.append(component)
            if not active:
                continue
            if amount is None:
                errors.append(ImportMessage("EXB01_FGD_BATCH_AMOUNT_REQUIRED", "已填写脱硫批次活动数据，必须填写该批次消耗量。", f"B.7!B{start}", "脱硫剂消耗量"))
                continue
            if not batch_name:
                errors.append(ImportMessage("EXB01_FGD_BATCH_NAME_REQUIRED", "已填写脱硫批次活动数据，必须填写批次名称。", f"B.7!A{start}", "碳酸盐批次名称"))
                continue
            if not component_rows:
                errors.append(ImportMessage("EXB01_FGD_COMPONENT_REQUIRED", "已填写脱硫剂消耗量，但没有填写任何碳酸盐组分含量。", f"B.7!D{start}", "碳酸盐组分含量"))
                continue
            output.append(FGDInput(
                components=tuple(component_rows),
                instance_id=_stable_id("fgd", unit_id, ordinal, batch_name),
            ))
            involved.add(SOURCE_FGD)
