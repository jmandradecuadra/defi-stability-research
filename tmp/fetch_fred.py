# File:      src/ingestion/fetch_fred.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download VIX, Federal Funds Rate, and DXY from FRED API
# Arch:      Calls FRED REST API v2, saves to data/raw/
# Rev:       v1.0.0
# Updated:   2026-04-08

import os
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from credentials import fred_key

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
RAW_DIR  = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = "2020-01-01"
END_DATE   = datetime.today().strftime("%Y-%m-%d")

SERIES = {
    "VIXCLS":   "fred_vix.csv",
    "FEDFUNDS": "fred_ffr.csv",
    "DTWEXBGS": "fred_dxy.csv",
}


def fetch_series(series_id: str, filename: str) -> pd.DataFrame:
    print(f"  Fetching {series_id} ...", end=" ")
    params = {
        "series_id":        series_id,
        "api_key":          fred_key(),
        "file_type":        "json",
        "observation_start": START_DATE,
        "observation_end":   END_DATE,
        "frequency":        "d",          # daily
        "aggregation_method": "avg",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()

    data = r.json().get("observations", [])
    if not data:
        print("NO DATA")
        return pd.DataFrame()

    df = pd.DataFrame(data)[["date", "value"]]
    df.columns = ["date", series_id.lower()]
    df["date"] = pd.to_datetime(df["date"])

    # FRED uses "." for missing values
    df = df[df[series_id.lower()] != "."].copy()
    df[series_id.lower()] = pd.to_numeric(df[series_id.lower()], errors="coerce")
    df = df.dropna().reset_index(drop=True)

    out_path = RAW_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"{len(df)} rows → {out_path.name}")
    return df


def run():
    print("\n=== FRED ingestion ===")
    results = {}
    for series_id, filename in SERIES.items():
        results[series_id] = fetch_series(series_id, filename)
        time.sleep(0.5)   # stay well under 5 calls/sec rate limit
    print(f"FRED done. {len(results)} series saved to {RAW_DIR}\n")
    return results


if __name__ == "__main__":
    run()
