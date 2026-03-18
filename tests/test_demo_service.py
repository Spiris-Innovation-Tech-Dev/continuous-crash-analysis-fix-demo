from __future__ import annotations

import unittest

from src.demo_service import build_account_overview, build_invoice_preview


class DemoServiceTests(unittest.TestCase):
    def test_build_account_overview_happy_path(self) -> None:
        overview = build_account_overview({"name": "  ada lovelace  "})
        self.assertEqual(overview["display_name"], "Ada Lovelace")

    def test_build_invoice_preview_happy_path(self) -> None:
        preview = build_invoice_preview(100, 20)
        self.assertAlmostEqual(preview["discount_ratio"], 0.2)


if __name__ == "__main__":
    unittest.main()
