"""GB/T 32151.34 authoritative facade with an explicit Decimal context.

QZC-N01-C found that the original G06 implementation mixed DecimalPolicy
operations with direct ``Decimal`` arithmetic.  Direct arithmetic inherited the
caller's ambient Decimal context, so the same authoritative calculation could
change in trailing digits when an external caller changed ``getcontext()``.

The frozen formula implementation is retained byte-for-byte in
``_carbon_material_impl``.  This facade makes the production calculator enter
its declared DecimalPolicy context before any formula, interpolation, summation
or validation arithmetic runs.  The move is intentionally narrow: formulas,
UnitService semantics and the public input/result models are unchanged.
"""

from __future__ import annotations

from decimal import localcontext

from . import _carbon_material_impl as _impl
from ._carbon_material_impl import *  # noqa: F401,F403


# Numeric correctness change only.  The standard formula/mapping version remains
# unchanged, while the algorithm version records the declared-context boundary.
ALGORITHM_VERSION = "CAR-SM01-2026-09-29-N01C.1"
_impl.ALGORITHM_VERSION = ALGORITHM_VERSION


class CarbonMaterialCalculator(_impl.CarbonMaterialCalculator):
    """Run the authoritative G06 chain inside the calculator's DecimalPolicy."""

    def calculate(self, input_value, *, calculated_at=None):
        with localcontext() as context:
            context.prec = self.policy.precision
            context.rounding = self.policy.rounding
            return super().calculate(input_value, calculated_at=calculated_at)


__all__ = _impl.__all__
