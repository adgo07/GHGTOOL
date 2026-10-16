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
    @staticmethod
    def segment_result(q, qvar, hm, fch, fox, days):
        # Independent Decimal expansion of Mapping §7.2/TV-CAR-POL-018, not production code.
        return (
            q * qvar * hm * fch * fox * days * Decimal("24")
            * Decimal("44") / Decimal("12") * Decimal("1e-9")
        )

    def test_complete_annual_coverage_sums_valid_nonoverlapping_segments(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            intervals = ((0, 180), (180, 365))
            segment_inputs = (
                (Decimal("1000"), Decimal("1000"), Decimal("180")),
                (Decimal("500"), Decimal("2000"), Decimal("185")),
            )
            hm = Decimal("40")
            fch = Decimal("0.02")
            fox = Decimal("1")
            segment_results = [
                self.segment_result(q, qvar, hm, fch, fox, days)
                for q, qvar, days in segment_inputs
            ]
            covered_total = sum(segment_results, Decimal("0"))
            covered_days = sum((end - start for start, end in intervals), 0)
            complete = (
                intervals[0][0] == 0
                and intervals[-1][1] == 365
                and all(left[1] == right[0] for left, right in zip(intervals, intervals[1:]))
            )

        self.assertTrue(complete)
        self.assertEqual(covered_days, 365)
        self.assertEqual(segment_results, [Decimal("12.672"), Decimal("13.024")])
        self.assertEqual(covered_total, Decimal("25.696"))

    def test_gap_keeps_covered_segment_subtotal_without_annualizing_or_zero_fill(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            intervals = ((0, 180), (185, 365))
            segment_inputs = (
                (Decimal("1000"), Decimal("1000"), Decimal("180")),
                (Decimal("500"), Decimal("2000"), Decimal("180")),
            )
            hm = Decimal("40")
            fch = Decimal("0.02")
            fox = Decimal("1")
            segment_results = [
                self.segment_result(q, qvar, hm, fch, fox, days)
                for q, qvar, days in segment_inputs
            ]
            covered_total = sum(segment_results, Decimal("0"))
            covered_days = sum((end - start for start, end in intervals), 0)
            has_gap = intervals[0][1] < intervals[1][0]

        self.assertTrue(has_gap)
        self.assertEqual(covered_days, 360)
        self.assertEqual(segment_results, [Decimal("12.672"), Decimal("12.672")])
        self.assertEqual(covered_total, Decimal("25.344"))
        self.assertNotEqual(covered_total, Decimal("25.696"))

    def test_overlap_is_invalid_within_one_instance_but_other_instances_can_be_concurrent(self):
        same_instance = ((0, 190), (180, 365))
        overlap_days = min(same_instance[0][1], same_instance[1][1]) - max(
            same_instance[0][0], same_instance[1][0]
        )
        self.assertEqual(overlap_days, 10)

        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            report_period = (0, 365)
            instances = {
                "source-A": (report_period, Decimal("1000"), Decimal("1000")),
                "source-B": (report_period, Decimal("500"), Decimal("1000")),
            }
            totals = {
                source: self.segment_result(
                    q, qvar, Decimal("40"), Decimal("0.02"), Decimal("1"), Decimal("365")
                )
                for source, (interval, q, qvar) in instances.items()
            }
            combined = sum(totals.values(), Decimal("0"))

        self.assertEqual(instances["source-A"][0], instances["source-B"][0])
        self.assertEqual(totals, {"source-A": Decimal("25.696"), "source-B": Decimal("12.848")})
        self.assertEqual(combined, Decimal("38.544"))

    def test_hour_input_is_normalized_to_days_once_before_formula_uses_times_24(self):
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP

            entered_hours = Decimal("24")
            segment_days = entered_hours / Decimal("24")
            result = self.segment_result(
                Decimal("1000"), Decimal("1000"), Decimal("40"),
                Decimal("0.02"), Decimal("1"), segment_days,
            )

        self.assertEqual(segment_days, Decimal("1"))
        self.assertEqual(result, Decimal("0.0704"))
        self.assertNotEqual(result, Decimal("1.6896"))


if __name__ == "__main__":
    unittest.main()
