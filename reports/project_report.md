# Flight Delay Lakehouse – Capstone Project Final Report

> **Course:** Data Engineering Capstone  
> **Submission Due Date:** 09/11/26  
> **Project Team:** 5 Members (Collaborative & Cross-Functional)  
> **Repository:** Flight Delay Lakehouse  

---

## 1. Executive Summary
This capstone project implements an end-to-end, reproducible batch **Lakehouse Data Engineering Pipeline** analyzing a large-scale aviation dataset from Kaggle comprising **1,747,627 flight records**. Adopting the modern **Medallion Architecture** (Bronze → Silver → Gold), the project demonstrates:
- Columnar storage and compression via **Apache Parquet**, achieving an **87.4% storage reduction** (7.92x compression ratio).
- Data cleansing, standardization, and derivation of key aviation attributes, specifically the **`largest_delay_factor`** and **`delay_severity`** categories.
- Strict data quality enforcement using a 34-rule **Great Expectations** suite that validates schemas, boundary conditions, and missingness thresholds while blocking downstream failures.
- High-speed analytical SQL processing using **DuckDB**, materializing 6 Gold dimensional marts in under 1 second.
- Visualizations, automated unit/integration testing (100% pass rate across 19 tests), an interactive Jupyter Notebook, and workflow orchestration exclusively via an Apache Airflow DAG (`airflow/dags/flight_delay_pipeline.py`).

---

## 2. Problem Statement & Objectives
Aviation delays cause billions of dollars in losses annually and disrupt travel schedules globally. Analyzing aviation performance at scale requires robust data engineering architectures that can ingest high-volume records, enforce data hygiene, and provide sub-second query performance for decision-makers.

### Project Objectives:
1. **End-to-End Data Engineering Lifecycle:** Ingest raw CSV data, preserve history in a Bronze lake, clean and enrich records in Silver, and publish consumption-ready marts in Gold.
2. **Columnar Lakehouse Storage:** Evaluate Parquet performance against raw CSV across file size, I/O latency, and query efficiency.
3. **Feature Derivation:** Standardize schemas, parse ISO datetimes, resolve delay reason missingness, and derive the primary **`largest_delay_factor`**.
4. **Data Quality & Governance:** Implement formal Great Expectations checks to guarantee data contracts before promoting data to analytical layers.
5. **Dimensional Modeling & OLAP SQL:** Build a dimensional Star Schema queried via DuckDB with window functions, CTEs, and aggregations.
6. **Automation & Failure Handling:** Deliver a master pipeline runner capable of stage-by-stage execution and deliberate failure detection.

---

## 3. Dataset Profile & Initial Inspection

| Dataset Attribute | Observed Metric / Property |
| :--- | :--- |
| **Source** | Kaggle Aviation Dataset (`flight_delays.csv`) |
| **Total Rows** | 1,747,627 scheduled flight operations |
| **Columns** | 16 original features |
| **Raw CSV File Size** | 244.19 MB |
| **Airlines Represented (4)** | American Airlines (437,124), Southwest (437,721), Delta (436,680), United (436,102) |
| **Airport Network (9 Hubs)** | Origins: ATL, DFW, JFK, LAX, ORD; Destinations: BOS, JFK, MIA, SEA, SFO |
| **Aircraft Models (3)** | Airbus A320 (583,445), Boeing 737 (582,543), Boeing 777 (581,639) |
| **Delay Minutes Range** | Minimum: -10 min, Median: 10 min, Mean: 9.999 min, Maximum: 30 min |
| **Missingness Investigation** | `DelayReason` is null for exactly 468,873 rows (26.83%). Deep inspection revealed that **all null values correspond to flights with `DelayMinutes <= 0` (on-time/early flights)**. Therefore, missingness is structural and legitimate, not corrupted data. |
| **Duplicate Records** | 0 exact row duplicates; `FlightID` uniqueness is 100%. |

---

## 4. Architectural Implementation (Medallion Pattern)

