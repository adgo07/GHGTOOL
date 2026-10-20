"""只读同Record冻结软件补充；不提供求和、求值或目录查询入口。"""
from collections.abc import Mapping
from decimal import Decimal, localcontext, ROUND_HALF_UP


def _number(value):
    if value is None:return '历史未记录'
    try:
        number=Decimal(str(value))
        if not number.is_finite():return '历史未记录'
        with localcontext() as context:
            context.prec=max(50,len(number.as_tuple().digits)+16);context.rounding=ROUND_HALF_UP
            display=format(number.quantize(Decimal('.01')),'f')
            return format(number,'.2E') if number and Decimal(display)==0 else display
    except (ValueError,ArithmeticError):return '历史未记录'


def frozen_software_supplement(trace):
    node=trace.get('software_supplement') if isinstance(trace,Mapping) else None
    return node if isinstance(node,Mapping) else None


def software_supplement_display(trace):
    node=frozen_software_supplement(trace)
    if node is None:return None
    state=node.get('status')
    states={'HISTORICAL_NOT_RECORDED':'历史未记录','NOT_INCLUDED':'未纳入（草稿不计入）',
            'PENDING':'已纳入，数值待补','COMPLETED_ZERO':'已纳入真实0','COMPLETED_POSITIVE':'已纳入'}
    formed=state in {'COMPLETED_ZERO','COMPLETED_POSITIVE'}
    rows=[('补充状态',states.get(state,'历史未记录')),
          ('原标准合计 ET（tCO₂）',_number(node.get('original_et_tco2'))),
          ('外部 CO₂（tCO₂）',_number(node.get('amount_tco2')) if formed else states.get(state,'历史未记录')),
          ('软件补充合计（tCO₂）',_number(node.get('supplementary_total_tco2')) if formed else '待补／未形成' if state=='PENDING' else '不参与' if state=='NOT_INCLUDED' else '历史未记录')]
    if node.get('label'):rows.append(('外部量短名称',str(node['label'])))
    notes=['外部值按用户同边界、同期且原结果未计入的声明纳入；软件未核验外部计算及完整企业排放。']
    if node.get('core_coverage_complete') is False:
        notes.append('原炭素结果未证明完整监测覆盖；外部补充不补齐原覆盖缺口，不代表完整期间或完整企业总量。')
    return tuple(rows),tuple(notes)


def software_supplement_summary(trace):
    display=software_supplement_display(trace)
    if display is None:return ''
    rows,notes=display
    return '\n'.join(f'{label}：{value}' for label,value in rows)+'\n'+'\n'.join(notes)
