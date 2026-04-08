# File:      src/ingestion/fetch_etherscan.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download daily average Ethereum gas price from Etherscan API
# Arch:      Etherscan REST API v2 — free key required (5 calls/sec limit)
# Rev:       v1.0.0
# Updated:   2026-04-08

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from credentials import etherscan_key

RAW_DIR  = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL   = "https://api.etherscan.io/v2/api"
START_DATE = pd.Timestamp("2020-01-01")
END_DATE   = pd.Timestamp(datetime.today().strftime("%Y-%m-%d"))


def fetch_gas_oracle_history() -> pd.DataFrame:
    """
    Etherscan's dailyavggasprice endpoint returns daily average gas price
    in Wei. We convert to Gwei (divide by 1e9) for readability.
    Endpoint: stats/dailyavggasprice
    """
    print("  Fetching Ethereum daily avg gas price ...", end=" ")

    params = {
        "chainid":   1,                    # Ethereum mainnet
        "module":    "stats",
        "action":    "dailyavggasprice",
        "startdate": START_DATE.strftime("%Y-%m-%d"),
        "enddate":   END_DATE.strftime("%Y-%m-%d"),
        "sort":      "asc",
        "apikey":    etherscan_key(),
    }

    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    if payload.get("status") != "1":
        msg = payload.get("message", "unknown error")
        result = payload.get("result", "")
        raise RuntimeError(f"Etherscan error: {msg} — {result}")

    records = payload["result"]
    df = pd.DataFrame(records)

    # Columns returned: UTCDate, unixTimeStamp, avgGasPrice_Wei
    df = df.rename(columns={
        "UTCDate":         "date",
        "avgGasPrice_Wei": "gas_price_wei",
    })

    df["date"] = pd.to_datetime(df["date"])
    df["gas_price_gwei"] = pd.to_numeric(df["gas_price_wei"],
                                          errors="coerce") / 1e9
    df = df[["date", "gas_price_gwei"]].dropna().reset_index(drop=True)

    out = RAW_DIR / "eth_gas_fees.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


def run():
    print("\n=== Etherscan ingestion ===")
    fetch_gas_oracle_history()
    print(f"Etherscan done. Files saved to {RAW_DIR}\n")


if __name__ == "__main__":
    run()
