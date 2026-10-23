"""Build the Windows standalone directory for the G08 delivery candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.persistence import build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from scripts.inspect_release import (
    ALLOWED_RESOURCE_FILES,
    APPROVED_TEMPLATE_PATH,
    APPROVED_TEMPLATE_SHA256,
    COMPATIBILITY_TEMPLATE_PATH,
    COMPATIBILITY_TEMPLATE_SHA256,
    V5_TEMPLATE_PATH, V5_TEMPLATE_SHA256, V10_TEMPLATE_PATH, V10_TEMPLATE_SHA256,
    V6_TEMPLATE_PATH, V6_TEMPLATE_SHA256, V7_TEMPLATE_PATH, V7_TEMPLATE_SHA256, V8_TEMPLATE_PATH, V8_TEMPLATE_SHA256, V9_TEMPLATE_PATH, V9_TEMPLATE_SHA256,
    PRIOR_TEMPLATE_PATH,
    PRIOR_TEMPLATE_SHA256,
    PREVIOUS_TEMPLATE_PATH,
    PREVIOUS_TEMPLATE_SHA256,
    EXCEL_SUFFIXES,
    inspect_release,
)
from scripts.build_environment import collect_build_environment, validate_build_environment
from scripts.verify_release_archive import verify_release_archive
from scripts.project_fuel_power_rules import verify_projection
from scripts.project_material_rules import verify_material_projection
from scripts.project_heat_rules import verify_heat_projection


APP_NAME = "QingzhouCarbonAccounting"
ENTRY_POINT = PROJECT_ROOT / "scripts" / "standalone_entry.py"


def _project_version() -> str:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def _catalog_manifest(source: Path) -> dict[str, str]:
    catalog = json.loads(source.read_text(encoding="utf-8"))
    manifest = catalog["manifest"]
    return {
        "schema_version": str(manifest["schema_version"]),
        "data_version": str(manifest["data_version"]),
    }


def _source_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _release_provenance() -> dict[str, str]:
    """Return explicit checkout, PR-head, and tested-merge provenance."""

    checkout_sha = _source_commit()
    return {
        "source_commit": checkout_sha,
        "pr_head_sha": os.environ.get("QZ_PR_HEAD_SHA", "").strip() or checkout_sha,
        "tested_merge_sha": os.environ.get("QZ_TESTED_MERGE_SHA", "").strip() or checkout_sha,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(artifact: Path, *, app_version: str, catalog_meta: dict[str, str]) -> None:
    environment = collect_build_environment()
    issues = validate_build_environment(environment)
    if issues:
        raise RuntimeError("; ".join(issues))
    entries: list[dict[str, Any]] = []
    for path in sorted(
        item.relative_to(artifact)
        for item in artifact.rglob("*")
        if item.is_file()
        and item.name != "build-manifest.json"
        and not any(part.startswith(".") for part in item.relative_to(artifact).parts)
    ):
        entries.append(
            {
                "path": path.as_posix(),
                "size": (artifact / path).stat().st_size,
                "sha256": _sha256(artifact / path),
            }
        )

    catalog_path = artifact / "databases" / "catalog.sqlite"
    manifest = {
        "manifest_version": 1,
        "build_environment": environment,
        "artifact_name": APP_NAME,
        "app_version": app_version,
        "catalog_schema_version": catalog_meta["schema_version"],
        "catalog_data_version": catalog_meta["data_version"],
        "database_schema_versions": {
            "catalog": "003",
            "user": "001",
            "records": "004",
            "projects": "003",
        },
        **_release_provenance(),
        "steam_property_profile": {
            "profile_id": "GHGTOOL_COOLPROP_IF97_PROPERTY_V1", "representation": "IEEE-754 binary64",
            "implementation": "Python CoolProp IF97 backend", "version": "8.0.0", "numpy": "2.3.3",
            "revision": "ae81610e7d23efc57f9d051c8e70a4d66e87537f",
            "method_version": "CAR-HEAT-IF97-017.1",
        },
        "files": entries,
    }
    (artifact / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not catalog_path.is_file():
        raise RuntimeError("PyInstaller output omitted databases/catalog.sqlite")


def _remove_incompatible_external_icu(artifact: Path) -> None:
    """Do not ship an unrelated Poppler ICU next to Qt's Windows runtime."""

    for filename in ("icuuc.dll", "icudt78.dll"):
        candidate = artifact / filename
        if candidate.is_file() and not candidate.is_symlink():
            candidate.unlink()

