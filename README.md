# Flight Delay Lakehouse 🛫

> **Capstone Project:** Data Engineering Lakehouse Pipeline  
> **Submission Due Date:** 09/11/26  
> **Architecture:** Modern Medallion Lakehouse (Bronze → Silver → Gold)  
> **Dataset:** Kaggle Large-Scale Aviation Delay Records (1,747,627 rows × 16 columns)

---

## 1. Project Overview & Motivation
The **Flight Delay Lakehouse** project builds a compact, realistic, and reproducible data engineering pipeline reflecting modern lakehouse architectures using publicly available aviation delay data from Kaggle.

The core goal is to demonstrate how large-scale aviation data is:
1. **Ingested** from raw CSV into columnar Parquet (**Bronze Layer**).
2. **Cleaned & Standardized** with snake_case naming, parsed timestamps, handled nulls, and derived features including the primary **`largest_delay_factor`** (**Silver Layer**).
3. **Validated** using a formal **Great Expectations** quality gate (34 expectations covering schema, ranges, uniqueness, and missingness thresholds).
4. **Queried & Materialized** into analytical data marts using **DuckDB** and OLAP SQL (**Gold Layer**).
5. **Surfaced** into actionable business insights, vector visualizations, an interactive Jupyter Notebook, and comprehensive reporting.

---

## 2. Lakehouse Architecture (Medallion Pattern)

```mermaid
flowchart TD
    subgraph S1 ["1. Raw Data Source"]
        raw["Kaggle Aviation Dataset<br/>flight_delays.csv<br/>(1.74M rows • 244.19 MB)"]
    end

    subgraph S2 ["2. Bronze Layer (Columnar Storage)"]
        ingest["Python Ingestion Engine<br/>src/ingestion/ingest.py"]
        bronze[("Bronze Parquet<br/>flights.parquet<br/>(30.82 MB • 7.92x compression)")]
        raw --> ingest --> bronze
    end

    subgraph S3 ["3. Silver Layer (Cleaned & Curated)"]
        clean["Vectorized Transformations<br/>src/transformations/clean_flights.py<br/>• Standardize snake_case<br/>• Parse datetime timestamps<br/>• Derive largest_delay_factor<br/>• Categorize delay severity<br/>• Compute flight durations"]
        silver[("Silver Parquet<br/>flights_cleaned.parquet<br/>(39.38 MB • 29 columns)")]
        bronze --> clean --> silver
    end

    subgraph S4 ["4. Data Quality Gate"]
        val["Great Expectations Suite<br/>src/validation/validate_flights.py<br/>34 Assertions (100% Passed)"]
        silver --> val
    end

    subgraph S5 ["5. Gold Layer (Analytics Marts)"]
        duck["DuckDB OLAP Engine<br/>src/analytics/build_gold.py"]
        val -->|Quality Gate Passed| duck
        g1[("airline_summary.parquet")]
        g2[("route_summary.parquet")]
        g3[("delay_factor_summary.parquet")]
        g4[("airport_bottlenecks.parquet")]
        g5[("temporal_trends.parquet")]
        g6[("aircraft_summary.parquet")]
        duck --> g1 & g2 & g3 & g4 & g5 & g6
    end

    subgraph S6 ["6. Delivery & Insights"]
        viz["Vector Visualizations<br/>reports/figures/*.svg"]
        nb["Jupyter Notebook<br/>notebooks/*.ipynb"]
        rep["Capstone Report<br/>reports/project_report.md"]
        g1 & g2 & g3 & g4 & g5 & g6 --> viz & nb & rep
    end
```

---

## 3. Key Summary

