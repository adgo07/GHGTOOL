"""Issue020 专属独立预期和边界测试；不声称正式入口已接管。

映射 TV-CAR-POL-017/018 的有限位预期用1e-37绝对误差核验，仅用于
p40工作修约的数值参考；覆盖/错误/身份断言均精确，无业务epsilon。
"""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import unittest

from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.standards.carbon_material import FumeIncinerationInput, InputValue
from packages.standards.carbon_material_fume_segments import (
    FumeMonitoringSegment, FumeReportingWindow, evaluate_fume_segments, parse_fume_timestamp,
)

START = datetime(2025, 1, 1)
POLICY = DecimalPolicy()
PROFILE = "GHGTOOL_CARBON_DECIMAL40_CURRENT"


def window(source="source-A", boundary="stack-1", days=365):
    return FumeReportingWindow(source, boundary, START, START + timedelta(days=days))


def segment(start=0, end=1, *, source="source-A", boundary="stack-1", sid="segment-1", **values):
    defaults = dict(q="1000", qvar="1000", hm="40", fch="0.02", fox="1",
                    duration=str(end - start), instance_id=source)
    defaults.update(values)
    return FumeMonitoringSegment(source, boundary, sid,
                                 START + timedelta(days=start), START + timedelta(days=end),
                                 FumeIncinerationInput(**defaults))


def evaluate(segments, windows=None, **kwargs):
    return evaluate_fume_segments(segments, windows if windows is not None else (window(),),
                                  policy=kwargs.get("policy", POLICY),
                                  numeric_profile_id=kwargs.get("numeric_profile_id", PROFILE))


class FumeSegmentArithmeticTests(unittest.TestCase):
    def assertMappingValue(self, actual, expected):
        # 数值参考容差只检查独立有限位算例，不控制正式业务状态。
        with localcontext() as ctx:
            ctx.prec = 60
            self.assertLessEqual(abs(actual - Decimal(expected)), Decimal("1e-37"))

    def test_mapping_two_segments_keep_partial_result_and_362_day_gap(self):
        result = evaluate((segment(), segment(1, 3, sid="segment-2", q="500", qvar="2000")))
        coverage = result.coverage[0]
        self.assertMappingValue(coverage.segments[0].amount_tco2, "0.0704")
        self.assertMappingValue(coverage.segments[1].amount_tco2, "0.1408")
        self.assertMappingValue(result.covered_amount_tco2, "0.2112")
        self.assertFalse(result.complete)
        self.assertEqual(coverage.covered_duration_days, Decimal("3"))
        self.assertEqual(coverage.uncovered_intervals, ((START + timedelta(days=3), START + timedelta(days=365)),))

    def test_full_year_uses_each_segment_and_accepts_adjacency(self):
        result = evaluate((segment(180, 365, sid="s2", q="500", qvar="2000"), segment(0, 180)))
        self.assertTrue(result.complete)
        self.assertEqual(result.coverage[0].uncovered_intervals, ())
        self.assertEqual(result.coverage[0].covered_duration_days, Decimal("365"))
        self.assertMappingValue(result.covered_amount_tco2, "25.696")

    def test_different_q_and_qvar_are_paired_not_separately_averaged(self):
        result = evaluate((segment(), segment(1, 2, sid="s2", q="500", qvar="2000")))
        self.assertMappingValue(result.covered_amount_tco2, "0.1408")
        # 两段Q与QVar分别取均值会得到0.1584，不能使用。
        self.assertGreater(abs(result.covered_amount_tco2 - Decimal("0.1584")), Decimal("0.01"))

    def test_24_hours_and_one_day_are_exactly_equivalent(self):
        days = evaluate((segment(),))
        hours = evaluate((segment(duration=InputValue("24", "h")),))
        self.assertEqual(days.covered_amount_tco2, hours.covered_amount_tco2)
        self.assertEqual(hours.coverage[0].segments[0].duration_days, Decimal("1"))
        self.assertMappingValue(hours.covered_amount_tco2, "0.0704")

    def test_one_hour_duration_does_not_fail_due_to_division_by_24(self):
        item = segment(duration=InputValue("1", "h"))
        item = replace(item, end=START + timedelta(hours=1))
        result = evaluate((item,))
        self.assertEqual(result.coverage[0].segments[0].duration_days, POLICY.divide(1, 24))
        self.assertMappingValue(result.covered_amount_tco2, "0.002933333333333333333333333333333333333333")

    def test_percent_is_normalized_once(self):
        ratio = evaluate((segment(fox="0.9"),))
        percent = evaluate((segment(fox=InputValue("90", "%")),))
        self.assertEqual(percent.covered_amount_tco2, ratio.covered_amount_tco2)
        self.assertEqual(percent.coverage[0].segments[0].fox, Decimal("0.90"))

    def test_each_segment_keeps_its_own_hm_fch_fox(self):
        result = evaluate((segment(), segment(1, 2, sid="s2", hm="20", fch="0.04", fox="0.5")))
        self.assertMappingValue(result.covered_amount_tco2, "0.1056")
        self.assertEqual(result.coverage[0].segments[1].hm, Decimal("20"))

    def test_zero_measurement_is_valid_with_proved_coverage(self):
        result = evaluate((segment(q="0"),), (window(days=1),))
        self.assertTrue(result.complete)
        self.assertEqual(result.covered_amount_tco2, Decimal("0"))

    def test_declared_profiles_propagate_and_ambient_precision_cannot_change_result(self):
        item = segment(q="1234.56789123456789123456789123456789", qvar="987.654321987654321")
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_DOWN)):
            policy = DecimalPolicy(precision=precision, rounding=rounding)
            with localcontext() as ctx:
                ctx.prec, ctx.rounding = precision, rounding
                coefficient = Decimal(44) / Decimal(12)
                expected = Decimal(1)
                for factor in (item.measurements.q.value, item.measurements.qvar.value,
                               Decimal("40"), Decimal(".02"), Decimal(1), Decimal(1),
                               Decimal(24), coefficient, Decimal("1e-9")):
                    expected = expected * factor
            for ambient in (6, 17, 60):
                with localcontext() as ctx:
                    ctx.prec, ctx.rounding = ambient, ROUND_DOWN
                    result = evaluate((item,), policy=policy, numeric_profile_id=f"TEST_P{precision}_{rounding}")
                    self.assertEqual(result.covered_amount_tco2, expected)
                    self.assertEqual(result.policy, policy)
                    self.assertEqual(ctx.prec, ambient)

    def test_result_retains_numeric_and_issue_identity_and_immutable_input(self):
        item = segment()
        result = evaluate((item,))
        self.assertEqual(result.numeric_profile_id, PROFILE)
        self.assertEqual(result.numeric_contract_version, "v1")
        self.assertEqual(result.standard_issue_id, "GHG-STD-32151-34-020")
        self.assertIs(result.coverage[0].segments[0].segment, item)
        with self.assertRaises(FrozenInstanceError):
            result.coverage[0].covered_amount_tco2 = Decimal(0)


