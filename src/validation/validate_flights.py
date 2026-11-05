import argparse
import json
import os
import sys
import time
from datetime import datetime
import pandas as pd


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    silver_path = os.path.join(base_dir, "data", "silver", "flights_cleaned.parquet")
    report_json_path = os.path.join(base_dir, "reports", "validation_results.json")
    report_md_path = os.path.join(base_dir, "reports", "validation_report.md")
    return silver_path, report_json_path, report_md_path


class GreatExpectationsValidator:
    """
    Custom Validation Engine modeled on the Great Expectations specification.
    Implements the same expectation method names, kwargs structure, and
    JSON result schema as the Great Expectations library, allowing a
    drop-in upgrade to the real library in future. Reports are fully
    GE-compatible (suite_name, run_id, evaluated_expectations, etc.).
    """

    def __init__(self, df: pd.DataFrame, suite_name: str = "flight_silver_suite"):
        self.df = df
        self.suite_name = suite_name
        self.results = []
        self.start_time = time.time()

    def expect_table_row_count_to_be_between(self, min_value: int, max_value: int = None):
        row_count = len(self.df)
        success = row_count >= min_value and (max_value is None or row_count <= max_value)
        self.results.append({
            "expectation_type": "expect_table_row_count_to_be_between",
            "kwargs": {"min_value": min_value, "max_value": max_value},
            "success": bool(success),
            "result": {
                "observed_value": row_count,
                "element_count": row_count,
            },
        })

    def expect_column_to_exist(self, column: str):
        exists = column in self.df.columns
        self.results.append({
            "expectation_type": "expect_column_to_exist",
            "kwargs": {"column": column},
            "success": bool(exists),
            "result": {"observed_value": exists},
        })

    def expect_column_values_to_not_be_null(self, column: str, max_unexpected_percent: float = 0.0):
        total = len(self.df)
        null_count = int(self.df[column].isna().sum())
        null_percent = (null_count / total) * 100.0 if total > 0 else 0.0
        success = null_percent <= max_unexpected_percent
        self.results.append({
            "expectation_type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": column, "max_unexpected_percent": max_unexpected_percent},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unexpected_count": null_count,
                "unexpected_percent": round(null_percent, 4),
            },
        })

    def expect_column_values_to_be_unique(self, column: str):
        total = len(self.df)
        unique_count = self.df[column].nunique(dropna=False)
        duplicate_count = total - unique_count
        success = duplicate_count == 0
        self.results.append({
            "expectation_type": "expect_column_values_to_be_unique",
            "kwargs": {"column": column},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unique_count": unique_count,
                "unexpected_count": duplicate_count,
            },
        })

    def expect_column_values_to_be_between(self, column: str, min_value: float = None, max_value: float = None):
        series = self.df[column].dropna()
        total = len(series)
        cond = pd.Series(True, index=series.index)
        if min_value is not None:
            cond = cond & (series >= min_value)
        if max_value is not None:
            cond = cond & (series <= max_value)
        unexpected_count = int((~cond).sum())
        unexpected_percent = (unexpected_count / total) * 100.0 if total > 0 else 0.0
        success = unexpected_count == 0
        self.results.append({
            "expectation_type": "expect_column_values_to_be_between",
            "kwargs": {"column": column, "min_value": min_value, "max_value": max_value},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unexpected_count": unexpected_count,
                "unexpected_percent": round(unexpected_percent, 4),
                "min_observed": float(series.min()) if total > 0 else None,
                "max_observed": float(series.max()) if total > 0 else None,
            },
        })

    def expect_column_values_to_be_in_set(self, column: str, value_set: list):
        series = self.df[column].dropna()
        total = len(series)
        unexpected = series[~series.isin(value_set)]
        unexpected_count = len(unexpected)
        unexpected_percent = (unexpected_count / total) * 100.0 if total > 0 else 0.0
        success = unexpected_count == 0
        self.results.append({
            "expectation_type": "expect_column_values_to_be_in_set",
            "kwargs": {"column": column, "value_set": value_set},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unexpected_count": unexpected_count,
                "unexpected_percent": round(unexpected_percent, 4),
                "unexpected_examples": unexpected.unique().tolist()[:5],
            },
        })

    def expect_column_missingness_to_be_between(self, column: str, min_percent: float, max_percent: float):
        total = len(self.df)
        null_count = int(self.df[column].isna().sum())
        null_percent = (null_count / total) * 100.0 if total > 0 else 0.0
        success = min_percent <= null_percent <= max_percent
        self.results.append({
            "expectation_type": "expect_column_missingness_to_be_between",
            "kwargs": {"column": column, "min_percent": min_percent, "max_percent": max_percent},
            "success": bool(success),
            "result": {
                "element_count": total,
                "null_count": null_count,
                "observed_null_percent": round(null_percent, 4),
            },
        })

    def get_validation_summary(self):
        total_eval = len(self.results)
        successful_eval = sum(1 for r in self.results if r["success"])
        unsuccessful_eval = total_eval - successful_eval
        success_percent = (successful_eval / total_eval) * 100.0 if total_eval > 0 else 0.0
        overall_success = unsuccessful_eval == 0

        summary = {
            "evaluation_engine": "Custom Validation Engine (Great Expectations-compatible) v1.0",
            "expectation_suite_name": self.suite_name,
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "success": overall_success,
            "statistics": {
                "evaluated_expectations": total_eval,
                "successful_expectations": successful_eval,
                "unsuccessful_expectations": unsuccessful_eval,
                "success_percent": round(success_percent, 2),
                "duration_seconds": round(time.time() - self.start_time, 3),
            },
            "results": self.results,
        }
        return summary


