"""G00 application configuration.

This module only defines application-level settings. Business data and database
configuration are intentionally deferred to later HANDOFF stages.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable configuration needed by the minimal desktop shell."""

    app_name: str = "青舟温室气体排放核算软件"
    app_version: str = "0.1.0"
    log_directory: Path | None = None
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

