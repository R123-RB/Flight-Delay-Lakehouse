-- ============================================================================
-- Flight Delay Lakehouse - SQL Analytical Suite (DuckDB Engine)
-- ============================================================================
-- This suite executes against the cleaned Silver layer Parquet dataset
-- and addresses the core aviation questions:
-- 1. Fleet Overview & Delay Statistics
-- 2. Carrier Comparison (Reliability, Average Delay, On-Time Percentage)
-- 3. Top 10 Worst Routes by Average Delay
-- 4. Primary Delay Factor Breakdown (largest_delay_factor)
-- 5. Departure Hour Congestion & Hourly Bottlenecks
-- 6. Airport Bottlenecks (Origin Departure vs Destination Arrival Performance)
-- 7. Aircraft Fleet Performance & Delay Characteristics
-- 8. Cancellation and Diversion Rates by Airline
-- 9. Delay Severity Distribution (On-Time, Minor, Moderate)
-- 10. Carrier-Specific Cause Profiling (Maintenance vs ATC vs Weather)
-- ============================================================================

-- Create View over Silver Parquet
CREATE OR REPLACE VIEW silver AS 
SELECT * FROM read_parquet('data/silver/flights_cleaned.parquet');

-- ----------------------------------------------------------------------------
-- 1. FLEET OVERVIEW & HIGH-LEVEL KPIS
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) AS total_flight_records,
    ROUND(AVG(delay_minutes), 2) AS overall_avg_delay_min,
    ROUND(MEDIAN(delay_minutes), 2) AS overall_median_delay_min,
    MIN(delay_minutes) AS min_delay_min,
    MAX(delay_minutes) AS max_delay_min,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS fleet_on_time_pct,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS fleet_delay_pct,
    ROUND(100.0 * SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) / COUNT(*), 2) AS fleet_cancellation_pct
FROM silver;

-- ----------------------------------------------------------------------------
-- 2. CARRIER COMPARISON & ON-TIME RANKING
-- ----------------------------------------------------------------------------
SELECT
    airline,
    COUNT(*) AS flight_count,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_rate_pct,
    ROUND(AVG(actual_departure_delay_minutes), 2) AS avg_departure_delay_min,
    ROUND(AVG(actual_arrival_delay_minutes), 2) AS avg_arrival_delay_min,
    DENSE_RANK() OVER (ORDER BY AVG(delay_minutes) ASC) AS performance_rank
FROM silver
GROUP BY airline
ORDER BY performance_rank ASC;

-- ----------------------------------------------------------------------------
-- 3. TOP 10 WORST ROUTES BY AVERAGE DELAY
-- ----------------------------------------------------------------------------
SELECT
    route,
    origin,
    destination,
    COUNT(*) AS flight_count,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    MAX(delay_minutes) AS max_delay_minutes,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_frequency_pct,
    ROUND(AVG(distance), 1) AS avg_distance_miles,
    ROUND(AVG(actual_flight_duration_minutes), 1) AS avg_flight_duration_min
FROM silver
GROUP BY route, origin, destination
ORDER BY avg_delay_minutes DESC, flight_count DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 4. LARGEST DELAY FACTOR DISTRIBUTION
-- ----------------------------------------------------------------------------
SELECT
    largest_delay_factor,
    COUNT(*) AS flight_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver), 2) AS pct_of_total_flights,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    MIN(delay_minutes) AS min_delay_minutes,
    MAX(delay_minutes) AS max_delay_minutes
FROM silver
GROUP BY largest_delay_factor
ORDER BY flight_count DESC;

-- ----------------------------------------------------------------------------
-- 5. HOURLY BOTTLENECK ANALYSIS (SCHEDULED DEPARTURE HOUR)
-- ----------------------------------------------------------------------------
SELECT
    departure_hour,
    COUNT(*) AS departures_count,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delay_pct,
    SUM(CASE WHEN delay_severity = 'Moderate Delay (16-30 min)' THEN 1 ELSE 0 END) AS moderate_delays
FROM silver
GROUP BY departure_hour
ORDER BY departure_hour ASC;

