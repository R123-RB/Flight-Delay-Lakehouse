import argparse
import os
import time
import numpy as np
import pandas as pd

COLUMN_MAPPING = {
    "FlightID": "flight_id",
    "Airline": "airline",
    "FlightNumber": "flight_number",
    "Origin": "origin",
    "Destination": "destination",
    "ScheduledDeparture": "scheduled_departure",
    "ActualDeparture": "actual_departure",
    "ScheduledArrival": "scheduled_arrival",
    "ActualArrival": "actual_arrival",
    "DelayMinutes": "delay_minutes",
    "DelayReason": "delay_reason",
    "Cancelled": "cancelled",
    "Diverted": "diverted",
    "AircraftType": "aircraft_type",
    "TailNumber": "tail_number",
    "Distance": "distance",
}

TIMESTAMP_COLS = ["scheduled_departure", "actual_departure", "scheduled_arrival", "actual_arrival"]


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bronze_path = os.path.join(base_dir, "data", "bronze", "flights.parquet")
    silver_path = os.path.join(base_dir, "data", "silver", "flights_cleaned.parquet")
    return bronze_path, silver_path


def clean_data(bronze_path=None, silver_path=None):
    default_bronze, default_silver = get_default_paths()
    bronze_path = bronze_path or default_bronze
    silver_path = silver_path or default_silver

    print("==================================================")
    print("STEP 2: SILVER LAYER CLEANING & TRANSFORMATION")
    print("==================================================")
    print(f"Reading Bronze Parquet from: {bronze_path}")
    start_time = time.time()

    if not os.path.exists(bronze_path):
        raise FileNotFoundError(f"Bronze file not found: {bronze_path}")

    df = pd.read_parquet(bronze_path)
    print(f"Loaded Bronze data: {len(df):,} rows, {len(df.columns)} columns")

    # 1. Rename columns to standardized snake_case
    df = df.rename(columns=COLUMN_MAPPING)

    # 2. Parse timestamps to datetime
    for col in TIMESTAMP_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required timestamp column: {col}")
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # 3. Derive spatial & temporal fields
    df["route"] = df["origin"].astype(str) + "-" + df["destination"].astype(str)
    df["departure_date"] = df["scheduled_departure"].dt.date.astype("string")
    df["departure_hour"] = df["scheduled_departure"].dt.hour
    df["departure_day_of_week"] = df["scheduled_departure"].dt.day_name()

    # 4. Derive operational flight duration and delay differences
    df["actual_departure_delay_minutes"] = (
        (df["actual_departure"] - df["scheduled_departure"]).dt.total_seconds() / 60.0
    )
    df["actual_arrival_delay_minutes"] = (
        (df["actual_arrival"] - df["scheduled_arrival"]).dt.total_seconds() / 60.0
    )
    df["actual_flight_duration_minutes"] = (
        (df["actual_arrival"] - df["actual_departure"]).dt.total_seconds() / 60.0
    )

    # 5. Derive operational flight status
    # Handling cancelled and diverted combinations vectorially
    is_cancelled = df["cancelled"].astype(bool)
    is_diverted = df["diverted"].astype(bool)

    status_conditions = [
        is_cancelled & is_diverted,
        is_cancelled & ~is_diverted,
        ~is_cancelled & is_diverted,
    ]
    status_choices = ["cancelled_and_diverted", "cancelled", "diverted"]
    df["flight_status"] = np.select(status_conditions, status_choices, default="operated")

    # 6. Parse Delay Causes and derive largest delay factor (Core Project Requirement)
    # The dataset records DelayReason when DelayMinutes > 0, and null when DelayMinutes <= 0 (on-time).
    # Standardize cause names
    reason_map = {
        "Weather": "Weather Delay",
        "Maintenance": "Carrier Equipment / Maintenance",
        "Air Traffic Control": "Air Traffic Control / NAS Delay",
    }
    cleaned_reason = df["delay_reason"].map(reason_map)

    # Derive largest delay factor
    # Priority:
    # - If cancelled: "Flight Cancelled"
    # - If diverted (and not cancelled): "Flight Diverted"
    # - If delay_minutes <= 0: "None (On-Time / Early)"
    # - If delay_minutes > 0: mapped reason or "Unspecified Carrier Delay"
    delay_factor_conditions = [
        is_cancelled,
        is_diverted,
        df["delay_minutes"] <= 0,
        df["delay_minutes"] > 0 & cleaned_reason.notna(),
    ]
    delay_factor_choices = [
        "Flight Cancelled",
        "Flight Diverted",
        "None (On-Time / Early)",
        cleaned_reason,
    ]
    df["largest_delay_factor"] = np.select(
        delay_factor_conditions,
        delay_factor_choices,
        default="Unspecified Carrier Delay",
    )

    # 7. Categorize Delay Severity
    severity_conditions = [
        df["delay_minutes"] <= 0,
        (df["delay_minutes"] > 0) & (df["delay_minutes"] <= 15),
        (df["delay_minutes"] > 15) & (df["delay_minutes"] <= 30),
        df["delay_minutes"] > 30,
    ]
    severity_choices = [
        "On-Time",
        "Minor Delay (1-15 min)",
        "Moderate Delay (16-30 min)",
        "Severe Delay (>30 min)",
    ]
    df["delay_severity"] = np.select(severity_conditions, severity_choices, default="Unknown")

    # 8. Boolean cause indicators for OLAP aggregation
    df["is_weather_delay"] = (df["delay_reason"] == "Weather").astype("int8")
    df["is_carrier_delay"] = (df["delay_reason"] == "Maintenance").astype("int8")
    df["is_nas_security_delay"] = (df["delay_reason"] == "Air Traffic Control").astype("int8")

    # Write Silver Parquet
    os.makedirs(os.path.dirname(silver_path) or ".", exist_ok=True)
    df.to_parquet(silver_path, engine="pyarrow", index=False, compression="snappy")
    elapsed = time.time() - start_time

    silver_size_mb = os.path.getsize(silver_path) / (1024 * 1024)
    print(f"Silver Layer complete: {len(df):,} rows | {len(df.columns)} columns")
    print(f"Derived columns added: route, departure_date, departure_hour, flight_status, largest_delay_factor, delay_severity")
    print(f"Saved to: {silver_path} ({silver_size_mb:.2f} MB) in {elapsed:.2f}s")
    print("--------------------------------------------------\n")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and transform Bronze data into Silver Parquet")
    parser.add_argument("--bronze", default=None, help="Path to input Bronze Parquet")
    parser.add_argument("--silver", default=None, help="Path to output Silver Parquet")
    args = parser.parse_args()
    clean_data(args.bronze, args.silver)
