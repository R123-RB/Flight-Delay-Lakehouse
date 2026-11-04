import os
import unittest
import pandas as pd

from src.analytics.build_gold import get_default_paths


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        _, self.gold_dir = get_default_paths()
        self.assertTrue(os.path.exists(self.gold_dir), f"Gold dir missing: {self.gold_dir}")

    def test_all_gold_marts_exist(self):
        expected_marts = [
            "airline_summary.parquet",
            "route_summary.parquet",
            "delay_factor_summary.parquet",
            "airport_bottlenecks.parquet",
            "temporal_trends.parquet",
            "aircraft_summary.parquet",
        ]
        for mart in expected_marts:
            path = os.path.join(self.gold_dir, mart)
            self.assertTrue(os.path.exists(path), f"Missing gold mart: {mart}")
            df = pd.read_parquet(path)
            self.assertGreater(len(df), 0, f"Gold mart {mart} is empty")

    def test_airline_summary_invariants(self):
        df = pd.read_parquet(os.path.join(self.gold_dir, "airline_summary.parquet"))
        self.assertEqual(len(df), 4, "Expected 4 airlines in airline summary")

        # Invariant: on_time_flights + delayed_flights == total_flights
        for _, row in df.iterrows():
            total = row["total_flights"]
            on_time = row["on_time_flights"]
            delayed = row["delayed_flights"]
            self.assertEqual(total, on_time + delayed, f"Airline {row['airline']} total does not balance")

    def test_route_summary_records(self):
        df = pd.read_parquet(os.path.join(self.gold_dir, "route_summary.parquet"))
        self.assertEqual(len(df), 25, "Expected 25 origin-destination route pairs")
        self.assertTrue((df["avg_delay_minutes"] >= -10).all())
        self.assertTrue((df["avg_delay_minutes"] <= 30).all())


if __name__ == "__main__":
    unittest.main()
