# File:      src/ingestion/fetch_defillama.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download total DeFi TVL, Uniswap TVL/volume, Aave TVL from DeFiLlama
# Arch:      Calls DeFiLlama public REST API — no key required
# Rev:       v1.0.0
# Updated:   2026-04-08

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.Timestamp("2020-01-01")
END_DATE   = pd.Timestamp(datetime.today().strftime("%Y-%m-%d"))


# ── helpers ───────────────────────────────────────────────────

def _get(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def _ts_to_df(records: list, value_col: str) -> pd.DataFrame:
    """Convert DeFiLlama [{'date': unix_ts, 'totalLiquidityUSD': v}, ...] to DataFrame."""
    df = pd.DataFrame(records)
    # DeFiLlama returns either 'date'/'totalLiquidityUSD' or 'date'/'tvl'
    date_col = "date"
    val_col  = [c for c in df.columns if c != "date"][0]
    df = df[[date_col, val_col]].copy()
    df["date"] = pd.to_datetime(df[date_col], unit="s")
    df = df.rename(columns={val_col: value_col})
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ── fetchers ──────────────────────────────────────────────────

def fetch_total_tvl() -> pd.DataFrame:
    print("  Fetching total DeFi TVL ...", end=" ")
    data = _get("https://api.llama.fi/v2/historicalChainTvl")
    df = _ts_to_df(data, "tvl_total_usd")
    out = RAW_DIR / "defillama_tvl_total.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


def fetch_protocol_tvl(slug: str, filename: str, col_name: str) -> pd.DataFrame:
    print(f"  Fetching {slug} TVL ...", end=" ")
    data = _get(f"https://api.llama.fi/protocol/{slug}")
    tvl_records = data.get("tvl", [])
    if not tvl_records:
        print("NO DATA")
        return pd.DataFrame()
    df = _ts_to_df(tvl_records, col_name)
    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


# ── main ──────────────────────────────────────────────────────

def run():
    print("\n=== DeFiLlama ingestion ===")

    fetch_total_tvl()
    fetch_protocol_tvl("uniswap",  "defillama_uniswap.csv",  "tvl_uniswap_usd")
    fetch_protocol_tvl("aave",     "defillama_aave.csv",     "tvl_aave_usd")

    print(f"DeFiLlama done. Files saved to {RAW_DIR}\n")


if __name__ == "__main__":
    run()
