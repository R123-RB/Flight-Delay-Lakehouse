import pandas as pd

df = pd.read_csv(
    "/run/media/rehan/AC868F2D868EF75C/Desktop Protection/Semester 3/Data Engineering/Capstone project/Flight Delay Lakehouse/dataset/raw/flight_delays.csv"
)

print("\nDataset Shape:")
print(df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

print("\nFirst 5 Records:")
print(df.head())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Records:")
print(df.duplicated().sum())

print("\nStatistical Summary:")
print(df.describe(include="all").T)
