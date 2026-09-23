"""Deterministic construction of catalog.sqlite from the canonical JSON source."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from packages.reference_data import DEFAULT_SOURCE_PATH, load_validated_catalog

from .sqlite import initialize_database


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _insert_catalog(connection: sqlite3.Connection, catalog: dict[str, Any]) -> None:
    manifest = catalog["manifest"]
    connection.execute(
        "INSERT INTO catalog_manifest("
        "catalog_id, schema_version, data_version, app_compatibility, canonical_format, generated_from"
        ") VALUES (?, ?, ?, ?, ?, ?)",
        (
            manifest["catalog_id"],
            manifest["schema_version"],
            manifest["data_version"],
            manifest["app_compatibility"],
            manifest["canonical_format"],
            manifest["generated_from"],
        ),
    )
    for source in sorted(catalog["sources"], key=lambda item: item["source_id"]):
        connection.execute(
            "INSERT INTO source_documents("
            "source_id, source_type, document_no, document_name, publisher, publication_date, "
            "effective_from, effective_to, region, version, official_url, review_status, notes"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(source[field] for field in (
                "source_id",
                "source_type",
                "document_no",
                "document_name",
                "publisher",
                "publication_date",
                "effective_from",
                "effective_to",
                "region",
                "version",
                "official_url",
                "review_status",
                "notes",
            )),
        )
    for subject in sorted(catalog["subjects"], key=lambda item: item["subject_id"]):
        connection.execute(
            "INSERT INTO subject_catalog(subject_id, subject_type, name, aliases_json, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                subject["subject_id"],
                subject["subject_type"],
                subject["name"],
                _json(subject["aliases"]),
                subject["notes"],
            ),
        )
    for standard in sorted(catalog["standards"], key=lambda item: item["standard_id"]):
        connection.execute(
            "INSERT INTO standard_catalog("
            "standard_id, standard_number, standard_name, standard_type, version, official_status, "
            "publication_date, implementation_date, ics, ccs, issuing_authority, "
            "competent_authority, technical_committee, official_source_id, "
            "official_source_url, base_standard_ids_json, parameter_refs_json, "
            "emission_source_refs_json, calculation_status, notes"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                standard["standard_id"],
                standard["standard_number"],
                standard["standard_name"],
                standard["standard_type"],
                standard["version"],
                standard["official_status"],
                standard["publication_date"],
                standard["implementation_date"],
                standard["ics"],
                standard["ccs"],
                standard["issuing_authority"],
                standard["competent_authority"],
                standard["technical_committee"],
                standard["official_source_id"],
                standard["official_source_url"],
                _json(standard["base_standard_ids"]),
                _json(standard["parameter_refs"]),
                _json(standard["emission_source_refs"]),
                standard["calculation_status"],
                standard["notes"],
            ),
        )
    for parameter in sorted(catalog["parameters"], key=lambda item: item["parameter_id"]):
        connection.execute(
            "INSERT INTO parameter_definitions("
            "parameter_id, parameter_type, name, canonical_unit, subject_id, source_id, "
            "source_location, review_status, applicable_standard_ids_json, notes"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                parameter["parameter_id"],
                parameter["parameter_type"],
                parameter["name"],
                parameter["canonical_unit"],
                parameter["subject_id"],
                parameter["source_id"],
                parameter["source_location"],
                parameter["review_status"],
                _json(parameter["applicable_standard_ids"]),
                parameter["notes"],
            ),
        )
    for factor in sorted(catalog["factors"], key=lambda item: item["factor_id"]):
        connection.execute(
            "INSERT INTO factor_values("
            "factor_id, parameter_id, subject_id, value, unit, source_value, source_unit, "
            "normalized_value, normalized_unit, source_id, source_location, factor_year, "
            "valid_from, valid_to, value_type, review_status, applicable_standard_ids_json, notes"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                factor["factor_id"],
                factor["parameter_id"],
                factor["subject_id"],
                factor["value"],
                factor["unit"],
                factor["source_value"],
                factor["source_unit"],
                factor["normalized_value"],
                factor["normalized_unit"],
                factor["source_id"],
                factor["source_location"],
                factor["factor_year"],
                factor["valid_from"],
                factor["valid_to"],
                factor["value_type"],
                factor["review_status"],
                _json(factor["applicable_standard_ids"]),
                factor["notes"],
            ),
        )
        for standard_id in sorted(factor["applicable_standard_ids"]):
            connection.execute(
                "INSERT INTO factor_applicable_standards(factor_id, standard_id) VALUES (?, ?)",
                (factor["factor_id"], standard_id),
            )
    for rule in sorted(catalog["conversion_rules"], key=lambda item: item["conversion_id"]):
        connection.execute(
            "INSERT INTO conversion_rules("
            "conversion_id, from_unit, to_unit, multiplier, offset, source_id, source_location, "
            "review_status, notes"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(rule[field] for field in (
                "conversion_id",
                "from_unit",
                "to_unit",
                "multiplier",
                "offset",
                "source_id",
                "source_location",
                "review_status",
                "notes",
            )),
        )


def build_catalog_database(
    source_path: str | Path = DEFAULT_SOURCE_PATH,
    output_path: str | Path = "build/databases/catalog.sqlite",
    *,
    app_version: str = "1.1.0",
) -> Path:
    """Validate and atomically rebuild one catalog database."""

    catalog = load_validated_catalog(source_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        initialize_database(
            temporary_path,
            "catalog",
            app_version=app_version,
            data_version=catalog["manifest"]["data_version"],
            deterministic=True,
        )
        connection = sqlite3.connect(temporary_path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                _insert_catalog(connection, catalog)
        finally:
            connection.close()
        os.replace(temporary_path, destination)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    return destination


def build_all_databases(
    output_dir: str | Path = "build/databases",
    source_path: str | Path = DEFAULT_SOURCE_PATH,
    *,
    app_version: str = "1.1.0",
) -> dict[str, Path]:
    """Build catalog and initialize physically separate user, records and projects databases."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    catalog_path = build_catalog_database(
        source_path,
        directory / "catalog.sqlite",
        app_version=app_version,
    )
    user_path = initialize_database(
        directory / "user.sqlite",
        "user",
        app_version=app_version,
        data_version="not_applicable",
        deterministic=True,
    )
    records_path = initialize_database(
        directory / "records.sqlite",
        "records",
        app_version=app_version,
        data_version="not_applicable",
        deterministic=True,
    )
    projects_path = initialize_database(
        directory / "projects.sqlite",
        "projects",
        app_version=app_version,
        data_version="not_applicable",
        deterministic=True,
    )
    return {"catalog": catalog_path, "user": user_path, "records": records_path, "projects": projects_path}