def _remove_hidden_release_placeholders(artifact: Path) -> None:
    """Remove source-tree placeholders that upload-artifact omits by default."""

    for candidate in artifact.rglob(".gitkeep"):
        if candidate.is_file() and not candidate.is_symlink():
            candidate.unlink()


def _remove_unpacked_docx_template(artifact: Path) -> None:
    """Remove PyInstaller's redundant extracted copy of python-docx's template.

    The original ``docx/templates/default.docx`` remains as the runtime resource.
    The extracted directory only duplicates that OOXML package and contains hidden
    ``.rels`` files that artifact ZIP filters omit.
    """

    candidate = artifact / "docx" / "templates" / "default-docx-template"
    if candidate.is_dir() and not candidate.is_symlink():
        candidate_resolved = candidate.resolve()
        if candidate_resolved.is_relative_to(artifact.resolve()):
            shutil.rmtree(candidate_resolved)


def _remove_unused_virtual_keyboard(artifact: Path) -> None:
    """Exclude the unused GPL-only Qt virtual keyboard collected by the GUI hook.

    Product uses Qt Widgets/native Windows input, with no VirtualKeyboard/QML
    consumer. Actual PE inspection showed only this plugin imports its DLL.
    A future consumer must resolve licensing before changing this package scope.
    """
    root = artifact.resolve()
    for relative in (
        "PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
        "Qt6VirtualKeyboard.dll",  # Qt 6.11 layout
        "PySide6/Qt6VirtualKeyboard.dll",  # Observed Qt 6.12 CI layout
    ):
        candidate = artifact / relative
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
            raise RuntimeError("refusing to remove an external Qt component")
        if candidate.is_file():
            candidate.unlink()


def _remove_unused_pdf_image_plugin(artifact: Path) -> None:
    """Remove the unused PDF image plugin and its direct Qt PDF dependency.

    Product image consumers load approved PNG/SVG resources, not PDF images.
    This is a package-scope exclusion, not a GPL-only license classification.
    """
    root = artifact.resolve()
    for relative in (
        "PySide6/plugins/imageformats/qpdf.dll",
        "Qt6Pdf.dll",
        "PySide6/Qt6Pdf.dll",
    ):
        candidate = artifact / relative
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
            raise RuntimeError("refusing to remove an external Qt component")
        if candidate.is_file():
            candidate.unlink()


def _validate_approved_template_inputs(project_root: Path = PROJECT_ROOT) -> None:
    resource_root = project_root / "resources"
    expected_hashes = {
        APPROVED_TEMPLATE_PATH: APPROVED_TEMPLATE_SHA256,
        V6_TEMPLATE_PATH: V6_TEMPLATE_SHA256,
        V7_TEMPLATE_PATH: V7_TEMPLATE_SHA256,
        V8_TEMPLATE_PATH: V8_TEMPLATE_SHA256,
        V9_TEMPLATE_PATH: V9_TEMPLATE_SHA256,
        V10_TEMPLATE_PATH: V10_TEMPLATE_SHA256,
        V5_TEMPLATE_PATH: V5_TEMPLATE_SHA256,
        PRIOR_TEMPLATE_PATH: PRIOR_TEMPLATE_SHA256,
        PREVIOUS_TEMPLATE_PATH: PREVIOUS_TEMPLATE_SHA256,
        COMPATIBILITY_TEMPLATE_PATH: COMPATIBILITY_TEMPLATE_SHA256,
    }
    expected_paths = tuple(sorted(path.relative_to("resources").as_posix() for path in expected_hashes))
    workbook_files = tuple(
        sorted(
            path.relative_to(resource_root).as_posix()
            for path in resource_root.rglob("*")
            if path.is_file() and path.suffix.lower() in EXCEL_SUFFIXES
        )
    )
    if workbook_files != expected_paths:
        raise RuntimeError(
            "Excel build inputs must contain only the approved current, previous, and compatibility templates at "
            f"{expected_paths!r}; found {workbook_files!r}"
        )
    for path in resource_root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.name in {"__init__.py", ".gitkeep"}:
            continue
        relative = path.relative_to(project_root).as_posix()
        if relative not in ALLOWED_RESOURCE_FILES or path.is_symlink():
            raise RuntimeError(f"unapproved build resource: {relative}")
    for relative, expected_hash in expected_hashes.items():
        expected = project_root / relative
        if expected.is_symlink() or not expected.is_file() or _sha256(expected) != expected_hash:
            raise RuntimeError(f"approved Excel template is missing or has an unexpected hash: {expected}")


