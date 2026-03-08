import unittest

from okx_skills.onchainos_api import OnchainOSClient


class OnchainApiTest(unittest.TestCase):
    def setUp(self):
        self.client = OnchainOSClient()

    def test_price_shape(self):
        result = self.client.get_price("ETH", "ethereum")
        self.assertIn("price", result)
        self.assertIn("source", result)
        self.assertGreater(result["price"], 0)

    def test_swap_quote_shape(self):
        result = self.client.get_swap_quote("ETH", "USDC", 1, "ethereum")
        self.assertIn("to_amount", result)
        self.assertIn("price_impact", result)
        self.assertIn("source", result)

    def test_route_snapshot_shape(self):
        result = self.client.get_route_snapshot("ETH", "USDC", "ethereum")
        self.assertIn("routes", result)
        self.assertIn("source", result)


if __name__ == "__main__":
    unittest.main()
