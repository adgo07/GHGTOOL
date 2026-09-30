"""N01-C numeric authority boundary for GB/T 32151.34.

N01-C originally fixed ambient ``Decimal`` context leakage by guarding the
calculator entry point.  Independent acceptance then found a second, distinct
failure mode: authoritative helpers such as ``_mul`` created a fresh default
``DecimalPolicy`` and therefore silently fell back to p40/HALF_UP even when a
calculator invocation explicitly requested p28, p34 or p50.

R1 defines one numeric authority scope per ``CarbonMaterialCalculator``
invocation.  The calculator's declared policy is carried by a ContextVar,
direct ``Decimal`` arithmetic runs under the matching local context, and the
legacy module helpers ``_d``/``_mul`` are rebound to consume that active policy.
Standalone formula-helper calls outside a calculator scope retain the historical
default profile for backwards compatibility; they are not the authoritative
calculator invocation covered by this pilot.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, localcontext
from functools import wraps
from typing import Iterator

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError

from . import carbon_material


N01C_ALGORITHM_VERSION = "CAR-SM01-2026-09-30-N01C-R1.1"
ORIGINAL_CALCULATE = carbon_material.CarbonMaterialCalculator.calculate
ORIGINAL_D = carbon_material._d
ORIGINAL_MUL = carbon_material._mul
_INSTALL_MARKER = "_qzc_n01c_declared_decimal_context_installed"
_ACTIVE_POLICY: ContextVar[DecimalPolicy | None] = ContextVar(
    "qzc_n01c_active_decimal_policy",
    default=None,
)


def current_declared_numeric_profile() -> DecimalPolicy | None:
    """Return the policy currently governing the authoritative calculation.

    This accessor exists primarily for R1 conformance instrumentation.  A
    ``None`` value means execution is outside an authoritative calculator
    invocation.
    """

    return _ACTIVE_POLICY.get()


@contextmanager
def declared_numeric_profile(policy: DecimalPolicy) -> Iterator[DecimalPolicy]:
    """Run one operation sequence under exactly ``policy``.

    Both direct ``Decimal`` expressions and policy-mediated helpers therefore
    observe the same precision and rounding mode.  The ContextVar makes nested
    helper calls explicit without introducing process-global mutable state.
    """

    token = _ACTIVE_POLICY.set(policy)
    try:
        with localcontext() as context:
            context.prec = policy.precision
            context.rounding = policy.rounding
            yield policy
    finally:
        _ACTIVE_POLICY.reset(token)


def _effective_helper_policy() -> DecimalPolicy:
    """Resolve the policy used by arithmetic helpers.

    Inside an authoritative calculator scope this *must* be the calculator's
    declared policy.  Outside that scope, standalone helper compatibility keeps
    the module's historical default p40/HALF_UP profile.
    """

    policy = _ACTIVE_POLICY.get()
    return policy if policy is not None else DecimalPolicy()


def _declared_d(value: str | Decimal | int) -> Decimal:
    """Parse a finite decimal without introducing a second arithmetic profile."""

    return _effective_helper_policy().parse(value)


def _declared_mul(*values: str | Decimal | int) -> Decimal:
    """Multiply using the active calculator profile, never a hidden p40 scope."""

    policy = _effective_helper_policy()
    result = Decimal("1")
    for value in values:
        result = policy.multiply(result, value)
    return result


def _assert_unit_policy_matches_calculator(calculator) -> None:
    """Reject a mixed Calculator/UnitService numeric profile.

    The normal constructor creates ``UnitService(self.policy)``.  R1 also
    covers dependency injection: an explicitly supplied UnitService may not
    silently carry a different precision/rounding/display profile.
    """

    unit_policy = calculator.units.policy
    if unit_policy != calculator.policy:
        raise DomainValidationError(
            "numeric profile mismatch: UnitService policy must match "
            "CarbonMaterialCalculator policy"
        )


def install_declared_decimal_context() -> None:
    """Install the idempotent R1 authoritative numeric-profile boundary."""

    calculator = carbon_material.CarbonMaterialCalculator
    if getattr(calculator, _INSTALL_MARKER, False):
        return

    # Formula functions resolve these names at call time.  Rebinding the two
    # helpers keeps the existing GB/T formula bodies intact while eliminating
    # their silent default-policy arithmetic inside a calculator invocation.
    carbon_material._d = _declared_d
    carbon_material._mul = _declared_mul

    original = ORIGINAL_CALCULATE

    @wraps(original)
    def calculate_with_declared_context(self, input_value, *, calculated_at=None):
        _assert_unit_policy_matches_calculator(self)
        with declared_numeric_profile(self.policy):
            return original(self, input_value, calculated_at=calculated_at)

    calculator.calculate = calculate_with_declared_context
    setattr(calculator, _INSTALL_MARKER, True)

    # The R1 authority change affects custom declared profiles and therefore
    # receives a distinct algorithm version, even though the production p40
    # formula mapping itself is unchanged.
    carbon_material.ALGORITHM_VERSION = N01C_ALGORITHM_VERSION


__all__ = [
    "N01C_ALGORITHM_VERSION",
    "ORIGINAL_CALCULATE",
    "ORIGINAL_D",
    "ORIGINAL_MUL",
    "current_declared_numeric_profile",
    "declared_numeric_profile",
    "install_declared_decimal_context",
]