-- ----------------------------------------------------------------------------
-- 6. AIRPORT BOTTLENECK ANALYSIS (ORIGIN VS DESTINATION IMPACT)
-- ----------------------------------------------------------------------------
WITH origin_metrics AS (
    SELECT
        origin AS airport,
        COUNT(*) AS flights_departed,
        ROUND(AVG(delay_minutes), 2) AS avg_dep_delay,
        ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS dep_delay_rate
    FROM silver
    GROUP BY origin
),
dest_metrics AS (
    SELECT
        destination AS airport,
        COUNT(*) AS flights_arrived,
        ROUND(AVG(delay_minutes), 2) AS avg_arr_delay,
        ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS arr_delay_rate
    FROM silver
    GROUP BY destination
)
SELECT
    COALESCE(o.airport, d.airport) AS airport_code,
    COALESCE(o.flights_departed, 0) AS departed_flights,
    COALESCE(o.avg_dep_delay, 0) AS avg_departure_delay_min,
    COALESCE(o.dep_delay_rate, 0) AS departure_delay_rate_pct,
    COALESCE(d.flights_arrived, 0) AS arrived_flights,
    COALESCE(d.avg_arr_delay, 0) AS avg_arrival_delay_min,
    COALESCE(d.arr_delay_rate, 0) AS arrival_delay_rate_pct,
    COALESCE(o.flights_departed, 0) + COALESCE(d.flights_arrived, 0) AS total_airport_movements
FROM origin_metrics o
FULL OUTER JOIN dest_metrics d ON o.airport = d.airport
ORDER BY total_airport_movements DESC;

-- ----------------------------------------------------------------------------
-- 7. AIRCRAFT FLEET RELIABILITY & PERFORMANCE
-- ----------------------------------------------------------------------------
SELECT
    aircraft_type,
    COUNT(*) AS total_flights,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    ROUND(AVG(distance), 1) AS avg_stage_length_miles,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancellation_rate_pct
FROM silver
GROUP BY aircraft_type
ORDER BY total_flights DESC;

-- ----------------------------------------------------------------------------
-- 8. CANCELLATION AND DIVERSION PROPORTIONS BY CARRIER
-- ----------------------------------------------------------------------------
SELECT
    airline,
    COUNT(*) AS total_scheduled_flights,
    SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) AS cancelled_flights,
    ROUND(100.0 * SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancellation_rate_pct,
    SUM(CASE WHEN diverted THEN 1 ELSE 0 END) AS diverted_flights,
    ROUND(100.0 * SUM(CASE WHEN diverted THEN 1 ELSE 0 END) / COUNT(*), 2) AS diversion_rate_pct,
    SUM(CASE WHEN flight_status = 'operated' THEN 1 ELSE 0 END) AS operated_flights,
    ROUND(100.0 * SUM(CASE WHEN flight_status = 'operated' THEN 1 ELSE 0 END) / COUNT(*), 2) AS operated_rate_pct
FROM silver
GROUP BY airline
ORDER BY cancellation_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- 9. DELAY SEVERITY PROFILE
-- ----------------------------------------------------------------------------
SELECT
    delay_severity,
    COUNT(*) AS flight_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver), 2) AS percentage_share,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    MIN(delay_minutes) AS min_delay,
    MAX(delay_minutes) AS max_delay
FROM silver
GROUP BY delay_severity
ORDER BY avg_delay_minutes ASC;

-- ----------------------------------------------------------------------------
-- 10. CARRIER SPECIFIC DELAY REASON PROFILING
-- ----------------------------------------------------------------------------
SELECT
    airline,
    SUM(is_weather_delay) AS weather_delay_events,
    ROUND(100.0 * SUM(is_weather_delay) / COUNT(*), 2) AS weather_delay_pct,
    SUM(is_carrier_delay) AS maintenance_delay_events,
    ROUND(100.0 * SUM(is_carrier_delay) / COUNT(*), 2) AS maintenance_delay_pct,
    SUM(is_nas_security_delay) AS atc_security_delay_events,
    ROUND(100.0 * SUM(is_nas_security_delay) / COUNT(*), 2) AS atc_security_delay_pct,
    SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) AS on_time_events,
    ROUND(100.0 * SUM(CASE WHEN delay_minutes <= 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct
FROM silver
GROUP BY airline
ORDER BY airline;
