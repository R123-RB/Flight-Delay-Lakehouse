import os
import unittest
import pandas as pd

from src.analytics.build_gold import get_default_paths


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        silver_path, self.gold_dir = get_default_paths()
        if not os.path.exists(self.gold_dir) or not os.path.exists(os.path.join(self.gold_dir, "airline_summary.parquet")):
            fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_flights.csv")
            if os.path.exists(fixture):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                bronze_path = os.path.join(base_dir, "data", "bronze", "flights.parquet")
                from src.ingestion.ingest import ingest_data
                from src.transformations.clean_flights import clean_data
                from src.analytics.build_gold import build_gold
                ingest_data(raw_path=fixture, bronze_path=bronze_path)
                clean_data(bronze_path=bronze_path, silver_path=silver_path)
                build_gold(silver_path=silver_path, gold_dir=self.gold_dir)
        self.assertTrue(os.path.exists(self.gold_dir), f"Gold dir missing: {self.gold_dir}")

    def test_all_canonical_gold_marts_exist(self):
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
        self.assertGreaterEqual(len(df), 10, "Expected at least 10 airlines in airline summary")
        expected_cols = {"airline", "total_flights", "avg_delay_minutes", "on_time_flights", "delayed_flights", "cancelled_flights"}
        self.assertTrue(expected_cols.issubset(set(df.columns)), f"Missing columns in airline_summary: {expected_cols - set(df.columns)}")
        for _, row in df.iterrows():
            total = row["total_flights"]
            on_time = row["on_time_flights"]
            delayed = row["delayed_flights"]
            self.assertLessEqual(on_time + delayed, total,
                                 f"Airline {row['airline']} delay split exceeds total")

    def test_route_summary_records(self):
        df = pd.read_parquet(os.path.join(self.gold_dir, "route_summary.parquet"))
        self.assertEqual(len(df), 25, "Expected 25 origin-destination route pairs")
        self.assertTrue((df["avg_delay_minutes"] >= -100).all())
        self.assertTrue((df["avg_delay_minutes"] <= 600).all())
        self.assertTrue(df["route"].str.contains("-", na=False).all())

    def test_delay_factor_and_temporal_coverage(self):
        factors = pd.read_parquet(os.path.join(self.gold_dir, "delay_factor_summary.parquet"))
        self.assertIn("largest_delay_factor", factors.columns)
        self.assertGreaterEqual(len(factors), 5)
        temporal = pd.read_parquet(os.path.join(self.gold_dir, "temporal_trends.parquet"))
        self.assertEqual(len(temporal), 24)
        self.assertEqual(sorted(temporal["departure_hour"].astype(int).tolist()), list(range(24)))


if __name__ == "__main__":
    unittest.main()
