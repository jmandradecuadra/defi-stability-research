# File:      src/modeling/event_study.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   Event study: TVL drawdown and ETH volatility around three
#            stress events — LUNA (May 2022), FTX (Nov 2022), SVB (Mar 2023)
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EVENTS = {
    "LUNA collapse":  "2022-05-09",
    "FTX bankruptcy": "2022-11-11",
    "SVB failure":    "2023-03-10",
}

WINDOW_PRE  = 30   # days before event
WINDOW_POST = 30   # days after event


def run():
    print("\n=== Event study ===")

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])
    df = df.set_index("date").sort_index()

    all_windows = []
    summary_rows = []

    for event_name, event_date_str in EVENTS.items():
        event_date = pd.Timestamp(event_date_str)
        start = event_date - pd.Timedelta(days=WINDOW_PRE)
        end   = event_date + pd.Timedelta(days=WINDOW_POST)

        window = df.loc[start:end].copy()
        window["event_day"] = (window.index - event_date).days
        window["event"]     = event_name

        # Normalize TVL to 100 at event date for comparability
        if event_date in window.index and "tvl_total_usd" in window.columns:
            base_tvl = window.loc[event_date, "tvl_total_usd"]
            if base_tvl and base_tvl > 0:
                window["tvl_indexed"] = (window["tvl_total_usd"] / base_tvl) * 100

        # Normalize ETH price similarly
        if event_date in window.index and "eth_close" in window.columns:
            base_eth = window.loc[event_date, "eth_close"]
            if base_eth and base_eth > 0:
                window["eth_indexed"] = (window["eth_close"] / base_eth) * 100

        all_windows.append(window.reset_index())

        # Summary statistics
        pre  = window[window["event_day"] < 0]
        post = window[window["event_day"] > 0]

        def safe_pct_change(pre_val, post_val):
            if pre_val and pre_val != 0:
                return round((post_val - pre_val) / abs(pre_val) * 100, 2)
            return None

        tvl_pre_mean  = float(pre["tvl_total_usd"].mean())  if "tvl_total_usd" in pre.columns else None
        tvl_post_mean = float(post["tvl_total_usd"].mean()) if "tvl_total_usd" in post.columns else None
        eth_pre_mean  = float(pre["eth_close"].mean())       if "eth_close" in pre.columns else None
        eth_post_mean = float(post["eth_close"].mean())      if "eth_close" in post.columns else None
        fg_pre_mean   = float(pre["fear_greed"].mean())      if "fear_greed" in pre.columns else None
        fg_post_mean  = float(post["fear_greed"].mean())     if "fear_greed" in post.columns else None

        tvl_min = float(window["tvl_total_usd"].min()) if "tvl_total_usd" in window.columns else None
        tvl_max_drawdown = safe_pct_change(tvl_pre_mean, tvl_min)

        summary_rows.append({
            "Event":            event_name,
            "Date":             event_date_str,
            "TVL pre-mean (B)": round(tvl_pre_mean  / 1e9, 2) if tvl_pre_mean  else None,
            "TVL post-mean (B)":round(tvl_post_mean / 1e9, 2) if tvl_post_mean else None,
            "TVL change (%)":   safe_pct_change(tvl_pre_mean, tvl_post_mean),
            "TVL max drop (%)": tvl_max_drawdown,
            "ETH pre-mean":     round(eth_pre_mean, 2)  if eth_pre_mean  else None,
            "ETH post-mean":    round(eth_post_mean, 2) if eth_post_mean else None,
            "ETH change (%)":   safe_pct_change(eth_pre_mean, eth_post_mean),
            "F&G pre-mean":     round(fg_pre_mean, 1)  if fg_pre_mean  else None,
            "F&G post-mean":    round(fg_post_mean, 1) if fg_post_mean else None,
        })

        print(f"\n  {event_name} ({event_date_str}):")
        print(f"    TVL change pre→post:  {safe_pct_change(tvl_pre_mean, tvl_post_mean)}%")
        print(f"    ETH change pre→post:  {safe_pct_change(eth_pre_mean, eth_post_mean)}%")
        print(f"    Fear&Greed pre→post:  {round(fg_pre_mean,1) if fg_pre_mean else 'N/A'} → "
              f"{round(fg_post_mean,1) if fg_post_mean else 'N/A'}")

    # Save full window data for Power BI
    combined = pd.concat(all_windows, ignore_index=True)
    out_windows  = OUTPUT_DIR / "event_study_windows.csv"
    out_summary  = OUTPUT_DIR / "table4_event_study_summary.csv"
    combined.to_csv(out_windows, index=False)
    pd.DataFrame(summary_rows).to_csv(out_summary, index=False)

    print(f"\n  → {out_windows.name}")
    print(f"  → {out_summary.name}")
    return combined, pd.DataFrame(summary_rows)


if __name__ == "__main__":
    run()
