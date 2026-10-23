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
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


# Support the documented `python scripts/inspect_release.py ...` invocation.
# scripts is repository tooling, deliberately not an installed product package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_environment import validate_build_environment

APP_EXECUTABLE = "QingzhouCarbonAccounting.exe"
MANIFEST_NAME = "build-manifest.json"
ALLOWED_SQLITE = Path("databases/catalog.sqlite")
PYTHON_DOCX_DEFAULT_TEMPLATE = "docx/templates/default.docx"
PRIOR_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v4.xlsx")
PRIOR_TEMPLATE_SHA256 = "e9b83462eabd97d5c7bd9aae1b4fa97a27d80006a205907c6671e626e8e57f6f"
V5_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v5.xlsx")
V5_TEMPLATE_SHA256 = "7438082b59e6ba294bb953ccc44db0c7a3a16eacbf4f8ddd83f063ce492bb890"
V6_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v6.xlsx")
V6_TEMPLATE_SHA256 = "ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a"
V7_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v7.xlsx")
V7_TEMPLATE_SHA256 = "e4203f0d5bf9133df5b6abde3bfede8b82905d11d795cd29ba590ea60f7ebb5a"
V8_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v8.xlsx")
V8_TEMPLATE_SHA256 = "a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4"
V9_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v9.xlsx")
V9_TEMPLATE_SHA256 = "0fa20cbc126fadd2807fe02bea9b26b4a8855285e6b90fc171985557a895fae9"
V10_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v10.xlsx")
V10_TEMPLATE_SHA256 = "705a9326f6910bceaad34ce955975a6150731fa8ed2b50ddfe8c2c5188deb729"
APPROVED_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v11.xlsx")
APPROVED_TEMPLATE_SHA256 = "b1e843a1eb8980c5a9bf4ee11d5b2369abcb89ebf4ca5b8659d8cccaefd166c4"
PREVIOUS_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v3.xlsx")
PREVIOUS_TEMPLATE_SHA256 = "f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718"
COMPATIBILITY_TEMPLATE_PATH = Path("resources/excel_templates/gb_t_32151_34_2024_appendix_b_v2.xlsx")
COMPATIBILITY_TEMPLATE_SHA256 = "58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4"
TEMPLATE_SHA256_BY_PATH = {
    V10_TEMPLATE_PATH: V10_TEMPLATE_SHA256,
    V8_TEMPLATE_PATH: V8_TEMPLATE_SHA256,
    V9_TEMPLATE_PATH: V9_TEMPLATE_SHA256,
    V6_TEMPLATE_PATH: V6_TEMPLATE_SHA256,
    V7_TEMPLATE_PATH: V7_TEMPLATE_SHA256,
    V5_TEMPLATE_PATH: V5_TEMPLATE_SHA256,
    PRIOR_TEMPLATE_PATH: PRIOR_TEMPLATE_SHA256,
    APPROVED_TEMPLATE_PATH: APPROVED_TEMPLATE_SHA256,
    PREVIOUS_TEMPLATE_PATH: PREVIOUS_TEMPLATE_SHA256,
    COMPATIBILITY_TEMPLATE_PATH: COMPATIBILITY_TEMPLATE_SHA256,
}
from packages.standards.carbon_material_business_policy import RUNTIME_RESOURCE, RUNTIME_SHA256, MATERIAL_RUNTIME_RESOURCE, MATERIAL_RUNTIME_SHA256, FGD_RUNTIME_RESOURCE, FGD_RUNTIME_SHA256, HEAT_RUNTIME_RESOURCE, HEAT_RUNTIME_SHA256

BUSINESS_RULES_PATH = Path("resources") / RUNTIME_RESOURCE

