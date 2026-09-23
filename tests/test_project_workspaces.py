from __future__ import annotations

from dataclasses import replace
import sqlite3
import tempfile
import unittest
from pathlib import Path

from packages.application import (
    AccountingUnitType,
    AccountingUnitWorkspace,
    ProjectWorkspace,
    ProjectWorkspaceService,
)
from packages.persistence import (
    MigrationError,
    ProjectWorkspaceRepositoryError,
    SQLiteProjectWorkspaceRepository,
    build_all_databases,
)


class ProjectWorkspacePersistenceTests(unittest.TestCase):
    def test_multiple_units_round_trip_and_project_deletion_never_touches_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = build_all_databases(directory)
            records = sqlite3.connect(paths["records"])
            try:
                records.execute(
                    "INSERT INTO accounting_records(record_id,status,created_at,standard_id,"
                    "standard_version,algorithm_version,input_snapshot_json,calculation_snapshot_json,"
                    "parameter_snapshot_json,warnings_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        "record.immutable",
                        "COMPLETED",
                        "2026-09-23T00:00:00+00:00",
                        "gbt_32151_34_2024",
                        "2024",
                        "algorithm.1",
                        "{}",
                        "{}",
                        "[]",
                        "[]",
                    ),
                )
                records.execute(
                    "INSERT INTO audit_log(audit_id,record_id,action,occurred_at,actor,details_json) "
                    "VALUES(?,?,?,?,?,?)",
                    ("audit.immutable", "record.immutable", "CREATE", "2026-09-23T00:00:00+00:00", "test", "{}"),
                )
                records.commit()
            finally:
                records.close()

            service = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(paths["projects"]))
            initial = service.new_workspace("炭素材料企业 2025")
            whole_site = replace(
                initial.units[0],
                form_state={"enterprise_name": "炭素材料企业", "fuel_rows": [{"row_id": "fuel-row-1", "kind": "天然气"}]},
                result_snapshot={"total": "12.345", "unit": "tCO₂"},
                record_ids=("record.immutable",),
            )
            process = AccountingUnitWorkspace(
                unit_id="unit.graphitization",
                name="石墨化工序",
                unit_type=AccountingUnitType.PROCESS,
                position=1,
                form_state={"source_enabled": {"P03": True}, "graphitization": {"gc": "100"}},
                result_snapshot={"total": "8.000", "unit": "tCO₂"},
                record_ids=("record.process",),
                input_fingerprint="fingerprint.process",
            )
            workspace = replace(
                initial,
                active_unit_id=process.unit_id,
                units=(whole_site, process),
            )
            service.save(workspace)

            reloaded = service.get(workspace.project_id)
            self.assertEqual(reloaded, workspace)
            self.assertEqual(service.list_all(), (workspace,))
            self.assertTrue(service.delete(workspace.project_id))
            self.assertIsNone(service.get(workspace.project_id))

            records = sqlite3.connect(paths["records"])
            try:
                self.assertEqual(records.execute("SELECT COUNT(*) FROM accounting_records").fetchone()[0], 1)
                self.assertEqual(records.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 1)
            finally:
                records.close()

    def test_a_project_cannot_be_saved_without_a_unit_or_valid_active_unit(self) -> None:
        with self.assertRaises(ValueError):
            ProjectWorkspace("project.bad", "Bad", "missing", ())

    def test_project_migration_errors_fail_safely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            SQLiteProjectWorkspaceRepository(database)
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "INSERT INTO schema_migrations(version,name,applied_at) VALUES(?,?,?)",
                    (999, "future_migration", "2099-01-01T00:00:00+00:00"),
                )
                connection.commit()
            finally:
                connection.close()
            with self.assertRaises(MigrationError):
                SQLiteProjectWorkspaceRepository(database)

            unopenable = Path(directory) / "unopenable.sqlite"
            unopenable.mkdir()
            with self.assertRaises(MigrationError):
                SQLiteProjectWorkspaceRepository(unopenable)

    def test_corrupt_workspace_json_is_reported_without_partial_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            workspace = ProjectWorkspaceService.new_workspace("损坏项目")
            repository.save(workspace)
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "UPDATE accounting_units SET form_state_json=? WHERE unit_id=?",
                    ("{broken-json", workspace.active_unit_id),
                )
                connection.commit()
            finally:
                connection.close()

            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "invalid project JSON"):
                repository.list_all()
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "invalid project JSON"):
                repository.get(workspace.project_id)

    def test_pending_record_link_recovers_after_project_save_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("关联恢复项目")
            unit = replace(
                initial.units[0],
                form_state={"enterpriseNameInput": "恢复企业"},
                result_snapshot={"record_id": "record.recover", "total": "1"},
                record_ids=("record.recover",),
                input_fingerprint="fingerprint.recover",
            )
            workspace = replace(initial, units=(unit,))
            original_save = repository.save
            repository.save = lambda _workspace: (_ for _ in ()).throw(  # type: ignore[method-assign]
                ProjectWorkspaceRepositoryError("simulated project write failure")
            )
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "queued for recovery"):
                repository.save_after_record(workspace, "record.recover")
            repository.save = original_save  # type: ignore[method-assign]

            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute("SELECT record_id FROM pending_record_links").fetchall(),
                    [("record.recover",)],
                )
            finally:
                connection.close()

            recovered = SQLiteProjectWorkspaceRepository(database)
            self.assertEqual(recovered.get(workspace.project_id), workspace)
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM pending_record_links").fetchone()[0],
                    0,
                )
            finally:
                connection.close()

    def test_pending_marker_clear_failure_does_not_overwrite_newer_explicit_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("original")
            linked_unit = replace(
                initial.units[0],
                form_state={"enterprise_name": "original input"},
                result_snapshot={"record_id": "record.clear", "total": "1"},
                record_ids=("record.clear",),
                input_fingerprint="fingerprint.clear",
            )
            linked = replace(initial, units=(linked_unit,))
            original_clear = repository._clear_pending_link
            repository._clear_pending_link = lambda _record_id: (_ for _ in ()).throw(  # type: ignore[method-assign]
                ProjectWorkspaceRepositoryError("simulated marker clear failure")
            )
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "clear failure"):
                repository.save_after_record(linked, "record.clear")
            repository._clear_pending_link = original_clear  # type: ignore[method-assign]

            newer_unit = replace(
                linked_unit,
                form_state={"enterprise_name": "newer input"},
            )
            newer = replace(linked, name="newer explicit save", units=(newer_unit,))
            repository.save(newer)

            reopened = SQLiteProjectWorkspaceRepository(database)
            recovered = reopened.get(initial.project_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.name, "newer explicit save")
            self.assertEqual(recovered.units[0].form_state, {"enterprise_name": "newer input"})
            self.assertEqual(recovered.units[0].record_ids, ("record.clear",))
            self.assertEqual(recovered.units[0].result_snapshot, linked_unit.result_snapshot)
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM pending_record_links").fetchone()[0],
                    0,
                )
            finally:
                connection.close()

    def test_pending_link_merges_into_newer_save_without_replacing_project_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("original")
            repository.save(initial)
            pending_unit = replace(
                initial.units[0],
                form_state={"enterprise_name": "calculated input"},
                result_snapshot={"record_id": "record.merge", "total": "2"},
                record_ids=("record.merge",),
                input_fingerprint="fingerprint.merge",
            )
            pending = replace(initial, units=(pending_unit,))
            original_save = repository.save
            repository.save = lambda _workspace: (_ for _ in ()).throw(  # type: ignore[method-assign]
                ProjectWorkspaceRepositoryError("simulated project write failure")
            )
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "queued for recovery"):
                repository.save_after_record(pending, "record.merge")
            repository.save = original_save  # type: ignore[method-assign]

            newer_unit = replace(
                initial.units[0],
                form_state={"enterprise_name": "newer input"},
            )
            newer = replace(initial, name="newer explicit save", units=(newer_unit,))
            repository.save(newer)

            reopened = SQLiteProjectWorkspaceRepository(database)
            recovered = reopened.get(initial.project_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.name, "newer explicit save")
            self.assertEqual(recovered.units[0].form_state, {"enterprise_name": "newer input"})
            self.assertEqual(recovered.units[0].record_ids, ("record.merge",))
            self.assertEqual(recovered.units[0].result_snapshot, pending_unit.result_snapshot)
            self.assertEqual(recovered.units[0].input_fingerprint, "fingerprint.merge")
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM pending_record_links").fetchone()[0],
                    0,
                )
            finally:
                connection.close()

    def test_pending_link_keeps_a_later_explicitly_saved_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("original")
            repository.save(initial)
            pending_unit = replace(
                initial.units[0],
                result_snapshot={"record_id": "record.pending", "total": "2"},
                record_ids=("record.pending",),
                input_fingerprint="fingerprint.pending",
            )
            pending = replace(initial, units=(pending_unit,))
            original_save = repository.save
            repository.save = lambda _workspace: (_ for _ in ()).throw(  # type: ignore[method-assign]
                ProjectWorkspaceRepositoryError("simulated project write failure")
            )
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "queued for recovery"):
                repository.save_after_record(pending, "record.pending")
            repository.save = original_save  # type: ignore[method-assign]

            later_result = {"record_id": "record.later", "total": "3"}
            later_unit = replace(
                initial.units[0],
                form_state={"enterprise_name": "later input"},
                result_snapshot=later_result,
                record_ids=("record.later",),
                input_fingerprint="fingerprint.later",
            )
            repository.save(replace(initial, name="later project", units=(later_unit,)))

            reopened = SQLiteProjectWorkspaceRepository(database)
            recovered = reopened.get(initial.project_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.name, "later project")
            self.assertEqual(recovered.units[0].form_state, {"enterprise_name": "later input"})
            self.assertEqual(
                recovered.units[0].record_ids,
                ("record.pending", "record.later"),
            )
            self.assertEqual(recovered.units[0].result_snapshot, later_result)
            self.assertEqual(recovered.units[0].input_fingerprint, "fingerprint.later")


if __name__ == "__main__":
    unittest.main()
