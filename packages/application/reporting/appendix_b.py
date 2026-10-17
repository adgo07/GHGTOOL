"""GB/T 32151.34 approved Appendix B layout and frozen-record field mapping.

Only this standard is registered. Layout contains labels/merges, never formulas.
"""
from __future__ import annotations

import json
import re
from importlib.resources import files
from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Mapping

from packages.core.decimal_policy import DecimalPolicy
from packages.core.units import UnitService
from packages.application.source_display import format_source_reference
from packages.standards.carbon_material import (
    STANDARD_ID, SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING,
    SOURCE_GRAPHITIZATION, SOURCE_FUME, SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_EXPORTED_ELECTRICITY, SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_HEAT,
)
from .carbon_material_model import (
    ReportCell, ReportRow, ReportTable, ReportSection, _mapping, _entries, _text,
    _enum, _FUEL_NAMES, _SOURCE_NAMES, _parameter_cell, _activity_source,
    _step_for_instance, _step_result, _trace_steps, _display_amount, frozen_totals, _snapshot_mapping, _snapshot_audit_detail,
)

_LAYOUT = json.loads(files(__package__).joinpath('appendix_b_layout.json').read_text(encoding='utf-8'))
APPROVED_TEMPLATE_SHA256 = _LAYOUT['approved_sha256']
LAYOUT_ID = _LAYOUT['layout_id']
# Display conversions only; the declared precision exceeds every frozen value's digits.

def _units(value, source, target):
    text = _text(value)
    if not text:
        return ''
    digits = len(Decimal(text).as_tuple().digits)
    return format(UnitService(DecimalPolicy(precision=max(50, digits + 16), rounding=ROUND_HALF_UP)).convert(text, source, target), 'f')


def _display_number(value):
    text=_text(value)
    try:
        number=Decimal(text)
        if not number.is_finite():return text
    except Exception:
        return text
    displayed=_display_amount(number)
    if number != 0 and Decimal(displayed)==0:
        with localcontext() as context:
            context.rounding=ROUND_HALF_UP
            return format(number,'.2E')
    return displayed


def _display_cell(value, *, source=None, detail=None, unit=None):
    exact=_text(value)
    displayed=_display_number(exact)
    explanation=detail
    try:
        if Decimal(displayed)!=Decimal(exact):
            explanation='；'.join(part for part in (detail,f"展示前完整值：{exact} {unit or ''}".strip()) if part)
    except Exception:
        pass
    return ReportCell(displayed,source=source,source_detail=explanation)


def _value(value, *, unit=None, percent=False):
    raw = _mapping(value)
    text = _text(value)
    if not text:
        return ReportCell('未填写')
    from_unit = _text(raw.get('unit')) or ('ratio' if percent else unit)
    if percent:
        text = _units(text, from_unit, 'percent')
    elif unit and from_unit and unit != from_unit:
        text = _units(text, from_unit, unit)
    detail=_activity_source(value)
    source = _short_source(value,None,detail) if detail else None
    if source in {"手工录入", "用户录入", "用户提供值", "填写值"}:
        source = None
    return _display_cell(text,source=source,detail=detail,unit=unit)


_SHORT_SOURCE_NAMES = {
    "STANDARD_DEFAULT":"缺省值","STANDARD_SPECIFIED":"标准规定值","STANDARD_REQUIRED":"标准规定值",
    "MEASURED":"实测值","ENTERPRISE_MEASURED":"实测值","USER_DEFINED":"填写值","USER_PROVIDED":"填写值","MANUAL_OVERRIDE":"填写值",
    "CALCULATED":"计算值","DERIVED":"计算值","INTERPOLATED":"插值计算",
    "GOVERNMENT_PUBLISHED":"官方发布值","OFFICIAL_PUBLISHED":"官方发布值","SCIENTIFIC_REFERENCE":"文献值",
    "SYSTEM_CONSTANT":"系统常数","HISTORICAL":"历史值",
    "USER_SELECTED_LIBRARY_VALUE":"库选值","SYSTEM_RECOMMENDED":"系统推荐值",
    "CHEMICAL_CALCULATION":"化学计算","METER":"计量器具","PRODUCTION_LEDGER":"生产台账",
    "ENERGY_BILL":"能源账单","TEST_REPORT":"检测报告","STATEMENT":"结算单",
    "MANUAL":"手工录入","OTHER":"其他来源",
}


