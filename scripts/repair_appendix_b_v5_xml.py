"""Narrow F01 repair of the unreleased v5 candidate; preserve all other parts."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

def repair_row_height(content: bytes) -> bytes:
    root = ET.fromstring(content)
    rows = root.findall(".//s:row[@r='20']", NS)
    if len(rows) != 1:
        raise ValueError("Expected exactly one B.2 row 20")
    text = content.decode("utf-8")
    def fix(match):
        row = match.group(0)
        for name, value in (("ht", "45"), ("customHeight", "1")):
            row, count = re.subn(r'(?<!\S)' + name + r'="[^"]*"', name + '="' + value + '"', row)
            if count != 1:
                raise ValueError("Expected exactly one complete row attribute: " + name)
        return row
    text, count = re.subn(r'<row\b(?=[^>]*\br="20")[^>]*>', fix, text)
    if count != 1:
        raise ValueError("Row 20 start tag is not unique")
    repaired = text.encode("utf-8")
    row = ET.fromstring(repaired).find(".//s:row[@r='20']", NS)
    if row.get("ht") != "45" or row.get("customHeight") != "1":
        raise ValueError("Row height repair failed")
    return repaired

def repair_workbook(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Use a separate reviewed candidate output")
    with ZipFile(source) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    if sum(info.filename == "xl/worksheets/sheet2.xml" for info, _ in entries) != 1:
        raise ValueError("Expected exactly one B.2 worksheet part")
    with ZipFile(destination, "w") as archive:
        for info, content in entries:
            if info.filename == "xl/worksheets/sheet2.xml":
                content = repair_row_height(content)
            archive.writestr(info, content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    repair_workbook(args.source, args.destination)
