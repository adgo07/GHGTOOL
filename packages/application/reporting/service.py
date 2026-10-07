"""Application boundary for reports generated from immutable saved records."""

from __future__ import annotations

from collections.abc import Mapping

from packages.core.models import AccountingRecord

from .model import ReportModel, build_report_model


def build_saved_record_report(
    repository: object,
    record: AccountingRecord,
    *,
    supplementary_info: Mapping[str, object] | None = None,
) -> ReportModel:
    """Read frozen record snapshots only; this function never invokes a calculator."""

    def read(name: str, fallback: object = None) -> object:
        method = getattr(repository, name, None)
        if not callable(method):
            return fallback
        value = method(record.record_id)
        return fallback if value is None else value

    schema = getattr(repository, "get_snapshot_schema_version", None)
    schema_version = int(schema(record.record_id)) if callable(schema) else 0
    return build_report_model(
        record,
        read("get_raw_input_snapshot", {}),
        read("get_trace_snapshot", {}),
        read("get_provenance_snapshot", {}),
        read("get_reporting_snapshot", {}),
        read("get_report_qualification", {}),
        supplementary_info=supplementary_info,
        snapshot_schema_version=schema_version,
    )


__all__ = ["build_saved_record_report"]
