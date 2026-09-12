"""Read-only SQLite implementation of the G04 catalog repository."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from packages.core.models import OfficialStatus, ParameterType, ReviewStatus, SourceType, ValueType
from packages.standards.catalog import (
    CatalogRepository,
    CatalogStandardType,
    FactorCatalogRecord,
    ParameterCatalogRecord,
    SourceCatalogRecord,
    StandardCatalogRecord,
    SubjectCatalogRecord,
)


class CatalogRepositoryError(RuntimeError):
    """Raised when the read-only catalog database cannot be consumed safely."""


def _date(value: str | None) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CatalogRepositoryError(f"invalid catalog date: {value!r}") from exc


def _required_date(value: str | None, field: str) -> date:
    parsed = _date(value)
    if parsed is None:
        raise CatalogRepositoryError(f"catalog field {field!r} is required")
    return parsed


def _tuple_json(value: str, field: str) -> tuple[str, ...]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise CatalogRepositoryError(f"invalid JSON in catalog field {field!r}") from exc
    if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
        raise CatalogRepositoryError(f"catalog field {field!r} must be a string array")
    return tuple(decoded)


class SQLiteCatalogRepository(CatalogRepository):
    """Load catalog rows without giving the presentation layer SQLite access."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise CatalogRepositoryError(f"catalog database does not exist: {self.path}")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = sqlite3.connect(
                f"{self.path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
            connection.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise CatalogRepositoryError(f"cannot open catalog database: {self.path}") from exc
        try:
            yield connection
        except sqlite3.Error as exc:
            raise CatalogRepositoryError("catalog query failed") from exc
        finally:
            connection.close()

    def list_sources(self) -> tuple[SourceCatalogRecord, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT source_id, source_type, document_no, document_name, publisher, "
                "publication_date, effective_from, effective_to, region, version, "
                "official_url, review_status, notes FROM source_documents ORDER BY source_id"
            ).fetchall()
        return tuple(
            SourceCatalogRecord(
                source_id=row["source_id"],
                source_type=SourceType(row["source_type"]),
                document_no=row["document_no"],
                document_name=row["document_name"],
                publisher=row["publisher"],
                publication_date=_required_date(row["publication_date"], "publication_date"),
                effective_from=_date(row["effective_from"]),
                effective_to=_date(row["effective_to"]),
                region=row["region"],
                version=row["version"],
                official_url=row["official_url"],
                review_status=ReviewStatus(row["review_status"]),
                notes=row["notes"],
            )
            for row in rows
        )

    def list_subjects(self) -> tuple[SubjectCatalogRecord, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT subject_id, subject_type, name, aliases_json, notes "
                "FROM subject_catalog ORDER BY name, subject_id"
            ).fetchall()
        return tuple(
            SubjectCatalogRecord(
                subject_id=row["subject_id"],
                subject_type=row["subject_type"],
                name=row["name"],
                aliases=_tuple_json(row["aliases_json"], "aliases_json"),
                notes=row["notes"],
            )
            for row in rows
        )

    def list_standards(self) -> tuple[StandardCatalogRecord, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT standard_id, standard_number, standard_name, standard_type, version, "
                "official_status, publication_date, implementation_date, ics, ccs, "
                "issuing_authority, competent_authority, technical_committee, "
                "official_source_id, official_source_url, base_standard_ids_json, "
                "parameter_refs_json, emission_source_refs_json, calculation_status, notes "
                "FROM standard_catalog ORDER BY standard_number, standard_id"
            ).fetchall()
        return tuple(
            StandardCatalogRecord(
                standard_id=row["standard_id"],
                standard_number=row["standard_number"],
                standard_name=row["standard_name"],
                standard_type=CatalogStandardType(row["standard_type"]),
                version=row["version"],
                official_status=OfficialStatus(row["official_status"]),
                publication_date=_required_date(row["publication_date"], "publication_date"),
                implementation_date=_required_date(row["implementation_date"], "implementation_date"),
                ics=row["ics"],
                ccs=row["ccs"],
                issuing_authority=row["issuing_authority"],
                competent_authority=row["competent_authority"],
                technical_committee=row["technical_committee"],
                official_source_id=row["official_source_id"],
                official_source_url=row["official_source_url"],
                base_standard_ids=_tuple_json(row["base_standard_ids_json"], "base_standard_ids_json"),
                parameter_refs=_tuple_json(row["parameter_refs_json"], "parameter_refs_json"),
                emission_source_refs=_tuple_json(row["emission_source_refs_json"], "emission_source_refs_json"),
                calculation_status=row["calculation_status"],
                notes=row["notes"],
            )
            for row in rows
        )

    def list_parameters(self) -> tuple[ParameterCatalogRecord, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT parameter_id, parameter_type, name, canonical_unit, subject_id, "
                "source_id, source_location, review_status, applicable_standard_ids_json, notes "
                "FROM parameter_definitions ORDER BY name, parameter_id"
            ).fetchall()
        return tuple(
            ParameterCatalogRecord(
                parameter_id=row["parameter_id"],
                parameter_type=ParameterType(row["parameter_type"]),
                name=row["name"],
                canonical_unit=row["canonical_unit"],
                subject_id=row["subject_id"],
                source_id=row["source_id"],
                source_location=row["source_location"],
                review_status=ReviewStatus(row["review_status"]),
                applicable_standard_ids=_tuple_json(
                    row["applicable_standard_ids_json"], "applicable_standard_ids_json"
                ),
                notes=row["notes"],
            )
            for row in rows
        )

    def list_factors(self) -> tuple[FactorCatalogRecord, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT factor_id, parameter_id, subject_id, value, unit, source_value, "
                "source_unit, normalized_value, normalized_unit, source_id, source_location, "
                "factor_year, valid_from, valid_to, value_type, review_status, "
                "applicable_standard_ids_json, notes FROM factor_values "
                "ORDER BY parameter_id, factor_year DESC, factor_id"
            ).fetchall()
        try:
            return tuple(
                FactorCatalogRecord(
                    factor_id=row["factor_id"],
                    parameter_id=row["parameter_id"],
                    subject_id=row["subject_id"],
                    value=Decimal(row["value"]),
                    unit=row["unit"],
                    source_value=Decimal(row["source_value"]),
                    source_unit=row["source_unit"],
                    normalized_value=Decimal(row["normalized_value"]),
                    normalized_unit=row["normalized_unit"],
                    source_id=row["source_id"],
                    source_location=row["source_location"],
                    factor_year=int(row["factor_year"]),
                    valid_from=_date(row["valid_from"]),
                    valid_to=_date(row["valid_to"]),
                    value_type=ValueType(row["value_type"]),
                    review_status=ReviewStatus(row["review_status"]),
                    applicable_standard_ids=_tuple_json(
                        row["applicable_standard_ids_json"], "applicable_standard_ids_json"
                    ),
                    notes=row["notes"],
                )
                for row in rows
            )
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise CatalogRepositoryError("invalid numeric or enum value in catalog") from exc


class EmptyCatalogRepository(CatalogRepository):
    """Safe empty fallback for a first launch before a catalog is installed."""

    def list_standards(self) -> tuple[StandardCatalogRecord, ...]:
        return ()

    def list_sources(self) -> tuple[SourceCatalogRecord, ...]:
        return ()

    def list_subjects(self) -> tuple[SubjectCatalogRecord, ...]:
        return ()

    def list_parameters(self) -> tuple[ParameterCatalogRecord, ...]:
        return ()

    def list_factors(self) -> tuple[FactorCatalogRecord, ...]:
        return ()