def run_great_expectations_suite(df: pd.DataFrame, simulate_failure: bool = False):
    """
    Executes the comprehensive Great Expectations suite.
    """
    validator = GreatExpectationsValidator(df, suite_name="flight_silver_suite")

    # 1. Volume & Schema Expectations
    validator.expect_table_row_count_to_be_between(min_value=1_000_000, max_value=3_000_000)

    required_columns = [
        "flight_id", "airline", "flight_number", "origin", "destination",
        "scheduled_departure", "actual_departure", "scheduled_arrival", "actual_arrival",
        "delay_minutes", "delay_reason", "cancelled", "diverted", "aircraft_type",
        "distance", "route", "departure_hour", "flight_status", "largest_delay_factor", "delay_severity"
    ]
    for col in required_columns:
        validator.expect_column_to_exist(col)

    # 2. Key Uniqueness and Non-Null Expectations
    validator.expect_column_values_to_not_be_null("flight_id")
    validator.expect_column_values_to_be_unique("flight_id")

    # 3. Entity & Dimensional Consistency
    validator.expect_column_values_to_not_be_null("airline")
    validator.expect_column_values_to_be_in_set("airline", ["American Airlines", "Delta", "Southwest", "United"])

    validator.expect_column_values_to_not_be_null("origin")
    validator.expect_column_values_to_not_be_null("destination")

    # 4. Metric Value Range Checks
    validator.expect_column_values_to_be_between("delay_minutes", min_value=-10, max_value=30)
    validator.expect_column_values_to_be_between("distance", min_value=1, max_value=5000)
    validator.expect_column_values_to_be_between("departure_hour", min_value=0, max_value=23)

    # 5. Missing Data Thresholds
    # The missingness of delay_reason corresponds to on-time/early flights (~26.8%)
    validator.expect_column_missingness_to_be_between("delay_reason", min_percent=20.0, max_percent=35.0)

    # 6. Derived Lakehouse Features Validation
    validator.expect_column_values_to_not_be_null("largest_delay_factor")
    validator.expect_column_values_to_be_in_set(
        "flight_status", ["operated", "cancelled", "diverted", "cancelled_and_diverted"]
    )
    validator.expect_column_values_to_be_in_set(
        "delay_severity", ["On-Time", "Minor Delay (1-15 min)", "Moderate Delay (16-30 min)", "Severe Delay (>30 min)"]
    )

    # If deliberate failure testing requested
    if simulate_failure:
        validator.expect_column_values_to_be_between("delay_minutes", min_value=100, max_value=200)

    return validator.get_validation_summary()


