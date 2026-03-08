import unittest

from okx_skills.trade_guard import (
    build_private_tx_strategy,
    plan_order_slices,
    pre_trade_check,
    revoke_high_risk_approvals,
    route_insight,
    simulate_trade,
)


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

    def test_private_strategy_shape(self):
        result = build_private_tx_strategy("ethereum", 5000, 0.8)
        self.assertIn("mode", result)
        self.assertIn("template", result)
        self.assertIn("providers", result)

    def test_simulate_trade_shape(self):
        result = simulate_trade("ETH", "USDC", 1, "ethereum", "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        self.assertIn("status", result)
        self.assertIn("executable", result)
        self.assertIn("tx_template", result)

    def test_revoke_flow_dry_run(self):
        result = revoke_high_risk_approvals("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "ethereum", execute=False)
        self.assertEqual(result["status"], "dry_run")
        self.assertIn("candidates", result)


if __name__ == "__main__":
    unittest.main()
