import os
import sys
from datetime import datetime

# Add project base directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

from src.ingestion.ingest import ingest_data
from src.transformations.clean_flights import clean_data
from src.validation.validate_flights import validate
from src.analytics.build_gold import build_gold
from src.reporting.visualize import generate_all_visualizations

if AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="flight_delay_lakehouse_pipeline",
        start_date=datetime(2024, 1, 1),
        schedule_interval="@daily",
        catchup=False,
        tags=["lakehouse", "aviation", "data_engineering"],
    ) as dag:
        t1 = PythonOperator(task_id="ingest_bronze", python_callable=ingest_data)
        t2 = PythonOperator(task_id="clean_transform_silver", python_callable=clean_data)
        t3 = PythonOperator(task_id="great_expectations_validation", python_callable=validate)
        t4 = PythonOperator(task_id="build_gold_marts", python_callable=build_gold)
        t5 = PythonOperator(task_id="generate_visualizations", python_callable=generate_all_visualizations)

        t1 >> t2 >> t3 >> t4 >> t5
