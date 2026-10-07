"""In-memory adapter for immutable accounting records and their evidence."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Sequence

from packages.core.errors import DomainValidationError
from packages.core.models import AccountingRecord
from packages.core.repositories import DetailedRecordRepository


def _snapshot_value(value: object) -> object:
    """Copy a snapshot into plain JSON-compatible values without domain internals."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _snapshot_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, dict):
        return {str(key): _snapshot_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_snapshot_value(item) for item in value]
    return value


class InMemoryRecordRepository(DetailedRecordRepository):
    """Ephemeral record store for explicit tests and preview fixtures."""

    def __init__(self) -> None:
        self._records: dict[str, AccountingRecord] = {}
        self._deleted: set[str] = set()
        self._audit: list[dict[str, object]] = []
        self._details: dict[str, dict[str, object]] = {}
        self._detail_schema_records: set[str] = set()

    def create(self, record: AccountingRecord) -> None:
        if record.record_id in self._records:
            raise DomainValidationError(f"record already exists: {record.record_id}")
        self._records[record.record_id] = record
        self._audit.append({"record_id": record.record_id, "action": "CREATE", "actor": "system"})

    def create_with_details(
        self,
        record: AccountingRecord,
        *,
        raw_input: object | None = None,
        effective_rule_set: Sequence[str] = (),
        trace_snapshot: object | None = None,
        provenance_snapshot: object | None = None,
        reporting_snapshot: object | None = None,
        report_qualification: object | None = None,
    ) -> None:
        self.create(record)
        self._details[record.record_id] = {
            "raw_input": _snapshot_value(raw_input if raw_input is not None else record.input_snapshot),
            "effective_rule_set": {"rule_ids": tuple(sorted(set(effective_rule_set)))},
            "trace_snapshot": _snapshot_value(trace_snapshot) if trace_snapshot else None,
            "provenance_snapshot": _snapshot_value(provenance_snapshot) if provenance_snapshot else None,
            "reporting_snapshot": _snapshot_value(reporting_snapshot) if reporting_snapshot else None,
            "report_qualification": _snapshot_value(report_qualification) if report_qualification else None,
        }
        if any(value is not None for value in (
            raw_input, trace_snapshot, provenance_snapshot, reporting_snapshot, report_qualification,
        )):
            self._detail_schema_records.add(record.record_id)

    def _detail(self, record_id: str, key: str) -> dict[str, object] | None:
        details = self._details.get(record_id)
        value = details.get(key) if details else None
        return value if isinstance(value, dict) else None

    def get_raw_input_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "raw_input")

    def get_effective_rule_set(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "effective_rule_set")

    def get_trace_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "trace_snapshot")

    def get_provenance_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "provenance_snapshot")

    def get_reporting_snapshot(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "reporting_snapshot")

    def get_report_qualification(self, record_id: str) -> dict[str, object] | None:
        return self._detail(record_id, "report_qualification")

    def get_snapshot_schema_version(self, record_id: str) -> int:
        return int(record_id in self._detail_schema_records)

    def get(self, record_id: str) -> AccountingRecord | None:
        if record_id in self._deleted:
            return None
        return self._records.get(record_id)

    def list_all(self) -> tuple[AccountingRecord, ...]:
        return tuple(record for record_id, record in self._records.items() if record_id not in self._deleted)

    def delete(self, record_id: str, *, actor: str, reason: str) -> bool:
        if not actor.strip() or not reason.strip():
            raise DomainValidationError("delete actor and reason are required")
        if record_id not in self._records or record_id in self._deleted:
            return False
        self._deleted.add(record_id)
        self._audit.append({"record_id": record_id, "action": "DELETE", "actor": actor, "reason": reason})
        return True

    def list_audit(self, record_id: str | None = None) -> tuple[dict[str, object], ...]:
        if record_id is None:
            return tuple(self._audit)
        return tuple(item for item in self._audit if item.get("record_id") == record_id)


__all__ = ["InMemoryRecordRepository"]
