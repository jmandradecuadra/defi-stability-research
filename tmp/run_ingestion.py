# File:      scripts/run_ingestion.py
# Component: econ-analytics pipeline — orchestration
# Purpose:   Run all ingestion scripts in correct order, validate outputs
# Rev:       v1.0.0
# Updated:   2026-04-08
#
# Usage:
#   cd "/c/Users/Public/VS Code/econ-analytics"
#   PYTHONPATH=. python scripts/run_ingestion.py

import sys
import time
from pathlib import Path

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))

from credentials import validate_all
from fetch_fred       import run as run_fred
from fetch_defillama  import run as run_defillama
from fetch_binance    import run as run_binance
from fetch_coingecko  import run as run_coingecko
from fetch_etherscan  import run as run_etherscan
from fetch_sentiment  import run as run_sentiment

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

EXPECTED_FILES = [
    "fred_vix.csv",
    "fred_ffr.csv",
    "fred_dxy.csv",
    "defillama_tvl_total.csv",
    "defillama_uniswap.csv",
    "defillama_aave.csv",
    "binance_eth_usd_daily.csv",
    "binance_btc_usd_daily.csv",
    "coingecko_usdc.csv",
    "coingecko_usdt.csv",
    "eth_gas_fees.csv",
    "fear_greed_index.csv",
    "google_trends_defi.csv",
    "lunarcrush_btc.csv",
    "lunarcrush_eth.csv",
]


def validate_outputs():
    print("\n=== Output validation ===")
    missing = []
    for fname in EXPECTED_FILES:
        path = RAW_DIR / fname
        if not path.exists():
            missing.append(fname)
            print(f"  MISSING  {fname}")
        else:
            import pandas as pd
            df = pd.read_csv(path)
            print(f"  OK  {fname:45s} {len(df):>5} rows")

    if missing:
        print(f"\n  {len(missing)} file(s) missing — check errors above.")
    else:
        print(f"\n  All {len(EXPECTED_FILES)} files present. Ingestion complete.")
    return len(missing) == 0


def main():
    print("=" * 60)
    print("  econ-analytics — full ingestion run")
    print(f"  Output directory: {RAW_DIR}")
    print("=" * 60)

    # Validate credentials before any network call
    validate_all(skip_lunarcrush=False)

    t0 = time.time()

    run_fred()
    run_defillama()
    run_binance()
    run_coingecko()
    run_etherscan()
    run_sentiment()

    elapsed = time.time() - t0
    print(f"\nAll ingestion complete in {elapsed:.0f}s")

    ok = validate_outputs()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
