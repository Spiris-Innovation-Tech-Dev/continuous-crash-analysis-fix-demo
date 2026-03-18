from __future__ import annotations

import unittest

from src.demo_service import (
    build_account_overview,
    build_invoice_preview,
    calculate_discount_ratio,
    load_customer_profile,
)


class DemoServiceTests(unittest.TestCase):
    def test_build_account_overview_happy_path(self) -> None:
        overview = build_account_overview({"name": "  ada lovelace  "})
        self.assertEqual(overview["display_name"], "Ada Lovelace")

    def test_build_invoice_preview_happy_path(self) -> None:
        preview = build_invoice_preview(100, 20)
        self.assertAlmostEqual(preview["discount_ratio"], 0.2)

    # --- guard: divide-by-zero in calculate_discount_ratio ---

    def test_calculate_discount_ratio_zero_total_raises(self) -> None:
        """Reproduces EXCEPTION_INT_DIVIDE_BY_ZERO (fingerprint baeca31860df)."""
        with self.assertRaises(ValueError):
            calculate_discount_ratio(0, 10)

    def test_build_invoice_preview_zero_total_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_invoice_preview(0, 10)

    # --- guard: missing / None name in load_customer_profile ---

    def test_load_customer_profile_none_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_customer_profile({"name": None})

    def test_load_customer_profile_missing_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_customer_profile({})


if __name__ == "__main__":
    unittest.main()
