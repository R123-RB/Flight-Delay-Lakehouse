import os
import unittest
import pandas as pd

from src.ingestion.ingest import get_default_paths, ingest_data


class TestIngestion(unittest.TestCase):

    def setUp(self):
        self.raw_path, self.bronze_path = get_default_paths()

    def test_raw_file_exists(self):
        self.assertTrue(os.path.exists(self.raw_path), f"Raw file missing: {self.raw_path}")

    def test_bronze_file_created(self):
        self.assertTrue(os.path.exists(self.bronze_path), f"Bronze file missing: {self.bronze_path}")

    def test_bronze_schema_and_rows(self):
        df_bronze = pd.read_parquet(self.bronze_path)
        self.assertGreater(len(df_bronze), 1_000_000, "Bronze row count too small")
        self.assertEqual(len(df_bronze.columns), 16, "Expected 16 columns in Bronze layer")

        expected_cols = [
            "FlightID", "Airline", "FlightNumber", "Origin", "Destination",
            "ScheduledDeparture", "ActualDeparture", "ScheduledArrival", "ActualArrival",
            "DelayMinutes", "DelayReason", "Cancelled", "Diverted",
            "AircraftType", "TailNumber", "Distance"
        ]
        for col in expected_cols:
            self.assertIn(col, df_bronze.columns, f"Expected column {col} missing in Bronze")

    def test_compression_ratio(self):
        csv_size = os.path.getsize(self.raw_path)
        pq_size = os.path.getsize(self.bronze_path)
        ratio = csv_size / pq_size
        self.assertGreater(ratio, 4.0, f"Expected compression ratio > 4x, got {ratio:.2f}x")


if __name__ == "__main__":
    unittest.main()
