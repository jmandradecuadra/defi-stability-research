import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))

from credentials    import validate_all
from fetch_fred      import run as run_fred
from fetch_defillama import run as run_defillama
from fetch_binance   import run as run_binance
from fetch_coingecko import run as run_coingecko
from fetch_etherscan import run as run_etherscan
from fetch_sentiment import run as run_sentiment

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# Files actually expected given API access constraints
EXPECTED = {
    "fred_vix.csv":               "FRED VIX index",
    "fred_ffr.csv":               "FRED Federal Funds Rate",
    "fred_dxy.csv":               "FRED USD index",
    "defillama_tvl_total.csv":    "DeFiLlama total TVL",
    "defillama_uniswap.csv":      "DeFiLlama Uniswap TVL",
    "defillama_aave.csv":         "DeFiLlama Aave TVL",
    "binance_eth_usd_daily.csv":  "Binance ETH/USD OHLCV",
    "binance_btc_usd_daily.csv":  "Binance BTC/USD OHLCV",
    "coingecko_usdc.csv":         "USDC price (Binance)",
    "fear_greed_index.csv":       "Fear & Greed Index",
    "google_trends_defi.csv":     "Google Trends DeFi",
}

EXCLUDED = {
    "coingecko_usdt.csv":   "USDT — no clean USD pair on Binance",
    "eth_gas_fees.csv":     "Etherscan — historical stats require API Pro",
    "lunarcrush_btc.csv":   "LunarCrush — historical time-series requires paid plan",
    "lunarcrush_eth.csv":   "LunarCrush — historical time-series requires paid plan",
}

def validate_outputs():
    print("\n=== Output validation ===")
    import pandas as pd
    missing = []
    for fname, label in EXPECTED.items():
        path = RAW_DIR / fname
        if not path.exists():
            missing.append(fname)
            print(f"  MISSING  {fname:45s} ← {label}")
        else:
            rows = len(pd.read_csv(path))
            print(f"  OK  {fname:45s} {rows:>5} rows")

    print()
    for fname, reason in EXCLUDED.items():
        print(f"  EXCL {fname:45s} ← {reason}")

    print()
    if missing:
        print(f"  {len(missing)} required file(s) missing.")
    else:
        print(f"  All {len(EXPECTED)} required files present.")
        print(f"  {len(EXCLUDED)} sources excluded by documented decision.")
        print(f"  Phase 1 ingestion COMPLETE.")
    return len(missing) == 0

def main():
    print("="*60)
    print("  econ-analytics — full ingestion run")
    print("="*60)
    validate_all()
    t0 = time.time()
    run_fred(); run_defillama(); run_binance()
    run_coingecko(); run_etherscan(); run_sentiment()
    print(f"\nAll ingestion complete in {time.time()-t0:.0f}s")
    sys.exit(0 if validate_outputs() else 1)

if __name__ == "__main__":
    main()
