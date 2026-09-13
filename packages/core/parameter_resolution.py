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
        if self.blocked:
            first = next(problem for problem in self.warnings if problem.level is IssueLevel.ERROR)
            raise DomainValidationError(
                f"blocked parameter resolution cannot be snapshotted: {first.code}"
            )
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


_NONFOSSIL_ELECTRICITY_TYPES = frozenset(
    {
        "nonfossil",
        "marketized_nonfossil",
        "self_consumed_nonfossil",
        "marketized_green",
        "self_consumed_green",
    }
)
_NONFOSSIL_PROOF_VALUES = frozenset(
    {
        "provided",
        "contract",
        "settlement",
        "gec",
        "self_consumption_monthly_record",
    }
)


def _is_nonfossil_context(context: ParameterResolutionContext) -> bool:
    return context.electricity_type in _NONFOSSIL_ELECTRICITY_TYPES


def _has_nonfossil_proof(context: ParameterResolutionContext) -> bool:
    values = dict(context.extra_context)
    proof = values.get("nonfossil_proof") or values.get("green_power_proof")
    return proof in _NONFOSSIL_PROOF_VALUES


def _is_nonfossil_zero_factor(factor: Factor) -> bool:
    return (
        factor.value == 0
        and factor.value_type is ValueType.STANDARD_SPECIFIED
        and factor.source_id is not None
        and factor.source_location is not None
        and "附录D.1.1" in factor.source_location
    )


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
        required_factor_match = bool(rule and factor.factor_id in rule.required_factor_id_set)
        if required_factor_match and policy is ParameterSelectionPolicy.STANDARD_REQUIRED:
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
            # The rule may identify the mapped parameter, but it must never
            # freeze one old factor.  Applicability was filtered before this
            # method; among valid official candidates, the newest year wins.
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
        # Coverage/specialization rules may cover several parameter paths without
        # carrying a selection policy of their own.  Keep the explicit parameter
        # selection policy in the same effective set when one is available.
        policy_rules = [item for item in rules if item.selection_policy is not None]
        if not policy_rules:
            inherited_ids = set(effective.inherited_rule_ids)
            policy_rules = [
                item
                for item in effective.considered_rules
                if item.rule_id in inherited_ids
                and context.parameter_id in item.parameter_ids
                and item.selection_policy is not None
            ]
        rule = policy_rules[0] if policy_rules else (rules[0] if rules else None)
        policy = rule.selection_policy if rule and rule.selection_policy else ParameterSelectionPolicy.NO_AUTOMATIC_SELECTION
        factors = self._collect_factors(context)
        if _is_nonfossil_context(context):
            if not _has_nonfossil_proof(context):
                problems.append(
                    self._problem(
                        "GEN-VAL-NONFOSSIL-EVIDENCE",
                        IssueLevel.ERROR,
                        "采用非化石电力零因子前必须提供 GB/T 32151.34—2024 附录 D.2 证明文件。",
                        context.parameter_id,
                    )
                )
                factors = ()
            else:
                factors = tuple(factor for factor in factors if _is_nonfossil_zero_factor(factor))
                if not factors:
                    problems.append(
                        self._problem(
                            "GEN-VAL-NONFOSSIL-EVIDENCE",
                            IssueLevel.ERROR,
                            "非化石电力证明已提供，但当前 Canonical 因子库没有附录 D.1.1 的有来源零因子。",
                            context.parameter_id,
                        )
                    )

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
            if effective.blocked:
                problems.append(
                    self._problem(
                        "GEN-PAR-CONFLICT-BLOCKED",
                        IssueLevel.ERROR,
                        "当前规则集存在未解决冲突，即使用户已确认候选值也不能形成推荐快照。",
                        context.parameter_id,
                    )
                )
            elif not context.confirmation_reason:
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


