# Flight Delay Lakehouse – Data Dictionary

## 1. Raw / Bronze Layer (`data/bronze/flights.parquet`)
Source-preserving Parquet converted from the raw BTS/Kaggle CSV by `src/ingestion/ingest.py`.

| Column Name | Parquet Type (typical) | Nullable | Description & Domain |
| :--- | :--- | :---: | :--- |
| `YEAR` | `int64` | No | Year of scheduled departure |
| `MONTH` | `int64` | No | Month of scheduled departure (1-12) |
| `DAY` | `int64` | No | Day of scheduled departure (1-31) |
| `DAY_OF_WEEK` | `int64` | No | Day of week (1=Monday … 7=Sunday) |
| `AIRLINE` | `string` | No | Operating carrier IATA code (e.g., `AA`, `DL`, `UA`, `WN`, `B6`, `NK`, `AS`, `HA`, `F9`, `EV`, `MQ`, `OO`, `US`, `VX`) |
| `FLIGHT_NUMBER` | `string` (ingested as identifier) | No | Scheduled flight number |
| `TAIL_NUMBER` | `string` | Yes | Aircraft registration (null in some records) |
| `ORIGIN_AIRPORT` | `string` | No | Departure airport IATA code |
| `DESTINATION_AIRPORT` | `string` | No | Arrival airport IATA code |
| `SCHEDULED_DEPARTURE` | `int64` / HHMM value | No | Scheduled departure time (HHMM) |
| `DEPARTURE_TIME` | `float64` / HHMM value | Yes | Actual departure time (HHMM); null for cancelled |
| `DEPARTURE_DELAY` | `float64` | Yes | Departure delay in minutes; null for cancelled |
| `TAXI_OUT` | `float64` | Yes | Taxi-out time in minutes |
| `WHEELS_OFF` | `float64` / HHMM value | Yes | Wheels-off time (HHMM) |
| `SCHEDULED_TIME` | `float64` | Yes | Scheduled elapsed time in minutes |
| `ELAPSED_TIME` | `float64` | Yes | Actual elapsed time in minutes |
| `AIR_TIME` | `float64` | Yes | Actual airborne time in minutes |
| `DISTANCE` | `int64` | No | Route distance in statute miles |
| `WHEELS_ON` | `float64` / HHMM value | Yes | Wheels-on time (HHMM) |
| `TAXI_IN` | `float64` | Yes | Taxi-in time in minutes |
| `SCHEDULED_ARRIVAL` | `int64` / HHMM value | No | Scheduled arrival time (HHMM) |
| `ARRIVAL_TIME` | `float64` / HHMM value | Yes | Actual arrival time (HHMM) |
| `ARRIVAL_DELAY` | `float64` | Yes | Arrival delay in minutes |
| `DIVERTED` | `int64` | No | Diversion flag (0/1) |
| `CANCELLED` | `int64` | No | Cancellation flag (0/1) |
| `CANCELLATION_REASON` | `string` | Yes | `A`=carrier, `B`=weather, `C`=NAS, `D`=security/late-aircraft context varies by BTS encoding; null when not cancelled |
| `AIR_SYSTEM_DELAY` | `float64` | Yes | Air system / NAS delay minutes (cause breakdown; often null) |
| `SECURITY_DELAY` | `float64` | Yes | Security delay minutes (often null) |
| `AIRLINE_DELAY` | `float64` | Yes | Carrier delay minutes (often null) |
| `LATE_AIRCRAFT_DELAY` | `float64` | Yes | Late aircraft delay minutes (often null) |
| `WEATHER_DELAY` | `float64` | Yes | Weather delay minutes (often null) |

---

## 2. Silver Layer (`data/silver/flights_cleaned.parquet`)
Standardized, typed, and enriched by `src/transformations/clean_flights.py`. This is the physical fact table for analytics.

