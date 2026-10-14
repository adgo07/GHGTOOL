"""Read-only render helpers for the same business tables consumed by Word."""
from html import escape


def cell_text(cell):
    value=cell.value
    if cell.unit:value=f"{value} {cell.unit}".strip()
    if cell.source:value=f"{value}（{cell.source}）" if value else cell.source
    return value


def report_text(model):
    output=list(model.notices)
    for section in model.sections:
        if section.section_id=="basic":continue
        output.append(section.title)
        for table in section.tables:
            if table.context_label:output.append(table.context_label)
            output.append(table.title)
            headers=table.header_rows
            output.append(" | ".join(next((row.cells[i].value for row in reversed(headers) if row.cells[i].value),table.columns[i]) for i in range(len(table.columns))))
            covered={(r,c) for top,left,bottom,right in table.body_merges for r in range(top,bottom+1) for c in range(left,right+1) if (r,c)!=(top,left)}
            for r,row in enumerate(table.rows):output.append(" | ".join("" if (r,c) in covered else cell_text(cell) for c,cell in enumerate(row.cells)))
            output.extend(table.footnotes)
        output.extend(section.notes)
        output.append("")
    return "\n".join(output)


def _table_html(table):
    def rows_html(rows,merges,header):
        starts={(top,left):(bottom-top+1,right-left+1) for top,left,bottom,right in merges}
        covered={(r,c) for top,left,bottom,right in merges for r in range(top,bottom+1) for c in range(left,right+1) if (r,c)!=(top,left)}
        output=[]
        for r,row in enumerate(rows):
            cells=[]
            for c,cell in enumerate(row.cells):
                if (r,c) in covered:continue
                height,width=starts.get((r,c),(1,1))
                style='background:#EAF1F7;font-weight:600;' if header else ''
                cells.append(f'<td rowspan="{height}" colspan="{width}" style="border:1px solid #D9D9D9;padding:6px;{style}">{escape(cell_text(cell)).replace(chr(10),"<br>")}</td>')
            output.append('<tr>'+''.join(cells)+'</tr>')
        return ''.join(output)
    from .types import ReportCell,ReportRow
    headers=table.header_rows or (ReportRow(tuple(ReportCell(value) for value in table.columns)),)
    return '<table width="100%" cellspacing="0" cellpadding="4">'+rows_html(headers,table.header_merges,True)+rows_html(table.rows,table.body_merges,False)+'</table>'


def report_html(model):
    output=['<div style="font-family:Microsoft YaHei UI;font-size:13px;color:#233749;">']
    for section in model.sections:
        if section.section_id=="basic":continue
        output.append('<h3>'+escape(section.title)+'</h3>')
        for table in section.tables:
            if table.context_label:output.append('<p><b>'+escape(table.context_label)+'</b></p>')
            output.append('<p><b>'+escape(table.title)+'</b></p>')
            output.append(_table_html(table))
            for note in table.footnotes:output.append('<p style="font-size:11px;color:#526579;">'+escape(note).replace(chr(10),'<br>')+'</p>')
        for note in section.notes:output.append('<p>'+escape(note)+'</p>')
    if model.notices:
        output.append('<h3>核算提醒</h3>')
        for notice in model.notices:output.append('<p style="color:#815A15;">'+escape(notice)+'</p>')
    output.append('</div>')
    return ''.join(output)