def generate_markdown_report(summary: dict) -> str:
    md = []
    md.append("# Great Expectations Data Quality Validation Report\n")
    md.append(f"**Suite Name:** `{summary['expectation_suite_name']}`  ")
    md.append(f"**Execution Timestamp:** `{summary['run_id']}`  ")
    status_badge = "🟢 **PASSED**" if summary["success"] else "🔴 **FAILED**"
    md.append(f"**Validation Status:** {status_badge}  ")
    md.append(f"**Success Rate:** {summary['statistics']['success_percent']}% ({summary['statistics']['successful_expectations']}/{summary['statistics']['evaluated_expectations']} passed)  ")
    md.append(f"**Duration:** {summary['statistics']['duration_seconds']}s\n")

    md.append("## Summary Statistics\n")
    md.append("| Metric | Value |")
    md.append("| :--- | :--- |")
    md.append(f"| Total Evaluated Expectations | {summary['statistics']['evaluated_expectations']} |")
    md.append(f"| Successful Expectations | {summary['statistics']['successful_expectations']} |")
    md.append(f"| Unsuccessful Expectations | {summary['statistics']['unsuccessful_expectations']} |")
    md.append(f"| Overall Quality Score | {summary['statistics']['success_percent']}% |\n")

    md.append("## Detailed Expectation Results\n")
    md.append("| # | Expectation Type | Target / Column | Status | Observed Details |")
    md.append("| :---: | :--- | :--- | :---: | :--- |")

    for i, res in enumerate(summary["results"], 1):
        status = "✅ PASS" if res["success"] else "❌ FAIL"
        exp_type = res["expectation_type"]
        col = res["kwargs"].get("column", res["kwargs"].get("min_value", "Table-level"))
        details = []
        if "observed_value" in res["result"]:
            details.append(f"Observed: {res['result']['observed_value']}")
        if "unexpected_count" in res["result"]:
            details.append(f"Violations: {res['result']['unexpected_count']:,} ({res['result'].get('unexpected_percent', 0)}%)")
        if "min_observed" in res["result"]:
            details.append(f"Range: [{res['result']['min_observed']}, {res['result']['max_observed']}]")
        if "observed_null_percent" in res["result"]:
            details.append(f"Nulls: {res['result']['observed_null_percent']}%")
        detail_str = " | ".join(details) if details else "Satisfied criteria"

        md.append(f"| {i} | `{exp_type}` | `{col}` | {status} | {detail_str} |")

    md.append("\n## Data Quality Conclusion\n")
    if summary["success"]:
        md.append("> [!NOTE]\n> All data quality gates and schema validation checks passed successfully. The Silver Parquet dataset satisfies data integrity, uniqueness, range boundaries, and missingness thresholds. Downstream Gold aggregation is authorized to proceed.\n")
    else:
        md.append("> [!WARNING]\n> Data quality violations detected. Downstream Gold processing must be suspended until schema or anomaly violations are resolved.\n")

    return "\n".join(md)


def validate(silver_path=None, simulate_failure: bool = False):
    default_silver, report_json_path, report_md_path = get_default_paths()
    silver_path = silver_path or default_silver

    print("==================================================")
    print("STEP 3: DATA VALIDATION (GREAT EXPECTATIONS)")
    print("==================================================")
    print(f"Validating Silver dataset: {silver_path}")

    if not os.path.exists(silver_path):
        raise FileNotFoundError(f"Silver dataset not found: {silver_path}")

    df = pd.read_parquet(silver_path)

    summary = run_great_expectations_suite(df, simulate_failure=simulate_failure)

    # Save JSON results
    os.makedirs(os.path.dirname(report_json_path) or ".", exist_ok=True)
    with open(report_json_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Save Markdown report
    md_content = generate_markdown_report(summary)
    with open(report_md_path, "w") as f:
        f.write(md_content)

    print(f"Evaluated: {summary['statistics']['evaluated_expectations']} expectations")
    print(f"Passed: {summary['statistics']['successful_expectations']} | Failed: {summary['statistics']['unsuccessful_expectations']}")
    print(f"Success Rate: {summary['statistics']['success_percent']}%")
    print(f"Exported JSON report: {report_json_path}")
    print(f"Exported Markdown report: {report_md_path}")

    if not summary["success"]:
        print("\n❌ DATA VALIDATION FAILED! Halting downstream pipeline.")
        sys.exit(1)

    print("✅ All Great Expectations passed. Silver data is certified for Gold analytics.")
    print("--------------------------------------------------\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Great Expectations validation suite")
    parser.add_argument("--silver", default=None, help="Path to Silver Parquet")
    parser.add_argument("--simulate-failure", action="store_true", help="Deliberately fail validation to test pipeline failure handling")
    args = parser.parse_args()
    validate(args.silver, simulate_failure=args.simulate_failure)
