"""Percent conversion must retain the entered decimal independently of context."""
import unittest
from decimal import localcontext
from packages.ui.field_specs import get_field_spec, ui_to_domain_value, domain_to_ui_value

class PercentagePrecisionTests(unittest.TestCase):
    def test_percentage_decimal_shift_retains_full_input_under_small_context(self):
        value = "98.12345678901234567890123456789012345678"
        ratio = "0.9812345678901234567890123456789012345678"
        for field in ("fuel_oxidation", "fgd.i", "fgd.tr"):
            for precision in (6, 28, 40, 80):
                with self.subTest(field=field, precision=precision), localcontext() as context:
                    context.prec = precision
                    spec = get_field_spec(field)
                    self.assertEqual(ui_to_domain_value(spec, value), ratio)
                    self.assertEqual(domain_to_ui_value(spec, ratio), value)

    def test_nonfinite_percentages_are_rejected(self):
        for text in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=text), self.assertRaises(ValueError):
                ui_to_domain_value(get_field_spec("fgd.i"), text)
