"""Smoke-test a Windows onedir candidate in an isolated user-data directory."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


APP_NAME = "QingzhouCarbonAccounting.exe"


def smoke(artifact: str | Path, *, starts: int = 2, wait_seconds: float = 8.0) -> None:
    if os.name != "nt":
        raise RuntimeError("standalone smoke test must run on Windows")
    root = Path(artifact).resolve()
    executable = root / APP_NAME
    if not executable.is_file():
        raise FileNotFoundError(executable)

    with tempfile.TemporaryDirectory(prefix="qz-g08-smoke-") as data_root:
        environment = os.environ.copy()
        environment["LOCALAPPDATA"] = data_root
        environment["QT_QPA_PLATFORM"] = "offscreen"
        environment.pop("QZ_G08_IMAGE_PROBE_PATH", None)
        image_probe = Path(data_root) / "image-resources.json"
        probe = subprocess.run([str(executable), "--probe-images", str(image_probe)], cwd=root, env=environment,
                               capture_output=True, timeout=30)
        if probe.returncode != 0 or not image_probe.is_file():
            raise RuntimeError(f"standalone image probe failed: {probe.returncode}")
        images = json.loads(image_probe.read_text(encoding="utf-8"))
        if set(images) != {"branding/qingzhou_logo.png", "icons/home.svg"} or any(
            len(size) != 2 or min(size) <= 0 for size in images.values()
        ):
            raise RuntimeError("standalone PNG/SVG resource proof is invalid")
        print("standalone-images: PASS (PNG/SVG)")
        for attempt in range(1, starts + 1):
            process = subprocess.Popen(
                [str(executable)],
                cwd=root,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                time.sleep(wait_seconds)
                if process.poll() is not None:
                    raise RuntimeError(
                        f"standalone startup {attempt} exited with code {process.returncode}"
                    )
                records = (
                    Path(data_root)
                    / "QingzhouEnergySuite"
                    / "carbon_accounting"
                    / "data"
                    / "records.sqlite"
                )
                projects = (
                    Path(data_root)
                    / "QingzhouEnergySuite"
                    / "carbon_accounting"
                    / "data"
                    / "projects.sqlite"
                )
                logs = (
                    Path(data_root)
                    / "QingzhouEnergySuite"
                    / "carbon_accounting"
                    / "logs"
                    / "application.jsonl"
                )
                if not records.is_file():
                    raise RuntimeError(f"records database missing after startup {attempt}")
                if not projects.is_file():
                    raise RuntimeError(f"projects database missing after startup {attempt}")
                if not logs.is_file():
                    raise RuntimeError(f"structured log missing after startup {attempt}")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    print(f"standalone-smoke: PASS ({starts} isolated starts)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a Windows standalone candidate")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--starts", type=int, default=2)
    args = parser.parse_args()
    smoke(args.artifact, starts=args.starts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
