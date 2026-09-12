"""Application-edge configuration for the G04 desktop shell.

This module only defines application-level settings. Business data and database
configuration stay outside the public shell and are passed to the application
query service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable configuration needed by the desktop shell and catalog view."""

    app_name: str = "青舟温室气体排放核算软件"
    app_version: str = "0.1.0"
    log_directory: Path | None = None
    catalog_database: Path | None = None
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
        """Resolve the packaged build output without creating or mutating it."""

        if self.catalog_database is not None:
            return self.catalog_database
        return Path(__file__).resolve().parents[2] / "build" / "databases" / "catalog.sqlite"

    def icons_directory(self) -> Path:
        """Resolve the shared SVG navigation icon directory."""

        return Path(files("resources").joinpath("icons"))
