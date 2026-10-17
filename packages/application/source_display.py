"""Short, display-only source labels built from frozen or catalog locators."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable


_STANDARD_NUMBER = re.compile(r"GB\s*/\s*T\s*\d+(?:\.\d+)*(?:\s*[—–-]\s*\d{4})?", re.IGNORECASE)
_PHYSICAL_PAGE = re.compile(
    r"(?:PDF\s*(?:(?:物理)?第\s*)?\d+(?:\s*[~～—–-]\s*\d+)?\s*页?"
    r"|(?:PDF\s*)?物理页\s*\d+(?:\s*[~～—–-]\s*\d+)?\s*页?"
    r"|印刷页\s*\d+(?:\s*[~～—–-]\s*\d+)?\s*页?)",
    re.IGNORECASE,
)
_LOCATOR_TOKEN = re.compile(
    r"第\s*\d+(?:\.\d+)*(?:\s*[、,，]\s*(?:第\s*)?\d+(?:\.\d+)*)*"
    r"(?:\s*[~～—–-]\s*(?:第\s*)?\d+(?:\.\d+)*)*\s*条"
    r"|附录\s*[A-Z](?:\.\d+(?:\.\d+)*)?"
    r"|表\s*[A-Z]?\d+(?:[.\-]\d+)*"
    r"|式\s*[（(]\s*\d+(?:\.\d+)*\s*[）)]"
    r"|\b[BCDE]\.\d+(?:\.\d+)*\b",
    re.IGNORECASE,
)
_TABLE_PREFIX = re.compile(r"^\s*表\s*[A-Z]?\d+(?:[.\-]\d+)*\s*[·、:：|]\s*", re.IGNORECASE)
_BRACKETED_YEAR = re.compile(r"\s*[（(]\s*(20\d{2})\s*年?\s*[）)]\s*$")
_YEAR_SUFFIX = re.compile(r"\s+(20\d{2})年\s*$")


def _text(value: object) -> str:
    if value is None:
        return ""
    value = getattr(value, "value", value)
    return str(value).strip()


def _source_name(value: object) -> str:
    if value is None:
        return ""
    document_no = _text(getattr(value, "document_no", None))
    document_name = _text(getattr(value, "document_name", None))
    if document_no and document_name:
        return f"{document_no} · {document_name}"
    return document_name or document_no or _text(value)


def _tokens(value: object) -> tuple[str, ...]:
    text = _text(value)
    if not text:
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for match in _LOCATOR_TOKEN.finditer(text):
        token = re.sub(r"\s+", "", match.group(0))
        key = token.casefold()
        if key not in seen:
            seen.add(key)
            result.append(token)
    return tuple(result)


def _locator_identity(token: str) -> str:
    return re.sub(r"^(?:附录|表)\s*", "", token, flags=re.IGNORECASE).casefold()


def strip_source_page_numbers(value: object) -> str:
    """Remove explicit PDF/printed-page citations from visible explanatory notes."""
    text = _PHYSICAL_PAGE.sub("", _text(value))
    text = re.sub(
        r"(?:[A-Z]\.\d+(?:\.\d+)*\s*)?定位\s*[:：]\s*(?=[；;、,，。]|$)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*([；;、,，])\s*([；;、,，。])", r"\2", text)
    text = re.sub(r"[；;、,，]\s*[。]", "。", text)
    text = re.sub(r"[；;、,，]{2,}", "；", text)
    text = re.sub(r"。{2,}", "。", text)
    return text.strip("；;、,，。 ")


def format_source_reference(
    source_location: object = None,
    source_name: object = None,
    *,
    clause: object = None,
    table_number: object = None,
) -> str:
    """Prefer a recorded clause/table locator; otherwise show the supplied name.

    PDF and printed-page numbers are deliberately excluded from this short label.
    Callers should retain the original source location separately for audit and
    expose it in a tooltip or a full-detail view.
    """
    location = _PHYSICAL_PAGE.sub("", _text(source_location))
    location = re.sub(r"[；;、，,|]+", "；", location).strip(" ；:：")
    standard_match = _STANDARD_NUMBER.search(location)
    standard = re.sub(r"\s+", "", standard_match.group(0)) if standard_match else ""

    locator_tokens = list(_tokens(clause)) + list(_tokens(location))
    explicit_table = _text(table_number)
    if explicit_table:
        table_tokens = _tokens(explicit_table)
        if table_tokens:
            existing = {_locator_identity(token) for token in locator_tokens}
            locator_tokens.extend(
                token for token in table_tokens
                if _locator_identity(token) not in existing
            )
        elif re.fullmatch(r"[BCDE]\.\d+(?:\.\d+)*", explicit_table, re.IGNORECASE):
            if _locator_identity(explicit_table) not in {
                _locator_identity(token) for token in locator_tokens
            }:
                locator_tokens.append(explicit_table)
        elif re.fullmatch(r"表\s*[A-Z]?\d+(?:[.\-]\d+)*", explicit_table, re.IGNORECASE):
            explicit_token = re.sub(r"\s+", "", explicit_table)
            if _locator_identity(explicit_token) not in {
                _locator_identity(token) for token in locator_tokens
            }:
                locator_tokens.append(explicit_token)

    unique: list[str] = []
    seen: set[str] = set()
    for token in locator_tokens:
        key = token.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(token)
    if unique:
        locators = "；".join(unique)
        return f"{standard} {locators}" if standard else locators

    return _source_name(source_name)


def _electricity_basis(option: object) -> str:
    label = _text(getattr(option, "label", None))
    table_number = _text(getattr(option, "table_number", None))
    if table_number:
        label = re.sub(rf"^\s*{re.escape(table_number)}\s*[·、:：|]\s*", "", label)
    else:
        label = _TABLE_PREFIX.sub("", label)
    label = _BRACKETED_YEAR.sub("", label)
    label = _YEAR_SUFFIX.sub("", label)
    label = label.strip(" ·、:：-—")
    if not label:
        label = _source_name(getattr(option, "source_document_name", None))
    return label


def electricity_factor_short_labels(options: Iterable[object]) -> tuple[str, ...]:
    """Build concise factor labels, adding year only to disambiguate same basis."""
    items = tuple(options)
    bases = tuple(_electricity_basis(item) for item in items)
    years_by_basis: dict[str, set[str]] = defaultdict(set)
    for item, basis in zip(items, bases):
        year = _text(getattr(getattr(item, "factor", None), "factor_year", None))
        if basis and year:
            years_by_basis[basis.casefold()].add(year)

    labels = []
    for item, basis in zip(items, bases):
        factor = getattr(item, "factor", None)
        value = _text(getattr(factor, "value", None))
        unit = _text(getattr(factor, "unit", None))
        label = basis
        if value or unit:
            label = f"{label}：{value} {unit}".strip(" ：")
        year = _text(getattr(factor, "factor_year", None))
        if year and len(years_by_basis.get(basis.casefold(), ())) > 1:
            label += f"（{year}年）"
        labels.append(label or "因子来源未记录")
    return tuple(labels)


__all__ = [
    "electricity_factor_short_labels",
    "format_source_reference",
    "strip_source_page_numbers",
]
