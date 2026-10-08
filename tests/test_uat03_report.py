"""UAT03 enterprise-history ordering and compatibility tests."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from packages.application.enterprise_history import list_enterprise_name_candidates
from packages.application.project_workspaces import ProjectWorkspaceService
from packages.ui import report_export


UTC = timezone.utc


class FakeRecordRepository:
    def __init__(
        self,
        names: tuple[str | None, ...],
        created_at: tuple[datetime | None, ...] | None = None,
    ) -> None:
        self.names = names
        self.created_at = created_at or (None,) * len(names)
        self.write_attempts = 0

    def list_all(self) -> tuple[object, ...]:
        return tuple(
            SimpleNamespace(
                input_snapshot=SimpleNamespace(enterprise_name=name),
                created_at=created_at,
            )
            for name, created_at in zip(self.names, self.created_at, strict=True)
        )

    def create(self, _record: object) -> None:
        self.write_attempts += 1
        raise AssertionError("enterprise candidate lookup must not write records")


class FakeProjectService:
    def __init__(
        self,
        projects: tuple[object, ...],
        timestamps: dict[str, datetime] | None = None,
    ) -> None:
        self.projects = projects
        self.timestamps = timestamps or {}

    def list_all(self) -> tuple[object, ...]:
        return self.projects

    def list_updated_at_by_project_id(self) -> dict[str, datetime]:
        return self.timestamps


class LegacyProjectService:
    """Older stub without the optional Application timestamp query."""

    def __init__(self, projects: tuple[object, ...]) -> None:
        self.projects = projects

    def list_all(self) -> tuple[object, ...]:
        return self.projects


def _unit(*, canonical_name: str | None = None, form_state_name: str | None = None) -> object:
    canonical = (
        SimpleNamespace(enterprise_name=canonical_name)
        if canonical_name is not None
        else None
    )
    return SimpleNamespace(
        canonical_input=canonical,
        form_state={"enterpriseNameInput": form_state_name} if form_state_name is not None else {},
    )


def _project(project_id: str, *units: object) -> object:
    return SimpleNamespace(project_id=project_id, units=units)


class EnterpriseHistoryTests(unittest.TestCase):
    def test_newer_project_is_sorted_before_yesterdays_formal_record(self) -> None:
        record_time = datetime(2026, 10, 8, 15, 0, tzinfo=UTC)
        project_time = datetime(2026, 10, 9, 8, 0, tzinfo=UTC)
        records = FakeRecordRepository(("昨日记录企业",), (record_time,))
        projects = FakeProjectService(
            (_project("project.newer", _unit(canonical_name="今日项目企业")),),
            {"project.newer": project_time},
        )

        self.assertEqual(
            list_enterprise_name_candidates(records, projects),
            ("今日项目企业", "昨日记录企业"),
        )
        self.assertEqual(records.write_attempts, 0)

    def test_equal_timestamps_keep_record_first_and_project_repository_order(self) -> None:
        shared_time = datetime(2026, 10, 9, 8, 0, tzinfo=UTC)
        older_time = datetime(2026, 10, 8, 8, 0, tzinfo=UTC)
        records = FakeRecordRepository(
            ("同名企业", "较早记录企业"),
            (shared_time, older_time),
        )
        projects = FakeProjectService(
            (
                _project("project.tie.one", _unit(canonical_name="同名企业")),
                _project("project.tie.two", _unit(form_state_name="同时间项目企业")),
            ),
            {
                "project.tie.one": shared_time,
                "project.tie.two": shared_time,
            },
        )

        self.assertEqual(
            list_enterprise_name_candidates(records, projects),
            ("同名企业", "同时间项目企业", "较早记录企业"),
        )

    def test_newer_duplicate_project_name_keeps_the_most_recent_spelling(self) -> None:
        record_time = datetime(2026, 10, 8, 8, 0, tzinfo=UTC)
        project_time = datetime(2026, 10, 9, 8, 0, tzinfo=UTC)
        records = FakeRecordRepository(("Qingzhou Carbon",), (record_time,))
        projects = FakeProjectService(
            (_project("project.same", _unit(canonical_name=" qingzhou carbon ")),),
            {"project.same": project_time},
        )

        self.assertEqual(
            list_enterprise_name_candidates(records, projects),
            ("qingzhou carbon",),
        )

    def test_canonical_project_name_takes_precedence_over_legacy_presentation_state(self) -> None:
        projects = FakeProjectService(
            (
                _project(
                    "project.canonical",
                    _unit(canonical_name="规范项目企业", form_state_name="不应采用"),
                ),
            ),
        )

        self.assertEqual(
            list_enterprise_name_candidates(project_service=projects),
            ("规范项目企业",),
        )

    def test_legacy_object_name_is_read_when_project_has_no_canonical_input(self) -> None:
        projects = LegacyProjectService(
            (_project("project.legacy", _unit(form_state_name="旧项目企业")),)
        )

        self.assertEqual(
            list_enterprise_name_candidates(project_service=projects),
            ("旧项目企业",),
        )

    def test_missing_timestamps_preserve_legacy_source_order(self) -> None:
        records = FakeRecordRepository(("记录企业",))
        projects = LegacyProjectService(
            (_project("project.legacy", _unit(form_state_name="项目企业")),)
        )

        self.assertEqual(
            list_enterprise_name_candidates(records, projects),
            ("记录企业", "项目企业"),
        )

    def test_application_service_falls_back_for_older_repository_without_timestamp_query(self) -> None:
        project = _project("project.legacy-repository", _unit(form_state_name="兼容项目企业"))

        class LegacyRepository:
            def list_all(self) -> tuple[object, ...]:
                return (project,)

        service = ProjectWorkspaceService(LegacyRepository())  # type: ignore[arg-type]
        self.assertEqual(service.list_updated_at_by_project_id(), {})
        self.assertEqual(
            list_enterprise_name_candidates(project_service=service),
            ("兼容项目企业",),
        )

    def test_case_and_whitespace_duplicates_keep_first_recent_spelling(self) -> None:
        records = FakeRecordRepository(("  Qingzhou Carbon  ",))
        projects = FakeProjectService(
            (_project("project.duplicate", _unit(form_state_name="qingzhou carbon")),),
        )

        self.assertEqual(
            list_enterprise_name_candidates(records, projects),
            ("Qingzhou Carbon",),
        )


class SharedReportExportFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_supplementary_read_failure_returns_false_before_file_or_audit(self) -> None:
        parent = QWidget()
        record = SimpleNamespace(record_id="record.supplementary.failure")
        repository = Mock()
        failing_dialog = Mock(side_effect=RuntimeError("private supplementary metadata detail"))

        with (
            patch.object(report_export.QMessageBox, "critical") as failure,
            patch.object(report_export.QFileDialog, "getSaveFileName") as file_dialog,
            patch.object(report_export, "write_report_atomically") as writer,
        ):
            result = report_export.export_saved_record_report(
                parent,
                repository,
                record,
                supplementary_dialog=failing_dialog,
            )

        self.assertFalse(result)
        failure.assert_called_once()
        self.assertEqual(failure.call_args.args[1], "报告未导出")
        self.assertIn("报告补充信息", failure.call_args.args[2])
        self.assertIn("未生成或保存", failure.call_args.args[2])
        self.assertNotIn("private supplementary metadata detail", failure.call_args.args[2])
        file_dialog.assert_not_called()
        writer.assert_not_called()
        repository.record_report_export.assert_not_called()
        parent.close()


if __name__ == "__main__":
    unittest.main()