def _short_source(raw,snapshot,detail):
    snapshot_data = _mapping(snapshot)
    raw_data = _mapping(raw)
    source_type = (
        snapshot_data.get("source_type")
        or raw_data.get("source_kind")
        or raw_data.get("source_type")
        or snapshot_data.get("selection_method")
    )
    source_name = _SHORT_SOURCE_NAMES.get(source_type) or "来源未记录"
    source_location = snapshot_data.get("source_location") or raw_data.get("source_location")
    if not source_location and raw_data.get("source_reference"):
        source_location = raw_data.get("source_reference")
    if not source_location and detail:
        match = re.search(r"(?:来源定位|来源参考)：([^；]+)", detail)
        source_location = match.group(1) if match else None
    return format_source_reference(source_location, source_name)


def _parameter(value, snapshots, key, *, percent=False):
    cell = _parameter_cell(value, snapshots, key)
    if not cell.value:
        if value is not None and not isinstance(value, Mapping) and _text(value):
            cell = ReportCell(_text(value), source_detail='历史来源未记录')
        else:
            return ReportCell('历史未记录' if value is None else '未填写')
    text = _units(cell.value, cell.unit or 'ratio', 'percent') if percent else cell.value
    detail = cell.source_detail or _activity_source(value) or '来源未记录'
    return _display_cell(text,source=_short_source(value,snapshots.get(key),detail),detail=detail,unit="%" if percent else cell.unit)


def _source_cell(cell):
    return ReportCell(cell.source or ('—' if cell.value == '不适用' else '来源未记录'),source_detail=cell.source_detail)


def _number_cell(cell):
    return ReportCell(cell.value,source_detail=cell.source_detail)


def _status(raw, source):
    state = next((item for item in _entries(raw, 'source_states') if item.get('source_id') == source), None)
    if state:
        return {'NOT_INVOLVED': '未启用', 'UNCONFIRMED': '未确认'}.get(state.get('status'), '历史未记录此项明细')
    return '历史未记录此项明细'


def _table(key, rows, *, source=None, raw=None, suffix='', merges=()):
    layout = _LAYOUT['tables'][key]
    values = tuple(ReportRow(tuple(c if isinstance(c, ReportCell) else ReportCell(str(c)) for c in row)) for row in rows)
    if not values:
        values = (ReportRow(tuple(ReportCell(_status(raw, source) if i == 0 else '—') for i in range(len(layout['headers'][0])))),)
        merges = ((0, 0, 0, len(layout['headers'][0]) - 1),)
    return ReportTable(
        table_id=key + suffix, title=layout['title'], columns=tuple(layout['headers'][0]),
        rows=values, landscape=key in ('b2', 'b6', 'b7', 'b9'),
        header_rows=tuple(ReportRow(tuple(ReportCell(c) for c in row)) for row in layout['headers']),
        header_merges=tuple(tuple(m) for m in layout['header_merges']),
        body_merges=tuple(merges), footnotes=tuple(layout['footnotes']),
        column_weights=tuple(layout['column_weights']),
    )


def _signed(step, exported=False):
    result = _step_result(step)
    if not result:
        return '历史未记录'
    return format(Decimal(result).copy_negate(), '.2f') if exported else result


def _variables(step):
    return {v.get('name'): v for v in _mapping(step).get('input_variables', ()) if isinstance(v, Mapping)}


def _frozen_step(record, trace, source, iid, *, single_instance=False):
    step = _step_for_instance(trace, source, iid)
    if step is not None and step.get("intermediate_result") is not None:
        return step
    prefix = {
        SOURCE_CALCINATION: "CAR-FLD-P01-RESULT", SOURCE_BAKING: "CAR-FLD-P02-RESULT",
        SOURCE_GRAPHITIZATION: "CAR-FLD-P03-RESULT", SOURCE_FUME: "CAR-FLD-P04A-RESULT",
        SOURCE_FGD: "CAR-FLD-P04B-RESULT", SOURCE_PURCHASED_ELECTRICITY: "CAR-FLD-PWR-PURCHASED-RESULT",
        SOURCE_EXPORTED_ELECTRICITY: "CAR-FLD-POWER-EXPORTED-RESULT", SOURCE_PURCHASED_HEAT: "CAR-FLD-HEAT-PURCHASED-RESULT",
        SOURCE_EXPORTED_HEAT: "CAR-FLD-HEAT-EXPORTED-RESULT",
    }.get(source)
    lines = [line for line in record.calculation_result.lines if line.emission_source_id == source]
    line = next((line for line in lines if line.line_id == f"{prefix}.{iid}"), None)
    if line is None and single_instance:
        line = next((line for line in lines if line.line_id == prefix), None)
    if line is not None:
        return {**_mapping(step), "intermediate_result": str(line.amount)}
    return step


