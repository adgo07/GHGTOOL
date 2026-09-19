"""Repository contracts with no persistence implementation dependency."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .models import AccountingRecord, Factor, Parameter, Settings, Standard
from .rules import RuleDefinition


@runtime_checkable
class StandardRepository(Protocol):
    def get(self, standard_id: str) -> Standard | None:
        """Return one immutable standard version by stable ID."""

    def list_all(self) -> Sequence[Standard]:
        """Return available standard versions."""


@runtime_checkable
class ParameterRepository(Protocol):
    def get_parameter(self, parameter_id: str) -> Parameter | None:
        """Return a parameter definition by stable ID."""

    def get_factor(self, factor_id: str) -> Factor | None:
        """Return one factor value by stable ID."""

    def list_factors(self, parameter_id: str) -> Sequence[Factor]:
        """Return factor versions associated with one parameter."""


@runtime_checkable
class RecordRepository(Protocol):
    def create(self, record: AccountingRecord) -> None:
        """Create one immutable successful record; updates are not part of this contract."""

    def get(self, record_id: str) -> AccountingRecord | None:
        """Return a record by stable ID."""

    def list_all(self) -> Sequence[AccountingRecord]:
        """Return records in repository-defined order."""


@runtime_checkable
class RecordLifecycleRepository(Protocol):
    """Optional record-store lifecycle operations owned by the application edge."""

    def delete(self, record_id: str, *, actor: str, reason: str) -> bool:
        """Soft-delete one record and append an audit entry."""

    def list_audit(self, record_id: str | None = None) -> Sequence[object]:
        """Return audit entries for one record or the whole record store."""


@runtime_checkable
class SettingsRepository(Protocol):
    def load(self) -> Settings:
        """Load user settings from the implementation-selected store."""

    def save(self, settings: Settings) -> None:
        """Persist user settings without exposing storage details to Domain."""


@runtime_checkable
class RuleRepository(Protocol):
    def list_rules(self, standard_id: str | None = None) -> Sequence[RuleDefinition]:
        """Return immutable common/industry rules, optionally scoped to a standard."""
