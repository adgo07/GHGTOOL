"""Public frozen-report dispatch; business projection belongs to each standard."""
from .types import REPORT_SCHEMA_VERSION,ReportCell,ReportRow,ReportTable,ReportSection,ReportModel
# Compatibility helpers used by the existing carbon-material audit view.
def _display_amount(value):
    from .carbon_material_model import _display_amount as display
    return display(value)


def frozen_totals(record,trace):
    from .carbon_material_model import frozen_totals as read
    return read(record,trace)

def build_report_model(record, *args, standard_registry=None, **kwargs) -> ReportModel:
    """Dispatch frozen snapshots by recorded standard, with no catalog lookup."""
    from packages.application.standard_registry import default_standard_registry
    registry = standard_registry or default_standard_registry()
    implementation = registry.require(record.standard_id, record.standard_version)
    if implementation.report_factory is None:
        raise ValueError("此标准尚未配置核算报告。")
    return implementation.report_factory(record, *args, **kwargs)


__all__ = ["REPORT_SCHEMA_VERSION", "ReportCell", "ReportModel", "ReportRow", "ReportSection", "ReportTable", "build_report_model"]