def _energy_parameter(record, item, iid, explicit_key, unit, variable, step, *, ambiguous_detail_ids=(),source_types=None):
    # detail IDs can coincide between purchased power and heat. Match quantity kind too.
    candidates = [snap for snap in record.parameter_snapshots
                  if snap.detail_id in (iid, explicit_key) and snap.unit_used.replace("₂", "2") == unit]
    explicit = [snap for snap in candidates if snap.detail_id == explicit_key]
    if explicit:
        candidates = explicit
    frozen_value = _mapping(_variables(step).get(variable)).get("value")
    ambiguous_single = len(candidates) == 1 and candidates[0].detail_id in ambiguous_detail_ids
    had_candidates = bool(candidates)
    if frozen_value is not None:
        candidates = [snap for snap in candidates if Decimal(str(snap.value_used)) == Decimal(str(frozen_value))]
    if had_candidates and not candidates:
        return ReportCell(_text(frozen_value), source="历史来源快照与冻结采用值不一致")
    if ambiguous_single:
        return ReportCell(_text(frozen_value) or "历史未记录", source="历史来源快照无法唯一关联")
    unique = {tuple(sorted((key, str(value)) for key, value in _snapshot_mapping(snap).items())): snap for snap in candidates}
    if len(unique) == 1:
        snapshot = _snapshot_mapping(next(iter(unique.values())))
        snapshot["source_type"] = _mapping(source_types).get(next(iter(unique.values())).detail_id+"|"+next(iter(unique.values())).unit_used)
        detail = _snapshot_audit_detail(snapshot) or "来源未记录"
        return _display_cell(snapshot["value_used"],source=_short_source(item.get("factor"),snapshot,detail),detail=detail,unit=unit)
    if len(unique) > 1:
        return ReportCell(_text(frozen_value) or "历史未记录", source="历史来源快照无法唯一关联")
    cell = _parameter(item.get("factor"), {}, explicit_key)
    if cell.value in ("历史未记录", "未填写") and frozen_value is not None:
        return ReportCell(_text(frozen_value), source="历史来源未记录")
    return cell


def _source_amount(record, trace, raw, source, subtotal=None):
    frozen = _mapping(trace.get('source_subtotals'))
    if subtotal in frozen:
        text = _display_amount(frozen[subtotal])
    else:
        # ER/ED already appear as frozen subtotals in the gas-control trace.
        name = {SOURCE_FUME: 'ER subtotal', SOURCE_FGD: 'ED subtotal'}.get(source)
        gas = next((s for s in _trace_steps(trace) if s.get('formula_id') == 'CAR-FML-GAS-CONTROL-TOTAL-001'), None)
        variable = _variables(gas).get(name)
        lines = [line for line in record.calculation_result.lines if line.emission_source_id == source]
        value = variable.get('value') if variable else (lines[0].amount if len(lines) == 1 else None)
        text = _display_amount(value)
    if _status(raw, source) == '未启用':
        return '未启用' + (f'（{text}）' if text else '')
    return text or '历史未记录'


