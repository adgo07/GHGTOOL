"""Issue016软件补充：仅由声明Profile求值，不改变标准ET或生成标准行。"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError

EXTERNAL_CO2_METHOD_VERSION = 'CAR-EXTERNAL-CO2-016.1'
EXTERNAL_CO2_ID = 'CAR-SUP-OTHER-ACTIVITY-CO2'

@dataclass(frozen=True, slots=True)
class ExternalCO2Input:
    included: bool = False
    amount_lexeme: str | None = None
    label: str | None = None
    unit: str = 'tCO2'
    known_scope_violation: bool = False
    known_period_mismatch: bool = False
    known_previously_counted: bool = False

    def __post_init__(self):
        for name in ('included','known_scope_violation','known_period_mismatch','known_previously_counted'):
            if type(getattr(self,name)) is not bool:
                raise DomainValidationError('外部补充状态必须是明确的布尔值。')
        for name in ('amount_lexeme','label'):
            if getattr(self,name) is not None and not isinstance(getattr(self,name),str):
                raise DomainValidationError('外部补充原始内容必须保留为文本。')
        if not isinstance(self.unit,str):
            raise DomainValidationError('外部补充单位必须保留为文本。')


def evaluate_external_co2_supplement(value: ExternalCO2Input | None, *, carbon_total_tco2: Decimal,
                                    carbon_complete: bool, policy: DecimalPolicy, numeric_profile_id: str) -> dict:
    if not isinstance(policy,DecimalPolicy) or not isinstance(numeric_profile_id,str) or not numeric_profile_id or numeric_profile_id!=numeric_profile_id.strip():
        raise DomainValidationError('外部补充必须显式消费声明的数值配置。')
    if numeric_profile_id=='GHGTOOL_CARBON_DECIMAL40_CURRENT' and (policy.precision!=40 or policy.rounding!=ROUND_HALF_UP):
        raise DomainValidationError('外部补充数值策略与声明的Carbon Profile不一致。')
    if not isinstance(carbon_total_tco2,Decimal) or not carbon_total_tco2.is_finite() or type(carbon_complete) is not bool:
        raise DomainValidationError('外部补充需要本次原ET及其覆盖资格，不接受显示值。')
    node={'schema_version':1,'business_id':EXTERNAL_CO2_ID,'method_version':EXTERNAL_CO2_METHOD_VERSION,
          'numeric_profile_id':numeric_profile_id,'precision':policy.precision,'rounding':policy.rounding,
          'status':'HISTORICAL_NOT_RECORDED','included':None,'raw_amount_lexeme':None,'raw_unit':None,'label':None,
          'user_scope_declaration':False,'amount_tco2':None,'original_et_tco2':str(carbon_total_tco2),
          'supplementary_total_tco2':None,'core_coverage_complete':carbon_complete,
          'external_calculation_verified':False,'enterprise_completeness_verified':False}
    if value is None:
        return node
    if not isinstance(value,ExternalCO2Input):
        raise DomainValidationError('外部补充输入类型未登记。')
    node.update(included=value.included,raw_amount_lexeme=value.amount_lexeme,raw_unit=value.unit,label=value.label,
                user_scope_declaration=value.included,
                known_scope_violation=value.known_scope_violation,known_period_mismatch=value.known_period_mismatch,
                known_previously_counted=value.known_previously_counted)
    if not value.included:
        node['status']='NOT_INCLUDED'
        return node
    if value.known_scope_violation or value.known_period_mismatch or value.known_previously_counted:
        raise DomainValidationError('该外部量已明确越界、跨期或重复计入，不能纳入补充。')
    if value.unit not in {'tCO2','tCO₂'}:
        raise DomainValidationError('外部补充只接受tCO₂，不能代用tC、tCO₂e或其他单位。')
    if value.amount_lexeme is None or not value.amount_lexeme.strip():
        node['status']='PENDING'
        return node
    try:
        amount=policy.parse(value.amount_lexeme)
        if amount<0:
            raise DomainValidationError('外部CO₂不能为负数。')
        total=policy.add(carbon_total_tco2,amount)
    except (ValueError,ArithmeticError) as exc:
        raise DomainValidationError('外部CO₂必须是非负、有限的十进制数值。') from exc
    node.update(status='COMPLETED_ZERO' if amount==0 else 'COMPLETED_POSITIVE',amount_tco2=str(amount),
                supplementary_total_tco2=str(total))
    return node
