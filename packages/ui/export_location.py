"""Shared user-selected location policy for exported files."""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from packages.core.models import SettingEntry, Settings
from packages.core.repositories import SettingsRepository

_LOGGER = logging.getLogger(__name__)
EXPORT_DIRECTORY_SETTING_KEY = "export.directory"
_INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class ExportLocationError(RuntimeError):
    """Raised when an export location cannot be resolved safely."""


FileDialog = Callable[[QWidget, str, str, str], tuple[str, str]]


def sanitize_filename_component(
    value: object, *, fallback: str = "未命名", max_length: int = 80
) -> str:
    """Remove characters Windows cannot use in a filename."""
    text = _INVALID_FILENAME_CHARACTERS.sub("_", str(value or "").strip())
    text = re.sub(r"\s+", " ", text).strip(" .")
    if not text:
        text = fallback
    if text.upper() in _WINDOWS_RESERVED_NAMES:
        text = f"_{text}"
    return text[:max_length].rstrip(" .") or fallback


def report_export_filename(record: object) -> str:
    """Build a readable, collision-resistant name from one frozen Record."""
    snapshot = getattr(record, "input_snapshot")
    period = getattr(snapshot, "period")
    start = getattr(period, "start")
    end = getattr(period, "end")
    start_text = start.isoformat() if hasattr(start, "isoformat") else str(start)
    end_text = end.isoformat() if hasattr(end, "isoformat") else str(end)
    record_id = str(getattr(record, "record_id", "record"))
    record_short = sanitize_filename_component(record_id.rsplit(".", 1)[-1][-8:])
    standard_id = str(getattr(record, "standard_id", "标准"))
    standard_version = getattr(record, "standard_version", None)
    standard_label = (
        f"{standard_id}_{standard_version}" if standard_version else standard_id
    )
    standard = sanitize_filename_component(standard_label, max_length=48)
    enterprise = str(getattr(snapshot, "enterprise_name", "") or "").strip()
    parts = ["温室气体核算报告"]
    if enterprise:
        parts.append(sanitize_filename_component(enterprise, max_length=48))
    parts.extend(
        (
            f"{sanitize_filename_component(start_text)}_{sanitize_filename_component(end_text)}",
            standard,
            record_short,
        )
    )
    return "_".join(parts) + ".docx"


def template_export_filename(standard_id: object, template_version: object) -> str:
    """Build a Windows-safe input-template filename with its registered version."""
    standard = sanitize_filename_component(standard_id, fallback="标准", max_length=64)
    version = sanitize_filename_component(template_version, fallback="当前版本", max_length=24)
    return f"{standard}_附录B输入模板_v{version}.xlsx"


def _system_documents_location() -> Path | None:
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    return Path(location) if location else None