# Template rows specify groups and roles; each role can expand to many real materials.
_PROCESS_ROWS = {
    'b3': (
        ('进入煅烧炉的碳', 'calcination_feed', 'fixed_carbon_percent', 'gc', 'wfc'),
        ('进入煅烧炉的挥发分', 'calcination_feed', 'volatile_matter_percent', 'gc', 'wvar'),
        ('输出煅烧炉的碳', 'calcined_product', 'fixed_carbon_percent', 'cc', 'wfc_c'),
        ('输出煅烧炉的碳', 'underburn_recovered', 'fixed_carbon_percent', 'ucc', 'wfc_c'),
        ('输出煅烧炉的碳', 'carbon_dust', 'fixed_carbon_percent', 'du', 'wfc_c'),
        ('输出煅烧炉的挥发分', 'calcined_product', 'volatile_matter_percent', 'cc', 'wvar_c'),
    ),
    'b4': (
        ('进入焙烧\n(炭化)的碳a', 'baking_filler', 'fixed_carbon_percent', 'bpm', 'bpmfc'),
        ('进入焙烧\n(炭化)的碳a', 'green_baking_product', 'fixed_carbon_percent', 'bg', 'bgfc'),
        ('进入焙烧\n(炭化)的挥发分', 'baking_filler', 'volatile_matter_percent', 'bpm', 'bpmvar'),
        ('进入焙烧\n(炭化)的挥发分', 'green_baking_product', 'volatile_matter_percent', 'bg', 'bgvar'),
        ('输出焙烧\n(炭化)炉的碳', 'baking_byproduct', 'fixed_carbon_percent', None, None),
        ('输出焙烧\n(炭化)炉的碳', 'baked_product', 'fixed_carbon_percent', 'bp', 'bpfc'),
    ),
    'b5': (
        ('进入石墨化\n炉的碳', 'graphitization_packing', 'fixed_carbon_percent', 'gpm', 'gpmfc'),
        ('进入石墨化\n炉的碳', 'green_graphitization_product', 'fixed_carbon_percent', 'gta', 'gtafc'),
        ('进入石墨化炉\n的挥发分', 'graphitization_packing', 'volatile_matter_percent', 'gpm', 'gpmvar'),
        ('输出石墨化\n炉的碳', 'graphitization_byproduct', 'fixed_carbon_percent', None, None),
        ('输出石墨化\n炉的碳', 'graphitized_product', 'fixed_carbon_percent', 'gp', 'gpfc'),
    ),
}
_ROLE_NAMES = {
    'calcination_feed':'待煅烧原料', 'calcined_product':'煅后料', 'underburn_recovered':'欠烧煅料', 'carbon_dust':'炭粉尘',
    'baking_filler':'填充料', 'green_baking_product':'待焙烧(炭化)品', 'baking_byproduct':'粉尘、碎屑、副产品等', 'baked_product':'焙烧(炭化)品',
    'graphitization_packing':'保温料和电阻料', 'green_graphitization_product':'待石墨化品', 'graphitization_byproduct':'粉尘、碎屑、残块(渣)、副产品等', 'graphitized_product':'石墨化产品',
}


def _process_table(key, process, step, ordinal, source, raw):
    materials = _entries(process, 'material_rows')
    rows, merges = [], []
    variables = _variables(step)
    adopted = _mapping(_mapping(step).get("calculation_provenance"))
    method_notes = []
    for group, role, component, mass_key, ratio_key in _PROCESS_ROWS[key]:
        matching = [m for m in materials if m.get('role') == role]
        if matching:
            for material in matching:
                source_key = 'fixed_carbon_source' if component == 'fixed_carbon_percent' else 'volatile_matter_source'
                prefix = f"material.{material.get('line_id')}.adopted."
                mass = adopted.get(prefix + "mass_t", material.get("mass_t"))
                composition = adopted.get(prefix + component, material.get(component))
                source_name = _enum(material.get(source_key), _SOURCE_NAMES) or '来源未记录'
                if material.get("conversion_method") == "DRY_TO_RECEIVED_MOISTURE":
                    source_name = "收到基换算" if material.get(source_key) == "CHEMICAL_CALCULATION" else source_name
                    note = f"{material.get('name') or _ROLE_NAMES[role]}：原质量{material.get('mass_t')} t，质量基准{ {'DRY':'干基','RECEIVED':'收到基'}.get(material.get('mass_basis'),'未记录')}；原含量{material.get(component)} {material.get('fixed_carbon_unit' if component == 'fixed_carbon_percent' else 'volatile_matter_unit', '%')}，含量基准{ {'DRY':'干基','RECEIVED':'收到基'}.get(material.get('composition_basis'),'未记录')}；收到基水分{material.get('moisture_received_percent')}%，按水分质量守恒归一。"
                    if note not in method_notes: method_notes.append(note)
                rows.append((group, _ROLE_NAMES[role], material.get('name') or _ROLE_NAMES[role], _value(mass), _value(composition), source_name))
        elif materials:
            rows.append((group, _ROLE_NAMES[role], '未列示此物流', '—', '—', '—'))
        else:
            # Legacy scalar inputs have frozen aggregated data, not individual material identities.
            mass = process.get(mass_key) if mass_key else None
            ratio = process.get(ratio_key) if ratio_key else None
            if mass is None:
                mass = variables.get(mass_key)
            if ratio is None:
                ratio = variables.get(ratio_key)
            rows.append((group, _ROLE_NAMES[role], '历史未记录实际名称', _value(mass) if mass is not None else '历史未记录', _number_cell(_value(ratio, percent=True)) if ratio is not None else '历史未记录', _activity_source(ratio) or _enum(_mapping(ratio).get('source_kind'), _SOURCE_NAMES) or '来源未记录'))
    # Merge adjacent group labels without discarding distinct material names.
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i][0] != rows[start][0]:
            if i - start > 1:
                merges.append((start, 0, i - 1, 0))
            start = i
    last = len(rows)
    rows.append(('排放量（tCO₂）', '', '', _step_result(step) or '历史未记录', '', ''))
    merges.extend(((last, 0, last, 2), (last, 3, last, 5)))
    return replace(_table(key, rows, source=source, raw=raw, suffix=f'-{ordinal}', merges=merges),
                   context_label=process.get('instance_name') or f'过程单元{ordinal}',
                   footnotes=tuple(_table(key, (), source=source, raw=raw).footnotes) + tuple(method_notes))


