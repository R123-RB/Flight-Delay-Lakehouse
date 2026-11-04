import os
import unittest
import subprocess
import sys


class TestPipelineE2E(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.python_bin = sys.executable

    def test_pipeline_dry_run_individual_stages(self):
        # Ingestion
        res = subprocess.run([self.python_bin, "pipeline.py", "--ingest"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Ingest step failed: {res.stderr}")
        self.assertIn("STEP 1: BRONZE LAYER", res.stdout)

        # Clean
        res = subprocess.run([self.python_bin, "pipeline.py", "--clean"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Clean step failed: {res.stderr}")
        self.assertIn("STEP 2: SILVER LAYER", res.stdout)

        # Validate
        res = subprocess.run([self.python_bin, "pipeline.py", "--validate"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Validate step failed: {res.stderr}")
        self.assertIn("STEP 3: DATA VALIDATION", res.stdout)

        # Gold
        res = subprocess.run([self.python_bin, "pipeline.py", "--gold"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Gold step failed: {res.stderr}")
        self.assertIn("STEP 4: GOLD LAYER", res.stdout)

        # Visualizations
        res = subprocess.run([self.python_bin, "pipeline.py", "--visualize"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Visualize step failed: {res.stderr}")
        self.assertIn("STEP 5: VISUALIZATION", res.stdout)

    def test_pipeline_failure_blocking(self):
        res = subprocess.run([self.python_bin, "pipeline.py", "--validate", "--simulate-failure"], cwd=self.base_dir, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0, "Pipeline should exit non-zero on validation failure")
        self.assertIn("DATA VALIDATION FAILED", res.stdout)


if __name__ == "__main__":
    unittest.main()