class FumeCoverageTests(unittest.TestCase):
    def test_gap_does_not_annualize(self):
        result = evaluate((segment(0, 180), segment(185, 365, sid="s2", q="500", qvar="2000")))
        self.assertFalse(result.complete)
        self.assertEqual(result.coverage[0].covered_duration_days, Decimal("360"))
        self.assertEqual(result.coverage[0].uncovered_intervals, ((START + timedelta(days=180), START + timedelta(days=185)),))
        FumeSegmentArithmeticTests().assertMappingValue(result.covered_amount_tco2, "25.344")

    def test_concurrent_real_sources_are_not_deduplicated(self):
        result = evaluate((segment(0, 365), segment(0, 365, source="source-B", q="500")),
                          (window(), window(source="source-B")))
        self.assertTrue(result.complete)
        self.assertEqual(len(result.coverage), 2)
        FumeSegmentArithmeticTests().assertMappingValue(result.covered_amount_tco2, "38.544")

    def test_other_boundary_cannot_fill_this_boundary_gap(self):
        result = evaluate((segment(0, 180), segment(180, 365, boundary="stack-2")),
                          (window(), window(boundary="stack-2")))
        self.assertFalse(result.complete)
        self.assertFalse(result.coverage[0].complete)
        self.assertFalse(result.coverage[1].complete)
        self.assertEqual([x.reporting_window.metering_boundary_id for x in result.coverage], ["stack-1", "stack-2"])

    def test_concurrent_boundaries_are_not_deduplicated(self):
        result = evaluate((segment(0, 365), segment(0, 365, boundary="stack-2")),
                          (window(), window(boundary="stack-2")))
        self.assertTrue(result.complete)
        self.assertEqual(len(result.coverage), 2)

    def test_empty_window_retains_whole_gap_not_complete_zero_emissions(self):
        result = evaluate(())
        self.assertFalse(result.complete)
        self.assertEqual(result.coverage[0].segments, ())
        self.assertEqual(result.coverage[0].uncovered_intervals, ((window().start, window().end),))
        self.assertFalse(evaluate((), ()).complete)

    def test_leading_and_trailing_gaps_are_explicit(self):
        result = evaluate((segment(1, 2),), (window(days=3),))
        self.assertEqual(result.coverage[0].uncovered_intervals,
                         ((START, START + timedelta(days=1)), (START + timedelta(days=2), START + timedelta(days=3))))


