"""Application contracts for explicitly saved accounting workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import uuid4

from packages.standards.carbon_material import CarbonMaterialInput


class ProjectWorkspaceRepositoryError(RuntimeError):
    """Raised when a project workspace cannot be safely read or written."""


class ProjectRecordAssociationError(ProjectWorkspaceRepositoryError):
    """Describe which part of a successful record's project link needs recovery."""

    def __init__(
        self,
        message: str,
        *,
        recovery_pending: bool,
        association_saved: bool,
    ) -> None:
        super().__init__(message)
        self.recovery_pending = recovery_pending
        self.association_saved = association_saved


class AccountingUnitType(str, Enum):
    WHOLE_SITE = "WHOLE_SITE"
    PROCESS = "PROCESS"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class AccountingUnitWorkspace:
    unit_id: str
    name: str
    unit_type: AccountingUnitType
    position: int
    form_state: dict[str, object]
    result_snapshot: dict[str, object] | None = None
    record_ids: tuple[str, ...] = ()
    input_fingerprint: str | None = None
    canonical_input: CarbonMaterialInput | None = None
    ingress_provenance: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not self.unit_id.strip() or not self.name.strip():
            raise ValueError("accounting unit identifier and name are required")
        if not isinstance(self.unit_type, AccountingUnitType):
            raise ValueError("unit_type must be an AccountingUnitType")
        if self.position < 0:
            raise ValueError("unit position must not be negative")
        if not isinstance(self.form_state, dict):
            raise ValueError("form_state must be an object")
        if self.result_snapshot is not None and not isinstance(self.result_snapshot, dict):
            raise ValueError("result_snapshot must be an object or None")
        if self.canonical_input is not None and not isinstance(self.canonical_input, CarbonMaterialInput):
            raise ValueError("canonical_input must be a CarbonMaterialInput or None")
        if self.ingress_provenance is not None and not isinstance(self.ingress_provenance, dict):
            raise ValueError("ingress_provenance must be an object or None")
        if len(set(self.record_ids)) != len(self.record_ids):
            raise ValueError("record identifiers must be unique within a unit")


@dataclass(frozen=True, slots=True)
class ProjectWorkspace:
    project_id: str
    name: str
    active_unit_id: str
    units: tuple[AccountingUnitWorkspace, ...]

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.name.strip():
            raise ValueError("project identifier and name are required")
        if not self.units:
            raise ValueError("a project must contain at least one accounting unit")
        ids = [unit.unit_id for unit in self.units]
        if len(set(ids)) != len(ids):
            raise ValueError("accounting unit identifiers must be unique")
        if self.active_unit_id not in ids:
            raise ValueError("active unit must belong to the project")


class ProjectWorkspaceRepository(Protocol):
    def save(self, workspace: ProjectWorkspace) -> None: ...
    def save_after_record(self, workspace: ProjectWorkspace, record_id: str) -> None: ...
    def get(self, project_id: str) -> ProjectWorkspace | None: ...
    def list_all(self) -> tuple[ProjectWorkspace, ...]: ...
    def delete(self, project_id: str) -> bool: ...


class ProjectWorkspaceTimestampRepository(Protocol):
    """Optional read-only timestamp query for repositories that expose one."""

    def list_updated_at_by_project_id(self) -> dict[str, datetime]: ...


class ProjectWorkspaceService:
    """Thin application service; project saves never write accounting records."""

    def __init__(self, repository: ProjectWorkspaceRepository) -> None:
        self.repository = repository

    @staticmethod
    def new_workspace(name: str = "新建核算项目") -> ProjectWorkspace:
        unit = AccountingUnitWorkspace(
            unit_id=f"unit.{uuid4().hex}",
            name="全厂",
            unit_type=AccountingUnitType.WHOLE_SITE,
            position=0,
            form_state={},
        )
        return ProjectWorkspace(f"project.{uuid4().hex}", name, unit.unit_id, (unit,))

    def save(self, workspace: ProjectWorkspace) -> None:
        self.repository.save(workspace)

    def save_after_record(self, workspace: ProjectWorkspace, record_id: str) -> None:
        """Persist a successful-record link through the repository recovery path."""

        self.repository.save_after_record(workspace, record_id)

    def get(self, project_id: str) -> ProjectWorkspace | None:
        return self.repository.get(project_id)

    def list_all(self) -> tuple[ProjectWorkspace, ...]:
        return self.repository.list_all()

    def list_updated_at_by_project_id(self) -> dict[str, datetime]:
        """Return saved project update times when the repository supports them.

        The optional capability keeps older repository test doubles and adapters
        usable while exposing existing persistence timestamps to Application.
        """
        reader = getattr(self.repository, "list_updated_at_by_project_id", None)
        if not callable(reader):
            return {}
        return reader()

    def delete(self, project_id: str) -> bool:
        return self.repository.delete(project_id)
