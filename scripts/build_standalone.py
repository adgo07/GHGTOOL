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
from scripts.inspect_release import inspect_release
from scripts.verify_release_archive import verify_release_archive


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
        "artifact_name": APP_NAME,
        "app_version": app_version,
        "catalog_schema_version": catalog_meta["schema_version"],
        "catalog_data_version": catalog_meta["data_version"],
        "database_schema_versions": {
            "catalog": "001",
            "user": "001",
            "records": "002",
            "projects": "001",
        },
        **_release_provenance(),
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


def build_standalone(output_root: str | Path = "dist", *, clean: bool = False) -> Path:
    """Build and audit an onedir Windows artifact."""

    if os.name != "nt":
        raise RuntimeError("G08 standalone build must run on Windows")
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
            "--add-data",
            f"{PROJECT_ROOT / 'resources'}{os.pathsep}resources",
            "--add-data",
            f"{PROJECT_ROOT / 'migrations'}{os.pathsep}migrations",
            "--add-data",
            f"{catalog_path}{os.pathsep}databases",
            "--hidden-import",
            "PySide6.QtSvg",
            str(ENTRY_POINT),
        ]
        subprocess.run(pyinstaller_args, cwd=PROJECT_ROOT, check=True)
        if not artifact.is_dir():
            raise RuntimeError(f"PyInstaller did not create {artifact}")
        _remove_incompatible_external_icu(artifact)
        _remove_hidden_release_placeholders(artifact)
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
