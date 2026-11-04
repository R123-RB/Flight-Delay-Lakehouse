import argparse
import os
import sys
from datetime import datetime

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


# Default arguments for the Airflow DAG
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

# Define the Master Lakehouse Airflow DAG
with DAG(
    dag_id="flight_delay_lakehouse_pipeline",
    default_args=default_args,
    description="End-to-End Batch Aviation Flight Delay Lakehouse Pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["lakehouse", "aviation", "data_engineering"],
) as dag:

    # Task 1: Bronze Ingestion
    ingest_task = PythonOperator(
        task_id="ingest_bronze",
        python_callable=ingest_data,
    )

    # Task 2: Silver Cleaning & Transformation
    transform_task = PythonOperator(
        task_id="clean_transform_silver",
        python_callable=clean_data,
    )

    # Task 3: Great Expectations Quality Validation Gate
    validate_task = PythonOperator(
        task_id="great_expectations_validation",
        python_callable=validate,
    )

    # Task 4: DuckDB Gold Marts Creation
    gold_task = PythonOperator(
        task_id="build_gold_marts",
        python_callable=build_gold,
    )

    # Task 5: Visualizations & Reporting
    visualize_task = PythonOperator(
        task_id="generate_visualizations",
        python_callable=generate_all_visualizations,
    )

    # Define Airflow task dependencies
    ingest_task >> transform_task >> validate_task >> gold_task >> visualize_task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apache Airflow Flight Delay Lakehouse DAG Runner")
    parser.add_argument("--task", help="Execute a specific task_id only")
    parser.add_argument("--simulate-failure", action="store_true", help="Deliberately fail validation task")
    args = parser.parse_args()

    if args.simulate_failure:
        # Override validation task callable to simulate data quality failure
        validate_task.python_callable = lambda: validate(simulate_failure=True)

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
