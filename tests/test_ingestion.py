import os
import unittest
import pandas as pd

from src.ingestion.ingest import get_default_paths, ingest_data


class TestIngestion(unittest.TestCase):

    def setUp(self):
        self.raw_path, self.bronze_path = get_default_paths()
        # Support CI hermetic fixtures when gitignored raw files are absent
        if not os.path.exists(self.raw_path):
            fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_flights.csv")
            if os.path.exists(fixture):
                os.makedirs(os.path.dirname(self.raw_path), exist_ok=True)
                import shutil
                shutil.copy(fixture, self.raw_path)

    def test_raw_file_exists(self):
        self.assertTrue(os.path.exists(self.raw_path), f"Raw file missing: {self.raw_path}")

    def test_bronze_file_created(self):
        self.assertTrue(os.path.exists(self.bronze_path), f"Bronze file missing: {self.bronze_path}")

    def test_bronze_schema_and_rows(self):
        df_bronze = pd.read_parquet(self.bronze_path)
        self.assertGreater(len(df_bronze), 1, "Bronze row count too small")
        self.assertEqual(len(df_bronze.columns), 31, "Expected 31 columns in Bronze layer")

        expected_cols = [
            "YEAR", "MONTH", "DAY", "DAY_OF_WEEK", "AIRLINE", "FLIGHT_NUMBER",
            "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
            "SCHEDULED_DEPARTURE", "DEPARTURE_TIME", "DEPARTURE_DELAY", "TAXI_OUT",
            "WHEELS_OFF", "SCHEDULED_TIME", "ELAPSED_TIME", "AIR_TIME", "DISTANCE",
            "WHEELS_ON", "TAXI_IN", "SCHEDULED_ARRIVAL", "ARRIVAL_TIME",
            "ARRIVAL_DELAY", "DIVERTED", "CANCELLED", "CANCELLATION_REASON",
            "AIR_SYSTEM_DELAY", "SECURITY_DELAY", "AIRLINE_DELAY",
            "LATE_AIRCRAFT_DELAY", "WEATHER_DELAY",
        ]
        for col in expected_cols:
            self.assertIn(col, df_bronze.columns, f"Expected column {col} missing in Bronze")

    def test_compression_ratio(self):
        csv_size = os.path.getsize(self.raw_path)
        pq_size = os.path.getsize(self.bronze_path)
        ratio = csv_size / pq_size if pq_size > 0 else 0
        # small fixtures may not compress as well as full dataset
        min_ratio = 1.0 if csv_size < 5 * 1024 * 1024 else 4.0
        self.assertGreater(ratio, min_ratio, f"Expected compression ratio > {min_ratio}x, got {ratio:.2f}x")


if __name__ == "__main__":
    unittest.main()