class FumeInvalidInputTests(unittest.TestCase):
    def test_overlap_blocks_entire_call_including_nested_and_duplicate_intervals(self):
        for a, b in ((segment(0, 190), segment(180, 365, sid="s2")),
                     (segment(0, 3), segment(1, 2, sid="s2")),
                     (segment(), segment(sid="s2"))):
            with self.subTest(b=b):
                with self.assertRaisesRegex(DomainValidationError, "重叠"):
                    evaluate((a, b))

    def test_invalid_numeric_values_are_not_skipped(self):
        for field in ("q", "qvar", "hm", "fch", "fox", "duration"):
            for value in (None, "-1"):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(DomainValidationError):
                        evaluate((segment(), segment(1, 2, sid="bad", **{field: value})))
        for value in ("NaN", "Infinity", "", 1.0, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    evaluate((segment(q=value),))

    def test_wrong_units_and_out_of_range_ratio_fail(self):
        for field, value in (("q", InputValue("1", "kg")), ("fch", InputValue("1", "t")),
                             ("duration", InputValue("24", "kg")), ("fox", "1.01"),
                             ("fox", InputValue("100.00000000000000000000000000000000000000001", "%"))):
            with self.subTest(field=field):
                with self.assertRaises(DomainValidationError):
                    evaluate((segment(**{field: value}),))

    def test_duration_mismatch_cannot_borrow_report_period(self):
        for duration in ("365", "0", InputValue("25", "h"),
                         InputValue("24.000000000000000000000000000000000000000001", "h")):
            with self.subTest(duration=duration):
                with self.assertRaisesRegex(DomainValidationError, "时长"):
                    evaluate((segment(duration=duration),))

    def test_missing_window_duplicate_window_and_duplicate_segment_identity_fail(self):
        for segments, windows in (((segment(),), ()), ((), (window(), window())),
                                  ((segment(), segment(1, 2)), (window(),))):
            with self.subTest(segments=segments):
                with self.assertRaises(DomainValidationError):
                    evaluate(segments, windows)

    def test_segment_outside_window_is_not_clipped(self):
        for item in (segment(-1, 1), segment(364, 366)):
            with self.subTest(item=item):
                with self.assertRaisesRegex(DomainValidationError, "超出"):
                    evaluate((item,))

    def test_reversed_zero_and_aware_intervals_are_rejected(self):
        item = segment()
        for start, end in ((START, START), (START + timedelta(days=1), START),
                           (START.replace(tzinfo=timezone.utc), item.end),
                           (START.replace(tzinfo=timezone.utc), item.end.replace(tzinfo=timezone.utc))):
            with self.subTest(start=start, end=end):
                with self.assertRaises(DomainValidationError):
                    replace(item, start=start, end=end)
                with self.assertRaises(DomainValidationError):
                    FumeReportingWindow("source-A", "stack-1", start, end)

    def test_identity_is_not_borrowed_from_name_or_other_instance(self):
        with self.assertRaises(DomainValidationError):
            replace(segment(), source_instance_id="source-B")
        for field in ("source_instance_id", "metering_boundary_id", "segment_id"):
            with self.subTest(field=field):
                with self.assertRaises(DomainValidationError):
                    replace(segment(), **{field: " "})

    def test_wrong_profile_claim_and_non_policy_are_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "Profile"):
            evaluate((segment(),), policy=DecimalPolicy(precision=28))
        with self.assertRaises(DomainValidationError):
            evaluate((segment(),), policy=None)

    def test_legacy_duration_only_input_does_not_gain_interval_evidence(self):
        old = FumeIncinerationInput(q="1000", qvar="1000", hm="40", fch=".02", fox="1", duration="365")
        with self.assertRaises(DomainValidationError):
            evaluate((old,))