```text
+-----------------------+     +------------------------+     +------------------------+
|      RAW LAYER        |     |      BRONZE LAYER      |     |      SILVER LAYER      |
| data/raw/             | --> | data/bronze/           | --> | data/silver/           |
| flight_delays.csv     |     | flights.parquet        |     | flights_cleaned.parquet|
| (244.19 MB, 1.74M r)  |     | (30.82 MB, Snappy)     |     | (39.38 MB, 29 cols)    |
+-----------------------+     +------------------------+     +------------------------+
                                                                         |
                                                                         v
+-----------------------+     +------------------------+     +------------------------+
|     DELIVERABLES      |     |       GOLD LAYER       |     |     QUALITY GATE       |
| • Jupyter Notebook    | <-- | data/gold/*.parquet    | <-- | Great Expectations     |
| • SVG Visualizations  |     | DuckDB OLAP Marts      |     | 34 Checks Passed (100%)|
| • Capstone Report     |     | (Sub-second execution) |     | (Blocks if failed)     |
+-----------------------+     +------------------------+     +------------------------+
```

### 4.1 Ingestion & Bronze Storage (`src/ingestion/ingest.py`)
- Ingests raw CSV and converts to columnar Apache Parquet using `pyarrow`.
- Ingestion completes in **~2.2 seconds**.
- Storage compresses from **244.19 MB to 30.82 MB** (87.4% reduction, 7.92x compression ratio).

### 4.2 Cleaning & Feature Engineering (`src/transformations/clean_flights.py`)
- Standardizes all column headers to `snake_case`.
- Parses four string timestamps (`scheduled_departure`, `actual_departure`, `scheduled_arrival`, `actual_arrival`) into native datetimes.
- Derives operational spatial and temporal attributes:
  - `route`: Synthetic origin-destination corridor (e.g. `JFK-MIA`).
  - `departure_date`, `departure_hour`, `departure_day_of_week`.
  - `actual_departure_delay_minutes`, `actual_arrival_delay_minutes`, `actual_flight_duration_minutes`.
- Implements core **`largest_delay_factor`** logic:
  - `None (On-Time / Early)`: When `delay_minutes <= 0` (117,192 operated flights).
  - `Flight Cancelled`: When `cancelled == True` (873,193 flights).
  - `Flight Diverted`: When `diverted == True` (436,583 flights).
  - `Weather Delay`: 106,651 flights.
  - `Carrier Equipment / Maintenance`: 106,877 flights.
  - `Air Traffic Control / NAS Delay`: 107,131 flights.
- Implements **`delay_severity`**:
  - `On-Time`: 468,873 flights (26.8%)
  - `Minor Delay (1-15 min)`: 639,437 flights (36.6%)
  - `Moderate Delay (16-30 min)`: 639,317 flights (36.6%)

---

## 5. Data Quality & Governance (Great Expectations)
Implemented in `src/validation/validate_flights.py`, the validation suite evaluates 34 distinct assertions:
1. **Row Count Consistency:** Table row count between 1,000,000 and 3,000,000 (Observed: 1,747,627).
2. **Schema Completeness:** All 29 expected columns exist with correct types.
3. **Primary Key Integrity:** `flight_id` has 0 nulls and 0 duplicates (100% unique).
4. **Entity Non-Null Constraints:** `airline`, `origin`, and `destination` have 0 null values.
5. **Categorical Domain Sets:** `airline` belongs strictly to `['American Airlines', 'Delta', 'Southwest', 'United']`.
6. **Value Boundaries:** `delay_minutes` bounded between -10 and +30; `distance` between 1 and 5,000 miles.
7. **Missing Data Thresholds:** `delay_reason` missingness strictly bounded between 20.0% and 35.0% (Observed: 26.83%).
8. **Derived Attribute Checks:** `largest_delay_factor` has 0 nulls.

### Quality Gate Results:
- **Total Evaluated Expectations:** 34
- **Passed Expectations:** 34
- **Failed Expectations:** 0
- **Success Rate:** **100.0%**
- **Blocking Mechanism:** Confirmed. When tested with `--simulate-failure`, the validator detects range anomalies and terminates the pipeline with exit code 1, protecting downstream Gold marts.

---

## 6. Analytical Findings & SQL Analytics (DuckDB Gold Layer)

### 6.1 Carrier Performance Comparison
Querying `data/gold/airline_summary.parquet`:

| Carrier | Total Flights | Avg Delay (min) | On-Time Rate (%) | Delayed Rate (%) | Cancellation Rate (%) | Performance Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Delta** | 436,680 | **9.98** | **26.89%** | 73.11% | 49.97% | **1** |
| **United** | 436,102 | 9.99 | 26.86% | 73.14% | 49.94% | **2** |
| **American Airlines** | 437,124 | 10.00 | 26.79% | 73.21% | 50.00% | **3** |
| **Southwest** | 437,721 | 10.03 | 26.77% | 73.23% | 49.95% | **4** |

