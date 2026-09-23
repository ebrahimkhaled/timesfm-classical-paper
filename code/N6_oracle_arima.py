"""Revision (JoF referee 1, M7): the Oracle ARIMA baseline, reproducibly.

The manuscript's Section 4.3 compares AutoARIMA with an "Oracle ARIMA" that knows the true orders
of the ARIMA-family processes D1-D4 and only estimates the parameters. The table behind it
(results/oracle_arima_results.csv, dated 2026-09-14) had no script in code/. This script
recomputes it from the same 200 series per cell.

Oracle specifications (the data-generating orders):
  D1  ARIMA(1,0,0) with constant
  D2  ARIMA(1,0,1) with constant
  D3  ARIMA(1,1,1) with drift
  D4  SARIMA(1,0,0)(1,1,0)[12], no constant
Estimation: Gaussian maximum likelihood in state-space form (statsmodels ARIMA, default settings);
D3 is fitted as ARMA(1,1) with a constant on the first differences and integrated back. Fits whose
optimiser reports non-convergence are kept as returned and counted ("nonconverged").

Output: results/oracle_arima_results.csv (overwritten) and results/oracle_arima_per_series.csv
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
REPS, H = 200, 12
SPEC = {"D1": dict(order=(1, 0, 0), trend="c"),
        "D2": dict(order=(1, 0, 1), trend="c"),
        "D3": dict(order=(1, 1, 1), trend="t"),
        "D4": dict(order=(1, 0, 0), seasonal_order=(1, 1, 0, 12), trend="n")}


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
mx = _load("metrics", "02_metrics.py")


def fit_forecast(y, spec):
    if spec.get("order") == (1, 1, 1):
        # ARIMA(1,1,1) with drift, fitted as ARMA(1,1) with a constant on the first differences
        # and integrated back: the drift is then the ARMA mean, with no state-space trend term.
        dy = np.diff(y)
        f, fell = fit_forecast(dy, dict(order=(1, 0, 1), trend="c"))
        return y[-1] + np.cumsum(f), fell
    res = ARIMA(y, **spec).fit()
    return res.forecast(H), not res.mle_retvals.get("converged", True)


def main():
    rows, per = [], []
    summ = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                       usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    summ = summ[summ.horizon_slice == "h1_12"]
    for d, spec in SPEC.items():
        m = dgp.SEASONAL_PERIOD[d]
        for n in dgp.LENGTHS:
            s = np.array([dgp.simulate(d, n, r, H) for r in range(REPS)])
            mase, fb = [], 0
            for r in range(REPS):
                fc, fell = fit_forecast(s[r, :n], spec)
                fb += fell
                den = mx.mase_denominator(s[r, :n], m)
                mase.append(mx.mase(s[r, n:], np.asarray(fc), den))
                per.append({"dgp": d, "n": n, "rep": r, "Oracle_MASE": mase[-1], "nonconverged": fell})
            o = float(np.nanmean(mase))
            a = summ[(summ.dgp == d) & (summ.n == n) & (summ.method == "AutoARIMA")].MASE.mean()
            t = summ[(summ.dgp == d) & (summ.n == n) & (summ.method == "TimesFM3")].MASE.mean()
            rows.append({"DGP": d, "n": n, "Oracle_MASE": round(o, 3), "AutoARIMA_MASE": round(a, 3),
                         "TimesFM3_MASE": round(t, 3),
                         "Selection_Penalty_%": round(100 * (a / o - 1), 1),
                         "Oracle_vs_TimesFM_%": round(100 * (o / t - 1), 1),
                         "nonconverged_fits": fb})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(ROOT / "results" / "oracle_arima_results.csv", index=False)
    pd.DataFrame(per).to_csv(ROOT / "results" / "oracle_arima_per_series.csv", index=False)


if __name__ == "__main__":
    main()
