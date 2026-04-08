# File:      scripts/run_analysis.py
# Component: econ-analytics pipeline — orchestration
# Purpose:   Run all six analysis scripts and copy outputs to Power BI
# Rev:       v1.0.0
# Updated:   2026-04-08
#
# Usage:
#   cd "/c/Users/Public/VS Code/econ-analytics"
#   pip install arch statsmodels scipy
#   PYTHONPATH=. python scripts/run_analysis.py

import sys, time, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "modeling"))

from descriptive_stats    import run as run_desc
from correlation_matrix   import run as run_corr
from garch_model          import run as run_garch
from event_study          import run as run_events
from lead_lag_sentiment   import run as run_leadlag
from regression_sentiment import run as run_regression

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "tables"
PBI_DIR    = Path(__file__).resolve().parents[1] / "powerbi" / "datasets"
PBI_DIR.mkdir(parents=True, exist_ok=True)

ANALYSIS_OUTPUTS = [
    "table1_descriptive_stats.csv",
    "table2_correlation_matrix.csv",
    "table2_pvalues.csv",
    "table3_garch_results.csv",
    "table4_event_study_summary.csv",
    "event_study_windows.csv",
    "table5_lead_lag_sentiment.csv",
    "table6_regression_coefficients.csv",
    "table6_regression_diagnostics.csv",
    "regression_residuals.csv",
]


def main():
    print("="*60)
    print("  econ-analytics — analysis pipeline")
    print("="*60)

    t0 = time.time()

    run_desc()
    run_corr()
    run_garch()
    run_events()
    run_leadlag()
    run_regression()

    # Copy all analysis outputs to Power BI datasets folder
    print("\n=== Copying to Power BI datasets ===")
    for fname in ANALYSIS_OUTPUTS:
        src = OUTPUT_DIR / fname
        if src.exists():
            shutil.copy2(src, PBI_DIR / fname)
            print(f"  {fname}")

    print(f"\nAnalysis complete in {time.time()-t0:.0f}s")
    print(f"\nAll outputs in: outputs/tables/")
    print(f"Power BI ready: powerbi/datasets/")


if __name__ == "__main__":
    main()
