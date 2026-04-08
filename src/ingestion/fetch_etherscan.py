# File:      src/ingestion/fetch_etherscan.py
# Component: econ-analytics pipeline
# Purpose:   Etherscan historical stats — API Pro required, excluded from pipeline
#            Key retained in .env for potential future use
# Rev:       v3.0.0
# Updated:   2026-04-08

def run():
    print("\n=== Etherscan ingestion ===")
    print("  Skipped: all historical stats endpoints require API Pro.")
    print("  On-chain network variable excluded from analysis.")
    print("  See paper Section 4.1 for methodological note.\n")

if __name__ == "__main__":
    run()
