# File:      src/processing/compute_features.py
# Component: econ-analytics pipeline — processing layer
# Purpose:   Compute log-returns, rolling volatility, USDC de-peg episodes,
#            stress event flags, and sentiment composite index
# Rev:       v1.0.0
# Updated:   2026-04-08

import numpy as np
import pandas as pd
from pathlib import Path

PROC_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

# Stress event windows (± days around date)
STRESS_EVENTS = {
    "luna":  ("2022-05-09", 30),   # Terra/LUNA collapse
    "ftx":   ("2022-11-11", 30),   # FTX bankruptcy filing
    "svb":   ("2023-03-10", 30),   # Silicon Valley Bank failure
}

DEPEG_THRESHOLD = 0.005   # |price - 1| > 0.5 cents = de-peg episode


def run():
    print("\n=== Feature computation ===")

    panel_path = PROC_DIR / "master_panel.csv"
    if not panel_path.exists():
        raise FileNotFoundError("master_panel.csv not found — run merge_panel.py first")

    df = pd.read_csv(panel_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # ── 1. Log-returns ────────────────────────────────────────
    print("  Computing log-returns ...")
    for col, new_col in [("eth_close", "eth_log_return"),
                          ("btc_close", "btc_log_return"),
                          ("tvl_total_usd", "tvl_log_return")]:
        if col in df.columns:
            df[new_col] = np.log(df[col] / df[col].shift(1))

    # ── 2. Rolling 30-day volatility ─────────────────────────
    print("  Computing 30-day rolling volatility ...")
    for col, new_col in [("eth_log_return",  "eth_vol_30d"),
                          ("btc_log_return",  "btc_vol_30d"),
                          ("tvl_log_return",  "tvl_vol_30d")]:
        if col in df.columns:
            df[new_col] = df[col].rolling(30, min_periods=15).std() * np.sqrt(365)

    # ── 3. TVL drawdown from 90-day rolling peak ─────────────
    print("  Computing TVL drawdown ...")
    if "tvl_total_usd" in df.columns:
        rolling_peak = df["tvl_total_usd"].rolling(90, min_periods=1).max()
        df["tvl_drawdown"] = (df["tvl_total_usd"] - rolling_peak) / rolling_peak

    # ── 4. Stress event dummy variables ──────────────────────
    print("  Flagging stress events ...")
    for event_name, (event_date, window) in STRESS_EVENTS.items():
        center = pd.Timestamp(event_date)
        df[f"event_{event_name}"] = (
            (df["date"] >= center - pd.Timedelta(days=window)) &
            (df["date"] <= center + pd.Timedelta(days=window))
        ).astype(int)

    # ── 5. USDC de-peg episodes ───────────────────────────────
    print("  Computing USDC de-peg episodes ...")
    if "usdc" in df.columns:
        df["usdc_depeg"]          = (abs(df["usdc"] - 1.0) > DEPEG_THRESHOLD).astype(int)
        df["usdc_deviation"]      = df["usdc"] - 1.0
        df["usdc_depeg_severity"] = abs(df["usdc_deviation"])

    # ── 6. Sentiment composite index (0-1 normalized) ─────────
    print("  Building sentiment composite ...")

    sentiment_cols = []

    if "fear_greed" in df.columns:
        df["fg_norm"] = df["fear_greed"] / 100.0
        sentiment_cols.append("fg_norm")

    # Google Trends: average of three keyword series, normalize to 0-1
    gt_cols = [c for c in df.columns if c.startswith("gtrends_")]
    if gt_cols:
        gt_max = df[gt_cols].max().max()
        if gt_max > 0:
            df["gtrends_norm"] = df[gt_cols].mean(axis=1) / gt_max
            sentiment_cols.append("gtrends_norm")

    if sentiment_cols:
        df["sentiment_composite"] = df[sentiment_cols].mean(axis=1)
        df["sentiment_z"] = (
            (df["sentiment_composite"] - df["sentiment_composite"].mean()) /
            df["sentiment_composite"].std()
        )
        print(f"    Composite built from: {sentiment_cols}")
    else:
        print("    WARNING: no sentiment sources available")

    # ── 7. VIX and DXY change variables ──────────────────────
    if "vixcls" in df.columns:
        df["vix_change"] = df["vixcls"].diff()
    if "dtwexbgs" in df.columns:
        df["dxy_log_return"] = np.log(df["dtwexbgs"] / df["dtwexbgs"].shift(1))
    if "fedfunds" in df.columns:
        df["ffr_change"] = df["fedfunds"].diff()

    # ── Save ──────────────────────────────────────────────────
    out = PROC_DIR / "master_panel_features.csv"
    df.to_csv(out, index=False)
    print(f"\n  Features panel: {len(df)} rows × {len(df.columns)} columns → {out.name}")

    # Summary of key series
    print("\n  Key series summary:")
    summary_cols = ["eth_close","tvl_total_usd","usdc","fear_greed",
                    "eth_vol_30d","tvl_drawdown","sentiment_composite"]
    for c in summary_cols:
        if c in df.columns:
            valid = df[c].dropna()
            print(f"    {c:30s} n={len(valid):>4}  mean={valid.mean():>10.4f}  "
                  f"min={valid.min():>10.4f}  max={valid.max():>10.4f}")

    if "usdc_depeg" in df.columns:
        depeg_days = df["usdc_depeg"].sum()
        print(f"\n  USDC de-peg episodes: {depeg_days} days (|price-1| > {DEPEG_THRESHOLD})")

    for event_name in STRESS_EVENTS:
        col = f"event_{event_name}"
        if col in df.columns:
            n = df[col].sum()
            print(f"  Event window {event_name:6s}: {n} days flagged")

    print()
    return df


if __name__ == "__main__":
    run()
