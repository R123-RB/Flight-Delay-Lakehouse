# Great Expectations Data Quality Validation Report

**Suite Name:** `flight_silver_suite`  
**Execution Timestamp:** `20261104_104301`  
**Validation Status:** 🔴 **FAILED**  
**Success Rate:** 97.14% (34/35 passed)  
**Duration:** 0.196s

## Summary Statistics

| Metric | Value |
| :--- | :--- |
| Total Evaluated Expectations | 35 |
| Successful Expectations | 34 |
| Unsuccessful Expectations | 1 |
| Overall Quality Score | 97.14% |

## Detailed Expectation Results

| # | Expectation Type | Target / Column | Status | Observed Details |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `expect_table_row_count_to_be_between` | `1000000` | ✅ PASS | Observed: 1747627 |
| 2 | `expect_column_to_exist` | `flight_id` | ✅ PASS | Observed: True |
| 3 | `expect_column_to_exist` | `airline` | ✅ PASS | Observed: True |
| 4 | `expect_column_to_exist` | `flight_number` | ✅ PASS | Observed: True |
| 5 | `expect_column_to_exist` | `origin` | ✅ PASS | Observed: True |
| 6 | `expect_column_to_exist` | `destination` | ✅ PASS | Observed: True |
| 7 | `expect_column_to_exist` | `scheduled_departure` | ✅ PASS | Observed: True |
| 8 | `expect_column_to_exist` | `actual_departure` | ✅ PASS | Observed: True |
| 9 | `expect_column_to_exist` | `scheduled_arrival` | ✅ PASS | Observed: True |
| 10 | `expect_column_to_exist` | `actual_arrival` | ✅ PASS | Observed: True |
| 11 | `expect_column_to_exist` | `delay_minutes` | ✅ PASS | Observed: True |
| 12 | `expect_column_to_exist` | `delay_reason` | ✅ PASS | Observed: True |
| 13 | `expect_column_to_exist` | `cancelled` | ✅ PASS | Observed: True |
| 14 | `expect_column_to_exist` | `diverted` | ✅ PASS | Observed: True |
| 15 | `expect_column_to_exist` | `aircraft_type` | ✅ PASS | Observed: True |
| 16 | `expect_column_to_exist` | `distance` | ✅ PASS | Observed: True |
| 17 | `expect_column_to_exist` | `route` | ✅ PASS | Observed: True |
| 18 | `expect_column_to_exist` | `departure_hour` | ✅ PASS | Observed: True |
| 19 | `expect_column_to_exist` | `flight_status` | ✅ PASS | Observed: True |
| 20 | `expect_column_to_exist` | `largest_delay_factor` | ✅ PASS | Observed: True |
| 21 | `expect_column_to_exist` | `delay_severity` | ✅ PASS | Observed: True |
| 22 | `expect_column_values_to_not_be_null` | `flight_id` | ✅ PASS | Violations: 0 (0.0%) |
| 23 | `expect_column_values_to_be_unique` | `flight_id` | ✅ PASS | Violations: 0 (0%) |
| 24 | `expect_column_values_to_not_be_null` | `airline` | ✅ PASS | Violations: 0 (0.0%) |
| 25 | `expect_column_values_to_be_in_set` | `airline` | ✅ PASS | Violations: 0 (0.0%) |
| 26 | `expect_column_values_to_not_be_null` | `origin` | ✅ PASS | Violations: 0 (0.0%) |
| 27 | `expect_column_values_to_not_be_null` | `destination` | ✅ PASS | Violations: 0 (0.0%) |
| 28 | `expect_column_values_to_be_between` | `delay_minutes` | ✅ PASS | Violations: 0 (0.0%) | Range: [-10.0, 30.0] |
| 29 | `expect_column_values_to_be_between` | `distance` | ✅ PASS | Violations: 0 (0.0%) | Range: [100.0, 3000.0] |
| 30 | `expect_column_values_to_be_between` | `departure_hour` | ✅ PASS | Violations: 0 (0.0%) | Range: [0.0, 23.0] |
| 31 | `expect_column_missingness_to_be_between` | `delay_reason` | ✅ PASS | Nulls: 26.8291% |
| 32 | `expect_column_values_to_not_be_null` | `largest_delay_factor` | ✅ PASS | Violations: 0 (0.0%) |
| 33 | `expect_column_values_to_be_in_set` | `flight_status` | ✅ PASS | Violations: 0 (0.0%) |
| 34 | `expect_column_values_to_be_in_set` | `delay_severity` | ✅ PASS | Violations: 0 (0.0%) |
| 35 | `expect_column_values_to_be_between` | `delay_minutes` | ❌ FAIL | Violations: 1,747,627 (100.0%) | Range: [-10.0, 30.0] |

## Data Quality Conclusion

> [!WARNING]
> Data quality violations detected. Downstream Gold processing must be suspended until schema or anomaly violations are resolved.
