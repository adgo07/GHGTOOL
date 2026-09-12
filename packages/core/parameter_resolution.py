"""Context-driven parameter selection and immutable snapshot creation for G05."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from .errors import DomainValidationError, IssueLevel, ValidationProblem
from .models import (
    AccountingPeriod,
    Factor,
    ParameterSelectionMethod,
    ParameterSnapshot,
    ParameterType,
    ReviewStatus,
    ValueType,
)
from .repositories import ParameterRepository
from .rules import (
    EffectiveRuleResolver,
    EffectiveRuleSet,
    ParameterSelectionPolicy,
    RuleApplicability,
    RuleContext,
    RuleDefinition,
    RuleEvidenceStatus,
    RuleOrigin,
    RuleRelation,
)


class FactorSourceMode(str, Enum):
    MEASURED = "MEASURED"
    CALCULATED = "CALCULATED"
    REFERENCE = "REFERENCE"
    STANDARD_DEFAULT = "STANDARD_DEFAULT"
    OFFICIAL_PUBLISHED = "OFFICIAL_PUBLISHED"
    USER_DEFINED = "USER_DEFINED"
    PROJECT_SPECIFIED = "PROJECT_SPECIFIED"
    SYSTEM_CONSTANT = "SYSTEM_CONSTANT"


class ParameterValueCategory(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    OTHER_APPLICABLE = "OTHER_APPLICABLE"
    HISTORICAL = "HISTORICAL"
    ENTERPRISE_MEASURED = "ENTERPRISE_MEASURED"


class FactorRelationType(str, Enum):
    SUPERSEDES = "SUPERSEDES"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    REFERENCED_BY = "REFERENCED_BY"
    SAME_VALUE_DIFFERENT_SOURCE = "SAME_VALUE_DIFFERENT_SOURCE"
    CONFLICTS_WITH = "CONFLICTS_WITH"


def _require_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise DomainValidationError(f"{field_name} must be a stable identifier")
    return value


@dataclass(frozen=True, slots=True)
class FactorApplicability:
    """Structured factor applicability metadata used by the resolver."""

    factor_id: str
    standard_id: str | None = None
    framework: str | None = None
    industry: str | None = None
    region: str | None = None
    subject_id: str | None = None
    parameter_type: ParameterType | None = None
    emission_source_type: str | None = None
    greenhouse_gas: str | None = None
    applicable_period_from: date | None = None
    applicable_period_to: date | None = None
    priority: int = 0
    conditions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.factor_id, "factor_id")
        for name in (
            "standard_id",
            "framework",
            "subject_id",
            "emission_source_type",
            "greenhouse_gas",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_id(value, name)
        if self.parameter_type is not None and not isinstance(self.parameter_type, ParameterType):
            raise DomainValidationError("parameter_type must be a ParameterType")
        if self.applicable_period_from and self.applicable_period_to and self.applicable_period_to < self.applicable_period_from:
            raise DomainValidationError("factor applicability dates are out of order")
        if not isinstance(self.priority, int):
            raise DomainValidationError("factor applicability priority must be an integer")
        normalized = tuple(self.conditions)
        if len({key for key, _ in normalized}) != len(normalized):
            raise DomainValidationError("factor applicability condition keys must be unique")
        object.__setattr__(self, "conditions", normalized)

    def matches(self, context: "ParameterResolutionContext") -> bool:
        if self.standard_id and self.standard_id != context.standard_id:
            return False
        if self.framework and self.framework != context.reporting_framework:
            return False
        if self.industry and self.industry != context.industry:
            return False
        if self.region and self.region != context.region:
            return False
        if self.subject_id and self.subject_id != context.subject_id:
            return False
        if self.parameter_type and self.parameter_type is not context.parameter_type:
            return False
        if self.emission_source_type and self.emission_source_type != context.emission_source_type:
            return False
        if self.greenhouse_gas and self.greenhouse_gas != context.greenhouse_gas:
            return False
        period = context.accounting_period
        if self.applicable_period_from and (period is None or period.end < self.applicable_period_from):
            return False
        if self.applicable_period_to and (period is None or period.start > self.applicable_period_to):
            return False
        values = dict(context.extra_context)
        return all(values.get(key) == value for key, value in self.conditions)


@dataclass(frozen=True, slots=True)
class FactorRelation:
    left_factor_id: str
    relation: FactorRelationType
    right_factor_id: str
    reason: str

    def __post_init__(self) -> None:
        _require_id(self.left_factor_id, "left_factor_id")
        _require_id(self.right_factor_id, "right_factor_id")
        if not isinstance(self.relation, FactorRelationType):
            raise DomainValidationError("relation must be a FactorRelationType")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise DomainValidationError("factor relation reason is required")


@dataclass(frozen=True, slots=True)
class ParameterResolutionContext:
    """All context fields that may affect a recommended value."""

    parameter_id: str
    standard_id: str | None = None
    accounting_period: AccountingPeriod | None = None
    region: str | None = None
    industry: str | None = None
    subject_id: str | None = None
    parameter_type: ParameterType | None = None
    emission_source_type: str | None = None
    greenhouse_gas: str | None = None
    electricity_type: str | None = None
    electricity_accounting_mode: str | None = None
    reporting_framework: str | None = None
    required_source_mode: FactorSourceMode | None = None
    required_factor_version: str | None = None
    measured_value_available: bool = False
    measured_evidence_available: bool = False
    measured_factor: Factor | None = None
    confirmed_factor_id: str | None = None
    confirmation_reason: str | None = None
    extra_context: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.parameter_id, "parameter_id")
        if self.standard_id is not None:
            _require_id(self.standard_id, "standard_id")
        if self.subject_id is not None:
            _require_id(self.subject_id, "subject_id")
        if self.parameter_type is not None and not isinstance(self.parameter_type, ParameterType):
            raise DomainValidationError("parameter_type must be a ParameterType")
        if self.required_source_mode is not None and not isinstance(self.required_source_mode, FactorSourceMode):
            raise DomainValidationError("required_source_mode must be a FactorSourceMode")
        if self.required_factor_version is not None:
            _require_id(self.required_factor_version, "required_factor_version")
        if self.confirmed_factor_id is not None:
            _require_id(self.confirmed_factor_id, "confirmed_factor_id")
        if self.confirmation_reason is not None and not self.confirmation_reason.strip():
            raise DomainValidationError("confirmation_reason cannot be blank")
        object.__setattr__(self, "extra_context", tuple(self.extra_context))

    def to_rule_context(self) -> RuleContext:
        return RuleContext(
            standard_id=self.standard_id,
            accounting_period=self.accounting_period,
            region=self.region,
            industry=self.industry,
            subject_id=self.subject_id,
            parameter_type=self.parameter_type,
            emission_source_type=self.emission_source_type,
            greenhouse_gas=self.greenhouse_gas,
            electricity_type=self.electricity_type,
            electricity_accounting_mode=self.electricity_accounting_mode,
            reporting_framework=self.reporting_framework,
            extra_context=self.extra_context,
        )


@dataclass(frozen=True, slots=True)
class ResolvedParameterValue:
    factor: Factor
    category: ParameterValueCategory
    priority: int
    match_reasons: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()

    @property
    def factor_id(self) -> str:
        return self.factor.factor_id

    @property
    def source_id(self) -> str | None:
        return self.factor.source_id


@dataclass(frozen=True, slots=True)
class ParameterResolution:
    context: ParameterResolutionContext
    recommended: ResolvedParameterValue | None
    alternatives: tuple[ResolvedParameterValue, ...]
    historical: tuple[ResolvedParameterValue, ...]
    selection_method: ParameterSelectionMethod | None
    selection_reason: str
    warnings: tuple[ValidationProblem, ...]
    effective_rules: EffectiveRuleSet
    requires_confirmation: bool = False

    @property
    def blocked(self) -> bool:
        return any(problem.level is IssueLevel.ERROR for problem in self.warnings)

    def to_snapshot(self, snapshot_id: str, snapshot_at: datetime) -> ParameterSnapshot:
        if self.recommended is None or self.selection_method is None:
            raise DomainValidationError("a parameter resolution without a recommendation cannot be snapshotted")
        factor = self.recommended.factor
        if self.context.standard_id is None:
            raise DomainValidationError("snapshot requires a standard_id in the resolution context")
        return ParameterSnapshot(
            snapshot_id=snapshot_id,
            parameter_id=factor.parameter_id,
            factor_id=factor.factor_id,
            value_used=factor.value,
            unit_used=factor.unit,
            source_id=factor.source_id,
            source_version=factor.version,
            selection_method=self.selection_method,
            selection_reason=self.selection_reason,
            standard_id=self.context.standard_id,
            snapshot_at=snapshot_at,
            factor_version=factor.version,
            source_location=factor.source_location,
            factor_year=factor.factor_year,
        )


def _source_mode(factor: Factor) -> FactorSourceMode:
    return {
        ValueType.MEASURED: FactorSourceMode.MEASURED,
        ValueType.DERIVED: FactorSourceMode.CALCULATED,
        ValueType.SCIENTIFIC_REFERENCE: FactorSourceMode.REFERENCE,
        ValueType.STANDARD_DEFAULT: FactorSourceMode.STANDARD_DEFAULT,
        ValueType.STANDARD_SPECIFIED: FactorSourceMode.STANDARD_DEFAULT,
        ValueType.GOVERNMENT_PUBLISHED: FactorSourceMode.OFFICIAL_PUBLISHED,
        ValueType.SYSTEM_CONSTANT: FactorSourceMode.SYSTEM_CONSTANT,
        ValueType.HISTORICAL: FactorSourceMode.REFERENCE,
    }[factor.value_type]


def _is_historical(factor: Factor, context: ParameterResolutionContext) -> bool:
    if factor.value_type is ValueType.HISTORICAL or factor.review_status is ReviewStatus.DEPRECATED:
        return True
    period = context.accounting_period
    return bool(period and factor.valid_to and factor.valid_to < period.start)


class ParameterResolver:
    """Resolve one parameter through effective rules and immutable candidates."""

    def __init__(
        self,
        repository: ParameterRepository,
        *,
        common_rules: Sequence[RuleDefinition] = (),
        industry_rules: Sequence[RuleDefinition] = (),
        applicability: Sequence[FactorApplicability] = (),
        relations: Sequence[FactorRelation] = (),
        rule_resolver: EffectiveRuleResolver | None = None,
    ) -> None:
        self._repository = repository
        self._common_rules = tuple(common_rules)
        self._industry_rules = tuple(industry_rules)
        self._applicability = {item.factor_id: item for item in applicability}
        self._relations = tuple(relations)
        self._rule_resolver = rule_resolver or EffectiveRuleResolver()

    @classmethod
    def with_default_g05_rules(cls, repository: ParameterRepository) -> "ParameterResolver":
        common, industry = default_g05_rules()
        return cls(repository, common_rules=common, industry_rules=industry)

    def _effective_rules(self, context: ParameterResolutionContext) -> EffectiveRuleSet:
        return self._rule_resolver.resolve(
            self._common_rules,
            self._industry_rules,
            context.to_rule_context(),
        )

    def _collect_factors(self, context: ParameterResolutionContext) -> tuple[Factor, ...]:
        factors = list(self._repository.list_factors(context.parameter_id))
        if context.measured_factor is not None and context.measured_factor.factor_id not in {
            factor.factor_id for factor in factors
        }:
            factors.append(context.measured_factor)
        return tuple(factor for factor in factors if self._factor_matches(factor, context))

    def _factor_matches(self, factor: Factor, context: ParameterResolutionContext) -> bool:
        if factor.parameter_id != context.parameter_id:
            return False
        if context.subject_id and factor.subject_id != context.subject_id:
            return False
        if context.parameter_type and factor.parameter_type is not context.parameter_type:
            return False
        if context.standard_id and factor.applicable_standard_ids and context.standard_id not in factor.applicable_standard_ids:
            return False
        applicability = self._applicability.get(factor.factor_id)
        if applicability is not None and not applicability.matches(context):
            return False
        period = context.accounting_period
        if period and factor.valid_from and factor.valid_from > period.end:
            return False
        if period and factor.valid_to and factor.valid_to < period.start:
            return False
        return True

    def _value(
        self,
        factor: Factor,
        context: ParameterResolutionContext,
        *,
        priority: int,
        reasons: tuple[str, ...],
    ) -> ResolvedParameterValue:
        if factor.value_type is ValueType.MEASURED:
            category = ParameterValueCategory.ENTERPRISE_MEASURED
        elif _is_historical(factor, context):
            category = ParameterValueCategory.HISTORICAL
        else:
            category = ParameterValueCategory.OTHER_APPLICABLE
        return ResolvedParameterValue(factor, category, priority, reasons)

    def _rank(
        self,
        factor: Factor,
        context: ParameterResolutionContext,
        policy: ParameterSelectionPolicy,
        rule: RuleDefinition | None,
    ) -> tuple[int, tuple[str, ...]]:
        if factor.source_id is None or factor.review_status in {ReviewStatus.PENDING_SOURCE, ReviewStatus.DEPRECATED}:
            return -1, ()
        if context.required_source_mode and _source_mode(factor) is not context.required_source_mode:
            return -1, ()
        if context.required_factor_version and factor.version != context.required_factor_version:
            return -1, ()
        if rule and rule.required_factor_version and factor.version != rule.required_factor_version:
            return -1, ()
        reasons: list[str] = []
        rank = 100
        required_factor_match = bool(rule and rule.required_factor_id == factor.factor_id)
        if required_factor_match and policy is not ParameterSelectionPolicy.MEASURED_FIRST:
            rank += 10_000
            reasons.append(f"规则指定因子 {factor.factor_id}")
        if policy is ParameterSelectionPolicy.NO_AUTOMATIC_SELECTION:
            return -1, ()
        if policy is ParameterSelectionPolicy.STANDARD_REQUIRED:
            if context.standard_id and context.standard_id in factor.applicable_standard_ids:
                if factor.value_type is ValueType.STANDARD_SPECIFIED:
                    rank += 900
                    reasons.append("当前标准直接规定")
                elif factor.value_type is ValueType.STANDARD_DEFAULT:
                    rank += 850
                    reasons.append("当前标准缺省值")
            else:
                return -1, ()
        elif policy is ParameterSelectionPolicy.MEASURED_FIRST:
            if factor.value_type is ValueType.MEASURED and context.measured_evidence_available:
                rank += 10_000
                reasons.append("存在合格实测值")
            elif factor.value_type is ValueType.STANDARD_DEFAULT:
                rank += 800
                if required_factor_match:
                    rank += 500
                    reasons.append(f"规则指定缺省因子 {factor.factor_id}")
                reasons.append("无合格实测值，回退标准缺省值")
            else:
                return -1, ()
        elif policy is ParameterSelectionPolicy.OFFICIAL_LATEST:
            if factor.value_type is not ValueType.GOVERNMENT_PUBLISHED:
                return -1, ()
            rank += 700 + (factor.factor_year or 0)
            reasons.append("主管部门官方发布值")
        elif policy is ParameterSelectionPolicy.SYSTEM_GWP:
            if factor.value_type is not ValueType.SCIENTIFIC_REFERENCE:
                return -1, ()
            rank += 700 + (factor.factor_year or 0)
            reasons.append("系统 GWP 通用推荐")
        if factor.factor_year:
            reasons.append(f"因子年度 {factor.factor_year}")
        return rank, tuple(reasons)

    def _problem(self, code: str, level: IssueLevel, message: str, field_id: str) -> ValidationProblem:
        return ValidationProblem(code, level, message, field_id)

    def resolve(self, context: ParameterResolutionContext) -> ParameterResolution:
        effective = self._effective_rules(context)
        problems = list(effective.problems)
        rules = effective.rules_for_parameter(context.parameter_id)
        rule = rules[0] if rules else None
        policy = rule.selection_policy if rule and rule.selection_policy else ParameterSelectionPolicy.NO_AUTOMATIC_SELECTION
        factors = self._collect_factors(context)

        if context.measured_factor is not None and not context.measured_evidence_available:
            problems.append(
                self._problem(
                    "GEN-VAL-MEASURED-NO-TEST-INFO",
                    IssueLevel.WARNING,
                    "实测值缺少合格检测或取样证据，不能按实测优先自动采用。",
                    context.parameter_id,
                )
            )
        if policy is ParameterSelectionPolicy.MEASURED_FIRST and context.measured_factor is None:
            problems.append(
                self._problem(
                    "GEN-PAR-MEASURED-FALLBACK",
                    IssueLevel.WARNING,
                    "当前规则要求实测优先，但未提供合格实测值，将回退到标准缺省值。",
                    context.parameter_id,
                )
            )

        ranked: list[ResolvedParameterValue] = []
        current_values: list[ResolvedParameterValue] = []
        historical: list[ResolvedParameterValue] = []
        for factor in factors:
            if factor.source_id is None:
                problems.append(
                    self._problem(
                        "GEN-VAL-FACTOR-NO-SOURCE",
                        IssueLevel.ERROR,
                        f"因子 {factor.factor_id} 缺少来源定位，不能自动采用。",
                        factor.factor_id,
                    )
                )
                continue
            if _is_historical(factor, context):
                historical.append(self._value(factor, context, priority=0, reasons=("历史或已弃用值",)))
                continue
            rank, reasons = self._rank(factor, context, policy, rule)
            if rank >= 0:
                ranked.append(self._value(factor, context, priority=rank, reasons=reasons))
            else:
                current_values.append(
                    self._value(
                        factor,
                        context,
                        priority=0,
                        reasons=("当前仍是可查看的适用值，但不满足自动推荐条件",),
                    )
                )

        ranked.sort(key=lambda item: (-item.priority, item.factor.factor_id))
        historical.sort(key=lambda item: (-(item.factor.factor_year or 0), item.factor.factor_id))
        recommended: ResolvedParameterValue | None = None
        selection_method: ParameterSelectionMethod | None = None
        selection_reason = "当前没有可以自动确定的唯一适用参数值。"
        requires_confirmation = False

        candidate_by_id = {item.factor.factor_id: item for item in ranked}
        if context.confirmed_factor_id is not None:
            if not context.confirmation_reason:
                problems.append(
                    self._problem(
                        "GEN-PAR-CONFIRMATION-REASON",
                        IssueLevel.ERROR,
                        "用户确认采用其他参数值时必须保存选择理由。",
                        context.confirmed_factor_id,
                    )
                )
            elif context.confirmed_factor_id not in candidate_by_id:
                problems.append(
                    self._problem(
                        "GEN-PAR-CONFIRMATION-INVALID",
                        IssueLevel.ERROR,
                        "用户确认的参数值不是当前上下文中的可用值。",
                        context.confirmed_factor_id,
                    )
                )
            else:
                recommended = candidate_by_id[context.confirmed_factor_id]
                selection_method = ParameterSelectionMethod.USER_SELECTED_LIBRARY_VALUE
                selection_reason = context.confirmation_reason
        elif not effective.blocked and policy is not ParameterSelectionPolicy.NO_AUTOMATIC_SELECTION:
            if ranked:
                top_priority = ranked[0].priority
                top = [item for item in ranked if item.priority == top_priority]
                if len(top) == 1:
                    recommended = top[0]
                    recommended = ResolvedParameterValue(
                        recommended.factor,
                        ParameterValueCategory.RECOMMENDED,
                        recommended.priority,
                        recommended.match_reasons,
                        recommended.evidence_requirements,
                    )
                    selection_method = (
                        ParameterSelectionMethod.ENTERPRISE_MEASURED
                        if recommended.factor.value_type is ValueType.MEASURED
                        else ParameterSelectionMethod.STANDARD_REQUIRED
                        if policy is ParameterSelectionPolicy.STANDARD_REQUIRED
                        else ParameterSelectionMethod.SYSTEM_RECOMMENDED
                    )
                    selection_reason = "；".join(recommended.match_reasons) or "按有效规则唯一确定。"
                else:
                    requires_confirmation = True
                    problems.append(
                        self._problem(
                            "GEN-PAR-CONFIRMATION-REQUIRED",
                            IssueLevel.ERROR,
                            "多个参数值同样适用且无法唯一确定，必须由用户确认并保存理由。",
                            context.parameter_id,
                        )
                    )
            else:
                problems.append(
                    self._problem(
                        "GEN-PAR-NO-APPLICABLE-VALUE",
                        IssueLevel.ERROR,
                        "当前规则下没有可自动采用的参数值。",
                        context.parameter_id,
                    )
                )
        elif not effective.blocked:
            requires_confirmation = True
            problems.append(
                self._problem(
                    "GEN-PAR-CONFIRMATION-REQUIRED",
                    IssueLevel.ERROR,
                    "没有适用的正式推荐规则，不能静默猜选参数值。",
                    context.parameter_id,
                )
            )

        selected_id = recommended.factor.factor_id if recommended else None
        alternative_by_id = {
            item.factor.factor_id: item
            for item in (*ranked, *current_values)
            if item.factor.factor_id != selected_id
        }
        alternatives = tuple(
            sorted(
                alternative_by_id.values(),
                key=lambda item: (-item.priority, item.factor.factor_id),
            )
        )
        return ParameterResolution(
            context=context,
            recommended=recommended,
            alternatives=alternatives,
            historical=tuple(historical),
            selection_method=selection_method,
            selection_reason=selection_reason,
            warnings=tuple(problems),
            effective_rules=effective,
            requires_confirmation=requires_confirmation,
        )

    def resolve_recommended_value(self, context: ParameterResolutionContext) -> ParameterResolution:
        return self.resolve(context)

    def resolve_parameter(self, context: ParameterResolutionContext) -> ParameterResolution:
        return self.resolve(context)


def _parameter_rule(
    rule_id: str,
    parameter_id: str,
    policy: ParameterSelectionPolicy,
    *,
    relation: RuleRelation,
    standard_id: str,
    applicable_standard_ids: tuple[str, ...],
    required_factor_id: str | None = None,
    priority: int = 100,
    description: str,
) -> RuleDefinition:
    return RuleDefinition(
        rule_id=rule_id,
        rule_domain="parameter_selection",
        target_id=parameter_id,
        parameter_id=parameter_id,
        relation=relation,
        description=description,
        standard_id=standard_id,
        applicability=RuleApplicability(standard_ids=applicable_standard_ids),
        priority=priority,
        origin=RuleOrigin.STANDARD_EXPLICIT,
        evidence_status=RuleEvidenceStatus.VERIFIED,
        selection_policy=policy,
        required_factor_id=required_factor_id,
    )


def default_g05_rules() -> tuple[tuple[RuleDefinition, ...], tuple[RuleDefinition, ...]]:
    """Return the small, source-backed rule set needed by the first standard.

    These are rule records, not UI conditionals.  The canonical catalog remains
    the source of factor values; this function only registers the approved
    mapping between contexts and those values for the G05 resolver.
    """

    common = (
        _parameter_rule(
            "GEN-PAR-ELECTRICITY-NATIONAL-LATEST",
            "electricity_emission_factor_national",
            ParameterSelectionPolicy.OFFICIAL_LATEST,
            relation=RuleRelation.BASE,
            standard_id="gbt_32150_2025",
            applicable_standard_ids=("gbt_32150_2025", "gbt_32151_34_2024"),
            required_factor_id="electricity_national_average_2023",
            description="通则要求采用符合条件的最新全国官方电力平均因子。",
        ),
        _parameter_rule(
            "GEN-PAR-HEAT-DEFAULT-011",
            "heat_emission_factor_default",
            ParameterSelectionPolicy.MEASURED_FIRST,
            relation=RuleRelation.BASE,
            standard_id="gbt_32150_2025",
            applicable_standard_ids=("gbt_32150_2025", "gbt_32151_34_2024"),
            required_factor_id="heat_default_2025",
            description="通则要求供热单位实测优先，无实测时采用 0.11 缺省值。",
        ),
        _parameter_rule(
            "GEN-PAR-GWP-SYSTEM-001",
            "gwp_co2_ar6_100",
            ParameterSelectionPolicy.SYSTEM_GWP,
            relation=RuleRelation.BASE,
            standard_id="gbt_32150_2025",
            applicable_standard_ids=("gbt_32150_2025", "gbt_32151_34_2024"),
            required_factor_id="gwp_co2_ar6_100",
            description="未指定其他制度时采用系统 GWP 通用推荐策略。",
        ),
    )
    industry = (
        _parameter_rule(
            "CAR-PAR-NATURAL-GAS-LHV-SELECT",
            "natural_gas_lhv",
            ParameterSelectionPolicy.STANDARD_REQUIRED,
            relation=RuleRelation.SPECIALIZE,
            standard_id="gbt_32151_34_2024",
            applicable_standard_ids=("gbt_32151_34_2024",),
            required_factor_id="natural_gas_lhv_gbt32151_34_c1",
            description="炭素材料生产标准直接规定天然气低位发热量。",
        ),
        _parameter_rule(
            "CAR-PAR-NATURAL-GAS-CARBON-SELECT",
            "natural_gas_carbon_content",
            ParameterSelectionPolicy.STANDARD_REQUIRED,
            relation=RuleRelation.SPECIALIZE,
            standard_id="gbt_32151_34_2024",
            applicable_standard_ids=("gbt_32151_34_2024",),
            required_factor_id="natural_gas_carbon_content_gbt32151_34_c1",
            description="炭素材料生产标准直接规定天然气单位热值含碳量。",
        ),
        _parameter_rule(
            "CAR-PAR-NATURAL-GAS-OXIDATION-SELECT",
            "natural_gas_oxidation_rate",
            ParameterSelectionPolicy.STANDARD_REQUIRED,
            relation=RuleRelation.SPECIALIZE,
            standard_id="gbt_32151_34_2024",
            applicable_standard_ids=("gbt_32151_34_2024",),
            required_factor_id="natural_gas_oxidation_rate_gbt32151_34_c1",
            description="炭素材料生产标准直接规定天然气碳氧化率。",
        ),
        _parameter_rule(
            "CAR-PAR-ELECTRICITY-NATIONAL-LATEST",
            "electricity_emission_factor_national",
            ParameterSelectionPolicy.OFFICIAL_LATEST,
            relation=RuleRelation.SPECIALIZE,
            standard_id="gbt_32151_34_2024",
            applicable_standard_ids=("gbt_32151_34_2024",),
            required_factor_id="electricity_national_average_2023",
            description="炭素材料生产标准明确采用最新全国电力平均官方因子。",
        ),
        _parameter_rule(
            "CAR-PAR-HEAT-MEASURED-OR-DEFAULT",
            "heat_emission_factor_default",
            ParameterSelectionPolicy.MEASURED_FIRST,
            relation=RuleRelation.SPECIALIZE,
            standard_id="gbt_32151_34_2024",
            applicable_standard_ids=("gbt_32151_34_2024",),
            required_factor_id="heat_default_2025",
            description="炭素材料生产标准沿用实测优先、无实测采用 0.11 的通则规则。",
        ),
    )
    return common, industry
