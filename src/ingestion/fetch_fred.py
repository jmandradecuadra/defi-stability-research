import time, requests, pandas as pd
from pathlib import Path
from datetime import datetime
from credentials import fred_key

BASE_URL   = "https://api.stlouisfed.org/fred/series/observations"
RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
START_DATE = "2020-01-01"
END_DATE   = datetime.today().strftime("%Y-%m-%d")

# frequency: d=daily, m=monthly (FEDFUNDS is monthly — daily request returns 400)
SERIES = {
    "VIXCLS":   ("fred_vix.csv", "d"),
    "FEDFUNDS": ("fred_ffr.csv", "m"),
    "DTWEXBGS": ("fred_dxy.csv", "d"),
}

def fetch_series(series_id, filename, frequency):
    print(f"  Fetching {series_id} ...", end=" ")
    params = {"series_id":series_id,"api_key":fred_key(),"file_type":"json",
              "observation_start":START_DATE,"observation_end":END_DATE,
              "frequency":frequency,"aggregation_method":"avg"}
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("observations",[])
    if not data:
        print("NO DATA"); return pd.DataFrame()
    df = pd.DataFrame(data)[["date","value"]]
    df.columns = ["date", series_id.lower()]
    df["date"] = pd.to_datetime(df["date"])
    df = df[df[series_id.lower()] != "."].copy()
    df[series_id.lower()] = pd.to_numeric(df[series_id.lower()], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    out = RAW_DIR / filename
    df.to_csv(out, index=False)
    print(f"{len(df)} rows → {out.name}")
    return df

def run():
    print("\n=== FRED ingestion ===")
    for sid, (fname, freq) in SERIES.items():
        fetch_series(sid, fname, freq)
        time.sleep(0.5)
    print("FRED done.\n")

if __name__ == "__main__":
    run()
