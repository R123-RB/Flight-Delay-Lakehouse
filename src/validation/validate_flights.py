import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    silver_path = os.path.join(base_dir, "data", "silver", "flights_cleaned.parquet")
    report_json_path = os.path.join(base_dir, "reports", "validation_results.json")
    report_md_path = os.path.join(base_dir, "reports", "validation_report.md")
    return silver_path, report_json_path, report_md_path


class CustomExpectationsValidator:
    """
    Retained custom validation engine with Great Expectations-style expectation names
    and a GE-compatible JSON result schema. Used as a fallback when the Great
    Expectations framework is unavailable, and as a supplemental check set.
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
            "result": {"observed_value": row_count, "element_count": row_count},
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
        if column not in self.df.columns:
            self.results.append({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": column, "max_unexpected_percent": max_unexpected_percent},
                "success": False,
                "result": {"element_count": total, "unexpected_count": total, "unexpected_percent": 100.0,
                           "note": "column missing"},
            })
            return
        null_count = int(self.df[column].isna().sum())
        null_percent = (null_count / total) * 100.0 if total > 0 else 0.0
        success = null_percent <= max_unexpected_percent
        self.results.append({
            "expectation_type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": column, "max_unexpected_percent": max_unexpected_percent},
            "success": bool(success),
            "result": {"element_count": total, "unexpected_count": null_count,
                       "unexpected_percent": round(null_percent, 4)},
        })

    def expect_column_values_to_be_unique(self, column: str):
        total = len(self.df)
        if column not in self.df.columns:
            self.results.append({
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": column},
                "success": False,
                "result": {"element_count": total, "unique_count": 0, "unexpected_count": total,
                           "note": "column missing"},
            })
            return
        unique_count = self.df[column].nunique(dropna=False)
        duplicate_count = total - unique_count
        success = duplicate_count == 0
        self.results.append({
            "expectation_type": "expect_column_values_to_be_unique",
            "kwargs": {"column": column},
            "success": bool(success),
            "result": {"element_count": total, "unique_count": int(unique_count),
                       "unexpected_count": int(duplicate_count)},
        })

    def expect_column_values_to_be_between(self, column: str, min_value: float = None, max_value: float = None,
                                           max_unexpected_percent: float = 0.0):
        if column not in self.df.columns:
            self.results.append({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": column, "min_value": min_value, "max_value": max_value},
                "success": False,
                "result": {"element_count": len(self.df), "unexpected_count": len(self.df),
                           "unexpected_percent": 100.0, "note": "column missing"},
            })
            return
        series = self.df[column].dropna()
        total = len(series)
        cond = pd.Series(True, index=series.index)
        if min_value is not None:
            cond = cond & (series >= min_value)
        if max_value is not None:
            cond = cond & (series <= max_value)
        unexpected_count = int((~cond).sum())
        unexpected_percent = (unexpected_count / total) * 100.0 if total > 0 else 0.0
        success = unexpected_percent <= max_unexpected_percent
        self.results.append({
            "expectation_type": "expect_column_values_to_be_between",
            "kwargs": {"column": column, "min_value": min_value, "max_value": max_value,
                       "max_unexpected_percent": max_unexpected_percent},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unexpected_count": unexpected_count,
                "unexpected_percent": round(unexpected_percent, 4),
                "min_observed": float(series.min()) if total > 0 else None,
                "max_observed": float(series.max()) if total > 0 else None,
            },
        })

    def expect_column_values_to_be_in_set(self, column: str, value_set: list,
                                          max_unexpected_percent: float = 0.0):
        if column not in self.df.columns:
            self.results.append({
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {"column": column, "value_set": value_set},
                "success": False,
                "result": {"element_count": len(self.df), "unexpected_count": len(self.df),
                           "unexpected_percent": 100.0, "note": "column missing"},
            })
            return
        series = self.df[column].dropna()
        total = len(series)
        unexpected = series[~series.isin(value_set)]
        unexpected_count = len(unexpected)
        unexpected_percent = (unexpected_count / total) * 100.0 if total > 0 else 0.0
        success = unexpected_percent <= max_unexpected_percent
        self.results.append({
            "expectation_type": "expect_column_values_to_be_in_set",
            "kwargs": {"column": column, "value_set": value_set,
                       "max_unexpected_percent": max_unexpected_percent},
            "success": bool(success),
            "result": {
                "element_count": total,
                "unexpected_count": int(unexpected_count),
                "unexpected_percent": round(unexpected_percent, 4),
                "unexpected_examples": unexpected.astype(str).unique().tolist()[:5],
            },
        })

    def expect_column_missingness_to_be_between(self, column: str, min_percent: float, max_percent: float):
        total = len(self.df)
        if column not in self.df.columns:
            self.results.append({
                "expectation_type": "expect_column_missingness_to_be_between",
                "kwargs": {"column": column, "min_percent": min_percent, "max_percent": max_percent},
                "success": False,
                "result": {"element_count": total, "null_count": total, "observed_null_percent": 100.0,
                           "note": "column missing"},
            })
            return
        null_count = int(self.df[column].isna().sum())
        null_percent = (null_count / total) * 100.0 if total > 0 else 0.0
        success = min_percent <= null_percent <= max_percent
        self.results.append({
            "expectation_type": "expect_column_missingness_to_be_between",
            "kwargs": {"column": column, "min_percent": min_percent, "max_percent": max_percent},
            "success": bool(success),
            "result": {"element_count": total, "null_count": null_count,
                       "observed_null_percent": round(null_percent, 4)},
        })

    def get_validation_summary(self, engine_label: str):
        total_eval = len(self.results)
        successful_eval = sum(1 for r in self.results if r["success"])
        unsuccessful_eval = total_eval - successful_eval
        success_percent = (successful_eval / total_eval) * 100.0 if total_eval > 0 else 0.0
        return {
            "evaluation_engine": engine_label,
            "expectation_suite_name": self.suite_name,
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "success": unsuccessful_eval == 0,
            "statistics": {
                "evaluated_expectations": total_eval,
                "successful_expectations": successful_eval,
                "unsuccessful_expectations": unsuccessful_eval,
                "success_percent": round(success_percent, 2),
                "duration_seconds": round(time.time() - self.start_time, 3),
            },
            "results": self.results,
        }


# Backward-compatible alias for existing imports/tests
GreatExpectationsValidator = CustomExpectationsValidator


REQUIRED_COLUMNS = [
    "flight_id", "airline", "flight_number", "origin", "destination",
    "year", "month", "day", "day_of_week",
    "scheduled_departure", "actual_departure", "scheduled_arrival", "actual_arrival",
    "departure_delay_minutes", "arrival_delay_minutes",
    "air_system_delay_minutes", "security_delay_minutes", "airline_delay_minutes",
    "late_aircraft_delay_minutes", "weather_delay_minutes",
    "cancelled", "diverted", "cancellation_reason",
    "tail_number", "distance", "route",
    "departure_date", "departure_hour", "departure_day_of_week",
    "flight_status", "largest_delay_factor", "delay_severity",
    "is_weather_delay", "is_carrier_delay", "is_nas_security_delay",
]


def run_custom_expectations_suite(df: pd.DataFrame, simulate_failure: bool = False):
    v = CustomExpectationsValidator(df, suite_name="flight_silver_suite")
    v.expect_table_row_count_to_be_between(min_value=1_000_000, max_value=10_000_000)
    for col in REQUIRED_COLUMNS:
        v.expect_column_to_exist(col)
    v.expect_column_values_to_not_be_null("flight_id")
    v.expect_column_values_to_be_unique("flight_id")
    v.expect_column_values_to_not_be_null("airline")
    v.expect_column_values_to_be_in_set(
        "airline", ["AA", "AS", "B6", "DL", "EV", "F9", "HA", "MQ", "NK", "OO", "UA", "US", "VX", "WN"],
    )
    v.expect_column_values_to_not_be_null("origin")
    v.expect_column_values_to_not_be_null("destination")
    v.expect_column_values_to_be_between("departure_delay_minutes", min_value=-60, max_value=2000, max_unexpected_percent=1.0)
    v.expect_column_values_to_be_between("arrival_delay_minutes", min_value=-90, max_value=2000, max_unexpected_percent=1.0)
    v.expect_column_values_to_be_between("distance", min_value=1, max_value=5000)
    v.expect_column_values_to_be_between("departure_hour", min_value=0, max_value=23)
    v.expect_column_missingness_to_be_between("weather_delay_minutes", min_percent=75.0, max_percent=90.0)
    v.expect_column_values_to_not_be_null("largest_delay_factor")
    v.expect_column_values_to_be_in_set("flight_status", ["operated", "cancelled", "diverted", "cancelled_and_diverted"])
    v.expect_column_values_to_be_in_set(
        "delay_severity",
        ["On-Time", "Minor Delay (1-15 min)", "Moderate Delay (16-60 min)", "Severe Delay (>60 min)", "Not Applicable"],
    )
    if simulate_failure:
        v.expect_column_values_to_be_between("departure_delay_minutes", min_value=1000, max_value=2000)
    return v


def _normalize_gx_result(item, index):
    """Normalize varied GX result shapes to our GE-compatible report schema."""
    if isinstance(item, dict):
        exp_type = item.get("expectation_type") or item.get("expectation_config", {}).get("expectation_type") or "gx_expectation"
        kwargs = item.get("kwargs") or item.get("expectation_config", {}).get("kwargs") or {}
        success = bool(item.get("success", False))
        result = item.get("result") or {}
        return {"expectation_type": exp_type, "kwargs": kwargs, "success": success, "result": result}
    success = bool(getattr(item, "success", False))
    cfg = getattr(item, "expectation_config", None)
    exp_type = getattr(cfg, "expectation_type", None) or getattr(cfg, "type", None) or "gx_expectation"
    kwargs = getattr(cfg, "kwargs", None) or {}
    result = getattr(item, "result", None) or {}
    return {"expectation_type": str(exp_type), "kwargs": dict(kwargs) if kwargs else {}, "success": success, "result": dict(result) if result else {}}


def run_great_expectations_framework_suite(df: pd.DataFrame, simulate_failure: bool = False):
    """
    Execute validation using the Great Expectations framework (when installed).
    Returns (normalized_results, gx_version, gx_error_message).
    """
    try:
        import great_expectations as gx  # noqa: F401
        gx_version = getattr(gx, "__version__", "unknown")
    except Exception as exc:
        return None, None, str(exc)

    results = []
    try:
        # GX 1.x fluent API (preferred when available)
        context = gx.get_context(mode="ephemeral")
        ds_name = "flight_pandas"
        asset_name = "silver_flights"
        try:
            datasource = context.data_sources.add_pandas(name=ds_name)
        except Exception:
            datasource = context.data_sources.get(ds_name)
        try:
            asset = datasource.add_dataframe_asset(name=asset_name)
        except Exception:
            asset = datasource.get_asset(asset_name)
        batch_def = asset.add_batch_definition_whole_dataframe("silver_batch")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})

        suite_name = "flight_silver_suite_gx"
        suite = gx.ExpectationSuite(name=suite_name)
        # Core GX expectations (framework-native)
        suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=1_000_000, max_value=10_000_000))
        for col in REQUIRED_COLUMNS:
            suite.add_expectation(gx.expectations.ExpectColumnToExist(column=col))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="flight_id"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="flight_id"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="airline"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
            column="airline", value_set=["AA","AS","B6","DL","EV","F9","HA","MQ","NK","OO","UA","US","VX","WN"]))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="origin"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="destination"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="departure_delay_minutes", min_value=-60, max_value=2000, mostly=0.99))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="arrival_delay_minutes", min_value=-90, max_value=2000, mostly=0.99))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="distance", min_value=1, max_value=5000))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="departure_hour", min_value=0, max_value=23))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="largest_delay_factor"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
            column="flight_status", value_set=["operated","cancelled","diverted","cancelled_and_diverted"]))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
            column="delay_severity",
            value_set=["On-Time","Minor Delay (1-15 min)","Moderate Delay (16-60 min)","Severe Delay (>60 min)","Not Applicable"]))
        if simulate_failure:
            suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="departure_delay_minutes", min_value=1000, max_value=2000))

        validation = batch.validate(suite)
        raw_results = getattr(validation, "results", None) or (validation.get("results") if isinstance(validation, dict) else [])
        for i, item in enumerate(raw_results):
            results.append(_normalize_gx_result(item, i))
        return results, gx_version, None
    except Exception as exc:
        logger.warning(f"Great Expectations framework execution failed; using custom validator fallback: {exc}")
        return None, gx_version, str(exc)


# Backward-compatible function name
def run_great_expectations_suite(df: pd.DataFrame, simulate_failure: bool = False):
    """Runs GX framework checks when available plus retained custom checks; returns combined summary."""
    start = time.time()
    gx_results, gx_version, gx_error = run_great_expectations_framework_suite(df, simulate_failure=simulate_failure)
    custom = run_custom_expectations_suite(df, simulate_failure=simulate_failure)

    if gx_results is not None:
        engine = f"Great Expectations v{gx_version} + retained custom checks"
        custom.results = gx_results + custom.results
        custom.start_time = start
        summary = custom.get_validation_summary(engine)
        summary["great_expectations"] = {"available": True, "version": gx_version, "native_checks": len(gx_results), "custom_checks": len(summary["results"]) - len(gx_results)}
    else:
        engine = "Custom Validation Engine (Great Expectations-compatible fallback)"
        summary = custom.get_validation_summary(engine)
        summary["great_expectations"] = {"available": False, "version": gx_version, "error": gx_error}
    return summary


def generate_markdown_report(summary: dict) -> str:
    md = []
    md.append("# Data Quality Validation Report\n")
    md.append(f"**Suite Name:** `{summary['expectation_suite_name']}`  ")
    md.append(f"**Execution Timestamp:** `{summary['run_id']}`  ")
    status_badge = "🟢 **PASSED**" if summary["success"] else "🔴 **FAILED**"
    md.append(f"**Validation Status:** {status_badge}  ")
    md.append(f"**Evaluation Engine:** {summary['evaluation_engine']}  ")
    gx = summary.get("great_expectations") or {}
    if gx:
        md.append(f"**Great Expectations Framework:** available={gx.get('available')} version={gx.get('version')}  ")
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
        col = (res.get("kwargs") or {}).get("column", (res.get("kwargs") or {}).get("min_value", "Table-level"))
        details = []
        result = res.get("result") or {}
        if "observed_value" in result:
            details.append(f"Observed: {result['observed_value']}")
        if "unexpected_count" in result:
            details.append(f"Violations: {result['unexpected_count']} ({result.get('unexpected_percent', 0)}%)")
        if "min_observed" in result:
            details.append(f"Range: [{result['min_observed']}, {result['max_observed']}]")
        if "observed_null_percent" in result:
            details.append(f"Nulls: {result['observed_null_percent']}%")
        if result.get("note"):
            details.append(str(result["note"]))
        detail_str = " | ".join(details) if details else "Satisfied criteria"
        md.append(f"| {i} | `{exp_type}` | `{col}` | {status} | {detail_str} |")

    md.append("\n## Data Quality Conclusion\n")
    if summary["success"]:
        md.append("> [!NOTE]\n> Data quality gates passed. The Silver Parquet dataset satisfies the configured validation checks. Downstream Gold aggregation is authorized to proceed.\n")
    else:
        md.append("> [!WARNING]\n> Data quality violations detected. Downstream Gold processing must be suspended until violations are resolved.\n")

    return "\n".join(md)


def validate(silver_path=None, simulate_failure: bool = False):
    default_silver, report_json_path, report_md_path = get_default_paths()
    silver_path = silver_path or default_silver

    logger.info("=" * 50)
    logger.info("STEP 3: DATA VALIDATION (GREAT EXPECTATIONS + CUSTOM CHECKS)")
    logger.info("=" * 50)
    logger.info(f"Validating Silver dataset: {silver_path}")

    if not os.path.exists(silver_path):
        raise FileNotFoundError(f"Silver dataset not found: {silver_path}")

    df = pd.read_parquet(silver_path)
    summary = run_great_expectations_suite(df, simulate_failure=simulate_failure)

    os.makedirs(os.path.dirname(report_json_path) or ".", exist_ok=True)
    with open(report_json_path, "w") as f:
        json.dump(summary, f, indent=2)
    with open(report_md_path, "w") as f:
        f.write(generate_markdown_report(summary))

    logger.info(f"Engine: {summary['evaluation_engine']}")
    gx = summary.get("great_expectations") or {}
    logger.info(f"GX framework available={gx.get('available')} version={gx.get('version')}")
    logger.info(f"Evaluated: {summary['statistics']['evaluated_expectations']} expectations")
    logger.info(f"Passed: {summary['statistics']['successful_expectations']} | Failed: {summary['statistics']['unsuccessful_expectations']}")
    logger.info(f"Success Rate: {summary['statistics']['success_percent']}%")
    logger.info(f"Exported JSON report: {report_json_path}")
    logger.info(f"Exported Markdown report: {report_md_path}")

    if not summary["success"]:
        logger.error("❌ DATA VALIDATION FAILED! Halting downstream pipeline.")
        sys.exit(1)

    logger.info("✅ Data quality validation passed. Silver data is certified for Gold analytics.")
    logger.info("-" * 50 + "\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run data quality validation (Great Expectations + custom checks)")
    parser.add_argument("--silver", default=None, help="Path to Silver Parquet")
    parser.add_argument("--simulate-failure", action="store_true", help="Deliberately fail validation to test pipeline failure handling")
    args = parser.parse_args()
    validate(args.silver, simulate_failure=args.simulate_failure)