def _frozen_rule(
    rule_id: str,
    rule_domain: str,
    relation: RuleRelation,
    description: str,
    *,
    standard_id: str,
    applicable_standard_ids: tuple[str, ...],
    target_id: str | None = None,
    parameter_id: str | None = None,
    parameter_ids: tuple[str, ...] = (),
    parameter_types: tuple[ParameterType, ...] = (),
    selection_policy: ParameterSelectionPolicy | None = None,
    required_factor_ids: tuple[str, ...] = (),
    priority: int = 100,
    origin: RuleOrigin = RuleOrigin.STANDARD_EXPLICIT,
    evidence_status: RuleEvidenceStatus = RuleEvidenceStatus.VERIFIED,
    supersedes_rule_ids: tuple[str, ...] = (),
    conflict_resolved: bool = False,
    resolution_reason: str | None = None,
    payload: tuple[tuple[str, str], ...] = (),
    conditions: tuple[tuple[str, str], ...] = (),
    source_location: str,
    evidence_source_id: str,
    confirmation_id: str | None = None,
) -> RuleDefinition:
    return RuleDefinition(
        rule_id=rule_id,
        rule_domain=rule_domain,
        target_id=target_id,
        parameter_id=parameter_id,
        relation=relation,
        description=description,
        standard_id=standard_id,
        applicability=RuleApplicability(
            standard_ids=applicable_standard_ids,
            parameter_types=parameter_types,
            conditions=conditions,
        ),
        priority=priority,
        origin=origin,
        evidence_status=evidence_status,
        supersedes_rule_ids=supersedes_rule_ids,
        conflict_resolved=conflict_resolved,
        resolution_reason=resolution_reason,
        selection_policy=selection_policy,
        required_factor_ids=required_factor_ids,
        applies_to_parameter_ids=parameter_ids,
        payload=payload,
        source_location=source_location,
        evidence_source_id=evidence_source_id,
        confirmation_id=confirmation_id,
    )


def _parameter_rule(
    rule_id: str,
    parameter_ids: tuple[str, ...],
    policy: ParameterSelectionPolicy,
    *,
    relation: RuleRelation,
    standard_id: str,
    applicable_standard_ids: tuple[str, ...],
    parameter_types: tuple[ParameterType, ...],
    required_factor_ids: tuple[str, ...] = (),
    target_id: str,
    priority: int = 100,
    description: str,
    source_location: str,
    evidence_source_id: str,
) -> RuleDefinition:
    return _frozen_rule(
        rule_id,
        "parameter_selection",
        relation,
        description,
        standard_id=standard_id,
        applicable_standard_ids=applicable_standard_ids,
        target_id=target_id,
        parameter_id=parameter_ids[0] if len(parameter_ids) == 1 else None,
        parameter_ids=parameter_ids,
        parameter_types=parameter_types,
        selection_policy=policy,
        required_factor_ids=required_factor_ids,
        priority=priority,
        source_location=source_location,
        evidence_source_id=evidence_source_id,
    )


