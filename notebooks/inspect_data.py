import os
import pandas as pd

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_csv_path = os.path.join(base_dir, "data", "raw", "flights.csv")

print(f"Loading raw dataset from: {raw_csv_path}")
df = pd.read_csv(raw_csv_path)

print("\n--- Dataset Shape ---")
print(f"Rows: {df.shape[0]:,}, Columns: {df.shape[1]}")

print("\n--- Column Names ---")
print(df.columns.tolist())

print("\n--- Data Types ---")
print(df.dtypes)

print("\n--- First 5 Records ---")
print(df.head())

print("\n--- Missing Values ---")
print(df.isnull().sum())

print("\n--- Duplicate Records ---")
print(f"Exact row duplicates: {df.duplicated().sum()}")
print(f"Duplicate (Year, Month, Day, Airline, FlightNumber, Origin, Dest): {df.duplicated(subset=['YEAR', 'MONTH', 'DAY', 'AIRLINE', 'FLIGHT_NUMBER', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT']).sum()}")

print("\n--- Statistical Summary ---")
print(df.describe(include="all").T)
