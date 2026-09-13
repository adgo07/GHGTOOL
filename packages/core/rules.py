"""Platform-independent rule inheritance and conflict resolution for G05.

The resolver deliberately works on immutable rule records and an explicit
context.  It does not know about Qt, SQLite, or any particular calculation
page.  An industry rule can specialize or override a common rule while the
provenance of the common rule remains available in the effective result.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Iterable

from .errors import DomainValidationError, IssueLevel, ValidationProblem, contains_errors
from .models import (
    AccountingPeriod,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ParameterType,
)


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")


def _require_token(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _TOKEN_PATTERN.fullmatch(value):
        raise DomainValidationError(f"{field_name} must be a stable identifier")
    return value


def _optional_token(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_token(value, field_name)


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} is required")
    return value.strip()


def _optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _texts(values: tuple[str, ...] | list[str] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise DomainValidationError(f"{field_name} must be a sequence of text")
    normalized = tuple(values)
    for value in normalized:
        _require_text(value, field_name)
    if len(set(normalized)) != len(normalized):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return normalized


def _tokens(values: tuple[str, ...] | list[str] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise DomainValidationError(f"{field_name} must be a sequence of stable identifiers")
    normalized = tuple(values)
    for value in normalized:
        _require_token(value, field_name)
    if len(set(normalized)) != len(normalized):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return normalized


def _pairs(values: tuple[tuple[str, str], ...] | list[tuple[str, str]] | None, field_name: str) -> tuple[tuple[str, str], ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise DomainValidationError(f"{field_name} must be key/value pairs")
    normalized = tuple(values)
    for key, value in normalized:
        _require_token(key, f"{field_name} key")
        if not isinstance(value, str):
            raise DomainValidationError(f"{field_name} values must be text")
    if len({key for key, _ in normalized}) != len(normalized):
        raise DomainValidationError(f"{field_name} keys must be unique")
    return normalized


class RuleRelation(str, Enum):
    """The only rule inheritance relations allowed by the frozen mapping."""

    BASE = "BASE"
    SPECIALIZE = "SPECIALIZE"
    OVERRIDE = "OVERRIDE"
    EXTEND = "EXTEND"
    SUPPLEMENT = "SUPPLEMENT"
    CONFLICT_REVIEW = "CONFLICT_REVIEW"


class RuleOrigin(str, Enum):
    STANDARD_EXPLICIT = "STANDARD_EXPLICIT"
    SOFTWARE_DERIVED = "SOFTWARE_DERIVED"
    CONFIRMED_CORRECTION = "CONFIRMED_CORRECTION"


class RuleEvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"


class ParameterSelectionPolicy(str, Enum):
    """Typed selection policies used by the parameter resolver."""

    STANDARD_REQUIRED = "STANDARD_REQUIRED"
    MEASURED_FIRST = "MEASURED_FIRST"
    OFFICIAL_LATEST = "OFFICIAL_LATEST"
    SYSTEM_GWP = "SYSTEM_GWP"
    NO_AUTOMATIC_SELECTION = "NO_AUTOMATIC_SELECTION"


@dataclass(frozen=True, slots=True)
class RuleContext:
    """Context used to decide whether a rule is applicable."""

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
    electricity_acquisition_mode: ElectricityAcquisitionMode | None = None
    electricity_attribute: ElectricityAttribute | None = None
    reporting_framework: str | None = None
    extra_context: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _optional_token(self.standard_id, "standard_id")
        _optional_text(self.region, "region")
        _optional_text(self.industry, "industry")
        _optional_token(self.subject_id, "subject_id")
        if self.parameter_type is not None and not isinstance(self.parameter_type, ParameterType):
            raise DomainValidationError("parameter_type must be a ParameterType")
        _optional_token(self.emission_source_type, "emission_source_type")
        _optional_token(self.greenhouse_gas, "greenhouse_gas")
        _optional_text(self.electricity_type, "electricity_type")
        _optional_text(self.electricity_accounting_mode, "electricity_accounting_mode")
        if self.electricity_acquisition_mode is not None and not isinstance(self.electricity_acquisition_mode, ElectricityAcquisitionMode):
            raise DomainValidationError("electricity_acquisition_mode must be an ElectricityAcquisitionMode")
        if self.electricity_attribute is not None and not isinstance(self.electricity_attribute, ElectricityAttribute):
            raise DomainValidationError("electricity_attribute must be an ElectricityAttribute")
        _optional_text(self.reporting_framework, "reporting_framework")
        object.__setattr__(self, "extra_context", _pairs(self.extra_context, "extra_context"))


@dataclass(frozen=True, slots=True)
class RuleApplicability:
    """Structured applicability constraints; empty fields mean any value."""

    standard_ids: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    industries: tuple[str, ...] = ()
    subject_ids: tuple[str, ...] = ()
    parameter_types: tuple[ParameterType, ...] = ()
    emission_source_types: tuple[str, ...] = ()
    greenhouse_gases: tuple[str, ...] = ()
    period_from: date | None = None
    period_to: date | None = None
    conditions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "standard_ids", _tokens(self.standard_ids, "standard_ids"))
        object.__setattr__(self, "regions", _texts(self.regions, "regions"))
        object.__setattr__(self, "industries", _texts(self.industries, "industries"))
        object.__setattr__(self, "subject_ids", _tokens(self.subject_ids, "subject_ids"))
        object.__setattr__(self, "emission_source_types", _tokens(self.emission_source_types, "emission_source_types"))
        object.__setattr__(self, "greenhouse_gases", _tokens(self.greenhouse_gases, "greenhouse_gases"))
        if any(not isinstance(value, ParameterType) for value in self.parameter_types):
            raise DomainValidationError("parameter_types must contain ParameterType values")
        if self.period_from and self.period_to and self.period_to < self.period_from:
            raise DomainValidationError("rule applicability dates are out of order")
        object.__setattr__(self, "conditions", _pairs(self.conditions, "conditions"))

    @staticmethod
    def _matches(value: str | None, accepted: tuple[str, ...]) -> bool:
        return not accepted or (value is not None and value in accepted)

    def matches(self, context: RuleContext) -> bool:
        if self.standard_ids and context.standard_id not in self.standard_ids:
            return False
        if not self._matches(context.region, self.regions):
            return False
        if not self._matches(context.industry, self.industries):
            return False
        if not self._matches(context.subject_id, self.subject_ids):
            return False
        if self.parameter_types and context.parameter_type not in self.parameter_types:
            return False
        if not self._matches(context.emission_source_type, self.emission_source_types):
            return False
        if not self._matches(context.greenhouse_gas, self.greenhouse_gases):
            return False
        period = context.accounting_period
        if self.period_from and (period is None or period.end < self.period_from):
            return False
        if self.period_to and (period is None or period.start > self.period_to):
            return False
        context_values = dict(context.extra_context)
        context_values.update(
            {
                "standard_id": context.standard_id,
                "region": context.region,
                "industry": context.industry,
                "subject_id": context.subject_id,
                "parameter_type": context.parameter_type.value if context.parameter_type else None,
                "emission_source_type": context.emission_source_type,
                "greenhouse_gas": context.greenhouse_gas,
                "electricity_type": context.electricity_type,
                "electricity_accounting_mode": context.electricity_accounting_mode,
                "electricity_acquisition_mode": context.electricity_acquisition_mode.value if context.electricity_acquisition_mode else None,
                "electricity_attribute": context.electricity_attribute.value if context.electricity_attribute else None,
                "reporting_framework": context.reporting_framework,
            }
        )
        for key, value in self.conditions:
            actual = context_values.get(key)
            if key == "electricity_attribute" and value == ElectricityAttribute.NONFOSSIL.value:
                if actual != ElectricityAttribute.NONFOSSIL.value:
                    return False
            elif key == "electricity_type" and value == "nonfossil":
                if actual not in {
                    "nonfossil",
                    "marketized_nonfossil",
                    "self_consumed_nonfossil",
                    "marketized_green",
                    "self_consumed_green",
                }:
                    return False
            elif actual != value:
                return False
        return True


@dataclass(frozen=True, slots=True)
class RuleDefinition:
    """One immutable rule record from the common or industry rule set."""

    rule_id: str
    rule_domain: str
    relation: RuleRelation
    description: str
    standard_id: str | None = None
    target_id: str | None = None
    applicability: RuleApplicability = RuleApplicability()
    priority: int = 0
    origin: RuleOrigin = RuleOrigin.STANDARD_EXPLICIT
    evidence_status: RuleEvidenceStatus = RuleEvidenceStatus.VERIFIED
    supersedes_rule_ids: tuple[str, ...] = ()
    conflict_resolved: bool = False
    resolution_reason: str | None = None
    parameter_id: str | None = None
    selection_policy: ParameterSelectionPolicy | None = None
    required_factor_id: str | None = None
    required_factor_version: str | None = None
    payload: tuple[tuple[str, str], ...] = ()
    applies_to_parameter_ids: tuple[str, ...] = ()
    required_factor_ids: tuple[str, ...] = ()
    source_location: str | None = None
    evidence_source_id: str | None = None
    confirmation_id: str | None = None

    def __post_init__(self) -> None:
        _require_token(self.rule_id, "rule_id")
        _require_token(self.rule_domain, "rule_domain")
        _require_text(self.description, "description")
        if not isinstance(self.relation, RuleRelation):
            raise DomainValidationError("relation must be a RuleRelation")
        if not isinstance(self.origin, RuleOrigin):
            raise DomainValidationError("origin must be a RuleOrigin")
        if not isinstance(self.evidence_status, RuleEvidenceStatus):
            raise DomainValidationError("evidence_status must be a RuleEvidenceStatus")
        _optional_token(self.standard_id, "standard_id")
        _optional_token(self.target_id, "target_id")
        _optional_token(self.parameter_id, "parameter_id")
        _optional_token(self.required_factor_id, "required_factor_id")
        _optional_token(self.required_factor_version, "required_factor_version")
        _optional_token(self.evidence_source_id, "evidence_source_id")
        _optional_token(self.confirmation_id, "confirmation_id")
        _optional_text(self.source_location, "source_location")
        if not isinstance(self.priority, int):
            raise DomainValidationError("rule priority must be an integer")
        if self.selection_policy is not None and not isinstance(self.selection_policy, ParameterSelectionPolicy):
            raise DomainValidationError("selection_policy must be a ParameterSelectionPolicy")
        object.__setattr__(self, "supersedes_rule_ids", _tokens(self.supersedes_rule_ids, "supersedes_rule_ids"))
        object.__setattr__(self, "payload", _pairs(self.payload, "payload"))
        object.__setattr__(
            self,
            "applies_to_parameter_ids",
            _tokens(self.applies_to_parameter_ids, "applies_to_parameter_ids"),
        )
        object.__setattr__(self, "required_factor_ids", _tokens(self.required_factor_ids, "required_factor_ids"))
        if self.relation is RuleRelation.CONFLICT_REVIEW and self.conflict_resolved:
            if not self.resolution_reason or not self.resolution_reason.strip():
                raise DomainValidationError("a resolved conflict requires resolution_reason")
        if self.resolution_reason is not None:
            _require_text(self.resolution_reason, "resolution_reason")

    @property
    def group_key(self) -> tuple[str, str]:
        return self.rule_domain, self.target_id or self.parameter_id or ""

    @property
    def parameter_ids(self) -> tuple[str, ...]:
        """Parameter IDs covered by this rule, including legacy singular data."""

        values = list(self.applies_to_parameter_ids)
        if self.parameter_id is not None and self.parameter_id not in values:
            values.insert(0, self.parameter_id)
        return tuple(values)

    @property
    def required_factor_id_set(self) -> frozenset[str]:
        values = set(self.required_factor_ids)
        if self.required_factor_id is not None:
            values.add(self.required_factor_id)
        return frozenset(values)

    def matches(self, context: RuleContext) -> bool:
        return self.applicability.matches(context)


class RuleResolutionAction(str, Enum):
    SELECTED = "SELECTED"
    INHERITED = "INHERITED"
    SUPPLEMENTED = "SUPPLEMENTED"
    OVERRIDDEN = "OVERRIDDEN"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"


@dataclass(frozen=True, slots=True)
class RuleResolutionTrace:
    rule_id: str
    action: RuleResolutionAction
    reason: str

    def __post_init__(self) -> None:
        _require_token(self.rule_id, "rule_id")
        if not isinstance(self.action, RuleResolutionAction):
            raise DomainValidationError("action must be a RuleResolutionAction")
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class EffectiveRuleSet:
    """Resolved rules plus provenance and blocking validation problems."""

    context: RuleContext
    rules: tuple[RuleDefinition, ...]
    considered_rules: tuple[RuleDefinition, ...]
    traces: tuple[RuleResolutionTrace, ...]
    overridden_rule_ids: tuple[str, ...] = ()
    problems: tuple[ValidationProblem, ...] = ()

    def __post_init__(self) -> None:
        rules = tuple(self.rules)
        considered = tuple(self.considered_rules)
        if len({rule.rule_id for rule in considered}) != len(considered):
            raise DomainValidationError("considered rule IDs must be unique")
        if len({rule.rule_id for rule in rules}) != len(rules):
            raise DomainValidationError("effective rule IDs must be unique")
        if any(not isinstance(problem, ValidationProblem) for problem in self.problems):
            raise DomainValidationError("rule problems must be ValidationProblem instances")
        object.__setattr__(self, "rules", rules)
        object.__setattr__(self, "considered_rules", considered)
        object.__setattr__(self, "traces", tuple(self.traces))
        object.__setattr__(self, "overridden_rule_ids", _tokens(self.overridden_rule_ids, "overridden_rule_ids"))
        object.__setattr__(self, "problems", tuple(self.problems))

    @property
    def blocked(self) -> bool:
        return contains_errors(self.problems)

    @property
    def is_resolved(self) -> bool:
        return not self.blocked

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self.rules)

    @property
    def inherited_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            trace.rule_id
            for trace in self.traces
            if trace.action is RuleResolutionAction.INHERITED
        )

    def rules_for_parameter(self, parameter_id: str) -> tuple[RuleDefinition, ...]:
        _require_token(parameter_id, "parameter_id")
        return tuple(rule for rule in self.rules if parameter_id in rule.parameter_ids)

    def ensure_resolved(self) -> None:
        if self.blocked:
            first = next(problem for problem in self.problems if problem.blocks_record)
            raise DomainValidationError(first.message)


class EffectiveRuleResolver:
    """Resolve common and industry rules without mutating either input set."""

    @staticmethod
    def _choose(
        candidates: Iterable[RuleDefinition],
        problems: list[ValidationProblem],
        group_key: tuple[str, str],
    ) -> RuleDefinition | None:
        ordered = sorted(candidates, key=lambda rule: (-rule.priority, rule.rule_id))
        if not ordered:
            return None
        top_priority = ordered[0].priority
        top = [rule for rule in ordered if rule.priority == top_priority]
        if len(top) > 1:
            problems.append(
                ValidationProblem(
                    "GEN-RULE-AMBIGUOUS",
                    IssueLevel.ERROR,
                    f"多个规则以相同优先级竞争 {group_key[0]}:{group_key[1]}，需要明确覆盖关系。",
                    group_key[1] or group_key[0],
                )
            )
            return None
        return ordered[0]

    def resolve(
        self,
        common_rules: Iterable[RuleDefinition],
        industry_rules: Iterable[RuleDefinition],
        context: RuleContext,
    ) -> EffectiveRuleSet:
        common = tuple(rule for rule in common_rules if rule.matches(context))
        industry = tuple(rule for rule in industry_rules if rule.matches(context))
        considered = tuple(sorted((*common, *industry), key=lambda rule: rule.rule_id))
        groups: dict[tuple[str, str], list[RuleDefinition]] = defaultdict(list)
        for rule in common:
            groups[rule.group_key].append(rule)
        for rule in industry:
            if rule.relation is RuleRelation.OVERRIDE and rule.supersedes_rule_ids:
                linked_groups = {
                    base.group_key
                    for base in common
                    if base.rule_id in set(rule.supersedes_rule_ids)
                }
                if linked_groups:
                    for group_key in linked_groups:
                        groups[group_key].append(rule)
                    continue
            if rule.relation is RuleRelation.SPECIALIZE and rule.parameter_ids:
                linked_groups = {
                    base.group_key
                    for base in common
                    if base.rule_domain == rule.rule_domain
                    and set(base.parameter_ids).intersection(rule.parameter_ids)
                }
                if linked_groups:
                    for group_key in linked_groups:
                        groups[group_key].append(rule)
                    continue
            groups[rule.group_key].append(rule)

        selected: list[RuleDefinition] = []
        traces: list[RuleResolutionTrace] = []
        overridden: set[str] = set()
        problems: list[ValidationProblem] = []

        for group_key in sorted(groups):
            group = groups[group_key]
            group_common = [rule for rule in group if rule in common]
            group_industry = [rule for rule in group if rule in industry]
            overrides = [rule for rule in group_industry if rule.relation is RuleRelation.OVERRIDE]
            specializations = [rule for rule in group_industry if rule.relation is RuleRelation.SPECIALIZE]
            extensions = [rule for rule in group_industry if rule.relation is RuleRelation.EXTEND]
            supplements = [rule for rule in group_industry if rule.relation is RuleRelation.SUPPLEMENT]

            if overrides:
                winner = self._choose(overrides, problems, group_key)
                if winner is not None:
                    common_ids = {base.rule_id for base in group_common}
                    requested_ids = set(winner.supersedes_rule_ids)
                    unknown_ids = requested_ids - common_ids
                    uncovered_ids = common_ids - requested_ids
                    valid_override = bool(requested_ids) and not unknown_ids and not uncovered_ids
                    if not requested_ids:
                        problems.append(
                            ValidationProblem(
                                "GEN-RULE-OVERRIDE-SUPERSEDES-MISSING",
                                IssueLevel.ERROR,
                                f"OVERRIDE {winner.rule_id} 必须明确列出 supersedes_rule_ids。",
                                winner.rule_id,
                            )
                        )
                    elif unknown_ids:
                        problems.append(
                            ValidationProblem(
                                "GEN-RULE-OVERRIDE-SUPERSEDES-UNKNOWN",
                                IssueLevel.ERROR,
                                f"OVERRIDE {winner.rule_id} 引用了不存在的通则规则：{', '.join(sorted(unknown_ids))}。",
                                winner.rule_id,
                            )
                        )
                    if uncovered_ids:
                        problems.append(
                            ValidationProblem(
                                "GEN-RULE-OVERRIDE-SUPERSEDES-INCOMPLETE",
                                IssueLevel.ERROR,
                                f"OVERRIDE {winner.rule_id} 未完整覆盖同组通则规则：{', '.join(sorted(uncovered_ids))}。",
                                winner.rule_id,
                            )
                        )

                    selected.append(winner)
                    traces.append(
                        RuleResolutionTrace(
                            winner.rule_id,
                            RuleResolutionAction.SELECTED,
                            "行业 OVERRIDE 明确替换通则规则。",
                        )
                    )
                    if valid_override:
                        for base in group_common:
                            overridden.add(base.rule_id)
                            traces.append(
                                RuleResolutionTrace(
                                    base.rule_id,
                                    RuleResolutionAction.OVERRIDDEN,
                                    f"被 {winner.rule_id} 明确覆盖。",
                                )
                            )
                    else:
                        # Invalid coverage must not silently discard BASE rules.
                        for base in sorted(group_common, key=lambda item: (-item.priority, item.rule_id)):
                            selected.append(base)
                            traces.append(
                                RuleResolutionTrace(
                                    base.rule_id,
                                    RuleResolutionAction.SELECTED,
                                    f"因 {winner.rule_id} 的覆盖声明无效，保留通则 BASE。",
                                )
                            )
            elif specializations:
                winner = self._choose(specializations, problems, group_key)
                if winner is not None:
                    selected.append(winner)
                    traces.append(
                        RuleResolutionTrace(
                            winner.rule_id,
                            RuleResolutionAction.SELECTED,
                            "行业 SPECIALIZE 具体化通则规则。",
                        )
                    )
                    for base in group_common:
                        traces.append(
                            RuleResolutionTrace(
                                base.rule_id,
                                RuleResolutionAction.INHERITED,
                                f"由 {winner.rule_id} 保留为通则依据。",
                            )
                        )
            elif extensions:
                for base in sorted(group_common, key=lambda rule: (-rule.priority, rule.rule_id)):
                    selected.append(base)
                    traces.append(
                        RuleResolutionTrace(base.rule_id, RuleResolutionAction.SELECTED, "保留通则 BASE 规则。")
                    )
                for extension in sorted(extensions, key=lambda rule: (-rule.priority, rule.rule_id)):
                    selected.append(extension)
                    traces.append(
                        RuleResolutionTrace(extension.rule_id, RuleResolutionAction.SELECTED, "行业 EXTEND 增加规则。")
                    )
            elif supplements:
                for base in sorted(group_common, key=lambda rule: (-rule.priority, rule.rule_id)):
                    selected.append(base)
                    traces.append(
                        RuleResolutionTrace(base.rule_id, RuleResolutionAction.SELECTED, "保留通则 BASE 规则。")
                    )
                for supplement in sorted(supplements, key=lambda rule: (-rule.priority, rule.rule_id)):
                    selected.append(supplement)
                    traces.append(
                        RuleResolutionTrace(
                            supplement.rule_id,
                            RuleResolutionAction.SUPPLEMENTED,
                            "行业 SUPPLEMENT 仅在没有明确行业覆盖时补充规则。",
                        )
                    )
            else:
                ordinary = [
                    rule
                    for rule in group
                    if rule.relation in {RuleRelation.BASE, RuleRelation.CONFLICT_REVIEW}
                ]
                winner = self._choose(ordinary, problems, group_key)
                if winner is not None:
                    selected.append(winner)
                    traces.append(
                        RuleResolutionTrace(winner.rule_id, RuleResolutionAction.SELECTED, "采用可用 BASE 规则。")
                    )

            for conflict in group:
                if conflict.relation is not RuleRelation.CONFLICT_REVIEW:
                    continue
                if conflict.conflict_resolved:
                    traces.append(
                        RuleResolutionTrace(
                            conflict.rule_id,
                            RuleResolutionAction.CONFLICT_RESOLVED,
                            conflict.resolution_reason or "冲突已由执行决策解决。",
                        )
                    )
                    continue
                if conflict.rule_id in overridden:
                    continue
                if (
                    overrides
                    and len(overrides) == 1
                    and conflict.rule_id in set(overrides[0].supersedes_rule_ids)
                    and conflict.rule_id in overridden
                ):
                    continue
                problems.append(
                    ValidationProblem(
                        "GEN-RULE-CONFLICT-REVIEW",
                        IssueLevel.ERROR,
                        f"规则 {conflict.rule_id} 存在未解决的 CONFLICT_REVIEW，不能形成有效规则集。",
                        conflict.rule_id,
                    )
                )

        unique_selected = tuple({rule.rule_id: rule for rule in selected}.values())
        unique_traces = tuple({(trace.rule_id, trace.action): trace for trace in traces}.values())
        return EffectiveRuleSet(
            context=context,
            rules=tuple(sorted(unique_selected, key=lambda rule: rule.rule_id)),
            considered_rules=considered,
            traces=unique_traces,
            overridden_rule_ids=tuple(sorted(overridden)),
            problems=tuple(problems),
        )

    def resolve_effective_rules(
        self,
        common_rules: Iterable[RuleDefinition],
        industry_rules: Iterable[RuleDefinition],
        context: RuleContext,
    ) -> EffectiveRuleSet:
        """Descriptive alias used by application services and tests."""

        return self.resolve(common_rules, industry_rules, context)
