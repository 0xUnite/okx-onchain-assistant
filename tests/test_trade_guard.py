import unittest

from okx_skills.trade_guard import plan_order_slices, pre_trade_check, route_insight


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
        self.assertIn("sandwich_risk", result["checks"])

    def test_plan_order_slices(self):
        amount = 50.0
        result = plan_order_slices("ETH", "USDC", amount, "ethereum")
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["recommended_slices"], 1)
        total = sum(item["from_amount"] for item in result["schedule"])
        self.assertAlmostEqual(total, amount, places=6)

    def test_route_insight_shape(self):
        result = route_insight("ETH", "USDC", "ethereum")
        self.assertIn("quality", result)
        self.assertIn("routes", result)


if __name__ == "__main__":
    unittest.main()
