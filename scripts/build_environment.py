"""Build-only toolchain identity; constraints remain requirements-build.txt."""
from __future__ import annotations
from importlib.metadata import version
from pathlib import Path
import platform
import struct

DISTRIBUTIONS = ("PySide6", "PySide6-Essentials", "PySide6-Addons", "shiboken6",
                 "PyInstaller", "pyinstaller-hooks-contrib")

def collect_build_environment() -> dict[str, str]:
    from PySide6.QtCore import qVersion
    return {**{name: version(name) for name in DISTRIBUTIONS},
            "Qt": qVersion(), "Python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(), "bits": str(struct.calcsize("P") * 8)}

def validate_build_environment(environment: object) -> tuple[str, ...]:
    if not isinstance(environment, dict):
        return ("manifest missing build_environment",)
    pins = {}
    for line in (Path(__file__).resolve().parents[1] / "requirements-build.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.startswith("#"):
            name, value = line.strip().split("==", 1)
            pins[name] = value
    expected = {name: pins[name] for name in DISTRIBUTIONS}
    expected.update(Qt=pins["PySide6"], implementation="CPython", system="Windows", bits="64")
    issues = [f"build_environment {key}: expected {value!r}, got {environment.get(key)!r}"
              for key, value in expected.items() if environment.get(key) != value]
    python = environment.get("Python")
    if not isinstance(python, str) or len(python.split(".")) != 3 or not python.startswith("3.12.") or not python.split(".")[-1].isdigit():
        issues.append(f"build_environment Python: expected 3.12.patch, got {python!r}")
    return tuple(issues)
