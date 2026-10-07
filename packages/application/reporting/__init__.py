"""Platform-independent report models and output adapters."""

from .model import REPORT_SCHEMA_VERSION, ReportCell, ReportModel, ReportRow, ReportSection, ReportTable, build_report_model
from .service import build_saved_record_report

__all__ = ["REPORT_SCHEMA_VERSION", "ReportCell", "ReportModel", "ReportRow", "ReportSection", "ReportTable", "build_report_model", "build_saved_record_report"]
