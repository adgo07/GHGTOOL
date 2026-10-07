from __future__ import annotations

import ast
import unittest
from pathlib import Path


PACKAGES_ROOT = Path(__file__).resolve().parents[1] / "packages"


def _module_name(path: Path) -> str:
    relative = path.relative_to(PACKAGES_ROOT.parent).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_import(path: Path, node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)

    if node.level == 0:
        return (node.module or "",)

    current = _module_name(path).split(".")
    if path.name != "__init__.py":
        current.pop()
    parent = current[: max(0, len(current) - node.level + 1)]
    if node.module:
        parent.extend(node.module.split("."))
    return (".".join(parent),)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def _imports(path: Path) -> tuple[tuple[str, ast.AST], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            found.extend((module, node) for module in _resolve_import(path, node))
    return tuple(found)


def _is_forbidden_desktop_or_storage(module: str) -> bool:
    normalized = module.casefold()
    return (
        normalized == "pyside6"
        or normalized.startswith("pyside6.")
        or normalized == "sqlite3"
        or normalized.startswith("sqlite3.")
        or normalized == "ui"
        or normalized.startswith("ui.")
        or normalized == "packages.ui"
        or normalized.startswith("packages.ui.")
        or normalized == "packages.persistence"
        or normalized.startswith("packages.persistence.")
        or normalized.startswith("packages.infrastructure.sqlite")
    )


def _call_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


class ArchitectureBoundaryTests(unittest.TestCase):
    def _assert_no_forbidden_imports(self, root: Path, *, include_persistence: bool) -> None:
        violations: list[str] = []
        for path in _python_files(root):
            for module, node in _imports(path):
                forbidden = _is_forbidden_desktop_or_storage(module)
                if not include_persistence and module.startswith("packages.persistence"):
                    forbidden = False
                if forbidden:
                    violations.append(f"{path.relative_to(PACKAGES_ROOT.parent)}:{node.lineno}: {module}")
        self.assertEqual(violations, [], "forbidden architectural imports:\n" + "\n".join(violations))

    def test_core_and_standards_do_not_depend_on_desktop_or_persistence(self) -> None:
        for package in ("core", "standards"):
            with self.subTest(package=package):
                self._assert_no_forbidden_imports(PACKAGES_ROOT / package, include_persistence=True)

    def test_application_does_not_depend_on_ui_or_concrete_storage(self) -> None:
        self._assert_no_forbidden_imports(PACKAGES_ROOT / "application", include_persistence=True)

    def test_excel_and_report_adapters_do_not_depend_on_ui(self) -> None:
        roots = (
            PACKAGES_ROOT / "excel",
            PACKAGES_ROOT / "reporting",
            PACKAGES_ROOT / "infrastructure" / "reporting",
        )
        violations: list[str] = []
        for root in roots:
            if not root.exists():
                continue
            for path in _python_files(root):
                for module, node in _imports(path):
                    normalized = module.casefold()
                    if (
                        normalized == "pyside6"
                        or normalized.startswith("pyside6.")
                        or normalized == "ui"
                        or normalized.startswith("ui.")
                        or normalized == "packages.ui"
                        or normalized.startswith("packages.ui.")
                    ):
                        violations.append(f"{path.relative_to(PACKAGES_ROOT.parent)}:{node.lineno}: {module}")
        self.assertEqual(violations, [], "adapter imports UI:\n" + "\n".join(violations))

    def test_ui_does_not_construct_sqlite_record_repository(self) -> None:
        violations: list[str] = []
        for path in _python_files(PACKAGES_ROOT / "ui"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported_names = {"SQLiteRecordRepository"}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported_names.update(
                        alias.asname or alias.name
                        for alias in node.names
                        if alias.name == "SQLiteRecordRepository"
                    )
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _call_name(node) in imported_names:
                    violations.append(f"{path.relative_to(PACKAGES_ROOT.parent)}:{node.lineno}")
        self.assertEqual(violations, [], "UI must receive its record repository from the composition root")

    def test_carbon_calculator_does_not_construct_or_persist_records(self) -> None:
        path = PACKAGES_ROOT / "standards" / "carbon_material.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            for module in _resolve_import(path, node):
                if module.startswith("packages.persistence"):
                    violations.append(f"{node.lineno}: imports {module}")
                if module == "packages.core.repositories":
                    prohibited_ports = {
                        "RecordRepository",
                        "DetailedRecordRepository",
                        "RecordLifecycleRepository",
                    }
                    for alias in node.names:
                        if alias.name in prohibited_ports:
                            violations.append(f"{node.lineno}: imports {alias.name}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name in {"AccountingRecord", "InMemoryRecordRepository", "create", "create_with_details"}:
                    violations.append(f"{node.lineno}: calls {name}")
            if isinstance(node, ast.Name) and node.id == "record_repository":
                violations.append(f"{node.lineno}: references record_repository")
        self.assertEqual(violations, [], "calculator must stay pure; persistence belongs to Application")


if __name__ == "__main__":
    unittest.main()
