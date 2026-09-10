"""Shared domain errors and validation-problem severity."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class DomainError(ValueError):
    """Base error for invalid domain values or state transitions."""


class DomainValidationError(DomainError):
    """Raised when a domain object violates a frozen invariant."""


class IssueLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


_PROBLEM_CODE_PATTERN = re.compile(r"[A-Z][A-Z0-9_.-]{1,63}")


@dataclass(frozen=True, slots=True)
class ValidationProblem:
    """Structured validation feedback; code is stable, message is descriptive."""

    code: str
    level: IssueLevel
    message: str
    field_id: str | None = None
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not _PROBLEM_CODE_PATTERN.fullmatch(self.code):
            raise DomainValidationError("validation problem code must be a stable token")
        if not self.message.strip():
            raise DomainValidationError("validation problem message is required")
        if self.field_id is not None and not re.fullmatch(
            r"[A-Za-z0-9_.:-]{1,128}", self.field_id
        ):
            raise DomainValidationError("field_id must be a stable token")
        object.__setattr__(self, "details", tuple(self.details))

    @property
    def blocks_record(self) -> bool:
        return self.level is IssueLevel.ERROR


def contains_errors(problems: tuple[ValidationProblem, ...] | list[ValidationProblem]) -> bool:
    return any(problem.level is IssueLevel.ERROR for problem in problems)


def contains_warnings(problems: tuple[ValidationProblem, ...] | list[ValidationProblem]) -> bool:
    return any(problem.level is IssueLevel.WARNING for problem in problems)

