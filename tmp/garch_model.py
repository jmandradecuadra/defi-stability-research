# File:      src/modeling/garch_model.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   Estimate GARCH(1,1) on ETH and BTC log-returns
#            Documents volatility clustering and persistence
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n=== GARCH(1,1) estimation ===")

    try:
        from arch import arch_model
    except ImportError:
        print("  arch not installed — run: pip install arch")
        return

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])
    df = df.set_index("date").sort_index()

    results_rows = []

    for asset, col in [("ETH", "eth_log_return"), ("BTC", "btc_log_return")]:
        if col not in df.columns:
            continue

        returns = df[col].dropna() * 100   # scale to percent for numerical stability
        print(f"\n  Fitting GARCH(1,1) on {asset} returns ({len(returns)} obs) ...")

        model  = arch_model(returns, vol="Garch", p=1, q=1, dist="normal", rescale=False)
        result = model.fit(disp="off")

        omega = float(result.params["omega"])
        alpha = float(result.params["alpha[1]"])
        beta  = float(result.params["beta[1]"])
        persistence = alpha + beta

        print(f"    ω (omega):           {omega:.6f}  p={result.pvalues['omega']:.4f}")
        print(f"    α (ARCH effect):     {alpha:.4f}  p={result.pvalues['alpha[1]']:.4f}")
        print(f"    β (GARCH effect):    {beta:.4f}  p={result.pvalues['beta[1]']:.4f}")
        print(f"    α + β (persistence): {persistence:.4f}")
        print(f"    Log-likelihood:      {result.loglikelihood:.2f}")
        print(f"    AIC:                 {result.aic:.2f}")

        # Save conditional volatility series
        cond_vol = result.conditional_volatility.reset_index()
        cond_vol.columns = ["date", f"{asset.lower()}_cond_vol"]
        cond_vol.to_csv(OUTPUT_DIR / f"garch_{asset.lower()}_cond_vol.csv", index=False)

        results_rows.append({
            "Asset":       asset,
            "omega":       round(omega, 6),
            "alpha":       round(alpha, 4),
            "beta":        round(beta, 4),
            "persistence": round(persistence, 4),
            "alpha_pval":  round(float(result.pvalues["alpha[1]"]), 4),
            "beta_pval":   round(float(result.pvalues["beta[1]"]), 4),
            "log_lik":     round(float(result.loglikelihood), 2),
            "aic":         round(float(result.aic), 2),
            "n_obs":       int(len(returns)),
        })

    if results_rows:
        summary = pd.DataFrame(results_rows)
        out = OUTPUT_DIR / "table3_garch_results.csv"
        summary.to_csv(out, index=False)
        print(f"\n  → {out.name}")
        return summary


if __name__ == "__main__":
    run()
