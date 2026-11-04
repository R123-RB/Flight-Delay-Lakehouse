# Flight Delay Lakehouse – Data Dictionary

## 1. Raw / Bronze Layer (`flights.parquet`)
Preserves the exact schema of the raw Kaggle dataset:

| Column Name | Raw Type | Parquet Type | Nullable | Description & Domain |
| :--- | :--- | :--- | :---: | :--- |
| `FlightID` | integer / string | `int64` | No | Unique identifier for each scheduled flight record |
| `Airline` | string | `string` | No | Operating carrier: `American Airlines`, `Delta`, `Southwest`, `United` |
| `FlightNumber` | integer | `int64` | No | Scheduled operational flight number (0001 - 9999) |
| `Origin` | string | `string` | No | Departure airport IATA code (`ATL`, `DFW`, `JFK`, `LAX`, `ORD`) |
| `Destination` | string | `string` | No | Arrival airport IATA code (`BOS`, `JFK`, `MIA`, `SEA`, `SFO`) |
| `ScheduledDeparture` | string | `string` | No | Scheduled departure timestamp string (`YYYY-MM-DD HH:MM`) |
| `ActualDeparture` | string | `string` | No | Actual departure timestamp string (`YYYY-MM-DD HH:MM`) |
| `ScheduledArrival` | string | `string` | No | Scheduled arrival timestamp string (`YYYY-MM-DD HH:MM`) |
| `ActualArrival` | string | `string` | No | Actual arrival timestamp string (`YYYY-MM-DD HH:MM`) |
| `DelayMinutes` | integer | `int64` | No | Net flight delay duration in minutes (Range: -10 to +30) |
| `DelayReason` | string | `string` | Yes | Cause of delay (`Weather`, `Air Traffic Control`, `Maintenance`). Missing (null) when flight is on-time (`DelayMinutes <= 0`) |
| `Cancelled` | boolean | `bool` | No | Whether the flight was cancelled (`True` or `False`) |
| `Diverted` | boolean | `bool` | No | Whether the flight was diverted to an alternate airport (`True` or `False`) |
| `AircraftType` | string | `string` | No | Equipment model: `Airbus A320`, `Boeing 737`, `Boeing 777` |
| `TailNumber` | string | `string` | No | Aircraft registration number (e.g. `N71066`) |
| `Distance` | integer | `int64` | No | Flight distance in statute miles (Range: 131 to 2,980) |

---

## 2. Silver Layer (`flights_cleaned.parquet`)
Standardized, typed, and enriched with derived analytics features:

| Column Name | Data Type | Nullable | Description & Derivation Logic |
| :--- | :--- | :---: | :--- |
| `flight_id` | `int64` | No | Standardized primary key |
| `airline` | `string` | No | Standardized operating carrier name |
| `flight_number` | `int64` | No | Flight identification number |
| `origin` | `string` | No | Departure airport code |
| `destination` | `string` | No | Destination airport code |
| `scheduled_departure` | `datetime64[ns]` | No | Standardized ISO datetime of scheduled departure |
| `actual_departure` | `datetime64[ns]` | No | Standardized ISO datetime of actual departure |
| `scheduled_arrival` | `datetime64[ns]` | No | Standardized ISO datetime of scheduled arrival |
| `actual_arrival` | `datetime64[ns]` | No | Standardized ISO datetime of actual arrival |
| `delay_minutes` | `int64` | No | Delay duration in minutes |
| `delay_reason` | `string` | Yes | Recorded delay reason; null for on-time flights |
| `cancelled` | `bool` | No | Cancellation flag |
| `diverted` | `bool` | No | Diversion flag |
| `aircraft_type` | `string` | No | Aircraft model |
| `tail_number` | `string` | No | Aircraft tail registration |
| `distance` | `int64` | No | Route distance in miles |
| `route` | `string` | No | Derived corridor format: `origin-destination` (e.g. `JFK-MIA`) |
| `departure_date` | `string` | No | Derived scheduled departure date (`YYYY-MM-DD`) |
| `departure_hour` | `int32` | No | Hour of scheduled departure (`0` to `23`) |
| `departure_day_of_week` | `string` | No | Day name of scheduled departure (e.g. `Sunday`) |
| `actual_departure_delay_minutes` | `float64` | No | `(actual_departure - scheduled_departure)` in minutes |
| `actual_arrival_delay_minutes` | `float64` | No | `(actual_arrival - scheduled_arrival)` in minutes |
| `actual_flight_duration_minutes` | `float64` | No | `(actual_arrival - actual_departure)` in minutes |
| `flight_status` | `string` | No | Operational status: `operated`, `cancelled`, `diverted`, `cancelled_and_diverted` |
| `largest_delay_factor` | `string` | No | Derived primary delay cause: `None (On-Time / Early)`, `Flight Cancelled`, `Flight Diverted`, `Weather Delay`, `Carrier Equipment / Maintenance`, `Air Traffic Control / NAS Delay` |
| `delay_severity` | `string` | No | Severity category: `On-Time`, `Minor Delay (1-15 min)`, `Moderate Delay (16-30 min)`, `Severe Delay (>30 min)` |
| `is_weather_delay` | `int8` | No | Flag (1/0) indicating weather-attributed delay |
| `is_carrier_delay` | `int8` | No | Flag (1/0) indicating maintenance/carrier delay |
| `is_nas_security_delay` | `int8` | No | Flag (1/0) indicating air traffic control delay |

