"""Verify the manifest after an upload-artifact-style ZIP round trip."""

from __future__ import annotations

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.inspect_release import inspect_release


def _is_hidden(relative: Path) -> bool:
    return any(part.startswith(".") for part in relative.parts)


def _write_upload_archive(source: Path, destination: Path) -> int:
    """Create the same visible-file subset used by the default artifact upload."""

    count = 0
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source)
            if _is_hidden(relative):
                continue
            archive.write(path, relative.as_posix())
            count += 1
    return count


def verify_release_archive(source: str | Path) -> int:
    """Round-trip a release through a visible-file ZIP and re-run the audit."""

    artifact = Path(source)
    with tempfile.TemporaryDirectory(prefix="qz-g08-archive-") as directory:
        archive_path = Path(directory) / "release.zip"
        file_count = _write_upload_archive(artifact, archive_path)
        extracted = Path(directory) / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extracted)
        issues = inspect_release(extracted)
        if issues:
            raise RuntimeError("uploaded archive audit failed: " + "; ".join(issues))
    return file_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a release after artifact ZIP filtering")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    count = verify_release_archive(args.artifact)
    print(f"release-archive: PASS ({count} visible files; manifest survives ZIP round-trip)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())