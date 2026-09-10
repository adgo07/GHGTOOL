"""Centralized unit definitions and dimensional conversion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from .decimal_policy import DecimalPolicy, DecimalPolicyError


class UnitError(ValueError):
    """Base error for unit lookup and conversion failures."""


class UnknownUnitError(UnitError):
    """Raised when a canonical unit ID or alias is not registered."""


class IncompatibleUnitError(UnitError):
    """Raised when two units cannot be converted without an approved bridge."""


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    """Stable unit metadata; the symbol is display-only and not an ID."""

    unit_id: str
    symbol: str
    dimension: str
    factor_to_base: Decimal
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.unit_id):
            raise UnitError("unit_id must be a stable token")
        if not self.symbol.strip() or not self.dimension.strip():
            raise UnitError("unit symbol and dimension are required")
        if not isinstance(self.factor_to_base, Decimal) or not self.factor_to_base.is_finite():
            raise UnitError("unit factor must be a finite Decimal")
        if self.factor_to_base <= 0:
            raise UnitError("unit factor must be positive")


_DEFAULT_UNITS = (
    UnitDefinition("kg", "kg", "mass", Decimal("1")),
    UnitDefinition("t", "t", "mass", Decimal("1000")),
    UnitDefinition("kWh", "kWh", "energy", Decimal("1")),
    UnitDefinition("MWh", "MWh", "energy", Decimal("1000")),
    UnitDefinition("kJ", "kJ", "energy", Decimal("1")),
    UnitDefinition("GJ", "GJ", "energy", Decimal("1000000")),
    UnitDefinition("Nm3", "Nm³", "volume", Decimal("1"), ("Nm³",)),
    UnitDefinition(
        "ten_thousand_Nm3",
        "10⁴Nm³",
        "volume",
        Decimal("10000"),
        ("10^4Nm3", "10⁴Nm³", "10⁴ Nm³"),
    ),
    UnitDefinition("ratio", "ratio", "ratio", Decimal("1"), ("比例",)),
    UnitDefinition("percent", "%", "ratio", Decimal("0.01"), ("百分数", "%")),
    UnitDefinition("kgC", "kgC", "mass_carbon", Decimal("1")),
    UnitDefinition("tC", "tC", "mass_carbon", Decimal("1000")),
    UnitDefinition("kgCO2", "kgCO₂", "mass_co2", Decimal("1"), ("kgCO₂",)),
    UnitDefinition("tCO2", "tCO₂", "mass_co2", Decimal("1000"), ("tCO₂",)),
)


class UnitService:
    """Convert values using one registry and one DecimalPolicy."""

    def __init__(
        self,
        policy: DecimalPolicy | None = None,
        definitions: tuple[UnitDefinition, ...] = _DEFAULT_UNITS,
    ) -> None:
        self._policy = policy or DecimalPolicy()
        self._definitions = {definition.unit_id: definition for definition in definitions}
        self._aliases: dict[str, str] = {}
        for definition in definitions:
            for alias in (definition.unit_id, definition.symbol, *definition.aliases):
                normalized = self._normalize(alias)
                existing = self._aliases.get(normalized)
                if existing is not None and existing != definition.unit_id:
                    raise UnitError(f"duplicate unit alias: {alias}")
                self._aliases[normalized] = definition.unit_id

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().casefold()

    @property
    def policy(self) -> DecimalPolicy:
        return self._policy

    def resolve(self, unit: str) -> str:
        if not isinstance(unit, str):
            raise UnknownUnitError("unit must be a string")
        unit_id = self._aliases.get(self._normalize(unit))
        if unit_id is None:
            raise UnknownUnitError(f"unknown unit: {unit}")
        return unit_id

    def definition(self, unit: str) -> UnitDefinition:
        return self._definitions[self.resolve(unit)]

    def is_compatible(self, from_unit: str, to_unit: str) -> bool:
        source = self.definition(from_unit)
        target = self.definition(to_unit)
        if source.dimension == target.dimension:
            return True
        return {source.dimension, target.dimension} == {"mass_carbon", "mass_co2"}

    def assert_compatible(self, from_unit: str, to_unit: str) -> None:
        if not self.is_compatible(from_unit, to_unit):
            raise IncompatibleUnitError(f"cannot convert {from_unit} to {to_unit}")

    def convert(
        self,
        value: str | Decimal | int,
        from_unit: str,
        to_unit: str,
    ) -> Decimal:
        try:
            amount = self._policy.parse(value)
        except DecimalPolicyError as exc:
            raise UnitError(str(exc)) from exc
        source = self.definition(from_unit)
        target = self.definition(to_unit)
        if source.unit_id == target.unit_id:
            return amount
        self.assert_compatible(source.unit_id, target.unit_id)

        source_base = self._policy.multiply(amount, source.factor_to_base)
        if source.dimension == target.dimension:
            return self._policy.divide(source_base, target.factor_to_base)

        if source.dimension == "mass_carbon" and target.dimension == "mass_co2":
            co2_base = self._policy.multiply(source_base, self._policy.divide("44", "12"))
            return self._policy.divide(co2_base, target.factor_to_base)
        if source.dimension == "mass_co2" and target.dimension == "mass_carbon":
            carbon_base = self._policy.multiply(source_base, self._policy.divide("12", "44"))
            return self._policy.divide(carbon_base, target.factor_to_base)
        raise IncompatibleUnitError(f"cannot convert {from_unit} to {to_unit}")

    def conversion_factor(self, from_unit: str, to_unit: str) -> Decimal:
        return self.convert("1", from_unit, to_unit)
