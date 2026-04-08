# File:      src/processing/merge_panel.py
# Component: econ-analytics pipeline — processing layer
# Purpose:   Merge all 11 raw series into a single daily master panel
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
from pathlib import Path

RAW_DIR  = Path(__file__).resolve().parents[2] / "data" / "raw"
PROC_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2020-01-01")
END   = pd.Timestamp("2025-12-31")


def load(filename, date_col="date"):
    path = RAW_DIR / filename
    if not path.exists():
        print(f"  SKIP (not found): {filename}")
        return None
    df = pd.read_csv(path, parse_dates=[date_col])
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
    df = df.drop_duplicates(date_col).set_index(date_col)
    return df


def run():
    print("\n=== Panel merge ===")

    # Build full daily date spine 2020-01-01 to 2025-12-31
    spine = pd.DataFrame(index=pd.date_range(START, END, freq="D"))
    spine.index.name = "date"

    series = {
        "binance_eth_usd_daily.csv": ["open","high","low","close","volume"],
        "binance_btc_usd_daily.csv": ["open","high","low","close","volume"],
        "defillama_tvl_total.csv":   ["tvl_total_usd"],
        "defillama_uniswap.csv":     ["tvl_uniswap_usd"],
        "defillama_aave.csv":        ["tvl_aave_usd"],
        "coingecko_usdc.csv":        ["usdc"],
        "fred_vix.csv":              ["vixcls"],
        "fred_dxy.csv":              ["dtwexbgs"],
        "fear_greed_index.csv":      ["fear_greed"],
    }

    panel = spine.copy()

    for filename, cols in series.items():
        df = load(filename)
        if df is None:
            continue
        # Keep only known columns that exist
        existing = [c for c in cols if c in df.columns]
        # Rename ETH and BTC OHLCV to avoid collision
        if "eth" in filename:
            df = df[existing].rename(columns={c: f"eth_{c}" for c in existing})
        elif "btc" in filename:
            df = df[existing].rename(columns={c: f"btc_{c}" for c in existing})
        else:
            df = df[existing]
        panel = panel.join(df, how="left")

    # FEDFUNDS is monthly — forward-fill to daily
    ffr = load("fred_ffr.csv")
    if ffr is not None:
        panel = panel.join(ffr[["fedfunds"]], how="left")
        panel["fedfunds"] = panel["fedfunds"].ffill()

    # Google Trends is weekly — forward-fill to daily
    gt = load("google_trends_defi.csv")
    if gt is not None:
        gt_cols = [c for c in gt.columns if c.startswith("gtrends")]
        panel = panel.join(gt[gt_cols], how="left")
        for c in gt_cols:
            panel[c] = panel[c].ffill()

    panel = panel.reset_index()
    panel = panel[(panel["date"] >= START) & (panel["date"] <= END)]
    panel = panel.sort_values("date").reset_index(drop=True)

    out = PROC_DIR / "master_panel.csv"
    panel.to_csv(out, index=False)
    print(f"  Master panel: {len(panel)} rows × {len(panel.columns)} columns → {out.name}")
    print(f"  Columns: {list(panel.columns)}\n")
    return panel


if __name__ == "__main__":
    run()
