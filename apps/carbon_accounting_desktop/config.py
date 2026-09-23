"""Application-edge configuration for the G04 desktop shell.

This module only defines application-level settings. Business data and database
configuration stay outside the public shell and are passed to the application
query service.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable configuration needed by the desktop shell and catalog view."""

    app_name: str = "青舟温室气体排放核算软件"
    app_version: str = "1.1.0"
    log_directory: Path | None = None
    catalog_database: Path | None = None
    records_database: Path | None = None
    projects_database: Path | None = None
    logo_resource: str = "branding/qingzhou_logo.png"

    def resolved_log_directory(self) -> Path:
        """Return the Windows per-user log directory without creating it."""

        if self.log_directory is not None:
            return self.log_directory

        local_app_data = os.environ.get("LOCALAPPDATA")
        base_directory = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base_directory / "QingzhouEnergySuite" / "carbon_accounting" / "logs"

    def logo_path(self) -> Path:
        """Resolve the packaged brand image copied during G00."""

        resource_parts = tuple(part for part in self.logo_resource.split("/") if part)
        return Path(files("resources").joinpath(*resource_parts))

    def resolved_catalog_database(self) -> Path:
        """Resolve the read-only catalog in source and standalone runtimes."""

        if self.catalog_database is not None:
            return self.catalog_database

        if getattr(sys, "frozen", False):
            bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
            bundled_path = bundle_root / "databases" / "catalog.sqlite"
            if bundled_path.exists():
                return bundled_path
            return Path(sys.executable).resolve().parent / "databases" / "catalog.sqlite"

        return Path(__file__).resolve().parents[2] / "build" / "databases" / "catalog.sqlite"

    def resolved_records_database(self) -> Path:
        """Resolve the per-user records store without creating it."""

        if self.records_database is not None:
            return self.records_database

        local_app_data = os.environ.get("LOCALAPPDATA")
        base_directory = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base_directory / "QingzhouEnergySuite" / "carbon_accounting" / "data" / "records.sqlite"

    def resolved_projects_database(self) -> Path:
        """Resolve mutable saved projects separately from immutable records."""

        if self.projects_database is not None:
            return self.projects_database

        local_app_data = os.environ.get("LOCALAPPDATA")
        base_directory = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base_directory / "QingzhouEnergySuite" / "carbon_accounting" / "data" / "projects.sqlite"

    def icons_directory(self) -> Path:
        """Resolve the shared SVG navigation icon directory."""

        return Path(files("resources").joinpath("icons"))
