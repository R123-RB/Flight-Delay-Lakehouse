import importlib.util
import os
import subprocess
import sys
import unittest

# Airflow is an optional dependency — skip tests gracefully if not installed
try:
    from airflow import DAG  # noqa: F401 — import verified here only
    _AIRFLOW_AVAILABLE = True
except ImportError:
    _AIRFLOW_AVAILABLE = False


def load_dag_module(dag_path):
    spec = importlib.util.spec_from_file_location("flight_delay_pipeline", dag_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(_AIRFLOW_AVAILABLE, "apache-airflow not installed — skipping Airflow DAG tests")
class TestAirflowPipelineE2E(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.python_bin = sys.executable
        self.dag_file = os.path.join(self.base_dir, "airflow", "dags", "flight_delay_pipeline.py")
        self.dag_module = load_dag_module(self.dag_file)
        self.dag = self.dag_module.dag

    def test_airflow_dag_structure(self):
        self.assertIsNotNone(self.dag, "Airflow DAG failed to load")
        self.assertEqual(self.dag.dag_id, "flight_delay_lakehouse_pipeline")
        self.assertEqual(len(self.dag.tasks), 5, "Expected 5 tasks in the Airflow DAG")

        expected_task_ids = [
            "ingest_bronze",
            "clean_transform_silver",
            "great_expectations_validation",
            "build_gold_marts",
            "generate_visualizations",
        ]
        for tid in expected_task_ids:
            self.assertIn(tid, self.dag.task_dict, f"Missing task: {tid}")

    def test_airflow_dependencies(self):
        t1 = self.dag.get_task("ingest_bronze")
        t2 = self.dag.get_task("clean_transform_silver")
        t3 = self.dag.get_task("great_expectations_validation")
        t4 = self.dag.get_task("build_gold_marts")
        t5 = self.dag.get_task("generate_visualizations")

        self.assertIn(t2, t1.downstream_list)
        self.assertIn(t3, t2.downstream_list)
        self.assertIn(t4, t3.downstream_list)
        self.assertIn(t5, t4.downstream_list)

    def test_airflow_task_execution(self):
        # Execute individual task via Airflow
        res = subprocess.run(
            [self.python_bin, self.dag_file, "--task", "ingest_bronze"],
            cwd=self.base_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Airflow task execution failed: {res.stderr}")
        self.assertIn("STEP 1: BRONZE LAYER", res.stdout)

    def test_airflow_dag_e2e_run(self):
        # Execute complete Airflow DAG run
        res = subprocess.run(
            [self.python_bin, self.dag_file],
            cwd=self.base_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Airflow DAG run failed: {res.stderr}")
        self.assertIn("Starting DAG Run: 'flight_delay_lakehouse_pipeline'", res.stdout)
        self.assertIn("COMPLETED SUCCESSFULLY", res.stdout)

    def test_airflow_validation_failure_blocking(self):
        # Execute Airflow DAG with simulated data quality failure
        res = subprocess.run(
            [self.python_bin, self.dag_file, "--simulate-failure"],
            cwd=self.base_dir,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0, "Airflow DAG should fail when data quality check fails")
        self.assertIn("DATA VALIDATION FAILED", res.stdout)


if __name__ == "__main__":
    unittest.main()