REPORT_LAYOUT_PATH = Path("packages/application/reporting/appendix_b_layout.json")
STEAM_LICENSE_HASHES = {'resources/licenses/steam_if97/CoolProp-8.0.0-LICENSE.txt': '33cfa17c9d0abe742bcbe532c52e79bc08704a0c30dbcc61dd76011b1ebe127e', 'resources/licenses/steam_if97/NumPy-2.3.3-LICENSE.txt': '596b953e1dcbe829b32ae444387efa15003fc6abdeca8a2179f364a6364c286e', 'resources/licenses/steam_if97/CoolProp_boost-headers_LICENSE.txt': '5aa9d6274dc04b8ef541d29ff973362936798a2316048ff9089f289243abc456', 'resources/licenses/steam_if97/CoolProp_IF97_LICENSE.txt': 'dc5c04001614c958cb46c383e7e88e3e50a98f4dd2f77e76d69c30be63a4f512', 'resources/licenses/steam_if97/CoolProp_REFPROP-headers_LICENSE.txt': '12190c4091c7cf90a71ef87a02f2677ec0bfbc0469c70a489201ea6b57db9044', 'resources/licenses/steam_if97/Eigen5.0.1_COPYING.MPL2.txt': '88c0394098e40fb1ca64bdc2048b20dc1d010b1745b48e41cbe76dae36eb1bf5', 'resources/licenses/steam_if97/fmtlib_fmt_LICENSE.txt': 'a9afff5540d894a9c7ba0e1b427cf61b77e06f1f72c25b025618169bdde52253', 'resources/licenses/steam_if97/msgpack_msgpack-c_COPYING.txt': 'a566eeb22107c7af7c091d47dd912f4249a3ebf3d07ca0d7ccb785becfe7d8ab', 'resources/licenses/steam_if97/nlohmann_json_LICENSE.MIT.txt': '3d20faab6958545bf6df39e42d046265786494f5c9e23b198f8aaa0a10e368bf', 'resources/licenses/steam_if97/tristanpenman_valijson_LICENSE.txt': '0eb47a50b864385008e182cff467a9970fc3db57801a08468075436016b60abc', 'resources/licenses/steam_if97/wjakob_nanobind_LICENSE.txt': '16faaa143ebee12b09cec5bb2aaa51ac99c9522a0b054aed4cf8bf54b07771c3', 'resources/licenses/steam_if97/miniz-3.1.1-LICENSE.txt': '6f20fa7672b00e2e975c291df737cf227addf3ad32e36fef3fe0f416e4664d3d', 'resources/licenses/steam_if97/incbin-UNLICENSE.txt': '7e12e5df4bae12cb21581ba157ced20e1986a0508dd10d0e8a4ab9a4cf94e85c', 'resources/licenses/steam_if97/SOURCES_AND_NOTICES.json': '2f825d09038c4a927adeb253baf5af836ac75e41cbaaaf0aa74d72c57ce411f2'}

ALLOWED_RESOURCE_FILES = frozenset({
    *STEAM_LICENSE_HASHES,
    BUSINESS_RULES_PATH.as_posix(),
    (Path("resources") / MATERIAL_RUNTIME_RESOURCE).as_posix(),
    V6_TEMPLATE_PATH.as_posix(), V7_TEMPLATE_PATH.as_posix(), V8_TEMPLATE_PATH.as_posix(),
    (Path("resources") / FGD_RUNTIME_RESOURCE).as_posix(),
    (Path("resources") / HEAT_RUNTIME_RESOURCE).as_posix(),
    V9_TEMPLATE_PATH.as_posix(), V10_TEMPLATE_PATH.as_posix(),
    V5_TEMPLATE_PATH.as_posix(),
    APPROVED_TEMPLATE_PATH.as_posix(),
    PRIOR_TEMPLATE_PATH.as_posix(),
    PREVIOUS_TEMPLATE_PATH.as_posix(),
    COMPATIBILITY_TEMPLATE_PATH.as_posix(),
    "resources/branding/qingzhou_logo.png",
    *(f"resources/icons/{name}.svg" for name in
      ("factors", "excel", "home", "records", "new", "settings", "standards", "chevron-down")),
})
EXCEL_SUFFIXES = frozenset(
    {".xls", ".xlsx", ".xlsm", ".xlsb", ".xltx", ".xltm", ".xlam", ".xla", ".ods", ".ots", ".fods", ".et", ".ett"}
)
FORBIDDEN_SUFFIXES = frozenset(
    {".pdf", ".doc", ".docx", ".docm", ".dotx", ".dotm", ".odt", ".rtf", ".xls", ".xlsx", ".csv", ".pem", ".key", ".p12"}
)
FORBIDDEN_PARTS = frozenset(
    {"tests", "test", "计算表", ".venv", "tmp", "data-source", ".git", ".github"}
)


