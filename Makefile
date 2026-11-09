.PHONY: test lint format clean run-pipeline help

help:
	@echo "Available targets:"
	@echo "  test        - Run test suite"
	@echo "  lint        - Run flake8 linting"
	@echo "  format      - Run black formatting"
	@echo "  clean       - Remove generated artifacts"
	@echo "  run-pipeline - Execute Airflow DAG"

test:
	python -m unittest discover -s tests -p "test_*.py" -v

lint:
	flake8 src/ tests/ notebooks/inspect_data.py

format:
	black src/ tests/ notebooks/inspect_data.py

clean:
	rm -rf data/gold/*.parquet reports/validation_results.json reports/validation_report.md

run-pipeline:
	python airflow/dags/flight_delay_pipeline.py
