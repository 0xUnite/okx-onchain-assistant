import unittest

from okx_skills.trade_guard import plan_order_slices, pre_trade_check


class TradeGuardTest(unittest.TestCase):
    def test_pre_trade_check_structure(self):
        result = pre_trade_check(
            from_token="ETH",
            to_token="USDC",
            amount=1,
            chain="ethereum",
            wallet_address="0x123",
        )
        self.assertIn(result["decision"], {"PASS", "WARN", "BLOCK"})
        self.assertIn("risk_score", result)
        self.assertIn("checks", result)
        self.assertIn("quote", result["checks"])

    def test_plan_order_slices(self):
        amount = 50.0
        result = plan_order_slices("ETH", "USDC", amount, "ethereum")
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["recommended_slices"], 1)
        total = sum(item["from_amount"] for item in result["schedule"])
        self.assertAlmostEqual(total, amount, places=6)


if __name__ == "__main__":
    unittest.main()
