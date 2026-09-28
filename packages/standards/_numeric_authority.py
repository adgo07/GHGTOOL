"""N01-C numeric authority boundary for GB/T 32151.34.

The G06 calculator historically mixed DecimalPolicy operations with direct
``Decimal`` arithmetic.  Direct arithmetic inherited the caller's ambient
Decimal context.  This module installs one narrow guard at the authoritative
calculator entry point so the complete calculation sequence runs under the
calculator's declared DecimalPolicy without rewriting the standard formulas.
"""

from __future__ import annotations

from decimal import localcontext
from functools import wraps

from . import carbon_material


N01C_ALGORITHM_VERSION = "CAR-SM01-2026-09-29-N01C.1"
ORIGINAL_CALCULATE = carbon_material.CarbonMaterialCalculator.calculate
_INSTALL_MARKER = "_qzc_n01c_declared_decimal_context_installed"


def install_declared_decimal_context() -> None:
    """Install the idempotent authoritative Decimal-context guard."""

    calculator = carbon_material.CarbonMaterialCalculator
    if getattr(calculator, _INSTALL_MARKER, False):
        return

    original = ORIGINAL_CALCULATE

    @wraps(original)
    def calculate_with_declared_context(self, input_value, *, calculated_at=None):
        with localcontext() as context:
            context.prec = self.policy.precision
            context.rounding = self.policy.rounding
            return original(self, input_value, calculated_at=calculated_at)

    calculator.calculate = calculate_with_declared_context
    setattr(calculator, _INSTALL_MARKER, True)

    # A correctness change that can alter trailing authoritative digits must be
    # distinguishable in new records even though the GB/T formula mapping did
    # not change.
    carbon_material.ALGORITHM_VERSION = N01C_ALGORITHM_VERSION


__all__ = [
    "N01C_ALGORITHM_VERSION",
    "ORIGINAL_CALCULATE",
    "install_declared_decimal_context",
]
