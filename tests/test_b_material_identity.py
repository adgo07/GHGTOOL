"""Prevent ambiguous material evidence without changing approved formulas."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from packages.core.decimal_policy import DecimalPolicy
from packages.standards.carbon_material_normalization import (
    MaterialInputLine,
    MaterialRole,
    normalize_material_inputs,
)


DUPLICATE_CODE = "CAR-VAL-MATERIAL-LINE-ID-DUPLICATE"


def material_rows():
    return (
        MaterialInputLine("feed", MaterialRole.CALCINATION_FEED, "同名物料",
                          "100", "90", volatile_matter_percent="10"),
        MaterialInputLine("cc", MaterialRole.CALCINED_PRODUCT, "同名物料",
                          "20", "80", volatile_matter_percent="5"),
        MaterialInputLine("ucc", MaterialRole.UNDERBURN_RECOVERED,
                          "同名物料", "30", "40"),
        MaterialInputLine("du", MaterialRole.CARBON_DUST,
                          "同名物料", "10", "25"),
    )


class MaterialIdentityTests(unittest.TestCase):
    def normalize(self, rows):
        return normalize_material_inputs("calcination", rows, policy=DecimalPolicy())

    def test_duplicate_same_role_is_rejected_without_renaming_or_losing_input(self):
        rows = material_rows()
        duplicate = replace(rows[2], name="另一物料", mass_t="10",
                            fixed_carbon_percent="80")
        supplied = (*rows, duplicate)
        result = self.normalize(supplied)
        self.assertIn(DUPLICATE_CODE, {issue.code for issue in result.problems})
        self.assertEqual(result.included_lines, supplied)
        self.assertEqual(duplicate.line_id, "ucc")
        self.assertEqual(sum(row.line_id == "ucc" for row in result.normalized_lines), 1)

    def test_duplicate_across_roles_is_also_ambiguous_for_frozen_line_keys(self):
        rows = material_rows()
        supplied = (*rows[:3], replace(rows[3], line_id="ucc"))
        result = self.normalize(supplied)
        self.assertIn(DUPLICATE_CODE, {issue.code for issue in result.problems})
        self.assertEqual(result.included_lines, supplied)

    def test_same_ids_in_separate_instances_remain_valid_and_independent(self):
        first = self.normalize(material_rows())
        other_rows = list(material_rows())
        other_rows[2] = replace(other_rows[2], fixed_carbon_percent="80")
        second = self.normalize(tuple(other_rows))
        self.assertFalse(first.problems)
        self.assertFalse(second.problems)
        self.assertEqual(first.value("output_carbon_total"), Decimal("30.5"))
        self.assertEqual(second.value("output_carbon_total"), Decimal("42.5"))
        self.assertEqual(self.normalize(material_rows()), first)

    def test_same_name_and_role_with_distinct_ids_are_not_deduplicated(self):
        rows = material_rows()
        result = self.normalize((*rows, replace(rows[2], line_id="ucc-second",
                                               mass_t="10", fixed_carbon_percent="80")))
        self.assertFalse(result.problems)
        self.assertEqual(result.value("output_carbon_ucc"), Decimal("20"))

    def test_inactive_empty_placeholder_does_not_reserve_a_line_identity(self):
        rows = material_rows()
        blank = MaterialInputLine("ucc", MaterialRole.UNDERBURN_RECOVERED, "", None)
        result = self.normalize((blank, *rows, blank))
        self.assertFalse(result.problems)
        self.assertEqual(result.included_lines, rows)
        self.assertEqual(result.value("output_carbon_total"), Decimal("30.5"))


class MaterialIdentityFormalTests(unittest.TestCase):
    def test_canonical_duplicate_rejected_no_record_and_saved_evidence_unchanged(self):
        # Real application/SQLite test; a selected-module probe must not claim
        # this test ran unless these full production dependencies are available.
        from tests.test_g06_carbon_material import _input, _measured_parameter
        from packages.application.carbon_accounting import CarbonAccountingUseCase
        from packages.application.canonical_input_codec import (
            decode_canonical_input, encode_canonical_input,
        )
        from packages.persistence import SQLiteRecordRepository
        from packages.standards.carbon_material import CarbonMaterialCalculator, CalcinationInput

        rows = material_rows()
        good = _input(calcination=CalcinationInput(
            material_rows=rows,
            k1=_measured_parameter("CAR-PAR-K1", ".35", "ratio"),
        ))
        with tempfile.TemporaryDirectory(prefix="ghg-material-identity-") as temporary:
            path = Path(temporary) / "records.sqlite"
            records = SQLiteRecordRepository(path)
            usecase = CarbonAccountingUseCase(CarbonMaterialCalculator(), records)
            accepted = usecase.calculate(good)
            self.assertTrue(accepted.successful, accepted.problems)
            record_id = accepted.record.record_id
            original_record = records.get(record_id)
            original_input = records.get_raw_input_snapshot(record_id)
            original_trace = records.get_trace_snapshot(record_id)
            bad_rows = (*rows, replace(rows[2], mass_t="10", fixed_carbon_percent="80"))
            bad_process = replace(good.calcination, material_rows=bad_rows)
            for version in ("MATERIAL_V1", "MATERIAL_V2"):
                with self.subTest(version=version):
                    bad = replace(good, calcination=bad_process,
                                  calcinations=(bad_process,), material_execution_version=version)
                    encoded = encode_canonical_input(bad)
                    restored = decode_canonical_input(encoded)
                    rejected = usecase.calculate(restored)
                    self.assertFalse(rejected.successful)
                    self.assertIn(DUPLICATE_CODE, {issue.code for issue in rejected.problems})
                    self.assertEqual(encode_canonical_input(restored), encoded)
                    self.assertEqual(len(records.list_all()), 1)
            reopened = SQLiteRecordRepository(path)
            self.assertEqual(reopened.get(record_id), original_record)
            self.assertEqual(reopened.get_raw_input_snapshot(record_id), original_input)
            self.assertEqual(reopened.get_trace_snapshot(record_id), original_trace)


if __name__ == "__main__":
    unittest.main()
