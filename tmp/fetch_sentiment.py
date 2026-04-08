# File:      src/ingestion/fetch_sentiment.py
# Component: econ-analytics pipeline — ingestion layer
# Purpose:   Download three sentiment series:
#              1. Crypto Fear & Greed Index (Alternative.me — no key)
#              2. Google Trends for DeFi-related terms (pytrends — no key)
#              3. LunarCrush BTC/ETH social sentiment (free Bearer token)
# Arch:      Three independent fetchers, each saves its own CSV to data/raw/
# Rev:       v1.0.0
# Updated:   2026-04-08

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from credentials import lunarcrush_token

RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.Timestamp("2020-01-01")
END_DATE   = pd.Timestamp(datetime.today().strftime("%Y-%m-%d"))


# ══════════════════════════════════════════════════════════════
# 1. FEAR & GREED INDEX
# ══════════════════════════════════════════════════════════════

def fetch_fear_greed() -> pd.DataFrame:
    """
    Alternative.me Fear & Greed Index — daily, no key required.
    Returns values 0 (Extreme Fear) to 100 (Extreme Greed).
    limit=0 returns the full available history.
    """
    print("  Fetching Fear & Greed Index ...", end=" ")
    url = "https://api.alternative.me/fng/?limit=0&format=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        print("NO DATA")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df["date"]        = pd.to_datetime(df["timestamp"].astype(int), unit="s")
    df["fear_greed"]  = pd.to_numeric(df["value"], errors="coerce")
    df["fg_label"]    = df["value_classification"]

    df = df[["date", "fear_greed", "fg_label"]].copy()
    df["date"] = df["date"].dt.normalize()
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("date").reset_index(drop=True)

    out = RAW_DIR / "fear_greed_index.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


# ══════════════════════════════════════════════════════════════
# 2. GOOGLE TRENDS
# ══════════════════════════════════════════════════════════════

def fetch_google_trends() -> pd.DataFrame:
    """
    Google Trends for DeFi-related search terms via pytrends.
    Returns weekly relative search interest (0-100) per keyword.
    Fetched in yearly chunks to maximize resolution.
    """
    print("  Fetching Google Trends ...", end=" ")

    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("pytrends not installed — run: pip install pytrends")
        return pd.DataFrame()

    keywords  = ["DeFi", "crypto crash", "Ethereum"]
    pytrends  = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    all_dfs   = []

    # Fetch in annual chunks — pytrends returns weekly data for multi-year ranges
    year = START_DATE.year
    while year <= END_DATE.year:
        chunk_start = f"{year}-01-01"
        chunk_end   = f"{min(year + 1, END_DATE.year + 1)}-01-01"
        try:
            pytrends.build_payload(
                keywords,
                timeframe=f"{chunk_start} {chunk_end}",
                geo="",        # worldwide
            )
            df_chunk = pytrends.interest_over_time()
            if not df_chunk.empty:
                df_chunk = df_chunk.drop(columns=["isPartial"], errors="ignore")
                df_chunk.index.name = "date"
                df_chunk = df_chunk.reset_index()
                all_dfs.append(df_chunk)
        except Exception as e:
            print(f"\n    Warning: Google Trends chunk {year} failed: {e}")
        year += 1
        time.sleep(2)   # avoid rate limiting

    if not all_dfs:
        print("NO DATA")
        return pd.DataFrame()

    df = pd.concat(all_dfs).drop_duplicates("date").sort_values("date")
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={
        "defi":         "gtrends_defi",
        "crypto_crash": "gtrends_crypto_crash",
        "ethereum":     "gtrends_ethereum",
    })
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.reset_index(drop=True)

    out = RAW_DIR / "google_trends_defi.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


# ══════════════════════════════════════════════════════════════
# 3. LUNARCRUSH
# ══════════════════════════════════════════════════════════════

def fetch_lunarcrush(coin: str = "bitcoin") -> pd.DataFrame:
    """
    LunarCrush v4 API — free Discover plan Bearer token required.
    Fetches social_score and sentiment for a given coin.
    coin: 'bitcoin' or 'ethereum'
    """
    token = lunarcrush_token()
    if not token:
        print(f"  LunarCrush: token not configured — skipping {coin}")
        return pd.DataFrame()

    col_prefix = "btc" if coin == "bitcoin" else "eth"
    print(f"  Fetching LunarCrush {coin} sentiment ...", end=" ")

    # LunarCrush v4 time series endpoint
    url = f"https://lunarcrush.com/api4/public/coins/{coin}/time-series/v2"
    headers = {"Authorization": f"Bearer {token}"}
    params  = {
        "bucket":   "day",
        "start":    int(START_DATE.timestamp()),
        "end":      int(END_DATE.timestamp()),
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if r.status_code == 401:
        print("invalid token — check LUNARCRUSH_TOKEN in .env")
        return pd.DataFrame()
    if r.status_code == 429:
        print("rate limited — waiting 60s ...", end=" ")
        time.sleep(60)
        r = requests.get(url, headers=headers, params=params, timeout=30)

    r.raise_for_status()
    payload = r.json()

    timeseries = payload.get("data", [])
    if not timeseries:
        print("NO DATA")
        return pd.DataFrame()

    df = pd.DataFrame(timeseries)

    # Keep only columns that exist in the response
    keep = {"time": "date"}
    for lc_col, our_col in [
        ("social_score",    f"lc_{col_prefix}_social_score"),
        ("sentiment",       f"lc_{col_prefix}_sentiment"),
        ("social_volume",   f"lc_{col_prefix}_social_volume"),
        ("galaxy_score",    f"lc_{col_prefix}_galaxy_score"),
    ]:
        if lc_col in df.columns:
            keep[lc_col] = our_col

    df = df[[c for c in keep.keys() if c in df.columns]].rename(columns=keep)
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.normalize()
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("date").reset_index(drop=True)

    filename = f"lunarcrush_{col_prefix}.csv"
    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def run():
    print("\n=== Sentiment ingestion ===")
    fetch_fear_greed()
    fetch_google_trends()
    fetch_lunarcrush("bitcoin")
    time.sleep(2)
    fetch_lunarcrush("ethereum")
    print(f"Sentiment done. Files saved to {RAW_DIR}\n")


if __name__ == "__main__":
    run()
