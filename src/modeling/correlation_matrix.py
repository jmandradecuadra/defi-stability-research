# File:      src/modeling/correlation_matrix.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   Generate Table 2: Pearson correlation matrix for key variables
#            Also exports p-values for significance marking
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORR_VARS = {
    "tvl_log_return":      "TVL return",
    "eth_log_return":      "ETH return",
    "btc_log_return":      "BTC return",
    "eth_vol_30d":         "ETH vol 30d",
    "tvl_drawdown":        "TVL drawdown",
    "usdc_deviation":      "USDC de-peg",
    "vixcls":              "VIX",
    "dtwexbgs":            "DXY",
    "fedfunds":            "Fed rate",
    "sentiment_composite": "Sentiment",
    "fear_greed":          "Fear & Greed",
}


def run():
    print("\n=== Correlation matrix ===")

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])

    available = {k: v for k, v in CORR_VARS.items() if k in df.columns}
    sub = df[list(available.keys())].rename(columns=available).dropna(how="all")

    corr = sub.corr(method="pearson")

    # Compute p-values matrix
    cols = corr.columns.tolist()
    pval = pd.DataFrame(np.ones((len(cols), len(cols))), columns=cols, index=cols)
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i != j:
                valid = sub[[c1, c2]].dropna()
                if len(valid) > 3:
                    _, p = stats.pearsonr(valid[c1], valid[c2])
                    pval.loc[c1, c2] = p

    corr_rounded = corr.round(3)
    out_corr = OUTPUT_DIR / "table2_correlation_matrix.csv"
    out_pval = OUTPUT_DIR / "table2_pvalues.csv"
    corr_rounded.to_csv(out_corr)
    pval.round(4).to_csv(out_pval)

    print(corr_rounded.to_string())
    print(f"\n  → {out_corr.name}")
    print(f"  → {out_pval.name}")
    return corr, pval


if __name__ == "__main__":
    run()
