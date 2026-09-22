"""Validate a Windows standalone artifact before delivery.

The audit is intentionally conservative: only the packaged catalog is allowed to
be a SQLite database, and source documents, user data, test data, and secrets
must not be present in the release directory.
"""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


APP_EXECUTABLE = "QingzhouCarbonAccounting.exe"
MANIFEST_NAME = "build-manifest.json"
ALLOWED_SQLITE = Path("databases/catalog.sqlite")
FORBIDDEN_SUFFIXES = frozenset(
    {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".pem", ".key", ".p12"}
)
FORBIDDEN_PARTS = frozenset(
    {"tests", "test", "计算表", ".venv", "tmp", "data-source", ".git", ".github"}
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_files(root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path.relative_to(root)
            for path in root.rglob("*")
            if path.is_file() and path.name != MANIFEST_NAME
        )
    )


def _check_catalog(path: Path, issues: list[str]) -> None:
    if not path.is_file():
        issues.append("missing packaged databases/catalog.sqlite")
        return
    try:
        uri = f"file:{path.as_posix()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM database_metadata"))
            catalog_row = connection.execute(
                "SELECT schema_version, data_version, app_compatibility "
                "FROM catalog_manifest LIMIT 1"
            ).fetchone()
            catalog_metadata = (
                {
                    "schema_version": str(catalog_row[0]),
                    "data_version": str(catalog_row[1]),
                    "app_compatibility": str(catalog_row[2]),
                }
                if catalog_row
                else {}
            )
            standard_count = int(
                connection.execute("SELECT COUNT(*) FROM standard_catalog").fetchone()[0]
            )
            table_names = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        issues.append(f"catalog read-only validation failed: {exc}")
        return

    if metadata.get("schema_version") != "001":
        issues.append(f"unexpected catalog database schema version: {metadata.get('schema_version')!r}")
    if metadata.get("app_version") != "1.1.0":
        issues.append(f"unexpected catalog app version: {metadata.get('app_version')!r}")
    if catalog_metadata.get("schema_version") != "1.0.0":
        issues.append(f"unexpected canonical schema version: {catalog_metadata.get('schema_version')!r}")
    if catalog_metadata.get("app_compatibility") != "1.x":
        issues.append(
            f"unexpected catalog app compatibility: {catalog_metadata.get('app_compatibility')!r}"
        )
    if not catalog_metadata.get("data_version"):
        issues.append("catalog data version is empty")
    if standard_count != 9:
        issues.append(f"expected 9 catalog standards, found {standard_count}")
    if {"accounting_records", "audit_log"} & table_names:
        issues.append("release catalog contains records tables")


def inspect_release(root: str | Path) -> tuple[str, ...]:
    """Return all release-audit findings; an empty tuple means PASS."""

    artifact = Path(root)
    issues: list[str] = []
    if not artifact.is_dir():
        return (f"release directory does not exist: {artifact}",)

    executable = artifact / APP_EXECUTABLE
    if not executable.is_file():
        issues.append(f"missing {APP_EXECUTABLE}")

    _check_catalog(artifact / ALLOWED_SQLITE, issues)
    for path in _relative_files(artifact):
        relative = Path(path)
        normalized = relative.as_posix()
        lower = normalized.lower()
        parts = {part.lower() for part in relative.parts}
        if parts & {part.lower() for part in FORBIDDEN_PARTS}:
            issues.append(f"forbidden development or user-data path: {normalized}")
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
            issues.append(f"forbidden source/document/secret file: {normalized}")
        if relative.suffix.lower() in {".sqlite", ".db"} and relative != ALLOWED_SQLITE:
            issues.append(f"unexpected database file: {normalized}")
        if lower.endswith(".env") or lower.endswith(".env.local"):
            issues.append(f"forbidden environment file: {normalized}")

    manifest_path = artifact / MANIFEST_NAME
    if not manifest_path.is_file():
        issues.append(f"missing {MANIFEST_NAME}")
        return tuple(dict.fromkeys(issues))

    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"invalid {MANIFEST_NAME}: {exc}")
        return tuple(dict.fromkeys(issues))

    for field in (
        "manifest_version",
        "artifact_name",
        "app_version",
        "catalog_schema_version",
        "catalog_data_version",
        "source_commit",
        "pr_head_sha",
        "tested_merge_sha",
        "files",
    ):
        if field not in manifest:
            issues.append(f"manifest missing field: {field}")

    if manifest.get("manifest_version") != 1:
        issues.append("unsupported release manifest version")
    if manifest.get("artifact_name") != "QingzhouCarbonAccounting":
        issues.append("unexpected release artifact name")
    if manifest.get("app_version") != "1.1.0":
        issues.append(f"unexpected manifest app version: {manifest.get('app_version')!r}")
    for provenance_field in ("source_commit", "pr_head_sha", "tested_merge_sha"):
        if not isinstance(manifest.get(provenance_field), str) or not manifest[provenance_field].strip():
            issues.append(f"manifest has empty provenance field: {provenance_field}")

    actual_files = {path.as_posix() for path in _relative_files(artifact)}
    manifest_files: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("files", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            issues.append("manifest contains an invalid file entry")
            continue
        manifest_files[entry["path"]] = entry

    if actual_files != set(manifest_files):
        missing = sorted(actual_files - set(manifest_files))
        extra = sorted(set(manifest_files) - actual_files)
        if missing:
            issues.append(f"manifest omits files: {missing[:5]}")
        if extra:
            issues.append(f"manifest lists missing files: {extra[:5]}")

    for relative, entry in manifest_files.items():
        path = artifact / Path(relative)
        if not path.is_file():
            continue
        expected_hash = entry.get("sha256")
        if expected_hash != _sha256(path):
            issues.append(f"manifest hash mismatch: {relative}")
        if entry.get("size") != path.stat().st_size:
            issues.append(f"manifest size mismatch: {relative}")

    return tuple(dict.fromkeys(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Qingzhou standalone release directory")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    issues = inspect_release(args.artifact)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    files = len(_relative_files(args.artifact))
    print(f"release-audit: PASS ({files} files; catalog, manifest, and scope checks passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