class ExportLocationService:
    """Resolve and persist the shared export directory preference.

    The default is resolved from the operating system Documents location. The
    directory is created only when an export is started, not when this service
    is constructed or when a setting is merely displayed.
    """

    def __init__(
        self,
        settings_repository: SettingsRepository | None = None,
        *,
        documents_location_provider: Callable[[], Path | None] | None = None,
    ) -> None:
        self.settings_repository = settings_repository
        self._documents_location_provider = (
            documents_location_provider or _system_documents_location
        )

    def documents_location(self) -> Path | None:
        return self._documents_location_provider()

    def default_directory(self) -> Path:
        documents = self.documents_location()
        if documents is None:
            raise ExportLocationError("系统未提供“文档”文件夹位置。")
        return documents / "青舟温室气体核算" / "导出文件"

    def preferred_directory(self) -> Path:
        if self.settings_repository is not None:
            settings = self.settings_repository.load()
            selected = next(
                (
                    entry.value
                    for entry in settings.entries
                    if entry.key == EXPORT_DIRECTORY_SETTING_KEY
                ),
                None,
            )
            if selected:
                directory = Path(selected).expanduser()
                if not directory.is_absolute():
                    raise ExportLocationError("已保存的导出文件夹必须是绝对路径。")
                return directory
        return self.default_directory()

    def display_directory(self) -> Path:
        """Return the active path for settings display without creating it."""
        return self.preferred_directory()

    def set_preferred_directory(self, directory: str | Path) -> Path:
        if self.settings_repository is None:
            raise ExportLocationError("用户设置存储尚未配置。")
        value = str(directory).strip()
        if not value:
            raise ExportLocationError("请选择导出文件夹。")
        selected = Path(value).expanduser()
        if not selected.is_absolute():
            raise ExportLocationError("导出文件夹必须是绝对路径。")
        current = self.settings_repository.load()
        values = {entry.key: entry.value for entry in current.entries}
        values[EXPORT_DIRECTORY_SETTING_KEY] = str(selected)
        self.settings_repository.save(
            Settings(
                settings_id=current.settings_id,
                entries=tuple(
                    SettingEntry(key, item) for key, item in sorted(values.items())
                ),
            )
        )
        return selected

    def prepare_dialog_path(self, filename: str) -> Path:
        """Create the preferred directory for an export attempt and return its target."""
        directory = self.preferred_directory()
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix=".qz-export-check-", dir=directory, delete=True
        ):
            pass
        filename_path = Path(filename).name
        stem = sanitize_filename_component(
            Path(filename_path).stem, fallback="导出文件", max_length=160
        )
        suffix = Path(filename_path).suffix
        if suffix and not re.fullmatch(r"\.[A-Za-z0-9]{1,10}", suffix):
            suffix = ""
        return directory / f"{stem}{suffix}"

    def explicit_browse_start_path(self, filename: str) -> str:
        """Start the explicit chooser in the OS Documents folder after a path failure."""
        documents = self.documents_location()
        if documents is not None:
            safe_name = sanitize_filename_component(
                Path(filename).stem, fallback="导出文件", max_length=160
            )
            suffix = Path(filename).suffix
            if suffix and not re.fullmatch(r"\.[A-Za-z0-9]{1,10}", suffix):
                suffix = ""
            return str(documents / f"{safe_name}{suffix}")
        return ""


def service_for_parent(parent: QWidget) -> ExportLocationService:
    """Read the service installed by desktop composition, with a system default."""
    direct = getattr(parent, "export_location_service", None)
    if isinstance(direct, ExportLocationService):
        return direct
    shared = getattr(parent.window(), "export_location_service", None)
    if isinstance(shared, ExportLocationService):
        return shared
    return ExportLocationService()


def _save_file_dialog(parent: QWidget, title: str, filename: str, filter_text: str) -> tuple[str, str]:
    """Defer overwrite decisions to the caller so every target is confirmed once."""
    return QFileDialog.getSaveFileName(
        parent,
        title,
        filename,
        filter_text,
        options=QFileDialog.Option.DontConfirmOverwrite,
    )


def choose_export_path(
    parent: QWidget,
    title: str,
    filename: str,
    filter_text: str,
    *,
    location_service: ExportLocationService | None = None,
    file_dialog: FileDialog | None = None,
) -> tuple[str, str]:
    """Open a save dialog with the shared path and make failures explicit."""
    service = location_service or service_for_parent(parent)
    try:
        initial_path = service.prepare_dialog_path(filename)
    except Exception:
        _LOGGER.warning("Preferred export directory is unavailable", exc_info=True)
        QMessageBox.warning(
            parent,
            "默认导出位置不可用",
            "无法创建或访问默认导出文件夹。请在随后打开的对话框中明确选择一个可写位置。",
        )
        initial_path = service.explicit_browse_start_path(filename)
    dialog = file_dialog or _save_file_dialog
    return dialog(parent, title, str(initial_path), filter_text)


def open_export_directory(directory: str | Path) -> bool:
    """Ask Windows to open the folder containing a saved export."""
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(directory).resolve()))))


def show_export_success(
    parent: QWidget,
    title: str,
    message: str,
    path: str | Path,
) -> bool:
    """Show the saved path and offer a direct action to open its folder."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(message)
    open_button = box.addButton("打开文件夹", QMessageBox.ButtonRole.AcceptRole)
    box.addButton(QMessageBox.StandardButton.Close)
    box.exec()
    if box.clickedButton() == open_button:
        return open_export_directory(Path(path).parent)
    return False


__all__ = [
    "EXPORT_DIRECTORY_SETTING_KEY",
    "ExportLocationError",
    "ExportLocationService",
    "choose_export_path",
    "open_export_directory",
    "report_export_filename",
    "sanitize_filename_component",
    "service_for_parent",
    "show_export_success",
    "template_export_filename",
]
