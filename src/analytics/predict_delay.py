"""Baseline predictive model: delay-severity classifier using Silver features.

Lightweight educational baseline completing the lakehouse data product.
Uses scikit-learn when installed, or a native NumPy/Pandas empirical Bayes
baseline if scikit-learn is not available in the environment.
"""
import os
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SILVER = os.path.join(BASE_DIR, "data", "silver", "flights_cleaned.parquet")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def main():
    if not os.path.exists(SILVER):
        # Support fallback fixture if silver is absent
        fixture = os.path.join(BASE_DIR, "tests", "fixtures", "sample_flights.csv")
        if os.path.exists(fixture):
            from src.ingestion.ingest import ingest_data
            from src.transformations.clean_flights import clean_data
            bronze = os.path.join(BASE_DIR, "data", "bronze", "flights.parquet")
            ingest_data(fixture, bronze)
            clean_data(bronze, SILVER)
        else:
            raise FileNotFoundError(f"Silver dataset not found: {SILVER}")

    df = pd.read_parquet(SILVER)
    sample_size = min(len(df), 200_000)
    if len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    target = (df["delay_minutes"].fillna(0) > 15).astype(int)
    features = pd.DataFrame({
        "departure_hour": df["departure_hour"].fillna(0).astype(int),
        "distance": df["distance"].fillna(0).astype(float),
        "month": pd.to_numeric(df.get("month", 1), errors="coerce").fillna(1).astype(int),
        "day_of_week": pd.to_numeric(df.get("day_of_week", 1), errors="coerce").fillna(1).astype(int),
    })

    try:
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import classification_report, accuracy_score
        import joblib

        Xtr, Xte, ytr, yte = train_test_split(
            features, target, test_size=0.2, random_state=42,
            stratify=target if target.nunique() > 1 else None
        )
        clf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
        clf.fit(Xtr, ytr)
        pred = clf.predict(Xte)
        rep = {
            "engine": "scikit-learn RandomForestClassifier",
            "accuracy": round(float(accuracy_score(yte, pred)), 4),
            "report": classification_report(yte, pred, output_dict=True, zero_division=0),
            "rows_used": int(len(df)),
            "features": list(features.columns),
            "target": "departure_delay_minutes > 15 (Severe Disruption)",
        }
        joblib.dump(clf, os.path.join(MODEL_DIR, "delay_baseline_rf.joblib"))
    except ImportError:
        # Native vectorized baseline (Empirical Bayesian Risk Scoring)
        split_idx = int(len(features) * 0.8)
        Xtr, Xte = features.iloc[:split_idx], features.iloc[split_idx:]
        ytr, yte = target.iloc[:split_idx], target.iloc[split_idx:]

        # Calculate hour-of-day empirical delay prior
        hour_risk = ytr.groupby(Xtr["departure_hour"]).mean()
        overall_prior = float(ytr.mean())

        # Predict based on prior threshold (risk > 0.25)
        test_risk = Xte["departure_hour"].map(hour_risk).fillna(overall_prior)
        pred = (test_risk > 0.25).astype(int)

        accuracy = float((pred == yte).mean()) if len(yte) > 0 else 0.0
        rep = {
            "engine": "Empirical Bayesian Risk Scorer (NumPy/Pandas Fallback)",
            "accuracy": round(accuracy, 4),
            "overall_delay_rate": round(overall_prior, 4),
            "hour_risk_profile": {int(k): round(float(v), 3) for k, v in hour_risk.items()},
            "rows_used": int(len(df)),
            "features": list(features.columns),
            "target": "departure_delay_minutes > 15 (Severe Disruption)",
        }

    out_metrics = os.path.join(MODEL_DIR, "delay_baseline_metrics.json")
    with open(out_metrics, "w") as f:
        json.dump(rep, f, indent=2)

    print(json.dumps({"engine": rep["engine"], "accuracy": rep["accuracy"], "rows_used": rep["rows_used"]}, indent=2))


if __name__ == "__main__":
    main()
