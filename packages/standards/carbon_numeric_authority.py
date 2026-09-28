"""Declared Numeric authority for GB/T 32151.34 authoritative calculations.

QZC-N01-C found that the frozen G06 formulas used direct ``Decimal`` operators
without an enclosing declared context.  Their mathematical formula was correct,
but repeating coefficients such as 44/12 and interpolation could inherit the
caller's global Decimal precision/rounding.

This module installs one narrow authority boundary around the existing formula
implementation instead of rewriting formula expressions into per-operator
wrappers.  The rule is:

    parse -> declared DecimalPolicy context -> formula operation sequence -> result

The default remains the existing GHGTOOL DecimalPolicy (40 digits,
ROUND_HALF_UP).  An explicit policy is accepted by standalone formula functions
for N01-C precision/conformance tests.  A CarbonMaterialCalculator always uses
its own ``self.policy`` for the complete calculation sequence.
"""

from __future__ import annotations

from contextvars import ContextVar
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from packages.core.decimal_policy import DecimalPolicy


NUMERIC_AUTHORITY_VERSION = "CAR-SM01-2026-09-29-N01C.1"

_F = TypeVar("_F", bound=Callable[..., Any])
_ACTIVE_POLICY: ContextVar[DecimalPolicy | None] = ContextVar(
    "qzc_n01_c_carbon_numeric_policy",
    default=None,
)


def _selected_policy(explicit: DecimalPolicy | None = None) -> DecimalPolicy:
    return explicit or _ACTIVE_POLICY.get() or DecimalPolicy()


def _authoritative_formula(function: _F) -> _F:
    """Run one standalone formula under an explicit or active policy."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        explicit = kwargs.pop("policy", None)
        if explicit is not None and not isinstance(explicit, DecimalPolicy):
            raise TypeError("policy must be a DecimalPolicy")
        policy = _selected_policy(explicit)
        token = _ACTIVE_POLICY.set(policy)
        try:
            with policy.calculation_context():
                return function(*args, **kwargs)
        finally:
            _ACTIVE_POLICY.reset(token)

    return cast(_F, wrapped)


def install_carbon_numeric_authority() -> None:
    """Install the N01-C Numeric boundary once for the carbon standard module."""

    from . import carbon_material as carbon

    if getattr(carbon, "_QZC_N01_C_NUMERIC_AUTHORITY_INSTALLED", False):
        return

    # Private parse/multiply helpers must use the same active policy as their
    # owning formula.  This makes an explicitly injected Calculator policy real,
    # rather than allowing _mul() to silently instantiate the default policy.
    def declared_d(value: str | Decimal | int) -> Decimal:
        return _selected_policy().parse(value)

    def declared_mul(*values: str | Decimal | int) -> Decimal:
        policy = _selected_policy()
        result = Decimal("1")
        for value in values:
            result = policy.multiply(result, value)
        return result

    carbon._d = declared_d
    carbon._mul = declared_mul

    formula_names = (
        "fuel_volume_emission",
        "fuel_mass_emission",
        "fuel_heat_emission",
        "fuel_energy_from_volume",
        "fuel_energy_from_mass",
        "calcination_emission",
        "baking_emission",
        "graphitization_emission",
        "fume_incineration_emission",
        "fgd_emission",
        "purchased_electricity_emission",
        "purchased_heat_emission",
        "direct_emission",
        "indirect_emission",
        "total_emission",
        "_linear_interpolate",
        "superheated_steam_enthalpy",
        "saturated_steam_enthalpy",
    )
    for name in formula_names:
        setattr(carbon, name, _authoritative_formula(getattr(carbon, name)))

    original_calculate = carbon.CarbonMaterialCalculator.calculate

    @wraps(original_calculate)
    def calculate_with_declared_numeric_context(self: Any, *args: Any, **kwargs: Any) -> Any:
        policy = self.policy
        if not isinstance(policy, DecimalPolicy):
            raise TypeError("CarbonMaterialCalculator.policy must be a DecimalPolicy")
        token = _ACTIVE_POLICY.set(policy)
        try:
            # This single boundary also covers accumulator + / - operations in
            # calculate(), so no caller/global Decimal context can affect them.
            with policy.calculation_context():
                return original_calculate(self, *args, **kwargs)
        finally:
            _ACTIVE_POLICY.reset(token)

    carbon.CarbonMaterialCalculator.calculate = calculate_with_declared_numeric_context

    # The formula mapping is unchanged, but authoritative numeric semantics are
    # now deterministic and therefore need a distinct calculator version for
    # newly-created records.  Historical records are never rewritten.
    carbon.ALGORITHM_VERSION = NUMERIC_AUTHORITY_VERSION
    carbon._QZC_N01_C_NUMERIC_AUTHORITY_INSTALLED = True


__all__ = ["NUMERIC_AUTHORITY_VERSION", "install_carbon_numeric_authority"]
