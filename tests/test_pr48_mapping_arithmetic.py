"""Independent Decimal arithmetic examples for the Mapping §16.5 candidates.

This checks the written equation and does not call the production Calculator,
validate inputs, or establish an official interpretation of the standard.
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


class CalcinationRoleCarbonExpansionTests(unittest.TestCase):
    def test_equal_role_contents_reduce_to_original_grouped_output_term(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            gc = Decimal("100")
            wfc = Decimal("0.9")
            cc = Decimal("20")
            ucc = Decimal("30")
            du = Decimal("10")
            role_content = Decimal("0.8")
            wvar = Decimal("0.10")
            wvar_c = Decimal("0.05")
            k1 = Decimal("0.35")

            role_output_carbon = (
                cc * role_content + ucc * role_content + du * role_content
            )
            expanded = (
                (gc * wfc - role_output_carbon) * Decimal("44") / Decimal("12")
                + (gc * wvar - cc * wvar_c)
                * k1
                * Decimal("44")
                / Decimal("16")
            )
            original_grouped = (
                (gc * wfc - (cc + ucc + du) * role_content)
                * Decimal("44")
                / Decimal("12")
                + (gc * wvar - cc * wvar_c)
                * k1
                * Decimal("44")
                / Decimal("16")
            )

        self.assertEqual(role_output_carbon, Decimal("48.0"))
        self.assertEqual(expanded, original_grouped)
        self.assertEqual(expanded, Decimal("162.6625"))

    def test_distinct_role_contents_are_multiplied_and_summed_independently(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            gc = Decimal("100")
            wfc = Decimal("0.9")
            cc = Decimal("20")
            ucc = Decimal("30")
            du = Decimal("10")
            wfc_c_cc = Decimal("0.8")
            wfc_c_ucc = Decimal("0.4")
            wfc_c_du = Decimal("0.25")
            wvar = Decimal("0.10")
            wvar_c = Decimal("0.05")
            k1 = Decimal("0.35")

            role_output_carbon = (
                cc * wfc_c_cc + ucc * wfc_c_ucc + du * wfc_c_du
            )
            expanded = (
                (gc * wfc - role_output_carbon) * Decimal("44") / Decimal("12")
                + (gc * wvar - cc * wvar_c)
                * k1
                * Decimal("44")
                / Decimal("16")
            )
            incorrectly_shared = (
                (gc * wfc - (cc + ucc + du) * wfc_c_cc)
                * Decimal("44")
                / Decimal("12")
                + (gc * wvar - cc * wvar_c)
                * k1
                * Decimal("44")
                / Decimal("16")
            )

        self.assertEqual(role_output_carbon, Decimal("30.5"))
        self.assertEqual(
            expanded,
            Decimal("226.8291666666666666666666666666666666667"),
        )
        self.assertEqual(incorrectly_shared, Decimal("162.6625"))
        self.assertNotEqual(expanded, incorrectly_shared)


class FumeMonitoringSegmentExampleTests(unittest.TestCase):
    def test_two_segments_use_their_own_days_without_annualizing_gaps(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            hm = Decimal("40")
            fch = Decimal("0.02")
            fox = Decimal("1")
            segments = (
                (Decimal("1000"), Decimal("1000"), Decimal("1")),
                (Decimal("500"), Decimal("2000"), Decimal("2")),
            )
            report_period_days = Decimal("365")
            # Both intervals belong to one smoke-source instance and one boundary.

            segment_results = [
                q * qvar * hm * fch * fox * days * Decimal("24")
                * Decimal("44") / Decimal("12") * Decimal("1e-9")
                for q, qvar, days in segments
            ]
            covered_segment_total = sum(segment_results, Decimal("0"))
            covered_days = sum((segment[2] for segment in segments), Decimal("0"))
            annualized_value = (
                covered_segment_total / covered_days * report_period_days
            )

        self.assertEqual(segment_results, [Decimal("0.0704"), Decimal("0.1408")])
        self.assertEqual(covered_days, Decimal("3"))
        self.assertEqual(covered_segment_total, Decimal("0.2112"))
        self.assertEqual(report_period_days, Decimal("365"))
        self.assertNotEqual(covered_segment_total, annualized_value)
        self.assertEqual(annualized_value, Decimal("25.696"))


if __name__ == "__main__":
    unittest.main()
