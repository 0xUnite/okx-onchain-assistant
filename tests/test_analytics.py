import unittest

from okx_skills.analytics import OnchainAnalytics


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.analytics = OnchainAnalytics()

    def test_holder_distribution_non_negative(self):
        result = self.analytics.get_holder_analysis("PEPE", "ethereum")
        dist = result["distribution"]
        self.assertGreaterEqual(dist["rest"], 0)
        self.assertGreaterEqual(dist["top50"], dist["top10"])
        self.assertLessEqual(dist["top50"], 100)

    def test_track_address_has_favorite_dex(self):
        result = self.analytics.track_address("0x123", "ethereum")
        self.assertIn("favorite_dex", result)
        self.assertIsInstance(result["favorite_dex"], str)
        self.assertTrue(result["favorite_dex"])


if __name__ == "__main__":
    unittest.main()