- **Source:** Publicly available Kaggle Flight Delays Dataset (`flight_delays.csv`).
- **Data Scale:** 1,747,627 flight records across 4 major carriers (American Airlines, Delta, Southwest, United) and 9 airport hubs.
- **Storage:** Apache Parquet with Snappy compression (**87.4% storage savings**, 244.19 MB CSV → 30.82 MB Parquet).
- **Cleaning & Feature Logic:**
  - Standardized column schema into `snake_case`.
  - Parsed all four timestamps to standard ISO datetimes.
  - Investigated missing `delay_reason`: structurally missing because it corresponds to on-time/early flights (`delay_minutes <= 0`).
  - Derived **`largest_delay_factor`**: identifies whether the primary cause was Weather, Carrier Maintenance, Air Traffic Control / Security, or None (On-Time).
  - Derived **`delay_severity`**, corridor **`route`**, and operational **`flight_status`**.
- **Data Quality:** Comprehensive Great Expectations validation suite verifying 34 business rules, range boundaries (-10 to 30 min delay), non-null primary keys, and missingness thresholds.
- **Analytics Engine:** **DuckDB** in-process columnar SQL engine querying Silver Parquet and generating 6 Gold analytical marts in sub-second times.
- **Deliverables:** Reproducible code repository, test suite, Great Expectations JSON/Markdown reports, vector SVG charts, Jupyter Notebook, and final report.

---

## 4. Team Work Allocation (5 Members)

| Member | Focus Area | Core Responsibilities |
| :---: | :--- | :--- |
| **Member 1** | **Data Ingestion & Storage** | Dataset profiling, Bronze Parquet conversion (`src/ingestion/ingest.py`), and storage/read benchmarking. |
| **Member 2** | **Data Cleaning & Transformation** | Schema standardization, timestamp parsing, `delay_reason` handling, and `largest_delay_factor` engineering (`src/transformations/clean_flights.py`). |
| **Member 3** | **Data Validation (Great Expectations)** | 34-rule validation suite (`src/validation/validate_flights.py`), failure blocking gate, and report generation (`reports/validation_report.md`). |
| **Member 4** | **Querying & Analysis (DuckDB + SQL)** | Dimensional Gold Marts (`src/analytics/build_gold.py`) and analytical SQL query suite (`sql/flight_analysis.sql`). |
| **Member 5** | **Reporting, Visualisation & Orchestration** | Master pipeline runner (`pipeline.py`), SVG visualizations (`src/reporting/visualize.py`), Airflow DAG, Jupyter Notebook, and documentation. |

---

## 5. Repository Structure

```text
Flight Delay Lakehouse/
├── airflow/
│   └── dags/
│       └── flight_delay_pipeline.py      # Apache Airflow DAG orchestrator
├── data/
│   ├── raw/                              # Original source CSV (1.74M rows)
│   ├── bronze/                           # Source-preserving Parquet (flights.parquet)
│   ├── silver/                           # Curated Silver Parquet (flights_cleaned.parquet)
│   └── gold/                             # Analytical Parquet marts
│       ├── airline_summary.parquet
│       ├── route_summary.parquet
│       ├── delay_factor_summary.parquet
│       ├── airport_bottlenecks.parquet
│       ├── temporal_trends.parquet
│       └── aircraft_summary.parquet
├── docs/
│   ├── architecture.md                   # Medallion Lakehouse architectural documentation
│   ├── data_model.md                     # Dimensional Star Schema & Entity-Relationship Model
│   ├── data_dictionary.md                # Detailed dictionary for Bronze, Silver, Gold layers
│   └── team_handbook.md                  # 5-member breakdown, 21-day plan & syllabus alignment
├── notebooks/
│   ├── inspect_data.py                   # Initial dataset profiling script
│   └── flight_delay_lakehouse_analysis.ipynb # Interactive Jupyter analytical notebook
├── reports/
│   ├── figures/                          # Generated vector SVG charts
│   │   ├── carrier_delay_comparison.svg
│   │   ├── worst_delay_routes.svg
│   │   ├── hourly_delay_trend.svg
│   │   ├── delay_factor_distribution.svg
│   │   └── airport_bottlenecks.svg
│   ├── validation_report.md              # Great Expectations human-readable report
│   ├── validation_results.json           # Great Expectations machine-readable results
│   └── project_report.md                 # Formal Capstone Final Project Report
├── sql/
│   └── flight_analysis.sql               # 10 comprehensive analytical SQL queries (DuckDB)
├── src/
│   ├── ingestion/
│   │   └── ingest.py                     # CSV to Bronze Parquet converter
│   ├── transformations/
│   │   └── clean_flights.py              # Silver cleaning & feature engineering
│   ├── validation/
│   │   └── validate_flights.py           # Great Expectations quality gate
│   ├── analytics/
│   │   └── build_gold.py                 # DuckDB Gold Marts builder
│   └── reporting/
│       └── visualize.py                  # Standalone SVG chart visualizer
├── tests/
│   ├── test_ingestion.py                 # Unit tests for Bronze ingestion
│   ├── test_transformations.py           # Unit tests for Silver transformations
│   ├── test_validation.py                # Unit tests for Great Expectations & failure gate
│   ├── test_analytics.py                 # Unit tests for Gold layer marts
│   └── test_pipeline_e2e.py              # End-to-end integration and failure tests
├── pipeline.py                           # Master pipeline CLI orchestrator
├── requirements.txt                      # Project dependency specification
└── README.md                             # Project documentation
```