def build_standalone(output_root: str | Path = "dist", *, clean: bool = False) -> Path:
    """Build and audit an onedir Windows artifact."""

    if os.name != "nt":
        raise RuntimeError("G08 standalone build must run on Windows")
    _validate_approved_template_inputs()
    verify_projection()
    verify_material_projection()
    verify_heat_projection()
    # Fail before creating/replacing an artifact when the declared physical runtime differs.
    from decimal import Decimal
    from packages.core.decimal_policy import DecimalPolicy
    from packages.standards.carbon_material import SteamKind
    from packages.standards.carbon_material_steam_if97 import evaluate_if97_steam
    evaluate_if97_steam(steam_kind=SteamKind.SUPERHEATED,pressure_mpa=Decimal(".0035"),temperature_c=Decimal("26.85"),
        policy=DecimalPolicy(),numeric_profile_id="GHGTOOL_CARBON_DECIMAL40_CURRENT")
    output_directory = Path(output_root)
    artifact = output_directory / APP_NAME
    if artifact.exists():
        if not clean:
            raise FileExistsError(f"release directory already exists: {artifact}; use --clean")
        if artifact.resolve().parent != output_directory.resolve():
            raise RuntimeError("refusing to clean an artifact outside output directory")
        shutil.rmtree(artifact)

    output_directory.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="qz-g08-build-"))
    try:
        catalog_path = temp_root / "databases" / "catalog.sqlite"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        app_version = _project_version()
        catalog_meta = _catalog_manifest(DEFAULT_SOURCE_PATH)
        build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path, app_version=app_version)

        pyinstaller_args = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--windowed",
            "--name",
            APP_NAME,
            "--contents-directory",
            ".",
            "--distpath",
            str(output_directory),
            "--workpath",
            str(temp_root / "pyinstaller-work"),
            "--specpath",
            str(temp_root / "pyinstaller-spec"),
            "--paths",
            str(PROJECT_ROOT),
            "--additional-hooks-dir",
            str(PROJECT_ROOT / "scripts" / "pyinstaller_hooks"),
            *(argument for relative in sorted(ALLOWED_RESOURCE_FILES)
              for argument in ("--add-data", f"{PROJECT_ROOT / relative}{os.pathsep}{Path(relative).parent}")),
            "--collect-data",
            "packages.application.reporting",
            "--add-data",
            f"{PROJECT_ROOT / 'migrations'}{os.pathsep}migrations",
            "--add-data",
            f"{catalog_path}{os.pathsep}databases",
            "--hidden-import",
            "CoolProp.CoolProp",
            "--hidden-import",
            "numpy",
            "--hidden-import",
            "PySide6.QtSvg",
            "--hidden-import",
            "resources",
            str(ENTRY_POINT),
        ]
        subprocess.run(pyinstaller_args, cwd=PROJECT_ROOT, check=True)
        if not artifact.is_dir():
            raise RuntimeError(f"PyInstaller did not create {artifact}")
        _remove_incompatible_external_icu(artifact)
        _remove_hidden_release_placeholders(artifact)
        _remove_unpacked_docx_template(artifact)
        _remove_unused_virtual_keyboard(artifact)
        _remove_unused_pdf_image_plugin(artifact)
        _write_manifest(artifact, app_version=app_version, catalog_meta=catalog_meta)
        issues = inspect_release(artifact)
        if issues:
            raise RuntimeError("standalone audit failed: " + "; ".join(issues))
        verify_release_archive(artifact)
        print(f"built standalone: {artifact}")
        return artifact
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Qingzhou Windows standalone directory")
    parser.add_argument("--output-root", type=Path, default=Path("dist"))
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    build_standalone(args.output_root, clean=args.clean)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
