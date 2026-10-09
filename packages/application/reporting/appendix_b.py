"""GB/T 32151.34 approved Appendix B layout and frozen-record field mapping.

Only this standard is registered. Layout contains labels/merges, never formulas.
"""
from __future__ import annotations

import json
from importlib.resources import files
from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping

from packages.core.decimal_policy import DecimalPolicy
from packages.core.units import UnitService
from packages.standards.carbon_material import (
    STANDARD_ID, SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING,
    SOURCE_GRAPHITIZATION, SOURCE_FUME, SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_EXPORTED_ELECTRICITY, SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_HEAT,
)
from .model import (
    ReportCell, ReportRow, ReportTable, ReportSection, _mapping, _entries, _text,
    _enum, _FUEL_NAMES, _SOURCE_NAMES, _parameter_cell, _activity_source,
    _step_for_instance, _step_result, _trace_steps, _display_amount, frozen_totals, _snapshot_mapping, _snapshot_source,
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
    return ReportCell(text, source=_activity_source(value))


def _parameter(value, snapshots, key, *, percent=False):
    cell = _parameter_cell(value, snapshots, key)
    if not cell.value:
        if value is not None and not isinstance(value, Mapping) and _text(value):
            cell = ReportCell(_text(value), source='历史来源未记录')
        else:
            return ReportCell('历史未记录' if value is None else '未填写')
    text = _units(cell.value, cell.unit or 'ratio', 'percent') if percent else cell.value
    return ReportCell(text, source=cell.source or _activity_source(value) or '来源未记录')


def _source_cell(cell):
    return ReportCell(cell.source or ('—' if cell.value == '不适用' else '来源未记录'))


def _number_cell(cell):
    return ReportCell(cell.value)


def _status(raw, source):
    state = next((item for item in _entries(raw, 'source_states') if item.get('source_id') == source), None)
    if state:
        return {'NOT_INVOLVED': '未启用', 'UNCONFIRMED': '未确认'}.get(state.get('status'), '历史未记录此项明细')
    return '历史未记录此项明细'


def _table(key, rows, *, source=None, raw=None, suffix='', merges=(), notes=()):
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
        body_merges=tuple(merges), footnotes=tuple(layout['footnotes']) + tuple(notes),
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


def _energy_parameter(record, item, iid, explicit_key, unit, variable, step, *, ambiguous_detail_ids=()):
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
        return ReportCell(_text(snapshot["value_used"]), source=_snapshot_source(snapshot) or "来源未记录")
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
    for group, role, component, mass_key, ratio_key in _PROCESS_ROWS[key]:
        matching = [m for m in materials if m.get('role') == role]
        if matching:
            for material in matching:
                source_key = 'fixed_carbon_source' if component == 'fixed_carbon_percent' else 'volatile_matter_source'
                rows.append((group, material.get('name') or _ROLE_NAMES[role], _value(material.get('mass_t')), _value(material.get(component)), _enum(material.get(source_key), _SOURCE_NAMES) or '来源未记录'))
        elif materials:
            rows.append((group, _ROLE_NAMES[role], '未列示此物流', '—', '—'))
        else:
            # Legacy scalar inputs have frozen aggregated data, not individual material identities.
            mass = process.get(mass_key) if mass_key else None
            ratio = process.get(ratio_key) if ratio_key else None
            if mass is None:
                mass = variables.get(mass_key)
            if ratio is None:
                ratio = variables.get(ratio_key)
            rows.append((group, _ROLE_NAMES[role], _value(mass) if mass is not None else '历史未记录', _number_cell(_value(ratio, percent=True)) if ratio is not None else '历史未记录', _activity_source(ratio) or _enum(_mapping(ratio).get('source_kind'), _SOURCE_NAMES) or '来源未记录'))
    # Merge adjacent group labels without discarding distinct material names.
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i][0] != rows[start][0]:
            if i - start > 1:
                merges.append((start, 0, i - 1, 0))
            start = i
    last = len(rows)
    rows.append(('排放量（tCO₂）', '', _step_result(step) or '历史未记录', '', ''))
    merges.extend(((last, 0, last, 1), (last, 2, last, 4)))
    return replace(_table(key, rows, source=source, raw=raw, suffix=f'-{ordinal}', merges=merges,
                  notes=('收到基；逐过程列示冻结结果，不向物料分摊。' + ('' if materials else '此记录仅存汇总输入，无逐物料快照。'),)), context_label=f'过程单元{ordinal}')


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

    b1_table = sections[0].tables[0]
    subject = enterprise_name or record.input_snapshot.enterprise_name or '报告主体'
    year = record.input_snapshot.period.start.year
    b1_title = b1_table.title.replace('报告主体                 年', f'{subject} {year}年')
    sections[0] = replace(sections[0], tables=(replace(b1_table, title=b1_title),))

    rows = []
    fuel_notes = []
    for i, item in enumerate(_entries(raw, 'fuel_inputs'), 1):
        iid = _text(item.get('fuel_id'))
        prefix = f'CAR-FLD-F01-{iid}'
        carbon = _parameter(item.get('carbon_content'), snapshots, prefix+'-CARBON')
        carbon_unit = _parameter_cell(item.get('carbon_content'), snapshots, prefix+'-CARBON').unit
        lhv = _parameter(item.get('lower_heating_value'), snapshots, prefix+'-LHV') if item.get('lower_heating_value') is not None or prefix+'-LHV' in snapshots else ReportCell('不适用')
        oxidation = _parameter(item.get('oxidation_rate'), snapshots, prefix+'-FOX', percent=True)
        path = item.get('path')
        unit = {'MASS':'t', 'VOLUME':'ten_thousand_Nm3', 'HEAT':'GJ'}.get(path)
        activity = _value(item.get('activity'), unit=unit)
        if path == 'HEAT':
            activity = replace(activity, unit='GJ（热量计量）')
            fuel_notes.append(f'燃料{i}按冻结的热量活动数据列示，不反推质量或体积。')
        if carbon_unit == 'tC/GJ':
            # A derived fuel carbon content was never frozen; do not recompute LHV × carbon.
            direct_carbon = ReportCell('未记录（采用单位热值含碳量）')
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
        rows.append((item.get('fuel_label') or _enum(item.get('fuel_type'), _FUEL_NAMES), activity, _number_cell(direct_carbon), _source_cell(direct_carbon), _number_cell(lhv), _source_cell(lhv), unit_carbon, _number_cell(oxidation), _source_cell(oxidation), result))
    if not rows:
        for i,line in enumerate(record.calculation_result.lines,1):
            if line.emission_source_id == SOURCE_FUEL:
                rows.append((f'历史燃料结果{i}', *('历史未记录',)*8, _display_amount(line.amount)))
    sections.append(ReportSection('b2', 'B.2 化石燃料活动数据和排放因子', (_table('b2', rows, source=SOURCE_FUEL, raw=raw),), tuple(fuel_notes)))

    for key, title, collection, legacy, source in (
        ('b3','B.3 原料煅烧','calcinations','calcination',SOURCE_CALCINATION),
        ('b4','B.4 焙烧/炭化','bakings','baking',SOURCE_BAKING),
        ('b5','B.5 石墨化','graphitizations','graphitization',SOURCE_GRAPHITIZATION),
    ):
        tables = tuple(_process_table(key, process, _frozen_step(record,trace,source,process.get('instance_id'),single_instance=len(_entries(raw,collection,legacy))==1), i, source, raw) for i, process in enumerate(_entries(raw,collection,legacy),1))
        if not tables:
            tables = tuple(_process_table(key, {}, {'intermediate_result': str(line.amount)}, i, source, raw) for i,line in enumerate((line for line in record.calculation_result.lines if line.emission_source_id == source),1))
        sections.append(ReportSection(key,title,tables or (_table(key,[],source=source,raw=raw),)))

    rows = []
    for i, item in enumerate(_entries(raw,'fume_incinerations','fume_incineration'),1):
        iid = _text(item.get('instance_id'))
        rows.append((_value(item.get('q')), _value(item.get('qvar')), _value(item.get('hm')), _parameter(item.get('fch'),snapshots,f'CAR-FLD-P04A-{iid}-FCH'), _value(item.get('fox'),percent=True), _value(item.get('duration')), _signed(_frozen_step(record,trace,SOURCE_FUME,iid,single_instance=len(_entries(raw,'fume_incinerations','fume_incineration'))==1))))
    if not rows:
        rows = [(*('历史未记录',)*6, _display_amount(line.amount)) for line in record.calculation_result.lines if line.emission_source_id == SOURCE_FUME]
    sections.append(ReportSection('b6','B.6 烟气焚烧治理',(_table('b6',rows,source=SOURCE_FUME,raw=raw),), ('每行对应一套设施，按冻结输入顺序列示。',)))

    rows, merges = [], []
    for i, unit in enumerate(_entries(raw,'fgd_units','fgd'),1):
        iid = _text(unit.get('instance_id'))
        start = len(rows)
        components = _entries(unit,'components')
        for index, comp in enumerate(components):
            prefix = f'CAR-FLD-P04B-{iid}-{index}'
            rows.append((f'设施/批次{i}', _value(comp.get('amount'),unit='t'), comp.get('carbonate_type') or '历史未记录', _parameter(comp.get('carbonate_fraction'),snapshots,prefix+'-I',percent=True), _parameter(comp.get('emission_factor'),snapshots,prefix+'-EF1'), _parameter(comp.get('conversion_rate'),snapshots,prefix+'-TR',percent=True), _signed(_frozen_step(record,trace,SOURCE_FGD,iid,single_instance=len(_entries(raw,'fgd_units','fgd'))==1)) if index==0 else ''))
        end = len(rows)-1
        if end > start:
            merges.extend(((start,0,end,0),(start,6,end,6)))
            if all(rows[j][1] == rows[start][1] for j in range(start,end+1)):
                merges.append((start,1,end,1))
    if not rows:
        rows = [(f'历史设施/批次{i}', *('历史未记录',)*5, _display_amount(line.amount)) for i,line in enumerate((line for line in record.calculation_result.lines if line.emission_source_id == SOURCE_FGD),1)]
    sections.append(ReportSection('b7','B.7 烟气脱硫净化',(_table('b7',rows,source=SOURCE_FGD,raw=raw,merges=merges),), ('排放量合并单元格列示该设施/批次的冻结合计；历史快照未保存逐组分排放量时不重新计算。',)))

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
                                       ambiguous_detail_ids=ambiguous_ids)
            rows.append((direction, _enum(item.get('attribute'),{'ORDINARY':'常规电力','NONFOSSIL':'非化石电力','FOSSIL':'化石能源电力'}) or '历史未记录', quantity, factor, _signed(step,direction=='输出')))
    for collection,direction,source in (('electricity_details','购入',SOURCE_PURCHASED_ELECTRICITY),('exported_electricity','输出',SOURCE_EXPORTED_ELECTRICITY)):
        if not _entries(raw,collection):
            for line in record.calculation_result.lines:
                if line.emission_source_id == source:
                    rows.append((direction, *('历史未记录',)*3, _signed({'intermediate_result':str(line.amount)},direction=='输出')))
    sections.append(ReportSection('b8','B.8 购入和输出电力',(_table('b8',rows,source=SOURCE_PURCHASED_ELECTRICITY,raw=raw),), ('输出电力对应排放量以负号列示扣减项。自发自用化石电力归燃料直接排放，不在本表重复计入。',)))

    rows, notes = [], []
    for collection,direction,source in (('purchased_heat','购入',SOURCE_PURCHASED_HEAT),('exported_heat','输出',SOURCE_EXPORTED_HEAT)):
        for i,item in enumerate(_entries(raw,collection),1):
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
            factor = _energy_parameter(record,item,iid,f'CAR-FLD-HEAT-{iid}-EF3','tCO2/GJ','EF3',step)
            rows.append((direction, _enum(item.get('steam_kind'),{'SATURATED':'饱和蒸汽','SUPERHEATED':'过热蒸汽'}) or '历史未记录', quantity, _value(item.get('pressure_mpa')), _value(item.get('temperature_c')) if item.get('steam_kind')!='SATURATED' else '不适用', ReportCell(_text(value) or '历史未记录',source=enthalpy_source or '历史来源未记录'), factor))
            notes.append(f'{direction}热力第{i}条对应排放量：{_signed(step,direction=="输出")} tCO₂' + ('（扣减项）' if direction=='输出' else ''))
            reference = provenance.get('automatic_reference_enthalpy_kj_per_kg')
            if reference is not None:
                notes.append(f'{direction}热力第{i}条冻结自动参考焓值：{reference} kJ/kg；仅供对照，未替换采用值。')
    for collection,direction,source in (('purchased_heat','购入',SOURCE_PURCHASED_HEAT),('exported_heat','输出',SOURCE_EXPORTED_HEAT)):
        if not _entries(raw,collection):
            for i,line in enumerate((line for line in record.calculation_result.lines if line.emission_source_id == source),1):
                rows.append((direction, *('历史未记录',)*6))
                notes.append(f'{direction}热力历史结果第{i}条：{_signed({"intermediate_result":str(line.amount)},direction=="输出")} tCO₂；输入和来源快照缺失。')
    sections.append(ReportSection('b9','B.9 购入和输出热力',(_table('b9',rows,source=SOURCE_PURCHASED_HEAT,raw=raw),),tuple(notes)))
    return tuple(sections)