def default_g05_rules() -> tuple[tuple[RuleDefinition, ...], tuple[RuleDefinition, ...]]:
    """Return the frozen common and carbon-material G05 rule sets."""

    common_ids = ("gbt_32150_2025", "gbt_32151_34_2024")
    carbon_ids = ("gbt_32151_34_2024",)
    common_source = "EVID-32150-PDF-2025-LOCAL"
    carbon_source = "EVID-32151-34-PDF-2024-LOCAL"

    common = (
        _frozen_rule("GEN-RULE-REFERENCE-MODE-001", "reference_mode", RuleRelation.BASE, "通则引用模式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="reference.mode",
            source_location="GB/T 32150—2025 第2条；PDF7；印刷页1", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-INDUSTRY-DELEGATION-001", "scope", RuleRelation.BASE, "未覆盖活动转交适用行业标准。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="industry.delegation",
            source_location="GB/T 32150—2025 第7.5.4条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-GHG-SCOPE-001", "scope", RuleRelation.BASE, "通则温室气体范围。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="ghg.scope",
            source_location="GB/T 32150—2025 第3.1、6条；PDF7、11；印刷页1、5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BOUNDARY-ENTITY-001", "boundary", RuleRelation.BASE, "企业实体边界。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.entity",
            source_location="GB/T 32150—2025 第3.2条；PDF7；印刷页1", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BOUNDARY-SYSTEMS-001", "boundary", RuleRelation.BASE, "生产系统边界。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.systems",
            source_location="GB/T 32150—2025 第6条；PDF10～11；印刷页4～5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BOUNDARY-AUXILIARY-001", "boundary", RuleRelation.BASE, "辅助生产系统边界。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.auxiliary",
            source_location="GB/T 32150—2025 第6条；PDF10～11；印刷页4～5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BOUNDARY-ANCILLARY-001", "boundary", RuleRelation.BASE, "附属生产系统边界。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.ancillary",
            source_location="GB/T 32150—2025 第6条；PDF10～11；印刷页4～5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BOUNDARY-INCLUDED-SOURCES-001", "boundary", RuleRelation.BASE, "纳入排放源清单。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.included_sources",
            source_location="GB/T 32150—2025 第6条；PDF11；印刷页5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-BIOMASS-001", "boundary", RuleRelation.BASE, "生物质排放单列。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.biomass",
            source_location="GB/T 32150—2025 第6条；PDF11；印刷页5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-REMOVAL-001", "boundary", RuleRelation.BASE, "移除量单列。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="boundary.removal",
            source_location="GB/T 32150—2025 第6条；PDF11；印刷页5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-ACTIVITY-PRIMARY-001", "activity", RuleRelation.BASE, "原始活动数据优先并保留测量证据。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="activity.primary",
            source_location="GB/T 32150—2025 表2；PDF14；印刷页8", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-ACTIVITY-SECONDARY-001", "activity", RuleRelation.BASE, "二次活动数据须记录折算方法。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="activity.secondary",
            source_location="GB/T 32150—2025 表2-3；PDF14；印刷页8", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-ACTIVITY-PROXY-001", "activity", RuleRelation.BASE, "替代活动数据须保留相似过程依据。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="activity.proxy",
            source_location="GB/T 32150—2025 表2；PDF14；印刷页8", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001", "execution", RuleRelation.BASE, "逸散排放执行路径阻断。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="fugitive.execution",
            origin=RuleOrigin.SOFTWARE_DERIVED, payload=(("decision", "SM01-DECISION-001"),),
            source_location="SM01-DECISION-001；GB/T 32150—2025 第7.5.5条；PDF15～16；印刷页9～10",
            evidence_source_id="SM01-DECISION-001", confirmation_id="SM01-DECISION-001"),
        _frozen_rule("GEN-RULE-TOTAL-COVERAGE-REQUIRED-001", "aggregation", RuleRelation.BASE, "总量必须覆盖应计排放源。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="total.coverage",
            origin=RuleOrigin.SOFTWARE_DERIVED, payload=(("decision", "SM01-DECISION-005"),),
            source_location="SM01-DECISION-005；GB/T 32150—2025 第7.5.8条；PDF16～17；印刷页10～11",
            evidence_source_id="SM01-DECISION-005", confirmation_id="SM01-DECISION-005"),
        _frozen_rule("GEN-MTH-FACTOR-001", "method", RuleRelation.BASE, "排放因子法。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="method.fuel",
            source_location="GB/T 32150—2025 第7.2.2条；PDF13；印刷页7", evidence_source_id=common_source),
        _frozen_rule("GEN-MTH-MATERIAL-BALANCE-001", "method", RuleRelation.BASE, "物料平衡法。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="method.process",
            source_location="GB/T 32150—2025 第7.2.3条；PDF13；印刷页7", evidence_source_id=common_source),
        _frozen_rule("GEN-MTH-MEASURED-001", "method", RuleRelation.BASE, "直接测量法。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="method.measured",
            source_location="GB/T 32150—2025 第7.2.4条；PDF13；印刷页7", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-FACTOR-001", "formula", RuleRelation.BASE, "排放因子法公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.factor",
            source_location="GB/T 32150—2025 第7.2.2条；PDF13；印刷页7", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-MATERIAL-BALANCE-001", "formula", RuleRelation.BASE, "物料平衡法公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.material_balance",
            source_location="GB/T 32150—2025 第7.2.3条；PDF13；印刷页7", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-FUEL-AGG-001", "formula", RuleRelation.BASE, "燃料排放聚合公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.fuel_aggregation",
            source_location="GB/T 32150—2025 第7.5.2条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-FUGITIVE-AGG-001", "execution", RuleRelation.CONFLICT_REVIEW, "逸散聚合公式待复核。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="fugitive.execution",
            priority=-10, evidence_status=RuleEvidenceStatus.CONFLICT,
            source_location="GB/T 32150—2025 第7.5.5条；PDF15～16；印刷页9～10；PENDING-GEN-001",
            evidence_source_id=common_source),
        _frozen_rule("GEN-FML-PROCESS-AGG-001", "formula", RuleRelation.BASE, "过程排放聚合公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.process_aggregation",
            source_location="GB/T 32150—2025 第7.5.3条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-WASTE-AGG-001", "formula", RuleRelation.BASE, "废弃物排放聚合公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.waste_aggregation",
            source_location="GB/T 32150—2025 第7.5.4条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-PURCHASED-ELECTRICITY-001", "formula", RuleRelation.BASE, "外购电力公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.purchased_electricity",
            source_location="GB/T 32150—2025 第7.5.6条；PDF16；印刷页10", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-PURCHASED-HEAT-001", "formula", RuleRelation.BASE, "外购热力公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.purchased_heat",
            source_location="GB/T 32150—2025 第7.5.6条；PDF16；印刷页10", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-TOTAL-001", "formula", RuleRelation.BASE, "通则总量公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="total.formula",
            source_location="GB/T 32150—2025 第7.5.8条；PDF16～17；印刷页10～11", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-TOTAL-001", "formula", RuleRelation.CONFLICT_REVIEW, "总量公式适用关系待行业覆盖确认。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="total.formula",
            priority=-10, evidence_status=RuleEvidenceStatus.CONFLICT,
            source_location="GB/T 32150—2025 第7.5.8条；PDF16～17；印刷页10～11；PENDING-GEN-002",
            evidence_source_id=common_source),
        _frozen_rule("GEN-FML-EXPORTED-ELECTRICITY-001", "formula", RuleRelation.BASE, "外供电力公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.exported_electricity",
            source_location="GB/T 32150—2025 第7.5.7条；PDF16；印刷页10", evidence_source_id=common_source),
        _frozen_rule("GEN-FML-EXPORTED-HEAT-001", "formula", RuleRelation.BASE, "外供热力公式。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="formula.exported_heat",
            source_location="GB/T 32150—2025 第7.5.7条；PDF16；印刷页10", evidence_source_id=common_source),
        _frozen_rule("GEN-AGG-FUEL-ADD", "aggregation", RuleRelation.BASE, "燃料加总。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="aggregation.fuel",
            source_location="GB/T 32150—2025 第7.5.2条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-AGG-PROCESS-ADD", "aggregation", RuleRelation.BASE, "过程加总。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="aggregation.process",
            source_location="GB/T 32150—2025 第7.5.3条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-AGG-WASTE-ADD", "aggregation", RuleRelation.BASE, "废弃物加总。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="aggregation.waste",
            source_location="GB/T 32150—2025 第7.5.4条；PDF15；印刷页9", evidence_source_id=common_source),
        _frozen_rule("GEN-AGG-FUGITIVE-REVIEW-001", "execution", RuleRelation.CONFLICT_REVIEW, "逸散聚合待复核。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="fugitive.execution",
            priority=-10, evidence_status=RuleEvidenceStatus.CONFLICT,
            source_location="GB/T 32150—2025 第7.5.5条；PDF15～16；印刷页9～10；PENDING-GEN-001",
            evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-FACTOR-PRIORITY-001", "parameter_selection", RuleRelation.BASE, "因子适用优先级。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="factor.priority",
            source_location="GB/T 32150—2025 第7.4条；PDF14～15；印刷页8～9", evidence_source_id=common_source),
        _parameter_rule("GEN-RULE-ELECTRICITY-001", ("electricity_emission_factor_national",),
            ParameterSelectionPolicy.OFFICIAL_LATEST, relation=RuleRelation.BASE, standard_id="gbt_32150_2025",
            applicable_standard_ids=common_ids, parameter_types=(ParameterType.ELECTRICITY_EMISSION_FACTOR,),
            target_id="electricity_emission_factor_national", description="最新适用官方电力因子。",
            source_location="GB/T 32150—2025 第7.5.6～7.5.7条；参数 GEN-PAR-ELECTRICITY-NATIONAL-LATEST",
            evidence_source_id=common_source),
        _parameter_rule("GEN-RULE-HEAT-001", ("heat_emission_factor_default",),
            ParameterSelectionPolicy.MEASURED_FIRST, relation=RuleRelation.BASE, standard_id="gbt_32150_2025",
            applicable_standard_ids=common_ids, parameter_types=(ParameterType.HEAT_EMISSION_FACTOR,),
            required_factor_ids=("heat_default_2025",), target_id="heat_emission_factor_default",
            description="热力实测优先，缺省值为 0.11 tCO2/GJ。",
            source_location="GB/T 32150—2025 第7.5.6～7.5.7条；参数 GEN-PAR-HEAT-DEFAULT-011",
            evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-PRINCIPLE-001", "governance", RuleRelation.BASE, "通则核算原则。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="principle.core",
            source_location="GB/T 32150—2025 PDF9；印刷页3", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-SOURCE-CATALOG-001", "source_catalog", RuleRelation.BASE, "通则公共排放源分类。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="source.catalog",
            source_location="GB/T 32150—2025 第6条；PDF11；印刷页5", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-WORKFLOW-001", "workflow", RuleRelation.BASE, "通则核算工作流程。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="workflow.accounting",
            source_location="GB/T 32150—2025 PDF9～10；印刷页3～4", evidence_source_id=common_source),
        _frozen_rule("GEN-RULE-QA-001", "quality", RuleRelation.BASE, "通则质量保证。",
            standard_id="gbt_32150_2025", applicable_standard_ids=common_ids, target_id="quality.assurance",
            source_location="GB/T 32150—2025 第8条；PDF17～18；印刷页11～12", evidence_source_id=common_source),

    )

    industry = (
        _frozen_rule("CAR-RULE-GHG-SCOPE-001", "scope", RuleRelation.SPECIALIZE, "炭素材料温室气体范围。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="ghg.scope",
            source_location="GB/T 32151.34—2024 第3.1条；PDF9；印刷页1", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-BOUNDARY-001", "boundary", RuleRelation.SPECIALIZE, "炭素材料生产系统边界。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="boundary.systems",
            source_location="GB/T 32151.34—2024 第5.1、5.2条；PDF11～15；印刷页3～7", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-FUEL-001", "method", RuleRelation.SPECIALIZE, "炭素材料天然气参数直接规定值。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="method.fuel",
            parameter_ids=("natural_gas_lhv", "natural_gas_carbon_content", "natural_gas_oxidation_rate"),
            selection_policy=ParameterSelectionPolicy.STANDARD_REQUIRED,
            required_factor_ids=("natural_gas_lhv_gbt32151_34_c1", "natural_gas_carbon_content_gbt32151_34_c1",
                "natural_gas_oxidation_rate_gbt32151_34_c1"),
            payload=(("mapping_parameters", "GEN-PAR-NATURAL-GAS-LHV|GEN-PAR-NATURAL-GAS-CARBON|GEN-PAR-NATURAL-GAS-OXIDATION"),),
            source_location="GB/T 32151.34—2024 第5.2.1条；附录C；PDF12；印刷页4", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-PROCESS-001", "method", RuleRelation.SPECIALIZE, "炭素材料过程排放方法。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="method.process",
            source_location="GB/T 32151.34—2024 第5.2.2～5.2.5条；PDF12～14；印刷页4～6", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-POWER-HEAT-001", "parameter_selection", RuleRelation.SPECIALIZE,
            "炭素材料外购电力和热力分别沿用各自适用的参数选择路径。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="power_heat",
            parameter_ids=("electricity_emission_factor_national", "heat_emission_factor_default"),
            parameter_types=(ParameterType.ELECTRICITY_EMISSION_FACTOR, ParameterType.HEAT_EMISSION_FACTOR),
            payload=(("specializes", "GEN-RULE-ELECTRICITY-001|GEN-RULE-HEAT-001"),),
            source_location="GB/T 32151.34—2024 第5.2.6条；PDF15；印刷页7", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-TOTAL-001", "formula", RuleRelation.OVERRIDE, "炭素材料总量公式覆盖通则路径。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="total.formula", priority=300,
            supersedes_rule_ids=("GEN-RULE-TOTAL-001", "GEN-FML-TOTAL-001"),
            source_location="GB/T 32151.34—2024 第5.2.7条；PDF15～16；印刷页7～8", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-TOTAL-COVERAGE-001", "aggregation", RuleRelation.OVERRIDE, "炭素材料总量覆盖。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="total.coverage", priority=300,
            supersedes_rule_ids=("GEN-RULE-TOTAL-COVERAGE-REQUIRED-001",),
            source_location="GB/T 32151.34—2024 第5.2.7.1～5.2.7.3条；PDF15～16；印刷页7～8", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-FUGITIVE-COVERAGE-001", "execution", RuleRelation.OVERRIDE, "炭素材料逸散排放行业覆盖。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="fugitive.execution", priority=300,
            supersedes_rule_ids=("GEN-RULE-FUGITIVE-EXECUTION-BLOCK-001", "GEN-FML-FUGITIVE-AGG-001",
                "GEN-AGG-FUGITIVE-REVIEW-001"), origin=RuleOrigin.SOFTWARE_DERIVED,
            payload=(("decision", "SM01-DECISION-001"),),
            source_location="GB/T 32151.34—2024 第4.2、5.2条；SM01-DECISION-001",
            evidence_source_id="SM01-DECISION-001", confirmation_id="SM01-DECISION-001"),
        _frozen_rule("CAR-RULE-NONFOSSIL-POWER-001", "parameter_selection", RuleRelation.OVERRIDE,
            "非化石能源电力按行业附录要求覆盖通则电力因子路径。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids,
            target_id="electricity_emission_factor_national", parameter_id="electricity_emission_factor_national",
            parameter_types=(ParameterType.ELECTRICITY_EMISSION_FACTOR,),
            selection_policy=ParameterSelectionPolicy.STANDARD_REQUIRED, priority=300,
            supersedes_rule_ids=("GEN-RULE-ELECTRICITY-001",),
            conditions=(("electricity_type", "nonfossil"),),
            source_location="GB/T 32151.34—2024 附录D.1.1、附录D.2；PDF22；印刷页20", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-QA-001", "quality", RuleRelation.EXTEND, "炭素材料质量要求补充。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="quality.assurance",
            source_location="GB/T 32151.34—2024 第6条；PDF16～18；印刷页8～10", evidence_source_id=carbon_source),
        _frozen_rule("CAR-RULE-REPORT-001", "reporting", RuleRelation.EXTEND, "炭素材料报告要求补充。",
            standard_id="gbt_32151_34_2024", applicable_standard_ids=carbon_ids, target_id="reporting.result",
            source_location="GB/T 32151.34—2024 第7条；PDF18～20；印刷页10～12", evidence_source_id=carbon_source),
    )
    return common, industry