def build_appendix_b_sections(record, raw, trace, snapshots, *, enterprise_name=None):
    if record.standard_id != STANDARD_ID:
        raise ValueError('尚未登记该标准的正式报告表式')
    totals = frozen_totals(record, trace)
    names = (
        ('化石燃料燃烧产生的 CO₂   排放', SOURCE_FUEL, 'fuel'),
        ('原料煅烧产生的 CO₂   排放', SOURCE_CALCINATION, 'calcination'),
        ('炭素制品焙烧(炭化)  产生的 CO₂   排放', SOURCE_BAKING, 'baking'),
        ('炭素制品石墨化产生的 CO₂   排放', SOURCE_GRAPHITIZATION, 'graphitization'),
        ('烟气焚烧治理产生的 CO₂   排放', SOURCE_FUME, None),
        ('烟气脱硫净化产生的 CO₂   排放', SOURCE_FGD, None),
        ('购入电力对应的产生的 CO₂   排放', SOURCE_PURCHASED_ELECTRICITY, 'purchased_electricity'),
        ('购入热力对应的产生的 CO₂   排放', SOURCE_PURCHASED_HEAT, 'purchased_heat'),
        ('输出电力对应的产生的 CO₂   排放', SOURCE_EXPORTED_ELECTRICITY, 'exported_electricity'),
        ('输出热力对应的产生的 CO₂   排放', SOURCE_EXPORTED_HEAT, 'exported_heat'),
    )
    rows = [(label, '', _source_amount(record, trace, raw, source, subtotal)) for label, source, subtotal in names]
    rows.extend((('… …', '', '—'), ('报告主体温室气体排放总量', '不包括购入和输出的电力、热力所产生的 CO₂   排放量', totals['ES'] or '历史未记录'), ('', '包括购入和输出的电力、热力所产生的 CO₂   排放量', totals['ET'] or '历史未记录')))
    merges = [(i, 0, i, 1) for i in range(11)] + [(11, 0, 12, 0)]
    sections = [ReportSection('b1', 'B.1 温室气体排放量汇总', (_table('b1', rows, merges=merges),), ('输出电力、热力在总量中扣减。未按1%脚注省略任何已冻结结果；其他行业活动须另按适用标准核算。',))]

    from packages.standards.carbon_material import verify_record_aggregation
    if trace.get("trace_schema_version")==1:
        calculation_snapshot={"lines":[{"line_id":line.line_id,"emission_source_id":line.emission_source_id,"amount":str(line.amount),"unit":line.unit} for line in record.calculation_result.lines],
                              "total_amount":str(record.calculation_result.total_amount)}
        errors=verify_record_aggregation(trace,calculation_snapshot)
        audit_note="历史汇总核对存在不一致，请在计算依据中查看冻结证据。" if errors else None
    else:
        audit_note="历史记录未保存完整汇总链；本报告未使用当前参数补算。"
    if audit_note:
        sections[0]=replace(sections[0],notes=(*sections[0].notes,audit_note))

    b1_table = sections[0].tables[0]
    subject = enterprise_name or record.input_snapshot.enterprise_name or '报告主体'
    year = record.input_snapshot.period.start.year
    b1_title = b1_table.title.replace('报告主体                 年', f'{subject} {year}年')
    sections[0] = replace(sections[0], tables=(replace(b1_table, title=b1_title),))

    rows = []
    fuel_notes = []
    for item in _entries(raw, 'fuel_inputs'):
        iid = _text(item.get('fuel_id'))
        prefix = f'CAR-FLD-F01-{iid}'
        fuel_name = item.get('fuel_label') or _enum(item.get('fuel_type'), _FUEL_NAMES) or '历史未记录燃料名称'
        carbon = _parameter(item.get('carbon_content'), snapshots, prefix+'-CARBON')
        carbon_unit = _parameter_cell(item.get('carbon_content'), snapshots, prefix+'-CARBON').unit
        lhv = _parameter(item.get('lower_heating_value'), snapshots, prefix+'-LHV') if item.get('lower_heating_value') is not None or prefix+'-LHV' in snapshots else ReportCell('不适用')
        oxidation = _parameter(item.get('oxidation_rate'), snapshots, prefix+'-FOX', percent=True)
        path = item.get('path')
        unit = {'MASS':'t', 'VOLUME':'ten_thousand_Nm3', 'HEAT':'GJ'}.get(path)
        activity = _value(item.get('activity'), unit=unit)
        if path == 'HEAT':
            activity = replace(activity, unit='GJ（热量计量）')
            note_label = fuel_name if fuel_name != '历史未记录燃料名称' else '该热量计量燃料'
            note = f'{note_label}按冻结的热量活动数据列示，不反推质量或体积。'
            if note not in fuel_notes:
                fuel_notes.append(note)
        if carbon_unit == 'tC/GJ':
            # A derived fuel carbon content was never frozen; do not recompute LHV × carbon.
            frozen = _mapping(_mapping(trace.get('derived_display_evidence')).get(prefix))
            direct_carbon = _display_cell(frozen.get('value'),source='计算值',unit=frozen.get('unit')) if frozen.get('value') is not None else ReportCell('未记录（采用单位热值含碳量）')
            unit_carbon = carbon
        elif carbon_unit in ('tC/t', 'tC/10^4Nm3', 'tC/10⁴Nm³'):
            direct_carbon = carbon
            unit_carbon = ReportCell('不适用')
        else:
            direct_carbon, unit_carbon = carbon, ReportCell('历史未记录')
        step = _step_for_instance(trace, SOURCE_FUEL, iid)
        result = _step_result(step)
        if not result:
            result = next((_display_amount(line.amount) for line in record.calculation_result.lines if line.line_id == f'{SOURCE_FUEL}.{iid}'), '历史未记录')
        rows.append((fuel_name, activity, {'MASS':'t','VOLUME':'10⁴Nm³','HEAT':'GJ'}.get(path,'历史未记录'), _number_cell(direct_carbon), _source_cell(direct_carbon), _number_cell(lhv), _source_cell(lhv), unit_carbon, _number_cell(oxidation), _source_cell(oxidation), result))
    if not rows:
        for i,line in enumerate(record.calculation_result.lines,1):
            if line.emission_source_id == SOURCE_FUEL:
                rows.append((f'历史燃料结果{i}', *('历史未记录',)*9, _display_amount(line.amount)))
    sections.append(ReportSection('b2', 'B.2 化石燃料活动数据和排放因子', (_table('b2', rows, source=SOURCE_FUEL, raw=raw),), tuple(fuel_notes)))

    for key, title, collection, legacy, source in (
        ('b3','B.3 原料煅烧','calcinations','calcination',SOURCE_CALCINATION),
        ('b4','B.4 焙烧/炭化','bakings','baking',SOURCE_BAKING),
        ('b5','B.5 石墨化','graphitizations','graphitization',SOURCE_GRAPHITIZATION),
    ):
        process_entries = _entries(raw,collection,legacy)
        tables = tuple(_process_table(key, process, _frozen_step(record,trace,source,process.get('instance_id'),single_instance=len(process_entries)==1), i, source, raw) for i, process in enumerate(process_entries,1))
        if not tables:
            tables = tuple(_process_table(key, {}, {'intermediate_result': str(line.amount)}, i, source, raw) for i,line in enumerate((line for line in record.calculation_result.lines if line.emission_source_id == source),1))
        section_notes = []
        if tables:
            if any(_entries(process, 'material_rows') for process in process_entries):
                section_notes.append('物料质量与含量按本软件冻结的收到基口径列示。')
            section_notes.append('排放量按冻结过程结果列示，不向单件物料分摊。')
            missing_details = [
                _text(process.get('instance_name')) or f'过程单元{index}'
                for index, process in enumerate(process_entries, 1)
                if not _entries(process, 'material_rows')
            ]
            if not process_entries:
                missing_details = [table.context_label or '历史过程' for table in tables]
            if missing_details:
                labels = '、'.join(dict.fromkeys(missing_details))
                section_notes.append(f'{labels}未保存逐物料明细；表内缺失字段标记为“历史未记录”。')
        sections.append(ReportSection(key,title,tables or (_table(key,[],source=source,raw=raw),),tuple(section_notes)))

    rows = []
    for i, item in enumerate(_entries(raw,'fume_incinerations','fume_incineration'),1):
        iid = _text(item.get('instance_id'))
        rows.append((_value(item.get('q')), _value(item.get('qvar')), _value(item.get('hm')), _parameter(item.get('fch'),snapshots,f'CAR-FLD-P04A-{iid}-FCH'), _value(item.get('fox'),percent=True), _value(item.get('duration')), _signed(_frozen_step(record,trace,SOURCE_FUME,iid,single_instance=len(_entries(raw,'fume_incinerations','fume_incineration'))==1))))
    if not rows:
        rows = [(*('历史未记录',)*6, _display_amount(line.amount)) for line in record.calculation_result.lines if line.emission_source_id == SOURCE_FUME]
    sections.append(ReportSection('b6','B.6 烟气焚烧治理',(_table('b6',rows,source=SOURCE_FUME,raw=raw),)))

    rows, merges = [], []
    for i, unit in enumerate(_entries(raw,'fgd_units','fgd'),1):
        iid = _text(unit.get('instance_id'))
        start = len(rows)
        components = _entries(unit,'components')
        for index, comp in enumerate(components):
            prefix = f'CAR-FLD-P04B-{iid}-{index}'
            rows.append((unit.get('reagent_name') or '历史未记录', _value(comp.get('amount'),unit='t'), comp.get('carbonate_type') or '历史未记录', _parameter(comp.get('carbonate_fraction'),snapshots,prefix+'-I',percent=True), _parameter(comp.get('emission_factor'),snapshots,prefix+'-EF1'), _parameter(comp.get('conversion_rate'),snapshots,prefix+'-TR',percent=True), _signed(_frozen_step(record,trace,SOURCE_FGD,iid,single_instance=len(_entries(raw,'fgd_units','fgd'))==1)) if index==0 else ''))
        end = len(rows)-1
        if end > start:
            merges.extend(((start,0,end,0),(start,6,end,6)))
            if all(rows[j][1] == rows[start][1] for j in range(start,end+1)):
                merges.append((start,1,end,1))
    if not rows:
        rows = [('历史未记录', *('历史未记录',)*5, _display_amount(line.amount)) for line in (line for line in record.calculation_result.lines if line.emission_source_id == SOURCE_FGD)]
    b7_notes = ('排放量列列示各脱硫剂组的冻结合计；历史记录未保存逐组分排放量时不重新计算。',) if any(merge[1] == 6 for merge in merges) else ()
    sections.append(ReportSection('b7','B.7 烟气脱硫净化',(_table('b7',rows,source=SOURCE_FGD,raw=raw,merges=merges),),b7_notes))

    rows = []
    purchased_ids = {_text(item.get('detail_id')) for item in _entries(raw, 'electricity_details')
                     if not (item.get('acquisition_mode') == 'SELF_CONSUMED' and item.get('attribute') == 'FOSSIL')}
    exported_ids = {_text(item.get('line_id')) for item in _entries(raw, 'exported_electricity')}
    exported_keys = {f'CAR-FLD-POWER-EXPORTED-EF.{iid}' for iid in exported_ids}
    for collection,direction,source in (('electricity_details','购入',SOURCE_PURCHASED_ELECTRICITY),('exported_electricity','输出',SOURCE_EXPORTED_ELECTRICITY)):
        for item in _entries(raw,collection):
            iid = _text(item.get('detail_id') or item.get('line_id'))
            step = _frozen_step(record,trace,source,iid)
            if item.get('acquisition_mode') == 'SELF_CONSUMED' and item.get('attribute') == 'FOSSIL':
                continue # already counted in fuel; never claim it was purchased electricity
            amount = item.get('electricity_amount',item.get('amount'))
            unit = _text(_mapping(amount).get('unit')) or _text(item.get('electricity_unit') or item.get('unit')) or 'MWh'
            quantity = ReportCell(_units(_text(amount),unit,'MWh') or '未填写',source=_activity_source(amount))
            factor_key = f'CAR-FLD-POWER-EXPORTED-EF.{iid}' if direction == '输出' else iid
            ambiguous_ids = purchased_ids & (exported_ids | exported_keys)
            if direction == '购入':
                export_key = f'CAR-FLD-POWER-EXPORTED-EF.{iid}'
                if export_key not in purchased_ids and any(s.detail_id == export_key for s in record.parameter_snapshots):
                    ambiguous_ids = ambiguous_ids - {iid}
            factor = _energy_parameter(record,item,iid,factor_key,'tCO2/MWh','EF2',step,
                                       ambiguous_detail_ids=ambiguous_ids,source_types=_mapping(trace.get("parameter_source_types")))
            rows.append((direction, ('不适用' if direction=='输出' else _enum(item.get('attribute'),{'ORDINARY':'常规电力','NONFOSSIL':'非化石电力','FOSSIL':'化石能源电力'}) or '历史未记录'), quantity, factor, _signed(step,direction=='输出')))
    for collection,direction,source in (('electricity_details','购入',SOURCE_PURCHASED_ELECTRICITY),('exported_electricity','输出',SOURCE_EXPORTED_ELECTRICITY)):
        if not _entries(raw,collection):
            for line in record.calculation_result.lines:
                if line.emission_source_id == source:
                    rows.append((direction, *('历史未记录',)*3, _signed({'intermediate_result':str(line.amount)},direction=='输出')))
    b8_notes = []
    if any(row[0] == '输出' for row in rows):
        b8_notes.append('输出电力对应排放量以负号列示扣减项。')
    if any(item.get('acquisition_mode') == 'SELF_CONSUMED' and item.get('attribute') == 'FOSSIL'
           for item in _entries(raw, 'electricity_details')):
        b8_notes.append('自发自用化石电力归燃料直接排放，不在本表重复计入。')
    sections.append(ReportSection('b8','B.8 购入和输出电力',(_table('b8',rows,source=SOURCE_PURCHASED_ELECTRICITY,raw=raw),),tuple(b8_notes)))

    rows, notes = [], []
    missing_heat_directions = []
    for collection,direction,source in (('purchased_heat','购入',SOURCE_PURCHASED_HEAT),('exported_heat','输出',SOURCE_EXPORTED_HEAT)):
        for item in _entries(raw,collection):
            iid = _text(item.get('line_id'))
            step = _frozen_step(record,trace,source,iid)
            provenance = _mapping(_mapping(step).get('calculation_provenance'))
            variables = _variables(step)
            amount = item.get('steam_amount_t') if item.get('steam_amount_t') is not None else item.get('amount')
            quantity = _value(amount,unit='t')
            value = provenance.get('enthalpy_used_kj_per_kg')
            if value is None:
                value = _mapping(variables.get('HM')).get('value')
            if value is None:
                value = _text(item.get('enthalpy'))
            enthalpy_source = _enum(provenance.get('enthalpy_source'),{'USER_MANUAL':'用户手动填写','SATURATED_TABLE':'标准饱和蒸汽表','SUPERHEATED_TABLE':'标准过热蒸汽表'})
            if provenance.get('table'):
                enthalpy_source = f'{enthalpy_source}；GB/T 32151.34—2024 附录{provenance["table"]}'
            reference = provenance.get('automatic_reference_enthalpy_kj_per_kg')
            enthalpy_detail = enthalpy_source or None
            if reference is not None and provenance.get('enthalpy_source') in {'USER_MANUAL','用户手动填写'}:
                enthalpy_detail = '；'.join(part for part in (
                    enthalpy_detail,
                    f'冻结自动参考焓值：{_text(reference)} kJ/kg；仅供对照，未替换采用值。',
                ) if part)
            factor = _energy_parameter(record,item,iid,f'CAR-FLD-HEAT-{iid}-EF3','tCO2/GJ','EF3',step,source_types=_mapping(trace.get('parameter_source_types')))
            rows.append((direction, _enum(item.get('steam_kind'),{'SATURATED':'饱和蒸汽','SUPERHEATED':'过热蒸汽'}) or '历史未记录', quantity, _value(item.get('pressure_mpa')), _value(item.get('temperature_c')) if item.get('steam_kind')!='SATURATED' else '不适用', _display_cell(value,source={'USER_MANUAL':'填写值','用户手动填写':'填写值','标准表自动确定':'标准查表','SATURATED_TABLE':'标准查表','SUPERHEATED_TABLE':'标准查表'}.get(provenance.get('enthalpy_source'),'历史来源未记录'),detail=enthalpy_detail,unit='kJ/kg') if value is not None else ReportCell('历史未记录'), factor))
    for collection,direction,source in (('purchased_heat','购入',SOURCE_PURCHASED_HEAT),('exported_heat','输出',SOURCE_EXPORTED_HEAT)):
        if not _entries(raw,collection):
            for line in (line for line in record.calculation_result.lines if line.emission_source_id == source):
                rows.append((direction, *('历史未记录',)*6))
                if direction not in missing_heat_directions:
                    missing_heat_directions.append(direction)
    if missing_heat_directions:
        directions = '、'.join(f'{direction}热力' for direction in missing_heat_directions)
        notes.append(f'历史记录未保存{directions}活动输入；B.9 相关字段标记为“历史未记录”。')
    sections.append(ReportSection('b9','B.9 购入和输出热力',(_table('b9',rows,source=SOURCE_PURCHASED_HEAT,raw=raw),),tuple(notes)))
    return tuple(sections)
