import argparse
import os
import time
import pandas as pd


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_path = os.path.join(base_dir, "data", "raw", "flight_delays.csv")
    bronze_path = os.path.join(base_dir, "data", "bronze", "flights.parquet")
    return raw_path, bronze_path


def ingest_data(raw_path=None, bronze_path=None):
    default_raw, default_bronze = get_default_paths()
    raw_path = raw_path or default_raw
    bronze_path = bronze_path or default_bronze

    print("==================================================")
    print("STEP 1: BRONZE LAYER INGESTION & STORAGE (PARQUET)")
    print("==================================================")
    print(f"Reading raw data from: {raw_path}")
    start_time = time.time()

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Input file not found: {raw_path}")

    # Read raw CSV
    df = pd.read_csv(raw_path)
    read_elapsed = time.time() - start_time
    print(f"Loaded CSV in {read_elapsed:.2f}s | Rows: {len(df):,} | Columns: {len(df.columns)}")

    # Ensure bronze destination directory exists
    os.makedirs(os.path.dirname(bronze_path) or ".", exist_ok=True)

    # Write source-preserving Bronze Parquet
    write_start = time.time()
    df.to_parquet(bronze_path, engine="pyarrow", index=False, compression="snappy")
    write_elapsed = time.time() - write_start
    total_elapsed = time.time() - start_time

    # Calculate compression metrics
    csv_size_mb = os.path.getsize(raw_path) / (1024 * 1024)
    pq_size_mb = os.path.getsize(bronze_path) / (1024 * 1024)
    compression_ratio = csv_size_mb / pq_size_mb if pq_size_mb > 0 else 0

    print(f"Saved Bronze Parquet to: {bronze_path} in {write_elapsed:.2f}s")
    print(f"CSV Size: {csv_size_mb:.2f} MB | Parquet Size: {pq_size_mb:.2f} MB")
    print(f"Storage Reduction: {((1 - pq_size_mb / csv_size_mb) * 100):.1f}% (Compression Ratio: {compression_ratio:.2f}x)")
    print(f"Total Ingestion Duration: {total_elapsed:.2f}s")
    print("--------------------------------------------------\n")

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "csv_size_mb": csv_size_mb,
        "pq_size_mb": pq_size_mb,
        "compression_ratio": compression_ratio,
        "total_elapsed_sec": total_elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest raw CSV to Bronze Parquet")
    parser.add_argument("--raw", default=None, help="Path to raw CSV file")
    parser.add_argument("--bronze", default=None, help="Path to output Bronze Parquet file")
    args = parser.parse_args()
    ingest_data(args.raw, args.bronze)
