import argparse
import logging
import os
import time
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COLUMN_MAPPING = {
    "YEAR": "year",
    "MONTH": "month",
    "DAY": "day",
    "DAY_OF_WEEK": "day_of_week",
    "AIRLINE": "airline",
    "FLIGHT_NUMBER": "flight_number",
    "TAIL_NUMBER": "tail_number",
    "ORIGIN_AIRPORT": "origin",
    "DESTINATION_AIRPORT": "destination",
    "SCHEDULED_DEPARTURE": "scheduled_departure_hhmm",
    "DEPARTURE_TIME": "actual_departure_hhmm",
    "DEPARTURE_DELAY": "departure_delay_minutes",
    "TAXI_OUT": "taxi_out_minutes",
    "WHEELS_OFF": "wheels_off_hhmm",
    "SCHEDULED_TIME": "scheduled_time_minutes",
    "ELAPSED_TIME": "elapsed_time_minutes",
    "AIR_TIME": "air_time_minutes",
    "DISTANCE": "distance",
    "WHEELS_ON": "wheels_on_hhmm",
    "TAXI_IN": "taxi_in_minutes",
    "SCHEDULED_ARRIVAL": "scheduled_arrival_hhmm",
    "ARRIVAL_TIME": "actual_arrival_hhmm",
    "ARRIVAL_DELAY": "arrival_delay_minutes",
    "DIVERTED": "diverted",
    "CANCELLED": "cancelled",
    "CANCELLATION_REASON": "cancellation_reason",
    "AIR_SYSTEM_DELAY": "air_system_delay_minutes",
    "SECURITY_DELAY": "security_delay_minutes",
    "AIRLINE_DELAY": "airline_delay_minutes",
    "LATE_AIRCRAFT_DELAY": "late_aircraft_delay_minutes",
    "WEATHER_DELAY": "weather_delay_minutes",
}

TIMESTAMP_COLS = ["scheduled_departure_hhmm", "actual_departure_hhmm",
                  "scheduled_arrival_hhmm", "actual_arrival_hhmm"]

CAUSE_PRIORITY = [
    ("late_aircraft_delay_minutes", "Late Aircraft Delay"),
    ("airline_delay_minutes", "Airline / Carrier Delay"),
    ("air_system_delay_minutes", "Air System / NAS Delay"),
    ("weather_delay_minutes", "Weather Delay"),
    ("security_delay_minutes", "Security Delay"),
]

CAUSE_LABELS = dict(CAUSE_PRIORITY)
CAUSE_COLUMNS = [c for c, _ in CAUSE_PRIORITY]


def _combine_datetime(year, month, day, hhmm):
    """Build a pandas datetime from YEAR/MONTH/DAY + HHMM integer columns.

    HHMM values may be single/double digit (e.g. 5 means 00:05) so we zero-pad
    to 4 digits before parsing. Handle midnight rollover codes like 2400 by
    rolling over to next day.
    """
    hhmm_num = pd.to_numeric(hhmm, errors="coerce")
    rollover = hhmm_num == 2400
    hhmm_fixed = hhmm_num.copy()
    hhmm_fixed[rollover] = 0

    y = year.astype("Int64").astype("string")
    m = month.astype("Int64").astype("string").str.zfill(2)
    d = day.astype("Int64").astype("string").str.zfill(2)
    t = hhmm_fixed.astype("Int64").astype("string").str.zfill(4)
    combined = y + m + d + t
    dt = pd.to_datetime(combined, format="%Y%m%d%H%M", errors="coerce")
    if rollover.any():
        dt = dt.copy()
        dt.loc[rollover] = dt.loc[rollover] + pd.Timedelta(days=1)
    return dt


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bronze_path = os.path.join(base_dir, "data", "bronze", "flights.parquet")
    silver_path = os.path.join(base_dir, "data", "silver", "flights_cleaned.parquet")
    return bronze_path, silver_path


