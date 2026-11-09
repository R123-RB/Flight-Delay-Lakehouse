"""
Flight Delay Lakehouse - Master Pipeline Runner
Runs all 5 stages sequentially: Bronze → Silver → Validation → Gold → Visualizations
"""

import sys
import time
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def run_pipeline():
    overall_start = time.time()

    # Stage 1: Bronze Ingestion
    print("=" * 65)
    print("STAGE 1: BRONZE LAYER INGESTION")
    print("=" * 65)
    from src.ingestion.ingest import ingest_data
    ingest_data()

    # Stage 2: Silver Cleaning & Transformation
    print("=" * 65)
    print("STAGE 2: SILVER LAYER CLEANING & TRANSFORMATION")
    print("=" * 65)
    from src.transformations.clean_flights import clean_data
    clean_data()

    # Stage 3: Data Validation
    print("=" * 65)
    print("STAGE 3: DATA VALIDATION (GREAT EXPECTATIONS)")
    print("=" * 65)
    from src.validation.validate_flights import validate
    validate()

    # Stage 4: Gold Layer Analytics
    print("=" * 65)
    print("STAGE 4: GOLD LAYER ANALYTICS & MARTS")
    print("=" * 65)
    from src.analytics.build_gold import build_gold
    build_gold()

    # Stage 5: Visualizations
    print("=" * 65)
    print("STAGE 5: VISUALIZATION GENERATION")
    print("=" * 65)
    from src.reporting.visualize import generate_all_visualizations
    generate_all_visualizations()

    total = time.time() - overall_start
    print("=" * 65)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {total:.2f} SECONDS!")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline()
