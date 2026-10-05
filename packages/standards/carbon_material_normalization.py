"""Pure-Python normalization of standard material rows into calculator inputs.

This module performs only the weighted activity-data aggregation prescribed by
the frozen carbon-material mapping. It does not implement emission formulas.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from packages.core.decimal_policy import DecimalPolicy


@dataclass(frozen=True, slots=True)
class MaterialAmount:
    mass: Decimal
    fixed_carbon: Decimal | None = None
    volatile_matter: Decimal | None = None

    def __post_init__(self) -> None:
        policy = DecimalPolicy()
        object.__setattr__(self, "mass", policy.parse(self.mass))
        if self.fixed_carbon is not None:
            object.__setattr__(self, "fixed_carbon", policy.parse(self.fixed_carbon))
        if self.volatile_matter is not None:
            object.__setattr__(self, "volatile_matter", policy.parse(self.volatile_matter))


_POLICY = DecimalPolicy()


def total_mass(rows: Iterable[MaterialAmount]) -> Decimal:
    total = Decimal(0)
    for row in rows:
        total = _POLICY.add(total, row.mass)
    return total


def weighted_fraction(rows: Iterable[MaterialAmount], field: str) -> Decimal:
    """Return a mass-weighted fraction, using the GHGTOOL Decimal Profile."""

    material_rows = tuple(rows)
    total = total_mass(material_rows)
    if total == 0:
        return Decimal(0)
    numerator = Decimal(0)
    for row in material_rows:
        fraction = getattr(row, field)
        if fraction is None:
            if row.mass == 0:
                continue
            raise ValueError(f"positive material mass requires {field}")
        numerator = _POLICY.add(numerator, _POLICY.multiply(row.mass, fraction))
    return _POLICY.divide(numerator, total)


def carbon_mass(rows: Iterable[MaterialAmount]) -> Decimal:
    """Sum material mass × fixed-carbon fraction into tC."""

    total = Decimal(0)
    for row in rows:
        if row.fixed_carbon is None:
            if row.mass == 0:
                continue
            raise ValueError("positive material mass requires fixed_carbon")
        total = _POLICY.add(total, _POLICY.multiply(row.mass, row.fixed_carbon))
    return total


__all__ = ["MaterialAmount", "carbon_mass", "total_mass", "weighted_fraction"]
