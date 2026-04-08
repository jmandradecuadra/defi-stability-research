# File:      src/modeling/lead_lag_sentiment.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   Cross-correlation analysis: does sentiment lead or lag TVL and ETH?
#            Tests lags 1-14 days in both directions
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_LAG = 14


def cross_corr_with_pval(x, y, lag):
    """Pearson correlation between x and y shifted by lag days.
    Positive lag: x leads y (x at t, y at t+lag).
    Negative lag: y leads x (y at t, x at t-lag).
    """
    if lag > 0:
        x_aligned = x.iloc[:-lag].values
        y_aligned = y.iloc[lag:].values
    elif lag < 0:
        x_aligned = x.iloc[-lag:].values
        y_aligned = y.iloc[:lag].values
    else:
        x_aligned = x.values
        y_aligned = y.values

    mask = ~(np.isnan(x_aligned) | np.isnan(y_aligned))
    x_clean = x_aligned[mask]
    y_clean = y_aligned[mask]

    if len(x_clean) < 10:
        return np.nan, np.nan

    r, p = stats.pearsonr(x_clean, y_clean)
    return round(float(r), 4), round(float(p), 4)


def run():
    print("\n=== Lead-lag sentiment analysis ===")

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    sentiment = df["sentiment_composite"]
    fg        = df["fear_greed"]

    targets = {}
    if "tvl_log_return" in df.columns:
        targets["TVL return"]    = df["tvl_log_return"]
    if "tvl_total_usd" in df.columns:
        targets["TVL level"]     = df["tvl_total_usd"]
    if "eth_log_return" in df.columns:
        targets["ETH return"]    = df["eth_log_return"]
    if "eth_vol_30d" in df.columns:
        targets["ETH vol 30d"]   = df["eth_vol_30d"]

    rows = []
    lags = list(range(-MAX_LAG, MAX_LAG + 1))

    for target_name, target_series in targets.items():
        for lag in lags:
            r_comp, p_comp = cross_corr_with_pval(sentiment, target_series, lag)
            r_fg,   p_fg   = cross_corr_with_pval(fg / 100, target_series, lag)
            rows.append({
                "target":          target_name,
                "lag_days":        lag,
                "direction":       "sentiment leads" if lag > 0 else ("target leads" if lag < 0 else "contemporaneous"),
                "r_composite":     r_comp,
                "p_composite":     p_comp,
                "r_fear_greed":    r_fg,
                "p_fear_greed":    p_fg,
                "sig_composite":   "***" if p_comp < 0.01 else ("**" if p_comp < 0.05 else ("*" if p_comp < 0.10 else "")),
            })

    result = pd.DataFrame(rows)
    out = OUTPUT_DIR / "table5_lead_lag_sentiment.csv"
    result.to_csv(out, index=False)

    # Print peak correlations per target
    print("\n  Peak correlations (sentiment composite → target):")
    for target_name in targets:
        sub = result[result["target"] == target_name].dropna(subset=["r_composite"])
        if sub.empty:
            continue
        peak = sub.loc[sub["r_composite"].abs().idxmax()]
        print(f"\n  {target_name}:")
        print(f"    Peak r = {peak['r_composite']:>7.4f}  at lag {int(peak['lag_days']):>+3d} days  "
              f"p={peak['p_composite']:.4f} {peak['sig_composite']}")
        print(f"    Direction: {peak['direction']}")

    print(f"\n  → {out.name}")
    return result


if __name__ == "__main__":
    run()