| Column Name | Data Type | Nullable | Description & Derivation Logic |
| :--- | :--- | :---: | :--- |
| `flight_id` | `int64` | No | Surrogate primary key (1..N) generated in Silver. |
| `airline` | `string` | No | Operating carrier IATA code (from `AIRLINE`). |
| `flight_number` | `string` | No | Flight identifier (from `FLIGHT_NUMBER`). |
| `tail_number` | `string` | Yes | Aircraft registration (from `TAIL_NUMBER`). |
| `origin` | `string` | No | Departure airport code (from `ORIGIN_AIRPORT`). |
| `destination` | `string` | No | Arrival airport code (from `DESTINATION_AIRPORT`). |
| `year` | `int64` | No | Scheduled departure year. |
| `month` | `int64` | No | Scheduled departure month. |
| `day` | `int64` | No | Scheduled departure day. |
| `day_of_week` | `int64` | No | Scheduled day of week (1=Monday … 7=Sunday). |
| `scheduled_departure` | `datetime64[ns]` | No | Parsed scheduled departure timestamp (YEAR/MONTH/DAY + scheduled HHMM). |
| `actual_departure` | `datetime64[ns]` | Yes | Parsed actual departure timestamp; null when unavailable/cancelled. |
| `scheduled_arrival` | `datetime64[ns]` | No | Parsed scheduled arrival timestamp. |
| `actual_arrival` | `datetime64[ns]` | Yes | Parsed actual arrival timestamp; null when unavailable/cancelled. |
| `departure_delay_minutes` | `float64` | Yes | BTS departure delay minutes. |
| `arrival_delay_minutes` | `float64` | Yes | BTS arrival delay minutes. |
| `delay_minutes` | `float64` | Yes | Alias of `departure_delay_minutes` for downstream compatibility. |
| `actual_departure_delay_minutes` | `float64` | Yes | Alias of `departure_delay_minutes`. |
| `actual_arrival_delay_minutes` | `float64` | Yes | Alias of `arrival_delay_minutes`. |
| `actual_flight_duration_minutes` | `float64` | Yes | Alias of `air_time_minutes`. |
| `taxi_out_minutes` | `float64` | Yes | Taxi-out minutes. |
| `taxi_in_minutes` | `float64` | Yes | Taxi-in minutes. |
| `scheduled_time_minutes` | `float64` | Yes | Scheduled elapsed minutes. |
| `elapsed_time_minutes` | `float64` | Yes | Actual elapsed minutes. |
| `air_time_minutes` | `float64` | Yes | Airborne minutes. |
| `distance` | `int64` | No | Route distance in statute miles. |
| `cancelled` | `int64` | No | Cancellation flag (0/1). |
| `diverted` | `int64` | No | Diversion flag (0/1). |
| `cancellation_reason` | `string` | Yes | BTS cancellation reason code; null when not cancelled. |
| `air_system_delay_minutes` | `float64` | Yes | NAS/air-system delay minutes. |
| `security_delay_minutes` | `float64` | Yes | Security delay minutes. |
| `airline_delay_minutes` | `float64` | Yes | Carrier delay minutes. |
| `late_aircraft_delay_minutes` | `float64` | Yes | Late aircraft delay minutes. |
| `weather_delay_minutes` | `float64` | Yes | Weather delay minutes. |
| `route` | `string` | No | Derived corridor key: `origin-destination`. |
| `departure_date` | `string` | No | Derived scheduled departure date (`YYYY-MM-DD`). |
| `departure_hour` | `int32` | No | Scheduled departure hour (0–23). |
| `departure_day_of_week` | `string` | No | Day name (e.g., `Monday`). |
| `flight_status` | `string` | No | `operated`, `cancelled`, `diverted`, `cancelled_and_diverted`. |
| `largest_delay_factor` | `string` | No | Primary disruption factor: `None (On-Time / Early)`, `Flight Cancelled`, `Flight Diverted`, `Weather Delay`, `Airline / Carrier Delay`, `Late Aircraft Delay`, `Air System / NAS Delay`, `Security Delay`, `Unspecified / Not Reported`. |
| `delay_severity` | `string` | No | `On-Time`, `Minor Delay (1-15 min)`, `Moderate Delay (16-60 min)`, `Severe Delay (>60 min)`, `Not Applicable`. |
| `is_weather_delay` | `int8` | No | 1 if weather delay minutes > 0 else 0. |
| `is_carrier_delay` | `int8` | No | 1 if airline or late-aircraft delay minutes > 0 else 0. |
| `is_nas_security_delay` | `int8` | No | 1 if air-system or security delay minutes > 0 else 0. |

> **Alignment note:** Raw HHMM helper columns are converted to datetime fields and not retained in the final Silver schema.

---

## 3. Gold Layer Marts (`data/gold/*.parquet`)
Canonical marts produced by `src/analytics/build_gold.py`. (Other `data/gold/*.parquet` files may exist from prior runs/experiments and are not canonical outputs of the current build script.)

### `airline_summary.parquet` (1 row per `airline`)
- `airline`, `total_flights`, `avg_delay_minutes`, `median_delay_minutes`
- `on_time_flights`, `on_time_pct`, `delayed_flights`, `delay_pct`
- `cancelled_flights`, `cancelled_pct`, `diverted_flights`, `diverted_pct`
- `avg_departure_delay`, `avg_arrival_delay`
- `weather_delays`, `maintenance_delays`, `atc_security_delays`

### `route_summary.parquet` (top corridor summary; 1 row per `route`)
- `route`, `origin`, `destination`, `total_flights`
- `avg_delay_minutes`, `max_delay_minutes`, `delayed_flights`, `delay_rate_pct`
- `avg_distance_miles`, `avg_flight_duration_min`

### `delay_factor_summary.parquet` (1 row per `largest_delay_factor`)
- `largest_delay_factor`, `flight_count`, `pct_of_total`
- `avg_delay_minutes`, `min_delay_minutes`, `max_delay_minutes`

### `airport_bottlenecks.parquet` (1 row per `airport_code`)
- `airport_code`, `departing_flights`, `avg_origin_delay`, `origin_delay_rate_pct`
- `arriving_flights`, `avg_destination_delay`, `dest_delay_rate_pct`, `total_operations`

### `temporal_trends.parquet` (1 row per `departure_hour`)
- `departure_hour`, `total_flights`, `avg_delay_minutes`, `on_time_pct`, `delay_pct`, `moderate_delay_count`

### `aircraft_summary.parquet` (1 row per `tail_number`)
- `tail_number`, `total_flights`, `avg_delay_minutes`, `avg_distance_miles`, `cancelled_flights`, `diverted_flights`

> **Note:** BTS does not publish aircraft type; `aircraft_summary` uses registration (`tail_number`) as the fleet proxy.

---

## 4. Keys & Relationships (Physical Implementation)
- **Silver PK:** `flight_id` (validated unique/non-null).
- **Logical FKs in Silver:** `airline`, `origin`, `destination`, `departure_date`, `tail_number` (documented/modelled; not DB-enforced in Parquet).
- **Gold lineage:** all canonical marts are aggregated from `data/silver/flights_cleaned.parquet` via DuckDB.
