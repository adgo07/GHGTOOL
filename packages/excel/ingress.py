"""Shared OOXML-exact ingress primitives for standard-specific Excel adapters.

This module deliberately contains no template schema or business mapping.  It
reads numeric cell lexemes from the saved OOXML package before openpyxl's float
conversion and keeps workbook/cell provenance next to normalized Decimal data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import posixpath
from typing import Mapping
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile
from io import BytesIO

from packages.application.project_workspaces import AccountingUnitType


_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


class WorkbookFatalError(ValueError):
    """The workbook cannot safely be interpreted as a supported template."""


@dataclass(frozen=True, slots=True)
class WorkbookProvenance:
    workbook_sha256: str
    template_id: str
    template_version: str
    standard_id: str
    standard_version: str
    ingress_policy_id: str
    imported_at: datetime
    canonical_path: str | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class NumericCellEvidence:
    sheet: str
    cell: str
    raw_cell_type: str
    workbook_value_repr: str
    serialized_numeric_text: str
    normalized_decimal: Decimal
    accounting_unit_id: str | None = None
    workbook_sha256: str | None = None
    canonical_path: str | None = None


@dataclass(frozen=True, slots=True)
class ImportMessage:
    code: str
    message: str
    location: str | None = None
    field_label: str | None = None


@dataclass(frozen=True, slots=True)
class UnitCalculationPreview:
    unit_id: str
    name: str
    unit_type: AccountingUnitType
    input_value: object | None
    calculation: object | None
    errors: tuple[ImportMessage, ...] = ()
    warnings: tuple[ImportMessage, ...] = ()

    @property
    def can_calculate(self) -> bool:
        return (
            self.input_value is not None
            and self.calculation is not None
            and bool(getattr(self.calculation, "successful", False))
            and not self.errors
        )

    @property
    def result(self):
        return getattr(self.calculation, "result", None) if self.can_calculate else None

    @property
    def source_breakdown(self) -> Mapping[str, Decimal]:
        if not self.can_calculate or self.calculation is None:
            return {}
        result = getattr(self.calculation, "result", None)
        if result is None:
            return {}
        from packages.standards.carbon_material import (
            SOURCE_BAKING,
            SOURCE_CALCINATION,
            SOURCE_EXPORTED_ELECTRICITY,
            SOURCE_EXPORTED_HEAT,
            SOURCE_FGD,
            SOURCE_FUME,
            SOURCE_FUEL,
            SOURCE_GRAPHITIZATION,
            SOURCE_PURCHASED_ELECTRICITY,
            SOURCE_PURCHASED_HEAT,
        )
        from packages.core.decimal_policy import DecimalPolicy

        source_ids = (
            SOURCE_FUEL, SOURCE_CALCINATION, SOURCE_BAKING, SOURCE_GRAPHITIZATION,
            SOURCE_FUME, SOURCE_FGD, SOURCE_PURCHASED_ELECTRICITY,
            SOURCE_PURCHASED_HEAT, SOURCE_EXPORTED_ELECTRICITY, SOURCE_EXPORTED_HEAT,
        )
        totals = {source_id: Decimal(0) for source_id in source_ids}
        policy = DecimalPolicy()
        for line in result.lines:
            source_id = getattr(line, "emission_source_id", None)
            if source_id in totals:
                totals[source_id] = policy.add(totals[source_id], line.amount)
        return totals


@dataclass(frozen=True, slots=True)
class WorkbookImportPreview:
    provenance: WorkbookProvenance
    units: tuple[UnitCalculationPreview, ...]
    warnings: tuple[ImportMessage, ...]
    numeric_evidence: tuple[NumericCellEvidence, ...]


def significant_digit_count(value: Decimal) -> int:
    if not value.is_finite():
        raise ValueError("numeric value must be finite")
    digits = list(value.as_tuple().digits)
    while len(digits) > 1 and digits[0] == 0:
        digits.pop(0)
    return len(digits) if any(digits) else 1


def read_worksheet_numeric_lexemes(source: bytes) -> dict[tuple[str, str], str]:
    """Return saved numeric <v> text indexed by (sheet name, cell ref)."""
    try:
        with ZipFile(BytesIO(source)) as archive:
            workbook_root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            rels_root = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            targets = {
                node.attrib["Id"]: node.attrib["Target"]
                for node in rels_root.findall(f"{{{_NS_PKG_REL}}}Relationship")
            }
            values: dict[tuple[str, str], str] = {}
            for node in workbook_root.findall(f"{{{_NS_MAIN}}}sheets/{{{_NS_MAIN}}}sheet"):
                sheet_name = node.attrib["name"]
                target = targets[node.attrib[f"{{{_NS_REL}}}id"]]
                if target.startswith("/"):
                    member = target.lstrip("/")
                else:
                    member = posixpath.normpath(posixpath.join("xl", target))
                root = ElementTree.fromstring(archive.read(member))
                for cell in root.findall(f".//{{{_NS_MAIN}}}c"):
                    reference = cell.attrib.get("r")
                    if not reference or cell.attrib.get("t") not in (None, "n"):
                        continue
                    value = cell.find(f"{{{_NS_MAIN}}}v")
                    if value is not None and value.text is not None:
                        values[(sheet_name, reference)] = value.text
            return values
    except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise WorkbookFatalError("文件不是可读取的 Excel 工作簿，或内部 OOXML 结构已损坏。") from exc


class WorkbookCellReader:
    """Read input cells while preserving the original OOXML Decimal lexeme."""

    def __init__(
        self,
        source: bytes,
        *,
        workbook_sha256: str,
        canonical_path: str | None = None,
    ) -> None:
        self.numeric_lexemes = read_worksheet_numeric_lexemes(source)
        self.workbook_sha256 = workbook_sha256
        self.canonical_path = canonical_path
        self.evidence: list[NumericCellEvidence] = []

    @staticmethod
    def _location(sheet: str, cell: str) -> str:
        return f"{sheet}!{cell}"

    def _evidence(self, sheet: str, cell_ref: str, cell, serialized: str, value: Decimal) -> None:
        self.evidence.append(NumericCellEvidence(
            sheet=sheet,
            cell=cell_ref,
            raw_cell_type=str(cell.data_type),
            workbook_value_repr=repr(cell.value),
            serialized_numeric_text=serialized,
            normalized_decimal=value,
            accounting_unit_id=None,
            workbook_sha256=self.workbook_sha256,
            canonical_path=self.canonical_path,
        ))

    def number(
        self,
        workbook,
        sheet: str,
        cell_ref: str,
        errors: list[ImportMessage],
        *,
        required: bool = False,
        field_label: str | None = None,
    ) -> Decimal | None:
        cell = workbook[sheet][cell_ref]
        location = self._location(sheet, cell_ref)
        if cell.data_type == "f":
            errors.append(ImportMessage(
                "EXB01_FORMULA_REJECTED",
                "输入值不接受 Excel 公式；请填写固定数值。",
                location,
                field_label,
            ))
            return None
        serialized = self.numeric_lexemes.get((sheet, cell_ref))
        if cell.value is None and serialized is None:
            if required:
                errors.append(ImportMessage(
                    "EXB01_NUMBER_REQUIRED",
                    "请填写此数值；空白表示未提供，0 表示明确为零。",
                    location,
                    field_label,
                ))
            return None
        if cell.data_type != "n" or isinstance(cell.value, (bool, datetime)):
            errors.append(ImportMessage(
                "EXB01_NUMERIC_CELL_REQUIRED",
                "此字段必须是 Excel 数值单元格；文本数字、公式和日期不能作为数值输入。",
                location,
                field_label,
            ))
            return None
        if serialized is None:
            errors.append(ImportMessage(
                "EXB01_NUMERIC_SERIALIZATION_MISSING",
                "无法读取此数值在工作簿中的原始保存内容。",
                location,
                field_label,
            ))
            return None
        try:
            value = Decimal(serialized)
        except InvalidOperation:
            errors.append(ImportMessage(
                "EXB01_NUMBER_INVALID",
                "此数值不是有效的十进制数。",
                location,
                field_label,
            ))
            return None
        self._evidence(sheet, cell_ref, cell, serialized, value)
        if not value.is_finite():
            errors.append(ImportMessage(
                "EXB01_NUMBER_NONFINITE",
                "NaN 和 Infinity 不能作为核算输入。",
                location,
                field_label,
            ))
            return None
        digits = significant_digit_count(value)
        if digits > 15:
            errors.append(ImportMessage(
                "EXB01_NUMBER_SIGNIFICANT_DIGITS",
                f"此数值有 {digits} 位有效数字；Excel 入口最多接受 15 位。",
                location,
                field_label,
            ))
            return None
        return value

    def text(
        self,
        workbook,
        sheet: str,
        cell_ref: str,
        errors: list[ImportMessage],
        *,
        required: bool = False,
        field_label: str | None = None,
    ) -> str | None:
        cell = workbook[sheet][cell_ref]
        location = self._location(sheet, cell_ref)
        if cell.data_type == "f":
            errors.append(ImportMessage(
                "EXB01_FORMULA_REJECTED",
                "此字段不接受公式，请填写固定文字。",
                location,
                field_label,
            ))
            return None
        if cell.value is None:
            if required:
                errors.append(ImportMessage("EXB01_TEXT_REQUIRED", "请填写此字段。", location, field_label))
            return None
        if not isinstance(cell.value, str):
            errors.append(ImportMessage(
                "EXB01_TEXT_CELL_REQUIRED",
                "此字段必须以文字填写。",
                location,
                field_label,
            ))
            return None
        value = cell.value.strip()
        if required and not value:
            errors.append(ImportMessage("EXB01_TEXT_REQUIRED", "请填写此字段。", location, field_label))
        return value or None

    def observe_unused(
        self,
        workbook,
        sheet: str,
        cell_ref: str,
        warnings: list[ImportMessage],
        *,
        field_label: str | None = None,
        reason: str = "此字段不参与当前选择的数据路径；原始数值已保留为证据。",
    ) -> Decimal | None:
        """Keep numeric evidence for a display-only branch without using it."""
        cell = workbook[sheet][cell_ref]
        if cell.value is None:
            return None
        location = self._location(sheet, cell_ref)
        if cell.data_type == "f":
            warnings.append(ImportMessage(
                "EXB01_UNUSED_FORMULA",
                "此字段位于当前不采用的数据路径中，公式未作为输入使用。",
                location,
                field_label,
            ))
            return None
        serialized = self.numeric_lexemes.get((sheet, cell_ref))
        if cell.data_type == "n" and serialized is not None and not isinstance(cell.value, (bool, datetime)):
            try:
                value = Decimal(serialized)
            except InvalidOperation:
                value = None
            if value is not None:
                self._evidence(sheet, cell_ref, cell, serialized, value)
                warnings.append(ImportMessage("EXB01_UNUSED_VALUE", reason, location, field_label))
                return value
        warnings.append(ImportMessage(
            "EXB01_UNUSED_VALUE",
            reason + " 当前内容未作为输入使用。",
            location,
            field_label,
        ))
        return None


__all__ = [
    "ImportMessage",
    "NumericCellEvidence",
    "UnitCalculationPreview",
    "WorkbookCellReader",
    "WorkbookFatalError",
    "WorkbookImportPreview",
    "WorkbookProvenance",
    "read_worksheet_numeric_lexemes",
    "significant_digit_count",
]

