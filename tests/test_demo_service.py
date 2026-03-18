from __future__ import annotations

import unittest

from src.demo_service import (
    build_account_overview,
    build_invoice_preview,
    load_customer_profile,
    calculate_discount_ratio,
    save_invoice,
)


class DemoServiceTests(unittest.TestCase):
    def test_build_account_overview_happy_path(self) -> None:
        overview = build_account_overview({"name": "  ada lovelace  "})
        self.assertEqual(overview["display_name"], "Ada Lovelace")

    def test_build_invoice_preview_happy_path(self) -> None:
        preview = build_invoice_preview(100, 20)
        self.assertAlmostEqual(preview["discount_ratio"], 0.2)

    # --- load_customer_profile edge cases ---

    def test_load_customer_profile_none_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_customer_profile({"name": None})

    def test_load_customer_profile_missing_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_customer_profile({})

    # --- calculate_discount_ratio edge cases ---

    def test_calculate_discount_ratio_zero_total_raises(self) -> None:
        with self.assertRaises(ValueError):
            calculate_discount_ratio(0, 10)

    # --- save_invoice ---

    def test_save_invoice_valid_does_not_raise(self) -> None:
        save_invoice({"customer_id": "c1", "total": 100, "line_items": []})

    def test_save_invoice_missing_fields_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            save_invoice({"customer_id": "c1"})

    def test_save_invoice_empty_dict_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            save_invoice({})


if __name__ == "__main__":
    unittest.main()
