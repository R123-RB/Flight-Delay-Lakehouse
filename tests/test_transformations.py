import os
import unittest
import pandas as pd

from src.transformations.clean_flights import get_default_paths


class TestTransformations(unittest.TestCase):

    def setUp(self):
        _, self.silver_path = get_default_paths()
        self.assertTrue(os.path.exists(self.silver_path), f"Silver file missing: {self.silver_path}")
        self.df = pd.read_parquet(self.silver_path)

    def test_snake_case_columns(self):
        expected_cols = [
            "flight_id", "airline", "flight_number", "origin", "destination",
            "scheduled_departure", "actual_departure", "scheduled_arrival", "actual_arrival",
            "delay_minutes", "delay_reason", "cancelled", "diverted", "aircraft_type",
            "tail_number", "distance", "route", "departure_date", "departure_hour",
            "departure_day_of_week", "flight_status", "largest_delay_factor", "delay_severity"
        ]
        for col in expected_cols:
            self.assertIn(col, self.df.columns, f"Missing expected Silver column: {col}")

    def test_timestamp_parsing(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["scheduled_departure"]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["actual_departure"]))

    def test_largest_delay_factor_logic(self):
        # 1. Delay <= 0 and not cancelled/diverted should be None (On-Time / Early)
        on_time_mask = (self.df["delay_minutes"] <= 0) & (~self.df["cancelled"]) & (~self.df["diverted"])
        if on_time_mask.sum() > 0:
            sample_factors = self.df.loc[on_time_mask, "largest_delay_factor"].unique()
            self.assertIn("None (On-Time / Early)", sample_factors)

        # 2. Cancelled flights should be marked Flight Cancelled
        cancelled_mask = self.df["cancelled"] == True
        sample_cancelled = self.df.loc[cancelled_mask, "largest_delay_factor"].unique()
        self.assertIn("Flight Cancelled", sample_cancelled)

        # 3. Weather delay flights should have Weather Delay
        weather_mask = (self.df["delay_reason"] == "Weather") & (~self.df["cancelled"]) & (~self.df["diverted"])
        if weather_mask.sum() > 0:
            sample_weather = self.df.loc[weather_mask, "largest_delay_factor"].unique()
            self.assertIn("Weather Delay", sample_weather)

    def test_no_nulls_in_critical_fields(self):
        self.assertEqual(self.df["flight_id"].isna().sum(), 0, "flight_id has null values")
        self.assertEqual(self.df["airline"].isna().sum(), 0, "airline has null values")
        self.assertEqual(self.df["origin"].isna().sum(), 0, "origin has null values")
        self.assertEqual(self.df["destination"].isna().sum(), 0, "destination has null values")
        self.assertEqual(self.df["largest_delay_factor"].isna().sum(), 0, "largest_delay_factor has null values")


if __name__ == "__main__":
    unittest.main()

