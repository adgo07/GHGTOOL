"""Smoke-test a Windows onedir candidate in an isolated user-data directory."""

from __future__ import annotations

import argparse
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
                logs = (
                    Path(data_root)
                    / "QingzhouEnergySuite"
                    / "carbon_accounting"
                    / "logs"
                    / "application.jsonl"
                )
                if not records.is_file():
                    raise RuntimeError(f"records database missing after startup {attempt}")
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