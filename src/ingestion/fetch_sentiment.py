import time, requests, pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
START_DATE = pd.Timestamp("2020-01-01")
END_DATE   = pd.Timestamp(datetime.today().strftime("%Y-%m-%d"))

def fetch_fear_greed():
    print("  Fetching Fear & Greed Index ...", end=" ")
    r = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=30)
    r.raise_for_status()
    data = r.json().get("data",[])
    if not data:
        print("NO DATA"); return
    df = pd.DataFrame(data)
    df["date"]       = pd.to_datetime(df["timestamp"].astype(int), unit="s").dt.normalize()
    df["fear_greed"] = pd.to_numeric(df["value"], errors="coerce")
    df["fg_label"]   = df["value_classification"]
    df = df[["date","fear_greed","fg_label"]]
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("date").reset_index(drop=True)
    out = RAW_DIR / "fear_greed_index.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")

def fetch_google_trends():
    print("  Fetching Google Trends ...", end=" ")
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("pytrends not installed"); return
    keywords = ["DeFi","crypto crash","Ethereum"]
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10,30))
    all_dfs  = []
    for year in range(START_DATE.year, END_DATE.year + 1):
        try:
            pytrends.build_payload(keywords, timeframe=f"{year}-01-01 {year+1}-01-01", geo="")
            df_chunk = pytrends.interest_over_time()
            if not df_chunk.empty:
                df_chunk = df_chunk.drop(columns=["isPartial"], errors="ignore").reset_index()
                all_dfs.append(df_chunk)
        except Exception as e:
            print(f"\n    Warning: chunk {year} failed: {e}")
        time.sleep(2)
    if not all_dfs:
        print("NO DATA"); return
    df = pd.concat(all_dfs).drop_duplicates("date").sort_values("date")
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df.rename(columns={"DeFi":"gtrends_defi",
                             "crypto crash":"gtrends_crypto_crash",
                             "Ethereum":"gtrends_ethereum"})
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)].reset_index(drop=True)
    out = RAW_DIR / "google_trends_defi.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")

def run():
    print("\n=== Sentiment ingestion ===")
    fetch_fear_greed()
    fetch_google_trends()
    print("\nNote: LunarCrush excluded — historical API requires paid plan.")
    print("Sentiment composite: Fear & Greed Index + Google Trends (2 sources).")
    print("Sentiment done.\n")

if __name__ == "__main__":
    run()