def excel_row_boolean_issues(path: Path) -> list[str]:
    """Inspect the known template format failure in actual packaged resources."""
    boolean_names = {"customHeight", "hidden", "collapsed", "customFormat", "thickTop", "thickBot", "ph"}
    issues = []
    try:
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if not (name.startswith("xl/worksheets/") and name.endswith(".xml")):
                    continue
                root = ET.fromstring(archive.read(name))
                for row in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
                    for attribute in boolean_names & row.attrib.keys():
                        if row.get(attribute) not in {"0", "1", "true", "false"}:
                            issues.append(f"invalid Excel row boolean: {path.name}/{name} row {row.get('r')} {attribute}={row.get(attribute)}")
    except (OSError, BadZipFile, ET.ParseError) as exc:
        issues.append(f"invalid Excel template XML: {path.name}: {type(exc).__name__}")
    return issues


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


def _check_catalog(path: Path, issues: list[str]) -> str | None:
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

    if metadata.get("schema_version") != "003":
        issues.append(f"unexpected catalog database schema version: {metadata.get('schema_version')!r}")
    if metadata.get("app_version") != "1.1.0":
        issues.append(f"unexpected catalog app version: {metadata.get('app_version')!r}")
    if catalog_metadata.get("schema_version") != "1.1.0":
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
    return metadata.get("schema_version")


