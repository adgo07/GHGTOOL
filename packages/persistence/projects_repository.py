"""SQLite adapter for mutable saved projects, isolated from immutable records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.application.project_workspaces import (
    AccountingUnitType,
    AccountingUnitWorkspace,
    ProjectWorkspace,
)

from .sqlite import initialize_database


class ProjectWorkspaceRepositoryError(RuntimeError):
    """Raised when a project workspace cannot be safely read or written."""


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(value: str, field: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ProjectWorkspaceRepositoryError(f"invalid project JSON in {field}") from exc


def _workspace_payload(workspace: ProjectWorkspace) -> dict[str, Any]:
    return {
        "project_id": workspace.project_id,
        "name": workspace.name,
        "active_unit_id": workspace.active_unit_id,
        "units": [
            {
                "unit_id": unit.unit_id,
                "name": unit.name,
                "unit_type": unit.unit_type.value,
                "position": unit.position,
                "form_state": unit.form_state,
                "result_snapshot": unit.result_snapshot,
                "record_ids": list(unit.record_ids),
                "input_fingerprint": unit.input_fingerprint,
            }
            for unit in workspace.units
        ],
    }


def _workspace_from_payload(payload: Any) -> ProjectWorkspace:
    if not isinstance(payload, dict) or not isinstance(payload.get("units"), list):
        raise ProjectWorkspaceRepositoryError("invalid pending project workspace payload")
    units = tuple(
        AccountingUnitWorkspace(
            unit_id=str(item["unit_id"]),
            name=str(item["name"]),
            unit_type=AccountingUnitType(str(item["unit_type"])),
            position=int(item["position"]),
            form_state=item["form_state"],
            result_snapshot=item.get("result_snapshot"),
            record_ids=tuple(str(record_id) for record_id in item.get("record_ids", ())),
            input_fingerprint=(
                str(item["input_fingerprint"])
                if item.get("input_fingerprint") is not None
                else None
            ),
        )
        for item in payload["units"]
        if isinstance(item, dict)
    )
    return ProjectWorkspace(
        project_id=str(payload["project_id"]),
        name=str(payload["name"]),
        active_unit_id=str(payload["active_unit_id"]),
        units=units,
    )


class SQLiteProjectWorkspaceRepository:
    """Stores editable project state; it has no table or FK into records.sqlite."""

    def __init__(self, path: str | Path, *, app_version: str = "1.1.0") -> None:
        self.path = initialize_database(
            path,
            "projects",
            app_version=app_version,
            data_version="not_applicable",
            deterministic=False,
        )
        self._recover_pending_links()

    def save(self, workspace: ProjectWorkspace) -> None:
        now = datetime.now(timezone.utc).isoformat()
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT created_at FROM projects WHERE project_id=?", (workspace.project_id,)
            ).fetchone()
            created_at = str(existing[0]) if existing else now
            connection.execute(
                "INSERT INTO projects(project_id,name,active_unit_id,created_at,updated_at) "
                "VALUES(?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET "
                "name=excluded.name, active_unit_id=excluded.active_unit_id, updated_at=excluded.updated_at",
                (workspace.project_id, workspace.name, workspace.active_unit_id, created_at, now),
            )
            connection.execute("DELETE FROM accounting_units WHERE project_id=?", (workspace.project_id,))
            for unit in workspace.units:
                connection.execute(
                    "INSERT INTO accounting_units(unit_id,project_id,unit_name,unit_type,position,"
                    "form_state_json,result_snapshot_json,record_ids_json,input_fingerprint) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        unit.unit_id,
                        workspace.project_id,
                        unit.name,
                        unit.unit_type.value,
                        unit.position,
                        _dump(unit.form_state),
                        _dump(unit.result_snapshot) if unit.result_snapshot is not None else None,
                        _dump(list(unit.record_ids)),
                        unit.input_fingerprint,
                    ),
                )
            connection.commit()
        except (sqlite3.Error, TypeError, ValueError) as exc:
            connection.rollback()
            raise ProjectWorkspaceRepositoryError(f"cannot save project {workspace.project_id}: {exc}") from exc
        finally:
            connection.close()

    def save_after_record(self, workspace: ProjectWorkspace, record_id: str) -> None:
        """Durably queue, save and clear one successful-record association."""

        linked_units = [unit for unit in workspace.units if record_id in unit.record_ids]
        if len(linked_units) != 1:
            raise ProjectWorkspaceRepositoryError(
                f"record {record_id} must belong to exactly one accounting unit"
            )
        now = datetime.now(timezone.utc).isoformat()
        connection = sqlite3.connect(self.path)
        try:
            with connection:
                connection.execute(
                    "INSERT INTO pending_record_links(record_id,project_id,unit_id,workspace_json,created_at) "
                    "VALUES(?,?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET "
                    "project_id=excluded.project_id,unit_id=excluded.unit_id,"
                    "workspace_json=excluded.workspace_json,created_at=excluded.created_at",
                    (
                        record_id,
                        workspace.project_id,
                        linked_units[0].unit_id,
                        _dump(_workspace_payload(workspace)),
                        now,
                    ),
                )
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise ProjectWorkspaceRepositoryError(
                f"record {record_id} was created but its project recovery marker could not be saved: {exc}"
            ) from exc
        finally:
            connection.close()

        try:
            self.save(workspace)
        except ProjectWorkspaceRepositoryError as exc:
            raise ProjectWorkspaceRepositoryError(
                f"record {record_id} was created; its project association remains queued for recovery: {exc}"
            ) from exc
        self._clear_pending_link(record_id)

    def _clear_pending_link(self, record_id: str) -> None:
        connection = sqlite3.connect(self.path)
        try:
            with connection:
                connection.execute("DELETE FROM pending_record_links WHERE record_id=?", (record_id,))
        except sqlite3.Error as exc:
            raise ProjectWorkspaceRepositoryError(
                f"project association was saved but recovery marker {record_id} could not be cleared: {exc}"
            ) from exc
        finally:
            connection.close()

    def _recover_pending_links(self) -> None:
        connection = sqlite3.connect(self.path)
        try:
            rows = connection.execute(
                "SELECT record_id,workspace_json FROM pending_record_links ORDER BY created_at,record_id"
            ).fetchall()
        except sqlite3.Error as exc:
            raise ProjectWorkspaceRepositoryError(f"cannot inspect pending record links: {exc}") from exc
        finally:
            connection.close()
        for record_id, workspace_json in rows:
            try:
                workspace = _workspace_from_payload(
                    _load(str(workspace_json), "pending_record_links.workspace_json")
                )
                self.save(workspace)
                self._clear_pending_link(str(record_id))
            except (KeyError, TypeError, ValueError, ProjectWorkspaceRepositoryError) as exc:
                raise ProjectWorkspaceRepositoryError(
                    f"cannot recover pending project association for record {record_id}: {exc}"
                ) from exc

    def get(self, project_id: str) -> ProjectWorkspace | None:
        connection = sqlite3.connect(self.path)
        try:
            project = connection.execute(
                "SELECT project_id,name,active_unit_id FROM projects WHERE project_id=?",
                (project_id,),
            ).fetchone()
            if project is None:
                return None
            units = self._units(connection, project_id)
            return ProjectWorkspace(str(project[0]), str(project[1]), str(project[2]), units)
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise ProjectWorkspaceRepositoryError(f"cannot read project {project_id}: {exc}") from exc
        finally:
            connection.close()

    def list_all(self) -> tuple[ProjectWorkspace, ...]:
        connection = sqlite3.connect(self.path)
        try:
            ids = tuple(str(row[0]) for row in connection.execute(
                "SELECT project_id FROM projects ORDER BY updated_at DESC, project_id"
            ))
            projects: list[ProjectWorkspace] = []
            for project_id in ids:
                project = connection.execute(
                    "SELECT project_id,name,active_unit_id FROM projects WHERE project_id=?",
                    (project_id,),
                ).fetchone()
                if project is not None:
                    projects.append(ProjectWorkspace(
                        str(project[0]), str(project[1]), str(project[2]), self._units(connection, project_id)
                    ))
            return tuple(projects)
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise ProjectWorkspaceRepositoryError(f"cannot list projects: {exc}") from exc
        finally:
            connection.close()

    def delete(self, project_id: str) -> bool:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.execute("DELETE FROM pending_record_links WHERE project_id=?", (project_id,))
                cursor = connection.execute("DELETE FROM projects WHERE project_id=?", (project_id,))
            return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise ProjectWorkspaceRepositoryError(f"cannot delete project {project_id}: {exc}") from exc
        finally:
            connection.close()

    @staticmethod
    def _units(connection: sqlite3.Connection, project_id: str) -> tuple[AccountingUnitWorkspace, ...]:
        rows = connection.execute(
            "SELECT unit_id,unit_name,unit_type,position,form_state_json,result_snapshot_json,"
            "record_ids_json,input_fingerprint FROM accounting_units WHERE project_id=? "
            "ORDER BY position,unit_id",
            (project_id,),
        ).fetchall()
        return tuple(
            AccountingUnitWorkspace(
                unit_id=str(row[0]),
                name=str(row[1]),
                unit_type=AccountingUnitType(str(row[2])),
                position=int(row[3]),
                form_state=_load(str(row[4]), "accounting_units.form_state_json"),
                result_snapshot=_load(str(row[5]), "accounting_units.result_snapshot_json") if row[5] is not None else None,
                record_ids=tuple(str(item) for item in _load(str(row[6]), "accounting_units.record_ids_json")),
                input_fingerprint=str(row[7]) if row[7] is not None else None,
            )
            for row in rows
        )
