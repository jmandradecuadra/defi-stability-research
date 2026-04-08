# File:      src/ingestion/fetch_coingecko.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download USDC and USDT daily prices from CoinGecko public API
# Arch:      CoinGecko REST API v3 — no key required (public endpoint)
# Rev:       v1.0.0
# Updated:   2026-04-08
# Note:      CoinGecko free tier allows ~10-30 calls/min. Script sleeps
#            between calls to avoid 429 errors.

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR  = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.coingecko.com/api/v3"

# CoinGecko coin IDs and output filenames
COINS = {
    "usd-coin": ("usdc", "coingecko_usdc.csv"),
    "tether":   ("usdt", "coingecko_usdt.csv"),
}

START_DATE = "01-01-2020"   # CoinGecko format: DD-MM-YYYY
END_DATE   = datetime.today().strftime("%d-%m-%Y")


def fetch_coin(coin_id: str, col_name: str, filename: str) -> pd.DataFrame:
    print(f"  Fetching {coin_id} price history ...", end=" ")

    # CoinGecko /market_chart/range returns unix timestamps and prices
    start_ts = int(pd.Timestamp("2020-01-01").timestamp())
    end_ts   = int(pd.Timestamp(datetime.today().strftime("%Y-%m-%d")).timestamp())

    url = f"{BASE_URL}/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from":        start_ts,
        "to":          end_ts,
    }

    r = requests.get(url, params=params, timeout=30)

    if r.status_code == 429:
        print("rate limited — waiting 60s ...", end=" ")
        time.sleep(60)
        r = requests.get(url, params=params, timeout=30)

    r.raise_for_status()
    prices = r.json().get("prices", [])

    if not prices:
        print("NO DATA")
        return pd.DataFrame()

    df = pd.DataFrame(prices, columns=["timestamp_ms", col_name])
    df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms").dt.normalize()
    df = df[["date", col_name]].copy()
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

    # Keep one observation per day (CoinGecko may return multiple)
    df = df.groupby("date")[col_name].mean().reset_index()
    df = df.sort_values("date").reset_index(drop=True)

    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


def run():
    print("\n=== CoinGecko ingestion ===")
    for coin_id, (col_name, filename) in COINS.items():
        fetch_coin(coin_id, col_name, filename)
        time.sleep(3)   # respect free tier rate limit
    print(f"CoinGecko done. Files saved to {RAW_DIR}\n")


if __name__ == "__main__":
    run()
