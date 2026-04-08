# File:      scripts/run_processing.py
# Component: econ-analytics pipeline — orchestration
# Purpose:   Run full processing pipeline: merge → features → export
# Rev:       v1.0.0
# Updated:   2026-04-08
#
# Usage:
#   cd "/c/Users/Public/VS Code/econ-analytics"
#   PYTHONPATH=. python scripts/run_processing.py

import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "processing"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))

from merge_panel      import run as run_merge
from compute_features import run as run_features

PROC_DIR   = Path(__file__).resolve().parents[1] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "tables"
PBI_DIR    = Path(__file__).resolve().parents[1] / "powerbi" / "datasets"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PBI_DIR.mkdir(parents=True, exist_ok=True)


def export_powerbi_tables(df):
    """Export clean, focused tables for Power BI consumption."""
    import pandas as pd, shutil

    print("\n=== Power BI export ===")

    # 1. Observations — full master panel
    obs_cols = ["date","eth_close","eth_volume","btc_close","tvl_total_usd",
                "tvl_uniswap_usd","tvl_aave_usd","usdc","vixcls","dtwexbgs",
                "fedfunds","fear_greed","gtrends_defi","gtrends_ethereum"]
    obs = df[[c for c in obs_cols if c in df.columns]]
    obs.to_csv(OUTPUT_DIR / "observations.csv", index=False)

    # 2. Predictions/features — derived variables
    feat_cols = ["date","eth_log_return","btc_log_return","tvl_log_return",
                 "eth_vol_30d","btc_vol_30d","tvl_vol_30d","tvl_drawdown",
                 "sentiment_composite","sentiment_z","fg_norm",
                 "usdc_depeg","usdc_deviation","vix_change","dxy_log_return","ffr_change"]
    feat = df[[c for c in feat_cols if c in df.columns]]
    feat.to_csv(OUTPUT_DIR / "features.csv", index=False)

    # 3. Event flags
    event_cols = ["date"] + [c for c in df.columns if c.startswith("event_")]
    events = df[event_cols]
    events.to_csv(OUTPUT_DIR / "event_flags.csv", index=False)

    # 4. USDC de-peg episodes summary
    if "usdc_depeg" in df.columns:
        depeg = df[df["usdc_depeg"] == 1][["date","usdc","usdc_deviation","usdc_depeg_severity"]]
        depeg.to_csv(OUTPUT_DIR / "depeg_events.csv", index=False)
        print(f"  depeg_events.csv: {len(depeg)} de-peg days")

    files = ["observations.csv","features.csv","event_flags.csv","depeg_events.csv"]
    for f in files:
        src = OUTPUT_DIR / f
        if src.exists():
            shutil.copy2(src, PBI_DIR / f)
            print(f"  {f:30s} → outputs/tables/ + powerbi/datasets/")

    print()


def main():
    print("="*60)
    print("  econ-analytics — processing pipeline")
    print("="*60)

    t0 = time.time()
    run_merge()
    df = run_features()
    export_powerbi_tables(df)

    print(f"Processing complete in {time.time()-t0:.0f}s")
    print(f"Files in outputs/tables/  : {list((Path('outputs/tables')).glob('*.csv'))}")
    print(f"Files in powerbi/datasets/: {list((Path('powerbi/datasets')).glob('*.csv'))}")


if __name__ == "__main__":
    main()