def clean_data(bronze_path=None, silver_path=None):
    default_bronze, default_silver = get_default_paths()
    bronze_path = bronze_path or default_bronze
    silver_path = silver_path or default_silver

    logger.info("=" * 50)
    logger.info("STEP 2: SILVER LAYER CLEANING & TRANSFORMATION")
    logger.info("=" * 50)
    logger.info(f"Reading Bronze Parquet from: {bronze_path}")
    start_time = time.time()

    if not os.path.exists(bronze_path):
        raise FileNotFoundError(f"Bronze file not found: {bronze_path}")

    df = pd.read_parquet(bronze_path)
    logger.info(f"Loaded Bronze data: {len(df):,} rows, {len(df.columns)} columns")

    # 1. Rename columns to standardized snake_case
    df = df.rename(columns=COLUMN_MAPPING)

    # 2. Parse HHMM timestamps into datetime64[ns] using YEAR/MONTH/DAY
    for hhmm_col in TIMESTAMP_COLS:
        dt_col = hhmm_col.replace("_hhmm", "")
        if hhmm_col not in df.columns:
            raise ValueError(f"Missing required timestamp column: {hhmm_col}")
        df[dt_col] = _combine_datetime(df["year"], df["month"], df["day"], df[hhmm_col])

    # 3. Derive spatial & temporal fields from scheduled departure
    df["route"] = df["origin"].astype(str) + "-" + df["destination"].astype(str)
    df["departure_date"] = (
        df["year"].astype("Int64").astype("string").str.zfill(2) + "-" +
        df["month"].astype("Int64").astype("string").str.zfill(2) + "-" +
        df["day"].astype("Int64").astype("string").str.zfill(2)
    )
    df["departure_hour"] = (df["scheduled_departure_hhmm"].fillna(0).astype("Int64") // 100).astype("int32")
    df["departure_day_of_week"] = df["day_of_week"].map(
        {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
         5: "Friday", 6: "Saturday", 7: "Sunday"}
    )

    # 4. Operational delay minutes (authoritative BTS columns)
    df["actual_departure_delay_minutes"] = df["departure_delay_minutes"]
    df["actual_arrival_delay_minutes"] = df["arrival_delay_minutes"]
    df["actual_flight_duration_minutes"] = df["air_time_minutes"]
    # Keep a `delay_minutes` alias for downstream Gold SQL compatibility
    df["delay_minutes"] = df["departure_delay_minutes"]

    # 5. Operational flight status (cancelled / diverted / operated)
    is_cancelled = df["cancelled"].astype(bool)
    is_diverted = df["diverted"].astype(bool)

    status_conditions = [
        is_cancelled & is_diverted,
        is_cancelled & ~is_diverted,
        ~is_cancelled & is_diverted,
    ]
    status_choices = ["cancelled_and_diverted", "cancelled", "diverted"]
    df["flight_status"] = np.select(status_conditions, status_choices, default="operated")

    # 6. Surrogate flight_id (BTS has no native flight identifier; composite key is
    #    YEAR+MONTH+DAY+AIRLINE+FLIGHT_NUMBER+ORIGIN+DESTINATION)
    df.insert(0, "flight_id", range(1, len(df) + 1))

    # 7. Derive largest_delay_factor (primary disruption factor)
    #    - cancelled -> "Flight Cancelled"
    #    - diverted (not cancelled) -> "Flight Diverted"
    #    - departure_delay <= 0 -> "None (On-Time / Early)"
    #    - delayed with cause data -> cause with max minutes (priority tie-break)
    #    - delayed with no cause -> "Unspecified / Not Reported"
    delay_factor_conditions = [
        is_cancelled,
        is_diverted & ~is_cancelled,
        df["departure_delay_minutes"] <= 0,
    ]
    delay_factor_choices = [
        "Flight Cancelled",
        "Flight Diverted",
        "None (On-Time / Early)",
    ]
    largest_delay_factor = np.select(
        delay_factor_conditions, delay_factor_choices, default=""
    )
    df["largest_delay_factor"] = largest_delay_factor

    delayed_mask = (~is_cancelled) & (~is_diverted) & (df["departure_delay_minutes"] > 0)
    if delayed_mask.any():
        delayed_idx = df.index[delayed_mask]
        causes = df.loc[delayed_idx, CAUSE_COLUMNS].fillna(0)
        max_vals = causes.max(axis=1)
        factor_vals = pd.Series("Unspecified / Not Reported", index=delayed_idx, dtype=object)
        for col, label in CAUSE_PRIORITY:
            is_max = (causes[col] == max_vals) & (max_vals > 0) & (factor_vals == "Unspecified / Not Reported")
            factor_vals = factor_vals.mask(is_max, label)
        df.loc[delayed_idx, "largest_delay_factor"] = factor_vals

    # Fill remaining unset factors (delayed rows not covered above)
    df["largest_delay_factor"] = df["largest_delay_factor"].replace("", "Unspecified / Not Reported")

    # 8. Categorize Delay Severity based on departure delay
    severity_conditions = [
        df["departure_delay_minutes"] <= 0,
        (df["departure_delay_minutes"] > 0) & (df["departure_delay_minutes"] <= 15),
        (df["departure_delay_minutes"] > 15) & (df["departure_delay_minutes"] <= 60),
        df["departure_delay_minutes"] > 60,
    ]
    severity_choices = [
        "On-Time",
        "Minor Delay (1-15 min)",
        "Moderate Delay (16-60 min)",
        "Severe Delay (>60 min)",
    ]
    df["delay_severity"] = np.select(severity_conditions, severity_choices, default="Not Applicable")

    # 9. Boolean cause indicators for OLAP aggregation
    df["is_weather_delay"] = (df["weather_delay_minutes"].fillna(0) > 0).astype("int8")
    df["is_carrier_delay"] = (
        (df["airline_delay_minutes"].fillna(0) > 0) |
        (df["late_aircraft_delay_minutes"].fillna(0) > 0)
    ).astype("int8")
    df["is_nas_security_delay"] = (
        (df["air_system_delay_minutes"].fillna(0) > 0) |
        (df["security_delay_minutes"].fillna(0) > 0)
    ).astype("int8")

    # Drop raw HHMM time columns (datetimes are the canonical form)
    drop_cols = ["scheduled_departure_hhmm", "actual_departure_hhmm",
                 "scheduled_arrival_hhmm", "actual_arrival_hhmm",
                 "wheels_off_hhmm", "wheels_on_hhmm"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Write Silver Parquet
    os.makedirs(os.path.dirname(silver_path) or ".", exist_ok=True)
    df.to_parquet(silver_path, engine="pyarrow", index=False, compression="snappy")
    elapsed = time.time() - start_time

    silver_size_mb = os.path.getsize(silver_path) / (1024 * 1024)
    logger.info(f"Silver Layer complete: {len(df):,} rows | {len(df.columns)} columns")
    logger.info(f"Derived columns added: route, departure_date, departure_hour, flight_status, largest_delay_factor, delay_severity")
    logger.info(f"Saved to: {silver_path} ({silver_size_mb:.2f} MB) in {elapsed:.2f}s")
    logger.info("-" * 50 + "\n")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and transform Bronze data into Silver Parquet")
    parser.add_argument("--bronze", default=None, help="Path to input Bronze Parquet")
    parser.add_argument("--silver", default=None, help="Path to output Silver Parquet")
    args = parser.parse_args()
    clean_data(args.bronze, args.silver)
