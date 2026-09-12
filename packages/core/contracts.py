"""Reusable G05 contracts for activity data, evidence, validation and sums."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import re
from typing import Protocol

from .decimal_policy import DecimalPolicy
from .errors import DomainValidationError, IssueLevel, ValidationProblem
from .models import ActivityData, ActivityDataSource, ActivitySourceLevel


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")


def _token(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _TOKEN_PATTERN.fullmatch(value):
        raise DomainValidationError(f"{field_name} must be a stable identifier")
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} is required")
    return value.strip()


class ValidationContract(Protocol):
    """A domain validation contract that returns structured problems."""

    def validate(self, value: object) -> tuple[ValidationProblem, ...]:
        ...


@dataclass(frozen=True, slots=True)
class DataSourceReference:
    """Evidence pointer for an activity value; files remain outside Domain."""

    reference_id: str
    source_type: ActivityDataSource
    description: str
    locator: str | None = None
    captured_at: datetime | None = None

    def __post_init__(self) -> None:
        _token(self.reference_id, "reference_id")
        if not isinstance(self.source_type, ActivityDataSource):
            raise DomainValidationError("source_type must be an ActivityDataSource")
        _text(self.description, "description")
        if self.locator is not None:
            _text(self.locator, "locator")
        if self.captured_at is not None and self.captured_at.tzinfo is None:
            raise DomainValidationError("captured_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ActivityDataContract:
    """Generic contract for validating one activity value before calculation."""

    contract_id: str
    activity_id: str
    expected_unit: str
    required: bool = True
    nonnegative: bool = True
    percentage_input: bool = False
    evidence_required: bool = False
    allowed_source_levels: tuple[ActivitySourceLevel, ...] = (
        ActivitySourceLevel.PRIMARY,
        ActivitySourceLevel.SECONDARY,
        ActivitySourceLevel.PROXY,
    )

    def __post_init__(self) -> None:
        _token(self.contract_id, "contract_id")
        _token(self.activity_id, "activity_id")
        _text(self.expected_unit, "expected_unit")
        if any(not isinstance(level, ActivitySourceLevel) for level in self.allowed_source_levels):
            raise DomainValidationError("allowed_source_levels must contain ActivitySourceLevel values")

    def validate(self, value: ActivityData | None) -> tuple[ValidationProblem, ...]:
        problems: list[ValidationProblem] = []
        if value is None:
            if self.required:
                problems.append(
                    ValidationProblem(
                        "GEN-VAL-REQUIRED-MISSING",
                        IssueLevel.ERROR,
                        f"缺少必填活动数据 {self.activity_id}。",
                        self.activity_id,
                    )
                )
            return tuple(problems)
        if value.activity_id != self.activity_id:
            problems.append(
                ValidationProblem(
                    "GEN-VAL-ACTIVITY-ID",
                    IssueLevel.ERROR,
                    f"活动数据 ID {value.activity_id} 与契约 {self.activity_id} 不一致。",
                    self.activity_id,
                )
            )
        if value.unit != self.expected_unit:
            problems.append(
                ValidationProblem(
                    "GEN-VAL-UNIT-INCOMPATIBLE",
                    IssueLevel.ERROR,
                    f"活动数据单位 {value.unit} 与要求单位 {self.expected_unit} 不一致。",
                    self.activity_id,
                )
            )
        if self.nonnegative and value.value < Decimal("0"):
            problems.append(
                ValidationProblem(
                    "GEN-VAL-NONNEGATIVE",
                    IssueLevel.ERROR,
                    "活动数据不得为负数。",
                    self.activity_id,
                )
            )
        if self.percentage_input and not Decimal("0") <= value.value <= Decimal("100"):
            problems.append(
                ValidationProblem(
                    "GEN-VAL-PERCENT-RANGE",
                    IssueLevel.ERROR,
                    "百分比活动数据必须处于 0% 到 100% 范围内。",
                    self.activity_id,
                )
            )
        if value.source_level not in self.allowed_source_levels:
            problems.append(
                ValidationProblem(
                    "GEN-VAL-SOURCE-LEVEL",
                    IssueLevel.ERROR,
                    "活动数据来源等级不满足当前契约。",
                    self.activity_id,
                )
            )
        if value.source_level is ActivitySourceLevel.PROXY:
            problems.append(
                ValidationProblem(
                    "GEN-VAL-PROXY-DATA",
                    IssueLevel.WARNING,
                    "使用替代活动数据，需保留折算或适用性说明。",
                    self.activity_id,
                )
            )
        if self.evidence_required and not value.source_reference:
            problems.append(
                ValidationProblem(
                    "GEN-VAL-SOURCE-EVIDENCE",
                    IssueLevel.ERROR,
                    "当前活动数据需要来源证据定位。",
                    self.activity_id,
                )
            )
        return tuple(problems)


class AggregationOperation(str, Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    REPORT_ONLY = "REPORT_ONLY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class AggregationLine:
    source_id: str
    operation: AggregationOperation
    required: bool = True

    def __post_init__(self) -> None:
        _token(self.source_id, "source_id")
        if not isinstance(self.operation, AggregationOperation):
            raise DomainValidationError("operation must be an AggregationOperation")


@dataclass(frozen=True, slots=True)
class AggregationContract:
    """A generic source-coverage contract; it does not encode industry formulas."""

    contract_id: str
    lines: tuple[AggregationLine, ...]
    requires_complete_coverage: bool = True

    def __post_init__(self) -> None:
        _token(self.contract_id, "contract_id")
        lines = tuple(self.lines)
        if len({line.source_id for line in lines}) != len(lines):
            raise DomainValidationError("aggregation source IDs must be unique")
        object.__setattr__(self, "lines", lines)

    def validate_coverage(self, enabled_source_ids: tuple[str, ...] | list[str]) -> tuple[ValidationProblem, ...]:
        enabled = tuple(enabled_source_ids)
        known = {line.source_id: line for line in self.lines}
        problems: list[ValidationProblem] = []
        for source_id in enabled:
            if source_id not in known:
                problems.append(
                    ValidationProblem(
                        "GEN-VAL-TOTAL-SOURCE-COVERAGE-001",
                        IssueLevel.ERROR,
                        f"启用排放源 {source_id} 没有明确的聚合关系。",
                        source_id,
                    )
                )
        if self.requires_complete_coverage:
            for line in self.lines:
                if line.required and line.source_id not in enabled and line.operation not in {
                    AggregationOperation.REPORT_ONLY,
                    AggregationOperation.NOT_APPLICABLE,
                }:
                    problems.append(
                        ValidationProblem(
                            "GEN-VAL-SOURCE-UNCONFIRMED",
                            IssueLevel.ERROR,
                            f"必需排放源 {line.source_id} 未确认是否启用。",
                            line.source_id,
                        )
                    )
        return tuple(problems)

    def aggregate(
        self,
        values: Mapping[str, str | Decimal | int],
        *,
        policy: DecimalPolicy | None = None,
    ) -> Decimal:
        """Apply only ADD/SUBTRACT contract operations to already compatible amounts."""

        decimal_policy = policy or DecimalPolicy()
        coverage_problems = self.validate_coverage(tuple(values.keys()))
        if coverage_problems:
            raise DomainValidationError(coverage_problems[0].message)
        total = Decimal("0")
        for line in self.lines:
            if line.operation in {AggregationOperation.REPORT_ONLY, AggregationOperation.NOT_APPLICABLE}:
                continue
            if line.source_id not in values:
                if line.required:
                    raise DomainValidationError(f"missing aggregation value: {line.source_id}")
                continue
            amount = decimal_policy.parse(values[line.source_id])
            total = decimal_policy.add(
                total,
                amount if line.operation is AggregationOperation.ADD else -amount,
            )
        return total
