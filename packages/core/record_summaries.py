"""Small read models for record lists; formal records remain immutable domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from .models import PeriodType, RecordStatus


@dataclass(frozen=True, slots=True)
class RecordSummary:
    """Fields needed by recent-record and full-list projections only."""

    record_id: str
    standard_id: str
    standard_version: str | None
    created_at: datetime
    enterprise_name: str | None
    period_type: PeriodType
    period_start: date
    period_end: date
    total_amount: Decimal
    total_unit: str
    status: RecordStatus
