"""Read recent enterprise-name candidates from saved business history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Protocol

from packages.core.repositories import RecordRepository
from packages.application.project_workspaces import ProjectWorkspace

_LOGGER = logging.getLogger(__name__)


class _ProjectService(Protocol):
    def list_all(self) -> tuple[ProjectWorkspace, ...]: ...


@dataclass(frozen=True, slots=True)
class _NameCandidate:
    name: str
    used_at: datetime | None


def _as_utc(value: object) -> datetime | None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


def list_enterprise_name_candidates(
    record_repository: RecordRepository | None = None,
    project_service: _ProjectService | None = None,
) -> tuple[str, ...]:
    """Return unique names sorted by saved Record/Project timestamps.

    Records use the AccountingRecord.created_at value. Projects use existing
    projects.updated_at values exposed through the Application service. Older
    repository stubs without that optional query retain their repository order
    and are considered after timestamped candidates. Equal timestamps preserve
    stable order: Records first, then the Project repository order.
    """

    candidates: list[_NameCandidate] = []

    if record_repository is not None:
        try:
            for record in record_repository.list_all():
                name = record.input_snapshot.enterprise_name
                if isinstance(name, str) and name.strip():
                    candidates.append(_NameCandidate(name.strip(), _as_utc(record.created_at)))
        except Exception:
            _LOGGER.warning("Unable to read enterprise names from saved records", exc_info=True)

    if project_service is not None:
        try:
            projects = project_service.list_all()
        except Exception:
            _LOGGER.warning("Unable to read enterprise names from saved projects", exc_info=True)
            projects = ()
        project_timestamps: dict[str, datetime] = {}
        timestamp_reader = getattr(project_service, "list_updated_at_by_project_id", None)
        if callable(timestamp_reader):
            try:
                raw_timestamps = timestamp_reader()
                if isinstance(raw_timestamps, dict):
                    project_timestamps = {
                        project_id: timestamp
                        for project_id, raw_timestamp in raw_timestamps.items()
                        if isinstance(project_id, str)
                        and (timestamp := _as_utc(raw_timestamp)) is not None
                    }
            except Exception:
                _LOGGER.warning("Unable to read saved project update timestamps", exc_info=True)

        for project in projects:
            project_id = getattr(project, "project_id", None)
            used_at = project_timestamps.get(project_id) if isinstance(project_id, str) else None
            for unit in project.units:
                canonical = unit.canonical_input
                canonical_name = canonical.enterprise_name if canonical is not None else None
                if isinstance(canonical_name, str) and canonical_name.strip():
                    name = canonical_name
                else:
                    # Existing objectName used when older projects captured Qt state.
                    name = unit.form_state.get("enterpriseNameInput")
                if isinstance(name, str) and name.strip():
                    candidates.append(_NameCandidate(name.strip(), used_at))

    timestamped = [candidate for candidate in candidates if candidate.used_at is not None]
    untimestamped = [candidate for candidate in candidates if candidate.used_at is None]
    timestamped.sort(key=lambda candidate: candidate.used_at, reverse=True)

    names: list[str] = []
    seen: set[str] = set()
    for candidate in (*timestamped, *untimestamped):
        key = candidate.name.casefold()
        if key not in seen:
            seen.add(key)
            names.append(candidate.name)
    return tuple(names)


__all__ = ["list_enterprise_name_candidates"]
