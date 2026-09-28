"""Pilot-only Quantity/Unit/trace candidates for QZC-N01-C.

These structures intentionally live under tests/ so GHGTOOL cannot accidentally
publish them as a frozen platform Contract.  They answer whether the candidate
semantics are expressive enough for C, CO2, CH4 and CO2e before D-011/D-004 are
resolved centrally.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from packages.core.decimal_policy import DecimalPolicy


_MASS_UNITS = {"kg", "t"}
_MINIMAL_QUANTITY_TYPES = {"mass_carbon", "mass_co2", "mass_co2e"}
_EXTENDED_QUANTITY_TYPES = {"substance_mass", "co2e_mass"}
_SUBSTANCES = {"C", "CO2", "CH4"}


@dataclass(frozen=True, slots=True)
class MinimalQuantityCandidate:
    value: Decimal | str | int
    quantity_type: str
    unit_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", DecimalPolicy().parse(self.value))
        if self.quantity_type not in _MINIMAL_QUANTITY_TYPES:
            raise ValueError("unsupported minimal quantity_type")
        if self.unit_id not in _MASS_UNITS:
            raise ValueError("mass quantity requires kg or t")

    def as_json(self) -> dict[str, str]:
        return {
            "value": str(self.value),
            "quantity_type": self.quantity_type,
            "unit_id": self.unit_id,
        }


@dataclass(frozen=True, slots=True)
class EquivalenceBasisCandidate:
    method_id: str
    factor_id: str
    factor_value: Decimal | str | int
    time_horizon_years: int
    assessment_id: str
    source_id: str
    source_location: str
    factor_year: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "factor_value", DecimalPolicy().parse(self.factor_value))
        if self.method_id != "GWP":
            raise ValueError("N01-C candidate currently supports GWP equivalence only")
        if self.time_horizon_years <= 0:
            raise ValueError("time horizon must be positive")
        for value in (self.factor_id, self.assessment_id, self.source_id, self.source_location):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("equivalence provenance fields are required")

    def as_json(self) -> dict[str, Any]:
        result = asdict(self)
        result["factor_value"] = str(self.factor_value)
        return result


@dataclass(frozen=True, slots=True)
class ExtendedQuantityCandidate:
    value: Decimal | str | int
    quantity_type: str
    unit_id: str
    substance_id: str | None = None
    equivalence_basis: EquivalenceBasisCandidate | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", DecimalPolicy().parse(self.value))
        if self.quantity_type not in _EXTENDED_QUANTITY_TYPES:
            raise ValueError("unsupported extended quantity_type")
        if self.unit_id not in _MASS_UNITS:
            raise ValueError("mass quantity requires kg or t")
        if self.quantity_type == "substance_mass":
            if self.substance_id not in _SUBSTANCES:
                raise ValueError("substance_mass requires a registered substance_id")
            if self.equivalence_basis is not None:
                raise ValueError("substance_mass must not carry an equivalence basis")
        elif self.quantity_type == "co2e_mass":
            if self.substance_id is not None:
                raise ValueError("co2e_mass is an equivalence result, not a substance mass")
            if self.equivalence_basis is None:
                raise ValueError("co2e_mass requires equivalence_basis provenance")

    def as_json(self) -> dict[str, Any]:
        return {
            "value": str(self.value),
            "quantity_type": self.quantity_type,
            "unit_id": self.unit_id,
            "substance_id": self.substance_id,
            "equivalence_basis": (
                self.equivalence_basis.as_json() if self.equivalence_basis else None
            ),
        }


@dataclass(frozen=True, slots=True)
class RationalCoefficientCandidate:
    coefficient_id: str
    coefficient_type: str
    numerator: Decimal | str | int
    denominator: Decimal | str | int
    formula_id: str
    source_id: str
    source_location: str

    def __post_init__(self) -> None:
        policy = DecimalPolicy()
        object.__setattr__(self, "numerator", policy.parse(self.numerator))
        denominator = policy.parse(self.denominator)
        if denominator == 0:
            raise ValueError("coefficient denominator cannot be zero")
        object.__setattr__(self, "denominator", denominator)
        if self.coefficient_type not in {"STOICHIOMETRIC", "STANDARD_FORMULA"}:
            raise ValueError("coefficient_type must not masquerade as UNIT_CONVERSION")
        for value in (self.coefficient_id, self.formula_id, self.source_id, self.source_location):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("coefficient provenance fields are required")

    @property
    def expression(self) -> str:
        return f"{self.numerator}/{self.denominator}"

    def value(self, policy: DecimalPolicy | None = None) -> Decimal:
        selected = policy or DecimalPolicy()
        return selected.divide(self.numerator, self.denominator)

    def as_json(self) -> dict[str, str]:
        return {
            "coefficient_id": self.coefficient_id,
            "coefficient_type": self.coefficient_type,
            "rational_expression": self.expression,
            "numerator": str(self.numerator),
            "denominator": str(self.denominator),
            "formula_id": self.formula_id,
            "source_id": self.source_id,
            "source_location": self.source_location,
        }


@dataclass(frozen=True, slots=True)
class TransformationTraceCandidate:
    numeric_profile: str
    operation: str
    input_quantity: dict[str, Any]
    output_quantity: dict[str, Any]
    coefficient: dict[str, Any]
    candidate_only: bool = True

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


def apply_rational_transformation(
    source: ExtendedQuantityCandidate,
    coefficient: RationalCoefficientCandidate,
    *,
    output_substance_id: str,
    policy: DecimalPolicy | None = None,
) -> tuple[ExtendedQuantityCandidate, TransformationTraceCandidate]:
    if source.quantity_type != "substance_mass":
        raise ValueError("rational stoichiometric transformation requires substance_mass input")
    selected = policy or DecimalPolicy()
    value = selected.multiply(source.value, coefficient.value(selected))
    output = ExtendedQuantityCandidate(
        value=value,
        quantity_type="substance_mass",
        unit_id=source.unit_id,
        substance_id=output_substance_id,
    )
    trace = TransformationTraceCandidate(
        numeric_profile=f"decimal:{selected.precision}:{selected.rounding}",
        operation="apply_rational_coefficient",
        input_quantity=source.as_json(),
        output_quantity=output.as_json(),
        coefficient=coefficient.as_json(),
    )
    return output, trace


def apply_gwp_candidate(
    source: ExtendedQuantityCandidate,
    basis: EquivalenceBasisCandidate,
    *,
    policy: DecimalPolicy | None = None,
) -> tuple[ExtendedQuantityCandidate, TransformationTraceCandidate]:
    if source.quantity_type != "substance_mass" or source.substance_id is None:
        raise ValueError("GWP requires a greenhouse-gas substance mass input")
    selected = policy or DecimalPolicy()
    value = selected.multiply(source.value, basis.factor_value)
    output = ExtendedQuantityCandidate(
        value=value,
        quantity_type="co2e_mass",
        unit_id=source.unit_id,
        equivalence_basis=basis,
    )
    trace = TransformationTraceCandidate(
        numeric_profile=f"decimal:{selected.precision}:{selected.rounding}",
        operation="apply_gwp_characterization_factor",
        input_quantity=source.as_json(),
        output_quantity=output.as_json(),
        coefficient={
            "coefficient_id": basis.factor_id,
            "coefficient_type": "CHARACTERIZATION_FACTOR",
            "value": str(basis.factor_value),
            "time_horizon_years": basis.time_horizon_years,
            "assessment_id": basis.assessment_id,
            "source_id": basis.source_id,
            "source_location": basis.source_location,
            "factor_year": basis.factor_year,
        },
    )
    return output, trace


__all__ = [
    "EquivalenceBasisCandidate",
    "ExtendedQuantityCandidate",
    "MinimalQuantityCandidate",
    "RationalCoefficientCandidate",
    "TransformationTraceCandidate",
    "apply_gwp_candidate",
    "apply_rational_transformation",
]
