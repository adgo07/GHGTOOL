"""Fuel draft isolation; expectations are independent of executable policies."""
import json
import unittest

from packages.ui.carbon_material_fuel import FuelParameterDrafts


class FuelParameterDraftTests(unittest.TestCase):
    def setUp(self):
        self.drafts = FuelParameterDrafts()

    def test_identity_path_basis_field_and_source_are_all_isolated(self):
        contexts = (
            ("catalog:diesel", "MASS", "HEAT_CONTENT", "lhv", "MEASURED"),
            ("catalog:diesel", "VOLUME", "HEAT_CONTENT", "lhv", "MEASURED"),
            ("custom:柴油混合", "MASS", "HEAT_CONTENT", "lhv", "MEASURED"),
            ("catalog:diesel", "MASS", "DIRECT", "lhv", "MEASURED"),
            ("catalog:diesel", "MASS", "HEAT_CONTENT", "carbon", "MEASURED"),
            ("catalog:diesel", "MASS", "HEAT_CONTENT", "lhv", "CALCULATED"),
        )
        for index, context in enumerate(contexts):
            self.drafts.save(*context, f"{index}.123456789012345678901234567890")
        for index, context in enumerate(contexts):
            self.assertEqual(self.drafts.load(*context), f"{index}.123456789012345678901234567890")

    def test_empty_invalid_and_absent_values_are_not_normalized(self):
        key = ("custom:未完成燃料", "MASS", "DIRECT", "direct_carbon", "MEASURED")
        self.assertIsNone(self.drafts.load(*key))
        for text in ("", "1.", "-", "NaN", "原始非法文本"):
            self.drafts.save(*key, text)
            self.assertEqual(self.drafts.load(*key), text)

    def test_json_round_trip_preserves_inactive_and_legacy_sources(self):
        entries = (
            ("catalog:gas", "VOLUME", "HEAT_CONTENT", "carbon", "CALCULATED", "0.015300001"),
            ("catalog:gas", "VOLUME", "HEAT_CONTENT", "carbon", "MEASURED", "0.016"),
            ("custom:gas", "VOLUME", "DIRECT", "direct_carbon", "PROJECT_SPECIFIED", "0.7"),
        )
        for entry in entries:
            self.drafts.save(*entry)
        restored = FuelParameterDrafts()
        restored.restore(json.loads(json.dumps(self.drafts.export())))
        self.assertEqual(restored.export(), self.drafts.export())
        for entry in entries:
            self.assertEqual(restored.load(*entry[:-1]), entry[-1])

    def test_old_pairs_require_explicit_saved_context(self):
        old = [{"field": "lhv", "source": "MEASURED", "value": "42.001"}]
        self.drafts.restore(old)
        self.assertEqual(self.drafts.export(), [])
        context = ("catalog:diesel", "MASS", "HEAT_CONTENT")
        self.drafts.restore(old, legacy_context=context)
        self.assertEqual(self.drafts.load(*context, "lhv", "MEASURED"), "42.001")
        self.assertIsNone(self.drafts.load("catalog:gas", "VOLUME", "HEAT_CONTENT", "lhv", "MEASURED"))

    def test_partially_scoped_drafts_cannot_be_rebound_to_current_context(self):
        self.drafts.restore([
            {"identity": "catalog:gas", "field": "lhv", "source": "MEASURED", "value": "400"},
            {"identity": "catalog:gas", "path": "VOLUME", "basis": "HEAT_CONTENT", "field": "lhv", "source": "MEASURED", "value": "399"},
            {"identity": "catalog:gas", "path": "VOLUME", "basis": "HEAT_CONTENT", "field": "lhv", "source": "MEASURED", "value": 123},
        ], legacy_context=("catalog:diesel", "MASS", "HEAT_CONTENT"))
        self.assertEqual(len(self.drafts.export()), 1)
        self.assertEqual(self.drafts.load("catalog:gas", "VOLUME", "HEAT_CONTENT", "lhv", "MEASURED"), "399")

    def test_unconfirmed_context_is_rejected(self):
        for identity, path, basis in (("", "MASS", "DIRECT"), ("custom:x", "", "DIRECT"), ("custom:x", "MASS", "")):
            with self.assertRaises(ValueError):
                self.drafts.save(identity, path, basis, "carbon", "MEASURED", "0.1")
