# File:      src/modeling/regression_sentiment.py
# Component: econ-analytics pipeline — modeling layer
# Purpose:   OLS regression: TVL return ~ sentiment + VIX + DXY + rate + events
#            Uses HAC (Newey-West) standard errors for serial correlation
# Rev:       v1.0.0
# Updated:   2026-04-08

import pandas as pd
import numpy as np
from pathlib import Path

PROC_DIR   = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n=== OLS regression with HAC standard errors ===")

    try:
        import statsmodels.api as sm
    except ImportError:
        print("  statsmodels not installed — run: pip install statsmodels")
        return

    df = pd.read_csv(PROC_DIR / "master_panel_features.csv", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # ── Dependent variable ────────────────────────────────────
    dep_var = "tvl_log_return"

    # ── Independent variables ─────────────────────────────────
    indep_vars = {
        "sentiment_composite_lag1": None,   # built below
        "vix_change":               "vix_change",
        "dxy_log_return":           "dxy_log_return",
        "ffr_change":               "ffr_change",
        "event_luna":               "event_luna",
        "event_ftx":                "event_ftx",
        "event_svb":                "event_svb",
    }

    # Sentiment lagged 1 day (hypothesis: sentiment leads TVL)
    if "sentiment_composite" in df.columns:
        df["sentiment_composite_lag1"] = df["sentiment_composite"].shift(1)

    # Build regression dataset
    reg_cols = [dep_var] + [v if v else k for k, v in indep_vars.items()
                            if v or k in df.columns]
    reg_cols = [dep_var, "sentiment_composite_lag1", "vix_change",
                "dxy_log_return", "ffr_change",
                "event_luna", "event_ftx", "event_svb"]
    reg_cols = [c for c in reg_cols if c in df.columns]

    reg_df = df[reg_cols].dropna()
    print(f"  Observations after dropping NaN: {len(reg_df)}")

    if len(reg_df) < 50:
        print("  ERROR: insufficient observations for regression")
        return

    y = reg_df[dep_var]
    X_cols = [c for c in reg_cols if c != dep_var]
    X = sm.add_constant(reg_df[X_cols])

    # ── OLS with HAC (Newey-West) standard errors ─────────────
    # maxlags=None uses Newey-West automatic bandwidth selection
    model  = sm.OLS(y, X)
    result = model.fit(cov_type="HAC", cov_kwds={"maxlags": None})

    print(f"\n  Dependent variable: {dep_var}")
    print(f"  R²          = {result.rsquared:.4f}")
    print(f"  Adj. R²     = {result.rsquared_adj:.4f}")
    print(f"  F-statistic = {result.fvalue:.4f}  p = {result.f_pvalue:.4f}")
    print(f"  N           = {int(result.nobs)}")

    # ── Coefficient table ─────────────────────────────────────
    coef_df = pd.DataFrame({
        "variable":    result.params.index,
        "coefficient": result.params.values.round(6),
        "std_error":   result.bse.values.round(6),
        "t_stat":      result.tvalues.values.round(4),
        "p_value":     result.pvalues.values.round(4),
        "ci_low":      result.conf_int()[0].values.round(6),
        "ci_high":     result.conf_int()[1].values.round(6),
        "significance": ["***" if p < 0.01 else "**" if p < 0.05 else
                         "*"   if p < 0.10 else "" for p in result.pvalues],
    })

    print("\n  Coefficient table (HAC standard errors):")
    print(coef_df.to_string(index=False))

    # ── Diagnostics ───────────────────────────────────────────
    from statsmodels.stats.stattools import durbin_watson
    dw = durbin_watson(result.resid)
    print(f"\n  Durbin-Watson:  {dw:.4f}")
    print(f"  (2.0 = no autocorrelation; HAC SEs correct for departures)")

    # ── Save outputs ──────────────────────────────────────────
    out_coef = OUTPUT_DIR / "table6_regression_coefficients.csv"
    coef_df.to_csv(out_coef, index=False)

    diag_df = pd.DataFrame([{
        "model":        "OLS_HAC",
        "dep_var":      dep_var,
        "n_obs":        int(result.nobs),
        "r_squared":    round(float(result.rsquared), 4),
        "adj_r_squared":round(float(result.rsquared_adj), 4),
        "f_stat":       round(float(result.fvalue), 4),
        "f_pvalue":     round(float(result.f_pvalue), 4),
        "durbin_watson":round(float(dw), 4),
        "aic":          round(float(result.aic), 2),
        "bic":          round(float(result.bic), 2),
    }])
    out_diag = OUTPUT_DIR / "table6_regression_diagnostics.csv"
    diag_df.to_csv(out_diag, index=False)

    # Residuals for Power BI diagnostics page
    resid_df = pd.DataFrame({
        "date":    df.loc[reg_df.index, "date"].values,
        "fitted":  result.fittedvalues.values,
        "residual":result.resid.values,
        "actual":  y.values,
    })
    resid_df.to_csv(OUTPUT_DIR / "regression_residuals.csv", index=False)

    print(f"\n  → {out_coef.name}")
    print(f"  → {out_diag.name}")
    print(f"  → regression_residuals.csv")
    return result, coef_df


if __name__ == "__main__":
    run()
