"""Transactional SQLite adapter for immutable G07 accounting records."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from packages.core.errors import DomainValidationError, IssueLevel, ValidationProblem
from packages.core.models import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    ActivityData,
    ActivityDataSource,
    ActivitySourceLevel,
    CalculationLine,
    CalculationResult,
    EmissionSourceSelection,
    ParameterSelectionMethod,
    ParameterSnapshot,
    PeriodType,
    RecordStatus,
)

from .sqlite import initialize_database


class RecordRepositoryError(RuntimeError):
    """Raised when the records database cannot complete a safe operation."""


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Read-only audit evidence for one records-database action."""

    audit_id: str
    record_id: str | None
    action: str
    occurred_at: datetime
    actor: str
    details: dict[str, Any]


def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {field.name: _encode(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_encode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load_json(value: str, field: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise RecordRepositoryError(f"invalid JSON in records field {field!r}") from exc


def _datetime(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RecordRepositoryError(f"invalid datetime in records field {field!r}") from exc
    if parsed.tzinfo is None:
        raise RecordRepositoryError(f"records field {field!r} must be timezone-aware")
    return parsed


def _date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordRepositoryError(f"invalid date in records field {field!r}") from exc


def _problem(payload: dict[str, Any]) -> ValidationProblem:
    details = tuple((str(item[0]), str(item[1])) for item in payload.get("details", []))
    return ValidationProblem(
        code=str(payload["code"]),
        level=IssueLevel(str(payload["level"])),
        message=str(payload["message"]),
        field_id=payload.get("field_id"),
        details=details,
    )


def _period(payload: dict[str, Any]) -> AccountingPeriod:
    return AccountingPeriod(
        period_type=PeriodType(str(payload["period_type"])),
        start=_date(str(payload["start"]), "period.start"),
        end=_date(str(payload["end"]), "period.end"),
    )


def _input(payload: dict[str, Any]) -> AccountingInput:
    return AccountingInput(
        input_id=str(payload["input_id"]),
        standard_id=str(payload["standard_id"]),
        period=_period(payload["period"]),
        enterprise_name=payload.get("enterprise_name"),
        boundary_component_ids=tuple(str(item) for item in payload.get("boundary_component_ids", [])),
        emission_sources=tuple(
            EmissionSourceSelection(str(item["source_id"]), bool(item["included"]))
            for item in payload.get("emission_sources", [])
        ),
        activities=tuple(
            ActivityData(
                activity_id=str(item["activity_id"]),
                value=item["value"],
                unit=str(item["unit"]),
                source_type=ActivityDataSource(str(item["source_type"])),
                source_reference=item.get("source_reference"),
                source_level=ActivitySourceLevel(str(item.get("source_level", ActivitySourceLevel.PRIMARY.value))),
            )
            for item in payload.get("activities", [])
        ),
    )


def _result(payload: dict[str, Any]) -> CalculationResult:
    return CalculationResult(
        result_id=str(payload["result_id"]),
        standard_id=str(payload["standard_id"]),
        algorithm_version=str(payload["algorithm_version"]),
        lines=tuple(
            CalculationLine(
                line_id=str(item["line_id"]),
                emission_source_id=str(item["emission_source_id"]),
                greenhouse_gas_id=str(item["greenhouse_gas_id"]),
                amount=item["amount"],
                unit=str(item["unit"]),
            )
            for item in payload.get("lines", [])
        ),
        total_amount=payload["total_amount"],
        total_unit=str(payload["total_unit"]),
        calculated_at=_datetime(str(payload["calculated_at"]), "calculation.calculated_at"),
        problems=tuple(_problem(item) for item in payload.get("problems", [])),
    )


def _parameter_snapshot(payload: dict[str, Any]) -> ParameterSnapshot:
    return ParameterSnapshot(
        snapshot_id=str(payload["snapshot_id"]),
        parameter_id=str(payload["parameter_id"]),
        factor_id=payload.get("factor_id"),
        value_used=payload["value_used"],
        unit_used=str(payload["unit_used"]),
        source_id=payload.get("source_id"),
        source_version=payload.get("source_version"),
        selection_method=ParameterSelectionMethod(str(payload["selection_method"])),
        selection_reason=str(payload["selection_reason"]),
        standard_id=str(payload["standard_id"]),
        snapshot_at=_datetime(str(payload["snapshot_at"]), "parameter.snapshot_at"),
        factor_version=payload.get("factor_version"),
        source_location=payload.get("source_location"),
        factor_year=payload.get("factor_year"),
        detail_id=payload.get("detail_id"),
    )


def _record_payload(record: AccountingRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "standard_id": record.standard_id,
        "standard_version": record.standard_version,
        "algorithm_version": record.algorithm_version,
        "created_at": record.created_at.isoformat(),
        "input_snapshot": _encode(record.input_snapshot),
        "calculation_result": _encode(record.calculation_result),
        "status": record.status.value,
        "parameter_snapshots": _encode(record.parameter_snapshots),
        "problems": _encode(record.problems),
    }


def _record_from_payload(payload: dict[str, Any]) -> AccountingRecord:
    return AccountingRecord(
        record_id=str(payload["record_id"]),
        standard_id=str(payload["standard_id"]),
        algorithm_version=str(payload["algorithm_version"]),
        created_at=_datetime(str(payload["created_at"]), "record.created_at"),
        input_snapshot=_input(payload["input_snapshot"]),
        calculation_result=_result(payload["calculation_result"]),
        status=RecordStatus(str(payload["status"])),
        parameter_snapshots=tuple(_parameter_snapshot(item) for item in payload.get("parameter_snapshots", [])),
        problems=tuple(_problem(item) for item in payload.get("problems", [])),
        standard_version=payload.get("standard_version"),
    )


class SQLiteRecordRepository:
    """Store immutable successful records in records.sqlite with soft deletion."""

    def __init__(
        self,
        path: str | Path,
        *,
        app_version: str = "0.1.0",
        data_version: str = "not_applicable",
    ) -> None:
        self.path = initialize_database(
            path,
            "records",
            app_version=app_version,
            data_version=data_version,
            deterministic=True,
        )

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _warnings(record: AccountingRecord) -> tuple[ValidationProblem, ...]:
        return tuple(
            problem
            for problem in (*record.problems, *record.calculation_result.problems)
            if problem.level is IssueLevel.WARNING
        )

    def create(self, record: AccountingRecord) -> None:
        self.create_with_details(record)

    def create_with_details(
        self,
        record: AccountingRecord,
        *,
        raw_input: object | None = None,
        effective_rule_set: Sequence[str] = (),
    ) -> None:
        payload = _record_payload(record)
        raw_snapshot = _encode(raw_input if raw_input is not None else record.input_snapshot)
        rule_snapshot = {
            "rule_ids": sorted({str(rule_id) for rule_id in effective_rule_set}),
            "parameter_snapshot_ids": [item.snapshot_id for item in record.parameter_snapshots],
        }
        warnings = self._warnings(record)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO accounting_records ("
                "record_id, status, created_at, standard_id, standard_version, algorithm_version, "
                "input_snapshot_json, calculation_snapshot_json, parameter_snapshot_json, warnings_json, "
                "raw_input_snapshot_json, effective_rule_set_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.status.value,
                    record.created_at.isoformat(),
                    record.standard_id,
                    record.standard_version or "",
                    record.algorithm_version,
                    _json(payload["input_snapshot"]),
                    _json(payload["calculation_result"] | {"record_problems": payload["problems"]}),
                    _json(payload["parameter_snapshots"]),
                    _json(warnings),
                    _json(raw_snapshot),
                    _json(rule_snapshot),
                ),
            )
            connection.execute(
                "INSERT INTO audit_log (audit_id, record_id, action, occurred_at, actor, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"audit.{uuid4().hex}",
                    record.record_id,
                    "CREATE",
                    record.created_at.isoformat(),
                    "system",
                    _json({
                        "status": record.status.value,
                        "standard_id": record.standard_id,
                        "standard_version": record.standard_version,
                        "parameter_snapshot_count": len(record.parameter_snapshots),
                    }),
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            if "accounting_records.record_id" in str(exc) or "UNIQUE constraint failed" in str(exc):
                raise DomainValidationError(f"record already exists: {record.record_id}") from exc
            raise RecordRepositoryError(f"record transaction rejected: {exc}") from exc
        except sqlite3.Error as exc:
            connection.rollback()
            raise RecordRepositoryError(f"record transaction failed: {exc}") from exc
        finally:
            connection.close()

    def get(self, record_id: str) -> AccountingRecord | None:
        connection = self._connection()
        try:
            row = connection.execute(
                "SELECT status, created_at, standard_id, standard_version, algorithm_version, input_snapshot_json, "
                "calculation_snapshot_json, parameter_snapshot_json "
                "FROM accounting_records WHERE record_id = ? AND deleted_at IS NULL",
                (record_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        input_payload = _load_json(row["input_snapshot_json"], "input_snapshot_json")
        calculation_payload = _load_json(row["calculation_snapshot_json"], "calculation_snapshot_json")
        problems = calculation_payload.pop("record_problems", [])
        payload = {
            "record_id": record_id,
            "standard_id": str(row["standard_id"]),
            "standard_version": str(row["standard_version"]) or None,
            "algorithm_version": str(row["algorithm_version"]),
            "created_at": str(row["created_at"]),
            "input_snapshot": input_payload,
            "calculation_result": calculation_payload,
            "status": str(row["status"]),
            "parameter_snapshots": _load_json(row["parameter_snapshot_json"], "parameter_snapshot_json"),
            "problems": problems,
        }
        return _record_from_payload(payload)

    def list_all(self) -> tuple[AccountingRecord, ...]:
        connection = self._connection()
        try:
            rows = connection.execute(
                "SELECT record_id FROM accounting_records "
                "WHERE deleted_at IS NULL ORDER BY created_at DESC, record_id DESC"
            ).fetchall()
        finally:
            connection.close()
        records = tuple(record for row in rows if (record := self.get(str(row["record_id"]))) is not None)
        return records

    def get_raw_input_snapshot(self, record_id: str) -> dict[str, Any] | None:
        connection = self._connection()
        try:
            row = connection.execute(
                "SELECT raw_input_snapshot_json FROM accounting_records "
                "WHERE record_id = ? AND deleted_at IS NULL",
                (record_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        value = _load_json(row["raw_input_snapshot_json"], "raw_input_snapshot_json")
        return value if isinstance(value, dict) else {"value": value}

    def get_effective_rule_set(self, record_id: str) -> dict[str, Any] | None:
        """Return the immutable effective-rule snapshot for one active record."""

        connection = self._connection()
        try:
            row = connection.execute(
                "SELECT effective_rule_set_json FROM accounting_records "
                "WHERE record_id = ? AND deleted_at IS NULL",
                (record_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        value = _load_json(row["effective_rule_set_json"], "effective_rule_set_json")
        return value if isinstance(value, dict) else {"value": value}

    def delete(self, record_id: str, *, actor: str, reason: str) -> bool:
        if not isinstance(actor, str) or not actor.strip():
            raise DomainValidationError("delete actor is required")
        if not isinstance(reason, str) or not reason.strip():
            raise DomainValidationError("delete reason is required")
        occurred_at = datetime.now(timezone.utc).isoformat()
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, standard_id FROM accounting_records "
                "WHERE record_id = ? AND deleted_at IS NULL",
                (record_id,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return False
            connection.execute(
                "UPDATE accounting_records SET deleted_at = ?, deleted_by = ?, deleted_reason = ? "
                "WHERE record_id = ? AND deleted_at IS NULL",
                (occurred_at, actor.strip(), reason.strip(), record_id),
            )
            connection.execute(
                "INSERT INTO audit_log (audit_id, record_id, action, occurred_at, actor, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"audit.{uuid4().hex}",
                    record_id,
                    "DELETE",
                    occurred_at,
                    actor.strip(),
                    _json({
                        "reason": reason.strip(),
                        "status_before_delete": row["status"],
                        "standard_id": row["standard_id"],
                    }),
                ),
            )
            connection.commit()
            return True
        except sqlite3.Error as exc:
            connection.rollback()
            raise RecordRepositoryError(f"record deletion failed: {exc}") from exc
        finally:
            connection.close()

    def list_audit(self, record_id: str | None = None) -> tuple[AuditEntry, ...]:
        connection = self._connection()
        try:
            if record_id is None:
                rows = connection.execute(
                    "SELECT audit_id, record_id, action, occurred_at, actor, details_json "
                    "FROM audit_log ORDER BY rowid"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT audit_id, record_id, action, occurred_at, actor, details_json "
                    "FROM audit_log WHERE record_id = ? ORDER BY rowid",
                    (record_id,),
                ).fetchall()
        finally:
            connection.close()
        result: list[AuditEntry] = []
        for row in rows:
            details = _load_json(row["details_json"], "audit.details_json")
            result.append(
                AuditEntry(
                    audit_id=str(row["audit_id"]),
                    record_id=row["record_id"],
                    action=str(row["action"]),
                    occurred_at=_datetime(str(row["occurred_at"]), "audit.occurred_at"),
                    actor=str(row["actor"]),
                    details=details if isinstance(details, dict) else {"value": details},
                )
            )
        return tuple(result)


__all__ = ["AuditEntry", "RecordRepositoryError", "SQLiteRecordRepository"]