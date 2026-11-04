# Flight Delay Lakehouse – Data Model & Schema Design

## 1. Dimensional Star Schema
The Flight Delay Lakehouse uses a Star Schema design optimized for OLAP aggregations in DuckDB and columnar query performance.

```mermaid
erDiagram
    FACT_FLIGHTS }|..|| DIM_AIRLINE : "operated_by"
    FACT_FLIGHTS }|..|| DIM_AIRPORT : "departs_from (origin)"
    FACT_FLIGHTS }|..|| DIM_AIRPORT : "arrives_at (destination)"
    FACT_FLIGHTS }|..|| DIM_AIRCRAFT : "flown_by"
    FACT_FLIGHTS }|..|| DIM_DATE : "scheduled_on"

    FACT_FLIGHTS {
        int64 flight_id PK
        string airline_code FK
        string origin_airport_code FK
        string destination_airport_code FK
        string aircraft_type FK
        date scheduled_date FK
        int32 flight_number
        int32 delay_minutes
        float actual_departure_delay_min
        float actual_arrival_delay_min
        float actual_flight_duration_min
        int32 distance
        boolean cancelled
        boolean diverted
        string flight_status
        string delay_reason
        string largest_delay_factor
        string delay_severity
        int8 is_weather_delay
        int8 is_carrier_delay
        int8 is_nas_security_delay
    }

    DIM_AIRLINE {
        string airline_code PK
        string airline_name
    }

    DIM_AIRPORT {
        string airport_code PK
        string airport_role
    }

    DIM_AIRCRAFT {
        string aircraft_type PK
        string manufacturer
    }

    DIM_DATE {
        date date_key PK
        int32 year
        int32 month
        int32 day
        string day_name
        int32 departure_hour
    }
```

---

## 2. Table Specifications

### Fact Table: `fact_flights` (Stored in `data/silver/flights_cleaned.parquet`)
- **Granularity:** One record per scheduled flight operation.
- **Grain Count:** 1,747,627 records.
- **Key Fields:**
  - `flight_id`: Unique identifier (1 to 1,747,627).
  - Foreign dimensions: `airline`, `origin`, `destination`, `aircraft_type`, `departure_date`.
- **Measures:**
  - `delay_minutes`: Primary recorded delay duration (-10 to +30 min).
  - `actual_departure_delay_minutes`: Scheduled vs actual departure differential.
  - `actual_arrival_delay_minutes`: Scheduled vs actual arrival differential.
  - `actual_flight_duration_minutes`: Elapsed in-air time.
  - `distance`: Stage length in miles (131 to 2,980 miles).
- **Categorical & Derived Attributes:**
  - `flight_status`: `operated`, `cancelled`, `diverted`, `cancelled_and_diverted`.
  - `largest_delay_factor`: Derived primary contributor.
  - `delay_severity`: Categorical classification (`On-Time`, `Minor Delay (1-15 min)`, `Moderate Delay (16-30 min)`).
  - `is_weather_delay`, `is_carrier_delay`, `is_nas_security_delay`.

### Dimension: `dim_airline`
- **Keys:** `American Airlines`, `Delta`, `Southwest`, `United`.
- **Attributes:** Airline Name, Fleet Profile.

### Dimension: `dim_airport`
- **Keys:** 9 distinct IATA codes: `ATL`, `BOS`, `DFW`, `JFK`, `LAX`, `MIA`, `ORD`, `SEA`, `SFO`.
- **Role:** Origin hubs and Destination terminals.

### Dimension: `dim_aircraft`
- **Keys:** `Airbus A320`, `Boeing 737`, `Boeing 777`.
- **Role:** Fleet categorization.
