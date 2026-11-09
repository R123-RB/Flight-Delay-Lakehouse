import json
import os
import unittest
import pandas as pd

from src.validation.validate_flights import (
    GreatExpectationsValidator,
    get_default_paths,
    run_great_expectations_suite,
    validate,
)


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.silver_path, self.json_path, self.md_path = get_default_paths()
        if not os.path.exists(self.silver_path):
            fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_flights.csv")
            if os.path.exists(fixture):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                bronze_path = os.path.join(base_dir, "data", "bronze", "flights.parquet")
                from src.ingestion.ingest import ingest_data
                from src.transformations.clean_flights import clean_data
                ingest_data(raw_path=fixture, bronze_path=bronze_path)
                clean_data(bronze_path=bronze_path, silver_path=self.silver_path)
        self.assertTrue(os.path.exists(self.silver_path), f"Silver file missing: {self.silver_path}")
        self.df = pd.read_parquet(self.silver_path)

    def test_validation_suite_passes_on_silver(self):
        summary = run_great_expectations_suite(self.df, simulate_failure=False)
        self.assertTrue(summary["success"], "Expected validation checks to pass")
        self.assertEqual(summary["statistics"]["unsuccessful_expectations"], 0)
        self.assertGreaterEqual(summary["statistics"]["success_percent"], 100.0)

    def test_great_expectations_metadata_present(self):
        summary = run_great_expectations_suite(self.df, simulate_failure=False)
        self.assertIn("evaluation_engine", summary)
        self.assertIn("great_expectations", summary)
        gx = summary["great_expectations"]
        self.assertIn("available", gx)
        # If GX is installed, we should see native checks; if not, fallback must be explicit.
        if gx.get("available"):
            self.assertGreater(gx.get("native_checks", 0), 0)
        else:
            self.assertIn("error", gx)

    def test_validation_reports_exist(self):
        self.assertTrue(os.path.exists(self.json_path), "JSON validation report missing")
        self.assertTrue(os.path.exists(self.md_path), "Markdown validation report missing")
        with open(self.json_path) as f:
            data = json.load(f)
        self.assertIn("results", data)
        self.assertIn("statistics", data)

    def test_deliberate_failure_detected(self):
        summary = run_great_expectations_suite(self.df, simulate_failure=True)
        self.assertFalse(summary["success"], "Expected validation failure when simulated")
        self.assertGreater(summary["statistics"]["unsuccessful_expectations"], 0)

    def test_validate_cli_behavior_blocks_on_failure(self):
        # validate() exits with code 1 on failure; run in subprocess to avoid killing test runner.
        import subprocess, sys
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cmd = [sys.executable, "src/validation/validate_flights.py", "--silver", self.silver_path, "--simulate-failure"]
        # CLI writes full reports; run in temp cwd behavior not needed, but ensure it exits 1
        res = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True, timeout=1800)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("DATA VALIDATION FAILED", (res.stdout + res.stderr))


if __name__ == "__main__":
    unittest.main()
