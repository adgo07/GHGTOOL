"""Shared Word export flow for immutable saved accounting records."""

from __future__ import annotations

from datetime import date
import hashlib
import logging
import os
from pathlib import Path
import tempfile
from typing import Protocol
from uuid import uuid4

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QWidget,
)

from packages.application.reporting import ReportModel, build_saved_record_report
from packages.core.models import AccountingRecord
from packages.core.repositories import RecordRepository
from packages.infrastructure.reporting import render_report_docx

_LOGGER = logging.getLogger(__name__)


class SupplementaryDialog(Protocol):
    def __call__(self, record: AccountingRecord) -> dict[str, object] | None: ...


class FileDialog(Protocol):
    def __call__(self, parent: QWidget, title: str, default_name: str, filter_text: str) -> tuple[str, str]: ...


class Renderer(Protocol):
    def __call__(self, model: ReportModel) -> bytes: ...


def write_report_atomically(path: Path, content: bytes) -> None:
    """Replace a target only after the complete report has been written."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".ghg-report-",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                _LOGGER.exception("Unable to remove temporary report file %s", temporary_path)
        raise


def report_supplementary_dialog(
    parent: QWidget,
    record_repository: RecordRepository,
    record: AccountingRecord,
) -> dict[str, object] | None:
    """Collect per-export details without changing the saved record."""
    reporting_getter = getattr(record_repository, "get_reporting_snapshot", None)
    reporting = reporting_getter(record.record_id) if callable(reporting_getter) else {}
    reporting = reporting if isinstance(reporting, dict) else {}
    history_getter = getattr(record_repository, "get_latest_report_export_supplementary", None)
    previous = history_getter(record.record_id) if callable(history_getter) else {}
    previous = previous if isinstance(previous, dict) else {}
    fields = (
        ("enterprise_name", "企业名称", reporting.get("enterprise_name", record.input_snapshot.enterprise_name or "")),
        ("social_credit_code", "统一社会信用代码", reporting.get("social_credit_code", "")),
        ("legal_representative", "法定代表人", reporting.get("legal_representative", "")),
        ("address", "地址", reporting.get("address", "")),
        ("contact_person", "联系人", reporting.get("contact_person", "")),
        ("preparer_name", "编制人", reporting.get("preparer_name", "")),
        ("phone", "联系电话", reporting.get("preparer_contact", "")),
        ("products_and_process", "主要产品及工艺", reporting.get("products_and_process", "")),
    )
    dialog = QDialog(parent)
    dialog.setWindowTitle("报告补充信息")
    dialog.setMinimumWidth(520)
    form = QFormLayout(dialog)
    widgets: dict[str, QLineEdit] = {}
    for key, label, fallback in fields:
        edit = QLineEdit(dialog)
        edit.setText(str(fallback or previous.get(key, "") or ""))
        widgets[key] = edit
        form.addRow(label, edit)
    prepared_on = QDateEdit(dialog)
    prepared_on.setCalendarPopup(True)
    prepared_on.setDisplayFormat("yyyy-MM-dd")
    try:
        parsed_date = QDate.fromString(str(previous.get("prepared_on") or date.today().isoformat()), "yyyy-MM-dd")
        prepared_on.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
    except ValueError:
        prepared_on.setDate(QDate.currentDate())
    form.addRow("编制日期", prepared_on)
    note = QTextEdit(dialog)
    note.setMaximumHeight(90)
    note.setPlainText(str(reporting.get("other_report_information", "") or previous.get("supplementary_note", "") or ""))
    form.addRow("补充说明", note)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    result: dict[str, object] = {key: edit.text().strip() for key, edit in widgets.items()}
    result["prepared_on"] = prepared_on.date().toString("yyyy-MM-dd")
    result["supplementary_note"] = note.toPlainText().strip()
    return result


def export_saved_record_report(
    parent: QWidget,
    record_repository: RecordRepository,
    record: AccountingRecord,
    *,
    supplementary_dialog: SupplementaryDialog | None = None,
    file_dialog: FileDialog | None = None,
    renderer: Renderer | None = None,
) -> bool:
    """Run the shared collect, render, atomic-save, and audit flow for one Record."""
    collect = supplementary_dialog or (
        lambda selected: report_supplementary_dialog(parent, record_repository, selected)
    )
    try:
        supplementary = collect(record)
    except Exception:
        _LOGGER.exception("Unable to read report supplementary information for record %s", record.record_id)
        QMessageBox.critical(
            parent,
            "报告未导出",
            "无法读取报告补充信息，报告未生成或保存，正式记录未修改。请检查后重试。",
        )
        return False
    if supplementary is None:
        return False

    suffix = ".docx"
    default_name = f"温室气体核算报告_{record.input_snapshot.period.start}_{record.input_snapshot.period.end}{suffix}"
    choose_path = file_dialog or QFileDialog.getSaveFileName
    target, _ = choose_path(parent, "保存 Word 核算报告", default_name, "Word 文档 (*.docx)")
    if not target:
        return False
    path = Path(target)
    suffix_added = path.suffix.lower() != suffix
    if suffix_added:
        path = path.with_suffix(suffix)
    if suffix_added and path.exists():
        answer = QMessageBox.question(
            parent,
            "确认覆盖文件",
            f"补全 Word 文件扩展名后的目标文件已存在：\n{path}\n是否覆盖？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False

    try:
        report = build_saved_record_report(record_repository, record, supplementary_info=supplementary)
        document_bytes = (renderer or render_report_docx)(report)
    except Exception:
        _LOGGER.exception("Unable to generate Word report for record %s", record.record_id)
        QMessageBox.critical(
            parent,
            "报告文件未保存",
            f"无法生成 Word 核算报告，文件未保存。\n目标位置：\n{path}\n请检查后重试。",
        )
        return False
    try:
        write_report_atomically(path, document_bytes)
    except Exception:
        _LOGGER.exception("Unable to write Word report for record %s to %s", record.record_id, path)
        QMessageBox.critical(
            parent,
            "报告文件未保存",
            f"无法写入 Word 核算报告，文件未保存。\n目标位置：\n{path}\n请检查文件夹和权限后重试。",
        )
        return False

    history_writer = getattr(record_repository, "record_report_export", None)
    try:
        if not callable(history_writer):
            raise RuntimeError("report export audit writer is unavailable")
        history_writer(
            record.record_id,
            export_id=f"report-export.{uuid4().hex}",
            format="DOCX",
            template_version=report.schema_version,
            document_filename=path.name,
            document_sha256=hashlib.sha256(document_bytes).hexdigest(),
            supplementary_info=supplementary,
            actor="current_user",
        )
    except Exception:
        _LOGGER.exception("Unable to record Word report export for record %s at %s", record.record_id, path)
        QMessageBox.warning(
            parent,
            "报告已保存，审计未完成",
            f"Word 核算报告已保存到：\n{path}\n该文件可使用；导出审计未完成，正式记录未改。请保留该文件，并保存诊断信息以便排查。",
        )
        return False
    QMessageBox.information(parent, "报告已导出", f"Word 核算报告已保存到：\n{path}")
    return True


__all__ = [
    "export_saved_record_report",
    "report_supplementary_dialog",
    "write_report_atomically",
]
