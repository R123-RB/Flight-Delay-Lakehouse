import argparse
import logging
import os
import time
import duckdb
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    silver_path = os.path.join(base_dir, "data", "silver", "flights_cleaned.parquet")
    gold_dir = os.path.join(base_dir, "data", "gold")
    return silver_path, gold_dir


def build_gold(silver_path=None, gold_dir=None):
    default_silver, default_gold = get_default_paths()
    silver_path = silver_path or default_silver
    gold_dir = gold_dir or default_gold

    logger.info("=" * 50)
    logger.info("STEP 4: GOLD LAYER ANALYTICS & MARTS (DUCKDB)")
    logger.info("=" * 50)
    logger.info(f"Reading Silver Parquet from: {silver_path}")
    start_time = time.time()

    if not os.path.exists(silver_path):
        raise FileNotFoundError(f"Silver dataset not found: {silver_path}")

    os.makedirs(gold_dir, exist_ok=True)
    con = duckdb.connect()

    # Create analytical view over Silver Parquet
    con.execute(f"CREATE OR REPLACE VIEW silver AS SELECT * FROM read_parquet('{silver_path}')")

    queries = {
        "airline_summary": """
            SELECT
                airline,
                COUNT(*) AS total_flights,
                ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
                ROUND(MEDIAN(delay_minutes), 2) AS median_delay_minutes,
                SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) AS on_time_flights,
                ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct,
                SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) AS delayed_flights,
                ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_pct,
                SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) AS cancelled_flights,
                ROUND(100.0 * SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancelled_pct,
                SUM(CASE WHEN diverted THEN 1 ELSE 0 END) AS diverted_flights,
                ROUND(100.0 * SUM(CASE WHEN diverted THEN 1 ELSE 0 END) / COUNT(*), 2) AS diverted_pct,
                ROUND(AVG(actual_departure_delay_minutes), 2) AS avg_departure_delay,
                ROUND(AVG(actual_arrival_delay_minutes), 2) AS avg_arrival_delay,
                SUM(is_weather_delay) AS weather_delays,
                SUM(is_carrier_delay) AS maintenance_delays,
                SUM(is_nas_security_delay) AS atc_security_delays
            FROM silver
            GROUP BY airline
            ORDER BY avg_delay_minutes DESC
        """,
        "route_summary": """
            SELECT
                route,
                origin,
                destination,
                COUNT(*) AS total_flights,
                ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
                MAX(delay_minutes) AS max_delay_minutes,
                SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) AS delayed_flights,
                ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_rate_pct,
                ROUND(AVG(distance), 1) AS avg_distance_miles,
                ROUND(AVG(actual_flight_duration_minutes), 1) AS avg_flight_duration_min
            FROM silver
            GROUP BY route, origin, destination
            ORDER BY avg_delay_minutes DESC, total_flights DESC
            LIMIT 25
        """,
        "delay_factor_summary": """
            SELECT
                largest_delay_factor,
                COUNT(*) AS flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver), 2) AS pct_of_total,
                ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
                MIN(delay_minutes) AS min_delay_minutes,
                MAX(delay_minutes) AS max_delay_minutes
            FROM silver
            GROUP BY largest_delay_factor
            ORDER BY flight_count DESC
        """,
        "airport_bottlenecks": """
            WITH dep_stats AS (
                SELECT
                    origin AS airport_code,
                    COUNT(*) AS departing_flights,
                    ROUND(AVG(delay_minutes), 2) AS avg_origin_delay,
                    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS origin_delay_rate_pct
                FROM silver
                GROUP BY origin
            ),
            arr_stats AS (
                SELECT
                    destination AS airport_code,
                    COUNT(*) AS arriving_flights,
                    ROUND(AVG(delay_minutes), 2) AS avg_destination_delay,
                    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS dest_delay_rate_pct
                FROM silver
                GROUP BY destination
            )
            SELECT
                COALESCE(d.airport_code, a.airport_code) AS airport_code,
                COALESCE(d.departing_flights, 0) AS departing_flights,
                COALESCE(d.avg_origin_delay, 0) AS avg_origin_delay,
                COALESCE(d.origin_delay_rate_pct, 0) AS origin_delay_rate_pct,
                COALESCE(a.arriving_flights, 0) AS arriving_flights,
                COALESCE(a.avg_destination_delay, 0) AS avg_destination_delay,
                COALESCE(a.dest_delay_rate_pct, 0) AS dest_delay_rate_pct,
                COALESCE(d.departing_flights, 0) + COALESCE(a.arriving_flights, 0) AS total_operations
            FROM dep_stats d
            FULL OUTER JOIN arr_stats a ON d.airport_code = a.airport_code
            ORDER BY total_operations DESC
        """,
        "temporal_trends": """
            SELECT
                departure_hour,
                COUNT(*) AS total_flights,
                ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
                ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct,
                ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_pct,
                SUM(CASE WHEN delay_severity = 'Moderate Delay (16-60 min)' THEN 1 ELSE 0 END) AS moderate_delay_count
            FROM silver
            GROUP BY departure_hour
            ORDER BY departure_hour ASC
        """,
        "aircraft_summary": """
            SELECT
                COALESCE(tail_number, 'Unknown') AS tail_number,
                COUNT(*) AS total_flights,
                ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
                ROUND(AVG(distance), 1) AS avg_distance_miles,
                SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) AS cancelled_flights,
                SUM(CASE WHEN diverted THEN 1 ELSE 0 END) AS diverted_flights
            FROM silver
            GROUP BY tail_number
            ORDER BY total_flights DESC
        """
    }

    results = {}
    for name, q in queries.items():
        try:
            table_start = time.time()
            df_gold = con.execute(q).fetchdf()
            out_path = os.path.join(gold_dir, f"{name}.parquet")
            df_gold.to_parquet(out_path, engine="pyarrow", index=False)
            table_elapsed = time.time() - table_start
            results[name] = len(df_gold)
            logger.info(f"Materialized Gold Mart: '{name}' -> {out_path} ({len(df_gold)} rows in {table_elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"Failed to materialize Gold Mart '{name}': {e}")
            raise

    # Materialize logical dimensions for star-schema physical alignment
    try:
        con.execute(f"COPY (SELECT DISTINCT airline AS airline_code FROM silver ORDER BY airline) TO '{os.path.join(gold_dir,"dim_airline.parquet")}' (FORMAT PARQUET)")
        con.execute(f"COPY (SELECT DISTINCT airport_code FROM (SELECT origin AS airport_code FROM silver UNION ALL SELECT destination AS airport_code FROM silver) ORDER BY airport_code) TO '{os.path.join(gold_dir,"dim_airport.parquet")}' (FORMAT PARQUET)")
        logger.info('Materialized dimension tables: dim_airline, dim_airport')
    except Exception as e:
        logger.warning(f'Failed to materialize dimension tables: {e}')
    con.close()
    total_elapsed = time.time() - start_time
    logger.info(f"\nGold Layer generation complete in {total_elapsed:.2f}s across {len(queries)} analytical marts.")
    logger.info("-" * 50 + "\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Gold Analytical Marts using DuckDB")
    parser.add_argument("--silver", default=None, help="Path to Silver Parquet")
    parser.add_argument("--gold", default=None, help="Directory for Gold Parquet marts")
    args = parser.parse_args()
    build_gold(args.silver, args.gold)
