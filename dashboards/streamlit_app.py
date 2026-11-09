import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GOLD_DIR = os.path.join(BASE_DIR, "data", "gold")

st.set_page_config(page_title="Flight Delay Lakehouse Dashboard", layout="wide")
st.title("Flight Delay Lakehouse Dashboard")
st.caption("Interactive BI layer over Gold Parquet marts (DuckDB/Parquet lakehouse outputs)")

def load(name):
    p = os.path.join(GOLD_DIR, name)
    return pd.read_parquet(p) if os.path.exists(p) else None

air = load("airline_summary.parquet")
route = load("route_summary.parquet")
factor = load("delay_factor_summary.parquet")
ap = load("airport_bottlenecks.parquet")
temp = load("temporal_trends.parquet")

if air is None:
    st.error("Gold marts not found. Run the pipeline first to generate data/gold/*.parquet")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Airlines", len(air))
c2.metric("Total Flights", f"{int(air['total_flights'].sum()):,}")
c3.metric("Avg Delay (min)", f"{air['avg_delay_minutes'].mean():.2f}")

st.subheader("Carrier Performance")
st.dataframe(air.sort_values("avg_delay_minutes"))
st.bar_chart(air.set_index("airline")["avg_delay_minutes"])

if temp is not None:
    st.subheader("Hourly Delay Trend")
    st.line_chart(temp.set_index("departure_hour")["avg_delay_minutes"])

if factor is not None:
    st.subheader("Delay Factors")
    st.dataframe(factor)
    st.bar_chart(factor.set_index("largest_delay_factor")["flight_count"])

if route is not None:
    st.subheader("Top Routes")
    st.dataframe(route.head(25))

if ap is not None:
    st.subheader("Airport Bottlenecks")
    st.dataframe(ap.sort_values("total_operations", ascending=False).head(20))