---

## 6. Getting Started & Execution Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Packages: `duckdb`, `pandas`, `pyarrow`, `numpy`

### Quickstart: Run the Complete End-to-End Pipeline
To run all stages (Ingest → Clean → Validate → Gold Marts → Visualizations):
```bash
python pipeline.py
```
*The full end-to-end pipeline processes all 1.74 million records and produces all outputs in ~10 seconds!*

### Running Individual Stages via CLI
```bash
# 1. Ingestion only (CSV -> Bronze Parquet)
python pipeline.py --ingest

# 2. Cleaning & Transformation only (Bronze -> Silver Parquet)
python pipeline.py --clean

# 3. Data Quality Validation (Great Expectations)
python pipeline.py --validate

# 4. Gold Layer Analytics (DuckDB Marts)
python pipeline.py --gold

# 5. Generate Visualizations only
python pipeline.py --visualize

# 6. Test Data Quality Failure Handling (deliberately trips validation gate)
python pipeline.py --validate --simulate-failure
```

### Running Automated Test Suite
To execute all 16 automated unit and integration tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 7. Key Analytics & Findings

### 1. Carrier Reliability
- **Delta** leads overall operational performance with the lowest average delay (**9.98 min**) and highest on-time rate (**26.89%**).
- **Southwest** recorded the highest average delay (**10.03 min**).
- Across all four carriers, on-time rate consistently hovers at ~26.8%, reflecting uniform operating schedules.

### 2. Root Cause of Flight Delays (`largest_delay_factor`)
- Early or on-time flights (`delay_minutes <= 0`) account for all 468,873 rows with missing `delay_reason`.
- For delayed flights (`delay_minutes > 0`), delays are equally distributed across three primary factors:
  - **Weather:** 426,098 flights (avg delay: 15.49 min)
  - **Carrier Maintenance:** 426,168 flights (avg delay: 15.50 min)
  - **Air Traffic Control / Security:** 426,488 flights (avg delay: 15.50 min)

### 3. Flight Corridors & Airport Bottlenecks
- The top corridors by average delay are **JFK-MIA**, **LAX-BOS**, and **ATL-SEA**.
- **JFK** is the largest dual-role congestion hub with over 698,000 total operations (departures + arrivals), followed by **ORD**, **ATL**, and **LAX**.

---

## 8. Syllabus Mapping
This project demonstrates complete mastery over the core competencies in the Data Engineering curriculum:
- **Lakehouse Architecture & Medallion Pattern:** Segregation of concerns into Bronze, Silver, and Gold layers.
- **Columnar Storage & Serialization:** PyArrow Parquet implementation achieving 87.4% compression ratio.
- **Data Quality & Governance:** Automated 34-rule Great Expectations validation gate blocking downstream errors.
- **High-Performance OLAP SQL:** In-process DuckDB queries with window functions, CTEs, and aggregation marts.
- **Pipeline Orchestration:** Standalone multi-stage Python CLI orchestrator with failure handling and Apache Airflow DAG.
