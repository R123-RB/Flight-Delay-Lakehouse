# Data Product Guide (Completion Layer)

## Streamlit Dashboard (interactive BI)
A lightweight dashboard reads the canonical Gold marts.

```bash
pip install -r requirements-dev.txt
streamlit run dashboards/streamlit_app.py
```

Data source: `data/gold/*.parquet` (run pipeline first).

## Baseline Predictive Model (optional completion artifact)
A simple educational baseline predicts `delay_minutes > 15` from Silver features.

```bash
python src/analytics/predict_delay.py
```

Outputs:
- `models/delay_baseline_rf.joblib`
- `models/delay_baseline_metrics.json`

## Notes
- These components complete the end-to-end data product presentation without adding distributed frameworks.
- Full dataset training is sampled for speed; adjust in `src/analytics/predict_delay.py` if needed.