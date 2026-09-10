"""Platform-independent decimal handling for the domain layer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
    InvalidOperation,
    localcontext,
)
from typing import Callable


class DecimalPolicyError(ValueError):
    """Raised when a value cannot be safely handled as a Decimal."""


_NUMBER_PATTERN = re.compile(
    r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$"
)
_VALID_ROUNDING_MODES = frozenset(
    {
        ROUND_05UP,
        ROUND_CEILING,
        ROUND_DOWN,
        ROUND_FLOOR,
        ROUND_HALF_DOWN,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_UP,
    }
)


@dataclass(frozen=True, slots=True)
class DecimalPolicy:
    """One shared precision and rounding policy for domain calculations."""

    precision: int = 40
    display_places: int = 2
    rounding: str = ROUND_HALF_UP

    def __post_init__(self) -> None:
        if not isinstance(self.precision, int) or isinstance(self.precision, bool):
            raise DecimalPolicyError("precision must be an integer")
        if self.precision < 28:
            raise DecimalPolicyError("precision must be at least 28 digits")
        if not isinstance(self.display_places, int) or isinstance(self.display_places, bool):
            raise DecimalPolicyError("display_places must be an integer")
        if self.display_places < 0:
            raise DecimalPolicyError("display_places cannot be negative")
        if self.rounding not in _VALID_ROUNDING_MODES:
            raise DecimalPolicyError("rounding must be a supported Decimal rounding mode")

    def parse(self, value: str | Decimal | int) -> Decimal:
        """Parse a strict decimal input without accepting binary floats."""

        if isinstance(value, bool) or isinstance(value, float):
            raise DecimalPolicyError("binary float and boolean values are not accepted")
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise DecimalPolicyError("Decimal value must be finite")
            text = str(value)
        elif isinstance(value, int):
            text = str(value)
        elif isinstance(value, str):
            text = value.strip()
        else:
            raise DecimalPolicyError("value must be a string, Decimal, or integer")

        if not _NUMBER_PATTERN.fullmatch(text):
            raise DecimalPolicyError("value is not a strict decimal literal")
        try:
            parsed = Decimal(text)
        except InvalidOperation as exc:
            raise DecimalPolicyError("value is not a valid Decimal") from exc
        if not parsed.is_finite():
            raise DecimalPolicyError("Decimal value must be finite")
        return parsed

    def _binary_operation(
        self,
        left: str | Decimal | int,
        right: str | Decimal | int,
        operation: Callable[[Decimal, Decimal], Decimal],
    ) -> Decimal:
        left_decimal = self.parse(left)
        right_decimal = self.parse(right)
        with localcontext() as context:
            context.prec = self.precision
            context.rounding = self.rounding
            result = operation(left_decimal, right_decimal)
            if not result.is_finite():
                raise DecimalPolicyError("operation produced a non-finite Decimal")
            return +result

    def add(self, left: str | Decimal | int, right: str | Decimal | int) -> Decimal:
        return self._binary_operation(left, right, lambda a, b: a + b)

    def subtract(self, left: str | Decimal | int, right: str | Decimal | int) -> Decimal:
        return self._binary_operation(left, right, lambda a, b: a - b)

    def multiply(self, left: str | Decimal | int, right: str | Decimal | int) -> Decimal:
        return self._binary_operation(left, right, lambda a, b: a * b)

    def divide(self, left: str | Decimal | int, right: str | Decimal | int) -> Decimal:
        right_decimal = self.parse(right)
        if right_decimal.is_zero():
            raise DecimalPolicyError("division by zero")
        return self._binary_operation(left, right_decimal, lambda a, b: a / b)

    def round_for_display(
        self,
        value: str | Decimal | int,
        places: int | None = None,
    ) -> Decimal:
        decimal_value = self.parse(value)
        target_places = self.display_places if places is None else places
        if target_places < 0:
            raise DecimalPolicyError("display places cannot be negative")
        quantizer = Decimal(1).scaleb(-target_places)
        with localcontext() as context:
            context.prec = max(self.precision, len(decimal_value.as_tuple().digits) + target_places + 2)
            context.rounding = self.rounding
            return decimal_value.quantize(quantizer, rounding=self.rounding)

    def format_for_display(
        self,
        value: str | Decimal | int,
        places: int | None = None,
    ) -> str:
        target_places = self.display_places if places is None else places
        rounded = self.round_for_display(value, target_places)
        return f"{rounded:.{target_places}f}"

    def is_close(
        self,
        left: str | Decimal | int,
        right: str | Decimal | int,
        tolerance: str | Decimal | int = "0.0000000000000000000000000001",
    ) -> bool:
        with localcontext() as context:
            context.prec = self.precision
            return abs(self.parse(left) - self.parse(right)) <= self.parse(tolerance)
