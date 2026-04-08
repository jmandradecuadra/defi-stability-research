# File:      src/ingestion/fetch_coingecko.py
# Component: econ-analytics pipeline
# Purpose:   Download USDC daily price from Binance (no key required)
#            CoinGecko removed free tier — replaced with Binance public API
#            USDT excluded: no clean USD pair available; USDC retained as
#            primary stablecoin series (SVB de-peg March 2023 is key event)
# Rev:       v3.0.0
# Updated:   2026-04-08

import time, requests, pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR  = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "https://api.binance.com/api/v3/klines"
START_MS = int(pd.Timestamp("2020-01-01").timestamp() * 1000)
END_MS   = int(pd.Timestamp(datetime.today().strftime("%Y-%m-%d")).timestamp() * 1000)
COLS     = ["open_time","open","high","low","close","volume","close_time",
            "quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]

def fetch_pair(symbol, col_name, filename):
    print(f"  Fetching {symbol} ...", end=" ")
    all_bars, start = [], START_MS
    while start < END_MS:
        r = requests.get(BASE_URL, params={"symbol":symbol,"interval":"1d",
            "startTime":start,"endTime":END_MS,"limit":1000}, timeout=30)
        r.raise_for_status()
        bars = r.json()
        if not bars: break
        all_bars.extend(bars)
        start = bars[-1][6] + 1
        if len(bars) < 1000: break
        time.sleep(0.2)
    if not all_bars:
        print("NO DATA"); return
    df = pd.DataFrame(all_bars, columns=COLS)
    df["date"]   = pd.to_datetime(df["open_time"], unit="ms").dt.normalize()
    df[col_name] = pd.to_numeric(df["close"], errors="coerce")
    df = df[["date", col_name]].drop_duplicates("date").sort_values("date").reset_index(drop=True)
    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")

def run():
    print("\n=== Stablecoin ingestion (Binance) ===")
    fetch_pair("USDCUSDT", "usdc", "coingecko_usdc.csv")
    print("Note: USDT excluded — no clean USD pair on Binance.")
    print("USDC retained as primary stablecoin (SVB de-peg March 2023).\n")
    print("Stablecoin done.\n")

if __name__ == "__main__":
    run()
