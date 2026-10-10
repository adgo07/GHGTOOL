"""Build synthetic mapping fixtures and formal GHG-RPT02 Word acceptance samples.

The build_acceptance_case/model helpers are synthetic layout fixtures only. The
Word samples are generated from persisted CarbonAccountingUseCase Records.
"""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass, replace
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from io import BytesIO
import json
import tempfile
import sys
from datetime import date, datetime, timezone
from collections.abc import Mapping
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
from typing import Any

from openpyxl import load_workbook

from packages.application import CarbonAccountingPreviewUseCase
from packages.application.carbon_accounting import CarbonAccountingUseCase, create_g06_parameter_resolver
from packages.application.catalog_queries import CatalogQueryService
from packages.application.reporting import build_saved_record_report
from packages.excel.appendix_b import AppendixBImportContext, AppendixBWorkbookImporter
from packages.excel.templates import ExcelTemplateService
from packages.persistence.catalog_builder import build_catalog_database
from packages.persistence.catalog_repository import SQLiteCatalogRepository
from packages.persistence.records_repository import SQLiteRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import CarbonMaterialCalculator, FuelPath, InputValue, ParameterSourceKind, ParameterValue

from packages.application.reporting.model import build_report_model, frozen_totals
from packages.core.models import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    CalculationLine,
    CalculationResult,
    ParameterSelectionMethod,
    ParameterSnapshot,
    PeriodType,
    RecordStatus,
)
from packages.infrastructure.reporting import render_report_docx
from packages.standards.carbon_material import (
    SOURCE_BAKING,
    SOURCE_CALCINATION,
    SOURCE_EXPORTED_ELECTRICITY,
    SOURCE_EXPORTED_HEAT,
    SOURCE_FGD,
    SOURCE_FUME,
    SOURCE_FUEL,
    SOURCE_GRAPHITIZATION,
    SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_PURCHASED_HEAT,
    STANDARD_ID,
)

_SAMPLE_AT = datetime.now(timezone.utc)
_SAMPLE_PERIOD = AccountingPeriod(
    PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)
)


def _snapshot_specs() -> tuple[tuple[str, str, str, ParameterSelectionMethod, str], ...]:
    specs: list[tuple[str, str, str, ParameterSelectionMethod, str]] = []
    for fuel_id, lhv, carbon, carbon_unit, oxidation in (
        ("fuel-gas", "35.5", "0.0153", "tC/GJ", "0.98"),
        ("fuel-coke", "28.0", "0.82", "tC/t", "0"),
    ):
        specs.extend((
            (f"CAR-FLD-F01-{fuel_id}-LHV", lhv, "GJ/t", ParameterSelectionMethod.ENTERPRISE_MEASURED, "燃料检测报告"),
            (f"CAR-FLD-F01-{fuel_id}-CARBON", carbon, carbon_unit, ParameterSelectionMethod.STANDARD_REQUIRED, "附录C.1"),
            (f"CAR-FLD-F01-{fuel_id}-FOX", oxidation, "ratio", ParameterSelectionMethod.SYSTEM_RECOMMENDED, "附录C.1"),
        ))
    specs.append(("CAR-FLD-P04A-fume-1-FCH", "0.027", "tC/GJ", ParameterSelectionMethod.ENTERPRISE_MEASURED, "焦油检测报告"))
    for facility, component, index in (("fgd-1", "CaCO3", 0), ("fgd-1", "MgCO3", 1), ("fgd-2", "CaCO3", 0)):
        prefix = f"CAR-FLD-P04B-{facility}-{index}"
        specs.extend((
            (prefix + "-I", "0.92", "ratio", ParameterSelectionMethod.ENTERPRISE_MEASURED, "脱硫剂检测报告"),
            (prefix + "-EF1", "0.44", "tCO2/t", ParameterSelectionMethod.STANDARD_REQUIRED, "附录C.2"),
            (prefix + "-TR", "0.95", "ratio", ParameterSelectionMethod.SYSTEM_RECOMMENDED, "附录C.2"),
        ))
    for detail_id, value in (("power-in-1", "0.62"), ("power-in-2", "0.48")):
        specs.append((detail_id, value, "tCO2/MWh", ParameterSelectionMethod.STANDARD_REQUIRED, "电力因子文件"))
    for detail_id, value in (("power-out-1", "0.62"), ("power-out-2", "0.50")):
        specs.append((f"CAR-FLD-POWER-EXPORTED-EF.{detail_id}", value, "tCO2/MWh", ParameterSelectionMethod.ENTERPRISE_MEASURED, "输出电力结算单"))
    for detail_id, value in (("heat-in-1", "0.11"), ("heat-in-2", "0.12"), ("heat-out-1", "0.11")):
        specs.append((f"CAR-FLD-HEAT-{detail_id}-EF3", value, "tCO2/GJ", ParameterSelectionMethod.STANDARD_REQUIRED, "热力因子来源"))
    return tuple(specs)


def _parameter_snapshots() -> tuple[ParameterSnapshot, ...]:
    snapshots = []
    for index, (detail_id, value, unit, method, location) in enumerate(_snapshot_specs(), 1):
        snapshots.append(ParameterSnapshot(
            snapshot_id=f"snapshot.rpt02.{index}",
            parameter_id=f"parameter.rpt02.{index}",
            factor_id=None,
            value_used=value,
            unit_used=unit,
            source_id="SRC-RPT02-EXAMPLE",
            source_version="2025",
            selection_method=method,
            selection_reason="来自该演示核算记录冻结的参数快照。",
            standard_id=STANDARD_ID,
            snapshot_at=_SAMPLE_AT,
            source_location="验收演示输入（非企业凭证）",
            detail_id=detail_id,
        ))
    return tuple(snapshots)


def _material(role: str, name: str, mass: str, fixed: str, volatile: str) -> dict[str, str]:
    return {
        "role": role,
        "name": name,
        "mass_t": mass,
        "fixed_carbon_percent": fixed,
        "fixed_carbon_source": "MEASURED",
        "volatile_matter_percent": volatile,
        "volatile_matter_source": "MEASURED",
    }


