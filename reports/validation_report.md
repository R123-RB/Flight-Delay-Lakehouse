# Data Quality Validation Report

**Suite Name:** `flight_silver_suite`  
**Execution Timestamp:** `20261108_172924`  
**Validation Status:** 🔴 **FAILED**  
**Evaluation Engine:** Custom Validation Engine (Great Expectations-compatible fallback)  
**Great Expectations Framework:** available=False version=None  
**Success Rate:** 98.04% (50/51 passed)  
**Duration:** 1.651s

## Summary Statistics

| Metric | Value |
| :--- | :--- |
| Total Evaluated Expectations | 51 |
| Successful Expectations | 50 |
| Unsuccessful Expectations | 1 |
| Overall Quality Score | 98.04% |

## Detailed Expectation Results

| # | Expectation Type | Target / Column | Status | Observed Details |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `expect_table_row_count_to_be_between` | `1000000` | ✅ PASS | Observed: 5819079 |
| 2 | `expect_column_to_exist` | `flight_id` | ✅ PASS | Observed: True |
| 3 | `expect_column_to_exist` | `airline` | ✅ PASS | Observed: True |
| 4 | `expect_column_to_exist` | `flight_number` | ✅ PASS | Observed: True |
| 5 | `expect_column_to_exist` | `origin` | ✅ PASS | Observed: True |
| 6 | `expect_column_to_exist` | `destination` | ✅ PASS | Observed: True |
| 7 | `expect_column_to_exist` | `year` | ✅ PASS | Observed: True |
| 8 | `expect_column_to_exist` | `month` | ✅ PASS | Observed: True |
| 9 | `expect_column_to_exist` | `day` | ✅ PASS | Observed: True |
| 10 | `expect_column_to_exist` | `day_of_week` | ✅ PASS | Observed: True |
| 11 | `expect_column_to_exist` | `scheduled_departure` | ✅ PASS | Observed: True |
| 12 | `expect_column_to_exist` | `actual_departure` | ✅ PASS | Observed: True |
| 13 | `expect_column_to_exist` | `scheduled_arrival` | ✅ PASS | Observed: True |
| 14 | `expect_column_to_exist` | `actual_arrival` | ✅ PASS | Observed: True |
| 15 | `expect_column_to_exist` | `departure_delay_minutes` | ✅ PASS | Observed: True |
| 16 | `expect_column_to_exist` | `arrival_delay_minutes` | ✅ PASS | Observed: True |
| 17 | `expect_column_to_exist` | `air_system_delay_minutes` | ✅ PASS | Observed: True |
| 18 | `expect_column_to_exist` | `security_delay_minutes` | ✅ PASS | Observed: True |
| 19 | `expect_column_to_exist` | `airline_delay_minutes` | ✅ PASS | Observed: True |
| 20 | `expect_column_to_exist` | `late_aircraft_delay_minutes` | ✅ PASS | Observed: True |
| 21 | `expect_column_to_exist` | `weather_delay_minutes` | ✅ PASS | Observed: True |
| 22 | `expect_column_to_exist` | `cancelled` | ✅ PASS | Observed: True |
| 23 | `expect_column_to_exist` | `diverted` | ✅ PASS | Observed: True |
| 24 | `expect_column_to_exist` | `cancellation_reason` | ✅ PASS | Observed: True |
| 25 | `expect_column_to_exist` | `tail_number` | ✅ PASS | Observed: True |
| 26 | `expect_column_to_exist` | `distance` | ✅ PASS | Observed: True |
| 27 | `expect_column_to_exist` | `route` | ✅ PASS | Observed: True |
| 28 | `expect_column_to_exist` | `departure_date` | ✅ PASS | Observed: True |
| 29 | `expect_column_to_exist` | `departure_hour` | ✅ PASS | Observed: True |
| 30 | `expect_column_to_exist` | `departure_day_of_week` | ✅ PASS | Observed: True |
| 31 | `expect_column_to_exist` | `flight_status` | ✅ PASS | Observed: True |
| 32 | `expect_column_to_exist` | `largest_delay_factor` | ✅ PASS | Observed: True |
| 33 | `expect_column_to_exist` | `delay_severity` | ✅ PASS | Observed: True |
| 34 | `expect_column_to_exist` | `is_weather_delay` | ✅ PASS | Observed: True |
| 35 | `expect_column_to_exist` | `is_carrier_delay` | ✅ PASS | Observed: True |
| 36 | `expect_column_to_exist` | `is_nas_security_delay` | ✅ PASS | Observed: True |
| 37 | `expect_column_values_to_not_be_null` | `flight_id` | ✅ PASS | Violations: 0 (0.0%) |
| 38 | `expect_column_values_to_be_unique` | `flight_id` | ✅ PASS | Violations: 0 (0%) |
| 39 | `expect_column_values_to_not_be_null` | `airline` | ✅ PASS | Violations: 0 (0.0%) |
| 40 | `expect_column_values_to_be_in_set` | `airline` | ✅ PASS | Violations: 0 (0.0%) |
| 41 | `expect_column_values_to_not_be_null` | `origin` | ✅ PASS | Violations: 0 (0.0%) |
| 42 | `expect_column_values_to_not_be_null` | `destination` | ✅ PASS | Violations: 0 (0.0%) |
| 43 | `expect_column_values_to_be_between` | `departure_delay_minutes` | ✅ PASS | Violations: 3 (0.0001%) | Range: [-82.0, 1988.0] |
| 44 | `expect_column_values_to_be_between` | `arrival_delay_minutes` | ✅ PASS | Violations: 0 (0.0%) | Range: [-87.0, 1971.0] |
| 45 | `expect_column_values_to_be_between` | `distance` | ✅ PASS | Violations: 0 (0.0%) | Range: [21.0, 4983.0] |
| 46 | `expect_column_values_to_be_between` | `departure_hour` | ✅ PASS | Violations: 0 (0.0%) | Range: [0.0, 23.0] |
| 47 | `expect_column_missingness_to_be_between` | `weather_delay_minutes` | ✅ PASS | Nulls: 81.725% |
| 48 | `expect_column_values_to_not_be_null` | `largest_delay_factor` | ✅ PASS | Violations: 0 (0.0%) |
| 49 | `expect_column_values_to_be_in_set` | `flight_status` | ✅ PASS | Violations: 0 (0.0%) |
| 50 | `expect_column_values_to_be_in_set` | `delay_severity` | ✅ PASS | Violations: 0 (0.0%) |
| 51 | `expect_column_values_to_be_between` | `departure_delay_minutes` | ❌ FAIL | Violations: 5732653 (99.9952%) | Range: [-82.0, 1988.0] |

## Data Quality Conclusion

> [!WARNING]
> Data quality violations detected. Downstream Gold processing must be suspended until violations are resolved.