---

## 3. Gold Layer Marts (`data/gold/*.parquet`)

### `airline_summary.parquet`
Aggregates performance by carrier:
- `airline`: Carrier name
- `total_flights`: Total volume of scheduled flights
- `avg_delay_minutes`: Average recorded delay
- `median_delay_minutes`: Median delay
- `on_time_flights` & `on_time_pct`: Flight volume and percentage with delay <= 0
- `delayed_flights` & `delay_pct`: Flight volume and percentage with delay > 0
- `cancelled_flights` & `cancelled_pct`: Cancellations count and rate
- `diverted_flights` & `diverted_pct`: Diversions count and rate
- `avg_departure_delay`: Average difference between actual and scheduled departure
- `avg_arrival_delay`: Average difference between actual and scheduled arrival
- `weather_delays`, `maintenance_delays`, `atc_security_delays`: Count of delay causes

### `route_summary.parquet`
Aggregates performance across the 25 origin-destination corridors:
- `route`: Synthetic corridor key (e.g. `JFK-MIA`)
- `origin`: Departure airport
- `destination`: Arrival airport
- `total_flights`: Corridor volume
- `avg_delay_minutes`: Average delay
- `max_delay_minutes`: Maximum recorded delay
- `delayed_flights`: Number of delayed flights
- `delay_rate_pct`: Percentage of delayed flights
- `avg_distance_miles`: Average flight distance
- `avg_flight_duration_min`: Average duration

### `delay_factor_summary.parquet`
Overall distribution of `largest_delay_factor`:
- `largest_delay_factor`: Factor category
- `flight_count`: Number of flights
- `pct_of_total`: Percentage share
- `avg_delay_minutes`: Mean delay for this factor
- `min_delay_minutes` & `max_delay_minutes`: Range

### `airport_bottlenecks.parquet`
Hub analysis comparing departure and arrival impacts across the 9 airports:
- `airport_code`: IATA airport code
- `departing_flights`: Number of departing flights
- `avg_origin_delay`: Mean origin departure delay
- `origin_delay_rate_pct`: Percentage of departed flights delayed
- `arriving_flights`: Number of arriving flights
- `avg_destination_delay`: Mean destination arrival delay
- `dest_delay_rate_pct`: Percentage of arrived flights delayed
- `total_operations`: Sum of departures and arrivals

### `temporal_trends.parquet`
Diurnal profile across the 24 departure hours:
- `departure_hour`: Scheduled departure hour (0 to 23)
- `total_flights`: Flights scheduled in this window
- `avg_delay_minutes`: Mean delay
- `on_time_pct`: On-time percentage
- `delay_pct`: Delay percentage
- `moderate_delay_count`: Flights with delay between 16 and 30 minutes

### `aircraft_summary.parquet`
Fleet performance by equipment model:
- `aircraft_type`: `Airbus A320`, `Boeing 737`, `Boeing 777`
- `total_flights`: Volume flown
- `avg_delay_minutes`: Mean delay
- `avg_distance_miles`: Average flight distance
- `cancelled_flights` & `diverted_flights`: Disruption volume