def inspect_release(root: str | Path) -> tuple[str, ...]:
    """Return all release-audit findings; an empty tuple means PASS."""

    artifact = Path(root)
    issues: list[str] = []
    if not artifact.is_dir():
        return (f"release directory does not exist: {artifact}",)

    executable = artifact / APP_EXECUTABLE
    if not executable.is_file():
        issues.append(f"missing {APP_EXECUTABLE}")

    catalog_database_version = _check_catalog(artifact / ALLOWED_SQLITE, issues)
    if not (artifact / APPROVED_TEMPLATE_PATH).is_file():
        issues.append(f"missing approved Excel template: {APPROVED_TEMPLATE_PATH.as_posix()}")
    if not (artifact / V8_TEMPLATE_PATH).is_file():
        issues.append(f"missing compatibility v8 Excel template: {V8_TEMPLATE_PATH.as_posix()}")
    if not (artifact / V6_TEMPLATE_PATH).is_file():
        issues.append(f"missing prior v6 Excel template: {V6_TEMPLATE_PATH.as_posix()}")
    if not (artifact / V5_TEMPLATE_PATH).is_file():
        issues.append(f"missing prior v5 Excel template: {V5_TEMPLATE_PATH.as_posix()}")
    if not (artifact / PRIOR_TEMPLATE_PATH).is_file():
        issues.append(f"missing prior Excel template: {PRIOR_TEMPLATE_PATH.as_posix()}")
    if not (artifact / PREVIOUS_TEMPLATE_PATH).is_file():
        issues.append(f"missing previous Excel template: {PREVIOUS_TEMPLATE_PATH.as_posix()}")
    if not (artifact / COMPATIBILITY_TEMPLATE_PATH).is_file():
        issues.append(f"missing compatibility Excel template: {COMPATIBILITY_TEMPLATE_PATH.as_posix()}")
    if not (artifact / REPORT_LAYOUT_PATH).is_file():
        issues.append(f"missing packaged Word report layout: {REPORT_LAYOUT_PATH.as_posix()}")
    if not (artifact / BUSINESS_RULES_PATH).is_file():
        issues.append(f"missing fuel/power runtime rules: {BUSINESS_RULES_PATH.as_posix()}")
    elif _sha256(artifact / BUSINESS_RULES_PATH) != RUNTIME_SHA256:
        issues.append(f"fuel/power runtime rules hash mismatch: {BUSINESS_RULES_PATH.as_posix()}")
    fgd_path = Path("resources") / FGD_RUNTIME_RESOURCE
    if not (artifact / fgd_path).is_file() or _sha256(artifact / fgd_path) != FGD_RUNTIME_SHA256:
        issues.append("missing or inconsistent adopted FGD rules")
    heat_path = Path("resources") / HEAT_RUNTIME_RESOURCE
    if not (artifact / heat_path).is_file() or _sha256(artifact / heat_path) != HEAT_RUNTIME_SHA256:
        issues.append("missing or inconsistent adopted heat rules")
    material_path = Path("resources") / MATERIAL_RUNTIME_RESOURCE
    if not (artifact / material_path).is_file() or _sha256(artifact / material_path) != MATERIAL_RUNTIME_SHA256:
        issues.append("missing or damaged material runtime rules")
    for notice, expected in STEAM_LICENSE_HASHES.items():
        if not (artifact / notice).is_file() or _sha256(artifact / notice) != expected:
            issues.append("missing or inconsistent steam licensing notice: " + notice)
    for path in _relative_files(artifact):
        relative = Path(path)
        normalized = relative.as_posix()
        lower = normalized.lower()
        if "virtualkeyboard" in lower:
            issues.append(f"unapproved GPL-only Qt Virtual Keyboard component: {normalized}")
        if relative.name.lower() in {"qpdf.dll", "qt6pdf.dll"}:
            issues.append(f"unused PDF image component outside approved package scope: {normalized}")
        if "iapws" in lower:
            issues.append(f"unapproved iapws distribution component: {normalized}")
        if normalized.startswith("resources/") and normalized not in ALLOWED_RESOURCE_FILES:
            issues.append(f"unexpected resource file: {normalized}")
        parts = {part.lower() for part in relative.parts}
        if parts & {part.lower() for part in FORBIDDEN_PARTS}:
            issues.append(f"forbidden development or user-data path: {normalized}")
        if relative.suffix.lower() in EXCEL_SUFFIXES:
            expected_hash = TEMPLATE_SHA256_BY_PATH.get(relative)
            if relative.suffix.lower() != ".xlsx" or expected_hash is None:
                issues.append(f"unexpected Excel workbook file: {normalized}")
            else:
                if _sha256(artifact / relative) != expected_hash:
                    issues.append(f"approved Excel template hash mismatch: {normalized}")
                issues.extend(excel_row_boolean_issues(artifact / relative))
        elif relative.suffix.lower() in FORBIDDEN_SUFFIXES and not (
            relative.suffix.lower() == ".docx"
            and normalized.lower() == PYTHON_DOCX_DEFAULT_TEMPLATE
        ):
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

    issues.extend(validate_build_environment(manifest.get("build_environment")))
    if manifest.get("manifest_version") != 1:
        issues.append("unsupported release manifest version")
    if manifest.get("artifact_name") != "QingzhouCarbonAccounting":
        issues.append("unexpected release artifact name")
    if manifest.get("app_version") != "1.1.0":
        issues.append(f"unexpected manifest app version: {manifest.get('app_version')!r}")
    database_versions = manifest.get("database_schema_versions")
    if not isinstance(database_versions, dict):
        issues.append("manifest missing database_schema_versions")
    elif catalog_database_version is not None and database_versions.get("catalog") != catalog_database_version:
        issues.append("manifest catalog database schema version does not match packaged database")
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