class FumeHourPrecisionTests(unittest.TestCase):
    def test_timestamp_lexical_precision_cannot_be_silently_discarded(self):
        for clock in ("00:00:00","00:00","00"):
            for separator in (".",","):
                text="2025-01-02 "+clock+separator+"0000001"
                with self.assertRaisesRegex(DomainValidationError,"不能自动截断"):
                    parse_fume_timestamp(text)
                self.assertEqual(parse_fume_timestamp("2025-01-02 "+clock+separator+"0000000"),datetime(2025,1,2))
        for text in ("2025-01-01 00:05:00","2025-01-01 00:00:01","2025-01-01 00:00:00.000001000"):
            value=parse_fume_timestamp(text)
            self.assertEqual(value,datetime.fromisoformat(text))
            with self.assertRaisesRegex(DomainValidationError,"只支持整小时"):
                evaluate((replace(segment(),start=value,end=value+timedelta(days=1)),))

    def test_integer_hours_and_declared_profile_days_are_identical(self):
        for precision, rounding in ((28, ROUND_HALF_EVEN), (40, ROUND_HALF_UP), (50, ROUND_DOWN)):
            policy=DecimalPolicy(precision=precision,rounding=rounding)
            for hours in (1,5,10,24,48):
                days=policy.divide(Decimal(hours),Decimal(24))
                items=[replace(segment(duration=InputValue(value,unit)),end=START+timedelta(hours=hours))
                       for value,unit in ((str(hours),"h"),(days,"d"))]
                expected=None
                for ambient in (6,17,60):
                    with localcontext() as ctx:
                        ctx.prec=ambient;ctx.rounding=ROUND_DOWN
                        results=[evaluate((item,),policy=policy,numeric_profile_id=f"explicit.{precision}.{rounding}") for item in items]
                    self.assertEqual(results[0].covered_amount_tco2,results[1].covered_amount_tco2)
                    self.assertEqual(results[0].coverage[0].segments[0].duration_days,days)
                    self.assertEqual(results[1].coverage[0].segments[0].segment.measurements.duration.value,days)
                    self.assertEqual(results[0].time_precision,"HOUR")
                    if expected is None:expected=results[0].covered_amount_tco2
                    self.assertEqual(results[0].covered_amount_tco2,expected)

    def test_non_hour_endpoints_remain_constructible_but_formal_evaluation_rejects(self):
        for delta in (timedelta(minutes=1),timedelta(minutes=5),timedelta(minutes=10),
                      timedelta(seconds=1),timedelta(microseconds=1)):
            item=replace(segment(duration=InputValue("1","h")),end=START+delta)
            self.assertEqual(item.end,START+delta)
            with self.assertRaisesRegex(DomainValidationError,"只支持整小时"):
                evaluate((item,))
            offset=replace(segment(),start=START+delta,end=START+timedelta(days=1)+delta)
            with self.assertRaisesRegex(DomainValidationError,"只支持整小时"):
                evaluate((offset,))

    def test_adjacent_hour_segments_have_no_false_gap_or_overlap(self):
        cursor=0;items=[]
        for index,hours in enumerate((1,5,10,8)):
            items.append(replace(segment(sid=f"h{index}",duration=InputValue(str(hours),"h")),
                start=START+timedelta(hours=cursor),end=START+timedelta(hours=cursor+hours)))
            cursor+=hours
        result=evaluate(items,(window(days=1),))
        self.assertTrue(result.complete)
        self.assertEqual(result.coverage[0].uncovered_intervals,())
        self.assertEqual(sum(item.duration_days for item in result.coverage[0].segments),Decimal(1))

    def test_wrong_finite_days_and_hour_values_still_fail_exactly(self):
        expected=POLICY.divide(1,24)
        with localcontext() as ctx:
            ctx.prec=80
            near=expected+Decimal("1e-60")
        for value,unit in ((near,"d"),("0.0416667","d"),("2","h"),("0","h"),("-1","h")):
            item=replace(segment(duration=InputValue(value,unit)),end=START+timedelta(hours=1))
            with self.assertRaises(DomainValidationError):evaluate((item,))


if __name__ == "__main__":
    unittest.main()
