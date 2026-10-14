"""Presentation-independent business report data shared by all renderers."""
from dataclasses import dataclass

REPORT_SCHEMA_VERSION = "3.0.0"


@dataclass(frozen=True, slots=True)
class ReportCell:
    value: str = ""
    unit: str | None = None
    source: str | None = None
    source_detail: str | None = None


@dataclass(frozen=True, slots=True)
class ReportRow:
    cells: tuple[ReportCell, ...]
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReportTable:
    table_id: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[ReportRow, ...]
    landscape: bool = False
    header_rows: tuple[ReportRow, ...] = ()
    header_merges: tuple[tuple[int, int, int, int], ...] = ()
    body_merges: tuple[tuple[int, int, int, int], ...] = ()
    footnotes: tuple[str, ...] = ()
    column_weights: tuple[float, ...] = ()
    context_label: str | None = None


@dataclass(frozen=True, slots=True)
class ReportSection:
    section_id: str
    title: str
    tables: tuple[ReportTable, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportModel:
    schema_version: str
    record_id: str
    standard_name: str
    standard_version: str
    period_text: str
    prepared_on: str
    basic_information: tuple[tuple[str, str], ...]
    sections: tuple[ReportSection, ...]
    notices: tuple[str, ...]
    supplementary_note: str | None = None
    layout_id: str = ""
    template_sha256: str = ""
    input_template_sha256: str = ""
    input_template_version: str = ""


