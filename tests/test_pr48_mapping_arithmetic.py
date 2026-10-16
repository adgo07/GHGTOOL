"""Independent Decimal arithmetic for the Mapping §16.5 R02 example.

This checks the written equation and does not call the production Calculator,
validate inputs, or approve Issue 018 different-output expansion.
"""
import unittest
from decimal import Decimal, ROUND_HALF_UP, localcontext


class CalcinationSharedCarbonContentExampleTests(unittest.TestCase):
    def test_zero_cc_does_not_remove_shared_wfc_c_when_ucc_is_positive(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            gc = Decimal("10")
            wfc = Decimal("0.9")
            cc = Decimal("0")
            ucc = Decimal("5")
            du = Decimal("0")
            shared_wfc_c = Decimal("0.8")
            wvar = Decimal("0")
            wvar_c = Decimal("0")
            k1 = Decimal("0.35")

            correct = (
                gc * wfc - (cc + ucc + du) * shared_wfc_c
            ) * Decimal("44") / Decimal("12") + (
                gc * wvar - cc * wvar_c
            ) * k1 * Decimal("44") / Decimal("16")
            output_term_dropped = gc * wfc * Decimal("44") / Decimal("12")
            overstatement = output_term_dropped - correct

        self.assertEqual(
            correct,
            Decimal("18.33333333333333333333333333333333333333"),
        )
        self.assertEqual(output_term_dropped, Decimal("33"))
        self.assertEqual(
            overstatement,
            Decimal("14.66666666666666666666666666666666666667"),
        )


if __name__ == "__main__":
    unittest.main()
