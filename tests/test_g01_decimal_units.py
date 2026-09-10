from __future__ import annotations

from decimal import Decimal
import unittest

from packages.core import DecimalPolicy, DecimalPolicyError
from packages.core.units import IncompatibleUnitError, UnitError, UnitService, UnknownUnitError


class DecimalPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = DecimalPolicy()

    def test_precision_and_rounding_are_explicit(self) -> None:
        self.assertGreaterEqual(self.policy.precision, 28)
        self.assertEqual(self.policy.round_for_display("1.235"), Decimal("1.24"))
        self.assertEqual(self.policy.round_for_display("-1.235"), Decimal("-1.24"))
        self.assertEqual(self.policy.format_for_display("1"), "1.00")
        self.assertEqual(len(self.policy.divide("1", "3").as_tuple().digits), 40)
        with self.assertRaises(DecimalPolicyError):
            DecimalPolicy(precision=27)
        self.assertEqual(DecimalPolicy(rounding="ROUND_DOWN").round_for_display("1.239"), Decimal("1.23"))
        with self.assertRaises(DecimalPolicyError):
            DecimalPolicy(rounding="NOT_A_ROUNDING_MODE")

    def test_parse_rejects_float_special_values_and_loose_literals(self) -> None:
        self.assertEqual(self.policy.parse(" 12.50 "), Decimal("12.50"))
        for invalid in (0.1, True, "", "NaN", "Infinity", "1,000", "1 000"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(DecimalPolicyError):
                    self.policy.parse(invalid)  # type: ignore[arg-type]

    def test_intermediate_arithmetic_stays_decimal(self) -> None:
        value = self.policy.multiply("1.234567890123456789", "3")
        self.assertEqual(value, Decimal("3.703703670370370367"))


class UnitServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.units = UnitService()

    def test_first_batch_conversions(self) -> None:
        self.assertEqual(self.units.convert("1", "t", "kg"), Decimal("1000"))
        self.assertEqual(self.units.convert("1000", "kg", "t"), Decimal("1"))
        self.assertEqual(self.units.convert("1", "MWh", "kWh"), Decimal("1000"))
        self.assertEqual(self.units.convert("1", "GJ", "kJ"), Decimal("1000000"))
        self.assertEqual(self.units.convert("1", "10⁴ Nm³", "Nm3"), Decimal("10000"))
        self.assertEqual(self.units.convert("1", "%", "ratio"), Decimal("0.01"))

    def test_carbon_to_co2_bridge_uses_44_over_12(self) -> None:
        co2 = self.units.convert("1", "tC", "tCO2")
        self.assertTrue(self.units.policy.is_close(co2, "3.666666666666666666666666666666666666667", "1E-38"))
        carbon_again = self.units.convert(co2, "tCO2", "tC")
        self.assertTrue(self.units.policy.is_close(carbon_again, "1", "1E-38"))

    def test_incompatible_unknown_and_float_units_fail(self) -> None:
        self.assertFalse(self.units.is_compatible("kWh", "kg"))
        with self.assertRaises(IncompatibleUnitError):
            self.units.convert("1", "kWh", "kg")
        with self.assertRaises(UnknownUnitError):
            self.units.convert("1", "not-a-unit", "kg")
        with self.assertRaises(UnitError):
            self.units.convert(0.1, "kg", "t")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
