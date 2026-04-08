# File:      src/ingestion/fetch_binance.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download ETH/USD and BTC/USD daily OHLCV from Binance public API
# Arch:      Binance REST API v3 — no key required for market data
# Rev:       v1.0.0
# Updated:   2026-04-08
# Note:      Binance returns max 1000 bars per request. Script paginates
#            automatically to cover the full 2020–present range.

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL   = "https://api.binance.com/api/v3/klines"
START_MS   = int(pd.Timestamp("2020-01-01").timestamp() * 1000)
END_MS     = int(pd.Timestamp(datetime.today().strftime("%Y-%m-%d")).timestamp() * 1000)
INTERVAL   = "1d"
LIMIT      = 1000   # Binance max per request

SYMBOLS = {
    "ETHUSDT": "binance_eth_usd_daily.csv",
    "BTCUSDT": "binance_btc_usd_daily.csv",
}

COLUMNS = ["open_time", "open", "high", "low", "close", "volume",
           "close_time", "quote_volume", "trades",
           "taker_buy_base", "taker_buy_quote", "ignore"]


def fetch_symbol(symbol: str, filename: str) -> pd.DataFrame:
    print(f"  Fetching {symbol} daily OHLCV ...", end=" ")
    all_bars = []
    start = START_MS

    while start < END_MS:
        params = {
            "symbol":    symbol,
            "interval":  INTERVAL,
            "startTime": start,
            "endTime":   END_MS,
            "limit":     LIMIT,
        }
        r = requests.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        bars = r.json()
        if not bars:
            break
        all_bars.extend(bars)
        # next page starts from the close_time of last bar + 1ms
        start = bars[-1][6] + 1
        if len(bars) < LIMIT:
            break
        time.sleep(0.2)   # be polite to Binance

    df = pd.DataFrame(all_bars, columns=COLUMNS)
    df["date"]  = pd.to_datetime(df["open_time"], unit="ms").dt.normalize()
    df["open"]  = pd.to_numeric(df["open"],   errors="coerce")
    df["high"]  = pd.to_numeric(df["high"],   errors="coerce")
    df["low"]   = pd.to_numeric(df["low"],    errors="coerce")
    df["close"] = pd.to_numeric(df["close"],  errors="coerce")
    df["volume"]= pd.to_numeric(df["volume"], errors="coerce")

    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df = df.drop_duplicates("date").sort_values("date").reset_index(drop=True)

    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


def run():
    print("\n=== Binance ingestion ===")
    for symbol, filename in SYMBOLS.items():
        fetch_symbol(symbol, filename)
        time.sleep(1)
    print(f"Binance done. Files saved to {RAW_DIR}\n")


if __name__ == "__main__":
    run()
