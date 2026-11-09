# Flight Delay Lakehouse – Team Handbook & Implementation Guide

> **Capstone Project:** Medallion Lakehouse Aviation Data Engineering Pipeline  
> **Architecture:** Python + Parquet + DuckDB + Airflow (local/batch)  
> **Team Size:** 5 Members (collaborative)

---

## 1. Project Goal
Build a compact, robust, and reproducible data engineering pipeline for BTS/Kaggle aviation delay data (~5.82M records in the current implementation) demonstrating the lakehouse lifecycle:

- Raw CSV ingestion into **Bronze** Parquet
- Cleaning/standardization/feature engineering into **Silver** Parquet
- **Data quality validation** (Great Expectations framework integration when installed, plus retained custom checks) as a blocking gate
- **DuckDB** analytical **Gold** marts
- **Airflow** orchestration, automated tests, CI checks, and clear documentation

---

## 2. Team Work Breakdown (aligned to implementation)

| Member | Focus Area | Core Responsibilities (implemented) | Primary Artifacts |
| :---: | :--- | :--- | :--- |
| **Member 1** | **Ingestion & Storage** | Raw CSV profiling; source-preserving Bronze Parquet ingestion; compression/row/column checks. | `src/ingestion/ingest.py`, `notebooks/inspect_data.py`, `tests/test_ingestion.py` |
| **Member 2** | **Cleaning & Transformation** | `snake_case` schema, HHMM→datetime parsing, missingness handling, derived fields (`route`, `departure_date/hour/day`), operational aliases, `flight_status`, `largest_delay_factor`, `delay_severity`, cause flags, `flight_id`. | `src/transformations/clean_flights.py`, `tests/test_transformations.py` |
| **Member 3** | **Data Validation & Governance** | GX framework integration (when available) + retained custom GE-style checks; JSON/Markdown reports; blocking gate and failure-path support (`--simulate-failure`). | `src/validation/validate_flights.py`, `reports/validation_*`, `tests/test_validation.py` |
| **Member 4** | **Analytics (DuckDB/SQL)** | Canonical Gold marts over Silver via DuckDB; analytical SQL suite. Current canonical marts: `airline_summary`, `route_summary`, `delay_factor_summary`, `airport_bottlenecks`, `temporal_trends`, `aircraft_summary`. | `src/analytics/build_gold.py`, `sql/flight_analysis.sql`, `tests/test_analytics.py` |
| **Member 5** | **Orchestration, Reporting & CI/Docs** | Airflow DAG task flow/dependencies, logging, `retry_delay`, failure notification hook, downstream blocking; SVG reporting; tests/CI workflow; architecture/model/dictionary/README alignment. | `airflow/dags/flight_delay_pipeline.py`, `src/reporting/visualize.py`, `tests/test_pipeline_e2e.py`, `.github/workflows/ci.yml`, `docs/*`, `README.md` |

---

## 3. Execution Principles (capstone quality)
1. **Data contracts first:** keep Bronze/Silver/Gold schemas and docs aligned with actual implementation.
2. **Quality as a gate:** validation failures must stop downstream Gold/report generation.
3. **Observable orchestration:** Airflow tasks should log context, handle failures, and make dependency blocking explicit.
4. **Testability:** maintain automated tests for stage logic and failure paths; keep CI simple and failing on errors.
5. **Reproducibility:** prefer deterministic transforms and clear run commands; avoid unnecessary frameworks.
6. **Documentation accuracy:** distinguish implemented/canonical outputs from proposed/legacy artifacts.

---

## 4. Validation & Orchestration Notes (current implementation)
- **Validation task (Airflow):** `data_quality_validation` runs `validate()` from `src/validation/validate_flights.py`.
- **GX integration:** uses Great Expectations when installed and records GX metadata in reports; custom checks are retained.
- **Failure handling:** DAG default args include retry settings and `on_failure_callback`; optional `PIPELINE_ALERT_WEBHOOK` enables webhook notification.
- **Downstream blocking:** sequential dependencies prevent Gold/report tasks after upstream failures.
- **Failure simulation:** `python airflow/dags/flight_delay_pipeline.py --simulate-failure` and `python src/validation/validate_flights.py --simulate-failure`.

---

## 5. Syllabus Alignment (implemented)
| Syllabus Concept | Implementation |
| :--- | :--- |
| **Data Engineering Lifecycle** | Raw CSV → Bronze → Silver → Validation Gate → Gold marts → Reports/visualizations |
| **Lakehouse / Medallion** | Layered `data/` storage and clear stage responsibilities |
| **Columnar Storage** | Parquet (Snappy) for Bronze/Silver/Gold |
| **Data Quality & Governance** | GX framework integration + retained custom checks, reports, blocking gate |
| **OLAP Analytics** | DuckDB SQL marts and analytical query suite |
| **Orchestration** | Apache Airflow DAG with task dependencies, logging, retry delay, failure notification, failure blocking |
| **Testing & CI/CD** | Unittest suite (including failure-path coverage where applicable) and GitHub Actions workflow that installs deps and fails on test/command errors |