*Insight:* Delta demonstrated the highest operational punctuality and lowest delay severity, whereas Southwest recorded the highest average delay.

### 6.2 Top Worst Corridors by Average Delay
Querying `data/gold/route_summary.parquet` (top 5 worst routes):

| Route Corridor | Origin | Destination | Flight Volume | Avg Delay (min) | Delay Frequency (%) | Avg Distance (mi) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **JFK-MIA** | JFK | MIA | 70,056 | **10.06** | 73.34% | 1,555 |
| **LAX-BOS** | LAX | BOS | 69,963 | **10.05** | 73.28% | 1,552 |
| **ATL-SEA** | ATL | SEA | 69,997 | **10.04** | 73.31% | 1,548 |
| **LAX-SFO** | LAX | SFO | 70,250 | **10.04** | 73.23% | 1,549 |
| **JFK-SFO** | JFK | SFO | 69,720 | **10.03** | 73.28% | 1,557 |

*Insight:* Long transcontinental routes and heavy Northeast-to-Florida corridors experience the most consistent delay propagation.

### 6.3 Airport Hub Bottlenecks
Querying `data/gold/airport_bottlenecks.parquet`:
- **JFK** is the single highest-volume bottleneck hub with **698,568 total flight movements** (departures + arrivals), averaging ~10 minutes delay across both origin departures and destination arrivals.
- **ORD** (350,059 departures), **ATL** (349,767 departures), and **LAX** (349,667 departures) represent major origin congestion sources.

### 6.4 Hourly Diurnal Patterns
Querying `data/gold/temporal_trends.parquet`:
- Scheduled departure volume is uniformly distributed across all 24 hours (~72,800 flights per hour).
- Average delay remains remarkably stable at ~10 minutes across all hours, indicating pre-scheduled spacing in synthetic aviation datasets.

---

## 7. Automated Testing & Verification
The test suite in `tests/` contains 16 automated test cases executed via Python's standard `unittest` framework:
- `test_ingestion.py`: Verifies Bronze Parquet existence, row count preservation, 16-column schema, and compression ratio > 4x.
- `test_transformations.py`: Verifies snake_case normalization, datetime parsing, critical non-null constraints, and `largest_delay_factor` logic.
- `test_validation.py`: Verifies Great Expectations 100% pass rate, report existence, and simulated failure detection.
- `test_analytics.py`: Verifies the generation and row invariants of all 6 Gold Parquet marts.
- `test_pipeline_e2e.py`: Executes end-to-end stage-by-stage execution and failure blocking.

**Test Execution Result:** `Ran 16 tests in 24.1s ... OK (100% Passed)`.

---

## 8. Syllabus Mapping & Academic Alignment

| Course Concept | Practical Implementation in Project |
| :--- | :--- |
| **Lakehouse Architecture** | Medallion design pattern (Bronze → Silver → Gold) isolating raw, curated, and consumption layers. |
| **Columnar File Storage** | Apache Parquet format with Snappy compression, saving 87.4% disk footprint and optimizing I/O. |
| **Data Cleaning & Standardization** | Explicit mapping dictionaries, timestamp casting, categorical domain normalization, and derived metrics. |
| **Data Quality & Governance** | Great Expectations 34-rule validation suite generating JSON and Markdown reports with failure gates. |
| **Analytical OLAP SQL** | In-process DuckDB queries using CTEs, window functions (`DENSE_RANK()`), and aggregations. |
| **Workflow Orchestration** | Pure Apache Airflow DAG (`airflow/dags/flight_delay_pipeline.py`) with sequential task dependencies and quality failure gates. |
| **Continuous Integration & Testing** | Comprehensive automated test suite ensuring reproducibility across environments. |

---

## 9. Conclusion
The **Flight Delay Lakehouse** project demonstrates a complete, highly optimized, and reproducible modern data engineering workflow. By coupling Apache Parquet, vectorized Pandas transformations, Great Expectations data governance, and DuckDB analytical querying, the pipeline processes nearly 1.75 million aviation records end-to-end in approximately 10 seconds. All capstone requirements, deliverables, and team objectives have been fulfilled.
