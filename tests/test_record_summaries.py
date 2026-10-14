from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from packages.core.models import PeriodType, RecordStatus
from packages.persistence import SQLiteRecordRepository
from packages.ui.pages import RecordLibraryPage
from tests.test_g07_records import _record


class RecordSummaryRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_sqlite_summaries_project_list_fields_without_loading_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
            records = tuple(
                replace(
                    _record(f"summary.{index}", warning=(index == 2)),
                    created_at=base_time + timedelta(days=index),
                )
                for index in range(5)
            )
            for record in records:
                repository.create(record)
            repository.delete(records[1].record_id, actor="test", reason="summary query fixture")

            with patch.object(repository, "get", side_effect=AssertionError("list projection must not load full records")):
                summaries = repository.list_summaries()
                recent = repository.list_summaries(limit=3)

            self.assertEqual(len(summaries), 4)
            self.assertEqual([item.record_id for item in summaries], ["summary.4", "summary.3", "summary.2", "summary.0"])
            self.assertEqual([item.record_id for item in recent], ["summary.4", "summary.3", "summary.2"])
            summary = next(item for item in summaries if item.record_id == "summary.2")
            self.assertEqual(summary.enterprise_name, "G07 示例企业")
            self.assertEqual(summary.period_type, PeriodType.ANNUAL)
            self.assertEqual(summary.period_start.isoformat(), "2025-01-01")
            self.assertEqual(summary.period_end.isoformat(), "2025-12-31")
            self.assertEqual(summary.total_amount, Decimal("1.25"))
            self.assertEqual(summary.total_unit, "tCO2")
            self.assertEqual(summary.status, RecordStatus.COMPLETED_WITH_WARNINGS)


    def test_recent_summaries_sort_timezone_offsets_and_microseconds_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            fixtures = (
                (
                    "summary.offset-older-same-second",
                    datetime(2025, 1, 1, 0, 0, 0, 500000, tzinfo=timezone(timedelta(hours=2))),
                ),
                (
                    "summary.utc-newer-same-second",
                    datetime(2024, 12, 31, 22, 0, 0, 500001, tzinfo=timezone.utc),
                ),
                (
                    "summary.offset-third",
                    datetime(2025, 1, 1, 6, 59, 59, 999999, tzinfo=timezone(timedelta(hours=9))),
                ),
                (
                    "summary.offset-oldest",
                    datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone(timedelta(hours=3))),
                ),
            )
            for record_id, created_at in fixtures:
                repository.create(replace(_record(record_id), created_at=created_at))
            recent = repository.list_summaries(limit=3)
            self.assertEqual(
                [item.record_id for item in recent],
                [
                    "summary.utc-newer-same-second",
                    "summary.offset-older-same-second",
                    "summary.offset-third",
                ],
            )


    def test_record_list_refreshes_on_repository_revision_then_filters_in_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            repository.create(_record("summary.initial"))
            calls = 0
            original_reader = repository.list_summaries

            def measured_reader(limit: int | None = None):
                nonlocal calls
                calls += 1
                return original_reader(limit)

            repository.list_summaries = measured_reader
            page = RecordLibraryPage(repository)
            self.addCleanup(page.close)
            self.addCleanup(page.deleteLater)
            self.assertEqual(calls, 1)

            repository.create(_record("summary.created-after-list"))
            page.search_input.setText("summary.created-after-list")
            self.assertEqual(page.record_list.rowCount(), 1)
            self.assertEqual(page._records[0].record_id, "summary.created-after-list")
            self.assertEqual(calls, 2)

            page.search_input.setText("summary")
            self.assertEqual(page.record_list.rowCount(), 2)
            self.assertEqual(calls, 2)

    def test_record_list_detects_write_from_another_sqlite_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "records.sqlite"
            seed_repository = SQLiteRecordRepository(database_path)
            seed_repository.create(_record("summary.before-external-write"))
            repository = SQLiteRecordRepository(database_path)
            self.assertEqual(repository.revision, 0)
            external_writer = SQLiteRecordRepository(database_path)
            calls = 0
            original_reader = repository.list_summaries

            def measured_reader(limit: int | None = None):
                nonlocal calls
                calls += 1
                return original_reader(limit)

            repository.list_summaries = measured_reader
            page = RecordLibraryPage(repository)
            self.addCleanup(page.close)
            self.addCleanup(page.deleteLater)
            self.assertEqual(calls, 1)
            self.assertEqual(page.record_list.rowCount(), 1)
            self.assertEqual(
                page._records[0].record_id,
                "summary.before-external-write",
            )

            external_writer.create(_record("summary.external-write"))
            page.refresh_if_dirty()

            self.assertEqual(calls, 2)
            self.assertEqual(page.record_list.rowCount(), 2)
            self.assertIn(
                "summary.external-write",
                [item.record_id for item in page._records],
            )
            page.search_input.setText("summary.external-write")
            self.assertEqual(calls, 2)
            self.assertEqual(page.record_list.rowCount(), 1)

    def test_project_associations_are_cached_until_invalidated(self) -> None:
        class ProjectList:
            def __init__(self) -> None:
                self.calls = 0

            def list_all(self):
                self.calls += 1
                return ()

        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            repository.create(_record("summary.project-cache"))
            projects = ProjectList()
            page = RecordLibraryPage(repository, project_service=projects)
            self.addCleanup(page.close)
            self.addCleanup(page.deleteLater)

            self.assertEqual(projects.calls, 1)
            self.assertEqual(page._workspace_associations(), {})
            self.assertEqual(projects.calls, 1)

            page.invalidate_project_associations()
            self.assertEqual(page._workspace_associations(), {})
            self.assertEqual(projects.calls, 2)

    def test_summary_limit_rejects_negative_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRecordRepository(Path(directory) / "records.sqlite")
            with self.assertRaises(ValueError):
                repository.list_summaries(limit=-1)


if __name__ == "__main__":
    unittest.main()
