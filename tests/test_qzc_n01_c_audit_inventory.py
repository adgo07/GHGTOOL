from __future__ import annotations

import unittest

from scripts.qzc_n01_c_audit import build_inventory


class N01CAuditInventoryTests(unittest.TestCase):
    def test_repository_tolerance_inventory_is_executed_and_business_is_close_is_absent(self) -> None:
        inventory = build_inventory()
        self.assertTrue(inventory)
        business_is_close = [
            item
            for item in inventory
            if item["marker"] == "is_close"
            and str(item["path"]).startswith("packages/")
            and not (
                item["path"] == "packages/core/decimal_policy.py"
                and str(item["text"]).startswith("def is_close")
            )
        ]
        self.assertEqual(business_is_close, [])

        categories = {str(item["category"]) for item in inventory}
        self.assertIn("test_assertion", categories)
        self.assertIn("lookup/interpolation", categories)


if __name__ == "__main__":
    unittest.main()
