import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

def _require(key):
    value = os.getenv(key, "").strip()
    if not value or value.startswith("YOUR_"):
        raise EnvironmentError(f"\n\n  Missing credential: {key}\n  Add it to: {_ROOT / '.env'}\n")
    return value

def _optional(key):
    value = os.getenv(key, "").strip()
    return None if (not value or value.startswith("YOUR_")) else value

def fred_key():
    return _require("FRED_API_KEY")

def etherscan_key():
    return _require("ETHERSCAN_API_KEY")

def lunarcrush_token():
    return _optional("LUNARCRUSH_TOKEN")

def validate_all(skip_lunarcrush=False):
    errors = []
    for fn in (fred_key, etherscan_key):
        try:
            fn()
        except EnvironmentError as e:
            errors.append(str(e))
    if errors:
        raise EnvironmentError("Credential validation failed:" + "".join(errors))
    lc = "configured" if lunarcrush_token() else "NOT configured"
    print("✓ FRED          configured")
    print("✓ Etherscan     configured")
    print(f"  LunarCrush    {lc}")
    print("  Keyless: DeFiLlama, Fear&Greed, Binance, CoinGecko, Google Trends")
