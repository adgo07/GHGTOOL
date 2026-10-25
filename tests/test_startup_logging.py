"""Startup logging failures use isolated paths; never probe live user logs."""
from __future__ import annotations

from contextlib import ExitStack
import ctypes
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import Mock, patch

from apps.carbon_accounting_desktop import app as desktop
from apps.carbon_accounting_desktop.config import AppConfig


class StartupLoggingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ghg-startup-logging-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = AppConfig(
            log_directory=self.root / "logs",
            records_database=self.root / "data/records.sqlite",
            projects_database=self.root / "data/projects.sqlite",
            user_database=self.root / "data/user.sqlite",
        )

    def _common(self, stack):
        application = Mock()
        application.exec.return_value = 0
        stack.enter_context(patch.object(desktop, "QApplication", return_value=application))
        stack.enter_context(patch.object(desktop, "initialize_chinese"))
        stack.enter_context(patch.object(desktop, "report_chinese_failure"))
        stack.enter_context(patch.object(desktop, "AppConfig", return_value=self.config))
        return application

    def _assert_safe_logging_failure(self, *, injected=False, standalone=False):
        with ExitStack() as stack:
            application = self._common(stack)
            stores = [stack.enter_context(patch.object(desktop, name)) for name in (
                "SQLiteRecordRepository", "SQLiteProjectWorkspaceRepository", "SQLiteSettingsRepository",
            )]
            window = stack.enter_context(patch.object(desktop, "create_main_window"))
            critical = stack.enter_context(patch.object(desktop.QMessageBox, "critical"))
            if injected:
                stack.enter_context(patch(
                    "apps.carbon_accounting_desktop.logging_config.RotatingFileHandler",
                    side_effect=PermissionError("enterprise-secret must not appear"),
                ))
            if standalone:
                from scripts.standalone_entry import entry
                with patch("sys.argv", ["QingzhouCarbonAccounting"]):
                    result = entry()
            else:
                result = desktop.main([])
            self.assertEqual(result, 1)
            critical.assert_called_once()
            self.assertEqual(critical.call_args.args[1], "应用日志无法打开")
            message = critical.call_args.args[2]
            self.assertIn("日志文件夹", message)
            self.assertIn("核算记录和项目数据尚未打开", message)
            self.assertNotIn("enterprise-secret", message)
            for store in stores:
                store.assert_not_called()
            window.assert_not_called()
            application.exec.assert_not_called()
        self.assertFalse((self.root / "data").exists())

    def test_permission_error_from_handler_is_explained_before_stores_open(self):
        self._assert_safe_logging_failure(injected=True)

    def test_standalone_entry_returns_safe_failure_without_unhandled_exception(self):
        self._assert_safe_logging_failure(injected=True, standalone=True)
    def test_log_directory_conflicting_file_is_preserved(self):
        self.config.log_directory.write_bytes(b"existing directory-conflict evidence")
        self._assert_safe_logging_failure()
        self.assertEqual(self.config.log_directory.read_bytes(), b"existing directory-conflict evidence")

    def test_log_file_conflicting_directory_is_preserved(self):
        target = self.config.log_directory / "application.jsonl"
        target.mkdir(parents=True)
        evidence = target / "keep.txt"
        evidence.write_bytes(b"existing file-conflict evidence")
        self._assert_safe_logging_failure()
        self.assertEqual(evidence.read_bytes(), b"existing file-conflict evidence")

    @unittest.skipUnless(os.name == "nt", "Windows read-only attribute semantics")
    def test_readonly_existing_log_is_not_deleted_or_rewritten(self):
        self.config.log_directory.mkdir()
        target = self.config.log_directory / "application.jsonl"
        target.write_bytes(b"existing read-only evidence")
        target.chmod(stat.S_IREAD)
        try:
            self._assert_safe_logging_failure()
            self.assertEqual(target.read_bytes(), b"existing read-only evidence")
        finally:
            target.chmod(stat.S_IWRITE)

    @unittest.skipUnless(os.name == "nt", "Windows file sharing semantics")
    def test_exclusively_open_log_is_not_deleted_or_rewritten(self):
        from ctypes import wintypes
        self.config.log_directory.mkdir()
        target = self.config.log_directory / "application.jsonl"
        target.write_bytes(b"existing occupied evidence")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        handle = create(str(target), 0x80000000, 0, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            self._assert_safe_logging_failure()
        finally:
            self.assertTrue(close(handle))
        self.assertEqual(target.read_bytes(), b"existing occupied evidence")

    def test_writable_logs_preserve_normal_startup_and_existing_content(self):
        self.config.log_directory.mkdir()
        target = self.config.log_directory / "application.jsonl"
        original = b'{"existing":"preserve"}\n'
        target.write_bytes(original)
        with ExitStack() as stack:
            application = self._common(stack)
            window = stack.enter_context(patch.object(desktop, "create_main_window"))
            critical = stack.enter_context(patch.object(desktop.QMessageBox, "critical"))
            self.assertEqual(desktop.main([]), 0)
            critical.assert_not_called()
            application.exec.assert_called_once()
            window.return_value.show.assert_called_once()
            window.assert_called_once()
            self.assertIsNotNone(window.call_args.kwargs["record_repository"])
            self.assertIsNotNone(window.call_args.kwargs["project_service"])
        self.assertTrue(target.read_bytes().startswith(original))
        events = [json.loads(line)["event"] for line in target.read_text(encoding="utf-8").splitlines()[1:]]
        self.assertEqual(events, ["application_started", "application_exited"])
        for name in ("records", "projects", "user"):
            self.assertTrue((self.root / "data" / f"{name}.sqlite").is_file())
