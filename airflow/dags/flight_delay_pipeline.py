import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

# Set project base directory into python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.ingest import ingest_data
from src.transformations.clean_flights import clean_data
from src.validation.validate_flights import validate
from src.analytics.build_gold import build_gold
from src.reporting.visualize import generate_all_visualizations

logger = logging.getLogger(__name__)


def _log_task_context(stage: str, **context):
    ti = context.get("ti")
    logger.info("[%s] task_id=%s dag_id=%s run_id=%s try=%s logical_date=%s",
                stage,
                getattr(ti, "task_id", None),
                getattr(ti, "dag_id", None),
                context.get("run_id"),
                getattr(ti, "try_number", None),
                context.get("logical_date") or context.get("execution_date"))
    print(f"[Airflow][{stage}] task={getattr(ti, 'task_id', 'unknown')} run_id={context.get('run_id')} try={getattr(ti, 'try_number', 'n/a')}")


def notify_failure(context):
    """Failure notification hook (logs + optional webhook)."""
    ti = context.get("ti")
    exc = context.get("exception")
    msg = (
        f"PIPELINE FAILURE: dag={getattr(ti, 'dag_id', None)} task={getattr(ti, 'task_id', None)} "
        f"run_id={context.get('run_id')} try={getattr(ti, 'try_number', None)} error={exc}"
    )
    logger.error(msg)
    print(msg)
    webhook = os.environ.get("PIPELINE_ALERT_WEBHOOK")
    if webhook:
        try:
            import json
            from urllib.request import Request, urlopen
            payload = json.dumps({"text": msg}).encode("utf-8")
            req = Request(webhook, data=payload, headers={"Content-Type": "application/json"})
            urlopen(req, timeout=10)
            print(f"[Airflow] Failure notification sent to PIPELINE_ALERT_WEBHOOK")
        except Exception as notify_exc:
            print(f"[Airflow] Failure notification webhook failed: {notify_exc}")
    else:
        print("[Airflow] No PIPELINE_ALERT_WEBHOOK set; failure recorded in task logs.")


def _run_stage(stage_name: str, fn, *args, **kwargs):
    def _callable(**context):
        _log_task_context(f"START:{stage_name}", **context)
        try:
            result = fn(*args, **kwargs)
            _log_task_context(f"SUCCESS:{stage_name}", **context)
            print(f"[Airflow][SUCCESS:{stage_name}] completed")
            return result
        except Exception:
            logger.exception("[%s] stage failed", stage_name)
            print(f"[Airflow][ERROR:{stage_name}] stage failed; downstream tasks will be blocked.")
            raise
    return _callable


# Default arguments for the Airflow DAG
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": False,
    "on_failure_callback": notify_failure,
}

# Define the Master Lakehouse Airflow DAG
with DAG(
    dag_id="flight_delay_lakehouse_pipeline",
    default_args=default_args,
    description="End-to-End Batch Aviation Flight Delay Lakehouse Pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",          # Airflow 2.4+ preferred (replaces deprecated schedule_interval)
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "aviation", "data_engineering"],
) as dag:

    # Task 1: Bronze Ingestion
    ingest_task = PythonOperator(
        task_id="ingest_bronze",
        python_callable=_run_stage("bronze_ingestion", ingest_data),
    )

    # Task 2: Silver Cleaning & Transformation
    transform_task = PythonOperator(
        task_id="clean_transform_silver",
        python_callable=_run_stage("silver_transform", clean_data),
    )

    # Task 3: Data Quality Validation Gate (Great Expectations framework when available + custom checks)
    validate_task = PythonOperator(
        task_id="data_quality_validation",
        python_callable=_run_stage("data_quality_validation", validate),
    )

    # Task 4: DuckDB Gold Marts Creation
    gold_task = PythonOperator(
        task_id="build_gold_marts",
        python_callable=_run_stage("gold_build", build_gold),
    )

    # Task 5: Visualizations & Reporting
    visualize_task = PythonOperator(
        task_id="generate_visualizations",
        python_callable=_run_stage("visualization", generate_all_visualizations),
    )

    # Strict sequential dependencies: downstream tasks do not run if an upstream task fails.
    ingest_task >> transform_task >> validate_task >> gold_task >> visualize_task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apache Airflow Flight Delay Lakehouse DAG Runner")
    parser.add_argument("--task", help="Execute a specific task_id only")
    parser.add_argument("--simulate-failure", action="store_true", help="Deliberately fail validation task")
    args = parser.parse_args()

    if args.simulate_failure:
        # Override validation task callable to simulate data quality failure
        validate_task.python_callable = _run_stage("data_quality_validation", validate, simulate_failure=True)

    if args.task:
        task = dag.get_task(args.task)
        if not task:
            print(f"[Airflow Error] Task '{args.task}' not found in DAG '{dag.dag_id}'.")
            print(f"Available tasks: {[t.task_id for t in dag.tasks]}")
            sys.exit(1)
        print(f"[Airflow] Running single task: '{args.task}'")
        task.execute({})
    else:
        # Airflow 2.5+ standard test runner
        dag.test()