def build_acceptance_case(origin: str = "GUI") -> tuple[AccountingRecord, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return a synthetic frozen-record fixture for mapping tests only."""
    normalized_origin = origin.upper()
    if normalized_origin not in {"GUI", "EXCEL_R2"}:
        raise ValueError("origin must be GUI or EXCEL_R2")
    suffix = "gui" if normalized_origin == "GUI" else "excel"
    enterprise = "验收演示输入（合成映射夹具）"
    snapshots = _parameter_snapshots()
    lines = [
        CalculationLine("CAR-FLD-DIRECT-RESULT", "CAR-SRC-DIRECT-RESULT", "GEN-GAS-CO2", "7.3", "tCO2"),
        CalculationLine("CAR-FLD-INDIRECT-RESULT", "CAR-SRC-INDIRECT-RESULT", "GEN-GAS-CO2", "2.4", "tCO2"),
        CalculationLine("CAR-FLD-TOTAL-RESULT", "CAR-SRC-TOTAL-RESULT", "GEN-GAS-CO2", "9.7", "tCO2"),
        CalculationLine(f"{SOURCE_FUEL}.fuel-gas", SOURCE_FUEL, "GEN-GAS-CO2", "1.4", "tCO2"),
        CalculationLine(f"{SOURCE_FUEL}.fuel-coke", SOURCE_FUEL, "GEN-GAS-CO2", "0.6", "tCO2"),
    ]
    calculation_result = CalculationResult(
        result_id=f"result.rpt02.{suffix}",
        standard_id=STANDARD_ID,
        algorithm_version="CAR-RPT02-FROZEN-SAMPLE",
        lines=tuple(lines),
        total_amount="9.7",
        total_unit="tCO2",
        calculated_at=_SAMPLE_AT,
    )
    record = AccountingRecord(
        record_id=f"record.rpt02.{suffix}",
        standard_id=STANDARD_ID,
        algorithm_version=calculation_result.algorithm_version,
        created_at=_SAMPLE_AT,
        input_snapshot=AccountingInput(
            input_id=f"input.rpt02.{suffix}",
            standard_id=STANDARD_ID,
            period=_SAMPLE_PERIOD,
            enterprise_name=enterprise,
            boundary_component_ids=("boundary.main",),
        ),
        calculation_result=calculation_result,
        status=RecordStatus.COMPLETED,
        parameter_snapshots=snapshots,
        standard_version="2024",
    )

    raw: dict[str, Any] = {
        "source_states": [
            {"source_id": source_id, "status": "INVOLVED"}
            for source_id in (
                SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING, SOURCE_GRAPHITIZATION,
                SOURCE_FUME, SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY,
                SOURCE_EXPORTED_ELECTRICITY, SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_HEAT,
            )
        ],
        "fuel_inputs": [
            {
                "fuel_id": "fuel-gas", "fuel_type": "NATURAL_GAS", "path": "VOLUME",
                "activity": {"value": "4.0", "unit": "ten_thousand_Nm3", "source_type": "METER", "source_reference": "验收演示输入（非企业凭证）"},
                "lower_heating_value": {"value": "35.5", "unit": "GJ/t"},
                "carbon_content": {"value": "0.0153", "unit": "tC/GJ"},
                "oxidation_rate": {"value": "0.98", "unit": "ratio"},
            },
            {
                "fuel_id": "fuel-coke", "fuel_type": "COKE", "path": "MASS",
                "activity": {"value": "0", "unit": "t", "source_type": "METER", "source_reference": "验收演示输入（非企业凭证）"},
                "lower_heating_value": {"value": "28.0", "unit": "GJ/t"},
                "carbon_content": {"value": "0.82", "unit": "tC/t"},
                "oxidation_rate": {"value": "0", "unit": "ratio"},
            },
        ],
        "calcinations": [
            {"instance_id": "calc-1", "material_rows": [
                _material("calcination_feed", "煅烧原料甲", "100", "0.80", "0.02"),
                _material("calcination_feed", "煅烧原料乙", "20", "0.75", "0.03"),
                _material("calcined_product", "煅后料", "90", "0.96", "0.01"),
                _material("underburn_recovered", "欠烧煅料", "2", "0.70", "0.04"),
                _material("carbon_dust", "炭粉尘", "1", "0.65", "0.08"),
            ]},
            {"instance_id": "calc-2", "material_rows": [
                _material("calcination_feed", "煅烧原料丙", "50", "0.78", "0.02"),
                _material("calcined_product", "煅后料乙", "45", "0.95", "0.01"),
            ]},
        ],
        "bakings": [{"instance_id": "bake-1", "material_rows": [
            _material("baking_filler", "填充料", "12", "0.70", "0.10"),
            _material("green_baking_product", "待焙烧品甲", "40", "0.82", "0.03"),
            _material("green_baking_product", "待焙烧品乙", "20", "0.79", "0.04"),
            _material("baking_byproduct", "焙烧粉尘", "1", "0.25", "0.20"),
            _material("baked_product", "焙烧产品", "55", "0.97", "0.01"),
        ]}],
        "graphitizations": [{"instance_id": "graph-1", "material_rows": [
            _material("graphitization_packing", "保温料", "10", "0.60", "0.12"),
            _material("green_graphitization_product", "待石墨化品甲", "30", "0.84", "0.03"),
            _material("green_graphitization_product", "待石墨化品乙", "15", "0.80", "0.04"),
            _material("graphitization_byproduct", "石墨化残块", "1", "0.35", "0.10"),
            _material("graphitized_product", "石墨化产品", "42", "0.99", "0.00"),
        ]}],
        "fume_incinerations": [
            {"instance_id": "fume-1", "q": {"value": "12000", "unit": "Nm3/h"}, "qvar": {"value": "45", "unit": "mg/Nm3"}, "hm": {"value": "38", "unit": "GJ/t"}, "fch": {"value": "0.027", "unit": "tC/GJ"}, "fox": {"value": "0.98", "unit": "ratio"}, "duration": {"value": "300", "unit": "d"}},
            {"instance_id": "fume-2", "q": {"value": "8000", "unit": "Nm3/h"}, "qvar": {"value": "30", "unit": "mg/Nm3"}, "hm": {"value": "37", "unit": "GJ/t"}, "fch": {"value": "0.027", "unit": "tC/GJ"}, "fox": {"value": "0.97", "unit": "ratio"}, "duration": {"value": "250", "unit": "d"}},
        ],
        "fgd_units": [
            {"instance_id": "fgd-1", "components": [
                {"carbonate_type": "CaCO3", "amount": {"value": "2", "unit": "t"}, "carbonate_fraction": {"value": "0.92", "unit": "ratio"}, "emission_factor": {"value": "0.44", "unit": "tCO2/t"}, "conversion_rate": {"value": "0.95", "unit": "ratio"}},
                {"carbonate_type": "MgCO3", "amount": {"value": "2", "unit": "t"}, "carbonate_fraction": {"value": "0.88", "unit": "ratio"}, "emission_factor": {"value": "0.52", "unit": "tCO2/t"}, "conversion_rate": {"value": "0.90", "unit": "ratio"}},
            ]},
            {"instance_id": "fgd-2", "components": [
                {"carbonate_type": "CaCO3", "amount": {"value": "1", "unit": "t"}, "carbonate_fraction": {"value": "0.91", "unit": "ratio"}, "emission_factor": {"value": "0.44", "unit": "tCO2/t"}, "conversion_rate": {"value": "0.95", "unit": "ratio"}},
            ]},
        ],
        "electricity_details": [
            {"detail_id": "power-in-1", "attribute": "ORDINARY", "electricity_amount": {"value": "3.0", "unit": "MWh", "source_type": "METER", "source_reference": "验收演示输入（非企业凭证）"}, "factor": {"value": "0.62", "unit": "tCO2/MWh"}},
            {"detail_id": "power-in-2", "attribute": "NONFOSSIL", "electricity_amount": {"value": "1.0", "unit": "MWh", "source_type": "METER", "source_reference": "验收演示输入（非企业凭证）"}, "factor": {"value": "0.48", "unit": "tCO2/MWh"}},
        ],
        "exported_electricity": [
            {"line_id": "power-out-1", "electricity_amount": "0.5", "electricity_unit": "MWh", "attribute": "ORDINARY", "factor": {"value": "0.62", "unit": "tCO2/MWh"}},
            {"line_id": "power-out-2", "electricity_amount": "0.2", "electricity_unit": "MWh", "attribute": "ORDINARY", "factor": {"value": "0.50", "unit": "tCO2/MWh"}},
        ],
        "purchased_heat": [
            {"line_id": "heat-in-1", "steam_amount_t": "4", "amount": {"value": "4", "unit": "t", "source_type": "METER"}, "steam_kind": "SATURATED", "pressure_mpa": {"value": "0.2", "unit": "MPa"}, "enthalpy": {"value": "2716", "unit": "kJ/kg"}},
            {"line_id": "heat-in-2", "steam_amount_t": "2", "amount": {"value": "2", "unit": "t", "source_type": "METER"}, "steam_kind": "SUPERHEATED", "pressure_mpa": {"value": "1.0", "unit": "MPa"}, "temperature_c": {"value": "250", "unit": "C"}, "enthalpy": {"value": "2940", "unit": "kJ/kg"}},
        ],
        "exported_heat": [
            {"line_id": "heat-out-1", "steam_amount_t": "1", "amount": {"value": "1", "unit": "t", "source_type": "METER"}, "steam_kind": "SATURATED", "pressure_mpa": {"value": "0.2", "unit": "MPa"}, "enthalpy": {"value": "2716", "unit": "kJ/kg"}},
        ],
    }
    formula_steps = []
    for instance, amount in (("calc-1", "1.5"), ("calc-2", "0.5")):
        formula_steps.append({"emission_source_id": SOURCE_CALCINATION, "process_instance_id": instance, "intermediate_result": amount, "input_variables": [{"name": "gc", "value": "100", "unit": "t"}]})
    formula_steps.extend((
        {"emission_source_id": SOURCE_BAKING, "process_instance_id": "bake-1", "intermediate_result": "1.2"},
        {"emission_source_id": SOURCE_GRAPHITIZATION, "process_instance_id": "graph-1", "intermediate_result": "1.0"},
        {"emission_source_id": SOURCE_FUME, "process_instance_id": "fume-1", "intermediate_result": "0.5"},
        {"emission_source_id": SOURCE_FUME, "process_instance_id": "fume-2", "intermediate_result": "0.2"},
        {"emission_source_id": SOURCE_FGD, "process_instance_id": "fgd-1", "intermediate_result": "0.3"},
        {"emission_source_id": SOURCE_FGD, "process_instance_id": "fgd-2", "intermediate_result": "0.1"},
        {"emission_source_id": SOURCE_PURCHASED_ELECTRICITY, "process_instance_id": "power-in-1", "intermediate_result": "1.86"},
        {"emission_source_id": SOURCE_PURCHASED_ELECTRICITY, "process_instance_id": "power-in-2", "intermediate_result": "0.48"},
        {"emission_source_id": SOURCE_EXPORTED_ELECTRICITY, "process_instance_id": "power-out-1", "intermediate_result": "0.31"},
        {"emission_source_id": SOURCE_EXPORTED_ELECTRICITY, "process_instance_id": "power-out-2", "intermediate_result": "0.10"},
        {"emission_source_id": SOURCE_PURCHASED_HEAT, "process_instance_id": "heat-in-1", "intermediate_result": "0.50", "calculation_provenance": {"enthalpy_used_kj_per_kg": "2716", "enthalpy_source": "SATURATED_TABLE", "table": "C.1", "automatic_reference_enthalpy_kj_per_kg": "2716"}},
        {"emission_source_id": SOURCE_PURCHASED_HEAT, "process_instance_id": "heat-in-2", "intermediate_result": "0.30", "calculation_provenance": {"enthalpy_used_kj_per_kg": "2940", "enthalpy_source": "SUPERHEATED_TABLE", "table": "C.2", "automatic_reference_enthalpy_kj_per_kg": "2940"}},
        {"emission_source_id": SOURCE_EXPORTED_HEAT, "process_instance_id": "heat-out-1", "intermediate_result": "0.20", "calculation_provenance": {"enthalpy_used_kj_per_kg": "2716", "enthalpy_source": "SATURATED_TABLE", "table": "C.1", "automatic_reference_enthalpy_kj_per_kg": "2716"}},
        {"formula_id": "CAR-FML-GAS-CONTROL-TOTAL-001", "input_variables": [{"name": "ER subtotal", "value": "0.7"}, {"name": "ED subtotal", "value": "0.4"}]},
    ))
    trace: dict[str, Any] = {
        "aggregations": {"ES": "7.3", "EI": "2.4", "ET": "9.7"},
        "source_subtotals": {
            "fuel": "2.0", "calcination": "2.0", "baking": "1.2", "graphitization": "1.0",
            "purchased_electricity": "2.34", "exported_electricity": "0.41",
            "purchased_heat": "0.8", "exported_heat": "0.2",
        },
        "formula_steps": formula_steps,
    }
    provenance = {
        "mapping_version": "SM01-RPT02-ACCEPTANCE",
        "ingress_source": "SYNTHETIC_MAPPING_FIXTURE",
        "ingress_artifact": "合成映射测试样例（不代表真实来源）",
    }
    reporting = {"boundary_description": "炭素材料生产厂区边界"}
    qualification = {"eligible": True, "message": "符合年度报告周期要求。"}
    return record, raw, trace, provenance, reporting, qualification


def build_acceptance_model(origin: str = "GUI"):
    record, raw, trace, provenance, reporting, qualification = build_acceptance_case(origin)
    return build_report_model(
        record,
        raw,
        trace,
        provenance,
        reporting,
        qualification,
        supplementary_info={"prepared_on": "2026-10-10", "supplementary_note": "合成映射单测夹具；不可作为正式Record或企业核算报告。"},
        today=date(2026, 10, 9),
    )


_DEMO_SOURCE_NOTE = "验收演示输入（示例数值，非企业凭证）"
_SAMPLE_DATE = _SAMPLE_AT.date()


def _json_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _annotate_demo_input(value: object) -> object:
    """Label manually supplied regression-fixture values without changing their numbers."""
    if isinstance(value, InputValue):
        if not value.source_reference:
            return replace(value, source_reference=_DEMO_SOURCE_NOTE)
        return value
    if isinstance(value, ParameterValue):
        if value.source_kind in {ParameterSourceKind.MEASURED, ParameterSourceKind.USER_DEFINED} or value.source_location == "G06 regression fixture":
            return replace(value, source_location=_DEMO_SOURCE_NOTE)
        return value
    if isinstance(value, tuple):
        return tuple(_annotate_demo_input(item) for item in value)
    if isinstance(value, list):
        return [_annotate_demo_input(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _annotate_demo_input(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        updates = {}
        for item in fields(value):
            current = getattr(value, item.name)
            if item.name == "source_reference" and not current:
                updates[item.name] = _DEMO_SOURCE_NOTE
            else:
                updates[item.name] = _annotate_demo_input(current)
        return replace(value, **updates)
    return value


def _gui_canonical_input():
    # Reuse the repository's complete Canonical-input regression fixture, then
    # explicitly relabel all hand-entered example evidence as non-enterprise data.
    from tests.test_g06_carbon_material import _full_input

    original = _full_input()
    annotated = _annotate_demo_input(original)
    reporting = replace(
        annotated.reporting_data,
        boundary_description="验收演示输入边界（仅用于报告表式验收）",
        other_report_information="数值为软件验收演示输入，不代表真实企业活动数据或企业凭证。",
    )
    return replace(
        annotated,
        input_id="input.rpt02.gui-canonical-demo",
        enterprise_name="验收演示输入（Canonical表单数据）",
        reporting_data=reporting,
    )


def _write_appendix_b_input(path: Path, template_service: ExcelTemplateService) -> None:
    # Start from the approved nine-sheet resource and preserve its authored layout.
    template_service.copy_to(path)
    workbook = load_workbook(path)
    try:
        fuel = workbook["B.2"]
        fuel["A4"], fuel["B4"], fuel["C4"], fuel["D4"] = "天然气", 1, 0.5, "实测值"
        fuel["H4"], fuel["I4"] = 98, "实测值"
        workbook.save(path)
    finally:
        workbook.close()


def _source_evidence(value: object, path: str = "input") -> list[dict[str, object]]:
    evidence_fields = {
        "source_reference", "source_type", "source_kind", "source_ids", "evidence_ref_ids",
        "source_location", "monitoring_location", "applies_to", "source_level",
        "source_version", "source_id", "factor_id", "reason", "note",
    }
    found = []
    if is_dataclass(value) and not isinstance(value, type):
        value_fields = fields(value)
        if {item.name for item in value_fields} & evidence_fields:
            found.append({"path": path, "type": type(value).__name__, "values": _json_value(value)})
        for item in value_fields:
            found.extend(_source_evidence(getattr(value, item.name), f"{path}.{item.name}"))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(_source_evidence(item, f"{path}.{key}"))
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            found.extend(_source_evidence(item, f"{path}[{index}]"))
    return found


def _appendix_b_ingress_provenance(preview, unit, workbook_path: Path) -> dict[str, object]:
    return {
        "source": preview.provenance.source or "EXCEL_APPENDIX_B",
        "workbook": {
            "sha256": preview.provenance.workbook_sha256,
            "file_name": workbook_path.name,
            "template_id": preview.provenance.template_id,
            "template_version": preview.provenance.template_version,
            "standard_id": preview.provenance.standard_id,
            "standard_version": preview.provenance.standard_version,
            "ingress_policy_id": preview.provenance.ingress_policy_id,
            "imported_at": preview.provenance.imported_at.isoformat(),
        },
        "accounting_unit": {
            "importer_unit_id": unit.unit_id,
            "name": unit.name,
            "unit_type": unit.unit_type.value,
        },
        "numeric_cell_evidence": [
            {
                "sheet": item.sheet,
                "cell": item.cell,
                "raw_cell_type": item.raw_cell_type,
                "workbook_value_repr": item.workbook_value_repr,
                "raw_numeric_lexical": item.serialized_numeric_text,
                "normalized_decimal_lexical": str(item.normalized_decimal),
                "accounting_unit_id": item.accounting_unit_id,
            }
            for item in preview.numeric_evidence
            if item.accounting_unit_id in (None, unit.unit_id)
        ],
        "canonical_source_evidence": _source_evidence(unit.input_value),
        "unit_warnings": [_json_value(item) for item in unit.warnings],
        "workbook_warnings": [_json_value(item) for item in preview.warnings],
    }


def _formal_record(use_case, input_value, *, ingress_provenance=None):
    outcome = use_case.calculate(
        input_value,
        calculated_at=_SAMPLE_AT,
        ingress_provenance=ingress_provenance,
    )
    if not outcome.successful or outcome.record is None:
        details = "；".join(problem.message for problem in outcome.problems)
        raise RuntimeError(f"验收演示输入未能生成正式Record：{details}")
    return outcome.record


def _frozen_record_payload(repository, record) -> dict[str, object]:
    record_id = record.record_id
    snapshots = {
        "raw_input": repository.get_raw_input_snapshot(record_id),
        "effective_rule_set": repository.get_effective_rule_set(record_id),
        "trace": repository.get_trace_snapshot(record_id),
        "provenance": repository.get_provenance_snapshot(record_id),
        "reporting": repository.get_reporting_snapshot(record_id),
        "qualification": repository.get_report_qualification(record_id),
    }
    return {
        "record": _json_value(record),
        "snapshots": _json_value(snapshots),
    }


def _record_evidence(repository, record, report, *, origin: str, input_description: str) -> dict[str, object]:
    record_id = record.record_id
    frozen_payload = _frozen_record_payload(repository, record)
    frozen_hash = sha256(json.dumps(frozen_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    totals = {
        line.line_id: str(line.amount)
        for line in record.calculation_result.lines
        if line.line_id in {"CAR-FLD-DIRECT-RESULT", "CAR-FLD-INDIRECT-RESULT", "CAR-FLD-TOTAL-RESULT"}
    }
    return {
        "origin": origin,
        "input_description": input_description,
        "native_gui_interaction_verified": False if origin == "GUI_CANONICAL_INPUT" else None,
        "record_id": record_id,
        "standard_id": record.standard_id,
        "algorithm_version": record.algorithm_version,
        "standard_version": record.standard_version,
        "created_at": record.created_at.isoformat(),
        "status": record.status.value,
        "frozen_es_ei_et": totals,
        "record_and_snapshot_sha256": frozen_hash,
        "report_layout_id": report.layout_id,
        "report_b1_es": next(section for section in report.sections if section.section_id == "b1").tables[0].rows[-2].cells[2].value,
        "report_b1_et": next(section for section in report.sections if section.section_id == "b1").tables[0].rows[-1].cells[2].value,
        "approved_template_sha256": report.template_sha256,
    }


def _write_new_file(path: Path, content: bytes) -> None:
    created = False
    try:
        with path.open("xb") as stream:
            created = True
            stream.write(content)
            stream.flush()
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise


def write_acceptance_samples(
    output_dir: Path,
    evidence_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Create Word samples from saved formal Records; refuse all existing targets."""
    output_dir = Path(output_dir)
    evidence_dir = Path(evidence_dir) if evidence_dir is not None else REPOSITORY_ROOT / "build" / "rpt02"
    gui_path = output_dir / "GHG-RPT02_GUI_Canonical_Record_Appendix_B.docx"
    excel_path = output_dir / "GHG-RPT02_Excel_Appendix_B_Record_Appendix_B.docx"
    records_path = evidence_dir / "records.sqlite"
    manifest_path = evidence_dir / "acceptance-evidence.json"
    frozen_records_path = output_dir / "records-and-snapshots.json"
    targets = (gui_path, excel_path, records_path, manifest_path, frozen_records_path)
    existing = tuple(path for path in targets if path.exists())
    if existing:
        raise FileExistsError("为避免覆盖用户文件，目标已存在：" + "、".join(str(path) for path in existing))

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    created_targets: list[Path] = []
    try:
        with tempfile.TemporaryDirectory(prefix="ghg-rpt02-") as temporary:
            stage = Path(temporary)
            stage_records = stage / "records.sqlite"
            stage_gui = stage / gui_path.name
            stage_excel = stage / excel_path.name
            stage_manifest = stage / manifest_path.name
            stage_frozen_records = stage / frozen_records_path.name
            catalog_path = stage / "catalog.sqlite"

            build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path)
            catalog_repository = SQLiteCatalogRepository(catalog_path)
            catalog_service = CatalogQueryService(catalog_repository)
            resolver = create_g06_parameter_resolver(catalog_repository)
            repository = SQLiteRecordRepository(stage_records)
            calculator = CarbonMaterialCalculator(parameter_resolver=resolver)
            preview_use_case = CarbonAccountingPreviewUseCase(calculator)
            template_service = ExcelTemplateService.default()
            importer = AppendixBWorkbookImporter(
                preview_use_case=preview_use_case,
                catalog_service=catalog_service,
                template_service=template_service,
            )
            use_case = CarbonAccountingUseCase(calculator, repository)

            gui_input = _gui_canonical_input()
            gui_record = _formal_record(use_case, gui_input)
            gui_saved = repository.get(gui_record.record_id)
            if gui_saved is None:
                raise RuntimeError("Canonical输入核算后未从独立records.sqlite读取到正式Record。")

            workbook_path = stage / "GHG-RPT02_Excel_Appendix_B_demo.xlsx"
            _write_appendix_b_input(workbook_path, template_service)
            preview = importer.import_preview(
                workbook_path,
                context=AppendixBImportContext(
                    period=_SAMPLE_PERIOD,
                    boundary_confirmed=True,
                    enterprise_name="验收演示输入（附录B工作簿）",
                    fuel_path_overrides={"B.2!B4": FuelPath.VOLUME},
                ),
            )
            valid_units = [unit for unit in preview.units if unit.can_calculate and unit.input_value is not None]
            if len(valid_units) != 1:
                problem_text = "；".join(error.message for unit in preview.units for error in unit.errors)
                raise RuntimeError(f"附录B验收输入必须产生一个可正式核算单元；现有{len(valid_units)}个。{problem_text}")
            unit = valid_units[0]
            if unit.result is None:
                raise RuntimeError("AppendixBWorkbookImporter未返回可计算预览结果。")
            excel_record = _formal_record(
                use_case,
                unit.input_value,
                ingress_provenance=_appendix_b_ingress_provenance(preview, unit, workbook_path),
            )
            excel_saved = repository.get(excel_record.record_id)
            if excel_saved is None:
                raise RuntimeError("附录B Excel正式核算后未从独立records.sqlite读取到正式Record。")
            if excel_saved.calculation_result.total_amount != unit.result.total_amount:
                raise AssertionError("附录B Excel预览与正式Record结果不一致。")

            # Exercise the same frozen Canonical input through the GUI/Application
            # path by removing only the Excel ingress envelope; compare B.1-B.9
            # business sections without creating another deliverable DOCX.
            parity_input = replace(unit.input_value, input_id="input.rpt02.excel-canonical-parity")
            parity_repository = SQLiteRecordRepository(stage / "parity-records.sqlite")
            parity_use_case = CarbonAccountingUseCase(calculator, parity_repository)
            parity_record = _formal_record(parity_use_case, parity_input)
            parity_saved = parity_repository.get(parity_record.record_id)
            if parity_saved is None:
                raise RuntimeError("相同Canonical输入的对照核算未保存正式Record。")

            manifest_records = []
            frozen_record_exports = []
            business_reports = {}
            for saved, destination, origin, description, supplementary in (
                (
                    gui_saved,
                    stage_gui,
                    "GUI_CANONICAL_INPUT",
                    "tests.test_g06_carbon_material._full_input经Canonical CarbonMaterialInput与正式CarbonAccountingUseCase核算；非原生GUI按钮交互实测。",
                    "验收演示输入；Canonical表单数据经正式核算用例写入不可变Record；不代表真实企业核算或企业凭证。",
                ),
                (
                    excel_saved,
                    stage_excel,
                    "EXCEL_APPENDIX_B_PREVIEW_TO_FORMAL_USE_CASE",
                    "批准的附录B九表工作簿由AppendixBWorkbookImporter真实预览，unit.can_calculate为真后将Canonical输入传入正式CarbonAccountingUseCase并写入Record。",
                    "验收演示输入；附录B Excel预览单元经正式核算用例写入不可变Record；活动数据来源为演示值，不是企业凭证。",
                ),
            ):
                report = build_saved_record_report(
                    repository,
                    saved,
                    supplementary_info={
                        "enterprise_name": saved.input_snapshot.enterprise_name,
                        "prepared_on": _SAMPLE_DATE.isoformat(),
                        "supplementary_note": supplementary,
                    },
                )
                b1 = next(section for section in report.sections if section.section_id == "b1").tables[0]
                recorded_totals = frozen_totals(saved, repository.get_trace_snapshot(saved.record_id))
                if (b1.rows[-2].cells[2].value, b1.rows[-1].cells[2].value) != (recorded_totals["ES"], recorded_totals["ET"]):
                    raise AssertionError("Word B.1未使用正式Record冻结的ES和ET。")
                render_report_docx(report, destination)
                business_reports[origin] = report
                manifest_records.append(_record_evidence(repository, saved, report, origin=origin, input_description=description))
                frozen_record_exports.append({
                    "origin": origin,
                    "record_and_snapshots_sha256": manifest_records[-1]["record_and_snapshot_sha256"],
                    **_frozen_record_payload(repository, saved),
                })

            parity_report = build_saved_record_report(
                parity_repository,
                parity_saved,
                supplementary_info={
                    "enterprise_name": excel_saved.input_snapshot.enterprise_name,
                    "prepared_on": _SAMPLE_DATE.isoformat(),
                    "supplementary_note": "验收演示输入；附录B Excel预览单元经正式核算用例写入不可变Record；活动数据来源为演示值，不是企业凭证。",
                },
            )
            excel_report = business_reports["EXCEL_APPENDIX_B_PREVIEW_TO_FORMAL_USE_CASE"]
            business_section_ids = {f"b{number}" for number in range(1, 10)}
            excel_business_sections = [
                _json_value(section) for section in excel_report.sections
                if section.section_id in business_section_ids
            ]
            canonical_business_sections = [
                _json_value(section) for section in parity_report.sections
                if section.section_id in business_section_ids
            ]
            if excel_business_sections != canonical_business_sections:
                raise AssertionError("同一附录B Excel Canonical输入的GUI/Application与Excel来源报告B.1-B.9业务内容不一致。")
            parity_evidence = {
                "same_canonical_input": True,
                "input_comparison": "AppendixBWorkbookImporter的Canonical unit.input_value仅变更input_id；Canonical/Application路径不传入ingress_provenance。",
                "source_excel_record_id": excel_saved.record_id,
                "canonical_path_record_id": parity_saved.record_id,
                "compared_section_ids": [f"b{number}" for number in range(1, 10)],
                "business_sections_equal": True,
                "excel_business_sections_sha256": sha256(json.dumps(excel_business_sections, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "canonical_business_sections_sha256": sha256(json.dumps(canonical_business_sections, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "parity_record_persisted_in_deliverable_database": False,
            }
            frozen_bundle = {
                "task": "GHG-RPT02",
                "notice": "以下为两个可交付Word样例对应的正式不可变Record与创建时冻结快照。所有活动数据为软件验收演示输入，不是企业业务数据或企业凭证。",
                "records": frozen_record_exports,
            }
            stage_frozen_records.write_text(json.dumps(frozen_bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

            manifest = {
                "task": "GHG-RPT02",
                "generated_at": _SAMPLE_AT.isoformat(),
                "sample_status": "FORMAL_RECORDS_FROM_APPLICATION_USE_CASE",
                "notice": "验收演示输入，不是实际企业业务Record或企业凭证；系统选用的标准参数来源按每条Record冻结快照保留。",
                "canonical_reference_data_source": DEFAULT_SOURCE_PATH.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix(),
                "catalog_database": "由本仓Canonical reference-data源临时构建，仅用于正式计算；Word生成时只读取records.sqlite中的冻结Record和快照。",
                "excel_appendix_b_preview": {
                    "can_calculate": unit.can_calculate,
                    "preview_total_amount": str(unit.result.total_amount),
                    "preview_total_unit": unit.result.total_unit,
                    "workbook_sha256": preview.provenance.workbook_sha256,
                    "template_id": preview.provenance.template_id,
                    "template_version": preview.provenance.template_version,
                    "ingress_policy_id": preview.provenance.ingress_policy_id,
                    "numeric_cell_evidence": _appendix_b_ingress_provenance(preview, unit, workbook_path)["numeric_cell_evidence"],
                },
                "records": manifest_records,
                "same_input_gui_canonical_vs_excel_appendix_b": parity_evidence,
                "files": {
                    gui_path.name: {"sha256": sha256(stage_gui.read_bytes()).hexdigest()},
                    excel_path.name: {"sha256": sha256(stage_excel.read_bytes()).hexdigest()},
                    "records.sqlite": {"sha256": sha256(stage_records.read_bytes()).hexdigest()},
                    frozen_records_path.name: {"sha256": sha256(stage_frozen_records.read_bytes()).hexdigest()},
                },
                "report_export_history_note": "验收样例由build_saved_record_report和现有DOCX renderer直接从已保存Record生成；文件保存及导出审计业务仍由PR #37共享Word导出入口负责。",
            }
            stage_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

            payloads = (
                (gui_path, stage_gui.read_bytes()),
                (excel_path, stage_excel.read_bytes()),
                (records_path, stage_records.read_bytes()),
                (manifest_path, stage_manifest.read_bytes()),
                (frozen_records_path, stage_frozen_records.read_bytes()),
            )
            for target, data in payloads:
                _write_new_file(target, data)
                created_targets.append(target)
    except Exception:
        for target in reversed(created_targets):
            target.unlink(missing_ok=True)
        raise
    return gui_path, excel_path



def _multi_source_canonical_input():
    """Repeat validated demo sources as distinct canonical rows/process units."""
    from packages.standards.carbon_material import (
        BakingInput,
        CalcinationInput,
        FGDInput,
        FuelType,
        GraphitizationInput,
    )
    from packages.standards.carbon_material_normalization import (
        MaterialDataSource,
        MaterialInputLine,
        MaterialRole,
    )

    base = _gui_canonical_input()

    # These material values and roles match the passing multi-row normalization
    # fixture in tests/test_uat01b_material_steam.py. Each facility receives
    # unique process and material IDs; no equation or calculator behavior is
    # introduced here.
    material_examples = {
        "calcination": (
            ("feed-a", MaterialRole.CALCINATION_FEED, "待煅烧原料甲", "100", "95", "10"),
            ("feed-b", MaterialRole.CALCINATION_FEED, "待煅烧原料乙", "200", "75", "5"),
            ("product-a", MaterialRole.CALCINED_PRODUCT, "煅后料甲", "250", "80", "2"),
            ("underburn-a", MaterialRole.UNDERBURN_RECOVERED, "欠烧煅料", "20", "50", None),
            ("dust-a", MaterialRole.CARBON_DUST, "炭粉尘", "10", "25", None),
        ),
        "baking": (
            ("filler-a", MaterialRole.BAKING_FILLER, "焙烧填充料甲", "20", "90", "1"),
            ("green-a", MaterialRole.GREEN_BAKING_PRODUCT, "待焙烧品甲", "100", "80", "2"),
            ("green-b", MaterialRole.GREEN_BAKING_PRODUCT, "待焙烧品乙", "50", "60", "4"),
            ("baked-a", MaterialRole.BAKED_PRODUCT, "焙烧产品", "100", "98", None),
            ("byproduct-a", MaterialRole.BAKING_BYPRODUCT, "粉尘", "4", "50", None),
            ("byproduct-b", MaterialRole.BAKING_BYPRODUCT, "碎屑", "1", "30", None),
        ),
        "graphitization": (
            ("packing-a", MaterialRole.GRAPHITIZATION_PACKING, "石墨化保温料", "15", "75", "1"),
            ("green-a", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品甲", "80", "80", None),
            ("green-b", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品乙", "40", "60", None),
            ("graphitized-a", MaterialRole.GRAPHITIZED_PRODUCT, "石墨化产品", "90", "90", None),
            ("dust-a", MaterialRole.GRAPHITIZATION_BYPRODUCT, "石墨化粉尘", "3", "50", None),
            ("residue-a", MaterialRole.GRAPHITIZATION_BYPRODUCT, "石墨化残块", "2", "25", None),
        ),
    }

    def material_rows(process: str, instance: str):
        return tuple(
            MaterialInputLine(
                f"rpt02-multi.{instance}.{line_id}", role, name, mass, fixed,
                MaterialDataSource.MEASURED, volatile, MaterialDataSource.MEASURED,
            )
            for line_id, role, name, mass, fixed, volatile in material_examples[process]
        )

    calcinations = tuple(
        CalcinationInput(k1=base.calcination.k1, instance_id=f"rpt02-multi-calc-{suffix}", material_rows=material_rows("calcination", f"calc-{suffix}"))
        for suffix in ("a", "b")
    )
    bakings = tuple(
        BakingInput(k2=base.baking.k2, instance_id=f"rpt02-multi-bake-{suffix}", material_rows=material_rows("baking", f"bake-{suffix}"))
        for suffix in ("a", "b")
    )
    graphitizations = tuple(
        GraphitizationInput(k3=base.graphitization.k3, instance_id=f"rpt02-multi-graph-{suffix}", material_rows=material_rows("graphitization", f"graph-{suffix}"))
        for suffix in ("a", "b")
    )

    base_fuel = base.fuel_inputs[0]
    fuels = (
        replace(base_fuel, fuel_id="rpt02-multi-natural-gas", fuel_type=FuelType.NATURAL_GAS, fuel_label="天然气（验收演示）"),
        replace(base_fuel, fuel_id="rpt02-multi-coke-oven-gas", fuel_type=FuelType.COKE_OVEN_GAS, fuel_label="焦炉煤气（验收演示）"),
    )
    fume_base = base.fume_incineration
    fume_units = tuple(replace(fume_base, instance_id=f"rpt02-multi-fume-{suffix}") for suffix in ("a", "b"))
    fgd_base = base.fgd
    fgd_units = tuple(replace(fgd_base, instance_id=f"rpt02-multi-fgd-{suffix}") for suffix in ("a", "b"))

    electricity_base = base.electricity_details[0]
    electricity_details = (
        electricity_base,
        replace(electricity_base, detail_id="rpt02-multi-purchased-electricity-b", electricity_amount="40"),
    )
    exported_power_base = base.exported_electricity[0]
    exported_electricity = (
        exported_power_base,
        replace(exported_power_base, line_id="rpt02-multi-exported-electricity-b"),
    )

    def demo_amount(original: InputValue, value: str) -> InputValue:
        return InputValue(
            value, original.unit, original.source_type, original.source_level,
            _DEMO_SOURCE_NOTE, original.evidence_ref_ids,
        )

    purchased_heat_base = base.purchased_heat[0]
    purchased_heat = (
        purchased_heat_base,
        replace(
            purchased_heat_base,
            line_id="rpt02-multi-purchased-heat-b",
            amount=demo_amount(purchased_heat_base.amount, "500"),
        ),
    )
    exported_heat_base = base.exported_heat[0]
    exported_heat = (
        exported_heat_base,
        replace(
            exported_heat_base,
            line_id="rpt02-multi-exported-heat-b",
            amount=demo_amount(exported_heat_base.amount, "500"),
        ),
    )
    exported_electricity = (
        exported_power_base,
        replace(
            exported_power_base,
            line_id="rpt02-multi-exported-electricity-b",
            amount=demo_amount(exported_power_base.amount, "1"),
        ),
    )

    return replace(
        base,
        input_id="input.rpt02.multi-source-demo",
        fuel_inputs=fuels,
        calcination=None,
        calcinations=calcinations,
        baking=None,
        bakings=bakings,
        graphitization=None,
        graphitizations=graphitizations,
        fume_incineration=None,
        fume_incinerations=fume_units,
        fgd=None,
        fgd_units=fgd_units,
        electricity_details=electricity_details,
        exported_electricity=exported_electricity,
        purchased_heat=purchased_heat,
        exported_heat=exported_heat,
    )


def write_multi_source_acceptance_sample(
    output_dir: Path,
    evidence_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    """Create one multi-row Word sample from a separate formal frozen Record."""
    output_dir, evidence_dir = Path(output_dir), Path(evidence_dir)
    docx_path = output_dir / "GHG-RPT02_MultiSource_Record_Appendix_B.docx"
    snapshots_path = output_dir / "GHG-RPT02_MultiSource_Record_Snapshots.json"
    records_path = evidence_dir / "records.sqlite"
    evidence_path = evidence_dir / "multisource-evidence.json"
    targets = (docx_path, snapshots_path, records_path, evidence_path)
    existing = tuple(path for path in targets if path.exists())
    if existing:
        raise FileExistsError("为避免覆盖前两份样例或其他用户文件，多源样例目标已存在：" + "、".join(str(path) for path in existing))
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    try:
        with tempfile.TemporaryDirectory(prefix="rpt02-multisource-") as temporary:
            stage = Path(temporary)
            stage_docx = stage / docx_path.name
            stage_snapshots = stage / snapshots_path.name
            stage_records = stage / "records.sqlite"
            stage_evidence = stage / evidence_path.name
            catalog_path = stage / "catalog.sqlite"

            build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path)
            resolver = create_g06_parameter_resolver(SQLiteCatalogRepository(catalog_path))
            repository = SQLiteRecordRepository(stage_records)
            use_case = CarbonAccountingUseCase(CarbonMaterialCalculator(parameter_resolver=resolver), repository)
            input_value = _multi_source_canonical_input()
            record = _formal_record(use_case, input_value)
            saved = repository.get(record.record_id)
            if saved is None:
                raise RuntimeError("多源Canonical输入核算后未从独立records.sqlite读取到正式Record。")

            report = build_saved_record_report(
                repository,
                saved,
                supplementary_info={
                    "enterprise_name": saved.input_snapshot.enterprise_name,
                    "prepared_on": _SAMPLE_DATE.isoformat(),
                    "supplementary_note": "多燃料、多设施、多物料及多条购入/输出能源行的版式验收演示输入；不代表企业业务数据或企业凭证。",
                },
            )
            raw = repository.get_raw_input_snapshot(saved.record_id)
            if not isinstance(raw, dict):
                raise AssertionError("正式多源Record缺少原始输入冻结快照。")
            required_counts = {
                "fuel_inputs": len(raw.get("fuel_inputs", ())),
                "calcination_processes": len(raw.get("calcinations", ())),
                "calcination_material_rows": sum(len(item.get("material_rows", ())) for item in raw.get("calcinations", ())),
                "baking_processes": len(raw.get("bakings", ())),
                "baking_material_rows": sum(len(item.get("material_rows", ())) for item in raw.get("bakings", ())),
                "graphitization_processes": len(raw.get("graphitizations", ())),
                "graphitization_material_rows": sum(len(item.get("material_rows", ())) for item in raw.get("graphitizations", ())),
                "fume_facilities": len(raw.get("fume_incinerations", ())),
                "fgd_facilities": len(raw.get("fgd_units", ())),
                "purchased_electricity_lines": len(raw.get("electricity_details", ())),
                "exported_electricity_lines": len(raw.get("exported_electricity", ())),
                "purchased_heat_lines": len(raw.get("purchased_heat", ())),
                "exported_heat_lines": len(raw.get("exported_heat", ())),
            }
            if any(value < 2 for value in required_counts.values()):
                raise AssertionError(f"多源样例未达到每类至少两条/两个实例：{required_counts}")
            sections = {section.section_id: section for section in report.sections}
            for section_id in ("b3", "b4", "b5"):
                tables = sections[section_id].tables
                if len(tables) != 2 or any(len(table.rows) < 8 for table in tables):
                    raise AssertionError(f"{section_id}必须展示两个含多物料明细的独立过程表。")
            if len(sections["b2"].tables[0].rows) < 2:
                raise AssertionError("B.2未展示两条燃料明细。")
            for section_id, minimum_rows in (("b6", 2), ("b7", 2), ("b8", 4), ("b9", 4)):
                if len(sections[section_id].tables[0].rows) < minimum_rows:
                    raise AssertionError(f"{section_id}未展示预期的多设施/购入输出明细。")

            b1 = sections["b1"].tables[0]
            totals = frozen_totals(saved, repository.get_trace_snapshot(saved.record_id))
            if (b1.rows[-2].cells[2].value, b1.rows[-1].cells[2].value) != (totals["ES"], totals["ET"]):
                raise AssertionError("多源样例B.1总量未来自正式Record冻结ES/ET。")
            render_report_docx(report, stage_docx)
            frozen_payload = _frozen_record_payload(repository, saved)
            record_hash = sha256(json.dumps(frozen_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            snapshot_bundle = {
                "task": "GHG-RPT02_MULTI_SOURCE_ACCEPTANCE",
                "notice": "单条由Canonical输入及正式CarbonAccountingUseCase生成的多源验收演示Record；输入值及实测类别为版式验收示例，不代表实际企业业务或凭证。",
                "record_and_snapshots_sha256": record_hash,
                **frozen_payload,
            }
            stage_snapshots.write_text(json.dumps(snapshot_bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            evidence = {
                "task": "GHG-RPT02_MULTI_SOURCE_ACCEPTANCE",
                "status": "FORMAL_RECORD_FROM_APPLICATION_USE_CASE",
                "notice": snapshot_bundle["notice"],
                "record_id": saved.record_id,
                "standard_id": saved.standard_id,
                "algorithm_version": saved.algorithm_version,
                "standard_version": saved.standard_version,
                "record_status": saved.status.value,
                "input_source": "_gui_canonical_input plus uniquely identified repeats of tested fuel/process/facility/electricity/heat rows; multi-row material values reuse tests.test_uat01b_material_steam fixture.",
                "multi_source_counts": required_counts,
                "appendix_table_structure": {
                    section_id: {
                        "table_count": len(sections[section_id].tables),
                        "body_row_counts": [len(table.rows) for table in sections[section_id].tables],
                        "material_row_counts": [sum(1 for row in table.rows if row.cells[1].value not in ("", "排放量（tCO₂）")) for table in sections[section_id].tables],
                    }
                    for section_id in ("b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9")
                },
                "frozen_es_ei_et": totals,
                "report_b1_es": b1.rows[-2].cells[2].value,
                "report_b1_et": b1.rows[-1].cells[2].value,
                "report_layout_id": report.layout_id,
                "approved_template_sha256": report.template_sha256,
                "canonical_reference_data_source": DEFAULT_SOURCE_PATH.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix(),
                "record_and_snapshots_sha256": record_hash,
                "files": {
                    docx_path.name: {"sha256": sha256(stage_docx.read_bytes()).hexdigest()},
                    snapshots_path.name: {"sha256": sha256(stage_snapshots.read_bytes()).hexdigest()},
                    "records.sqlite": {"sha256": sha256(stage_records.read_bytes()).hexdigest()},
                },
                "frozen_record_snapshot_json": snapshots_path.name,
                "word_source": "build_saved_record_report(SQLiteRecordRepository.get(record_id)) then existing render_report_docx; no calculator/catalog reads occur during report generation.",
            }
            stage_evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

            for destination, content in (
                (docx_path, stage_docx.read_bytes()),
                (snapshots_path, stage_snapshots.read_bytes()),
                (records_path, stage_records.read_bytes()),
                (evidence_path, stage_evidence.read_bytes()),
            ):
                _write_new_file(destination, content)
                created.append(destination)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return docx_path, snapshots_path, records_path, evidence_path


def refresh_acceptance_samples_from_saved_records(
    output_dir: Path,
    evidence_dir: Path,
) -> tuple[Path, Path]:
    """Re-render the historical RPT02 Records from their frozen DB and bundle.

    The original R2 source identity and parity evidence are preserved. This path
    does not import workbooks, run a calculator, or rewrite the frozen bundle.
    """
    output_dir = Path(output_dir)
    evidence_dir = Path(evidence_dir)
    gui_path = output_dir / "GHG-RPT02_GUI_Canonical_Record_Appendix_B.docx"
    excel_path = output_dir / "GHG-RPT02_Excel_R2_Record_Appendix_B.docx"
    records_path = evidence_dir / "records.sqlite"
    manifest_path = evidence_dir / "acceptance-evidence.json"
    bundle_path = output_dir / "records-and-snapshots.json"
    required = (gui_path, excel_path, records_path, manifest_path, bundle_path)
    missing = tuple(path for path in required if not path.is_file())
    if missing:
        raise FileNotFoundError("saved-record刷新缺少既有验收文件：" + "、".join(str(path) for path in missing))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_records = manifest.get("records")
    if not isinstance(manifest_records, list) or len(manifest_records) != 2:
        raise ValueError("existing acceptance manifest must contain exactly two formal sample Records")
    record_by_origin = {item.get("origin"): item for item in manifest_records if isinstance(item, dict)}
    expected_origins = ("GUI_CANONICAL_INPUT", "EXCEL_R2_PREVIEW_TO_FORMAL_USE_CASE")
    if set(record_by_origin) != set(expected_origins):
        raise ValueError("existing acceptance manifest does not identify both expected sample Records")

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle_records = bundle.get("records")
    if bundle.get("task") != "GHG-RPT02" or not isinstance(bundle_records, list):
        raise ValueError("existing frozen Record bundle is not a GHG-RPT02 bundle")
    bundle_by_origin = {item.get("origin"): item for item in bundle_records if isinstance(item, dict)}
    if set(bundle_by_origin) != set(expected_origins):
        raise ValueError("existing frozen Record bundle does not preserve both historical sample identities")

    repository = SQLiteRecordRepository(records_path)
    saved_by_origin = {}
    for origin in expected_origins:
        manifest_record = record_by_origin[origin]
        frozen_item = bundle_by_origin[origin]
        saved = repository.get(str(manifest_record["record_id"]))
        if saved is None:
            raise RuntimeError(f"records.sqlite缺少既有样例Record：{origin}")
        bundle_record = frozen_item.get("record")
        bundle_snapshots = frozen_item.get("snapshots")
        if not isinstance(bundle_record, dict) or not isinstance(bundle_snapshots, dict):
            raise ValueError(f"冻结bundle缺少Record或快照内容：{origin}")
        frozen_payload = {"record": bundle_record, "snapshots": bundle_snapshots}
        stored_hash = str(frozen_item.get("record_and_snapshots_sha256", ""))
        frozen_hash = sha256(
            json.dumps(frozen_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if saved.record_id != bundle_record.get("record_id"):
            raise AssertionError(f"冻结bundle与records.sqlite的Record身份不一致：{origin}")
        if stored_hash != frozen_hash or _frozen_record_payload(repository, saved) != frozen_payload:
            raise AssertionError(f"冻结bundle与records.sqlite的Record/快照内容不一致：{origin}")
        saved_by_origin[origin] = saved

    prepared_on = str(manifest.get("generated_at", _SAMPLE_AT.isoformat()))[:10]
    notes = {
        "GUI_CANONICAL_INPUT": "验收演示输入；Canonical表单数据经正式核算用例写入不可变Record；不代表真实企业核算或企业凭证。",
        "EXCEL_R2_PREVIEW_TO_FORMAL_USE_CASE": "历史R2验收演示输入；重渲染读取冻结Record，不重新导入工作簿或计算；活动数据不是企业凭证。",
    }
    descriptions = {origin: record_by_origin[origin].get("input_description", "") for origin in expected_origins}
    refreshed_summaries = []
    with tempfile.TemporaryDirectory(prefix="rpt02-saved-docs-", dir=output_dir) as docs_temp, tempfile.TemporaryDirectory(prefix="rpt02-saved-evidence-", dir=evidence_dir) as evidence_temp:
        docs_stage = Path(docs_temp)
        evidence_stage = Path(evidence_temp)
        for origin, destination in ((expected_origins[0], gui_path), (expected_origins[1], excel_path)):
            saved = saved_by_origin[origin]
            report = build_saved_record_report(
                repository,
                saved,
                supplementary_info={
                    "enterprise_name": saved.input_snapshot.enterprise_name,
                    "prepared_on": prepared_on,
                    "supplementary_note": notes[origin],
                },
            )
            b1 = next(section for section in report.sections if section.section_id == "b1").tables[0]
            totals = frozen_totals(saved, repository.get_trace_snapshot(saved.record_id))
            if (b1.rows[-2].cells[2].value, b1.rows[-1].cells[2].value) != (totals["ES"], totals["ET"]):
                raise AssertionError("saved-record渲染未保留冻结的ES和ET。")
            staged_docx = docs_stage / destination.name
            render_report_docx(report, staged_docx)
            refreshed_summaries.append(_record_evidence(
                repository, saved, report, origin=origin, input_description=descriptions[origin],
            ))

        refreshed_manifest = dict(manifest)
        refreshed_manifest["records"] = refreshed_summaries
        refreshed_manifest["historical_refresh_note"] = (
            "Word仅从已冻结RPT02 Record及快照重渲染；历史EXCEL_R2身份与既有同输入对照证据保留，本次未重新导入或计算。"
        )
        refreshed_files = dict(manifest.get("files", {}))
        refreshed_files[gui_path.name] = {"sha256": sha256((docs_stage / gui_path.name).read_bytes()).hexdigest()}
        refreshed_files[excel_path.name] = {"sha256": sha256((docs_stage / excel_path.name).read_bytes()).hexdigest()}
        refreshed_files["records.sqlite"] = {"sha256": sha256(records_path.read_bytes()).hexdigest()}
        refreshed_files[bundle_path.name] = {"sha256": sha256(bundle_path.read_bytes()).hexdigest()}
        refreshed_manifest["files"] = refreshed_files
        staged_manifest = evidence_stage / manifest_path.name
        staged_manifest.write_text(json.dumps(refreshed_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

        # Keep the frozen Record bundle and PDF samples byte-for-byte unchanged.
        for destination in (gui_path, excel_path):
            (docs_stage / destination.name).replace(destination)
        staged_manifest.replace(manifest_path)
    return gui_path, excel_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repository_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repository_root / "docs" / "rpt02" / "samples",
        help="directory for the two editable DOCX acceptance samples",
    )
    parser.add_argument("--evidence-dir", type=Path, default=repository_root / "build" / "rpt02", help="独立Record数据库与验收证明JSON目录")
    parser.add_argument("--refresh-from-saved-records", action="store_true", help="只从既有正式Record和冻结快照重渲染样例，不重算样例Record")
    parser.add_argument("--multi-source-sample", action="store_true", help="生成独立的真实多源Canonical Record及Appendix B Word样例")
    parser.add_argument("--multi-evidence-dir", type=Path, default=repository_root / "build" / "rpt02-multi", help="多源正式Record与验收证明目录")
    args = parser.parse_args()
    if args.multi_source_sample:
        for path in write_multi_source_acceptance_sample(args.output_dir, args.multi_evidence_dir):
            print(path.resolve())
        return
    if args.refresh_from_saved_records:
        for path in refresh_acceptance_samples_from_saved_records(args.output_dir, args.evidence_dir):
            print(path.resolve())
        print((args.output_dir / "records-and-snapshots.json").resolve())
        print((args.evidence_dir / "records.sqlite").resolve())
        print((args.evidence_dir / "acceptance-evidence.json").resolve())
        return
    for path in write_acceptance_samples(args.output_dir, args.evidence_dir):
        print(path.resolve())
    print((args.output_dir / "records-and-snapshots.json").resolve())
    print((args.evidence_dir / "records.sqlite").resolve())
    print((args.evidence_dir / "acceptance-evidence.json").resolve())


if __name__ == "__main__":
    main()