import json
import os
import unittest
import pandas as pd

from src.validation.validate_flights import (
    GreatExpectationsValidator,
    get_default_paths,
    run_great_expectations_suite,
)


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.silver_path, self.json_path, self.md_path = get_default_paths()
        self.assertTrue(os.path.exists(self.silver_path), f"Silver file missing: {self.silver_path}")
        self.df = pd.read_parquet(self.silver_path)

    def test_validation_suite_passes_on_silver(self):
        summary = run_great_expectations_suite(self.df, simulate_failure=False)
        self.assertTrue(summary["success"], "Expected all validation checks to pass")
        self.assertEqual(summary["statistics"]["unsuccessful_expectations"], 0)
        self.assertEqual(summary["statistics"]["success_percent"], 100.0)

    def test_validation_reports_exist(self):
        self.assertTrue(os.path.exists(self.json_path), "JSON validation report missing")
        self.assertTrue(os.path.exists(self.md_path), "Markdown validation report missing")

        with open(self.json_path) as f:
            data = json.load(f)
            self.assertIn("evaluation_engine", data)
            self.assertIn("results", data)

    def test_deliberate_failure_detected(self):
        summary = run_great_expectations_suite(self.df, simulate_failure=True)
        self.assertFalse(summary["success"], "Expected validation failure when simulated")
        self.assertGreater(summary["statistics"]["unsuccessful_expectations"], 0)


if __name__ == "__main__":
    unittest.main()
