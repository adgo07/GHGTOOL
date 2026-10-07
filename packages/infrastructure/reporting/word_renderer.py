"""Word renderer for immutable application report models."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from packages.application.reporting.model import ReportCell, ReportModel, ReportTable


def _set_run_font(run, *, size: float = 10.5, bold: bool = False, color: str | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def _cell_text(cell_value: ReportCell) -> str:
    value = cell_value.value
    if cell_value.unit:
        value = f"{value} {cell_value.unit}".strip()
    if cell_value.source:
        value = f"{value}\n来源：{cell_value.source}" if value else f"来源：{cell_value.source}"
    return value


def _shade(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def _repeat_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def _page_field(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    _set_run_font(run, size=9, color="657080")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)
    run = paragraph.add_run(" 页")
    _set_run_font(run, size=9, color="657080")


def _format_section(section, landscape: bool) -> None:
    section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    if landscape:
        section.page_width, section.page_height = Cm(29.7), Cm(21)
        section.left_margin = section.right_margin = Cm(1.5)
    else:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.left_margin = section.right_margin = Cm(2.1)
    section.top_margin = section.bottom_margin = Cm(1.8)
    _page_field(section.footer.paragraphs[0])


def _add_table(document: Document, table_model: ReportTable) -> None:
    heading = document.add_paragraph()
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(table_model.title)
    _set_run_font(run, size=11, bold=True, color="214C68")
    table = document.add_table(rows=1, cols=len(table_model.columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    header = table.rows[0]
    _repeat_header(header)
    for index, title in enumerate(table_model.columns):
        cell = header.cells[index]
        cell.text = title
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _shade(cell, "E5EFF5")
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                _set_run_font(run, size=9, bold=True)
    for report_row in table_model.rows:
        cells = table.add_row().cells
        for index, cell_model in enumerate(report_row.cells[: len(cells)]):
            cells[index].text = _cell_text(cell_model)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cells[index].paragraphs:
                paragraph.paragraph_format.space_after = Pt(1)
                for run in paragraph.runs:
                    _set_run_font(run, size=8.5)
        if report_row.note:
            paragraph = document.add_paragraph(report_row.note)
            for run in paragraph.runs:
                _set_run_font(run, size=8.5, color="657080")


def render_report_docx(model: ReportModel, destination: str | Path | None = None) -> bytes:
    """Render a Word file and return its bytes; no record or calculation is modified."""

    document = Document()
    _format_section(document.sections[0], False)
    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    run = title.add_run(model.standard_name)
    _set_run_font(run, size=18, bold=True, color="173B52")
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(f"核算期间：{model.period_text}    编制日期：{model.prepared_on}")
    _set_run_font(run, size=10, color="657080")
    run = document.add_paragraph().add_run(f"适用版本：{model.standard_version}")
    _set_run_font(run, size=9, color="657080")

    current_landscape = False
    for report_section in model.sections:
        renderable_tables = tuple(table for table in report_section.tables if table.rows)
        first_orientation = renderable_tables[0].landscape if renderable_tables else current_landscape
        if report_section.section_id == "b1":
            document.add_page_break()
        if renderable_tables and first_orientation != current_landscape:
            section = document.add_section()
            _format_section(section, first_orientation)
            current_landscape = first_orientation
        heading = document.add_paragraph()
        heading.paragraph_format.keep_with_next = True
        heading.paragraph_format.space_before = Pt(13)
        run = heading.add_run(report_section.title)
        _set_run_font(run, size=14, bold=True, color="173B52")
        for table_model in report_section.tables:
            if not table_model.rows:
                empty = document.add_paragraph("该记录未保存此项明细。")
                for run in empty.runs:
                    _set_run_font(run, size=9, color="657080")
                continue
            if table_model.landscape != current_landscape:
                section = document.add_section()
                _format_section(section, table_model.landscape)
                current_landscape = table_model.landscape
            _add_table(document, table_model)
        for note in report_section.notes:
            paragraph = document.add_paragraph(note)
            for run in paragraph.runs:
                _set_run_font(run, size=9, color="657080")

    if model.notices:
        heading = document.add_paragraph()
        run = heading.add_run("核算提醒")
        _set_run_font(run, size=13, bold=True, color="8A5A00")
        for notice in model.notices:
            paragraph = document.add_paragraph(style="List Bullet")
            run = paragraph.add_run(notice)
            _set_run_font(run, size=9)
    if model.supplementary_note:
        paragraph = document.add_paragraph()
        run = paragraph.add_run("补充说明：" + model.supplementary_note)
        _set_run_font(run, size=9)
    footer = document.sections[-1].footer.paragraphs[0]
    footer.text = "本报告由已保存的核算记录生成    "
    _page_field(footer)

    output = BytesIO()
    document.save(output)
    content = output.getvalue()
    if destination is not None:
        Path(destination).write_bytes(content)
    return content


__all__ = ["render_report_docx"]
