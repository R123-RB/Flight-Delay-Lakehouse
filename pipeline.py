import argparse
import os
import sys
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.ingestion.ingest import ingest_data
from src.transformations.clean_flights import clean_data
from src.validation.validate_flights import validate
from src.analytics.build_gold import build_gold
from src.reporting.visualize import generate_all_visualizations


def run_pipeline(
    run_ingest: bool = True,
    run_clean: bool = True,
    run_validation: bool = True,
    run_gold_layer: bool = True,
    run_viz: bool = True,
    simulate_failure: bool = False,
):
    print("\n" + "=" * 65)
    print("      FLIGHT DELAY LAKEHOUSE - END-TO-END BATCH PIPELINE")
    print("=" * 65)
    print(f"Project Base Directory: {BASE_DIR}")
    overall_start = time.time()

    # Stage 1: Ingestion
    if run_ingest:
        ingest_data()

    # Stage 2: Cleaning & Transformation
    if run_clean:
        clean_data()

    # Stage 3: Great Expectations Data Validation
    if run_validation:
        is_valid = validate(simulate_failure=simulate_failure)
        if not is_valid:
            print("Validation gate failed. Aborting downstream Gold generation.")
            sys.exit(1)

    # Stage 4: Gold Layer Analytical Marts
    if run_gold_layer:
        build_gold()

    # Stage 5: Visualizations & Reporting
    if run_viz:
        generate_all_visualizations()

    total_time = time.time() - overall_start
    print("=" * 65)
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f} SECONDS!")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Flight Delay Lakehouse Master Pipeline")
    parser.add_argument("--all", action="store_true", default=True, help="Run complete pipeline (default)")
    parser.add_argument("--ingest", action="store_true", help="Run ingestion only")
    parser.add_argument("--clean", action="store_true", help="Run cleaning & transformation only")
    parser.add_argument("--validate", action="store_true", help="Run Great Expectations validation only")
    parser.add_argument("--gold", action="store_true", help="Run Gold layer DuckDB analytics only")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations only")
    parser.add_argument("--simulate-failure", action="store_true", help="Deliberately fail validation check")

    args = parser.parse_args()

    # If any specific step is selected
    specific_selected = any([args.ingest, args.clean, args.validate, args.gold, args.visualize])

    if specific_selected:
        run_pipeline(
            run_ingest=args.ingest,
            run_clean=args.clean,
            run_validation=args.validate,
            run_gold_layer=args.gold,
            run_viz=args.visualize,
            simulate_failure=args.simulate_failure,
        )
    else:
        run_pipeline(simulate_failure=args.simulate_failure)


if __name__ == "__main__":
    main()
