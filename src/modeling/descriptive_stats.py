# File:      src/modeling/descriptive_stats.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   Generate Table 1: descriptive statistics for all key series
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VARIABLES = {
    "eth_close":           "ETH price (USD)",
    "btc_close":           "BTC price (USD)",
    "tvl_total_usd":       "Total DeFi TVL (USD)",
    "tvl_uniswap_usd":     "Uniswap TVL (USD)",
    "tvl_aave_usd":        "Aave TVL (USD)",
    "usdc":                "USDC price (USD)",
    "eth_log_return":      "ETH log-return (daily)",
    "btc_log_return":      "BTC log-return (daily)",
    "tvl_log_return":      "TVL log-return (daily)",
    "eth_vol_30d":         "ETH volatility 30d (ann.)",
    "tvl_vol_30d":         "TVL volatility 30d (ann.)",
    "tvl_drawdown":        "TVL drawdown from peak",
    "vixcls":              "VIX index",
    "dtwexbgs":            "USD index (DXY)",
    "fedfunds":            "Fed Funds Rate (%)",
    "fear_greed":          "Fear & Greed Index",
    "sentiment_composite": "Sentiment composite (0-1)",
}


def run():
    print("\n=== Descriptive statistics ===")

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])

    rows = []
    for col, label in VARIABLES.items():
        if col not in df.columns:
            continue
        s = df[col].dropna()
        if len(s) < 10:
            continue

        jb_stat, jb_p = stats.jarque_bera(s)

        rows.append({
            "Variable":     label,
            "N":            int(len(s)),
            "Mean":         round(float(s.mean()), 6),
            "Std dev":      round(float(s.std()), 6),
            "Min":          round(float(s.min()), 6),
            "Median":       round(float(s.median()), 6),
            "Max":          round(float(s.max()), 6),
            "Skewness":     round(float(s.skew()), 4),
            "Kurtosis":     round(float(s.kurtosis()), 4),
            "JB p-value":   round(float(jb_p), 4),
        })

    table = pd.DataFrame(rows)
    out = OUTPUT_DIR / "table1_descriptive_stats.csv"
    table.to_csv(out, index=False)

    print(table.to_string(index=False))
    print(f"\n  → {out.name}")
    return table


if __name__ == "__main__":
    run()
